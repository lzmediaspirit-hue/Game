extends Page
## S50 Keeping Post (V10): the Roll-Call. Every character's post, rates and pouch; settle one or all into the
## Storehouse, burn Hour Incense at a post, switch to someone. Crafts: the active character's craft levels, Finesse
## and tools, and the Chance and Abundance bars of the node in reach. Storehouse: the account's bulk store.

const CAT_ICON := {"ore": "copper_ore", "herb": "willow_moss", "fish": "river_minnow", "insect": "glowfly", "material": "boar_hide"}

func _init() -> void:
	title = Tx.t("ui.posts.title")
	tabs = [{"id": "roll", "label": Tx.t("ui.posts.tab_roll")}, {"id": "crafts", "label": Tx.t("ui.posts.tab_crafts")},
		{"id": "store", "label": Tx.t("ui.posts.tab_store")}, {"id": "bench", "label": Tx.t("ui.posts.tab_bench")},
		{"id": "vows", "label": Tx.t("ui.posts.tab_vows")}]

func setup() -> void:
	var want := str(args.get("tab", ""))
	for i in tabs.size():
		if str(tabs[i].id) == want: tab = i

func draw_page() -> void:
	match tab:
		0: _draw_roll()
		1: _draw_crafts()
		2: _draw_store()
		3: _draw_bench()
		4: _draw_vows()

