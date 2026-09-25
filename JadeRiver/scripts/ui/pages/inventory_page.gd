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
			text(Vector2(r.position.x + 16, y + 20), "✦ %s" % str(a.get("stat", "")).replace("_", " "), 16, UiKit.PALE_GOLD)
			y += 22
	if def.get("pill", {}).has("toxicity"):
		var tox_mult := float(ContentDB.config("grades").get("pill", {}).get("toxicity", {}).get(q if q != "" else "common", 1.0))
		text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.inventory.toxicity") % int(round(float(def.pill.toxicity) * tox_mult)), 16, UiKit.RED)
		y += 22
	if not def.get("pill", {}).is_empty() and q != "":
		# S15: quality sets potency; a Pill Halo also shows what dense-Qi seclusion has added.
		text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.inventory.potency") % int(round(InventoryAuthority.pill_potency(s) * 100.0)), 16, name_col)
		y += 22
		if q == "pill_halo":
			text(Vector2(r.position.x + 16, y + 20), Tx.t("ui.inventory.halo_charge") % int(round(float(s.get("halo", 0.0)) * 100.0)), 16, UiKit.PALE_GOLD)
			y += 22
	_relic(ch, s, def, r, y)
	# Actions.
	var bx := r.position.x + 14
	var bw := (r.size.x - 38) / 2
	var by := r.end.y - 118
	if sel.has("bag"):
		if def.has("slot"):
			var ok := RequirementRules.passes(def.get("requires", {}), Game.ctx(ch))
			btn(Rect2(bx, by, bw, 50), Tx.t("ui.inventory.equip"), "equip", null, true, ok, RequirementRules.first_failure_text(def.get("requires", {}), Game.ctx(ch)))
		elif def.has("use"):
			btn(Rect2(bx, by, bw, 50), Tx.t("ui.inventory.use"), "use", null, true)
			var q_on = ch.inventory.quick_use == id
			btn(Rect2(bx + bw + 10, by, bw, 50), Tx.t("ui.inventory.quick") if q_on else Tx.t("ui.inventory.quick_use"), "quick", null, false, Unlocks.is_unlocked(ch.id, "quick_use"), Tx.t("ui.inventory.quick_use_is_not_unlocked"))
		btn(Rect2(bx, by + 58, bw, 46), Tx.t("ui.inventory.unlock") if ch.inventory.locked.has(int(s.get("uid", -1))) else Tx.t("ui.inventory.lock"), "lock")
		btn(Rect2(bx + bw + 10, by + 58, bw, 46), Tx.t("ui.inventory.discard"), "discard", null, false, def.get("type", "") != "key")
	elif sel.has("slot"):
		btn(Rect2(bx, by + 30, r.size.x - 28, 54), Tx.t("ui.inventory.unequip"), "unequip", null, false, str(sel.slot) != "gourd", Tx.t("ui.inventory.the_spirit_gourd_holds_your"))

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
		"quick":
			var s = selected_item()
			if s != null: submit({"type": "set_quick_use", "item": "" if ch.inventory.quick_use == str(s.id) else str(s.id)})
		"lock": submit({"type": "lock_item", "index": int(sel.bag)})
		"discard":
			var s2 = selected_item()
			if s2 != null: ask(Tx.t("ui.inventory.discard_2") % [ContentDB.item_name(str(s2.id)), int(s2.get("count", 1))], "discard_yes", int(sel.bag), true)
		"discard_yes":
			var s3 = ch.inventory.bag[int(data)]
			if s3 != null and submit({"type": "discard", "index": int(data), "count": int(s3.get("count", 1))}).get("ok", false): sel = {}
		"_tab": sel = {}
