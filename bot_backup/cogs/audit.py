from typing import List, Optional, Dict
import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timezone, timedelta

from bot.utils.config import config
from bot.utils.paginator import ActivityPaginator, GridPaginator, PaginatorView
from bot.utils.helpers import create_embed, format_number
from bot.handler import info, error, warning
from bot import data as get_data
from bot import calculate
from bot import vars
import json
import os

class AuditCog(commands.Cog):
    """Cog for audit-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
        
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
        
        # Load registered nations data
        self.registrations_file = "data/registrations.json"
        self.registered_nations = self.load_registered_nations()
    
    def load_registered_nations(self) -> Dict:
        """Load registered nations data from JSON file."""
        try:
            if os.path.exists(self.registrations_file):
                with open(self.registrations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            error(f"Error loading registered nations: {e}", tag="AUDIT")
            return {}
    
    def get_discord_username(self, nation_id: str) -> str:
        """Get Discord username from registered nations data."""
        for discord_id, data in self.registered_nations.items():
            if str(data.get('nation_id')) == str(nation_id):
                return data.get('discord_name', 'N/A')
        return 'N/A'
    
    def check_city_mmr(self, city: Dict, role: str) -> Dict[str, bool]:
        """Check if a city meets MMR requirements for a role."""
        requirements = self.mmr_requirements[role]
        return {
            "barracks": city.get("barracks", 0) >= requirements["barracks"],
            "factory": city.get("factory", 0) >= requirements["factory"],
            "hangar": city.get("hangar", 0) >= requirements["hangar"],
            "drydock": city.get("drydock", 0) >= requirements["drydock"]
        }
    
    def check_deposit_excess(self, member: Dict) -> List[str]:
        """Check if a member has excess resources that should be deposited."""
        excess = []
        resources = member.get("resources", {})
        
        for resource, threshold in self.deposit_thresholds.items():
            amount = resources.get(resource, 0)
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
            embed=create_embed(
                title="🔍 Running Audit...",
                description=f"Performing {type} audit on alliance members. Please wait...",
                color=discord.Color.blue()
            )
        )
        
        try:
            members = get_data.GET_ALLIANCE_MEMBERS(self.config.ALLIANCE_ID, self.config.API_KEY)
            if members is None:
                await interaction.followup.send(
                    embed=create_embed(
                        title=":warning: Error Fetching Alliance Members",
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
        
            info(f"Starting Audit For {len(members)} Members Of Alliance: https://politicsandwar.com/alliance/id={self.config.ALLIANCE_ID}")
        
            need_login = []
            needers = []
            summary = []
        
            # Pre-fetch alliance color for bloc audit
            if type == "bloc":
                alliance_data = get_data.GET_ALLIANCE_DATA(self.config.ALLIANCE_ID, self.config.API_KEY)
                if alliance_data:
                    self.alliance_color = alliance_data.get('color', 'gray')
                else:
                    # Fallback: use the first member's color as reference
                    self.alliance_color = members[0].get('color', 'gray') if members else 'gray'
        
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
                                discord_username = self.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                f"**Last Active:** <t:{int(last_active_unix)}:F>\n"
                                f"**Defensive Wars:** {member['defensive_wars_count']}\n"
                                f"**Discord:** {discord_username}"
                            )
                            audit_results.append(result)
                                needers.append(f"@{discord_username}")
                    except ValueError:
                        error(f"Error parsing last_active for {member['leader_name']}", tag="AUDIT")
                        audit_results.append(f"Error parsing last_active for {member['leader_name']}")
                
                elif type == "warchest":
                    summary = "### The Following People Need To Fix Their Warchests"
                    
                    if cities >= len(member.get("cities", [])):
                        wc_result, _, wc_supply = calculate.warchest(member, vars.COSTS, vars.MILITARY_COSTS)
                        if wc_result is None:
                            audit_results.append(f"Error calculating warchest for {member['leader_name']}")
                            continue
                        
                        nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                        header = (
                            f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                            f"**Nation:** {member['nation_name']}\n"
                                f"**Discord:** {self.get_discord_username(member['id'])}\n"
                        )
                        
                        deficits = []
                        if wc_result['money_deficit'] > 0.25 * wc_supply['money']:
                            deficits.append(f"<:money:1357103044466184412> {wc_result['money_deficit']:,.2f}\n")
                        if wc_result['coal_deficit'] > 0.25 * wc_supply['coal']:
                            deficits.append(f"<:coal:1357102730682040410> {wc_result['coal_deficit']:,.2f}\n")
                        if wc_result['oil_deficit'] > 0.25 * wc_supply['oil']:
                            deficits.append(f"<:Oil:1357102740391854140> {wc_result['oil_deficit']:,.2f}\n")
                        if wc_result['uranium_deficit'] > 0.25 * wc_supply['uranium']:
                            deficits.append(f"<:uranium:1357102742799126558> {wc_result['uranium_deficit']:,.2f}\n")
                        if wc_result['iron_deficit'] > 0.25 * wc_supply['iron']:
                            deficits.append(f"<:iron:1357102735488581643> {wc_result['iron_deficit']:,.2f}\n")
                        if wc_result['bauxite_deficit'] > 0.25 * wc_supply['bauxite']:
                            deficits.append(f"<:bauxite:1357102729411039254> {wc_result['bauxite_deficit']:,.2f}\n")
                        if wc_result['lead_deficit'] > 0.25 * wc_supply['lead']:
                            deficits.append(f"<:lead:1357102736646209536> {wc_result['lead_deficit']:,.2f}\n")
                        if wc_result['gasoline_deficit'] > 0.25 * wc_supply['gasoline']:
                            deficits.append(f"<:gasoline:1357102734645399602> {wc_result['gasoline_deficit']:,.2f}\n")
                        if wc_result['munitions_deficit'] > 0.25 * wc_supply['munitions']:
                            deficits.append(f"<:munitions:1357102777389814012> {wc_result['munitions_deficit']:,.2f}\n")
                        if wc_result['steel_deficit'] > 0.25 * wc_supply['steel']:
                            deficits.append(f"<:steel:1357105344052072618> {wc_result['steel_deficit']:,.2f}\n")
                        if wc_result['aluminum_deficit'] > 0.25 * wc_supply['aluminum']:
                            deficits.append(f"<:aluminum:1357102728391819356> {wc_result['aluminum_deficit']:,.2f}\n")
                        if wc_result['food_deficit'] > 0.25 * wc_supply['food']:
                            deficits.append(f"<:food:1357102733571784735> {wc_result['food_deficit']:,.2f}\n")
                        if wc_result['credits_deficit'] > 10:
                            deficits.append(f"<:credits:1357102732187537459> {wc_result['credits_deficit']:,.2f}")
                        
                        if deficits:
                            deficits_str = "".join(deficits)
                                discord_username = self.get_discord_username(member['id'])
                                needers.append(f"@{discord_username}")
                        else:
                            deficits_str = "**All Good!** No deficits found."
                        
                        result = header + f"**Warchest Deficits:**\n{deficits_str}"
                        audit_results.append(result)
                
                elif type == "spies":
                        summary = "### The Following People Need To Fix Their Spies"
                    
                    # Get nation data to check for Intelligence Agency project
                        nation_data = get_data.GET_NATION_DATA(member['id'], self.config.API_KEY)
                        if nation_data:
                    # Check if nation has Intelligence Agency project
                    has_intel_agency = any(project.get('name') == 'Intelligence Agency' for project in nation_data.get('projects', []))
                    required_spies = 60 if has_intel_agency else 50
                    
                    # Check if nation has enough spies
                    if member.get("spies", 0) < required_spies:
                        nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                                discord_username = self.get_discord_username(member['id'])
                        result = (
                            f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                            f"**Nation:** {member['nation_name']}\n"
                                    f"**Discord:** {discord_username}\n\n"
                            f"**Current Spies:** {member.get('spies', 0)}\n"
                            f"**Required Spies:** {required_spies}\n"
                            f"**Has Intelligence Agency:** {'Yes' if has_intel_agency else 'No'}"
                        )
                        audit_results.append(result)
                                needers.append(f"@{discord_username}")
                    
                    elif type == "projects":
                        summary = "### The Following People Need To Fix Their Projects"
                        
                        if member.get("projects", 0) < 10:
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                            discord_username = self.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                f"**Projects:** {member.get('projects', 0)}\n"
                                f"**Discord:** {discord_username}"
                            )
                            audit_results.append(result)
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
                                discord_username = self.get_discord_username(member['id'])
                        result = (
                            f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                            f"**Nation:** {member['nation_name']}\n"
                            f"**Role:** {role}\n"
                                    f"**Discord:** {discord_username}\n\n"
                            + "\n".join(mmr_violations)
                        )
                        audit_results.append(result)
                                needers.append(f"@{discord_username}")
                    
                    elif type == "bloc":
                        summary = "### The Following People Need To Fix Their Color Bloc"
                        
                        # Check if member is on beige (exclude from color bloc check)
                        member_color = member.get('color', 'gray')
                        is_beige = member_color.lower() == 'beige'
                        
                        # Check if member's color matches alliance color
                        if not is_beige and member_color.lower() != self.alliance_color.lower():
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                            discord_username = self.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                f"**Current Color:** {member_color.title()}\n"
                                f"**Alliance Color:** {self.alliance_color.title()}\n"
                                f"**Discord:** {discord_username}"
                            )
                            audit_results.append(result)
                            needers.append(f"@{discord_username}")
                
                elif type == "deposit":
                    summary = "### The Following People Need To Deposit Resources"
                    
                    # Only check nations with city count <= specified limit
                    if cities >= len(member.get("cities", [])):
                        excess = self.check_deposit_excess(member)
                        if excess:
                            nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                                discord_username = self.get_discord_username(member['id'])
                            result = (
                                f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                                f"**Nation:** {member['nation_name']}\n"
                                    f"**Discord:** {discord_username}\n\n"
                                f"**Excess Resources:**\n" + "\n".join(excess)
                            )
                            audit_results.append(result)
                                needers.append(f"@{discord_username}")
        
            # Update progress message with results
            if audit_results:
        paginator = ActivityPaginator(audit_results)
                await progress_msg.edit(embed=paginator.get_embed(), view=paginator)
            else:
                # No violations found
                embed = create_embed(
                    title="✅ Audit Complete",
                    description=f"No violations found for {type} audit!",
                    color=discord.Color.green()
                )
                await progress_msg.edit(embed=embed)
            
            # Send summary with violators
            if needers:
                await interaction.followup.send(
                    f"```{summary}\n" + f"{needers}" + "```".replace("'", "").replace("[", "").replace("]", "").replace(",", "")
                )
            else:
        await interaction.followup.send(
                    f"```{summary}\nNo Violators!```"
        )
        
        info(f"Audit completed for {len(members)} members of alliance: {self.config.ALLIANCE_ID}", tag="AUDIT")
    
        except Exception as e:
            error(f"Error in audit command: {e}", tag="AUDIT")
            try:
                await progress_msg.edit(
                    embed=create_embed(
                        title="❌ Audit Error",
                        description="An error occurred while performing the audit. Please try again later.",
                        color=discord.Color.red()
                    )
                )
            except:
                pass

async def setup(bot: commands.Bot):
    """Set up the audit cog."""
    await bot.add_cog(AuditCog(bot)) 