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
            await interaction.followup.send(f"```### The Following People Need To Deposit\n{violators_text}```")
            
    except Exception as e:
        logger.error(f"Error in deposit audit: {e}")
        await interaction.followup.send("Error running deposit audit.", ephemeral=True)

async def check_deposit_compliance(member: Dict, nation_data: Dict, cache_service) -> Optional[Dict]:
    """Check if a member has excess resources that should be deposited."""
    try:
        # Import warchest service to calculate actual requirements
        from services.warchest_service import WarchestService
        warchest_service = WarchestService()
        
        # Calculate warchest requirements using the same logic as warchest audit
        warchest_result = warchest_service.calculate_warchest(nation_data)
        
        logger.info(f"Deposit audit for nation {member.get('id', 'unknown')}: warchest_result = {warchest_result}")
        
        if not warchest_result:
            logger.warning(f"No warchest result for nation {member.get('id', 'unknown')}")
            return None
        
        # Unpack the warchest result tuple: (deficits, production, requirements)
        deficits, production, requirements = warchest_result
        
        if not requirements:
            logger.warning(f"No requirements found for nation {member.get('id', 'unknown')}")
            return None
        
        # Check for excess resources (120% of required)
        excesses = []
        
        # Resource emojis for display (same as warchest command)
        resource_emojis = {
            'money': '<:money:1357103044466184412>',
            'coal': '<:coal:1357102730682040410>',
            'oil': '<:oil:1357102740391854140>',
            'uranium': '<:uranium:1357102742799126558>',
            'iron': '<:iron:1357102735488581643>',
            'bauxite': '<:bauxite:1357102729411039254>',
            'lead': '<:lead:1357102736646209536>',
            'gasoline': '<:gasoline:1357102734645399602>',
            'munitions': '<:munitions:1357102777389814012>',
            'steel': '<:steel:1357105344052072618>',
            'aluminum': '<:aluminum:1357102728391819356>',
            'food': '<:food:1357102733571784735>'
        }
        
        # Check if member is a raider (C15 and below)
        cities_data = nation_data.get("cities", [])
        if isinstance(cities_data, list):
            city_count = len(cities_data)
        else:
            city_count = cities_data
        is_raider = city_count <= 15
        
        for resource in ['money', 'coal', 'oil', 'uranium', 'iron', 'bauxite', 'lead', 'gasoline', 'munitions', 'steel', 'aluminum', 'food']:
            if resource in requirements:
                required = requirements[resource]
                current = nation_data.get(resource, 0)
                
                logger.info(f"Resource {resource}: current={current:,.0f}, required={required:,.0f}, 120% threshold={required * 1.2:,.0f}")
                
                # Special rule for raiders (C15 and below): only violate money if they have more than 40 million
                if resource == 'money' and is_raider:
                    if current > 40000000:  # 40 million
                        excess_amount = current - 40000000
                        # Apply 300 threshold filter for all deposit amounts
                        if excess_amount >= 300:
                            emoji = resource_emojis.get(resource, '')
                            excesses.append(f"{emoji} {excess_amount:,.0f}")
                            logger.info(f"EXCESS FOUND (raider money rule): {resource} - {current:,.0f} > 40,000,000 (excess: {excess_amount:,.0f})")
                        else:
                            logger.info(f"SKIPPING (under 300 threshold): {resource} - {excess_amount:,.0f} excess")
                else:
                    # Standard 120% rule for all other resources and non-raiders
                    if current > required * 1.2:
                        excess_amount = current - required
                        # Apply 300 threshold filter for all deposit amounts
                        if excess_amount >= 300:
                            emoji = resource_emojis.get(resource, '')
                            excesses.append(f"{emoji} {excess_amount:,.0f}")
                            logger.info(f"EXCESS FOUND: {resource} - {current:,.0f} > {required * 1.2:,.0f} (excess: {excess_amount:,.0f})")
                        else:
                            logger.info(f"SKIPPING (under 300 threshold): {resource} - {excess_amount:,.0f} excess")
        
        # Only return violation if there are excesses
        if excesses:
            return {
                'member': member,
                'nation_data': nation_data,
                'excesses': excesses,
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
    cache_service = violation.get('cache_service')
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    # Get city count properly
    cities_data = nation_data.get("cities", [])
    if isinstance(cities_data, list):
        city_count = len(cities_data)
    else:
        city_count = cities_data
    
    # Format excesses with resource emojis (like warchest command)
    excesses_text = "\n".join(excesses)
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Resource Excesses:**\n{excesses_text}\n"
        f"**Discord:** {discord_username}"
    )

async def setup(bot):
    """Setup function for the cog."""
    pass
