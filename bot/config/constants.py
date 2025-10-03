"""
Game constants and formulas for Politics and War.
"""

from typing import Dict

class GameConstants:
    """Constants and formulas for Politics and War calculations."""
    
    # Military Unit Costs (per turn)
    MILITARY_COSTS = {
        "soldiers": 1.88 / 12,      # per soldier per turn
        "tanks": 75 / 12,           # per tank per turn
        "aircraft": 750 / 12,       # per aircraft per turn
        "ships": 5062.5 / 12        # per ship per turn
    }
    
    # Building Upkeep Costs (per turn)
    BUILDING_COSTS = {
        "coal_power": 100,          # $100/turn
        "oil_power": 150,           # $150/turn
        "nuclear_power": 875,       # $875/turn
        "wind_power": 42,           # $42/turn
        "farm": 25,                 # $25/turn
        "uranium_mine": 417,        # $417/turn
        "iron_mine": 134,           # $134/turn
        "coal_mine": 34,            # $34/turn
        "oil_refinery": 334,        # $334/turn
        "steel_mill": 334,          # $334/turn
        "aluminum_refinery": 209,   # $209/turn
        "munitions_factory": 292,   # $292/turn
        "police_station": 63,       # $63/turn
        "hospital": 84,             # $84/turn
        "recycling_center": 209,    # $209/turn
        "subway": 271,              # $271/turn
        "supermarket": 50,          # $50/turn
        "bank": 150,                # $150/turn
        "shopping_mall": 450,       # $450/turn
        "stadium": 1013             # $1013/turn
    }
    
    # Military Capacity per Building
    CAPACITY_PER_BUILDING = {
        "barracks": 3000,    # soldiers per barracks
        "factory": 250,      # tanks per factory
        "hangar": 15,        # aircraft per hangar
        "drydock": 5         # ships per drydock
    }
    
    # Resource Consumption (per turn)
    RESOURCE_CONSUMPTION = {
        "coal_per_coal_power": 0.1,      # per coal power plant
        "coal_per_steel_mill": 0.1,      # per steel mill
        "oil_per_oil_power": 0.1,        # per oil power plant
        "oil_per_refinery": 0.5,         # per oil refinery
        "uranium_per_nuclear": 0.2,      # per nuclear power plant
        "iron_per_steel_mill": 0.75,     # per steel mill
        "bauxite_per_aluminum": 0.75,    # per aluminum refinery
        "lead_per_munitions": 1.5,       # per munitions factory
    }
    
    # Food Consumption
    FOOD_CONSUMPTION_RATE = 0.01  # 1% of population per turn
    
    # War Range Calculation
    WAR_RANGE_MULTIPLIER = 0.25  # 25% above/below score
    
    # Raid Configuration
    MIN_LOOT_POTENTIAL = 100000  # $100k minimum
    MAX_DEFENSIVE_WARS = 3
    TOP_ALLIANCE_RANK = 60
    
    # Audit Thresholds
    ACTIVITY_THRESHOLD = 86400  # 24 hours in seconds
    WARCHEST_DEFICIT_THRESHOLD = 0.25  # 25% of required supply
    MIN_PROJECTS = 10
    SPY_REQUIREMENTS = {
        "base": 50,
        "with_intelligence_agency": 60
    }
    
    # Deposit Thresholds (in thousands)
    DEPOSIT_THRESHOLDS = {
        "money": 100000,      # $100M
        "coal": 1000,         # 1M coal
        "oil": 1000,          # 1M oil
        "uranium": 100,       # 100k uranium
        "iron": 1000,         # 1M iron
        "bauxite": 1000,      # 1M bauxite
        "lead": 1000,         # 1M lead
        "gasoline": 100,      # 100k gasoline
        "munitions": 100,     # 100k munitions
        "steel": 100,         # 100k steel
        "aluminum": 100,      # 100k aluminum
        "food": 1000,         # 1M food
        "credits": 0          # 0 credits
    }
    
    # MMR Requirements
    MMR_REQUIREMENTS = {
        "Raider": {  # < 15 cities
            "barracks": 5,    # 5 barracks per city
            "factory": 0,     # 0 factories per city
            "hangar": 5,      # 5 hangars per city
            "drydock": 0      # 0 drydocks per city
        },
        "Whale": {   # ≥ 15 cities
            "barracks": 0,    # 0 barracks per city
            "factory": 2,     # 2 factories per city
            "hangar": 5,      # 5 hangars per city
            "drydock": 0      # 0 drydocks per city
        }
    }
    
    # Military Usage Thresholds
    MILITARY_HIGH_USAGE = 0.90  # 90% capacity
    MILITARY_LOW_USAGE = 0.10   # 10% capacity
    
    # City Scaling (for nations > 15 cities)
    CITY_SCALING_THRESHOLD = 15
    CITY_SCALING_REDUCTION = 0.05  # 5% reduction per city
    MIN_SCALING_FACTOR = 0.5  # Cap at 50% minimum
    
    # Loot Calculation Multipliers
    GDP_LOOT_MULTIPLIER = 0.1  # 10% of GDP
    MILITARY_LOOT_MULTIPLIER = 0.1  # 10% of military value
    CITY_LOOT_MULTIPLIER = 0.05  # 5% of estimated city value
    CITY_VALUE_ESTIMATE = 50000  # $50k per city estimate
    
    # Military Unit Values (for loot calculation)
    MILITARY_UNIT_VALUES = {
        "soldiers": 1.25,
        "tanks": 50,
        "aircraft": 500,
        "ships": 3375
    }
    
    # War Duration
    WAR_DURATION_TURNS = 60  # 5 days
    
    # Cache Configuration
    CACHE_UPDATE_INTERVAL = 300  # 5 minutes
    CACHE_RETRY_ATTEMPTS = 3
    CACHE_RETRY_DELAY = 5  # seconds
    
    # API Configuration
    API_TIMEOUT = 30  # seconds
    API_RETRY_ATTEMPTS = 3
    API_RETRY_DELAY = 1  # seconds
    
    # Pagination
    DEFAULT_ITEMS_PER_PAGE = 9
    PAGINATION_TIMEOUT = 300  # 5 minutes
    
    # Discord Configuration
    EMBED_COLOR_SUCCESS = 0x00ff00
    EMBED_COLOR_WARNING = 0xffff00
    EMBED_COLOR_ERROR = 0xff0000
    EMBED_COLOR_INFO = 0x0099ff
    EMBED_COLOR_RAID = 0x5865F2  # Discord blurple


