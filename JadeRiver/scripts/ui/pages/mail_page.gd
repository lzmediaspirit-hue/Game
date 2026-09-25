extends Page
## Mail (S41): one account-wide inbox; attachments are claimed into the bag and kept
## attached when the bag is full.

var sel := -1

func _init() -> void:
	title = Tx.t("ui.mail.mail")

## Open on the newest letter, so the page never starts with an empty reading pane.
func setup() -> void:
	var mails: Array = Game.mail.visible(c())
	if not mails.is_empty(): on_action("sel", int(mails[0].id))

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var mails: Array = Game.mail.visible(ch)   # newest first
	var left := Rect2(content.position.x, content.position.y, 440, content.size.y - 70)
	panel(left)
	if mails.is_empty(): text(left.position + Vector2(0, 70), Tx.t("ui.mail.no_letters"), 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, left.size.x)
	list("mail", left.grow(-10), mails.size(), 64, func(i: int, rr: Rect2):
		var m: Dictionary = mails[i]
		panel(rr, "minor_panel", "selected" if int(m.id) == sel else "normal")
		if not m.get("read", false): draw_circle(rr.position + Vector2(16, 32), 6, UiKit.RED)
		text(rr.position + Vector2(32, 28), str(m.subject), 18, UiKit.PAPER)
		text(rr.position + Vector2(32, 50), str(m.from), 15, UiKit.MIST)
		if not (m.get("attachments", []) as Array).is_empty() and not m.get("claimed", false): icon_at(Rect2(rr.end.x - 40, rr.position.y + 16, 28, 28), "open")
		region(rr, "sel", int(m.id))
	)
	btn(Rect2(content.position.x, content.end.y - 58, 210, 54), Tx.t("ui.mail.claim_all"), "claim_all", null, true)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	var mm := {}
	for m in mails:
		if int(m.id) == sel: mm = m
	if mm.is_empty(): return
	heading(right.position + Vector2(24, 44), str(mm.subject), right.size.x - 48)
	text(right.position + Vector2(24, 74), Tx.t("ui.mail.from") % str(mm.from), 17, UiKit.MIST)
	para(Rect2(right.position + Vector2(24, 90), Vector2(right.size.x - 48, 200)), str(mm.body), 19)
	var x := right.position.x + 24
	for a in mm.get("attachments", []):
		if a.has("item"):
			slot_box(Rect2(x, right.end.y - 150, 60, 60), str(a.item), int(a.get("count", 1)))
			x += 68
		elif a.has("currency"):
			x += currency_pill(Vector2(x, right.end.y - 138), str(a.currency), int(a.amount)) + 8
	if not (mm.get("attachments", []) as Array).is_empty() and not mm.get("claimed", false):
		btn(Rect2(right.end.x - 224, right.end.y - 70, 200, 54), Tx.t("ui.mail.claim"), "claim", int(mm.id), true)
	btn(Rect2(right.position.x + 24, right.end.y - 70, 160, 54), Tx.t("ui.mail.delete"), "delete", int(mm.id))

func on_action(id: String, data) -> void:
	match id:
		"sel":
			sel = int(data)
			submit({"type": "read_mail", "id": sel})
		"claim": submit({"type": "claim_mail", "id": int(data)})
		"claim_all": submit({"type": "claim_all"})
		"delete":
			if submit({"type": "delete_mail", "id": int(data)}).get("ok", false): sel = -1
