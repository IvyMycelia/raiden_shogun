"""
Raid service for business logic.
"""

from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.constants import GameConstants

class RaidService:
    """Service for raid-related business logic."""
    
    def __init__(self):
        pass
    
    def find_raid_targets(self, nations: List[Dict], user_score: float, 
                         max_targets: int = 20, exclude_alliances: List[str] = None) -> List[Dict]:
        """Find raid targets from nation list."""
        min_score = user_score * (1 - GameConstants.WAR_RANGE_MULTIPLIER)
        max_score = user_score * (1 + GameConstants.WAR_RANGE_MULTIPLIER)
        
        valid_targets = []
        filtered_out = {
            'score_range': 0,
            'vmode': 0,
            'beige_turns': 0,
            'top_alliance': 0,
            'defensive_wars': 0,
            'no_cities': 0,
            'low_loot': 0
        }
        
        for nation in nations:
            # Stage 1: Score range filter
            score = float(nation.get('score', 0))
            if not (min_score <= score <= max_score):
                filtered_out['score_range'] += 1
                continue
            
            # Stage 2: Vacation mode filter
            if nation.get('vmode', 0) == 1:
                filtered_out['vmode'] += 1
                continue
            
            # Stage 3: Beige turns filter
            if nation.get('beige_turns', 0) > 0:
                filtered_out['beige_turns'] += 1
                continue
            
            # Stage 4: Alliance filter
            alliance_id = nation.get('alliance_id', 0)
            if alliance_id == 13033 or (exclude_alliances and alliance_id in exclude_alliances):
                filtered_out['top_alliance'] += 1
                continue
            
            # Stage 5: Defensive wars filter
            if nation.get('defensive_wars', 0) >= GameConstants.MAX_DEFENSIVE_WARS:
                filtered_out['defensive_wars'] += 1
                continue
            
            # Stage 6: Cities existence filter
            if nation.get('cities', 0) == 0:
                filtered_out['no_cities'] += 1
                continue
            
            # Stage 7: Loot potential filter
            loot_potential = self.calculate_loot_potential(nation)
            if loot_potential < GameConstants.MIN_LOOT_POTENTIAL:
                filtered_out['low_loot'] += 1
                continue
            
            # Stage 8: Final validation
            valid_targets.append({
                'nation_id': nation.get('id'),
                'nation_name': nation.get('nation_name', 'Unknown'),
                'leader_name': nation.get('leader_name', 'Unknown'),
                'score': score,
                'cities': nation.get('cities', 0),
                'alliance': nation.get('alliance', 'None'),
                'alliance_id': alliance_id,
                'loot_potential': loot_potential,
                'soldiers': nation.get('soldiers', 0),
                'tanks': nation.get('tanks', 0),
                'aircraft': nation.get('aircraft', 0),
                'ships': nation.get('ships', 0),
                'spies': nation.get('spies', 0)
            })
            
            if len(valid_targets) >= max_targets:
                break
        
        # Sort by loot potential (highest first)
        valid_targets.sort(key=lambda x: x['loot_potential'], reverse=True)
        
        return {
            'targets': valid_targets,
            'filtered_out': filtered_out,
            'total_checked': len(nations)
        }
    
    def calculate_loot_potential(self, nation: Dict) -> float:
        """Calculate loot potential for a nation."""
        base_loot = 0.0
        
        # GDP-based loot (10% of GDP)
        gdp = float(nation.get('gdp', 0))
        base_loot += gdp * GameConstants.GDP_LOOT_MULTIPLIER
        
        # Military value-based loot (10% of military value)
        soldiers = int(nation.get('soldiers', 0))
        tanks = int(nation.get('tanks', 0))
        aircraft = int(nation.get('aircraft', 0))
        ships = int(nation.get('ships', 0))
        
        military_value = (
            soldiers * GameConstants.MILITARY_UNIT_VALUES["soldiers"] +
            tanks * GameConstants.MILITARY_UNIT_VALUES["tanks"] +
            aircraft * GameConstants.MILITARY_UNIT_VALUES["aircraft"] +
            ships * GameConstants.MILITARY_UNIT_VALUES["ships"]
        )
        base_loot += military_value * GameConstants.MILITARY_LOOT_MULTIPLIER
        
        # City-based loot (5% of estimated city value)
        cities_count = int(nation.get('cities', 0))
        if cities_count > 0:
            city_loot = cities_count * GameConstants.CITY_VALUE_ESTIMATE
            base_loot += city_loot * GameConstants.CITY_LOOT_MULTIPLIER
        
        return base_loot
    
    def find_purge_targets(self, nations: List[Dict]) -> List[Dict]:
        """Find purge targets (purple nations with <15 cities, not in alliance 13033)."""
        targets = []
        
        for nation in nations:
            # Check if purple color
            if nation.get('color', '').lower() != 'purple':
                continue
            
            # Check city count < 15
            if nation.get('cities', 0) >= 15:
                continue
            
            # Check not in alliance 13033
            if nation.get('alliance_id', 0) == 13033:
                continue
            
            targets.append({
                'nation_id': nation.get('id'),
                'nation_name': nation.get('nation_name', 'Unknown'),
                'leader_name': nation.get('leader_name', 'Unknown'),
                'score': float(nation.get('score', 0)),
                'cities': nation.get('cities', 0),
                'alliance': nation.get('alliance', 'None'),
                'alliance_id': nation.get('alliance_id', 0)
            })
        
        # Sort by score (highest first)
        targets.sort(key=lambda x: x['score'], reverse=True)
        return targets
    
    def find_counter_targets(self, target_nation: Dict, alliance_members: List[Dict]) -> List[Dict]:
        """Find alliance members within war range of target nation."""
        target_score = float(target_nation.get('score', 0))
        min_score = target_score * 0.75
        max_score = target_score * 1.25
        
        counters = []
        
        for member in alliance_members:
            if member.get("alliance_position", "") != "APPLICANT":
                member_score = float(member.get('score', 0))
                
                if min_score <= member_score <= max_score:
                    counters.append({
                        'nation_id': member.get('id'),
                        'nation_name': member.get('nation_name', 'Unknown'),
                        'leader_name': member.get('leader_name', 'Unknown'),
                        'score': member_score,
                        'cities': member.get('cities', 0),
                        'soldiers': member.get('soldiers', 0),
                        'tanks': member.get('tanks', 0),
                        'aircraft': member.get('aircraft', 0),
                        'ships': member.get('ships', 0)
                    })
        
        # Sort by score (closest to target first)
        counters.sort(key=lambda x: abs(x['score'] - target_score))
        return counters
