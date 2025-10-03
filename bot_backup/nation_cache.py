import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from bot.handler import info, error, warning

class NationCache:
    """Cache system for nation data to avoid API rate limiting."""
    
    def __init__(self, cache_file: str = "data/nations_cache.json", api_key: str = None):
        self.cache_file = cache_file
        self.data = {}
        self.last_update = None
        self.api_key = api_key
        self.update_interval = 5 * 60  # 5 minutes in seconds
        
    def load_cache(self) -> bool:
        """Load cached data from JSON file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.data = cache_data.get('data', {})
                    self.last_update = cache_data.get('last_update')
                    info(f"Loaded nation cache with {len(self.data)} nations", tag="NATION_CACHE")
                    return True
            return False
        except Exception as e:
            error(f"Error loading nation cache: {e}", tag="NATION_CACHE")
            return False
    
    def save_cache(self) -> bool:
        """Save data to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            cache_data = {
                "data": self.data,
                "last_update": self.last_update
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            info(f"Saved nation cache with {len(self.data)} nations", tag="NATION_CACHE")
            return True
        except Exception as e:
            error(f"Error saving nation cache: {e}", tag="NATION_CACHE")
            return False
    
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid (within 30 minutes)."""
        if not self.last_update:
            return False
        
        try:
            last_update_time = datetime.fromisoformat(self.last_update.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            time_diff = (now - last_update_time).total_seconds()
            return time_diff < self.update_interval
        except Exception as e:
            error(f"Error checking cache validity: {e}", tag="NATION_CACHE")
            return False
    
    async def update_cache(self, progress_callback=None) -> bool:
        """Update the nation cache with fresh data from API."""
        try:
            info("Starting nation cache update...", tag="NATION_CACHE")
            
            if progress_callback:
                await progress_callback("🔄 **Updating Nation Cache:** Fetching nation data from API...")
            
            # Get all nations from CSV cache first for basic data
            from bot.csv_cache import get_cache
            csv_cache = get_cache()
            all_nations = csv_cache.get_nations()
            
            if not all_nations:
                error("No nations data available from CSV cache", tag="NATION_CACHE")
                return False
            
            # Process nations in batches to avoid overwhelming the API
            batch_size = 50
            total_nations = len(all_nations)
            processed = 0
            
            new_data = {}
            
            async with aiohttp.ClientSession() as session:
                for i in range(0, total_nations, batch_size):
                    batch = all_nations[i:i + batch_size]
                    
                    if progress_callback:
                        await progress_callback(f"🔄 **Processing Batch:** {processed + 1}-{min(processed + batch_size, total_nations)} of {total_nations} nations")
                    
                    # Process batch concurrently
                    tasks = []
                    for nation in batch:
                        nation_id = nation.get('nation_id') or nation.get('﻿nation_id')
                        if nation_id:
                            tasks.append(self._fetch_nation_data(session, nation_id, nation))
                    
                    # Wait for all tasks in this batch
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for result in batch_results:
                        if isinstance(result, Exception):
                            error(f"Error fetching nation data: {result}", tag="NATION_CACHE")
                            continue
                        
                        if result:
                            nation_id = result['nation_id']
                            new_data[nation_id] = result
                    
                    processed += len(batch)
                    
                    # Add delay between batches to respect rate limits
                    await asyncio.sleep(1)
            
            # Update cache data
            self.data = new_data
            self.last_update = datetime.now(timezone.utc).isoformat()
            
            # Save to file
            if self.save_cache():
                info(f"Nation cache updated successfully with {len(self.data)} nations", tag="NATION_CACHE")
                if progress_callback:
                    await progress_callback(f"✅ **Cache Updated:** Successfully cached {len(self.data)} nations")
                return True
            else:
                error("Failed to save nation cache", tag="NATION_CACHE")
                return False
                
        except Exception as e:
            error(f"Error updating nation cache: {e}", tag="NATION_CACHE")
            if progress_callback:
                await progress_callback(f"❌ **Error:** Failed to update cache: {str(e)}")
            return False
    
    async def _fetch_nation_data(self, session: aiohttp.ClientSession, nation_id: int, csv_nation: dict) -> Optional[Dict]:
        """Fetch detailed nation data from API."""
        try:
            query = f"""
            {{
                nations(id: {nation_id}) {{
                    data {{
                        id
                        nation_name
                        leader_name
                        score
                        vmode
                        beige_turns
                        defensive_wars
                        soldiers
                        tanks
                        aircraft
                        ships
                        alliance {{
                            id
                            name
                            rank
                        }}
                        cities {{
                            id
                            name
                            infrastructure
                            land
                            oil_power_plants
                            coal_power_plants
                            nuclear_power_plants
                            wind_power_plants
                            coal_mines
                            iron_mines
                            uranium_mines
                            oil_wells
                            bauxite_mines
                            lead_mines
                            farms
                            oil_refineries
                            steel_mills
                            aluminum_refineries
                            munitions_factories
                            police_stations
                            hospitals
                            recycling_centers
                            subways
                            supermarkets
                            banks
                            shopping_malls
                            stadiums
                            barracks
                            factories
                            hangars
                            drydocks
                        }}
                    }}
                }}
            }}
            """
            
            async with session.post(
                "https://api.politicsandwar.com/graphql",
                json={"query": query},
                params={"api_key": self.api_key},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "errors" in data:
                        error(f"GraphQL error for nation {nation_id}: {data['errors']}", tag="NATION_CACHE")
                        return None
                    
                    nations = data.get("data", {}).get("nations", {}).get("data", [])
                    if nations:
                        nation_data = nations[0]
                        # Add CSV data as fallback
                        nation_data['csv_data'] = csv_nation
                        return nation_data
                    
                elif response.status == 429:
                    warning(f"Rate limited for nation {nation_id}, skipping", tag="NATION_CACHE")
                    return None
                else:
                    error(f"HTTP {response.status} for nation {nation_id}", tag="NATION_CACHE")
                    return None
                    
        except asyncio.TimeoutError:
            error(f"Timeout fetching nation {nation_id}", tag="NATION_CACHE")
            return None
        except Exception as e:
            error(f"Error fetching nation {nation_id}: {e}", tag="NATION_CACHE")
            return None
    
    def get_nation_data(self, nation_id: int) -> Optional[Dict]:
        """Get cached nation data."""
        return self.data.get(str(nation_id)) or self.data.get(nation_id)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache."""
        return {
            "nations_count": len(self.data),
            "last_update": self.last_update,
            "is_valid": self.is_cache_valid(),
            "file_size": os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0
        }
    
    def get_nations_in_score_range(self, min_score: float, max_score: float) -> List[Dict]:
        """Get nations within a specific score range."""
        results = []
        for nation_data in self.data.values():
            score = nation_data.get('score', 0)
            if min_score <= score <= max_score:
                results.append(nation_data)
        return results

# Global cache instance
_cache_instance = None

def get_nation_cache() -> NationCache:
    """Get the global nation cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = NationCache()
        _cache_instance.load_cache()
    return _cache_instance

def init_nation_cache(api_key: str = None):
    """Initialize the nation cache system."""
    global _cache_instance
    _cache_instance = NationCache(api_key=api_key)
    _cache_instance.load_cache()
    info("Nation cache system initialized", tag="NATION_CACHE")