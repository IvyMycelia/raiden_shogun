import logging
import asyncio
import time
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger('raiden_shogun')

class RaidCalculationService:
    """Service for calculating loot potential and filtering raid targets."""
    
    def __init__(self):
        # Simple in-memory cache for city improvements data
        self._city_cache = {}
        self._cache_timestamp = 0
        self._cache_duration = 3600  # 1 hour cache duration
        
        # Cache for market prices
        self._market_prices = {}
        self._prices_timestamp = 0
        self._prices_duration = 3600  # 1 hour cache duration
    
    async def calculate_loot_potential(self, nation_data: Dict, cities_data: List[Dict], wars_data: List[Dict]) -> float:
        """Calculate total loot potential for a nation based on city improvements and infrastructure."""
        total_loot = 0.0
        
        # 1. Infrastructure value (major factor from cities)
        total_infrastructure = sum(city.get('infrastructure', 0) for city in cities_data)
        infrastructure_value = total_infrastructure * 100  # Base infrastructure value
        total_loot += infrastructure_value
        
        # 2. City improvements value (based on actual improvements)
        improvements_value = self.calculate_improvements_value(cities_data)
        total_loot += improvements_value
        
        # 3. Commerce-based income potential
        commerce_value = self.calculate_commerce_value(cities_data)
        total_loot += commerce_value
        
        # 4. Military value (indicates nation strength and development)
        military_value = (
            nation_data.get('soldiers', 0) * 1.25 +     # $1.25 per soldier
            nation_data.get('tanks', 0) * 50 +          # $50 per tank
            nation_data.get('aircraft', 0) * 500 +      # $500 per aircraft
            nation_data.get('ships', 0) * 3375 +        # $3,375 per ship
            nation_data.get('missiles', 0) * 10000 +    # $10k per missile
            nation_data.get('nukes', 0) * 100000        # $100k per nuke
        )
        total_loot += military_value
        
        # 5. City count bonus (more cities = more value)
        city_count = len(cities_data)
        if city_count > 0:
            city_bonus = city_count * 50000  # $50k per city
            total_loot += city_bonus
        
        # 6. Score-based bonus (indicates development level)
        score = float(nation_data.get('score', 0))
        if score > 0:
            score_bonus = score * 1000  # $1k per score point
            total_loot += score_bonus
        
        # 7. Resource production value (daily production * market prices)
        production_value = await self.calculate_production_value(cities_data)
        total_loot += production_value
        
        return total_loot

    async def get_market_prices(self) -> Dict[str, float]:
        """Get current market prices for resources."""
        current_time = time.time()
        
        # Check cache first
        if current_time - self._prices_timestamp < self._prices_duration and self._market_prices:
            return self._market_prices
        
        try:
            from api.politics_war_api import api
            prices_data = await api.get_tradeprices()
            
            if prices_data and len(prices_data) > 0:
                # Get the most recent prices
                latest_prices = prices_data[0]
                self._market_prices = {
                    'coal': latest_prices.get('coal', 50.0),
                    'oil': latest_prices.get('oil', 100.0),
                    'uranium': latest_prices.get('uranium', 2000.0),
                    'iron': latest_prices.get('iron', 75.0),
                    'bauxite': latest_prices.get('bauxite', 80.0),
                    'lead': latest_prices.get('lead', 90.0),
                    'gasoline': latest_prices.get('gasoline', 150.0),
                    'munitions': latest_prices.get('munitions', 200.0),
                    'steel': latest_prices.get('steel', 300.0),
                    'aluminum': latest_prices.get('aluminum', 400.0),
                    'food': latest_prices.get('food', 25.0),
                    'credits': latest_prices.get('credits', 1000.0)
                }
                self._prices_timestamp = current_time
                logger.info(f"🌐 Updated market prices: {self._market_prices}")
            else:
                logger.warning("🌐 No market prices data available, using defaults")
                # Use default prices if API fails
                self._market_prices = {
                    'coal': 50.0, 'oil': 100.0, 'uranium': 2000.0, 'iron': 75.0,
                    'bauxite': 80.0, 'lead': 90.0, 'gasoline': 150.0, 'munitions': 200.0,
                    'steel': 300.0, 'aluminum': 400.0, 'food': 25.0, 'credits': 1000.0
                }
        except Exception as e:
            logger.error(f"🌐 Error fetching market prices: {e}")
            # Use default prices on error
            self._market_prices = {
                'coal': 50.0, 'oil': 100.0, 'uranium': 2000.0, 'iron': 75.0,
                'bauxite': 80.0, 'lead': 90.0, 'gasoline': 150.0, 'munitions': 200.0,
                'steel': 300.0, 'aluminum': 400.0, 'food': 25.0, 'credits': 1000.0
            }
        
        return self._market_prices

    def calculate_gdp(self, nation_data: Dict, cities_data: List[Dict]) -> float:
        """Calculate nation GDP based on cities."""
        total_gdp = 0.0
        
        for city in cities_data:
            # GDP = Infrastructure * 100 * (1 + Commerce/100)
            infrastructure = city.get('infrastructure', 0)
            commerce = self.calculate_city_commerce(city)
            city_gdp = infrastructure * 100 * (1 + commerce / 100)
            total_gdp += city_gdp
        
        return total_gdp

    def calculate_city_commerce(self, city: Dict) -> float:
        """Calculate city commerce rate based on improvements."""
        # Simplified commerce calculation
        infrastructure = city.get('infrastructure', 0)
        return min(infrastructure / 100, 100)  # Cap at 100%

    def calculate_military_value(self, nation_data: Dict) -> float:
        """Calculate total military value."""
        soldiers = nation_data.get('soldiers', 0)
        tanks = nation_data.get('tanks', 0)
        aircraft = nation_data.get('aircraft', 0)
        ships = nation_data.get('ships', 0)
        
        # Military unit values (based on PnW costs)
        return (
            soldiers * 1.25 +      # $1.25 per soldier
            tanks * 50 +           # $50 per tank
            aircraft * 500 +       # $500 per aircraft
            ships * 3375           # $3,375 per ship
        )

    def calculate_city_value(self, cities_data: List[Dict]) -> float:
        """Calculate total city value."""
        total_value = 0.0
        
        for city in cities_data:
            infrastructure = city.get('infrastructure', 0)
            land = city.get('land', 0)
            
            # City value = Infrastructure cost + Land cost
            infra_cost = self.calculate_infrastructure_cost(infrastructure)
            land_cost = self.calculate_land_cost(land)
            total_value += infra_cost + land_cost
        
        return total_value

    def calculate_infrastructure_cost(self, infrastructure: float) -> float:
        """Calculate infrastructure cost using PnW formula."""
        if infrastructure <= 10:
            return infrastructure * 1000
        else:
            return ((infrastructure - 10) ** 2.2) / 710 + 300

    def calculate_land_cost(self, land: float) -> float:
        """Calculate land cost using PnW formula."""
        if land <= 20:
            return land * 100
        else:
            return 0.002 * (land - 20) ** 2 + 50

    def calculate_color_bonus(self, nation_data: Dict) -> float:
        """Calculate color bloc bonus based on nation's color."""
        color = nation_data.get('color', '').lower()
        
        # Color bloc turn bonuses (affects income)
        color_bonuses = {
            'red': 1.15,      # 15% bonus
            'blue': 1.10,     # 10% bonus
            'green': 1.05,    # 5% bonus
            'yellow': 1.20,   # 20% bonus
            'purple': 1.25,   # 25% bonus
            'orange': 1.10,   # 10% bonus
            'pink': 1.15,     # 15% bonus
            'black': 1.30,    # 30% bonus
            'white': 1.00,    # No bonus
            'beige': 0.50,    # Penalty (inactive)
            'gray': 0.80      # Penalty (no color)
        }
        
        return color_bonuses.get(color, 1.0)

    def calculate_city_infrastructure_value(self, cities_data: List[Dict]) -> float:
        """Calculate city infrastructure value based on public data."""
        total_value = 0.0
        
        for city in cities_data:
            infrastructure = city.get('infrastructure', 0)
            land = city.get('land', 0)
            
            # Infrastructure value (public data)
            infra_value = infrastructure * 100  # Base infrastructure value
            
            # Land value (public data)
            land_value = land * 50  # Approximate land value
            
            # City age bonus (older cities = more developed)
            age = city.get('age', 0)
            age_bonus = 1 + (age / 1000)  # 1% bonus per 1000 days
            
            city_value = (infra_value + land_value) * age_bonus
            total_value += city_value
        
        return total_value

    def calculate_war_loot_modifier(self, nation_data: Dict, wars_data: List[Dict]) -> float:
        """Calculate loot modifier based on historical war performance."""
        nation_id = nation_data.get('id')
        if not nation_id or not wars_data:
            return 1.0
        
        # Find wars involving this nation
        nation_wars = []
        for war in wars_data:
            if (war.get('aggressor_nation_id') == nation_id or 
                war.get('defender_nation_id') == nation_id):
                nation_wars.append(war)
        
        if not nation_wars:
            return 1.0
        
        # Calculate average loot from wars where they were defeated
        total_loot = 0
        looted_wars = 0
        
        for war in nation_wars:
            loot = war.get('loot', 0)
            if loot and loot > 0:
                total_loot += loot
                looted_wars += 1
        
        if looted_wars == 0:
            return 1.0
        
        avg_loot = total_loot / looted_wars
        
        # Categorize based on average loot (more conservative estimates)
        if avg_loot < 1000000:  # Under 1M = bad target
            return 0.3
        elif avg_loot < 3000000:  # 1M-3M = poor target
            return 0.6
        elif avg_loot < 7000000:  # 3M-7M = decent target
            return 1.0
        elif avg_loot < 15000000:  # 7M-15M = good target
            return 1.4
        else:  # 15M+ = excellent target
            return 1.8

    async def calculate_production_value(self, cities_data: List[Dict]) -> float:
        """Calculate production value based on city improvements using real-time market prices."""
        total_value = 0.0
        
        # Get current market prices
        prices = await self.get_market_prices()
        
        for city in cities_data:
            # Coal mines: 3 tons/day = 0.25/turn
            coal_mines = city.get('coal_mine', 0)
            coal_production = coal_mines * 0.25 * 30  # 30 turns = 1 day
            total_value += coal_production * prices['coal']
            
            # Iron mines: 3 tons/day = 0.25/turn
            iron_mines = city.get('iron_mine', 0)
            iron_production = iron_mines * 0.25 * 30
            total_value += iron_production * prices['iron']
            
            # Uranium mines: 3 tons/day = 0.25/turn
            uranium_mines = city.get('uranium_mine', 0)
            uranium_production = uranium_mines * 0.25 * 30
            total_value += uranium_production * prices['uranium']
            
            # Oil wells: 3 tons/day = 0.25/turn
            oil_wells = city.get('oil_well', 0)
            oil_production = oil_wells * 0.25 * 30
            total_value += oil_production * prices['oil']
            
            # Bauxite mines: 3 tons/day = 0.25/turn
            bauxite_mines = city.get('bauxite_mine', 0)
            bauxite_production = bauxite_mines * 0.25 * 30
            total_value += bauxite_production * prices['bauxite']
            
            # Lead mines: 3 tons/day = 0.25/turn
            lead_mines = city.get('lead_mine', 0)
            lead_production = lead_mines * 0.25 * 30
            total_value += lead_production * prices['lead']
            
            # Farms: Land/500 tons per turn
            farms = city.get('farm', 0)
            land = city.get('land', 0)
            food_production = farms * (land / 500) * 30
            total_value += food_production * prices['food']
            
            # Manufacturing improvements
            # Oil refineries: 0.5/turn (3 oil -> 6 gasoline)
            oil_refineries = city.get('oil_refinery', 0)
            gasoline_production = oil_refineries * 0.5 * 30
            total_value += gasoline_production * prices['gasoline']
            
            # Steel mills: 0.75/turn (3 iron + 3 coal -> 9 steel)
            steel_mills = city.get('steel_mill', 0)
            steel_production = steel_mills * 0.75 * 30
            total_value += steel_production * prices['steel']
            
            # Aluminum refineries: 0.75/turn (3 bauxite -> 9 aluminum)
            aluminum_refineries = city.get('aluminum_refinery', 0)
            aluminum_production = aluminum_refineries * 0.75 * 30
            total_value += aluminum_production * prices['aluminum']
            
            # Munitions factories: 1.5/turn (6 lead -> 18 munitions)
            munitions_factories = city.get('munitions_factory', 0)
            munitions_production = munitions_factories * 1.5 * 30
            total_value += munitions_production * prices['munitions']
        
        return total_value

    def calculate_improvements_value(self, cities_data: List[Dict]) -> float:
        """Calculate total value of city improvements based on references.md."""
        total_value = 0.0
        
        for city in cities_data:
            # Military improvements (high value)
            total_value += city.get('barracks', 0) * 3000      # $3k each
            total_value += city.get('factory', 0) * 15000      # $15k each
            total_value += city.get('hangar', 0) * 100000      # $100k each
            total_value += city.get('drydock', 0) * 250000     # $250k each
            
            # Commerce improvements (medium value)
            total_value += city.get('supermarket', 0) * 5000   # $5k each
            total_value += city.get('bank', 0) * 15000         # $15k each
            total_value += city.get('shopping_mall', 0) * 45000  # $45k each
            total_value += city.get('stadium', 0) * 100000     # $100k each
            total_value += city.get('subway', 0) * 250000      # $250k each
            
            # Civil improvements (medium value)
            total_value += city.get('police_station', 0) * 75000  # $75k each
            total_value += city.get('hospital', 0) * 100000       # $100k each
            total_value += city.get('recycling_center', 0) * 125000  # $125k each
            
            # Resource improvements (medium value)
            total_value += city.get('coal_mine', 0) * 1000     # $1k each
            total_value += city.get('oil_well', 0) * 1000      # $1k each
            total_value += city.get('uranium_mine', 0) * 25000 # $25k each
            total_value += city.get('iron_mine', 0) * 9500     # $9.5k each
            total_value += city.get('bauxite_mine', 0) * 1000  # $1k each
            total_value += city.get('lead_mine', 0) * 1000     # $1k each
            total_value += city.get('farm', 0) * 1000          # $1k each
            
            # Manufacturing improvements (high value)
            total_value += city.get('oil_refinery', 0) * 45000    # $45k each
            total_value += city.get('steel_mill', 0) * 45000      # $45k each
            total_value += city.get('aluminum_refinery', 0) * 30000  # $30k each
            total_value += city.get('munitions_factory', 0) * 35000  # $35k each
            
            # Power improvements (medium value)
            total_value += city.get('nuclear_power', 0) * 500000  # $500k each
            total_value += city.get('oil_power', 0) * 7000        # $7k each
            total_value += city.get('coal_power', 0) * 5000       # $5k each
            total_value += city.get('wind_power', 0) * 30000      # $30k each
        
        return total_value

    def calculate_commerce_value(self, cities_data: List[Dict]) -> float:
        """Calculate commerce-based income potential based on references.md."""
        total_commerce_value = 0.0
        
        for city in cities_data:
            infrastructure = city.get('infrastructure', 0)
            land = city.get('land', 0)
            
            # Calculate commerce rate based on improvements (from references.md)
            commerce_rate = 0
            commerce_rate += city.get('supermarket', 0) * 3   # +3% each
            commerce_rate += city.get('bank', 0) * 5          # +5% each
            commerce_rate += city.get('shopping_mall', 0) * 9 # +9% each
            commerce_rate += city.get('stadium', 0) * 12      # +12% each
            commerce_rate += city.get('subway', 0) * 8        # +8% each
            
            # Cap at 100% (or 125% with International Trade Center project)
            commerce_rate = min(commerce_rate, 100)
            
            # Calculate city income
            # Base income = Infrastructure * 100 * (1 + Commerce/100)
            base_income = infrastructure * 100 * (1 + commerce_rate / 100)
            
            # Add land value
            land_value = land * 50  # Approximate land value
            
            total_commerce_value += base_income + land_value
        
        return total_commerce_value

    def calculate_score_bonus(self, nation_data: Dict) -> float:
        """Calculate bonus based on nation score and city count."""
        score = float(nation_data.get('score', 0))
        cities = int(nation_data.get('cities', 0))
        
        if cities == 0:
            return 0.1  # Very low bonus for inactive nations
        
        # Score per city ratio (indicates development level)
        score_per_city = score / cities if cities > 0 else 0
        
        # Higher score per city = more developed = more loot potential
        if score_per_city < 50:  # Underdeveloped
            return 0.5
        elif score_per_city < 100:  # Developing
            return 0.8
        elif score_per_city < 200:  # Developed
            return 1.0
        elif score_per_city < 300:  # Well-developed
            return 1.2
        else:  # Highly developed
            return 1.5

    def calculate_alliance_bonus(self, nation_data: Dict) -> float:
        """Calculate bonus based on alliance strength."""
        alliance_id = nation_data.get('alliance_id')
        alliance_name = nation_data.get('alliance_name', '').lower()
        
        # No alliance = easier target
        if not alliance_id or alliance_id == 0:
            return 1.2
        
        # Check for known strong alliances (public knowledge)
        strong_alliances = [
            'the legion', 'rose', 'tkr', 'tfp', 'npo', 'arrgh', 'sk', 'guardian',
            'cet', 'tct', 't$', 't$', 't$', 't$', 't$', 't$', 't$', 't$'
        ]
        
        if any(strong_alliance in alliance_name for strong_alliance in strong_alliances):
            return 0.8  # Strong alliance = harder to loot
        
        # Unknown alliance = neutral
        return 1.0

    async def _is_valid_raid_target(self, nation_data: Dict) -> bool:
        """Check if a nation is a valid raid target using ONLY real-time API data."""
        nation_name = nation_data.get('nation_name', 'Unknown')
        nation_id = nation_data.get('id')
        
        try:
            # Get real-time nation data with alliance information
            from api.politics_war_api import api
            detailed_nation = await api.get_nation_data(nation_id, "everything_scope")
            
            if not detailed_nation:
                logger.warning(f"Alliance filter: {nation_name} - API call returned None, FILTERED")
                return False
            
            # Check if detailed_nation is a dictionary
            if not isinstance(detailed_nation, dict):
                logger.warning(f"Alliance filter: {nation_name} - API call returned non-dict: {type(detailed_nation)}, FILTERED")
                return False
            
            # Get real-time alliance data
            alliance_id = detailed_nation.get('alliance_id', 0)
            alliance_data = detailed_nation.get('alliance', {})
            alliance_rank = alliance_data.get('rank', 999) if alliance_data else 999
            alliance_position = detailed_nation.get('alliance_position', '').upper()
            
            # No alliance = valid target
            if not alliance_id or alliance_id == 0:
                # Ensure alliance_name is set to 'None' for display
                if 'alliance_name' not in nation_data or not nation_data.get('alliance_name'):
                    nation_data['alliance_name'] = 'None'
                logger.debug(f"Alliance filter: {nation_name} - No alliance, VALID")
                return True
            
            # Check if it's our alliance (13033) - filter out our own members
            if alliance_id == 13033:
                logger.debug(f"Alliance filter: {nation_name} - Our alliance (13033), FILTERED")
                return False
            
            # Check if it's a top 65 alliance
            if alliance_rank <= 65:
                # Filter out actual members of top 65 alliances
                member_positions = {'MEMBER', 'OFFICER', 'HEIR', 'LEADER'}
                if alliance_position in member_positions:
                    logger.debug(f"Alliance filter: {nation_name} - Top 65 alliance member (rank {alliance_rank}, {alliance_position}), FILTERED")
                    return False
                else:
                    # Applicant or unknown position in top alliance
                    logger.debug(f"Alliance filter: {nation_name} - Top 65 alliance applicant (rank {alliance_rank}, {alliance_position}), VALID")
                    return True
            else:
                # Nations in smaller alliances (rank > 65) are valid targets
                logger.debug(f"Alliance filter: {nation_name} - Small alliance (rank {alliance_rank}), VALID")
                return True
                
        except Exception as e:
            logger.error(f"Alliance filter: {nation_name} - Error checking alliance status: {e}")
            # If API call fails, be conservative and filter out
            return False

    async def filter_raid_targets(self, user_nation_data: Dict, all_nations: Dict, cities_data: Dict, wars_data: Dict, alliances_data: Dict, progress_callback=None) -> Tuple[List[Dict], Dict[str, int]]:
        """Filter nations through optimized pipeline with all filtering before calculations."""
        user_score = float(user_nation_data.get('score', 0))
        min_score = user_score * 0.75  # 75% of user's score
        max_score = user_score * 1.25  # 125% of user's score
        
        valid_targets = []
        filtered_out = {
            'score_range': 0,
            'vmode': 0,
            'beige_turns': 0,
            'defensive_wars': 0,
            'no_cities': 0,
            'alliance_member': 0,
            'low_loot': 0
        }
        
        logger.info(f"Filtering targets for user score {user_score} (range: {min_score}-{max_score})")
        
        # Update progress
        if progress_callback:
            await progress_callback("Phase 1: CSV-based filtering (score, vmode, beige, wars, cities)")
        
        # Phase 1: CSV-based filtering (fast, bulk operations)
        candidates = []
        for nation_id, nation_data in all_nations.items():
            # Stage 1: Score Range Filter
            nation_score = float(nation_data.get('score', 0))
            if not (min_score <= nation_score <= max_score):
                filtered_out['score_range'] += 1
                continue
            
            # Stage 2: Vacation Mode Filter
            if nation_data.get('vmode', 0) == 1:
                filtered_out['vmode'] += 1
                continue
            
            # Stage 3: Beige Turns Filter
            if nation_data.get('beige_turns', 0) > 0:
                filtered_out['beige_turns'] += 1
                continue
            
            # Stage 4: Defensive Wars Filter
            nation_wars = wars_data.get(nation_id, [])
            defensive_wars = len([w for w in nation_wars if w.get('defender_id') == nation_id])
            if defensive_wars >= 3:
                filtered_out['defensive_wars'] += 1
                continue
            
            # Stage 5: Cities Existence Filter
            nation_cities = cities_data.get(nation_id, [])
            if not nation_cities:
                filtered_out['no_cities'] += 1
                continue
            
            # Add to candidates for API filtering
            candidates.append({
                'nation_id': nation_id,
                'nation_data': nation_data,
                'cities_data': nation_cities,
                'wars_data': nation_wars
            })
        
        logger.info(f"After CSV filtering: {len(candidates)} candidates for API checks")
        
        # Update progress
        if progress_callback:
            await progress_callback(f"Phase 2: Alliance filtering ({len(candidates)} candidates)")
        
        # Store progress callback for batch methods
        self._progress_callback = progress_callback
        
        # Phase 2: Batch API-based alliance filtering (before calculations)
        alliance_filtered_candidates = await self._batch_alliance_filtering(candidates, filtered_out)
        
        logger.info(f"After alliance filtering: {len(alliance_filtered_candidates)} candidates for city improvements check")
        
        # Update progress
        if progress_callback:
            await progress_callback(f"Phase 3: City improvements analysis ({len(alliance_filtered_candidates)} candidates)")
        
        # Phase 3: Batch API call for city improvements (only for alliance-filtered candidates)
        if alliance_filtered_candidates:
            from api.politics_war_api import api
            candidate_ids = [c['nation_id'] for c in alliance_filtered_candidates]
            city_improvements_data = await self._get_city_improvements_with_rate_limiting(api, candidate_ids)
            
            # Update progress
            if progress_callback:
                await progress_callback(f"Phase 4: Loot calculation and final filtering ({len(alliance_filtered_candidates)} candidates)")
            
            # Phase 4: Calculate loot potential and filter by loot threshold
            for candidate in alliance_filtered_candidates:
                nation_id = candidate['nation_id']
                nation_data = candidate['nation_data']
                nation_cities = candidate['cities_data']
                nation_wars = candidate['wars_data']
                
                # Use real-time city improvements if available, fallback to CSV
                if nation_id in city_improvements_data:
                    real_cities = city_improvements_data[nation_id]
                    loot_potential = await self.calculate_loot_potential(nation_data, real_cities, nation_wars)
                    final_cities = real_cities
                else:
                    # Fallback to CSV data
                    loot_potential = await self.calculate_loot_potential(nation_data, nation_cities, nation_wars)
                    final_cities = nation_cities
                
                # Stage 7: Loot Potential Filter (final filter)
                if loot_potential <= 100000:  # Minimum $100k loot
                    filtered_out['low_loot'] += 1
                    continue
                
                # Add to valid targets
                valid_targets.append({
                    'nation_data': nation_data,
                    'cities_data': final_cities,
                    'wars_data': nation_wars,
                    'loot_potential': loot_potential,
                    'profit_score': loot_potential
                })
        
        # Sort by profit score (descending)
        valid_targets.sort(key=lambda x: x['profit_score'], reverse=True)
        
        # Update progress
        if progress_callback:
            await progress_callback(f"✅ Search complete! Found {len(valid_targets)} valid targets")
        
        logger.info(f"Found {len(valid_targets)} valid targets after all filtering")
        logger.info(f"Filtering stats: {filtered_out}")
        
        return valid_targets, filtered_out

    async def _batch_alliance_filtering(self, candidates: List[Dict], filtered_out: Dict[str, int]) -> List[Dict]:
        """Batch process alliance filtering to reduce API calls."""
        if not candidates:
            return []
        
        from api.politics_war_api import api
        
        # Configuration for batch alliance filtering
        ALLIANCE_CHUNK_SIZE = 50  # Process 50 nations at a time for alliance checks
        ALLIANCE_DELAY = 0.5  # 500ms delay between alliance chunks
        MAX_ALLIANCE_RETRIES = 2
        ALLIANCE_RETRY_DELAY = 1.0
        
        alliance_filtered_candidates = []
        candidate_ids = [c['nation_id'] for c in candidates]
        total_chunks = (len(candidate_ids) + ALLIANCE_CHUNK_SIZE - 1) // ALLIANCE_CHUNK_SIZE
        
        logger.info(f"🌐 Processing {len(candidate_ids)} nations for alliance filtering in {total_chunks} chunks of {ALLIANCE_CHUNK_SIZE}")
        
        for i in range(0, len(candidate_ids), ALLIANCE_CHUNK_SIZE):
            chunk_ids = candidate_ids[i:i + ALLIANCE_CHUNK_SIZE]
            chunk_num = (i // ALLIANCE_CHUNK_SIZE) + 1
            
            logger.info(f"🌐 Processing alliance chunk {chunk_num}/{total_chunks} ({len(chunk_ids)} nations)")
            
            # Update progress with chunk info
            if hasattr(self, '_progress_callback') and self._progress_callback:
                await self._progress_callback(f"Phase 2: Alliance filtering - Chunk {chunk_num}/{total_chunks} ({len(chunk_ids)} nations)")
            
            # Get alliance data for this chunk
            chunk_alliance_data = await self._get_alliance_data_with_retry(api, chunk_ids, MAX_ALLIANCE_RETRIES, ALLIANCE_RETRY_DELAY)
            
            if chunk_alliance_data:
                # Filter candidates in this chunk
                for candidate in candidates[i:i + ALLIANCE_CHUNK_SIZE]:
                    nation_id = candidate['nation_id']
                    nation_data = candidate['nation_data']
                    
                    # Check alliance status using batch data
                    if self._is_valid_raid_target_from_batch(nation_data, chunk_alliance_data.get(nation_id)):
                        alliance_filtered_candidates.append(candidate)
                    else:
                        filtered_out['alliance_member'] += 1
                
                logger.info(f"✅ Alliance chunk {chunk_num} completed successfully")
            else:
                logger.warning(f"⚠️ Alliance chunk {chunk_num} failed, using CSV data as fallback")
                # Fallback: assume all nations in this chunk are valid targets (conservative approach)
                # This prevents the system from completely failing due to API issues
                for candidate in candidates[i:i + ALLIANCE_CHUNK_SIZE]:
                    alliance_filtered_candidates.append(candidate)
                    logger.debug(f"🌐 Using CSV fallback for nation {candidate['nation_id']}")
            
            # Add delay between chunks (except for the last one)
            if i + ALLIANCE_CHUNK_SIZE < len(candidate_ids):
                await asyncio.sleep(ALLIANCE_DELAY)
        
        logger.info(f"🌐 Completed alliance filtering: {len(alliance_filtered_candidates)} candidates passed")
        return alliance_filtered_candidates

    async def _get_alliance_data_with_retry(self, api, nation_ids: List[int], max_retries: int, retry_delay: float) -> Optional[Dict[int, Dict]]:
        """Get alliance data for multiple nations with retry logic using batch API."""
        for attempt in range(max_retries):
            try:
                # Use the new batch alliance API
                alliance_data = await api.get_alliance_batch_data(nation_ids, "everything_scope")
                
                if alliance_data:
                    return alliance_data
                else:
                    logger.warning(f"🌐 Alliance batch API call returned no data (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"🌐 Alliance batch API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
        
        logger.error(f"🌐 All {max_retries} attempts failed for alliance batch")
        return None

    def _is_valid_raid_target_from_batch(self, nation_data: Dict, alliance_data: Optional[Dict]) -> bool:
        """Check if a nation is a valid raid target using batch alliance data."""
        if not alliance_data:
            return False
        
        alliance_id = alliance_data.get('alliance_id', 0)
        alliance_info = alliance_data.get('alliance', {})
        alliance_rank = alliance_info.get('rank', 999) if alliance_info else 999
        alliance_position = alliance_data.get('alliance_position', '').upper()
        
        # No alliance = valid target
        if not alliance_id or alliance_id == 0:
            # Ensure alliance_name is set to 'None' for display
            if 'alliance_name' not in nation_data or not nation_data.get('alliance_name'):
                nation_data['alliance_name'] = 'None'
            return True
        
        # Check if it's our alliance (13033) - filter out our own members
        if alliance_id == 13033:
            return False
        
        # Check if it's a top 65 alliance
        if alliance_rank <= 65:
            # Filter out actual members of top 65 alliances
            member_positions = {'MEMBER', 'OFFICER', 'HEIR', 'LEADER'}
            if alliance_position in member_positions:
                return False
            else:
                # Applicant or unknown position in top alliance
                return True
        else:
            # Nations in smaller alliances (rank > 65) are valid targets
            return True

    async def _get_city_improvements_with_rate_limiting(self, api, candidate_ids: List[int]) -> Dict[int, List[Dict]]:
        """Get city improvements data with intelligent batching, rate limiting, and caching."""
        if not candidate_ids:
            return {}
        
        # Check cache first
        current_time = time.time()
        if current_time - self._cache_timestamp < self._cache_duration and self._city_cache:
            logger.info(f"🌐 Using cached city data ({len(self._city_cache)} nations cached)")
            # Return cached data for requested nations
            cached_data = {nation_id: self._city_cache.get(nation_id, []) for nation_id in candidate_ids}
            return cached_data
        
        # Configuration for rate limiting
        CHUNK_SIZE = 25  # Process 25 nations at a time
        DELAY_BETWEEN_CHUNKS = 0.3  # 300ms delay between chunks
        MAX_RETRIES = 3
        RETRY_DELAY = 1.0  # 1 second delay on retry
        
        city_improvements_data = {}
        total_chunks = (len(candidate_ids) + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        logger.info(f"🌐 Processing {len(candidate_ids)} nations in {total_chunks} chunks of {CHUNK_SIZE}")
        
        for i in range(0, len(candidate_ids), CHUNK_SIZE):
            chunk = candidate_ids[i:i + CHUNK_SIZE]
            chunk_num = (i // CHUNK_SIZE) + 1
            
            logger.info(f"🌐 Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} nations)")
            
            # Update progress with chunk info
            if hasattr(self, '_progress_callback') and self._progress_callback:
                await self._progress_callback(f"Phase 3: City improvements - Chunk {chunk_num}/{total_chunks} ({len(chunk)} nations)")
            
            # Try to get city data for this chunk with retries
            chunk_data = await self._get_chunk_with_retry(api, chunk, MAX_RETRIES, RETRY_DELAY)
            
            if chunk_data:
                city_improvements_data.update(chunk_data)
                # Update cache
                self._city_cache.update(chunk_data)
                logger.info(f"✅ Chunk {chunk_num} completed successfully")
            else:
                logger.warning(f"⚠️ Chunk {chunk_num} failed, using CSV fallback")
                # Fallback to empty data (will use CSV data in calculation)
                for nation_id in chunk:
                    city_improvements_data[nation_id] = []
            
            # Add delay between chunks (except for the last one)
            if i + CHUNK_SIZE < len(candidate_ids):
                await asyncio.sleep(DELAY_BETWEEN_CHUNKS)
        
        # Update cache timestamp
        self._cache_timestamp = current_time
        
        logger.info(f"🌐 Completed city improvements fetch: {len(city_improvements_data)} nations processed")
        return city_improvements_data

    async def _get_chunk_with_retry(self, api, chunk: List[int], max_retries: int, retry_delay: float) -> Optional[Dict[int, List[Dict]]]:
        """Get city data for a chunk with retry logic."""
        for attempt in range(max_retries):
            try:
                result = await api.get_cities_batch_data(chunk)
                if result:
                    return result
                else:
                    logger.warning(f"🌐 Chunk API call returned None (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.warning(f"🌐 Chunk API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
        
        logger.error(f"🌐 All {max_retries} attempts failed for chunk")
        return None

    def clear_city_cache(self):
        """Clear the city improvements cache."""
        self._city_cache.clear()
        self._cache_timestamp = 0
        logger.info("🌐 City improvements cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        cache_age = current_time - self._cache_timestamp
        is_valid = cache_age < self._cache_duration
        
        return {
            'cached_nations': len(self._city_cache),
            'cache_age_seconds': cache_age,
            'cache_duration_seconds': self._cache_duration,
            'is_valid': is_valid,
            'cache_hit_rate': 'N/A'  # Could be implemented with hit/miss counters
        }
