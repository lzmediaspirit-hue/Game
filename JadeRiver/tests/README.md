# Tests

`tools/run_tests.sh` (Linux, macOS) and `Test.ps1` (Windows) run the same gates, in the same order:
1. the animation rules (`Validate-Animations.ps1`, where PowerShell is installed);
2. the data checks (`tools/data/*.py --check`, including `build_data` and `cues`; `tools/lib/pix.py --check`; the
   monster engine's `tools/content/monsters/build.py --check`; `tools/audio/build_audio.py --check`);
3. the Godot suites listed in `tests/suites.txt`.

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

`tests/lib/off_grid.gd` is for decision 41's gate (the prototype's end). Since R8 and R9, every side-view room has a
top-down layout, so no way leads off the grid. While a suite checks the gate, `stand_off()` stands R9's rooms off it
(`rules_tests`' prototype suite, `topdown_tutorial`'s end of the prototype), and `restore()` puts them back. It does
nothing while a real way off the grid is left.

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
  - `draw_model.gd`;
  - `places_suite.gd`;
  - `topdown_suite.gd`, `topdown_life_suite.gd` and `topdown_foliage_suite.gd`.
- **Side-view tests, run with `godot --headless -s res://tests/<name>.gd`:**
  - `combo_tests`, `landing_matrix`, `map_generation`, `movement_v07` and `room_gates` still pass;
  - they go when the side view is deleted.
- **Review renders that need a window**, run with
  `xvfb-run -a godot --rendering-driver opengl3 --path . -s res://tests/<name>.gd`:
  - `gauntlet_review`, which writes the sheets under `docs/mockups/gauntlets/`;
  - `weapon_combo_visual`;
  - `weapon_combo_outlines`, built on `combo_visual`.

  The galleries are scenes: `animation_gallery.tscn` and `topdown_figure_gallery.tscn` (AGENTS.md rule 3).
- **Art bakes:** `bake_combos.gd` and `bake_equipment.gd`.
