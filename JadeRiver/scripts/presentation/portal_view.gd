class_name PortalView
extends Node2D
## Portal art and label (S17): edge gates are jade swirls between lantern posts,
## doors are building or interior doors, sealed gates show their lock rune and
## condition, "Coming soon" for planned rooms. An open way always names where it
## leads on a plate with a bobbing arrow, brighter when the player stands at it; a
## sealed way shows its condition when near. The arrow and the plate draw on their
## own canvas item above every figure and building (WorldLabels.LABEL_Z), so a door
## in a building's front is never hidden by the facade it stands in.

const Terrain = preload("res://scripts/terrain.gd")

var def: Dictionary = {}
var t := 0.0
var near := false
var state: Dictionary = {"open": true, "text": ""}
var wall_y := INF      # an interior door stands on the back wall's foot, this far above `at`
var door_top := -96.0  # where the arrow and plate sit
var label_dx := 0.0    # a way at the room's edge names itself a little inside, not half off-screen
## P5a (G4): the plate's box (local, at no offset) and the offset in whole rows the world's label pass gives it.
var label_box := Rect2()
var label_offset := Vector2.ZERO
var tag: Node2D   # the arrow and the plate, above every figure (WorldLabels.LABEL_Z)

func setup(p: Dictionary, room_def: Dictionary = {}) -> void:
	def = p
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = p.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]))
	z_index = 1500 + int(float(at[1])) - 30
	if _wall_door(p, room_def):
		wall_y = minf(0.0, float(room_def.wall.get("bottom", at[1])) - float(at[1]))
	door_top = (wall_y - 128.0) if wall_y != INF else -96.0
	var b: Array = room_def.get("bounds", [])
	if b.size() >= 3:
		label_dx = clampf(position.x, float(b[0]) + 150.0, float(b[0]) + float(b[2]) - 150.0) - position.x
	tag = WorldLabels.make_tag(self, _draw_tag)

## An interior's way out: a door with no art of its own on the back wall (drawn here, as the `door` prop).
static func _wall_door(p: Dictionary, room_def: Dictionary) -> bool:
	return str(p.get("type", "")) == "door" and str(p.get("art", "")) == "" and not p.get("facade", false) and not room_def.get("wall", {}).is_empty()

## The building a door stands at the foot of (a roof's front, a portal on the plane): {id, art, door: the doorway its
## art draws, [x0, x1] in room x, [] when it draws none}. {} for every other way: a road, a boat, a cave, a back wall.
static func building_front(p: Dictionary, room_def: Dictionary) -> Dictionary:
	if str(p.get("type", "")) != "door" or p.has("surface") or not room_def.get("wall", {}).is_empty(): return {}
	var at: Array = p.get("at", [0, 0])
	var x := float(at[0])
	var y := float(at[1])
	for s in room_def.get("surfaces", []):
		if str(s.get("kind", "")) != "roof": continue
		var r: Array = s.get("rect", [0, 0, 0, 0])
		var front := float(r[1]) + float(r[3])
		if x < float(r[0]) or x > float(r[0]) + float(r[2]) or y < front or y > front + 40.0: continue
		return {"id": str(s.get("id", "")), "art": str(s.get("art", "")), "door": Terrain.doorway(s)}
	return {}

## What shows the player a way in, open (S17; a closed door always shows the sealed gate): "art" (its own gate or swirl),
## "wall" (an interior's door on the back wall), "decor" (a door placed in the room at it: a cave abode, a raised door),
## "building" (it stands in the doorway its building's art draws), or "" (nothing but the arrow and the plate). A way
## into a building must show "decor" or "building" (tests/tutorial_order.gd, data_validation).
static func entrance(p: Dictionary, room_def: Dictionary) -> String:
	var type := str(p.get("type", "edge"))
	if not str(p.get("art", "")) in ["", "none"] or type in ["edge", "sealed", "dungeon"]: return "art"
	if type != "door": return ""
	if _wall_door(p, room_def): return "wall"
	var at: Array = p.get("at", [0, 0])
	for d in room_def.get("decor", []):
		var da: Array = d.get("at", [0, 0])
		if str(d.get("prop", "")) == "door" and absf(float(da[0]) - float(at[0])) <= 24.0 and absf(float(da[1]) - float(at[1])) <= 40.0: return "decor"
	var door: Array = building_front(p, room_def).get("door", [])
	if door.size() == 2 and float(at[0]) >= float(door[0]) and float(at[0]) <= float(door[1]): return "building"
	return ""

func _process(delta: float) -> void:
	t += delta
	var c = Game.active()
	if c:
		state = Game.world.portal_state(c, def)
		near = Game.world.portal_near(c, def)
	visible = not state.get("hidden", false)
	queue_redraw()
	tag.queue_redraw()

func _draw() -> void:
	var type := str(def.get("type", "edge"))
	var art := str(def.get("art", ""))
	if art == "":
		art = {"edge": "portal_swirl", "sealed": "sealed_gate", "dungeon": "portal_swirl"}.get(type, "")
		if type != "edge" and not state.open: art = "sealed_gate"
	var bob := 0.5 + 0.5 * sin(t * 4.0)
	if art != "none" and art != "":
		SpriteCache.draw_prop(self, art, "idle", t, Vector2.ZERO, false, Color(0.6, 0.6, 0.65) if not state.open and art == "portal_swirl" else Color.WHITE)
	elif type == "door" and wall_y != INF:
		# An interior exit: a double door on the back wall that swings open as the player comes to it.
		var foot := Vector2(0, wall_y)
		draw_colored_polygon(PackedVector2Array([foot + Vector2(-60, 2), foot + Vector2(60, 2), foot + Vector2(80, 26), foot + Vector2(-80, 26)]),
			Color(UiKit.PALE_GOLD, 0.10 + 0.08 * bob))
		SpriteCache.draw_prop(self, "door", "open" if near and state.open else "closed", t, foot, false)

## The arrow over a door and the plate naming the way, on `tag` (above every figure and facade).
func _draw_tag() -> void:
	var type := str(def.get("type", "edge"))
	var bob := 0.5 + 0.5 * sin(t * 4.0)
	if type == "door":
		_draw_arrow(Vector2(0, door_top - 8 + bob * 5), bob)
	_draw_label(type)

## A chevron over the way in, pulsing so the eye finds it against busy walls.
func _draw_arrow(p: Vector2, bob: float) -> void:
	var col := Color(UiKit.PALE_GOLD, 0.75 + 0.25 * bob) if state.open else Color(UiKit.MIST, 0.6)
	var pts := PackedVector2Array([p + Vector2(-14, -10), p + Vector2(14, -10), p + Vector2(0, 6)])
	tag.draw_colored_polygon(PackedVector2Array([p + Vector2(-17, -12), p + Vector2(17, -12), p + Vector2(0, 9)]), Color(UiKit.INK, 0.85))
	tag.draw_colored_polygon(pts, col)

func _draw_label(type: String) -> void:
	var label := str(state.text)
	label_box = Rect2()
	if label == "" or (not state.open and not near): return
	var y := (door_top - 30.0) if type == "door" else -150.0
	var col := UiKit.PALE_GOLD if state.open else UiKit.MIST
	if not near: col = Color(col, 0.82)
	var size := 19 if near else 17
	tag.draw_set_transform(Vector2(label_dx, 0))
	var plate := UiKit.draw_nameplate(tag, ("▲ " if state.open and near else "") + label, "", y + label_offset.y, col, UiKit.MIST, size)
	label_box = Rect2(plate.position + Vector2(label_dx, -label_offset.y), plate.size)
	tag.draw_set_transform(Vector2.ZERO)
