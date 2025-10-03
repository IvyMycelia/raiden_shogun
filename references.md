Improvements & Details
City Details
Base Population = Infrastructure * 100
Infra Unit Cost = [((Current Infra-10)^2.2) / 710] + 300
Improvements = Infra/50
Land Unit Cost  = 0.002*(Current Land-20)^2 + 50
Population = (Base Pop - ((Disease Rate * 100 * Infra)/100) - MAX((Crime Rate / 10) * (100*Infra) - 25, 0) * (1 + ln(CityAgeInDays)/15)
Note: 0≤ Crime Rate ≤100
Crime (%) = ((103 - Commerce)^2 + ( Infrastructure * 100))/(111111) - Police Modifier
Where Police Modifier is:
Police Modifier = (# of Police Stations)*(2.5)

Disease Rate = ((((Population Density^2) * 0.01) - 25)/100) + (Base Population/100000) + Pollution Modifier - Hospital Modifier

Pop density is based on base population not on displayed population
Pollution Modifier is the increase to disease, from increasing Pollution.
Pollution Modifier = Pollution Index * 0.05

Hospital Modifier is the amount of disease reduced by buying Hospitals.
Hospital Modifier = Hospital Count * 2.5
Crime Deaths = (Crime Rate/10)*(Infrastructure*100)-25
Disease Deaths = Disease Rate * Base Population
Food Production = Farm Count * (Land Area / 500)
Modifiers to this basic formula include:
If the Mass Irrigation Nation Project is built the formula is changed to Farms * (Land Area / 400)
If the season is Summer the production is changed to Food * 1.2
If the season is Winter the production is changed to Food * .8
Final Food Prod = Food Production * (nation+continent+global rad index)/1000
The improvements that affect Commerce and their effects are:
Supermarkets (+3%)
Banks (+5%)
Shopping Malls (+9%)
Stadiums (+12%)
Subways (+8%)


Continent
Oil
Coal
Iron
Bauxite
Lead
Uranium
Africa
X




X


X
Antarctica
X
X






X
Asia
X


X




X
Australia


X


X
X


Europe


X
X


X


North America


X
X




X
South America
X




X
X




Africa: Oil, bauxite, uranium
Antarctica: Oil, Coal, Uranium
Asia: Oil, Iron, Uranium
Australia: Coal, Bauxite, Lead
Europe: Coal, Iron, Lead
North America: Coal, Iron, Uranium
South America: Oil, Bauxite, Lead































Power
Coal Power Plant
Coal power is an inexpensive but dirty way to power your city. Coal plants cost $5,000 to build.
Coal power plants can provide power for up to 500 infrastructure levels. They use 1.2 tons of coal a day (0.1/turn) per 100 infrastructure. Operational costs are $1200 a day ($100/turn).
Coal plants add 8 points to your pollution index.

Oil Power Plant
Oil power is cleaner than coal power but more expensive. Oil plants cost $7,000 to build.
Oil power plants can provide power for up to 500 infrastructure levels. They use 1.2 tons of oil a day (0.1/turn) per 100 infrastructure. Operational costs are $1800 a day. ($150/turn)
Oil plants add 6 points to your pollution index.

Nuclear Power Plant
Nuclear power is very expensive but provides a lot of power and is clean. Nuclear plants cost $500,000 and 100 to build.
They use 2.4 tons a day (0.2/turn) of uranium per 1,000 infrastructure and can power up to 2,000 infrastructure. Operational costs are $10,500 a day ($875/turn).
Nuclear power plants do not affect your pollution index.

Wind Power Plant
Wind power is expensive and does not provide much power but is very clean. Wind plants cost $30,000 and 25 to build.
Wind power plants can provide power for up to 250 infrastructure levels. They do not require resources to operate. Operational costs are $500 a day ($42/turn).
Wind power plants do not affect your pollution index.
Resources
Coal Mine
Coal mines allow you to harvest coal for energy use and trade. Coal mines cost $1,000 to build.
Coal mines provide 0.25 tons of coal per turn or 3 tons of coal per day. Operational costs are $400 per day ($34/turn). You can have up to 10 coal mines per city.
Each coal mine adds 12 points to your pollution index.

Iron Mine
Iron mines allow you to harvest iron which is refined into Steel. Steel can be used for a variety of things, namely naval ships and structures. Iron mines cost $9,500 to build.
Iron mines provide 0.25 tons of iron per turn or 3 tons of iron per day. Operational costs are $1,600 per day ($134/turn). You can have up to 10 iron mines per city.
Each iron mine adds 12 points to your pollution index.

Uranium Mine
Uranium mines allow you to harvest uranium for energy use, trade, and nuclear weapons. Uranium mines cost $25,000 to build.
Uranium mines provide 0.25 tons of uranium per turn or 3 tons of uranium per day. Operational costs are $5,000 per day ($417/turn). You can have up to 5 uranium mines per city.
Each uranium mine adds 20 points to your pollution index.

Farm
Farms allow you to produce food for your ever growing population. Farms cost $1,000 to build.
Farms provide Food equivalent to your Land Area⁄500 (9.00) tons of Food per turn. Operational costs are $300 per day ($25/turn). You can have up to 20 farms per city.
Each Farm adds 2 points to your Pollution Index.
Manufacturing
Oil Refinery
Oil Refineries turn oil into gasoline. They can turn 3 tons of oil into 6 tons of gasoline daily (0.5/turn). Oil Refineries cost $45,000 to build.
Operational costs are $4,000 per day ($334/turn). You can have up to 5 oil refineries per city.
Each oil refinery adds 32 points to your pollution index.

Steel Mill
Steel Mills turn iron into steel. They can turn 3 tons of iron and coal into 9 tons of steel daily (0.75/turn). Steel Mills cost $45,000 to build.
Operational costs are $4,000 per day ($334/turn). You can have up to 5 steel mills per city.
Each steel mill adds 40 points to your pollution index.

Aluminum Refinery
Aluminum Refineries turn bauxite into aluminum. They can turn 3 tons of bauxite into 9 tons of aluminum daily (0.75/turn). Aluminum Refineries cost $30,000 to build.
Operational costs are $2,500 per day ($209/turn). You can have up to 5 aluminum refineries per city.
Each aluminum refinery adds 40 points to your pollution index.

Munitions Factory
Munitions Factories turn lead into munitions. They can turn 6 tons of lead into 18 tons of munitions daily (1.5/turn). Munitions factories cost $35,000 to build.
Operational costs are $3,500 per day ($292/turn). You can have up to 5 munitions factories per city.
Each munitions factory adds 32 points to your pollution index.
Civil
Police Station
Police Stations reduce crime by 2.5%. Police Stations cost $75,000 and 20 to build.
Operational costs are $750 per day ($63/turn). You can have up to 5 police stations per city.
Police stations add 1 point to your pollution index.

Hospital
Hospitals reduce disease by 2.5%. Hospitals cost $100,000 and 25 to build.
Operational costs are $1,000 per day ($84/turn). You can have up to 5 hospitals per city.
Each hospital adds 4 points to your pollution index.

Recycling Center
Recycling centers reduce the pollution index by 70 in this city. Recycling centers cost $125,000 to build.
Operational costs are $2,500 per day ($209/turn). You can have up to 3 recycling centers per city.
Each recycling center removes 70 points from your pollution index.

Subway
Subways increase the commerce rate by 8% and reduce the pollution index by 45 in this city. Subways cost $250,000, 50 and 25 to build.
Operational costs are $3,250 per day ($271/turn). You can have up to 1 subway per city.
Each subway removes 45 points from your pollution index.
Commerce
Supermarket
Supermarkets increase commerce by 4%. Supermarkets cost $5,000 to build.
Operational costs are $600 per day ($50/turn). You can have up to 4 Supermarkets per city.
Supermarkets do not affect your pollution index.

Bank
Banks increase commerce by 6%. Banks cost $15,000, 5 and 10 to build.
Operational costs are $1,800 per day ($150/turn). You can have up to 5 banks per city.
Banks do not affect your pollution index.

Shopping Mall
Shopping malls increase commerce by 8%. Shopping malls cost $45,000, 20 and 25 to build.
Operational costs are $5,400 per day ($450/turn). You can have up to 4 shopping malls per city.
Each shopping mall adds 2 points to your pollution index.

Stadium
Stadiums increase commerce by 10%. Stadiums cost $100,000, 40 and 50 to build.
Operational costs are $12,150 per day ($1013/turn). You can have up to 3 stadiums per city.
Each stadium adds 5 points to your pollution index.
Military
Barracks
Barracks allow you to train infantry. Barracks cost $3,000 to build.
Barracks house Soldiers and increase the maximum amount you can have enlisted. Each Barracks lets you enlist 1,000 new Soldiers a day at a maximum of 3,000 Soldiers per Barracks. Each Soldier costs $1.25 per day in peacetime, or $1.88 per day in wartime. You can have 5 Barracks per city.

Factory
Factories allow you to manufacture tanks. Factories cost $15,000 and 5 to build.
Factories allow you to manufacture up to 50 new Tanks a day at a maximum of 250 Tanks per factory. Each Tank costs $50 per day in peacetime and $75 per day in wartime. In battles Tanks use 1 per 100 Tanks and 1 per 100 Tanks. You can have 5 Factories per city.

Hangar
Hangars allow you to manufacture Aircraft. Hangars cost $100,000 and 10 to build.
Hangars allow you to manufacture up to 3 new Aircraft a day at a maximum of 15 aircraft per Hangar. Each Aircraft costs $500 per day in peacetime and $750 per day in wartime. In battles Aircraft use 1 per 4 Aircraft and 1 per 4 Aircraft. You can have 5 Hangars per city.

Drydock
Drydocks allow you to manufacture navy ships. Drydocks cost $250,000 and 20 to build.
Drydocks allow you to manufacture up to 1 new Ship per day at a maximum of 5 Ships per Drydock. Each Ship costs $3,375 per day in peacetime and $5,062.5 per day in wartime. In battles Ships use 2 per Ship and 2.5 per Ship. You can have 3 Drydocks per city.


Activity Center

The Activity Center increases the daily login bonus by $1,000,000 on the first day and $2,000,000 on subsequent days in a streak. This project will not function in nations with more than 20 cities.


Advanced Engineering Corps

The Advanced Engineering Corps develops new technologies that make building new infrastructure and acquiring new land cheaper. This project reduces the cost of new land and infrastructure by 5%. Advanced Engineering Corps requires the Center for Civil Engineering and Arable Land Agency national projects to be built.
Advanced Pirate Economy

Advanced Pirate Economy is a national project that enables the nation to use an additional offensive war slot, provides a 5% bonus to loot from ground attacks, and a 10% bonus to loot from a defeated nation and its alliance bank. This national project requires the nation to have won or lost a combined 100 wars, as well as the Propaganda Bureau and Pirate Economy projects to be built.
Arable Land Agency

The Arable Land Agency makes it easier and more cost effective to acquire new habitable land, reducing the cost of purchasing new land in cities by 5%.
Arms Stockpile

Arms Stockpile is a national project that boosts Munitions Factories' productivity by 20% nationwide. Rates increase from 1.5/turn (per Munitions Factory) to 1.8/turn (per Munitions Factory). Lead usage is NOT increased to create more Munitions.
Bauxiteworks

Bauxiteworks is a national project that increases Aluminum Refineries' productivity by 36% nationwide. Rates increase from 0.75/turn (per Aluminum Refinery) to 1.02/turn (per Aluminum Refinery). Bauxite usage is increased to create more Aluminum.
Bureau of Domestic Affairs

Bureau of Domestic Affairs is a national project that removes the timer for changing Domestic Policies, and adds a +25% effect modifier to your chosen Domestic Policy. Requires the Government Support Agency National Project to build
Center for Civil Engineering

Center for Civil Engineering is a national project that increases knowledge about infrastructure. Infrastructure costs drop 5% in all cities.
Clinical Research Center

The Clinical Research Center is a dedicated effort to combatting infectious diseases in your nation, increasing the disease reduction rate from Hospitals by 1% from 2.5% to 3.5% each. This project also allows you to build an additional Hospital in each city.
Emergency Gasoline Reserve

Emergency Gasoline Reserve is a national project that boosts Oil Refineries' production by 100% nationwide. Rates increase from 0.5/turn (per Oil Refinery) to 1/turn (per Oil Refinery). Oil usage is increased to create more Gasoline.
Fallout Shelter

Fallout Shelter is a national project that decreases damage from nukes by 10%, fallout length by 25%, and reduce food lost to radiation by 15%. Requires the Research and Development Center and Mass Irrigation National Projects to build.	
Green Technologies

Green Technologies is a national project that decreases the pollution created from Manufacturing improvements by 25%, and reduces pollution from Farms by 50%. It increases the effectiveness of subways at reducing pollution by +25, and reduces resource production upkeep costs by 10%. Requires the Space Program national project to be built first.
Government Support Agency

The Government Support Agency adds a +50% effect modifier to your chosen Domestic Policy.
Guiding Satellite

Guiding Satellite increases infrastructure damage dealt by Missiles and Nuclear Weapons by 20% as well as destroy an additional improvement. Requires the Nuclear Research Facility, Missile Launch Pad, and Space Program National Projects to build.
Intelligence Agency

Intelligence Agency is a national project that allows you to do two espionage operations per day instead of one, recruit 3 spies per day instead of 2, and increases your Spy Cap by 10, allowing you to train up to 60 spies.
International Trade Center

International Trade Center is a national project that increases the Commerce rate in each city by 1%, allows your maximum commerce rate in cities to reach 115% and increases the maximum number of Banks per city from 5 to 6.
Iron Dome

Iron Dome is a national project that gives you a 30% chance of shooting down enemy missiles and prevents 1 improvement from being destroyed by enemy missiles.
Ironworks

Ironworks is a national project that boosts Steel Mills' production by 36% nationwide. Rates increase from 0.75/turn (per Steel Mill) to 1.02/turn (per Steel Mill). Iron and Coal usages are increased to create more Steel.
Mass Irrigation

Mass Irrigation is a national project that boosts food production nationwide. Rates increase from (City Land/500) per Farm to (City Land/400) per Farm.
Military Salvage

Military Salvage is a national project that recovers 5% of lost steel and aluminum from units in a victorious attack.
Missile Launch Pad

Missile Launch Pad is a national project that allows you to build Missiles. Missiles are powerful units that damage infrastructure and improvements.
Mars Landing

Mars Landing is a national project that puts astronauts from your nation onto the Martian surface. This project does not benefit your nation competitively, but is a prestigious accomplishment for your nation's space program. Requires the Space Program and Moon Landing National Projects to build. This national project cannot be destroyed.
Moon Landing

Moon Landing is a national project that puts astronauts from your nation onto the lunar surface. This project does not benefit your nation competitively, but is a prestigious accomplishment for your nation's space program. Requires the Space Program National Project to build. This national project cannot be destroyed.
Nuclear Launch Facility

Nuclear Launch Facility is a national project that allows you to build an additional Nuclear Weapon each day. Requires the Nuclear Research Facility, Missile Launch Pad, and Space Program National Projects to build.
Nuclear Research Facility

Nuclear Research Facility is a national project that allows you to build Nuclear Weapons. Nuclear Weapons are weapons of mass destruction that damage infrastructure and improvements.
Pirate Economy

Pirate Economy is a national project that enables the nation to use an additional offensive war slot, thereby increasing the cap to 6 offensive wars, and a 5% bonus to loot from ground attacks. This national project requires the nation to have won or lost a combined 50 wars, as well as have already built the Propaganda Bureau national project.


Propaganda Bureau

Propaganda Bureau is a national project that increases your military unit recruitment rate. Propaganda Bureau increases the number of Soldiers, Tanks, Aircraft, and Ships you can recruit per day by 10%. It does not increase your caps on these units, or affect Missile, Nuclear Weapon, or Spy production.
Recycling Initiative

Recycling Initiative is a national project that buffs Recycling Center improvements throughout your nation. Each Recycling Center reduces +5 pollution (70 -> 75 each) and the maximum number of Recycling Centers per city increases from 3 to 4. Requires the Center for Civil Engineering national project to be built first.


Research and Development Center

The Research and Development Center increases your maximum National Project slots by 2.
Space Program

Space Program is a national project that enables the construction of further space-related national projects. The Space Program also allows your nation to construct an additional Missile per day. You must build the Missile Launch Pad before you can build the Space Program.


Specialized Police Training Program

The Specialized Police Training Program increases the quality and effectiveness of your city police forces. This project increases the crime reduction rate from Police Stations by 1% from 2.5% to 3.5% each. Increases commerce in all cities by 4%.
Spy Satellite

Spy Satellite is a national project that enables your nation to train an additional spy per day. It increases the damages from successful espionage operations by 50% and decreases the cost of espionage operations by 20%. Requires the Intelligence Agency and Space Program National Projects to build.
Surveillance Network

Surveillance Network is a national project that makes spy attacks against your nation 10% less likely to succeed and the attacker is 10% more likely to be identified (multiplicative). It reduces the damages received from successful espionage operations by 25% (excluding Missiles and Nuclear Weapons). Requires the Spy Satellite National Project to build.
Telecommunications Satellite

Telecommunications Satellite is a national project that increases the Commerce rate in each city by 2%, increases the maximum Commerce rate to 125% in all cities and Increases the maximum number of Malls per city increases from 4 to 5. Requires the International Trade Center, and Space Program national projects to be built first.
Uranium Enrichment Program

Uranium Enrichment Program is a national project that increases productivity of Uranium Mines. Uranium Enrichment Program doubles Uranium production in your nation.
Vital Defense System

Vital Defense System is a national project that gives you a 25% chance of thwarting enemy nuclear attacks and prevents 1 non-power plant, non-military improvement from being destroyed.


