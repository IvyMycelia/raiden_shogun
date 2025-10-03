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
    
    def calculate_military_capacity(self, cities: List, military_research: Dict[str, int] = None) -> Dict[str, int]:
        """Calculate total military capacity from cities and research."""
        capacity = {
            "soldiers": 0,
            "tanks": 0,
            "aircraft": 0,
            "ships": 0
        }
        
        # Calculate from cities - handle both City objects and dictionaries
        for city in cities:
            if hasattr(city, 'barracks'):
                # City object - access direct building fields
                capacity["soldiers"] += city.barracks * 3000
                capacity["tanks"] += city.factory * 250
                capacity["aircraft"] += city.hangar * 15
                capacity["ships"] += city.drydock * 5
            else:
                # Dictionary - use get method
                capacity["soldiers"] += city.get("barracks", 0) * 3000
                capacity["tanks"] += city.get("factory", 0) * 250
                capacity["aircraft"] += city.get("hangar", 0) * 15
                capacity["ships"] += city.get("drydock", 0) * 5
        
        # Apply military research flat bonuses
        print(f"DEBUG: Military research data: {military_research}")
        if military_research:
            print(f"DEBUG: Applying military research bonuses")
            # Ground capacity: 250 tanks per level, 3000 soldiers per level
            ground_level = military_research.get('ground_capacity', 0)
            print(f"DEBUG: Ground level: {ground_level}")
            capacity["tanks"] += ground_level * 250
            capacity["soldiers"] += ground_level * 3000
            
            # Air capacity: 15 planes per level
            air_level = military_research.get('air_capacity', 0)
            print(f"DEBUG: Air level: {air_level}")
            capacity["aircraft"] += air_level * 15
            
            # Naval capacity: 5 ships per level
            naval_level = military_research.get('naval_capacity', 0)
            print(f"DEBUG: Naval level: {naval_level}")
            capacity["ships"] += naval_level * 5
            print(f"DEBUG: Ships capacity after naval bonus: {capacity['ships']}")
        else:
            print(f"DEBUG: No military research data, skipping bonuses")
        
        return capacity
    
    def calculate_military_usage(self, nation: Dict) -> Dict[str, int]:
        """Get current military usage."""
        return {
            "soldiers": nation.get("soldiers", 0),
            "tanks": nation.get("tanks", 0),
            "aircraft": nation.get("aircraft", 0),
            "ships": nation.get("ships", 0)
        }
    
    def get_user_nation(self, user_id: int) -> Optional[int]:
        """Get user's nation ID from registrations."""
        from services.cache_service import CacheService
        cache_service = CacheService()
        return cache_service.get_user_nation(str(user_id))
    
    async def military_logic(self, interaction, nation_id: int = None, ctx=None):
        interaction_responded = False
        try:
            if nation_id is None:
                user_id = interaction.user.id if interaction else ctx.author.id
                nation_id = self.get_user_nation(user_id)
                if nation_id is None:
                    msg = (
                        "❌ No Nation ID Provided\n"
                        "Please provide a nation ID or register your nation using `/register`."
                    )
                    if interaction:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                    else:
                        await ctx.send(msg)
                    return
            
            # Get nation data
            logger.info(f"Fetching nation data for ID: {nation_id}")
            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            logger.info(f"Nation data result: {nation is not None}")
            if not nation:
                logger.warning(f"No nation data found for ID: {nation_id}")
                if interaction:
                    await interaction.response.send_message("❌ Nation not found.", ephemeral=True)
                    interaction_responded = True
                else:
                    await ctx.send("❌ Nation not found.")
                return
            
            # Get cities data
            logger.info(f"Getting cities data from nation object")
            cities = nation.cities_data if hasattr(nation, 'cities_data') else []
            logger.info(f"Cities data result: {len(cities) if cities else 0} cities found")
            print(f"DEBUG: Cities check passed, about to continue")
            if not cities:
                logger.warning(f"No cities data found for nation {nation_id}")
                if interaction:
                    await interaction.response.send_message("❌ Could not fetch city data.", ephemeral=True)
                    interaction_responded = True
                else:
                    await ctx.send("❌ Could not fetch city data.")
            return
        
            # Calculate capacity and usage
            print(f"DEBUG: About to calculate military capacity for {len(cities)} cities")
            print(f"DEBUG: Nation object type: {type(nation)}")
            logger.info(f"DEBUG: About to calculate military capacity for {len(cities)} cities")
            logger.info(f"DEBUG: Nation object type: {type(nation)}")
            logger.info(f"DEBUG: Nation attributes: {dir(nation)}")
            logger.info(f"Calculating military capacity for {len(cities)} cities")
            military_research = getattr(nation, 'military_research', {})
            logger.info(f"Military research data: {military_research}")
            capacity = self.calculate_military_capacity(cities, military_research)
            logger.info(f"Military capacity calculated: {capacity}")
            
            usage = self.calculate_military_usage(nation.__dict__)
            logger.info(f"Military usage calculated: {usage}")
            
            # Create embed with separate categories for each military unit
            embed = discord.Embed(
                title=f"Military Status for {nation.name}",
                description=f"Leader: {nation.leader_name}",
                color=discord.Color.blue()
            )
            
            # Add separate fields for each military unit type
            embed.add_field(
                name="Soldiers",
                value=f"{usage['soldiers']:,} / {capacity['soldiers']:,}",
                inline=True
            )
            
            embed.add_field(
                name="Tanks", 
                value=f"{usage['tanks']:,} / {capacity['tanks']:,}",
                inline=True
            )
            
            embed.add_field(
                name="Aircraft",
                value=f"{usage['aircraft']:,} / {capacity['aircraft']:,}",
                inline=True
            )
            
            embed.add_field(
                name="Ships",
                value=f"{usage['ships']:,} / {capacity['ships']:,}",
                inline=True
            )
            
            embed.add_field(
                name="Missiles",
                value=f"{nation.missiles:,}",
                inline=True
            )
            
            embed.add_field(
                name="Nukes",
                value=f"{nation.nukes:,}",
                inline=True
            )
            
            if interaction:
                logger.info(f"Sending military response to {interaction.user.name} in #{interaction.channel.name}")
                await interaction.response.send_message(embed=embed)
                interaction_responded = True
                logger.info(f"Military response sent successfully")
            else:
                logger.info(f"Sending military response to {ctx.author.name} in #{ctx.channel.name}")
                await ctx.send(embed=embed)
                logger.info(f"Military response sent successfully")
            
            logger.info(f"Military command executed for nation {nation_id} by {interaction.user if interaction else ctx.author}")
            
        except Exception as e:
            logger.error(f"Error in military command: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            msg = "❌ An error occurred while fetching military information."
            if interaction and not interaction_responded:
                await interaction.response.send_message(msg, ephemeral=True)
                logger.info(f"Error response sent to {interaction.user.name} in #{interaction.channel.name}")
            elif not interaction:
                await ctx.send(msg)
                logger.info(f"Error response sent to {ctx.author.name} in #{ctx.channel.name}")
    
    @app_commands.command(name="military", description="Check a nation's military capacity and usage")
    @app_commands.describe(nation_id="The ID of the nation to check (uses registered nation if not provided)")
    async def military_slash(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        """Check military capacity."""
        await self.military_logic(interaction, nation_id)
    
    @commands.command(name="military")
    async def military_prefix(self, ctx, nation_id: Optional[int] = None):
        """Check military capacity."""
        await self.military_logic(None, nation_id, ctx=ctx)

async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(WarAnalysisCog(bot))