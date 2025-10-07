"""
Pagination utilities for Discord embeds.
"""

import discord
from typing import List, Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.constants import GameConstants
from datetime import datetime, timezone

class ActivityPaginator(discord.ui.View):
    """A paginator for displaying activity results."""
    
    def __init__(self, results: List[str], timeout: int = 120):
        super().__init__(timeout=timeout)
        self.results = results
        self.current_page = 0
        self.items_per_page = 4
        self.pages = []
        self.create_pages()
    
    def create_pages(self) -> None:
        """Split results into pages."""
        for i in range(0, len(self.results), self.items_per_page):
            page = self.results[i:i + self.items_per_page]
            self.pages.append(page)
        
        if not self.pages:
            self.pages.append(["**All Good!** No inactive members found."])
    
    def get_embed(self) -> discord.Embed:
        """Get the current page's embed."""
        page_results = self.pages[self.current_page].copy()
        
        # Ensure grid consistency
        if len(page_results) % 2 != 0:
            page_results.append("\u200b")
        
        fields = []
        for idx, result in enumerate(page_results, start=1):
            # Truncate field value to 1024 characters to avoid Discord limits
            truncated_result = result[:1021] + "..." if len(result) > 1024 else result
            fields.append({
                "name": "\u200b",
                "value": truncated_result,
                "inline": True
            })
        
        embed = discord.Embed(
            title="**Audit Results**",
            description="Below is a grid view of alliance members Violating the audit ran.\nUse the buttons below to navigate through pages.",
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc)
        )
        
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )
        
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} • Bot Maintained By Ivy Banana <3")
        return embed
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle previous page button."""
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle next page button."""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()

class Paginator:
    """Base paginator for Discord embeds."""
    
    def __init__(self, items: List[Any], items_per_page: int = 10, timeout: int = 300):
        self.items = items
        self.items_per_page = items_per_page
        self.timeout = timeout
        self.current_page = 0
        self.total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    def get_page_items(self, page: int) -> List[Any]:
        """Get items for a specific page."""
        start_index = page * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(self.items))
        return self.items[start_index:end_index]
    
    def create_embed(self, page: int, title: str, description: str = "", color: int = GameConstants.EMBED_COLOR_INFO) -> discord.Embed:
        """Create embed for a specific page."""
        embed = discord.Embed(title=title, description=description, color=color)
        
        page_items = self.get_page_items(page)
        for i, item in enumerate(page_items, start=page * self.items_per_page + 1):
            embed.add_field(
                name=f"{i}. {item}",
                value="",
                inline=False
            )
        
        embed.set_footer(text=f"Page {page + 1}/{self.total_pages}")
        return embed
    
    def get_view(self) -> 'PaginatorView':
        """Get pagination view."""
        return PaginatorView(self)

class RaidPaginator:
    """Paginator for raid targets with 3x3 grid layout."""
    
    def __init__(self, targets: List[Dict[str, Any]], min_score: float, max_score: float, 
                 targets_per_page: int = 9, timeout: int = 300):
        self.targets = targets
        self.min_score = min_score
        self.max_score = max_score
        self.targets_per_page = targets_per_page
        self.timeout = timeout
        self.current_page = 0
        self.total_pages = (len(targets) + targets_per_page - 1) // targets_per_page
    
    def create_embed(self, page: int) -> discord.Embed:
        """Create embed for raid targets page."""
        start_index = page * self.targets_per_page
        end_index = min(start_index + self.targets_per_page, len(self.targets))
        
        embed = discord.Embed(
            title=f"⚔️ Raid Targets ({self.min_score:.0f}-{self.max_score:.0f} Score)",
            description=f"Found {len(self.targets)} potential raid targets. Showing page {page + 1}/{self.total_pages}",
            color=GameConstants.EMBED_COLOR_RAID
        )
        
        if not self.targets:
            embed.description = "No valid raid targets found in your range."
            return embed
        
        for i, target in enumerate(self.targets[start_index:end_index], start_index + 1):
            nation_id = target['nation_id']
            nation_name = target['nation_name']
            leader_name = target['leader_name']
            score = target['score']
            cities = target['cities']
            alliance = target['alliance']
            loot_potential = target['loot_potential']
            soldiers = target.get('soldiers', 0)
            tanks = target.get('tanks', 0)
            aircraft = target.get('aircraft', 0)
            ships = target.get('ships', 0)
            spies = target.get('spies', 0)

            # Format loot potential
            if loot_potential >= 1_000_000_000:
                loot_str = f"${loot_potential/1_000_000_000:.1f}B"
            elif loot_potential >= 1_000_000:
                loot_str = f"${loot_potential/1_000_000:.1f}M"
            elif loot_potential >= 1_000:
                loot_str = f"${loot_potential/1_000:.1f}K"
            else:
                loot_str = f"${loot_potential:.0f}"
            
            nation_link = f"https://politicsandwar.com/nation/war/declare/id={nation_id}"

            embed.add_field(
                name=f"{i}. [{nation_name} ({nation_id})]({nation_link})",
                value=(
                    f"**Leader:** {leader_name}\n"
                    f"**Score:** {score:.0f}\n"
                    f"**Cities:** {cities}\n"
                    f"**Alliance:** {alliance}\n"
                    f"**Military:** S:{soldiers:,} T:{tanks:,} A:{aircraft:,} H:{ships:,} Sp:{spies:,}\n"
                    f"**Potential Loot:** {loot_str}"
                ),
                inline=True
            )
        
        embed.set_footer(text="Data from Politics and War (CSV Cache)")
        return embed
    
    def get_view(self) -> 'RaidPaginatorView':
        """Get pagination view."""
        return RaidPaginatorView(self)

class PaginatorView(discord.ui.View):
    """View for pagination controls."""
    
    def __init__(self, paginator: Paginator):
        super().__init__(timeout=paginator.timeout)
        self.paginator = paginator
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states."""
        self.clear_items()
        
        if self.paginator.total_pages > 1:
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Previous page button."""
        if self.paginator.current_page > 0:
            self.paginator.current_page -= 1
            embed = self.paginator.create_embed(self.paginator.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Next page button."""
        if self.paginator.current_page < self.paginator.total_pages - 1:
            self.paginator.current_page += 1
            embed = self.paginator.create_embed(self.paginator.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

class RaidPaginatorView(discord.ui.View):
    """View for raid pagination controls."""
    
    def __init__(self, paginator: RaidPaginator):
        super().__init__(timeout=paginator.timeout)
        self.paginator = paginator
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states."""
        self.clear_items()
        
        if self.paginator.total_pages > 1:
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Previous page button."""
        if self.paginator.current_page > 0:
            self.paginator.current_page -= 1
            embed = self.paginator.create_embed(self.paginator.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Next page button."""
        if self.paginator.current_page < self.paginator.total_pages - 1:
            self.paginator.current_page += 1
            embed = self.paginator.create_embed(self.paginator.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)
