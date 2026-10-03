# The NPC engine (E3)

Audit 45 §6.3, phase 3. A person of the world used to live in four places: a hand dictionary in `story.py`'s `npcs()`,
an object of the side-view room in `world.py`, an anchor in the room's spec, and a work entry with spots written cell by
cell in `topdown_life.py`. Now a person is one `npc(...)` spec, and the engine writes them into every place the game
reads them from. The game reads nothing new.

| File | What it holds |
|---|---|
| `tools/content/npcs/spec.py` | the spec language: `npc()`, `look()`, `place()`, `work()`, `role()` and `staff()`, `extra()`, `DROP`, `ROLE`; its docstring is the format |
| `tools/content/npcs/spots.py` | the work spots named by anchors, resolved on a room's layout |
| `tools/content/npcs/engine.py` | the compile, the channels the hosts read, the checks and the command line |
| `tools/content/npcs/tests.py` | the engine's own tests (`engine.py --check` runs them) |
| `tools/content/npcs/specs/<zone>.py` | the people, one module a zone, each listing its `NPCS` and its `EXTRAS`; `specs/__init__.py` lists the zones |

```
python3 tools/content/npcs/engine.py --check       # the engine's gate (tools/run_tests.sh and Test.ps1: npc_engine)
python3 tools/content/npcs/engine.py --list        # every person, their places and their work
python3 tools/content/npcs/engine.py --show ID     # one person: the row, the places, the spots resolved
```

## What a spec writes

| What | Where it goes | Host |
|---|---|---|
| the row: name, title, look, lines, barks, services, dialogue tree, keys, the lines to a hidden realm | `data/npcs.json` | `story.py` `npcs()` takes `rows()`, places its one-off rows among them, and adds the hearts and gifts (`relations.py`) and a lost art's tree |
| the work at each place | `data/topdown/life.json` `work` | `topdown_life.py` takes `work()`, resolves the anchored spots on the built layout, and checks every spot and leg |
| a figure at work with no part in the story | `life.json` `extras` | `topdown_life.py` takes `extras()` |
| the look | the row's `outfit`, an extra's `outfit` | (the character pipeline's parts and dyes) |
| a placement the engine makes itself (`anchor=`) | the side-view room's object, `data/rooms/<room>.json` | `world.py`'s `npc_engine_pass()` takes `objects(room)`, before the passes over rooms |
| ...and its cell on the grid | `data/topdown/<room>.json` `place` | the room engine takes `anchors(room)` after the room spec's own anchors |

A room's own people (their objects written in `world.py` with the story's conditions, their cells among the room spec's
anchors) are named by their room and object: the spec checks they are there.

## A spec

A person new to the grid, Washer Ying of Greyreed Hamlet (`specs/valley_roads.py`), five lines:

```python
HOME_AGAIN = dict(visible_if=all_of(qdone("cleansing_the_well")))

npc("washer_ying", "Washer Ying", "Greyreed villager", look("ponytail", "cardigan:rose", "straight:grey", "slippers"),
    ["The pools took the grey downstream. The washing comes out white again.",
     "Elder Gao wept when the well ran clear. Don't tell him I told you."], ["Scrub, scrub.", "White as a heron."],
    at=[place("gh_hamlet_square", anchor="commons@9", facing=1, **HOME_AGAIN,
              work=work("laundry", "water_edge:wash", "by:laundry_line:hang"))])
```

It writes her `npcs.json` row; her object in the side-view hamlet (at the anchor's column on the ground line, facing
east, shown once Cleansing the Well is done); her cell in the top-down hamlet (the room engine resolves `commons@9` to
(9, 19)); and her laundry loop in `life.json`, its spots found on the layout: the wash at the bank south of her, facing
the water, `[9, 21, "s", "wash"]`; the hanging at the laundry line north of her, `[9, 18, "n", "hang"]`.

A person who already had a place keeps it pinned, Washer Mei of Lotus Ferry (`specs/lotus_ferry.py`):

