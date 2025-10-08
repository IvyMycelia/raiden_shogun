"""
Military information commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logging import get_logger
from utils.helpers import create_embed
from services.nation_service import NationService
from config import Config

config = Config()
logger = get_logger('nation.military')

class MilitaryCog(commands.Cog):
    """Military information commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.nation_service = NationService()
    
    @app_commands.command(name="military", description="Get military information for a nation")
    @app_commands.describe(nation_id="Nation ID to check (optional, defaults to your registered nation)")
    async def military(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        """Get military information for a nation."""
        try:
            await interaction.response.defer()
            
            # If no nation ID provided, try to get from registrations
            if not nation_id:
                from services.cache_service import CacheService
                cache_service = CacheService()
                registrations = cache_service.load_registrations()
                
                user_id = str(interaction.user.id)
                if user_id in registrations:
                    nation_id = registrations[user_id].get('nation_id')
                else:
                    await interaction.followup.send("No nation ID provided and you're not registered. Please provide a nation ID or register first.", ephemeral=True)
                    return
            
            # Get nation data using batch API (same as audit commands)
            nation_data = await self.nation_service.api.get_nations_batch_data([str(nation_id)], "everything_scope")
            if not nation_data or str(nation_id) not in nation_data:
                await interaction.followup.send(f"Could not find nation with ID {nation_id}.", ephemeral=True)
                return
            
            nation_info = nation_data[str(nation_id)]
            
            # Calculate military information
            military_info = self.calculate_military_info_from_dict(nation_info)
            
            # Create embed
            embed = create_embed(
                title=f"Military Information - {nation_info.get('nation_name', 'Unknown')}",
                description=f"**Leader:** {nation_info.get('leader_name', 'Unknown')}",
                color=discord.Color.blue()
            )
            
            # Add military fields
            for unit_type, info in military_info.items():
                percentage = (info['current'] / info['max']) * 100 if info['max'] > 0 else 0
                embed.add_field(
                    name=f"{unit_type.title()}",
                    value=f"**Current:** {info['current']:,}\n**Max:** {info['max']:,}\n**Percentage:** {percentage:.1f}%",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in military command: {e}")
            await interaction.followup.send("Error retrieving military information.", ephemeral=True)
    
    def calculate_military_info_from_dict(self, nation_info: dict) -> dict:
        """Calculate military capacity and current units."""
        try:
            cities_data = nation_info.get("cities", [])
            logger.info(f"Military calculation - Cities data: {len(cities_data) if cities_data else 0} cities")
            
            if not cities_data:
                logger.warning("No cities data found")
                return {
                    'soldiers': {'current': 0, 'max': 0},
                    'tanks': {'current': 0, 'max': 0},
                    'aircraft': {'current': 0, 'max': 0},
                    'ships': {'current': 0, 'max': 0}
                }
            
            # Get military research data
            military_research = nation_info.get("military_research", {})
            ground_capacity = military_research.get("ground_capacity", 0)
            air_capacity = military_research.get("air_capacity", 0)
            naval_capacity = military_research.get("naval_capacity", 0)
            
            logger.info(f"Military research data: ground={ground_capacity}, air={air_capacity}, naval={naval_capacity}")
            
            # Calculate total capacity from military research (flat bonuses)
            total_ground_research_capacity = ground_capacity * 250  # 250 tanks per level
            total_air_research_capacity = air_capacity * 15  # 15 planes per level  
            total_naval_research_capacity = naval_capacity * 5  # 5 ships per level
            
            # Debug: Check first city structure
            if cities_data:
                first_city = cities_data[0]
                logger.info(f"First city data keys: {list(first_city.keys()) if isinstance(first_city, dict) else 'Not a dict'}")
                if isinstance(first_city, dict):
                    logger.info(f"First city barracks: {first_city.get('barracks', 'NOT_FOUND')}")
                    logger.info(f"First city factory: {first_city.get('factory', 'NOT_FOUND')}")
                    logger.info(f"First city hangar: {first_city.get('hangar', 'NOT_FOUND')}")
                    logger.info(f"First city drydock: {first_city.get('drydock', 'NOT_FOUND')}")
            
            # Calculate total capacity and current units
            total_soldiers_capacity = 0
            total_tanks_capacity = 0
            total_aircraft_capacity = 0
            total_ships_capacity = 0
            
            for city in cities_data:
                if not isinstance(city, dict):
                    continue
                
                # Soldiers: barracks * 3000 (no research bonus for soldiers)
                barracks = city.get("barracks", 0)
                soldiers_cap = barracks * 3000
                total_soldiers_capacity += soldiers_cap
                
                # Tanks: factories * 250 + ground research bonus
                factories = city.get("factory", 0)
                tanks_cap = factories * 250
                total_tanks_capacity += tanks_cap
                
                # Aircraft: hangars * 15 + air research bonus
                hangars = city.get("hangar", 0)
                aircraft_cap = hangars * 15
                total_aircraft_capacity += aircraft_cap
                
                # Ships: drydocks * 5 + naval research bonus
                drydocks = city.get("drydock", 0)
                ships_cap = drydocks * 5
                total_ships_capacity += ships_cap
            
            # Add military research bonuses to total capacity
            total_soldiers_capacity += total_ground_research_capacity  # Ground research affects soldiers too
            total_tanks_capacity += total_ground_research_capacity
            total_aircraft_capacity += total_air_research_capacity
            total_ships_capacity += total_naval_research_capacity
            
            # Get current units
            current_soldiers = nation_info.get("soldiers", 0)
            current_tanks = nation_info.get("tanks", 0)
            current_aircraft = nation_info.get("aircraft", 0)
            current_ships = nation_info.get("ships", 0)
            
            logger.info(f"Final calculations - Soldiers: {current_soldiers}/{total_soldiers_capacity}, Tanks: {current_tanks}/{total_tanks_capacity}, Aircraft: {current_aircraft}/{total_aircraft_capacity}, Ships: {current_ships}/{total_ships_capacity}")
            logger.info(f"Research bonuses - Ground: {total_ground_research_capacity}, Air: {total_air_research_capacity}, Naval: {total_naval_research_capacity}")
            
            return {
                'soldiers': {
                    'current': current_soldiers,
                    'max': total_soldiers_capacity
                },
                'tanks': {
                    'current': current_tanks,
                    'max': total_tanks_capacity
                },
                'aircraft': {
                    'current': current_aircraft,
                    'max': total_aircraft_capacity
                },
                'ships': {
                    'current': current_ships,
                    'max': total_ships_capacity
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating military info: {e}")
            return {
                'soldiers': {'current': 0, 'max': 0},
                'tanks': {'current': 0, 'max': 0},
                'aircraft': {'current': 0, 'max': 0},
                'ships': {'current': 0, 'max': 0}
            }

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(MilitaryCog(bot))
