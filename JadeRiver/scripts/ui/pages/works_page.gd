extends Page
## S50 Keeping Post (V10d): the account web behind the posts. Arts: the active character's Post Arts, bought with
## points from its craft levels. Seals: Seal Scripts inscribed with Storehouse goods. Steles: Guardian Steles raised
## with silver and ore. Favours: the Magistrate's Favours, earned once each with silver and tribute.

func _init() -> void:
	title = Tx.t("ui.works.title")
	tabs = [{"id": "arts", "label": Tx.t("ui.works.tab_arts")}, {"id": "seals", "label": Tx.t("ui.works.tab_seals")},
		{"id": "steles", "label": Tx.t("ui.works.tab_steles")}, {"id": "favours", "label": Tx.t("ui.works.tab_favours")}]

func setup() -> void:
	var want := str(args.get("tab", ""))
	for i in tabs.size():
		if str(tabs[i].id) == want: tab = i

func draw_page() -> void:
	match tab:
		0: _draw_arts()
		1: _draw_seals()
		2: _draw_steles()
		3: _draw_favours()

## A locked tab's reason; true when the tab is open.
func _gate(unlock_id: String) -> bool:
	var ch = c()
	if ch == null: return false
	if Unlocks.is_unlocked(ch.id, unlock_id): return true
	para(Rect2(content.position + Vector2(0, 20), Vector2(content.size.x, 80)), Unlocks.locked_text(unlock_id), 18, UiKit.HOLLOW)
	return false

## An effect line: `fmt` with the value, if the format takes one.
func _effect(fmt: String, v: float) -> String:
	if not "%s" in fmt: return fmt
	var step := (0.01 if v < 10.0 else 0.1) if "%%" in fmt else 0.001   # percents to 2 places, Flow and Windfall to 3
	var shown := str(snappedf(v, step))
	return fmt % shown

# ------------------------------------------------------------------ Post Arts
func _draw_arts() -> void:
	if not _gate("post_arts"): return
	var ch = c()
	var x := content.position.x
	var y := content.position.y
	para(Rect2(Vector2(x, y), Vector2(content.size.x - 480, 50)), Tx.t("ui.works.arts_note"), 16, UiKit.MIST, 2)
	text(Vector2(content.end.x - 470, y + 32), Tx.t("ui.works.art_points") % Game.posts.art_points_free(ch), 19, UiKit.PALE_GOLD)
	var cost := int(ContentDB.config("posts").get("arts", {}).get("reset_taels", 1000))
	btn(Rect2(content.end.x - 230, y, 230, 50), Tx.t("ui.works.art_reset") % UiKit.fmt(cost), "art_reset", null, false,
		not Game.posts.arts(ch).is_empty(), Tx.t("ui.works.no_arts"), 16)
	var arts: Array = ContentDB.config("posts").get("post_arts", [])
	var area := Rect2(content.position + Vector2(0, 64), Vector2(content.size.x, content.size.y - 64))
	list("arts", area, arts.size(), 78, func(i: int, rr: Rect2):
		var a: Dictionary = arts[i]
		var id := str(a.id)
		var lv := Game.posts.art_level(ch, id)
		var mx := int(a.get("max", 1))
		panel(rr, "minor_panel", "selected" if lv > 0 else "normal")
		text(rr.position + Vector2(16, 30), str(a.name), 19, UiKit.PALE_GOLD if lv > 0 else UiKit.PAPER)
		text(rr.position + Vector2(300, 30), Tx.t("ui.works.level_of") % [lv, mx], 16, UiKit.MIST)
		var now := Game.posts._curve_of(a, lv)
		var line := _effect(str(a.text), now) if lv > 0 else Tx.t("ui.works.not_learned")
		if lv < mx: line += "   " + Tx.t("ui.works.next") % _effect(str(a.text), Game.posts._curve_of(a, lv + 1))
		text(rr.position + Vector2(16, 60), fit(line, 15, rr.size.x - 200), 15, UiKit.BRIGHT_JADE if lv > 0 else UiKit.MIST)
		if lv < mx:
			btn(Rect2(rr.end.x - 170, rr.position.y + 14, 154, 50), Tx.t("ui.works.learn"), "art", id, true, Game.posts.art_points_free(ch) > 0,
				Tx.t("sim.posts.no_art_points"), 17)
	)

