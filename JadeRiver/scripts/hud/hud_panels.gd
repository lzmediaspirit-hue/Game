class_name HudPanels
extends HudPart
## Drawing the HUD's plates: the player panel with its bars and statuses, the points badges, the party chips, the quest
## tracker, the purse, the icon row, the progress edge, the log, and the unbound player's plain panel.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

const MenuPage = preload("res://scripts/ui/pages/menu_page.gd")

func draw_player_panel(c) -> void:
	if not hud.shown("player_panel"): return
	# The panel grows by one row once the Soul bar exists (Spirit Awakening).
	var soul_row: bool = c.pools.max_soul > 0.0 and hud.shown("soul_bar")
	var r := hud.layout.panel_rect(c)
	hud.draw_style_box(hud.frame_style, r)
	# No portrait roundel (the user's note on the P3 mockups): name, realm and the bars take the panel's width; the
	# bottleneck shows on the Stored Qi bar along the bottom edge.
	UiKit.draw_text(hud, c.name, r.position + Vector2(18, 30), 18, UiKit.PAPER)
	if hud.shown("realm_badge"):
		# Concealment's false realm (S48) is the badge the world sees; a veil mark says it is not the true one.
		var badge := ContentDB.realm_label(Game.progression.shown_realm(c), -1 if c.cultivator.false_realm != "" else ProgressionRules.level(c))
		var veiled: bool = c.cultivator.false_realm != ""
		UiKit.draw_text(hud, badge, r.position + Vector2(18, 50), 16, UiKit.MIST if veiled else UiKit.PALE_GOLD)
		if veiled: UiKit.draw_text(hud, Tx.t("hud.realm_veiled"), r.position + Vector2(24 + UiKit.text_width(badge, 16), 50), 14, UiKit.MIST)
	var y := 60.0
	if hud.shown("hp_bar"):
		# A heal over time still running shows where the bar is going: a pale jade run past the red.
		var coming := 0.0
		for h in Game.combat.hots_of(c.id): coming += float(h.per_s) * float(h.left)
		bar(Rect2(r.position.x + 56, r.position.y + y, 288, 14), c.pools.hp / maxf(1.0, c.pools.max_hp), UiKit.HP, Tx.t("hud.hp"), "%s / %s" % UiKit.pool_values(c.pools.hp, c.pools.max_hp),
			coming / maxf(1.0, c.pools.max_hp), float(hud.pulses.get("bar:hp", 0.0)))
		y += 18
	# No cultivation, no Qi: the QI bar appears only once a QI pool exists.
	if c.pools.max_qi > 0.0 and hud.shown("qi_bar"):
		bar(Rect2(r.position.x + 56, r.position.y + y, 288, 14), c.pools.qi / c.pools.max_qi, UiKit.QI, Tx.t("hud.qi"), "%s / %s" % UiKit.pool_values(c.pools.qi, c.pools.max_qi), 0.0, float(hud.pulses.get("bar:qi", 0.0)))
		y += 18
	if soul_row:
		bar(Rect2(r.position.x + 56, r.position.y + y, 288, 14), c.pools.soul / c.pools.max_soul, UiKit.SOUL, Tx.t("hud.sl"), "%s / %s" % UiKit.pool_values(c.pools.soul, c.pools.max_soul), 0.0, float(hud.pulses.get("bar:soul", 0.0)))
	# S48 the Blood path: a thin crimson strip for the blood essence kills have gathered.
	if ProgressionAuthority.walks(c, "blood"):
		var strip := Rect2(r.position.x + 56, r.end.y - 6, 288, 3)
		hud.draw_rect(strip.grow(1), UiKit.INK)
		hud.draw_rect(Rect2(strip.position, Vector2(strip.size.x * clampf(Game.combat.essence_of(c.id) / 100.0, 0.0, 1.0), strip.size.y)), UiKit.BLOOD)
	# Status stack (injuries, stability, toxicity, composure, buffs, statuses).
	var meter: bool = c.pools.hollowing > 0.5
	var icons: Array = []
	for kind in c.cultivator.injuries: icons.append("injury_" + kind)
	if Unlocks.is_unlocked(c.id, "foundation") and c.cultivator.stability != "stable": icons.append("stability_" + c.cultivator.stability)
	if c.cultivator.state == "consolidating": icons.append("consolidating")
	if c.cultivator.toxicity > 0.5 * c.stats.value("toxicity_tolerance") and c.cultivator.toxicity > 5: icons.append("toxicity")
	if c.pools.hollowing > 5 and not meter: icons.append("hollowing")
	if ProgressionRules.heart_demon_steps(c.cultivator) >= 1: icons.append("heart_demon")   # S48: 25 and more
	if Game.combat.killing_intent_stacks(c.id) >= 5: icons.append("buff_attack")               # S48 Killing Intent
	if Game.combat.poison_body_active(c): icons.append("poison_body")                          # S48 the Poison Body
	if Unlocks.is_unlocked(c.id, "composure") and c.pools.composure < 100: icons.append("composure")
	# Timed entries carry their seconds left, drawn under the icon: a status, a buff, a heal over time (the tea's own
	# icon while it works, so a tea drunk at full HP still shows it is running).
	var left := {}
	for s in c.pools.statuses:
		if s.id == "spawn_protection": continue
		var sic := str(ContentDB.entry("status_effects", str(s.id)).get("icon", s.id))
		if not icons.has(sic): icons.append(sic)
		left[sic] = maxf(float(left.get(sic, 0.0)), float(s.get("remaining", 0.0)))
	for m in c.stats.modifiers:
		if float(m.duration) >= 0 and not str(m.source).begins_with("heal:"):
			var ic := "buff_attack" if str(m.stat) in ["physical_attack", "qi_attack"] else ("buff_defense" if "defense" in str(m.stat) else "buff_speed")
			if not icons.has(ic): icons.append(ic)
			left[ic] = maxf(float(left.get(ic, 0.0)), float(m.get("remaining", m.duration)))
	for h in Game.combat.hots_of(c.id):
		var src := str(h.get("source", ""))
		var hic := src.substr(5) if src.begins_with("item:") and SpriteCache.icon_fit(src.substr(5), 24).size() > 0 else "healing_pill"
		if not icons.has(hic): icons.append(hic)
		left[hic] = maxf(float(left.get(hic, 0.0)), float(h.left))
	# Under the panel (mockups 01, 02): the Hollowing meter first once it has risen, then 24 px icons 4 apart.
	var row_y := r.end.y + 8.0
	var x := r.position.x + 4.0
	if meter: x = _draw_hollowing(c, Vector2(r.position.x + 2.0, row_y))
	# What the row holds, for the world's labels to keep off (a Festival Lantern's plate lay over the Hollowing meter).
	hud.status_rect = Rect2(r.position.x, row_y - 2.0, minf(r.end.x, x + 28.0 * icons.size()) - r.position.x, 46.0) if meter or not icons.is_empty() else Rect2()
	for ic in icons.slice(0, 12):
		if x + 24.0 > r.end.x: break
		hud.glyph(ic, Vector2(x + 12, row_y + 12), 24)
		if float(left.get(ic, 0.0)) > 0.0:
			var secs := float(left[ic])
			UiKit.draw_outlined(hud, UiKit.span(secs), Vector2(x - 6, row_y + 40), 14, UiKit.PAPER,
				HORIZONTAL_ALIGNMENT_CENTER, 36)
		x += 28
	# S47 Sword Intent: ten pips along the panel's foot while a jian is in hand and Intent is building.
	var stacks := int(Game.combat.sword_intent.get(c.id, {}).get("stacks", 0))
	if stacks > 0 and str(StatRules.family(c).get("id", "")) == "jian":
		for i in 10:
			var pc := Vector2(r.position.x + 130 + i * 21, r.end.y - 7)
			var dia := PackedVector2Array([pc + Vector2(0, -5), pc + Vector2(5, 0), pc + Vector2(0, 5), pc + Vector2(-5, 0)])
			if i < stacks: hud.draw_colored_polygon(dia, UiKit.GOLD if stacks >= 10 else UiKit.MIST)
			hud.draw_polyline(dia + PackedVector2Array([dia[0]]), UiKit.INK, 1.5)

