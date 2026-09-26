class_name PortalView
extends Node2D
## Portal art and label (S17): edge gates are jade swirls between lantern posts,
## doors are building or interior doors, sealed gates show their lock rune and
## condition, "Coming soon" for planned rooms. An open way always names where it
## leads on a plate with a bobbing arrow, brighter when the player stands at it; a
## sealed way shows its condition when near.

var def: Dictionary = {}
var t := 0.0
var near := false
var state: Dictionary = {"open": true, "text": ""}
var wall_y := INF      # an interior door stands on the back wall's foot, this far above `at`
var door_top := -96.0  # where the arrow and plate sit
var label_dx := 0.0    # a way at the room's edge names itself a little inside, not half off-screen

func setup(p: Dictionary, room_def: Dictionary = {}) -> void:
	def = p
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = p.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]))
	z_index = 1500 + int(float(at[1])) - 30
	var wall: Dictionary = room_def.get("wall", {})
	if str(p.get("type", "")) == "door" and str(p.get("art", "")) == "" and not p.get("facade", false) and not wall.is_empty():
		wall_y = minf(0.0, float(wall.get("bottom", at[1])) - float(at[1]))
	door_top = (wall_y - 128.0) if wall_y != INF else -96.0
	var b: Array = room_def.get("bounds", [])
	if b.size() >= 3:
		label_dx = clampf(position.x, float(b[0]) + 150.0, float(b[0]) + float(b[2]) - 150.0) - position.x

func _process(delta: float) -> void:
	t += delta
	var c = Game.active()
	if c:
		state = Game.world.portal_state(c, def)
		near = Game.world.portal_near(c, def)
	visible = not state.get("hidden", false)
	queue_redraw()

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
	if type == "door":
		_draw_arrow(Vector2(0, door_top - 8 + bob * 5), bob)
	_draw_label(type)

## A chevron over the way in, pulsing so the eye finds it against busy walls.
func _draw_arrow(p: Vector2, bob: float) -> void:
	var col := Color(UiKit.PALE_GOLD, 0.75 + 0.25 * bob) if state.open else Color(UiKit.MIST, 0.6)
	var pts := PackedVector2Array([p + Vector2(-14, -10), p + Vector2(14, -10), p + Vector2(0, 6)])
	draw_colored_polygon(PackedVector2Array([p + Vector2(-17, -12), p + Vector2(17, -12), p + Vector2(0, 9)]), Color(UiKit.INK, 0.85))
	draw_colored_polygon(pts, col)

func _draw_label(type: String) -> void:
	var label := str(state.text)
	if label == "" or (not state.open and not near): return
	var y := (door_top - 30.0) if type == "door" else -150.0
	var col := UiKit.PALE_GOLD if state.open else UiKit.MIST
	if not near: col = Color(col, 0.82)
	var size := 19 if near else 17
	draw_set_transform(Vector2(label_dx, 0))
	UiKit.draw_nameplate(self, ("▲ " if state.open and near else "") + label, "", y, col, UiKit.MIST, size)
	draw_set_transform(Vector2.ZERO)
