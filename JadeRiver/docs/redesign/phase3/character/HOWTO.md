# How to add a layer set to the top-down character

The top-down character (decision 32; decision 37 asks for the full set) is drawn in **layer sets**. Each set is built
on its own into its own files, so several agents can draw sets at once without touching each other's work. This page
says how to add one. The pipeline is in the redesign plan, "As built: Phase 3, third part", and the art rules are in
`docs/redesign/art_bible.md` §13.

## What a set is

| Piece | Where | Who edits it |
|---|---|---|
| The set: its looks, their specs (a few numbers each), their colours | `tools/art/topdown/figure/sets/<set>.py` | the set's agent |
| A generator for a new shape | `tools/art/topdown/figure/kinds/<kind>.py` | the set's agent, when no generator fits |
| Its manifest: items, sections, rects, sheets, the game items that wear each look | `data/topdown/character/<set>.json` | generated; never by hand |
| Its sheets | `art/topdown/character/<cat>_<look>[__<variant>].png` (+ `.import`) | generated; never by hand |
| The index every set shares: actions, facings, z order, the catalogue's signature | `data/topdown/character.json` | generated; the same bytes from every set's build |

Sets today (the full set, decision 37): `body`, `hair`, `shirt`, `pants`, `shoes`, `hat`, `cape`, and one per weapon
family: `weapon_gauntlets`, `weapon_short_blade`, `weapon_jian`, `weapon_spear`, `weapon_staff`, `weapon_heavy_sabre`,
`weapon_fan`, `weapon_brush`, `weapon_flute`, `weapon_bell` and `weapon_bow`. `python3 tools/art/topdown/build_character.py
--list` lists them, with what each draws and what is still pending (nothing).

Generators (`figure/kinds/`): `torso` (shirts, coats, robes), `legs` (trousers), `feet` (shoes, boots), `head` (hats),
`back` (capes), `hands` (gauntlets), `hair`, `blade` (a blade in the hand), `pole` (a pole in the hands), `sabre`,
`fan`, `brush`, `flute`, `bell` and `bow` (slung on the back, drawn in the left hand). `sound` is not a layer: the flute
and the bell ring with it on a blow's hit frame. Each takes a skeleton and a spec and returns solids.
`figure/weapons.py` says how a weapon is held.

## Inputs

- **The look's name, label and side-view sheets:** `data/parts.json`, in the category (`weapon`, `shirt`, ...). The
  side-view sheets it names under `art_v12/` are in `art/`, for example `art/weapon_fan_1_idle_0.png`. Look at them:
  the top-down look must be recognisably the same thing, in the same colours.
- **A weapon family's looks:** `data/weapon_families.json` `appearance`. The build refuses a family set that draws
  anything else.
- **The game items that wear a look:** `data/artifacts.json` (`slot` and `appearance`). The build lists them in the
  set's manifest (`artifacts`).
- **Dyes and hair colours:** `data/parts.json` `_dyes` and `_colors.hair`. Shirts and trousers are baked in every dye
  from `palettes.garment`; hair in every colour.
- **Colours:** the art bible's palette, and the side view's ramps in `figure/palettes.py`. Put a ramp only your set
  uses in your set module (`P.ramp(...)`), not in `palettes.py`, so two sets never edit the same file.

## Adding a weapon family (for example, the fan)

1. **The shape.**
   - A blade or a pole: use `kinds/blade.py` or `kinds/pole.py` with a spec. Extend a generator only by adding an
     optional spec key, so the looks already drawn do not change: their sheets must stay byte-identical.
   - Anything else (a fan's ribs and leaf, a bell on its handle, a flute, a brush's tuft, a bow): write
     `kinds/<family>.py` with `solids(sk, spec) -> list`. Use the primitives in `figure/raster.py` (`sphere`,
     `ellipsoid`, `cone`, `limb`) and the hold in `figure/weapons.py`:
     - `blade_line(sk)` gives the grip, the direction and the flat of a one-handed weapon;
     - `pole_line(sk)` gives a two-handed pole;
     - `stretch` lengthens a weapon along the ground's depth;
     - `band_of(sk, point)` puts each piece behind or in front of the body.

     Give every piece a `band` from `band_of`, a material name and a `part`. A cut's smear is `smear_from` in the
     pose (see `kinds/blade.py`).
2. **The set.** Write `figure/sets/weapon_<family>.py`, after `sets/weapon_jian.py`:
   - `KIND = "weapon_<family>"`, and `FAMILY` set to the family's id in `weapon_families.json`;
   - `items(L)` returns one `Item` per look. Use `items.steel_weapon(...)` for jade steel and gold, or build an
     `Item` with your own `Look` and palette (see `sets/weapon_gauntlets.py`).
3. **Build it:** `python3 tools/art/topdown/build_character.py --only weapon_<family> --check`. It takes about ten
   seconds and builds twice to prove the result is byte-identical. It writes your set's manifest and sheets and the
   shared index; no other set's files change.
4. **Import:** `godot --headless --path . --import`, then commit the new `.png.import` files with the sheets.
5. **Look at every frame.** A number cannot certify alignment (AGENTS.md rule 3).
   - `python3 tools/art/topdown/build_character.py --only weapon_<family> --review` redraws
     `docs/redesign/phase3/character/`, including `03_weapon_<look>.png`: every action in the five drawn facings.
   - `xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tests/topdown_figure_gallery.tscn -- --only=weapon_<family> --out=/tmp/gallery`
     draws it with the game's own compositor: every action in all eight facings, the west three mirrored.
   - Check the combo stages the family plays (`weapon_families.json` `combo`), the hit frames, the smear, the guard,
     the plunge, and the weapon laid down while meditating.
