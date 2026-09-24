# Jade River: The Broken Seal

A wuxia cultivation action RPG for **landscape mobile**, built in **Godot 4.5** (GDScript, GL Compatibility renderer). 2D pixel art, side-scrolling, with walkable depth on the ground *and* on raised roofs and bridges.

Start as a novice disciple in a threatened river town. Practise sword or spear, gather ore and herbs you can see in the world, craft pills and weapons, meditate and break through the realms, repair a broken seal, and defeat the three guardians of the Broken Seal campaign.

All art is procedural pixel art generated at startup by a small software rasterizer (`scripts/art/`). The project has no external image assets.

## Running

1. Install [Godot 4.5](https://godotengine.org/download) (standard build, not .NET).
2. Open `project.godot` in the editor and press **F5**, or run `godot --path .` from this folder.

### Exporting to Android

`export_presets.cfg` has an **Android** preset (arm64, landscape, immersive) and a **Linux** preset.
In the editor, install the Android export templates, set your Android SDK and debug keystore under *Editor Settings → Export → Android*, then use *Project → Export → Android*.

## Controls

| Action | Touch | Keyboard |
|---|---|---|
| Move (left/right, toward/away from the camera) | Left thumb stick (floating) | WASD / arrows |
| Jump · drop through a bridge | Jump · stick down + Jump | Space · S + Space |
| Attack (3-hit combo) | Attack | J |
| Step (dash) | Step, or swipe Attack sideways | K |
| Guard | Shield, or swipe Attack upward and hold | L / Shift |
| Arts 1–3 | Art buttons around Attack | 1 2 3 (or U I O) |
| Interact (talk, mine, harvest, fish, stations, portals) | Context button | F / E |
| Pill quickslots | Two slots beside the mode switch | Q / R |
| Combat ↔ Cultivation mode | Bottom-centre switch | Tab |
| Meditate (Cultivation mode, safe spots) | Meditate | G |
| Map · Systems menu · Inventory | Top-right buttons | M · Esc · B |

The touch layer reads raw multi-touch events, so moving, jumping and attacking work at the same time. Settings include left-handed layout, button size and joystick anchor.

## What's in the game

- **Three chapters, six areas.** Jade River Town ↔ River Outskirts → Lantern Haven ↔ Whispering Bamboo → Cloudrest Court ↔ Black Wind Monastery, with mentors Elder Wen, Archivist Suyin and Keeper Tao. The bosses are the Black River Captain, the Reed Sentinel and Master Qiu, each with telegraphed patterns (dash, floor shockwaves, reed spikes, Qi fans, blink, expanding rings). The authored ending leaves the valley open for more play afterwards.
- **Shared x / depth / height movement** (`scripts/world/physics.gd`). Every surface (ground, stair, terrace, roof, bridge) is a bounded top face that you walk across with the same four-direction stick. Stairs link levels. Solid terraces act as walls, and bridges can be walked under. Down + Jump drops through one-way bridges. Melee, projectiles, enemies and resource nodes all check depth and height, so you can't hit a foe under a bridge or mine a vein from the level below.
- **Resources you can see in the world.** Copper, iron and jade veins, Spirit Shard, Vein Crystal and Source Crystal nodes, Dewleaf, Moon Lotus and Spirit Ginseng, and fishing piers for carp, eel and koi. Each node has a harvest channel that moving or taking damage cancels, plus a respawn timer, a profession level gate and a tool requirement. Enemies drop beast hide and cores.
- **Crafting at stations.** The forge smelts bronze, steel and jade alloy and forges sword/spear tiers plus a steel pick. The alchemy furnace brews Mending, Clear Qi, Insight and Foundation pills. The research desk teaches permanent doctrines. You can read recipes anywhere, but you can only craft at the right station.
- **Cultivation.**
  - Five realms: Mortal → Qi Awakening → Foundation → Golden Core → Nascent Spirit, using the baseline thresholds 2/30/0, 4/100/1, 7/250/2 and 10/500/3.
  - Insight gates breakthroughs. Qi essence is a separate currency spent on meridians and body tempering. The combat Qi bar is separate again and refills.
  - Six meridians, two more accessible per realm.
  - Body tempering has Endurance, Guard and Mobility branches.
  - Soul milestones are earned by discovering resource sites. The first reveals nodes on the minimap.
  - Two Dao principles (River and Ember) change how your arts behave.
  - Meditation is a field action that only works at safe spots. Moving, taking damage or an enemy approaching interrupts it, and a partial cycle gives no reward.
  - Major breakthroughs are a short three-wave Inner Sea trial. Failing costs nothing.
- **Weapon mastery.** Sword and spear each have their own technique tree (e.g. Spear Thrust → Long Thrust → Guarding Spear / Dragon Art / Flowing Spear). Mastery grows from real hits, and switching weapons keeps both records. There are also realm arts (Nova, Mend), three disciplines (Blade Adept, Spear Warden, Spirit Sage) and a three-slot art hotbar.
- **Formation seal puzzle** in Whispering Bamboo: set Spirit Shards in the altar, then touch four runes in order. One rune sits on a raised step.
- **Systems.**
  - Systems hub, plus Character, Cultivation, Inventory, Skills, Gathering and Workshop pages.
  - Journal: story, commissions, guidance and lore.
  - Illustrated World Map with area dots, route lines, and Areas / Resources / Objectives overlays. *Track* pins a route. *Travel* works only from a safe shrine.
  - Shop, three-slot shared storage, and daily-capped commissions.
  - Offline assignments, capped at 8 h.
  - Defeat screen offering a free sanctuary revive or a paid on-site revive.
- **Saves.** Three character slots in `user://jaderiver_save.json`, written atomically. Save format v4 migrates legacy v1–v3 (0.7) saves: realms, insight, gear, mastery, quests and bank are kept, a backup is written, owned higher-grade weapons are credited, and a save from a newer version is left untouched.

## Architecture

```
scripts/data/content.gd   stable content tables (items, realms, abilities, recipes, enemies, nodes, areas, chapters)
scripts/core/state.gd     profile creation, derived stats, requirement checks, save migration
scripts/core/rules.gd     every state-changing action (harvest, craft, breakthrough, talk, equip, trade…)
scripts/core/game.gd      autoload: save/load and the single command boundary Game.perform(action, args)
scripts/world/            physics (surfaces), actors, input state, world simulation + pixel renderer
scripts/art/              Painter rasterizer; icons, sprites, backgrounds, props, world-map painting
scripts/ui/               theme kit, HUD, multi-touch controls, menus/pages, title & disciple creation
tests/                    headless rules tests, scripted smoke / campaign / area-tour runs
```

UI and world code never change coins, items or ranks directly. They call `Game.perform`, which snapshots state, runs the rule, and rolls back if the rule fails. This is the boundary a future authoritative server would replace.

## Tests

```sh
GODOT=/path/to/godot tests/run.sh                                   # rules + migration (headless)
godot --headless --path . tests/campaign.tscn                        # boss arena, trial, seal, travel, defeat
godot --headless --path . tests/tour.tscn                            # walk and fight through all six areas
xvfb-run godot --path . --rendering-driver opengl3 tests/smoke.tscn  # scripted play + screenshots in user://shots/
```

## Roadmap status

Phases 0–7 of the design roadmap (the single-player cultivation vertical slice) are implemented in this offline build. Phases 8–9 (accounts, a server-authoritative multiplayer service, parties, sects, trading) are not: this is a single-player game, and nothing in it is presented as online. Audio is not implemented yet.
