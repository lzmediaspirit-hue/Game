class_name HudTopStack
extends HudPart
## The top centre (P5a), one thing under another: a run's seconds, the room's name, a room event, a tribulation, a
## fortune card, the toasts and a caption; and the boss bar above them.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

## The top centre (P5a), one thing under another so none covers another, from under the party chips (or under the boss
## bar) down to the clear zone: the room's name as you enter, a room event or a tribulation under way, a fortune card,
## the toasts (408 wide, 8 apart; a toast with no room waits), a caption.
func draw(c) -> void:
	var y := Hud.TOP_STACK_BOSS if room_boss() != null else Hud.TOP_STACK
	y = _draw_run_banner(c, y)
	if not band_on_top():   # a moment's band there says the same, and the two drawn together read as neither
		y = _draw_banner(y)
		y = _draw_event(c, y)
	y = _draw_tribulation(c, y)
	y = _draw_vignette(y)
	y = _draw_toasts(y)
	_draw_caption(y)

## S43 rule 15: while a thief runs or a timed route is on, the seconds sit at the top of the screen (first in the top
## centre's stack).
func _draw_run_banner(c, y0: float) -> float:
	if c == null: return y0
	var label := ""
	var secs := 0.0
	var ch: Dictionary = Game.world.chases.get(c.id, {})
	var run: Dictionary = Game.world.runs.get(c.id, {})
	if not ch.is_empty():
		label = Tx.t("hud.chase_banner")
		secs = Game.sim_time - float(ch.start)
	elif not run.is_empty():
		var o: Dictionary = Game.room_rt.object_def(str(run.object)) if Game.room_rt else {}
		if o.is_empty(): return y0
		label = str(o.route.get("name", ""))
		secs = Game.sim_time - float(run.start)
	else:
		return y0
	var text := "%s   %.1f s" % [label, secs]
	var w := UiKit.text_width(text, 22) + 40
	var r := Rect2(640 - w * 0.5, y0, w, 40)
	hud.draw_rect(r, UiKit.PLATE)
	hud.draw_rect(r, Color(UiKit.GOLD, 0.7), false, 1.5)
	UiKit.draw_text(hud, text, r.position + Vector2(0, 28), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	return r.end.y + 8.0

func _draw_banner(y: float) -> float:
	if hud.banner.text == "" or hud.banner.t > 3.4 or not hud.shown("room_banner"): return y
	var a := clampf(hud.banner.t / 0.3, 0, 1) * clampf((3.4 - hud.banner.t) / 0.5, 0, 1)
	var slide := (1.0 - clampf(hud.banner.t / 0.3, 0, 1)) * -12.0
	UiKit.draw_text(hud, str(hud.banner.text), Vector2(340, y + 32 + slide), 34, Color(UiKit.PALE_GOLD, a), HORIZONTAL_ALIGNMENT_CENTER, 600, true, true)
	if str(hud.banner.sub) != "": UiKit.draw_text(hud, str(hud.banner.sub), Vector2(340, y + 56 + slide), 16, Color(UiKit.MIST, a), HORIZONTAL_ALIGNMENT_CENTER, 600)
	return y + 68.0

## A room event under way (a survival rite, a Temper trial, a siege): its name, the time left and its rule.
func _draw_event(c, y0: float) -> float:
	if Game.room_rt == null or not Game.room_rt.event.get("active", false): return y0
	var ev: Dictionary = Game.room_rt.event
	var rule := ""
	var danger := false
	if float(ev.get("hp_floor", 0.0)) > 0.0:
		rule = Tx.t("hud.event_rule.hp_floor") % int(round(float(ev.hp_floor) * 100))
		danger = c.pools.hp < c.pools.max_hp * (float(ev.hp_floor) + 0.1)
	if not (ev.get("kill_count", {}) as Dictionary).is_empty():
		var foe := Tx.t("hud.event_rule.foes") if str(ev.kill_count.enemy) == "*" else str(ContentDB.entry("enemies", str(ev.kill_count.enemy)).get("name", ""))
		rule = Tx.t("hud.event_rule.kills") % [foe, int(ev.get("kills", 0)), int(ev.kill_count.get("count", 1))]
	elif str(ev.get("win_on_kill", "")) != "" and ev.has("floor"):
		rule = Tx.t("hud.event_rule.guardian") % ContentDB.name_of("enemies", str(ev.win_on_kill))
	elif ev.has("floor"):
		rule = Tx.t("hud.event_rule.survive")
	if ev.has("ground_grace_s"):
		rule = Tx.t("hud.event_rule.ground")
		danger = float(ev.get("ground_s", 0.0)) > 0.0
	# v1.2 the lantern defence: the lantern's light, and a warning when it gutters.
	if ev.get("lantern") is Dictionary and not ev.lantern.is_empty():
		var light := float(ev.get("light", 100.0))
		rule = Tx.t("hud.event_rule.lantern") % int(ceil(light))
		danger = light < 35.0
	var r := Rect2(470, y0, 340, 52 if rule != "" else 34)
	hud.draw_style_box(UiKit.style("toast"), r)
	var left := maxf(0.0, float(ev.get("remaining", 0.0)))
	var ev_name := Tx.t("hud.tower_floor") % int(ev.floor) if ev.has("floor") else ContentDB.text("event." + str(ev.get("id", "")))
	UiKit.draw_text(hud, ev_name, r.position + Vector2(14, 23), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 240)
	# Decision 45: an event whose time is only a last resort (`clock: false`, the Hollow Night: it ends when its boss
	# falls) shows no countdown, which would read as a time to hold out for.
	if ev.get("clock", true):
		UiKit.draw_text(hud, UiKit.clock(left), r.position + Vector2(r.size.x - 84, 23), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 70)
		var frac := left / maxf(1.0, float(ev.get("duration", 1.0)))
		hud.draw_rect(Rect2(r.position + Vector2(12, 29), Vector2(r.size.x - 24, 3)), Color(UiKit.INK, 0.8))
		hud.draw_rect(Rect2(r.position + Vector2(12, 29), Vector2((r.size.x - 24) * clampf(frac, 0, 1), 3)), UiKit.BRIGHT_JADE)
	if rule != "": UiKit.draw_text(hud, rule, r.position + Vector2(14, 46), 14, UiKit.RED_TEXT if danger else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
	return r.end.y + 8.0

## S48 heavenly tribulation: bolts struck and to come, and whether a ring is closing now.
func _draw_tribulation(c, y0: float) -> float:
	var tv: Dictionary = Game.progression.tribulation_view(c.id)
	if tv.is_empty(): return y0
	var r := Rect2(470, y0, 340, 52)
	hud.draw_style_box(UiKit.style("toast"), r)
	UiKit.draw_text(hud, Tx.t("hud.tribulation_title"), r.position + Vector2(14, 23), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 200)
	UiKit.draw_text(hud, Tx.t("hud.tribulation_count") % [int(tv.index), int(tv.total)], r.position + Vector2(r.size.x - 144, 23), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 130)
	var n := int(tv.total)
	var w := (r.size.x - 28) / maxf(1.0, float(n))
	for i in n:
		var cell := Rect2(r.position.x + 14 + i * w, r.position.y + 32, maxf(2.0, w - 2), 6)
		hud.draw_rect(cell, UiKit.SKY if i < int(tv.index) else (UiKit.GOLD if i == int(tv.index) and not (tv.warn as Dictionary).is_empty() else Color(UiKit.INK, 0.8)))
	if not (tv.warn as Dictionary).is_empty():
		UiKit.draw_text(hud, Tx.t("hud.tribulation_move"), r.position + Vector2(14, 51), 16, UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
		return r.end.y + 16.0
	return r.end.y + 8.0

## A fortune encounter (S49): a card that fades in under the room banner, long enough to read, then fades away.
func _draw_vignette(y0: float) -> float:
	if str(hud.vignette.title) == "" or float(hud.vignette.t) > Hud.VIGNETTE_S: return y0
	var tv := float(hud.vignette.t)
	var a := clampf(tv / 0.4, 0, 1) * clampf((Hud.VIGNETTE_S - tv) / 0.8, 0, 1)
	var w := 560.0
	var lines: Array = []
	var cur := ""
	for word in str(hud.vignette.text).split(" "):
		var cand: String = word if cur == "" else cur + " " + word
		if UiKit.text_width(cand, 18) > w - 48 and cur != "":
			lines.append(cur)
			cur = word
		else: cur = cand
	lines.append(cur)
	var r := Rect2(640 - w / 2.0, y0, w, 86 + lines.size() * 23)
	hud.draw_style_box(UiKit.style("toast"), r)
	hud.draw_rect(Rect2(r.position + Vector2(0, 0), Vector2(r.size.x, 3)), Color(UiKit.GOLD, 0.8 * a))
	UiKit.draw_text(hud, Tx.t("hud.fortune_label"), r.position + Vector2(24, 30), 14, Color(UiKit.GOLD, a))
	UiKit.draw_text(hud, str(hud.vignette.title), r.position + Vector2(24, 58), 22, Color(UiKit.PALE_GOLD, a), HORIZONTAL_ALIGNMENT_LEFT, w - 48, true, true)
	var y := r.position.y + 86
	for ln in lines:
		UiKit.draw_text(hud, str(ln), Vector2(r.position.x + 24, y), 18, Color(UiKit.PAPER, a))
		y += 23
	return r.end.y + 8.0

## Toasts at the top centre (docs/mockups/20_states: over play, under the chips), 408 wide and 8 apart. The first always
## shows; the next only while it stays above the clear zone, and the rest wait their turn.
func _draw_toasts(y: float) -> float:
	hud.toasts_fit = 0
	if moment_on_screen(): return y
	for r in toast_rects(y):
		var tt: Dictionary = hud.toasts[hud.toasts_fit]
		var sub := str(tt.get("sub", ""))
		var a := clampf(tt.t / 0.2, 0, 1) * clampf((float(tt.get("life", 3.2)) - tt.t) / 0.4, 0, 1)
		hud.draw_style_box(UiKit.style("toast"), r)
		var col = UiKit.PALE_GOLD if tt.kind in ["unlock", "gold"] else (UiKit.RED_TEXT if tt.kind == "danger" else UiKit.BRIGHT_JADE)
		UiKit.draw_text(hud, UiKit.fit(str(tt.text), 20, 376), r.position + Vector2(16, 31), 20, Color(col, a), HORIZONTAL_ALIGNMENT_LEFT, 376)
		var row_y := 58.0
		for row in toast_sub_rows(sub):
			UiKit.draw_text(hud, str(row), r.position + Vector2(16, row_y), 18, Color(UiKit.PAPER, a), HORIZONTAL_ALIGNMENT_LEFT, 376)
			row_y += Hud.TOAST_ROW
		y = r.end.y + 8.0
		hud.toasts_fit += 1
	return y

## A toast's second line, wrapped to two rows at most (a spar's lesson, said whole), the second cut if it must be.
static func toast_sub_rows(sub: String) -> Array:
	if sub == "": return []
	var rows: Array = UiKit.wrap(sub, 18, 376)
	if rows.size() <= 1: return [UiKit.fit(sub, 18, 376)]
	var first := str(rows[0])
	return [first, UiKit.fit(sub.substr(first.length()).strip_edges(), 18, 376)]

## Where the toasts stand from `y` down: the first always, each next only while it ends above the clear zone.
func toast_rects(y: float) -> Array:
	var out: Array = []
	for tt in hud.toasts:
		var rows := toast_sub_rows(str(tt.get("sub", ""))).size()
		var h := 48.0 if rows == 0 else 74.0 + Hud.TOAST_ROW * (rows - 1)
		if not out.is_empty() and y + h > Hud.CLEAR_ZONE.position.y: break
		out.append(Rect2(436, y, 408, h))
		y += h + 8.0
	return out

func _draw_caption(y: float) -> void:
	if hud.caption.text == "" or float(hud.caption.t) > 2.6: return
	var a := clampf((2.6 - float(hud.caption.t)) / 0.4, 0.0, 1.0)
	var w := 520.0
	hud.draw_rect(Rect2(640 - w / 2.0, y, w, 30), Color(UiKit.INK, 0.55 * a))
	UiKit.draw_text(hud, "[" + str(hud.caption.text) + "]", Vector2(640 - w / 2.0, y + 21), 18, Color(UiKit.PAPER, a), HORIZONTAL_ALIGNMENT_CENTER, w)

func moment_on_screen() -> bool:
	return is_instance_valid(hud.moments) and hud.moments.screen_busy()

func band_on_top() -> bool:
	return is_instance_valid(hud.moments) and hud.moments.band_on_top()

## The boss in the room, if one lives (with two, the one furthest into the fight: the lowest share of its HP).
func room_boss() -> EnemyState:
	if Game.room_rt == null: return null
	var boss: EnemyState = null
	for e in Game.room_rt.enemies.values():
		if e.alive and e.is_boss() and e.team == "enemy" and (boss == null or e.pools.hp / maxf(1.0, e.pools.max_hp) < boss.pools.hp / maxf(1.0, boss.pools.max_hp)): boss = e
	return boss

## The boss bar (mockup 01): the name in the display face with its Level and phase, an ember fill on a dark trough, a
## notch at each phase's share of HP (gold once passed, the next one lit) with what it brings under it, and the share
## left on the bar.
func draw_boss() -> void:
	var boss := room_boss()
	if boss == null: return
	var r := Rect2(400, 130, 480, 18)
	var phases: Array = boss.def.get("phases", [])
	var at := int(boss.ai.get("phase", -1))
	var frac := clampf(boss.pools.hp / maxf(1.0, boss.pools.max_hp), 0.0, 1.0)
	var name_s := boss.display_name()
	var sub := Tx.t("hud.boss_phase") % [boss.level, at + 2, phases.size() + 1] if not phases.is_empty() else Tx.t("hud.level_stop") % boss.level
	var nw := UiKit.text_width(name_s, 26, true)
	var x0 := 640.0 - (nw + 10.0 + UiKit.text_width(sub, 16, true)) * 0.5
	UiKit.draw_text(hud, name_s, Vector2(x0, 118), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true, true)
	UiKit.draw_outlined(hud, sub, Vector2(x0 + nw + 10.0, 117), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 240)
	hud.draw_rect(r.grow(3), UiKit.INK)
	hud.draw_rect(r, Color(UiKit.BLOOD, 0.3))
	var last := 0.0
	for ph in phases:
		if ph.has("below"): last = float(ph.below) if last == 0.0 else minf(last, float(ph.below))
	if last > 0.0: hud.draw_rect(Rect2(r.position, Vector2(r.size.x * last, r.size.y)), Color(UiKit.BLOOD, 0.35))
	var fw := r.size.x * frac
	if fw > 0.5:
		var top := UiKit.WARNING.lerp(UiKit.PALE_GOLD, 0.2)
		var mid := UiKit.WARNING.lerp(UiKit.RED, 0.5)
		var low := UiKit.RED.lerp(UiKit.BRONZE, 0.45)
		var ym := r.position.y + r.size.y * 0.55
		hud.draw_polygon(PackedVector2Array([r.position, r.position + Vector2(fw, 0), Vector2(r.position.x + fw, ym), Vector2(r.position.x, ym)]), PackedColorArray([top, top, mid, mid]))
		hud.draw_polygon(PackedVector2Array([Vector2(r.position.x, ym), Vector2(r.position.x + fw, ym), r.end - Vector2(r.size.x - fw, 0), Vector2(r.position.x, r.end.y)]), PackedColorArray([mid, mid, low, low]))
		hud.draw_line(r.position + Vector2(1, 2), r.position + Vector2(maxf(1.0, fw - 1.0), 2), Color(UiKit.PALE_GOLD, 0.45), 2)
	# Decision 45: a boss that cannot be beaten yet (the first boss awake) shows what its hide holds: the bar under its
	# floor hatched over in stone, the floor's edge marked, and the word under it; blows that reach it glance off.
	var hide := float(boss.ai.get("hp_floor", 0.0))
	if hide > 0.0:
		var hw := r.size.x * hide
		hud.draw_rect(Rect2(r.position, Vector2(hw, r.size.y)), Color(UiKit.INK, 0.5))
		for k in range(0, int(hw) - 4, 7):
			hud.draw_line(Vector2(r.position.x + k, r.end.y - 1), Vector2(r.position.x + k + 6, r.position.y + 1), Color(UiKit.MIST, 0.4), 1.0)
		hud.draw_rect(Rect2(r.position.x + hw - 1.5, r.position.y - 4, 3, r.size.y + 8), UiKit.MIST)
		UiKit.draw_outlined(hud, Tx.t("hud.boss_hide"), Vector2(r.position.x, 172), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, hw - 8.0)
	UiKit.draw_outlined(hud, "%d%%" % int(round(frac * 100.0)), Vector2(r.position.x, r.position.y + 15), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	# The notches, and under each what the phase brings: the next one's caption always, the others where they fit.
	var nxt := -1
	for i in phases.size():
		if i > at and phases[i].has("below"):
			nxt = i
			break
	var taken: Array = []
	var order: Array = range(phases.size())
	if nxt >= 0:
		order.erase(nxt)
		order.push_front(nxt)
	for i in order:
		var ph: Dictionary = phases[i]
		if not ph.has("below"): continue
		var x := r.position.x + r.size.x * float(ph.below)
		var done: bool = int(i) <= at
		hud.draw_rect(Rect2(x - 2.5, r.position.y - 9, 5, 36), UiKit.INK)
		hud.draw_rect(Rect2(x - 1.5, r.position.y - 8, 3, 34), UiKit.PALE_GOLD)
		var dia := PackedVector2Array([Vector2(x, r.position.y - 16), Vector2(x + 6, r.position.y - 10), Vector2(x, r.position.y - 4), Vector2(x - 6, r.position.y - 10)])
		if i == nxt: hud.draw_circle(Vector2(x, r.position.y - 10), 9.0, Color(UiKit.RED, 0.35))
		hud.draw_colored_polygon(dia, UiKit.GOLD if done else (UiKit.RED if i == nxt else UiKit.DEEP_TEAL))
		hud.draw_polyline(dia + PackedVector2Array([dia[0]]), UiKit.PALE_GOLD, 1.5)
		var cap := Tx.t("hud.boss_notch") % [int(round(float(ph.below) * 100.0)), _phase_words(ph, done)]
		var cw := UiKit.text_width(cap, 14, true)
		# Centred under its notch, or leaning away from a caption already there (ending at the notch, or starting at it).
		for left in [x - cw * 0.5, x + 10.0 - cw, x - 10.0]:
			var cr := Rect2(left - 4.0, 158, cw + 8.0, 18)
			if taken.any(func(o): return (o as Rect2).intersects(cr)): continue
			taken.append(cr)
			UiKit.draw_outlined(hud, cap, Vector2(left, 172), 14, UiKit.PALE_GOLD if i == nxt else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, cw + 4.0)
			break

## What a boss's phase brings, in a few words (a summons names who comes, and is ticked once it has come).
func _phase_words(ph: Dictionary, done: bool) -> String:
	var act := str(ph.get("action", ""))
	if act == "summon":
		var who := str(ph.get("summon", ""))
		if who == "": return Tx.t("hud.phase_help")
		return (Tx.t("hud.phase_summoned") if done else Tx.t("hud.phase_summon")) % ContentDB.name_of("enemies", who)
	if act in ["enrage", "dig_in", "drink_wine", "self_detonate", "awaken"]: return Tx.t("hud.phase_" + act)
	return Tx.t("hud.phase_turn")
