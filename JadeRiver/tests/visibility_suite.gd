extends "res://tests/lib/suite.gd"
## Visibility suite (on the height grid since S12a retired the side view): every room of the world as the world view
## builds it (TopdownPlaces on the room's layout, the room entered through the World authority), headless. Everything
## the player uses or walks into shows itself where it is.
##   Art:    every thing (an object, a pickup) draws art: its prop a frame on a texture that loads, a pickup with no prop
##           its item's icon, a thing with no prop of its own art the layout draws where it is (a prop, a place's sight
##           or a stair within two tiles) or a light of its own (TopdownLight.OBJECT_LIGHTS); every person is drawn in the top-down style, every piece of their outfit with
##           its layer; every way has its mark on the floor and its plate on the overlay.
##   Place:  its anchor lies on the grid; no person or thing stands inside a solid prop's footprint (drawn under it)
##           unless on the prop's top.
##   Labels: a way into a real room names the room on its plate; a way into a building (tests/lib/building_ways.gd)
##           stands in the building's doorway.
## Run headless:  godot --headless --path . res://tests/visibility_suite.tscn [-- --room=<id>] [-- --verbose]

const NEAR_ART := 2         # tiles round a thing with no prop of its own where the layout's art may stand for it

var seen := {}              # kind -> count of things held to the rules
var holder: Node2D

func _main() -> void:
	var only := ""
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--room="): only = str(a).trim_prefix("--room=")
		if str(a) == "--verbose": verbose = true
	var folder := run_root() + "saves/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	check(Game.submit({"type": "create_character", "slot": 1, "name": "Seer"}).get("ok", false) and Game.submit({"type": "enter_character", "slot": 1}).get("ok", false),
		"a character to see the rooms with")
	holder = Node2D.new()
	add_child(holder)
	var rooms := 0
	for rid in ContentDB.rooms:
		if only != "" and rid != only: continue
		room(str(rid))
		rooms += 1
	print("visibility_suite: %d rooms, %s" % [rooms, str(seen)])
	check(only != "" or rooms >= 160 and int(seen.get("portal", 0)) > 300 and int(seen.get("object", 0)) > 900,
		"the suite held every room's ways and objects to the rules (%d rooms)" % rooms)
	holder.free()
	end_suite()

func room(rid: String) -> void:
	var c = Game.active()
	Game.world.load_room(c, rid, "")
	GameEvents.flush()
	check(Game.room_rt != null and Game.room_rt.room_id == rid and Game.room_rt.topdown != null, "%s is entered on the grid" % rid)
	if Game.room_rt == null or Game.room_rt.room_id != rid: return
	var grid: TopdownRoom = Game.room_rt.topdown
	var def: Dictionary = Game.room_rt.def
	var sorted := Node2D.new()
	var floor_layer := Node2D.new()
	var overlay := Node2D.new()
	for n in [sorted, floor_layer, overlay]: holder.add_child(n)
	var built := TopdownPlaces.build(grid, def, sorted, floor_layer, overlay)
	for o in def.get("objects", []):
		if str(o.get("type", "")) == "decor" or not o.has("at"): continue
		var fig = built.figures.get(str(o.id))
		if str(o.type) == "npc": _person(rid, grid, o, fig)
		else: _thing(rid, grid, o, fig)
	var marks: Array = floor_layer.get_children().filter(func(m): return m is TopdownPlaces.WayMark)
	for p in def.get("portals", []): _way(rid, grid, p, built.portal_views, marks)
	for n in [sorted, floor_layer, overlay]: n.free()

## A person: a figure in the top-down style, every piece of their outfit drawn, standing on the grid.
func _person(rid: String, grid: TopdownRoom, o: Dictionary, fig) -> void:
	seen["npc"] = int(seen.get("npc", 0)) + 1
	var drawn: bool = fig is TopdownPlaces.Figure and fig.art is TopdownPlaces.Person and (fig.art.figure as TopdownFigure).missing.is_empty() \
		and not (fig.art.figure as TopdownFigure).layers.is_empty()
	check(drawn, "%s: %s is drawn in the top-down style, every piece of their outfit with its layer%s" % [rid, o.id,
		" (missing %s)" % str(fig.art.figure.missing) if fig is TopdownPlaces.Figure and fig.art is TopdownPlaces.Person else ""])
	_placed(rid, grid, o)

