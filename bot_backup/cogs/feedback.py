import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

from bot.utils.config import config
from bot.utils.helpers import create_embed
from bot.handler import info, error, warning
from bot import db as dataBase

class FeedbackCog(commands.Cog):
    """Cog for feedback-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
    
    @app_commands.command(name="suggest", description="Suggest Something To The Bot! (Please Only Suggest One Thing At A Time)")
    @app_commands.describe(suggestion="Your suggestion.")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        """Submit a suggestion to the bot."""
        try:
            embed = create_embed(
                title="Suggestion Received",
                description=f"From: {interaction.user.mention}\n",
                color=discord.Color.green(),
                fields=[{"name": "Suggestion", "value": suggestion, "inline": False}]
            )
            
            channel = self.bot.get_channel(self.config.SUGGESTIONS_CHANNEL_ID)
            if channel is None:
                await interaction.response.send_message("Suggestion channel not found. Please try again later.", ephemeral=True)
                return
            
            await channel.send(
                embed=embed,
                content=f"<@&{self.config.DEVELOPER_ROLE_ID}>",
                allowed_mentions=discord.AllowedMentions(roles=True)
            )
            await interaction.response.send_message("Your suggestion has been sent!", ephemeral=True)
            
            suggestion_data = {
                "user_id": interaction.user.id,
                "username": str(interaction.user),
                "suggestion": suggestion,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            dataBase.insert(suggestion_data, 'suggestions')
            
        except Exception as e:
            error(f"Error while processing suggestion: {e}", tag="SUGGESTION")
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="report-a-bug", description="Report A Bug To The Bot! (Please Only Report One Bug At A Time)")
    @app_commands.describe(report="The Bug.")
    async def report(self, interaction: discord.Interaction, report: str):
        """Submit a bug report to the bot."""
        try:
            embed = create_embed(
                title="Bug Report Received",
                description=f"From: {interaction.user.mention}\n",
                color=discord.Color.red(),
                fields=[{"name": "Bug Report", "value": report, "inline": False}]
            )
            
            channel = self.bot.get_channel(self.config.BUG_REPORTS_CHANNEL_ID)
            if channel is None:
                await interaction.response.send_message("Bug Reports channel not found. Please try again later.", ephemeral=True)
                return
            
            await channel.send(
                embed=embed,
                content=f"<@&{self.config.DEVELOPER_ROLE_ID}>",
                allowed_mentions=discord.AllowedMentions(roles=True)
            )
            await interaction.response.send_message("Your report has been sent!", ephemeral=True)
            
            report_data = {
                "user_id": interaction.user.id,
                "username": str(interaction.user),
                "bug_report": report,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            dataBase.insert(report_data, 'bug_reports')
            
        except Exception as e:
            error(f"Error while processing bug report: {e}", tag="BUG_REPORT")
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    """Set up the feedback cog."""
    await bot.add_cog(FeedbackCog(bot)) 