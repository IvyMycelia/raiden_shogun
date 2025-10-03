"""
Environment variables and configuration settings.
"""

import os
from typing import Dict, List

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove export prefix if present
                    key = key.replace('export ', '')
                    os.environ[key] = value

# Load .env file
load_env_file()

class Config:
    """Configuration management for the bot."""
    
    def __init__(self):
        # Discord Bot Configuration
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        self.GUILD_ID = int(os.getenv('GUILD_ID', '0'))
        self.ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))
        
        # Politics and War API Configuration
        self.ALLIANCE_ID = int(os.getenv('ALLIANCE_ID', '13033'))
        self.PERSONAL_NATION_ID = int(os.getenv('PERSONAL_NATION_ID', '590508'))
        
        # API Key Pool Configuration
        self.API_KEYS = {
            "everything_scope": [
                "1adc0368729abdbba56c",  # Everything Scope - Primary
                "29cc5d1b8aca3b02fe75"   # Everything Scope - Secondary
            ],
            "alliance_scope": [
                "39c40d62a96e5e2fff86",  # Alliance Scope - Primary
                "ada85c10c9fe0944cbb1",  # Alliance Scope - Secondary
                "8986a7e3c790d574a561",  # Alliance Scope - Tertiary
                "631fef9d485f7090dbfa"   # Alliance Scope - Quaternary
            ],
            "personal_scope": [
                "d26fe3dacf8ea09032b0"   # Personal (Nation 590508 only)
            ],
            "messaging_scope": [
                "2457ef98256e4256bd81"   # Send messages to nations
            ]
        }
        
        # Cache Configuration
        self.CACHE_UPDATE_INTERVAL = 300  # 5 minutes
        self.CACHE_DIR = "data/cache"
        self.JSON_DIR = "data"
        
        # Rate Limiting Configuration
        self.API_RATE_LIMIT = 1000  # calls per hour per key
        self.API_DELAY = 0.5  # seconds between calls
        
        # Pagination Configuration
        self.ITEMS_PER_PAGE = 9
        self.PAGINATION_TIMEOUT = 300  # 5 minutes
        
        # Audit Configuration
        self.MMR_REQUIREMENTS = {
            "Raider": {
                "barracks": 5,
                "factory": 0,
                "hangar": 5,
                "drydock": 0
            },
            "Whale": {
                "barracks": 0,
                "factory": 2,
                "hangar": 5,
                "drydock": 0
            }
        }
        
        # Resource Thresholds for Deposit Audit (in thousands)
        self.DEPOSIT_THRESHOLDS = {
            "money": 100000,  # $100M
            "coal": 1000,     # 1M coal
            "oil": 1000,      # 1M oil
            "uranium": 100,   # 100k uranium
            "iron": 1000,     # 1M iron
            "bauxite": 1000,  # 1M bauxite
            "lead": 1000,     # 1M lead
            "gasoline": 100,  # 100k gasoline
            "munitions": 100, # 100k munitions
            "steel": 100,     # 100k steel
            "aluminum": 100,  # 100k aluminum
            "food": 1000,     # 1M food
        }
        
        # Raid Configuration
        self.RAID_SCORE_RANGE = 0.25  # 25% above/below user score
        self.MIN_LOOT_POTENTIAL = 100000  # $100k minimum
        self.MAX_DEFENSIVE_WARS = 3
        self.TOP_ALLIANCE_RANK = 60
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        if not self.GUILD_ID:
            raise ValueError("GUILD_ID environment variable is required")
        
        if not self.ADMIN_USER_ID:
            raise ValueError("ADMIN_USER_ID environment variable is required")
    
    def get_api_key(self, scope: str) -> str:
        """Get a random API key for the specified scope."""
        if scope not in self.API_KEYS:
            raise ValueError(f"Invalid scope: {scope}")
        
        import random
        return random.choice(self.API_KEYS[scope])
    
    def get_all_api_keys(self) -> List[str]:
        """Get all API keys from all scopes."""
        all_keys = []
        for keys in self.API_KEYS.values():
            all_keys.extend(keys)
        return all_keys

# Global config instance
config = Config()
