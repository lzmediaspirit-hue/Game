extends Page
## S46 · The Beast Arena on Market Street: a ladder of ten NPC tamers. Challenge the one above you with your active
## animal (1v1) or three of your animals (3v3); five fights a day; the rank you hold when the week turns pays out.
## The last fight replays as health bars draining.

var replay_start := -1.0

func _init() -> void:
	title = Tx.t("ui.arena.title")
	frame_rect = Rect2(130, 60, 1020, 600)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var a: Dictionary = Game.pets.arena_state(ch)
	var cfg: Dictionary = Game.pets.arena_cfg()
	var rank := int(a.rank)
	var unranked := int(cfg.get("unranked", 11))
	# Left: the ladder, with you placed at your rank (the tamers at and below it each step down one).
	var left := Rect2(content.position, Vector2(390, content.size.y))
	panel(left)
	var rows: Array = []
	var tamers: Array = (cfg.get("tamers", []) as Array).duplicate()
	tamers.sort_custom(func(x, y): return int(x.rank) < int(y.rank))
	for t in tamers:
		if int(t.rank) == rank: rows.append({"you": true})
		rows.append(t)
	if rank >= unranked: rows.append({"you": true})
	list("ladder", left.grow(-10), rows.size(), 52, func(i: int, rr: Rect2):
		var row: Dictionary = rows[i]
		var shown_rank := i + 1
		if row.get("you", false):
			panel(rr, "minor_panel", "selected")
			text(rr.position + Vector2(12, 33), str(shown_rank) if rank < unranked else "—", 20, UiKit.GOLD)
			text(rr.position + Vector2(56, 33), fit(Tx.t("ui.arena.you") % ch.name, 18, rr.size.x - 70), 18, UiKit.PALE_GOLD)
			return
		panel(rr, "minor_panel")
		text(rr.position + Vector2(12, 33), str(shown_rank), 20, UiKit.MIST)
		var solo: Array = row.get("solo", [])
		if not solo.is_empty(): creature_at(Rect2(rr.position + Vector2(44, 4), Vector2(44, 44)), _art(str(solo[0].species)))
		text(rr.position + Vector2(96, 33), fit(str(row.name), 17, rr.size.x - 104), 17, UiKit.PAPER)
	)
	# Right: your standing, the tamer above you, the challenge buttons and the last fight.
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(right)
	var px := right.position.x + 22
	var fights_left := int(cfg.get("fights_per_day", 5)) - int(a.get("fights", 0))
	heading(Vector2(px, right.position.y + 40), Tx.t("ui.arena.rank") % rank if rank < unranked else Tx.t("ui.arena.unranked"), right.size.x - 44)
	text(Vector2(px, right.position.y + 72), fit(Tx.t("ui.arena.fights_left") % [fights_left, int(cfg.get("fights_per_day", 5))] + "  ·  " + _week_line(cfg, rank),
		15, right.size.x - 44), 15, UiKit.MIST)
	var opp: Dictionary = Game.pets.arena_opponent(ch)
	var y := right.position.y + 90
	if opp.is_empty():
		para(Rect2(px, y + 10, right.size.x - 44, 60), Tx.t("sim.pet.arena_top"), 18, UiKit.PALE_GOLD)
	else:
		var card := Rect2(px, y, right.size.x - 44, 150)
		panel(card, "minor_panel")
		text(card.position + Vector2(14, 28), fit(Tx.t("ui.arena.next") % [str(opp.name), int(opp.rank)], 18, card.size.x - 28), 18, UiKit.GOLD)
		for mi in 2:
			var mode: String = ["solo", "trio"][mi]
			var col := card.position + Vector2(14 + mi * (card.size.x * 0.5), 40)
			text(col + Vector2(0, 14), Tx.t("ui.arena.mode_" + mode), 14, UiKit.MIST)
			var tm: Array = opp.get(mode, [])
			for k in tm.size():
				creature_at(Rect2(col + Vector2(k * 56, 20), Vector2(52, 52)), _art(str(tm[k].species)))
				text(col + Vector2(k * 56, 86), Tx.t("ui.arena.lv") % int(tm[k].level), 13, UiKit.MIST)
		y += 160
		for mi in 2:
			var mode2: String = ["solo", "trio"][mi]
			var team: Array = Game.pets.arena_team(ch, mode2)
			var need := 1 if mode2 == "solo" else 3
			var bw := (right.size.x - 44 - 12) / 2.0
			btn(Rect2(px + mi * (bw + 12), y, bw, 50), Tx.t("ui.arena.challenge_" + mode2), "fight", mode2, mi == 0,
				fights_left > 0 and team.size() >= need, Tx.t("sim.pet.arena_tired") if fights_left <= 0 else Tx.t("sim.pet.arena_team_" + mode2), 17)
		y += 62
	_replay(ch, a, Rect2(px, y, right.size.x - 44, right.end.y - y - 12))

