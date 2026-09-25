# Audit P3 · Herbs (S45 and its Part 8 content) against the build

**Build audited:** `/home/user/Game/JadeRiver`, branch `claude/jade-river-game-build-pua2z2`. The audit began on the G2a
working tree and ended at `dbeff8c`; G2a (treasures, throwables, flight vessels) was committed as `800f3a1` along the way. A
parallel session was editing and regenerating files while the audit ran: heart-demon tweaks, and `data/rooms` rewritten by
the generator. None of those edits touches herbs. Line numbers in files outside the herb code may have moved a few lines. The changelog calls this build **1.1** (heading "1.1 — The Azure Expanse" in `docs/CHANGELOG.md`; the CHANGELOG was being edited during this audit, so line numbers are not cited), so
every S45 milestone tag (v0.4 to v1.1) is at or below the build's own version number. Only "shared at v2.0" is later.
The audit only read files. Nothing was run or changed.

**Classes:** Present (exists and matches) · Differs (exists under another name, number or behaviour) · Partial (part of it
exists) · Missing (nothing like it).

## Totals

**Herb scope** (sections 1 to 17): 87 rows.

| Status | Count |
|---|---|
| Present | 5 |
| Differs | 7 |
| Partial | 10 |
| Missing | 65 |

**Cross-packet rows** (the priority table, the non-herb rows of the undefined-rules and stay-out tables, and the non-herb
event rows). These were checked only lightly, because other packets own them: 49 rows, of which 16 are Present, 2 Differ,
8 are Partial and 23 are Missing. Section 18, the coverage matrix, repeats rows counted elsewhere and is not counted
again.

**In short:** the herb loop in the build is the S16 baseline. It has 44 `herb_patch` nodes with `item`, `rank`,
`yield` and a 240 s `regrow_s`. Harvesting is a 1.5 s channel that completes by itself, and `node_gathered` reports it.
Three inert `garden_bed` objects open the Crafts page. None of S45's flags, intents, events, data files, UI or tests
exist. The best hooks to build on are:

- the 48-minute day clock;
- elite spawns, leash and Concealment;
- the Spirit Sense pulse;
- Appraisal, and the Flawed pill quality;
- the auto-refine offline timer;
- Qi springs;
- Old Pan's 100-year ginseng;
- the Drowned Shrine chests.

---

## 1. S45 · Purpose, ownership, intents, events

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Purpose: rare herbs are world events (guarded, timed, skill-picked, cultivated), not respawn timers | Missing | Every node is a respawn timer: `regrow_s` defaults to 240 (`tools/data/world.py:250`). The only states are ready and depleted (`world_authority.gd:37-44`, `:555-562`) | Build the S45 flags below |
| World owns node flags and ripen timers "in RoomState" | Partial | World owns depletion. State is split between `RoomRuntime.objects[id] {state, timer}` and each character's `c.rooms[room].nodes {obj: regrow_utc}` (`game_character.gd:31`, `world_authority.gd:43`, `:244-256`). There is no `RoomState` class, no node flags and no ripen timers | Add per-node `ripen`/`guardian` runtime state. Ripen timers should come from UTC plus the node definition, so they work offline. Name the owner to match the spec, or note in the spec that `RoomRuntime` plus room memory is the RoomState |
| Crafting owns garden beds (`field_grade`, `soil`, `watered_utc`) | Partial | Only an unused `crafting.garden: []` exists (`game_character.gd:19`). Nothing reads or writes it | Store per-bed records `{bed, field_grade, soil, watered_utc, herb, age, planted_utc}` |
| Crafting owns racks | Missing | — | Add `crafting.racks` |
| Crafting owns the Verdant Dew Vial's dew count | Missing | — | Add a dew count and `last_dew_utc` |
| Intent `harvest {node}` | Differs | The build uses `interact {object}` → `CraftingAuthority.gather` (`world_authority.gd:329-330`, `crafting_authority.gd:100-110`), then `complete_node {object}` (`crafting_authority.gd:29-31`, `:112`) | Rename these, or alias `harvest` to them |
| Intent `harvest_tap {timing}` | Missing | `complete_node` takes no timing. It only checks that elapsed ≥ channel − 0.15 s (`crafting_authority.gd:115`) | Add a `timing` argument and judge it against the rank window |
| Intents `transplant`, `water_bed`, `apply_spirit_soil`, `bottle_spring_water`, `use_dew`, `start_rack` | Missing | Not in any authority's `intents()` (`crafting_authority.gd:29-31`, `world_authority.gd:15`) | Add all six to CraftingAuthority and WorldAuthority |
| Emit `herb_harvested {age, perfect}` | Differs | The build emits `node_gathered {actor, object, item, count, craft}` (`crafting_authority.gd:134`). It has no age or perfect fields and is not in the event contract (`tools/data/contract.py:20-21` lists only `node_depleted` and `node_regrown` for World) | Emit `herb_harvested {actor, node, age, perfect}` and register it in `contract.py` |
| Emit `herb_ripening`, `guardian_spawned`, `seed_found`, `transplant_result`, `garden_raided`, `treasure_birth_announced` | Missing | None are emitted anywhere in `scripts/`, and none are in `data/event_contract.json` (121 events) | Add them to the authorities and the contract |

