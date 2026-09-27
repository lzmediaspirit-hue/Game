extends Node
## Visibility suite: every room, headless. Everything the player uses or walks into shows itself where it is.
##   Art:     every way (open, and closed), object, person and piece of solid scenery draws art: a prop whose texture
##            exists, with a frame of non-zero size and opaque pixels. A door in a building's front shows the doorway
##            its building draws (PortalView.entrance), an interior's door its own door on the back wall. An open gate
##            or a found hidden way draws its own art, never only its plate.
##   Place:   its anchor lies in the room's bounds and most of its art where the camera can show it.
##   Cover:   it is not hidden by a layer drawn after it (a greater depth, or the same depth added later, as `world.gd`
##            draws them: tests/draw_model.gd): at least VISIBLE of its opaque pixels show. A way into a building is
##            held to its doorway, which no tree, stall or later building may stand in front of.
##   Labels:  an open way's plate names a room and sits where the camera can show it.
## Run headless:  godot --headless --path . res://tests/visibility_suite.tscn [-- --room=<id>] [-- --verbose]

const DrawModel = preload("res://tests/draw_model.gd")
const STEP := 3.0          # px between the pixels sampled
const VISIBLE := 0.5       # the share of a thing's opaque pixels that must show
const VIEW_H := 720.0      # the camera's view (world.gd camera_target: centre y clamped to the room's y range)
const IN_VIEW := 0.5       # the share of a thing's art that must lie where the camera can show it