func _week_line(cfg: Dictionary, rank: int) -> String:
	for rw in cfg.get("rewards", []):
		if rank >= int(rw.ranks[0]) and rank <= int(rw.ranks[1]):
			return Tx.t("ui.arena.week_pays") % int(rw.get("spirit_stone", 0))
	return Tx.t("ui.arena.week_none")

## The last fight, replayed at 8x: each side's health bars drain as the log's blows land.
func _replay(_ch, a: Dictionary, r: Rect2) -> void:
	var last: Dictionary = a.get("last", {})
	if last.is_empty() or r.size.y < 80:
		para(r, Tx.t("ui.arena.help"), 15, UiKit.MIST, 4)
		return
	if replay_start < 0.0: replay_start = t
	var rt := (t - replay_start) * 8.0
	var hp := {"a": (last.a as Array).map(func(m): return float(m.max_hp)), "b": (last.b as Array).map(func(m): return float(m.max_hp))}
	var skill_flash := ""
	for e in last.get("log", []):
		if float(e.t) > rt: break
		var foe := "b" if str(e.side) == "a" else "a"
		var ti := int(e.target)
		if ti < (hp[foe] as Array).size(): hp[foe][ti] = maxf(0.0, float(hp[foe][ti]) - float(e.dmg))
		if e.get("skill", false) and float(e.t) > rt - 1.0: skill_flash = str(e.side)
	text(r.position + Vector2(0, 16), Tx.t("ui.arena.last") % Tx.t("ui.arena.mode_" + str(last.mode)), 15, UiKit.GOLD)
	var colw := (r.size.x - 20) / 2.0
	for si in 2:
		var side: String = ["a", "b"][si]
		var team: Array = last[side]
		var x := r.position.x + si * (colw + 20)
		for k in team.size():
			var yy := r.position.y + 28 + k * 34
			creature_at(Rect2(x, yy - 2, 30, 30), _art(str(team[k].species)))
			var frac := float(hp[side][k]) / maxf(1.0, float(team[k].max_hp))
			bar(Rect2(x + 36, yy + 4, colw - 40, 22), frac, UiKit.BRIGHT_JADE if side == "a" else UiKit.RED, fit(str(team[k].name), 13, colw - 60))
		if skill_flash == side: text(Vector2(x, r.position.y + 28 + team.size() * 34 + 12), Tx.t("ui.arena.skill"), 14, UiKit.PALE_GOLD)
	if rt >= float(last.get("t", 0.0)):
		var won: bool = last.get("won", false)
		text(Vector2(r.position.x, r.end.y - 8), Tx.t("ui.arena.won") if won else Tx.t("ui.arena.lost"), 22, UiKit.GOLD if won else UiKit.MIST)
	queue_redraw()

func _art(species: String) -> String:
	return str(ContentDB.entry("pets", species).get("art", species))

func on_action(id: String, data) -> void:
	match id:
		"fight":
			var r := submit({"type": "arena_challenge", "mode": str(data)})
			if r.get("ok", false): replay_start = -1.0
	queue_redraw()
