import discord
from discord import app_commands, AllowedMentions
from discord.ext import commands
from discord.ui import View, Button, Select
from datetime import datetime, timezone
import pytz
import math
import random
import os
import asyncio
import json
import time
import traceback
import sys
import re
from typing import Optional, List, Dict, Any

from bot.utils.config import config
from bot.utils.helpers import create_embed, format_number
from bot.utils.paginator import GridPaginator, PaginatorView
from bot.handler import info, error, warning
from bot import data as get_data
from bot import calculate
from bot import vars
from bot import db as dataBase

class NationCog(commands.Cog):
    """Cog for nation-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
    
    def get_user_nation(self, user_id: int) -> Optional[int]:
        """Get a user's registered nation ID."""
        from bot.cogs.user import UserCog  # Avoid circular import
        user_cog = self.bot.get_cog('UserCog')
        if not user_cog:
            return None
        return user_cog.get_user_nation(user_id)
    
    
    def extract_war_id_from_channel(self, channel_name: str) -> Optional[int]:
        """Extract war ID from channel name like 'something-here-590506'."""
        # Look for numbers at the end of the channel name
        match = re.search(r'-(\d+)$', channel_name)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None
    
    def format_war_result(self, war: Dict) -> str:
        """Format detailed war result information."""
        attacker = war.get('attacker', {})
        defender = war.get('defender', {})
        
        # Calculate losses and gains
        att_soldiers_lost = war.get('att_soldiers_lost', 0)
        def_soldiers_lost = war.get('def_soldiers_lost', 0)
        att_tanks_lost = war.get('att_tanks_lost', 0)
        def_tanks_lost = war.get('def_tanks_lost', 0)
        att_aircraft_lost = war.get('att_aircraft_lost', 0)
        def_aircraft_lost = war.get('def_aircraft_lost', 0)
        att_ships_lost = war.get('att_ships_lost', 0)
        def_ships_lost = war.get('def_ships_lost', 0)
        
        att_infra_destroyed = war.get('att_infra_destroyed', 0)
        def_infra_destroyed = war.get('def_infra_destroyed', 0)
        att_money_looted = war.get('att_money_looted', 0)
        def_money_looted = war.get('def_money_looted', 0)
        
        # Determine winner
        winner_id = war.get('winner_id')
        if winner_id == attacker.get('id'):
            winner = f"**Winner:** {attacker.get('leader_name', 'N/A')} (Attacker)"
        elif winner_id == defender.get('id'):
            winner = f"**Winner:** {defender.get('leader_name', 'N/A')} (Defender)"
        else:
            winner = "**Winner:** Draw/In Progress"
        
        # Format war result
        result = [
            f"**War ID:** {war['id']}",
            f"**Type:** {war.get('war_type', 'N/A')}",
            f"**Reason:** {war.get('reason', 'N/A')}",
            "",
            f"**Attacker:** [{attacker.get('leader_name', 'N/A')}](https://politicsandwar.com/nation/id={attacker.get('id', '')})",
            f"**Defender:** [{defender.get('leader_name', 'N/A')}](https://politicsandwar.com/nation/id={defender.get('id', '')})",
            "",
            winner,
            "",
            f"**Final Points:** {war.get('att_points', 0)} vs {war.get('def_points', 0)}",
            f"**Final Resistance:** {war.get('att_resistance', 0)}% vs {war.get('def_resistance', 0)}%",
            "",
            f"**Military Losses:**",
            f"<:military_helmet:1357103044466184412> Soldiers: {format_number(att_soldiers_lost)} vs {format_number(def_soldiers_lost)}",
            f"<:tank:1357398163442635063> Tanks: {format_number(att_tanks_lost)} vs {format_number(def_tanks_lost)}",
            f":airplane: Aircraft: {format_number(att_aircraft_lost)} vs {format_number(def_aircraft_lost)}",
            f":ship: Ships: {format_number(att_ships_lost)} vs {format_number(def_ships_lost)}",
            "",
            f"**Infrastructure Destroyed:**",
            f"Attacker: {format_number(att_infra_destroyed)}",
            f"Defender: {format_number(def_infra_destroyed)}",
            "",
            f"**Money Looted:**",
            f"Attacker: ${format_number(att_money_looted)}",
            f"Defender: ${format_number(def_money_looted)}",
            "",
            f"**Control:** {war.get('ground_control', 'None')} Ground | {war.get('air_superiority', 'None')} Air | {war.get('naval_blockade', 'None')} Naval"
        ]
        
        return "\n".join(result)
    
    async def warchest_logic(self, interaction, nation_id: int = None, ctx=None):
        interaction_responded = False
        try:
            # If no nation_id provided, try to get user's registered nation
            if nation_id is None:
                user_id = interaction.user.id if interaction else ctx.author.id
                nation_id = self.get_user_nation(user_id)
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
            nation_info = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            info(f"Starting Warchest Calculation For: {nation_info.get('nation_name', 'N/A')} || https://politicsandwar.com/nation/id={nation_id} || By {interaction.user if interaction else ctx.author} In {interaction.channel if interaction else ctx.channel}")
            
            # Fetch city data separately and merge with nation data
            cities = get_data.GET_CITY_DATA(nation_id, self.config.API_KEY)
            if cities:
                nation_info["cities"] = cities
                info(f"Fetched {len(cities)} cities for warchest calculation", tag="WARCH")
            else:
                nation_info["cities"] = []
                warning(f"No city data found for nation {nation_id}", tag="WARCH")
            
            result, excess, _ = calculate.warchest(nation_info, vars.COSTS, vars.MILITARY_COSTS)
                
            if result is None:
                error(f"Error calculating warchest for nation ID {nation_id}", tag="WARCH")
                if interaction:
                    await interaction.response.send_message("Error calculating warchest. Please check the nation ID.")
                    interaction_responded = True
                else:
                    await ctx.send("Error calculating warchest. Please check the nation ID.")
                return
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
            excess_resources = {k: v for k, v in excess.items() if v > 0}
            if excess_resources:
                base_url = f"https://politicsandwar.com/alliance/id={self.config.ALLIANCE_ID}&display=bank&d_note=safekeepings"
                query_params = "&".join(
                    f"d_{key}={math.floor(value * 100) / 100}" for key, value in excess_resources.items()
                )
                deposit_url = f"{base_url}&{query_params}"
            else:
                deposit_url = None
            
            embed = create_embed(
                title=f':moneybag: Warchest for {nation_info.get("nation_name", "N/A")} "{nation_info.get("leader_name", "N/A")}"',
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
            error(f"Error in warchest command: {e}", tag="WARCH")
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

    @app_commands.command(name="warchest", description="Calculate a nation's warchest requirements (5 days of upkeep).")
    @app_commands.describe(nation_id="Nation ID for which to calculate the warchest (optional if you're registered)")
    async def warchest(self, interaction: discord.Interaction, nation_id: int = None):
        await self.warchest_logic(interaction, nation_id)

    @commands.command(name="wc")
    async def warchest_prefix(self, ctx, nation_id_or_name: str = None):
        try:
            nation_id = None
            if nation_id_or_name:
                try:
                    nation_id = int(nation_id_or_name)
                except ValueError:
                    await ctx.send(
                        embed=create_embed(
                            title=":warning: Invalid Parameter",
                            description=f"'{nation_id_or_name}' is not a valid nation ID. Please provide a valid nation ID.",
                            color=discord.Color.orange()
                        )
                    )
                    return
            await self.warchest_logic(None, nation_id, ctx=ctx)
        except Exception as e:
            error(f"Error in warchest command: {e}", tag="WARCH")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while processing the warchest command. Please try again later.",
                    color=discord.Color.red()
                )
            )
    
    @app_commands.command(name="bank", description="Check the bank balance of a nation.")
    @app_commands.describe(nation_id="Nation ID to check.")
    async def bank(self, interaction: discord.Interaction, nation_id: int):
        """Check the bank balance of a nation."""
        nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
        nation_name = nation.get("nation_name", "N/A")
        alliance = nation.get("alliance", {})
        alliance_name = alliance.get("name", "None")
        alliance_id = alliance.get("id", "N/A")
        
        header_info = (
            f"**{nation_name} of {alliance_name}**\n"
            f"Nation: {nation_id}-{nation_name} | Alliance: {alliance_name} (ID: {alliance_id})\n"
            f"Score: {nation.get('score', 'N/A')} | Pop: {nation.get('population', 'N/A')} | Leader: {nation.get('leader_name', 'N/A')}\n"
            f"{'-'*85}\n"
        )
        
        bank_balance = nation.get("bank_balance", {})
        bank_text = "\n".join([f"{key}: {value}" for key, value in bank_balance.items() if value > 0])
        
        if not bank_text:
            bank_text = "No funds available."
        
        output = header_info + "\n" + bank_text
        output = "\n" + output + "\n"
        
        await interaction.response.send_message(
            embed=create_embed(
                description=output,
                color=discord.Color.purple()
            )
        )
    
    async def wars_logic(self, interaction, nation_id: int = None, ctx=None):
        try:
            # If no nation_id provided, try to get user's registered nation
            if nation_id is None:
                user_id = interaction.user.id if interaction else ctx.author.id
                nation_id = self.get_user_nation(user_id)
                if nation_id is None:
                    msg = (
                        ":warning: No Nation ID Provided\n"
                        "Please provide a nation ID or register your nation using `/register`."
                    )
                    if interaction:
                        await interaction.response.send_message(msg, ephemeral=True)
                    else:
                        await ctx.send(msg)
                    return
            nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            nation_name = nation.get("nation_name", "N/A")
            alliance = nation.get("alliance", {})
            alliance_name = alliance.get("name", "None")
            alliance_id = alliance.get("id", "N/A")
            header_info = (
                f"**{nation_name} of {alliance_name}**\n"
                f"Nation: {nation_id}-{nation_name} | Alliance: {alliance_name} (ID: {alliance_id})\n"
                f"Score: {nation.get('score', 'N/A')} | Pop: {nation.get('population', 'N/A')} | Leader: {nation.get('leader_name', 'N/A')}\n"
                f"{'-'*85}\n"
            )
            wars_list = nation.get("wars", [])
            offensive_wars = []
            defensive_wars = []
            for war in wars_list:
                try:
                    turns_left = int(war.get("turns_left", 0))
                except Exception:
                    turns_left = 0
                if turns_left <= 0:
                    continue
                attacker_id = int(war.get("attacker", {}).get("id", -1))
                defender_id = int(war.get("defender", {}).get("id", -1))
                if nation_id == attacker_id:
                    offensive_wars.append(war)
                elif nation_id == defender_id:
                    defensive_wars.append(war)
            offensive_wars = offensive_wars[:7]
            defensive_wars = defensive_wars[:3]
            def format_stats(nation):
                s = nation.get("soldiers", 0)
                t = nation.get("tanks", 0)
                a = nation.get("aircraft", 0)
                sh = nation.get("ships", 0)
                return f"🪖{s:>8} 🚜{t:>6} ✈️{a:>4} 🚢{sh:>3}"
            def format_control(war, is_offensive: bool):
                if is_offensive:
                    gc = "AT" if war.get("ground_control", False) else "_"
                    air = "AT" if war.get("air_superiority", False) else "_"
                    nb = "AT" if war.get("naval_blockade", False) else "_"
                    pc = "AT" if war.get("att_peace", False) else "_"
                else:
                    gc = "DF" if war.get("ground_control", False) else "_"
                    air = "DF" if war.get("air_superiority", False) else "_"
                    nb = "DF" if war.get("naval_blockade", False) else "_"
                    pc = "DF" if war.get("def_peace", False) else "_"
                return f"{gc:>2} {air:>2} {nb:>2} {pc:>2}"
            def format_offensive_line(war):
                defender = war.get("defender", {})
                opp = f"{defender.get('id', 'N/A')}"
                opp = opp[:12]
                our_stats = format_stats(war.get("attacker", {}))
                opp_stats = format_stats(defender)
                ctrl = format_control(war, True)
                line = f"{opp:<12} | {opp_stats} | {our_stats} | {ctrl}"
                return line[:85]
            def format_defensive_line(war):
                attacker = war.get("attacker", {})
                opp = f"{attacker.get('id', 'N/A')}-{attacker.get('nation_name', 'Unknown')}"
                opp = opp[:12]
                our_stats = format_stats(war.get("defender", {}))
                opp_stats = format_stats(attacker)
                ctrl = format_control(war, False)
                line = f"{opp:<12} | {our_stats} | {opp_stats} | {ctrl}"
                return line[:85]
            def build_section(wars, is_offensive: bool, title: str):
                if not wars:
                    return f"{title}:\nNo active wars."
                lines = [f"{title}:"]
                lines.append(f"{'ID':<12} | {'Opponent Stats':<30} | {'Our Stats':<30} | {'Control':<8}")
                lines.append("-" * 85)
                for war in wars:
                    if is_offensive:
                        lines.append(format_offensive_line(war))
                    else:
                        lines.append(format_defensive_line(war))
                return "\n".join(lines)
            off_text = build_section(offensive_wars, True, "Offensive Wars")
            def_text = build_section(defensive_wars, False, "Defensive Wars")
            output = header_info + "\n" + off_text + "\n\n" + def_text
            output = "\n" + output + "\n"
            if interaction:
                await interaction.response.send_message(f"```\n{output}\n```")
            else:
                await ctx.send(f"```\n{output}\n```")
        except Exception as e:
            msg = (
                ":warning: An Error Occurred\n"
                f"**An unexpected error occurred while processing the command.**\n\n"
                f"**Error Type:** `{type(e).__name__}`\n"
                f"**Error Message:** {e}\n\n"
                f"Detailed error information has been logged internally. Please contact <@860564164828725299> if this issue persists."
            )
            if interaction:
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.send(msg)

    @app_commands.command(name="wars", description="Check the active wars and military of a nation.")
    @app_commands.describe(nation_id="Nation ID to check (optional if you're registered)")
    async def wars(self, interaction: discord.Interaction, nation_id: int = None):
        await self.wars_logic(interaction, nation_id)

    @commands.command(name="war")
    async def wars_prefix(self, ctx, nation_id_or_name: str = None):
        """Show active wars for a nation based on channel name or provided nation ID/name."""
        try:
            nation_id = None
            
            # If a parameter was provided, try to parse it as an integer
            if nation_id_or_name:
                try:
                    nation_id = int(nation_id_or_name)
                except ValueError:
                    # If it's not a valid integer, try to extract from channel name
                    nation_id = self.extract_war_id_from_channel(ctx.channel.name)
                    if nation_id is None:
                        await ctx.send(
                            embed=create_embed(
                                title=":warning: Invalid Parameter",
                                description=f"'{nation_id_or_name}' is not a valid nation ID. Please provide a valid nation ID or use this command in a channel named like 'war-room-123456'.",
                                color=discord.Color.orange()
                            )
                        )
                        return
            
            # If no nation_id provided, try to extract from channel name
            if nation_id is None:
                nation_id = self.extract_war_id_from_channel(ctx.channel.name)
                if nation_id is None:
                    await ctx.send(
                        embed=create_embed(
                            title=":warning: No Nation ID Found",
                            description="Could not find a nation ID in the channel name. Please provide a nation ID or use this command in a channel named like 'war-room-123456'.",
                            color=discord.Color.orange()
                        )
                    )
                    return
            
            # Get active wars for the nation
            params = {
                "active": True,
                "nation_id": [nation_id],
                "first": 50
            }
            
            wars = get_data.GET_WARS(params, self.config.API_KEY)
            if not wars:
                await ctx.send(
                    embed=create_embed(
                        title=":information_source: No Active Wars",
                        description=f"No active wars found for nation ID {nation_id}.",
                        color=discord.Color.blue()
                    )
                )
                return
            
            # Get nation data for the title
            nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            nation_name = nation.get('nation_name', f'Nation {nation_id}') if nation else f'Nation {nation_id}'
            
            # Format war information
            def format_war_info(war):
                attacker = war.get('attacker', {})
                defender = war.get('defender', {})
                
                # Determine if this nation is attacker or defender
                is_attacker = attacker.get('id') == nation_id
                opponent = defender if is_attacker else attacker
                opponent_name = opponent.get('leader_name', 'N/A')
                opponent_id = opponent.get('id', '')
                
                # Format control status
                ground_control = war.get('ground_control', 'None')
                air_superiority = war.get('air_superiority', 'None')
                naval_blockade = war.get('naval_blockade', 'None')
                
                return [
                    f"**War ID:** {war['id']}",
                    f"**Type:** {war.get('war_type', 'N/A')}",
                    f"**Turns Left:** {war.get('turns_left', 'N/A')}",
                    f"**Reason:** {war.get('reason', 'N/A')}",
                    "",
                    f"**Opponent:** [{opponent_name}](https://politicsandwar.com/nation/id={opponent_id})",
                    f"**Role:** {'Attacker' if is_attacker else 'Defender'}",
                    "",
                    f"**Points:** {war.get('att_points', 0)} vs {war.get('def_points', 0)}",
                    f"**Resistance:** {war.get('att_resistance', 0)}% vs {war.get('def_resistance', 0)}%",
                    "",
                    f"**Control:** {ground_control} Ground | {air_superiority} Air | {naval_blockade} Naval"
                ]
            
            # Create embed with all wars
            embed = create_embed(
                title=f"Active Wars - {nation_name}",
                description=f"Found **{len(wars)}** active wars for [{nation_name}](https://politicsandwar.com/nation/id={nation_id})",
                color=discord.Color.red()
            )
            
            # Add each war as a field
            for i, war in enumerate(wars, 1):
                war_info = format_war_info(war)
                embed.add_field(
                    name=f"War {i}",
                    value="\n".join(war_info),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            info(f"Wars lookup completed by {ctx.author} for nation {nation_id}", tag="WARS")
            
        except Exception as e:
            error(f"Error in wars command: {e}", tag="WARS")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while fetching the wars. Please try again later.",
                    color=discord.Color.red()
                )
            )

    @commands.command(name="w")
    async def who_search_prefix(self, ctx, *, search_term: str = None):
        """Search for registered nations by nation name or discord username."""
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
                        description="Please provide a search term (nation name or discord username).\nExample: `!w joa` or `!w Naturumgibt`",
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
                
                # Check if search term matches nation name or discord name
                if (search_term_lower in nation_name or 
                    search_term_lower in discord_name or
                    nation_name.startswith(search_term_lower) or
                    discord_name.startswith(search_term_lower)):
                    
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
            info(f"Registration search completed by {ctx.author} for term '{search_term}', found {len(matches)} matches", tag="WHO_SEARCH")
            
        except Exception as e:
            error(f"Error in who search command: {e}", tag="WHO_SEARCH")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while searching registrations. Please try again later.",
                    color=discord.Color.red()
                )
            )

    async def who_logic(self, interaction, nation_id: int = None, ctx=None):
        if interaction is not None:
            await interaction.response.defer()
        try:
            # If no nation_id provided, try to get user's registered nation
            user_id = interaction.user.id if interaction else ctx.author.id
            if nation_id is None:
                nation_id = self.get_user_nation(user_id)
                if nation_id is None:
                    msg_embed = create_embed(
                        title=":warning: No Nation ID Provided",
                        description="Please provide a nation ID or register your nation using `/register`.",
                        color=discord.Color.orange()
                    )
                    if interaction:
                        await interaction.followup.send(embed=msg_embed, ephemeral=True)
                    else:
                        await ctx.send(embed=msg_embed)
                    return
            
            # Get nation data
            nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            if not nation:
                error_msg = f"Nation {nation_id} not found."
                if interaction:
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await ctx.send(error_msg)
                return
            
            # Get city data
            cities = get_data.GET_CITY_DATA(nation_id, self.config.API_KEY)
            if not cities:
                error_msg = f"Could not fetch city data for nation {nation_id}."
                if interaction:
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await ctx.send(error_msg)
                return
            
            # Calculate total infrastructure and land
            total_infra = sum(city.get('infrastructure', 0) for city in cities)
            total_land = sum(city.get('land', 0) for city in cities)
            
            # Get continent resources
            continent = nation.get('continent', '').lower()
            continent_resources = {
                'africa': {'oil': 3, 'bauxite': 3, 'uranium': 3},
                'antarctica': {'oil': 3, 'coal': 3, 'uranium': 3},
                'asia': {'oil': 3, 'iron': 3, 'uranium': 3},
                'australia': {'coal': 3, 'bauxite': 3, 'lead': 3},
                'europe': {'coal': 3, 'iron': 3, 'lead': 3},
                'north america': {'coal': 3, 'iron': 3, 'uranium': 3},
                'south america': {'oil': 3, 'bauxite': 3, 'lead': 3}
            }
            
            # Calculate resource production from buildings and continent
            resource_production = {
                'coal': sum(city.get('coal_mine', 0) * 3 for city in cities),
                'oil': sum(city.get('oil_refinery', 0) * 3 for city in cities),
                'uranium': sum(city.get('uranium_mine', 0) * 3 for city in cities),
                'iron': sum(city.get('iron_mine', 0) * 3 for city in cities),
                'bauxite': sum(city.get('bauxite_mine', 0) * 3 for city in cities),
                'lead': sum(city.get('lead_mine', 0) * 3 for city in cities),
                'gasoline': sum(city.get('oil_refinery', 0) * 6 for city in cities),
                'munitions': sum(city.get('munitions_factory', 0) * 18 for city in cities),
                'steel': sum(city.get('steel_mill', 0) * 9 for city in cities),
                'aluminum': sum(city.get('aluminum_refinery', 0) * 9 for city in cities),
                'food': sum(city.get('farm', 0) * (city.get('land', 0) / 500) for city in cities)
            }
            
            # Add continent resource production
            if continent in continent_resources:
                for resource, amount in continent_resources[continent].items():
                    resource_production[resource] += amount * len(cities)
            
            # Get top 3 resource productions
            top_resources = sorted(resource_production.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Get color block based on color
            color = nation.get('color', 'gray').lower()
            color_block = {
                'red': '🟥', 'orange': '🟧', 'yellow': '🟨', 'green': '🟩', 'blue': '🟦',
                'purple': '🟪', 'pink': '💗', 'gray': '⬜', 'black': '⬛', 'brown': '🟫'
            }.get(color, '⬜')
            
            # Handle alliance info safely
            alliance_info = nation.get('alliance', {})
            alliance_name = alliance_info.get('name', 'No Alliance') if alliance_info else 'No Alliance'
            
            # Handle last_active field safely
            last_active = nation.get('last_active')
            if last_active:
                try:
                    # Handle different date formats
                    if last_active.endswith('Z'):
                        last_active = last_active.replace('Z', '+00:00')
                    timestamp = int(datetime.fromisoformat(last_active).timestamp())
                    last_active_str = f"<t:{timestamp}:R>"
                except Exception:
                    last_active_str = "Unknown"
            else:
                last_active_str = "Unknown"
            
            # Format basic info with better emojis and layout
            nation_info = [
                f"**[{nation.get('nation_name', 'N/A')}](https://politicsandwar.com/nation/id={nation_id})**",
                f"👑 **Leader:** {nation.get('leader_name', 'N/A')}",
                f"⭐ **Score:** {nation.get('score', 0):,.2f}",
                f"🏙️ **Cities:** {len(cities)}",
                f"<:population:1357366133233029413> **Population:** {format_number(nation.get('population', 0))}",
                f"🏗️ **Total Infrastructure:** {format_number(total_infra)}",
                f"🌍 **Total Land:** {format_number(total_land)}",
                f"🎨 **Color:** {color_block}",
                "",
                f"**Military:**",
                f"<:military_helmet:1357103044466184412> **Soldiers:** {format_number(nation.get('soldiers', 0))}",
                f"<:tank:1357398163442635063> **Tanks:** {format_number(nation.get('tanks', 0))}",
                f"✈️ **Aircraft:** {format_number(nation.get('aircraft', 0))}",
                f"🚢 **Ships:** {format_number(nation.get('ships', 0))}",
                "",
                f"**Top Resource Production:**",
            ]
            
            # Add top 3 resources with their emojis
            resource_emojis = {
                'coal': '<:coal:1357102730682040410>',
                'oil': '<:oil:1357102740391854140>',
                'uranium': '<:uranium:1357102742799126558>',
                'iron': '<:iron:1357102735488581643>',
                'bauxite': '<:bauxite:1357102729411039254>',
                'lead': '<:lead:1357102736646209536>',
                'gasoline': '<:gasoline:1357102734645399602>',
                'munitions': '<:munitions:1357102777389814012>',
                'steel': '<:steel:1357105344052072618>',
                'aluminum': '<:aluminum:1357102728391819356>',
                'food': '<:food:1357102733571784735>'
            }
            
            for resource, amount in top_resources:
                if amount > 0:
                    emoji = resource_emojis.get(resource, '📦')
                    nation_info.append(f"{emoji} **{resource.title()}:** {format_number(amount)}/day")
            
            nation_info.extend([
                "",
                f"🤝 **Alliance:** {alliance_name}",
                f"⏰ **Last Active:** {last_active_str}"
            ])
            
            embed = create_embed(
                title=f"Nation Information",
                description="\n".join(nation_info),
                color=discord.Color.blue(),
            )
            
            if nation.get('flag'):
                embed.set_thumbnail(url=nation['flag'])
            
            if interaction:
                await interaction.followup.send(embed=embed)
                info(f"Nation lookup completed by {interaction.user}", tag="WHO")
            else:
                await ctx.send(embed=embed)
                info(f"Nation lookup completed by {ctx.author}", tag="WHO")
                
        except Exception as e:
            error(f"Error in who command: {e}", tag="WHO")
            error_embed = create_embed(
                title=":warning: An Error Occurred",
                description=(
                    f"**An unexpected error occurred while processing the command.**\n\n"
                    f"**Error Type:** `{type(e).__name__}`\n"
                    f"**Error Message:** {e}\n\n"
                    f"Detailed error information has been logged internally. Please contact <@860564164828725299> if this issue persists."
                ),
                color=discord.Color.red(),
            )
            if interaction:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            else:
                await ctx.send(embed=error_embed)

    @app_commands.command(name="who", description="Show basic information about a nation.")
    @app_commands.describe(
        nation_id="The ID of the nation to look up (optional if you're registered)"
    )
    async def who(
        self,
        interaction: discord.Interaction,
        nation_id: int = None
    ):
        """Show basic information about a nation."""
        await self.who_logic(interaction, nation_id)

    @commands.command(name="who")
    async def who_prefix(self, ctx, nation_id_or_name: str = None):
        try:
            nation_id = None
            if nation_id_or_name:
                try:
                    nation_id = int(nation_id_or_name)
                except ValueError:
                    await ctx.send(
                        embed=create_embed(
                            title=":warning: Invalid Parameter",
                            description=f"'{nation_id_or_name}' is not a valid nation ID. Please provide a valid nation ID.",
                            color=discord.Color.orange()
                        )
                    )
                    return
            await self.who_logic(None, nation_id, ctx=ctx)
        except Exception as e:
            error(f"Error in who command: {e}", tag="WHO")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while processing the who command. Please try again later.",
                    color=discord.Color.red()
                )
            )

    async def chest_logic(self, interaction, nation_id: int = None, ctx=None):
        # Determine user ID for registration lookup
        user_id = interaction.user.id if interaction else ctx.author.id
        if nation_id is None:
            nation_id = self.get_user_nation(user_id)
            if nation_id is None:
                msg_embed = create_embed(
                    title=":warning: No Nation ID Provided",
                    description="Please provide a nation ID or register your nation using `/register`.",
                    color=discord.Color.orange()
                )
                if interaction:
                    await interaction.response.send_message(embed=msg_embed, ephemeral=True)
                else:
                    await ctx.send(embed=msg_embed)
                return
        nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
        if not nation:
            if interaction:
                await interaction.response.send_message("Nation not found.", ephemeral=True)
            else:
                await ctx.send("Nation not found.")
            return
        # List of resources to display
        resources = [
            ("money", "<:money:1357103044466184412>", "Money"),
            ("coal", "<:coal:1357102730682040410>", "Coal"),
            ("oil", "<:Oil:1357102740391854140>", "Oil"),
            ("uranium", "<:uranium:1357102742799126558>", "Uranium"),
            ("iron", "<:iron:1357102735488581643>", "Iron"),
            ("bauxite", "<:bauxite:1357102729411039254>", "Bauxite"),
            ("lead", "<:lead:1357102736646209536>", "Lead"),
            ("gasoline", "<:gasoline:1357102734645399602>", "Gasoline"),
            ("munitions", "<:munitions:1357102777389814012>", "Munitions"),
            ("steel", "<:steel:1357105344052072618>", "Steel"),
            ("aluminum", "<:aluminum:1357102728391819356>", "Aluminum"),
            ("food", "<:food:1357102733571784735>", "Food"),
            ("credits", "<:credits:1357102732187537459>", "Credits"),
        ]
        lines = []
        for key, emoji, label in resources:
            value = nation.get(key, 0)
            lines.append(f"{emoji} **{label}:** {format_number(value)}")
        embed = create_embed(
            title=f"Resource Chest for {nation.get('nation_name', 'N/A')}",
            description="\n".join(lines),
            color=discord.Color.gold()
        )
        if interaction:
            await interaction.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.command(name="nw")
    async def chest_prefix(self, ctx, nation_id_or_name: str = None):
        try:
            nation_id = None
            if nation_id_or_name:
                try:
                    nation_id = int(nation_id_or_name)
                except ValueError:
                    await ctx.send(
                        embed=create_embed(
                            title=":warning: Invalid Parameter",
                            description=f"'{nation_id_or_name}' is not a valid nation ID. Please provide a valid nation ID.",
                            color=discord.Color.orange()
                        )
                    )
                    return
            await self.chest_logic(None, nation_id, ctx=ctx)
        except Exception as e:
            error(f"Error in chest command: {e}", tag="CHEST")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while processing the chest command. Please try again later.",
                    color=discord.Color.red()
                )
            )
    
    async def raid_logic(self, interaction, nation_id: int = None, ctx=None):
        """Find profitable raid targets within a nation's war range."""
        interaction_responded = False
        try:
            # If no nation_id provided, try to get user's registered nation
            if nation_id is None:
                user_id = interaction.user.id if interaction else ctx.author.id
                nation_id = self.get_user_nation(user_id)
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

            # Get the nation's data from CSV cache
            from bot.csv_cache import get_cache
            cache = get_cache()
            
            # Find the nation in cache
            nation = cache.find_nation_by_id(nation_id)
            if not nation:
                if interaction:
                    await interaction.response.send_message("Nation not found in cache. Try updating the cache first.", ephemeral=True)
                    interaction_responded = True
                else:
                    await ctx.send("Nation not found in cache. Try updating the cache first.")
                return
            
            # Calculate war range
            score = float(nation.get('score', 0))
            min_score = score * 0.75
            max_score = score * 1.75

            # Send initial response to prevent timeout
            if interaction and not interaction_responded:
                await interaction.response.send_message("🔍 Searching for raid targets... This may take a moment!", ephemeral=True)
                interaction_responded = True
            
            # Get all data from cache
            all_nations = cache.get_nations()
            all_cities = cache.get_cities()
            all_wars = cache.get_wars()
            top_60_alliances = cache.get_top_60_alliances()
            
            # Create lookup dictionaries for faster access
            cities_by_nation = {}
            for city in all_cities:
                nation_id_key = city.get('nation_id')
                if nation_id_key not in cities_by_nation:
                    cities_by_nation[nation_id_key] = []
                cities_by_nation[nation_id_key].append(city)
            
            # Count defensive wars for each nation
            defensive_wars_by_nation = {}
            for war in all_wars:
                def_id = war.get('defender_id')
                if def_id not in defensive_wars_by_nation:
                    defensive_wars_by_nation[def_id] = 0
                defensive_wars_by_nation[def_id] += 1

            # Filter potential targets according to your specifications
            valid_targets = []
            total_checked = 0
            filtered_out = {
                'score_range': 0,
                'vmode': 0,
                'beige_turns': 0,
                'top_alliance': 0,
                'defensive_wars': 0,
                'no_cities': 0,
                'low_loot': 0
            }
            
            for target in all_nations:
                if not target:
                    continue
                
                total_checked += 1
                
                # Progress update every 1000 nations
                if total_checked % 1000 == 0:
                    info(f"Filtered {total_checked}/{len(all_nations)} nations... Found {len(valid_targets)} targets so far", tag="RAID")
                    
                target_score = float(target.get('score', 0))
                if not (min_score <= target_score <= max_score):
                    filtered_out['score_range'] += 1
                    continue

                # A) Filter out nations in vmode
                if target.get('vmode', 0) == 1:
                    filtered_out['vmode'] += 1
                    continue

                # A) Filter out nations with beige turns
                if target.get('beige_turns', 0) > 0:
                    filtered_out['beige_turns'] += 1
                    continue

                # A) Filter out nations in top 60 alliances or your alliance
                alliance_id = target.get('alliance_id')
                if alliance_id == 13033 or alliance_id in top_60_alliances:
                    filtered_out['top_alliance'] += 1
                    continue

                # A) Filter out nations with 3+ defensive wars
                defensive_wars = defensive_wars_by_nation.get(target.get('id'), 0)
                if defensive_wars >= 3:
                    filtered_out['defensive_wars'] += 1
                    continue

                # Get cities for this nation
                cities = cities_by_nation.get(target.get('id'), [])
                if not cities:
                    filtered_out['no_cities'] += 1
                    continue

                # Calculate loot potential based on cities and wars
                total_loot_potential = self.calculate_loot_potential(target, cities, [])

                # Only show profitable targets
                if total_loot_potential > 100000:  # Minimum $100k potential loot
                    # Calculate military strength
                    military_strength = (
                        target.get('soldiers', 0) * 0.5 +
                        target.get('tanks', 0) * 5 +
                        target.get('aircraft', 0) * 10 +
                        target.get('ships', 0) * 20
                    )
                    
                    # Calculate total infrastructure
                    total_infra = sum(city.get('infrastructure', 0) for city in cities)
                    
                    valid_targets.append({
                        'nation': target,
                        'score': target_score,
                        'military': military_strength,
                        'profit': total_loot_potential,
                        'cities': len(cities),
                        'alliance_id': alliance_id,
                        'alliance_rank': target.get('alliance_rank', 999),
                        'beige_turns': 0,  # Already filtered out
                        'wars': defensive_wars,
                        'infrastructure': total_infra
                    })
                else:
                    filtered_out['low_loot'] += 1

            # Sort by profit
            valid_targets.sort(key=lambda x: x['profit'], reverse=True)
            
            # Log filtering results
            info(f"Raid filtering results: {total_checked} nations checked", tag="RAID")
            info(f"  - Score range: {filtered_out['score_range']} filtered", tag="RAID")
            info(f"  - Vmode: {filtered_out['vmode']} filtered", tag="RAID")
            info(f"  - Beige turns: {filtered_out['beige_turns']} filtered", tag="RAID")
            info(f"  - Top 60 alliances: {filtered_out['top_alliance']} filtered", tag="RAID")
            info(f"  - 3+ defensive wars: {filtered_out['defensive_wars']} filtered", tag="RAID")
            info(f"  - No cities data: {filtered_out['no_cities']} filtered", tag="RAID")
            info(f"  - Low loot (<$100k): {filtered_out['low_loot']} filtered", tag="RAID")
            info(f"  - Valid targets found: {len(valid_targets)}", tag="RAID")
            
            if not valid_targets:
                msg = (
                    f"**No profitable raid targets found in war range.**\n\n"
                    f"**Search Results:**\n"
                    f"• Nations checked: {total_checked}\n"
                    f"• Score range: {min_score:,.0f} - {max_score:,.0f}\n"
                    f"• Filtered out:\n"
                    f"  - Outside score range: {filtered_out['score_range']}\n"
                    f"  - Vmode: {filtered_out['vmode']}\n"
                    f"  - Beige turns: {filtered_out['beige_turns']}\n"
                    f"  - Top 60 alliances: {filtered_out['top_alliance']}\n"
                    f"  - 3+ defensive wars: {filtered_out['defensive_wars']}\n"
                    f"  - No cities data: {filtered_out['no_cities']}\n"
                    f"  - Low loot: {filtered_out['low_loot']}\n\n"
                    f"**Try:** Lowering the minimum loot threshold or expanding your war range."
                )
                if interaction:
                    if interaction_responded:
                        await interaction.followup.send(msg, ephemeral=True)
                    else:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                else:
                    await ctx.send(msg)
                return

            # Create results message (limit to top 10)
            top_targets = valid_targets[:10]
            result_lines = []
            result_lines.append(f"**Top {len(top_targets)} Raid Targets (Score Range: {min_score:,.0f} - {max_score:,.0f})**\n")
            
            for i, target in enumerate(top_targets, 1):
                nation = target['nation']
                result_lines.append(
                    f"**{i}.** [{nation.get('nation_name', 'Unknown')}](https://politicsandwar.com/nation/id={nation.get('id')}) "
                    f"(ID: {nation.get('id')})"
                )
                result_lines.append(
                    f"    💰 **Loot Potential:** ${target['profit']:,.0f} | "
                    f"⭐ **Score:** {target['score']:,.0f} | "
                    f"🏙️ **Cities:** {target['cities']} | "
                    f"🏗️ **Infra:** {target['infrastructure']:,.0f}"
                )
                result_lines.append(
                    f"    🪖 **Military:** {target['military']:,.0f} | "
                    f"⚔️ **Wars:** {target['wars']} | "
                    f"🤝 **Alliance Rank:** {target['alliance_rank'] or 'None'}"
                )
                if target['beige_turns'] > 0:
                    result_lines.append(f"    🟡 **Beige Turns:** {target['beige_turns']}")
                result_lines.append("")
            
            result_text = "\n".join(result_lines)
            
            # Split into chunks if too long
            if len(result_text) > 2000:
                result_text = result_text[:1900] + "\n... (truncated)"
            
            embed = discord.Embed(
                title="🎯 Raid Targets Found",
                description=result_text,
                color=discord.Color.red()
            )
            embed.add_field(
                name="📊 Search Results",
                value=(
                    f"• Nations checked: {total_checked}\n"
                    f"• Score range: {min_score:,.0f} - {max_score:,.0f}\n"
                    f"• Vmode filtered: {filtered_out['vmode']}\n"
                    f"• Beige turns: {filtered_out['beige_turns']}\n"
                    f"• Top 60 alliances: {filtered_out['top_alliance']}\n"
                    f"• 3+ defensive wars: {filtered_out['defensive_wars']}\n"
                    f"• No cities data: {filtered_out['no_cities']}\n"
                    f"• Low loot: {filtered_out['low_loot']}",
                ),
                inline=False
            )
            
            if interaction:
                if interaction_responded:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    interaction_responded = True
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            error(f"Error in raid command: {e}", tag="RAID")
            msg = (
                ":warning: Error\n"
                "An error occurred while processing the raid command. Please try again later."
            )
            if interaction:
                if not interaction_responded:
                    try:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                    except:
                        pass
                else:
                    try:
                        await interaction.followup.send(msg, ephemeral=True)
                    except:
                        pass
            else:
                try:
                    await ctx.send(msg)
                except:
                    pass
    
    def calculate_loot_potential(self, nation: Dict, cities: List[Dict], wars: List[Dict]) -> float:
        """Calculate potential loot based on cities and war history."""
        try:
            # Base loot from infrastructure
            total_infra = sum(city.get('infrastructure', 0) for city in cities)
            base_loot = total_infra * 0.25  # 25% of infrastructure value
            
            # Building value loot
            building_loot = 0
            for city in cities:
                # Resource buildings
                oil_wells = city.get('oil_well', 0)
                coal_mines = city.get('coal_mine', 0)
                iron_mines = city.get('iron_mine', 0)
                bauxite_mines = city.get('bauxite_mine', 0)
                lead_mines = city.get('lead_mine', 0)
                uranium_mines = city.get('uranium_mine', 0)
                
                # Manufacturing buildings
                oil_refineries = city.get('oil_refinery', 0)
                steel_mills = city.get('steel_mill', 0)
                aluminum_refineries = city.get('aluminum_refinery', 0)
                munitions_factories = city.get('munitions_factory', 0)
                
                # Commerce buildings
                supermarkets = city.get('supermarket', 0)
                banks = city.get('bank', 0)
                shopping_malls = city.get('shopping_mall', 0)
                stadiums = city.get('stadium', 0)
                subways = city.get('subway', 0)
                
                # Military buildings
                barracks = city.get('barracks', 0)
                factories = city.get('factory', 0)
                hangars = city.get('hangar', 0)
                drydocks = city.get('drydock', 0)
                
                # Civil buildings
                police_stations = city.get('police_station', 0)
                hospitals = city.get('hospital', 0)
                recycling_centers = city.get('recycling_center', 0)
                
                # Building values (cost to build)
                building_values = {
                    'oil_well': 1000, 'coal_mine': 1000, 'iron_mine': 9500, 'bauxite_mine': 1000,
                    'lead_mine': 1000, 'uranium_mine': 25000, 'oil_refinery': 45000,
                    'steel_mill': 45000, 'aluminum_refinery': 30000, 'munitions_factory': 35000,
                    'supermarket': 5000, 'bank': 15000, 'shopping_mall': 45000, 'stadium': 100000,
                    'subway': 250000, 'barracks': 3000, 'factory': 15000, 'hangar': 100000,
                    'drydock': 250000, 'police_station': 75000, 'hospital': 100000, 'recycling_center': 125000
                }
                
                city_building_value = (
                    oil_wells * building_values['oil_well'] +
                    coal_mines * building_values['coal_mine'] +
                    iron_mines * building_values['iron_mine'] +
                    bauxite_mines * building_values['bauxite_mine'] +
                    lead_mines * building_values['lead_mine'] +
                    uranium_mines * building_values['uranium_mine'] +
                    oil_refineries * building_values['oil_refinery'] +
                    steel_mills * building_values['steel_mill'] +
                    aluminum_refineries * building_values['aluminum_refinery'] +
                    munitions_factories * building_values['munitions_factory'] +
                    supermarkets * building_values['supermarket'] +
                    banks * building_values['bank'] +
                    shopping_malls * building_values['shopping_mall'] +
                    stadiums * building_values['stadium'] +
                    subways * building_values['subway'] +
                    barracks * building_values['barracks'] +
                    factories * building_values['factory'] +
                    hangars * building_values['hangar'] +
                    drydocks * building_values['drydock'] +
                    police_stations * building_values['police_station'] +
                    hospitals * building_values['hospital'] +
                    recycling_centers * building_values['recycling_center']
                )
                
                building_loot += city_building_value * 0.3  # 30% of building value
            
            # War history bonus
            war_bonus = 1.0
            if wars:
                # Calculate average loot lost in wars
                total_money_lost = 0
                war_count = 0
                for war in wars:
                    # Check if this nation was the defender (lost loot)
                    if war.get('defender_id') == nation.get('id'):
                        money_lost = war.get('def_money_looted', 0) or 0
                        if money_lost > 0:
                            total_money_lost += money_lost
                            war_count += 1
                
                if war_count > 0:
                    avg_money_lost = total_money_lost / war_count
                    if avg_money_lost > 100000:
                        war_bonus = 2.0
                    elif avg_money_lost > 50000:
                        war_bonus = 1.5
                    elif avg_money_lost > 25000:
                        war_bonus = 1.2
                    elif avg_money_lost > 10000:
                        war_bonus = 1.1
            
            # Beige bonus
            beige_bonus = 1.2 if nation.get('beige_turns', 0) > 0 else 1.0
            
            # Total loot potential
            total_loot = (base_loot + building_loot) * war_bonus * beige_bonus
            
            return total_loot
            
        except Exception as e:
            error(f"Error calculating loot potential: {e}", tag="RAID")
            return 0

    async def purge_logic(self, interaction, ctx=None):
        """Find profitable raid targets within a nation's war range with enhanced analysis."""
        interaction_responded = False
        try:
            # If no nation_id provided, try to get user's registered nation
            if nation_id is None:
                user_id = interaction.user.id if interaction else ctx.author.id
                nation_id = self.get_user_nation(user_id)
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

            # Get the nation's data from cache instead of API
            from simple_cache import get_cache
            cache = get_cache()
            if not cache:
                msg = "Cache not initialized. Please try again later."
                if interaction:
                    await interaction.response.send_message(msg, ephemeral=True)
                    interaction_responded = True
                else:
                    await ctx.send(msg)
                return
            
            # Find the nation in cache
            all_nations = cache.get_nations()
            nation = None
            for n in all_nations:
                if str(n.get('id')) == str(nation_id):
                    nation = n
                    break
            
            if not nation:
                if interaction:
                    await interaction.response.send_message("Nation not found in cache.", ephemeral=True)
                    interaction_responded = True
                else:
                    await ctx.send("Nation not found in cache.")
                return
            
            # Calculate war range
            score = float(nation.get('score', 0))
            min_score = score * 0.75
            max_score = score * 1.75

            # Send initial response to prevent timeout
            if interaction and not interaction_responded:
                await interaction.response.send_message("🔍 Searching cached nations for raid targets... This should be fast!", ephemeral=True)
                interaction_responded = True
                info("Sent initial response to prevent timeout", tag="RAID")
            
            # Get user ID for cache update logic
            user_id = interaction.user.id if interaction else ctx.author.id
            info(f"Getting nations from cache for user {user_id}", tag="RAID")
            info(f"Retrieved {len(all_nations) if all_nations else 0} nations from cache", tag="RAID")
            if not all_nations:
                msg = "Could not load nations data from cache. Please try again later."
                if interaction:
                    if interaction_responded:
                        await interaction.followup.send(msg, ephemeral=True)
                    else:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                else:
                    await ctx.send(msg)
                return

            # Get top 60 alliances for filtering
            info("Building top 60 alliances list...", tag="RAID")
            top_alliances = set()
            for target in all_nations:
                alliance = target.get('alliance')
                if alliance and alliance.get('rank', 999) <= 60:
                    top_alliances.add(alliance.get('id'))
            info(f"Found {len(top_alliances)} top 60 alliances", tag="RAID")

            # Filter potential targets
            info("Starting to filter potential raid targets...", tag="RAID")
            valid_targets = []
            total_checked = 0
            filtered_out = {
                'score_range': 0,
                'too_many_wars': 0,
                'top_alliance': 0,
                'no_cities': 0,
                'low_loot': 0
            }
            
            for i, target in enumerate(all_nations):
                if not target:
                    continue
                
                total_checked += 1
                
                # Progress update every 1000 nations
                if total_checked % 1000 == 0:
                    info(f"Filtered {total_checked}/{len(all_nations)} nations... Found {len(valid_targets)} targets so far", tag="RAID")
                    
                target_score = float(target.get('score', 0))
                if not (min_score <= target_score <= max_score):
                    filtered_out['score_range'] += 1
                    continue

                # Check war count (max 2 wars)
                active_wars = target.get('wars', [])
                if len(active_wars) > 2:
                    filtered_out['too_many_wars'] += 1
                    continue

                # Check alliance (skip top 60 alliances and our alliance)
                alliance = target.get('alliance')
                if alliance:
                    alliance_id = alliance.get('id')
                    if alliance_id in top_alliances or alliance_id == 13033:
                        filtered_out['top_alliance'] += 1
                        continue
                    alliance_name = alliance.get('name', 'Unknown')
                    alliance_rank = alliance.get('rank', 999)
                else:
                    alliance_name = 'None'
                    alliance_rank = 999

                # Check cities data - handle both enriched and basic cache
                cities = target.get('cities', [])
                
                # If no cities data (not enriched yet), estimate based on score
                if not cities:
                    # Estimate cities based on score (rough approximation)
                    estimated_cities = max(1, int(target_score / 1000))  # ~1 city per 1000 score
                    total_infra = target_score * 0.8  # Rough infra estimate
                    total_income = total_infra * 100 * 0.2  # Base income estimate
                    total_commerce = min(total_infra / 100, 50)  # Commerce estimate
                    
                    # Estimate building values for loot calculation
                    # Assume average city has various buildings worth significant money
                    estimated_building_value = 0
                    for i in range(estimated_cities):
                        # Estimate buildings per city based on score
                        city_score = target_score / estimated_cities
                        
                        # Resource buildings (mines, wells, etc.)
                        oil_wells = min(int(city_score / 2000), 10)  # Up to 10 oil wells
                        coal_mines = min(int(city_score / 1500), 10)  # Up to 10 coal mines
                        iron_mines = min(int(city_score / 2000), 10)  # Up to 10 iron mines
                        bauxite_mines = min(int(city_score / 2500), 10)  # Up to 10 bauxite mines
                        lead_mines = min(int(city_score / 3000), 10)  # Up to 10 lead mines
                        uranium_mines = min(int(city_score / 5000), 5)  # Up to 5 uranium mines
                        
                        # Manufacturing buildings
                        oil_refineries = min(int(city_score / 4000), 5)  # Up to 5 refineries
                        steel_mills = min(int(city_score / 4000), 5)  # Up to 5 steel mills
                        aluminum_refineries = min(int(city_score / 5000), 5)  # Up to 5 aluminum refineries
                        munitions_factories = min(int(city_score / 6000), 5)  # Up to 5 munitions factories
                        
                        # Commerce buildings
                        supermarkets = min(int(city_score / 1000), 4)  # Up to 4 supermarkets
                        banks = min(int(city_score / 2000), 5)  # Up to 5 banks
                        shopping_malls = min(int(city_score / 3000), 4)  # Up to 4 shopping malls
                        stadiums = min(int(city_score / 5000), 3)  # Up to 3 stadiums
                        subways = min(int(city_score / 8000), 1)  # Up to 1 subway
                        
                        # Military buildings
                        barracks = min(int(city_score / 1000), 5)  # Up to 5 barracks
                        factories = min(int(city_score / 2000), 5)  # Up to 5 factories
                        hangars = min(int(city_score / 3000), 5)  # Up to 5 hangars
                        drydocks = min(int(city_score / 5000), 3)  # Up to 3 drydocks
                        
                        # Civil buildings
                        police_stations = min(int(city_score / 2000), 5)  # Up to 5 police stations
                        hospitals = min(int(city_score / 2500), 5)  # Up to 5 hospitals
                        recycling_centers = min(int(city_score / 4000), 3)  # Up to 3 recycling centers
                        
                        # Calculate total building value (rough estimates)
                        building_values = {
                            'oil_well': 1000, 'coal_mine': 1000, 'iron_mine': 9500, 'bauxite_mine': 1000,
                            'lead_mine': 1000, 'uranium_mine': 25000, 'oil_refinery': 45000,
                            'steel_mill': 45000, 'aluminum_refinery': 30000, 'munitions_factory': 35000,
                            'supermarket': 5000, 'bank': 15000, 'shopping_mall': 45000, 'stadium': 100000,
                            'subway': 250000, 'barracks': 3000, 'factory': 15000, 'hangar': 100000,
                            'drydock': 250000, 'police_station': 75000, 'hospital': 100000, 'recycling_center': 125000
                        }
                        
                        city_building_value = (
                            oil_wells * building_values['oil_well'] +
                            coal_mines * building_values['coal_mine'] +
                            iron_mines * building_values['iron_mine'] +
                            bauxite_mines * building_values['bauxite_mine'] +
                            lead_mines * building_values['lead_mine'] +
                            uranium_mines * building_values['uranium_mine'] +
                            oil_refineries * building_values['oil_refinery'] +
                            steel_mills * building_values['steel_mill'] +
                            aluminum_refineries * building_values['aluminum_refinery'] +
                            munitions_factories * building_values['munitions_factory'] +
                            supermarkets * building_values['supermarket'] +
                            banks * building_values['bank'] +
                            shopping_malls * building_values['shopping_mall'] +
                            stadiums * building_values['stadium'] +
                            subways * building_values['subway'] +
                            barracks * building_values['barracks'] +
                            factories * building_values['factory'] +
                            hangars * building_values['hangar'] +
                            drydocks * building_values['drydock'] +
                            police_stations * building_values['police_station'] +
                            hospitals * building_values['hospital'] +
                            recycling_centers * building_values['recycling_center']
                        )
                        
                        estimated_building_value += city_building_value
                    
                    # Add building value to total_infra for loot calculation
                    total_infra += estimated_building_value / 1000  # Convert to infra equivalent
                else:
                    # Calculate detailed income analysis from actual cities data
                    total_income = 0
                    total_commerce = 0
                    total_infra = 0
                    
                    for city in cities:
                        city_infra = city.get('infrastructure', 0)
                        total_infra += city_infra
                        
                        # Base income per city
                        base_income = city_infra * 100 * 0.2  # $0.20 per population
                        total_income += base_income
                        
                        # Calculate commerce from actual improvements
                        city_commerce = 0
                        
                        # Commerce buildings
                        supermarket = city.get('supermarket', 0)
                        bank = city.get('bank', 0)
                        shopping_mall = city.get('shopping_mall', 0)
                        stadium = city.get('stadium', 0)
                        subway = city.get('subway', 0)
                        
                        # Calculate commerce bonus
                        city_commerce += supermarket * 3  # +3% each
                        city_commerce += bank * 5  # +5% each
                        city_commerce += shopping_mall * 9  # +9% each
                        city_commerce += stadium * 12  # +12% each
                        city_commerce += subway * 8  # +8% each
                        
                        # Cap commerce at 100%
                        city_commerce = min(city_commerce, 100)
                        total_commerce += city_commerce
                        
                        # Apply commerce bonus to income
                        commerce_income = base_income * (city_commerce / 100)
                        total_income += commerce_income

                # Calculate military strength (for display only, no filtering)
                military_strength = (
                    target.get('soldiers', 0) * 0.5 +
                    target.get('tanks', 0) * 5 +
                    target.get('aircraft', 0) * 10 +
                    target.get('ships', 0) * 20
                )

                # Calculate potential loot based on infrastructure and war history
                # Much more realistic loot calculation
                base_loot = total_infra * 0.25  # 25% of infrastructure value (more realistic)
                
                # Add building value directly to loot potential
                if not cities:  # If using estimates
                    building_loot = estimated_building_value * 0.3  # 30% of building value
                    base_loot += building_loot
                
                # Analyze war history for better loot estimation
                war_history_bonus = self.analyze_war_history(target)
                
                # Apply war history bonus to loot calculation
                potential_loot = base_loot * war_history_bonus

                # Only show profitable targets - much lower threshold
                if potential_loot > 100000:  # Minimum $100k potential loot (more realistic)
                    # Check beige status
                    beige_turns = 0
                    if target.get('beige_turns', 0) > 0:
                        beige_turns = target.get('beige_turns', 0)
                    
                    valid_targets.append({
                        'nation': target,
                        'score': target_score,
                        'military': military_strength,
                        'profit': potential_loot,
                        'income': total_income,
                        'commerce': total_commerce,
                        'cities': len(cities) if cities else estimated_cities,
                        'alliance': alliance_name,
                        'alliance_rank': alliance_rank,
                        'beige_turns': beige_turns,
                        'wars': len(active_wars)
                    })
                else:
                    filtered_out['low_loot'] += 1

            # Sort by profit
            valid_targets.sort(key=lambda x: x['profit'], reverse=True)
            
            # Log filtering results
            info(f"Raid filtering results: {total_checked} nations checked", tag="RAID")
            info(f"  - Score range: {filtered_out['score_range']} filtered", tag="RAID")
            info(f"  - Too many wars (>2): {filtered_out['too_many_wars']} filtered", tag="RAID")
            info(f"  - Top 60 alliances: {filtered_out['top_alliance']} filtered", tag="RAID")
            info(f"  - No cities data: {filtered_out['no_cities']} filtered", tag="RAID")
            info(f"  - Low loot (<$50k): {filtered_out['low_loot']} filtered", tag="RAID")
            info(f"  - Valid targets found: {len(valid_targets)}", tag="RAID")
            
            if not valid_targets:
                msg = (
                    f"**No profitable raid targets found in war range.**\n\n"
                    f"**Search Results:**\n"
                    f"• Nations checked: {total_checked}\n"
                    f"• Score range: {min_score:,.0f} - {max_score:,.0f}\n"
                    f"• Filtered out:\n"
                    f"  - Outside score range: {filtered_out['score_range']}\n"
                    f"  - Too many wars: {filtered_out['too_many_wars']}\n"
                    f"  - Top 60 alliances: {filtered_out['top_alliance']}\n"
                    f"  - No cities data: {filtered_out['no_cities']}\n"
                    f"  - Low loot (<$100k): {filtered_out['low_loot']}\n\n"
                    f"**Try:** Lowering the minimum loot threshold or expanding your war range."
                )
                if interaction:
                    if interaction_responded:
                        await interaction.followup.send(msg, ephemeral=True)
                    else:
                        await interaction.response.send_message(msg, ephemeral=True)
                        interaction_responded = True
                else:
                    await ctx.send(msg)
                return

            # Create paginated view
            from bot.utils.paginator import RaidPaginator, RaidView
            paginator = RaidPaginator(valid_targets, per_page=5)
            view = RaidView(paginator, interaction if interaction else ctx)
            
            embed = paginator.get_page(0)
            embed.title = "🎯 Raid Targets"
            embed.description = f"War Range: {min_score:,.0f} - {max_score:,.0f} | Found {len(valid_targets)} targets"

            if interaction:
                if interaction_responded:
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    await interaction.response.send_message(embed=embed, view=view)
                interaction_responded = True  # Always set to True after any response
            else:
                await ctx.send(embed=embed, view=view)

        except Exception as e:
            error(f"Error in raid command: {e}", tag="RAID")
            
            # Only show error to user if we haven't already sent results
            if not interaction_responded:
                msg = (
                    ":warning: An Error Occurred\n"
                    f"**An unexpected error occurred while processing the command.**\n\n"
                    f"**Error Type:** `{type(e).__name__}`\n"
                    f"**Error Message:** {e}\n\n"
                    f"Detailed error information has been logged internally. Please contact <@860564164828725299> if this issue persists."
                )
                if interaction:
                    try:
                        await interaction.response.send_message(msg, ephemeral=True)
                    except Exception:
                        # If all else fails, just log the error
                        error(f"Failed to send error message to user: {e}", tag="RAID")
                else:
                    await ctx.send(msg)
            else:
                # If we already sent results, just log the error silently
                error(f"Error occurred after sending results: {e}", tag="RAID")




    async def purge_logic(self, interaction, ctx=None):
        interaction_responded = False
        try:
            if interaction:
                await interaction.response.defer()
                interaction_responded = True
            # Get all nations with purple color
            nations = get_data.GET_PURGE_NATIONS(self.config.API_KEY)
            if not nations:
                msg = "No purple nations found or error fetching data."
                if interaction:
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await ctx.send(msg)
                return
            # Filter nations: sub-15 cities, not in alliance 13033, not in top 50 alliances
            target_alliance_id = 13033
            valid_targets = []
            for nation in nations:
                if nation is None or not isinstance(nation, dict):
                    warning("Encountered invalid nation entry during purge search", tag="PURGE")
                    continue
                nation_id = nation.get("id")
                if nation_id is None:
                    warning("Nation entry missing 'id' during purge search", tag="PURGE")
                    continue
                alliance = nation.get("alliance", {})
                if not isinstance(alliance, dict):
                    alliance = {}
                alliance_id = alliance.get("id")
                alliance_position = nation.get("alliance_position", "None")  # Get from nation data
                alliance_rank = alliance.get("rank", 999)  # Get alliance rank for top 50 filtering
                
                # Skip if in target alliance
                if alliance_id is not None and int(alliance_id) == target_alliance_id:
                    continue
                
                # Skip if they're in a top 50 alliance (regardless of position)
                if alliance_rank is not None and int(alliance_rank) <= 50:
                    continue
                # Get city data for this nation
                cities = get_data.GET_CITY_DATA(nation_id, self.config.API_KEY)
                await asyncio.sleep(1)  # Avoid API rate limit
                if not isinstance(cities, list) or not cities:
                    continue
                city_count = len(cities)
                # Only include nations with less than 15 cities
                if city_count < 15:
                    valid_targets.append({
                        "nation": nation,
                        "city_count": city_count,
                        "cities": cities
                    })
            if not valid_targets:
                msg = "No valid purge targets found (all purple nations have 15+ cities or are in the target alliance)."
                if interaction:
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await ctx.send(msg)
                return
            # Sort by city count (lowest first for easier targets)
            valid_targets.sort(key=lambda x: x["city_count"])
            
            # Create grid items for pagination
            grid_items = []
            for target in valid_targets:
                nation = target.get("nation", {})
                city_count = target.get("city_count", 0)
                nation_id = nation.get("id", "?") if isinstance(nation, dict) else "?"
                nation_name = nation.get("nation_name", "Unknown") if isinstance(nation, dict) else "Unknown"
                score = nation.get("score", 0) if isinstance(nation, dict) else 0
                alliance = nation.get("alliance", {})
                alliance_name = alliance.get("name", "None") if isinstance(alliance, dict) else "None"
                alliance_position = nation.get("alliance_position", "None") if isinstance(nation, dict) else "None"
                
                # Create clean, organized target entry with nation link
                target_text = (
                    f"**[{nation_name}](https://politicsandwar.com/nation/id={nation_id})** - {nation_id}\n"
                    f"{alliance_name} - {alliance_position}\n"
                    f"Score: {score:,}\n"
                    f"Cities: {city_count}\n\n"
                )
                grid_items.append({"content": target_text})
            
            # Use GridPaginator for proper grid display
            grid_paginator = GridPaginator(grid_items, items_per_page=4, items_per_row=2)
            
            if grid_paginator.total_pages > 1:
                # Create custom pagination view for GridPaginator
                class PurgeView(discord.ui.View):
                    def __init__(self, grid_paginator, title, description, color):
                        super().__init__(timeout=300)
                        self.grid_paginator = grid_paginator
                        self.current_page = 0
                        self.title = title
                        self.description = description
                        self.color = color
                        self.update_buttons()
                    
                    def update_buttons(self):
                        """Update button states based on current page."""
                        self.previous_button.disabled = self.current_page == 0
                        self.next_button.disabled = self.current_page == self.grid_paginator.total_pages - 1
                    
                    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.gray)
                    async def previous_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        if self.current_page > 0:
                            self.current_page -= 1
                            self.update_buttons()
                            embed = self.grid_paginator.create_grid_embed(
                                self.current_page, self.title, self.description, self.color
                            )
                            await button_interaction.response.edit_message(embed=embed, view=self)
                    
                    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.gray)
                    async def next_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        if self.current_page < self.grid_paginator.total_pages - 1:
                            self.current_page += 1
                            self.update_buttons()
                            embed = self.grid_paginator.create_grid_embed(
                                self.current_page, self.title, self.description, self.color
                            )
                            await button_interaction.response.edit_message(embed=embed, view=self)
                
                view = PurgeView(
                    grid_paginator,
                    "Purge Targets",
                    f"Found **{len(valid_targets)}** valid targets",
                    discord.Color.purple()
                )
                embed = grid_paginator.create_grid_embed(
                    0, 
                    "Purge Targets",
                    f"Found **{len(valid_targets)}** valid targets",
                    discord.Color.purple()
                )
                
                if interaction:
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    await ctx.send(embed=embed, view=view)
            else:
                # No pagination needed
                embed = grid_paginator.create_grid_embed(
                    0, 
                    "Purge Targets",
                    f"Found **{len(valid_targets)}** valid targets",
                    discord.Color.purple()
                )
                
                if interaction:
                    await interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
            
            info(f"Purge command executed by {interaction.user if interaction else ctx.author}, found {len(valid_targets)} targets", tag="PURGE")
        except Exception as e:
            error(f"Error in purge command: {e}", tag="PURGE")
            msg = "An error occurred while searching for purge targets."
            if interaction:
                try:
                    await interaction.followup.send(msg, ephemeral=True)
                except Exception:
                    pass
            elif not interaction:
                await ctx.send(msg)

    @app_commands.command(name="purge", description="Find purge targets: purple nations with <15 cities, not in alliance 13033.")
    async def purge(self, interaction: discord.Interaction):
        await self.purge_logic(interaction)

    @commands.command(name="purge")
    async def purge_prefix(self, ctx):
        await self.purge_logic(None, ctx=ctx)

    async def counter_logic(self, interaction, target_nation_id: int, ctx=None):
        interaction_responded = False
        try:
            if interaction:
                await interaction.response.defer()
                interaction_responded = True
            
            # Get target nation data
            target_nation = get_data.GET_NATION_DATA(target_nation_id, self.config.API_KEY)
            if not target_nation:
                msg = f"Nation {target_nation_id} not found."
                if interaction:
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await ctx.send(msg)
                return
            
            target_score = target_nation.get("score", 0)
            target_name = target_nation.get("nation_name", "Unknown")
            
            # Load registrations like !w command
            from bot.cogs.user import UserCog  # Avoid circular import at top
            user_cog = self.bot.get_cog('UserCog')
            if not user_cog:
                msg = "UserCog not loaded."
                if interaction:
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await ctx.send(msg)
                return
            registrations = user_cog.load_registrations()
            
            # Find members within war range (-50% to 150% of target score)
            min_score = target_score * 0.5   # -50% = 50% of target score
            max_score = target_score * 1.5   # 150% of target score
            valid_counters = []
            
            info(f"Looking for counters for {target_name} (Score: {target_score:.2f}, Range: {min_score:.2f}-{max_score:.2f})", tag="COUNTER")
            info(f"Total registrations to check: {len(registrations)}", tag="COUNTER")
            
            for discord_id, reg in registrations.items():
                if isinstance(reg, dict):
                    nation_id = reg.get('nation_id')
                    if not nation_id:
                        continue
                    
                    # Get nation data to check score and alliance
                    nation_data = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
                    if not nation_data:
                        info(f"Could not fetch nation data for {reg.get('nation_name', 'Unknown')} ({nation_id})", tag="COUNTER")
                        continue
                    
                    # Check if they're not an applicant (all registered nations are assumed to be in alliance 13033)
                    alliance_position = nation_data.get("alliance_position", "None")
                    if alliance_position == "APPLICANT":
                        info(f"Skipping {reg.get('nation_name', 'Unknown')} - is applicant", tag="COUNTER")
                        continue
                    
                    member_score = nation_data.get("score", 0)
                    info(f"Checking registered member {reg.get('nation_name', 'Unknown')} with score {member_score} against range {min_score:.2f}-{max_score:.2f}", tag="COUNTER")
                    
                    if min_score <= member_score <= max_score:
                        info(f"Found valid counter: {reg.get('nation_name', 'Unknown')} with score {member_score}", tag="COUNTER")
                        valid_counters.append({
                            "registration": reg,
                            "nation_data": nation_data,
                            "score": member_score,
                            "score_diff": abs(member_score - target_score)
                        })
                    else:
                        info(f"Score out of range: {reg.get('nation_name', 'Unknown')} with score {member_score}", tag="COUNTER")
            
            info(f"Found {len(valid_counters)} valid counters", tag="COUNTER")
            
            if not valid_counters:
                msg = f"No registered alliance members found within war range of {target_name} (Score: {target_score:,.2f}, Range: {min_score:,.2f}-{max_score:,.2f})."
                if interaction:
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await ctx.send(msg)
                return
            
            # Sort by closest score difference
            valid_counters.sort(key=lambda x: x["score_diff"])
            
            # Format like !w command with simple fields
            embed = discord.Embed(
                title=f"Counter Targets for {target_name}",
                description=f"Found **{len(valid_counters)}** registered members within war range (Score: {target_score:,.2f})",
                color=discord.Color.blue()
            )
            
            # Collect all results into a single string
            result_lines = []
            for counter in valid_counters:
                reg = counter.get("registration", {})
                nation_data = counter.get("nation_data", {})
                nation_id = reg.get("nation_id", "?")
                nation_name = reg.get("nation_name", "Unknown")
                leader_name = nation_data.get("leader_name", "Unknown")
                discord_name = reg.get("discord_name", "N/A")
                score = counter.get("score", 0)
                alliance_position = nation_data.get("alliance_position", "None")
                
                # Create user mention and nation link like !w command
                user_mention = f"<@{list(registrations.keys())[list(registrations.values()).index(reg)]}>"
                nation_link = f"[{leader_name}-{nation_name}](https://politicsandwar.com/nation/id={nation_id})"
                
                # Format line exactly like !w command
                line = f"{user_mention} | {nation_link} ({nation_id}) | Score: {score:,.2f}"
                result_lines.append(line)
            
            # Add all results to description
            embed.description += f"\n\n" + "\n".join(result_lines)
            
            if interaction:
                await interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)
            
            info(f"Counter command executed by {interaction.user if interaction else ctx.author}, found {len(valid_counters)} counters for {target_name}", tag="COUNTER")
        except Exception as e:
            error(f"Error in counter command: {e}", tag="COUNTER")
            msg = "An error occurred while searching for counter targets."
            if interaction:
                try:
                    await interaction.followup.send(msg, ephemeral=True)
                except Exception:
                    pass
            elif not interaction:
                await ctx.send(msg)

    @app_commands.command(name="counter", description="Find alliance members within war range of a target nation.")
    @app_commands.describe(target_nation_id="The ID of the target nation to find counters for")
    async def counter(self, interaction: discord.Interaction, target_nation_id: int):
        await self.counter_logic(interaction, target_nation_id)

    @commands.command(name="c")
    async def counter_prefix(self, ctx, target_nation_id_or_name: str = None):
        """Find alliance members within war range of a target nation based on channel name or provided nation ID."""
        try:
            target_nation_id = None
            
            # If a parameter was provided, try to parse it as an integer
            if target_nation_id_or_name:
                try:
                    target_nation_id = int(target_nation_id_or_name)
                except ValueError:
                    # If it's not a valid integer, try to extract from channel name
                    target_nation_id = self.extract_war_id_from_channel(ctx.channel.name)
                    if target_nation_id is None:
                        await ctx.send(
                            embed=create_embed(
                                title=":warning: Invalid Parameter",
                                description=f"'{target_nation_id_or_name}' is not a valid nation ID. Please provide a valid nation ID or use this command in a channel named like 'war-room-123456'.",
                                color=discord.Color.orange()
                            )
                        )
                        return
            
            # If no target_nation_id provided, try to extract from channel name
            if target_nation_id is None:
                target_nation_id = self.extract_war_id_from_channel(ctx.channel.name)
                if target_nation_id is None:
                    await ctx.send(
                        embed=create_embed(
                            title=":warning: No Nation ID Found",
                            description="Could not find a nation ID in the channel name. Please provide a nation ID or use this command in a channel named like 'war-room-123456'.",
                            color=discord.Color.orange()
                        )
                    )
                    return
            
            await self.counter_logic(None, target_nation_id, ctx=ctx)
            
        except Exception as e:
            error(f"Error in counter command: {e}", tag="COUNTER")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while processing the counter command. Please try again later.",
                    color=discord.Color.red()
                )
            )

    @commands.command(name="wr")
    @commands.has_permissions(manage_channels=True)
    async def war_room(self, ctx, nation_id_or_name: str):
        """Create a war room channel for a specific nation."""
        try:
            nation_id = None
            if nation_id_or_name:
                try:
                    nation_id = int(nation_id_or_name)
                except ValueError:
                    await ctx.send(
                        embed=create_embed(
                            title=":warning: Invalid Parameter",
                            description=f"'{nation_id_or_name}' is not a valid nation ID. Please provide a valid nation ID.",
                            color=discord.Color.orange()
                        )
                    )
                    return
            
            # Get nation data
            nation_data = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            if not nation_data:
                await ctx.send(f"Nation {nation_id} not found.")
                return
            
            nation_name = nation_data.get("nation_name", "Unknown")
            leader_name = nation_data.get("leader_name", "Unknown")
            
            # Create channel name (sanitized for Discord)
            channel_name = f"war-{nation_name.lower().replace(' ', '-').replace('_', '-')}-{nation_id}"
            # Remove any characters that aren't allowed in Discord channel names
            channel_name = ''.join(c for c in channel_name if c.isalnum() or c in '-')
            # Ensure it starts with a letter or number
            if not channel_name[0].isalnum():
                channel_name = 'war-' + channel_name
            
            # Check if channel already exists
            existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
            if existing_channel:
                await ctx.send(f"War room channel `{channel_name}` already exists.")
                return
            
            # Find or create the war room category
            category_name = "War Rooms"
            category = discord.utils.get(ctx.guild.categories, name=category_name)
            
            if not category:
                # Create the category
                category = await ctx.guild.create_category(
                    name=category_name,
                    reason="War room category creation"
                )
                
                # Set permissions for the category - only role 1279671433085190195 can view
                role = ctx.guild.get_role(1279671433085190195)
                if role:
                    await category.set_permissions(ctx.guild.default_role, view_channel=False)
                    await category.set_permissions(role, view_channel=True, send_messages=True, read_message_history=True)
                else:
                    await ctx.send("Warning: Role 1279671433085190195 not found. Category created with default permissions.")
            
            # Create the war room channel
            channel = await ctx.guild.create_text_channel(
                name=channel_name,
                category=category,
                reason=f"War room for {nation_name} ({nation_id})"
            )
            
            # Create embed with nation info
            alliance_info = nation_data.get('alliance')
            alliance_name = alliance_info.get('name', 'No Alliance') if alliance_info else 'No Alliance'
            
            # Handle last_active field safely
            last_active = nation_data.get('last_active')
            if last_active:
                try:
                    # Handle different date formats
                    if last_active.endswith('Z'):
                        last_active = last_active.replace('Z', '+00:00')
                    timestamp = int(datetime.fromisoformat(last_active).timestamp())
                    last_active_str = f"<t:{timestamp}:R>"
                except Exception:
                    last_active_str = "Unknown"
            else:
                last_active_str = "Unknown"
            
            embed = create_embed(
                title=f"War Room: {nation_name}",
                description=(
                    f"**Leader:** {leader_name}\n"
                    f"**Nation ID:** {nation_id}\n"
                    f"**Score:** {nation_data.get('score', 0):,.2f}\n"
                    f"**Alliance:** {alliance_name}\n"
                    f"**Last Active:** {last_active_str}"
                ),
                color=discord.Color.red(),
                footer=f"War room created by {ctx.author.display_name}"
            )
            
            # Send the embed to the new channel
            await channel.send(embed=embed)
            
            # Confirm creation with link to the channel
            await ctx.send(f"War room channel {channel.mention} created successfully!")
            
            info(f"War room created by {ctx.author} for nation {nation_name} ({nation_id})", tag="WAR_ROOM")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create channels or manage permissions.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Error creating war room: {e}")
        except Exception as e:
            error(f"Error in war room command: {e}", tag="WAR_ROOM")
            await ctx.send("❌ An error occurred while creating the war room.")

    async def raid_logic(self, interaction: discord.Interaction, nation_id: int = None):
        """Find profitable raid targets within your war range using API wrappers."""
        interaction_responded = False
        try:
            from bot.csv_cache import get_cache
            
            cache = get_cache()
            if not cache:
                await interaction.response.send_message("❌ Cache system not initialized. Please contact an administrator.", ephemeral=True)
                interaction_responded = True
                return
            
            # Get user's nation data
            if not nation_id:
                # Try to get from registration
                user_id = interaction.user.id
                try:
                    with open('data/registrations.json', 'r') as f:
                        registration_data = json.load(f)
                    if str(user_id) not in registration_data:
                        await interaction.response.send_message("❌ You must register your nation ID first using `/nation register <nation_id>`.", ephemeral=True)
                        interaction_responded = True
                        return
                    nation_id = registration_data[str(user_id)]['nation_id']
                except (FileNotFoundError, KeyError, json.JSONDecodeError):
                    await interaction.response.send_message("❌ You must register your nation ID first using `/nation register <nation_id>`.", ephemeral=True)
                    interaction_responded = True
                    return
            
            # Get user's nation data from API for real-time score
            try:
                user_nation_data = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
                if not user_nation_data:
                    await interaction.response.send_message(f"❌ Nation with ID {nation_id} not found.", ephemeral=True)
                    interaction_responded = True
                    return
                
                # Calculate war range (75% to 133% of user's score)
                user_score = float(user_nation_data.get('score', 0))
                min_score = user_score * 0.75
                max_score = user_score * 1.33
                
            except Exception as e:
                await interaction.response.send_message(f"❌ Error fetching your nation data: {str(e)}", ephemeral=True)
                interaction_responded = True
                return
            
            # Send initial response to prevent timeout
            interaction_responded = False
            if interaction and not interaction_responded:
                await interaction.response.send_message("🔍 Searching for raid targets... This may take a moment!", ephemeral=True)
                interaction_responded = True
            
            # Get data from cache for initial filtering and city data
            all_nations = cache.get_nations()
            all_cities = cache.get_cities()
            top_60_alliances = cache.get_top_60_alliances()
            
            # Create lookup dictionaries for faster access
            cities_by_nation = {}
            for city in all_cities:
                nation_id_key = city.get('nation_id')
                if nation_id_key not in cities_by_nation:
                    cities_by_nation[nation_id_key] = []
                cities_by_nation[nation_id_key].append(city)

            # Filter potential targets using API wrappers for real-time data
            valid_targets = []
            total_checked = 0
            filtered_out = {
                'score_range': 0,
                'vmode': 0,
                'beige_turns': 0,
                'top_alliance': 0,
                'defensive_wars': 0,
                'no_cities': 0,
                'low_loot': 0,
                'api_error': 0
            }
            
            for target in all_nations:
                if not target:
                    continue
                
                total_checked += 1
                
                # Progress update every 1000 nations
                if total_checked % 1000 == 0:
                    info(f"Filtered {total_checked}/{len(all_nations)} nations... Found {len(valid_targets)} targets so far", tag="RAID")
                    
                target_score = float(target.get('score', 0))
                if not (min_score <= target_score <= max_score):
                    filtered_out['score_range'] += 1
                    continue

                # First pass: Use cached data for initial filtering
                # A) Filter out nations in vmode (cached check)
                if target.get('vmode', 0) == 1:
                    filtered_out['vmode'] += 1
                    continue

                # A) Filter out nations with beige turns (cached check)
                if target.get('beige_turns', 0) > 0:
                    filtered_out['beige_turns'] += 1
                    continue

                # A) Filter out nations in top 60 alliances or your alliance
                alliance_id = target.get('alliance_id')
                if alliance_id == 13033 or alliance_id in top_60_alliances:
                    filtered_out['top_alliance'] += 1
                    continue

                # Get cities for this nation from cache
                cities = cities_by_nation.get(target.get('id'), [])
                if not cities:
                    filtered_out['no_cities'] += 1
                    continue

                # Calculate loot potential based on cities and wars
                total_loot_potential = self.calculate_loot_potential(target, cities, [])

                # Only make API calls for potentially profitable targets
                if total_loot_potential > 100000:  # Minimum $100k potential loot
                    # Get real-time data from API for final verification
                    try:
                        target_id = target.get('id')
                        real_time_data = get_data.GET_NATION_DATA(target_id, self.config.API_KEY)
                        if not real_time_data:
                            filtered_out['api_error'] = filtered_out.get('api_error', 0) + 1
                            continue
                        
                        # Final verification with real-time data
                        if real_time_data.get('vmode', 0) == 1:
                            filtered_out['vmode'] += 1
                            continue

                        if real_time_data.get('beige_turns', 0) > 0:
                            filtered_out['beige_turns'] += 1
                            continue

                        # Check defensive wars with real-time data
                        defensive_wars = real_time_data.get('defensive_wars', 0)
                        if defensive_wars >= 3:
                            filtered_out['defensive_wars'] += 1
                            continue

                        # Calculate military strength from real-time data
                        military_strength = (
                            real_time_data.get('soldiers', 0) * 0.5 +
                            real_time_data.get('tanks', 0) * 5 +
                            real_time_data.get('aircraft', 0) * 10 +
                            real_time_data.get('ships', 0) * 20
                        )
                        
                        # Calculate total infrastructure
                        total_infra = sum(city.get('infrastructure', 0) for city in cities)
                        
                        valid_targets.append({
                            'nation': real_time_data,  # Use real-time data
                            'score': target_score,
                            'military': military_strength,
                            'profit': total_loot_potential,
                            'cities': len(cities),
                            'alliance_id': alliance_id,
                            'alliance_rank': real_time_data.get('alliance_rank', 999),
                            'beige_turns': real_time_data.get('beige_turns', 0),
                            'wars': defensive_wars,
                            'infrastructure': total_infra
                        })

                    except Exception as e:
                        # If API call fails, skip this target
                        filtered_out['api_error'] = filtered_out.get('api_error', 0) + 1
                        if filtered_out['api_error'] <= 5:  # Only log first 5 errors to avoid spam
                            info(f"API error for nation {target_id}: {str(e)}", tag="RAID")
                        continue
                else:
                    filtered_out['low_loot'] += 1

            # Sort by profit
            valid_targets.sort(key=lambda x: x['profit'], reverse=True)
            
            # Log filtering results
            info(f"Raid filtering results: {total_checked} nations checked", tag="RAID")
            info(f"  - Score range: {filtered_out['score_range']} filtered", tag="RAID")
            info(f"  - Vmode: {filtered_out['vmode']} filtered", tag="RAID")
            info(f"  - Beige turns: {filtered_out['beige_turns']} filtered", tag="RAID")
            info(f"  - Top 60 alliances: {filtered_out['top_alliance']} filtered", tag="RAID")
            info(f"  - 3+ defensive wars: {filtered_out['defensive_wars']} filtered", tag="RAID")
            info(f"  - No cities data: {filtered_out['no_cities']} filtered", tag="RAID")
            info(f"  - Low loot (<$100k): {filtered_out['low_loot']} filtered", tag="RAID")
            info(f"  - API errors: {filtered_out.get('api_error', 0)} filtered", tag="RAID")
            info(f"  - Valid targets found: {len(valid_targets)}", tag="RAID")
            
            if not valid_targets:
                msg = (
                    f"**No profitable raid targets found in war range.**\n\n"
                    f"**Search Results:**\n"
                    f"• Nations checked: {total_checked}\n"
                    f"• Score range: {min_score:,.0f} - {max_score:,.0f}\n"
                    f"• Filtered out:\n"
                    f"  - Outside score range: {filtered_out['score_range']}\n"
                    f"  - Vmode: {filtered_out['vmode']}\n"
                    f"  - Beige turns: {filtered_out['beige_turns']}\n"
                    f"  - Top 60 alliances: {filtered_out['top_alliance']}\n"
                    f"  - 3+ defensive wars: {filtered_out['defensive_wars']}\n"
                    f"  - No cities data: {filtered_out['no_cities']}\n"
                    f"  - Low loot potential: {filtered_out['low_loot']}\n"
                    f"  - API errors: {filtered_out.get('api_error', 0)}\n\n"
                    f"Try adjusting your search criteria or check back later!"
                )
                
                if interaction and not interaction_responded:
                    await interaction.response.send_message(msg, ephemeral=True)
                else:
                    await interaction.followup.send(msg, ephemeral=True)
                return
            
            # Create embed with top targets
            embed = discord.Embed(
                title="🎯 Raid Targets Found",
                description=f"**War Range:** {min_score:,.0f} - {max_score:,.0f} score",
                color=0x00ff00
            )
            
            # Show top 10 targets
            for i, target in enumerate(valid_targets[:10]):
                nation = target['nation']
                profit = target['profit']
                military = target['military']
                cities = target['cities']
                alliance_rank = target['alliance_rank']
                wars = target['wars']
                infra = target['infrastructure']
                
                # Format alliance info
                if alliance_rank == 999:
                    alliance_info = "No Alliance"
                else:
                    alliance_info = f"#{alliance_rank}"
                
                # Format military strength
                if military < 1000:
                    military_str = f"{military:,.0f}"
                elif military < 1000000:
                    military_str = f"{military/1000:.1f}K"
                else:
                    military_str = f"{military/1000000:.1f}M"
                
                embed.add_field(
                    name=f"#{i+1} {nation.get('name', 'Unknown')}",
                    value=(
                        f"**Score:** {target['score']:,.0f}\n"
                        f"**Profit:** ${profit:,.0f}\n"
                        f"**Military:** {military_str}\n"
                        f"**Cities:** {cities} | **Infra:** {infra:,.0f}\n"
                        f"**Alliance:** {alliance_info} | **Wars:** {wars}"
                    ),
                    inline=False
                )
            
            # Add footer with summary
            embed.set_footer(
                text=(
                    f"Showing top 10 of {len(valid_targets)} targets | "
                    f"Checked {total_checked:,} nations | "
                    f"API errors: {filtered_out.get('api_error', 0)}"
                )
            )
            
            if interaction and not interaction_responded:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            error_msg = f"❌ Error in raid logic: {str(e)}"
            info(error_msg, tag="RAID")
            if interaction and not interaction_responded:
                await interaction.response.send_message(error_msg, ephemeral=True)
            else:
                await interaction.followup.send(error_msg, ephemeral=True)

