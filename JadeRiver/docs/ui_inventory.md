# UI inventory (P2 b)

The project inventory the UI Designer Prompt asks for in its first phase (`docs/roadmap_master_ui.md` §2.2, rows
U1–U5; §3, phase P2 b). It describes the build at commit bfbb2c5 (v1.2 Phase C) as it is: the player-facing systems,
every page and shell screen with its tap regions, every HUD region, the tap paths between them, the art and UI kit,
the inconsistencies found in code and on screen, and the bugs met on the way.

Conventions:

- Paths are relative to `JadeRiver/`; `file:line` points at the line that declares the thing. Page files are in
  `scripts/ui/pages/` and are cited by file name alone (`quest_page.gd:118`).
- Pages are immediate-mode `Page` subclasses (`scripts/ui/page.gd`) that draw in `_draw`. There are no Control scenes,
  so a "node path" here is a page file and a region id. `btn()` draws a kit button and registers a tap region;
  `region()` registers an invisible one; `slot_box()` registers one when it is given an id; `list()` makes a scrolling
  area. A region's id reaches the page's `on_action(id, data)`, which submits an intent through `Game.submit()` or
  opens another page through the `navigate` signal.
- "Submits `x`" means the intent type `x`; "opens *P*" means the page id *P* registered in `scripts/main.gd:10-71`.
- Screenshots are in `docs/ui_inventory/` at 640×360 (captured at 1280×720) and are named in `code style` without the
  extension. Section 5 lists how each was taken.
- Sizes are in screen pixels of the 1280×720 canvas (`project.godot:25-30`).

---

## 1. Systems (U1)

One row per player-facing system, grouped by the authority that owns its state (`scripts/simulation/authority/`).
"Opens with" gives the entry in `data/unlocks.json` (line of its `id`), its trigger and the guided quest that
teaches it; an unlock marked *account* is judged on the account's highest realm. "Code" is the authority's intent list,
which names every action the player can take in the system.

### CombatAuthority (`combat_authority.gd:17`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Combat: attack, guard, dodge, statuses | One damage pipeline (`CombatRules`) for the player, allies and monsters; pools HP, QI, Soul, Composure, Hollowing | Win fights without being gravely wounded | `techniques.json`, `status_effects.json`, `combos.json`, `weapon_families.json`, `elements.json` | `attack` (`unlocks.json:164`, after *A Quiet River*, quest *Fists First*); `guard` (`unlocks.json:561`, Bone Forging 3); `dodge_dash` (`unlocks.json:720`, Bone Forging 5) | Progression (kill progress, mastery), World (loot on `actor_defeated`), Quests (kill objectives), Pets and Companions (allies) |
| Treasures, natal treasure, self-detonation | Artifacts fired from two HUD buttons for QI or Soul; one weapon raised as a natal treasure | Fill both Treasure buttons; raise the natal weapon | `treasures.json`, `artifacts.json` | `treasures` (`unlocks.json:1901`, Heart Tempering 1); `treasure_slot_2` (`unlocks.json:2377`, Spirit Awakening 1); `natal` (`unlocks.json:2018`, Heart Tempering 1) | Inventory (`set_treasure`), Crafting (natal feeding at the forge), HUD Treasure buttons |
| Revival | After a grave wound: return to the last shrine, or revive in place with a talisman or a fruit | Lose as little progress as possible | `talismans.json` | From the start (no penalty in the Prologue) | World (shrines, `shrines` `unlocks.json:127`, `shrine_respawn` `unlocks.json:363`), Progression (10% progress loss) |
| Flight and movement arts | QI-paid flight, glide, air dash, double jump, wall-step | Reach sky rooms and the optional "Paths Above" ledges | `movement.json`, `movement_contracts.json` | `flight` (`unlocks.json:2204`, Cloud Stride 1); `glide` (`unlocks.json:2683`); `air_dash` (`unlocks.json:2701`); `double_jump` (`unlocks.json:2719`); `wall_step` (`unlocks.json:2737`) | World (`sky_rooms` `unlocks.json:2274`), Achievements (Paths Above), Inventory (flight vessels) |

