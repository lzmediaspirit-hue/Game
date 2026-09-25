# Audit: v2 changes to existing sections (packet p8_changes.md)

Build audited: `/home/user/Game/JadeRiver` working tree (HEAD 796f089 plus the uncommitted G2a changes). The audit is read-only: no tests or builds were run.

Status key:
- **Present**: the build matches the v2 text.
- **Differs**: the build follows the old text or does something else.
- **Partial**: some of the requirement is built.
- **Missing**: nothing is built.
- **Not yet due**: v1.2+ rows. The build is at v1.1 (Act II).

Pairs that differ only in formatting are skipped. S43–S49 are audited elsewhere. The rows below cover where the existing sections now point at them.

Build facts that many rows depend on:
- **Double jump is free.** `MovementSolver.jump` allows a second full-impulse jump for anyone who has "jump" (movement_solver.gd:14; apex 244). The world builder places ledges at 110/220/320 on that assumption (tools/data/world.py:2142; docs/movement.md).
- **Surface edges are one boolean.** Each surface has a single `open_edges` flag (scripts/surface.gd:10,25; world.py:187). It is true on 224 of 232 platforms. Room JSON has no `edges`, `blocks`, `climbables`, `movers`, `volumes` or `void_altitude`. `camera` is `{y_min, y_max}` in 18 rooms.
- **No Relations or Calendar layer.** There is no Relations or Calendar state or authority and no nav graph. Karma (merit, sin, debts) sits on CultivatorState (cultivator_state.gd:46-49).
- **None of the new guided quests exist**, including the new S43 movement-art quests (grep of tools/data/story.py).

---

## The game in one page / The existing project (v0.3)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Portals entered by a context prompt or a short press-up hold (S43) | Partial | The context "Enter" shows for door and `press_up` portals (world_authority.gd:416-423; hud.gd:287-290). The press-up hold fires after 0.18 s (world.gd:224) and there is no sideways-input limit | Raise the hold to 0.3 s, require sideways input < 0.3 within 28 units, and add the "Climb" context |
| Extend v0.3 with per-side edges, blocks, climbables, movers, volumes, coyote and buffer, mantle, movement arts and a nav graph | Missing | Only standable props become support blocks (world.py:2143-2286). Everything else is absent (grep: no coyote, buffer, mantle, climbable, mover, nav) | Implement the S43 geometry kinds and solver features |

## Rules that are never broken

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Base jump never grows with stats or gear | Present | `JUMP_IMPULSE` is a const 530 (movement_solver.gd:3-4). No jump stat or affix exists in data | — |
| Reach grows only through the S43 arts | Differs | The free double jump from the Prologue (movement_solver.gd:14; player.gd:84-114). The kite quest says "Jump twice if you have to!" (data/quests.json the_runaway_kite) | Gate the air jump behind Cloud Ladder Step (QU6) with impulse 430 |
| Every room's required route fits the S43 reach table for its lowest realm | Partial | No room lint or reach contract. Ledge heights assume the free double jump (world.py:2142) | Add the room lint and a reach-contract test, then re-grade ledges |

## Conflicts already resolved

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Fall recovery returns to the last safe position, not the spawn | Present | recover_to_safe (world.gd:512-527) is called at altitude < −250 (player.gd:288) | — |
| Fall costs 5% max HP outside the Prologue, towns and safe rooms | Missing | recover_to_safe changes no pool | Apply 5% max HP (never below 1) unless the room is `safe`, a town or the Prologue |
| Back edges of platforms closed by default | Differs | `open_edges` true on all sides (world.py:187). Walking north off a roof clamps you to the ground strip's edge (zone_geometry.gd:73-81) | Per-side edges with n closed |
| Portals and ladders: context "Enter"/"Climb" or a 0.3 s hold; a plain press-up cannot trigger | Partial | Enter works. No Climb: ladders are walk-on `ladder` surfaces (zone_geometry.gd walk_target). The hold is 0.18 s | Add the climbable mode, the Climb label and the 0.3 s hold |
| Wall-Step: +88 height, 3 per airtime | Differs | One kick per airtime at 0.95 × 530 impulse, about +110 (movement_solver.gd:28-37). The data says "One kick off a wall per jump" (techniques.py:145) | Vertical speed 450, push 90 units away, 3 kicks per airtime |
| Jump scaling: "the base jump never scales; reach through the arts ladder" | Differs | The base part holds, but reach comes from the free double jump (see above) | As above |
| Flight controls: joystick for x and depth, hold Jump to rise, hold Evade to descend | Present | player.gd:270-274; hud.gd:192,205; with neither held, altitude holds (movement_solver.gd:115-127) | — |
| Pills never decay; Pill Grain means less toxicity and no resistance | Present | stats.py:297 ("Pills never decay"); grain toxicity ×0.5 (grades.json); resistance skipped for grain (inventory_authority.gd:425) | — |
| Alchemy batch set by the furnace (3/5/8/10) | Present | items.json: bronze 3, earth-vein 5, cloud-pattern 8, mystic 10; enforced at crafting_authority.gd:232-234,415 | — |
| Combat puppet from Cloud Stride 5 in a pet slot | Missing | `puppetry` at CS5 builds worker puppets only (story.py:478,934-937; workshop_page.gd:120-152) | Add a combat puppet that fills a pet slot |
| Pet button at (965, 560) | Differs | `pet_center := Vector2(975, 555)` (hud.gd:31) | Move it to (965, 560) |

## The five layers / Folders and files

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| RelationsState and CalendarState (scene-free, snapshot/restore) | Missing | scripts/simulation/state/ has no such files | Create them |
| Relations and Calendar authorities | Missing | scripts/simulation/authority/ has no relations_ or calendar_ authority | Create them |
| nav/nav_graph.gd (per-room nav graph from ZoneGeometry) | Missing | No nav/ folder | Create it |

