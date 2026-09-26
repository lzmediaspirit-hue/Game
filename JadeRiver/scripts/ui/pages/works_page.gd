extends Page
## S50 Keeping Post (V10d): the account web behind the posts. Arts: the active character's Post Arts, bought with
## points from its craft levels. Seals: Seal Scripts inscribed with Storehouse goods. Steles: Guardian Steles raised
## with silver and ore. Favours: the Magistrate's Favours, earned once each with silver and tribute. Furnace: the
## Calcination Furnace's salt lines. Flags: Formation Flags over posts. Mirror: the Mirror of Echoes' slots.

func _init() -> void:
	title = Tx.t("ui.works.title")
	tabs = [{"id": "arts", "label": Tx.t("ui.works.tab_arts")}, {"id": "seals", "label": Tx.t("ui.works.tab_seals")},
		{"id": "steles", "label": Tx.t("ui.works.tab_steles")}, {"id": "favours", "label": Tx.t("ui.works.tab_favours")},
		{"id": "furnace", "label": Tx.t("ui.works.tab_furnace")}, {"id": "flags", "label": Tx.t("ui.works.tab_flags")},
		{"id": "mirror", "label": Tx.t("ui.works.tab_mirror")}]

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
		4: _draw_furnace()
		5: _draw_flags()
		6: _draw_mirror()

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

# ------------------------------------------------------------------ the Calcination Furnace
func _draw_furnace() -> void:
	if not _gate("calcination"): return
	Game.posts.calcination_settle()
	para(Rect2(content.position, Vector2(content.size.x, 50)), Tx.t("ui.works.furnace_note"), 16, UiKit.MIST, 2)
	var salts: Array = ContentDB.config("posts").get("salts", [])
	var area := Rect2(content.position + Vector2(0, 60), Vector2(content.size.x, content.size.y - 60))
	list("furnace", area, salts.size(), 96, func(i: int, rr: Rect2):
		var sd: Dictionary = salts[i]
		var id := str(sd.id)
		var ln: Dictionary = Game.posts.salt_line(id)
		var open := Game.posts.line_open(id)
		var rank := int(ln.rank)
		panel(rr, "minor_panel", "selected" if ln.get("on", false) else "normal")
		icon_at(Rect2(rr.position + Vector2(12, 18), Vector2(56, 56)), id)
		text(rr.position + Vector2(82, 30), "%s · %s" % [ContentDB.item_name(id), Tx.t("ui.works.rank") % rank], 18, UiKit.PALE_GOLD if ln.get("on", false) else UiKit.PAPER)
		if not open:
			text(rr.position + Vector2(82, 62), Tx.t("sim.posts.line_closed") % int(PostRules.rule_calc("open_rank", 3)), 15, UiKit.HOLLOW)
			return
		var parts: Array = []
		for inp in sd.get("inputs", []):
			parts.append("%d %s (%s)" % [PostRules.calcination_cost(rank, int(inp.qty)), ContentDB.item_name(str(inp.item)), UiKit.fmt(int(Game.account.storehouse.get(str(inp.item), 0)))])
		var every := Tx.t("ui.works.every") % _dur_s(float(sd.get("cycle_s", 900)))
		text(rr.position + Vector2(82, 58), fit(every + ": " + ", ".join(parts), 14, rr.size.x - 440), 14, UiKit.MIST)
		text(rr.position + Vector2(82, 82), Tx.t("ui.works.fire") % [UiKit.fmt(int(ln.get("fire", 0))), PostRules.calcination_fire(rank),
			UiKit.fmt(int(ln.get("refined", 0))), UiKit.fmt(PostRules.calcination_rank_need(rank))], 14, UiKit.BRIGHT_JADE)
		var on: bool = ln.get("on", false)
		btn(Rect2(rr.end.x - 340, rr.position.y + 22, 160, 50), Tx.t("ui.works.bank_line") if on else Tx.t("ui.works.light_line"), "line", [id, not on], not on, true, "", 16)
		btn(Rect2(rr.end.x - 170, rr.position.y + 22, 154, 50), Tx.t("ui.works.refine"), "refine", id, false, int(ln.get("fire", 0)) > 0, Tx.t("sim.posts.no_fire"), 16)
	)

