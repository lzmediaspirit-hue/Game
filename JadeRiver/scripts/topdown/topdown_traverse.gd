class_name TopdownTraverse
extends RefCounted
## T1 (docs/architecture/topdown_mechanics.md): the side view's traversal on the height grid, read from a layout's
## `traverse` (tools/content/rooms/spec.py; checked against the grid by tools/data/topdown_rooms.py check_traverse).
## Each piece keeps its side-view id and the side view's rule; only where it stands is the grid's:
##   raft     a floor on the water that a mover carries along its path on the room's clock (ZoneGeometry.mover_offset,
##            the side view's own function of the clock): a body standing on it rides with it (TopdownMotor);
##   updraft  a column of rising air over its cells, up to `top` levels: a body in the air inside it is eased toward a
##            rise (the side view's +220 while falling, gliding or flying);
##   vine, ladder, rope, chain   a climbable face between a foot cell and the cell beside it a level or more higher:
##            the body climbs it at the side view's climb speed, the World authority's climbable_open saying whether
##            it may (a sealed loft, a library floor).
## The grid's own queries (TopdownRoom.height_at, find_path, the rooms' reach checks, auto-path) never count a raft, an
## updraft or a climb: each is a way more, never the only one. Nothing here draws (TopdownTraverseView does).

const CLIMBABLES := ["vine", "ladder", "rope", "chain"]

## The room's clock, ZoneGeometry.time: the World authority's tick mirrors it here (WorldAuthority.tick), and a motor
## with no authority behind it (the motor's own tests) advances it itself.
var time := 0.0
var rafts: Array = []      ## {id, kind, rest: Rect2, mover: {path, speed, wait_s, mode, trigger_t}, z}
var updrafts: Array = []   ## {id, kind, rect: Rect2, lo, hi, speed}
var climbs: Array = []     ## {id, kind, foot: Vector2, top: Vector2, foot_z, top_z, dir: Vector2, face: Vector2}
var bounces: Array = []    ## {id, kind, rect: Rect2, z, speed}: a landing on it launches the body straight back up
var crumbles: Array = []   ## {id, kind, rect: Rect2, z, break_s, return_s, start}: rotten boards over a pit
var currents: Array = []   ## {id, kind, rect: Rect2, push: Vector2}: water pushing a body standing in it
var floods: Array = []     ## {id, kind, rect: Rect2, top, rises, goal, level}: rising water on an event's script
static var _geo: ZoneGeometry = null

## The room's traversal, read from its layout once and kept on the room (TopdownRoom.traverse, untyped so the grid's
## class does not name this one: the room's queries never ask it).
static func of(room: TopdownRoom) -> TopdownTraverse:
	if room == null: return null
	if room.traverse == null: room.traverse = from_layout(room.def.get("traverse", []), room)
	return room.traverse

