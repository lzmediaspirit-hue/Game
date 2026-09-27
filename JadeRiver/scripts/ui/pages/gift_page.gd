extends "res://scripts/ui/pages/dialogue_page.gd"
## A gift (S49): one a day for each person with favourite gifts. Pick something from the bag; what they love is
## worth a heart, what they like less, anything else a courtesy. What they told you they love or like is marked.
## P5 (docs/page_identity.md row 28, the Bonds family; mockup 21_dialogue_gift): a red-lacquered gift tray held out
## over the talk. The tray's compartments hold what the bag can give, what they are known to love or like first, each
## tagged; Give under them. The talk stays below it as the Dialogue's own paper strip (this page extends the Dialogue):
## their hearts, their answer to the gift, the heart bar with what the gift moved, and the talk's other choices beside
## it. A given gift lifts from the tray toward the speaker and the bar fills (0.3 s); under Reduce motion the gift is not
## flown and the bar is set.

const TRAY := Rect2(252, 268, 972, 188)
const CELL := 86.0        # a compartment: the 76 px slot and the fillet to the next
const PER_TRAY := 10
const LIFT_S := 0.3

var npc := ""
var sel := -1
var shelf := 0            # which ten of the giftable things lie in the tray
var answer := {}          # the last gift's answer: {reaction, item, delta, before, from, at}
var _placed := {}         # bag index -> where its compartment is, for the gift's flight

func _init() -> void:
	modal = true
	frame_rect = WINDOW_DIALOGUE
	identity = Identity.new("lacquer", false, "own", "gift_tray_over_talk", LIFT_S)

## The talk strip, and the tray held out above it.
func window_rect() -> Rect2:
	return frame_rect.merge(TRAY)

func setup() -> void:
	npc = str(args.get("npc", args.get("tab", "")))   # --open-page=gift:npc passes it as the tab
	sel = -1
	shelf = 0
	answer = {}
	# The talk the gift was offered from (the Dialogue hands it on) keeps its other choices; from the Companions page
	# there is only Farewell. Four at most, Farewell kept, so they stay on the strip.
	var talk: Dictionary = args.get("convo", {})
	if str(talk.get("npc", npc)) != npc: talk = {}
	var choices: Array = (talk.get("choices", []) as Array).filter(func(x): return str(x.get("page", "")) != "gift")
	if choices.size() > 4: choices = choices.slice(0, 3) + [choices[-1]]
	if choices.is_empty(): choices = [{"text": Tx.t("sim.quest.farewell"), "close": true}]
	var n := ContentDB.entry("npcs", npc)
	args["convo"] = {"npc": npc, "speaker": str(talk.get("speaker", ContentDB.name_of("npcs", npc))), "portrait": talk.get("portrait", n.get("outfit", {})),
		"choices": choices}
	title = Tx.t("ui.gift.for") % ContentDB.name_of("npcs", Game.relations.aff_id(npc)) if npc != "" else ""
	super.setup()

func draw_page() -> void:
	var ch = c()
	if ch == null or npc == "": return
	var id := Game.relations.aff_id(npc)
	var a: Dictionary = ch.relations.affinity.get(id, {})
	convo["hearts"] = ch.relations.hearts_of(id)
	# The tray is held out from behind the strip as the page opens.
	move(Vector2(0, 40.0 * (1.0 - unfold())))
	_tray(ch, a)
	move()
	_strip()
	_answer(ch, a)
	_choice_buttons(convo.get("choices", []))
	_lift()

## Bag indices of what can be given: what they are known to love, then to like, then the rest in bag order.
func _giftable(ch, known: Dictionary) -> Array:
	var out: Array = []
	for i in ch.inventory.bag.size():
		var s = ch.inventory.bag[i]
		if s != null and RelationsAuthority.giftable(s): out.append(i)
	var rank := func(i: int) -> int: return {"loved": 0, "liked": 1}.get(str(known.get(str(ch.inventory.bag[i].id), "")), 2)
	out.sort_custom(func(x, y): return rank.call(x) < rank.call(y) or (rank.call(x) == rank.call(y) and x < y))
	return out

