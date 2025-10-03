"""
Configuration module for the Raiden Shogun bot.
"""

from .settings import Settings, settings
from .constants import (
    NationColor,
    AlliancePosition,
    WarType,
    WarStatus,
    GameConstants,
    MILITARY_COSTS,
    RESOURCE_VALUES,
    WAR_RANGE_MULTIPLIERS,
    ALLIANCE_RANK_THRESHOLDS
)

__all__ = [
    'Settings',
    'settings',
    'NationColor',
    'AlliancePosition', 
    'WarType',
    'WarStatus',
    'GameConstants',
    'MILITARY_COSTS',
    'RESOURCE_VALUES',
    'WAR_RANGE_MULTIPLIERS',
    'ALLIANCE_RANK_THRESHOLDS'
]
