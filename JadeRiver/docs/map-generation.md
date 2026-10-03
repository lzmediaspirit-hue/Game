# Map engine v0.13

**Status (decision 45):** this is the record of v0.13's side-view map engine. The game no longer opens in a generated
map, and the side view is retiring. Only `tests/map_generation.gd` calls `MapGenerator.generate` today. The game's rooms
are top-down layouts (`docs/redesign_top_down_plan.md`).

The game now opens in a generated village. Pass fully through an entrance gate to travel through village → road → forest → cave → mountain → town and back around. The same joystick touch remains active across transitions. Existing disciples migrate from the old authored map to a safe village entry while retaining appearance, equipment and resources.

## Responsibilities

- `MapGenerator`: deterministic spatial grammar. Reserve the road and ascent, allocate rear building plots, add roof-access balconies, fill legal rear-edge tree/rock plots, then create the elevation route.
- `map_themes.json`: editable profiles for density, building width, ground material, background, ascent kind, trees, rocks and clouds. Copy a profile under another name to add a theme without changing movement code.
- `ZoneLayout`: compile building walls and balcony posts from their actual surfaces. Rendering and collision share dimensions.
- `MapValidator`: reject overlapping plots, blocked spawn/roads, invalid/out-of-bounds surfaces, missing object allocations, disconnected surfaces and unreachable jumps. It simulates ground approaches from spawn and jump connections using the real movement solver.
- `WorldCatalog`: adjacent region identities and stable theme/seed/generator-version keys.
- `World`: create render nodes, restore progress, follow the player vertically and horizontally, and dispatch completed gate crossings.
- `LocalAuthority`, `ActorState`, `MovementSolver`: input-to-state simulation remains separate from art and UI. These are suitable boundaries for a future server; this release does not implement MMO transport or accounts.

## Generation contract

Call `MapGenerator.generate(theme, seed, overrides)` to receive serializable zone data: bounds, spawn, gates, surfaces, solid scenery, plots, reserved road, routes, profile and generation identity. Pass it through `MapValidator.validate`; an empty error list means the specified placement and traversal rules pass. `ZoneLayout.compile` produces collision-ready data consumed by `ZoneGeometry`.

The current map extent is 5400 units, with a 480-unit ground-depth band. Buildings and tree trunks occupy the rear edge. Ground circulation is reserved at y=790–920. Jump height is governed by MovementSolver; platform spacing is validated against it. Buildings use balconies for roof access; tall trees have six climbable levels leading to five cloud platforms. Cave and mountain ascents use rock ledges. Cave profiles omit clouds.

Theme fields: `ground` (earth/moss/slate/stone), `background` (settlement/forest/cave), `ascent_kind` (tree_branch/rock_ledge), `building_count`, `building_width`, `tree_count`, `rock_count`, `climb`, `clouds`. Overrides merge with the selected profile before generation. Invalid capacity requests are reported by the validator rather than silently accepted.

v0.13 previewed a theme with `--preview-world --map-theme=forest --map-seed=7`. Those two flags are gone; `tests/map_generation.gd` generates and validates every profile. A new profile still needs its name in WorldCatalog.REGIONS to join the travel circuit.

## Save and compatibility

Progress includes theme, seed, generator version, surface ID and plane coordinates. Generated snapshots use a matching zone identity. A mismatched layout never restores its old coordinates into another map. Save files retain the existing atomic-write and backup behavior. No NPCs, monsters, loot or extra gameplay buttons are generated.

## Verification

- `tests/map_generation.gd`: 72 seeded maps across all six themes, three deliberately broken layouts and a custom profile (76 cases). No suite runs it; it is one of the side-view scripts in `tests/README.md` ("Other scripts here"):
  `godot --headless --path . -s res://tests/map_generation.gd`, or `tools/dev/audit/run_legacy.py`, which runs them all.
- `engine_tests`, a suite in `tests/suites.txt`: movement, collision, equipment, animation, save and input regression checks.

v0.13's traversal run (`generated_runtime.gd`), its viewport touch checks (`pixel_input.gd`) and its region captures (`generated_visuals.gd`) were deleted in decision 45 (S2). The game's review pictures come from the capture registry, `tools/dev/capture/capture.tscn -- <set>` (`tools/dev/README.md`).

Run everything from `JadeRiver/` with the Godot 4.5.1 executable: `tools/run_tests.sh` runs the gates and every suite of `tests/suites.txt`, and `godot --headless --path . res://tests/<name>.tscn` runs one suite. Physical Android performance remains a device-testing limitation.
