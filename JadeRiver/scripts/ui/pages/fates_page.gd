extends Page
## Breakthrough fates (S48): after a major breakthrough, three cards drawn from the deck. Each carries a gift and,
## most often, a cost; one is chosen. Closing the page keeps the offer (the Heart tab reopens it).
## P5 (docs/page_identity.md row 40, the way family): fortune sticks shaken from a bamboo cylinder under the stars. The
## cylinder stands low in the centre with three sticks fanned out of it, each carrying its verse on a paper slip: the
## fate's name, the gift above and the cost below, Take this fate at the slip's foot. The sticks rise out one after
## another as the page opens (a tap shows all; under Reduce motion all three are there).

const CYLINDER := Rect2(584, 572, 112, 84)
const MOUTH := Vector2(640, 578)
const SLIP_W := 280.0
const SLIP_TOP := [212.0, 192.0, 212.0]
const SLIP_FOOT := 500.0

func _init() -> void:
	title = Tx.t("ui.fates.title")
	frame_rect = WINDOW_LARGE
	identity = Identity.new("sky_top", false, "own", "sticks_fanned_from_cylinder", OPEN_MOTION_MAX)

func content_rect() -> Rect2:
	return Rect2(frame_rect.position.x + 24, frame_rect.position.y + 80, frame_rect.size.x - 48, frame_rect.size.y - 96)

## The night the fortune is read under.
func draw_surface(r: Rect2) -> void:
	WayKit.night(self, r, 120, [Rect2(r.position.x + 300, r.position.y, 424, 70)])
	glow(Rect2(MOUTH.x - 260, MOUTH.y - 120, 520, 220), Color(UiKit.PALE_GOLD, 0.08 * _halo()))
	draw_rect(r, Color(UiKit.GOLD, 0.35), false, 1.0)

func title_rect() -> Rect2:
	return Rect2(frame_rect.get_center().x - 210, frame_rect.position.y + 12, 420, 52)

func draw_title_mount(r: Rect2) -> void:
	WayKit.tablet(self, r, true)

## Where slip `i` of `n` hangs, centred over its stick's end.
func slip_rect(i: int, n: int) -> Rect2:
	var cx := MOUTH.x + (float(i) - float(n - 1) * 0.5) * 310.0
	var top: float = SLIP_TOP[clampi(i + (3 - n) / 2, 0, 2)] if n > 1 else SLIP_TOP[1]
	return Rect2(cx - SLIP_W * 0.5, top, SLIP_W, SLIP_FOOT - top)

## How far stick `i` has risen out of the cylinder, 0 to 1: one after another over the opening.
func risen(i: int) -> float:
	return clampf(unfold() * 1.5 - 0.25 * i, 0.0, 1.0)

## How far below its resting place slip `i` (and its stick) still is while it rises.
func _lift(i: int, sr: Rect2) -> float:
	return (1.0 - risen(i)) * (sr.size.y + 60.0)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var cards: Array = ch.cultivator.fate_offer
	if cards.is_empty():
		para(Rect2(frame_rect.position.x + 160, 300, frame_rect.size.x - 320, 80), Tx.t("ui.fates.none"), 20, UiKit.MIST)
		_cylinder(0)
		return
	para(Rect2(frame_rect.position.x + 120, frame_rect.position.y + 78, frame_rect.size.x - 240, 50), Tx.t("ui.fates.intro"), 16, UiKit.MIST, 2)
	# The sticks first, from inside the cylinder up behind their slips; then the slips over them.
	for i in cards.size():
		var sr := slip_rect(i, cards.size())
		move(Vector2(0, _lift(i, sr)))
		var tip := Vector2(sr.get_center().x, sr.position.y - 14)
		var foot := MOUTH + Vector2((float(i) - float(cards.size() - 1) * 0.5) * 10.0, 30)
		draw_line(foot, tip, UiKit.INK, 12.0, true)
		draw_line(foot, tip, UiKit.SURFACE.bamboo, 8.0, true)
		draw_line(foot + Vector2(-2, 0), tip + Vector2(-2, 0), Color(UiKit.PAPER, 0.35), 2.0, true)
		draw_circle(tip, 5.0, UiKit.BLOOD, true, -1.0, true)
	for i in cards.size():
		var sr := slip_rect(i, cards.size())
		move(Vector2(0, _lift(i, sr)))
		_slip(ContentDB.entry("fates", str(cards[i])), sr)
		move()
		# Take this fate at the slip's foot, where it comes to rest.
		btn(Rect2(sr.position.x + 18, sr.end.y - 70, sr.size.x - 36, 56), Tx.t("ui.fates.choose"), "choose", str(cards[i]), true)
	move()
	_cylinder(cards.size())