## The intent → authority pattern (owner table)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Movement owns climbing, gliding, flight, art use and cooldowns, and the last safe position | Partial | LocalAuthority moves the flying body (local_authority.gd:18-24). The last safe position lives in the world view and is not saved (world.gd:34,486-489). The Wind Blink cooldown is in Combat (combat_authority.gd:344-351) | Move last_safe and art cooldowns into Movement state, saved |
| Progression adds pill resistance, foundation, residue, heart demon, body tier, core grade, fates, physiques, vows, Inner Arts, stances | Partial | The first four exist (cultivator_state.gd:42-50). The rest are absent | Add the fields as neutral hooks |
| Inventory adds treasure slots, loadouts, item pity and natal growth, wardrobe overrides | Partial | `treasures` ["",""] (inventory_state.gd:17). `loadouts` is an unused character field (game_character.gd:38). The others are absent | Add the loadout, pity/natal and override fields |
| Crafting adds absorbed flames, recipe fragments, experiment log, guild ranks and commissions | Partial | `crafting.flames` (crafting_authority.gd:332-338). The others are absent | Add the fields |
| Relations owns karma, alignment, Fame, affinity, bonds, grudges, bounties, missions, Fortune | Differs | merit, sin, debts and merit_used are on CultivatorState, written by Progression (cultivator_state.gd:46-49). The rest are absent | Move karma to RelationsState and add the other tracks |
| Calendar owns the world calendar, seasons, weather and rankings | Missing | — | Build CalendarState and the Calendar authority |

## Requirement / Effect / Randomness (Part 2)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Requirement kinds art_known, heart_demon_at_most, body_tier_at_least, merit_at_least, alignment_at_least, hearts_at_least, foundation_share_at_most | Missing | requirement_rules.gd:65-218 matches none of them | Add all seven |
| Effects add_heart_demon, clear_residue | Present | game_authority.gd:139,142 | — |
| Effects add_merit, add_sin, record_debt | Differs | Built as `karma` {merit, sin} and `karma_debt` (game_authority.gd:140-141) | Rename or alias to the v2 kinds |
| Effect grant_art | Differs | Only `learn_secret_art` exists (game_authority.gd:173) | Add or alias grant_art |
| Effect absorb_flame | Partial | Exists as an item use, not an apply_effects kind (crafting_authority.gd:330-339) | Expose it as an Effect |
| Effects add_residue, add_affinity, add_fame, add_alignment, grant_fate, add_pet_purity | Missing | — | Add them |
| RNG streams fortune (encounters, epiphany) and calendar; sect stream covers beast tides | Missing | CHARACTER_STREAMS and ACCOUNT_STREAMS have neither (rng_service.gd:6-7) | Add the streams |

## S02 · Unlocks and HUD reveal

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| same_stage_ok on the S43/S47 entries that share a stage (QK3, QK6, QK7, QU6, HT1) | Partial | Only HT1 `treasures` exists and carries it (story.py:463-464). No glide, talisman, air-dash or double-jump entries exist (unlocks.json has 119 entries) | Add the entries with the flag |
| Paired guided quests at QK3, QK6, QK7, QU6/QU7 and HT1/HT5 carry same_stage_ok | Partial | The HT1, HT5, QU7, BF2, BF4 and CS1 pairs carry it. The QK3, QK6, QK7 and QU6 guided quests do not exist | Add the quests |

## S04 · Cultivator state (hook fields)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| pill_resistance {family: {count, doses}} | Differs | {family: doses (int)} (cultivator_state.gd:42) | Change the shape, with a restore shim |
| foundation {pill_qp, total_qp} | Differs | {realm, total, pill} (cultivator_state.gd:43) | Rename the keys |
| residue, heart_demon | Present | cultivator_state.gd:44-45 | — |
| support_failures {realm_key: …} | Differs | Named `support_fails` (cultivator_state.gd:50) | Rename |
| body_tier, core_grade, fates, physiques, vows, inner_arts, stances, false_realm | Missing | — | Add as neutral hooks |
| Karma, alignment, fame, affinity and bonds are not on CultivatorState | Differs | merit, sin, debts and merit_used are on it (cultivator_state.gd:46-49) | Move to Relations |
| Hook fields neutral from v0.5, so no later migration | Partial | restore() gives defaults for missing keys, so old saves load, but many fields do not exist yet | Add all of them now |

## S05 · Cultivation loop

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| +1 risk step for "Foundation: hollow" | Present | progression_authority.gd:363-366 | — |
| +1 risk step per 25 heart demon | Present | progression_rules.gd:145-146; progression_authority.gd:367 | — |
| A support pill stops counting after 2 failures | Present | progression_authority.gd:349-357 | — |
| −1 risk step once per major realm per 100 merit | Present | progression_rules.gd:149-151 | — |
| +5 heart demon with 2 or more supports | Present | progression_authority.gd:415 | — |
| A flawless Cleansing clears all residue | Present | world_authority.gd:875-877; set_pieces.json clear_residue | — |
| Heart Trial: one Heart Demon add per 25 | Present | world_authority.gd:831 | — |
| The Heart Trial step sets the Core Forging grade | Missing | purity always starts at 9 (cultivator_state.gd:17) | Add the grade roll |
| Heavenly tribulation on every major breakthrough after Cloud Stride | Missing | — | Add it |
| Fate card choice at every major breakthrough | Missing | — | Add it |
| Qi Deviation on a Severe failure or a Poor-compatibility method | Missing | — | Add it |

## S07 · Offline seclusion

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Settle foundation: −5 share points and −5 residue per hour, no progress | Differs | 6%/h share and 3 residue/h (stats.py:111; progression_authority.gd:958-970) | Set both to 5/h |
| Settle foundation at BF7, visible once the share passes 20% | Differs | Always listed behind the `seclusion` unlock (cultivation_page.gd:224-230; progression_authority.gd:906) | Hide the focus until share > 20% |
| Medicinal bath focus at a Bath station (QU1, retreat rooms) | Missing | — | Add the focus and the station |

## S09 · Daos, techniques and secret arts

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Movement arts ladder: plunge, dodge dash, glide, air dash, double jump, water skimming, Wall-Step, blink, flight | Partial | Dodge dash, Wall-Step (old form), Wind Blink and flight exist (secret_arts.json). Plunge, glide, air dash and skimming are absent. Double jump is ungated | Build the missing arts and gate double jump |
| Concealment with a false realm badge | Missing | Concealment only halves aggro range (enemy_brain.gd) | Add the badge |
| Technique grade, stances and combo pairs; Inner Arts passive slots | Missing | techniques.json has no `grade`; no inner arts exist | Add them |

