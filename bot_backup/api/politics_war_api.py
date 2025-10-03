"""
Politics and War API client.
"""
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.settings import settings
from config.constants import GameConstants


class PoliticsWarAPI:
    """Client for Politics and War API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = settings.API_BASE_URL
        self.timeout = aiohttp.ClientTimeout(total=settings.API_TIMEOUT)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make API request with rate limiting."""
        session = await self._get_session()
        
        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        try:
            async with session.get(f"{self.base_url}/{endpoint}", params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:  # Rate limited
                    await asyncio.sleep(1)  # Wait 1 second and retry
                    return await self._make_request(endpoint, params)
                else:
                    return None
        except Exception:
            return None
    
    async def get_nation_data(self, nation_id: int) -> Optional[Dict[str, Any]]:
        """Get nation data by ID."""
        return await self._make_request("nation", {"id": nation_id})
    
    async def search_nations(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for nations by name or leader."""
        # This would need to be implemented based on available API endpoints
        # For now, return empty list
        return []
    
    async def get_nation_wars(self, nation_id: int) -> List[Dict[str, Any]]:
        """Get wars for a nation."""
        return await self._make_request("wars", {"nation_id": nation_id}) or []
    
    async def get_alliance_data(self, alliance_id: int) -> Optional[Dict[str, Any]]:
        """Get alliance data by ID."""
        return await self._make_request("alliance", {"id": alliance_id})
    
    async def get_alliance_members(self, alliance_id: int) -> List[Dict[str, Any]]:
        """Get alliance members."""
        return await self._make_request("alliance_members", {"id": alliance_id}) or []
    
    async def get_war_data(self, war_id: int) -> Optional[Dict[str, Any]]:
        """Get war data by ID."""
        return await self._make_request("war", {"id": war_id})
    
    async def get_cities_data(self, nation_id: int) -> List[Dict[str, Any]]:
        """Get cities data for a nation."""
        return await self._make_request("cities", {"nation_id": nation_id}) or []
    
    async def get_trades_data(self, nation_id: int) -> List[Dict[str, Any]]:
        """Get trades data for a nation."""
        return await self._make_request("trades", {"nation_id": nation_id}) or []
    
    async def get_bank_data(self, alliance_id: int) -> Optional[Dict[str, Any]]:
        """Get alliance bank data."""
        return await self._make_request("alliance_bank", {"id": alliance_id})
    
    async def get_nations_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all nations data (for CSV-like functionality)."""
        # This would need to be implemented based on available API endpoints
        # For now, return empty list
        return []
    
    async def get_wars_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all wars data (for CSV-like functionality)."""
        # This would need to be implemented based on available API endpoints
        # For now, return empty list
        return []
    
    async def get_alliances_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all alliances data (for CSV-like functionality)."""
        # This would need to be implemented based on available API endpoints
        # For now, return empty list
        return []
    
    async def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            result = await self._make_request("nations", {"limit": 1})
            return result is not None
        except Exception:
            return False