## A room's traversal from its layout's rows (cells), in world units on the grid's plane.
static func from_layout(rows: Array, room: TopdownRoom) -> TopdownTraverse:
	var t := TopdownTraverse.new()
	var T := TopdownRoom.TILE
	for r in rows:
		var kind := str(r.get("kind", ""))
		var id := str(r.get("id", ""))
		if kind == "raft" or kind == "lift":
			# A raft rides the water along the plane; a lift (a crane's basket, a trial's plank) rises and falls between
			# levels (its path's third number, in levels), over the floor under it. Both are decks a body rides.
			var at: Array = r.get("at", [0, 0])
			var size: Array = r.get("size", [2, 2])
			var path: Array = []
			for q in r.get("path", []): path.append([float(q[0]) * T, float(q[1]) * T, float(q[2]) * TopdownRoom.LEVEL if (q as Array).size() > 2 else 0.0])
			t.rafts.append({"id": id, "kind": kind, "rest": Rect2(float(at[0]) * T, float(at[1]) * T, float(size[0]) * T, float(size[1]) * T),
				"z": float(r.get("level", 0)) * TopdownRoom.LEVEL,
				"mover": {"surface": id, "path": path, "speed": float(r.get("speed", 40.0)), "wait_s": float(r.get("wait_s", 2.0)),
					"mode": str(r.get("mode", "pingpong")), "trigger_t": -1.0}})
		elif kind == "crumble":
			# Rotten boards over a pit: a floor at `level` until a foot has stood on them `break_s`, gone for `return_s`.
			var cc: Array = r.get("rect", [0, 0, 1, 1])
			t.crumbles.append({"id": id, "kind": kind, "rect": Rect2(float(cc[0]) * T, float(cc[1]) * T, float(cc[2]) * T, float(cc[3]) * T),
				"z": float(r.get("level", 0)) * TopdownRoom.LEVEL, "break_s": float(r.get("break_s", 0.8)), "return_s": float(r.get("return_s", 5.0)),
				"start": -1.0})
		elif kind == "current":
			var qc: Array = r.get("rect", [0, 0, 1, 1])
			var push: Array = r.get("push", [0, 0])
			t.currents.append({"id": id, "kind": kind, "rect": Rect2(float(qc[0]) * T, float(qc[1]) * T, float(qc[2]) * T, float(qc[3]) * T),
				"push": Vector2(float(push[0]), float(push[1]))})
		elif kind == "flood":
			# Rising water: over its cells the water's top follows the side-view volume's script (`rise`: the event that
			# starts it, how fast, how long it holds, back), up to `top` levels; under it a floor is water.
			var fc: Array = r.get("rect", [0, 0, 1, 1])
			var rises: Array = []
			for v in ContentDB.room(room.id).get("volumes", []):
				if str(v.get("id", "")) == id: rises = v.get("rise", [])
			t.floods.append({"id": id, "kind": kind, "rect": Rect2(float(fc[0]) * T, float(fc[1]) * T, float(fc[2]) * T, float(fc[3]) * T),
				"top": float(r.get("top", 1.0)) * TopdownRoom.LEVEL, "rises": rises, "goal": {}, "level": -INF})
		elif kind == "updraft":
			var rc: Array = r.get("rect", [0, 0, 1, 1])
			t.updrafts.append({"id": id, "kind": kind, "rect": Rect2(float(rc[0]) * T, float(rc[1]) * T, float(rc[2]) * T, float(rc[3]) * T),
				"lo": TopdownRoom.WATER_Z, "hi": float(r.get("top", 1.0)) * TopdownRoom.LEVEL,
				"speed": float(r.get("speed", conf("updraft_speed", 220.0)))})
		elif kind == "bounce":
			var bc: Array = r.get("rect", [0, 0, 1, 1])
			var brect := Rect2(float(bc[0]) * T, float(bc[1]) * T, float(bc[2]) * T, float(bc[3]) * T)
			t.bounces.append({"id": id, "kind": kind, "rect": brect, "z": room.floor_at(brect.get_center()),
				"speed": float(r.get("speed", conf("bounce_speed", 528.0)))})
		elif kind in CLIMBABLES:
			var foot := TopdownRoom.cell_point(r.get("foot", [0, 0]))
			var top := TopdownRoom.cell_point(r.get("top", [0, 0]))
			var dir := (top - foot).normalized()
			# The sort key a body on it and its own tiles draw after (art px): the face's own row on a south face; on an east
			# or west side, past the raised floor's front row in that column (the body hangs in front of the whole side).
			var tc := TopdownRoom.cell_of(top)
			var front := tc.y + 1
			if absf(dir.x) > 0.5:
				var lv := room.level(tc.x, tc.y)
				while front < room.h and room.level(tc.x, front) >= lv and room.level(tc.x, front) != TopdownRoom.SOLID: front += 1
			else: front = maxi(tc.y, TopdownRoom.cell_of(foot).y)
			t.climbs.append({"id": id, "kind": kind, "foot": foot, "top": top, "dir": dir, "face": (foot + top) * 0.5,
				"foot_z": room.floor_at(foot), "top_z": room.floor_at(top), "front_key": float(front) * TopdownRoom.TILE / TopdownRoom.ART + 0.25})
	return t

## A number of the top-down traversal (movement.json `topdown.traverse`).
static func conf(key: String, fallback = 0.0):
	return ContentDB.movement("topdown.traverse." + key, fallback)

func is_empty() -> bool:
	return rafts.is_empty() and updrafts.is_empty() and climbs.is_empty() and bounces.is_empty() and crumbles.is_empty() \
		and currents.is_empty() and floods.is_empty()

# ------------------------------------------------------------------ crumbling boards
## The boards at a ground point that are a floor now ({} when none, or they have given way).
func crumble_at(p: Vector2) -> Dictionary:
	for c in crumbles:
		if (c.rect as Rect2).has_point(p) and crumble_state(c) != "broken": return c
	return {}

## "whole", "giving" (stood on: it holds `break_s`), "broken" (gone `return_s`), on the room's clock (the side view's
## crumble rule).
func crumble_state(c: Dictionary) -> String:
	var s := float(c.start)
	if s < 0.0: return "whole"
	var e := time - s
	if e < float(c.break_s): return "giving"
	if e < float(c.break_s) + float(c.return_s): return "broken"
	c.start = -1.0
	return "whole"

## A foot on the boards: they start to give way (once, until they are back).
func touch(c: Dictionary) -> void:
	if float(c.start) < 0.0: c.start = time

# ------------------------------------------------------------------ currents
## The push of the water on a body standing at `p` (units a second; the side view's current volume).
func current_at(p: Vector2) -> Vector2:
	var out := Vector2.ZERO
	for q in currents:
		if (q.rect as Rect2).has_point(p): out += q.push
	return out

# ------------------------------------------------------------------ rising water
## A game event starts a flood's script (a boss's phase): its rise row that matches, as the side view's on_event.
func on_event(event_name: String, payload: Dictionary) -> void:
	for f in floods:
		for r in f.rises:
			if str(r.get("event", "")) != event_name: continue
			var fits := true
			for k in r.get("match", {}):
				if str(payload.get(k, "")) != str(r.match[k]): fits = false
			if fits: f.goal = {"t0": time, "over": maxf(0.01, float(r.get("over_s", 4.0))), "hold": float(r.get("hold_s", -1.0)), "back": r.has("back_to")}