## S11 · StatBlock / reach

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Base jump and room geometry never scale | Present | movement_solver.gd:3-4 | — |
| Rooms are designed against the S43 reach table | Differs | Rooms use the 110/220/320 table with a free double jump at apex 244 (world.py:2142; docs/movement.md) | Re-grade against the S43 reach table |

## S12 · Combat

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Altitude band relative to the attacker | Present | hit_test (combat_authority.gd:176-189) | — |
| Bands: melee −30..+60, Qi arcs −10..+80 | Differs | Families use [0,90], [0,100] and [0,110]; the bow uses [20,110] (stats.py:228-268) | Retune the bands |
| Arrows and thrown weapons at launch altitude +58 | Partial | Player shots use +58 (combat_authority.gd:476). Enemy shots use height × 0.55 (combat_authority.gd:829) | Use +58 for all |
| Blocks and wall edges stop projectiles | Partial | Only enemy shots below altitude 60 stop, on ground-stratum blocks (combat_authority.gd:852) | Stop all projectiles on blocks and walls |
| Tier fighting rules (knockback off ledges, out-of-reach) | Missing | — | Implement S43 rules 10–11 |
| Hold Jump in the air to enter flight | Differs | A third press after the double jump takes off (player.gd:102-105) | Hold Jump while descending |
| Flight: joystick for x and depth, Jump rises, Evade descends | Present | See Conflicts | — |
| Death costs 5% of stage progress from Sage (nascent-soul escape) | Missing | Flat 10% (stats.py:101; progression_authority.gd:553) | Use 5% from Sage |
| +3 heart demon on death | Present | progression_authority.gd:565 | — |

## S13 · Enemies

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Chase along the nav graph with species movement (jump, climb, fly, drop) inside the leash | Missing | Flat x/depth chase (enemy_brain.gd:60-100) | Nav graph and chase |
| Out-of-reach rule, tier natives, knockback off ledges | Missing | All 137 spawns are on the `ground` surface | Implement them |
| beast_rank 1–9, nature, core drop 2% × rank | Missing | None of the 75 enemies has these fields | Add the data and drops |
| Rogue cultivator elites drop their visible weapon or treasure | Missing | Bandits only have a 5–6% `equipment_chance` | Add the elites |
| A zone's field boss is its Beast King | Missing | — | Add it |
| enemies.json gains movement, beast_rank, nature, core_chance, home_tier | Missing | Field survey of enemies.json | Add the fields |

## S14 · Items, inventory, equipment

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Treasure slots | Present | inventory_state.gd:17; hud.gd treasure buttons | — |
| Weapon loadouts A and B | Missing | `loadouts` is unused (game_character.gd:38) | Build the dual loadout and swap |
| Item instances gain pity, natal, natal_xp, broken, locked_affix | Missing | — | Add the fields |
| Furnaces are item instances | Partial | Furnaces are key-item tools with type-level `furnace` stats (items.json) | Per-instance furnace fields |
| S47 extensions (flying sword, natal, talismans, throwables, pity, Inherit, Salvage, affix lock, override, loadout) | Partial | Treasures, throwables, vessels and the talisman treasure exist (CHANGELOG G2a). Salvage has an authority function but no page (crafting_authority.gd:463). The rest are absent | Build the rest |
| Enhancement never destroys; only a self-detonated item is destroyed | Present | No destruction path. Self-detonation is not built | — |

## S15 · Alchemy and pills

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Choose the fire at the furnace | Present | Fire selector (G1); grades.json fires | — |
| Herb nature (hot/cold/neutral) moves the band | Missing | No `nature` in items or recipes | Add it |
| Fusion follows the recipe's role order | Missing | No `role` in recipes | Add it |
| Batch capped by the furnace | Present | See Conflicts | — |
| Pill tribulation screen and Pill Soul catch (v1.0, Heaven+) | Missing | — | Build them |
| Grain −50% toxicity and ignores resistance | Present | grades.json; inventory_authority.gd:425 | — |
| Halo +1%/24 h in a storage chest in a room of density ≥ 2, cap +20% | Differs | +5%/h, cap +50%, for bag pills during seclusion (stats.py:289; inventory_authority.gd:226-237; progression_authority.gd:973) | Move growth to storage chests and fix the rates |
| Pill Soul adds the recipe's unique effect | Differs | 50% chance of a random effect from a shared list (stats.py:300) | Give each recipe its own soul effect |
| Pills never decay | Present | stats.py:297 | — |
| Grain needs Earth, Beast or Heavenly fire; Halo and Soul need a Heavenly Flame; Nine-Dragon allows any fire | Present | grades.json fires; crafting_authority.gd:315 | — |
| Marks 0–9 at +2% each | Present | grades.json marks; inventory_authority.gd:222 | — |
| 5% of toxicity becomes residue; lifetime resistance | Present | stats.py:109-111; progression_rules.gd:120-142 | — |
| Auto-refine gives 25% XP | Present | crafting_authority.gd:433 | — |
| Conflicting herbs blast the furnace | Missing | No conflict data or code | Add herb_conflicts and the blast |
| S44 extensions: guild, fragments, experiments, poison pills, oils, liquids, baths, Qi Flow Pill | Missing | Only eating herbs raw is built (G1) | Build them |

## S16 · Crafts

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Harvest timing tap (a perfect keeps full age and may give a seed; a miss drops an age tier) | Missing | Gather is a channel only | Add the tap |
| Guardians, ripening windows and seasons on rare nodes | Missing | — | S45 |
| Seeds from shops and perfect harvests; rare seeds from secret realms | Missing | The only seed is `evergreen_heart_seed` (items.py:295) | Add seeds |
| Field grades, Spirit Soil, spring water, transplanting, Dew Vial, racks, raids | Missing | — | S45 |
| Talisman craft at QK6 (Old Scribe Bai, stroke trace) | Missing | The Revival Talisman is still inscribed under Formations | Build the craft |
| Combat puppet from CS5 in a pet slot | Missing | See Conflicts | — |

