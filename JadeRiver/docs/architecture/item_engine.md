# The item engine

Roadmap decision 45, phase 3, engine E4 (`docs/architecture/audit_45.md` §6.4). A new tier ladder of items used to touch
four or five files: its rows in `tools/data/items.py`, its lines in each shop and its recipes in
`tools/data/economy.py`, its loot, and its icon rows in `tools/icons/families/pills.py`. Items are now written as
**families**: a family is one spec, and the engine compiles it into everything the game reads about it. A new ladder of
four pills is one 30-line spec (the Streams Pills below); nothing else is edited.

| File | What it is |
|---|---|
| `tools/content/items/specs/*.py` | the families, as Python literals (`FAMILIES`), one module a group: `pills`, `herbs`, `ores`, `parts`, `gear`, `streams` |
| `tools/content/items/dsl.py` | the spec language: `family()`, `gear()`, `member()`, `curve()`, `per()`, `qi()`, `effect()`, `DROP` |
| `tools/content/items/curves.py` | what a tier is worth: `MID_ILV`, decision 45's `cultivation()`, `SPEED`, `PILL_TOXICITY`, `RECIPE_TIME` |
| `tools/content/items/kinds.py` | the row templates, a kind each (pill, herb, seed, ore, part, weapon, armour, gourd, pet_gear, furnace), and `item()` / `artifact()` |
| `tools/content/items/engine.py` | the compile, the channels the hosts read, the checks and the command line |
| `tools/content/items/tests.py` | the engine's own tests (`engine.py --check` runs them) |
| `tools/data/items.py` | the host of the rows: places each family section among the one-offs it writes by hand |
| `tools/data/economy.py` | the host of the recipes (`recipes()`) and the shop lines (`shops()`) |
| `tools/icons/families/pills.py` | the pill icons: the families' vessels and grade kits, plus the three pills no family writes |

```
python3 tools/data/build_data.py                   # every data file, the families' included
python3 tools/icons/build_icons.py                 # the icons (a new pill family's too)
python3 tools/content/items/engine.py --check      # the engine's gate (tools/run_tests.sh and Test.ps1 run it)
python3 tools/content/items/engine.py --list       # every family and its members
```

## A family: the Streams Pills

The first family written as a spec only (`specs/streams.py`): cultivation speed from Cloud Stride to Will Manifest,
where the incense (Plain, Common) and the Qi Flow Pill (Earth) leave off.

```python
family("pill.streams", kind="pill", tiers=("heaven", "mystic", "sage", "sovereign"),
       words={"heaven": "three", "mystic": "five", "sage": "seven", "sovereign": "nine"},
       id="{word}_streams_pill", name="{Word} Streams Pill",
       desc="It opens {word} streams of the meridians to the Qi around you: cultivation +{pct}% for {minutes} minutes. ...",
       mark="spiral_up", toxicity=curve("toxicity"), cause="energy", group="buff", resist="accumulation",
       use=[effect("add_modifier", stat="accumulation_rate", op="flat", value=curve("speed"),
                   duration=curve("speed", "seconds"), source="streams_pill")],
       recipe=dict(inputs=per(heaven=[("cloudtop_orchid", 1), ("mist_lotus", 2), ("cloud_feather", 1)], ...),
                   time_s=curve("recipe_time"), element="earth",
                   learn={"alchemist_guild": {"heaven": dict(price=1900, flag="guild_alchemy_expert"), ...},
                          "port_apothecary": {"sage": dict(price=45)}, "lanternfall_apothecary": {"sovereign": dict(price=5)}}),
       icon=dict(vessel="buff", pill="cyan", ink=("qi", -1)),
       sources=dict(shop={"mei_qing": {"heaven": dict(realm="cloud_stride_1"), "mystic": dict(realm="heaven_glimpse_1")},
                          "condensing_hall": {"sage": dict(realm="sage_sovereign_1")},
                          "lanternfall_apothecary": {"sovereign": dict(realm="will_manifest_1")}}))
```

It writes, for each of its four members:
- **the row** (`items.json`): `three_streams_pill`, "Three Streams Pill", Heaven, ilv 45 (`MID_ILV`), toxicity 8
  (`PILL_TOXICITY`), +30% `accumulation_rate` for 2,700 s (`SPEED`), its text filled from the same numbers, its Pill Soul
  from its group, its resistance family. The section is the kind's (`pills`), so items.py places it with no change;
- **the recipe** (`recipes.json`): alchemy, its grade's inputs, 600 s (`RECIPE_TIME`), element earth, at the end of
  economy.py's alchemy block;
- **the shop lines** (`shops.json`): the pill at Mei Qing's stall from Cloud Stride 1 at the game's price for its Level
  (`LootRules.value_of`, so no price is written), and its recipe scroll at the Alchemist Guild; each line no shop list
  places joins the end of its shop's stock;
- **the icon** (`pill_icons()`): the gourd of a lifting draught in the grade's kit (`PILL_GRADES`), the spiral mark, a
  cyan pill. `build_icons.py` draws it: 64 px and @32, about 3.5 KB a pill.

