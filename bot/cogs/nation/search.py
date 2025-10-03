"""
Nation search commands.
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
from utils.logging import get_logger
from utils.formatting import format_number, format_currency
from config.constants import GameConstants

logger = get_logger('nation.search')

class NationSearchCog(commands.Cog):
    """Cog for nation search commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nation_service = NationService()
        self.cache_service = CacheService()
    
    @app_commands.command(name="chest", description="Show the current amount of resources on a nation")
    @app_commands.describe(nation_id="The nation ID to check (uses registered nation if not provided)")
    async def chest(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        """Show current resources."""
        await interaction.response.defer()
        
        try:
            # Get nation ID
            if nation_id is None:
                user_id = str(interaction.user.id)
                nation_id = self.cache_service.get_user_nation(user_id)
                if not nation_id:
                    await interaction.followup.send("❌ You need to register your nation first! Use `/register` command.", ephemeral=True)
                    return
            
            # Get nation data
            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                await interaction.followup.send("❌ Could not find nation data.", ephemeral=True)
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"📦 Resources - {nation.name}",
                description="Current resource amounts",
                color=GameConstants.EMBED_COLOR_INFO
            )
            
            # Basic resources
            basic_resources = (
                f"**Money:** {format_currency(nation.money, 0)}\n"
                f"**Credits:** {format_number(nation.credits, 0)}\n"
                f"**GDP:** {format_currency(nation.gdp, 0)}"
            )
            
            embed.add_field(
                name="💰 Basic Resources",
                value=basic_resources,
                inline=True
            )
            
            # Raw resources
            raw_resources = (
                f"**Coal:** {format_number(nation.coal, 0)}\n"
                f"**Oil:** {format_number(nation.oil, 0)}\n"
                f"**Uranium:** {format_number(nation.uranium, 0)}\n"
                f"**Iron:** {format_number(nation.iron, 0)}\n"
                f"**Bauxite:** {format_number(nation.bauxite, 0)}\n"
                f"**Lead:** {format_number(nation.lead, 0)}"
            )
            
            embed.add_field(
                name="⛏️ Raw Resources",
                value=raw_resources,
                inline=True
            )
            
            # Manufactured resources
            manufactured_resources = (
                f"**Gasoline:** {format_number(nation.gasoline, 0)}\n"
                f"**Munitions:** {format_number(nation.munitions, 0)}\n"
                f"**Steel:** {format_number(nation.steel, 0)}\n"
                f"**Aluminum:** {format_number(nation.aluminum, 0)}\n"
                f"**Food:** {format_number(nation.food, 0)}"
            )
            
            embed.add_field(
                name="🏭 Manufactured Resources",
                value=manufactured_resources,
                inline=True
            )
            
            # Nation URL
            nation_url = f"https://politicsandwar.com/nation/id={nation.id}"
            embed.add_field(
                name="🔗 Links",
                value=f"[View Nation]({nation_url})",
                inline=False
            )
            
            embed.set_footer(text="Data from Politics and War API")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in chest command: {e}")
            await interaction.followup.send("❌ An error occurred while fetching resource data.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(NationSearchCog(bot))
