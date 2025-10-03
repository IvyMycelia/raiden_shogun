import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from bot.handler import info, error, warning
from bot.utils.paginator import RaidPaginator, RaidView
import discord

class CachedRaidSystem:
    """Fast raid system using cached nation data."""
    
    def __init__(self, config):
        self.config = config
        
        # Resource production rates per day (from references.md)
        self.resource_production = {
            'coal_mines': 3,      # 3 tons/day per mine
            'iron_mines': 3,      # 3 tons/day per mine  
            'uranium_mines': 3,   # 3 tons/day per mine
            'oil_wells': 3,       # 3 tons/day per well
            'bauxite_mines': 3,   # 3 tons/day per mine
            'lead_mines': 3,      # 3 tons/day per mine
            'farms': 0           # Calculated separately based on land
        }
        
        # Resource market values (estimated)
        self.resource_values = {
            'coal': 50,      # $50/ton
            'iron': 100,     # $100/ton
            'uranium': 200,  # $200/ton
            'oil': 80,       # $80/ton
            'bauxite': 90,   # $90/ton
            'lead': 85,      # $85/ton
            'food': 30       # $30/ton
        }
        
        # Building costs (from references.md)
        self.building_costs = {
            'oil_power_plants': 7000,
            'coal_power_plants': 5000,
            'nuclear_power_plants': 500000,
            'wind_power_plants': 30000,
            'coal_mines': 1000,
            'iron_mines': 9500,
            'uranium_mines': 25000,
            'oil_wells': 50000,
            'bauxite_mines': 10000,
            'lead_mines': 10000,
            'farms': 1000,
            'oil_refineries': 45000,
            'steel_mills': 45000,
            'aluminum_refineries': 30000,
            'munitions_factories': 35000,
            'police_stations': 75000,
            'hospitals': 100000,
            'recycling_centers': 125000,
            'subways': 250000,
            'supermarkets': 5000,
            'banks': 15000,
            'shopping_malls': 45000,
            'stadiums': 100000,
            'barracks': 3000,
            'factories': 15000,
            'hangars': 100000,
            'drydocks': 250000
        }
        
        # Commerce bonuses (from references.md)
        self.commerce_bonuses = {
            'supermarkets': 0.03,    # 3% each
            'banks': 0.05,           # 5% each
            'shopping_malls': 0.09,  # 9% each
            'stadiums': 0.12,        # 12% each
            'subways': 0.08          # 8% each
        }

    def calculate_comprehensive_loot_potential(self, nation: dict, cities: list) -> dict:
        """Calculate comprehensive loot potential using cached data."""
        
        # 1. Infrastructure Loot (50% of infra value)
        total_infra = sum(city.get('infrastructure', 0) for city in cities)
        infra_cost_per_level = 100  # Base cost per infrastructure level
        infra_loot = total_infra * infra_cost_per_level * 0.50  # 50% loot rate
        
        # 2. Resource Production Revenue (daily production * 5 days)
        resource_loot = self.calculate_resource_production_loot(cities)
        
        # 3. Commerce Income (daily income * 5 days)
        commerce_loot = self.calculate_commerce_income_loot(cities)
        
        # 4. Building Value (40% of building costs)
        building_loot = self.calculate_building_value_loot(cities)
        
        total_loot = infra_loot + resource_loot + commerce_loot + building_loot
        
        return {
            'total': total_loot,
            'infrastructure': infra_loot,
            'resources': resource_loot,
            'commerce': commerce_loot,
            'buildings': building_loot,
            'breakdown': {
                'infra_levels': total_infra,
                'city_count': len(cities),
                'total_buildings': sum(sum(city.get(building, 0) for building in self.building_costs.keys()) for city in cities)
            }
        }

    def calculate_resource_production_loot(self, cities: list) -> float:
        """Calculate loot from resource production over 5 days."""
        total_loot = 0
        
        for city in cities:
            land = city.get('land', 0)
            
            # Coal mines: 3 tons/day * 5 days * $50/ton
            coal_production = city.get('coal_mines', 0) * 3 * 5 * self.resource_values['coal']
            
            # Iron mines: 3 tons/day * 5 days * $100/ton  
            iron_production = city.get('iron_mines', 0) * 3 * 5 * self.resource_values['iron']
            
            # Uranium mines: 3 tons/day * 5 days * $200/ton
            uranium_production = city.get('uranium_mines', 0) * 3 * 5 * self.resource_values['uranium']
            
            # Oil wells: 3 tons/day * 5 days * $80/ton
            oil_production = city.get('oil_wells', 0) * 3 * 5 * self.resource_values['oil']
            
            # Bauxite mines: 3 tons/day * 5 days * $90/ton
            bauxite_production = city.get('bauxite_mines', 0) * 3 * 5 * self.resource_values['bauxite']
            
            # Lead mines: 3 tons/day * 5 days * $85/ton
            lead_production = city.get('lead_mines', 0) * 3 * 5 * self.resource_values['lead']
            
            # Food production: Farms * (Land Area / 500) * 5 days * $30/ton
            food_production = city.get('farms', 0) * (land / 500) * 5 * self.resource_values['food']
            
            total_loot += coal_production + iron_production + uranium_production + \
                         oil_production + bauxite_production + lead_production + food_production
        
        return total_loot * 0.3  # 30% loot rate

    def calculate_commerce_income_loot(self, cities: list) -> float:
        """Calculate loot from commerce income over 5 days."""
        total_loot = 0
        
        for city in cities:
            infra = city.get('infrastructure', 0)
            base_income = infra * 100  # Base income per infra level
            
            # Commerce bonuses
            commerce_bonus = 1.0
            commerce_bonus += city.get('supermarkets', 0) * self.commerce_bonuses['supermarkets']
            commerce_bonus += city.get('banks', 0) * self.commerce_bonuses['banks']
            commerce_bonus += city.get('shopping_malls', 0) * self.commerce_bonuses['shopping_malls']
            commerce_bonus += city.get('stadiums', 0) * self.commerce_bonuses['stadiums']
            commerce_bonus += city.get('subways', 0) * self.commerce_bonuses['subways']
            
            daily_income = base_income * commerce_bonus
            total_loot += daily_income * 5  # 5 days of income
        
        return total_loot * 0.4  # 40% loot rate

    def calculate_building_value_loot(self, cities: list) -> float:
        """Calculate loot from building values."""
        total_building_value = 0
        
        for city in cities:
            for building, cost in self.building_costs.items():
                count = city.get(building, 0)
                total_building_value += count * cost
        
        return total_building_value * 0.40  # 40% loot rate

    async def cached_raid_logic(self, interaction: discord.Interaction, nation_id: int = None):
        """Fast raid logic using cached nation data."""
        interaction_responded = False
        
        try:
            # Get user's nation data
            if not nation_id:
                user_id = interaction.user.id
                try:
                    with open('data/registrations.json', 'r') as f:
                        registration_data = json.load(f)
                    if str(user_id) not in registration_data:
                        await interaction.response.send_message("❌ You must register your nation ID first using `/nation register <nation_id>`.")
                        interaction_responded = True
                        return
                    nation_id = registration_data[str(user_id)]['nation_id']
                except (FileNotFoundError, KeyError, json.JSONDecodeError):
                    await interaction.response.send_message("❌ You must register your nation ID first using `/nation register <nation_id>`.")
                    interaction_responded = True
                    return
            
            # Get user's nation data from cache
            from bot.nation_cache import get_nation_cache
            nation_cache = get_nation_cache()
            
            if not nation_cache.is_cache_valid():
                await interaction.response.send_message("⚠️ Nation cache is outdated. Please run `/force_update` to refresh the cache.")
                interaction_responded = True
                return
            
            user_nation_data = nation_cache.get_nation_data(nation_id)
            if not user_nation_data:
                await interaction.response.send_message(f"❌ Nation with ID {nation_id} not found in cache.")
                interaction_responded = True
                return
            
            # Calculate war range (75% to 133% of user's score)
            user_score = float(user_nation_data.get('score', 0))
            min_score = user_score * 0.75
            max_score = user_score * 1.33
            
            # Send initial response
            if not interaction_responded:
                await interaction.response.send_message("🔍 Searching for raid targets using cached data... This should be fast!")
                interaction_responded = True
                progress_message = await interaction.original_response()
            
            # Get nations in score range from cache
            valid_nations = nation_cache.get_nations_in_score_range(min_score, max_score)
            
            info(f"Found {len(valid_nations)} nations in score range {min_score:.0f}-{max_score:.0f}", tag="RAID")
            
            # Filter and calculate loot for each nation
            valid_targets = []
            filtered_out = {
                'vmode': 0,
                'beige_turns': 0,
                'top_alliance': 0,
                'defensive_wars': 0,
                'low_loot': 0
            }
            
            # Get top 60 alliances for filtering
            from bot.csv_cache import get_cache
            csv_cache = get_cache()
            top_60_alliances = csv_cache.get_top_60_alliances()
            
            for nation in valid_nations:
                # Filter out nations in vmode
                if nation.get('vmode', 0) == 1:
                    filtered_out['vmode'] += 1
                    continue
                
                # Filter out nations with beige turns
                if nation.get('beige_turns', 0) > 0:
                    filtered_out['beige_turns'] += 1
                    continue
                
                # Filter out nations in top 60 alliances or your alliance
                alliance = nation.get('alliance', {})
                alliance_id = alliance.get('id') if isinstance(alliance, dict) else None
                if alliance_id == 13033 or alliance_id in top_60_alliances:
                    filtered_out['top_alliance'] += 1
                    continue
                
                # Filter out nations with 3+ defensive wars
                defensive_wars = nation.get('defensive_wars', 0)
                if defensive_wars >= 3:
                    filtered_out['defensive_wars'] += 1
                    continue
                
                # Get cities for this nation
                cities = nation.get('cities', [])
                if not cities:
                    continue
                
                # Calculate comprehensive loot potential
                loot_analysis = self.calculate_comprehensive_loot_potential(nation, cities)
                
                # Use lower threshold since we're using cached data
                if loot_analysis['total'] > 5000:  # $5k threshold for cached data
                    # Calculate military strength
                    military_strength = (
                        nation.get('soldiers', 0) * 0.5 +
                        nation.get('tanks', 0) * 5 +
                        nation.get('aircraft', 0) * 10 +
                        nation.get('ships', 0) * 20
                    )
                    
                    # Calculate total infrastructure
                    total_infra = sum(city.get('infrastructure', 0) for city in cities)
                    
                    # Calculate commerce percentage
                    commerce_percentage = 0
                    for city in cities:
                        city_commerce = 1.0
                        city_commerce += city.get('supermarkets', 0) * self.commerce_bonuses['supermarkets']
                        city_commerce += city.get('banks', 0) * self.commerce_bonuses['banks']
                        city_commerce += city.get('shopping_malls', 0) * self.commerce_bonuses['shopping_malls']
                        city_commerce += city.get('stadiums', 0) * self.commerce_bonuses['stadiums']
                        city_commerce += city.get('subways', 0) * self.commerce_bonuses['subways']
                        commerce_percentage += city_commerce
                    commerce_percentage = (commerce_percentage / len(cities)) * 100 if cities else 0
                    
                    # Calculate daily income
                    daily_income = sum(city.get('infrastructure', 0) * 100 * (1 + city.get('supermarkets', 0) * 0.03 + 
                                                                               city.get('banks', 0) * 0.05 + 
                                                                               city.get('shopping_malls', 0) * 0.09 + 
                                                                               city.get('stadiums', 0) * 0.12 + 
                                                                               city.get('subways', 0) * 0.08) for city in cities)
                    
                    valid_targets.append({
                        'nation': nation,
                        'score': nation.get('score', 0),
                        'military': military_strength,
                        'profit': loot_analysis['total'],
                        'cities': len(cities),
                        'alliance_id': alliance_id,
                        'alliance_rank': alliance.get('rank', 999) if isinstance(alliance, dict) else 999,
                        'beige_turns': nation.get('beige_turns', 0),
                        'wars': defensive_wars,
                        'infrastructure': total_infra,
                        'commerce': commerce_percentage,
                        'income': daily_income,
                        'loot_breakdown': loot_analysis
                    })
                else:
                    filtered_out['low_loot'] += 1
            
            # Sort by profit
            valid_targets.sort(key=lambda x: x['profit'], reverse=True)
            
            # Update progress message
            embed = discord.Embed(
                title="✅ Search Complete",
                description=f"Found {len(valid_targets)} valid targets from {len(valid_nations)} nations in range",
                color=discord.Color.green()
            )
            await progress_message.edit(embed=embed)
            
            # Log filtering results
            info(f"Cached raid filtering results: {len(valid_nations)} nations in range", tag="RAID")
            info(f"  - Vmode: {filtered_out['vmode']} filtered", tag="RAID")
            info(f"  - Beige turns: {filtered_out['beige_turns']} filtered", tag="RAID")
            info(f"  - Top 60 alliances: {filtered_out['top_alliance']} filtered", tag="RAID")
            info(f"  - 3+ defensive wars: {filtered_out['defensive_wars']} filtered", tag="RAID")
            info(f"  - Low loot (<$5k): {filtered_out['low_loot']} filtered", tag="RAID")
            info(f"  - Valid targets found: {len(valid_targets)}", tag="RAID")
            
            if not valid_targets:
                msg = (
                    f"**No profitable raid targets found in war range.**\n\n"
                    f"**Search Results:**\n"
                    f"• Nations in range: {len(valid_nations)}\n"
                    f"• Score range: {min_score:.0f} - {max_score:.0f}\n"
                    f"• Filtered out:\n"
                    f"  - Vmode: {filtered_out['vmode']}\n"
                    f"  - Beige turns: {filtered_out['beige_turns']}\n"
                    f"  - Top 60 alliances: {filtered_out['top_alliance']}\n"
                    f"  - 3+ defensive wars: {filtered_out['defensive_wars']}\n"
                    f"  - Low loot potential: {filtered_out['low_loot']}\n\n"
                    f"Try adjusting your search criteria or check back later!"
                )
                embed = discord.Embed(
                    title="❌ No Raid Targets Found",
                    description=msg,
                    color=discord.Color.red()
                )
                await progress_message.edit(embed=embed)
                return
            
            # Display results with enhanced pagination
            formatted_targets = []
            for target in valid_targets[:50]:  # Limit to top 50
                nation = target.get('nation', {})
                if not nation:
                    continue
                    
                formatted_targets.append({
                    'nation': {
                        'name': nation.get('nation_name', 'Unknown'),
                        'leader': nation.get('leader_name', 'Unknown'),
                        'id': nation.get('id', target.get('nation_id', 'Unknown'))
                    },
                    'score': target.get('score', 0),
                    'cities': target.get('cities', 0),
                    'income': target.get('income', 0),
                    'commerce': target.get('commerce', 0),
                    'profit': target.get('profit', 0),
                    'military': target.get('military', 0),
                    'alliance': nation.get('alliance', {}).get('name', 'None') if isinstance(nation.get('alliance'), dict) else 'None',
                    'alliance_rank': target.get('alliance_rank', 999),
                    'beige_turns': target.get('beige_turns', 0),
                    'wars': target.get('wars', 0),
                    'loot_breakdown': target.get('loot_breakdown', {})
                })
            
            paginator = RaidPaginator(formatted_targets, per_page=5)
            view = RaidView(paginator, interaction)
            
            embed = paginator.get_page(0)
            await progress_message.edit(embed=embed, view=view)
            
            info(f"Cached raid command completed by {interaction.user} - Found {len(valid_targets)} targets", tag="RAID")
            
        except Exception as e:
            error(f"Error in cached raid logic: {e}", tag="RAID")
            if interaction:
                if interaction_responded:
                    await interaction.followup.send(f"❌ Error finding raid targets: {str(e)}")
                else:
                    await interaction.response.send_message(f"❌ Error finding raid targets: {str(e)}")