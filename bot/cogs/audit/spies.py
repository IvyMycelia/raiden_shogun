"""
Spies audit logic.
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

logger = get_logger('audit.spies')

async def run_spies_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service):
    """Run spies audit logic."""
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
        
        # Load yesterday's CSV data for spy comparison
        yesterday_data = None
        try:
            from services.raid_cache_service import RaidCacheService
            async with RaidCacheService() as raid_cache:
                yesterday_data = raid_cache.load_yesterday_nations_cache()
        except Exception as e:
            logger.warning(f"Could not load yesterday's data for spies audit: {e}")
        
        violations = []
        violators = []
        
        for member in filtered_members:
            nation_id = str(member.get("id", 0))
            if nation_id not in nations_data:
                continue
            
            nation_data = nations_data[nation_id]
            violation = await check_spies_compliance(member, nation_data, cache_service, yesterday_data)
            if violation:
                violations.append(violation)
                discord_username = get_discord_username_with_fallback(member, cache_service)
                violators.append(f"@{discord_username}")
        
        # Create paginated results
        if violations:
            # Format violations for display
            formatted_violations = [format_spies_violation(violation) for violation in violations]
            paginator = ActivityPaginator(formatted_violations)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="Spies Audit Complete",
                description="All members have adequate spy counts!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
        
        # Send summary with violators in codeblock
        if violators:
            violators_text = " ".join(violators)
            await interaction.followup.send(f"```### The Following People Need To Buy Spies\n{violators_text}```")
            
    except Exception as e:
        logger.error(f"Error in spies audit: {e}")
        await interaction.followup.send("Error running spies audit.", ephemeral=True)

async def check_spies_compliance(member: Dict, nation_data: Dict, cache_service, yesterday_data: Dict = None) -> Optional[Dict]:
    """Check if a member has adequate spy counts, considering if they bought spies today."""
    try:
        current_spies = nation_data.get("spies", 0)
        
        # Check if member has Intelligence Agency project
        project_bits = nation_data.get("project_bits", 0) or 0
        project_bits = int(project_bits) if project_bits else 0
        has_intel_agency = False
        
        if project_bits:
            bits = bin(project_bits)[2:][::-1]
            project_order = [
                'iron_works','bauxite_works','arms_stockpile','emergency_gasoline_reserve','mass_irrigation',
                'international_trade_center','missile_launch_pad','nuclear_research_facility','iron_dome',
                'vital_defense_system','central_intelligence_agency','center_for_civil_engineering',
                'propaganda_bureau','uranium_enrichment_program','urban_planning','advanced_urban_planning',
                'space_program','spy_satellite','moon_landing','pirate_economy','recycling_initiative',
                'telecommunications_satellite','green_technologies','arable_land_agency','clinical_research_center',
                'specialized_police_training_program','advanced_engineering_corps','government_support_agency',
                'research_and_development_center','activity_center','metropolitan_planning','military_salvage',
                'fallout_shelter','bureau_of_domestic_affairs','advanced_pirate_economy','mars_landing',
                'surveillance_network','guiding_satellite','nuclear_launch_facility'
            ]
            for i, ch in enumerate(bits):
                if ch == '1' and i < len(project_order) and project_order[i] == 'central_intelligence_agency':
                    has_intel_agency = True
                    break
        
        # Determine required spies
        required_spies = 60 if has_intel_agency else 50
        
        # Check if they bought spies today by comparing with yesterday's data
        if yesterday_data:
            nation_id = str(member.get('id', ''))
            yesterday_nation = yesterday_data.get(nation_id, {})
            yesterday_spies = yesterday_nation.get('spies', 0)
            
            # If they bought spies today (current > yesterday), exclude from violations
            if current_spies > yesterday_spies:
                logger.info(f"Nation {nation_id} bought spies today ({yesterday_spies} -> {current_spies}), excluding from violations")
                return None
        
        if current_spies < required_spies:
            return {
                'member': member,
                'nation_data': nation_data,
                'current_spies': current_spies,
                'required_spies': required_spies,
                'has_intel_agency': has_intel_agency,
                'cache_service': cache_service
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking spies compliance for {member.get('id', 'unknown')}: {e}")
        return None

def format_spies_violation(violation: Dict) -> str:
    """Format a spies violation for display."""
    member = violation['member']
    nation_data = violation['nation_data']
    current_spies = violation['current_spies']
    required_spies = violation['required_spies']
    has_intel_agency = violation['has_intel_agency']
    cache_service = violation['cache_service']
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    intel_status = "Yes" if has_intel_agency else "No"
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Current Spies:** {current_spies}\n"
        f"**Required Spies:** {required_spies}\n"
        f"**Has Intel Agency:** {intel_status}\n"
        f"**Discord:** {discord_username}"
    )

async def setup(bot):
    """Setup function for the cog."""
    pass