func bar(r: Rect2, frac: float, fill: Color, label: String, value_text: String, ahead := 0.0, flash := 0.0) -> void:
	hud.draw_rect(r.grow(2), UiKit.INK)
	hud.draw_rect(r, UiKit.BAR_TROUGH)
	if ahead > 0.0 and frac < 1.0:
		var a0 := r.size.x * clampf(frac, 0, 1)
		hud.draw_rect(Rect2(r.position + Vector2(a0, 0), Vector2(r.size.x * clampf(frac + ahead, 0, 1) - a0, r.size.y)), Color(UiKit.BRIGHT_JADE, 0.45))
	hud.draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(frac, 0, 1), r.size.y)), fill)
	# A consumable just touched this pool (item_used): the frame glows jade for a moment, full or not.
	if flash > 0.0: hud.draw_rect(r.grow(2), Color(UiKit.BRIGHT_JADE, clampf(flash / 0.8, 0.0, 1.0)), false, 2.0)
	hud.draw_line(r.position + Vector2(1, 2), r.position + Vector2(maxf(1, r.size.x * clampf(frac, 0, 1) - 1), 2), Color(UiKit.PALE_GOLD, 0.35), 2)
	UiKit.draw_text(hud, label, r.position + Vector2(-34, 12), 14, UiKit.HUD_LABEL, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	UiKit.draw_outlined(hud, value_text, r.position + Vector2(0, r.size.y * 0.5 + 5), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

## The Hollowing meter (mockup 02): its stops at Burden and at Seizure, the value, and which way it runs (falling
## faster near the lanterns). Returns where the status icons go on.
func _draw_hollowing(c, at: Vector2) -> float:
	var h: float = c.pools.hollowing
	if hud._hollow_last >= 0.0 and absf(h - hud._hollow_last) > 0.0001: hud._hollow_dir = signf(h - hud._hollow_last)
	hud._hollow_last = h
	var burden := float(ContentDB.stat_const("hollowing.burden_at", 50))
	var seize := float(ContentDB.stat_const("hollowing.seizure_at", 100))
	hud.glyph("hollowing", at + Vector2(12, 12), 24)
	var b := Rect2(at.x + 32, at.y + 8, 170, 10)
	hud.draw_rect(b.grow(2), UiKit.INK)
	hud.draw_rect(b, UiKit.BAR_TROUGH)
	hud.draw_rect(Rect2(b.position, Vector2(b.size.x * clampf(h / seize, 0.0, 1.0), b.size.y)), UiKit.HOLLOW if h < burden else UiKit.WARNING)
	var bx := b.position.x + b.size.x * burden / seize
	hud.draw_rect(Rect2(bx - 1, b.position.y - 3, 2, 16), UiKit.PALE_GOLD)
	hud.draw_rect(Rect2(b.end.x - 1, b.position.y - 3, 2, 16), UiKit.RED)
	UiKit.draw_outlined(hud, Tx.t("hud.hollow_burden") % int(burden), Vector2(bx - 60, at.y + 34), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 120)
	var x := b.end.x + 8.0
	var v := str(int(round(h)))
	UiKit.draw_outlined(hud, v, Vector2(x, at.y + 18), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 40)
	x += UiKit.text_width(v, 16, true) + 4.0
	if hud._hollow_dir != 0.0:
		var col := UiKit.BRIGHT_JADE if hud._hollow_dir < 0.0 else UiKit.RED_TEXT
		UiKit.draw_outlined(hud, "▼" if hud._hollow_dir < 0.0 else "▲", Vector2(x, at.y + 18), 14, col, HORIZONTAL_ALIGNMENT_LEFT, 20)
		x += 16.0
		if hud._hollow_dir < 0.0 and Game.room_rt != null and Game.room_rt.def.get("lantern", false):
			var lw := Tx.t("hud.hollow_lanterns")
			UiKit.draw_outlined(hud, lw, Vector2(x, at.y + 18), 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, 90)
			x += UiKit.text_width(lw, 14, true) + 4.0
	return x + 12.0

## The badges in their row, each popping in as it appears: from small past full size and back, fading in.
func draw_points(_c) -> void:
	for pb in hud.layout.frame_badges():
		var k := hud.layout.points_pop(str(pb.id))
		if k >= 1.0:
			hud.glyph("points_" + str(pb.id), pb.center, 32)
			continue
		var s := lerpf(0.4, 1.2, k / 0.6) if k < 0.6 else lerpf(1.2, 1.0, (k - 0.6) / 0.4)
		hud.draw_set_transform(pb.center, 0.0, Vector2(s, s))
		hud.glyph("points_" + str(pb.id), Vector2.ZERO, 32, Color(1, 1, 1, clampf(k * 2.5, 0.0, 1.0)))
		hud.draw_set_transform(Vector2.ZERO)

func draw_party(c) -> void:
	for pc in hud.layout.party_chips(c):
		var cen: Vector2 = pc.center
		var kind := str(pc.kind)
		var a = _party_ally(pc)
		var frac: float = clampf(a.pools.hp / maxf(1.0, a.pools.max_hp), 0.0, 1.0) if a != null else 1.0
		var down: bool = a != null and str(a.ai.get("state", "")) == "downed"
		hud.ring(cen, 24, kind == "mount" and c.riding)
		if kind == "companion":
			_draw_face(cen, str(pc.uid), down)
		else:
			var p: Dictionary = Game.pets.pet_of(c, str(pc.uid))
			var art := str(ContentDB.entry("pets", str(p.get("species", ""))).get("art", p.get("species", "")))
			UiKit.draw_creature(hud, Rect2(cen - Vector2(18, 18), Vector2(36, 36)), art, "idle", hud.t)
			if p.get("wounded", false): down = true   # a Grievous Wound: the ring runs red all round
		if down: hud.draw_arc(cen, 28, 0, TAU, 32, UiKit.RED, 3)
		elif kind in ["active", "party", "companion"]:
			hud.draw_arc(cen, 28, -PI / 2, -PI / 2 + TAU * maxf(frac, 0.001), 32, UiKit.BRIGHT_JADE if frac > 0.3 else UiKit.RED, 3)
		# A name too long for its chip gives its last word ("Reed Otter" is the otter, mockup 01).
		var nm := str(pc.name)
		if UiKit.text_width(nm, 14, true) > 58.0: nm = nm.get_slice(" ", nm.get_slice_count(" ") - 1)
		var col := UiKit.SKY
		if kind == "bag": col = UiKit.MIST
		elif kind == "mount":
			col = UiKit.GOLD if c.riding else UiKit.MIST
			nm = Tx.t("hud.walk") if c.riding else Tx.t("hud.ride")
		UiKit.draw_outlined(hud, UiKit.fit(nm, 14, 58, true), cen + Vector2(-30, 42), 14, col, HORIZONTAL_ALIGNMENT_CENTER, 60)

## The party member's body in this room (a pet's or a disciple's ally), or null when it is not out.
func _party_ally(pc: Dictionary):
	if Game.room_rt == null: return null
	var au = (Game.companions.allies if str(pc.kind) == "companion" else Game.pets.allies).get(str(pc.uid))
	return Game.room_rt.enemies.get(int(au)) if au != null else null

## A fellow disciple's face for their chip: the head of their figure as the game draws them. Decision 42 (no old
## side-view character left in the top-down game): for a top-down character, the top-down figure's head (its idle
## frame three-quarters toward the camera at x FACE_TOP_K, its sheets loading on threads: the chip is empty the frames
## they take; the frame cast for the pictures at 38 px, decision 43, so the chip keeps the head it was framed for); the
## side view's head and shoulders only for a classic side-view character.
func _draw_face(center: Vector2, cid: String, dim := false) -> void:
	var box := Vector2(Hud.FACE_BOX, Hud.FACE_BOX)
	if Figures.top_down():
		var fig: TopdownFigure = hud._faces.get("top|" + cid)
		if fig == null:
			fig = TopdownFigure.wearing(face_outfit(cid), true)
			hud._faces["top|" + cid] = fig
		if not fig.loaded(): return
		var b := fig.bounds("idle", TopdownDoll.PORTRAIT_ROW, 0, "body", true)   # the bare body: its head under any hair
		var head := Vector2(roundf(b.get_center().x), b.position.y + Hud.FACE_TOP_HEAD)   # the head's middle, art px from the feet
		fig.draw(hud, (center - head * Hud.FACE_TOP_K).round(), "idle", TopdownDoll.PORTRAIT_ROW, 0, Color(1, 1, 1, 0.45 if dim else 1.0), Hud.FACE_TOP_K,
			Rect2(center - box * 0.5, box), true)
		return
	hud.side_view.draw_face(center, cid, dim)   # side view

## A companion's look for their face: their outfit, its unset pieces a disciple's, no weapon.
func face_outfit(cid: String) -> Dictionary:
	var o: Dictionary = ContentDB.entry("companions", cid).get("outfit", {}).duplicate()
	for k in ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]:
		if not o.has(k): o[k] = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "boots"}.get(k, "none")
	if not o.has("hair_color"): o.hair_color = 0
	o.weapon = "none"
	return o

