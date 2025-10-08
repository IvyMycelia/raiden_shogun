"""
Main entry point for Raiden Shogun Discord bot.
"""

import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import os
import sys

# Add bot directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from utils.logging import setup_logging, get_logger
from services.cache_service import CacheService
from tasks.raid_cache_task import update_raid_cache_task, startup_cache_update
from tasks.latency_monitor import latency_monitor_task

# Setup logging
logger = setup_logging()
bot_logger = get_logger('main')

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
# Note: members intent removed as it's privileged and not needed for basic functionality

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)
bot.help_command = None  # Disable default help so our custom help cog handles !help

# Global services
cache_service = CacheService()

@bot.event
async def on_ready():
    """Bot ready event."""
    bot_logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    
    # Initialize cache service
    try:
        # Download initial cache data
        success = await cache_service.download_csv_data()
        if success:
            bot_logger.info("Initial cache download successful")
        else:
            bot_logger.warning("Initial cache download failed")
    except Exception as e:
        bot_logger.error(f"Error initializing cache: {e}")
    
        # Load cogs
    await load_cogs()
    
    # Start background tasks
    bot.loop.create_task(update_cache_task())
    bot.loop.create_task(update_raid_cache_task())
    
    # Run startup cache update
    bot.loop.create_task(startup_cache_update())
    
    # Start latency monitor after a short delay to ensure bot is ready
    async def start_latency_monitor():
        await asyncio.sleep(5)  # Wait 5 seconds for bot to be fully ready
        bot_logger.info("Starting latency monitor task...")
        bot.loop.create_task(latency_monitor_task(bot))
    
    bot.loop.create_task(start_latency_monitor())
        
        # Sync commands
        try:
            synced = await bot.tree.sync()
        bot_logger.info(f"Synced {len(synced)} commands")
        except Exception as e:
        bot_logger.error(f"Failed to sync commands: {e}")
    
    bot_logger.info("Bot is ready!")

@bot.event
async def on_command_error(ctx, error):
    """Log command errors."""
    bot_logger.error(f"Command error: {error}")

@bot.event
async def on_app_command_error(interaction, error):
    """Log slash command errors."""
    bot_logger.error(f"Slash command error: {error}")

async def update_cache_task():
    """Background task to update cache every 5 minutes."""
    while True:
        try:
            await asyncio.sleep(config.CACHE_UPDATE_INTERVAL)
            success = await cache_service.download_csv_data()
            if success:
                bot_logger.info("Cache update successful")
            else:
                bot_logger.warning("Cache update failed")
        except Exception as e:
            bot_logger.error(f"Error in cache update task: {e}")


@bot.event
async def on_command_completion(ctx):
    """Log successful command execution."""
    channel_name = ctx.channel.name if hasattr(ctx.channel, 'name') else 'DM'
    bot_logger.info(f"Command executed: {ctx.command.name} by {ctx.author.name} (ID: {ctx.author.id}) in #{channel_name}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    bot_logger.error(f"Command error: {error}")
    
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
        return
    
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ I don't have permission to perform this action.")
        return
    
    # Generic error message
    await ctx.send("❌ An error occurred while processing your command.")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Log slash command execution."""
    if interaction.type == discord.InteractionType.application_command:
        channel_name = interaction.channel.name if hasattr(interaction.channel, 'name') else 'DM'
        bot_logger.info(f"Slash command executed: {interaction.command.name} by {interaction.user.name} (ID: {interaction.user.id}) in #{channel_name}")

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle slash command errors."""
    bot_logger.error(f"Slash command error: {error}")
    
    if not interaction.response.is_done():
        try:
            await interaction.response.send_message("❌ An error occurred while processing your command.", ephemeral=True)
            bot_logger.info(f"Error response sent to {interaction.user.name} in #{interaction.channel.name}")
        except:
            pass
    else:
        try:
            await interaction.followup.send("❌ An error occurred while processing your command.", ephemeral=True)
            bot_logger.info(f"Error followup sent to {interaction.user.name} in #{interaction.channel.name}")
        except:
            pass

async def load_cogs():
    """Load all bot cogs."""
    cogs = [
        'cogs.nation.info',
        'cogs.nation.raid',
        'cogs.nation.search',
        'cogs.nation.wars',
        'cogs.nation.intel',
        'cogs.nation.purge',
        'cogs.nation.projects',
        'cogs.nation.military',
        'cogs.nation.build',
        'cogs.audit.main',
        'cogs.audit.activity',
        'cogs.audit.warchest',
        'cogs.audit.spies',
        'cogs.audit.bloc',
        'cogs.audit.military',
        'cogs.alliance.management',
        'cogs.war.detection',
        'cogs.war.analysis',
        'cogs.utility.help',
        'cogs.utility.feedback',
        'cogs.utility.admin',
        'cogs.utility.market'
    ]
    
    # First, unload any existing cogs to avoid conflicts
    for cog_name in list(bot.extensions.keys()):
        try:
            await bot.unload_extension(cog_name)
            bot_logger.info(f"Unloaded existing cog: {cog_name}")
        except Exception as e:
            bot_logger.warning(f"Failed to unload cog {cog_name}: {e}")
    
    # Now load all cogs
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            bot_logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            bot_logger.error(f"Failed to load cog {cog}: {e}")

async def main():
    """Main function."""
    try:
        # Start bot
        await bot.start(config.BOT_TOKEN)
    except Exception as e:
        bot_logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.info("Bot stopped by user")
    except Exception as e:
        bot_logger.error(f"Fatal error: {e}")
        sys.exit(1)
