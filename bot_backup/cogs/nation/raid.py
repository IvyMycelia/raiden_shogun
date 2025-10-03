"""
Nation raid commands.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from bot.utils.helpers import create_embed, format_number
from bot.handler import info, error, warning
from bot import data as get_data


class NationRaidCog(commands.Cog):
    """Cog for nation raid commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config
    
    def get_user_nation(self, user_id: int) -> Optional[int]:
        """Get a user's registered nation ID."""
        from bot.cogs.user import UserCog  # Avoid circular import
        user_cog = self.bot.get_cog('UserCog')
        if not user_cog:
            return None
        return user_cog.get_user_nation(user_id)
    
    async def raid_logic(self, interaction: discord.Interaction, nation_id: int = None):
        """Logic for raid command."""
        # Get user's nation data to determine score range
        if nation_id is None:
            # Get user's nation ID from their registration
            user_id = str(interaction.user.id)
            user_nation_id = self.get_user_nation(user_id)
            if not user_nation_id:
                await interaction.response.send_message("❌ You need to register your nation first! Use `/register` command.", ephemeral=True)
                return
            nation_id = user_nation_id
        
        # Get nation data to determine score range
        try:
            nation_data = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            if not nation_data:
                await interaction.response.send_message("❌ Could not find your nation data.", ephemeral=True)
                return
            
            user_score = float(nation_data.get('score', 0))
            min_score = user_score * 0.75
            max_score = user_score * 1.25
            
            # Defer the response
            await interaction.response.defer()
            
            # Use enhanced raid logic
            from bot.enhanced_raid import enhanced_raid_logic
            embed, view = await enhanced_raid_logic(interaction, min_score, max_score)
            if view:
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error finding raid targets: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="raid", description="Find profitable raid targets within your war range.")
    @app_commands.describe(nation_id="The ID of the nation to check (optional if you're registered)")
    async def raid(self, interaction: discord.Interaction, nation_id: int = None):
        """Find profitable raid targets within your war range."""
        await self.raid_logic(interaction, nation_id)


async def setup(bot: commands.Bot):
    """Set up the nation raid cog."""
    await bot.add_cog(NationRaidCog(bot))