## 2. `herb_patch` fields

The nodes carry only `id, type, at, item, prop, yield, rank, regrow_s, requires, locked_text` (plus `alt` on one node). All
44 nodes are in `data/rooms/*.json` and are generated by `Room.herb()` (`world.py:245-251`), whose `**kw` would accept
the new optional fields.

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `age` 10 / 100 / 1,000 years ("existing") | Differs | Nodes have no `age` field. Age exists only as two item ids, `riverreed_ginseng_10` and `riverreed_ginseng_100` (`items.py:16-17`). There is no 1,000-year item, and the other five herbs have no ages. No node yields the 100-year root: it comes only from Old Pan (`economy.py:96`) and the Deepwater Bend expedition (`economy.py:581`) | Give nodes an `age` field. Either add aged item variants (for example `riverreed_ginseng_1000`, `mist_lotus_100`, `cloudtop_orchid_100`, `soulbell_flower_100`, `ember_pepper_100`) or store age on the stack instance. Define how age maps to recipes |
| `guardian`: nodes of 100 years and older spawn an elite from the roster; kill it, lure it past its leash, or pick under Concealment [v0.9] | Missing | Only hooks exist: elite spawns (`world.py:569-571`, `elite=True`), the 600-unit leash (`enemy_brain.gd:5`, `:74`), and Concealment (the secret art halves aggro, and the formation hides the player: `enemy_brain.gd:48-50`) | Add `guardian {enemy, elite}` to nodes. Spawn the guardian when the node ripens. Let the pick succeed if the guardian is dead, leashed away, or the player is concealed |
| `ripen`: a window of about 20 real minutes around a phase, every Nth in-game day [v0.9] | Missing | Nodes are ready or depleted only | Add `ripen {phase, every_days, minutes}` and a node state computed from UTC |
| The in-game day is 48 minutes | Present | `curves.json time_of_day.day_minutes = 48` (`stats.py:187`), `clock_service.gd:46-55` | — (note the phase-name issue in the next row) |
| Ripen phases "dawn / dusk / day / night" | Differs | The clock's phases are `morning / day / evening / night`, in four 12-minute quarters (`clock_service.gd:47-54`). It has no "dawn" or "dusk" and no in-game day index. A 20-minute window is longer than one 12-minute phase | Add `Clock.game_day(utc)` and define dawn and dusk as instants (for example the morning/night and day/evening boundaries), with ±10 minute windows |
| Picking early drops one age tier | Missing | — | Allow a pick when the node is unripe, at age − 1 tier |
| A Spirit Sense pulse shows the countdown [v1.0] | Missing | `sense_pulse` reveals only hidden portals and fog-hidden foes (`world_authority.gd:212-240`) | Report ripen countdowns for nodes within the sense radius |
| `season`: flowers only in named seasons (four seasons of one real week each, shown in the Codex); never gates progression [v1.0] | Missing | The only "season" is the Evergreen tree's per-character 7-day fruit cycle (`stats.py:65` `season_days: 7`, `crafting_authority.gd:347-359`). There is no global season | Add `seasons.json` and a global `Clock.season(utc)`. Nodes out of season show as dormant |
| `seed_chance`: a seed on a perfect harvest (default 10%) [v0.8] | Missing | There are no seed items | Add the field, default 0.10, rolled on the `crafting` stream |
| `tier_height`: rare nodes prefer raised tiers (S43 rule 14) [v0.4 data] | Missing | 43 of 44 nodes sit at `alt` 0. The only raised one is a 10-year ginseng on the Herb Terraces (`world.py:813`, `alt=120`). The Sky Ledges orchids are on the ground although ledges exist at 260 and 360 | Place rare nodes on raised surfaces (see section 16) |

