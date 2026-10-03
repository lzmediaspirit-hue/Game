extends Page
## Breakthrough dialog (S05): requirements with their fixes, support items that
## lower the risk, risk word and success chance, then the 3 s channel.
## P5 (docs/page_identity.md row 9, the way family): the heaven gate at the top of the stair. One stone archway against
## the night: the title on the gold-leafed plaque of its beam and the step it leads to written in the doorway; each
## requirement hangs from the beam on red cords as a tablet, lit with gold leaf when met, dark with its Go when not;
## three jade offering dishes on the step hold the supports, chosen from the stele at the right, which also says what
## weighs on the attempt; the risk and the chance are cut into the two pillars; Break Through stands on the threshold and
## opens the doors (0.5 s) into moment 05. Core Forging's checklist stands on the stele at the left.

const ROOF := Rect2(316, 70, 648, 34)
const BEAM := Rect2(330, 100, 620, 64)
const PILLARS := [Rect2(366, 164, 112, 420), Rect2(802, 164, 112, 420)]
const OPENING := Rect2(478, 164, 324, 420)
const STEP := Rect2(330, 584, 620, 32)
const THRESHOLD := Rect2(290, 616, 700, 56)
const LEFT_STELE := Rect2(88, 188, 256, 360)
const RIGHT_STELE := Rect2(928, 188, 264, 396)
const TABLETS := Rect2(494, 240, 292, 256)   # where the requirement tablets hang
const DISH_Y := 500.0
const DOORS_S := 0.5   # the doors open into moment 05 (page_identity §6 rule 2)

var supports: Array = []
var _doors_at := -1.0   # the page clock when Break Through opened the doors

func _init() -> void:
	title = Tx.t("ui.breakthrough.breakthrough")
	identity = Identity.new("sky_top", false, "own", "archway_tablets_offering_dishes", 0.3)

func content_rect() -> Rect2:
	return Rect2(88, 156, 1104, 516)

func support_candidates(ch) -> Array:
	var out: Array = []
	for s in ch.inventory.bag:
		if s != null and ContentDB.item(str(s.id)).has("support") and not out.has(str(s.id)): out.append(str(s.id))
	return out

## How far the doors have opened, 0 to 1 (under Reduce motion the light only fades in).
func doors_open() -> float:
	if _doors_at < 0.0: return 0.0
	return clampf((t - _doors_at) / (UiKit.MOTION_FADE_S if UiKit.reduce_motion() else DOORS_S), 0.0, 1.0)

func _process(delta: float) -> void:
	super(delta)
	if _doors_at >= 0.0 and doors_open() >= 1.0:
		_doors_at = -1.0
		close()

## The night behind the gate, the terrace at its foot, and the gate itself: roof, beam, pillars, doors, step, threshold.
func draw_surface(r: Rect2) -> void:
	WayKit.night(self, r, 110, [ROOF.grow(40), OPENING])
	vshade(Rect2(r.position.x, 560, r.size.x, r.end.y - 560), Color(UiKit.SURFACE.stone.lerp(UiKit.INK, 0.7), 0.0), UiKit.SURFACE.stone.lerp(UiKit.INK, 0.6))
	draw_rect(r, Color(UiKit.GOLD, 0.35), false, 1.0)
	_doors(doors_open())
	for p in PILLARS: WayKit.stone(self, p, UiKit.SURFACE.stone, 36.0, 56.0)
	WayKit.stone(self, BEAM, UiKit.SURFACE.stone, 26.0, 80.0)
	# The roof: dark tiles with upturned eaves.
	var eave := PackedVector2Array([Vector2(ROOF.position.x - 14, ROOF.position.y - 6), Vector2(ROOF.position.x + 40, ROOF.position.y + 8), Vector2(ROOF.end.x - 40, ROOF.position.y + 8),
		Vector2(ROOF.end.x + 14, ROOF.position.y - 6), Vector2(ROOF.end.x - 6, ROOF.end.y), Vector2(ROOF.position.x + 6, ROOF.end.y)])
	draw_colored_polygon(eave, UiKit.INK)
	draw_colored_polygon(PackedVector2Array(Array(eave).map(func(p): return p + (Vector2(640, 88) - p) * 0.04)), UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.2))
	for i in 24:
		var x := ROOF.position.x + 24 + i * 25.0
		draw_line(Vector2(x, ROOF.position.y + 10), Vector2(x, ROOF.end.y - 2), Color(UiKit.INK, 0.6), 2.0)
	draw_rect(Rect2(BEAM.position.x, BEAM.end.y - 3, BEAM.size.x, 3), UiKit.INK)
	WayKit.stone(self, STEP, UiKit.SURFACE.stone, 32.0, 88.0)
	WayKit.stone(self, THRESHOLD, UiKit.SURFACE.stone.lerp(UiKit.INK, 0.15), 28.0, 100.0)