# ------------------------------------------------------------------ Roll-Call
func _draw_roll() -> void:
	var rows: Array = Game.posts.roll_call()
	var top := Rect2(content.position, Vector2(content.size.x, 60))
	para(Rect2(top.position + Vector2(0, 6), Vector2(content.size.x - 520, 56)), Tx.t("ui.posts.roll_note"), 16, UiKit.MIST, 2)
	var ch = c()
	var here := str(Game.room_rt.room_id) if Game.room_rt != null else ""
	if ch != null and here != "" and Game.posts.vigil_allowed(here):
		btn(Rect2(content.end.x - 500, top.position.y + 4, 250, 52), Tx.t("ui.posts.keep_vigil"), "vigil", null, false,
			Unlocks.is_unlocked(ch.id, "keeping_post"), Unlocks.locked_text("keeping_post"))
	btn(Rect2(content.end.x - 240, top.position.y + 4, 240, 52), Tx.t("ui.posts.settle_all"), "settle_all", null, true)
	var area := Rect2(content.position + Vector2(0, 70), Vector2(content.size.x, content.size.y - 70))
	list("roll", area, rows.size(), 104, func(i: int, rr: Rect2):
		var row: Dictionary = rows[i]
		panel(rr, "minor_panel", "selected" if row.active else "normal")
		text(rr.position + Vector2(18, 32), str(row.name), 22, UiKit.PALE_GOLD if row.active else UiKit.PAPER)
		var p: Dictionary = row.post
		var r: Dictionary = row.rates
		if p.is_empty():
			text(rr.position + Vector2(18, 62), Tx.t("ui.posts.no_post"), 17, UiKit.HOLLOW)
		elif str(p.get("kind", "")) == "vigil":
			text(rr.position + Vector2(18, 60), fit(Tx.t("ui.posts.vigil_at") % str(ContentDB.room(str(p.get("room", ""))).get("name", "")), 17, 330), 17, UiKit.RED.lightened(0.3))
			var state := Tx.t("ui.posts.playing") if row.active else Tx.t("ui.posts.away_for") % _dur(float(row.since_h))
			text(rr.position + Vector2(18, 86), state, 15, UiKit.MIST)
			text(Vector2(rr.position.x + 360, rr.position.y + 35), Tx.t("ui.posts.kills_h") % UiKit.fmt(int(float(r.get("kills_h", 0.0)))), 15, UiKit.PAPER)
			if int(r.get("sweep", 0)) > 0: text(Vector2(rr.position.x + 360, rr.position.y + 60), Tx.t("ui.posts.sweep") % int(r.sweep), 15, UiKit.PALE_GOLD)
			text(Vector2(rr.position.x + 540, rr.position.y + 35), Tx.t("ui.posts.in_pouch") % UiKit.fmt(int(row.pouch)), 15, UiKit.PAPER)
		else:
			var craft := ContentDB.entry("posts", str(p.get("craft", "")))
			var where := "%s · %s" % [str(craft.get("short", "")), str(ContentDB.room(str(p.get("room", ""))).get("name", ""))]
			text(rr.position + Vector2(18, 60), fit(where, 17, 330), 17, UiKit.BRIGHT_JADE)
			var lvtxt := Tx.t("ui.posts.level_short") % int(r.get("level", 1))
			var state := Tx.t("ui.posts.playing") if row.active else Tx.t("ui.posts.away_for") % _dur(float(row.since_h))
			text(rr.position + Vector2(18, 86), "%s · %s" % [lvtxt, state], 15, UiKit.MIST)
			var x := rr.position.x + 360
			var k := 0
			for id in r.get("items", {}):
				if k >= 3: break
				icon_at(Rect2(x, rr.position.y + 16 + k * 26, 24, 24), str(id))
				text(Vector2(x + 30, rr.position.y + 35 + k * 26), Tx.t("ui.posts.per_hour") % UiKit.fmt(snappedf(float(r.items[id]), 0.1)), 15, UiKit.PAPER)
				k += 1
			var fill := float(row.fill_h)
			var fill_txt := Tx.t("ui.posts.pouch_full") if fill <= 0.0 else (Tx.t("ui.posts.full_in") % _dur(fill) if fill < INF else "")
			text(Vector2(rr.position.x + 540, rr.position.y + 35), Tx.t("ui.posts.in_pouch") % UiKit.fmt(int(row.pouch)), 15, UiKit.PAPER)
			text(Vector2(rr.position.x + 540, rr.position.y + 60), fill_txt, 15, UiKit.RED if fill <= 0.0 else UiKit.MIST)
		if not row.active:
			btn(Rect2(rr.end.x - 150, rr.position.y + 10, 136, 40), Tx.t("ui.posts.switch"), "switch", int(row.slot), false, true, "", 18)
			if not p.is_empty():
				var inc := _incense()
				btn(Rect2(rr.end.x - 300, rr.position.y + 54, 136, 40), Tx.t("ui.posts.incense"), "incense", str(row.id), false, inc != "",
					Tx.t("ui.posts.no_incense"), 18)
				btn(Rect2(rr.end.x - 150, rr.position.y + 54, 136, 40), Tx.t("ui.posts.settle"), "settle", str(row.id), false, true, "", 18)
	)

## The shortest Hour Incense the active character carries ("" when none).
func _incense() -> String:
	var ch = c()
	if ch == null: return ""
	for id in ["hour_incense_1", "hour_incense_2", "hour_incense_4", "hour_incense_12", "hour_incense_24", "hour_incense_72", "wandering_incense"]:
		if ch.inventory.count(id) > 0: return id
	return ""

