from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional, List, Dict, Tuple

from bot.services.nation_service import NationService
from bot.config.settings import config
from bot.services.cache_service import CacheService

logger = logging.getLogger('raiden_shogun')


def infra_unit_cost(current_infra: float) -> float:
    """Infra unit cost per references.md: [((Current Infra - 10)^2.2)/710] + 300 for infra > 10; else 1000 per unit up to 10.
    Returns cost to buy ONE infra at the current level.
    """
    if current_infra < 10:
        return 1000.0
    return ((current_infra - 10.0) ** 2.2) / 710.0 + 300.0


def cost_to_reach_infra(start: float, target: float) -> float:
    """Numerically integrate marginal cost from start to target infra (in 1.0 increments)."""
    if target <= start:
        return 0.0
    cost = 0.0
    level = start
    while level < target:
        cost += infra_unit_cost(level)
        level += 1.0
    return cost


def next_city_cost(current_city_count: int) -> float:
    """Cubic next city cost per user-provided formula:

    Next City Cost = 50000*(X-1)^3 + 150000*X + 75000
    Where X is the current number of cities (1-indexed count for the new city position).

    Here, current_city_count is the nation's existing number of cities. The next city's
    X should be current_city_count + 1.
    """
    x = float(current_city_count + 1)
    return 50000.0 * ((x - 1.0) ** 3) + 150000.0 * x + 75000.0


