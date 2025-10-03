"""
API key rotation and management system.
"""

import time
import random
from typing import Dict, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config

class APIKeyManager:
    """Manages API key rotation and rate limiting."""
    
    def __init__(self):
        self.key_pools = config.API_KEYS
        self.current_indices = {scope: 0 for scope in self.key_pools.keys()}
        self.rate_limits = {key: {"calls": 0, "reset_time": 0} for key in self._get_all_keys()}
        self.key_health = {key: {"status": "healthy", "last_error": None, "error_time": 0} for key in self._get_all_keys()}
    
    def _get_all_keys(self) -> List[str]:
        """Get all API keys from all scopes."""
        all_keys = []
        for keys in self.key_pools.values():
            all_keys.extend(keys)
        return all_keys
    
    def get_key(self, scope: str) -> str:
        """Get next available key for specified scope with health checking."""
        if scope not in self.key_pools:
            raise ValueError(f"Invalid scope: {scope}")
        
        keys = self.key_pools[scope]
        if not keys:
            raise ValueError(f"No keys available for scope: {scope}")
        
        # Find healthy keys with lowest usage
        healthy_keys = [key for key in keys if self.key_health[key]["status"] == "healthy"]
        
        if not healthy_keys:
            # Fallback to any key if all unhealthy
            healthy_keys = keys
        
        # Select key with lowest usage
        selected_key = min(healthy_keys, key=lambda k: self.rate_limits[k]["calls"])
        
        # Update rotation index
        self.current_indices[scope] = (self.current_indices[scope] + 1) % len(keys)
        
        return selected_key
    
    def check_rate_limit(self, key: str) -> bool:
        """Check if key is within rate limits."""
        current_time = time.time()
        rate_data = self.rate_limits[key]
        
        # Reset if past reset time (1 hour)
        if current_time >= rate_data["reset_time"]:
            rate_data["calls"] = 0
            rate_data["reset_time"] = current_time + 3600
        
        return rate_data["calls"] < config.API_RATE_LIMIT
    
    def increment_usage(self, key: str):
        """Increment usage counter for key."""
        self.rate_limits[key]["calls"] += 1
    
    def mark_key_unhealthy(self, key: str, error: str):
        """Mark key as unhealthy due to error."""
        self.key_health[key]["status"] = "unhealthy"
        self.key_health[key]["last_error"] = error
        self.key_health[key]["error_time"] = time.time()
    
    def check_key_health(self, key: str) -> bool:
        """Check if key is healthy."""
        if self.key_health[key]["status"] == "unhealthy":
            # Auto-recovery after 5 minutes
            if time.time() - self.key_health[key]["error_time"] > 300:
                self.key_health[key]["status"] = "healthy"
                self.key_health[key]["last_error"] = None
        
        return self.key_health[key]["status"] == "healthy"
    
    def get_key_usage_stats(self) -> Dict:
        """Get usage statistics for all keys."""
        stats = {}
        for scope, keys in self.key_pools.items():
            stats[scope] = {
                "total_calls": sum(self.rate_limits[key]["calls"] for key in keys),
                "average_calls": sum(self.rate_limits[key]["calls"] for key in keys) / len(keys),
                "healthy_keys": sum(1 for key in keys if self.key_health[key]["status"] == "healthy"),
                "unhealthy_keys": sum(1 for key in keys if self.key_health[key]["status"] == "unhealthy")
            }
        return stats
    
    def reset_all_keys(self):
        """Reset all keys to healthy status."""
        for key in self._get_all_keys():
            self.key_health[key]["status"] = "healthy"
            self.key_health[key]["last_error"] = None
            self.rate_limits[key]["calls"] = 0
            self.rate_limits[key]["reset_time"] = time.time() + 3600

# Global key manager instance
key_manager = APIKeyManager()
