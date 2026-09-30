extends Page
## Notice board (S19/S20): today's sect missions and the open side quests nearby; S49: the town's bounties on named
## targets, two taken at a time, each once a day.
## P5 (docs/page_identity.md row 21; no mockup, drawn from its row): the town wall where the posters are pasted one over
## another. Grey brick with its mortar; the wanted posters pasted at different places across it, the chosen one largest
## and on top with its Take strip at its foot, the reward stamped in red, torn strips of older posters between; the
## Board tab's missions and requests as small handbills, and each tab keeps the other's in one corner.

const WALL := Rect2(64, 32, 1152, 656)
const CORNER := Rect2(848, 120, 336, 540)   # the other tab's handbills or posters
const BIG := Vector2(312, 470)              # the chosen poster
const SMALL := Vector2(236, 330)            # the others
const HANDBILL := Vector2(350, 64)


var chosen := ""          # the bounty whose poster is on top
var likeness: Node2D      # the target's figure on the chosen poster, drawn from its own layers
var took_at := -1.0       # when a strip was torn off (the poster is slapped on as the page opens)

func _init() -> void:
	title = Tx.t("ui.notice.notice_board")
	tabs = [{"id": "board", "label": Tx.t("ui.notice.tab_board")}, {"id": "bounties", "label": Tx.t("ui.notice.tab_bounties")}]
	identity = Identity.new("stone", false, "own", "poster_collage_on_wall", 0.2)

func content_rect() -> Rect2:
	return Rect2(88, 112, 1104, 560)

## Grey brick in its courses with the mortar between, a paste stain here and there; a timber lintel along the top.
func draw_surface(r: Rect2) -> void:
	rounded(r.grow(2), 6.0, UiKit.INK)
	rounded(r, 5.0, UiKit.SURFACE.stone.lerp(UiKit.PAPER, 0.22))
	var course := 0
	var y := r.position.y + 64.0
	while y < r.end.y - 4.0:
		var x := r.position.x + 4.0 - (32.0 if course % 2 == 1 else 0.0)
		var i := course * 7
		while x < r.end.x - 4.0:
			var brick := Rect2(maxf(x, r.position.x + 4.0), y, minf(62.0, r.end.x - 4.0 - maxf(x, r.position.x + 4.0)), 22.0)
			if brick.size.x > 2.0: draw_rect(brick, UiKit.SURFACE.stone.lerp(UiKit.INK, float(i % 5) * 0.04))
			x += 64.0
			i += 3
		course += 1
		y += 24.0
	ground(Rect2(r.position + Vector2(0, 64), r.size - Vector2(0, 64)), UiKit.SURFACE.stone)
	for s in [[180, 640, 70], [760, 150, 50], [1100, 600, 60], [520, 420, 44]]:
		glow(Rect2(s[0] - s[2] * 0.5, s[1] - s[2] * 0.5, s[2], s[2]), Color(UiKit.BRONZE, 0.18))
	# The lintel.
	var lintel := Rect2(r.position, Vector2(r.size.x, 64))
	vshade(lintel, UiKit.SURFACE.wood, UiKit.SURFACE.wood_dark)
	draw_rect(Rect2(lintel.position.x, lintel.end.y - 3, lintel.size.x, 3), UiKit.INK)
	ground(lintel, UiKit.SURFACE.wood_dark)

func title_rect() -> Rect2:
	return Rect2(470, 40, 340, 60)

## The title on a black lacquered signboard hung from the lintel.
func draw_title_mount(r: Rect2) -> void:
	for x in [r.position.x + 40, r.end.x - 40]: draw_line(Vector2(x, 32), Vector2(x, r.position.y + 6), UiKit.SURFACE.hemp.lerp(UiKit.BRONZE, 0.5), 3.0, true)
	rounded(r.grow(3), 6.0, UiKit.INK)
	rounded(r.grow(1), 5.0, UiKit.GOLD)
	rounded(r, 4.0, UiKit.SURFACE.lacquer_black)

func tab_rects() -> Array:
	return [Rect2(96, 44, 128, 48), Rect2(236, 44, 148, 48)]

