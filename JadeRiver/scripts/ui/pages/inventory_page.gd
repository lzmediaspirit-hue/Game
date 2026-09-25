extends Page
## Inventory (S14, Part 9.6): equipment view around the avatar, the Spirit Gourd
## bag grid, key items and an item detail panel with every action the item allows.

const Avatar = preload("res://scripts/avatar.gd")
const SLOT_POS := {"hat": Vector2(0, 0), "robe": Vector2(0, 1), "trousers": Vector2(0, 2), "boots": Vector2(0, 3),
	"weapon": Vector2(1, 0), "gourd": Vector2(1, 1), "cape": Vector2(1, 2), "talisman": Vector2(1, 3)}
var SLOT_LABEL := {"weapon": Tx.t("ui.inventory.weapon"), "hat": Tx.t("ui.inventory.hat"), "robe": Tx.t("ui.inventory.robe"), "trousers": Tx.t("ui.inventory.trousers"), "boots": Tx.t("ui.inventory.boots"), "gourd": Tx.t("ui.inventory.gourd"),
	"cape": Tx.t("ui.inventory.cape"), "talisman": Tx.t("ui.inventory.talisman")}

var sel := {}          # {"bag": index} | {"slot": name} | {"key": index}
var doll: Node2D
var sort_by := "type"

func _init() -> void:
	title = Tx.t("ui.inventory.bag")
	tabs = [{"id": "bag", "label": Tx.t("ui.inventory.spirit_gourd")}, {"id": "key", "label": Tx.t("ui.inventory.key_items")}]

func setup() -> void:
	if is_instance_valid(doll): doll.queue_free()
	doll = Avatar.new()
	doll.position = Vector2(236, 468)
	doll.scale = Vector2.ONE * 2.0
	add_child(doll)
	_refresh_doll()

func _refresh_doll() -> void:
	if c() == null or not is_instance_valid(doll): return
	doll.outfit = InventoryAuthority.outfit_for(c())
	doll.last_key = ""
	doll.play("idle")

func on_event(name: String, _p: Dictionary) -> void:
	if name in ["equipment_changed", "item_added", "item_removed"]: _refresh_doll()
	queue_redraw()

func slot_locked(slot: String) -> String:
	var ch = c()
	match slot:
		"weapon": return "" if Unlocks.is_unlocked(ch.id, "weapons") else Tx.t("ui.inventory.fists_only_until_the_weapon")
		"cape": return "" if Unlocks.is_unlocked(ch.id, "cape_slot") else Tx.t("ui.inventory.cape_slot_opens_at_heaven")
		"talisman": return "" if Unlocks.is_unlocked(ch.id, "spirit_sense") else Tx.t("ui.inventory.soul_talisman_slot_opens_at")
	return ""

