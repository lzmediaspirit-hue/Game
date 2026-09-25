class_name NpcView
extends Node2D
## A villager, vendor, mentor or recruiter drawn with the layered avatar (the
## same engine that builds the player) plus a name tag, quest marker and barks.

const Avatar = preload("res://scripts/avatar.gd")

var object_id := ""
var npc_id := ""
var avatar: Node2D
var marker := ""
var bark := ""
var bark_time := 0.0
var bark_timer := 0.0
var display_name := ""
var title := ""
var focus := false
var t := 0.0
var def: Dictionary = {}

func setup(o: Dictionary) -> void:
	def = o
	object_id = str(o.id)
	npc_id = str(o.npc)
	var n := ContentDB.entry("npcs", npc_id)
	display_name = str(n.get("name", npc_id))
	title = str(n.get("title", ""))
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = o.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]) - float(o.get("alt", 0)))
	z_index = 1500 + int(float(at[1]))
	avatar = Avatar.new()
	var outfit: Dictionary = n.get("outfit", {}).duplicate()
	for k in ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]:
		if not outfit.has(k): outfit[k] = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}.get(k, "none")
	if not outfit.has("hair_color"): outfit.hair_color = 0
	avatar.outfit = outfit
	avatar.facing = int(o.get("facing", n.get("facing", -1)))
	add_child(avatar)
	var pose := str(o.get("pose", n.get("pose", "idle")))
	avatar.play(pose)
	if n.has("tint"): avatar.modulate = Color(str(n.tint))
	bark_timer = randf_range(4.0, 12.0)

func _process(delta: float) -> void:
	t += delta
	var c = Game.active()
	visible = c == null or Game.world.object_visible(c, def)
	if not visible: return
	marker = Game.quest.npc_marker(c, npc_id) if c else ""
	bark_timer -= delta
	if bark_timer <= 0.0:
		bark_timer = randf_range(10.0, 22.0)
		var barks: Array = ContentDB.entry("npcs", npc_id).get("barks", [])
		if not barks.is_empty() and marker == "":
			bark = str(barks[randi() % barks.size()])
			bark_time = 4.0
	bark_time = maxf(0.0, bark_time - delta)
	queue_redraw()

func face(x: float) -> void:
	avatar.facing = 1 if x >= position.x else -1

func _draw() -> void:
	draw_set_transform(Vector2(0, 0), 0.0, Vector2(1, 0.28))
	draw_circle(Vector2.ZERO, 16, Color(0.01, 0.035, 0.04, 0.35))
	draw_set_transform(Vector2.ZERO)
	var col := UiKit.PALE_GOLD if focus else UiKit.PAPER
	UiKit.draw_nameplate(self, display_name, title, 24, col, UiKit.MIST, 15)
	var top := -112.0 + sin(t * 3.0) * 3.0
	match marker:
		"main":
			draw_colored_polygon(PackedVector2Array([Vector2(0, top - 18), Vector2(11, top - 4), Vector2(0, top + 10), Vector2(-11, top - 4)]), UiKit.INK)
			draw_colored_polygon(PackedVector2Array([Vector2(0, top - 15), Vector2(8, top - 4), Vector2(0, top + 7), Vector2(-8, top - 4)]), UiKit.GOLD)
			UiKit.draw_text(self, "!", Vector2(-3, top + 3), 16, UiKit.INK, HORIZONTAL_ALIGNMENT_LEFT, -1, false)
		"side":
			draw_circle(Vector2(0, top - 4), 11, UiKit.INK)
			draw_circle(Vector2(0, top - 4), 9, Color("5aa7e8"))
			UiKit.draw_text(self, "!", Vector2(-3, top + 3), 16, UiKit.INK, HORIZONTAL_ALIGNMENT_LEFT, -1, false)
		"ready":
			UiKit.draw_outlined(self, "?", Vector2(-20, top + 8), 30, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, 40)
		"talk":
			UiKit.draw_outlined(self, "…", Vector2(-20, top + 4), 24, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 40)
	if bark_time > 0.0 and bark != "":
		var w := minf(260.0, UiKit.text_width(bark, 16) + 20)
		var r := Rect2(-w * 0.5, -150, w, 26)
		draw_rect(r, Color(0.9, 0.87, 0.78, minf(1.0, bark_time)))
		draw_rect(r, Color(UiKit.INK, minf(1.0, bark_time)), false, 2)
		UiKit.draw_text(self, bark, Vector2(r.position.x + 10, r.position.y + 19), 16, Color(UiKit.INK, minf(1.0, bark_time)), HORIZONTAL_ALIGNMENT_LEFT, w - 20, false)
