import discord
from discord import app_commands
from discord.ext import commands

from bot.utils.config import config
from bot.utils.helpers import create_embed
from bot.utils.paginator import ActivityPaginator
from bot.handler import info

class HelpCog(commands.Cog):
    """Cog for help-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
    
    @app_commands.command(name="help", description="Get help with bot commands.")
    @app_commands.describe(category="Category of commands to get help with.")
    @app_commands.choices(category=[
        app_commands.Choice(name="All Commands", value="all"),
        app_commands.Choice(name="Audit Commands", value="audit"),
        app_commands.Choice(name="Nation Commands", value="nation"),
        app_commands.Choice(name="War Commands", value="war"),
        app_commands.Choice(name="Military Commands", value="military"),
        app_commands.Choice(name="Bank Commands", value="bank"),
    ])
    async def help(self, interaction: discord.Interaction, category: str = "all"):
        """Get help with bot commands."""
        help_texts = []
        
        if category in ["all", "audit"]:
            help_texts.append("""
### Audit Commands
`/audit` - Audit alliance members for various requirements
- **Types:**
  - `activity` - Check for inactive members (24+ hours)
  - `warchest` - Check if members have enough resources for 60 turns (5 days)
  - `spies` - Check if members have enough spies (50 or 60 with Intelligence Agency)
  - `mmr` - Check if members meet MMR requirements
  - `deposit` - Check for excess resources that should be deposited
- **Parameters:**
  - `cities` - Only audit members with ≤ this many cities (for warchest)

`/audit_member` - Audit a specific alliance member for all requirements
- **Parameters:**
  - `nation_id` - The ID of the nation to audit
""")
        
        if category in ["all", "nation"]:
            help_texts.append("""
### Nation Commands
`/warchest` - Calculate a nation's warchest requirements (5 days of upkeep)
- **Parameters:**
  - `nation_id` - Nation ID for which to calculate the warchest
- **Shows:**
  - Required resources for 60 turns
  - Excess resources that should be deposited
  - Direct deposit link if there are excess resources

`/bank` - Check the bank balance of a nation
- **Parameters:**
  - `nation_id` - Nation ID to check
- **Shows:**
  - Current bank balance
  - All resources in the bank

`/wars` - Check the active wars and military of a nation
- **Parameters:**
  - `nation_id` - Nation ID to check
- **Shows:**
  - Active offensive and defensive wars
  - Military units in each war
  - War control status
""")
        
        if category in ["all", "war"]:
            help_texts.append("""
### War Commands
`/war` - Get detailed information about a specific war
- **Parameters:**
  - `war_id` - ID of the war to check
- **Shows:**
  - War type and reason
  - Attacker and defender information
  - War points and resistance
  - Control status (ground, air, naval)

`/wars` - Get a list of active wars
- **Parameters:**
  - `alliance_id` - Optional alliance ID to filter wars
  - `nation_id` - Optional nation ID to filter wars
- **Shows:**
  - List of active wars
  - Basic war information
  - War status and control
""")
        
        if category in ["all", "military"]:
            help_texts.append("""
### Military Commands
`/military` - Check military capacity and usage
- **Parameters:**
  - `nation_id` - Nation ID to check
- **Shows:**
  - Current military units
  - Military capacity from buildings
  - Usage percentage
  - MMR compliance

`/mmr` - Check MMR (Military Manufacturing Ratio) requirements
- **Parameters:**
  - `nation_id` - Nation ID to check
- **Shows:**
  - Required MMR based on city count
  - Current MMR status
  - Missing buildings
""")
        
        if category in ["all", "bank"]:
            help_texts.append("""
### Bank Commands
`/bank` - Check alliance bank balance
- **Shows:**
  - Total resources in bank
  - Resource breakdown
  - Recent transactions

`/deposit` - Get a deposit link for excess resources
- **Parameters:**
  - `nation_id` - Nation ID to generate deposit link for
- **Shows:**
  - Direct deposit link
  - Amount of each resource to deposit
""")
        
        # Use paginator to display results
        paginator = ActivityPaginator(help_texts)
        await interaction.response.send_message(embed=paginator.get_embed(), view=paginator)
        
        info(f"Help command used by {interaction.user} in {interaction.channel}", tag="HELP")

async def setup(bot: commands.Bot):
    """Set up the help cog."""
    await bot.add_cog(HelpCog(bot)) 