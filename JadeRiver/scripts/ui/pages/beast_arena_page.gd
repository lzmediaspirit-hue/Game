extends Page
## S46 · The Beast Arena on Market Street: a ladder of ten NPC tamers. Challenge the one above you with your active
## animal (1v1) or three of your animals (3v3); five fights a day; the rank you hold when the week turns pays out.
## The last fight replays as health bars draining.
## P5 (docs/page_identity.md row 36; the Beasts family, §2): the arena pit seen from the stands. An oval sand pit fills
## the timber stands, ringed with a fence; round its rim the eleven banners of the ladder in rank order, rank 1 at the
## top, each tamer's lead animal at its pole's foot, yours in jade and the one you may challenge in gold; inside the pit
## your standing and the last fight replayed as draining bars between the two sides; 1v1 and 3v3 at the pit's gate.
## A challenge raises your banner (0.3 s). The page submits intents only.

const PIT_C := Vector2(640, 382)
const PIT_R := Vector2(400, 196)
const RAISE_S := 0.3

var replay_start := -1.0
var raised_t := -1.0     # when your banner was last raised (a fight fought)

func _init() -> void:
	title = Tx.t("ui.arena.title")
	frame_rect = WINDOW_LARGE
	identity = Identity.new("sand", false, "own", "oval_pit_banner_ring", 0.3)

func content_rect() -> Rect2:
	return frame_rect.grow(-24)

## The stands in rough timber, the oval pit of sand inside them ringed by a fence of posts and two rails, the gate
## at its foot.
func draw_surface(r: Rect2) -> void:
	rounded(r.grow(3), 8.0, UiKit.INK)
	BeastKit.timber(self, r, 61)
	draw_rect(r.grow(-6), Color(UiKit.SURFACE.wood_dark, 0.9), false, 4.0)
	ground(r, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.18))
	draw_colored_polygon(_oval(PIT_R + Vector2(18, 14)), Color(UiKit.INK, 0.45))
	draw_colored_polygon(_oval(PIT_R), UiKit.SURFACE.sand)
	draw_colored_polygon(_oval(PIT_R * 0.72), UiKit.SURFACE.sand.lerp(UiKit.PAPER, 0.12))
	for k in 5:   # raked rings in the sand
		draw_polyline(_oval(PIT_R * (0.3 + 0.13 * k), true), Color(UiKit.BRONZE, 0.18), 1.5, true)
	ground(Rect2(PIT_C.x - 300, PIT_C.y - 170, 600, 340), UiKit.SURFACE.sand)   # where the pit's words stand
	# The fence: two rails round the rim, a post every so often; open at the gate.
	for rail in [0.0, 9.0]:
		draw_polyline(_oval(PIT_R + Vector2(6, 4) - Vector2(0, rail), true), UiKit.SURFACE.wood_dark, 4.0, true)
		draw_polyline(_oval(PIT_R + Vector2(6, 4) - Vector2(0, rail), true), UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.3), 2.0, true)
	for i in 28:
		var a := TAU * i / 28.0
		if absf(a - PI * 0.5) < 0.2: continue
		var p := PIT_C + Vector2(cos(a) * (PIT_R.x + 6), sin(a) * (PIT_R.y + 4))
		draw_rect(Rect2(p - Vector2(3, 14), Vector2(6, 18)), UiKit.SURFACE.wood_dark)
		draw_rect(Rect2(p - Vector2(3, 14), Vector2(2, 18)), UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.3))

func _oval(radii: Vector2, closed := false) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 72:
		pts.append(PIT_C + Vector2(cos(TAU * i / 72.0) * radii.x, sin(TAU * i / 72.0) * radii.y))
	if closed: pts.append(pts[0])
	return pts

func title_rect() -> Rect2:
	return Rect2(frame_rect.position.x + 28, frame_rect.position.y + 16, 250, 52)

