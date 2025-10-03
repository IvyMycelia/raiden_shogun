import discord
from discord.ext import commands
import json
import re
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger('raiden_shogun')

class GeneralHelpPaginator(discord.ui.View):
    """Interactive paginator for general help."""
    
    def __init__(self, commands_data: Dict, per_page: int = 8, timeout: int = 300, is_admin: bool = False):
        super().__init__(timeout=timeout)
        self.commands_data = commands_data
        self.per_page = per_page
        self.current_page = 1
        self.is_admin = is_admin
        
        # Get all visible commands grouped by category
        self.categories = {}
        for category_key, category_info in commands_data.get("categories", {}).items():
            commands_in_category = [
                cmd for cmd in commands_data.get("commands", [])
                if cmd.get("category") == category_key and (self.is_admin or not cmd.get("hidden", False))
            ]
            if commands_in_category:
                self.categories[category_key] = {
                    'info': category_info,
                    'commands': commands_in_category
                }
        
        self.category_keys = list(self.categories.keys())
        self.total_pages = max(1, len(self.category_keys))
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page."""
        self.first_page.disabled = self.current_page <= 1
        self.previous_page.disabled = self.current_page <= 1
        self.next_page.disabled = self.current_page >= self.total_pages
        self.last_page.disabled = self.current_page >= self.total_pages
    
    def create_embed(self) -> discord.Embed:
        """Create embed for current page."""
        embed = discord.Embed(
            title="🤖 **Raiden Shogun Help**",
            description=self.commands_data.get("general", {}).get("description", "A comprehensive Politics and War Discord bot"),
            color=discord.Color.green()
        )
        
        # Show current page categories
        start_idx = (self.current_page - 1) * self.per_page
        end_idx = min(start_idx + self.per_page, len(self.category_keys))
        
        for i in range(start_idx, end_idx):
            category_key = self.category_keys[i]
            category_data = self.categories[category_key]
            category_info = category_data['info']
            commands = category_data['commands']
            
            category_commands = ", ".join([f"`/{cmd['name']}`" for cmd in commands[:5]])
            if len(commands) > 5:
                category_commands += f" (+{len(commands) - 5} more)"
            
            embed.add_field(
                name=f"{category_info.get('emoji', '📋')} {category_info.get('name', category_key.title())}",
                value=f"{category_info.get('description', '')}\n{category_commands}",
                inline=False
            )
        
        embed.add_field(
            name="🔍 **Search Commands**",
            value=f"Use `/help <keyword>` to search for specific commands\nExample: `/help raid` or `/help spy`",
            inline=False
        )
        
        embed.set_footer(text=f"Page {self.current_page}/{self.total_pages} • Use /help <command_name> for details")
        return embed
    
    @discord.ui.button(label="First", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to first page."""
        if self.current_page > 1:
            self.current_page = 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Last", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to last page."""
        if self.current_page < self.total_pages:
            self.current_page = self.total_pages
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    # Close button removed per requirements