6. **Tests.** Run `data_validation`, which holds the layer contract and the coverage gate, then the full
   `tools/run_tests.sh` (`GODOT=...`), with zero SCRIPT ERROR.
7. **Docs.** Add a CHANGELOG entry, and a line under the plan's "As built" for your batch.

`sets/__init__.py` `FULL_SET` is on and `PENDING` is empty (the bow batch, the last, did it): a look the game's data
can put on a character must now land with its layers, or `data_validation`'s coverage gate fails.

## Adding other looks

- **A garment, hat or cape look** (a new armour piece in `artifacts.json`): add its spec and colours to
  `sets/<slot>.py`. It must be in `parts.json` first, since the side view is the source of truth. If no spec can make
  the shape, add an optional key to its generator (`kinds/torso.py`, `legs.py`, `feet.py`, `head.py`, `back.py`). The
  looks already drawn must stay byte-identical: build the whole set and check that `git status` shows only your new
  sheets.
- **A hair style:** add its pieces to `sets/hair.py` `STYLES`: knots, lumps, ribbons, pins and tails, each placed
  from the head or an earlier piece. `kinds/hair.py` says what each piece takes.
- **A skin tone or face:** `sets/body.py` `SKINS`. The eyes and mouth are stamped by `figure/body.py` `face`. A new
  body variant changes what every other set is cast over, so rebuild every set after it (see below).

## Adding an action (as the bow batch did)

A new action is drawn for every layer. It changes the action catalogue in `figure/actions.py` `CATALOG`, and with it
the index's `catalog` signature. Every set built before it is then **stale**: the game leaves it out and
`data_validation` fails until it is built again.

So an action batch runs on its own, never beside other set batches:

1. **The body first** (AGENTS.md rule 4): write the pose function and the `CATALOG` entry, and look at it on the
   unclothed body in all five facings before any layer. A pose also says where every weapon line points (`W`: the
   blade, the pole, the bow, a family's own keys such as the flute's `note`), so every weapon is drawn in it.
2. **A family's own action** goes in `OWN` (the game plays it only with that family), a new blow in `BLOWS` (the
   flute and the bell ring on its hit frame), and the fan's `open` and `thrown` lists in `sets/weapon_fan.py` say
   whether it opens (or leaves the hand) in it.
3. Replace any stand-in alias in `ALIASES`, and drop it from `STAND_INS` (empty today).
4. Rebuild every set: `python3 tools/art/topdown/build_character.py --check`, about fifteen minutes for 864 frames.
5. Wire the action where the game plays it: a family's step or technique in `tools/data/combat_feel.py` `poses`, a
   move (dash, air, throw, charge, parry, melody) in `MOVES`, then `topdown_player.gd` `sync` and `_strike_pose` and
   `TopdownFigure.resolve(action, family, move)`; a story gesture in `tools/data/scenes.py` (`pose` steps).
6. Look at every frame on every layer: `--review` (`10_actions_<facing>.png`, `11_gestures.png`, the weapon sheets)
   and the gallery.

## Merging

- The generated files are deterministic. Two batches that both rebuild the index write the same bytes, so git merges
  them.
- If git reports a conflict in a generated file (`data/topdown/character*.json`, a sheet), do not merge it by hand.
  Take either side, rebuild your set (`--only <set>`), or rebuild all sets after an action batch, and commit.
- Batches own disjoint files: their set module, their generator, their manifest and their sheets. Shared files
  (`palettes.py`, `weapons.py`, the generators of existing looks, `actions.py`) change only with a reason, in a
  batch of their own or with a rebuild of every set.

## Rules (AGENTS.md)

- The unclothed body is drawn first, and every layer is cast from the same poses of it.
- No layer may be missing an action or a facing. A section that has nothing to draw gets an explicit `hidden` entry
  with its reason; the build writes these.
- Original art, in the art bible's palette. Nearest neighbour, no metadata, byte-identical twice (`--check`).
- Never hand-edit generated files. No model names in files or commits.

## What is left (decision 37)

Nothing: the full set is drawn, and `FULL_SET` is on. The batches, all landed:

| Batch | Sets | Looks | Game items | What it drew |
|---|---|---|---|---|
| heavy_sabre | `weapon_heavy_sabre` | sabre | 10 | the broad dao (`kinds/sabre.py`); its crescent smear |
| fan_and_brush | `weapon_fan`, `weapon_brush` | fan, brush | 10 + 11 | the iron fan, open in the blows (`kinds/fan.py`); the calligraphy brush and its ink stroke (`kinds/brush.py`) |
| flute_and_bell | `weapon_flute`, `weapon_bell` | flute, bell | 10 + 11 | the jade flute and the warden's hand-bell, ringing on their blows (`kinds/flute.py`, `bell.py`, `sound.py`) |
| bow (the action batch) | `weapon_bow`, and every set rebuilt | bow; 18 actions | 10, and NPC qiu_feng | the recurve bow, slung on the back and drawn in the left hand (`kinds/bow.py`); `bow_draw`; the combat moves `charge_hold`, `dash_slash`, `air_strike`, `parry_deflect`; the families' own `two_hand_swing_1`–`3`, `flute_play`, `bell_toll`, `fan_throw`, `brush_write`; the story's `salute`, `kneel`, `point`, `startle` |

`data_validation` prints the coverage on every run ("… of … looks and actions drawn; missing []"). With `FULL_SET` on it
fails for any missing look or action.
