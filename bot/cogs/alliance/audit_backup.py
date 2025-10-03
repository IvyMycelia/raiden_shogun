import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timezone
import logging

from config.settings import config
from services.alliance_service import AllianceService
from services.nation_service import NationService
from services.warchest_service import WarchestService
from services.cache_service import CacheService
from utils.pagination import ActivityPaginator
from utils.helpers import format_number
from config.constants import GameConstants

logger = logging.getLogger('raiden_shogun')

class AuditCog(commands.Cog):
    """Cog for audit-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.alliance_service = AllianceService()
        self.nation_service = NationService()
        self.warchest_service = WarchestService()
        self.cache_service = CacheService()
        
        # MMR requirements for different roles
        self.mmr_requirements = {
            "Raider": {
                "barracks": 5,
                "factory": 0,
                "hangar": 5,
                "drydock": 0
            },
            "Whale": {
                "barracks": 0,
                "factory": 2,
                "hangar": 5,
                "drydock": 0
            }
        }
        
        # Resource thresholds for deposit excess check (in thousands)
        self.deposit_thresholds = {
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
        }
        
    def check_city_mmr(self, city: dict, role: str) -> dict:
        """Check if a city meets MMR requirements for a role."""
        requirements = self.mmr_requirements[role]
        return {
            "barracks": city.get("barracks", 0) >= requirements["barracks"],
            "factory": city.get("factory", 0) >= requirements["factory"],
            "hangar": city.get("hangar", 0) >= requirements["hangar"],
            "drydock": city.get("drydock", 0) >= requirements["drydock"]
        }
    
    def check_deposit_excess(self, member: dict) -> list:
        """Check if a member has excess resources that should be deposited."""
        excess = []
        
        for resource, threshold in self.deposit_thresholds.items():
            amount = member.get(resource, 0)
            if amount > threshold:
                if resource == "money":
                    excess.append(f"💰 Money: ${amount:,.0f}")
                else:
                    excess.append(f"📦 {resource.title()}: {amount:,.0f}")
        
        return excess
    
    @app_commands.command(name="audit", description="Audit alliance members for various requirements.")
    @app_commands.describe(
        type="Type of audit to perform",
        cities="Only audit members with ≤ this many cities (for warchest)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="activity", value="activity"),
        app_commands.Choice(name="warchest", value="warchest"),
        app_commands.Choice(name="spies", value="spies"),
        app_commands.Choice(name="projects", value="projects"),
        app_commands.Choice(name="bloc", value="bloc"),
        app_commands.Choice(name="military", value="military"),
        app_commands.Choice(name="mmr", value="mmr"),
        app_commands.Choice(name="deposit", value="deposit"),
    ])
    async def audit(
        self,
        interaction: discord.Interaction,
        type: str,
        cities: int = 100
    ):
        """Audit alliance members based on different criteria."""
        # Defer immediately to prevent timeout
        await interaction.response.defer()
        
        # Send progress message
        progress_msg = await interaction.followup.send(
            embed=discord.Embed(
                title="🔍 Running Audit...",
                description=f"Performing {type} audit on alliance members. Please wait...",
                color=discord.Color.blue()
            )
        )
        
        try:
            members = await self.alliance_service.get_alliance_members(config.ALLIANCE_ID)
            if members is None:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Error Fetching Alliance Members",
                        description="Failed to fetch alliance members. Please try again later.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            audit_results = []
            current_time = time.time()
            one_day_seconds = 86400
            type = type.lower()
        
            logger.info(f"Starting Audit For {len(members)} Members Of Alliance: https://politicsandwar.com/alliance/id={config.ALLIANCE_ID}")
        
            needers = []
            summary = ""
        
            # Pre-fetch alliance color for bloc audit
            if type == "bloc":
                alliance_data = await self.alliance_service.get_alliance_data(config.ALLIANCE_ID)
                if alliance_data:
                    alliance_color = alliance_data.get('color', 'gray')
                else:
                    # Fallback: use the first member's color as reference
                    alliance_color = members[0].get('color', 'gray') if members else 'gray'
        
            for member in members:
            if member.get("alliance_position", "") != "APPLICANT":
                if type == "activity":
                    summary = "### The Following People Need To Log In"
                    
                    last_active_str = member.get("last_active", "1970-01-01T00:00:00+00:00")
                    try:
                        last_active_dt = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
                        last_active_unix = last_active_dt.timestamp()
                        
                        if (current_time - last_active_unix) >= one_day_seconds:
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                                discord_username = self.cache_service.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                f"**Last Active:** <t:{int(last_active_unix)}:F>\n"
                                    f"**Defensive Wars:** {member.get('defensive_wars_count', 0)}\n"
                                f"**Discord:** {discord_username}"
                            )
                            audit_results.append(result)
                                if discord_username != 'N/A':
                                needers.append(f"@{discord_username}")
                    except ValueError:
                            logger.error(f"Error parsing last_active for {member['leader_name']}")
                        audit_results.append(f"Error parsing last_active for {member['leader_name']}")
                
                elif type == "warchest":
                    summary = "### The Following People Need To Fix Their Warchests"
                    
                    if cities >= len(member.get("cities", [])):
                            # Use the old warchest calculation format
                            wc_result = self.warchest_service.calculate_warchest_old_format(member)
                        if wc_result is None:
                            audit_results.append(f"Error calculating warchest for {member['leader_name']}")
                            continue
                        
                        nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                            discord_username = self.cache_service.get_discord_username(member['id'])
                        header = (
                            f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                            f"**Nation:** {member['nation_name']}\n"
                                f"**Discord:** {discord_username}\n"
                        )
                        
                        deficits = []
                            if wc_result.get('money_deficit', 0) > 0.25 * wc_result.get('money_supply', 0):
                            deficits.append(f"<:money:1357103044466184412> {wc_result['money_deficit']:,.2f}\n")
                            if wc_result.get('coal_deficit', 0) > 0.25 * wc_result.get('coal_supply', 0):
                            deficits.append(f"<:coal:1357102730682040410> {wc_result['coal_deficit']:,.2f}\n")
                            if wc_result.get('oil_deficit', 0) > 0.25 * wc_result.get('oil_supply', 0):
                            deficits.append(f"<:Oil:1357102740391854140> {wc_result['oil_deficit']:,.2f}\n")
                            if wc_result.get('uranium_deficit', 0) > 0.25 * wc_result.get('uranium_supply', 0):
                            deficits.append(f"<:uranium:1357102742799126558> {wc_result['uranium_deficit']:,.2f}\n")
                            if wc_result.get('iron_deficit', 0) > 0.25 * wc_result.get('iron_supply', 0):
                            deficits.append(f"<:iron:1357102735488581643> {wc_result['iron_deficit']:,.2f}\n")
                            if wc_result.get('bauxite_deficit', 0) > 0.25 * wc_result.get('bauxite_supply', 0):
                            deficits.append(f"<:bauxite:1357102729411039254> {wc_result['bauxite_deficit']:,.2f}\n")
                            if wc_result.get('lead_deficit', 0) > 0.25 * wc_result.get('lead_supply', 0):
                            deficits.append(f"<:lead:1357102736646209536> {wc_result['lead_deficit']:,.2f}\n")
                            if wc_result.get('gasoline_deficit', 0) > 0.25 * wc_result.get('gasoline_supply', 0):
                            deficits.append(f"<:gasoline:1357102734645399602> {wc_result['gasoline_deficit']:,.2f}\n")
                            if wc_result.get('munitions_deficit', 0) > 0.25 * wc_result.get('munitions_supply', 0):
                            deficits.append(f"<:munitions:1357102777389814012> {wc_result['munitions_deficit']:,.2f}\n")
                            if wc_result.get('steel_deficit', 0) > 0.25 * wc_result.get('steel_supply', 0):
                            deficits.append(f"<:steel:1357105344052072618> {wc_result['steel_deficit']:,.2f}\n")
                            if wc_result.get('aluminum_deficit', 0) > 0.25 * wc_result.get('aluminum_supply', 0):
                            deficits.append(f"<:aluminum:1357102728391819356> {wc_result['aluminum_deficit']:,.2f}\n")
                            if wc_result.get('food_deficit', 0) > 0.25 * wc_result.get('food_supply', 0):
                            deficits.append(f"<:food:1357102733571784735> {wc_result['food_deficit']:,.2f}\n")
                            if wc_result.get('credits_deficit', 0) > 10:
                            deficits.append(f"<:credits:1357102732187537459> {wc_result['credits_deficit']:,.2f}")
                        
                        if deficits:
                            deficits_str = "".join(deficits)
                                if discord_username != 'N/A':
                                needers.append(f"@{discord_username}")
                        else:
                            deficits_str = "**All Good!** No deficits found."
                        
                        result = header + f"**Warchest Deficits:**\n{deficits_str}"
                        audit_results.append(result)
                
                elif type == "spies":
                    summary = "### The Following People Need To Fix Their Spies"
                    
                    # Load yesterday's nations data for comparison
                    from services.raid_cache_service import RaidCacheService
                    raid_cache = RaidCacheService()
                    yesterday_nations = raid_cache.load_yesterday_nations_cache()
                    
                    # Get nation data to check for Central Intelligence Agency project
                    nation_data = await self.nation_service.get_nation_data(member['id'])
                    if nation_data:
                        # Check if nation has Central Intelligence Agency project
                        has_cia = any(project.get('name') == 'Central Intelligence Agency' for project in nation_data.get('projects', []))
                        required_spies = 3 if has_cia else 2
                        
                        current_spies = member.get("spies", 0)
                        yesterday_spies = 0
                        
                        # Get yesterday's spy count if available
                        if yesterday_nations and str(member['id']) in yesterday_nations:
                            yesterday_spies = yesterday_nations[str(member['id'])].get('spies', 0)
                        
                        # Check if nation has enough spies
                        if current_spies < required_spies:
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                            discord_username = self.cache_service.get_discord_username(member['id'])
                            
                            # Determine if they bought spies
                            spy_change = current_spies - yesterday_spies
                            spy_status = ""
                            if spy_change > 0:
                                spy_status = f"✅ Bought {spy_change} spy{'s' if spy_change > 1 else ''}"
                            elif spy_change < 0:
                                spy_status = f"❌ Lost {abs(spy_change)} spy{'s' if abs(spy_change) > 1 else ''}"
                            else:
                                spy_status = "➖ No change"
                            
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                f"**Discord:** {discord_username}\n\n"
                                f"**Current Spies:** {current_spies}\n"
                                f"**Yesterday's Spies:** {yesterday_spies}\n"
                                f"**Required Spies:** {required_spies}\n"
                                f"**Has CIA Project:** {'Yes' if has_cia else 'No'}\n"
                                f"**Spy Status:** {spy_status}"
                            )
                            audit_results.append(result)
                            if discord_username != 'N/A':
                                needers.append(f"@{discord_username}")
                    
                    elif type == "projects":
                        summary = "### The Following People Need To Fix Their Projects"
                        
                        if member.get("projects", 0) < 10:
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                            discord_username = self.cache_service.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                f"**Projects:** {member.get('projects', 0)}\n"
                                f"**Discord:** {discord_username}"
                            )
                            audit_results.append(result)
                            if discord_username != 'N/A':
                                needers.append(f"@{discord_username}")
                    
                    elif type == "bloc":
                        summary = "### The Following People Need To Fix Their Color Bloc"
                        
                        # Check if member is on beige (exclude from color bloc check)
                        member_color = member.get('color', 'gray')
                        is_beige = member_color.lower() == 'beige'
                        
                        # Check if member's color matches alliance color
                        if not is_beige and member_color.lower() != alliance_color.lower():
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                            discord_username = self.cache_service.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                f"**Current Color:** {member_color.title()}\n"
                                f"**Alliance Color:** {alliance_color.title()}\n"
                                f"**Discord:** {discord_username}"
                            )
                            audit_results.append(result)
                            if discord_username != 'N/A':
                                needers.append(f"@{discord_username}")
                    
                    elif type == "military":
                        summary = "### The Following People Need To Fix Their Military"
                        
                        # Calculate military capacity and usage
                        cities = member.get("cities", [])
                        if cities:
                            capacity = self.alliance_service.calculate_military_capacity(cities)
                            current = {
                                'soldiers': member.get('soldiers', 0),
                                'tanks': member.get('tanks', 0),
                                'aircraft': member.get('aircraft', 0),
                                'ships': member.get('ships', 0)
                            }
                            
                            issues = []
                            if current['soldiers'] > capacity['soldiers'] * 0.9:
                                issues.append(f"High soldier usage: {current['soldiers']:,}/{capacity['soldiers']:,}")
                            elif current['soldiers'] < capacity['soldiers'] * 0.1:
                                issues.append(f"Low soldier usage: {current['soldiers']:,}/{capacity['soldiers']:,}")
                            
                            if issues:
                                nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                                discord_username = self.cache_service.get_discord_username(member['id'])
                                
                                issues_text = "\n".join([f"• {issue}" for issue in issues])
                                military_text = f"**Current:** {current['soldiers']:,} Soldiers, {current['tanks']:,} Tanks, {current['aircraft']:,} Aircraft, {current['ships']:,} Ships"
                                capacity_text = f"**Capacity:** {capacity['soldiers']:,} Soldiers, {capacity['tanks']:,} Tanks, {capacity['aircraft']:,} Aircraft, {capacity['ships']:,} Ships"
                                
                                result = (
                                    f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                    f"**Nation:** {member['nation_name']}\n"
                                    f"**Discord:** {discord_username}\n\n"
                                    f"{military_text}\n{capacity_text}\n\n"
                                    f"**Usage Issues:**\n{issues_text}"
                                )
                                audit_results.append(result)
                                if discord_username != 'N/A':
                            needers.append(f"@{discord_username}")
                
                elif type == "mmr":
                    summary = "### The Following People Need To Fix Their MMR"
                    
                    # Get city data for MMR check
                        cities = member.get("cities", [])
                        if cities:
                    role = "Whale" if len(cities) >= 15 else "Raider"
                    
                    # Check MMR requirements
                    mmr_violations = []
                    for city in cities:
                        mmr_status = self.check_city_mmr(city, role)
                        if not all(mmr_status.values()):
                            city_name = city.get("name", "Unknown")
                            missing = []
                            if not mmr_status["barracks"]:
                                missing.append(f"Barracks: {city.get('barracks', 0)}/{self.mmr_requirements[role]['barracks']}")
                            if not mmr_status["factory"]:
                                missing.append(f"Factory: {city.get('factory', 0)}/{self.mmr_requirements[role]['factory']}")
                            if not mmr_status["hangar"]:
                                missing.append(f"Hangar: {city.get('hangar', 0)}/{self.mmr_requirements[role]['hangar']}")
                            if not mmr_status["drydock"]:
                                missing.append(f"Drydock: {city.get('drydock', 0)}/{self.mmr_requirements[role]['drydock']}")
                            mmr_violations.append(f"{city_name}: {', '.join(missing)}")
                    
                    if mmr_violations:
                                nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                                discord_username = self.cache_service.get_discord_username(member['id'])
                        result = (
                            f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                            f"**Nation:** {member['nation_name']}\n"
                            f"**Role:** {role}\n"
                                    f"**Discord:** {discord_username}\n\n"
                            + "\n".join(mmr_violations)
                        )
                        audit_results.append(result)
                                if discord_username != 'N/A':
                            needers.append(f"@{discord_username}")
                
                elif type == "deposit":
                    summary = "### The Following People Need To Deposit Resources"
                    
                    # Only check nations with city count <= specified limit
                    if cities >= len(member.get("cities", [])):
                        excess = self.check_deposit_excess(member)
                        if excess:
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                                discord_username = self.cache_service.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                    f"**Discord:** {discord_username}\n\n"
                                f"**Excess Resources:**\n" + "\n".join(excess)
                            )
                            audit_results.append(result)
                                if discord_username != 'N/A':
                                needers.append(f"@{discord_username}")
        
            # Update progress message with results
            if audit_results:
        paginator = ActivityPaginator(audit_results)
                await progress_msg.edit(embed=paginator.get_embed(), view=paginator)
            else:
                # No violations found
                embed = discord.Embed(
                    title="✅ Audit Complete",
                    description=f"No violations found for {type} audit!",
                    color=discord.Color.green()
                )
                await progress_msg.edit(embed=embed)
            
            # Send summary with violators
            if needers:
                summary = f"### The Following People Need To Fix Their {type.title()}\n" + " ".join(needers)
                await interaction.followup.send(f"```{summary}```")
            else:
                await interaction.followup.send(f"```### The Following People Need To Fix Their {type.title()}\nNo Violators!```")
            
        except Exception as e:
            logger.error(f"Error in audit command: {e}")
            await progress_msg.edit(embed=discord.Embed(
                title="❌ Audit Error",
                description="An error occurred while performing the audit.",
                color=GameConstants.EMBED_COLOR_ERROR
            ))

    @app_commands.command(name="audit_member", description="Audit a specific alliance member for all requirements")
    @app_commands.describe(nation_id="The ID of the nation to audit")
    async def audit_member(self, interaction: discord.Interaction, nation_id: int):
        """Audit a specific alliance member."""
        await interaction.response.defer()
        
        try:
            # Get alliance members
            members = await self.alliance_service.get_alliance_members(config.ALLIANCE_ID)
            if members is None:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Error",
                        description="Failed to fetch alliance members.",
                        color=GameConstants.EMBED_COLOR_ERROR
                    ),
                    ephemeral=True
                )
                return
            
            # Find the specific member
            member = next((m for m in members if int(m['id']) == nation_id), None)
            if not member:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Member Not Found",
                        description=f"Could not find nation {nation_id} in alliance.",
                        color=GameConstants.EMBED_COLOR_ERROR
                    ),
                    ephemeral=True
                )
                return
            
            # Run all audit types on this member
            audit_results = []
            current_time = time.time()
            one_day_seconds = 86400
            
            # Activity audit
            last_active_str = member.get("last_active", "1970-01-01T00:00:00+00:00")
            try:
                last_active_dt = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
                last_active_unix = last_active_dt.timestamp()
                
                if (current_time - last_active_unix) >= one_day_seconds:
                    audit_results.append("❌ **Activity:** Inactive for more than 24 hours")
                else:
                    audit_results.append("✅ **Activity:** Active within 24 hours")
            except ValueError:
                audit_results.append("❌ **Activity:** Error parsing last active time")
            
            # Spies audit
            nation_data = await self.nation_service.get_nation_data(member['id'])
            if nation_data:
                # Check for Central Intelligence Agency project
                has_cia = any(project.get('name') == 'Central Intelligence Agency' for project in nation_data.get('projects', []))
                required_spies = 3 if has_cia else 2
                current_spies = member.get('spies', 0)
                
                # Load yesterday's data for comparison
                from services.raid_cache_service import RaidCacheService
                raid_cache = RaidCacheService()
                yesterday_nations = raid_cache.load_yesterday_nations_cache()
                yesterday_spies = 0
                
                if yesterday_nations and str(member['id']) in yesterday_nations:
                    yesterday_spies = yesterday_nations[str(member['id'])].get('spies', 0)
                
                # Determine spy change status
                spy_change = current_spies - yesterday_spies
                if spy_change > 0:
                    spy_status = f" (Bought {spy_change} spy{'s' if spy_change > 1 else ''})"
                elif spy_change < 0:
                    spy_status = f" (Lost {abs(spy_change)} spy{'s' if abs(spy_change) > 1 else ''})"
                else:
                    spy_status = " (No change)"
                
                if current_spies >= required_spies:
                    audit_results.append(f"✅ **Spies:** {current_spies}/{required_spies} (CIA: {'Yes' if has_cia else 'No'}){spy_status}")
                else:
                    audit_results.append(f"❌ **Spies:** {current_spies}/{required_spies} (CIA: {'Yes' if has_cia else 'No'}){spy_status}")
            else:
                audit_results.append("❌ **Spies:** Could not fetch nation data")
            
            # Projects audit
            current_projects = member.get('projects', 0)
            if current_projects >= 10:
                audit_results.append(f"✅ **Projects:** {current_projects}/10")
            else:
                audit_results.append(f"❌ **Projects:** {current_projects}/10")
            
            # Color bloc audit
            alliance_data = await self.alliance_service.get_alliance_data(config.ALLIANCE_ID)
            alliance_color = alliance_data.get('color', 'gray') if alliance_data else 'gray'
            member_color = member.get('color', 'gray')
            is_beige = member_color.lower() == 'beige'
            
            if is_beige or member_color.lower() == alliance_color.lower():
                audit_results.append(f"✅ **Color Bloc:** {member_color.title()} (Alliance: {alliance_color.title()})")
            else:
                audit_results.append(f"❌ **Color Bloc:** {member_color.title()} (Alliance: {alliance_color.title()})")
            
            # MMR audit
            cities = member.get("cities", [])
            if cities:
                role = "Whale" if len(cities) >= 15 else "Raider"
                mmr_violations = []
                for city in cities:
                    mmr_status = self.check_city_mmr(city, role)
                    if not all(mmr_status.values()):
                        city_name = city.get("name", "Unknown")
                        missing = []
                        if not mmr_status["barracks"]:
                            missing.append(f"Barracks: {city.get('barracks', 0)}/{self.mmr_requirements[role]['barracks']}")
                        if not mmr_status["factory"]:
                            missing.append(f"Factory: {city.get('factory', 0)}/{self.mmr_requirements[role]['factory']}")
                        if not mmr_status["hangar"]:
                            missing.append(f"Hangar: {city.get('hangar', 0)}/{self.mmr_requirements[role]['hangar']}")
                        if not mmr_status["drydock"]:
                            missing.append(f"Drydock: {city.get('drydock', 0)}/{self.mmr_requirements[role]['drydock']}")
                        mmr_violations.append(f"{city_name}: {', '.join(missing)}")
                
                if mmr_violations:
                    audit_results.append(f"❌ **MMR ({role}):** " + "; ".join(mmr_violations))
                else:
                    audit_results.append(f"✅ **MMR ({role}):** All requirements met")
            else:
                audit_results.append("❌ **MMR:** No city data available")
            
            # Deposit audit
            excess = self.check_deposit_excess(member)
            if excess:
                audit_results.append(f"❌ **Deposits:** " + "; ".join(excess))
            else:
                audit_results.append("✅ **Deposits:** No excess resources")
            
            # Create embed
            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
            discord_username = self.cache_service.get_discord_username(member['id'])
            
            embed = discord.Embed(
                title=f"🔍 Audit Results for {member['nation_name']}",
                description=f"**Leader:** [{member['leader_name']}]({nation_url})\n**Discord:** {discord_username}",
                color=GameConstants.EMBED_COLOR_INFO
            )
            
            for result in audit_results:
                embed.add_field(name="\u200b", value=result, inline=False)
            
            await interaction.followup.send(embed=embed)
    
        except Exception as e:
            logger.error(f"Error in audit_member command: {e}")
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description="An error occurred while performing the audit.",
                    color=GameConstants.EMBED_COLOR_ERROR
                ),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    """Set up the audit cog."""
    await bot.add_cog(AuditCog(bot)) 