## The spec

`family(fid, kind=..., tiers=(...) | members=[...], ...)`:

- **`fid`** is `<kind>.<stem>`. A one-member family's id is its stem (`pill.healing_pill` writes `healing_pill`); a
  ladder names its ids, names and texts with templates (`id="{word}_streams_pill"`). A template sees `{tier}`,
  `{Tier}`, `{Grade}`, `{word}`, `{Word}` (from `words=`), `{pct}` and `{minutes}` (the grade's `SPEED`), `{cult}`
  (the cultivation its `qi()` effects pay: "+420 cultivation"), and the member's own fields.
- **`tiers=`** makes one member a grade. **`members=[member(tier, grade, id=..., ...)]`** lists them by hand: a herb's
  ages, an ore a grade, a zone's creature parts, an armour slot's pieces. A member's field wins over its family's.
- **A kind's fields** are the row's own: a pill's `mark`, `toxicity`, `cause`, `group`, `use`, `soul`, `resist` and
  `extra` (the row's other keys, after `soul_effect`); a herb's `nature`, `roles`, `raw=dict(use, toxicity)` and
  `seed=dict(grade, desc, sources)`; a part's `type`; a weapon's `appearance`, `attribute`; an armour piece's `slot`,
  `dye`; a gourd's `bag` and `quick`; a pet piece's or a furnace's `stats`. `kinds.py` writes the keys in the order the
  game's rows have always had them.
- **Values** may be `curve(name[, key])`, the member's grade on a curve of `curves.py`, or `per({tier: value},
  default=...)`. `qi(share)` is decision 45's fixed cultivation: `share` of the need of the stage at the middle of the
  member's grade, rounded as a reward (`realms.cultivation`). Phase 1's numbers are kept exactly: the Qi Gathering Pill
  is still `qi(0.08)` at Common, +420; a raw ten-year ginseng `qi(0.024)`, +130.
- **`recipe=dict(inputs, craft="alchemy", time_s, element, fragments, learn, block, after, id, grade, ...)`**, or a
  function of the member that returns one (the gear's `forged()`): its other keys (`hidden`, `fire`, `default`,
  `requires_ranks`) go in the row as given. `learn={shop: line}` sells its recipe scroll; `fragments` are an ancient
  recipe's pages; `element` its furnace affinity (S44).
- **`icon=dict(vessel, pill, ink[, mark, extra])`** for a pill (the vessel defaults to its group's, the mark to its
  own), or `icon="<id>"` for a row that shows another item's icon.
- **`sources=dict(...)`**: where it comes from, below.

## Sources

A family must name its sources, so `wiki.py --gaps` stays empty by construction: the engine refuses to build a member
nothing hands out.

| Key | What it is | Written or found |
|---|---|---|
| `shop={shop: line}` | its shop lines (and `learn=` in its recipe: its recipe scroll's) | written (`shelves()`) |
| `recipe` | its recipe | written (`recipes()`) |
| `drop=[creature, ...]` | the creatures whose loot tables carry it (`True`: many do) | found: each named creature drops it |
| `chest`, `gather`, `garden`, `craft`, `reward`, `mail`, `auction` | the other channels of `tools/dev/wiki.py` | found in the built data |
| `mark="story" \| "system" \| "later"` | wiki.py's marks, for what no channel hands out | the row's `source` |

A shop line is `{}` or its own keys: `price` (none: the game's price for the item's Level, in the shop's currency),
`realm` or `flag` (a `requires` of one condition), `requires`, `rotation=True` (the rotating pool), `currency`, `daily`,
`sealed`. The value of a shop may be one line for every member, a list of the tiers it sells, or a dict of each tier's
line. An outside source may be a list of the tiers it covers (the plain straw hat's `reward=["plain"]`).

**Loot belongs to the monster engine.** `tools/data/enemies.py` (E2) writes every loot table, the chests' and jars'
included. A creature part names its creatures and `--check` finds it in each one's table; a family that should drop
from a creature or a chest names the table here and asks E2 for the row.

## Placing what a family writes

The data files keep the order their rows have always had, so the hosts place each piece:

- **Rows.** A family writes into its kind's section (`pills`, `herbs`, `seeds`, `ores`, `parts.valley`, `weapons`,
  `armour`, `gourds`, `pet_gear`, `furnaces`) or the one its members name (`section="parts.expanse"`). items.py places
  each with `rows.extend(E.items("<section>"))` between `E.begin("items")` and `E.end("items")`; `end` fails on a
  section nobody placed. A section lists its families' members in spec order; `ORDER = {section: [ids]}` in a spec pins
  the legacy order (the herbs and the seeds), and `ORDER = {section: "grade"}` lays it out grade by grade (the gear).
- **Recipes.** A recipe joins its block (the craft's name, or `block=`); economy.py places each with
  `R.extend(E.recipes("<block>"))` and reads each one's element and pages with `E.recipe_meta(id)`. `after=` moves one
  recipe behind another (the Storm Blood Pill's legacy place).
- **Shop lines.** economy.py's `shops()` ends with `E.shelves(rows)`. A shop's list names a family's line only to place
  it among the shop's own lines: `F("<item>")` for the item, `L("<recipe>")` for the scroll that teaches the recipe.
  Every declared line no marker places follows the shop's own lines, in spec order: a new family needs no marker.
  Mei Qing's Recipe Box holds nothing of its own; the Tidebreak Armoury and Lanternwright Han's shelf take their
  Sovereign and Will gear that way.
- **Icons.** `pills.py` builds `PILLS_HD` from `engine.pill_icons()` and its three one-offs.
- **What other generators read.** items.py keeps `HERB_AGE` and `SEEDS` (herbs.py, `garden.json`) and the weapons'
  `FAMILY_APPEARANCE` from the engine.

## Hand tweaks

Every generated value can be pinned in the spec, never in the JSON (audit 45 §6, rule 3):

- `row=dict(key=value)` on a family or a member pins a key of the finished row: a key the row has keeps its place, a
  new one goes at the end, and `DROP` removes one (`soul=DROP` and `cause=DROP` drop a pill's soul effect and cause, as
  the Law pills have none).
- A member's own field wins over its family's; `per()` gives each member its own value.
- `ORDER`, `after=` and the `F` / `L` markers pin where a row, a recipe or a line stands.
- `sinks=("use", "gift")` without `"sell"` writes `sell: false`.

## One-offs

Items that are one of a kind stay plain rows in items.py's labelled one-offs section, never forced into a family:
quest items and keys (the sun seal, the Black Ledger, the tokens, the charts and the skiffs), unique treasures and
relics (the Mindwell Lotus, the Spirit Fruit, the Heavenly Flames, the named furnaces and the Nine-Dragon Cauldron, the
Moonlit Blade), the curios and valuables. So do the small groups no family writes yet (foods, fish, talismans and their
inks, tools, scrolls and manuals, beast cores, pet medicine and books, the post goods of `posts.py`); each is a family
the day it grows a ladder. Three pills stay out of the pill families: the two pet medicines and the thrown Viper Smoke
Pill (their rows, recipes and icons are written by hand).

## Adding a family

1. Write it in the spec module of its group (or a new module, added to `engine.SPECS`): its tiers or members, its
   kind's fields, values from the curves, its recipe and icon, and its sources.
2. `python3 tools/data/build_data.py`; for a pill, `python3 tools/icons/build_icons.py` and an import
   (`godot --headless --path . --import`) for the new icons' `.import` files.
3. `python3 tools/content/items/engine.py --check`, and `git diff data/`: only the new rows and lines.
4. A drop or a chest row it names: ask the monster engine (E2) for it.

## The checks

- **`build_data.py --check`**: every data file is what its generators write, the families' rows, recipes and lines
  among them.
- **`engine.py --check`** (`item_engine` in `tools/run_tests.sh` and `Test.ps1`):
  - two compiles write the same bytes;
  - the built data holds every member's row and recipe, and the icon manifest its icon;
  - each source a member names is in the built data by wiki.py's channels, and each creature a part names drops it;
  - each pill family's icon renders the same bytes twice and the same as the PNG on disk;
  - `tests.py`: 17 tests of the engine on families of their own (templates, curves, `per`, pins, `DROP`, sources,
    marks, markers, recipe blocks and `after`, `ORDER` and the grade order, unplaced sections, herbs and seeds, gear,
    pill icons) and of today's specs (decision 45's numbers, gear.py's archetypes, every member sourced).
- **`wiki.py --gaps`** stays empty; **`data_validation`**'s `item_source_suite` checks every item's source.
- **`balance_sim`**'s speed ladder: every item that raises cultivation speed, at the realm of its grade, with the Qi an
  active hour gathers without it and with it and what one use adds to a sitting; each rung (the incense, the Qi Flow
  Pill, the Streams Pills) adds more than the rung below.

## The migration (phase 3)

Each family was first used to write what items.py wrote, one at a time, each step with an empty `git diff data/`
(audit 45 §6, rule 4). Lines of the old hosts removed (items.py, economy.py, pills.py) against the spec lines that
replace them:

| Family | Members | Hand lines removed | Spec lines |
|---|---|---|---|
| Pills (30 families: their rows, recipes, elements, ancient pages, shop and recipe lines, icons) | 30 | 211 | 200 |
| Herbs by age (9 families) and their seeds | 22 | 124 | 107 |
| Ores (one family) | 9 | 25 | 37 |
| Creature parts (4 families, a zone each) | 60 | 92 | 120 |
| Gear: 11 weapon families, 4 armour slots, the gourds, 3 pet gear ladders, the far zones' furnaces | 169 | 201 | 212 |

The specs are about as long as the lines they replace; what they save is the next ladder. The Streams Pills are one
spec of 36 lines (with their notes) for four items, their recipes, eight shop lines and four icons, where a ladder
before took rows in items.py, recipes, an element table and shop lines in economy.py, and icon rows in pills.py.
items.py went from 1,031 lines to 672. The engine is about 1,000 lines (engine.py 623, kinds.py 195, dsl.py 124,
curves.py 73) and its tests 220.
