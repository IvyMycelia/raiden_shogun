from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional, Dict, Any
import json

from bot.services.nation_service import NationService
from bot.services.cache_service import CacheService
from bot.config.settings import config

logger = logging.getLogger('raiden_shogun')


class BuildCog(commands.Cog):
    """Nation build optimization commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nation_service = NationService()
        self.cache_service = CacheService()

    def _get_first_city_data(self, nation: object) -> tuple[int, int]:
        """Get infrastructure and land from the first city."""
        cities_data = getattr(nation, 'cities_data', [])
        if not cities_data:
            return 0, 0
        
        first_city = cities_data[0]
        if hasattr(first_city, 'infrastructure'):
            infra = int(getattr(first_city, 'infrastructure', 0) or 0)
        else:
            infra = int(first_city.get('infrastructure', 0) or 0)
            
        if hasattr(first_city, 'land'):
            land = int(getattr(first_city, 'land', 0) or 0)
        else:
            land = int(first_city.get('land', 0) or 0)
            
        return infra, land

    def _calculate_optimal_build(self, infra: int, land: int, mmr_type: str, 
                               continent: str, projects: set, 
                               barracks: int = 5, factories: int = 5, 
                               hangars: int = 5, drydocks: int = 3) -> Dict[str, Any]:
        """Calculate the most optimal self-sufficient build for a city using references.md formulas."""
        
        # Base infrastructure needed calculation
        infra_needed = max(infra, 1000)  # Minimum 1000 infra
        
        # Calculate total improvements based on infrastructure (Improvements = Infra/50)
        imp_total = int(infra_needed // 50)
        
        # Initialize all improvements to 0
        build = {
            "infra_needed": infra_needed,
            "imp_total": imp_total,
            "imp_coalpower": 0,
            "imp_oilpower": 0,
            "imp_windpower": 0,
            "imp_nuclearpower": 0,
            "imp_coalmine": 0,
            "imp_oilwell": 0,
            "imp_uramine": 0,
            "imp_leadmine": 0,
            "imp_ironmine": 0,
            "imp_bauxitemine": 0,
            "imp_farm": 0,
            "imp_gasrefinery": 0,
            "imp_aluminumrefinery": 0,
            "imp_munitionsfactory": 0,
            "imp_steelmill": 0,
            "imp_policestation": 0,
            "imp_hospital": 0,
            "imp_recyclingcenter": 0,
            "imp_subway": 0,
            "imp_supermarket": 0,
            "imp_bank": 0,
            "imp_mall": 0,
            "imp_stadium": 0,
            "imp_barracks": 0,
            "imp_factory": 0,
            "imp_hangars": 0,
            "imp_drydock": 0
        }
        
        # STEP 1: POWER CALCULATION
        # Power needed = 1 per 50 infrastructure
        power_needed = infra_needed // 50
        
        # Choose optimal power source based on infrastructure
        # Nuclear is more efficient for high infra (saves improvement slots)
        if infra_needed >= 1000:
            # Nuclear power: 1 plant powers up to 2000 infra, uses 2.4 uranium per 1000 infra
            nuclear_plants_needed = (infra_needed + 1999) // 2000  # Ceiling division
            build["imp_nuclearpower"] = min(nuclear_plants_needed, 5)
        else:
            # Wind power for low infra
            wind_plants_needed = (infra_needed + 249) // 250
            build["imp_windpower"] = min(wind_plants_needed, 5)
        
        # STEP 2: MMR MILITARY IMPROVEMENTS
        if mmr_type == "raiding":
            # Raider MMR: 5050 (5 barracks, 0 factories, 5 hangars, 0 drydocks)
            build["imp_barracks"] = min(barracks, 5)
            build["imp_factory"] = 0
            build["imp_hangars"] = min(hangars, 5)
            build["imp_drydock"] = 0
        elif mmr_type == "whale":
            # Whale MMR: 0250 (0 barracks, 2 factories, 5 hangars, 0 drydocks)
            build["imp_barracks"] = 0
            build["imp_factory"] = min(factories, 5)
            build["imp_hangars"] = min(hangars, 5)
            build["imp_drydock"] = 0
        else:
            # Custom MMR
            build["imp_barracks"] = min(barracks, 5)
            build["imp_factory"] = min(factories, 5)
            build["imp_hangars"] = min(hangars, 5)
            build["imp_drydock"] = min(drydocks, 3)
        
        # STEP 3: MINIMAL RESOURCE PRODUCTION (Only power needs)
        # Only produce resources for power, not for military (commerce priority)
        
        # Power resource needs only
        if build["imp_nuclearpower"] > 0:
            # Nuclear: 2.4 uranium per 1000 infra per plant per day
            # Convert to per turn: 2.4 / 12 = 0.2 per turn per 1000 infra
            uranium_needed_per_turn = build["imp_nuclearpower"] * (infra_needed / 1000) * 0.2
            # Each uranium mine produces 0.25/turn
            uranium_mines_needed = int(uranium_needed_per_turn / 0.25) + 1  # Ceiling division
            build["imp_uramine"] = min(uranium_mines_needed, 5)
        
        # NO military resource production - prioritize commerce instead
        # Military units can be bought with money, commerce generates money
        
        # STEP 4: NO MANUFACTURING IMPROVEMENTS
        # Skip manufacturing - prioritize commerce for income
        # Military units can be purchased with money from commerce
        
        # STEP 5: FOOD PRODUCTION (Ultra-Minimal)
        # Ultra-minimal food production to save slots for commerce
        # Just 1 farm - food can be bought with commerce income
        build["imp_farm"] = 1
        
        # STEP 6: CIVIL IMPROVEMENTS (Adequate Crime and Disease Control)
        # Adequate civil improvements to keep crime/disease under 1%
        
        # Crime control: 1 police station (adequate for most cases)
        build["imp_policestation"] = 1
        
        # Disease control: Use practical hospital count based on land
        # Higher land = lower density = fewer hospitals needed
        # Lower land = higher density = more hospitals needed
        if land >= 1000:
            # High land: 2 hospitals sufficient
            build["imp_hospital"] = 2
        elif land >= 500:
            # Medium land: 3 hospitals needed
            build["imp_hospital"] = 3
        else:
            # Low land: 4 hospitals needed
            build["imp_hospital"] = 4
        
        # Pollution control: 1 recycling center (adequate for minimal pollution)
        build["imp_recyclingcenter"] = 1
        
        # Subway: +8% commerce, -45 pollution
        build["imp_subway"] = 1  # Always build 1 subway
        
        # STEP 7: COMMERCE IMPROVEMENTS (Income Optimization - PRIORITY)
        # Calculate remaining improvement slots
        used_improvements = (
            build["imp_nuclearpower"] + build["imp_windpower"] +
            build["imp_uramine"] + build["imp_ironmine"] + build["imp_bauxitemine"] +
            build["imp_leadmine"] + build["imp_coalmine"] + build["imp_oilwell"] +
            build["imp_farm"] + build["imp_steelmill"] + build["imp_aluminumrefinery"] +
            build["imp_munitionsfactory"] + build["imp_gasrefinery"] +
            build["imp_policestation"] + build["imp_hospital"] + build["imp_recyclingcenter"] +
            build["imp_subway"] + build["imp_barracks"] + build["imp_factory"] +
            build["imp_hangars"] + build["imp_drydock"]
        )
        
        remaining_slots = max(0, imp_total - used_improvements)
        
        # PRIORITIZE COMMERCE OVER RESOURCE PRODUCTION
        # Allocate commerce improvements first (highest income impact)
        # Both raider and whale should maximize commerce for income
        
        # Maximum commerce allocation (matching your optimal build)
        # Allocate in order of commerce efficiency: banks, malls, stadiums, supermarkets
        build["imp_bank"] = min(remaining_slots, 5)
        remaining_slots -= build["imp_bank"]
        
        build["imp_mall"] = min(remaining_slots, 4)
        remaining_slots -= build["imp_mall"]
        
        build["imp_stadium"] = min(remaining_slots, 3)
        remaining_slots -= build["imp_stadium"]
        
        build["imp_supermarket"] = min(remaining_slots, 4)
        
        # STEP 8: OPTIMIZE RESOURCE PRODUCTION (Only if slots remain)
        # Check if we have remaining slots after commerce allocation
        final_used_improvements = (
            build["imp_nuclearpower"] + build["imp_windpower"] +
            build["imp_uramine"] + build["imp_ironmine"] + build["imp_bauxitemine"] +
            build["imp_leadmine"] + build["imp_coalmine"] + build["imp_oilwell"] +
            build["imp_farm"] + build["imp_steelmill"] + build["imp_aluminumrefinery"] +
            build["imp_munitionsfactory"] + build["imp_gasrefinery"] +
            build["imp_policestation"] + build["imp_hospital"] + build["imp_recyclingcenter"] +
            build["imp_subway"] + build["imp_barracks"] + build["imp_factory"] +
            build["imp_hangars"] + build["imp_drydock"] + build["imp_bank"] + 
            build["imp_mall"] + build["imp_stadium"] + build["imp_supermarket"]
        )
        
        final_remaining_slots = max(0, imp_total - final_used_improvements)
        
        # Only add extra resource production if we have slots left
        if final_remaining_slots > 0:
            # Add extra resource production for income
            if final_remaining_slots >= 1:
                build["imp_bauxitemine"] = min(build["imp_bauxitemine"] + 1, 10)
                final_remaining_slots -= 1
            
            if final_remaining_slots >= 1:
                build["imp_oilwell"] = min(build["imp_oilwell"] + 1, 10)
                final_remaining_slots -= 1
        
        # Project bonuses
        if "international_trade_center" in projects:
            build["imp_bank"] = min(build["imp_bank"] + 1, 6)  # Max 6 with ITC
            build["imp_mall"] = min(build["imp_mall"] + 1, 5)
        
        if "telecommunications_satellite" in projects:
            build["imp_mall"] = min(build["imp_mall"] + 1, 5)  # Max 5 with Telecom
        
        if "clinical_research_center" in projects:
            build["imp_hospital"] = min(build["imp_hospital"] + 1, 6)  # Max 6 with CRC
        
        if "recycling_initiative" in projects:
            build["imp_recyclingcenter"] = min(build["imp_recyclingcenter"] + 1, 4)  # Max 4 with RI
        
        # Continent bonuses
        if continent == "North America":
            build["imp_bank"] = min(build["imp_bank"] + 1, 5)
        elif continent == "Europe":
            build["imp_mall"] = min(build["imp_mall"] + 1, 5)
        elif continent == "Asia":
            build["imp_factory"] = min(build["imp_factory"] + 1, 5)
        elif continent == "Africa":
            build["imp_uramine"] = min(build["imp_uramine"] + 1, 5)
        elif continent == "South America":
            build["imp_farm"] = min(build["imp_farm"] + 1, 20)
        elif continent == "Australia":
            build["imp_ironmine"] = min(build["imp_ironmine"] + 1, 10)
        
        return build

    def _get_nation_projects(self, nation: object) -> set:
        """Get the nation's projects as a set."""
        projects = set()
        
        # Check project_bits
        project_bits = getattr(nation, 'project_bits', 0) or 0
        project_bits = int(project_bits) if project_bits else 0
        
        if project_bits:
            bits = bin(project_bits)[2:][::-1]
            project_order = [
                'iron_works','bauxite_works','arms_stockpile','emergency_gasoline_reserve','mass_irrigation',
                'international_trade_center','missile_launch_pad','nuclear_research_facility','iron_dome',
                'vital_defense_system','central_intelligence_agency','center_for_civil_engineering',
                'propaganda_bureau','uranium_enrichment_program','urban_planning','advanced_urban_planning',
                'space_program','spy_satellite','moon_landing','pirate_economy','recycling_initiative',
                'telecommunications_satellite','green_technologies','arable_land_agency','clinical_research_center',
                'specialized_police_training_program','advanced_engineering_corps','government_support_agency',
                'research_and_development_center','activity_center','metropolitan_planning','military_salvage',
                'fallout_shelter','bureau_of_domestic_affairs','advanced_pirate_economy','mars_landing',
                'surveillance_network','guiding_satellite','nuclear_launch_facility'
            ]
            for i, ch in enumerate(bits):
                if ch == '1' and i < len(project_order):
                    projects.add(project_order[i])
        
        # Check boolean project fields
        boolean_projects = [
            'mass_irrigation', 'international_trade_center', 'center_for_civil_engineering',
            'iron_works', 'bauxite_works', 'arms_stockpile', 'emergency_gasoline_reserve',
            'nuclear_research_facility', 'uranium_enrichment_program', 'urban_planning',
            'advanced_urban_planning', 'space_program', 'spy_satellite', 'moon_landing',
            'pirate_economy', 'recycling_initiative', 'telecommunications_satellite',
            'green_technologies', 'arable_land_agency', 'clinical_research_center',
            'specialized_police_training_program', 'advanced_engineering_corps',
            'government_support_agency', 'research_and_development_center', 'activity_center',
            'metropolitan_planning', 'military_salvage', 'fallout_shelter',
            'bureau_of_domestic_affairs', 'advanced_pirate_economy', 'mars_landing',
            'surveillance_network', 'guiding_satellite', 'nuclear_launch_facility'
        ]
        
        for project in boolean_projects:
            if getattr(nation, project, False):
                projects.add(project)
        
        return projects

    @app_commands.command(name="build", description="Generate optimal city build based on your nation's data")
    @app_commands.describe(
        continent="Your continent (optional, auto-detected if not provided)",
        land="Land count (optional, uses first city if not provided)",
        infra="Infrastructure (optional, uses first city if not provided)",
        barracks="Number of barracks (max 5, default 5)",
        factories="Number of factories (max 5, default 5)",
        hangars="Number of hangars (max 5, default 5)",
        drydocks="Number of drydocks (max 3, default 3)"
    )
    @app_commands.choices(continent=[
        app_commands.Choice(name="North America", value="North America"),
        app_commands.Choice(name="Europe", value="Europe"),
        app_commands.Choice(name="Asia", value="Asia"),
        app_commands.Choice(name="Africa", value="Africa"),
        app_commands.Choice(name="South America", value="South America"),
        app_commands.Choice(name="Australia", value="Australia")
    ])
    async def build_command(self, interaction: discord.Interaction, 
                           continent: Optional[str] = None,
                           land: Optional[int] = None,
                           infra: Optional[int] = None,
                           barracks: int = 5,
                           factories: int = 5,
                           hangars: int = 5,
                           drydocks: int = 3):
        """Generate optimal city build."""
        await interaction.response.defer()
        
        try:
            # Get user's nation
            user_nid = self.cache_service.get_user_nation(str(interaction.user.id))
            if not user_nid:
                await interaction.followup.send("❌ You need to register first. Use /register.", ephemeral=True)
                return
            
            nation_id = int(user_nid)
            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                await interaction.followup.send("❌ Could not fetch nation.", ephemeral=True)
                return
            
            # Get first city data if not provided
            if land is None or infra is None:
                first_city_infra, first_city_land = self._get_first_city_data(nation)
                if land is None:
                    land = first_city_land
                if infra is None:
                    infra = first_city_infra
            
            # Auto-detect continent if not provided
            if continent is None:
                nation_continent = getattr(nation, 'continent', 'North America')
                continent = nation_continent if nation_continent else 'North America'
            
            # Auto-determine MMR type based on city count (C15+ is whale)
            city_count = getattr(nation, 'cities', 0) or 0
            if city_count >= 15:
                mmr_type = "whale"
            else:
                mmr_type = "raiding"
            
            # Get nation's projects
            projects = self._get_nation_projects(nation)
            
            # Validate parameters
            barracks = max(0, min(barracks, 5))
            factories = max(0, min(factories, 5))
            hangars = max(0, min(hangars, 5))
            drydocks = max(0, min(drydocks, 3))
            
            # Calculate optimal build
            build = self._calculate_optimal_build(
                infra=infra,
                land=land,
                mmr_type=mmr_type,
                continent=continent,
                projects=projects,
                barracks=barracks,
                factories=factories,
                hangars=hangars,
                drydocks=drydocks
            )
            
            # Format as JSON
            build_json = json.dumps(build, indent=4)
            
            # Create embed
            embed = discord.Embed(
                title="🏗️ Optimal City Build",
                description=f"**Nation:** {getattr(nation, 'name', 'Unknown')}\n"
                           f"**Cities:** {city_count}\n"
                           f"**MMR Type:** {mmr_type.title()} (auto-detected)\n"
                           f"**Continent:** {continent}\n"
                           f"**Infrastructure:** {infra:,}\n"
                           f"**Land:** {land:,}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Military Improvements",
                value=f"Barracks: {build['imp_barracks']} | Factories: {build['imp_factory']}\n"
                      f"Hangars: {build['imp_hangars']} | Drydocks: {build['imp_drydock']}",
                inline=False
            )
            
            embed.add_field(
                name="Economic Improvements",
                value=f"Banks: {build['imp_bank']} | Malls: {build['imp_mall']}\n"
                      f"Stadiums: {build['imp_stadium']} | Supermarkets: {build['imp_supermarket']}",
                inline=False
            )
            
            embed.add_field(
                name="Resource Production",
                value=f"Uranium Mines: {build['imp_uramine']} | Iron Mines: {build['imp_ironmine']}\n"
                      f"Bauxite Mines: {build['imp_bauxitemine']} | Lead Mines: {build['imp_leadmine']}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            await interaction.followup.send(f"```json\n{build_json}\n```")
            
        except Exception as e:
            logger.error(f"Error in /build command: {e}")
            await interaction.followup.send("❌ Error generating build.", ephemeral=True)


async def setup(bot):
    cog = BuildCog(bot)
    await bot.add_cog(cog)
