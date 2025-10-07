import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime
import logging

from bot.config.settings import config
from bot.services.alliance_service import AllianceService
from bot.services.nation_service import NationService
from bot.services.cache_service import CacheService
from bot.utils.pagination import ActivityPaginator
from bot.utils.helpers import create_embed

logger = logging.getLogger('raiden_shogun')

def get_discord_username_with_fallback(member: dict, cache_service) -> str:
    """Get Discord username with proper fallback order: registrations -> API -> N/A."""
    nation_id = str(member.get('id', ''))
    
    # First try registrations
    registrations = cache_service.load_registrations()
    for discord_id, data in registrations.items():
        if str(data.get('nation_id')) == nation_id:
            # Prefer discord_username (exact username) over discord_name (display name)
            return data.get('discord_username', data.get('discord_name', 'N/A'))
    
    # Then try API data from member
    discord_username = member.get('discord', '')
    if discord_username:
        return discord_username
    
    # Finally return N/A
    return 'N/A'

class ActivityAuditCog(commands.Cog):
    """Cog for activity audit commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = config
        self.alliance_service = AllianceService()
        self.nation_service = NationService()
        self.cache_service = CacheService()
    
    async def get_discord_username(self, nation_id: int, member_data: dict = None) -> str:
        """Get Discord username for a nation ID with API fallback."""
        try:
            discord_username = self.cache_service.get_discord_username(nation_id)
            if discord_username and discord_username != 'N/A':
                return discord_username
            
            if member_data:
                if member_data.get('discord_username'):
                    return member_data['discord_username']
                elif member_data.get('discord'):
                    return member_data['discord']
            
            nation = await self.nation_service.get_nation(nation_id)
            if nation and hasattr(nation, 'discord_username') and nation.discord_username:
                return nation.discord_username
            elif nation and hasattr(nation, 'discord') and nation.discord:
                return nation.discord
        except Exception as e:
            logger.error(f"Error fetching Discord username for nation {nation_id}: {e}")
        
        return 'N/A'
    
    @app_commands.command(name="activity", description="Audit alliance members for activity requirements.")
    async def activity_audit(self, interaction: discord.Interaction):
        """Audit alliance members for activity requirements."""
        await interaction.response.defer()
        
        # Start audit without progress message
        
        try:
            members = await self.alliance_service.get_alliance_members(config.ALLIANCE_ID)
            if members is None:
                await interaction.followup.send(
                    embed=create_embed(
                        title="Error Fetching Alliance Members",
                        description="Failed to fetch alliance members. Please try again later.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Get detailed nation data for all members in a single batch API call
            nation_ids = [member['id'] for member in members]
            detailed_members_data = await self.nation_service.api.get_nations_batch_data(nation_ids)
            
            if not detailed_members_data:
                await interaction.followup.send(
                    embed=create_embed(
                        title="Error Fetching Detailed Data",
                        description="Failed to fetch detailed nation data. Please try again later.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            
            # Merge detailed data with basic member data
            for member in members:
                member_id = member['id']
                if member_id in detailed_members_data:
                    member.update(detailed_members_data[member_id])
            
            audit_results = []
            current_time = time.time()
            one_day_seconds = 86400
            needers = []
            
            for member in members:
                if member.get("alliance_position", "") == "APPLICANT":
                    continue
                
                last_active_str = member.get("last_active", "1970-01-01T00:00:00+00:00")
                try:
                    last_active_dt = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
                    last_active_unix = last_active_dt.timestamp()
                    
                    if (current_time - last_active_unix) >= one_day_seconds:
                        nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                        discord_username = await self.get_discord_username(member['id'], member)
                        result = (
                            f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                            f"**Nation:** {member['nation_name']}\n"
                            f"**Last Active:** <t:{int(last_active_unix)}:F>\n"
                            f"**Defensive Wars:** {member['defensive_wars_count']}\n"
                            f"**Discord:** {discord_username}"
                        )
                        audit_results.append(result)
                        needers.append(f"@{discord_username}")
                except ValueError:
                    logger.error(f"Error parsing last_active for {member['leader_name']}")
                    audit_results.append(f"Error parsing last_active for {member['leader_name']}")
            
            # Update progress message with results
            if audit_results:
                paginator = ActivityPaginator(audit_results)
                await progress_msg.edit(embed=paginator.get_embed(), view=paginator)
            else:
                embed = create_embed(
                    title="Activity Audit Complete",
                    description="No violations found for activity audit!",
                    color=discord.Color.green()
                )
                await progress_msg.edit(embed=embed)
            
            # Send summary with violators
            if needers:
                violators_text = " ".join(needers)
                await interaction.followup.send(
                    f"```### The Following People Need To Log In\n{violators_text}```"
                )
            else:
                await interaction.followup.send(
                    "```### The Following People Need To Log In\nNo Violators!```"
                )
            
            logger.info(f"Activity audit completed for {len(members)} members of alliance: {config.ALLIANCE_ID}")
        
        except Exception as e:
            logger.error(f"Error in activity audit command: {e}")
            try:
                await progress_msg.edit(
                    embed=create_embed(
                        title="Activity Audit Error",
                        description="An error occurred while performing the activity audit. Please try again later.",
                        color=discord.Color.red()
                    )
                )
            except:
                pass

async def run_activity_audit(interaction: discord.Interaction, alliance_service, nation_service, cache_service):
    """Run activity audit logic."""
    try:
        members = await alliance_service.get_alliance_members(config.ALLIANCE_ID)
        if members is None:
            await interaction.followup.send("Error fetching alliance members.", ephemeral=True)
            return
        
        # Get detailed nation data for all members in a single batch API call
        nation_ids = [member['id'] for member in members]
        detailed_members_data = await nation_service.api.get_nations_batch_data(nation_ids)
        
        if not detailed_members_data:
            await interaction.followup.send("Error fetching detailed data.", ephemeral=True)
            return
        
        # Merge detailed data with basic member data
        for member in members:
            member_id = member['id']
            if member_id in detailed_members_data:
                member.update(detailed_members_data[member_id])
        
        audit_results = []
        current_time = time.time()
        one_day_seconds = 86400
        needers = []
        
        for member in members:
            if member.get("alliance_position", "") == "APPLICANT":
                continue
            
            last_active_str = member.get("last_active", "1970-01-01T00:00:00+00:00")
            try:
                last_active_dt = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
                last_active_unix = last_active_dt.timestamp()
                
                if (current_time - last_active_unix) >= one_day_seconds:
                    nation_url = f"https://politicsandwar.com/nation/id={member['id']}"
                    discord_username = get_discord_username_with_fallback(member, cache_service)
                    result = (
                        f"**Leader:** [{member['leader_name']}]({nation_url})\n"
                        f"**Nation:** {member['nation_name']}\n"
                        f"**Last Active:** <t:{int(last_active_unix)}:F>\n"
                        f"**Defensive Wars:** {member['defensive_wars_count']}\n"
                        f"**Discord:** {discord_username}"
                    )
                    audit_results.append(result)
                    needers.append(f"@{discord_username}")
            except ValueError:
                logger.error(f"Error parsing last_active for {member['leader_name']}")
                audit_results.append(f"Error parsing last_active for {member['leader_name']}")
        
        # Send results
        if audit_results:
            paginator = ActivityPaginator(audit_results)
            await interaction.edit_original_response(embed=paginator.get_embed(), view=paginator)
        else:
            embed = create_embed(
                title="Activity Audit Complete",
                description="No violations found for activity audit!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed)
        
        # Send summary with violators in codeblock
        if needers:
            violators_text = " ".join(needers)
            await interaction.followup.send(f"```The Following People Need To Login: {violators_text}```")
        
    except Exception as e:
        logger.error(f"Error in activity audit: {e}")
        await interaction.followup.send("Error running activity audit.", ephemeral=True)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(ActivityAuditCog(bot))
