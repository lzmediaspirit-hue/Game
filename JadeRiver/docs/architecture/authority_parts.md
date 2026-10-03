# Authority parts

Roadmap decision 45, phase 2 (`docs/architecture/audit_45.md` §7). A large authority is split into parts. The
authority stays the one owner of its state and the one name the rest of the game calls. Its parts do the work of its
sections. Four authorities use the pattern:
- `CombatAuthority` (S8);
- `WorldAuthority` (S9);
- `CraftingAuthority` and `ProgressionAuthority` (S10).

## The shape

- **The authority's file keeps:**
  - its state, that is every `var` that the save, the views or the tests read;
  - `intents`, `handle`, `subscribe` and `tick`;
  - for Combat, the core flow as well: the attacks, hits and damage, and the `apply_*` commands;
  - a one-line forwarder for every public method that moved into a part.
- **A part** does the work of one section of the authority, in its own script, and holds no state of its own. The parts
  live in a folder named after the authority, for example `scripts/simulation/authority/combat/` for
  `combat_authority.gd`.
- **A part's file name is its class name in snake_case, prefixed with the authority's name:**
  `authority/<name>/<name>_<part>.gd`. For example, `combat/combat_flight.gd` holds `class_name CombatFlight`, and
  `crafting/crafting_garden.gd` holds `CraftingGarden`.
  - `contract_tests` and the event contract find scripts by file name alone, and so do the audit scripts.
  - The prefix keeps every file name unique, so `combat_talismans` and a crafting part for talismans can both exist.
  - The data build stops if two scripts share a file name (`tools/data/contract.py`).
- **Each authority has one small base for its parts,** `<name>_part.gd`: `CombatPart`, `CraftingPart` and
  `ProgressionPart`. It extends `RefCounted` and provides:
  - `_authority`, a weak reference to the authority, behind a typed getter named after it (`combat`, `crafting`,
    `progression`);
  - `game`, the Game autoload, as an authority has it;
  - `emit`, `ok` and `fail`, which work as they do in an authority. `ProgressionPart` also has `t` and `log_line`.
- **The authority makes one of each part in `_init`, passing itself.** It keeps each part in a typed member named
  after the part's file:

```gdscript
# combat_authority.gd
var flight: CombatFlight             # flight and the movement arts

func _init(g) -> void:
	super(g)
	flight = CombatFlight.new(self)

func stop_flight(actor_id: String, reason: String) -> void: flight.stop_flight(actor_id, reason)
```

```gdscript
# combat/combat_part.gd
var _authority: WeakRef   # weak: the authority holds its parts, and Game builds new authorities on every boot
var game

var combat: CombatAuthority:
	get: return _authority.get_ref()

func _init(authority: CombatAuthority) -> void:
	_authority = weakref(authority)
	game = authority.game
```

```gdscript
# combat/combat_flight.gd
class_name CombatFlight
extends CombatPart

func stop_flight(actor_id: String, reason: String) -> void:
	if not combat.flying.has(actor_id): return
	combat.flying.erase(actor_id)
	emit("flight_ended", {"actor": actor_id, "reason": reason})
```

## Why the back-reference is weak

The authority holds its parts. If a part also held its authority, the two would hold each other. `RefCounted` has no
cycle collector, so neither would ever be freed. `Game` builds new authorities on every boot (`reset_state`), and the
tests boot again and again, so each rebuild would leak the old authority with all its parts and state.

The weak reference breaks the cycle. When `Game` drops an old authority, it is freed, and so are its parts. A probe
that rebuilds the authorities finds the old `CombatAuthority` and its parts freed, and the new parts reaching the new
authority.

## The rules

- **State stays on the authority.** Parts read and write it through the getter, as `combat.<var>`. The save data does
  not change, and code that reads the state, such as `Game.combat.flying`, keeps working.
- **The authority is still the facade.**
  - Code outside the authority calls the authority, as before: other authorities, views, pages, tests and tools.
  - Every public method that moved into a part keeps a one-line forwarder on the authority, with the same name,
    arguments and result. In `combat_authority.gd`, the forwarders are the last section, "the parts' faces".
  - A static method gets a static forwarder, so `CombatAuthority.treasure_of` still works.
  - Some private helpers are called by name from tests and tools, such as `Game.combat._tick_projectiles`. They keep a
    forwarder under their old name, until S11 gives them public names. Inside their part they are already public.
  - To find them, grep `scripts/`, `tests/` and `tools/` for `<name>.<method>` and `<Name>Authority.<method>` for every
    moved method.
  - When code outside needs a part's method, add a forwarder. Do not call `Game.<name>.<part>`.
- **Inside the authority and its parts:**
  - `handle` routes intents to the public names, as before.
  - The authority's own flow, such as its tick, calls the parts directly: `flight.tick_flight(c, delta)`.
  - A part reaches the authority's state and methods through the getter (`combat.player_view(c)`). It calls a helper
    that another part keeps to itself on that part (`combat.projectiles.spawn_projectile(p)`).
  - Combat's parts also call the core's private helpers, such as `combat._apply_status_to_enemy` and
    `combat._dao_tier`. The authority and its parts are one owner. A contract rule against private calls between
    owners (S11) should allow those calls from inside `authority/<name>/`.
  - Parts do not reach into other authorities' parts. They call other authorities through `game.<authority>`.
