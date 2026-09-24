extends Page
## Dialogue box (Part 9.10): portrait, speaker plaque, typewriter lines (tap to
## finish or advance), then choices. Choices go back through `choose_dialogue`;
## shops, pages and spars navigate. The world keeps running behind it.

const Avatar = preload("res://scripts/avatar.gd")

var convo: Dictionary = {}
var line := 0
var shown_chars := 0.0
var portrait: Node2D

func _init() -> void:
	modal = true
	frame_rect = Rect2(40, 470, 1200, 232)

func setup() -> void:
	convo = args.get("convo", {})
	line = 0
	shown_chars = 0.0
	if is_instance_valid(portrait): portrait.queue_free()
	portrait = null
	var outfit: Dictionary = convo.get("portrait", {})
	if not outfit.is_empty():
		portrait = Avatar.new()
		var o := outfit.duplicate()
		for k in ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]:
			if not o.has(k): o[k] = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}.get(k, "none")
		if not o.has("hair_color"): o.hair_color = 0
		portrait.outfit = o
		portrait.position = Vector2(142, 690)
		portrait.scale = Vector2.ONE * 1.35
		portrait.facing = 1
		add_child(portrait)
		portrait.play("idle")

func lines() -> Array:
	return convo.get("lines", [])

func current() -> String:
	var ls := lines()
	return str(ls[line]) if line < ls.size() else ""

func at_end() -> bool:
	return line >= lines().size() - 1

func _process(delta: float) -> void:
	super._process(delta)
	shown_chars += delta * 60.0

func _draw() -> void:
	_regions.clear()
	_areas.clear()
	draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.18))
	draw_page()
	_draw_toast()

func draw_page() -> void:
	var box := Rect2(40, 500, 1200, 204)
	draw_style_box(UiKit.style("dialogue_box"), box)
	var pf := Rect2(56, 470, 176, 220)
	draw_style_box(UiKit.style("portrait_frame"), pf)
	var plaque := Rect2(250, 470, maxf(220, UiKit.text_width(str(convo.get("speaker", "")), 26, true) + 60), 48)
	draw_style_box(UiKit.style("title_plaque"), plaque)
	text(plaque.position + Vector2(0, 34), str(convo.get("speaker", "")), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plaque.size.x, true)
	var s := current()
	var visible := s.left(int(shown_chars))
	var choices: Array = convo.get("choices", [])
	var text_w := 560.0 if at_end() and not choices.is_empty() else 900.0
	para(Rect2(262, 532, text_w, 150), visible, 22, UiKit.PAPER)
	region(Rect2(40, 470, 1200, 234), "advance")
	if at_end() and shown_chars >= s.length():
		if choices.is_empty():
			text(Vector2(1160, 690), "▼", 18, UiKit.GOLD)
		else:
			var y := 520.0
			var h := minf(52.0, 170.0 / maxf(1.0, choices.size()))
			for i in choices.size():
				var ch: Dictionary = choices[i]
				var primary := ch.has("accept") or ch.has("hand_in")
				btn(Rect2(846, y, 370, h - 6), str(ch.get("text", "...")), "choose", i, primary, true, "", 19 if h < 46 else 21)
				y += h
	elif shown_chars < s.length():
		pass
	else:
		text(Vector2(1160, 690 + sin(t * 5.0) * 3), "▼", 18, UiKit.GOLD)

func on_action(id: String, data) -> void:
	match id:
		"advance":
			if shown_chars < current().length():
				shown_chars = 9999.0
			elif not at_end():
				line += 1
				shown_chars = 0.0
			elif (convo.get("choices", []) as Array).is_empty():
				close()
		"choose": _choose(int(data))

func _choose(i: int) -> void:
	var choices: Array = convo.get("choices", [])
	if i < 0 or i >= choices.size(): return
	var ch: Dictionary = choices[i]
	var npc := str(convo.get("npc", ""))
	if ch.has("shop"):
		navigate.emit("shop", {"shop": str(ch.shop), "npc": npc})
		close()
		return
	if ch.has("page"):
		navigate.emit(str(ch.page), {"npc": npc})
		close()
		return
	var needs_authority := ch.has("accept") or ch.has("hand_in") or ch.has("effects") or ch.has("next") or ch.has("spar")
	if needs_authority:
		var r := submit({"type": "choose_dialogue", "npc": npc, "choice": ch})
		if r.get("ok", false) and r.has("dialogue"):
			args = {"convo": r.dialogue}
			setup()
			return
		if r.get("ok", false) and (ch.has("accept") or ch.has("hand_in")):
			Audio.ui("quest_accept" if ch.has("accept") else "quest_complete")
			# Talk again: a giver often has a follow-up line or the next offer.
			var again := Game.submit({"type": "talk", "npc": npc})
			if again.get("ok", false) and again.has("dialogue"):
				var d: Dictionary = again.dialogue
				var only_farewell: bool = (d.get("choices", []) as Array).size() <= 1 and not d.has("quest")
				if not only_farewell:
					args = {"convo": d}
					setup()
					return
	close()

func _unhandled_key_input(event: InputEvent) -> void:
	if event.pressed and not event.echo:
		if event.keycode in [KEY_SPACE, KEY_ENTER, KEY_J, KEY_F]:
			on_action("advance", null)
			get_viewport().set_input_as_handled()
		elif event.keycode >= KEY_1 and event.keycode <= KEY_4 and at_end():
			_choose(event.keycode - KEY_1)
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_ESCAPE:
			close()
			get_viewport().set_input_as_handled()
