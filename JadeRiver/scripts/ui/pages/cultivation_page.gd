extends Page
## Cultivation (S04–S10, Part 9.6): Overview with the realm, progress, stability and
## bottleneck; Foundation (body and meridians); Heart (what the past costs: heart demons, karma,
## a hollow foundation, residue and pill resistance, gap report G1); Methods; Dao; Seclusion.

## P5 (docs/page_identity.md row 5, the way family; mockup 04_cultivation_ascent): the mountain ascent. The Overview
## is the night mountain of the great realms at the left, the stair of this realm's steps in the middle with the figure
## seated on the step it has reached and the gate at the top, and this step, the next and the gate's asks at the right.
## The shared window, plaque and tabs stay, as the approved mockup keeps them; the other tabs keep their panels on it.
const Avatar = preload("res://scripts/avatar.gd")
const MOUNTAIN := Rect2(96, 168, 312, 496)
const STAIR := Rect2(424, 168, 376, 496)
const RIGHT := Rect2(816, 168, 368, 496)
const STAIR_FOOT := 626.0
const CLIMB_S := 0.3   # a step climbed while the page is open (page_identity §6: a change's motion, 0.3 s at most)

var doll: Node2D           # the figure seated on its step
const TOP_SCALE := 2      # decision 42: a top-down character's seated figure (TopdownDoll), screen px an art px
var _seen_realm := ""      # the step the figure sat on at the last draw
var _climb := {}           # {from: step index, at: page clock} while the figure climbs

func _init() -> void:
	title = Tx.t("ui.cultivation.cultivation")
	identity = Identity.new("space", true, "plaque", "realm_path_nine_step_stair_gate", 0.3)

## The shared window stays round the page (mockup 04); its face is the ground under the words set on it.
func draw_surface(r: Rect2) -> void:
	face(r, "major_window")

func setup() -> void:
	var ch = c()
	tabs = [{"id": "overview", "label": Tx.t("ui.cultivation.overview")},
		{"id": "foundation", "label": Tx.t("ui.cultivation.foundation"), "locked": "" if Unlocks.is_unlocked(ch.id, "foundation") else Unlocks.locked_text("foundation")},
		{"id": "body", "label": Tx.t("ui.cultivation.body_tab")},
		{"id": "heart", "label": Tx.t("ui.cultivation.heart")},
		{"id": "vows", "label": Tx.t("ui.cultivation.paths"), "locked": "" if Unlocks.is_unlocked(ch.id, "vows") else Unlocks.locked_text("vows")},
		{"id": "methods", "label": Tx.t("ui.cultivation.methods")},
		{"id": "dao", "label": Tx.t("ui.cultivation.dao"), "locked": "" if Unlocks.is_unlocked(ch.id, "dao_tree") else Unlocks.locked_text("dao_tree")},
		{"id": "seclusion", "label": Tx.t("ui.cultivation.seclusion"), "locked": "" if Unlocks.is_unlocked(ch.id, "seclusion") else Unlocks.locked_text("seclusion")}]
	if doll == null:
		# Decision 42: the character as its game draws it, seated in meditation facing the camera: the top-down figure for
		# a top-down character, the side view's for a classic one.
		doll = TopdownDoll.new() if TopdownDoll.shown(ch) else Avatar.new()
		doll.visible = false
		add_child(doll)
	TopdownDoll.dress(doll, InventoryAuthority.outfit_for(ch))
	doll.play("meditate")
	if page_id == "seclusion" and Unlocks.is_unlocked(ch.id, "seclusion"): tab = 7
	if page_id == "heart": tab = 3
	if page_id == "body": tab = 2

func on_event(name: String, _p: Dictionary) -> void:
	if name == "equipment_changed" and doll != null and c() != null:
		TopdownDoll.dress(doll, InventoryAuthority.outfit_for(c()))
	queue_redraw()

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	match str(tabs[tab].id):
		"overview": _overview(ch)
		"foundation": _foundation(ch)
		"body": _body(ch)
		"heart": _heart(ch)
		"vows": _vows(ch)
		"methods": _methods(ch)
		"dao": _dao(ch)
		"seclusion": _seclusion(ch)

func _overview(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	# Decision 43: a tour's anchors.
	tour_mark("mountain", MOUNTAIN)
	tour_mark("stair", STAIR)
	tour_mark("next", RIGHT)
	var steps := _steps(cu.realm_key)
	var here := steps.find(cu.realm_key)
	# A step climbed while the page is open: the figure climbs from the one it sat on (none under Reduce motion).
	if _seen_realm != "" and _seen_realm != cu.realm_key and steps.has(_seen_realm) and not UiKit.reduce_motion():
		_climb = {"from": steps.find(_seen_realm), "at": t}
	_seen_realm = cu.realm_key
	var cur := _mountain(ch)
	var top := _stair(ch, steps, here)
	# The leader from this realm on the mountain to its stair.
	var a := Vector2(MOUNTAIN.end.x - 64, cur.y + 16)
	var b: Vector2 = top
	var pts := PackedVector2Array()
	for i in 13:
		var k := float(i) / 12.0
		pts.append(a.bezier_interpolate(Vector2(a.x + 44, a.y), Vector2(b.x - 36, b.y), b, k))
	for i in 12:
		if i % 2 == 0: draw_line(pts[i], pts[i + 1], Color(UiKit.PALE_GOLD, 0.6), 2.0, true)
	_stage(ch, steps, here)

## The great realms in ladder order, each once.
static func great_realms() -> Array:
	var out: Array = []
	for k in ContentDB.realm_order:
		var g := ProgressionRules.great_realm(str(k))
		if not out.has(g): out.append(g)
	return out

## The steps of the great realm `key` belongs to, in order (nine, three or one).
static func _steps(key: String) -> Array:
	var g := ProgressionRules.great_realm(key)
	return ContentDB.realm_order.filter(func(k): return ProgressionRules.great_realm(str(k)) == g)

## Early, middle, late or peak: where step `i` of `n` stands in its realm (the last is the peak).
static func band_of(i: int, n: int) -> String:
	if i >= n - 1: return "peak"
	var f := float(i) / float(n)
	return "early" if f < 1.0 / 3.0 - 0.001 else ("middle" if f < 2.0 / 3.0 - 0.001 else "late")

## A band's faces: the lit lip, the riser and its foot.
static func band_faces(band: String) -> Array:
	match band:
		"early": return [UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.5), UiKit.JADE_SHADOW, UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.45)]
		"middle": return [UiKit.BRIGHT_JADE.lerp(UiKit.JADE, 0.4), UiKit.JADE.lerp(UiKit.INK, 0.3), UiKit.JADE.lerp(UiKit.INK, 0.6)]
		"late": return [UiKit.BRONZE.lerp(UiKit.GOLD, 0.4), UiKit.BRONZE.lerp(UiKit.INK, 0.3), UiKit.BRONZE.lerp(UiKit.INK, 0.6)]
	return [UiKit.PALE_GOLD, UiKit.GOLD.lerp(UiKit.INK, 0.3), UiKit.GOLD.lerp(UiKit.INK, 0.6)]

