extends Page
## Mail (S41): one account-wide inbox; attachments are claimed into the bag and kept attached when the bag is full.
## P5 (docs/page_identity.md row 17, mockup 22): the letter case on a writing desk. The envelopes lie in a fanned stack
## at the left, newest on top, unread ones sealed in red wax, those that carry something tied with hemp string; the
## chosen one slides out and its letter lies unfolded on the felt at the right, the two creases opening, the words in
## ink and the sender's name at its foot; what it carries is tied beneath it as a parcel, and Claim unties it.

const DESK := Rect2(64, 32, 1152, 656)
const STACK := Rect2(96, 112, 424, 448)   # the envelopes, 64 a row
const MAT := Rect2(540, 100, 648, 572)    # the felt under the open letter
const SHEET := Rect2(572, 118, 584, 388)  # the letter unfolded
const PARCEL := Rect2(572, 520, 584, 78)  # what it carries
const UNFOLD_S := 0.3

var sel := -1
var opened_at := -1.0     # when the chosen letter was taken out (it unfolds over UNFOLD_S)

func _init() -> void:
	title = Tx.t("ui.mail.mail")
	identity = Identity.new("wood", false, "own", "envelope_stack_open_letter", 0.3)

## Open on the newest letter, so the page never starts with an empty reading pane.
func setup() -> void:
	var mails: Array = Game.mail.visible(c())
	if not mails.is_empty(): on_action("sel", int(mails[0].id))

func content_rect() -> Rect2:
	return Rect2(88, 104, 1112, 568)

func draw_surface(r: Rect2) -> void:
	RecordsKit.timber(self, r, UiKit.SURFACE.wood, false, 90.0)

func title_rect() -> Rect2:
	return Rect2(88, 44, 180, 56)

## The title on a small lacquer name plate on the letter rack.
func draw_title_mount(r: Rect2) -> void:
	rounded(r.grow(2), 5.0, UiKit.INK)
	rounded(r, 4.0, UiKit.GOLD)
	vshade(r.grow(-2), UiKit.SURFACE.lacquer.lerp(UiKit.BLOOD, 0.15), UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.2))
	ground(r, UiKit.SURFACE.lacquer)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var mails: Array = Game.mail.visible(ch)   # newest first
	var unread := mails.filter(func(m): return not m.get("read", false)).size()
	var carry := mails.filter(func(m): return _carries(m)).size()
	text(Vector2(284, 66), Tx.plural("ui.mail.letters", mails.size()) % mails.size(), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 500)
	text(Vector2(284, 88), Tx.t("ui.mail.unread_carry") % [unread, carry], 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 500)
	# Decision 43: a tour's anchors (the envelopes, the open letter and what it carries).
	tour_mark("stack", STACK)
	tour_mark("letter", SHEET)
	tour_mark("parcel", PARCEL)
	_stack(mails)
	btn(Rect2(112, 596, 240, 56), Tx.t("ui.mail.claim_all") + (" · %d" % carry if carry > 0 else ""), "claim_all", null, true, carry > 0, Tx.t("ui.mail.nothing_to_claim"))
	para(Rect2(364, 604, 156, 48), Tx.t("ui.mail.claim_all_note"), 14, UiKit.PAPER, 2)
	var mm := {}
	for m in mails:
		if int(m.id) == sel: mm = m
	_letter(mm)

func _carries(m: Dictionary) -> bool:
	return not (m.get("attachments", []) as Array).is_empty() and not m.get("claimed", false)

