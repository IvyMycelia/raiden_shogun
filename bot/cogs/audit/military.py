"""
Military audit logic.
"""

import discord
from typing import List, Dict, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logging import get_logger
from utils.pagination import ActivityPaginator
from utils.helpers import create_embed
from config import Config

config = Config()

def get_discord_username_with_fallback(member: dict, cache_service) -> str:
    """Get Discord username with proper fallback order: registrations -> API -> N/A."""
    nation_id = str(member.get('id', ''))
    
    # First try registrations
    registrations = cache_service.load_registrations()
    for discord_id, data in registrations.items():
        if str(data.get('nation_id')) == nation_id:
            # Prefer discord_username (exact username) over discord_name (display name)
            return data.get('discord_username', data.get('discord_name', 'N/A'))
    
    # Then try API data from member
    discord_username = member.get('discord', '')
    if discord_username:
        return discord_username
    
    # Finally return N/A
    return 'N/A'

logger = get_logger('audit.military')

async def run_military_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service):
    """Run military audit logic."""
    try:
        # Get alliance members
        members = await alliance_service.get_alliance_members(config.ALLIANCE_ID)
        if not members:
            await interaction.followup.send("Could not fetch alliance members.", ephemeral=True)
            return
        
        # Filter for non-applicants
        filtered_members = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                filtered_members.append(member)
        
        if not filtered_members:
            await interaction.followup.send("No members found to audit.", ephemeral=True)
            return
        
        # Get detailed nation data for all members
        nation_ids = [str(member.get("id", 0)) for member in filtered_members]
        nations_data = await nation_service.api.get_nations_batch_data(nation_ids, "everything_scope")
        
        # Load yesterday's CSV data for military comparison
        yesterday_data = None
        try:
            from services.raid_cache_service import RaidCacheService
            async with RaidCacheService() as raid_cache:
                yesterday_data = raid_cache.load_yesterday_nations_cache()
        except Exception as e:
            logger.warning(f"Could not load yesterday's data for military audit: {e}")
        
        violations = []
        violators = []
        
        for member in filtered_members:
            nation_id = str(member.get("id", 0))
            if nation_id not in nations_data:
                continue
            
            nation_data = nations_data[nation_id]
            violation = await check_military_compliance(member, nation_data, cache_service, yesterday_data)
            if violation:
                violations.append(violation)
                discord_username = get_discord_username_with_fallback(member, cache_service)
                violators.append(f"@{discord_username}")
        
        # Create paginated results
        if violations:
            # Format violations for display
            formatted_violations = [format_military_violation(violation) for violation in violations]
            paginator = ActivityPaginator(formatted_violations)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="Military Audit Complete",
                description="All members meet military capacity requirements!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
        
        # Send summary with violators in codeblock
        if violators:
            violators_text = " ".join(violators)
            await interaction.followup.send(f"```### The Following People Need To Buy Their Military\n{violators_text}```")
            
    except Exception as e:
        logger.error(f"Error in military audit: {e}")
        await interaction.followup.send("Error running military audit.", ephemeral=True)

