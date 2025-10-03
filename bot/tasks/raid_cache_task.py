import asyncio
import logging
from datetime import datetime, timezone, timedelta
import pytz

from services.raid_cache_service import RaidCacheService

logger = logging.getLogger('raiden_shogun')

async def update_raid_cache_task():
    """Background task to update raid cache at 20:00 EST daily."""
    # Set up EST timezone
    est = pytz.timezone('US/Eastern')
    
    while True:
        try:
            # Get current time in EST
            now_est = datetime.now(est)
            
            # Check if it's 20:00 EST (8 PM)
            if now_est.hour == 20 and now_est.minute == 0:
                logger.info("Starting scheduled raid cache update at 20:00 EST...")
                
                async with RaidCacheService() as cache_service:
                    success = await cache_service.update_raid_cache()
                    
                    if success:
                        logger.info("Raid cache updated successfully at 20:00 EST")
                        # Clean up old cache files
                        cache_service.cleanup_old_cache(keep_days=7)
                    else:
                        logger.error("Failed to update raid cache at 20:00 EST")
                
                # Wait 1 hour to avoid multiple updates
                await asyncio.sleep(3600)
            else:
                # Check every minute
                await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in raid cache update task: {e}")
            # Wait 1 minute before retrying on error
            await asyncio.sleep(60)

async def startup_cache_update():
    """Update cache at bot startup."""
    try:
        logger.info("Starting startup raid cache update...")
        
        async with RaidCacheService() as cache_service:
            success = await cache_service.update_raid_cache()
            
            if success:
                logger.info("Startup raid cache update successful")
                return True
            else:
                logger.error("Startup raid cache update failed")
                return False
                
    except Exception as e:
        logger.error(f"Error in startup cache update: {e}")
        return False

async def force_update_raid_cache():
    """Force update raid cache immediately."""
    try:
        logger.info("Force updating raid cache...")
        
        async with RaidCacheService() as cache_service:
            success = await cache_service.update_raid_cache()
            
            if success:
                logger.info("Raid cache force updated successfully")
                return True
            else:
                logger.error("Failed to force update raid cache")
                return False
                
    except Exception as e:
        logger.error(f"Error force updating raid cache: {e}")
        return False