## S17 · Rooms, portals and world objects

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| use_portal by the context button or a 0.3 s hold | Partial | See Conflicts (0.18 s) | 0.3 s |
| Up to 4 tiers; Lower Pit, Echo Cliffs and Crane Cliffs get taller camera bounds | Missing | Every room is 480 tall. sq_lower_pit, wg_echo_cliffs and cc_* have no `camera` | Add camera.bounds |
| Fall recovery to the last safe position, spawn as fallback | Present | world.gd:512-527 | — |
| Safe position recorded only after 0.3 s on a surface ≥ 24 from an open edge | Differs | Recorded every frame on any surface (world.gd:265,486-489) | Apply the S43 rule 6 filter |
| Room data gains edges, blocks, climbables, movers, volumes, camera | Missing | Survey of the room JSON keys | Extend the schema and generator |
| Every room follows the verticality rules and its Part 8 row | Partial | No lint. Heights are off-standard (lf_village roofs at 124/128/168) | Lint, then rebuild rooms |
| use_link extended with context, hold and a real climb mode | Missing | Ladders are walk-on surfaces | Climb mode |
| Block kinds (crate, barrel, cart, fence, wall, rock, pillar, stall, well, lantern) | Partial | Standable props get tops 22–86, not in a blocks[] list; none are breakable (world.py:2143-2147) | Build blocks[] with standard heights |
| Herb patch carries S45 flags | Missing | — | S45 |

## S19 / S20 / S22 / S23

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| S19: affinity, gifts, bonds, grudges, bounties, debts and missions belong to Relations | Differs | Debts are on Progression. The rest do not exist | Relations authority |
| S20: Fame and alignment tracks, sect role variants, guilds | Missing | — | S48/S49 |
| S22: pet depth fields from v0.9 (purity … lock) | Missing | The pet dict has uid, species, name, level, xp, bond, role, stage, rarity, branch and traits only (pet_authority.gd:88-90) | Add the fields |
| S22: pets follow across tiers and blink back when stranded | Missing | Allies are forced to altitude 0 and teleport only beyond 700 (ally_brain.gd:77-78) | Nav follow and a 2 s blink |
| S22: a beast downed with an Offering on quick-use is subdued at 1 HP for 10 s | Missing | — | Add it |
| S22: bloodline suppression in taming; demonic beasts need a Purifying Offering; Hollowed must be cleansed first | Missing | tame_chance (pet_authority.gd:413-420) | Add the terms |
| S22: Grievous Wound after 3 knockouts in 5 minutes | Missing | Only a 60 s retreat (pet_authority.gd:253) | Add it |
| S23: auto-hunt (v1.0), idle-eligible rooms only | Missing | — | Add it |

## S24 · HUD

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Context labels Climb and Enter, only while no enemy is aggroed | Partial | Enter exists; no Climb. The context is suppressed by any hostile within 150 (hud.gd:275,281-285), not "aggroed within 400" | Add Climb and the aggro-within-400 test |
| In-fight Context button at (1165, 500) r26 | Missing | — | Add it |
| Jump: a new press in the air is double jump or Wall-Step; hold while descending to glide/fly; toward camera to drop | Differs | The second press is always a double jump; the third press takes flight at CS1 (player.gd:84-114) | Implement the S43 control table |
| Pet button at (965, 560): command wheel, mount, Pet Bag | Differs | At (975, 555), it opens the Spirit Animals page (hud.gd:31,214) | Move it and build the wheel |
| Treasure 1 at (887, 470) and Treasure 2 at (799, 470); HT1 and SA1 | Differs | The positions are (711, 555) and (711, 470) (hud.gd:34). The stages match | Move them |
| Weapon swap button at (1240, 515) from HT1 | Missing | — | Add it |
| Auto-hunt toggle under the minimap icon row | Missing | — | Add it |
| Guard: tap in the air for an air dash (QK7); hold in flight to descend | Partial | Descend works (hud.gd:203-205). An air tap is Wind Blink from SA5 only (combat_authority.gd:344) | Add Swallow Dart |

## S25 / S30 / S36 / S37 / Ordering

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| S25: spirit-stone mines (v1.1) | Missing | — | Add them |
| S25: defence-wave code also runs town Beast Tides | Missing | — | Add them |
| S25: Beast Pavilion hosts the Core Exchange and the Feeding Trough | Missing | beast_pavilion exists without them (sect_buildings.json) | Add both |
| S30: F context | Present | hud.gd:361 | — |
| S30: K descends in flight | Present | player.gd:273 | — |
| S30: Z and X treasures, R weapon swap | Differs | Treasures are on R and T (hud.gd:368-369); there is no swap | Rebind |
| S30: S+Space drop, S+J plunge, K air dash | Missing | — | Add them |
| S30: air attacks keep ×0.8 speed, one hit, +10% | Differs | ×0.3 in the air too (combat_authority.gd:73) | Separate the air factor |
| S36: camera clamps to camera.bounds, follows the support surface, looks down at drops | Differs | It clamps y to y_min/y_max (default 470–600) and follows position.y − 110, the jump arc (world.gd:237-250) | Implement S43 rule 13 |
| S37: world calendar (tides, rifts, auctions, births, secret realms), seasons and weather | Missing | — | Calendar authority |
| S37: notifications "secret realm opens" and "beast tide in 1 h" | Missing | account_state.gd default_settings | Add both |
| Ordering: Calendar ticks after World | Missing | game_authority.gd:224-229 | Add the step |