## The tabs are two handbills tacked to the lintel; the open one fresh, the other yellowed.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	var paper := RecordsKit.PAPER_LIT if state == "selected" else UiKit.SURFACE.scroll.lerp(UiKit.BRONZE, 0.3)
	rounded(r.grow(1), 2.0, UiKit.BRONZE)
	rounded(r, 2.0, paper)
	ground(r, paper)
	draw_circle(Vector2(r.get_center().x, r.position.y + 6), 3.0, UiKit.INK, true, -1.0, true)
	text(Vector2(r.position.x, r.position.y + 33), str(tabs[i].label), 20, RecordsKit.INK if state != "disabled" else RecordsKit.FADED, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	if likeness != null: likeness.visible = false
	if str(tabs[tab].id) == "bounties":
		_bounties(ch)
		_handbills(ch, CORNER, true)
	else:
		tour_mark("board", Rect2(96, 120, 720, 548))   # decision 43: a tour's anchor
		_handbills(ch, Rect2(96, 120, 720, 548), false)
		_posters_corner(ch)

# ------------------------------------------------------------------ the bounties
func _rows() -> Array:
	return Game.relations.fcfg().get("bounties", [])

## The wanted posters pasted across the wall: the others first at their places, the chosen one over them, largest.
func _bounties(ch) -> void:
	var rows := _rows()
	if rows.is_empty(): return
	if chosen == "" or not rows.any(func(b): return str(b.id) == chosen): chosen = str(rows[0].id)
	# Older posters torn away, strips of them left on the brick.
	for s in [[Vector2(430, 560), -0.05, Vector2(200, 80)], [Vector2(640, 520), 0.06, Vector2(170, 110)], [Vector2(700, 118), 0.1, Vector2(120, 120)]]:
		move(s[0], s[1])
		draw_rect(Rect2(Vector2.ZERO, s[2]), UiKit.SURFACE.scroll.lerp(UiKit.SURFACE.stone, 0.35))
		for k in range(0, int(s[2].x), 9): draw_rect(Rect2(k, s[2].y - float(k * 7 % 5) - 2.0, 9, float(k * 7 % 5) + 2.0), UiKit.SURFACE.stone)
		draw_rect(Rect2(8, 8, s[2].x * 0.6, 6), Color(RecordsKit.INK, 0.12))
	move()
	var spots := [Vector2(440, 132), Vector2(596, 228), Vector2(452, 300)]
	var others := rows.filter(func(b): return str(b.id) != chosen)
	for i in others.size():
		_poster(ch, others[i], Rect2(spots[i % spots.size()], SMALL), false)
	var top: Dictionary = rows.filter(func(b): return str(b.id) == chosen)[0]
	var at := Vector2(100, 124)
	# The chosen poster is slapped on as the page opens (a fade under Reduce motion).
	var k := 1.0 - unfold()
	move(-(at + BIG * 0.5) * 0.06 * k, 0.0, Vector2.ONE * (1.0 + 0.06 * k))
	_poster(ch, top, Rect2(at, BIG), true)
	move()

## One wanted poster: WANTED, the target's likeness, its name and band, what it did, the reward stamped in red; the
## chosen one carries its Take strip at the foot.
func _poster(ch, b: Dictionary, r: Rect2, big: bool, tap := true) -> void:
	face(r, "poster")
	var x := r.position.x + 18
	var w := r.size.x - 36
	text(Vector2(r.position.x, r.position.y + (46 if big else 38)), Tx.t("ui.notice.wanted"), 30 if big else 26, RecordsKit.RED_INK, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, true)
	var pic := Rect2(r.position.x + 30, r.position.y + (60 if big else 50), r.size.x - 60, 150.0 if big else 110.0)
	draw_rect(pic, UiKit.SURFACE.scroll.lerp(UiKit.BRONZE, 0.18))
	draw_rect(pic, Color(RecordsKit.INK, 0.6), false, 2.0)
	var art: Dictionary = ContentDB.entry("enemies", str(b.target)).get("art", {})
	if big and art.get("avatar") is Dictionary: _likeness(art.avatar, Vector2(pic.get_center().x, pic.end.y - 4))
	elif not creature_at(pic.grow(-8), str(b.target)):
		# A sketch of the head and shoulders where no likeness can be drawn (a poster half hidden under another).
		var hc := Vector2(pic.get_center().x, pic.position.y + pic.size.y * 0.4)
		draw_circle(hc, pic.size.y * 0.2, Color(RecordsKit.INK, 0.35), true, -1.0, true)
		draw_colored_polygon(PackedVector2Array([Vector2(hc.x - pic.size.y * 0.42, pic.end.y - 2), Vector2(hc.x - pic.size.y * 0.3, hc.y + pic.size.y * 0.24),
			Vector2(hc.x + pic.size.y * 0.3, hc.y + pic.size.y * 0.24), Vector2(hc.x + pic.size.y * 0.42, pic.end.y - 2)]), Color(RecordsKit.INK, 0.35))
	var y := pic.end.y + (36 if big else 30)
	text(Vector2(x, y), ContentDB.name_of("enemies", str(b.target)), 26 if big else 22, RecordsKit.INK, HORIZONTAL_ALIGNMENT_CENTER, w, true)
	var rw: Dictionary = b.get("reward", {})
	var reward := "%s %s" % [UiKit.fmt(int(rw.get("amount", 0))), currency_name(str(rw.get("currency", "silver_tael")))]
	if big:
		text(Vector2(x, y + 22), ContentDB.name_of("factions", str(b.faction)) + " · " + ContentDB.name_of("rooms", str(b.room)), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_CENTER, w)
		para(Rect2(x, y + 32, w, 64), str(b.get("text", "")), 14, RecordsKit.INK, 3)
	# The reward, stamped in red.
	var sy := r.end.y - (118 if big else 56)
	var sw := minf(w, UiKit.text_width(reward, 18) + 28)
	var sr := Rect2(r.get_center().x - sw * 0.5, sy, sw, 36)
	draw_rect(sr, Color(UiKit.BLOOD, 0.85), false, 3.0)
	draw_rect(sr.grow(-4), Color(UiKit.BLOOD, 0.5), false, 1.0)
	text(Vector2(sr.position.x, sr.position.y + 25), reward, 18, RecordsKit.RED_INK, HORIZONTAL_ALIGNMENT_CENTER, sr.size.x)
	if not big:
		if tap: region(r, "poster", str(b.id))
		return
	var mine: Array = ch.relations.bounties.map(func(v): return str(v.get("id", "")))
	var strip := Rect2(r.position.x + 16, r.end.y - 72, r.size.x - 32, 56)
	if mine.has(str(b.id)):
		RecordsKit.stamp(self, strip.get_center(), Tx.t("ui.notice.bounty_hunting"), 30.0)
	else:
		# The strip to tear off, along a dashed line.
		for dx in range(0, int(strip.size.x), 12): draw_line(Vector2(strip.position.x + dx, strip.position.y - 6), Vector2(strip.position.x + dx + 6, strip.position.y - 6), Color(RecordsKit.INK, 0.5), 1.5)
		var ok_realm := ProgressionRules.at_least(ch.cultivator.realm_key, str(b.get("realm", "")))
		btn(strip, Tx.t("ui.notice.take_bounty"), "bounty", str(b.id), true, ok_realm, Tx.t("req.reach") % ContentDB.name_of("realms", str(b.get("realm", ""))), 20)

## The target's own figure standing in the chosen poster's picture, at a whole scale: in the top-down game the top-down
## figure (TopdownDoll, 3 px an art px, facing the reader), as the world draws such a foe; the side view's at 1 (2 px an
## art px) for a classic side-view character (decision 42).
func _likeness(outfit: Dictionary, feet: Vector2) -> void:
	var o: Dictionary = Wardrobe.defaults().duplicate()
	o.merge(outfit, true)
	o.erase("name")
	if likeness == null:
		likeness = Figures.for_outfit(o, 1.0, 3, null, "s")
		add_child(likeness)
		likeness.play("idle")
	if likeness.outfit != o: Figures.dress(likeness, o)
	likeness.position = feet
	likeness.visible = true

## The Board tab's corner: the posters, small, in a stack; a tap turns to them.
func _posters_corner(ch) -> void:
	var rows := _rows()
	var r := Rect2(CORNER.position + Vector2(40, 20), Vector2(240, 340))
	for i in mini(2, rows.size() - 1):
		rounded(Rect2(r.position + Vector2(12 + i * 10, 8 + i * 6), r.size), 2.0, UiKit.SURFACE.scroll.lerp(UiKit.SURFACE.stone, 0.4 + 0.15 * i))
	if not rows.is_empty(): _poster(ch, rows[0], r, false, false)
	text(Vector2(CORNER.position.x, r.end.y + 44), Tx.plural("ui.notice.bounties_posted", rows.size()) % rows.size(), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, CORNER.size.x)
	region(Rect2(r.position, r.size + Vector2(0, 60)), "to_tab", 1)

# ------------------------------------------------------------------ the handbills
## Today's sect missions and the requests of people nearby, as handbills pasted in two columns (the Board tab), or
## summed up in the corner of the Bounties tab, where a tap turns to them.
func _handbills(ch, area: Rect2, corner: bool) -> void:
	var missions: Array = ch.quests.daily.keys()
	var requests: Array = []
	for qid in ch.quests.offered:
		var d := ContentDB.entry("quests", qid)
		if not d.is_empty() and str(d.get("kind", "")) == "side" and Game.quest.can_offer(ch, d): requests.append(str(qid))
	if corner:
		var y := area.position.y + 20
		for part in [[Tx.t("ui.notice.sect_missions"), missions.size(), missions, true], [Tx.t("ui.notice.requests"), requests.size(), requests, false]]:
			var hb := Rect2(area.position.x + 20, y, area.size.x - 40, 200)
			_bill(hb, str(part[0]), str(part[1]))
			var ly := hb.position.y + 66
			for q in (part[2] as Array).slice(0, 4):
				var nm := str(ch.quests.daily[q].name) if part[3] else ContentDB.name_of("quests", str(q))
				text(Vector2(hb.position.x + 16, ly), "· " + nm, 14, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, hb.size.x - 32)
				ly += 22
			if (part[2] as Array).size() > 4: text(Vector2(hb.position.x + 16, ly), Tx.t("ui.quest.and_more") % ((part[2] as Array).size() - 4), 14, RecordsKit.BROWN)
			region(hb, "to_tab", 0)
			y += 230
		return
	var cols := [[Tx.t("ui.notice.sect_missions"), missions, true], [Tx.t("ui.notice.requests"), requests, false]]
	for ci in cols.size():
		var col: Array = cols[ci]
		var x := area.position.x + ci * (HANDBILL.x + 20)
		var head := Rect2(x, area.position.y, HANDBILL.x, 48)
		_bill(head, str(col[0]), str((col[1] as Array).size()))
		var ids: Array = col[1]
		if ids.is_empty():
			var why := ""
			if col[2]: why = Tx.t("ui.notice.missions_open_at_qi_kindling") if not Unlocks.is_unlocked(ch.id, "daily_missions") else Tx.t("ui.notice.all_of_today_missions_are")
			else: why = Tx.t("ui.notice.no_requests")
			para(Rect2(x + 8, head.end.y + 16, HANDBILL.x - 16, 80), why, 16, UiKit.PAPER, 3)
			continue
		var fit_n := int((area.end.y - head.end.y - 12) / (HANDBILL.y + 8))
		for i in mini(ids.size(), fit_n):
			var q := str(ids[i])
			var r := Rect2(x + float([0, 10, 4, 12][i % 4]), head.end.y + 12 + i * (HANDBILL.y + 8), HANDBILL.x - 12, HANDBILL.y)
			rounded(r.grow(1), 2.0, UiKit.BRONZE)
			rounded(r, 2.0, RecordsKit.PAPER_LIT)
			ground(r, UiKit.SURFACE.scroll)
			if col[2]:
				var d: Dictionary = ch.quests.daily[q]
				var st: Dictionary = ch.quests.active.get(q, {})
				var o: Dictionary = d.objectives[0]
				var have := int(st.get("progress", [0])[0]) if not st.is_empty() else 0
				text(r.position + Vector2(14, 26), str(d.name), 18, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
				text(r.position + Vector2(14, 50), "%s (%d / %d)" % [str(o.get("text", "")), mini(have, int(o.get("count", 1))), int(o.get("count", 1))], 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
			else:
				var d2 := ContentDB.entry("quests", q)
				text(r.position + Vector2(14, 26), str(d2.name), 18, RecordsKit.INK, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
				text(r.position + Vector2(14, 50), Tx.t("ui.notice.ask") % ContentDB.name_of("npcs", str(d2.giver)), 14, RecordsKit.BROWN, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
		if ids.size() > fit_n: text(Vector2(x, area.end.y + 2), Tx.t("ui.quest.and_more") % (ids.size() - fit_n), 14, UiKit.PAPER)

## A handbill's head: its words and a count, pasted with a pin of paste at each top corner.
func _bill(r: Rect2, words: String, count: String) -> void:
	rounded(r.grow(1), 2.0, UiKit.BRONZE)
	rounded(r, 2.0, RecordsKit.PAPER_LIT)
	ground(r, UiKit.SURFACE.scroll)
	for px in [r.position.x + 8, r.end.x - 8]: draw_circle(Vector2(px, r.position.y + 8), 4.0, Color(UiKit.BRONZE, 0.35), true, -1.0, true)
	text(r.position + Vector2(16, 34), words, 22, RecordsKit.RED_INK, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 80, true)
	text(Vector2(r.end.x - 66, r.position.y + 34), count, 20, RecordsKit.INK, HORIZONTAL_ALIGNMENT_RIGHT, 50)

func on_action(id: String, data) -> void:
	match id:
		"bounty":
			if submit({"type": "take_bounty", "id": str(data)}).get("ok", false): took_at = t
		"poster": chosen = str(data)
		"to_tab":
			tab = int(data)
			scroll.clear()
	queue_redraw()
