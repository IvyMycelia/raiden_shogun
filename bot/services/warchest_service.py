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
            # Get city count
            city_count = nation_info.get("cities", 0)
            
            if city_count == 0:
                logger.warning("Nation has 0 cities, skipping warchest calculation")
                return None, None, None

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
            current_aluminum = nation_info.get("aluminum", 0)
            current_steel = nation_info.get("steel", 0)
            current_gasoline = nation_info.get("gasoline", 0)
            current_munitions = nation_info.get("munitions", 0)

            # Calculate deficits (what you need to get to required amounts)
            aluminum_deficit = max(aluminum_nation - current_aluminum, 0)
            steel_deficit = max(steel_nation - current_steel, 0)
            gasoline_deficit = max(gasoline_nation - current_gasoline, 0)
            munitions_deficit = max(munitions_nation - current_munitions, 0)

            # Calculate excess (what you have above required amounts)
            aluminum_excess = max(current_aluminum - aluminum_nation, 0)
            steel_excess = max(current_steel - steel_nation, 0)
            gasoline_excess = max(current_gasoline - gasoline_nation, 0)
            munitions_excess = max(current_munitions - munitions_nation, 0)

            # Return results (keeping same format for compatibility)
            result = {
                "money_deficit": 0,  # Not used in simple formula
                "coal_deficit": 0,   # Not used in simple formula
                "oil_deficit": 0,    # Not used in simple formula
                "uranium_deficit": 0, # Not used in simple formula
                "iron_deficit": 0,   # Not used in simple formula
                "bauxite_deficit": 0, # Not used in simple formula
                "lead_deficit": 0,   # Not used in simple formula
                "gasoline_deficit": gasoline_deficit,
                "munitions_deficit": munitions_deficit,
                "steel_deficit": steel_deficit,
                "aluminum_deficit": aluminum_deficit,
                "food_deficit": 0,   # Not used in simple formula
                "credits_deficit": 0  # Not used in simple formula
            }

            excess = {
                "money": 0,          # Not used in simple formula
                "coal": 0,           # Not used in simple formula
                "oil": 0,            # Not used in simple formula
                "uranium": 0,        # Not used in simple formula
                "iron": 0,           # Not used in simple formula
                "bauxite": 0,        # Not used in simple formula
                "lead": 0,           # Not used in simple formula
                "gasoline": gasoline_excess,
                "munitions": munitions_excess,
                "steel": steel_excess,
                "aluminum": aluminum_excess,
                "food": 0,           # Not used in simple formula
                "credits": 0         # Not used in simple formula
            }

            supply = {
                "money": 0,          # Not used in simple formula
                "coal": 0,           # Not used in simple formula
                "oil": 0,            # Not used in simple formula
                "uranium": 0,        # Not used in simple formula
                "iron": 0,           # Not used in simple formula
                "bauxite": 0,        # Not used in simple formula
                "lead": 0,           # Not used in simple formula
                "gasoline": gasoline_nation,
                "munitions": munitions_nation,
                "steel": steel_nation,
                "aluminum": aluminum_nation,
                "food": 0,           # Not used in simple formula
                "credits": 0         # Not used in simple formula
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