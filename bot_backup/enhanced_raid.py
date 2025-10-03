import asyncio
import discord
from typing import List, Dict, Any, Optional, Tuple

from bot.handler import info, error, warning
from bot.csv_raid import get_raid_system

async def enhanced_raid_logic(interaction, min_score: float, max_score: float, 
                            max_targets: int = 20, exclude_alliances: List[str] = None) -> Tuple[discord.Embed, discord.ui.View]:
    """Enhanced raid logic using CSV data for fast, reliable target finding."""
    try:
        info(f"Starting enhanced raid search for score range {min_score:.0f}-{max_score:.0f}", tag="RAID")
        
        # Get the CSV raid system
        raid_system = get_raid_system(interaction.client.config)
        
        # Find targets using CSV data
        targets = await raid_system.find_raid_targets(
            interaction=interaction,
            min_score=min_score,
            max_score=max_score,
            max_targets=max_targets,
            exclude_alliances=exclude_alliances
        )
        
        # Format and return results
        embed, view = raid_system.format_raid_results(targets, min_score, max_score)
        return embed, view
            
        except Exception as e:
        error(f"Error in enhanced raid logic: {e}", tag="RAID")
        
        # Return error embed
                        embed = discord.Embed(
            title="❌ Raid Search Error",
            description="An error occurred while searching for raid targets. Please try again later.",
            color=0xff6b6b
        )
        embed.add_field(
            name="Error Details",
            value=f"```{str(e)[:1000]}```",
            inline=False
        )
        
        # Return error embed with no view
        return embed, None