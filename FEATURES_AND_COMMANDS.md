# 🤖 Raiden Shogun Bot - Technical Features & Commands Specification

## 📋 **Overview**
The Raiden Shogun Discord bot is a comprehensive Politics and War (PnW) management tool designed for alliance operations, nation analysis, and military planning. This document provides detailed technical specifications, formulas, algorithms, and edge cases for all features.

## 🏗️ **Core Technical Features**

### **1. Data Management System**
- **CSV Cache System**: Downloads PnW CSV data every 5 minutes (300 seconds)
- **Nation Cache**: Real-time nation data caching with 5-minute refresh
- **Auto-updates**: Background asyncio tasks for data synchronization
- **Error Recovery**: Exponential backoff retry with corrupted file backup
- **Data Sources**: Politics and War GraphQL API + CSV endpoints
- **Storage**: Local JSON files with compression and validation
- **API Key Rotation**: Round-robin cycling through 8 API keys to prevent rate limiting
- **Scope-Based Access**: Different keys for different operations (everything, alliance, personal, messaging)

### **2. Alliance Management Engine**
- **Member Auditing**: Multi-criteria audit system with role-based requirements
- **Activity Monitoring**: Unix timestamp-based inactivity detection
- **Resource Management**: Threshold-based excess resource detection
- **Compliance Checking**: MMR, spy, project, and color bloc validation
- **Discord Integration**: Username mapping via registrations.json

### **3. Nation Analysis Framework**
- **War Range Calculations**: 75%-125% score range with binary search optimization
- **Military Analysis**: Building-based capacity calculations with usage tracking
- **Resource Tracking**: Real-time bank balance and resource monitoring
- **War Status**: Active war detection with military unit tracking

### **4. Raid Target Discovery System**
- **Target Finding**: CSV-based search with advanced filtering algorithms
- **Loot Calculations**: Multi-factor loot potential estimation
- **Filtering**: 8-stage filtering pipeline with detailed logging
- **Pagination**: 3x3 grid layout with navigation controls

## 🎯 **Detailed Command Specifications**

### **🔍 Audit Commands**

#### `/audit`
**Description:** Comprehensive alliance member audit system with 8 audit types
**Parameters:**
- `type` (required): Audit type selection
- `cities` (optional): City count filter for warchest audit [default: 100]

**Technical Implementation:**

**1. Activity Audit (`activity`)**
- **Threshold**: 24 hours (86,400 seconds)
- **Formula**: `current_time - last_active_unix >= 86400`
- **Data Source**: `member.last_active` (ISO 8601 format)
- **Parsing**: `datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))`
- **Edge Cases**: 
  - Invalid date format → Error logged, member flagged
  - Missing last_active → Defaults to 1970-01-01 (always inactive)
  - Timezone handling → Converts Z suffix to +00:00
- **Output Format**: 
  ```
  **Leader:** [Name](https://politicsandwar.com/nation/id={id})
  **Nation:** {nation_name}
  **Last Active:** <t:{unix_timestamp}:F>
  **Defensive Wars:** {count}
  **Discord:** {username}
  ```

**2. Warchest Audit (`warchest`)**
- **Duration**: 60 turns (5 days)
- **Formula**: Complex multi-resource calculation (see Warchest Calculation section)
- **Threshold**: Deficit > 25% of required supply
- **Filtering**: Only nations with ≤ `cities` parameter
- **Edge Cases**:
  - Missing city data → Skipped
  - Calculation error → Error logged, member flagged
  - Zero cities → Skipped (inactive nation)
- **Resource Thresholds**:
  - Money: 25% of required money
  - Coal: 25% of required coal
  - Oil: 25% of required oil
  - Uranium: 25% of required uranium
  - Iron: 25% of required iron
  - Bauxite: 25% of required bauxite
  - Lead: 25% of required lead
  - Gasoline: 25% of required gasoline
  - Munitions: 25% of required munitions
  - Steel: 25% of required steel
  - Aluminum: 25% of required aluminum
  - Food: 25% of required food
  - Credits: > 10 credits

**3. Spies Audit (`spies`)**
- **Requirements**: 
  - Base: 50 spies
  - With Intelligence Agency: 60 spies
- **Detection**: Checks nation projects for "Intelligence Agency"
- **Formula**: `required_spies = 60 if has_intel_agency else 50`
- **Edge Cases**:
  - Missing project data → Assumes no Intelligence Agency
  - Invalid spy count → Defaults to 0
- **Output**: Current vs Required spy count

**4. Projects Audit (`projects`)**
- **Purpose**: Check raiders (C15 and below) for project compliance when timer is up
- **Timer Check**: 120 turns (10 days) since last project
- **Required Projects**: Activity Center, Propaganda Bureau, Intelligence Agency, Research & Development, Pirate Economy, Advanced Pirate Economy
- **Data Sources**: 
  - `turns_since_last_project` (timer check)
  - `project_bits` (owned projects via bit decoding)
- **Edge Cases**:
  - Timer not up → No violation
  - Missing project data → Assumes no projects owned
  - Invalid project bits → Error logged
- **Output**: Raiders with timer up who are missing required projects

**5. Color Bloc Audit (`bloc`)**
- **Logic**: Members must match alliance color (exclude beige)
- **Formula**: `member_color != alliance_color AND member_color != 'beige'`
- **Data Sources**: 
  - Alliance color: `GET_ALLIANCE_DATA(ALLIANCE_ID)`
  - Member color: `member.color`