## The stack of envelopes, newest on top, a little fanned; drag or wheel through the older ones.
func _stack(mails: Array) -> void:
	if mails.is_empty():
		para(Rect2(STACK.position + Vector2(16, 30), Vector2(STACK.size.x - 32, 80)), Tx.t("ui.mail.no_letters"), 18, UiKit.PAPER)
		return
	var slide := 1.0 if opened_at < 0.0 or UiKit.reduce_motion() else clampf((t - opened_at) / 0.2, 0.0, 1.0)
	list("mail", STACK, mails.size(), 64, func(i: int, rr: Rect2):
		var m: Dictionary = mails[i]
		var chosen := int(m.id) == sel
		var r := Rect2(rr.position + Vector2(float([2, 8, -2, 6, 0][i % 5]) + (18.0 * slide if chosen else 0.0), 0), Vector2(392, 60))
		face(r, "envelope", "selected" if chosen else "normal")
		RecordsKit.wax(self, r.position + Vector2(28, 30), m.get("read", false))
		var right := r.end.x - (44.0 if _carries(m) else 12.0)
		text(r.position + Vector2(56, 26), str(m.subject), 16, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, right - r.position.x - 56)
		text(r.position + Vector2(56, 50), str(m.from), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, 200)
		text(Vector2(r.end.x - 132, r.position.y + 50), _when(m), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_RIGHT, 120)
		if _carries(m): _knot(r.position + Vector2(r.size.x - 22, 18))
		region(r, "sel", int(m.id))
	)

## The string's knot on an envelope that carries something.
func _knot(c: Vector2) -> void:
	var col := UiKit.SURFACE.hemp.lerp(UiKit.BRONZE, 0.55)
	draw_line(c - Vector2(10, 0), c + Vector2(10, 0), col, 3.0, true)
	draw_line(c - Vector2(0, 10), c + Vector2(0, 10), col, 3.0, true)
	draw_circle(c, 5.0, col, true, -1.0, true)
	draw_circle(c, 3.0, UiKit.SURFACE.hemp, true, -1.0, true)

## "today", or how long ago it came ("3 days ago", by the span).
func _when(m: Dictionary) -> String:
	var days := int((Clock.now_utc() - float(m.get("received_utc", Clock.now_utc()))) / 86400.0)
	return Tx.t("ui.mail.today") if days <= 0 else Tx.t("ui.mail.ago") % UiKit.span(days * 86400.0)

## The open letter on its felt mat: unfolding from its thirds as it is taken out; the parcel it carries beneath.
func _letter(mm: Dictionary) -> void:
	rounded(MAT.grow(2), 7.0, UiKit.RIVER_NIGHT)
	vshade(MAT, UiKit.SURFACE.cloth.lerp(UiKit.JADE_SHADOW, 0.15), UiKit.SURFACE.cloth.lerp(UiKit.INK, 0.2))
	ground(MAT, UiKit.SURFACE.cloth)
	if mm.is_empty():
		text(MAT.position + Vector2(0, 80), Tx.t("ui.mail.choose_letter"), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, MAT.size.x)
		return
	var k := 1.0 if opened_at < 0.0 or UiKit.reduce_motion() else clampf((t - opened_at) / UNFOLD_S, 0.0, 1.0)
	k = 1.0 - pow(1.0 - k, 3.0)
	# The sheet opens from its left third: the two creases open one after the other.
	move(SHEET.position, 0.0, Vector2(lerpf(1.0 / 3.0, 1.0, k), 1.0))
	face(Rect2(Vector2.ZERO, SHEET.size), "letter_sheet")
	for f in [1.0 / 3.0, 2.0 / 3.0]:
		var x := roundf(SHEET.size.x * f)
		draw_rect(Rect2(x - 1, 6, 1, SHEET.size.y - 14), Color(UiKit.BRONZE, 0.22))
		draw_rect(Rect2(x, 6, 2, SHEET.size.y - 14), Color(UiKit.PAPER, 0.35))
		hshade(Rect2(x - 14, 6, 14, SHEET.size.y - 14), Color(UiKit.BRONZE, 0.0), Color(UiKit.BRONZE, 0.07))
	move()
	# Under Reduce motion the letter fades in instead (the felt laid over it, thinning).
	if UiKit.reduce_motion() and opened_at >= 0.0:
		var fade := clampf((t - opened_at) / UiKit.MOTION_FADE_S, 0.0, 1.0)
		if fade < 1.0: draw_rect(SHEET.grow(2), Color(UiKit.SURFACE.cloth, 1.0 - fade))
	if k >= 1.0:
		ground(SHEET, UiKit.SURFACE.scroll)
		var x := SHEET.position.x + 28
		var w := SHEET.size.x - 56
		text(Vector2(x, SHEET.position.y + 70), str(mm.subject), 34 if UiKit.text_width(str(mm.subject), 34, true) <= w else 26, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, w, true)
		text(Vector2(x, SHEET.position.y + 100), Tx.t("ui.mail.from_when") % [str(mm.from), _when(mm)], 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, w)
		para(Rect2(x, SHEET.position.y + 120, w, 170), str(mm.body), 20, RecordsKit.INK, 5)
		# The sender's name at the foot, with a red seal beside it.
		var sign := str(mm.from).get_slice(",", 0)
		text(Vector2(SHEET.end.x - 96 - 300, SHEET.end.y - 60), sign, 26, RecordsKit.INK, HORIZONTAL_ALIGNMENT_RIGHT, 300, true)
		var seal := Rect2(SHEET.end.x - 80, SHEET.end.y - 90, 34, 34)
		rounded(seal, 3.0, UiKit.BLOOD)
		draw_rect(seal.grow(-3), Color(UiKit.PALE_GOLD, 0.7), false, 2.0)
	# The paperweight across the letter's head.
	rounded(Rect2(640, 108, 260, 20), 5.0, UiKit.INK)
	vshade(Rect2(641, 109, 258, 18), UiKit.SURFACE.stone.lerp(UiKit.PAPER, 0.1), UiKit.SURFACE.stone.lerp(UiKit.INK, 0.6))
	_parcel(mm)
	if _carries(mm): btn(Rect2(980, 612, 176, 52), Tx.t("ui.mail.claim"), "claim", int(mm.id), true)
	btn(Rect2(572, 614, 140, 48), Tx.t("ui.mail.delete"), "delete", int(mm.id), false, not _carries(mm), Tx.t("ui.mail.claim_first"), 20)

