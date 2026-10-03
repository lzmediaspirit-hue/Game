# tools/dev

Developer tools that play the game or read the project. Nothing here ships in the game.

| Tool | What it does |
|---|---|
| `capture/` | The review pictures the game takes of itself for `docs/`: one registry of rows (below) |
| `prototype_qa.gd` | The prototype's QA walk: a new player from the title to the prototype's gate through the game's own input, a shot at every step (`docs/redesign/prototype_qa.md`) |
| `tutorial_play.gd` | That walk with every tutorial guide and tour answered by a finger, each card's layout checked (decision 45, `docs/redesign/tutorials.md`) |
| `tutorial_prof.gd` | What the tutorial coach costs a frame, hidden and showing (decision 45) |
| `combat_trace.gd` | The combat feel frame by frame: chains of presses played through the world's loop, logged as CSV and summed up (decision 43; `combat_feel.json`'s flow came from it) |
| `stat_probe.gd` | Read-only stat-scaling probe on copies of valley_run's checkpoints (`docs/research/stat_scaling_research.md`) |
| `check_scripts.gd` | Loads every script so parse errors surface in files the main scene does not reach |
| `extract_strings.py` | Moves player-facing text out of GDScript into `tools/data/ui_strings.json` |
| `ui_style_audit.py` | Measures the UI against `docs/ui_style_guide.md` (read-only) |
| `render_mockups.py` | Renders the HTML mockups in `docs/mockups/src/` and composes their figures |
| `wiki.py` | Writes the Item and Monster wikis in `docs/wiki/` from `data/` |
| `audit/` | Decision 45's read-only code audit (`docs/architecture/audit_45.md`, §8) |

The walk, trace and probe scripts say how to run them in their first lines.

## Captures

Every review picture in `docs/redesign/` that the game draws of itself comes from one tool, `capture/capture.tscn`. It
plays the real game (`scenes/main.tscn`) on saves of its own (`user://capture_<set>/`, never a player's and never the
Max Tester's) and needs a renderer:

```sh
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . \
    res://tools/dev/capture/capture.tscn -- <set> [--tag=before|after] [--only=<text>] [--out-root=<dir>]
godot --headless --path . res://tools/dev/capture/capture.tscn -- --list   # the sets, their rows and folders
godot --headless --path . res://tools/dev/capture/capture.tscn -- --lint   # every step known, its arguments counted
```

- `--tag=<t>` (and any other `--key=value`) fills `{key}` in the set's folder and picture names. A set that compares
  a before with an after takes `--tag` (its default is `after`).
- `--only=<text>` takes only the named rows whose name holds the text. The rows between still play, so the game is in
  the same state when the picture is taken.
- `--out-root=<dir>` writes under `<dir>` instead of `docs/`, for trying a change without touching the committed
  pictures. What a set reads (a mock, a before) still comes from `docs/` when `<dir>` has none.
- A bare `--<flag>` turns on the rows gated on it: `life --detail` (the close-ups), `pictures --pages`.
- The phone's shots: `-screen 0 2400x1080x24` and `--resolution 2400x1080` (the `hud_round` and `progression` sets
  name them `…_phone`).
- `--fixed-fps 60` (a Godot flag) steps the game one frame per 1/60 s however slow the machine is. A strip or a sheet
  of frames then shows the same instants on every machine.

### The sets

`capture.tscn -- --list` prints them. There are 32, and each is what one of the old one-off scripts took:

| Set | Folder under `docs/` | From |
|---|---|---|
| `phase1` `phase2` `phase3` `character` `drag_moves` `combat` | `redesign/phase1/` … `phase5/combat/` | the redesign's phases; decisions 32, 35, 38 |
| `phase4` `chapter2` `tutorial_foes` | `redesign/phase4/` | phase 4: every converted room, chapter 2, the tutorial's foes |
| `story` `night` `first_boss` | `redesign/phase5/story/`, `feedback/hollow_night/`, `feedback/first_boss/` | decisions 39, 42, 45 |
| `light` `terrain` `foliage` `sand_snow` | `redesign/terrain_v2/…`, `feedback/sand_snow/` | decisions 40 and 44, before and after |
| `life` `work_poses` | `feedback/living_world/`, `feedback/work_poses/` | decisions 43 and 44 |
| `quality` `people_scale` `monsters` `monsters_polish` | `feedback/character_quality/rollout/`, `people_scale/`, `monsters/` | decisions 42–44, before and after |
| `hud` `hud_round` `pictures` `progression` | `feedback/hud/`, `pictures/`, `progression/` | decisions 42, 43, 45 |
| `tutorials` `tutorials_late` `places` `sect` | `feedback/tutorials/`, `places/`, `sect/` | decisions 42–44 |
| `decision42` `decision42_route` | `feedback/combat/` | decision 42 |