## Unlock timeline additions

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Prologue: Jump, ladders and Drop Through at the Runaway Kite; sprint always on; mantle always on | Partial | Jump works (story.py:373). The ladder is a walk-on surface. Sprint is not gated in code (player.gd). No drop-through or mantle | Add drop-through, mantle and the climb ladder |
| BF4: Plunge (Outer Trial) and the harvest timing tap | Missing | outer_trial is 3 spars (story.py:709-714) | Add both |
| BF7: Settle foundation shown once the share passes 20% | Differs | Always shown | Gate it |
| QK3: Falling Leaf Glide ("Leaf on the Wind") | Missing | — | Add it |
| QK6: Talismans (Old Scribe Bai); rogue cultivator elites | Missing | — | Add them |
| QK7: Swallow Dart | Missing | — | Add it |
| QK8: Alchemist Guild exam and commission board (with "Batch Work") | Partial | batch_work opens auto-refine; there is no guild | Add the guild |
| QU1: Inner Arts 2 slots; medicinal bath | Missing | — | Add them |
| QU6: Cloud Ladder Step | Differs | Double jump works from the Prologue | Gate it |
| QU8: Water Skimming | Missing | — | Add it |
| HT1: Treasure slot 1, weapon swap, natal treasure, Inner Arts 3 | Partial | Only the treasure slot works, via Lines in the Sand (story.py:462-464) | Add the rest |
| HT4: Wall-Step redefined, "Between Two Walls" | Differs | Granted automatically at HT4, old behaviour (story.py:499-501) | Add the quest and the new numbers |
| HT9: talisman treasure from Elder Hu; Core Forging checklist | Differs | The talisman comes at SA5 in the_mentors_gift (story.py:962-965). There is no checklist | Move the talisman; add the checklist |
| CS1: Flight and heavenly tribulation | Partial | Flight works; no tribulation | Add the tribulation |
| CS5: combat puppet in a pet slot | Missing | — | Add it |
| SA1: Treasure slot 2, Inner Arts 4, command capacity 2 | Partial | Only slot 2 works (story.py:482) | Add the rest |
| SA3: Nine-Dragon Cauldron (sealed vault) | Differs | Reward at HG3 from Alchemist Fen (story.py:1146-1148) | Move it to the SA3 vault |
| v1.0 world: Calendar page, capped secret realms, tides, births, NPC affinity and bonds, grudges and bounties, Trial Tower, activity chests, auto-hunt | Missing | — | S49 |

## File list additions

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| movement.json (every S43 constant) | Missing | Constants are in movement_solver.gd and stats.json `move` | Create it |
| flames.json, herb_conflicts.json, guilds.json | Missing | Flames are items; fires are in grades.json | Create them |
| seasons.json, garden.json | Missing | — | Create them |
| pet_skill_books.json, beast_kings.json | Missing | — | Create them |
| treasures.json, talismans.json, salvage.json, legendary_chains.json | Differs | Treasures are embedded in items.json `treasure`; the other three are absent | Split out or record the deviation |
| fates, physiques, body_tiers, vows, inner_arts, tribulations, combos .json | Missing | — | Create them |
| karma, bonds, factions, calendar, fortune_deck, rankings, tower, activity .json | Missing | Karma constants are in stats.json `karma` (stats.py:117) | Create them |

## Data examples: rooms/<id>.json, account.json, char_<slot>.json

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Surfaces carry `edges` {n,s,e,w} and the new kinds (raft, stilt) | Missing | Only `open_edges` | Extend the schema |
| blocks[] (base, top, kind, breakable) | Missing | — | Add it |
| climbables[] | Missing | — | Add it |
| movers[] | Missing | — | Add it |
| volumes[] with an alt range | Differs | `areas` of kind shallows/river with no alt range (lf_reed_shallows.json) | Migrate to volumes |
| camera {bounds, look_ahead} and void_altitude | Differs | {y_min, y_max} in 18 rooms; void fixed at −250 (player.gd:288) | Adopt the new keys |
| Objects placed by `surface` | Partial | Ledge objects use `alt` | Add the surface field |
| Reed Shallows example (stilt hut with ladder, raised path ≥ 40% of width) | Differs | Three driftwood branches at 60–90; no hut or ladder | Rebuild the room |
| account.calendar {seed, season, events, weather, rankings} | Missing | account_state.gd:46-56 | Add it (empty block) |
| account.experiments, wardrobe_unlocked, activity | Missing | — | Add them |
| char.movement {arts, last_safe} | Missing | No block; last_safe is unsaved view state | Add it |
| char.relations block | Missing | Karma is in cultivator | Add it |
| inventory treasure_slots, loadout {a,b,active}, appearance_override | Partial | `treasures` only (inventory_state.gd:84) | Rename or add |
| crafting.flames, recipe_fragments, guild, commissions | Partial | Only flames exists | Add the others |
| mount, pet_bag | Missing | Mount is a role of the active pet | Add them |
| Item fields pity, natal(_xp/_level), broken, locked_affix, awakened; furnace heat_stability, batch_cap, impurity_filter, element, yield_chance | Missing | Furnaces use band/batch/filter/yield at type level | Add the fields |
| Pills keep marks on the stack | Present | crafting_authority.gd:268; inventory_page.gd:88 | — |
| Pet fields from S46 | Missing | pet_authority.gd:88-90 | Add them |
| Hook rule: neutral fields written from the milestone that creates the class | Differs | Fields arrive with each G-phase; the movement, relations and calendar blocks are absent | Write all hooks now |

## v0.4 · Fists and Rooms

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Portal entry by context or a 0.3 s hold | Partial | 0.18 s hold | 0.3 s |
| Ladders and ropes as S43 climbables | Missing | — | Add them |
| Fall recovery per S43 rule 6 | Partial | The last safe position works. No HP cost, no safe-record rule; void is fixed at −250 | Complete rule 6 |
| Per-side edges with back edges closed | Differs | See Conflicts | — |
| Blocks: stand on, jump over, slide along | Partial | Standable props only | blocks[] |
| Climb mode (stop, jump off, knock-off, climb-speed stat) | Missing | — | Add it |
| Coyote 0.10 s and jump buffer 0.12 s | Missing | — | Add them |
| Ledge mantle | Missing | — | Add it |
| Drop Through | Missing | — | Add it |
| Air-attack speed ×0.8 | Differs | ×0.3 | Fix it |
| Movers; water_shallow, water_deep, bounce and crumble volumes | Partial | Shallows ×0.7 exist as `areas` (player.gd:315-324). deep_water exists as a hazard (Drowned Grotto). No movers, bounce or crumble | Add the rest |
| Camera bounds with support-based follow | Differs | See S36 | — |
| Landing ring | Partial | shadow.gd projects a shadow; there is no ring | Add the ring |
| movement.json | Missing | — | Create it |
| Rooms built to their verticality rows (rooftops, crates, ladders) | Partial | lf_village has roofs 88–312, a hall ladder and the kite at 176. The other rows are unchecked | Lint |
| S43 measured-facts suite and room lint with the engine checks | Partial | rules_tests.gd movement_suite (647-716) checks apex 122 and ledge reach. No lint | Add the lint |
| "No automatic rooftop transport links" becomes "climbables load from data" | Differs | Unchanged (engine_tests.gd:65) | Update the check |
| Room-lint suite | Missing | — | Add it |
| Acceptance: walking north off any roof never leaves the room | Partial | You fall to the ground edge, not blocked (zone_geometry.gd:73-81) | Close the back edges |
| Acceptance: a 60 crate jumped at walk speed; a 110 block stood on | Differs | Block tops are 22–86; there is no 110 block (world.py:2143-2147) | Standard block heights |
| Acceptance: every v0.4 room passes the lint; kite, Old Net and Straw Sandals reachable as catalogued | Partial | The kite is reachable with single jumps; no lint | Lint |

