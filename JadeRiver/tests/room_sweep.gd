extends "res://tests/lib/suite.gd"
## Room sweep (M16, the P2 play-through pass; on the height grid since S12a retired the side view): every room of the
## world on its layout (TopdownRoom, merged with its room's definition as the World authority merges it), headless,
## with the game's own path search and motor.
##   Routes: from every way in (each way's arrival) and the room's spawn, the grid's path (TopdownRoute.reach: walking,
##           stairs, drops, a hop a level up, a running jump over a tile) reaches every way out (its cell) and every
##           thing the context button offers or a training post (a cell within three tiles of it whose floor is within
##           the button's 48 of the thing's height), and every arrival reaches a way out (a story instance with no way
##           ends by its event). A thing on a path above (S12c: a ledge only a movement art climbs onto) is its art's,
##           landed on in topdown_traversal.
##   Walks:  TopdownMotor walks the grid's own way (TopdownRoute.find, auto-path's: no running jump) from the spawn to
##           each of them, the stick held toward each next cell, Jump where the way hops a level up; a body that gets
##           no nearer the next cell for STUCK_FRAMES frames is stuck, one that falls in the water is lost. (Auto-path's
##           steering along such a way is topdown_suite's route tour.)
##   Art:    every prop on a layout is one the tile set draws, and every solid one's opaque columns span its footprint
##           (no invisible walls).
## Run headless:  godot --headless --path . res://tests/room_sweep.tscn [-- --room=<id>]

const DT := 1.0 / 60.0
## Legs the motor does not walk though the grid's way takes them. Each must still stick: one that walks is taken off this
## list. S12a found two, off a stair's top row sideways onto the floor a full step (8) above the stair's middle (the
## motor's corner test meets 64 against a body at 55.9999 and refuses it, where TopdownRoute.step_rise and
## topdown_rooms.py's Grid take the step at the cells' edge); S12c laid both rooms' flights with their cheeks clear (the
## Herb Terraces' second flight below the terrace's edge, the Rapids Terraces' by the engine's `flights`), so none is left.
const KNOWN_STICKS: Array = []
const STUCK_FRAMES := 90        # 1.5 s of held input without getting nearer
const ART_SLACK := 4            # art px a solid footprint may stand past its art's opaque columns
const Reach = preload("res://tests/topdown_tutorial.gd")   # its reach: the motor's rules, as topdown_rooms.py's Grid checks them

var walked_s := 0.0
var legs := 0
var art_seen := 0               # solid prop kinds compared with their art
var opaque := {}                # prop kind -> Vector2i(first, last) opaque column of its rect

func _main() -> void:
	var only := ""
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--room="): only = str(a).trim_prefix("--room=")
	var t0 := Time.get_ticks_msec()
	var rooms := 0
	for rid in ContentDB.rooms:
		if only != "" and rid != only: continue
		sweep(str(rid))
		rooms += 1
	print("room_sweep: %d rooms, %d legs, %.0f s of walking in %.1f s" % [rooms, legs, walked_s, (Time.get_ticks_msec() - t0) / 1000.0])
	check(only != "" or art_seen > 50 and walked_s > 1000.0, "the sweep compared %d solid props with their art and walked %.0f s over %d legs" % [art_seen, walked_s, legs])
	end_suite()