func draw_title_mount(r: Rect2) -> void:
	BeastKit.hung_board(self, r, frame_rect.position.y + 2)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var a: Dictionary = Game.pets.arena_state(ch)
	var cfg: Dictionary = Game.pets.arena_cfg()
	var rank := int(a.rank)
	var unranked := int(cfg.get("unranked", 11))
	var opp: Dictionary = Game.pets.arena_opponent(ch)
	# Decision 43: a tour's anchors (the pit, and the ladder's banners round its rim).
	tour_mark("pit", Rect2(PIT_C - PIT_R * 0.72, PIT_R * 1.44))
	tour_mark("ladder", Rect2(PIT_C - PIT_R - Vector2(40, 60), (PIT_R + Vector2(40, 60)) * 2.0))
	_banners(ch, cfg, rank, unranked, opp)
	_standing(cfg, a, rank, unranked, opp)
	if a.get("last", {}).is_empty(): _help(opp)
	else: _replay(a.last)
	_gate(ch, cfg, a, opp)

## The ladder round the rim: the tamers in rank order with you placed at your rank (those at and below it each step
## down one), eleven banners on the eleven posts clockwise from the top, the gate's post left for the gate.
func _banners(ch, cfg: Dictionary, rank: int, unranked: int, opp: Dictionary) -> void:
	var rows: Array = []
	var tamers: Array = (cfg.get("tamers", []) as Array).duplicate()
	tamers.sort_custom(func(x, y): return int(x.rank) < int(y.rank))
	for tm in tamers:
		if int(tm.rank) == rank: rows.append({"you": true})
		rows.append(tm)
	if rank >= unranked: rows.append({"you": true})
	var slots: Array = []
	for j in 12:
		if j != 6: slots.append(-PI * 0.5 + TAU * j / 12.0)
	var lift := 1.0 - unfold()
	for i in mini(rows.size(), slots.size()):
		var row: Dictionary = rows[i]
		var you: bool = row.get("you", false)
		var next: bool = not opp.is_empty() and str(row.get("id", "")) == str(opp.get("id", ""))
		var foot := PIT_C + Vector2(cos(slots[i]) * (PIT_R.x + 4), sin(slots[i]) * (PIT_R.y + 2))
		var side := -1.0 if cos(slots[i]) < -0.2 else 1.0   # the cloth flies outward, away from the pit's middle
		var up := lift
		if you and raised_t >= 0.0 and not UiKit.reduce_motion(): up = maxf(up, 1.0 - clampf((t - raised_t) / RAISE_S, 0.0, 1.0))
		var name := Tx.t("ui.arena.you") % ch.name if you else str(row.name)
		_banner(foot, side, str(i + 1) if not you or rank < unranked else "—", name, UiKit.JADE if you else (UiKit.GOLD if next else _cloth(i)), up, you or next, you)
		var solo: Array = row.get("solo", [])
		if not solo.is_empty(): creature_at(Rect2(foot + Vector2(-side * 44.0 - 18.0, -40), Vector2(36, 36)), _art(str(solo[0].species)))

## A banner on its pole planted at `foot`: a swallow-tailed cloth flying to `side` with the rank inked on it, lowered
## by `down` (0 up the pole, 1 at the foot), and the holder's name on a board hung under it (B18: as long as the name,
## kept inside the stands); `lit` rings the cloth in pale gold.
func _banner(foot: Vector2, side: float, words: String, name: String, col: Color, down: float, lit: bool, you: bool) -> void:
	var top := foot - Vector2(0, 90)
	draw_line(foot, top, UiKit.SURFACE.wood_dark, 4.0, true)
	draw_line(foot + Vector2(-1, 0), top + Vector2(-1, 0), UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.4), 1.5, true)
	draw_circle(top, 4.0, UiKit.GOLD, true, -1.0, true)
	var y := top.y + 4 + down * 30.0
	var x0 := foot.x + (2.0 if side > 0.0 else -54.0)
	var cloth := PackedVector2Array([Vector2(x0, y), Vector2(x0 + 52, y), Vector2(x0 + 52, y + 40), Vector2(x0 + 38, y + 32),
		Vector2(x0 + 26, y + 40), Vector2(x0 + 14, y + 32), Vector2(x0, y + 40)])
	if lit:
		var halo := PackedVector2Array()
		for p in cloth: halo.append(p + (p - Vector2(x0 + 26, y + 20)).normalized() * 3.0)
		draw_colored_polygon(halo, UiKit.PALE_GOLD)
	draw_colored_polygon(cloth, col)
	draw_rect(Rect2(x0, y, 52, 5), col.lerp(UiKit.INK, 0.3))
	inked(Vector2(x0, y + 28), words, 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 52, true)
	var pw := clampf(UiKit.text_width(name, 14) + 24.0, 96.0, 216.0)
	var px := foot.x - 2.0 if side > 0.0 else foot.x + 2.0 - pw
	px = clampf(px, frame_rect.position.x + 14, frame_rect.end.x - 14 - pw)
	var plate := BeastKit.board(self, Rect2(roundf(px), foot.y - 42, pw, 26))
	text(Vector2(plate.position.x, plate.position.y + 19), fit(name, 14, plate.size.x - 12), 14, UiKit.PALE_GOLD if you else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, plate.size.x)

