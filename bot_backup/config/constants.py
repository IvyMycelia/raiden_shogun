"""
Game constants and enums for Politics and War.
"""
from enum import Enum


class NationColor(Enum):
    """Nation colors in Politics and War."""
    BEIGE = "beige"
    GRAY = "gray"
    LIME = "lime"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    PURPLE = "purple"
    PINK = "pink"
    MAROON = "maroon"
    BROWN = "brown"
    BLACK = "black"


class AlliancePosition(Enum):
    """Alliance positions."""
    LEADER = "LEADER"
    HEIR = "HEIR"
    OFFICER = "OFFICER"
    MEMBER = "MEMBER"
    APPLICANT = "APPLICANT"


class WarType(Enum):
    """Types of wars."""
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"


class WarStatus(Enum):
    """War status."""
    ACTIVE = "active"
    ENDED = "ended"
    PEACE = "peace"


# Game constants
class GameConstants:
    """Constants for Politics and War game mechanics."""
    
    # Score ranges
    MIN_SCORE = 0
    MAX_SCORE = 10000
    
    # City limits
    MIN_CITIES = 1
    MAX_CITIES = 50
    
    # Military limits
    MAX_SOLDIERS = 2000000
    MAX_TANKS = 100000
    MAX_AIRCRAFT = 20000
    MAX_SHIPS = 1000
    MAX_MISSILES = 1000
    MAX_NUKES = 1000
    MAX_SPIES = 60
    
    # War limits
    MAX_OFFENSIVE_WARS = 5
    MAX_DEFENSIVE_WARS = 10
    
    # Alliance limits
    MAX_ALLIANCE_MEMBERS = 1000
    TOP_ALLIANCE_RANK = 60
    
    # Resource limits
    MAX_MONEY = 1000000000  # 1B
    MAX_RESOURCES = 10000000  # 10M
    
    # Cache settings
    CACHE_TTL = 300  # 5 minutes
    MAX_CACHE_ENTRIES = 10000
    
    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 50
    
    # Rate limiting
    API_RATE_LIMIT = 100  # requests per minute
    API_TIMEOUT = 30  # seconds


# Military unit costs (per day)
MILITARY_COSTS = {
    'soldiers': 1.25,
    'tanks': 50,
    'aircraft': 500,
    'ships': 3375,
    'missiles': 10000,
    'nukes': 100000,
    'spies': 50
}

# Resource values (approximate market prices)
RESOURCE_VALUES = {
    'money': 1.0,
    'coal': 100,
    'oil': 100,
    'uranium': 1000,
    'iron': 100,
    'bauxite': 100,
    'lead': 100,
    'gasoline': 1000,
    'munitions': 1000,
    'steel': 1000,
    'aluminum': 1000,
    'food': 100
}

# War range multipliers
WAR_RANGE_MULTIPLIERS = {
    'min': 0.75,
    'max': 1.25
}

# Alliance rank thresholds
ALLIANCE_RANK_THRESHOLDS = {
    'top_alliance': 60,
    'major_alliance': 100,
    'minor_alliance': 500
}