class NationGroup(app_commands.Group):
    def __init__(self, cog):
        super().__init__(name="nation", description="Nation-related commands")
        self.cog = cog

    @app_commands.command(name="chest", description="Show the current amount of resources on a nation.")
    @app_commands.describe(nation_id="The nation ID to check (optional if you're registered)")
    async def chest(self, interaction: discord.Interaction, nation_id: int = None):
        await self.cog.chest_logic(interaction, nation_id)
    
    @app_commands.command(name="update_cache", description="Update the CSV cache with latest data from Politics and War.")
    async def update_cache(self, interaction: discord.Interaction):
        """Update the CSV cache with latest data."""
        # Check if user is admin
        if interaction.user.id != 860564164828725299:  # Your Discord ID
            await interaction.response.send_message("❌ This command can only be used by Ivy.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            from bot.csv_cache import get_cache
            cache = get_cache()
            
            # Progress callback function
            async def progress_callback(message):
                try:
                    await interaction.followup.send(message, ephemeral=True)
                except:
                    pass  # Ignore errors updating progress
            
            # Update cache
            success = await cache.download_csv_data(progress_callback)
            
            if success:
                cache_info = cache.get_cache_info()
                embed = discord.Embed(
                    title="✅ Cache Update Complete",
                    color=discord.Color.green(),
                    description=f"Successfully updated CSV cache with latest data from Politics and War."
                )
                embed.add_field(name="Wars", value=f"{cache_info['wars_count']:,} records", inline=True)
                embed.add_field(name="Cities", value=f"{cache_info['cities_count']:,} records", inline=True)
                embed.add_field(name="Nations", value=f"{cache_info['nations_count']:,} records", inline=True)
                embed.add_field(name="Last Update", value=cache_info['last_update'] or "Never", inline=False)
                embed.add_field(name="File Size", value=f"{cache_info['file_size'] / 1024 / 1024:.1f} MB", inline=True)
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Failed to update cache. Check logs for details.")
                
        except Exception as e:
            error(f"Error in update_cache command: {e}", tag="CACHE")
            await interaction.followup.send(f"❌ Error updating cache: {str(e)}")
    
    @app_commands.command(name="force_update", description="Force update both CSV and nation caches immediately.")
    async def force_update(self, interaction: discord.Interaction):
        """Force update both caches immediately."""
        # Check if user is admin
        if interaction.user.id != 860564164828725299:  # Your Discord ID
            await interaction.response.send_message("❌ This command can only be used by Ivy.")
            return
        
        await interaction.response.defer()
        
        try:
            # Progress callback function
            async def progress_callback(message):
                try:
                    embed = discord.Embed(
                        title="🔄 Force Updating Caches",
                        description=message,
                        color=discord.Color.blue()
                    )
                    await interaction.edit_original_response(embed=embed)
                except:
                    pass  # Ignore errors updating progress
            
            # Update CSV cache
            await progress_callback("🔄 **Step 1/2:** Updating CSV cache...")
            from bot.csv_cache import get_cache
            csv_cache = get_cache()
            csv_success = await csv_cache.download_csv_data(progress_callback)
            
            # Update nation cache
            await progress_callback("🔄 **Step 2/2:** Updating nation cache...")
            from bot.nation_cache import get_nation_cache
            nation_cache = get_nation_cache()
            nation_success = await nation_cache.update_cache(progress_callback)
            
            if csv_success and nation_success:
                csv_info = csv_cache.get_cache_info()
                nation_info = nation_cache.get_cache_info()
                
                embed = discord.Embed(
                    title="✅ Force Update Complete",
                    color=discord.Color.green(),
                    description="Successfully updated both CSV and nation caches."
                )
                embed.add_field(name="CSV Cache", value=f"{csv_info['wars_count']:,} wars, {csv_info['cities_count']:,} cities, {csv_info['nations_count']:,} nations", inline=False)
                embed.add_field(name="Nation Cache", value=f"{nation_info['nations_count']:,} nations with detailed data", inline=False)
                embed.add_field(name="File Sizes", value=f"CSV: {csv_info['file_size'] / 1024 / 1024:.1f} MB\nNation: {nation_info['file_size'] / 1024 / 1024:.1f} MB", inline=True)
                embed.add_field(name="Last Update", value=nation_info['last_update'] or "Never", inline=True)
                
                await interaction.edit_original_response(embed=embed)
            else:
                await interaction.edit_original_response(content="❌ Failed to update one or both caches. Check logs for details.")
                
        except Exception as e:
            error(f"Error in force_update command: {e}", tag="CACHE")
            await interaction.edit_original_response(content=f"❌ Error force updating caches: {str(e)}")
    
    @app_commands.command(name="raid", description="Find profitable raid targets within your war range.")
    @app_commands.describe(nation_id="The ID of the nation to check (optional if you're registered)")
    async def raid(self, interaction: discord.Interaction, nation_id: int = None):
        """Find profitable raid targets within your war range."""
        # Use the enhanced raid system
        from bot.enhanced_raid import enhanced_raid_logic
        
        # Get user's nation data to determine score range
        if nation_id is None:
            # Get user's nation ID from their registration
            user_id = str(interaction.user.id)
            user_nation_id = self.cog.get_user_nation(user_id)
            if not user_nation_id:
                await interaction.response.send_message("❌ You need to register your nation first! Use `/register` command.", ephemeral=True)
                return
            nation_id = user_nation_id
        
        # Get nation data to determine score range
        try:
            from bot.data import GET_NATION_DATA
            nation_data = GET_NATION_DATA(nation_id, self.cog.config.API_KEY)
            if not nation_data:
                await interaction.response.send_message("❌ Could not find your nation data.", ephemeral=True)
                return
            
            user_score = float(nation_data.get('score', 0))
            min_score = user_score * 0.75
            max_score = user_score * 1.25
            
            # Defer the response
            await interaction.response.defer()
            
            # Use enhanced raid logic
            embed, view = await enhanced_raid_logic(interaction, min_score, max_score)
            if view:
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error finding raid targets: {str(e)}", ephemeral=True)
    
    async def raid_logic(self, interaction: discord.Interaction, nation_id: int = None):
        """Find profitable raid targets within your war range using API wrappers."""
        interaction_responded = False
        try:
            from bot.csv_cache import get_cache
            
            cache = get_cache()
            if not cache:
                await interaction.response.send_message("❌ Cache system not initialized. Please contact an administrator.", ephemeral=True)
                interaction_responded = True
                return
            
            # Get user's nation data
            if not nation_id:
                # Try to get from registration
                user_id = interaction.user.id
                try:
                    with open('data/registrations.json', 'r') as f:
                        registration_data = json.load(f)
                    if str(user_id) not in registration_data:
                        await interaction.response.send_message("❌ You must register your nation ID first using `/nation register <nation_id>`.", ephemeral=True)
                        interaction_responded = True
                        return
                    nation_id = registration_data[str(user_id)]['nation_id']
                except (FileNotFoundError, KeyError, json.JSONDecodeError):
                    await interaction.response.send_message("❌ You must register your nation ID first using `/nation register <nation_id>`.", ephemeral=True)
                    interaction_responded = True
                    return
            
            # Get user's nation data from API for real-time score
            try:
                user_nation_data = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
                if not user_nation_data:
                    await interaction.response.send_message(f"❌ Nation with ID {nation_id} not found.", ephemeral=True)
                    interaction_responded = True
                    return
                
                # Calculate war range (75% to 133% of user's score)
                user_score = float(user_nation_data.get('score', 0))
                min_score = user_score * 0.75
                max_score = user_score * 1.33
                
            except Exception as e:
                await interaction.response.send_message(f"❌ Error fetching your nation data: {str(e)}", ephemeral=True)
                interaction_responded = True
                return
            
            # Send initial response to prevent timeout
            interaction_responded = False
            if interaction and not interaction_responded:
                await interaction.response.send_message("🔍 Searching for raid targets... This may take a moment!", ephemeral=True)
                interaction_responded = True
            
            # Get data from cache for initial filtering and city data
            all_nations = cache.get_nations()
            all_cities = cache.get_cities()
            top_60_alliances = cache.get_top_60_alliances()
            
            # Create lookup dictionaries for faster access
            cities_by_nation = {}
            for city in all_cities:
                nation_id_key = city.get('nation_id')
                if nation_id_key not in cities_by_nation:
                    cities_by_nation[nation_id_key] = []
                cities_by_nation[nation_id_key].append(city)

            # Filter potential targets using API wrappers for real-time data
            valid_targets = []
            total_checked = 0
            filtered_out = {
                'score_range': 0,
                'vmode': 0,
                'beige_turns': 0,
                'top_alliance': 0,
                'defensive_wars': 0,
                'no_cities': 0,
                'low_loot': 0,
                'api_error': 0
            }
            
            for target in all_nations:
                if not target:
                    continue
                
                total_checked += 1
                
                # Progress update every 1000 nations
                if total_checked % 1000 == 0:
                    info(f"Filtered {total_checked}/{len(all_nations)} nations... Found {len(valid_targets)} targets so far", tag="RAID")
                    
                target_score = float(target.get('score', 0))
                if not (min_score <= target_score <= max_score):
                    filtered_out['score_range'] += 1
                    continue

                # A) Filter out nations in vmode
                if target.get('vmode', 0) == 1:
                    filtered_out['vmode'] += 1
                    continue

                # A) Filter out nations with beige turns
                if target.get('beige_turns', 0) > 0:
                    filtered_out['beige_turns'] += 1
                    continue

                # A) Filter out nations in top 60 alliances or your alliance
                alliance_id = target.get('alliance_id')
                if alliance_id == 13033 or alliance_id in top_60_alliances:
                    filtered_out['top_alliance'] += 1
                    continue

                # A) Filter out nations with 3+ defensive wars
                defensive_wars = defensive_wars_by_nation.get(target.get('id'), 0)
                if defensive_wars >= 3:
                    filtered_out['defensive_wars'] += 1
                    continue

                # Get cities for this nation
                cities = cities_by_nation.get(target.get('id'), [])
                if not cities:
                    filtered_out['no_cities'] += 1
                    continue

                # Calculate loot potential based on cities and wars
                total_loot_potential = self.calculate_loot_potential(target, cities, [])

                # Only show profitable targets
                if total_loot_potential > 100000:  # Minimum $100k potential loot
                    # Calculate military strength
                    military_strength = (
                        target.get('soldiers', 0) * 0.5 +
                        target.get('tanks', 0) * 5 +
                        target.get('aircraft', 0) * 10 +
                        target.get('ships', 0) * 20
                    )
                    
                    # Calculate total infrastructure
                    total_infra = sum(city.get('infrastructure', 0) for city in cities)
                    
                    valid_targets.append({
                        'nation': target,
                        'score': target_score,
                        'military': military_strength,
                        'profit': total_loot_potential,
                        'cities': len(cities),
                        'alliance_id': alliance_id,
                        'alliance_rank': target.get('alliance_rank', 999),
                        'beige_turns': 0,  # Already filtered out
                        'wars': defensive_wars,
                        'infrastructure': total_infra
                    })
                else:
                    filtered_out['low_loot'] += 1

            # Sort by profit
            valid_targets.sort(key=lambda x: x['profit'], reverse=True)
            
            # Log filtering results
            info(f"Raid filtering results: {total_checked} nations checked", tag="RAID")
            info(f"  - Score range: {filtered_out['score_range']} filtered", tag="RAID")
            info(f"  - Vmode: {filtered_out['vmode']} filtered", tag="RAID")
            info(f"  - Beige turns: {filtered_out['beige_turns']} filtered", tag="RAID")
            info(f"  - Top 60 alliances: {filtered_out['top_alliance']} filtered", tag="RAID")
            info(f"  - 3+ defensive wars: {filtered_out['defensive_wars']} filtered", tag="RAID")
            info(f"  - No cities data: {filtered_out['no_cities']} filtered", tag="RAID")
            info(f"  - Low loot (<$100k): {filtered_out['low_loot']} filtered", tag="RAID")
            info(f"  - Valid targets found: {len(valid_targets)}", tag="RAID")
            
            if not valid_targets:
                msg = (
                    f"**No profitable raid targets found in war range.**\n\n"
                    f"**Search Results:**\n"
                    f"• Nations checked: {total_checked}\n"
                    f"• Score range: {min_score:,.0f} - {max_score:,.0f}\n"
                    f"• Filtered out:\n"
                    f"  - Outside score range: {filtered_out['score_range']}\n"
                    f"  - Vmode: {filtered_out['vmode']}\n"
                    f"  - Beige turns: {filtered_out['beige_turns']}\n"
                    f"  - Top 60 alliances: {filtered_out['top_alliance']}\n"
                    f"  - 3+ defensive wars: {filtered_out['defensive_wars']}\n"
                    f"  - No cities data: {filtered_out['no_cities']}\n"
                    f"  - Low loot: {filtered_out['low_loot']}\n\n"
                    f"**Try:** Lowering the minimum loot threshold or expanding your war range."
                )
                if interaction:
                    if interaction_responded:
                        await interaction.followup.send(msg, ephemeral=True)
                    else:
                        await interaction.response.send_message(msg, ephemeral=True)
                return

            # Create results message (limit to top 10)
            top_targets = valid_targets[:10]
            result_lines = []
            result_lines.append(f"**Top {len(top_targets)} Raid Targets (Score Range: {min_score:,.0f} - {max_score:,.0f})**\n")
            
            for i, target in enumerate(top_targets, 1):
                nation = target['nation']
                result_lines.append(
                    f"**{i}.** [{nation.get('nation_name', 'Unknown')}](https://politicsandwar.com/nation/id={nation.get('id')}) "
                    f"(ID: {nation.get('id')})"
                )
                result_lines.append(
                    f"    💰 **Loot Potential:** ${target['profit']:,.0f} | "
                    f"⭐ **Score:** {target['score']:,.0f} | "
                    f"🏙️ **Cities:** {target['cities']} | "
                    f"🏗️ **Infra:** {target['infrastructure']:,.0f}"
                )
                result_lines.append(
                    f"    🪖 **Military:** {target['military']:,.0f} | "
                    f"⚔️ **Wars:** {target['wars']} | "
                    f"🤝 **Alliance Rank:** {target['alliance_rank'] or 'None'}"
                )
                if target['beige_turns'] > 0:
                    result_lines.append(f"    🟡 **Beige Turns:** {target['beige_turns']}")
                result_lines.append("")
            
            result_text = "\n".join(result_lines)
            
            # Split into chunks if too long
            if len(result_text) > 2000:
                result_text = result_text[:1900] + "\n... (truncated)"
            
            embed = discord.Embed(
                title="🎯 Raid Targets Found",
                description=result_text,
                color=discord.Color.red()
            )
            embed.add_field(
                name="📊 Search Results",
                value=(
                    f"• Nations checked: {total_checked}\n"
                    f"• Score range: {min_score:,.0f} - {max_score:,.0f}\n"
                    f"• Vmode filtered: {filtered_out['vmode']}\n"
                    f"• Beige turns: {filtered_out['beige_turns']}\n"
                    f"• Top 60 alliances: {filtered_out['top_alliance']}\n"
                    f"• 3+ defensive wars: {filtered_out['defensive_wars']}\n"
                    f"• No cities data: {filtered_out['no_cities']}\n"
                    f"• Low loot: {filtered_out['low_loot']}",
                ),
                inline=False
            )
            
            if interaction:
                if interaction_responded:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    interaction_responded = True
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            error(f"Error in raid_logic: {e}", tag="RAID")
            if interaction:
                if interaction_responded:
                    await interaction.followup.send(f"❌ Error finding raid targets: {str(e)}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ Error finding raid targets: {str(e)}", ephemeral=True)
    
    def calculate_loot_potential(self, nation: dict, cities: list, wars: list) -> float:
        """Calculate potential loot from a nation based on cities and war history."""
        try:
            total_loot = 0.0
            
            # Base loot from infrastructure (25% of total infrastructure value)
            total_infra = sum(city.get('infrastructure', 0) for city in cities)
            infra_cost_per_level = 100  # Base cost per infrastructure level
            total_infra_value = total_infra * infra_cost_per_level
            total_loot += total_infra_value * 0.25
            
            # Building value estimation (30% of building costs)
            building_values = {
                'oil_well': 50000, 'coal_mine': 1000, 'iron_mine': 9500, 'bauxite_mine': 10000,
                'lead_mine': 10000, 'uranium_mine': 25000, 'farm': 1000, 'oil_refinery': 45000,
                'steel_mill': 45000, 'aluminum_refinery': 30000, 'munitions_factory': 35000,
                'police_station': 75000, 'hospital': 100000, 'recycling_center': 125000,
                'subway': 250000, 'supermarket': 5000, 'bank': 15000, 'shopping_mall': 45000,
                'stadium': 100000, 'barracks': 3000, 'factory': 15000, 'hangar': 100000,
                'drydock': 250000
            }
            
            total_building_value = 0
            for city in cities:
                for building, cost in building_values.items():
                    count = city.get(building, 0)
                    total_building_value += count * cost
            
            total_loot += total_building_value * 0.30
            
            # War history bonus (based on average money lost in recent wars)
            war_bonus = 1.0
            if wars:
                total_money_lost = 0
                for war in wars:
                    if war.get('defender_id') == nation.get('id'):
                        total_money_lost += war.get('def_money_lost', 0)
                    elif war.get('attacker_id') == nation.get('id'):
                        total_money_lost += war.get('att_money_lost', 0)
                
                if total_money_lost > 0:
                    avg_money_lost = total_money_lost / len(wars)
                    war_bonus = 1.0 + (avg_money_lost / 1000000)  # 1% bonus per $1M lost
            
            # Beige bonus (nations with beige turns have more loot)
            beige_bonus = 1.0
            if nation.get('beige_turns', 0) > 0:
                beige_bonus = 1.5
            
            # Apply bonuses
            total_loot *= war_bonus * beige_bonus
            
            return total_loot
            
        except Exception as e:
            error(f"Error calculating loot potential: {e}", tag="RAID")
            return 0.0


async def setup(bot: commands.Bot):
    """Set up the nation cog."""
    cog = NationCog(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(NationGroup(cog)) 