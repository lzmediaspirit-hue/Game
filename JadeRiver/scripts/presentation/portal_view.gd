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
## The art an open way draws by its type when it names none: an edge or a way into a dungeon swirls, a road's gate
## stands open, a hidden way once found shows its cleft, and a door with no building's doorway or door of its own at it
## stands as a door (PortalView.entrance "door").
const TYPE_ART := {"edge": "portal_swirl", "sealed": "sealed_gate", "dungeon": "portal_swirl", "gate": "road_gate", "hidden": "hidden_way", "door": "door"}
## Decor that is itself a way in where a door or gate stands at it: a door, a boat or a sky ship to board, a tent's
## open front, a swirl or an arch.
const WAY_DECOR := ["door", "lu_boat", "sky_ship", "cloud_skiff", "recruiter_tent_jade", "recruiter_tent_cloud", "portal_swirl", "paifang_gate"]

var def: Dictionary = {}
var t := 0.0
var near := false
var state: Dictionary = {"open": true, "text": ""}
var wall_y := INF      # an interior door stands on the back wall's foot, this far above `at`
var door_top := -96.0  # where the arrow and plate sit
var label_dx := 0.0    # a way at the room's edge names itself a little inside, not half off-screen
var label_span := Vector2(-INF, INF)   # the room's x extent: a long plate (the gate's line) is kept wholly inside it
## P5a (G4): the plate's box (local, at no offset) and the offset in whole rows the world's label pass gives it.
var label_box := Rect2()
var label_offset := Vector2.ZERO
var arrow_box := Rect2()   # the chevron over a door, local, as last drawn (none when not drawn): other plates keep off it
var tag: Node2D   # the arrow and the plate, above every figure (WorldLabels.LABEL_Z)
## A shut way walked into (WorldShared.request_portal): its own plate is the refusal, lit up this long, in place of a
## line floating over the player and one in the log (the prototype's QA saw the gate's line three times at once).
const TOUCH_S := 1.8
var touched := 0.0
var shows := ""   # what shows the way (entrance)
## The top-down view (redesign Phase 4) draws the way itself in its pixel viewport (a building's doorway, the gap in an
## interior's wall, the marks of an edge); this view then draws only the arrow and the plate, on its overlay.
var label_only := false

func setup(p: Dictionary, room_def: Dictionary = {}) -> void:
	def = p
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = p.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]))
	z_index = 1500 + int(float(at[1])) - 30
	if _wall_door(p, room_def):
		wall_y = minf(0.0, float(room_def.wall.get("bottom", at[1])) - float(at[1]))
	door_top = (wall_y - 128.0) if wall_y != INF else -96.0
	shows = entrance(p, room_def)
	var b: Array = room_def.get("bounds", [])
	if b.size() >= 3:
		label_span = Vector2(float(b[0]), float(b[0]) + float(b[2]))
		label_dx = clampf(position.x, label_span.x + 150.0, label_span.y - 150.0) - position.x
	tag = WorldLabels.make_tag(self, _draw_tag)

## An interior's way out: a door with no art of its own on the back wall (drawn here, as the `door` prop).
static func _wall_door(p: Dictionary, room_def: Dictionary) -> bool:
	return str(p.get("type", "")) == "door" and str(p.get("art", "")) == "" and not p.get("facade", false) and not room_def.get("wall", {}).is_empty()

## The building a door stands at the foot of (a roof's front, a portal on the plane): {id, art, door: the doorway its
## art draws, [x0, x1] in room x, [] when it draws none}. {} for every other way: a road, a boat, a cave, a back wall.
static func building_front(p: Dictionary, room_def: Dictionary) -> Dictionary:
	if not str(p.get("type", "")) in ["door", "gate"] or p.has("surface") or not room_def.get("wall", {}).is_empty(): return {}
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