## A thing: its art, where it stands.
func _thing(rid: String, grid: TopdownRoom, o: Dictionary, fig) -> void:
	seen["object"] = int(seen.get("object", 0)) + 1
	check(fig is TopdownPlaces.Figure and fig.art != null, "%s: %s has its figure in the room" % [rid, o.id])
	if not (fig is TopdownPlaces.Figure) or fig.art == null: return
	_placed(rid, grid, o)
	if not (fig.art is ObjectView): return   # a thing the places table adds, drawn by its place (TopdownPlaceArt)
	var prop: String = fig.art.current_prop()
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	if prop == "" or prop == "none":
		if str(o.type) == "pickup":
			check(not SpriteCache.icon_renders(str(o.get("item", ""))).is_empty(), "%s: pickup %s shows its item %s, which has no icon" % [rid, o.id, str(o.get("item", ""))])
		else:
			var lit := TopdownLight.OBJECT_LIGHTS.has(str(o.type))   # a light of its own there (a Qi spring's jade breath)
			check(lit or _layout_art_near(grid, rid, TopdownRoom.cell_of(at)), "%s: %s at %s draws nothing, and nothing the layout draws is there" % [rid, o.id, str(TopdownRoom.cell_of(at))])
		return
	check(_prop_drawn(prop), "%s: %s draws %s, which has no art (missing, empty or blank)" % [rid, o.id, prop])

## A prop's art: a texture that loads and a first frame of some size with opaque pixels.
var _drawn := {}
func _prop_drawn(prop: String) -> bool:
	if _drawn.has(prop): return _drawn[prop]
	var e := SpriteCache.prop(prop)
	var ok := false
	if not e.is_empty():
		var tex := SpriteCache.tex(str(e.get("file", "")))
		var size := SpriteCache.prop_size(prop)
		if tex != null and size.x > 0.0 and size.y > 0.0:
			var img := tex.get_image()
			ok = img != null and img.get_region(Rect2i(0, 0, int(size.x), int(size.y))).get_used_rect().size.x > 0
	_drawn[prop] = ok
	return ok

## A way: its mark on the floor, its plate on the overlay naming the room it leads to, a building's door in its doorway.
func _way(rid: String, grid: TopdownRoom, p: Dictionary, views: Array, marks: Array) -> void:
	seen["portal"] = int(seen.get("portal", 0)) + 1
	var pid := str(p.id)
	check(views.any(func(v): return str(v.def.get("id", "")) == pid) and marks.any(func(m): return str(m.def.get("id", "")) == pid),
		"%s: the way %s has its plate and its mark on the floor" % [rid, pid])
	var c := TopdownRoom.cell_of(Vector2(float(p.at[0]), float(p.at[1])))
	check(c.x >= -1 and c.y >= -1 and c.x <= grid.w and c.y <= grid.h, "%s: the way %s stands at %s, off the grid" % [rid, pid, str(c)])
	var to := str(p.get("to", ""))
	if not ContentDB.room(to).is_empty():
		check(ContentDB.name_of("rooms", to) != "", "%s: the way %s names no room on its plate" % [rid, pid])
	var own: Array = ContentDB.room(rid).get("portals", []).filter(func(q): return str(q.id) == pid)
	if not own.is_empty() and preload("res://tests/lib/building_ways.gd").into_building(own[0], ContentDB.room(rid)):
		check(grid.entrance(pid) == "building", "%s: the way %s into a building stands in its doorway (%s)" % [rid, pid, grid.entrance(pid)])

## Its anchor on the grid, and not inside a solid prop's footprint unless on the prop's top.
func _placed(rid: String, grid: TopdownRoom, o: Dictionary) -> void:
	var c := TopdownRoom.cell_of(Vector2(float(o.at[0]), float(o.at[1])))
	check(grid.inside(c.x, c.y), "%s: %s stands at %s, off the grid" % [rid, o.id, str(c)])
	if not grid.inside(c.x, c.y): return
	var i := c.y * grid.w + c.x
	var under := grid.solid[i] == 1 and grid.top_of[i] == 0 and _prop_at(grid, c) != ""
	check(not under, "%s: %s at %s stands inside %s, drawn under it" % [rid, o.id, str(c), _prop_at(grid, c)])

## The layout prop whose footprint holds `c` ("" when none).
func _prop_at(grid: TopdownRoom, c: Vector2i) -> String:
	for p in grid.props:
		if Rect2i(p.cell, p.size).has_point(c) and p.art.get("solid", true): return str(p.kind)
	return ""

## The layout draws art within NEAR_ART tiles of `c`: a prop, a stair, a place's sight, or a building's wall.
func _layout_art_near(grid: TopdownRoom, rid: String, c: Vector2i) -> bool:
	var box := Rect2i(c - Vector2i(NEAR_ART, NEAR_ART), Vector2i(NEAR_ART * 2 + 1, NEAR_ART * 2 + 1))
	if grid.props.any(func(p): return Rect2i(p.cell, p.size).intersects(box)): return true
	if grid.stairs.any(func(s): return (s.rect as Rect2i).intersects(box)): return true
	for s in PlaceRules.solids(rid):
		if (s as Rect2i).intersects(box): return true
	return false
