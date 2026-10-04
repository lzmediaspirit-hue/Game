class_name RoomRuntime
extends RefCounted
## S17 · Live state of the loaded room: enemies, spawn slots, ground loot,
## projectiles, object states and the event timer. Scene-free; the World and
## Enemy authorities are its only writers.

var room_id := ""
var def: Dictionary = {}
var geometry := ZoneGeometry.new()
var enemies: Dictionary = {}          # uid -> EnemyState
var spawn_slots: Array = []           # [{spawn, point, enemy, elite, timer, uid, level_range, surface}]
var loot: Array = []                  # [{uid, item, count, instance, coins, x, y, ttl, age}]
var projectiles: Array = []           # [{uid, team, owner, x, y, alt, dir, speed, range, travelled, attack, pierce, hits, art, element}]
var objects: Dictionary = {}          # object id -> {state, timer, hits, cooldown}
var guardians: Dictionary = {}        # S45 rare herb object id -> the uid of its guardian this ripening
var next_uid := 1
var elapsed := 0.0
var event: Dictionary = {}            # survival/escort events {id, remaining, ...}
var arrival_protection := 0.0
var first_visit := false
var hazards: Dictionary = {}          # hazard id -> {phase, t, dur, spots: [[x, y, alt]], dir, pulse, inside}
var hazard_drift := Vector2.ZERO      # the push the room's hazards put on the active character this tick
var hazard_pulse: Dictionary = {}      # S43 hazard volumes: seconds to each one's next pulse
var topdown: TopdownRoom = null       # the room's layout on the height grid (WorldAuthority.load_room; its foes steer on it)

func uid() -> int:
	next_uid += 1
	return next_uid

func object_def(id: String) -> Dictionary:
	for o in def.get("objects", []):
		if str(o.get("id", "")) == id: return o
	return {}

func portal_def(id: String) -> Dictionary:
	for p in def.get("portals", []):
		if str(p.get("id", "")) == id: return p
	return {}

func width() -> float:
	return float(def.get("bounds", [0, 480, 1280, 480])[2])

## Half the world view in world units: the 1280 x 720 canvas (the top-down view's 640 x 360 art px at 2 units each).
const HALF_VIEW := TopdownRoom.VIEW * TopdownRoom.ART * 0.5
## A foe's figure over its feet in world units (half its width, its height), for telling whether any of it shows.
const FIGURE := Vector2(24, 80)

## Is a figure standing at `p` (height `alt`) out of the view of the body `st`, by at least `margin` world units? The
## camera's own rect for a body there (TopdownRoom.view_rect: both axes, clamped to the room, the ridge at the north edge
## included) against the figure's rect on the screen's plane.
func out_of_view(p: Vector2, alt: float, st: ActorState, margin := 0.0) -> bool:
	if st == null: return true
	var z := topdown.ground_under(st.plane, st.altitude)
	var fig := Rect2(p.x - FIGURE.x, p.y - alt - FIGURE.y, FIGURE.x * 2.0, FIGURE.y)
	return not topdown.view_rect(st.plane, z).grow(margin).intersects(fig)

func living_enemies() -> Array:
	var out: Array = []
	for u in enemies:
		var e: EnemyState = enemies[u]
		if e.alive: out.append(e)
	return out
