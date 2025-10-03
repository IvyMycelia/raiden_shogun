"""
Nation information commands.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from bot.utils.helpers import create_embed, format_number
from bot.handler import info, error, warning
from bot import data as get_data
from bot import calculate
from bot import vars


class NationInfoCog(commands.Cog):
    """Cog for nation information commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config
    
    def get_user_nation(self, user_id: int) -> Optional[int]:
        """Get a user's registered nation ID."""
        from bot.cogs.user import UserCog  # Avoid circular import
        user_cog = self.bot.get_cog('UserCog')
        if not user_cog:
            return None
        return user_cog.get_user_nation(user_id)
    
    async def who_logic(self, interaction, nation_id: int = None, ctx=None):
        """Logic for who command."""
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
        
        # Get nation data
        nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
        if not nation:
            if interaction:
                await interaction.response.send_message("Nation not found.", ephemeral=True)
            else:
                await ctx.send("Nation not found.")
            return
        
        # Create embed with nation information
        embed = create_embed(
            title=f"🏛️ {nation.get('nation_name', 'N/A')}",
            description=f"**Leader:** {nation.get('leader_name', 'N/A')}",
            color=discord.Color.blue()
        )
        
        # Basic info
        embed.add_field(
            name="📊 Basic Info",
            value=(
                f"**Nation ID:** {nation.get('nation_id', 'N/A')}\n"
                f"**Score:** {format_number(nation.get('score', 0))}\n"
                f"**Cities:** {nation.get('cities', 0)}\n"
                f"**Population:** {format_number(nation.get('population', 0))}\n"
                f"**Infrastructure:** {format_number(nation.get('infrastructure', 0))}\n"
                f"**Land Area:** {format_number(nation.get('land_area', 0))}"
            ),
            inline=True
        )
        
        # Alliance info
        embed.add_field(
            name="🤝 Alliance",
            value=(
                f"**Alliance:** {nation.get('alliance', 'None')}\n"
                f"**Position:** {nation.get('alliance_position', 'N/A')}\n"
                f"**Color:** {nation.get('color', 'N/A').title()}\n"
                f"**Beige Turns:** {nation.get('beige_turns_remaining', 0)}\n"
                f"**VM Turns:** {nation.get('vm_turns', 0)}"
            ),
            inline=True
        )
        
        # Military info
        embed.add_field(
            name="⚔️ Military",
            value=(
                f"**Soldiers:** {format_number(nation.get('soldiers', 0))}\n"
                f"**Tanks:** {format_number(nation.get('tanks', 0))}\n"
                f"**Aircraft:** {format_number(nation.get('aircraft', 0))}\n"
                f"**Ships:** {format_number(nation.get('ships', 0))}\n"
                f"**Missiles:** {format_number(nation.get('missiles', 0))}\n"
                f"**Nukes:** {format_number(nation.get('nukes', 0))}\n"
                f"**Spies:** {format_number(nation.get('spies', 0))}"
            ),
            inline=True
        )
        
        # Wars info
        embed.add_field(
            name="⚔️ Wars",
            value=(
                f"**Offensive Wars:** {nation.get('offensive_wars', 0)}/5\n"
                f"**Defensive Wars:** {nation.get('defensive_wars', 0)}/10\n"
                f"**Last Active:** <t:{int(nation.get('last_active', 0))}:R>"
            ),
            inline=True
        )
        
        # Resources (simplified)
        money = nation.get('money', 0)
        embed.add_field(
            name="💰 Resources",
            value=f"**Money:** {format_number(money)}",
            inline=True
        )
        
        # Projects
        projects = nation.get('projects', [])
        project_names = [p.get('name', 'Unknown') for p in projects]
        embed.add_field(
            name="🏗️ Projects",
            value=f"**Count:** {len(projects)}\n**Projects:** {', '.join(project_names[:5])}{'...' if len(project_names) > 5 else ''}",
            inline=True
        )
        
        # Add nation URL
        nation_url = f"https://politicsandwar.com/nation/id={nation_id}"
        embed.add_field(
            name="🔗 Links",
            value=f"[View Nation]({nation_url})",
            inline=False
        )
        
        if interaction:
            await interaction.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)
    
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
        """Logic for chest command."""
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
    
    @app_commands.command(name="chest", description="Show the current amount of resources on a nation.")
    @app_commands.describe(nation_id="The ID of the nation to check (optional if you're registered)")
    async def chest(self, interaction: discord.Interaction, nation_id: int = None):
        """Show the current amount of resources on a nation."""
        await self.chest_logic(interaction, nation_id)
    
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


async def setup(bot: commands.Bot):
    """Set up the nation info cog."""
    await bot.add_cog(NationInfoCog(bot))
