# The cue table

Roadmap decision 45, phase 2, slice E6, the world half (`docs/architecture/audit_45.md` §6.6). The world views
answered the game's events with effects, sounds and shakes in one long `match` in `WorldShared.play`, an arm an event.
Those answers are now rows of a table: a new cue is a row, not code. The HUD half of E6 (the toasts and log lines of
`hud.gd`, slice S6) is meant to use the same format, reader and generator.

| File | What it is |
|---|---|
| `tools/data/cues.py` | the rows, as Python literals, and the build's checks; it writes `data/cues.json` |
| `data/cues.json` | the table the game reads (generated, a row a line: never edit it by hand) |
| `scripts/presentation/cues.gd` | `Cues`, the reading half: the rows of an event, their conditions, values, colours and texts |
| `scripts/presentation/world_shared.gd` | `WorldShared.play`, the world's player: the steps, the anchors and the handlers |
| `tests/cue_tests.gd` | the suite `cue_tests`: every row against the game, and every row played once |

```
python3 tools/data/cues.py            # write data/cues.json (build_data.py runs it too, last)
python3 tools/data/cues.py --check    # fail unless data/cues.json is current
godot --headless --path . res://tests/cue_tests.tscn
```

## How a row plays

Both views hand every event they do not handle themselves to `WorldShared.play(host, name, payload)`. It asks
`Cues.pick("world", name, payload)` for the first of the event's rows, in the table's order, whose `when` holds, and
does that row's steps in order. The first match wins, as the `match` arm and its `if`s did, so an event's rows go from
the narrowest to the widest, and a row without `when` comes last. `play` returns false for an event with no rows, so
the view knows the table leaves it alone.

## The format

`data/cues.json` is a list table, `{"schema_version": 1, "_note": ..., "entries": [row, ...]}`, so
`ContentDB.all("cues")` reads it. A row:

```json
{"id": "world.object_hit", "to": "world", "event": "object_hit",
 "do": [{"hit_flash": 0.15}, {"fx": "spark", "at": "ground", "off": [0, -30], "color": "PALE_GOLD", "dur": 0.2}, {"sound": "hit"}]}
{"id": "world.hazard_struck.harmless", "to": "world", "event": "hazard_struck", "when": {"actor": "active", "amount": 0},
 "do": [{"fx": "label", "off": [0, -130], "text": {"name_of": "hazards", "id": "payload.hazard"}, "color": "PALE_GOLD", "size": 17}]}
```

- **`id`**: `<to>.<event>`, and `.<name>` when an event has several rows. It is unique over the whole table.
- **`to`**: who plays the row. `world` is `WorldShared.play`. The HUD half adds `hud`.
- **`event`**: a `GameEvents` event the game emits. It is written as `"event": "<name>"`, which is how
  `contract_tests` finds a reactor in data.
- **`when`** (optional): every key must hold.
  - `"actor": "active"` (or `"target"`): the payload's actor is the active character.
  - Any other key tests the payload's value by the type of the value written. A key the payload leaves out holds
    `false`, `0` or `""`, as `p.get(key, default)` did. A list holds for one of its values, and `{"gt": n}` for more
    than `n`.
  - `"@active": true` holds when a character is active. `"@<path>"` tests a value of the active character, such as
    `"@pools.max_qi": {"gt": 0}`; without an active character it never holds.
- **`do`**: the steps, in order. Each step is one of:
  - `{"fx": kind, "at": anchor, "off": [x, y], "flip": "side", ...}`: an effect. `kind` is one of `FxLayer.KINDS`,
    added with `FxLayer.add`, or `label` (`FxLayer.label`, a word that rises like a number: `text`, `color`, `size`),
    or `parry` (`FxLayer.parry`, turned by the host's facing). The other keys are `FxLayer.add`'s own (`color`,
    `radius`, `dur`, `size`, `text`, `facing`, ...).
  - `{"sound": id}`: `Audio.play(id)`. The id is the sound bank's (`data/audio.json`), never a copy of a sound.
  - `{"shake": s}`: `host.add_shake(s)`.
  - `{"hit_flash": s}`: the view of the payload's `object` flashes for `s` seconds.
  - `{"call": handler}`: one of `WorldShared.HANDLERS`, for an answer that is code (below).

**Anchors** (`at`, default `feet`), then moved by `off`. With `"flip": "side"`, the offset's x is turned by the
payload's `side`.

| Anchor | Where |
|---|---|
| `feet` | the player's feet (`host.feet()`) |
| `ground` | the payload's `x`, `y` (the feet's when it has none) |
| `point` | the payload's `x`, `y - alt` (a thing in the air) |
| `object` | the view of the payload's `object`; the effect is skipped when there is none |
| `foe` | over the head of the payload's `enemy` in the room; skipped when it is gone or hidden |

