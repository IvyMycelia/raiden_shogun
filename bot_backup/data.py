import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import pytz
from bot.handler import error, info
import time

def GET_ALLIANCE_MEMBERS(ALLIANCE_ID: int, API_KEY: str, max_retries: int = 3):
    """Get alliance members from the API with retry logic."""
    query = f"""{{
    nations(first:500, vmode: false, alliance_id:{ALLIANCE_ID}) {{data {{
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

        military_research {{
            ground_capacity
            air_capacity
            naval_capacity
        }}

        alliance {{
            id
            name
        }}

        cities {{
            date
            infrastructure
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
    }}}}}}"""
    
    url = f"https://api.politicsandwar.com/graphql?api_key={API_KEY}&query={query}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "errors" in data:
                error_msg = data["errors"][0] if isinstance(data["errors"], list) else data["errors"]
                error_type = error_msg.get("extensions", {}).get("category", "unknown")
                
                # If it's an internal server error, retry after a delay
                if error_type == "internal":
                    if attempt < max_retries - 1:
                        error(f"Internal server error, retrying... (Attempt {attempt + 1}/{max_retries})", tag="ALLIANCE_MEMBERS")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        error(f"Internal server error after {max_retries} attempts", tag="ALLIANCE_MEMBERS")
                        return None
                else:
                    error(f"API Error: {error_msg}", tag="ALLIANCE_MEMBERS")
                    return None
            
            members = data.get("data", {}).get("nations", {}).get("data", [])
            if not members:
                error("No members found in the API response.", tag="ALLIANCE_MEMBERS")
                return None
                
            return members
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                error(f"API request failed, retrying... (Attempt {attempt + 1}/{max_retries}): {e}", tag="ALLIANCE_MEMBERS")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                error(f"API request failed after {max_retries} attempts: {e}", tag="ALLIANCE_MEMBERS")
                return None
                
        except (ValueError, KeyError, TypeError) as e:
            error(f"Error parsing API response: {e}", tag="ALLIANCE_MEMBERS")
            return None
    
    return None