`sect` starts from `topdown_tutorial`'s checkpoints after the Weapon Hall: run
`tests/topdown_tutorial.tscn -- --keep="The Weapon Hall,The Weapon Hall (Cloud)"` first.

### The registry

`capture/shots.gd` holds the sets. Each set has:

- `out`: its folder under `docs/`;
- `stage`: the steps that make its game (`new_game` for a new top-down character, `proto` for the prototype square,
  `weapon_hall`, `places_stage` or a checkpoint for the richer ones);
- `rows`: its rows, run in order.

A row is one picture, or a few, and what leads to it:

| Key | Meaning |
|---|---|
| `name` | The picture's name (`{tag}` filled in). A row with no name takes no picture; it only moves the game on. |
| `if` | Run the row only when a condition holds: `detail` (the flag was given), `tag=after`, `sect=jade`, `phone`, `!phone`. |
| `hour` | The clock pinned at this hour of the day (0.375 midday, 0.68 dusk, 0.87 night), and the light with it. Every set is at midday otherwise. |
| `room`, `cell`, `wait` | The room entered through the World authority, the cell the body stands on (facing the camera, the camera settled), and the frames it waits there (the set's `wait`, else 120). |
| `foes`, `turned`, `fight` | `[[def, offset in cells]]` set round the cell. `turned` sets them on the player. `fight` is the number of frames played with the body kept whole (`[n, false]`: not kept). Without `fight`, the row waits 20 frames. |
| `do` | Steps before the picture: `[name, args...]`. |
| `take` | The steps that take it. The default is the set's `take`, else `[["shot"]]`: the whole window, HUD and all. |
| `then` | Steps after it. |

A take's first argument is its picture's name. `"*"` is the row's own name, and a name may hold a folder
(`"closeups/*_1"`).

The steps are the functions `s_<name>` of the tool's scripts:

- `capture/capture_steps.gd` holds the shared steps, the ones a new row uses:
  - stand and move: `spot`, `start`, `arena`, `load`, `portal`, `beside`, `face`, `move`;
  - act: `attack`, `aim_attack`, `aim_technique`, `jump`, `dodge`, the HUD's `press`, `drag`, `release`;
  - play: `fight`, `timeline` (steps on given frames, crops kept for a sheet), `frames`, `tick`;
  - set the character: `gear`, `equip`, `give`, `unlock`, `set`, `quests_done`, `flag`, `effects`;
  - the clock: `hour`, `weather`;
  - pages and talk: `open_page`, `talk`, `choose`;
  - the story: `scene_at`, `until_idle`;
  - takes: `shot`, `world` (the world alone, x2), `detail` (a quarter of the screen round the body, x2), `view_x4`,
    `closeup`, `region`, `whole_room`, `strip`, `sheet`, `panels`, `pairs`.
- `capture/capture_scripted.gd` holds the scripted steps: the stages, and the loops ported from the old scripts that
  wait on the game (the eel's fight, a worker's pose, a staged and frozen scene, the foes' lineups, the tutorials'
  tours).

Each step does what the old script did, call for call and frame for frame, so its pictures are framed as they were.

### Adding a capture

A new picture is a row, not a function.

- **A room under the HUD, at dusk:**
  `{"name": "05_marsh_dusk", "hour": 0.68, "room": "rm_marsh_edge", "cell": Vector2(30, 14)}`
- **The same, with foes fighting the player and the world alone at x2:**
  `{"name": "06_marsh_fight", "room": "rm_marsh_edge", "cell": Vector2(30, 14), "foes": [["reed_otter", Vector2(3, 2)]], "turned": true, "fight": 120, "take": [["world"]]}`
- **A page:**
  `{"name": "07_bag", "do": [["open_page", "inventory"], ["frames", 60]], "then": [["close_pages"]]}`

A new review is a new set: its `doc` line, its `out` folder, a `stage` (usually `[["new_game"], ["frames", 360]]`, so
a new game's first notices have gone) and its rows.

Run `-- --lint`, then the set with `--out-root=/tmp/…` until the pictures are right, then into `docs/`. Only when a
picture needs something no step can do (a loop that waits on the game) does a new `s_<name>` go into
`capture_scripted.gd`, with its comment saying what it waits for.

### Reproducing a picture

Two runs of a set frame every picture the same: the camera, the body and its pose, the HUD, the pages and the crops.
What moves by itself can differ between runs:

- the foes' wander, since a new account's random seed comes from the clock;
- whatever the game draws by the wall clock: the water's frames, the grass and trees swaying, a lamp's flicker, and
  the frame on which a sheet finishes loading on its thread.

Decision 45's comparison pinned the clock and the random seed and ran at `--fixed-fps 60`. Then only the wall-clock
things differed. The old scripts and this tool gave byte-identical pictures wherever those were out of frame: 245 of
531 (see the changelog).