- **Edge Cases**:
  - Missing alliance data → Uses first member's color as reference
  - Missing member color → Defaults to 'gray'
  - Case sensitivity → Converts to lowercase for comparison
- **Exclusions**: Nations on beige color

**6. Military Audit (`military`)**
- **Purpose**: Check military capacity vs usage
- **Formula**: `usage_percentage = (current_units / capacity) * 100`
- **Capacity Calculation**: See Military Capacity section
- **Thresholds**: 
  - High usage (>90%): Warning
  - Low usage (<10%): Inefficient
- **Edge Cases**:
  - Zero capacity → Division by zero protection
  - Missing military data → Defaults to 0

**7. MMR Audit (`mmr`)**
- **Role Classification**: 
  - Raider: < 15 cities
  - Whale: ≥ 15 cities
- **Requirements**:
  - **Raider**: 5 Barracks, 0 Factories, 5 Hangars, 0 Drydocks per city
  - **Whale**: 0 Barracks, 2 Factories, 5 Hangars, 0 Drydocks per city
- **Formula**: `city.get(building) >= requirements[role][building]`
- **Edge Cases**:
  - Missing city data → Skipped
  - Missing building data → Defaults to 0
  - Invalid role → Defaults to Raider

**8. Deposit Audit (`deposit`)**
- **Thresholds** (in thousands):
  - Money: 100,000 ($100M)
  - Coal: 1,000 (1M coal)
  - Oil: 1,000 (1M oil)
  - Uranium: 100 (100k uranium)
  - Iron: 1,000 (1M iron)
  - Bauxite: 1,000 (1M bauxite)
  - Lead: 1,000 (1M lead)
  - Gasoline: 100 (100k gasoline)
  - Munitions: 100 (100k munitions)
  - Steel: 100 (100k steel)
  - Aluminum: 100 (100k aluminum)
  - Food: 1,000 (1M food)
- **Formula**: `current_amount > threshold`
- **Edge Cases**:
  - Missing resource data → Defaults to 0
  - Invalid type → Error logged

**Processing Pipeline:**
1. **Defer Response**: Immediate `interaction.response.defer()`
2. **Progress Message**: Send "Running Audit..." embed
3. **Fetch Data**: `GET_ALLIANCE_MEMBERS(ALLIANCE_ID, API_KEY)`
4. **Filter Applicants**: Exclude `alliance_position == "APPLICANT"`
5. **Pre-fetch Alliance Data**: For bloc audit (alliance color)
6. **Process Members**: Loop through each member
7. **Execute Audit**: Run specified audit type
8. **Collect Results**: Build audit_results array
9. **Update Progress**: Edit progress message with results
10. **Send Summary**: Tag violators in follow-up message

**Error Handling:**
- **API Failures**: Graceful degradation with error messages
- **Data Parsing**: Try-catch with fallback values
- **Timeout Protection**: Immediate defer prevents 3-second timeout
- **Progress Updates**: Real-time feedback during processing

#### `/audit_member`
**Description:** Comprehensive single-member audit covering all requirements
**Parameters:**
- `nation_id` (required): The ID of the nation to audit

**Technical Implementation:**
1. **Member Lookup**: `next((m for m in members if int(m['id']) == nation_id), None)`
2. **Comprehensive Audit**: Executes all 8 audit types on single member
3. **Result Aggregation**: Combines all violations into single report
4. **Error Handling**: Graceful handling of missing member or data

**Output Format:**
- **Activity**: Last active timestamp, defensive wars count
- **Warchest**: Resource deficits with emoji indicators
- **Spies**: Current vs required spy count
- **Projects**: Current project count
- **Bloc**: Color mismatch details
- **Deposit**: Excess resources list
- **MMR**: Missing buildings per city

---

## 🔑 **API Key Management & Rotation System**

### **API Key Pool Configuration**

**1. Key Distribution:**
```python
API_KEYS = {
    "everything_scope": [
        "1adc0368729abdbba56c",  # Everything Scope - Primary
        "29cc5d1b8aca3b02fe75"   # Everything Scope - Secondary
    ],
    "alliance_scope": [
        "39c40d62a96e5e2fff86",  # Alliance Scope - Primary
        "ada85c10c9fe0944cbb1",  # Alliance Scope - Secondary
        "8986a7e3c790d574a561",  # Alliance Scope - Tertiary
        "631fef9d485f7090dbfa"   # Alliance Scope - Quaternary
    ],
    "personal_scope": [
        "d26fe3dacf8ea09032b0"   # Personal (Nation 590508 only)
    ],
    "messaging_scope": [
        "2457ef98256e4256bd81"   # Send messages to nations
    ]
}
```

**2. Scope Usage Rules:**

**Everything Scope Keys (2 keys):**
- **Usage**: Nation data, war data, city data, general queries
- **Commands**: `/who`, `/wars`, `/warchest`, `/bank`, `/chest`, `/raid`, `/purge`, `/counter`
- **Operations**: `GET_NATION_DATA()`, `GET_WAR_DATA()`, CSV downloads
- **Rotation**: Round-robin between 2 keys
- **Rate Limit**: 1000 calls/hour per key

**Alliance Scope Keys (4 keys):**
- **Usage**: Alliance member data, alliance bank, alliance operations
- **Commands**: `/audit`, `/audit_member`
- **Operations**: `GET_ALLIANCE_MEMBERS()`, `GET_ALLIANCE_DATA()`
- **Rotation**: Round-robin between 4 keys
- **Rate Limit**: 1000 calls/hour per key

