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
var pose_now := ""
## P5a (G4): the nameplate's box under the feet at no offset, and the offset in whole rows the layout pass gives it.
var label_box := Rect2()
var label_offset := Vector2.ZERO
var label_flip := Vector2.ZERO
var tag: Node2D   # the nameplate's own canvas item, above every figure (WorldLabels.LABEL_Z)
## The top-down view (redesign Phase 4) draws the figure in its pixel viewport (NpcView.figure) and this view only for
## the marker, the bark and the nameplate, on its overlay at the HUD's resolution.
var label_only := false

func setup(o: Dictionary, geo: ZoneGeometry = null) -> void:
	def = o
	object_id = str(o.id)
	npc_id = str(o.npc)
	var n := ContentDB.entry("npcs", npc_id)
	display_name = str(n.get("name", npc_id))
	title = str(n.get("title", ""))
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = o.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]) - float(o.get("alt", 0)))
	z_index = ObjectView.depth(o, geo)
	avatar = figure(o)
	add_child(avatar)
	if label_only:
		avatar.visible = false
		avatar.set_process(false)
	tag = WorldLabels.make_tag(self, _draw_tag)
	pose_now = avatar.action
	bark_timer = randf_range(4.0, 12.0)

## The villager's figure: the layered avatar in their outfit, pose, facing and tint (npcs.json), for either view.
static func figure(o: Dictionary) -> Node2D:
	var n := ContentDB.entry("npcs", str(o.npc))
	var av = Avatar.new()
	av.lazy_sheets = true   # a room full of new outfits draws each villager once its sheets are in, not on entry
	var outfit: Dictionary = n.get("outfit", {}).duplicate()
	for k in ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]:
		if not outfit.has(k): outfit[k] = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}.get(k, "none")
	if not outfit.has("hair_color"): outfit.hair_color = 0
	av.outfit = outfit
	av.facing = int(o.get("facing", n.get("facing", -1)))
	av.play(str(o.get("pose", n.get("pose", "idle"))))
	if n.has("tint"): av.modulate = Color(str(n.tint))
	av.refresh_entries()   # its sheets are asked for as the room is populated, not at its first draw
	return av

func _process(delta: float) -> void:
	t += delta
	var c = Game.active()
	visible = c == null or Game.world.object_visible(c, def)
	if not visible: return
	if def.has("chase"): _follow_chase(c)
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
	tag.queue_redraw()

## S43 rule 15: a rooftop thief on the run is wherever his route puts him (the authority's clock), running, leaping
## between tiers, or waiting to jeer.
func _follow_chase(c) -> void:
	var p: Dictionary = Game.world.chase_view(c) if c != null else {}
	var at: Array = def.get("at", [0, 0])
	var pose := "idle"
	if p.is_empty() or str(p.get("object", "")) != object_id:
		position = Vector2(float(at[0]), float(at[1]))
	else:
		position = Vector2(float(p.x), float(p.y) - float(p.alt))
		z_index = 1500 + int(float(p.y)) + int(float(p.alt))
		avatar.facing = int(p.facing)
		if p.moving: pose = "walk"
	if pose != pose_now:
		pose_now = pose
		avatar.play(pose)

func face(x: float) -> void:
	avatar.facing = 1 if x >= position.x else -1

## The nameplate under the feet, drawn on `tag` above every figure (P5a, G4). With no free row below it (a HUD control,
## another plate) the layout pass may lift it over the head instead: `label_flip` is that offset, clear of the marker.
func _draw_tag() -> void:
	var col := UiKit.PALE_GOLD if focus else UiKit.PAPER
	var plate := UiKit.draw_nameplate(tag, display_name, title, 26 + label_offset.y, col, UiKit.MIST, 17)
	label_box = Rect2(plate.position - label_offset, plate.size)
	label_flip = Vector2(0, -136.0 - label_box.end.y)

func _draw() -> void:
	if not label_only:
		draw_set_transform(Vector2(0, 0), 0.0, Vector2(1, 0.28))
		draw_circle(Vector2.ZERO, 16, Color(0.01, 0.035, 0.04, 0.35))
		draw_set_transform(Vector2.ZERO)
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
		"again":
			# A new quest from someone you have helped before: the gold diamond inside a jade ring.
			draw_circle(Vector2(0, top - 4), 17, UiKit.INK)
			draw_arc(Vector2(0, top - 4), 14.5, 0, TAU, 28, UiKit.BRIGHT_JADE, 3.0)
			draw_colored_polygon(PackedVector2Array([Vector2(0, top - 16), Vector2(10, top - 4), Vector2(0, top + 8), Vector2(-10, top - 4)]), UiKit.GOLD)
			UiKit.draw_text(self, "!", Vector2(-3, top + 3), 16, UiKit.INK, HORIZONTAL_ALIGNMENT_LEFT, -1, false)
		"progress":
			# A quest of theirs under way: three dots in a grey speech bubble.
			var bub := Rect2(-18, top - 16, 36, 22)
			draw_colored_polygon(PackedVector2Array([Vector2(-5, bub.end.y - 1), Vector2(3, bub.end.y - 1), Vector2(-7, bub.end.y + 7)]), Color("8d969a"))
			draw_rect(bub.grow(1.5), UiKit.INK)
			draw_rect(bub, Color("b7c0c3"))
			for k in 3: draw_circle(Vector2(-8 + k * 8, top - 5), 2.6, UiKit.INK)
		"ready":
			UiKit.draw_outlined(self, "?", Vector2(-20, top + 8), 30, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, 40)
		"talk":
			UiKit.draw_outlined(self, "…", Vector2(-20, top + 4), 24, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 40)
	if bark_time > 0.0 and bark != "":
		var w := minf(300.0, UiKit.text_width(bark, 17) + 22)
		var r := Rect2(-w * 0.5, -154, w, 30)
		draw_rect(r, Color(0.9, 0.87, 0.78, minf(1.0, bark_time)))
		draw_rect(r, Color(UiKit.INK, minf(1.0, bark_time)), false, 2)
		UiKit.draw_text(self, bark, Vector2(r.position.x + 11, r.position.y + 21), 17, Color(UiKit.INK, minf(1.0, bark_time)), HORIZONTAL_ALIGNMENT_LEFT, w - 22, false)
