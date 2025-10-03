import discord
from datetime import datetime, timezone
from typing import List, Dict

class PurgePaginator(discord.ui.View):
    """Paginator for purge results with 3x2 grid layout."""
    
    def __init__(self, targets: List[Dict], timeout: int = 300):
        super().__init__(timeout=timeout)
        self.targets = targets
        self.current_page = 0
        self.items_per_page = 6  # 3x2 grid
        self.pages = []
        self.create_pages()
    
    def create_pages(self) -> None:
        """Split targets into pages."""
        for i in range(0, len(self.targets), self.items_per_page):
            page = self.targets[i:i + self.items_per_page]
            self.pages.append(page)
    
    def get_embed(self) -> discord.Embed:
        """Get current page's embed."""
        page_targets = self.pages[self.current_page]
        
        embed = discord.Embed(
            title="<:purple:1423182746385252392> **Purge Targets Found**",
            description=f"**Page {self.current_page + 1}/{len(self.pages)}** • {len(self.targets)} total targets",
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Create 3x2 grid
        for i, target in enumerate(page_targets):
            nation = target['nation_data']
            city_count = target['city_count']
            
            # Create target info with emojis
            target_info = f"**Score:** {nation['score']:,}\n"
            target_info += f"**Cities:** {city_count}\n"
            target_info += f"**Alliance:** {nation.get('alliance_name', 'None')}\n"
            target_info += f"**Position:** {nation.get('alliance_position', 'None')}\n"
            
            # Calculate estimated color bonus (higher score = more bonus)
            estimated_bonus = min(nation['score'] / 100, 20)  # Rough estimate
            target_info += f"**Est. Color Bonus:** +{estimated_bonus:.1f}%\n"
            
            # Add war declare link
            target_info += f"[**Declare War**](https://politicsandwar.com/nation/war/declare/id={nation['id']}) - [Link](https://politicsandwar.com/nation/id={nation['id']})"
            
            # Add field (3 columns)
            embed.add_field(
                name=f"**{nation['nation_name']}** (ID: {nation['id']})",
                value=target_info,
                inline=True
            )
        
        embed.set_footer(text="Use buttons to navigate • Higher score = more color bonus when defeated")
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
    
    @discord.ui.button(label="First", style=discord.ButtonStyle.secondary)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle first page button."""
        if self.current_page != 0:
            self.current_page = 0
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Last", style=discord.ButtonStyle.secondary)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle last page button."""
        if self.current_page != len(self.pages) - 1:
            self.current_page = len(self.pages) - 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.defer()