## The doors in the opening: two leaves of dark timber studded in bronze, a line of heaven's light between them; they swing
## open by `o` (under Reduce motion they stay and the light cross-fades over them).
func _doors(o: float) -> void:
	var r := OPENING
	var half := r.size.x * 0.5
	var leaf := UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.3)
	glow(Rect2(r.get_center().x - 60 - 160 * o, r.position.y, 120 + 320 * o, r.size.y), Color(UiKit.PALE_GOLD, (0.25 + 0.6 * o) * halo_k()))
	var swing := 0.0 if UiKit.reduce_motion() else o
	var fade := 1.0 - (o if UiKit.reduce_motion() else 0.0)
	for side in [0, 1]:
		var w := half * (1.0 - 0.85 * swing)
		var lr := Rect2(r.position.x if side == 0 else r.end.x - w, r.position.y, w, r.size.y)
		draw_rect(lr, Color(leaf, fade))
		draw_rect(lr, Color(UiKit.INK, 0.8 * fade), false, 2.0)
		for row in 6:
			for col in 3:
				var at := Vector2(lr.position.x + lr.size.x * (0.2 + 0.3 * col), lr.position.y + 40 + row * 64)
				draw_circle(at, 3.5, Color(UiKit.BRONZE, fade), true, -1.0, true)
	if o <= 0.0: draw_line(Vector2(r.get_center().x, r.position.y), Vector2(r.get_center().x, r.end.y), Color(UiKit.PALE_GOLD, 0.8 * halo_k()), 2.0)
	ground(r, leaf)

func title_rect() -> Rect2:
	return Rect2(BEAM.get_center().x - 160, BEAM.position.y + 4, 320, 56)

func draw_title_mount(r: Rect2) -> void:
	WayKit.tablet(self, r, true)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var q: Dictionary = Game.progression.query_breakthrough(ch, supports)
	# Decision 43: a tour's anchors (the doorway's words, the requirement tablets, the offering dishes, the stele).
	tour_mark("doorway", Rect2(OPENING.position, Vector2(OPENING.size.x, 76)))
	tour_mark("tablets", TABLETS)
	tour_mark("dishes", Rect2(OPENING.get_center().x - 148, DISH_Y - 8, 296, SLOT + 28))
	tour_mark("supports", RIGHT_STELE)
	# In the doorway: the step it leads from, and to.
	text(Vector2(OPENING.position.x, OPENING.position.y + 28), Tx.t("ui.breakthrough.from") % ContentDB.name_of("realms", str(q.from)), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, OPENING.size.x)
	text(Vector2(OPENING.position.x, OPENING.position.y + 60), ContentDB.name_of("realms", str(q.to)), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, OPENING.size.x - 16, true)
	var top := TABLETS.position.y
	if str(q.get("event", "")) != "":
		text(Vector2(OPENING.position.x, OPENING.position.y + 86), Tx.t("ui.breakthrough.trial") % ContentDB.text("event." + str(q.event)), 16, UiKit.SOUL_TEXT, HORIZONTAL_ALIGNMENT_CENTER, OPENING.size.x)
		top += 16
	move(Vector2(0, -(1.0 - unfold()) * 20.0))
	_tablets(q, top)
	move()
	_pillars(q)
	_dishes(ch)
	_offerings(ch, q)
	# S48 Core Forging: into Cloud Stride the core forms, and how it was prepared sets its purity grade.
	if str(q.from) == "heart_tempering_9": _core_checklist(ch, LEFT_STELE)
	btn(Rect2(THRESHOLD.get_center().x - 130, THRESHOLD.position.y - 2, 260, 60), Tx.t("ui.breakthrough.break_through"), "go", null, true, bool(q.can) and _doors_at < 0.0, str(q.blocked))

