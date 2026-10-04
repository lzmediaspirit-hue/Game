# The shell: main.gd, the page registry and the debug flags

Roadmap decision 45, phase 2, slice S7 (`docs/architecture/audit_45.md` §2.2, BUG-07). `scripts/main.gd` had 1,061
lines, 510 of them one function of preview and debug flags. It now has about 520 and does only the shell's work. The
pages it opens are in a registry, and the flags are in a script of their own that a player's game never loads.

## main.gd

`scripts/main.gd` is the root of `scenes/main.tscn`. It routes intents and signals and keeps no rules:
- the boot, then the title, the character selection and the creator (`ShellScreens`);
- the world: the room's view, the HUD, the moments and the staged scenes, mounted and unmounted together;
- the top-down game and the prototype room on saves of their own;
- the stack of pages, and Back (Escape on a keyboard);
- the fade, the app pausing and resuming, and quitting.

## The page registry

`scripts/shell/page_registry.gd` is the table of every page the shell opens.
- `PAGES` maps a page id to the script that draws it.
  - Ids that share a script are one page opened on another of its views. Examples are the Codex's Collection, Seasons
    and Achievements, the nine crafts benches, and the Cultivation page's Seclusion, Heart and Body.
  - `script_of(id)` gives an id's script, or `""` when the id is no page.
  - `scripts()` gives every page script in the table's order. `PageWarmer` compiles them in that order from the title
    screen on, one at a time.
- `main.gd` keeps `const PAGES := PageRegistry.PAGES`. The tests and tools that read `load("res://scripts/main.gd").PAGES`
  still work.
- `tools/data/tutorials.py` reads the table's text into `tutorials.json`'s page map. `tests/tutorials.gd` checks
  that the map matches the table. So keep one `"id": "res://scripts/ui/pages/<file>.gd",` a line.
- The registry holds no titles or unlocks. A page sets its own title and tabs in `_init`. The Menu's entries and the
  HUD's reveals say what is unlocked.

`main.open_page(id, args)` opens the pages:
1. An id that starts with `_` is one of the shell's own actions (`_shell_action`), not a page:
   - `_harvest`: the HUD's hold-and-tap harvest of a rare herb (a dialogue choice, "Pick it");
   - `_exit`: the Menu's Save & Exit;
   - `_tour`: a page's "?" plays its tour again;
   - `_import`: Settings replaces the saves with an export;
   - `_switch`: the Characters page and the Roll-Call play another character.
2. An id with no script in the registry logs "coming in a later update" on the HUD.
3. A page that is already open comes to the front with the new arguments.
4. Otherwise the page's script is taken from its loading thread, or loaded, and the page opens on top. The HUD is
   blocked while any page is open, and the Quest authority hears `report_page_opened`.

A page's `closed` signal closes it, and its `navigate` signal opens another id. Back first skips a tutorial tour that
dims the screen, then closes the top page. On the play screen with no page open, Back opens the Menu once the Menu
button is revealed. A room entered closes every page.

**To add a page:** add its row to `PAGES`, then run `python3 tools/data/tutorials.py` (or `build_data.py`) so the
tutorials' page map follows, and give the page its tour.

## The debug flags

`scripts/dev/debug_args.gd` holds the preview and debug flags of the command line. README.md ("Preview and debug
arguments") and the review folders' READMEs under `docs/` show them in use:

```sh
godot --path . -- --preview-world --room=lf_village --give=herbal_tea:3 --open-page=inventory --capture --shot=bag
```

- **Inert in a player's game.** `main.gd` loads the script only when the game starts with arguments after `--`. This
  is the same guard as before. An APK has no arguments, so the script is never loaded. Any argument also puts the game
  on `user://preview_saves/`.
- **Not in `scripts/shell/`.** The shell never writes game state, and `contract_tests` checks that rule over
  `scripts/shell/`. The flags exist to write state: the realm set by hand, foes placed, the clock moved.
- **The Max Test build is not a flag.** Its custom feature `max_test`, with `--max-character` as its editor spelling,
  stays in `main.gd`'s boot.

A run goes in steps. Each step is a table of rows read in a fixed order:

| Step | Table | Flags |
|---|---|---|
| Before `Game.boot` | `before_boot` | the preview saves, `--load=`, `--log-events` |
| The screen | `OPEN`, `ROOM` | `--topdown-proto`, `--topdown-tutorial`, `--preview-selection`, `--preview-create`; `--room=`, `--text-size=` |
| The preview character | `_enter`, `PLACE` | `--preview-world`, `--load-slot` or a room: the character made (or the loaded one), placed (`--at=`, `--unlock-all`, `--debug-sect`), in the world |
| The state shown | `STEPS` | the character and the room (`--give=`, `--foe=`, `--realm=` …), pages and talk (`--open-page=`, `--tap=`, `--talk=` …), riding and flight, powers, the HUD (`--toggle=`, `--fan=` …), the moments (`--moment=`, `--breakthrough`) |
| The picture | `CAPTURE` | with `--capture`: `--auto-path=`, `--auto-hunt`, `--wait=`, `--hazard=`, then `../<shot>-preview.png` and quit |

A row is `[flag, handler, needs]`:
- `"--name="` takes a value, `"--name"` takes none, and `"--name[=]"` takes either.
- In an `EACH` table, a row runs once for each time its flag is given, in the order the flags are given. In a `ONCE`
  table, a row runs once if its flag is given (or any flag of a list), in the table's order.
- The handler is a function of the script. It gets the whole argument (`"--foe=ashborn_raider:2"`), and `_val(a)` is
  the text after the `=`. The row holds the function itself, never its name, because `contract_tests` forbids calling
  a method by a name. That is why the tables are variables rather than constants.
- `needs` names what must be there for the row to run: `active`, `actor`, `sect`, `room`, `world`, `hud`, `moments`,
  `page` or `technique_preview`. A row that lacks one is skipped.
- A handler that waits on a timer holds every row after it, so the picture is taken once everything before it has
  played.

**To add a flag:** add a row to the table whose step it belongs to, and a small handler. Give the handler a doc line
in the flag's own spelling.

**Dropped in S7.** Nothing in `tools/`, `tests/`, `docs/` or the capture registry used these flags: `--body=`,
`--learn=`, `--physique=`, `--set-piece=`, `--tribulation` and `--test-saves`. The last never did anything of its own,
because any argument already chose the preview saves.

**Dropped in S12a, with the side view.** `--topdown` (every character plays on the grid now) and `--cast=` (it drew a
cast through the side view's `World.preview_cast`; the Techniques page's preview, `--open-page=techniques` with
`--preview-t=`, draws a cast now). `--fly` takes off on the grid, as a held jump does from Cloud Stride 1.
`--capture` waits on the clock (2.5 s, or just past a moment's t). The capture registry (`tools/dev/capture/`) takes
the review pictures.

## The side view in main.gd

The side view is retiring (decision 45). `main.gd` keeps what it does for it in its last section, "side view
(retiring)". Its calls elsewhere carry a `# side view` mark:
- `const World`, the side view's script;
- `_side_view()`, which `_add_world_view` mounts when the room has no top-down layout;
- `_backdrop_follows_world()`, which shows the river backdrop behind the side view and hides it under the top-down
  view. `unmount_world` clears it.
- `_swap_world_view()`, which `_on_game_event` calls on `room_entered` to swap the view when a character walks into a
  room of the other kind.

`_add_backdrop()` is in the same section. The backdrop is also the title screens' sky, so it stays until those screens
have one of their own. In `debug_args.gd`, `_dress` (the avatar's outfit), `_cast`, `_fly` and `--capture`'s frame
count are side-view only and marked so.
