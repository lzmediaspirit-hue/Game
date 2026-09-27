extends Node
## Room sweep (M16, the P2 play-through pass): every room, headless, with the real movement solver.
##   Routes: the walkable ground is a 40 px grid built with the solver's own rules (walk_target, blocks_at along each
##           step, no deep water). From every way in (each portal's arrival and the spawn point) it reaches every door
##           and every interactable on the ground, and every arrival reaches a way out. A raised object has a surface at
##           its height within reach, or a bounce that throws a body up to it (room_lint proves the tiers reachable).
##           Walkable ground never lies under a higher ground surface (in under the side of a flight of steps).
##   Walks:  MovementSolver walks the route between every pair of them, input held toward the next grid point at the
##           player's speed (sprinting after two seconds, as a held joystick does). A body held in place for
##           STUCK_FRAMES frames is snagged. A stretch of route is walked once: a pair whose route runs over stretches
##           already walked walks only the new ones.
##   Art:    every solid footprint lies under drawn art (no invisible walls).
## Run headless:  godot --headless --path . res://tests/room_sweep.tscn [-- --room=<id>]

const Terrain = preload("res://scripts/terrain.gd")
const G := 40.0                 # grid step
const DT := 1.0 / 60.0
const SPEED := 205.0            # the player's walk (player.gd); x1.7 sprinting
const STUCK_FRAMES := 45        # 0.75 s of held input without moving closer or anywhere
const LEG_FRAMES := 600         # 10 s to cover one 40 px step (ice may slide a body past and back)
const ART_SLACK := 8.0          # a footprint may stand this far past its art's opaque pixels
const MELEE := 60.0             # a training target is struck from within this
const DIRS := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]