# ------------------------------------------------------------------ Crafts
func _draw_crafts() -> void:
	var ch = c()
	if ch == null: return
	var left := Rect2(content.position, Vector2(620, content.size.y))
	var list_crafts: Array = Game.posts.crafts()
	var step := minf(126.0, (left.size.y + 6.0) / maxf(1.0, float(list_crafts.size())))
	var y := left.position.y
	for cd in list_crafts:
		var craft := str(cd.id)
		var r := Rect2(left.position.x, y, left.size.x, step - 6.0)
		panel(r)
		icon_at(Rect2(r.position + Vector2(12, 10), Vector2(36, 36)), str(cd.get("icon", "")))
		var known: bool = Game.posts.craft_known(ch, craft)
		text(r.position + Vector2(60, 30), str(cd.name), 19, UiKit.PAPER if known else UiKit.HOLLOW)
		if not known:
			text(r.position + Vector2(60, 56), fit(Unlocks.locked_text(str(cd.get("unlock", craft))), 15, r.size.x - 80), 15, UiKit.HOLLOW)
			y += step
			continue
		var info := PostRules.level_info(Game.posts.xp(ch, craft))
		text(Vector2(r.end.x - 140, r.position.y + 30), Tx.t("ui.posts.level_short") % int(info.level), 19, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 120)
		bar(Rect2(r.position + Vector2(60, 38), Vector2(r.size.x - 80, 22)), float(info.into) / maxf(1.0, float(info.need)), UiKit.JADE,
			"%s / %s" % [UiKit.fmt(int(info.into)), UiKit.fmt(int(info.need))])
		var tool: Dictionary = Game.posts.tool_of(ch, craft)
		var tool_name := ContentDB.item_name(str(tool.item)) if not tool.is_empty() else Tx.t("ui.posts.bare_hands")
		var line := Tx.t("ui.posts.finesse_line") % [UiKit.fmt(int(Game.posts.finesse_of(ch, craft))), fit(tool_name, 15, 220)]
		if craft == "rites": line += "  ·  " + Tx.t("ui.posts.charge") % int(Game.posts.rite_charge(ch))
		if craft == "snaring": line += "  ·  " + Tx.t("ui.posts.snares_out") % (Game.posts.snares(ch) as Array).size()
		text(r.position + Vector2(60, minf(r.size.y - 8.0, 82.0)), line, 14, UiKit.MIST)
		y += step
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	_draw_node_info(ch, right.grow(-16))

## Post Info for the node in reach: each output's Chance bar (jade) or, once full, its Abundance bar (gold).
func _draw_node_info(ch, r: Rect2) -> void:
	var o := {}
	if Game.world != null and Game.room_rt != null:
		var ctx: Dictionary = Game.world.query_context(ch)
		if ctx.has("object"): o = Game.room_rt.object_def(str(ctx.object))
	if o.is_empty() or Game.posts.craft_of_object(o) == "":
		var here := str(Game.room_rt.room_id) if Game.room_rt != null else ""
		if here != "" and Game.posts.vigil_allowed(here):
			_draw_vigil_info(ch, r, here)
			return
		heading(r.position + Vector2(0, 24), Tx.t("ui.posts.node_info"), r.size.x)
		para(Rect2(r.position + Vector2(0, 44), Vector2(r.size.x, 200)), Tx.t("ui.posts.node_info_none"), 17, UiKit.MIST)
		return
	var rates: Dictionary = Game.posts.rates_at(ch, o)
	heading(r.position + Vector2(0, 24), Tx.t("ui.posts.at_this_node"), r.size.x)
	text(r.position + Vector2(0, 62), Tx.t("ui.posts.finesse_dil") % [UiKit.fmt(int(float(rates.get("finesse", 0.0)))), int(round(float(rates.get("diligence", 0.52)) * 100.0))], 16, UiKit.MIST)
	var y := r.position.y + 80
	var lv: int = Game.posts.level(ch, Game.posts.craft_of_object(o))
	for out in Game.posts.outputs_of(o):
		icon_at(Rect2(r.position.x, y, 32, 32), str(out.item))
		text(Vector2(r.position.x + 40, y + 20), fit(ContentDB.item_name(str(out.item)), 16, r.size.x - 40), 16, UiKit.PAPER)
		y += 36
		if int(out.gate) > lv:
			text(Vector2(r.position.x + 40, y + 16), Tx.t("ui.posts.gate") % int(out.gate), 15, UiKit.HOLLOW)
			y += 30
			continue
		var yv := PostRules.yield_of(float(rates.get("finesse", 0.0)), float(out.toughness))
		if float(yv.chance) < 1.0:
			bar(Rect2(r.position.x + 40, y, r.size.x - 40, 24), float(yv.chance), UiKit.BRIGHT_JADE, Tx.t("ui.posts.chance") % int(round(float(yv.chance) * 100.0)))
		else:
			bar(Rect2(r.position.x + 40, y, r.size.x - 40, 24), float(yv.abundance_progress), UiKit.GOLD, Tx.t("ui.posts.abundance") % int(yv.abundance))
		y += 28
		text(Vector2(r.position.x + 40, y + 16), Tx.t("ui.posts.next_at") % UiKit.fmt(int(float(yv.next_finesse))), 14, UiKit.MIST)
		y += 30
		if y > r.end.y - 40: break

