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
## T2 (topdown_mechanics.md): a sealed hatch over a flight of stairs, shut while the World authority's climbable_open
## refuses the side view's climbable it stands for (the player sets `shut`; a motor with no character behind it finds it
## open); a side-view hazard volume's cells (a spike pit); ice and wind volumes' cells, their numbers the side view's.
var hatches: Array = []    ## {id, kind, rect: Rect2, shut, text}
var hazards: Array = []    ## {id, kind, rect: Rect2}
var ices: Array = []       ## {id, kind, rect: Rect2, traction}
var winds: Array = []      ## {id, kind, rect: Rect2, push: Vector2, cycle, strong_s, calm, phase, edge_factor}
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
	var side: Dictionary = {}   # the side-view room's volumes by id (a flood's script, an ice's traction, a wind's push)
	for v in ContentDB.room(room.id).get("volumes", []): side[str(v.get("id", ""))] = v
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
				"z": float(r.get("level", 0)) * TopdownRoom.LEVEL, "look": str(r.get("look", "lift" if kind == "lift" else "raft")),
				"mover": {"surface": id, "path": path, "speed": float(r.get("speed", 40.0)), "wait_s": float(r.get("wait_s", 2.0)),
					"mode": str(r.get("mode", "pingpong")), "trigger_t": -1.0}})
		elif kind == "lantern":
			# T2 · a lantern hung from the vault (the Hall of Lanterns): a deck at `level` over the floor that swings east and
			# west along its arc (`length` cells of chain) or goes round (`radius` cells), the side view's own mover rule
			# (ZoneGeometry.mover_offset) on the room's clock, laid on the plane.
			var la: Array = r.get("at", [0, 0])
			var ls: Array = r.get("size", [2, 2])
			t.rafts.append({"id": id, "kind": kind, "rest": Rect2(float(la[0]) * T, float(la[1]) * T, float(ls[0]) * T, float(ls[1]) * T),
				"z": float(r.get("level", 0)) * TopdownRoom.LEVEL, "look": "lantern",
				"mover": {"surface": id, "path": [], "mode": str(r.get("mode", "swing")), "length": float(r.get("length", 3.0)) * T,
					"amp_deg": float(r.get("amp_deg", 25.0)), "period_s": float(r.get("period_s", 3.2)), "phase_deg": float(r.get("phase_deg", 0.0)),
					"radius": float(r.get("radius", 1.5)) * T, "trigger_t": -1.0}})
		elif kind == "crumble":
			# Rotten boards over a pit: a floor at `level` until a foot has stood on them `break_s`, gone for `return_s`.
			# T2 · `under`: boards that are the grid's own floor at `level` (the grid's queries walk them): gone, the floor
			# drops to the `under` level, or opens on water or a pit a body falls into (the motor's `hole`).
			var cc: Array = r.get("rect", [0, 0, 1, 1])
			var under = r.get("under", null)
			var hole := str(under) if under is String else ""
			t.crumbles.append({"id": id, "kind": kind, "rect": Rect2(float(cc[0]) * T, float(cc[1]) * T, float(cc[2]) * T, float(cc[3]) * T),
				"z": float(r.get("level", 0)) * TopdownRoom.LEVEL, "break_s": float(r.get("break_s", 0.8)), "return_s": float(r.get("return_s", 5.0)),
				"start": -1.0, "flush": under != null, "hole": hole, "look": str(r.get("look", "boards")),
				"under": TopdownRoom.WATER_Z if hole != "" else (float(under) * TopdownRoom.LEVEL if under != null else -INF)})
		elif kind == "hatch":
			var hc: Array = r.get("rect", [0, 0, 1, 1])
			t.hatches.append({"id": id, "kind": kind, "rect": Rect2(float(hc[0]) * T, float(hc[1]) * T, float(hc[2]) * T, float(hc[3]) * T),
				"shut": false, "text": ""})
		elif kind == "hazard":
			var zc: Array = r.get("rect", [0, 0, 1, 1])
			t.hazards.append({"id": id, "kind": kind, "rect": Rect2(float(zc[0]) * T, float(zc[1]) * T, float(zc[2]) * T, float(zc[3]) * T),
				"hazard": str(side.get(id, {}).get("hazard", id))})
		elif kind == "ice":
			var ic: Array = r.get("rect", [0, 0, 1, 1])
			t.ices.append({"id": id, "kind": kind, "rect": Rect2(float(ic[0]) * T, float(ic[1]) * T, float(ic[2]) * T, float(ic[3]) * T),
				"traction": float(side.get(id, {}).get("traction", 380.0)) * float(conf("side_scale", 0.755))})
		elif kind == "wind":
			var wc: Array = r.get("rect", [0, 0, 1, 1])
			var wv: Dictionary = side.get(id, {})
			var wp: Array = wv.get("push", [0, 0])
			t.winds.append({"id": id, "kind": kind, "rect": Rect2(float(wc[0]) * T, float(wc[1]) * T, float(wc[2]) * T, float(wc[3]) * T),
				"push": Vector2(float(wp[0]), float(wp[1])) * float(conf("side_scale", 0.755)), "cycle": float(wv.get("cycle", 4.0)),
				"strong_s": float(wv.get("strong_s", 1.5)), "calm": float(wv.get("calm", 0.3)), "phase": float(wv.get("phase", 0.0)),
				"edge_factor": float(wv.get("edge_factor", 1.5))})
		elif kind == "current":
			var qc: Array = r.get("rect", [0, 0, 1, 1])
			var push: Array = r.get("push", [0, 0])
			t.currents.append({"id": id, "kind": kind, "rect": Rect2(float(qc[0]) * T, float(qc[1]) * T, float(qc[2]) * T, float(qc[3]) * T),
				"push": Vector2(float(push[0]), float(push[1]))})
		elif kind == "flood":
			# Rising water: over its cells the water's top follows the side-view volume's script (`rise`: the event that
			# starts it, how fast, how long it holds, back), up to `top` levels; under it a floor is water.
			var fc: Array = r.get("rect", [0, 0, 1, 1])
			var rises: Array = side.get(id, {}).get("rise", [])
			var alt: Array = side.get(id, {}).get("alt", [-100, -20])
			t.floods.append({"id": id, "kind": kind, "rect": Rect2(float(fc[0]) * T, float(fc[1]) * T, float(fc[2]) * T, float(fc[3]) * T),
				"top": float(r.get("top", 1.0)) * TopdownRoom.LEVEL, "rises": rises, "goal": {}, "level": -INF, "rest": float(alt[1])})
		elif kind == "updraft":
			var rc: Array = r.get("rect", [0, 0, 1, 1])
			t.updrafts.append({"id": id, "kind": kind, "rect": Rect2(float(rc[0]) * T, float(rc[1]) * T, float(rc[2]) * T, float(rc[3]) * T),
				"lo": TopdownRoom.WATER_Z, "hi": float(r.get("top", 1.0)) * TopdownRoom.LEVEL,
				"speed": float(r.get("speed", conf("updraft_speed", 220.0)))})
		elif kind == "bounce":
			var bc: Array = r.get("rect", [0, 0, 1, 1])
			var brect := Rect2(float(bc[0]) * T, float(bc[1]) * T, float(bc[2]) * T, float(bc[3]) * T)
			t.bounces.append({"id": id, "kind": kind, "rect": brect, "z": room.floor_at(brect.get_center()),
				"speed": float(r.get("speed", conf("bounce_speed", 528.0))), "look": str(r.get("look", "drum"))})
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
		and currents.is_empty() and floods.is_empty() and hatches.is_empty() and hazards.is_empty() and ices.is_empty() and winds.is_empty()