**Personal Scope Key (1 key):**
- **Usage**: Personal nation data only (Nation 590508)
- **Commands**: Personal `/who`, `/warchest`, `/wars` when no nation_id specified
- **Operations**: `GET_NATION_DATA(590508)`
- **Rate Limit**: 1000 calls/hour

**Messaging Scope Key (1 key):**
- **Usage**: Send messages to nations (future feature)
- **Commands**: Future messaging commands
- **Operations**: `SEND_MESSAGE_TO_NATION()`
- **Rate Limit**: 1000 calls/hour

### **API Key Rotation Algorithm**

**1. Round-Robin Selection:**
```python
class APIKeyManager:
    def __init__(self):
        self.key_pools = API_KEYS
        self.current_indices = {scope: 0 for scope in API_KEYS.keys()}
        self.rate_limits = {key: {"calls": 0, "reset_time": 0} for key in self._get_all_keys()}
        self.key_health = {key: {"status": "healthy", "last_error": None} for key in self._get_all_keys()}
    
    def get_key(self, scope: str) -> str:
        """Get next available key for specified scope with health checking."""
        if scope not in self.key_pools:
            raise ValueError(f"Invalid scope: {scope}")
        
        keys = self.key_pools[scope]
        if not keys:
            raise ValueError(f"No keys available for scope: {scope}")
        
        # Find healthy key with lowest usage
        healthy_keys = [key for key in keys if self.key_health[key]["status"] == "healthy"]
        if not healthy_keys:
            # Fallback to any key if all unhealthy
            healthy_keys = keys
        
        # Select key with lowest usage
        selected_key = min(healthy_keys, key=lambda k: self.rate_limits[k]["calls"])
        
        # Update rotation index
        self.current_indices[scope] = (self.current_indices[scope] + 1) % len(keys)
        
        return selected_key
```

**2. Rate Limit Management:**
```python
def check_rate_limit(self, key: str) -> bool:
    """Check if key is within rate limits."""
    current_time = time.time()
    rate_data = self.rate_limits[key]
    
    # Reset if past reset time (1 hour)
    if current_time >= rate_data["reset_time"]:
        rate_data["calls"] = 0
        rate_data["reset_time"] = current_time + 3600
    
    # Check if under limit (1000 calls per hour)
    return rate_data["calls"] < 1000

def increment_usage(self, key: str):
    """Increment usage counter for key."""
    self.rate_limits[key]["calls"] += 1
```

**3. Key Health Monitoring:**
```python
def mark_key_unhealthy(self, key: str, error: str):
    """Mark key as unhealthy due to error."""
    self.key_health[key]["status"] = "unhealthy"
    self.key_health[key]["last_error"] = error
    self.key_health[key]["error_time"] = time.time()

def check_key_health(self, key: str) -> bool:
    """Check if key is healthy."""
    if self.key_health[key]["status"] == "unhealthy":
        # Auto-recovery after 5 minutes
        if time.time() - self.key_health[key]["error_time"] > 300:
            self.key_health[key]["status"] = "healthy"
            self.key_health[key]["last_error"] = None
    
    return self.key_health[key]["status"] == "healthy"
```

### **Integration with Existing Functions**

**1. Modified Data Fetching Functions:**
```python
def GET_NATION_DATA(nation_id: str, scope: str = "everything_scope") -> Optional[Dict]:
    """Get nation data using appropriate scoped key."""
    key_manager = get_key_manager()
    api_key = key_manager.get_key(scope)
    
    # Check rate limit
    if not key_manager.check_rate_limit(api_key):
        # Try next key in pool
        api_key = key_manager.get_key(scope)
    
    try:
        # Make API call
        response = make_api_call(api_key, nation_id)
        key_manager.increment_usage(api_key)
        return response
    except RateLimitError:
        key_manager.mark_key_unhealthy(api_key, "Rate limit exceeded")
        # Retry with different key
        return GET_NATION_DATA(nation_id, scope)
    except Exception as e:
        key_manager.mark_key_unhealthy(api_key, str(e))
        raise

def GET_ALLIANCE_MEMBERS(alliance_id: str, scope: str = "alliance_scope") -> Optional[List[Dict]]:
    """Get alliance members using alliance scoped key."""
    key_manager = get_key_manager()
    api_key = key_manager.get_key(scope)
    
    # Implementation with key rotation
    # ... (similar pattern)
```

**2. Command-Specific Key Usage:**
```python
# In audit commands
async def audit(self, interaction: discord.Interaction, type: str, cities: int = 100):
    # Use alliance scope for member data
    members = get_data.GET_ALLIANCE_MEMBERS(self.config.ALLIANCE_ID, scope="alliance_scope")
    
    # Use everything scope for individual nation data
    for member in members:
        nation_data = get_data.GET_NATION_DATA(member['id'], scope="everything_scope")

# In personal commands
async def warchest(self, interaction: discord.Interaction, nation_id: int = None):
    if nation_id is None:
        # Use personal scope for user's nation
        nation_data = get_data.GET_NATION_DATA(user_nation_id, scope="personal_scope")
    else:
        # Use everything scope for specified nation
        nation_data = get_data.GET_NATION_DATA(nation_id, scope="everything_scope")
```

### **Performance Benefits**

**1. Rate Limit Avoidance:**
- **Before**: 1 key handling all requests → 1000 calls/hour limit
- **After**: 8 keys with rotation → 8000 calls/hour total capacity
- **Improvement**: 8x increase in API call capacity