## How far up its top a flood's water stands now (0 at rest, 1 risen), on the room's clock: up over `over_s`, held
## `hold_s`, back down over the same (or held for good without a way back).
func flood_k(f: Dictionary) -> float:
	var g: Dictionary = f.goal
	if g.is_empty(): return 0.0
	var e := time - float(g.t0)
	var over := float(g.over)
	if e < over: return e / over
	if not bool(g.back) or float(g.hold) < 0.0: return 1.0
	e -= over + float(g.hold)
	if e < 0.0: return 1.0
	if e < over: return 1.0 - e / over
	f.goal = {}
	return 0.0

## Is the floor at `p` (height `floor_z`) under a flood's water now?
func flooded(p: Vector2, floor_z: float) -> bool:
	for f in floods:
		if not (f.rect as Rect2).has_point(p): continue
		var k := flood_k(f)
		if k > 0.0 and lerpf(TopdownRoom.WATER_Z, float(f.top), k) > floor_z + 0.5: return true
	return false

## The bounce a body landing at `p` on the floor at `z` comes down on ({} when none).
func bounce_at(p: Vector2, z: float) -> Dictionary:
	for b in bounces:
		if (b.rect as Rect2).has_point(p) and absf(z - float(b.z)) <= 8.0: return b
	return {}

# ------------------------------------------------------------------ rafts
## Where a raft is at the room's clock (or at `t`): its offset from where it rests, the side view's mover rule.
func raft_offset(r: Dictionary, t := -1.0) -> Vector2:
	if _geo == null: _geo = ZoneGeometry.new()
	var o: Vector3 = _geo.mover_offset(r.mover, time if t < 0.0 else t)
	return Vector2(o.x, o.y)

## A deck's height now: a raft's is its own; a lift's rises and falls along its path.
func deck_z(r: Dictionary) -> float:
	if str(r.kind) != "lift": return float(r.z)
	if _geo == null: _geo = ZoneGeometry.new()
	return float(r.z) + (_geo.mover_offset(r.mover, time) as Vector3).z

## The raft's deck on the plane now.
func raft_rect(r: Dictionary) -> Rect2:
	var rest: Rect2 = r.rest
	return Rect2(rest.position + raft_offset(r), rest.size)

## The raft whose deck is under a ground point now ({} when none).
func raft_at(p: Vector2) -> Dictionary:
	for r in rafts:
		if raft_rect(r).has_point(p): return r
	return {}

func raft(id: String) -> Dictionary:
	for r in rafts:
		if str(r.id) == id: return r
	return {}

## A body stepped onto a trigger raft: it sets off (once, until it is back), as the side view's trigger movers do.
func trigger(id: String) -> void:
	var r := raft(id)
	if not r.is_empty() and str(r.mover.mode) == "trigger" and float(r.mover.trigger_t) < 0.0: r.mover.trigger_t = time

# ------------------------------------------------------------------ updrafts
## The updraft a body at `p`, height `z`, is inside ({} when none): its cells, between the water and its top.
func updraft_at(p: Vector2, z: float) -> Dictionary:
	for u in updrafts:
		if (u.rect as Rect2).has_point(p) and z >= float(u.lo) and z <= float(u.hi): return u
	return {}

# ------------------------------------------------------------------ climbable faces
## The climbable a body standing at `p` on the floor at `z` may take: at its foot (on the foot's floor, against the
## face) or at its top (on the top's floor, at the edge). {climb, end: "foot" | "top"} or {}.
func climb_near(p: Vector2, z: float, reach := -1.0) -> Dictionary:
	var r := reach if reach > 0.0 else float(conf("climb_reach", 22.0))
	for c in climbs:
		if p.distance_to(c.foot) <= r + TopdownRoom.TILE * 0.5 and absf(z - float(c.foot_z)) <= 8.0 and _against(p, c, c.foot): return {"climb": c, "end": "foot"}
		if p.distance_to(c.top) <= r + TopdownRoom.TILE * 0.5 and absf(z - float(c.top_z)) <= 8.0 and _against(p, c, c.top): return {"climb": c, "end": "top"}
	return {}

## Within the climbable's own width (its cell's) across the face, and no further than `climb_reach` from the face.
func _against(p: Vector2, c: Dictionary, end: Vector2) -> bool:
	var dir: Vector2 = c.dir
	var side := Vector2(-dir.y, dir.x)
	var across := absf((p - end).dot(side))
	var to_face := absf((p - (c.face as Vector2)).dot(dir))
	return across <= TopdownRoom.TILE * 0.5 and to_face <= float(conf("climb_reach", 22.0))

func climb(id: String) -> Dictionary:
	for c in climbs:
		if str(c.id) == id: return c
	return {}
