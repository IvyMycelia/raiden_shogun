import discord
from discord.ext import commands
from discord import app_commands
import logging
import re
from typing import Optional

from bot.services.nation_service import NationService
from bot.services.raid_calculation_service import RaidCalculationService

logger = logging.getLogger('raiden_shogun')

class IntelCog(commands.Cog):
    """Commands for gathering intelligence on nations."""
    
    def __init__(self, bot):
        self.bot = bot
        self.nation_service = NationService()
        self.raid_calculation_service = RaidCalculationService()
    
    @app_commands.command(name="intel", description="Gather intelligence on a nation")
    @app_commands.describe(nation="Nation name or ID to gather intelligence on")
    async def intel_slash(self, interaction: discord.Interaction, nation: str):
        """Slash command for gathering intelligence."""
        await self.intel_logic(interaction, nation, is_slash=True)
    
    @commands.command(name="intel")
    async def intel_prefix(self, ctx: commands.Context, *, nation: str):
        """Prefix command for gathering intelligence."""
        await self.intel_logic(ctx, nation, is_slash=False)
    
    async def intel_logic(self, ctx_or_interaction, nation: str, is_slash: bool = True):
        """Main intel logic for both slash and prefix commands."""
        try:
            # Defer response for slash commands
            if is_slash:
                await ctx_or_interaction.response.defer()
            
            # Find nation by name or ID
            nation_data = await self.find_nation(nation)
            
            if not nation_data:
                error_embed = discord.Embed(
                    title="❌ **Nation Not Found**",
                    description=f"Could not find a nation matching `{nation}`",
                    color=discord.Color.red()
                )
                
                if is_slash:
                    await ctx_or_interaction.followup.send(embed=error_embed)
                else:
                    await ctx_or_interaction.send(embed=error_embed)
                return
            
            # Get market prices for conversion
            market_prices = await self.raid_calculation_service.get_market_prices()
            
            # Calculate total value
            total_value = self.calculate_total_value(nation_data, market_prices)
            
            # Create intel embed
            intel_embed = await self.create_intel_embed(nation_data, market_prices, total_value)
            
            # Send results
            if is_slash:
                await ctx_or_interaction.followup.send(embed=intel_embed)
            else:
                await ctx_or_interaction.send(embed=intel_embed)
            
            # Log success
            logger.info(f"Intel command completed for nation: {nation_data.get('nation_name', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"Error in intel command: {e}")
            error_embed = discord.Embed(
                title="❌ **Error**",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            
            if is_slash:
                await ctx_or_interaction.followup.send(embed=error_embed)
            else:
                await ctx_or_interaction.send(embed=error_embed)
    
    async def find_nation(self, nation: str) -> Optional[dict]:
        """Find nation by name or ID, or extract from intel report."""
        try:
            # Try to parse as nation ID first
            if nation.isdigit():
                nation_id = int(nation)
                nation_data = await self.nation_service.get_nation(nation_id)
                if nation_data:
                    return nation_data.__dict__
            
            # Try to extract nation name from intel report text
            nation_name = self.extract_nation_name_from_intel(nation)
            if nation_name:
                # If this looks like an intel report, extract data from it
                if self.is_intel_report(nation):
                    return self.extract_nation_data_from_intel(nation)
                else:
                    # Search for nation by name in cached data
                    nation_data = await self.search_nation_by_name(nation_name)
                    if nation_data:
                        return nation_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding nation: {e}")
            return None
    
    def extract_nation_name_from_intel(self, intel_text: str) -> Optional[str]:
        """Extract nation name from intel report text."""
        try:
            # Look for patterns like "about [NationName]" or "discovered that [NationName] has"
            import re
            
            # Pattern 1: "about [NationName]"
            pattern1 = r"about\s+([A-Za-z0-9\s]+?)\s*\.\s*Your"
            match1 = re.search(pattern1, intel_text)
            if match1:
                return match1.group(1).strip()
            
            # Pattern 2: "discovered that [NationName] has"
            pattern2 = r"discovered that\s+([A-Za-z0-9\s]+?)\s+has"
            match2 = re.search(pattern2, intel_text)
            if match2:
                return match2.group(1).strip()
            
            # Pattern 3: "gathered intelligence about [NationName]"
            pattern3 = r"gathered intelligence about\s+([A-Za-z0-9\s]+?)\s*\.\s*Your"
            match3 = re.search(pattern3, intel_text)
            if match3:
                return match3.group(1).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting nation name: {e}")
            return None
    
    def is_intel_report(self, text: str) -> bool:
        """Check if text looks like an intel report."""
        intel_indicators = [
            "successfully gathered intelligence",
            "spies discovered",
            "operation cost",
            "spies were captured",
            "agents were able to operate"
        ]
        return any(indicator in text.lower() for indicator in intel_indicators)
    
    def extract_nation_data_from_intel(self, intel_text: str) -> dict:
        """Extract nation data directly from intel report text."""
        import re
        
        # Extract nation name
        nation_name = self.extract_nation_name_from_intel(intel_text) or "Unknown"
        
        # Initialize nation data
        nation_data = {
            'nation_name': nation_name,
            'money': 0,
            'coal': 0,
            'oil': 0,
            'uranium': 0,
            'iron': 0,
            'bauxite': 0,
            'lead': 0,
            'gasoline': 0,
            'munitions': 0,
            'steel': 0,
            'aluminum': 0,
            'food': 0,
            'credits': 0
        }
        
        # Extract money
        money_match = re.search(r'\$([0-9,]+\.?[0-9]*)', intel_text)
        if money_match:
            nation_data['money'] = float(money_match.group(1).replace(',', ''))
        
        # Extract resources with their amounts (handle commas in numbers)
        resource_patterns = {
            'coal': r'([0-9,]+\.?[0-9]*)\s+coal',
            'oil': r'([0-9,]+\.?[0-9]*)\s+oil',
            'uranium': r'([0-9,]+\.?[0-9]*)\s+uranium',
            'iron': r'([0-9,]+\.?[0-9]*)\s+iron',
            'bauxite': r'([0-9,]+\.?[0-9]*)\s+bauxite',
            'lead': r'([0-9,]+\.?[0-9]*)\s+lead',
            'gasoline': r'([0-9,]+\.?[0-9]*)\s+gasoline',
            'munitions': r'([0-9,]+\.?[0-9]*)\s+munitions',
            'steel': r'([0-9,]+\.?[0-9]*)\s+steel',
            'aluminum': r'([0-9,]+\.?[0-9]*)\s+aluminum',
            'food': r'([0-9,]+\.?[0-9]*)\s+food',
            'credits': r'([0-9,]+\.?[0-9]*)\s+credits'
        }
        
        for resource, pattern in resource_patterns.items():
            match = re.search(pattern, intel_text.lower())
            if match:
                nation_data[resource] = float(match.group(1).replace(',', ''))
        
        return nation_data
    
    async def search_nation_by_name(self, nation_name: str) -> Optional[dict]:
        """Search for a nation by name in cached data."""
        try:
            from services.raid_cache_service import RaidCacheService
            
            async with RaidCacheService() as cache_service:
                cache_data = cache_service.load_raid_cache()
                if not cache_data:
                    return None
                
                nations_data = cache_data.get('nations', {})
                
                # Search for exact match first
                for nation_id, nation_data in nations_data.items():
                    if nation_data.get('nation_name', '').lower() == nation_name.lower():
                        return nation_data
                
                # Search for partial match
                for nation_id, nation_data in nations_data.items():
                    if nation_name.lower() in nation_data.get('nation_name', '').lower():
                        return nation_data
                
                return None
                
        except Exception as e:
            logger.error(f"Error searching for nation by name: {e}")
            return None
    
    def calculate_total_value(self, nation_data: dict, market_prices: dict) -> float:
        """Calculate total value of all resources and money."""
        total = 0.0
        
        # Add money
        total += nation_data.get('money', 0)
        
        # Add resource values
        resources = ['coal', 'oil', 'uranium', 'iron', 'bauxite', 'lead', 
                    'gasoline', 'munitions', 'steel', 'aluminum', 'food', 'credits']
        
        for resource in resources:
            amount = nation_data.get(resource, 0)
            price = market_prices.get(resource, 0)
            total += amount * price
        
        return total
    
    async def create_intel_embed(self, nation_data: dict, market_prices: dict, total_value: float) -> discord.Embed:
        """Create the intel report embed."""
        nation_name = nation_data.get('nation_name', 'Unknown')
        money = nation_data.get('money', 0)
        
        # Create embed
        embed = discord.Embed(
            title=f"🔍 **Intelligence Report: {nation_name}**",
            color=discord.Color.green()
        )
        
        # Add resources with correct emoji IDs (including money)
        resources = [
            ('money', 'money:1357103044466184412', 'Money'),
            ('coal', 'coal:1357102730682040410', 'Coal'),
            ('oil', 'Oil:1357102740391854140', 'Oil'),
            ('uranium', 'uranium:1357102742799126558', 'Uranium'),
            ('iron', 'iron:1357102735488581643', 'Iron'),
            ('bauxite', 'bauxite:1357102729411039254', 'Bauxite'),
            ('lead', 'lead:1357102736646209536', 'Lead'),
            ('gasoline', 'gasoline:1357102734645399602', 'Gasoline'),
            ('munitions', 'munitions:1357102777389814012', 'Munitions'),
            ('steel', 'steel:1357105344052072618', 'Steel'),
            ('aluminum', 'aluminum:1357102728391819356', 'Aluminum'),
            ('food', 'food:1357102733571784735', 'Food'),
            ('credits', 'credits:1357102732187537459', 'Credits')
        ]
        
        resource_text = ""
        for resource_key, emoji_id, display_name in resources:
            amount = nation_data.get(resource_key, 0)
            if resource_key == 'money':
                # Money doesn't have a market price, just show the amount
                resource_text += f"<:{emoji_id}> **{display_name}:** ${amount:,.2f}\n"
            else:
                price = market_prices.get(resource_key, 0)
                value = amount * price
                resource_text += f"<:{emoji_id}> **{display_name}:** {amount:,.2f}\n"
        
        embed.add_field(
            name="Resources",
            value=resource_text,
            inline=False
        )
        
        # Add total value
        embed.add_field(
            name="Total Value",
            value=f"<:emoji:1357103044466184412> {total_value:,.2f}",
            inline=True
        )
        
        # Add footer
        embed.set_footer(text="Intelligence gathered successfully • Developed And Maintained By Ivy <3")
        
        return embed

async def setup(bot):
    await bot.add_cog(IntelCog(bot))
