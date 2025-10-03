"""
Nation data model and related classes.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Nation:
    """Represents a nation in Politics and War."""
    
    # Basic info
    nation_id: int
    nation_name: str
    leader_name: str
    alliance_id: int
    alliance_name: str
    alliance_position: str
    
    # Stats
    score: float
    cities: int
    population: int
    infrastructure: float
    land_area: float
    
    # Military
    soldiers: int
    tanks: int
    aircraft: int
    ships: int
    missiles: int
    nukes: int
    spies: int
    
    # Resources
    money: float
    coal: float
    oil: float
    uranium: float
    iron: float
    bauxite: float
    lead: float
    gasoline: float
    munitions: float
    steel: float
    aluminum: float
    food: float
    
    # Status
    color: str
    beige_turns_remaining: int
    vm_turns: int
    defensive_wars: int
    offensive_wars: int
    last_active: datetime
    
    # Projects
    projects: List[Dict[str, Any]]
    
    # Cities
    cities_data: List[Dict[str, Any]]
    
    def __post_init__(self):
        """Validate nation data after initialization."""
        if self.nation_id <= 0:
            raise ValueError("Nation ID must be positive")
        if self.score < 0:
            raise ValueError("Score cannot be negative")
        if self.cities < 0:
            raise ValueError("Cities cannot be negative")
    
    @property
    def is_active(self) -> bool:
        """Check if nation is active (not in vacation mode)."""
        return self.vm_turns == 0
    
    @property
    def is_beige(self) -> bool:
        """Check if nation is on beige turns."""
        return self.beige_turns_remaining > 0
    
    @property
    def total_military_value(self) -> float:
        """Calculate total military value."""
        return (
            self.soldiers * 1.25 +
            self.tanks * 50 +
            self.aircraft * 500 +
            self.ships * 3375 +
            self.missiles * 10000 +
            self.nukes * 100000
        )
    
    @property
    def total_resources_value(self) -> float:
        """Calculate total resources value."""
        return (
            self.money +
            self.coal * 100 +
            self.oil * 100 +
            self.uranium * 1000 +
            self.iron * 100 +
            self.bauxite * 100 +
            self.lead * 100 +
            self.gasoline * 1000 +
            self.munitions * 1000 +
            self.steel * 1000 +
            self.aluminum * 1000 +
            self.food * 100
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert nation to dictionary."""
        return {
            'nation_id': self.nation_id,
            'nation_name': self.nation_name,
            'leader_name': self.leader_name,
            'alliance_id': self.alliance_id,
            'alliance_name': self.alliance_name,
            'alliance_position': self.alliance_position,
            'score': self.score,
            'cities': self.cities,
            'population': self.population,
            'infrastructure': self.infrastructure,
            'land_area': self.land_area,
            'soldiers': self.soldiers,
            'tanks': self.tanks,
            'aircraft': self.aircraft,
            'ships': self.ships,
            'missiles': self.missiles,
            'nukes': self.nukes,
            'spies': self.spies,
            'money': self.money,
            'coal': self.coal,
            'oil': self.oil,
            'uranium': self.uranium,
            'iron': self.iron,
            'bauxite': self.bauxite,
            'lead': self.lead,
            'gasoline': self.gasoline,
            'munitions': self.munitions,
            'steel': self.steel,
            'aluminum': self.aluminum,
            'food': self.food,
            'color': self.color,
            'beige_turns_remaining': self.beige_turns_remaining,
            'vm_turns': self.vm_turns,
            'defensive_wars': self.defensive_wars,
            'offensive_wars': self.offensive_wars,
            'last_active': self.last_active.isoformat(),
            'projects': self.projects,
            'cities_data': self.cities_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Nation':
        """Create nation from dictionary."""
        return cls(
            nation_id=data['nation_id'],
            nation_name=data['nation_name'],
            leader_name=data['leader_name'],
            alliance_id=data.get('alliance_id', 0),
            alliance_name=data.get('alliance_name', 'None'),
            alliance_position=data.get('alliance_position', 'NONE'),
            score=data['score'],
            cities=data['cities'],
            population=data.get('population', 0),
            infrastructure=data.get('infrastructure', 0.0),
            land_area=data.get('land_area', 0.0),
            soldiers=data.get('soldiers', 0),
            tanks=data.get('tanks', 0),
            aircraft=data.get('aircraft', 0),
            ships=data.get('ships', 0),
            missiles=data.get('missiles', 0),
            nukes=data.get('nukes', 0),
            spies=data.get('spies', 0),
            money=data.get('money', 0.0),
            coal=data.get('coal', 0.0),
            oil=data.get('oil', 0.0),
            uranium=data.get('uranium', 0.0),
            iron=data.get('iron', 0.0),
            bauxite=data.get('bauxite', 0.0),
            lead=data.get('lead', 0.0),
            gasoline=data.get('gasoline', 0.0),
            munitions=data.get('munitions', 0.0),
            steel=data.get('steel', 0.0),
            aluminum=data.get('aluminum', 0.0),
            food=data.get('food', 0.0),
            color=data.get('color', 'gray'),
            beige_turns_remaining=data.get('beige_turns_remaining', 0),
            vm_turns=data.get('vm_turns', 0),
            defensive_wars=data.get('defensive_wars', 0),
            offensive_wars=data.get('offensive_wars', 0),
            last_active=datetime.fromisoformat(data.get('last_active', '1970-01-01T00:00:00+00:00')),
            projects=data.get('projects', []),
            cities_data=data.get('cities_data', [])
        )


@dataclass
class RaidTarget:
    """Represents a potential raid target."""
    
    nation: Nation
    loot_potential: float
    risk_level: str  # 'low', 'medium', 'high'
    war_range: bool
    alliance_rank: int
    
    def __post_init__(self):
        """Validate raid target data."""
        if self.loot_potential < 0:
            raise ValueError("Loot potential cannot be negative")
        if self.risk_level not in ['low', 'medium', 'high']:
            raise ValueError("Risk level must be 'low', 'medium', or 'high'")
    
    @property
    def is_valid_target(self) -> bool:
        """Check if this is a valid raid target."""
        return (
            self.nation.is_active and
            not self.nation.is_beige and
            self.nation.defensive_wars < 3 and
            self.alliance_rank > 60 and
            self.war_range
        )