### ProgressionAuthority (`progression_authority.gd:16`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Realm ladder, meditation, breakthrough | Qi progress per stage; bottlenecks; minor and major breakthroughs with requirements, supports, risk and tribulations | Climb the realms | `realms.json`, `tribulations.json`, `failures.json`, `injuries.json` | `cultivate`, `cultivation`, `breakthrough` (`unlocks.json:246`, `unlocks.json:268`, `unlocks.json:289`; flag `night_survived`, quest *The River Token*); `bottleneck_panel` (`unlocks.json:1260`, Bone Forging 9); `stored_qi` (`unlocks.json:1278`) | Every realm-gated unlock; Calendar (heavenly phenomena); Fates; HUD progress bar and Cultivate button |
| Breakthrough fates | Three cards after a major breakthrough, a gift and usually a cost | Keep the card that suits the build | `fates.json` | After a major breakthrough (no unlock row) | HUD opens *fates* on `fate_offered` (`hud.gd:1069-1070`); Heart tab |
| Foundation (meridians) | Points into Body, Agility, Essence, Spirit, Insight | Spend points where the build needs them | `stats.json`, `realms.json` | `foundation` (`unlocks.json:401`, Bone Forging 1) | Stats (`StatRules`), Workshop and crafts (Insight) |
| Body ladder | Body level and four tiers (Copper to Gold Body), each with a Temper trial and a bath | Reach the next body tier | `body_tiers.json`, `set_pieces.json` | `body_training` (`unlocks.json:329`, Bone Forging 1); `medicinal_bath` (`unlocks.json:2034`) | Crafting (bath brewing), World (training objects), Seclusion (Temper body) |
| Methods | Cultivation methods with rate, capacity, ceiling and element | Run a method that fits the root and realm | `methods.json` | Learned from quests and shops (no unlock row) | Energy type and purity (`refine_qi` `unlocks.json:2258`) |
| Techniques and mastery | Known techniques, eight slots on two HUD pages, mastery tiers 1–6; cast through Combat | Fill the slots and raise mastery | `techniques.json` | `technique_slots_2` (`unlocks.json:1296`, Qi Kindling 1); `technique_slots_4` (`unlocks.json:1440`); `technique_slots_8` (`unlocks.json:1796`); `technique_page_2` (`unlocks.json:1649`, Qi Unfurling 1) | Combat (`use_technique`), HUD skill slots, Research (manuals) |
| Inner Arts and stances | Passive arts in up to four slots; one stance per weapon family | Wear the arts and stance for the weapon in hand | `inner_arts.json`, `stances.json` | Inner Art slots by realm (`inner_arts.json` "slots"); `stances` (`unlocks.json:1943`, Qi Kindling 5) | Combat (weapon family) |
| Dao | Insight per Dao through seven tiers; contemplation in seclusion | Deepen the Daos the build uses | `daos.json`, `curves.json` (`dao_tiers`) | `dao_tree` (`unlocks.json:1315`, Qi Kindling 1); `insight_sites`, `contemplate` (`unlocks.json:1406`, `unlocks.json:1422`, Qi Kindling 4) | Field (the Sphere's element), Crafting (weapon awakening, Alchemy Dao), Workshop (teaching) |
| Seclusion | Offline gains for one chosen focus, capped by the room | Leave each character on a useful focus | `curves.json`, room data | `seclusion` (`unlocks.json:853`, Bone Forging 7); `retreat_room` (`unlocks.json:1682`); `refine_qi` (`unlocks.json:2258`); `nourish_soul` (`unlocks.json:2428`) | Account (the Welcome back page), Workshop (Gathering Formation), Posts |
| Heart: heart demons, merit, residue, pill resistance | What the past costs at a breakthrough | Keep the heart calm and the foundation sound | `curves.json`, `stats.json` | With the Cultivation page | Relations (merit, sin), Crafting (pills) |
| Vows and paths | Vows forbid one thing for a gift; the Blood, Buddhist, Poison Body and Confucian paths | Choose the paths the build wants | `vows.json` | `vows` (`unlocks.json:1960`, Heart Tempering 1); `confucian_path` (`unlocks.json:2975`) | Relations (alignment gates), Combat (Blood path lifesteal) |
| Attunement | Jades raised with zone shards against each region's need | Meet the attunement a region asks for | `zones.json` (attunement blocks) | `storm_ward` (`unlocks.json:2866`); `starsea_endurance` (`unlocks.json:2887`) | World (region need on the map), Combat (damage dealt and taken) |
| Leisure arts: guqin and chess | A rhythm piece on the zither (meditation bonus) and a daily Go problem at insight stones (Dao insight) | Play daily | `chess.json` | The guqin item; `insight_sites` (`unlocks.json:1406`) for chess | Progression (meditation rate), Dao |
| Concealment | Shows a false realm to the world | Hide strength from NPCs | `secret_arts.json` | The Concealment secret art | HUD realm badge, NPC lines |

### WorldAuthority (`world_authority.gd:17`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Rooms, portals, objects, minimap, world map | One loaded room with portals, NPCs and objects; the scroll map per zone | Explore every room and region | `data/rooms/`, `zones.json`, `world.json`, `map_themes.json` | `move` (`unlocks.json:5`); `navigation` (`unlocks.json:43`, minimap, tracker, room banner); `world_menu` (`unlocks.json:381`, Bone Forging 1, the Map button and page) | Quests (guide target), Calendar (events on the map), Crafting (stations), every page opened by an object |
| Room hazards | Rocks, lightning, gusts, fog, heat and others: warn, strike, rest | Answer each hazard with its attribute | `hazards.json` | Per room | Progression (attributes), Combat (statuses, Hollowing) |
| Teleport stones | Travel between discovered stones for a shard | Discover every stone | `teleport_stones.json` | `teleport_stones` (`unlocks.json:1382`, Qi Kindling 3) | Inventory (Spirit Stone shards) |
| Spirit Sense and hidden portals | A Soul pulse that shows what is hidden | Find hidden ways | — | `spirit_sense` (`unlocks.json:2358`, Spirit Awakening 1); `hidden_portals` (`unlocks.json:2396`) | Combat (Soul pool), HUD Sense button |
| Trial Tower | Thirty floors with rules; cleared floors swept once a day | Climb to floor 30 | `tower.json` | A room object at the Fairground | Account (daily activity), Combat |
| Auto-hunt and auto-path | Idle hunting in allowed rooms; walking to a quest's room | Save walking and grinding | — | Auto-hunt with `idle_tasks` (`unlocks.json:757`); auto-path from the tracker | Quests (target room), presentation `Autopilot` |
| Starsea voyages | Sailing a built vessel along a charted route | Cross the Starsea | `voyages.json` | `starsea` (`unlocks.json:2797`) | Crafting (charts, vessels) |

### InventoryAuthority (`inventory_authority.gd:9`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Bag, key items, equipment, quick-use | The Spirit Gourd bag, the key-item pouch, eight worn slots, a spare weapon, quick-use and a draught slot | Wear the best gear; carry what the fight needs | `items.json`, `sets.json`, `affixes.json`, `grades.json` | `bag` (`unlocks.json:30`); `quick_use` (`unlocks.json:105`); `equipment` (`unlocks.json:207`); `weapons` (`unlocks.json:584`, Bone Forging 3); `dual_loadout` (`unlocks.json:1981`); `cape_slot` (`unlocks.json:2544`); `wardrobe` (`unlocks.json:2059`) | Economy, Crafting (forge upkeep), Combat (stats), Storage |
| Relics and artifact spirits | Sealed relics bound by a channel; a spirit woken, fed and gifted | Wake and raise the relic's spirit | `artifacts.json` | `binding` (`unlocks.json:2412`, Spirit Awakening 3) | Crafting (restore relic), Quests |

### QuestAuthority (`quest_authority.gd:26`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Quests, tracker, dialogue | Main, side, guided and daily quests; NPC dialogue with choices and services | Finish the story and the guided quests | `quests.json`, `npcs.json`, `data/dialogue/`, `set_pieces.json` | `talk` (`unlocks.json:19`); `navigation` (`unlocks.json:43`, the tracker) | Every system (each unlock names its guided quest); Relations (hearts in dialogue); pages opened by NPC services |
| Daily sect missions and the weekly mission | Missions generated each day from templates, and the week's Sect Service | Finish them for contribution and activity | `mission_templates.json`, `weekly_mission.json` | `daily_missions` (`unlocks.json:775`, Bone Forging 6) | Training sect (contribution), Account (activity points) |
| Codex | Entries learned from quests and objects | Complete the Codex | `codex.json` | `codex` (`unlocks.json:308`) | Quests, World (inspect objects) |

### EconomyAuthority (`economy_authority.gd:14`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Currencies and shops | Buy, sell, buy back; daily rotation | Afford the next upgrade | `currencies.json`, `shops.json` | `shop` (`unlocks.json:85`); `town_hub` (`unlocks.json:458`); `contribution_shop` (`unlocks.json:795`) | Inventory, Training sect (contribution) |
| Currency exchange | Each zone's clerk trades its currency with the tier below, less 20% | Move money between tiers | `currencies.json` (`exchange`, `zone_pairs`) | `currency_exchange` (`unlocks.json:2560`, Heaven Glimpse 3) | — |
| Auctions | The Nine Peaks pavilion and the valley's Saturday auction | Win rare lots | `auction.json` | `auction_house` (`unlocks.json:2578`, Sage 1 and *Nine Seats*); the valley auction on the calendar | Mail (won lots), Calendar |

### CraftingAuthority (`crafting_authority.gd:33`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Gathering: herbs, ore, fish, insects | Hold and tap at nodes; the fishing minigame | Gather the inputs of every craft | `items.json`, `fish.json`, `loot_tables.json` | `herb_gathering` (`unlocks.json:627`, Bone Forging 4); `mining` (`unlocks.json:698`); `insect_netting` (`unlocks.json:970`); `fishing` (`unlocks.json:935`, Bone Forging 8) | Posts (the same nodes), every craft |
| Cooking | Dishes that heal and lend buffs | Keep food for fights and animals | `recipes.json` | `cooking` (`unlocks.json:908`, Bone Forging 8) | Combat (buffs), Pets (feeding) |
| Alchemy | The five-screen furnace (ingredients, furnace, extraction, fusion, condensation) and the pill tribulation; experiments; auto-refine | Make high-quality pills | `recipes.json`, `herb_conflicts.json`, `items.json` | `alchemy` (`unlocks.json:1352`, Qi Kindling 2); `auto_refine` (`unlocks.json:1513`); `experiments` (`unlocks.json:1607`) | Progression (pills, toxicity, resistance), Guilds, Garden (herb age and prep) |
| Forge and upkeep | Forging from recipes; Enhance, Inherit, Salvage, Reroll, Natal, Awaken | Keep gear at +10 with good affixes | `recipes.json`, `forge_upkeep.json`, `salvage.json`, `affixes.json` | `smithing` (`unlocks.json:1718`, Qi Unfurling 2) | Inventory (gear), Dao (awakening), Combat (natal) |
| Array plates and talismans | Etched one-use formations; traced talismans | Carry plates and talismans for fights | `recipes.json`, `talismans.json` | `array_plates` (`unlocks.json:2098`); `talisman` (`unlocks.json:1999`, Qi Kindling 6) | Combat (deploy, use), Workshop (etching uses `inscribe`) |
| Guilds | Rank exams and a commission board per guild | Reach Master rank in each guild | `guilds.json` | `alchemist_guild` (`unlocks.json:1529`); `forge_guild` (`unlocks.json:1553`); `formation_guild` (`unlocks.json:1580`) | Achievements (titles), Economy (pay) |
| Herb garden and drying racks | Beds with field grades; water, soil, dew; steam or soak racks | Grow old herbs; prepare herbs | `garden.json` | `herb_garden` (`unlocks.json:1756`, Qi Unfurling 4) | Alchemy, Pets (guard role) |
| Star charts and vessels | Charts from sighting stones; vessels on a slipway | Chart the routes and build a vessel | `recipes.json`, `voyages.json` | `star_charting` (`unlocks.json:2755`); `shipwright` (`unlocks.json:2776`) (Sage 3 and *Ironroot Blood*) | World (`set_sail`) |

### WorkshopAuthority (`workshop_authority.gd:11`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Formations | Fuelled formations placed in a room | Keep a Gathering or Guard formation where you cultivate | `formations.json` | `formations` (`unlocks.json:1877`, Heart Tempering 1); `guard_formation` (`unlocks.json:2147`); `advanced_formations` (`unlocks.json:2460`) | Seclusion (cap), breakthrough risk |
| Appraisal | Identify curios and unappraised herbs | Appraise what the loupe allows | `professions.json` | `appraisal` (`unlocks.json:1475`, Qi Kindling 6); `appraisal_eye` (`unlocks.json:2620`) | Inventory |
| Infirmary | Treat patients for contribution | Treat five a day | `professions.json` | `healing` (`unlocks.json:2076`, Heart Tempering 3) | Training sect (contribution) |
| Puppetry | Worker puppets that gather; a combat puppet | Build and keep puppets | `professions.json` | `puppetry` (`unlocks.json:2306`, Cloud Stride 5) | Pets (the combat puppet takes a pet slot), gathering |
| Research | Restore damaged manuals | Recover techniques | `professions.json` | `research` (`unlocks.json:2512`, Spirit Awakening 6) | Techniques |
| Teaching | Teach your sect's disciples a Dao | Raise disciples | `daos.json` | `teaching` (`unlocks.json:2528`, Spirit Awakening 7) | Your sect |

### TrainingSectAuthority (`training_sect_authority.gd:6`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Training sect | Rank, contribution, regard, promotion trials, a role variant and a contribution tree | Rise from outer disciple to Elder | `sects.json`, `sect_ranks.json`, `sect_roles.json` | `sect_choice` (`unlocks.json:440`); `outer_rank` (`unlocks.json:677`); `core_rank` (`unlocks.json:2237`); `personal_disciple` (`unlocks.json:2444`); `elder_token` (`unlocks.json:2838`) | Quests (missions), Economy (contribution shop), Combat (signature line) |

### SectAuthority (`sect_authority.gd:8`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Your own sect | Buildings, NPC disciples, expeditions, raids to defend | Grow the sect to its top level | `sect_buildings.json`, `sect_levels.json`, `disciples.json`, `expeditions.json`, `defence.json` | `your_sect` (`unlocks.json:1700`, *account*, Qi Unfurling 1) | Account (slots), Workshop (teaching), Posts (Mirror of Echoes) |
| Territory | Spirit-stone mines taken from rival sects, guarded by disciples | Hold as many mines as the cap allows | `territory.json` | With a founded sect | World (mine rooms), Economy (spirit stones) |

### PetAuthority (`pet_authority.gd:16`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Spirit animals | Care, roles, growth stages, bloodline, contracts, skills, gear, eggs, breeding, fusion, mounts, the party | Raise strong animals and a mount | `pets.json`, `pet_growth.json`, `eggs.json`, `taming.json`, `pet_traits.json`, `pet_skill_books.json` | `spirit_animals` (`unlocks.json:1777`, Qi Unfurling 5); `taming` (`unlocks.json:1828`); `mounts` (`unlocks.json:2220`); `spirit_eggs` (`unlocks.json:2114`); `pet_breeding` (`unlocks.json:2480`); `star_beasts` (`unlocks.json:2931`) | Combat (ally), Crafting (gatherer role, cores), Garden (guard role), HUD pet strip and Pet button |
| Beast Arena and Core Exchange | A ladder of ten tamers; cores sold for Spirit Stones | Hold a high arena rank each week | `beast_arena.json`, `pet_growth.json` (cores) | Room object on Market Street; the Beast Hall NPC | Economy (spirit stones) |

### CompanionAuthority (`companion_authority.gd:9`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Companions | Up to two fellow disciples fight beside you | Keep two companions with you; raise their hearts | `companions.json`, `bonds.json` | `companions` (`unlocks.json:1456`, Qi Kindling 5); `second_companion` (`unlocks.json:2131`); `paired_cultivation` (`unlocks.json:2817`) | Relations (hearts, bonds), Combat |

### AccountAuthority (`account_authority.gd:10`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Character slots and idle tasks | Up to twelve characters; one idle task for each character left behind | Keep every slot working | `account_rules.json`, `idle_tasks.json` | Slots by account realm and sect level; `idle_tasks` (`unlocks.json:757`, *account*, Bone Forging 5) | Posts, Seclusion, the shell's selection screen |
| Shared storage | One account-wide chest | Move goods between characters | — | `storage` (`unlocks.json:1335`, *account*, Qi Kindling 1) | Inventory |
| Daily activity chests | Four chests for daily points from missions, crafts, harvests and fights | Open all four each day | `activity.json` | The Daily tab (no unlock row) | Quests, Crafting, World (tower) |
| Collection book | Kill counts per monster | Fill the book | `enemies.json` | `collection_book` (`unlocks.json:737`, Bone Forging 5) | Codex page |
| Settings and app lifecycle | Audio, controls, accessibility, save data; pause and resume | — | — | Always | HUD (left-handed), Audio, Notifier |

### MailAuthority (`mail_authority.gd:9`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Mail | One inbox; attachments kept when the bag is full | Claim everything | `mail_templates.json` | `mail` (`unlocks.json:421`, Bone Forging 1) | Economy (auction lots), Quests, overflow |

### AchievementAuthority (`achievement_authority.gd:6`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Achievements, titles, emotes, Paths Above | Counters from events; titles (+1% to a stat); emotes; ledges found | Earn titles and emotes | `achievements.json`, `titles.json`, `emotes.json`, `paths_above.json` | The Codex (`codex` `unlocks.json:308`); emotes always | Stats (titles), movement arts |

### FieldAuthority (`field_authority.gd:20`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Presence | A held aura that presses weaker foes, paid in Soul; levels 1–10 | Level the Presence | `curves.json` | `presence` (`unlocks.json:2908`, Will Manifest 1) | Combat (Pressure), vows (Silence forbids it) |
| Sphere | A circle of the strongest combat Dao's element, paid in QI | Hold the Sphere in fights | `daos.json` | `sphere` (`unlocks.json:2952`, Sphere Lord 1) | Dao, room terrain |

### PostAuthority (`post_authority.gd:10`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Keeping Post, Vigil, Storehouse | Characters not being played work a node or hunt a room; settle into the account Storehouse | Keep every idle character at a good post | `posts.json`, `fish.json` | `keeping_post` (`unlocks.json:952`, *account* Bone Forging 6, quest *Keeping Post*) | Crafting (nodes), Account (switching), the Welcome back ledger |
| Qiankun pouches | Pouch tiers per category | Sew the pouches deeper | `posts.json` (`sewing`) | `pouch_sewing` (`unlocks.json:993`) | Posts (capacity) |
| Snares, rites, Post Vows, Apprentice Bench | Timed snares, ancestral rites, vows paid in wisps, apprentices making components | Keep each running | `posts.json` | `beast_snaring` (`unlocks.json:1016`); `ancestral_rites` (`unlocks.json:1043`); `apprentice_bench` (`unlocks.json:1070`) | Posts, Storehouse |
| Works | Post Arts, Seal Scripts, Guardian Steles, Magistrate's Favours, Calcination Furnace, Formation Flags, Mirror of Echoes | Build the account web | `posts.json` | `post_arts` (`unlocks.json:1091`); `seal_scripts` (`unlocks.json:1114`); `guardian_steles` (`unlocks.json:1137`); `magistrates_favours` (`unlocks.json:1160`); `calcination` (`unlocks.json:1183`); `formation_flags` (`unlocks.json:1210`); `mirror_of_echoes` (`unlocks.json:1233`) | Storehouse goods, Your sect (Mirror), Formation Guild (Furnace) |

### CalendarAuthority (`calendar_authority.gd:10`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| World calendar, weather, world events, Heaven Ranking | Seeded schedule of events, seasons and weather; a weekly ranking of the valley's cultivators | Be where the events are; climb the ranking | `calendar.json`, `seasons.json`, `rankings.json` | The Calendar tile with `world_menu` (`unlocks.json:381`); the ranking tab on the map | World (rift, fruit, Beast Tide), Combat (weather), Crafting (herb seasons) |

### RelationsAuthority (`relations_authority.gd:13`)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Karma, alignment, Fame | Merit and sin, the righteous-demonic scale, named Fame and young masters' challenges | Keep the merit a breakthrough wants; earn Fame | `karma.json` | Always (no unlock row) | Progression (merit, heart demon, paths), HUD (challenge opens *relations*, `hud.gd:948-951`) |
| Affinity, gifts, bonds | Hearts per NPC, one gift a day, Dao Companion, sworn siblings, master | Raise hearts; form bonds | `bonds.json`, `npcs.json` (`gifts`) | NPCs with gifts | Companions, Economy (keeper discounts) |
| Grudges, bounties, mercy | Factions that hunt you; bounties on named targets; spare or finish a foe who yields | Settle grudges; take bounties | `factions.json` | Always | Combat (hunters), Notice board (bounties), HUD (`foe_surrendered` opens *mercy*, `hud.gd:851-852`) |
| Fortune encounters | A meter that turns up an encounter | Meet them | `fortune_deck.json` | Always | HUD fortune vignette |
| County (mortal kingdom) | County jobs, favour tiers, a relief fund | Reach Benefactor | `karma.json` (`mortal`) | County Hall object and clerk | Quests (county jobs), Works (Magistrate's Favours) |

### EnemyAuthority (`enemy_authority.gd:3`, no intents)

| System | Purpose | Player's goal | Data | Opens with | Connects to |
|---|---|---|---|---|---|
| Monsters, bosses, Beast Kings | Spawns, AI, boss phases, field-boss respawn timers | Beat the bosses and Kings | `enemies.json`, `beast_kings.json`, `loot_tables.json` | `field_boss_timers` (`unlocks.json:817`, Bone Forging 6); `field_bosses` (`unlocks.json:1812`) | Combat, World (loot), Codex (collection), map (boss timers) |

`GameAuthority` (`game_authority.gd`) is the facade that routes intents; it owns no player-facing system.

---
## 2. Screens (U2)

### 2.1 What every page shares

`scripts/ui/page.gd` gives every page the same frame and controls:

| Element | Declared | What it does |
|---|---|---|
| Window | `page.gd:21` (1152×656 at 64,32); modal default `page.gd:42` (700×380 at 290,170) | Dims the world (`page.gd:108`), draws the `major_window` frame |
| Title plaque | `page.gd:111-113` | 440×60, title at 34 px in Cormorant |
| Close button | `page.gd:114-117` | 52×52 region `_close`; tapping outside the window also closes (`page.gd:393`); Esc closes (`page.gd:425`) |
| Tabs | `page.gd:136-149` | 40 px high, at least 118 px wide, 6 px apart; region `_tab`; a locked tab keeps its reason and shows a lock |
| Scroll list | `page.gd:326-346` | `list(area, rect, count, row_h, draw_row)`; drag or wheel; a 4 px jade thumb |
| Confirm dialog | `page.gd:348-357` | 500×220; buttons `_confirm_no` and `_confirm_yes` (190×54) |
| Toast | `page.gd:123-128` | The reason an intent failed, for 2.4 s |

Every page opening also submits `report_page_opened` (`main.gd:700`), which guided quests count. An unknown page id
logs "coming in a later update" (`main.gd:684`).

`scripts/main.gd:10-71` registers 60 page ids over the 44 files; the aliases open a file on a tab (for example
*alchemy*, *forge*, *arrays* open `crafts_page.gd` on that tab; *seclusion*, *heart*, *body* open
`cultivation_page.gd`; *collection*, *seasons*, *achievements* open `codex_page.gd`; *library* opens `shop_page.gd`;
*formations* opens `workshop_page.gd`).

### 2.2 Pages

One subsection per file in `scripts/ui/pages/` (44), in file-name order. "Reached from" names the ways in; the tap
paths are in section 3. Sizes are width×height; a size given as a formula depends on the layout.

#### auction_page.gd — Auction Pavilion / Auction Day

Page id *auction* (`main.gd:69`). Reached from the pavilion object and the `page:auction` NPC services; the tab argument
`valley` or `args.house` shows the valley's Saturday auction (`auction_page.gd:12-14`). No tabs. Screenshots
`auction`, `auction_valley`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Lot list | `auction_page.gd:28` | rows 96 | — |
| Bid the minimum | `auction_page.gd:44` | 150×52 | `auction_bid` |
| Bid 1.5× the price | `auction_page.gd:46` | 150×52 | `auction_bid` |

#### beast_arena_page.gd — Beast Arena

Page id *beast_arena* (`main.gd:39`), window 1020×600 (`beast_arena_page.gd:10`). Reached from the arena object on
Market Street. No tabs. Screenshot `beast_arena`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Ladder list | `beast_arena_page.gd:29` | rows 52 | — |
| Challenge 1v1 / 3v3 | `beast_arena_page.gd:73` | half width × 50 | `arena_challenge` |

#### breakthrough_page.gd — Breakthrough

Page id *breakthrough* (`main.gd:15`). Reached from the HUD Cultivate button at a bottleneck (`hud.gd:406-410`) and the
Cultivation page. No tabs. Screenshot `breakthrough`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Go (fix an unmet requirement) | `breakthrough_page.gd:35` | 110×40 | opens the page the requirement names (*cultivation*, *inventory*, *techniques*, *world_map*) |
| Support item (toggle, up to 3) | `breakthrough_page.gd:46` | 66×66 | local choice |
| Break Through | `breakthrough_page.gd:54` | 226×58 | `start_breakthrough` |

#### calendar_page.gd — Calendar

Page id *calendar* (`main.gd:43`). Reached from the Menu. No tabs, no buttons. Screenshot `calendar`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| World events list | `calendar_page.gd:55` | rows 128 | — |

#### character_page.gd — Character

Page id *character* (`main.gd:13`). Reached from the HUD player panel and the Menu. Tabs Overview, Stats, Aptitude,
Titles, Attunement, Wardrobe (`character_page.gd:14-15`); the paper doll is an `Avatar` node (`character_page.gd:18-22`).
Screenshots `character`, `character_stats`, `character_aptitude`, `character_titles`, `character_attunement`,
`character_wardrobe`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Relations (Overview) | `character_page.gd:54` | 220×52 | opens *relations* |
| Title row (Titles) | `character_page.gd:76` | 600×56 | `set_title` |
| Raise jade (Attunement) | `character_page.gd:152` | card × 48 | `attune_jade` |
| Its own look / a look (Wardrobe) | `character_page.gd:103`, `:107` | 120×40 | `set_appearance` |

#### characters_page.gd — Characters

Page id *characters* (`main.gd:25`). Reached from the Menu. No tabs. Screenshot `characters`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Slot list | `characters_page.gd:17` | rows 84 | — |
| Switch | `characters_page.gd:28` | 140×50 | `_switch` → `switch_character` (`main.gd:672`) |
| Idle task (Seclusion, Train, Hunt, Gather, Rest) | `characters_page.gd:44` | panel × 50 | `set_idle_task` |

#### chess_page.gd — A Chess Problem

Page id *chess* (`main.gd:47`). Reached from an insight stone's dialogue ("Study the problem",
`world_authority.gd:615`); the site id comes in `args.site` or the tab argument (`chess_page.gd:12`). No tabs.
Screenshot `chess`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Play at A–D | `chess_page.gd:68` | half width × 56 | `solve_chess` |

#### codex_page.gd — Codex

Page ids *codex*, *collection*, *seasons*, *achievements* (`main.gd:19-21`, `:70`). Reached from the Menu. Tabs Codex,
Collection, Achievements, Paths Above, Seasons (`codex_page.gd:8-9`). Screenshots `codex`, `codex_collection`,
`codex_achievements`, `codex_paths_above`, `codex_seasons`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Entry row (Codex) | `codex_page.gd:41` | rows 48 | local selection |
| Lists (Collection, Paths Above, Achievements) | `codex_page.gd:67`, `:148`, `:166` | rows 150, 72, 72 | — |

#### companions_page.gd — Companions

Page id *companions* (`main.gd:48`). Reached from the Menu. No tabs; one card per companion with an `Avatar` portrait
(`companions_page.gd:12-25`). Screenshot `companions`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Gift | `companions_page.gd:60` | 107×46 | opens *gift* |
| Duel (3 hearts) | `companions_page.gd:61` | 107×46 | `companion_duel` |
| Ask to be Dao Companion (5 hearts) | `companions_page.gd:66` | 222×46 | `offer_bond` |
| Swear siblings (4 hearts) | `companions_page.gd:69` | 222×46 | `offer_bond` |
| Bring along / Active | `companions_page.gd:71` | 222×48 | `set_active_companions` |

#### core_exchange_page.gd — Core Exchange

Page id *core_exchange* (`main.gd:61`), window 940×580 (`core_exchange_page.gd:7`). Reached from the Beast Hall NPC
(`page:core_exchange`). No tabs. Screenshot `core_exchange`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Rest your animals | `core_exchange_page.gd:19` | 244×46 | `rest_pets` |
| Core list | `core_exchange_page.gd:29` | rows 66 | — |
| Sell one / Sell all | `core_exchange_page.gd:35`, `:36` | 140×44 | `sell_cores` |

#### county_page.gd — County Hall

Page id *county* (`main.gd:45`). Reached from the County Hall object and clerk (`page:county`). Tabs County Jobs,
Relief Fund (`county_page.gd:7`); opening it submits `county_jobs` (`county_page.gd:11`), which takes today's three
jobs. Screenshots `county`, `county_relief`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Give (Relief Fund) | `county_page.gd:85` | 170×54 | `donate_relief` |

The job cards are text only.

#### crafts_page.gd — Crafts

Page ids *crafts*, *cooking*, *alchemy*, *forge*, *arrays*, *talisman*, *guild*, *charts*, *vessels* (`main.gd:49-59`).
Reached from the Menu and from stations (pot, furnace, anvil, chart table, slipway: `world_authority.gd:603-605`) and
NPC services. Tabs Cooking, Alchemy, Forge, Arrays, Talismans, Guild, Charts, Vessels (`crafts_page.gd:6-7`, built in
`setup` at `:61-67`; Charts and Vessels stay hidden until `star_charting`). The Forge tab has six mode buttons
(Recipes, Enhance, Inherit, Salvage, Reroll, Natal); the Guild tab one button per open guild; Alchemy runs the
five-screen furnace. Screenshots `crafts`, `crafts_alchemy`, `crafts_alchemy_furnace`, `crafts_alchemy_extraction`,
`crafts_alchemy_fusion`, `crafts_alchemy_condensation`, `crafts_alchemy_tribulation`, `crafts_forge`,
`crafts_forge_enhance`, `crafts_arrays`, `crafts_talisman`, `crafts_guild`, `crafts_charts`, `crafts_vessels`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Recipe list, Experiment and ancient-recipe rows | `crafts_page.gd:164`, regions `:176`, `:184` | rows 62 | local selection |
| Forge mode ×6 | `crafts_page.gd:142` | 179×46 | local mode |
| Swap herb (Alchemy Dao 5) | `crafts_page.gd:236` | 94×40 | local substitute |
| Count − / + | `crafts_page.gd:243`, `:245` | 56×50 | local |
| Cook / Etch / Chart / Build / Write / Forge / To the furnace | `crafts_page.gd:253` | 220×58 | `cook`; `inscribe` (Arrays); `chart_route`; `build_vessel`; `trace_talisman` (untraced talismans) or starts tracing; Forge starts the strike game, then `craft_step` ×3 and `forge`; Alchemy moves to the Furnace screen |
| Queue batch (auto-refine) | `crafts_page.gd:255` | 220×58 | `queue_auto_refine` |
| Collect batches | `crafts_page.gd:598` | 200×50 | `collect_auto_refine` |
| Gear row (Forge modes) | `crafts_page.gd:282`, region `:298` | rows 62 | local choice |
| Essence − / + | `crafts_page.gd:346`, `:347` | 56×44 | local |
| Enhance / Mend / Awaken | `crafts_page.gd:349`, `:357`, `:383` | 220×58 | `enhance`; `mend_furnace`; `awaken_weapon` |
| Inherit / Clear | `crafts_page.gd:408`, `:409` | 220×58, 160×58 | `inherit_enhancement`; local |
| Salvage | `crafts_page.gd:421` | 220×58 | `salvage` |
| Lock / Unlock affix | `crafts_page.gd:444` | 140×42 | `lock_affix` |
| Keep old / Take new | `crafts_page.gd:449`, `:450` | 200×58, 220×58 | `choose_affixes` |
| Reroll | `crafts_page.gd:460` | 220×58 | `reroll_affixes` |
| Make natal / Feed ×1 / ×5 / Re-forge | `crafts_page.gd:471`, `:496`, `:497`, `:498` | 220×58, 130×44 | `flag_natal`; `feed_natal`; `reforge_natal` |
| Talisman tracing (paper) / Stop tracing | `crafts_page.gd:559-585` (input), `:518` | paper; 140×46 | `trace_talisman`; local |
| Experiment herb / Experiment | `crafts_page.gd:613`, `:623` | 96×86; 220×58 | local; `start_experiment` |
| Deduce | `crafts_page.gd:641` | 220×58 | `deduce_recipe` |
| Guild pick / Start exam | `crafts_page.gd:652`, `:689` | ≤260×46; 164×40 | local; `take_guild_exam` |
| Take order / Deliver for taels / Deliver for contribution | `crafts_page.gd:713`, `:720`, `:721` | 136×38 | `accept_commission`; `deliver_commission` |
| Fire ×4 / Array ×2 / ‹ Ingredients / Light the furnace | `crafts_page.gd:1092`, `:1101`, `:1103`, `:1105` | ×48; 200×58; 240×58 | local; local; local; `start_refine` |
| Put out the fire | `crafts_page.gd:1132`, `:1218` | 194×46, 160×46 | confirm → `cancel_refine` |
| Specks (Extraction) / Fan the flame (held) | `crafts_page.gd:1210`, `:1220` | 52×52; 250×76 | local; `refine_input` (extraction) |
| Try again (Extraction) | `crafts_page.gd:1217` | 160×46 | local |
| Orbs (Fusion) / Turn | `crafts_page.gd:1258`, `:1284` | 84×84; 250×76 | local order; `refine_input` (fusion) |
| Condense! | `crafts_page.gd:1309` | 250×76 | `refine_input` (condensation) |
| Raise shield / Catch (pill tribulation) | `crafts_page.gd:1136` | 250×72 | `tribulation_shield`; `catch_pill_soul` |

The furnace's timed controls act on press through `_gui_input` (`crafts_page.gd:559-570`), not on release.

#### cultivation_page.gd — Cultivation

Page ids *cultivation*, *seclusion*, *heart*, *body* (`main.gd:14`, `:63-65`). Reached from the HUD progress bar, a
held Cultivate button (`hud.gd:137-140`) and the Menu. Tabs Overview, Foundation, Body, Heart, Paths, Methods, Dao,
Seclusion (`cultivation_page.gd:11-18`; Foundation, Paths, Dao and Seclusion carry lock reasons). Screenshots
`cultivation`, `cultivation_foundation`, `cultivation_body`, `cultivation_heart`, `cultivation_paths`,
`cultivation_methods`, `cultivation_dao`, `cultivation_seclusion`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Meditate / Stop (Overview) | `cultivation_page.gd:78` | 220×58 | `toggle_meditation` |
| Breakthrough (Overview) | `cultivation_page.gd:80` | 230×58 | opens *breakthrough* |
| +1 per meridian (Foundation) | `cultivation_page.gd:113` | 120×44 | `open_meridian` |
| Reset (Foundation) | `cultivation_page.gd:116` | 420×52 | confirm → `reset_meridians` |
| Take the vow / Break the vow (Paths) | `cultivation_page.gd:180`, `:178` | 172×46 | `set_vow` (breaking asks first) |
| Walk it / Leave (Blood, Confucian paths) | `cultivation_page.gd:201`, `:195`, `:232`, `:226` | 128×40 | `set_path` (leaving asks first) |
| Ledger › (Heart) | `cultivation_page.gd:258` | 150×40 | opens *relations* |
| Choose your fate (Heart) | `cultivation_page.gd:274` | panel × 44 | opens *fates* |
| Methods list / Switch | `cultivation_page.gd:318`, `:327` | rows 110; 150×50 | confirm → `switch_method` |
| Daos list / Contemplate | `cultivation_page.gd:340`, `:350` | rows 76; 150×44 | `set_contemplate` |
| Focus card (Seclusion) | `cultivation_page.gd:378` | 310×112 | `enter_seclusion`; `start_bath` for the bath card |

#### dialogue_page.gd — Dialogue

Page id *dialogue* (`main.gd:27`). Opened by talking to an NPC (HUD context button → `talk`) and by objects that answer
with a dialogue. It replaces `_draw` (`dialogue_page.gd:51-56`): no window frame, a paper box 1200×204 at the bottom,
a portrait frame with an `Avatar`, a name plaque and hearts. Screenshot `dialogue` (Warden-Commander Yao).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Advance (the whole box) | `dialogue_page.gd:74` | 1200×234 | finishes the line, next line, or closes |
| Choice 1–4 | `dialogue_page.gd:84` | 370 × (≤46) | `choose_dialogue`; a shop choice opens *shop*; a page choice opens that page; an intent choice submits it (`dialogue_page.gd:111-146`) |

#### emotes_page.gd — Emotes

Page id *emotes* (`main.gd:34`), modal 600×540 (`emotes_page.gd:8`). Reached from the Menu. No tabs. Screenshot
`emotes`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Emote around the wheel | `emotes_page.gd:26` | 156×56 | `emote` |

#### exchange_page.gd — Exchange

Page id *exchange* (`main.gd:68`), modal 640×420 (`exchange_page.gd:8`). Reached from each zone's exchange object. No
tabs. Screenshot `exchange`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Pay lower for higher / higher for lower | `exchange_page.gd:30`, `:31` | 280×50 | `exchange_currency` |

#### fates_page.gd — Breakthrough Fate

Page id *fates* (`main.gd:66`), window 1040×580 (`fates_page.gd:7`). Opens by itself on `fate_offered`
(`hud.gd:1069-1070`) and from the Heart tab. No tabs. Screenshot `fates`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Take this fate ×3 | `fates_page.gd:39` | card × 56 | `choose_fate` |

#### fishing_page.gd — Fishing

Page id *fishing* (`main.gd:62`), modal 600×420 (`fishing_page.gd:19`). Opened by a fishing spot through the HUD
(`hud.gd:519-521`, `main.gd:628`). Phases wait, bite, fight, done. Screenshot `fishing` (the done phase: the bite passed untouched during the capture, so it reads "It got away.").

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Tap to strike / hold to reel | `fishing_page.gd:70`, hold in `_gui_input` `:72-75` | content | the result goes out as `catch_fish` (`fishing_page.gd:49`) |
| Again | `fishing_page.gd:67` | 200×56 | `interact` (casts again) |
| Done | `fishing_page.gd:68` | 200×56 | closes |

#### garden_page.gd — Herb Garden

Page id *garden* (`main.gd:60`). Opened by a garden bed object (`world_authority.gd:603-605`). Tabs Beds, Racks
(`garden_page.gd:13`). Screenshots `garden`, `garden_racks` (both from `cm_cave_abode` with `--garden-preview`).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Bed card | `garden_page.gd:59` | ≤360×300 | local selection |
| Seed to plant | `garden_page.gd:93` | 50×50 | `plant_seed` |
| Harvest / Water / Pour a drop of dew | `garden_page.gd:98`, `:100`, `:105` | 210×50 | `harvest_bed`; `water_bed`; `use_dew` |
| Work in Spirit Soil | `garden_page.gd:109` | 232×50 | `apply_spirit_soil` |
| Collect (Racks) | `garden_page.gd:136` | 240×48 | `collect_racks` |
| Herb / Steam / Soak / − / + | `garden_page.gd:151`, `:156`, `:160`, `:162` | 60×60; 250×48; 48×48 | local |
| Start | `garden_page.gd:167` | 240×50 | `start_rack` |

#### gift_page.gd — A Gift

Page id *gift* (`main.gd:41`), window 980×600 (`gift_page.gd:10`). Reached from an NPC's "Give a gift" choice
(`quest_authority.gd:242`) and the Companions page; the NPC id comes in `args.npc` or the tab argument
(`gift_page.gd:13`). No tabs. Screenshot `gift`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Giftable item | `gift_page.gd:65`, `:72` | 64×64 | local choice |
| Give | `gift_page.gd:78` | 210×56 | `give_gift` |

#### guqin_page.gd — The Guqin

Page id *guqin* (`main.gd:46`). Meant to open from using the guqin item (`inventory_authority.gd:860`); see "Found
while inventorying" (it cannot be opened that way). The tab argument `play` starts a piece (`guqin_page.gd:21`). No
tabs. Screenshots `guqin`, `guqin_play`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| String pegs 1–5 (press), strings | `guqin_page.gd:83-86`, input `:149-156`; keys 1–5 `:158-163` | 52×52 | local plucks; the score goes out as `play_guqin` (`guqin_page.gd:73`) |
| Play | `guqin_page.gd:141` | 240×60 | starts the piece |

#### inventory_page.gd — Bag

Page id *inventory* (`main.gd:12`). Reached from the HUD Bag button, the Menu, an empty Treasure button
(`hud.gd:539`) and the weapon swap with no spare (`hud.gd:532`). Tabs Spirit Gourd, Key Items (`inventory_page.gd:17`);
the paper doll is an `Avatar` node (`inventory_page.gd:21-25`). Screenshots `inventory`, `inventory_key`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Worn slot ×8 | `inventory_page.gd:64`, `:69` | 64×64 | local selection |
| Bag grid (6 columns) | `inventory_page.gd:77`, `:85`, `:87` | 66×66 | local selection |
| Sort | `inventory_page.gd:93` | 140×44 | `sort_bag` |
| Key item row | `inventory_page.gd:97`, `:99`, `:102` | rows 76 | local selection |
| Equip / Set as furnace | `inventory_page.gd:222` | 126×50 | `equip` |
| Set as spare | `inventory_page.gd:225` | 126×50 | `set_spare_weapon` |
| Use / Eat raw / Absorb / Bathe | `inventory_page.gd:231` | 126×50 | `use_item` (a result may open a page, `:365-367`) |
| Quick-use | `inventory_page.gd:233` | 126×50 | `set_quick_use` |
| Treasure 1 / 2 | `inventory_page.gd:239` | 126×50 | `set_treasure` |
| Lock / Discard | `inventory_page.gd:241`, `:242` | 126×46 | `lock_item`; confirm → `discard` |
| Restore relic / Appraise / Self-detonate | `inventory_page.gd:213`, `:215`, `:218` | 262×50, 262×46 | `restore_relic`; `appraise_item`; `self_detonate` (asks first) |
| Ride in flight / Stop riding (key items) | `inventory_page.gd:245` | 262×54 | `choose_vessel` |
| Unequip / Swap now / Spare out (worn slot) | `inventory_page.gd:248`, `:252`, `:253` | 262×54, 126×46 | `unequip`; `swap_loadout`; `set_spare_weapon` |
| Bind (sealed relic) | `inventory_page.gd:291` | 126×46 | `bind_item` |
| Subdue / Gift / Devour (relic spirit) | `inventory_page.gd:324` | ≤262×40 | `subdue_spirit`; `gift_spirit`; `devour_gear` |

#### mail_page.gd — Mail

Page id *mail* (`main.gd:22`). Reached from the HUD Mail button and the Menu. No tabs. Screenshot `mail`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Letter row | `mail_page.gd:22`, `:29` | rows 64 | `read_mail` |
| Claim all | `mail_page.gd:31` | 210×54 | `claim_all` |
| Claim | `mail_page.gd:49` | 200×54 | `claim_mail` |
| Delete | `mail_page.gd:50` | 160×54 | `delete_mail` |

#### map_page.gd — World map and Heaven Ranking

Page id *world_map* (`main.gd:18`). Reached from the HUD Map button, the minimap and the Menu. Tabs: one per zone the
account has visited, then Heaven Ranking (`map_page.gd:22-27`). Screenshots `world_map`, `world_map_ranking`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Region marker | `map_page.gd:120` | 60×60 | local selection (rooms, hazards, boss timers in the right panel) |
| Challenge (Heaven Ranking) | `map_page.gd:277` | 160×36 | `challenge_rank` |

#### menu_page.gd — Menu

Page id *menu* (`main.gd:11`). Reached from the HUD Menu button, Tab, and the system back button (`main.gd:751`). 21
tiles in a 7×3 grid (`menu_page.gd:5-27`), each 142×≤150; a locked tile explains its unlock on tap. Currency pills at
the foot. Screenshot `menu`.

| Tile (region `open`, `menu_page.gd:53`) | Entry | Unlock | Opens |
|---|---|---|---|
| Character | `menu_page.gd:6` | `character_menu` | *character* |
| Cultivation | `:7` | `cultivation` | *cultivation* |
| Techniques | `:8` | `technique_slots_2` | *techniques* |
| Bag | `:9` | `bag` | *inventory* |
| Quests | `:10` | `navigation` | *quests* |
| Map | `:11` | `world_menu` | *world_map* |
| Calendar | `:12` | `world_menu` | *calendar* |
| Sect | `:13` | `sect_choice` | *training_sect* |
| Your Sect | `:14` | `your_sect` | *your_sect* |
| Spirit Animals | `:15` | `spirit_animals` | *spirit_animals* |
| Companions | `:16` | `companions` | *companions* |
| Crafts | `:17` | `herb_gathering` | *crafts* |
| Workshop | `:18` | `appraisal` | *workshop* |
| Characters | `:19` | `idle_tasks` | *characters* |
| Roll-Call | `:20` | `keeping_post` | *posts* |
| Works | `:21` | `post_arts` | *works* |
| Codex | `:22` | `codex` | *codex* |
| Mail | `:23` | `mail` | *mail* |
| Emotes | `:24` | — | *emotes* |
| Settings | `:25` | — | *settings* |
| Save & Exit | `:26` | — | confirm → `_exit` (back to character selection, `main.gd:659`) |

#### mercy_page.gd — Mercy

Page id *mercy* (`main.gd:42`), modal 680×400 (`mercy_page.gd:8`). Opens by itself when a named foe yields
(`hud.gd:851-852`) or from the context button beside one (`hud.gd:495-497`). No tabs. Screenshot `mercy`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Spare them / Finish it | `mercy_page.gd:22`, `:23` | 284×58 | `judge_foe` |

#### notice_page.gd — Notice Board

Page id *notice_board* (`main.gd:35`). Reached from board objects and the Training Sect's Missions button. Tabs Board,
Bounties (`notice_page.gd:7`). The Board tab is text only (today's missions and nearby requests). Screenshots
`notice_board`, `notice_board_bounties`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Take the bounty | `notice_page.gd:62` | 230×54 | `take_bounty` |

#### pets_page.gd — Spirit Animals

Page id *spirit_animals* (`main.gd:38`). Reached from the HUD Pet button (tap), the pet strip, the pet wheel's Pet Bag
and the Menu. Tabs Care, Growth (`pets_page.gd:11`). A construct (the combat puppet) shows the same panel on both tabs
(`pets_page.gd:72-75`). Screenshots `spirit_animals`, `spirit_animals_growth`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Animal row | `pets_page.gd:24`, `:32` | rows 70 | local selection |
| Lock / Unlock | `pets_page.gd:63` | 99×38 | `lock_pet` |
| Rename / Save name (with a `LineEdit`, `:395-403`) | `pets_page.gd:70`, `:68` | 99×38 | `rename_pet` |
| Role ×3–5 (Care) | `pets_page.gd:118` | share × 46 | `set_pet_role` |
| Set active / Rest | `pets_page.gd:124`, `:91` | third × 50 | `set_active_pet` |
| Beside you / Send home | `pets_page.gd:135`, `:96` | third × 50 | `set_party` |
| Carry / Unpack | `pets_page.gd:128` | third × 50 | `set_pet_bag` |
| Food / own-element core | `pets_page.gd:143`, `:149` | 60×60 | `feed_pet`; `devour_core` |
| Breed with (two partners) | `pets_page.gd:296` | half × 44 | `breed` |
| Hatch / Infuse ×3 (eggs) | `pets_page.gd:310`, `:325` | ≤120×46; third × 44 | `hatch_egg`; `incubate_input` |
| Evolve / branch / Break Through… | `pets_page.gd:349`, `:344`, `:347` | column × 46/42 | `evolve_pet`; the last goes to the Growth tab |
| Contract (Growth) | `pets_page.gd:190` | 180×30 | `offer_contract` |
| Fuse… / Cancel | `pets_page.gd:196`, `:266` | 110×28; 140×44 | local fusion picker |
| Gear slot / pet gear / skill book | `pets_page.gd:216`, `:224`, `:229` | 52×52 | `unequip_pet`; `equip_pet`; `learn_skill_book` |
| Support item / Break Through (Growth) | `pets_page.gd:243`, `:246` | 44×44; 170×44 | local; `pet_breakthrough` |
| Fuse (picker row) | `pets_page.gd:256`, `:262` | rows 52; 130×38 | confirm → `fuse_pets` |

#### posts_page.gd — Roll-Call

Page id *posts* (`main.gd:29`). Reached from the Menu (Roll-Call) and the HUD Keep Post chip (`hud.gd:475-481`). Tabs
Roll-Call, Crafts, Storehouse, Bench, Vows (`posts_page.gd:10-12`). Screenshots `posts`, `posts_crafts`,
`posts_store`, `posts_bench`, `posts_vows`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Keep vigil | `posts_page.gd:35` | 250×52 | `take_vigil` |
| Settle all | `posts_page.gd:37` | 240×52 | `settle_all` |
| Character row | `posts_page.gd:39` | rows 104 | — |
| Switch / Incense / Settle | `posts_page.gd:73`, `:76`, `:78` | 136×40 | `_switch` → `switch_character`; `burn_incense`; `settle_post` then `send_to_storehouse` |
| Auto-Settle / Granary Seal (Storehouse) | `posts_page.gd:263`, `:267` | 240×48, 250×48 | `set_post_option` |
| Storehouse cell | `posts_page.gd:276`, `:282` | 90×90 | `withdraw_storehouse` (50 at a time) |
| Collect (Bench) / point ×3 / Change | `posts_page.gd:195`, `:200`, `:215` | 240×52; 200×44; 154×48 | `bench_collect`; `bench_point`; `bench_assign` |
| Learn / Hold / Drop (Vows) | `posts_page.gd:247`, `:251`, `:249` | 180×48 | `learn_post_vow`; `pledge_post_vow` |

#### pouches_page.gd — Qiankun Pouches

Page id *pouches* (`main.gd:30`), modal 1000×640 (`pouches_page.gd:12`). Reached from Tailor Xun (`page:pouches`). No
tabs. Screenshot `pouches`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Sew (per category) | `pouches_page.gd:42` | 106×48 | `sew_pouch` |

#### quest_page.gd — Quests

Page id *quests* (`main.gd:17`). Reached from the HUD tracker, L and the Menu. Tabs Main, Side, Daily, Done
(`quest_page.gd:8`). Screenshots `quests`, `quests_side`, `quests_daily`, `quests_done`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Quest row | `quest_page.gd:67`, `:77` | rows 62 | local selection |
| Track / Untrack | `quest_page.gd:118` | 200×52 | `track_quest` |
| Abandon (side and daily) | `quest_page.gd:120` | 200×52 | confirm → `abandon_quest` |
| Activity chest ×4 (Daily) | `quest_page.gd:165` | 48×46 | `claim_activity_chest` |

#### relations_page.gd — Relations

Page id *relations* (`main.gd:40`). Reached from the Character page, the Heart tab's Ledger and a young master's
challenge (`hud.gd:948-951`). Tabs Karma, Bonds, Grudges, Fame (`relations_page.gd:11-12`). Screenshots `relations`,
`relations_bonds`, `relations_grudges`, `relations_fame` (Karma's Named Debts show "Debt Dou Rescue": B24).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Recent deeds / friends / grudges lists | `relations_page.gd:81`, `:168`, `:190` | rows 36, 38, 96 | — |
| Pay blood money / Duel (Grudges) | `relations_page.gd:205`, `:208` | 216×56 | `pay_grudge` |
| Accept / Decline (Fame) | `relations_page.gd:270`, `:271` | half × 54 | `answer_challenge` |

#### revival_page.gd — Gravely Wounded

Page id *revival* (`main.gd:32`), modal 680×500 (`revival_page.gd:8`). Opens by itself on `player_gravely_wounded`
(`main.gd:741`); closing it returns to the shrine (`revival_page.gd:43-45`). No tabs. Screenshot `revival` (its shrine name, "Tf Tidebreak Bastion", and the 150,645 s talisman wait come from the checkpoint, see §5).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Return to the shrine | `revival_page.gd:23` | 544×62 | `choose_revival` |
| Revive here | `revival_page.gd:25` | 544×58 | `choose_revival` |
| Eat an Evergreen Heart fruit | `revival_page.gd:35` | 544×58 | `choose_revival` |

#### settings_page.gd — Settings

Page id *settings* (`main.gd:26`). Reached from the Menu and the title screen (`main.gd:556-560`). Tabs Audio,
Controls, Accessibility, Data (`settings_page.gd:14`). Screenshots `settings`, `settings_controls`,
`settings_access`, `settings_data`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Volume step ×11 per slider (Audio) | `settings_page.gd:32`, `:36` | 48×36 | `set_setting` |
| Toggle (Controls, Accessibility) | `settings_page.gd:89`, `:92` | 110×44 | `set_setting` |
| Text size Small / Normal / Large | `settings_page.gd:46` | 140×50 | `set_setting` |
| Save now / Export save / Export log (Data) | `settings_page.gd:55`, `:56`, `:57` | 240×54 | local calls (`Game.save_all`, `Game.export_save`, `Saves.export_log`) |
| Restore an export | `settings_page.gd:65` | 180×46 | confirm → `_import` (`main.gd:662`) |

#### shop_page.gd — Shop and Library

Page ids *shop*, *library* (`main.gd:23`, `:67`). Reached from NPC Trade choices, the `shop_opened` event
(`main.gd:743`), the Training Sect's Sect Shop button and library objects. Tabs Buy, Sell, Buy Back
(`shop_page.gd:12`). Screenshots `shop`, `shop_sell`, `shop_buyback`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Stock row | `shop_page.gd:38`, `:45` | rows 76 | local selection |
| − / + / ×10 | `shop_page.gd:59`, `:61`, `:62` | 60×52, 80×52 | local quantity |
| Buy | `shop_page.gd:66` | 200×56 | `buy` |
| Bag row (Sell) | `shop_page.gd:75`, `:83` | rows 70 | local selection |
| Sell one / Sell all | `shop_page.gd:93`, `:94` | panel × 54 | `sell` |
| Buy back | `shop_page.gd:101`, `:107` | rows 70; 210×48 | `buyback` |

#### storage_page.gd — Storage

Page id *storage* (`main.gd:24`). Reached from storage chests and NPC services. No tabs. Screenshot `storage`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Bag cell / storage cell (7 columns, lists at `storage_page.gd:23`) | `storage_page.gd:30` | 64×64 | `deposit`; `withdraw` |

#### techniques_page.gd — Techniques

Page id *techniques* (`main.gd:16`). Reached from the Menu. Tabs Combat, Inner Arts, Secret Arts
(`techniques_page.gd:10-11`). Screenshots `techniques`, `techniques_inner`, `techniques_secret`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Technique slot ×8 (Combat) | `techniques_page.gd:112`, `:116` | 80×80 | `equip_technique` (after picking) or `unequip_technique` |
| Technique row / Rank up | `techniques_page.gd:125`, `:139`, `:138` | rows 96; 104×40 | local pick; `rank_up_technique` |
| Inner Art slot ×4 / art row | `techniques_page.gd:39`, `:52`, `:59` | 236×70; rows 64 | `equip_inner_art` |
| Stance Take / Held | `techniques_page.gd:73` | 100×38 | `set_stance` |
| False realm (Concealment, Secret Arts) | `techniques_page.gd:101` | ≥120×40 | `set_false_realm` |

#### teleport_page.gd — Teleport Stones

Page id *teleport* (`main.gd:33`), modal 680×500 (`teleport_page.gd:7`). Opened by touching a teleport stone
(`world_authority.gd:578`). No tabs. Screenshot `teleport`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Stone ×10 | `teleport_page.gd:22` | 624 × (row gap − 8) | `teleport` |

#### tower_page.gd — Trial Tower

Page id *tower* (`main.gd:44`). Reached from the tower object at the Fairground. No tabs. Screenshot `tower` (Tester has cleared no floor; see B25).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Floor row | `tower_page.gd:27`, `:38` | rows 58 | local selection |
| Sweep cleared floors | `tower_page.gd:43` | 388×58 | `sweep_floor` |
| Climb / Climb again | `tower_page.gd:68` | panel × 60 | `climb_tower` |

#### training_sect_page.gd — Sect

Page id *training_sect* (`main.gd:36`). Reached from the Menu and NPCs' Missions service (`quest_authority.gd:232`).
Tabs Rank, Role (`training_sect_page.gd:11-12`; Role locks below the role rank). Screenshots `training_sect`,
`training_sect_role` (Tester is Sect Master, so no Promotion trial shows), and `training_sect_ae_end` (checkpoint `ae_end`,
Tester as an Elder: the Promotion trial button under Missions, B5).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Promotion trial | `training_sect_page.gd:45` | 220×46 | `take_promotion_trial` |
| Sect shop | `training_sect_page.gd:47` | 230×56 | opens *shop* |
| Missions | `training_sect_page.gd:48` | 230×56 | opens *notice_board* |
| Choose variant (Role) | `training_sect_page.gd:75` | 136×40 | `set_sect_role` |
| Buy tree node (Role) | `training_sect_page.gd:109` | 78×28 | `buy_sect_node` |

#### welcome_page.gd — Welcome Back

Page id *welcome* (`main.gd:28`), modal 760×560 (`welcome_page.gd:7`). Opens by itself when entering or resuming with
gains (`main.gd:609`, `:680`, `:775`). No tabs. Screenshot `welcome`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| To the Storehouse / Keep in the pouch | `welcome_page.gd:57`, `:58` | 250×58 | `send_to_storehouse`; closes |
| Collect | `welcome_page.gd:60` | 240×58 | closes |

#### works_page.gd — Works

Page id *works* (`main.gd:31`). Reached from the Menu. Tabs Arts, Seals, Steles, Favours, Furnace, Flags, Mirror
(`works_page.gd:9-12`); a locked tab shows its reason in the body (`works_page.gd:30-35`). Screenshots `works`,
`works_seals`, `works_steles`, `works_favours`, `works_furnace`, `works_flags`, `works_mirror`: the checkpoint character
has not opened Post Arts or any of the six works, so every tab shows its locked state (the Menu tile is locked too).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Forget all (reset) / Learn (Arts) | `works_page.gd:53`, `:70` | 230×50; 154×50 | `reset_post_arts`; `learn_post_art` |
| Inscribe (Seals) | `works_page.gd:102` | 154×50 | `inscribe_seal` |
| Raise (Steles) | `works_page.gd:134` | 154×50 | `raise_stele` |
| Seek (Favours) | `works_page.gd:161` | 174×54 | `seek_favour` |
| Light / Bank the line; Refine (Furnace) | `works_page.gd:191`, `:192` | 160×50; 154×50 | `calcine_line`; `refine_line` |
| Plant plain / deep; Raise; Uproot (Flags) | `works_page.gd:205`, `:206`, `:226`, `:227` | 220×52; 150×50; 154×50 | `plant_flag`; `raise_flag`; `uproot_flag` |
| Inscribe an echo (Mirror) | `works_page.gd:262` | 234×52 | `echo_inscribe` |

#### workshop_page.gd — Workshop

Page ids *workshop*, *formations* (`main.gd:53-54`). Reached from the Menu and many NPC services (`page:workshop`); the
NPC picks the tab (`workshop_page.gd:8-10`). Tabs Formations, Appraisal, Infirmary, Puppets, Research, Teaching (built
in `setup`, `workshop_page.gd:17-19`, each locked until its system). Screenshots `workshop`, `workshop_appraisal`,
`workshop_healing`, `workshop_puppetry`, `workshop_research`, `workshop_teaching`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Blueprint list / Place | `workshop_page.gd:55`, `:64` | rows 128; 144×50 | `place_formation` |
| Dispel | `workshop_page.gd:81` | 106×46 | `remove_formation` |
| Appraise | `workshop_page.gd:101` | 96×46 | `appraise_item` |
| Treat a patient | `workshop_page.gd:117` | 260×56 | `treat_patient` |
| Build / Repair / Collect (Puppets) | `workshop_page.gd:137`, `:152`, `:158` | 144×48; 150×44; 220×54 | `build_puppet`; `repair_puppet`; `collect_puppets` |
| Restore (Research) | `workshop_page.gd:173` | 240×56 | `restore_manual` |
| Disciple list / Teach | `workshop_page.gd:187`, `:191` | rows 64; 136×48 | `teach_disciple` |

#### your_sect_page.gd — Your Sect

Page id *your_sect* (`main.gd:37`). Reached from the Menu and the sect's objects and the mine dialogue
(`sect_authority.gd:499`). Tabs Buildings, Disciples, Expeditions, Territory (`your_sect_page.gd:9-10`). Before the sect
is founded the page shows a name field (a `LineEdit` at a fixed 440,300, `your_sect_page.gd:14-22`) and Found.
Screenshots `your_sect`, `your_sect_disciples`, `your_sect_expeditions`, `your_sect_territory` (the checkpoint
character's sect, founded at level 1; the Found state is not captured).

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Found (unfounded) | `your_sect_page.gd:32` | 200×56 at 540,380 | `found_sect` |
| Building list / Build or Upgrade / Repair | `your_sect_page.gd:38`, `:50`, `:46` | rows 70; 150×48 | `upgrade_building`; `repair_building` |
| Recruit | `your_sect_page.gd:65` | 160×44 | `recruit_disciple` |
| Send for N hours | `your_sect_page.gd:75` | 90×40 | `send_expedition` |
| Collect expedition | `your_sect_page.gd:81` | 160×40 | `collect_expedition` |
| Mine list / Collect / Post a guard / Recall / Go | `your_sect_page.gd:94`, `:123`, `:126`, `:129`, `:130`, `:135` | rows 104; 150×42 | `collect_mine`; `guard_mine`; `auto_path` (closes) |

### 2.3 Shell screens (`scripts/shell/`)

`shell_screens.gd` holds three frameless pages drawn over the river backdrop; `notifier.gd` is the `Notifier` autoload
(local notifications, at most three a day, `notifier.gd:8-21`) and has no screen.

**Title** (`shell_screens.gd:9-33`; shown by `main.gd:548`). Screenshot `shell_title`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Continue / Begin | `shell_screens.gd:25` | 300×64 | character selection, or the creator when there are no characters (`main.gd:556-559`) |
| Settings | `shell_screens.gd:26` | 300×56 | opens *settings* |
| Quit (desktop only) | `shell_screens.gd:28` | 300×56 | saves and quits (`main.gd:647`) |

**Character selection** (`shell_screens.gd:36-131`; `main.gd:564`). Four 256×420 cards per page, three pages for
twelve slots. Screenshot `shell_selection`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| Character card (tap twice to enter) | `shell_screens.gd:92` | 256×420 | selects; enters (`enter_character`, `enter_world`, `main.gd:594-604`) |
| Empty slot | `shell_screens.gd:96` | 256×420 | opens the creator |
| ◀ / ▶ page | `shell_screens.gd:106`, `:107` | 56×72 | local page |
| Enter World | `shell_screens.gd:111` | 350×64 | `enter_character`, `enter_world` |
| Delete | `shell_screens.gd:112` | 170×48 | confirm → `delete_character` |
| ‹ Title | `shell_screens.gd:113` | 150×48 | the title screen |

**Create Disciple** (`shell_screens.gd:134-275`; `main.gd:574`). A name `LineEdit` at 820,128 (`shell_screens.gd:164-174`)
and an `Avatar` preview. Screenshot `shell_creator`.

| Region | Declared | Size | Submits / opens |
|---|---|---|---|
| ◀ / ▶ for Hair, Robe, Trousers, Shoes, Origin | `shell_screens.gd:230`, `:232` | 52×46 | local |
| Hair dye ×6 | `shell_screens.gd:237`, `:240` | 50×42 | local |
| Skip the Prologue | `shell_screens.gd:249` | 420×38 | local |
| ‹ Back / Randomize | `shell_screens.gd:250`, `:251` | 150×54, 170×54 | selection or title; local |
| Begin | `shell_screens.gd:252` | 300×60 | `create_character` |

### 2.4 HUD regions (`scripts/hud.gd`)

The HUD is one `Control` that draws in `_draw` (`hud.gd:1367`) and hit-tests touches itself in `role_at`
(`hud.gd:211-241`, tested in that order). Every element stays hidden until its `hud:<element>` reveal
(`hud.gd:107-108`, `data/unlocks.json` "reveals"); positions are the S24 table (`hud.gd:25-42`), mirrored for
left-handed play (`hud.gd:94-102`). Screenshots `hud_rest`, `hud_fight`, `hud_tracker`, `hud_pet_wheel`.

Tap regions (28):

| # | Region | Hit test | Drawn | Size | Revealed by | Submits / opens |
|---|---|---|---|---|---|---|
| 1 | Joystick (left half) | `hud.gd:240` | `hud.gd:1422-1424` | half screen | `move` | moves the player (LocalAuthority) |
| 2 | Attack / context | `hud.gd:212` | `hud.gd:1717-1732` | r 74 (ring 66) | `attack` | `basic_attack` (`player.gd:173`), `plunge`; beside an object `interact` (talk, gather, open, stations, pages); held with a flute `channel_melody`; the harvest ring's `complete_node` |
| 3 | Jump | `hud.gd:213` | `hud.gd:1738` | r 36 | `jump` | jump, `start_flight`, `glide` (`player.gd:97-160`) |
| 4 | Cultivate | `hud.gd:214` | `hud.gd:1741-1747` | r 36 | `cultivate` | tap `toggle_meditation`, or opens *breakthrough* at a bottleneck (`hud.gd:406-410`); hold 0.6 s opens *cultivation* (`hud.gd:137-140`) |
| 5 | Spirit Sense | `hud.gd:215` | `hud.gd:1748` | r 36 | `spirit_sense` | `sense_pulse` |
| 6 | Presence | `hud.gd:216` | `hud.gd:1756-1760` | r 30 | `presence` | `toggle_presence` |
| 7 | Sphere | `hud.gd:217` | `hud.gd:1761-1764` | r 30 | `sphere` | `toggle_sphere` |
| 8 | Quick-use | `hud.gd:218` | `hud.gd:1765-1778` | r 30 | `quick_use` | `use_quick` |
| 9 | Draught | `hud.gd:219` | `hud.gd:1779-1786` | r 22 | a fresh liquid medicine | `drink_draught` |
| 10 | Pet (tap / hold for the wheel) | `hud.gd:220` | `hud.gd:1787-1789`, wheel `hud.gd:389-404` | r 30; wheel r 152 | `spirit_animals` | tap opens *spirit_animals*; the wheel sends `pet_command`, `set_mount` or opens *spirit_animals* (`hud.gd:381-387`) |
| 11 | Guard / Dodge | `hud.gd:221` | `hud.gd:1830-1834` | r 30 | `guard` | `guard_start`, `guard_end`; a tap `dodge` |
| 12 | Fight context (Climb / Enter) | `hud.gd:222` | `hud.gd:1826-1829` | r 30 | a ladder or portal in reach while a foe is aggroed | climb, portal |
| 13 | Keep Post chip | `hud.gd:223` | `hud.gd:1751-1755` | r 30 | `keeping_post`, beside a node | `take_post`, then opens *posts* |
| 14 | Treasure 1 | `hud.gd:224-225` | `hud.gd:1790-1815` | r 30 | `treasures` | `use_treasure`; empty opens *inventory* |
| 15 | Treasure 2 | `hud.gd:224-225` | `hud.gd:1790-1815` | r 30 | `treasure_slot_2` | as above |
| 16 | Weapon swap | `hud.gd:226` | `hud.gd:1816-1825` | r 30 | `dual_loadout` | `swap_loadout`; no spare opens *inventory* |
| 17 | Skill slots ×4 (two pages) | `hud.gd:227-228` | `hud.gd:1734-1737`, `:1314-1357` | r 43 | `technique_slots_2` | `use_technique` (`player.gd:192`); a vertical swipe turns the page |
| 18 | Minimap | `hud.gd:229` | `hud.gd:1601-1698` | 232×140 | `navigation` | opens *world_map* |
| 19 | Menu | `hud.gd:230-231` | `hud.gd:1377-1382` | r 27 | `menu` | opens *menu* |
| 20 | Bag | `hud.gd:230-231` | `hud.gd:1377-1382` | r 27 | `bag` | opens *inventory* |
| 21 | Map | `hud.gd:230-231` | `hud.gd:1377-1382` | r 27 | `world_menu` | opens *world_map* |
| 22 | Mail (red dot when unread) | `hud.gd:230-231` | `hud.gd:1377-1382` | r 27 | `mail` | opens *mail* |
| 23 | Pet strip: active / bag / mount | `hud.gd:232-233` | `hud.gd:1446-1465` | r 24 / 18 / 20 | `spirit_animals` | opens *spirit_animals*; `swap_pet_from_bag`; `set_mount` |
| 24 | Player panel (portrait, bars, realm) | `hud.gd:234` | `hud.gd:1467-1529` | 360×104 (120 with Soul) | `quick_use` (panel, HP); `qi_pool`; `spirit_sense` (Soul) | opens *character* |
| 25 | Tracker auto-path button | `hud.gd:235-236` | `hud.gd:1556-1563` | 30×22 (hit 42×34) | `navigation` | `auto_path` |
| 26 | Auto-hunt toggle | `hud.gd:237` | `hud.gd:1384-1389` | r 27 | `idle_tasks`, rooms that allow it | `set_auto_hunt` |
| 27 | Quest tracker | `hud.gd:238` | `hud.gd:1534-1576` | 300×150 | `navigation` | opens *quests* |
| 28 | Progress bar | `hud.gd:239` | `hud.gd:1836-1845` | 1280×16 hit, 8 drawn | `cultivate` | opens *cultivation* |

Display regions (15):

| # | Region | Drawn | Shows |
|---|---|---|---|
| 29 | Currency pill | `hud.gd:1390-1406` | Silver taels and Spirit Stones (`shop` reveals `hud:currency`) |
| 30 | Status icons | `hud.gd:1501-1520` | Injuries, stability, toxicity, Hollowing, heart demon, buffs, statuses (up to 12) |
| 31 | System log | `hud.gd:1847-1853` | The last five lines (`loot` reveals `hud:system_log`) |
| 32 | Room banner | `hud.gd:1855-1861` | Room name on entry |
| 33 | Sound captions | `hud.gd:662-667` | Captions for sound-only cues (Settings) |
| 34 | Toasts | `hud.gd:1888-1899` | Unlocks, quests, danger (three at a time) |
| 35 | Fortune vignette | `hud.gd:1864-1886` | A fortune encounter's card for 9 s |
| 36 | Boss bar | `hud.gd:1901-1912` | The room boss's HP, name and level |
| 37 | Room event panel | `hud.gd:1914-1942` | A rite, trial, siege or tower floor: time left and its rule |
| 38 | Tribulation panel | `hud.gd:1944-1957` | Bolts struck and to come |
| 39 | Run banner | `hud.gd:1578-1599` | A chase or timed route's seconds |
| 40 | Harvest tap ring | `hud.gd:1700-1714` | The shrinking ring and its gold band |
| 41 | Pet command wheel | `hud.gd:389-404` | Six commands while the Pet button is held |
| 42 | Prologue joystick hint | `hud.gd:1425-1426` | "Drag on the left half of the screen to move" for 12 s |
| 43 | Perfect / miss label | `hud.gd:1419-1421` | The harvest tap's grade |

`_draw_legacy` (`hud.gd:1959-1970`) draws a minimal panel when no character is bound (engine tests only) and is not
counted. Keyboard equivalents are in `hud.gd:570-625` (Tab, I/B, M, L, E, P open pages; C, K, Q, V, G, H, O, R, Z, X,
1–8 act).

---
## 3. Navigation map (U3)

Taps from the HUD at rest, counting every tap (a tab is a tap). The shortest HUD path comes first; other ways in are in
the last column. "World" means the page is opened by walking to an object or NPC and pressing the context button
(1 tap), sometimes followed by a dialogue choice (2). "Event" means it opens by itself. The HUD buttons are
`hud.gd:229-239`; the Menu tiles `menu_page.gd:6-26`; keyboard shortcuts `hud.gd:610-615`.

| Page · tab | Shortest path from the HUD | Taps | Also |
|---|---|---|---|
| Menu | Menu (1) | 1 | Tab; system back (`main.gd:751-756`) |
| Bag · Spirit Gourd | Bag (1) | 1 | Menu → Bag (2); I or B; empty Treasure button (1); Weapon swap with no spare (1) |
| Bag · Key Items | Bag (1) → Key Items (2) | 2 | |
| Character · Overview | Player panel (1) | 1 | Menu → Character (2) |
| Character · Stats, Aptitude, Titles, Attunement, Wardrobe | Player panel (1) → tab (2) | 2 | |
| Relations · Karma | Player panel (1) → Relations (2) | 2 | Progress bar → Heart → Ledger (3); event: a young master's challenge opens Fame |
| Relations · Bonds, Grudges, Fame | Player panel (1) → Relations (2) → tab (3) | 3 | |
| Cultivation · Overview | Progress bar (1) | 1 | Hold Cultivate 0.6 s (1); P; Menu → Cultivation (2) |
| Cultivation · Foundation, Body, Heart, Paths, Methods, Dao, Seclusion | Progress bar (1) → tab (2) | 2 | World: bath station opens Seclusion (1) |
| Breakthrough | Cultivate at a bottleneck (1) | 1 | Progress bar → Breakthrough (2) |
| Fates | Progress bar (1) → Heart (2) → Choose your fate (3) | 3 | Event: `fate_offered` |
| Techniques · Combat | Menu (1) → Techniques (2) | 2 | |
| Techniques · Inner Arts, Secret Arts | Menu (1) → Techniques (2) → tab (3) | 3 | |
| Quests · Main | Tracker (1) | 1 | L; Menu → Quests (2) |
| Quests · Side, Daily, Done | Tracker (1) → tab (2) | 2 | |
| World map · the zone you are in | Map (1) | 1 | Minimap (1); M; Menu → Map (2) |
| World map · other zones, Heaven Ranking | Map (1) → tab (2) | 2 | |
| Calendar | Menu (1) → Calendar (2) | 2 | |
| Codex · Codex | Menu (1) → Codex (2) | 2 | |
| Codex · Collection, Achievements, Paths Above, Seasons | Menu (1) → Codex (2) → tab (3) | 3 | |
| Mail | Mail (1) | 1 | Menu → Mail (2) |
| Sect · Rank | Menu (1) → Sect (2) | 2 | World: NPC → Missions (2) |
| Sect · Role | Menu (1) → Sect (2) → Role (3) | 3 | |
| Shop · Buy (sect shop) | Menu (1) → Sect (2) → Sect shop (3) | 3 | World: NPC → Trade (2); event `shop_opened` |
| Shop · Sell, Buy Back | Menu (1) → Sect (2) → Sect shop (3) → tab (4) | 4 | World: NPC → Trade (2) → tab (3) |
| Notice Board · Board | Menu (1) → Sect (2) → Missions (3) | 3 | World: board (1) |
| Notice Board · Bounties | Menu (1) → Sect (2) → Missions (3) → Bounties (4) | 4 | World: board (1) → Bounties (2) |
| Your Sect · Buildings | Menu (1) → Your Sect (2) | 2 | World: sect objects (1); mine dialogue → Territory (2) |
| Your Sect · Disciples, Expeditions, Territory | Menu (1) → Your Sect (2) → tab (3) | 3 | |
| Spirit Animals · Care | Pet (1) | 1 | Pet strip (1); E; Menu → Spirit Animals (2) |
| Spirit Animals · Growth | Pet (1) → Growth (2) | 2 | |
| Spirit Animals · Growth · fusion picker | Pet (1) → Growth (2) → Fuse… (3) | 3 | |
| Companions | Menu (1) → Companions (2) | 2 | |
| Gift | Menu (1) → Companions (2) → Gift (3) | 3 | World: NPC → Give a gift (2) |
| Crafts · Cooking | Menu (1) → Crafts (2) | 2 | World: stations open their tab (1) |
| Crafts · Alchemy, Forge, Arrays, Talismans, Guild, Charts, Vessels | Menu (1) → Crafts (2) → tab (3) | 3 | World: furnace, anvil, chart table, slipway (1); NPC services (2) |
| Crafts · Forge · Enhance, Inherit, Salvage, Reroll, Natal | Menu (1) → Crafts (2) → Forge (3) → mode (4) | 4 | World: anvil (1) → mode (2) |
| Crafts · Guild · a second or third guild | Menu (1) → Crafts (2) → Guild (3) → guild (4) | 4 | World: a guild master (2) opens on their guild |
| Crafts · Alchemy · Furnace screen | Menu (1) → Crafts (2) → Alchemy (3) → recipe (4) → To the furnace (5) | 5 | World: furnace (1) → recipe (2) → To the furnace (3) |
| Crafts · Alchemy · Extraction, Fusion, Condensation | … → Light the furnace (6) | 6 | They follow in play |
| Workshop · Formations | Menu (1) → Workshop (2) | 2 | World: NPC service opens the NPC's tab (2) |
| Workshop · Appraisal, Infirmary, Puppets, Research, Teaching | Menu (1) → Workshop (2) → tab (3) | 3 | |
| Characters | Menu (1) → Characters (2) | 2 | |
| Roll-Call · Roll-Call | Menu (1) → Roll-Call (2) | 2 | Keep Post chip at a node (1) |
| Roll-Call · Crafts, Storehouse, Bench, Vows | Menu (1) → Roll-Call (2) → tab (3) | 3 | Altar dialogue → Post Vows (2) |
| Works · Arts | Menu (1) → Works (2) | 2 | |
| Works · Seals, Steles, Favours, Furnace, Flags, Mirror | Menu (1) → Works (2) → tab (3) | 3 | |
| Emotes | Menu (1) → Emotes (2) | 2 | |
| Settings · Audio | Menu (1) → Settings (2) | 2 | Title → Settings (1) |
| Settings · Controls, Accessibility, Data | Menu (1) → Settings (2) → tab (3) | 3 | |
| Save & Exit | Menu (1) → Save & Exit (2) → Confirm (3) | 3 | |
| Dialogue | World: NPC (1) | 1 | |
| Storage | World: chest (1) | 1 | NPC → Storage (2) |
| Teleport Stones | World: stone (1) | 1 | |
| Herb Garden · Beds / Racks | World: bed (1) / → Racks (2) | 1–2 | |
| Fishing | World: fishing spot (1) | 1 | |
| Exchange | World: exchange clerk (1) | 1 | |
| Auction | World: pavilion or Market Street (1) | 1 | NPC (2) |
| Trial Tower | World: tower (1) | 1 | |
| County Hall · Jobs / Relief | World: County Hall (1) / → Relief (2) | 1–2 | Clerk (2) |
| Beast Arena | World: arena (1) | 1 | |
| Core Exchange | World: Beast Hall NPC (2) | 2 | |
| Qiankun Pouches | World: Tailor Xun (2) | 2 | |
| Library (shop) | World: library (1) | 1 | |
| Chess | World: insight stone (1) → Study (2) | 2 | |
| Guqin | none (see "Found while inventorying") | — | Meant: Bag → Key Items → Guqin → Use (4) |
| Welcome Back | Event: entering or resuming with gains | 0 | |
| Gravely Wounded | Event: `player_gravely_wounded` | 0 | |
| Mercy | Event: `foe_surrendered` | 0 | Context button beside a yielding foe (1) |

Deepest paths (4 taps or more):

1. Crafts · Alchemy · Extraction and later screens: Menu → Crafts → Alchemy → recipe → To the furnace → Light the
   furnace (6). The Furnace screen alone is 5.
2. Crafts · Forge · Enhance (and Inherit, Salvage, Reroll, Natal): Menu → Crafts → Forge → mode (4).
3. Crafts · Guild · another guild: Menu → Crafts → Guild → guild (4).
4. Shop · Sell and Buy Back for the sect shop: Menu → Sect → Sect shop → tab (4).
5. Notice Board · Bounties from the HUD: Menu → Sect → Missions → Bounties (4).
6. Relations tabs by the Heart: Progress bar → Heart → Ledger → tab (4); by the portrait it is 3.

Pages with no HUD path at all: Dialogue, Storage, Teleport Stones, Herb Garden, Fishing, Exchange, Auction, Trial
Tower, County Hall, Beast Arena, Core Exchange, Qiankun Pouches, Library, Chess (world objects and NPCs), the three
event pages, and the Guqin.

---
## 4. Art and UI inventory (U4)

### 4.1 Colour tokens

`UiKit` defines fifteen colours (`scripts/ui/ui_kit.gd:11-25`). The count is the number of `UiKit.<TOKEN>` references in
`scripts/`; the convention is how the code uses each one, since nothing names the roles.

| Token | Value | Uses | Used for, by convention |
|---|---|---|---|
| `INK` | `#071015` | 56 | Outlines of text and glyphs, the close button's X (`page.gd:131-132`), dark marks on light art |
| `RIVER_NIGHT` | `#0A2027` | 0 | Only the `StyleBoxFlat` fallback when a kit texture is missing (`ui_kit.gd:141`) |
| `DEEP_TEAL` | `#0D3035` | 4 | Icon placeholder (`page.gd:257`), portrait roundel (`hud.gd:1476`), pet strip discs |
| `JADE_SHADOW` | `#15514F` | 0 | Unused |
| `JADE` | `#2C9E8F` | 27 | Progress bars (meridians, body, crafts), met-requirement dots, the scroll thumb (`page.gd:346`) |
| `BRIGHT_JADE` | `#67D6BD` | 125 | Positive text: done objectives, gains, "ready", owned; the rare herb ring |
| `BRONZE` | `#9A6A35` | 11 | Heading underline (`page.gd:207`), lock icon (`page.gd:152-153`), map border |
| `GOLD` | `#E5B84C` | 156 | Headings (`page.gd:206`), main-quest marks, bottleneck, section labels |
| `PALE_GOLD` | `#FFE6A1` | 241 | Window titles (`page.gd:113`), primary button labels (`page.gd:162`), names and key values |
| `PAPER` | `#E8E1CF` | 187 | Body text (default of `Page.text`, `page.gd:192`), secondary button labels |
| `MIST` | `#AFC9D1` | 386 | Secondary text, notes, hints, lock reasons |
| `RED` | `#E45858` | 81 | Danger, unmet needs, sin-side states, the mail badge, HP on the Character page |
| `QI` | `#32BED1` | 12 | QI bars |
| `SOUL` | `#9B78D1` | 21 | Soul bars, Dao insight bars, trial lines |
| `HOLLOW` | `#87949A` | 65 | Disabled button labels (`page.gd:163`), locked tabs, unknown entries |

Grade and quality colours come from `data/grades.json` through `UiKit.grade_color` and `UiKit.quality_color`
(`ui_kit.gd:239-243`); `UiKit.badge_color` (`ui_kit.gd:245-246`) adds its own grey, green and orange.

### 4.2 Fonts and sizes

| Face | File | Set up | Used for |
|---|---|---|---|
| Cormorant Garamond, weight 700 | `art/fonts/CormorantGaramond.ttf` | `ui_kit.gd:75-77` | Display text (`display = true`) at 22 px and up, drawn at 1.2× (`WORD_SCALE`, `ui_kit.gd:35`): titles, headings, big names |
| Source Serif 4, 600, optical size 14 | `art/fonts/SourceSerif4.ttf` | `ui_kit.gd:80-82` | Every word: labels, paragraphs, buttons |
| Source Serif 4, 700 | same | `ui_kit.gd:85-87` | Display text under 22 px, world labels, nameplates |
| Pixelify Sans | `art/fonts/PixelifySans.ttf` | `ui_kit.gd:90-98` | Numbers drawn outlined over the world (`draw_outlined`, `ui_kit.gd:196-198`): HUD counters, damage numbers, bar values |
| JadeRiverSymbols (DejaVu subset) | `art/fonts/JadeRiverSymbols.ttf` | `ui_kit.gd:49-53` | Fallback for ✓ ◆ ▶ ★ and arrows |

- `MIN_SIZE` = 14 (`ui_kit.gd:44`): `size_for` raises any smaller request to 14 (`ui_kit.gd:117`), as does
  `draw_outlined` (`ui_kit.gd:198`).
- `DISPLAY_MIN` = 22 (`ui_kit.gd:40`): display text below it is set in the bold serif (`ui_kit.gd:108-113`).
- The three text sizes (Settings › Accessibility): `TEXT_SIZES` = 0.92, 1.0, 1.12 (`ui_kit.gd:42`), applied to every
  word (`ui_kit.gd:120-122`) and to line height (1.3 × size, `ui_kit.gd:125-126`). At Small, a 14 px word draws at 13 px.
- The sizes in use: window title 34 (`page.gd:113`); heading 26 stepping down to 20 (`page.gd:202-207`); tab 20
  (`page.gd:145`); button 22 stepping down to 13 (`page.gd:156`, `:166-167`); body 19–20 (`page.gd:192`, `:210`);
  toast 20 (`page.gd:128`); bar label 17 (`page.gd:243`); HUD bars 16 (`hud.gd:1364-1365`), tracker 17/16/15
  (`hud.gd:1554-1572`), log 16 (`hud.gd:1853`), minimap room name 14 (`hud.gd:1605`).
- `hud.gd:9` also preloads Cormorant directly for the legacy panel (`hud.gd:1964`), outside `UiKit`.

### 4.3 The two kits

| | Pixel kit | HD kit |
|---|---|---|
| Builder | `tools/ui/build_ui.py` (647 lines) | `tools/ui/build_ui_hd.py` (474 lines) |
| Output | `art/ui/<asset>__<state>.png` (35 files) | `art/ui/hd/<asset>__<state>.png` (25 files) |
| Manifest | `data/ui_assets.json`: 21 assets | `data/ui_assets_hd.json`: 17 assets, `"scale": 3` |
| Authoring | Art pixels saved 2× nearest: 2 screen px per art px (`tools/ui/README.md`) | Signed distance fields at 3 texels per screen px (`build_ui_hd.py:33`) |
| Drawn as | `StyleBoxTexture`, nearest (`ui_kit.gd:146-158`) | `HdStyleBox` scaled down 3× with linear mipmaps (`scripts/ui/hd_style_box.gd`, `ui_kit.gd:162-182`) |

`UiKit.style(asset, state)` takes the HD asset first, then the pixel one, then a flat jade-edged box
(`ui_kit.gd:129-159`). A state an asset does not have falls back to its `normal` art (`ui_kit.gd:137`, `:165`).

| Asset | Pixel states | HD states | Margins (pixel / HD) | Used in code |
|---|---|---|---|---|
| `major_window` | normal | normal | 24 / 32 | windows, confirm, creator panels |
| `minor_panel` | normal | normal | 12 / 12 | panels, cards, list rows, HUD player panel |
| `slot` | normal, selected, disabled | same | 8 / 8 | item slots, volume steps, name fields |
| `selected_slot_glow` | normal | normal | 12 / 12 | selected slot, focused name field |
| `button_primary`, `button_secondary` | normal, pressed, disabled | same | 16×14, 14×12 | every `btn()` |
| `tab` | normal, selected | same | 16×10 | tabs |
| `title_plaque` | normal | normal | 48×16 / 48×26 | window titles, dialogue speaker |
| `close_button` | normal, pressed | same | fixed | close |
| `toast`, `bar_shell`, `currency_pill`, `minimap_frame`, `dialogue_box`, `portrait_frame`, `realm_badge` | normal | normal | various | as named |
| `tooltip` | normal | normal | 10 | not used anywhere |
| `slot_empty_motif` | normal | — | fixed | empty technique and Treasure slots on the HUD (`hud.gd:1325`, `:1797`) |
| `hud_circle`, `hud_circle_large`, `hud_circle_small` | normal, pressed, active | — | fixed | not used: the HUD draws its rings (`hud.gd:1281-1303`) |

### 4.4 Icons and pixel scale

- `data/icon_manifest.json` maps ids to 756 icons in `art/icons/`: items 477, equipment 100 and techniques 58 at 64×64;
  HUD glyphs 70 at 32×32; status 34 and markers 17 at 24×24.
- Drawn sizes: slot contents at the slot less 12 px (`page.gd:253-255`; 52 px in a 64 px slot, 54 in the bag's 66);
  menu tiles 64 (`menu_page.gd:44-45`); HUD icon row 32 (`hud.gd:1380`); Attack glyph 64 (`hud.gd:1727`); other HUD
  glyphs 28 (`hud.gd:1759` and siblings); skill icons 48 (`hud.gd:1332`); quick-use and Treasure items 36
  (`hud.gd:1770`, `:1803`); status icons and the coin 24 (`hud.gd:1520`, `:1400`).
- Filtering: nearest for the project (`project.godot:37`) and every page (`page.gd:40`); linear only for HD frames
  (`ui_kit.gd:170`). Canvas 1280×720, stretch `canvas_items`, aspect `keep` (`project.godot:25-30`).

### 4.5 Inconsistencies

| # | What | Where | Screenshot |
|---|---|---|---|
| I1 | Mixed kits and drawing styles. HD frames sit beside pixel-kit art (the empty-slot motif, `hud.gd:1325`, `:1797`), procedural HUD rings (`hud.gd:1281-1303`) that match neither kit, and hand-drawn widgets outside the kit: the map scroll (`map_page.gd:66-68`), the Go board (`chess_page.gd:27-45`), the zither (`guqin_page.gd:100-110`), talisman paper (`crafts_page.gd:510-511`), the tribulation sky (`crafts_page.gd:767-771`), the tension bar (`fishing_page.gd:61-63`) | as listed | `hud_rest`, `world_map`, `chess`, `guqin`, `crafts_alchemy_tribulation` |
| I2 | Pixel icons scaled by non-integer factors under nearest filtering: 64→52 in slots, 64→48 skills, 64→36 quick-use, 32→28 HUD glyphs, 32→64 menu tiles | `page.gd:253-255`, `hud.gd:1332`, `:1770`, `:1759`, `menu_page.gd:44` | `inventory`, `hud_rest`, `menu` |
| I3 | States asked of the kit that neither kit has, so they draw as `normal`: `minor_panel` "selected", "disabled", "pressed" at 54 call sites; `slot` "pressed"; `tab` "disabled" | `data/ui_assets.json:112`, `data/ui_assets_hd.json:79`; e.g. `mail_page.gd:24`, `quest_page.gd:72`, `crafts_page.gd:181`, `menu_page.gd:43`, `page.gd:144`, `:250`, `settings_page.gd:34` | `mail`, `quests`, `crafts_alchemy_furnace` |
| I4 | Four ways to show a selection: a gold outline (`garden_page.gd:58`, `map_page.gd:266`), the kit glow (`page.gd:264`), the (missing) `minor_panel` "selected", and text colour only (`codex_page.gd:40`) | as listed | `garden`, `world_map_ranking`, `codex` |
| I5 | Off-token colours: 38 hex literals in 12 page files and 27 in `hud.gd`, plus float `Color()` literals (31 in `hud.gd`, 23 in `crafts_page.gd`, 14 in `map_page.gd`). The same colour is redefined page by page: sin red `e07a7a` (`character_page.gd:253`, `cultivation_page.gd:262`, `fates_page.gd:36`, `mercy_page.gd:21`, `relations_page.gd:7`, `hud.gd:828`, `:844`, `:1094`), merit gold `e8c872` (`mercy_page.gd:20`, `relations_page.gd:6`), warning orange `f0a040` (`breakthrough_page.gd:30`, `:51`, `cultivation_page.gd:93`, `ui_kit.gd:246`), heart pink `e05a6e` (`gift_page.gd:37`, `ui_kit.gd:320`). `hud.gd:45` defines its own `GOLD` (`d5bd85`) beside `UiKit.GOLD`; `map_page.gd:209-210` spell out `JADE` and `BRIGHT_JADE` in hex; HP is `c2474f` on the HUD (`hud.gd:1488`) and `UiKit.RED` on the Character page (`character_page.gd:172`); the side-quest blue `8fc8ff` (`hud.gd:1552-1553`) has no token | as listed | `mercy`, `relations`, `cultivation_heart`, `hud_rest`, `character` |
| I6 | Text asked for below `MIN_SIZE`: 13 px at `map_page.gd:110`, `:269`, `codex_page.gd:85`, `:140`, `pets_page.gd:202`, `:217`, `:232`, `:260`, `pouches_page.gd:41`, `beast_arena_page.gd:66`, `:110`, `crafts_page.gd:612`, `works_page.gd:101`, `:133`, `hud.gd:1485`, `:1760`; 12 px at `pets_page.gd:218`; 10 px at `hud.gd:1689`. They draw at 14 (`ui_kit.gd:117`), but `fit()` measured them at the smaller size, so a label fitted with an ellipsis still overruns (the "Talism…" gear label). `btn()` shrinks labels down to 13 (`page.gd:167`) with the same mismatch | as listed | `spirit_animals_growth`, `codex_seasons`, `pouches` |
| I7 | Tap targets under 48×48 px: 86 `btn`/`region`/`slot_box` declarations with a literal side under 48 (for example `training_sect_page.gd:109` 78×28, `pets_page.gd:196` 110×28, `pets_page.gd:190` 180×30, `map_page.gd:277` 160×36, `crafts_page.gd:713-721` 136×38, `techniques_page.gd:73` 100×38, `pets_page.gd:63-70` 99×38, `posts_page.gd:73-78` 136×40, `your_sect_page.gd:75` 90×40, `cultivation_page.gd:195-232` 128×40, `shell_screens.gd:249` 420×38), and computed ones: dialogue choices never above 46 px high (`dialogue_page.gd:80`, `:84`), teleport rows 27 px with ten stones (`teleport_page.gd:14`, `:22`), volume steps 48×36 (`settings_page.gd:32`), toggles 110×44 (`settings_page.gd:89`), hair dye 50×42 (`shell_screens.gd:237`), the HUD Draught button 44 px (`hud.gd:219`), pet-strip bag animals 44 px (`hud.gd:1440`), the tracker's auto-path button 30×22 (`hud.gd:1558`) | as listed | `teleport`, `training_sect_role`, `techniques_inner`, `dialogue`, `settings`, `hud_tracker` |
| I8 | Spacing off the 8 px grid: content insets 28 and 84/128 (`page.gd:67-69`), tab gap 6 and minimum 118 (`page.gd:141`, `:149`), list row inset 4 and 10 (`page.gd:338`), the default modal at 290,170 700×380 (`page.gd:42`); 23 of the 39 `list()` row heights (62 in `quest_page.gd:67` and `crafts_page.gd:164`, 70 and 76 in `shop_page.gd:38-101`, 58 in `tower_page.gd:27`, 52 in `beast_arena_page.gd:29`, 36 and 38 in `relations_page.gd:81`, `:168`, 150 in `codex_page.gd:67` …); gaps between neighbouring buttons of 6, 8, 10, 12, 14, 16 and 20 px; HUD button pitch 92 (`hud.gd:27-29`) and 58 (`hud.gd:42`); the bag grid ends 2 px from the detail panel (`inventory_page.gd:72-73`, `:105`) | as listed | `inventory`, `hud_rest` |
| I9 | Labels that clip or run into frames: the tracker's objective count (`hud.gd:1572`), the Body hint (`cultivation_page.gd:129`), path cards (`cultivation_page.gd:192`, `:206`, `:207`, `:215`, `:224`), the arena help (`beast_arena_page.gd:88`), the Dao list on Teaching (`workshop_page.gd:184-185`; one line with no width check, short enough for Tester's three Daos), sect-tree nodes (`training_sect_page.gd:101`), the auction's "Held by" under the bid buttons (`auction_page.gd:40`), the Daily activity note and the post craft line on the panel's bottom edge (`quest_page.gd:167`, `posts_page.gd:117`) | as listed | `hud_tracker`, `cultivation_body`, `cultivation_paths`, `beast_arena`, `training_sect_role`, `auction`, `quests_daily`, `posts_crafts` |
| I10 | Words built from ids rather than strings: rank names (`training_sect_page.gd:29`, `character_page.gd:44`, `quest_page.gd:132`), profession ranks (`workshop_page.gd:47`, `crafts_page.gd:163`), family and element (`techniques_page.gd:134`), method grade and affinity (`cultivation_page.gd:324-326`), state, stability and injuries (`cultivation_page.gd:45`, `:57`, `:60`), grade and quality (`inventory_page.gd:134-135`), wardrobe looks (`character_page.gd:107`), disciple traits (`your_sect_page.gd:158`), requirement causes (`breakthrough_page.gd:33`, `cultivation_page.gd:95`), origins (`shell_screens.gd:190`) | as listed | `workshop_appraisal` ("Apprentice · 24"), `shell_creator` ("Fishers Child") |
| I11 | Numbers: `UiKit.fmt` rounds and groups thousands (`ui_kit.gd:272-279`), the HUD truncates and does not group (`hud.gd:1488`): Max HP 31,751 on the Stats tab, 31750/31750 on the HUD and the Overview | as listed | `character_stats`, `hud_rest` |
| I12 | Plurals: "Raise · %d shards" and "%s  ·  %d shard" are fixed forms, so the game can print "Raise · 1 shards" and "5 shard" (`data/strings/en.json:1372`, `:2483`) | as listed | `teleport` |
| I13 | Window sizes chosen per page and off the grid: 1020×600, 940×580, 980×600, 1040×580, 1000×640, 760×560, 680×500, 680×400, 640×420, 600×540, 600×420 (`beast_arena_page.gd:10`, `core_exchange_page.gd:7`, `gift_page.gd:10`, `fates_page.gd:7`, `pouches_page.gd:12`, `welcome_page.gd:7`, `teleport_page.gd:7`, `mercy_page.gd:8`, `exchange_page.gd:8`, `emotes_page.gd:8`, `fishing_page.gd:19`); two widgets placed in screen coordinates regardless of the window (`your_sect_page.gd:17`, `:32`) | as listed | `beast_arena`, `fates`, `pouches` |
| I14 | Durations in four styles: "1 h 6 m" (`ui.calendar.span_hm`, `data/strings/en.json:1317`), "5h 15m" (`ui.auction.closes_in`, `:1277`; `ui.posts.hours_minutes`, `:2215`), "4:23:55" (`UiKit.clock`, `ui_kit.gd:266-270`, for the garden, dew and rack timers) and bare seconds, "Talisman recovering (150645s)" (`sim.combat.talisman_recovering_ds`, `data/strings/en.json:817`; `combat_authority.gd:1451`) | as listed | `calendar`, `auction`, `garden`, `revival` |

---
## 5. Screenshots (U5)

122 screenshots in `docs/ui_inventory/` (640×360, 256-colour PNG; `.gdignore` keeps Godot from importing them). They
show **Tester**, the character `tests/valley_run.gd` creates and plays through Acts I–III, from its last checkpoint
`ls6_end` (Sphere Lord 3; the Jade Sect's Sect Master; a sect of its own at level 1; a Reed Otter active; standing in
the Wardens' Hall). No screenshot uses `--unlock-all`, `--max-character` or the Max Test character. Each was captured
headlessly from `JadeRiver/` with Godot 4.5.1:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://valley_cp/ls6_end --load-slot <extra> --wait=2 --capture --shot=<name>
```

`--load` plays from a copy of the checkpoint folder (`main.gd:131-138`) and `--load-slot` enters slot 1 as saved
(`main.gd:166-167`). `--open-page=<id>[:<tab>]` opens a page 0.8 s after entering (`main.gd:388-391`); the tab part is a
tab id or, for some pages, an argument (the furnace's preview states such as `alchemy:__fusion`, `mercy:<enemy>`,
`gift:<npc>`, `chess:<site>`, `guqin:play`, `auction:valley`). This replaces the brief's `--unlock-all
--realm=sphere_lord_1 --room=lh_harbor_market` capture, at the user's instruction.

What the character has not reached shows as it would to that player: the Works tile and all seven Works tabs are
locked (Post Arts and the six works are not opened on this run), and so is the Qiankun pouch's sewing (`pouch_sewing`).

Two notes on the pictures:

- The page screenshots were retaken on the build that carries this page (`7b3d40d`, v1.2 with the Phase D and E
  art), the same build as the checkpoint, so every id in them resolves. The three shell screens (`shell_title`,
  `shell_selection`, `shell_creator`) are from the first pass at `bfbb2c5`; they did not change between the two. The
  findings below were made on the first pass: B13 and B14 were already fixed in the build, B6 was fixed after it
  (P4a), and the P2 bug pass re-checks each of the rest before fixing it.
- `valley_run` plays on a simulated clock that runs ahead of the real one, and the checkpoint's timestamps follow it.
  A capture runs on the real clock, so a cooldown set near the end of the run reads long (the revival talisman:
  150,645 s) and the Welcome page counts 0 minutes away.

| Screenshots | Extra arguments |
|---|---|
| `hud_rest` | none |
| `hud_fight` | `--foe=admiral_voss:1 --foe=scarlet_kiln_disciple:2` |
| `hud_tracker` | `--guide-demo` (a tracked quest leading out of the room) |
| `hud_pet_wheel` | `--pet-wheel` |
| `menu`, `inventory`, `inventory_key`, `character`, `character_stats`, `character_aptitude`, `character_titles`, `character_attunement`, `character_wardrobe` | `--open-page=menu`, `inventory[:key]`, `character[:<tab>]` |
| `cultivation`, `cultivation_foundation`, `cultivation_body`, `cultivation_heart`, `cultivation_paths`, `cultivation_methods`, `cultivation_dao`, `cultivation_seclusion`, `breakthrough` | `--open-page=cultivation[:<tab>]` (Paths is tab id `vows`), `breakthrough` |
| `cultivation_dao_tier5` | as `cultivation_dao`, from a copy of `ls6_end` whose Daos are listed Sword first (key order only), so the tier-5 row is on screen (see B1) |
| `techniques`, `techniques_inner`, `techniques_secret`, `quests`, `quests_side`, `quests_daily`, `quests_done` | `--open-page=techniques[:inner\|secret]`, `quests[:<tab>]` |
| `world_map`, `world_map_ranking`, `calendar` | `--open-page=world_map[:ranking]`, `calendar` |
| `codex`, `codex_collection`, `codex_achievements`, `codex_paths_above`, `codex_seasons` | `--open-page=codex[:<tab>]` |
| `mail`, `shop`, `shop_sell`, `shop_buyback`, `storage`, `characters` | `--open-page=mail`, `shop[:sell\|buyback]`, `storage`, `characters` |
| `settings`, `settings_controls`, `settings_access`, `settings_data` | `--open-page=settings[:<tab>]` |
| `dialogue` | `--talk=warden_commander_yao` |
| `welcome`, `revival`, `teleport`, `emotes`, `fishing`, `exchange` | `--open-page=<id>` |
| `posts`, `posts_crafts`, `posts_store`, `posts_bench`, `posts_vows`, `pouches` | `--open-page=posts[:<tab>]`, `pouches` |
| `works`, `works_seals`, `works_steles`, `works_favours`, `works_furnace`, `works_flags`, `works_mirror` | `--open-page=works[:<tab>]` (all locked for this character) |
| `notice_board`, `notice_board_bounties`, `training_sect`, `training_sect_role` | `--open-page=notice_board[:bounties]`, `training_sect[:role]` |
| `training_sect_ae_end` | from checkpoint `ae_end` (Tester as an Elder of the Jade Sect, mid Act II, at the Starsea Launch): `--load=user://valley_cp/ae_end --load-slot --open-page=training_sect`, to show the Promotion trial button (B5) |
| `your_sect`, `your_sect_disciples`, `your_sect_expeditions`, `your_sect_territory` | `--open-page=your_sect[:<tab>]` |
| `spirit_animals`, `spirit_animals_growth` | `--open-page=spirit_animals[:growth]` |
| `beast_arena`, `companions`, `core_exchange`, `tower` | `--open-page=<id>` |
| `relations`, `relations_bonds`, `relations_grudges`, `relations_fame` | `--open-page=relations[:<tab>]` |
| `gift`, `mercy`, `chess` | `--open-page=gift:aunt_ping`, `mercy:scarlet_kiln_warden`, `chess:insight_falls` |
| `county`, `county_relief`, `guqin`, `guqin_play` | `--open-page=county[:relief]`, `guqin[:play]` |
| `crafts`, `crafts_alchemy`, `crafts_forge`, `crafts_arrays`, `crafts_talisman`, `crafts_guild`, `crafts_charts`, `crafts_vessels` | `--open-page=crafts`, `alchemy`, `forge`, `arrays`, `talisman`, `guild`, `charts`, `vessels` |
| `crafts_alchemy_furnace`, `crafts_alchemy_extraction`, `crafts_alchemy_fusion`, `crafts_alchemy_condensation`, `crafts_alchemy_tribulation`, `crafts_forge_enhance` | `--open-page=alchemy:__furnace`, `:__extraction`, `:__fusion`, `:__condensation`, `:__tribulation`, `forge:enhance` |
| `workshop`, `workshop_appraisal`, `workshop_healing`, `workshop_puppetry`, `workshop_research`, `workshop_teaching` | `--open-page=workshop[:<tab>]` |
| `garden`, `garden_racks` | `--load=user://valley_cp/ls6_end` without `--load-slot` (which ignores `--room`), then `--room=cm_cave_abode --at=1000,900 --garden-preview --open-page=garden[:racks]`: the same character at a garden, with `--garden-preview` filling the beds and a rack |
| `fates` | `--offer-fates --open-page=fates` |
| `auction`, `auction_valley` | `--open-page=auction[:valley]` |
| `shell_title`, `shell_selection`, `shell_creator` | `--load=user://valley_cp/ls6_end` without `--load-slot`; then nothing, `--preview-selection`, `--preview-create` |

Not captured: Your Sect before founding, the Library (the shop page with a library's stock), and fishing's wait, bite
and fight phases (the capture lands after the bite has passed, on "It got away.").

---
## Found while inventorying

| # | What | Where | Screenshot | Likely cause |
|---|---|---|---|---|
| B1 | The Dao tab throws a script error every frame for any Dao at tier 5 or 6 (48 in the `cultivation_dao_tier5` capture), and those rows draw no insight bar and no Contemplate button (Tester's Sword Dao, Adaptation). Every other row shows the next-but-one target: Alchemy at Unaware shows 12 / 300 where tier 1 needs 100; Blood at Imitation shows 549 / 2,000 where tier 3 needs 800 | `cultivation_page.gd:347` | `cultivation_dao`, `cultivation_dao_tier5` | The page indexes `dao_tiers` as if it began with a 0 (`[mini(tier + 1, 6)]`; its fallback has 7 entries), but `data/curves.json:62-69` holds 6 thresholds, where tier *n + 1* needs `dao_tiers[n]` (`progression_rules.gd:278-283`). Index 6 is out of range and every other row is one step ahead |
| B2 | The guqin page cannot be opened in play. The guqin is a `tool`, so it goes to the key-item pouch; `use_item` takes only bag indices, and the Key Items tab offers no Use button (only "Ride in flight" for vessels) | `data/items.json` (guqin, `type: tool`); `inventory_authority.gd:306-313`, `:846`, `:860`; `inventory_page.gd:243-246` | `inventory_key`; `guqin` (opened with `--open-page=guqin`) | The guqin's `use_action` route (`inventory_authority.gd:860`) was written for bag items; it is the only usable item of `type: tool` |
| B3 | List selection is invisible: rows passed the `minor_panel` "selected" state draw exactly like the others (the auto-selected quest, the mail being read, recipes, shop stock, pets, tower floors, works rows …). Locked menu tiles and disabled rows get no dimmed frame either | 54 call sites, e.g. `quest_page.gd:72`, `mail_page.gd:24`, `crafts_page.gd:181`, `menu_page.gd:43`; `ui_kit.gd:137`, `:165` | `quests_side`, `quests_done`, `mail` | Neither kit builds `minor_panel` in any state but `normal` (`tools/ui/build_ui.py:523`, `tools/ui/build_ui_hd.py:401`; `data/ui_assets.json:112`, `data/ui_assets_hd.json:79`), and `UiKit.style` falls back to `normal` silently |
| B4 | Content runs off the window and under the HUD, and its buttons cannot be reached: Character › Titles (Tester's 19 titles at 64 px; the page holds 7½), Techniques › Secret Arts (11 arts at 64 px; Concealment's false-realm buttons sit on the ninth row, on the HUD), Your Sect › Expeditions (10 regions at 50 px, then running expeditions and their Collect buttons), Works › Favours (four 122 px cards from 64 px down: the fourth ends 48 px past the content) | `character_page.gd:73-79`; `techniques_page.gd:88-102`; `your_sect_page.gd:67-82`; `works_page.gd:143-162` | `character_titles`, `techniques_secret`, `your_sect_expeditions` (Works › Favours is locked for Tester: from the geometry) | Plain `for` loops with a fixed step instead of `Page.list()` |
| B5 | Sect › Rank: when the next rank is near the foot of the list (Elder to Sect Master), its Promotion trial button is drawn under the Missions button and cannot be pressed | `training_sect_page.gd:45`, `:48` | `training_sect_ae_end` (checkpoint `ae_end`, an Elder) | The trial button follows the rank row (`y - 30`) with no check against the two fixed buttons at the panel's foot |
| B6 | Emotes: the eight 156×56 buttons overlap (Bow over Beast Call and Wave, Laugh over Sit and Fist salute); a tap in the overlap goes to the later one | `emotes_page.gd:15`, `:26` | `emotes` | A wheel radius of 0.36 × the content's short side (about 155 px) puts neighbours 119 px apart |
| B7 | Teleport Stones: with ten stones each button is 27 px high around 22 px text | `teleport_page.gd:14`, `:22` | `teleport` | Row height is the content height shared by the stones, less 8, with no scroll or minimum |
| B8 | English words written in the scripts, so a translation cannot reach them: "ready" on the map's boss timers and in the auto-refine queue; "taels", "stones", "contrib." after shop prices; "furnace" and "forge" inside the Alchemy and Forge empty-state sentence (the Cooking, Charts and Vessels words come from strings) | `map_page.gd:173`; `crafts_page.gd:597`; `shop_page.gd:44`; `crafts_page.gd:195` | `shop`, `crafts_alchemy`, `crafts_forge` | `contract_tests` treats any lowercase single word as an id (`tests/contract_tests.gd:112`), so these pass the "no player-facing text" gate |
| B9 | The title screen says "v1.0 · Jade River Valley" on the v1.2 build | `shell_screens.gd:29`; `tools/data/ui_strings.json:511` | `shell_title` | The string was not updated after v1.0 |
| B10 | Origins have no names or descriptions: the creator shows "Fishers Child", "Scholars Heir", "Smiths Apprentice" (no apostrophe) and an empty description; the Character page reads "Origin: Fishers Child" | `data/origins.json` (entries carry `id`, `bonus`, `element_nudge` only); `shell_screens.gd:190`, `:242-243`; `character_page.gd:45` | `shell_creator`, `character` | `ContentDB.name_of` falls back to the capitalised id (`content_db.gd:173-185`) |
| B11 | The HUD tracker cuts objective counts: "Net glowflies at the Reed Shallows  0/5" shows "…Shallows  0" | `hud.gd:1572` | `hud_tracker` | A 290 px draw width, with the count appended to the end of the text |
| B12 | The Breakthrough page shows "Trial: <null>" for every great breakthrough without a trial event (13 realms, Sphere Lord 3 among them) | `breakthrough_page.gd:23-24`; `progression_authority.gd:439` | `breakthrough` | `data/realms.json` stores `"event": null` (`tools/data/realms.py:25-75` and `:149-151` write `None`), and `str(spec.get("event", ""))` turns null into the text "<null>", which is not "" |
| B13 | The Sphere button on the HUD is an empty ring: there is no `sphere` icon | `hud.gd:1763`; `data/icon_manifest.json` (no `sphere` key) | `hud_rest` (the ring left of the two Treasure buttons) | The Sphere (v1.2 Phase C) shipped its button without a glyph; `glyph()` draws nothing for a missing icon (`hud.gd:1305-1308`). Drawn in `16b89f7`, the commit after `bfbb2c5` |
| B14 | Three Phase C materials have no icon and show as three letters in their slot ("Orb", "Gra"): Orbit Stone Chip, Gravity Core, Moth Dust | `data/items.json` (`icon` names an id missing from `data/icon_manifest.json`); `page.gd:256-258` | `inventory` | The icons were not drawn; `data_validation` asserts every item has an icon (`tests/data_validation.gd:464-468`), so the suite should be failing on these. The same gap leaves three Phase C technique icons (`benevolent_script`, `rite_seal_script`, `upright_glyph`, named in `data/techniques.json`) undrawn. All six were drawn in `16b89f7`, the commit after `bfbb2c5` |
| B15 | Two Levels for one character: the HUD, Character page, Menu and slot cards say "Sphere Lord 3 · Lv 97"; the Cultivation badge and the Heaven Ranking say 98 | `content_db.gd:135-138` (`realm_label`); `progression_rules.gd:11-19` (`level`) | `hud_rest`, `character`, `cultivation`, `world_map_ranking` | `realm_label` prints the stage's first Level; `ProgressionRules.level` adds the progress within the stage |
| B16 | Auction rows: "Held by …" runs under the Bid buttons | `auction_page.gd:40`, `:44` | `auction` | The text is fitted to 30% of the row starting at 45%, while the two buttons start at the row's end less 324 px |
| B17 | Cultivation › Paths: the Buddhist card's merit line runs under the Poison Body card ("… vows h"); the card descriptions stop mid-sentence at three lines ("Heart demon x2;", "Righteous Qi,") | `cultivation_page.gd:207`; `:192`, `:206`, `:215`, `:224` | `cultivation_paths` | The merit line has no width; the descriptions get 58 px |
| B18 | Paragraphs cut short without an ellipsis: the Body hint loses "and a full soak in its bath."; the Jade Body trial stops at "and it is"; the arena help stops at "the rank you hold when the"; sect-tree node texts stop at two lines | `cultivation_page.gd:129`, `:155`; `beast_arena_page.gd:88`; `training_sect_page.gd:101` | `cultivation_body`, `beast_arena`, `training_sect_role` | Single-line `text()` with a width, or `para()` with a small height or `max_lines`, and no check that the text fits |
| B19 | Pages change game state themselves, which `page.gd:6-7` and `docs/architecture.md` forbid: the Bag erases the "new" dot directly; Works settles the Calcination Furnace and the Mirror of Echoes, and Roll-Call › Bench settles the bench, from `draw_page` on every frame; Spirit Animals fills an animal's missing fields while drawing | `inventory_page.gd:355`; `works_page.gd:167`, `:234`; `posts_page.gd:190`; `pets_page.gd:61` | — | Convenience calls into authority helpers (`calcination_settle`, `mirror_settle`, `_bench_settle`, `ensure_fields`) instead of an intent or a settle on open |
| B20 | Characters shows "no idle task" for a character keeping a post, which the Roll-Call lists at its post | `characters_page.gd:26-27` | — (Tester's second character keeps no post) | The page reads only `idle_task`; Keeping Post (S50) moved hunting idlers to posts and clears `idle_task` (`post_authority.gd:278-282`) |
| B21 | Text measured at one size and drawn at another: `fit()` and `btn()` measure at 12–13 px while `UiKit` draws at 14, so fitted labels can still overrun (see I6) | `page.gd:167`; `pets_page.gd:218`; the lines in I6 | `spirit_animals_growth` | `MIN_SIZE` is applied in `size_for` (`ui_kit.gd:117`) but not by the callers that measure |
| B22 | Cultivation › Seclusion: with a focus set, the "Set: … close the game" line is drawn over the seventh focus card (Medicinal bath) | `cultivation_page.gd:373`, `:380` | `cultivation_seclusion` (seven cards and no focus set; the overlap follows from the geometry: the third row ends 12 px above the content's foot, the line sits 30 px above it) | The third row of cards (bath, settle foundation) was added without moving the status line |
| B23 | Settings › Controls says "C cultivate (hold for the Cultivation page)", but holding C does nothing more than a tap; P opens the page. The line also leaves out E, P, V, G, H, O and R | `tools/data/ui_strings.json:2143` (`ui.settings.keyboard_arrows_wasd_move_space`); `hud.gd:597`, `:615` | `settings_controls` | The hold is only on the touch button (`hud.gd:137-140`); the keyboard handler taps on press |
| B24 | Relations › Karma › Named Debts shows the three debts defined in `karma.json` by their id: "Debt Dou Rescue" (and, when they occur, "Debt Lieutenant Spared", "Debt Lieutenant Killed"); only the two Gu debts have labels | `relations_page.gd:99`; `data/karma.json:765-795` (`dou_rescue`, `lieutenant_spared`, `lieutenant_killed`); `data/strings/en.json:1651-1652` (only `debt_gu_remembers`, `debt_gu_repays`) | `relations` | The label is `Tx.t("ui.cultivation.debt_" + id)` with no string for the debts in `karma.json`; `ContentDB.text` then capitalises the key's last part (`content_db.gd:175-176`) |
| B25 | Trial Tower: with no floor cleared, the Sweep button reads "Every floor swept today" (disabled). A tap answers with its lock reason, "Clear a floor to sweep it", which is the right message; the label says the opposite | `tower_page.gd:40-44`; `data/strings/en.json:2508`, `:2510` | `tower` | The label only tests `sweepable > 0`, and zero cleared floors also gives zero |

No other capture logged a script error.
