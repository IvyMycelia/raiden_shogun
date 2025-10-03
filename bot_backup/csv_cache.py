import asyncio
import aiohttp
import csv
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from io import StringIO
import hashlib

from bot.handler import info, error, warning

class CSVCache:
    """Cache system for downloading and parsing CSV data from Politics and War."""
    
    def __init__(self, cache_file: str = "data/csv_cache.json", api_key: str = None):
        self.cache_file = cache_file
        self.data = {"wars": [], "cities": [], "nations": [], "alliances": []}
        self.last_update = None
        self.api_key = api_key
        self.api_base = "https://api.politicsandwar.com/graphql"
        self.csv_base_urls = {
            "alliances": "https://politicsandwar.com/data/alliances",
            "nations": "https://politicsandwar.com/data/nations", 
            "cities": "https://politicsandwar.com/data/cities",
            "wars": "https://politicsandwar.com/data/wars"
        }
        
    def load_cache(self) -> bool:
        """Load cached data from JSON file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.data = cache_data.get('data', {"wars": [], "cities": [], "nations": []})
                    self.last_update = cache_data.get('last_update')
                    info(f"Loaded cache with {len(self.data['wars'])} wars, {len(self.data['cities'])} cities, {len(self.data['nations'])} nations", tag="CSV_CACHE")
                    return True
            return False
        except Exception as e:
            error(f"Error loading cache: {e}", tag="CSV_CACHE")
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
            info(f"Saved cache with {len(self.data['wars'])} wars, {len(self.data['cities'])} cities, {len(self.data['nations'])} nations", tag="CSV_CACHE")
            return True
        except Exception as e:
            error(f"Error saving cache: {e}", tag="CSV_CACHE")
            return False
    
    def get_data_hash(self) -> str:
        """Get hash of current data to detect changes."""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def download_csv_data(self, progress_callback=None) -> bool:
        """Download and parse all CSV data from Politics and War."""
        try:
            info("Starting CSV data download from Politics and War...", tag="CSV_CACHE")
            
            # Store original data hash to detect changes
            original_hash = self.get_data_hash()
            
            async with aiohttp.ClientSession() as session:
                # Download alliances data first (needed for filtering)
                if progress_callback:
                    await progress_callback("🔄 **Step 1/4:** Downloading alliances data...")
                
                alliances_data = await self._download_latest_csv(session, "alliances", progress_callback)
                if alliances_data:
                    self.data["alliances"] = alliances_data
                    info(f"Downloaded {len(alliances_data)} alliances", tag="CSV_CACHE")
                else:
                    warning("Failed to download alliances data", tag="CSV_CACHE")
                    self.data["alliances"] = []
                
                # Download nations data
                if progress_callback:
                    await progress_callback("🔄 **Step 2/4:** Downloading nations data...")
                
                nations_data = await self._download_latest_csv(session, "nations", progress_callback)
                if nations_data:
                    self.data["nations"] = nations_data
                    info(f"Downloaded {len(nations_data)} nations", tag="CSV_CACHE")
                else:
                    error("Failed to download nations data", tag="CSV_CACHE")
                    return False
                
                # Download cities data
                if progress_callback:
                    await progress_callback("🔄 **Step 3/4:** Downloading cities data...")
                
                cities_data = await self._download_latest_csv(session, "cities", progress_callback)
                if cities_data:
                    self.data["cities"] = cities_data
                    info(f"Downloaded {len(cities_data)} cities", tag="CSV_CACHE")
                else:
                    warning("Failed to download cities data, continuing with empty cities", tag="CSV_CACHE")
                    self.data["cities"] = []
                
                # Download wars data
                if progress_callback:
                    await progress_callback("🔄 **Step 4/4:** Downloading wars data...")
                
                wars_data = await self._download_latest_csv(session, "wars", progress_callback)
                if wars_data:
                    self.data["wars"] = wars_data
                    info(f"Downloaded {len(wars_data)} wars", tag="CSV_CACHE")
                else:
                    warning("Failed to download wars data, continuing with empty wars", tag="CSV_CACHE")
                    self.data["wars"] = []
            
            # Check if data actually changed
            new_hash = self.get_data_hash()
            if new_hash == original_hash:
                info("No changes detected in data", tag="CSV_CACHE")
                if progress_callback:
                    await progress_callback("✅ **Complete:** No changes detected, cache up to date")
                return True
            
            # Update timestamp
            self.last_update = datetime.now(timezone.utc).isoformat()
            
            # Save the updated data
            if self.save_cache():
                info("Cache updated successfully", tag="CSV_CACHE")
                if progress_callback:
                    await progress_callback("✅ **Complete:** Cache updated successfully!")
                return True
            else:
                error("Failed to save cache", tag="CSV_CACHE")
                if progress_callback:
                    await progress_callback("❌ **Error:** Failed to save cache")
                return False
                
        except Exception as e:
            error(f"Error in download_csv_data: {e}", tag="CSV_CACHE")
            if progress_callback:
                await progress_callback(f"❌ **Error:** {str(e)}")
            return False
    
    async def _download_latest_csv(self, session: aiohttp.ClientSession, data_type: str, progress_callback=None) -> List[Dict[str, Any]]:
        """Download the latest CSV file for a data type."""
        try:
            # Get today's date for the CSV filename
            today = datetime.now().strftime("%Y-%m-%d")
            csv_filename = f"{data_type}-{today}.csv.zip"
            csv_url = f"{self.csv_base_urls[data_type]}/{csv_filename}"
            
            if progress_callback:
                await progress_callback(f"Downloading {data_type} CSV from {csv_url}...")
            
            # Try to download today's file first
            async with session.get(csv_url) as response:
                if response.status == 200:
                    csv_content = await response.read()
                    return await self._parse_zip_csv(csv_content, data_type)
                else:
                    # If today's file doesn't exist, try yesterday's
                    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                    csv_filename = f"{data_type}-{yesterday}.csv.zip"
                    csv_url = f"{self.csv_base_urls[data_type]}/{csv_filename}"
                    
                    if progress_callback:
                        await progress_callback(f"Trying yesterday's {data_type} CSV...")
                    
                    async with session.get(csv_url) as response2:
                        if response2.status == 200:
                            csv_content = await response2.read()
                            return await self._parse_zip_csv(csv_content, data_type)
                        else:
                            error(f"Failed to download {data_type} CSV: HTTP {response2.status}", tag="CSV_CACHE")
                            return []
            
        except Exception as e:
            error(f"Error downloading {data_type} CSV: {e}", tag="CSV_CACHE")
            return []
    
    async def _parse_zip_csv(self, zip_content: bytes, data_type: str) -> List[Dict[str, Any]]:
        """Parse CSV content from a ZIP file."""
        try:
            import zipfile
            from io import BytesIO
            
            with zipfile.ZipFile(BytesIO(zip_content)) as zip_file:
                # Find the CSV file in the ZIP
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
                if not csv_files:
                    error(f"No CSV file found in {data_type} ZIP", tag="CSV_CACHE")
                    return []
                
                # Read the first CSV file
                csv_filename = csv_files[0]
                with zip_file.open(csv_filename) as csv_file:
                    csv_content = csv_file.read().decode('utf-8')
                    return self._parse_csv(csv_content)
                    
        except Exception as e:
            error(f"Error parsing {data_type} ZIP CSV: {e}", tag="CSV_CACHE")
            return []
    
    def _parse_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse CSV content into list of dictionaries."""
        try:
            csv_reader = csv.DictReader(StringIO(csv_content))
            data = []
            for row in csv_reader:
                # Convert numeric strings to appropriate types
                processed_row = {}
                for key, value in row.items():
                    if value is None or value == '':
                        processed_row[key] = None
                    elif value.isdigit():
                        processed_row[key] = int(value)
                    elif value.replace('.', '').replace('-', '').isdigit():
                        try:
                            processed_row[key] = float(value)
                        except ValueError:
                            processed_row[key] = value
                    else:
                        processed_row[key] = value
                data.append(processed_row)
            return data
        except Exception as e:
            error(f"Error parsing CSV: {e}", tag="CSV_CACHE")
            return []
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache."""
        return {
            "wars_count": len(self.data.get("wars", [])),
            "cities_count": len(self.data.get("cities", [])),
            "nations_count": len(self.data.get("nations", [])),
            "alliances_count": len(self.data.get("alliances", [])),
            "last_update": self.last_update,
            "file_size": os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0
        }
    
    def get_nations(self) -> List[Dict[str, Any]]:
        """Get nations data."""
        return self.data.get("nations", [])
    
    def get_cities(self) -> List[Dict[str, Any]]:
        """Get cities data."""
        return self.data.get("cities", [])
    
    def get_wars(self) -> List[Dict[str, Any]]:
        """Get wars data."""
        return self.data.get("wars", [])
    
    def find_nation_by_id(self, nation_id: int) -> Optional[Dict[str, Any]]:
        """Find a nation by ID."""
        for nation in self.data.get("nations", []):
            if nation.get("id") == nation_id:
                return nation
        return None
    
    def get_cities_for_nation(self, nation_id: int) -> List[Dict[str, Any]]:
        """Get all cities for a specific nation."""
        cities = []
        for city in self.data.get("cities", []):
            if city.get("nation_id") == nation_id:
                cities.append(city)
        return cities
    
    def get_wars_for_nation(self, nation_id: int) -> List[Dict[str, Any]]:
        """Get all wars for a specific nation (as attacker or defender)."""
        wars = []
        for war in self.data.get("wars", []):
            if (war.get("attacker_id") == nation_id or 
                war.get("defender_id") == nation_id):
                wars.append(war)
        return wars
    
    def get_alliances(self) -> List[Dict[str, Any]]:
        """Get alliances data."""
        return self.data.get("alliances", [])
    
    def get_alliance_by_id(self, alliance_id: str) -> Optional[Dict[str, Any]]:
        """Get a single alliance's data by ID."""
        for alliance in self.data.get("alliances", []):
            if str(alliance.get("alliance_id", "")) == str(alliance_id):
                return alliance
        return None
    
    def get_top_60_alliances(self) -> set:
        """Get set of top 60 alliance IDs."""
        top_alliances = set()
        for alliance in self.data.get("alliances", []):
            if alliance.get("rank", 999) <= 60:
                top_alliances.add(alliance.get("id"))
        return top_alliances

# Global cache instance
_cache_instance = None

def get_cache() -> CSVCache:
    """Get the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CSVCache()
        _cache_instance.load_cache()
    return _cache_instance

def init_cache(api_key: str = None):
    """Initialize the cache system."""
    global _cache_instance
    _cache_instance = CSVCache(api_key=api_key)
    _cache_instance.load_cache()
    info("CSV cache system initialized", tag="CSV_CACHE")