var checks := 0
var failures := 0
var walked_s := 0.0
var art_seen := 0               # footprints compared with their art
var opaque := {}                # prop id -> Vector2(first, last) opaque column of its idle frame

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

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
	print("room_sweep: %d rooms, %.0f s of walking in %.1f s" % [rooms, walked_s, (Time.get_ticks_msec() - t0) / 1000.0])
	check(only != "" or art_seen > 50 and walked_s > 1000.0, "the sweep compared %d footprints with their art and walked %.0f s" % [art_seen, walked_s])
	print("room_sweep: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ one room
func sweep(rid: String) -> void:
	var def := ContentDB.room(rid)
	var geo := ZoneGeometry.new()
	geo.configure(WorldAuthority.compile_geometry(def))
	art_suite(rid, def, geo)
	var grid := _grid(geo)
	var nodes: Dictionary = grid.nodes
	# Every way in, and the walkable ground each one opens (comp: node -> the entry node it was flooded from).
	var comp := {}
	var entries: Array = []
	for p in def.get("portals", []):
		var at := _at(p)
		var inward := 1.0 if at.x < geo.bounds.size.x * 0.5 else -1.0
		entries.append({"what": "arriving by " + str(p.id), "p": at + Vector2(inward * float(p.get("arrive_offset", 70)), float(p.get("arrive_dy", 0)))})
	entries.append({"what": "the spawn point", "p": Vector2(float(def.spawn_point[0]), float(def.spawn_point[1]))})
	for e in entries:
		e.node = _nearest(grid, e.p, 60.0)
		if e.node < 0:
			# A way in onto a raised surface (a door on a deck) is not walked from the ground.
			var s := geo.surface_under(e.p, 9999.0)
			check(s != null and s.stratum != "ground", "%s: %s at %s lands off the walkable ground" % [rid, e.what, str(e.p)])
		elif not comp.has(e.node):
			_flood(grid, e.node, comp)
	# Targets: doors and edges, interactables, training posts.
	var targets: Array = []
	for p in def.get("portals", []):
		var at := _at(p)
		var cells := _cells(grid, func(q: Vector2, _h: float): return absf(q.x - at.x) <= 60.0 and absf(q.y - at.y) <= 50.0)
		if cells.is_empty() and p.has("surface"):
			check(geo.index.has(str(p.surface)), "%s: portal %s stands on a real surface" % [rid, p.id])
			continue
		targets.append({"what": "%s %s" % [str(p.get("type", "edge")), p.id], "at": at, "cells": cells, "alt": 0.0, "way_out": true})
	for o in def.get("objects", []):
		var trains: bool = str(o.type) in WorldAuthority.TRAINING
		if not trains and not WorldAuthority.offers_context(o): continue
		var at := _at(o)
		var alt := float(o.get("alt", 0.0))
		var reach := MELEE if trains else float(o.get("radius", 110))
		var cells := _cells(grid, func(q: Vector2, h: float): return q.distance_to(at) <= reach and absf(h - alt) <= WorldAuthority.REACH_ALT)
		if cells.is_empty():
			check(_stand_near(geo, at, alt, reach), "%s: %s at %s (alt %d) has nowhere to stand within reach" % [rid, o.id, str(at), int(alt)])
			continue
		targets.append({"what": str(o.id), "at": at, "cells": cells, "alt": alt, "way_out": false})
	for t in targets:
		t.node = -1
		for n in t.cells:
			if comp.has(n) and (t.node < 0 or (nodes[n].p as Vector2).distance_to(t.at) < (nodes[t.node].p as Vector2).distance_to(t.at)): t.node = n
		# Ground a walk cannot reach may still be a raised terrace, reached by a jump (room_lint's reach).
		check(t.node >= 0 or float(t.alt) > 0.5, "%s: no route reaches %s at %s" % [rid, t.what, str(t.at)])
	# Walkable ground under a higher ground surface (the side of a flight of stairs): the walker is drawn inside it, and
	# pressing on toward the top does nothing there.
	var under := {}
	for n in comp:
		for s in geo.surfaces:
			if s.stratum == "ground" and s != nodes[n].s and s.contains(nodes[n].p) and s.height_at(nodes[n].p) > float(nodes[n].h) + 8.0: under[s.id] = nodes[n].p
	for sid in under: check(false, "%s: the player walks in under %s at %s" % [rid, sid, str(under[sid])])
	if not def.get("portals", []).is_empty():   # a story instance with no door ends by its event
		for e in entries:
			if e.node < 0: continue
			check(targets.any(func(t): return t.way_out and t.node >= 0 and comp[t.node] == comp[e.node]),
				"%s: %s at %s, the player is shut in (no way out walks from there)" % [rid, e.what, str(e.p)])
	walk_pairs(rid, geo, grid, targets.filter(func(t): return t.node >= 0))

## Walk the route between every pair of reached targets. A stretch (a step between two grid points) is walked once:
## a pair whose route runs over stretches already walked walks only the runs of new ones.
func walk_pairs(rid: String, geo: ZoneGeometry, grid: Dictionary, reached: Array) -> void:
	var walked := {}
	for i in reached.size():
		var prev := _bfs(grid, reached[i].node)
		for j in range(i + 1, reached.size()):
			if not prev.has(reached[j].node): continue
			var path: Array = [reached[j].node]
			while prev[path[0]] >= 0: path.push_front(prev[path[0]])
			var run: Array = []
			for k in range(1, path.size()):
				var edge := Vector2i(mini(path[k - 1], path[k]), maxi(path[k - 1], path[k]))
				var fresh := not walked.has(edge)
				if fresh:
					if run.is_empty(): run.append(path[k - 1])
					run.append(path[k])
					walked[edge] = true
				if (not fresh or k == path.size() - 1) and run.size() > 1:
					_walk(rid, geo, grid, run, "%s to %s" % [reached[i].what, reached[j].what])
					run = []

# ------------------------------------------------------------------ the walkable grid
## Nodes are (cell, ground surface) pairs whose centre is free at that surface's height and not in deep water; each
## node lists the neighbours a walker comes to by the solver's walk_target with nothing solid on the way (a diagonal
## only past two open corners).
func _grid(geo: ZoneGeometry) -> Dictionary:
	var cols := int(ceil(geo.bounds.size.x / G))
	var rows := int(ceil(geo.bounds.size.y / G))
	var nodes := {}
	var at_cell := {}
	for s in geo.surfaces:
		if s.stratum != "ground" or s.disabled or s.moving or not geo.crumble_volume(s.id).is_empty(): continue
		for j in rows:
			for i in cols:
				var p := geo.bounds.position + Vector2((i + 0.5) * G, (j + 0.5) * G)
				if not s.contains(p): continue
				var h := s.height_at(p)
				if geo.blocks_at(p, h, "ground") or not geo.volume_at(p, h, "water_deep").is_empty(): continue
				var id := nodes.size()
				nodes[id] = {"p": p, "s": s, "h": h, "i": i, "j": j, "next": []}
				at_cell[Vector2i(i, j)] = (at_cell.get(Vector2i(i, j), []) as Array) + [id]
	var solid: Array = []   # blocking footprints as the solver grows them
	for ob in geo.obstacles:
		if ob.get("blocks", true) and ob.has("footprint"): solid.append((ob.footprint as Rect2).grow(float(ob.get("radius", 11))))
	var grid := {"nodes": nodes, "at_cell": at_cell, "solid": solid}
	for id in nodes:
		var a: Dictionary = nodes[id]
		for d in DIRS:
			var b := _step(geo, grid, a, d)
			if b >= 0 and (d.x == 0 or d.y == 0 or _step(geo, grid, a, Vector2i(d.x, 0)) >= 0 and _step(geo, grid, a, Vector2i(0, d.y)) >= 0):
				a.next.append(b)
	return grid

## The node a walker on `a` comes to one cell along `d` (the solver's walk_target from its surface at its height, and
## nothing solid on the way), or -1.
func _step(geo: ZoneGeometry, grid: Dictionary, a: Dictionary, d: Vector2i) -> int:
	var there: Array = grid.at_cell.get(Vector2i(a.i + d.x, a.j + d.y), [])
	if there.is_empty(): return -1
	var s: WalkSurface = a.s
	var q: Vector2 = a.p + Vector2(d) * G
	var flat_only: bool = there.size() == 1 and grid.nodes[there[0]].s == s and s.rise == 0.0
	var t: WalkSurface = s if flat_only else geo.walk_target(q, s.height_at(q) if s.contains(q) else float(a.h), s)
	for n in there:
		if grid.nodes[n].s != t: continue
		var box := Rect2(a.p, Vector2.ZERO).expand(q)
		var h := minf(float(a.h), float(grid.nodes[n].h))
		for r in grid.solid:
			if not (r as Rect2).intersects(box, true): continue
			for k in range(1, 10):
				if geo.blocks_at(a.p.lerp(q, k / 10.0), h, "ground"): return -1
		return n
	return -1

func _flood(grid: Dictionary, start: int, comp: Dictionary) -> void:
	var todo: Array = [start]
	comp[start] = start
	while not todo.is_empty():
		var n: int = todo.pop_back()
		for m in grid.nodes[n].next:
			if not comp.has(m):
				comp[m] = start
				todo.append(m)

## Breadth first from a node: node -> the node before it (-1 at the start).
func _bfs(grid: Dictionary, start: int) -> Dictionary:
	var prev := {start: -1}
	var queue: Array = [start]
	var head := 0
	while head < queue.size():
		var n: int = queue[head]
		head += 1
		for m in grid.nodes[n].next:
			if not prev.has(m):
				prev[m] = n
				queue.append(m)
	return prev

func _nearest(grid: Dictionary, p: Vector2, within: float) -> int:
	var best := -1
	for n in grid.nodes:
		var d: float = (grid.nodes[n].p as Vector2).distance_to(p)
		if d <= within and (best < 0 or d < (grid.nodes[best].p as Vector2).distance_to(p)): best = n
	return best

func _cells(grid: Dictionary, near: Callable) -> Array:
	var out: Array = []
	for n in grid.nodes:
		if near.call(grid.nodes[n].p, grid.nodes[n].h): out.append(n)
	return out

func _at(d: Dictionary) -> Vector2:
	return Vector2(float(d.at[0]), float(d.at[1]))

## A raised object is in reach from a surface at its height (the context button's 48 up or down), or over a bounce
## (a drum, a lotus pad) whose throw carries a body up to it.
func _stand_near(geo: ZoneGeometry, at: Vector2, alt: float, reach: float) -> bool:
	for s in geo.surfaces:
		if s.disabled or s.kind == "ladder": continue
		var q := at.clamp(s.bounds.position, s.bounds.end - Vector2(0.01, 0.01))
		if s.contains(q) and q.distance_to(at) <= reach and absf(s.height_at(q) - alt) <= WorldAuthority.REACH_ALT: return true
	for v in geo.volumes:
		var speed := float(v.get("speed", MovementSolver.BOUNCE_SPEED))
		var apex := (float(v.lo) + float(v.hi)) * 0.5 + speed * speed / (2.0 * MovementSolver.GRAVITY)
		if str(v.kind) == "bounce" and at.clamp(v.rect.position, v.rect.end).distance_to(at) <= reach and apex >= alt - WorldAuthority.REACH_ALT: return true
	return false

# ------------------------------------------------------------------ walking
## Walk a run of grid nodes with the solver, holding the input toward each next point until the body stands there at
## that point's height (not on the ground under a flight of steps). A body held in place (neither closer nor moved 4 px) for STUCK_FRAMES frames is snagged; one
## that leaves the ground has fallen through it.
func _walk(rid: String, geo: ZoneGeometry, grid: Dictionary, run: Array, what: String) -> void:
	var st := ActorState.new()
	var first: Dictionary = grid.nodes[run[0]]
	st.surface = first.s
	st.plane = first.p
	st.altitude = float(first.h)
	var held := 0.0
	var side := 0.0
	for k in range(1, run.size()):
		var goal: Vector2 = grid.nodes[run[k]].p
		var h: float = grid.nodes[run[k]].h
		var best: float = st.plane.distance_to(goal)
		var anchor: Vector2 = st.plane
		var still := 0
		var frames := 0
		while st.plane.distance_to(goal) > 6.0 or absf(st.altitude - h) > 8.0:
			var dir: Vector2 = (goal - st.plane).normalized()
			# The player's sprint: two seconds of input held one way across, not in shallow water.
			var across := signf(dir.x) if absf(dir.x) > 0.12 else 0.0
			held = held + DT if across != 0.0 and across == side else 0.0
			side = across
			var sprint := held > 2.0 and geo.volume_at(st.plane, st.altitude, "water_shallow").is_empty()
			MovementSolver.advance(st, geo, DT, dir * SPEED * (1.7 if sprint else 1.0))
			walked_s += DT
			frames += 1
			var d: float = st.plane.distance_to(goal)
			if d < best - 0.5 or st.plane.distance_to(anchor) > 4.0:
				best = minf(best, d)
				anchor = st.plane
				still = 0
			else:
				still += 1
			if st.surface == null or st.surface.stratum != "ground":
				check(false, "%s: walking %s the ground gives way at %s" % [rid, what, str(st.plane.round())])
				return
			if still >= STUCK_FRAMES or frames >= LEG_FRAMES:
				check(false, "%s: walking %s the player sticks at %s (heading for %s)" % [rid, what, str(st.plane.round()), str(goal)])
				return
	checks += 1

# ------------------------------------------------------------------ invisible walls
## Every solid footprint lies under art: a scenery prop's opaque columns, a building's facade, a block (always drawn
## over its footprint), an object's own prop.
func art_suite(rid: String, def: Dictionary, geo: ZoneGeometry) -> void:
	var roofs := {}
	for s in def.get("surfaces", []): roofs[str(s.id)] = s
	var objects := {}
	for o in def.get("objects", []): objects["obj_" + str(o.id)] = o
	for ob in geo.obstacles:
		if not ob.get("blocks", true) or ob.get("block", false) or not ob.has("footprint"): continue
		var fp: Rect2 = ob.footprint
		var id := str(ob.id)
		var span := Vector2.ZERO   # the drawn x-extent over this footprint
		if ob.has("surface"):
			var art := str(roofs.get(str(ob.surface), {}).get("art", ""))
			var e := SpriteCache.prop(art)
			if art == "" or Terrain.ATLAS_BUILDINGS.has(art) or e.is_empty(): continue   # painted across its whole roof
			span = Vector2(fp.get_center().x - float(e.frame[0]) * 0.5, fp.get_center().x + float(e.frame[0]) * 0.5)
		elif id.contains("_post_") or ob.has("cell"):
			continue   # a balcony's posts are drawn with it; the painted atlas at its size over its position
		elif str(ob.get("art", "")) == "none" and geo.surfaces.any(func(s): return s.stratum == "ground" and s.base > 8.0 and s.bounds.grow(1).encloses(fp)):
			continue   # the ground under a flight of steps or a terrace face, drawn over by them
		elif objects.has(id):
			check(not SpriteCache.prop(str(objects[id].get("prop", ""))).is_empty(), "%s: %s is solid and drawn" % [rid, id])
			continue
		else:
			var e2 := SpriteCache.prop(str(ob.get("prop", "")))
			check(str(ob.get("art", "props")) != "none" and not e2.is_empty(), "%s: scenery %s is solid but draws nothing (an invisible wall)" % [rid, id])
			if e2.is_empty(): continue
			var cols := _opaque(str(ob.prop), e2)
			var x := float(ob.position[0])
			var left := x - float(e2.anchor[0])
			span = Vector2(left + cols.x, left + cols.y + 1.0)
			if ob.get("flip", false): span = Vector2(2.0 * x - span.y, 2.0 * x - span.x)
		art_seen += 1
		check(fp.position.x >= span.x - ART_SLACK and fp.end.x <= span.y + ART_SLACK,
			"%s: %s is solid from x %d to %d, its art from %d to %d (an invisible wall)" % [rid, id, int(fp.position.x), int(fp.end.x), int(span.x), int(span.y)])

## The first and last columns of a prop's idle frame with any opaque pixel.
func _opaque(id: String, e: Dictionary) -> Vector2:
	if opaque.has(id): return opaque[id]
	var fw := int(e.frame[0])
	var out := Vector2(0, fw - 1)
	var texture := SpriteCache.tex(str(e.get("file", "")))
	var img: Image = texture.get_image() if texture else null
	if img != null:
		if img.is_compressed(): img.decompress()
		var states: Dictionary = e.get("states", {})
		var col := int((states.get("idle", states.values()[0] if not states.is_empty() else {}) as Dictionary).get("col", 0))
		var used := img.get_region(Rect2i(col * fw, 0, fw, int(e.frame[1]))).get_used_rect()
		if used.size.x > 0: out = Vector2(used.position.x, used.end.x - 1)
	opaque[id] = out
	return out