## The tamers' cloths: the kit's own colours, one after another round the ring.
func _cloth(i: int) -> Color:
	var cloths := [UiKit.BLOOD, UiKit.DEEP_TEAL, UiKit.BRONZE, UiKit.SURFACE.lacquer, UiKit.JADE_SHADOW, UiKit.SOUL.lerp(UiKit.INK, 0.4)]
	return cloths[i % cloths.size()]

## In the pit: your rank, the day's fights and what the week pays, and who you face next.
func _standing(cfg: Dictionary, a: Dictionary, rank: int, unranked: int, opp: Dictionary) -> void:
	var w := 520.0
	var x := PIT_C.x - w * 0.5
	text(Vector2(x, 246), Tx.t("ui.arena.rank") % rank if rank < unranked else Tx.t("ui.arena.unranked"), 26, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, w, true)
	var fights_left := int(cfg.get("fights_per_day", 5)) - int(a.get("fights", 0))
	text(Vector2(x, 270), fit(Tx.t("ui.arena.fights_left") % [fights_left, int(cfg.get("fights_per_day", 5))] + "  ·  " + _week_line(cfg, rank), 14, w), 14, UiKit.PAPER_INK,
		HORIZONTAL_ALIGNMENT_CENTER, w)
	var next := Tx.t("sim.pet.arena_top") if opp.is_empty() else Tx.t("ui.arena.next") % [str(opp.name), int(opp.rank)]
	text(Vector2(x, 294), fit(next, 16, w), 16, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, w)

func _week_line(cfg: Dictionary, rank: int) -> String:
	for rw in cfg.get("rewards", []):
		if rank >= int(rw.ranks[0]) and rank <= int(rw.ranks[1]):
			return Tx.plural("ui.arena.week_pays", int(rw.get("spirit_stone", 0))) % int(rw.get("spirit_stone", 0))
	return Tx.t("ui.arena.week_none")

## Before any fight: the next tamer's two teams on the sand and how the arena works (B18: all of it).
func _help(opp: Dictionary) -> void:
	var w := 540.0
	var x := PIT_C.x - w * 0.5
	var y := 310.0
	if not opp.is_empty():
		for mi in 2:
			var mode: String = ["solo", "trio"][mi]
			var tm: Array = opp.get(mode, [])
			var cx := PIT_C.x + (mi - 0.5) * 240.0
			text(Vector2(cx - 90, y + 14), Tx.t("ui.arena.mode_" + mode), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, 180)
			for k in tm.size():
				var at := Vector2(cx - tm.size() * 26.0 + k * 52.0, y + 20)
				creature_at(Rect2(at, Vector2(48, 44)), _art(str(tm[k].species)))
				text(at + Vector2(0, 58), Tx.t("ui.arena.lv") % int(tm[k].level), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, 48)
		y += 80
	para(Rect2(x, y, w, 540 - y), Tx.t("ui.arena.help"), 14, UiKit.PAPER_INK)

