# Audit 45 · code, dead weight, duplication, bugs and the content engines

Roadmap decision 45, phase 1, the code audit (`docs/roadmap_master_ui.md`). The user: "Go over the game code, compress,
clean, go over bugs or dead code. I want a clean and organized game code and architecture in the whole game. If things
could be automated we should go in that direction instead of rewriting everything every time."

This is an audit and a plan. No game code was changed. The findings are in `docs/architecture/audit_45.json`, and the
read-only scans that found them are in `tools/dev/audit/`. You can rerun everything with
`python3 tools/dev/audit/findings.py`. The tree audited is commit `35105ac`, the decision-45 roadmap, from 2026-09-30.

## 0. The short version

- **The game code is in better shape than its size suggests, but it has a few very large files.**
  - It has 73,240 lines of GDScript in `scripts/`. There is little line-for-line copying: exact clones in the game
    code come to under 100 lines.
  - Almost every function is called from somewhere.
  - Every file under `art/` is named by some manifest.
  - The problems are structural:
    - six god objects: `hud.gd` is 3,266 lines and its event handler has 234 branches; `main.gd` carries 510 lines of
      debug flags;
    - a dense web of calls between the authorities: 36 pairs of authorities call each other, and code calls other
      objects' private methods 56 times;
    - two views, side and top-down, sharing the simulation through 74 `topdown == null` branches;
    - content that is still authored by hand, one coordinate at a time.
- **Dead code: about 6,500 lines are unused or never run, and about 34,000 more are the frozen side view.**
  - Game scripts nothing loads: 42 lines (2 scripts) and 1 orphan `.uid`.
  - Unreferenced game functions, constants, variables and signals: 98 lines.
  - Game functions only tests call: 439 lines.
  - Tests no suite runs: 27 scripts, 1,634 lines. Four of them no longer compile or run.
  - Stale probes and one-off generators: about 4,300 lines (the decision-42 study alone is 1,857).
  - Data the game never reads: 3 tables and 11 row fields, the largest on 117 rows.
  - About 62 string keys nothing asks for, and 20 manifest ids nothing names.
  - The side view (decision 41's fallback) is not dead, but it is frozen:
    - 2,233 lines of game scripts that only it reaches;
    - 55.7 MB of art (3,957 files) that the top-down game never draws;
    - about 32,000 lines of frozen side-view art generators (`tools/props`' 13,265 more are partly shared with the
      pages).
- **Duplication.** None of it is copy-and-paste inside the game code. It comes in three kinds:
  - Parallel mechanisms, each needing one home:
    - seven hand-rolled per-frame caches;
    - five copies of the same hash-noise function;
    - 18 `TopdownDoll`/`Avatar` branches;
    - 11 event listeners that each receive every event, most of them dispatching through a `match` on its name;
    - the side-view and top-down pairs (`world`/`topdown_world`, `player`/`topdown_player`, `EnemyBrain`/`TopdownBrain`).
  - In the generators, near-copies:
    - five families of side-view creature modules (893 lines);
    - four pixel libraries;
    - the grid's walking rules written twice, once in Python and once in GDScript, with the thresholds hard-coded on
      the Python side.
- **Bugs.** 14 findings: 1 crash after a content rename and 13 performance, fragility and structure issues.
  - The crash: recipe ids read from the save's queues are looked up without a check (`crafts_page.gd:810` and
    `:1528`).
  - A flaky gate: `perf_tests` fails under CPU load.
  - The costs:
    - every event goes to 11 listeners, most of them string `match` chains, the HUD's with 234 branches;
    - the boot parses every table;
    - the FX cap leaks when the loops fill it.
  - Seven writes cross between authorities through private methods.
- **The engines.** Seven are designed:
  - room;
  - monster;
  - NPC;
  - item;
  - quest;
  - cue and notice;
  - technique, which already exists and is the model for the others.
  Each is a spec compiled by the generators that exist today. Each migrates by round-trip: the spec must reproduce the
  current JSON byte for byte before it is used for new content. Estimated savings:
  - the 141 side-view rooms still to convert: about 8,500–15,500 hand lines of coordinates become about 2,100–2,800
    spec lines;
  - the 110 species without top-down art: about 22,000 lines of pose code become about 2,500.
- **Phase 2** has 18 slices in three waves, each owning its own files:
  - wave 1 (dead code, tests, tools, shared utilities, generator hygiene) runs in parallel once phase 1 lands;
  - wave 2 splits the god objects, one owner per file;
  - wave 3 builds the engines.

## 1. Baseline: `tools/run_tests.sh` on the untouched tree

Run once on commit `35105ac`, with four other agents sharing the 4-core machine:

| Gate or suite | Result |
|---|---|
| room_lint | 168 rooms, 0 failing |
| topdown_rooms --check · sect_walks · places · sound · audio_check | current, 0 failing (26 places, 271 sound files) |
| engine_tests | 3,908 / 3,908 |
| data_validation | 50,302 checks, 0 failures |
| room_sweep | 3,736, 0 |
| visibility_suite | 6,758, 0 |
| rules_tests | 2,695, 0 |
| contract_tests | 1,084, 0 |
| balance_sim | 177, 0 |
| **perf_tests** | **18, 1 failure** ("the crowd under the breakthrough and a sword swarm fits the budget (13.03, 16.66 ms)") |
| prologue_run | 103, 0 |
| tutorial_order | 434, 0 |
| topdown_tutorial | 969, 0 |
| tutorials | 87, 0 |
| story_scenes | 90, 0 |
| hollow_night | 47, 0 |
| audio_tests | 56, 0 |
| valley_run | 3,007, 0 |
| places_tests | 16, 0 |
| **Total** | **73,487 checks, 1 failure (perf_tests)** |

`perf_tests` measures milliseconds on the shared machine. I reran it alone at a load average of 7.7: it failed 5 of 18
checks:
- room load 330 ms;
- crowd 18 ms;
- `techniques.json` 191 ms;
- the wood tree drag;
- Lotus Ferry 473 ms.

Treat it as a flaky gate while agents run in parallel (BUG-10). Every other suite and gate passed.

## 2. Inventory

### 2.1 Lines, files and functions per area

Lines include comments. `scripts/` has 73,240 lines of game code; `tests/`, `tools/` and `tools/dev` hold the rest.
The totals are 258 `.gd` files with 110,305 lines and 294 `.py` files with 119,796 lines.

| Area | Files | Lines | Funcs | Responsibility |
|---|---:|---:|---:|---|
| scripts/simulation/authority | 23 | 19,425 | 1,449 | The 21 authorities and the `Game` facade: every state write |
| scripts/ui/pages | 53 | 17,932 | 1,073 | 45 pages plus 8 page kits |
| scripts/topdown | 21 | 8,877 | 535 | The top-down world: room grid, motor, player, terrain, foliage, life, light, FX, places |
| scripts/presentation | 25 | 7,851 | 471 | Shared views: FX layer, moments, staged scenes, labels, sprite cache, technique pictures |
| scripts/ (root) | 17 | 6,943 | 357 | `main.gd` (shell), `hud.gd`, and the side view: `world.gd`, `player.gd`, `avatar.gd`, terrain, backdrop |
| scripts/simulation/rules | 14 | 3,291 | 345 | Pure rule functions |
| scripts/ui | 5 | 2,405 | 187 | `Page` base, `UiKit`, tutorial coach, equip prompt |
| scripts/simulation (root) | 10 | 1,553 | 89 | Side-shaped movement: ActorState, ZoneGeometry, MovementSolver, LocalAuthority, map generator |
| scripts/core | 10 | 1,352 | 127 | Autoloads: ContentDB, GameEvents, Clock, Rng, Saves, Unlocks, Tx, tutorial rules |
| scripts/audio | 3 | 1,212 | 101 | AudioDirector, SoundBank, TopdownSound |
| scripts/simulation/state | 10 | 1,126 | 74 | Plain state objects |
| scripts/simulation/ai | 3 | 849 | 35 | EnemyBrain (side), TopdownBrain, AllyBrain |
| scripts/shell | 3 | 424 | 31 | Title and selection screens, page warmer, notifier |
| tests | 69 | 31,836 | 813 | 17 suites plus 27 scripts no suite runs |
| tools/data | 39 | 23,504 | 677 | `build_data.py` and its 24 modules, layouts, places, life, lints |
| tools/art/creatures | 70 | 21,160 | 607 | Side-view creature sheets, one module per species |
| tools/icons | 35 | 17,459 | 1,090 | HD icon families (Style A) and studies |
| tools/props | 17 | 13,265 | 450 | Side-view props (`prop_art.json`) |
| tools/art/topdown (+ figure 5,562 · creature 2,607) | 96 | 18,235 | 812 | The top-down pipeline: tiles, terrain v2, decor, life, the character pipeline, foes |
| tools/dev | 24 | 7,467 | 327 | Captures, QA probe, wiki, string extractor, style audit |
| tools/backdrops | 1 | 6,623 | 192 | Side-view parallax backdrops |
| tools/audio | 12 | 5,867 | 359 | Synth, sfx, music, beds, life sounds |
| tools/art (root) + fx | 21 | 8,014 | 396 | Side-view `pixel.py`, bakes, helper batches; FX sheets (side and top-down) |
| tools/ui | 3 | 3,642 | 190 | UI kit, HD kit, valley map |

Assets: `art/` has 6,714 files (130 MB without `.import`), `data/` has 371 files (8.7 MB), and `docs/` has 1,978 files
(335 MB, most of them review pictures).

### 2.2 The largest files and the god objects

