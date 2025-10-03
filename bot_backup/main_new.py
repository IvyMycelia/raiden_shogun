"""
Main entry point for the Raiden Shogun Discord bot.
"""
import asyncio
import discord
from discord.ext import commands
import logging

from config.settings import settings
from services.cache_service import CacheService
from services.nation_service import NationService
from services.raid_service import RaidService
from services.audit_service import AuditService
from api.politics_war_api import PoliticsWarAPI
from handler import info, error, warning


class RaidenShogunBot(commands.Bot):
    """Main bot class with organized structure."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Initialize services
        self.api_client = PoliticsWarAPI(settings.API_KEY)
        self.cache_service = CacheService()
        self.nation_service = NationService(self.api_client, self.cache_service)
        self.raid_service = RaidService(self.nation_service, self.cache_service)
        self.audit_service = AuditService(self.nation_service, self.cache_service)
        
        # Store services in bot for access by cogs
        self.services = {
            'api_client': self.api_client,
            'cache_service': self.cache_service,
            'nation_service': self.nation_service,
            'raid_service': self.raid_service,
            'audit_service': self.audit_service
        }
    
    async def setup_hook(self):
        """Set up the bot after login."""
        # Load cogs
        await self.load_cogs()
        
        # Start background tasks
        self.latency_task = self.loop.create_task(self.check_latency())
        self.cache_update_task = self.loop.create_task(self.auto_update_cache())
    
    async def load_cogs(self):
        """Load all cogs."""
        cogs_to_load = [
            'bot.cogs.nation.info',
            'bot.cogs.nation.search', 
            'bot.cogs.nation.raid',
            'bot.cogs.alliance.audit',
            'bot.cogs.war.detection',
            'bot.cogs.utility.help',
            'bot.cogs.utility.feedback',
            'bot.cogs.user'
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                info(f"Loaded cog: {cog}", tag="BOT")
            except Exception as e:
                error(f"Failed to load cog {cog}: {e}", tag="BOT")
    
    async def check_latency(self):
        """Check bot latency periodically."""
        while not self.is_closed():
            try:
                latency = self.latency * 1000
                info(f"Latency: {latency:.2f} ms", tag="LATENCY")
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                error(f"Error checking latency: {e}", tag="LATENCY")
                await asyncio.sleep(60)
    
    async def auto_update_cache(self):
        """Automatically update cache every 5 minutes."""
        while not self.is_closed():
            try:
                await asyncio.sleep(300)  # Wait 5 minutes
                info("Auto-updating cache...", tag="CACHE")
                
                # Update cache from CSV data
                from csv_cache import get_cache
                cache = get_cache()
                success = await cache.download_csv_data()
                
                if success:
                    info("Auto cache update successful", tag="CACHE")
                else:
                    warning("Auto cache update failed", tag="CACHE")
                    
            except Exception as e:
                error(f"Error in auto cache update: {e}", tag="CACHE")
                await asyncio.sleep(300)
    
    async def on_ready(self):
        """Called when bot is ready."""
        info(f"Logged in as {self.user.name} ({self.user.id})", tag="BOT")
        
        # Initialize CSV cache system
        try:
            from csv_cache import init_cache
            init_cache(settings.API_KEY)
            info("CSV cache system initialized", tag="CSV_CACHE")
        except Exception as e:
            error(f"Failed to initialize CSV cache: {e}", tag="CSV_CACHE")
        
        # Sync commands globally
        try:
            synced = await self.tree.sync()
            info(f"Synced {len(synced)} commands globally", tag="BOT")
        except Exception as e:
            error(f"Failed to sync commands: {e}", tag="BOT")
        
        info("Bot is ready!", tag="BOT")
    
    async def close(self):
        """Clean up when bot is closing."""
        if hasattr(self, 'api_client'):
            await self.api_client.close()
        
        await super().close()


async def main():
    """Main function to run the bot."""
    # Validate configuration
    try:
        settings.validate()
    except ValueError as e:
        error(f"Configuration error: {e}", tag="BOT")
        return
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run bot
    bot = RaidenShogunBot()
    
    try:
        await bot.start(settings.BOT_TOKEN)
    except KeyboardInterrupt:
        info("Bot stopped by user", tag="BOT")
    except Exception as e:
        error(f"Bot error: {e}", tag="BOT")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
