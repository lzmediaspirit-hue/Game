extends Page
## Codex, Collection book and Achievements (S19, S32, S34) in one tabbed page.

var sel := ""

func _init() -> void:
	title = Tx.t("ui.codex.codex")
	tabs = [{"id": "codex", "label": Tx.t("ui.codex.codex")}, {"id": "collection", "label": Tx.t("ui.codex.collection")}, {"id": "achievements", "label": Tx.t("ui.codex.achievements")},
		{"id": "paths_above", "label": Tx.t("ui.codex.paths_above")}, {"id": "seasons", "label": Tx.t("ui.codex.seasons")}]

func setup() -> void:
	match page_id:
		"collection": tab = 1
		"achievements": tab = 2
		"paths_above": tab = 3
		"seasons": tab = 4

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	match str(tabs[tab].id):
		"codex": _codex()
		"collection": _collection()
		"achievements": _achievements(ch)
		"paths_above": _paths_above(ch)
		"seasons": _seasons()

func _codex() -> void:
	var entries: Array = ContentDB.all("codex")
	if sel == "" or not Game.account.codex.has(sel):
		for e0 in entries:
			if Game.account.codex.has(str(e0.id)):
				sel = str(e0.id)
				break
	var left := Rect2(content.position.x, content.position.y, 380, content.size.y)
	panel(left)
	list("codex", left.grow(-10), entries.size(), 48, func(i: int, rr: Rect2):
		var e: Dictionary = entries[i]
		var known: bool = Game.account.codex.has(str(e.id))
		text(rr.position + Vector2(14, 30), str(e.title) if known else "? ? ?", 19, (UiKit.PALE_GOLD if sel == str(e.id) else UiKit.PAPER) if known else UiKit.HOLLOW)
		region(rr, "sel", str(e.id), known, Tx.t("ui.codex.not_yet_discovered"))
	)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	if sel != "":
		var e2 := ContentDB.entry("codex", sel)
		heading(right.position + Vector2(24, 46), str(e2.get("title", "")), right.size.x - 48)
		var used := para(Rect2(right.position + Vector2(24, 70), right.size - Vector2(48, 90)), str(e2.get("body", "")), 20)
		# S44: the experiment log, shared by every character on the account.
		if sel == "experiments":
			var y := right.position.y + 90 + used
			for ex in Game.account.experiments.slice(maxi(0, Game.account.experiments.size() - 10)):
				var names: Array = []
				for h in ex.get("herbs", []): names.append(ContentDB.item_name(str(h)))
				text(Vector2(right.position.x + 24, y), fit(" + ".join(names) + "  →  " + Game.crafting.experiment_result_text(ex), 16, right.size.x - 48), 16,
					UiKit.GOLD if str(ex.get("result", "")).begins_with("learned:") else UiKit.MIST)
				y += 24
	else:
		para(Rect2(right.position + Vector2(24, 30), right.size - Vector2(48, 60)), Tx.t("ui.codex.of_entries_discovered") % [Game.account.codex.size(), entries.size()], 20, UiKit.MIST)