## Vigil Info for the room: kills an hour and what limits them, the Sweep tier, blows landed, and how long the
## character would last on the provisions it carries.
func _draw_vigil_info(ch, r: Rect2, room: String) -> void:
	var pr: Dictionary = Game.posts.vigil_profile(ch, room)
	heading(r.position + Vector2(0, 24), Tx.t("ui.posts.vigil_info"), r.size.x)
	if pr.is_empty(): return
	var y := r.position.y + 62
	var rows := [
		[Tx.t("ui.posts.v_kills"), UiKit.fmt(int(float(pr.kills_h)))],
		[Tx.t("ui.posts.v_limit"), Tx.t("ui.posts.v_spawn") if float(pr.spawn_h) < float(pr.fighter_h) else Tx.t("ui.posts.v_blade")],
		[Tx.t("ui.posts.v_hit"), "%d%% · %s" % [int(round(100.0 * float(pr.hit))), UiKit.fmt(int(float(pr.avg_hit)))]],
		[Tx.t("ui.posts.v_sweep"), Tx.t("ui.posts.v_sweep_val") % [int(pr.sweep_tier), float(pr.sweep)]],
		[Tx.t("ui.posts.v_dil"), "%d%%" % int(round(100.0 * float(pr.diligence)))],
		[Tx.t("ui.posts.v_taken"), "%s / %s" % [UiKit.fmt(int(float(pr.dmg_h))), UiKit.fmt(int(float(pr.regen_h)))]],
		[Tx.t("ui.posts.v_food"), (ContentDB.item_name(str(pr.food)) + " ×%d" % int(pr.food_count)) if str(pr.food) != "" else Tx.t("ui.posts.v_no_food")],
	]
	var sv := PostRules.survivability(ch.pools.max_hp, float(pr.dmg_h), float(pr.regen_h), float(pr.heal_each), int(pr.food_count), 12.0)
	rows.append([Tx.t("ui.posts.v_alive"), "%d%%" % int(round(100.0 * float(sv.alive)))])
	for row in rows:
		text(Vector2(r.position.x, y + 18), str(row[0]), 16, UiKit.MIST)
		text(Vector2(r.position.x, y + 18), str(row[1]), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x)
		y += 32