## A fate's verse on its paper slip: the name, the gift above and the cost below; a rare fate carries a red seal.
func _slip(f: Dictionary, sr: Rect2) -> void:
	rounded(Rect2(sr.position + Vector2(3, 4), sr.size), 4.0, Color(UiKit.INK, 0.5))
	rounded(sr, 4.0, UiKit.SURFACE.scroll_edge)
	rounded(sr.grow(-3), 3.0, UiKit.SURFACE.scroll)
	ground(sr, UiKit.SURFACE.scroll)
	draw_rect(Rect2(sr.position.x + 10, sr.position.y + 8, sr.size.x - 20, 2), Color(UiKit.BLOOD, 0.7))
	var rare: bool = f.get("rare", false)
	var x := sr.position.x + 18
	var w := sr.size.x - 36
	var y := sr.position.y + 18
	if rare:
		var seal := Rect2(sr.end.x - 70, y, 54, 30)
		rounded(seal, 3.0, UiKit.BLOOD)
		ground(seal, UiKit.BLOOD)
		text(Vector2(seal.position.x, seal.position.y + 21), Tx.t("ui.fates.rare"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, seal.size.x)
	y += para(Rect2(x, y, w - (60.0 if rare else 0.0), 64), str(f.get("name", "")), 22, UiKit.PAPER_INK, 2, true) + 10
	text(Vector2(x, y + 12), Tx.t("ui.fates.gift"), 14, UiKit.PAPER_INK)
	y += 18
	y += para(Rect2(x, y, w, 88), str(f.get("gift_text", "")), 18, UiKit.JADE_SHADOW, 4) + 8
	draw_line(Vector2(x, y), Vector2(x + w, y), Color(UiKit.PAPER_INK, 0.3), 1.0)
	y += 8
	text(Vector2(x, y + 12), Tx.t("ui.fates.cost"), 14, UiKit.PAPER_INK)
	y += 18
	y += para(Rect2(x, y, w, sr.end.y - 80 - y), str(f.get("cost_text", "")), 18, UiKit.BLOOD, 4) + 4
	if not (f.get("realm_modifiers", []) as Array).is_empty() and y + 20 < sr.end.y - 76:
		para(Rect2(x, y, w, sr.end.y - 76 - y), Tx.t("ui.fates.this_realm"), 14, UiKit.PAPER_INK, 2)

## The bamboo cylinder the sticks were shaken from, bound in bronze, `left` sticks still standing in it.
func _cylinder(left: int) -> void:
	var r := CYLINDER
	for i in 5 - mini(left, 3):
		var x := r.position.x + 30 + i * 12.0
		draw_line(Vector2(x, r.position.y + 10), Vector2(x - 6 + i * 3, r.position.y - 26), UiKit.INK, 8.0, true)
		draw_line(Vector2(x, r.position.y + 10), Vector2(x - 6 + i * 3, r.position.y - 26), UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.2), 5.0, true)
	rounded(r.grow(2), 10.0, UiKit.INK)
	hshade(r, UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.35), UiKit.SURFACE.bamboo)
	hshade(Rect2(r.get_center().x, r.position.y, r.size.x * 0.5, r.size.y), UiKit.SURFACE.bamboo, UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.4))
	for y in [r.position.y + 14, r.end.y - 18]:
		draw_rect(Rect2(r.position.x, y, r.size.x, 6), UiKit.BRONZE)
		draw_rect(Rect2(r.position.x, y, r.size.x, 1), UiKit.GOLD)
	draw_set_transform(Vector2(r.get_center().x, r.position.y), 0.0, Vector2(1.0, 0.25))
	draw_circle(Vector2.ZERO, r.size.x * 0.5, UiKit.INK, true, -1.0, true)
	draw_arc(Vector2.ZERO, r.size.x * 0.5 - 1.0, 0.0, TAU, 32, UiKit.SURFACE.bamboo, 3.0, true)
	draw_set_transform(Vector2.ZERO)

func on_action(id: String, data) -> void:
	if id == "choose":
		var r := submit({"type": "choose_fate", "card": str(data)})
		if r.get("ok", false): closed.emit(self)