## The quest tracker (mockup 02): a plate under the statuses with a gold rule down its left, each quest's title, where
## it leads with a 48 px go button that walks you there (lit while it does), and its objectives; between main quests
## the story's next one first (◇ Next: who gives it and where, or the Level it waits on and where to hunt); it rests in
## boss arenas and stops above the log.
func draw_tracker(c) -> void:
	var entries: Array = WorldShared.quest_tracker(c)
	if entries.is_empty() or boss_arena(): return
	var top := hud.layout.panel_rect(c).end.y + Hud.TRACKER_DROP
	var here := Game.room_rt.room_id if Game.room_rt else ""
	var rows: Array = []
	var h := 8.0
	for q in entries:
		var goal := str(q.get("target_room", ""))
		var go := goal != "" and goal != here
		var eh := 24.0 + (20.0 if go else 0.0) + 20.0 * (q.lines as Array).size()
		if go: eh = maxf(eh, 52.0)
		if not rows.is_empty() and top + h + eh > Hud.TRACKER_FOOT: break
		rows.append({"q": q, "goal": goal, "go": go, "h": eh})
		h += eh + 4.0
	hud.tracker_rect = Rect2(14, top, 342, h)
	hud.draw_rect(hud.tracker_rect, UiKit.PLATE)
	hud.draw_rect(Rect2(hud.tracker_rect.position, Vector2(2, hud.tracker_rect.size.y)), Color(UiKit.GOLD, 0.5))
	var y := top + 4.0
	for row in rows:
		var q: Dictionary = row.q
		var main: bool = QuestAuthority.leads(str(q.kind))
		var col = UiKit.GOLD if main else UiKit.SKY
		var tw := 266.0 if row.go else 318.0
		var mark := "◇ " if str(q.kind) == "next" else ("◆ " if main else "● ")
		UiKit.draw_text(hud, UiKit.fit(mark + str(q.name), 18, tw), Vector2(24, y + 20), 18, col, HORIZONTAL_ALIGNMENT_LEFT, tw)
		var ly := y + 24.0
		if row.go:
			# S49 auto-path: a button that walks you to where the quest leads (lit while it is walking you there).
			var br := Rect2(300, y + 2, 48, 48)
			var going: bool = Game.world.auto_path_target(Game.active()) == str(row.goal)
			hud.draw_style_box(UiKit.style("button_secondary", "selected" if going else "normal"), br)
			UiKit.draw_text(hud, "➤", br.position + Vector2(0, 31), 18, UiKit.GOLD if going else UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, br.size.x)
			hud.tracker_paths.append({"rect": HudLayout.go_hit(br), "target": str(row.goal)})
			# P1: the tracker names where the quest leads (a hunting ground as one).
			var place := WorldAuthority.place_name(str(row.goal))
			if q.get("hunt", false): place = Tx.t("hud.hunt_at") % place
			UiKit.draw_text(hud, UiKit.fit("➤ " + place, 14, 262), Vector2(32, ly + 15), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 262)
			ly += 20.0
		for line in q.lines:
			var lw := 262.0 if row.go and ly < y + 52.0 else 314.0
			var count := "%d / %d" % [int(line.have), int(line.need)] if int(line.need) > 1 else ""
			var lc := UiKit.BRIGHT_JADE if line.done else UiKit.PAPER
			UiKit.draw_text(hud, tracker_objective(("✓ " if line.done else "· ") + str(line.text), count, lw), Vector2(32, ly + 16), 16, lc, HORIZONTAL_ALIGNMENT_LEFT, lw)
			if count != "": UiKit.draw_text(hud, count, Vector2(32, ly + 16), 16, lc, HORIZONTAL_ALIGNMENT_RIGHT, lw)
			ly += 20.0
		y += float(row.h) + 4.0

