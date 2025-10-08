"""
Project audit logic for checking raider project compliance.
"""

import discord
from typing import List, Dict, Optional
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logging import get_logger
from utils.pagination import ActivityPaginator
from utils.helpers import create_embed
from config import Config

config = Config()

logger = get_logger('audit.projects')

def get_discord_username_with_fallback(member: dict, cache_service) -> str:
    """Get Discord username with proper fallback order: API -> registrations -> N/A."""
    nation_id = str(member.get('id', ''))
    
    # First try API data from member (exact username from API)
    discord_username = member.get('discord', '')
    if discord_username:
        return discord_username
    
    # Then try registrations
    registrations = cache_service.load_registrations()
    for discord_id, data in registrations.items():
        if str(data.get('nation_id')) == nation_id:
            # Prefer discord_username (exact username) over discord_name (display name)
            return data.get('discord_username', data.get('discord_name', 'N/A'))
    
    # Finally return N/A
    return 'N/A'

async def run_projects_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service, max_cities: int):
    """Run project audit for raiders (C15 and below)."""
    try:
        # Get alliance members
        members = await alliance_service.get_alliance_members(config.ALLIANCE_ID)
        if not members:
            await interaction.followup.send("Could not fetch alliance members.", ephemeral=True)
            return
        
        # Filter for raiders (C15 and below)
        raiders = []
        for member in members:
            cities_data = member.get("cities", 0)
            if isinstance(cities_data, list):
                city_count = len(cities_data)
            else:
                city_count = cities_data
                
            if (member.get("alliance_position", "") != "APPLICANT" and 
                city_count <= max_cities):
                raiders.append(member)
        
        if not raiders:
            await interaction.followup.send(f"No raiders found (C{max_cities} and below).", ephemeral=True)
            return
        
        # Get detailed nation data for all raiders
        violations = []
        violators = []
        nation_ids = [str(member.get("id", 0)) for member in raiders]
        
        # Batch fetch nation data
        nations_data = await nation_service.api.get_nations_batch_data(nation_ids, "everything_scope")
        
        for member in raiders:
            nation_id = str(member.get("id", 0))
            if nation_id not in nations_data:
                continue
            
            nation_data = nations_data[nation_id]
            violation = await check_project_compliance(member, nation_data, cache_service)
            if violation:
                violations.append(violation)
                discord_username = get_discord_username_with_fallback(member, cache_service)
                violators.append(f"@{discord_username}")
        
        # Create paginated results
        if violations:
            # Format violations for display
            formatted_violations = [format_violation(violation) for violation in violations]
            paginator = ActivityPaginator(formatted_violations)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="Project Audit Complete",
                description=f"All raiders (C{max_cities} and below) are compliant with project requirements!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
        
        # Send summary with violators in codeblock
        if violators:
            violators_text = " ".join(violators)
            await interaction.followup.send(f"```### The Following People Need To Build Projects\n{violators_text}```")
            
    except Exception as e:
        logger.error(f"Error in project audit: {e}")
        await interaction.followup.send("Error running project audit.", ephemeral=True)

async def check_project_compliance(member: Dict, nation_data: Dict, cache_service) -> Optional[Dict]:
    """Check if a raider is compliant with project requirements."""
    try:
        # Get project timer status
        turns_since_last_project = nation_data.get("turns_since_last_project", 0)
        timer_up = turns_since_last_project == 0  # Timer is up if 0 turns since last project
        
        logger.info(f"Nation {member.get('id')} timer status: {turns_since_last_project} turns since last project (timer up: {timer_up})")
        
        # Get project bits to determine owned projects (same logic as /project next)
        project_bits = nation_data.get("project_bits", 0) or 0
        project_bits = int(project_bits) if project_bits else 0
        owned_projects = set()
        
        logger.info(f"Nation {member.get('id')} project_bits: {project_bits}")
        
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
                if ch == '1' and i < len(project_order):
                    owned_projects.add(project_order[i])
        
        # Use same fallback logic as /project next
        def has(name: str, fallback_attr: str) -> bool:
            if name in owned_projects:
                return True
            return bool(nation_data.get(fallback_attr, False))
        
        has_activity = has('activity_center', 'activity_center')
        has_pb = has('propaganda_bureau', 'propaganda_bureau')
        has_ia = has('central_intelligence_agency', 'central_intelligence_agency')
        has_rnd = has('research_and_development_center', 'research_and_development_center')
        has_pe = has('pirate_economy', 'pirate_economy')
        has_ape = has('advanced_pirate_economy', 'advanced_pirate_economy')
        
        # Check for Military Research Center project
        has_military_research = False
        military_research = nation_data.get('military_research', {})
        if isinstance(military_research, dict):
            # Check if any of the military research capacities are > 0
            has_military_research = any(
                military_research.get(key, 0) > 0 
                for key in ['ground_capacity', 'air_capacity', 'naval_capacity']
            )
        
        logger.info(f"Nation {member.get('id')} project status: AC={has_activity}, PB={has_pb}, IA={has_ia}, RnD={has_rnd}, PE={has_pe}, APE={has_ape}")
        
        # Update owned_projects with actual status
        owned_projects = set()
        if has_activity: owned_projects.add('activity_center')
        if has_pb: owned_projects.add('propaganda_bureau')
        if has_ia: owned_projects.add('central_intelligence_agency')
        if has_rnd: owned_projects.add('research_and_development_center')
        if has_pe: owned_projects.add('pirate_economy')
        if has_ape: owned_projects.add('advanced_pirate_economy')
        
        # Required projects in order
        required_projects = [
            "activity_center",
            "propaganda_bureau", 
            "central_intelligence_agency",
            "research_and_development_center",
            "pirate_economy",
            "advanced_pirate_economy"
        ]
        
        # Check which required projects are missing
        missing_projects = []
        for project in required_projects:
            if project not in owned_projects:
                missing_projects.append(project)
        
        logger.info(f"Nation {member.get('id')} owned projects: {list(owned_projects)}")
        logger.info(f"Nation {member.get('id')} missing projects: {missing_projects}")
        
        # Check if they have missing projects (check all raiders regardless of timer)
        if missing_projects:
            return {
                'member': member,
                'nation_data': nation_data,
                'turns_since_last_project': turns_since_last_project,
                'timer_up': timer_up,
                'missing_projects': missing_projects,
                'owned_projects': list(owned_projects),
                'cache_service': cache_service
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking project compliance for {member.get('id', 'unknown')}: {e}")
        return None

def format_violation(violation: Dict) -> str:
    """Format a project violation for display."""
    member = violation['member']
    nation_data = violation['nation_data']
    turns_since = violation['turns_since_last_project']
    missing = violation['missing_projects']
    cache_service = violation['cache_service']
    
    # Convert project names to abbreviations
    project_names = {
        "activity_center": "AC",
        "propaganda_bureau": "PB",
        "central_intelligence_agency": "IA", 
        "research_and_development_center": "RnD",
        "pirate_economy": "PE",
        "advanced_pirate_economy": "APE"
    }
    
    missing_display = [project_names.get(p, p) for p in missing]
    
    nation_url = f"https://politicsandwar.com/nation/id={member.get('id', '')}"
    discord_username = get_discord_username_with_fallback(member, cache_service)
    
    return (
        f"**Leader:** [{member.get('leader_name', 'Unknown')}]({nation_url})\n"
        f"**Nation:** {member.get('nation_name', 'Unknown')}\n"
        f"**Missing Projects:** {', '.join(missing_display)}\n"
        f"**Discord:** {discord_username}"
    )