## What the letter carries, tied beneath it as a parcel; once claimed, the string lies loose.
func _parcel(mm: Dictionary) -> void:
	var atts: Array = mm.get("attachments", [])
	if atts.is_empty() and not mm.get("claimed", false): return
	rounded(PARCEL.grow(1), 6.0, UiKit.BRONZE)
	vshade(PARCEL, UiKit.SURFACE.hemp, UiKit.SURFACE.hemp.lerp(UiKit.BRONZE, 0.15))
	ground(PARCEL, UiKit.SURFACE.hemp.lerp(UiKit.BRONZE, 0.15))
	RecordsKit.string_tie(self, PARCEL, PARCEL.end.x - 114, _carries(mm))
	if atts.is_empty():
		text(PARCEL.position + Vector2(18, 46), Tx.t("ui.mail.claimed"), 16, RecordsKit.INK)
		return
	text(PARCEL.position + Vector2(18, 30), Tx.t("ui.mail.it_carries"), 16, RecordsKit.INK)
	var x := PARCEL.position.x + 112
	var named := false
	for a in atts:
		if x > PARCEL.end.x - 240: break
		if a.has("currency"):
			x += currency_pill(Vector2(x, PARCEL.position.y + 22), str(a.currency), int(a.amount)) + 12
		elif a.has("item") or a.has("instance"):
			var item := str(a.get("item", (a.get("instance", {}) as Dictionary).get("id", "")))
			slot_box(Rect2(x, PARCEL.position.y + 1, SLOT, SLOT), item, int(a.get("count", 1)), str(a.get("quality", "")))
			x += SLOT + 10
			if not named and x < PARCEL.end.x - 260:
				named = true
				var d := ContentDB.item(item)
				text(Vector2(x, PARCEL.position.y + 32), ContentDB.item_name(item), 16, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, 150)
				text(Vector2(x, PARCEL.position.y + 54), str(d.get("grade", "plain")).capitalize(), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, 150)
				x += 160

func on_action(id: String, data) -> void:
	match id:
		"sel":
			if int(data) != sel: opened_at = t
			sel = int(data)
			submit({"type": "read_mail", "id": sel})
		"claim": submit({"type": "claim_mail", "id": int(data)})
		"claim_all": submit({"type": "claim_all"})
		"delete":
			if submit({"type": "delete_mail", "id": int(data)}).get("ok", false): sel = -1
