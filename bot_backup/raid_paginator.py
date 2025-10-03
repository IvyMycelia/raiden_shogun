import discord
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class RaidPaginator:
    """Paginator for raid results with 3x3 grid display."""
    
    def __init__(self, targets: List[Dict[str, Any]], min_score: float, max_score: float):
        self.targets = targets
        self.min_score = min_score
        self.max_score = max_score
        self.targets_per_page = 9  # 3x3 grid
        self.total_pages = (len(targets) + self.targets_per_page - 1) // self.targets_per_page
        self.current_page = 0
    
    def get_page_targets(self, page: int) -> List[Dict[str, Any]]:
        """Get targets for a specific page."""
        start_idx = page * self.targets_per_page
        end_idx = start_idx + self.targets_per_page
        return self.targets[start_idx:end_idx]
    
    def create_embed(self, page: int) -> discord.Embed:
        """Create embed for a specific page."""
        page_targets = self.get_page_targets(page)
        
        embed = discord.Embed(
            title=f"⚔️ Raid Targets ({self.min_score:.0f}-{self.max_score:.0f} Score)",
            description=f"Page {page + 1}/{self.total_pages} • {len(self.targets)} total targets",
            color=0x5865F2
        )
        
        if not page_targets:
            embed.description = "No valid raid targets found in your range."
            return embed
        
        # Create 3x3 grid display
        for i, target in enumerate(page_targets):
            row = i // 3
            col = i % 3
            
            # Create nation link
            nation_link = f"[{target['nation_name']}](https://politicsandwar.com/nation/war/declare/id={target['nation_id']})"
            
            # Format military units
            military = f"🛡️ {target['soldiers']:,} | 🚗 {target['tanks']:,} | ✈️ {target['aircraft']:,} | 🚢 {target['ships']:,} | 🕵️ {target['spies']:,}"
            
            # Format alliance
            alliance = target.get('alliance', 'None')
            if alliance == 'None':
                alliance = "No Alliance"
            
            # Create field value
            field_value = (
                f"**Leader:** {target['leader_name']}\n"
                f"**Score:** {target['score']:.0f} | **Cities:** {target['cities']}\n"
                f"**Alliance:** {alliance}\n"
                f"**Military:** {military}\n"
                f"**Loot Potential:** ${target['loot_potential']:,.0f}"
            )
            
            # Add field (using position in grid as field name)
            position = f"{chr(65 + row)}{col + 1}"  # A1, A2, A3, B1, B2, B3, etc.
            embed.add_field(
                name=f"{position}. {nation_link}",
                value=field_value,
                inline=True
            )
        
        # Add pagination info
        embed.set_footer(
            text=f"Use buttons to navigate • Showing {len(page_targets)} targets",
            icon_url="https://politicsandwar.com/img/flags/usa.png"
        )
        embed.timestamp = datetime.now(timezone.utc)
        
        return embed
    
    def get_view(self) -> 'RaidPaginatorView':
        """Get the view with navigation buttons."""
        return RaidPaginatorView(self)

class RaidPaginatorView(discord.ui.View):
    """View with navigation buttons for raid paginator."""
    
    def __init__(self, paginator: RaidPaginator):
        super().__init__(timeout=300)  # 5 minute timeout
        self.paginator = paginator
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page."""
        # Clear existing buttons
        self.clear_items()
        
        # First page button
        first_btn = discord.ui.Button(
            label="⏮️ First",
            style=discord.ButtonStyle.secondary,
            disabled=self.paginator.current_page == 0
        )
        first_btn.callback = self.first_page
        self.add_item(first_btn)
        
        # Previous page button
        prev_btn = discord.ui.Button(
            label="◀️ Previous",
            style=discord.ButtonStyle.primary,
            disabled=self.paginator.current_page == 0
        )
        prev_btn.callback = self.previous_page
        self.add_item(prev_btn)
        
        # Page info button (disabled)
        page_btn = discord.ui.Button(
            label=f"Page {self.paginator.current_page + 1}/{self.paginator.total_pages}",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        self.add_item(page_btn)
        
        # Next page button
        next_btn = discord.ui.Button(
            label="Next ▶️",
            style=discord.ButtonStyle.primary,
            disabled=self.paginator.current_page >= self.paginator.total_pages - 1
        )
        next_btn.callback = self.next_page
        self.add_item(next_btn)
        
        # Last page button
        last_btn = discord.ui.Button(
            label="Last ⏭️",
            style=discord.ButtonStyle.secondary,
            disabled=self.paginator.current_page >= self.paginator.total_pages - 1
        )
        last_btn.callback = self.last_page
        self.add_item(last_btn)
    
    async def first_page(self, interaction: discord.Interaction):
        """Go to first page."""
        self.paginator.current_page = 0
        embed = self.paginator.create_embed(0)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page."""
        if self.paginator.current_page > 0:
            self.paginator.current_page -= 1
            embed = self.paginator.create_embed(self.paginator.current_page)
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page."""
        if self.paginator.current_page < self.paginator.total_pages - 1:
            self.paginator.current_page += 1
            embed = self.paginator.create_embed(self.paginator.current_page)
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def last_page(self, interaction: discord.Interaction):
        """Go to last page."""
        self.paginator.current_page = self.paginator.total_pages - 1
        embed = self.paginator.create_embed(self.paginator.current_page)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

