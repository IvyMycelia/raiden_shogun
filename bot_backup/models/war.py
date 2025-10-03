"""
War data model and related classes.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class WarType(Enum):
    """Types of wars."""
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"


class WarStatus(Enum):
    """War status."""
    ACTIVE = "active"
    ENDED = "ended"
    PEACE = "peace"


@dataclass
class War:
    """Represents a war in Politics and War."""
    
    # Basic info
    war_id: int
    war_type: WarType
    status: WarStatus
    
    # Participants
    attacker_id: int
    attacker_name: str
    attacker_alliance_id: int
    attacker_alliance_name: str
    
    defender_id: int
    defender_name: str
    defender_alliance_id: int
    defender_alliance_name: str
    
    # War details
    ground_control: str  # attacker or defender
    air_superiority: str  # attacker or defender
    naval_blockade: str  # attacker or defender
    
    # Loot
    money_looted: float
    coal_looted: float
    oil_looted: float
    uranium_looted: float
    iron_looted: float
    bauxite_looted: float
    lead_looted: float
    gasoline_looted: float
    munitions_looted: float
    steel_looted: float
    aluminum_looted: float
    food_looted: float
    
    # Timestamps
    date: datetime
    turns_left: int
    
    def __post_init__(self):
        """Validate war data after initialization."""
        if self.war_id <= 0:
            raise ValueError("War ID must be positive")
        if self.attacker_id <= 0 or self.defender_id <= 0:
            raise ValueError("Attacker and defender IDs must be positive")
    
    @property
    def total_loot_value(self) -> float:
        """Calculate total loot value."""
        return (
            self.money_looted +
            self.coal_looted * 100 +
            self.oil_looted * 100 +
            self.uranium_looted * 1000 +
            self.iron_looted * 100 +
            self.bauxite_looted * 100 +
            self.lead_looted * 100 +
            self.gasoline_looted * 1000 +
            self.munitions_looted * 1000 +
            self.steel_looted * 1000 +
            self.aluminum_looted * 1000 +
            self.food_looted * 100
        )
    
    @property
    def is_active(self) -> bool:
        """Check if war is still active."""
        return self.status == WarStatus.ACTIVE and self.turns_left > 0
    
    @property
    def is_offensive(self) -> bool:
        """Check if this is an offensive war."""
        return self.war_type == WarType.OFFENSIVE
    
    @property
    def is_defensive(self) -> bool:
        """Check if this is a defensive war."""
        return self.war_type == WarType.DEFENSIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert war to dictionary."""
        return {
            'war_id': self.war_id,
            'war_type': self.war_type.value,
            'status': self.status.value,
            'attacker_id': self.attacker_id,
            'attacker_name': self.attacker_name,
            'attacker_alliance_id': self.attacker_alliance_id,
            'attacker_alliance_name': self.attacker_alliance_name,
            'defender_id': self.defender_id,
            'defender_name': self.defender_name,
            'defender_alliance_id': self.defender_alliance_id,
            'defender_alliance_name': self.defender_alliance_name,
            'ground_control': self.ground_control,
            'air_superiority': self.air_superiority,
            'naval_blockade': self.naval_blockade,
            'money_looted': self.money_looted,
            'coal_looted': self.coal_looted,
            'oil_looted': self.oil_looted,
            'uranium_looted': self.uranium_looted,
            'iron_looted': self.iron_looted,
            'bauxite_looted': self.bauxite_looted,
            'lead_looted': self.lead_looted,
            'gasoline_looted': self.gasoline_looted,
            'munitions_looted': self.munitions_looted,
            'steel_looted': self.steel_looted,
            'aluminum_looted': self.aluminum_looted,
            'food_looted': self.food_looted,
            'date': self.date.isoformat(),
            'turns_left': self.turns_left
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'War':
        """Create war from dictionary."""
        return cls(
            war_id=data['war_id'],
            war_type=WarType(data.get('war_type', 'offensive')),
            status=WarStatus(data.get('status', 'active')),
            attacker_id=data['attacker_id'],
            attacker_name=data['attacker_name'],
            attacker_alliance_id=data.get('attacker_alliance_id', 0),
            attacker_alliance_name=data.get('attacker_alliance_name', 'None'),
            defender_id=data['defender_id'],
            defender_name=data['defender_name'],
            defender_alliance_id=data.get('defender_alliance_id', 0),
            defender_alliance_name=data.get('defender_alliance_name', 'None'),
            ground_control=data.get('ground_control', ''),
            air_superiority=data.get('air_superiority', ''),
            naval_blockade=data.get('naval_blockade', ''),
            money_looted=data.get('money_looted', 0.0),
            coal_looted=data.get('coal_looted', 0.0),
            oil_looted=data.get('oil_looted', 0.0),
            uranium_looted=data.get('uranium_looted', 0.0),
            iron_looted=data.get('iron_looted', 0.0),
            bauxite_looted=data.get('bauxite_looted', 0.0),
            lead_looted=data.get('lead_looted', 0.0),
            gasoline_looted=data.get('gasoline_looted', 0.0),
            munitions_looted=data.get('munitions_looted', 0.0),
            steel_looted=data.get('steel_looted', 0.0),
            aluminum_looted=data.get('aluminum_looted', 0.0),
            food_looted=data.get('food_looted', 0.0),
            date=datetime.fromisoformat(data.get('date', '1970-01-01T00:00:00+00:00')),
            turns_left=data.get('turns_left', 0)
        )


@dataclass
class WarSummary:
    """Summary of wars for a nation."""
    
    nation_id: int
    active_wars: List[War]
    recent_wars: List[War]
    total_offensive: int
    total_defensive: int
    
    @property
    def total_active_wars(self) -> int:
        """Get total number of active wars."""
        return len(self.active_wars)
    
    @property
    def can_declare_war(self) -> bool:
        """Check if nation can declare more wars."""
        return self.total_offensive < 5  # Max 5 offensive wars
    
    def get_wars_by_type(self, war_type: WarType) -> List[War]:
        """Get wars by type."""
        return [war for war in self.active_wars if war.war_type == war_type]