## B11: an objective beside its count on a tracker line `width` wide: the count keeps its place at the right end and
## the words give way with an ellipsis (the count was appended and cut: "…Shallows  0" for 0/5).
static func tracker_objective(words: String, count: String, width: float) -> String:
	return UiKit.fit(words, 16, width - (UiKit.text_width(count, 16) + 10.0 if count != "" else 0.0))

## The icon row (Menu, Bag, Map, Mail at 56 apart): a count on Mail, and a vermilion ready seal on Menu when something
## waits in the hub (mockup 02).
func draw_icon_row(c) -> void:
	for ic in hud.icon_row:
		if not hud.shown(ic[0]): continue
		var at: Vector2 = ic[1]
		hud.ring(at, 26, hud.pulses.has("hud:" + ic[0]))
		hud.glyph(ic[0], at, 32)
		if ic[0] == "mail" and Game.mail.unread(c) > 0: UiKit.count_badge(hud, at + Vector2(23, -23), Game.mail.unread(c))
		if ic[0] == "menu" and hub_ready(c): UiKit.ready_seal(hud, at + Vector2(25, -25))

## Something waits in the hub: the bottleneck is reached, or a day's activity chest is full and not yet opened (the
## Menu's tablets that carry a ready seal, MenuPage.ready_seals).
func hub_ready(c) -> bool:
	return not MenuPage.ready_seals(c).is_empty()