## v0.5 · Cultivation Core

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Hook fields: CultivatorState set, movement block, relations block, account calendar | Partial | Cultivator subset only (see S04) | Add the rest |
| Requirement and Effect kinds exist even if unused | Missing | See Part 2 | Add them |
| Foundation share counts pill and core QP | Present | progression_rules.gd:131-134 | — |
| "Foundation: hollow" computed and shown in the Breakthrough dialog | Present | progression_authority.gd:363-366 | — |
| Settle foundation exists but is hidden | Differs | Visible | Gate it |
| Acceptance: a v0.5 save round-trips every hook field | Partial | save_suite exists; many fields are absent | A depth-hooks test |

## v0.6 · Combat and Monsters

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Tier combat: relative bands, projectile stops, knockback off edges, air attacks, Plunge | Partial | Only relative bands and partial stops | Complete it |
| Enemy movement data, nav graph, chase, out-of-reach, tier natives (Pebble Imp, Reed Frog) | Missing | pebble_imp and reed_frog have no movement or home_tier; they spawn on ground | Add them |
| beast_rank, nature, core_chance on every enemy | Missing | — | Add them |
| Acceptance: no melee monster farmed safely from a roof (2 s / 6 s) | Missing | — | Out-of-reach rule |
| Acceptance: pets and companions follow across tiers or blink after 2 s | Missing | ally_brain.gd:77-78 | Add it |

## v0.7 · The Prologue

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| The Runaway Kite teaches ladders, the 88 and 176 roofs, and Drop Through | Partial | Hall ladder, hall roof 88, inn roof 176 and the kite at alt 176 are in lf_village.json. No Drop Through | Add drop-through |
| Race to the Tower uses the Village Square rooftops | Differs | A ground sprint to a ground-level bell (tower_bell at [3590,710], no alt) | Route it over the roofs |
| The night event uses roofs as the safe tier | Partial | lf_village_night has 4 roofs (88–168). Safety is incidental; no out-of-reach rule | Design and test it |
| Entry Trials match their verticality rows (moving planks; ropes; crumbling ledge) | Differs | Both trials are identical static steps at 60/120/180 (sf_trial_jade.json, sf_trial_cloud.json) | Rebuild them |
| Fairground drum bounce | Missing | sf_fairground has decks at 110/220 only | Add the bounce volume |
| Daily rooftop thief chase in Stoneford | Missing | — | Add it |
| Acceptance: ladders, a roof chain, a crate jump and Drop Through before the night | Partial | No drop-through | — |

## v0.8 · Valley I

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| S44 rules (resistance, foundation, residue, Settle, no decay, herb nature and roles, eat raw, auto-refine 25%, guild) | Partial | All built except herb nature and roles and the guild. Settle rates differ | Add those |
| Harvest tap, seed chance and seed sources | Missing | — | Add them |
| Root names | Missing | Aptitudes are hidden ±15% | Add them |
| Talisman craft Apprentice (tracing canvas, Revival Talisman moves here); blood-drop bind animation | Missing | A timed bind bar exists | Add them |
| S43 arts: Plunge, Glide, Swallow Dart | Missing | — | Add them |
| v0.8 rooms: Quarry lift and falling rocks; Grey Pools rafts and lily pads; Bamboo vines; Mudwater stockade and wine-jar shelves | Partial | Falling rocks work (sq_quarry_rim). The others are plain ledges (rm_grey_pools, bg_whispering_bamboo, mh_stockade) | Add movers, bounce and climbables |
| Quest auto-path over the room graph using known arts | Missing | `target_room` is used only by the tracker (quest_authority.gd:489) | Add it |
| Acceptance: a pill-fed run shows resistance, hollow and residue, and Settle repairs it | Present | rules_tests.gd g1_suite (718+) | — |
| Acceptance: auto-path reaches Act I ch.1–3 objectives | Missing | — | — |

## v0.9 · Valley II

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| S44: Earth Fire (Rapids Terraces vent), Beast Fire, furnaces with caps, marks, blast, oils, baths, Cleansing clears residue | Partial | All built except the blast, oils and baths (earth_vent in wg_rapids_terraces.json) | Add those three |
| S45 garden and herb depth | Missing | — | Add it |
| S46 pet depth | Missing | Only a rename intent exists | Add it |
| S47: slot 1 with Bell, Pagoda, Mirror, Seal, Cauldron, Banner, Gourd | Present | CHANGELOG G2a; items.json treasure entries | — |
| S47: Sword Release and Intent, talisman Adept, pity, Inherit, Salvage page, dual loadout, rogue cultivators | Missing | The talisman treasure and throwables are built | Add the rest |
| S48: heart-demon rules | Present | progression_authority.gd:168,415,565,710-723,820 | — |
| S48: fates, Qi Deviation, Inner Arts, technique grades, stances, combos, Copper Body, sect roles, quick-deploy | Missing | — | Add them |
| S49: karma ledger state | Present | cultivator_state.gd:46-49 (wrong owner, see Part 2) | — |
| S43 arts: Cloud Ladder Step (QU6), Water Skimming (QU8), Wall-Step (HT4, Echo Cliffs) | Differs | Double jump is free, Wall-Step uses the old form, no skimming | Rebuild them |
| v0.9 rooms: Serpent's Shallows rising water, Drowned Shrine lanterns and well, Echo Cliffs shafts, Sword Court poles | Missing | dw_serpents_shallows has 3 rocks at 100. wg_echo_cliffs has ledges at 100–300 and no wall shaft. cm_sword_court has one roof at 110 | Build the rows |
| Acceptance: a pill-forced Heart Trial shows adds; a fate card at each major | Partial | Adds work; no fates | — |
| Acceptance: treasure, flying sword, talisman and pity under a fixed-seed replay | Partial | Treasures and the talisman are covered in g2_suite | — |
| Acceptance: every optional "later" ledge reachable with its named art | Missing | — | — |

