import asyncio
import discord
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

from bot.handler import info, error, warning
from bot.csv_cache import get_cache
# Removed calculate import - we implement our own loot calculation

class CSVRaidSystem:
    """Enhanced raid system using CSV data for fast, reliable target finding."""
    
    def __init__(self, config):
        self.config = config
        self.csv_cache = get_cache()
    
    async def find_raid_targets(self, interaction, min_score: float, max_score: float, 
                              max_targets: int = 20, exclude_alliances: List[str] = None) -> List[Dict[str, Any]]:
        """Find raid targets using CSV data."""
        try:
            info(f"Starting CSV-based raid search for score range {min_score:.0f}-{max_score:.0f}", tag="CSV_RAID")
            
            # Load CSV cache if not already loaded
            if not self.csv_cache.data.get('nations'):
                self.csv_cache.load_cache()
            
            # Get nations data from CSV cache
            nations_data = self.csv_cache.get_nations()
            if not nations_data:
                warning("No nations data available", tag="CSV_RAID")
                return []
            
            # Filter nations in score range
            nations_in_range = []
            for nation in nations_data:
                try:
                    score = float(nation.get('score', 0))
                    if min_score <= score <= max_score:
                        nations_in_range.append(nation)
                except (ValueError, TypeError):
                    continue
            info(f"Found {len(nations_in_range)} nations in score range", tag="CSV_RAID")
            
            if not nations_in_range:
                return []
            
            # Filter out invalid targets
            valid_targets = []
            excluded_count = 0
            
            for nation in nations_in_range:
                # Check vmode (vm_turns > 0 means in vacation mode)
                vm_turns = int(nation.get('vm_turns', 0))
                if vm_turns > 0:
                    excluded_count += 1
                    continue
                
                # Check beige turns
                beige_turns = int(nation.get('beige_turns_remaining', 0))
                if beige_turns > 0:
                    excluded_count += 1
                    continue
                
                # Check if nation has cities (cities = 0 means inactive)
                cities = int(nation.get('cities', 0))
                if cities == 0:
                    excluded_count += 1
                    continue
                
                # Check defensive wars (exclude if 3 or more)
                defensive_wars = int(nation.get('defensive_wars', 0))
                if defensive_wars >= 3:
                    excluded_count += 1
                    continue
                
                # Check alliance rank (exclude if alliance rank 60 or above)
                alliance_id = nation.get('alliance_id', '0')
                if alliance_id != '0':
                    # Get alliance data to check rank
                    alliance_data = self.csv_cache.get_alliance_by_id(alliance_id)
                    if alliance_data:
                        alliance_rank = int(alliance_data.get('rank', 999))
                        if alliance_rank <= 60:  # Rank 60 or above (lower number = higher rank)
                            excluded_count += 1
                            continue
                
                # Check alliance exclusion
                if exclude_alliances:
                    alliance_id = nation.get('alliance_id', '0')
                    alliance_name = nation.get('alliance', 'None')
                    if alliance_id in exclude_alliances or alliance_name in exclude_alliances:
                        excluded_count += 1
                        continue
                
                # Get additional data for this nation
                nation_id = nation.get('﻿nation_id') or nation.get('nation_id')
                if not nation_id:
                    continue
                
                # Get recent wars for loot calculation (simplified)
                wars = []  # CSV cache doesn't have wars data, so we'll skip this for now
                
                # Calculate loot potential (simplified without cities data)
                loot_potential = self._calculate_loot_potential(nation, wars)
                
                # Add to valid targets
                valid_targets.append({
                    'nation_id': nation_id,
                    'nation_name': nation.get('nation_name', 'Unknown'),
                    'leader_name': nation.get('leader_name', 'Unknown'),
                    'score': float(nation.get('score', 0)),
                    'cities': int(nation.get('cities', 0)),
                    'alliance': nation.get('alliance', 'None'),
                    'alliance_id': nation.get('alliance_id', '0'),
                    'loot_potential': loot_potential,
                    'recent_wars': wars,
                    'soldiers': int(nation.get('soldiers', 0)),
                    'tanks': int(nation.get('tanks', 0)),
                    'aircraft': int(nation.get('aircraft', 0)),
                    'ships': int(nation.get('ships', 0)),
                    'spies': int(nation.get('spies', 0))
                })
            
            info(f"Excluded {excluded_count} nations (vmode/beige/defensive wars/alliance)", tag="CSV_RAID")
            info(f"Found {len(valid_targets)} valid targets", tag="CSV_RAID")
            
            # Sort by loot potential (highest first)
            valid_targets.sort(key=lambda x: x['loot_potential'], reverse=True)
            
            # Return top targets
            return valid_targets[:max_targets]
            
        except Exception as e:
            error(f"Error in CSV raid search: {e}", tag="CSV_RAID")
            return []
    
    def _calculate_loot_potential(self, nation: Dict[str, Any], wars: List[Dict[str, Any]]) -> float:
        """Calculate loot potential based on nation data, cities, and war history."""
        try:
            # Base loot from nation income and resources
            base_loot = 0.0
            
            # Calculate income-based loot (using GDP as proxy for money)
            gdp = float(nation.get('gdp', 0))
            base_loot += gdp * 0.1  # 10% of GDP
            
            # Calculate military-based loot potential
            soldiers = int(nation.get('soldiers', 0))
            tanks = int(nation.get('tanks', 0))
            aircraft = int(nation.get('aircraft', 0))
            ships = int(nation.get('ships', 0))
            
            # Military unit values (approximate)
            military_value = (soldiers * 1.25) + (tanks * 50) + (aircraft * 500) + (ships * 3375)
            base_loot += military_value * 0.1  # 10% of military value
            
            # Calculate city-based loot potential (simplified)
            cities_count = int(nation.get('cities', 0))
            if cities_count > 0:
                # Estimate city value based on nation data
                city_loot = cities_count * 50000  # $50k per city estimate
                base_loot += city_loot * 0.05  # 5% of estimated city value
            
            # Factor in recent war performance
            war_modifier = 1.0
            if wars:
                # Calculate average loot from recent wars
                total_loot = 0
                war_count = 0
                
                for war in wars:
                    # Check if this nation was the aggressor (won loot)
                    aggressor_id = war.get('aggressor_nation_id') or war.get('﻿aggressor_nation_id')
                    if aggressor_id == nation.get('nation_id') or aggressor_id == nation.get('﻿nation_id'):
                        # This nation was the aggressor, check if they won
                        war_status = war.get('war_status', '')
                        if war_status == 'Defeat':
                            # They lost, might be easier target
                            war_modifier *= 1.2
                        elif war_status == 'Victory':
                            # They won, might be harder target
                            war_modifier *= 0.8
                
                # If no recent wars, they might be inactive (easier target)
                if not wars:
                    war_modifier *= 1.3
            
            # Apply war modifier
            final_loot = base_loot * war_modifier
            
            return max(0, final_loot)
            
        except Exception as e:
            error(f"Error calculating loot potential: {e}", tag="CSV_RAID")
            return 0.0
    
    def format_raid_results(self, targets: List[Dict[str, Any]], 
                          min_score: float, max_score: float) -> tuple[discord.Embed, discord.ui.View]:
        """Format raid results into a Discord embed with pagination."""
        from bot.raid_paginator import RaidPaginator
        
        paginator = RaidPaginator(targets, min_score, max_score)
        embed = paginator.create_embed(0)
        view = paginator.get_view()
        
        return embed, view

# Global instance
_raid_system = None

def get_raid_system(config) -> CSVRaidSystem:
    """Get the global CSV raid system instance."""
    global _raid_system
    if _raid_system is None:
        _raid_system = CSVRaidSystem(config)
    return _raid_system