# ------------------------------------------------------------------ one room
func sweep(rid: String) -> void:
	check(TopdownRoom.has_layout(rid), "%s has its layout on the grid" % rid)
	if not TopdownRoom.has_layout(rid): return
	var grid := TopdownRoom.load_room(rid)
	var def := grid.merge_def(ContentDB.room(rid))
	art_suite(rid, grid)
	# Every way in: each way's arrival, and the spawn.
	var entries: Array = [{"what": "the spawn", "p": grid.spawn}]
	for p in def.get("portals", []):
		if p.has("arrive"): entries.append({"what": "arriving by " + str(p.id), "p": _at(p, "arrive")})
	# Targets: the ways out, the things the context button offers, the training posts.
	var targets: Array = []
	for p in def.get("portals", []):
		targets.append({"what": "%s %s" % [str(p.get("type", "edge")), p.id], "at": _at(p, "at"), "alt": float(p.get("alt", 0.0)), "way_out": true})
	for o in def.get("objects", []):
		if not o.has("at") or not (str(o.type) in WorldAuthority.TRAINING or WorldAuthority.offers_context(o)): continue
		# S12c: a thing on a path above (a ledge only a movement art climbs onto) is its art's to reach, not a walk's
		# (topdown_traversal lands on every one; tools/data/topdown_rooms.py check_above holds its reach).
		if grid.ledge_at(_at(o, "at"), grid.height_at(_at(o, "at"))) != "": continue
		targets.append({"what": str(o.id), "at": _at(o, "at"), "alt": float(o.get("alt", 0.0)), "way_out": false,
			"reach": 0.0 if str(o.type) in WorldAuthority.TRAINING else float(o.get("radius", 110))})   # a post: its spot
	for e in entries:
		var start := TopdownRoom.cell_of(e.p)
		check(grid.standable(start), "%s: %s at %s is on no floor" % [rid, e.what, str(start)])
		var seen := Reach.reach(grid, start)
		var out := false
		for t in targets:
			var ok := _in_reach(grid, seen, t)
			check(ok, "%s: from %s no way on the grid reaches %s at %s" % [rid, e.what, t.what, str(t.at)])
			out = out or (ok and t.way_out)
		if not def.get("portals", []).is_empty():   # a story instance with no door ends by its event
			check(out, "%s: %s, the player is shut in (no way out reached from there)" % [rid, e.what])
	walk_tour(rid, grid, targets)

## A target is reached when its cell (a way's) or the spot a body stands at to reach it (a thing's: TopdownRoom.spot_near
## at its height) is reached.
func _in_reach(grid: TopdownRoom, seen: Dictionary, t: Dictionary) -> bool:
	if t.way_out: return seen.has(TopdownRoom.cell_of(t.at))
	return seen.has(TopdownRoom.cell_of(grid.spot_near(t.at, float(t.alt), t.at)))

# ------------------------------------------------------------------ walking
## From the spawn the motor walks the grid's own way (TopdownRoute.find without a running jump: auto-path's) to each
## target, the stick held toward each next cell of it (Jump pressed where it hops a level up), until it stands on the
## way's cell or in the thing's reach (the context button's: its radius, its floor within 48). Auto-path's steering
## along such a way (its straight runs) is topdown_suite's route tour.
func walk_tour(rid: String, grid: TopdownRoom, targets: Array) -> void:
	for t in targets:
		var m := TopdownMotor.new(grid)
		var goal: Vector2 = t.at if t.way_out else grid.spot_near(t.at, float(t.alt), m.pos)
		var from := TopdownRoom.cell_of(m.pos)
		var to := TopdownRoom.cell_of(grid.nearest_standable(goal))
		var path := TopdownRoute.find(grid, from, to, false) if from != to else []
		if from != to and path.is_empty(): continue
		legs += 1
		var why := _walk(grid, m, path, t)
		var known := "%s: %s" % [rid, t.what] in KNOWN_STICKS
		if known:
			check(why.begins_with("sticks"), "%s: walking to %s, a known stick off a stair's top row, still sticks (else take it off KNOWN_STICKS: %s)" % [rid, t.what, why])
			print("  known: %s: walking to %s the player %s" % [rid, t.what, why])
		elif why != "": check(false, "%s: walking to %s the player %s at %s" % [rid, t.what, why, str(m.pos.round())])
		else: checks += 1