## The lacquered tray: whose gift it is, what they are known to love and like, the compartments with the bag's giftable
## things (ten at a time, the rest behind "+n"), and Give with what it would do.
func _tray(ch, a: Dictionary) -> void:
	face(TRAY, "gift_tray")
	ground(TRAY.grow(-8), UiKit.SURFACE.lacquer)
	var x := TRAY.position.x + 18
	var tw := minf(UiKit.text_width(title, 26, true), 440.0)
	inked(Vector2(x, TRAY.position.y + 38), title, 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 440)
	text(Vector2(x + tw + 16, TRAY.position.y + 36), Tx.t("ui.gift.one_a_day"), 14, UiKit.MIST)
	var known: Dictionary = a.get("known", {})
	var kx := TRAY.position.x + 500
	for kind in ["loved", "liked"]:
		var names: Array = []
		for it in known:
			if str(known[it]) == kind: names.append(ContentDB.item_name(str(it)))
		var label := Tx.t("ui.gift.loves" if kind == "loved" else "ui.gift.likes")
		text(Vector2(kx, TRAY.position.y + 36), label, 16, UiKit.GOLD)
		var lw := UiKit.text_width(label, 16) + 8
		text(Vector2(kx + lw, TRAY.position.y + 36), ", ".join(names) if not names.is_empty() else Tx.t("ui.gift.not_known"), 16,
			UiKit.PALE_GOLD if not names.is_empty() else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 226 - lw)
		kx += 236
	var gifts := _giftable(ch, known)
	_placed.clear()
	if gifts.is_empty():
		para(Rect2(x, TRAY.position.y + 76, TRAY.size.x - 36, 48), Tx.t("ui.gift.nothing"), 18, UiKit.MIST, 2)
	else:
		var shelves := ceili(gifts.size() / float(PER_TRAY))
		shelf = shelf % shelves
		var shown := gifts.slice(shelf * PER_TRAY, shelf * PER_TRAY + PER_TRAY)
		for i in shown.size():
			var bi: int = shown[i]
			var s: Dictionary = ch.inventory.bag[bi]
			var r := Rect2(x + i * CELL, TRAY.position.y + 52, SLOT, SLOT)
			# The compartment: a well sunk in the lacquer, a gold fillet round it.
			rounded(r.grow(5), 6.0, UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.4))
			draw_rect(r.grow(5), Color(UiKit.GOLD, 0.35), false, 1.0)
			slot_box(r, str(s.id), int(s.get("count", 1)), str(s.get("quality", "")), "pick", bi, bi == sel)
			if known.has(str(s.id)): _tag(r, str(known[str(s.id)]))
			_placed[bi] = r.get_center()
		if shelves > 1:
			btn(Rect2(TRAY.end.x - 80, TRAY.position.y + 52, 64, SLOT), Tx.t("ui.gift.more") % (gifts.size() - shown.size()), "more", null, false, true, "", 18)
	# Give, and what it would do.
	var gifted := int(a.get("gift_day", -1)) == Clock.reset_day(Clock.now_utc())
	var gy := TRAY.position.y + 136
	btn(Rect2(x, gy, 170, 48), Tx.t("ui.gift.give"), "give", sel, true, sel >= 0 and not gifted,
		Tx.t("ui.gift.given_today") if gifted else Tx.t("ui.gift.pick_first"), 20)
	var line := Tx.t("ui.gift.pick_first")
	var col := UiKit.MIST
	if gifted: line = Tx.t("ui.gift.given_today")
	elif sel >= 0 and sel < ch.inventory.bag.size() and ch.inventory.bag[sel] != null:
		var it := str(ch.inventory.bag[sel].id)
		line = Tx.t("ui.gift.picked_" + str(known[it])) % ContentDB.item_name(it) if known.has(it) else ContentDB.item_name(it)
		col = UiKit.PAPER
	text(Vector2(x + 186, gy + 30), line, 16, col, HORIZONTAL_ALIGNMENT_LEFT, TRAY.end.x - x - 210)

