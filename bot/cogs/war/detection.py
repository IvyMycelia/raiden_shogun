"""
War detection commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.war_service import WarService
from services.nation_service import NationService
from utils.logging import get_logger
from utils.formatting import format_number
from config.constants import GameConstants

logger = get_logger('war.detection')

class WarDetectionCog(commands.Cog):
    """Cog for war detection commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.war_service = WarService()
        self.nation_service = NationService()
    
    @app_commands.command(name="war", description="Show active wars for a nation")
    @app_commands.describe(nation_id="The ID of the nation to check wars for")
    async def war(self, interaction: discord.Interaction, nation_id: int):
        """Show active wars."""
        await interaction.response.defer()
        
        try:
            # Get nation data
            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                await interaction.followup.send("❌ Could not find nation data.", ephemeral=True)
                return
            
            # Get active wars
            active_wars = self.war_service.get_active_wars(nation.__dict__)
            offensive_wars = self.war_service.get_offensive_wars(nation.__dict__)
            defensive_wars = self.war_service.get_defensive_wars(nation.__dict__)
            
            # Create embed
            embed = discord.Embed(
                title=f"⚔️ Wars - {nation.name}",
                description=f"**Active Wars:** {len(active_wars)}\n**Offensive:** {len(offensive_wars)} | **Defensive:** {len(defensive_wars)}",
                color=GameConstants.EMBED_COLOR_INFO
            )
            
            if not active_wars:
                embed.add_field(
                    name="🕊️ No Active Wars",
                    value="This nation is not currently at war.",
                    inline=False
                )
            else:
                for i, war in enumerate(active_wars[:5], 1):  # Show max 5 wars
                    war_type = "🟢 Offensive" if war.get('attacker_id') == nation.id else "🔴 Defensive"
                    turns_left = war.get('turns_left', 0)
                    
                    # Get control status
                    control_status = self.war_service.get_war_control_status(war)
                    
                    embed.add_field(
                        name=f"{i}. {war_type} War",
                        value=(
                            f"**Target:** {war.get('defender_name' if war.get('attacker_id') == nation.id else 'attacker_name', 'Unknown')}\n"
                            f"**Turns Left:** {turns_left}\n"
                            f"**Control:** G:{control_status['ground']} A:{control_status['air']} N:{control_status['naval']}"
                        ),
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
            logger.error(f"Error in war command: {e}")
            await interaction.followup.send("❌ An error occurred while fetching war data.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(WarDetectionCog(bot))
