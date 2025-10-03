"""
Wars command for displaying active wars.
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import traceback
from typing import Optional

from services.nation_service import NationService

logger = logging.getLogger('raiden_shogun')

class WarsCog(commands.Cog):
    """Wars command cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.nation_service = NationService()
    
    def format_war_line(self, war, nation_id: int, is_offensive: bool) -> str:
        """Format a single war line for the table."""
        # Determine if this nation is attacker or defender
        is_attacker = war['attacker']['id'] == nation_id
        
        # Get opponent info
        if is_attacker:
            opponent = war['defender']
            our_resistance = war.get('att_resistance', 0)
            their_resistance = war.get('def_resistance', 0)
            our_fortify = war.get('att_fortify', 0)
            their_fortify = war.get('def_fortify', 0)
        else:
            opponent = war['attacker']
            our_resistance = war.get('def_resistance', 0)
            their_resistance = war.get('att_resistance', 0)
            our_fortify = war.get('def_fortify', 0)
            their_fortify = war.get('att_fortify', 0)
        
        # War type abbreviation
        war_type = war.get('war_type', 'Unknown')
        if war_type == 'ground':
            type_abbr = 'G'
        elif war_type == 'air':
            type_abbr = 'A'
        elif war_type == 'naval':
            type_abbr = 'N'
        else:
            type_abbr = '?'
        
        # Control indicators
        ground_control = war.get('groundcontrol', 0)
        air_superiority = war.get('airsuperiority', 0)
        naval_blockade = war.get('navalblockade', 0)
        
        # Determine control status
        if is_attacker:
            ground_status = "A" if ground_control == 1 else "D" if ground_control == 2 else "-"
            air_status = "A" if air_superiority == 1 else "D" if air_superiority == 2 else "-"
            naval_status = "A" if naval_blockade == 1 else "D" if naval_blockade == 2 else "-"
        else:
            ground_status = "D" if ground_control == 2 else "A" if ground_control == 1 else "-"
            air_status = "D" if air_superiority == 2 else "A" if air_superiority == 1 else "-"
            naval_status = "D" if naval_blockade == 2 else "A" if naval_blockade == 1 else "-"
        
        # Format fortify as Yes/No
        our_fortify_str = "Yes" if our_fortify else "No"
        their_fortify_str = "Yes" if their_fortify else "No"
        
        # Format the line
        line = f"#{war['id']:07d} {type_abbr} | {opponent['nation_name'][:15]:<15} | {our_resistance:>3}/{their_resistance:>3} | {our_fortify_str:>3}/{their_fortify_str:>3} | {ground_status}/{air_status}/{naval_status} | {war.get('turns_left', 0):>2}T"
        
        return line
    
    def format_wars_table(self, wars_data: dict, nation_id: int) -> str:
        """Format the complete wars table."""
        nation_name = wars_data.get('nation_name', 'Unknown')
        
        # Get all wars - handle both list and count formats
        defensive_wars = wars_data.get('defensive_wars', [])
        offensive_wars = wars_data.get('offensive_wars', [])
        
        # If they're integers (counts), convert to empty lists
        if isinstance(defensive_wars, int):
            defensive_wars = []
        if isinstance(offensive_wars, int):
            offensive_wars = []
        
        # If no wars data available, show a message
        if not defensive_wars and not offensive_wars:
            return f"```\nActive Wars for {nation_name} (ID: {nation_id})\n{'='*60}\n\nNo active wars found.\n```"
        
        # Build the table
        lines = []
        lines.append(f"Active Wars for {nation_name} (ID: {nation_id})")
        lines.append("=" * 60)
        lines.append("")
        lines.append("ID      T | Opponent         | Res  | Fort | G/A/N | T")
        lines.append("-" * 60)
        
        # Add defensive wars
        for war in defensive_wars:
            lines.append(self.format_war_line(war, nation_id, False))
        
        # Add offensive wars
        for war in offensive_wars:
            lines.append(self.format_war_line(war, nation_id, True))
        
        # Add summary
        total_wars = len(defensive_wars) + len(offensive_wars)
        offensive_count = len(offensive_wars)
        defensive_count = len(defensive_wars)
        
        lines.append("-" * 60)
        lines.append(f"Total: {total_wars} Active Wars ({offensive_count} Offensive, {defensive_count} Defensive)")
        
        return f"```\n" + "\n".join(lines) + "\n```"
    
    async def get_target_nation_id(self, context, nation_id: int = None):
        """Determine which nation ID to use based on the fallback logic."""
        # If nation ID is provided, use it
        if nation_id:
            return nation_id
        
        # Get the channel and user
        if hasattr(context, 'channel'):  # Context object (prefix command)
            channel = context.channel
            user_id = str(context.author.id)
        else:  # Interaction object (slash command)
            channel = context.channel
            user_id = str(context.user.id)
        
        # Look for numbers in recent channel messages
        try:
            # Get last 10 messages in the channel
            messages = []
            async for message in channel.history(limit=10):
                messages.append(message)
            
            # Look for nation IDs in messages (6-digit numbers)
            import re
            for message in messages:
                # Look for 6-digit numbers (typical nation ID format)
                numbers = re.findall(r'\b\d{6}\b', message.content)
                if numbers:
                    # Return the first 6-digit number found
                    return int(numbers[0])
                
                # Also look for nation ID patterns like "ID: 123456" or "id=123456"
                id_patterns = re.findall(r'(?:id[=:]\s*|ID[=:]\s*)(\d{6})', message.content, re.IGNORECASE)
                if id_patterns:
                    return int(id_patterns[0])
        
        except Exception as e:
            logger.warning(f"Error searching channel messages: {e}")
        
        # Fall back to user's registered nation
        try:
            from services.cache_service import CacheService
            cache_service = CacheService()
            registered_nation_id = cache_service.get_user_nation(user_id)
            if registered_nation_id:
                return registered_nation_id
        except Exception as e:
            logger.warning(f"Error getting registered nation: {e}")
        
        return None
    
    @app_commands.command(name="wars", description="Show active wars for a nation")
    @app_commands.describe(nation_id="Nation ID to check wars for (optional)")
    async def wars_slash(self, interaction: discord.Interaction, nation_id: int = None):
        """Slash command to show active wars."""
        await interaction.response.defer()
        
        try:
            # Determine which nation ID to use
            target_nation_id = await self.get_target_nation_id(interaction, nation_id)
            if not target_nation_id:
                await interaction.followup.send("❌ Could not determine nation ID. Please provide a nation ID or ensure you're registered.")
                return
            
            # Get nation data
            nation_data = await self.nation_service.get_nation(target_nation_id)
            if not nation_data:
                await interaction.followup.send(f"❌ Nation with ID {target_nation_id} not found.")
                return
            
            # Format and send wars table
            wars_table = self.format_wars_table(nation_data.__dict__, target_nation_id)
            await interaction.followup.send(wars_table)
            
        except Exception as e:
            logger.error(f"Error in wars command: {e}")
            logger.error(f"Wars command traceback: {traceback.format_exc()}")
            await interaction.followup.send(f"❌ Error retrieving war data: {str(e)}")
    
    @commands.command(name="wars", aliases=["war"])
    async def wars_prefix(self, ctx, nation_id: int = None):
        """Prefix command to show active wars."""
        try:
            # Determine which nation ID to use
            target_nation_id = await self.get_target_nation_id(ctx, nation_id)
            if not target_nation_id:
                await ctx.send("❌ Could not determine nation ID. Please provide a nation ID or ensure you're registered.")
                return
            
            # Get nation data
            nation_data = await self.nation_service.get_nation(target_nation_id)
            if not nation_data:
                await ctx.send(f"❌ Nation with ID {target_nation_id} not found.")
                return
            
            # Format and send wars table
            wars_table = self.format_wars_table(nation_data.__dict__, target_nation_id)
            await ctx.send(wars_table)
            
        except Exception as e:
            logger.error(f"Error in wars command: {e}")
            logger.error(f"Wars command traceback: {traceback.format_exc()}")
            await ctx.send(f"❌ Error retrieving war data: {str(e)}")

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(WarsCog(bot))