# ------------------------------------------------------------------ Seal Scripts
func _draw_seals() -> void:
	if not _gate("seal_scripts"): return
	var ch = c()
	para(Rect2(content.position, Vector2(content.size.x, 50)), Tx.t("ui.works.seals_note"), 16, UiKit.MIST, 2)
	var seals: Array = ContentDB.config("posts").get("seals", [])
	var area := Rect2(content.position + Vector2(0, 60), Vector2(content.size.x, content.size.y - 60))
	list("seals", area, seals.size(), 84, func(i: int, rr: Rect2):
		var sd: Dictionary = seals[i]
		var id := str(sd.id)
		var lv := Game.posts.seal_level(id)
		var mx := int(sd.get("max", 10))
		panel(rr, "minor_panel", "selected" if lv > 0 else "normal")
		var craft := str(sd.get("craft", ""))
		icon_at(Rect2(rr.position + Vector2(12, 14), Vector2(52, 52)), str(ContentDB.entry("posts", craft).get("icon", "")) if craft != "" else str(sd.ladder[0]))
		text(rr.position + Vector2(78, 30), str(sd.name), 18, UiKit.PALE_GOLD if lv > 0 else UiKit.PAPER)
		var eff := Game.posts._curve_of(sd, lv)
		var what := Tx.t("ui.works.seal_" + str(sd.gives[0])) % str(snappedf(eff, 0.1))
		if craft != "": what += " · " + Tx.t("ui.works.seal_yours") % Game.posts.seal_effective(ch, sd)
		text(rr.position + Vector2(78, 58), fit(Tx.t("ui.works.level_of") % [lv, mx] + " · " + what, 15, rr.size.x - 470), 15, UiKit.MIST)
		if lv >= mx:
			text(Vector2(rr.end.x - 200, rr.position.y + 48), Tx.t("ui.works.deepest"), 16, UiKit.PALE_GOLD)
			return
		var cost: Dictionary = Game.posts.seal_next_cost(id)
		var have := int(Game.account.storehouse.get(str(cost.item), 0))
		icon_at(Rect2(rr.end.x - 380, rr.position.y + 18, 40, 40), str(cost.item))
		text(Vector2(rr.end.x - 332, rr.position.y + 36), "%s / %s" % [UiKit.fmt(have), UiKit.fmt(int(cost.count))], 15, UiKit.PAPER if have >= int(cost.count) else UiKit.RED)
		text(Vector2(rr.end.x - 332, rr.position.y + 60), fit(ContentDB.item_name(str(cost.item)), 13, 150), 13, UiKit.MIST)
		btn(Rect2(rr.end.x - 170, rr.position.y + 16, 154, 50), Tx.t("ui.works.inscribe"), "seal", id, true, have >= int(cost.count),
			Tx.t("sim.posts.needs_stored") % [int(cost.count), ContentDB.item_name(str(cost.item))], 17)
	)