- **Names.**
  - A moved method keeps its name, and drops its leading underscore when the authority or another part calls it. For
    example, the tick's `_tick_flight` became `flight.tick_flight`.
  - A helper that only its own part uses keeps its underscore.
  - A local variable must not share a part member's name. A local `blood` in `use_technique` hid a `blood` part, which
    is why that part is `blood_path`.
- **Order is behaviour.** The tick calls the parts in the order it called the sections before, and a moved function
  keeps its statements in their order. Random streams and event order depend on it.
- **The checks that name scripts see the part folders** (S10).
  - `tools/data/contract.py` (`with_parts()`) adds every script in `authority/<name>/` to that authority's system, so
    an `emit` that moved into a part is still the owner's.
  - After adding or renaming a part, run `python3 tools/data/build_data.py` and commit `data/event_contract.json`. Only
    the `files` lists of that system's events change.
  - `data_validation` reads the part folders when it looks for the authority that reports a `use_system` objective.
- **After adding a script,** run `godot --headless --path . --import`. The class cache then knows the new
  `class_name`, and Godot writes the script's `.uid` file. Commit the `.uid` file.
- **The side view.** Its branches (`grid() == null`) move as they are. Do not polish them: the side view is to be
  retired.

## Adding parts to an authority

1. Make the folder. Copy `combat/combat_part.gd` as `<name>/<name>_part.gd`. Replace `combat` and `CombatAuthority`
   with `<name>` and `<Name>Authority`.
2. Move a section into `<name>/<name>_<part>.gd`, which `extends <Name>Part`.
   - Prefix the authority's state and methods with `<name>.`.
   - Qualify the authority's static calls as `<Name>Authority.x`.
   - Point the authority's calls at the part.
3. Add a forwarder for every moved public method, and for every private one that code outside calls.
4. Import, rebuild the data, and run `tools/run_tests.sh`. Every suite's check count must stay the same.

## CombatAuthority's parts (S8)

`combat_authority.gd` went from 2,912 lines to 1,807. The core flow is 1,721 of those lines. The other 86 are the
parts' faces: 59 forwarders, 42 for public methods and 17 for private names that tests and tools call. The parts hold
1,308 lines.

| Member | File | Lines | What it holds | State it works on |
|---|---|---:|---|---|
| — | `combat_part.gd` | 28 | The base: the weak reference behind `combat`, `game`, `emit`, `ok` and `fail` | — |
| `flight` | `combat_flight.gd` | 143 | Flight (S18); the movement arts Plunge and Falling Leaf Glide (S43) | `flying`, `gliding` |
| `phantom` | `combat_phantom.gd` | 42 | Phantom Double (S48, the Soul line) | `decoys` |
| `sword` | `combat_sword.gd` | 132 | Natal overcharge, Sword Release, Sword Intent (S47); Killing Intent (S48), which fades in the same tick | `sword_released`, `sword_intent`, `killing_intent` |
| `swarm` | `combat_swarm.gd` | 83 | The sword swarm (S47 v1.1) | `sword_swarm` |
| `flute` | `combat_flute.gd` | 88 | The flute's held melody (S47 v1.1, the Music path) | `melody` |
| `heals` | `combat_heals.gd` | 97 | Heals over time on you and on allies, the healing song, the sect roles' support variants (S48) | `hots`, `ally_hots` |
| `blood_path` | `combat_blood_path.gd` | 52 | The Blood path's lifesteal and blood essence (S48) | `blood_essence` |
| `plates` | `combat_plates.gd` | 61 | Array Plates in a fight (S48) | `arrays` |
| `talismans` | `combat_talismans.gd` | 51 | Talismans used from the bag (S47) | `treasure_fx` |
| `projectiles` | `combat_projectiles.gd` | 136 | Every shot in flight: spawning, aiming on the plane, flying, hitting, the Mirror and the Gourd, the fan's return | `RoomRuntime.projectiles`, `treasure_fx` |
| `treasures` | `combat_treasures.gd` | 217 | The two Treasure buttons and their lingering effects, throwables and their bursts (G2), self-detonation (S47) | `treasure_fx`, `captured` |
| `revival` | `combat_revival.gd` | 68 | Being gravely wounded; revival at the shrine, with a talisman or with a fruit | `wounded` |
| `riders` | `combat_riders.gd` | 110 | What a landed blow carries after its damage: armour break, the fan's lift, the brush's talisman, Sense Lock and Soul Search, the Poison Body, weapon oils, and the Artifact Spirit's and the awakened weapon's skills | `searched`, `poison_touch`, `spirit_hits`, `awaken_hits` |