| File | Lines | Funcs | What is in it | Verdict |
|---|---:|---:|---|---|
| `scripts/hud.gd` | 3,266 | 168 | Layout (354–447), input (448–1243), **events (1244–1964): `_handle` 1349–1963, one 615-line `match` with 234 branches, 134 `add_log` and 124 `toast` calls**, drawing (1965–3266: minimap 127, player panel 89, boss bar 62, tracker 50 …) | God object. Split into input, layout, notices (data), panels and tours (S6) |
| `scripts/simulation/authority/combat_authority.gd` | 2,819 | 169 | 18 sections: flight, movement arts, views, attacks, tick, resolution, Phantom Double, flying sword, melody, sect roles, Blood path, Array Plates, swarm, talismans, projectiles, treasures, `apply_*` | God object. Split by section into parts under the same authority (S8) |
| `scripts/simulation/authority/world_authority.gd` | 2,296 | 155 | 16 sections: ambushes, rare herbs, rooms, transfer arrays, objects (`interact` 156 lines), beast cores, loot, tick, rooftop chases, hazards, voyages, room events, nests and Beast Tide, Trial Tower, idle and auto-path | God object (S9) |
| `scripts/simulation/authority/crafting_authority.gd` | 2,055 | 157 | 20 sections: professions, gathering, garden, racks, raids, transplanting, recipes, the furnace, herb nature, pill tribulation, fire, treasures, upkeep, talismans, ancient recipes, experiments, guilds, commissions | God object (S10) |
| `scripts/simulation/authority/progression_authority.gd` | 1,810 | 135 | Realms, breakthroughs, tribulation, meditation, offline claim, insight, Daos | Large (S10; phase 1 edits it) |
| `scripts/ui/pages/techniques_page.gd` | 1,724 | 120 | Tree layout jobs, drawing, dock, actions | Large but cohesive |
| `scripts/simulation/authority/pet_authority.gd` | 1,690 | 142 | `handle` 92 lines; taming, eggs, breeding, arena | Large, cohesive |
| `scripts/ui/pages/crafts_page.gd` | 1,669 | 77 | `on_action` 196 lines covering nine page ids | Large |
| `scripts/ui/pages/map_page.gd` | 1,442 | 79 | Cards, model, tokens, ranking | Large, cohesive |
| `scripts/simulation/authority/post_authority.gd` | 1,423 | 132 | Keeping Post, Vigil, snares, works | Large, cohesive |
| `scripts/topdown/topdown_life.gd` | 1,373 | 69 | Critters, hangings, animals, workers | Large, cohesive |
| `scripts/topdown/topdown_world.gd` | 1,230 | 87 | Room build, camera, foes, labels, fight warm-up; `FoeView` is an inner class | Parallel to `world.gd` (DUP-05) |
| `scripts/main.gd` | 1,058 | 35 | Shell, page table, world mounting; **`_handle_preview_args` is 510 lines of debug flags (180–690)** | Move the flags out (S7) |
| `tools/dev/topdown_capture.gd` | 2,182 | 61 | One capture scene per decision (story 130, hollow_night 119, monsters 95 …) | A capture registry (S3) |
| `tests/rules_tests.gd` | 13,493 | 174 | Every rule test in one file | Split per system when it is next touched |

### 2.3 Tangles

- **Autoloads.** Scripts reference the ten autoloads 4,880 times across 145 files. The heaviest users:
  - `hud.gd`: 405 (Game 247, ContentDB 130);
  - `main.gd`: 325;
  - `crafting_authority.gd`: 241;
  - `progression_authority.gd`: 220.

  This is by design: `Game` is the facade. It still means views read deep into the authorities (741 `Game.<authority>.x`
  references in 67 presentation files). Twelve of those calls go to five private queries, and presentation never
  calls a writer. Good.
- **Authorities call each other directly.** There are 575 `game.<authority>.<method>` calls, and 36 of the 210
  possible pairs call in both directions. The heaviest:

  | Pair | Calls each way |
  |---|---|
  | crafting and inventory | 54 / 2 |
  | world and combat | 23 / 5 |
  | combat and progression | 12 / 15 |
  | world and quest | 21 / 6 |
  | pets and inventory | 19 / 5 |
  | field and combat | 15 / 4 |

  `docs/architecture.md` says authorities "call the owner's public `apply_*` commands". Seven calls break that by going
  through private methods (BUG-05):
  - `field_authority.gd:218-226` calls `game.combat._apply_status_to_enemy` four times;
  - `enemy_authority.gd:616` calls `game.world._drop_loot`;
  - `quest_authority.gd:1093` calls `game.world._start_event`;
  - `account_authority.gd:319` calls `game.quest._refresh_offers`.
- **Private calls in general: 56**, including:
  - `EnemyBrain._set_state`, `_wander`, `_choose_attack`, `_start_hop`, `_hop` and `_follow_edge`, driven from
    TopdownBrain and AllyBrain;
  - `UiKit._stat_is_percent` and `_heart`;
  - `InventoryPage._stat_key` and `BagPage._hash`;
  - `ShapeJob._col`, `_place` and `_route_box`.
- **Method names from data:** `hud.gd:521` and `tutorial_rules.gd:102` call
  `Game.get(row[0]).call(row[1], c)` with names read from `unlocks.json` and the tutorials (BUG-06).
- **Two event paths**, which is fine and documented:
  - authorities `subscribe` with priorities;
  - presentation listens to the `GameEvents.event` signal. Eleven presentation nodes connect to it (every open page
    too), and most of them run their own `match name:` over every event (BUG-02).

### 2.4 Side view and top-down

The world mounted depends on the room (`main.gd:798 _add_world_view`):
- the top-down world (`topdown_world.gd`) when the character plays top-down and the room has a layout in
  `data/topdown/`: 27 rooms of the world, plus the prototype and review rooms (`td_*`);
- otherwise the side view (`world.gd`).

Decision 41 keeps the side view as a new-game fallback setting, "never mid-game". A gate closes every way from a
top-down room into a room with no layout. The remaining 141 side-view rooms are reachable only by a side-view
character.