## What shows the player a way in, open (S17; a closed way shows the sealed gate, a back-wall door itself shut): "art"
## (its own art, or its type's: a swirl, a road gate, a found hidden way), "wall" (an interior's door on the back wall),
## "decor" (a way placed in the room at it: a door, a boat, a tent), "building" (it stands in the doorway its building's
## art draws), or "door" (a door drawn where it stands). A way into a building must show "decor" or "building"
## (tests/tutorial_order.gd, data_validation); every way shows something (tests/visibility_suite.gd).
static func entrance(p: Dictionary, room_def: Dictionary) -> String:
	var type := str(p.get("type", "edge"))
	if not str(p.get("art", "")) in ["", "none"]: return "art"
	if _wall_door(p, room_def): return "wall"
	if type in ["door", "gate"]:
		var at: Array = p.get("at", [0, 0])
		for d in room_def.get("decor", []):
			var da: Array = d.get("at", [0, 0])
			if str(d.get("prop", "")) in WAY_DECOR and absf(float(da[0]) - float(at[0])) <= 24.0 and absf(float(da[1]) - float(at[1])) <= 40.0: return "decor"
		var door: Array = building_front(p, room_def).get("door", [])
		if door.size() == 2 and float(at[0]) >= float(door[0]) and float(at[0]) <= float(door[1]): return "building"
	return "door" if type == "door" else "art"

## The prop a way draws where it stands: its own `art`, else its type's (TYPE_ART) when nothing else shows it
## (`shows`, entrance). A closed way shows the sealed gate; an interior's own door on its back wall stays itself, shut
## (a quest holds it until a step is done, Morning Tide's Bag), its plate saying what to do first. "" draws none.
static func art_for(p: Dictionary, open: bool, shown_by: String) -> String:
	var type := str(p.get("type", "edge"))
	var art := str(p.get("art", ""))
	if art != "": return "" if art == "none" else art
	if type != "edge" and not open and shown_by != "wall": return "sealed_gate"
	return str(TYPE_ART.get(type, "")) if shown_by in ["art", "door"] else ""

## The way refused the player: light its plate (it shows even from a step away while lit).
func touch() -> void:
	touched = TOUCH_S

func _process(delta: float) -> void:
	t += delta
	touched = maxf(0.0, touched - delta)
	var c = Game.active()
	if c:
		state = WorldShared.portal_state(c, def)
		near = Game.world.portal_near(c, def)
	visible = not state.get("hidden", false)
	queue_redraw()
	tag.queue_redraw()

func _draw() -> void:
	if label_only: return
	var type := str(def.get("type", "edge"))
	var art := art_for(def, state.open, shows)
	var bob := 0.5 + 0.5 * sin(t * 4.0)
	if art == "door":
		SpriteCache.draw_prop(self, art, "open" if near and state.open else "closed", t, Vector2.ZERO)
	elif art != "":
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
	arrow_box = Rect2()
	if type == "door":
		_draw_arrow(Vector2(0, door_top - 8 + bob * 5), bob)
		arrow_box = Rect2(-17, door_top - 20, 34, 26)   # the chevron's whole bob
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
	var lit: bool = touched > 0.0 and not state.open
	if label == "" or (not state.open and not near and not lit): return
	var y := (door_top - 30.0) if type == "door" else -150.0
	var col := UiKit.PALE_GOLD if state.open else UiKit.MIST
	if not near: col = Color(col, 0.82)
	var size := 19 if near else 17
	if lit:
		# The refusal itself: the plate brightens and steps up a size, easing back as it fades.
		col = UiKit.PAPER.lerp(UiKit.PALE_GOLD, 0.5 + 0.5 * sin(t * 8.0)) if touched > TOUCH_S - 0.5 else UiKit.PAPER
		size = 20
	var shown := ("▲ " if state.open and near else "") + label
	# The whole plate inside the room: a way at its edge with a long line (the prototype's gate) ran off the screen.
	var dx := label_dx
	if label_span.x > -INF:
		var half := UiKit.text_width(shown, size, true) * 0.5 + 12.0
		if half * 2.0 < label_span.y - label_span.x: dx = clampf(position.x + label_dx, label_span.x + half, label_span.y - half) - position.x
	tag.draw_set_transform(Vector2(dx + label_offset.x, 0))   # label_offset.x: a crowd's plate half a box aside
	var plate := UiKit.draw_nameplate(tag, shown, "", y + label_offset.y, col, UiKit.MIST, size)
	label_box = Rect2(plate.position + Vector2(dx, -label_offset.y), plate.size)
	tag.draw_set_transform(Vector2.ZERO)
