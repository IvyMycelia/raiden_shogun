"""
War data model.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class War:
    """War data model."""
    id: int
    attacker_id: int
    attacker_name: str
    defender_id: int
    defender_name: str
    war_type: str
    reason: str
    turns_left: int
    ground_control: int
    air_control: int
    naval_control: int
    attacker_military: Dict[str, int]
    defender_military: Dict[str, int]
    attacker_resistance: float
    defender_resistance: float
    attacker_war_points: int
    defender_war_points: int
    loot: Dict[str, float]
    created: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'War':
        """Create War from dictionary."""
        # Parse created timestamp
        created_str = data.get('created', '1970-01-01T00:00:00+00:00')
        try:
            created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
        except ValueError:
            created = datetime.fromisoformat('1970-01-01T00:00:00+00:00')
        
        return cls(
            id=data.get('id', 0),
            attacker_id=data.get('attacker_id', 0),
            attacker_name=data.get('attacker_name', 'Unknown'),
            defender_id=data.get('defender_id', 0),
            defender_name=data.get('defender_name', 'Unknown'),
            war_type=data.get('war_type', 'unknown'),
            reason=data.get('reason', ''),
            turns_left=data.get('turns_left', 0),
            ground_control=data.get('ground_control', 0),
            air_control=data.get('air_control', 0),
            naval_control=data.get('naval_control', 0),
            attacker_military=data.get('attacker_military', {}),
            defender_military=data.get('defender_military', {}),
            attacker_resistance=float(data.get('attacker_resistance', 0)),
            defender_resistance=float(data.get('defender_resistance', 0)),
            attacker_war_points=data.get('attacker_war_points', 0),
            defender_war_points=data.get('defender_war_points', 0),
            loot=data.get('loot', {}),
            created=created
        )
    
    def is_active(self) -> bool:
        """Check if war is still active."""
        return self.turns_left > 0
    
    def get_control_status(self) -> Dict[str, int]:
        """Get control status for all three areas."""
        return {
            'ground': self.ground_control,
            'air': self.air_control,
            'naval': self.naval_control
        }
    
    def get_total_loot_value(self) -> float:
        """Get total loot value in money."""
        return float(self.loot.get('money', 0))
    
    def get_war_duration(self) -> int:
        """Get war duration in turns."""
        return 60 - self.turns_left  # Wars last 60 turns max