func _process(delta: float) -> void:
	super._process(delta)
	# The paper doll belongs to the Spirit Gourd tab only.
	if is_instance_valid(doll): doll.visible = str(tabs[tab].id) == "bag"

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var inv: InventoryState = ch.inventory
	if str(tabs[tab].id) == "bag":
		# Equipment around the doll.
		panel(Rect2(content.position.x, content.position.y, 360, content.size.y))
		for slot in SLOT_POS:
			var gp: Vector2 = SLOT_POS[slot]
			var r := Rect2(content.position.x + 16 + gp.x * 264, content.position.y + 20 + gp.y * 112, 64, 64)
			var inst = inv.equipped.get(slot)
			var why := slot_locked(slot)
			if inst != null:
				slot_box(r, str(inst.id), 1, str(inst.get("quality", "")), "slot", slot, sel.get("slot", "") == slot)
			else:
				draw_style_box(UiKit.style("slot", "disabled" if why != "" else "normal"), r)
				if slot == "weapon" and why != "": icon_at(r.grow(-10), "fist")
				if why != "": _lock_icon(r.position + Vector2(46, 4))
				region(r, "slot", slot, true)
			text(Vector2(r.position.x - 10, r.end.y + 20), SLOT_LABEL[slot], 15, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 84)
		# Bag grid.
		var grid := Rect2(content.position.x + 380, content.position.y, 420, content.size.y - 56)
		panel(grid.grow(4))
		var cols := 6
		var cell := 66.0
		var rows := int(ceil(float(inv.bag.size()) / cols))
		list("bag", grid, rows, cell + 4, func(row: int, rr: Rect2):
			for col in cols:
				var i := row * cols + col
				if i >= inv.bag.size(): break
				var s = inv.bag[i]
				var r2 := Rect2(rr.position.x + 6 + col * (cell + 2), rr.position.y, cell, cell)
				if s == null:
					draw_style_box(UiKit.style("slot"), r2)
					region(r2, "bag", i)
				else:
					slot_box(r2, str(s.id), int(s.get("count", 1)), str(s.get("quality", "")), "bag", i, int(sel.get("bag", -1)) == i,
						inv.locked.has(int(s.get("uid", -1))))
					pill_marks(r2, int(s.get("marks", 0)))
					if inv.new_items.has(str(s.id)): draw_circle(r2.position + Vector2(cell - 8, 8), 5, UiKit.BRIGHT_JADE)
		)
		text(Vector2(grid.position.x, grid.end.y + 36), "%d / %d" % [inv.bag.size() - inv.free_slots(), inv.capacity()], 18, UiKit.MIST)
		btn(Rect2(grid.end.x - 140, grid.end.y + 10, 140, 44), Tx.t("ui.inventory.sort"), "sort")
	else:
		var r := Rect2(content.position.x, content.position.y, 800, content.size.y)
		panel(r)
		list("keys", r.grow(-10), inv.key_items.size(), 76, func(i: int, rr: Rect2):
			var k: Dictionary = inv.key_items[i]
			slot_box(Rect2(rr.position, Vector2(64, 64)), str(k.id), int(k.get("count", 1)), "", "key", i, int(sel.get("key", -1)) == i)
			text(rr.position + Vector2(80, 28), ContentDB.item_name(str(k.id)), 21, UiKit.PAPER)
			text(rr.position + Vector2(80, 54), fit(str(ContentDB.item(str(k.id)).get("desc", "")), 16, rr.size.x - 96), 16, UiKit.MIST)
			region(rr, "key", i)
		)
		if inv.key_items.is_empty(): text(r.position + Vector2(0, 80), Tx.t("ui.inventory.no_key_items"), 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	_draw_detail(Rect2(content.end.x - 290, content.position.y, 290, content.size.y))

func selected_item():
	var inv: InventoryState = c().inventory
	if sel.has("bag"):
		var i := int(sel.bag)
		return inv.bag[i] if i >= 0 and i < inv.bag.size() else null
	if sel.has("slot"): return inv.equipped.get(str(sel.slot))
	if sel.has("key"):
		var k := int(sel.key)
		return inv.key_items[k] if k >= 0 and k < inv.key_items.size() else null
	return null

func _draw_detail(r: Rect2) -> void:
	panel(r)
	var s = selected_item()
	if s == null:
		para(Rect2(r.position + Vector2(18, 20), r.size - Vector2(36, 40)), Tx.t("ui.inventory.tap_an_item_to_see"), 18, UiKit.MIST)
		return
	var ch = c()
	var id := str(s.id)
	var def := ContentDB.item(id)
	var q := str(s.get("quality", ""))
	var name_col := UiKit.quality_color(q) if q != "" else UiKit.grade_color(str(def.get("grade", "plain")))
	var y := r.position.y + 16
	slot_box(Rect2(r.position.x + 16, y, 64, 64), id, int(s.get("count", 1)), q)
	pill_marks(Rect2(r.position.x + 16, y, 64, 64), int(s.get("marks", 0)))
	para(Rect2(r.position.x + 92, y - 4, r.size.x - 104, 60), ContentDB.item_name(id) + (" +%d" % int(s.enhance) if int(s.get("enhance", 0)) > 0 else ""), 20, name_col, 2)
	y += 78
	var sub := "%s · %s" % [str(def.get("grade", "plain")).capitalize(), str(def.get("slot", def.get("type", ""))).replace("_", " ").capitalize()]
	if q != "": sub = q.capitalize() + " · " + sub
	text(Vector2(r.position.x + 16, y), sub, 16, UiKit.MIST)
	y += 10
	y += para(Rect2(r.position.x + 16, y, r.size.x - 32, 120), str(def.get("desc", "")), 17, UiKit.PAPER, 5)
	if def.has("slot"):
		for m in StatRules.instance_modifiers(str(def.slot), s, ch.cultivator.energy_type):
			if y > r.end.y - 150: break
			var v := float(m.value)
			var shown := ("+%d%%" % int(round(v * 100))) if str(m.op) != "flat" else ("+%s" % UiKit.fmt(v))
			text(Vector2(r.position.x + 16, y + 20), "%s %s" % [shown, str(m.stat).replace("_", " ")], 16, UiKit.BRIGHT_JADE)
			y += 22
		for a in s.get("affixes", []):
			if y > r.end.y - 150: break
			text(Vector2(r.position.x + 16, y + 20), "✦ %s" % UiKit.affix_text(a), 16, UiKit.PALE_GOLD)
			y += 22
		# S44 furnace: what it does for a batch, and how whole it is.
		if def.has("furnace"):
			var fs: Dictionary = def.furnace
			var band := float(fs.get("band", 0.0)) + float(Game.crafting.upkeep("furnace_band_per_level", 0.01)) * int(s.get("enhance", 0))
			for ln in [Tx.t("ui.crafts.furnace_stats") % [int(fs.get("batch", 1)), int(round(band * 100)), int(round(float(fs.get("filter", 0.0)) * 100)),
					int(round(float(fs.get("yield", 0.0)) * 100))],
					Tx.t("ui.inventory.furnace_durability") % int(s.get("durability", 100))]:
				text(Vector2(r.position.x + 16, y + 20), ln, 16, UiKit.BRIGHT_JADE)
				y += 22
			if str(fs.get("element", "")) != "":
				text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.crafts.furnace_element") % str(fs.element).capitalize(), 16, UiKit.PALE_GOLD)
				y += 22
		# S47 natal treasure: its level and growth, or that it is broken.
		if s.get("natal", false):
			var nl := Tx.t("ui.forge.natal_broken") if s.get("broken", false) else Tx.t("ui.inventory.natal_line") % [int(s.get("natal_level", 0)), int(s.get("ilv_eff", s.get("ilv", 1)))]
			text(Vector2(r.position.x + 16, y + 20), nl, 16, UiKit.RED if s.get("broken", false) else UiKit.GOLD)
			y += 22
		# S47: failed enhancements leave pity on the piece; the forge adds it to the next try.
		if float(s.get("pity", 0.0)) > 0.0:
			text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.forge.pity_line") % int(round(float(s.pity) * 100)), 16, UiKit.GOLD)
			y += 22
	if def.get("pill", {}).has("toxicity"):
		var tox_mult := float(ContentDB.config("grades").get("pill", {}).get("toxicity", {}).get(q if q != "" else "common", 1.0))
		text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.inventory.toxicity") % int(round(float(def.pill.toxicity) * tox_mult)), 16, UiKit.RED)
		y += 22
	if not def.get("pill", {}).is_empty() and q != "":
		# S15: quality sets potency; a Pill Halo also shows what dense-Qi seclusion has added.
		text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.inventory.potency") % int(round(InventoryAuthority.pill_potency(s) * 100.0)), 16, name_col)
		y += 22
		if int(s.get("marks", 0)) > 0:
			text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.inventory.pill_marks") % [int(s.marks), int(s.marks) * 2], 16, UiKit.GOLD)
			y += 22
		if q == "pill_halo":
			text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.inventory.halo_charge") % int(round(float(s.get("halo", 0.0)) * 100.0)), 16, UiKit.PALE_GOLD)
			y += 22
	# S44: what lifetime resistance leaves of this pill's effect.
	var fam := ProgressionRules.pill_family(def)
	if fam != "" and not def.get("pill", {}).is_empty():
		var line := Tx.t("ui.inventory.ignores_resistance") if q == "pill_grain" \
			else Tx.t("ui.inventory.resistance") % [Tx.t("ui.cultivation.family_" + fam), int(round(ProgressionRules.resistance_factor(ch.cultivator, fam) * 100.0))]
		text(Vector2(r.position.x + 16, y + 20), line, 16, UiKit.MIST)
		y += 22
	_relic(ch, s, def, r, y)
	y = _treasure_lines(ch, s, def, r, y)
	# Actions.
	var bx := r.position.x + 14
	var bw := (r.size.x - 38) / 2
	var by := r.end.y - 118
	if sel.has("bag"):
		# S47: a Shattered Relic is restored at a forge by an Expert smith.
		if def.has("restores"):
			btn(Rect2(bx, by, r.size.x - 28, 50), Tx.t("ui.inventory.restore_relic"), "restore", null, true)
		# S47 self-detonation: a spare artifact bursts for damage by its grade and is gone (confirmed first).
		if (ContentDB.is_equipment(id) or def.has("treasure")) and not def.has("furnace") and Unlocks.is_unlocked(ch.id, "treasures"):
			btn(Rect2(bx, by - 56, r.size.x - 28, 46), Tx.t("ui.inventory.detonate"), "detonate", null, false, not ch.inventory.locked.has(int(s.get("uid", -1))), Tx.t("ui.forge.locked_item"))
		if def.has("slot"):
			var ok := RequirementRules.passes(def.get("requires", {}), Game.ctx(ch))
			var eq_label := Tx.t("ui.inventory.set_furnace") if def.has("furnace") else Tx.t("ui.inventory.equip")
			btn(Rect2(bx, by, bw, 50), eq_label, "equip", null, true, ok, RequirementRules.first_failure_text(def.get("requires", {}), Game.ctx(ch)))
			# S47 dual loadout: a second weapon waits in the spare slot for the Swap button.
			if str(def.get("slot", "")) == "weapon":
				btn(Rect2(bx + bw + 10, by, bw, 50), Tx.t("ui.inventory.set_spare"), "spare", null, false, Unlocks.is_unlocked(ch.id, "dual_loadout"), Unlocks.locked_text("dual_loadout"))
		elif def.has("use"):
			var verb := Tx.t("ui.inventory.use")
			if def.has("raw"): verb = Tx.t("ui.inventory.absorb") if def.has("core") else Tx.t("ui.inventory.eat_raw")
			elif str(def.get("use_action", "")) == "absorb_flame": verb = Tx.t("ui.inventory.absorb")
			elif str(def.get("use_action", "")) == "bath": verb = Tx.t("ui.inventory.bathe")
			btn(Rect2(bx, by, bw, 50), verb, "use", null, true)
			var q_on = ch.inventory.quick_use == id
			btn(Rect2(bx + bw + 10, by, bw, 50), Tx.t("ui.inventory.quick") if q_on else Tx.t("ui.inventory.quick_use"), "quick", null, false, Unlocks.is_unlocked(ch.id, "quick_use"), Tx.t("ui.inventory.quick_use_is_not_unlocked"))
		elif def.has("treasure"):
			# G2: a treasure art is set in one of the HUD's two Treasure buttons; tapping its own slot clears it.
			for k in 2:
				var here := str(ch.inventory.treasures[k]) == id
				var slot_id := "treasures" if k == 0 else "treasure_slot_2"
				btn(Rect2(bx + k * (bw + 10), by, bw, 50), Tx.t("ui.inventory.in_treasure") % (k + 1) if here else Tx.t("ui.inventory.treasure_n") % (k + 1),
					"treasure", k, here, Unlocks.is_unlocked(ch.id, slot_id), Unlocks.locked_text(slot_id))
		btn(Rect2(bx, by + 58, bw, 46), Tx.t("ui.inventory.unlock") if ch.inventory.locked.has(int(s.get("uid", -1))) else Tx.t("ui.inventory.lock"), "lock")
		btn(Rect2(bx + bw + 10, by + 58, bw, 46), Tx.t("ui.inventory.discard"), "discard", null, false, def.get("type", "") != "key")
	elif sel.has("key") and def.has("flight"):
		var riding := str(ch.inventory.vessel) == id
		btn(Rect2(bx, by + 30, r.size.x - 28, 54), Tx.t("ui.inventory.stop_riding") if riding else Tx.t("ui.inventory.ride_in_flight"), "vessel",
			"" if riding else id, not riding, Unlocks.is_unlocked(ch.id, "flight"), Unlocks.locked_text("flight"))
	elif sel.has("slot"):
		btn(Rect2(bx, by + 30, r.size.x - 28, 54), Tx.t("ui.inventory.unequip"), "unequip", null, false, str(sel.slot) != "gourd", Tx.t("ui.inventory.the_spirit_gourd_holds_your"))
		var spare = ch.inventory.loadout.get("spare")
		if str(sel.slot) == "weapon" and spare != null:
			text(Vector2(bx, by - 8), Tx.t("ui.inventory.spare_weapon") % ContentDB.item_name(str(spare.id)), 17, UiKit.PALE_GOLD)
			btn(Rect2(bx, by - 62 - 8, bw, 46), Tx.t("ui.inventory.swap_now"), "swap", null, true)
			btn(Rect2(bx + bw + 10, by - 62 - 8, bw, 46), Tx.t("ui.inventory.spare_out"), "spare_out")

## G2: what a treasure art, a flight vessel or a talisman does, in numbers.
func _treasure_lines(ch, s: Dictionary, def: Dictionary, r: Rect2, y: float) -> float:
	var x := r.position.x + 16
	var tr := CombatAuthority.treasure_of(str(s.id))
	if not tr.is_empty():
		var soul := int(CombatAuthority.treasure_soul_cost(ch, tr))
		var line := Tx.t("ui.inventory.treasure_charges") % int(s.get("charges", int(tr.charges))) if tr.has("charges") \
			else (Tx.t("ui.inventory.treasure_cost_soul") % [int(tr.get("qi", 0)), soul, int(tr.get("cooldown_s", 0))] if soul > 0
			else Tx.t("ui.inventory.treasure_cost") % [int(tr.get("qi", 0)), int(tr.get("cooldown_s", 0))])
		text(Vector2(x, y + 20), line, 16, UiKit.BRIGHT_JADE if not tr.has("charges") else UiKit.PALE_GOLD)
		y += 22
	if def.has("flight"):
		var fl: Dictionary = def.flight
		text(Vector2(x, y + 20), Tx.t("ui.inventory.vessel_stats") % int(round((1.0 - float(fl.get("qi_mult", 1.0))) * 100.0)), 16, UiKit.BRIGHT_JADE)
		y += 22
		if str(ch.inventory.vessel) == str(s.id):
			text(Vector2(x, y + 20), Tx.t("ui.inventory.vessel_ridden"), 16, UiKit.PALE_GOLD)
			y += 22
	return y

## S14: a sealed relic offers Bind (a channel a hit breaks); a bound one with a dormant spirit offers the contest.
func _relic(ch, s: Dictionary, def: Dictionary, r: Rect2, y: float) -> void:
	if not def.get("relic", false): return
	var target := {"slot": str(sel.slot)} if sel.has("slot") else {"index": int(sel.get("bag", -1))}
	var bx := r.position.x + 14
	var bw := r.size.x - 28
	var by := r.end.y - 176
	var prog: float = Game.inventory.binding_progress(ch.id)
	if s.get("sealed", false):
		text(Vector2(bx, y + 22), Tx.t("ui.inventory.sealed_bind_it_to_wake"), 16, UiKit.RED)
		if prog >= 0.0:
			bar(Rect2(bx, by, bw, 34), prog, UiKit.JADE, Tx.t("ui.inventory.binding"))
		else:
			var secs := float(ContentDB.stat_const("binding", {}).get("seconds", {}).get(str(def.get("grade", "common")), 10))
			btn(Rect2(bx, by - 6, bw, 46), Tx.t("ui.inventory.bind_s") % int(secs), "bind", target, true, Unlocks.is_unlocked(ch.id, "binding"), Unlocks.locked_text("binding"))
	elif str(s.get("spirit", "")) == "dormant":
		text(Vector2(bx, y + 22), Tx.t("ui.inventory.a_spirit_sleeps_in_it"), 16, UiKit.SOUL)
		var chance: float = Game.inventory.spirit_chance(ch, str(s.id))
		btn(Rect2(bx, by - 6, bw, 46), Tx.t("ui.inventory.subdue_the_spirit") % int(round(chance * 100.0)), "subdue", target, false)
	elif str(s.get("spirit", "")) == "awake":
		text(Vector2(bx, y + 22), Tx.t("ui.inventory.spirit_awake") % str(def.get("unique", "")), 16, UiKit.PALE_GOLD)

func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"bind":
			var br := submit(({"type": "bind_item"} as Dictionary).merged(data))
			if br.get("ok", false): flash(Tx.t("ui.inventory.binding_hold_still"))
		"subdue":
			var sr := submit(({"type": "subdue_spirit"} as Dictionary).merged(data))
			if sr.get("ok", false): flash(Tx.t("ui.inventory.the_spirit_wakes_and_answers") if sr.get("awake", false) else Tx.t("ui.inventory.the_spirit_throws_you_off"))
		"bag":
			sel = {"bag": int(data)}
			var s = ch.inventory.bag[int(data)]
			if s != null: ch.inventory.new_items.erase(str(s.id))
		"slot": sel = {"slot": str(data)}
		"key": sel = {"key": int(data)}
		"sort": submit({"type": "sort_bag", "by": sort_by})
		"equip":
			if submit({"type": "equip", "index": int(sel.bag)}).get("ok", false): sel = {}
		"unequip":
			if submit({"type": "unequip", "slot": str(sel.slot)}).get("ok", false): sel = {}
		"use":
			var r := submit({"type": "use_item", "index": int(sel.bag)})
			if not r.get("ok", false) and r.get("reason", "") == "confirm":
				ask(str(r.get("text", Tx.t("ui.inventory.use_it_anyway"))), "use_confirm", int(sel.bag))
		"use_confirm": submit({"type": "use_item", "index": int(data), "confirm": true})
		"spare":
			if submit({"type": "set_spare_weapon", "index": int(sel.bag)}).get("ok", false):
				flash(Tx.t("ui.inventory.spare_set"))
				sel = {}
		"spare_out": submit({"type": "set_spare_weapon", "index": -1})
		"restore":
			var rr := submit({"type": "restore_relic", "index": int(sel.bag)})
			if rr.get("ok", false): sel = {}
			elif str(rr.get("text", "")) != "": flash(str(rr.text))
		"swap": submit({"type": "swap_loadout"})
		"detonate":
			var dr := submit({"type": "self_detonate", "index": int(sel.bag)})
			if not dr.get("ok", false) and dr.get("reason", "") == "confirm": ask(str(dr.get("text", "")), "detonate_yes", int(sel.bag), true)
			elif not dr.get("ok", false) and str(dr.get("text", "")) != "": flash(str(dr.text))
		"detonate_yes":
			if submit({"type": "self_detonate", "index": int(data), "confirm": true}).get("ok", false): sel = {}
		"quick":
			var s = selected_item()
			if s != null: submit({"type": "set_quick_use", "item": "" if ch.inventory.quick_use == str(s.id) else str(s.id)})
		"lock": submit({"type": "lock_item", "index": int(sel.bag)})
		"treasure":
			var st = selected_item()
			if st != null:
				var k := int(data)
				submit({"type": "set_treasure", "slot": k, "item": "" if str(ch.inventory.treasures[k]) == str(st.id) else str(st.id)})
		"vessel": submit({"type": "choose_vessel", "item": str(data)})
		"discard":
			var s2 = selected_item()
			if s2 != null: ask(Tx.t("ui.inventory.discard_2") % [ContentDB.item_name(str(s2.id)), int(s2.get("count", 1))], "discard_yes", int(sel.bag), true)
		"discard_yes":
			var s3 = ch.inventory.bag[int(data)]
			if s3 != null and submit({"type": "discard", "index": int(data), "count": int(s3.get("count", 1))}).get("ok", false): sel = {}
		"_tab": sel = {}