var checks := 0
var failures := 0
var verbose := false
var seen := {}             # kind -> count of things held to the rules

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
		if str(a) == "--verbose": verbose = true
	var rooms := 0
	for rid in ContentDB.rooms:
		if only != "" and rid != only: continue
		room(str(rid))
		rooms += 1
	print("visibility_suite: %d rooms, %s" % [rooms, str(seen)])
	check(only != "" or rooms >= 160 and int(seen.get("portal", 0)) > 300 and int(seen.get("object", 0)) > 900,
		"the suite held every room's ways and objects to the rules (%d rooms)" % rooms)
	print("visibility_suite: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

func room(rid: String) -> void:
	var def := ContentDB.room(rid)
	var geo := ZoneGeometry.new()
	geo.configure(WorldAuthority.compile_geometry(def))
	var all := DrawModel.layers(def, geo)
	var view := _view(def, geo)
	for l in all:
		match str(l.kind):
			"portal": _portal(rid, def, all, l, view)
			"object", "npc": _thing(rid, all, l, view)
			"scenery":
				if l.get("blocks", false): _thing(rid, all, l, view)

## The part of the room the camera can show: the room's width, and the camera's y range grown by half its view.
func _view(def: Dictionary, geo: ZoneGeometry) -> Rect2:
	var cam: Dictionary = def.get("camera", {})
	var b: Array = cam.get("bounds", [])
	var y0 := float(b[1]) if b.size() == 4 else float(cam.get("y_min", ContentDB.movement("camera.y_min", 180)))
	var y1 := float(b[3]) if b.size() == 4 else float(cam.get("y_max", ContentDB.movement("camera.y_max", 600)))
	return Rect2(geo.bounds.position.x, y0 - VIEW_H * 0.5, geo.bounds.size.x, y1 - y0 + VIEW_H)

func _in_bounds(def: Dictionary, p: Vector2) -> bool:
	var b: Array = def.get("bounds", [0, 480, 1280, 480])
	return p.x >= float(b[0]) and p.x <= float(b[0]) + float(b[2]) and p.y >= float(b[1]) and p.y <= float(b[1]) + float(b[3] if b.size() > 3 else 480)

## An object, a person or a piece of solid scenery.
func _thing(rid: String, all: Array, l: Dictionary, view: Rect2) -> void:
	seen[l.kind] = int(seen.get(l.kind, 0)) + 1
	var d: Dictionary = l.def
	var at_a: Array = d.get("at", d.get("position", [0, 0]))
	var at := Vector2(float(at_a[0]), float(at_a[1]))
	check(_in_bounds(ContentDB.room(rid), at), "%s: %s stands at %s, outside the room" % [rid, l.what, str(at)])
	if l.kind == "npc":
		_cover(rid, all, l, [], l.fills)
		return
	if str(d.get("type", "")) == "pickup" and str(l.get("prop", "")) in ["", "none"]:
		# A pickup with no prop of its own shows its item's icon in a gold ring over a pool of light.
		check(not SpriteCache.icon_renders(str(d.get("item", ""))).is_empty(), "%s: pickup %s shows its item %s, which has no icon" % [rid, d.id, str(d.get("item", ""))])
		return
	if str(l.get("prop", "")) == "none":
		# A thing with no prop of its own marks art the room draws where it is (the library's racks, a well, a door).
		var p := at - Vector2(0, float(d.get("alt", 0)))
		check(_drawn_in(all, l, Rect2(p + Vector2(-32, -64), Vector2(64, 68))), "%s: %s at %s draws nothing, and nothing the room draws is there" % [rid, l.what, str(at)])
		return
	if not _art(rid, l, "draws %s" % str(l.get("prop", d.get("cell", "")))): return
	_placed(rid, l, view)
	_cover(rid, all, l, l.pieces, [])

## A way: its art open and closed, where it stands, its plate, and what stands over it.
func _portal(rid: String, def: Dictionary, all: Array, l: Dictionary, view: Rect2) -> void:
	seen["portal"] = int(seen.get("portal", 0)) + 1
	var p: Dictionary = l.def
	var at := Vector2(float(p.at[0]), float(p.at[1]))
	check(_in_bounds(def, at) or p.has("surface"), "%s: %s stands at %s, outside the room" % [rid, l.what, str(at)])
	var closed := str(l.art_closed)
	if closed != "":
		check(not DrawModel.prop_piece(closed, "idle", at).is_empty(), "%s: %s shut draws %s, which has no art" % [rid, l.what, closed])
	# The plate: an open way names the room it leads to, where the camera can show it.
	var to := str(p.get("to", ""))
	if not ContentDB.room(to).is_empty():
		check(ContentDB.name_of("rooms", to) != "", "%s: %s names no room on its plate" % [rid, l.what])
		check(float(l.label_y) - 30.0 >= view.position.y, "%s: %s has its plate at y %d, above what the camera shows (from %d)" % [rid, l.what, int(l.label_y), int(view.position.y)])
	match str(l.entrance):
		"building":
			# The doorway its building draws: held to it at the building's depth.
			var front := PortalView.building_front(p, def)
			var door: Array = front.door
			var bl: Dictionary = {}
			for m in all:
				if m.kind == "surface" and str(m.id) == str(front.id): bl = m
			var doorway := Rect2(float(door[0]), at.y - 14.0 - 64.0, float(door[1]) - float(door[0]), 64.0)
			var dl := bl.duplicate()
			dl.what = "%s (the doorway of %s)" % [l.what, str(front.id)]
			_cover(rid, all, dl, [], [doorway], bl)
		"decor":
			for m in all:
				if m.kind == "decor" and str(m.id) in PortalView.WAY_DECOR and absf(float(m.def.at[0]) - at.x) <= 24.0 and absf(float(m.def.at[1]) - at.y) <= 40.0:
					var dl: Dictionary = m.duplicate()
					dl.what = "%s (its door)" % l.what
					_cover(rid, all, dl, m.pieces, [], m)
					break
		_:
			if not _art(rid, l, "draws %s open" % ("nothing" if str(l.art) == "" else str(l.art))): return
			_placed(rid, l, view)
			_cover(rid, all, l, l.pieces, [])

## The layer draws art: a texture that loads, a frame of some size with opaque pixels.
func _art(rid: String, l: Dictionary, what: String) -> bool:
	var ok: bool = not l.pieces.is_empty()
	for piece in l.pieces:
		ok = ok and piece.get("tex") != null and (piece.rect as Rect2).size.x > 0.0 and (piece.rect as Rect2).size.y > 0.0 and DrawModel.used(piece).size.x > 0
	check(ok, "%s: %s %s, which draws no art (missing, empty or blank)" % [rid, l.what, what])
	return ok

## Another layer draws art in `box` (a thing, a decor prop, a building, a platform).
func _drawn_in(all: Array, l: Dictionary, box: Rect2) -> bool:
	for m in all:
		if m == l or m.get("cond", false) or m.kind in ["npc", "wall"]: continue
		if m.fills.any(func(f): return (f as Rect2).intersects(box)): return true
		for piece in m.pieces:
			if not (piece.rect as Rect2).intersects(box): continue
			var y := box.position.y
			while y < box.end.y:
				var x := box.position.x
				while x < box.end.x:
					if DrawModel.alpha(piece, Vector2(x, y)) >= 0.5: return true
					x += STEP
				y += STEP
	return false

## Most of its art lies where the camera can show it.
func _placed(rid: String, l: Dictionary, view: Rect2) -> void:
	for piece in l.pieces:
		var r: Rect2 = piece.rect
		var inside := r.intersection(view).get_area() / maxf(1.0, r.get_area())
		check(inside >= IN_VIEW, "%s: %s draws at %s, %d%% of it where the camera can show it (%s)" % [rid, l.what, str(r), int(inside * 100.0), str(view)])

## At least VISIBLE of its opaque pixels show: none of the layers drawn after `under` (itself, or the building a
## doorway is part of) has art there.
func _cover(rid: String, all: Array, l: Dictionary, pieces: Array, fills: Array, under: Dictionary = {}) -> void:
	var at: Dictionary = under if not under.is_empty() else l
	var total := 0
	var shown := 0
	var by := {}
	for area in fills + pieces.map(func(pc): return pc.rect):
		var r: Rect2 = area
		var y := r.position.y + STEP * 0.5
		while y < r.end.y:
			var x := r.position.x + STEP * 0.5
			while x < r.end.x:
				var q := Vector2(x, y)
				var own := fills.any(func(f): return (f as Rect2).has_point(q)) or pieces.any(func(pc): return DrawModel.alpha(pc, q) >= 0.5)
				if own:
					total += 1
					var m := DrawModel.covering(all, at, q)
					if m.is_empty(): shown += 1
					else: by[m.what] = int(by.get(m.what, 0)) + 1
				x += STEP
			y += STEP
	if total == 0: return
	var share := float(shown) / float(total)
	if verbose and share < 1.0: print("  %s: %s shows %d%% (%s)" % [rid, l.what, int(share * 100.0), str(by)])
	var worst := ""
	for k in by: if worst == "" or by[k] > by[worst]: worst = k
	check(share >= VISIBLE, "%s: %s is hidden: %d%% of it shows, the rest under %s (z %d over its %d)" % [rid, l.what, int(share * 100.0), worst,
		int(_layer(all, worst).get("z", 0)), int(at.z)])

func _layer(all: Array, what: String) -> Dictionary:
	for m in all: if m.what == what: return m
	return {}
