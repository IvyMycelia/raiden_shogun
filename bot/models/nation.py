"""
Nation and City data models.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class City:
    """City data model."""
    id: int
    name: str
    nation_id: int
    infrastructure: int
    land: int
    population: int
    age: int
    pollution: int
    commerce: int
    crime: float
    disease: float
    power: int
    power_plants: Dict[str, int]
    improvements: Dict[str, int]
    resources: Dict[str, int]
    # Direct building fields
    barracks: int = 0
    hangar: int = 0
    drydock: int = 0
    factory: int = 0
    oil_refinery: int = 0
    steel_mill: int = 0
    aluminum_refinery: int = 0
    munitions_factory: int = 0
    coal_mine: int = 0
    iron_mine: int = 0
    uranium_mine: int = 0
    oil_well: int = 0
    bauxite_mine: int = 0
    lead_mine: int = 0
    police_station: int = 0
    hospital: int = 0
    recycling_center: int = 0
    subway: int = 0
    supermarket: int = 0
    bank: int = 0
    shopping_mall: int = 0
    stadium: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'City':
        """Create City from dictionary."""
        return cls(
            id=data.get('id', 0),
            name=data.get('name', 'Unknown'),
            nation_id=data.get('nation_id', 0),
            infrastructure=data.get('infrastructure', 0),
            land=data.get('land', 0),
            population=data.get('population', 0),
            age=data.get('age', 0),
            pollution=data.get('pollution', 0),
            commerce=data.get('commerce', 0),
            crime=data.get('crime', 0.0),
            disease=data.get('disease', 0.0),
            power=data.get('power', 0),
            power_plants=data.get('power_plants', {}),
            improvements=data.get('improvements', {}),
            resources=data.get('resources', {}),
            # Direct building fields
            barracks=data.get('barracks', 0),
            hangar=data.get('hangar', 0),
            drydock=data.get('drydock', 0),
            factory=data.get('factory', 0),
            oil_refinery=data.get('oil_refinery', 0),
            steel_mill=data.get('steel_mill', 0),
            aluminum_refinery=data.get('aluminum_refinery', 0),
            munitions_factory=data.get('munitions_factory', 0),
            coal_mine=data.get('coal_mine', 0),
            iron_mine=data.get('iron_mine', 0),
            uranium_mine=data.get('uranium_mine', 0),
            oil_well=data.get('oil_well', 0),
            bauxite_mine=data.get('bauxite_mine', 0),
            lead_mine=data.get('lead_mine', 0),
            police_station=data.get('police_station', 0),
            hospital=data.get('hospital', 0),
            recycling_center=data.get('recycling_center', 0),
            subway=data.get('subway', 0),
            supermarket=data.get('supermarket', 0),
            bank=data.get('bank', 0),
            shopping_mall=data.get('shopping_mall', 0),
            stadium=data.get('stadium', 0)
        )

@dataclass
class Nation:
    """Nation data model."""
    id: int
    name: str
    leader_name: str
    score: float
    cities: int
    color: str
    alliance_id: int
    alliance_name: str
    alliance_position: str
    last_active: datetime
    date: datetime
    discord_username: str
    soldiers: int
    tanks: int
    aircraft: int
    ships: int
    spies: int
    missiles: int
    nukes: int
    projects: int
    project_bits: str
    turns_since_last_project: int
    wars_won: int
    wars_lost: int
    central_intelligence_agency: bool
    vmode: bool
    beige_turns: int
    defensive_wars: int
    offensive_wars: int
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
    credits: int
    gdp: float
    military_research: Dict[str, int]
    cities_data: List[City]
    wars: List[Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Nation':
        """Create Nation from dictionary."""
        try:
            # Parse last_active timestamp
            last_active_str = data.get('last_active', '1970-01-01T00:00:00+00:00')
            try:
                last_active = datetime.fromisoformat(last_active_str.replace('Z', '+00:00'))
            except ValueError:
                last_active = datetime.fromisoformat('1970-01-01T00:00:00+00:00')
            
            # Parse date timestamp
            date_str = data.get('date', '1970-01-01T00:00:00+00:00')
            try:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                date = datetime.fromisoformat('1970-01-01T00:00:00+00:00')
            
            # Parse cities data
            cities_data = []
            for city_data in data.get('cities', []):
                try:
                    cities_data.append(City.from_dict(city_data))
                except Exception as e:
                    print(f"Error creating city from data: {e}")
                    print(f"City data: {city_data}")
                    raise
            
            return cls(
            id=data.get('id', 0),
            name=data.get('nation_name', 'Unknown'),
            leader_name=data.get('leader_name', 'Unknown'),
            score=float(data.get('score', 0)),
            cities=len(cities_data),
            color=data.get('color', 'gray'),
            alliance_id=int(data.get('alliance_id', 0)),
            alliance_name=data.get('alliance', {}).get('name', 'None') if isinstance(data.get('alliance'), dict) else 'None',
            alliance_position=data.get('alliance_position', 'MEMBER'),
            last_active=last_active,
            date=date,
            discord_username=data.get('discord', ''),
            soldiers=int(data.get('soldiers', 0)),
            tanks=int(data.get('tanks', 0)),
            aircraft=int(data.get('aircraft', 0)),
            ships=int(data.get('ships', 0)),
            spies=int(data.get('spies', 0)),
            missiles=int(data.get('missiles', 0)),
            nukes=int(data.get('nukes', 0)),
            projects=int(data.get('projects', 0)),
            project_bits=str(data.get('project_bits', '')),
            turns_since_last_project=int(data.get('turns_since_last_project', 0)),
            wars_won=int(data.get('wars_won', 0)),
            wars_lost=int(data.get('wars_lost', 0)),
            central_intelligence_agency=bool(data.get('central_intelligence_agency', False)),
            vmode=bool(data.get('vmode', 0)),
            beige_turns=int(data.get('beige_turns', 0)),
            defensive_wars=len(data.get('defensive_wars', [])),
            offensive_wars=len(data.get('offensive_wars', [])),
            money=float(data.get('money', 0)),
            coal=float(data.get('coal', 0)),
            oil=float(data.get('oil', 0)),
            uranium=float(data.get('uranium', 0)),
            iron=float(data.get('iron', 0)),
            bauxite=float(data.get('bauxite', 0)),
            lead=float(data.get('lead', 0)),
            gasoline=float(data.get('gasoline', 0)),
            munitions=float(data.get('munitions', 0)),
            steel=float(data.get('steel', 0)),
            aluminum=float(data.get('aluminum', 0)),
            food=float(data.get('food', 0)),
            credits=int(data.get('credits', 0)),
            gdp=float(data.get('gdp', 0)),
            military_research=data.get('military_research', {
                'ground_capacity': 0,
                'air_capacity': 0,
                'naval_capacity': 0
            }),
            cities_data=cities_data,
            wars=data.get('wars', [])
        )
        except Exception as e:
            print(f"Error in Nation.from_dict: {e}")
            print(f"Data keys: {list(data.keys()) if data else 'None'}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    def get_military_capacity(self) -> Dict[str, int]:
        """Calculate military capacity from city buildings."""
        capacity = {"soldiers": 0, "tanks": 0, "aircraft": 0, "ships": 0}
        
        for city in self.cities_data:
            capacity["soldiers"] += city.improvements.get("barracks", 0) * 3000
            capacity["tanks"] += city.improvements.get("factory", 0) * 250
            capacity["aircraft"] += city.improvements.get("hangar", 0) * 15
            capacity["ships"] += city.improvements.get("drydock", 0) * 5
        
        return capacity
    
    def get_military_usage(self) -> Dict[str, int]:
        """Get current military unit counts."""
        return {
            "soldiers": self.soldiers,
            "tanks": self.tanks,
            "aircraft": self.aircraft,
            "ships": self.ships
        }
    
    def get_military_usage_percentage(self) -> Dict[str, float]:
        """Calculate military usage percentage."""
        capacity = self.get_military_capacity()
        usage = self.get_military_usage()
        
        percentages = {}
        for unit_type in capacity:
            if capacity[unit_type] > 0:
                percentages[unit_type] = (usage[unit_type] / capacity[unit_type]) * 100
            else:
                percentages[unit_type] = 0.0
        
        return percentages
    
    def is_active(self) -> bool:
        """Check if nation is active (not in vmode, has cities)."""
        return not self.vmode and self.cities > 0
    
    def is_in_war_range(self, target_score: float) -> bool:
        """Check if this nation is in war range of target score."""
        min_score = target_score * 0.75
        max_score = target_score * 1.25
        return min_score <= self.score <= max_score
    
    def get_role(self) -> str:
        """Get nation role based on city count."""
        return "Whale" if self.cities >= 15 else "Raider"
    
    def get_total_infrastructure(self) -> int:
        """Get total infrastructure across all cities."""
        return sum(city.infrastructure for city in self.cities_data)
    
    def get_total_land(self) -> int:
        """Get total land across all cities."""
        return sum(city.land for city in self.cities_data)
    
    def get_total_population(self) -> int:
        """Get total population across all cities."""
        return sum(city.population for city in self.cities_data)
