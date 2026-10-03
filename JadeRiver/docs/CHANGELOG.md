# Changelog

## The shell: the debug flags in a script of their own, and the page registry (decision 45, S7)

This is phase 2, slice S7 of the code audit (`docs/architecture/audit_45.md` §2.2 and §7, BUG-07). `scripts/main.gd`
had 1,061 lines and now has 522. The game plays the same, and every flag a tool, a test or a document uses works
with the same spelling. `docs/architecture/shell.md` describes the shell.

- **The debug flags moved to `scripts/dev/debug_args.gd`.**
  - `_handle_preview_args` was one 510-line chain of `if`s. The flags are now tables of rows, `[flag, handler, needs]`,
    read in the same steps and order as before. Each handler is a small function: before the boot, the screen, the
    preview character, the state the picture shows, and with `--capture` the picture.
  - `main.gd` loads the script only when the game starts with arguments after `--`. That is the guard the flags always
    had, and a player's game, which has none, now never even loads the script.
  - The script is not in `scripts/shell/`, because `contract_tests` holds the shell to never writing game state, and
    the flags write it on purpose.
  - Six flags that nothing in `tools/`, `tests/`, `docs/` or the capture registry used are gone: `--body=`, `--learn=`,
    `--physique=`, `--set-piece=`, `--tribulation` and `--test-saves`. The last did nothing of its own, since any
    argument already chose the preview saves.
- **The page table moved to a registry, `scripts/shell/page_registry.gd`.**
  - It maps each page id to its script, with `script_of(id)` and `scripts()`. `main.gd` keeps `PAGES` as a name for
    it, for the tests and tools that read it there.
  - `tools/data/tutorials.py` reads the registry for the tutorials' page map, and `tutorials.json` is unchanged.
  - The five ids that are no page (`_harvest`, `_exit`, `_tour`, `_import` and `_switch`) are one `match` in
    `_shell_action`. Opening, closing and Back behave as before.
- **The side view in `main.gd`** is one section, "side view (retiring)". It holds the side view's world, the backdrop
  following it, and the swap when a room of the other kind is entered. The `World` preload and the four side-view
  lines elsewhere (in `_add_world_view`, `_unmount_world` and `_on_game_event`) are marked `# side view`.
- **Dead in `main.gd`:** `boot_report` was a member that only `_ready` read, and it is now a local.
## Tools: one capture registry, and the stale study and generators gone (decision 45, S3)

The code audit's slice S3 (`docs/architecture/audit_45.md` §3.3, §3.4 and §7). No game code changed.

- **One capture tool.** `tools/dev/capture/capture.tscn -- <set>` now takes every review picture the game draws of
  itself. It replaces `topdown_capture.gd` with its 22 modes, plus `hud_capture`, `picture_capture`, `sect_capture`,
  `places_capture`, `tutorial_capture` and `progression_capture` (3,560 lines, now 2,802).
  - The pictures are data. `shots.gd` holds 32 sets and 375 rows. A row gives the picture's name, its room, cell and
    wait, the clock's hour, the foes and their fight, the steps before it, how it is taken and what follows.
  - A new picture is a row, not a function. `tools/dev/README.md` says how to add one.
  - `capture_steps.gd` holds the shared steps that rows use: stand, act, set the character, pin the clock, open a page,
    wait on a scene. It also holds the takes: the window, the world alone x2, a detail, a close-up, a whole room, a
    strip, a sheet, panels, and before-and-after pairs.
  - `capture_scripted.gd` holds the old scripts' loops that wait on the game, ported call for call: the eel's fight, a
    worker's pose, a frozen staged scene, the foes' lineups and the tutorials' tours.
  - `--out-root=<dir>` writes a set outside `docs/`, and `--only=<text>` takes some of its pictures. `--list` names
    the sets, and `--lint` checks every row's steps and argument counts without playing.
  - Every set plays on saves of its own (`user://capture_<set>/`), never a player's or the Max Tester's. The review
    room loads from `tests/data/topdown/`, where S5 moved it.
- **The same pictures, the same framing.** Every set was run with the old script and with the registry under a harness
  that pins the clock and the random seed, at `--fixed-fps 60`. Most ran the old script twice, to see where it differs
  from itself. The two phone-size sets ran at 2400x1080 too.
  - All 531 pictures came out with the same names and sizes. 245 are byte-identical to an old run, among them:
    - every weapon family's combo sheet, both weaves, phase 2's strips and aimed shots;
    - the monsters' and the polish's lineups at x4 (the foes' spots and poses);
    - every page (Techniques, the trees, the shop, the Bag, the Character, the Cultivation page, the travel picker);
    - the places' close-ups and minimap, the Techniques page's tour, nine of the thirteen workers shown;
    - all 49 before-and-after pairs (terrain, foliage, sand and snow), and `boxes.json`.
  - The first boss's log of beats is identical: every scene's start and end, the waking and the overwhelm, at the same
    sim seconds.
  - The rest differ only where the game draws by the wall clock, which is also where two runs of the old script differ
    from each other: the water's frames, grass and trees swaying, a lamp's flicker, and a sheet loaded a frame sooner
    on its thread.
- **Removed (2,542 lines):**
  - the decision-42 study `tools/art/topdown/study_quality/`, superseded since the B renderer shipped (its pictures
    stay in `docs/redesign/feedback/character_quality/`, and git history keeps its code);
  - `tools/icons/study/technique_cards.py`, which nothing ran;
  - the `build_topdown_proto.py` shim;
  - `tools/dev/fix_infer.py`;
  - five helpers no builder calls (`terrain2.pnxy` and `_q`, `sand_snow._slope`, `elements.base_hex`,
    `topdown_forms._dome`).
- **Kept on purpose:**
  - The side view is retiring, and its pipeline will be deleted with it in a later slice, so it is not moved. That is
    `build_creatures.py`, `bake_act2_hats.py`, `bake_straw_hat.py`, `tools/bake_hat_cape_combos.gd`, `combo_rig.gd`
    and `equipment_rig.gd`.
  - `stat_probe.gd` and `combat_trace.gd` are numeric probes that docs cite, not screenshot captures.
  - `prototype_qa.gd` is the QA walk that `tutorial_play.gd` builds on.
- **One sheet packer** (audit DUP-12). `tools/art/topdown/sheet.py` has `pack()` (shelf rows), `png_bytes()` and the
  builders' `run()` (build, `--check`, write, `--review`).
  - `build_decor.py` and `build_life.py` use all three, and `build_tiles.py` and `build_foes.py` use `png_bytes()`.
  - `build_tiles.py`'s two review sheets share one layout.
  - Every output is byte-identical. All 31 files the four builders write have the same sha1 before and after, and
    each builder's `--check` passes. So do `build_fx_topdown.py --check` and `build_fx.py --verify`, and the review
    sheets are byte-identical too.
- **Found, not fixed:** `build_tiles.py --review` stops with a KeyError on the `sand` decals, in the Terrain v2
  sheet's ground table. This predates the slice. `--review-sand-snow` runs.

## Crafting and Progression in parts (decision 45, S10)

This is phase 2, wave 2, slice S10 of the code audit (`docs/architecture/audit_45.md` §2.2 and §7). The two
authorities are now split into parts, one for each section of their work:
- `crafting_authority.gd`, which had 2,055 lines;
- `progression_authority.gd`, which had 1,858 lines.

The code moved as it was. The game plays the same, every caller still calls `Game.crafting.<method>` and
`Game.progression.<method>`, and the save data is untouched.

- **How the parts work.**
  - Each authority keeps its state, its intents (`intents` and `handle`), its subscriptions and its tick. Its public
    methods are one-line forwarders to the part that does the work.
  - A part is a `RefCounted` that its authority makes. It has no state of its own. It holds a weak reference back to
    the authority: `Game` builds new authorities on every boot, and a strong reference would keep the old ones alive.
    The bases are `CraftingPart` and `ProgressionPart`.
  - A part reaches the authority's state and public methods through the authority, as any caller would
    (`crafting.pending`, `progression.apply_insight`). It calls a helper that another part keeps to itself on that part
    (`progression.realms.fail_breakthrough`).
  - Some private helpers are called by name from tests and tools, such as `_consume`, `_start_tribulation` and
    `_levels_gained`. They keep their forwarders on the authority until S11 gives them public names. Inside their part
    they are already public.
- **Crafting** (`scripts/simulation/authority/crafting/`, 271 lines left in the authority) has nine parts:
  - professions;
  - gathering;
  - the garden;
  - recipes and the craft;
  - the five-screen refine;
  - furnaces, with the fire and the pill tribulation;
  - the forge's gear upkeep;
  - ancient recipes and experiments;
  - the guilds.
- **Progression** (`scripts/simulation/authority/progression/`, 274 lines left in the authority) has eleven parts:
  - meditation, with seclusion and the offline claim;
  - realms and breakthroughs;
  - the heavenly tribulation;
  - fates;
  - insight and the Daos;
  - attunement;
  - the body;
  - the cultivator's condition;
  - vows and paths;
  - methods and techniques;
  - the element trees, with the Lost Arts.

  The authority's tick still runs the cultivator's clock, in the same order. Phase 1's rules for meditation, fixed
  experience and cultivation speed moved unchanged.
- **Dead code dropped.**
  - An unused local in `claim_offline`.
  - The public copy of `_spend_fate_next`. `spend_fate_next` is now the function itself, and both names still work.
- **The checks that name scripts now see the parts.** Both changes cover any `authority/<name>/` folder, so the other
  splits need no edits of their own.
  - `tools/data/contract.py` adds every script in an authority's folder to that authority's system, so the event
    contract accepts an event that a part emits.
  - It also stops the build if two scripts share a file name, because `contract_tests` finds scripts by name. The parts
    are named after their authority, such as `crafting_garden.gd` and `progression_realms.gd`.
  - In `data/event_contract.json`, only the `files` lists of the Crafting and Progression events changed.
  - `data_validation` also looks in the part folders for the authority that reports a `use_system` objective.
- **Checks.**
  - Every suite has the same check count as the base, with no failures and no script errors.
  - `balance_sim` prints the same figures, line for line.
  - The data build is unchanged apart from the contract's `files` lists.
  - `perf_tests` misses its millisecond budgets on the base and on S10 alike, at a load of about 14 on 4 cores. Over
    two interleaved rounds, the base failed 9 and then 5 of its 18 checks, and S10 failed 6 and then 2.

## Shared runtime: one per-frame cache, one noise, one figure factory, lazy tables (decision 45, S4)

This is phase 2, slice S4 of the code audit (`docs/architecture/audit_45.md` §4 and §5; findings DUP-01, 02 and 03,
and BUG-03, 04, 08 and 11). Each finding was checked again on the tree phase 1 and S1 left. How to use each helper is
in `docs/architecture/shared_runtime.md`. The game plays and draws the same, apart from the two bug fixes.

- **`FrameMemo` (`scripts/core/frame_memo.gd`) is the one per-frame cache.**
  - It replaced the seven hand-written caches in `WorldShared`, the HUD's badges and look, `TopdownWorld.soft_target`,
    `PostsPage.rows`, `PlaceRules.home` and `SpriteCache`'s loading budget.
  - It also replaced the cache phase 1 added for the tutorial coach (`hud.tour_targets`).
  - The HUD's badges no longer copy `points_override` on every call (BUG-08).
- **`HashNoise` (`scripts/core/noise.gd`) is the one hash noise.**
  - It replaced the five copies of the sin-hash and `TopdownTerrain.h01` and `vnoise`.
  - Its outputs match the old functions' bit for bit over a grid: 35,888 sin-hash points, 113,967 cells and 16,800
    noise values.
  - It is not named `Noise` because that is the engine's own class.
- **`Figures` (`scripts/presentation/figures.gd`) makes every figure of a character.**
  - The pages, cards, chips and views ask it for their figure. It replaced the 18 `TopdownDoll`/`Avatar` forks and
    `TopdownDoll.figure_for`, `dress` and `shown`.
  - Every side-view `Avatar` is made in one section, so retiring the side view deletes that section.
- **ContentDB reads its tables lazily (BUG-11).**
  - Boot reads only `realms`, `recipes` and the strings on the game's thread. A low-priority loading thread reads the
    rest beside the boot. A lookup that comes first reads its own table, and never waits on the thread.
  - Every lookup answers as before. `ContentDB.has_table` asks for one list table without reading them all.
- **GameEvents (BUG-03).** Its triggers are now sets, and its listener lists are copied on write, so a delivery no
  longer copies its list. Listener order and semantics are unchanged.
- **The TopdownFx cap (BUG-04).**
  - The cap no longer grows past 72 when loops fill it, and a new one-shot is no longer dropped as soon as it begins:
    the oldest loop goes instead.
  - `advance` drops finished effects in one ordered pass.
- **Checks.**
  - The new `shared_runtime_tests` suite (42 checks) is in `tools/run_tests.sh` and `Test.ps1`. It covers:
    - the noise over grids;
    - the memo's keeping and dropping;
    - the listeners' order during a delivery;
    - the cap full of loops;
    - the figures;
    - every table, room and dialogue tree against a fresh read, both as booted and as read by the thread.
  - Every other suite's check count is unchanged.
  - Captures match the base pixel for pixel, 13 of 13: Lotus Ferry, the Marsh Edge's fight, the selection's cards,
    and five pages of a top-down and of a side-view character.
  - The data build is unchanged.
- **Measured.** All figures are medians of interleaved runs on a shared 4-core machine at a load of 14 to 17, which
  inflates every time and makes `perf_tests`' millisecond budgets fail on the base and on S4 alike.
  - Boot, over 7 runs:
    - ContentDB's own load fell from 480 ms to 33 ms.
    - The engine's start to the title's first frame went from 9,273 to 8,923 ms.
    - A new character's first room went from 429 to 256 ms.
  - `perf_tests`, over 3 runs:
    - Rooms load in 44 ms on average against 43 ms, the slowest in 109 ms against 126 ms.
    - Lotus Ferry is entered in 397 ms against 458 ms, at 10.21 ms a frame against 11.27.
    - The Marsh Edge's fight runs at 17.54 ms a frame against 18.56.
    - The top-down fight's frame is within the noise: 14.93 ms against 10.94 in `perf_tests`, 14.60 against 15.56 in
      a separate probe that keeps the best of five rounds.

## Generator hygiene: one command line, one pixel library, the Grid held to the game, the dead data gone (decision 45, S5)

Phase 2, wave 1, slice S5 of the code audit (`docs/architecture/audit_45.md` §7): the Python generators the content
engines will build on, made tidy first. No game behaviour changes; the data diff is only the drops below.

- **One command line for the generators** (`tools/data/common.py`, `tools/data/README.md`).
  - Every generated file leaves by `emit()`: written only when it changed, or with `--check` compared with the file
    on disk. `write` and `entries` use it; a folder a build makes whole says so with `clear()`, so a file renamed away
    goes (or, with `--check`, is stale).
  - `run_cli()` gives every module of `build_data.py`'s list, and `topdown_rooms.py`, the same flags and exit codes:
    `--write` (the default), `--check`, `--only NAME[,NAME]`; 0 written or current, 1 a failed check or a stale file,
    2 a usage error. `build_data.py` takes them too, so `build_data.py --check` proves all 301 tables current.
  - A module run as a script builds with the copy its own imports share: `world.py` run alone works again.
  - `places.py` and `sect_walks.py` take the Grid's starts, solids and measures instead of their own copies.
- **The grid's walking rules, held to the game** (DUP-10).
  - The Python Grid reads `step_up` and the jump (`impulse`, `gravity`, `mantle`) from `data/movement.json`, as the
    game does. The thresholds were hard-coded.
  - `topdown_rooms.py --check` now asks the game, through `tools/data/grid_parity.tscn`, for every layout's cells and
    auto-path reach. It compares them with the Grid, cell for cell: 27 layouts, 95 starts, all equal.
    `TopdownRoute.reach` is `find`'s own search run with no goal. Without a Godot the check says it did not run.
- **One pixel library for new art** (`tools/lib/pix.py`, DUP-08).
  - It takes the icons' masks, ramps, shading modes and material-tinted outline, props' mask moves and erosion, and
    the top-down and FX hashes and tileable noise. `python3 tools/lib/pix.py --check` proves each draws exactly as in
    its source.
  - The builders that kept their own copy of a hash or of the noise import it: `canvas.py`, `creature/motion.py`,
    `fxpix.py` and `tools/data/topdown_life.py`. Their art rebuilds byte for byte.
  - The four old libraries stay with the art they made. Their conventions differ, so moving that art is a redraw.
- **Dead data dropped** (DEAD-12, 13, 14), each re-checked against the current tree:
  - **Tables** moved out of `data/` (which ContentDB loads whole and the export ships) to `tests/data/`:
    `balance.json` (balance_sim's own), `legendary_chains.json` (the checks' and the wiki's) and
    `topdown/td_review_heights.json` (the captures' review room, now given to the view as a preset).
  - **Row fields:** the techniques' `mastery`; the shops' `buys_all`; the enemies' `weak_to` and `equipment_chance`
    (the builder keeps its own for the loot roll); the zones' `laws` and `exit`; and `same_stage_ok` on unlocks and
    quests. The one-lesson-a-stage rule it served moves into `story.validate`. After S1 removed their readers, the
    NPCs' `age` and `sound.json`'s `steps.materials` go too.
  - **Strings:** 51 `ui.*` keys nothing asks for. The 11 `world_view.*` keys are built from data and stay.
  - **Manifest ids:** 8 icons, 8 props and 4 UI assets that nothing names, with their drawings and files.
  - **Kept:** the artifacts' `named.archetype` and the sets' `archetype`, which the item plan's checks and the wiki
    read. The items' `core.qp_pct` was already gone.

## Dead code removed, and an old save's renamed recipe no longer crashes the Crafts page (decision 45, S1)

This is phase 2, slice S1 of the code audit (`docs/architecture/audit_45.md` §3 and §5; findings DEAD-01, 02, 05, 06,
07 and 08, and BUG-01). Each name was checked again on the tree phase 1 left behind: as a token and as a string
(`call`, `has_method`, `connect`), in `.tscn` files, in data and in tools. The game plays the same, apart from the bug
fix.

- **Removed: 160 lines of game code nothing ran, and seven files.**
  - `scripts/ornament.gd`, `scripts/room_gate.gd`, their `.uid` files, and the orphan `connection_visual.gd.uid`.
  - `art/environment/room-gate.png` (1.2 MB) and its `.import`, which only `room_gate.gd` drew.
  - Eleven functions:
    - `SoundBank.surface_of_material` and `is_night`;
    - `Avatar.still_image`;
    - `SpriteCache.icon_ready`;
    - `TechniquePicture.draw_cooldown` and `draw_qi_short` (the HUD draws the round ones);
    - `TechniqueTreeRules.tree_state`;
    - `TopdownLife.critter_count`;
    - the Techniques page's `_slot`;
    - `ContentDB.level_of` and `GameAuthority.level_of`.
  - Constants and variables:
    - `UiKit`'s six unused type-scale names;
    - `Page.GROUP_GAP`, the Mail page's `DESK`, `SceneRules.TARGETS` and `SpriteCache.ICON_PX`;
    - three HUD fan positions nothing reads.
  - Four signals emitted but never connected, with their emits: the side world's `room_changed` and
    `context_changed`, the top-down world's `context_changed`, and the HUD's `page_changed`.
- **Game code only tests called.**
  - Three functions are removed:
    - `ProgressionAuthority.tree_view`. Its checks now read `tree_node` and `realisations`, which the page uses.
    - `WorldRules.npc_room`. The auto-path check reads `rooms_with` itself.
    - `ProgressionRules.npc_age` and its one check. No page shows an NPC's age.
  - `WorldAuthority.context_portal` stays: the context button's portal loop now calls it instead of an inline copy of
    the same rule.
  - The 31 deliberate hooks the suites need are kept and marked `## Test hook`.
  - The side-view and tool-only code is left for its own slices (S2, S3 and the side view's retirement).
- **BUG-01 fixed.** A save that still named a recipe renamed or removed from the data crashed the Crafts page. The
  auto-refine queue stopped with a SCRIPT ERROR.
  - The page now looks every recipe id it did not take from the data up through its `made_by`, which returns
    nothing for an unknown id. That covers six lookups.
  - Each load drops unknown recipe ids from the known recipes, the pages held and the queue, with a warning. It skips
    this when no recipe loaded, so a broken data build never empties a save.
- **Tests.** The `rules_tests` suite gains `recipe_rename_suite`, with two checks. Both fail with the fix undone. It
  loses the NPC-age check, so it goes from 2,711 checks to 2,712. Every other suite's count is unchanged. The data
  build is unchanged. `npcs.json` `age` and `sound.json` `steps.materials` are now unread, and are left for S5 to drop
  in their generators.

## Tutorial bugs: a card a thumb can answer, and a cheap coach (decision 45)

The user played build 110 on an Android phone: the tutorial that teaches the buttons felt laggy, Done or Skip
sometimes did nothing and the card did not close, and there were many other bugs. The tutorials were played again as a
player: through the phone's own input path (a touch that also reaches the pages as a mouse click), at 1280×720 and at a
20:9 phone's 2400×1080, from a new character through the Prologue into chapter 2 and through every lesson a later
checkpoint had queued. What was found and fixed is listed in `docs/redesign/tutorials.md` §7 "Bugs fixed", each bug
with a check in the `tutorials` suite.

- **Done, Skip and Later act on the first tap.**
  - The card was placed around the pointing hand as it bobbed, so it moved every frame under the thumb. It is now
    placed once per step, from the hand at rest.
  - A page's tour waits for the page to come in (`Page.settled`) and for its anchor, instead of standing in the middle
    and jumping.
  - After the player closes a card, the next lesson waits 1.2 s on the same screen. A queue of lessons no longer puts
    the next card in the same place at once, which looked like a Later that did nothing.
  - A HUD lesson on screen keeps the screen when a higher-priority guide is queued.
- **Buttons for a thumb.** They are 56 px tall, with touch targets 8 px past them. They act on release, up to 24 px
  off, and show pressed while held. A phone's tap is taken once. A tap that closes a card guards its place for 0.35 s,
  so the second tap of a double tap reaches nothing under it.
- **Fingers are kept whole.** Each finger belongs to the HUD or the coach from press to release. A thumb on the stick
  sliding over a guide's card no longer leaves the character walking on alone.
- **Other fixes:**
  - A tab's tour under way resumes only on its tab.
  - Back and Escape skip a tour instead of closing the page under it.
  - Replay tutorials no longer starts the Settings tour at once.
  - Cards keep clear of the HUD's controls, plates and equip prompt, and a guide's card keeps off the thumbs' places.
  - A tall anchor gets its card tight over or under it.
  - The gear guide's hand moves on to Equip.
  - The Cultivate tour lights the fan while it is folded.
  - Guides wait for the HUD to fade back in after a scene.
  - The Map's Walk step and the last Settings step light their buttons for a new player.
  - The Qi pool's tour, now at Bone Forging 1, rings the Qi bar rather than the whole panel.
- **The lag.** Measured on a desktop CPU with `tools/dev/tutorial_prof.tscn`, the median of three runs each:
  - Hidden, the coach cost 40 µs a frame on the play screen and 531 µs over any page. It now costs 14 µs and 35 µs
    (2 µs and 8 µs timed directly in the suite).
  - Showing a lesson, it cost 0.62 to 1.02 ms a frame. It now costs 0.17 to 0.19 ms.
  - A page's "?" cost 188 µs on each drawing of the page. It now costs 2 µs.
  - A page's tours are listed once per page and tab, where every open page listed them twice a frame.
  - The HUD's controls are counted once a frame (`HUD.tour_targets`, shared with the HUD's own frame).
  - The words are wrapped once per step.
  - The card is a child node, drawn again only when it changes.
  - The authority's poll checks only the passing states (0.34 ms down to 0.04 ms every half second). An event checks
    only the kinds it can bring.
- **Tools.**
  - `tools/dev/tutorial_play.tscn` plays the tutorials as a player on the prototype's QA walk. It answers every card
    with a finger, shoots each card and reports each miss. `--only=sweep` plays every lesson a kept game has queued.
  - `tools/dev/tutorial_prof.tscn` measures the coach's frame.
  - The QA walk gains `--only=<steps>` and a `p_boat` step.
  - `tests/prologue_run.gd` keeps "Crab Trouble done" and "The River Token" for `--keep`.
- **Tests:** the `tutorials` suite goes from 87 checks to 136, with a new section 10, "the card under a thumb". Each
  check was confirmed to fail with its fix undone.

## The first boss: the eel wakes, and the elders come (decision 45)

The Hollowed Eel of the Hollow Night was a fight the player won with a blade before they had ever cultivated. It is
now the first boss, and it is lost by design: at 80% of its HP it wakes, too strong to stand against, and the elders of
Lotus Ferry come out of the dark and slay it with cultivation arts. That is how the player learns what cultivation is,
and the Cultivation page unlocks through the same `night_survived` flow as before. As built in
`docs/redesign/story_staging.md` §3.6 ("The first boss"); screenshots before and after in
`docs/redesign/feedback/first_boss/`.

- **Phase 1** is the old fight, with 3.3 times the HP (`hp_mult` 1.0), until 80% (or 90 s into its fight).
- **The waking** (`eel_awakens`, a cut that holds the fight): the camera closes on the eel as it rears, the river
  boils (a new story art, `river_boil`), it roars (`story_eel_roar`, `story_river_boil`), the screen shakes and
  flashes, the night's colours bruise toward dread (lifting as the elders bind it), and the music crosses to its
  awakened theme (`boss_eel_awakened`). Aunt Ping cries a warning, and the prompt says the truth: "Its hide turns
  every blow now: stay alive!" It is drawn in a new awakened look (`hollowed_eel_awakened.png`: 1.22 times the size,
  near black, a crest of spines, red eyes).
- **Phase 2** cannot be won, and cannot kill. The surge and a new thrash are faster, wider, `unblockable`, and take a
  share of the player's max HP (18% and 12%), so no armour or healing outpaces them. Its hide holds its HP at 72%
  (every blow, burn, technique and treasure passes `_damage_enemy`, which shows "Glances off"). No blow takes the
  player under 30%, and the blow that reaches that floor (or the river rising, 22 s in) leaves them overwhelmed:
  held down, the eel looming. The boss bar is hatched under the floor ("Its hide turns every blow"). The night's
  event shows no countdown.
- **The rescue** (`elders_come`, about 24 s staged): Granny Liu binds it with **Nine Seals** (`talisman_array`,
  `story_talisman`), Old Ma drops the **Thousand-Catty Palm** on it (`force_palm`, `story_palm`), and Lu comes up the
  river in his boat and ends it with the **Coiling River Dragon** (`water_dragon`, `story_dragon`). Each lands with a
  hit-stop, a struck flash, a screen flash and a shake. The dragon's checkpoint slays the eel (`slay_foe`, the elders
  its killer). Whatever the player drank or used against the awakened eel is given back.
- **Into cultivation** (`grey_lifts`, rewritten): the elders stand you up and heal you, name what you saw
  (cultivation), and Lu calls you to his boat. The quest and flag order is unchanged, so Cultivate, the Cultivation
  page, the breakthrough, the Codex and their tutorials unlock as before.
- **No soft-lock:** a player who flees still meets the waking on its clock and the rising river; a fall in phase 1
  begins the night again; the flags `eel_awakened`, `eel_overwhelmed` and `night_held` carry each stage over a reload
  (the eel rises again awake; has you down again; the night comes back won). The waking and the rescue replay whole if
  cut short (`resume: false`). With no scene director, the elders slay it 30 s after it has you down. The event's
  timer is still the last resort.
- **The stage** (`SceneDirector`, `SceneRules`): new steps `art` (a story art of the FX sheets where a target stands),
  `foe` (a room's foe staged: its pose, a struck flash, the dread lifted from it) and `hitstop` (the stage's clock
  held); spots `beside` a target where it stands (mirrored to the side away from another); `hold_fight` scenes take
  the stage from a live part or a hand-off; a letterboxed camera may look past the room's edge by the bar's height; an
  art may come in from an actor's side (`from`); a blow's flash or flinch under way is no longer frozen on a body
  through a cut. Room events gained `unless`, `from_start` and `won_if`.
- **Art and sound:** four story arts in `tools/art/fx/story_arts.py` (FX pipeline, index palettes, nearest neighbour);
  the eel's awakened look in the creature pipeline; five sounds and the awakened theme in `tools/audio/story.py`
  (ids in `tools/data/sound.py`).
- **Checks:** `hollow_night` rewritten (76 checks: the waking at 80% by blade and by technique alone; its hide against
  a billion, a burn and a technique; that phase 2 cannot be won or kill; the scenes' order and the eel slain in
  `elders_come`; the unlocks and their tutorial; the refund; fleeing, falling, and reloads awake, in the rescue and
  after the kill). `prologue_run`, `balance_sim` and the capture (`topdown_capture -- --first-boss`) play the new
  night.

## Progression numbers, three quick slots and a 50-space bag (decision 45)

The user's feedback on build 110: charged attacks should out-damage a basic attack; the player should have Qi when the
first technique comes; meditation should give much more cultivation at the start, with ways to raise its speed;
quests and pills should give a fixed amount instead of a percentage; three quick slots; a bag of 50. The numbers, old
→ new, are in `docs/cultivation_loop.md` §16 and `docs/redesign_top_down_plan.md` ("As built: decision 45").

- **The charged attack.** The long drag on Attack now charges while held past the finisher's line: the blow rises in
  a straight line from the plain finisher (let go at once, as before) to 2.2–2.4 basic hits at 0.4–0.6 s by family
  (`combat_feel.json` `charge`), so every family's full charge is 1.8–2.5 of one basic hit and deals 7–42% more a
  second than its whole chain over the charge and the blow. The bow and the flute charge their one shot. The mark on
  the ground fills and burns warm when full; the hit's number is bigger in pale gold with "Charged ×2.3" over it.
- **Qi at the first technique.** The Qi pool opens at Bone Forging 1 with Flowing Palm (from Bone Forging 7), full,
  its bar and tour with it: about 30 Qi, 3.6 palms. Qi comes back as if the pool held at least 100 (0.75 a second at
  rest, 6 meditating), so the small first pool refills in about 40 s. The First Current now wakes the springs.
- **Meditation's early current.** `meditation_rate` × 3.0 at Mortal and Bone Forging 1, 2.5 at Level 9, 1.8 at 18,
  1.3 at 27, 1.0 from Level 36 (it replaces the body stages' ×0.3): Bone Forging 1 at the valley's 1.2 gathers 212 a
  minute (from 22), its stage in 2.8 minutes (from 28); Cloud Stride and later are unchanged.
- **Cultivation speed.** The Cultivation page's speed line ("Meditating here: 216 a minute · ×3.0") opens a list of
  every term of the rate and each bonus with its time left, and the ways to more, lit once open. New: Qi-Gathering
  Incense (+30% for 10 minutes, Granny Liu's hut from Bone Forging 1 and Stoneford, 12 taels) and Deep Current
  Incense (+50% for 15 minutes, Stoneford from Qi Kindling 1, 45 taels), with their icons.
- **Fixed rewards.** Each quest's tier is found as the data is built and it pays its kind's share of that stage's
  need as a number (`quests.json` `tier`, `cultivation`); a posted mission pays by the Level it was posted at. Pills,
  cores, raw herbs and the Spirit Fruit pay a number by their grade and say it ("+420 cultivation"); the River's dream
  +150; a chess problem before any Dao +120. Losses (a grave wound, a failed breakthrough, a method switch) stay a share
  of the stage, as a penalty should. `data_validation` refuses a share in any content.
- **Three quick slots** on ring 2 at 204°, 226° and 244° round Attack (`quick:0`–`quick:2`), each drawn while it holds
  something, with its own cooldown and count; set from the Bag's Quick 1, 2, 3; saved (an old save's one slot is the
  first). Past ring 2's six places the rest stand on an outer row. Tours find them as `quick:0`–`quick:2`, or `quick`
  for all.
- **A 50-space bag.** The bag holds 50 with no gourd and in the Starter Spirit Gourd (from 25), and each gourd up the
  ladder adds its 5 on top (the Lantern Gourd 90); Deep Pockets adds its row on top of that; saves grow on load.
- **Balance.** `balance_sim` places each quest at its own tier and pays its number, and meditates at the early current:
  every pacing row within ±15% (Qi Kindling 1 at 4.8 h, from 5.3; Sage 1 at 64.5, from 60.7; Sphere Lord 3 at 164,
  from 133). The thirty-day run of the posts is unchanged.
- **Review:** `docs/redesign/feedback/progression/` (the HUD's three quick slots at 1280×720 and 2400×1080, the Bag at
  50, the Cultivation page's speed list, a basic and a charged hit in the combat text).

## Work and place poses, and a held-tool rig (decision 44)

Decision 43's living world borrowed the figure's fighting moves for its villagers' work (the woodcutter swung the heavy
sabre, a sweeper held a guard, the cook wrote with a brush) and drew their tools as small sprites placed by the
figure's outline. The work is now drawn in the character pipeline, body first (AGENTS.md), with each tool in the
hands on every frame; and using a place plays a pose before its page opens. As built in
`docs/redesign_top_down_plan.md` ("As built: work and place poses"); the art rules in `docs/redesign/art_bible.md` §13
("Work and place poses") and §14.13.

- **Eleven work actions** (`tools/art/topdown/figure/work.py`), each a short loop with a key pose, an anticipation and
  a follow-through, in the five drawn facings (three mirrored): a two-handed broom sweep, walking with a shoulder pole
  (both hands on it, the baskets bobbing a beat behind the step), holding a rod out and casting it, reaching up to hang
  washing, stirring a pot with a ladle, a pestle in a mortar, an axe's overhead chop, a one-handed hammer at an anvil
  (tongs holding the hot bar), crouching to pick herbs, mending a net seated. The weapon is put away in each (an
  explicit hidden entry in every weapon section).
- **Three place poses:** `open` (a lid, the letter box, the storehouse's door, with the left hand), `tend` (a garden
  bed or a furnace, crouched) and `sit` (the mat, redrawn on the body), the weapon kept as their lines say.
- **The held-tool rig:** a `tool` layer set (`figure/sets/tool.py`, `figure/kinds/tool.py`) cast from the same
  skeleton: broom, shoulder pole with its baskets, rod with line and float, washing (a basket on the shoulder, a
  cloth), ladle and pot, pestle and mortar, axe, hammer with tongs and the hot bar, herb basket, net and needle; each fitted
  to the fists the pose puts on it (cut away inside them), in the §14 palette and the figure's lighting, nearest
  neighbour; drawn only in its own actions (the broom, rod, axe and herb basket carried in idle and walk) and
  explicitly hidden elsewhere.
- **The living world wired to them:** every stand-in replaced (the woodcutter swings an axe, not the sabre); a working
  step runs whole cycles so `life_work_chop_hit` and `life_work_hammer_hit` land on the drawn contact frame on every
  blow; a worker wears their loop's tools; a cook, a grinder, a smith and a net mender stopped by the player keep their
  work pose's rest frame, the tool in hand. The smiths hammer on their room's own anvil (each spot stands it where the
  blow meets its hot ingot, checked as the data is built); Granny Liu grinds by her stove in her own mortar. The held-tool sprites (`broom`, `pole_side`) left the life sheet; the loads
  set down at a spot stay.
- **Places:** the HUD plays the pose for 0.4 s, raising `place_open`, `place_tend` or `place_sit`, then opens the page;
  a second tap opens it at once; the body keeps the pose while the page is open (seated through the Cultivation page)
  and rises when it closes. `data/places.json` names each place's `pose`.
- **Checks:** the layer contract refuses a work action that keeps the weapon and a tool drawn outside its actions or
  missing from them; every work action holds a drawn tool; `topdown_life.py` refuses a step that is not a whole number
  of its action's cycles; `topdown_life_suite` checks every chop and hammer hit falls on its contact frame for a minute;
  `places_tests` walks up to each kind of place and checks the pose, the delay, the second tap and the hold.
- **Sheets and memory** (RGBA8, as imported): 168 sheets and 206.8 MB before, the tallest 512 x 1,446; 178 sheets and
  293.7 MB after (the ten tool sheets 0.8 MB of it), the tallest 512 x 2,072, all under 4,096 so none is split. The
  player's outfit 8.1 MB before, 11.2 after; a villager 7.5 before, 10.8 after. PNG on disk 25.3 MB before, 35.7
  after. The same draw calls a figure: a held tool is its layer's rect where the old sprite blit was, and the weapon
  draws nothing while put away.
- **Review:** `docs/redesign/feedback/work_poses/` (a sheet per action: every facing, hair colour, look, dye and
  weapon; in-game shots of the village, the sect and the player at the letter box, a bed and the mat), and
  `docs/redesign/phase3/character/12_work.png`.

## Sand and snow ground (decision 44)

Decision 43's sound pass made footsteps and landings for sand and snow, but no top-down tile painted either, so they
were never heard. Three new paint marks, drawn to Terrain v2's rules and lit by its sun: `a` river sand, `n` fresh
snow and `k` packed snow. As built in the art bible, §14.14.

- **The tiles** (`tools/art/topdown/sand_snow.py`, ramps `SAND2`, `SNOW2`, `WET`, `SHELL` in `palette.py`). Each is a
  64 px pattern with its decals. Sand: pale fine grain, wind ripples in broken rows of short crests, pebbles and shell
  chips; decals of shells, a snail shell, pebbles, heron and crab tracks, crab holes, driftwood, wrack and dune grass.
  Fresh snow: an even sunlit white with small wind crescents, buried mounds and a sparse sparkle; packed snow two
  steps down, trodden into prints and glazed in streaks. Sand's face is a beach running into the water; snow's is the
  karst cliff under the snow's lip, with icicles and snow on its ledges.
- **The transitions** extend the positional overlays grass already uses (14 corner cases × 16 places each): sand
  creeps over paths and paving as a thin drift, packed and fresh snow over the meadow, paths, paving, granite and rock
  (fresh over packed too), each in its own pixels, with edges that wander in soft lobes. Grass creeps over sand as
  over a path. Sand darkens where its corners touch the water (the `wet` tint through the tint masks), and the water
  by sand shows it through the shallows (`v2.water.beach`, 15 cases × 4 frames). Where two kinds of face meet on one
  level, the one whose top creeps over the other's runs into it in a lobe (`v2.face_end`), so a beach ends in the
  grassy bank and a bare lip in the snowy one at no straight seam. The atlas grows from 704 to 1,088 px tall;
  `build_tiles.py --check` stays byte-identical.
- **Where they lie** (`topdown_rooms.py`, `Layout.sand` and `Layout.snow`, ground paint only):
  - sand: Lotus Ferry's waterline from Home Lane's end to the ferry landing (and at night), with the washing beach, a
    cove and the landing under the docks; the Reed Shallows' beach and sandbar; the Marsh Edge's spits and islet;
    coves on Willow Path East's stream and Willow Path West's pond;
  - snow: no top-down room is set in winter and the peaks are green meadows, so only a dusting where the height
    allows it: the summit crags of Elder Hu's and Elder Sung's Peaks, the Meditation Rock's shaded back (packed where
    one sits), the heads of the side crags, Elder Sung's high east peak and the back of the far peak, and the Cloud
    Sect's cliff crown and top ledge on the Cliff Stair, with a packed path from the library's door to the bell.
- **Steps.** `k` steps as snow (`tools/data/sound.py`); `audio_tests` checks that every mark of the tile set steps on
  a surface with its sounds and that every such surface, sand and snow now too, is heard in a room of the world.
- **Foliage, light and life.** Sand takes a few pebbles, dune grass and reeds at the waterline (`decor.py`); nothing
  grows on snow or within a cell of it (`TopdownFoliage`). The cast shadows fall on both as on any floor. Critters land
  and peck on both (`TopdownLife`).
- **Review** (`docs/redesign/feedback/sand_snow/`): before and after of every painted room (whole at 1 art px, and a
  view with the body on the new ground), x4 close-ups of the transitions, the pairs side by side, a sampler of every
  transition drawn by the game, and the tile sheet at x4 (`tools/dev/topdown_capture.tscn -- --sand-snow`,
  `build_tiles.py --review-sand-snow`).
- **Tests.** `topdown_suite`: the layers of sand and snow and their faces; `data_validation`: the creeping sets, the
  wet tint, the faces and the sandy shore; `audio_tests`: the surfaces.
## Foe polish: the marsh leech redrawn, and the four-legged foes head-on (decision 44)

Decision 43's foes were weakest in two places: the marsh leech read as a slug-shaped pickle, and a four-legged foe
facing the camera or walking away read as a blob. Built in `tools/art/topdown/creature/` (art bible §8 "Foes"); every
combat number, the hit frame and the wind-up rates are unchanged. Before and after, in the game (the Reed Shallows'
flats, `tools/dev/topdown_capture.gd -- --monsters --monsters-polish`) and from the sheets:
`docs/redesign/feedback/monsters/polish/`.

- **The marsh leech** (`creature/leech.py`, rewritten). Its body is laid along a spine resampled by its length, so it
  can loop and rear and keep its shape: flattened, broadest in its hind third, tapering to a narrow head, a groove
  every ring (painted by the length along it, so the rings follow the loop); dark olive down its back going to black
  on its flanks, a paler khaki belly banded by the same grooves. A wet sheen (`sculpt.Part.sheen`, new): where the
  surface turns half-way between the §14 sun and the camera it steps up to the bright and highlight steps, the ramp lit
  late so the sheen is what reaches them, and the grooves cut through it, so every ring has its own glint. At the
  front a sucker mouth, a fleshy lip ring round a dark maw with tiny teeth, puckered as it creeps and flared into a
  cup to feed; at the back a smaller sucker, a disc with a lit rim; pale eyespots on its head. It walks as a leech
  does, an inchworm's loop: the rear sucker holds (sliding back at the walk's rate, so it is planted in the world)
  while the front stretches long and thin and plants, then the rear is drawn up and the middle rises in a loop the
  body's own length. It swims (a new `swim` row, 8 frames at the walk's rate, `creatures.EXTRA`): a flat ribbon with
  a wave running tailward and ripples along it; the room view plays it for its walk and idle where it stands in water
  (`TopdownWorld.FoeView`; today's leeches keep to land, as every foe that does not fly). The tell is still the S-rear
  with the mouth wide, now clearer: it winds sideways too (wider head-on), its head level over its prey in the side
  rows and standing up in a column facing the camera, the cup turned toward the camera. It lunges and latches, swells
  as it drinks, balls up when struck, writhes, curls and goes limp in death. Its elite keeps the elite look: the darker
  ramp, pale-gold Qi at its outline, and three pairs of gold glow spots down its back (`Pose.eye` with no colour now
  draws on an elite only).
- **Head-on and tail-on** (`motion.headon`; `creatures.Spec(view=True)` tells a pose its row's turn on the ground):
  full in the S and N rows, nothing in SE, E and NE.
  - *Facing the camera:* the boarlets' face lifts 12° (the otter's 10°, the rat's 4° so its snout still points), the
    forelegs stand apart and a little forward so they show beside and below the chin and step with a higher lift, the
    ears stand out at the head's corners, the boarlets' shoulders widen past the head and their tusks sweep out, and
    the body behind is drawn in. The rat's reed tail lies swept out to one side on the ground (raised, it stood up
    behind its head like a stalk).
  - *Walking away:* the rump rounds, the hind legs spread and step, the ears rise over the back; the boarlets' tail
    now droops dark off the top of the rump with its tassel (in every row: the hide-coloured curl was lost against the
    rump), the otter's thick tail swings wider and curves off to one side, and the toad's golden eyes rise over the
    moss of its back while its folded hind legs spread.
  - Walks, tells, strikes, flinches and falls were checked in both rows for both boarlets, the rat, the otter, the
    toad and their elites; the otter's tail now curls round toward its belly as it dies, so facing the camera it no
    longer stands up from the body, and the hollowed boarlet's three grey strands fan out from its spine head-on and
    tail-on (bunched, they stood over its head like one grey horn). The crab keeps its broad side to the camera, so it
    is unchanged.
- **Sheets** (all under 4096 px a side): the leech 2021 × 200 (from 1540 × 170) and its elite 2537 × 285 (from
  1960 × 250), with the swim; the boarlets 1680 × 205 and 1680 × 220 (from 1610), their elites 2100 × 285 and
  2100 × 305; the otter 1820 × 210, the rat 1575 × 170 and its elite 2030 × 245; the toad's as they were. The room
  view still draws a foe with one call; the crab, frog, snapper, puppet, minnow and eel sheets are byte-identical.
- **Checks:** `topdown_suite` has the leech walking on land and swimming in water from its sheet's row (its elite's
  too); `data_validation` holds an action past the catalogue (the swim) to the frame and sheet rules;
  `build_foes.py --check` is byte-identical; `balance_sim` green.

## The late HUD powers teach themselves (decision 44)

Decision 43's tutorials left out the HUD powers that open after the prototype. Each now has a guide from its unlock
and a short tour on the play screen, as built in `docs/redesign/tutorials.md` ("A late HUD power", §5's table).
Screenshots of every step at the phone layout are in `docs/redesign/feedback/tutorials/late_powers/`.

- **The powers and where they open:**
  - Spirit Sense: `spirit_sense`, Spirit Awakening 1.
  - The Presence: `presence`, Will Manifest 1 and "Will Manifest".
  - The Sphere: `sphere`, Sphere Lord 1 and "Sphere Lord".
  - Treasures: `treasures`, Heart Tempering 1, with `treasure_slot_2` at Spirit Awakening 1.
  - The weapon swap: `dual_loadout`, Heart Tempering 1.
- **The guide.**
  - The hand, the ring and the "!" point at the power's own button. A button in the folded fan has the hand on the fan
    first: "New in the fan: Sense. Tap the fan to open it."
  - A tap on the button under the hand plays the tour and does not use the power.
  - The swap's guide first leads to the Bag, to set a spare weapon, since Swap only shows with one.
  - After the tour, the Sphere's guide goes on to Cultivation's Dao tab, and the treasures' to the Bag.
- **The tours.** Three steps each, two lines on a phone:
  - the button, what it does;
  - its cost on the panel's SL or QI bar (10 Soul and 6 s a pulse; Soul or Qi each second held; Qi a use, then a rest);
  - a "try it" whose spotlight lets the tap through and ends the tour when the power is used.
  - A Treasure button comes out only in a fight, where the coach waits. So its tour plays at rest and lights the place
    on ring 2, with the treasure drawn faint there. It has no "try it".
- **Anchors.** `HUD.tour_rect` names the panel's `qi` and `soul` bars. At rest, `treasure:0` and `treasure:1` name
  the place where each button will come out. The Bag marks its first `weapon` and `treasure_item` in view. The fan's
  toggles and Swap already had their roles.
- **Rules as built.** The late guides wait out fights, scenes, talks and confirms, and queue one at a time.
  - The tutorials record has a version (`v`, now 2). An entry has a `since`.
  - A save from before these lessons counts the powers it already has as known.
  - The coach lights a thin anchor 3 px round, so the next bar stays dim.
- **Tests.** The `tutorials` suite has 87 checks (from 53), and its "later" list is gone.
  - Every late power has its guide and tour.
  - Their 29 anchors are found on a character at each realm once the power is unlocked.
  - Spirit Sense runs end to end through real taps.
  - The treasures', the Sphere's and the swap's guides are checked in their own orders, and so is the old save.
  - `tools/dev/tutorial_capture.tscn -- --late` takes the screenshots.

## The living world's sounds: critters, people at work, places used (decision 44)

Decision 43's living world raised a named sound for each moment of life, and the bank had none, so the critters and
the villagers at work were silent. Now they sound, synthesized in code like the rest (`tools/audio/life.py`), as
ambience well under the fight and falling off with distance. `docs/redesign/sound.md` §10 has the design and the
review, §9 a listening guide.

- **Critters:** a flock of sparrows bursting up (wings and alarm chirps), a fish darting off (a flick and a plip), a
  frog's squeaking leap and its plop, a hen scattering (wings, clucks, a "b-gawk"), a cat waking (a trilled "mrrp", a
  mew, a stretch), a village dog glad to see you (two "arf"s, or a "ruff" and a whine).
- **Work,** one for each cue of the loops: a broom on paving, a load set down off the pole, scrubbing on a ribbed
  board, washing shaken out and pegged, a herb snapped, a ladle round the pot, a pestle in a mortar, the axe's swing
  and its bite (splitting the log two blows in three), the hammer's swing and the anvil's ring (a lighter tap between
  blows), the forge poked to a crackle, a line cast and recast, a net's cord drawn tight, a rustle as someone looks
  about, a brush on paper, a meditator's slow breath.
- **Places** for the place poses: `place_open` (a latch, a creak, a lid knocking open), `place_tend` (soil and
  leaves), `place_sit` (settling on a straw mat).
- **Takes** where repetition would show (the sweep, the washing, the axe, the hammer, the dog) play in turn, and every
  one is varied a little in pitch and level. The village ranks under every sound of the fight in the voice pool: at
  most three critters and three workers at once, and any blow, step or tell takes their voices first.
- **Checks:** `tools/data/sound.py --check` fails when a cue the code or `data/topdown/life.json` can raise, or a place
  sound, has no file (it reads the data's cues and the code's `raise_cue` calls); `audio_tests` checks the same in the
  engine, plays a raised cue once where it happens, the takes in turn and a busy village under a fight. Review pictures
  and a loudness table in `docs/redesign/feedback/sound/life/`.
- **Size:** the audio in the APK went from 7.04 MB to 7.33 MB (38 more one-shots, 1.36 MB of sources). Frame time:
  within the shared machine's noise (Lotus Ferry with the living world 7.96 ms a frame before, 8.26 after, the least
  of six rounds, medians of three runs each).

## The Marsh Edge fight back inside its frame; the tutorials suite's crash on quitting (decision 43 follow-up)

With decision 43's seven pieces merged, `perf_tests` failed one check on the quiet test machine: chapter 2's Marsh
Edge with 25 foes fighting took 18.3-22.5 ms a frame against its 16.6 ms budget (the mean of the first 150 frames
after the room is entered and 15 of its foes are turned on the player). As built in `docs/redesign_top_down_plan.md`
("the Marsh Edge fight back inside its frame").

- **Where the time went.** A probe running only the check's Marsh Edge part (three entries a run, two runs a commit)
  over the merges: 15.7 ms before decision 43 (55eda88); 14.2-14.9 after the tutorials, the people 1.2x, the
  monsters, the places and the sound (inside the ±1.5 ms a run swings); 16.2 after the round buttons and combat flow;
  16.8 after the living world. So the fight was near its budget before, and decision 43 added about 1.5 ms. Timers
  round every `_process`, `_draw` and tick placed the frame: the simulation 4.2 ms (it runs 1.8 times a frame in the
  check, its own tick and the world's physics tick; the foes' AI 2.6 of it), the world's `_process` 4.1 (the labels'
  layout 2.5 of it), the HUD's drawing 2.9, the views asking the World authority whether each thing shows 83 times a
  frame (1.0), the HUD's points badges three times a frame (0.7), the minimap 0.8. No one part took the frame; after
  the first fixes the engine's own script profiler (the local debugger's, `-d`, over the fight's window) still found
  it spread thin: the foes' AI, the labels, the HUD's text, each view's own step.
- **Why the check's window was slower than the living world's A/B rounds** (14.5 ms with it, 13.8 without, in the
  same run): the A/B figure is the least of six rounds' medians, taken after the room has been rebuilt, while the
  check is the plain mean of the fight's first 150 frames, and that window carried one-off costs a median skips. The
  spawn frame loaded the four species' sheets (10 ms; a 35-54 ms frame, then two or three physics ticks to catch up);
  the first blows loaded the fists' smears (8 ms), each direction's impact marks (3.6 ms each), the common marks
  (4.8 ms) and the damage numbers' font (4 ms); and the water redrew every chunk in view four times a second (5 ms
  each time). A frame over 16.7 ms also brings a second physics tick with it, so a slow stretch feeds itself.
- **What changed** (the same pixels, sounds and rules): the labels' layout tries a label's own row and last frame's
  first and weighs its other rows only against the boxes in reach, sorted by the engine (the same offsets, checked
  against the old pass on 3,000 random crowds); visibility, quest markers, ways' states, the quest tracker and the
  direction's step asked once a frame (`WorldShared`, again when `Game.revision` moves), and the points badges likewise;
  the context button weighs reach before requirements; `free_at` and the chase's clear line read the grid directly;
  sanctuaries gathered once a room; a foe winding up, striking or recovering no longer asks where the player is and
  whether it sees them; the stats, movement and curve constants kept once found (`ContentDB`, forgotten by `load_all`)
  and a Level's realm worked out once; the soft lock worked out once a frame; each species' walk cycle once; the
  fight's sheets and the numbers' font asked for on the loading threads as a room is built; the water's four frames
  drawn once each; the air's three layers each pass over the others' particles; a foe's figure moved once a frame and
  its label view no longer redrawn empty; text widths keyed without formatting.
- **After**, `perf_tests` alone, three runs interleaved with three of 3c0bb0f on one machine (a slower one than the
  first measurements': there 3c0bb0f failed the side view's sword swarm in all eight of its runs and the 22-foe
  prototype fight in three): the Marsh Edge fight 11.6-13.9 ms a frame against 18.2-20.2; the prototype's 22-foe fight
  9.7-10.0 against 13.1-15.3; Lotus Ferry walking 7.7-9.3 against 10.4-12.0; the side view's crowd with the sword swarm
  15.0-16.2 against 16.8-17.6; the rooms' loads as before. The branch passed every frame budget in all three. In the
  full runs, where `perf_tests` comes after ten minutes of other suites and this machine ran slower still, the Marsh
  Edge fight took 12.3 and 15.9 ms, and the side view's sword swarm (outside this work, failed by 3c0bb0f in every run
  here) once went over, 17.5 ms.
- **Still loose**: the v1.5 techniques.json check (filling in the defaults at most twice the JSON parse, plus 20 ms)
  fails now and then on this machine, 3c0bb0f too (one run in three to six; 128-163 ms against a 50 ms parse at worst).
  Its two halves slow unequally with the process's history: in one process, `ContentDB.expand` over the fixture took
  113 ms the first time and 180-205 ms each time after, the parse 51 then 60-75 ms. Left as it is, measured as it is.
- **The tutorials suite's non-zero exit** ("53 checks, 0 failures", then a non-zero exit, in full runs): the engine
  crashed as it quit (signal 11 in a mutex; `run_tests.sh` and `Test.ps1` now print a failing suite's exit code, and the
  shell script its last lines). The Techniques page's preview reads the foes' index (`data/topdown/foes.json`) on a
  worker thread with a script lambda; a preview gone before it took the reading back left the task unclaimed, the
  lambda outlived `TechniquePreview.TopFoe`'s script ("1 orphaned lambdas becoming invalid"), and the thread pool's
  teardown freed it after the script language was gone. Whether the page's preview took the reading back before it
  closed depended on the worker's timing, hence a crash only now and then. The preview now takes the reading back as it
  goes (`TopFoe.settle`, as `TechniquePicture` already did for its pictures), and `rules_tests` checks it. A scene that
  opens the page and quits at once crashed 6 times in 6 with the fix taken out and never in 15 with it; the suite alone
  exited 0 in 8 runs and in every full run since.
- **The calendar on a Terraces Trial day**: the trial's note under the chosen event wraps to two lines, and its last
  word fell past the card's edge (`rules_tests`' B17/B22 check failed on trial days, at 3c0bb0f too); the event's
  words now take what the note leaves of the card's three lines.

## A living world: critters, people at work, grass that parts, smoke, banners, vistas and interiors (decision 43)

The user's picks after build 109 asked for "a living world: critters, NPCs at work, grass that parts, smoke, banners,
vistas, and interiors", in the spirit of Alabaster Dawn. Built to `docs/redesign/art_bible.md` §14.13 in every room on
the grid; before, after and close-ups in `docs/redesign/feedback/living_world/`.

- **Critters that notice you.** Sparrows fly in, hop and peck, and the flock goes up as you come near; butterflies
  flutter at the flowers and dragonflies over the water; fish glide as shadows under the river and rise in rings, and
  dart off from the bank; frogs call at the marsh's edge and leap into the water; the village's hens scatter, its cat
  wakes and walks off, its dog comes to greet you; fireflies drift away at night. Cheap: at most 24, pooled, dropped
  off screen, no physics, spawned from each area's table and each room's own animals.
- **People at work.** 52 villagers and disciples in 21 rooms work short loops of their own actions between two to four
  spots: Aunt Ping sweeps her lane and cooks at her stove, Washer Mei washes at the river and hangs her washing, Uncle
  Guo trains his fists, Shen Lian carries baskets on a shoulder pole, Fisher Wen mends his nets, Little Dou plays and
  scatters the hens, disciples sweep and practise sword and staff forms, the smiths hammer and stoke their forges,
  gardeners and physicians tend herbs, vendors call their goods. Five people with no part in the story fish, chop wood
  and sweep where a room has the work. They stop and turn to you at your side, and someone with a quest waiting stays
  at their own spot, so the marker and the talk are where the tracker points.
- **Grass that parts** round you, the foes and the people walking, rustling faster at a sprint; tall grass and
  cattails lean aside; a slash over grass throws cut blades.
- **One wind** for all of it: the grass leans in its gusts, chimney smoke and incense drift along it, the sect banners,
  the washing and the red paper lanterns flap and swing on it (and the lantern's night flame swings with it), and
  the cook fires, stoves and forges steam and spark.
- **Vistas** past 22 rooms' edges: karst peaks rising behind the sects, the valley's hills behind the village, the
  marsh going on, the river flowing on past the south bank, the sects' edges falling away in a cliff into a drifting
  sea of cloud with peaks standing out of it (the path's stairs going on down), and the river all round Lu's boat.
- **Interiors** furnished to say who lives there: Aunt Ping's stove, bed and nets; Granny Liu's cabinet of jars, drying
  rack, mortar and her cat; Old Ma's goods, sacks and cloth; the weapon halls' forges, plaques and scrolls. The sun
  falls through their windows in shafts onto the floor, with dust turning in them, and the stoves and forges glow warm.
- **Sound hooks.** Each moment raises a named cue as a positional world sound (`Audio.world_sound`:
  `life_sparrow_flee`, `life_dog_bark`, `life_work_hammer_hit`, ...), silent until the sound bank is given them; the
  people walking between their spots step like the sound pass's walking villagers.
- **Cost** (headless, on the shared four-core test machine; `perf_tests` run alone, twelve runs, the last three after
  merging the other decision-43 pieces). Lotus Ferry walking (the busiest room: about ten critters in view, seven
  people at work and two extras, smoke, two vistas): the living world's own work 0.48-0.70 ms a frame (median 0.6),
  and the whole frame with it against without it, in rounds run back to back, +0.3 to +1.8 ms (median +1.0) on a
  6.5-8.8 ms frame. The Marsh Edge with 25 foes fighting: own work 0.53-0.75 ms, the frame -0.2 to +2.1 ms (median
  +1.3) on 13-17 ms. Its build adds 1.2 ms to Lotus Ferry's (0.7 ms to the marsh's); entering Lotus Ferry took
  173-264 ms with it and 160-283 ms without it in alternate runs, and the first two seconds' walk 9.4-10.1 ms a frame
  with it and 8.7-12.6 without. Before any of it (the same suite that morning, a quieter machine): Lotus Ferry
  entered in 159-247 ms at 8.3-9.2 ms a frame, the marsh's fight 13.3-17.7 ms; after the merge, 187-287 ms at
  11.2-11.9 and 16.9-20.1 ms. `perf_tests` checks it in both rooms (its difference within 1 ms and a seventh of the frame, its own work under
  6% of a 60 fps frame); its other checks fail as they did before on a busy machine (the marsh's 25-foe fight over
  16.6 ms, the crowd under the breakthrough, the v1.5 rows' load).
- **Tests.** `topdown_life_suite` (by `rules_tests`): the loops keep to their leash and stop for the player, a quest
  giver stays reachable, critters flee and are dropped off screen, the pools stay bounded, the grass parts, the
  interiors and vistas are there; `data_validation` checks the art and data; `topdown_rooms.py --check` checks the work
  spots, furnishings and `life.json`.
- **Left for the figures' pipeline:** poses drawn for the work (a broom sweep, a shoulder pole, a rod's cast, reaching
  up to hang washing, stirring, a pestle, an axe's chop, a hammer, picking herbs, mending seated) and a held-tool rig;
  the loops use the actions that exist until then.

## Round technique buttons, smoother combat, jumps you can steer (decision 43)

The user asked: "The skills in the HUD should be a little bigger and circular", "Combat should feel more smooth", and
"because the player moves fast (that's ok), when I try to jump from a box to a roof I jump over the box; it's a bit hard
to control the jumping." `docs/ui_style_guide.md` §9 and `docs/redesign_top_down_plan.md` ("As built: smoother combat
and jumps you can steer") hold the details and the numbers.

- **Round technique buttons, 1.21x.** Each technique on the HUD is a round button 68 px across (from a 56 px square):
  an ink rim, the bright jade ring (slate when the weapon in hand cannot use the art) and the art's picture cut to the
  circle. The picture is still the card's miniature: the whole figure at x1 stands inside the circle and the rank badge
  sits inside it at the upper right. The four stand in the thumb's arc round Attack, clear of each other, of the 64 px
  Jump, of ring 2 and of the context's Talk button and its label; their touch targets are 80 px. Cooling, a radial
  sweep runs round from the top (an ink pie over the picture, the ring dim over the part still to wait, a pale gold
  hand, the seconds); ready again, the ring flares and a ring of light goes out from it (the flare alone under Reduce
  motion). Short of Qi, a Qi arc along the foot. The techniques and Attack stay out at rest. Shots before and after at
  1280 x 720 and at a 20:9 phone's 2400 x 1080: `docs/redesign/feedback/hud/*_round_*.png`.
- **Smoother combat,** found in frame-by-frame traces of real chains (`tools/dev/combat_trace.tscn`) and fixed in data
  (`combat_feel.json` `flow`):
  - the presses go in their order: Attack, Attack, technique no longer drops the second Attack (the technique cut in
    ahead of it); taps made while a technique waits are kept behind it;
  - a queued step aims again as it begins, at the foe the stick has turned to (it struck 111° off), turns the body and
    lunges toward it; every step pulls toward its foe, a far one within reach, a near one never overrun;
  - a technique woven into a chain knocks its foe back only as far as the next step reaches (a Mole Cuts knocked a foe
    to 96 units, past the fists' 46, and the next two blows missed: now 4 of 4 land); a chain's last blow and a lone
    technique keep their whole knockback;
  - a hit-stop holds exactly its frames (each held one more), and one action adds at most 10 in all;
  - a dodge pressed while a heavy blow is committed goes at the blow's cancel point (the heavy sabre's was dropped);
    the stick pushed out of a recovery cuts it at the same point when no press waits, so a sprint leaves a chain 10-12
    frames sooner; the feet stay planted through a blow's wind-up and strike (the stick slid the body 8.6 units through
    a swing); the stick's turns pass through the rows between, one a frame.
- **Jumps you can steer.** The stick steers in the air and brakes hard pulled back; let go, the body slows. A landing
  assist brings a jump that would carry a few pixels past a box or a roof it came onto down on it, and the top's edge
  holds the body a moment after it lands on something it jumped onto, so a thumb still pushing does not run it off. On
  the village's crates by the hall and the Jade Sect's by the Weapon Hall, a sprint and Jump 2 to 38 units short of the
  crates now lands and rests on them 10 times of 10 (0 of 10 before); from the crates onto the roof and off the hall's
  roof over the gap to the inn's, every jump still lands. The sprint was already not carried into the air (a take-off
  keeps the walk's 154); coyote time and the jump buffer are as they were.

## The people drawn 1.2 times bigger (decision 43)

The user: "I think the player should look a little bigger." The player and the villagers go from about 38 art px to
about 46 from sole to crown, drawn with more pixels, never scaled at runtime.

- **Re-rendered at the new size.** The character pipeline (`tools/art/topdown/figure/`) casts every layer at 1.104 art px
  a unit (`geom.WORLD_SCALE`, from 0.92): every layer set, all 864 frames of the 37 actions in the five drawn facings,
  every hair colour and dye, with the same proportions, poses, weapons in the hands and outfits. The face has more
  room: an eye is 3 px wide (a lash row, the white, a pupil and the iris, the iris's lower light) and the mouth 2 px.
  The working canvas grows to 136 x 124 (the feet at 68, 84), clear of the widest cut and the highest blade.
- **The technique pictures keep their framing.** The cards, the reading, the HUD's buttons and the loadout bar were
  approved with the 38 px figure, and a 46 px one no longer fits a 42 px button whole nor a card from the head to the
  ankles. So the 105 poses a picture draws are cast once more at 0.92 (the index's `pictures`; `TopdownFigure.frame_of`,
  `draw` and `bounds` with `picture`), and the pictures and the HUD's companion chip draw those. The Character page,
  the Bag and a shop's merchant draw the figure at x5, as tall as the 38 px one was at x6.
- **The size pass** (art bible §13, "The scale rule"; `TopdownRoom.PEOPLE`): the foot box 19 world units across (from
  16; its depth stays 10, which the stairs' side steps are measured by), the player's body for a blow on the grid 17
  wide each way (from 14), a body's height and chest 92 and 48 (from 76 and 40), a person's talk reach 132 (from 110) on
  the grid, markers, barks, a lifted plate and the label over a person who fights 16 higher, a staged scene's balloons
  over the heads at 104 (from 88) and a hand-off's chevron over a person 16 higher, the blob shadows 10 and 8 art px
  (from 8 and 7), the camera's body box 20 x 52 and its framing 14 px over the feet (from 16 x 44 and 12), the labels'
  keep-clear box round the body 34 x 77, and the FX sheets' hand and chest at 17 and 26 art px (from 14 and 22;
  `build_fx_topdown.py` rebuilt). The paces (walk 154, sprint 216), the jumps, the tops a body stands on, a blow's reach
  and every range stay as they were. Every way is a tile wide or more, so the bigger foot box passes them all
  (`room_lint`, `topdown_rooms --check`, the sect walks); no room has a bench, bed or seat a person sits on yet.
- **Cost.** The same draw calls. The 168 sheets hold 207 MB of RGBA8 (from 139; 512 px wide, the tallest 1,446), the
  player's outfit 8.1 MB (from 5.4); a full build takes about 6 minutes on two cores.
- **Screenshots** before and after in `docs/redesign/feedback/people_scale/` (`tools/dev/topdown_capture.tscn --
  --people-scale --people-tag=<before|after>`; the pictures with `tools/dev/picture_capture.tscn -- --tag=<before|after>
  --dir=people_scale`).
## The monsters at the characters' quality (decision 43)

The user chose to bring the monsters up to the characters' quality: more frames, tells that read, and bigger elites and
bosses, beside people growing 1.2×. The art bible's §8 "Foes" holds the rules; the plan's "As built: the monsters at the
characters' quality" the pipeline.

- **Drawn like the characters.** Every foe drawn for the grid (the mud crab, reed rat, wild boarlet, Trial Puppet, reed
  frog, marsh leech, reed otter, hollowed boarlet, Old Snapper, mossback toad, hollow minnow and hollowed eel) is now
  cast by the character's own renderer: 4 × 4 samples a pixel, seven-step ramps leaning toward the art bible's sun and
  shadow, a warm rim, a cool bounce and contact shade, tinted outlines a step lighter on the lit side with half-alpha
  stair corners, and a lighter inner line where a leg, a claw or a head stands in front of the body. Each sculpture was
  redrawn with fuller anatomy: the boarlet's high shoulder, wedge head and pointed ears, the crab's chelae and pale
  underside, the snapper's plates and moss, the toad's warts, the leech's flattened rings and ochre stripes, the
  puppet's rope, carved eyes and jade plate, the minnow's scales.
- **More frames, the principles of animation.** Every species plays idle 6, walk 8, wind-up 4, attack 6, hurt 3 and
  death 8 frames (from 4, 4, 2, 3, 2, 4): squash and stretch on the lunges, hops and landings, overshoot and settle,
  trailing tails, strands, weed and ferns, and a death that suits each (the crab and the frog flip onto their backs,
  the boarlet's forelegs buckle, the puppet's joints give and the jade on its crown goes dark, the hollowed boarlet and
  the minnow come apart into grey motes, the eel sinks until only its stain and rings are left).
- **A tell for each.** The wind-up's last frame is its tell, held until the blow: the crab rears and raises both claws
  wide open; the rat rears on its haunches, teeth bared; the boarlet lowers its head and paws the ground twice in a
  spurt of dust; the puppet draws its palm back and Qi gathers there in a jade orb; the frog crouches and its throat
  puffs up pale; the leech rears in an S, its mouth wide; the otter sits up; Old Snapper raises its crusher high over
  its head; the toad rocks back, cheeks bulging, mouth open; the minnow curls into a C; the eel rears high, jaws wide,
  eyes flaring. The rate of each wind-up comes from its `windup_s`, so the tell is always up before the blow; the blow
  still lands on frame 1 of the attack, and no fight timing changed.
- **Sized to the new people.** Every foe is about 1.2× its earlier size, so a crab still reads as a crab beside a person
  and a boarlet as a young boar. The Trial Puppet is a head over a disciple (51 px), Old Snapper 1.5× (77 px from its
  tail to its crusher) and the hollowed eel about 1.4×.
- **Elites.** An elite draws its own rows: 1.2× larger, darker, gold-eyed, and burning with pale gold Qi (a ring on its
  outline, tongues licking up off its back, motes rising). The crab, the rat, both boarlets, the frog, the leech, the
  otter and the toad have them; Old Snapper wears the ring of Qi in its own colours as its boss presence.
- **A sheet a species.** `art/topdown/foes/<species>.png` (an elite's apart, `<species>_elite.png`), each in its own
  cell and under 4096 px a side (the old single sheet was 1216 × 4320), indexed by `data/topdown/foes.json` and built by
  `tools/art/topdown/build_foes.py` (its own build now, apart from the tiles'). A room loads only its own species'
  sheets, and an elite's only where an elite stands: the Reed Shallows' foes take about 2.2 M texels, from the old
  sheet's 5.3 M. A foe is still one draw.
- **Screenshots** before and after in the game (the lineup idle, in its tell, on its hit, struck and falling, the
  elites, the eel, and fights under the HUD) in `docs/redesign/feedback/monsters/` (`topdown_capture.gd -- --monsters`),
  and every sheet at ×3, each species playing its catalogue as a GIF and the tells side by side in
  `docs/redesign/feedback/monsters/sheets/`.
- **Tests.** `data_validation`: the whole catalogue in five facings for every foe and its elite, inside its sheet, no
  sheet over 4096 px, every tell up before its blow. `topdown_suite`: an elite draws its own sheet in its larger cell,
  its label on its larger figure.
## Systems as places (decision 43)

The user: "don't forget some systems should be moved to the main world map instead." The study
(`docs/redesign/systems_as_places.md`) was waiting on them; its set for the prototype is built in the top-down game,
in the rooms the systems belong to. Its "As built" section has the whole account.

- **The place table.** `tools/data/places.py` builds `data/places.json`: 26 places, each with its system, page, room,
  object (one of the room's, or one it adds on the grid), cell, the cell its user stands on, kind, verb, what it shows,
  its rule (both, earned, place) and its remote rule. It is checked as it is built: every place is reached by
  auto-path from every way into its room, what it blocks cuts nothing off, and a system of the prologue or the tutorial
  has its home place on their path. `PlaceRules` reads it.
- **In the world** (`TopdownPlaceArt`, original pixel art in the §14 palette): Lotus Ferry's services round its square
  (the shrine, a new letter box, the notice board, a new Storehouse shed behind the chest, the pot, a meditation mat by
  the spring), Proprietor Fang's stall on Market Street (a counter with his wares, an awning behind him), a courier
  post, the furnaces, the beds, the stones and shrines. Each shows its state: papers on the board and a gold "!" when
  one is new, a red ribbon and the flag up on the letter box while a letter waits, sacks in the shed by what the
  storehouse holds, Qi mist over the mat, smoke from a furnace at work and a jade wisp when a batch is ready, glints
  over a ripe bed. Walking up and pressing the verb opens the same page.
- **Earned remote.** Storage opens from anywhere after a first use at a storehouse and Tailor Xun's pouch; a bed is
  tended from anywhere after the first harvest; the Crafts queue fills from anywhere after a first batch at a furnace
  and Qi Unfurling 1. Until then the Menu's new Storage and Garden tablets say where they live ("At the Storehouse")
  and open a card with Travel there, which walks through the rooms and on to the place (`auto_path` with `place`).
- **The map.** The world map's fourth view, Places, marks every area that holds the chosen kind of place, and its card
  names the place, what it shows and its rule, with Go there. The minimap draws each place of the room as a small
  glyph of its kind, a gold spark where something waits; a tap on one opens the map's Places on it.
- **A fix from the review:** an object's prop drew at its side-view depth as its z in the top-down view, over every
  body (a notice board over the head of one standing in front of it); the room now sorts it.
- **Tests:** `places_tests` (the table, every place opening its page from its user's cell, the three remote rules, the
  map's and the minimap's marks, the Menu's card and the walk, the unlock order) and `places.py --check`, both in
  `tools/run_tests.sh`. Screens in `docs/redesign/feedback/places/` (`tools/dev/places_capture.tscn`).
## The sound pass: layered hits, footsteps by surface, ambient beds, combat music, stingers and a mix (decision 43)

The user's pick after build 109: "layered hits, footsteps by surface, ambient beds, combat music that comes in with a
fight, and stingers". Every sound is still synthesized in code, original and seeded. `docs/redesign/sound.md` holds
the audit of what the prototype played before, the design, the review and a listening guide.

- **Layered hits.** A blow is the weapon family's transient (sword, sabre, spear, fan, brush, flute, bell, bow,
  fists), the struck body (flesh, shell, wood and puppets, slime and water) and the family's tail, played the moment
  the hit-stop lets go; two takes of each, varied in pitch and level, the weight moving the whole; a crit's or
  finisher's accent, the chain's last blow, a weave cancel. Blows landing together sound as one. Each family swings
  its own whoosh (the bow twangs), each element casts and strikes its own sound.
- **Footsteps by surface**, on the walk's and run's contact frames (fractions of the cycle in the data): grass, dirt,
  paving and stone, planks, reeds, roof tiles, wading water (sand and snow ready for their tiles), read from the room's
  paint marks, a prop's top and its water. Landings by surface and height, a splash into water. Foes and villagers step
  quieter, falling off with distance; foes' tells and deaths by race and body, where they stand.
- **Ambient beds** per place (the river, the village by it, the marsh, bamboo, pines, fields, the town, the sect, a
  cave, indoors), 16 s bases with layers of the hour (birds by day, insects and frogs by night) that follow the room's
  light, crossfaded on a room change. The rooms' beds are a table of their own (`tools/data/sound.py`).
- **Adaptive music.** The village by day and by night, the field, the river and the sect have a combat stem on their
  own grid, started with the track and kept in step: it comes in on the next beat when foes near the player turn on it
  and leaves on a bar line four seconds after the last falls (another track crossfades to the battle theme). Old
  Snapper and the Hollowed Eel have their own themes. Stingers for a quest done, a new realm, a rare find, a system
  unlocked, an elite and a victory.
- **The mix.** An All sound slider over Music, Ambience, Effects and Interface; a high-pass and a limiter on Master;
  the music ducking under stingers, talks, barks and scenes; 24 voices with priorities and per-sound caps (the
  fifteen-monster fight peaks at half of them); every new sound levelled by its loudness and kept audible on a phone
  speaker (`boss_sting` fixed). A talk's scroll and lines, barks, doors, loot hitting the ground, the scene cue, tabs
  and the missing `ui_confirm` now sound.
- **Size:** the loops are Ogg Vorbis now: the audio in the APK went from 8.38 MB to 7.04 MB while its sounds went from
  76 to 233; the sources in the repository from 41 MB to 9.8 MB.
- **Checks:** `audio_tests` (every sound named in data and code exists; the buses and sliders; footsteps by surface
  and frame; the layered hit; the combat music entering and leaving on its events and beats, Old Snapper's theme; the
  beds and hours; the stingers' ducking; the voice limit in the fifteen-monster fight), and `tools/run_tests.sh` checks
  `data/sound.json` and every audio file's levels, seams and phone band. Review pictures in
  `docs/redesign/feedback/sound/`.

## Every newly unlocked system teaches itself (decision 43)

The user asked: "I want the game to teach the player how to use new systems that unlocked. For example, when the
player first gets foundation points the game should navigate the player to the right screen to spend those points, or
when he unlocks the techniques page, the player should get a tutorial for each new system he unlocks and understand
how this system page works." The design note is `docs/redesign/tutorials.md`.

- **Guides.** A system opening starts one: an unlock, the first foundation points, Realisations, Bench or Post Art
  points, the first piece of gear in the bag, or the first bottleneck.
  - A hand, a pulsing ring and a small card with Later lead the player there, step by step: the HUD button (with a red
    "!" badge), the page, its tab, and the element to use.
  - With the first foundation points: the Menu button, Cultivation, the Foundation tab, then the +1. Spending a point
    through it ends the guide.
  - Each step is found from what is on screen, so a shortcut (the points badge) works too.
  - A place-only system leads to the nearest thing of its kind in the world, through the quest direction mark (the
    minimap's gold exit and chevron) and the World map's lantern.
- **Tours.** A page's (or a tab's) first opening plays one: 3 to 6 steps, each lighting one part of the page in a
  spotlight over a dim, with a line of at most two lines, Next and Skip.
  - A "try it" step lets taps through its spotlight and moves on when done.
  - The HUD's own controls get short tours: meditate, the technique buttons, dodge and guard, the Qi bar, the animal's
    button.
  - Every page of `PAGES` has one, except the talks and events. The prototype's pages came first.
- **The coach waits.** It never shows in a fight (a foe near, or blows in the last 8 s), a staged scene, a moment, a
  talk, a page's own question, or while a page is a game in play (fishing, the guqin).
  - Guides queue one at a time, by priority.
  - One tour plays each time a page opens.
- **The "?"** beside each page's close button plays its tour again. **Settings → Controls → Replay tutorials** makes
  every tour play again on its page's next opening.
- **Saves.** Progress is kept per character in the save, and a tour resumes at its step after a reload. A save from
  before this, or a character that skipped the Prologue, counts what it has as known.
- **Data.** `tools/data/tutorials.py` → `data/tutorials.json` (64 entries: the trigger, the chain, the tour). The
  words are in `tools/data/ui_strings.json` (`ui.tutorial.*`).
- **Runtime.**
  - The Tutorial authority keeps the progress (`tutorial_step`, `tutorial_done`, `tutorial_replay`, `tutorial_goal`).
  - `TutorialRules` holds the rules and `TutorialCoach` is the overlay (`scripts/ui/tutorial_coach.gd`).
  - Tours point at named anchors that the pages and the HUD give, never at node paths. A page's tap regions name
    themselves by action, its tabs and shared parts have names, and a page adds its own with `tour_mark`. The HUD names
    its controls by role (`HUD.tour_rect`).
- **Fixed on the way:** the tap that opened a page from the HUD also reached the new page. When the button stood
  outside the page's window (the Mail button), its release closed the page as it opened (`Page._gui_input`).
- **Screenshots** at the phone layout are in `docs/redesign/feedback/tutorials/`: the foundation path step by step,
  the Techniques page's tour and the Quests page's (`tools/dev/tutorial_capture.tscn`).
- **Tests.** A new suite, `tutorials`, registered in `tools/run_tests.sh`. It checks:
  - the data;
  - every tour and guide anchor on its page or the HUD;
  - the foundation path end to end through real taps;
  - that the coach waits in a fight, a scene and a talk;
  - the queue, Later, the "?" and Replay;
  - the save and reload, and a legacy save;
  - the place steps. They skip cleanly until the systems-as-places table lands.

## The technique pictures like the reference, the last side-view figures, the array's travel picker (decision 42)

The user asked again: "I want the skills icon to look like the attached image"
(`docs/redesign/feedback/skill_icon_reference.png`, the tree's cards as their phone showed them), and "there are places
we still use the old sprite character, we need to fix it". `docs/ui_style_guide.md` §8.4 holds the picture's style.

- **One technique picture** (`TechniquePicture`), the reference's look, for the tree's cards, the tree's reading, the
  HUD's technique buttons and the Techniques page's loadout bar. A square of deep starry ground in the art's element's
  ink; the character large (x2 on a card, x3 in the reading, whole at x1 in a button) in the art's pose, drawn in that one ink as a
  dark shape with light touches and a light rim; a few marks of the art's form round it (a palm's crescents, a ward's
  dome, a domain's ring, a pillar's springs, a seal's square, a snare's loop, a chorus's notes...); the frame; and a
  small rank badge (the art's mastery tier). The figure is the top-down one (`TopdownFigure`) for a top-down character:
  the pose a fight casts the art in with the art's own weapon family (a free-hand art's palm with no blade in hand), a
  weapon's blow on the frame it lands in profile, the bare hand's just after it lands three-quarters (the face shows),
  the hand seal toward the camera, and an art cast from a sitting whose form rests round the body seated in
  meditation. At a button's size it has its own pass (below). A locked art on the tree is in a grey ink. The side view's Avatar is drawn only for a classic side-view character.
  The cards lose the big emblem in their corner; the cooldown's sweep, the Qi-short strip and the lock stay.
- **No stutter.** No picture is built on the main thread any more (the side view's stills took 10-30 ms each there).
  Each picture is a cell of an atlas sheet (a SubViewport) the GPU draws: its ground, stars and marks are painted on a
  worker thread, and the main thread only makes two small textures and a canvas item, at most six a frame within
  1.5 ms; the figure and the ink are the GPU's (`technique_picture_ink.gdshader`). A picture shows in its place as it
  is painted, so the tree's kept tiles are not drawn again for it, and the page's redraw-on-change holds
  (`perf_tests`' `_techniques_redraws`). A picture's look (its pose, its outfit, its cell's key) is found once and
  remembered while that look is worn, so the HUD's buttons cost a lookup a frame (about 5 µs a button, from 36).
- **A button is a miniature of its card** (the HUD's 50 px buttons, the loadout bar's 42 px pictures; the cards and the
  reading are as above). The first pictures there were dark and muddy; a readability pass cropped them to head and
  shoulders at x2, and then "the skills icon don't fit right in the HUD buttons". Now the whole figure stands in the
  button at x1 (about 38 px tall), top to foot with a few pixels of margin and nothing cut by the frame, facing the
  camera on the frame before its blow lands (its face always shows), a little left of the middle; on the card's
  ground in the element's ink with a few faint stars, in the card's ink and rim; one bold mark of its form clear of the
  figure on the right. The rank badge is small and wholly inside the upper right corner, clear of the face; the
  cooldown's seconds, the Qi strip and the lock stay inside the frame. The HUD dims a Qi-short art to 0.72 (from 0.55)
  and a closed one to 0.45 (from 0.38), so the figure reads under the Qi strip and the lock.
- **Painting is quicker, and the Techniques check steadier.** A picture's ground, stars and marks are painted with the
  image's own fills, blends and blits instead of a script loop over its pixels: a card's in about 0.3 ms of a worker's
  time (from 2.5), a button's in 0.3 (from 0.5). A picture's rounded plates keep their style boxes by radius and colour, with
  no key written out each draw (a HUD button's picture costs about 25 µs a frame). `perf_tests`' decision 42 check ("with its preview casting
  the Techniques page is not drawn again and a frame costs about the world's alone") failed now and then on a quiet
  runner, though the pictures do no work while the preview casts (none drawn, no page or tile drawn again, none being
  painted): the runner's CPU runs half again slower or more for a second or so at a time, the same fixed piece of
  script work timed after each frame 1.7x slower in exactly those frames, and one such stretch in the casting window
  and none in the world's alone decided it (12.3 against 9.95 ms). Its windows now count the frames at the machine's
  own speed (`_median_frames`: a frame the fixed work shows slow is left out, unless a picture was being made then),
  and the line says how many were left out.
- **The companion's chip** on the HUD shows the top-down figure's head (the bare body's crown under the chip's top),
  where it showed a side-view head.
- **The sect's Transfer Array** asks where to on its own small travel picker (`array_page.gd`, `transfer_array`), not
  the dialogue page with an empty portrait: the array's name on the plaque, the room it stands in, its line, and one
  button a destination its token knows by the far room's name, with the array's rune ring (`WorldAuthority.array_view`;
  never an array the token has not keyed, of the other sect, or past the prototype's gate).
- **Screenshots** before and after at 1280x720 in `docs/redesign/feedback/pictures/`: the Water and Fire trees, the
  HUD at rest and in a fight, the loadout bar at x2 and the travel picker, and the reference beside the result
  (`tools/dev/picture_capture.tscn -- --tag=<before|after>`).
- **Tests.** `rules_tests`: the technique_pictures_suite (every picture of a top-down character is the top-down figure
  at its whole scale, the HUD's buttons, the loadout bar, the tree's cards and the reading, painted within a few frames;
  a button's the whole figure at x1 facing the camera, its head never cut; a companion's chip its head; a classic character's the side view's; the states; no main-thread piece past 4 ms nor
  a frame's past 8), the figures_suite (the cards), and the prototype suite's travel picker (only known arrays, by
  room name, none past the gate).

## The player and the NPCs drawn better (decision 42)

"I want the player and the NPCs to be drawn in higher quality." The study (`docs/redesign/feedback/character_quality.md`)
showed four options; the user chose **B**: the same 38 px figure, drawn better. It is now the game's character
pipeline, for every layer set, action, facing, hair colour and dye, so the villagers follow. The art bible's §13 has
the rules.

- **How the doll becomes pixels** (`tools/art/topdown/figure/raster.py`, `render.py`):
  - 4 x 4 samples a pixel; a pixel takes the material most of its samples hit (trim, pins and blades vote extra) and
    the mean light over them. Materials say how they resolve (`render.MATS`, a set's `Look(mats=...)`): `thin` parts
    are solid from a quarter covered; a new `line` rule keeps a part about a pixel wide (a shaft, a bow's limbs and
    string, a flute, a ripple, the brush's stroke of ink seen edge on) one unbroken pixel wide.
  - Seven-step ramps leaning toward the §14 sun and shadow; a warm rim, a cool bounce, contact shade under and beside
    nearer parts. Light (smears, rings, strings, ink) keeps its own colours.
  - Tinted outlines, a step lighter on the lit side; lighter inner lines over the body; half-alpha pixels at stair
    corners and softer convex tips.
  - Faces (`figure/body.py`): 2 x 3 eyes, a brow, a mouth, the nose's shade in three quarters, blush, lit nearly flat.
  - Hair (`kinds/hair.py`, `sets/hair.py` `TUNE`): broad locks, a broken sheen ring, a darker crown, locks wound round
    knots and down tails, and loose locks at the temples and brow so the cap no longer reads as a helmet.
  - Cloth (`kinds/folds.py`): folds from the belt to the hem, gathers over the belt, creases at the elbow and knee, a
    zigzag over the ankle wrap.
- **Fixed on the way**, found in the review:
  - A fringe, the forelocks or a band hat covered the eyes whenever the head nodded (meditation, a bow, a hurt): hair
    and band hats now leave the eyes' box clear in every pose, a row higher over shut eyes. Eyes hidden under hair or a
    hat, over every style, the headband and tied band, action and facing: 2,818 of 9,702 cases before, 21 now (all
    face down in a knock-down).
  - The brush's stroke of ink seen edge on (the leaping chop) broke up at 4 x 4: the `line` rule.
  - The guan's gold hid its jade crown; the heavy sabre's flat turned cream under a warm rim, and the tattered cape
    trailing in the run turned the colour of the paving: the guan's jade outvotes its gold, and bare steel (the sabre,
    the gauntlets, the greaves' plates) and capes keep a faint rim.
- **The build** (`build_character.py`): the frames are cast in one process per core (`--jobs N`; the same bytes for
  any N), and each item's sheet is coloured whole for each dye. A full pass takes about 2.5 minutes on four cores (11
  on one); `--check` builds twice and stays byte-identical.
- **Rebuilt:** all 18 sets, 168 sheets. The index and its catalogue signature did not change; the frames, rects,
  hidden entries and draw calls are the same. The sheets are imported lossless with no mipmaps, so their memory is
  their texels in RGBA8: 1.046 times as many (140.1 MB for all 168, from 134.0; the player's starting outfit 5.42 MB,
  from 5.20; the 26 sheets the study's nine people wear 19.9 MB, from 19.3).
- **In the game, before and after**, the same instants: the village square, Jade Gate Street, a fight with the jian
  frame by frame, and the story's gestures, in `docs/redesign/feedback/character_quality/rollout/`
  (`tools/dev/topdown_capture.tscn -- --quality --quality-tag=<before|after>`, paired by
  `tools/art/topdown/study_quality/rollout.py`). The review sheets in `docs/redesign/phase3/character/` are redrawn.
- **Tests:** `tools/run_tests.sh` green with no SCRIPT ERROR: 14 suites, 73,262 checks (`data_validation`'s layer
  contract and coverage gate among them), and the room lint, layouts and sect walks. `perf_tests` missed a frame
  budget in one run beside another agent's suite, and passed alone and in the final run.

## The prototype's feedback: the HUD at rest, the tree's pictures, one stall, talks that close (decision 42)

The user played the prototype APK (build 108) and asked for these (roadmap decision 42). This is the HUD's and the
pages' part; `docs/ui_style_guide.md` §7 and §9 ("As built, decision 42") hold the layout.

- **"I want the jumping button a bit bigger."** Jump is drawn 64 px across (from 52), hit r 36, in its place on ring 1.
  The techniques' squares stand at 180°, 207°, 243° and 270° so nothing of the cluster touches: the `hud_suite` checks
  every pair of controls, in a fight and at rest, the fan open or closed, right- and left-handed.
- **"I want the player skills to be visible when in rest and the normal attack button visible."**
  - The technique buttons no longer fold into beads out of a fight; they and Attack stay out at rest.
  - Attack keeps the weapon's glyph whatever is in reach. What the world offers (Talk, Gather, Open, Enter, Climb) has
    its own button on ring 2 above the techniques, at rest as in a fight, its verb and target under it. The earlier fix
    (a resource took the button mid-fight) now holds everywhere: `HUD.attack_first` is simply "the character may
    attack". The harvest's hold runs round the context's button and its tap lands there.
  - Nothing shows before it is unlocked: `tutorial_order`'s new invariant 15 walks a new player through the tutorial
    and checks at every step that Attack, the techniques, Jump and Dodge are drawn exactly as they are revealed.
- **"I want the skills icon to look like the attached image."** The HUD's technique buttons and the Techniques page's
  loadout bar (Ring I and II) draw each art as the tree's node picture (`TechniquePicture`): the character in the art's
  pose from the same source as the tree's cards (the Avatar's still of `TechniquePreview.pose_of`, an art pixel a
  screen pixel) on its element's ground, in the tree's bright jade frame, its emblem as a round seal in the corner. At
  a button's size the figure is framed from the head down with a light rim, so it reads on the dark ground. Its states:
  the cooldown's ink sweep with a pale gold hand and the seconds; short of Qi, the picture dimmed and a Qi strip along
  its foot; closed by the weapon in hand, a slate frame, dim, and a lock.
- **"When in trading I want the shop and player bag background to be the same."** The shop's bag side is the stall's
  own timber wall under the same awning, where it was a patch of the gourd's night sky (decision 24).
- **"Conversation with NPC should close after getting / completing the quest."** Taking or handing in a quest closes
  the talk even when the same person has another quest to give or take back (M17 went on to it); talking again offers
  it, and a scene the quest starts plays once the talk is closed. A talk that itself finishes or gives a quest (a talk
  objective, a quest done by talking) is marked `quest_moved` and closes at its last line's tap when only a service or
  Farewell is left to choose.
- **Screenshots** before and after, at 1280x720 under the real HUD: at rest, in a fight, the Techniques page and its
  loadout bar, Old Ma's shop, and Aunt Ping's offer then the screen once it is taken, in `docs/redesign/feedback/hud/`
  (`tools/dev/hud_capture.tscn -- --tag=<before|after>`).
- **Tests.** `rules_tests`: the hud_suite (the layout, Jump's size, no two controls touching, the techniques and Attack
  at rest, the context's own button), the attack_first_suite (Attack attacks beside a herb at rest and in a fight, the
  gather and its tap on the context's button), a technique_pictures_suite (the HUD and the loadout bar draw the tree's
  pictures, never the round emblem, and their cooldown, Qi and lock states) and the shop's one background;
  `story_scenes` 6 (talks close after taking and handing in in the top-down game, with a second quest waiting, the
  scene after, and a talk that finishes a quest); `prologue_run._choose_on_page` (so every accept and hand-in on the
  page in `tutorial_order` and `valley_run`) now asks that the talk closed.
## The Techniques tree without its lag, and the top-down character on every page (decision 42)

Two notes from the prototype APK (build 108): "The Techniques tree feels a bit laggy", and "there are places we still
use the old sprite character".

- **Why the tree lagged.** The whole page was drawn again every frame, whatever changed: the chart and every card in
  view, the chooser, the reading, the dock and thirteen seals, about 5-6.5 ms of work a frame here (four to five times
  that on a phone). The live preview animating, or a finger resting, was enough to redraw it all. On top of that came
  stalls: a card's picture was composed from the side view's sheets (26 ms each, one a frame), choosing an art loaded
  the side view's pose sheets for the reading and the preview (60-70 ms), and a new tab laid its tree out in one frame.
- **What the page does now** (`techniques_page.gd`):
  - **It is drawn only when something on it changes**: a tap, an event, its toast, art coming in from a loading thread
    (`Page.redraw_on_change`, a new mode every page may take; the others still draw every frame).
  - **The chart is drawn apart from the page, in tiles.** Each tile is half a family's column, two rings deep, drawn
    once in the chart's own space in three layers (ground and routes, passages and gates, cards) and kept. A drag or a
    glide only moves the sheets that hold them. Tiles are drawn as they come near the view, four a frame at most, and
    again only when what they show changes: a node chosen or learned, an emblem composed.
  - The cards' names and tags, the ring numerals and the plaque of the family in view are small layers of their own.
    They are drawn again only when what they write changes. A word is still written only while it is wholly inside the
    chart. The chooser lights the family in view once the view comes to rest.
  - **Idle frames work ahead**: the other trees' shapes are laid out a family at a time (`ShapeJob`), and the nodes'
    states are asked of the authority nearest the view first.
  - The preview's caster and foes are drawn again only when their frame changes. The foe sheet's index is read on a
    worker thread, and its texture on a loading thread.
- **Measured** with the page's own profile, a top-down character on the Water tree. Two runs before and two after,
  alternating, on the same machine. Headless frames never go under 6.9 ms here (the engine's idle sleep); the world
  alone is 6.9 ms.

  | ms a frame (mean / p95, or max) | before | after |
  |---|---|---|
  | the preview casting | 11.3-11.7 / 12.8-15.0 | 6.9-7.1 / 7.0-9.4 |
  | a finger dragging the chart | 11.7-12.0 / 15.1-15.5, max 36-38 | 6.9-7.0 / 8.1-8.6, max 12 |
  | the wheel's glide | 10.7-11.9 | 6.9 |
  | nothing chosen | 10.1-10.2 | 6.9 |
  | the frames after the page opens | 14.7-15.5, max 53-63 | 7.4-7.7, max 23-30 |
  | the worst frame after choosing an art | 68-70 | 24-25 |
  | a tab's first frame | 26.5-29.0, max 41-55 | 20.0-20.5, max 25-27 |

  The page's own work a frame, timed inside it, went from 6.5 ms to 0.2 ms with the preview casting, and from 5.8 ms
  to about 1 ms dragging.
- **A bug on the way:** a ring's passage that cuts Qi cost read "Cuts the Qi cost of 2 Water arts by …" with a string
  error: the words' arguments were out of order.
- **The top-down character on every page.** The top-down figure (`TopdownFigure`, the layer sets under
  `art/topdown/character/`) is the game's character. A new `TopdownDoll` draws it on a page: one action in one facing,
  at a whole scale, nearest neighbour. Its sheets load on threads, it redraws only when its frame changes, and it can be
  cropped. A classic side-view character (Settings' fallback) keeps the side view everywhere. Places changed:
  - **The Techniques page:**
    - the preview under the chooser (the side-view swordsman of the reference image). The character plays the art's
      top-down pose, the one a fight casts it in (`TechniquePreview.top_pose`), toward the top-down world's mud-shell
      crabs, at 3 px an art px (`moments.json` `technique_preview.top_foe`, `top_scale`);
    - the reading's picture (the pose on its blow's frame, at 3);
    - the cards' pictures: the top-down figure doing the art on the element's ground, with the art's emblem in the
      corner, as the side view's still stood (not composed, so no card waits).
  - **The Character page:** the figure (6 px an art px), and the friends' faces in the chips beside it.
  - **The Bag:** the figure on its island (6).
  - **The dialogue strip:** the speaker's portrait (4), and so the Gift's too.
  - **The Companions:** each friend in their moon gate (4).
  - **A shop:** the merchant behind the counter (6).
  - **The Cultivation stair:** the figure seated in meditation (2), where the breakthrough's climb plays.
  - **The Notice Board:** the wanted poster's likeness (3).
  - **The sect hall** (Training Sect), **the Characters roster** and **the Roll-Call:** `SectKit.figure` draws each
    character as their own game draws them.
  - **The selection screen:** a top-down character's card at a whole 4 (was 3.2).
  - Checked and unchanged: the Codex (its beasts are creature sheets), Relations, the Revival lamp and the
    Breakthrough gate draw no figure.
  - Not mine to change: the HUD's companion chip still draws a side-view head (`hud.gd` `_draw_face`).
- **Tests:**
  - `perf_tests` `_techniques_redraws`: with a top-down character and its preview casting, the page and its tiles
    are not drawn again, and a frame costs within 1.5 ms of the world's alone. A drag across the biggest tree draws the
    page at most three times, at most fifteen tile layers a frame, and a frame within 2 ms of the world's alone. Medians.
    Before this change the page cost about 4 ms over the world's alone with its preview casting (the medians above), so
    the first would fail.
  - `rules_tests` `figures_suite`: every page above draws the top-down figure, at a whole scale, for a top-down
    character, and no side-view avatar; a classic character keeps the side view.
- Screenshots at 1280×720, before and after, are in `docs/redesign/feedback/sprites/`.
## Less walking in the sect stretch: transfer arrays, errands that come to you, something on the way (decision 42)

The user played the prototype APK (build 108): "There should be less monotone walking between places in the sect
quest." The full measurement, the before and after trip tables, and the screenshots are in
`docs/redesign/feedback/sect_walking.md`.

- **Measured first.** `tools/data/sect_walks.py` walks every trip of the sect stretch the way the tracker's go button
  does, at the sprint pace (216 a second, the new default). Build 108 asked for 18–20 minutes of plain walking per
  sect, twelve trips of them over 35 seconds and up to two minutes. It had five back-and-forths: up the mentor's peak and
  back down to the marsh twice, Artisan Row to the marsh and back, and the lessons up the peak and back. The Jade
  Sect's East Terrace and Herb Terraces were each crossed eleven times with nothing in them, and Stoneford and the
  Willow Path ten times. Now it is about three minutes, no trip is over 20 seconds, and there is no back-and-forth.
- **The sect's transfer arrays.** Each sect has one on its gate's plaza and one on its mentor's peak, and both keep one
  at the Marsh Edge's watch post.
  - They open with the Weapon Hall (`transfer_array`). The steward shows the gate's as Strange Tracks begins (the scene
    `array_lesson_*`). The lesson keys the token to the gate's array and the watch post's; the mentor keys his peak's
    when he first receives you (`mentor_peak_*`).
  - Stand in the ring and tap Travel. The array asks where to, among the arrays the token knows, and you come out in a
    column of the sect's light. It is free. The teleport stones keep their shards and Qi Kindling 3.
  - The route, the minimap's mark, the tracker's go button and auto-path all take an array. It is a way in
    `WorldRules.ways_out`, open to the sect's own disciple once the token knows both ends (`WorldAuthority.array_open`).
    Auto-path walks onto the array and steps through (`auto_path_board`). No array leads past the end-of-prototype gate.
  - New prop art: `transfer_array`, `_cloud` and `_watch`. Each is dark until the token opens it, then its runes glow
    and turn in the sect's colour.
- **The errands come to the player.**
  - Strange Tracks is done at the third grey patch. The River Token hums (`grey_rises`) and The Humming Token begins on
    the spot.
  - The mentor comes down to the marsh in a column of light for the hand-in (`mentor_descends_*`). He stands there
    only while the quest waits for him: two new requirement kinds, `quest_ready` and `quest_not_ready`.
  - Mei Qing tends the watch post's two watchers from the Weapon Hall's end until her errand is done. The errand is
    taken, gathered and handed in there.
  - A collect step's places now include the rooms whose foes drop the item, so her moss leads to the frogs beside her,
    not a bundle in Granny Liu's hut.
  - The Outer Trial is handed in to the training hall's master in the yard where it is won.
- **Something on the way.** The first walk up through the grounds (Grey at the Edges) has a live scene in each room,
  and the player keeps the controls:
  - the hall master offers a round at the practice post, and the Cloud master adds the plum-blossom poles;
  - the formation elder and the physician are overheard on the grey and on a drowned shrine at Deepwater Bend;
  - the gardener asks you to carry lotus root tea up to the elder. This is a new side quest, Tea for the Elder, handed
    in where you are going anyway.
  - The Marsh Edge's watch post has its two watchers, Watcher Bo and Watcher Su, one of them sitting with his arm gone
    grey.
- **The rule.** `tools/run_tests.sh` now runs `sect_walks.py --check`. No step of the stretch may ask for a plain walk
  over 35 s with nothing on the way, nor a walk out and straight back. Every stop is checked against the built data.
- **Tests.**
  - `tutorial_order`: Strange Tracks now ends at the marsh, with no report up the peak.
  - `topdown_tutorial` plays both sects to the gate by the new route:
    - the lesson, and the gate's array to the marsh;
    - the hand-in to the mentor who came down, and Mei Qing's Errand at the post;
    - the Jade disciple's walk up now too;
    - the peak's array to The First Current;
    - auto-path onto an array and back.
  - `valley_run` follows the new places.
  - The tracker's Next after The Humming Token is Mei Qing's Errand at the Marsh Edge, where she now is, not Artisan
    Row.
## The Hollow Night as a set piece, and its foes can be killed (decision 42)

The QA note: "The Hollow Night quest feels boring with no action, also there is a bug that I can't kill the monsters".

- **The bug.** Neither of the night's foes could be killed on the height grid, by a basic attack or a technique.
  - **The grey minnows** hovered where the side view puts its flyers: 40-56 px over their feet, which is inside the
    side view's melee window (+60, S43). On the grid a blow lands only between feet inside the hit band
    (`movement.json` `topdown.combat.hit_band`, ±12), so every blow passed under them, and their bites passed over
    the player. A flyer on the grid now skims under the band's top over the floor it hunts on, with a bob and a swoop
    as it strikes (`EnemyAuthority._hover`). Flyers chase in a straight line on the grid, not along the ground's paths
    (`TopdownBrain.chase`).
  - **The Hollowed Eel** was invulnerable by design (`_eel`: "cannot be hurt"), and the quest was a 60 s timer.
- **The night is a fight in beats**, two to four minutes long (about 3 minutes on the play clock), deterministic, and
  fair at the story's Level and gear (Level 0, about 80 HP, the crab's short blade or Guo's gauntlets, three teas).
  1. **The river boils.** A cut with the title "That Night": a storm, the river rings, Dou's cry among the minnows,
     Granny's call, Aunt Ping at her door with the lamp lit. The hand-off: "Strike the grey minnows: tap Attack".
  2. **Get them in.** Two minnows are about each villager, and one more leaps up the bank every 6 s (two at most).
     Each villager sent in runs for Ping's door in a live scene (Granny gives you a healing pill). The minnows are
     one-blow foes that dart after a short tell, so a combo swung through a school fells several. Ping's lamplight is
     a refuge: within 150 px of her door the minnows let you be (`sanctuary`).
  3. **The grey spreads.** Once all three are in, schools pour up the lane from both ends for 24 s and hunt you
     (`hunt`). Ping: "Too many of them? Come into my lamplight."
  4. **The eel rises**, 14 s after the villagers are in. It gets the boss card ("Hollowed Eel · Level 2") and the boss
     bar with its phase mark. It glides in the river, out of reach and unhurt. It rears up (the tell, 1.1 s) and lunges
     onto the bank where you stood, then lies stranded there for 2.4 s, open to every blow, before it slides back.
     The hand-off: "It rears before it lunges: step aside, then strike it on the bank".
  5. **The climax.** Below half its HP it dives, and Lu's boat comes up the river. From then on every lunge is the
     great lunge (a 1.8 s tell and a heavier blow). As the first one lands, Lu's palm pins it to the bank for 5.5 s
     (3.5 s after that). The hand-off: "Strike the pinned eel". It is the palm he teaches on the boat.
  6. **The grey lifts.** Lu: "You held the bank, child. Not one of them lost. ... The palm you saw? I'll teach it to
     you. Come, to my boat." The night's way on (`leave`) takes you to Lu's boat.

  If you hold out until the 200 s timer ends, the night is also won (`timeout_wins`: Lu comes), but the eel's fang is
  not earned. If you fall, you wake at Ping's door and the night begins again (`refuge`).
- **Rewards.**
  - The eel drops a **Hollowed Eel Fang** the first time (a rare find with its own icon, worth 80 taels to a trader),
    a river pearl, about 80 taels and 15 Fame (a story boss felled).
  - Holding the night earns the title **Guardian of Lotus Ferry** (+2% Hollow ward).
  - Each minnow has a 25% chance of a Tiny Hollow Shard.
  - An untouched night adds two Herbal Teas.
  - Lu's palm is the hint of the technique he teaches next (Flowing Palm).
  - Evening on the River heals you fully before the night.
  - The low soul core's only source was the old Level-10 eel, so Broker Mu now sells it (under the counter, to the
    shadowed).
- **The room event** (`WorldAuthority`) gains:
  - `requires`, `for_s`, `delay_s` and `latest_s` on waves and timed spawns (a part that waits on the story), and
    `hunt` on waves;
  - `timeout_wins`;
  - `leave` (after a win: the loot swept up, then effects, such as the teleport to Lu's boat);
  - a room's `refuge`, and an object's `sanctuary` radius (`EnemyBrain.in_sanctuary`).

  The top-down layout gives every wave point and timed spawn its cell. `room_event_completed` joins the event contract.
- **Staged scenes** (`tools/data/scenes.py`): the night has 8 scenes where it had one: `hollow_rises`, `night_ma_goes`,
  `night_granny_goes`, `night_dou_runs`, `grey_spreads`, `eel_rises`, `lu_arrives` and `grey_lifts`. The eel's scene
  waits for the lane's (the `grey_spread` flag), so the beats keep their order in the game's own time.
- **Tests.**
  - **`hollow_night`** (new, in `tools/run_tests.sh`):
    - each night foe killed by a basic attack and by a technique, on the grid, through the real combat path;
    - the night played through on a headless director: its length, its beats in order, all 8 scenes, HP never under
      a quarter, the rewards, and the boat's meditation after it;
    - the lamplight refuge and the timeout win;
    - a fall and the restart at the door.
  - **`balance_sim`** "story night": the eel at the story's Level, won with HP to spare. The figures are the lowest
    HP over four seeds:
    - the short blade, played carefully: 61%, won in at most 64 s (at least 50% required);
    - Guo's Flawed gauntlets alone: 18%, won in at most 114 s (at least 10%);
    - the short blade, trading blows: 71% (at least 35%).
  - **`prologue_run`** fights the night through: it reads the eel's tell and strikes it in its windows.
  - **`topdown_tutorial`** invariant 9 checks the event's waves and timed spawns too.
  - **`tutorial_order`**: the first hour's longest gap is 2.6 min, the night's (from Granny's healing pill to the eel's fall).
- **Screenshots** (`tools/dev/topdown_capture.tscn -- --night`, in `docs/redesign/feedback/hollow_night/`): 01-17,
  from the storm to Lu's boat.

## The prototype feedback: animation canceling, sprint by default, auto-path round props, meditation's pose (decision 42)

From the user's play of the prototype APK (build 108; roadmap decision 42). Shots:
`docs/redesign/feedback/combat/`.

- **Animation canceling: basic attack, technique, basic attack in one flow.** The Alabaster Dawn and action-RPG weave:
  - **A technique cuts a basic step's recovery**, and **a basic attack cuts a technique's recovery**, the frame the
    blow's active frames end. A step's hit lands one smear frame into its active window, and a technique's hit at the
    end of its wind-up, so a cut never drops a hit and never lands one early.
  - **A press that comes early waits** (0.4 s) and goes at the cut. That covers a light or middling step from its
    first frame (the fists' cut comes 0.28 s in, the jian's 0.36 s) and a technique's wind-up (0.4 s). A heavy sabre's
    first moments still commit.
  - **The combo carries through the technique:** basic 1, technique, basic 2. With the bare hands, basic, technique,
    basic begin within 0.67 s, not the 0.99 s that waiting out each takes.
  - **The figure takes each new action's pose from its first frame.**
  - The numbers are in `tools/data/combat_feel.py` (`WEAVE`). It runs on the grid only; the side view is unchanged.
- **The body sprints by default.** The stick pushed runs at 216 units a second (6.75 tiles a second, 40% over the
  walk), playing the run the character sheets draw. A light touch (the stick at 0.6 or under) is still the careful
  walk at 69, for a step to a ledge or a jump onto a top one tile deep. Keyboard: WASD sprints, Alt walks.
  - **The world keeps its measure.** In the air the body carries no more than the 154 of the walk the world was
    measured at:
    - a running jump from a sprint reaches 73 units, as the walk's did (one tile's gap, not three);
    - a step off a ledge lands 31 units past it, as before;
    - the dash's long jump keeps its 142.
  - Full speed comes in 0.08 s and a stop takes 0.07 s over 6 units. The camera leads a sprint by 22 art px (15 at the
    walk). The rooms' reach checks, `room_lint` and the tutorial walks hold.
- **Auto-path and auto-hunt go round props, at the sprint** (`TopdownRoute`, which the Autopilot steers by):
  - **Round what blocks:** tree trunks, rocks, fences, hedges, crates, lanterns, buildings' walls and the water's bank.
  - **The way:** find_path's own rules on a binary heap, with no search limit, keeping to open lanes.
  - **The line:** it aims at the farthest cell of the way that a straight line reaches with the foot box kept 6 units
    clear, so the grid's steps become straight runs and corners are rounded with room to spare.
  - **No getting stuck:** a push that leaves it hugging a wall, or a diagonal onto a stair's side, goes by a waypoint.
    A drop lying in a trunk's cell is picked up from the spot beside it; it used to push into the trunk forever.
  - Over a tour of all 29 rooms (154 legs, 7 minutes of running), every leg arrives. It never touches a prop, never
    stalls and never turns back and forth. The old steering stalled twice against a stair's side and brushed a
    bamboo.
- **Fixed: after cultivating, walking stayed in the cultivation pose.** Moving now ends meditation at once, and the
  figure runs, or walks at a light touch. A jump rises from the seat too. The Agility gate that lets a body cultivate
  on the move still does, and still walks.

## The prototype's polish: fair first fights, rewards that are new, the top-down creator (decision 41)

The last pass before the prototype's APK, on what the QA playthrough (`docs/redesign/prototype_qa.md`) left for
decisions. The research's aim (`docs/research/player_motivation.md`): the start should feel rewarding, not forced.

- **A new player following the story is not downed again and again.**
  - **The herd's elite boarlet** (The Willow Path's last fight) is met at the Level the story brings the player there,
    Level 1 (Bone Forging 1), not the herd's top Level 2: 304 HP and 12 attack, from 425 and 16.2. It keeps apart at
    Willow Path West's west meadow by the willow, where the herd's walk west ends, instead of charging into the herd's
    fights from the middle of it. It downed the QA player one to four times a run; see the QA document for the runs
    after.
  - **An early surprise waits for the room's story fight.** A common foe of the Reed Shallows and Willow Path West
    comes as an elite one spawn in twenty-five only once Crab Trouble, and The Willow Path, are done (`elite_after`):
    a Level-2 surprise elite in The Willow Path's herd downed the QA player twice in one run, where the story's own
    elite is met alone.
  - **The Marsh Edge fits the Level the story sends there.** Strange Tracks sends a Bone Forging 3 (Level 3) disciple
    out of the Weapon Hall; the marsh's band is Level 3-5, from 4-6: its reed frogs 3-5, its leeches 4-5, and its elite
    frog Level 5 (874 HP, 30.5 attack, from 1053 and 36). The elite frog keeps to the lookout, a level up that it cannot
    see the path from, guarding the moss there: an optional fight, not one the path walks into.
  - **The Humming Token's grey boarlets are Level 3-4**, from the earlier fix's 4-5: the story's Level and one over.
    Three at a time among the marsh's frogs and leeches, two Level-5 ones charging together took a Level-3 player to
    9% of its HP in `balance_sim`'s room fight (51% now), and the QA player fell there.
  - **Shen Lian's spar is a lesson.** He spars at the player's own Level (`spar_level: "match"`, as the sparring
    disciples do; his Level-4 double beat the QA's Level-2 player): at Level 2, 193 HP and 6.9 attack, from 322 and
    10.8. His fist winds up for 0.6 s, as long as Old Snapper's claw, a tell a thumb can read. He says what the spar
    teaches: the offer ("every fighter tells you when the blow is coming"), a toast as it starts ("Watch my shoulder.
    When it drops, step aside, then hit back!"), and another when it ends, won or lost (`spar_lines`,
    `HUD.spar_line`). A toast's second line too long for one row wraps onto a second now (`HUD.toast_sub_rows`): the
    lesson was cut at "When it…".
- **One Shen Lian on the screen.** Asked for a spar, the person is the one who fights: the partner steps out from where
  they stand, in their own clothes on the grid, and their villager figure is hidden while the spar and its bow last
  (`QuestAuthority.start_spar`'s `npc`, `WorldAuthority.in_spar`, `TopdownPlaces.stand_in`).
- **Rewards that are new.** No early reward is a second of what the player has:
  - Crab Trouble pays 50 taels, the Plain Straw Hat and a **Boar Bone Broth** (+120 body XP: the QA player's body level
    went from 1 to 3 for good), not Straw Sandals, which the starting kit wears. The skip-the-Prologue start follows.
  - Old Ma's storeroom loft holds **two Riverfish Soups** (+5% max HP for 20 minutes), not a third pair of sandals.
  - The Weapon Hall's rack holds each sect's own weapon, the Jade Sect's jian and the Cloud Sect's staff, and the spear,
    not a second pair of Uncle Guo's gauntlets; each is handed out only to one who lacks it (`unless_owned` on a
    `grant_item` effect).
  - Eyes for Qi pays two Herbal Teas in place of a herb sickle: herb gathering's unlock hands out the sickle already.
- **The creator shows the top-down character.** A new game is top-down, so the preview is the top-down figure
  (`TopdownFigure`, the layer sets under `art/topdown/character/`) walking in place as it turns through the eight
  facings, with a rest facing the camera each round; a tap on it turns it by hand, and it follows every change of the
  look in the starting garments' dyes (`ShellScreens.TopdownPreview`). The side view's avatar shows only with Settings'
  classic side view on. Character selection draws a top-down character's card in the top-down style too.
- **Smaller fixes from the QA document:**
  - **A locked resource node never takes the context button**: a herb before herb gathering, a swarm before the net, a
    trail before snaring, a Temper drum before its body level stay in the world, and are offered once open
    (`WorldAuthority.RESOURCE_NODES`, `resource_node`).
  - **A plate at the screen's side edge is pulled in whole** ("…Crab" at the Reed Shallows' left edge), every row it
    tries with it; one wider than the screen is left (`WorldLabels._pull_in`).
  - **The gate's line shows once, near the gate, never under the HUD.** It was on the screen three times at once: the
    log, the way's plate, and a line floating over the player, partly under the purse. Now a shut way walked into
    lights its own plate at the way (`PortalView.touch`); nothing floats over the player, and the log keeps quiet
    where a plate says it (`HUD._way_plate`).
  - **Log lines wrap** onto a second, indented row instead of ending in "…"; the log keeps to six rows
    (`HUD.log_rows`).
  - **Inside an instanced room a step is done in** (the Siege of Two Sects, its way out held until it is won), the
    step leads there, not back to the street its rite was begun in (`QuestAuthority.objective_room`). `valley_run` met
    it when a sect mission was finished mid-siege.
- **Tests:**
  - `balance_sim` adds the story's rooms (no field the story sends the player into is over the Level it brings them
    there at) and the story's duels: each fight of the prototype's story fought through the real Combat on the room's
    own grid, at the story's Level and gear, at a thumb's pace (the herd's elite boarlet trading blows with the first
    weapon, and with Guo's gauntlets by a careful player; the Entry Trial's puppet; Shen Lian's spar; the Marsh Edge's
    frogs, leeches and grey boarlets trading blows; its elite frog by a careful player), and the story's room fights:
    the Willow Path's herd and The Humming Token's grey boarlets killed in their rooms as they stand, the room's other
    foes joining, won every time with HP never under 40% (66% and 51%).
  - `data_validation` adds the early rewards: no piece of gear or tool the early story hands out (the starting kit,
    the quests, their unlocks, the pickups in the rooms on the grid) is given twice, and the Weapon Hall's rack.
  - `rules_tests` `prototype_suite` adds the creator's top-down preview (fully drawn, all eight facings, the rest,
    the dyes, following the look, a tap) and the classic side view's avatar, the selection cards, locked nodes, Shen
    Lian's spar (hidden in the square, stepping out where he stood, his clothes, his Level, his tell, his lines, back
    after), a toast's long second line, plates pulled in at the edge, the log's wrap, the gate's line (no log line where
    a plate says it, the plate lit, nothing floating), and a step in an instanced room; its P7 suite, an early
    surprise waiting for the room's story fight.
  - `prologue_run` checks Crab Trouble's pay; `tutorial_order` and `topdown_tutorial` drink the broth, check the rack
    (no second gauntlets), and hold that no locked resource node took the context button in a fight. `valley_run`
    waits out a stun carried into a room before it meditates (the Quarry Rim's falling rocks, the travel between not
    played out).
- **Tools:** the QA player plays with `--no-assist` (every fight on its own HP; its log lists every fall with the
  damage by foe, the foes about and the teas left, and every spar), drinks the broth, looks in the Bag at the Weapon
  Hall, follows Shen Lian's lesson in his spar, hits the Trial Puppet while it strikes (it guards otherwise: stepping
  out of its wind-up, the QA player never landed a blow in 90 s), says why a fight ran out of time, and shoots the
  herd's elite's fight.

## The prototype: top-down by default, the end-of-prototype gate, and a QA playthrough (decision 41)

- **New games start in the top-down world.** The character creator makes a top-down character. Settings → Controls →
  "Top-down world (new games)" is replaced by **"Classic side view (new games)"**, off by default: the fallback that
  makes the next new character side-view. Characters already made keep their own view, and a create intent that names
  no view (the test walks, the debug characters) still makes a side-view one (`AccountAuthority.new_game_view`). The
  title's hidden five-tap entry, `--topdown-tutorial` and `--topdown-proto` stay as dev tools; `--topdown` now only
  makes a preview's character top-down.
- **The end-of-prototype gate.** In a top-down character's game every way from a room on the height grid into a room
  with no top-down layout yet is closed (`WorldAuthority.prototype_gate`): the Marsh Edge's road east to the Grey
  Pools, the Trial Tower's door, the Caravan Road, the Quarry Road, the County Hall, Elder Gu's warehouse, the Beast
  Grove, the sects' libraries, Alchemy Hall, retreats and cave abodes, and the Cloud Herb Terraces, 18 in all.
  - A road barrier stands in each (`TopdownGate`, drawn in the room's pixel style: timber posts with red-lacquered
    caps, rails and a cross-brace, a red cord of paper talismans and a notice board).
  - Its plate, a touch and the context button say "The road beyond is still being drawn."
  - No route, direction mark, auto-path, teleport (a stone another character found) or tower climb goes through it.
    A side-view character's game is unchanged, and a way out of a side-view room stays open.
- **The tracker never points past the gate.**
  - A quest whose step lies past it keeps its steps, leads nowhere, and says the road is still being drawn.
  - Hunting grounds are rooms on the grid.
  - When the story's next quest is played past it (after The First Current, Bandits on the Road on the Caravan Road)
    the lessons on offer inside the prototype lead first. Then the tracker's first entry, and the Quests page's Next
    slip, is the prototype's end: **"The Tale Rests Here · The road beyond is still being drawn · The prototype ends
    here, for now."** It has no mark and no Go.
- **Fixes from the QA playthrough** (`docs/redesign/prototype_qa.md`, both sects from the title on a 1280×720 screen
  with the HUD's touch controls):
  - **A clean field.** Every foe carried a large "Lv 1 · R1 Mudshell Crab" plate, and a pack's plates overlapped. In
    the top-down view a foe's full plate now shows only for the target the thumb has (the soft lock, or the foe an aim
    snaps to), a foe in a fight with the player and three seconds after, and elites and bosses; every other foe keeps
    a compact HP bar once hurt or aggroed, and a foe well above the player's Level keeps its danger mark. Plates that
    show never touch: a crowd the label rows cannot clear takes further rows, then half a box aside
    (`WorldLabels.ROWS_MORE`). Each label sits on the top-down figure's head (the foe sheet's new `top`), not at the
    side view's height, so the hovering eel's plate no longer floats high above it.
  - **The hollowed eel turns.** It glides by a velocity and lunges along an aim at its target on the grid, so its
    figure faces where it goes instead of keeping the row it rose in.
  - **World news waits for the player.** A late-game calendar event ("The Drowned Shrine Surfaces · Abbot's Sanctum")
    was toasted over a brand-new player's village and the Hollow Night's timer. World and calendar notices (event
    toasts and reminders, the season, the Heaven Ranking's shifts, a treasure born elsewhere) now wait for the
    calendar's unlock, never play during a staged scene, and name only places the player has been, never one past the
    gate (`HUD.world_news`).
  - **Mei Qing's willow moss led to herbs the player cannot pick yet** (herb gathering opens at Bone Forging 4). A
    collect step's places are now those where the item can be had now: nodes and pickups the character may take, and
    with none, the rooms whose foes drop it (the Marsh Edge's reed frogs).
  - **The creator's preview wears the starting garments' own dyes**, so the robe chosen is the robe worn (it showed
    a teal tunic and the game an earth-brown one).
  - **No log spam on closing a page.** A page or shell screen closed by a tap was taken out of the tree while the tap
    was still being handled ("Condition !is_inside_tree()" at every close); it is now hidden and freed at the frame's
    end.
  - **No plate over the player.** A villager's plate under their feet (Uncle Guo's at his stump) or a foe's over its
    head just in front lay over the player's body; the body is now kept clear as the HUD's controls are.
  - **The player is seen behind the training dummy.** A thing as tall as a body (the dummy, a stump) standing in front
    hid the player entirely; it now counts for the silhouette, so the body shows through it.
  - **A crowd's plates laid aside are drawn aside.** The layout's half-box moves were computed but every view drew its
    plate where it stood; the views now draw at the offset's x as well as its row.
  - **No label under the HUD.** A way's plate at the screen's edge stayed under the player panel (the Reed Shallows'
    way to the village) or the minimap (Willow Path West's way east read "Willow"): the layout now also tries just
    clear of the control, beside it. The purse and the status row under the player panel are among the HUD's rects
    the labels keep off, and so is a door's chevron (it lay over Granny Liu's plate). The QA player reports any label left under the HUD in every shot; the
    last runs had none.
  - **Walking into the gate.** Its line showed five times over in the log, and the way's plate ran off the right edge
    of the screen: a way's refusal now shows once in the log (kept fresh while it repeats), a way's plate stays
    wholly inside the room (`PortalView.label_span`), and a floating line stays whole on the screen
    (`FxLayer.on_screen`).
  - **The tracker asks for the breakthrough.** At a bottleneck one breakthrough short of the Level the story waits on,
    its Next entry said "Hunt at Willow Path West" while the bar said "breakthrough ready"; it now says "Bottleneck:
    tap Cultivate to break through", with no hunt and no Go.
  - **A staged scene's prompt stays on the screen** ("Punch the stump: tap Attack" ran off the right edge over a
    person near it), and **a speech balloon keeps clear of the HUD** (Granny Liu's line sat over the HP panel): aside,
    or on the first clear row below.
  - **The equip prompt names the early gear whole** ("Training Short Bl…"): a long name steps its size down to fit.
  - **The tea's heal is seen.** Granny's Remedy's drink step handed back the controls under her balloon, so the heal's
    "+14 HP" and the HP bar filling were hidden by the scene; the hand-off now waits a breath, live, before she speaks.
  - **A moment's band holds the top of the screen alone.** As the Hollow Night began, the room's name, the night's
    timer plate and the "The Hollow Night" band were drawn over one another; while a band plays in the top centre the
    room's name keeps its time and the event's plate waits under it (`MomentView.band_on_top`).
- **Tests:**
  - `rules_tests` adds `prototype_suite`: the creator's default and the fallback, side-view saves, every gated way
    (its state, a touch, the context button, no route), no teleport, auto-path or tower climb past it, the view's
    barriers, hunting grounds on the grid, a quest past the gate, the tracker's end and a side-view character's Next
    at the same point, a lesson before the end, the Quests page's slip, world news, the equip prompt's names, a
    moment's band over the top stack, a way's plate under the minimap, the purse and the status row, the gate's line
    once in the log and whole on the screen, and the Next entry at a bottleneck.
  - `topdown_suite` adds the clean field (plates, HP bars, the danger mark, a crowd's plates not touching, labels on
    the figure's head, no plate over the body, a plate laid aside keeping its box, a plate off a door's chevron, a
    way's long plate inside the room), the eel's turn, and the player seen behind the dummy.
  - `story_scenes` adds the prompt kept on the screen, the balloon kept clear of the HUD, and the drink step's live
    hand-off.
  - `topdown_tutorial` plays on past The Humming Token: Mei Qing's Errand (moss from frogs, never locked herbs), Grey
    at the Edges, The First Current, the lessons inside the prototype, and the prototype's end; the Marsh Edge's gate
    walked into; the Trial Tower's door gated, and auto-path through the Cloud Sect's road instead.
  - `prologue_run`'s route search and story guidance, and `tutorial_order`'s "leads to next", know the gate.
- **Found and left** (in the QA document with the reasons): the herd's elite boarlet and the Marsh Edge's frogs and
  hollowed boarlets outclass the player the story sends there; Crab Trouble pays Straw Sandals the start already
  wears; Shen Lian stays in the square while his spar double fights; locked nodes offer their button with a line.
- **Tools:** `tools/dev/prototype_qa.tscn`, the QA playthrough player: from the title through the game's own touches
  (a careful player's fights, the breakthroughs the bar asks for, a logged assist after three falls), a screenshot
  at every step with the tracker and any label under the HUD, named steps and checkpoints (`--keep-at`, `--from`,
  `--start`, `--until`). `tools/dev/topdown_capture.tscn -- --tutorial-foes --into=<dir>/` shoots elsewhere than
  `docs/redesign/phase4/`.

## Top-down: Terrain v2, foliage and decor (decision 40, third part)

- **The top-down rooms are lush and layered, in the Alabaster Dawn manner, with every path kept clear**
  (`docs/redesign/art_bible.md` §14.12). Every top-down room is dressed: the 13 tutorial rooms and chapter 2's 14.
  - **Big trees** frame the paths and edges, and their canopies overhang and shade them: a village camphor, a wishing
    tree hung with red prayer ribbons and wish tablets, a great willow with swaying strands, plum and peach in blossom,
    a maple turning, a "cloud pine" and a bamboo grove. Each casts the shade of its crown along the sun.
  - **Canopies** draw over whoever walks under them. They fade to 35% while you or a foe stand beneath, and never
    cover a roof or a body in front of the tree. Trunks block; canopies do not.
  - **Garden and wild pieces:** bushes and flowering azaleas, clipped hedges, bamboo rail fences, mossy rocks, a fallen
    log, stumps, a wayside earth-god shrine, and potted pines and orchids in the halls, on the boat and in the yards.
    Tall grass, cattails, ferns and lotus pads are walk-through.
  - **Ground cover** is scattered over meadows, flower beds, the marsh and rock, the same every time:
    - tall grass (in patches), tufts, ferns, small shrubs, wild flowers, pebbles and mossy stones;
    - mushrooms and lingzhi;
    - reeds, cattails and irises on the shore;
    - leaves, maple leaves, petals, needles and bamboo leaves under their trees.

    Grass, flowers and reeds sway gently. Nothing grows round the Hollowing's dead trees.
- **Readable and fast.**
  - No ground cover lies on a path, the paving, a doorway, a way's lane, the spawn or anyone's spot.
  - Names, markers, pickups and rings draw above the foliage.
  - The ground cover is drawn inside the floor's own chunks (no node per piece), and the sway runs on the GPU.
  - `perf_tests` holds its budgets (Lotus Ferry loads under 0.3 s; the Marsh Edge holds 60 fps with 25 foes).
- **Tests.**
  - `topdown_foliage_suite` checks every room: the scatter's clear cells, trunks blocking, canopies not blocking, the
    batched draws and the canopy fade.
  - `data_validation` checks the kit's and the ground cover's sheets and rules.
  - `topdown_rooms.py --check` refuses a plant on a path, a kept-clear cell or a scene's walk, and a canopy that hides a
    person, a thing or a way.
- **Screenshots:** before and after, drawn by the game: `docs/redesign/terrain_v2/foliage/`, with every room whole in
  `after/rooms/`.

## Top-down: Terrain v2, runtime light (decision 40)

- **Cast shadows.** Trees, bamboo, lanterns, banners, houses, halls and cliffs of two levels or more now cast
  shadows to the lower right, longer the taller they are. Shadows fall down drops, never onto faces or bodies, and keep
  the tiles' crisp two-step look.
  - The shadows are worked out once, when a room loads, and cost nothing while you play.
  - The shadow under every body is now the same blue-violet.
- **Colour and time of day.**
  - Each area has its own light: a warm midday in the villages and a cool, misty marsh.
  - Outdoors, the game's clock turns morning, day, evening and night.
- **Night.** The Hollow Night and the clock's nights are lit by lanterns, fires, incense, Qi springs and warm open
  doorways. Their flames flicker, and a pale light round your feet keeps you visible.
- **The air.** A few particles drift in the pixel style:
  - pollen in the sun;
  - fireflies at night;
  - leaves and petals falling from willows, bamboo and flowering shrubs;
  - mist wisps over water and the marsh;
  - glints on sunlit water.

  Faint cloud shade glides over everything by day.
- **Settings → Controls → "Light and particles"** turns the extras off on older phones. It removes the colour
  grade, the hours, the clouds and the particles, and keeps the shadows and the night's lights. Reduce motion halves
  the particles.
- **Numbers.** Every colour and amount is in one place, `scripts/topdown/topdown_light.gd`, set to the art bible's
  contract (§14.2 and §14.11).
- **Screenshots:** before and after, drawn by the game: `docs/redesign/terrain_v2/light/`.
## Top-down: the full character set, the bow and the combat and story poses (decisions 37, 38, 39)

The last character batch: the full set is drawn and its gate is on. See `docs/redesign_top_down_plan.md`, "As built:
Phase 3, third part" (batch bow) and "As built: combat animation and feel".

- **The spirit bow** (`weapon_bow`, a new generator `kinds/bow.py`; the 10 bows and Qiu Feng's): a recurve wuxia bow in
  the side view's colours, gold limbs curving back to the string and flicking forward at the dark ears, a string of
  pale jade light. It is slung across the back with the string round the chest, and taken into the left hand to shoot.
- **Eighteen new actions**, each drawn on the unclothed body first, then on every layer (body, hair, garments, hats,
  capes and all twelve weapons) in the five drawn facings (864 frames, up from 494):
  - the bow's shot, `bow_draw` (7 frames at 12 fps): nock, draw, full draw at the chin, hold, release with the string
    humming, follow-through, recover;
  - the combat moves decision 38 asked for: the charged finisher's held wind-up, the dash slash, the air strike and the
    parry's deflection;
  - each family's own: the heavy sabre's three two-handed cuts, the flute played at the lips (its note from the open
    end; the held melody loops it), the bell rung out on both sides, the fan thrown (it leaves the hand on the
    release), the brush writing three strokes;
  - the story's gestures (decision 39): the wuxia salute (fist in palm, then a bow), a kneel, pointing with the sword
    fingers, a startled step back.
- **In the fight**, each plays where the game names it (`combat_feel.json` `poses` and `moves`, `CombatFeel.top_pose`,
  `TopdownFigure.resolve(action, family, move)`): a family's steps and techniques in its own pose, a blow in the air or
  out of a dash as that move, the parry when a guard parries, the charge while the finisher is armed, the melody while
  it plays. A companion or foe drawn as a person strikes with its family's first step. No pose is a stand-in any more
  (`missing_poses` and `stand_ins` are empty).
- **In the story**, the scenes use the gestures (`tools/data/scenes.py`): the recruiters salute, and the new disciple
  salutes back; Lu points to where the eel rose and kneels by the water; the Hollow Night startles Dou and Granny;
  Granny kneels to see to your graze; Aunt Ping, Dou, Lu and Courier Lin point the way.
- **The full set's gate is on** (`FULL_SET`, `PENDING` empty): 52 of 52 looks and actions are drawn, and a new look in
  the game's data must land with its layers.
- **Tests:** `topdown_suite` checks each family's pose, the air, dash, parry, charge and melody poses and a staged
  salute; `data_validation` checks that every family's poses and moves are drawn actions and that no pose is missing.
- **Review:** `docs/redesign/phase3/character/10_actions_<facing>.png` and `11_gestures.png` are new; every other
  sheet there is redrawn with the new actions.

## Top-down: the tutorial rooms' other foes in their own figures

- **Four foes drawn for the grid**, each in five drawn facings and three mirrored, with idle, walk, wind-up, strike,
  hurt and death. They stood in with their side-view sheets at half size, and took the crab's figure before that
  (`docs/redesign/art_bible.md` §8, "Foes").
  Each is the same creature as on its side-view sheet, in the same colours:
  - **Old Snapper**, the Reed Shallows' tough foe: an old snapping turtle with a mossy domed shell, a hooked beak and
    its great red crusher claw. It raises the crusher over its head in the wind-up and slams it down in a splash;
    beaten, it rolls onto its back;
  - **the mossback toad** on Willow Path West: moss and curled ferns on its back, golden eyes, a throat that puffs up
    in the wind-up and a long pink tongue;
  - **the hollowed eel** of the night: a grey eel rising in an S-curve out of the river over a dark stain, a loop of
    its back breaking the surface beside it, foam, rings and a wake round it. Its water is drawn where the game hovers
    it, 20 px under its feet. In death it sinks back under;
  - **the hollow minnows** of the night: small grey fish swimming through the air at their hover, grey strands
    trailing as their wake. Beaten, they come apart into mist.

  The two Hollow things have the hollowing look: colour drunk out, ash grey, cold white eyes and grey strands.
- **Every foe the grid's rooms spawn now has its own figure.** The stand-in stays for spirit animals, companions and
  any species not drawn yet, which an ambush, a hunter or a summons might bring onto the grid.
- **The foe cell grows to 64 × 72** (feet at 32, 40), for Old Snapper's slam and the eel's water. The earlier foes are
  unchanged pixel for pixel. The eel keeps the row it rose in, since it moves without a velocity or an aim; the plan's
  Phase 4 notes say so.
- **Tests:**
  - `topdown_tutorial` (801 checks) now checks the tutorial rooms' foes and every room event's foes for their
    own figures too, not just chapter 2's rooms.
  - `topdown_suite`'s stand-in check takes a pebble imp, which is still undrawn, and a new check sees Old Snapper drawn
    by its own rows.
- **Screenshots:** `docs/redesign/phase4/33`–`38`, from `tools/dev/topdown_capture.tscn -- --tutorial-foes`: the night,
  the Reed Shallows and Willow Path West, under the HUD and ×4 round the fight. The foe sheet at ×3 is
  `docs/redesign/phase3/12_foes_x3.png`.

## Top-down: Terrain v2, the tiles (decision 40)

- **The top-down world's terrain is redrawn to look closer to Alabaster Dawn, in Jade River's own xianxia world**
  (`docs/redesign/art_bible.md` §14, the contract for the runtime light and foliage work that follows).
  - **Light and colour.** One sun from the north-west. Warm lit edges and translucent blue-violet shadows: never
    black, never grey. Every ground, rock, water and roof material has a hue-shifted ramp.
  - **No visible grid.** Each material is one 64 or 128 px pattern. Clumps, tufts, flowers, pebbles, leaves, petals,
    cracks, moss and puddles are scattered as decals. Soft sun and shade patches drift across the big areas.
  - **Edges.** Grass hangs over paths and paving in soft tufts with a two-step shadow; the sawtooth is gone.
  - **Cliffs and faces.** Cliffs are fluted limestone under a lit, mossy lip with vines, with a dark foot where they
    meet the ground. Earth banks, stone walls and piers follow the same rules in their own materials.
  - **Water.** It is deeper and bluer away from land. The bed shows in the sunlit shallows, foam breathes at every
    waterline, ripples drift and glints twinkle, and rings spread round the pier pilings. It keeps its four frames.
  - **Paving and buildings.**
    - Town squares are irregular flagstones with moss in the joints; granite terraces are big slabs.
    - Roofs are dark glazed tile with a glint on every rib. The houses' roofs sweep up at the ends, with a heavy
      ridge and a shadow band under the eaves.
- **Polish pass, after review against Alabaster Dawn:**
  - the grass is a vivid green again, with crisp tufts of blades;
  - the paving is warm grey-beige flagstones about a tile across, with crisp joints and moss in the gaps;
  - the sun and shade patches are much subtler, and paving and granite take none;
  - cliffs are deeper, lips brighter, and granite terraces crisper.
- **No room had to change.** Every tile name and auto-tile rule stays; the room view draws each cell as layers.
- **Tests:** `topdown_suite` checks the layers ("terrain v2"); `data_validation` checks that every tile the new sets
  name is in the atlas.
- **Screenshots:** before and after, drawn by the game: `docs/redesign/terrain_v2/` (the village square, Jade Gate
  Street, the Marsh Edge, the Reed Shallows, the Fisher's Hut lane, Riverside Square, the height-levels room, the
  Cloud Sect's cliff stair and Elder Sung's peak), and the new tile sheet at ×4.

## Top-down redesign, Phase 4: the gaps closed (allies, hazards, respawn, the people, and the side view's rules)

See `docs/redesign_top_down_plan.md`, "As built: Phase 4, third part".

- **Companions and spirit animals move on the plane.** They follow behind you along your facing, on your floor, by
  the grid's paths: stairs, drops, and a hop a level up as you jump. With no way to you on foot they blink to you after
  2 s, onto your floor on your side of any wall. They strike only a foe on a height their blow reaches, and a foe's
  blow reaches them only on theirs.
- **Their figures:** a companion is drawn in the top-down style in its own outfit (`TopdownPlaces.Person`, turning to
  where it walks or strikes). A spirit animal, and a foe the grid's sheet does not draw yet (Old Snapper, the toads),
  is its side-view creature sheet at half size instead of the mud crab. Each is sorted and stands on its floor.
- **Hazards and weather are layered with the room.**
  - A strike's ring, a scorch, a pool or a current lies on its floor under whoever stands on it.
  - A falling rock, a bolt or springing spikes sorts at its spot, so a terrace or a wall in front hides it.
  - Washes, weather and warning marks draw over the room, under the names and the HUD.
  - Their effects are on the plane:
    - strikes fall all round you on floors, and reach you only on their own level;
    - a gust carries the top-down body;
    - the heavens' bolt strikes a circle;
    - burning ground burns only on its own floor.
- **Respawns out of view use the camera's rect**, on both axes (a foe no longer pops in on screen near a room's wall).
  On the grid two foes are never put on one point.
- **The people come with the room.** Page scripts now warm up one at a time after launch. While one compiles, every
  other load waits, and asking for all sixty at once held villagers back for seconds. They now draw within a moment
  of the room (80 ms headless, with 56 page scripts still to compile). `perf_tests` times rooms and pages once the
  pages are in.
- **The side view's x-only and walk-strip rules found on the grid, all fixed:**
  - camera bounds (a ridge on the north edge, the body always in view);
  - the ways' reach (turned with each way, on its own floor);
  - the pickup magnet and loot spill (by floor);
  - auto-path's arrival and auto-hunt's targets (by floor and reachability);
  - label order and the minimap's direction mark and arrow;
  - a foe's choice of ranged or close attack, and the off-screen notice;
  - a rare herb guardian's wake and spawn, and spar partners, summoned adds and ambushes (placed on floors);
  - decals on raised floors, and a drop's name distance.
- **Tests:** `topdown_suite` goes from 87 to 117 checks. `topdown_tutorial` (786 checks) adds a room's people drawn
  while the pages warm up, and each way's reach. The tutorial walk's blows aim at their target on the grid.

## Top-down combat animation and feel (decision 38)

- **Research first.** `docs/research/alabaster_dawn_2_5d.md` §3.9 covers how the reference game and CrossCode time and
  sell their blows. It covers combo length and finishers, commitment, charged and delayed attacks, guard and parry,
  break, hit feedback and how skills read from above, with fighting-game and pixel-art craft numbers. Every claim is
  labelled confirmed, inferred or not found.
- **The look rule.** The user clarified decision 38: only the *feel* comes from the reference game. The look stays
  wuxia:
  - sword-light arcs and qi trails, ink-brush strokes, jade and gold qi;
  - the elements' Dao images;
  - palm prints, sword formations and calligraphic impact marks.

  The rule heads the research section, the feel table and the FX manifest, and is written into roadmap §6 decision 38.
- **One table for the feel**, `data/combat_feel.json` (from `tools/data/combat_feel.py`, read by `CombatFeel`):
  - four blow weights: hit-stop 3, 4, 6 or 8 frames, a crit 2 more; the camera's kick along the blow; a shake for the
    heaviest; the impact mark and the knockback hop;
  - per weapon family, its steps' weights, lunges, smear rate and cancel points;
  - per technique form, its weight and pose;
  - foes' blows by role.

  The steps' phases (anticipation, active, recovery) are derived from `weapon_families.json`, never kept twice. The old
  flat hit-stop constants in `stats.json` are gone.
- **The fight on the grid feels it:**
  - hit-stop by weight, including a foe's blow on the player;
  - a dodge cancels a blow's anticipation or late recovery, is refused in its active window, and the player's dodge
    waits in a short buffer;
  - each step lunges along its aim, and an attack out of a dash is a dash attack;
  - the camera kicks and shakes;
  - struck bodies flash white, then tint, and hop with a knockback over a skid of dust;
  - effects freeze with the fight in a hit-stop.

  Reduce motion turns off the hit-stop, kick and shake. The side view is unchanged.
- **Everything drawn on the ground plane in eight directions** (`tools/art/fx/build_fx_topdown.py`, with `plane.py`,
  `wuxia.py`, `topdown_forms.py` and `topdown_melee.py`; 107 sheets in `art/fx/topdown/`, manifest
  `data/fx_topdown.json`, byte-identical on every build):
  - all 12 weapon families' combo steps, the dragged (charged) finisher, the dash attack and the air blow;
  - the guard, the parry, the Plunge's crater, a charge, a foe's tell and swipe;
  - all 24 technique forms in 11 elements at three richness bands, with the thrown forms' bolts;
  - impact marks by weight and element, and dust.

  `TopdownFx` plays them in the world viewport, sorted with the bodies, their contact frames on the hits.
- **Poses.** The figure's hit frame lands on the blow's hit, the same instant as the smear's contact. A cast of a
  meditation or jump form plays its form's top-down pose (`cast`, `plunge`). The poses the character pipeline does not
  draw yet (bow draw, flute, charge hold, dash slash, air strike, parry deflect, two-handed sabre, bell, fan throw,
  brush) are listed for it in the feel table and the plan.
- **Tests:**
  - `data_validation` `combat_feel_suite`: timing tables valid for every family, form, technique and foe; every sheet
    at its size;
  - `topdown_suite`: 9 new checks, among them the hit-stop and shake off under Reduce motion;
  - `perf_tests`: 22 foes fighting with techniques, 9.9 ms a frame.
- **Review images** in `docs/redesign/phase5/combat/`: the builder's strips per form, family, impact and mark, and the
  game's own frames of combos, a finisher and a dash attack, techniques, the guard, a parry and the Plunge.
## The story staged: in-engine scenes and a playable opening (decision 39)

- **Research first.** `docs/redesign/story_staging.md` covers how CrossCode, Alabaster Dawn and other top-down RPGs
  stage their stories in the engine:
  - dialogue with portraits, and live side lines;
  - emotion balloons and scripted events (move, face, emote, speak, camera);
  - teaching through the story (A Link to the Past's rainy opening, "pick up that can");
  - hold to skip, and bypassing for accessibility.

  Each claim is marked confirmed or inferred, with sources. Eight principles for Jade River follow from it.
- **A scene system, data-driven and in one place.** `tools/data/scenes.py` builds `data/scenes.json`, and
  `SceneDirector` plays it in the rooms on the height grid. A scene's steps are:
  - **actors:** walk (round obstacles), face, emote, pose, speak in a balloon or on the dialogue page's portrait strip;
  - **camera:** pan, follow, zoom, shake, letterbox;
  - **screen:** fade, flash, title card;
  - **world:** spawn and despawn people and props, open a door, weather, a moment, effects, sounds;
  - **flow:** wait for time, a tap or an event, branch on the story's state, labels, checkpoints;
  - **hand-off:** the player acts, with a prompt over the thing, the person, the foe, the way or the HUD control.
- **How a scene behaves:**
  - **Modes.** A cut holds the game still under a letterbox, with the HUD and the names faded. A hand-off gives the
    controls back. A live part plays around the player. A fight turns a cut live, and a cut never starts in one.
  - **Skipping.** A tap moves a line on. A hold skips to the next hand-off, and the skipped part's checkpoints still
    apply.
  - **State.** The Quest authority owns it (`scene_begin`, `scene_mark`, `scene_end`; `QuestState.scenes`). A seen
    scene never replays, and a scene cut short by quitting resumes at its last checkpoint, its people where the script
    had put them.
  - **Reduce motion** makes the camera cut instead of pan, fades the bars and the title instead of sliding them, holds
    the rain still and drops the shake.
- **The opening, rewritten as a playable story.** Fifteen scenes run from waking to the sect choice:
  - Aunt Ping wakes you and hands you the tea, teaching the Bag through a gift, then sends you to the door;
  - a boat passes, the villagers talk of grey water, and the wind takes Little Dou's kite;
  - Guo shows the jab on his stump before handing it to you;
  - Dou shows the way up to his kite, and Shen Lian races you to the tower (sprint, through a chase);
  - a jar falls in Granny's hut and grazes you, so the Quick-use slot is taught by an injury;
  - Guo opens the East Gate, and the crabs corner Washer Mei (the first fight);
  - a storm comes on the Hollow Night;
  - Lu teaches meditation, and after the first breakthrough shows the palm and gives the reason to leave home;
  - a thief runs through the market;
  - the recruiters trade calls at the fair, and the chosen sect welcomes you.

  All writing is original. The quests, gates and tests are unchanged, and each scene runs 10–26 s.
- **Shared code, nothing copied:**
  - `MomentView.letterbox`, `draw_title`, `play_row` and `in_fight`;
  - `UiKit.wrap` (the pages' wrap);
  - `TopdownPlaces.person` and `figures`;
  - `PropView.place_at`;
  - `TopdownWorld` gains `stage_cam`, `stage_zoom` and `fade_labels`.
- **The event contract gains** the scenes' three events, plus `page_opened`, `quest_failed`, `object_hit` and
  `quick_use_changed`, which the catalogue had missed.
- **Tests:**
  - `story_scenes` is new, in `tools/run_tests.sh`. It checks that every scene validates, the opening in the real view,
    resuming after a reload, never replaying, skipping, Reduce motion, and a fight breaking a cut.
  - `topdown_tutorial` plays every scene of the tutorial to its end as the walk reaches it. The cuts count on the play
    clock, and the first hour's pacing still holds.
- **Screenshots:** `tools/dev/topdown_capture.tscn -- --story`, in `docs/redesign/phase5/story/`.
## Top-down character: the flute and the bell (decision 37)

- **The jade flute and the warden's hand-bell are drawn** in every action and facing, as two layer sets
  (`weapon_flute`, `weapon_bell`). The 21 game items that wear them (10 flutes, 11 bells) now show on the top-down
  character. Both are held in the fist as the side view holds them, and look like its sheets in its colours.
  - **The flute** is a green bamboo dizi with dark joints, finger holes and a red tassel. On every blow its note leaves
    the far end as ripples of pale jade light: sound-wave arcs from the side, rings when it points at the camera.
  - **The bell** is bronze, with a domed crown, a dark band, a flared lip and its clapper, on a dark-wood handle with a
    red cord. Its blows ring out as rings of pale-gold qi round the mouth.
  - The sound shows on the hit frame and, fainter, on the frame after. Laid down while meditating, the flute lies
    beside the figure and the bell rests on its side.
- **New generators:** `figure/kinds/flute.py`, `bell.py`, and `sound.py`, which draws what a sounding weapon sends out on
  its blows. A blow's frame is known by its pose, so the action catalogue and every other set are unchanged.
- **Review sheets:** `docs/redesign/phase3/character/03_weapon_flute.png` and `03_weapon_bell.png`.
## Top-down: the fan and the brush (decision 37)

- **The fan and brush batch is drawn.** `weapon_fan` and `weapon_brush` give the top-down figure the looks of 21 game
  items (10 fans, 11 brushes), in every action and facing. Two new generators cast them, `figure/kinds/fan.py` and
  `figure/kinds/brush.py`. No shared file changed, and every other set's files are byte-identical.
- **The iron fan** is the side view's: cream paper pleated over brown ribs, a teal ink band on its rim, and a gold
  rivet under the fist.
  - It folds at rest into a slim bar, brown at the handle and the tip.
  - It opens in the blows (the family's swings, and every thrust, punch, the guard and the plunge's dive).
  - Open, it always shows its face: it is turned at least 50° off the camera's line and faces the camera.
  - Its cuts leave the jian's smear of jade light. It lies folded beside a meditating figure.
- **The calligraphy brush** has a jointed bamboo shaft, a lacquered cap and collar, and a tuft pale at the root and
  soaked black to its point. Its cuts leave an ink stroke along the arc the point swept. The stroke is broad at the
  brush and thin behind it, and at its tail it has run dry: grey and broken.
- Review sheets: `docs/redesign/phase3/character/03_weapon_fan.png` and `03_weapon_brush.png`.
## Top-down character: the heavy sabre (decision 37, the heavy_sabre batch)

- **The heavy sabre is drawn** in every action and facing (`weapon_heavy_sabre`; parts.json weapon `sabre`). Its ten
  game items, from the Training Heavy Sabre to the Mountainsplit Sabre, now show on the top-down character instead of
  going in `TopdownFigure.missing`.
- **The side view's dao, in its colours.** It has a broad, single-edged blade of grey steel with a pale bevel on the
  edge. The blade swells to a belly near the point, and the point sweeps back to the spine. It has a bronze oval guard
  and pommel on a dark grip long enough for the second hand. The broad side is turned part way toward the camera, so
  the blade reads as wide in every facing and thin only where it points along the view. Laid down while meditating,
  it lies beside the figure with its breadth showing.
- **A heavy wuxia arc on its cuts.** The swings (swing_1–3) leave a crescent of pale jade light. On the hit frame the
  crescent is fat at the blade, thins to a sliver at its tail, and is brightest along the path of the point; on the
  frame after, a thinner, dimmer wisp trails the blade. The heavy descending cut goes over the top in a full
  half-round crescent: straight over the head where the facing shows it, else leaning to a shoulder. It never cuts
  through the body, and it never draws as a flat bar.
- **Its own files only.** The new generator is `figure/kinds/sabre.py` and the set is
  `figure/sets/weapon_heavy_sabre.py`. The build writes `data/topdown/character/weapon_heavy_sabre.json`,
  `art/topdown/character/weapon_sabre.png` and the review sheet `docs/redesign/phase3/character/03_weapon_sabre.png`.
  The shared index and every other set's files are byte-identical.

## Top-down redesign, Phase 4 goes on: chapter 2's stretch on the grid, for both sects

- **Fourteen more rooms on the grid** (`docs/redesign_top_down_plan.md`, "As built: Phase 4, second part"). They are
  the rooms the story visits from the sect choice to The Humming Token, for both sects a player can join:
  - both Entry Trial grounds: a rooftop climb for the Jade Sect and a ledge climb for the Cloud Sect, each to the bell,
    and a sand ring for the Trial Puppet;
  - the Jade Sect's Gate Street, Weapon Hall, Pavilion Rooftops (its training yard), East Terrace, Herb Terraces and
    Elder Hu's Peak;
  - the Cloud Sect's Cliff Stair, Sword Court, Weapon Hall, Array Court and Elder Sung's Peak;
  - the Marsh Edge.

  Each keeps its side-view room's people, objects, ways, foes and rules. On the grid they have:
  - halls on terraces a level apart, with roofs you can climb;
  - stairs and ledges up to the mentors, the Meditation Rock and the library's cliff door;
  - the plum-blossom poles, stilt platforms over the marsh water, boardwalks, ponds and gardens.
- **New art in the approved style:** a sect hall with a red colonnade, pines, weapon racks, the two sects' banners,
  training stumps, a drained dead tree, grey reeds and boulders, and a wet-meadow tile. **Five new foes**, each in five
  drawn facings and three mirrored, with all six actions: the Trial Puppet, the reed frog, the marsh leech, the reed
  otter and the hollowed boarlet.
- **Fixes:**
  - A Cloud Sect disciple's chores and Weapon Hall now lead to the Cloud Sect's own rooms. The tracker used to name
    the Jade Sect's rooms, which a Cloud disciple cannot enter; this was wrong in both views.
  - The Cloud Steps' finish follows its bell wherever the room puts it.
- **Tests:**
  - `topdown_tutorial` (777 checks) plays the Jade walk on the grid through The Humming Token. It then goes back to
    the fair and plays the whole stretch again as a Cloud disciple, running the Cloud Steps on the way. Every
    `tutorial_order` invariant holds throughout.
  - `topdown_rooms.py` also checks that auto-path can reach every way, and `perf_tests` times the Marsh Edge with 25
    foes fighting.
  - The walk's sect comes from one table (`SECTS`), and `valley_run` shares the run's checkpoint helpers.
- **Screenshots:** `docs/redesign/phase4/17`–`32`.

## Top-down: the real character (decision 32)

- **The prototype's body is the game's own character**, redrawn for the ¾ view: the side view's big-headed build,
  faces, hair styles, clothes, colours, dyes and weapons. It reads the same data: `parts.json`'s names, dyes and hair
  colours, and the save's outfit. It replaces the placeholder body, which is removed. Details are in
  `docs/redesign_top_down_plan.md`, "As built: Phase 3, third part", and `docs/redesign/art_bible.md` §13.
- **Drawn by `tools/art/topdown/build_character.py`.** It is deterministic and byte-identical twice (`--check`). A
  posed doll is ray-cast at 1 art px and shaded in the side view's ramps with the art bible's outlines.
- **Drawn in layer sets, for the full set (decision 37).** The sets are `body`, `hair`, each garment slot and each
  weapon family.
  - Each set is its looks' specs, cast by one generator per layer kind (`figure/kinds/`).
  - `--only <set>` builds one set in about ten seconds into its own manifest, `data/topdown/character/<set>.json`,
    and its own sheets, so agents can draw sets in parallel.
  - A stale set, built for another action catalogue, is refused.
  - Each look lists the game items that wear it.
  - `data_validation`'s coverage gate fails for any look or action that no pending batch lists, and it fails for any
    missing one once `FULL_SET` is on.
  - `docs/redesign/phase3/character/HOWTO.md` says how to add a set. Four batches are left, 62 items: the sabre; the
    fan and brush; the flute and bell; and the bow with its draw and release.
  - The unclothed body comes first; every layer is cast from the same poses over it (`AGENTS.md`).
  - S, SE, E, NE and N are drawn; SW, W and NW mirror. The collar and the weapon hand swap sides in the mirrored
    facings.
- **Twenty-one actions, 494 frames:** idle, walk, run, jump, dash, dodge, hurt, knock-down, punch 1–3, swing 1–3,
  thrust 1–3, cast, guard, plunge and meditate (S only; its other facings redirect to S). A cut leaves a smear of
  jade light.
- **Every creator look is drawn,** with every dye and hair colour:
  - the body and the six hair styles;
  - all five shirts, five trousers and three shoes;
  - the five hats and two capes;
  - the training gauntlets, the short blade, the jian, the spear and the staff.

  124 of the 125 NPCs are fully drawn, and so are all nine of the tutorial's. Only the bow (qiu_feng's, and the bow
  family's) and the later weapon families are left; each goes in `TopdownFigure.missing` and draws nothing.
- **In the game.** `TopdownFigure` composites the layers. The player wears its equipment and dyes from the save,
  dresses again when they change, and plays each state's action. A blow lands its hit frame on Combat's clock. The
  facing picks one of eight rows. The i-frames' blink and the occlusion silhouette fade the figure as one image, so
  the body never shows through its clothes.
- **The people of the rooms on the grid are drawn the same way** (`TopdownPlaces.Person`), in place of the side
  view's avatars at half size facing east or west:
  - each in their own outfit, at rest three-quarters toward the camera (or meditating, facing it);
  - turned to the player in the eight rows during a talk, a gift or a shop, then back;
  - walking the way a route moves them.

  `TopdownWorld.add_villager` stands one anywhere, for the prototype and the reviews.
- **Tests.**
  - `data_validation` holds the layer contract for every item, action and facing, and shows the gate refusing
    eleven broken manifests.
  - `topdown_suite` checks the outfit from the save, dressing again, each state's action and the eight facings; the
    drag moves use the real guard and plunge. A villager wears their own outfit, turns in eight rows, walks, and
    meditates facing the camera.
  - `topdown_tutorial` checks every person of the walk's rooms is drawn this way, fully dressed, and that Shen Lian
    turns to the player talking to her and back.
  - `tests/topdown_figure_gallery.tscn` renders the compatibility gallery with the game's own compositor.
- **Review sheets** are in `docs/redesign/phase3/character/`: the body, an outfit per facing, the weapons, hair,
  dyes, wardrobe and villagers, the mirrored facings, and Riverside Square in the game. The game's Phase 3 review
  images (`topdown_capture.tscn -- --phase3`) now draw the real character.

## Top-down redesign, Phase 4 begins: the real game on the grid, from the Fisher's Hut to the sect choice

- **The top-down world runs the real game** (decision 36; `docs/redesign_top_down_plan.md`, "As built: Phase 4").
  A character made for it keeps its own save and quests, and every authority runs as in the side view. That covers:
  - NPCs, talk, quest offers and hand-ins, gifts and shops;
  - the tracker, its Next, the direction mark and auto-path;
  - pickups and loot, gathering, doors and edges between rooms, room events and respawns;
  - the equip popup and the "+" badges, moments, the night tint, saving and loading, and the fall and revival rules.
- **Rooms with a layout are played on the grid; the rest stay side-view.** The view changes under the same HUD at the
  way between them.
- **Thirteen rooms** are laid out for the top-down world by `tools/data/topdown_rooms.py`: the Fisher's Hut, Lotus
  Ferry and its night, Old Ma's Store, Granny Liu's Herb Hut, Lu's Boat, the Reed Shallows, both Willow Paths, and
  Stoneford's Gate, Market Street, Artisan Row and Fairground. They use the approved tile set, with height levels,
  paths to the doors and water edges. Every id of the side-view rooms is kept.
- **How to reach it:**
  - the title screen's hidden entry (five taps on the version) now opens the top-down game on saves of its own,
    starting the Prologue in the Fisher's Hut the first time;
  - Settings → Controls → "Top-down world (new games)" makes the next new character a top-down one;
  - `--topdown` and `--topdown-tutorial` do the same for previews; `--topdown-proto` still opens Riverside Square.
- **One code path per concern.**
  - The effects both views play for the game's events, the context button's offer, the names over the world and the
    request for a way out now live in `WorldShared`.
  - `NpcView`, `ObjectView` and `PortalView` gained label and art modes, so the top-down view draws the side view's
    own art in its pixel viewport and its plates at the HUD's resolution.
  - The autopilot, the minimap, `MomentView` and `HazardView` work in either view.
- **Tests:**
  - `topdown_tutorial` (new, 473 checks) plays `tutorial_order`'s whole walk, and every invariant of it, as a
    top-down character. It adds checks that:
    - every layout places and reaches everything of its room;
    - every spot the walk stands at is reached on foot;
    - the view builds each room;
    - a save resumes on the grid;
    - auto-path walks through a door and an edge.
  - `tools/run_tests.sh` also runs `topdown_rooms.py --check`.
  - `prologue_run` and `tutorial_order` are view-neutral.
  - `perf_tests`: Lotus Ferry entered in 63 ms, 7.44 ms a frame.
- **Screenshots** of every room and of a quest talk are in `docs/redesign/phase4/`.

## Top-down redesign, Phase 3: the terrain in the game, Riverside Square redesigned, the first foes in eight facings

- **The terrain draws by the art bible in the game** (decision 33; `scripts/topdown/topdown_terrain.gd`):
  - paths and paving take grass's corner-matched edge from their own level;
  - water takes its shore case in each of its four frames;
  - every raised edge has its rims, contact shade and cast shade, and every face its lit and shaded ends;
  - stairs have their cheeks;
  - each prop's floor shadow is cut to the floor it stands on.

  Phase 2's combat and collision are unchanged.
- **Riverside Square is redesigned for it** (`data/topdown/td_proto_square.json`):
  - a terrace path from the stairs to the rooftop jump and a cliff-foot shrine;
  - paving from both doors and the stairs to the pier, between lawns;
  - a lotus pond with a willow, and a planted bed in place of the low wall;
  - bamboo groves, and red lantern posts at the house door and the pier;
  - a boat's notch in the promenade, and grassy banks.

  The rooftop route, both gaps and every `topdown_suite` number are unchanged (decision 34).
- **Plants move:** bamboo and willow sway a pixel, and lotus flowers bob on the water's clock, each at its own phase.
- **The first foes** (`tools/art/topdown/creatures.py` → `art/topdown/foes.png`):
  - the mud crab, reed rat and boarlet, redrawn from their side-view sheets;
  - five facings drawn and three mirrored;
  - idle, walk, wind-up, strike, hurt and death at their own rates.

  They replace the placeholder foes. The crab scuttles sideways, broad side to the camera, as in its side-view sheet.
- **Review images come from the game** (`topdown_capture.tscn -- --phase3`, `docs/redesign/phase3/08`–`15`, a
  regenerated height test). They include the mock beside the loader before and the game after. The Python reference
  renderer is retired.
- **Tests:** `topdown_suite` gains 8 checks (terrain rules, the square's routes and dressing, the foes' facings).
  `data_validation` checks prop frames, prop shadows and every foe's frames. `build_tiles.py --check` stays
  byte-identical.

## Study: which systems live on the map as places (decision 36)

- **`docs/redesign/systems_as_places.md`**, a proposal for the user; nothing is built. It gives every page a verdict:
  menu, place, both (the place opens the page and the menu keeps it), or earned remote. Each verdict comes with where
  the place would sit, how interacting looks in the top-down view, what the player gains and loses, what runs while
  away, and a priority.
- **Research** on how Final Fantasy XIV, Old School RuneScape, Albion Online, Black Desert Mobile, Genshin Impact,
  Stardew Valley, Animal Crossing, Pokémon, IdleOn and Sea of Stars split the world from the menu, with links.
- **Recommended:**
  - most systems get a place and keep their menu entry;
  - Storage, the Garden's tending and the Crafts queue earn remote access;
  - the self and the events stay in the menu;
  - the home is Lotus Ferry, then the existing Cave Abode;
  - eight places for the prototype room;
  - a phased list, and five decisions for the user.

## Top-down: Attack's drag moves (decision 35)

- **Three new moves on the Attack button in the top-down room.** The tap and the aimed drag work as before. Details
  are in `docs/redesign_top_down_plan.md`, "As built: Attack's drag moves".
  - **A long drag strikes the combo's finisher at once** along the drag. Mid-chain it comes next, in place of the
    steps between.
  - **A drag down in the air is the Plunge**: the existing art, with its unlock, 4 s cooldown and its strike and stun
    where it lands. The body drops straight down at 900. Without the art the drag stays an aimed air blow.
  - **Holding still for 0.3 s guards**, with the weapon family's damage cut and parry window. With a counter-stance
    technique slotted and ready, the hold casts that instead. Letting go ends the guard and strikes nothing.
- **The finisher's line** is 120 px from the button, pulled in near the screen's edges (67 px toward the right and
  bottom), so every drag zone stays at least 48 px deep on both layouts.
- **Each armed move shows on the button** (the finisher's line, the Plunge's sector and chevron, the hold's ring, and
  the move's name) **and on the ground** (a gold arrow, the landing ring under the body, and the guarded half ring).
  Nothing pulses under Reduce motion.
- **Guard and plunge poses** come from the body sheet's `guard` and `plunge` rows when it has them. Until then they
  fall back to the idle and jump cells.
- **Tests:** `topdown_suite` goes from 62 to 75 checks. `rules_tests` runs the top-down fight checks again; a merge had
  dropped the call.
- **Screenshots** are in `docs/redesign/drag_moves/`.

## Pages, rooms and the top-down room open inside their budgets under load

- **Techniques page** (P13b). It keeps the tree's layout across opens, built as the world mounts or a room is entered,
  and the technique trees' index is built there too. The live preview is built the frame after the page opens. The
  preview's form sheets load on a thread as an art is chosen. Card emblems compose within 4 ms a frame, and card
  stills are kept across opens.
- **Every page that fades in** now draws once as it opens, not twice. On that frame its icons, creature sheets and
  seals load on threads while the page is still nearly transparent.
- **Rooms.** A room's backdrop layers and its villagers' outfit sheets load on threads under the entry fade.
- **perf_tests** frees its 4,350-row fixture outside every timing. Freeing it fell into the top-down room's mount time.
- **Measured** with 10 perf_tests runs before and 10 after, alternating, at load ~6 (median / max, ms):
  - Techniques page open: 236 / 314 → 36 / 73.
  - Slowest page: 230 / 626 → 78 / 114. "Every page opens in under 0.15 s" failed 8 of 10 runs before and 0 after.
  - Techniques page with sixty composed arts: 107 / 162 → 43 / 81.
  - Slowest room: 150 / 206 → 116 / 158.
  - Top-down room mount: 286 / 412 → 86 / 143. Its check failed 4 of 10 runs before and 0 after.
  - Budgets are unchanged. At that load the 60 fps frame checks and the v1.5 parse ratio still fail at times, before
    and after.

## Top-down redesign, Phase 3 begins: the art direction and the prototype room's terrain

- **An art bible for the top-down world** (`docs/redesign/art_bible.md`, decision 31). It sets:
  - bright ¾ pixel art in the game's own xianxia river-town theme, original throughout;
  - seven-step material ramps tied to the Style A palette, with a jade river;
  - one sun in the upper left, and outlines on props only;
  - 16 px tiles in a 640×360 view, one level = one 16 px face row, a ~38 px body;
  - six cues on every raised edge: a lit lip, a contact line, a face at most 0.65× its top's value, shade at the foot,
    side rims, and the body's shadow;
  - corner-matched path auto-tiles, side-matched shore auto-tiles, and faces from the height grid;
  - prop rules, water and foliage animation, and what makes it xianxia.
- **A deterministic tile and prop build** (`tools/art/topdown/build_tiles.py`; `--check` proves two builds
  byte-identical). It draws a new `art/topdown/proto_tiles.png`:
  - tops: grass, path, paving, granite, karst rock, pier planks, grey roof tiles, wall caps;
  - faces with lips: earth bank, retaining wall, cliff, embankment, pier pilings, roof eave, plaster walls with a
    window and a red door, courtyard wall;
  - stairs, four frames of jade water, 16 shore cases × 4 frames, 32 grass-to-path transitions and five light
    overlays.
- **A new `proto_props.png`.** The house and storehouse have tiled roofs that read as floors, and the crates have
  lids that do too (decision 29). Willow, lanterns, barrel, notice board, reeds and boat are redrawn. Bamboo, lotus, a red lantern post, an incense burner and a
  shrub are new.
- **A Godot TileSet** (`art/topdown/proto_tiles.tres`): terrains for paths (corners) and water (sides), animated water,
  and every tile's name as custom data.
- **The manifest** (`data/topdown/proto_tileset.json`, schema 2) keeps the Phase 2 schema (atlas, paint, prop tops,
  foes) and adds auto-tile and overlay tables. The room and its view are unchanged and now draw the new art. The auto-tiles, rims and prop shadows are drawn by the
  reference renderer (`compose.py`) and wait for the loader work.
- **Review images** are in `docs/redesign/phase3/`:
  - the square mock at 640×360 and ×2;
  - the whole room and the water loop;
  - the tile sheet and props at ×4;
  - the height-levels test in colour and grey;
  - the loader in the game.
- **Tests:** `data_validation` `topdown_art_suite` checks the atlas against the paint table and the view's names, the
  props against their sheet, and the TileSet (terrain sets, names, animations).

## Top-down redesign, Phase 2: fights, foes and aiming in the prototype room

- **Riverside Square fights** (`docs/redesign_top_down_plan.md`, "As built: Phase 2"). The room now runs on the same
  Combat, Enemies and World authorities as every room. Blows, techniques and the dodge work in eight directions with
  the existing damage, Might, hit-stop, knockback (now pushing away on the plane) and i-frames. The technique forms
  from `art/fx/` turn to the aim.
- **Heights count.** A blow lands only on a foe whose feet are within a few units of yours: a foe a level up is out
  of reach until you jump at it, and it cannot strike you below either. Shots fly along the ground and stop at a
  face.
- **Foes on the grid.** Crabs, rats and boarlets use **placeholder** sprites; their full art is Phase 3/5. They spawn
  and respawn by the usual rules. They chase along a path over the height grid: stairs, drops, and a hop one level up
  for the rat. They flee, leash at 600, and wait beneath a roof they cannot reach before going home. They have HP bars
  and labels, and drop loot, with the equip popup for a better piece.
- **Aiming** (decision 30; research in `docs/research/alabaster_dawn_2_5d.md` §3.8). A tap strikes the nearest foe in
  front, marked by a faint ring. Hold and drag Attack or a technique to aim it: a line, a cone, a circle at a point, or
  a circle round you, snapping to a foe near the line. Drag back onto the button to cancel.
- **Decision 29.** Water stops a walk unless the character knows Water Skimming. Roofs and crates are floors: climb
  from the terrace onto the new storehouse's roof, cross it, and jump down to the square. The dash cooldown stays
  2.5 s.
- The side-view game is unchanged. Its cast and hit effects and camera shake now come from shared `CombatFx` and
  `ShakeRig`.
- Tests: `topdown_suite` 62 checks (27 new). `perf_tests` holds 15+ foes and the fight's effects at 60 fps.
  Screenshots are in `docs/redesign/phase2/`.

## World map plates and the Roll-Call as drawn

- **World map:** each plate names its area and nothing more, and the available and current-area dots are smaller
  (9 and 11 px radius). The level band, "You are here", the field boss and the kinds of resources stay on the card. The
  legend drops the marks that no longer appear on the painting. `map_suite` checks every plate is one line holding its
  area's name. Screenshots in `docs/ui_p5/map/`.
- **Roll-Call:** the board fills the screen at mockup 13's size and places: the beam, cartouche and tags with their
  glyphs; tablets 184 x 268 set 200 apart; vessels, shelf and brackets; Settle with the goods' glyph; Settle all in
  two sizes; the roofed cabinet with the Auto-Settle switch; the Bench on its legs with the craft-level diamonds. A
  turned tablet hangs askew and carries its own Switch and Incense. The Board tag now shows only while another view is
  open. Buttons can carry a 32 px icon (`Page.btn`). Screenshots in `docs/ui_p5/post/`.

## Visibility: gates, doors, hidden ways and things set on roofs and decks show themselves in every room

Some gates and map items could not be seen. A new suite found every case in all 168 rooms, and each one is fixed at
its cause.
- **Every way draws something where it stands.** An open `gate` (the village's West and East Gates, Stoneford's roads,
  the stockade, the tomb, the vale and the hamlet) drew only its plate. It now stands as a road gate, a timber gateway
  under a glazed roof with its leaves swung back (new art, `road_gate`, `tools/props/defs_structures.py`). A hidden way
  found by Spirit Sense or the Wandering Eye drew nothing at all. It now shows a cleft in the rock with a breathing
  jade rim (`hidden_way`). Sixty-six `door` ways drew nothing when open. A door way with no building doorway
  and no door placed at it now stands as a door: cave and dungeon exits, trial exits, skiff landings and paths
  (`PortalView.TYPE_ART`, `entrance` "door"). A boat, a sky ship, a tent, a swirl or an arch placed at a way shows it
  (`PortalView.WAY_DECOR`). A gate standing in a painted gate's arch (the Ascension Gate) is shown by its arch.
- **Doors stand in their building's doorway, in front of the facade** (the door rule of the tutorial fix, now in every
  room). Gate Street's Weapon Hall, Alchemy Hall and Library doors stood 6 px behind the hall fronts, so they drew
  behind them. They now stand in the doorways (y 724). The Quarry Road door stood behind the town wall's face and now
  stands at its foot.
- **A thing set on a roof, deck or terrace draws over it** (`ZoneGeometry.depth_at`, the player's rule, now shared by
  `ObjectView` and `NpcView`). Lu's float in the hut loft, the star mat on the boat's cabin roof, the hermit's mat and
  tea on his stilt deck, the Bend Shore and Rapids fishing spots, and the grey lantern on the granary roof all drew
  behind the surface under them. Only a decal prop now lies flat under figures, so an inspected notice board, mat or
  scope stands like any other thing (the Beast Arena ladder was behind the warehouse). Decal decor on the ground (a
  rug, flowers, planks) draws under everything standing on it: the abode and retreat mats were under their rugs.
- **Placed clear of what hid them.** Two Marsh Edge jars were under reed bundles. A Lightning Scar jar stood behind
  the insight stone. The Stoneford tide gong was inside a gate step. The tunnel's shard vein was behind the
  rubble heap and now sits on top of it. Gate Street's notice board was behind the library front. The Rapids spirit
  mine was behind the salmon stone (`spirit_mines` now keeps a mine out from behind a block). The abode's scroll rack
  stood in front of the terrace door.
- **Tests**: `visibility_suite` (new, in `tools/run_tests.sh` and `Test.ps1`) builds each room's draw list in the order
  and at the depths `world.gd` uses (`tests/draw_model.gd`, from the views' own `depth`, `prop_rect`,
  `building_pieces`, `sort_z` and `art_for`). It checks every way (open and shut), object, person and solid prop:
  its art exists and has a non-zero size with opaque pixels, it stands in the room where the camera can show it, and
  at least half of its pixels are not covered by a layer drawn after it. It also checks that a doorway is clear, that
  a thing with no prop marks art the room draws, and that an open way's plate is on screen. It found 118 failures
  before the fixes and finds none after. `room_sweep` reads prop pixels through the same model.
- **Screenshots** (before and after) in `docs/ui_p5/visibility_fix/`.
## Points to spend show on the HUD

- **A "+" badge by the HP panel for each system with points to spend.** Meridian points (Foundation), Realisations
  (the trees), bench points and Post Arts points each get a small badge in a row at the panel's top right. Each badge
  has its own colour, shape and symbol, is a 48 px target and pops in (with Reduce motion it just appears). A tap opens
  the page and tab where the points are spent. A badge is hidden while its system is locked or at 0. There is one
  table, `HUD.POINT_SYSTEMS`, and the counts come from the authorities' getters. Screenshots are in
  `docs/ui_p5/points_badges/`.
## Quests that ask for items take them

- **Turning in a "bring" quest hands the items over.** `QuestAuthority.hand_in` took a collect objective's items only
  when it was marked `consume`, and most were not, so "Bring Willow Moss" (Mei Qing's Errand) and 11 other quests left the
  items in the bag. Every collect objective now says whether it hands over or only counts (`story.o` refuses one that
  does not; data_validation checks quests, sect missions and county jobs); 33 quests hand items over. The hand-in
  checks everything first and takes it with the reward, is refused with what is still missing, never takes a worn
  piece ("Take off your ... first"), names the items on its choice and toasts "Gave 5 Willow Moss".
## The Techniques page: closer to its mockup, and each art cast live

- **The chosen art is cast under the chooser.** The character, a little smaller, performs the art as a fight does
  (`TechniquePreview`: its `vfx.pose`, its form's sheet through the room's own `FxLayer.cast`, now shared with
  `World._cast`, and its hits through `FxLayer.hit`) against pebble imps (the creature sprite a foe's view draws) that
  flinch, flash, are knocked back and show their numbers: one imp for a single strike, a pack for a multi-hit or area
  form, an imp's blow turned by a ward's dome, parried by a counter, held by a snare or a seal. It loops with a pause,
  starts again on another art, holds one still frame at the impact under Reduce motion, steps at 30 fps under Battery
  saver, and plays only while the page is open; a passage, an Inner Art or an art still unfound shows nothing.
- **Nearer the mockup** (`docs/ui_p5/techniques/README.md`): cards show the art's picture (the character in its pose
  on its element's ground, a small still composed once a pose, the emblem in its corner) instead of the emblem alone; no head strip over the chart (rows 139 px
  apart, Learned and Let all go small at its top right); name plaques with gold diamonds; locks and the Realisations
  mark in the tags; closed Learn plain with the reason in gold; lighter section names in the reading.

## Top-down redesign, Phase 1: a prototype room and the new controller

- **A top-down room you can play beside the current game** (`docs/redesign_top_down_plan.md`, "As built: Phase 1").
  Open it with `--topdown-proto`, or tap the title screen's version line five times. From the title it plays on its
  own saves with a stand-in character. Riverside Square is a ¾ top-down room drawn at 640×360 and shown ×2 under the
  unchanged HUD. It has a terrace and a paved square one level apart, stairs, a ledge to drop from, a house to walk
  behind (a jade silhouette shows you through it), a low wall to jump onto, the river with a pier, a one-tile gap and a
  three-tile gap, and props.
- **The controller** (`TopdownMotor`): 8-way analog walking at 154 units/s, with a tiptoe band and 0.08 s / 0.06 s
  acceleration and stop. The Jump button (decision 28) clears one level (apex 47, 0.47 s). Walking off any edge
  falls. Coyote time is 0.10 s and the input buffer 0.12 s. A landing shows a squash pose, dust and a sound. A dash
  covers 96 units, or is a back-step standing still; Jump during it makes a 4.5-tile long jump. Collision works per
  height level with corner sliding. The blob shadow shrinks with height, and the camera follows the ground (not the
  arc) on whole pixels. The joystick, Jump, Dodge and Attack buttons drive it.
- **Original art** from `tools/art/build_topdown_proto.py`: 16-px tiles, cliff faces, stairs, water, props, and a
  **placeholder** body in S/E/N (the layered set is Phase 5). The side-view game and its rooms are unchanged.
- Tests: rules_tests `topdown_suite` (35 checks: movement, collision, jump, fall, height rules, depth-sort order and
  pixel snapping in the real view); perf_tests `_topdown` (mounts in 149 ms, 6.8 ms a frame). Screenshots and frame
  strips are in `docs/redesign/phase1/`.

## A rewarding first hour: techniques early, a faster Bone Forging, the story carries the floors

Research docs/research/player_motivation.md, items 3, 4, 5, 8 and 10 of its top ten; the first hour as built is in its
"As built" section and in docs/tutorial_order.md.
- **The first technique at Bone Forging 1, the second at the Weapon Hall.** Lu teaches Flowing Palm on his boat with
  the first breakthrough (The River Token's reward; its unlock realm is now Bone Forging 1). The skill ring and the
  Techniques page open at Bone Forging 1, so the palm takes its slot at once. The Weapon Hall, done, teaches the first
  art of the family in hand, from the arts the training halls and the library already keep: the jian's Cloudpiercing
  Stroke, the spear's Jade Thrust, fists' and gauntlets' Tiger Rush, the short blade's Reedcutter Slash and so on.
  Until the body has a Qi pool (Bone Forging 7) a technique costs no Qi, only its cooldown
  (`stats.json technique_cost.free_without_pool`, `CombatAuthority.breath_only`). A technique learned is its own
  moment (`moments.json` row `technique_learned`: its name, "tap it on the skill ring", the light gathering).
- **Bone Forging 1-4 take 600 / 900 / 1,200 / 1,600 progress** (was 1,200 / 3,200 / 3,200 / 3,200); Bone Forging 5-9
  take 3,100 each (was 3,200), so Qi Kindling 1 lands at 5.2 hours in balance_sim (target 5), with the chores moved to it. The River Token's
  endowed bar starts at 98% (was 92%), so the boat's fifteen breaths fill it.
- **Chapter 2 opens at Bone Forging 2, and the story carries every floor.** The Entry Trial has no "Reach Bone Forging
  2" step; the Willow Path (35% of a stage), the fair and the trial (20%) carry Bone Forging 1 to 2, and Fish-Gutting
  Fists (45%, and the title River Rival) carries 2 to 3, the Weapon Hall's realm. Strange Tracks (chapter 2's floor
  Bone Forging 2; the marsh path opens there too) starts as the mentor's note the moment the Weapon Hall is done. When
  the story does wait on a Level, the tracker's Next entry names a second way to close it: a lesson or side quest on
  offer, or meditation and body training (`QuestAuthority._floor_other_way`). A story quest that follows a lesson now
  waits next (`story_waiting`), so between Fish-Gutting Fists and the Weapon Hall the Next is the Weapon Hall.
- **Nine early quests cut, merged or rewritten.** Morning Tide is under way from waking, Aunt Ping's tea in hand and the
  hut's door open (no teas to hunt, no Bag to open first). A Quiet River (Return) is gone: the fourth lesson done, Guo
  has Crab Trouble at once. Ma's Delivery is one step (sell the net). Fists First asks five on the stump and three on
  the dummy (was 12 and 5). Crab Trouble wants three shells, which drop every kill while he wants them, and pays the
  Straw Sandals with the hat. The Willow Path has no stump quota (was 30): Flowing Palm on a boarlet, five boarlets and
  the herd's elite (a kill objective may now ask for an elite). A Disciple's Chores is a side errand: two spots, and the
  third is the grey itself, with a cache of two spirit stone shards. Eyes for Qi sits 20 s (was 60) and pays a
  ten-year Riverreed Ginseng. Mei Qing's Errand asks the grey hides of the Humming Token's boarlets, not copper ore
  (which needed mining), and they drop every kill while she wants them. The Weapon Hall asks five dummy hits (was 15).
- **Breakthroughs show what they gave, and the look changes.** Every realm step's moment now carries a card, "What the
  breakthrough gave", each number that rose before → after with its gain (Level, Max HP, Physical attack...). The
  character wears an aura by realm (`moments.json auras`: a jade ring at Bone Forging 1, motes at 4, a Qi glow at 7,
  on to gold at Cloud Stride), drawn behind the avatar from plain shapes (no new pose), still with Reduce motion; the
  card names it when a breakthrough changes it.
- **Tests.** `tutorial_order` walks from waking to Strange Tracks with no test shortcut: the story reaches Bone Forging
  2 and 3 by itself, the first technique comes at Bone Forging 1 and the second at the Weapon Hall, and on a play clock
  (`prologue_run.play_s`: the simulated time, walking, a look at each new room, reading) something new comes at least
  every 3 minutes to minute 20 and every 5 to minute 60 (invariant 14); it prints the timeline. `prologue_run` no
  longer grinds to Bone Forging 2. `rules_tests` holds the Next entry's second way. Screenshots of the technique moment
  and the breakthrough cards in `docs/ui_p5/early_game/`.

## Chores after power, early surprises, a gentle first fall

Items 6, 7 and 9 of `docs/research/player_motivation.md`.

- **Dailies, idle tasks and posts open at Qi Kindling 1, optional, and a missed day banks.** The sect board, the
  contribution shop, field-boss timers, the activity chests (new unlock `activity_chests`), idle tasks, offline
  seclusion, Keeping Post and insect netting opened at Bone Forging 5–7, before the first technique. They now open at
  Qi Kindling 1, each unlock row marked `obligation`. Earning Your Keep is a side errand that asks for any one mission;
  A Second Path completes with an idle task *or* one seclusion; Keeping Post is kept by the same character, which burns
  Fisher Wen's incense stick at its own post (or puts the game away), so no quest asks for a second character, and the
  Keep Post button no longer needs one. The First Current no longer asks for seclusion. Missed days bank
  (`account_rules.bank`): the board keeps unfinished missions and adds each missed day's, up to three days' worth
  (`QuestState.board_day`); a filled, unopened activity chest waits, and each day away doubles the next activity points
  up to three days' worth. `data_validation` checks P3, P4 and P5 (no chore before Qi Kindling 1; no main or guided
  quest asks for a daily mission or a second character; no main-story step, requirement or unlock waits on a chore);
  `rules_tests` plays the bank; `tutorial_order` holds that no chore is open or offered at any step of the walk, and
  `valley_run` takes the lessons at Qi Kindling 1.
- **Early surprises, each with a moment.** The first walk onto the Willow Path after the River Token turns up the
  Remnant Soul in a Ring (`fortune_deck` `first`: sure, meter or not; the three-hour meter paces every card after it).
  As The Willow Path is done a Spirit Fruit ripens on Willow Path West, once per character: its guardian alone at the
  room's Level, then the fruit (`CalendarAuthority.open_first_fruit`). The first monsters (crab, rat, boarlet, toad)
  have rare rows, a pearl and a manual page, marked `find` (rolled on their own `finds` stream), which play the
  rare-find moment. Common foes of the Reed
  Shallows and Willow Path West come as elites one spawn in twenty-five (`elite_chance`, their own `elites` stream).
  New moments: `fortune_card`, `first_fruit` and `elite_appears`.
- **A fall costs nothing before Bone Forging 5** (`death.grace_below`, `ProgressionRules.death_grace`): no progress,
  no injury or heart demon, and you wake whole. The revival page explains it in full on the first fall, then in a line.
## Deterministic playthrough suites

- **valley_run, prologue_run and tutorial_order play the same on any machine, under any load.** The run's clock was the
  wall clock (the account seed at boot, time of day, weather, herb ripening, respawn timers and cooldowns all moved with
  how fast the machine ran), and every run on the machine shared `user://test_saves_*`, `valley_cp` and `valley_work`.
  Now `Clock.simulate` pins "now" to a fixed start and `Game.tick` advances it by the fixed step; the seed is fixed; the
  enemy authority's fallback dice are seeded; every wait counts simulated seconds; each run keeps its saves and
  checkpoints in its own `user://test_runs/<suite>_<pid>/`, removed at the end (`--cp=user://valley_cp/` keeps
  valley_run's checkpoints for previews and `--from`). **The Lantern Run's deck** fought at Level 82 against a party
  that reaches it at Level 79-80 (chapter 17's floor): a plain blow took 10% of par HP, outside the 4-8% band, and a
  par party lost the crossing on 1 seed in 12; its foes now come at 79 (deck Lv 79-81), and 18 seeds keep 73%+ HP.

## Starter gear: a weapon from the start

- **The weapon slot is open from the start, and the first monsters drop weapons** (`docs/research/player_motivation.md`
  items 1-2). A new character fights bare-handed with the slot drawn empty, not locked (Character and Bag pages); Uncle
  Guo's Fists First hands out his old Training Gauntlets, worn at once; the `weapons` unlock moves to that lesson and
  the smiths sell weapons from then on (the weapon Dao stays with the Weapon Hall). The first kill in the Reed Shallows
  always drops the first weapon, a Training Short Blade, with a "Your first weapon" strip, its beam and the equip
  prompt. The first rooms' foes (Mudshell Crab, Reedtail Rat, Old Snapper, Wild Boarlet, Mossback Toad) roll starter
  gear (`grades.json` `drop.starter`, 2% a kill, Old Snapper 25%): training gauntlets, jian, spear or short blade, or
  plain armour, at the par item Level with a weapon never above par quality, so balance_sim finds no weapon of the
  first rooms more than 2% over par attack; the character's first three pieces come by the 15th kill without one
  (`starter_drops`, saved). Tests: rules_tests `starter_gear_suite`, tutorial_order and prologue_run (the slot open,
  the gauntlets, the first kill's weapon and its equip prompt), balance_sim `_starter_checks`.

## Slain foes stay slain

- **Monsters no longer all come back the moment you re-enter a room.** Room load rebuilt every spawn point from the
  room data with no memory of kills (the respawn timers lived only in the loaded room). Now the character remembers
  each kill with the room (`rooms.<room>.slain`, saved), and a spawn point stays empty for its own time in game time
  (Clock), so time away counts: a common foe 1–3 minutes (its spawn's pace x6), an elite at least 10 minutes, a boss
  its own long timer (a field boss its account-wide one), so no boss returns on entry. Foes a quest step still needs
  (a kill count, Crab Trouble's shells) keep their quick pace. While you are in the room a foe returns only out of
  view. The Vigil's and balance maths keep their own `respawn_s`. A beaten boss also no longer returned after a loot pickup.
## Gauntlets are worn on the hands

- **Every gauntlet draws on both hands, in every pose.** The gauntlet family had no avatar look (its appearance was
  "none", the bare-fist look), so the ten gauntlets (Training to Lanternsteel, and the Stone Drum Gauntlets) showed
  only in their icons. `tools/art/bake_gauntlets.py` now draws weapon look `gauntlets` over the body's own hands in
  all 17 catalog actions, both facings, frame for frame: a steel fist shaded from the hand's tones, a bronze rim at
  the wrist and a cuff on a bare forearm. Each pixel sits just over the body layer that draws that hand (z 12, and
  z 92 over the jab and lotus fists), so the torso, sleeves, head and hair hide it where they hide the hand; a
  gauntlet still punches. `engine_tests` checks every gauntlet is drawn in every frame of every pose on the body;
  review sheets in `docs/mockups/gauntlets/`.

## Consumables show what they did

- **Every tea, pill, herb, core, draught and food says what it did.** Drinking the Herbal Tea (Granny's Remedy) showed
  nothing: `item_used` carried no result and nothing drew it; the tea heals over 5 s, only a fifth at once, and at full
  HP (as the prologue's player is) it changed nothing; the log that could have said so is not revealed yet. Now
  `InventoryAuthority.apply_use` reports each effect (`item_used.effects`, `gains`); the world floats the heal over the
  player ("+21 HP", or "HP already full"); the HUD writes "Herbal Tea: +21 HP over 5 s" (shown before the log is
  revealed), shows the heal still to come on the HP bar, and puts the tea's icon with its seconds left in the status
  row (buffs and statuses show their time too). Screenshots in `docs/ui_p5/guidance_fix/`.
## The equip prompt; the tracker at Bone Forging 3

- **A better piece offers itself.** Picked up or received, a piece that beats the one worn in its slot (an empty slot
  counts as worse) and can be worn now shows a small card at the right of the screen for 10 s (`EquipPrompt`): its
  icon and name, the gain the Bag's card names first and Combat Power (the same `StatRules.equip_change`, through
  `InventoryPage.card_rows`), Equip (the equip intent) and ×. It stands clear of the HUD's controls, the purse and the
  clear zone, only its two buttons take a tap, several wait their turn, and with Reduce motion on it does not slide.
  Screenshots in `docs/ui_p5/starter_gear/`.
- **At Bone Forging 3 the tracker leads to the Weapon Hall.** With Fish-Gutting Fists done, the next main quest
  (Strange Tracks) waits on Bone Forging 4, and the story's Next entry, which only looked at main quests, sent the
  tracker and the direction mark to the hunt for it at Willow Path West; the Weapon Hall, the lesson Bone Forging 3
  opens, was on offer and nothing led to it. With no quest of the story to take now, a lesson on offer now comes
  before the Level (`QuestAuthority._story_next`), and one under way leads the tracker itself. The `tutorial_order`
  walk now spars Shen Lian before the Weapon Hall, as a player does, and holds after every step that the tracker and
  the mark lead where the story goes next (invariant 9).
## Codex page-completion rewards (decision 27, mockup 18's two seals)
- **Every collection page has two seals, each with a gift, claimed once for the account.** Seal I: every card filled
  (50). Seal II: every card studied through (500, an elite 200, a boss 100: `kills_to_master`), after seal I. Earned
  the kill the condition first holds (a toast), claimed by the Account authority's `claim_collection_seal` from Claim
  on the book page (the seal stamps in, a toast lists the gift), saved as `collection_seals`. Gifts are data
  (`tools/data/economy.py`, `account_rules.json` `collection_seals`): one small defensive or finding stat for seal I,
  healing received, knockback resistance or mastery gain and a Bestiary Leaf of a page beast for seal II, every stat
  given to each character by `StatRules.rebuild` (source `collection:`); no attack or damage stat. The Codex draws
  both seals on the page head, the page's seals with rule, gift, bar and Claim, a filled card's bar on to its seal II
  mark, and Contents the seal to come; it opens at a page with a seal to claim. Tests: `rules_tests`' codex seals
  (earned exactly on the kill, once, in order, saved and loaded, gifts through the stat rules), `balance_sim`'s
  per-stat budgets and par Combat Power with every seal (+0.9% at Level 30, +0.6% at 99, +0.7% at 165; at most 3%).
  Screenshots in `docs/ui_p5/records/` (`codex_seals_*`).

## Guidance: the sect's first step, the story's Next entry, the Quick-use slot, the hut door, the attack button

Found on the Android build; each fixed at its cause and held by the walks (docs/tutorial_order.md).
- **After the sect choice the sect's first quest is under way.** The choice was recorded (sect, rank, token, method),
  but nothing took it up: the Entry Trial, which the fair's last words send you to, waited for Bone Forging 2 behind
  three unlocks, so at Bone Forging 1 no quest was active and the tracker went blank. The Entry Trial now starts the
  moment a sect is chosen; its first step, Bone Forging 2, leads to a hunting ground ("➤ Hunt at Willow Path West"),
  and the lessons it teaches still open at Bone Forging 2. The Willow Path likewise starts once Lu has handed you the
  River Token (it started at the breakthrough a moment before, pointing ashore while the boat was still shut), and an
  auto-taken lesson now unlocks its systems in the same pass (`GameAuthority._after_pass`).
- **Between main quests the tracker shows the story's Next entry, never a blank plate** (`QuestAuthority.story_next`):
  who gives the next quest and where ("Next: Fish-Gutting Fists · Talk to Shen Lian", ➤ Fairground), or what it still
  waits on and where to get it: another quest first (followed back through requirements and unlock triggers), or a
  Level ("Reach Level 21 (Qi Unfurling 3)", ➤ Hunt at Bend Shore: a field whose foes suit the character's Level, the
  ones P12's gap names). It is a tracker entry like the others, so the P1 direction mark, the P5a plate, the go button
  and the world map lead to it; the story's quests and lessons are always tracked (a full tracker drops a side quest).
  Race to the Tower's bell step threw a script error in the tracker (an objective by object id); fixed.
- **The Quick-use slot is on the HUD.** P5a rested the healing slot outside a fight, so Granny's Remedy asked for a
  slot the player never saw. At rest it is now drawn while a quest step asks for it (glowing, named "Quick-use"; a tap
  on the empty slot opens the Bag) and while it holds something to drink, clear of the open fan. The steps say what
  the player sees: "Bag: put Herbal Tea in Quick-use", "Drink a Herbal Tea: tap Quick-use".
- **The first quest cannot be skipped.** A quest whose step is to leave its room (Morning Tide's "Step outside") keeps
  the room's ways shut while it is on offer and until the steps before it are done, and says which on the door and on
  a try: "Before you go: Open your Bag" (`QuestAuthority.room_hold`, `WorldAuthority.portal_state`). The hut's door
  stays drawn as itself, shut. Taken pickups stay taken on a reload (Aunt Ping's teas came back).
- **In a fight the attack button attacks.** A herb, pickup, person or door in reach took the button whenever no foe
  was aggroed within 400 px (a foe walked up to, or one between blows, did not count). One rule now
  (`HUD.attack_first`): in the P5a fight state (a foe within the fight range, one engaged anywhere in the room, held a
  moment after) the button attacks and the offer waits in ring 2's context slot with its own glyph; at rest the context
  takes the button (mockup 02). Auto-hunt attacks directly and is unchanged.
- "Ready to hand in" no longer flashes for a quest that completes itself (the fair).
- **Tests**: `tutorial_order` holds every step to three more invariants (the control a step names drawn on the real
  HUD, no room left early, the attack button in every fight beside the Reed Shallows' herbs) and, with `valley_run`
  over every main quest of Acts I–III, to the story's guidance (`prologue_run.story_guidance`: the tracker never
  empty, every target a real room the player can walk to, the mark toward it, the Next entry's giver or hunting ground,
  the sect's first quest right after the choice). `rules_tests`: the Next entry (a giver through a chain, a Level),
  the healing slot at rest, the attack-first rule. Each fix, reverted, fails its suite.
- **Screenshots** from a new character (and one `valley_run` checkpoint) in `docs/ui_p5/guidance_fix/`.

## Tutorial order: the first fight, foes' HP bars, doors and quest talks (docs/tutorial_order.md)

Found on the Android build from a new character; each fixed at its cause and held by a new suite.
- **The first fight comes after the HP bars.** The East Gate to the Reed Shallows opened with Fists First, while the
  HP bar comes with Granny's Remedy and the foes' HP bars with Crab Trouble, so a player who went to Uncle Guo first
  fought crabs and rats with neither. The gate now opens with Crab Trouble (the quest that sends you there, after all
  four lessons); Guo's lines say so. Old Ma's and Granny Liu's Trade waits for Coins and Shops (buying needed it and
  the purse was off the HUD).
- **Foes in a fight show their HP bar.** Beyond the reveal above (not a regression of the P5a labels), a foe showed
  its bar only once hurt, so a Reedtail Rat biting you showed none. A foe now shows it from the moment it turns on
  you (`EnemyState.in_fight`, `EnemyView.shows_hp_bar`).
- **Every way into a building shows a door.** Old Ma's store drew an open counter and no door. The store's art now has
  its own plank door under a blue shop curtain in the right bay (`tools/props/defs_buildings.py`); every building prop
  names its doorway (`door` in `data/prop_art.json`) and `Room.building` stands the door portal in it (the Fisher's
  Hut's was 44 px off its door; the harbour's and the port's inns and shops too). A door's arrow and plate draw above
  the facade (they were hidden behind the building). The painted bell towers of the retreat rooms get a door at their
  foot, the Cloud Library's door moved onto the Sword Court hall's doors, the Beast Trial Grove's way stands clear of
  the bell tower, and the Wardens' Hall is a house with a door instead of a watch tower. `data_validation` holds every
  room to it (`PortalView.entrance`).
- **Taking a quest ends the talk.** The dialogue page talked again after an accept and stayed open on a shop, a gift
  or a farewell. `choose_dialogue` now hands back a conversation only when the same person has the next quest to give
  or take back (`QuestAuthority._then`); otherwise the page closes. Every quest-giver alike.
- **Tests**: `tutorial_order` (new) walks the Prologue and the start of Act I fists-first on the real dialogue page and
  checks after every step and tick: no room with foes in reach before the HP bars, every foe in a fight showing its bar,
  a door at every way into a building, the talk closing after each quest taken, each step's control on the HUD when its
  quest is taken. `prologue_run` is split into steps both runs share; `valley_run`'s page check is stricter.
- **Screenshots** from a new character in `docs/ui_p5/tutorial_fix/`.

## P13b · The Techniques page (docs/technique_plan.md "As built: P13b")

Built to the approved mockups 06 (tree, tree learned, lost arts; decisions 11, 18, 19).
- **One tree a tab.** The page is the whole screen: a rail of element seals (Time locked until its Level, then Lost
  Arts and Secret Arts), the chooser, the tree and the reading on carved jade-teal panels, the loadout dock below. A
  tab lays out the element's whole tree, every family side by side with its rings, notables, keystones and the Dao
  arts at its gate, on the element's chart; drag to move along it, tap a family to go to its arts, **Learned** to go
  from one learned art to the next.
- **The reading.** A chosen art shows your character in its pose, its numbers, its prerequisites ticked and crossed,
  the cost, and **Learn · N Realisations**: an art one passage out takes the passage with it. A learned art shows its
  mastery, its slot, Slot or Unslot, Rank up and Let go (its Realisations back); **Let all go** resets a tree.
- **The Dao bar follows the tab**: the free hand shows the tab's element Dao, a weapon its weapon Dao.
- **Lost Arts** is an album, one leaf an act: found arts pasted in, a manual you carry marked Unread with **Read**,
  every other leaf sealed alike and only counted (decision 19).
- The Inner Arts and stances are worn from the dock's drawer; the Secret Arts keep Concealment's false realms.
- **Tests**: `rules_tests techniques_page_suite` (layout, tabs, Learn and Let go, Read, decision 19 on the page, the
  Dao bar); `perf_tests` drags the biggest tree. Screenshots in `docs/ui_p5/techniques/`.

## P13a · Techniques at scale, the data (docs/technique_plan.md)

The techniques of Acts I–III are written, 3,171 in all: every weapon family and cultivation path has hundreds of arts,
each element grows a tree of its own, and the lost arts are found only by finding them. The page that draws the trees
is P13b; today's Techniques page is kept and draws the new arts' emblems.
- **The grammar in data** (`tools/data/technique_grammar.py`, `technique_gen.py`, `technique_hand.py`): an art is a
  FORM (24) × FAMILY (12 built, 16 planned) × ELEMENT (11) × PATH (five and the orthodox) × RING (13). The forms carry
  the shape and the line, the element its verb (Water pulls, Wood blooms, Formless strikes 10% harder with no verb),
  the path its rule and cost, the ring its grade, reach, extra targets and effect tier. Rows are baked and compact
  (`techniques.json`, 974 KB): a row keeps only what its form, ring, element and family do not give it. Every art
  plays its form's effect (the technique animations, decision 23); a keystone plays its template's.
- **Counts**: the trees of v1.2.x hold 1,773 arts (the plan's 1,768 and today's five twin cells): 1,661 in the cells of
  Acts I–III and 112 hand-named keystones; beside them 38 Dao arts and 52 lost techniques (62 lost arts with the Inner
  and Secret ones); the later acts' 1,308 arts are written and locked behind their act. Per tree 192 or 193 (Space 40);
  per family 138 own arts in Acts I–III (the free hand 142); per path of the cells: orthodox 889, Body 152, Blood 150,
  Buddhist 159, Poison 149, Confucian 162; Act I 797, II 468, III 508.
- **Names** from the lexicons only, at most 28 characters, unique, never another thing's name, and checked against a
  146-entry denylist exactly and within two edits: Backwater Swallows, Nightshade Riptide Net, Pine-Needle Burst,
  Scholar's Ghost-Light Shaft; keystones such as Hundred Springs Rising, Drums That Beat Themselves, Pyre That Answers
  Twice.
- **Today's 56 arts** keep their ids: 47 in cells (five cells hold two), five on Dao trunks, four become lost arts.
- **The trees** (`TechniqueTreeRules`, `ProgressionAuthority`): eleven trees (nine elements, Formless, Space from ring
  7; Time from ring 9 waits for v1.3) of twelve sectors in four kin groups, a passage a ring, a notable at each act's
  edge, four keystones an act. Realising a node costs Realisations (Level + 2 × major breakthroughs + Dao tiers +
  mastery tiers past 2); an art's node teaches it. Free out of combat node by node from the leaves, one free reset a
  tree each great realm, then a Clear Heart Incense (the sect Mission Halls). One heavy art (a keystone or a lost art)
  to a ring of four slots. Saves from before the trees light the routes to the arts they know, once.
- **Lost Arts** (roadmap decision 19): found only in the world, never hinted at. Steles (the insight stones, with a
  Rubbing Kit from the Stoneford General Store and a Dao tier, an hour or a season), 28 old writings in 24 rooms, six
  masters' last lessons (a choice beside what they already say), ten foes' manuals (rolled like named rows, sure by the
  pity-th kill, only while the art is lost), four quests, the auction, and Lu's journal (twelve more pages) for the
  Ferryman's Oar. The board counts an act's lost arts and shows a found art's full card; nothing names, draws or places
  an unfound one. Found twice, an art is a Manual Page.
- **Balance**: techniques still grow only through Might. The trees feed the one damage bucket (+15% at most by Level
  99, +25% by 165) and cut Qi cost within the 30% cap; the grade is +0/+10/+20%, flat from ring 3; the par main art now
  follows the grammar's Arc at the band's ring, and with its tree route lands on the plan's line within ±7% from Level
  20 to 165 (1.45 at 20, 3.51 at 60, 4.12 at 99, 4.71 at 165; +10% at 200).
- **Emblems**: today's 56 stay baked; the other 3,115 are composed in the game from one atlas of 361 layers at 64, 48
  and 32 px (466 KB), about 0.6 ms each at 64 px and then held. The icon build writes the same bytes twice.
- **Tests**: `data_validation` `technique_suite` (counts, filled rings, rules 1–3, 5 and 6 of §3.6, names and the
  denylist, reachability, poses) and `lost_art_suite`; every art resolves to an emblem; `rules_tests` `tree_suite`,
  `tree_migration_suite`, `lost_arts_suite` (with the no-leak board) and `tree_queries_suite`; `balance_sim` the
  technique line and the trees' share; `perf_tests` the file's size, v1.5's 4,350 rows read and filled in, the trees'
  index, emblem composition and the Techniques page; `contract_tests` the trees' intents and words.
- **Fixed on the way**: an art with no pose (Blood River Slash, Venom Needles) played "<null>"; it now plays the
  weapon's third stroke.
## Technique animations (docs/roadmap_master_ui.md, decision 23)

- **An FX animation library**: one frame-by-frame pixel-art effect per technique form, the 24 of
  `docs/technique_plan.md` §3.2, drawn by a deterministic generator (`tools/art/fx/`: `fxpix.py` the palette-index
  rasteriser, `elements.py` the eleven element palettes and flourishes, `forms.py` the 24 drawers, `build_fx.py` the
  build) into `art/fx/<form>.png` and `data/fx_art.json`. Slash arcs with smear frames, three-cut flurries, thrust
  trails with a point flash, lunges with afterimages, low sweeping crescents, crescents that form and launch, volleys
  from a muzzle flash, rain that falls and splashes, pillars that rise and flare, a crest that curls and travels,
  bursts that pop into a ring, seekers that gather and fly, a blade that spins out and is called back, snares that
  rise and knot, a counter's guard flash, a ward's dome closing, a chorus's sound rings and notes, blink afterimages
  and the arrival cut, a plunge's crater and cracks, the released sword's streak, an orbit of swarm blades, a seal
  stamp that falls and slams, a domain drawing itself, and an echo's ghost strike; four projectile loops (arc, volley,
  seeker, return).
- **Every element reads as itself** on every form, by a palette swap and its own flourishes: water in droplets and
  ripples, wood in leaves, fire in flame tongues and embers, earth in rock and dust, metal in shards and glints, wind
  in streaks, thunder in forked bolts, soul in thin rings and wisps, formless in plain ink flicks, space in stars
  over a dark rift, time in clock ticks and a half-there ghost of the frame before. Colours sit on the element
  colours and the Style A emblem ramps, so an art's effect matches its icon.
- **Three richness bands** per form for the vfx tiers 1–2, 3–4 and 5–7: thicker strokes, more particles, extra
  layers; the sprite itself grows 1×, 1.5×, 2× for the forms sized by tier, never past a strike's reach. 28 sheets,
  3.6 MB; a rebuild is byte-identical (`build_fx.py --verify`).
- **Wiring** (presentation only): every technique carries `vfx.anim` (its form) and `vfx.pose` (the catalogue action
  the effect is timed to; `combo_1` / `combo_3` for the wielded family's step that `meditate_burst` and a null
  action resolve to), written by `tools/data/technique_anim.py` from the plan's form table (a row P13 tags with
  `form` takes that). `World._cast` plays the sheet through a new `FxLayer` kind, `anim`, timed so its impact frame
  lands on the pose's hit frame (`attack_started`'s `windup`), mirrored for the facing, at the element's row and the
  tier's band, sized to the hitbox: a ring form snapped down so it never passes the true reach (a procedural ring
  still marks the edge), a wave's crest travelling the reach, a rain tiled across it, a pillar or a seal on the foe in
  reach. A technique's Qi bolt is drawn from its form's projectile loop. Reduce motion plays the calmest band and
  Battery saver the middle one at most; the sheets never fill the screen, so the flash limiter stays with the tint.
- **Preview**: `--cast=<technique>[:t]` now also holds the pose the cast would play on the avatar, resolved as the
  timeline resolves it, and lands its hits at the hit frame; with `--capture` the effect and the pose step a sixtieth
  a frame and the simulation holds still from the cast (`World.sim_frozen`, `FxLayer.fixed_step`), so a shot lands on
  the frame `t` names whatever the renderer's pace and shows the effect on the pose, not a boarlet's counter-attack.
  `--load=<folder>` now copies into `user://loaded_<folder name>/` rather than one shared `loaded_copy`, so two
  previews of different checkpoints run at once no longer clobber each other's copy.
- **Review**: `docs/mockups/fx/`: every form × element at each band's impact frame at 1× and 2×, a strip of every
  frame per form, the projectile loops, and in-game captures of one technique per form at four moments of the cast
  from the `ls6_end` checkpoint (its README lists them).
- **Tests**: `data_validation` `_fx_art_suite` (the 24 sheets exist at the size their spec says, a hit frame inside
  each, known anchor and size rules; every technique's animation is a built form and its pose an existing action or
  a combo alias every weapon family resolves); `rules_tests` `moments_suite` case 15 (bands by tier and under Reduce
  motion and Battery saver, element rows, half-step scales, an anim's facing, delay, length and row, a form without a
  sheet); `contract_tests` keeps `anim` in `FxLayer.KINDS`; `perf_tests` casts through the same path.
- **Not done, by design (`AGENTS.md`)**: no new body pose. Every form maps to an existing action; two poses would
  serve some forms better and are listed as follow-ups in the report (a true plunge from the air, a stance hold for
  Counter and Ward).

## Moments (docs/roadmap_master_ui.md, P6)

### P6e · The escalation curve
- **Every technique has a `vfx` block** (`techniques.py`): its tier, 1 to 7, is the band of the realm that teaches it
  (the valley's Common 1, Earth 2, Heaven 3; the Azure Expanse 4; the Lantern Star Field 5; 6 and 7 wait for their
  zones), its shape what it draws on cast, and its particles the hit spark's style. Today: tiers 1–5 hold 16, 22, 9, 1
  and 8 techniques; strike 15, bolt 11, ring 9, domain 9, wave 5, pillar 5, rain 2.
- **A technique's hits grow with its tier** (`moments.json` `vfx_tiers`, §5.2): the spark's count, size, reach and
  white core, the damage number's size, a ring at the caster's feet from tier 2, echo waves inside an area's edge from
  tier 3, one small shake per cast on its first hit from tier 3, and from tier 3 a wash of the element over the screen
  for 0.4 s. Tier 1 is today's look, so the first techniques do not change; a basic blow stays tier 1, and a
  companion's blow of a technique draws a tier lower.
- **Shapes drawn at the true reach** (§5.3–5.4): a slash that grows with the tier; a talisman wave along the reach; a
  ring at the reach with echo rings inside it, never beyond; a rain of streaks over the hitbox (`rain`, new); a pillar
  on the foe in reach; a ring and motes round the caster for a buff or heal; a bolt is its projectile.
- **Sparks by family and element** (§5.6): the brush's ink drops fall, the bell's and flute's (and Soul's) rings
  spread, fire's embers rise and flicker with a pale-gold heart, metal's, ice's and thunder's shards fall; the rest
  keep their squares.
- **Multi-hit numbers** (§5.5): the hits of one cast on one foe rise one after another, 18 px and 0.06 s apart,
  swaying left and right, six at most, and three or more add up to a total in pale gold a size up.
- **Large numbers** (§5.7): from 10,000 a number is written in three figures, 12.4K, 124K, 1.25M (`UiKit.short`, the
  style guide's §4 helper, which the P4 pass landed beside P6e and both now share). Damage numbers still follow
  Settings › Damage numbers.
- **The flash limiter covers tints** (§5.10): a technique's screen tint shares the one-a-second limit with every
  flash, is 0.3 as strong with Bright flashes off, and does not play with Reduce motion or Battery saver, which also
  thin sparks to tier 1's and tier 2's counts.
- Preview: `--cast=<technique>[:t]` draws a technique's cast and its hits on the foes in reach, submitting nothing.
- **Tests:** `moments_suite` case 12 (the tier rows by technique, a spark carrying its tier's count and size, a
  companion a tier lower, the spark styles, a tint under the settings and the limiter) and case 13 (three hits stacked
  18 px and 0.06 s apart on alternating sides then a total; seven hits show six and total seven; two, no total);
  `moments_data_suite` checks every technique's tier against its realm's band and grade, its
  shape and style, and that every shape draws `FxLayer` kinds; `perf_tests` plays the crowd under the major
  breakthrough and again with a Sword Swarm and a Cursive Storm cast each tenth of a second (each striking as many foes
  as many times as it does), inside the frame budget and the FX cap, and prints the view's share (MomentView.advance
  about 0.08 ms a frame; the whole moment, drawn, about 1–2 ms on a desktop).
- **P6 closed:** the screenshots are in `docs/moments/` (its README gives each one's checkpoint and flags); roadmap rows
  M5–M9, M22, M23 and M25 are Present, M6 with P9's intro pan and epithets still to come, and M24 stays Partial for
  P4's biome palette rule.
- **With the P4 pass merged:** a moment's counted line takes its "_one" twin (`plural` in a text source, through
  `Tx.plural`), so one bolt is "1 bolt"; the tribulation card's summary reads "Waves 3 · Bolts 9 · Struck 2"; and
  `UiKit.short` is the style guide's one helper.

### P6d · Rare finds, story beats and trials
- **A rare find** (`rare_drop`) is seen from across the room: a tall beam in the piece's colour stands over it and breathes
  until it is picked up, and a strip names it in its grade or quality colour under "A rare find", with `rare_chime`
  and a short buzz. Finds within 1.5 s share one strip (three names, then "+N"); in a fight it is a toast. What is
  rare is data (`moments.json` `rare`): a Perfect or Relic piece, a legend piece, a spirit animal's book, a treasure,
  and 49 named drops (every boss's unique drop and first-defeat reward, every set piece, every legendary chain piece).
- **A chapter closes** (`story_beat`): when the main quest that ends a chapter is handed in, after its dialogue page
  closes, thin ink bars close in and a band writes the chapter over the quest's name, "The chapter closes" under it,
  with the bell. `moments.json` `chapter_ends` names the closing quest of each of the 23 chapters (the Prologue and
  1–22), read from the quests.
- **A trial opens** on a band in pale gold with the bell (it was red text over the room), and ends when you leave.
- **Tests:** `moments_suite` case 4 on the real rows (after a major breakthrough: the Dao tier, then the title and the
  rare find by arrival), case 14 (the rare rule), two finds sharing a strip, and a chapter's close waiting for its
  page; `moments_data_suite` checks every rare find exists and one quest closes each chapter.

### P6c · Bosses and the loot fountain
- **The boss intro** (`boss_intro`): the first time a boss turns on you in a visit, two ink bars close in top and
  bottom (under the HUD, so its controls stay live), its name is written large with its Level under it, and war drums
  and a falling gong sound (`boss_sting`, new; captioned). The boss does not wait for it and nothing locks, so you keep
  control; until P9 gives the bosses epithets and lines, the Level stands in. It never plays twice in one visit.
- **The phase card** (`boss_phase`): the fight's stage as a gold numeral on an ink band under the boss bar, with the
  shake and the roar it had; one that would come late drops silently.
- **A boss's fall** (`boss_defeated`, `field_boss_defeated`): a pale-gold flash, its name on a band with "Defeated", and
  for a clean dungeon kill the Untouched line (it takes the Untouched achievement's toast into itself); `boss_fall`
  (new) sounds. The HUD's field-boss toast is now the row's fallback.
- **The loot fountain** (`loot_fountain`, §5.8): a boss's, a field boss's, a chest's, a Trial Tower floor's or a rift's
  drop leaves the drop point one piece after another and arcs to where it really lies, higher and longer the more
  there is (capped); rare pieces go last so they land on top, and the first rings `rare_chime` (new) as it lands; a
  boss's coins burst as six and close into one, with a pale-gold flash at the drop. A foe's or a jar's drop bounces as
  before, and so does every drop with Reduce motion. `LootView.launch` flies them.
- **`loot_dropped` says where the loot came from** (finding 6), the one simulation edit of P6: `source` is enemy,
  elite, boss, field_boss, fled, jar, chest, rift or tower, a payload key and nothing else.
- A moment that takes an event into itself now takes back the HUD's toast for it too (a breakthrough's unlock, its
  tribulation, the Untouched achievement). The pill cloud rings `rare_chime`, not the breakthrough gong.
- Previews: `--hold=t[:row]` holds a real moment at t, `--defeat-foe[=s]` defeats the first foe through Combat with its
  real drop, `--foe=` takes an HP share, and `--room=` works with `--load-slot`.
- **Tests:** `moments_suite` plays Big Toad Tan's den for real: his first aggro opens the intro and the second does not,
  his 49% opens the phase card, a phase cuts the major breakthrough (case 5), leaving the den ends his intro with no
  toast (case 8), his clean fall takes the Untouched line, his drop says `boss` and flies (and only bounces with Reduce
  motion), a jar's does not fly. `moments_data_suite`: a numeral for every boss phase, the fountain table.

### P6b · The breakthrough and the progression cards
- **The major breakthrough, as mockup 05 draws it** (`breakthrough_major`): the world darkens round you and the HUD
  recedes, sixteen motes gather into you, a column of light rises and three rings open at your feet (0–0.6 s); the
  great realm's name is written on an ink band in one brush stroke, "BREAKTHROUGH" over it and the step under it, and
  the stage is pressed on in a vermilion seal (0.6–1.4 s); the stats that rose climb in one after another, with the
  tribulation you weathered on a card beside them and what the new stage opens on a chip (1.4–2.4 s). It holds to
  3.6 s and fades by 4.0 s. Input comes back at 1.5 s; a tap before then skips to the full frame. Its sounds are the
  gong and chimes, then a brush stroke and a seal (both new), then the unlock bell only when something opens.
- **A minor breakthrough** writes its step and the Level it gave on a slim ink strip, with any unlock on a chip, and
  keeps the guzheng run (no shake). **A failed one** darkens the world a moment and says why and how to recover
  (`failure.<id>` now has words for all seven causes, finding 8), and after a tribulation how many bolts struck.
- **The tribulation** opens on a band over a shadowed sky that stays while the rite lasts; its storm is laid again
  every 5 s until the result, not once for 6 s (finding 10).
- **The silent milestones speak** (finding 4): a Dao tier (its line from the Dao's tiers, in the element's colour; a
  sixth tier on the large band), a craft's new rank, a guild rank with its title, a body tier, an earned title with its
  bonus and a seal, a spirit animal's new form and an awakened weapon in its grade's colour each have a strip. In a
  fight the celebration cards become toasts; the HUD's old toasts for them are gone.
- A level gained alone rings a short gong (new) instead of the guzheng run.
- **Reduce motion** (Settings › Accessibility, off by default): no camera moves or shakes, bands and cards fade in
  instead of wiping and sliding, bursts thin to tier 1's particles. Bright flashes off leaves a flash or a screen tint
  at 0.3 of its strength. One flash or tint a second from every source (the flash limiter).
- **Art and sound:** the ink band, a dry-brush stroke drawn by `tools/ui/build_ui_hd.py` (`art/ui/hd/ink_band__normal.png`);
  `brush_stroke`, `seal_press` and `gong_short` from the synth. New FX kinds `pillar` and `converge`; `spark` takes a
  count, size and a falling `shard` style, `ring` a count. Strings for every great realm's name, every craft, the
  stat labels and the cards.
- `--breakthrough[=t]` takes the character over its next step through the progression authority and holds the moment
  at t, for screenshots of the real stat rise.
- **Tests:** `moments_suite` runs the gather, the skip, the lock (F4: never more than 1.5 s), pages, fights, the
  settings and the held tribulation on the real rows, and a real minor breakthrough and a level gained by meditating;
  `moments_data_suite` checks the new text sources, the ink band and every great realm, craft, failure and stat string.

### P6a · The table and the view
- **`data/moments.json`** from the new `tools/data/moments.py` (run by `build_data.py` before the contract): one row per
  moment kind with its trigger event, filters, priority, duration, input lock, queue rule, layers, art and a sample
  payload, and the settings the view plays them by (`docs/moments_design.md` §3). The first eleven rows carry today's
  effects: the breakthrough channel, the breakthrough (every one, until P6b gives the major one its own row), a failed
  breakthrough, the realm phenomenon's clouds, the tribulation's storm, a level, a body level, an awakened weapon, a
  Halo or Soul pill, a boss's phase and a trial opening. The escalation curve's seven tiers are in the file too.
- **`MomentView`** (`scripts/presentation/moment_view.gd`, mounted with the world by `main.gd`) plays the rows:
  it gathers the events of one pass and resolves them together, so a breakthrough takes its level and its unlocks
  into itself; world layers run on the row's own clock; screen parts take one slot by priority, wait for pages, cut
  or queue, go stale into a toast, and end on leaving a room. `MomentRules` holds the matchers, the rare rule and the
  text and colour sources. Neither writes game state (`contract_tests`), and the headless suites run without them.
- **Moved out of `world.gd`, the HUD and the audio director into rows**, with nothing to see changed: the
  breakthrough's spiral, name, shake, sound and buzz; the channel ring; the failure line; the phenomenon's clouds and
  storm with the townsfolk's words; the level and body-level lines; the awakened weapon's wave; the pill cloud; the
  boss phase's shake and roar; a trial's name. The one change: **the doubled sounds play once** — a major breakthrough
  no longer rings `breakthrough` twice (once more for its clouds), and a tribulation no longer thunders twice; a
  breakthrough's level no longer rings its own chime under the breakthrough's. The pill cloud takes its quality's
  colour (Halo orange, Soul pale violet) as the grades do (M24).
- **A camera rig in `world.gd`:** `add_shake(s, amp)` is the one writer of the shake (the hazards call it too), and
  every shake stops with Screen shake off; `hold_camera` eases to a point and back for later rows.
- **The Damage numbers setting works** (finding 2): off, no damage number rises; Miss, Immune, Evade and Parry still do
  (`FxLayer.label`).
- **The contract:** `level_changed` and `room_event_started` join the catalogue; the payload keys of every event a
  moment reads are declared, and `contract_tests` checks every emit site names them. `FxLayer.KINDS` lists its kinds.
  `UiKit` names the three colours that left `world.gd` (`HEAVEN_CLOUD`, `HEAVEN_BOLT`, `BODY`).
- **`--moment=<id>[:t]`** plays a row with its sample payload for previews and screenshots.
- **Tests:** `data_validation` `moments_data_suite` (every trigger, merge, payload key, FX kind, sound, string, colour,
  anchor, lock and timing; the curve rises); `contract_tests` (declared payloads, `FxLayer.KINDS`, the moments scripts
  read only); `rules_tests` `moments_suite` (every real row plays from its sample and ends on time; the gather and
  merge, the queue order, a cut, stale and full queues, pages and fights, a room change, the settings and the lock on
  fixture rows).

## P12 · Might (docs/research/stat_scaling_research.md §6)

A par character now hits about 130K with a plain blow at Level 99 and 531K with its main art (929K on a crit), with
460K health; 571K a blow at Level 120. Bone Forging keeps its numbers. The research's §6.8 lists what differs from its
proposal and the numbers measured on the valley_run checkpoints before and after.
- **Might** (`stats.json` `might`, a table for Levels 0–200): ×1.30 a great realm, ×1.17 of it at the major
  breakthrough and the rest over the realm's Levels; Bone Forging climbs only to ×1.05, so Qi Kindling 1 is the first
  ×1.30 step; ×1.10 for each advanced state, ×1.18 an Inner Heaven rank, +2% a World Genesis Level. It multiplies the
  character's three attacks, max HP and three defences (a `might` modifier, so gear and buffs scale with them), never
  max Qi or max Soul, and every monster's armour at its Level. The defence constant grows with the attacker's Might, so a
  same-Level cut is what it was.
- **The par character** (`stats.json` `par`, `StatRules.par` and `par_step`): a steady cultivator of the jian at every
  Level (gear three Levels behind at Fine, then Superior and Perfect, enhanced a Level a dozen; the Sword Dao and the
  main art's mastery by realm; an attack affix; the sets' damage%; crits), modelled in `stats.py` with the rules' own
  formulas and built with the real rules in `balance_sim`, which agree within 1%. The Codex's Realms entry shows it at
  your Level.
- **Monsters from par**: a normal foe has 3.5 par blows of health (never below today's) and a blow of 6% of par health
  after par's armour (8% under Level 20); under Level 10 the old curves stand. Elites ×6 health, ×1.5 attack. The twelve
  bosses have the par DPS of their Level times their par time (Big Toad Tan 46.7K at 90 s, the Nebula Leviathan 121M at
  300 s); a boss's plain blow is 15%.
- **The damage formula**: the energy multiplier becomes a Qi edge (1.00–1.30) on Qi and Soul blows only; one additive
  bucket of damage%, elemental power and (against elites and bosses) boss damage; a product of final-damage sources;
  three new stats (`damage_pct`, `boss_damage`, `final_damage`). Combat Power has no energy term. A damage-over-time share
  of an elite's or a boss's health is capped at 60% of the caster's attack a second. An ally struck by a foe stands
  behind its owner's armour.
- **Numbers**: `UiKit.short` ("18.2K", "136K", "1.27M"; units in `ui.num.*`) for damage numbers, pool bars of 100,000 and
  more, and every page number from ten million.
- **Chapter floors**: every main quest of chapters 2–22 asks its chapter's floor (Bone Forging 4 to Sphere Lord 2; new
  for chapters 16, 18, 21 and 22), floors only; the later acts' floors are recorded in `quests.json`. The quest log names
  the floor, your Level and the fastest ways there. The Copperjaw Box now follows The Tide Breaks, which opens Tinker
  Mei's bastion.
- **Conversions**: the Soul Lantern Ward shields 10% of max HP; a body technique short of QI spends the same share of max
  HP; rooms recommend the par CP at their middle Level and the Heaven Ranking's rivals take the par CP at theirs.
- **Saves**: an old save's health grows by the Might of its Level, once (character minor version 1).
- **Tests**: `balance_sim` gains the research's ten checks (par_hit, ttk, blow, boss_par, smooth, realm_step, cp_rec,
  digits, chapter_floor, pacing) and plays on to Sphere Lord 3 (133 h); `rules_tests` gains `might_suite`; valley_run
  gains the labelled par-up shortcut at each section start from Qi Kindling 1 and a labelled "par pace" for bosses
  (sized to 20 s of its own blows: the scripted fighter neither strikes with a main art at par nor dodges), and its
  checkpoints are regenerated. On them a Level 98 blow went from 2,850 to 85K and a normal foe's blow from 2.9% to 5.7%
  of health.

## The Copperjaw swarm's creature art (v1.2 Phase D)

- **The swarm has a sheet of its own.** `copperjaw_swarm` (`tools/art/creatures/copperjaw_swarm.py`, flying, cell
  128): eleven small copper beetles at three depths, each a copper wing-case oval with a seam and pronotum band, a
  chitin head, pale-gold jaws and, when its cases lift, two pale wing blurs, the cases flicking from beetle to beetle
  so the cloud buzzes. Idle hangs and drifts, walk streams forward with streaks, windup draws back into a ball inside
  a tightening copper ring (held), attack lances forward as a spearhead and bites on frame 1, hurt scatters the cloud
  with copper dust, death rains the beetles down onto their backs and fades. `copperjaw_queen` is the same cloud led
  by a large gold-cased Queen with a pale-gold crown. The swarm config (`stats.swarm`) names them as `art` and
  `queen_art`; `Game.pets.swarm_art` picks the Queen's once she has risen. The Swarm tab shows the cloud on the wing
  on a stage beside its numbers, and while the box is open clouds of beetles circle the bearer in the world (three at
  fifty beetles, five at thousands, the far half behind the body), drawn from the sheet. `data_validation` checks
  both sheets exist and fly; `--beetle-swarm` opens the box for previews. The review sheets (2x, 1x, 8x close-ups)
  and in-game shots from the `ls6_end` checkpoint are in `docs/mockups/creatures/copperjaw_swarm/`.

## P4b · Icons in Style A: the pipeline and the display (docs/mockups/icon_study)

- **The pipeline** (`tools/icons/`, README "How to convert a family"): `pix.py` gains the HD mode the study
  prototyped (`SCanvas`, `Frame`, 7-level bands, `PixelPainter` with its texture, rim-light and selective-outline
  passes); `palette.py` gains `Mat` / `mat7` / `M`, material kinds, and grade kits from Plain to Sphere (Sovereign,
  Will and Sphere are new). Each family module declares `ART`: 32 (legacy) until every icon in it has an HD drawing,
  then 64 (HUD glyphs 32). An HD family builds its icons at 1:1 plus native `@48` (techniques) and `@32` renders, and
  the manifest lists them as `<id>@<px>`. `--only <family> --review-dir` writes the family in the 76 px slot at 1x and
  2x and in context (a Bag grid, the HUD rings); `--preview-hd` shows an unfinished family in the game.
- **The study's twelve icons** are the first HD drawings, in their own families (weapons, armour, pills, herbs,
  minerals, beast parts, workshop, techniques, HUD), behind each family's `ART`, so nothing on screen changes until a
  family flips. The study's Style A library is folded in (the study now renders from the families); from Style B come
  the domed technique disc with a shadow under the mark and a glass crescent in more steps.
- **The display**: every icon is drawn through `SpriteCache.draw_icon`, at a whole-number scale of its art and on
  whole pixels, never filtered (review I2). Page slots are 76 px (`Page.SLOT`: a 64 px icon at 1:1, a legacy icon at
  2x) or 44 px in list rows (`Page.SLOT_SMALL`: 32 px); the Bag keeps the figure between its worn slots, with a
  five-column grid. The HUD takes an HD technique's native 48 and an item's native 32; a legacy technique shows at 2x
  in its ring, HUD glyphs at 32 (2x). The slot draws a soft grade halo behind Mystic items and above. The kit CSS and
  the kit sheet have the 76 px slot. A `ui_suite` rule checks every icon on every page, and `icon_draw_suite` the fit.
- **Pills in Style A** (`tools/icons/families/pills.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/pills/`): the 33 pills redrawn at 64 px with native `@32` renders for the HUD item ring,
  The vessel is now the kind of pill (a jar heals and restores, a footed bottle is taken at
  a breakthrough, a gourd is a draught, a round box remakes the body or a method, a paper wrap holds loose pills) and
  the grade its material and trim (a cloth cap, a jade plug, a silver cloud lid, a domed lid with a gem finial; ring
  handles and the glow from Mystic up; Law and Monarch in night steel and rose gold), driven from one table; the
  effect marks are shapes, and the legacy 32 px code is gone.
- **The HUD family is redrawn in Style A**: all 73 glyphs are HD drawings at 32 art px
  (`families/hud.py`, `ART = 32`), a pale-gold face with a lit edge, a warm shade edge and one highlight under the ink
  outline, shown 1:1 in the button rings and at 2x in the attack ring and on the menu tiles. The attack button's
  weapons share one diagonal frame and the shaft, blade and grip builders; the button glyphs share the book, bust,
  arrow and chest templates. The ASCII tables and the legacy glyph painter are gone. Sheets and in-game screenshots
  from the valley_run checkpoints in `docs/mockups/icon_families/hud/`.
- **Herbs in Style A** (`tools/icons/families/herbs.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/herbs/`): the 26 icons (16 herbs, 6 seeds, spring water, spirit soil, the dyed root and
  rice wine) redrawn at 64 px with native `@32` renders, each herb living plant matter on the clump of earth, stone,
  snow or water it grows from, with leaf ribs, petals, roots, fruit and stems. The nine species drawers take the age
  from one table and show it by form, never by colour alone: an older root is larger with more growth rings and root
  hairs (gold at a hundred years, gold to the tips at a thousand, pale as jade at ten thousand), an older lotus has a
  taller pair of petals and a fuller seed head, an older orchid a third bloom, an older soulbell a third bell, an older
  pepper two dark full pods; leaf veins turn gold at a hundred years, and a Mystic herb and above carries its spirit
  aura as stepped glow bands. The seeds share one hemp pouch with a tag stamped in the herb's colour and their own seeds
  spilled beside it. The legacy 32 px code is gone.
- **Techniques in Style A, as composed emblems** (`families/techniques.py`, `ART = 64`; the sheets and in-game shots
  in `docs/mockups/icon_families/techniques/`): the 66 technique icons are composed by one
  `emblem(element, form, family, grade, kind, path)` from parts drawn once and kept as tables, the technique plan's
  emblem grammar (§3.9): eleven element discs (the domed disc with the keyline under the mark), the 24 forms' marks
  with the family's weapon inset (sixteen weapons and the free hand's palm), rims for the thirteen grades and the four
  kinds (secret art, keystone, Dao art, lost art), the five path stamps, and hand marks for the arts off the grammar's
  line. A technique's row comes from `data/techniques.json` and its form from `FORM_OF`; a path art's mark takes the
  path's colour as well as its stamp. Rendered at 64 with native 48 (the HUD ring) and 32. The 66 hand-drawn legacy
  marks are gone.
- **Minerals in Style A** (`tools/icons/families/minerals.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/minerals/`): the 75 icons (9 ores, the spirit stones and shard, the fuel crystals, the
  stones and cores, the Act II and III materials, the two currencies, the six essence salts and the 40 beast cores)
  redrawn at 64 px with native `@32` renders, one language per kind: raw ore is its material in a chunk of rock with
  stone grain (copper nuggets, jade veins, a crystal cluster, a glass lump with its sand crust); the comet-iron ingot
  shows its three faces and the metal's sheen and reflection bands; a cut crystal or spirit stone has a table, crown
  facets and light pooling through its shade side; a polished stone is a disc, a stele or a chip with an inlay; a core
  is a sphere with a bright heart in its element's shape (a flame, waves, a leaf, peaks, a curl, a bolt, an eye, a
  blade, a star, a ring); the salts are a heap of grains in a footed dish. The templates (rock, nugget, crystal, cut
  gem, core, dish and heap) are driven from tables: the spirit stones grow and gain gold prongs, the beast cores grow
  by rank tier and gain a band, a swirl of light, then a coil and a glint, the salts a richer dish; a Mystic mineral and
  above carries its aura as stepped glow bands. The legacy 32 px code is gone.
- **Beast parts in Style A** (`tools/icons/families/beast_parts.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/beast_parts/`): the 62 parts and the 21 pet-gear ladder pieces (collars, beast
  talismans and saddles, taken over from `banded.py`) redrawn at 64 px with native `@32` renders, each part as the
  material it is in the colour of its beast: fur in strands down a pegged pelt, scales with their growth ridges and
  keels, horn and claw with a keratin sheen and the grain along them, feathers with barbs swept back to the quill,
  through-lit glass, jade and cores with the light pooling on the far side (the Gravity Core with its rings of bent
  light). The kinds share one drawing each (hide, scale, fang, feather, vial, pouch, heap, shard, core) and every icon
  comes from one table. The grade is form and trim (`GRADE_HD`): a plain part is raw, a common one tied with hemp and
  pegged with wood, from Earth bound in the grade's silk with a cap, peg or bead in its metal, and from Mystic the
  aura in the beast's own light at the grade's strength; the ladders take a grade's kit for the band, plaque, seat,
  scales, cord and buckle. The legacy 32 px drawings are gone, except two helpers the unconverted families import.
- **Armour, the gourds, the cape and the soul talisman in Style A** (`tools/icons/families/armour.py`, `ART = 64`;
  the sheets and in-game shots in `docs/mockups/icon_families/armour/`): the 47 icons (nine hats, robes, trousers and
  boots, the mistjade cape, the cloud talisman and the nine spirit gourds, the Sovereign and Will rows folded in from
  `banded.py`) redrawn at 64 px with native `@32` renders. Each piece is shown as it is worn: its row in
  `data/artifacts.json` gives the cut of the avatar layer (`appearance`) and its garment dye (`dye`, now the
  `palette.dye_*` ramps), so the straw douli, the jade circlet, the tied silk band, the gold crown with its jade pin
  and the veiled hat, the vest, the scoop-necked tunic, the sect robe with crossed lapels, the cloud tunic and the
  scholar's coat, the loose, straight, martial, cuffed and scholar trousers, and the leather boots, folded greaves and
  cloth shoes match the figure beside them, with cloth folds, riveted plates and lacquer in their own textures. The
  grade is the kit, Plain to Sphere: the trim of cuffs, hem and collar, the fittings, the plates and greaves in the
  grade's metal, the gem, and the grade's mark (jadeiron plates and scales, cloud scrolls, gold lines, a lightning
  stitch, desert-glass beads, driftglass studs, star dots, pearls), with the aura from Mystic up; the gourds carry the
  same ladder. The legacy 32 px code is gone.
- **Weapons in Style A** (`tools/icons/families/weapons.py`, `ART = 64`; the sheets and in-game shots in
  `docs/mockups/icon_families/weapons/`): the 103 weapon icons (eleven families at nine grades, Training to
  Lanternsteel, the Sovereign and Will ladders and the brush and bell ladders taken over from `banded.py`, and the
  Wardens' four pieces) redrawn at 64 px with native `@32` renders. Every weapon lies on the study's diagonal frame
  (the bell mouth down-right, the gauntlet a fist over its cuff) and every family is one builder on the shared tassel,
  grip, fitting, blade and gem builders, so the family is the silhouette, after the held sprite: the jian's straight
  blade under a winged guard, the sabre broad and curved under a disc with a ring pommel, the short blade a leaf, the
  spear's leaf head with its tassel on a long shaft, the staff's crook, the recurve bow on its string, the fan open on
  its sticks, the flute with its holes and cord, the brush with its tuft dipped in ink, the bell with its cord and
  clapper. The grade is the kit (`palette.kit`, Plain to Sphere) as material, fittings and work, never a colour
  alone: a wooden blade with its grain and a hemp lattice, iron with a plain fuller, a jade inlay, silver cloud
  curls, gold runes down a dark fuller, a lightning zigzag, desert-glass beads on an ember line, driftglass diamonds
  in a driftteal line, star dots with a starlight edge; a gem in the guard from Earth, a metal bead on the tassel and
  the glow from Mystic; the same work runs along a bow's limb, a fan's leaf, a cuff or a bell's waist. The Ink-Warden's
  Brush keeps its black lacquer collar and falling drop, the Starwrit Brush its lantern-ash tip lit at the point, the
  Warden's Hand-bell its bronze and cloud scroll, the Tidebreak Bell its cage lattice and cold blue mouth. The legacy
  32 px drawings and the recolour rows are gone; `banded.py` keeps only the Sovereign and Will armour, hats and gourds
  and the four furnaces.
- **Fish, insects, critters and food in Style A** (`tools/icons/families/fish.py`, `insects.py`, `critters.py`,
  `food.py`, each `ART = 64`; the sheets and in-game shots in `docs/mockups/icon_families/<family>/`): the posts'
  catches and the dishes, 41 icons, redrawn at 64 px with native `@32` renders, each catch the living animal drawn
  with care in its species' colours (after its sprite where it has one). The seven fish are side views on one
  template in a body frame (`fish.Axis`): the body profile, a forked tail and the dorsal, pectoral, pelvic and anal
  fins with their rays, rows of overlapping scales, the gill cover, a lateral line, the eye with its ring and
  catch-light, and the species' marks (the perch's bars and spiny dorsal, the trout's spots and pink band, the carp's
  gold-edged scales and barbels, the salmon's kype and spray, the moon carp's crescent, the minnows' shoal, the eel's
  ribbon fin and rings). The eight insects are specimens from above, the side or three-quarter on, with jointed legs,
  antennae, compound eyes and segmented abdomens (the firefly's lit tail with its own halo, the cicada's clear veined
  wings, the scarab's jade-sheened shell, the moth's eyespots and comb antennae, the mantis's raised spined forelegs
  and spark, the cricket's cocked hind leg, the locust's fanned ember wings, the mote's star-dusted points). The nine
  critters are bodies from a spine of discs with fur in strands, faces with ringed eyes, noses and whiskers, ears
  with their pink, paws with toes (the frog's gold eyes, the hare's misty ear tips, the marmot's cloud tail, the
  hedgehog's sparking quills, the stoat's black tail tip, the fox's sail ears, the gecko's star spots, the tied
  pearly pelt). The grade is form and trim on `beast_parts.GRADE_HD`, never colour alone: a plain catch as it came;
  from Common a stringer loop at a fish's jaw, a thread round an insect's waist or a cord at a critter's neck, hemp
  at Common and the grade's silk with a metal bead from Earth; the aura from Mystic up. The 17 dishes are their
  vessel and contents with steam and gloss on shared cup, bowl, plate and pot templates, in the grade's ware
  (`WARE_HD`, after the pills' ladder: bare earthenware, a bronze band, porcelain with jade, skyware with silver,
  storm glaze and sand glaze with their aura; a pot takes the grade's metal for its handles and band). Every icon
  comes from its module's table. The legacy 32 px code of the four families is gone.

- **Treasures, legends, Qi jades and the workshop in Style A** (`tools/icons/families/treasures.py`, `legends.py`,
  `jades.py`, `workshop.py`, each `ART = 64`; the sheets and in-game shots in `docs/mockups/icon_families/<family>/`):
  98 icons redrawn at 64 px with native `@32` renders. The 31 treasures are each the object the item is, on shared
  builders: the upright temple bell (a plain iron practice bell against the bronze bell studded with jade), the
  three-legged vessel (the taming cauldron with its gold claw, the grimed curio, the furnaces), the paper talisman
  strip, the Heavenly Flame on its dish (the Lantern Heart in its bronze cage); the pagoda's jade roofs with silver
  ridges, the mirror with its gold bosses, the mountain seal's beast and red face, the wisp banner with its three
  lights, the sealing gourd under the pills' silver cloud lid, the nine swords fanned from their lacquer case, the
  needles, knives and pellet, the flying sword streaming Qi, the cloud, the jade gourd and the maple leaf. The furnace
  ladder (`furnace_hd` on `palette.kit`, the four Act II and III furnaces taken over from `banded.py`, now deleted)
  shows the grade as the walls' metal, the grade's work round the belly (the weapons' `work_hd`), the trim of the rim
  and ears and the jewel as the lid's finial, the Nine-Dragon Cauldron with its gold dragons; the aura from Mystic up
  in the object's own light. The 28 legend pieces are the thing each is named (`legends.PIECES_HD`: a knuckle, a
  cuff, a heart; a hilt, a blade, a soul bead; a spearhead, a shaft, a tassel; an edge, a grip, a sheath; an iron
  cap, an oak shaft, a knot; a spine, an edge, a guard; a rib, a silk, a pin; a mouthpiece, a jade body, a tassel; a
  limb, a string, a sight), built from the weapons' builders in the chain's tint (`chain_kit`) with gold Mystic
  fittings, a lit jagged break where a piece was broken (`broken_hd`) and the Mystic aura in the tint; the Weapon
  Soul Crystal is a gold crystal with an ember flame in it. The 13 jades: five cut stones in bezels (`cut_hd`, any
  outline: a cushion, a marquise, a twelve-sided round, a hexagon, a kite with an eye) and eight bi discs (`bi_hd`)
  carved with their signs in their own light. The 26 workshop goods: thread-bound books (`book_hd`, the cover's
  cloth naming the element, a paw for the pet skill books; the torn manual with its corner gone) and tied scrolls
  with element tags (`EMBLEMS_HD`), the grimed ding, the river-jade bi against its glass fake with a chip and
  bubbles, old coins on a string, the spirit wood with Qi in its grain, the puppet's jade heart in its pegged frame,
  the three array plates with their arrays lit, and the Sphere Comprehension Stone with its folded world and the Will
  aura. The legacy 32 px drawings of all four modules are gone.

- **Miscellany and tools in Style A** (`tools/icons/families/misc.py` and `tools.py`, both `ART = 64`; the sheets and
  in-game shots in `docs/mockups/icon_families/misc/` and `tools/`): the 93 miscellany icons and the 65 tools and
  talismans redrawn at 64 px with native `@32` renders, one language per kind. Miscellany: a manual or a page is paper
  with its laid lines and columns of script (a stance figure, a seal, a river sketch), a closed scroll lies on the
  diagonal with its tie and tag, a hand scroll opens between its rollers; a token hangs upright from a cord loop and
  bead with a tassel, its face carved inside a keyline or a gold rim (the sect discs, the alliance summits, the entry
  gate, the elders' knots and crests); a bag is a drawstring pouch tied at the neck (the storage pouch's seal slip, the
  five beast bags with the paw sewn on in straw, hide, cloud silk, deep jade and starweave); the eggs sit in their
  nests, the wyrm egg on its night cushion; incense stands in a bowl or, for the Roll-Call's hour incense, a tall cup
  whose label carries the hours in pixel numerals over a holder that grows from clay to bronze, porcelain, jade and
  gold; the rite tablets stand in stepped pedestals with their crests; the Keeping Post's components (cord, rivets, the
  brick, lacquer, the whetstone, spirit glue), the Starsea charts and ships, the sun seal and its pieces, the treasures
  and the Ash and Tide pieces are one-offs on the shared builders (the weapons' tassel, the beast parts' cords, vials
  and heaps, the herbs' leaves and lotus, the minerals' dish). Tools: the four Keeping Post ladders (picks, sickles,
  rods, hoop nets, nine tiers each) and the snare kits are one builder each on the weapons' diagonal frame and kit
  builders, painting with the tier's head metal (copper, iron, jadeiron, cloudsteel, mistjade, stormsteel, then
  sunglass and driftglass through-lit) over the grade's kit, so a tier shows as material, fittings and work, never as
  colour alone: a hemp grip on plain wood, then leather on darkwood with the guard metal's butt cap, eye ring, ferrule
  or reel, a gem at the eye from Earth, the grade's work down the head (a fuller, a jade inlay, cloud curls, gold
  runes, a lightning zigzag, ember beads, driftglass diamonds), capped points from Mystic and the aura as stepped glow
  bands; a net's mesh grows finer up the ladder. A talisman is a strip of yellow paper with red bars, its glyph traced
  in the element's ink over the maker's seal; the offerings sit on the minerals' footed dish. The legacy 32 px code is
  gone from both modules.

- **Status icons and markers in Style A** (`tools/icons/families/status.py` and `markers.py`, both `ART = 24`; the
  sheets and in-game shots in `docs/mockups/icon_families/status/` and `markers/`): the last two families, 34 status
  icons and 17 map and quest markers, redrawn at 24 px, the size they are shown at, with a native `@12` render of each
  status icon for the row over an enemy's name. The pipeline gains the 24 px size (`registry.HD_SIZE`, `VARIANTS`) and
  the game draws 24 and 12 natively (`SpriteCache.ICON_PX`; the technique emblems keep their own sizes). The colour
  language stays, never alone: every glyph has its own silhouette. An injury is its object with a red crack cut into
  the outline (a bone, a broken meridian arch with its acupoints, a cracked soul orb); stability is the stepped
  foundation built one tier at a time, red, yellow, jade and gold, the unstable slab cracked and chipped; a buff is its
  object (a sword, a shield, chevrons) with the green up-arrow; cultivation states are jade and gold (the seated figure
  under a halo, the gold diamond with its jade core); the debuffs are their own shapes (a flame, a venom drop, an
  hourglass, a dazed ring of stars, gripping roots, drips from a wound, a snowflake, a bolt, a sealed Qi orb, a split
  shield, a spiral, a ghost, a horned demon, a circuit whose arm turns back, a bolted eye). The markers are one bold
  object each (the gold quest diamond, the blue side-quest seal, the question mark, a figure, a sycee, the medicine
  gourd, the anvil, the shrine, the open and the sealed portal, the teleport stone, the crown, the skull, a leaf, a
  crystal on its rock, a fish, the player's arrow). `asciiart.py` and the unused `glyphs.py` are gone with the ASCII
  sprites; no legacy family remains.

## Wikis and volume (docs/roadmap_master_ui.md, P7)

### P7b · part 1
The data work of `docs/item_plan.md` §6, steps 1–7, 9 and 11–13 (step 10 for the new bases); the named pieces (step 8)
come next. Where it differs from the plan, the plan's §6 says so.
- **Drops are about six pieces an hour of hunting, not fifteen.** Every loot table's chance and quality floor follow
  §4.1 (normal foes 1.2% from Flawed, elites 8% from Common, chests 30/50/60% from Fine); the quality tables, the weapon
  share, the elite spawn's extra roll and the named rows' rules sit in `grades.json` `drop`, which `LootRules` and the
  World read. A weapon drop is in the family in hand one time in three, so about 76% of what drops fits the character.
  The item Level stops at the top of the highest grade with banded bases: Act III drops Sovereign and Will gear.
  Salvage gives half as much Refining Essence again.
- **`balance_sim` measures it:** 29 field regions, each room hunted 20 hours with the real rolls, 5.9 pieces an hour
  on average and every grade inside its §4.4 targets (pieces, Fine, Superior, Perfect), every region at least 3 an
  hour, 75–81% of the pieces usable by each archetype, no named piece from the random roll.
- **Named pieces carry tags** (archetype, zone, element, path, fixed affixes): a fixed affix is always on and counts
  half again on its archetype's path, and each named piece adds 2% elemental power of its element. The Serpent-Tongue
  Jian and the Tidebreak Bastion's brushes and bells have theirs; loot tables gain `named` and `elite_named` rows. Big
  Toad Tan's Mudwater Cleaver comes on his first defeat (the unread `unique_drop` is gone), his robe and the Drowned
  Abbot's hat and boots are 8% rows, the Crane Trousers a Cloudpeak Roc's 0.2%.
- **Ten affixes** (Qi and soul attack, Essence, knockback, max Soul in the random pools; taming, crafting control, pet
  damage, array power and melody power only on named pieces) and **three stats**: pet damage (your animal's strike),
  array power (an Array Plate's time and the killing array's blow) and melody power (the melody's slow and heals, the
  bell's ring, Clear Heart Melody).
- **Sets** move to `tools/data/gear.py` with an archetype, tier, element and path; on its path a set's 2-piece bonus
  counts double. The six archetype lines and their 6-piece mechanics are in `gear.json`, each read by the rule that owns
  it: Unbroken (a shield before a blow breaks 30% HP), Honed Intent (two more stacks of Sword Intent, fading half as
  fast), Venom Hand (the Poison Body at 35%, oils on more hits), Kin-Bond (your animal takes 15% less), Living Array
  (wider rings that lay the brush's talisman) and Sustained Note (a melody's first 3 s free).
- **71 banded bases:** the brush and the bell at every grade from Training, so the formation master and the bell
  musician have a weapon from Level 1; Driftsteel and Lanternsteel weapons in all eleven families, Starsilk and
  Lanternsilk armour and the Driftglass and Lantern Gourds (Sovereign and Will); collars, beast talismans and saddles up
  to Will; the Stormsteel to Lanternsteel furnaces. Each has its wear level, sockets, salvage row, forge recipe and a
  shop, and an icon drawn with its family's existing function (`tools/icons/families/banded.py`).
- **Every item has a source; `KNOWN_SOURCE_GAPS` is empty.** Hermit Yao sells metal cores and Peddler Ning star and
  space cores (two a day each: shop rows can now carry a daily limit); the Weeping Lantern, Mirror Wisp and Terracotta
  Warden carry soul cores; a Stormgrass Stag grazes the Thunderhorn Plains on the Cloud Stag's sheet (the peak wood
  core); the high Spirit Stone from the Sovereign of Sages achievement, the Nine Peaks auction and the Tomb and Wreck
  chests; the beast bags, incense sticks, snare kits, rite tablets and gourds from shops, activity chests, the Trial
  Tower's guardian floors (first clear), auctions and the forge; the sect sets' hats, trousers and boots at their
  Mission Halls; the Crane Robe from "Crane Falls at Dawn" and the Crane Boots from the Cloud Stepper.
- **Checks:** `rules_tests` `drop_pool_suite` (family bias, the Level cap, the pool, quality tables, named rows,
  named-only affixes) and `set_suite` (paths, each line's bonuses and mechanic, the three stats' readers);
  `data_validation` `gear_suite` (tags, fixed affixes from the archetype's pool, every set sourced and completable, every
  banded grade whole, loot-table fields and named rows; the named count per archetype and zone waits for step 8).
- The wiki shows named tags, sets, the drop rules, named rows and shop limits.
- Two checks that depended on the account's random seed now pass whatever it draws: the Cloud Steps run in `rules_tests`
  finishes under the fastest time a rival can draw, and valley_run's Hollowed Wyrmlings get to land their grey flame
  when the fight ends before one has.

### P7a · The item and monster wikis
- **`docs/wiki/items.md`**: all 614 items (472 items, 142 pieces of equipment) by type or slot, each with its icon,
  grade, iLv, stats or effect, requirement, description and every source the data gives, with rates: enemy drops,
  jars and chests, the Trial Tower, gathering nodes and posts, gardens, recipes and other crafts, shops and auctions,
  quest and unlock rewards, mail. Banded equipment names the foes and chests whose roll can make it.
- **`docs/wiki/monsters.md`**: all 121 enemies by zone, each with its sheet, room spawns, other appearances (events,
  set pieces, the tower, tides, summons), level band, stats, attacks and phases, and its full drop table with rates.
- Written by `tools/dev/wiki.py` from `data/` alone and byte-identical on every run; `build_data.py` runs it after a
  full build.
- **Every item has a source.** A `data_validation` rule scans the same channels; an item nothing hands out carries an
  explicit mark instead (`"source": "story"`, `"system"` or `"later"`): the starting gourd, the dyed root, the murky
  pill, the Evergreen Heart fruit and the two Monarch pills. 43 real gaps are listed in the suite's
  `KNOWN_SOURCE_GAPS` for P7b: 12 beast cores no beast carries, the high Spirit Stone, two beast bags, five Hour
  Incenses and the Wandering Incense, six snare kits and rite tablets, three gourds, and 13 set pieces (the sect sets'
  hats, trousers and boots, and the Mudwater, Drowned Abbot and Crane sets but the Abbot's robe).
- **Found by the scan, fixed:**
  - The banded equipment roll could make one of the nine legendary weapons or the two imitation relics as ordinary
    Mystic or Heaven gear; they come only from their chains and the forge now (`drop_pool_suite`).
  - Loot group rows carried a `chance` the roll never read (a group rolls once and picks by weight); the rows keep
    only their weight, and `data_validation` refuses a chance on a group row.
  - The Lantern Star Field's ledge and cloud chests used the valley's chest tables; each zone's chests now use its own
    table (`ZONE_CHESTS` in `tools/data/world.py`). The Flame Heart's ledge chest, in a room with no Level of its own,
    was Level 1; a chest in such a room now takes its region's top Level.
  - The mist trout's valley spot at the Falls Pool had no fishing spot; it has one in the shallows now.
- **Left for P7b:** 43 items nothing in the data hands out (12 beast cores, incense sticks, snare kits and rite tablets,
  three gourds, the sect sets' hats, trousers and boots, pieces of the Mudwater, Drowned and Crane sets,
  `spirit_stone_high`, two beast bags). `data_validation` lists them in `KNOWN_SOURCE_GAPS`: a new unsourced item
  fails, and a listed item fails once it gains a source, so the list only shrinks.

## The UI review and restyle (docs/roadmap_master_ui.md, P2–P5)

### P5 · The first pages with their own identity (`docs/page_identity.md`, decisions 14–16)
- **The foundation** (`docs/page_identity.md` §8, How a page takes its identity). A page declares what it is,
  `Page.Identity`: its `SURFACE` material, whether the shared window frame stays round it, its own title mount, its
  layout signature and its opening. Page then draws the page's surface in the standard window rect in place of the
  shared window, inks the title on the page's own mount and draws the tabs in the page's own form, while the close
  button, Esc and a tap outside, primary buttons with inked labels, the text tokens, the type scale and the 48 px
  targets stay Page's. Pages that declare nothing keep today's look exactly.
- **Every word is measured on what it sits on.** A page with its own surface names its grounds as it draws them
  (`ground`, `face`, `panel`), and the `ui_suite` measures every plain word it draws on the ground under it (4.5:1, or
  3:1 from 20 px). It found the washed slips too light for `MIST` (4.21), so words there are `PAPER`.
- **Motion by the reduced-motion rule** (`docs/moments_design.md` §4.6, page_identity §6): `unfold()` runs a page's
  opening over its declared time (0.35 s at most) and a tap finishes it; under Reduce motion nothing moves and the
  page only fades in, over 0.2 s. Every target is live from the first frame.
- **Tokens.** The twenty `SURFACE` materials of page_identity §7 join `UiKit` (and `cloth_wash`, the washed slips), each
  a mix of two tokens, with `TEXT_ON` rows for those words are drawn on; the talisman's red ink and the zither's
  strings, which had the names `cinnabar` and `silk`, are `cinnabar_ink` and `qin_silk`, unchanged in colour. New Page
  helpers: `rich` (words in several colours), `rounded`, `glow`, and `grade_rims` (slots ring an item in its grade's
  colour and mark a rolled quality with a gem).
- **The Character page as the jade-slip record** (row 13, mockup 09 v2). One mat of vertical jade slips bound by two
  gold cords, fanning open from a bundle as the page opens; the title and the four tabs are jade tags on the upper
  cord. The figure stands at 2.5 on the first slips, washed lighter as if painted there, with the eight worn slots down
  the slips either side (decision 8), a closed slot showing its lock and what opens it, an empty one glowing jade while
  the bag holds a piece for it; who walks beside in round chips. The register is written across the rest: the name,
  the realm with its Level and stage pips, sect, rank and worn title, Combat Power, Relations and age, the origin and
  what it gave, the three pools, and offence and defence in ruled columns with Soul attack, Soul defence and Will
  added. Stats and Titles fold into the Overview, so the tabs are Overview, Aptitude, Attunement and Wardrobe.
- **The titles as honours** (decision 16). Each title is a red lacquer tablet with cut corners and a gold inlay line;
  its motif (blade, shield, pearl, cloud, peak, lotus, coin, cauldron or star, by the stat its gift raises) on a
  gilt boss; its name in pale gold and its gift inscribed in gold on a sunk band. The worn title comes first, in a
  gilded frame with a stud at each corner and the gold ◆ of the style guide's "you" mark. Five to a page and a button
  to the next five; a tap wears one (`set_title`, as before).
- **Art** (`tools/ui/build_ui_hd.py`, byte-identical twice): `jade_tag`, `jade_label`, `honour_tablet` and
  `honour_seal`'s nine motifs; the slips, cords, knots and wash are drawn by the page from tokens.
- **The Bag** was built as the spirit gourd of mockups 07 and 08 v2 and withdrawn before it merged, by decision 15 (no
  gourd drawing; a big space with a small card for the chosen item, new concepts to the user first). The Bag keeps its
  P4 page; the general pieces it used are the foundation above.
- **Tests:** `rules_tests` `ui_suite` (every word on a page with its own surface read on its ground, the close button
  and inked title kept, a signature no other page shares, in every tab), the new `identity_suite` (on a probe page: a
  word too dim for its ground caught, the tabs' targets and the inked title kept, the regions live from the first frame,
  the opening and a tap, Reduce motion's fade; a page with no identity opening at once), `ui_style_suite` (the new
  surfaces and faces measured); every target 48 px or more and every word on the type scale, as before. The full
  suite on this build: room_lint 168 / 0; engine_tests 3785/3785; data_validation 23287 / 0; room_sweep 3568 / 0;
  rules_tests 1830 / 0; contract_tests 1032 / 0; balance_sim 124 / 0; perf_tests 5 / 0; prologue_run 107 / 0;
  valley_run 1257 / 0; check_scripts 0 failures.
- **Screenshots** in `docs/ui_p5/`, on copies of the valley_run checkpoints `ls6_end` and `bf2` taken on this build, with
  the comparison against mockup 09 v2 and why each difference is there; `--tap=x,y` (a debug tool) taps the top page.
- **Roadmap:** U20 Partial and U21 Present (C8), U15 stays Partial with decision 15's withdrawal recorded; the P5 row
  says what has started.

### P5 · The Bag as the heaven in the gourd (concept B, decisions 8, 15 and 24)
- **The page** (`docs/page_identity.md` row 3; mockups 07_bag_b, _card, _pill, 08_bag_b_empty). No gourd is drawn and
  no frame: the page is the world inside the Spirit Gourd, a night sky over a sea of cloud with far islands, and a
  bigger gourd is a wider heaven (more stars and islands, the light from its mouth once it holds 40). The figure stands
  at 2.5 on its own island with the eight worn slots riding a gold orbit round it (`CharacterPage.draw_worn`, which the
  Bag now shares; the figure is drawn by the page, `Avatar.draw_on`, so the card lies over it). What is carried floats
  as one grid ten across, five rows in view and the next fading into the cloud, the next gourd's spaces locked at its
  end with the gourd that opens them; the Spirit Gourd and Key Pouch tokens, the purses (the rarer ones give way when
  room is short), the kinds (All, Gear, Pills, Materials, Other; items.json `bag_kinds`) and Sort; "Space n / m" and
  the next gourd under the grid; while the gourd is small, the hint in the open sky (how things come in, a loose find
  and what a trader pays, the piece that fits an empty slot, what opens the locked ones). The grid rises out of the
  cloud and the worn slots ride in along the orbit as it opens (0.3 s; a fade under Reduce motion).
- **The small card** (decision 15) opens beside a tapped space with a pointer to it: below it on the top row, to its
  right from the first columns and beside the orbit for a worn piece, else to its left, above the line under the grid
  while it fits. The head (icon, name and count, quality, grade, kind, item level); for a piece in the bag what wearing
  it would make of your own totals against the one worn (the three that change most, and Combat Power, each after the
  change with ▲ or ▼ beside it), for a worn one what it gives you; what else is true of it (the rolls, a pill's
  toxicity against yours, what quick-use holds, a furnace's batch, a relic's spirit, a treasure's cost); its action and
  partner (Equip and Set as spare, Use and Quick-use, the Treasure buttons, Unequip and Swap, Ride, Play) and "···" for
  Lock, Discard, Self-detonate and Appraise. A tap on open sky puts it away. Every P4 action and intent is kept.
- **Rules** (pages submit intents only): `StatRules.equip_change` works out the comparison by `rebuild` on scratch
  copies of the character, so the character is never touched and the numbers are the Character page's;
  `InventoryAuthority.bag_kind` and `next_gourd`.
- **Art and tokens.** `build_ui_hd.py` (byte-identical twice): `sky_token` (normal, selected) and `sky_card`; the sky,
  stars, islands, orbit and sea are drawn by the page from tokens. `SURFACE.sky` and `SURFACE.sea` with their
  `TEXT_ON` rows. `Page.rich` can centre its lines.
- **Tests:** `rules_tests` `ui_suite` opens the Bag with its card on a worn jian, a carried one and a pill; the
  `identity_suite`'s Bag part checks the kinds split the bag with nothing lost, the eight worn slots, the card beside
  its space and inside the window with 48 px actions and words that read on it, that `equip_change` leaves the character
  untouched, that its "before" is the character as it stands and that equipping the piece gives what the card said,
  "···", and a pill's Use and Quick-use. The full suite: room_lint 168 / 0; engine_tests 3785/3785; data_validation
  23287 / 0; room_sweep 3568 / 0; rules_tests 1860 / 0; contract_tests 1032 / 0; balance_sim 124 / 0; perf_tests 5 / 0;
  prologue_run 107 / 0; valley_run 1257 / 0.
- **Screenshots** in `docs/ui_p5/bag/`, on copies of this build's valley_run checkpoints `ls6_end` and `bf2`, beside
  each mockup, with why each difference is there. Roadmap U15 Present.

### P5a · The HUD to the approved mockups
- **The right thumb, two rings (mockup 01).** Ring 1 at R 132 round the 132 px attack button holds jump, the page's four
  techniques (64 px, the HD icons at their native 48) and dodge; ring 2 at R 214 holds the fan and, beside it, a toggle
  that is on, the healing slot, the Draught, the treasures, the in-fight context (or Keep Post) and the weapon swap.
  The pinned toggle, the healing slot, the first treasure, the context and the swap have their own places; the rest
  take the next free one, and a heavy load spreads over the arc without two rings touching. A "1/2" tab turns the
  technique page (a swipe on the ring still does). **An empty or locked slot is not drawn** (review G3): no blank
  circles, no empty treasure, no swap without a spare.
- **The fan holds the system toggles (decision 20).** Cultivate, the Presence, the Sphere, Sense and Pet fold into one
  button; a tap opens it on a paper fan with each toggle named (only the ones the character has, packed from the
  first place) and a tap closes it. Closed, a toggle that is on stands pinned beside it (a held Presence with its Soul
  upkeep arc and level; meditation; a raised Sphere), and the fan glows gold at the bottleneck or when a toggle in it
  is new. At rest the fan keeps the player's choice (open, as mockup 02 draws it, until closed); a foe near folds it,
  and in a fight a toggle taken from the open fan folds it again.
- **Rest and fight (mockup 02).** With no foe within 560 px (and no boss in the room) for two seconds, the techniques
  fold into four beads on the attack ring over 0.25 s (a fade with Reduce motion), the healing slot and the treasures
  rest, and the attack button becomes the context with its verb and target under it ("Talk · Peddler Ning"). A foe
  near brings them back. Every existing control, key and reveal is kept.
- **The rest of the HUD to the mockups.** Party chips beside the panel for the animals beside you and the fellow
  disciples, each a 48 px ring with its face (a disciple's from their own sprite layers), an HP arc, a red ring for a
  wound and the name under it; the bag animals and the mount after them. The Hollowing as a meter with its Burden and
  Seizure stops, its value and which way it runs ("46 ▼ lanterns"). The quest tracker on its plate with a 48 px go
  button. A count on Mail and a vermilion ready seal on Menu when the bottleneck is reached or a day's chest is full.
  The purse rests in boss arenas. The boss bar with its name in the display face, "Lv · phase n of m", an ember fill,
  a notch at each phase (gold once passed, the next lit) and what each brings ("60% · Ashborn Pyre Keeper called ✓",
  "30% · Enrage"). The progress edge with a stop and a "Lv n" at each Level; at the bottleneck it glows gold with
  Stored Qi as a bright lane and "◆ Bottleneck reached · breakthrough ready · tap Cultivate". The log above the
  joystick. The top centre as one stack under the chips (or the boss bar): a run's timer, the room's name, an event or
  a tribulation, a fortune card, then toasts 408 wide and 8 apart that stop above the clear zone (the rest wait).
- **World labels never stack (review G4).** Each kind keeps its own offset: a foe's level and name over its head, the
  party's thin HP lines lower (only in a fight; their names are on the chips), an NPC's plate under the feet, a way's
  or a thing's plate over its art. Labels draw above every figure. Each frame `world.gd` hands them to
  `WorldLabels` (`scripts/presentation/world_labels.gd`), which places them in whole rows so none touches another or
  sits under a HUD control (the HUD writes its controls' rects each frame); a plate under the feet with no room below
  goes over the head; a label keeps last frame's row while it is still clear.
- **The clear zone.** No control or panel stands in the lower middle round the player (x 380–900, y 324–656 at 1280 ×
  720, `hud.gd` `CLEAR_ZONE`), in a fight or at rest with the fan closed, left- or right-handed; the log, the
  tracker and the toasts keep out of it, and the open fan at rest keeps off the player at the common camera positions.
- The legacy panel's own Cormorant preload is gone; outlined words are fitted in the face they are drawn in. Debug
  flags for previews: `--toggle=presence|sphere` and `--fan=open|closed`.
- **Tests:** `rules_tests` `hud_suite` rewritten for four states (a fight, the fan open or closed, at rest): every hit
  circle 48 across and its drawn radius + 4, the nearest centre wins, the cluster where the mockups draw it, ring 2's
  places and a heavy load, rest and fight, the fan's open, close, fold and pin, the clear zone (and mirrored), the
  toasts' stop, and G3 on a bound character; a new `labels_suite` checks the layout pass on a crowd, under a control
  and over the head, a second pass holding still, and the real views (foes, a boss, the party's lines, two NPCs on one
  spot). Screenshots from the valley_run checkpoints beside mockups 01 and 02 are in `docs/ui_p5/hud/`.

### P5 · The World map as drawn (mockups 16 and 16_resources, decisions 11, 17 and 25)
- **The framed painting** (`docs/page_identity.md` row 7). The zone's landscape fills the screen inside a lacquered
  frame (timber, a bronze fillet, a gold line, cloud-scroll corners): the valley is the painting of
  `tools/ui/build_valley_map.py`, its nodes where that painting drew each area. The title plate with the map glyph and
  the pennant hang at the upper left, the zone tags from the top rail beside the Heaven Ranking (a zone not yet set foot
  in shows its lock and says why), the close button at the top right. `Page.WINDOW_SCREEN` (0, 0, 1280, 720) is the
  one window that is the screen itself (style guide §2.2); the `ui_suite` allows it.
- **Areas.** Every area a glowing node: jade where you may walk in (you have been there, or a portal open to you leads
  there), gold where you stand, a dark disc with a padlock where the way is shut. Dotted routes along the rooms'
  portals, pale between open areas and dim into a locked one; the way to the chosen area lit gold, dot by dot. Name
  plates carry the level band ("You are here", "Locked · Lv 28–36"), and a known area's field boss with the time till it
  rises; a locked area beside none you know shows its padlock alone. The tracked quest's lantern, the world events' plum
  blossoms (gold under way, violet coming) and the paths above (S43's wind glyph) stand beside their nodes.
- **No text on the map touches (decision 17).** One layout pass places the marks, then the plates (where you stand,
  the chosen area, the open areas, the locked), each at the first place round its node, below, above or beside and
  slid along that side, then a leader step out, clear of every other plate, mark, node and the frame's furniture; a
  plate with no room drops its last lines, and the ones still without room go first on another pass. It never lays one
  thing over another.
- **The card.** Areas: the area's own picture from the painting with what grows there, its kind and band against your
  Level, Act II's attunement, the tracked quest that leads there with Walk there, its world events, its rooms (you, the
  quest's room, seen, unknown) with their hazards, paths above and field bosses, and Track Route with the areas it
  crosses. Resources: Herbs, Ores and Fish, the zone's things of that kind (those in areas not yet reached greyed), the
  chosen one's rank and craft, its rooms and regrowth, the quest or daily that asks for it, a gold ring and its disc on
  every area that holds it, and Track Route to the nearest. Objectives: the tracked quests and the zone's events, the
  chosen one's way lit and Track Route. Track Route and Walk there are the `auto_path` intent; the page writes nothing.
- **What the painting does not place.** A room in a hidden region shows at the nearest placed area by portals; a
  region without a `map` position stands at the mean of its placed neighbours, moved clear of the other nodes. The
  Azure Expanse and the Lantern Star Field have no painting yet: the page draws them from tokens in the same manner
  (far ranges over a sea of cloud; the star river and drifting lanterns), each area an isle under its node.
- **Motion:** the card slides in from the frame's edge (0.2 s), the chosen way lights in 0.3 s; under Reduce motion
  the way shows lit and the page fades; glows at 0.3 with Bright flashes off. Strings through `ui_strings.json`.
- **Tests:** `rules_tests` `map_suite`: the valley's nodes on the painting's map rect with a picture each; every room of
  every zone shows at an area of its zone; the pass on a crowd; on the real data, in every zone, view, kind and chosen
  area, with every area known and with few, at every text size, no plate or mark touches another, a node or the frame's
  furniture, and every word on the painting sits on a plate (180 views); in the valley no plate is left out; Track Route
  and Walk there walk by `auto_path` and close the map; a locked zone's tag says why. The `ui_suite` opens the map's
  three views in every tab. Screenshots beside the mockups in `docs/ui_p5/map/`.

### P5 · The Bonds family: Companions, Gift and Relations (mockup 21_dialogue_gift; decision 14)
- **The Gift as a red-lacquered tray held out over the talk** (`docs/page_identity.md` row 28, mockup 21_dialogue_gift).
  The tray (HD `gift_tray`, lacquer in a gold rim) sits above the Dialogue's own paper strip: "A gift for …", one a day,
  what they are known to love and like; ten compartments of what the bag can give, the known ones first with a pink
  "Loves it" or "Likes it" tag, the rest behind "+n"; Give, shut with why, and what the chosen thing would be. The
  strip keeps the portrait, plaque, hearts and who they are; it answers a gift ("… likes it." and what it taught you),
  and the heart bar fills with what the gift moved. The page extends the Dialogue: "Give a gift" hands the talk on, so
  its other choices (four at most, Farewell kept) stay beside the tray, and one that leads on goes back to the talk.
  A given gift lifts from its compartment toward the speaker (0.3 s). No close button, as the talk has none; a tap
  outside what a page draws (`Page.window_rect`, the tray and the Dialogue's offer card included) closes it.
- **Companions as moon gates in a whitewashed wall** (row 27, no mockup). The plaster under a coping of jade tiles, the
  title on a lacquer board set in it; each friend full-length in a round gate with the garden beyond, lanterns lit over
  the two beside you (lighting in 0.2 s when one is brought along), their hearts as knots on the red thread beneath
  (a new one tied in 0.3 s). A tap on a gate chooses the friend; their actions (Bring along, Gift, the duel, the bond
  their hearts open) stand under their gate alone.
- **Relations as the karma steelyard** (row 42, no mockup). A timber rafter carries the title and the four tabs as tally
  tags; from its hook hang your fame's plaque and the beam, merit's gold weight at its right end and sin's black one at
  its left, leaning with the alignment (the reading beside the hook), the recent deeds notched along it. Each tab's
  boards hang from the beam: the bonds on red thread, the grudges on black, the ledger and the name on hemp cords. The
  beam swings to its lean as the page opens (0.35 s).
- **Shared:** `scripts/ui/pages/bonds_kit.gd` (the wall and coping, threads and knots, lanterns, the hung timber boards,
  the family's inks); the Dialogue's strip and choices are its own functions now (`_strip`, `_choice_buttons`,
  `_go_on`), which the Gift draws with; the five hearts no longer touch "who they are". `TEXT_ON` rows for ink on
  `plaster` and words on `gift_tray`; strings in `tools/data/ui_strings.json`; every intent kept (give_gift,
  set_active_companions, companion_duel, offer_bond, pay_grudge, answer_challenge).
- **Tests:** the `identity_suite`'s Bonds part: the tray over the talk with its other choices and no close button, the
  liked gift first and tagged, a gift given as an intent with the strip answering and Give shut; a gate per friend and
  the chosen one's actions under their gate, Bring along as an intent; the beam leaning with the alignment; every word
  read on its ground. The `ui_suite` opens the Gift over a talk and alone, and the Companions empty and with all four.
  The full suite on the merged tree: room_lint 168 / 0; engine_tests 3908/3908; data_validation 49968 / 0; room_sweep
  3673 / 0; visibility_suite 6726 / 0; rules_tests 2423 / 0; contract_tests 1060 / 0; balance_sim 163 / 0; perf_tests
  11 / 0 (run alone; under load five timings missed); prologue_run 100 / 0; tutorial_order 422 / 0; valley_run 3032 / 0.
- **Screenshots** in `docs/ui_p5/bonds/` on copies of this build's valley_run checkpoints `qu5` and `ls6_end`, with
  `compare_21_dialogue_gift.png` and what differs.

### P5 · The Records family, second part: Dialogue, Quests, Mail and the Notice Board (mockups 21, 12 v2, 22; decision 14)
- **The talk as rice paper under the scene** (`docs/page_identity.md` row 2, mockup 21). The paper strip along the foot
  keeps the portrait, the speaker's plaque and the words in ink; under the name, their hearts and who they are; the
  choices stacked at the right, each numbered on a pale gold key (1–4 answer them). A quest the talk offers (or takes
  back) is pinned above the choices as a small scroll with its kind, name, first steps and rewards, read before
  choosing; it unrolls downward (0.2 s). Everything recent is kept: a quest taken or handed in closes the talk or goes on
  to the same person's next quest (M17), a last line with nothing to choose closes on a tap. The talk has no close
  button, the one page without (§8).
- **Quests as the sect's mission board** (row 6, mockup 12 v2). Two tabs, Current and Done, as paper index slips. Slips
  pinned to dark timber: the story's slip under a red head (the tracked story quest with its step and where it leads,
  or, between chapters, the tracker's Next entry with its lines and the chapter floor's ways); the side quests near you;
  today's missions (the banked days' others in a stack); the day's round as a red cord with its chest charms, lit when
  one can be opened (banked ones too), from the Activity Chests; the other side quests stacked under their nameboards,
  the companions' first, then each zone's with its regions counted. A tap on a stack spreads it across the board
  (sixteen a sheet, the way back). The chosen slip is taken down and held at the right: its head, name, giver and
  where they stand, the route from here with how many regions away, what it says, its steps (➤ now, ✓ done), its
  rewards and the story's next quest, then **Go** (the `auto_path` intent), Track or Untrack, and Abandon for side quests
  and missions. Done lays the finished slips out stamped, 24 a sheet. The slips settle as it opens (0.25 s); a chosen
  slip lifts to the reading place (0.2 s).
- **Mail as the letter case** (row 17, mockup 22). A lacquer name plate with the count of letters, unread and those that
  carry something; the envelopes in a fanned stack on the desk, newest on top, sealed in red wax until read, the
  string's knot on those that carry something, the chosen one slid out; its letter unfolded on the felt (the creases
  open, 0.3 s), the words in ink and the sender's name with a red seal at its foot, a paperweight across its head; what
  it carries tied beneath as a parcel, Claim unties it; Delete is shut, with why, until it is claimed; Claim all · n.
- **The Notice Board as the town wall** (row 21, no mockup). Grey brick under a timber lintel and a black signboard;
  the tabs two handbills. Bounties: the wanted posters pasted over each other, torn strips of older ones between, the
  chosen one on top with the target drawn from its own layers, its band and place, what it did, the reward stamped in
  red and its Take strip (shut with the realm it needs; "Hunting" stamped once taken); the missions and requests
  summed up on handbills in the corner. Board: the missions and requests as handbills in two columns, the posters
  stacked in the corner. The chosen poster is slapped on as the page opens (0.2 s).
- **Shared** (`scripts/ui/pages/records_kit.gd`): the paper inks the Codex now takes from it too, timber, pins, torn
  slips, red heads, planks, stamps, wax seals and the string and bow. New HD paper (`tools/ui/build_ui_hd.py`, byte-
  identical on two builds): `paper_slip`, `envelope` (and its lit state), `letter_sheet`, `poster`, with their
  `TEXT_ON` rows, and brick and lacquer rows. `Page.regions_away` and `go_reason` are the Calendar's route, shared with
  the Quests' Go; `Page.move` moves a part with its HD faces (`HdStyleBox.base`: the nine-slices used to drop the
  page's transform); `Page.window_rect` names what a page pins beyond its window.
- **Tests:** the `identity_suite`'s Records part two: every quest under way, on offer or on the sect board on the board
  once; the story's slip carries the story quest under way or the Next entry; a stack spreads with the way back; the
  slip being read walks to its quest's target and tracks it; Done a sheet at a time; every letter an envelope, the
  newest open with its parcel to claim and Delete shut; a poster per bounty; the offered quest pinned inside what the
  talk draws, with no close button. The `ui_suite` opens all four in every tab and measures every word on its paper.
  The full suite on the merged tree: room_lint 168 / 0; engine_tests 3908/3908; data_validation 49847 / 0; room_sweep
  3673 / 0; visibility_suite 6726 / 0; rules_tests 2170 / 0; contract_tests 1060 / 0; balance_sim 163 / 0; perf_tests 11 / 0;
  prologue_run 100 / 0; tutorial_order 422 / 0; valley_run 3032 / 0.
- **Screenshots** in `docs/ui_p5/records/` on copies of this build's valley_run checkpoints `ae_end`, `ls6_end`, `bf5`
  and `qu5`, with `compare_21_dialogue.png`, `compare_12_quests_v2.png` and `compare_22_mail.png` and what still differs.
### P5 · The Records family: the Codex, its Old Scrolls and the Calendar (mockups 18, 18_scrolls, 19; decisions 11, 14, 22)
- **The Codex as the field book** (`docs/page_identity.md` row 26). A bound book open on the reading desk: a jade cloth
  cover, the page block's edges, two pages with the gutter's shadow and foxing. The sections are silk ribbons standing
  out of the top edge; the open one hangs longer and carries the page's title, inked. The Collection is a spread for
  each collection page (four beasts a spread, a long page over several): the whole book's cards filled and the next
  stop (the Collector title and its gift), Contents (the fourteen pages, a tap turns to one), the page's name, how many
  beasts and when a card fills, each beast drawn from its sheet on squared paper and taped in (a shadow until met, with
  where it lives once you have been there), its rank, nature, levels, what taming makes of it and its drops, its count
  on an ink bar to the fill, a filled card stamped; the page's seal (every card filled, `collection_pages_done`) with
  its count. The curled corners turn the leaves; the Codex's entries, Achievements, Paths Above and Seasons are written
  on the same spread. A leaf turns over the spread on a turn, a new section and the opening (0.35 s).
- **The Old Scrolls** (decision 11: like nothing else in the game) are a tab of their own: a black stone rubbing on a
  hanging scroll (brocade, silk, rods with jade caps) on the reading room's wall, inked from the top down to the rungs
  the account has reached, the carved names pale, the stone's chips and crack in the ink, the rest bare paper with the
  ink pad where the work stopped; beside each rung the scholar's vermilion gloss of our realms on it (their halves,
  "you", "? ? ?" for one not reached); the chosen rung ringed and its note pinned on a sheet with a vermilion frame
  (levels, steps and years from `realms.json`). A second tap on a rung turns to the other realm on it; the newest rung
  is dabbed in as the tab opens (0.4 s). Each old scroll entry now names its rung and half (`tools/data/story.py`).
- **The Calendar to mockup 19** (row 22, decision 22; the almanac, 19 v2, stays the record). The kit's window: the four
  seasons as a strip from the one now; the week as seven day columns from today with every occurrence of every world
  event on its day as a slip (gold under way, violet coming; a short name each, `tools/data/living_world.py`) and a red
  line at the hour now; the Beast Tide across the week; the chosen event (a slip or the tide) with when, where, what it
  means for you (a repeat run's cap, the Terraces Trial's standing, the tide's week) and **Go there**, the `auto_path`
  intent the World map uses, with how many regions away; the weather with its next change and what each changes. The
  slips drop onto their days as it opens (0.3 s). Everything the old Calendar said is kept.
- **Shared:** Page takes the World map's `_halo`, `_pulse` and `_blossom` (the map and the Calendar draw the same event
  blossom) and `vshade`/`hshade` gradients; dark ink words take no drop shadow (`UiKit.draw_text`); the plaque's title
  is logged like every inked word, so the `ui_suite` finds it. Everything is drawn by the pages from tokens; no new
  HD art or `SURFACE` token.
- **Tests:** the `identity_suite`'s Records part: the field book binds every card once, a page each; the open ribbon
  carries the title; a corner turns the leaf; Contents lists every page and turns to one; the Old Scrolls rub only the
  rungs reached, gloss each, pin the note and turn to the other realm on a second tap, every word reading on the ink,
  the silk or the note, and every great realm names its rung; the Calendar lays every occurrence of the week on its
  day with no two slips touching and the tide across, and Go there walks to the chosen event's room by `auto_path`,
  shut with its reason when no way leads there. The `ui_suite` opens the Codex also with every old scroll rubbed and
  every card filled, and holds a layout signature to its page script (the Codex opens under four ids).
  The three "n of m" counts join `contract_tests`' counts of a total. The full suite after merging the build branch: room_lint 168 / 0;
  engine_tests 3785/3785; data_validation 49083 / 0; room_sweep 3676 / 0; rules_tests 1972 / 0; contract_tests 1051 / 0;
  balance_sim 148 / 0; perf_tests 9 / 0; prologue_run 111 / 0; tutorial_order 340 / 0; valley_run 3253 / 0.
- **Screenshots** in `docs/ui_p5/records/`, on copies of this build's valley_run checkpoints `bf5`, `qu5` and `ls6_end`,
  with each mockup above the build and why each difference is there (18's second seal and the seals' gifts were
  proposals the rules do not hold; the build draws the one seal the game keeps).
### P5 · The Beasts family: Spirit Animals, the Core Exchange, the Beast Arena (mockup 10; decision 14)
- **Spirit Animals as the bestiary** (row 16, mockup 10). The kit's window keeps its plaque and its tabs, now Stable and
  Swarm. Down the left, the animals beside you on their posts ("1 of 3"; an open post takes the chosen animal out or
  beside you, a post not yet commanded is locked with the realm that opens it) and the stable, a stall a row with the
  animal looking out over its half-door, its level, role and element, a red mark on a wounded one. In the middle the
  chosen animal's leaf, a sheet between two timber rollers (HD `bestiary_leaf`): its name (a tap renames it), level and
  lock; what it is; the animal stood on its straw (it walks out onto the leaf when chosen, 0.4 s); its level, its bond as
  ten hearts and a Grievous Wound or hunger; its growth as stepping stones from Hatchling to Primordial with the next
  stage's gates ticked and what the stage opens; its bloodline purity with the stops at 50 and 90 named; its skills as
  chips; its traits and learned skills. The leaf's foot turns its lower half to **Grow** (lit when ready: the gates,
  Evolve, the two lines at Adult, a breakthrough with its support from Awakened; the aptitude, contract, core and
  resonance), **Feed** (its foods and its own element's cores), **Teach** (the learned slots and the books you carry),
  **Breed** and **Fuse**. The tack wall at the right: care (out or at rest, beside you, carried; the roles two or three
  across; its nature and the +25% a matching role gives), the three gear places (a worn piece comes off with a tap, an
  empty place lays the bag's pet gear on the leaf to put on), the nest (the egg warming with its three inputs, or its
  Hatch) and the swarm's chip, which opens the Swarm tab. A construct's leaf names its strikes and its keeping, with no
  bond, growth or views.
- **The Core Exchange as the Beast Hall's urn and tally** (row 34). On a wall of rough timber: your cores standing on
  shelves at the left, a tier a shelf with its price on a board; the glazed urn in the middle (HD `core_urn`, no words on
  it) with the chosen core at its mouth and Sell one and Sell all under it; your Spirit Stones, what the Exchange will
  still pay today and the prices at the right, over the heap of stones spilled from the spout; the straw bed in the
  corner with the wounded animals lying in it and Rest your animals; the day's bamboo tally across the foot, a notch a
  stone paid. A sold core drops into the urn and a stone clinks out of the spout (0.3 s).
- **The Beast Arena as the pit seen from the stands** (row 36). An oval sand pit ringed by a fence inside timber
  stands; the ladder's eleven banners round its rim in rank order from rank 1 at the top, each with its holder's name on
  a board as long as the name and the tamer's lead animal at the pole, yours in jade and the one you may challenge in
  gold; inside the pit your rank, the day's fights, what the week pays and who is next, and before any fight the next
  tamer's two teams and how the arena works; after one, the fight replayed as draining bars between the two sides;
  Challenge 1v1 and 3v3 at the pit's gate. A challenge raises your banner (0.3 s).
- **Shared:** `scripts/ui/pages/beast_kit.gd` (rough timber, straw, the rough board and the hung title board, the bar on
  paper with its stops, the heap of Spirit Stones); the leaf's inks are the Records family's (`RecordsKit`). HD
  `bestiary_leaf` and `core_urn` in `tools/ui/build_ui_hd.py`; `TEXT_ON` rows for ink on the leaf, on `sand` and on
  `straw`. Every intent is kept (roles, out and beside, carry, feed, devour, lock, rename, evolve, breakthrough, contracts,
  teach, pet gear on and off, breed, fuse, hatch and the egg's inputs, the swarm's feeding, core sales, rest, the
  arena's challenges).
- **Tests:** `rules_tests` `identity_suite` (the Beasts family: the stable and the leaf with its five views, each view's
  words on their grounds and its button turning it back, Feed offering the animal's own core and Fuse the other animals,
  the nest's inputs and Hatch, a construct's leaf, a role and a chosen stall through as intents; the shelves, the urn's
  Sell one and Sell all and the tally; every tamer's name whole round the pit and a challenge replayed inside it).
  Screenshots beside mockup 10 in `docs/ui_p5/beasts/`.
### P5 · The Workshop family: Crafts, Workshop, Garden (mockup 15; decision 14)
- **Crafts as the hearth** (row 18, mockup 15). The trade's vessel stands centred over its fire on a brick hearth: your
  own furnace (its icon at 192) or the station's prop at a whole scale (the pot, the anvil, the chart table), the blank
  plate, the spirit paper; the fire burns in the hearth's arched mouth, hot, steady or banked by trade, in the chosen
  fire's colour under the furnace, with the array's rings round its foot. The recipe's ingredients sit on the rim above
  it with what you hold of them (in the furnace also role, nature, stand-ins, Spirit Sense and a tap to swap). The steps
  run as a strip across the top (the furnace's five or six screens; else Recipe, Materials and the making), each with
  what it asks; the controls at the right change with the step and nothing else moves: the recipe book with the batch
  and the craft button, the fire and array, the strike band, and once lit the step's hint, the herb's time and the timed
  control (Fan the flame, Turn the array, Condense, Raise shield) at the foot. The five-screen game is played on the
  hearth: the heat gauge at its left, the specks at the furnace's mouth, the essences circling it, the ring closing over
  it, the storm above it. The Forge's upkeep and the Guild keep their lists on the wall with their modes or guilds on the
  strip; the Experiment bench lays your herbs on the rim. The vessel settles onto its fire as the page opens; a finished
  craft lifts out in a puff (0.4 s, none under Reduce motion); the flames hold still under Reduce motion and the battery
  saver, their height the heat.
- **The Workshop as the tool wall over the bench** (row 30). The six tabs are six tools hung on a pegboard (HD
  `workshop_tool`), each over its outline painted in ink; choosing one takes it off its hooks and lays it on the bench
  (0.2 s), the outline staying. The jobs lie on the dark bench below; the puppet blueprints scroll.
- **The Garden as terraced beds** (row 29). The beds step down the hillside on stone walls, soil darker the richer the
  field, each herb at its stage (shoots, then its icon at 32 and at 64, glowing when ready) with its field's grade on a
  staked tag; the water, Spirit Soil and dew in a basket at the top; the chosen bed's tending on a board at the right;
  the Racks tab as two bamboo racks with woven trays. The terraces settle into place as the page opens.
- **Shared:** `scripts/ui/pages/workshop_kit.gd` (the plank wall and beam, the timber board, brick courses, the fire,
  soil beds, pegs and the tags hung as tabs); HD `timber_sign`, `timber_tag` and `workshop_tool` in
  `tools/ui/build_ui_hd.py`; `TEXT_ON` rows for the sign, the tags and `soil`. Every intent is kept (cook, refine and the
  furnace's inputs, forge and the strikes, the Forge's upkeep, inscribe, trace, chart, build, experiments, Deduce, the
  guild, formations, appraisal, healing, puppets, restoration, teaching, planting, watering, dew, soil, harvest, racks).
- **Tests:** the `ui_suite` and `identity_suite` measure every word of the three on its ground and hold the new
  signatures apart; the furnace suite plays the page's five screens as before. Screenshots beside mockup 15 in
  `docs/ui_p5/workshop/`.

### P5 · The Market family: Shop, Storage, Exchange, County Hall, Auction (decisions 11, 14 and 24)
- **The Shop as the merchant's stall** (row 8, mockup 17; `17_shop_buyback` rejected). A red and cream awning with the
  shop's name on a black lacquer sign; the merchant behind her counter at the left (her own layers at 2.5) with her
  nameplate and a bark of hers in a bubble; the wares on two plank shelves, five a shelf, each on a jade mat with a paper
  price tag (the rotating ones flagged "today"; more shelves a drag away); the deal on the counter plank (the ware on its
  cloth, its grade and how many you hold, what it does, − n + ×10, the total and what is left after, Buy n); the purses
  on the counter's front, the shop's own coin ringed. No tabs: beside the stall "your bag" is a patch of the Bag's
  heaven (decision 24), the gourd's spaces floating five across with what each sells for under it, and Sell 1 · All n on
  the sea of cloud. Buy-back is a small token in the bag's header (decision 11): it turns the same spaces to the last
  sales, each with its buy-back price. A bought ware slides down to the counter (0.25 s).
- **Storage as the storehouse chest** (row 19). The camphor chest's lid thrown open over the right two-thirds (HD
  `storehouse_lid`, swinging up as the page opens), the account's things in its lacquer tray, and the Treasury's spaces
  (`storage_slots_per_level` a level) as a second tray under a partition; the chest's front says how full it is and what
  the Treasury adds, or would. The gourd's side at the left is the Bag's heaven lit from the gourd's mouth. A tap moves a
  thing across, arcing over (0.2 s).
- **The Exchange as the money-changer's barred window** (row 33): the rate board, each pair's rate on its rail, the
  changer's coin trays behind brass bars, the coin slot, your purses on the counter and the trades under the slot.
- **The County Hall as the magistrate's bench** (row 37): the plaque over a painted screen of sea and sun; county favour
  as a cinnabar banner with its tiers written on its paper (sealed once held); today's jobs as warrant sticks in the tube
  on the desk (tipped red, gold once done), the chosen one drawn up and its warrant hung at the right; the relief box on
  the desk opens the relief ledger; the tabs are two red placards.
- **The Auction as the stage** (row 38): the chosen lot on a pedestal in a cone of light (its slot at 2×), the lot board
  with its price, holder, time and premium, two numbered bid paddles, and every lot on a small pedestal along the
  stage's front, a tap bringing it up (0.3 s).
- **Shared:** `scripts/ui/pages/market_kit.gd` (planks, brass fittings, the lacquer board, price tags, the gourd's heaven
  and its floating grid, a thing in flight); the Bag's sky pieces are statics of `inventory_page.gd` now, which the Bag
  itself draws from (its look unchanged); `DialoguePage.full_outfit` fills an NPC's outfit for the dialogue portrait and
  the merchant. HD `market_plate` and `storehouse_lid` in `tools/ui/build_ui_hd.py`; `TEXT_ON` rows for words on
  `lacquer_black`, `lacquer`, `market_plate`, `board`, `bamboo` and `scroll`. Every intent is kept (buy, sell, buy-back,
  deposit, withdraw, exchange, county jobs, relief, bids).
- **Tests:** `rules_tests` `identity_suite` (the Market family: the stall with no tabs and its wares in view, the bag in
  the heaven with its sale prices, a tapped ware on the counter, a sale and its buy-back through the token as intents;
  the Treasury's tray; the rates and trades; a stick per job and its warrant, the relief ledger's Give per gift; every lot
  on a small pedestal and a tap bringing it up; every word read on its ground), the `ui_suite` with the chest with a
  Treasury and the stage with its lots. Screenshots beside mockup 17 in `docs/ui_p5/market/`.

### P5 · The way family: Cultivation, Breakthrough, Revival, Fates (mockups 04 and 05; decision 14)
- **Cultivation as the mountain ascent** (row 5, mockup 04). The shared window, plaque and eight tabs stay, as the
  approved mockup keeps them. The Overview's left is the night mountain: every great realm a waystation on one dashed
  path from Mortal up. The realms passed are gold and ticked, this one is lit, and the next two are named (the next with
  what it opens). The far ones fade into the mist. In the middle stands this realm's stair, nine steps, or three, or
  one, in the Early, Middle, Late and Peak bands with their chips. The step reached is ringed, with its bar inside it
  and the figure seated on it (the live Avatar, meditating); it climbs when a step is gained while the page is open
  (0.3 s, none under Reduce motion). The riser to the next step glows at a bottleneck, later steps that open something
  carry a gold mark, and the gate to the next great realm stands on the last step. At the right: the Level badge, the
  stage and its band, the method line, the bar, Stored Qi, the body's ledger (the old Overview's rows, kept), the next
  step with chips of what it opens, the gate's asks from the rules, Meditate and Breakthrough.
- **Breakthrough as the heaven gate** (row 9). A stone archway against the night: the title on the beam's gold-leafed
  plaque and the step it leads to in the doorway, with the trial under it. Each requirement hangs from the beam on red
  cords as a tablet, gold-leafed when met, dark with its Go when not; a minor step hangs one tablet that says so. The
  risk and the chance are cut into the two pillars. Supports are chosen from the stele at the right, which also lists
  what weighs on the attempt, and lie in the three jade dishes on the step (a tap takes one back). Core Forging's
  checklist stands on the left stele. Break Through on the threshold opens the doors (0.5 s; a cross-fade under Reduce
  motion), then the page closes into moment 05; the gains card and aura of the early-game rewrite are unchanged.
- **Revival as the life lamp** (row 39). A bronze lamp in a stone niche, its flame guttering and then steady (0.6 s;
  steady under Reduce motion or the battery saver). What the fall takes is at its left in the shadow: red past the
  grace, pale gold while a fall costs nothing. The early grace before Bone Forging 5 is told in full on the first fall
  and in a line after. What you keep is at its right in the light, and the choices are under the lamp.
- **Fates as fortune sticks** (row 40). A bamboo cylinder low in the centre under the stars, three sticks fanned out
  of it, each slip with the fate's name, its gift above and its cost below and Take this fate at its foot; the sticks
  rise one after another inside the opening (a tap shows all).
- **Shared:** `scripts/ui/pages/way_kit.gd` (the night and its stars, coursed stone, the stone tablet, a red cord, a
  flame). HD `stone_tablet` (dark and gold-leafed) in `tools/ui/build_ui_hd.py`; the `niche` surface (`HOLLOW` + 0.85
  `INK`); `TEXT_ON` rows for `sky_top`, `space`, `niche`, `stone_tablet` and the slips' `scroll`. Every intent is kept
  (meditate, the tabs' intents, start_breakthrough with its supports, choose_revival, choose_fate); the Meridian badge
  still opens Cultivation on Foundation.
- **Tests:** `rules_tests` `identity_suite` (the way family: every great realm named once on the mountain and a
  numbered step for each stage; the figure climbing when a step is gained; Foundation opened by its tab; a tablet for
  each requirement, as many gold-leafed as are met, no two buttons touching; a chosen support in a dish; the doors
  opening over 0.5 s with nothing else answering; a minor step's one tablet; the early grace in full at the lamp's left
  and what is kept at its right; a slip and Take this fate for each card; every word read on its ground). Screenshots
  beside mockups 04 and 05 in `docs/ui_p5/way/`.
### P5 · The sect family: Menu, Your Sect, Sect, Characters (decision 14; mockups 03 and 11)
- **The Menu as the sect's hall of hanging plaques** (row 4, mockup 03, approved). Inside the shared window, a lacquered
  hall with its lattice frieze and floor; five bays (Self, World, Bonds, Works, System) under their plaques between
  red-lacquered pillars, each entry a teal lacquer tablet hung on the bay's gold cord: its seal and glyph, its name and,
  when something waits there, a line (Bottleneck reached, chests to claim, slots set, the rank held, who asks to join,
  a letter's sender, what opens a locked one). A vermilion ready seal, Mail's count or a new mark sits in the corner;
  the character line and the purses stand on the floor. The tablets sway once as the page opens, a seal is pressed on.
  The HUD's Menu seal reads the same entries (`MenuPage.ready_seals`); `UiKit.count_badge`, `ready_seal`, `new_mark`
  and `pill` are shared by the HUD and the pages.
- **Your Sect as the courtyard under construction** (row 24, mockup 11). Tabs Courtyard, Expeditions, Territory. The
  Sect Grounds drawn from the room's own backdrop layers and props, scaled once smoothly: all fourteen buildings where
  the room places them, raised ones solid, the rest dashed bronze scaffolds, one being raised filling from the ground
  up; tags (level, "to raise", or the sect level with a lock) placed by the World map's layout pass so none touches;
  the disciples at home idling in the yard, the day's candidates at the gate. Under it the sect level, prestige and a
  bar with stops three levels ahead naming what each opens; then the building tapped (what it gives, the next level's
  cost, what is short, Build with its lock and reason, Repair, Open storage), the disciples (rooms, each disciple, the
  candidates, Recruit taking the one tapped) and Beyond the Walls (Expeditions and Territory one tap each, the
  builders). `SectAuthority.upgrade_check` (why a raise would fail, the check `upgrade` itself runs) and
  `prestige_for`.
- **The Sect as the hall's seats seen from its door** (row 25). One-point perspective drawn from tokens: walls, beams,
  floor boards, red pillars, the master's dais and screen; a row of cushions for every rank coloured by rank, nearer
  rows lower, your seat lit with you sitting on it, the next rank's row lit with its trial on a lacquer board; Missions
  and the Sect Shop as the side doors. The title is the sect's own name. The Role tab's variants and tree hang as
  lacquer tablets on two timber boards.
- **Characters as the roster handscroll** (row 32). On the timber wall between two pillars, the scroll unrolled from
  its rod (HD `handscroll`): each disciple painted as its live figure at 2 px an art px with its task's sign at its
  feet and a column of name, realm and task in ink, the one you play under a red "Playing" seal; an open slot a blank
  stretch; the roll at the end as thick as the slots still to come, the next three gates on paper tags. A tap chooses a
  disciple: under the scroll the one you play sets its task, another offers Switch. It unrolls as the page opens.
- **Shared** (`scripts/ui/pages/sect_kit.gd`): pillars, lacquer boards, the title board, the timber wall, live figures
  and smoothly scaled pixel art. Every intent is kept (open, set_idle_task, switch, promotion, role, tree, shop,
  missions, found, upgrade, repair, recruit, expeditions, mines); behaviour unchanged (sect membership and guidance,
  no quest needs a second character, dailies after Qi Kindling 1).
- **Tests:** `rules_tests` `identity_suite` (the sect family: every Menu entry once in its bay, locked ones saying what
  opens them, the bottleneck's seal matching the HUD's; every building placed and tagged with no two tags touching,
  the card and Build's reason, Recruit taking the tapped candidate, the figures at whole pixels; a row per rank, your
  seat, the trial and the doors; a stretch per open slot, the roll's thickness and gate tags, the task buttons; every
  word read on its ground). Screenshots beside mockups 03 and 11 in `docs/ui_p5/sect/`.

### P5 · The Post family: Roll-Call, Works, Welcome Back, Pouches (decisions 11, 14, 21 and 26)
- **Roll-Call as the sect's duty board** (row 14, mockups 13 and 13_first; decision 11, friendlier and more interactive).
  A pale name tablet per character hangs from the peg rail on a red cord, its arched window holding the character's
  live figure (the Avatar at 3 px an art px, clipped to the arch: standing while played or working, seated at rest), the
  craft and its level, the place and a band that says how the post stands (playing now, full and idle for how long,
  full in how long, on vigil, no post). A tap turns the tablet over (0.25 s) to its back: the level and Finesse, what it
  brings in an hour, the first output's Chance or Abundance bar and the Hour Incense. Under each tablet the pouch is a
  woven vessel on the shelf (a basket, a creel or a cage by what the post fills) heaped with the goods to its level and a
  paper tag with the count (red when full), then one big Settle and a Switch. Soonest full first, four at a time with
  page arrows past four. Settle all with its goods and ready seal, the Storehouse as a cabinet of drawers under a tiled
  roof (tap to take 50, Auto-Settle) and the Bench as a work table (what the apprentice made, Collect, points to spend,
  the craft levels to the next point and apprentice) stand at the right. Board, Crafts and Vows hang as tags on the beam;
  the Storehouse's and the Bench's plaques open their full views (every drawer and the Granary Seal; the apprentices and
  the bench points). A new player's board (Keeping Post not yet done) pins a note that teaches the loop in three steps.
  `PostAuthority.roll_call` rows also carry `cap` and `idle_h`.
- **Works as the curio cabinet** (row 23, mockup 14 v4; decisions 21 and 26). The seven works are the compartments of
  an irregular bamboo shelf, and the compartments are the tabs: each object drawn at its native 96 from
  `tools/icons/families/works.py` (the drawings moved there from the study; the icon build renders them at 64 and
  `@96`, and `SpriteCache` reads 96 px renders), its state on a hemp label (points to spend, seals the Storehouse can pay
  for, the highest stele, flags planted, the lit line, favours granted, the mirror), a ready seal where something
  waits, a locked one dark behind a lattice with what opens it. The chosen work's list lies on the tray below; the Seal
  Scripts show five rows at once. The inventory slip at the right writes what the works add for the character, craft by
  craft and at every post, and the Storehouse and silver they are paid with. Every work's actions are kept.
- **Welcome Back as the incense coil and the winnowing tray** (row 12). The coil on its bronze dish is burnt from its
  outer end to the time away out of the cap (the account's `idle_cap_h` and the sect's bonus), the ember at the mark
  (it runs there as the page opens; drawn at its mark under Reduce motion); the goods drop into the round bamboo tray
  one after another (a tap names one); the rest of the summary and the post's Return Ledger is on a hemp slip; To the
  Storehouse and Keep in pouch, or Collect, under the tray.
- **Pouches as the tailor's chalk patterns** (row 44). Seven drawstring pouches chalked on the cutting cloth in two
  staggered rows, each at its tier's size with the next tier dashed round it and its compartments ruled inside, the
  category's thing in it, what it holds, the next fold and its price, and Sew, which runs a stitch round the pattern;
  a bamboo ruler across the corner.
- **Shared** (`scripts/ui/pages/post_kit.gd`): arches, basketry, paper tags, hemp labels, the lattice screen, planks,
  dashed outlines and the ready seal. `TEXT_ON` rows for words on `wood_dark`, `wood`, `bridge`, `hemp` and
  `talisman`. `--welcome-demo` (a debug tool) opens Welcome Back from a real Return Ledger of 7.5 hours at a post.
- **Tests:** `rules_tests` `identity_suite` (the Post family: a tablet per character, the one played first, soonest full
  first, Settle and Switch under each post, the tags' counts, the figures whole-pixel and clipped, a tap turns a tablet;
  the seven compartments as 48 px tabs, each object at its native 96, a closed work saying what opens it, five Seal
  Scripts at once; the coil burnt to the time away out of the cap and every good in the tray; seven patterns, a deeper
  pouch larger; every word read on its ground), `icon_draw_suite` (the Works objects' 96 and 64 renders), and the
  `ui_suite` in every tab. Screenshots beside the mockups in `docs/ui_p5/post/`.

### P4 · The style guide applied (`docs/ui_style_guide.md` §11, §12)
- **Tokens.** `UiKit` gains the roles the palette left to literals: `RED_TEXT`, `SOUL_TEXT`, `WARNING`, `HP`, `BLOOD`,
  `HEART`, `SKY`, `HUD_LABEL`, `PAPER_INK`, `BAR_TROUGH`, `PLATE`, `DIM` and `SURFACE`, the drawn pages' own materials
  (the map scroll, the Go board, the zither, talisman paper, the tribulation sky, the furnace). Every hex and float
  colour literal in the pages, `Page` and the HUD is a token now (64 and 55 of them); red and violet words take the
  text tokens that pass 4.5:1. Sphere's name colour is #9a87e3 (4.81:1, from 4.17); the three grades past it keep the
  colours P7b gave them, and every grade is checked to have one. The HUD's buttons are the HD kit's new `hud_ring` (132, 64, 52 and 48 px; normal, pressed and
  active), and a held button sinks.
- **Contrast, option C (decision 10).** The bright jade primary face stays; primary labels in every state, page titles
  and the dialogue speaker carry a 2 px ink outline (pale gold 15.6:1, a disabled label 6.2:1, where the face alone gave
  2.13 and 2.64). Plates over the world are 0.72 (`PLATE`: secondary words 4.56:1 over a white sky), and the HUD log is
  outlined. The option B previews are gone; `00b_button_faces.png` stays as the record.
- **Type.** Every word is asked for on the scale (14, 16, 18, 20, 22; Cormorant 22, 26, 30, 34) and none under 14;
  buttons and headings step down the scale; paragraphs default to 18; the HUD realm is 16 and its bar labels 14.
- **Numbers, durations, plurals.** Numbers over the world shorten to three figures from 10,000 ("18.2K"); a value of a
  total reads "a / b". Every time left, wait and cooldown is written by one `Tx.span` ("1 h 6 m", "3 h", "2 d 5 h"),
  in the simulation's messages too; six duration strings retire. 75 counted strings gain their singular ("1 heart").
- **Spacing and windows.** Page layout on the 8 px grid: content 32 px in and 80 under the title, 48 px tabs 8 apart,
  a 512 × 224 confirm dialog; the twelve pages with windows of their own take one of the six standard windows, and the
  dialogue strip sits inside the safe area; list rows on the grid; the Bag grid 16 px from its detail panel.
- **The figure on the Character page (decision 8)** is drawn at 3x, crisp, with the worn slots round it (the Bag's own
  drawing); a tap on a slot opens the Bag on it.
- **States.** Settings' toggles are on in the selected art and Off in secondary grey-blue, not the disabled grey. The
  character you play, your row in the Heaven Ranking and the Body rung you climb are marked with a gold ◆ rather than
  the selection glow.
- **Touch.** Every HUD control answers in a circle at least 48 across and its drawn radius + 4 (the Draught, the bag
  animals and the icon row were short); where two overlap the nearest centre wins; the tracker's go button is 48 × 48,
  and the Soul row opens Character.
- **Found in the screenshots, fixed:** the quest tracker's plate hid the status icons (it now starts under them); menu
  tile names touched their frames; a Welcome row's words ran into its value; the vow rows were shorter than their
  buttons.
- **Checks:** `rules_tests` `ui_style_suite` (no off-token colour, every grade coloured, every text colour measured on the
  kit art it sits on, the HUD's text sizes, pressed only under the finger) and `hud_suite` (the HUD's targets); the
  `ui_suite` holds every page to the type scale, the standard windows and the grid; `contract_tests` holds durations to
  the span and every counted plural to its twin. The audit before and after is in the guide's §12; the pages and the HUD
  re-taken from the valley_run checkpoint `ls6_end` are in `docs/ui_after_p4/`.

### P2 · The close-out: rooms walked, objects apart, the mark follows the objective (M16–M18, M20)
- **Every room walked (M16).** A new suite, `room_sweep`, walks every room headless with the real movement solver. It
  checks that every door and interactable can be reached from every way in and that every arrival reaches a way out.
  It walks the route between every pair of them and fails on a body held in place, and it fails on any solid
  footprint that sticks out past its art (an invisible wall). It takes about 18 s.
- **No more walking in under the steps.** In the Herb Terraces, the East Terrace, the Pavilion Rooftops and the Cliff
  Stair the ground ran on under the raised stairs and landings. A walker along the back row ended up inside the
  staircase, and pressing up did nothing there. The ground is now solid under any raised ground surface more than 8
  above it (`under_steps()` in `tools/data/world.py`).
- **No interactable hides another (M18).** A `data_validation` rule fails when one interactable would take the
  context button from another where it stands, or from a door. It found 41: NPCs in six interior doorways and on three
  anvils, chests over ledge herbs, signposts on sealed ways, the Gate Street bunk on the Weapon Hall's door, the
  recruiters on their tent doors, a gravity switch on a herb. All were moved in the builders. Nodes and chests lifted
  onto a tier now keep out of each other's reach.
- **The context button looks at height.** A chest on a ledge could take the button from the herb below it and then
  say "out of reach". The button now skips anything more than 48 above or below, as the interaction already did.
- **The dummy case, played (M17).** As the valley_run character: between Uncle Guo and his dummy the button talks to
  Guo and a blow strikes the dummy only. On the dialogue page a last line with nothing to choose, an accept and a
  hand-in (Stone and Sweat, played on the page) all close the conversation by themselves.
- **The direction mark follows the objective (M20).** It leads to the current objective's place: the room it names,
  the NPC where they stand now and in your own sect, the nearest room with the foe or the herb, the room where a
  dropped item drops. It goes as far as the room that hides a hidden way. Before, 18 main and guided quests had no
  mark and 27 marked one room for every objective. Hand-in marks could point at the Weapon Master's yard before he
  moves there, at Aunt Ping's hut after the Hollow Night, and at the other sect's arena.
- Tests: `room_sweep`; `data_validation` `overlap_suite` and `quest_guidance_suite`, which plays every guided and main
  quest on a probe set at the point where the story offers it (giver, marker, offer, each objective's mark and route,
  the hand-in); `rules_tests` `guidance_suite`; `valley_run` bf5.

### The code review (`docs/review-code.md`)
- **Bugs fixed, each with a `fixes_suite` test that failed before:** the Relations and Calendar authorities now tick.
  Buyback returns the stack as sold and charges only for what fits. Every item instance keeps its own uid across bags
  and splits. A full bag beside loot is announced once, not every tick. Guild orders never take locked pieces and turn
  over with the daily reset. A Wind Step charge is spent only by a dodge that happens. One answer to "the Dao you know
  best" (`ProgressionRules.strongest_dao`) serves the Sphere, Dao Echo, the chess problems and the insight sites. The
  fall cost moved from `world.gd` into Combat.
- **Each authority writes only its own state; pages only submit intents (B19).** Two new intents, `mark_item_seen` and
  `settle_works`, replace the pages' own writes. A `contract_tests` check fails if a page, the HUD or the shell writes
  character or account state.
- **Duplication removed:** one way to mint a uid and find a piece, one dodge cooldown, one defeat path, one in-game day,
  one dotted config lookup, one node yield for gathering and harvest, one duration helper (`UiKit.span`), and the data
  builders' requirement constructors and reach table written once. Dead code removed. `scripts/` and `tools/` are 210
  lines shorter, and `data/` rebuilds byte-identical.
- **Left, with reasons in the review:** whether an ally's blow breaks a monster's wind-up (the pet and companion tests
  say it should; a design call), the three durations whose wording differs, and the two-column page layout (the
  restyle rewrites those pages).

### P2 · The UI bug pass (B1–B25 of `docs/review-v12.md`)
- **Broken, now working:** a Dao at tier 5 or 6 no longer throws a script error every frame, and each Dao row shows
  its own next target (B1). The guqin plays from the key-item pouch (B2). "Trial: <null>" is gone from great
  breakthroughs with no trial (B12), and the HUD, the Cultivation badge and the Ranking show the same Level (B15).
- **Layouts that ran off the window:** the Titles, Secret Arts, Expeditions and Favours lists scroll inside their
  window, the Promotion trial button no longer sits under Missions, the Teleport Stones rows keep 48 px with ten
  stones, and the Paths, Body, Beast Arena and Sect tree cards neither overlap nor stop mid-sentence (B4, B5, B7, B16,
  B17, B18, B22, I7, I9). The `ui_suite` now opens the context pages as well as the menu pages.
- **Words:** every label is fitted at the size it is drawn (B21, I6). Text written in scripts moved into the strings,
  with a `contract_tests` rule (B8). The Roll-Call shows a post for a character keeping one (B20), the three named
  debts show their names (B24), the Sweep button tells the truth on a day with no floor cleared (B25), and the keyboard
  help names every key (B23). Origins have names and a line saying what each one gives (B10).
- **One version, from one place (B9):** `project.godot` holds `application/config/version` ("1.2"); the title screen
  reads it and the Android presets leave `version/name` empty so the APK takes it too. The APK's visible version moves
  from 1.0.4 to 1.2; the version codes stay 104.
- **Selections:** the kit's selected and disabled panels are built from the normal art, so a chosen row looks chosen
  everywhere (B3, I3, I4). The HUD tracker keeps an objective's count whole (B11).
- B6 was fixed in P4a; B19 (pages that change game state) goes to the code review. I2, I5, I8 and I11–I14 go to the
  P4 style guide.

### P7b · The item and archetype plan
- `docs/item_plan.md`: today's gear counted by zone, grade, slot and archetype; a target of 481 pieces through v1.3
  (264 named); 24 archetype sets; drop rates cut to about 6 pieces an hour of hunting with a `balance_sim` drop check;
  a source for each of the 43 unsourced items; the Bedrock Pill (Solid stability); and the sprite gaps by region.
- **Named pieces leave the random pool.** The Serpent-Tongue Jian and the Tidebreak Bastion's brushes and bells carry
  `named` and never come from the banded equipment roll; Expanse foes dropped Act III's Bastion weapons before.
- **The Drowned Abbot's robe** drops on his first defeat only, not on every kill.

### P9 · The boss design, and what it found
- `docs/boss_design.md`: all 13 bosses redesigned (phases, a telegraphed arena mechanic each, enrage timers, reward
  loops, intro and phase cards), the shared marker system, the build order (P9a–P9f) and `boss_suite`.
- **Untouched can be earned.** Its achievement waited on a `boss_defeated` event nothing sent. A dungeon or story boss's
  fall now announces it, clean when no grave wound came first in the room; Untouched asks for a clean dungeon boss.
- `boss_phase`, `enemy_summoned`, `boss_fled` and `boss_defeated` are in the event contract, so `contract_tests`
  checks who sends and hears them (`boss_event_suite` in `rules_tests`).

### P10 · Findings fixed
- **The Account Legacy records again.** It waited on an `account_legacy` unlock that was never defined, so its +2%
  accumulation per recorded great realm was always 0. The unlock now opens for the whole account at Bone Forging 1, and
  a save that reached great realms before this has them recorded once when it opens (`legacy_suite` in `rules_tests`).
- **The old scrolls' names.** Twenty Codex entries set the common xianxia ladder's names beside Jade River's realms
  (Heart Tempering beside Foundation Establishment, Cloud Stride beside Core Formation, and so on); each opens the
  first time the account reaches that great realm (`docs/realm_old_names.md`).

### P3 · Fixes found by the mockups
The open items the mockup agents listed while drawing (`docs/mockups/README.md`), each with a test in `rules_tests`
(`mockup_fixes_suite`) or `data_validation` that failed before.
- **A sect building takes its materials from the Storehouse and storage too.** The Treasury no longer waits while 49
  Copper Ore sit in storage: a build spends from the bag, then the Storehouse, then the storage chest. One spend path
  (`InventoryAuthority.count_owned` and `apply_spend`) serves the sect builds and the Post Vows, each store written by
  its own owner (`PostAuthority.apply_take_storehouse`, `AccountAuthority.apply_take_storage`).
- **Every sect building has a place in the Sect Grounds.** The Herb Terraces (three garden beds before the Treasury),
  the Expanse Outpost (a watchtower beside the pagoda), the Mirror of Echoes (a bronze mirror before the Meditation
  Pavilion) and the Ancestral Shrine (an ancestors' altar by the shrine) appear in `hv_sect_grounds` once raised, like
  the other ten. They pass the room lint, the `room_sweep` and the `overlap_suite`; a `data_validation` rule fails on
  a sect building with no place there.
- **The Treasury's output says what it gives.** Its key `taels_per_level` sized the storage chest; it is now
  `storage_slots_per_level` (20 spaces a level) in the builder, the data and `SectAuthority.treasury_bonus`.
- **`move_speed` is a number.** `stats.json` gave it the percent format while the Character page shows the speed
  itself (242), so a flat bonus would have read "+2000% move speed". Its format is `int`; a test holds that every
  percent stat is a share.
- **Technique sources have names.** Each of the 26 sources (`library_1`, `night_peddler` …) has a string
  `technique_source.<id>` ("Sect library, first floor", "Peddler Shao's night mat"; a quest reads as its name), read
  with `ContentDB.name_of("technique_sources", id)` where a technique's source is shown (an unlearned star's line on
  the proposed Techniques sky). A `data_validation` rule fails on a source without one.
- **A locked feature says everything it waits on.** `Unlocks.locked_text` has one rule: a system's own locked text if
  it has one; else every trigger condition still unmet, in order ("Reach Qi Kindling 1 · Complete "Keeping Post"",
  where it named only the first); and when a quest is all that is left (the one unmet condition, or the system's own
  quest once the trigger holds) that quest and who gives it ("Take "An Idle Art" from Elder Hu", where it said "Not
  yet available"). `RequirementRules.unmet` gives the unmet conditions, and `first_failure_text` is its first.
  `data_validation` holds that every quest the rule may name has a giver.
- **The hub's Works tile reads the same rule.** It showed Keeping Post at `qu5`, where Keeping Post is done; the hub
  asks `Unlocks.locked_text` for its locked tiles, so at `qu5` Works now waits on Elder Hu's An Idle Art.
- **Every weapon family has a stance held without buying anything** (found by the technique planner). The jian's only
  stance was Willow Leaf Parry, also a technique bought at the library, and bare fists, the brush and the bell had
  none. Four basic stances join the eight: Guarding Blade (jian: a parry counters for 120%, attacks 10% slower),
  Tiger Crouch (fists), Steady Wrist (brush) and Deep Tone (bell). Willow Leaf Parry stays the jian's better stance
  (200%) and now holds only for one who has learned its technique (`ProgressionRules.stance_known`, used by
  `set_stance`, the active stance and the Techniques page). `data_validation` holds one basic stance per family.
- **Found, not fixed: the Copperjaw swarm has no creature art.** No sheet fits: `rock_beetle` is the quarry's grey
  stone beetle (an enemy) and `jade_scarab_swarm` a jade insect-netting prop. Nothing maps the swarm to art today (the
  Swarm tab draws none); a new `copperjaw_swarm` sheet in `creature_art.json`, named by an `art` key in the `swarm`
  config of `stats.json` as `pets.json` names an animal's, is a pixel-art task.

### P3 · The first mockups, approved
- Mockups 00–05 (the kit, the HUD in a fight and at rest, the hub, the cultivation ascent, the breakthrough) approved
  by the user, with two notes, both recorded in `docs/roadmap_master_ui.md` §6.
- **The portrait roundel is gone.** The HUD's player panel no longer draws a circle with the character's initial: the
  name and realm sit at the panel's edge, and the HP, Qi and Soul bars take the width it freed (288 px, 14 px tall,
  their numbers inside and grouped by thousands like every page's). The bottleneck, which the roundel's ring showed,
  shows on the Stored Qi bar.
- An icon style study is under way for the user's second note, that every icon in the game should look better.

### P4a · Touch targets
- **Every tap target is at least 48 px on a side.** `Page._register` gives smaller art a margin of hit area round its
  centre (`Page.MIN_TAP`); the art keeps its look. Tabs, which are 40 px tall, now answer a tap anywhere in 48.
- Buttons that were 36–46 px tall are 48: the stance, wardrobe, meridian, path, vow and ledger buttons, the bag's sort,
  the forge mode and guild pickers, the guild exam, the bench points, the core exchange's rest, the Settings toggles and
  the volume steps.
- The stances on the Techniques page's Inner Arts tab are a scrolled list: nine families no longer squeeze nine buttons
  into the panel's height.
- **Numbers that read.** Under 20 px, numbers are drawn in the bold serif's lining figures: in Pixelify Sans a 5 read
  as an S and a 2 as a Z on the HP, Qi and Soul bars. Damage numbers and large counts keep the pixel face.
- The emote wheel lies on an ellipse that fills its dialog: on the old circle the diagonal buttons overlapped their
  neighbours.
- Tests: `rules_tests` `ui_suite` opens every page and tab with every system unlocked and checks that every tap target
  is at least 48 px on a side, that no two buttons share a point, and that text asked for under the minimum size is
  drawn at the minimum.

## V10 · Keeping Post (idle gathering)

The idle gathering milestone (docs/idle_gathering_design.md), after IdleOn's AFK model in Jade River's own names. It
runs between v1.2 Phase B and Phase C.

### P1 · Guidance and gaps (docs/roadmap_master_ui.md)
- **Quest direction.**
  - The tracker names where a tracked quest leads ("➤ Reed Shallows · Lotus Ferry").
  - The minimap's exit toward it pulses gold, with a gold chevron on the frame's edge pointing the way.
  - The world map marks the destination's region with a pulsing gold quest mark and lists the room with a ◆.
  - The main story's quest leads when several are tracked.
- **Head markers, all four.** Gold ! for the main story. Blue ! for a new side quest. The new **jade-ringed gold !**
  marks a new quest from someone you have already helped. Gold ? means ready to hand in. The new **grey bubble of
  three dots** marks a quest of theirs under way. The minimap mirrors the jade ring. The grey bubble does not pull
  the context button to the NPC.
- **Every loot table rolls equipment or says why not.**
  - The five story bosses now drop superior gear like the other bosses.
  - Event foes roll gear like normal foes (3%); jars roll 2%.
  - Spar and trial opponents carry `no_equipment: "spar"`, and the three story vaults `"set_reward"`.
  - A new data-validation rule enforces both.
- **Boss phases.**
  - The Reflection calls up a heart demon at half health and enrages at a quarter.
  - The Hollow Behemoth sheds Hollowed boarlets at 60% and enrages at 30%.
  - Elder Gu cannot be hurt yet, so his phases run on the fight's clock (`after_s`): hired blades at 20 s, a
    cornered rat at 40 s.
  - A validation rule requires phases on every boss.
- Tests: `guidance_suite` walks one NPC through side, again, progress and ready, and checks the route mark and the
  destination's name. The valley run stands beside Uncle Guo's dummy (a blow opens no conversation; beside Guo the
  button talks). A `--guide-demo` debug flag shows every marker in Lotus Ferry.

### V10d3 · The first month
- `balance_sim` plays 30 days of twelve characters: three to each gathering craft on successive rungs, 20 hours a day
  at their posts, and a day's silver from active play. It buys the account web greedily: Post Arts, craft seals,
  steles, the Favour of the Guilds, the Cinnabar line and two plain flags.
- By day 30: craft level about 35, seals at 14 and steles about 18. Craft Diligence is about 62% from arts, the
  Guilds and flags alone. The web multiplies Finesse by about ×1.9.
- The checks hold Craft Diligence between 60% and 80%, the Finesse multiplier between ×1.5 and ×2.5 and still
  growing, and the Cinnabar line at rank 3 or higher. The design doc's §8 records the month.
- Found on the way: GDScript lambdas capture locals by value, so the simulator keeps shared state in a Dictionary.

### V10d2 · Furnace, Flags and the Mirror
- **Calcination Furnace** (Array Master Ren's Fire and Salt, Heart Tempering 6 with the Formation Guild): six salt
  lines on the Works page. A lit line burns floor(rank^1.5) × qty of each input from the Storehouse every cycle (15
  min for the first three salts, 1 h after) and banks floor(rank^1.3) fire; Refine turns the fire into **Essence
  Salts** (Cinnabar, Verdigris, Azurite, Pearl, Amethyst, Star) and ranks the line up at floor(20 × rank^1.8)
  refined. Each line from the second also burns the salt before it and opens when that line reaches rank 3; a
  starved line waits. Lines keep burning while the game is closed (up to 90 days).
- Essence Salts pay for Seal Scripts past level 10 (seals now go to 30) and for the pick, sickle, rod and net tiers
  6–8 (Cinnabar, Verdigris, Azurite).
- **Formation Flags** (Elder Bian's Flags over the Posts, Heart Tempering 8): two flags, each planted for 500 taels
  in a room with posts; a plain flag gives its posts +1% Craft Diligence (+0.1% a level), a deep flag +2% Finesse
  (+0.2% a level); salts raise them to level 20.
- **Mirror of Echoes** (a sect building, Elder Hu's Echoes in Bronze): a slot at level 1, a second at level 5. A
  disciple with the new **Echo Sampling** art (10% + 0.075% a level) inscribes that share of its post's hourly haul,
  +5% a Mirror level; the Mirror keeps adding it to the Storehouse whatever the disciple does next.
- **Auto-Settle** (with the Seal Scripts): a returning disciple's haul goes straight to the Storehouse without the
  Return Ledger. **Favour of the Granary Seal** (a fourth Magistrate's Favour): a chosen post fills the Storehouse
  directly, past its pouch. Both toggles are on the Roll-Call's Storehouse tab.
- Tests: `works_suite` covers the furnace (cycles, starvation, refining, rank-up), seal salts, flags, the Mirror and
  the options; the valley run lights the Cinnabar line, refines it and plants a flag over the Reed Shallows.

### V10d1 · Arts, Seals, Steles and Favours
The account web's multipliers (docs/idle_gathering_design.md §6), on a new **Works of the Post** page (the menu's
Works). Every source uses one of two curves: add (x1·L) or decay (x1·L/(L + x2)).
- **Post Arts** (Elder Hu's An Idle Art, Qi Kindling 6): a character's own, one point for every two craft levels
  across all crafts; forgetting them all costs 1,000 taels.
  - Dreaming Artisan 20·L/(L+40) Craft Diligence; Sleeping Sword 20·L/(L+50) Martial; Water-Clock Breath 8·L/(L+50)
    both; Steady Hand 30·L/(L+60)% Finesse; Deep Sleeves 60·L/(L+60)% pouch capacity; Windfall Knack and Flowing
    Hand feed the Windfall and Flow terms of a post's rates.
  - Hunter's Recall (one point) now gates taking up a snare from afar, at half the catch.
- **Seal Scripts** (Old Scribe Bai's Seals in Red Ink, Qi Unfurling 2): account-wide, paid from the Storehouse,
  ceil(25 × 1.12^L) of the seal's ladder item for the level band. A craft seal gives +3 flat Finesse a level to its
  craft; the Deep Pouch seal pouch capacity; the Unsleeping Hand both Diligences. A character draws on a seal only
  up to its own level in that craft (its highest craft for the others). Levels 1–10 for now; Essence Salts open
  the rest in V10d2.
- **Guardian Steles** (Elder Bian's The Guardian Stones, Qi Unfurling 6): one per craft, +0.3 tool power a level
  for everyone, floor(150 × 1.22^L) taels and ceil(10 × 1.1^L) ore from the Storehouse.
- **Magistrate's Favours** (Magistrate Qian's The County Tribute, Heart Tempering 2): the Watch (+5% Martial
  Diligence), the Guilds (+3% Craft Diligence) and the Red Seal (a 2.2% chance a settle's craft EXP counts twice),
  each earned once with taels and Storehouse tribute.
- Guardian Stele power now adds to the tool's power inside Finesse (it was added to the base once, not twice).
- Tests: `works_suite`; the valley run learns an art, inscribes a seal with its willow moss and raises a stele with
  three hours of a copper post.

### V10c · Snares, Rites and the Bench
- **Beast Snaring** (Agility; Adventurer Kai's Snares Before Swords, a hemp snare kit): 16 beast trails from the Reed
  Shallows to the Drifting Shoals, each with its critter (jade frog, mist hare, reed ferret, cloud marmot, thunder
  hedgehog, frost stoat, sand fox, star gecko).
  - A snare is set for one of the kit's lengths and runs on the clock, whoever is played: 20 min for 1 critter up to
    28 days for 550. Short snares pay more an hour, long ones more a visit.
  - A snare holds nothing if its Finesse is under the beast's Toughness, and (Finesse / Toughness)^0.25 more above
    it. Kits from iron up hold more snares at once, open longer lengths, and bring a radiant pelt now and then.
  - Critters are pet food.
- **Ancestral Rites** (Spirit; Magistrate Qian's The Ancestors' Regard, a wooden rite tablet): rite charge builds by
  itself for everyone with the Rites, 6 / max(5.7 - 0.2 x tablet speed^1.3 - level/40, 0.57) an hour, up to its
  tablet's cap. Held at one of five ancestral altars (the County Hall, both sect libraries, the Hall of Nine, the
  Star Chandlery), it is all spent on the altar's defence; the wave held calls **Spirit Wisps**.
- **Post Vows:** five boons with curses, learned once for the account with Spirit Wisps, two held per disciple. The
  Short Lamp: +25% craft EXP, posts stop after 10 h. The Quiet Hand: +15% Finesse, -30% EXP. The Burdened Back: +8%
  Craft Diligence, pouches hold 60% less. The Iron Fast: +10% Martial Diligence, provisions go twice as fast. The
  Open Palm: +50% Vigil drops, -20% kills.
- **The Apprentice Bench** (Tinkerer Yu's An Apprentice's Hands): apprentices make components while you are away,
  3600 x speed / progress an hour (36 hemp cord at the start), up to the bench's capacity (the material
  compartment x (2 + 0.1 a point)). They are hemp cord, bronze rivets, kiln bricks, lacquer, whetstones and spirit
  glue.
  - More apprentices at 60 and 150 craft levels in all, and a bench point every five for speed, capacity or smithing
    EXP.
  - Tools from tier 4 and pouch folds from the Satchel up now ask for components.
- The Roll-Call gains Bench and Vows tabs; the Crafts tab shows all six crafts, rite charge and snares out; Tailor Xun
  sews all seven pouch categories.
- Tests: `rules_tests` `station_suite`; `valley_run` sets an apprentice, a snare and the rites at Qi Kindling 3.

### V10b · The Vigil
- **Keep vigil** from the Roll-Call in any room with beasts to hunt: the character hunts the room while you play
  someone else, at IdleOn's kills an hour. That is the lesser of the room's spawn cap (spawns / respawn) and the
  fighter's pace (walking, blows needed, hit chance, techniques slotted), times 40% Martial Diligence and the
  **Sweep** tier (a blow of twice a beast's life or more fells extra: tier floor(log2(hit / HP))).
- Blows both ways come from the S12 damage pipeline itself (seeded samples), so a Vigil agrees with the fight you
  would have.
- **Provisions:** the best healing food in the bag is eaten as blows outpace regeneration. Without food the
  character keeps falling, losing 600 s each time, and fights less of the hours.
- Kills roll the room's loot at expected value into the pouch, pay coins, give a quarter of a hunted kill's realm
  progress, and find **Bestiary Leaves**: one in a thousand per species, account-wide. Tiers at 1, 5, 25 and 100
  leaves give a species' bonus (Martial or Craft Diligence, Finesse, pouch capacity or drop rate).
- The Roll-Call shows a Vigil's kills an hour and Sweep tier. The Crafts tab shows Vigil Info in a hunting room:
  what holds it back, blows landed, damage taken and healed, provisions, and time fighting over twelve hours. The
  Return Ledger lists beasts felled, provisions eaten, realm progress, coins, leaves and loot.
- An old idle Hunt task becomes a Vigil; with Keeping Post, hunting while away is only done by Vigil.
- Tests: `rules_tests` `vigil_suite` (the two caps, Sweep, survivability, a four-hour Vigil settled, leaves and their
  bonus, migration).

### V10a · Posts and crafts
- **Keeping post.** Beside an ore vein, a herb patch, a fishing spot or an insect swarm, the Keep Post button (key O)
  leaves the character there and opens the Roll-Call to choose who to play next. Every character with a post works
  while you play someone else, and while the game is put away.
- **Four crafts**, each with its own level (1-200, IdleOn's EXP curve) per character: Vein Delving (Body), Spirit
  Foraging (Insight, spirit wood on the side), River Angling (Body) and Insect Netting (Agility). Hand harvesting
  trains them too.
- **The rules** (`PostRules`, constants in `posts.json`):
  - Finesse = 12 + (base^1.3 + (attribute + 1)^0.6) x (1 + level/200) x (1 + (attribute/100)^0.35) x (1 + base/100),
    with base = 2 x tool power + 4.
  - Against a node's Toughness T: the Chance bar (Finesse / 10T)^0.4, nothing below 2.5% of the mark; past full, the
    Abundance bar floor(r^0.25) units a success.
  - A swing takes 6 x (1 + (10 - tool speed)/5) s. Craft Diligence is 52% of full work.
  - Worked example: a copper pick, Body 10, level 1: Finesse 81, 64% on copper, about 83 ore and 994 EXP an hour.
- **Nodes:** nine ores, nine herbs, seven fish and eight new insects, each with a Toughness, EXP and a level gate.
  Aged herbs stay a thing of the hand.
- **Tools:** four ladders of nine tiers (picks, sickles, rods, nets), 32 of them new, forged by any smith from each
  zone's ores. The best one carried is used.
- **Insect Netting:** 22 swarms across the valley, Mist Peak, the Expanse and the Drifting Shoals, netted by hand or
  kept as posts. Glowfly, reed cicada, jade scarab, silk moth, thunder mantis, frost cricket, ember locust and starwing
  mote. Little Dou's Glowflies teaches it and gives the reed net.
- **Qiankun pouches:** four compartments per category, 10 each unsewn. Tailor Xun on Market Street sews them deeper
  (25 up to 35,000 a compartment). A full category stops filling, EXP does not, and the Return Ledger says when it
  filled.
- **The Storehouse:** the account's bulk store. The Ledger sends a haul there; items come out into the bag in any
  town.
- **The Return Ledger** on entering a character (hours, Diligence, EXP and levels, the haul, full pouches). **The
  Roll-Call** (menu) lists every character's post, rates, pouch and time to full; it can settle one or all, burn
  Hour Incense (1 to 72 hours, or a Wandering 5 to 500) at a post, and switch.
- An old idle Gather task becomes a post. With Keeping Post unlocked, gathering while away is only done at a post.
- Quests: Keeping Post (Fisher Wen), Little Dou's Glowflies, A Pouch for the Road (Tailor Xun).
- Tests:
  - `rules_tests` `post_suite`: the formulas and worked examples; a post taken, settled, filled and emptied; the
    clock moved back; hand EXP; incense; the Roll-Call and settle all; migration; sewing; the save.
  - `balance_sim` checks the calibration targets.
  - `valley_run` plays the lesson with a second disciple, then nets the glowflies.

## 1.2 — The Lantern Star Field (Act III)

Built in phases (docs/act3_design.md): zone tier 3, levels 82-99, ceiling Sphere Lord 3, Starsea Endurance 20 -> 90.

### Phases D and E · art
- **The brush and the bell in hand**: weapon sheets for both families in every pose the avatar has (idle, walk, jump,
  meditate, attack, the three swings, thrusts and punches, the bow and punch combos), baked by
  `tools/art/bake_weapons.py` from the dagger's grips, each in two layers, in front of the body and behind it
  (`data/parts.json`: `weapon/brush`, `weapon/bell`).
- **Icons** (20): cinder ash, the pyre ember, the drone shell, Kharn's glaive shard, the Copperjaw box, eel essence,
  the void carapace, the Leviathan's scale and the Lantern Heart's flame; the four brush and bell weapons; the five
  brush and bell manuals; the `brush` and `bell` glyphs on the attack button.
- `data_validation` is clean again: every item, technique and weapon has its icon and its appearance.

### Phase E · The Nebula Deep and the Lantern Heart (chapter 22)
- **The Nebula Deep** (94-99, Endurance 80-84), past the Drone Hive: Nebula Verge, Eel Currents, Crab Grottoes, and the
  Leviathan's Maw.
- **Monsters:**
  - Nebula Eel (94-99): a space bite that dashes in, and a current coil that drags you close.
  - Void Crab (94-99, shelled: 60% more defence): a blinking claw that closes 320 at once. It can be tamed as a
    star-tier beast.
- **The Nebula Leviathan** (field boss, 99, back every 45 minutes): Presence 5 and a Sphere of Space. It swallows
  the current (a pull from both sides), breathes the void (460 ahead) and crashes down (a stun). Eels answer its
  call at 60%, and it rages at 30%.
- **The Lantern Heart**, a secret realm (97-99, Endurance 90), reached by the stair above Lanternfall's market once
  Lu's notes are found: Wick Gate, Hall of Burning Stars, and the Flame Heart.
  - **The Lantern Heart's flame**, the first lantern's, is a Heavenly Flame like the others: absorbed, it burns
    under every furnace.
- **The Law pills' recipes** (Law Condensing, Law Touching), sold by Stargazer Ming to a Sphere Lord 3, for the step
  past the Field's ceiling. They are made from star lotus and the Deep's drops: eel essence, void carapace and the
  Leviathan's scales.
- **Chapter 22:**
  - Lu's Lantern: the star notes in the Crab Grottoes, the stair, the flame.
  - The Leviathan's Maw (optional).
  - Greyfall: Sphere Lord 3, and a 90-second stand at the Greyfall Breach. When the Tide closes over the Breach,
    Shen Lian is on the far side, and the Frontier waits past the Field.
  - Four codex entries; the flag `act3_complete`.
- Monster stats take a `defence_mult` for shelled foes.
- Tests:
  - `rules_tests` `lantern_heart_suite`: the crab's shell, the Leviathan's Presence, Sphere and phases, the tameable
    crab, the two Law recipes, the flame absorbed, and the Greyfall stand's outcome.
  - `valley_run` `ls6` plays chapter 22: the notes, the flame absorbed, the Leviathan brought down, Sphere Lord 3
    and the Law recipes, the stand held. Act III now plays from the Lantern Run to Greyfall.

### Phase D · Ash and Tide (chapter 21)
- **The brush and the bell**, two new weapon families (docs/act3_design.md, Phase D in detail).
  - The brush (the new Brush Dao): quick Qi strikes. Every technique used with it writes a talisman on each foe it
    strikes, by the technique's element (Fire burns, Water slows, Wood roots, Metal sunders, Earth leaves the foe
    open, Thunder shocks, none seals its Qi); one talisman on a foe at a time.
  - The bell (the Music Dao): its strikes ring out on both sides for soul damage.
  - Five manuals: Splashed Ink and Cursive Storm for the brush; Stilling Peal (a stun ring), Qi Seal Toll and
    Warden's Call (a group heal and defence) for the bell.
  - Four weapons at the Tidebreak Bastion's armoury, the Lantern Star Field's first: the Ink-Warden's Brush and the
    Warden's Hand-bell (Sage grade), the Starwrit Brush and the Tidebreak Bell (Will grade).
- **The Copperjaw Beetle swarm.** A box of beetles from Tinker Mei.
  - Fed ore, the swarm grows 8% an hour while its food lasts, even while you are away, up to 5,000. Unfed, it
    dwindles.
  - Opened in a fight, it chews every foe within 220 for 8 s at 0.12 × ln(1 + population) of your Qi attack a
    second. Wood foes take half.
  - A Queen can rise (1% a fed hour): after that the swarm grows faster and bites harder.
  - The Pets page gains a Swarm tab to feed it and see it.
- **The Hollow Tide battle** (the Tidebreak Bastion's great bell), 150 s.
  - Every foe near the great lantern dims it; standing by it without striking relights it. If it goes out, the Tide
    breaks through.
  - The battle can be fought again once a day.
- **Ground fire**: Ashborn blows leave the ground burning where they land; standing in it burns.
- **Titles**: Star Warden (+10 Starsea Endurance, 8% Hollow Ward) and Tidebreaker (+3% max HP).
- **Rooms** (9):
  - The Ashen Reach, by the Wardens' second skiff: Cinder Fields, Ashborn Palisade, War Camp and Kharn's Pyre.
  - The Tidebreak Front, by the third: the Tidebreak Bastion (safe), Greyfall Breach, Hollow Wake and Drone Hive.
  - The Tide battle's own instance.
- **Monsters:**
  - Ashborn Raider (88-96).
  - Ashborn Pyre-Keeper (elite, rings of fire, Presence 2).
  - Hollow Drone (88-99, a flying pack that spreads the Hollowing).
  - **General Kharn** (92): Presence 4 and a Sphere of Cinders; a leaping cleave and pyre rings that leave fire;
    a Pyre-Keeper at 60%, rage at 30%. At a fifth of his health he kneels, and you decide whether he lives.
- **Chapter 21:**
  - Main quests: Cinder Fields, Kharn's Pyre, The Tide Breaks, Star Warden. Star Warden asks for Sphere Lord 2 and
    the hatched star-wyrm.
  - Side: Brush and Bell. The Copperjaw swarm's quest comes with its unlock.
  - Five NPCs and six codex entries.
- **New quest objectives**: `judge_foe` (a kneeling foe spared or finished) and `hatch_egg`.
- **Fix: Dao caps carry forward.**
  - A zone now keeps at least the cap the zone before it allowed.
  - Before this, Beast Taming fell back to its valley cap of 2 in the Lantern Star Field, and the rare Daos to 0.
- Tests:
  - `rules_tests` `ash_tide_suite`:
    - the brush's talismans (one at a time; Splashed Ink seals) and the bell ringing out both ways;
    - the swarm's growth, shrinking, Queen, bite and cap, then feeding, time away and release (the box stays);
    - ground fire, and Kharn spared counting for his quest;
    - the lantern dimming, relit and going out.
  - `valley_run` `ls5` plays chapter 21, from the Cinder Fields to Star Warden:
    - Kharn spared;
    - the swarm fed and the brush bought;
    - the Tide battle won with the lantern lit;
    - the star-wyrm hatched.

### Phase C · The Citadel, the Sphere and the Orbit Ruins (chapter 20)
- **The Sphere (Sphere Lord 1).** A small world of your own, raised with the Sphere button (H) and drawn from your
  strongest combat Dao.
  - It reaches 160 + 20 a Dao tier (40 more at tier 6) and costs 0.4% of max Qi a second.
  - Its power is (5 + Level) × (1 + 8% a tier, +10% at tier 6).
  - What it does follows its element:
    - Water slows by a fifth, and freezes the surface of water underfoot.
    - Fire burns, hotter on grass. Wood heals you, more on grass.
    - Earth leaves foes open to harm and roots them on stone.
    - Metal cuts. A Sword Dao Sphere with a jian in hand is the Sword Domain, which cuts harder.
    - Wind quickens you. Space pierces defences. Soul lowers the foes' Will. Thunder shocks every other pulse.
  - A technique whose element the room or the Sphere feeds (its own, or the one it generates: Wood feeds Fire)
    strikes 10% harder.
  - Where two Spheres meet, the weaker breaks. A foe's broken Sphere staggers it. Yours tears a meridian and cannot
    be raised again for 30 s.
  - A Sphere Lord's pets carry a small Sphere of their own and strike 10% harder.
- **Dao tier 6, Original Application,** for every weapon and element Dao (the Lantern Star Field allows it).
- **The Space Dao, six tiers** (penetration, speed, evasion, Qi attack, crit damage), opened by the Orbit Hermit.
- **Gravity switches.**
  - A jade switch lightens the air over its part of a room to 45% (a longer, higher jump); press it again to restore
    it.
  - Volumes tied to a switch start off.
  - The Inverted Hall's high gallery (400) is out of reach of any jump (a double jump tops out near 300) until its
    switch is down.
- **The Confucian path** (Will Manifest 2, an upright heart of alignment 20 or more, never beside the Blood path).
  - Righteous Qi strikes Hollow and demonic foes 25% harder.
  - Three glyphs whose strength follows Insight rather than the arm: the Upright Glyph (a Qi strike ahead),
    Benevolent Script (a group heal) and Rite-Seal Script (roots and soul-strikes foes on both sides).
- **Rooms** (8):
  - The Star Warden Citadel, by the Wardens' skiff from the Arrival Quay: the Citadel Gate (with a teleport stone),
    the Wardens' Hall, the Observatory and the Presence Court.
  - The Orbit Ruins, east past the Warden line: the Tumbling Stair (Endurance 50), the Orbit Garden, the Golem Foundry
    and the Inverted Hall (56, no flight).
- **Monsters:**
  - Gravity Golem (88-93): a gravity well that pulls you in, and an orbit slam. It cannot be knocked back.
  - Orbit Moth (88-93): a ranged flyer, tameable as a star-tier pet.
  - Shen Lian, now a Warden aspirant (91), spars with a Sword Domain Sphere of his own.
- **Chapter 20, The Star Wardens:** The Citadel, The Aspirant, The Observatory, Sphere Lord and The Orbit Ruins. Two
  quests come with unlocks: A Sphere of One's Own (the Sphere's lesson) and The Written Word (the Confucian path).
  Six NPCs and five codex entries.
- **Shops:**
  - Lanternwright Han sells the two later glyphs.
  - Stargazer Ming sells another Sphere Comprehension Stone after the Observatory. A failed Sphere Lord breakthrough
    consumes the stone, and without this shop a player could be stuck.
- **Fixes:**
  - Reaching a Presence level now refreshes quest offers. Before, the Observatory's offer waited for a room change.
  - Warden Xiao's harbour talk now waits until The Citadel. Before, it hid the chapter 20 offer.
- Tests:
  - `rules_tests` `sphere_suite`: the radius, power and element rules, feeding, the six Space tiers and tier 6.
    - A switch lightens only its own half of the hall, and the gallery is out of jump reach without it.
    - Raising the Sphere: its Qi cost, a foe slowed inside and not outside, a weaker Sphere broken, yours broken by a
      stronger one and the wait after.
    - The Sword Domain needs a jian.
    - The Confucian gates: locked, alignment, the Blood path.
  - `data_validation`: a switch-tied volume must name a gravity switch in its room.
  - `valley_run` `ls4` plays chapter 20, from the valley stone back to Lanternfall through The Written Word:
    - a 36-bolt Sphere Lord tribulation;
    - a jade switch pressed;
    - three golems broken.

### Phase B · Blackmast, Wyrmnest and the Hollow Tide (chapters 18-19)
- **The Hollow Tide (S28):** the Hollowing is held under half in the valley and the Expanse. In the Lantern Star Field it
  fills.
  - At 50% the burden begins: techniques cost 25% more and Composure drains instead of recovering.
  - At 100% the Tide takes the body for 3 s (no moving, striking or casting). The allies beside you turn on you for
    10 s. The meter falls back to 80%, and surviving it awakens Hollow-Touched.
  - Cleansing: Lantern Incense (-15, the apothecary), the Tide Cleansing Pill (-40; Star Lotus, wyrm ash, jelly silk),
    and resting under a lit lantern (the harbour and the hulks), which draws it out four times as fast.
- **Rooms** (8):
  - Blackmast Haven: Docks (Endurance 30), Gunners' Battery (33, three cannons to spike, gun decks, a hidden door to
    the Smugglers' Cove), the Flagship Deck (36, Admiral Voss).
  - The Wyrmnest Isles, by Old Bo's skiff from the Moored Hulks: Nest Cliffs (40, Tamer Qiu), Eggshell Terraces (44,
    Hollow puddles), Guardian's Crown (48) and the Hatching Cave.
- **Monsters:**
  - Pirate Gunner (85-90): powder bombs and a slow bombard.
  - Nest Guardian (85-93): club tail and crystal stomp, with a small Presence.
  - Hollowed Wyrmling (88-96): grey flame that adds Hollowing.
  - Admiral Voss (90): Presence 4, the first clash. He calls gunners at 60% and rages at 30%.
  - The Starsea pirates now leave the shards of the zone they die in.
- **Star-tier beasts (Will Manifest 2):** the Comet Sparrow can be tamed once Tamer Qiu has shown you how.
- **The Hatchling Wyrm:** the first Primordial line, from the last star-wyrm egg. It warms like any egg but hatches
  only for a Sphere Lord 2, and grows past Sovereign.
- **Sect Master (Will Manifest 3):** the succession quest. Your valley mentor names you Sect Master, a rank above
  Elder: 300 contribution a day and a fifth off in your sect's Mission Hall, plus the Sect Master title.
- **Chapter 18, Blackmast:** The Purser's Ledger, Gunners' Battery, The Admiral. Gu flees into the Hollow Wake with a
  grey hand.
- **Chapter 19, Wyrmnest:** Star-Tier Beasts, A Hollowed Brood, The Last Egg, The Master's Seat. Three new NPCs, six
  codex entries, two titles (Breaker of the Blackmast, Sect Master).
- Metal, Star and Space beast cores (and a parent-element fallback), so every beast of the Field drops a core.
- Icons for the phase's items: star powder, the guardian scale, wyrm ash, the Admiral's seal, the wyrm egg, Lantern
  Incense and the Tide Cleansing Pill.
- Tests:
  - `rules_tests` `hollow_tide_suite`: the valley cap, the burden, the seizure (allies turned, back to 80,
    Hollow-Touched), cleansing and the lantern.
  - `valley_run` `ls2` and `ls3` play chapters 18 and 19, from the docks to the Master's Seat.

### Phase A · Lanternfall and the Presence (chapter 17)
- **The Lantern Run** is charted and open. From the Starsea Launch a vessel crosses the open Starsea (90 s, faster
  in a storm sloop) past Comet Sparrows and Star Jellyfish to **Lanternfall Harbor**, and sails home from its pier.
- **Zone 3, the Lantern Star Field:**
  - Ceiling Sphere Lord 3: the Expanse cannot hold a Will Manifest, the Field can.
  - Laws: Fire, Metal, Space and Star; Qi density 1.5-2.5.
  - Money: loot pays in **Sage Crystals** and savings are kept in **Star Jade**. The harbour exchange trades
    10 Spirit Stones for a crystal and 100 crystals for a Star Jade, less a fifth each way. Shops price in each
    currency's tael value.
  - Ten regions on the map; the ones later phases build show as planned.
- **Starsea Endurance:** four jades (Tide, Comet, Wick, Void), fed with star shards, fifteen levels each at 1.5 a
  level (0 to 90). The Warden's quest opens them.
- **Rooms** (9):
  - Lanternfall Harbor: Arrival Quay (the pier and the Warden), Harbor Market (exchange, teleport stone, shops),
    Star Chandlery (insight), Tidelight Inn (rest).
  - The Drifting Shoals: Jellyfish Shallows (Endurance 20), Moored Hulks (rest, garden beds), Sparrow Reefs (24),
    Driftglass Bank (28, driftglass and Star Lotus, an insight lens).
  - The Lantern Run crossing (instanced).
- **Monsters:** Star Jellyfish (82-87, a confusing sting and spark trails) and Comet Sparrow (82-87, burning dives).
- **Presence (S28, Will Manifest 1)**, a new Field authority:
  - Hold it with the Presence button (key G). It costs 0.25% of max Soul a second and trains by use:
    experience while it presses something, double in a clash, more for a kill made under it. Levels 1-10;
    level 5 is what Sphere Lord asks.
  - Pressure = (5 + Level) x (1 + 6% a Presence level) + the pressure stat. A foe's Will = 5 + its Level, x1.15
    for elites and x1.3 for bosses.
  - A weaker foe in reach loses output and speed by the S12 Pressure rule, min(50%, 25% x (Pressure / Will - 1)).
  - A foe with a Presence of its own meets yours at a visible boundary. Whoever presses harder than the other
    side's Will (or held Presence) presses them by the same rule; the weaker side is pressed, never both. Without
    your Presence, your Will alone stands against theirs.
  - It shows as a pale ring on the ground, a gold or red wall where two meet, and a line on the Cultivation page.
    The requirement `presence_level_at_least` now works.
- **Chapter 17, Lanternfall:** The Lantern Run, Crystal and Jade, Salt of the Stars, Will Manifest, A Presence of
  One's Own. Nine new NPCs (the harbourmaster, Star Warden Xiao Ning, the exchange clerk, a peddler, an apothecary,
  a smith, Chandler Shu, the innkeeper, Old Bo of the hulks), four codex entries, two shops.
- Star Lotus (herb, Master) and driftglass (ore, Master); star shards, jelly silk and comet plumes; lantern jars and
  chests. The Verdant Dew Vial ages herbs to 10,000 years in the Field as in the Expanse.
- New art for the whole act, drawn ahead of the later phases:
  - eleven creature sheets (Star Jellyfish, Comet Sparrow, Nest Guardian, Hollowed Wyrmling, Hatchling Wyrm,
    Gravity Golem, Orbit Moth, Hollow Drone, Nebula Eel, Void Crab, Nebula Leviathan);
  - ten backdrops, one per region (Lanternfall Harbor to the Lantern Heart), four layers each;
  - 32 props (lantern-star cages and posts, driftglass, hulks, cannons, wyrm nests, orbit stones, Ashborn pyres and banners);
  - five music tracks (`lantern_harbor`, `star_field`, `hollow_tide`, `ashen_war`, `lantern_heart`);
  - icons for the zone's items, the Endurance jades, metal, star and space cores, and the Presence button.
- Tests:
  - `rules_tests` `field_suite`: the Pressure rule, foe Will and Pressure, clashes (only the weaker side is
    pressed), levels, the pressed foe, Soul upkeep, a boss's stronger Presence, letting go, the Sphere Lord
    requirement, running out of Soul.
  - `starsea_suite` sails the Lantern Run to Lanternfall.
  - `valley_run` `ls1` plays chapter 17 end to end, from the Starsea Launch to a level-2 Presence.

## 1.1 — The Azure Expanse (Act II)

Built in phases (docs/act2_design.md). All five phases (chapters 11 to 16) are playable end to end, from
the Ascension Gate to the Starsea Launch.

### V9f3 · The rest of the room verticality catalogue (Part 8, S43)
About forty valley rooms that V2d left partial are now built by hand to their catalogue rows and marked
`authored`, so the movement and verticality passes leave them as built. Every portal, quest object, event and spawn
the story and the tests use still works. One module per group: `tools/data/catalogue_rows_towns.py`, `_fields.py`
and `_dungeons.py`. The room-by-room notes are in `docs/v9f3_towns.md`, `docs/v9f3_fields.md` and
`docs/v9f3_dungeons.md`.
- **Towns and sects:**
  - Willow Path's stumps and lifting stones stand as blocks, and Old Pan trades from his cart deck.
  - Market Street has galleries at 176, rooftops at 264 and the bell tower at 300; the rooftop thief's route follows them.
  - The Fairground has stone stages and tent tops, with festival lanterns only the drum's bounce reaches.
  - Jade Sect: terraced herb beds at 40/80/120, a mezzanine in the Alchemy Hall, weapon racks you can stand on,
    Elder Hu's peak ledges at 100/200/300, and doors to the Retreat Rooms and cave abodes on the high tiers.
  - Cloud Sect: the Cliff Stair's landing, rope and the Library's upper gate, and the Array Court's dais.
  - Hidden Vale's back mountain gets ledges.
- **Fields:**
  - Quarry: a falling-rock pit and a rubble heap with a cracked wall that opens for Body 20.
  - Marsh: stilt decks around the Marsh Edge; rafts, a moored chest raft and a lily-pad climb on the Grey Pools.
  - Greyreed Hamlet: roofs chained at 88 to 176, with two grey lanterns to cleanse for "Grey Roofs". The hamlet
    door now opens at the quest's own realm, which fixes a quest that could never be started.
  - Water: canopy decks and spirit-egg nests in the Thicket Heart; stepping rocks and deep water at the Falls Pool;
    docks, a ferry and a sampan roof at the Bend Shore; a current and stepping stones in the Rapids Terraces.
  - Heights: landings and shortcuts on the Pilgrim Stairs, pillars on the Cleansing Summit, crags with updraft
    columns on the Cliff Faces, and cloud ledges up to 900 on the Sky Ledges.
- **Dungeons and story rooms:**
  - Mudwater Hideout: palisades and watchtowers in the Stockade, spike pits under crumbling planks in the Tunnels,
    stalagmites in the Loot Cave.
  - Drowned Shrine:
    - rafts on a current at the Flooded Gate;
    - swinging and circling lantern platforms up to a loft in the Hall of Lanterns;
    - a descent from a 300 rim to a flooded bottom in the Scripture Well;
    - the Abbot's rising water.
  - Mist Peak and beyond:
    - ruined roofs, crumbling floors and a hidden stair at the Forgotten Monastery;
    - cloud rings at the Ascension Gate;
    - crumbling icicle platforms at the Frozen Shrine;
    - a mirrored arena for the Trial of Reflections;
    - catwalks and rafters in Gu's Warehouse;
    - a battlement and towers for the siege.
- Known limits (engine work for later):
  - Portals have no altitude.
  - Objects placed mid-roof draw behind the roof face.
  - Bosses do not use tiers.
  - Sect-level buildings cannot grow roofs yet.

### V9f2 · Ice, and mounts in a vertical world (S43 rules 5 and 12, v1.1)
- **Ice (the v1.1 traction rule):** a new `ice` volume.
  - On ice, your speed only eases toward what you ask for, at 380 to 420 a second. You slide on when you let go and
    slide to a stop. In the air, control stays total.
  - Glazed ground in the Frozen Shrine (two sheets), on the Rimefrost Summit and on the Frostpine Climb, drawn as a
    pale blue glaze with slow glints.
- **Mount jumps:** a ground mount jumps with its species' impulse. The Cloud Stag's 600 reaches about 156, where a
  jump on foot reaches 122. A flying mount's rider jumps as on foot, because the animal flies instead.
- **No Wall-Step on a ground mount.**
- **Climbing:** a ladder or rope puts the rider down off any mount; it waits below. You are back in the saddle when
  you step off at the top or land. The log says so calmly, not in red.
- Tests: `rules_tests` `ice_mount_suite`:
  - slow speed gain on ice, sliding on and stopping, a dead stop off the ice, air control over it;
  - the 600 jump's height;
  - mount jumps by kind;
  - dismounting for a ladder and remounting at the top.

### V9f1 · The rooftop thief and the Cloud Steps (S43 rule 15)
- **"Catch the thief"**, daily on Market Street (from Qi Kindling 1) and Gate Street (from Qi Kindling 3).
  - Quick-Fingered Hou loiters in the street. Speak to him (the action reads Chase!) and he bolts over the roofs.
  - Market Street: store, awning, tea house, awning, warehouse, then the bell tower. Gate Street: the three-roof
    chain.
  - He pauses at each roof to jeer. A timer runs at the top of the screen.
  - Reach him on his roof, at his height, to catch him. From the street below you cannot lay a hand on him.
  - Market Street pays 150 taels and a Spirit Stone shard; Gate Street pays 120 taels and sect contribution.
  - If he gets over the far wall, nothing is paid. Leaving the street lets him get away too.
  - One chase a street a day, caught or not.
  - Catching ten earns the Thief-Catcher title (+2% coin find).
- **The Cloud Steps**, the Cloud Sect's timed climb:
  - The Cliff Stair now reaches its catalogue's 300 ledge. Touch the flag at the foot (from Bone Forging 3) and reach
    the bell at the top before the incense burns down (60 s).
  - Each week has a board of six sect disciples with fixed, seeded times.
  - A place in the top three pays contribution and taels once a week.
  - Medal pars: bronze 18 s, silver 13 s, gold 10 s. Each medal's reward is paid the first time you beat its par.
    Gold also earns the Cloud Stepper title (+1% move speed).
- New World events `chase_started`, `thief_caught`, `thief_escaped`, `route_started` and `route_finished`, with HUD
  toasts.
- Debug tools: `--interact=<object>` presses a room object in a preview (a thief, a route stone).
- Tests: `rules_tests` `rooftop_routes_suite`:
  - the route clock;
  - every waypoint standing on a roof;
  - the grace moment, the height rule, the catch and its pay, one chase a day, the escape;
  - the Cliff Stair's 300 ledge;
  - the week's board, medals once, a timed finish, the burned-out incense.

### V9e3 · The Cloud Herb Terraces and the ten-thousand-year tier (S45, Part 8, v1.1)
- **Cloud Herb Terraces:** a new room east of the Cloud Sect's Array Court, with three terraces cut into the cliff.
  Willow moss and ember pepper grow at the foot, ginseng on the middle terrace and mist lotus on the high one.
- **The weekly Herb Terraces Trial** is now held on each sect's own terraces, as Part 8 says ("Jade or Cloud Herb
  Terraces"):
  - Cloud Sect disciples gather on the Cloud terraces and Jade Sect disciples on the Jade terraces; a disciple of
    neither sect uses the Jade terraces.
  - Each terraces is ranked against the other sect's gatherers (a fixed, seeded draw per trial). The Jade draw is
    unchanged.
  - Herbs gathered on the other sect's terraces do not count.
  - The Calendar page, the event toast and the ranking name your own terraces. The rewards are unchanged
    (Foundation Guard Pill recipes for the top three).
- **Ten-thousand-year ginseng** (Riverreed Ginseng 10,000 yr, Mystic grade, hot, Principal or Minister):
  - The herb ages now run 10, 100, 1,000 and 10,000 years.
  - It ripens on two high Expanse ledges, a Master's pick, every fifth in-game day:
    - Snow Ape Ledges at dawn, guarded by a Snow Ape elite;
    - Harpy Roosts at night, guarded by a Canyon Harpy elite.
  - None grows in the valley.
  - Its icon wears the Expanse's pale jade over the thousand-year gold.
- **The Verdant Dew Vial's v1.1 tier:**
  - A bed in the valley still holds a herb at 1,000 years.
  - A bed in the Azure Expanse ages it to 10,000. The Herders' Camp on the Thunderhorn Plains lets two High-grade
    plots inside its fence.
  - A herb already as old as it grows says so.
- **Page headings** step their size down to fit instead of being cut off (the World map's "Cloud Sect Monastery").
- Tests: `rules_tests` `expanse_herbs_suite`:
  - the room and its link;
  - each sect's trial room;
  - the rivals by sect;
  - herbs counting only on your own terraces;
  - the dew cap by zone and the ten-thousand-year age;
  - the two guarded Expanse nodes, and none in the valley.

### V9e2 · The five-screen furnace (S15, S44)
- **Alchemy is now played in five screens** (the forge keeps its three strikes). A step tracker shows where you are.
  1. **Ingredients:** the recipe, the batch, each herb's role and nature, and stand-ins. With Spirit Sense, the
     sealed (unappraised) roots the batch would use are counted. At 4% Crafting perception, dyed fakes among them
     are named.
  2. **Furnace:** the fire (as before) and a new **array**, Still Water or Rising Flame.
     - The array that answers the Principal herb's nature widens every heat band by 15%: Still Water under a hot
       herb, Rising Flame under a cold one. The other array narrows the bands by 15%.
     - The screen shows the band width you will get.
  3. **Extraction** (full width), one herb at a time in the recipe's order:
     - Hold **Fan the flame** to raise the heat, and keep it inside a gold band that sways. Hot herbs sit their band
       high on the gauge; cold herbs sit it low.
     - Tap the dark impurities as they rise: they are a quarter of the score. Crafting perception shows more of them
       plainly; the rest are faint.
     - Heat in the band less than 35% of the time **scorches the herb**. That herb's share is lost (early mistakes
       waste ingredients). Put in another and try again, or put out the fire.
  4. **Fusion:** tap the essences into the core in the recipe's order (Principal first), then **turn the array**
     as a needle crosses each of 2–3 marks.
  5. **Condensation:** a ring closes on the pill; press **Condense!** as it meets the outline.
     - Early makes a weaker pill.
     - Late by more than 0.2 s **cracks the pill** and the whole batch is lost (late mistakes ruin the batch).
  6. **Pill tribulation:** unchanged, now drawn full width.
- **Liquids** skip Condensation: they are done at Fusion.
- **Herbs that fight each other** now blow the furnace at Fusion, as they merge.
- **Putting out the fire** mid-refine loses the herbs already in it; the rest stay in the bag. A refine left burning
  when the page closes is picked up where it was.
- **Intents** (S15): `start_refine` draws the plan (band sway, impurities, the marks) on its own RNG stream, so the
  quality roll's stream is untouched. `refine_input {step, value}` sends what the hand did, and the authority clamps
  it to what could happen and scores it. `cancel_refine` puts out the fire. The quality roll uses the three screens'
  scores, averaged; Extraction's score is the mean of its herbs.
- **Crafting perception** now also grows with Spirit (0.1% a point), as S15 asks.
- **Alchemist Guild candles** are longer, allowing about half a minute a refine: Adept five minutes, Expert seven,
  Master ten.
- The numbers live in `forge_upkeep.json` `furnace_game`.
- Previews: `--open-page=alchemy:` followed by `__furnace`, `__extraction`, `__scorched`, `__fusion`,
  `__fusion_turn` or `__condensation`.
- Tests:
  - `rules_tests` `furnace_game_suite`:
    - the plan, the natures and the array;
    - steps out of order;
    - a scorched herb;
    - the clamped report;
    - out-of-order Fusion;
    - a cracked pill;
    - an early (weak) pill;
    - putting out the fire;
    - a liquid;
    - Spirit Sense on sealed herbs;
    - the same seed and the same hand making the same pills;
    - the crafts page played frame by frame by a steady hand.
  - `valley_run` refines every pill through the five screens.

### V9e1 · The Forge and Formation guilds, and the Alchemist Master (S44, S49)
- **Three profession guilds** share one Guild tab in Crafts, with a button for each guild you have opened.
  - Each has three ranks, and each rank is an exam against the candle.
  - Passing gives a badge title (a small crafting bonus), opens more of the guild shop, and raises what the
    commission board pays.
  - Only one candle burns at a time, and the auto-refine queue never counts toward an exam.
- **Alchemist Guild** (Guildmaster Tang): Adept and Expert as before. New **Master** exam: three Superior Storm
  Blood Pills in eight minutes.
  - The reward is the Sage Condensing Pill recipe; the shop adds Soulbell Flower and Frost Lotus.
  - Its badges are now named Alchemist Adept and Alchemist Expert (same ids).
- **Forge Guild** (v1.0; Smith Bao, Artisan Row) opens at Qi Unfurling 3 once you forge. Its exams ask for weapons
  of any family at a grade or better:
  - two Earth-grade at Fine in five minutes (Adept);
  - two Heaven-grade at Superior in seven (Expert; ten Refining Essence);
  - two Spirit-grade at Superior in ten (Master; a Weapon Soul Crystal).

  Its counter sells ore by rank, and its board orders forged pieces.
- **Formation Guild** (v1.1; the new Array Master Ren, Artisan Row) opens at Heart Tempering 5 once you carry array
  plates. Plates are etched, not rolled, so its exams ask only for speed:
  - four Array Plates in three minutes (Adept);
  - three Killing Array Plates in four (Expert);
  - five Binding Array Plates in five (Master).

  Its counter sells plates and stones.
- **Master exams** are sat at Cloudgate Port and need the Sage realm. Smith Hong and Apothecary Wu open the Guild tab
  there; elsewhere the Start button says where to go.
- **Commission boards:** each guild keeps its own, with three orders a day from what you can make, each board
  capped at a fifth of the day's income target. Old saves keep the Alchemist Guild's board.
- The Guild Board on the Artisan Row covers all three guilds. A guild master opens the tab on their own guild.
- The Max Test character holds every guild at Master.
- Tests:
  - `rules_tests`:
    - the Master exam's realm and hall;
    - auto-refines not counting;
    - Forge exams by grade and slot;
    - a forge commission on its own board and cap;
    - the Formation Adept exam.
  - `data_validation` checks every guild's hall, master, shop, gate, ranks, titles and rewards.

### Old Snapper and crowding
- **Old Snapper** (the first elite, *Crab Trouble*) was tuned for a perfect player. A Mortal with bare fists has
  83 HP and no defence. Against them it had 235 HP and a 20-point claw, and two Reedtail Rats spawned beside
  it. A player who did not step out of every slam died in about 7 s with the Snapper at three quarters health.
  - It now has about 135 HP and a 9-point claw (`hp_mult` 0.24, `attack_mult` 0.33).
  - A player who arrives hurt from the crabs, never rests and never dodges wins in about 18 s. Reading the tell
    makes it easy.
- **Reed Shallows.** The rats keep to the west and middle of the shallows, away from the Snapper's bank, and
  come back after 20 s instead of 8.
- **Crowd cap on sight aggro.** An ordinary monster that sees the player stays put, and joins only when struck,
  in two cases (`combat.sight_aggro_cap`):
  - an elite or boss is already fighting the player;
  - two ordinary foes already are.

  Elites, bosses and summoned monsters (a boss's adds, an event's waves) always come. Monsters notice the player
  within 100 px of depth (`combat.sight_depth`, was 140), so foes in other lanes stay out of it.
- Tests:
  - `prologue_run` beats Old Snapper as a new player would, without resting or reading the tell (it fails with the
    old numbers);
  - `rules_tests` `aggro_cap_suite` covers the cap, being struck, elites and summoned adds.
- Both APKs are version 1.0.3 (code 103).

### Two Android builds; no Credits button
- **Max Test APK.** A second Android preset, *Android Max Test* (custom feature `max_test`, package
  `com.jaderiver.cleanengine.maxtest`), installs beside the normal game.
  - On first launch it makes **Max Tester** (`AccountAuthority.create_max_character`): the Prologue behind them, at
    the highest realm this build's zones allow (Sage Sovereign 3, Level 79).
  - Every system is unlocked. Every method, technique (top mastery), Inner Art (worn), movement art, recipe, Dao
    tier and craft rank is theirs.
  - Gear: the best piece for every slot and the best furnace at Perfect +10, one best weapon of each family, every
    flight vessel and a Beast Bag. Ten of every pill, talisman and throwable wait in storage.
  - Every animal at the highest stage the realm reaches, a mount, the companions, Elder of the Jade Sect, and a
    founded sect at level 20 with every building at 10.
  - Every teleport stone and room is known, with 10,000,000 silver, 1,000,000 spirit stones and shards for fees.
  - The build opens every way (`WorldAuthority.debug_open_ways`: portals, hidden ways and climbs, except rooms not
    built yet).
  - Debug tools (`Unlocks.debug_tools()`) now run in debug builds and in this APK; a plain release build still has
    none. `--max-character` does the same in the editor.
- **Credits removed.** The Credits buttons on the title screen and in Settings > Data, and the Credits page, are
  gone. The title's Settings button spans the row. Attribution still ships inside the game (`data/LPC-CREDITS.txt`
  and the font licences) and in the README.
- **HUD money.** The silver and spirit stone pill widens for large balances, and spirit stones show thousands
  separators. Before, 10,000,000 silver ran into the stones.
- Tests: `rules_tests` `max_character_suite` checks the Max Test character:
  - the top realm;
  - every unlock;
  - every technique and movement art;
  - Perfect +10 gear;
  - a bag with room;
  - every stone and room;
  - animals, mount and companions;
  - both sects and the start room;
  - with ways open, every built room reachable.
- **Numbers on Android.** The Android preset left `art/fonts/PixelifySans.ttf` out of the export (a filter from
  before Pixelify was the number font). In every APK up to 1.0.1, numbers over the world failed to draw, and so did
  what came after them in the same draw: HP and Qi values, bag counts, damage numbers, cooldowns. The font now ships.
  `contract_tests` checks that no export preset leaves out a file the scripts load.
- Both APKs are version 1.0.2 (code 102).

### Readability pass and the Fisher's Hut
- **Heavier, clearer type.** Every word in the game was drawn in Cormorant Garamond **Light**: the font's weight was
  set with a plain `"wght"` key, which Godot ignores, so it stayed at its thinnest default. Weights now use OpenType
  tags and take effect.
- **Source Serif 4 for text.** Labels, names, paragraphs, buttons and world labels are now set in Source Serif 4
  (semi-bold for text, bold for world labels and small headings, small optical size). It has a taller x-height and
  twice the stroke weight at the same widths the layouts were drawn for. Headings of 22 px and up stay in
  Cormorant Garamond, now truly bold. Numbers keep Pixelify Sans.
- **Minimum size.** No word or figure is drawn below 14 px (before the text size setting).
- **Settings > Accessibility > Text size now works.** Small, Normal and Large scale every word, and paragraphs and
  dialogue follow with their line height. It was saved before but never applied.
- **World labels are larger and sit on plates.**
  - NPC nameplates, enemy and ally names, loot names, NPC barks and the context verb are all larger.
  - Door and gate names show all the time, not only when you stand at them. They sit on a plate with a bobbing
    arrow and brighten when you are near.
  - Names at a room's edge move inward instead of hanging half off-screen.
- **HUD.**
  - The quest tracker sits on a soft ink panel, so it reads over sky and foliage. Its lines are a size larger.
  - The minimap title, bar values, bag item counts, the Ride/Walk and Auto labels, draught counts and the loadout
    letter are larger.
  - Toasts are larger.
- **Interior doors are drawn.** An exit on an interior's back wall showed only a faint arrow. It now shows the
  carved double door, which swings open as you come to it, with a pool of light at its foot. This covers 19 exits:
  the Fisher's Hut, Old Ma's store, the sect halls and the retreats.
- **Pickups glow.** Anything you can take stands in a warm pool of light. Its item icon bobs in a gold ring above
  it, with turning glints and its name on a plate; the verb shows when you are close.
- **The Fisher's Hut (the first room).**
  - Aunt Ping's three teas now show as tea bowls, not brown jars that read as clods of earth.
  - The tea on the table now sits on the tabletop instead of hidden behind the table.
  - The loft's bonus tea stays out of sight until the loft ladder can be climbed (after *The Runaway Kite*), so the
    first quest shows exactly three.
- **Prologue steps are no longer silent.** The quest tracker is revealed after *Morning Tide*, so until then:
  - the new-quest toast names the first step ("Pick up Herbal Tea 0/3");
  - each step forward shows as a toast ("Pick up Herbal Tea 2/3", ticked when done).

  New `QuestAuthority.steps_forward`.
- **Tests.**
  - `prologue_run`:
    - the hut's exit draws a door;
    - exactly three teas show, each as its icon;
    - each tea is counted as a step while the tracker is hidden;
    - all three are held at once.
  - `rules_tests` `text_suite`:
    - the fonts carry their weights;
    - small headings use the bold serif;
    - the minimum size holds;
    - Large text widens words and lines.
- Debug tools: `--text-size=0|1|2` previews at a text size.
- The Android preset is version 1.0.1 (code 101), so the rebuilt APK installs over 1.0.0.

### V9d3 · Weapon awakening and legendary chains (S47, v1.1+)
- **Weapon awakening.** A weapon can be awakened at any forge (the new Awaken section on the Forge's Enhance tab)
  when:
  - it is Heaven grade or better and at +10;
  - its family's Dao is at Explanation (tier 4);
  - you have a **Weapon Soul Crystal**, which is used up.
- An awakened weapon:
  - glows: a warm halo on the weapon side and gold motes rising in front of the body;
  - strikes on its own every so many blows with its family's skill: Sword Light (jian), Piercing Light (spear),
    Shadow Twin (short blade), Cleaving Wave (heavy sabre), Gale Leaf (fan), Echoing Note (flute), Twin Arrow (bow),
    or, as a ring around you, Thunder Knuckles (gauntlets) and Sweeping Gale (staff).
- New intent `awaken_weapon` and event `weapon_awakened` (a toast and a burst of light).
- *A Blade That Answers* (Smith Hong, Cloudgate Port, after the Ascension Gate) asks you to forge a Heaven weapon to
  +10 and gives the first crystal. After that, the Ironroot Clan Forge sells crystals for 900 spirit stones.
- **Legendary chains** (`legendary_chains.json`). There is one questline per weapon family, nine in all: bare fists
  have no weapon, so the Fist Dao's chain is the gauntlets'.
  - Each chain gathers three pieces. One comes from an old foe of the valley (the Drowned Abbot, the Riverbed Serpent,
    Big Toad Tan and the valley's elites). Two come from the Azure Expanse (its creatures at 12%, and the Thousand-Eye
    Toad, the Scarlet Kiln Warden and the Tomb King).
  - A piece drops only while its chain wants it.
  - An Expert smith makes the pieces whole at a forge (with Mystic ore and Refining Essence). The result is a
    Mystic-grade legend with a gift of its own.
  - Awakened at +10, a legend strikes with its own skill instead of its family's.
  - Smith Bao or Smith Hong gives each chain from the Ascension Gate on. The quest teaches the restoring recipe, and it
    ends when the legend is awake.
- **The nine legends:**
  - Stone Drum Gauntlets (Mountain Drum, a ring);
  - Riverlight Jian (Riverlight Cut);
  - Heron's Reach (Heron Strike);
  - Reedwhisper Dagger (Whisper Through Reeds);
  - The Ferryman's Pole (Pole the Current, a ring);
  - Mountainsplit Sabre (Split the Mountain, a ring);
  - Seven Winds Fan (The Seventh Wind);
  - Crane Mourning Flute (Crane's Lament);
  - Dragonfly Bow (Dragonfly Volley, three arrows).
- **Later steps.** Each chain lists its later steps, a Spirit-grade and a Sage-grade reforging in the Outer Heavens
  (v1.4 and v1.5). They are data only until those zones exist.
- **Art.** 28 new icons: the nine chains' pieces (a hilt, a fragment and a caged heart, in each legend's colour) and
  the Weapon Soul Crystal. The legends use the Mistjade weapon art of their family.
- **Code.** The Artifact Spirit's skill and a weapon's awakened skill share one strike: projectiles that pass through
  every foe in their path, or a ring around the wielder.
- **Tests.**
  - The new rules suite covers:
    - the awakening gates (grade, +10, Dao tier, crystal, forge), one awakening per weapon and the flag;
    - the family skill on its count, and Smith Hong's +10 flag;
    - the nine chains and a chain's quest shape and Expert recipe;
    - the gated piece drop, a legend's gift and own skill, and a ring skill.
  - Data validation checks every chain's weapon, pieces, sources, recipe, quest and later steps, and every
    family's awakening skill.
- Debug flag: `--awaken=item[:awake]`.

### V9d2 · Artifact Spirit depth and imitation relics (S47, v1.0 and v1.1)
- **Affinity.** A bound relic's spirit, asleep or awake, has an affinity meter (0–100) saved on the blade.
  - **Use** feeds it: one point for every 25 blows the relic lands in your hand.
  - **Gifts** feed it: three a day, on the Bag page (Refining Essence 10, Mist Lotus 6, Cloudsteel 4, Jadeiron 2).
    Each spirit's favourite counts double: Mist Lotus for the Moon Spirit, Refining Essence for the Blade Spirit.
  - Affinity raises an awake spirit's gift and skill by up to half again.
- **Waking is a quest per relic.**
  - A spirit answers the soul contest only once it knows your hand (affinity 30), and only where it once slept.
  - *The Blade That Sleeps No More*: the Sleeping Blade wakes in the Abbot's sanctum.
  - *Moon on the Water*: the Moonlit Blade wakes at the Lake Shrine on Mirrorwater Lake.
  - Elder Hu offers each quest once the relic is bound. The quest steps follow the flags `bound:`, `spirit_close:`
    and `spirit_awake:`.
- **Skills.** An awake spirit strikes on its own:
  - the **Moonlit Crescent**, a Qi crescent of moonlight every 8 blows (160%);
  - the **Waking Edge**, a flying edge every 10 blows (220%).
  - Each goes through every foe in its path and is weighed by the spirit's power.
- **Control demand.** An awake spirit needs Spirit at or above its demand: 60 for the Moon Spirit, 80 for the Blade
  Spirit. Below that it gives half its gift, keeps its skill to itself, and says so when you take it in hand.
- **Devour.** Held in hand, the spirit eats a weaker weapon of its own family: a lower grade, or the same grade at a
  lower item level. It will not eat a locked, natal or relic weapon.
  - Each meal adds spirit XP (by grade: 2, 4, 8 or 16) and 2 affinity.
  - Levels 1–5 come at 10, 30, 60, 100 and 150 XP, and each adds 10% to the gift and skill.
- **Barks.** Each spirit has its own one-line barks, for waking, kills, gifts, meals, low health, and refusing a weak
  hand.
  - A line shows in a violet-edged bubble over your head and in the log.
  - Kills speak one time in four, with 40 s of quiet between lines. Waking, gifts, meals and refusals always speak.
- **The Bag page** shows the spirit's affinity and level and what it still needs. It has Subdue, Gift (the best gift
  you carry, favourite first) and Devour (the weakest candidate) for the relic in hand.
- **Imitation relics** (v1.1). Expert smiths forge copies that keep 60% of a boss relic's gift, always on, with no
  binding, spirit or control demand:
  - the **Moonshadow Jian** (+4.8% Qi Attack, from the Moonlit Blade);
  - the **Drowsing Edge** (+6% crit damage, from the Sleeping Blade).
  - Their recipes are sold at the Stoneford Smith (2,400 taels) once you have bound the original.
- New events:
  - Inventory: `spirit_affinity_changed`, `artifact_spirit_spoke` and `artifact_spirit_grew`;
  - Combat: `artifact_skill_used`.
- Tests:
  - The new rules suite covers:
    - affinity from use and gifts, the daily cap and the favourite;
    - the waking gates (affinity and place) and the quest flags;
    - the gift growing with affinity, devouring (family, locks, levels) and the skill every tenth blow;
    - the control demand halving the gift and silencing the skill, and the barks' quiet;
    - the imitation's 60%, and its recipe and scroll gates.
  - The valley run now wins the Blade Spirit's trust with two gifts and wakes it in the Abbot's sanctum.
  - Data validation checks every relic spirit's fields, barks and awakening quest, and every imitation's share.
- Debug flag: `--relic=item[:awake[:affinity]]`. `--open-page=inventory:weapon` opens the Bag on the worn weapon.

### V9d1 · The sword swarm, Array Plates in a fight, and the combat puppet (S47, S48, v1.1)
- **The Sword Swarm** is the Sword Dao's fifth tier. It is a toggle technique (30 QI, 30 s cooldown).
  - Swords of Qi orbit you for 12 s and take turns striking the nearest foe within 420. There is one strike every
    1.2 s divided by the number of swords, each at 0.9 ÷ √n of your attack, so more swords add damage but not in
    proportion.
  - **How many swords:** 3 at Sword Dao 5; 9 with the **Nine Swords Array** (released, or set in a Treasure slot);
    36 with the Array at Original Application (tier 6).
  - **Spirit is the control demand:** you can steer one sword for each 10 Spirit.
  - The **Nine Swords Array** is a new treasure (60 QI, 45 s cooldown; the swarm lasts 12 s). Its recipe is a
    heaven-grade smithing recipe for an expert smith. The scroll is sold at the Ironroot Clan Forge for 60 spirit
    stones.
  - The swords orbit your chest, riding or on foot. The near half of the ring is drawn over the body.
  - **Deviation:** the swarm's swords are the flying sword's seeking projectiles, not one pet-style actor per
    sword. This keeps 36 swords cheap and uses the Sword Release rules already tested.
- **Array Plates in a fight.** A plate from the bag lays an array at your feet for a few seconds. Arrays stay in
  the room they were laid in.
  - **Guarding array** (the old Array Plate): +15% Physical Defense while you stand inside its ring, for 12 s.
  - **Killing array** (new): every foe inside takes 50% of your Qi Attack each second, for 10 s.
  - **Binding array** (new): every foe inside is slowed by 40%, for 10 s.
  - **The Formation Dao scales them.** From tier 1 an array lasts 10% longer, and each tier makes the killing array
    20% sharper. Each plate laid teaches the Formation Dao 3 insight.
  - The two new plates are formations recipes: a blank plate and a formation stone, plus two ore dust (killing) or
    two willow moss (binding). *Carry a Wall* teaches all three plates.
  - Each array is drawn in its plate's colour with its own centre: trigram bars (guarding), four blades pointing
    inward (killing) or a turning chain (binding).
  - New events: `array_deployed` and `array_faded` (world FX and sound).
- **Formations placed in the world:** from Formation Dao tier 1 they hold 10% longer, and each placement teaches the
  Dao 5 insight.
- **The combat puppet** (S48; from Cloud Stride 5, when puppetry opens).
  - Tinkerer Yu builds it at the Stoneford bench from 8 spirit wood, 2 puppet cores and 4 jadeiron. You can own only
    one.
  - It takes a pet slot and fights beside you. It is a construct: it is built full-grown, and it has no traits,
    bloodline, hunger or bond. It cannot breed, fuse, evolve, break through or devour cores, and it only takes the
    combat role.
  - Three knockouts break it, as they wound an animal. A Beast Revival Pill or a rest does not mend it; the
    tinkerer repairs it for 2 spirit wood (the new Repair button on the Puppets tab).
  - The Spirit Animals page shows it as a Construct, with what it can and cannot do, in place of food, traits and
    growth.
- Four new icons: the killing and binding plates, the Nine Swords Array and the Sword Swarm.
- The new rules suite covers:
  - the swarm: its counts, the Spirit cap, Sword Dao 5 teaching it, the toggle and its QI, strikes without a
    button, recall, the time running out, and the treasure release;
  - the arrays: the guarding defence, the killing damage, the binding slow, the Formation Dao scaling, fading, and
    leaving the room;
  - the puppet: the build, one only, no food, only the combat role, no breeding or growth, not mended by pills,
    and the paid repair.
- Debug flags: `--swarm` and `--arrays`.

### V9c3 · Sect role variants and the sect tree (S48, v0.9)
- The Sect page has a new **Role** tab, open from Outer Disciple.
- **Signature lines.** Each sect has one, and each line has a damage and a support variant. The first choice is
  free; changing it costs 50 contribution.
  - **Jade** (Flowing Palm, Palm Wave, Rising Tide):
    - Surging Tide: +25% damage.
    - Mending Current: each use heals you and every ally within 220 by 4%, and slows each foe hit by 20% for two
      seconds.
  - **Cloud** (Jade Thrust, Spear Lance, Dragon Tail Sweep):
    - Piercing Peak: +20% damage, one more target, +10% penetration.
    - Guarding Cloud: a shield of 8% of your health for 4 s, and allies within 220 healed by 3%.
  - Support healing grows with the crafts you have ranked up: +5% per rank step, up to +50% (v2's
    `profession_rank_up` → sect roles).
- **The sect tree**: three branches of five nodes, bought in order with contribution (60, 120, 200, 320, 480). The
  third node needs Inner Disciple and the fifth Core Disciple. Each sect names the branches its own way.
  - Edge: attack, crit damage, signature arts ready 1 s sooner, signature arts +15% damage.
  - Lotus: healing received, QI recovery, the support variant heals half again as much, signature arts cost 20%
    less QI.
  - Root: max HP, Physical Defense, Qi Resistance, Tenacity, guard.
- New events: `sect_role_chosen` and `sect_node_bought` (HUD; stats refresh when a node is bought).
- The new rules suite covers the rank gate, the free first choice and the paid switch, the variant limited to the
  line, the support heal and its craft scaling, buying in order with its rank and contribution gates, the tree's
  flags, and the Cloud shield. Debug flag: `--join=sect[:rank]`.

### V9c2 · The Blood path and the Buddhist path (S48, S49 alignment)
- **The Blood path** (v1.1) is an opt-in for a demonic heart. It never locks anything else.
  - Take it on the Cultivation page's new **Paths** tab (the Vows tab, renamed), from Heart Tempering 1 at alignment
    -20 or lower. Taking it costs 10 alignment and 20 of the training sect's regard, and opens the Blood Dao.
  - Leaving it adds 10 heart demon.
  - While on it: the heart demon grows twice as fast; every hit drinks back 3% of its damage (+1% per Blood Dao
    tier, twice that for Blood arts); kills fill a blood-essence meter (10 a foe, 25 an elite, 50 a boss, up to
    100; it drains after 20 s without a kill). A thin crimson strip under the HUD bars shows it.
  - **Three Blood arts**, sold by Peddler Shao at night to the demonic side only. Each spends health, and blood
    essence pays first (one point per 1% of health). Each use costs a point of sect regard:
    - Crimson Palm (5%, Heart Tempering 1);
    - Blood River Slash (10%, Heart Tempering 5);
    - Sanguine Lotus (15%, Cloud Stride 1).
  - **Sect regard** now shows on the Sect page. Below zero, the Mission Hall lends no technique manuals (the new
    `reputation_at_least` requirement).
- **The Buddhist path** (v1.1):
  - **Golden Body** (Heart Tempering 3): for a vow-keeper only, +25% Physical Defence and Qi Resistance and +15%
    healing received for 10 s. The Mission Halls lend it to the upright (alignment 20, merit 50).
  - **Merit milestones calm the heart**: each hundred merit a vow-keeper crosses takes 10 heart demon away.
  - **Healing an ally is merit**: Clear Heart Melody reaching a companion or pet gives +1 merit, five times a day.
- The Paths tab shows three cards (the Blood path, the Buddhist path, the Poison Body) above the vows.
- New event: `path_changed` (HUD). Four new technique icons.
- The new rules suite covers:
  - the alignment gate, the costs of taking and leaving the path, and the path surviving a save;
  - the doubled heart demon, the Blood arts' costs paid from blood essence, the essence gains and drain;
  - lifesteal, and the sect-regard gate on manuals;
  - merit milestones, the daily healing merit and the Golden Body's vow gate.

### V9c1 · The Soul line, the Poison path and the meridian gates (S48, S10)
- **The Soul line** (S48, v1.0). The Soul Dao's first three tiers each teach a technique:
  - **Sense Lock** (tier 1): fixes your Spirit Sense on one foe within 420 for 8 s. It cannot evade you and cannot
    hide (a burrower stays in sight).
  - **Phantom Double** (tier 2): leaves an illusion where you stand for 6 s (+1 s per Soul Dao tier). Foes within
    500 hunt it until it has been struck three times; bosses see through it. The world draws it as a pale copy of
    you (`illusion_cast` and `illusion_broken`).
  - **Soul Search** (tier 3): a spike into an elite or boss that ignores armour. If it dies within 12 s you read a
    memory from its soul (ten new Codex pages) and find what it hid: one more loot roll (`soul_searched`).
- **Spirit as a main stat.** Soul attack now scales with Spirit and Insight (+0.8% and +0.4% a point) whatever the
  weapon, on top of Spirit's +0.5% soul attack.
- **Soul Lantern Ward** now works: a shield of 20% of max Soul for 6 s. Before, it set a stat nothing read.
- **Teachers for the mentor's techniques.** Three techniques had no source:
  - Elder Hu teaches Mirror Mind Spike in "A Lake Inside" (Spirit Awakening 1);
  - Soul Lantern Ward in "The Mentor's Gift" (Spirit Awakening 5);
  - Still Water Focus in "Brothers in Arms" (Heart Tempering 6).
- **The Poison path** (S48, v1.1).
  - Peddler Shao sells two poison arts at night: Venom Needles (three seeking needles that poison, Qi Unfurling 1)
    and Miasma Palm (poisons every foe within 160, Heart Tempering 1).
  - **Poison Body**: with a poison art known and toxicity past half your tolerance, each hit turns a point of your
    own toxicity into poison on the foe (2% of its health a second for 4 s, once per foe each half second). A HUD
    icon shows while it is open.
- **The S10 meridian gates, completed.** Ten of the fifteen gates had no effect; all now work:
  - Agility 50: a second dodge charge.
  - Essence 25: the first technique of each fight costs no QI. A fight starts after 8 s without a blow.
  - Essence 50: flight costs 20% less QI.
  - Essence 100: Qi projectiles pierce one more foe (flute notes too).
  - Spirit 25: the Sense pulse costs 25% less.
  - Spirit 50: fear and confusion from weaker foes do not take.
  - Spirit 100: soul attacks ignore 20% of Soul Defence.
  - Insight 25: one free affix reroll a week (the Forge says so).
  - Insight 50: insight stones give double.
  - Insight 100: a Dao at Explanation or above gives one more tier's effect.
- New art: five technique icons and two status icons (Sense Locked, Poison Body).
- The new rules suite covers:
  - the grants and the Soul Dao's teaching;
  - Spirit scaling and every gate at its threshold;
  - Sense Lock against an evasive foe;
  - the illusion (drawing foes, breaking, fading) and Soul Search on elites only;
  - the ward, the Poison Body and the peddler's stock.

  Debug flag: `--illusion`.

### V9b · Weapon families: the heavy sabre, the fan and the flute (S47 v1.1, the Music path)
Three new weapon families, each with seven grades (Training to Sunsteel), smithing recipes, icons, avatar art in every
animation, a stance, two techniques and a Dao.
- **The heavy sabre** (Blade Dao, Body).
  - It is slow (0.75 hits a second) and its cleave strikes up to three foes in a line.
  - Every blow may break armour (30%; always on the third stroke). A **Sundered** foe takes every hit through a
    quarter of its defence for 4 s.
  - Its stance is Iron Ox: twice the armour-break chance, 10% slower on foot.
  - Techniques: Mountain Cleaver and Thunder Dao Arc.
- **The fan** (Fan Dao, Agility and Insight).
  - Its wind reaches 140. The third stroke throws the fan 280 units out and back, cutting everything both ways.
  - A foe the wind catches is **launched**: it rises in an arc and can neither move nor strike for 0.8 s. Bosses,
    flyers and immovable foes are not launched.
  - Its stance is Drifting Cloud (+15% reach).
  - Techniques: Gale Fan, and Returning Crane Fan (a thrown fan that returns).
- **The flute** (Music Dao, Insight and Essence).
  - A tap sends a note of Qi 240 units.
  - **Hold Attack** (0.35 s) to play a melody. Every half second it slows the foes within 220 by 30% and may
    confuse them (8%). You recover 1% of your health a second, and every companion and pet in the circle 2%.
  - Composure pays for it at 8 a second. It needs Composure (Qi Unfurling) and ends when you let go, when Composure
    runs out, or when you are stunned, wounded, attack, fly or change rooms. You walk at half pace while playing.
  - Each Music Dao tier carries the melody 5% further. Its stance is Clear Note (a third less Composure).
  - Techniques: Reed Song (three seeking notes) and Clear Heart Melody. Clear Heart Melody now heals the caster and
    every ally within 220 by 4% a second for 6 s, in a fight too.
  - New events in the contract: `melody_changed` and `melody_pulse`. The HUD notes a melody broken or spent, and
    the world draws a jade ring and rising notes.
- **Monsters now answer Fear and Confusion.** A feared monster runs from its foe and a confused one stumbles back
  and forth; neither attacks until it ends. Stun, root and the fan's launch already held them.
- **Getting them.**
  - The Stoneford Smith sells the training and iron grades; the jade-iron grades join its rotation.
  - The Inner Disciple quest teaches each family's Qi technique.
  - The Mission Halls now lend every library technique (library 1 to 3, and the Cloud library for Cloud
    disciples) as a Technique Manual for contribution. Until now these had no source.
- **Art.** Sabre, fan and flute avatar sheets are baked for every action and both facings (`tools/art/bake_weapons.py`).
  They were reviewed in every animation, with plain and dyed robes. New art: equipment and technique icons, HUD
  glyphs, and note and fan projectiles.
- The new rules suite covers:
  - the cleave, Sundered and launch;
  - the returning throw and the note;
  - the melody (slow, heals, drain, release, running dry);
  - Fear, Clear Heart Melody and the Mission Hall manuals.

  Debug flags: `--wield=item`, `--foe=enemy[:count]`, `--melody` and `--throw`.

### V9a · v2 hooks: rule kinds, the treasure-birth pillar, world-event markers and the pet command wheel
A sweep of every v2 audit row against the build after V8g3 lists what v2 makes due by v1.1 and is still open. It
is planned as V9a–V9f in `docs/v2_audit.md`. V9a covers the small hooks:
- **Rule kinds.**
  - New requirements: `heart_demon_at_most` and `foundation_share_at_most`.
  - New effects: `grant_fate` (a fate given as if chosen, leaving any offer alone) and `absorb_flame` (a Heavenly
    Flame given outright).
  - Aliases for v2's names: `art_known` for the secret-art requirement, `grant_art` for learning one.
  - Data validation now reads every alias on a rule line.
- **Treasure births.** World announces each Spirit Fruit ripening (`treasure_birth_announced`, with its room and
  fruit) and the HUD logs it. On the minimap the tree stands up as a pulsing pillar of light while it is ripe.
- **Other minimap markers.** Spirit mines show as a diamond: jade when yours, the holder's colour when not.
- **World map markers.** Each region with a world event gets a diamond: gold and glowing while the event is under
  way, violet while it is coming. The region's panel names each event and its room.
- **The pet command wheel** (v2 HUD). Hold the Pet button (0.45 s) and drag to a choice; a tap still opens the page.
  The choices are:
  - Follow;
  - Stay, which holds its spot and only fights what comes close;
  - Attack, which reaches to 600 instead of 260;
  - Hold back, which never fights;
  - Ride or Dismount;
  - the Pet Bag.

  The order is kept for every animal out with you and for new ones called (`pet_commanded`, now in the contract).
  The active order has a gold ring.
- **Settle foundation** shows as a seclusion focus only once pills make up more than 20% of this realm's foundation
  (the v2 unlock timeline), or while it is the focus.
- **The depth-hooks suite** (v2's test list). A new character carries every S44–S49 field, neutral. Non-neutral
  values of every one survive a save as JSON and a restore. The account's calendar, activity and sect (with its
  mines) round-trip too. `docs/v2_audit.md` records where the build's names differ from v2's.
- New rules tests cover the rule kinds, the announcement and the wheel. Debug flag: `--pet-wheel`.

### V8g3 · The living world: territory and spirit mines (S49)
- **Spirit-stone mines** (`territory.json`). There are five, each a vein in a field room with sacks, a barrel and
  the holder's banner beside it:
  - Lower Pit Seam, Stonewall Quarry: Level 9, 1 stone an hour.
  - Grey Pools Seep, Reed Marsh: Level 14, 2 an hour.
  - Rapids Terrace Vein, Whitewater Gorge: Level 32, 3 an hour.
  - Lightning Scar Lode, Thunderhorn Plains: Level 66, 6 an hour.
  - Glass Dunes Lode, Sunscar: Level 75, 8 an hour.
- **Three rival sects** hold the mines at first:
  - Ironpine Gate: spearmen in ochre.
  - Blackreed Hall: veiled marsh-folk in ink.
  - Scarlet Kiln Sect: forge-cultivators in crimson.

  Each sect has its own disciples, a named warden and a banner. The six new enemies use existing avatar parts and
  dyes only. The four banners are new props, one for each rival and one for your own sect.
- **Taking a mine** (`assault_mine`). This extends the S25 defence waves into offence.
  - Survey the vein and choose *Take the mine*. Three guards stand at the vein at the mine's Level, more come while
    they fall, and the warden stands three Levels higher.
  - Bring the warden down within two minutes and the mine is yours, with +30 Prestige (`mine_claimed`).
  - Your sect can hold one mine, plus one more at every third sect level. Each mine also needs its own sect level.
- **Production.** A mine you hold fills its carts with its rate every hour, up to a day's worth. Collect at the vein
  or on the Territory tab (`collect_mine`) for Spirit Stones and 1 Prestige per stone (`mine_collected`). Only whole
  stones leave the carts.
- **Contests on a timer.**
  - Every two to four days the old holder comes back (`mine_contested`). The timer is seeded by the account and
    runs offline.
  - A toast and a phone notification (the Defence category) give you twelve hours. Hold the mine in person: survive
    a minute of waves, with the warden joining after 20 seconds (`defend_mine`).
  - If you do not come, the guards you posted decide it when the window closes. The chance is 30%, plus 15% for each
    guard and 1% for each of the guard's Levels.
  - A held mine pays +20 Prestige (`mine_defended`). A lost one goes back to its holder with whatever was in the
    carts (`mine_lost`).
- **Guards** (`guard_mine`). Post up to three disciples at each mine. A disciple on guard cannot go on an
  expedition, and one on an expedition cannot stand guard.
- **The Territory tab** on the Your Sect page lists every mine with:
  - its banner, room, Level, rate and needed sect level;
  - its holder, or its carts and when the rivals come;
  - its guards and their chance to hold it.

  It has Collect, Post guard, Recall and Go buttons. Go walks you there by quest auto-path.
- Fixes:
  - An expedition now sends two disciples who are home. Before, every expedition sent disciple 0, because the page
    passed names where the rule wanted indices.
  - The "back" label is now a string, not a literal.
- New rules tests cover the data, the assault and its guards, the cap, the carts and their limit, guards and
  expeditions, the contest timer, holding the mine in person, and losing it with its carts. Debug flags:
  `--mine=id[:contested]` and `--assault=id`.

### V8g2 · The living world: the mortal kingdom and leisure arts (S49)
- **The County Hall** (`sf_county_hall`). It is a new room behind Stoneford Gate. Its door is under a roof that a
  rope bridge joins to the gatehouse.
  - Magistrate Qian, a new NPC made only from existing avatar parts, keeps the hall.
  - The hall has the county job board and the locked relief box. Either one, or the magistrate's "County business"
    service, opens the new County page.
- **County jobs** (`relations.json` `mortal`, Relations authority).
  - Each day, three jobs are drawn for the character from four boards: vermin, raiders, relief deliveries and
    letters. Each board offers only jobs that suit the character's Level.
  - Reading the board accepts the jobs. They show on the Quests page's Daily tab, and yesterday's unfinished jobs
    are taken down.
  - A job pays silver by Level, 10 county favour and the `county_service` deed (+3 merit).
- **County favour** has four named tiers: Stranger (0), Known at the Hall (50), Friend of the County (150) and
  Benefactor (400).
  - The last two grant the county's titles, *Friend of the County* and *Benefactor of Stoneford* (coin find).
  - A Benefactor pays 5% less in Stoneford's shops.
  - The HUD announces a new tier (`favour_changed`).
- **The relief fund.** You can give 100, 1,000 or 10,000 silver, each size once a day (`donate_relief`,
  `relief_donated`). The gifts pay 1, 8 or 60 merit and 3, 30 or 200 favour; the largest also adds Fame.
- **Non-interference.** From Qi Kindling up, using a technique in a mortal town (Lotus Ferry's village or Greyreed
  Hamlet) is the `mortal_interference` deed: +5 sin and -2 alignment, at most once a minute. The magistrate warns
  you about it. In the wild, a technique carries no penalty.
- **Leisure arts: the guqin.** A seven-string guqin is sold at the Stoneford Tea House. Play it from the bag and the
  new Guqin page opens: a short rhythm piece of 16 notes on five strings.
  - Tap the strings, or press 1 to 5, as each note reaches the line. PERFECT and GOOD windows score the playing.
  - A clean piece makes meditation up to 15% faster for 30 minutes, and never less than 5%. Then the hands rest as
    long (`play_guqin`, `guqin_played`).
- **Leisure arts: chess** (`chess.json`, six Go problems on a 9×9 board).
  - Every insight stone offers a chess problem as well as meditation. Each site has its own problem for the day,
    the same on every device. Each problem has four lettered points, and only one is right.
  - The new Chess page gives one answer a day at each site. The right point gives insight into your deepest Dao, or
    a little realm progress before you have one (`solve_chess`, `chess_solved`).
  - The fortune deck's Hermit's Chess Problem now uses the same rule.
- **Regional teas.** Each tea house pours its own tea, with a new icon for each:
  - Jasmine Dew (Stoneford): +10% insight for 30 minutes.
  - Marsh Mist (Greyreed): +8% evasion.
  - Thunderhead (Cloudgate Port): +2 Storm Ward.
- New rules tests cover the jobs, the favour tiers, the titles and discount, the relief fund's limits,
  non-interference in towns and the wild, the guqin's bonus and rest, and the chess problems.

### V8g1 · Mobile conventions: idle-room eligibility, auto-hunt and quest auto-path (S49)
- **Idle rooms.** Idle Hunt and Gather now run only in rooms that list them (`room.idle`, the S23 Hunt rule). A
  town or a dungeon refuses them, with the reason, and the Characters page greys those buttons out there. Saves that
  set an idle hunt somewhere else gain nothing from it. Rest, seclusion and training still go anywhere.
- **Auto-hunt** (`set_auto_hunt`). A small **AUTO** toggle sits under the icon row, shown only where idle Hunt is
  allowed.
  - It is off in towns, trials, dungeons, boss dens and story instances. It switches itself off when a room event
    starts, a boss appears, a tribulation begins or health falls below a fifth.
  - Your character closes on the nearest foe along the room's navigation graph (walking, jumping, climbing,
    dropping). It fights with basic attacks and the equipped techniques, and picks up the drops between fights.
  - It never uses treasures, pills or breakthroughs. Touching the joystick takes over.
- **Quest auto-path** (`auto_path`). A small ➤ button beside each tracked quest walks you to where it leads, or to
  the hand-in NPC's room once it is ready.
  - `WorldRules.route` finds the fewest rooms through the portals open to this character (realm, quests, arts,
    hidden ways found). It also crosses the Starsea by boarding from a dock, and stops there, saying why, if you
    have no vessel or chart.
  - Within a room, the autopilot follows the navigation graph, then presses up at a door or walks out through an
    edge.
  - It stops at danger (the first blow), when you touch the joystick, or on arrival. Verified live: Willow Path West
    to Market Street through Stoneford Gate.
- New tests:
  - Data validation checks that every quest target is reachable from its giver without movement arts the
    character has not been taught (the Breath Control grotto stays closed to it).
  - Rules tests cover the idle-room rule, auto-hunt refusals and cut-offs, routes, the portal to take, stopping at
    danger, arriving, and the Starsea dock.
- Debug flags: `--auto-path=room`, `--auto-hunt` and `--wait=s` (let them run before the capture).

### V8f · The living world: the Heaven Ranking, the Trial Tower and daily activity chests (S49)
- **The Heaven Ranking** (`rankings.json`, Part 8's valley seeds). It is a tab on the World map. The seven ranked
  cultivators are:
  - Shen Lian and Wen Zhao;
  - Yun Zhiqiu and Bai Yuheng, the first disciples of the Cloud and Jade Sects;
  - "Iron Crane" Guo Ming, a rogue cultivator;
  - Captain Lou Chen, Madam Hua's guard captain;
  - Chief Yan Bo of the Gorge Bandit Adepts.
- How the ranking moves:
  - Each ranked cultivator climbs a set number of Levels every week of the account calendar, up to a ceiling. A
    seeded wobble keeps the order moving, and the table is the same on every device.
  - The Calendar announces a new order (`ranking_changed`), and the tab shows who rose or fell since last week.
  - You enter at the top eight by CP, or by reaching the Valley Tournament finals.
  - You can challenge the cultivator directly above you to a spar at their Level. Win, and you hold their place for
    the rest of the week and gain 15 Fame. Four new duelists use existing avatar parts only.
- **The Trial Tower** (`tower.json`, Part 8): thirty floors inside a pagoda at the Stoneford Fairground, Levels 4
  to 62, all in one new room.
  - Each floor is a room event with one of four rules:
    - **Clear**: defeat four foes in 90 seconds.
    - **Swift**: defeat three in 45 seconds.
    - **Survive**: hold out while waves come.
    - **Guardian**: every fifth floor, bring down its guardian and escort.
  - Clearing a floor for the first time pays Spirit Stones and opens the next floor.
  - The Tower page (at the pagoda's board or the stele inside) lists every floor with its rule, foes and rewards.
  - **Sweep** gives each cleared floor's loot once a day, straight to the bag (`sweep_floor`).
- **Daily activity chests** (`activity.json`, Account):
  - Points come from missions, dungeon clears, crafts, harvests, spars, tower floors, arena fights and the Beast
    Trial Grove. Some sources have daily caps.
  - The points fill four chests at 20, 40, 60 and 100, for the whole account, and reset each day.
  - A bar with the chests sits on the Quests page's Daily tab (`claim_activity_chest`). The HUD says when a chest
    is ready.
- Debug flags: `--tower=N`, `--climb=N` and `--activity=N`. New tests cover the tower, sweeps, the chests and the
  ranking.

### V8e · The living world: fortune encounters, heavenly phenomena and lifespan (S49)
- **Fortune encounters** (`fortune_deck.json`, Part 8's eight vignettes). A card can turn up when you enter a room,
  gather, or recover from a fall into the void. It appears as a card at the top of the screen.
  - **The Fortune meter** (Relations) fills over three hours of play and holds one encounter, so encounters cannot be
    farmed. It starts empty, and the Karma tab shows how long it has left to fill.
  - Fortune raises the chance and every card's weight. Merit makes the kind cards likelier. Draws use the
    character's own fortune stream.
  - The cards:
    - A **Hidden Cave**: a fall ends in the Hidden Grotto, a new unmapped room. Its old chest fills again for each
      such fall, and the way up leaves you where you fell.
    - A remnant soul in a ring: three manual pages.
    - The hermit's chess problem: insight into your deepest Dao.
    - A wounded crane: +2 bond with your Jade Crane, and a little merit.
    - A jar of **Hundred-Year Wine**: pour it over the furnace and your next Perfect batch has +25% chance to come
      out Grain.
    - A lost child walked home: +10 merit.
    - A meteor fragment of Cloudsteel.
    - A **Dream of the River** (a Codex entry, once).
  - Debug flag: `--fortune=<card>`.
- **Heavenly phenomena**. The Calendar announces each one:
  - A major breakthrough gathers golden clouds and a pillar of light over the room.
  - A tribulation darkens the room with a storm bank and bolts.
  - People nearby call out, in congratulation or alarm.
  - Where people saw the clouds, a **jealous senior** (Senior Brother Hao Qian) may challenge you to a spar at your
    new level, for Fame.
  - Debug flag: `--phenomenon=cloud|lightning`.
- **Lifespan as flavour** (display only, never a clock):
  - Each great realm grants a span, from 80 years for a mortal to 1,200 at Sage, and without end at World Genesis.
  - Characters start at sixteen and age a year every four weeks (a season a week).
  - The Character page shows your age and lifespan, and the gift page shows named people growing older with you.
  - Longevity treasures add years. A **Longevity Peach** (+10) is sold at Auction Day. A **Thousand-Year Lingzhi**
    (+30) is your master's parting gift in The Elder's Last Lesson, with a Codex entry on years.

### V8d2 · The living world: Auction Day, Spirit Fruit births, the Herb Terraces trial and weather (S49)
- **Auction Day** (Part 8): every Saturday an auctioneer's stall stands on Market Street. It shows only while the
  calendar event runs.
  - The valley house is a second auction beside the Pavilion's. It offers five lots at a time from rare seeds,
    spirit eggs, manual pages and recipe scrolls, for Spirit Stones. Every lot closes when the day ends.
  - Winning a recipe scroll teaches the recipe at once, and a letter confirms it.
  - The Pavilion auction is unchanged. Its lots, seeding and saves are as before.
- **A Spirit Fruit ripens** every fourth day for six hours, under a glowing tree in one of the valley's dry field
  rooms.
  - Reach for it and the room's beasts withdraw. Two rival cultivators and the Fruit-Guardian Boar, two levels
    above the room, stand in the way.
  - Beat all three and the fruit is yours, once per birth. Eating it gives 8% of this realm's progress, and heart
    demons fall by 5.
- **The Herb Terraces Trial** runs every Wednesday on the Jade Herb Terraces. Every herb you gather there while it
  runs counts against five of the valley's gatherers, whose scores come from a seeded draw.
  - The ranking pays out once, when the day is over. The top three learn the Foundation Guard Pill, and the top
    two also receive pills.
  - The Calendar page shows your standing while the trial runs.
- **Weather effects** (never gating):
  - Rain widens the fishing bite window and adds 10% gathering power.
  - Fog adds 5% evasion.
  - A storm adds 10% elemental power to Thunder techniques.
  - The effects apply when you enter a room and change with the sky. Rain and storms draw streaks and a grey tint
    (storms also flash), and fog drifts over the room.
- Debug: `--event=<id>` moves the clock to an event's next opening, and `--weather=rain|fog|storm` previews a sky.

### V8d1 · The living world: the world calendar, spatial rifts and reopenings (S49)
- **Calendar authority** (new, account level). The schedule is pure (`CalendarRules`): it comes from the account
  seed, the account's first day and the UTC clock, so the same save shows the same calendar on any device.
  - Draws come from `Rng.keyed`, which is stateless and never moves a gameplay stream.
  - The authority announces events a day ahead (a notification through the Notifier), when they start and when
    they end, the season and the weather.
- **calendar.json** (`tools/data/living_world.py`):
  - A **Spatial Rift** every three days for an hour, in one of the valley's seventeen field rooms. Its violet tear
    shows only then. Touch it and the room's beasts pour out three levels stronger for a minute; survive, and it
    leaves a chest's roll at your feet (once per rift).
  - **The Drowned Shrine Surfaces** every fifth day, for a day. After its first defeat the Drowned Abbot wakes
    again only then, at Qi Unfurling 9 and below.
  - **The Waterfall Cave Opens** two days later on the same rhythm. A new inner cache fills once per opening,
    at Heart Tempering 9 and below.
  - First visits, the story entry and the vault are never behind the cycle.
  - The weekly Beast Tide shows on the calendar too.
- **Seasons** now run from the account's first week, spring first. Saves from before this keep the old count.
  The account gains `created_utc` and a `calendar` block.
- **Weather** (v1.1 groundwork): a seeded pick every three hours for Reedmarsh and Whitewater Gorge (rain or fog)
  and Summit Ridge (storms or fog). Those rooms carry their region. Effects and visuals came in V8d2.
- **Calendar page** (a new Menu entry; the Menu is now seven tiles wide): the season and its days left, the
  weather by region, this week's Beast Tide, and every world event with when, where and whether its repeat runs
  are open to you.
- New requirement kinds `world_event_active` and `world_event_here`; chests that `reopens` with an event.
- **Events:** `world_event_scheduled`, `world_event_started`, `world_event_ended`, `season_changed`,
  `weather_changed` and `rift_opened`, with HUD notes.
- **Tests:**
  - the same save gives the same calendar, and another seed moves the rifts;
  - each rhythm and duration;
  - repeat runs open and capped, while the first defeat is never gated;
  - the cache is keyed to each opening;
  - the rift tear, its once-per-rift rule and its +3 levels;
  - spring first from the account's week.

### V8c · The living world: grudges, hunters, bounties, mercy and named debts (S49)
- **Grudges** (factions.json) against three factions:
  - the Mudwater Bandits (hunters at 30; 200 taels, or a duel with Tan the Younger);
  - the Gorge Bandits (hunters at 30; 400 taels, or the new quest **Old Scores**: a fair fight with Chief Yan Bo
    at the Gorge Mouth for Trader Min);
  - Elder Gu's Stoneford Smugglers (hunters at 50). Theirs is story-bound: +20 for the cargo, +20 for the hidden
    cargo, and gone for good when the warehouse falls.
- **Grudge rules**:
  - Only named kills raise a grudge (+15), such as Big Toad Tan, the lieutenant and bounty targets.
  - Past the threshold, a hunter may be waiting in the faction's grounds (35%, at most every 30 minutes), at your
    level: a Mudwater Cutthroat, a Gorge Stalker or a Gu Family Enforcer.
- **Bounties** on the town board's new Bounties tab: One-Eye Pang (Caravan Road), Ferryman Lou (Bend Shore) and
  Knife-Hand Sui (Echo Cliffs).
  - You can hold two at a time, and take each one once a day. The target waits in its room while the bounty is
    yours.
  - Claiming pays taels and +10 Fame, and a bounty target is a named kill.
- **Mercy** (Part 8): Lieutenant Kuai, who now guards the Mudwater loot cave, yields at a fifth of his health. He
  kneels and cannot be struck. You judge him on the Mercy page, or with the Judge button when you stand near him.
  - Spare him: +10 merit. Before Gu's warehouse his warning arrives, with three Thunderclap Pellets.
  - Finish him: +15 sin. His brother Kuai Shan then waits for you on the Caravan Road.
- **Named debts** (Part 8):
  - Debts can now fall due with a quest as well as with time.
  - A debt can send a letter, set a flag or post a hunter.
  - Little Dou's rescue in the Hollow Night is repaid when the Heart Trial is done, with a Cloudtop Orchid.
- **The night peddler** (Part 8): Peddler Shao sets out his mat on the Caravan Road after dark. Every purchase
  there is +5 sin.
- **UI**:
  - The Relations page's Grudges tab shows each grudge against its threshold, with Pay and Duel buttons, or
    what settles it.
  - A Mercy page.
  - The Bounties tab.
  - A Codex entry, "Grudges and bounties".
- **Events:** `grudge_changed`, `hunter_dispatched`, `bounty_taken`, `bounty_claimed`, `foe_surrendered` and
  `foe_judged`, with HUD notes. Intents: `pay_grudge`, `take_bounty` and `judge_foe`. Combat's new
  `apply_execute` finishes a foe who yielded.
- **Debug flags:** `--grudge=faction:n`, `--open-page=mercy:def` and `--open-page=notice_board:bounties`.
- **Tests:**
  - named kills and ordinary ones;
  - hunters: chance, level and cooldown;
  - blood money, the duel, Old Scores and the story grudge;
  - a bounty from start to claim, and once a day;
  - surrender, both judgements and their debts;
  - Kuai Shan's hunt;
  - Dou's letter;
  - the night peddler.

### V8b · The living world: hearts, gifts and bonds (S49)
- **NPC affinity**: 0–5 hearts with fourteen named people and the four companions.
  - Part 8's favourite gifts: Aunt Ping's Riverfish Soup, Granny Liu's Mist Lotus, Old Ma's pearls, Mei Qing's
    Cloudtop Orchid, Lan Yue's Lotus Root Tea, Tie Niu's Boar Bone Broth, Qiu Feng's vulture plume and Bai
    Ling's formation stone. There are more for Little Dou, Lu, Uncle Guo, Shen Lian and the two elders.
  - One gift per person a day: a loved gift is a whole heart (+100), a liked one +40, anything else +15.
  - Each quest done for someone is +30.
  - Mei Qing and Shen Lian keep one heart count across their two rows.
  - What someone loves or likes is remembered once you learn it.
- **Hearts pay out once each**: a recipe taught at three (Aunt Ping's soup, Lan Yue's tea, Tie Niu's broth and
  more) and keepsakes at three or five. A shopkeeper takes 5% off at three hearts and 10% at five. New
  requirement kind `hearts_at_least`; new effect `add_affinity`.
- **Companions**, on the Companions page:
  - A friendly duel from three hearts, at your level (+20 for a win, once a day).
  - **Sworn Siblings** at four hearts, up to three: +3% attack and defence for each one in the party, and the
    Sworn Sibling title.
  - A **Dao Companion** at five hearts, only one. While they are with you, they hold the breakthrough support
    slot (one risk step), share +10% insight and meditate with you (+25% resonance meditation, from the day the
    bond is sworn).
- **Master**: passing the personal-disciple trial makes your sect's elder your master. **The Elder's Last
  Lesson** (a new chapter 10 quest before the farewells) passes on their legacy Inner Art, which is never sold:
  Elder Hu's Lotus Mind (+8% insight, +5% Will) or Elder Sung's Drifting Cloud (+6% move speed, +5% evasion).
- **UI**:
  - A **Gift** page from any gift-taker's dialogue ("Give a gift") and from the Companions page.
  - Hearts beside the speaker's name in dialogue.
  - Companion cards show hearts, a bond tag, and Gift, Duel, Swear and Dao Companion buttons.
  - The Relations page's Bonds tab lists every friend with their hearts.
  - A Codex entry, "Hearts and bonds".
- **Events:** `affinity_changed` and `bond_formed`, with HUD notes. Intents: `give_gift`, `offer_bond` and
  `companion_duel`.
- **Debug flags:** `--companion=id`, `--hearts=npc:n` and `--open-page=gift:npc`.
- **Tests:**
  - loved, liked and courtesy gifts, and once a day;
  - gear and key items refused;
  - Mei Qing's shared hearts;
  - one-time heart rewards and quest affinity;
  - keeper discounts;
  - the duel's heart gate, level and daily reward;
  - sworn and Dao Companion rules and their effects;
  - the master and the legacy.
  The valley run now takes the Last Lesson.

### V8a · The living world: the Relations authority, karma deeds, alignment and Fame (S49)
- **Relations authority** (new, per character). It owns the karma ledger, which moves off the cultivator, and old
  saves carry their merit, sin, debts and eased realms across. Progression, Combat and the tribulation now read the
  ledger from it. `merit_changed`, `sin_changed`, `debt_recorded` and `debt_called` are its events now.
- **karma.json** (new, from `tools/data/relations.py`): every deed with its merit, sin, alignment and Fame.
  - A deed fires three ways: from the `deed` effect (quest rewards, dialogue choices), from code (a patient
    healed), or from a matching event (a back-room purchase, the Beast Tide held, a field lord felled, a spar won
    or lost where a town can see).
  - Flags: once, once per boss, per item bought, and town-only.
  - Part 8 numbers: cleansing a Hollowed village or well is +30 merit (it was +15 and +10), and each patient
    healed is +2. The build's own deeds (the Hollow Night rescues, the tomb, Elder Gu, the ledger) are now named
    deeds.
- **Alignment**: −100 (demonic) to +100 (righteous), named Demonic, Shadowed, Balanced, Upright or Righteous.
  - Deeds lean it.
  - New requirement kinds: `alignment_at_least`, `alignment_at_most`, `merit_at_least` and `fame_at_least`.
  - The Cloud Sect sells Calm Heart Incense only to the upright. Broker Mu keeps Mid Soul Cores and Beast
    Essence Blood under the counter for the shadowed.
  - Data validation keeps these kinds off every realm breakthrough.
- **Personal Fame**: Unknown, Noted, Rising, Renowned, Legendary.
  - Raised by tournaments (qualifier +20, last eight +60, finals +150), great foes, cleansings and the Beast Tide.
  - Losing a spar in a town costs 5.
  - From Noted, townsfolk greet you by name.
  - From Rising, Young Master Luo Heng may be waiting when you walk into a town (once a day). Accept, and he
    spars at your level (+15 Fame for humbling him). Decline, and you lose 5.
- **Relations page** (Character → Relations; also the Heart tab's Ledger button) with four tabs:
  - Karma: merit, sin, the merit step, the alignment scale, recent deeds and named debts.
  - Bonds and Grudges: filled in by V8b and V8c.
  - Fame: the tier ladder and what each tier brings, plus a waiting challenge with Accept and Decline.
- Quest rewards list the merit and Fame a deed gives. There are Codex entries for alignment and Fame.
- **Events:** `alignment_changed`, `fame_changed` and `young_master_challenge`, with HUD notes. Intent:
  `answer_challenge`.
- **Debug flags:** `--deed=id` and `--challenge`.
- **Tests:**
  - old-save migration;
  - once-only deeds;
  - public and private spars;
  - once-per-boss Fame;
  - tier-ups;
  - alignment clamps and gates;
  - per-item black-market sin;
  - the young master's chance, daily limit, decline, accept (at your level) and lapse.

### V7e · Spirit beasts: the Beast Arena, the Trial Grove and the Taming Dao (S46)
- **Beast Arena** (the ladder board on Market Street, and a new page). Ten NPC tamers, from Farmhand Qiao at rank 10
  to Jing Mo at rank 1.
  - Challenge the one above you in 1v1 (your active animal) or 3v3 (three beside you or in the bag), five times a
    day. A win takes their rank.
  - The rank held when the week turns pays out: 30 Spirit Stones and Beast Essence Blood at rank 1, down to 3 Spirit
    Stones at rank 10. Then the ladder starts again.
  - The fights are pet-only auto-battles in the new pure `PetRules.battle`, seeded on their own stream. Level,
    rarity, stage, growth, aptitude, gear, core, wounds, traits, skills and awakened skills all count, and an Equal
    Contract opens with its free cast.
  - The page replays the last fight as draining health bars.
- **Beast Trial Grove** (a door off Market Street). Once a day the animals fight ten beasts (their Level following
  yours). Your own blows do no harm there: they rally the animals (+25 % for 5 s, every 8 s). The first clear gives
  the Guardian Spirit skill book; later clears draw essence blood, marrow pills or skill books.
- **Beast Taming Dao**: six tiers, two in the valley and four in the Azure Expanse.
  - Every tier adds 5 % to taming.
  - Tier 2: eggs hatch 10 % sooner.
  - Tier 3: elites can be tamed (not before).
  - Tier 4: you can teach it to your disciples.
  - Tiers 5–6 (Beast King taming, custom contracts) are named hooks for later ages.
- **Pavilion Feeding Trough**: with a Beast Pavilion, hungry animals are fed once a day from storage, their favourite
  food first.
- **Rename** on the Spirit Animals page.
- **Events:** `arena_battle`, `arena_rewarded`, `beast_trial_result` and `pet_fed` (from the trough), with HUD notes.
  Debug flag: `--arena=solo|trio`.
- **Tests:**
  - battle determinism and the free cast;
  - the ladder, the daily limit and the weekly payout;
  - the Grove's once-a-day limit, rally, kill count and first-clear book;
  - the Dao gates for elites and teaching;
  - the trough's once-a-day feeding.

### V7d · Spirit beasts: the Beast Bag, the Mount slot, Beast Kings and the Beast Tide (S46)
- **Spirit Beast Bags** (key items): Reed 2, Hide 3 and Cloud 4 (Hermit Yao), Mistjade 5 and Starweave 6. Pack animals
  somewhere safe (a town, a sect, a rest stop or home).
  - In the field only carried animals can be called, and never in a fight.
  - A swap puts the old active animal in the new one's bag slot.
- **HUD pet strip** beside the portrait:
  - the active animal with its health arc (tap for the Spirit Animals page);
  - the bag's animals (tap to swap one in);
  - the Mount slot with a Ride / Walk toggle.
- **The Mount slot.** Setting an animal to Mount puts it in its own slot, so a combat animal walks beside you while
  you ride. The `set_mount` intent rides or walks. Thrown off by a heavy blow, the mount follows until you climb
  back on. Saves that rode the active animal move it into the slot.
- **Mount-only species**, with new creature art:
  - The **Riverstone Ox** (walk ×1.5, jump 530, no climbing) grazes Quarry Rim from Cloud Stride 1, paw-marked.
  - The **Cloud Stag** (walk ×1.6, jump 600) hatches from the Cloud Stag egg the Beast Tide gives once from Cloud
    Stride 1.
  - Mount-only animals only take the Mount role.
- **Rarity rolls.** A tamed beast is mostly Common, an elite never is, a plain egg is sometimes Rare, and a Beast
  King's nest egg is Rare or better (on the bloodline stream). Bred eggs keep their parents' rarity.
- **Beast Kings** (`beast_kings.json`): the Riverbed Serpent (valley) and the Thousand-Eye Toad (Azure Expanse).
  - While a King lives, its zone's beasts are 10 % stronger, and paw-marked otters and foxes gather on Bend Shore.
  - When it falls, the buff lifts at once, and its lair's nest holds one Rare Spirit Egg per character for 30
    minutes.
- **The Beast Tide.** Once a real week, ring the gong at Stoneford Gate (from Qi Unfurling 1). Three 30-second waves
  of crabs, boarlets and hounds, their Level following yours between 10 and 45 (the S25 room-event waves, now with
  `until_s` and level offsets). Holding the gate gives three cores of your rank, an egg and Spirit Soil.
- **Events:** `pet_swapped`, `beast_king_spawned`, `king_nest_opened`, `beast_tide_started` and `beast_tide_result`,
  with HUD toasts. Debug flags: `--mount=species` and `--bag=species,species`.
- **Tests:**
  - rarity odds;
  - the egg's species;
  - bag capacity, packing, field calls, swaps and the in-combat block;
  - the Mount slot with a combat animal, mount-only rules, speeds and old-save migration;
  - the King's buff, spawns and nest;
  - the tide's due week, wave levels, wave end and rewards;
  - pets never dying.

### V7c · Spirit beasts: skill books, gear, fusion and breakthroughs (S46)
- **Skill books** (`pet_skill_books.json`). Learned slots open by stage (2 as a Juvenile, 3 as an Adult, 4 from
  Awakened); when they are full a new book overwrites a random slot. Teach from the Growth tab, or use a book from
  the gourd on the active animal.
  - Iron Hide: 10 % less damage (Beast Hall shop).
  - Frenzy: strikes 15 % faster for 6 s after a kill (Big Toad Tan, 35 %).
  - Deep Pockets: one more gourd row while it is active (Beast Hall shop).
  - Herb Whisper: rare herbs within 400 show their ripening time (the new chest on the Falls Pool ledge).
  - Thunder Roar: every 15 s of a fight, foes near it are stunned for 1 s (the Stormwing Hawk elite, 25 %).
  - Guardian Spirit: takes one blow meant for you every 30 s (its book comes with the Beast Trial Grove).
  - Book drops roll on their own stream, so the loot roll is unchanged.
- **Pet gear.** The Bone Collar (+10 % HP), Scale Talisman (+10 % attack, +5 % defence) and Reed Saddle (+10 %
  mount speed) are forged at the anvil. They are enhanced like any gear (+10 % of the base a level) and worn by an
  animal. Equipping one from the gourd puts it on the active animal. Random drops never roll pet gear.
- **Fusion** at the Beast Hall or the Beast Pavilion. Fold one animal into another: a 30 % chance at each of its
  traits and learned skills, and half its purity above the kept one's. It asks for confirmation, locked animals are
  never fused, and the sacrificed animal's gear comes back to the gourd.
- **Pet breakthroughs.** From Awakened on, a stage-up is a breakthrough: a 55 % base, +0.2 % a point of purity,
  and up to three support items (cores of its element +5–20 %, essence blood +15 %), capped at 95 %. A failure costs
  a heart or leaves a Grievous Wound.
- **Pet Core Formation** (Adult to Awakened) grades the core from purity, growth, support and a roll: Cracked,
  Common (+5 %), Fine (+10 %) or Flawless (+18 %) to every stat.
- **Spirit Animals page:** Care and Growth tabs. Growth shows the purity bar with the 50 and 90 marks, growth and
  aptitude, the contract and core, learned-skill chips, gear slots, books and gear to use, the breakthrough with
  support toggles, and a Fuse picker. Icons for the six books and three pieces of gear.
- **Events:** `pet_skill_learned`, `pets_fused`, `pet_core_formed`, `pet_breakthrough` and `pet_gear_changed`.
- **Tests:** slots by stage, overwrite under a fixed seed, every skill's effect, gear and enhancement, the saddle
  rule, fusion (place, lock, confirmation, purity, about 30 % odds over 180 rolls), breakthrough odds, success and
  failure, and the core grade.

### V7b · Spirit beasts: awakenings, contracts, command capacity and incubation (S46)
- **Bloodline awakenings.** At 50 purity an ancestral skill wakes: a heavy strike (×2.5) every 12 s of a fight,
  such as the Ember Fox's Nine-Tail Flame. At 90 the animal takes its true form (the Nine-Tail Fox): +10 % to every
  stat, drawn larger and in its lineage's colour. Every point of purity strengthens revealed traits by 0.2 %.
- **Beast Essence Blood** (Hermit Yao, from Heart Tempering 1): +10 purity for the active animal. It also seals a
  Blood Contract and rerolls an egg's hidden trait.
- **Suppression** reads the S12 Pressure contest (`CombatRules.pressure_loss`). An animal's bloodline tier (rarity
  step plus awakenings) against a wild beast's (rank ÷ 2, +1 elite, +2 boss): when it wins, the beast is gripped by
  Fear once and taming it is 10 % likelier.
- **Contracts.**
  - At 10 hearts an animal offers the one Equal Contract a character ever makes. Resonance flows both ways (it
    resonates at half strength whatever its role, and your meditation feeds it XP) and it casts one free skill a
    fight.
  - A Blood Contract costs a drop of essence blood: +15 % to its stats, but its knockout bruises your soul.
- **Command capacity** tied to Soul: 1 animal, 2 from Spirit Awakening, 3 from Sage. "Beside You" on the Spirit
  Animals page brings more animals along; each fights with its own strength.
- **Incubation input**, once of each kind per egg: drip your own essence blood (+10 purity, −10 % max HP for 24
  real hours), add a beast core to steer its element, or Beast Essence Blood to reroll a hidden trait. Animals
  hatched from an egg you warmed start at 3 hearts.
- **Beast Marrow Washing Pill** (alchemy): rerolls the active animal's weakest aptitude, with no toxicity; it waits
  for a Juvenile. Pet medicines now check they can help before they are spent.
- **Fox Spirit's Favour** joins the fate deck once eggs are open: the next egg hatches with +10 purity.
- **Events:** `bloodline_awakened`, `contract_formed`, `contract_offered`, `pet_skill_cast`, `beast_suppressed`,
  `egg_infused` and `party_changed`, with HUD toasts and notes. Debug flags: `--pet=species[:stage[:purity[:hearts]]]`
  and `--egg=species`.
- **Tests:** purity at 49, 50, 89 and 90; trait strength; the Pressure rule and suppression; skill casts; Equal
  once per character and only at 10 hearts; Blood stats and the soul injury; capacity by realm and the party;
  every incubation input; the Fox fate; and the marrow pill.

### V7a · Spirit beasts: bloodline, beast ranks, cores, wounds and taming by nature (S46)
- **Pet state depth.** Every animal now carries these fields, filled with neutral values on animals from older
  saves: bloodline purity, growth, aptitude, contract, learned skills, gear, a wound flag, knockouts, core grade,
  a colour variant and a lock.
  - A hatch or tame rolls purity by rarity (Common 5–15 … Primordial 60–80), a hidden growth (0.8–1.3) and
    aptitude per stat (0.8–1.2), on their own stream. Growth and aptitude show from Juvenile.
  - 1 % of animals wear a rare colour.
  - Growth × aptitude scale the animal's HP and attack.
  - The Spirit Animals page shows all of this and gains a Lock toggle, a Guard role, a wider detail panel and
    localized role buttons.
- **Beast ranks and natures** (Part 8) in `enemies.json`.
  - Rank 1–9 comes from the Level band (1–9 is rank 1 … 73+ is rank 9), for beasts only. Nameplates read
    "Lv 22 · R3" and the Collection shows rank and nature.
  - Ghosts (Paper Talisman Ghost, Mirror Wisp, Weeping Lantern) and constructs (sentinels, puppets, the Gate
    Guardian) are no longer beasts.
  - Green Viper, Mud Hound and Mist Vulture are demonic; the Hollowed Boarlet and Hollow Stag are Hollowed. All
    five can now be tamed into new species: Green Viper, Mud Hound, Mist Vulture, Cleansed Boarlet, Pale Stag.
- **Taming by nature.**
  - A demonic beast takes only a Purifying Offering (Hermit Yao, from Qi Unfurling 7).
  - A Hollowed one must first be cleansed by one; then any offering tames it.
  - The taming fix: a tameable beast struck down while an offering sits on quick-use is subdued at 1 HP for 10 s
    instead of dying (once).
- **Beast cores.** Beasts of rank 2 and up drop a core at 2 % a rank, on their own stream. Cores come in 28 kinds:
  Low, Mid, High and Peak, in seven elements.
  - A pet devours cores of its own element for XP (60 / 200 / 600 / 1,500).
  - The new Core Exchange at Hermit Yao's Beast Hall buys them for 1 / 3 / 8 / 20 Spirit Stones, up to 60 a day.
  - They also burn as Beast Fire.
- **Grievous Wound.** Three knockouts in five minutes leave an animal at 80 %. It mends by resting at the Beast
  Hall or with a Beast Revival Pill (alchemy, or Hermit Yao). Pets still never die.
- **Events:** `pet_wounded`, `pet_healed`, `core_devoured`, `cores_sold`, `beast_cleansed` and `beast_subdued`,
  with HUD notes. Debug flag: `--pet=species[:stage]`.
- **Tests:**
  - bloodline bands, hidden aptitude, and older-save migration;
  - ranks, natures and core odds by rank;
  - devouring by element, and the Exchange cap;
  - the wound window and its cure;
  - demonic and Hollowed taming, and the subdued fix;
  - data validation for tame species, pet art and cores.

### V6c · Processing racks, sealed herbs and garden raids (S45)
- **Racks** on the drying rack (Batch Work's reward, its text now true): two at a time, ten herbs each, on the
  clock and offline too. A new Racks tab on the Garden page runs them.
  - Steaming (1 h): pills made from the herb carry 30 % less toxicity.
  - Wine-soaking (4 h, a jar of rice wine per five herbs; Stoneford General Store): +10 % potency.
  - The herbs come back marked (a `prep` on the stack). A pill takes the prep of its principal herb when there
    is enough prepared of it. Other herbs are taken plain first, so prepared ones aren't wasted.
- **Sealed herbs.** Old Pan's "hundred-year" ginseng comes sealed, each in its own slot, and 30 % are dyed roots.
  - Appraisal (loupe, Appraisal Eye, or Old Pan and Elder Gu in person) shows which, from the item's new Appraise
    button.
  - An unappraised fake in the furnace spoils the pill (Flawed) 60 % of the time. Sealed stacks are taken last.
- **Garden raids.** Once a reset day, checked when you come back, an unguarded planted bed may be hit (8 %):
  - pests halve its growth, or a thief takes the herb;
  - a mail from the gardener tells you which;
  - a pet on the new Guard duty stays home and keeps them off, as does a Protection or Concealment formation
    burning in the bed's room that day.
- Pill tooltips show the prep and its toxicity; sealed herbs say so.
- **Events:** `rack_started`, `rack_collected`, `garden_raided` and `herb_appraised`, with HUD notes.
- **Tests:**
  - rack timing, the wine cost, and the prep carried into a pill;
  - potency and toxicity by prep;
  - sealed slots, appraisal needing a loupe, and fakes revealed only by appraisal;
  - a fake taken into a craft;
  - raids on an unguarded bed and none under a Protection formation.
- **Moved to V8** (they run on the S49 world calendar): treasure births and gathering trials.

### V6b · The herb garden: beds, Spirit Soil, spring water, transplanting and the Verdant Dew Vial (S45)
- **Garden beds** grow a herb from seed on the clock, offline too. A new Garden page, opened from a bed, shows each
  bed with its herb, age, growth and time left.
  - Grow times: willow moss 2 h, ember pepper 3 h, ginseng 4 h, mist lotus 6 h, orchid and soulbell 8 h.
  - A room's Qi speeds its beds by half its bonus.
  - Harvest gives 2–3 of a young herb (one of an aged one), with a 20 % chance of the seed back.
  - A planted bed shows its herb growing from a seedling in the room.
- **Field grades.** A Low bed grows up to Earth-grade herbs, Mid up to Heaven and High up to Mystic.
  - Spirit Soil raises a bed one grade for good. It drops 1 % from beasts of rank 3 and above (Level 19+), and one
    lies in the Drowned Abbot's vault.
  - The Jade Herb Terraces have 3 Low beds. The Cloud Sect's Array Court gets 3 Low beds and Gardener Ren; before,
    Cloud disciples had no beds and could not finish Seeds of the Valley.
  - Each cave abode has 2 Mid beds.
- **Spring water.** A Qi spring gives three bottles a reset day once the garden is open. A bottle poured on a bed
  gives +25 % growth.
- **Transplanting.** With a Spirit Spade (Stoneford General Store, from Cloud Stride 1) and Expert gathering, a
  rare herb offers Pick it or Dig it up.
  - Dug up, it moves at its age to the first free bed that can hold it, grown.
  - It dies 25 % of the time at Expert, 5 % less per rank above. Either way the node waits for its next ripening.
- **The Verdant Dew Vial** (A Lake Inside, Spirit Awakening 1) fills with a drop a day, offline too, up to three.
  A drop ages a bed's herb one tier, up to 1,000 years in the valley.
- **Seeds of the Valley** now gives three willow moss seeds to plant (text fixed to name the seed sources) and three
  bottles of spring water.
- **Events:** `herb_planted`, `bed_watered`, `bed_enriched`, `herb_aged`, `spring_bottled` and
  `transplant_result`, with HUD notes. A Codex entry covers the garden. Debug flag: `--garden-preview`.
- **Tests:**
  - soil caps the grade, and Spirit Soil lifts it;
  - three bottles a day, and +25 % a watering;
  - offline growth to the minute;
  - the dew accrues offline and is capped at three; it ages a root to 1,000 years and no further;
  - transplant odds by rank, and the survival rate under a fixed seed;
  - data validation for beds;
  - the valley run plants three beds and harvests one.

### V6a · Rare herbs, the harvest tap, seeds and seasons (S45)
- **Herb ages.** Every herb has a family and an age (10, 100 or 1,000 years; `garden.json`). New aged herbs, each
  with raw uses and a gold-haloed icon:
  - Riverreed Ginseng (1,000 yr);
  - Ember Pepper, Mist Lotus, Cloudtop Orchid and Soulbell Flower (100 yr).
- **Aged herbs in recipes.** When the herb a recipe calls for runs short, an older one of its family stands in, and
  the craft's quality score rises 0.04 per age tier. A thousand-year root is never spent while ten-year roots are
  to hand.
- **Rare nodes** (Part 8), on raised tiers only, placed after the verticality pass on named surfaces:
  - hundred-year ginseng at Bend Shore and the Rapids Terraces (Tide Crab guardians; dawn, every 2nd day);
  - the thousand-year root on the Serpent's Shallows high rock (the Riverbed Serpent; midnight, every 5th day;
    Summer);
  - hundred-year lotus at the Falls Pool and Behind the Falls (dusk, every 3rd day);
  - the orchid on the Sky Ledges' top ledge (a Stormwing Hawk; midday, every 3rd day; Spring);
  - soulbells on the Misty Slopes and at the Frozen Shrine (Mirror Wisps; midnight, every 3rd day; Autumn);
  - the pepper in the Thicket Heart canopy (a Thornback Boar; midday, every 2nd day; Summer).
  - The Sky Ledges' second orchid moves up to the east ledge.
- **Ripening.** A rare node is ripe for 20 real minutes around its phase on its day (the in-game day is 48 minutes).
  Picking early gives a herb one tier younger, and a picked node grows back with its next ripening. A ripe node
  shimmers gold, and the room log says when one ripens.
- **Guardians** wake once per ripening, when you climb within reach of a ripe node. To pick it:
  - kill the guardian, lure it past its leash, or pick unseen under Concealment while it hasn't noticed you;
  - for the thousand-year root, the Serpent must be away.
- **The harvest tap.** The 1.5 s hold ends in a ring that shrinks toward the Attack button; tap inside the gold band.
  - The band is 12 % of the ring at Apprentice, then 16, 20, 24 and 28 % at Grandmaster (a new rank cap, from Sage
    Sovereign 1).
  - A perfect tap keeps the full age, gives 1.5× gathering XP and may drop a seed (10 %). A miss drops one age tier,
    never below ten years.
- **Seeds.**
  - Willow Moss, Ember Pepper and Riverreed Ginseng seeds are sold at Granny Liu's and in Greyreed Hamlet.
  - Mist Lotus seeds come only from perfect harvests.
  - Cloudtop Orchid and Soulbell seeds come only from Lu's inheritance (the Riverbreath Trial and the Drowned Abbot).
- **Seasons** (`seasons.json`): Spring, Summer, Autumn and Winter, one real week each, turning with the Monday
  reset. A seasonal node out of season lies dormant. They never gate progression.
- **UI:**
  - the harvest ring;
  - a leaf marker on the minimap with the time left (or until it ripens);
  - a Spirit Sense readout over each rare node in reach;
  - a Seasons tab in the Codex, with the calendar and each herb's rhythm (places shown once visited);
  - Codex entries: Rare herbs, Seasons.
- **Events:** `herb_ripening`, `herb_harvested`, `guardian_spawned` and `seed_found`, with HUD notes. Debug flags:
  `--herb-ripe=<object>` and `--tap-preview`.
- **Tests:**
  - the ripening window by time, and an early pick a tier younger;
  - the guardian once per ripening, lured away, and unseen under Concealment;
  - the tap window per rank, and a miss;
  - the seed rate under a fixed seed, and seasons;
  - aged stand-ins in recipes;
  - data validation for families, seeds and every rare node;
  - a guarded hundred-year harvest in the valley run.

### V5d · Vows, epiphany, Killing Intent, Blood Burning, the false realm and the soul's escape (S48)
- **Vows** (`vows.json`, open at Heart Tempering 1): four oaths, each taken or dropped on a new Cultivation tab.
  - Mercy: no killing blow on a fleeing foe (it gets away with its life); +10 % healing received (a new stat).
  - Plain Fare: no burst pills (Tiger Blood, Sunfire); +10 % Physical Defense and Qi Resistance.
  - Silence: no Presence, so Killing Intent never builds; +10 % Will.
  - Fasting: no food that lends a buff; +5 % accumulation.
  - The bag refuses what a vow forbids. Dropping a vow is breaking it: +15 heart demon.
- **Epiphany.** Contemplation, insight stones, technique use and kills each roll 0.2 % (weighted by Insight) on the
  fortune stream. An epiphany gives 60 s of ×5 insight and a 25 % chance that the most-used technique gains a
  mastery tier for free. Then it rests for two hours of play.
- **Killing Intent.** A kill within 10 s of the last adds a stack (up to 10), +1 % crit each. At 10, weaker
  foes within reach hesitate for half a second. It fades 10 s after the last kill.
- **Blood Burning** (a secret technique taught by Blood Remembers with the Blood Dao): +50 % attack for 10 s. It
  costs 30 % of HP and leaves a body injury.
- **The false realm.** With Concealment, the Techniques page's Secret Arts tab picks a realm to show, up to two
  great realms lower.
  - The HUD badge shows it, marked "(veiled)", and the Character page adds "shown as …".
  - Twenty townsfolk, merchants and wardens speak to the weaker cultivator you show. Elders Hu and Sung, the Grey
    Pilgrim, Elder Zhong and Champion Qiao see through it.
  - **Bandit ambushes.** Once a road's own story is done, its gang's stragglers jump travellers who look weak
    enough: the Mudwater on the Caravan Road, the gorge bandits at the Gorge Mouth, the veiled brigands at the
    Canyon Mouth.
    - The chance is 6 % per entry (never on a first visit or during an event), with a 15-minute rest between
      ambushes.
    - Bandits judge the shown realm and leave alone anyone more than 8 levels past them. A false realm doubles
      the odds.
- **Nascent-soul escape.** From Sage, a grave wound costs 5 % of the stage instead of 10 %: the soul flees to the
  shrine, and the revival page says so. A defeat during a tribulation fails the breakthrough as a Bodily failure.
- **Boss self-detonation.** Comet Captain Rao, cornered below 12 % HP, burns his nascent soul. He is invulnerable
  through a 3 s wind-up with a ring on the ground, then deals 60 % of max HP to anyone inside 280 px and is gone.
- **Fix:** a teacher's lesson (the rare Daos of the Expanse) now opens its Dao at exactly tier 1. Before, a Dao
  Echo fate for another Dao (×0.9) or the 60-second repeat damping could leave it just short, at tier 0.
- **Events:** `vow_taken`, `vow_broken`, `false_realm_changed`, `epiphany`, `soul_escaped`,
  `killing_intent_changed` and `ambush_sprung`, with HUD notes. Debug flag: `--false-realm=<realm>`.
- **Tests:**
  - vow gifts, refusals and the breaking cost;
  - Mercy on a fleeing foe;
  - Killing Intent stacks, crit, decay and Silence;
  - the epiphany buff and cooldown, and Blood Burning's cost;
  - false-realm limits, veiled dialogue and ambush odds, and an ambush spawn;
  - the soul's escape, and the Captain's detonation;
  - a teacher's lesson under Dao Echo.

### V5c · Inner Arts, stances, technique grades and combos (S48)
- **Inner Arts** (`inner_arts.json`, the Part 8 eight) are passive arts, worn in slots: 2 at Qi Unfurling 1, 3 at
  Heart Tempering 1, 4 at Spirit Awakening 1.
  - Riverflow Circulation, Iron Shirt, Swallow's Breath (a new `dodge_cooldown` stat), Stone Root and Clear Lake
    work with any weapon. Sword Heart (Sword Intent to 12) needs a jian and Hunter's Patience needs a bow. Ember
    Channel cuts Fire techniques' cost.
  - Both sect Mission Halls sell a manual for each art, for contribution, from its realm.
  - They have a new Techniques tab, and an art tied to another weapon shows as asleep.
- **Stances** (`stances.json`): one toggle per weapon family, held only with that weapon in hand.
  - Willow Leaf Parry (jian): a parry counters for 200 %, and attacks are 10 % slower.
  - Iron Horse (gauntlets): no knockback, 20 % slower on foot.
  - Coiled Dragon (spear): +15 % reach.
  - Low Shadow (short blade): +10 % crit on a foe's back.
  - Mountain Root (staff): guard +10 %.
  - Still Draw (bow): +15 % damage while standing still.
  - Stances open at Qi Kindling 5.
- **Technique grades.** Every technique is Common, Earth or Heaven (+0 / 10 / 20 % to its base), set by the realm
  that teaches it. The Techniques list shows the grade.
- **Combos** (`combos.json`, Part 8): technique A then B within 1 s.
  - Flowing Palm → Tiger Rush: a shockwave.
  - Cloudpiercing Stroke → Crescent Arc: one more target, 15 % further.
  - Jade Thrust → Dragon Tail Sweep: a pull.
  - Reedcutter Slash → Shadow Flick: a fresh bleed.
  - Riverstone Sweep → Bell Toll Strike: a certain stun, 0.3 s longer.
  - Twin Reed Shot → Pinning Arrow: the root holds 0.5 s longer.
- **Events:** `inner_art_learned`, `inner_art_equipped`, `stance_changed` and `combo_landed`, with HUD notes.
- **Tests:**
  - slot counts, learning and wearing, stat gifts, per-element cost;
  - a weapon-linked art asleep and awake;
  - stance ownership, the gauntlet and jian swap, grades and the combo window;
  - data validation for the new tables.

### V5b · Heavenly tribulation, breakthrough fates and Qi Deviation (S48)
- **Heavenly tribulation.** From Cloud Stride 9 on, every great breakthrough draws a cloud over the room once the
  channel ends. The row for each step is in `tribulations.json`.
  - Bolts: 3 into Spirit Awakening, 6 into Heaven Glimpse and 9 into Sage. After that come waves of 9: 2 into Sage
    Sovereign, and one more wave for each great realm after.
  - Each 25 heart demon and each 100 sin adds a bolt. Debt of Heaven adds 2 to the next tribulation.
  - A ring shows where each bolt will land, one second ahead. Step out of it or guard to take half. Roofs do not
    help. A Lightning Rod Talisman in the bag takes one bolt.
  - Damage is 20 % of max HP × (1 + sin ÷ 500) × (1 + heart demon ÷ 200).
  - A bolt that would kill leaves the body at a tenth of its HP and fails the breakthrough as a Bodily failure.
    Leaving the room fails it as an interruption.
  - Weathering every bolt leads to the usual success roll. The bolt timing comes from the breakthrough stream and
    the ring positions from the combat stream.
  - A HUD panel counts the bolts, and the rings and strikes use the lightning hazard's art in any room.
- **Breakthrough fates** (`fates.json`, the Part 8 deck of 12).
  - After each great breakthrough (past the Prologue), three distinct cards are drawn by weight on the breakthrough
    stream. A picker opens; the offer is saved and can be reopened from the Heart tab.
  - A card can give modifiers for life, costs that last until the next great realm, one-off effects (heart demon,
    pill resistance, stability, purity), or something the next tribulation or breakthrough spends.
  - Wandering Eye reveals a hidden way in each room. Blood Memory adds heart demon for every streak of 10 kills.
    Dao Echo speeds your strongest Dao and slows the rest.
  - Fox Spirit's Favour stays out of the deck until pets have purity (S46).
- **Qi Deviation.** A failure at Severe risk, or on a Poor-compatibility method, applies a ten-minute status. While
  it lasts, every technique takes a random element.
- **HUD.** A heart-demon status icon shows at 25 and more, and the Heart tab's bar turns red when it adds risk.
  Toasts cover the tribulation, fates and Qi Deviation.
- **Fixes.**
  - `ContentDB.config()` now also returns an entries table's own constants. The talisman constants were never read
    before: grade power, quality multiplier and trace tolerance.
  - The hazard layer is in every room.
- **Tests:**
  - bolt counts by realm, heart demon and sin, and the damage formula;
  - a tribulation weathered, and one dodged;
  - a lethal bolt as a Bodily failure;
  - three distinct fate cards, with the same draw for the same seed;
  - each fate's gift, cost, realm expiry and spent `next`;
  - Blood Memory's streak;
  - Qi Deviation only under its conditions;
  - valley checks for the core grade, fates kept and a tribulation stood through.

### V5a · The body ladder, Core Forging, named roots and physiques (S48)
- **The body ladder.** Copper (body level 18), Iron (36), Jade (54) and Gold (72) Body, in `body_tiers.json`. Each
  rung needs three things: the body level, its Temper trial and a full soak in its bath.
  - Temper trials start at a Temper drum. Copper is on Willow Path West: three minutes above half HP. Iron is on the
    Pilgrim Stairs: five Stone Guardians in one run. Jade is on the plum-blossom poles in the Sword Court or East
    Terrace: ninety seconds, never two seconds on the ground. Gold is in the Lightning Scar: three minutes above
    half HP.
  - A trial clears the room's own foes and sends foes at the character's own level.
  - Gifts: Copper gives +5 % Physical Defense, and body techniques (Tiger Rush, Stone Skin, Mountain Shaker) spend
    HP when QI runs short. Iron gives +10 % knockback resistance, Jade heals injuries 1.5 times as fast, and Gold
    is immune to Qi Seal.
  - Iron teaches the Jade Marrow Bath and Jade teaches the Golden Body Bath (both new). A bath beyond the rung you
    have reached still injures the body. That check now reads the rung reached, not the body level.
- **Core Forging.** At Heart Tempering 9 → Cloud Stride 1 the core forms at a purity grade instead of always 9.
  - Five preparation points: a room of the method's element, the method's Yin or Yang hour, full Composure, no
    residue, and a Heavenly Flame Pill within the hour (new; it is refined only over a Heavenly Flame).
  - Each point met counts on an 80 % roll. The grade is 9 minus the points counted, never better than 5. A
    flawless Heaven's Cleansing is one more point, down to 4.
  - The Breakthrough dialog shows the checklist, and methods now lean Yin or Yang.
- **Named roots.** The Aptitude tab names the root once the elements show: Heavenly, True, Mixed, Mutated or Faint.
  It also lists every aptitude as a signed percentage and says when hidden ones appear.
- **Physiques** (`physiques.json`), earned by deeds, each with a drawback:
  - Jade Bone: a flawless Cleansing.
  - Yin Vessel: ten nights of meditation at the Falls Pool.
  - Ember Heart: fifty Fire pills.
  - Stone Marrow: Copper Body before Qi Unfurling 3.
  - Cloud Lung: ten kilometres gliding or flying.
  - Hollow-Touched: its hook is ready for v1.2.
  - The Aptitude tab shows progress toward the ones not yet earned.
- **A Body tab** on the Cultivation page shows the four rungs, what each still needs, and its trial and gift.
- **HUD.** A panel shows any running room event (rites, trials, sieges) with its name, time left and rule. Toasts
  now cover passed and failed trials, rungs, physiques and the core grade.
- **Fixes.**
  - Worn titles now apply their bonuses (none ever did), and the Titles tab shows each bonus.
  - The Still Water title pointed at a stat that does not exist.
  - Modifier text now shows signs, percent stats and elements.
  - Room events that had no display name now have one.
  - The quest tracker no longer touches the taller player panel.
- **State.** CultivatorState version 6 adds `body_tier`, `body_trials`, `body_baths`, `core_grade`, `fates`,
  `physiques`, `vows`, `inner_arts`, `stances`, `false_realm` and `epiphany_cooldown`. Older saves load with
  neutral values.
- **Tests:**
  - a rung needs both the trial and the bath;
  - the HP floor and kill-count trial rules;
  - Gold Body's seal immunity and the HP cost of body techniques;
  - physique gifts, counters and the heart-demon multiplier;
  - root names at the affinity edges;
  - core grade from points, and with a fixed seed;
  - title modifiers;
  - data validation for the new files.

### V4e · Pill tribulation and the Pill Soul's flight (S44)
- **Pill tribulation.** When a Heaven-grade (or better) pill reaches Halo or Soul at the furnace, the heavens test
  it before the pills are yours.
  - Bolts come down in turn: 3 for a Heaven pill, 2 more for each grade above, at most 9. Their timing comes from
    the crafting stream.
  - Each bolt is telegraphed by a ring closing on its strike. *Raise shield* as it lands, within 0.22 s either side.
  - Every bolt held keeps the result, with a 10 % chance to rise a tier. One bolt through drops the batch to Perfect.
- **The Pill Soul's flight.** A Soul pill that comes through flees the furnace. One *Catch* tap as it crosses the
  mark keeps it. A miss settles the batch as Pill Halo; the batch is never lost.
- **Unfinished tribulations.** If the page closes or another craft begins, the tribulation settles as though every
  unanswered bolt struck and the Soul got away. Its pills still come.
- **Who plays it.** Only a live refine from the furnace page plays the tribulation. Auto-refine and other callers
  keep the roll as it is.
- **Events:** `pill_tribulation_result` and `pill_soul_flight`, with HUD toasts. The constants are in
  `forge_upkeep.json` (`tribulation`).
- **Tests:** bolt counts by grade, held and missed outcomes, the Soul's flight and a missed catch, settling an
  abandoned tribulation, and buying a named recipe scroll.

### V4d · The Alchemist Guild, ancient recipes and experiments (S44, Part 8)
- **The Alchemist Guild** (Qi Kindling 8, alongside *Batch Work*). Guildmaster Tang keeps its corner of Stoneford's
  Artisan Row: a stall, the Guild Board, and a new **Guild** tab in Crafts.
- **Exams.** An exam starts with *Light the candle*. It counts pills of the right recipe and quality made before the
  time runs out; a burnt-out candle fails it.

  | Rank | Exam | Rewards |
  |---|---|---|
  | Adept | 5 Healing Pills at Fine or better in 3 minutes | Badge title, the guild shop, the commission board |
  | Expert | 3 Foundation Guard Pills at Superior or better in 5 minutes | Badge title, the Qi Flow Pill recipe, better-paid commissions |

- **The guild shop** sells:
  - the Foundation Guard, Clear Mind and Meridian Reversal recipes;
  - the Jadeiron Furnace blueprint, which is no longer known by default;
  - Mist Lotus and jade scales;
  - for an Expert, the Storm Blood Pill.
- **Mei Qing's Recipe Box** now teaches the Qi Gathering, Bone Strengthening, Viper Antidote and Tiger Blood recipes.
  These recipes, and the guild's, could not be learned anywhere before.
- **Commissions.**
  - Three orders each morning, drawn from the pills you can refine: take the order, deliver it, and choose taels or
    contribution.
  - An order pays 1.2 × the pills' shop price, 1.5 × for an Expert.
  - Daily pay is capped at a fifth of the zone's daily income target: Level × 60 taels an hour for three hours of
    play, from S39's worked example.
- **Ancient recipes** come in torn pages on dungeon shelves:
  - the Method Conversion Pill: 3 pages, in the Mudwater Hideout, the Drowned Shrine and the Forgotten Monastery;
  - the Sovereign Settling Pill: 4 pages, in the Tomb of Sunscar, the Oasis of Bones and the Skyport Wreck.

  A full set teaches the recipe. With pages missing, **Deduce** spends one set of ingredients at 20 % a page, plus
  10 % for each Alchemy Dao tier above the third, never above 95 %.
- **Experiments** (Qi Unfurling 1).
  - At the alchemy furnace, choose 2–4 herbs. A hidden recipe of exactly those herbs is learned:
    - the Sunfire Pill, from ginseng and Ember Pepper;
    - the Stillwater Pill, from Mist Lotus, Soulbell and willow moss;
    - the Cloudstep Pill, from Cloudtop Orchid and willow moss.
  - Anything else makes a Murky Pill, and conflicting herbs blow the furnace.
  - Every mix is logged for the whole account. A mix already tried, in any order, is refused. The log is shown on
    the Codex's Experiments page.
- **Fix:** a shop that sells several recipe scrolls now sells the one you chose. It used to sell the first on the
  shelf; the buy intent now names the recipe (`learn`).
- **Events:** `recipe_page_found`, `recipe_deduced`, `experiment_result`, `guild_exam_started`, `guild_exam_failed`,
  `guild_rank_changed` and `commission_completed`, each with a HUD toast.
- **Tests:** Deduce odds and the 95 % cap, a full set teaching the recipe, the hidden recipe, the Murky Pill and the
  log's refusal, both exams (quality counting, the time limit, rewards), and commission pay and cap.

### V4c · New forms: poison pill, oils, a draught, baths, Qi Flow and incense (S44, Part 8)
- **Qi Flow Pill** (Earth): +20 % accumulation for an hour. When it wears off, the 15 toxicity it held back comes
  due. The recipe is the Alchemist Guild's Expert reward (V4d).
- **Viper Smoke Pill**, a poison pill. Thrown from quick-use, it bursts into a cloud: 4 % of max HP a second for
  5 s to everything within 90. It still bursts where it lands if it hits no one.
- **Weapon oils.** Viper Oil (poison) and Ember Oil (burn) coat the blade for 5 minutes. Each hit has a 20 % chance
  to carry the status. A second oil wipes off the first.
- **Riverreed Draught**, a liquid medicine: +30 % HP and a minor body injury mended.
  - A liquid takes two strikes, with no Condensation.
  - It goes straight to the new **Draught slot**, next to Quick-use on the HUD (key V). The slot shows the count
    and the time left.
  - It goes flat 10 minutes after it is made (`draught_expired`), the one thing in the game that spoils.
- **Medicinal baths** (Qi Unfurling 1).
  - A Bath station (a cedar tub) now stands in the retreat rooms and cave abodes.
  - A bath takes the seclusion slot. Choose *Medicinal bath* on the Seclusion page, or *Bathe* on the bath itself.
  - An hour's soak gives:

    | Bath | Body XP | Residue cleared | Foundation pill share |
    |---|---|---|---|
    | Copper Body Bath | +600 | 10 | 10 points lower |
    | Marrow-Washing Bath | +1,500 | 20 | 10 points lower |

  - A bath beyond your body tier injures the body. Body tiers go by body level: Copper Body from 18, Iron from 36,
    until the S48 trials arrive.
  - The two bath recipes come with the unlock.
- **Calm Heart Incense**: heart demon −10.
- **Murky Pill**: what a failed experiment leaves (V4d). It sells for a tael.
- **Fixes.**
  - A heal over time ("30 % HP over 5 s") now runs in a fight too, and resting no longer multiplies it. Before, a
    Healing Pill used mid-fight gave only its first fifth.
  - Accumulation and insight-rate bonuses are now added flat. A percentage of their zero base used to add nothing,
    so the Clear Mind Pill, Jade Carp Congee, raw Mist Lotus and the Sage-Born title had no effect. Data
    validation now guards this.
- **Tests:** the Qi Flow debt, oil chance and exclusivity, the smoke cloud, the draught's slot, strikes and expiry,
  both baths with the body-tier injury, and the incense.

### V4b · Herb natures, recipe roles and furnace blasts (S44, Part 8)
- **Herb natures.** Every herb is hot, cold or neutral:
  - hot: Riverreed Ginseng, Ember Pepper, Ember Cactus;
  - cold: Mist Lotus, Cloudtop Orchid, Frost Lotus;
  - neutral: Willow Moss, Soulbell Flower.

  Each hot herb in a recipe drives the Extraction band 8 % up the bar, and each cold herb draws it 8 % down. The
  item text says which.
- **The furnace's stages.** The three alchemy strikes are labelled Extraction, Fusion and Condensation. The
  Extraction label says which way the herbs push the band.
- **Recipe roles.** Recipe order gives each slot its role: Principal, Minister, Assistant, Envoy. The recipe card
  shows each slot's role and each herb's nature.
- **Substitutes** (Alchemy Dao tier 5):
  - *Swap* lets one herb stand in for another of the same nature, in a role it can fill;
  - the card marks what stands in for what;
  - the refine intent carries `substitute {from, to}`.
- **Herb conflicts** (`herb_conflicts.json`):
  - the pairs: Ember Pepper with Mist Lotus, Ember Pepper with Cloudtop Orchid, and venom sac with Soulbell Flower;
  - when a pair meets in one batch, the furnace blows: the batch is lost, the furnace loses 10 durability, and a
    minor body injury follows (`furnace_blast`, with a HUD warning);
  - the pair is remembered, and the recipe card warns before it happens again;
  - no authored recipe contains a conflicting pair, and data validation checks that.
- **Tests:** natures, the band shift, roles, substitute rules, a blast from each listed conflict, and the blast's
  cost.

### V4a · Furnaces, Beast Fire rank and the valley's Heavenly Flame (S44, Part 8)
- **Furnaces are equipment.** Each furnace is an item instance worn in the new furnace slot, apart from the eight
  worn slots. The first one you get goes straight into the slot. Choose another from the bag with *Use this
  furnace*.

  | Furnace | Grade | Batch | Heat | Filter | Extra pill | Source |
  |---|---|---|---|---|---|---|
  | Bronze Furnace | Plain | 3 | +0 % | 0 % | 0 % | Mei Qing |
  | Jadeiron Furnace | Earth | 5 | +5 % | 10 % | 5 % | Forge: Jadeiron ×8, Riverstone ×6, crab shell ×4 (Adept) |
  | Cloudsteel Furnace | Heaven | 8 | +8 % | 20 % | 10 % | Forge: Cloudsteel ×8, cloud feather ×4, serpent scale ×4 (Expert) |
  | Mistjade Furnace | Mystic | 10 | +10 % | 30 % | 15 % | Forge: Mystic ore ×6, roc feather ×4, vulture plume ×4 (Master) |
  | Nine-Dragon Cauldron | Heaven | 8 | +12 % | 20 % | 10 % | The Drowned Abbot's sealed vault (Spirit Awakening 3) |

- **What a furnace does.**
  - Enhancing a furnace at the forge steadies its heat, +1 % a level.
  - The impurity filter takes out its share of what each strike missed.
  - A furnace of the pill's own element adds 5 % to the quality roll. The Nine-Dragon Cauldron is Water, and every
    alchemy recipe now has an element.
  - Only the Nine-Dragon Cauldron reaches Grain, Halo and Soul on any fire.
- **Durability.**
  - A furnace has durability. At 0 it is cracked and refines nothing.
  - Mend it in the forge's Enhance mode, for its grade's metal: two for each 10 durability lost.
- **Old saves.** Furnaces in the key-item pouch become furnace instances, and the best one goes into the slot.
  The Earth-Vein Furnace, Cloud-Pattern Furnace and Mystic Tripod become the Jadeiron, Cloudsteel and Mistjade
  Furnaces.
- **Beast Fire** burns a beast core of rank 2 or more:
  - rank 2: Serpent Core and Guardian Stone;
  - rank 3: Jade Core;
  - a Pebble Core is rank 1, too weak.
- **Heavenly Flames.**
  - The valley's flame is now the **Mist Lantern Flame**, carried by the elite Weeping Lantern of the Forgotten
    Monastery and dropped the first time you defeat it.
  - The Cold Lamp Flame moves to the Thousand-Eye Toad under Mirrorwater Lake.
  - Alchemist Fen no longer hands over the Nine-Dragon Cauldron. She points you to the Abbot's vault instead.
- **Pages open faster.** Page scripts load in the background from the title screen, so the first time a page opens
  it no longer stalls (the slowest page went from about 130 ms to about 35 ms).
- **Tests.**
  - The furnace slot, swapping furnaces, batch refusal, enhancement heat, the filter and affinity arithmetic,
    cracked furnaces and their mend cost, Beast Fire rank, old-save migration and the flame source.
  - The valley run opens the vault at Spirit Awakening 3 and sets the Nine-Dragon Cauldron.

### V3c · Talisman craft and Shattered Relics (S47)
- **Talisman craft** (Qi Kindling 6). Old Scribe Bai in Artisan Row teaches it through the guided quest
  *Ink and Paper*. He opens the Talismans page, a tab of the crafting table.
- **Tracing.**
  - Each talisman has a stroke path. Trace it in one motion on the canvas.
  - Staying near the path and keeping an unhurried pace (0.6 to 5 s) set the quality, Flawed to Perfect.
  - Straying too far breaks the stroke and spoils one sheet of paper; the ink is kept.
  - Inks and spirit paper are made without tracing.
- **Talismans.** They work at the talisman's own grade and quality, never from the user's stats.
  - Attack: Flame (180% fire in a burst) and Thunder (240% thunder, with Shock).
  - Defence: Iron Wall, a shield of 20% max HP for 6 s.
  - Movement: Wind Step, one free dodge within 60 s, even on cooldown.
  - Concealment: Veil, which hides you from foes for 10 s.
  - Sealing: Binding, which roots the nearest foe. Bosses are Steadfast.
  - The Revival and Lightning Rod talismans move here from Formations.
- **Materials.**
  - Talisman paper and spirit paper (paper and Mist Lotus).
  - Cinnabar, sold at Stoneford's general store.
  - Beast-blood ink, from hound fangs and rat tails.
- **Data.** `talismans.json` holds base power by grade, quality multipliers, the stroke paths and the trace
  tolerances. Events: `talisman_crafted` (spoiled or not) and `talisman_used`.
- **Shattered Relics.**
  - The Drowned Abbot's first defeat leaves the Shattered Moon Blade.
  - An Expert smith at a forge restores it into the Moonlit Blade, a Heaven relic whose spirit still sleeps.
    It costs 6 Cloudsteel, 6 Refining Essence and 3000 taels.
  - The Restore button is on the shard's item details. Event: `relic_restored`.
- **Tests.**
  - `talisman_suite`: spoiled strokes, stroke quality, grade-fixed damage whatever your Qi attack, Iron Wall,
    Wind Step on cooldown, Binding, and the relic's gates.
  - The valley run writes the first Flame Talisman at Qi Kindling 6.

### V3c · Natal treasure, wardrobe, blood-drop bind and rogue cultivators (S47)
- **Natal treasure** (Heart Tempering 1).
  - Flag one weapon as Natal, in the forge's Natal mode.
  - It grows from kills and technique uses with it in hand, and from ore fed at the forge (20 XP a grade step), to
    natal level 10, +2% stats a level.
  - Its item level follows yours up to the top of the grade band above its own.
  - It breaks only to a boss's telegraphed shatter blow (the Tomb King's glaive sweep, the Hollow Behemoth's
    stampede) or to overcharging, a 5% chance a technique when your Spirit is below its control demand
    (10 + 5 a level).
  - Broken, its stats go dark and a meridian injury follows (a soul injury from Spirit Awakening), until a
    re-forge. A re-forge mends it, or at its cap carries it into the next band with its growth.
  - Item details show its level and item level. Events: `natal_grew` and `natal_broken`.
- **Wardrobe** (Heart Tempering 1): every look you wear joins the account's wardrobe. The Character page's
  Wardrobe tab lets any of them stand in for a slot's own look; stats do not change.
- **Blood-drop bind**: the first time a Plain to Heaven piece is worn, a drop of blood falls on it (`item_blooded`,
  cosmetic).
- **Rogue cultivators**: elites whose visible weapon or treasure is a guaranteed drop.
  - A Rogue Cultivator in the Drowned Grotto carries the Serpent-Tongue Jian.
  - A Rogue Mirror Adept on the Misty Slopes carries a Bright Mirror.
  - Both carry a Sealed Storage Pouch, which Appraisal opens into something from its own table.
- `natal_wardrobe_suite`: growth, the item-level cap, breaking only to shatter, re-forging, the wardrobe,
  blood-drop, rogue drops and the pouch.

### V3b · Flying sword, Sword Intent, dual loadout and self-detonation (S47)
- **Sword Release.** The Sword Dao's third tier teaches it; it goes on the skill arc.
  - The jian leaves your hand for 8 s, or until you use the technique again to call it back.
  - It homes on the nearest foe within 420, 1.5 strikes a second at 60% of the jian's attack. Each strike is a
    flying-sword projectile that stops at walls.
  - Meanwhile your hands fight with Qi palms: the fist combo at ×0.8.
  - While it is out, the sword hangs point-up over your shoulder between strikes.
  - It returns when the time runs out, when you are wounded, or when you lose the jian.
  - Events: `sword_released` and `sword_returned`.
- **Sword Intent.**
  - Consecutive jian hits (combo, techniques and the flying sword) stack up to 10, each +1% penetration.
  - At 10, a weaker foe may falter (a 10% Fear chance).
  - It fades 3 s after the last jian hit, and ten pips along the player panel's foot show it.
  - Event: `sword_intent_changed`.
- **Dual loadout** (Heart Tempering 1).
  - A second weapon waits in the spare slot: "Set as spare" in the bag.
  - The Swap button (R) trades it for the weapon in hand.
  - Each weapon keeps its own technique bar, and a swap never touches a Dao tier.
  - Event: `loadout_swapped`.
- **Self-detonation.** A spare artifact (an unworn piece of equipment, or a treasure) bursts around you for
  1.5 + 0.75 × grade × Qi attack within 180. It is destroyed, which is the one thing the game ever destroys, and
  only after you confirm. Event: `artifact_detonated`.
- `sword_loadout_suite`: the Dao teaches the art; the sword strikes, the palms stay active and the sword returns;
  Intent stacks and fades; the swap keeps each bar; detonation asks first.

### V3a · Gear upkeep at the forge (S47)
- **Enhancement pity.**
  - An enhancement from +5 upward can fail, and it never breaks the piece or takes a level.
  - Each failure adds 5% to the next try on that piece. The piece keeps its pity and shows it in its details;
    a success clears it.
  - The roll uses the affix stream.
- **Refining Essence** (a new material, from Salvage) steadies a try: +2.5% each, up to four.
- **Salvage** breaks any number of pieces into their grade's metal and Refining Essence (`salvage.json`:
  Plain copper; Common Riverstone and 1 essence; Earth Jadeiron and 3; Heaven Cloudsteel and 6; Mystic ore and 10;
  Spirit and Sage in their zone metals). Worn, bound and locked pieces are never salvaged. The intent is
  `salvage {items[]}`, and it emits `items_salvaged`.
- **Inherit** moves a piece's enhancement, less two levels, onto another piece for the same slot, for 2 Spirit
  Stones a level moved (`enhancement_inherited`).
- **Reroll and affix lock.**
  - A reroll rolls a piece's affixes again, and you choose to keep the old roll or take the new one.
  - Locking one affix keeps it through the reroll, and the reroll then costs double.
- **Forge modes** on the Crafts page: Recipes, Enhance, Inherit, Salvage and Reroll. Each shows the chance, pity,
  costs and returns before you commit.
- Enhancement uses each grade's own metal from `salvage.json`, so Spirit and Sage gear now eat Stormsteel and
  Sunglass instead of copper.
- `forge_upkeep_suite`: pity builds and resets, Inherit moves N − 2 in one slot, Salvage skips locked pieces, and
  a locked affix survives a reroll that costs double.

### V2d · The room verticality catalogue, room lint and Paths Above (S43 rules 14–15)
- **Every valley room is built to its v2 catalogue row** (tools/data/catalogue.py):
  - **Lotus Ferry:**
    - lofts sealed until The Runaway Kite;
    - Aunt Ping's lost ladle (a new quest) on a roof;
    - Home Lane's crates and well;
    - the roof chain and the watchtower;
    - the docks' boat deck and mast lookout;
    - stilt decks and drifting rafts in the Reed Shallows.
  - **Willow Path and Stoneford:**
    - willow branches and a later pine top;
    - Market Street's awnings and bell tower;
    - Artisan Row's scaffolds and chimney (the Tinkerer's Gear, a new item);
    - Stoneford Gate's walltop;
    - the Entry Trials rebuilt: Jade climbs roofs over moving planks, Cloud climbs ropes past a crumbling ledge.
  - **The sects:**
    - the Sword Court's plum-blossom poles and a Wall-Step pillar pair;
    - Elder Sung's rope bridge between peaks;
    - library floors at 120 and 240, sealed by rank.
  - **Fields and dungeons:**
    - scaffolds and a crane lift at the quarry;
    - a cracked slab in the Lower Pit that a Plunge breaks;
    - rafts, a moored chest and a lily-pad bounce in the Grey Pools;
    - sprint gaps and a Wall-Step pillar on the Sunken Causeway;
    - bamboo tiers and a bent-bamboo bounce;
    - rope bridges on Caravan Road and at the Gorge Mouth;
    - the Boss Den's wine shelves and the Abbot's bell ledges;
    - a Wall-Step shaft behind the falls.
- **Verticality pass for every other room** (tools/data/verticality.py):
  - standard heights and landings;
  - a raised route across 40% of wide rooms, with rope bridges where roofs are too far apart;
  - a second tier where a room has only one;
  - later ledges for a named art;
  - two ways up each tier;
  - loot lifted onto tiers.
- **Room lint and reach contract** (tools/data/room_lint.py) runs first in `tools/run_tests.sh`. All 122 rooms pass.
- **Paths Above:**
  - Every later ledge is a row in `paths_above.json` and in a new Codex tab.
  - Standing on one records it (`path_above_found`, with a toast).
  - The World map shows a faint wind glyph where your arts now open a ledge you have not stood on.
- **New kit art:**
  - rope bridges, a walltop, chimneys and stone pillars;
  - bamboo slat platforms, scaffolds and stilt decks, awnings, a causeway slab and a cracked slab;
  - log, rubble, lily-pad and bent-bamboo blocks.
- Monsters that live on tiers now also start on branches, canopies, stilts, scaffolds and causeways.

### V2c · Camera, heights in a fight, monster navigation and allies (S43 rules 10–13)
- **Camera.**
  - Rooms may set camera bounds and look-ahead.
  - The camera leads by a quarter of the velocity and follows the surface underfoot instead of the jump arc,
    settling in 0.4 s after a landing.
  - It follows falls of more than a tier and looks down 60 near a high edge.
  - The vertical range opens to 180 so high tiers stay in view.
- **Heights in a fight.**
  - Blows reach −30 to +60 of the attacker's height, and Qi and Soul techniques −10 to +80: from the ground
    you cannot hit someone on an 88 roof, only mid-jump.
  - Flyers hover at about 48 so grounded fighters can still reach them.
  - Every shot stops at blocks and building walls and passes platform decks.
- **Monsters move through vertical rooms.**
  - Each species has `movement {jump, climb, fly, drop}`. Each room builds a deterministic navigation graph
    of walk, jump, drop and climb edges, and melee monsters hop along it after their target.
  - A monster that cannot reach you waits beneath you. After 2 s it takes half damage from you, and after 6 s
    it goes home, healing 10 % a second.
  - Flyers sink toward the height they hunt at.
  - Archers, imps, frogs, toads and vultures start on raised tiers in five rooms.
- **Allies** walk on surfaces and follow along the graph. More than 480 away, or unable to reach you for 2 s,
  they blink to you in a puff of mist.
- **Landing ring** under an airborne player within 200 of the surface below. The minimap shows blocks,
  climbables and movers. Enemy shadows fall on the surface under them.
- **Tests:**
  - the melee and Qi bands, and shots against blocks and decks;
  - graph edges by species, a graph identical on two builds, and chained paths;
  - a bandit chasing up a ledge, a tortoise hitting the out-of-reach rule, and allies blinking after 2 s and
    past 480.

### V2b · Movement arts, volumes and movers (S43)
- **Four new movement arts**, each taught by a guided quest when the quest is accepted:
  - **Plunge** (*Outer Trial*, Bone Forging 4): Down + Attack in the air drops at 900. The landing strikes
    within 60 for 120 % damage and a 0.5 s stun, breaks jars and cracked floors, and has a 4 s cooldown.
  - **Falling Leaf Glide** (*Leaf on the Wind*, Falls Pool, Qi Kindling 3): hold Jump while falling. The fall
    is capped at 120 a second and drift is 10 % faster, for 2 QI a second. The Falls Pool gains a vine, a
    200 ledge and the waterfall's updraft.
  - **Swallow Dart** (*Swallow Dart*, the library's first floor, Qi Kindling 7): tap Evade in the air to dart
    140 while holding your height for 0.25 s, once per airtime, on the dodge's cooldown.
  - **Water Skimming** (the hermit's side quest *Skipping Stones*, Qi Unfurling 8): sprint across deep water.
    The pond under the hermit's stilts has a rock with a Mist Lotus on it and a raft that poles across.
- **Flight by holding Jump.** Hold Jump as you start to fall to take off. Flight replaces the glide where it
  is allowed and QI is above 10 %. In the air, hold Jump to rise, hold Evade to descend, and tap Evade to
  dash. Flight is refused indoors, on sect grounds, in dungeons and in `no_flight` volumes. The third-press
  take-off is gone.
- **Volumes** in room data:
  - shallow water: ×0.7, no sprint or dodge;
  - deep water: sink in 1 s and return to the last safe spot, or swim 30 s with Breath Control;
  - current, updraft, wind (a 4 s pulse, stronger at edges), bounce (700) and crumble (0.8 s, back after 5 s);
  - rising water keyed to events, hazard and no_flight.

  They are placed in the Flooded Gate (current), Falls Pool and Cliff Faces (updrafts), Windswept Ridge
  (wind), the Fairground (a bounce drum) and the Mudwater Tunnels (rotten boards). In the Serpent's
  Shallows the Riverbed Serpent floods the arena to 30 for 14 s at half health.
- **Movers.** A surface or block follows a path as a pure function of the room clock, in loop, pingpong or
  trigger mode, and carries its riders. The hermit's raft is the first.
- **Controls and feedback:**
  - techniques and attacks wait while climbing;
  - the climb-speed stat now counts;
  - a fall fades the screen briefly;
  - no safe spot is recorded in deep water, on a mover or on a crumbling floor.
- **Learning an art** shows a toast with its name and a one-line how-to. Each of the five arts has its own
  icon.
- **Data.** `data/movement.json` holds every traversal number, and data validation checks the solver
  against it. Every movement art in `secret_arts.json` names its `movement_art`, how-to and quest. The new
  events are `mover_boarded`, `volume_entered` and `volume_left`.
- **Tests.** The solver is tested at each art's numbers:
  - the glide lasts 1.5 s and covers about 300;
  - the dart covers 140 with no height lost;
  - a Plunge breaks a cracked floor.

  Every volume behaves as its table row says, movers replay identically, and rising water follows its
  event. Game-level tests cover the Plunge blow and stun, glide QI, the air dash and flight on sect grounds.
  The valley run plays the four new quests.

### V2a · Traversal engine (S43)
- **Surfaces have sides.** Each walk surface records which of its four edges are open. A platform is closed
  at the back (north) and open on the other three; the ground and ramps are closed all round. Walking off an
  open edge starts a fall; a closed edge stops you.
- **Blocks** (crates, walls, rocks, carts) are solid boxes: you walk around them, or jump onto their tops at
  40, 60, 80 or 110. A block is an obstacle and a small platform at once, open on every side.
- **Jump feel.** Coyote time 0.10 s after walking off an edge, and a 0.12 s jump buffer that fires on landing.
- **Cloud Ladder Step** (double jump, impulse 430, about 202 high from the ground) is learned in *Cloud Ladder*,
  a Qi Unfurling 6 guided quest from the librarians. It no longer comes free with the first realm.
- **Wall-Step** is learned in *Between Two Walls*, a Heart Tempering 4 guided quest at the Echo Cliffs. Push
  into a wall and jump to kick off it, up to three kicks per airtime; each kick springs away from the wall. The
  Echo Cliffs now have a shaft of two rock walls 100 apart that climbs to the 300 ledge.
- **Drop-through.** Down + Jump on a platform drops through it.
- **Mantle.** Falling past a ledge lip within 24 of your feet pulls you up onto it.
- **Climbables.** Ladders, ropes, vines and chains are their own objects, not ramps. Hold toward one for 0.3 s
  (or use the context button) to climb; jumping lets go. The Lotus Ferry hall ladder is the first.
- **Air attacks.** A basic attack in the air is a single stronger strike (×1.1) and slows drift less.
- **Falls.** Falling out of a room returns you to the last safe spot (0.3 s standing, at least 24 from an open
  edge) and costs 5 % of max HP, except in towns, the prologue and the Lotus Ferry.
- **Context button** (1165, 500) appears in a fight when a ladder or door is in reach, since Attack takes
  the main button then.
- **Doors** need Up held 0.3 s, so a passing jump no longer walks you through them.
- **Events:** `jumped`, `landed` (with fall height), `wall_kicked`, `art_used`, `climb_started`,
  `climb_finished` and `fell_out`.
- **Standard heights** 100 (one jump), 176 (double jump, two storeys) and 300 (flight only). The room
  catalogue uses them; docs/movement.md has the reach table.
- **Tests.** A traversal suite covers edges, blocks, coyote time, the buffer, the double jump, drop-through,
  mantle, climbing, Wall-Step and falls, and checks that a room's blocks and climbables reach its geometry. The
  valley run now plays *Cloud Ladder*, *A Treasure in Hand* and *Between Two Walls*.

### V1b · Pill rules follow Build Prompt v2 (S44)
- **Lifetime resistance** counts every 5 doses of a family as 1 (`pill_resistance {family: {count, doses}}`); a
  pill works at 1 ÷ (1 + 0.25 × count). Each major breakthrough drops every count by 1 and then halves it. A
  normal ten pills a realm now keeps pills near two-thirds strength, where the gap report's rule left them at 29 %.
- **Families come from data** (`family` on each pill, raw herb and core):
  - accumulation (Qi Gathering; herbs and cores that add Qi);
  - body (Bone Strengthening);
  - insight (Clear Mind);
  - soul (Soul Soothing);
  - support (Foundation Guard, Cleansing).

  Healing, restoration, antidote, purging and conversion pills are exempt. Pill details show what resistance
  leaves of a pill, or that a Pill Grain ignores it.
- **Foundation.** The share is pill QP ÷ total QP since the last major breakthrough, and resets at each major
  breakthrough. Beast cores count as pill QP. *Settle foundation* lowers the share by 5 points an hour and burns
  off 5 residue an hour.
- **Support pills.** After two failed attempts at the same breakthrough (`support_failures`), support pills stop
  lowering its risk.
- **Pill marks** by quality: Fine 1–2, Superior 2–4, Perfect 4–6, Grain 6–7, Halo 8, Soul 9.
- **Pill Halo** grows +1 % a day, to +20 %, while in a storage chest in a room of Qi density 2 or more. It no
  longer grows in the bag during seclusion.
- **Pill Soul** always carries its recipe's own `soul_effect`.
- **Events and saves.**
  - Events: `pill_resistance_changed` and `foundation_changed` are emitted.
  - Saves move to version 5: version 4 resistance, foundation and support-failure data migrate on load.
- **Tests.** `tools/run_tests.sh` now fails a suite that prints a script error. A runtime error used to abort a
  suite part-way and skip its remaining checks silently.

### V1a · Treasures, talismans and throwables follow Build Prompt v2 (S47, Part 8)
Build Prompt v2 folds the gap report into the build prompt and wins where they disagree (docs/v2_audit.md).
G2a's treasures now match its Part 8.
- **Treasures and sources.** Each treasure has a flat QI cost and, from Spirit Awakening 1, a Soul cost of a
  third of that. Their definitions are in `treasures.json`.

  | Treasure | Effect | Cost | Source |
  |---|---|---|---|
  | Practice Bell | stun 0.5 s, radius 100 | 25 s · 15 QI | *A Treasure in Hand*, the new Heart Tempering 1 guided quest from Elder Hu or Elder Sung; it opens Treasure slot 1 |
  | Bronze Bell | stun 1 s + Qi Seal 3 s, radius 150 | 20 s · 30 QI | Drowned Abbot, first clear |
  | Little Pagoda | holds one foe 4 s, an elite first; bosses immune | 30 s · 40 QI | Gu's Warehouse vault |
  | Bright Mirror | returns projectiles 2 s | 18 s · 25 QI | forged from Jadeiron ×6 and pearls ×2 (blueprint at Heart Tempering 1) |
  | Mountain Seal | 250 % Qi Attack, radius 120 | 25 s · 45 QI | Stone Guardian, rare drop |
  | Taming Cauldron | takes a beast below 20 % HP as its fixed materials, no loot roll | 40 s · 30 QI | Hermit Yao's Beast Hall |
  | Wisp Banner | three wisps fight for 10 s | 45 s · 50 QI | Bai Ling's quest line |
  | Sealing Gourd | drinks projectiles for 3 s | 20 s · 30 QI | Old Ma, after Spirit Awakening 1 |

- **Elder Hu's Talisman** (was the Heaven Splitting Talisman). It sits in a Treasure button and holds three
  charges of the Heaven-Splitting Palm (600 % Qi Attack), with no cooldown. Elder Hu gives it when you accept
  the Heart Trial. The button shows the charges left.
- **Throwables are forged:**
  - Iron Needles ×20 from Riverstone and a beetle shell;
  - Flying Knives ×10 from Jadeiron;
  - Thunderclap Pellets ×3 from ore dust, Ember Pepper and a lantern wick.

  The Lightning-Rod Talisman item exists, ready for tribulation.
- **Vessels** set the flight sprite and QI cost only. The speed changes and the Sealing Gourd's heal were
  inventions, and are gone.
- **HUD.** Treasure 1 is at (887, 470) and Treasure 2 at (799, 470), with the Z and X keys. The Pet button moved
  to (965, 560), clear of skill slot 2.
- **Events** use v2's names:
  - `treasure_used` for deployed treasures; the natural-treasure event is now `natural_treasure_used`;
  - `merit_changed`, `sin_changed`, `debt_recorded` and `debt_called`.
  - Effects `add_merit`, `add_sin`, `record_debt` and `add_residue`.
  - The event contract now lists every S43–S49 event the build emits.
- The Wisp Banner is described as formation light, not bound wisps, to stay clear of soul banners.

### G2a · Treasures, throwables, a talisman treasure and flight vessels (gap report priorities 4–5)
- **Two Treasure buttons** left of Guard (R and T on a keyboard). The first opens at Heart Tempering 1
  with the **Stilling Bell** (quest *Lines in the Sand*), the second at Spirit Awakening 1. Set a treasure
  from the bag. Each treasure is one action with a Qi cost and a cooldown, shown as a sweep on the button:
  - **Stilling Bell:** stuns foes within 220 for 1.5 s and seals their Qi for 4 s. Bosses only lose their Qi.
  - **Nine-Storey Pagoda:** a 4 s prison over the nearest foe, never a boss.
  - **Returning Mirror:** for 2 s every missile that reaches you flies back at its thrower.
  - **Mountain Seal:** 250 % attack to everything within 170, with knockback.
  - **Beast-Taking Cauldron:** takes a beast worn below 20 % HP whole, for twice its materials.
  - **Wisp Banner:** three wisps strike the nearest foes each second for 10 s.
  - **Sealing Gourd:** drinks every missile within reach for 3 s, each mending 1 % HP.

  The Mission Halls, Old Pan and the port peddler sell them. The Hollow Behemoth and the Gate Guardian
  drop the Seal and the Banner on their first defeat.
- **Throwables.** Throwing needles (three at once), flying knives (pierce one) and thunderclap pellets (burst
  and knockback) share a 1.2 s cooldown and can sit in quick-use. Needles and knives can be made at the forge.
- **Talisman treasure.** Elder Hu's gift, the **Heaven Splitting Talisman**, holds three charges of a 12,000
  damage cut, at its own power, not yours. The bag shows the charges left.
- **Flight vessels** ride in the key pouch; choose one in the bag:
  - **Flying Sword:** −20 % Qi, +25 % speed (the reward for *Riding the Wind*);
  - **Cloud Puff:** −35 % Qi, −5 % speed (a Mission Hall);
  - **Jade Gourd:** −15 % Qi, +10 % speed (the other Mission Hall);
  - **Maple Leaf:** −25 % Qi (the hermit's).

  Each is drawn under the rider in flight.
- **Fix: shots now strike short creatures.** Arrows, ranged Qi techniques and throwables fly at chest height, and
  their hit band stopped 36 units above the ground, so they passed over 30 of the 75 monsters (crabs, rats,
  frogs, foxes and every creature under 38 tall). The band now reaches the ground; a shot fired from the air
  still passes over them.
- A new temple-bell sound effect. The first treasure carried goes straight into Treasure 1. 36 new rules checks
  drive every treasure, throwable, the talisman and the vessels through the real authorities, plus the arrow
  regression. `--vessel=<id>` with `--fly` previews a vessel.

### G1 · What pills cost, heart demons, karma, fire and furnace (gap report priorities 1–3)
- **Lifetime pill resistance.** Each dose of a pill family (Qi, body, soul or insight) weakens the next:
  1 / (1 + 0.25 × doses). A major breakthrough forgets one dose. A Pill Grain slips past resistance. A support
  pill that has failed the same breakthrough twice stops lowering its risk.
- **Foundation.** Every great realm tracks how much of its Qi came from pills, raw herbs and cores.
  - Above 30 % the foundation is hollow: the next major breakthrough counts it as an unmet soft requirement,
    and a failure is always *Weak foundation*.
  - The new seclusion focus **Settle foundation** makes pill-given Qi your own and burns off residue.
- **Residue.** 5 % of all toxicity stays behind. Each 10 residue costs 1 % accumulation, up to −10 %.
  Purging Pills don't touch it. A **flawless Heaven's Cleansing** (not hit once) washes it all away.
- **Heart-demon meter (0–100).** It is fed by:
  - a changed method (+10);
  - a pill-forced breakthrough with two or more supports (+5);
  - a defeat (+3);
  - sin.

  Each 25 is a risk step at every major breakthrough and one more crimson **Heart Demon**, wearing your face,
  at the Trial of Reflections. Meditation wears it down. Myriad-Year Calm Incense now really clears 40.
- **Karma ledger.**
  - Merit comes from the Hollow Night rescues, resealing the Tomb, freeing Gu, burning the Black Ledger,
    and ten helping quests. 100 merit eases one great breakthrough in each realm.
  - Sin comes from leaving Gu in chains, sending the ledger pages home, and every purchase in Broker Mu's
    back room. Sin feeds the heart demon.
  - Named debts come back as letters. Freed, Gu repays you two days later; the Gu family remembers otherwise.
- **Fire and furnace** (the S15 "rare fire or special furnace", now defined).
  - Fires:
    - Charcoal takes a pill as far as Perfect.
    - Earth Fire, at a vent in Whitewater Gorge and on the Scorpion Flats, reaches Pill Grain.
    - Beast Fire, burning one beast core a batch, also reaches Pill Grain.
    - Heavenly Flames, absorbed for good, reach Halo and Soul. They are the Cold Lamp (Drowned Abbot),
      the Sunscar Throne Ember (Tomb King) and the Comet Tail (Captain Rao), each a Codex collectable.
  - Each fire widens the strike band. The Crafts page has a fire selector.
  - Furnaces are items that set the batch (Bronze 3, Earth-Vein 5, Cloud-Pattern 8, Mystic Tripod 10),
    with band, filter and yield-chance stats. Each is cast around the last at the forge.
    **Alchemist Fen's Nine-Dragon Cauldron** is a named furnace that reaches Soul on any fire.
- **Pill marks.** Every batch rolls 0–9 gold lines by quality, each +2 % effect, drawn on the slot. When a Halo or
  Soul pill forms, a coloured pill cloud boils up and nearby NPCs cry out.
- **Undefined rules settled.**
  - Pills never decay; the Codex says so.
  - Auto-refine teaches 25 % of the XP refining by hand does.
  - Herbs can be eaten raw in need (a third of a pill, twice the toxicity), and beast cores can be absorbed
    for Qi.
- The Cultivation page has a new **Heart** tab: the meter with its steps, merit, sin and debts, the foundation
  share against the hollow line, residue, and each pill family's resistance.
- 38 new rules checks drive every G1 rule through the real authorities.

### Text and button quality pass
- **Type.** Words and page figures are now set in Cormorant Garamond, as the style guide asks: semi-bold for
  text, bold for headers, with lining figures so "Lv 0" no longer reads as "Lv o". Previously every label was
  in the pixel face, drawn aliased at the phone's non-integer scale, which made glyph pixels uneven. Numbers
  over the world (damage, bar values) keep Pixelify Sans, now anti-aliased.
  - `JadeRiverSymbols.ttf` supplies ✓ ↻ ✦ ★, which both faces lack. It is a renamed DejaVu Sans subset,
    licence included.
  - World nameplates sit on a soft ink plate instead of a heavy outline.
- **HD UI kit** (`tools/ui/build_ui_hd.py`). Every frame, button, tab, slot, plaque, pill, toast, tooltip, bar
  and the dialogue paper is rendered as anti-aliased vector art at 3 texels per screen pixel:
  - gradient jade enamel and bevelled gold trim;
  - filigree corners with jade gems;
  - a paper dialogue box with lacquer seals.
  It is drawn through `HdStyleBox`, a nine-slice scaled by ⅓ with mipmapped linear filtering, so it is crisp
  from 1280×720 to 4K. The build checks that no ornament leaves its corner, since a leaking ornament would
  smear when stretched.
- **HUD buttons** are anti-aliased enamel discs with a gold bezel, a gloss arc and a soft gold halo when active.
  Empty technique slots show a faint cloud seal.
- The minimap title fits its header. The dialogue plaque leaves room for the speaker's name. The creator's
  arrows are proper ◀ ▶ buttons.

### Gap report audit (docs/gap_audit.md)
- Every proposal in the Xianxia Systems Gap Report is checked against the build: 2 present, 38 partial,
  71 missing. The game breaks none of the report's "stay out" rules.
- The missing systems are planned in seven phases (G1–G7) that follow the report's priority table.

### World movement pass (docs/movement.md)
- **Something to climb in every room.** An audit found 79 of 121 rooms flat. Now 7 of 122 are, all by design
  (insight rooms, the first hut, the home boat, story trials).
  - Fields, paths and dungeons get a one-jump ledge (110) and a double-jump ledge (220) with a chest on it.
  - Outdoor rooms from level 37 get a cloud bank at 320 that only fliers reach.
  - Towns get timber decks and halls get lofts.
  - Plum-blossom poles stand in the home sect's yard, and the elders' peaks and cave abodes get rock shelves.
- **Standable props.** Crates, barrels, tables, low walls, carts, boulders, sarcophagi and 9 more props in
  the walk strip are now solid blocks with tops, so a jump lands on them.
- **Secret arts that move you.** They were named in the design but never granted. Now:
  - **Wall-Step** (Heart Tempering 4): kick off a wall once in the air.
  - **Wind Blink** (Spirit Awakening 5): an air dodge that blinks 120 units, with a 10 s cooldown.
  - **Breath Control** (Qi Unfurling 3): opens the flooded shaft below the Scripture Well into the new
    **Drowned Grotto** (deep water, air pockets, drowned acolytes, a ledge chest).
  - **Appraisal Eye** (Qi Kindling 6): appraise without the tool.
  - **Lotus Heart Breathing** now does what it says: it heals 10% over 5 s below 30% HP, once a minute.
- New rules tests drive the real solver: one jump lands on 110 and not on 220, a double jump reaches 220,
  the cloud is out of double-jump reach, a crate takes a landing, and Wall-Step works once and only beside a wall.
- The Collection page no longer stalls its first frame (160–220 ms). Creature sheets load within a 12 ms budget
  per frame, and each sheet's drawn bounds are baked into `creature_art.json`.

### Phase E · the Starsea
- **The Shipwrights' Yard** at the west end of the Cloudgate Skydock: Navigator Sun's chart table, Shipwright
  Lao's slipway, an armillary sphere and the first Starsea dock.
- **Star charts and vessels (S16, Sage 3).** Two new crafts on the Crafts page, shown from Sage 3. Sighting
  stones on high places (the Yard, Rimefrost Summit, the Presence Terrace, the Riven Peak) give one star reading
  every ten minutes. Readings and sky ink make a route's chart (40 XP a route). Vessels are built on the slipway: the Cloud Skiff
  (smithing Adept) and the Storm Sloop (smithing and formations Adept, comet iron, half again as fast).
- **Starsea voyages (S18).** At a dock, a vessel and the route's chart set sail into an instanced crossing on
  the vessel's deck. The crossing lasts as long as the vessel takes: pirates board, wind kites dive, and the
  **star wind** strips Qi from anyone whose Spirit cannot hold it in (Starsea survival). The crossing ends in port
  at the far end. Falling overboard abandons it.
- **The Skyport Wreck** (Lv 76–81, Storm Ward 56–60), reached only by sailing: the Broken Pier, the Pirate
  Deck, the Riven Peak and the Starsea Launch (rest, teleport stone), with a wrecked-sky-port backdrop, an open
  Starsea backdrop for the crossing, and a new synthesized Starsea theme.
- Five new foes drawn with the avatar engine: the **Starsea Pirate**, the **Rogue Nine Peaks Disciple**,
  **Comet Captain Rao** and the Trial Hall's **Presences** (tinted phantoms, and the Ninth Presence).
- **Chapter 15, Pirates of the Starsea**:
  - Gu's Ledger: a page of the valley's secrets turns up at the auction.
  - The Skyport Wreck: chart, build, sail, take back the pages, and free Elder Gu or leave him.
  - Sect War: at Sage Sovereign 2, the defence of the Alliance Gate, with waves of pirates and deserters and then the captain. Burn the Black Ledger or send each page home. Afterwards the Alliance war gong calls a new battle every 20 hours, for Spirit Stones, comet iron and storm shards.
- **Chapter 16, The Presence Trial**:
  - Lu's Last Page, on the Riven Peak.
  - The Presence Trial: at Sage Sovereign 3, ninety seconds beneath the eight seats of the Trial Hall. Their Presence presses down, answered by Will; phantoms attack; the Ninth Presence arrives half-way. Passing it holds the key to Will Manifest, which the Expanse's ceiling still locks.
  - Stars Beyond: chart the Lantern Run, and the Launch's ring lights toward the Lantern Star Field (Act III).
- Act II systems from the v1.1 row:
  - **Elder's token** at Sage Sovereign 1: the training sect's token upgrades, the Elder rank follows, and home is a free teleport.
  - **Expanse Outpost**, a sect building from sect level 8: +1 Storm Ward per level for every member, and expeditions to three Expanse regions.
  - **Paired cultivation** from Sage 1: +15% accumulation while a companion sits with you.
  - **Rare Daos from teachers:**
    - Blood (Matriarch Tie);
    - Life and Death (Bone-Reader Xiu);
    - Emotion (Hermit Shuang).
    - Each has four tiers of stat bonuses and grows only after its teacher opens it.
  - The Expanse's own Laws (Fire, Metal, Thunder, Soul) now deepen past their valley caps there.
- Six side stories (The Deserters, Iron from a Comet, Clear Skies over the Peak and the three Dao lessons), three
  guided quests, five NPCs, six codex entries, seven titles and three achievements.
- Fixes: a tinted avatar enemy (a drowned acolyte, a phantom) kept its hit-flash white instead of its colour.
- Tests: two new valley_run sections (ae5, ae6) sail, build, fight the sect war and sit the Presence Trial through
  intents; 18 new rules checks cover docks, charts, vessels, the star wind, the outpost, rare Daos, zone caps and
  the Elder's token; data validation follows Starsea routes when it checks that every room can be reached.

### Phase D · Sunscar
- **The Sunscar Desert** (Lv 73–81, Storm Ward 45–50), south of Ironroot Hold down the desert road from the
  Clan Hearth: the Glass Dunes, the Scorpion Flats and the Worm Sea, a sand ground of wind ripples and desert
  glass, a new desert backdrop and a synthesized desert theme. The **Oasis of Bones** (rest, teleport stone)
  lies among the ribs of a giant beast, with Keeper Meng's stores and Bone-Reader Xiu.
- **The Tomb of Sunscar** (Lv 77, Storm Ward 55): the Sealed Gate, the Hall of Sand Kings, the Mirror Crypt and
  the **Throne of the Tomb King**, a dungeon boss who summons clay guards at 60% and enrages at 30%. Dungeon
  theme, tomb backdrop, statues, mirrors, sarcophagi and the King's throne.
- Four new monsters: the **Sandstorm Scorpion**, the burrowing **Dune Worm**, the **Terracotta Warden** and the
  **Tomb King of Sunscar**.
- Four new hazards: scorching heat (Essence; shrines give shade), sandstorms (Body; they push and blind),
  quicksand (Agility) and spike traps in the tomb (Agility).
- **Chapter 14, Sunscar**: Glass and Bone (follow the Pilgrim's caravan to the oasis), The Sealed Gate (cut the
  key's pieces out of the Dune Worms and read the gate's inscription, Insight 80), Sovereign (break through to
  Sage Sovereign 1) and The Tomb King (Lu's page in the Mirror Crypt, the King, and the sun seal: keep it, or put
  it back in his hand; either way the Grey Pilgrim leaves without it). Side stories: Cactus Water, Glass Teeth and
  Stingers for the Hold.
- **Sage-grade equipment**: sunsteel weapons and sunsilk armour (with the veiled weimao hat), forged from
  Sunglass and scorpion stingers from Sage Sovereign 1, and sold to Ironroot kin. Sunglass ore, Ember Cactus,
  the **Sovereign Settling Pill** (ends a new stage's consolidation), cactus water (+Essence against the heat),
  three titles and the King Sleeps achievement.
- Fixes: a boss's summoning phase now calls its own minions (the Thousand-Eye Toad summoned paper ghosts),
  phases can set the level of what they summon, and a new enrage phase shortens pauses and hardens blows.
  The Canyon Harpy's bleed was twenty times too strong. Act II delivery quests now take the goods they ask for.
  A burrower travelling underground now shows as a moving mound of sand or earth instead of vanishing.
- Tests: a new ae4 section plays chapter 14 end to end, buying Sage-grade gear before the tomb; the fight
  helper clears a boss's adds when they wear the player down.

### Room hazards (S17)
- The hazards rooms have always listed now act: **falling rocks** (Quarry Rim), **Hollow puddles** (Grey
  Pools), **the rapids current** (Rapids Terraces), **fog** (Misty Slopes), **wind gusts** (Windswept Ridge and
  the Gale Canyons), **lightning** (Thunderhorn Plains), **bitter cold** (Rimefrost Heights), and two the
  spec lists that no room used: **thorn thickets** in the Thicket Heart and **poison mist** from gas vents in
  the Mudwater tunnels.
- Each runs a readable cycle: a quiet tell (dust trickling, storm clouds, bubbles, a hiss), a warning with a
  broken amber border and a "!" mark that read without colour, the active blow, then a cooldown. A dodge
  through a strike avoids it; a shrine shelters from the cold; hazards start mid-cooldown, so nothing
  strikes on arrival, and safe rooms have none.
- One attribute answers each (Body for rocks, gusts, currents, cold, thorns and gas; Spirit for fog and the
  Hollow; Essence for lightning). A room asks k x (5 + its top Level); below that the effect falls to
  half as the answer nears, and once it is met pushes and statuses stop (a strike still lands at 35%).
  The room banner and the World map show each hazard with the attribute and value it asks.
- New thorn thicket and gas vent props, and eight synthesized sounds (rumble, rockfall, charge, thunder,
  gust, surge, hiss, frost). A `--hazard=phase[:fraction]` preview flag holds a room's hazards in one state.
- Tests: 19 new rules checks cover the answer formula, the cycle, strikes, dodging, gusts, currents,
  puddles and shelter.

### Phase C · Nine Peaks
- **Nine Peaks**, seat of the Alliance (town, teleport stone), reached by a second sky-ship route from the
  Skydock once the lake's mirror has spoken: the Alliance Gate, the Hall of Nine, the Auction Pavilion and
  the Presence Terrace, where the Alliance champion takes sparring challenges.
- **Alliance or the free road (S20).** "Nine Seats" ends in a choice kept on the character. The Alliance
  gives its token, the Factor's 10% discount and a smaller auction premium; the free road opens Broker
  Mu's back room (black-market lots) and the smallest premium. Envoy Lanshi changes your path once, for
  300 Spirit Stones. Titles for each: Alliance Envoy (+2 Storm Ward) and Free Cultivator (+3% drops).
- **NPC auction house (S21, Sage 1).** Four lots are open at all times, drawn from a pool of thirteen
  rare goods with staggered closing times. Five NPC bidders answer at once up to a limit they keep to
  themselves. A bid above it holds the lot; outbid stones return at once; a won lot arrives by mail.
  The house premium is 10%, 8% for the Alliance and 4% for the free road. A backward clock never closes
  a lot early.
- **Gale Canyons** (Lv 73–78, Storm Ward 35–42): the Canyon Mouth toll, the Kite Winds, the Harpy Roosts
  and the Windbridge (no flight), with the **Wind Kite** (a living swallow kite that throws wind
  blades), the **Canyon Harpy** and the veiled canyon brigands, under new canyon and Nine Peaks backdrops.
- **Ironroot Clan Hold (clans, Sage 2):** Hold Gate, Clan Hearth and Ancestor Hall. "Ironroot Blood"
  is the adoption: the warden's test of root, the Matriarch, and the ancestral tablets. Kin get the clan
  forge at 15% off and the Ironroot Kin title (+4% max HP).
- **Chapter 13, The Nine Peaks**: Nine Seats, The Canyon Toll (who pays the canyon toll in Hollow
  shards?) and Ironroot Blood, plus the guided Going Once at the auction block. Side stories: Silk on
  the Wind and Plumes for the Bellows.
- New materials (kite silk, harpy plume) and the Alliance and Ironroot tokens, with icons.
- Tests: a new ae3 section plays chapter 13 (path choice, factor discount, auction bids through the
  close and mail, the canyon, the clan and the path change); valley checkpoints now keep the run's clock.

### Phase B · Heights and lake
- **Rimefrost Heights** (Lv 67–72, Storm Ward 16–22): Frostpine Climb, the Snow Ape Ledges, Rimefrost
  Summit and the **Hermit's Ice Cave**, a hidden cave only Spirit Sense finds. Frost Lynx and Snow Ape,
  Frost Lotus herb patches, icicle-hung boulders and a snowbound parallax backdrop.
- **Mirrorwater Lake** (Lv 68–75, Storm Ward 22–28), reached by sky-ship from the Skydock: the Reedless
  Shore, the Mirror Shallows with their lotus lanterns, the Sentinel Causeway, the Lake Shrine and
  **Toad's Hollow**, home of the **Thousand-Eye Toad** (field boss, Lv 68). Azure Carp Dragonet and River
  Sentinel; a backdrop where the lake mirrors the floating peaks.
- **Chapter 12, The Grey Pilgrim**: Shards for Sale (a shadowless stranger buying Hollow shards),
  Frost and Silence (Hermit Shuang, a meditation in the ice cave) and The Mirror Remembers (the Lake
  Shrine's mirror shows the stranger and a young Lu; Lu's second journal page). Three side quests:
  Snow for the Cabinet, Clear Skies and A-Lan's Herd.
- New materials (rime fang, snow ape hide, dragonet scale, sentinel core, mirror eye, frost lotus) with
  icons, an ice-shard projectile, and the lake as a fishing spot.

### Phase A · Foundation
- The crossing: after the Gate Guardian falls, the Ascension Gate opens onto **Cloudgate Port**, a sky
  harbour on a floating island (Arrival Terrace, Port Market, Skydock, the Wayfarers' Inn and the
  Condensing Hall). The Expanse is its own zone: ceiling Sage Sovereign 3, Qi density 1.2–2.0,
  Spirit Stones as the everyday currency.
- **Thunderhorn Plains** (Lv 64–69): the Stormgrass Verge, Thunderhorn Flats, the Lightning Scar and the
  Herders' Camp, with two new monsters, the lightning-spitting **Spark Weasel** and the charging
  **Thunderhorn Rhino**, stormsteel ore veins and a thunder insight stone.
- **Storm Ward attunement** (S18): four jades per zone (Thunder, Gale, Rain, Lightning) on a new
  Character › Attunement tab, each raised with Storm Shards (level n costs n shards, up to 15). The total
  is set against what each room asks; under-attuned, you deal less and take more (S18 formula). Safe
  rooms ask nothing; a Storm Blood Pill adds +4 for 30 minutes.
- **Chapter 11**: Through the Gate, A Sky Full of Toll Roads, Storm in the Blood, Horns for the Furnace
  and Sage — the first breakthrough of the Expanse, to Sage 1 in the Condensing Hall (third-grade purity,
  the Sage Condensing Pill, and a land that can hold it).
- Fifteen new NPCs of the port and plains: the Alliance toll warden and factor, a veiled free broker,
  the Condensing Hall's alchemist, sky-ship hands, a stormsteel smith, an apothecary, innkeeper and
  herders. Two new avatar hats: the jade **Guan** crown of Alliance officials and the veiled
  **Weimao**, pose-registered in every action and both facings.
- Spirit-grade (stormsteel/stormsilk) gear in the Alliance Factor's hall, stormsteel forge blueprints
  from Sage 1 (Sage realms may refine Spirit grade), Thunderhorn Stew, the Storm Blood Pill, and five
  Spirit Stone shops. Spirit Stone prices come from tael prices at the exchange rate; loot coins in the
  Expanse pay Spirit Stones.
- A zone-aware World map (one tab per zone you have set foot in; the Expanse as islands in a sea of
  cloud, with each region's Storm Ward need). Teleporting across zones costs five times the fee.
- Art and sound: two new parallax backdrops (the storm plains under a thunder deck, the sky port among
  floating islands), sky-ships, herders' yurts, storm menhirs, the Alliance banner, stormsteel veins,
  Storm Ward jade icons, and two synthesized music loops (Cloudgate Port, the Thunderhorn Plains).
- Tests: the valley run now crosses the gate and plays chapter 11 to Sage 1 (a new ae1 section);
  the contract suite loads and compiles every script.

## 1.0 — The Complete Valley (Act I)

Built on the v0.13 movement and avatar engine, which is kept intact (its 3,660 engine checks pass).

### A game around the engine
- Five-layer architecture: data, state, rules, authorities, presentation. Sixteen authorities own every
  system; presentation only sends intents. Named random streams, a single clock, event queue, unlock
  service and v3 saves with migration from the v0.13 slots.
- The Jade River Valley: 75 rooms across 20 regions, built from data with painted buildings, ladders,
  depth stairs, driftwood platforms, hidden portals, teleport stones and layered parallax backdrops.
- The Prologue in Lotus Ferry: ten short quests, one lesson each, the HUD filling in one element at a
  time, the Hollow Night, and the first breakthrough on Lu's boat. No weapon and no Qi until earned.
- Act I: twelve chapters of main story, a guided quest for every system, side stories for the village,
  the merchants and all four companions, daily sect missions, a tournament, sieges and a finale at the
  Ascension Gate.

### Systems
- Cultivation: 89 realm stages, bottlenecks and breakthrough risk, methods with ceilings (Lu's fragment
  gives way to a sect scripture at no cost), meridians, body training, purity, stability, injuries,
  Daos and technique mastery, offline seclusion (accumulate, temper body, heal, contemplate, refine Qi,
  nourish soul) with caps and no offline breakthroughs.
- Retreat rooms and cave abodes: inner disciples get a door off the East Terrace or Array Court into
  the sect retreat rooms (seclusion up to 16 h, one breakthrough risk step safer); passing the
  mentor's trial opens a personal cave abode behind the elder's pagoda, with dense Qi, a spring,
  a mat and a bed.
- Combat: weapon-family combos, techniques, guard and dodge dash, elements, statuses, readable wind-ups,
  hit-stun, elites, field bosses, dungeon bosses with phases and weaknesses, story bosses (the
  Reflection, Elder Gu who flees with his ledger, the Gate Guardian), revival at shrines or on the spot.
- Crafts: gathering, mining, fishing, cooking, alchemy and the forge (timing mini-game), array plates,
  appraisal, formations, infirmary healing, worker puppets, manual restoration and teaching.
- Pill qualities: every refined pill keeps its quality (Flawed 50% with extra toxicity up to Perfect
  160%). From Heart Tempering 1 a run with every strike perfect may give a Pill Grain (180%, half the
  toxicity), a Pill Halo (200%, grows up to +50% while you sit in seclusion somewhere the Qi is dense)
  or a Pill Soul (220%, sometimes a unique effect). Sect Alchemy Hall furnaces and the Alchemy Dao
  raise the odds; quality pills glow in the bag with a dot, ring or star mark.
- Natural treasures (Spirit Awakening 8, "Treasures of Heaven and Earth"), one job each and never sold:
  the Mindwell Lotus behind Crane Falls (+500 Soul, mends the soul, shields it for an hour; once per
  great realm); the Evergreen Heart Tree, planted in rich earth on the elder's peak, a cave abode or the
  Back Mountain, whose fruit (one per season) revives you where you fell at full health; and the
  Nine-Bough Jade Tree at the Forgotten Monastery, which answers only an Understanding bottleneck with
  three quarters of your strongest Dao's gap to its next tier, once per stage. New props and icons.
- Spirit animal rarity and breeding: rarity (Common to Primordial) now scales an animal's strength and
  health. From Heaven Glimpse 1, with a level 4 Beast Pavilion, two Adults of one family (river, hound,
  burrow, wing) make an egg over a day; the child takes the higher rarity (sometimes one more), mixes
  its parents' traits and may carry a new one. The Spirit Animals page shows eggs with a Hatch button.
- Formations: the Restraint (monsters move 30% slower) and Concealment (monsters do not notice you until
  you strike) blueprints from library floor 3, completing the five valley formations. The blueprint
  list scrolls.
- Story: "The Riverbreath Trial" (Lu's inheritance at the Scripture Well: hold the ring while the drowned
  rise) before the Drowned Abbot, and "Farewells" split from "Beyond the Valley" (follow Lu's map to the
  Frozen Shrine first), matching the chapter list. Nine new side quests give the valley's quieter people
  a thread each (Fisher Wen, Washer Mei, Proprietor Fang, Smith Bao, Auntie Rong, Kai, Su Qing, Trader
  Min and a Wen Zhao rematch): 127 authored quests in all.
- Balance simulator: optional side quests now cost active time (10 minutes each) as well as paying their
  QP share, so adding side content no longer speeds the pacing. Every realm lands within 0.95-1.09 of the
  pacing table; Act I ends at 65.7 h (target 65).
- Emotes: a wheel in the Menu with the six starting emotes (bow, wave, cheer, fist salute, laugh, sit) and
  two earned from achievements (Champion, Beast Call). The avatar holds a pose, leans or bounces, with a
  speech bubble, until you move or act.
- Release checklist (S40): Settings > Data exports every save to one file (the device's Documents folder
  when allowed) and restores an export found on the device, keeping the current saves as backups; the
  engine log (five rotating files) can be exported for bug reports. A Credits screen (title and Settings)
  lists every LPC author and licence in full, the OFL fonts and the engine. Accessibility adds Bright
  flashes, Vibration and Captions for sounds (boss roars, bells, war drums, heavy wind-ups, off-screen
  notices). The notification toggle now switches every category. The Android preset is version 1.0.0.
- Companions, spirit animals (starter choice, taming with offerings, eggs), your own sect (buildings
  that appear as built, disciples, expeditions, defence raids), mail, achievements and titles.
- 27 pages on one shared frame, a HUD that reveals itself, a minimap, dialogue with portraits, shops,
  storage, map and teleports, codex, settings.

### Art and sound
- Mountain, gorge, quarry and cliff rooms walk on painted rocky ground, and the Summit Ridge on snow
  (`tools/art/bake_ground.py`, seamlessly tiling), instead of courtyard paving.
- 42 creature sheets, 45 backdrop layers, 114 scenery props, 12 music tracks and 39 sound effects.
- Human enemies and all NPCs use the layered avatar engine; shirts and trousers now come in ten baked dyes
  (every action and facing), so villagers, elders and sect robes look distinct. Equipment carries its dye.

### Interface pass (from screenshots of a mid-game save)
- Every item has its own icon: new thread-bound method manuals (cover and emblem by element), tied technique
  scrolls, curios (the fake jade reads as glass), spirit wood, puppet core, array plate and the late-realm
  pills. `data_validation` now checks that every item, piece of equipment and technique has an icon.
- Spirit Animals, Codex and Mail open on an entry instead of an empty pane; pets and the bestiary draw the
  creatures themselves (undiscovered ones as silhouettes); companions are drawn with the avatar engine.
- Your Sect shows real build costs; long descriptions are trimmed to fit; bar labels are outlined; the Main
  quest tab says which chapter comes next and what it waits for; the board never lists the same mission twice.

### Systems finished against the spec
- Flight from Cloud Stride 1: jump again at the top of a double jump to ride a cloud; hold Jump to climb and
  Guard to descend. Combat pays the QI each second, no-flight rooms and interiors refuse, landing or an
  empty pool ends it. "Wings of Cloud" now teaches it.
- Mounts (Cloud Stride 1): the Jade Crane, Mist Wolf and Ember Fox can carry you (Mount role, walk ×1.5);
  you stand on the crane's back as it glides; a hard blow throws you off for a while; a flying mount halves
  flight QI from Cloud Stride 5.
- Binding (Spirit Awakening 3): a found relic's power is sealed until bound with a channel that a blow
  breaks; its Artifact Spirit wakes through a soul contest (a failure bruises the soul). The Sleeping Blade
  goes from bare-hand power to its full edge once bound.
- Spirit animals grow: Hatchling, Juvenile and Adult (a branch choice) need level, hearts and your realm
  together; three hidden traits reveal as they grow and change real numbers; Resonance adds to accumulation.
- Zone ceilings and attunement (S18) are announced and applied; alchemy and forge strikes are scored by
  Crafting; lost raids damage a building until you repair it.
- Every event in the catalogue is emitted by the system that owns it. Enemies notice you with a "!", and the
  HUD reports raids, hatched eggs, revealed paths, codex entries, quests ready to hand in and more.

### Accessibility
- Enemy danger badges carry shapes as well as colours (▲ tougher, ▲▲ a realm above, ▽ weaker), next to the
  left-handed HUD and text-size settings.

### Text
- Every line the player reads (about 730 interface strings plus realms, currencies and unlocks) now comes
  from `data/strings/en.json`, ready for translation; a test keeps new text out of the scripts.

### Balance
- A balance simulator (S38) plays the data with the real rules: every realm of Act I lands within 11% of the
  pacing table (Qi Kindling at 4.7 h, Heaven Glimpse at 52 h, the end of the Act at 61 h), and the next gear
  upgrade costs 0.8 h of play at Level 15 and 1.4 h at Level 25.
- Monster kills before the Weapon Hall can no longer drop equipment.
- The weekly mission from the content catalogue, Sect Service: twenty daily missions or one field boss for
  150 contribution. Every other row of the Part 8 catalogue was already in the data.

### Found and fixed by the scripted Act I run
- Event spawns were wiped on room entry; stale companion uids could delete monsters; daily missions
  dropped four of five; the Hideout key, the library methods, the Sleeping Blade and the Siege had no
  source; the Core Disciple rank could not be reached; tools filled the bag; the first technique could
  not be used with a sword; kept quest items stopped counting once used in a recipe.

### Tests
- `data_validation`, `rules_tests` (with same-seed replay and offline checks), `prologue_run` and
  `valley_run` (the whole of Act I) join the engine checks; `tools/run_tests.sh` and `Test.ps1` run all.
