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
	frame_rect = WINDOW_DIALOGUE

func setup() -> void:
	convo = args.get("convo", {})
	line = 0
	shown_chars = 0.0
	if is_instance_valid(portrait): portrait.queue_free()
	portrait = null
	var outfit: Dictionary = convo.get("portrait", {})
	if not outfit.is_empty():
		portrait = Avatar.new()
		portrait.outfit = full_outfit(outfit)
		portrait.position = Vector2(frame_rect.position.x + 104, frame_rect.end.y - 12)
		portrait.scale = Vector2.ONE * 1.35
		portrait.facing = 1
		add_child(portrait)
		portrait.play("idle")

## An NPC's outfit (npcs.json) with every layer the figure needs: what it leaves out is the villager's default.
static func full_outfit(outfit: Dictionary) -> Dictionary:
	var o := outfit.duplicate()
	for k in ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]:
		if not o.has(k): o[k] = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}.get(k, "none")
	if not o.has("hair_color"): o.hair_color = 0
	return o

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
	draw_rect(Rect2(Vector2.ZERO, size), Color(UiKit.INK, 0.18))
	draw_page()
	_draw_toast()

func draw_page() -> void:
	var fr := frame_rect
	var box := Rect2(fr.position.x, fr.position.y + 32, fr.size.x, fr.size.y - 32)
	draw_style_box(UiKit.style("dialogue_box"), box)
	var pf := Rect2(fr.position.x + 16, fr.position.y, 176, 216)
	draw_style_box(UiKit.style("portrait_frame"), pf)
	# The plaque's ribbon ends take ~44 px a side: leave the name room inside the enamel.
	var plaque := Rect2(fr.position.x + 208, fr.position.y, maxf(240, UiKit.text_width(str(convo.get("speaker", "")), 26, true) + 130), 48)
	draw_style_box(UiKit.style("title_plaque"), plaque)
	inked(plaque.position + Vector2(0, 34), str(convo.get("speaker", "")), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plaque.size.x)
	# S49: how this person feels about you, as hearts beside their name.
	if convo.has("hearts"): UiKit.draw_hearts(self, Vector2(plaque.end.x + 12, plaque.position.y + 26), int(convo.hearts), 5, 10.0)
	var s := current()
	var visible := s.left(int(shown_chars))
	var choices: Array = convo.get("choices", [])
	var text_w := 560.0 if at_end() and not choices.is_empty() else 900.0
	_ink_para(Rect2(fr.position.x + 216, fr.position.y + 64, text_w, 144), visible, 22)
	region(fr, "advance")
	if at_end() and shown_chars >= s.length():
		if choices.is_empty():
			text(Vector2(fr.end.x - 72, fr.end.y - 8), "▼", 18, UiKit.GOLD)
		else:
			# Every choice a full 48 px high (I7): four of them rise above the box's top rather than shrink.
			var h := 52.0
			var y := minf(fr.position.y + 48, fr.end.y - 8 - h * choices.size())
			for i in choices.size():
				var ch: Dictionary = choices[i]
				var primary := ch.has("accept") or ch.has("hand_in")
				btn(Rect2(fr.end.x - 384, y, 368, h - 4), str(ch.get("text", "...")), "choose", i, primary, true, "", 20)
				y += h
	elif shown_chars < s.length():
		pass
	else:
		text(Vector2(fr.end.x - 72, fr.end.y - 8 + sin(t * 5.0) * 3), "▼", 18, UiKit.GOLD)

## Dialogue lines are ink on the paper box: dark, no drop shadow.
func _ink_para(rect: Rect2, s: String, size: int) -> void:
	var y := rect.position.y + size * UiKit.text_scale()
	for ln in _wrap(s, size, rect.size.x):
		if y > rect.end.y + 2: break
		UiKit.draw_text(self, ln, Vector2(rect.position.x, y), size, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, -1.0, false)
		y += UiKit.line_height(size) * 1.04

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
		navigate.emit(str(ch.page), ch.get("args", {"npc": npc}))
		close()
		return
	# A choice that is itself an intent (S45: dig up a rare herb); its authority validates it.
	if ch.has("intent"):
		if submit(ch.intent).get("ok", false): close()   # a refusal stays open with its reason flashed
		return
	var needs_authority := ch.has("accept") or ch.has("hand_in") or ch.has("effects") or ch.has("next") or ch.has("spar")
	if needs_authority:
		var r := submit({"type": "choose_dialogue", "npc": npc, "choice": ch})
		if r.get("ok", false) and (ch.has("accept") or ch.has("hand_in")):
			Audio.ui("quest_accept" if ch.has("accept") else "quest_complete")
		# The conversation goes on only where the authority hands one back (the next node, or the same person's next
		# quest to take or hand in, QuestAuthority._then); taking a quest otherwise ends it (M17).
		if r.get("ok", false) and r.has("dialogue"):
			args = {"convo": r.dialogue}
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
