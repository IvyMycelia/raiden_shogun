"""
Helper utility functions.
"""

import discord
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

def create_embed(
    title: str,
    description: str,
    color: discord.Color = discord.Color.blue(),
    fields: Optional[List[Dict[str, Any]]] = None,
    footer: Optional[str] = None
) -> discord.Embed:
    """Create a standardized embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    return embed

def format_number(number: float, precision: int = 2) -> str:
    """Format a number with commas and specified decimal places."""
    return f"{number:,.{precision}f}"

def truncate_text(text: str, length: int) -> str:
    """Truncate text to specified length with ellipsis."""
    return text if len(text) <= length else text[:length-2] + ".."