**2. Load Distribution:**
- **Everything Scope**: 2 keys for general operations
- **Alliance Scope**: 4 keys for audit operations (high volume)
- **Personal Scope**: 1 key for personal commands
- **Messaging Scope**: 1 key for future messaging

**3. Fault Tolerance:**
- **Key Health Monitoring**: Automatic detection of unhealthy keys
- **Auto-Recovery**: Unhealthy keys recover after 5 minutes
- **Fallback Strategy**: Use any available key if all healthy keys exhausted
- **Error Isolation**: One bad key doesn't affect others

### **Monitoring & Analytics**

**1. Key Usage Tracking:**
```python
def get_key_usage_stats(self) -> Dict:
    """Get usage statistics for all keys."""
    stats = {}
    for scope, keys in self.key_pools.items():
        stats[scope] = {
            "total_calls": sum(self.rate_limits[key]["calls"] for key in keys),
            "average_calls": sum(self.rate_limits[key]["calls"] for key in keys) / len(keys),
            "healthy_keys": sum(1 for key in keys if self.key_health[key]["status"] == "healthy"),
            "unhealthy_keys": sum(1 for key in keys if self.key_health[key]["status"] == "unhealthy")
        }
    return stats
```

**2. Rate Limit Alerts:**
- **Warning**: Key reaches 80% of rate limit (800 calls/hour)
- **Critical**: Key reaches 95% of rate limit (950 calls/hour)
- **Emergency**: All keys in scope reach 90% of rate limit

**3. Performance Metrics:**
- **API Call Distribution**: Calls per key per scope
- **Error Rates**: Failed calls per key
- **Recovery Times**: Time to recover from key failures
- **Load Balancing**: Evenness of key usage distribution

### **Edge Cases & Error Handling**

**1. All Keys Unhealthy:**
- **Detection**: All keys in scope marked as unhealthy
- **Response**: Use fallback key (first key in pool)
- **Recovery**: Reset all keys to healthy after 10 minutes
- **Logging**: Critical error logged for investigation

**2. Rate Limit Exceeded:**
- **Detection**: 429 error response from API
- **Response**: Mark key unhealthy, try next key
- **Retry**: Exponential backoff with different key
- **Fallback**: Use personal scope key if available

**3. Invalid Scope:**
- **Detection**: Scope not found in key pools
- **Response**: Default to everything scope
- **Logging**: Warning logged for invalid scope usage
- **Recovery**: Continue with default scope

**4. Key Pool Exhaustion:**
- **Detection**: All keys in scope at rate limit
- **Response**: Queue requests for next hour
- **Notification**: Alert administrators
- **Recovery**: Automatic retry when rate limits reset

---

## 🧮 **Mathematical Formulas & Calculations**

### **Warchest Calculation System**

**Purpose**: Calculate required resources for 60 turns (5 days) of operation

**Base Formulas:**

**1. Military Resource Usage (Per Turn):**
```
gasoline_per_turn = (soldiers / 5000) + (tanks / 100) + (aircraft / 4) + 2.5
munitions_per_turn = (soldiers / 5000) + (tanks / 100) + (aircraft / 4) + 2
steel_per_turn = (tanks / 100) + (ships / 5)
aluminum_per_turn = aircraft / 4
```

**2. Total Military Requirements (60 Turns):**
```
required_gasoline = gasoline_per_turn * 60
required_munitions = munitions_per_turn * 60
required_steel = steel_per_turn * 60
required_aluminum = aluminum_per_turn * 60
```

**3. Building Upkeep Costs (Per Turn):**
```
COSTS = {
    "coal_power": 100,          # $100/turn
    "oil_power": 150,           # $150/turn
    "nuclear_power": 875,       # $875/turn
    "wind_power": 42,           # $42/turn
    "farm": 25,                 # $25/turn
    "uranium_mine": 417,        # $417/turn
    "iron_mine": 134,           # $134/turn
    "coal_mine": 34,            # $34/turn
    "oil_refinery": 334,        # $334/turn
    "steel_mill": 334,          # $334/turn
    "aluminum_refinery": 209,   # $209/turn
    "munitions_factory": 292,   # $292/turn
    "police_station": 63,       # $63/turn
    "hospital": 84,             # $84/turn
    "recycling_center": 209,    # $209/turn
    "subway": 271,              # $271/turn
    "supermarket": 50,          # $50/turn
    "bank": 150,                # $150/turn
    "shopping_mall": 450,       # $450/turn
    "stadium": 1013             # $1013/turn
}
```

**4. Military Upkeep Costs (Per Turn):**
```
MILITARY_COSTS = {
    "soldiers": 1.88 / 12,      # per soldier per turn
    "tanks": 75 / 12,           # per tank per turn
    "aircraft": 750 / 12,       # per aircraft per turn
    "ships": 5062.5 / 12        # per ship per turn
}
```

**5. Resource Consumption (Per Turn):**
```
coal_consumption = (coal_power_plants * 0.1) + (steel_mills * 0.1)
oil_consumption = (oil_power_plants * 0.1) + (oil_refineries * 0.5)
uranium_consumption = nuclear_power_plants * 0.2
iron_consumption = steel_mills * 0.75
bauxite_consumption = aluminum_refineries * 0.75
lead_consumption = munitions_factories * 1.5
```

**6. Food Consumption (Per Turn):**
```
food_consumption = population * 0.01  # 1% of population per turn
```