# ------------------------------------------------------------------ T2: hatches, hazards, ice, wind
## The shut hatch over a ground point ({} when none, or it is open).
func hatch_at(p: Vector2) -> Dictionary:
	for h in hatches:
		if bool(h.shut) and (h.rect as Rect2).has_point(p): return h
	return {}

## The side-view hazard volumes whose cells hold a ground point (a spike pit's).
func hazards_at(p: Vector2) -> Array:
	return hazards.filter(func(z): return (z.rect as Rect2).has_point(p))

## The ice under a ground point ({} when none).
func ice_at(p: Vector2) -> Dictionary:
	for i in ices:
		if (i.rect as Rect2).has_point(p): return i
	return {}

## The wind's push on a body standing at `p` now, units a second, before its edge factor (the side view's wind
## volume: strong for `strong_s` of each `cycle`, a breeze of `calm` the rest, on the room's clock).
func wind_at(p: Vector2) -> Dictionary:
	for wv in winds:
		if (wv.rect as Rect2).has_point(p): return wv
	return {}

func wind_strength(wv: Dictionary) -> float:
	var ph := fposmod(time + float(wv.phase), maxf(0.1, float(wv.cycle)))
	return 1.0 if ph < float(wv.strong_s) else float(wv.calm)

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

## T2 · boards that were the floor itself (`under`) and are gone now, at a ground point ({} when none).
func crumble_gone_at(p: Vector2) -> Dictionary:
	for c in crumbles:
		if bool(c.flush) and (c.rect as Rect2).has_point(p) and crumble_state(c) == "broken": return c
	return {}

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
			if not fits: continue
			# T2: a row that takes the water back down to its rest (the Serpent's when it is beaten: its `to` no higher than
			# the volume's resting top) lowers a risen flood from where it stands now; any other raises it.
			if f.has("rest") and float(r.get("to", 1.0)) <= float(f.rest) + 0.5:
				var now := flood_k(f)
				f.goal = {} if now <= 0.0 else {"t0": time, "over": maxf(0.01, float(r.get("over_s", 4.0))), "fall": now}
			else: f.goal = {"t0": time, "over": maxf(0.01, float(r.get("over_s", 4.0))), "hold": float(r.get("hold_s", -1.0)), "back": r.has("back_to")}

## How far up its top a flood's water stands now (0 at rest, 1 risen), on the room's clock: up over `over_s`, held
## `hold_s`, back down over the same (or held for good without a way back).
func flood_k(f: Dictionary) -> float:
	var g: Dictionary = f.goal
	if g.is_empty(): return 0.0
	var e := time - float(g.t0)
	if g.has("fall"):
		if e >= float(g.over):
			f.goal = {}
			return 0.0
		return float(g.fall) * (1.0 - e / float(g.over))
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
	# T2: a lantern's swing is laid east-west along the plane (its small rise at the arc's ends left out: the deck keeps
	# its level), and its circle on the plane round from its rest.
	match str(r.mover.mode):
		"swing": return Vector2(o.x, 0.0)
		"circle": return Vector2(o.x, o.z)
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
