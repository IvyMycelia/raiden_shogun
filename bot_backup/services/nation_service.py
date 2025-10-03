"""
Service for nation-related operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from models.nation import Nation, RaidTarget
from api.politics_war_api import PoliticsWarAPI
from services.cache_service import CacheService
from config.constants import GameConstants, WAR_RANGE_MULTIPLIERS


class NationService:
    """Service for nation-related business logic."""
    
    def __init__(self, api_client: PoliticsWarAPI, cache_service: CacheService):
        self.api_client = api_client
        self.cache_service = cache_service
    
    async def get_nation(self, nation_id: int) -> Optional[Nation]:
        """Get nation data by ID."""
        # Try cache first
        cache_key = f"nation:{nation_id}"
        cached_nation = await self.cache_service.get(cache_key)
        if cached_nation:
            return Nation.from_dict(cached_nation)
        
        # Fetch from API
        nation_data = await self.api_client.get_nation_data(nation_id)
        if not nation_data:
            return None
        
        nation = Nation.from_dict(nation_data)
        
        # Cache the result
        await self.cache_service.set(cache_key, nation.to_dict(), ttl=GameConstants.CACHE_TTL)
        
        return nation
    
    async def search_nations(self, query: str, limit: int = 50) -> List[Nation]:
        """Search for nations by name or leader."""
        # Try cache first
        cache_key = f"nation_search:{query}:{limit}"
        cached_results = await self.cache_service.get(cache_key)
        if cached_results:
            return [Nation.from_dict(nation_data) for nation_data in cached_results]
        
        # Fetch from API
        nations_data = await self.api_client.search_nations(query, limit)
        if not nations_data:
            return []
        
        nations = [Nation.from_dict(nation_data) for nation_data in nations_data]
        
        # Cache the results
        await self.cache_service.set(cache_key, [nation.to_dict() for nation in nations], ttl=GameConstants.CACHE_TTL)
        
        return nations
    
    async def get_nation_wars(self, nation_id: int) -> List[Dict[str, Any]]:
        """Get wars for a nation."""
        cache_key = f"nation_wars:{nation_id}"
        cached_wars = await self.cache_service.get(cache_key)
        if cached_wars:
            return cached_wars
        
        wars_data = await self.api_client.get_nation_wars(nation_id)
        if not wars_data:
            return []
        
        await self.cache_service.set(cache_key, wars_data, ttl=GameConstants.CACHE_TTL)
        
        return wars_data
    
    async def calculate_war_range(self, nation_score: float) -> tuple[float, float]:
        """Calculate war range for a nation."""
        min_score = nation_score * WAR_RANGE_MULTIPLIERS['min']
        max_score = nation_score * WAR_RANGE_MULTIPLIERS['max']
        return min_score, max_score
    
    async def find_raid_targets(
        self, 
        attacker_score: float, 
        max_targets: int = 20,
        exclude_alliances: List[str] = None
    ) -> List[RaidTarget]:
        """Find potential raid targets for a nation."""
        min_score, max_score = await self.calculate_war_range(attacker_score)
        
        # Get nations in range from cache
        nations_data = await self.cache_service.get_nations_in_range(min_score, max_score)
        if not nations_data:
            return []
        
        targets = []
        for nation_data in nations_data[:max_targets]:
            nation = Nation.from_dict(nation_data)
            
            # Skip invalid targets
            if not self._is_valid_raid_target(nation, exclude_alliances):
                continue
            
            # Calculate loot potential
            loot_potential = await self._calculate_loot_potential(nation)
            
            # Determine risk level
            risk_level = self._calculate_risk_level(nation)
            
            # Get alliance rank
            alliance_rank = await self._get_alliance_rank(nation.alliance_id)
            
            target = RaidTarget(
                nation=nation,
                loot_potential=loot_potential,
                risk_level=risk_level,
                war_range=True,  # Already filtered by score range
                alliance_rank=alliance_rank
            )
            
            targets.append(target)
        
        # Sort by loot potential (highest first)
        targets.sort(key=lambda x: x.loot_potential, reverse=True)
        
        return targets
    
    def _is_valid_raid_target(self, nation: Nation, exclude_alliances: List[str] = None) -> bool:
        """Check if a nation is a valid raid target."""
        # Skip inactive nations
        if not nation.is_active:
            return False
        
        # Skip beige nations
        if nation.is_beige:
            return False
        
        # Skip nations with too many defensive wars
        if nation.defensive_wars >= 3:
            return False
        
        # Skip excluded alliances
        if exclude_alliances:
            if (str(nation.alliance_id) in exclude_alliances or 
                nation.alliance_name in exclude_alliances):
                return False
        
        return True
    
    async def _calculate_loot_potential(self, nation: Nation) -> float:
        """Calculate potential loot from a nation."""
        # Base loot from resources
        base_loot = nation.total_resources_value * 0.1  # 10% of resources
        
        # Military value loot
        military_loot = nation.total_military_value * 0.1  # 10% of military value
        
        # City-based loot (simplified)
        city_loot = nation.cities * 50000  # $50k per city estimate
        
        # Recent war performance (simplified)
        war_modifier = 1.0
        # TODO: Implement actual war history analysis
        
        total_loot = (base_loot + military_loot + city_loot) * war_modifier
        
        return total_loot
    
    def _calculate_risk_level(self, nation: Nation) -> str:
        """Calculate risk level for a raid target."""
        # High risk: Strong military, many cities, top alliance
        if (nation.total_military_value > 1000000 or 
            nation.cities > 20 or 
            nation.alliance_id in [1, 2, 3]):  # Top alliances
            return 'high'
        
        # Medium risk: Moderate military, medium cities
        if (nation.total_military_value > 500000 or 
            nation.cities > 10):
            return 'medium'
        
        # Low risk: Weak military, few cities
        return 'low'
    
    async def _get_alliance_rank(self, alliance_id: int) -> int:
        """Get alliance rank by ID."""
        if alliance_id == 0:
            return 999  # No alliance
        
        cache_key = f"alliance_rank:{alliance_id}"
        cached_rank = await self.cache_service.get(cache_key)
        if cached_rank:
            return cached_rank
        
        # Fetch from API
        alliance_data = await self.api_client.get_alliance_data(alliance_id)
        rank = alliance_data.get('rank', 999) if alliance_data else 999
        
        # Cache the result
        await self.cache_service.set(cache_key, rank, ttl=GameConstants.CACHE_TTL)
        
        return rank
    
    async def calculate_warchest(self, nation: Nation) -> Dict[str, Any]:
        """Calculate warchest requirements for a nation."""
        # This would integrate with the existing calculate module
        # For now, return a simplified calculation
        
        # 5 days of military upkeep
        military_upkeep = (
            nation.soldiers * 1.25 * 5 +
            nation.tanks * 50 * 5 +
            nation.aircraft * 500 * 5 +
            nation.ships * 3375 * 5 +
            nation.missiles * 10000 * 5 +
            nation.nukes * 100000 * 5 +
            nation.spies * 50 * 5
        )
        
        # 5 days of city upkeep (simplified)
        city_upkeep = nation.cities * 1000 * 5
        
        total_warchest = military_upkeep + city_upkeep
        
        return {
            'total_warchest': total_warchest,
            'military_upkeep': military_upkeep,
            'city_upkeep': city_upkeep,
            'current_money': nation.money,
            'deficit': max(0, total_warchest - nation.money)
        }
