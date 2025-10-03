"""
API Coordinator to prevent simultaneous API calls and manage rate limiting.
"""
import asyncio
import time
from typing import Dict, Any
import threading

class APICoordinator:
    """Coordinates API calls to prevent rate limiting."""
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._last_call_time = 0
        self._min_interval = 1.0  # Minimum 1 second between API calls
        
    async def make_api_call(self, func, *args, **kwargs):
        """Make an API call with rate limiting coordination."""
        async with self._lock:
            # Calculate time since last call
            current_time = time.time()
            time_since_last = current_time - self._last_call_time
            
            # If we need to wait, do so
            if time_since_last < self._min_interval:
                wait_time = self._min_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            # Make the API call
            try:
                # Check if the function is async and await it properly
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                self._last_call_time = time.time()
                return result
            except Exception as e:
                # If we get rate limited, wait longer
                if "429" in str(e) or "Too Many Requests" in str(e):
                    await asyncio.sleep(5)
                    # Retry once
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    self._last_call_time = time.time()
                    return result
                raise

# Global API coordinator instance
api_coordinator = APICoordinator()
