extends Page
## The County Hall (S49 mortal kingdom): county favour and its tiers on the left; on the right, today's three county
## jobs from the magistrate's board, or the relief fund, where silver for the county's poor earns merit and favour.

func _init() -> void:
	title = Tx.t("ui.county.title")
	tabs = [{"id": "jobs", "label": Tx.t("ui.county.jobs")}, {"id": "relief", "label": Tx.t("ui.county.relief")}]

func setup() -> void:
	if str(args.get("tab", "")) == "relief": tab = 1
	if c() != null: submit({"type": "county_jobs"})   # the board is read: today's jobs are posted and taken

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var left := Rect2(content.position, Vector2(420, content.size.y))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(left)
	panel(right)
	# Left: county favour.
	var x := left.position.x + 24
	var y := left.position.y + 40
	heading(Vector2(x, y), Tx.t("ui.county.favour"), left.size.x - 48)
	var tier: Dictionary = Game.relations.favour_tier(ch)
	var nxt: Dictionary = Game.relations.next_favour_tier(ch)
	y += 48
	text(Vector2(x, y), Tx.t("ui.county.tier_" + str(tier.get("id", "stranger"))), 28, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	text(Vector2(left.end.x - 24 - 160, y), Tx.t("ui.county.favour_pts") % Game.relations.favour(ch), 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 160)
	y += 16
	if not nxt.is_empty():
		var lo := int(tier.get("min", 0))
		var hi := int(nxt.min)
		bar(Rect2(x, y, left.size.x - 48, 24), float(Game.relations.favour(ch) - lo) / float(maxi(1, hi - lo)), UiKit.GOLD,
			Tx.t("ui.county.to_next") % [hi - Game.relations.favour(ch), Tx.t("ui.county.tier_" + str(nxt.id))])
	y += 44
	for t2 in Game.relations.mcfg().get("favour_tiers", []):
		var got: bool = Game.relations.favour(ch) >= int(t2.get("min", 0))
		text(Vector2(x, y + 18), Tx.t("ui.county.tier_" + str(t2.id)), 18, UiKit.GOLD if got else UiKit.HOLLOW)
		text(Vector2(left.end.x - 24 - 90, y + 18), Tx.t("ui.county.favour_pts") % int(t2.get("min", 0)), 14, UiKit.MIST if got else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_RIGHT, 90)
		text(Vector2(x + 14, y + 38), fit(Tx.t("ui.county.brings_" + str(t2.id)), 14, left.size.x - 62), 14, UiKit.PAPER if got else UiKit.HOLLOW)
		y += 48
	para(Rect2(x, y + 6, left.size.x - 48, left.end.y - y - 12), Tx.t("ui.county.note"), 15, UiKit.MIST, 4)
	# Right: the jobs or the relief fund.
	x = right.position.x + 24
	y = right.position.y + 40
	if str(tabs[tab].id) == "jobs":
		heading(Vector2(x, y), Tx.t("ui.county.today"), right.size.x - 48)
		y += 24
		var jobs: Array = ch.relations.mortal.get("jobs", [])
		if jobs.is_empty():
			para(Rect2(x, y, right.size.x - 48, 60), Tx.t("ui.county.no_jobs"), 17, UiKit.MIST, 3)
			return
		for qid in jobs:
			var def := Game.quest.quest_def(ch, str(qid))
			var done: bool = ch.quests.done.has(str(qid))
			var st: Dictionary = ch.quests.active.get(str(qid), {})
			var card := Rect2(x, y, right.size.x - 48, 112)
			panel(card, "minor_panel", "normal")
			text(card.position + Vector2(18, 32), fit(str(def.get("name", qid)), 20, card.size.x - 150), 20, UiKit.PALE_GOLD if not done else UiKit.MIST)
			text(Vector2(card.end.x - 18 - 120, card.position.y + 32), Tx.t("ui.county.done") if done else "", 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, 120)
			var objs: Array = def.get("objectives", [])
			if not objs.is_empty():
				var o: Dictionary = objs[0]
				var have := int((st.get("progress", [0]) as Array)[0]) if not st.is_empty() else (int(o.get("count", 1)) if done else 0)
				text(card.position + Vector2(18, 62), fit("%s  %d/%d" % [str(o.get("text", "")), have, int(o.get("count", 1))], 17, card.size.x - 36), 17, UiKit.PAPER)
			var silver := 0
			for rw in def.get("rewards", []):
				if str(rw.get("kind", "")) == "grant_currency": silver = int(rw.get("amount", 0))
			text(card.position + Vector2(18, 92), Tx.t("ui.county.pays") % [silver, int(Game.relations.mcfg().get("reward", {}).get("favour", 10))], 15, UiKit.MIST)
			y += 122
		return
	heading(Vector2(x, y), Tx.t("ui.county.relief_title"), right.size.x - 48)
	y += 18
	y += para(Rect2(x, y, right.size.x - 48, 60), Tx.t("ui.county.relief_note"), 16, UiKit.MIST, 3) + 16
	var given: Dictionary = ch.relations.mortal.get("donated", {})
	var today := Clock.reset_day(Clock.now_utc())
	for d in Game.relations.mcfg().get("donations", []):
		var card2 := Rect2(x, y, right.size.x - 48, 90)
		panel(card2, "minor_panel", "normal")
		text(card2.position + Vector2(18, 36), Tx.t("ui.county.give") % UiKit.fmt(int(d.silver)), 21, UiKit.PALE_GOLD)
		var merit := int(ContentDB.entry("karma", str(d.get("deed", ""))).get("merit", 0))
		text(card2.position + Vector2(18, 66), Tx.t("ui.county.gives_back") % [merit, int(d.get("favour", 0))], 15, UiKit.MIST)
		var gave: bool = int(given.get(str(d.id), -1)) == today
		var can: bool = not gave and Game.economy.balance("silver_tael") >= int(d.silver)
		btn(Rect2(card2.end.x - 18 - 170, card2.position.y + 18, 170, 54), Tx.t("ui.county.given") if gave else Tx.t("ui.county.donate"), "donate", str(d.id), true, can,
			Tx.t("ui.county.given_today") if gave else Tx.t("ui.county.need_silver") % UiKit.fmt(int(d.silver)), 19)
		y += 100

func on_action(id: String, data) -> void:
	match id:
		"donate":
			var r := submit({"type": "donate_relief", "tier": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.county.thanks"))
	queue_redraw()
