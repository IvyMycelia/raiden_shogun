import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from services.raid_cache_service import RaidCacheService
from tasks.raid_cache_task import force_update_raid_cache

logger = logging.getLogger('raiden_shogun')

class AdminCog(commands.Cog):
    """Admin commands for bot management."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin (Ivy's Discord ID)."""
        return user_id == 860564164828725299  # Ivy's Discord ID
    
    @commands.command(name="update_raid_cache")
    async def update_raid_cache_prefix(self, ctx: commands.Context):
        """Update raid cache using prefix command."""
        if not await self.is_admin(ctx.author.id):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        try:
            await ctx.send("🔄 Updating raid cache...")
            
            success = await force_update_raid_cache()
            
            if success:
                await ctx.send("✅ Raid cache updated successfully!")
            else:
                await ctx.send("❌ Failed to update raid cache.")
                
        except Exception as e:
            logger.error(f"Error updating raid cache: {e}")
            await ctx.send(f"❌ Error updating raid cache: {str(e)}")
    
    @app_commands.command(name="update_raid_cache", description="Update raid cache with latest data")
    async def update_raid_cache_slash(self, interaction: discord.Interaction):
        """Update raid cache using slash command."""
        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        try:
            await interaction.response.defer()
            
            success = await force_update_raid_cache()
            
            if success:
                await interaction.followup.send("✅ Raid cache updated successfully!")
            else:
                await interaction.followup.send("❌ Failed to update raid cache.")
                
        except Exception as e:
            logger.error(f"Error updating raid cache: {e}")
            await interaction.followup.send(f"❌ Error updating raid cache: {str(e)}")
    
    @app_commands.command(name="rpt", description="Send a message as the bot (Admin only)")
    @app_commands.describe(
        message="The message content to send",
        reply_to="Optional message ID to reply to"
    )
    async def rpt(self, interaction: discord.Interaction, message: str, reply_to: Optional[str] = None):
        """Send a message as the bot and optionally reply to another message."""
        if not await self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate message length
            if len(message) > 2000:
                await interaction.followup.send("❌ Message too long. Maximum 2000 characters.", ephemeral=True)
                return
            
            # Check if we should reply to a message
            if reply_to:
                try:
                    # Try to parse the message ID
                    message_id = int(reply_to)
                    
                    # Find the message to reply to
                    reply_message = None
                    for channel in interaction.guild.channels:
                        if isinstance(channel, (discord.TextChannel, discord.Thread)):
                            try:
                                reply_message = await channel.fetch_message(message_id)
                                break
                            except (discord.NotFound, discord.Forbidden):
                                continue
                    
                    if reply_message:
                        # Send reply
                        await reply_message.reply(message)
                        await interaction.followup.send(f"✅ Message sent as reply to message {message_id}", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ Could not find message with ID {message_id}", ephemeral=True)
                        return
                        
                except ValueError:
                    await interaction.followup.send("❌ Invalid message ID format. Please provide a valid message ID.", ephemeral=True)
                    return
            else:
                # Send regular message
                await interaction.channel.send(message)
                await interaction.followup.send("✅ Message sent successfully", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in rpt command: {e}")
            await interaction.followup.send(f"❌ Error sending message: {str(e)}", ephemeral=True)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(AdminCog(bot))