## A band's word on its chip, in the band's colour.
func _band_chip(r: Rect2, band: String, label: String) -> void:
	var fill: Color = {"early": UiKit.JADE_SHADOW, "middle": UiKit.JADE.lerp(UiKit.INK, 0.35), "late": UiKit.BRONZE.lerp(UiKit.INK, 0.45)}.get(band, UiKit.GOLD.lerp(UiKit.INK, 0.55))
	rounded(r, r.size.y * 0.5, band_faces(band)[0])
	rounded(r.grow(-1.5), r.size.y * 0.5 - 1.5, fill)
	ground(r, fill)
	text(Vector2(r.position.x, r.position.y + r.size.y * 0.5 + 5), label, 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

## The systems that open at step `key` and are not open yet (unlocks.json: realm_at_least that step).
static func opens_at(ch, key: String) -> Array:
	var out: Array = []
	for u in ContentDB.all("unlocks"):
		if Unlocks.is_unlocked(ch.id, str(u.id)): continue
		for cond in u.get("trigger", {}).get("all", []):
			if str(cond.get("kind", "")) == "realm_at_least" and str(cond.get("realm", "")) == key: out.append(str(u.get("label", u.id)))
	return out

## The mountain of the great realms: all of them as waystations on one path winding up from Mortal, those passed ticked in
## gold, this one lit, the next two named (the next with what it opens), the far ones fading into the mist near the top.
## Returns where this realm's waystation stands.
func _mountain(ch) -> Vector2:
	var r := MOUNTAIN
	var mist_h := 150.0
	var lit := UiKit.RIVER_NIGHT.lerp(UiKit.MIST, 0.06)
	rounded(r, 4.0, UiKit.RIVER_NIGHT)
	vshade(Rect2(r.position.x + 1, r.position.y + mist_h, r.size.x - 2, r.size.y - mist_h - 1), UiKit.RIVER_NIGHT, UiKit.SURFACE.space.lerp(UiKit.INK, 0.35))
	ground(r, UiKit.RIVER_NIGHT)
	var o := r.position
	draw_colored_polygon(PackedVector2Array([o + Vector2(0, 492), o + Vector2(58, 348), o + Vector2(26, 258), o + Vector2(84, 158), o + Vector2(58, 88), o + Vector2(98, 18),
		o + Vector2(136, 90), o + Vector2(122, 168), o + Vector2(170, 248), o + Vector2(152, 328), o + Vector2(208, 388), o + Vector2(312, 492)]), Color(UiKit.JADE_SHADOW, 0.28))
	draw_colored_polygon(PackedVector2Array([o + Vector2(118, 492), o + Vector2(168, 388), o + Vector2(238, 348), o + Vector2(312, 298), o + Vector2(312, 492)]),
		Color(UiKit.DEEP_TEAL, 0.55))
	WayKit.stars(self, Rect2(r.position, Vector2(r.size.x, mist_h)), 24)
	vshade(Rect2(r.position.x + 1, r.position.y + 1, r.size.x - 2, mist_h), Color(UiKit.MIST, 0.06), Color(UiKit.MIST, 0.0))
	ground(Rect2(r.position, Vector2(r.size.x, mist_h)), lit)
	draw_rect(r, Color(UiKit.BRONZE, 0.45), false, 1.0)
	var realms := great_realms()
	var ci := realms.find(ProgressionRules.great_realm(ch.cultivator.realm_key))
	var gaps: Array = [0.0]
	var total := 0.0
	for i in range(1, realms.size()):
		var w := 1.0 if i <= ci + 2 else 0.55
		total += w
		gaps.append(total)
	var foot := r.end.y - 28.0
	var unit := (foot - r.position.y - 30.0) / maxf(1.0, total)
	var at: Array = []
	for i in realms.size():
		var amp := 46.0 if i <= ci + 2 else 22.0
		at.append(Vector2(r.position.x + 96.0 + amp * sin(i * 0.9 + 0.3), foot - float(gaps[i]) * unit))
	for i in realms.size() - 1:
		draw_dashed_line(at[i], at[i + 1], Color(UiKit.BRONZE, 0.75), 3.0, 6.0, true, true)
	var next_open: Array = []
	if ci + 1 < realms.size():
		var first: Array = ContentDB.realm_order.filter(func(k): return ProgressionRules.great_realm(str(k)) == str(realms[ci + 1]))
		if not first.is_empty(): next_open = opens_at(ch, str(first[0]))
	for i in realms.size():
		var p: Vector2 = at[i]
		var name := ContentDB.text("realm_great." + str(realms[i]))
		var room := r.end.x - p.x - 24.0
		if i == ci:
			glow(Rect2(p - Vector2(24, 24), Vector2(48, 48)), Color(UiKit.GOLD, 0.55 * _halo()))
			draw_circle(p, 13.0, UiKit.INK, true, -1.0, true)
			draw_circle(p, 11.0, UiKit.PALE_GOLD, true, -1.0, true)
			draw_circle(p, 8.5, UiKit.GOLD, true, -1.0, true)
			text(Vector2(p.x + 20, p.y + 7), name, 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, room - 4, true)
			continue
		var done := i < ci
		var near := i > ci and i <= ci + 2
		var veil := i > ci + 8
		var rad := 6.0 if done or near else (5.0 if not veil else 4.0)
		draw_circle(p, rad + 2.0, UiKit.INK, true, -1.0, true)
		draw_circle(p, rad + 1.0, UiKit.BRONZE if done else (UiKit.JADE if near else UiKit.JADE_SHADOW), true, -1.0, true)
		draw_circle(p, rad - 0.5, UiKit.GOLD if done else UiKit.DEEP_TEAL, true, -1.0, true)
		var size := 16 if done or near else 14
		var col := UiKit.PAPER if done or near else (UiKit.MIST if not veil else UiKit.HOLLOW)
		text(Vector2(p.x + 16, p.y + 5), name, size, col, HORIZONTAL_ALIGNMENT_LEFT, room - (18.0 if done else 0.0))
		var w := UiKit.text_width(fit(name, size, room), size)
		if done:   # a gold tick after the name
			var q := Vector2(p.x + 22 + w, p.y)
			draw_polyline(PackedVector2Array([q + Vector2(0, 0), q + Vector2(4, 4), q + Vector2(11, -5)]), UiKit.GOLD, 2.0, true)
		elif i == ci + 1 and not next_open.is_empty() and room - w > 60.0:
			text(Vector2(p.x + 22 + w, p.y + 5), "· " + ", ".join(next_open.slice(0, 2)), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, room - w - 8.0)
	return at[maxi(0, ci)]

## The stair of this great realm: its steps rising left to right in the band colours, the steps climbed lipped in gold,
## the one reached lit with its bar inside it and the figure seated on it; the riser to the next step glows at a
## bottleneck; what a later step opens is a gold mark on it; the gate to the next great realm stands on the last.
## Returns the reached step's top left, where the mountain's leader arrives.
func _stair(ch, steps: Array, here: int) -> Vector2:
	var cu: CultivatorState = ch.cultivator
	var n := steps.size()
	var realms := great_realms()
	var gr := ProgressionRules.great_realm(cu.realm_key)
	text(Vector2(STAIR.position.x + 6, STAIR.position.y + 40), ContentDB.text("realm_great." + gr), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, STAIR.size.x - 12, true)
	text(Vector2(STAIR.position.x + 8, STAIR.position.y + 66), Tx.t("ui.cultivation.great_realm_of") % [realms.find(gr) + 1, realms.size(), Tx.plural("ui.cultivation.realm_steps", n) % n],
		14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, STAIR.size.x - 12)
	var sw := minf(360.0 / float(n), 100.0)
	var x0 := STAIR.position.x + 6.0
	var rise := 304.0 / float(maxi(1, n - 1))
	var rects: Array = []
	for i in n:
		var h := 28.0 + rise * i if n > 1 else 160.0
		rects.append(Rect2(x0 + i * sw, STAIR_FOOT - h, sw, h))
	# The steps rise into place as the page opens.
	var lift := (1.0 - unfold()) * 24.0
	move(Vector2(0, lift))
	for i in n:
		var sr: Rect2 = rects[i]
		var f: Array = band_faces(band_of(i, n))
		vshade(Rect2(sr.position, Vector2(sr.size.x, 9)), f[0], f[0])
		vshade(Rect2(sr.position.x, sr.position.y + 9, sr.size.x, sr.size.y - 9), f[1], f[2])
		draw_rect(sr, UiKit.INK, false, 1.0)
		if i < here: draw_rect(Rect2(sr.position, Vector2(sr.size.x, 3)), UiKit.GOLD)
		elif i == here:
			var frac := cu.progress_fraction()
			draw_rect(Rect2(sr.position.x + 3, sr.end.y - 3 - (sr.size.y - 6) * frac, sr.size.x - 6, (sr.size.y - 6) * frac), Color(UiKit.BRIGHT_JADE, 0.4))
		else:
			draw_rect(sr, Color(UiKit.INK, 0.28))
		inked(Vector2(sr.position.x, sr.position.y + 30), str(i + 1), 16, UiKit.PALE_GOLD if i == here else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, sr.size.x, false)
		if i > here + 1 and i < n - 1 and not opens_at(ch, str(steps[i])).is_empty():
			var m := Vector2(sr.get_center().x, sr.position.y - 12)
			draw_colored_polygon(PackedVector2Array([m + Vector2(0, -7), m + Vector2(7, 0), m + Vector2(0, 7), m + Vector2(-7, 0)]), UiKit.INK)
			draw_colored_polygon(PackedVector2Array([m + Vector2(0, -5), m + Vector2(5, 0), m + Vector2(0, 5), m + Vector2(-5, 0)]), UiKit.GOLD)
	if here >= 0:
		var cr: Rect2 = rects[here]
		glow(cr.grow(10), Color(UiKit.PALE_GOLD, 0.18 * _halo()))
		draw_rect(cr.grow(1), UiKit.PALE_GOLD, false, 2.0)
		# At a bottleneck the riser up to the next step glows.
		if cu.state == "bottleneck" and here + 1 < n:
			var nr: Rect2 = rects[here + 1]
			var riser := Rect2(nr.position.x - 2, nr.position.y, 4, cr.position.y - nr.position.y)
			glow(riser.grow(12), Color(UiKit.GOLD, 0.6 * _halo()))
			draw_rect(riser, UiKit.PALE_GOLD)
	_gate(ch, rects[n - 1], cu.state == "bottleneck" and here == n - 1)
	# The figure, seated on its step (climbing from the last one while it moves up); at the peak, before the gate.
	var feet := Vector2(rects[maxi(0, here)].get_center().x, rects[maxi(0, here)].position.y + 4)
	if not _climb.is_empty():
		var k := clampf((t - float(_climb.at)) / CLIMB_S, 0.0, 1.0)
		var fr: Rect2 = rects[clampi(int(_climb.from), 0, n - 1)]
		feet = Vector2(fr.get_center().x, fr.position.y + 4).lerp(feet, k) + Vector2(0, -10.0 * sin(k * PI))
		if k >= 1.0: _climb = {}
	move()
	if doll is TopdownDoll: doll.draw_on(self, feet + Vector2(0, lift - 24), TOP_SCALE)   # seated on the step's top
	elif doll != null: doll.draw_on(self, feet + Vector2(0, lift), 0.75)
	# The bands under the steps, each with its chip.
	var spans := {}
	for i in n:
		var bd := band_of(i, n)
		if not spans.has(bd): spans[bd] = [i, i]
		spans[bd][1] = i
	for bd in spans:
		var a: int = spans[bd][0]
		var b: int = spans[bd][1]
		var span := Rect2((rects[a] as Rect2).position.x + 2, STAIR_FOOT + 2, (rects[b] as Rect2).end.x - (rects[a] as Rect2).position.x - 4, 4)
		draw_rect(span, band_faces(bd)[0])
		var word := Tx.t("ui.cultivation.band_" + str(bd))
		var label := Tx.t("ui.cultivation.band_range") % [word, a + 1, b + 1] if b - a >= 2 else word
		var cw := maxf(UiKit.text_width(label, 14) + 18.0, 44.0)
		_band_chip(Rect2(span.get_center().x - cw * 0.5, STAIR_FOOT + 10, cw, 24), bd, label)
	return (rects[maxi(0, here)] as Rect2).position + Vector2(0, lift)

## The gate on the last step: two red posts under a jade roof with a gold beam, the next great realm's name above it; lit
## while the character waits at it.
func _gate(ch, top_step: Rect2, lit: bool) -> void:
	var next := ContentDB.next_realm(str(_steps(ch.cultivator.realm_key)[-1]))
	if next == "": return
	var cx := top_step.get_center().x
	var half := maxf(14.0, minf(top_step.size.x * 0.5 - 4.0, 40.0))
	var y := top_step.position.y
	if lit: glow(Rect2(cx - half - 30, y - 110, half * 2 + 60, 120), Color(UiKit.GOLD, 0.5 * _halo()))
	for sx in [-1.0, 1.0]:
		var post := Rect2(cx + sx * half - 3.0, y - 72, 6, 72)
		draw_rect(post.grow(1), UiKit.INK)
		hshade(post, UiKit.RED.lerp(UiKit.INK, 0.55), UiKit.RED.lerp(UiKit.INK, 0.2))
	var roof := Rect2(cx - half - 10, y - 86, half * 2 + 20, 10)
	rounded(roof.grow(1), 3.0, UiKit.INK)
	vshade(roof, UiKit.JADE.lerp(UiKit.JADE_SHADOW, 0.4), UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.2))
	draw_rect(Rect2(cx - half, y - 72, half * 2, 12), UiKit.INK)
	draw_rect(Rect2(cx - half + 1, y - 71, half * 2 - 2, 10), UiKit.GOLD)
	inked(Vector2(cx - 80, y - 96), ContentDB.text("realm_great." + ProgressionRules.great_realm(next)), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 160, false)

