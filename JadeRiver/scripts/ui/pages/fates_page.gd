extends Page
## Breakthrough fates (S48): after a major breakthrough, three cards drawn from the deck. Each carries a gift and,
## most often, a cost; one is chosen. Closing the page keeps the offer (the Heart tab reopens it).

func _init() -> void:
	title = Tx.t("ui.fates.title")
	frame_rect = Rect2(120, 70, 1040, 580)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var cards: Array = ch.cultivator.fate_offer
	if cards.is_empty():
		para(Rect2(content.position.x + 20, content.position.y + 30, content.size.x - 40, 80), Tx.t("ui.fates.none"), 20, UiKit.MIST)
		return
	para(Rect2(content.position.x + 20, content.position.y + 4, content.size.x - 40, 50), Tx.t("ui.fates.intro"), 18, UiKit.MIST, 2)
	var gap := 22.0
	var cw := (content.size.x - 40 - gap * (cards.size() - 1)) / float(cards.size())
	var top := content.position.y + 64
	for i in cards.size():
		var f := ContentDB.entry("fates", str(cards[i]))
		var cr := Rect2(content.position.x + 20 + i * (cw + gap), top, cw, content.end.y - top - 10)
		panel(cr, "minor_panel", "selected" if f.get("rare", false) else "normal")
		draw_rect(cr.grow(-6), Color(UiKit.GOLD, 0.35), false, 1.5)
		var x := cr.position.x + 20
		var y := cr.position.y + 16
		if f.get("rare", false): text(Vector2(cr.end.x - 110, y + 16), Tx.t("ui.fates.rare"), 15, UiKit.GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 90)
		y += para(Rect2(x, y, cw - 40 - (70 if f.get("rare", false) else 0), 70), str(f.get("name", "")), 23, UiKit.PALE_GOLD, 2) + 30
		text(Vector2(x, y), Tx.t("ui.fates.gift"), 16, UiKit.MIST)
		y += 4
		y += para(Rect2(x, y, cw - 40, 90), str(f.get("gift_text", "")), 19, UiKit.BRIGHT_JADE, 4) + 18
		draw_line(Vector2(x, y - 8), Vector2(cr.end.x - 20, y - 8), Color(UiKit.GOLD, 0.25), 1.0)
		y += 14
		text(Vector2(x, y), Tx.t("ui.fates.cost"), 16, UiKit.MIST)
		y += 4
		y += para(Rect2(x, y, cw - 40, 90), str(f.get("cost_text", "")), 19, Color("e07a7a"), 4) + 16
		if not (f.get("realm_modifiers", []) as Array).is_empty():
			para(Rect2(x, y, cw - 40, 50), Tx.t("ui.fates.this_realm"), 15, UiKit.MIST, 2)
		btn(Rect2(cr.position.x + 20, cr.end.y - 74, cw - 40, 56), Tx.t("ui.fates.choose"), "choose", str(cards[i]), true)

func on_action(id: String, data) -> void:
	if id == "choose":
		var r := submit({"type": "choose_fate", "card": str(data)})
		if r.get("ok", false): closed.emit(self)
