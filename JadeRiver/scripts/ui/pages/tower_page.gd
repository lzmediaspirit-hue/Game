extends Page
## The Trial Tower (S49): thirty floors at the Fairground (tower.json). The floors on the left, the chosen one on the
## right: its Level, its rule and its foes, and a button to climb it. Every floor you have cleared can be swept once a
## day for its loot without the fight.

var sel := 0

func _init() -> void:
	title = Tx.t("ui.tower.title")

func setup() -> void:
	var ch = c()
	if ch != null: sel = mini(30, Game.world.tower_cleared(ch) + 1)
	# The list runs from the top floor down: start it scrolled to the floor you can climb.
	scroll["floors"] = maxf(0.0, floorf(((ContentDB.all("tower").size() - sel) * 58.0 - 150.0) / 58.0) * 58.0)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var cleared := Game.world.tower_cleared(ch)
	var floors: Array = ContentDB.all("tower")
	var left := Rect2(content.position, Vector2(420, content.size.y))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(left)
	panel(right)
	# Left: every floor, the highest first; cleared ones marked, the next one bright, the rest dim.
	list("floors", Rect2(left.position.x + 10, left.position.y + 10, left.size.x - 20, left.size.y - 96), floors.size(), 58, func(i: int, rr: Rect2):
		var row: Dictionary = floors[floors.size() - 1 - i]
		var f := int(row.floor)
		panel(rr, "minor_panel", "selected" if sel == f else "normal")
		var col := UiKit.PAPER if f <= cleared else (UiKit.PALE_GOLD if f == cleared + 1 else UiKit.HOLLOW)
		text(rr.position + Vector2(16, 36), Tx.t("ui.tower.floor") % f, 20, col)
		text(rr.position + Vector2(130, 36), Tx.t("ui.tower.kind_" + str(row.kind)), 16, UiKit.MIST if f <= cleared + 1 else UiKit.HOLLOW)
		var mark := ""
		if f <= cleared: mark = Tx.t("ui.tower.swept") if Game.world.tower_swept_today(ch, f) else "✓"
		text(Vector2(rr.end.x - 16 - 120, rr.position.y + 36), mark if mark != "" else Tx.t("ui.arena.lv") % int(row.level), 16,
			UiKit.BRIGHT_JADE if mark == "✓" else UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 120)
		region(rr, "sel", f)
	)
	var sweepable := 0
	for f in range(1, cleared + 1):
		if not Game.world.tower_swept_today(ch, f): sweepable += 1
	btn(Rect2(left.position.x + 16, left.end.y - 74, left.size.x - 32, 58), Tx.t("ui.tower.sweep") % sweepable if sweepable > 0 else Tx.t("ui.tower.swept_all"),
		"sweep", null, sweepable > 0, sweepable > 0, Tx.t("ui.tower.sweep_none"))
	# Right: the chosen floor.
	var row2 := Game.world.tower_floor(sel)
	if row2.is_empty(): return
	var x := right.position.x + 28
	var y := right.position.y + 44
	heading(Vector2(x, y), Tx.t("ui.tower.floor_title") % [sel, Tx.t("ui.tower.kind_" + str(row2.kind))], right.size.x - 56)
	y += 44
	text(Vector2(x, y), Tx.t("ui.arena.lv") % int(row2.level), 20, UiKit.PALE_GOLD)
	text(Vector2(right.end.x - 28 - 300, y), Tx.t("ui.tower.cleared_to") % cleared, 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 300)
	y += 16
	y += para(Rect2(x, y, right.size.x - 56, 80), Tx.t("ui.tower.rule_" + str(row2.kind)) % [int(row2.get("count", 0)), int(row2.get("time_s", 0))]
		if str(row2.kind) in ["clear", "swift"] else Tx.t("ui.tower.rule_" + str(row2.kind)) % int(row2.get("time_s", 0)), 18, UiKit.PAPER, 3) + 18
	text(Vector2(x, y + 4), Tx.t("ui.tower.foes"), 16, UiKit.MIST)
	y += 14
	var names: Array = (row2.get("foes", []) as Array).map(func(e): return ContentDB.name_of("enemies", str(e)))
	if str(row2.kind) == "guardian": names.push_front(Tx.t("ui.tower.guardian") % ContentDB.name_of("enemies", str(row2.guardian)))
	y += para(Rect2(x, y, right.size.x - 56, 60), ", ".join(names), 18, UiKit.PAPER, 2) + 18
	text(Vector2(x, y + 4), Tx.t("ui.tower.rewards"), 16, UiKit.MIST)
	y += 14
	var first := sel > cleared
	para(Rect2(x, y, right.size.x - 56, 60), (Tx.t("ui.tower.reward_first") % int(row2.get("stones", 2))) if first else Tx.t("ui.tower.reward_again"), 17,
		UiKit.PALE_GOLD if first else UiKit.MIST, 2)
	var can := sel <= cleared + 1
	btn(Rect2(right.position.x + 28, right.end.y - 80, right.size.x - 56, 60), Tx.t("ui.tower.climb") % sel if sel > cleared else Tx.t("ui.tower.again") % sel,
		"climb", sel, true, can, Tx.t("ui.tower.locked") % (cleared + 1))

func on_action(id: String, data) -> void:
	match id:
		"sel": sel = int(data)
		"sweep": submit({"type": "sweep_floor", "floor": -1})
		"climb":
			if submit({"type": "climb_tower", "floor": int(data)}).get("ok", false):
				close()
				return
	queue_redraw()