async def check_military_compliance(member: Dict, nation_data: Dict, cache_service, yesterday_data: Dict = None) -> Optional[Dict]:
    """Check if a member meets military capacity requirements."""
    try:
        cities_data = nation_data.get("cities", [])
        if not cities_data:
            return None
        
        # Get military research data
        military_research = nation_data.get("military_research", {})
        ground_capacity = military_research.get("ground_capacity", 0)
        air_capacity = military_research.get("air_capacity", 0)
        naval_capacity = military_research.get("naval_capacity", 0)
        
        # Calculate total capacity and units for each type
        total_soldiers_capacity = 0
        total_tanks_capacity = 0
        total_aircraft_capacity = 0
        total_ships_capacity = 0
        
        total_soldiers = 0
        total_tanks = 0
        total_aircraft = 0
        total_ships = 0
        
        for city in cities_data:
            # Calculate capacity for each city
            barracks = city.get("barracks", 0)
            hangars = city.get("hangars", 0)
            drydocks = city.get("drydocks", 0)
            factories = city.get("factories", 0)
            
            # Soldiers: barracks * 1000 + ground_capacity
            soldiers_cap = barracks * 1000 + ground_capacity
            total_soldiers_capacity += soldiers_cap
            
            # Tanks: factories * 1000 + ground_capacity
            tanks_cap = factories * 1000 + ground_capacity
            total_tanks_capacity += tanks_cap
            
            # Aircraft: hangars * 1000 + air_capacity
            aircraft_cap = hangars * 1000 + air_capacity
            total_aircraft_capacity += aircraft_cap
            
            # Ships: drydocks * 1000 + naval_capacity
            ships_cap = drydocks * 1000 + naval_capacity
            total_ships_capacity += ships_cap
        
        # Get current units
        total_soldiers = nation_data.get("soldiers", 0)
        total_tanks = nation_data.get("tanks", 0)
        total_aircraft = nation_data.get("aircraft", 0)
        total_ships = nation_data.get("ships", 0)
        
        # Check if they bought military units today by comparing with yesterday's data
        if yesterday_data:
            nation_id = str(member.get('id', ''))
            yesterday_nation = yesterday_data.get(nation_id, {})
            yesterday_soldiers = yesterday_nation.get('soldiers', 0)
            yesterday_tanks = yesterday_nation.get('tanks', 0)
            yesterday_aircraft = yesterday_nation.get('aircraft', 0)
            yesterday_ships = yesterday_nation.get('ships', 0)
            
            # If they bought any military units today, exclude from violations
            if (total_soldiers > yesterday_soldiers or 
                total_tanks > yesterday_tanks or 
                total_aircraft > yesterday_aircraft or 
                total_ships > yesterday_ships):
                logger.info(f"Nation {nation_id} bought military units today, excluding from violations")
                return None
        
        # Check usage percentage for each unit type
        violations = []
        threshold = 0.79  # 79%
        
        if total_soldiers_capacity > 0:
            soldiers_usage = total_soldiers / total_soldiers_capacity
            if soldiers_usage < threshold:
                violations.append(f"Soldiers: {soldiers_usage:.1%} ({total_soldiers:,}/{total_soldiers_capacity:,})")
        
        if total_tanks_capacity > 0:
            tanks_usage = total_tanks / total_tanks_capacity
            if tanks_usage < threshold:
                violations.append(f"Tanks: {tanks_usage:.1%} ({total_tanks:,}/{total_tanks_capacity:,})")
        
        if total_aircraft_capacity > 0:
            aircraft_usage = total_aircraft / total_aircraft_capacity
            if aircraft_usage < threshold:
                violations.append(f"Aircraft: {aircraft_usage:.1%} ({total_aircraft:,}/{total_aircraft_capacity:,})")
        
        if total_ships_capacity > 0:
            ships_usage = total_ships / total_ships_capacity
            if ships_usage < threshold:
                violations.append(f"Ships: {ships_usage:.1%} ({total_ships:,}/{total_ships_capacity:,})")
        
        if violations:
            return {
                'member': member,
                'nation_data': nation_data,
                'violations': violations,
                'cache_service': cache_service
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking military compliance for {member.get('id', 'unknown')}: {e}")
        return None

def format_military_violation(violation: Dict) -> str:
    """Format a military violation for display."""
    member = violation['member']
    nation_data = violation['nation_data']
    violations = violation['violations']
    cache_service = violation['cache_service']
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    # Get city count properly
    cities = member.get('cities', 0)
    if isinstance(cities, list):
        city_count = len(cities)
    else:
        city_count = cities
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Cities:** {city_count}\n"
        f"**Violations:** {', '.join(violations)}\n"
        f"**Discord:** {discord_username}"
    )

async def setup(bot):
    """Setup function for the cog."""
    pass