"""
Bloc audit logic.
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

logger = get_logger('audit.bloc')

async def run_bloc_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service):
    """Run bloc audit logic."""
    try:
        # Get alliance members
        members = await alliance_service.get_alliance_members(config.ALLIANCE_ID)
        if not members:
            await interaction.followup.send("Could not fetch alliance members.", ephemeral=True)
            return
        
        # Get alliance data to determine required color
        try:
            alliance_data = await alliance_service.get_alliance(config.ALLIANCE_ID)
            if not alliance_data:
                logger.error(f"Failed to fetch alliance data for ID: {config.ALLIANCE_ID}")
                await interaction.followup.send("Could not fetch alliance data.", ephemeral=True)
                return
        except Exception as e:
            logger.error(f"Error fetching alliance data: {e}")
            await interaction.followup.send("Error fetching alliance data.", ephemeral=True)
            return
        
        alliance_color = alliance_data.color.lower() if alliance_data.color else ""
        if not alliance_color:
            await interaction.followup.send("Could not determine alliance color.", ephemeral=True)
            return
        
        # Filter for non-applicants
        filtered_members = []
        for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                filtered_members.append(member)
        
        if not filtered_members:
            await interaction.followup.send("No members found to audit.", ephemeral=True)
            return
        
        violations = []
        violators = []
        
        for member in filtered_members:
            violation = await check_bloc_compliance(member, alliance_color, cache_service)
            if violation:
                violations.append(violation)
                discord_username = get_discord_username_with_fallback(member, cache_service)
                violators.append(f"@{discord_username}")
        
        # Create paginated results
        if violations:
            # Format violations for display
            formatted_violations = [format_bloc_violation(violation) for violation in violations]
            paginator = ActivityPaginator(formatted_violations)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="Bloc Audit Complete",
                description=f"All members are in the correct {alliance_color} bloc!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
        
        # Send summary with violators in codeblock
        if violators:
            violators_text = " ".join(violators)
            await interaction.followup.send(f"```### The Following People Need To Change Color\n{violators_text}```")
            
    except Exception as e:
        logger.error(f"Error in bloc audit: {e}")
        await interaction.followup.send("Error running bloc audit.", ephemeral=True)

async def check_bloc_compliance(member: Dict, alliance_color: str, cache_service) -> Optional[Dict]:
    """Check if a member is in the correct color bloc."""
    try:
        member_color = member.get("color", "").lower()
        
        # Skip beige nations
        if member_color == "beige":
            return None
        
        # Check if member color matches alliance color
        if member_color != alliance_color:
            return {
                'member': member,
                'alliance_color': alliance_color,
                'member_color': member_color,
                'cache_service': cache_service
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking bloc compliance for {member.get('id', 'unknown')}: {e}")
        return None

def format_bloc_violation(violation: Dict) -> str:
    """Format a bloc violation for display."""
    member = violation['member']
    alliance_color = violation['alliance_color']
    member_color = violation['member_color']
    cache_service = violation['cache_service']
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Current Color:** {member_color.title()}\n"
        f"**Required Color:** {alliance_color.title()}\n"
        f"**Discord:** {discord_username}"
    )

async def setup(bot):
    """Setup function for the cog."""
    pass