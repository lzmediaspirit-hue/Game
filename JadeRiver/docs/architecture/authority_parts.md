# Authority parts

Roadmap decision 45, phase 2 (`docs/architecture/audit_45.md` §7). A large authority is split into parts. The
authority stays the one owner of its state and the one name the rest of the game calls. Its parts hold the sections
of its rules around the core flow. `CombatAuthority` is the first to use the pattern (S8); `WorldAuthority` (S9) and
`CraftingAuthority` and `ProgressionAuthority` (S10) follow it.

## The shape

- **The authority's file keeps:**
  - its state, that is every `var` that the save, the views or the tests read;
  - `intents`, `handle`, `subscribe` and `tick`;
  - the core flow of its system. For Combat, that is attacks, the tick, hits and damage, and the `apply_*` commands.
- **A part is one section of the authority's rules** in its own script. The parts live in a folder named after the
  authority, `scripts/simulation/authority/combat/` for `combat_authority.gd`.
- **A part's file name is its class name in snake_case, prefixed with the authority's name:**
  `authority/<name>/<name>_<part>.gd`. For example, `combat/combat_flight.gd` holds `class_name CombatFlight`, and
  World's parts are `world/world_*.gd`.
  - Some tools key scripts by base name alone, such as `contract_tests`' sources, the event contract and the audit
    scripts.
  - The prefix keeps every base name unique, so `combat_talismans` and a crafting part for talismans
    (`crafting_talismans`) can both exist.
- **Each authority with parts has one small base in its folder.** Combat's is `combat/combat_part.gd`,
  `CombatPart extends RefCounted`, with:
  - `game`, the Game autoload, as an authority has it;
  - `combat`, the authority, a getter that reads `game.combat`;
  - `emit`, and the static `ok` and `fail`, the same as `Authority`'s. Code moved into a part therefore reads as it
    did.
- **The authority makes its parts in `_init`.** It keeps each part in a typed member named after the part's file:

```gdscript
var flight: CombatFlight             # flight and the movement arts

func _init(g) -> void:
	super(g)
	flight = CombatFlight.new(g)
```

```gdscript
class_name CombatFlight
extends CombatPart

func stop_flight(actor_id: String, reason: String) -> void:
	if not combat.flying.has(actor_id): return
	combat.flying.erase(actor_id)
	emit("flight_ended", {"actor": actor_id, "reason": reason})
```

**Why a part reads its authority through `game`.** A part could keep a reference to its authority instead. But
`RefCounted` has no cycle collector, so a part and its authority holding each other would never be freed.
`Game.reset_state` builds new authorities on every boot, and the tests boot again and again, so every rebuild would
leak the old authority with all its parts and state. The getter costs one call each time a part uses it.

## The rules

- **State stays on the authority.** Parts read and write it as `combat.<var>`. The save data does not change, and
  code that reads the state, such as `Game.combat.flying`, keeps working.
- **The authority is still the facade.**
  - Code outside the authority calls the authority, as before. That means other authorities, views, pages, tests and
    tools.
  - Every method that such code calls still exists on the authority, with the same name, arguments and result. For a
    method that moved, it is a one-line forwarder in the authority's last section, "the parts' faces". This includes
    the underscore names that the tests call, such as `Game.combat._tick_projectiles`. A static method gets a static
    forwarder, so `CombatAuthority.treasure_of` still works.
  - A method that only an intent reaches, such as `start_flight`, is not forwarded. `handle` calls the part.
  - The authority and its parts call a part directly, for example `flight.stop_flight(...)` and
    `combat.projectiles.spawn_projectile(...)`.
  - When code outside needs a part's method, add a forwarder rather than calling `Game.combat.<part>`.
  - To find what needs a forwarder, grep `scripts/`, `tests/` and `tools/` for `combat.<name>` and
    `CombatAuthority.<name>` for each moved method.
- **Names.**
  - A moved method keeps its name. It drops its leading underscore when the authority or another part calls it: the
    tick's `_tick_flight` became `flight.tick_flight`.
  - A helper that only its own part uses keeps its underscore.
  - A local variable must not share a part member's name. A local `blood` in `use_technique` hid a `blood` part,
    which is why that part is `blood_path`.
- **The authority and its parts are one owner.** A part may call its authority's underscore helpers, such as
  `combat._apply_status_to_enemy` and `combat._dao_tier`. A contract rule against private calls between owners (S11)
  should allow `combat._x(` from inside `authority/combat/`.
- **Order is behaviour.** The tick calls the parts in the order it called the sections before, and a moved function
  keeps its statements in their order. Random streams and event order depend on it.
- **Parts do not reach into other authorities' parts.** They call other authorities through `game.<authority>`, as
  before.
- **Events.**
  - The event contract lists the scripts that may emit each system's events. It is `data/event_contract.json`, built
    by `tools/data/contract.py`, and `contract_tests` checks the code against it.
  - The builder's `with_parts()` (S10) adds every script in `authority/<name>/` to that authority's system, so an
    `emit` that moved into a part is still the owner's. It also asserts that the base names are unique.
  - After adding or renaming a part, run `python3 tools/data/build_data.py` and commit `data/event_contract.json`.
- **After adding a script:**
  - Run `godot --headless --path . --import`. The class cache then knows the new `class_name`, and Godot writes the
    script's `.uid` file. Commit the `.uid` file.
- **Tests that read the authority folder.** `data_validation`'s `_system_reported` looks for the authority that
  reports a `use_system` objective. It walks the part folders too (S10), so a `system_used` that moved into a part
  still counts.
- **The side view.** Its branches (`grid() == null`) move as they are. Do not polish them: the side view is to be
  retired.

## Adding parts to an authority

1. Make the folder. Copy `combat/combat_part.gd` as `<name>/<name>_part.gd`, and replace `combat` and
   `CombatAuthority` with `<name>` and `<Name>Authority`.
2. Move a section into `<name>/<name>_<part>.gd`, which `extends <Name>Part`.
   - Prefix the authority's state and methods with `<name>.`.
   - Qualify the authority's static calls as `<Name>Authority.x`.
   - Point the authority's calls at the part.
3. Add a forwarder for every moved method that code outside calls, as above.
4. Import, rebuild the event contract, and run `tools/run_tests.sh`. Every suite's check count must stay the same.

## CombatAuthority's parts (S8)

`combat_authority.gd` went from 2,912 lines to 1,798. The core flow is 1,721 of those lines, and the parts' faces are
the other 77 (50 forwarders). The parts hold 1,303 lines.

| Member | File | Lines | What it holds | State it works on |
|---|---|---:|---|---|
| — | `combat_part.gd` | 23 | The base: `game`, `combat`, `emit`, `ok`, `fail` | — |
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
