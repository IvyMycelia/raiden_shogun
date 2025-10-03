from typing import List, Optional, Dict
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import re

from bot.utils.config import config
from bot.utils.paginator import ActivityPaginator
from bot.utils.helpers import create_embed, format_number
from bot.handler import info, error, warning
from bot import data as get_data

class WarCog(commands.Cog):
    """Cog for war-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
    
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
    
    def format_war_info(self, war: Dict) -> str:
        """Format war information into a compact string."""
        attacker = war.get('attacker', {})
        defender = war.get('defender', {})
        
        # Basic war info
        info = [
            f"**War ID:** {war['id']}",
            f"**Type:** {war.get('war_type', 'N/A')}",
            f"**Turns Left:** {war.get('turns_left', 'N/A')}",
            f"**Reason:** {war.get('reason', 'N/A')}",
            "",
            f"**Attacker:** [{attacker.get('leader_name', 'N/A')}](https://politicsandwar.com/nation/id={attacker.get('id', '')})",
            f"**Defender:** [{defender.get('leader_name', 'N/A')}](https://politicsandwar.com/nation/id={defender.get('id', '')})",
            "",
            f"**Points:** {war.get('att_points', 0)} vs {war.get('def_points', 0)}",
            f"**Resistance:** {war.get('att_resistance', 0)}% vs {war.get('def_resistance', 0)}%",
            "",
            f"**Control:** {war.get('ground_control', 'None')} Ground | {war.get('air_superiority', 'None')} Air | {war.get('naval_blockade', 'None')} Naval"
        ]
        
        return "\n".join(info)
    
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
    
    @app_commands.command(name="war", description="Show active wars for a nation.")
    @app_commands.describe(
        nation_id="The ID of the nation to check wars for"
    )
    async def war(
        self,
        interaction: discord.Interaction,
        nation_id: int
    ):
        """Show active wars for a nation."""
        await interaction.response.defer()
        
        # Get active wars for the nation
        params = {
            "active": True,
            "nation_id": [nation_id],
            "first": 50
        }
        
        wars = get_data.GET_WARS(params, self.config.API_KEY)
        if not wars:
            await interaction.followup.send("No active wars found for this nation.", ephemeral=True)
            return
        
        # Format results
        results = [self.format_war_info(war) for war in wars]
        
        # Use paginator to display results
        paginator = ActivityPaginator(results)
        await interaction.followup.send(embed=paginator.get_embed(), view=paginator)
        
        info(f"War lookup completed by {interaction.user}", tag="WAR")

async def setup(bot: commands.Bot):
    """Set up the war cog."""
    await bot.add_cog(WarCog(bot)) 