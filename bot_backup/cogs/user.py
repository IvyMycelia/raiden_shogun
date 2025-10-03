import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from typing import Dict, Optional
from bot.utils.helpers import create_embed
from bot.handler import info, error, warning
from bot import data as get_data

class UserCog(commands.Cog):
    """Cog for user-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = bot.config
        self.registrations_file = "data/registrations.json"
        self.ensure_registrations_file()
    
    def ensure_registrations_file(self):
        """Ensure the registrations file exists."""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.registrations_file):
            with open(self.registrations_file, "w") as f:
                json.dump({}, f)
    
    def load_registrations(self) -> Dict:
        """Load registrations from file."""
        try:
            with open(self.registrations_file, "r") as f:
                return json.load(f)
        except Exception as e:
            error(f"Error loading registrations: {e}", tag="USER")
            return {}
    
    def save_registrations(self, registrations: Dict):
        """Save registrations to file."""
        try:
            with open(self.registrations_file, "w") as f:
                json.dump(registrations, f, indent=4)
        except Exception as e:
            error(f"Error saving registrations: {e}", tag="USER")
    
    def get_user_nation(self, user_id: int) -> Optional[int]:
        """Get a user's registered nation ID."""
        registrations = self.load_registrations()
        user_data = registrations.get(str(user_id), {})
        return user_data.get('nation_id') if isinstance(user_data, dict) else user_data
    
    @commands.command(name="add")
    async def add_nation(self, ctx: commands.Context, nation_id: int):
        """Add a nation's Discord user to the current channel."""
        try:
            # Check if user has permission to manage channels
            if not ctx.author.guild_permissions.manage_channels:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Permission Denied",
                        description="You need the 'Manage Channels' permission to use this command.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Get nation data to verify the nation exists and get Discord info
            nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            if not nation:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Nation Not Found",
                        description="Could not find a nation with that ID. Please check the ID and try again.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Check if nation has Discord info
            discord_username = nation.get('discord')
            if not discord_username:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: No Discord Found",
                        description=f"The nation [{nation['nation_name']}](https://politicsandwar.com/nation/id={nation_id}) does not have Discord information set in their nation profile.",
                        color=discord.Color.orange()
                    )
                )
                return
            
            # Try to find the Discord user
            discord_user = None
            
            # First try to find by Discord ID from registrations
            registrations = self.load_registrations()
            for user_id, user_data in registrations.items():
                reg_nation_id = user_data.get('nation_id') if isinstance(user_data, dict) else user_data
                if str(reg_nation_id) == str(nation_id):
                    try:
                        # Try to get the member from the guild first
                        discord_user = ctx.guild.get_member(int(user_id))
                        if not discord_user:
                            # If not found as member, try to fetch member
                            try:
                                discord_user = await ctx.guild.fetch_member(int(user_id))
                            except discord.NotFound:
                                # If still not found, try to fetch user to confirm they exist
                                await self.bot.fetch_user(int(user_id))
                                await ctx.send(
                                    embed=create_embed(
                                        title=":warning: User Not in Server",
                                        description=f"The Discord user for this nation is not a member of this server. They need to join first.",
                                        color=discord.Color.orange()
                                    )
                                )
                                return
                        break
                    except (ValueError, discord.NotFound):
                        continue
            
            # If not found in registrations, try the discord field from nation data
            if not discord_user:
                try:
                    # Try to parse as Discord ID first
                    user_id = int(discord_username)
                    discord_user = ctx.guild.get_member(user_id)
                    if not discord_user:
                        # If not found as member, try to fetch member
                        try:
                            discord_user = await ctx.guild.fetch_member(user_id)
                        except discord.NotFound:
                            # If still not found, try to fetch user to confirm they exist
                            await self.bot.fetch_user(user_id)
                            await ctx.send(
                                embed=create_embed(
                                    title=":warning: User Not in Server",
                                    description=f"The Discord user '{discord_username}' is not a member of this server. They need to join first.",
                                    color=discord.Color.orange()
                                )
                            )
                            return
                except (ValueError, discord.NotFound):
                    # If not a valid ID, try to find by username
                    for member in ctx.guild.members:
                        if (member.name.lower() == discord_username.lower() or 
                            member.display_name.lower() == discord_username.lower() or
                            str(member).lower() == discord_username.lower()):
                            discord_user = member
                            break
            
            if not discord_user:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Discord User Not Found",
                        description=f"Could not find Discord user '{discord_username}' in this server. They may need to join the server first.",
                        color=discord.Color.orange()
                    )
                )
                return
            
            # Check if user is already in the channel
            if ctx.channel.permissions_for(discord_user).view_channel:
                await ctx.send(
                    embed=create_embed(
                        title=":information_source: User Already Has Access",
                        description=f"{discord_user.mention} already has access to this channel.",
                        color=discord.Color.blue()
                    )
                )
                return
            
            # Add user to the channel
            try:
                await ctx.channel.set_permissions(discord_user, view_channel=True, send_messages=True, read_message_history=True)
                
                # Send success message
                await ctx.send(
                    embed=create_embed(
                        title=":white_check_mark: User Added Successfully",
                        description=(
                            f"Successfully added {discord_user.mention} to this channel!\n\n"
                            f"**Nation:** [{nation['nation_name']}](https://politicsandwar.com/nation/id={nation_id})\n"
                            f"**Leader:** {nation['leader_name']}\n"
                            f"**Discord:** {discord_username}"
                        ),
                        color=discord.Color.green()
                    )
                )
                
                info(f"User {ctx.author} added {discord_username} (nation {nation_id}) to channel {ctx.channel.name}", tag="USER")
                
            except discord.Forbidden:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Permission Error",
                        description="I don't have permission to manage this channel's permissions.",
                        color=discord.Color.red()
                    )
                )
            except Exception as e:
                error(f"Error adding user to channel: {e}", tag="USER")
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Error",
                        description="An error occurred while adding the user to the channel. Please try again later.",
                        color=discord.Color.red()
                    )
                )
                
        except Exception as e:
            error(f"Error in add command: {e}", tag="USER")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while processing your request. Please try again later.",
                    color=discord.Color.red()
                )
            )

    @commands.command(name="rm")
    async def remove_nation(self, ctx: commands.Context, target: str):
        """Remove a nation's Discord user from the current channel."""
        try:
            # Check if user has permission to manage channels
            if not ctx.author.guild_permissions.manage_channels:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Permission Denied",
                        description="You need the 'Manage Channels' permission to use this command.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Try to parse as nation ID first
            nation_id = None
            discord_user = None
            nation_name = None
            
            try:
                nation_id = int(target)
                # Get nation data to verify the nation exists and get Discord info
                nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
                if nation:
                    discord_username = nation.get('discord')
                    nation_name = nation['nation_name']
                    
                    # First try to find by Discord ID from registrations
                    registrations = self.load_registrations()
                    for user_id, user_data in registrations.items():
                        reg_nation_id = user_data.get('nation_id') if isinstance(user_data, dict) else user_data
                        if str(reg_nation_id) == str(nation_id):
                            try:
                                # Try to get the member from the guild first
                                discord_user = ctx.guild.get_member(int(user_id))
                                if not discord_user:
                                    # If not found as member, try to fetch member
                                    try:
                                        discord_user = await ctx.guild.fetch_member(int(user_id))
                                    except discord.NotFound:
                                        # If still not found, try to fetch user to confirm they exist
                                        await self.bot.fetch_user(int(user_id))
                                        await ctx.send(
                                            embed=create_embed(
                                                title=":warning: User Not in Server",
                                                description=f"The Discord user for this nation is not a member of this server.",
                                                color=discord.Color.orange()
                                            )
                                        )
                                        return
                                break
                            except (ValueError, discord.NotFound):
                                continue
                    
                    # If not found in registrations, try the discord field from nation data
                    if not discord_user and discord_username:
                        try:
                            # Try to parse as Discord ID first
                            user_id = int(discord_username)
                            discord_user = ctx.guild.get_member(user_id)
                            if not discord_user:
                                # If not found as member, try to fetch member
                                try:
                                    discord_user = await ctx.guild.fetch_member(user_id)
                                except discord.NotFound:
                                    # If still not found, try to fetch user to confirm they exist
                                    await self.bot.fetch_user(user_id)
                                    await ctx.send(
                                        embed=create_embed(
                                            title=":warning: User Not in Server",
                                            description=f"The Discord user '{discord_username}' is not a member of this server.",
                                            color=discord.Color.orange()
                                        )
                                    )
                                    return
                        except (ValueError, discord.NotFound):
                            # If not a valid ID, try to find by username
                            for member in ctx.guild.members:
                                if (member.name.lower() == discord_username.lower() or 
                                    member.display_name.lower() == discord_username.lower() or
                                    str(member).lower() == discord_username.lower()):
                                    discord_user = member
                                    break
            except ValueError:
                # Not a number, try to parse as Discord mention or username
                pass
            
            # If we didn't find by nation ID, try to parse as Discord mention or username
            if not discord_user:
                # Check if it's a mention
                if target.startswith('<@') and target.endswith('>'):
                    user_id = target[2:-1]  # Remove <@ and >
                    if user_id.startswith('!'):  # Remove ! if present
                        user_id = user_id[1:]
                    try:
                        discord_user = await self.bot.fetch_user(int(user_id))
                    except (ValueError, discord.NotFound):
                        pass
                
                # If still not found, try to find by username
                if not discord_user:
                    for member in ctx.guild.members:
                        if (member.name.lower() == target.lower() or 
                            member.display_name.lower() == target.lower() or
                            str(member).lower() == target.lower()):
                            discord_user = member
                            break
            
            if not discord_user:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: User Not Found",
                        description="Could not find the specified user. Please provide a valid nation ID, Discord mention, or username.",
                        color=discord.Color.red()
                    )
                )
                return
            
            # Check if user currently has access to the channel
            if not ctx.channel.permissions_for(discord_user).view_channel:
                await ctx.send(
                    embed=create_embed(
                        title=":information_source: User Already Removed",
                        description=f"{discord_user.mention} already doesn't have access to this channel.",
                        color=discord.Color.blue()
                    )
                )
                return
            
            # Remove user from the channel
            try:
                await ctx.channel.set_permissions(discord_user, overwrite=None)
                
                # Send success message
                description = f"Successfully removed {discord_user.mention} from this channel!"
                if nation_name:
                    description += f"\n\n**Nation:** [{nation_name}](https://politicsandwar.com/nation/id={nation_id})"
                
                await ctx.send(
                    embed=create_embed(
                        title=":white_check_mark: User Removed Successfully",
                        description=description,
                        color=discord.Color.green()
                    )
                )
                
                info(f"User {ctx.author} removed {discord_user} from channel {ctx.channel.name}", tag="USER")
                
            except discord.Forbidden:
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Permission Error",
                        description="I don't have permission to manage this channel's permissions.",
                        color=discord.Color.red()
                    )
                )
            except Exception as e:
                error(f"Error removing user from channel: {e}", tag="USER")
                await ctx.send(
                    embed=create_embed(
                        title=":warning: Error",
                        description="An error occurred while removing the user from the channel. Please try again later.",
                        color=discord.Color.red()
                    )
                )
                
        except Exception as e:
            error(f"Error in rm command: {e}", tag="USER")
            await ctx.send(
                embed=create_embed(
                    title=":warning: Error",
                    description="An error occurred while processing your request. Please try again later.",
                    color=discord.Color.red()
                )
            )

    @app_commands.command(name="register", description="Register your Politics and War nation with your Discord account.")
    @app_commands.describe(nation_id="Your Politics and War nation ID")
    async def register(self, interaction: discord.Interaction, nation_id: int):
        """Register a user's PnW nation with their Discord account."""
        await interaction.response.defer()
        
        try:
            # Get nation data to verify the nation exists
            nation = get_data.GET_NATION_DATA(nation_id, self.config.API_KEY)
            if not nation:
                await interaction.followup.send(
                    embed=create_embed(
                        title=":warning: Nation Not Found",
                        description="Could not find a nation with that ID. Please check the ID and try again.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Load current registrations
            registrations = self.load_registrations()
            
            # Check if this nation is already registered
            for user_id, user_data in registrations.items():
                reg_nation_id = user_data.get('nation_id') if isinstance(user_data, dict) else user_data
                if str(reg_nation_id) == str(nation_id):
                    await interaction.followup.send(
                        embed=create_embed(
                            title=":warning: Nation Already Registered",
                            description=f"This nation is already registered to <@{user_id}>.",
                            color=discord.Color.orange()
                        ),
                        ephemeral=True
                    )
                    return
            
            # Register the nation with user info
            registrations[str(interaction.user.id)] = {
                'nation_id': nation_id,
                'discord_name': str(interaction.user),
                'nation_name': nation['nation_name']
            }
            self.save_registrations(registrations)
            
            # Send confirmation
            await interaction.followup.send(
                embed=create_embed(
                    title=":white_check_mark: Registration Successful",
                    description=(
                        f"Successfully registered your nation:\n"
                        f"**Discord User:** {interaction.user}\n"
                        f"**Nation:** [{nation['nation_name']}](https://politicsandwar.com/nation/id={nation_id})\n"
                        f"**Leader:** {nation['leader_name']}"
                    ),
                    color=discord.Color.green()
                )
            )
            
            info(f"User {interaction.user} registered nation {nation_id}", tag="USER")
            
        except Exception as e:
            error(f"Error in register command: {e}", tag="USER")
            await interaction.followup.send(
                embed=create_embed(
                    title=":warning: Registration Failed",
                    description="An error occurred while registering your nation. Please try again later.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    """Set up the user cog."""
    await bot.add_cog(UserCog(bot)) 