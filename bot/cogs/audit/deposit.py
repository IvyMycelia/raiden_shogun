"""
Deposit audit logic.
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

logger = get_logger('audit.deposit')

async def run_deposit_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service):
    """Run deposit audit logic."""
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
            violation = await check_deposit_compliance(member, nation_data, cache_service)
            if violation:
                violations.append(violation)
                discord_username = get_discord_username_with_fallback(member, cache_service)
                violators.append(f"@{discord_username}")
        
        # Create paginated results
        if violations:
            # Format violations for display
            formatted_violations = [format_deposit_violation(violation) for violation in violations]
            paginator = ActivityPaginator(formatted_violations)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="Deposit Audit Complete",
                description="All members have proper bank deposits!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
        
        # Send summary with violators in codeblock
        if violators:
            violators_text = " ".join(violators)
            await interaction.followup.send(f"```The Following People Need To Deposit: {violators_text}```")
            
    except Exception as e:
        logger.error(f"Error in deposit audit: {e}")
        await interaction.followup.send("Error running deposit audit.", ephemeral=True)

async def check_deposit_compliance(member: Dict, nation_data: Dict, cache_service) -> Optional[Dict]:
    """Check if a member has proper bank deposits."""
    try:
        # Resource thresholds (in thousands)
        thresholds = {
            "money": 100000,  # $100M
            "coal": 1000,     # 1M coal
            "oil": 1000,      # 1M oil
            "uranium": 100,   # 100k uranium
            "iron": 1000,     # 1M iron
            "bauxite": 1000,  # 1M bauxite
            "lead": 1000,     # 1M lead
            "gasoline": 100,  # 100k gasoline
            "munitions": 100, # 100k munitions
            "steel": 100,     # 100k steel
            "aluminum": 100,  # 100k aluminum
            "food": 1000,     # 1M food
            # Credits cannot be deposited, so skip
        }
        
        # Check each resource
        excesses = []
        deficits = []
        
        for resource, threshold in thresholds.items():
            current = nation_data.get(resource, 0)
            
            # Check for excess (120% threshold)
            if current > threshold * 1.2:
                excesses.append(f"{resource.title()}: {current:,.0f} (excess: {current - threshold:,.0f})")
            
            # Check for deficit (80% threshold)
            elif current < threshold * 0.8:
                deficits.append(f"{resource.title()}: {current:,.0f} (deficit: {threshold - current:,.0f})")
        
        if excesses or deficits:
            return {
                'member': member,
                'nation_data': nation_data,
                'excesses': excesses,
                'deficits': deficits,
                'cache_service': cache_service
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking deposit compliance for {member.get('id', 'unknown')}: {e}")
        return None

def format_deposit_violation(violation: Dict) -> str:
    """Format a deposit violation for display."""
    member = violation['member']
    nation_data = violation['nation_data']
    excesses = violation['excesses']
    deficits = violation['deficits']
    cache_service = violation['cache_service']
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    violations_text = []
    if excesses:
        violations_text.append(f"**Excesses:** {', '.join(excesses)}")
    if deficits:
        violations_text.append(f"**Deficits:** {', '.join(deficits)}")
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Cities:** {member.get('cities', 0)}\n"
        f"{chr(10).join(violations_text)}\n"
        f"**Discord:** {discord_username}"
    )

async def setup(bot):
    """Setup function for the cog."""
    pass
