# The HUD in parts

Roadmap decision 45, phase 2, slice S6 (`docs/architecture/audit_45.md` §2.2, §6.6 and §7). `scripts/hud.gd` had 3,302
lines, 170 functions and a 615-line `match` with 234 arms. It now keeps the HUD's state, its frame and its input, and
its work is done by ten parts under `scripts/hud/`. The game's events reach the player as rows of the cue table, the
same table the world views read (`docs/architecture/cues.md`). Callers use the HUD as before.

| File | Lines | What it holds |
|---|---:|---|
| `scripts/hud.gd` (`Hud`) | 552 | Every field (the state tests, captures and the parts read), the layout's constants, the signals, `_process` and `_draw` (which call the parts in order), `_input` with the keys, the locks (`set_blocked`, `set_moment_lock`, `set_scene_lock`), `add_log`, `toast`, `ring`, `glyph`, and a forwarder for every public method |
| `hud/hud_part.gd` (`HudPart`) | 17 | The base: a part's `hud` |
| `hud/hud_layout.gd` (`HudLayout`) | 344 | Where the controls stand and which show: the cluster's rings, ring 2 as the moment fills it, the hit circles, the rects the world's names keep off, the points badges, rest and fight |
| `hud/hud_tours.gd` (`HudTours`) | 44 | The tutorial coach's anchors by name (`tour_rect`, `tour_targets`) |
| `hud/hud_input.gd` (`HudInput`) | 367 | A finger on the screen: what a touch lands on, the aiming gestures of Attack and the techniques, the pet wheel, the holds, the technique page's scroll |
| `hud/hud_actions.gd` (`HudActions`) | 208 | What a control asks of the game: the context in reach, a harvest's hold and tap, a place's pose, Keeping Post, the quick slots, the Draught, the treasures, the swap, the Presence, the Sphere, a points badge |
| `hud/hud_notices.gd` (`HudNotices`) | 291 | The game's events as log lines, toasts and captions: the cue table's rows, and 47 arms of code |
| `hud/hud_controls.gd` (`HudControls`) | 388 | Drawing the thumb's cluster: Attack and its drag moves, the techniques, the fan, ring 2, the auto-hunt toggle, the harvest ring, the pet wheel, the stick |
| `hud/hud_panels.gd` (`HudPanels`) | 390 | Drawing the plates: the player panel, the points badges, the party chips, the tracker, the icon row, the purse, the progress edge, the log, the unbound player's plain panel |
| `hud/hud_minimap.gd` (`HudMinimap`) | 162 | The minimap and what a tap on it opens |
| `hud/hud_top_stack.gd` (`HudTopStack`) | 280 | The top centre (a run's seconds, the room's name, a room event, a tribulation, a fortune card, the toasts, a caption) and the boss bar |
| `hud/hud_side_view.gd` (`HudSideView`) | 79 | The side view's own answers (below) |

## How a part works

A part is a `RefCounted` with one field, `hud`, set when the HUD is made (`Hud._init`, so a HUD made with `new()` and
never added to the tree has its parts too). It keeps no state: every field stays on the HUD.

- **The HUD's fields, signals and canvas** are `hud.touches`, `hud.open_page.emit(...)`, `hud.draw_rect(...)`. A part
  draws only while the HUD draws: `Hud._draw` calls the parts in the order the screen is painted, and they paint on the
  HUD's canvas (`UiKit.draw_text(hud, ...)`).
- **Its constants** are the class's: `Hud.RING2_R`, `Hud.CLEAR_ZONE`.
- **Another part's function** is called on that part (`hud.layout.ring2(c)`), so the names one part calls on another
  are public. A function the HUD keeps (`hud.shown`, `hud.add_log`, `hud.ring`) is called on the HUD.
- **The reference is a plain one.** S10's authority parts hold a weak reference, because an authority is ref-counted
  and would keep its parts alive in a cycle. The HUD is a Node, so the two cannot keep each other alive, and a plain
  typed reference lets the GDScript compiler check every name a part uses.

