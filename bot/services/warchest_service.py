"""
Warchest calculation service.
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger

logger = get_logger('warchest_service')

class WarchestService:
    """Service for warchest calculations using simple city-based formula."""
    
    def calculate_warchest(self, nation_info: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
        """Calculate warchest requirements for a nation using simple city-based formula."""
        try:
            # Get cities data - could be a list of cities or just a count
            cities_data = nation_info.get("cities", [])
            
            # Handle case where cities might be an integer (city count) instead of list
            if isinstance(cities_data, int):
                city_count = cities_data
                cities_data = []  # Set to empty list for processing
            elif isinstance(cities_data, list):
                city_count = len(cities_data)
            else:
                logger.warning(f"Unexpected cities data type: {type(cities_data)} = {cities_data}")
                city_count = 0
                cities_data = []
            
            if city_count == 0:
                logger.warning("Nation has 0 cities, skipping warchest calculation")
                return None, None, None

            # Calculate resource requirements based on actual city improvements and military units
            def get_resource_value(resource_data):
                if resource_data is None:
                    return 0
                if isinstance(resource_data, list):
                    return sum(resource_data) if resource_data else 0
                try:
                    return float(resource_data) if resource_data else 0
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert resource_data to float: {type(resource_data)} = {resource_data}")
                    return 0
            
            # Get current resources
            current_money = get_resource_value(nation_info.get("money", 0))
            current_coal = get_resource_value(nation_info.get("coal", 0))
            current_oil = get_resource_value(nation_info.get("oil", 0))
            current_uranium = get_resource_value(nation_info.get("uranium", 0))
            current_iron = get_resource_value(nation_info.get("iron", 0))
            current_bauxite = get_resource_value(nation_info.get("bauxite", 0))
            current_lead = get_resource_value(nation_info.get("lead", 0))
            current_aluminum = get_resource_value(nation_info.get("aluminum", 0))
            current_steel = get_resource_value(nation_info.get("steel", 0))
            current_gasoline = get_resource_value(nation_info.get("gasoline", 0))
            current_munitions = get_resource_value(nation_info.get("munitions", 0))
            current_food = get_resource_value(nation_info.get("food", 0))
            current_credits = get_resource_value(nation_info.get("credits", 0))
            
            # Get military units for consumption calculation
            soldiers = get_resource_value(nation_info.get("soldiers", 0))
            tanks = get_resource_value(nation_info.get("tanks", 0))
            aircraft = get_resource_value(nation_info.get("aircraft", 0))
            ships = get_resource_value(nation_info.get("ships", 0))
            
            # Debug logging
            logger.debug(f"Nation {nation_info.get('id', 'unknown')} cities_data type: {type(cities_data)}")
            if isinstance(cities_data, list) and len(cities_data) > 0:
                logger.debug(f"First city type: {type(cities_data[0])}")
            
            # Ensure cities_data is a list
            if not isinstance(cities_data, list):
                logger.warning(f"cities_data is not a list: {type(cities_data)} = {cities_data}")
                cities_data = []
            
            # Initialize totals
            total_coal_consumption = 0
            total_oil_consumption = 0
            total_uranium_consumption = 0
            total_iron_consumption = 0
            total_bauxite_consumption = 0
            total_lead_consumption = 0
            total_aluminum_consumption = 0
            total_steel_consumption = 0
            total_gasoline_consumption = 0
            total_munitions_consumption = 0
            total_food_consumption = 0
            total_money_consumption = 0
            
            # Calculate consumption for each city
            for city in cities_data:
                try:
                    # Ensure city is a dictionary
                    if not isinstance(city, dict):
                        logger.warning(f"City data is not a dict: {type(city)} = {city}")
                        continue
                        
                    infrastructure = city.get("infrastructure", 0)
                    land = city.get("land", 0)
                    # Calculate population from infrastructure (API doesn't provide population)
                    # Use the same formula as the old warchest
                    base_population = int(infrastructure * 100)
                    
                    # Calculate city age in days
                    from datetime import datetime, timezone
                    import math
                    
                    date_format = "%Y-%m-%d"
                    date1 = datetime.now(timezone.utc)
                    date2 = datetime.strptime(city.get("date", "2025-01-01"), date_format).replace(tzinfo=timezone.utc)
                    age = (date1 - date2).days
                    
                    city_age_modifier = 1 + max(math.log(max(age, 1)) / 15, 0)
                    
                    # EXACT formula from old warchest
                    population = ((base_population ** 2) / 125_000_000) + ((base_population * city_age_modifier - base_population) / 850)
                    
                    # Power plant consumption
                    coal_power = city.get("coalpower", 0)
                    oil_power = city.get("oilpower", 0)
                    nuclear_power = city.get("nuclearpower", 0)
                    
                    # Coal power: 1.2 tons per day per 100 infrastructure
                    total_coal_consumption += coal_power * (infrastructure / 100) * 1.2
                    
                    # Oil power: 1.2 tons per day per 100 infrastructure  
                    total_oil_consumption += oil_power * (infrastructure / 100) * 1.2
                    
                    # Nuclear power: 2.4 tons per day per 1000 infrastructure
                    total_uranium_consumption += nuclear_power * (infrastructure / 1000) * 2.4
                    
                    # Manufacturing consumption
                    steel_mills = city.get("steel_mill", 0)
                    aluminum_refineries = city.get("aluminum_refinery", 0)
                    oil_refineries = city.get("oil_refinery", 0)
                    munitions_factories = city.get("munitions_factory", 0)
                    
                    # Steel mills: 3 tons iron + 3 tons coal = 9 tons steel per day
                    total_iron_consumption += steel_mills * 3
                    total_coal_consumption += steel_mills * 3
                    total_steel_consumption -= steel_mills * 9  # Steel production
                    
                    # Aluminum refineries: 3 tons bauxite = 9 tons aluminum per day
                    total_bauxite_consumption += aluminum_refineries * 3
                    total_aluminum_consumption -= aluminum_refineries * 9  # Aluminum production
                    
                    # Oil refineries: 3 tons oil = 6 tons gasoline per day
                    total_oil_consumption += oil_refineries * 3
                    total_gasoline_consumption -= oil_refineries * 6  # Gasoline production
                    
                    # Munitions factories: 6 tons lead = 18 tons munitions per day
                    total_lead_consumption += munitions_factories * 6
                    total_munitions_consumption -= munitions_factories * 18  # Munitions production
                    
                    # Food consumption based on population
                    # Each person consumes 0.1 food per day
                    total_food_consumption += population * 0.1
                    
                    # Food production from farms
                    farms = city.get("farm", 0)
                    # Farms produce: Land Area / 500 tons per farm per day
                    total_food_consumption -= farms * (land / 500)
                    
                except Exception as e:
                    logger.error(f"Error processing city data: {e}")
                    continue  # Skip this city and continue with the next one
            
            # Military unit consumption (per day)
            # Soldiers: $1.25 per day in peacetime, $1.88 in wartime (use wartime for warchest)
            total_money_consumption += soldiers * 1.88
            
            # Tanks: $75 per day in wartime
            total_money_consumption += tanks * 75
            
            # Aircraft: $750 per day in wartime
            total_money_consumption += aircraft * 750
            
            # Ships: $5,062.5 per day in wartime
            total_money_consumption += ships * 5062.5
            
            # City count-based resource requirements
            city_count = len(cities_data)
            
            # Count cities above C10 (infrastructure > 1000)
            c10_cities = sum(1 for city in cities_data if isinstance(city, dict) and city.get("infrastructure", 0) > 1000)
            
            # Gasoline and Munitions: city_count * 600 (already accounts for days)
            total_gasoline_consumption += city_count * 600
            total_munitions_consumption += city_count * 600
            
            # Steel and Aluminum: 1000 * city_count for cities above C10 (already accounts for days)
            total_steel_consumption += c10_cities * 1000
            total_aluminum_consumption += c10_cities * 500
            
            # Check if nation has C15+ cities (infrastructure >= 1500)
            c15_cities = sum(1 for city in cities_data if isinstance(city, dict) and city.get("infrastructure", 0) >= 1500)
            
            # Calculate warchest requirements
            # Use 7 days for food and uranium if C15+, otherwise 5 days
            warchest_days = 7 if c15_cities > 0 else 5
            food_uranium_days = 7 if c15_cities > 0 else 5
            
            money_required = total_money_consumption * warchest_days
            coal_required = total_coal_consumption * warchest_days
            oil_required = total_oil_consumption * warchest_days
            uranium_required = total_uranium_consumption * food_uranium_days
            iron_required = total_iron_consumption * warchest_days
            bauxite_required = total_bauxite_consumption * warchest_days
            lead_required = total_lead_consumption * warchest_days
            # Gasoline, munitions, steel, aluminum already account for days
            aluminum_required = total_aluminum_consumption
            steel_required = total_steel_consumption
            gasoline_required = total_gasoline_consumption
            munitions_required = total_munitions_consumption
            food_required = total_food_consumption * food_uranium_days
            
            # Calculate production over the warchest period and subtract from requirements
            production = self.calculate_production(nation_info, cities_data, warchest_days)
            
            # Adjust requirements based on production
            money_required = max(money_required - production.get('money', 0), 0)
            coal_required = max(coal_required - production.get('coal', 0), 0)
            oil_required = max(oil_required - production.get('oil', 0), 0)
            uranium_required = max(uranium_required - production.get('uranium', 0), 0)
            iron_required = max(iron_required - production.get('iron', 0), 0)
            bauxite_required = max(bauxite_required - production.get('bauxite', 0), 0)
            lead_required = max(lead_required - production.get('lead', 0), 0)
            aluminum_required = max(aluminum_required - production.get('aluminum', 0), 0)
            steel_required = max(steel_required - production.get('steel', 0), 0)
            gasoline_required = max(gasoline_required - production.get('gasoline', 0), 0)
            munitions_required = max(munitions_required - production.get('munitions', 0), 0)
            food_required = max(food_required - production.get('food', 0), 0)
            
            # Credits requirement (1 credit per 1000 population per day)
            try:
                total_population = sum(city.get("population", 0) for city in cities_data)
            except TypeError as e:
                logger.warning(f"Error calculating total population: {e}")
                total_population = 0
            credits_required = (total_population / 1000) * warchest_days
            
            # Calculate deficits
            money_deficit = max(money_required - current_money, 0)
            coal_deficit = max(coal_required - current_coal, 0)
            oil_deficit = max(oil_required - current_oil, 0)
            uranium_deficit = max(uranium_required - current_uranium, 0)
            iron_deficit = max(iron_required - current_iron, 0)
            bauxite_deficit = max(bauxite_required - current_bauxite, 0)
            lead_deficit = max(lead_required - current_lead, 0)
            aluminum_deficit = max(aluminum_required - current_aluminum, 0)
            steel_deficit = max(steel_required - current_steel, 0)
            gasoline_deficit = max(gasoline_required - current_gasoline, 0)
            munitions_deficit = max(munitions_required - current_munitions, 0)
            food_deficit = max(food_required - current_food, 0)
            credits_deficit = max(credits_required - current_credits, 0)
            
            # Calculate excess
            money_excess = max(current_money - money_required, 0)
            coal_excess = max(current_coal - coal_required, 0)
            oil_excess = max(current_oil - oil_required, 0)
            uranium_excess = max(current_uranium - uranium_required, 0)
            iron_excess = max(current_iron - iron_required, 0)
            bauxite_excess = max(current_bauxite - bauxite_required, 0)
            lead_excess = max(current_lead - lead_required, 0)
            aluminum_excess = max(current_aluminum - aluminum_required, 0)
            steel_excess = max(current_steel - steel_required, 0)
            gasoline_excess = max(current_gasoline - gasoline_required, 0)
            munitions_excess = max(current_munitions - munitions_required, 0)
            food_excess = max(current_food - food_required, 0)
            credits_excess = max(current_credits - credits_required, 0)

            # Return results with ALL resources
            result = {
                "money_deficit": money_deficit,
                "coal_deficit": coal_deficit,
                "oil_deficit": oil_deficit,
                "uranium_deficit": uranium_deficit,
                "iron_deficit": iron_deficit,
                "bauxite_deficit": bauxite_deficit,
                "lead_deficit": lead_deficit,
                "gasoline_deficit": gasoline_deficit,
                "munitions_deficit": munitions_deficit,
                "steel_deficit": steel_deficit,
                "aluminum_deficit": aluminum_deficit,
                "food_deficit": food_deficit,
                "credits_deficit": credits_deficit
            }

            excess = {
                "money": money_excess,
                "coal": coal_excess,
                "oil": oil_excess,
                "uranium": uranium_excess,
                "iron": iron_excess,
                "bauxite": bauxite_excess,
                "lead": lead_excess,
                "gasoline": gasoline_excess,
                "munitions": munitions_excess,
                "steel": steel_excess,
                "aluminum": aluminum_excess,
                "food": food_excess,
                "credits": credits_excess
            }

            supply = {
                "money": money_required,
                "coal": coal_required,
                "oil": oil_required,
                "uranium": uranium_required,
                "iron": iron_required,
                "bauxite": bauxite_required,
                "lead": lead_required,
                "gasoline": gasoline_required,
                "munitions": munitions_required,
                "steel": steel_required,
                "aluminum": aluminum_required,
                "food": food_required,
                "credits": credits_required
            }

            return result, excess, supply

        except Exception as e:
            logger.error(f"Error in warchest calculation: {e}")
            return None, None, None
    
    def calculate_warchest_old_format(self, member: Dict[str, Any]) -> Optional[Dict]:
        """Calculate warchest using the old format for audit compatibility."""
        try:
            # Get city count
            city_count = len(member.get("cities", []))
            
            if city_count == 0:
                logger.warning("Nation has 0 cities, skipping warchest calculation")
                return None

            # Simple city-based warchest formula
            # Total warchest needed (in bank):
            aluminum_bank = city_count * 1000
            steel_bank = city_count * 2000
            gasoline_bank = city_count * 1500
            munitions_bank = city_count * 1500
            
            # Amount you should have on nation:
            aluminum_nation = city_count * 500
            steel_nation = city_count * 1000
            gasoline_nation = city_count * 600
            munitions_nation = city_count * 600

            # Get current resources
            current_aluminum = member.get("aluminum", 0)
            current_steel = member.get("steel", 0)
            current_gasoline = member.get("gasoline", 0)
            current_munitions = member.get("munitions", 0)

            # Calculate deficits (what you need to get to required amounts)
            aluminum_deficit = max(aluminum_nation - current_aluminum, 0)
            steel_deficit = max(steel_nation - current_steel, 0)
            gasoline_deficit = max(gasoline_nation - current_gasoline, 0)
            munitions_deficit = max(munitions_nation - current_munitions, 0)

            # Return results in old format
            result = {
                "money_deficit": 0,
                "coal_deficit": 0,
                "oil_deficit": 0,
                "uranium_deficit": 0,
                "iron_deficit": 0,
                "bauxite_deficit": 0,
                "lead_deficit": 0,
                "gasoline_deficit": gasoline_deficit,
                "munitions_deficit": munitions_deficit,
                "steel_deficit": steel_deficit,
                "aluminum_deficit": aluminum_deficit,
                "food_deficit": 0,
                "credits_deficit": 0,
                # Supply amounts for threshold calculations
                "money_supply": 0,
                "coal_supply": 0,
                "oil_supply": 0,
                "uranium_supply": 0,
                "iron_supply": 0,
                "bauxite_supply": 0,
                "lead_supply": 0,
                "gasoline_supply": gasoline_nation,
                "munitions_supply": munitions_nation,
                "steel_supply": steel_nation,
                "aluminum_supply": aluminum_nation,
                "food_supply": 0,
                "credits_supply": 0
            }

            return result

        except Exception as e:
            logger.error(f"Error in old format warchest calculation: {e}")
            return None
    
    def calculate_production(self, nation_info: dict, cities_data: list, days: int) -> dict:
        """Calculate resource production over the specified number of days."""
        production = {
            'money': 0,
            'coal': 0,
            'oil': 0,
            'uranium': 0,
            'iron': 0,
            'bauxite': 0,
            'lead': 0,
            'gasoline': 0,
            'munitions': 0,
            'steel': 0,
            'aluminum': 0,
            'food': 0
        }
        
        try:
            # Calculate daily production from cities
            for city in cities_data:
                if not isinstance(city, dict):
                    continue
                    
                # Money production (from population and improvements)
                population = city.get('population', 0)
                money_daily = population * 0.01  # $0.01 per population per day
                production['money'] += money_daily * days
                
                # Resource production from improvements
                # Coal mines
                coal_mines = city.get('coal_mine', 0)
                production['coal'] += coal_mines * 2.5 * days  # 2.5 coal per mine per day
                
                # Oil wells
                oil_wells = city.get('oil_well', 0)
                production['oil'] += oil_wells * 2.5 * days  # 2.5 oil per well per day
                
                # Uranium mines
                uranium_mines = city.get('uranium_mine', 0)
                production['uranium'] += uranium_mines * 0.5 * days  # 0.5 uranium per mine per day
                
                # Iron mines
                iron_mines = city.get('iron_mine', 0)
                production['iron'] += iron_mines * 2.5 * days  # 2.5 iron per mine per day
                
                # Bauxite mines
                bauxite_mines = city.get('bauxite_mine', 0)
                production['bauxite'] += bauxite_mines * 2.5 * days  # 2.5 bauxite per mine per day
                
                # Lead mines
                lead_mines = city.get('lead_mine', 0)
                production['lead'] += lead_mines * 2.5 * days  # 2.5 lead per mine per day
                
                # Farms (food production)
                farms = city.get('farm', 0)
                production['food'] += farms * 2.5 * days  # 2.5 food per farm per day
                
                # Manufacturing improvements
                # Munitions factories
                munitions_factories = city.get('munitions_factory', 0)
                production['munitions'] += munitions_factories * 2.5 * days  # 2.5 munitions per factory per day
                
                # Steel mills
                steel_mills = city.get('steel_mill', 0)
                production['steel'] += steel_mills * 2.5 * days  # 2.5 steel per mill per day
                
                # Aluminum refineries
                aluminum_refineries = city.get('aluminum_refinery', 0)
                production['aluminum'] += aluminum_refineries * 2.5 * days  # 2.5 aluminum per refinery per day
                
                # Oil refineries (gasoline production)
                oil_refineries = city.get('oil_refinery', 0)
                production['gasoline'] += oil_refineries * 2.5 * days  # 2.5 gasoline per refinery per day
                
        except Exception as e:
            logger.error(f"Error calculating production: {e}")
            
        return production