class HelpPaginator(discord.ui.View):
    """Interactive paginator for help search results."""
    
    def __init__(self, results: List[Dict], query: str, per_page: int = 6, timeout: int = 300, is_admin: bool = False):
        super().__init__(timeout=timeout)
        # Filter hidden commands for non-admins
        if not is_admin:
            self.results = [r for r in results if not r.get("hidden", False)]
        else:
            self.results = results
        self.query = query
        self.per_page = per_page
        self.current_page = 1
        self.total_pages = max(1, (len(results) + per_page - 1) // per_page)
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page."""
        self.first_page.disabled = self.current_page <= 1
        self.previous_page.disabled = self.current_page <= 1
        self.next_page.disabled = self.current_page >= self.total_pages
        self.last_page.disabled = self.current_page >= self.total_pages
    
    def get_page_items(self) -> List[Dict]:
        """Get items for current page."""
        start = (self.current_page - 1) * self.per_page
        end = start + self.per_page
        return self.results[start:end]
    
    def create_embed(self) -> discord.Embed:
        """Create embed for current page."""
        page_items = self.get_page_items()
        
        embed = discord.Embed(
            title=f"🔍 **Search Results for \"{self.query}\"**",
            description=f"Found {len(self.results)} matching command(s) • Page {self.current_page}/{self.total_pages}",
            color=discord.Color.blue()
        )
        
        # Group results by category
        categories = {}
        for result in page_items:
            category = result.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Add results grouped by category
        for category, commands in categories.items():
            category_info = {
                "nation": {"name": "Nation Commands", "emoji": "🏴"},
                "alliance": {"name": "Alliance Commands", "emoji": "🤝"},
                "user": {"name": "User Commands", "emoji": "👤"},
                "admin": {"name": "Admin Commands", "emoji": "⚙️"},
                "war": {"name": "War Commands", "emoji": "⚔️"},
                "utility": {"name": "Utility Commands", "emoji": "🔧"}
            }.get(category, {"name": category.title(), "emoji": "📋"})
            
            field_value = ""
            for cmd in commands:
                field_value += f"**/{cmd['name']}** - {cmd['description']}\n"
            
            embed.add_field(
                name=f"{category_info['emoji']} {category_info['name']}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text="Use /help <command_name> for details • Use buttons to navigate")
        return embed
    
    @discord.ui.button(label="First", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to first page."""
        if self.current_page > 1:
            self.current_page = 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Last", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to last page."""
        if self.current_page < self.total_pages:
            self.current_page = self.total_pages
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()
    
    # Close button removed per requirements

class HelpCog(commands.Cog):
    """Help system with regex-based command search."""
    
    def __init__(self, bot):
        self.bot = bot
        self.commands_data = self.load_commands_data()
    
    def load_commands_data(self) -> Dict:
        """Load commands documentation from JSON file."""
        try:
            docs_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'commands.json')
            with open(docs_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading commands data: {e}")
            return {"commands": [], "categories": {}, "general": {}}
    
    @commands.hybrid_command(name="help", description="Get help with bot commands")
    async def help_command(self, ctx, *, query: Optional[str] = None):
        """Help command with regex-based search."""
        try:
            # Determine requesting user id (works for both prefix and slash)
            user_id = None
            try:
                if hasattr(ctx, 'author') and getattr(ctx.author, 'id', None):
                    user_id = ctx.author.id
                elif hasattr(ctx, 'interaction') and getattr(ctx.interaction, 'user', None):
                    user_id = ctx.interaction.user.id
            except Exception:
                user_id = None
            if query:
                # Check if query matches a specific command name exactly
                exact_match = self.find_exact_command(query)
                if exact_match:
                    await self.send_command_details(ctx, exact_match)
                else:
                    # Search for commands matching the query
                    results = self.search_commands(query, user_id=user_id)
                    if results:
                        # Use interactive pagination for multiple results
                        if len(results) > 6:  # Only show paginator if more than 6 results
                            paginator = HelpPaginator(results, query)
                            embed = paginator.create_embed()
                            await ctx.send(embed=embed, view=paginator)
                        else:
                            # Show all results in a single embed for small result sets
                            await self.send_search_results(ctx, query, results)
                    else:
                        await self.send_no_results(ctx, query)
            else:
                # Show general help
                await self.send_general_help(ctx)
                
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await ctx.send("❌ An error occurred while processing your help request.")
    
    def _is_admin(self, user_id: int) -> bool:
        return user_id == 860564164828725299

    def _filter_visible(self, commands_list: List[Dict], user_id: Optional[int]) -> List[Dict]:
        is_admin = self._is_admin(user_id) if user_id is not None else False
        filtered: List[Dict] = []
        for cmd in commands_list:
            if cmd.get("hidden", False) and not is_admin:
                continue
            filtered.append(cmd)
        return filtered

    def search_commands(self, query: str, user_id: Optional[int] = None) -> List[Dict]:
        """Search for commands matching the query using flexible regex."""
        query_lower = query.lower().strip()
        results = []
        
        # Split query into words for more flexible matching
        query_words = re.findall(r'\b\w+\b', query_lower)
        
        for command in self._filter_visible(self.commands_data.get("commands", []), user_id):
            command_name = command.get("name", "").lower()
            command_desc = command.get("description", "").lower()
            command_details = command.get("details", "").lower()
            command_keywords = [kw.lower() for kw in command.get("keywords", [])]
            command_aliases = [alias.lower() for alias in command.get("aliases", [])]
            
            # Priority 1: Exact command name match
            if query_lower == command_name:
                results.append(command)
                continue
            
            # Priority 2: Command name starts with query (only for short queries)
            if len(query_lower) <= 4 and command_name.startswith(query_lower):
                results.append(command)
                continue
            
            # Priority 3: Query starts with command name (for partial matches, only for short queries)
            if len(query_lower) <= 4 and query_lower.startswith(command_name):
                results.append(command)
                continue
            
            # Priority 4: Check aliases for exact matches only (for short queries)
            if len(query_lower) <= 4:
                for alias in command_aliases:
                    if query_lower == alias:
                        results.append(command)
                        break
            
            # Priority 5: Special sound-alike matches (only for short queries)
            if len(query_lower) <= 4:
                if query_lower in ["ra", "rai"] and command_name == "raid":
                    results.append(command)
                    continue
                if query_lower in ["pur", "purp"] and command_name == "purge":
                    results.append(command)
                    continue
                if query_lower in ["spy", "spi"] and command_name in ["spies", "intel"]:
                    results.append(command)
                    continue
            
            # Priority 6: Keyword matches (only for longer queries and exact word matches)
            if len(query_lower) > 4:
                for word in query_words:
                    for keyword in command_keywords:
                        # Only match if the word is at the start of the keyword or is the whole keyword
                        if keyword.startswith(word) or word == keyword:
                            results.append(command)
                            break
                    if command in results:
                        break
            
            # Priority 7: Description matches (only for longer queries and word boundaries)
            if len(query_lower) > 4:
                for word in query_words:
                    # Use word boundaries to avoid partial matches
                    if re.search(r'\b' + re.escape(word) + r'\b', command_desc) or re.search(r'\b' + re.escape(word) + r'\b', command_details):
                        results.append(command)
                        break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for result in results:
            if result["name"] not in seen:
                seen.add(result["name"])
                unique_results.append(result)
        
        return unique_results
    
    def find_exact_command(self, query: str) -> Optional[Dict]:
        """Find a command by exact name match."""
        query_lower = query.lower().strip()
        
        for command in self.commands_data.get("commands", []):
            if command.get("name", "").lower() == query_lower:
                return command
            
            # Check aliases
            for alias in command.get("aliases", []):
                if alias.lower() == query_lower:
                    return command
        
        return None
    
    async def send_command_details(self, ctx, command: Dict):
        """Send detailed information about a specific command."""
        embed = discord.Embed(
            title=f"📖 **Command: /{command['name']}**",
            description=command.get("description", ""),
            color=discord.Color.blue()
        )
        
        # Usage
        embed.add_field(
            name="📝 **Usage**",
            value=command.get('usage', 'N/A'),
            inline=False
        )
        
        # Details
        if command.get("details"):
            embed.add_field(
                name="📋 **Details**",
                value=command["details"],
                inline=False
            )
        
        # Examples
        if command.get("examples"):
            examples_text = "\n".join([f"• {ex}" for ex in command["examples"]])
            embed.add_field(
                name="💡 **Examples**",
                value=examples_text,
                inline=False
            )
        
        # Aliases
        if command.get("aliases") and len(command["aliases"]) > 1:
            aliases = [alias for alias in command["aliases"] if alias != command["name"]]
            if aliases:
                embed.add_field(
                    name="🔗 **Aliases**",
                    value=", ".join([f"`{alias}`" for alias in aliases]),
                    inline=True
                )
        
        # Category
        category = command.get("category", "other")
        category_info = self.commands_data.get("categories", {}).get(category, {})
        if category_info:
            embed.add_field(
                name="📂 **Category**",
                value=f"{category_info.get('emoji', '📋')} {category_info.get('name', category.title())}",
                inline=True
            )
        
        embed.set_footer(text="Use /help to see all commands or /help <keyword> to search")
        
        await ctx.send(embed=embed)
    
    def _paginate(self, items: List[Dict], page: int, per_page: int) -> List[Dict]:
        start = (page - 1) * per_page
        end = start + per_page
        return items[start:end]

    async def send_search_results(self, ctx, query: str, results: List[Dict]):
        """Send search results for a query (for small result sets)."""
        embed = discord.Embed(
            title=f"🔍 **Search Results for \"{query}\"**",
            description=f"Found {len(results)} matching command(s)",
            color=discord.Color.blue()
        )

        # Group results by category
        categories = {}
        for result in results:
            category = result.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Add results grouped by category
        for category, commands in categories.items():
            category_info = self.commands_data.get("categories", {}).get(category, {})
            category_name = category_info.get("name", category.title())
            category_emoji = category_info.get("emoji", "📋")
            
            field_value = ""
            for cmd in commands:
                field_value += f"**/{cmd['name']}** - {cmd['description']}\n"

            embed.add_field(
                name=f"{category_emoji} {category_name}",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text="Use /help <command_name> for details")
        
        await ctx.send(embed=embed)
    
    async def send_no_results(self, ctx, query: str):
        """Send message when no results found."""
        embed = discord.Embed(
            title="❌ **No Results Found**",
            description=f"No commands found matching \"{query}\"",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="💡 **Suggestions:**",
            value="• Try different keywords\n• Use broader search terms\n• Check spelling\n• Use `/help` to see all commands",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def send_general_help(self, ctx):
        """Send general help information with interactive pagination."""
        # Filter commands for the viewer
        viewer_id = None
        try:
            if hasattr(ctx, 'author') and getattr(ctx.author, 'id', None):
                viewer_id = ctx.author.id
            elif hasattr(ctx, 'interaction') and getattr(ctx.interaction, 'user', None):
                viewer_id = ctx.interaction.user.id
        except Exception:
            viewer_id = None
        
        # Create filtered commands data
        filtered_commands = self._filter_visible(self.commands_data.get("commands", []), viewer_id)
        filtered_data = {
            **self.commands_data,
            "commands": filtered_commands
        }
        
        # Use interactive paginator for general help
        paginator = GeneralHelpPaginator(filtered_data)
        embed = paginator.create_embed()
        await ctx.send(embed=embed, view=paginator)
    
    @help_command.autocomplete('query')
    async def help_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for help command query parameter."""
        if not current:
            return []
        
        suggestions = []
        current_lower = current.lower()
        
        # Get command names and aliases
        for command in self.commands_data.get("commands", []):
            if current_lower in command.get("name", "").lower():
                suggestions.append(command["name"])
            
            for alias in command.get("aliases", []):
                if current_lower in alias.lower() and alias not in suggestions:
                    suggestions.append(alias)
        
        # Get keywords
        for command in self.commands_data.get("commands", []):
            for keyword in command.get("keywords", []):
                if current_lower in keyword.lower() and keyword not in suggestions:
                    suggestions.append(keyword)
        
        # Limit to 25 suggestions
        return suggestions[:25]

async def setup(bot):
    await bot.add_cog(HelpCog(bot)) 