## 3. Harvest technique [v0.8]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| 1.5 s hold | Present | `crafting_authority.gd:106` (herb channel 1.5); the HUD channel is at `hud.gd:128-145`, `:304-305` | — |
| The hold ends in a timing tap on a shrinking ring | Missing | The channel completes on its own when a filling arc on the Attack button reaches full (`hud.gd:138-145`, `:827-828`) | Draw a shrinking ring with a target band, and send `harvest_tap {timing}` |
| Window 12% Apprentice, 16% Adept, 20% Expert, 24% Master, 28% Grandmaster | Missing | — (fishing has a comparable tool-scaled window at `crafting_authority.gd:144`) | Add a `harvest_window` curve keyed by `herb_gathering` rank |
| Rank ladder up to Grandmaster | Differs | Rank names match (`curves.json profession_ranks`: apprentice … grandmaster), but `RANK_CAPS.herb_gathering` stops at master (`crafting_authority.gd:13`). Grandmaster, and so the 28% window, cannot be reached | Add a Grandmaster cap row, or drop 28% from the spec |
| Perfect: full age plus the seed chance | Missing | — | On perfect, grant the node's age and roll `seed_chance` |
| Miss: −1 age tier, never below 10 years | Missing | — | On a miss, grant age − 1 tier, with a floor of 10 years |

