"""
Politics and War API client with key rotation.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from config.constants import GameConstants
from api.key_manager import key_manager
from utils.logging import get_logger

logger = get_logger('api')

class PoliticsWarAPI:
    """Politics and War API client with key rotation and rate limiting."""
    
    def __init__(self):
        self.base_url = "https://api.politicsandwar.com"
        self.graphql_url = f"{self.base_url}/graphql"
        self.csv_url = f"{self.base_url}/nation/id={config.ALLIANCE_ID}&key="
        self.timeout = aiohttp.ClientTimeout(total=GameConstants.API_TIMEOUT)
    
    async def _make_request(self, url: str, params: Dict = None, scope: str = "everything_scope") -> Optional[Dict]:
        """Make API request with key rotation and rate limiting."""
        api_key = key_manager.get_key(scope)
        
        # Check rate limit
        if not key_manager.check_rate_limit(api_key):
            # Try next key
            api_key = key_manager.get_key(scope)
        
        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = api_key
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        # Rate limit exceeded
                        key_manager.mark_key_unhealthy(api_key, "Rate limit exceeded")
                        # Retry with different key
                        return await self._make_request(url, params, scope)
                    
                    if response.status == 200:
                        key_manager.increment_usage(api_key)
                        return await response.json()
                    else:
                        key_manager.mark_key_unhealthy(api_key, f"HTTP {response.status}")
                        return None
        
        except Exception as e:
            key_manager.mark_key_unhealthy(api_key, str(e))
            raise
    
    async def _make_graphql_request(self, query: str, variables: Dict = None, scope: str = "everything_scope") -> Optional[Dict]:
        """Make GraphQL request with key rotation."""
        api_key = key_manager.get_key(scope)
        
        # Check rate limit
        if not key_manager.check_rate_limit(api_key):
            logger.warning(f"🌐 Rate limit exceeded for key, trying next key")
            api_key = key_manager.get_key(scope)
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        try:
            # Use GET request with query parameter like the backup
            url = f"{self.graphql_url}?api_key={api_key}&query={query}"
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 429:
                        logger.warning(f"🌐 Rate limit exceeded, retrying with different key")
                        key_manager.mark_key_unhealthy(api_key, "Rate limit exceeded")
                        return await self._make_graphql_request(query, variables, scope)
                    
                    if response.status == 200:
                        key_manager.increment_usage(api_key)
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"🌐 GraphQL request failed with status: {response.status}")
                        key_manager.mark_key_unhealthy(api_key, f"HTTP {response.status}")
                        return None
        
        except Exception as e:
            key_manager.mark_key_unhealthy(api_key, str(e))
            raise
    
    async def get_nation_data(self, nation_id: int, scope: str = "everything_scope") -> Optional[Dict]:
        """Get nation data by ID."""
        
        # Use the correct GraphQL structure based on actual API schema
        query = f"""{{
            nations(id: {nation_id}) {{
                data {{
                    date
                    id
                    nation_name
                    leader_name
                    score
                    color
                    alliance_id
                    alliance {{
                        id
                        name
                        rank
                    }}
                    alliance_position
                    last_active
                    soldiers
                    tanks
                    aircraft
                    ships
                    spies
                    missiles
                    nukes
                    projects
                    project_bits
                    turns_since_last_project
                    wars_won
                    wars_lost
                    central_intelligence_agency
                    discord
                    military_research {{
                        ground_capacity
                        air_capacity
                        naval_capacity
                    }}
                    vmode
                    beige_turns
                    money
                    coal
                    oil
                    uranium
                    iron
                    bauxite
                    lead
                    gasoline
                    munitions
                    steel
                    aluminum
                    food
                    credits
                    cities {{
                        id
                        name
                        infrastructure
                        land
                        powered
                        oilpower
                        windpower
                        coalpower
                        nuclearpower
                        date
                        barracks
                        hangar
                        drydock
                        factory
                        farm
                        steel_mill
                        aluminum_refinery
                        oil_refinery
                        munitions_factory
                        coal_mine
                        oil_well
                        uranium_mine
                        iron_mine
                        bauxite_mine
                        lead_mine
                    }}
                    defensive_wars {{
                        id
                        attacker {{
                            id
                            nation_name
                            leader_name
                        }}
                        defender {{
                            id
                            nation_name
                            leader_name
                        }}
                        war_type
                        reason
                        turns_left
                        groundcontrol
                        airsuperiority
                        navalblockade
                        att_resistance
                        def_resistance
                        att_fortify
                        def_fortify
                    }}
                    offensive_wars {{
                        id
                        attacker {{
                            id
                            nation_name
                            leader_name
                        }}
                        defender {{
                            id
                            nation_name
                            leader_name
                        }}
                        war_type
                        reason
                        turns_left
                        groundcontrol
                        airsuperiority
                        navalblockade
                        att_resistance
                        def_resistance
                        att_fortify
                        def_fortify
                    }}
                }}
            }}
        }}"""
        
        response = await self._make_graphql_request(query, scope=scope)
        if response and response.get("data", {}).get("nations", {}).get("data"):
            nation_data = response["data"]["nations"]["data"][0]
            return nation_data
        else:
            logger.warning(f"🌐 No nation data found for ID: {nation_id}")
            if response:
                logger.warning(f"🌐 Response structure: {list(response.keys()) if isinstance(response, dict) else type(response)}")
                if response.get("errors"):
                    logger.error(f"🌐 GraphQL errors: {response['errors']}")
            return None
    
    async def get_nations_batch_data(self, nation_ids: List[int], scope: str = "everything_scope") -> Optional[Dict[int, Dict]]:
        """Get detailed nation data for multiple nations in a single API call."""
        if not nation_ids:
            return {}
        
        # Convert nation IDs to proper GraphQL array format
        ids_str = ','.join(map(str, nation_ids))
        
        # Create a properly formatted GraphQL query with all the fields from get_nation_data
        query = f"""query {{
            nations(first: 500, vmode: false, id: [{ids_str}]) {{
                data {{
                    date
                    id
                    nation_name
                    leader_name
                    score
                    color
                    alliance_id
                    alliance {{
                        id
                        name
                        rank
                    }}
                    alliance_position
                    last_active
                    soldiers
                    tanks
                    aircraft
                    ships
                    spies
                    missiles
                    nukes
                    projects
                    project_bits
                    turns_since_last_project
                    wars_won
                    wars_lost
                    central_intelligence_agency
                    discord
                    military_research {{
                        ground_capacity
                        air_capacity
                        naval_capacity
                    }}
                    vmode
                    beige_turns
                    money
                    coal
                    oil
                    uranium
                    iron
                    bauxite
                    lead
                    gasoline
                    munitions
                    steel
                    aluminum
                    food
                    credits
                    population
                    defensive_wars_count
                    cities {{
                        id
                        name
                        date
                        infrastructure
                        land
                        coal_power
                        oil_power
                        nuclear_power
                        wind_power
                        farm
                        uranium_mine
                        iron_mine
                        coal_mine
                        oil_refinery
                        steel_mill
                        aluminum_refinery
                        munitions_factory
                        police_station
                        hospital
                        recycling_center
                        subway
                        supermarket
                        bank
                        shopping_mall
                        stadium
                        barracks
                        factory
                        hangar
                        drydock
                    }}
                    defensive_wars {{
                        id
                        attacker {{
                            id
                            nation_name
                            leader_name
                        }}
                        defender {{
                            id
                            nation_name
                            leader_name
                        }}
                        war_type
                        reason
                        turns_left
                        groundcontrol
                        airsuperiority
                        navalblockade
                        att_resistance
                        def_resistance
                        att_fortify
                        def_fortify
                    }}
                    offensive_wars {{
                        id
                        attacker {{
                            id
                            nation_name
                            leader_name
                        }}
                        defender {{
                            id
                            nation_name
                            leader_name
                        }}
                        war_type
                        reason
                        turns_left
                        groundcontrol
                        airsuperiority
                        navalblockade
                        att_resistance
                        def_resistance
                        att_fortify
                        def_fortify
                    }}
                }}
            }}
        }}"""
        
        response = await self._make_graphql_request(query, scope=scope)
        if response and response.get("data", {}).get("nations", {}).get("data"):
            nations_data = response["data"]["nations"]["data"]
            
            # Organize by nation ID
            result = {}
            for nation in nations_data:
                nation_id = nation.get('id')
                if nation_id:
                    result[nation_id] = nation
            
            logger.info(f"🌐 Retrieved detailed data for {len(result)} nations")
            return result
        else:
            logger.warning(f"🌐 No nations data found for IDs: {nation_ids}")
            if response:
                logger.warning(f"🌐 Response structure: {list(response.keys()) if isinstance(response, dict) else type(response)}")
                if response.get("errors"):
                    logger.error(f"🌐 GraphQL errors: {response['errors']}")
            return {}
    
    async def get_alliance_data(self, alliance_id: int, scope: str = "alliance_scope") -> Optional[Dict]:
        """Get alliance data by ID."""
        query = """
        {
            alliances(id: %d) {
                data {
                    id
                    name
                    acronym
                    color
                    score
                    flag
                    created
                }
            }
        }
        """ % alliance_id
        
        response = await self._make_graphql_request(query, scope=scope)
        if response and response.get("data", {}).get("alliances", {}).get("data"):
            return response["data"]["alliances"]["data"][0]
        else:
            logger.warning(f"Alliance data not found for ID {alliance_id}. Response: {response}")
        return None
    
    async def get_alliance_members(self, alliance_id: int, scope: str = "alliance_scope") -> Optional[List[Dict]]:
        """Get alliance members."""
        # Use string formatting like the old implementation
        query = f"""{{
            nations(first:500, vmode: false, alliance_id:{alliance_id}) {{
                data {{
                    id
                    nation_name
                    leader_name
                    score
                    soldiers
                    tanks
                    aircraft
                    ships
                    money
                    oil
                    uranium
                    iron
                    bauxite
                    lead
                    coal
                    gasoline
                    munitions
                    steel
                    aluminum
                    food
                    credits
                    population
                    defensive_wars_count
                    last_active
                    discord
                    alliance_position
                    spies
                    missiles
                    nukes
                    projects
                    vmode
                    beige_turns
                    color
                    alliance_id
                    alliance {{
                        id
                        name
                        color
                    }}
                    cities {{
                        id
                        name
                        date
                        infrastructure
                        land
                        coal_power
                        oil_power
                        nuclear_power
                        wind_power
                        farm
                        uranium_mine
                        iron_mine
                        coal_mine
                        oil_refinery
                        steel_mill
                        aluminum_refinery
                        munitions_factory
                        police_station
                        hospital
                        recycling_center
                        subway
                        supermarket
                        bank
                        shopping_mall
                        stadium
                        barracks
                        factory
                        hangar
                        drydock
                    }}
                    defensive_wars {{
                        id
                        att_id
                        def_id
                        war_type
                        reason
                        turns_left
                    }}
                    offensive_wars {{
                        id
                        att_id
                        def_id
                        war_type
                        reason
                        turns_left
                    }}
                }}
            }}
        }}"""
        
        response = await self._make_graphql_request(query, scope=scope)
        logger.info(f"🌐 Alliance members response: {response}")
        if response and response.get("data", {}).get("nations", {}).get("data"):
            members = response["data"]["nations"]["data"]
            logger.info(f"🌐 Found {len(members)} alliance members")
            return members
        else:
            logger.warning(f"🌐 No alliance members found in response")
            return None
    
    async def get_war_data(self, war_id: int, scope: str = "everything_scope") -> Optional[Dict]:
        """Get war data by ID."""
        query = """
        {
            wars(id: %d) {
                data {
                    id
                    attacker_id
                    attacker_name
                    defender_id
                    defender_name
                    war_type
                    reason
                    turns_left
                    ground_control
                    air_control
                    naval_control
                    attacker_military
                    defender_military
                    attacker_resistance
                    defender_resistance
                    attacker_war_points
                    defender_war_points
                    loot
                    created
                }
            }
        }
        """ % war_id
        
        response = await self._make_graphql_request(query, scope=scope)
        if response and response.get("data", {}).get("wars", {}).get("data"):
            return response["data"]["wars"]["data"][0]
        return None
    
    async def get_alliance_batch_data(self, nation_ids: List[int], scope: str = "everything_scope") -> Optional[Dict[int, Dict]]:
        """Get alliance data for multiple nations in a single API call."""
        if not nation_ids:
            return {}
        
        # Convert nation IDs to proper GraphQL array format
        # GraphQL expects [1,2,3] format with double quotes
        ids_str = ','.join(map(str, nation_ids))
        
        # Create a properly formatted GraphQL query
        query = f"""query {{
            nations(first: 500, vmode: false, id: [{ids_str}]) {{
                data {{
                    id
                    alliance_id
                    alliance {{
                        id
                        name
                        rank
                    }}
                    alliance_position
                }}
            }}
        }}"""
        
        response = await self._make_graphql_request(query, scope=scope)
        if response and response.get("data", {}).get("nations", {}).get("data"):
            nations_data = response["data"]["nations"]["data"]
            
            # Organize by nation ID
            result = {}
            for nation in nations_data:
                nation_id = nation.get('id')
                if nation_id:
                    result[nation_id] = {
                        'alliance_id': nation.get('alliance_id', 0),
                        'alliance': nation.get('alliance', {}),
                        'alliance_position': nation.get('alliance_position', '')
                    }
            
            logger.info(f"🌐 Retrieved alliance data for {len(result)} nations")
            return result
        else:
            logger.warning(f"🌐 No alliance data found for nations: {nation_ids}")
            if response and response.get("errors"):
                logger.error(f"🌐 Alliance batch GraphQL errors: {response['errors']}")
            return {}

    async def get_cities_batch_data(self, nation_ids: List[int], scope: str = "everything_scope") -> Optional[Dict[int, List[Dict]]]:
        """Get city improvements data for multiple nations in a single API call."""
        if not nation_ids:
            return {}
        
        # Convert nation IDs to proper GraphQL array format
        # GraphQL expects [1,2,3] format with double quotes
        ids_str = ','.join(map(str, nation_ids))
        
        # Create a properly formatted GraphQL query
        query = f"""query {{
            nations(first: 500, vmode: false, id: [{ids_str}]) {{
                data {{
                    id
                    cities {{
                        id
                        name
                        infrastructure
                        land
                        powered
                        nuclearpower
                        oilpower
                        coalpower
                        windpower
                        coal_mine
                        oil_well
                        uranium_mine
                        iron_mine
                        bauxite_mine
                        lead_mine
                        farm
                        oil_refinery
                        steel_mill
                        aluminum_refinery
                        munitions_factory
                        police_station
                        hospital
                        recycling_center
                        subway
                        supermarket
                        bank
                        shopping_mall
                        stadium
                        barracks
                        factory
                        hangar
                        drydock
                        date
                    }}
                }}
            }}
        }}"""
        
        response = await self._make_graphql_request(query, scope=scope)
        if response and response.get("data", {}).get("nations", {}).get("data"):
            nations_data = response["data"]["nations"]["data"]
            
            # Organize by nation ID
            result = {}
            for nation in nations_data:
                nation_id = nation.get('id')
                cities = nation.get('cities', [])
                if nation_id:
                    result[nation_id] = cities
            
            logger.info(f"🌐 Retrieved city data for {len(result)} nations")
            return result
        else:
            logger.warning(f"🌐 No city data found for nations: {nation_ids}")
            if response and response.get("errors"):
                logger.error(f"🌐 Cities batch GraphQL errors: {response['errors']}")
            return {}

    async def get_tradeprices(self, scope: str = "everything_scope") -> Optional[List[Dict]]:
        """Get current trade prices for resources."""
        query = """{
            tradeprices(first: 1) {
                data {
                    id
                    date
                    coal
                    oil
                    uranium
                    iron
                    bauxite
                    lead
                    gasoline
                    munitions
                    steel
                    aluminum
                    food
                    credits
                }
            }
        }"""
        
        response = await self._make_graphql_request(query, scope=scope)
        if response and response.get("data", {}).get("tradeprices", {}).get("data"):
            prices_data = response["data"]["tradeprices"]["data"]
            logger.info(f"🌐 Retrieved trade prices for {len(prices_data)} entries")
            return prices_data
        else:
            logger.warning("🌐 No trade prices data found")
            return []

    async def download_csv_data(self, data_type: str, scope: str = "everything_scope") -> Optional[str]:
        """Download CSV data from Politics and War."""
        api_key = key_manager.get_key(scope)
        
        # Check rate limit
        if not key_manager.check_rate_limit(api_key):
            api_key = key_manager.get_key(scope)
        
        url = f"{self.base_url}/{data_type}.csv"
        params = {"api_key": api_key}
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        key_manager.mark_key_unhealthy(api_key, "Rate limit exceeded")
                        return await self.download_csv_data(data_type, scope)
                    
                    if response.status == 200:
                        key_manager.increment_usage(api_key)
                        return await response.text()
                    else:
                        key_manager.mark_key_unhealthy(api_key, f"HTTP {response.status}")
                        return None
        
        except Exception as e:
            key_manager.mark_key_unhealthy(api_key, str(e))
            raise

# Global API instance
api = PoliticsWarAPI()