## The purse (mockup 02): silver and spirit stones on the currency pill under the icon row, growing leftward for large
## sums; it rests in boss arenas (mockup 01).
func draw_purse() -> void:
	var silver := UiKit.fmt(Game.economy.balance("silver_tael"))
	var stones := int(Game.account.currencies.get("spirit_stone", 0))
	var sw := UiKit.text_width(silver, 18)
	var w := 38.0 + sw + 16.0
	if stones > 0: w += 34.0 + UiKit.text_width(UiKit.fmt(stones), 18)
	w = maxf(222.0, w)
	var cr := Rect2(1262 - w, 222, w, 34)
	hud.purse_rect = cr
	hud.draw_style_box(UiKit.style("currency_pill"), cr)
	hud.glyph("coin", cr.position + Vector2(20, 17), 32)
	UiKit.draw_text(hud, silver, cr.position + Vector2(38, 24), 18, UiKit.PALE_GOLD)
	if stones > 0:
		var sx := 38.0 + sw + 28.0
		hud.glyph("spirit_stone", cr.position + Vector2(sx, 17), 32)
		UiKit.draw_text(hud, UiKit.fmt(stones), cr.position + Vector2(sx + 20, 24), 18, UiKit.BRIGHT_JADE)

func boss_arena() -> bool:
	return Game.room_rt != null and str(Game.room_rt.def.get("type", "")) == "boss_arena"

