"""
Service for raid-related operations.
"""
from typing import List, Dict, Any, Optional
import discord

from models.nation import Nation, RaidTarget
from services.nation_service import NationService
from services.cache_service import CacheService
from config.constants import GameConstants, ALLIANCE_RANK_THRESHOLDS


class RaidService:
    """Service for raid-related business logic."""
    
    def __init__(self, nation_service: NationService, cache_service: CacheService):
        self.nation_service = nation_service
        self.cache_service = cache_service
    
    async def find_raid_targets(
        self,
        attacker_score: float,
        max_targets: int = 20,
        exclude_alliances: List[str] = None
    ) -> List[RaidTarget]:
        """Find potential raid targets for a nation."""
        return await self.nation_service.find_raid_targets(
            attacker_score, max_targets, exclude_alliances
        )
    
    async def calculate_raid_potential(
        self, 
        target: Nation, 
        attacker_score: float
    ) -> Dict[str, Any]:
        """Calculate detailed raid potential for a target."""
        # Basic loot calculation
        base_loot = target.total_resources_value * 0.1
        military_loot = target.total_military_value * 0.1
        city_loot = target.cities * 50000
        
        # War range check
        min_score, max_score = await self.nation_service.calculate_war_range(attacker_score)
        in_range = min_score <= target.score <= max_score
        
        # Risk assessment
        risk_factors = []
        risk_score = 0
        
        if target.defensive_wars >= 3:
            risk_factors.append("High defensive wars")
            risk_score += 3
        
        if target.cities > 20:
            risk_factors.append("Large nation")
            risk_score += 2
        
        if target.total_military_value > 1000000:
            risk_factors.append("Strong military")
            risk_score += 2
        
        # Alliance risk
        alliance_rank = await self.nation_service._get_alliance_rank(target.alliance_id)
        if alliance_rank <= ALLIANCE_RANK_THRESHOLDS['top_alliance']:
            risk_factors.append("Top alliance")
            risk_score += 3
        
        # Determine risk level
        if risk_score >= 5:
            risk_level = "high"
        elif risk_score >= 2:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Calculate total potential
        total_potential = base_loot + military_loot + city_loot
        
        return {
            'total_potential': total_potential,
            'base_loot': base_loot,
            'military_loot': military_loot,
            'city_loot': city_loot,
            'in_range': in_range,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'risk_score': risk_score,
            'alliance_rank': alliance_rank
        }
    
    async def format_raid_results(
        self, 
        targets: List[RaidTarget], 
        min_score: float, 
        max_score: float
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Format raid results for Discord display."""
        from utils.raid_paginator import RaidPaginator
        
        paginator = RaidPaginator(targets, min_score, max_score)
        embed = paginator.create_embed(0)
        view = paginator.get_view()
        
        return embed, view
    
    async def get_raid_statistics(self, targets: List[RaidTarget]) -> Dict[str, Any]:
        """Get statistics about raid targets."""
        if not targets:
            return {
                'total_targets': 0,
                'average_loot': 0,
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0},
                'alliance_distribution': {}
            }
        
        total_loot = sum(target.loot_potential for target in targets)
        average_loot = total_loot / len(targets)
        
        risk_distribution = {'low': 0, 'medium': 0, 'high': 0}
        alliance_distribution = {}
        
        for target in targets:
            # Count risk levels
            risk_distribution[target.risk_level] += 1
            
            # Count alliances
            alliance_name = target.nation.alliance_name
            alliance_distribution[alliance_name] = alliance_distribution.get(alliance_name, 0) + 1
        
        return {
            'total_targets': len(targets),
            'average_loot': average_loot,
            'total_loot': total_loot,
            'risk_distribution': risk_distribution,
            'alliance_distribution': alliance_distribution,
            'top_alliances': sorted(
                alliance_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
    
    async def validate_raid_target(self, target: Nation, attacker_score: float) -> Dict[str, Any]:
        """Validate if a target is suitable for raiding."""
        issues = []
        warnings = []
        
        # Check if target is active
        if not target.is_active:
            issues.append("Target is in vacation mode")
        
        # Check if target is on beige
        if target.is_beige:
            issues.append("Target is on beige turns")
        
        # Check defensive wars
        if target.defensive_wars >= 3:
            issues.append(f"Target has {target.defensive_wars} defensive wars")
        
        # Check war range
        min_score, max_score = await self.nation_service.calculate_war_range(attacker_score)
        if not (min_score <= target.score <= max_score):
            issues.append("Target is outside war range")
        
        # Check alliance rank
        alliance_rank = await self.nation_service._get_alliance_rank(target.alliance_id)
        if alliance_rank <= ALLIANCE_RANK_THRESHOLDS['top_alliance']:
            warnings.append("Target is in a top alliance")
        
        # Check military strength
        if target.total_military_value > 1000000:
            warnings.append("Target has strong military")
        
        # Check city count
        if target.cities > 20:
            warnings.append("Target is a large nation")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'alliance_rank': alliance_rank,
            'in_range': min_score <= target.score <= max_score
        }
