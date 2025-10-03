from discord.ext import commands
from typing import Optional
from ..utils.config import config
from ..handler import info, error, warning

class BaseCog(commands.Cog):
    """Base cog class with common functionality."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
    
    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle errors in cog commands."""
        error_msg = str(error)
        error(f"Error in {ctx.command.name}: {error_msg}")
        
        # Send error message to user
        await ctx.send(
            embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {error_msg}",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
    
    def log_command(self, ctx: commands.Context, tag: Optional[str] = None) -> None:
        """Log command execution."""
        info(f"Command {ctx.command.name} executed by {ctx.author} in {ctx.channel}", tag=tag) 