## The right column: this step (its Level, band, method and bar), what the past has left (body, toxicity, injuries),
## the next step and what it opens, and the gate's asks; Meditate and Break Through at its foot.
func _stage(ch, steps: Array, here: int) -> void:
	var cu: CultivatorState = ch.cultivator
	var x := RIGHT.position.x
	var w := RIGHT.size.x
	var y := RIGHT.position.y + 4
	face(Rect2(x, y, 62, 62), "realm_badge")
	text(Vector2(x, y + 43), str(ProgressionRules.level(ch)), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 62, true)
	text(Vector2(x + 76, y + 24), ContentDB.text("realm." + cu.realm_key), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w - 76, true)
	var bd := band_of(here, steps.size())
	var word := Tx.t("ui.cultivation.band_" + bd)
	var cw := UiKit.text_width(word, 14) + 18.0
	_band_chip(Rect2(x + 76, y + 36, cw, 24), bd, word)
	text(Vector2(x + 84 + cw, y + 54), Tx.t("ui.cultivation.level") % [ProgressionRules.level(ch), str(cu.state).capitalize()], 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w - 84 - cw)
	y += 86
	var method := ProgressionRules.method(cu.method_id)
	var mname := ContentDB.name_of("methods", cu.method_id) if cu.method_id != "" else Tx.t("ui.cultivation.none")
	if method.is_empty() and cu.realm_key == "mortal": mname = Tx.t("ui.cultivation.not_yet_learned")
	var energy := str(cu.energy_type).replace("_", " ").capitalize() if cu.energy_type != "none" else Tx.t("ui.cultivation.body_only")
	text(Vector2(x, y), " · ".join([mname, energy, Tx.t("ui.cultivation.stability_word") % str(cu.stability)]), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w)
	y += 10
	bar(Rect2(x, y, w, 36), cu.progress_fraction(), UiKit.GOLD if cu.state == "bottleneck" else UiKit.JADE, Tx.t("ui.cultivation.qp") % [UiKit.fmt(cu.qp), UiKit.fmt(cu.need())])
	y += 46
	if cu.stored_qi > 0.0 or Unlocks.is_unlocked(ch.id, "stored_qi"):
		y += rich(Rect2(x, y, w, 40), [[Tx.t("ui.cultivation.stored_qi") % [UiKit.fmt(cu.stored_qi), UiKit.fmt(ProgressionRules.stored_qi_cap(ch))], UiKit.QI],
			["· " + Tx.t("ui.cultivation.stored_banks"), UiKit.MIST]], 14) + 4
	# What the body and the past carry, in one ledger.
	var rows := [[Tx.t("ui.cultivation.body_level"), "%d (%d%%)" % [cu.body_level, int(100.0 * cu.body_xp / maxf(1.0, ProgressionRules.body_xp_needed(cu.body_level)))]],
		[Tx.t("ui.cultivation.toxicity"), "%d / %d" % [int(cu.toxicity), int(ch.stats.value("toxicity_tolerance"))]],
		[Tx.t("ui.cultivation.injuries"), Tx.t("ui.cultivation.none") if cu.injuries.is_empty() else ", ".join(cu.injuries.keys()).capitalize()]]
	if cu.energy_type == "true_qi": rows.append([Tx.t("ui.cultivation.purity"), Tx.t("ui.cultivation.grade") % cu.purity])
	# S28 v1.2: the Presence level and the experience toward the next (Will Manifest on).
	var pl: int = Game.field.presence_level(ch)
	if pl > 0:
		var pxp: Array = ContentDB.stat_const("presence.xp_levels", [0])
		rows.append([Tx.t("ui.cultivation.presence"), Tx.t("ui.cultivation.presence_level") % [pl, int(Game.field.presence_xp(ch)), int(pxp[pl])] if pl < pxp.size()
			else Tx.t("ui.cultivation.presence_max") % pl])
	y += para(Rect2(x, y, w, 40), " · ".join(rows.map(func(rw): return "%s %s" % [rw[0], rw[1]])), 14, UiKit.MIST, 2) + 16
	# The next step, and what the gate asks.
	var q: Dictionary = Game.progression.query_breakthrough(ch)
	heading(Vector2(x, y + 20), Tx.t("ui.cultivation.next") % ContentDB.name_of("realms", str(q.get("to", ""))), w)
	y += 34
	var foot := RIGHT.end.y - 64.0
	if not q.get("major", false):
		y += para(Rect2(x, y, w, 72), Tx.t("ui.cultivation.a_minor_step_fill_the"), 18, UiKit.PAPER, 3) + 6
		var opens := opens_at(ch, str(q.get("to", "")))
		var cx := x
		for i in opens.size():
			var label := str(opens[i])
			var more := opens.size() - i - 1
			var cwid := UiKit.text_width(label, 16) + 28.0
			if cx + cwid > x + w - (56.0 if more > 0 else 0.0):
				label = "+%d" % (opens.size() - i)
				cwid = UiKit.text_width(label, 16) + 28.0
				more = 0
			var chip := Rect2(cx, y, cwid, 36)
			rounded(chip, 10.0, UiKit.JADE)
			rounded(chip.grow(-1.5), 8.5, UiKit.DEEP_TEAL)
			ground(chip, UiKit.DEEP_TEAL)
			text(Vector2(chip.position.x, chip.position.y + 24), label, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, chip.size.x)
			cx += cwid + 8.0
			if label.begins_with("+"): break
		if not opens.is_empty(): y += 46
		# The gate at the top of this stair, and what it asks.
		var spec := ProgressionRules.breakthrough_spec(str(steps[-1]))
		var next := str(spec.get("to", ""))
		if not spec.is_empty() and next != "":
			text(Vector2(x, y + 16), Tx.t("ui.cultivation.gate_at") % [ContentDB.text("realm_great." + ProgressionRules.great_realm(next)), steps.size()], 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, w)
			y += 26
			for r in RequirementRules.check(spec.get("requirements", {}), Game.ctx(ch)):
				if y + 24 > foot: break
				_ask(Vector2(x, y), r, w)
				y += 26
	else:
		for r in q.get("results", []):
			if y + 24 > foot - 26: break
			_ask(Vector2(x, y), r, w)
			y += 26
		text(Vector2(x, foot - 8), Tx.t("ui.cultivation.risk_success") % [str(q.risk).capitalize(), int(float(q.success) * 100)], 18, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, w)
	var medit: bool = cu.meditating
	btn(Rect2(x, RIGHT.end.y - 56, 176, 56), Tx.t("ui.cultivation.stop") if medit else Tx.t("ui.cultivation.meditate"), "meditate", null, not medit, Unlocks.is_unlocked(ch.id, "cultivate"),
		Unlocks.locked_text("cultivate"))
	btn(Rect2(x + 188, RIGHT.end.y - 56, w - 188, 56), Tx.t("ui.cultivation.breakthrough"), "breakthrough", null, cu.state == "bottleneck",
		Unlocks.is_unlocked(ch.id, "breakthrough"), Unlocks.locked_text("breakthrough"))

