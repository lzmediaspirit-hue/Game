# tools/data: the data generators

The game reads only the JSON under `data/`. Every table there is written by a module here, from Python literals and
formulas: never edit a file under `data/` by hand, change its module and rebuild. Run everything from `JadeRiver/`.

```
python3 tools/data/build_data.py                 # every module of MODULES, in order, then the item and monster wikis
python3 tools/data/build_data.py --check         # build in memory: fail unless every file on disk is current
python3 tools/data/build_data.py story economy   # only these modules (still in MODULES' order)
python3 tools/data/<module>.py [--write | --check] [--only NAME[,NAME]]
```

## The command line

Every generator module ends with `raise SystemExit(run_cli(build))` (`common.run_cli`), so they all take the same flags:

| Flag | What it does |
|---|---|
| `--write` (the default) | builds, and writes each file whose text changed |
| `--check` | builds in memory and compares each file with the one on disk; a missing or different file is stale |
| `--only NAME[,NAME]` | touches only these outputs: a file's name without `.json` (`lf_village`), or its path under `data/` (`strings/en`). The module's own checks still run whole |

Exit code: **0** written or current, **1** a check failed or a file is stale (the message says which), **2** a usage
error. `build_data.py` takes the same flags, and module names after them.

## A generator module

```python
"""What it writes (data/<table>.json), what it checks, the decisions behind it."""
from common import entries, fail, run_cli, write

ROWS = [...]                              # the content, as literals and small constructors


def build():
    errs = [...]                          # its own checks
    fail("<module>", errs)                # raises: run_cli prints the problems and exits 1
    entries("<table>", ROWS, extra=...)   # a list table; write(name, payload) for a config table
    return "26 rows reached"              # optional: said after the run's last line


if __name__ == "__main__":
    raise SystemExit(run_cli(build))
```

- **Writing.** Every file leaves by `common.emit(path, text)`: `write` and `entries` format a table as the game reads
  it (`schema_version` first, one space of indent, UTF-8 as is). A module that formats its own text (the layouts,
  `techniques.json` a row a line) calls `emit` itself. A module that makes every file of a folder (`world.py`'s rooms,
  `story.py`'s dialogue) says so with `clear(folder)`: a file there it no longer makes is removed (`--write`) or stale
  (`--check`).
- **Reading back.** `common.read(name)` and `common.rows(name)` read a table of `data/` (a module later in `MODULES`
  may read what an earlier one wrote).
- **Tables the game does not read** (a check's or a tool's own: `balance.json`, `legendary_chains.json`, the review
  room) go to `tests/data/` (`common.TESTS_DATA`): ContentDB loads every `data/*.json` and the export ships it.
- **Deterministic.** Two builds write the same bytes: no clock, no unseeded randomness, dictionaries in a fixed order.

## Adding one

1. Write `tools/data/<module>.py` as above, and add it to `MODULES` in `build_data.py` after the modules it reads.
2. `python3 tools/data/build_data.py`, then `git diff data/`: only what you meant to change.
3. If it has a check worth running on every change, add `python3 tools/data/<module>.py --check` to
   `tools/run_tests.sh` (as `places` and `sound` are).

## The item engine

The pills, the herbs by age, the ores, the creature parts and the gear by family × grade are families of the item
engine (`tools/content/items`, `docs/architecture/item_engine.md`): a new item of those kinds is a spec there, not a row
here. `items.py` places their rows among its one-offs, and `economy.py` their recipes and shop lines. Its gate is
`python3 tools/content/items/engine.py --check`.

## The gates here (tools/run_tests.sh runs them)

- `room_lint.py`: the side-view rooms against the verticality rules.
- `topdown_rooms.py --check`: the top-down layouts are current, every thing and way in them is placed and reached on
  foot, and their Grid walks as the game does. The Grid's measures come from `data/movement.json` `topdown`
  (`step_up`, and the jump's `impulse`, `gravity` and `mantle`); `parity()` asks the game, through
  `grid_parity.tscn` (Godot from `$GODOT`, else `godot` on the PATH), for every layout's floors and auto-path reach
  (`TopdownRoute.reach`) and compares them cell for cell. Without a Godot it says it did not run.
- `sect_walks.py --check`, `places.py --check`, `sound.py --check`.