## v1.0 · The Complete Valley

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Flight mode with S43 controls, QI drain, altitude limits, no-flight rooms | Partial | All built except take-off, which is a third press (see S12) | Fix take-off |
| First Heavenly Flame is the Mist Lantern Flame (Weeping Lantern, Forgotten Monastery) | Differs | The valley flame is the Cold Lamp from the Drowned Abbot (items.py:63) | Rename or move it |
| Pill cloud; pill tribulation; Soul catch; fragments and Deduce; Experiment; poison pills; liquids; Qi Flow Pill | Partial | Only the pill cloud is built (G1) | Add the rest |
| S45 v1.0 (seasons, transplanting, Dew Vial, treasure births, trials, Sense countdown) | Missing | — | — |
| S46 v1.0 (awakenings, suppression, Equal Contract, command capacity, marrow pill, skill books, gear, Beast Bag, Mount slot with Riverstone Ox and Cloud Stag, Beast Kings, weekly Tide) | Missing | pets.json has 7 species, none of them mounts | — |
| S47 v1.0: slot 2, natal, affix lock, override, shattered relics, spirit depth, flight vessels | Partial | Slot 2 and vessels are built (G2a) | Add the rest |
| S48 v1.0: tribulation, Core grade, physiques, epiphany, Blood Burning, Self-Detonation, false realm, Killing Intent, soul line | Missing | — | — |
| S49 v1.0: Relations page, Calendar, fortune, phenomena, lifespan, Trial Tower, activity chests, auto-hunt, forge guild | Missing | Phenomena are partial (world.gd spiral and ring) | — |
| Acceptance: calendar deterministic across devices; capped secret realm refuses an over-realm character | Missing | — | — |
| Acceptance: every valley room passes the lint; "Paths Above" ledges reachable | Missing | — | — |

## v1.1 to v1.5 / v2.0

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| v1.1 (built version) additions: alignment, the four paths, Fame, rankings, territory and mines, mortal kingdom, weather, teahouse and leisure, Blood Contract, fusion, pet breakthroughs and Pet Core, Beast Arena and Grove, sword swarm, imitation relics, awakening, sabre/flute/fan, Formation guild, Dew Vial 10,000 y, soul escape, Azure Heavenly Flame, ice traction | Missing | Fragments exist: Blood Dao stat tiers, Stoneford teas, `cold` hazard. The Act II flames are Sunscar Throne Ember and Comet Tail, not Azure | Plan into Act II |
| v1.2 row | Not yet due | — | — |
| v1.3 row | Not yet due | — | — |
| v1.4–v1.5 row | Not yet due | — | — |
| v2.0 row and acceptance | Not yet due | — | — |

## Test suites

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Traversal baseline (measured facts, coyote and buffer at several frame rates, blocks, mantle, climb, drop, each art, movers in replay) | Partial | movement_suite covers apex, ledge reach, crate top and Wall-Step once | Extend it |
| Room lint (S43 rule 14) | Missing | data_validation checks ledge chests and reachability only | Add it |
| Reach contract | Missing | — | Add it |
| Depth hooks (S44–S49 fields round-trip; no early reads) | Missing | — | Add it |

## Forbidden patterns

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| No stat, item or buff raises the base jump | Present | None found | — |
| No platform back edge drops into the void | Partial | Falls clamp to the ground edge, not the void, but back edges are open | Close them |
| No required route needs an art above the room's lowest realm | Partial | Not verifiable without a lint. Kite route checked: it is fine | Lint |
| No lifespan clock, stamina gate, pet death, destructive enhancement, shop aptitude pill, decay, or unrestricted auto-battle | Present | gap_audit.md stay-out table; pets retreat (pet_authority.gd:253) | — |
| No alignment or karma hard gate on a core breakthrough | Present | Merit only removes a risk step (progression_rules.gd:149-151) | — |

## Glossary

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Tier, block, climbable, mover, volume | Partial | "block"/"support" is used; the rest are absent | — |
| Movement arts names | Partial | Dodge Dash, Wall-Step, Wind Blink and Flight exist. Plunge, Falling Leaf Glide, Swallow Dart, Cloud Ladder Step and Water Skimming do not | — |
| Paths Above collection page | Missing | — | — |
| Pill resistance, foundation share, residue | Present | Cultivation Heart tab (G1) | — |
| Heavenly Flame, Earth Fire, Beast Fire | Present | grades.json fires | — |
| Heart demon, tribulation, Core Forging grade, fate card | Partial | Only the heart demon exists | — |
| Bloodline purity, contract, Beast King, Beast Tide | Missing | — | — |
| Treasure slot, natal treasure, Sword Release, Sword Intent | Partial | Only the treasure slot exists | — |
| Merit, sin, debt, alignment, Fame, hearts, Dao Companion | Partial | Merit, sin and debt exist | — |

## Secret arts / Guided unlock quests

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Wall-Step: HT4 via "Between Two Walls" (Echo Cliffs, both sects); +88 and 90 away; 3 kicks | Differs | Auto-granted at HT4 (story.py:499-501). One kick, about +110 (movement_solver.gd:28-37) | Rebuild it |
| BF4 Outer Trial: plunge onto 2 marked targets plus 3 spars; Plunge usable from acceptance | Differs | Spars only (story.py:709-714) | Add the objective and the art |
| QK3 "Leaf on the Wind" | Missing | — | Add it |
| QK6 "Ink and Paper" | Missing | — | Add it |
| QK7 "Swallow Dart" | Missing | — | Add it |
| QU6 "Cloud Ladder" | Missing | — | Add it |
| HT1 "A Treasure in Hand" (Elder Hu or Sung; Practice Bell 3 uses in one fight; one weapon swap) | Differs | Treasure slot 1 comes from the formations quest Lines in the Sand with the Stilling Bell (story.py:462-464,876-881) | Add the quest and move the grant |
| HT4 "Between Two Walls" | Missing | — | Add it |

---

## Counts

| Status | Rows |
|---|---|
| Present | 43 |
| Differs | 50 |
| Partial | 60 |
| Missing | 128 |
| Not yet due | 4 |
| **Total** | **285** |

A single row may bundle several related items. Where a row covers a mixed bundle, its status is the weaker one.

## Top 25 Differs and Missing, in priority order

