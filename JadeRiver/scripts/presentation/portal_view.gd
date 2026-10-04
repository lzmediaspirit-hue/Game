class_name PortalView
extends Node2D
## A way's plate (S17): an open way names where it leads on a plate with a bobbing arrow over a door, brighter when
## the player stands at it; a shut way shows its condition when near, "Coming soon" for a planned room. The top-down view
## (redesign Phase 4) draws the way itself in its pixel viewport (a building's doorway, the gap in an interior's wall,
## the marks of an edge: TopdownPlaces.WayMark); this view draws the arrow and the plate on its overlay, on their own
## canvas item above every figure and building (WorldLabels.LABEL_Z), so a door in a building's front is never hidden by
## the facade it stands in.

var def: Dictionary = {}
var t := 0.0
var near := false
var state: Dictionary = {"open": true, "text": ""}
var door_top := -96.0  # where the arrow and plate sit (TopdownPlaces sets a door's over its building's front)
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

func setup(p: Dictionary, room_def: Dictionary = {}) -> void:
	def = p
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = p.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]))
	z_index = 1500 + int(float(at[1])) - 30
	var b: Array = room_def.get("bounds", [])
	if b.size() >= 3:
		label_span = Vector2(float(b[0]), float(b[0]) + float(b[2]))
		label_dx = clampf(position.x, label_span.x + 150.0, label_span.y - 150.0) - position.x
	tag = WorldLabels.make_tag(self, _draw_tag)

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
	tag.queue_redraw()

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
