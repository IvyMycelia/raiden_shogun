import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, List, Dict
import asyncio

from bot.services.nation_service import NationService
from bot.services.raid_calculation_service import RaidCalculationService
from bot.api.politics_war_api import api
from bot.utils.purge_paginator import PurgePaginator

logger = logging.getLogger('raiden_shogun')

class PurgeCog(commands.Cog):
    """Commands for finding purge targets to boost color bloc bonus."""
    
    def __init__(self, bot):
        self.bot = bot
        self.nation_service = NationService()
        self.raid_calculation_service = RaidCalculationService()
    
    @app_commands.command(name="purge", description="Find purple nations to purge for color bloc bonus")
    @app_commands.describe(max_score="Maximum score to search for (default: 2000)")
    async def purge_slash(self, interaction: discord.Interaction, max_score: int = 2000):
        """Slash command for finding purge targets."""
        await self.purge_logic(interaction, max_score, is_slash=True)
    
    @commands.command(name="purge")
    async def purge_prefix(self, ctx: commands.Context, max_score: int = 2000):
        """Prefix command for finding purge targets."""
        await self.purge_logic(ctx, max_score, is_slash=False)
    
    async def purge_logic(self, ctx_or_interaction, max_score: int, is_slash: bool = True):
        """Main purge logic for both slash and prefix commands."""
        try:
            # Defer response for slash commands
            if is_slash:
                await ctx_or_interaction.response.defer()
            
            # Send initial response
            loading_embed = discord.Embed(
                title="🔍 **Searching for Purge Targets...**",
                description=f"Finding purple nations with score ≤ {max_score:,}...",
                color=discord.Color.purple()
            )
            
            if is_slash:
                await ctx_or_interaction.followup.send(embed=loading_embed)
            else:
                loading_msg = await ctx_or_interaction.send(embed=loading_embed)
            
            # Get purple nations from API
            purple_nations = await self.get_purge_nations(max_score)
            
            if not purple_nations:
                error_embed = discord.Embed(
                    title="❌ **No Purple Nations Found**",
                    description=f"No purple nations found with score ≤ {max_score:,}",
                    color=discord.Color.red()
                )
                
                if is_slash:
                    await ctx_or_interaction.followup.send(embed=error_embed)
                else:
                    await loading_msg.edit(embed=error_embed)
                return
            
            # Filter and process targets
            valid_targets = await self.filter_purge_targets(purple_nations)
            
            if not valid_targets:
                no_targets_embed = discord.Embed(
                    title="❌ **No Valid Purge Targets**",
                    description="All purple nations are either in your alliance, top 50 alliances, or have 15+ cities",
                    color=discord.Color.red()
                )
                
                if is_slash:
                    await ctx_or_interaction.followup.send(embed=no_targets_embed)
                else:
                    await loading_msg.edit(embed=no_targets_embed)
                return
            
            # Create paginator
            paginator = PurgePaginator(valid_targets)
            
            # Send results
            results_embed = paginator.get_embed()
            
            if is_slash:
                await ctx_or_interaction.followup.send(embed=results_embed, view=paginator)
            else:
                await loading_msg.edit(embed=results_embed, view=paginator)
            
            # Log success
            logger.info(f"{len(valid_targets)} targets found")
        
        except Exception as e:
            logger.error(f"Error in purge command: {e}")
            error_embed = discord.Embed(
                title="❌ **Error**",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            
            if is_slash:
                await ctx_or_interaction.followup.send(embed=error_embed)
            else:
                await loading_msg.edit(embed=error_embed)
    
    async def get_purge_nations(self, max_score: int) -> List[Dict]:
        """Get purple nations from API."""
        try:
            query = f"""
            {{
                nations(first: 500, vmode: false, color: "purple", max_score: {max_score}) {{
                    data {{
                        id
                        score
                        color
                        nation_name
                        leader_name
                        num_cities
                        alliance_id
                        alliance_position
                        alliance {{
                            id
                            name
                            rank
                        }}
                    }}
                }}
            }}
            """
            
            response = await api._make_graphql_request(query)
            if response and response.get("data", {}).get("nations", {}).get("data"):
                nations_data = response["data"]["nations"]["data"]
                logger.info(f"Retrieved {len(nations_data)} purple nations from API")
                return nations_data
            else:
                logger.warning("No purple nations data found in API response")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching purple nations: {e}")
            return []
    
    async def filter_purge_targets(self, purple_nations: List[Dict]) -> List[Dict]:
        """Filter purple nations to find valid purge targets."""
        valid_targets = []
        
        for nation in purple_nations:
            try:
                # Skip if no valid data
                if not nation or not isinstance(nation, dict):
                    continue
                
                nation_id = nation.get('id')
                if not nation_id:
                    continue
                
                # Get alliance info
                alliance = nation.get('alliance', {})
                alliance_id = alliance.get('id') if alliance else nation.get('alliance_id')
                alliance_rank = alliance.get('rank', 999) if alliance else 999
                alliance_name = alliance.get('name', 'None') if alliance else 'None'
                
                # Skip if in our alliance (13033)
                if alliance_id and int(alliance_id) == 13033:
                    continue
                
                # Skip if in top 70 alliances (too strong)
                if alliance_rank and int(alliance_rank) <= 70:
                    continue
                
                # Get city count
                city_count = nation.get('num_cities', 0)
                
                # Only include nations with less than 15 cities (easier to defeat)
                if city_count < 15:
                    # Format nation data for RaidPaginator
                    formatted_nation = {
                        'id': nation.get('id'),
                        'nation_name': nation.get('nation_name', 'Unknown'),
                        'score': nation.get('score', 0),
                        'alliance_name': alliance_name,
                        'alliance_position': self.format_alliance_position(nation.get('alliance_position', 'None')),
                        'soldiers': 0,  # Not available in purge data
                        'tanks': 0,
                        'aircraft': 0,
                        'ships': 0
                    }
                    
                    valid_targets.append({
                        'nation_data': formatted_nation,
                        'cities_data': [],  # Will be filled by batch_get_city_data
                        'city_count': city_count,
                        'loot_potential': 0  # Not calculated for purge targets
                    })
                    
            except Exception as e:
                logger.error(f"Error processing nation {nation.get('id', 'unknown')}: {e}")
                continue
        
        # Sort by score (highest first - more color bonus)
        valid_targets.sort(key=lambda x: x['nation_data']['score'], reverse=True)
        
        # Batch retrieve city data for all valid targets
        if valid_targets:
            await self.batch_get_city_data(valid_targets)
        
        return valid_targets
    
    async def batch_get_city_data(self, targets: List[Dict]) -> None:
        """Batch retrieve city data for all targets."""
        try:
            # Extract all nation IDs
            nation_ids = [target['nation_data']['id'] for target in targets]
            
            # Batch retrieve city data
            cities_data = await api.get_cities_batch_data(nation_ids)
            
            # Add city data to each target
            for target in targets:
                nation_id = target['nation_data']['id']
                target['cities_data'] = cities_data.get(str(nation_id), [])
                
        except Exception as e:
            logger.error(f"Error batch fetching city data: {e}")
            # Set empty cities data for all targets on error
            for target in targets:
                target['cities_data'] = []
    
    def format_alliance_position(self, position: str) -> str:
        """Format alliance position for display."""
        if not position or position.upper() in ['NONE', 'NOALLIANCE', 'NULL']:
            return 'None'
        
        # Convert common positions to proper case
        position_map = {
            'MEMBER': 'Member',
            'LEADER': 'Leader',
            'OFFICER': 'Officer',
            'HEIR': 'Heir',
            'APPLICANT': 'Applicant'
        }
        
        return position_map.get(position.upper(), position.title())
    

async def setup(bot):
    await bot.add_cog(PurgeCog(bot))
