# Jade River — the Complete Valley (Act I)

A 2.5D side-scrolling wuxia/xianxia cultivation RPG built in Godot 4.5.1 (GL Compatibility,
1280×720, touch-first with full keyboard support). You begin as a fisher's child in Lotus Ferry
with bare fists and no Qi. The Prologue teaches one thing at a time: talking, carrying, jumping,
money, healing, fighting. After a night the village will not forget, you step onto the cultivation
ladder. Act I climbs from Bone Forging through Qi Kindling, Qi Unfurling, Heart Tempering, Cloud
Stride and Spirit Awakening to Heaven Glimpse and the Ascension Gate.

Open `project.godot` in Godot 4.5.1 and press F5. The first import rebuilds the generated caches.

## What is in the valley

| | |
|---|---|
| Rooms | 71 hand-built rooms in 20 regions: Lotus Ferry, Willow Path, Stoneford, both training sects, Stonewall Quarry, the Reed Marsh and Greyreed Hamlet, the Bamboo Grove, Crane Falls, the Caravan Road, Mudwater Hideout, Cleansing Peak, Deepwater Bend, the Drowned Shrine, Whitewater Gorge, the Crane Cliffs, the Misty Peaks, the Summit Ridge and the Hidden Vale |
| Story | 115 quests: the 10-quest Prologue, 12 Act I chapters of main story, a guided quest for every system as it unlocks, companion, village and merchant side stories, daily sect missions |
| People | 62 NPCs in dyed outfits, 4 AI companions, 7 spirit-animal species |
| Combat | 53 monsters (normals, elites, field bosses, dungeon and story bosses), 30 techniques, 25 Daos, weapon families with their own combos |
| Cultivation | 89 realm stages with their requirements, 9 methods, meridians, purity, stability, injuries, offline seclusion |
| Crafts | Herb gathering, mining, fishing, cooking, alchemy, the forge, formations and array plates, appraisal, healing, puppetry, research, teaching |
| Your sect | Found it at four character slots: buildings that appear as they are built, NPC disciples, expeditions, raids to defend |

No cultivation, no Qi: the QI bar appears only when the pool exists (Bone Forging 7). Weapons appear only
at the Weapon Hall (Bone Forging 3). Every HUD button is revealed by the system that introduces it.

## Controls

| Action | Touch | Keyboard |
|---|---|---|
| Move (horizontal and depth) | Left joystick | WASD / arrows |
| Sprint | Keep moving sideways for 2 s | Hold Shift |
| Jump / double jump | Jump | Space |
| Fly (Cloud Stride 1): take off, climb, descend | Jump again at the top of a double jump; hold Jump to climb, hold Guard to descend | Space; hold Space / K |
| Attack / context action (talk, gather, pray, travel) | Attack button (changes with context) | J / Enter, F for the context |
| Guard / dodge dash | Guard button: hold to guard, tap to dash | K: hold / tap |
| Techniques | Skill slots | 1–8 |
| Cultivate | Cultivate button | C |
| Quick-use item | Gourd button | Q |
| Menu, Bag, Map, Quests, Pet, Cultivation | HUD buttons | Tab, I or B, M, L, E, P |
| Back / close page | System back | Esc |

## Architecture in one paragraph

Five layers: data (`data/*.json`, built by `tools/data/`), state (plain objects with stable IDs),
rules (pure formulas), authorities (the only writers of state, one per system) and presentation
(scenes and pages that only send intents). Every change goes through `Game.submit(intent)`;
authorities validate, change their own state and emit events on `GameEvents`; other systems react
to events. Randomness comes from named `Rng` streams, time from `Clock`. See `docs/architecture.md`.

## Building the data

The game reads only `data/`. Authoring modules in `tools/data/` generate it:

```
python3 tools/data/build_data.py            # everything
python3 tools/data/build_data.py world story # just some modules
```

Player-facing text lives in `tools/data/ui_strings.json` (merged into `data/strings/en.json`) and is read
with `Tx.t("key")`; `python3 tools/dev/extract_strings.py` moves any new literal out of the scripts.

Modules: realms, stats, items, techniques, enemies, world, story, economy, crafts, contract. Each validates its
own references; `tests/data_validation` checks the whole set again inside Godot.

## Testing

```
tools/run_tests.sh                 # Linux/macOS (GODOT=/path/to/godot)
./Test.ps1 -GodotPath <godot>       # Windows
```

| Suite | What it proves |
|---|---|
| `engine_tests` | Movement, avatar, surfaces, saves (3,660 checks) |
| `data_validation` | Every ID resolves, known effect and requirement kinds, appearances, dyes and icons exist, every room reachable, portals link both ways, spawns on surfaces and clear of portals |
| `rules_tests` | Formulas at the spec's sample values (damage, attunement, mastery, risk), same-seed replay, offline caps, no offline breakthroughs, spirit animal stage gates, the weekly mission, save recovery from `.bak` |
| `balance_sim` | A rate-based bot plays the data to Heaven Glimpse 3 with the real rules and meets the pacing table (±15%); the next gear upgrade is affordable after 1–2 hours at Levels 15 and 25 (`data/balance.json`) |
| `perf_tests` | Every room loads in under 0.3 s, every page opens in under 0.15 s, a frame with fifteen monsters fits 60 fps (CPU, headless) |
| `contract_tests` | Every event in the Part 4 catalogue is emitted only by its own system and has a reactor (`data/event_contract.json`); no player-facing text is written in the scripts |
| `prologue_run` | A scripted Prologue to Bone Forging 2 with the HUD reveal order |
| `valley_run` | The whole of Act I from a new character to the Ascension Gate, through intents only (about a minute) |

`valley_run` saves a checkpoint at the start of each section, so one part can be replayed:
`godot --headless --path . res://tests/valley_run.tscn -- --from=ht5 --only --verbose`.

The art rules in `AGENTS.md` still apply to every new item and animation (`Validate-Animations.ps1`).

## Preview and debug arguments

```
godot --path . -- --preview-world --room=hv_sect_grounds --unlock-all --debug-sect
godot --path . -- --preview-world --room=lf_village --talk=washer_mei --shot=name --capture
```

`--preview-world` enters with a preview character, `--room=` starts in a room, `--unlock-all` opens
every system, `--debug-sect` gives a founded sect with all buildings, `--fly` takes off, `--ride` mounts a crane, `--give=item[:count[:quality]]` fills the bag, `--at=x,y` starts at a point in the room, `--open-page=<id>[:tab]` and
`--talk=<npc>` open UI, `--log-events` prints the event stream, `--capture` saves `../<shot>-preview.png`.

## Art and credits

Characters use the layered avatar engine (body, hair, garments in ten dyes, shoes, weapons, hats,
capes) with pose-registered sheets; enemies and NPCs are drawn with the same engine or with the
creature sheets in `art/creatures/`. Backdrops, props, UI and audio are original to this project.
Character attribution: `data/LPC-CREDITS.txt`. Font licence: `art/fonts/OFL.txt`.