**7. City Scaling Factor (Nations > 15 Cities):**
```
if city_count > 15:
    additional_cities = city_count - 15
    reduction_factor = 1 - (additional_cities * 0.05)  # 5% reduction per city
    reduction_factor = max(reduction_factor, 0.5)  # Cap at 50% minimum
    
    # Apply to all resource requirements
    required_money *= reduction_factor
    required_coal *= reduction_factor
    # ... (all resources)
```

**8. Deficit Calculation:**
```
deficit = max(required_amount - current_amount, 0)
```

**9. Excess Calculation:**
```
excess = max(current_amount - required_amount, 0)
```

**Edge Cases:**
- **Zero Cities**: Nation skipped (inactive)
- **Missing Data**: Defaults to 0 for all values
- **Calculation Error**: Returns None, error logged
- **Division by Zero**: Protected with max() functions
- **Negative Values**: Protected with max(0, value)

### **Raid Target Discovery Algorithm**

**Purpose**: Find profitable raid targets using CSV data with advanced filtering

**1. Score Range Calculation:**
```
user_score = float(nation_data.get('score', 0))
min_score = user_score * 0.75  # 75% of user's score
max_score = user_score * 1.25  # 125% of user's score
```

**2. 8-Stage Filtering Pipeline:**

**Stage 1: Score Range Filter**
```
if not (min_score <= target_score <= max_score):
    filtered_out['score_range'] += 1
    continue
```

**Stage 2: Vacation Mode Filter**
```
if target.get('vmode', 0) == 1:
    filtered_out['vmode'] += 1
    continue
```

**Stage 3: Beige Turns Filter**
```
if target.get('beige_turns', 0) > 0:
    filtered_out['beige_turns'] += 1
    continue
```

**Stage 4: Alliance Filter**
```
alliance_id = target.get('alliance_id')
if alliance_id == 13033 or alliance_id in top_60_alliances:
    filtered_out['top_alliance'] += 1
    continue
```

**Stage 5: Defensive Wars Filter**
```
defensive_wars = defensive_wars_by_nation.get(target.get('id'), 0)
if defensive_wars >= 3:
    filtered_out['defensive_wars'] += 1
    continue
```

**Stage 6: Cities Existence Filter**
```
cities = cities_by_nation.get(target.get('id'), [])
if not cities:
    filtered_out['no_cities'] += 1
    continue
```

**Stage 7: Loot Potential Filter**
```
total_loot_potential = calculate_loot_potential(target, cities, [])
if total_loot_potential <= 100000:  # Minimum $100k
    filtered_out['low_loot'] += 1
    continue
```

**Stage 8: Final Validation**
```
# Additional checks for military strength, infrastructure, etc.
```

**3. Loot Potential Calculation:**
```
def calculate_loot_potential(nation, cities, wars):
    base_loot = 0.0
    
    # GDP-based loot (10% of GDP)
    gdp = float(nation.get('gdp', 0))
    base_loot += gdp * 0.1
    
    # Military value-based loot (10% of military value)
    soldiers = int(nation.get('soldiers', 0))
    tanks = int(nation.get('tanks', 0))
    aircraft = int(nation.get('aircraft', 0))
    ships = int(nation.get('ships', 0))
    
    military_value = (soldiers * 1.25) + (tanks * 50) + (aircraft * 500) + (ships * 3375)
    base_loot += military_value * 0.1
    
    # City-based loot (5% of estimated city value)
    cities_count = int(nation.get('cities', 0))
    if cities_count > 0:
        city_loot = cities_count * 50000  # $50k per city estimate
        base_loot += city_loot * 0.05
    
    # War performance modifier
    war_modifier = 1.0
    if wars:
        # Calculate average loot from recent wars
        total_loot = sum(war.get('loot', 0) for war in wars)
        war_modifier = 1.0 + (total_loot / len(wars)) / 1000000  # 1% per $1M average loot
    
    return base_loot * war_modifier
```

**4. Military Strength Calculation:**
```
military_strength = (
    target.get('soldiers', 0) * 0.5 +
    target.get('tanks', 0) * 5 +
    target.get('aircraft', 0) * 10 +
    target.get('ships', 0) * 20
)
```

**5. Infrastructure Calculation:**
```
total_infra = sum(city.get('infrastructure', 0) for city in cities)
```

**6. Sorting Algorithm:**
```
valid_targets.sort(key=lambda x: x['profit'], reverse=True)
```

**Edge Cases:**
- **Missing Data**: Defaults to 0 for all calculations
- **Invalid Scores**: Skipped with error logging
- **Empty Cities**: Nation filtered out
- **API Failures**: Graceful degradation
- **Large Datasets**: Progress updates every 1000 nations

### **Military Capacity Calculation**

**Purpose**: Calculate military unit capacity from city buildings

**1. Capacity per Building:**
```
capacity_per_building = {
    "barracks": 3000,    # soldiers per barracks
    "factory": 250,      # tanks per factory
    "hangar": 15,        # aircraft per hangar
    "drydock": 5         # ships per drydock
}
```

**2. Total Capacity Calculation:**
```
def calculate_military_capacity(cities):
    capacity = {"soldiers": 0, "tanks": 0, "aircraft": 0, "ships": 0}
    
    for city in cities:
        capacity["soldiers"] += city.get("barracks", 0) * 3000
        capacity["tanks"] += city.get("factory", 0) * 250
        capacity["aircraft"] += city.get("hangar", 0) * 15
        capacity["ships"] += city.get("drydock", 0) * 5
    
    return capacity
```

**3. Usage Percentage:**
```
usage_percentage = (current_units / capacity) * 100
```