## The progress edge (mockups 01, 02): the stage's progress along the foot with a stop at each Level; at the
## bottleneck it glows gold, Stored Qi runs as a bright lane along it and the line above says the breakthrough is ready.
func draw_progress(c) -> void:
	var cu: CultivatorState = c.cultivator
	var r := Rect2(0, 712, 1280, 8)
	var frac := cu.progress_fraction()
	var realm := ContentDB.realm(cu.realm_key)
	var levels := int(realm.get("levels", 1))
	var base := int(realm.get("level", 0))
	var lv := ProgressionRules.level(c)
	if cu.state == "bottleneck":
		hud.draw_polygon(PackedVector2Array([Vector2(0, 660), Vector2(1280, 660), Vector2(1280, 712), Vector2(0, 712)]),
			PackedColorArray([Color(UiKit.GOLD, 0.0), Color(UiKit.GOLD, 0.0), Color(UiKit.PALE_GOLD, 0.3), Color(UiKit.PALE_GOLD, 0.3)]))
		hud.draw_rect(Rect2(0, 710, 1280, 10), UiKit.GOLD)
		hud.draw_rect(Rect2(0, 710, 1280, 3), UiKit.PALE_GOLD)
		if cu.stored_qi > 0: hud.draw_rect(Rect2(0, 710, 1280 * clampf(cu.stored_qi / maxf(1.0, cu.need()), 0, 1), 3), UiKit.PAPER)
		for k in range(1, levels): hud.draw_rect(Rect2(1280.0 * k / levels - 1, 706, 2, 14), UiKit.INK)
		var x := 16.0
		if cu.stored_qi > 0:
			var sq := Tx.t("hud.stored_qi") % UiKit.fmt(cu.stored_qi)
			UiKit.draw_outlined(hud, sq, Vector2(x, 700), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 200)
			x += UiKit.text_width(sq, 14, true) + 24.0
		var ready := Tx.t("hud.bottleneck_ready")
		UiKit.draw_outlined(hud, ready, Vector2(x, 700), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, 520)
		UiKit.draw_outlined(hud, Tx.t("hud.bottleneck_tap"), Vector2(x + UiKit.text_width(ready, 16, true) + 6.0, 700), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 240)
		return
	hud.draw_rect(r, Color(UiKit.INK, 0.6))
	var col = UiKit.QI if c.pools.max_qi > 0 else UiKit.PALE_GOLD
	var fx := r.size.x * frac
	hud.draw_rect(Rect2(r.position, Vector2(fx, r.size.y)), col)
	if cu.stored_qi > 0:
		hud.draw_rect(Rect2(0, 710, 1280 * clampf(cu.stored_qi / maxf(1.0, cu.need()), 0, 1), 2), UiKit.PALE_GOLD)
	for k in range(1, levels):
		var sx := 1280.0 * k / levels
		hud.draw_rect(Rect2(sx - 2, 707, 4, 13), UiKit.INK)
		hud.draw_rect(Rect2(sx - 1, 708, 2, 12), UiKit.PALE_GOLD)
		UiKit.draw_outlined(hud, Tx.t("hud.level_stop") % (base + k), Vector2(sx - 40, 700), 14, UiKit.PALE_GOLD if base + k == lv + 1 else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 80)
	var pct := "%d%%" % int(frac * 100.0)
	if fx >= 56.0: UiKit.draw_outlined(hud, pct, Vector2(fx - 86, 700), 14, col, HORIZONTAL_ALIGNMENT_RIGHT, 80)
	else: UiKit.draw_outlined(hud, pct, Vector2(fx + 6, 700), 14, col, HORIZONTAL_ALIGNMENT_LEFT, 80)

