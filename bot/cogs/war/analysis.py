"""
War analysis commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.war_service import WarService
from services.nation_service import NationService
from utils.logging import get_logger
from utils.formatting import format_number
from config.constants import GameConstants

logger = get_logger('war.analysis')

class WarAnalysisCog(commands.Cog):
    """Cog for war analysis commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.war_service = WarService()
        self.nation_service = NationService()
        
        # MMR requirements for different roles
        self.mmr_requirements = {
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
    
    

async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(WarAnalysisCog(bot))