# ------------------------------------------------------------------ Formation Flags
func _draw_flags() -> void:
	if not _gate("formation_flags"): return
	var ch = c()
	var fl: Dictionary = ContentDB.config("posts").get("flags", {})
	var x := content.position.x
	var y := content.position.y
	para(Rect2(Vector2(x, y), Vector2(content.size.x - 460, 60)), Tx.t("ui.works.flags_note") % int(fl.get("max", 2)), 16, UiKit.MIST, 3)
	var here := str(ch.position.get("room", ""))
	var cost := UiKit.fmt(int(fl.get("plant_taels", 500)))
	btn(Rect2(content.end.x - 450, y, 220, 52), Tx.t("ui.works.plant_plain") % cost, "plant", "plain", true, true, "", 15)
	btn(Rect2(content.end.x - 220, y, 220, 52), Tx.t("ui.works.plant_deep") % cost, "plant", "deep", false, true, "", 15)
	y += 76
	var list_flags: Array = Game.posts.flags()
	if list_flags.is_empty():
		text(Vector2(x, y + 30), Tx.t("ui.works.no_flags") % str(ContentDB.room(here).get("name", here)), 18, UiKit.HOLLOW)
		return
	for i in list_flags.size():
		var f: Dictionary = list_flags[i]
		var r := Rect2(x, y, content.size.x, 88)
		panel(r, "minor_panel", "selected" if str(f.room) == here else "normal")
		var kind := str(f.kind)
		var lv := int(f.get("level", 0))
		text(r.position + Vector2(16, 32), "%s · %s" % [Tx.t("ui.works.flag_" + kind), str(ContentDB.room(str(f.room)).get("name", ""))], 18, UiKit.PALE_GOLD)
		var eff := Tx.t("ui.works.flag_eff_" + kind) % str(snappedf(PostRules.flag_value(kind, lv), 0.1))
		text(r.position + Vector2(16, 62), Tx.t("ui.works.level_of") % [lv, int(fl.get("max_level", 20))] + " · " + eff, 15, UiKit.MIST)
		var nc := PostRules.flag_cost(lv)
		if not nc.is_empty() and lv < int(fl.get("max_level", 20)):
			var have := int(Game.account.storehouse.get(str(nc.salt), 0))
			icon_at(Rect2(r.end.x - 470, r.position.y + 22, 40, 40), str(nc.salt))
			text(Vector2(r.end.x - 422, r.position.y + 48), "%s / %s" % [UiKit.fmt(have), UiKit.fmt(int(nc.salt_count))], 15, UiKit.PAPER if have >= int(nc.salt_count) else UiKit.RED)
			btn(Rect2(r.end.x - 330, r.position.y + 18, 150, 50), Tx.t("ui.works.raise"), "flag_raise", i, true, have >= int(nc.salt_count), Tx.t("ui.works.cannot_pay"), 16)
		btn(Rect2(r.end.x - 170, r.position.y + 18, 154, 50), Tx.t("ui.works.uproot"), "flag_uproot", i, false, true, "", 16)
		y += 96

# ------------------------------------------------------------------ the Mirror of Echoes
func _draw_mirror() -> void:
	if not _gate("mirror_of_echoes"): return
	var ch = c()
	Game.posts.mirror_settle()
	var x := content.position.x
	var y := content.position.y
	para(Rect2(Vector2(x, y), Vector2(content.size.x, 60)), Tx.t("ui.works.mirror_note"), 16, UiKit.MIST, 3)
	y += 70
	var lv := Game.posts.mirror_level()
	if lv <= 0:
		text(Vector2(x, y + 30), Tx.t("ui.works.mirror_unbuilt"), 18, UiKit.HOLLOW)
		return
	var share := Game.posts.art_sum(ch, "echo_share") * (1.0 + float(ContentDB.config("posts").get("mirror", {}).get("per_level", 0.05)) * lv)
	text(Vector2(x, y + 24), Tx.t("ui.works.mirror_level") % [lv, str(snappedf(share, 0.1))], 17, UiKit.PALE_GOLD)
	y += 44
	var slots: Array = Game.posts.mirror_slots()
	for i in Game.posts.mirror_slot_count():
		var sl: Dictionary = slots[i] if i < slots.size() else {}
		var r := Rect2(x, y, content.size.x, 96)
		panel(r, "minor_panel", "selected" if not sl.is_empty() else "normal")
		text(r.position + Vector2(16, 32), Tx.t("ui.works.mirror_slot") % (i + 1), 18, UiKit.PAPER)
		if sl.is_empty():
			text(r.position + Vector2(16, 64), Tx.t("ui.works.mirror_empty"), 15, UiKit.HOLLOW)
		else:
			text(r.position + Vector2(200, 32), fit(str(sl.get("name", "")), 16, 300), 16, UiKit.PALE_GOLD)
			var k := 0
			for id in sl.get("items", {}):
				if k >= 3: break
				icon_at(Rect2(r.position.x + 16 + k * 190, r.position.y + 50, 32, 32), str(id))
				text(Vector2(r.position.x + 54 + k * 190, r.position.y + 72), Tx.t("ui.posts.per_hour") % UiKit.fmt(snappedf(float(sl.items[id]), 0.1)), 15, UiKit.PAPER)
				k += 1
		btn(Rect2(r.end.x - 250, r.position.y + 22, 234, 52), Tx.t("ui.works.mirror_inscribe") % str(ch.name), "echo", i, true,
			Game.posts.art_level(ch, "echo_sampling") > 0 and Game.posts.has_post(ch), Tx.t("sim.posts.needs_echo"), 15)
		y += 104

func _dur_s(secs: float) -> String:
	if secs >= 3600.0: return Tx.t("ui.posts.hours_minutes") % [int(secs / 3600.0), int(fmod(secs / 60.0, 60.0))]
	return Tx.t("ui.posts.minutes") % int(secs / 60.0)

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
		"line": submit({"type": "calcine_line", "line": str(data[0]), "on": bool(data[1])})
		"refine":
			var r := submit({"type": "refine_line", "line": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.refined") % [int(r.salts), ContentDB.item_name(str(data)), int(r.rank)])
		"plant":
			var r := submit({"type": "plant_flag", "kind": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.planted"))
		"flag_raise": submit({"type": "raise_flag", "index": int(data)})
		"flag_uproot": submit({"type": "uproot_flag", "index": int(data)})
		"echo":
			var r := submit({"type": "echo_inscribe", "slot": int(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.echoed"))
