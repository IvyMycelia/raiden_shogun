"""
Nation information commands.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import math
import json
import traceback
from datetime import datetime, timezone

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.nation_service import NationService
from services.cache_service import CacheService
from services.war_service import WarService
from services.warchest_service import WarchestService
from utils.logging import get_logger
from utils.formatting import format_currency
from utils.helpers import create_embed, format_number
from config.constants import GameConstants

logger = get_logger('nation.info')

class NationInfoCog(commands.Cog):
    """Cog for nation information commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nation_service = NationService()
        self.cache_service = CacheService()
        self.war_service = WarService()
        self.warchest_service = WarchestService()
    
    async def who_logic(self, interaction, nation_id: Optional[int] = None, ctx=None):
        """Show basic nation information."""
        interaction_responded = False
        
        try:
            # Get nation ID
            if nation_id is None:
                user_id = str(interaction.user.id if interaction else ctx.author.id)
                nation_id = self.cache_service.get_user_nation(user_id)
                if not nation_id:
                    msg = "❌ You need to register your nation first! Use `/register` command."
                    if interaction:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                    else:
                        await ctx.send(msg)
                    return
            
            # Get nation data
            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                msg = "❌ Could not find nation data."
                if interaction:
                    if not interaction_responded:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                else:
                    await ctx.send(msg)
                return
            
            # Calculate war/spy ranges
            score = nation.score
            war_range_min = int(score * 0.75)
            war_range_max = int(score * 1.25)
            spy_range_min = int(score * 0.5)
            spy_range_max = int(score * 2.0)
            
            # Get Discord user if registered
            discord_info = ""
            try:
                # First try registrations.json
                with open('data/registrations.json', 'r') as f:
                    registrations = json.load(f)
                    for discord_id, reg_data in registrations.items():
                        if reg_data.get('nation_id') == nation_id:
                            discord_user = f"<@{discord_id}>"
                            discord_info = f" | {discord_user}"
                            break
                
                # If not found in registrations, try nation's Discord field from API
                if not discord_info and hasattr(nation, 'discord_username') and nation.discord_username:
                    discord_info = f" | {nation.discord_username}"
                elif not discord_info:
                    discord_info = " | N/A"
                    
            except Exception as e:
                # If registrations file fails, try nation's Discord field
                if hasattr(nation, 'discord_username') and nation.discord_username:
                    discord_info = f" | {nation.discord_username}"
                else:
                    discord_info = " | N/A"
            
            # Color emoji mapping
            color_emojis = {
                'gold': '<:Gold:1423182522027737159>',
                'aqua': '<:aqua:1423182542848393226>',
                'beige': '<:beige:1423182565946425356>',
                'black': '<:black:1423182584933912577>',
                'blue': '<:blue:1423182450628104242>',
                'brown': '<:brown:1423182485751070772>',
                'gray': '<:gray:1423182610162516018>',
                'green': '<:green:1423182626771959878>',
                'lime': '<:lime:1423182646724268072>',
                'maroon': '<:maroon:1423182673576329236>',
                'olive': '<:olive:1423182692937105419>',
                'orange': '<:orange:1423182713392861285>',
                'pink': '<:pink:1423182730161815647>',
                'purple': '<:purple:1423182746385252392>'
            }
            
            # Status emoji
            # status_emoji = "🟢"
            # if nation.vmode:
            #     status_emoji = "🟡"
            # elif nation.beige_turns > 0:
            #     status_emoji = "🟠"
            
            # Create compact embed
            embed = create_embed(
                title=f"{color_emojis.get(nation.color.lower(), '⚪')} **{nation.name}**",
                description=f"**Leader:** {nation.leader_name}{discord_info}",
                color=discord.Color.blue()
            )
            
            # Basic stats (compact)
            embed.add_field(
                name="**Stats**",
                value=(
                    f"**Score:** {format_number(nation.score, 0)}\n"
                    f"**Cities:** {nation.cities}\n"
                    f"**Alliance:** {nation.alliance_name if nation.alliance_name != 'None' else 'None'}\n"
                    f"**Position:** {nation.alliance_position}"
                ),
                inline=True
            )
            
            # Military (compact with emojis)
            embed.add_field(
                name="**Military**",
                value=(
                    f":military_helmet: {format_number(nation.soldiers, 0)}\n"
                    f"<:tank:1357398163442635063> {format_number(nation.tanks, 0)}\n"
                    f":airplane: {format_number(nation.aircraft, 0)}\n"
                    f":ship: {format_number(nation.ships, 0)}\n"
                    f"🕵️ {format_number(nation.spies, 0)}"
                ),
                inline=True
            )
            
            # War info (compact)
            embed.add_field(
                name="**War Info**",
                value=(
                    f"**Range:** {format_number(war_range_min, 0)} - {format_number(war_range_max, 0)}\n"
                    f"**Defensive:** {nation.defensive_wars}/10\n"
                    f"**Offensive:** {nation.offensive_wars}/5\n"
                ),
                inline=True
            )
            
            # Timestamps (compact)
            embed.add_field(
                name="**Activity**",
                value=(
                    f"**Last Online:** <t:{int(nation.last_active.timestamp())}:R>\n"
                    f"**Created:** <t:{int(nation.date.timestamp())}:R>"
                ),
                inline=True
            )
            
            # Nation URL (footer style)
            nation_url = f"https://politicsandwar.com/nation/id={nation.id}"
            embed.set_footer(text=f"View Nation: {nation_url}")
            
            if interaction:
                if not interaction_responded:
                    await interaction.response.send_message(embed=embed)
                    interaction_responded = True
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            file_name = tb[-1].filename.split('/')[-1] if tb else "unknown"
            line_num = tb[-1].lineno if tb else 0
            logger.error(f"Error in who command: {e} (File: {file_name}, Line: {line_num})")
            msg = (
                ":warning: An Error Occurred\n"
                f"**An unexpected error occurred while processing the command.**\n\n"
                f"**Error Type:** `{type(e).__name__}`\n"
                f"**Error Message:** {e}\n\n"
                f"Detailed error information has been logged internally. Please contact <@860564164828725299> if this issue persists."
            )
            if interaction and not interaction_responded:
                await interaction.response.send_message(msg, ephemeral=True)
            elif not interaction:
                await ctx.send(msg)

    @app_commands.command(name="who", description="Show basic information about a nation")
    @app_commands.describe(nation_id="The ID of the nation to look up (uses registered nation if not provided)")
    async def who_slash(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        """Show basic nation information."""
        await self.who_logic(interaction, nation_id)
    
    # Traditional ! prefix commands
    @commands.command(name="who")
    async def who_prefix(self, ctx, *, search_term: str = None):
        """Search for registered nations by nation name or discord username."""
        logger.info(f"Prefix command !who called by {ctx.author.name} (ID: {ctx.author.id}) with search term: {search_term}")
        
        try:
            # Load registrations
            try:
                with open('data/registrations.json', 'r') as f:
                    registrations = json.load(f)
            except FileNotFoundError:
                await ctx.send("No registrations found.")
                return
            except json.JSONDecodeError:
                await ctx.send("Error reading registrations file.")
                return
            
            if not search_term:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: No Search Term",
                        description="Please provide a search term (nation name or discord username).\nExample: `!who tre` or `!who Naturumgibt`",
                        color=discord.Color.orange()
                    )
                )
                return
            
            search_term_lower = search_term.lower()
            matches = []
            
            # Search through registrations
            for discord_id, reg_data in registrations.items():
                nation_name = reg_data.get('nation_name', '').lower()
                discord_name = reg_data.get('discord_name', '').lower()
                discord_username = reg_data.get('discord_username', '').lower()
                
                # Check if search term matches nation name, discord display name, or exact username
                if (search_term_lower in nation_name or 
                    search_term_lower in discord_name or
                    search_term_lower in discord_username or
                    nation_name.startswith(search_term_lower) or
                    discord_name.startswith(search_term_lower) or
                    discord_username.startswith(search_term_lower)):
                    
                    matches.append({
                        'discord_id': discord_id,
                        'reg_data': reg_data
                    })
            
            if not matches:
                await ctx.send(
                    embed=create_embed(
                        title=":information_source: No Matches Found",
                        description=f"No registered nations found matching '{search_term}'.",
                        color=discord.Color.blue()
                    )
                )
                return
            
            # Create embed with results
            embed = create_embed(
                title=f"Search Results for '{search_term}'",
                description=f"Found **{len(matches)}** matching registration(s):",
                color=discord.Color.green()
            )
            
            # Collect all results into a single string
            result_lines = []
            for match in matches:
                discord_id = match['discord_id']
                reg_data = match['reg_data']
                nation_id = reg_data.get('nation_id', '?')
                nation_name = reg_data.get('nation_name', 'Unknown')
                discord_name = reg_data.get('discord_name', 'Unknown')
                
                # Create user mention and nation link
                user_mention = f"<@{discord_id}>"
                nation_link = f"[{nation_name}](https://politicsandwar.com/nation/id={nation_id})"
                
                # Format line
                line = f"{user_mention} | {nation_link} ({nation_id})"
                result_lines.append(line)
            
            # Add all results to description
            embed.description += f"\n\n" + "\n".join(result_lines)
            
            await ctx.send(embed=embed)
            logger.info(f"Registration search completed by {ctx.author} for term '{search_term}', found {len(matches)} matches")
            
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            file_name = tb[-1].filename.split('/')[-1] if tb else "unknown"
            line_num = tb[-1].lineno if tb else 0
            logger.error(f"Error in who search command: {e} (File: {file_name}, Line: {line_num})")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while searching registrations. Please try again later.",
                    color=discord.Color.red()
                )
            )

    @commands.command(name="nw", aliases=["chest"])
    async def chest_prefix(self, ctx, nation_id: Optional[int] = None):
        """Show nation's resource chest (networth)."""
        logger.info(f"Prefix command !nw called by {ctx.author.name} (ID: {ctx.author.id})")
        await self.chest_logic(None, nation_id, ctx=ctx)
    
    @commands.command(name="wc", aliases=["warchest"])
    async def warchest_prefix(self, ctx, nation_id: Optional[int] = None):
        """Calculate warchest requirements for a nation."""
        logger.info(f"Prefix command !wc called by {ctx.author.name} (ID: {ctx.author.id})")
        await self.warchest_logic(None, nation_id, ctx=ctx)
    
    @app_commands.command(name="networth", description="Show a nation's resource chest (networth).")
    @app_commands.describe(nation_id="Nation ID to check (optional if you're registered)")
    async def networth_slash(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        """Show a nation's resource chest (networth)."""
        await self.chest_logic(interaction, nation_id)
    
    @app_commands.command(name="warchest", description="Calculate a nation's warchest requirements (5 days of upkeep)")
    @app_commands.describe(nation_id="Nation ID to calculate warchest for (optional if you're registered)")
    async def warchest_slash(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        """Calculate warchest requirements for a nation."""
        await self.warchest_logic(interaction, nation_id)

    
    
    
    async def chest_logic(self, interaction, nation_id: Optional[int] = None, ctx=None):
        """Show nation's resource chest (networth)."""
        interaction_responded = False
        
        try:
            # Get user's nation ID for permission checking
            user_id = str(interaction.user.id if interaction else ctx.author.id)
            user_nation_id = self.cache_service.get_user_nation(user_id)
            
            # If no nation_id provided, use user's registered nation
            if nation_id is None:
                if not user_nation_id:
                    msg = "❌ You need to register your nation first! Use `/register` command."
                    if interaction:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                    else:
                        await ctx.send(msg)
                    return
                nation_id = user_nation_id
            else:
                # User is trying to check someone else's nation
                # Check if user is above member rank in alliance
                if not user_nation_id:
                    msg = "❌ You need to register your nation first! Use `/register` command."
                    if interaction:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                    else:
                        await ctx.send(msg)
                    return
                
                # Get user's nation data to check alliance position
                user_nation = await self.nation_service.get_nation(user_nation_id, "everything_scope")
                if not user_nation:
                    msg = "❌ Could not find your nation data."
                    if interaction:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                    else:
                        await ctx.send(msg)
                    return
                
                # Check if user is above member rank (LEADER, HEIR, OFFICER)
                user_position = getattr(user_nation, 'alliance_position', 'MEMBER').upper()
                logger.info(f"User {user_id} (nation {user_nation_id}) has alliance position: {user_position}")
                
                # Allow if user is LEADER, HEIR, OFFICER, or if they're the alliance leader
                if user_position not in ['LEADER', 'HEIR', 'OFFICER']:
                    # Additional check: if user is the alliance leader (by nation ID)
                    if user_nation_id == 590508:  # Ivy's nation ID - alliance leader
                        logger.info(f"Allowing access for alliance leader (nation {user_nation_id})")
                    else:
                        msg = f"❌ You need to be above member rank in the alliance to check other people's resources. Your current position: {user_position}"
                        if interaction:
                            await interaction.response.send_message(msg, ephemeral=True)
                            interaction_responded = True
                        else:
                            await ctx.send(msg)
                        return
            
            # Get target nation data
            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                msg = "❌ Could not find nation data."
                if interaction:
                    if not interaction_responded:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                else:
                    await ctx.send(msg)
                return
            
            # Format the resources text with the same emojis as warchest
            txt = f"""
<:money:1357103044466184412> {format_number(nation.money, 0)}
<:coal:1357102730682040410>  {format_number(nation.coal, 0)}
<:oil:1357102740391854140> {format_number(nation.oil, 0)}
<:uranium:1357102742799126558> {format_number(nation.uranium, 0)}
<:iron:1357102735488581643>  {format_number(nation.iron, 0)}
<:bauxite:1357102729411039254>  {format_number(nation.bauxite, 0)}
<:lead:1357102736646209536> {format_number(nation.lead, 0)}
<:gasoline:1357102734645399602>  {format_number(nation.gasoline, 0)}
<:munitions:1357102777389814012> {format_number(nation.munitions, 0)}
<:steel:1357105344052072618>  {format_number(nation.steel, 0)}
<:aluminum:1357102728391819356>  {format_number(nation.aluminum, 0)}
<:food:1357102733571784735>  {format_number(nation.food, 0)}
<:credits:1357102732187537459>  {format_number(nation.credits, 0)} credits
"""
            
            # Create embed using the exact same design as warchest
            embed = create_embed(
                title=f':moneybag: Resource Chest for {nation.name} "{nation.leader_name}"',
                description="Current Resources On-Hand",
                color=discord.Color.purple(),
                fields=[
                    {"name": "Current Resources", "value": txt, "inline": False},
                ],
                footer="Maintained By Ivy"
            )
            
            if interaction:
                if not interaction_responded:
                    await interaction.response.send_message(embed=embed)
                    interaction_responded = True
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            file_name = tb[-1].filename.split('/')[-1] if tb else "unknown"
            line_num = tb[-1].lineno if tb else 0
            logger.error(f"Error in chest command: {e} (File: {file_name}, Line: {line_num})")
            msg = (
                ":warning: An Error Occurred\n"
                f"**An unexpected error occurred while processing the command.**\n\n"
                f"**Error Type:** `{type(e).__name__}`\n"
                f"**Error Message:** {e}\n\n"
                f"Detailed error information has been logged internally. Please contact <@860564164828725299> if this issue persists."
            )
            if interaction and not interaction_responded:
                await interaction.response.send_message(msg, ephemeral=True)
            elif not interaction:
                await ctx.send(msg)

    async def warchest_logic(self, interaction, nation_id: int = None, ctx=None):
        """Calculate warchest requirements for a nation."""
        interaction_responded = False
        try:
            # If no nation_id provided, try to get user's registered nation
            if nation_id is None:
                user_id = interaction.user.id if interaction else ctx.author.id
                nation_id = self.cache_service.get_user_nation(str(user_id))
                if nation_id is None:
                    msg = (
                        ":warning: No Nation ID Provided\n"
                        "Please provide a nation ID or register your nation using `/register`."
                    )
                    if interaction:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                    else:
                        await ctx.send(msg)
                    return
            
            # Get nation data
            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                if interaction:
                    await interaction.response.send_message("❌ Could not find nation data.", ephemeral=True)
                    interaction_responded = True
                else:
                    await ctx.send("❌ Could not find nation data.")
                return
            
            logger.info(f"Starting Warchest Calculation For: {nation.name} || https://politicsandwar.com/nation/id={nation_id} || By {interaction.user if interaction else ctx.author} In {interaction.channel if interaction else ctx.channel}")
            
            # Calculate warchest using the service with raw API data
            # Get the raw nation data from the API instead of using the Nation object
            raw_nation_data = await self.nation_service.api.get_nation_data(nation_id, "everything_scope")
            if not raw_nation_data:
                if interaction:
                    await interaction.response.send_message("❌ Could not fetch nation data for warchest calculation.", ephemeral=True)
                    interaction_responded = True
                else:
                    await ctx.send("❌ Could not fetch nation data for warchest calculation.")
                return
            
            result, excess, supply = self.warchest_service.calculate_warchest(raw_nation_data)
                
            if result is None:
                logger.error(f"Error calculating warchest for nation ID {nation_id}")
                if interaction:
                    await interaction.response.send_message("Error calculating warchest. Please check the nation ID.")
                    interaction_responded = True
                else:
                    await ctx.send("Error calculating warchest. Please check the nation ID.")
                return
            
            # Get current resources from the nation object
            current_resources = {
                'money': nation.money,
                'coal': nation.coal,
                'oil': nation.oil,
                'uranium': nation.uranium,
                'iron': nation.iron,
                'bauxite': nation.bauxite,
                'lead': nation.lead,
                'gasoline': nation.gasoline,
                'munitions': nation.munitions,
                'steel': nation.steel,
                'aluminum': nation.aluminum,
                'food': nation.food,
                'credits': nation.credits
            }
            
            # Format the resources showing deficits (what you actually need to get)
            txt = f"""
<:money:1357103044466184412> {format_number(result['money_deficit'])}
<:coal:1357102730682040410>  {format_number(result['coal_deficit'])}
<:oil:1357102740391854140> {format_number(result['oil_deficit'])}
<:uranium:1357102742799126558> {format_number(result['uranium_deficit'])}
<:iron:1357102735488581643>  {format_number(result['iron_deficit'])}
<:bauxite:1357102729411039254>  {format_number(result['bauxite_deficit'])}
<:lead:1357102736646209536> {format_number(result['lead_deficit'])}
<:gasoline:1357102734645399602>  {format_number(result['gasoline_deficit'])}
<:munitions:1357102777389814012> {format_number(result['munitions_deficit'])}
<:steel:1357105344052072618>  {format_number(result['steel_deficit'])}
<:aluminum:1357102728391819356>  {format_number(result['aluminum_deficit'])}
<:food:1357102733571784735>  {format_number(result['food_deficit'])}
<:credits:1357102732187537459>  {format_number(result['credits_deficit'])} credits
"""
            
            # Check for excess resources and create deposit URL
            excess_resources = {k: v for k, v in excess.items() if v > 0}
            if excess_resources:
                # Get alliance ID from config (you'll need to add this to your config)
                alliance_id = 13033  # Replace with actual alliance ID from config
                base_url = f"https://politicsandwar.com/alliance/id={alliance_id}&display=bank&d_note=safekeepings"
                query_params = "&".join(
                    f"d_{key}={math.floor(value * 100) / 100}" for key, value in excess_resources.items()
                )
                deposit_url = f"{base_url}&{query_params}"
            else:
                deposit_url = None
            
            # Create embed using the exact design from backup
            embed = create_embed(
                title=f':moneybag: Warchest for {nation.name} "{nation.leader_name}"',
                description="Warchest for 60 Turns (5 Days)",
                color=discord.Color.purple(),
                fields=[
                    {"name": "Required On-Hand", "value": txt, "inline": False},
                ],
                footer="Maintained By Ivy"
            )
            
            if deposit_url:
                embed.add_field(name="", value=f"[Deposit Excess]({deposit_url})", inline=False)
            
            if interaction:
                await interaction.response.send_message(embed=embed)
                interaction_responded = True
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            file_name = tb[-1].filename.split('/')[-1] if tb else "unknown"
            line_num = tb[-1].lineno if tb else 0
            logger.error(f"Error in warchest command: {e} (File: {file_name}, Line: {line_num})")
            msg = (
                ":warning: An Error Occurred\n"
                f"**An unexpected error occurred while processing the command.**\n\n"
                f"**Error Type:** `{type(e).__name__}`\n"
                f"**Error Message:** {e}\n\n"
                f"Detailed error information has been logged internally. Please contact <@860564164828725299> if this issue persists."
            )
            if interaction and not interaction_responded:
                await interaction.response.send_message(msg, ephemeral=True)
            elif not interaction:
                await ctx.send(msg)
    

async def setup(bot: commands.Bot):
    """Setup the cog."""
    await bot.add_cog(NationInfoCog(bot))