## One ask of a breakthrough: a dot (jade met, red a hard need, amber a soft one) and its words, with why it matters.
func _ask(at: Vector2, r: Dictionary, w: float) -> void:
	var ok: bool = r.get("ok", false)
	var hard: bool = r.get("hard", false)
	draw_circle(at + Vector2(9, 11), 8.0, UiKit.INK, true, -1.0, true)
	draw_circle(at + Vector2(9, 11), 7.0, UiKit.JADE if ok else (UiKit.RED if hard else UiKit.WARNING), true, -1.0, true)
	var words := str(r.get("text", ""))
	text(at + Vector2(26, 17), words, 16, UiKit.PAPER if ok else UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w - 26)
	var used := UiKit.text_width(fit(words, 16, w - 26), 16)
	if w - 26 - used > 90.0:
		text(at + Vector2(34 + used, 17), "· " + (Tx.t("ui.cultivation.required") if hard else Tx.t("ui.cultivation.lowers_risk")), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w - 34 - used)

func _foundation(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	text(r.position + Vector2(24, 40), Tx.t("ui.cultivation.unspent_meridian_points") % cu.unspent_meridian_points, 22, UiKit.PALE_GOLD)
	tour_mark("points", Rect2(r.position + Vector2(16, 8), Vector2(420, 44)))   # decision 43: a tour's anchors
	tour_mark("bars", Rect2(r.position.x + 462, r.position.y + 70, 376, 5 * 64 - 16))
	var names := {"body": Tx.t("ui.cultivation.body"), "agility": Tx.t("ui.cultivation.agility"), "essence": Tx.t("ui.cultivation.essence"), "spirit": Tx.t("ui.cultivation.spirit"), "insight": Tx.t("ui.cultivation.insight")}
	var desc := {"body": Tx.t("ui.cultivation.hp_defence_body_training"), "agility": Tx.t("ui.cultivation.speed_evasion_accuracy"), "essence": Tx.t("ui.cultivation.qi_qi_attack"), "spirit": Tx.t("ui.cultivation.soul_sense_will"),
		"insight": Tx.t("ui.cultivation.insight_mastery_crafting")}
	var y := r.position.y + 70
	for k in names:
		var v := int(cu.meridians.get(k, 0))
		text(Vector2(r.position.x + 24, y + 30), names[k], 22, UiKit.PAPER)
		text(Vector2(r.position.x + 170, y + 30), str(desc[k]), 18, UiKit.MIST)
		bar(Rect2(r.position.x + 470, y + 8, 360, 30), v / 100.0, UiKit.JADE, "%d" % v)
		btn(Rect2(r.position.x + 850, y, 120, 48), "+1", "meridian", k, true, cu.unspent_meridian_points > 0, Tx.t("ui.cultivation.no_points_to_spend"))
		y += 64
	var free := not ProgressionRules.at_least(cu.realm_key, "qi_unfurling_1")
	btn(Rect2(r.position.x + 24, r.end.y - 70, 420, 52), Tx.t("ui.cultivation.reset_free") if free else Tx.t("ui.cultivation.reset_meridian_reversal_pill"), "reset_meridians")

## Body (S48): the body level and the four rungs of the ladder, each with its level, Temper trial and bath.
func _body(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := content
	panel(r)
	var x := r.position.x + 24
	var y := r.position.y + 20
	var here := ProgressionRules.body_tier_index(cu)
	text(Vector2(x, y + 30), Tx.t("ui.cultivation.mortal_body") if here == 0 else ContentDB.name_of("body_tiers", cu.body_tier), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 300, true)
	var need := ProgressionRules.body_xp_needed(cu.body_level)
	bar(Rect2(x + 320, y + 8, 440, 32), cu.body_xp / maxf(1.0, need), UiKit.JADE, Tx.t("ui.cultivation.body_level_bar") % [cu.body_level, int(100.0 * cu.body_xp / maxf(1.0, need))])
	tour_mark("body_level", Rect2(x - 8, y, 776, 48))   # decision 43: a tour's anchors
	tour_mark("hint", Rect2(x - 8, y + 48, r.size.x - 32, 48))
	tour_mark("rungs", Rect2(x - 8, y + 100, r.size.x - 32, r.end.y - y - 116))
	# B18: the hint wraps to a second line (one line lost "and a full soak in its bath.").
	y += 52 + para(Rect2(x, y + 46, r.size.x - 48, 44), Tx.t("ui.cultivation.body_hint"), 16, UiKit.MIST, 2)
	var tiers := ContentDB.all("body_tiers")
	var gap := 14.0
	var cw := (r.size.x - 48 - gap * (tiers.size() - 1)) / float(tiers.size())
	for i in tiers.size():
		var t: Dictionary = tiers[i]
		var cr := Rect2(x + i * (cw + gap), y, cw, r.end.y - y - 20)
		var reached := i < here
		# P4 (§6): the rung you climb now is a mark, not a selection: the normal panel, its name in pale gold and a gold ◆.
		panel(cr, "minor_panel", "normal" if reached or i == here else "disabled")
		var cx := cr.position.x + 16
		var cy := cr.position.y + 36
		text(Vector2(cx, cy), str(t.get("name", "")), 22, UiKit.PALE_GOLD if reached or i == here else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, cw - 110, true)
		if reached: text(Vector2(cr.end.x - 106, cy - 2), Tx.t("ui.cultivation.reached"), 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, 90)
		elif i == here: text(Vector2(cr.end.x - 106, cy - 2), "◆ " + Tx.t("ui.cultivation.next_rung"), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 90)
		cy += 22
		var checks := [[Tx.t("ui.cultivation.body_need_level") % int(t.need), cu.body_level >= int(t.need)],
			[Tx.t("ui.cultivation.body_need_trial"), str(t.id) in cu.body_trials],
			[ContentDB.item_name(str(t.bath)), str(t.id) in cu.body_baths]]
		for chk in checks:
			var done: bool = reached or chk[1]
			draw_circle(Vector2(cx + 7, cy + 12), 7, UiKit.JADE if done else Color(UiKit.MIST, 0.35))
			text(Vector2(cx + 22, cy + 18), str(chk[0]), 16, UiKit.PAPER if done else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, cw - 46)
			cy += 26
		cy += 6
		cy += para(Rect2(cx, cy, cw - 32, 120), str(t.get("trial_text", "")), 16, UiKit.MIST, 6) + 8   # B18: six lines (the Jade Body trial was cut at five)
		para(Rect2(cx, cy, cw - 32, cr.end.y - cy - 10), str(t.get("gift_text", "")), 16, UiKit.BRIGHT_JADE if reached else UiKit.PAPER, 4)

## Vows (S48): each forbids one thing while held and gives a steady gift; letting one go breaks it.
func _vows(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := content
	panel(r)
	var intro := para(Rect2(r.position.x + 24, r.position.y + 14, r.size.x - 48, 50), Tx.t("ui.cultivation.vows_intro") % int(ContentDB.config("vows").get("break_heart_demon", 15)), 18, UiKit.MIST, 2)
	var vows := ContentDB.all("vows")
	# B17: the path cards take the room the intro leaves, tall enough for five lines of description.
	var cards_y := r.position.y + 22 + intro
	_path_cards(ch, Rect2(r.position.x + 20, cards_y, r.size.x - 40, 196))
	tour_mark("paths", Rect2(r.position.x + 20, cards_y, r.size.x - 40, 196))   # decision 43: a tour's anchor
	var top := cards_y + 206
	var h := (r.end.y - top - 12) / float(maxi(1, vows.size()))
	for i in vows.size():
		var v: Dictionary = vows[i]
		var held := str(v.id) in cu.vows
		var vr := Rect2(r.position.x + 20, top + i * h, r.size.x - 40, h - ROW_GAP)   # rows 48 tall, as their buttons
		panel(vr, "minor_panel", "selected" if held else "normal")
		var mid := vr.size.y * 0.5
		text(vr.position + Vector2(18, mid + 8), str(v.get("name", "")), 22, UiKit.PALE_GOLD if held else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 200, true)
		text(vr.position + Vector2(230, mid - 5), str(v.get("desc", "")), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, vr.size.x - 440)
		text(vr.position + Vector2(230, mid + 16), str(v.get("gift_text", "")), 16, UiKit.BRIGHT_JADE if held else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, vr.size.x - 440)
		if held:
			btn(Rect2(vr.end.x - 190, vr.position.y + (vr.size.y - 48) * 0.5, 172, 48), Tx.t("ui.cultivation.break_vow"), "vow_off", str(v.id), false, true, "", 18)
		else:
			btn(Rect2(vr.end.x - 190, vr.position.y + (vr.size.y - 48) * 0.5, 172, 48), Tx.t("ui.cultivation.take_vow"), "vow_on", str(v.id), true, true, "", 18)

## S48 paths as layers: the Blood path (opt-in), the Buddhist path (vows, merit, the Golden Body) and the Poison Body.
func _path_cards(ch, area: Rect2) -> void:
	# v1.2: a fourth card, the Confucian path, once the lanternwright has shown it.
	var n := 4 if Unlocks.is_unlocked(ch.id, "confucian_path") else 3
	var w := (area.size.x - 12.0 * (n - 1)) / float(n)
	var cards: Array = []
	for i in n: cards.append(Rect2(area.position + Vector2((w + 12) * i, 0), Vector2(w, area.size.y)))
	var walking := ProgressionAuthority.walks(ch, "blood")
	panel(cards[0], "minor_panel", "selected" if walking else "normal")
	text(cards[0].position + Vector2(16, 30), Tx.t("ui.cultivation.blood_path"), 20, UiKit.RED_TEXT if walking else UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	para(Rect2(cards[0].position + Vector2(16, 40), Vector2(w - 32, 92)), Tx.t("ui.cultivation.blood_path_desc"), 14, UiKit.MIST, 5)
	if walking:
		text(cards[0].position + Vector2(16, 140), Tx.t("ui.cultivation.blood_on") % [int(round(Game.combat.blood_lifesteal(ch) * 100.0)), int(Game.combat.essence_of(ch.id))], 16, UiKit.PAPER,
			HORIZONTAL_ALIGNMENT_LEFT, w - 32)
		btn(Rect2(cards[0].end.x - 142, cards[0].end.y - 52, 128, 48), Tx.t("ui.cultivation.leave_blood"), "path_leave", "blood", false, true, "", 16)
	else:
		var cfg: Dictionary = ContentDB.stat_const("paths", {}).get("blood", {})
		var why := ""
		if ProgressionRules.realm_index(ch.cultivator.realm_key) < ProgressionRules.realm_index(str(cfg.get("min_realm", "heart_tempering_1"))): why = Tx.t("sim.progression.path_realm")
		elif ch.relations.alignment > int(cfg.get("alignment_at_most", -20)): why = Tx.t("sim.progression.path_alignment")
		btn(Rect2(cards[0].end.x - 142, cards[0].end.y - 52, 128, 48), Tx.t("ui.cultivation.walk_blood"), "path_take", "blood", true, why == "", why, 16)
	var bud: Dictionary = ContentDB.stat_const("paths", {}).get("buddhist", {})
	var step := int(bud.get("merit_milestone", 100))
	panel(cards[1], "minor_panel", "selected" if not ch.cultivator.vows.is_empty() else "normal")
	text(cards[1].position + Vector2(16, 30), Tx.t("ui.cultivation.golden_body"), 20, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	para(Rect2(cards[1].position + Vector2(16, 40), Vector2(w - 32, 92)), Tx.t("ui.cultivation.golden_body_desc"), 14, UiKit.MIST, 5)
	# B17: the merit line keeps to its card (it ran on under the Poison Body card).
	para(Rect2(cards[1].position + Vector2(16, 134), Vector2(w - 32, 60)), Tx.t("ui.cultivation.merit_line") % [ch.relations.merit, (int(ch.relations.merit / step) + 1) * step, ch.cultivator.vows.size()], 16, UiKit.PAPER, 3)
	var open: bool = Game.combat.poison_body_active(ch)
	var has_art := ProgressionRules.knows_poison_art(ch)
	var tol: float = ch.stats.value("toxicity_tolerance")
	panel(cards[2], "minor_panel", "selected" if open else "normal")
	text(cards[2].position + Vector2(16, 30), Tx.t("ui.cultivation.poison_body"), 20, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	para(Rect2(cards[2].position + Vector2(16, 40), Vector2(w - 32, 92)), Tx.t("ui.cultivation.poison_body_desc"), 14, UiKit.MIST, 5)
	var pline := Tx.t("ui.cultivation.poison_no_art")
	if has_art: pline = Tx.t("ui.cultivation.poison_open") % [int(ch.cultivator.toxicity), int(tol)] if open else Tx.t("ui.cultivation.poison_closed") % [int(ch.cultivator.toxicity), int(tol * 0.5)]
	para(Rect2(cards[2].position + Vector2(16, 134), Vector2(w - 32, 60)), pline, 16, UiKit.PAPER, 3)
	if n < 4: return
	var upright := ProgressionAuthority.walks(ch, "confucian")
	var cc: Dictionary = ContentDB.stat_const("paths", {}).get("confucian", {})
	panel(cards[3], "minor_panel", "selected" if upright else "normal")
	text(cards[3].position + Vector2(16, 30), Tx.t("ui.cultivation.confucian_path"), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	para(Rect2(cards[3].position + Vector2(16, 40), Vector2(w - 32, 92)), Tx.t("ui.cultivation.confucian_desc") % int(round(float(cc.get("righteous", 0.25)) * 100.0)), 14, UiKit.MIST, 5)
	if upright:
		btn(Rect2(cards[3].end.x - 142, cards[3].end.y - 52, 128, 48), Tx.t("ui.cultivation.leave_path"), "path_leave", "confucian", false, true, "", 16)
	else:
		var why2 := ""
		if ProgressionRules.realm_index(ch.cultivator.realm_key) < ProgressionRules.realm_index(str(cc.get("min_realm", "will_manifest_2"))): why2 = Tx.t("sim.progression.path_realm")
		elif ch.relations.alignment < int(cc.get("alignment_at_least", 20)): why2 = Tx.t("sim.progression.path_upright")
		elif walking: why2 = Tx.t("sim.progression.path_exclusive")
		btn(Rect2(cards[3].end.x - 142, cards[3].end.y - 52, 128, 48), Tx.t("ui.cultivation.walk_confucian"), "path_take", "confucian", true, why2 == "", why2, 16)

## Heart (G1): the meter, the ledger, the foundation and what the pills have left behind.
func _heart(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var left := Rect2(content.position.x, content.position.y, 540, content.size.y)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(left)
	panel(right)
	tour_mark("heart_panel", left)   # decision 43: a tour's anchor
	var x := left.position.x + 24
	var y := left.position.y + 44
	heading(Vector2(x, y), Tx.t("ui.cultivation.heart_demons"), left.size.x - 48)
	y += 26
	var hb := Rect2(x, y, left.size.x - 48, 30)
	# Red once it adds a risk step at great breakthroughs (25 and more, S48); a dull rose below that.
	bar(hb, cu.heart_demon / 100.0, UiKit.BLOOD if ProgressionRules.heart_demon_steps(cu) > 0 else Color(UiKit.BLOOD, 0.45), "%d / 100" % int(cu.heart_demon))
	for k in [25, 50, 75]:
		var tx: float = hb.position.x + hb.size.x * float(k) / 100.0
		draw_line(Vector2(tx, hb.position.y - 4), Vector2(tx, hb.end.y + 4), Color(UiKit.PALE_GOLD, 0.7), 2)
	y += 62
	var steps := ProgressionRules.heart_demon_steps(cu)
	para(Rect2(x, y - 20, left.size.x - 48, 70), Tx.t("ui.cultivation.heart_demon_steps") % steps if steps > 0 else Tx.t("ui.cultivation.heart_calm"), 18,
		UiKit.RED_TEXT if steps > 0 else UiKit.MIST, 3)
	y += 70
	# The karma ledger belongs to Relations (S49); the Heart shows what it does to a breakthrough, and links there.
	heading(Vector2(x, y), Tx.t("ui.cultivation.karma"), left.size.x - 48)
	btn(Rect2(left.end.x - 24 - 150, y - 34, 150, 48), Tx.t("ui.cultivation.ledger"), "relations", null, false, true, "", 16)
	y += 40
	var rel: RelationsState = ch.relations
	text(Vector2(x, y), Tx.t("ui.cultivation.merit") % rel.merit, 22, UiKit.PALE_GOLD)
	text(Vector2(x + 250, y), Tx.t("ui.cultivation.sin") % rel.sin, 22, UiKit.RED_TEXT)
	y += 28
	var merit_ready := ProgressionRules.merit_step(ch) > 0
	text(Vector2(x, y), Tx.t("ui.cultivation.merit_ready") if merit_ready else Tx.t("ui.cultivation.merit_not_ready") % int(Game.relations.cfg().get("merit_step", 100)),
		16, UiKit.BRIGHT_JADE if merit_ready else UiKit.MIST)
	y += 34
	# S48 fates: the cards chosen at major breakthroughs, and one waiting to be chosen.
	if not cu.fates.is_empty() or not cu.fate_offer.is_empty():
		y += 16
		heading(Vector2(x, y + 20), Tx.t("ui.cultivation.fates"), left.size.x - 48)
		y += 44
		if not cu.fate_offer.is_empty():
			btn(Rect2(x, y, left.size.x - 48, 44), Tx.t("ui.cultivation.choose_fate"), "fates", null, true, true, "", 20)
			y += 52
		var names: Array = []
		for rec in cu.fates: names.append(ContentDB.name_of("fates", str(rec.get("id", ""))))
		if not names.is_empty(): para(Rect2(x, y - 14, left.size.x - 48, maxf(24.0, left.end.y - y)), ", ".join(names), 16, UiKit.PAPER, 3)
	# Right: foundation, residue, resistance.
	x = right.position.x + 24
	y = right.position.y + 44
	heading(Vector2(x, y), Tx.t("ui.cultivation.foundation_share"), right.size.x - 48)
	y += 26
	var share := ProgressionRules.foundation_share(cu)
	var hollow_at := float(ContentDB.stat_const("pill_life", {}).get("hollow_share", 0.3))
	var fb := Rect2(x, y, right.size.x - 48, 30)
	bar(fb, share, UiKit.WARNING if share > hollow_at else UiKit.JADE, "%d%%" % int(round(share * 100)))
	var hx := fb.position.x + fb.size.x * hollow_at
	draw_line(Vector2(hx, fb.position.y - 4), Vector2(hx, fb.end.y + 4), UiKit.RED, 2)
	y += 60
	para(Rect2(x, y - 20, right.size.x - 48, 60), Tx.t("ui.cultivation.foundation_hollow") if share > hollow_at else Tx.t("ui.cultivation.foundation_sound"), 16,
		UiKit.WARNING if share > hollow_at else UiKit.MIST, 2)
	y += 56
	heading(Vector2(x, y), Tx.t("ui.cultivation.residue"), right.size.x - 48)
	y += 36
	var pen := int(round(ProgressionRules.residue_penalty(cu) * 100))
	text(Vector2(x, y), Tx.t("ui.cultivation.residue_value") % [cu.residue, pen] if pen > 0 else Tx.t("ui.cultivation.residue_harmless") % cu.residue, 18,
		UiKit.PAPER if pen == 0 else UiKit.WARNING)
	y += 44
	heading(Vector2(x, y), Tx.t("ui.cultivation.pill_resistance"), right.size.x - 48)
	y += 36
	if cu.pill_resistance.is_empty():
		text(Vector2(x, y), Tx.t("ui.cultivation.no_resistance"), 18, UiKit.MIST)
	for fam in cu.pill_resistance:
		text(Vector2(x, y), Tx.t("ui.cultivation.family_" + str(fam)), 18, UiKit.PAPER)
		var rr: Dictionary = cu.pill_resistance[fam]
		text(Vector2(right.end.x - 24 - 320, y), Tx.t("ui.cultivation.resistance_row") % [int(rr.get("count", 0)), int(rr.get("doses", 0)),
			int(round(ProgressionRules.resistance_factor(cu, str(fam)) * 100))], 18, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 320)
		y += 28

func _methods(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	if cu.methods_known.is_empty():
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.cultivation.you_know_no_cultivation_method"), 22, UiKit.MIST)
		return
	tour_mark("methods", r.grow(-14))   # decision 43: a tour's anchor
	list("methods", r.grow(-14), cu.methods_known.size(), 112, func(i: int, rr: Rect2):
		var mid := str(cu.methods_known[i])
		var m := ProgressionRules.method(mid)
		var active := mid == cu.method_id
		panel(rr, "minor_panel", "selected" if active else "normal")
		text(rr.position + Vector2(20, 34), ContentDB.name_of("methods", mid), 22, UiKit.PALE_GOLD if active else UiKit.PAPER)
		text(rr.position + Vector2(20, 64), Tx.t("ui.cultivation.affinity_rate_2f_capacity_2f") % [str(m.get("grade", "")).capitalize(),
			str(m.get("affinity", "none")).capitalize(), float(m.get("rate", 1.0)), float(m.get("capacity", 1.0)), ContentDB.name_of("realms", str(m.get("ceiling", "")))], 16, UiKit.MIST)
		text(rr.position + Vector2(20, 90), Tx.t("ui.cultivation.compatibility") % ProgressionRules.method_compatibility(ch, mid).capitalize(), 16, UiKit.BRIGHT_JADE)
		if not active: btn(Rect2(rr.end.x - 170, rr.position.y + 26, 150, 50), Tx.t("ui.cultivation.switch"), "switch", mid)
		else: text(Vector2(rr.end.x - 170, rr.position.y + 58), Tx.t("ui.cultivation.active"), 20, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, 150)
	)

func _dao(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	var ids: Array = cu.daos.keys()
	if ids.is_empty():
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.cultivation.no_dao_insight_yet_use"), 22, UiKit.MIST)
		return
	var tiers := [Tx.t("ui.cultivation.unaware"), Tx.t("ui.cultivation.observation"), Tx.t("ui.cultivation.imitation"), Tx.t("ui.cultivation.reliable_execution"), Tx.t("ui.cultivation.explanation"), Tx.t("ui.cultivation.adaptation"), Tx.t("ui.cultivation.original_application")]
	tour_mark("daos", r.grow(-14))   # decision 43: a tour's anchor
	list("daos", r.grow(-14), ids.size(), 80, func(i: int, rr: Rect2):
		var d := str(ids[i])
		var st: Dictionary = cu.daos[d]
		var tier := int(st.get("tier", 0))
		text(rr.position + Vector2(20, 32), ContentDB.name_of("daos", d), 22, UiKit.PAPER)
		text(rr.position + Vector2(20, 60), tiers[clampi(tier, 0, tiers.size() - 1)], 16, UiKit.GOLD)
		var ins := float(st.get("insight", 0.0))
		var need := ProgressionRules.dao_next_need(tier)
		var bar_r := Rect2(rr.position.x + 330, rr.position.y + 18, 520, 30)
		if need > 0.0: bar(bar_r, ins / need, UiKit.SOUL, Tx.t("ui.cultivation.insight_2") % [UiKit.fmt(ins), UiKit.fmt(need)])
		else: bar(bar_r, 1.0, UiKit.SOUL, Tx.t("ui.cultivation.insight_top") % UiKit.fmt(ins))
		if Unlocks.is_unlocked(ch.id, "contemplate"):
			btn(Rect2(rr.end.x - 170, rr.position.y + 12, 150, 44), Tx.t("ui.cultivation.contemplate"), "contemplate", d, false, need > 0.0, Tx.t("ui.cultivation.dao_top_tier"))
	)

func _seclusion(ch) -> void:
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	var room: Dictionary = Game.room_rt.def if Game.room_rt else {}
	var cap := Game.progression.seclusion_cap(room)
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 90)), Tx.plural("ui.cultivation.choose_what_to_cultivate_while", int(cap)) % int(cap), 20, UiKit.PAPER)
	tour_mark("away", Rect2(r.position + Vector2(16, 12), Vector2(r.size.x - 32, 96)))   # decision 43: a tour's anchor
	var foci := [["accumulate", Tx.t("ui.cultivation.accumulate"), Tx.t("ui.cultivation.realm_progress"), "seclusion"], ["temper_body", Tx.t("ui.cultivation.temper_body"), Tx.t("ui.cultivation.body_training"), "seclusion"],
		["heal", Tx.t("ui.cultivation.heal"), Tx.t("ui.cultivation.treat_injuries"), "seclusion"], ["contemplate", Tx.t("ui.cultivation.contemplate"), Tx.t("ui.cultivation.dao_insight"), "insight_sites"],
		["refine_qi", Tx.t("ui.cultivation.refine_qi"), Tx.t("ui.cultivation.purity"), "refine_qi"], ["nourish_soul", Tx.t("ui.cultivation.nourish_soul"), Tx.t("ui.cultivation.soul"), "nourish_soul"]]
	# v2 unlock timeline: Settle foundation shows once pills pass a fifth of this realm's foundation (or while it is the focus).
	if ProgressionRules.foundation_share(ch.cultivator) > float(ContentDB.stat_const("pill_life", {}).get("settle_show_share", 0.2)) \
		or str(ch.seclusion.get("focus", "")) == "settle_foundation":
		foci.append(["settle_foundation", Tx.t("ui.cultivation.settle_foundation"), Tx.t("ui.cultivation.settle_foundation_desc"), "seclusion"])
	# S44: a medicinal bath takes the seclusion slot at a Bath station.
	var bath_item := _bath_item(ch)
	foci.append(["bath", Tx.t("ui.cultivation.bath"), Tx.t("ui.cultivation.bath_desc") % [ContentDB.item_name(bath_item), ch.inventory.count(bath_item)]
		if bath_item != "" else Tx.t("ui.cultivation.bath_none"), "medicinal_bath"])
	var cur := str(ch.seclusion.get("focus", ""))
	for i in foci.size():
		var f: Array = foci[i]
		var rr := Rect2(r.position.x + 24 + (i % 3) * 330, r.position.y + 116 + (i / 3) * 118, 310, 104)   # B22: three rows clear of the status line
		var ok := Unlocks.is_unlocked(ch.id, f[3])
		panel(rr, "minor_panel", "selected" if cur == f[0] else ("disabled" if not ok else "normal"))
		text(rr.position + Vector2(20, 40), f[1], 22, UiKit.PAPER if ok else UiKit.HOLLOW)
		text(rr.position + Vector2(20, 72), f[2], 18, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 40)
		region(rr, "focus", f[0], ok, Unlocks.locked_text(f[3]))
	if cur != "":
		text(Vector2(r.position.x + 24, r.end.y - 14), Tx.t("ui.cultivation.set_close_the_game_and") % cur.replace("_", " ").capitalize(), 20, UiKit.BRIGHT_JADE,
			HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 48)

## The strongest bath in the bag, or "".
func _bath_item(ch) -> String:
	var best := ""
	for s in ch.inventory.bag:
		if s != null and ContentDB.item(str(s.id)).has("bath"):
			if best == "" or StatRules.grade_index(str(ContentDB.item(str(s.id)).get("grade", "plain"))) > StatRules.grade_index(str(ContentDB.item(best).get("grade", "plain"))):
				best = str(s.id)
	return best

func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"meditate":
			if submit({"type": "toggle_meditation"}).get("ok", false): close()
		"breakthrough": navigate.emit("breakthrough", {})
		"fates": navigate.emit("fates", {})
		"relations": navigate.emit("relations", {})
		"vow_on": submit({"type": "set_vow", "vow": str(data), "on": true})
		"path_take": submit({"type": "set_path", "path": str(data), "on": true})
		"path_leave": ask(Tx.t("ui.cultivation.leave_blood_confirm" if str(data) == "blood" else "ui.cultivation.leave_path_confirm") % int(ContentDB.stat_const("paths", {}).get(str(data), {}).get("leave_heart_demon", 10)), "path_off", data, true)
		"path_off": submit({"type": "set_path", "path": str(data), "on": false})
		"vow_off": ask(Tx.t("ui.cultivation.break_vow_confirm") % [ContentDB.name_of("vows", str(data)), int(ContentDB.config("vows").get("break_heart_demon", 15))], "vow_break", data, true)
		"vow_break": submit({"type": "set_vow", "vow": str(data), "on": false})
		"meridian": submit({"type": "open_meridian", "channel": str(data)})
		"reset_meridians": ask(Tx.t("ui.cultivation.reset_all_meridian_points"), "reset_yes")
		"reset_yes": submit({"type": "reset_meridians"})
		"switch":
			var cost := Game.progression.method_switch_preview(ch, false)
			ask(Tx.t("ui.cultivation.switch_method_you_lose_qp") % UiKit.fmt(cost), "switch_yes", data)
		"switch_yes": submit({"type": "switch_method", "id": str(data)})
		"contemplate":
			submit({"type": "set_contemplate", "dao": str(data)})
			flash(Tx.t("ui.cultivation.contemplating_in_seclusion") % ContentDB.name_of("daos", str(data)))
		"focus":
			if str(data) == "bath":
				var rb := submit({"type": "start_bath", "item": _bath_item(ch)})
				if rb.get("ok", false): flash(Tx.t("ui.cultivation.seclusion_set"))
				elif str(rb.get("text", "")) != "": flash(str(rb.text))
				return
			if submit({"type": "enter_seclusion", "focus": str(data)}).get("ok", false): flash(Tx.t("ui.cultivation.seclusion_set"))