**Values** (any parameter but `color` and `text`): a number as written; `"payload.<key>"`; `{"payload": key, "or": d}`
with a default; `{"const": "<stats.json path>", "or": d}`; `{"field_of": table, "id": ref, "field": f, "or": d}`, a
field of a data row; `{"treasure": f, "or": d}`, a field of the used treasure's row; `{"if": when, "then": a, "else":
b}`. A number source may carry `"times": k`.

**Colours**: a UiKit token (`"PALE_GOLD"`, `MomentRules.tokens`), or `element:`, `grade:`, `quality:` and `dao:` as in
moments; `"#rrggbb"`; `[token, alpha]`; `[r, g, b, a]`; `"array:<ref>"`, an array's engraving (`FxLayer.ARRAY_COLOURS`,
the guard's by default); `{"if": ...}`. The hex colours are the ones the arms wrote; name a new colour as a token where
one fits.

**Texts** are moments.json's sources (`MomentRules.text`): `{"key": k, "args": [...]}`, a string key and its
arguments; `{"name_of": table, "id": ref}`; `"payload.<key>"`; `{"first": [...]}`, the first that says something; or a
mark written as it is (`"!"`, `"·"`). Words the player reads are string keys, never literals.

## Adding a cue

1. Add a row to `world()` in `tools/data/cues.py` with the helpers there (`row`, `fx`, `label`, `sound`, `shake`,
   `call`, `tx`, `name_of`, `when`, `payload`). Put it before the event's wider rows.

   ```python
   row("herb_withered", fx("dust", at="object", color="#8a7a50", dur=0.6), sound("break"), when=ACTIVE),
   ```

2. `python3 tools/data/cues.py`. The build fails on an event the game does not emit, a sound not in
   `data/audio.json`, a string key not in the strings, an unknown step or anchor, or a row that can never play.
3. Run `cue_tests`. It checks the rest against the game (the effect kinds, anchors, handlers and colour tokens), and
   plays every row once.

## What stays code, and why

- **The handlers** (`WorldShared._handle`), named by a row's `call`:
  - `combat_hit` and `combat_word`: a blow's number, spark, shakes and layered sound at its tier, and a missed,
    immune or dodged blow's word. They are `CombatFx`'s, which the casts share.
  - `loot_views`: a drop makes a `LootView` node for each item, not an effect.
  - `use_parts`: what a use did is worked out from its effects (`UiKit.use_parts`), up to three lines and motes in
    the first one's colour.
  - `melody_notes`: the flute's two notes, scattered at random, each its own size.
- **The views' own answers**, which draw with their own pieces rather than the effects layer:
  - the top-down room (`topdown_world.gd`): the transfer array's column of light on arrival (held between
    `array_travelled` and `room_entered`), the parry's mark on the ground plane and its jolt (`TopdownFx`, `feel`),
    and the casts and swings of `attack_started`. The top-down room had no copy of a `WorldShared` answer. Its one
    effect of the same kind, the artifact spirit's line over the player, is now the row `world.artifact_spirit_spoke`.
  - the side view (`world.gd`, to be retired): the plunge's landing, the illusion, its casts and swings, and the
    spirit's line said by the player. It keeps these as they are.
- **Sounds of the audio director** (`audio_director.gd`): `EVENT_SFX` (an event answered with one sound, some on the UI
  bus), the door on a room change and the loot's drop are already a table there, played whatever view is up. They are
  candidates for rows with a bus once the HUD half lands.

## For the HUD half (S6)

The notices can use this file or a table of their own from the same generator:
- rows `to: "hud"`, ids `hud.<event>[.<name>]`, with steps such as `{"log": text, "color": ...}` and
  `{"toast": text, "style": ...}`, played by `hud/notices.gd`;
- `Cues.pick("hud", event, payload)`, `Cues.holds`, `Cues.value`, `Cues.color` and `Cues.text` as they are. The HUD's
  own gates (`shown("system_log")`) are new `when` keys, added to `Cues.holds`;
- `cues.py`'s `TO` and its checks take the new player and steps.
