"""
Service for caching operations.
"""
import json
import asyncio
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta

from config.constants import GameConstants


class CacheService:
    """Service for managing cache operations."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            cache_entry = self._cache[key]
            
            # Check if expired
            if datetime.now() > cache_entry['expires_at']:
                del self._cache[key]
                return None
            
            return cache_entry['value']
    
    async def set(self, key: str, value: Any, ttl: int = GameConstants.CACHE_TTL) -> None:
        """Set value in cache with TTL."""
        async with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
            
            # Clean up expired entries if cache is getting large
            if len(self._cache) > GameConstants.MAX_CACHE_ENTRIES:
                await self._cleanup_expired()
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
    
    async def get_nations_in_range(self, min_score: float, max_score: float) -> List[Dict[str, Any]]:
        """Get nations within score range from cache."""
        cache_key = f"nations_range:{min_score}:{max_score}"
        return await self.get(cache_key) or []
    
    async def set_nations_in_range(
        self, 
        min_score: float, 
        max_score: float, 
        nations: List[Dict[str, Any]], 
        ttl: int = GameConstants.CACHE_TTL
    ) -> None:
        """Set nations within score range in cache."""
        cache_key = f"nations_range:{min_score}:{max_score}"
        await self.set(cache_key, nations, ttl)
    
    async def get_alliance_members(self, alliance_id: int) -> List[Dict[str, Any]]:
        """Get alliance members from cache."""
        cache_key = f"alliance_members:{alliance_id}"
        return await self.get(cache_key) or []
    
    async def set_alliance_members(
        self, 
        alliance_id: int, 
        members: List[Dict[str, Any]], 
        ttl: int = GameConstants.CACHE_TTL
    ) -> None:
        """Set alliance members in cache."""
        cache_key = f"alliance_members:{alliance_id}"
        await self.set(cache_key, members, ttl)
    
    async def get_war_data(self, war_id: int) -> Optional[Dict[str, Any]]:
        """Get war data from cache."""
        cache_key = f"war:{war_id}"
        return await self.get(cache_key)
    
    async def set_war_data(
        self, 
        war_id: int, 
        war_data: Dict[str, Any], 
        ttl: int = GameConstants.CACHE_TTL
    ) -> None:
        """Set war data in cache."""
        cache_key = f"war:{war_id}"
        await self.set(cache_key, war_data, ttl)
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            now = datetime.now()
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values()
                if now > entry['expires_at']
            )
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'max_entries': GameConstants.MAX_CACHE_ENTRIES
            }
    
    async def load_from_file(self, file_path: str) -> bool:
        """Load cache from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            async with self._lock:
                for key, entry_data in data.items():
                    self._cache[key] = {
                        'value': entry_data['value'],
                        'expires_at': datetime.fromisoformat(entry_data['expires_at']),
                        'created_at': datetime.fromisoformat(entry_data['created_at'])
                    }
            
            return True
        except Exception:
            return False
    
    async def save_to_file(self, file_path: str) -> bool:
        """Save cache to file."""
        try:
            async with self._lock:
                # Clean up expired entries first
                await self._cleanup_expired()
                
                # Prepare data for serialization
                data = {}
                for key, entry in self._cache.items():
                    data[key] = {
                        'value': entry['value'],
                        'expires_at': entry['expires_at'].isoformat(),
                        'created_at': entry['created_at'].isoformat()
                    }
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