## One leg along `path`: "" when the body arrives, else what went wrong.
func _walk(grid: TopdownRoom, m: TopdownMotor, path: Array, t: Dictionary) -> String:
	var step := float(TopdownMotor.conf("step_up", 8.0))
	var prev := TopdownRoom.cell_of(m.pos)
	for cell in path:
		var goal := TopdownRoute.centre(cell)
		var hop: bool = TopdownRoute.step_rise(grid, prev, cell).x > step
		var best := m.pos.distance_to(goal)
		var still := 0
		var pressed := false
		while m.pos.distance_to(goal) > 8.0 or not m.grounded or absf(m.z - grid.cell_floor(cell)) > 8.0:
			if _there(m, t): return ""
			var axis := (goal - m.pos).normalized() if m.pos.distance_to(goal) > 1.0 else Vector2.ZERO
			var jump := hop and not pressed and m.grounded
			if jump: pressed = true
			for sub in 2: m.step(DT * 0.5, axis, jump and sub == 0)
			m.drain()
			walked_s += DT
			if m.sink_t >= 0.0:
				while m.sink_t >= 0.0: m.step(DT, Vector2.ZERO)
				return "falls in the water (on the way to %s)" % str(cell)
			if m.grounded and pressed and m.z < grid.cell_floor(cell) - 8.0: pressed = false   # the hop fell short: again
			var d := m.pos.distance_to(goal)
			if d < best - 0.5:
				best = d
				still = 0
			else:
				still += 1
			if still >= STUCK_FRAMES: return "sticks on the way to %s (%.0f from it)" % [str(cell), d]
		prev = cell
	return ""   # the way's cell, or the spot the game stands a body at to reach the thing (TopdownRoom.spot_near)

## In the thing's reach on its floor (a way: on its cell).
func _there(m: TopdownMotor, t: Dictionary) -> bool:
	if t.way_out: return TopdownRoom.cell_of(m.pos) == TopdownRoom.cell_of(t.at)
	return m.grounded and m.pos.distance_to(t.at) <= float(t.reach) and absf(m.z - float(t.alt)) <= WorldAuthority.REACH_ALT

func _at(d: Dictionary, key: String) -> Vector2:
	var a: Array = d.get(key, [0, 0])
	return Vector2(float(a[0]), float(a[1]))

# ------------------------------------------------------------------ invisible walls
## Every prop the layout lays is one the tile set draws, and a solid one's opaque columns span its footprint.
func art_suite(rid: String, grid: TopdownRoom) -> void:
	var props: Dictionary = grid.tileset.get("props", {})
	var tile := int(grid.tileset.get("tile", 16))
	for p in grid.props:
		var art: Dictionary = p.art
		check(not art.is_empty() and props.has(str(p.kind)), "%s: the prop %s at %s is one the tile set draws" % [rid, p.kind, str(p.cell)])
		if art.is_empty() or not art.get("solid", true) or opaque.has(str(p.kind)): continue
		var cols := _opaque(str(p.kind), art)
		opaque[str(p.kind)] = cols
		art_seen += 1
		var org: Array = art.get("origin", [0, 0])
		var foot := Vector2i(int(org[0]), int(org[0]) + int(art.footprint[0]) * tile)   # the footprint's columns in the rect (drawn at its origin)
		check(cols.x <= foot.x + ART_SLACK and cols.y >= foot.y - 1 - ART_SLACK,
			"%s: the prop %s is solid over art px %d to %d, its art opaque from %d to %d (an invisible wall)" % [rid, p.kind, foot.x, foot.y - 1, cols.x, cols.y])

## The first and last opaque columns of a prop's rect on the tile set's atlas.
func _opaque(kind: String, art: Dictionary) -> Vector2i:
	var img := _atlas()
	var r: Array = art.rect
	if img == null: return Vector2i(0, int(r[2]) - 1)
	var used := img.get_region(Rect2i(int(r[0]), int(r[1]), int(r[2]), int(r[3]))).get_used_rect()
	return Vector2i(used.position.x, used.end.x - 1) if used.size.x > 0 else Vector2i(int(r[2]), -1)

var _atlas_img: Image = null
func _atlas() -> Image:
	if _atlas_img == null:
		var ts := TopdownRoom.load_room(str(ContentDB.rooms.keys()[0])).tileset
		var tex = load(str(ts.get("atlas", {}).get("props", "")))
		if tex is Texture2D: _atlas_img = (tex as Texture2D).get_image()
	return _atlas_img