# ------------------------------------------------------------------ Apprentice Bench (V10c)
func _draw_bench() -> void:
	var ch = c()
	if ch == null: return
	if not Unlocks.is_unlocked(ch.id, "apprentice_bench"):
		para(Rect2(content.position + Vector2(0, 20), Vector2(content.size.x, 80)), Unlocks.locked_text("apprentice_bench"), 18, UiKit.HOLLOW)
		return
	Game.posts._bench_settle(ch)
	var b: Dictionary = Game.posts.bench(ch)
	var x := content.position.x
	var y := content.position.y
	para(Rect2(Vector2(x, y), Vector2(content.size.x - 260, 50)), Tx.t("ui.posts.bench_note") % UiKit.fmt(int(Game.posts.bench_capacity(ch))), 16, UiKit.MIST, 2)
	btn(Rect2(content.end.x - 240, y, 240, 52), Tx.t("ui.posts.bench_collect"), "bench_collect", null, true)
	y += 64
	text(Vector2(x, y + 22), Tx.t("ui.posts.bench_points") % Game.posts.bench_points_free(ch), 18, UiKit.PALE_GOLD)
	var bx := x + 300
	for k in ["speed", "capacity", "exp"]:
		btn(Rect2(bx, y, 200, 44), Tx.t("ui.posts.bench_" + k) % int(b.points.get(k, 0)), "bench_point", k, false, Game.posts.bench_points_free(ch) > 0, Tx.t("ui.posts.no_points_text"), 16)
		bx += 212
	y += 60
	var comps: Array = ContentDB.config("posts").get("bench", {}).get("components", [])
	for i in Game.posts.apprentices(ch):
		var cur := str(b.slots[i]) if i < b.slots.size() else ""
		var r := Rect2(x, y, content.size.x, 76)
		panel(r)
		text(r.position + Vector2(16, 30), Tx.t("ui.posts.apprentice") % (i + 1), 18, UiKit.PAPER)
		if cur != "":
			icon_at(Rect2(r.position + Vector2(200, 12), Vector2(48, 48)), cur)
			text(r.position + Vector2(260, 32), ContentDB.item_name(cur), 18, UiKit.PAPER)
			text(r.position + Vector2(260, 60), Tx.t("ui.posts.bench_rate") % [snappedf(Game.posts.bench_rate_of(ch, cur), 0.1), UiKit.fmt(int(float(b.stock.get(cur, 0.0))))], 15, UiKit.MIST)
		else:
			text(r.position + Vector2(200, 44), Tx.t("ui.posts.bench_idle"), 17, UiKit.HOLLOW)
		btn(Rect2(r.end.x - 170, r.position.y + 14, 154, 48), Tx.t("ui.posts.bench_change"), "bench_next", [i, cur], false, true, "", 17)
		y += 84
	para(Rect2(Vector2(x, y + 6), Vector2(content.size.x, 60)), Tx.t("ui.posts.bench_more") % [Game.posts.total_craft_levels(ch)], 15, UiKit.MIST, 2)

## The next component this character may set an apprentice to (by Level), after `cur` ("" = idle).
func _next_component(ch, cur: String) -> String:
	var opts: Array = [""]
	for cp in ContentDB.config("posts").get("bench", {}).get("components", []):
		if ProgressionRules.level(ch) >= int(cp.get("gate", 1)): opts.append(str(cp.item))
	var i := opts.find(cur)
	return str(opts[(i + 1) % opts.size()])

# ------------------------------------------------------------------ Post Vows (V10c)
func _draw_vows() -> void:
	var ch = c()
	if ch == null: return
	if not Unlocks.is_unlocked(ch.id, "ancestral_rites"):
		para(Rect2(content.position + Vector2(0, 20), Vector2(content.size.x, 80)), Unlocks.locked_text("ancestral_rites"), 18, UiKit.HOLLOW)
		return
	var wisps := int(ch.inventory.count("spirit_wisp")) + int(Game.account.storehouse.get("spirit_wisp", 0))
	para(Rect2(content.position, Vector2(content.size.x - 240, 50)), Tx.t("ui.posts.vows_note"), 16, UiKit.MIST, 2)
	icon_at(Rect2(content.end.x - 220, content.position.y + 4, 36, 36), "spirit_wisp")
	text(Vector2(content.end.x - 176, content.position.y + 30), UiKit.fmt(wisps), 20, UiKit.PALE_GOLD)
	var y := content.position.y + 60
	var held: Array = Game.posts.held_vows(ch)
	for v in ContentDB.config("posts").get("post_vows", []):
		var id := str(v.id)
		var r := Rect2(content.position.x, y, content.size.x, 76)
		panel(r, "minor_panel", "selected" if held.has(id) else "normal")
		text(r.position + Vector2(16, 30), str(v.name), 18, UiKit.PALE_GOLD if held.has(id) else UiKit.PAPER)
		text(r.position + Vector2(16, 58), fit(str(v.text), 15, r.size.x - 230), 15, UiKit.MIST)
		if not Game.account.post_vows.has(id):
			btn(Rect2(r.end.x - 196, r.position.y + 14, 180, 48), Tx.t("ui.posts.vow_learn") % int(v.cost), "vow_learn", id, false, wisps >= int(v.cost), Tx.t("ui.posts.vow_need"), 16)
		elif held.has(id):
			btn(Rect2(r.end.x - 196, r.position.y + 14, 180, 48), Tx.t("ui.posts.vow_drop"), "vow_off", id, false, true, "", 16)
		else:
			btn(Rect2(r.end.x - 196, r.position.y + 14, 180, 48), Tx.t("ui.posts.vow_hold"), "vow_on", id, true, held.size() < 2, Tx.t("sim.posts.vows_full"), 16)
		y += 82