class ProjectsCog(commands.Cog):
    """Nation projects planning commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nation_service = NationService()
        self.cache_service = CacheService()

    def _normalize_cities(self, nation: object) -> List[Dict]:
        """Return cities as list of dicts with keys: id, infrastructure.
        Supports both dict cities and City objects.
        """
        out: List[Dict] = []
        cities = getattr(nation, 'cities_data', None)
        if isinstance(cities, list) and cities:
            for city in cities:
                try:
                    if isinstance(city, dict):
                        out.append({
                            'id': int(city.get('id', 0) or 0),
                            'infrastructure': float(city.get('infrastructure', 0) or 0)
                        })
                    else:
                        cid = int(getattr(city, 'id', 0) or 0)
                        infra = float(getattr(city, 'infrastructure', 0) or 0)
                        out.append({'id': cid, 'infrastructure': infra})
                except Exception:
                    continue
        return out

    async def _get_target_infra_needed(self, nation: object) -> Tuple[int, int]:
        """Compute (current_total_infra, target_total_infra) to reach next 5,000 infra slot."""
        # Nation should expose total infrastructure across cities; fall back to summing city infra
        total_infra = 0
        cities = self._normalize_cities(nation)
        if cities:
            for city in cities:
                total_infra += city['infrastructure']
        else:
            total_infra = int(getattr(nation, 'infrastructure', 0) or 0)

        # Next multiple of 5000 above current
        current_slot_floor = (int(total_infra) // 5000) * 5000
        target_total = current_slot_floor + 5000
        if target_total <= total_infra:
            target_total += 5000
        return int(total_infra), int(target_total)

    def _plan_greedy_with_new_cities(self, cities: List[Dict], delta_needed: int, add_new_cities: int, current_city_count: int) -> Tuple[float, List[Tuple[str, int, float]], float]:
        """Greedy planner across existing cities plus a number of new blank cities.

        Returns (total_cost, plan_entries, fixed_city_cost)
        - total_cost includes infra marginal costs + fixed new city costs
        - plan_entries: list of (label, infra_added, infra_cost)
        - fixed_city_cost: sum of base costs of created cities
        """
        # Prepare working set: existing cities
        work_labels: List[str] = []
        work_infra: List[float] = []
        start_infra_map: List[float] = []
        city_ids: List[Optional[int]] = []
        for idx, city in enumerate(cities):
            cur = float(city.get('infrastructure', 0) or 0)
            work_infra.append(cur)
            start_infra_map.append(cur)
            city_ids.append(int(city.get('id', idx)))
            work_labels.append(f"City {int(city.get('id', idx))}")

        # Add virtual new cities with 0 infra
        fixed_city_cost = 0.0
        for i in range(add_new_cities):
            # Next city cost depends on progressive index
            fixed_city_cost += next_city_cost(current_city_count + i)
            work_infra.append(0.0)
            start_infra_map.append(0.0)
            city_ids.append(None)
            work_labels.append(f"New City #{i+1}")

        added = [0 for _ in work_infra]
        infra_cost_total = 0.0

        for _ in range(delta_needed):
            best_i = 0
            best_cost = float('inf')
            for i, cur in enumerate(work_infra):
                c = infra_unit_cost(cur)
                if c < best_cost:
                    best_cost = c
                    best_i = i
            work_infra[best_i] = work_infra[best_i] + 1.0
            added[best_i] += 1
            infra_cost_total += best_cost

        plan: List[Tuple[str, int, float]] = []
        for i, inc in enumerate(added):
            if inc > 0:
                start = start_infra_map[i]
                plan.append((work_labels[i], inc, cost_to_reach_infra(start, start + inc)))

        total_cost = infra_cost_total + fixed_city_cost
        return total_cost, plan, fixed_city_cost

    async def _evaluate_new_city_option(self, nation: object, delta_needed: int) -> Optional[Tuple[float, Dict]]:
        """Evaluate creating a new city and building infra there up to delta_needed.
        If new city cost formula is unavailable, return None to skip this option.
        """
        # We don't have a reliable new city base cost formula in codebase/references.
        # Skip unless config provides an override.
        base_new_city_cost = getattr(config, 'NEW_CITY_BASE_COST', None)
        if base_new_city_cost is None:
            return None
        # Assume new city starts at 0 infra; often cities start with some infra, but absent exact rule we use 0.
        infra_cost = cost_to_reach_infra(0.0, float(delta_needed))
        total = float(base_new_city_cost) + infra_cost
        return total, {"city_id": None, "infra_added": delta_needed, "cost": total}

    

    async def project_infra(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        await interaction.response.defer()
        try:
            if nation_id is None:
                user_nid = self.cache_service.get_user_nation(str(interaction.user.id))
                if not user_nid:
                    await interaction.followup.send("❌ You need to register first. Use /register.", ephemeral=True)
                    return
                nation_id = int(user_nid)

            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                await interaction.followup.send("❌ Could not fetch nation.", ephemeral=True)
                return

            # Compute infra needed based on desired next slot = current projects + 1,
            # accounting for RnD (+2 slots) and wars (>=100 gives +1).
            # Slots formula: 1 + floor(infra/5000) + rnd_bonus + wars_bonus
            # Find minimal infra so that slots >= projects_built + 1
            cities_norm = self._normalize_cities(nation)
            total_infra = sum(c['infrastructure'] for c in cities_norm)
            projects_built = getattr(nation, 'projects', 0) or 0
            # Check for RnD using project_bits
            project_bits = getattr(nation, 'project_bits', 0) or 0
            project_bits = int(project_bits) if project_bits else 0
            has_rnd = False
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
                    if ch == '1' and i < len(project_order) and project_order[i] == 'research_and_development_center':
                        has_rnd = True
                        break
            rnd_bonus = 2 if has_rnd else 0
            
            # Check for Military Research Center project (also gives +2 slots)
            has_military_research = False
            military_research = getattr(nation, 'military_research', {})
            if isinstance(military_research, dict):
                # Check if any of the military research capacities are > 0
                has_military_research = any(
                    military_research.get(key, 0) > 0 
                    for key in ['ground_capacity', 'air_capacity', 'naval_capacity']
                )
            military_research_bonus = 2 if has_military_research else 0
            
            # Wars achievement bonus: +1 slot at 100 total wars (won + lost)
            wars_total = int(getattr(nation, 'wars_won', 0) or 0) + int(getattr(nation, 'wars_lost', 0) or 0)
            wars_bonus = 1 if wars_total >= 100 else 0
            
            # Calculate current and target slots
            # Formula: max(1, 1 + floor(infra/4000)) + RnD bonus + Military Research bonus + Wars bonus
            current_slots = max(1, 1 + int(total_infra // 4000)) + rnd_bonus + military_research_bonus + wars_bonus
            desired_slots = projects_built + 1
            needed_floor = max(0, desired_slots - 1 - rnd_bonus - military_research_bonus - wars_bonus)
            target_total = needed_floor * 4000
            target_slots = max(1, 1 + int(target_total // 4000)) + rnd_bonus + military_research_bonus + wars_bonus
            delta_needed = max(0, target_total - int(total_infra))
            if delta_needed == 0:
                await interaction.followup.send("✅ You already have enough infrastructure for the next project slot.")
                return

            cities: List[Dict] = cities_norm
            current_city_count = len(cities)

            # Evaluate options: add 0..3 new cities (progressive costs) + greedy infra
            best_total = float('inf')
            best_plan: List[Tuple[str, int, float]] = []
            best_k = 0
            best_fixed = 0.0
            for k in range(0, 4):
                total_k, plan_k, fixed_k = self._plan_greedy_with_new_cities(cities, delta_needed, k, current_city_count)
                if total_k < best_total:
                    best_total = total_k
                    best_plan = plan_k
                    best_k = k
                    best_fixed = fixed_k

            total_cost = best_total
            option = "Existing Cities" if best_k == 0 else (f"Add {best_k} New City(ies) + Infra")

            # Summarize plan entries
            details_lines = []
            # Show up to 10 lines
            for label, infra_add, cost in sorted(best_plan, key=lambda x: -x[1])[:10]:
                details_lines.append(f"- {label}: +{infra_add:,} infra (cost ${cost:,.0f})")
            if len(best_plan) > 10:
                details_lines.append(f"... and {len(best_plan)-10} more entries")

            embed = discord.Embed(
                title=f"Project Slot Infra Planner - {current_slots} Slots -> {target_slots} Slots",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Nation", value=f"ID {nation_id} - {getattr(nation, 'name', 'Unknown')}", inline=False)
            embed.add_field(name="Current Total Infra", value=f"{int(total_infra):,}", inline=True)
            embed.add_field(name="Target Total Infra", value=f"{target_total:,}", inline=True)
            embed.add_field(name="Infra Needed", value=f"{delta_needed:,}", inline=True)
            embed.add_field(name="Cheapest Option", value=option, inline=False)
            if best_k > 0:
                embed.add_field(name="New City Fixed Cost", value=f"${best_fixed:,.0f}", inline=True)
            embed.add_field(name="Estimated Total Cost", value=f"${total_cost:,.0f}", inline=False)
            if details_lines:
                embed.add_field(name="Plan Details", value="\n".join(details_lines), inline=False)


            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in /project infra: {e}")
            await interaction.followup.send("❌ Error computing infra plan.", ephemeral=True)

    # === Slash Commands: /project slot and /project next ===
    project_group = app_commands.Group(name="project", description="Project planning tools")

    @project_group.command(name="slot", description="Find cheapest way to reach next project slot (4k total infra)")
    @app_commands.describe(nation_id="Optional nation ID (defaults to your registration)")
    async def project_slot(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        await self.project_infra(interaction, nation_id)

    @project_group.command(name="next", description="Show the next recommended project to build and timer/slots")
    @app_commands.describe(nation_id="Optional nation ID (defaults to your registration)")
    async def project_next(self, interaction: discord.Interaction, nation_id: Optional[int] = None):
        await interaction.response.defer()
        try:
            if nation_id is None:
                user_nid = self.cache_service.get_user_nation(str(interaction.user.id))
                if not user_nid:
                    await interaction.followup.send("❌ You need to register first. Use /register.", ephemeral=True)
                    return
                nation_id = int(user_nid)

            nation = await self.nation_service.get_nation(nation_id, "everything_scope")
            if not nation:
                await interaction.followup.send("❌ Could not fetch nation.", ephemeral=True)
                return

            # Determine owned projects using project_bits if available, else booleans
            project_bits = getattr(nation, 'project_bits', 0) or 0
            project_bits = int(project_bits) if project_bits else 0
            owned = set()
            
            if project_bits:
                # Convert to binary and reverse for right-to-left reading
                bits = bin(project_bits)[2:][::-1]
                # Project bits are read right-to-left in API_REFERENCES order; map names to index
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
                        owned.add(project_order[i])

            def has(name: str, fallback_attr: str) -> bool:
                if name in owned:
                    return True
                return bool(getattr(nation, fallback_attr, False))

            has_activity = has('activity_center', 'activity_center')
            has_pb = has('propaganda_bureau', 'propaganda_bureau')
            has_ia = has('central_intelligence_agency', 'central_intelligence_agency')
            has_rnd = has('research_and_development_center', 'research_and_development_center')
            has_pe = has('pirate_economy', 'pirate_economy')
            has_ape = has('advanced_pirate_economy', 'advanced_pirate_economy')

            order = [
                ("Activity Center", has_activity),
                ("Propaganda Bureau", has_pb),
                ("Intelligence Agency", has_ia),
                ("Research and Development Center", has_rnd),
                ("Pirate Economy", has_pe),
                ("Advanced Pirate Economy", has_ape),
            ]

            next_project = None
            for name, owned in order:
                if not owned:
                    next_project = name
                    break

            # Slots and timer using API fields
            projects_built = getattr(nation, 'projects', 0) or 0
            current_infra, _ = await self._get_target_infra_needed(nation)
            # Formula: max(1, 1 + floor(infra/4000)) + RnD bonus + Wars bonus
            base_slots = max(1, 1 + int(current_infra // 4000))
            if has_rnd:
                base_slots += 2
            
            # Check for Military Research Center project (also gives +2 slots)
            has_military_research = False
            military_research = getattr(nation, 'military_research', {})
            if isinstance(military_research, dict):
                # Check if any of the military research capacities are > 0
                has_military_research = any(
                    military_research.get(key, 0) > 0 
                    for key in ['ground_capacity', 'air_capacity', 'naval_capacity']
                )
            if has_military_research:
                base_slots += 2
                
            wars_total = int(getattr(nation, 'wars_won', 0) or 0) + int(getattr(nation, 'wars_lost', 0) or 0)
            if wars_total >= 100:
                base_slots += 1
            project_slots = base_slots
            # Use turns_since_last_project to compute remaining days (max 120 turn cooldown)
            turns_since = getattr(nation, 'turns_since_last_project', None)
            timer_turns = None
            if isinstance(turns_since, int):
                remaining_turns = max(0, 120 - turns_since)
                timer_turns = remaining_turns

            timer_text = "Unknown"
            if isinstance(timer_turns, (int, float)):
                # 12 turns per day
                days = max(0.0, float(timer_turns)) / 12.0
                timer_text = f"{days:.1f} days"

            slots_text = "Unknown"
            if isinstance(project_slots, int) and isinstance(projects_built, int):
                free = max(0, project_slots - projects_built)
                slots_text = f"{free} free (built {projects_built}, slots {project_slots})"

            desc_lines = []
            if next_project:
                desc_lines.append(f"**Next Project:** {next_project}")
            else:
                desc_lines.append("**Next Project:** All recommended projects acquired")
            desc_lines.append(f"**Project Timer:** {timer_text}")
            desc_lines.append(f"**Slots:** {slots_text}")

            embed = discord.Embed(title=f"Next Project Recommendation - Nation {nation_id}", color=discord.Color.teal(), description="\n".join(desc_lines))
            if timer_turns is None:
                embed.set_footer(text="Project timer not available via public API")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in /project next: {e}")
            await interaction.followup.send("❌ Error fetching next project info.", ephemeral=True)

async def setup(bot):
    cog = ProjectsCog(bot)
    await bot.add_cog(cog)
    # Register group commands once
    try:
        existing = bot.tree.get_command('project')
        if existing is None:
            bot.tree.add_command(cog.project_group)
    except Exception as e:
        logger.warning(f"/project group registration skipped: {e}")