The core file keeps these sections:
- the state, the parts, `subscribe`, `handle` and the queries;
- views: the hit test, the player's and a foe's view, the grid and hit-stop;
- the player's attacks: basic attacks, techniques and their costs, guard, dodge, and the cancels;
- the tick;
- resolution, from a blow to a foe's damage;
- a foe's end: defeat, execution, a story's slaying, the eel's overwhelm and a boss's detonation;
- foes' blows and harm to the player: a foe's strikes, ground fire, the tribulation's bolt, hazards and
  `_damage_player`;
- the `apply_*` commands;
- the parts' faces.

## WorldAuthority's parts (S9)

`world_authority.gd` went from 2,321 lines to 430. Its facade is 106 one-line forwarders: 91 for public methods,
including the new `apply_loot_drop` (BUG-05), and 15 for private names that tests and `ObjectView` call. The parts
hold 2,133 lines.

| Member | File | Lines | What it holds | State it works on |
|---|---|---:|---|---|
| — | `world_part.gd` | 29 | The base: the weak reference behind `world`, `game`, `emit`, `ok` and `fail` | — |
| `ambush` | `world_ambush.gd` | 48 | Bandit ambushes on the road rooms (S48) | `ambush_cd` |
| `herbs` | `world_herbs.gd` | 87 | Rare herbs: ripening, their guardians and what stops a pick (S45) | `herb_clock`, `sensed_herbs` |
| `portals` | `world_portals.gd` | 204 | Portals and hidden ways, the prototype's gate, the open ways and the route, teleports, the shrine a fall wakes you at, Spirit Sense and the Wandering Eye | `debug_open_ways`, `sensed_herbs` |
| `arrays` | `world_arrays.gd` | 95 | The sect's transfer arrays (decision 42) | the character's flags |
| `objects` | `world_objects.gd` | 165 | Whether a room object shows and is open; its states and regrowth; blows on jars and training posts; gravity switches; shrines attuned in passing; the first Spirit Fruit's announcement | `debug_open_ways`, `chases` |
| `context` | `world_context.gd` | 269 | `interact`, and the context button with its ranks and verbs | `chases` |
| `loot` | `world_loot.gd` | 233 | Beast ranks and cores (S46), the roll on a kill, starter gear, the drops on the ground and picking them up | `RoomRuntime.loot` |
| `races` | `world_races.gd` | 164 | The rooftop chases and the timed routes (S43 rule 15) | `chases`, `runs` |
| `hazards` | `world_hazards.gd` | 213 | Room hazards (S17), hazard volumes (S43) and the drift they push | `RoomRuntime.hazards` |
| `starsea` | `world_starsea.gd` | 41 | The Starsea voyages (S18) | `voyages` |
| `room_events` | `world_room_events.gd` | 227 | Room events: waves, timed spawns, the lantern, kill-to-win, and the way on | `RoomRuntime.event`, `voyages` |
| `nests` | `world_nests.gd` | 102 | The Beast Kings' nests, the Beast Tide and the Beast Trial Grove (S46) | the character's cooldowns |
| `tower` | `world_tower.gd` | 87 | The Trial Tower (S49) | the character's `tower` |
| `idle` | `world_idle.gd` | 198 | Idle rooms, auto-hunt, auto-path and the direction mark | `auto_hunt`, `auto_paths`, `auto_check`, `guide_cache` |

The authority's file keeps these sections:
- the state, the parts, `intents`, `subscribe` and `handle`;
- the room's lifecycle: `load_room`, `enter_world`, `enter_grid_room`, the arrival, `grid_for` and the ground;
- the character's memory of a room: `room_mem`, `slain_foes` and the foes slain and returned;
- the tick;
- the facade, and the old private names at its end.

**Its part members are untyped.** This is the one difference from the shape above, and it is deliberate:
- With the members typed, the parts and `WorldAuthority` resolve in a cycle while `Game` boots.
- Godot 4.5's analyzer then leaves `ActorState`'s untyped members, such as `plane`, unresolved for every script it
  compiles afterwards. `rules_tests.gd` fails to parse at `_jump_to` (`var v := (toward - st.plane)…`), and the suite
  hangs on the await of its first broken call. A one-line script that does the same fails in the same way.
- Which members trip it depends on the graph. A member named `events` alone did it, as did `room_events`
  (`WorldRoomEvents`) with its real content.
- Untyped members keep the parts out of `WorldAuthority`'s interface. Each one's comment names its class.
- The parts still type their back-reference, `world: WorldAuthority`. The other authorities' typed members pass today.
  If a test script ever fails to parse with "Cannot infer the type" on an untyped member, look for such a cycle first.

The member for room events is `room_events`, not `events`, because `ActorState` already has an `events` member.

Its brief asked S9 to group the side-view branches where that was free. Each of them asks `WorldAuthority.side_view(rt)`
(13 sites) or finds `grid_for` null (7 sites), so retiring the side view can find them all.

Crafting's and Progression's parts are listed in the S10 entry of `docs/CHANGELOG.md`.
