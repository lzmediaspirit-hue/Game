class_name WorldLabels
extends RefCounted
## P5a (review G4; docs/ui_style_guide.md §9 "World labels"): the names over the world never stack, and never sit
## under a HUD control. Each view keeps its label's box at its own offset from the figure, by kind: a foe's level and
## name over its head, the party's thin HP lines lower, just over their heads (only in a fight), an NPC's nameplate
## under the feet, a way's or a thing's plate over its art. Labels draw on their own canvas item above every figure
## (LABEL_Z). Once a frame `world.gd` hands the boxes on screen to `resolve`, which places them one by one in a fixed
## order: a box that would touch one already placed, or a HUD control, moves by whole rows (up for the labels over a
## head, down for the plates under the feet) until it is clear; then the other way (a plate under the feet goes over
## the head instead); else to the row it overlaps least, never off the screen. A box keeps last frame's row while
## that row is still clear, so labels do not flicker between rows as figures move.
##
## Presentation only: it reads the views and the HUD's rects and writes nothing but each view's `label_offset`.

const ROW_GAP := 2.0
const ROWS_OUT := 3        # rows tried in a label's own direction ...
const ROWS_BACK := 2       # ... then the other way
const ROWS_MORE := 8       # ... then, for a crowd, further rows its own way and half a box aside
## A living foe this close to the player (plane px), or any boss in the room, puts the party in a fight (the HUD's
## technique ring comes out, the party's HP lines show).
const FIGHT_NEAR := 560.0

## The order labels are placed in (a placed label keeps its place; later ones move round it) and the way each kind
## moves first: -1 up (a way's or a thing's plate, the labels over a head), +1 down (an NPC's plate under the feet).
const ORDER := {"place": 0, "boss": 1, "focus": 2, "elite": 3, "foe": 4, "npc": 5, "ally": 6}
const DIRECTION := {"place": -1, "boss": -1, "focus": 1, "elite": -1, "foe": -1, "npc": 1, "ally": -1}

## Labels draw on their own canvas item at this depth: over every figure, terrain piece and prop in the room (1500 + y),
## under the effects layer (4000), so a figure standing in front never hides a name.
const LABEL_Z := 3600

## The party's fight state as the HUD reads it (hud.gd sets it each frame; false with no HUD).
static var party_fight := false

## A view's label node: a child canvas item at LABEL_Z that draws with `draw`.
static func make_tag(view: Node2D, draw: Callable) -> Node2D:
	var tag := Node2D.new()
	tag.z_as_relative = false
	tag.z_index = LABEL_Z
	tag.texture_filter = view.texture_filter
	tag.draw.connect(draw)
	view.add_child(tag)
	return tag

## Place `items` round each other and the `obstacles`, inside `bounds` (the screen; a row that leaves it costs dearly).
## items: [{id, kind, rect: Rect2 on screen at no offset, prev: Vector2 last frame's offset, near: float, closer first}]
## obstacles: [Rect2] on screen (the HUD's controls and panels).
## Returns {id: Vector2 offset}; every offset is a whole number of rows of its own box (row = height + ROW_GAP).
static func resolve(items: Array, obstacles: Array, bounds := Rect2(0, 0, 1280, 720)) -> Dictionary:
	var order := items.filter(func(it): return (it.rect as Rect2).size.x > 0.0 and (it.rect as Rect2).size.y > 0.0)
	order.sort_custom(func(a, b):
		var ka := int(ORDER.get(str(a.kind), 9))
		var kb := int(ORDER.get(str(b.kind), 9))
		if ka != kb: return ka < kb
		var na := float(a.get("near", 0.0))
		var nb := float(b.get("near", 0.0))
		if na != nb: return na < nb
		return str(a.id) < str(b.id))
	var placed: Array = []
	var out := {}
	for it in order:
		var r: Rect2 = it.rect
		var dir := int(DIRECTION.get(str(it.kind), -1))
		var cands: Array = [Vector2.ZERO]
		if dir != 0:
			var step := r.size.y + ROW_GAP
			var prev: Vector2 = it.get("prev", Vector2.ZERO)
			if prev != Vector2.ZERO: cands.append(prev)
			for k in range(1, ROWS_OUT + 1): cands.append(Vector2(0, dir * step * k))
			# A plate under the feet with no room below goes over the head (its `flip`), and rows up from there; any other
			# label tries rows the other way.
			var flip: Vector2 = it.get("flip", Vector2.ZERO)
			if flip != Vector2.ZERO:
				for k in ROWS_BACK + 1: cands.append(flip - Vector2(0, step * k))
			else:
				for k in range(1, ROWS_BACK + 1): cands.append(Vector2(0, -dir * step * k))
			# A crowd those rows cannot clear (a pack of foes in a fight, the prototype's QA): more rows its own way, then
			# half a box aside at each of them. Tried last, so a label the rows above clear keeps its place.
			for k in range(ROWS_OUT + 1, ROWS_MORE + 1): cands.append(Vector2(0, dir * step * k))
			var aside := r.size.x * 0.5 + 6.0
			for k in ROWS_MORE + 1:
				for sx in [-aside, aside]: cands.append(Vector2(sx, dir * step * k))
		var best: Vector2 = cands[0]
		var best_cost := INF
		var base_out := _outside(r, bounds)
		for off in cands:
			var moved := Rect2(r.position + off, r.size)
			# A label already partly off the screen keeps that share; a row that takes it further off is dear.
			var cost := overlap(moved, placed, obstacles) + 4.0 * maxf(0.0, _outside(moved, bounds) - base_out)
			if cost < best_cost:
				best = off
				best_cost = cost
			if cost <= 0.0: break
		placed.append(Rect2(r.position + best, r.size))
		out[it.id] = best
	return out