## The last fight, replayed at 8x: your side at the left and theirs at the right face each other across the pit, each
## animal's health bar draining as the log's blows land.
func _replay(last: Dictionary) -> void:
	if replay_start < 0.0: replay_start = t
	var rt := (t - replay_start) * 8.0
	if UiKit.reduce_motion(): rt = float(last.get("t", 0.0))   # Reduce: the bars show their end values
	var hp := {"a": (last.a as Array).map(func(m): return float(m.max_hp)), "b": (last.b as Array).map(func(m): return float(m.max_hp))}
	var skill_flash := ""
	for e in last.get("log", []):
		if float(e.t) > rt: break
		var foe := "b" if str(e.side) == "a" else "a"
		var ti := int(e.target)
		if ti < (hp[foe] as Array).size(): hp[foe][ti] = maxf(0.0, float(hp[foe][ti]) - float(e.dmg))
		if e.get("skill", false) and float(e.t) > rt - 1.0: skill_flash = str(e.side)
	text(Vector2(PIT_C.x - 200, 322), Tx.t("ui.arena.last") % Tx.t("ui.arena.mode_" + str(last.mode)), 16, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, 400)
	for si in 2:
		var side: String = ["a", "b"][si]
		var team: Array = last[side]
		for k in team.size():
			var yy := 338.0 + k * 50.0
			var frac := float(hp[side][k]) / maxf(1.0, float(team[k].max_hp))
			var bar_r := Rect2(PIT_C.x - 236, yy + 12, 200, 24) if si == 0 else Rect2(PIT_C.x + 36, yy + 12, 200, 24)
			var fig := Rect2(bar_r.position.x - 58, yy, 52, 44) if si == 0 else Rect2(bar_r.end.x + 6, yy, 52, 44)
			creature_at(fig, _art(str(team[k].species)))
			bar(bar_r, frac, UiKit.BRIGHT_JADE if side == "a" else UiKit.RED, fit(str(team[k].name), BAR_LABEL, bar_r.size.x - 16))
		if skill_flash == side:
			text(Vector2(PIT_C.x - 236 + si * 272, 338 + team.size() * 50 + 10), Tx.t("ui.arena.skill"), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, 200)
	if rt >= float(last.get("t", 0.0)):
		var won: bool = last.get("won", false)
		inked(Vector2(PIT_C.x - 150, 522), Tx.t("ui.arena.won") if won else Tx.t("ui.arena.lost"), 30, UiKit.GOLD if won else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 300, true)
	queue_redraw()

## The pit's gate at its foot: the two challenges.
func _gate(ch, cfg: Dictionary, a: Dictionary, opp: Dictionary) -> void:
	var gate := Rect2(PIT_C.x - 196, PIT_C.y + PIT_R.y - 6, 392, 24)
	rounded(gate, 4.0, UiKit.SURFACE.wood_dark)
	draw_rect(Rect2(gate.position.x + 6, gate.position.y + 4, gate.size.x - 12, 3), UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.3))
	var fights_left := int(cfg.get("fights_per_day", 5)) - int(a.get("fights", 0))
	var bw := 184.0
	for mi in 2:
		var mode: String = ["solo", "trio"][mi]
		var team: Array = Game.pets.arena_team(ch, mode)
		var need := 1 if mode == "solo" else 3
		var why := Tx.t("sim.pet.arena_top") if opp.is_empty() else (Tx.t("sim.pet.arena_tired") if fights_left <= 0 else Tx.t("sim.pet.arena_team_" + mode))
		btn(Rect2(PIT_C.x - bw - 6 + mi * (bw + 12), gate.end.y - 8, bw, BTN_H), Tx.t("ui.arena.challenge_" + mode), "fight", mode, mi == 0,
			not opp.is_empty() and fights_left > 0 and team.size() >= need, why, 18)

func _art(species: String) -> String:
	return str(ContentDB.entry("pets", species).get("art", species))

func on_action(id: String, data) -> void:
	match id:
		"fight":
			var r := submit({"type": "arena_challenge", "mode": str(data)})
			if r.get("ok", false):
				replay_start = -1.0
				raised_t = t
	queue_redraw()
