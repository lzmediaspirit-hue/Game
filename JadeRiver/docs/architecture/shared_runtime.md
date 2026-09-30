# Shared runtime

Roadmap decision 45, phase 2, slice S4 (`docs/architecture/audit_45.md` §4 and §5). The game had several hand-written
copies of the same small mechanisms. Each now has one home, described below. Its checks are in
`tests/shared_runtime_tests.gd`, which is part of `tools/run_tests.sh`.

## FrameMemo: `scripts/core/frame_memo.gd`

A per-frame cache (DUP-01). Use it when a question is asked several times in a frame and the answer cannot change
until the frame or the game moves on. Examples are a view's plate, the HUD's badges and a page's rows.

- `FrameMemo.new(ttl_frames := 1, on_revision := true, max_keys := 1)`. By default an answer is kept for the frame it
  was worked out in. It is dropped as soon as `Game.revision` moves, that is after an intent, a tick or effects.
  - Pass `on_revision = false` for an answer that depends on the frame only.
  - Pass `ttl_frames > 1` to keep answers for longer. The Menu's place homes are kept for 60 frames.
- `memo.value(key, compute: Callable)` returns the kept answer for `key`, or calls `compute`, keeps its answer and
  returns it.
  - Keys are compared by value. An array or dictionary key is kept as a copy, so a key the caller changes later is
    never matched with a stale answer.
  - `max_keys` answers are kept. The default of 1 keeps the last key only, as the hand-written key comparisons did.
- `memo.table(scope := null, scope2 := null)` returns the kept `Dictionary` itself, for a hot path asked many times a
  frame. It avoids making a `Callable` for each question. You get a new `Dictionary` when the frame, the revision or
  the scope moves. `WorldShared` passes the room and the character as its scope. Scopes are compared with `==`, so pass
  them as the same types each time, such as instance ids.
- A repeated question costs about what a hand-written cache did. On a desktop, `table` takes 472 ns against 412, and a
  one-key `value` takes 878 ns against 374, most of it the `Callable` made at the call. Keep `value` for questions asked
  a few times a frame, and `table` for the ones asked for every thing in view.
- An answer worked out while the memo was started over is returned but not kept. This happens when the `compute`
  moved the revision, or asked the memo again under another scope.
- Keep one memo for each question: a member, or a `static var` for a static owner.

```gdscript
var _badges := FrameMemo.new()
func frame_badges() -> Array:
	return _badges.value([c.get_instance_id(), points_override], func(): return point_badges(c))
```

It replaced the caches in:
- `WorldShared._frame_memo`;
- `hud.gd`: `tour_targets`, `_frame_badges` (which no longer duplicates `points_override` on every call, BUG-08) and
  `_look`;
- `TopdownWorld.soft_target`;
- `PostsPage.rows`;
- `PlaceRules.home`;
- `SpriteCache.tex_sliced`'s per-frame loading budget.

## HashNoise: `scripts/core/noise.gd`

Steady pseudo-random numbers for painted detail and placement (DUP-02). They are the same on every frame, run and
machine, and never touch the game's `Rng` streams. The class is named `HashNoise` because `Noise` is the engine's own
class.

- `HashNoise.scatter(i, salt)` returns a number in [0, 1). It is the sin-hash that `FxLayer`, `HazardView`, `MapPage`,
  `BeastKit` and the Bag each had a copy of.
- `HashNoise.cell(x, y, seed)` returns a number in [0, 1). It is the integer hash of the tile builder
  (`tools/art/topdown/canvas.py` `h01`), which was `TopdownTerrain.h01`.
- `HashNoise.value(x, y, seed)` is value noise over `cell`, which was `TopdownTerrain.vnoise`.

The outputs are bit-identical to the copies they replaced. The suite compares them over grids. Terrain, foliage,
critters and the tile builder depend on these numbers, so do not change the constants.

## Figures: `scripts/presentation/figures.gd`

The one factory for the figure of a character that a page, a card, a chip or a view draws (DUP-03). A character who
plays the top-down game is drawn as a `TopdownDoll`. A classic side-view character, decision 41's fallback, is drawn as
the side view's `Avatar`. Either figure takes the same calls: `outfit`, `play`, `facing` and `draw_on`.

| Call | What it gives |
|---|---|
| `Figures.top_down(ch = null)` | Whether `ch`, or the active character, is drawn top-down |
| `Figures.for_character(ch = null)` / `for_view(top)` | An undressed figure. The page dresses it and plays it |
| `Figures.for_outfit(o, side_k, top_px, ch = null, row = "se")` | A figure wearing `o` at each view's scale |
| `Figures.chip(o, top_clip, side_box)` | A friend's head and shoulders for a chip |
| `Figures.dress(fig, o)` | Dresses either kind of figure |
| `Figures.draw_on(fig, ci, top_at, top_px, side_at, side_k)` | Draws the figure among a page's own layers |
| `Figures.pick(fig, top_value, side_value)` | A value by the figure's kind, such as an offset |
| `Figures.side_avatar(o = null)` | The side view's `Avatar`. The side view's world uses it too (`player.gd`, `NpcView`, `EnemyView`) |

**Retiring the side view.** Every `Avatar` is made in the file's SIDE VIEW section. To retire the side view:
1. Delete that section.
2. Make `top_down` answer true, and make `for_view` return the doll.
3. Drop the `side_*` arguments at the call sites.

## ContentDB: lazy tables (BUG-11)

`scripts/core/content_db.gd` no longer parses every data file at boot. `techniques.json` alone took 133 to 191 ms.

- **At boot** it reads only:
  - `realms` and `recipes`, whose indexes (`realm_order`, `realm_index`, `used_in`) are built at load;
  - the strings.
- **Beside the boot**, a low-priority loading thread reads the other tables one at a time, starting with
  `techniques`. What it has read is handed over each frame. On a device with a spare core, it reads while the boot
  and the title run.
- **If a lookup comes first**, it takes the thread's copy if there is one, else reads its table on the spot. It never
  waits on the thread: if the thread has that table in hand, its copy comes too late and is let go.
- **Every lookup** (`entry`, `has_entry`, `all`, `config`, `room`, `rooms`, `room_zone`, `dialogue`, `parts`) returns
  the same answer as when boot read everything: the same rows, in the same order, with the same errors.
- **Reading `tables`, `lists`, `configs` or `load_errors` as a whole** reads every table first. Tests and validation do
  this. The three are kept in the data folder's order.
- **To ask whether a list table exists without reading everything**, use `ContentDB.has_table(name)`.

## GameEvents (BUG-03)

- `UNLOCK_TRIGGERS` and `SAVE_TRIGGERS` are constant sets (`name -> true`). Every emitted event checks both, so each
  check is now one hash lookup.
- A name's list of listeners is replaced on `subscribe`, never changed in place. A delivery walks the list it began
  with, without copying it for every event. A listener added or removed during a delivery joins or leaves from the
  next event, as before.

## TopdownFx cap (BUG-04)

`TopdownFx` keeps at most `MAX_NODES` (72) effects.

- **When the cap is full**, the oldest one-shot is retired first. If no one-shot is left, the oldest loop goes. The
  effect just begun is never retired.
  - Before, only one-shots were retired. With the list full of loops, it grew past the cap, and each new one-shot was
    dropped as soon as it began.
- **`advance`** drops finished effects in one pass. It keeps the others in their order, since the cap retires the
  oldest first.