## A known gift's tag over its compartment: "Loves it" or "Likes it", ink on the heart's pink, ringed in ink.
func _tag(slot: Rect2, kind: String) -> void:
	var words := Tx.t("ui.gift.tag_" + kind)
	var w := UiKit.text_width(words, 14) + 18
	var r := Rect2(roundf(slot.get_center().x - w * 0.5), slot.position.y - 12, w, 22)
	rounded(r.grow(2), 11.0, UiKit.INK)
	rounded(r, 10.0, BondsKit.TAG)
	ground(r, BondsKit.TAG)
	text(Vector2(r.position.x, r.position.y + 16), words, 14, UiKit.INK, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

## The strip's words: their answer to today's gift and what it taught you, or the rules before one; the heart bar under
## them, filling to where the gift brought it, and what the gift moved beside it.
func _answer(ch, a: Dictionary) -> void:
	var fr := frame_rect
	var x := fr.position.x + 220
	var id := Game.relations.aff_id(npc)
	if not answer.is_empty():
		var reaction := str(answer.reaction)
		text(Vector2(x, fr.position.y + 114), Tx.t("ui.gift.reaction_" + reaction) % ContentDB.name_of("npcs", id), 26, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, 580, true)
		para(Rect2(x, fr.position.y + 124, 580, 28), Tx.t("ui.gift.learned_" + reaction), 18, RecordsKit.INK, 1)
	else:
		para(Rect2(x, fr.position.y + 90, 580, 66), Tx.t("ui.gift.rules"), 16, RecordsKit.INK, 3)
	var per := int(Game.relations.acfg().get("per_heart", 100))
	var top := int(Game.relations.acfg().get("max_hearts", 5))
	var pts := int(a.get("points", 0))
	var br := Rect2(x, fr.position.y + 162, 420, 26)
	if ch.relations.hearts_of(id) >= top:
		bar(br, 1.0, UiKit.HEART, Tx.t("ui.gift.all_hearts"))
	else:
		var shown := float(pts)
		if not answer.is_empty() and not UiKit.reduce_motion():
			shown = lerpf(float(answer.before), float(pts), clampf((t - float(answer.at)) / LIFT_S, 0.0, 1.0))
		bar(br, fposmod(shown, float(per)) / float(per), UiKit.HEART, Tx.t("ui.gift.next_heart") % [pts % per, per])
	if not answer.is_empty():
		text(Vector2(br.end.x + 14, br.position.y + 20), Tx.t("ui.gift.moved") % int(answer.delta), 20, RecordsKit.JADE_INK)

## The given gift lifting from its compartment toward the speaker (none under Reduce motion).
func _lift() -> void:
	if answer.is_empty() or UiKit.reduce_motion(): return
	var k := clampf((t - float(answer.at)) / LIFT_S, 0.0, 1.0)
	if k >= 1.0: return
	var to := frame_rect.position + Vector2(104, 96)
	var p: Vector2 = (answer.from as Vector2).lerp(to, 1.0 - pow(1.0 - k, 2.0))
	p.y -= sin(k * PI) * 60.0
	icon_at(Rect2((p - Vector2(32, 32)).round(), Vector2(64, 64)), str(answer.item), Color(1, 1, 1, 1.0 - 0.6 * k))

func on_action(id: String, data) -> void:
	match id:
		"pick": sel = int(data)
		"more": shelf += 1
		"give":
			var ch = c()
			var aid := Game.relations.aff_id(npc)
			var before := int(ch.relations.affinity.get(aid, {}).get("points", 0))
			var from: Vector2 = _placed.get(int(data), TRAY.get_center())
			var r := submit({"type": "give_gift", "npc": npc, "index": int(data)})
			if r.get("ok", false):
				var after := int(ch.relations.affinity.get(aid, {}).get("points", 0))
				answer = {"reaction": str(r.reaction), "item": str(r.item), "delta": after - before, "before": before, "from": from, "at": t}
				sel = -1
		_: super.on_action(id, data)
	queue_redraw()

## A choice that leads on hands the talk back to the Dialogue.
func _go_on(next: Dictionary) -> void:
	navigate.emit("dialogue", {"convo": next})
	close()
