import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
import os
import json
import time
import asyncio

from bot.utils.config import config
from bot.utils.helpers import create_embed, format_number
from bot.handler import info, error, warning
from bot import data as get_data

class WarDetectionCog(commands.Cog):
    """Cog for detecting and monitoring war declarations."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
        
        # Configuration
        self.monitoring_channel_id = 1386829632036409425  # Channel to post notifications - UPDATE THIS ID
        self.alert_role_id = 1358606073824546996  # Role to ping for defensive wars - UPDATE THIS ID
        self.alliance_id = 13033  # Your alliance ID
        
        # File to persist highest war ID
        self.highest_id_file = "data/highest_war_id.json"
        self.highest_war_id_seen = self.load_highest_id()
        
        # Start the monitoring task
        self.war_monitor.start()
        
        info("War Detection Cog initialized", tag="WAR_DETECTION")
    
    def load_highest_id(self):
        try:
            if os.path.exists(self.highest_id_file):
                with open(self.highest_id_file, 'r') as f:
                    data = json.load(f)
                    return int(data.get('highest_id', 0))
        except Exception as e:
            error(f"Error loading highest war ID: {e}", tag="WAR_DETECTION")
        return 0

    def save_highest_id(self):
        try:
            os.makedirs(os.path.dirname(self.highest_id_file), exist_ok=True)
            with open(self.highest_id_file, 'w') as f:
                json.dump({'highest_id': self.highest_war_id_seen}, f)
        except Exception as e:
            error(f"Error saving highest war ID: {e}", tag="WAR_DETECTION")

    async def get_alliance_members(self) -> List[Dict]:
        """Get all alliance members."""
        try:
            # Use separate API key for wars to distribute load
            war_api_key = "29cc5d1b8aca3b02fe75"
            # Add delay to prevent rate limiting
            await asyncio.sleep(0.5)
            members = get_data.GET_ALLIANCE_MEMBERS(self.alliance_id, war_api_key)
            if not members:
                error(f"Could not fetch alliance members for ID {self.alliance_id} (API returned: {members})", tag="WAR_DETECTION")
                return []
            # Check if the expected key is present in the first member
            if isinstance(members, list) and members and 'id' in members[0]:
                for m in members:
                    if 'nation_id' not in m and 'id' in m:
                        m['nation_id'] = m['id']
            return members
        except Exception as e:
            error(f"Error getting alliance members: {e}", tag="WAR_DETECTION")
            return []
    
    def format_war_notification(self, war: Dict, is_defensive: bool = False) -> discord.Embed:
        """Format war notification embed."""
        attacker = war.get('attacker', {})
        defender = war.get('defender', {})
        
        # Determine if this is a defensive war (our member is being attacked)
        if is_defensive:
            color = discord.Color.red()
            title = "🛡️ **DEFENSIVE WAR DECLARATION**"
            description = f"**{defender.get('leader_name', 'N/A')}** is being attacked!"
        else:
            color = discord.Color.orange()
            title = "⚔️ **OFFENSIVE WAR DECLARATION**"
            description = f"**{attacker.get('leader_name', 'N/A')}** has declared war!"
        
        embed = create_embed(
            title=title,
            description=description,
            color=color
        )
        
        # Add basic war info
        embed.add_field(
            name="War Information",
            value=(
                f"**War ID:** {war['id']}\n"
                f"**Type:** {war.get('war_type', 'N/A')}\n"
                f"**Reason:** {war.get('reason', 'N/A')}"
            ),
            inline=False
        )
        
        # Add nation links
        embed.add_field(
            name="Attacker",
            value=f"[{attacker.get('leader_name', 'N/A')}](https://politicsandwar.com/nation/id={attacker.get('id', '')})",
            inline=True
        )
        
        embed.add_field(
            name="Defender", 
            value=f"[{defender.get('leader_name', 'N/A')}](https://politicsandwar.com/nation/id={defender.get('id', '')})",
            inline=True
        )
        
        # Add timestamp
        embed.set_footer(text=f"Declared at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        return embed
    
    @tasks.loop(seconds=30)  # Reduced from 2.5 to 30 seconds to avoid rate limits
    async def war_monitor(self):
        """Monitor for new war declarations using min_id and orderBy ASC."""
        try:
            # Add delay to avoid rate limiting
            await asyncio.sleep(1)
            
            params = {
                "min_id": self.highest_war_id_seen,
                "orderBy": [{"column": "ID", "order": "ASC"}],
                "first": 50  # Reduced from 100 to 50 to reduce API load
            }
            # Use separate API key for wars to distribute load
            war_api_key = "29cc5d1b8aca3b02fe75"
            # Add delay to prevent rate limiting
            await asyncio.sleep(1)
            wars = get_data.GET_WARS(params, war_api_key)
            if not wars:
                return
            alliance_members = await self.get_alliance_members()
            alliance_member_ids = {str(member.get('nation_id')) for member in alliance_members}
            channel = self.bot.get_channel(self.monitoring_channel_id)
            if not channel:
                error(f"Could not find monitoring channel {self.monitoring_channel_id}", tag="WAR_DETECTION")
                return
            for war in wars:
                war_id = war.get('id')
                if not war_id:
                    continue
                try:
                    war_id_int = int(war_id)
                except (ValueError, TypeError):
                    error(f"Invalid war ID format: {war_id}", tag="WAR_DETECTION")
                    continue
                if war_id_int <= self.highest_war_id_seen:
                    continue
                attacker_id = str(war.get('attacker', {}).get('id'))
                defender_id = str(war.get('defender', {}).get('id'))
                if attacker_id in alliance_member_ids or defender_id in alliance_member_ids:
                    is_defensive = defender_id in alliance_member_ids
                    embed = self.format_war_notification(war, is_defensive=is_defensive)
                    if is_defensive:
                        await channel.send(f"<@&{self.alert_role_id}>", embed=embed)
                        info(f"Posted defensive war declaration for war {war_id_int}", tag="WAR_DETECTION")
                    else:
                        await channel.send(embed=embed)
                        info(f"Posted offensive war declaration for war {war_id_int}", tag="WAR_DETECTION")
                if war_id_int > self.highest_war_id_seen:
                    self.highest_war_id_seen = war_id_int
                    self.save_highest_id()
        except Exception as e:
            error(f"Error in war monitor: {e}", tag="WAR_DETECTION")
            # If we get rate limited, wait longer before next attempt
            if "429" in str(e) or "Too Many Requests" in str(e):
                warning("Rate limited in war monitor, waiting 60 seconds", tag="WAR_DETECTION")
                await asyncio.sleep(60)
    
    @war_monitor.before_loop
    async def before_war_monitor(self):
        """Wait until bot is ready before starting the monitor."""
        await self.bot.wait_until_ready()
        info("War declaration monitor task started", tag="WAR_DETECTION")
    
    @commands.command(name="warstatus")
    @commands.has_permissions(administrator=True)
    async def war_status(self, ctx):
        """Show the status of war detection system."""
        try:
            alliance_members = await self.get_alliance_members()
            channel = self.bot.get_channel(self.monitoring_channel_id)
            status_info = [
                f"**War Declaration Detection Status**",
                f"✅ **Monitoring:** {'Active' if self.war_monitor.is_running() else 'Inactive'}",
                f"📊 **Highest War ID Seen:** {self.highest_war_id_seen}",
                f"👥 **Alliance Members:** {len(alliance_members)}",
                f"📢 **Alert Channel:** {channel.mention if channel else 'Not Found'}",
                f"🔔 **Alert Role:** <@&{self.alert_role_id}>",
                f"🔄 **Check Interval:** Every 2.5 seconds"
            ]
            embed = create_embed(
                title="War Declaration Detection System Status",
                description="\n".join(status_info),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            error(f"Error in war status command: {e}", tag="WAR_DETECTION")
            await ctx.send("Error getting war detection status.")
    
    @commands.command(name="clearwars")
    @commands.has_permissions(administrator=True)
    async def clear_known_wars(self, ctx):
        """Reset the war ID tracking to detect all current wars as new."""
        try:
            old_id = self.highest_war_id_seen
            self.highest_war_id_seen = 0
            self.save_highest_id()
            embed = create_embed(
                title="War ID Tracking Reset",
                description=f"Reset highest war ID from {old_id} to 0. Will detect all current wars as new on next check.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            info(f"War ID tracking reset by {ctx.author}", tag="WAR_DETECTION")
        except Exception as e:
            error(f"Error resetting war tracking: {e}", tag="WAR_DETECTION")
            await ctx.send("Error resetting war tracking.")

async def setup(bot: commands.Bot):
    """Set up the war detection cog."""
    await bot.add_cog(WarDetectionCog(bot)) 