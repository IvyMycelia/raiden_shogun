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
                    if type == "spies":
                        summary = "### The Following People Need To Fix Their Spies"
                        
                        # Load yesterday's nations data for comparison
                        from services.raid_cache_service import RaidCacheService
                        raid_cache = RaidCacheService()
                        yesterday_nations = raid_cache.load_yesterday_nations_cache()
                        
                        # Get nation data to check for Central Intelligence Agency project
                        nation = await self.nation_service.get_nation(member['id'])
                        if nation:
                            # Check if nation has Central Intelligence Agency project
                            has_cia = nation.central_intelligence_agency
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
            
            # Create paginator if there are results
            if audit_results:
                paginator = ActivityPaginator(audit_results)
                await interaction.followup.send(embed=paginator.get_embed(), view=paginator)
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="✅ Audit Complete",
                        description=f"No issues found in {type} audit!",
                        color=discord.Color.green()
                    )
                )
                
        except Exception as e:
            logger.error(f"Error in audit command: {e}")
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Audit Error",
                    description=f"An error occurred during the audit: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(AuditCog(bot))
