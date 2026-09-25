# Architecture

Jade River is one simulation with many small owners. Every piece of game state has exactly one
owner (an *authority*); everything else asks that owner to change it by sending an *intent*, and
learns about changes by listening to *events*. The same structure is what a future server would run.

## The five layers

| Layer | Where | Holds | Rule |
|---|---|---|---|
| Data | `data/*.json`, `data/rooms/`, `data/dialogue/`, `data/strings/` | Every number, name, room, quest, recipe, loot table | Read-only after boot; built by `tools/data/`; loaded by `ContentDB` |
| State | `scripts/simulation/state/` | `GameCharacter`, `CultivatorState`, `InventoryState`, `QuestState`, `ResourcePool`, `StatBlock`, `AccountState`, `EnemyState`, `RoomRuntime` | Plain objects with stable IDs and primitives; no Nodes, scene paths or Callables; snapshot/restore to the v3 save |
| Rules | `scripts/simulation/rules/`, `scripts/core/requirement_rules.gd` | `StatRules`, `CombatRules`, `ProgressionRules`, `LootRules`, `HazardRules`, `RequirementRules` | Pure functions of state and data; randomness only through an `Rng` stream passed in |
| Authorities | `scripts/simulation/authority/` | One per system (below) | The only writers of their state; validate intents; emit events |
| Presentation | `scripts/*.gd`, `scripts/presentation/`, `scripts/ui/`, `scripts/shell/` | World scene, views, HUD, pages, shell screens, audio | Draw state and send intents; never change HP, items, progress, currencies or unlocks |

## Autoloads

`ContentDB` (data), `GameEvents` (event queue), `Clock` (time: every rule takes time from here or as an
argument), `Rng` (named, saved random streams), `Unlocks` (system unlocks and HUD reveal), `Saves`
(v3 save format, migrations, `.bak` recovery), `Game` (the GameAuthority facade), `Audio`, `Notifier`,
and `Wardrobe` (the appearance catalogue from v0.13).

## Intent → authority → event

```
Presentation ──Game.submit({"type": "use_item", "index": 3})──▶ GameAuthority
      ▲                                                          │ routes by type
      │                                                          ▼
      │                                               InventoryAuthority.handle()
      │                                               validate → change own state
      │                                               emit("item_used", {...})
      │                                                          │
      └──── pages/HUD redraw on events ◀── GameEvents.flush() ◀──┘
                                           QuestAuthority advances objectives
                                           AchievementAuthority counts
                                           Unlocks re-evaluates triggers
```

`Game.tick(delta)` advances the simulation in a fixed order: Combat → Progression → Enemies → World →
the other authorities → deliver events → unlocks re-evaluate → save checkpoint. The world scene calls it
each physics frame; the tests call it directly without any scene.

| Authority | Owns |
|---|---|
| `CombatAuthority` | Pools (HP, QI, Soul, Composure, Hollowing), hits, techniques, guard and dodge, statuses, death and revival |
| `ProgressionAuthority` | Realm, progress, breakthroughs, methods, meridians, body level, Daos and mastery, purity, stability, injuries, seclusion |
| `EnemyAuthority` + `EnemyBrain` | Spawning, monster AI, boss phases, fleeing story bosses |
| `WorldAuthority` | Rooms, portals, objects, loot on the ground, room events, shrines, Spirit Sense |
| `InventoryAuthority` | Bag, key items and tools, equipment, quick-use; routes system items (appraise, incubate, tame) to their owners |
| `QuestAuthority` | Quests, flags, dialogue trees, daily missions, set pieces, quest drops |
| `EconomyAuthority` | Currencies, shops, buyback, exchange |
| `CraftingAuthority` | Recipes, professions, gathering, fishing, cooking, alchemy, the forge, array plates |
| `WorkshopAuthority` | Appraisal, formations, infirmary healing, puppets, manual restoration, teaching |
| `TrainingSectAuthority` | Training sect membership, rank, contribution |
| `SectAuthority` | Your own sect: buildings, disciples, expeditions, defence raids |
| `PetAuthority`, `CompanionAuthority` | Spirit animals (starter, taming, eggs, bloodline, contracts, the party up to the command capacity) and AI companions fighting beside you |
| `AccountAuthority`, `MailAuthority`, `AchievementAuthority` | Slots and idle tasks, letters with attachments, achievements and titles |
| `CalendarAuthority` | The world calendar (S49, account level): world events from the seeded, pure `CalendarRules` schedule, the season, the weather and its effects, the spatial rift, Spirit Fruit births and the Herb Terraces trial |
| `RelationsAuthority` | What the world remembers of each character (S49): the karma ledger (merit, sin, named debts), the righteous-demonic alignment, personal Fame and young masters' challenges (deeds come from karma.json); NPC hearts, gifts and keeper discounts; bonds (Dao Companion, sworn siblings, master) from bonds.json; grudges, hunters, bounties and mercy from factions.json |

## Unlocks and the HUD

`data/unlocks.json` lists every system with its trigger (usually a realm), the guided quest that
teaches it and the HUD elements it reveals. When the trigger holds, the quest is offered; accepting it
unlocks the system. The HUD shows a button only after `Game.is_revealed("hud:<element>")`. This is
why the QI bar is invisible until Bone Forging 7 and the weapon row absent until the Weapon Hall.

## Saves

Format v3: `account.json` plus `char_<slot>.json`, written through `RepositoryLocal` (temp file, `.bak`,
rename). `SaveService` migrates v1/v2 `disciples.json` slots into v3 characters. Additive fields default
on restore (eggs, workshop state), and tools found in old bags move to the key-item pouch.

## Data builders