## 4. Seeds [text fix, v0.8]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Common seeds come from shops | Missing | The only seed in `items.json` is `evergreen_heart_seed`, a treasure (`items.py:295-296`). No shop stocks seeds | Add seed items and shop rows (see section 16) |
| Common seeds come from perfect harvests | Missing | — | Emit `seed_found` on a perfect pick |
| Rare seeds come only from secret realms and inheritances | Missing | No rare herb seeds exist. There are no secret realms (0 hits for `secret_realm`). Inheritances exist (unlock `inheritances`, `story.py:450`; Lu's trial, `story.py:1063`) but give no seeds. The Evergreen seed is Elder Hu's quest gift (`story.py:969-973`) | Add rare seeds to inheritance rewards now, and to secret-realm loot when S49 lands |
| The text fix (gardening must not imply seeds that don't exist) | Missing | The quest *Seeds of the Valley* reads "Plant, water, harvest. Three beds." and completes on any bed interaction (`story.py:828-831`). Gardener Ji says "Plant, water, wait. Harvest." (`story.py:197-199`). Nothing can be planted | Rewrite the text to name the seed sources, and make the quest plant a seed |

## 5. Beds [v0.9]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Garden beds | Partial | There are 3 `garden_bed` objects, on the Jade Herb Terraces only (`world.py:810-811`), unlocked at Qi Unfurling 4 (`story.py:451`). Interacting opens page `"garden"` (`world_authority.gd:362-364`). That page maps to `crafts_page.gd` (`main.gd:46`), which has no garden tab and falls back to the first unlocked craft (`crafts_page.gd:30`, `:39-43`). The bed is drawn with the willow-moss prop (`object_view.gd:12`) | Build a Garden page with plant, water and harvest. Consider beds for the Cloud sect and the cave abode |
| Each bed has a field grade (Low, Mid, High) that caps the herb grade it can grow | Missing | Herbs use the six item grades plain, common, earth, heaven, spirit and sage (`items.py:14-22`). The spec does not say how Low/Mid/High map onto them | Add `garden.json` with a field-grade → max-herb-grade table, and check it when planting |
| Spirit Soil (a rare drop) raises one bed a grade permanently | Missing | No such item | Add the `spirit_soil` item and the `apply_spirit_soil` intent |
| Qi-spring water can be bottled 3 times per day | Missing | `qi_spring` objects exist in 10+ rooms (for example `cf_falls_pool`, `hv_back_mountain`, `ja_cave_abode`) but only return text (`world_authority.gd:369-370`) | Add `bottle_spring_water`, with a daily count reset by `Clock.reset_day` |
| Each watering gives +25% growth | Missing | Beds have no growth model | Define the growth time per herb and age in `garden.json`. A watering shortens the remainder by 25% |

## 6. Transplanting [v1.0]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| "Dig up" at a rare node needs a spade tool and Expert gathering | Missing | There is no spade. The tools are pickaxes, a herb sickle, a rod, a loupe and a drying rack (`items.py:303-306`). The Expert rank exists | Add a `spirit_spade` tool (`tool.craft = "transplant"`) and the `transplant` intent |
| Moves the herb to a bed at its current age | Missing | — | Write a bed record at the node's age, and deplete the node |
| 25% chance to kill it, −5% per rank above Expert | Missing | — | Roll on the crafting stream and emit `transplant_result` |

## 7. Verdant Dew Vial [v1.0; tier extension v1.1]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| A Spirit Awakening reward | Missing | No item | Add `verdant_dew_vial` to `items.py` and grant it from a Spirit Awakening quest |
| Fills with one dew per 24 hours offline | Missing | Offline timers exist to reuse: the auto-refine `done_utc` (`crafting_authority.gd:418`) and `offline_claimed` | Accrue dew from `last_dew_utc` |
| Each dew ages one bed one tier | Missing | — | Add the `use_dew {bed}` intent |
| Capped at 1,000 years in the valley; 10,000-year herbs come from the Azure Expanse [v1.1] | Missing | No 1,000-year or 10,000-year items. The Azure Expanse rooms (`ae_*`) have no herb nodes | Cap by region, and add 10,000-year variants and nodes for the Expanse |

## 8. Processing racks [v0.9]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Racks "use the drying rack's offline timer code" | Differs | The drying rack has no timer. It is a tool item with `alchemy` power 1.0 (`items.py:306`), sold at `economy.py:61` and given by *Batch Work*, which promises "Batches go faster with dry ingredients" (`story.py:799-804`). Nothing ever reads `tool_power(c, "alchemy")`. The only offline craft timer is the auto-refine queue (`crafting_authority.gd:410-437`) | Build racks on the auto-refine queue pattern. Correct the spec's reference, and either make the drying rack a rack or fix the *Batch Work* text |
| Steaming: −30% toxicity for pills made from the herb | Missing | Hook: the pill `toxicity` field (`items.py:104-105`), applied in `inventory_authority.gd:429` | Add a processed-herb marker that carries into the crafted pill's instance |
| Wine-soaking: +10% potency | Missing | Hook: potency by quality (`inventory_authority.gd:220`) | Same pattern, applied as a potency multiplier |

## 9. Treasure births [v1.0, via the S49 scheduler]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| "A Spirit Fruit is ripening at X", shown as a light pillar on the minimap | Missing | There is no world-event scheduler (no `world_event_*` events). The minimap draws only portals, NPCs, shrines, springs, teleport stones and enemies (`hud.gd:765-810`) | Depends on S49. Add a notifier line and a minimap pillar marker |
| Rival NPC cultivators and a mini-boss arrive; scripted PvE that works offline; shared at v2.0 | Missing | Hooks: the room-event framework (`room_event_started`, `room_event_wave`, `room_event_completed`; set pieces at `world.py:1319-1340`) and field-boss timers. The only human foes resembling rivals are `nine_peaks_disciple` and `sparring_disciple` | Add a treasure-birth room event with a rival wave and a mini-boss, resolved offline |

## 10. Gathering trials [v1.0]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| A sect event dungeon: a timed gather of aged herbs against rival-sect NPCs | Missing | — | Add an instanced room event with timed aged nodes and rival gatherers |
| Rankings pay Foundation-pill recipes | Missing | There are no rankings. A possible payout exists: `foundation_guard_pill` (`economy.py:193`) | Add a trial ranking and recipe-scroll rewards |

## 11. Garden raids and fakes [v0.9]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Offline pest or thief events hit unguarded beds | Missing | Raids exist only for sect buildings (`sect_authority.gd:200-213`) | Roll raids offline per bed. Emit `garden_raided` and mail a report |
| A formation or a pet on Guard duty stops them | Missing | Formations exist (`workshop_authority.gd:81-127`) but have no guard effect. Pet roles are `combat`, `gatherer`, `cultivation` and `mount` (`pet_authority.gd:33`), with no Guard duty | Add a `guard` pet role and a garden-ward formation effect |
| Wandering-merchant "100-year" herbs | Partial | Old Pan, the "Wandering merchant" (`story.py:123`), sells `riverreed_ginseng_100` in rotation for 4 spirit stones (`economy.py:96`). They are always genuine | Make some of that stock fake |
| Some are fakes that only Appraisal reveals | Missing | Appraisal only accepts items with `use_action == "appraise"` (curios; `workshop_authority.gd:61-79`). `fake_jade` exists as an appraisal outcome (`items.py:353`) | Give herbs a hidden `fake` instance flag. Appraisal reveals it |
| Using an unappraised fake risks a Flawed pill | Missing | Hook: the Flawed quality exists (`crafting_authority.gd:248`) | Force or raise the chance of Flawed when a fake is an input |

## 12. Stays out

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Herbs never rot | Present | Bag stacks have no expiry. `items.py:170-171` says "Herbs never rot." | — |
| Herbs need no jade boxes | Present | No jade-box item or preservation mechanic exists | — |

## 13. Data

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `objects.json` herb fields | Differs | There is no `data/objects.json`. Room objects live in `data/rooms/*.json` `objects[]`, generated by `tools/data/world.py` (`Room.obj`/`Room.herb`, `:236-251`). None of the S45 fields are present | Add the fields through `Room.herb()`, or change the spec to name the room files |
| `seasons.json` | Missing | No such file | Add it (four named seasons of one week each, plus an epoch) |
| `garden.json` (field grades, soil, water) | Missing | No such file | Add it |
| Racks in `professions.json` | Missing | Its entries are appraisal, healing, puppetry, research, teaching and formations | Add steaming and wine-soaking rack entries |
| The Verdant Dew Vial in `items.json` | Missing | No entry | Add it |

## 14. UI

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Harvest ring | Missing | Only a filling progress arc on the Attack button (`hud.gd:827-828`) | Draw a shrinking ring with a rank-sized band |
| Minimap ripening icon with a timer | Missing | The minimap has no herb markers (`hud.gd:795-803`) | Add ripening icons with mm:ss |
| Garden page showing field grade and water | Missing | `"garden"` maps to `crafts_page.gd` (`main.gd:46`), which has no garden view | Build a `garden_page.gd` |
| The Codex season calendar | Missing | The Codex tabs are codex, collection and achievements (`codex_page.gd:8`) | Add a Seasons calendar tab |

## 15. Tests

`tests/rules_tests.gd` has no gathering checks. Its only herb-related checks are the Evergreen tree (`:361-377`) and raw
herbs (`:742-747`). `tests/data_validation.gd:268` checks only that each object's item exists, and
`tests/valley_run.gd:271-281` drives `complete_node` end to end. Hooks exist for pinning the clock
(`clock_service.gd:5-7`, `override_utc`) and for fixed seeds (`rules_tests.gd:101`).

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Test: ripen window by in-game time | Missing | — | Pin `Clock.override_utc` inside and outside the window |
| Test: an early pick drops a tier | Missing | — | Add it |
| Test: the guardian spawns once per ripening | Missing | — | Add it |
| Test: the tap window per rank | Missing | — | Add it |
| Test: seed chance under a fixed seed | Missing | — | Add it |
| Test: soil caps the grade | Missing | — | Add it |
| Test: transplant odds | Missing | — | Add it |
| Test: dew accrues offline and is capped | Missing | — | Add it |
| Test: fakes are revealed only by Appraisal | Missing | — | Add it |

## 16. Part 8 · Rare herb nodes, seeds, Spirit Soil

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| **Riverreed Ginseng 100 yr**: Bend Shore and Rapids Terraces; Tide Crab elite; dawn, every 2nd day, 20 min; no season | Partial | Bend Shore (`world.py:1171`) has a 10-year ginseng (`herb_1`, apprentice) and a mist lotus. Tide Crab spawns there as a normal foe; the room's elite is `jade_carp`. Rapids Terraces (`world.py:1230`) has only two mist lotus nodes. The item `riverreed_ginseng_100` exists | Add 100-year ginseng nodes on the raised ledges (`ledge_mv_1` at 220; Rapids `ledge_1` at 150), with a `tide_crab` elite guardian and a dawn/2-day ripen |
| **Riverreed Ginseng 1,000 yr**: Serpent's Shallows high rock; Riverbed Serpent (field boss); night, every 5th day; Summer | Partial | The room (`world.py:1181`) has `high_rock_0/1/2` at `alt` 100 and a `riverbed_serpent` field boss (`respawn_min` 45). It has no herb node, and there is no 1,000-year item | Add the item and a node on a high rock, guarded by the serpent, with a night/5-day ripen and `season: summer` |
| **Mist Lotus 100 yr**: Falls Pool and Behind the Falls; no guardian; dusk, every 3rd day | Partial | Falls Pool (`world.py:1087`) has an ordinary `mist_lotus` node (adept, 240 s). Behind the Falls holds only the weekly Mindwell Lotus (`world.py:1109`, regrow 604,800 s). Mist lotus has no age tier | Add the aged item and nodes |
| **Cloudtop Orchid 100 yr**: Sky Ledges; Stormwing Hawk elite; day, every 3rd day; Spring | Partial | Sky Ledges (`world.py:1260`) has two `cloudtop_orchid` nodes (expert) and a Stormwing Hawk elite spawn, but they are not linked. The orchids are at `alt` 0 although ledges stand at 260 and 360 | Move one orchid to a ledge and make it the aged node, with the hawk as guardian |
| **Soulbell Flower 100 yr**: Misty Slopes and Frozen Shrine; Mirror Wisp elite; night, every 3rd day; Autumn | Partial | Misty Slopes (`world.py:1269`) has a `soulbell_flower` node and normal Mirror Wisps; its elite is `mist_wolf`. The Frozen Shrine (`world.py:1296`) has no herb | Add the aged nodes in both rooms, with a Mirror Wisp elite guardian |
| **Ember Pepper 100 yr**: Thicket Heart canopy; Thornback Boar elite; day, every 2nd day; Summer | Partial | Thicket Heart (`world.py:1075`) has an `ember_pepper` node on the ground. It has no canopy surface, only rock ledges at 110 and 220. Thornback Boar spawns normally; the room's elite is `green_viper` | Add a canopy (branch) surface and the aged node, guarded by a boar elite |
| Willow Moss, Ember Pepper and Riverreed Ginseng seeds sold at Granny Liu's and in Greyreed Hamlet | Missing | `granny_liu` (`economy.py:34`) sells tea, salve, talisman, purging pill and incense. `greyreed` (`economy.py:98`) sells rice, rice balls, pills and hide. Neither sells seeds | Add three seed items and the shop rows |
| Mist Lotus seeds come only from perfect harvests | Missing | — | Set `seed_chance` on mist lotus nodes and sell the seed nowhere |
| Cloudtop Orchid and Soulbell seeds come from secret realms | Missing | There are no secret realms | Put them on inheritance rewards or hold them for S49 |
| Spirit Soil drops at 1% from rank 3+ beasts | Missing | The item doesn't exist, and enemies have no `beast_rank` (0 hits in `enemies.json` and `enemies.py`) | This depends on S46 beast ranks. Until then, use level or realm bands |
| Spirit Soil from the Drowned Shrine chest | Missing | The `ds_*` chests use `chest_dungeon` (for example `ds_abbots_sanctum` `vault`) | Add a guaranteed or weighted Spirit Soil drop to the vault chest |

## 17. Undefined rules and stay-out rows that concern herbs

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Undefined rule: "Gardening plants seeds with no seed source" (now defined in S45 seeds, the S16 gardening row and the Part 8 seeds) | Missing | Still undefined: there are no seed items and no planting (see section 4) | As in section 4 |
| Kept out: herb rot and pill decay | Present | Herbs have no expiry. Pills never decay: the Codex says "Pills never spoil" (`data/codex.json`; CHANGELOG G1 "Undefined rules settled") | — |

## 18. Coverage matrix (roll-up of rows above; not counted again)

| Gap report row | Milestone | Status |
|---|---|---|
| Guardian beasts | v0.9 | Missing |
| Ripening windows; Sense | v0.9; v1.0 | Missing (the 48-minute day exists) |
| Harvest technique | v0.8 | Partial (the 1.5 s hold only) |
| Seeds | v0.8 | Missing |
| Field grade, spirit soil, spring water | v0.9 | Missing (beds exist but do nothing) |
| Transplanting | v1.0 | Missing |
| Herb aging artifact | v1.0; v1.1 | Missing |
| Processing | v0.9 | Missing (the drying rack does nothing) |
| Treasure births | v1.0 | Missing |
| Gathering trials | v1.0 | Missing |
| Seasons | v1.0 | Missing |
| Garden raids, fakes | v0.9 | Missing (Old Pan's 100-year ginseng is always real) |
| Preservation | Stays out | Present |

## 19. Priority table (cross-packet, light check)

| # | Priority | Status | Evidence |
|---|---|---|---|
| 1 | Define S15's undefined rules | Partial | Fire, furnaces, "pills never decay", auto-refine XP (`crafting_authority.gd:431-433`) and the heart-demon field (`cultivator_state.gd:45`) came with G1 (CHANGELOG, section G1). **Seed sources (S16/S45) are Missing**, although `docs/gap_audit.md:52` had planned them for G1 |
| 2 | Lifetime pill resistance, foundation share, residue | Present | G1 rules (CHANGELOG, section G1). Of the events, only `residue_changed` is emitted (`progression_authority.gd:706`) |
| 3 | Heart-demon meter and karma ledger | Present | `cultivator_state.gd:45`; `progression_authority.gd:715`, `:726` |
| 4 | Treasure quick slot, flying sword, talisman craft, throwables | Partial | G2a (`800f3a1`): treasure buttons, throwables, a talisman treasure, and a Flying Sword flight vessel (CHANGELOG, section G2a). Talisman crafting and Sword Release are missing |
| 5 | PetState depth | Missing | No bloodline, contracts or skill books (grep finds 0 hits) |
| 6 | Herb node flags and harvest tap | Missing | This packet |
| 7 | Enhancement pity, transfer, salvage | Partial | `salvage` exists (`crafting_authority.gd:463-474`). A failed enhance stores nothing, so there is no pity (`:439-461`), and there is no transfer |
| 8 | Heavenly tribulation, Core Forging grade, breakthrough fates | Missing | 0 hits for tribulation or fate |
| 9 | World-event scheduler and calendar | Missing | No `world_event_*` events |
| 10 | NPC affinity, bonds, grudges, bounties | Missing | 0 hits for grudge or bounty |
| 11 | Pet skill books, gear, mount slot, Spirit Beast Bag, Beast Arena | Missing | — |
| 12 | Body ladder, soul line, sect role variants, Inner Arts, stances | Partial | `body_level` and `body_level_changed` exist; the rest does not |
| 13 | Associations, recipe fragments, experimentation | Missing | — |
| 14 | Alignment, Blood and Buddhist paths, new weapon families | Missing | 7 families only (`weapon_families.json`) |
| 15 | Rankings, territory, mortal kingdom, weather, lifespan, insect swarm | Missing | — |

## 20. Other undefined rules and kept-out staples (cross-packet, light check)

| Row | Status | Evidence |
|---|---|---|
| Pill Grain "keeps longer": no decay rule | Present | Codex: "Pills never spoil"; `stats.py` pill-marks comment |
| "Rare fire or a special furnace" | Present | `crafting_authority.gd:285-315`; CHANGELOG G1 "Fire and furnace" |
| The Reflection's Heart Demons need a state field | Present | `cultivator_state.gd:45` `heart_demon` |
| Auto-refine XP | Present | 25% (`crafting_authority.gd:431-433`) |
| Hard lifespan | Present (kept out) | No lifespan anywhere |
| Stamina gates, battle passes | Present (kept out) | None (`gap_audit.md` stay-out table) |
| Pet permadeath | Present (kept out) | Pets retreat at 0 HP |
| Destructive enhancement | Present (kept out) | A failure costs materials only (`crafting_authority.gd:452-458`) |
| Sexual dual cultivation | Present (kept out) | None |
| Player full-loot | Present (kept out) | None |
| A full Gu path | Present (kept out) | None ("Gu" is an NPC family) |
| Corpse refining, soul banners, body seizing as player powers | Differs (borderline) | The G2a `wisp_banner` (`800f3a1`) is "A banner of three bound wisps" used by the player (`data/items.json`). It is close to a soul banner, so it needs recasting or an explicit ruling |
| Stat and aptitude pills in shops | Present (kept out) | Shops sell body-XP and progress items only |
| Unrestricted auto-battle | Present (kept out) | The idle hunt is abstract |

## 21. S43–S49 events

None of these names is in `data/event_contract.json`. The herb row is counted in section 1.

| Event row | Status | Evidence |
|---|---|---|
| jumped, landed, wall_kicked, art_used | Missing | Only `flight_started`, `flight_ended` and `dodged` exist |
| climb_started / climb_finished | Missing | — |
| fell_out | Missing | — |
| volume_entered / volume_left | Missing | `hazard_struck` and `hazard_warned` are different events |
| pill_resistance_changed, foundation_changed, residue_changed | Partial | Only `residue_changed` (`progression_authority.gd:706`) |
| heart_demon_changed | Present | `progression_authority.gd:715`; HUD toast at `hud.gd:490-493` |
| fate_offered / fate_chosen | Missing | — |
| tribulation_started, tribulation_bolt, tribulation_result | Missing | — |
| core_graded | Missing | `purity_changed` only |
| qi_deviation, epiphany, vow_broken, body_tier_reached, physique_awakened | Missing | Near equivalents: `qi_backlash`, `body_level_changed` |
| flame_absorbed, furnace_blast, pill_cloud, pill_tribulation_result | Partial | `flame_absorbed` (`crafting_authority.gd:340`), `pill_cloud` (`:280`) |
| recipe_deduced, experiment_result, guild_rank_changed, commission_completed | Missing | `recipe_learned` and `profession_rank_up` exist |
| **herb_harvested, guardian_spawned, seed_found, herb_ripening, garden_raided** | Differs / Missing | `node_gathered {actor, object, item, count, craft}` only (section 1) |
| bloodline_awakened, contract_formed, pet_wounded, pet_skill_learned, pets_fused, pet_core_formed | Missing | `pet_bonded`, `pets_bred` and `pet_evolved` exist |
| beast_king_spawned, beast_tide_started, beast_tide_result | Missing | — |
| treasure_used, sword_released, sword_returned, sword_intent_changed | Partial | `treasure_used` (`inventory_authority.gd:454`), `treasure_art_used` (`combat_authority.gd:978`) |
| natal_grew, natal_broken, enhancement_inherited, items_salvaged, loadout_swapped, talisman_crafted, weapon_awakened | Partial | Only `item_salvaged`, in the singular (`crafting_authority.gd:473`) |
| merit_changed, sin_changed, debt_recorded, debt_called | Differs | `karma_changed {merit, sin, delta_merit, delta_sin}` (`progression_authority.gd:726`), `karma_debt_recorded` (`:733`), `karma_debt_repaid` (`:741`) |
| alignment_changed, affinity_changed, bond_formed, grudge_changed, hunter_dispatched, fame_changed | Missing | — |
| world_event_scheduled / started / ended | Missing | The `room_event_*` events are room-local |
| season_changed, weather_changed, ranking_changed, fortune_encounter, heavenly_phenomenon | Missing | — |
