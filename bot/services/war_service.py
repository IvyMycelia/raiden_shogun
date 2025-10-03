"""
War service for business logic.
"""

from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.war import War
from api.politics_war_api import api

class WarService:
    """Service for war-related business logic."""
    
    def __init__(self):
        self.api = api
    
    async def get_war(self, war_id: int) -> Optional[War]:
        """Get war data by ID."""
        data = await self.api.get_war_data(war_id, "everything_scope")
        if data:
            return War.from_dict(data)
        return None
    
    def get_active_wars(self, nation: Dict) -> List[Dict]:
        """Get active wars for a nation."""
        wars = nation.get('wars', [])
        return [war for war in wars if war.get('turns_left', 0) > 0]
    
    def get_offensive_wars(self, nation: Dict) -> List[Dict]:
        """Get offensive wars for a nation."""
        wars = self.get_active_wars(nation)
        return [war for war in wars if war.get('attacker_id') == nation.get('id')]
    
    def get_defensive_wars(self, nation: Dict) -> List[Dict]:
        """Get defensive wars for a nation."""
        wars = self.get_active_wars(nation)
        return [war for war in wars if war.get('defender_id') == nation.get('id')]
    
    def calculate_war_strength(self, military: Dict[str, int]) -> float:
        """Calculate military strength for war."""
        return (
            military.get('soldiers', 0) * 0.5 +
            military.get('tanks', 0) * 5 +
            military.get('aircraft', 0) * 10 +
            military.get('ships', 0) * 20
        )
    
    def is_in_war_range(self, attacker_score: float, defender_score: float) -> bool:
        """Check if two nations are in war range."""
        min_score = attacker_score * 0.75
        max_score = attacker_score * 1.25
        return min_score <= defender_score <= max_score
    
    def get_war_control_status(self, war: Dict) -> Dict[str, str]:
        """Get war control status."""
        ground = war.get('ground_control', 0)
        air = war.get('air_control', 0)
        naval = war.get('naval_control', 0)
        
        return {
            'ground': 'Attacker' if ground > 0 else 'Defender' if ground < 0 else 'Neutral',
            'air': 'Attacker' if air > 0 else 'Defender' if air < 0 else 'Neutral',
            'naval': 'Attacker' if naval > 0 else 'Defender' if naval < 0 else 'Neutral'
        }
    
    def calculate_war_progress(self, war: Dict) -> Dict[str, float]:
        """Calculate war progress."""
        turns_left = war.get('turns_left', 0)
        total_turns = 60  # Wars last 60 turns max
        progress = ((total_turns - turns_left) / total_turns) * 100
        
        return {
            'progress_percentage': progress,
            'turns_remaining': turns_left,
            'turns_elapsed': total_turns - turns_left
        }
