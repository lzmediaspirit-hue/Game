extends Page
## Dialogue box (Part 9.10): portrait, speaker plaque, typewriter lines (tap to
## finish or advance), then choices. Choices go back through `choose_dialogue`;
## shops, pages and spars navigate. The world keeps running behind it.
## P5 (docs/page_identity.md row 2, mockup 21): rice paper laid under the scene, a storyteller's caption. Frameless: one
## paper strip along the foot, the speaker's portrait framed at its left, their name on a jade plaque with their hearts
## and who they are, the words in ink, and the choices stacked at its right, numbered for the keys. A quest offered (or
## ready to hand in) is pinned above the choices as a small scroll, what it asks and what it gives read before choosing;
## it unrolls downward (0.2 s). A talk ends by its own choices, a tap on its last line or Esc: it has no close button.

const Avatar = preload("res://scripts/avatar.gd")

var convo: Dictionary = {}
var line := 0
var shown_chars := 0.0
var portrait: Node2D
var card_at := INF                         # when the offered quest's card began to unroll (INF: not yet)

const CARD := Rect2(880, 264, 336, 212)    # the offered quest, pinned above the choices
const OFFER_S := 0.2

func _init() -> void:
	modal = true
	frame_rect = WINDOW_DIALOGUE
	identity = Identity.new("scroll", false, "own", "paper_strip_under_scene", OFFER_S)

## The strip, and the card above it while a quest is offered.
func window_rect() -> Rect2:
	return frame_rect.merge(CARD) if not _card_quest().is_empty() else frame_rect

func setup() -> void:
	convo = args.get("convo", {})
	line = 0
	shown_chars = 0.0
	card_at = INF
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
	HdStyleBox.base = Transform2D.IDENTITY
	if text_log != null: text_log.clear()
	draw_rect(Rect2(Vector2.ZERO, size), Color(UiKit.INK, 0.18))
	draw_page()
	_draw_toast()

func draw_page() -> void:
	var fr := frame_rect
	var box := Rect2(fr.position.x, fr.position.y + 32, fr.size.x, fr.size.y - 32)
	face(box, "dialogue_box")
	var pf := Rect2(fr.position.x + 16, fr.position.y, 176, 216)
	draw_style_box(UiKit.style("portrait_frame"), pf)
	# The plaque's ribbon ends take ~44 px a side: leave the name room inside the enamel.
	var speaker := str(convo.get("speaker", ""))
	var plaque := Rect2(fr.position.x + 208, fr.position.y, maxf(240, UiKit.text_width(speaker, 26, true) + 130), 48)
	draw_style_box(UiKit.style("title_plaque"), plaque)
	inked(plaque.position + Vector2(0, 34), speaker, 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plaque.size.x)
	# S49: how this person feels about you, as hearts under their name, and who they are.
	var who := str(ContentDB.entry("npcs", str(convo.get("npc", ""))).get("title", ""))
	var hx := fr.position.x + 220
	if convo.has("hearts"):
		UiKit.draw_hearts(self, Vector2(hx + 4, fr.position.y + 72), int(convo.hearts), 5, 9.0)
		hx += 110
		who = (who + " · " if who != "" else "") + Tx.plural("ui.dialogue.hearts", int(convo.hearts)) % int(convo.hearts)
	if who != "": text(Vector2(hx, fr.position.y + 78), who, 16, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, 560)
	var s := current()
	var visible := s.left(int(shown_chars))
	var choices: Array = convo.get("choices", [])
	var text_w := 580.0 if at_end() and not choices.is_empty() else 900.0
	para(Rect2(fr.position.x + 220, fr.position.y + 90, text_w, 132), visible, 20, RecordsKit.INK, 4)
	region(fr, "advance")
	if at_end() and shown_chars >= s.length():
		if choices.is_empty():
			text(Vector2(fr.end.x - 72, fr.end.y - 12), "▼", 16, RecordsKit.BROWN)
		else:
			# Every choice a full 48 px high (I7), numbered for the keys; past four they rise above the strip.
			var h := 52.0
			var y := minf(fr.position.y + 32, fr.end.y + 4 - h * choices.size())
			for i in choices.size():
				var ch: Dictionary = choices[i]
				var primary := ch.has("accept") or ch.has("hand_in")
				var r := Rect2(fr.end.x - 360, y, 352, h - 4)
				btn(r, str(ch.get("text", "...")), "choose", i, primary, true, "", 20)
				if i < 4: _key(r.position + Vector2(24, r.size.y * 0.5), i + 1)
				y += h
			_offer_card()
	elif shown_chars >= s.length():
		text(Vector2(fr.end.x - 72, fr.end.y - 12 + (0.0 if UiKit.reduce_motion() else sin(t * 5.0) * 3)), "▼", 16, RecordsKit.BROWN)

