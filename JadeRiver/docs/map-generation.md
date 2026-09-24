# Map engine v0.13

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

For a direct development preview, use Godot user arguments `--preview-world --map-theme=forest --map-seed=7`. New profiles can be previewed the same way; add their names to WorldCatalog.REGIONS to include them in the travel circuit.

## Save and compatibility

Progress includes theme, seed, generator version, surface ID and plane coordinates. Generated snapshots use a matching zone identity. A mismatched layout never restores its old coordinates into another map. Save files retain the existing atomic-write and backup behavior. No NPCs, monsters, loot or extra gameplay buttons are generated.

## Verification

- `tests/map_generation.gd`: 72 seeded maps across all six themes, three deliberately broken layouts and a custom profile (76 cases).
- `tests/generated_runtime.gd`: continuous player traversal from entry through branches/ledges/clouds, descent, real disk saves/reloads, scene transitions, held joystick transfer and legacy migration (127 checks).
- `tests/engine_tests.tscn`: existing movement, collision, equipment, animation, save and input regression checks (1,963).
- `tests/pixel_input.gd`: actual viewport touch/mouse checks (7).
- `tests/generated_visuals.gd`: captures ground, ascent and elevated views for every region into the workspace previews folder.

Run tests with the Godot 4.5.1 executable and `--path game`; use `--script res://tests/<name>.gd` for script runners and `res://tests/engine_tests.tscn` for the scene test. Visual/input runners need a graphics display. Physical Android performance remains a device-testing limitation.