**The facade.** Every public method the HUD had is still the HUD's, forwarded in one line to its part
(`func press(id: int, p: Vector2): input.press(id, p)`). Tests and tools call 16 private names; their forwarders keep
those names (`_layout`, `_ring2`, `_tick_fight`, `_tick_aims` …), as S10's do, until S11 renames them.
`tests/hud_tests.gd` holds the HUD to its 82 names.

**The frame.** `_process` runs, in order: the place pose's wait, the page scroll, `notices.age` (the log, the toasts,
the banner, a card, a caption, the pulses), `input.tick_holds` (Cultivate, Pet, Dodge and Attack held), the channel and
the harvest tap, the aims, the equip prompt, the context, rest and fight, the points badges, and the rects the world's
names keep off. `_draw` paints the player panel, the badges, the party, the tracker, the minimap, the icon row, the
auto-hunt toggle, the purse, the cluster, the progress edge, the log, the boss bar, the top stack, the equip prompt,
the pet wheel, the harvest ring, its word and the stick.

**What reads the sources.** `rules_tests`' `ui_style_suite` (the colour tokens, the type scale of the 66 text calls,
the outlined log) and `contract_tests`' strings and read-only gates read `hud.gd` and `scripts/hud/`; so do
`tools/dev/extract_strings.py` (prefix `hud`) and `tools/dev/ui_style_audit.py`. `contract_tests`' controls line reads
the keys in `Hud._input`.

## The notices

An event reaches the player as the first of its rows in `data/cues.json` with `to: "hud"` whose `when` holds
(`HudNotices.play`): a log line, a toast or both. 237 rows answer 188 events. The other 47 events are arms of
`HudNotices.handle`'s `match`, and an event is one or the other, never both (`cue_tests` checks). They stay code because
they do more than say something or say it from more than the payload:

- they open a page (`foe_surrendered`, `fate_offered`, `young_master_challenge`), set the room's banner
  (`room_entered`), a fortune card (`fortune_encounter`), a reveal pulse (`hud_element_revealed`), the equip prompt
  (`item_added`), a buzz (`player_gravely_wounded`), a sound (`tribulation_bolt`) or a phone notification
  (`world_event_scheduled`, `mine_contested`);
- they ask the world, the calendar or a quest (`world_event_started`/`_ended`, `season_changed`, `ranking_changed`,
  `treasure_birth_announced`, `weather_changed`, `portal_blocked`, `quest_accepted`, `quest_ready`,
  `objective_progressed`, `prestige_gained`, `post_left`);
