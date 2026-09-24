class_name PortalView
extends Node2D
## Portal art and label (S17): edge gates are jade swirls between lantern posts,
## doors are building or interior doors, sealed gates show their lock rune and
## condition, "Coming soon" for planned rooms. Destination name shows when near.

var def: Dictionary = {}
var t := 0.0
var near := false
var state: Dictionary = {"open": true, "text": ""}

func setup(p: Dictionary) -> void:
	def = p
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = p.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]))
	z_index = 1500 + int(float(at[1])) - 30

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
	if art != "none" and art != "":
		SpriteCache.draw_prop(self, art, "idle", t, Vector2.ZERO, false, Color(0.6, 0.6, 0.65) if not state.open and art == "portal_swirl" else Color.WHITE)
	elif type == "door":
		# An arrow above a building door; the facade art already shows the door.
		var a := 0.5 + 0.5 * sin(t * 4.0)
		draw_colored_polygon(PackedVector2Array([Vector2(-9, -96 + a * 4), Vector2(9, -96 + a * 4), Vector2(0, -84 + a * 4)]), Color(UiKit.PALE_GOLD, 0.6 + 0.4 * a))
	if near:
		var label := str(state.text)
		if state.open: label = "▲ " + label
		UiKit.draw_outlined(self, label, Vector2(-150, -150), 16, UiKit.PALE_GOLD if state.open else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 300)
