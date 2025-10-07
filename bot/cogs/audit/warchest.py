"""
Warchest audit logic.
"""

import discord
from typing import List, Dict, Optional
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logging import get_logger
from utils.pagination import ActivityPaginator
from utils.helpers import create_embed
from services.warchest_service import WarchestService
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

logger = get_logger('audit.warchest')

async def run_warchest_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service, cities: int):
    """Run warchest audit logic."""
    try:
        # Get alliance members
        members = await alliance_service.get_alliance_members(config.ALLIANCE_ID)
        if not members:
            await interaction.followup.send("Could not fetch alliance members.", ephemeral=True)
            return
        
        # Filter for members with cities <= max_cities
        filtered_members = []
        for member in members:
            # Handle cities data - could be int or list
            cities_data = member.get("cities", 0)
            if isinstance(cities_data, list):
                city_count = len(cities_data)
            else:
                city_count = cities_data
            
            if (member.get("alliance_position", "") != "APPLICANT" and 
                city_count <= cities and 
                city_count > 0):
                filtered_members.append(member)
        
        if not filtered_members:
            await interaction.followup.send(f"No members found with ≤{cities} cities.", ephemeral=True)
            return
        
        # Get detailed nation data for all members
        nation_ids = [str(member.get("id", 0)) for member in filtered_members]
        nations_data = await nation_service.api.get_nations_batch_data(nation_ids, "everything_scope")
        
        violations = []
        warchest_service = WarchestService()
        
        for member in filtered_members:
            nation_id = str(member.get("id", 0))
            if nation_id not in nations_data:
                continue
            
            nation_data = nations_data[nation_id]
            violation = await check_warchest_compliance(member, nation_data, warchest_service, cache_service)
            if violation:
                violations.append(violation)
        
        # Create paginated results
        if violations:
            # Format violations for display
            formatted_violations = [format_warchest_violation(violation) for violation in violations]
            paginator = ActivityPaginator(formatted_violations)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="Warchest Audit Complete",
                description=f"All members (≤{cities} cities) have adequate warchest resources!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
            
    except Exception as e:
        logger.error(f"Error in warchest audit: {e}")
        await interaction.followup.send("Error running warchest audit.", ephemeral=True)

async def check_warchest_compliance(member: Dict, nation_data: Dict, warchest_service, cache_service) -> Optional[Dict]:
    """Check if a member has adequate warchest resources."""
    try:
        # Calculate warchest requirements
        supply, result, production = warchest_service.calculate_warchest(nation_data)
        
        if not supply or not result:
            return None
        
        # Check for significant deficits (deficit > 0)
        deficits = []
        
        for resource, required in supply.items():
            if resource in result:
                deficit = result[resource]
                if deficit > 0:
                    deficits.append(f"{resource.title()}: {deficit:,.0f} deficit (need {required:,.0f})")
        
        if deficits:
            return {
                'member': member,
                'nation_data': nation_data,
                'deficits': deficits,
                'supply': supply,
                'result': result,
                'cache_service': cache_service
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking warchest compliance for {member.get('id', 'unknown')}: {e}")
        return None

def format_warchest_violation(violation: Dict) -> str:
    """Format a warchest violation for display."""
    member = violation['member']
    nation_data = violation['nation_data']
    deficits = violation['deficits']
    cache_service = violation['cache_service']
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Cities:** {member.get('cities', 0)}\n"
        f"**Deficits:** {', '.join(deficits)}\n"
        f"**Discord:** {discord_username}"
    )

async def setup(bot):
    """Setup function for the cog."""
    pass