def GET_ALLIANCE_DATA(alliance_id: str, api_key: str) -> Optional[Dict]:
    """Get alliance data from the API."""
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
            }
        }
    }
    """ % int(alliance_id)
    
    try:
        response = requests.post(
            "https://api.politicsandwar.com/graphql?api_key=" + api_key,
            json={"query": query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("alliances", {}).get("data"):
                return data["data"]["alliances"]["data"][0]
            else:
                error("No alliance data found in the API response.", tag="ALLIANCE_DATA")
                return None
        else:
            error(f"API Error: {response.status_code} - {response.text}", tag="ALLIANCE_DATA")
            return None
            
    except Exception as e:
        error(f"Error fetching alliance data: {e}", tag="ALLIANCE_DATA")
        return None


def GET_NATION_DATA(nation_id: int, api_key: str) -> Optional[Dict]:
    """Get nation data from the API."""
    query = """
    {
        nations(id: %d) { 
            data {
                last_active
                flag
                id
                score
                color
                population
                nation_name
                leader_name
                soldiers
                tanks
                aircraft
                ships
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
                continent
                discord
                spies_today
                
                alliance {
                    id
                    name
                }
                
                wars {
                    id
                    attacker {
                        id
                        nation_name
                        leader_name
                        soldiers
                        tanks
                        aircraft
                        ships
                        alliance {
                            id
                            name
                        }
                    }
                    defender {
                        id
                        nation_name
                        leader_name
                        soldiers
                        tanks
                        aircraft
                        ships
                        alliance {
                            id
                            name
                        }
                    }
                    war_type
                    turns_left
                    att_points
                    def_points
                    att_peace
                    def_peace
                    att_resistance
                    def_resistance
                    att_fortify
                    def_fortify
                    ground_control
                    air_superiority
                    naval_blockade
                }
            }
        }
    }
    """ % nation_id
    
    try:
        response = requests.post(
            "https://api.politicsandwar.com/graphql",
            json={"query": query, "variables": {"id": [nation_id]}},
            params={"api_key": api_key}
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            error(f"API Error in GET_NATION_DATA: {data['errors']}", tag="NATION")
            return None
            
        nations = data.get("data", {}).get("nations", {}).get("data", [])
        return nations[0] if nations else None
        
    except Exception as e:
        error(f"Error fetching nation data: {e}", tag="NATION")
        return None


def GET_CITY_DATA(nation_id: int, api_key: str) -> Optional[List[Dict]]:
    """Get city data for a nation from the API."""
    nation_id = int(nation_id)  # Ensure nation_id is always an integer
    query = """
    {
        nations(id:%d) { data {
            cities {
                name
                id
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
            }
        }}
    }
    """ % nation_id
    
    try:
        response = requests.get(
            "https://api.politicsandwar.com/graphql",
            params={"api_key": api_key, "query": query}
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print(f"API Error: {data['errors']}")
            return None
            
        nations = data.get("data", {}).get("nations", {}).get("data", [])
        return nations[0].get("cities", []) if nations else None
        
    except Exception as e:
        print(f"Error fetching city data: {e}")
        return None


def GET_PURGE_NATIONS(API_KEY: str):
    query = '''
        query {
            nations(max_score: 2000, color: "purple") { 
                data {
                    id
                    score
                    color
                    nation_name
                    leader_name
                    alliance_position
                    alliance {
                        id
                        name
                        rank
                    }
                }
            }
        }
    '''
    try:
        response = requests.post(
            "https://api.politicsandwar.com/graphql",
            json={"query": query},
            params={"api_key": API_KEY},
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

    try:
        data = response.json()
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            return None
            
        nation_list = data.get("data", {}).get("nations", {}).get("data", [])
        if not nation_list:
            print("No purple nations found in the API response.")
            return []

        return nation_list

    except Exception as e:
        print(f"Error parsing API response: {e}")
        return None




def GET_GAME_DATA(API_KEY: str):
    query = f"""
    {{
    game_info {{
            game_date
        
        radiation {{
            global
            north_america
            south_america
            europe
            africa
            asia
            australia
            antarctica
        }}
    }}
    }}
    """
    url = f"https://api.politicsandwar.com/graphql?api_key={API_KEY}&query={query}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return
    
    try:
        game_info = response.json()
        game_data = game_info.get("data", {}).get("game_info", {})
    except Exception as e:
        print(f"Error parsing API response: {e}")
        return
    
    return game_data

def GET_WAR_DATA(war_id: int, api_key: str) -> Optional[Dict]:
    """Get war data from the API."""
    query = """
    {
        wars(id:%d) { data {
            id
            attacker {
                id
                nation_name
                leader_name
                soldiers
                tanks
                aircraft
                ships
                alliance {
                    id
                    name
                }
            }
            defender {
                id
                nation_name
                leader_name
                soldiers
                tanks
                aircraft
                ships
                alliance {
                    id
                    name
                }
            }
            war_type
            turns_left
            att_points
            def_points
            att_peace
            def_peace
            att_resistance
            def_resistance
            att_fortify
            def_fortify
            ground_control
            air_superiority
            naval_blockade
        }}
    }
    """ % war_id
    
    try:
        response = requests.get(
            "https://api.politicsandwar.com/graphql",
            params={"api_key": api_key, "query": query}
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            print(f"API Error: {data['errors']}")
            return None
            
        wars = data.get("data", {}).get("wars", {}).get("data", [])
        return wars[0] if wars else None
        
    except Exception as e:
        print(f"Error fetching war data: {e}")
        return None

def GET_WARS(params: Dict, api_key: str) -> List[Dict]:
    """Get war data from the API."""
    query = """
    query Wars($id: [Int], $min_id: Int, $max_id: Int, $before: DateTime, $after: DateTime, 
              $ended_before: DateTime, $ended_after: DateTime, $attid: [Int], $defid: [Int], 
              $or_id: [Int], $days_ago: Int, $active: Boolean, $status: WarActivity, 
              $nation_id: [Int], $alliance_id: [Int], $orderBy: [QueryWarsOrderByOrderByClause!], 
              $first: Int, $page: Int) {
        wars(id: $id, min_id: $min_id, max_id: $max_id, before: $before, after: $after,
             ended_before: $ended_before, ended_after: $ended_after, attid: $attid, defid: $defid,
             or_id: $or_id, days_ago: $days_ago, active: $active, status: $status,
             nation_id: $nation_id, alliance_id: $alliance_id, orderBy: $orderBy,
             first: $first, page: $page) {
            data {
                id
                date
                end_date
                reason
                war_type
                ground_control
                air_superiority
                naval_blockade
                winner_id
                turns_left
                att_id
                att_alliance_id
                att_alliance_position
                def_id
                def_alliance_id
                def_alliance_position
                att_points
                def_points
                att_peace
                def_peace
                att_resistance
                def_resistance
                att_fortify
                def_fortify
                att_gas_used
                def_gas_used
                att_mun_used
                def_mun_used
                att_alum_used
                def_alum_used
                att_steel_used
                def_steel_used
                att_infra_destroyed
                def_infra_destroyed
                att_money_looted
                def_money_looted
                def_soldiers_lost
                att_soldiers_lost
                def_tanks_lost
                att_tanks_lost
                def_aircraft_lost
                att_aircraft_lost
                def_ships_lost
                att_ships_lost
                att_missiles_used
                def_missiles_used
                att_nukes_used
                def_nukes_used
                att_infra_destroyed_value
                def_infra_destroyed_value
                attacker {
                    id
                    leader_name
                    nation_name
                    alliance {
                        id
                        name
                    }
                }
                defender {
                    id
                    leader_name
                    nation_name
                    alliance {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    
    try:
        response = requests.post(
            "https://api.politicsandwar.com/graphql",
            json={"query": query, "variables": params},
            params={"api_key": api_key}
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            error(f"API Error: {data['errors']}", tag="WARS")
            return []
        
        return data["data"]["wars"]["data"]
    except Exception as e:
        error(f"Error fetching war data: {e}", tag="WARS")
        return []

# OLD BROKEN FUNCTION - REPLACED BELOW
def GET_ALL_NATIONS_OLD(api_key: str) -> Optional[List[Dict]]:
    """Get all nations from the API in chunks of 500."""
    all_nations = []
    page = 1
    
    while True:
        query = """
        {{
            nations(first: 500, page: %d) {{ 
                data {{
                    id
                    nation_name
                    leader_name
                    score
                    population
                    soldiers
                    tanks
                    aircraft
                    ships
                    alliance {{
                        id
                        name
                    }}
                    cities {{
                        infrastructure
                    }}
                }
            }}
        }}
        """ % page
        
        try:
            response = requests.get(
                "https://api.politicsandwar.com/graphql",
                params={"api_key": api_key, "query": query},
                timeout=30  # Add timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                error(f"API Error in GET_ALL_NATIONS: {data['errors']}", tag="NATIONS")
                return None
                
            nations = data.get("data", {}).get("nations", {}).get("data", [])
            if not nations:  # No more nations to fetch
                break
                
            all_nations.extend(nations)
            page += 1
            
            # Add a small delay between requests to avoid rate limiting
            time.sleep(0.5)
            
        except requests.exceptions.Timeout:
            error("Timeout while fetching nations data", tag="NATIONS")
            return None
        except requests.exceptions.RequestException as e:
            error(f"Request error while fetching nations: {e}", tag="NATIONS")
            return None
        except Exception as e:
            error(f"Unexpected error in GET_ALL_NATIONS: {e}", tag="NATIONS")
            return None
    
    return all_nations if all_nations else None

async def GET_ALL_NATIONS(api_key: str, max_pages: int = 20) -> Optional[List[Dict]]:
    """Get nations from the API in chunks of 500, limited to max_pages."""
    import aiohttp
    import asyncio
    
    all_nations = []
    page = 1
    
    info(f"Starting to fetch nations from API (max {max_pages} pages = {max_pages * 500} nations)...", tag="NATIONS")
    
    async with aiohttp.ClientSession() as session:
        while page <= max_pages:
            query = """
            query GetNations($first: Int!, $page: Int!) {
                nations(first: $first, page: $page) { 
                    data {
                        id
                        nation_name
                        leader_name
                        score
                        population
                        soldiers
                        tanks
                        aircraft
                        ships
                        beige_turns
                        alliance {
                            id
                            name
                            rank
                        }
                        cities {
                            infrastructure
                            supermarket
                            bank
                            shopping_mall
                            stadium
                            subway
                            coal_mine
                            oil_well
                            uranium_mine
                            iron_mine
                            bauxite_mine
                            lead_mine
                            oil_refinery
                            steel_mill
                            aluminum_refinery
                            munitions_factory
                        }
                        projects
                        wars {
                            id
                            defender {
                                id
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "first": 500,
                "page": page
            }
            
            try:
                async with session.post(
                    "https://api.politicsandwar.com/graphql",
                    json={"query": query, "variables": variables},
                    params={"api_key": api_key},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if "errors" in data:
                        error(f"API Error in GET_ALL_NATIONS: {data['errors']}", tag="NATIONS")
                        return None
                        
                    nations = data.get("data", {}).get("nations", {}).get("data", [])
                    if not nations:  # No more nations to fetch
                        break
                        
                    all_nations.extend(nations)
                    info(f"Fetched page {page}: {len(nations)} nations (total: {len(all_nations)})", tag="NATIONS")
                    page += 1
                    
                    # Add a small delay between requests to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
            except asyncio.TimeoutError:
                error("Timeout while fetching nations data", tag="NATIONS")
                return None
            except aiohttp.ClientError as e:
                error(f"Request error while fetching nations: {e}", tag="NATIONS")
                return None
            except Exception as e:
                error(f"Unexpected error in GET_ALL_NATIONS: {e}", tag="NATIONS")
                return None
    
    info(f"Finished fetching nations: {len(all_nations)} total", tag="NATIONS")
    return all_nations if all_nations else None

async def GET_NATIONS_IN_RANGE(api_key: str, min_score: float, max_score: float) -> Optional[List[Dict]]:
    """Get nations in a specific score range for faster raid searches."""
    import aiohttp
    import asyncio
    
    all_nations = []
    page = 1
    max_pages = 10  # Limit to 10 pages (5000 nations max)
    
    info(f"Fetching nations in score range {min_score:,.0f} - {max_score:,.0f}...", tag="RAID")
    
    async with aiohttp.ClientSession() as session:
        while page <= max_pages:
            query = """
            query GetNationsInRange($first: Int!, $page: Int!, $min_score: Float!, $max_score: Float!) {
                nations(first: $first, page: $page, min_score: $min_score, max_score: $max_score) { 
                    data {
                        id
                        nation_name
                        leader_name
                        score
                        population
                        soldiers
                        tanks
                        aircraft
                        ships
                        beige_turns
                        alliance {
                            id
                            name
                            rank
                        }
                        cities {
                            infrastructure
                        }
                        projects
                        wars {
                            id
                            defender {
                                id
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "first": 500,
                "page": page,
                "min_score": min_score,
                "max_score": max_score
            }
            
            try:
                async with session.post(
                    "https://api.politicsandwar.com/graphql",
                    json={"query": query, "variables": variables},
                    params={"api_key": api_key},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if "errors" in data:
                        error(f"API Error in GET_NATIONS_IN_RANGE: {data['errors']}", tag="RAID")
                        return None
                        
                    nations = data.get("data", {}).get("nations", {}).get("data", [])
                    if not nations:  # No more nations to fetch
                        break
                        
                    all_nations.extend(nations)
                    info(f"Fetched page {page}: {len(nations)} nations in range (total: {len(all_nations)})", tag="RAID")
                    page += 1
                    
                    # Add a small delay between requests to avoid rate limiting
                    await asyncio.sleep(0.3)
                    
            except asyncio.TimeoutError:
                error("Timeout while fetching nations in range", tag="RAID")
                return None
            except aiohttp.ClientError as e:
                error(f"Request error while fetching nations in range: {e}", tag="RAID")
                return None
            except Exception as e:
                error(f"Unexpected error in GET_NATIONS_IN_RANGE: {e}", tag="RAID")
                return None
    
    info(f"Finished fetching nations in range: {len(all_nations)} total", tag="RAID")
    return all_nations if all_nations else None

async def GET_WAR_ATTACKS_FOR_NATIONS(nation_ids: List[str], api_key: str, days_ago: int = 14) -> Dict:
    """Get war attacks for specific nations from the past N days."""
    import aiohttp
    import asyncio
    from datetime import datetime, timezone, timedelta
    
    if not nation_ids:
        return {}
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_ago)
    
    info(f"Fetching war attacks for {len(nation_ids)} nations from last {days_ago} days...", tag="WAR_ATTACKS")
    
    all_attacks = {}
    
    try:
        async with aiohttp.ClientSession() as session:
            # Process nations in batches to avoid huge queries
            batch_size = 50
            for i in range(0, len(nation_ids), batch_size):
                batch = nation_ids[i:i + batch_size]
                
                query = """
                query GetWarAttacks($nation_ids: [ID!]!, $after: DateTime!, $before: DateTime!) {
                    warAttacks(nation_id: $nation_ids, after: $after, before: $before, first: 1000) {
                        data {
                            id
                            date
                            att_id
                            def_id
                            victor
                            success
                            money_looted
                            coal_looted
                            oil_looted
                            uranium_looted
                            iron_looted
                            bauxite_looted
                            lead_looted
                            gasoline_looted
                            munitions_looted
                            steel_looted
                            aluminum_looted
                            food_looted
                        }
                    }
                }
                """
                
                variables = {
                    "nation_ids": batch,
                    "after": start_date.isoformat(),
                    "before": end_date.isoformat()
                }
                
                payload = {
                    "query": query,
                    "variables": variables
                }
                
                try:
                    async with session.post(
                        f"https://api.politicsandwar.com/graphql?api_key={api_key}",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if "errors" in data:
                                error(f"GraphQL errors in war attacks: {data['errors']}", tag="WAR_ATTACKS")
                                continue
                            
                            attacks = data.get("data", {}).get("warAttacks", {}).get("data", [])
                            
                            # Group attacks by defender ID
                            for attack in attacks:
                                def_id = attack.get('def_id')
                                if def_id:
                                    if def_id not in all_attacks:
                                        all_attacks[def_id] = []
                                    all_attacks[def_id].append(attack)
                            
                            info(f"Fetched {len(attacks)} war attacks for batch {i//batch_size + 1}", tag="WAR_ATTACKS")
                        else:
                            error(f"HTTP {response.status} while fetching war attacks for batch {i//batch_size + 1}", tag="WAR_ATTACKS")
                except Exception as batch_error:
                    error(f"Error in war attacks batch {i//batch_size + 1}: {batch_error}", tag="WAR_ATTACKS")
                    continue
                
                # Add delay between batches
                await asyncio.sleep(1)
                
    except Exception as e:
        error(f"Error fetching war attacks: {e}", tag="WAR_ATTACKS")
        return {}
    
    info(f"Retrieved war attacks for {len(all_attacks)} nations", tag="WAR_ATTACKS")
    return all_attacks