## How much of `r` is covered: the area it shares with the labels placed so far, and twice that for a HUD control
## (a label is sooner beside another label than under a button).
static func overlap(r: Rect2, placed: Array, obstacles: Array) -> float:
	var cost := 0.0
	for p in placed: cost += _shared(r, p)
	for o in obstacles: cost += 2.0 * _shared(r, o)
	return cost

## The area of `r` outside `bounds` (none when `bounds` is empty).
static func _outside(r: Rect2, bounds: Rect2) -> float:
	if bounds.size.x <= 0.0: return 0.0
	return r.size.x * r.size.y - _shared(r, bounds)

static func _shared(a: Rect2, b: Rect2) -> float:
	var i := a.intersection(b)
	return i.size.x * i.size.y if i.size.x > 0.0 and i.size.y > 0.0 else 0.0

## Any two placed boxes that still touch (the tests' check): [[id, id], ...].
static func touching(items: Array, offsets: Dictionary) -> Array:
	var out: Array = []
	for i in items.size():
		for j in range(i + 1, items.size()):
			var a: Rect2 = items[i].rect
			var b: Rect2 = items[j].rect
			var ra := Rect2(a.position + offsets.get(items[i].id, Vector2.ZERO), a.size)
			var rb := Rect2(b.position + offsets.get(items[j].id, Vector2.ZERO), b.size)
			if _shared(ra, rb) > 0.0: out.append([items[i].id, items[j].id])
	return out

## Is a fight on round the player at `plane`: a boss alive in the room, a heavenly tribulation, or a living foe that is
## not passive, hidden or yielding within FIGHT_NEAR.
static func fight_near(c, plane: Vector2) -> bool:
	if c == null or Game.room_rt == null: return false
	if Game.progression.is_under_tribulation(c.id): return true
	for e in Game.room_rt.living_enemies():
		if e.team != "enemy" or e.def.get("passive", false) or e.ai.get("surrendered", false): continue
		if e.is_boss(): return true
		if not e.hidden and e.plane.distance_to(plane) < FIGHT_NEAR: return true
	return false

## Gather every view's label (world coordinates, `xf` to the screen), place them, and give each view its offset.
## `views`: [{id, view, kind, near}]; a view offers `label_box` (local, at no offset) and takes `label_offset`.
static func place_views(views: Array, xf: Transform2D, obstacles: Array, screen := Rect2(-160, -160, 1600, 1040)) -> Dictionary:
	var items: Array = []
	var by_id := {}
	for v in views:
		var node = v.view
		if not is_instance_valid(node) or not node.visible: continue
		var box: Rect2 = node.label_box
		if box.size.x <= 0.0: continue
		var r := Rect2(xf * (node.position + box.position), box.size)
		if not screen.intersects(r): continue
		var it := {"id": v.id, "kind": v.kind, "rect": r, "prev": node.label_offset, "near": float(v.get("near", 0.0))}
		if "label_flip" in node: it.flip = node.label_flip
		items.append(it)
		by_id[v.id] = node
	var offs := resolve(items, obstacles)
	for id in offs: by_id[id].label_offset = offs[id]
	return {"items": items, "offsets": offs}
