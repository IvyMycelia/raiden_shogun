import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger('raiden_shogun')

class MarketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = None
        
    async def cog_load(self):
        """Initialize API when cog loads."""
        try:
            from bot.api.politics_war_api import api
            self.api = api
            logger.info("🌐 Market cog loaded with API access")
        except ImportError as e:
            logger.error(f"❌ Failed to import API for market cog: {e}")

    @app_commands.command(name="market", description="Get current market prices for resources")
    @app_commands.describe(
        resource="The resource to get price for",
        coal="Amount of coal to calculate cost for",
        oil="Amount of oil to calculate cost for", 
        uranium="Amount of uranium to calculate cost for",
        iron="Amount of iron to calculate cost for",
        bauxite="Amount of bauxite to calculate cost for",
        lead="Amount of lead to calculate cost for",
        gasoline="Amount of gasoline to calculate cost for",
        munitions="Amount of munitions to calculate cost for",
        steel="Amount of steel to calculate cost for",
        aluminum="Amount of aluminum to calculate cost for",
        food="Amount of food to calculate cost for",
        credits="Amount of credits to calculate cost for"
    )
    @app_commands.choices(resource=[
        app_commands.Choice(name="All Resources", value="all"),
        app_commands.Choice(name="Coal", value="coal"),
        app_commands.Choice(name="Oil", value="oil"),
        app_commands.Choice(name="Uranium", value="uranium"),
        app_commands.Choice(name="Iron", value="iron"),
        app_commands.Choice(name="Bauxite", value="bauxite"),
        app_commands.Choice(name="Lead", value="lead"),
        app_commands.Choice(name="Gasoline", value="gasoline"),
        app_commands.Choice(name="Munitions", value="munitions"),
        app_commands.Choice(name="Steel", value="steel"),
        app_commands.Choice(name="Aluminum", value="aluminum"),
        app_commands.Choice(name="Food", value="food"),
        app_commands.Choice(name="Credits", value="credits"),
    ])
    async def market_slash(self, interaction: discord.Interaction, 
                          resource: str = "all",
                          coal: int = None,
                          oil: int = None,
                          uranium: int = None,
                          iron: int = None,
                          bauxite: int = None,
                          lead: int = None,
                          gasoline: int = None,
                          munitions: int = None,
                          steel: int = None,
                          aluminum: int = None,
                          food: int = None,
                          credits: int = None):
        """Slash command for market prices."""
        # Check if any quantities are provided for cost calculation
        quantities = {
            'coal': coal, 'oil': oil, 'uranium': uranium, 'iron': iron,
            'bauxite': bauxite, 'lead': lead, 'gasoline': gasoline,
            'munitions': munitions, 'steel': steel, 'aluminum': aluminum,
            'food': food, 'credits': credits
        }
        
        # Filter out None values
        quantities = {k: v for k, v in quantities.items() if v is not None and v > 0}
        
        if quantities:
            # Cost calculation mode
            await self.cost_logic(interaction, quantities, is_slash=True)
        else:
            # Regular price display mode
            await self.market_logic(interaction, resource, is_slash=True)

    @commands.command(name="market", aliases=["m"])
    async def market_prefix(self, ctx, *, resource: str = "all"):
        """Prefix command for market prices."""
        # Check if this is a cost calculation request
        if resource.lower().startswith("cost"):
            # Parse cost calculation from the remaining text
            cost_text = resource[4:].strip() if len(resource) > 4 else ""
            quantities = self.parse_cost_quantities(cost_text)
            
            if quantities:
                await self.cost_logic(ctx, quantities, is_slash=False)
            else:
                # No quantities provided, show all unit prices
                await self.market_logic(ctx, "all", is_slash=False)
        else:
            # Regular price display
            await self.market_logic(ctx, resource, is_slash=False)

    async def market_logic(self, interaction_or_ctx, resource: str, is_slash: bool = True):
        """Main logic for market command."""
        try:
            if is_slash:
                await interaction_or_ctx.response.defer()
            else:
                async with interaction_or_ctx.typing():
                    pass

            # Get market prices
            prices = await self.get_market_prices()
            if not prices:
                embed = discord.Embed(
                    title="❌ Market Error",
                    description="Failed to fetch market prices. Please try again later.",
                    color=0xff0000
                )
                if is_slash:
                    await interaction_or_ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction_or_ctx.send(embed=embed)
                return

            # Parse resource parameter
            resource_key = self.parse_resource_parameter(resource)
            if resource_key is None:
                embed = discord.Embed(
                    title="❌ Invalid Resource",
                    description=f"Unknown resource: `{resource}`\nUse `!help market` for available options.",
                    color=0xff0000
                )
                if is_slash:
                    await interaction_or_ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction_or_ctx.send(embed=embed)
                return

            # Create embed
            embed = self.create_market_embed(prices, resource_key)
            
            if is_slash:
                await interaction_or_ctx.followup.send(embed=embed)
            else:
                await interaction_or_ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"❌ Error in market command: {e}")
            embed = discord.Embed(
                title="❌ Market Error",
                description="An error occurred while fetching market prices.",
                color=0xff0000
            )
            if is_slash:
                await interaction_or_ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction_or_ctx.send(embed=embed)

    async def get_market_prices(self) -> Optional[Dict[str, float]]:
        """Get current market prices from API."""
        try:
            if not self.api:
                logger.error("❌ API not available for market prices")
                return None
                
            prices_data = await self.api.get_tradeprices()
            if not prices_data or len(prices_data) == 0:
                logger.warning("🌐 No market prices data available")
                return None
                
            # Get the latest prices
            latest_prices = prices_data[0]
            
            # Convert to float and return
            market_prices = {
                'coal': float(latest_prices.get('coal', 50.0)),
                'oil': float(latest_prices.get('oil', 100.0)),
                'uranium': float(latest_prices.get('uranium', 2000.0)),
                'iron': float(latest_prices.get('iron', 75.0)),
                'bauxite': float(latest_prices.get('bauxite', 80.0)),
                'lead': float(latest_prices.get('lead', 90.0)),
                'gasoline': float(latest_prices.get('gasoline', 150.0)),
                'munitions': float(latest_prices.get('munitions', 200.0)),
                'steel': float(latest_prices.get('steel', 300.0)),
                'aluminum': float(latest_prices.get('aluminum', 400.0)),
                'food': float(latest_prices.get('food', 25.0)),
                'credits': float(latest_prices.get('credits', 1000.0))
            }
            
            logger.info(f"🌐 Retrieved market prices: {len(market_prices)} resources")
            return market_prices
            
        except Exception as e:
            logger.error(f"❌ Error fetching market prices: {e}")
            return None

    def parse_resource_parameter(self, resource: str) -> Optional[str]:
        """Parse resource parameter and return standardized key."""
        if not resource:
            return "all"
            
        resource_lower = resource.lower().strip()
        
        # Handle special cases
        if resource_lower in ["all", "everything", ""]:
            return "all"
            
        # Handle single letter abbreviations
        abbreviation_map = {
            'c': 'coal',
            'o': 'oil', 
            'u': 'uranium',
            'i': 'iron',
            'b': 'bauxite',
            'l': 'lead',
            'g': 'gasoline',
            'm': 'munitions',
            's': 'steel',
            'a': 'aluminum',
            'f': 'food',
            'cr': 'credits'
        }
        
        if resource_lower in abbreviation_map:
            return abbreviation_map[resource_lower]
            
        # Handle full names (case insensitive)
        resource_names = {
            'coal': 'coal',
            'oil': 'oil',
            'uranium': 'uranium',
            'iron': 'iron',
            'bauxite': 'bauxite',
            'lead': 'lead',
            'gasoline': 'gasoline',
            'munitions': 'munitions',
            'steel': 'steel',
            'aluminum': 'aluminum',
            'food': 'food',
            'credits': 'credits'
        }
        
        if resource_lower in resource_names:
            return resource_names[resource_lower]
            
        return None

    def create_market_embed(self, prices: Dict[str, float], resource_key: str) -> discord.Embed:
        """Create market price embed."""
        if resource_key == "all":
            # Show all resources
            embed = discord.Embed(
                title="📊 Current Market Prices",
                description="All resource prices from the trade market",
                color=0x00ff00
            )
            
            # Resource emojis and names (using same emojis as warchest command)
            resources = [
                ("coal", "Coal", "<:coal:1357102730682040410>"),
                ("oil", "Oil", "<:oil:1357102740391854140>"),
                ("uranium", "Uranium", "<:uranium:1357102742799126558>"),
                ("iron", "Iron", "<:iron:1357102735488581643>"),
                ("bauxite", "Bauxite", "<:bauxite:1357102729411039254>"),
                ("lead", "Lead", "<:lead:1357102736646209536>"),
                ("gasoline", "Gasoline", "<:gasoline:1357102734645399602>"),
                ("munitions", "Munitions", "<:munitions:1357102777389814012>"),
                ("steel", "Steel", "<:steel:1357105344052072618>"),
                ("aluminum", "Aluminum", "<:aluminum:1357102728391819356>"),
                ("food", "Food", "<:food:1357102733571784735>"),
                ("credits", "Credits", "<:credits:1357102732187537459>")
            ]
            
            # Create straight list format like warchest command
            txt = ""
            for key, name, emoji in resources:
                price = prices.get(key, 0.0)
                txt += f"{emoji} **{name}**: ${price:,.2f}\n"
            
            embed.add_field(name="Current Market Prices", value=txt, inline=False)
                
        else:
            # Show single resource (using same emojis as warchest command)
            resource_names = {
                'coal': ('Coal', '<:coal:1357102730682040410>'),
                'oil': ('Oil', '<:oil:1357102740391854140>'),
                'uranium': ('Uranium', '<:uranium:1357102742799126558>'),
                'iron': ('Iron', '<:iron:1357102735488581643>'),
                'bauxite': ('Bauxite', '<:bauxite:1357102729411039254>'),
                'lead': ('Lead', '<:lead:1357102736646209536>'),
                'gasoline': ('Gasoline', '<:gasoline:1357102734645399602>'),
                'munitions': ('Munitions', '<:munitions:1357102777389814012>'),
                'steel': ('Steel', '<:steel:1357105344052072618>'),
                'aluminum': ('Aluminum', '<:aluminum:1357102728391819356>'),
                'food': ('Food', '<:food:1357102733571784735>'),
                'credits': ('Credits', '<:credits:1357102732187537459>')
            }
            
            name, emoji = resource_names.get(resource_key, (resource_key.title(), "📦"))
            price = prices.get(resource_key, 0.0)
            
            embed = discord.Embed(
                title=f"{emoji} {name} Price",
                description=f"Current market price: **${price:,.2f}**",
                color=0x00ff00
            )
            
        # Add timestamp
        embed.set_footer(text="Prices from Politics & War Trade Market")
        
        return embed

    def parse_cost_quantities(self, cost_text: str) -> Dict[str, int]:
        """Parse cost quantities from text like 'aluminum:50 u:100'."""
        if not cost_text:
            return {}
            
        quantities = {}
        
        # Resource name mappings
        resource_map = {
            'c': 'coal', 'coal': 'coal',
            'o': 'oil', 'oil': 'oil', 
            'u': 'uranium', 'uranium': 'uranium',
            'i': 'iron', 'iron': 'iron',
            'b': 'bauxite', 'bauxite': 'bauxite',
            'l': 'lead', 'lead': 'lead',
            'g': 'gasoline', 'gasoline': 'gasoline',
            'm': 'munitions', 'munitions': 'munitions',
            's': 'steel', 'steel': 'steel',
            'a': 'aluminum', 'aluminum': 'aluminum',
            'f': 'food', 'food': 'food',
            'cr': 'credits', 'credits': 'credits'
        }
        
        # Split by spaces and parse each item
        items = cost_text.split()
        for item in items:
            if ':' in item:
                try:
                    resource_part, amount_str = item.split(':', 1)
                    resource_key = resource_map.get(resource_part.lower())
                    if resource_key:
                        amount = int(amount_str.replace(',', ''))
                        if amount > 0:
                            quantities[resource_key] = amount
                except (ValueError, IndexError):
                    continue
                    
        return quantities

    async def cost_logic(self, interaction_or_ctx, quantities: Dict[str, int], is_slash: bool = True):
        """Calculate cost for specified quantities of resources."""
        try:
            if is_slash:
                await interaction_or_ctx.response.defer()
            else:
                async with interaction_or_ctx.typing():
                    pass

            # Get market prices
            prices = await self.get_market_prices()
            if not prices:
                embed = discord.Embed(
                    title="❌ Market Error",
                    description="Failed to fetch market prices. Please try again later.",
                    color=0xff0000
                )
                if is_slash:
                    await interaction_or_ctx.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction_or_ctx.send(embed=embed)
                return

            # Calculate costs
            total_cost = 0.0
            cost_breakdown = []
            
            # Resource emojis and names
            resource_info = {
                'coal': ('Coal', '<:coal:1357102730682040410>'),
                'oil': ('Oil', '<:oil:1357102740391854140>'),
                'uranium': ('Uranium', '<:uranium:1357102742799126558>'),
                'iron': ('Iron', '<:iron:1357102735488581643>'),
                'bauxite': ('Bauxite', '<:bauxite:1357102729411039254>'),
                'lead': ('Lead', '<:lead:1357102736646209536>'),
                'gasoline': ('Gasoline', '<:gasoline:1357102734645399602>'),
                'munitions': ('Munitions', '<:munitions:1357102777389814012>'),
                'steel': ('Steel', '<:steel:1357105344052072618>'),
                'aluminum': ('Aluminum', '<:aluminum:1357102728391819356>'),
                'food': ('Food', '<:food:1357102733571784735>'),
                'credits': ('Credits', '<:credits:1357102732187537459>')
            }
            
            for resource, amount in quantities.items():
                if resource in prices and resource in resource_info:
                    unit_price = prices[resource]
                    total_price = unit_price * amount
                    total_cost += total_price
                    
                    name, emoji = resource_info[resource]
                    cost_breakdown.append(f"{emoji} **{name}**: {amount:,} × ${unit_price:,.2f} = **${total_price:,.2f}**")
            
            # Create embed
            embed = discord.Embed(
                title="💰 Cost Calculation",
                description="Total cost for specified resources",
                color=0x00ff00
            )
            
            # Add breakdown in straight list format like warchest command
            if cost_breakdown:
                txt = "\n".join(cost_breakdown)
                txt += f"\n\n**Total Cost: ${total_cost:,.2f}**"
                embed.add_field(name="Cost Breakdown", value=txt, inline=False)
            else:
                embed.add_field(
                    name="No Resources",
                    value="No valid resources specified for cost calculation.",
                    inline=False
                )
            
            embed.set_footer(text="Prices from Politics & War Trade Market")
            
            if is_slash:
                await interaction_or_ctx.followup.send(embed=embed)
            else:
                await interaction_or_ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"❌ Error in cost calculation: {e}")
            embed = discord.Embed(
                title="❌ Cost Calculation Error",
                description="An error occurred while calculating costs.",
                color=0xff0000
            )
            if is_slash:
                await interaction_or_ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction_or_ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MarketCog(bot))
