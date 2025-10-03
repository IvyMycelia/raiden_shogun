"""
Raid paginator for displaying raid targets.
"""
import discord
from typing import List, Dict, Any
from datetime import datetime, timezone

from models.nation import RaidTarget


class RaidPaginator(discord.ui.View):
    """Paginator for raid results."""
    
    def __init__(self, targets: List[RaidTarget], min_score: float, max_score: float, targets_per_page: int = 9):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.targets = targets
        self.min_score = min_score
        self.max_score = max_score
        self.targets_per_page = targets_per_page
        self.current_page = 0
        self.total_pages = (len(targets) + targets_per_page - 1) // targets_per_page
        
        self.update_buttons()

    def create_embed(self, page_num: int) -> discord.Embed:
        """Create embed for the current page."""
        start_index = page_num * self.targets_per_page
        end_index = min(start_index + self.targets_per_page, len(self.targets))
        
        embed = discord.Embed(
            title=f"⚔️ Raid Targets ({self.min_score:.0f}-{self.max_score:.0f} Score)",
            description=f"Found {len(self.targets)} potential raid targets. Showing page {page_num + 1}/{self.total_pages}",
            color=0x5865F2  # Discord blurple
        )
        
        if not self.targets:
            embed.description = "No valid raid targets found in your range."
            return embed
        
        for i, target in enumerate(self.targets[start_index:end_index], start_index + 1):
            nation = target.nation
            nation_id = nation.nation_id
            nation_name = nation.nation_name
            leader_name = nation.leader_name
            score = nation.score
            cities = nation.cities
            alliance = nation.alliance_name
            loot_potential = target.loot_potential
            soldiers = nation.soldiers
            tanks = nation.tanks
            aircraft = nation.aircraft
            ships = nation.ships
            spies = nation.spies

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
                    f"**Potential Loot:** {loot_str}\n"
                    f"**Risk:** {target.risk_level.title()}"
                ),
                inline=True
            )
        
        embed.set_footer(text="Data from Politics and War (CSV Cache)")
        embed.timestamp = datetime.now(timezone.utc)
        return embed

    def update_buttons(self):
        """Update pagination buttons."""
        self.clear_items()
        if self.total_pages > 1:
            self.add_item(self.prev_button)
            self.add_item(self.next_button)
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle previous page button."""
        if self.current_page > 0:
            self.current_page -= 1
            embed = self.create_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You are on the first page.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle next page button."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            embed = self.create_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You are on the last page.", ephemeral=True)

    def get_view(self):
        """Get the view for this paginator."""
        return self
