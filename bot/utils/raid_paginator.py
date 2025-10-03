import discord
from datetime import datetime, timezone
from typing import List, Dict

class RaidPaginator(discord.ui.View):
    """Paginator for raid results with 3x2 grid layout."""
    
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
            title="**Raid Targets Found**",
            description=f"**Page {self.current_page + 1}/{len(self.pages)}** • {len(self.targets)} total targets",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Create 3x2 grid
        for i, target in enumerate(page_targets):
            nation = target['nation_data']
            
            # Create target info with emojis
            target_info = f"**Score:** {nation['score']:,}\n"
            target_info += f"**Cities:** {len(target['cities_data'])}\n"
            target_info += f"**Alliance:** {nation.get('alliance_name', 'None')}\n"
            
            # Military units in top-down order with emojis
            target_info += f"**Military:**\n"
            target_info += f"🪖 {nation['soldiers']:,} soldiers\n"
            target_info += f"<:tank:1357398163442635063> {nation['tanks']:,} tanks\n"
            target_info += f"✈️ {nation['aircraft']:,} aircraft\n"
            target_info += f"🚢 {nation['ships']:,} ships\n"
            
            # Loot with money emoji
            target_info += f"💰 **Loot:** ${target['loot_potential']:,.0f}\n"
            
            # Add war declare link
            target_info += f"[**Declare War**](https://politicsandwar.com/nation/war/declare/id={nation['id']})"
            
            # Add field (3 columns)
            embed.add_field(
                name=f"**{nation['nation_name']}** (ID: {nation['id']})",
                value=target_info,
                inline=True
            )
        
        embed.set_footer(text="Use buttons to navigate • Bot Maintained By Ivy Banana <3")
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