1. **Free double jump.** Anyone with "jump" gets a second jump at full impulse, apex 244 (movement_solver.gd:14). Gate it behind Cloud Ladder Step (QU6) with impulse 430 (apex ~202), then re-grade the 220 ledges (world.py:2142).
2. **Open back edges.** Each surface has one `open_edges` flag, true on every side. Build per-side `edges` {n,s,e,w} with n closed by default, through the schema, the generator and the solver.
3. **Room schema.** Rooms have no blocks[], climbables[], movers[], volumes[], camera.bounds or void_altitude. Extend the rooms JSON, world.py and ZoneGeometry.
4. **Ladders and portals.** Ladders are walk-on surfaces, with no climb mode and no "Climb" context. The portal hold is 0.18 s with no sideways limit (world.gd:224). Build a climb mode, the Climb label and a 0.3 s hold with sideways input < 0.3.
5. **Fall recovery.** A fall costs nothing, and the safe position is recorded every frame on any surface. Add the 5% max HP cost outside safe rooms and record only after 0.3 s standing ≥ 24 units from an open edge.
6. **Wall-Step.** It uses the old form: one kick, about +110, granted automatically at HT4. Change it to vertical speed 450 (+88), a 90-unit push away from the wall and 3 kicks per airtime, taught by the "Between Two Walls" quest.
7. **Missing arts.** Plunge, Falling Leaf Glide, Swallow Dart, Water Skimming, Drop Through, ledge mantle, coyote time and the jump buffer are all absent. Add them with their unlock entries and guided quests: Outer Trial plunge, "Leaf on the Wind", "Swallow Dart", "Cloud Ladder", "Between Two Walls".
8. **Flight take-off.** Flight starts with a third press after the double jump. It should start by holding Jump while descending, which glides below CS1. Flight controls are otherwise right.
9. **Enemy traversal.** There is no nav graph, enemy movement data, graph chase, out-of-reach rule (2 s and 6 s) or tier natives. All 137 spawns are on ground, and enemies.json lacks movement, beast_rank, nature, core_chance and home_tier.
10. **Camera.** It clamps y to y_min/y_max and follows the jump arc (world.gd:237-250). Use camera.bounds with look-ahead, follow the support surface, look down at drops, and give Lower Pit, Echo Cliffs and Crane Cliffs taller bounds.
11. **Relations and Calendar layers.** RelationsState, CalendarState, both authorities and nav/nav_graph.gd are missing. Karma (merit, sin, debts) should move off CultivatorState into Relations.
12. **Save hooks.** Fix the key shapes: `pill_resistance` should be {count, doses}, `foundation` should be {pill_qp, total_qp}, and `support_fails` should be named `support_failures`. Add the neutral fields body_tier through false_realm. Add the char `movement` and `relations` blocks, the account `calendar`, experiments and activity, and the inventory treasure_slots, loadout {a,b,active} and appearance_override. This avoids later migrations.
13. **Requirement kinds.** Add art_known, heart_demon_at_most, body_tier_at_least, merit_at_least, alignment_at_least, hearts_at_least and foundation_share_at_most.
14. **Effect kinds.** Add grant_art, add_residue, add_affinity, add_fame, add_alignment, grant_fate and add_pet_purity. Alias `karma` to add_merit/add_sin, `karma_debt` to record_debt, and expose absorb_flame as an Effect.
15. **HUD positions.** Move Pet from (975, 555) to (965, 560); it currently overlaps skill slot 2. Move the Treasure buttons from (711, 555)/(711, 470) to (887, 470)/(799, 470).
16. **HUD and keyboard gaps.** Add the in-fight Context button (1165, 500), the Weapon swap button (1240, 515) and the auto-hunt toggle. Hide context only while an enemy is aggroed within 400, not whenever any hostile is within 150. Rebind treasures from R/T to Z/X and put weapon swap on R. Add S+Space drop, S+J plunge and K air dash.
17. **Dual loadout and HT1 quest.** Build the dual loadout with weapon swap and the natal flag at HT1 through "A Treasure in Hand" (Practice Bell). Treasure slot 1 currently rides on the formations quest.
18. **Combat numbers.** Melee should be −30..+60 and Qi arcs −10..+80; they are [0,90]–[0,110]. Blocks and walls should stop all projectiles. Enemy shots should fly at +58. Air attacks should keep ×0.8 speed, not ×0.3.
19. **S48 breakthrough hooks.** Add heavenly tribulation from Cloud Stride, a fate card at each major breakthrough, Qi Deviation and the Core Forging grade set in the Heart Trial. Death should cost 5% from Sage.
20. **Settle foundation.** Change the rates from 6%/h and 3 residue/h to 5 and 5 per hour, and hide the focus until the pill share passes 20%. Add the medicinal bath focus at QU1.
21. **Pill Halo and Pill Soul.** Halo should grow +1% per 24 h in a storage chest (density ≥ 2, cap +20%); now it grows +5%/h in the bag, cap 50%. Pill Soul should add the recipe's own unique effect, not a random shared one.
22. **Unlock placement.** The talisman treasure comes at SA5; move it to HT9. The Nine-Dragon Cauldron comes at HG3; move it to the SA3 sealed vault. The valley Heavenly Flame should be the Mist Lantern Flame; the build has the Cold Lamp. Add talisman craft at QK6 (Old Scribe Bai) and the combat puppet at CS5.
23. **Traversal content.** The Entry Trials are identical static steps; give them moving planks, ropes and a crumbling ledge. Add the Fairground drum bounce, the Stoneford rooftop thief chase, Race to the Tower over the roofs, and the Reed Shallows stilt hut and ladder. Build the v0.8/v0.9 room rows (rafts, lily pads, vines, rising water, Echo Cliffs shafts, Sword Court poles).
24. **Pets and companions.** They must follow across tiers and blink after 2 s; ally_brain.gd:77-78 forces altitude 0. Add the S22 taming changes: subdue at 1 HP, bloodline suppression, the Purifying Offering and the Grievous Wound.
25. **Tests and heights.** Add the room lint, reach-contract and depth-hooks suites. Rename "No automatic rooftop transport links" to "climbables load from data" (engine_tests.gd:65). Standardise block heights to 40/60/80/110; they are 22–86 now (world.py:2143-2147).
