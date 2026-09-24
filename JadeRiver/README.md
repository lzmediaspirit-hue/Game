# Jade River — clean source

Version 0.13 fixes the difference between visible platform tops and hidden depth coordinates. Descending feet can land on the visible top after reaching its elevation; single/double-jump height limits and solid collisions still apply. Holding up no longer requires guessing the platform's depth. Ordinary roof-edge falls retain physical support checks.

Rooms now connect through visible gates. Cross the complete opening, including the player's trailing side, to travel. Touching a post, retreating, walking beside a gate or reaching the map edge does not trigger travel. The next room places the player safely inside its entrance and retains the held joystick, resources and sprint state.

Version 0.12 uses weapon-specific three-hit combos. Swords perform rising cut → return cut → heavy descending cut; spears, daggers and staves perform straight thrust → low thrust → high lunge; unarmed attacks perform jab → cross → uppercut. Tap once per strike; three quick taps buffer the full combo. Bow shots are unchanged.

All nine attacks have eight registered frames, matching body, hair, clothing, shoes and equipment layers, both facings and all six hair dyes. Shared authoring recipes preserve foot registration, articulate the original poses and keep weapons rigid at their grips. The recipes and reproducible baker are `scripts/combo_rig.gd` and `tests/bake_combos.gd`.

The 0.45-second chain window, jump/equipment-change cancellation, foot-sized platform landing contact and stable sideways branch walking are preserved. Real platform ends and deliberate depth-only exits remain open.
Rear building circulation, bidirectional roof routes, floating platforms above the ground edge and stairs are preserved. See `docs/review-v09.md` for that review.

Open `project.godot` in Godot 4.5.1 and press F5. Create or select a disciple and enter the world. The first import rebuilds generated caches omitted from the ZIP.

## Controls

| Action | Mobile | Desktop |
|---|---|---|
| Move horizontally / in depth | Invisible left joystick | WASD / arrows |
| Sprint | Move left or right for over two seconds | Same |
| Jump / double jump | Tap jump once / twice | Space once / twice |
| Attack / fire equipped bow | Attack button | J |
| Meditate | Meditation button | M |
| Switch four empty skill slots | Swipe slots vertically | Swipe / Tab |
| Save and return to selection | System Back | Esc |

Stopping or reversing horizontal direction resets sprint buildup; depth steering preserves it. Creation previews only idle and offers six hair dyes.

## World and persistence

Six seeded region themes connect through their entrance gates. Ground depth and elevation are separate from jump height. Roofs, balconies, branches and clouds use walkable support masks. Scenery footprints and altitude determine collision; sprite depth handles partial occlusion. Runtime images and original character assets retain their quality.

Three local slots store appearance, equipment and progress. Autosave runs every five seconds and on pause, focus loss, selection return and normal close. Midair saves retain the last supported position. Temporary writes and backup recovery protect saves. There is no cloud save or multiplayer server.

## Architecture

Simulation owns actor state and movement; zone geometry owns support, collision and depth rules. Map generation produces validated data. World nodes bind simulation to presentation, camera and persistence. Initial entry and region travel share world setup. See `docs/architecture.md` and `docs/map-generation.md` for the future multiplayer boundaries.

## Testing and packaging

The mandatory compatibility rules are in `AGENTS.md`. Every future movement starts by redrawing the main unclothed body into the new poses; review that body first, then author matching hair, clothing and equipment. The v0.12 combo baker only rebuilds the existing clips and is not a substitute for that body-first authoring rule. `Validate-Animations.ps1` checks every item, action, facing and dye against registered frame counts; it runs before testing, packaging and `Export-Android.ps1`. Inspect the rendered compatibility galleries; numerical checks cannot certify alignment.

Run `./Test.ps1 -GodotPath <Godot-console-path>` for engine tests. Additional suites in `tests/` run with `--headless --path . --script res://tests/<name>.gd`. Visual/input suites require a display.

Run `./Package.ps1` to build the source ZIP, optionally supplying `-OutputPath`. It refuses overwrites. The user permits packages over 30 MB; include only necessary source, runtime assets, tests, credits and art provenance. Caches, concepts and working documents stay outside the package. No lossy image recompression is applied.

Character attribution: `data/LPC-CREDITS.txt`. Font license: `art/fonts/OFL.txt`.