# ------------------------------------------------------------------ Storehouse
func _draw_store() -> void:
	var ids: Array = Game.account.storehouse.keys()
	ids.sort()
	para(Rect2(content.position, Vector2(content.size.x, 50)), Tx.t("ui.posts.store_note"), 17, UiKit.MIST, 2)
	if ids.is_empty():
		text(content.position + Vector2(0, 110), Tx.t("ui.posts.store_empty"), 19, UiKit.HOLLOW)
		return
	var cols := 9
	var cell := 110.0
	var area := Rect2(content.position + Vector2(0, 60), Vector2(content.size.x, content.size.y - 60))
	var nrows := int(ceil(ids.size() / float(cols)))
	list("store", area, nrows, cell + 26, func(ri: int, rr: Rect2):
		for k in cols:
			var idx := ri * cols + k
			if idx >= ids.size(): break
			var id := str(ids[idx])
			var sr := Rect2(rr.position + Vector2(k * (cell + 10), 0), Vector2(cell - 20, cell - 20))
			slot_box(sr, id, 0, "", "withdraw", id)
			UiKit.draw_outlined(self, UiKit.fmt(int(Game.account.storehouse[id])), sr.position + Vector2(0, sr.size.y + 20), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, sr.size.x)
	)

# ------------------------------------------------------------------ actions
func on_action(id: String, data) -> void:
	match id:
		"settle_all":
			var r := submit({"type": "settle_all"})
			if r.get("ok", false): flash(Tx.t("ui.posts.settled_n") % (r.get("ledgers", []) as Array).size())
		"settle":
			var r := submit({"type": "settle_post", "character": str(data)})
			if r.get("ok", false):
				submit({"type": "send_to_storehouse", "character": str(data)})
				flash(Tx.t("ui.posts.settled_one"))
		"incense":
			var inc := _incense()
			if inc == "": return
			var r := submit({"type": "burn_incense", "character": str(data), "item": inc})
			if r.get("ok", false): flash(Tx.t("ui.posts.incense_burned") % _dur(float(r.hours)))
		"switch": navigate.emit("_switch", {"slot": int(data)})
		"bench_collect":
			var r := submit({"type": "bench_collect"})
			if r.get("ok", false): flash(Tx.t("ui.posts.bench_collected"))
		"bench_point": submit({"type": "bench_point", "kind": str(data)})
		"bench_next": submit({"type": "bench_assign", "slot": int(data[0]), "item": _next_component(c(), str(data[1]))})
		"vow_learn": submit({"type": "learn_post_vow", "vow": str(data)})
		"vow_on": submit({"type": "pledge_post_vow", "vow": str(data), "on": true})
		"vow_off": submit({"type": "pledge_post_vow", "vow": str(data), "on": false})
		"vigil":
			var r := submit({"type": "take_vigil"})
			if r.get("ok", false): flash(Tx.t("ui.posts.vigil_taken"))
		"withdraw":
			var r := submit({"type": "withdraw_storehouse", "item": str(data), "count": 50})
			if r.get("ok", false): flash(Tx.t("ui.posts.withdrew") % [int(r.count), ContentDB.item_name(str(data))])

func _dur(h: float) -> String:
	if h >= 48.0: return Tx.t("ui.posts.days") % int(h / 24.0)
	if h >= 1.0: return Tx.t("ui.posts.hours_minutes") % [int(h), int(fmod(h * 60.0, 60.0))]
	return Tx.t("ui.posts.minutes") % int(h * 60.0)
