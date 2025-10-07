"""
Main audit command that handles different audit types.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.nation_service import NationService
from services.cache_service import CacheService
from services.alliance_service import AllianceService
from api.politics_war_api import PoliticsWarAPI
from utils.logging import get_logger
from config.constants import GameConstants

logger = get_logger('audit.main')

class AuditMainCog(commands.Cog):
    """Main audit command handler."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nation_service = NationService()
        self.cache_service = CacheService()
        self.alliance_service = AllianceService()
        self.api = PoliticsWarAPI()
    
    @app_commands.command(name="audit", description="Audit alliance members for various compliance issues")
    @app_commands.describe(
        type="Audit type to run",
        cities="Maximum cities to audit (for warchest and project audits)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="activity", value="activity"),
        app_commands.Choice(name="warchest", value="warchest"),
        app_commands.Choice(name="spies", value="spies"),
        app_commands.Choice(name="projects", value="projects"),
        app_commands.Choice(name="bloc", value="bloc"),
        app_commands.Choice(name="military", value="military"),
        app_commands.Choice(name="mmr", value="mmr"),
        app_commands.Choice(name="deposit", value="deposit")
    ])
    async def audit(self, interaction: discord.Interaction, type: str, cities: int = 100):
        """Main audit command that routes to specific audit types."""
        await interaction.response.defer()
        
        try:
            if type == "activity":
                from .activity import run_activity_audit
                await run_activity_audit(interaction, self.alliance_service, self.nation_service, self.cache_service)
            elif type == "warchest":
                from .warchest import run_warchest_audit
                await run_warchest_audit(interaction, self.alliance_service, self.nation_service, self.cache_service, cities)
            elif type == "spies":
                from .spies import run_spies_audit
                await run_spies_audit(interaction, self.alliance_service, self.nation_service, self.cache_service)
            elif type == "projects":
                from .projects import run_projects_audit
                await run_projects_audit(interaction, self.alliance_service, self.nation_service, self.cache_service, 15)
            elif type == "bloc":
                from .bloc import run_bloc_audit
                await run_bloc_audit(interaction, self.alliance_service, self.nation_service, self.cache_service)
            elif type == "military":
                from .military import run_military_audit
                await run_military_audit(interaction, self.alliance_service, self.nation_service, self.cache_service)
            elif type == "mmr":
                from .mmr import run_mmr_audit
                await run_mmr_audit(interaction, self.alliance_service, self.nation_service, self.cache_service)
            elif type == "deposit":
                from .deposit import run_deposit_audit
                await run_deposit_audit(interaction, self.alliance_service, self.nation_service, self.cache_service)
            else:
                await interaction.followup.send("Invalid audit type.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in audit command: {e}")
            await interaction.followup.send("Error running audit.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(AuditMainCog(bot))
