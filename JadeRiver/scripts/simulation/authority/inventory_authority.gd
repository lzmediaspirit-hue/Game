class_name InventoryAuthority
extends Authority
## S14 · One authority for every add and remove: bag slots, equipped slots,
## quick-use, item instances. Buying/selling (Economy) and storage (Account) call
## the apply_* commands here.

const COOLDOWN_GROUPS := {"restoration": 15.0, "healing": 15.0, "buff": 30.0, "utility": 5.0}

func intents() -> Array:
	return ["move_item", "equip", "unequip", "use_item", "use_quick", "set_quick_use", "lock_item", "discard", "split_stack", "sort_bag"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"equip": return equip(c, int(intent.get("index", -1)))
		"unequip": return unequip(c, str(intent.get("slot", "")))
		"use_item": return use_item(c, int(intent.get("index", -1)), bool(intent.get("confirm", false)))
		"use_quick":
			if c.inventory.quick_use == "": return fail("no_quick_use")
			var idx = c.inventory.first_index(c.inventory.quick_use)
			if idx < 0: return fail("none_left", {"item": c.inventory.quick_use})
			return use_item(c, idx, true)
		"set_quick_use":
			var item := str(intent.get("item", ""))
			if item != "" and not ContentDB.item(item).has("use"): return fail("not_usable")
			c.inventory.quick_use = item
			emit("quick_use_changed", {"actor": c.id, "item": item})
			return ok()
		"lock_item":
			var i := int(intent.get("index", -1))
			if i < 0 or i >= c.inventory.bag.size() or c.inventory.bag[i] == null: return fail("empty")
			var inst: Dictionary = c.inventory.bag[i]
			if not inst.has("uid"):
				inst.uid = c.inventory.next_uid
				c.inventory.next_uid += 1
			if c.inventory.locked.has(int(inst.uid)): c.inventory.locked.erase(int(inst.uid))
			else: c.inventory.locked[int(inst.uid)] = true
			emit("item_locked", {"actor": c.id, "index": i})
			return ok()
		"move_item": return move_item(c, int(intent.get("from", -1)), int(intent.get("to", -1)))
		"discard": return discard(c, int(intent.get("index", -1)), int(intent.get("count", 1)))
		"split_stack": return split(c, int(intent.get("index", -1)), int(intent.get("count", 1)))
		"sort_bag": return sort_bag(c, str(intent.get("by", "type")))
	return fail("unknown_intent")

# ------------------------------------------------------------------ apply commands
func apply_add(actor_id: String, item_id: String, count: int, source: String, fields: Dictionary = {}, overflow := true) -> int:
	var c = game.character(actor_id)
	var def := ContentDB.item(item_id)
	if c == null or def.is_empty() or count <= 0: return 0
	if def.get("type") == "currency_item":
		var per = {"spirit_stone_low": 1, "spirit_stone_mid": 10, "spirit_stone_high": 100}.get(item_id, 1)
		game.economy.apply_currency("spirit_stone", per * count, source)
		return count
	if def.get("type") == "key" or def.get("quest_item", false):
		for k in c.inventory.key_items:
			if k.id == item_id:
				k.count = int(k.count) + count
				emit("item_added", {"actor": c.id, "item": item_id, "count": count, "source": source})
				return count
		c.inventory.key_items.append({"id": item_id, "count": count})
		emit("item_added", {"actor": c.id, "item": item_id, "count": count, "source": source})
		return count
	if ContentDB.is_equipment(item_id):
		var added := 0
		for i in count:
			var inst := LootRules.make_instance(item_id, int(fields.get("ilv", def.get("ilv", 1))), str(fields.get("quality", "common")), null, c.inventory.next_uid)
			c.inventory.next_uid += 1
			if fields.has("appearance"): inst.appearance = fields.appearance
			if apply_add_instance(actor_id, inst, source, overflow) > 0: added += 1
		return added
	var stack := int(def.get("stack", 99))
	var left := count
	var bag: Array = c.inventory.bag
	for s in bag:
		if left <= 0: break
		if s != null and s.id == item_id and int(s.count) < stack:
			var n := mini(left, stack - int(s.count))
			s.count = int(s.count) + n
			left -= n
	for i in bag.size():
		if left <= 0: break
		if bag[i] == null:
			var n := mini(left, stack)
			bag[i] = {"id": item_id, "count": n}
			left -= n
	var added_n := count - left
	if added_n > 0:
		c.inventory.new_items[item_id] = true
		emit("item_added", {"actor": c.id, "item": item_id, "count": added_n, "source": source})
	if left > 0:
		emit("bag_full", {"actor": c.id, "items": [{"item": item_id, "count": left}]})
		if overflow:
			game.mail.apply_overflow(c.id, [{"item": item_id, "count": left}])
			return count
	return added_n

func apply_add_instance(actor_id: String, inst: Dictionary, source: String, overflow := true) -> int:
	var c = game.character(actor_id)
	if c == null: return 0
	var bag: Array = c.inventory.bag
	for i in bag.size():
		if bag[i] == null:
			var copy := inst.duplicate(true)
			if not copy.has("uid"):
				copy.uid = c.inventory.next_uid
				c.inventory.next_uid += 1
			bag[i] = copy
			c.inventory.new_items[str(inst.id)] = true
			emit("item_added", {"actor": c.id, "item": str(inst.id), "count": 1, "source": source, "quality": str(inst.get("quality", "common"))})
			return 1
	emit("bag_full", {"actor": c.id, "items": [{"item": inst.id, "count": 1}]})
	if overflow:
		game.mail.apply_overflow(c.id, [{"item": inst.id, "count": 1, "instance": inst}])
		return 1
	return 0

func apply_add_equipment(actor_id: String, item_id: String, ilv: int, quality: String, source: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var def := ContentDB.item(item_id)
	var inst := LootRules.make_instance(item_id, ilv if ilv > 0 else int(def.get("ilv", 1)), quality, Rng.stream(actor_id, "affix"), c.inventory.next_uid)
	c.inventory.next_uid += 1
	apply_add_instance(actor_id, inst, source)

func apply_remove(actor_id: String, item_id: String, count: int, source: String) -> int:
	var c = game.character(actor_id)
	if c == null or count <= 0: return 0
	var left := count
	for k in c.inventory.key_items.duplicate():
		if left <= 0: break
		if k.id == item_id:
			var n := mini(left, int(k.count))
			k.count = int(k.count) - n
			left -= n
			if int(k.count) <= 0: c.inventory.key_items.erase(k)
	for i in range(c.inventory.bag.size() - 1, -1, -1):
		if left <= 0: break
		var s = c.inventory.bag[i]
		if s == null or s.id != item_id: continue
		var n2 := mini(left, int(s.get("count", 1)))
		s.count = int(s.get("count", 1)) - n2
		left -= n2
		if int(s.count) <= 0: c.inventory.bag[i] = null
	var removed := count - left
	if removed > 0: emit("item_removed", {"actor": c.id, "item": item_id, "count": removed, "source": source})
	return removed

func apply_remove_index(actor_id: String, index: int, count: int, source: String) -> Dictionary:
	var c = game.character(actor_id)
	if c == null or index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return {}
	var s: Dictionary = c.inventory.bag[index]
	var n := mini(count, int(s.get("count", 1)))
	var removed := s.duplicate(true)
	removed.count = n
	s.count = int(s.get("count", 1)) - n
	if int(s.count) <= 0: c.inventory.bag[index] = null
	emit("item_removed", {"actor": c.id, "item": str(s.id), "count": n, "source": source})
	return removed

# ------------------------------------------------------------------ equipment
func wear_check(c, def: Dictionary) -> String:
	var ctx: Dictionary = game.ctx(c)
	if def.has("requires") and not RequirementRules.passes(def.requires, ctx):
		return RequirementRules.first_failure_text(def.requires, ctx)
	var grade := str(def.get("grade", "plain"))
	var need := int(ContentDB.config("grades").get("wear_level", {}).get(grade, 0))
	if ProgressionRules.level(c) < need: return "Requires Level %d" % need
	for attr in def.get("attribute_req", {}):
		if c.stats.value(attr) < float(def.attribute_req[attr]): return "Requires %s %d" % [attr.capitalize(), int(def.attribute_req[attr])]
	var slot := str(def.get("slot", ""))
	var slot_unlock := {"weapon": "weapon_slot", "cape": "cape_slot", "talisman": "soul_talisman_slot"}
	if slot_unlock.has(slot) and not Unlocks.is_unlocked(c.id, slot_unlock[slot]): return Unlocks.locked_text(slot_unlock[slot])
	return ""

func equip(c, index: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var inst: Dictionary = c.inventory.bag[index]
	var def := ContentDB.item(str(inst.id))
	if def.get("type") != "equipment": return fail("not_equipment")
	var why := wear_check(c, def)
	if why != "": return fail("cannot_wear", {"text": why})
	var slot := str(def.slot)
	var old = c.inventory.equipped.get(slot)
	c.inventory.equipped[slot] = inst
	c.inventory.bag[index] = old
	if slot == "gourd": c.inventory.resize(c.inventory.capacity())
	emit("equipment_changed", {"actor": c.id, "slot": slot, "old": old.id if old else "", "new": inst.id})
	return ok()

func unequip(c, slot: String) -> Dictionary:
	var inst = c.inventory.equipped.get(slot)
	if inst == null: return fail("empty")
	if slot == "gourd": return fail("gourd_required", {"text": "You always carry a Spirit Gourd."})
	var free := -1
	for i in c.inventory.bag.size():
		if c.inventory.bag[i] == null:
			free = i
			break
	if free < 0: return fail("bag_full")
	c.inventory.bag[free] = inst
	c.inventory.equipped[slot] = null
	emit("equipment_changed", {"actor": c.id, "slot": slot, "old": inst.id, "new": ""})
	return ok()

## Avatar outfit from the creator look plus equipped appearances (S14).
static func outfit_for(c) -> Dictionary:
	var a: Dictionary = c.appearance
	var o := {"name": c.name, "body": str(a.get("body", "light")), "hair": str(a.get("hair", "topknot")), "hair_color": int(a.get("hair_color", 0)),
		"shirt": str(a.get("shirt", "cardigan")), "pants": str(a.get("pants", "loose")), "shoes": str(a.get("shoes", "boots")),
		"weapon": "none", "hat": "none", "cape": "none"}
	var map := {"robe": "shirt", "trousers": "pants", "boots": "shoes", "weapon": "weapon", "hat": "hat", "cape": "cape"}
	for slot in map:
		var inst = c.inventory.equipped.get(slot)
		if inst == null: continue
		var look := str(inst.get("appearance", ContentDB.item(inst.id).get("appearance", "none")))
		if ContentDB.parts.get(map[slot], {}).has(look): o[map[slot]] = look
	return o

# ------------------------------------------------------------------ use (S15 limits)
func use_warning(c, def: Dictionary) -> String:
	var p: Dictionary = def.get("pill", {})
	if p.is_empty(): return ""
	var cause := str(p.get("cause", ""))
	if c.cultivator.state == "bottleneck" and cause != "" and def.get("use", []).size() > 0:
		var needed := {}
		for r in game.progression.query_requirements(c):
			if not r.ok: needed[str(r.cause)] = true
		if not needed.is_empty() and not needed.has(cause) and "add_progress" in str(def.use):
			return "This pill will not help your current bottleneck (%s)" % ", ".join(needed.keys()).capitalize()
	var grade_gap := StatRules.grade_index(str(def.get("grade", "plain"))) - StatRules.grade_index(LootRules.grade_for_ilv(maxi(1, ProgressionRules.level(c))))
	if grade_gap >= 2: return "This pill is two grades above your realm: it will injure you"
	if c.cultivator.toxicity + float(p.get("toxicity", 0)) > c.stats.value("toxicity_tolerance"): return "Toxicity above tolerance: the pill will lose effect and hurt your meridians"
	return ""

func use_item(c, index: int, confirm: bool) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var s: Dictionary = c.inventory.bag[index]
	var def := ContentDB.item(str(s.id))
	if not def.has("use"): return fail("not_usable")
	if game.combat.is_wounded(c.id): return fail("wounded")
	var group := str(def.get("pill", def.get("food", {})).get("group", "utility"))
	var cd_key := "item:" + group
	if c.pools.cooldown(cd_key) > 0.0: return fail("cooldown", {"remaining": c.pools.cooldown(cd_key)})
	var warning := use_warning(c, def)
	if warning != "" and not confirm: return fail("confirm", {"text": warning})
	var factor := 1.0
	var p: Dictionary = def.get("pill", {})
	if not p.is_empty():
		var tox := float(p.get("toxicity", 0))
		var last := float(c.cultivator.pill_memory.get(str(s.id), -9999.0))
		if game.sim_time - last < float(ContentDB.stat_const("toxicity.repeat_window_s", 300)): factor *= float(ContentDB.stat_const("toxicity.repeat_factor", 0.5))
		c.cultivator.pill_memory[str(s.id)] = game.sim_time
		var grade_gap := StatRules.grade_index(str(def.get("grade", "plain"))) - StatRules.grade_index(LootRules.grade_for_ilv(maxi(1, ProgressionRules.level(c))))
		if grade_gap >= 2:
			apply_remove_index(c.id, index, 1, "use")
			game.progression.apply_injury(c.id, "meridian", 2)
			emit("pill_used", {"actor": c.id, "item": s.id, "result": "injury"})
			return ok({"result": "injury"})
		if c.cultivator.toxicity + tox > c.stats.value("toxicity_tolerance"): factor *= 0.3
		game.progression.apply_toxicity(c.id, tox)
	apply_remove_index(c.id, index, 1, "use")
	c.pools.cooldowns[cd_key] = float(COOLDOWN_GROUPS.get(group, 5.0))
	var effects: Array = []
	for e in def.use:
		var ed: Dictionary = e.duplicate(true)
		for k in ["pct", "amount", "value", "pct_of_need"]:
			if ed.has(k) and factor != 1.0: ed[k] = float(ed[k]) * factor
		effects.append(ed)
	game.apply_effects(c.id, effects, "item:" + str(s.id))
	emit("item_used", {"actor": c.id, "item": s.id, "factor": factor})
	if not p.is_empty(): emit("pill_used", {"actor": c.id, "item": s.id, "factor": factor})
	return ok({"factor": factor})

func move_item(c, from: int, to: int) -> Dictionary:
	var bag: Array = c.inventory.bag
	if from < 0 or to < 0 or from >= bag.size() or to >= bag.size() or bag[from] == null: return fail("bad_index")
	var a = bag[from]
	var b = bag[to]
	if b != null and b.id == a.id and not ContentDB.is_equipment(str(a.id)):
		var stack := int(ContentDB.item(str(a.id)).get("stack", 99))
		var n := mini(int(a.count), stack - int(b.count))
		b.count = int(b.count) + n
		a.count = int(a.count) - n
		if int(a.count) <= 0: bag[from] = null
	else:
		bag[from] = b
		bag[to] = a
	emit("bag_changed", {"actor": c.id})
	return ok()

func discard(c, index: int, count: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var s: Dictionary = c.inventory.bag[index]
	if c.inventory.locked.has(int(s.get("uid", -1))): return fail("locked")
	if ContentDB.item(str(s.id)).get("type") in ["key", "treasure"]: return fail("cannot_discard")
	apply_remove_index(c.id, index, count, "discard")
	return ok()

func split(c, index: int, count: int) -> Dictionary:
	var bag: Array = c.inventory.bag
	if index < 0 or index >= bag.size() or bag[index] == null: return fail("empty")
	var s: Dictionary = bag[index]
	if int(s.get("count", 1)) <= count or count <= 0: return fail("bad_count")
	for i in bag.size():
		if bag[i] == null:
			bag[i] = {"id": s.id, "count": count}
			s.count = int(s.count) - count
			emit("bag_changed", {"actor": c.id})
			return ok()
	return fail("bag_full")

func sort_bag(c, by: String) -> Dictionary:
	var items: Array = c.inventory.bag.filter(func(x): return x != null)
	var order := ["equipment", "pill", "food", "talisman", "herb", "ore", "beast_part", "core", "fish", "material", "scroll", "tool", "taming", "jade", "hollow", "other", "egg"]
	items.sort_custom(func(a, b):
		var da := ContentDB.item(str(a.id))
		var db := ContentDB.item(str(b.id))
		if by == "grade" and StatRules.grade_index(str(da.get("grade", "plain"))) != StatRules.grade_index(str(db.get("grade", "plain"))):
			return StatRules.grade_index(str(da.get("grade", "plain"))) > StatRules.grade_index(str(db.get("grade", "plain")))
		var ta := order.find(str(da.get("type", "other")))
		var tb := order.find(str(db.get("type", "other")))
		if ta != tb: return ta < tb
		return str(a.id) < str(b.id))
	for i in c.inventory.bag.size(): c.inventory.bag[i] = items[i] if i < items.size() else null
	emit("bag_changed", {"actor": c.id})
	return ok()