**4. MMR Requirements:**
```
mmr_requirements = {
    "Raider": {
        "barracks": 5,    # 5 barracks per city
        "factory": 0,     # 0 factories per city
        "hangar": 5,      # 5 hangars per city
        "drydock": 0      # 0 drydocks per city
    },
    "Whale": {
        "barracks": 0,    # 0 barracks per city
        "factory": 2,     # 2 factories per city
        "hangar": 5,      # 5 hangars per city
        "drydock": 0      # 0 drydocks per city
    }
}
```

**5. Role Classification:**
```
role = "Whale" if len(cities) >= 15 else "Raider"
```

**6. MMR Compliance Check:**
```
def check_city_mmr(city, role):
    requirements = mmr_requirements[role]
    return {
        "barracks": city.get("barracks", 0) >= requirements["barracks"],
        "factory": city.get("factory", 0) >= requirements["factory"],
        "hangar": city.get("hangar", 0) >= requirements["hangar"],
        "drydock": city.get("drydock", 0) >= requirements["drydock"]
    }
```

**Edge Cases:**
- **Missing City Data**: Skipped with error logging
- **Zero Capacity**: Division by zero protection
- **Invalid Role**: Defaults to Raider
- **Missing Building Data**: Defaults to 0

---

## 🔧 **Technical Architecture & Performance**

### **Data Management System**

**1. CSV Cache Architecture:**
- **Update Frequency**: Every 5 minutes (300 seconds)
- **Data Sources**: Politics and War CSV endpoints
- **Storage Format**: Local JSON files with compression
- **Error Recovery**: Corrupted file backup and regeneration
- **Memory Usage**: ~50MB for full dataset
- **Disk Usage**: ~100MB for compressed JSON

**2. API Rate Limiting & Key Management:**
- **Rate Limit**: 1 request per 0.5 seconds per key
- **Key Rotation**: Round-robin cycling through 8 API keys
- **Scope Distribution**: 
  - Everything Scope: 2 keys (nation data, wars, cities)
  - Alliance Scope: 4 keys (alliance operations)
  - Personal Scope: 1 key (Nation 590508 only)
  - Messaging Scope: 1 key (future messaging feature)
- **Retry Logic**: Exponential backoff (1s, 2s, 4s, 8s)
- **Queue Management**: Sequential processing to prevent overwhelming
- **Error Handling**: Graceful degradation on 429 errors
- **Key Health Monitoring**: Track usage and rate limits per key

**3. Caching Strategy:**
- **L1 Cache**: In-memory nation data (5-minute TTL)
- **L2 Cache**: CSV data (5-minute TTL)
- **L3 Cache**: Alliance data (30-minute TTL)
- **Cache Invalidation**: Time-based with manual refresh capability

### **Performance Metrics**

**1. Response Times:**
- **Simple Commands** (< 1 second):
  - `/ping`: ~50ms
  - `/help`: ~100ms
  - `/who`: ~200ms
- **Medium Commands** (1-3 seconds):
  - `/warchest`: ~1.5s
  - `/bank`: ~1.2s
  - `/wars`: ~2.0s
- **Complex Commands** (3-10 seconds):
  - `/audit`: ~5-8s (depends on alliance size)
  - `/raid`: ~3-5s (depends on CSV cache size)
  - `/counter`: ~2-3s

**2. Memory Usage:**
- **Base Memory**: ~20MB
- **With Full Cache**: ~70MB
- **Peak Memory**: ~100MB (during large operations)
- **Memory Growth**: Linear with cache size

**3. CPU Usage:**
- **Idle**: < 1%
- **Normal Operations**: 5-15%
- **Large Audits**: 20-40%
- **Peak Load**: 50-80%

### **Error Handling & Recovery**

**1. API Error Handling:**
- **429 Too Many Requests**: Automatic retry with backoff
- **503 Service Unavailable**: Graceful degradation
- **400 Bad Request**: Error logging and user notification
- **Timeout**: 30-second timeout with retry

**2. Data Error Handling:**
- **Corrupted JSON**: Backup and regeneration
- **Missing Fields**: Default value substitution
- **Invalid Types**: Type conversion with error logging
- **Empty Responses**: Graceful fallback

**3. Discord Error Handling:**
- **Interaction Timeout**: Immediate defer prevents 3-second timeout
- **Permission Errors**: User-friendly error messages
- **Rate Limiting**: Queue management for bulk operations
- **Channel Errors**: Fallback to DM if possible

### **Security & Permissions**

**1. Permission System:**
- **Admin Commands**: Restricted to specific user IDs
- **Guild Commands**: Limited to specific Discord server
- **User Registration**: Required for nation-specific commands
- **Data Access**: Read-only access to public PnW data

**2. Input Validation:**
- **Nation IDs**: Integer validation with range checks
- **User Input**: Sanitization and length limits
- **API Parameters**: Type checking and validation
- **File Operations**: Path validation and sandboxing

**3. Data Protection:**
- **No Sensitive Data**: Only public PnW data stored
- **Secure Storage**: Environment variables for secrets
- **Access Control**: Role-based command restrictions
- **Audit Trail**: Command usage logging

---

## 📊 **Monitoring & Logging**

### **Logging System**

**1. Log Levels:**
- **DEBUG**: Detailed operation information
- **INFO**: General operation status
- **WARNING**: Non-critical issues
- **ERROR**: Recoverable errors
- **FATAL**: Critical errors requiring attention

