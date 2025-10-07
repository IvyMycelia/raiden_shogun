"""
Cache service for data management.
"""

import asyncio
import json
import os
import csv
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from api.politics_war_api import api

class CacheService:
    """Service for cache management and data synchronization."""
    
    def __init__(self):
        self.cache_dir = config.CACHE_DIR
        self.json_dir = config.JSON_DIR
        self.cache_file = os.path.join(self.json_dir, "cache.json")
        self.registrations_file = os.path.join(self.json_dir, "registrations.json")
        
        # Ensure directories exist
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)
    
    async def download_csv_data(self) -> bool:
        """Download CSV data from Politics and War."""
        try:
            # Download all CSV files
            nations_csv = await api.download_csv_data("nations", "everything_scope")
            cities_csv = await api.download_csv_data("cities", "everything_scope")
            wars_csv = await api.download_csv_data("wars", "everything_scope")
            alliances_csv = await api.download_csv_data("alliances", "alliance_scope")
            
            if not all([nations_csv, cities_csv, wars_csv, alliances_csv]):
                return False
            
            # Parse CSV data
            nations_data = self._parse_csv(nations_csv)
            cities_data = self._parse_csv(cities_csv)
            wars_data = self._parse_csv(wars_csv)
            alliances_data = self._parse_csv(alliances_csv)
            
            # Save to cache
            cache_data = {
                'last_update': datetime.now(timezone.utc).isoformat(),
                'data': {
                    'nations': nations_data,
                    'cities': cities_data,
                    'wars': wars_data,
                    'alliances': alliances_data
                }
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error downloading CSV data: {e}")
            return False
    
    def _parse_csv(self, csv_content: str) -> List[Dict]:
        """Parse CSV content to list of dictionaries."""
        if not csv_content:
            return []
        
        try:
            reader = csv.DictReader(csv_content.splitlines())
            return list(reader)
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            return []
    
    def load_cache(self) -> Dict[str, Any]:
        """Load cached data from JSON file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}
    
    def get_nations(self) -> List[Dict]:
        """Get nations data from cache."""
        cache_data = self.load_cache()
        return cache_data.get('data', {}).get('nations', [])
    
    def get_cities(self) -> List[Dict]:
        """Get cities data from cache."""
        cache_data = self.load_cache()
        return cache_data.get('data', {}).get('cities', [])
    
    def get_wars(self) -> List[Dict]:
        """Get wars data from cache."""
        cache_data = self.load_cache()
        return cache_data.get('data', {}).get('wars', [])
    
    def get_alliances(self) -> List[Dict]:
        """Get alliances data from cache."""
        cache_data = self.load_cache()
        return cache_data.get('data', {}).get('alliances', [])
    
    def get_alliance_by_id(self, alliance_id: str) -> Optional[Dict]:
        """Get alliance data by ID."""
        alliances = self.get_alliances()
        for alliance in alliances:
            if str(alliance.get('id', '')) == str(alliance_id):
                return alliance
        return None
    
    def is_cache_valid(self) -> bool:
        """Check if cache is valid and not expired."""
        cache_data = self.load_cache()
        if not cache_data:
            return False
        
        last_update_str = cache_data.get('last_update')
        if not last_update_str:
            return False
        
        try:
            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            return (current_time - last_update).total_seconds() < config.CACHE_UPDATE_INTERVAL
        except ValueError:
            return False
    
    def load_registrations(self) -> Dict:
        """Load registered nations data."""
        try:
            if os.path.exists(self.registrations_file):
                with open(self.registrations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading registrations: {e}")
            return {}
    
    def save_registrations(self, registrations: Dict):
        """Save registered nations data."""
        try:
            with open(self.registrations_file, 'w', encoding='utf-8') as f:
                json.dump(registrations, f, indent=2)
        except Exception as e:
            print(f"Error saving registrations: {e}")
    
    def get_user_nation(self, discord_id: str) -> Optional[int]:
        """Get user's nation ID from registrations."""
        registrations = self.load_registrations()
        user_data = registrations.get(discord_id)
        if user_data:
            return user_data.get('nation_id')
        return None
    
    def register_user(self, discord_id: str, nation_id: int, discord_name: str, nation_name: str):
        """Register a user with their nation."""
        registrations = self.load_registrations()
        registrations[discord_id] = {
            'nation_id': nation_id,
            'discord_name': discord_name,  # Keep for compatibility
            'discord_username': discord_name,  # Exact username
            'nation_name': nation_name,
            'registered_at': datetime.now(timezone.utc).isoformat()
        }
        self.save_registrations(registrations)
    
    def get_discord_username(self, nation_id: str) -> str:
        """Get Discord username from nation ID."""
        registrations = self.load_registrations()
        for discord_id, data in registrations.items():
            if str(data.get('nation_id')) == str(nation_id):
                # Prefer discord_username (exact username) over discord_name (display name)
                return data.get('discord_username', data.get('discord_name', 'N/A'))
        return 'N/A'