func draw_log() -> void:
	# Above the joystick's half (mockup 01), newest at the foot, outlined, and kept out of the clear zone. Before the log
	# is revealed only the lines that must reach the player (what a consumable did) are drawn.
	var x := 20.0 if not hud.left_handed else 1280.0 - 20.0 - Hud.LOG_W
	var lines := hud.log_lines if hud.shown("system_log") else hud.log_lines.filter(func(l): return l.get("always", false))
	var rows := log_rows(lines)
	var n := rows.size()
	for i in n:
		var r: Dictionary = rows[i]
		var col: Color = r.color
		UiKit.draw_outlined(hud, str(r.text), Vector2(x + float(r.indent), Hud.LOG_FOOT - (n - 1 - i) * 21.0), 16, col, HORIZONTAL_ALIGNMENT_LEFT, Hud.LOG_W - float(r.indent))

## The log's rows, newest at the foot: a line longer than the log's width wraps onto a second row, indented (only a
## third row's worth ends in "…"; the prototype's QA read "A drop of blood on Plain Straw Hat: it knows…"), and the
## oldest rows give way so the log never grows past LOG_ROWS toward the tracker.
func log_rows(lines: Array) -> Array:
	var out: Array = []
	for l in lines:
		var a = 1.0 if float(l.t) < 5.0 else 6.0 - float(l.t)
		var col := Color(l.color, a)
		var text := str(l.text)
		var first := str(UiKit.wrap(text, 16, Hud.LOG_W, true)[0])
		out.append({"text": UiKit.fit(first, 16, Hud.LOG_W, true), "indent": 0.0, "color": col})
		var rest := text.substr(first.length()).strip_edges()
		if rest != "": out.append({"text": UiKit.fit(rest, 16, Hud.LOG_W - Hud.LOG_INDENT, true), "indent": Hud.LOG_INDENT, "color": col})
	return out.slice(maxi(0, out.size() - Hud.LOG_ROWS))

## With no character bound (the engine tests' bare player), a plain panel and the cluster's rings.
func draw_legacy() -> void:
	hud.draw_style_box(hud.frame_style, Rect2(22, 22, 310, 82))
	for row in 2:
		var y = 40 + row * 32
		var amount = hud.player.hp if row == 0 else hud.player.qi
		UiKit.draw_text(hud, Tx.t("hud.hp") if row == 0 else Tx.t("hud.qi"), Vector2(38, y + 13), 18, UiKit.HUD_LABEL)
		hud.draw_rect(Rect2(75, y, 237, 16), UiKit.BAR_TROUGH)
		hud.draw_rect(Rect2(77, y + 2, 233 * amount / 100, 12), UiKit.HP if row == 0 else UiKit.QI)
	hud.controls.draw_skill_scroll()
	hud.ring(hud.attack_center, 66, hud.player.attack_time > 0)
	hud.ring(hud.jump_center, Hud.JUMP_R)
	hud.ring(hud.fan_center, 26, hud.player.meditating)
