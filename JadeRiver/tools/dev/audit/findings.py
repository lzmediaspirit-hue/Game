#!/usr/bin/env python3
"""Audit 45: writes docs/architecture/audit_45.json, the machine-readable half of docs/architecture/audit_45.md.

Usage: python3 tools/dev/audit/findings.py [--out docs/architecture/audit_45.json] [--no-scan]

It runs every read-only scan of this folder (inventory, gd_graph, py_graph, asset_refs, manifest_refs, data_refs,
strings_refs, dupes, hot_paths, smells) into a temporary folder, keeps their summaries and their lists, and adds the
curated findings below (each read and confirmed by a person: where, how it was checked, confidence, severity, the
phase-2 slice that owns it), the engine designs and the phase-2 slices. `--no-scan` writes the curated part alone.
Deterministic apart from the scans' own inputs: the JSON is sorted and has no timestamps.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

# ---------------------------------------------------------------------------------------------------------------------
# The baseline (tools/run_tests.sh on the untouched tree, commit 35105ac, 2026-09-30, four agents sharing the machine).
BASELINE = {
    "commit": "35105ac",
    "gates": {"room_lint": "168 rooms, 0 failing", "topdown_rooms": "current", "sect_walks": "hold", "places": "26 places",
              "sound": "current, 271 files", "audio_check": "0 failing"},
    "suites": {"engine_tests": [3908, 0], "data_validation": [50302, 0], "room_sweep": [3736, 0], "visibility_suite": [6758, 0],
               "rules_tests": [2695, 0], "contract_tests": [1084, 0], "balance_sim": [177, 0], "perf_tests": [18, 1],
               "prologue_run": [103, 0], "tutorial_order": [434, 0], "topdown_tutorial": [969, 0], "tutorials": [87, 0],
               "story_scenes": [90, 0], "hollow_night": [47, 0], "audio_tests": [56, 0], "valley_run": [3007, 0],
               "places_tests": [16, 0]},
    "total_checks": 73487,
    "total_failures": 1,
    "failed": ["perf_tests: 'the crowd under the breakthrough and a sword swarm fits the budget (13.03, 16.66 ms)'"],
    "note": "perf_tests is timing-bound: rerun alone under load average 7.7 on 4 cores it failed 5 of 18 (room load "
            "330 ms, crowd 18 ms, techniques.json 191 ms, the wood tree drag, Lotus Ferry 473 ms). Every other suite passed.",
}

# The tests no suite runs, each run once with `godot --headless -s` (tools/dev/audit/run_legacy.py, 180 s limit).
LEGACY_RUN = {
    "tests/combo_tests.gd": "pass 2057/2057", "tests/landing_matrix.gd": "pass 1354/1354", "tests/map_generation.gd": "pass 76/76",
    "tests/movement_v07.gd": "pass 30/30", "tests/room_gates.gd": "pass 276/276",
    "tests/movement_review_v09.gd": "exit 1 (run, line 52)",
    "tests/obstacle_review.gd": "compile error: Identifier not found: GameEvents",
    "tests/platform_contact.gd": "compile error: Identifier not found: GameEvents",
    "tests/upward_landing.gd": "compile error: Identifier not found: GameEvents",
    "tests/pixel_input.gd": "exit 2: needs a window",
    "tests/support_review_v08.gd": "timeout (opens a review window)", "tests/generated_runtime.gd": "timeout",
    "tests/gauntlet_review.gd": "timeout", "tests/release_review.gd": "timeout", "tests/visual_checks.gd": "timeout",
    "tests/weapon_combo_outlines.gd": "timeout",
}

# ---------------------------------------------------------------------------------------------------------------------
F = []


def finding(fid, category, title, where, method, confidence, action, slice_id, severity=None, lines=0, evidence=""):
    F.append({"id": fid, "category": category, "title": title, "where": where, "method": method,
              "confidence": confidence, "severity": severity, "lines": lines, "evidence": evidence,
              "action": action, "slice": slice_id})


GREP = "grep of every .gd/.tscn/.json/.sh for the name as a token and as a string (call/has_method/Callable/connect), load/preload paths, class_name, scene ext_resources (tools/dev/audit/gd_graph.py)"

# ---- dead code: scripts and files
finding("DEAD-01", "dead_script", "scripts/ornament.gd and scripts/room_gate.gd: nothing loads them",
        ["scripts/ornament.gd", "scripts/room_gate.gd"], GREP + "; not reachable from project.godot, any suite or any tool scene",
        "high", "delete both (and their .uid)", "S1", lines=42,
        evidence="room_gate.gd's job moved to topdown_gate.gd and the side view's portal_view.gd; architecture.md still names room_gate.gd")
finding("DEAD-02", "dead_file", "scripts/connection_visual.gd.uid has no script", ["scripts/connection_visual.gd.uid"],
        "file walk: a .uid whose .gd is missing", "high", "delete", "S1", lines=1)
finding("DEAD-03", "tool_only_script", "scripts/combo_rig.gd and scripts/equipment_rig.gd run only from tests/bake_combos.gd, tests/bake_equipment.gd and tools/bake_hat_cape_combos.gd (v0.13 side-view bakes)",
        ["scripts/combo_rig.gd", "scripts/equipment_rig.gd"], GREP, "high",
        "move to tools/art/sideview/ with their bake scripts (they are art tools, not game code)", "S3", lines=99)
finding("DEAD-04", "test_only_script", "scripts/simulation/map_validator.gd and world_catalog.gd are reached only by tests/map_generation.gd (not a suite)",
        ["scripts/simulation/map_validator.gd", "scripts/simulation/world_catalog.gd"], GREP, "high",
        "move under tests/lib/ with map_generation.gd, or delete with the v0.9 map generator tests", "S2", lines=121)
finding("DEAD-05", "dead_function", "Unreferenced functions in game code (name found nowhere else, no string use, no dynamic prefix)",
        ["scripts/audio/sound_bank.gd:42 surface_of_material", "scripts/audio/sound_bank.gd:119 is_night",
         "scripts/avatar.gd:72 still_image", "scripts/presentation/sprite_cache.gd:152 icon_ready",
         "scripts/presentation/technique_picture.gd:948 draw_cooldown", "scripts/presentation/technique_picture.gd:965 draw_qi_short",
         "scripts/simulation/rules/technique_tree_rules.gd:193 tree_state", "scripts/topdown/topdown_life.gd:533 critter_count",
         "scripts/ui/pages/techniques_page.gd:554 _slot"], GREP, "high", "delete", "S1", lines=74)
finding("DEAD-06", "dead_const", "Unreferenced constants and member variables",
        ["scripts/ui/ui_kit.gd:222-228 T_HINT T_CAPTION T_ROW T_BODY T_BUTTON D_HEADING", "scripts/ui/page.gd:44 GROUP_GAP",
         "scripts/ui/pages/mail_page.gd:8 DESK", "scripts/ui/tutorial_coach.gd:22 MISSING_S", "scripts/ui/tutorial_coach.gd:45 _tab_was",
         "scripts/presentation/sprite_cache.gd:68 ICON_PX", "scripts/presentation/scene_rules.gd:27 TARGETS",
         "scripts/hud.gd:111 meditate_center", "scripts/hud.gd:113 sphere_center", "scripts/hud.gd:114 sense_center"],
        GREP, "high", "delete (tutorial_coach.gd and hud.gd after phase 1 lands: the tutorial job edits them)", "S1", lines=16)
finding("DEAD-07", "dead_signal", "Signals emitted but never connected: world.gd room_changed and context_changed, topdown_world.gd context_changed, hud.gd page_changed",
        ["scripts/world.gd:54", "scripts/world.gd:55", "scripts/topdown/topdown_world.gd:100", "scripts/hud.gd:131"],
        "regex for <name>.connect / connect(\"name\") / signal=\"name\" in every .gd and .tscn", "high",
        "drop the signals and their emit lines (context is read from world.context each frame by the HUD)", "S1", lines=8)
finding("DEAD-08", "test_only_api", "42 game-code symbols used only by tests or tools (set_state, touching, lock_left, restore_authoritative_snapshot, MapGenerator.generate ...)",
        ["see symbols[status=not_used_by_game] in this file"], GREP, "medium",
        "keep the deliberate test hooks (a suite needs them) but mark them `## test hook`; delete the rest with their tests (map_generator.generate, equipment_rig.render_sheet)",
        "S1", lines=439)
finding("DEAD-09", "stale_test", "27 SceneTree scripts under tests/ that no suite runs (1,634 lines); 22 were imported with v0.13 and never touched since",
        ["tests/combo_tests.gd", "tests/landing_matrix.gd", "tests/map_generation.gd", "tests/movement_v07.gd", "tests/room_gates.gd",
         "tests/movement_review_v09.gd", "tests/obstacle_review.gd", "tests/platform_contact.gd", "tests/upward_landing.gd",
         "tests/support_review_v08.gd", "tests/generated_runtime.gd", "tests/review_visual_v08.gd", "tests/review_visual_v09.gd",
         "tests/visual_checks.gd", "tests/weapon_combo_outlines.gd", "tests/weapon_combo_visual.gd"],
        "tools/run_tests.sh and Test.ps1 suite lists; each run with godot -s (tools/dev/audit/run_legacy.py)", "high",
        "five still pass (combo_tests 2057, landing_matrix 1354, map_generation 76, movement_v07 30, room_gates 276 checks): wire them into one `side_view_suite` run by run_tests.sh while the fallback exists; delete the four that no longer compile or exit 1 (obstacle_review, platform_contact, upward_landing, movement_review_v09) and the review/visual scripts that only open windows",
        "S2", lines=1634)
finding("DEAD-10", "stale_probe", "tools/dev probes and captures no runner, doc or test names since their decision closed",
        ["tools/dev/fix_infer.py (one-off := fixer, 2026-09-24)", "tools/dev/stat_probe.gd", "tools/dev/sect_capture.gd",
         "tools/dev/places_capture.gd", "tools/dev/picture_capture.gd", "tools/dev/tutorial_capture.gd", "tools/dev/combat_trace.gd"],
        "tools/dev/audit/mentions.py: docs, code and runners naming each stem, and its last commit", "medium",
        "keep topdown_capture/hud_capture/prototype_qa/wiki/extract_strings/ui_style_audit; fold the per-decision capture scenes into one capture registry (data: shot name -> room, setup, camera) so a new review is a row, not a 150-line script; delete fix_infer.py",
        "S3", lines=1389)
finding("DEAD-11", "stale_generator", "Side-view art generators frozen since decision 41 (paused side-view art); several one-off bakes nothing runs",
        ["tools/art/bake_act2_hats.py (named nowhere)", "tools/art/bake_straw_hat.py", "tools/bake_hat_cape_combos.gd",
         "tools/art/build_creatures.py", "tools/art/build_topdown_proto.py (22 lines, superseded by build_tiles.py)",
         "tools/art/topdown/study_quality/ (decision 42 study, 1,857 lines, copies raster.py and folds.py)",
         "tools/icons/study/technique_cards.py (594 lines, no caller)"],
        "tools/dev/audit/py_graph.py (imports, entry points, names outside Python) and mentions.py", "medium",
        "move the side-view pipeline (tools/art/creatures, pixel.py, helpers_batch_*, bake_*, tools/backdrops) under tools/art/sideview/ with a README saying it is frozen; delete build_topdown_proto.py and the study copies once the study's pictures are archived",
        "S3", lines=2889)
finding("DEAD-12", "dead_data", "Data the game never reads",
        ["data/balance.json (tests/balance_sim.gd only)", "data/legendary_chains.json (tests and wiki only)",
         "data/topdown/td_review_heights.json (tools only)",
         "techniques.json mastery.dmg_per_tier and mastery.cost_per_tier (117 rows each; the game reads stats.json mastery_cost_per_tier)",
         "unlocks.json/quests.json same_stage_ok (111 rows, read by data_validation only)", "shops.json buys_all (11)",
         "items.json core.qp_pct (44 cores; the Qi comes from each core's effects)", "enemies.json weak_to (4), equipment_chance (3)",
         "artifacts.json named.archetype (29)", "sets.json archetype (5)", "zones.json laws, exit.to_zone (3)"],
        "tools/dev/audit/data_refs.py: table names as strings in scripts/, row keys as strings or .attribute tokens; each confirmed by grep", "medium",
        "move balance.json and legendary_chains.json out of data/ (ContentDB loads every data/*.json at boot) into tests/data or tools/data; drop the unread fields in their generators; keep same_stage_ok as a generator-side check",
        "S5", lines=0)
finding("DEAD-13", "dead_asset", "Manifest ids nothing names: 8 legacy icons (elite_crown, gathering_log, player_arrow, portal_marker, portal_sealed, quest_main, quest_side, vendor), 8 props (broken_ring, leviathan_bones, star_iron_vein, stone_steps, void_geode, void_orchid_patch, war_drum, wooden_bridge)",
        ["data/icon_manifest.json", "data/prop_art.json"], "tools/dev/audit/manifest_refs.py (every string in data and scripts, prefix-composed keys)", "medium",
        "drop from their generators' lists (tools/icons, tools/props) and rebuild", "S5", lines=0,
        evidence="every one of the 6,714 files under art/ is named by some manifest (asset_refs.py): the only unnamed files are 4 font licences, which must stay")
finding("DEAD-14", "dead_string", "About 62 player-facing string keys nothing asks for (ui.begin, ui.continue, ui.new_game, the Works page's *_note, ...)",
        ["data/strings/en.json", "tools/data/ui_strings.json"], "tools/dev/audit/strings_refs.py: literals in scripts and tests, data strings, composed prefixes, Tx.plural's _one",
        "medium", "remove from tools/data/ui_strings.json after a grep per key (the 11 world_view.* keys are built from data prefixes: keep)", "S5", lines=62)
finding("DEAD-15", "side_view_only", "Side-view-only game scripts: 13 files, 2,233 lines, reachable only through world.gd, backdrop.gd and the Avatar fallback",
        ["scripts/world.gd 653", "scripts/player.gd 774", "scripts/backdrop.gd 124", "scripts/avatar.gd 125", "scripts/presentation/volume_view.gd 124",
         "scripts/simulation/map_generator.gd 128", "scripts/presentation/decor_views.gd 70", "scripts/occlusion_outline.gd 50",
         "scripts/presentation/climbable_view.gd 46", "scripts/simulation/room_travel.gd 43", "scripts/scenery_prop.gd 42", "scripts/arrow.gd 34", "scripts/shadow.gd 20"],
        "reachability from project.godot with main.gd's edges to world.gd and backdrop.gd cut (gd_graph.json references)", "high",
        "not dead: decision 41 keeps the side view as the new-game fallback setting. Freeze it: move to scripts/sideview/, keep its suites green, add nothing; delete only if the fallback setting is retired (a product decision)",
        "S12", lines=2233)

# ---- duplication
finding("DUP-01", "duplication", "Seven hand-rolled per-frame caches keyed on Engine.get_process_frames() and Game.revision",
        ["scripts/presentation/world_shared.gd:28 _frame_memo", "scripts/hud.gd:542 _frame_badges", "scripts/hud.gd:2033 _look_frame",
         "scripts/topdown/topdown_world.gd:555 soft_target", "scripts/ui/pages/posts_page.gd:172 _rows_frame",
         "scripts/simulation/rules/place_rules.gd:137 _home_cache (60-frame TTL)", "scripts/presentation/sprite_cache.gd:24 slice budget"],
        "grep get_process_frames() in scripts/ (22 uses)", "high",
        "one FrameMemo (scripts/core/frame_memo.gd): memo(owner, key, callable, ttl_frames=1, on_revision=true)", "S4", lines=80)
finding("DUP-02", "duplication", "Five copies of the sin-hash noise and one integer hash",
        ["scripts/presentation/fx_layer.gd:682 _hash", "scripts/presentation/hazard_view.gd:179 _h", "scripts/ui/pages/map_page.gd:1308 _rnd",
         "scripts/ui/pages/beast_kit.gd:9 noise", "scripts/ui/pages/inventory_page.gd:87 _hash", "scripts/topdown/topdown_terrain.gd:230 h01"],
        "grep 12.9898 (5 files) and 374761393", "high", "scripts/core/noise.gd: Noise.h01(i, salt), Noise.cell(x, y, s), Noise.value(x, y, s)", "S4", lines=30)
finding("DUP-03", "duplication", "`TopdownDoll.new() if TopdownDoll.shown() else Avatar.new()` and its dress/draw branches in 12 files (18 sites)",
        ["scripts/ui/pages/character_page.gd", "scripts/ui/pages/shop_page.gd", "scripts/ui/pages/inventory_page.gd", "scripts/ui/pages/cultivation_page.gd",
         "scripts/ui/pages/techniques_page.gd", "scripts/shell/shell_screens.gd", "scripts/presentation/technique_picture.gd",
         "scripts/presentation/technique_preview.gd", "scripts/presentation/npc_view.gd", "scripts/presentation/enemy_view.gd",
         "scripts/player.gd", "scripts/hud.gd"],
        "grep TopdownDoll.shown|Avatar.new()", "high", "Figures.for_character(ch) / Figures.for_outfit(o, top_down): one factory, one draw_on", "S4", lines=90)
finding("DUP-04", "duplication", "Event -> presentation switches: hud.gd _handle (234 branches, 615 lines, 134 add_log + 124 toast calls), WorldShared.play (147 lines), world.gd and topdown_world.gd _on_event (70 lines each), audio_director, moment_view, scene_director, tutorial_coach, page, atmosphere, life: 11 listeners each run their own match on every event",
        ["scripts/hud.gd:1349-1963", "scripts/presentation/world_shared.gd:82-228", "scripts/world.gd:406", "scripts/topdown/topdown_world.gd:576"],
        "function sizes (tools/dev/audit/funcs.py); count of GameEvents.event.connect (11)", "high",
        "a Notice table (data/hud_notices.json: event -> log|toast, key, args from payload, colour, filter actor==active) replaces the one-line cases of hud._handle (about 180 of 234); a Cue table (data/cues.json: event -> fx, sound, shake) replaces WorldShared.play's simple cases; a dispatcher Dictionary(name -> Callable) replaces the match chains",
        "S6", lines=900)
finding("DUP-05", "duplication", "Parallel side-view and top-down implementations with 74 `topdown == null` checks in 20 shared files",
        ["scripts/world.gd vs scripts/topdown/topdown_world.gd (_build_room 92/97 lines, _on_event 69/72)",
         "scripts/player.gd vs scripts/topdown/topdown_player.gd", "scripts/simulation/ai/enemy_brain.gd vs topdown_brain.gd",
         "scripts/simulation/authority/world_authority.gd (21 checks)", "scripts/simulation/authority/enemy_authority.gd (10)",
         "scripts/simulation/ai/ally_brain.gd (8)", "scripts/hud.gd (8)", "scripts/presentation/autopilot.gd (5)"],
        "grep for room_rt.topdown ==/!= null, is World, grid ==/!= null, TopdownDoll.shown", "high",
        "a RoomSpace interface on RoomRuntime (distance, place_near, floor_at, ground_under, in_reach) with SideSpace and GridSpace; the authorities call the space and never branch. Freeze the side view's own files (DEAD-15)",
        "S12", lines=400)
finding("DUP-06", "duplication", "TopdownBrain and AllyBrain drive EnemyBrain's private helpers (_set_state, _wander, _choose_attack, _start_hop, _hop, _follow_edge)",
        ["scripts/simulation/ai/topdown_brain.gd:40-175", "scripts/simulation/ai/ally_brain.gd:70,141"], "tools/dev/audit/smells.py private_call", "high",
        "a public BrainKit (scripts/simulation/ai/brain_kit.gd) with those steps; the brains compose it", "S11", lines=60)
finding("DUP-07", "duplication", "Test boilerplate: the same check()/summary/quit block in 10 suites and the same pixel_stage preamble in 8 visual scripts",
        ["tests/contract_tests.gd:16", "tests/data_validation.gd:14", "tests/balance_sim.gd:15", "tests/audio_tests.gd:29", "tests/room_sweep.gd:32",
         "tests/visibility_suite.gd:25", "tests/perf_tests.gd:14", "tests/places_tests.gd:8", "tests/prologue_run.gd:33", "tests/tutorials.gd:51"],
        "tools/dev/audit/dupes.py --ext .gd (exact, window 6)", "high", "tests/lib/suite.gd (extends Node): check(), section(), finish(); every suite extends it", "S2", lines=110)
finding("DUP-08", "duplication", "Four pixel-drawing libraries in the Python art tools with the same line, ellipse and polygon rasterisers",
        ["tools/art/pixel.py (1,410)", "tools/icons/pix.py (951)", "tools/props/pixlib.py (573)", "tools/art/fx/fxpix.py (298)"],
        "tools/dev/audit/dupes.py --ext .py (the same 9-line line rasteriser in all four)", "high",
        "tools/lib/pix.py for the primitives; the four keep their own palettes and conventions as thin wrappers. Only for new work: rebuilding the frozen side-view art is not needed",
        "S5", lines=300)
finding("DUP-09", "duplication", "Side-view creature modules copied species to species",
        ["tools/art/creatures/riverstone_ox.py <-> thunderhorn_rhino.py <-> thornback_boar.py (515 lines)", "cloud_stag.py <-> hollow_stag.py (177)",
         "ember_fox.py <-> spark_weasel.py (148)", "mudshell_crab.py <-> tide_crab.py <-> void_crab.py (35)", "cliff_ape.py <-> snow_ape.py (18)"],
        "tools/dev/audit/dupes.py (exact, window 8)", "high",
        "frozen side-view art: no action now; the monster engine (ENG-2) is the answer for new species", "E2", lines=893)
finding("DUP-10", "duplication", "The grid's walking rules exist twice: Python (tools/data/topdown_rooms.py Grid.reach, thresholds 32.5 and 8.0 hard-coded) and GDScript (TopdownRoom/TopdownMotor, from data/movement.json topdown.*); the room graph route twice (sect_walks.route and WorldRules.route)",
        ["tools/data/topdown_rooms.py:222", "tools/data/sect_walks.py:222", "scripts/topdown/topdown_room.gd:308", "scripts/simulation/rules/world_rules.gd"],
        "reading both", "high",
        "keep both (the checks must run without Godot) but read the thresholds from data/movement.json in Python too, and add a parity test that runs Grid.reach and TopdownRoom.find_path on every layout and compares",
        "S5", lines=40)
finding("DUP-11", "duplication", "Generator CLI boilerplate: build/--check/stale/write repeated in topdown_rooms, topdown_life, places, sound, sect_walks, contract, scenes",
        ["tools/data/topdown_rooms.py:1746", "tools/data/topdown_life.py", "tools/data/places.py:342", "tools/data/sound.py"],
        "reading", "high", "tools/data/common.py: emit(path, payload, check_only) and run_cli(build)", "S5", lines=120)
finding("DUP-12", "duplication", "Atlas packing and sheet writing repeated in build_decor, build_life, build_tiles and build_foes; the study copies of raster.py (47 lines) and folds.py (56)",
        ["tools/art/topdown/build_decor.py <-> build_life.py (32 lines)", "tools/art/topdown/build_tiles.py:320 <-> :418 (23)",
         "tools/art/topdown/figure/raster.py <-> study_quality/hifi.py (47)", "tools/art/topdown/figure/kinds/folds.py <-> study_quality/looks.py (56)"],
        "tools/dev/audit/dupes.py", "high", "tools/art/topdown/atlas.py grows pack(sheets) -> (png, manifest); delete study_quality after archiving", "S3", lines=160)

# ---- bugs and smells
finding("BUG-01", "bug", "Recipe ids read from the save are dotted into ContentDB with no check: after a recipe is renamed or removed in data, a save with it in the auto-refine queue or a refine in progress crashes the Crafts page (no load-time sweep drops unknown ids)",
        ["scripts/ui/pages/crafts_page.gd:810 (ch.crafting.auto_queue)", "scripts/ui/pages/crafts_page.gd:1528 (the refine in progress)",
         "scripts/ui/pages/crafts_page.gd:716 (the selected talisman recipe)", "scripts/ui/pages/crafts_page.gd:957 (a guild exam task)"],
        "grep ContentDB.(entry|item|room|config)(...).<field> without .get (12 sites), each traced to where its id comes from; crafting_authority.gd:1991 and :1043 read ids from data and are safe", "medium",
        "ContentDB.recipe_output(id) returning '' for an unknown id, and a save-load sweep that drops unknown recipe ids from the queues", "S1", severity="low")
finding("BUG-02", "perf", "Every event is string-matched by 11 listeners, the HUD's through 234 branches: GDScript match tests them in order",
        ["scripts/hud.gd:1349", "scripts/core/game_events.gd:77 event.emit"], "reading; count of listeners", "high",
        "handler Dictionaries (DUP-04)", "S6", severity="medium")
finding("BUG-03", "perf", "GameEvents.emit_event does a linear `in` over UNLOCK_TRIGGERS (18) and SAVE_TRIGGERS (13) per event, and flush() duplicates the subscriber list per delivered event",
        ["scripts/core/game_events.gd:52", "scripts/core/game_events.gd:53", "scripts/core/game_events.gd:69"], "reading", "high",
        "const Dictionaries for the two sets; iterate the subscriber array by index with a delivering flag instead of duplicating", "S4", severity="low")
finding("BUG-04", "bug", "TopdownFx's effect cap only retires one-shot effects: with MAX_NODES looping effects alive the list grows past the cap; advance() copies the list every frame and erases by value (O(n^2))",
        ["scripts/topdown/topdown_fx.gd:92-97", "scripts/topdown/topdown_fx.gd:101-111"], "reading", "high",
        "swap-remove by index in one pass; retire the oldest loop when no one-shot is left", "S4", severity="low")
finding("BUG-05", "architecture", "56 calls into another object's private methods, 7 of them writes across authorities (Field -> Combat._apply_status_to_enemy x4, Enemy -> World._drop_loot, Quest -> World._start_event, Account -> Quest._refresh_offers)",
        ["scripts/simulation/authority/field_authority.gd:218-226", "scripts/simulation/authority/enemy_authority.gd:616",
         "scripts/simulation/authority/quest_authority.gd:1093", "scripts/simulation/authority/account_authority.gd:319",
         "scripts/presentation/object_view.gd:194 Game.world._verb", "scripts/hud.gd:2189 Game.pets._pet", "scripts/ui/pages/your_sect_page.gd:282 Game.sect._on_expedition",
         "scripts/ui/pages/works_page.gd:220 Game.posts._curve_of", "scripts/ui/pages/auction_page.gd:98 Game.economy._au_cfg"],
        "tools/dev/audit/smells.py private_call", "high",
        "public apply_*/query names for each; a contract_tests rule that fails on `\\.(_[a-z]\\w*)\\(` against another object in scripts/", "S11", severity="medium")
finding("BUG-06", "fragile", "Method names read from data and called unchecked: Game.get(row[0]).call(row[1], c)",
        ["scripts/hud.gd:521", "scripts/core/tutorial_rules.gd:102"], "tools/dev/audit/smells.py data_method_call", "high",
        "a data_validation rule: every count pair names an authority and a method it has (has_method)", "S2", severity="low")
finding("BUG-07", "debug_in_release", "main.gd carries 510 lines of preview/debug flags (_handle_preview_args), several calling private authority methods (Game.combat._defeat, Game.progression._advance, _start_tribulation, Game.calendar._phenomenon, Game.combat._cast_illusion)",
        ["scripts/main.gd:180-690"], "tools/dev/audit/funcs.py; smells.py private_call", "high",
        "scripts/shell/debug_args.gd (one function per flag, a table flag -> handler), loaded only when OS.has_feature('debug') or preview_mode", "S7", severity="low")
finding("BUG-08", "perf", "hud.gd builds a per-frame cache key with points_override.duplicate() every frame",
        ["scripts/hud.gd:542"], "tools/dev/audit/hot_paths.py and reading", "high", "FrameMemo (DUP-01)", "S4", severity="low")
finding("BUG-09", "fragile", "assert() in game code vanishes in release exports: avatar's missing-pose check, zone_geometry's duplicate surface id, map_generator's unknown theme",
        ["scripts/avatar.gd:65", "scripts/simulation/zone_geometry.gd:31", "scripts/simulation/zone_geometry.gd:40", "scripts/simulation/map_generator.gd:16"],
        "tools/dev/audit/smells.py assert_game", "high", "push_error + a safe fallback (these are side-view files: fold into S12's freeze)", "S12", severity="low")
finding("BUG-10", "flaky_gate", "perf_tests fails under CPU load (1 of 18 in the baseline, 5 of 18 in a rerun at load 7.7): ms budgets measured on a shared machine",
        ["tests/perf_tests.gd"], "two runs", "high",
        "take the least of N rounds for every budget (the living-world check already does), and print but do not fail when Engine reports the process was starved", "S2", severity="medium")
finding("BUG-11", "boot_cost", "ContentDB reads and expands every data/*.json at boot, including techniques.json (974 KB, 3,171 rows, 133 ms here) and icon_manifest (2,570 keys); perf_tests' own v1.5 budget fails at 191 ms",
        ["scripts/core/content_db.gd:31-92"], "perf_tests output; reading", "high",
        "lazy tables: parse a table on its first entry()/all()/config(); keep the realm and recipe indexes eager", "S4", severity="medium")
finding("BUG-12", "fragile", "TopdownRoom.from_dict reads the level under a prop's footprint without a bounds check: a prop pushed past the edge by a hand override crashes the room load (the Python check guards today's layouts)",
        ["scripts/topdown/topdown_room.gd:87", "tools/data/topdown_rooms.py:192 (same read in the Python Grid)"], "reading", "medium",
        "clamp and push_error; the room engine validates footprints before writing", "E1", severity="low")
finding("BUG-13", "smell", "Authorities are one dense mutual graph: 575 game.<authority>.<method> calls, 36 mutually dependent pairs (crafting<->inventory 54/2, world<->combat 23/5, combat<->progression 12/15, world<->quest 21/6)",
        ["scripts/simulation/authority/*"], "regex game.<authority>.<method> per file (gd_graph.json cross_authority)", "high",
        "no rewrite: publish each authority's public surface (the apply_* writers and the queries) as its doc header, enforce it with the private-call rule (BUG-05), and let new systems talk through events", "S11", severity="low")
finding("BUG-14", "god_object", "God objects: hud.gd (3,266 lines, 168 funcs: layout, input, 234 event cases, 40 draw panels, tours), combat_authority.gd (2,819, 169 funcs, 18 sections), world_authority.gd (2,296, 16 sections), crafting_authority.gd (2,055, 20 sections), progression_authority.gd (1,810), main.gd (1,058, 510 of them debug flags)",
        ["scripts/hud.gd", "scripts/simulation/authority/combat_authority.gd", "scripts/simulation/authority/world_authority.gd",
         "scripts/simulation/authority/crafting_authority.gd", "scripts/simulation/authority/progression_authority.gd", "scripts/main.gd"],
        "tools/dev/audit/inventory.py and funcs.py; section headers", "high",
        "split by section into parts the authority owns (scripts/simulation/authority/combat/flight.gd ...), the facade and state unchanged", "S6-S10", severity="medium")

# ---------------------------------------------------------------------------------------------------------------------
ENGINES = [
    {"id": "E1", "name": "Room engine", "home": "tools/content/rooms/ (engine.py, biomes.py, specs/<zone>.py)",
     "builds_on": ["tools/data/topdown_rooms.py Layout DSL and Grid checks", "tools/data/world.py field()/town() side-view templates (ids of NPCs, objects, portals, spawns)",
                   "tools/data/topdown_life.py dress()/extend() (furnishings, vistas, work spots)", "tools/data/places.py", "tools/data/room_lint.py"],
     "spec_example": {
         "room": "wp_east", "size": [64, 26], "biome": "valley_meadow", "seed": "wp_east",
         "bands": [["rock", 0, 2, {"level": 2}], ["terrace", 2, 5, {"level": 1, "paint": "f"}], ["road", 12, 3, {"paint": "d"}],
                   ["stream", 21, 5, {"water": True}]],
         "features": [["knoll", [27, 8, 8, 3], {"level": 1, "stair": "s"}]],
         "stairs": "auto", "exits": {"east": ["e", 13, 3], "west": ["w", 13, 3]}, "spawn_at": "east",
         "anchors": {"npc_old_pan_wp": "knoll.top", "pan_spot": "road@34", "sign_wp": "road.north@60", "note_lu": "road.north@57",
                     "herb_1": "verge.south@33", "jar_2": "terrace@48", "jar_4": "bank@52", "crate_3": "bank@33"},
         "flora": {"road": ["tree_plum", "tree_peach", "fence_4", "bush"], "terrace": ["tree_camphor", "bush_azalea"],
                   "stream": ["tree_willow", "tall_grass", "cattails", "lotus_pads"], "density": 0.3},
         "props": {"willow": {"along": "terrace", "every": 11}, "reeds": {"along": "stream.edge", "every": 10}, "incense": [50, 10]},
         "ground": {"sand": "stream.coves"}, "foes": {"verge": 5}, "pins": {}},
     "migration": "1) The engine emits Layout calls, so a spec can reproduce an existing room exactly with `pins` (cells, props, places); migrate the 27 layouts one by one until `topdown_rooms --check` shows no diff. 2) Convert the 141 side-view rooms from their world.py template (which already lists the ids) plus a 10-20 line shape spec. 3) Hand-tweaks stay as pins in the spec, never edits to the JSON.",
     "saves": "wp_east is 44 hand lines (~600 tokens) and about 60 placed coordinates; its spec is ~15 lines (~220 tokens) with 8 anchors. Across the 141 rooms left: ~8,500-15,500 hand lines at today's rate against ~2,100-2,800 spec lines.",
     "tests": ["determinism: build twice, byte-identical", "topdown_rooms --check, places --check, room_lint, sect_walks --check", "round-trip: every migrated room's JSON unchanged",
               "tests/topdown_tutorial.gd reach checks in the game", "a golden picture per biome in the capture registry"]},
    {"id": "E2", "name": "Monster engine", "home": "tools/content/monsters.py (+ tools/art/topdown/creature/plans/)",
     "builds_on": ["tools/data/enemies.py mob()/atk()", "tools/art/topdown/creatures.py Spec and SIZE", "tools/art/topdown/creature/sculpt.py (E/S/L parts, Pose, Look)",
                   "creature/motion.py (gait, pick, wave, headon)", "tools/data/sound.py FOE rules by race", "tools/icons/families/beast_parts.py (drops)"],
     "spec_example": {
         "id": "reedtail_rat", "plan": "quadruped.rodent", "size": 1.0, "length_px": 38,
         "palette": ["fur", "fur_light", "pink", "tail_a", "tail_b"], "eyes": "rat_eye",
         "parts": {"ears": "round", "tail": {"kind": "segmented", "n": 14, "mats": ["tail_a", "tail_b"]}, "whiskers": 3, "teeth": "yellow"},
         "motion": {"idle": "sniff", "walk": "bound", "tell": "rear", "attack": "lunge_bite", "hurt": "knock_squash", "death": "topple_side"},
         "data": {"level": 2, "role": "normal", "element": "none", "race": "beast", "codex": "valley_shore",
                  "attacks": [["bite", 0.35, 36]], "ai": "melee", "loot": [["rat_tail", 0.6]]},
         "sound": "race"},
     "migration": "Extract five body plans from the twelve drawn species (quadruped: rat, otter, boarlets; amphibian: frog, toad; crab; serpent/fish: eel, minnow, leech; shell: snapper; humanoid: puppet). A spec may name `pose: creature.rat:rat` as an escape hatch, so the existing modules keep working while their plans are extracted; each migrated species is checked against its old sheet (pixel diff under a threshold, then the gallery review AGENTS.md rule 3 asks for).",
     "saves": "a top-down species today: 95-304 lines of pose code (rat 129 lines, ~1,900 tokens) plus rows in three files; a spec is ~20 lines (~300 tokens). 110 of the 122 species still lack top-down art: ~22,000 hand lines against ~2,500.",
     "tests": ["build_foes determinism", "every action's frame count and HIT_FRAME per plan", "data_validation (enemies, loot, codex)", "sound.py --check (every foe has a voice)",
               "the foe gallery (topdown_figure_gallery) reviewed by eye"]},
    {"id": "E3", "name": "NPC engine", "home": "tools/content/npcs.py",
     "builds_on": ["tools/data/story.py npcs() and outfit()", "tools/data/topdown_life.py LOOPS, work, extras", "the room engine's anchors", "tools/data/economy.py shops",
                   "tools/art/topdown/figure (every look is already data: sets/*.py)"],
     "spec_example": {"id": "washer_mei", "name": "Washer Mei", "title": "Villager",
                      "look": {"body": "light", "hair": "ponytail", "hair_color": 2, "shirt": "cardigan:white", "pants": "straight", "shoes": "slippers"},
                      "home": ["lf_village", "river_bank@14"], "work": {"loop": "laundry", "spots": "auto:water_edge,line", "leash": 2.5},
                      "lines": ["Aunt Ping says you're finally awake before noon.", "The river's cold as winter this morning."],
                      "barks": ["Scrub, scrub."], "gives": ["the_muddy_wash"], "shop": None, "schedule": {"night": "lf_village_night:npc_granny_night"}},
     "migration": "Generate npcs.json rows, life.json work entries and the layouts' places from specs; start with the villagers of Lotus Ferry (the work loops exist), compare the three outputs byte for byte, then the sect disciples (templates: steward, deacon, disciple_a/b).",
     "saves": "an NPC today: a dict in story.py (~8 lines), a work entry in topdown_life.py (1-3 lines with hand-placed spots), an r.at() in the layout, dialogue/quest hooks by hand; one ~10-line spec, spots found by the room engine.",
     "tests": ["topdown_life --check (spots stand, walk legs clear)", "data_validation (npcs, services, shops)", "story.validate", "tutorial_order and topdown_tutorial (who stands where)"]},
    {"id": "E4", "name": "Item engine", "home": "tools/content/items.py (+ tools/icons family specs)",
     "builds_on": ["tools/data/items.py item(), MID_ILV, GRADE_WORD, ATTRIBUTE_REQ, ARMOUR, pills()", "tools/data/gear.py ARCHETYPES", "tools/icons/families/pills.py PILL_GRADES (vessel x grade already)",
                   "tools/dev/wiki.py source scan and data_validation item_source_suite", "data/curves.json"],
     "spec_example": {"family": "pill.qi_gathering", "kind": "pill", "vessel": "jar", "tiers": ["common", "earth", "heaven", "mystic"],
                      "names": "{tier_word} Qi Gathering Pill", "effect": {"kind": "add_progress", "amount": "curve:pill_qp[tier]"},
                      "price": "curve:pill_price[tier]", "sources": {"shop": {"granny_liu": ["common"]}, "recipe": "alchemy", "loot": "chests>=tier"},
                      "sinks": ["use", "sell", "gift"]},
     "migration": "Re-express one family at a time (pills, herbs by age, ores, beast parts, gear by family x grade) as specs that emit the same rows; `build_data.py --check` style diff proves it. New tiers then cost one line.",
     "saves": "an item today: a row in items.py, a price in economy.py, a recipe in crafts.py, a loot line in enemies.py and an icon function; a family spec covers the tiers at once (~10 lines for 4-9 items).",
     "tests": ["wiki.py --gaps shows no new gap", "data_validation item_source_suite", "balance_sim (prices, Qi per hour)", "icon build determinism"]},
    {"id": "E5", "name": "Quest engine", "home": "tools/content/quests.py",
     "builds_on": ["tools/data/story.py quest(), o(), item(), taels(), fx()", "unlocks.json guided quests", "mission_templates.json (daily missions are already templated)"],
     "spec_example": {"id": "the_muddy_wash", "template": "clear", "giver": "washer_mei", "target": {"enemy": "reedtail_rat", "count": 6},
                      "band": "village", "reward": "band", "lines": {"offer": "The rats are at the washing lines again.", "done": "Clean sheets at last!"}},
     "migration": "Templates for talk, fetch, kill/clear, deliver, gather, spar and escort; rewards from a band table (fixed amounts, phase 1's progression decision). Keep story beats hand-written (prologue, main quests), template the side and daily quests first.",
     "saves": "a side quest today: 4-8 lines with its dialogue elsewhere; a template row is 3-5 lines and its tracker text and hand-in lines are generated.",
     "tests": ["story.validate", "tutorial_order", "valley_run and prologue_run (no change to the story's quests)", "balance_sim (reward per hour)"]},
    {"id": "E6", "name": "Cue and notice engine (FX, sound, toasts)", "home": "data/cues.json, data/hud_notices.json (from tools/data/cues.py)",
     "builds_on": ["WorldShared.play", "hud._handle", "tools/data/sound.py (hits, steps, foes, life are already tables)", "data/combat_feel.json", "data/moments.json (the big set pieces are already data)"],
     "spec_example": {"event": "item_blooded", "when": {"actor": "active"}, "log": {"key": "hud.item_blooded", "args": ["item_name:item"], "colour": "MIST"}},
     "migration": "Move the one-line cases first (about 180 of hud._handle's 234, most of WorldShared.play's), keep the code cases as named handlers the table can call.",
     "saves": "about 700 lines of GDScript match arms become ~250 table rows; a new event's toast is one row, no code.",
     "tests": ["contract_tests (every event in the table is in the event contract)", "tutorials and hud suites unchanged", "a notices snapshot test: each row rendered once"]},
    {"id": "E7", "name": "Technique engine (exists)", "home": "tools/data/technique_gen.py, technique_grammar.py",
     "builds_on": ["3,171 technique rows already generated from forms x rings x elements x families (P13a compact rows with defaults)"],
     "spec_example": {"note": "already an engine: extend it rather than write a new one; its row compaction is the model for the others"},
     "migration": "none", "saves": "done", "tests": ["perf_tests techniques.json budget", "rules_tests technique checks"]},
]

SLICES = [
    {"id": "S1", "wave": 1, "title": "Delete dead code and fix the save-id crash", "owns": ["the files in DEAD-01/02/05/06/07", "crafts_page.gd lookups and a save-load sweep for unknown recipe ids (BUG-01)"],
     "size": "~300 lines removed, ~40 changed", "risk": "low", "tests": ["run_tests.sh", "contract_tests strings gate"],
     "after_phase1": ["hud.gd", "tutorial_coach.gd"], "notes": "hud.gd and tutorial_coach.gd edits wait for the tutorial and quick-slot jobs"},
    {"id": "S2", "wave": 1, "title": "Tests hygiene: a suite base, the side-view suite, a steadier perf gate, data-method rule",
     "owns": ["tests/lib/suite.gd (new)", "tests/*.gd headers", "tests/side_view_suite.tscn (new)", "tools/run_tests.sh", "Test.ps1"],
     "size": "~150 lines new, ~200 removed, header edits in 17 suites", "risk": "low", "tests": ["every suite's check count unchanged"],
     "after_phase1": ["tests/rules_tests.gd", "tests/tutorials.gd", "tests/hollow_night.gd", "tests/balance_sim.gd", "tests/topdown_tutorial.gd"],
     "notes": "the phase-1 jobs add checks to these suites: rebase onto them"},
    {"id": "S3", "wave": 1, "title": "Tools housekeeping: capture registry, side-view pipeline moved under tools/art/sideview, study copies archived",
     "owns": ["tools/dev/*capture*", "tools/dev/prototype_qa.gd", "tools/art/creatures", "tools/art/pixel.py", "tools/art/helpers_batch_*", "tools/art/bake_*", "tools/backdrops", "tools/art/topdown/study_quality", "scripts/combo_rig.gd", "scripts/equipment_rig.gd"],
     "size": "moves ~32,000 lines, rewrites ~2,000 (captures)", "risk": "low (no game code)", "tests": ["each moved generator still builds byte-identical output (run once before and after)"],
     "after_phase1": ["tools/dev/topdown_capture.gd (the boss job adds shots)"], "notes": ""},
    {"id": "S4", "wave": 1, "title": "Shared runtime utilities: FrameMemo, Noise, Figures factory, lazy ContentDB tables, GameEvents sets, TopdownFx cap",
     "owns": ["scripts/core/frame_memo.gd (new)", "scripts/core/noise.gd (new)", "scripts/presentation/figures.gd (new)", "scripts/core/content_db.gd", "scripts/core/game_events.gd", "scripts/topdown/topdown_fx.gd", "the 12 pages of DUP-03 (one line each)"],
     "size": "~250 new, ~350 removed", "risk": "medium (content_db laziness touches boot)", "tests": ["run_tests.sh", "perf_tests (boot and room load)", "engine_tests"],
     "after_phase1": ["scripts/ui/pages/inventory_page.gd (the bag job)"], "notes": ""},
    {"id": "S5", "wave": 1, "title": "Generator hygiene: common CLI, one pixel lib for new work, Grid thresholds from movement.json, dead data and fields",
     "owns": ["tools/data/common.py", "tools/data/topdown_rooms.py (Grid only)", "tools/data/{stats,moments,techniques,economy,enemies,items}.py (dropped fields)", "tools/lib/pix.py (new)"],
     "size": "~400 changed", "risk": "low", "tests": ["build_data.py then git diff: only the dropped fields change", "every --check gate"],
     "after_phase1": ["tools/data/stats.py", "tools/data/items.py", "tools/data/story.py", "tools/data/enemies.py"], "notes": "the progression job rewrites numbers in these"},
    {"id": "S6", "wave": 2, "title": "hud.gd split and the notice table (E6's HUD half)",
     "owns": ["scripts/hud.gd", "scripts/hud/*.gd (new: hud_input, hud_layout, hud_notices, hud_panels, hud_tours)", "data/hud_notices.json", "tools/data/cues.py"],
     "size": "3,266 lines moved into 5-6 files; ~450 lines of match arms become ~180 rows", "risk": "medium", "tests": ["tutorials", "topdown_tutorial", "rules_tests HUD checks", "hud_capture before/after"],
     "after_phase1": ["hud.gd (tutorial coach, quick slots, first boss HP bar)"], "notes": "one owner for hud.gd for the whole slice"},
    {"id": "S7", "wave": 2, "title": "main.gd: debug flags to scripts/shell/debug_args.gd, the page table to data",
     "owns": ["scripts/main.gd", "scripts/shell/debug_args.gd (new)"], "size": "~550 moved", "risk": "low", "tests": ["tools/dev captures that use flags", "tutorials", "perf_tests"],
     "after_phase1": [], "notes": ""},
    {"id": "S8", "wave": 2, "title": "combat_authority.gd into parts (flight, arts, phantom, flying sword, melody, blood, arrays, swarm, talismans, projectiles, treasures)",
     "owns": ["scripts/simulation/authority/combat_authority.gd", "scripts/simulation/authority/combat/*.gd (new)"], "size": "2,819 lines moved", "risk": "medium",
     "tests": ["rules_tests", "balance_sim", "hollow_night", "valley_run"], "after_phase1": ["combat_authority.gd (charged attack, boss phase)"], "notes": ""},
    {"id": "S9", "wave": 2, "title": "world_authority.gd into parts (ambush, herbs, arrays, objects, loot, hazards, voyages, events, nests, tower, idle)",
     "owns": ["scripts/simulation/authority/world_authority.gd", "scripts/simulation/authority/world/*.gd (new)"], "size": "2,296 moved", "risk": "medium",
     "tests": ["room_sweep", "tutorial_order", "valley_run", "places_tests"], "after_phase1": [], "notes": ""},
    {"id": "S10", "wave": 2, "title": "crafting_authority.gd and progression_authority.gd into parts",
     "owns": ["scripts/simulation/authority/crafting_authority.gd", "scripts/simulation/authority/progression_authority.gd", "their part folders"], "size": "3,865 moved", "risk": "medium",
     "tests": ["rules_tests", "balance_sim", "valley_run"], "after_phase1": ["progression_authority.gd (meditation, fixed XP)"], "notes": ""},
    {"id": "S11", "wave": 2, "title": "Public surfaces: private cross-calls to public API, BrainKit, the contract rule",
     "owns": ["the 56 call sites of BUG-05", "scripts/simulation/ai/*", "tests/contract_tests.gd (new rule)"], "size": "~200 changed", "risk": "low-medium",
     "tests": ["contract_tests", "rules_tests", "hollow_night"], "after_phase1": ["enemy_brain/topdown_brain (boss phase 2)"],
     "notes": "runs after S8-S10 so the renamed methods live in their final files"},
    {"id": "S12", "wave": 3, "title": "Side view frozen behind RoomSpace; its files under scripts/sideview/",
     "owns": ["scripts/world.gd", "scripts/player.gd", "scripts/backdrop.gd", "the DEAD-15 list", "the topdown==null checks in world_authority/enemy_authority/ally_brain"],
     "size": "~400 changed, 2,233 moved", "risk": "medium-high", "tests": ["side_view_suite (S2)", "engine_tests", "visibility_suite", "room_sweep", "valley_run"],
     "after_phase1": [], "notes": "optional; only if the fallback setting stays. If the product retires it, delete instead"},
    {"id": "E1", "wave": 3, "title": "Room engine, then migrate the 27 layouts (round-trip), then new rooms", "owns": ["tools/content/rooms/ (new)", "tools/data/topdown_rooms.py"],
     "size": "~900 new; the 1,778-line layouts file becomes specs", "risk": "medium", "tests": ["topdown_rooms/places/room_lint/sect_walks --check", "topdown_tutorial"], "after_phase1": [], "notes": ""},
    {"id": "E2", "wave": 3, "title": "Monster engine: plans from the 12 species, data+art+sound from one spec", "owns": ["tools/content/monsters.py (new)", "tools/art/topdown/creature/plans/ (new)", "tools/art/topdown/creatures.py", "tools/data/enemies.py"],
     "size": "~1,200 new", "risk": "medium (visual)", "tests": ["build_foes determinism", "data_validation", "gallery review"], "after_phase1": ["hollowed_eel (the boss job)"], "notes": ""},
    {"id": "E3", "wave": 3, "title": "NPC engine", "owns": ["tools/content/npcs.py (new)", "tools/data/story.py npcs()", "tools/data/topdown_life.py work/extras"],
     "size": "~500 new", "risk": "low-medium", "tests": ["topdown_life --check", "data_validation", "tutorial_order"], "after_phase1": ["story.py (elders' scene)"], "notes": "after E1 (anchors)"},
    {"id": "E4", "wave": 3, "title": "Item engine", "owns": ["tools/content/items.py (new)", "tools/data/items.py", "tools/data/gear.py"], "size": "~600 new", "risk": "medium (balance)",
     "tests": ["wiki --gaps", "data_validation", "balance_sim"], "after_phase1": ["items.py (fixed-XP pills)"], "notes": ""},
    {"id": "E5", "wave": 3, "title": "Quest engine (side and daily quests)", "owns": ["tools/content/quests.py (new)", "tools/data/story.py side_quests()"], "size": "~400 new", "risk": "low-medium",
     "tests": ["story.validate", "valley_run", "balance_sim"], "after_phase1": ["story.py"], "notes": "after E3"},
    {"id": "E6", "wave": 2, "title": "Cue table for WorldShared.play (the HUD half is S6)", "owns": ["scripts/presentation/world_shared.gd", "data/cues.json", "tools/data/cues.py"], "size": "~250", "risk": "low",
     "tests": ["audio_tests", "rules_tests FX checks", "topdown_capture before/after"], "after_phase1": [], "notes": ""},
]


def run_scans(tmp):
    out = {}
    scans = {"inventory": ["inventory.py"], "gd_graph": ["gd_graph.py", "--quiet"], "py_graph": ["py_graph.py", "--quiet"],
             "assets": ["asset_refs.py", "--quiet"], "manifests": ["manifest_refs.py"], "data": ["data_refs.py", "--quiet"],
             "strings": ["strings_refs.py"], "dupes_gd": ["dupes.py", "--ext", ".gd", "--window", "6", "--quiet"],
             "dupes_py": ["dupes.py", "--ext", ".py", "--window", "8", "--quiet"], "hot_paths": ["hot_paths.py"], "smells": ["smells.py"]}
    for name, cmd in scans.items():
        path = os.path.join(tmp, name + ".json")
        subprocess.run([sys.executable, os.path.join(HERE, cmd[0])] + cmd[1:] + ["--json", path], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
        try:
            out[name] = json.load(open(path))
        except Exception as e:
            out[name] = {"error": str(e)}
    return out


def trim(scans):
    """Keep the summaries and the lists a phase-2 slice needs; drop the bulky per-file tables."""
    g = scans.get("gd_graph", {})
    return {
        "inventory": {k: scans.get("inventory", {}).get(k) for k in ("areas", "largest", "totals", "assets")},
        "gd_graph": {"summary": g.get("summary"), "unreached_scripts": g.get("unreached_scripts"),
                     "game_scripts_not_reached_from_game": g.get("game_scripts_not_reached_from_game"),
                     "nonsuite_tests": g.get("nonsuite_tests"), "orphan_uids": g.get("orphan_uids"),
                     "symbols": g.get("symbols"), "signals": g.get("signals"), "cross_authority": g.get("cross_authority"),
                     "dynamic_prefixes": g.get("dynamic_prefixes")},
        "py_graph": {k: scans.get("py_graph", {}).get(k) for k in ("summary", "orphans", "cli_named_nowhere", "unreferenced_defs")},
        "assets": {k: scans.get("assets", {}).get(k) for k in ("summary", "unnamed")},
        "manifests": scans.get("manifests"),
        "data": {"summary": scans.get("data", {}).get("summary"),
                 "tables": [t for t in scans.get("data", {}).get("tables", []) if t.get("game_refs", 1) == 0 or t.get("unread_keys")]},
        "strings": scans.get("strings"),
        "dupes_gd": {k: scans.get("dupes_gd", {}).get(k) for k in ("summary", "by_pair")},
        "dupes_py": {k: scans.get("dupes_py", {}).get(k) for k in ("summary", "by_pair")},
        "hot_paths": (scans.get("hot_paths") or [])[:40] if isinstance(scans.get("hot_paths"), list) else scans.get("hot_paths"),
        "smells": scans.get("smells"),
    }


def main():
    out_path = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "docs", "architecture", "audit_45.json")
    doc = {"schema_version": 1, "decision": 45, "baseline": BASELINE, "legacy_tests": LEGACY_RUN, "findings": F, "engines": ENGINES, "slices": SLICES,
           "tools": "tools/dev/audit/*.py (read-only; rerun with python3 tools/dev/audit/findings.py)"}
    if "--no-scan" not in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            doc["scans"] = trim(run_scans(tmp))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote", os.path.relpath(out_path, ROOT), len(F), "findings,", len(ENGINES), "engines,", len(SLICES), "slices")


if __name__ == "__main__":
    main()