## A choice's key (1 to 4), a pale gold disc with its number in ink.
func _key(c: Vector2, n: int) -> void:
	draw_circle(c, 14.0, UiKit.INK, true, -1.0, true)
	draw_circle(c, 12.0, UiKit.PALE_GOLD, true, -1.0, true)
	ground(Rect2(c - Vector2(12, 12), Vector2(24, 24)), UiKit.PALE_GOLD)
	text(Vector2(c.x - 12, c.y + 5), str(n), 14, UiKit.INK, HORIZONTAL_ALIGNMENT_CENTER, 24)

## The quest this talk offers or takes back (convo.quest) once its choices show, while it is on offer or ready.
func _card_quest() -> Dictionary:
	var q := str(convo.get("quest", ""))
	var ch = c()
	if q == "" or ch == null or not (at_end() and shown_chars >= current().length()): return {}
	var d := Game.quest.quest_def(ch, q)
	if d.is_empty() or ch.quests.is_done(q): return {}
	return d

## The offered quest as a small scroll above the choices: its kind, its name, its first steps and what it gives. It
## unrolls downward over OFFER_S (a fade under Reduce motion, with the page's).
func _offer_card() -> void:
	var d := _card_quest()
	if d.is_empty(): return
	var ch = c()
	var q := str(d.id)
	var ready: bool = ch.quests.is_active(q) and str(ch.quests.active[q].get("state", "")) == "ready"
	if card_at == INF: card_at = t
	var k := 1.0 if UiKit.reduce_motion() else clampf((t - card_at) / OFFER_S, 0.0, 1.0)
	move(CARD.position, 0.0, Vector2(1.0, lerpf(0.12, 1.0, k)))
	var r := Rect2(Vector2.ZERO, CARD.size)
	rounded(Rect2(r.position + Vector2(4, 6), r.size), 4.0, Color(UiKit.INK, 0.4))
	draw_style_box(UiKit.style("paper_slip"), r)
	for yy in [-4.0, r.size.y - 8.0]:   # the scroll's rods
		rounded(Rect2(-6, yy, r.size.x + 12, 12), 5.0, UiKit.SURFACE.wood)
	move()
	if k < 1.0: return
	ground(CARD, UiKit.SURFACE.scroll)
	var x := CARD.position.x + 18
	var w := CARD.size.x - 36
	var kind := str(d.get("kind", "side"))
	var kind_word := Tx.t("ui.dialogue.kind_" + (kind if kind in ["main", "prologue", "guided"] else "side"))
	text(Vector2(x, CARD.position.y + 30), (Tx.t("ui.dialogue.ready") if ready else Tx.t("ui.dialogue.offered")) % kind_word, 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, w)
	text(Vector2(x, CARD.position.y + 62), str(d.get("name", q)), 26, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, w, true)
	var y := CARD.position.y + 74
	for o in (d.get("objectives", []) as Array).slice(0, 2):
		if y > CARD.end.y - 72: break
		draw_rect(Rect2(x, y + 4, 14, 14), RecordsKit.BROWN, false, 2.0)
		y += para(Rect2(x + 24, y, w - 24, 40), str(o.get("text", o.get("kind", ""))), 14, RecordsKit.INK, 2) + 2
	for rw in d.get("rewards", []):
		if y > CARD.end.y - 46: break
		var words := ""
		var icon := ""
		match str(rw.get("kind", "")):
			"grant_currency":
				words = "%s %s" % [UiKit.fmt(int(rw.amount)), currency_name(str(rw.currency))]
				icon = currency_icon(str(rw.currency))
			"grant_item":
				words = "%d %s" % [int(rw.get("count", 1)), ContentDB.item_name(str(rw.item))]
				icon = str(rw.item)
		if words == "": continue
		icon_at(Rect2(x - 4, y + 2, 32, 32), icon)
		text(Vector2(x + 34, y + 24), words, 16, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, w - 34)
		y += 34

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
		if not r.get("ok", false) and ch.has("hand_in"): return   # a refused hand-in stays open with what is missing flashed
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
