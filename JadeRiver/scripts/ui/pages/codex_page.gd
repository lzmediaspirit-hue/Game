extends Page
## Codex, Collection book and Achievements (S19, S32, S34) in one tabbed page.

var sel := ""

func _init() -> void:
	title = Tx.t("ui.codex.codex")
	tabs = [{"id": "codex", "label": Tx.t("ui.codex.codex")}, {"id": "collection", "label": Tx.t("ui.codex.collection")}, {"id": "achievements", "label": Tx.t("ui.codex.achievements")}]

func setup() -> void:
	match page_id:
		"collection": tab = 1
		"achievements": tab = 2

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	match str(tabs[tab].id):
		"codex": _codex()
		"collection": _collection()
		"achievements": _achievements(ch)

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
		para(Rect2(right.position + Vector2(24, 70), right.size - Vector2(48, 90)), str(e2.get("body", "")), 20)
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
				text(cr.position + Vector2(0, 104), str(e.name), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
				text(cr.position + Vector2(0, 126), Tx.t("ui.codex.defeated") % kills, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
			else:
				var art2 = e.get("art", {})
				var cid2 := str(art2.get("creature", "")) if art2 is Dictionary else ""
				if cid2 == "" or not creature_at(Rect2(cr.position + Vector2(8, 6), Vector2(cr.size.x - 16, 78)), cid2, "idle", Color(0, 0, 0, 0.6)):
					text(cr.position + Vector2(0, 80), "?", 40, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
				text(cr.position + Vector2(0, 116), "? ? ?", 16, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
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