**2. Log Categories:**
- **API**: All external API calls and responses
- **CACHE**: Cache operations and updates
- **AUDIT**: Audit command execution and results
- **RAID**: Raid target discovery and filtering
- **MILITARY**: Military calculations and analysis
- **ERROR**: All error conditions and exceptions

**3. Performance Monitoring:**
- **Latency Tracking**: Bot response times
- **Memory Usage**: RAM consumption monitoring
- **API Calls**: Request frequency and success rates
- **Cache Hit Rate**: Cache effectiveness metrics

### **Health Checks**

**1. System Health:**
- **Bot Status**: Online/offline detection
- **API Connectivity**: PnW API availability
- **Cache Status**: Data freshness and validity
- **Memory Usage**: Resource consumption monitoring

**2. Data Health:**
- **Cache Age**: Time since last update
- **Data Completeness**: Missing or corrupted data detection
- **API Response Quality**: Data validation and verification
- **Error Rates**: Failure frequency tracking

---

## 🚀 **Deployment & Maintenance**

### **Deployment Process**

**1. Environment Setup:**
- **Python Version**: 3.8+
- **Dependencies**: requirements.txt
- **Environment Variables**: BOT_TOKEN, API_KEY, ALLIANCE_ID
- **File Permissions**: Read/write access to data directory

**2. Startup Sequence:**
1. Load configuration and environment variables
2. Initialize Discord bot with intents
3. Load all cogs and command handlers
4. Initialize CSV cache system
5. Start background tasks (latency monitoring, cache updates)
6. Sync Discord commands
7. Set bot status and presence

**3. Shutdown Sequence:**
1. Stop background tasks gracefully
2. Save any pending data
3. Close API connections
4. Log shutdown reason
5. Exit cleanly

### **Maintenance Tasks**

**1. Daily:**
- Monitor error logs for issues
- Check cache update success rates
- Verify API connectivity
- Review performance metrics

**2. Weekly:**
- Clean up old log files
- Verify data integrity
- Update dependencies if needed
- Review user feedback and suggestions

**3. Monthly:**
- Full system health check
- Performance optimization review
- Security audit
- Backup verification

---

**Last Updated:** 2024-09-30
**Version:** 2.0
**Bot Version:** Raiden Shogun v2.0
**Technical Specification:** Complete

### **🏛️ Nation Commands**

#### `/warchest`
**Description:** Calculate a nation's warchest requirements (5 days of upkeep)
**Parameters:**
- `nation_id` (optional): Nation ID for which to calculate the warchest (uses registered nation if not provided)

**How it works:**
1. Fetches nation data from PnW API
2. Calculates required resources for 60 turns (5 days)
3. Compares with current resources
4. Shows deficits and excess resources
5. Provides direct deposit link if there are excess resources

**Output:**
- Required resources breakdown
- Current resources status
- Deficit/excess calculations
- Direct deposit link (if applicable)

#### `/bank`
**Description:** Check the bank balance of a nation
**Parameters:**
- `nation_id` (required): Nation ID to check

**How it works:**
1. Fetches nation data from PnW API
2. Extracts bank resource information
3. Formats and displays bank contents

**Output:**
- Bank resource breakdown
- Total bank value
- Resource icons and amounts

#### `/wars`
**Description:** Check the active wars and military of a nation
**Parameters:**
- `nation_id` (optional): Nation ID to check (uses registered nation if not provided)

**How it works:**
1. Fetches nation data from PnW API
2. Retrieves active wars (offensive and defensive)
3. Shows military units in each war
4. Displays war control status

**Output:**
- Active wars list
- Military units per war
- War control status (ground, air, naval)
- War points and resistance

#### `/who`
**Description:** Show basic information about a nation
**Parameters:**
- `nation_id` (optional): The ID of the nation to look up (uses registered nation if not provided)

**How it works:**
1. Fetches comprehensive nation data
2. Displays key nation statistics
3. Shows alliance information
4. Includes recent activity data

**Output:**
- Nation name and leader
- Score and cities
- Alliance information
- Last active timestamp
- Military units summary

#### `/raid`
**Description:** Find profitable raid targets within your war range
**Parameters:**
- `nation_id` (optional): The ID of the nation to check (uses registered nation if not provided)