- they work out what they say (`snare_collected` sums its catch, `tribulation_result` subtracts, `treasure_set` counts
  from one, `spirit_affinity_changed` every tenth point, `experiment_result` and `craft_completed` read a prefix,
  `pill_tribulation_result` compares two fields, `killing_intent_changed` a stat's maximum, `treasure_used` whether the
  payload has charges at all, `system_unlocked` a flag that is true when left out, `contract_formed` a key with the
  payload's word in its middle, `lantern_light` a light that is full when left out);
- they read deep into data (`sect_role_chosen`, `sect_node_bought`, `secret_art_learned`, `post_vow_learned`,
  `pet_core_formed`, `artifact_spirit_spoke`, `collection_seal_claimed`, `mine_lost`), or the spar's lines
  (`spar_started`, `spar_ended`), or what a use did (`item_used`), or two things that each may happen
  (`heart_demon_changed`).

The captions (a sound written out, when the player turns captions on) stay the HUD's `CAPTIONS`.

### Adding a notice

Add a row to `hud()` in `tools/data/cues.py`, before the event's wider rows, with the helpers there:

```python
hrow("herb_withered", log(tx("hud.herb_withered", item("herb")), "MIST"), when=ACTIVE),
hrow("bounty_claimed", toast(tx("hud.bounty_claimed", name("enemies", "bounty"), i("reward")), "gold")),
hrow("route_started", toast(tx("hud.route_started"), "quest", sub=tx("hud.route_hint", i("limit", 60), plural=i("limit", 60))), when=ACTIVE),
```

- `log(text, colour)` is a line of the log in a UiKit colour token; `always=True` shows it before the log is revealed.
  `toast(text, style, sub=...)` is a toast: `unlock`, `gold`, `quest` or `danger`, with its second line.
- The words are string keys of `tools/data/ui_strings.json` (`tx(key, args...)`), never literals. Their arguments
  come from the payload: `p("name")` as it is, `i("level", 0)` a whole number (with its default when the payload
  leaves it out), `f("seconds")`, `item()`, `name("enemies", "def")`, `field("posts", "craft", "name")`,
  `pet()`, `span("hours", times=3600.0)`, `{"fmt": p("silver")}`, `{"title": p("kind")}`; `ui(prefix, key)` is the
  string of a key that ends in the payload's word, `join(...)` texts one after another. `cues.md` has the whole list.
- `when` holds when every key does: `ACTIVE` (the active character's event), a payload value, a list of them,
  `{"gt": n}`, `{"ge"}`, `{"lt"}`, `{"le"}`, `{"not": v}`, `SHOWN_LOG` (`{"@revealed": "hud:system_log"}`) or
  `{"@unlocked": "mail"}`.

Then `python3 tools/data/cues.py` (or `build_data.py`). It fails on an event the game does not emit, a string key
that does not exist, a step the HUD does not play, a toast style it does not know, or a row after an open one. Then run
`cue_tests`: it plays every HUD row once through the HUD's own `_on_event`.

## The side view

The side view is decision 41's frozen fallback (`audit_45.md` §2.4). Its code on the HUD is grouped so that retiring it
is quick: `HudSideView` (`scripts/hud/hud_side_view.gd`) holds its answers, and each place that calls them or guards
against its body is marked `# side view` (or, for the engine tests' bare player, `# the engine tests' bare side-view
player`). Retiring the side view deletes the file and these branches:

| Where | What the side view gets |
|---|---|
| `HudInput.dodge` | A body with no dash of its own: `HudSideView.dodge`, the combat authority's dodge along its facing |
| `HudInput.aims` | No aiming: Attack and the techniques act on a tap (it gates the aims in `press`, `tick_aims`, `armed`, `Hud._notification` and the drag moves' drawing) |
| `HudActions.use_context` | A ladder or a rope in reach (`"climbable"`, which only `world.gd` offers): `HudSideView.climb` |
| `HudActions._play_place_pose`, `open_place_page`, `Hud.set_blocked` | No place poses (`has_method("play_place_pose")`, `"end_place_pose"`) |
| `HudPanels._draw_face` | A classic character's companions, cut from their avatar's idle frame: `HudSideView.draw_face` (and `Hud._faces` keeps them by id) |
| `HudMinimap.draw` | A room with no height grid: `HudSideView.minimap_projection`, `draw_minimap_surfaces` and `draw_minimap_ladders`; the quest's chevron and the player's arrow along x; every shrine as a square |
| `Hud._input`, `HudPanels.draw_legacy` | The engine tests' bare player (no character bound): its four keys and a plain panel |

## The swap and the context's label

At 1280 × 720 the weapon swap's button (ring 2's sixth place, 292°) crossed the top corner of the context's label
("Talk · Lu" under the 270° button) by 3 px. The label is now `CTX_LABEL_W` 116 px wide (from 128), centred as before:
no control moves, and a label wider than 116 px ends in "…" sooner. Anything else ring 2 puts at 292° in a crowded
fight clears it too. `tests/hud_tests.gd` checks it right- and left-handed, with crowded loads.

## Checks

- `tests/hud_tests.gd` (new; S2's runners take it): the HUD's 82 names, its ten parts on `new()`, the swap and the label.
- `tests/cue_tests.gd`: the HUD's rows against the game and the HUD's code, its conditions and texts, every row played.
- `rules_tests`' HUD suites, `tutorials`, `topdown_tutorial`, `tutorial_order`, `prologue_run`, `hollow_night` and
  `contract_tests` guard the move. Their check counts are as before.
- The capture sets `hud`, `hud_round` (at 1280 × 720 and at 2400 × 1080), `tutorials` and `tutorials_late` were taken
  before and after under the pinned clock and seed. The pictures differ only where the game draws by the wall clock
  (water, grass, trees and reeds), and in the context's label where it is wider than 116 px.