## Each requirement a tablet hung from the beam on two red cords: gold-leafed when met, dark with its Go when not. A minor
## step hangs one tablet that says so.
func _tablets(q: Dictionary, top: float) -> void:
	var results: Array = q.get("results", [])
	var r := Rect2(TABLETS.position.x, top, TABLETS.size.x, TABLETS.end.y - top)
	var above := BEAM.end.y
	if not q.major:
		var tr := Rect2(r.position.x, r.position.y, r.size.x, 96)
		for x in [tr.position.x + 30, tr.end.x - 30]: WayKit.cord(self, Vector2(x, above), Vector2(x, tr.position.y + 4))
		WayKit.tablet(self, tr, true)
		para(Rect2(tr.position.x + 16, tr.position.y + 12, tr.size.x - 32, tr.size.y - 16), Tx.t("ui.breakthrough.a_minor_step_within_the"), 16, UiKit.PAPER, 4)
		return
	var n := maxi(1, results.size())
	var h := clampf(floorf((r.size.y - 6.0 * (n - 1)) / n), 48.0, 64.0)
	var y := r.position.y
	for res in results:
		var ok: bool = res.ok
		var tr := Rect2(r.position.x, y, r.size.x, h)
		for x in [tr.position.x + 30, tr.end.x - 30]: WayKit.cord(self, Vector2(x, above), Vector2(x, tr.position.y + 4))
		above = tr.end.y - 4
		WayKit.tablet(self, tr, ok)
		draw_circle(Vector2(tr.position.x + 18, tr.get_center().y), 8.0, UiKit.INK, true, -1.0, true)
		draw_circle(Vector2(tr.position.x + 18, tr.get_center().y), 6.5, UiKit.JADE if ok else (UiKit.RED if res.hard else UiKit.WARNING), true, -1.0, true)
		if ok: draw_polyline(PackedVector2Array([Vector2(tr.position.x + 14, tr.get_center().y), Vector2(tr.position.x + 17, tr.get_center().y + 3), Vector2(tr.position.x + 23, tr.get_center().y - 4)]), UiKit.INK, 2.0, true)
		var fix := str(res.get("fix", ""))
		var go := not ok and fix.begins_with("page:")
		var tw := tr.size.x - 44.0 - (88.0 if go else 12.0)
		var lines := 2 if h >= 56.0 else 1
		var used := para(Rect2(tr.position.x + 34, tr.position.y + 8, tw, h - 12), str(res.text), 16, UiKit.PAPER if ok else UiKit.PALE_GOLD, lines)
		if h >= 56.0 and used < 30.0:
			text(Vector2(tr.position.x + 34, tr.position.y + 8 + used + 14), (Tx.t("ui.breakthrough.required") if res.hard else Tx.t("ui.breakthrough.soft_raises_risk_if_unmet")) + " · " + str(res.cause).capitalize(),
				14, UiKit.PAPER if ok else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, tw)
		if go: btn(Rect2(tr.end.x - 88, tr.get_center().y - 24, 76, 48), Tx.t("ui.breakthrough.go"), "fix", fix.trim_prefix("page:"), false, true, "", 18)
		y += h + 6.0

