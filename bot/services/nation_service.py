"""
Nation service for business logic.
"""

import asyncio
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.nation import Nation, City
from api.politics_war_api import api
from config.constants import GameConstants
from utils.logging import get_logger

logger = get_logger('nation_service')

class NationService:
    """Service for nation-related business logic."""
    
    def __init__(self):
        self.api = api
    
    async def get_nation(self, nation_id: int, scope: str = "everything_scope") -> Optional[Nation]:
        """Get nation data by ID."""
        data = await self.api.get_nation_data(nation_id, scope)
        if data:
            return Nation.from_dict(data)
        logger.warning(f"No data returned for nation ID: {nation_id}")
        return None
    
    async def get_nation_basic(self, nation_id: int, scope: str = "everything_scope") -> Optional[Dict]:
        """Get basic nation data without cities."""
        data = await self.api.get_nation_data(nation_id, scope)
        if data:
            # Remove cities data for basic info
            data.pop('cities', None)
            return data
        return None
    
    def calculate_warchest(self, nation: Nation) -> Dict[str, Any]:
        """Calculate warchest requirements for a nation."""
        try:
            # Calculate military resource usage per turn
            gasoline_per_turn = (
                (nation.soldiers / 5000) + 
                (nation.tanks / 100) + 
                (nation.aircraft / 4) + 
                2.5
            )
            munitions_per_turn = (
                (nation.soldiers / 5000) + 
                (nation.tanks / 100) + 
                (nation.aircraft / 4) + 
                2
            )
            steel_per_turn = (nation.tanks / 100) + (nation.ships / 5)
            aluminum_per_turn = nation.aircraft / 4
            
            # Calculate total requirements for 60 turns
            required_gasoline = gasoline_per_turn * GameConstants.WAR_DURATION_TURNS
            required_munitions = munitions_per_turn * GameConstants.WAR_DURATION_TURNS
            required_steel = steel_per_turn * GameConstants.WAR_DURATION_TURNS
            required_aluminum = aluminum_per_turn * GameConstants.WAR_DURATION_TURNS
            
            # Calculate building upkeep costs
            total_upkeep = 0
            for city in nation.cities_data:
                for building, count in city.improvements.items():
                    if building in GameConstants.BUILDING_COSTS:
                        total_upkeep += GameConstants.BUILDING_COSTS[building] * count
            
            # Calculate military upkeep costs
            military_upkeep = (
                nation.soldiers * GameConstants.MILITARY_COSTS["soldiers"] +
                nation.tanks * GameConstants.MILITARY_COSTS["tanks"] +
                nation.aircraft * GameConstants.MILITARY_COSTS["aircraft"] +
                nation.ships * GameConstants.MILITARY_COSTS["ships"]
            )
            
            # Calculate resource consumption
            coal_consumption = 0
            oil_consumption = 0
            uranium_consumption = 0
            iron_consumption = 0
            bauxite_consumption = 0
            lead_consumption = 0
            
            for city in nation.cities_data:
                power_plants = city.power_plants
                improvements = city.improvements
                
                coal_consumption += (
                    power_plants.get("coal_power", 0) * GameConstants.RESOURCE_CONSUMPTION["coal_per_coal_power"] +
                    improvements.get("steel_mill", 0) * GameConstants.RESOURCE_CONSUMPTION["coal_per_steel_mill"]
                )
                
                oil_consumption += (
                    power_plants.get("oil_power", 0) * GameConstants.RESOURCE_CONSUMPTION["oil_per_oil_power"] +
                    improvements.get("oil_refinery", 0) * GameConstants.RESOURCE_CONSUMPTION["oil_per_refinery"]
                )
                
                uranium_consumption += power_plants.get("nuclear_power", 0) * GameConstants.RESOURCE_CONSUMPTION["uranium_per_nuclear"]
                iron_consumption += improvements.get("steel_mill", 0) * GameConstants.RESOURCE_CONSUMPTION["iron_per_steel_mill"]
                bauxite_consumption += improvements.get("aluminum_refinery", 0) * GameConstants.RESOURCE_CONSUMPTION["bauxite_per_aluminum"]
                lead_consumption += improvements.get("munitions_factory", 0) * GameConstants.RESOURCE_CONSUMPTION["lead_per_munitions"]
            
            # Calculate food consumption
            total_population = sum(city.population for city in nation.cities_data)
            food_consumption = total_population * GameConstants.FOOD_CONSUMPTION_RATE
            
            # Calculate total requirements
            required_money = (total_upkeep + military_upkeep) * GameConstants.WAR_DURATION_TURNS
            required_coal = coal_consumption * GameConstants.WAR_DURATION_TURNS
            required_oil = oil_consumption * GameConstants.WAR_DURATION_TURNS
            required_uranium = uranium_consumption * GameConstants.WAR_DURATION_TURNS
            required_iron = iron_consumption * GameConstants.WAR_DURATION_TURNS
            required_bauxite = bauxite_consumption * GameConstants.WAR_DURATION_TURNS
            required_lead = lead_consumption * GameConstants.WAR_DURATION_TURNS
            required_food = food_consumption * GameConstants.WAR_DURATION_TURNS
            
            # Apply city scaling for nations > 15 cities
            if nation.cities > GameConstants.CITY_SCALING_THRESHOLD:
                additional_cities = nation.cities - GameConstants.CITY_SCALING_THRESHOLD
                reduction_factor = 1 - (additional_cities * GameConstants.CITY_SCALING_REDUCTION)
                reduction_factor = max(reduction_factor, GameConstants.MIN_SCALING_FACTOR)
                
                required_money *= reduction_factor
                required_coal *= reduction_factor
                required_oil *= reduction_factor
                required_uranium *= reduction_factor
                required_iron *= reduction_factor
                required_bauxite *= reduction_factor
                required_lead *= reduction_factor
                required_food *= reduction_factor
                required_gasoline *= reduction_factor
                required_munitions *= reduction_factor
                required_steel *= reduction_factor
                required_aluminum *= reduction_factor
            
            # Calculate deficits
            deficits = {
                'money': max(required_money - nation.money, 0),
                'coal': max(required_coal - nation.coal, 0),
                'oil': max(required_oil - nation.oil, 0),
                'uranium': max(required_uranium - nation.uranium, 0),
                'iron': max(required_iron - nation.iron, 0),
                'bauxite': max(required_bauxite - nation.bauxite, 0),
                'lead': max(required_lead - nation.lead, 0),
                'gasoline': max(required_gasoline - nation.gasoline, 0),
                'munitions': max(required_munitions - nation.munitions, 0),
                'steel': max(required_steel - nation.steel, 0),
                'aluminum': max(required_aluminum - nation.aluminum, 0),
                'food': max(required_food - nation.food, 0),
                'credits': max(0 - nation.credits, 0)
            }
            
            # Calculate supplies
            supplies = {
                'money': required_money,
                'coal': required_coal,
                'oil': required_oil,
                'uranium': required_uranium,
                'iron': required_iron,
                'bauxite': required_bauxite,
                'lead': required_lead,
                'gasoline': required_gasoline,
                'munitions': required_munitions,
                'steel': required_steel,
                'aluminum': required_aluminum,
                'food': required_food,
                'credits': 0
            }
            
            return {
                'deficits': deficits,
                'supplies': supplies,
                'total_cost': required_money,
                'military_upkeep': military_upkeep,
                'building_upkeep': total_upkeep
            }
        
        except Exception as e:
            return None
    
    def calculate_military_capacity(self, nation: Nation) -> Dict[str, int]:
        """Calculate military capacity from city buildings."""
        return nation.get_military_capacity()
    
    def calculate_military_usage(self, nation: Nation) -> Dict[str, int]:
        """Calculate current military usage."""
        return nation.get_military_usage()
    
    def calculate_military_usage_percentage(self, nation: Nation) -> Dict[str, float]:
        """Calculate military usage percentage."""
        return nation.get_military_usage_percentage()
    
    def check_mmr_compliance(self, nation: Nation) -> Dict[str, Any]:
        """Check MMR compliance for a nation."""
        role = nation.get_role()
        violations = []
        
        for city in nation.cities_data:
            city_violations = []
            
            if role == "Raider":
                if city.improvements.get("barracks", 0) < 5:
                    city_violations.append(f"Barracks: {city.improvements.get('barracks', 0)}/5")
                if city.improvements.get("hangar", 0) < 5:
                    city_violations.append(f"Hangar: {city.improvements.get('hangar', 0)}/5")
            else:  # Whale
                if city.improvements.get("factory", 0) < 2:
                    city_violations.append(f"Factory: {city.improvements.get('factory', 0)}/2")
                if city.improvements.get("hangar", 0) < 5:
                    city_violations.append(f"Hangar: {city.improvements.get('hangar', 0)}/5")
            
            if city_violations:
                violations.append({
                    'city_name': city.name,
                    'violations': city_violations
                })
        
        return {
            'role': role,
            'compliant': len(violations) == 0,
            'violations': violations
        }
    
    def calculate_loot_potential(self, nation: Nation, wars: List[Dict] = None) -> float:
        """Calculate loot potential for a nation."""
        base_loot = 0.0
        
        # GDP-based loot (10% of GDP)
        base_loot += nation.gdp * GameConstants.GDP_LOOT_MULTIPLIER
        
        # Military value-based loot (10% of military value)
        military_value = (
            nation.soldiers * GameConstants.MILITARY_UNIT_VALUES["soldiers"] +
            nation.tanks * GameConstants.MILITARY_UNIT_VALUES["tanks"] +
            nation.aircraft * GameConstants.MILITARY_UNIT_VALUES["aircraft"] +
            nation.ships * GameConstants.MILITARY_UNIT_VALUES["ships"]
        )
        base_loot += military_value * GameConstants.MILITARY_LOOT_MULTIPLIER
        
        # City-based loot (5% of estimated city value)
        if nation.cities > 0:
            city_loot = nation.cities * GameConstants.CITY_VALUE_ESTIMATE
            base_loot += city_loot * GameConstants.CITY_LOOT_MULTIPLIER
        
        # War performance modifier
        war_modifier = 1.0
        if wars:
            total_loot = sum(war.get('loot', {}).get('money', 0) for war in wars)
            if total_loot > 0:
                war_modifier = 1.0 + (total_loot / len(wars)) / 1000000  # 1% per $1M average loot
        
        return base_loot * war_modifier