| | Side view only | Shared | Top-down only |
|---|---|---|---|
| Game scripts | 13 files, **2,233 lines**: `world.gd` 653, `player.gd` 774, `backdrop.gd` 124, `avatar.gd` 125 (also the portrait fallback for side-view characters), `volume_view` 124, `map_generator` 128, `decor_views` 70, `occlusion_outline` 50, `climbable_view` 46, `room_travel` 43, `scenery_prop` 42, `arrow` 34, `shadow` 20 | The authorities, rules and state (side-shaped: `ActorState`'s plane plus altitude plus surface; `ZoneGeometry` runs a stand-in ground under the grid, `TopdownRoom.geometry_def`), `MovementSolver` 491, `ZoneGeometry` 511, `LocalAuthority` 108, `surface.gd` 144, `terrain.gd` 462 (the portal view still uses it), the HUD, the pages, `WorldShared`, `FxLayer`, `EnemyView` (labels, and the stand-in art for species with no top-down sheet), `ObjectView`, `NpcView`, `PortalView`, `MomentView`, `SceneDirector` | `scripts/topdown/` (21 files, 8,877 lines), `TopdownBrain`, `aim_gesture`, `TopdownSound` |
| Branches | — | **74 `topdown == null` / `is World` / `TopdownDoll.shown()` checks in 20 files**: `world_authority` 21, `enemy_authority` 10, `ally_brain` 8, `hud` 8, `autopilot` 5, `main` 4, pages 6 … | — |
| Art | `art/` root 2,121 files (14.4 MB, `parts.json` body, hair and gear), `art/dye` 1,700 (14.3 MB), `art/environment` 11 (24.5 MB), `art/backdrops` 125 (2.5 MB): **3,957 files, 55.7 MB, all exported to the APK** | `art/creatures` (stand-in sheets for 110 species with no top-down art; pages), `art/props` (pages such as the sect page, and `ObjectView`), `art/fx`, icons, UI | `art/topdown/*` (character 35.7 MB, foes 2.9 MB), `art/fx/topdown` 10.2 MB, tiles |
| Tests | 5 legacy scripts still green but outside any suite (combo 2,057 checks, landing 1,354, maps 76, movement 30, gates 276) | engine_tests, room_sweep, visibility_suite and valley_run all drive side-view rooms | topdown_tutorial, topdown_suite, places, hollow_night |
| Generators | `tools/art/creatures` 21,160 lines, `tools/backdrops` 6,623, `tools/art/pixel.py` 1,410, `helpers_batch_*` 934, `bake_*` about 1,600, `build_creatures`, and the side-view parts of `tools/props` (13,265, partly shared through the pages) | `tools/data/world.py` (every room's ids, which both views use) | `tools/art/topdown/*`, `tools/data/topdown_rooms.py`, `topdown_life.py`, `places.py` |

**Verdict.** The side view is frozen, not dead. Keep it green behind a `side_view_suite` (S2) and move its files under
`scripts/sideview/` and `tools/art/sideview/` (S3, S12). Its 74 branches in shared code go behind one `RoomSpace`
interface (S12).

Deleting the side view is a product decision: it would retire the fallback setting and save 55.7 MB of APK and about
36,000 lines. I recommend taking that decision once the room engine (E1) has converted the remaining rooms. After
that, no room needs the side view.

## 3. Dead code

How each class of finding was checked:
- **GDScript.** `tools/dev/audit/gd_graph.py` tokenizes every `.gd` file, splitting out strings and comments. It
  collects every string literal, every string in `data/**/*.json`, and every path, method and signal in the `.tscn`
  and `.godot` files. A name counts as used when it appears as a token or a string anywhere outside its own
  definition. That covers string-based calls (`call`, `has_method`, `Callable`, `connect`), data-driven names (such as
  `unlocks.json` `count`), `load`/`preload` paths and scene references.
  - Dynamic prefixes: `moment_view.gd:512 call("_draw_" + kind)` and `valley_run.gd:54 call("sec_" + s)` are scoped
    to their own files.
  - Private functions are checked within their own file and their `extends` family.
  - Scripts are checked by reachability from `project.godot`, from the suites in `run_tests.sh`, and from every tool
    scene.
- **Python.** `py_graph.py` works on the AST. It resolves relative imports, and counts `build_data.MODULES`,
  `importlib` by name, `spec_from_file_location` creature loaders, auto-imported `figure/sets` modules and functions
  registered by decorators (`@sfx`, `@music`) as uses.
- **Assets and data.** `asset_refs.py`, `manifest_refs.py`, `data_refs.py` and `strings_refs.py` do the same
  analysis for art, manifests, data tables and fields, and string keys.
- **Every high-confidence item below was confirmed by grep.** The scans are conservative: a name shared with another
  definition counts as used. The real dead code is therefore slightly larger than what is listed.

### 3.1 Scripts and files (high confidence)

| Finding | Lines | Action |
|---|---:|---|
| `scripts/ornament.gd`, `scripts/room_gate.gd`: nothing loads them. `room_gate`'s job moved to `topdown_gate.gd` and the side view's `portal_view.gd`; `architecture.md` still names it | 42 | delete (S1) |
| `scripts/connection_visual.gd.uid` without a script | 1 | delete (S1) |
| `scripts/combo_rig.gd`, `scripts/equipment_rig.gd`: only the v0.13 bakes run them (`tests/bake_*.gd`, `tools/bake_hat_cape_combos.gd`) | 99 | move to `tools/art/sideview/` (S3) |
| `scripts/simulation/map_validator.gd`, `world_catalog.gd`: only `tests/map_generation.gd` (not a suite) reaches them | 121 | move with that test, or delete it (S2) |

**Status (phase 2, S1):**
- **DEAD-01, closed.** `ornament.gd` and `room_gate.gd` are deleted with their `.uid` files. So is
  `art/environment/room-gate.png` (1.2 MB) with its `.import`, since only `room_gate.gd` drew it. `architecture.md`
  now names `PortalView`, and `docs/art-v13-gate.md` says the gate is retired.
- **DEAD-02, closed.** `connection_visual.gd.uid` is deleted.

### 3.2 Functions, constants, variables and signals

High confidence: the name occurs nowhere else, not even as a string. Delete these (S1). The `hud.gd` and
`tutorial_coach.gd` lines wait for phase 1.

| Where | Symbol | Lines |
|---|---|---:|
| `scripts/audio/sound_bank.gd:42` / `:119` | `surface_of_material`, `is_night` | 11 |
| `scripts/avatar.gd:72` | `still_image` | 18 |
| `scripts/presentation/sprite_cache.gd:152` / `:68` | `icon_ready`, `ICON_PX` | 8 |
| `scripts/presentation/technique_picture.gd:948` / `:965` | `draw_cooldown`, `draw_qi_short` | 25 |
| `scripts/simulation/rules/technique_tree_rules.gd:193` | `tree_state` | 3 |
| `scripts/topdown/topdown_life.gd:533` | `critter_count` | 6 |
| `scripts/ui/pages/techniques_page.gd:554` | `_slot` (private, unused in its family) | 4 |
| `scripts/ui/ui_kit.gd:222-228` | `T_HINT`, `T_CAPTION`, `T_ROW`, `T_BODY`, `T_BUTTON`, `D_HEADING` | 6 |
| `scripts/ui/page.gd:44`, `mail_page.gd:8`, `scene_rules.gd:27` | `GROUP_GAP`, `DESK`, `TARGETS` | 3 |
| `scripts/ui/tutorial_coach.gd:22` / `:45` | `MISSING_S`, `_tab_was` | 2 |
| `scripts/hud.gd:111`, `:113`, `:114` | `meditate_center`, `sphere_center`, `sense_center` | 3 |
| `scripts/world.gd:54-55`, `topdown_world.gd:100`, `hud.gd:131` | signals `room_changed`, `context_changed` ×2, `page_changed`: emitted, never connected | 8 |

**Status (phase 2, S1):** each name was checked again after phase 1 (tokens, strings, `call`/`has_method`/`connect`,
`.tscn` files, data and tools).
- **DEAD-05, closed.** All nine functions are deleted.
- **DEAD-06, closed.** The constants and variables are deleted. Phase 1 put `tutorial_coach.gd`'s `MISSING_S` to use and
  removed `_tab_was`, so neither was left to delete. Two unreferenced `level_of`s are deleted too: `ContentDB.level_of`
  and `GameAuthority.level_of`. The scan had marked them low confidence only because they share a name; neither is
  called. `docs/ui_style_guide.md` now names the type scale by `WORD_SCALE_STEPS` and `DISPLAY_STEPS`.
- **DEAD-07, closed.** The four signals and their emit lines are deleted. The two `context` updates keep their hash test.
- Left for S2: `world_catalog.gd`'s unreferenced `neighbour`, which goes with that file (DEAD-04).

Medium confidence: 42 symbols that only tests or tools use (439 lines). Some are deliberate test hooks, and those
should stay but be marked `## test hook`:
- `hud.set_state` (29 test uses);
- `world_labels.touching`;
- `moment_view.lock_left`;
- `scene_director.poll`;
- `local_authority.restore_authoritative_snapshot` (the server boundary);
- `clock_service.simulate`.

Others go with their tests: `MapGenerator.generate` (110 lines), `equipment_rig.render_sheet`,
`progression_authority.tree_view`, `world_rules.npc_room`, `progression_rules.npc_age` and
`world_authority.context_portal`. The full list is `scans.gd_graph.symbols[status=not_used_by_game]` in the JSON.

**Status (phase 2, S1): DEAD-08, closed.**
- **Deleted, with their tests moved or dropped:**
  - `progression_authority.tree_view`. Its two `rules_tests` checks now read `tree_node` and `realisations`, which
    the page uses.
  - `world_rules.npc_room`. `data_validation`'s auto-path check reads `WorldRules.rooms_with` itself.
  - `progression_rules.npc_age`, with its one check, "Granny Liu grows older alongside you". No page shows an NPC's
    age.
- **Kept, now used by the game:** `world_authority.context_portal`. The context button's portal loop had the same rule
  written out inline; it now calls `context_portal`, so the rule `data_validation` checks is the one the game uses.
- **Kept and marked `## Test hook`:**
  - `audio_director.voices_playing` and `music_state`;
  - `sound_bank.life_ids` and `named_ids`;
  - `clock_service.simulate`, `repository_local.wipe`;
  - `hud.PICTURE`, `presence_center` and `set_state`;
  - `main.pages_warm`;
  - `moment_rules.MATCHERS`, `ANCHORS`, `SHAPES` and `STYLES`;
  - `moment_view.lock_left`, `scene_director.poll`, `scene_rules.problems`;
  - `sprite_cache.icon_hd` and `emblem_whole`, `world_labels.touching`;
  - `local_authority.restore_authoritative_snapshot` (the server boundary too);
  - `topdown_atmosphere._count`, `topdown_motor.airtime`, `topdown_world.add_villager`;
  - `equip_prompt.gain_text`;
  - `page.GRID`, `SAFE_AREA` and `WINDOWS`;
  - `ui_kit.TEXT_ON` and `on_scale`;
  - `technique_tree_rules.nodes_of`, which became test-only once `tree_view` went.
- **Left for their own slices:**
  - `game_events.unsubscribe_object`, S4's file. It is the pair of `subscribe`, so it stays.
  - `combo_rig` and `equipment_rig`, which S3 moves.
  - `map_generator.generate`, which goes with `map_generation.gd` (S2) or the side view.
  - `surface.projected_front` and `world.save_slot_index`, side view, reached only by legacy tests.
  - `topdown_atmosphere`'s `vec4`, a false hit on a shader's word.
- **Data left unread** for S5 to drop in the generators: `npcs.json` `age` (24 rows), read only by `npc_age`, and
  `sound.json` `steps.materials`, read only by `surface_of_material`.

### 3.3 Tests and probes nothing runs

- **27 SceneTree scripts under `tests/`, 1,634 lines, outside every suite.** 22 were imported with v0.13 and never
  touched since. Each was run with `godot -s` (`tools/dev/audit/run_legacy.py`):
  - still green, so wire them into a `side_view_suite` (S2): `combo_tests` (2,057/2,057), `landing_matrix`
    (1,354/1,354), `map_generation` (76/76), `movement_v07` (30/30), `room_gates` (276/276);
  - broken: `obstacle_review`, `platform_contact` and `upward_landing` do not compile when run as scripts
    ("Identifier not found: GameEvents"), and `movement_review_v09` exits 1;
  - windows or never quit: `support_review_v08`, `generated_runtime`, `gauntlet_review` and `release_review` time
    out; `pixel_input` needs a window;
  - these are one-off review renders: `review_visual_v08`/`v09`, `visual_checks`, `weapon_combo_outlines`/`visual`,
    `movement_visual_v07`, `platform_contact_visual`, `generated_visuals`.
- **`tools/dev` probes nothing names** (last commit in brackets; `mentions.py`):
  - `fix_infer.py` (09-24): a one-off `:=` fixer. Delete it.
  - `stat_probe.gd` (09-27), `sect_capture.gd` (09-29), `places_capture.gd` (09-29), `picture_capture.gd` (09-29),
    `tutorial_capture.gd` (09-30) and `combat_trace.gd` (09-29). Each is a 150–300-line one-decision capture.
  - `topdown_capture.gd` holds 59 more such scenes.

  Fold them into one capture registry, where a shot is a data row (room, setup, camera, frames) (S3).

### 3.4 Obsolete paths and stale generators

- **One-off bakes nothing runs:**
  - `tools/art/bake_act2_hats.py` (named nowhere);
  - `bake_straw_hat.py`;
  - `tools/bake_hat_cape_combos.gd`;
  - `build_creatures.py` (side view);
  - `build_topdown_proto.py` (22 lines, superseded by `build_tiles.py`).
- **`tools/art/topdown/study_quality/`** (1,857 lines): the decision-42 comparison study. It carries copies of
  `figure/raster.py` (47 lines) and `kinds/folds.py` (56). Archive the pictures, then delete the folder.
- **`tools/icons/study/technique_cards.py`** (594 lines): nothing calls it.
- **Frozen side-view generators:** `tools/art/creatures` (70 modules, 21,160 lines), `tools/backdrops` (6,623),
  `pixel.py`, `helpers_batch_*` and `bake_*`. Move them under `tools/art/sideview/` with a README saying they are
  frozen (S3).
- **Python functions nothing calls:** 21 top-level functions, 139 lines, for example `synth.gauss_band`,
  `pix.hsv_shift`, `shapes.bez_line`, `terrain2.pnxy`, `pixlib.inner_line` and `defs_objects.chest_body`
  (`py_graph.json`).

### 3.5 Data

| Finding | Evidence | Action |
|---|---|---|
| `data/balance.json`: only `balance_sim` reads it | table name nowhere in `scripts/` | move it to `tests/data/`. ContentDB loads every `data/*.json` at boot (S5) |
| `data/legendary_chains.json`: only tests and the wiki read it | same | move it next to its generator's output for the wiki (S5) |
| `data/topdown/td_review_heights.json`: only tools read it | same | keep it, but out of `data/` |
| `techniques.json` `mastery.dmg_per_tier` and `cost_per_tier` on 117 rows | the game reads `stats.json` `mastery_cost_per_tier` | drop them in `technique_gen` |
| `unlocks.json` and `quests.json` `same_stage_ok` (111 rows) | only `data_validation` reads it | keep it as a generator-side check, off the row |
| `items.json` `core.qp_pct` (44 cores) | a core's Qi comes from its effects; nothing reads `qp_pct` | drop it (the progression job is changing these numbers: after phase 1) |
| `shops.json` `buys_all` (11), `enemies.json` `weak_to` (4) and `equipment_chance` (3), `artifacts.json` `named.archetype` (29), `sets.json` `archetype` (5), `zones.json` `laws` and `exit.to_zone` (3) | not read | drop, or wire in if a design needs them (S5) |
| Manifest ids nothing names: `icon_manifest` 8 legacy icons (`elite_crown`, `gathering_log`, `player_arrow`, `portal_marker`, `portal_sealed`, `quest_main`, `quest_side`, `vendor`), `prop_art` 8 props (`broken_ring`, `leviathan_bones`, `star_iron_vein`, `stone_steps`, `void_geode`, `void_orchid_patch`, `war_drum`, `wooden_bridge`), `ui_assets` 4 (`hud_circle*`, `slot_empty_motif`) | `manifest_refs.py`, including format prefixes such as `hud_ring_%d` | drop them from their generators (S5) |
| String keys: 62 of 4,316 unasked (`ui.begin`, `ui.continue`, `ui.new_game`, the Works page's `*_note` …) | `strings_refs.py` (literals, data, composed prefixes, `Tx.plural`'s `_one`) | remove after a per-key grep. Keep the 11 `world_view.*` keys, which are built from data prefixes (S5) |

**Art and audio:** every one of the 6,714 files under `art/` is named by some manifest. The only unnamed files are
four font licences, which must stay. The dead weight is at the manifest level (above), plus the frozen side-view
art (§2.4).

## 4. Duplication and single homes

| # | What is repeated | Where | Single home |
|---|---|---|---|
| DUP-01 | **Seven per-frame caches** keyed on `Engine.get_process_frames()` plus `Game.revision` | `world_shared.gd:28`, `hud.gd:542` and `:2033`, `topdown_world.gd:555`, `posts_page.gd:172`, `place_rules.gd:137` (60-frame TTL), `sprite_cache.gd:24` | `scripts/core/frame_memo.gd`: `FrameMemo.get(owner, key, callable, ttl := 1, on_revision := true)` |
| DUP-02 | **The same sin-hash** `fposmod(sin(i*12.9898 + k*78.233)*43758.5453, 1)` five times, plus an integer hash | `fx_layer.gd:682`, `hazard_view.gd:179`, `map_page.gd:1308`, `beast_kit.gd:9`, `inventory_page.gd:87`, `topdown_terrain.gd:230` | `scripts/core/noise.gd` |
| DUP-03 | **The figure fork** `TopdownDoll.new() if TopdownDoll.shown() else Avatar.new()`, with its dress and draw branches, 18 sites | 12 files: the character, shop, inventory, cultivation and techniques pages, `shell_screens`, `technique_picture`, `technique_preview`, `npc_view`, `enemy_view`, `player.gd`, `hud.gd` | `Figures.for_character(ch)` / `Figures.for_outfit(o)` |
| DUP-04 | **Event → presentation switches** | `hud._handle` (234 branches), `WorldShared.play` (147 lines), `world._on_event` and `topdown_world._on_event` (70 each), `audio_director`, `moment_view`, `scene_director`, `tutorial_coach`, `page`, `topdown_atmosphere`, `topdown_life` | A **notice table** (`data/hud_notices.json`) for the one-line toasts and logs (about 180 of the 234), a **cue table** (`data/cues.json`) for event → fx, sound and shake, and a `Dictionary(name → Callable)` for what stays code (E6, S6) |
| DUP-05 | **Side view against top-down**, twice over | `world.gd`/`topdown_world.gd`, `player.gd`/`topdown_player.gd`, `EnemyBrain`/`TopdownBrain`, and 74 view branches in 20 shared files | A `RoomSpace` on `RoomRuntime` (`distance`, `place_near`, `floor_at`, `ground_under`, `in_reach`), with side and grid implementations; the authorities stop branching (S12) |
| DUP-06 | **Brains reaching into EnemyBrain's private steps** | `topdown_brain.gd:40-175`, `ally_brain.gd:70,141` | `scripts/simulation/ai/brain_kit.gd` (public) |
| DUP-07 | **Suite boilerplate:** `check()`, the summary and the quit block in 10 suites; the pixel_stage preamble in 8 visual scripts | `contract_tests.gd:16`, `data_validation.gd:14`, `balance_sim.gd:15`, … | `tests/lib/suite.gd` |
| DUP-08 | **Four pixel libraries** with the same line, ellipse and polygon rasterisers | `tools/art/pixel.py` 1,410, `tools/icons/pix.py` 951, `tools/props/pixlib.py` 573, `tools/art/fx/fxpix.py` 298 | `tools/lib/pix.py` for new work; the frozen side view keeps its own |
| DUP-09 | **Side-view creature modules copied** | ox, rhino and boar (515 lines); stag and hollow stag (177); fox and weasel (148); three crabs (35); two apes (18) | The monster engine (E2) for new species; no change to frozen art |
| DUP-10 | **The grid's walking rules written twice:** Python (`topdown_rooms.py:222 Grid.reach`, its 32.5 and 8.0 hard-coded) and GDScript (`TopdownRoom`/`TopdownMotor`, from `movement.json` `topdown.*`); the room route written twice (`sect_walks.py:222` and `WorldRules.route`) | — | Keep both, since the checks must run without Godot. Read the thresholds from `data/movement.json` in Python, and add a parity test that runs both on every layout (S5) |
| DUP-11 | **Generator CLI boilerplate** (build, `--check`, stale list, write) in 7 modules | `topdown_rooms.py:1746`, `topdown_life.py`, `places.py:342`, `sound.py`, `sect_walks.py`, `contract.py`, `scenes.py` | `tools/data/common.py` `emit()` and `run_cli()` (S5) |
| DUP-12 | **Atlas packing** in four builders, and the study's copies of the renderer | `build_decor` and `build_life` (32 lines), `build_tiles` ×2 (23), `raster`/`hifi` (47), `folds`/`looks` (56) | `tools/art/topdown/atlas.py` `pack()` (S3) |

**Status (phase 2, S4):** each finding was checked again on the tree phase 1 and S1 left. How to use each helper is in
`docs/architecture/shared_runtime.md`.
- **DUP-01, closed.** `FrameMemo` (`scripts/core/frame_memo.gd`) replaced the seven caches, and an eighth that phase
  1 added for the tutorial coach (`hud.tour_targets`).
  - `value(key, compute)` keeps answers by key. `table(scope)` hands the kept `Dictionary` to a hot path, which is how
    `WorldShared` uses it. `PlaceRules.home` keeps its 60-frame answers.
  - A repeated question costs about what the hand-written cache cost. On a desktop, `WorldShared`'s table takes 472 ns
    against 412, and a one-key `value` takes 878 ns against 374, most of it the `Callable` made at the call.
- **DUP-02, closed.** `HashNoise` (`scripts/core/noise.gd`) has `scatter`, `cell` and `value`. It is not named `Noise`
  because that is the engine's own class. The five sin-hash copies and `TopdownTerrain.h01` and `vnoise` are gone.
  - The outputs are bit-identical. The old functions' outputs over a grid match the new ones byte for byte: 35,888
    sin-hash points, 113,967 cells and 16,800 noise values.
  - `tests/shared_runtime_tests.gd` compares them over grids on every run.
- **DUP-03, closed.** `Figures` (`scripts/presentation/figures.gd`) makes every figure.
  - It covers the 18 sites, and `TopdownDoll`'s `figure_for`, `dress` and `shown`, which the dialogue, posts,
    companions, notice and sect pages called.
  - Every `Avatar` is made in its side-view section, so retiring the side view deletes that section.
  - Before and after captures match pixel for pixel, 13 of 13: Lotus Ferry, the Marsh Edge's fight, the selection's
    cards, and the Character, Bag, Cultivation, Techniques and Shop pages of a top-down and of a side-view character.

The label and plate layout is **not** duplicated: `WorldLabels.resolve` plus `WorldShared.label_views` place every
name for both views. `map_page`'s plates are map art, not world labels.

## 5. Bugs and smells found while reading

| # | Severity | Where | What | Fix |
|---|---|---|---|---|
| BUG-01 | low–medium | `crafts_page.gd:810` (`auto_queue` from the save), `:1528` (the refine in progress), `:716`, `:957` | Recipe ids read from the save are dotted into `ContentDB.entry("recipes", id).outputs[0]` with no check, and no load-time sweep drops unknown ids. After a recipe is renamed or removed in data, a save with it queued crashes the Crafts page. (There are 12 unchecked `ContentDB.x(...).field` sites in all; `crafting_authority.gd:1991` and `:1043` take their ids from data and are safe.) | `ContentDB.recipe_output(id)` returning `""`, and a save-load sweep for unknown ids |
| BUG-02 | medium (perf) | `hud.gd:1349`, `game_events.gd:77` | Every event goes to 11 listeners (plus each open page); most run a `match` on its name, and the HUD's has 234 branches, tested in order | Handler dictionaries (DUP-04) |
| BUG-03 | low (perf) | `game_events.gd:52-53`, `:69` | A linear `in` over `UNLOCK_TRIGGERS` (18) and `SAVE_TRIGGERS` (13) for every emitted event, and a copy of the subscriber array for every delivered one | Constant dictionaries, and an index loop |
| BUG-04 | low | `topdown_fx.gd:92-97`, `:101-111` | The effect cap only retires one-shot effects, so with 72 loops alive the list grows without bound. `advance()` copies the list every frame and erases by value (O(n²)) | Swap-remove in one pass; retire the oldest loop when no one-shot is left |
| BUG-05 | medium (architecture) | `field_authority.gd:218-226`, `enemy_authority.gd:616`, `quest_authority.gd:1093`, `account_authority.gd:319`, plus 50 more private calls | Writes across authorities through private methods, against `architecture.md` | Public `apply_*` names, and a `contract_tests` rule against `other._x(` (S11) |
| BUG-06 | low (fragile) | `hud.gd:521`, `tutorial_rules.gd:102` | `Game.get(row[0]).call(row[1], c)` with names from data: a rename fails only at runtime | A `data_validation` rule using `has_method` |
| BUG-07 | low (debug in release) | `main.gd:180-690` | 510 lines of preview flags in the shipped shell. Several call private methods (`Game.combat._defeat`, `Game.progression._advance`, `_start_tribulation`, `Game.calendar._phenomenon`, `Game.combat._cast_illusion`), so a rename breaks them silently | `scripts/shell/debug_args.gd`, a table of flag → handler, loaded only with the debug feature or `preview_mode` (S7) |
| BUG-08 | low (perf) | `hud.gd:542` | A per-frame cache key built with `points_override.duplicate()` every frame | FrameMemo |
| BUG-09 | low | `avatar.gd:65`, `zone_geometry.gd:31,40`, `map_generator.gd:16` | `assert()` in game code is removed from release exports, so the missing-pose check just draws wrong | `push_error` plus a fallback |
| BUG-10 | **medium** (flaky gate) | `tests/perf_tests.gd` | Millisecond budgets on a shared machine: 1 failure in the baseline, 5 in a rerun under load | Least-of-N rounds for every budget, as the living-world check already does |
| BUG-11 | medium (boot) | `content_db.gd:31-92` | Every `data/*.json` is parsed and expanded at boot: `techniques.json` is 974 KB and 3,171 rows (133 ms, and its own v1.5 budget fails at 191 ms); `icon_manifest` has 2,570 keys | Lazy tables, parsed on first `entry`/`all`/`config` |
| BUG-12 | low | `topdown_room.gd:87`, `topdown_rooms.py:192` | The level under a prop's footprint is read with no bounds check. A prop pushed past the edge crashes the room load; today the Python check guards it | Clamp plus `push_error`; the room engine validates footprints (E1) |
| BUG-13 | low (structure) | `scripts/simulation/authority/*` | 575 calls between authorities, 36 pairs in both directions | Publish each authority's surface; forbid private cross-calls (S11) |
| BUG-14 | medium (structure) | `hud.gd`, `combat_`, `world_`, `crafting_` and `progression_authority.gd`, `main.gd` | God objects (§2.2) | Split by section (S6–S10) |

**Status (phase 2, S1): BUG-01, fixed.**
- **Every recipe id the Crafts page did not take from the data is looked up through the page's `made_by(id)`**, which
  returns `""` for an unknown id. That covers six sites: the auto-refine queue, the refine in progress, the talisman
  template, the guild exam task, the ancient recipes' row and Deduce. The helper lives in the page rather than in
  `ContentDB` because S4 owns `content_db.gd` in this wave. The refine in progress is held in memory, not in the save,
  but it is guarded all the same.
- **On every load, `SaveService.migrate_character` drops recipe ids the data no longer has, with a warning.** It
  sweeps the known recipes, the pages held and the auto-refine queue, so a queued batch of such a recipe is lost. It
  does nothing when no recipe loaded, so a broken data build never empties a save.
- **`rules_tests`' `recipe_rename_suite` checks both halves.** It saves a character holding an unknown id, loads it,
  and opens the Crafts page with the id queued again. With the fix undone, both checks fail, and the page stops with
  the old SCRIPT ERROR at `crafts_page.gd:810`.

**Status (phase 2, S4):**
- **BUG-03, fixed.** `UNLOCK_TRIGGERS` and `SAVE_TRIGGERS` are constant sets.
  - A name's listener list is replaced on `subscribe`, never changed in place. A delivery walks the list it began with,
    without a copy for every event.
  - The order and semantics hold: priority, then the order of subscription. A listener added or removed during a
    delivery joins or leaves from the next event. `tests/shared_runtime_tests.gd` checks both.
- **BUG-04, fixed.** When the cap is full, the oldest one-shot goes, or with none left the oldest loop. The effect just
  begun is never dropped.
  - Before, a list full of loops grew past the cap, and every new one-shot was dropped as soon as it began.
  - `advance` drops finished effects in one pass. It keeps the rest in order, because the cap retires the oldest
    first: a swap-remove would lose that order.
  - `tests/shared_runtime_tests.gd` fills the cap with loops and checks that a one-shot plays.
- **BUG-08, fixed.** `FrameMemo` compares the badges' key by value and copies it only when it changes.
- **BUG-11, fixed.** Boot reads only `realms`, `recipes` (their indexes) and the strings on the game's thread. A
  low-priority loading thread reads the rest beside the boot, `techniques` first. A lookup that comes before the thread
  has its table reads it itself, and never waits on the thread.
  - Every lookup returns what a full boot read returned. The suite compares every table, room, dialogue tree and
    `parts` with a fresh read, both as booted and as read by the thread.
  - `tables`, `lists`, `configs` and `load_errors` read in whole still read everything, in the data folder's order.
    `tutorial_rules` asks `ContentDB.has_table("places")` instead of `lists`.
  - Measured as the median of 7 interleaved runs, on a shared 4-core machine at a load of 14 to 17, which inflates
    every time:
    - boot to the title's first frame: 9,273 ms before, 8,923 ms after;
    - ContentDB's own load at boot: 480 ms before, 33 ms after;
    - a new character's first room: 429 ms before, 256 ms after.

Also noted, not bugs:
- `ContentDB.entry("techniques", tech).hitbox.x[1]` in `world.gd:362` is safe: all 3,171 rows carry a `hitbox`.
- `hot_paths.py` found the per-frame work mostly careful: pages redraw on change, and the world memoises. The top
  scores are `fx_layer._draw_fx` (13 nested loops over its effect list, bounded by the FX cap) and the side view's
  `terrain._draw`.
- Tick-time allocations in `combat_authority._tick_pools` (`statuses.duplicate()`, eight `ContentDB.stat_const`
  dotted lookups per tick) and `_tick_projectiles` are small, but they run every physics tick for every character.

## 6. The content engines

Today content is written case by case: a room is a Python function of coordinates, a species is 100–300 lines of pose
code, and an NPC is split over four files. Much of the machinery to generate content already exists:
- the `Layout` DSL and its reach checks;
- `field()` room templates;
- `mob()`/`atk()`;
- the character pipeline, where every look is data;
- `sculpt.py`'s parts;
- `PILL_GRADES` (vessel × grade icons);
- `technique_gen` (3,171 rows from a grammar).

The engines are thin compilers over that machinery.

**Design rules (all engines):**
1. **A spec is data, in one place** (`tools/content/<engine>/specs/*.py`, Python literals, so comments and shared
   constants work). A spec names intent (bands, anchors, body plan, family, tier) and leaves coordinates, frames and
   prices to the engine.
2. **Deterministic.** The seed is the id. Two builds are byte-identical, and each engine has `--check`.
3. **Hand-tweakable.** Every generated value can be pinned in the spec: `pins` for cells, props and places, `pose`
   for a species' escape hatch, `row` overrides for an item. Tweaks never go into the JSON.
4. **Migration is a round trip.** An engine is first used to re-express existing content, until its output equals
   today's files (`git diff` empty). Only then is it used for new content. This keeps phase 2 a refactor.
5. **The existing gates stay the gates:** `room_lint`, `topdown_rooms --check`, `places --check`, `sect_walks`,
   `data_validation`, `sound --check`, `wiki --gaps` and the galleries AGENTS.md asks for.

### 6.1 Room engine (E1)

**What exists to build on:**
- `tools/data/topdown_rooms.py`: the `Layout` DSL (`rect`, `water`, `stair`, `prop`, `green`, `sand`, `walls`,
  `door`, `way`, `at`), the `Grid.reach` checks and `DOORS`;
- `tools/data/world.py` `field()`/`town()`: the side-view templates that already declare a room's ids, foes, herbs,
  jars and exits;
- `topdown_life.dress()` and `extend()` (furnishings, vistas, work spots);
- `places.py` (the systems-as-places rows and their `stand` check);
- `room_lint.py`.

**Spec format** (a real room re-expressed: `wp_east`, today `topdown_rooms.py:758-800`, 44 hand lines with about 60
coordinates):

```python
room("wp_east", size=(64, 26), biome="valley_meadow",          # biome: paint set, flora pools, vista, ambience
     bands=[("rock", 0, 2, dict(level=2)),                     # horizontal strata, north to south
            ("terrace", 2, 5, dict(level=1, paint="f")),
            ("road", 12, 3, dict(paint="d")),                   # a band named road is the main walk
            ("stream", 21, 5, dict(water=True))],
     features=[("knoll", (27, 8, 8, 3), dict(level=1))],        # raised or sunken shapes on a band
     stairs="auto",                                            # a flight wherever a walk crosses a level edge
     exits={"east": ("e", 13, 3), "west": ("w", 13, 3)},        # side-view portal id -> edge, row, span
     spawn_at="east",
     anchors={"npc_old_pan_wp": "knoll.top",                   # every id of the side-view room: an anchor or a cell
              "pan_spot": "road@34", "sign_wp": "road.north@60", "note_lu": "road.north@57",
              "herb_1": "verge.south@33", "jar_2": "terrace@48", "jar_4": "bank@52", "crate_3": "bank@33"},
     flora={"road": ["tree_plum", "tree_peach", "fence_4", "bush"],   # pools per band edge; density and the seed
            "terrace": ["tree_camphor", "bush_azalea"],               # place them clear of anchors, ways and walks
            "stream": ["tree_willow", "tall_grass", "cattails", "lotus_pads"], "density": 0.30},
     props={"willow": dict(along="terrace", every=11), "reeds": dict(along="stream.edge", every=10),
            "incense": (50, 10)},
     ground={"sand": "stream.coves"},
     foes={"verge": 5},                                        # the side-view spawn's count, on the verges
     pins={})                                                  # exact cells, props or places that override the engine
```

**Generation:**
1. Lay the bands and features.
2. Put stairs where a declared walk crosses a level.
3. Cut the exits and door paths (`door_path` exists).
4. Resolve anchors to cells, ranked by reach from every way and by distance from other anchors.
5. Scatter props and flora with a seeded Poisson-disc sampler per band edge, keeping clear of anchors, ways and the
   walk lanes (`portal_lane` exists).
6. Place the foe spawns on the verges, clear of shrines and portals (`world.py` already has that rule).
7. Call `LIFE.dress` and `LIFE.extend`.
8. Run the checks.

The output is the same `Layout.dict()` the game reads today, so **no game code changes**.

**Living-world tables:** the room's `work`, `extras`, `animals` and `hangings` in `topdown_life.py` take anchors
instead of cells (`"spots": "auto:water_edge"`), so a moved building moves its workers.

**Migration:**
1. Build the engine and use `pins` so that each of the 27 world layouts reproduces byte for byte. Start with the interiors
   (`lf_old_ma_store` is 23 lines), then the paths, then the village.
2. Delete the hand functions as they match.
3. Convert the 141 side-view rooms: the `field()` call already lists the ids; add a 10–20-line shape spec.

**What it saves:**
- A path room: 44 lines and about 600 tokens become about 15 lines and about 220 tokens.
- The village: 112 lines and about 1,600 tokens become about 35 lines.
- Across the 141 rooms left: about 8,500–15,500 hand lines at today's rate (60–110 per room) against about 2,100–2,800
  spec lines.
- Each new room costs about 250 tokens instead of 600–1,600.

**Tests:**
- determinism;
- `topdown_rooms --check`, `places --check`, `room_lint`, `sect_walks --check`;
- a round trip for every migrated room;
- `topdown_tutorial`'s in-game reach checks;
- one golden capture per biome in the capture registry;
- a unit test that every anchor kind resolves on a sample band set.

### 6.2 Monster engine (E2)

**What exists to build on:**
- `tools/data/enemies.py` `mob()` and `atk()` (the data row, with movement derived from the AI profile);
- `tools/art/topdown/creatures.py` `Spec` and `SIZE` (sheet, size, palette, elite);
- `creature/sculpt.py` (the `E`/`S`/`L` parts, `Pose`, `Look`, the renderer);
- `creature/motion.py` (`gait`, `pick`, `wave`, `headon`, `FRAMES`, `HIT_FRAME`);
- `tools/data/sound.py` (`FOE_FAMILY`, voices by race and nature);
- `tools/icons/families/beast_parts.py`;
- `wiki.py`.

**Body plans**, extracted from the twelve drawn species:

| Plan | Species it comes from |
|---|---|
| `quadruped` (rodent, mustelid, suid variants) | rat, otter, the boarlets |
| `amphibian` | frog, toad |
| `crab` | mudshell crab |
| `serpent` / `fish` | eel, minnow, leech |
| `shell` | Old Snapper |
| `humanoid` | the trial puppet |

A plan is a pose function parameterised by part sizes and motion styles. The key-frame tables every species
repeats — `LUNGE`, `PITCH`, `HEAD`, `YAW`, `GAPE`, `SQUASH`, `ROLL`, `TAIL` in `rat.py` — become named styles
("lunge_bite", "rear", "topple_side").

**Spec** (a real species: `reedtail_rat`, today `creature/rat.py` 129 lines plus rows in `enemies.py:232`,
`creatures.py` and `sound.py`):

```python
species("reedtail_rat", plan="quadruped.rodent", size=1.0, length_px=38,
        palette=("fur", "fur_light", "pink", "tail_a", "tail_b"), eyes="rat_eye",
        parts={"ears": "round", "tail": {"kind": "segmented", "n": 14, "mats": ("tail_a", "tail_b")},
               "whiskers": 3, "teeth": "yellow", "coat": {"belly": "fur_light", "streak": 0.15}},
        motion={"idle": "sniff", "walk": "bound", "tell": "rear", "attack": "lunge_bite",
                "hurt": "knock_squash", "death": "topple_side"},
        data=dict(level=2, role="normal", element="none", race="beast", codex="valley_shore",
                  attacks=[("bite", 0.35, 36)], ai="melee", loot=[("rat_tail", 0.6)]),
        sound="race")                                          # the race's voice unless named
```

One spec writes all of these:
- the `enemies.json` row (through `mob()`);
- the `loot_tables` row;
- the `foes.json` block and sheets (through `Spec` and the plan);
- the voice line in `sound.json`;
- the codex page;
- the wiki.

**Escape hatch:** `pose="creature.rat:rat"` keeps a hand-written module, so migration is species by species.

**Migration:**
1. Write each plan from its species.
2. Diff the new sheet against the old one per frame. Accept either an exact match or a reviewed diff: numerical
   checks cannot certify visual alignment (AGENTS.md rule 3), so the gallery is reviewed by eye.
3. The 110 species that still draw with side-view stand-ins then need only a spec.

**What it saves:**
- A top-down species: 95–304 lines of pose code (rat 129 lines, about 1,900 tokens) plus rows in three files, against
  a spec of about 20 lines (about 300 tokens).
- The 110 species left: about 22,000 lines against about 2,500.

**Tests:**
- `build_foes` determinism;
- every plan's action frame counts and `HIT_FRAME`;
- the elite ring;
- `data_validation` (enemies, loot, codex);
- `sound --check`;
- the foe gallery (`topdown_figure_gallery`), reviewed.

### 6.3 NPC engine (E3)

**What exists to build on:**
- `story.py` `npcs()` and `outfit()`: 127 NPCs as hand dictionaries, about 480 lines;
- `topdown_life.py` `LOOPS`, `work`, `extras` and `LEASH`;
- the room engine's anchors;
- `economy.py` shops;
- the character pipeline (every hair, shirt and dye is already a set).

**Spec** (a real NPC: `washer_mei`, today spread over `npcs.json` via `story.py`, `topdown_life.py`,
`topdown_rooms.py` `r.at("npc_washer_mei", 14, 31)` and her quest in `story.py:2329`):

```python
npc("washer_mei", "Washer Mei", title="Villager",
    look=dict(body="light", hair="ponytail", hair_color=2, shirt="cardigan:white", pants="straight", shoes="slippers"),
    home=("lf_village", "river_bank@14"),                       # an anchor of the room engine
    work=dict(loop="laundry", spots="auto:water_edge,washing_line"),
    lines=["Aunt Ping says you're finally awake before noon.", "The river's cold as winter this morning."],
    barks=["Scrub, scrub."], gives=["the_muddy_wash"],
    schedule={"night": ("lf_village_night", "npc_granny_night")})   # her place in the night variant, if any
```

**Role templates** cover the sect staff:

| Template | Examples |
|---|---|
| `steward` | `jade_steward`, `cloud_steward` |
| `deacon` | the deacons |
| `disciple` | `disciple_a`/`disciple_b` |
| `smith` | the sect smiths |
| `physician` | the sect physicians |

`story.py` already keeps these in paired lists (`STEWARDS`, `DEACONS`, …). A template sets the outfit, the work loop,
the service and the barks, and the spec gives only the name and the sect.

**Migration:** generate the three outputs and diff them byte for byte. Start with Lotus Ferry's villagers, whose work
loops exist, then the two sects' staff.

**What it saves:** an NPC today is about 8 lines in `story.py`, 1–3 lines with hand spots in `topdown_life.py`, one
`r.at` and hand hooks. It becomes one spec of about 10 lines, and the spots follow the room.

**Tests:**
- `topdown_life --check` (spots stand, walk legs clear, within `LEASH`);
- `data_validation` (npcs, services, shops);
- `story.validate`;
- `tutorial_order` and `topdown_tutorial`.

### 6.4 Item engine (E4)

**What exists to build on:**
- `items.py`: `item()`, `MID_ILV`, `GRADE_WORD`, `ATTRIBUTE_REQ`, `GRADE_DYE`, `ARMOUR`, `pills()`, `HERB_AGE`;
- `gear.py` `ARCHETYPES`;
- `tools/icons/families/pills.py` `PILL_GRADES`: the icon is already vessel × grade material;
- `curves.json`;
- `wiki.py` and `data_validation`'s `item_source_suite` (sources and gaps).

**Spec** (family × tier):

```python
family("pill.qi_gathering", kind="pill", vessel="jar", tiers=("common", "earth", "heaven", "mystic"),
       name="{tier_word} Qi Gathering Pill",
       effect=dict(kind="add_progress", amount="curve:pill_qp[tier]"),     # fixed amounts: phase 1's decision
       price="curve:pill_price[tier]", ilv="MID_ILV[tier]",
       sources=dict(shop={"granny_liu": ["common"]}, recipe="alchemy", loot="chests>=tier"),
       sinks=("use", "sell", "gift"))
```

One family writes all of these:
- the `items.json` rows;
- the recipes (through `crafts.py`);
- the shop lines;
- the loot lines;
- the icon ids, with the vessel and grade kit;
- each tier's balance values from the curves.

Gear works the same way: `gear("jian", grades=MID_ILV.keys(), archetypes=...)` on `ARCHETYPES`.

**Migration:** one family at a time, in this order:
1. pills;
2. herbs by age;
3. ores;
4. beast parts;
5. gear by family × grade.

Each step must show an empty data diff.

**What it saves:** a new tier ladder today touches 4–5 files (the item row, shop, recipe, loot and icon); a family is
about 10 lines for 4–9 items. `wiki --gaps` stays empty by construction, because a family must name a source.

**Tests:**
- `wiki.py --gaps`;
- `data_validation` `item_source_suite`;
- `balance_sim` (prices, and Qi per hour from pills);
- icon build determinism.

### 6.5 Quest engine (E5)

**What exists to build on:**
- `story.py` `quest()`, `o()`, `item()`, `taels()` (already compact: 4–6 lines a quest);
- the daily `mission_templates.json`;
- `unlocks.json`'s guided quests.

**Spec:** templates for `talk`, `fetch`, `clear`, `deliver`, `gather`, `spar` and `escort`. The engine derives
`target_room` from the spawns, `requires` from the room's level band, and the rewards from a band table.

```python
side("the_muddy_wash", "clear", giver="washer_mei", target=("reedtail_rat", 6), band="village",
     offer="Rats in the reeds again. They chew the lines and drag the washing through the mud. Six of them, at least.",
     done="Clean sheets for once. Bless you.")
```

Today that quest is 4 lines with its room, realm and reward chosen by hand (`story.py:2329`).

**Migration:** side and daily quests only. The prologue and the main story stay hand-written: they are beats, not
templates.

**What it saves:**
- a smaller per-quest gain (about 40%);
- more importantly, rewards and requirements follow the bands, which is phase 1's fixed-amount progression in one
  table.

**Tests:**
- `story.validate`;
- `valley_run`/`prologue_run` unchanged;
- `balance_sim` (reward per hour);
- `tutorial_order`.

### 6.6 Cue and notice engine (E6)

**What exists to build on:**
- `WorldShared.play` and `hud._handle`;
- `sound.py`, where hits, steps, foes, beds and life sounds are already tables;
- `combat_feel.json` and `moments.json` (the big set pieces are already data).

**Spec** (a real case, `hud.gd` `"item_blooded"`):

```json
{"event": "item_blooded", "log": {"key": "hud.item_blooded", "args": ["item_name:item"], "colour": "MIST"}}
{"event": "wall_kicked", "when": {"actor": "active"}, "fx": {"kind": "spark", "at": "feet+(-14*side,-50)", "colour": "PAPER", "dur": 0.25}}
```

**Migration:** the one-line cases first (about 180 of `hud._handle`'s 234, most of `WorldShared.play`). The code
cases become named handlers the table calls.

**What it saves:** about 700 lines of match arms become about 250 rows, and a new event's toast is one row.

**Tests:**
- `contract_tests` (every table event is in the event contract);
- `tutorials` and the HUD checks in `rules_tests`;
- a notices snapshot.

**Status (phase 2, E6 world half): done.** `docs/architecture/cues.md` has the format and how to add a cue.
- `tools/data/cues.py` writes `data/cues.json`: 60 rows for 41 events, a row a line. `WorldShared.play` plays the first
  row of an event whose `when` holds, and `Cues` (`scripts/presentation/cues.gd`) reads the table. Its conditions,
  values, colours and texts are meant for the HUD half too, whose texts are already moments.json's (`MomentRules.text`).
- `WorldShared.play` and `_treasure` went from 178 lines of arms to 102: the player, its anchors and the five
  handlers. `world_shared.gd` is 76 lines shorter. The reader, `cues.gd`, is 93 lines and is meant to serve the HUD's
  234 arms as well; a new world cue is now a row.
- Five answers stay code, named by a row's `call`: a blow's hit and words (`CombatFx`), a drop's `LootView`s, what a use
  did (`UiKit.use_parts`) and the flute's scattered notes.
- The top-down room had no copy of these answers. Its artifact spirit's line is now a row. Its array light, its parry
  mark and its casts stay its own, and so do the side view's answers and the audio director's `EVENT_SFX`.
- Every sample payload of every arm, played on a stub host with the random seed fixed, makes the same effects,
  sounds, shakes and random draws before and after. The new suite `cue_tests` checks every row against the game and
  plays each once.

### 6.7 Technique engine (exists), FX and sound

`tools/data/technique_gen.py` and `technique_grammar.py` already generate 3,171 techniques from forms × rings ×
elements × families. They write compact rows with `defaults` that `ContentDB.expand` merges. It is the model for the
others. Extend it rather than replace it.

The FX sheets (`build_fx_topdown.py`: 24 forms × 11 elements) and the sounds (`sfx_pass.py` families × materials) are
already generated by grammar, so no new engine is needed. E6 covers when they play.

## 7. Phase 2: the slices

**Assumptions:** phase 1 lands first. Its jobs edit these files:

| Phase-1 job | Files it edits |
|---|---|
| **Tutorial bugs** | `scripts/ui/tutorial_coach.gd`, `scripts/core/tutorial_rules.gd`, `scripts/hud.gd` (tours), `tools/data/tutorials.py`, `tests/tutorials.gd`, `tests/topdown_tutorial.gd` |
| **First boss** | the Hollowed Eel: `tools/data/enemies.py`, `scripts/simulation/ai/enemy_brain.gd`/`topdown_brain.gd` (phase 2 at 80%), `enemy_authority.gd`, `tools/data/scenes.py` plus `scene_director.gd` (the elders' scene), `tests/hollow_night.gd`, `tools/dev/topdown_capture.gd` |
| **Progression, quick slots and the bag** | `tools/data/stats.py`, `items.py`, `story.py`, `curves`; `combat_authority.gd` (the charged attack), `progression_authority.gd` (meditation, fixed experience), `quest_authority.gd`, `inventory_authority.gd` (50 slots), `hud.gd` (three quick slots), `inventory_page.gd`, `tests/rules_tests.gd`, `tests/balance_sim.gd` |

Every slice below rebases onto those changes. The ones that touch the same files wait for phase 1 (the
`after_phase1` column in the JSON).

**Rules for every slice:**
- behaviour identical, except the named bug fixes;
- `tools/run_tests.sh` green, with `perf_tests` judged by S2's least-of-N;
- one owner per file for the whole slice;
- data builds must show an empty `git diff` unless the slice drops a field on purpose.

| Wave | Slice | What | Owns | Size | Risk | Guarded by |
|---|---|---|---|---|---|---|
| 1 | **S1** | Delete dead code (DEAD-01/02/05/06/07) and fix the save-id crash (BUG-01) | the listed lines; the `crafts_page.gd` lookups and a load-time sweep | about 300 lines removed, about 40 changed | low | run_tests.sh, `contract_tests` |
| 1 | **S2** | Tests: `tests/lib/suite.gd`, the `side_view_suite` (the 5 green legacy scripts), delete the 4 broken ones, least-of-N `perf_tests`, the data-method rule (BUG-06) | `tests/**`, `tools/run_tests.sh`, `Test.ps1` | about 150 new, about 200 removed | low | every suite's check count unchanged |
| 1 | **S3** | Tools: the capture registry (fold the 7 probes and `topdown_capture`'s 59 scenes into rows), move the side-view pipeline to `tools/art/sideview/`, archive `study_quality`, `atlas.pack()` | `tools/dev/*`, `tools/art/{creatures,pixel.py,helpers_*,bake_*}`, `tools/backdrops`, `combo_rig`/`equipment_rig` | moves about 32,000 lines, rewrites about 2,000 | low (no game code) | each moved generator rebuilds byte-identical |
| 1 | **S4** | Shared runtime: `FrameMemo`, `Noise`, `Figures`, lazy ContentDB tables (BUG-11), GameEvents sets (BUG-03), the TopdownFx cap (BUG-04) | the new `scripts/core/*.gd`, `content_db.gd`, `game_events.gd`, `topdown_fx.gd`, one line in each of the 12 pages | about 250 new, about 350 removed | medium (boot order) | run_tests.sh, `perf_tests` (boot and room load), `engine_tests` |
| 1 | **S5** | Generators: `common.run_cli`, `tools/lib/pix.py` for new work, Grid thresholds from `movement.json` plus a parity test, drop dead data, fields, manifest ids and string keys | `tools/data/common.py`, `topdown_rooms.py` (Grid), the field-owning generators, `tools/lib/` | about 400 changed | low | `build_data.py` then `git diff` (only the dropped fields); every `--check` |
| 2 | **S6** | `hud.gd` split (`hud/input`, `hud/layout`, `hud/notices`, `hud/panels`, `hud/tours`) and the notice table (E6, HUD half) | `scripts/hud.gd`, `scripts/hud/*`, `data/hud_notices.json`, `tools/data/cues.py` | 3,266 moved; about 450 lines of arms become about 180 rows | medium | `tutorials`, `topdown_tutorial`, `rules_tests` HUD checks, `hud_capture` before and after |
| 2 | **S7** | `main.gd`: the debug flags to `scripts/shell/debug_args.gd`, the page table to a registry | `scripts/main.gd`, `scripts/shell/debug_args.gd` | about 550 moved | low | the flag-driven captures, `tutorials`, `perf_tests` |
| 2 | **S8** | `combat_authority.gd` into parts (`combat/flight.gd`, `arts`, `phantom`, `flying_sword`, `melody`, `blood`, `arrays`, `swarm`, `talismans`, `projectiles`, `treasures`); state and facade unchanged | `combat_authority.gd`, `authority/combat/*` | 2,819 moved | medium | `rules_tests`, `balance_sim`, `hollow_night`, `valley_run` |
| 2 | **S9** | `world_authority.gd` into parts (ambush, herbs, arrays, objects, loot, hazards, voyages, events, nests, tower, idle) | `world_authority.gd`, `authority/world/*` | 2,296 moved | medium | `room_sweep`, `tutorial_order`, `valley_run`, `places_tests` |
| 2 | **S10** | `crafting_authority.gd` and `progression_authority.gd` into parts | both, and their part folders | 3,865 moved | medium | `rules_tests`, `balance_sim`, `valley_run` |
| 2 | **S11** | Public surfaces: the 56 private cross-calls to public names, `BrainKit`, a `contract_tests` rule forbidding `other._x(` | the call sites, `scripts/simulation/ai/*` | about 200 changed | low–medium | `contract_tests`, `rules_tests`, `hollow_night` |
| 2 | **E6** | The cue table for `WorldShared.play` | `world_shared.gd`, `data/cues.json`, `tools/data/cues.py` | about 250 | low | `audio_tests`, the FX checks, captures before and after |
| 3 | **E1** | Room engine; migrate the 27 layouts by round trip; then new rooms | `tools/content/rooms/` (new), `tools/data/topdown_rooms.py` | about 900 new; the 1,778-line file becomes specs | medium | `topdown_rooms`/`places`/`room_lint`/`sect_walks --check`, `topdown_tutorial` |
| 3 | **E2** | Monster engine: plans from the 12 species, then specs | `tools/content/monsters.py`, `creature/plans/`, `creatures.py`, `enemies.py` | about 1,200 new | medium (visual) | `build_foes` determinism, `data_validation`, gallery review |
| 3 | **E3** | NPC engine (after E1, for anchors) | `tools/content/npcs.py`, `story.py` `npcs()`, `topdown_life.py` work and extras | about 500 new | low–medium | `topdown_life --check`, `data_validation`, `tutorial_order` |
| 3 | **E4** | Item engine | `tools/content/items.py`, `items.py`, `gear.py` | about 600 new | medium (balance) | `wiki --gaps`, `data_validation`, `balance_sim` |
| 3 | **E5** | Quest engine (side and daily; after E3) | `tools/content/quests.py`, `story.py` `side_quests()` | about 400 new | low–medium | `story.validate`, `valley_run`, `balance_sim` |
| 3 | **S12** | Freeze the side view behind `RoomSpace`: its files to `scripts/sideview/`, the 74 branches out of the authorities. Optional: delete instead if the product retires the fallback | the DEAD-15 files, and the branches in `world_`/`enemy_authority` and `ally_brain` | about 400 changed, 2,233 moved | medium–high | the `side_view_suite`, `engine_tests`, `visibility_suite`, `room_sweep`, `valley_run` |

**Order and parallelism:**
- **Wave 1** (S1–S5) runs in parallel as soon as phase 1 lands. The five slices own disjoint files, and S1's `hud.gd`
  and `tutorial_coach.gd` lines go last.
- **Wave 2** (S6–S11 and E6) can run five at a time: S6 (HUD), S7 (main), S8 (combat), S9 (world), S10 (crafting
  and progression) and E6 (`world_shared`) own different files. S11 goes after S8–S10, so its renamed methods land in
  their final files.
- **Wave 3:**
  - E1, E2 and E4 run in parallel;
  - E3 needs E1's anchors;
  - E5 needs E3;
  - S12 goes last and only if the fallback stays.

**Why this order:** dead code and shared utilities first shrink the files the splits must move and give them their
helpers (FrameMemo, Figures, the suite base). The splits come before the engines so E6's notice table lands in a small
`hud/notices.gd` rather than inside a 3,266-line file.

### Status: S5 (generator hygiene), done

- **DUP-11, the generator command line: done.** `tools/data/common.py` has `emit()` (every generated file, written
  only when it changed, or compared with `--check`) and `run_cli()`: every module of `build_data.py`'s list and
  `topdown_rooms.py` take `--write`, `--check` and `--only`, with exit codes 0, 1 and 2 (`tools/data/README.md`).
  `sect_walks.py` and `room_lint.py` are checks, not generators, and keep their own flags.
- **DUP-10, the grid's walking rules: done.** The Python Grid reads `step_up` and the jump from `data/movement.json`.
  `topdown_rooms.py --check` compares it with the game's `TopdownRoom` and `TopdownRoute.reach`, through
  `tools/data/grid_parity.tscn`, on every layout: 27 layouts, 95 starts, all equal.
  - Still copied: `tests/topdown_tutorial.gd` `reach()` repeats the Grid's on-foot rules, with 32.5 and 8.0 written
    in. The game has no discrete form of a running jump to call instead.
  - The room graph route (`sect_walks` against `WorldRules.route`) is unchanged.
- **DUP-08, the pixel libraries: done for new work.** `tools/lib/pix.py`, with `--check` against its sources. The
  hash and noise copies in `canvas.py`, `creature/motion.py`, `fxpix.py` and `topdown_life.py` import it.
  - The four old libraries stay with their art. `pixlib` samples pixel corners and draws polygons through PIL, and
    its `shift` moves a mask where the icons' reads a neighbour, so moving their art onto `pix` is a redraw.
- **DEAD-12, data the game never reads: done.**
  - `balance.json`, `legendary_chains.json` and `td_review_heights.json` moved to `tests/data/`. Their readers
    changed to match: `balance_sim`, `data_validation`, `rules_tests`, the wiki, `moments.py` and `topdown_capture`.
  - The dropped fields: techniques' `mastery`, shops' `buys_all`, enemies' `weak_to` and `equipment_chance`, zones'
    `laws` and `exit`, and `same_stage_ok` on unlocks and quests (its check moved into `story.validate`).
  - S1 removed the readers of the NPCs' `age` and of `sound.json`'s `steps.materials`, so those went too.
  - Kept: `named.archetype` and the sets' `archetype`, which `data_validation`'s item-plan checks and the wiki read.
  - `core.qp_pct` had already gone in phase 1.
- **DEAD-13 and DEAD-14: done.** The 20 manifest ids are gone with their drawings (8 icons, 8 props, 4 UI assets),
  and so are the 51 `ui.*` string keys. The 11 `world_view.*` keys stay.

## 8. Rerunning the audit

Every scan is read-only and writes JSON only where asked:

| Script | What it does |
|---|---|
| `tools/dev/audit/inventory.py` | Lines, files and functions per area; the largest files |
| `tools/dev/audit/gd_graph.py` | The script graph, symbol use, signals, autoloads, cross-authority calls |
| `tools/dev/audit/py_graph.py` | Generator imports, entry points, unreferenced defs |
| `tools/dev/audit/asset_refs.py` · `manifest_refs.py` | Art files and manifest ids nothing names |
| `tools/dev/audit/data_refs.py` · `strings_refs.py` | Data tables and row fields the game never reads; unasked string keys |
| `tools/dev/audit/dupes.py` | Clone detection (exact and shape modes) |
| `tools/dev/audit/hot_paths.py` · `smells.py` | Per-frame allocation map; bug patterns |
| `tools/dev/audit/funcs.py` · `mentions.py` · `run_legacy.py` | Function sizes; who names a file; running the tests no suite runs |
| `tools/dev/audit/findings.py` | Runs them all and writes `docs/architecture/audit_45.json` |

The JSON's `findings[]` are the curated items: id, category, where, method, confidence, severity, action and slice.
`engines[]` and `slices[]` repeat §6 and §7 in machine form, and `scans` keeps each scan's summary and lists.
