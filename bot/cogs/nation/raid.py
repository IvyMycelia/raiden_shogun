import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from services.raid_cache_service import RaidCacheService
from services.raid_calculation_service import RaidCalculationService
from services.nation_service import NationService
from services.cache_service import CacheService
from utils.raid_paginator import RaidPaginator

logger = logging.getLogger('raiden_shogun')

class RaidCog(commands.Cog):
    """Raid-related commands for finding profitable targets."""
    
    def __init__(self, bot):
        self.bot = bot
        self.nation_service = NationService()
        self.cache_service = CacheService()
        self.raid_calculation_service = RaidCalculationService()
    
    async def get_user_nation_id(self, ctx_or_interaction, is_slash: bool = True) -> Optional[int]:
        """Get user's nation ID from cache."""
        try:
            user_id = str(ctx_or_interaction.user.id) if is_slash else str(ctx_or_interaction.author.id)
            nation_id = self.cache_service.get_user_nation(user_id)
            
            if not nation_id:
                error_msg = "❌ You need to register your nation first! Use /register command."
                if is_slash:
                    await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
                else:
                    await ctx_or_interaction.send(error_msg)
                return None
            
            return nation_id
        except Exception as e:
            logger.error(f"Error getting user nation ID: {e}")
            return None
    
    async def send_error(self, ctx_or_interaction, message: str, is_slash: bool = True):
        """Send error message."""
        try:
            if is_slash:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(message, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(message, ephemeral=True)
            else:
                await ctx_or_interaction.send(message)
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
    async def raid_logic(self, ctx_or_interaction, score: float = None, is_slash: bool = True):
        """Main raid logic for both slash and prefix commands."""
        try:
            # Get user's score
            if score is None:
                user_nation_id = await self.get_user_nation_id(ctx_or_interaction, is_slash)
                if not user_nation_id:
                    return
                
                # Fetch user's nation data to get score
                user_nation_data = await self.nation_service.get_nation(user_nation_id)
                if not user_nation_data:
                    await self.send_error(ctx_or_interaction, "Could not find nation data.", is_slash)
                    return
                
                user_score = user_nation_data.score
            else:
                user_score = score
            
            # Defer response for slash commands
            if is_slash:
                await ctx_or_interaction.response.defer()
            
            # Send progress message
            progress_embed = discord.Embed(
                title="🔍 **Searching for Raid Targets...**",
                description=f"Finding targets within war range of score {user_score:,.2f}...",
                color=discord.Color.yellow()
            )
            
            if is_slash:
                progress_msg = await ctx_or_interaction.followup.send(embed=progress_embed)
            else:
                progress_msg = await ctx_or_interaction.send(embed=progress_embed)
            
            # Progress callback function
            async def update_progress(step_description):
                progress_embed.description = f"**{step_description}**\n\nFinding targets within war range of score {user_score:,.2f}..."
                await progress_msg.edit(embed=progress_embed)
            
            # Load cached data
            async with RaidCacheService() as cache_service:
                cache_data = cache_service.load_raid_cache()
                
                if not cache_data:
                    await self.send_error(ctx_or_interaction, "No cached data available. Please try again later.", is_slash)
                    return
                
                nations_data = cache_data.get('nations', {})
                cities_data = cache_data.get('cities', {})
                wars_data = cache_data.get('wars', {})
                alliances_data = cache_data.get('alliances', {})
                
                if not nations_data:
                    await self.send_error(ctx_or_interaction, "No nations data available in cache.", is_slash)
                    return
                
                # Create user nation dict for filtering (only need score for war range)
                user_nation_dict = {
                    'score': user_score,
                    'id': user_nation_data.id if score is None else 0,  # Use actual ID if from registered nation
                    'nation_name': user_nation_data.name if score is None else "Custom Score",
                    'leader': user_nation_data.leader_name if score is None else "Unknown",
                    'alliance_id': user_nation_data.alliance_id if score is None else 0,
                    'alliance_name': user_nation_data.alliance_name if score is None else "None",
                    'cities': user_nation_data.cities if score is None else 0,
                    'soldiers': user_nation_data.soldiers if score is None else 0,
                    'tanks': user_nation_data.tanks if score is None else 0,
                    'aircraft': user_nation_data.aircraft if score is None else 0,
                    'ships': user_nation_data.ships if score is None else 0,
                    'missiles': user_nation_data.missiles if score is None else 0,
                    'nukes': user_nation_data.nukes if score is None else 0,
                    'spies': user_nation_data.spies if score is None else 0,
                    'money': user_nation_data.money if score is None else 0,
                    'coal': user_nation_data.coal if score is None else 0,
                    'oil': user_nation_data.oil if score is None else 0,
                    'uranium': user_nation_data.uranium if score is None else 0,
                    'iron': user_nation_data.iron if score is None else 0,
                    'bauxite': user_nation_data.bauxite if score is None else 0,
                    'lead': user_nation_data.lead if score is None else 0,
                    'gasoline': user_nation_data.gasoline if score is None else 0,
                    'munitions': user_nation_data.munitions if score is None else 0,
                    'steel': user_nation_data.steel if score is None else 0,
                    'aluminum': user_nation_data.aluminum if score is None else 0,
                    'food': user_nation_data.food if score is None else 0,
                    'credits': user_nation_data.credits if score is None else 0
                }
                
                # Filter targets
                valid_targets, filtered_out = await self.raid_calculation_service.filter_raid_targets(
                    user_nation_dict, nations_data, cities_data, wars_data, alliances_data, update_progress
                )
                
                if not valid_targets:
                    no_targets_embed = discord.Embed(
                        title="❌ **No Raid Targets Found**",
                        description="No suitable targets found within your war range.",
                        color=discord.Color.red()
                    )
                    
                    # Add filtering statistics
                    stats = "**Filtering Results:**\n"
                    for reason, count in filtered_out.items():
                        if count > 0:
                            stats += f"• {reason.replace('_', ' ').title()}: {count:,}\n"
                    
                    no_targets_embed.add_field(name="Filtering Statistics", value=stats, inline=False)
                    
                    # Replace the progress message with no targets message
                    await progress_msg.edit(embed=no_targets_embed)
                    return
                
                # Create paginator
                paginator = RaidPaginator(valid_targets)
                
                # Send results
                results_embed = paginator.get_embed()
                
                # Replace the progress message with results
                await progress_msg.edit(embed=results_embed, view=paginator)
                
                # Log success
                logger.info(f"Raid command completed: {len(valid_targets)} targets found for score {user_score}")
        
        except Exception as e:
            logger.error(f"Error in raid command: {e}")
            await self.send_error(ctx_or_interaction, f"An error occurred: {str(e)}", is_slash)
    
    @commands.command(name="raid")
    async def raid_prefix(self, ctx: commands.Context, score: float = None):
        """Find raid targets using prefix command."""
        await self.raid_logic(ctx, score, is_slash=False)
    
    @app_commands.command(name="raid", description="Find profitable raid targets within your war range")
    @app_commands.describe(score="Your nation score to filter war range (uses your registered nation if not provided)")
    async def raid_slash(self, interaction: discord.Interaction, score: float = None):
        """Find raid targets using slash command."""
        await self.raid_logic(interaction, score, is_slash=True)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(RaidCog(bot))