func _collection() -> void:
	var foes: Array = ContentDB.all("enemies").filter(func(e): return str(e.get("role", "")) in ["normal", "elite", "field_boss", "dungeon_boss"])
	var r := Rect2(content.position, content.size)
	panel(r)
	var cols := 5
	var rows := int(ceil(foes.size() / float(cols)))
	list("col", r.grow(-10), rows, 150, func(row: int, rr: Rect2):
		for col in cols:
			var i := row * cols + col
			if i >= foes.size(): break
			var e: Dictionary = foes[i]
			var kills := int(Game.account.collection.get(str(e.id), 0))
			var cr := Rect2(rr.position.x + col * (rr.size.x / cols) + 4, rr.position.y, rr.size.x / cols - 8, 142)
			panel(cr, "minor_panel", "normal" if kills > 0 else "disabled")
			if kills > 0:
				var art = e.get("art", {})
				var cid := str(art.get("creature", "")) if art is Dictionary else ""
				if cid == "" or not creature_at(Rect2(cr.position + Vector2(8, 6), Vector2(cr.size.x - 16, 78)), cid):
					icon_at(Rect2(cr.get_center() - Vector2(24, 50), Vector2(48, 48)), str(e.get("loot_icon", "boss_skull")))
				text(cr.position + Vector2(0, 100), str(e.name), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
				# S46: a beast's rank and nature (demonic and Hollowed ones are tamed differently).
				var sub := Tx.t("ui.codex.defeated") % kills
				if int(e.get("beast_rank", 0)) > 0:
					sub = Tx.t("ui.codex.rank_nature") % [int(e.beast_rank), Tx.t("ui.codex.nature_" + str(e.get("nature", "spirit")))] + "  ·  " + sub
				text(cr.position + Vector2(0, 124), fit(sub, 13, cr.size.x - 8), 13, UiKit.GOLD if str(e.get("nature", "")) == "demonic" else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
			else:
				var art2 = e.get("art", {})
				var cid2 := str(art2.get("creature", "")) if art2 is Dictionary else ""
				if cid2 == "" or not creature_at(Rect2(cr.position + Vector2(8, 6), Vector2(cr.size.x - 16, 78)), cid2, "idle", Color(0, 0, 0, 0.6)):
					text(cr.position + Vector2(0, 80), "?", 40, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
				text(cr.position + Vector2(0, 116), "? ? ?", 16, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
	)

## S43 "Paths Above": every optional ledge that only a later movement art reaches, and whether you have stood on it.
## S45 season calendar: which rare herbs flower in which season, and when each ripens. A place shows once visited.
func _seasons() -> void:
	var now := Clock.now_utc()
	var cur := HerbRules.season(now)
	var rares: Array = []
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if o.get("type", "") == "herb_patch" and o.has("ripen"): rares.append({"room": str(rid), "o": o})
	rares.sort_custom(func(a, b): return str(a.o.item) < str(b.o.item))
	text(content.position + Vector2(20, 30), Tx.t("ui.codex.season_now") % [ContentDB.name_of("seasons", cur), UiKit.clock(HerbRules.season_left_s(now))], 20, UiKit.PALE_GOLD)
	var seasons: Array = ContentDB.all("seasons")
	var gap := 14.0
	var cw := (content.size.x - gap * 3) / 4.0
	var top := content.position.y + 50
	var ch_h := 250.0
	for i in seasons.size():
		var sd: Dictionary = seasons[i]
		var r := Rect2(content.position.x + i * (cw + gap), top, cw, ch_h)
		panel(r, "minor_panel", "selected" if str(sd.id) == cur else "normal")
		text(r.position + Vector2(16, 34), str(sd.name), 22, UiKit.GOLD if str(sd.id) == cur else UiKit.PALE_GOLD)
		var y := r.position.y + 44 + para(Rect2(r.position + Vector2(16, 44), Vector2(cw - 32, 90)), str(sd.get("desc", "")), 15, UiKit.MIST, 4) + 8
		for rn in rares:
			if str(rn.o.get("season", "")) != str(sd.id): continue
			y = _rare_line(rn, Vector2(r.position.x + 16, y), cw - 32)
	var r2 := Rect2(content.position.x, top + ch_h + gap, content.size.x, content.end.y - top - ch_h - gap)
	panel(r2)
	text(r2.position + Vector2(16, 32), Tx.t("ui.codex.no_season"), 19, UiKit.PALE_GOLD)
	var y2 := r2.position.y + 44
	var col := 0
	for rn in rares:
		if str(rn.o.get("season", "")) != "": continue
		_rare_line(rn, Vector2(r2.position.x + 16 + col * (r2.size.x / 2.0), y2), r2.size.x / 2.0 - 32)
		col += 1
		if col == 2:
			col = 0
			y2 += 48

func _rare_line(rn: Dictionary, at: Vector2, w: float) -> float:
	var o: Dictionary = rn.o
	var ic := SpriteCache.icon(str(o.item))
	if ic: draw_texture_rect(ic, Rect2(at.x, at.y, 28, 28), false)
	var seen: bool = Game.account.visited_rooms.has(str(rn.room))
	text(at + Vector2(34, 13), fit(ContentDB.item_name(str(o.item)), 15, w - 34), 15, UiKit.PAPER)
	var rp: Dictionary = o.get("ripen", {})
	var where := str(ContentDB.room(str(rn.room)).get("name", "")) if seen else "? ? ?"
	text(at + Vector2(34, 31), fit(Tx.t("ui.codex.ripens") % [where, Tx.t("ui.herb.phase_" + str(rp.get("phase", "dawn"))), int(rp.get("every_days", 1))], 13, w - 34), 13, UiKit.MIST)
	return at.y + 44

func _paths_above(ch) -> void:
	var rows: Array = ContentDB.all("paths_above")
	var r := Rect2(content.position, content.size)
	panel(r)
	text(r.position + Vector2(24, 36), Tx.t("ui.codex.paths_above_intro") % [Game.account.paths_above.size(), rows.size()], 18, UiKit.MIST)
	list("paths", Rect2(r.position + Vector2(10, 52), r.size - Vector2(20, 62)), rows.size(), 72, func(i: int, rr: Rect2):
		var e: Dictionary = rows[i]
		var found: bool = Game.account.paths_above.has(str(e.id))
		var known: bool = Game.combat.knows_art(ch, str(e.art)) or Unlocks.is_unlocked(ch.id, str(e.art))
		var seen: bool = found or Game.account.visited_rooms.has(str(e.room))
		var cell := Rect2(rr.position + Vector2(4, 4), rr.size - Vector2(8, 8))
		panel(cell, "minor_panel", "normal" if found else "disabled")
		text(cell.position + Vector2(18, 28), str(e.room_name) if seen else "? ? ?", 19, UiKit.PAPER if seen else UiKit.HOLLOW)
		text(cell.position + Vector2(18, 52), Tx.t("ui.codex.paths_above_needs") % [str(e.art_name), int(e.height)], 15, UiKit.BRIGHT_JADE if known else UiKit.HOLLOW)
		var status := Tx.t("ui.codex.paths_above_found") % str(e.reward) if found else (Tx.t("ui.codex.paths_above_open") if known else Tx.t("ui.codex.paths_above_later"))
		text(cell.position + Vector2(cell.size.x * 0.45, 40), status, 17, UiKit.PALE_GOLD if found else (UiKit.PAPER if known else UiKit.HOLLOW),
			HORIZONTAL_ALIGNMENT_RIGHT, cell.size.x * 0.55 - 18)
	)

func _achievements(ch) -> void:
	var list_a: Array = ContentDB.all("achievements")
	var r := Rect2(content.position, content.size)
	panel(r)
	list("ach", r.grow(-10), list_a.size(), 72, func(i: int, rr: Rect2):
		var a: Dictionary = list_a[i]
		var done: bool = Game.account.achievements.done.has(str(a.id))
		var n := int(Game.account.achievements.counters.get(str(a.id), 0))
		panel(rr, "minor_panel", "selected" if done else "normal")
		text(rr.position + Vector2(20, 30), str(a.name), 21, UiKit.PALE_GOLD if done else UiKit.PAPER)
		text(rr.position + Vector2(20, 56), str(a.get("desc", "")), 16, UiKit.MIST)
		if a.has("title"): text(rr.position + Vector2(0, 30), Tx.t("ui.codex.title") % ContentDB.name_of("titles", str(a.title)), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_RIGHT, rr.size.x - 20)
		if int(a.get("count", 1)) > 1 and not done: text(rr.position + Vector2(0, 56), "%d / %d" % [n, int(a.count)], 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, rr.size.x - 20)
		elif done: text(rr.position + Vector2(0, 56), Tx.t("ui.codex.complete"), 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, rr.size.x - 20)
	)

func on_action(id: String, data) -> void:
	if id == "sel": sel = str(data)
	if id == "_tab": sel = ""
