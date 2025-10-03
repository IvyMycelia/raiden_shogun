"""
Nation search commands.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from bot.utils.helpers import create_embed, format_number
from bot.utils.paginator import GridPaginator, PaginatorView
from bot.handler import info, error, warning
from bot import data as get_data


class NationSearchCog(commands.Cog):
    """Cog for nation search commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config
    
    async def who_search_logic(self, interaction, search_term: str = None, ctx=None):
        """Logic for who search command."""
        if not search_term:
            msg_embed = create_embed(
                title=":warning: No Search Term Provided",
                description="Please provide a search term to search for nations.",
                color=discord.Color.orange()
            )
            if interaction:
                await interaction.response.send_message(embed=msg_embed, ephemeral=True)
            else:
                await ctx.send(embed=msg_embed)
            return
        
        # Search for nations
        nations = get_data.SEARCH_NATIONS(search_term, self.config.API_KEY)
        if not nations:
            msg_embed = create_embed(
                title=":warning: No Nations Found",
                description=f"No nations found matching '{search_term}'.",
                color=discord.Color.orange()
            )
            if interaction:
                await interaction.response.send_message(embed=msg_embed, ephemeral=True)
            else:
                await ctx.send(embed=msg_embed)
            return
        
        # Create paginator for results
        paginator = GridPaginator(nations, per_page=9)
        
        if interaction:
            await interaction.response.send_message(embed=paginator.get_embed(), view=PaginatorView(paginator))
        else:
            await ctx.send(embed=paginator.get_embed(), view=PaginatorView(paginator))
    
    @app_commands.command(name="who_search", description="Search for nations by name or leader.")
    @app_commands.describe(search_term="The search term to look for")
    async def who_search(
        self,
        interaction: discord.Interaction,
        search_term: str
    ):
        """Search for nations by name or leader."""
        await self.who_search_logic(interaction, search_term)
    
    @commands.command(name="who_search")
    async def who_search_prefix(self, ctx, *, search_term: str = None):
        try:
            await self.who_search_logic(None, search_term, ctx=ctx)
        except Exception as e:
            error(f"Error in who_search command: {e}", tag="WHO_SEARCH")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while processing the search. Please try again later.",
                    color=discord.Color.red()
                )
            )


async def setup(bot: commands.Bot):
    """Set up the nation search cog."""
    await bot.add_cog(NationSearchCog(bot))
