from datetime import datetime, timezone
import math

import vars
from handler import debug, info, success, warning, error, fatal

def warchest(nation_info, COSTS, MILITARY_COSTS):
    # Cost constants per turn (calculated from daily cost divided by 12 turns)
    try:
        COSTS = vars.COSTS
        MILITARY_COSTS = vars.MILITARY_COSTS

        # Initialize totals for building upkeep and resource consumption per turn.
        total_building_upkeep = 0
        total_coal_consumption = 0.0      # from coal power plants and steel mills
        total_oil_consumption = 0.0       # from oil power plants and oil refineries
        total_uranium_consumption = 0.0   # from nuclear power plants
        total_steel_mill_iron = 0.0       # iron consumption in steel mills
        total_steel_mill_coal = 0.0       # additional coal consumption in steel mills
        total_aluminum_refinery_bauxite = 0.0  # bauxite consumption in aluminum refineries
        total_munitions_factory_lead = 0.0     # lead consumption in munitions factories
        total_food_consumption = 0.0       # food consumption in cities

        gasoline_preparedness = 0
        munitions_preparedness = 0
        steel_preparedness = 0
        aluminum_preparedness = 0

        # Calculate military resource requirements for 5 days (60 turns)
        soldiers = nation_info.get("soldiers", 0)
        tanks = nation_info.get("tanks", 0)
        aircraft = nation_info.get("aircraft", 0)
        ships = nation_info.get("ships", 0)

        # Calculate military resource usage per turn
        gasoline_per_turn = (soldiers / 5000) + (tanks / 100) + (aircraft / 4) + 2.5  # Base gasoline usage
        munitions_per_turn = (soldiers / 5000) + (tanks / 100) + (aircraft / 4) + 2    # Base munitions usage
        steel_per_turn = (tanks / 100) + (ships / 5)                                   # Base steel usage
        aluminum_per_turn = aircraft / 4                                               # Base aluminum usage

        # Calculate total military resource requirements for 5 days
        required_gasoline = gasoline_per_turn * 60  # 60 turns = 5 days
        required_munitions = munitions_per_turn * 60
        required_steel = steel_per_turn * 60
        required_aluminum = aluminum_per_turn * 60

        for city in nation_info.get("cities", []):
            infra = city.get("infrastructure", 0)
            # Sum building upkeep per turn from all buildings in the city.
            building_upkeep = (
                city.get("coal_power", 0) * COSTS["coal_power"] +
                city.get("oil_power", 0) * COSTS["oil_power"] +
                city.get("nuclear_power", 0) * COSTS["nuclear_power"] +
                city.get("wind_power", 0) * COSTS["wind_power"] +
                city.get("farm", 0) * COSTS["farm"] +
                city.get("uranium_mine", 0) * COSTS["uranium_mine"] +
                city.get("iron_mine", 0) * COSTS["iron_mine"] +
                city.get("coal_mine", 0) * COSTS["coal_mine"] +
                city.get("oil_refinery", 0) * COSTS["oil_refinery"] +
                city.get("steel_mill", 0) * COSTS["steel_mill"] +
                city.get("aluminum_refinery", 0) * COSTS["aluminum_refinery"] +
                city.get("munitions_factory", 0) * COSTS["munitions_factory"] +
                city.get("police_station", 0) * COSTS["police_station"] +
                city.get("hospital", 0) * COSTS["hospital"] +
                city.get("recycling_center", 0) * COSTS["recycling_center"] +
                city.get("subway", 0) * COSTS["subway"] +
                city.get("supermarket", 0) * COSTS["supermarket"] +
                city.get("bank", 0) * COSTS["bank"] +
                city.get("shopping_mall", 0) * COSTS["shopping_mall"] +
                city.get("stadium", 0) * COSTS["stadium"]
            )
            total_building_upkeep += building_upkeep

            # Resource consumption per turn:
            # Coal power plants: 0.1 ton coal per 100 infra per turn.
            total_coal_consumption += city.get("coal_power", 0) * ((infra / 100) * 0.1)

            # Oil power plants: 0.1 ton oil per 100 infra per turn.
            total_oil_consumption += city.get("oil_power", 0) * ((infra / 100) * 0.1)

            # Nuclear power plants: 0.2 ton uranium per 1000 infra per turn.
            total_uranium_consumption += city.get("nuclear_power", 0) * ((infra / 1000) * 0.2)

            # Oil refineries: 0.25 ton oil per turn.
            total_oil_consumption += city.get("oil_refinery", 0) * 0.5

            # Steel mills: consume 0.25 ton iron and 0.25 ton coal per turn each.
            total_steel_mill_iron += city.get("steel_mill", 0) * 0.75
            total_steel_mill_coal += city.get("steel_mill", 0) * 0.75

            # Aluminum refineries: consume 0.25 ton bauxite per turn.
            total_aluminum_refinery_bauxite += city.get("aluminum_refinery", 0) * 0.75

            # Munitions factories: consume 0.5 ton lead per turn.
            total_munitions_factory_lead += city.get("munitions_factory", 0) * 1.5

            # Food Consumption: 1 Per Base-Person Per Turn and 1 Per 750 Soldiers
            base_population = int(city.get("infrastructure", 0) * 100)
            date_format = "%Y-%m-%d"
            
            date1 = datetime.now(timezone.utc)
            date2 = datetime.strptime(city.get("date", "2025-01-01"), date_format).replace(tzinfo=timezone.utc)

            age = (date1 - date2).days

            city_age_modifier = 1 + max(math.log(max(age, 1)) / 15, 0)

            population = ((base_population ^ 2) / 125_000_000) + ((base_population * city_age_modifier - base_population) / 850)
            total_food_consumption += population * 1 + (nation_info.get("soldiers", 0) / 750)

            MMR_WEIGHT = 0.5
            aluminum_preparedness += (city.get("hangar", 0) * 3 * 5) * MMR_WEIGHT
            steel_preparedness += ((city.get("factory", 0) * 50 * 0.5) + (city.get("drydock", 0) * 30)) * MMR_WEIGHT

        # Military upkeep per turn (wartime rates).
        soldier_upkeep = soldiers * MILITARY_COSTS["soldiers"]
        tank_upkeep = tanks * MILITARY_COSTS["tanks"]
        aircraft_upkeep = aircraft * MILITARY_COSTS["aircraft"]
        ship_upkeep = ships * MILITARY_COSTS["ships"]
        total_military_upkeep = soldier_upkeep + tank_upkeep + aircraft_upkeep + ship_upkeep

        total_upkeep_turn = total_building_upkeep + total_military_upkeep

        # Calculate required money for 5 days (60 turns).
        required_money = total_upkeep_turn * 60
        current_money = nation_info.get("money", 0)
        money_deficit = max(required_money - current_money, 0)

        # Calculate required resources over 60 turns (5 days).
        required_coal = (total_coal_consumption + total_steel_mill_coal) * 60
        required_oil = total_oil_consumption * 60
        required_uranium = total_uranium_consumption * 60
        required_iron = total_steel_mill_iron * 60
        required_bauxite = total_aluminum_refinery_bauxite * 60
        required_lead = total_munitions_factory_lead * 60
        required_food = total_food_consumption * 60
        required_credits = 1 - nation_info.get("credits", 0) 

        # Apply scaling factor for nations with more than 15 cities
        city_count = len(nation_info.get("cities", []))
        if city_count > 15:
            # Calculate reduction: 5% per additional city beyond 15
            additional_cities = city_count - 15
            reduction_factor = 1 - (additional_cities * 0.05)  # 5% reduction per city
            reduction_factor = max(reduction_factor, 0.5)  # Cap at 50% reduction minimum
            
            # Apply scaling to all resource requirements
            required_money *= reduction_factor
            required_coal *= reduction_factor
            required_oil *= reduction_factor
            required_uranium *= reduction_factor
            required_iron *= reduction_factor
            required_bauxite *= reduction_factor
            required_lead *= reduction_factor
            required_gasoline *= reduction_factor
            required_munitions *= reduction_factor
            required_steel *= reduction_factor
            required_aluminum *= reduction_factor
            required_food *= reduction_factor
            
            info(f"Applied {reduction_factor:.2f} scaling factor for {city_count} cities (reduced by {additional_cities * 5}%)", tag="WARCH")

        # Get current resource amounts.
        current_coal = nation_info.get("coal", 0)
        current_oil = nation_info.get("oil", 0)
        current_uranium = nation_info.get("uranium", 0)
        current_iron = nation_info.get("iron", 0)
        current_bauxite = nation_info.get("bauxite", 0)
        current_lead = nation_info.get("lead", 0)
        current_gasoline = nation_info.get("gasoline", 0)
        current_munitions = nation_info.get("munitions", 0)
        current_steel = nation_info.get("steel", 0)
        current_aluminum = nation_info.get("aluminum", 0)
        current_food = nation_info.get("food", 0)
        current_credits = nation_info.get("credits", 0)
        
        # Calculate deficits (if current >= required, deficit is 0).
        coal_deficit = max(required_coal - current_coal, 0)
        oil_deficit = max(required_oil - current_oil, 0)
        uranium_deficit = max(required_uranium - current_uranium, 0)
        iron_deficit = max(required_iron - current_iron, 0)
        bauxite_deficit = max(required_bauxite - current_bauxite, 0)
        lead_deficit = max(required_lead - current_lead, 0)
        gasoline_deficit = max(required_gasoline - current_gasoline, 0)
        munitions_deficit = max(required_munitions - current_munitions, 0)
        steel_deficit = max(required_steel - current_steel, 0)
        aluminum_deficit = max(required_aluminum - current_aluminum, 0)
        food_deficit = max(required_food - current_food, 0)
        credits_deficit = max(required_credits - current_credits, 0)

        result = {
            "money_deficit": money_deficit,
            "coal_deficit": coal_deficit,
            "oil_deficit": oil_deficit,
            "uranium_deficit": uranium_deficit,
            "iron_deficit": iron_deficit,
            "bauxite_deficit": bauxite_deficit,
            "lead_deficit": lead_deficit,
            "gasoline_deficit": gasoline_deficit,
            "munitions_deficit": munitions_deficit,
            "steel_deficit": steel_deficit,
            "aluminum_deficit": aluminum_deficit,
            "food_deficit": food_deficit,
            "credits_deficit": credits_deficit,
        }

        excess = {
            resource: current - required if current > required else 0
            for resource, (required, current) in {
                "money": (required_money, current_money),
                "coal": (required_coal, current_coal),
                "oil": (required_oil, current_oil),
                "uranium": (required_uranium, current_uranium),
                "iron": (required_iron, current_iron),
                "bauxite": (required_bauxite, current_bauxite),
                "lead": (required_lead, current_lead),
                "gasoline": (required_gasoline, current_gasoline),
                "munitions": (required_munitions, current_munitions),
                "steel": (required_steel, current_steel),
                "aluminum": (required_aluminum, current_aluminum),
                "food": (required_food, current_food),
            }.items()
        }

        supply = {
            "money": required_money,
            "coal": required_coal,
            "oil": required_oil,
            "uranium": required_uranium,
            "iron": required_iron,
            "bauxite": required_bauxite,
            "lead": required_lead,
            "gasoline": required_gasoline,
            "munitions": required_munitions,
            "steel": required_steel,
            "aluminum": required_aluminum,
            "food": required_food,
            "credits": required_credits,
        }

    except Exception as e:
        error(f"Error in warchest calculation: {e}")
        return None, {}, {}

    return result, excess, supply

