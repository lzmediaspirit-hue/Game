# Tests

`tools/run_tests.sh` (Linux, macOS) and `Test.ps1` (Windows) run the same gates, in the same order (the side view's
animation rules, `Validate-Animations.ps1`, went with it in S12a):
1. the data checks (`tools/data/*.py --check`, including `build_data` and `cues`; `tools/lib/pix.py --check`; the
   monster engine's `tools/content/monsters/build.py --check`; `tools/audio/build_audio.py --check`);
2. the Godot suites listed in `tests/suites.txt`.

Each suite is a scene, `tests/<name>.tscn`, run headless:

```
godot --headless --path . res://tests/<name>.tscn [-- --verbose]
```

## The suite base: `tests/lib/suite.gd`

Every suite extends it (`extends "res://tests/lib/suite.gd"`), puts its body in `_main()` and ends with `end_suite()`.

- **`check(ok, what)`** counts a check. A failure counts too and prints `FAIL: <what>`. With `--verbose`, a suite that
  sets `echo_passes` (the story walks and `tutorials`) also prints `ok: <what>` for each pass.
- **`end_suite()`** prints the summary line the runners read, `<name>: N checks, M failures`. It then quits cleanly:
  - it frees what the suite made (its children, and anything it left under the tree's root);
  - it lets the game's worker tasks finish (a technique picture being painted, the foes' sheet index being read);
  - it removes the run's own folder;
  - it exits 1 on a failure, else 0.

  A worker task left unclaimed used to crash the engine as it quit, after a clean summary.
- **`run_root()`** is the run's own folder, `user://test_runs/<name>_<pid>/`. A suite keeps its saves there, so two
  runs at once never share one: another checkout's run, or another agent's.
- **The Max Tester guard.** In-game tests never use the Max Tester save.
  - A suite will not start in the Max Test build, or with `--max-character` or `--unlock-all`.
  - Until the suite picks a save folder of its own, the saves stand in `run_root() + "boot/"`, never in the player's
    own `user://`, where the Max Tester lives.
  - A suite fails if it ends on the player's saves, or with the Max Tester loaded.
- **Hooks.** `report_failure(what)` and `summary_line()` are overridden by `engine_tests` only: it pushes errors, and
  prints `ENGINE_TESTS: P/N passed`. `stop(code)` quits cleanly without a summary; `valley_run` uses it when it has no
  checkpoint to resume.
- **Timing on a shared machine.**
  - `now_us()` is the game's own clock: the wall clock less the time the main thread waited for a CPU while other
    processes held them all. Linux counts this per thread; elsewhere it is the wall clock.
  - `ask_for_cpu()` and `usual_cpu()` lower and restore the game's niceness, where the system allows it (root on
    Linux). The main thread goes to −10 and its workers to −5: ahead of other processes, the main thread ahead of its
    own painters. Elsewhere they do nothing.
  - Users: `perf_tests`; `rules_tests`, for the technique pictures' budget, the preview and the living world;
    `topdown_tutorial`'s people stream.
  - The technique pictures time their own main-thread budget on the same clock (`TechniquePicture._clock_us`), and
    `rules_tests` reads it over one building.
  - `now_us()` reads a file each call (about 20 µs), so microsecond timings keep the wall clock: the coach's cost in
    `tutorials` is a median of 120.

## One world (S12a)

The side view is gone, and with it decision 41's gate and `tests/lib/off_grid.gd`: every suite plays the grid. Since
every room has its layout, `tools/data/topdown_rooms.py` checks it once for the data (`every_room_laid_out`): a room
of `world.py` without a layout, or a way into one, fails the `topdown_rooms` gate. The suites that drove side-view
rooms drive the grid now:
- `engine_tests`: every look drawn by the top-down figure, the motor's walk, stairs, jumps and solids on a room's grid,
  the HUD's touches over the top-down player, saves and creation;
- `room_sweep`: every room's entries, every way and every context or training object reached by the grid's route, the
  motor walking each leg cell by cell, and every tile-set prop drawn;
- `visibility_suite`: every room's people, things and ways as `TopdownPlaces` builds them;
- `valley_run`, `prologue_run`, `tutorial_order` and `rules_tests`: their bodies stand on the layout's floor
  (`prologue_run.place`, `rules_tests`' `_open_lane` and `_stand_at`), their foes and objects where the layout puts them;
  a HUD with no real player takes `tests/lib/player_stub.gd`, the top-down player's shape;
- `rules_tests`' `side_view_save_suite` loads a save the side view made (`tests/data/side_view_save/`) and plays it on
  the grid.

`tests/lib/building_ways.gd` tells a way into a building from its room's data (a facade, or a door in a roof's front),
for the suites that check doors.

S12c restored on the grid what only the side view had carried (`docs/architecture/topdown_mechanics.md`, "S12c"):
`topdown_traversal`'s parts 40 to 44 play it (the jumps and landings, the six paths above landed on by their arts, falls
out of a room and the Hidden Cave, the volumes and the shallows' dodge, the fame greeting), `cue_tests` the fall's short
fade, `audio_tests` the music let go when the world unmounts mid-scene (its old workaround gone). A thing on a path above stands on a ledge only its
movement art climbs onto: `room_sweep`, `topdown_tutorial` and the chapter suites' walks leave it to that art
(`TopdownRoom.ledge_at`), and `room_sweep` keeps no known stuck leg.

A new suite needs three things:
1. a scene with one `Node` that holds its script;
2. a line in `tests/suites.txt`;
3. a summary line of the form above, which `end_suite()` prints for it.

## The performance gate

`perf_tests` measures milliseconds on a machine it shares with other work, so every figure is taken three ways:
- on the game's own clock (`now_us`), with the main thread's share of a CPU asked for (`ask_for_cpu`);
- at the machine's full speed: a fixed piece of work is timed beside each sample, and samples taken while it ran slow
  are left out;
- as the least of three interleaved rounds.

Samples are left out, never scaled, and the budgets are the gate's own. `techniques.json` is timed first, on memory as
fresh as the boot's. The file's section "measuring on a shared machine" has the details.

## Other scripts here

- **Helpers the suites load:**
  - `places_suite.gd`;
  - `topdown_suite.gd`, `topdown_life_suite.gd` and `topdown_foliage_suite.gd`;
  - `lib/building_ways.gd` and `lib/player_stub.gd`.
- **The gallery** is a scene: `topdown_figure_gallery.tscn` (AGENTS.md rule 3).
- The side view's tests and tools went with it in S12a: the five legacy scripts (`combo_tests`, `landing_matrix`,
  `map_generation`, `movement_v07`, `room_gates`), its review renders (`gauntlet_review`, `combo_visual`,
  `weapon_combo_visual`, `weapon_combo_outlines`, `animation_gallery`), its bakes (`bake_combos`, `bake_equipment`) and
  `draw_model.gd`.