```python
npc("washer_mei", "Washer Mei", "Villager", look("ponytail:2", "cardigan:white", "straight", "slippers"),
    ["Aunt Ping says you're finally awake before noon.", "The river's cold as winter this morning."], ["Scrub, scrub."],
    at=[place("lf_village", work=work("laundry", [14.1, 33.2, "e", "wash"], [12.0, 30.4, "nw", "hang"]))]),
```

`place("lf_village")` names her object `npc_washer_mei` in the village, written in `world.py` and anchored at (14, 31) in
the village's spec; her spots are cells, set by eye beside the tub and the line.

The keys (the full format is `spec.py`'s docstring):

- **`npc(id, name, title, look, lines, barks=(), services=(), at=(), concealed=(), row=None, **keys)`.** `keys` are
  `scale`, `tint`, `tree`, `on_talk`, `service_labels`, `service_unlocks`, `companion` and `sect`; the row takes them
  in that order (`spec.KEYS`), whatever order the spec gives. `concealed` is what they say to a cultivator hiding their
  realm (S48).
- **`look(hair, shirt, pants, shoes, hat=, cape=, weapon=, body=)`**: the parts of `data/parts.json`, `"style:colour"`
  for the hair (an index of the character's `hair_colors`), `"garment:dye"` for the shirt and the trousers (a dye of
  `character.json` `dyes`). It is the dict `story.py`'s `outfit()` made, key for key.
- **`place(room, oid=None, work=None, anchor=None, side=None, **obj)`**: where they stand, their home first. `oid` is
  their object there (`npc_<id>` by default). With `anchor` the engine makes the placement: a room engine anchor (any
  of `room_engine.md`'s kinds, or a cell), `side` the side-view point, and `obj` the object's other fields (`facing`,
  `visible_if`, `hidden_if`).
- **`work(loop, *spots, auto=None)`**: a loop of `topdown_life.LOOPS`, and its spots (below), or `auto=n` spots round
  the person by a hash of the room and the person (`topdown_life.auto_spots`).
- **`extra(id, room, look, work)`**: a figure at work with no part in the story: no row, no talk. Its first spot is
  its home.

## Work loops by anchors

A spot is a cell `[x, y, facing(, steps)]`, which pins it, or an anchor that `spots.py` resolves on the room's built
layout as `topdown_life.py` writes `life.json`. A moved tub, line, rack or shore moves the workers with it.

| Anchor | A spot |
|---|---|
| `"home"` | the person's own spot |
| `"water_edge"` | on the bank beside open water, facing it |
| `"by:<prop kind>"` | beside a prop of that kind: its side first (a figure at a tub or an anvil reads side-on), then in front, then behind; facing it |
| `"near:<oid>"` | within two cells of another thing of the room (a shrine, a board, a well), facing it |
| `"open"` | a free spot round the person, as far from them and the spots before it as the leash allows, facing out |

Each may add, in this order, `@x` or `@x,y` (the point it looks round: the person's own spot by default; an extra's
first spot needs one), `>dir` (the facing kept) and `:steps` (the loop's steps there): `"by:wash_tub>e:wash"`.
`"auto:water_edge"` reads as `"water_edge"`.

The rules a resolved spot keeps are the hand spots' rules, which `topdown_life.py`'s checks still hold:
- a cell's centre on the person's floor, within the leash less 0.4 of a tile of their own spot (`LEASH` 2.5: a player
  beside the worker is always in talk's reach), and at least a tile from it;
- off every way's lane, a tile clear of every other thing of the room, never on a stair, a tile from the spots already
  chosen;
- walked to in a straight line from the spot before it, the last back to the first.

Among the cells that fit, the anchor's own rank wins, then the nearest to the point it looks round, then a hash of the
room, the person and the cell's offset from that point. So the choice is deterministic, and a building moved with its
worker keeps the worker's spots round it as they were (`tests.py` moves the tub and the line two cells east and the
spots follow them).

The leash is short: a worker's home has to stand within two tiles of what they work at. For a person the engine
places, anchor the home beside the work (`commons@9` is a cell above the bank and below the line). A spot that fits
nowhere says which person and anchor failed.

## Pins

Every generated value can be pinned in the spec, never in the JSON:

- a spot written as a cell is pinned (every migrated spot is);
- `row={key: value}` pins a key of the finished row (a key the row has keeps its place, a new one goes at the end),
  `DROP` takes one out;
- `place(..., anchor=(x, y))` pins a placement's cell, `side=[x, y]` its side-view point; a room spec's `pins` still
  pin its own anchors;
- `>dir` pins a spot's facing.

## Role templates

The sects' staff come from one template a post (`specs/sects.py` `ROLES`): the steward, the weapon master, the deacon,
the hall master, the librarian, the smith, the formation elder, the physician, the gardener and the outer disciple.
A template sets the title, look, lines, barks, services, keys and loop, with `{Sect}`, `{sect}`, `{key}`, `{dye}` and
`{weapon}` filled from the sect (`SECTS`). The spec gives the name and the places:

```python
staff("steward", JADE, "Steward Wei", at=[place("ja_gate_street", work=work(ROLE, [7, 16, "s"], [5.4, 14.8, "n"]))]),
```

`work(ROLE, ...)` is the role's own loop; a keyword given to `staff` wins over the role's. A new sect is a row of
`SECTS` and ten one-line specs.

## One-offs

Nine rows stay plain dictionaries in `story.py`'s `npcs()`, in a labelled section, each placed after the row it
follows in `npcs.json` (`after=`): the figures the story stages rather than people who live somewhere.
- the rooftop thief, whose daily chase is the rooftop routes' (S43 rule 15);
- Elder Gu in chains and as the Blackmast's purser, Shen Lian at the Presence Court and at the Greyfall Breach (a
  quest's turn of a person);
- the four companions (S26), the party's.

## Adding an NPC

1. Write the spec in its zone's module (a new zone goes into `specs/__init__.py`'s `ZONES`): the look from the
   character's parts, the lines and barks, the services and the dialogue tree, and the place.
   - In a room on the grid that already has their object, `place(room)` or `place(room, oid)`.
   - In a room on the grid, new to it, `place(room, anchor=..., facing=..., visible_if=...)`: the engine adds the object
     and the anchor.
   - Their work: `work(loop, ...)` with anchors (`"by:stove"`, `"water_edge"`, `"open"`), or cells.
2. Build:
   ```
   python3 tools/data/build_data.py          # the row, the side-view object (topdown_life may fail here: no cell yet)
   python3 tools/data/topdown_rooms.py       # the cell on the grid, then life.json with the spots resolved
   python3 tools/data/build_data.py --check
   ```
3. `python3 tools/content/npcs/engine.py --show ID` prints the row, the cell and the spots it chose. A spot that fits
   nowhere names the person and the anchor.
4. **Look at them in the game.** Add rows to the capture set `npc_engine` (`tools/dev/capture/shots.gd`), or a set of
   your own beside it:
   ```
   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/capture/capture.tscn -- npc_engine --out-root=<scratch>
   ```
   Check that the person stands where they belong, reads apart from their neighbours, and works at what their spots
   name. The `worker` take shoots a worker mid-action, the player kept out of its notice at each of its spots.
5. `python3 tools/content/npcs/engine.py --check`, then `tools/run_tests.sh`.

## The checks

- **`engine.py --check`** (`npc_engine` in `tools/run_tests.sh` and `Test.ps1`):
  - two compiles write the same rows, work, extras and anchors;
  - every spec resolves: its look's parts, hair colour and dyes; its dialogue tree and shops; each place's room and
    object there (placed on the grid where the room has a layout); each loop; each spot anchor's grammar;
  - the built data holds every person as the engine writes them: their row's keys in order in `npcs.json` (and the
    specs' people in the specs' order), each place's work in `life.json` with its anchors resolved as they resolve now,
    each extra first in its room's list;
  - a placement the engine makes is not anchored by the room's spec too;
  - `tests.py`: 12 tests of the engine on specs and a layout of their own (the look against `outfit()`, a row's key
    order and pins, the one-off rows' places, the role templates, work and extras, the engine's own placements, every
    spot anchor kind, a moved prop moving its worker, an extra's first spot, the errors, pinned spots).
- **`topdown_life.py --check`** (in `build_data.py --check`): every spot stands on its person's floor within the
  leash, every leg is walked clear, a smith's anvil spot holds its anvil.
- **`topdown_rooms.py --check`** and the room engine's `test_engine.py`: every person placed and reached on foot.
- **`data_validation`** (npcs, services, shops), `story.validate` (every NPC a room places exists, every quest giver is
  placed), `tutorial_order` and `topdown_tutorial`.

## The migration (the round trip)

Every person was re-expressed as a spec, zone by zone, until the built data was byte for byte what the hand rows wrote
(`build_data.py`, then `git diff data/` empty): first Lotus Ferry's villagers, then Stoneford, the roads east, the two
sects, then Act II's and Act III's people.

| Module | People | Extras | Spec lines | From |
|---|---|---|---|---|
| `lotus_ferry.py` | 9 | 2 | 55 | the prologue's village, its houses and the night |
| `stoneford.py` | 27 | | 132 | the gate, Market Street, Artisan Row, the County Hall, the Fairground |
| `valley_roads.py` | 4 (+3 new) | 1 | 48 | Greyreed Hamlet, the Caravan Road, the Reed Marsh |
| `sects.py` | 26 (20 from 10 templates) | 2 | 120 | both sects' staff, the inner disciple, the elders, the Marsh Edge's watchers, the arena master |
| `azure_expanse.py` | 31 | | 168 | Act II |
| `star_field.py` | 21 | | 113 | Act III |

118 people and 5 extras, with 57 work loops at 134 places. Gone from the hosts: 430 lines of `story.py` (`npcs()` went
from 474 lines to 63, the one-offs and the passes; the 23-line table of hidden-realm lines is in the specs) and the
110 lines of `topdown_life.py`'s `WORK` and `EXTRAS`. `WORK` and `EXTRAS` remain, empty, for what no spec writes yet: a
room batch may add its people's work there in a `# R<n>` block until they have specs, and `work_table()` puts them
after the engine's.

The specs are about as long as the lines they replaced, and now also name every person's home room. What they save is
the next person: Washer Ying is five lines, where before she was a row in `story.py`, an object in `world.py`, an
anchor in the room's spec and a work entry with cells chosen by eye in `topdown_life.py`.

## The first new people: Greyreed Hamlet comes home

"If the well runs clean again, we might come home," Elder Gao says. Greyreed Hamlet's square stood empty but for him
(and Trader Min after Market Day). Once Cleansing the Well is done, three villagers are home and at work there, each one
spec in `specs/valley_roads.py`, each placed by an anchor of the room and set to work by anchors of its layout:

| Person | Home | Work |
|---|---|---|
| Washer Ying | `commons@9` (9, 19) | laundry: the wash at the water's edge, the hanging at the laundry line |
| Fisher Gan | `commons@12` (12, 19) | mending nets: at the net rack, then looking out over the water |
| Old Jiu | `square@22` (22, 21) | sweeping the square: home and two open spots |

The capture set `npc_engine` (`docs/architecture/npc_engine/`):

| Picture | What |
|---|---|
| `01_hamlet_before` | the square before the well runs clean: Elder Gao alone |
| `02_hamlet_home_again` | after: the three villagers home and at work |
| `03_washer_ying_wash`, `04_washer_ying_hang` | the washer scrubbing at the bank, hanging the washing at the line |
| `05_fisher_gan_mend` | the fisher mending at the net rack |
| `06_old_jiu_sweep` | the old man sweeping the square, and his bark |
| `07_talk_washer_ying` | a word with the washer |
| `rooms/gh_hamlet_square` | the hamlet whole |

Their three anchors moved a few of the hamlet's scattered plants (a dead tree stood where the washer lives): the room
engine keeps its flora clear of every anchor.

**Engine size.** `spec.py` 181 lines, `spots.py` 204, `engine.py` 418, `tests.py` 206; the specs 641.