def balance(nation_info):
    money = 0
    coal = 0
    oil = 0
    uranium = 0
    iron = 0
    bauxite = 0
    lead = 0
    gasoline = 0
    munitions = 0
    steel = 0
    aluminum = 0
    food = 0

    try:
        for rec in nation_info.get("bankrecs", []):
            if rec.get("receiver", {}).get("id") == nation_info.get("id"):
                money += rec.get("money", 0)
                coal += rec.get("coal", 0)
                oil += rec.get("oil", 0)
                uranium += rec.get("uranium", 0)
                iron += rec.get("iron", 0)
                bauxite += rec.get("bauxite", 0)
                lead += rec.get("lead", 0)
                gasoline += rec.get("gasoline", 0)
                munitions += rec.get("munitions", 0)
                steel += rec.get("steel", 0)
                aluminum += rec.get("aluminum", 0)
                food += rec.get("food", 0)
            elif rec.get("sender", {}).get("id") == nation_info.get("id"):
                money -= rec.get("money", 0)
                coal -= rec.get("coal", 0)
                oil -= rec.get("oil", 0)
                uranium -= rec.get("uranium", 0)
                iron -= rec.get("iron", 0)
                bauxite -= rec.get("bauxite", 0)
                lead -= rec.get("lead", 0)
                gasoline -= rec.get("gasoline", 0)
                munitions -= rec.get("munitions", 0)
                steel -= rec.get("steel", 0)
                aluminum -= rec.get("aluminum", 0)
                food -= rec.get("food", 0)

    except Exception as e:
        error(f"Error in balance calculation: {e}")
        return {
            "money": 0,
            "coal": 0,
            "oil": 0,
            "uranium": 0,
            "iron": 0,
            "bauxite": 0,
            "lead": 0,
            "gasoline": 0,
            "munitions": 0,
            "steel": 0,
            "aluminum": 0,
            "food": 0
        }
    return {
        "money": money,
        "coal": coal,
        "oil": oil,
        "uranium": uranium,
        "iron": iron,
        "bauxite": bauxite,
        "lead": lead,
        "gasoline": gasoline,
        "munitions": munitions,
        "steel": steel,
        "aluminum": aluminum,
        "food": food
    }
