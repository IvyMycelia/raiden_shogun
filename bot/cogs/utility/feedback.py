"""
Feedback and user management commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.cache_service import CacheService
from utils.logging import get_logger
from utils.validation import validate_nation_id
from config.constants import GameConstants

logger = get_logger('utility.feedback')

class FeedbackCog(commands.Cog):
    """Cog for feedback and user management commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache_service = CacheService()
    
    @app_commands.command(name="register", description="Register your Politics and War nation with your Discord account")
    @app_commands.describe(nation_id="Your Politics and War nation ID")
    async def register(self, interaction: discord.Interaction, nation_id: int):
        """Register user with their nation."""
        try:
            # Validate nation ID
            if not validate_nation_id(nation_id):
                await interaction.response.send_message("❌ Invalid nation ID.", ephemeral=True)
                return
            
            # Check if nation exists (basic validation)
            from services.nation_service import NationService
            nation_service = NationService()
            nation = await nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                await interaction.response.send_message("❌ Nation not found. Please check your nation ID.", ephemeral=True)
                return
            
            # Register user
            user_id = str(interaction.user.id)
            discord_name = interaction.user.display_name
            nation_name = nation.name
            
            self.cache_service.register_user(user_id, nation_id, discord_name, nation_name)
            
            embed = discord.Embed(
                title="✅ Registration Successful",
                description=f"Successfully registered {nation_name} (ID: {nation_id}) to your Discord account.",
                color=GameConstants.EMBED_COLOR_SUCCESS
            )
            
            embed.add_field(
                name="🔗 Links",
                value=f"[View Nation](https://politicsandwar.com/nation/id={nation_id})",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in register command: {e}")
            await interaction.response.send_message("❌ An error occurred during registration.", ephemeral=True)
    
    @app_commands.command(name="suggest", description="Suggest something to the bot")
    @app_commands.describe(suggestion="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        """Submit a suggestion."""
        try:
            # Validate input
            if not suggestion or len(suggestion) > 1000:
                await interaction.response.send_message("❌ Suggestion must be between 1 and 1000 characters.", ephemeral=True)
                return
            
            # Store suggestion (in a real implementation, this would go to a database)
            logger.info(f"Suggestion from {interaction.user}: {suggestion}")
            
            embed = discord.Embed(
                title="💡 Suggestion Submitted",
                description="Thank you for your suggestion! It has been recorded and will be reviewed.",
                color=GameConstants.EMBED_COLOR_SUCCESS
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in suggest command: {e}")
            await interaction.response.send_message("❌ An error occurred while submitting your suggestion.", ephemeral=True)
    
    @app_commands.command(name="report-a-bug", description="Report a bug to the bot")
    @app_commands.describe(report="The bug description")
    async def report_bug(self, interaction: discord.Interaction, report: str):
        """Report a bug."""
        try:
            # Validate input
            if not report or len(report) > 1000:
                await interaction.response.send_message("❌ Bug report must be between 1 and 1000 characters.", ephemeral=True)
                return
            
            # Store bug report (in a real implementation, this would go to a database)
            logger.error(f"Bug report from {interaction.user}: {report}")
            
            embed = discord.Embed(
                title="🐛 Bug Report Submitted",
                description="Thank you for reporting this bug! It has been recorded and will be investigated.",
                color=GameConstants.EMBED_COLOR_WARNING
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in report_bug command: {e}")
            await interaction.response.send_message("❌ An error occurred while submitting your bug report.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(FeedbackCog(bot)) 