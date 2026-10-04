# Art rules for the top-down game

These requirements apply to every sprite, sheet, tile, prop, effect and animation
added to this game. The game is drawn only in the top-down 3/4 view; the side
view is gone.

## Every piece of art

1. Original artwork only, drawn by the generators under `tools/art/topdown/` and
   `tools/content/`, never painted by hand into a PNG and never derived from
   other games' art. Nearest-neighbor pixel rendering. Every build is
   byte-identical (`--check`).
2. Follow the art bible (`docs/redesign/art_bible.md`): the palette ramps in
   `palette.py`, light from the upper left, its outline rules, the 16 px grid and
   height levels, and the 3/4 view's five drawn facings (S, SE, E, NE, N; the west
   facings mirror).
3. Numerical checks cannot certify visual alignment. Review every piece by eye in
   its review sheets and in the game through the capture registry
   (`tools/dev/capture/`), on its own saves and never the Max Tester save, at
   1280x720 and on the phone-size shots.
4. Keep the APK lean: share identical frames, add no unused assets or caches, and
   report the bytes a batch adds. The user permits the source ZIP to exceed 30 MB
   when needed.

## Creatures and foes (the monster engine)

5. Body first. Every new creature or movement starts from the unclothed body
   (`opts.bare`). Draw it and review its anatomy, feet, joints, timing and every
   facing first; then draw armour, robes, hair and props over the approved body
   frames. Never derive a new pose by deforming a dressed composite or use
   garment art as its base.
6. Every species has a spec in `tools/content/monsters/specs/` and is drawn in
   every action its brain plays, in every facing, base and elite (an elite sheet
   only where a room makes an elite). The tell reads and is its own, the blow lands
   on frame 1, the feet sit on the line, and head-on and tail-on read as the
   creature. A boss has its own silhouette and presence: bulk, posture, a
   signature weapon or prop and a colour accent.
7. Run `python3 tools/content/monsters/build.py --check`, review
   `build.py --review ID` and a `monsters_*` capture set with a live fight in the
   species' own room. `docs/architecture/monster_engine.md` has the steps.

## Tiles, props, decor and effects

8. Follow the art bible's checklist (§11): palette ramps, faces at most 0.65 of
   their top's value with a lip and a contact line, a footprint, origin, `solid`
   and `shadow` for every prop, and an outline except on water. Build sheets with
   their scripts (`build_tiles.py`, `build_decor.py`, `build_traverse.py`). A new
   prop never reuses another prop's name; rename yours instead of replacing theirs.
9. Rooms change only through the room engine's specs
   (`docs/architecture/room_engine.md`); never hand-edit layouts or generated
   `data/*.json`.

## Characters: on hold

10. The character art is waiting for a new style the user will give. Until the
    user says so, do not draw, redraw or extend the player, NPC bodies, hair,
    clothing, weapons, riders or any new player pose (`tools/art/topdown/figure/`,
    `build_character.py`, `art/topdown/character/`). Do not add a wearable item,
    weapon family, hair style or action that would need new character art; if a
    task needs one, stop and ask.
