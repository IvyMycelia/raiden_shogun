"""
Latency monitoring task for the bot.
"""

import asyncio
import logging
from datetime import datetime
from discord import Activity, ActivityType

# Use the main logger instead of module-specific logger
logger = logging.getLogger('raiden_shogun')

async def latency_monitor_task(bot):
    """Background task to monitor bot latency every minute."""
    logger.info("Starting latency monitor task...")
    
    # Wait for bot to be ready
    while not bot.is_ready():
        logger.info("Waiting for bot to be ready...")
        await asyncio.sleep(5)
    
    logger.info("Bot is ready, starting latency monitoring...")
    
    while True:
        try:
            # Check if bot is ready and latency is available
            if not bot.is_ready():
                logger.warning("Bot not ready, skipping latency check")
                await asyncio.sleep(10)
                continue
                
            # Get bot latency in milliseconds
            raw_latency = bot.latency
            
            # Check if latency is valid (not None, inf, or negative)
            if raw_latency is None or raw_latency == float('inf') or raw_latency < 0:
                logger.warning(f"Invalid latency value: {raw_latency}, skipping")
                await asyncio.sleep(10)
                continue
            
            # Convert to milliseconds and round
            latency_ms = round(raw_latency * 1000)
            
            # Additional check for valid range
            if latency_ms <= 0 or latency_ms > 60000:  # Max 60 seconds
                logger.warning(f"Latency out of range: {latency_ms}ms, skipping")
                await asyncio.sleep(10)
                continue
            
            # Determine color based on latency
            if latency_ms < 100:
                color = "\033[92m"  # Green
                status = "EXCELLENT"
            elif latency_ms < 500:
                color = "\033[93m"  # Yellow
                status = "GOOD"
            elif latency_ms < 1000:
                color = "\033[91m"  # Red (for orange)
                status = "FAIR"
            else:
                color = "\033[91m"  # Red
                status = "POOR"
            
            # Reset color after the message
            reset = "\033[0m"
            
            # Log latency with ANSI color
            logger.info(f"{color}Bot latency: {latency_ms}ms ({status}){reset}")
            
            # Update bot activity to show ping
            activity = Activity(name=f"Ping: {latency_ms}ms", type=ActivityType.watching)
            await bot.change_presence(activity=activity)
            
            # Wait 1 minute before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in latency monitor task: {e}")
            import traceback
            logger.error(f"Latency monitor traceback: {traceback.format_exc()}")
            # Wait 30 seconds before retrying on error
            await asyncio.sleep(30)
