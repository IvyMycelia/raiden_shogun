"""
MMR audit logic.
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

logger = get_logger('audit.mmr')

async def run_mmr_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service):
    """Run MMR audit logic."""
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
        
        violations = []
        violators = []
        
        for member in filtered_members:
            nation_id = str(member.get("id", 0))
            if nation_id not in nations_data:
                continue
            
            nation_data = nations_data[nation_id]
            violation = await check_mmr_compliance(member, nation_data, cache_service)
            if violation:
                violations.append(violation)
                discord_username = get_discord_username_with_fallback(member, cache_service)
                violators.append(f"@{discord_username}")
        
        # Create paginated results
        if violations:
            # Format violations for display
            formatted_violations = [format_mmr_violation(violation) for violation in violations]
            paginator = ActivityPaginator(formatted_violations)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="MMR Audit Complete",
                description="All members meet MMR requirements!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
        
        # Send summary with violators in codeblock
        if violators:
            violators_text = " ".join(violators)
            await interaction.followup.send(f"```The Following People Need To Fix MMR: {violators_text}```")
            
    except Exception as e:
        logger.error(f"Error in MMR audit: {e}")
        await interaction.followup.send("Error running MMR audit.", ephemeral=True)

async def check_mmr_compliance(member: Dict, nation_data: Dict, cache_service) -> Optional[Dict]:
    """Check if a member meets MMR requirements."""
    try:
        cities_data = nation_data.get("cities", [])
        if not cities_data:
            return None
        
        city_count = len(cities_data)
        
        # Determine role: Raider (< 15 cities) or Whale (≥ 15 cities)
        role = "Whale" if city_count >= 15 else "Raider"
        
        # MMR requirements based on role
        if role == "Raider":
            # Raider: 5 Barracks, 0 Factories, 5 Hangars, 0 Drydocks per city
            required_barracks = 5
            required_factories = 0
            required_hangars = 5
            required_drydocks = 0
        else:
            # Whale: 0 Barracks, 2 Factories, 5 Hangars, 0 Drydocks per city
            required_barracks = 0
            required_factories = 2
            required_hangars = 5
            required_drydocks = 0
        
        # Check each city for compliance
        violations = []
        for i, city in enumerate(cities_data):
            city_id = city.get("id", i+1)
            barracks = city.get("barracks", 0)
            factories = city.get("factories", 0)
            hangars = city.get("hangars", 0)
            drydocks = city.get("drydocks", 0)
            
            city_violations = []
            if barracks < required_barracks:
                city_violations.append(f"Barracks: {barracks}/{required_barracks}")
            if factories < required_factories:
                city_violations.append(f"Factories: {factories}/{required_factories}")
            if hangars < required_hangars:
                city_violations.append(f"Hangars: {hangars}/{required_hangars}")
            if drydocks < required_drydocks:
                city_violations.append(f"Drydocks: {drydocks}/{required_drydocks}")
            
            if city_violations:
                violations.append(f"City {city_id}: {', '.join(city_violations)}")
        
        if violations:
            return {
                'member': member,
                'nation_data': nation_data,
                'role': role,
                'violations': violations,
                'cache_service': cache_service
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking MMR compliance for {member.get('id', 'unknown')}: {e}")
        return None

def format_mmr_violation(violation: Dict) -> str:
    """Format an MMR violation for display."""
    member = violation['member']
    nation_data = violation['nation_data']
    role = violation['role']
    violations = violation['violations']
    cache_service = violation['cache_service']
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    # Get city count properly
    cities_data = nation_data.get("cities", [])
    city_count = len(cities_data) if isinstance(cities_data, list) else cities_data
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Role:** {role}\n"
        f"**Cities:** {city_count}\n"
        f"**Violations:** {'; '.join(violations)}\n"
        f"**Discord:** {discord_username}"
    )

async def setup(bot):
    """Setup function for the cog."""
    pass