## The risk cut into the left pillar and the chance into the right, each on a gold-leafed plaque.
func _pillars(q: Dictionary) -> void:
	var risk := str(q.risk)
	var risk_col = {"none": UiKit.JADE, "low": UiKit.JADE, "moderate": UiKit.WARNING, "high": UiKit.RED, "severe": UiKit.RED}.get(risk, UiKit.HOLLOW)
	var pl: Rect2 = PILLARS[0]
	var pr: Rect2 = PILLARS[1]
	var a := Rect2(pl.position.x + 10, pl.position.y + 150, pl.size.x - 20, 104)
	var b := Rect2(pr.position.x + 10, pr.position.y + 150, pr.size.x - 20, 104)
	tour_mark("pillars", a)   # decision 43: the risk and the chance, a tour's anchor
	tour_mark("pillars", b)
	WayKit.tablet(self, a, true)
	WayKit.tablet(self, b, true)
	text(Vector2(a.position.x, a.position.y + 30), Tx.t("ui.breakthrough.risk_label"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, a.size.x)
	draw_circle(Vector2(a.get_center().x, a.position.y + 50), 7.0, UiKit.INK, true, -1.0, true)
	draw_circle(Vector2(a.get_center().x, a.position.y + 50), 5.5, risk_col, true, -1.0, true)
	text(Vector2(a.position.x + 4, a.position.y + 84), risk.capitalize(), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, a.size.x - 8)
	text(Vector2(b.position.x, b.position.y + 30), Tx.t("ui.breakthrough.chance_label"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, b.size.x)
	text(Vector2(b.position.x, b.position.y + 80), "%d%%" % int(float(q.success) * 100), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, b.size.x, true)

## The three jade offering dishes on the step: each holds a chosen support (a tap takes it back), or waits empty.
func _dishes(ch) -> void:
	for i in 3:
		var sr := Rect2(OPENING.get_center().x - 138 + i * 100, DISH_Y, SLOT, SLOT)
		var foot := Vector2(sr.get_center().x, sr.end.y + 4)
		draw_set_transform(foot, 0.0, Vector2(1.0, 0.28))
		draw_circle(Vector2.ZERO, 50.0, UiKit.INK, true, -1.0, true)
		draw_circle(Vector2.ZERO, 47.0, UiKit.BRIGHT_JADE, true, -1.0, true)
		draw_circle(Vector2.ZERO, 42.0, UiKit.JADE_SHADOW, true, -1.0, true)
		draw_set_transform(Vector2.ZERO)
		if i < supports.size(): slot_box(sr, str(supports[i]), ch.inventory.count(str(supports[i])), "", "support", str(supports[i]), true)

## The stele at the right: the supports carried (a tap lays one in a dish, up to three) and what weighs on the attempt.
func _offerings(ch, q: Dictionary) -> void:
	var r := RIGHT_STELE
	WayKit.tablet(self, r, false)
	var x := r.position.x + 12
	text(Vector2(x, r.position.y + 32), Tx.t("ui.breakthrough.support"), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24)
	var y := r.position.y + 42.0
	y += para(Rect2(x, y, r.size.x - 24, 60), Tx.t("ui.breakthrough.offer_hint"), 14, UiKit.MIST, 3) + 6
	var cands := support_candidates(ch)
	if cands.is_empty():
		text(Vector2(x, y + 20), Tx.t("ui.breakthrough.no_support_items"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24)
		y += 36
	for i in mini(cands.size(), 6):
		var r2 := Rect2(x + (i % 3) * (SLOT + 6), y + (i / 3) * (SLOT + 6), SLOT, SLOT)
		slot_box(r2, str(cands[i]), ch.inventory.count(str(cands[i])), "", "support", str(cands[i]), supports.has(cands[i]))
	if not cands.is_empty(): y += (SLOT + 6) * ceili(minf(cands.size(), 6) / 3.0) + 6
	for reason in q.get("reasons", []):
		if y + 20 > r.end.y - 10: break
		y += para(Rect2(x, y, r.size.x - 24, r.end.y - 10 - y), "· " + str(reason), 14, UiKit.PAPER, 2)

func _core_checklist(ch, r: Rect2) -> void:
	WayKit.tablet(self, r, false)
	r = r.grow(-14)
	var pts: Array = Game.progression.core_forging_points(ch)
	var met := 0
	for pt in pts:
		if pt.met: met += 1
	var flawless: bool = ch.quests.has_flag("cleansing_flawless")
	var best := ProgressionRules.core_grade(met, flawless)
	var head := para(Rect2(r.position.x, r.position.y + 4, r.size.x, 60), Tx.t("ui.breakthrough.core_forging") % best, 18, UiKit.PALE_GOLD, 3)
	var y := r.position.y + head + 14
	var step := minf(44.0, (r.end.y - y) / float(pts.size() + (1 if flawless else 0)))
	for pt in pts:
		var ok: bool = pt.met
		draw_circle(Vector2(r.position.x + 8, y + 12), 6, UiKit.JADE if ok else Color(UiKit.MIST, 0.35))
		para(Rect2(r.position.x + 22, y, r.size.x - 24, step), Tx.t("ui.breakthrough.core." + str(pt.id)), 14, UiKit.PAPER if ok else UiKit.MIST, 2)
		y += step
	if flawless: para(Rect2(r.position.x + 22, y, r.size.x - 24, step), Tx.t("ui.breakthrough.core.flawless"), 14, UiKit.PALE_GOLD, 2)

func on_action(id: String, data) -> void:
	if _doors_at >= 0.0: return   # the doors are opening
	match id:
		"support":
			if supports.has(data): supports.erase(data)
			elif supports.size() < 3: supports.append(data)
		"fix": navigate.emit(str(data), {})
		"go":
			var r := submit({"type": "start_breakthrough", "support_items": supports})
			if r.get("ok", false): _doors_at = t
