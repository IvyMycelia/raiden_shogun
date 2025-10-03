import aiohttp
import zipfile
import csv
import io
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger('raiden_shogun')

class CSVParser:
    """Parser for Politics and War CSV data."""
    
    def parse_nations_csv(self, csv_content: str) -> Dict[str, Dict[str, Any]]:
        """Parse nations CSV data."""
        nations = {}
        
        # Remove BOM if present
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in csv_reader:
            nation_id = row.get('nation_id', '')
            if nation_id:
                # Handle vmode (vm_turns > 0 means in vacation mode)
                vm_turns = int(row.get('vm_turns', 0))
                vmode = 1 if vm_turns > 0 else 0
                
                # Handle beige turns
                beige_turns = int(row.get('beige_turns_remaining', 0))
                
                nations[nation_id] = {
                    'id': int(nation_id),
                    'nation_name': row.get('nation_name', ''),
                    'leader_name': row.get('leader_name', ''),
                    'score': float(row.get('score', 0)),
                    'cities': int(row.get('cities', 0)),
                    'alliance_id': int(row.get('alliance_id', 0)) if row.get('alliance_id') and row.get('alliance_id') != 'None' else None,
                    'alliance_name': row.get('alliance', 'None') if row.get('alliance') and row.get('alliance') != 'None' else 'None',
                    'alliance_rank': 999,  # Not available in this CSV
                    'color': row.get('color', 'gray'),
                    'vmode': vmode,
                    'beige_turns': beige_turns,
                    'last_active': row.get('date_created', ''),
                    'soldiers': int(row.get('soldiers', 0)),
                    'tanks': int(row.get('tanks', 0)),
                    'aircraft': int(row.get('aircraft', 0)),
                    'ships': int(row.get('ships', 0)),
                    'spies': int(row.get('spies', 0)),
                    'missiles': int(row.get('missiles', 0)),
                    'nukes': int(row.get('nukes', 0)),
                    'money': 0,  # Not available in this CSV
                    'coal': 0,   # Not available in this CSV
                    'oil': 0,    # Not available in this CSV
                    'uranium': 0, # Not available in this CSV
                    'iron': 0,   # Not available in this CSV
                    'bauxite': 0, # Not available in this CSV
                    'lead': 0,   # Not available in this CSV
                    'gasoline': 0, # Not available in this CSV
                    'munitions': 0, # Not available in this CSV
                    'steel': 0,  # Not available in this CSV
                    'aluminum': 0, # Not available in this CSV
                    'food': 0,   # Not available in this CSV
                    'credits': 0  # Not available in this CSV
                }
        
        return nations
    
    def parse_cities_csv(self, csv_content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse cities CSV data."""
        cities_by_nation = {}
        
        # Remove BOM if present
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in csv_reader:
            nation_id = row.get('nation_id', '')
            if nation_id:
                if nation_id not in cities_by_nation:
                    cities_by_nation[nation_id] = []
                
                cities_by_nation[nation_id].append({
                    'id': int(row.get('city_id', 0)),
                    'name': row.get('name', ''),
                    'nation_id': int(nation_id),
                    'infrastructure': float(row.get('infrastructure', 0)),
                    'land': float(row.get('land', 0)),
                    'powered': int(row.get('powered', 0)) == 1,
                    'nuclear_power': int(row.get('nuclear_power_plants', 0)) > 0,
                    'oil_power': int(row.get('oil_power_plants', 0)) > 0,
                    'coal_power': int(row.get('coal_power_plants', 0)) > 0,
                    'wind_power': int(row.get('wind_power_plants', 0)) > 0,
                    'date': row.get('date_created', '')
                })
        
        return cities_by_nation
    
    def parse_alliances_csv(self, csv_content: str) -> Dict[str, Dict[str, Any]]:
        """Parse alliances CSV data."""
        alliances = {}
        
        # Remove BOM if present
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in csv_reader:
            alliance_id = row.get('alliance_id', '')
            if alliance_id:
                alliances[alliance_id] = {
                    'id': int(alliance_id),
                    'name': row.get('name', ''),
                    'rank': 999,  # Not available in this CSV
                    'score': float(row.get('score', 0)),
                    'cities': 0,  # Not available in this CSV
                    'members': 0  # Not available in this CSV
                }
        
        return alliances
    
    def parse_wars_csv(self, csv_content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse wars CSV data."""
        wars_by_nation = {}
        
        # Remove BOM if present
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row in csv_reader:
            attacker_id = row.get('aggressor_nation_id', '')
            defender_id = row.get('defender_nation_id', '')
            
            war_data = {
                'id': int(row.get('war_id', 0)),
                'attacker_id': int(attacker_id) if attacker_id else 0,
                'defender_id': int(defender_id) if defender_id else 0,
                'war_type': row.get('war_type', ''),
                'reason': row.get('reason', ''),
                'turns_left': int(row.get('turns_left', 0)),
                'groundcontrol': row.get('ground_control', ''),
                'aircontrol': row.get('air_superiority', ''),
                'navalcontrol': row.get('blockade', '')
            }
            
            # Add to both attacker and defender
            if attacker_id:
                if attacker_id not in wars_by_nation:
                    wars_by_nation[attacker_id] = []
                wars_by_nation[attacker_id].append(war_data)
            
            if defender_id:
                if defender_id not in wars_by_nation:
                    wars_by_nation[defender_id] = []
                wars_by_nation[defender_id].append(war_data)
        
        return wars_by_nation

class RaidCacheService:
    """Service for managing raid-related cache data from CSV files."""
    
    def __init__(self):
        self.cache_dir = "data/raid_cache"
        self.parser = CSVParser()
        self.session = None
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def update_raid_cache(self, date: str = None) -> bool:
        """Update all raid-related cache data."""
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Starting raid cache update for date: {date}")
            
            # Try current date first, then previous day if not available
            dates_to_try = [date]
            if date == datetime.now().strftime("%Y-%m-%d"):
                # If trying today's date, also try yesterday
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                dates_to_try.append(yesterday)
            
            nations_data = None
            cities_data = None
            alliances_data = None
            wars_data = None
            
            for i, try_date in enumerate(dates_to_try):
                if i == 0:
                    logger.info(f"Trying current date: {try_date}")
                else:
                    logger.info(f"Current date failed, trying fallback date: {try_date}")
                
                if nations_data is None:
                    nations_data = await self.update_nations_cache(try_date)
                if cities_data is None:
                    cities_data = await self.update_cities_cache(try_date)
                if alliances_data is None:
                    alliances_data = await self.update_alliances_cache(try_date)
                if wars_data is None:
                    wars_data = await self.update_wars_cache(try_date)
                
                # If we got all data, break
                if all([nations_data, cities_data, alliances_data, wars_data]):
                    logger.info(f"Successfully loaded all data from {try_date}")
                    break
            
            logger.info(f"Cache update results: nations={bool(nations_data)}, cities={bool(cities_data)}, alliances={bool(alliances_data)}, wars={bool(wars_data)}")
            
            if all([nations_data, cities_data, alliances_data, wars_data]):
                logger.info("✅ All cache components updated successfully")
                # Save combined cache
                combined_cache = {
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "date": date,
                    "nations": nations_data,
                    "cities": cities_data,
                    "alliances": alliances_data,
                    "wars": wars_data
                }
                
                cache_path = f"{self.cache_dir}/combined_cache.json"
                with open(cache_path, 'w') as f:
                    json.dump(combined_cache, f, indent=2)
                
                logger.info(f"Raid cache updated successfully for date {date}")
                return True
            else:
                logger.error("❌ Failed to update all cache components - no data available for current or fallback dates")
                return False
                
        except Exception as e:
            logger.error(f"Error updating raid cache: {e}")
            return False
    
    async def update_nations_cache(self, date: str) -> Optional[Dict]:
        """Update nations CSV data."""
        try:
            url = f"https://politicsandwar.com/data/nations/nations-{date}.csv.zip"
            logger.info(f"Downloading nations data from: {url}")
            
            response = await self.session.get(url)
            
            if response.status == 200:
                content = await response.read()
                
                # Extract and parse CSV
                with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                    csv_file = zip_file.namelist()[0]
                    csv_content = zip_file.read(csv_file).decode('utf-8')
                
                nations_data = self.parser.parse_nations_csv(csv_content)
                
                # Before overwriting, save current data as yesterday's data
                current_cache_path = f"{self.cache_dir}/nations.json"
                yesterday_cache_path = f"{self.cache_dir}/nations_yesterday.json"
                
                # If current cache exists, copy it to yesterday's cache
                if os.path.exists(current_cache_path):
                    try:
                        with open(current_cache_path, 'r') as f:
                            yesterday_data = json.load(f)
                        with open(yesterday_cache_path, 'w') as f:
                            json.dump(yesterday_data, f, indent=2)
                        logger.info(f"Saved yesterday's nations data: {len(yesterday_data)} nations")
                    except Exception as e:
                        logger.warning(f"Could not save yesterday's data: {e}")
                
                # Save new data as current cache
                with open(current_cache_path, 'w') as f:
                    json.dump(nations_data, f, indent=2)
                
                logger.info(f"Updated nations cache: {len(nations_data)} nations")
                return nations_data
            else:
                logger.warning(f"Nations data not available for {date} (status: {response.status}) - will try fallback date")
                return None
                
        except Exception as e:
            logger.error(f"Error updating nations cache: {e}")
            return None
    
    async def update_cities_cache(self, date: str) -> Optional[Dict]:
        """Update cities CSV data."""
        try:
            url = f"https://politicsandwar.com/data/cities/cities-{date}.csv.zip"
            logger.info(f"Downloading cities data from: {url}")
            
            response = await self.session.get(url)
            
            if response.status == 200:
                content = await response.read()
                
                # Extract and parse CSV
                with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                    csv_file = zip_file.namelist()[0]
                    csv_content = zip_file.read(csv_file).decode('utf-8')
                
                cities_data = self.parser.parse_cities_csv(csv_content)
                
                # Save individual cache (always overwrite the same file)
                cache_path = f"{self.cache_dir}/cities.json"
                with open(cache_path, 'w') as f:
                    json.dump(cities_data, f, indent=2)
                
                logger.info(f"Updated cities cache: {len(cities_data)} nations with cities")
                return cities_data
            else:
                logger.warning(f"Cities data not available for {date} (status: {response.status}) - will try fallback date")
                return None
                
        except Exception as e:
            logger.error(f"Error updating cities cache: {e}")
            return None
    
    async def update_alliances_cache(self, date: str) -> Optional[Dict]:
        """Update alliances CSV data."""
        try:
            url = f"https://politicsandwar.com/data/alliances/alliances-{date}.csv.zip"
            logger.info(f"Downloading alliances data from: {url}")
            
            response = await self.session.get(url)
            
            if response.status == 200:
                content = await response.read()
                
                # Extract and parse CSV
                with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                    csv_file = zip_file.namelist()[0]
                    csv_content = zip_file.read(csv_file).decode('utf-8')
                
                alliances_data = self.parser.parse_alliances_csv(csv_content)
                
                # Save individual cache (always overwrite the same file)
                cache_path = f"{self.cache_dir}/alliances.json"
                with open(cache_path, 'w') as f:
                    json.dump(alliances_data, f, indent=2)
                
                logger.info(f"Updated alliances cache: {len(alliances_data)} alliances")
                return alliances_data
            else:
                logger.warning(f"Alliances data not available for {date} (status: {response.status}) - will try fallback date")
                return None
                
        except Exception as e:
            logger.error(f"Error updating alliances cache: {e}")
            return None
    
    async def update_wars_cache(self, date: str) -> Optional[Dict]:
        """Update wars CSV data."""
        try:
            url = f"https://politicsandwar.com/data/wars/wars-{date}.csv.zip"
            logger.info(f"Downloading wars data from: {url}")
            
            response = await self.session.get(url)
            
            if response.status == 200:
                content = await response.read()
                
                # Extract and parse CSV
                with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                    csv_file = zip_file.namelist()[0]
                    csv_content = zip_file.read(csv_file).decode('utf-8')
                
                wars_data = self.parser.parse_wars_csv(csv_content)
                
                # Save individual cache (always overwrite the same file)
                cache_path = f"{self.cache_dir}/wars.json"
                with open(cache_path, 'w') as f:
                    json.dump(wars_data, f, indent=2)
                
                logger.info(f"Updated wars cache: {len(wars_data)} nations with wars")
                return wars_data
            else:
                logger.warning(f"Wars data not available for {date} (status: {response.status}) - will try fallback date")
                return None
                
        except Exception as e:
            logger.error(f"Error updating wars cache: {e}")
            return None
    
    def load_raid_cache(self) -> Optional[Dict]:
        """Load raid cache data from individual files."""
        try:
            cache_data = {}
            
            # Load nations
            nations_path = f"{self.cache_dir}/nations.json"
            if os.path.exists(nations_path):
                with open(nations_path, 'r') as f:
                    cache_data['nations'] = json.load(f)
            
            # Load cities
            cities_path = f"{self.cache_dir}/cities.json"
            if os.path.exists(cities_path):
                with open(cities_path, 'r') as f:
                    cache_data['cities'] = json.load(f)
            
            # Load alliances
            alliances_path = f"{self.cache_dir}/alliances.json"
            if os.path.exists(alliances_path):
                with open(alliances_path, 'r') as f:
                    cache_data['alliances'] = json.load(f)
            
            # Load wars
            wars_path = f"{self.cache_dir}/wars.json"
            if os.path.exists(wars_path):
                with open(wars_path, 'r') as f:
                    cache_data['wars'] = json.load(f)
            
            return cache_data
                
        except Exception as e:
            logger.error(f"Error loading raid cache: {e}")
            return None
    
    def load_yesterday_nations_cache(self) -> Optional[Dict]:
        """Load yesterday's nations cache data for comparison."""
        try:
            yesterday_path = f"{self.cache_dir}/nations_yesterday.json"
            if os.path.exists(yesterday_path):
                with open(yesterday_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("Yesterday's nations cache not found")
                return None
        except Exception as e:
            logger.error(f"Error loading yesterday's nations cache: {e}")
            return None
    
    def cleanup_old_cache(self, keep_days: int = 7):
        """Clean up old cache files."""
        try:
            import glob
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (keep_days * 24 * 60 * 60)
            
            # Find old cache files
            old_files = glob.glob(f"{self.cache_dir}/*.json")
            
            for file_path in old_files:
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old cache file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old cache: {e}")
