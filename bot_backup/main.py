# Import Discord libraries
import discord
from discord import app_commands, AllowedMentions
from discord.ext import commands
from discord.ui import View, Button, Select

# Import standard libraries
from datetime import datetime, timezone
import pytz
import math
import random
import os
import asyncio
import json
import time
import traceback
import sys
from typing import Optional, List, Dict, Any

# Import custom modules
import calculate
import data as get_data
import vars as vars
import db as dataBase
from handler import debug, info, success, warning, error, fatal, missing_data, latency_check
from utils.config import config
from bot.csv_cache import init_cache, get_cache

# Constants
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
ALLIANCE_ID = os.getenv("ALLIANCE_ID")

# Configuration
COSTS = vars.COSTS
MILITARY_COSTS = vars.MILITARY_COSTS

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.config = config  # Add config to bot instance

GUILD_ID = 1279582264568713308  # Provided guild/server ID
GUILD_OBJECT = discord.Object(id=GUILD_ID)

async def check_latency():
    """Monitor bot latency."""
    while True:
        try:
            latency = bot.latency * 1000
            latency_check(latency, tag="LATENCY")
            await bot.change_presence(
                activity=discord.Game(name=f"Latency: {latency:,.2f}ms")
            )
            await asyncio.sleep(60)
        except Exception as e:
            error(f"Error in latency check: {e}", tag="LATENCY")
            await asyncio.sleep(60)

async def auto_update_csv_cache():
    """Automatically update CSV cache every 5 minutes."""
    while True:
        try:
            await asyncio.sleep(300)  # Wait 5 minutes
            from bot.csv_cache import get_cache
            cache = get_cache()
            info("Auto-updating CSV cache...", tag="CSV_CACHE")
            success = await cache.download_csv_data()
            if success:
                info("Auto CSV cache update successful", tag="CSV_CACHE")
            else:
                warning("Auto CSV cache update failed", tag="CSV_CACHE")
        except Exception as e:
            error(f"Error in auto CSV cache update: {e}", tag="CSV_CACHE")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying



@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    try:
        # Load cogs
        for cog in ["bot.cogs.audit", "bot.cogs.utility", "bot.cogs.nation", "bot.cogs.feedback", "bot.cogs.military", "bot.cogs.war", "bot.cogs.user", "bot.cogs.war_detection"]:
            try:
                await bot.load_extension(cog)
                info(f"Successfully loaded extension: {cog}")
            except Exception as e:
                error(f"Failed to load extension {cog}: {e}")
                fatal(f"Extension load error details: {traceback.format_exc()}")
                raise  # Re-raise to prevent bot from starting with missing functionality
        
        # Sync commands
        try:
            synced = await bot.tree.sync()
            info(f"Successfully synced {len(synced)} commands")
            # Clear old guild commands for the specified guild
            bot.tree.clear_commands(guild=GUILD_OBJECT)
        except Exception as e:
            error(f"Failed to sync commands: {e}")
            fatal(f"Command sync error details: {traceback.format_exc()}")
            raise  # Re-raise to prevent bot from starting with unsynced commands
        success(f"Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
        # Initialize CSV cache
        try:
            init_cache(API_KEY)
            info("CSV cache system initialized", tag="CSV_CACHE")
        except Exception as e:
            error(f"Failed to initialize CSV cache: {e}", tag="CSV_CACHE")
        
        # CSV data manager removed - using CSV cache instead
        
        # Start latency monitoring
        if not hasattr(bot, 'latency_task'):
            bot.latency_task = bot.loop.create_task(check_latency())
            info("Started latency monitoring task")
        
        # Start auto CSV cache update
        if not hasattr(bot, 'csv_cache_task'):
            bot.csv_cache_task = bot.loop.create_task(auto_update_csv_cache())
            info("Started auto CSV cache update task")
        
        # CSV cache is already loaded, no need for immediate update
        
    except Exception as e:
        fatal(f"Critical error during bot startup: {e}")
        fatal(f"Startup error details: {traceback.format_exc()}")
        raise

@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler for all events."""
    error(f"Error in {event}: {sys.exc_info()}", tag="EVENT_ERROR")
    fatal(f"Event error details: {traceback.format_exc()}")

@bot.event
async def on_command_error(ctx, err):
    """Global error handler for all commands."""
    if isinstance(err, commands.CommandNotFound):
        warning(f"Command not found: {ctx.message.content}", tag="COMMAND")
        return
    if isinstance(err, commands.MissingPermissions):
        warning(f"Missing permissions for command: {ctx.message.content}", tag="PERMISSIONS")
        await ctx.send("You don't have permission to use this command.")
        return
    if isinstance(err, commands.MissingRequiredArgument):
        warning(f"Missing required argument for command: {ctx.message.content}", tag="ARGUMENTS")
        await ctx.send(f"Missing required argument: {err.param.name}")
        return
    error(f"Command error in {ctx.command}: {err}", tag="COMMAND_ERROR")
    fatal(f"Command error details: {traceback.format_exc()}")

def main():
    """Main entry point for the bot."""
    try:
        # Validate configuration before starting
        if not config.BOT_TOKEN:
            fatal("Bot token not found in configuration")
            sys.exit(1)
        
        if not config.API_KEY:
            fatal("API key not found in configuration")
            sys.exit(1)
        
        if not config.ALLIANCE_ID:
            fatal("Alliance ID not found in configuration")
            sys.exit(1)
        
        info("Starting bot...")
        bot.run(config.BOT_TOKEN)
    except discord.LoginFailure:
        fatal("Failed to login: Invalid bot token")
        sys.exit(1)
    except discord.HTTPException as e:
        fatal(f"HTTP error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        fatal(f"Unexpected error during bot startup: {e}")
        fatal(f"Startup error details: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()