`tools/data/*.py` are authoring aids that keep formula-driven tables consistent (realm ladder,
equipment bands, rooms). `python3 tools/data/build_data.py [module...]` writes `data/`. The world
builder lays out rooms from helpers (surfaces, painted buildings, ladders, portals, spawns, objects)
and keeps spawns clear of shrines and portals; `story.py` validates quests, NPCs and unlocks.

## Player-facing text

No script writes text the player reads. Pages, the HUD, the shell and the authorities' messages call
`Tx.t("key")`, which reads `data/strings/en.json`. Interface lines are authored in
`tools/data/ui_strings.json` and merged by the economy builder with the generated keys (realms,
currencies, unlock labels). Formats stay in the string (`"Level %d"`), so a translation only swaps the
file. `tools/dev/extract_strings.py` moves new literals out of the code, and `contract_tests` fails if one
is left behind.

## Event contract

`data/event_contract.json` (from `tools/data/contract.py`) lists every event in the Part 4 catalogue with
the system that emits it. `contract_tests` checks that only that system's scripts emit it and that
something reacts; reactors that read state every frame are marked `polled`.

## Testing

`tests/` holds the suites listed in the README (engine, data validation, rules, contract and strings,
balance simulator, performance, Prologue and Act I runs). They drive the real autoloads headlessly: a test binds an
`ActorState` for the player, submits intents and calls `Game.tick`. `valley_run` extends `prologue_run`
and plays Act I with section checkpoints; grinding is shortened with `apply_progress(..., "test_shortcut")`
and every shortcut is labelled in the code.

## Movement, rooms and the future server boundary


### What runs now

`ActorState` is a scene-free state model with stable entity and zone IDs, planar position, absolute elevation, vertical velocity, support surface, and takeoff elevation. Versioned snapshots contain primitive values and stable IDs, not scene paths or Node references.

`ZoneGeometry` loads the map once, indexes surfaces by ID, and owns walking, landing, obstacle footprints, save relocation, and occlusion volumes. `MovementSolver` integrates motion with bounded 1/120-second substeps and ballistic height, resolves both axes at closed boundaries, and treats elevated platforms as one-way jump surfaces. Decorative objects opt out explicitly. Platform actors ignore ground footprints below them; an actor falling to ground is moved to the nearest valid point before support is assigned.

`PlatformLanding` owns joystick landing guidance and projected-foot contact. It corrects depth registration only after a jump reaches the platform's elevation, while the descending visible feet overlap support. It never raises a player to an unreachable height or intercepts an ordinary walk-off fall. One landing finalizer updates support, height, jump count and guidance together. `ActorState.air_peak` makes the reachability decision reproducible through trusted snapshots.

`RoomTravel` owns full gate-crossing detection using the same gate data as generation. It tracks entry, cancellation and whole-body exit, independently of scene drawing. `room_gate.gd` draws the far and near portions with separate depth orders; `ZoneLayout` supplies solid posts. World only dispatches the accepted transition and mounts the next region. A future server must run this crossing state per actor rather than accept a client-requested destination.

`LocalAuthority` owns command ordering and movement execution. It rejects duplicate/stale sequences, nonfinite vectors and durations, and invalid movement parameters. Positions and speed are not supplied in client movement intent. The local caller supplies elapsed time and server-owned speed. It supports validated trusted snapshot correction and deterministic replay on the same runtime. This is a local authority adapter, not a network-security claim or a cross-platform bit-identical physics guarantee.

`player.gd` owns local input sampling, sprint/action timers, and animation. Its position properties delegate to ActorState. `world.gd` builds scenery depth, renderer-independent outline occlusion, camera, projectile effects, and save checkpoints. `wardrobe.gd` remains the local appearance/catalog/save adapter. `hud.gd` only routes controls and draws the requested interface.

Room hazards (S17) are World state. `RoomRuntime.hazards` runs each hazard's cycle (tell, warning, active, cooldown) from `data/hazards.json`; the World authority lands strikes, statuses and Hollowing through Combat, and computes the push of gusts and currents as `hazard_drift`. `player.gd` adds that drift to the walking vector it hands `LocalAuthority.move`, so the push is decided by the authority, never by input. `HazardView` draws the phases from state.

Static object definitions are data, not scene-node collision bodies. The same footprint contract is used by local movement and trusted snapshot validation, which is necessary before moving the solver to a server. Occlusion is presentation-only. A future remote-actor view must evaluate the same volumes per replicated actor; outline state must never affect authoritative simulation.

### Extension contract

A future zone server should instantiate one ActorState and authority per authenticated entity, advance fixed ticks using server time, and bind input sequence streams to server-owned identities. The transport should carry normalized movement/action intents, acknowledged input sequences, and versioned state snapshots. It must not expose `restore_authoritative_snapshot` as a client command. Clients can reuse MovementSolver for prediction, then reconcile acknowledged snapshots and replay outstanding commands. Remote actors should interpolate snapshots separately from local prediction.

Combat, sprint eligibility, resource changes, equipment swaps, cooldowns, arrow spawning/hits, inventory, quests, and persistence must become server-owned before online release. Today those action/resource timers and projectiles are local. Preserve the same equipment IDs in authoritative inventories; rendering can continue using the existing avatar compositor.

Use zone IDs to partition simulation and interest regions to select nearby entities for replication. Put account authentication, database transactions, inventory authority, and session ownership behind separate adapters. Replace local JSON writes with a repository keyed by authenticated character ID; retain local JSON as offline storage or a cache only. Version and migrate save/snapshot schemas deliberately.

### Explicitly not implemented

No networking transport, login/accounts, live server, database, matchmaking, shards, interest management, client prediction/reconciliation loop, remote actor interpolation, authoritative combat, trading, or anti-cheat service is shipped. The changes provide the shared movement/state boundary and validation/replay tests needed before those systems are added.
