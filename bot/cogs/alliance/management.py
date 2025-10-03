"""
Alliance management commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.alliance_service import AllianceService
from utils.logging import get_logger
from utils.formatting import format_number, format_currency
from config.constants import GameConstants

logger = get_logger('alliance.management')

class AllianceManagementCog(commands.Cog):
    """Cog for alliance management commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.alliance_service = AllianceService()
    
    @app_commands.command(name="bank", description="Check alliance bank balance")
    async def bank(self, interaction: discord.Interaction):
        """Check alliance bank."""
        await interaction.response.defer()
        
        try:
            # Get alliance data
            alliance = await self.alliance_service.get_alliance(13033)  # Replace with actual alliance ID
            if not alliance:
                await interaction.followup.send("❌ Could not find alliance data.", ephemeral=True)
                return
            
            # Get bank resources
            bank_resources = alliance.get_bank_resources()
            
            # Create embed
            embed = discord.Embed(
                title=f"🏦 {alliance.name} Bank",
                description=f"**Total Value:** {format_currency(alliance.get_bank_value(), 0)}",
                color=GameConstants.EMBED_COLOR_INFO
            )
            
            # Resource breakdown
            resource_text = ""
            for resource, amount in bank_resources.items():
                if amount > 0:
                    resource_text += f"**{resource.title()}:** {format_number(amount, 0)}\n"
            
            if resource_text:
                embed.add_field(
                    name="💰 Resources",
                    value=resource_text,
                    inline=True
                )
            
            # Alliance info
            embed.add_field(
                name="📊 Alliance Info",
                value=(
                    f"**Members:** {alliance.get_member_count()}\n"
                    f"**Score:** {format_number(alliance.score, 0)}\n"
                    f"**Color:** {alliance.color.title()}\n"
                    f"**Acronym:** {alliance.acronym}"
                ),
                inline=True
            )
            
            embed.set_footer(text="Data from Politics and War API")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in bank command: {e}")
            await interaction.followup.send("❌ An error occurred while fetching bank data.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(AllianceManagementCog(bot))