**How it works:**
1. Gets user's nation score
2. Calculates war range (75% to 125% of user's score)
3. Searches CSV cache for valid targets
4. Filters out invalid targets (vmode, beige, defensive wars, high-rank alliances)
5. Calculates loot potential
6. Returns paginated results with 3x3 grid layout

**Output:**
- Paginated target list (9 per page)
- Nation links to war declare page
- Military unit counts
- Loot potential estimates
- Navigation buttons

#### `/purge`
**Description:** Find purge targets: purple nations with <15 cities, not in alliance 13033
**Parameters:** None

**How it works:**
1. Searches CSV cache for purple nations
2. Filters by city count (<15)
3. Excludes alliance 13033 members
4. Returns paginated results

#### `/counter`
**Description:** Find alliance members within war range of a target nation
**Parameters:**
- `target_nation_id` (required): The ID of the target nation to find counters for

**How it works:**
1. Gets target nation's score
2. Calculates war range for target
3. Searches alliance members within range
4. Returns potential counter nations

#### `/chest`
**Description:** Show the current amount of resources on a nation
**Parameters:**
- `nation_id` (optional): The nation ID to check (uses registered nation if not provided)

**How it works:**
1. Fetches nation data from PnW API
2. Displays current resource amounts
3. Shows resource values and totals

### **⚔️ Military Commands**

#### `/military`
**Description:** Check a nation's military capacity and usage
**Parameters:**
- `nation_id` (optional): The ID of the nation to check (uses registered nation if not provided)

**How it works:**
1. Fetches nation data from PnW API
2. Calculates military capacity from buildings
3. Compares with current military units
4. Shows usage percentage and compliance

**Output:**
- Current military units
- Military capacity from buildings
- Usage percentage
- MMR compliance status

#### `/mmr`
**Description:** Check a nation's MMR (Military Manufacturing Ratio) status
**Parameters:**
- `nation_id` (optional): The ID of the nation to check (uses registered nation if not provided)

**How it works:**
1. Fetches nation data from PnW API
2. Determines role (Raider for <15 cities, Whale for ≥15 cities)
3. Checks MMR requirements for each city
4. Reports missing buildings

**Output:**
- Required MMR based on city count
- Current MMR status per city
- Missing buildings breakdown
- Role classification

### **🏛️ Alliance Commands**

#### `/bank` (Alliance)
**Description:** Check alliance bank balance
**Parameters:** None

**How it works:**
1. Fetches alliance data from PnW API
2. Displays total resources in bank
3. Shows resource breakdown

### **⚔️ War Commands**

#### `/war`
**Description:** Show active wars for a nation
**Parameters:**
- `nation_id` (required): The ID of the nation to check wars for

**How it works:**
1. Fetches nation data from PnW API
2. Retrieves active wars
3. Displays war details and status

**Output:**
- Active wars list
- War type and reason
- Attacker and defender information
- War points and resistance
- Control status

### **🛠️ Utility Commands**

#### `/help`
**Description:** Get help with bot commands
**Parameters:**
- `category` (optional): Category of commands to get help with
  - `all` - All commands
  - `audit` - Audit commands
  - `nation` - Nation commands
  - `war` - War commands
  - `military` - Military commands
  - `bank` - Bank commands

**How it works:**
1. Displays categorized command help
2. Shows command descriptions and parameters
3. Provides usage examples

#### `/ping`
**Description:** Check the bot's latency
**Parameters:** None

**How it works:**
1. Measures bot latency
2. Displays latency in milliseconds
3. Shows connection status

#### `/suggest`
**Description:** Suggest something to the bot
**Parameters:**
- `suggestion` (required): Your suggestion

**How it works:**
1. Stores suggestion in database
2. Sends confirmation message
3. Logs suggestion for review

#### `/report-a-bug`
**Description:** Report a bug to the bot
**Parameters:**
- `report` (required): The bug description

**How it works:**
1. Stores bug report in database
2. Sends confirmation message
3. Logs bug report for review

### **👤 User Commands**

#### `/register`
**Description:** Register your Politics and War nation with your Discord account
**Parameters:**
- `nation_id` (required): Your Politics and War nation ID

**How it works:**
1. Validates nation ID exists
2. Links Discord account to nation
3. Stores registration in database
4. Enables nation-specific commands

### **🔧 Admin Commands**

#### `/update_cache`
**Description:** Update the CSV cache with latest data from Politics and War
**Parameters:** None
**Permissions:** Admin only (Ivy)

**How it works:**
1. Triggers manual cache update
2. Downloads latest CSV data
3. Updates local cache files
4. Confirms update completion

#### `/force_update`
**Description:** Force update both CSV and nation caches immediately
**Parameters:** None
**Permissions:** Admin only (Ivy)

**How it works:**
1. Forces immediate cache refresh
2. Updates both CSV and nation caches
3. Clears old cache data
4. Confirms update completion

## 🔧 **Technical Features**

### **Caching System**
- **CSV Cache**: Downloads PnW CSV data every 5 minutes
- **Nation Cache**: Real-time nation data caching
- **Auto-cleanup**: Removes old cache files
- **Error Recovery**: Handles corrupted cache files

### **Pagination**
- **Activity Paginator**: For audit results
- **Grid Paginator**: For raid targets (3x3 grid)
- **Navigation**: Previous/Next buttons
- **Timeout**: 5-minute timeout for interactions

### **Error Handling**
- **API Errors**: Handles 429 (rate limit), 503 (service unavailable)
- **Timeout Handling**: Prevents command timeouts
- **Graceful Degradation**: Continues operation on errors
- **User Feedback**: Clear error messages

### **Data Sources**
- **Politics and War API**: Primary data source
- **CSV Downloads**: Bulk data for performance
- **Local Cache**: Fast access to frequently used data
- **Real-time Updates**: Live data when needed

## 📊 **Performance Metrics**

### **Response Times**
- **Simple Commands**: < 1 second
- **Complex Commands**: < 5 seconds
- **Cache Hits**: < 500ms
- **API Calls**: 1-3 seconds

### **Rate Limiting**
- **API Calls**: Respects PnW rate limits
- **Delays**: 0.5s between API calls
- **Retry Logic**: Exponential backoff
- **Queue Management**: Prevents overwhelming API

## 🔒 **Security Features**

### **Permission System**
- **Admin Commands**: Restricted to specific users
- **Guild Commands**: Limited to specific Discord server
- **Input Validation**: Sanitizes all user inputs
- **Error Logging**: Comprehensive error tracking

### **Data Protection**
- **No Sensitive Data**: Only public PnW data
- **Secure Storage**: Encrypted configuration
- **Access Control**: Role-based permissions
- **Audit Trail**: Command usage logging

---

**Last Updated:** 2024-09-30
**Version:** 1.0
**Bot Version:** Raiden Shogun v2.0