# ------------------------------------------------------------------ Guardian Steles
func _draw_steles() -> void:
	if not _gate("guardian_steles"): return
	var ch = c()
	para(Rect2(content.position, Vector2(content.size.x - 230, 50)), Tx.t("ui.works.steles_note"), 16, UiKit.MIST, 2)
	currency_pill(Vector2(content.end.x - 210, content.position.y + 6), "silver_tael", Game.economy.balance("silver_tael", ch))
	var crafts: Array = Game.posts.crafts()
	var st: Dictionary = ContentDB.config("posts").get("steles", {})
	var area := Rect2(content.position + Vector2(0, 60), Vector2(content.size.x, content.size.y - 60))
	list("steles", area, crafts.size(), 84, func(i: int, rr: Rect2):
		var cr: Dictionary = crafts[i]
		var craft := str(cr.id)
		var lv := Game.posts.stele_level(craft)
		var mx := int(st.get("max", 40))
		panel(rr, "minor_panel", "selected" if lv > 0 else "normal")
		icon_at(Rect2(rr.position + Vector2(12, 14), Vector2(52, 52)), str(cr.get("icon", "")))
		text(rr.position + Vector2(78, 30), Tx.t("ui.works.stele_of") % str(cr.name), 18, UiKit.PALE_GOLD if lv > 0 else UiKit.PAPER)
		text(rr.position + Vector2(78, 58), Tx.t("ui.works.level_of") % [lv, mx] + " · " + Tx.t("ui.works.stele_power") % str(snappedf(Game.posts.stele_power(craft), 0.1)), 15, UiKit.MIST)
		if lv >= mx:
			text(Vector2(rr.end.x - 200, rr.position.y + 48), Tx.t("ui.works.highest"), 16, UiKit.PALE_GOLD)
			return
		var cost := PostRules.stele_cost(lv)
		var have := int(Game.account.storehouse.get(str(cost.item), 0))
		var can := have >= int(cost.count) and Game.economy.balance("silver_tael", ch) >= int(cost.taels)
		text(Vector2(rr.end.x - 470, rr.position.y + 36), Tx.t("ui.works.taels") % UiKit.fmt(int(cost.taels)), 15, UiKit.PAPER)
		icon_at(Rect2(rr.end.x - 380, rr.position.y + 18, 40, 40), str(cost.item))
		text(Vector2(rr.end.x - 332, rr.position.y + 36), "%s / %s" % [UiKit.fmt(have), UiKit.fmt(int(cost.count))], 15, UiKit.PAPER if have >= int(cost.count) else UiKit.RED)
		text(Vector2(rr.end.x - 332, rr.position.y + 60), fit(ContentDB.item_name(str(cost.item)), 13, 150), 13, UiKit.MIST)
		btn(Rect2(rr.end.x - 170, rr.position.y + 16, 154, 50), Tx.t("ui.works.raise"), "stele", craft, true, can, Tx.t("ui.works.cannot_pay"), 17)
	)

# ------------------------------------------------------------------ Magistrate's Favours
func _draw_favours() -> void:
	if not _gate("magistrates_favours"): return
	var ch = c()
	para(Rect2(content.position, Vector2(content.size.x - 230, 50)), Tx.t("ui.works.favours_note"), 16, UiKit.MIST, 2)
	currency_pill(Vector2(content.end.x - 210, content.position.y + 6), "silver_tael", Game.economy.balance("silver_tael", ch))
	var y := content.position.y + 64
	for f in ContentDB.config("posts").get("favours", []):
		var id := str(f.id)
		var held := Game.posts.has_favour(id)
		var r := Rect2(content.position.x, y, content.size.x, 112)
		panel(r, "minor_panel", "selected" if held else "normal")
		text(r.position + Vector2(16, 32), str(f.name), 19, UiKit.PALE_GOLD if held else UiKit.PAPER)
		text(r.position + Vector2(16, 60), fit(str(f.text), 15, r.size.x - 220), 15, UiKit.MIST)
		if held:
			text(Vector2(r.end.x - 190, r.position.y + 60), Tx.t("ui.works.granted"), 17, UiKit.PALE_GOLD)
		else:
			var parts: Array = [Tx.t("ui.works.taels") % UiKit.fmt(int(f.taels))]
			var can := Game.economy.balance("silver_tael", ch) >= int(f.taels)
			for need in f.get("items", []):
				var have := int(Game.account.storehouse.get(str(need.item), 0))
				parts.append("%s %s (%s)" % [UiKit.fmt(int(need.count)), ContentDB.item_name(str(need.item)), UiKit.fmt(have)])
				if have < int(need.count): can = false
			text(r.position + Vector2(16, 90), fit(Tx.t("ui.works.tribute") % ", ".join(parts), 14, r.size.x - 220), 14, UiKit.BRIGHT_JADE)
			btn(Rect2(r.end.x - 190, r.position.y + 28, 174, 54), Tx.t("ui.works.seek"), "favour", id, true, can, Tx.t("ui.works.cannot_pay"), 17)
		y += 122

# ------------------------------------------------------------------ actions
func on_action(id: String, data) -> void:
	match id:
		"art":
			var r := submit({"type": "learn_post_art", "art": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.learned") % int(r.level))
		"art_reset":
			var r := submit({"type": "reset_post_arts"})
			if r.get("ok", false): flash(Tx.t("ui.works.arts_forgotten"))
		"seal":
			var r := submit({"type": "inscribe_seal", "seal": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.inscribed") % int(r.level))
		"stele":
			var r := submit({"type": "raise_stele", "craft": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.raised") % int(r.level))
		"favour":
			var r := submit({"type": "seek_favour", "favour": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.favour_granted"))
