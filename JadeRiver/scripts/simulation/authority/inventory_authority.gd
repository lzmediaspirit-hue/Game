class_name InventoryAuthority
extends Authority
## S14 · One authority for every add and remove: bag slots, equipped slots,
## quick-use, item instances. Buying/selling (Economy) and storage (Account) call
## the apply_* commands here.

const COOLDOWN_GROUPS := {"restoration": 15.0, "healing": 15.0, "buff": 30.0, "utility": 5.0, "throw": 1.2}

func intents() -> Array:
	return ["move_item", "equip", "unequip", "use_item", "use_quick", "set_quick_use", "lock_item", "discard", "split_stack", "sort_bag",
		"bind_item", "subdue_spirit", "set_treasure", "choose_vessel", "swap_loadout", "set_spare_weapon"]

var binding: Dictionary = {}   # actor -> {uid, left, total}: a relic being bound (S14)
var spirit_cd: Dictionary = {} # actor -> seconds before another soul contest

func subscribe() -> void:
	GameEvents.subscribe("hit_landed", _on_hit, 40)

## A blow breaks the binding channel.
func _on_hit(p: Dictionary) -> void:
	var who := str(p.get("target", ""))
	if binding.has(who):
		binding.erase(who)
		emit("binding_interrupted", {"actor": who})

func tick(delta: float) -> void:
	for actor in spirit_cd.keys():
		spirit_cd[actor] = float(spirit_cd[actor]) - delta
		if float(spirit_cd[actor]) <= 0.0: spirit_cd.erase(actor)
	for actor in binding.keys():
		var b: Dictionary = binding[actor]
		b.left = float(b.left) - delta
		if float(b.left) > 0.0: continue
		binding.erase(actor)
		var c = game.character(actor)
		var found := _instance_by_uid(c, int(b.uid)) if c else {}
		if found.is_empty(): continue
		found.inst.erase("sealed")
		found.inst.bound = true
		emit("item_bound", {"actor": actor, "item": str(found.inst.id)})
		emit("system_used", {"actor": actor, "system": "bind"})
		if found.slot != "": emit("equipment_changed", {"actor": actor, "slot": found.slot, "old": found.inst.id, "new": found.inst.id})

## {inst, slot} for an equipped slot or a bag index.
func _instance(c, slot: String, index: int) -> Dictionary:
	if slot != "":
		var e = c.inventory.equipped.get(slot)
		return {"inst": e, "slot": slot} if e is Dictionary else {}
	if index >= 0 and index < c.inventory.bag.size() and c.inventory.bag[index] is Dictionary:
		return {"inst": c.inventory.bag[index], "slot": ""}
	return {}

func _instance_by_uid(c, uid: int) -> Dictionary:
	for slot in c.inventory.equipped:
		var e = c.inventory.equipped[slot]
		if e is Dictionary and int(e.get("uid", -1)) == uid: return {"inst": e, "slot": str(slot)}
	for it in c.inventory.bag:
		if it is Dictionary and int(it.get("uid", -1)) == uid: return {"inst": it, "slot": ""}
	return {}

## S14 binding: a timed channel by grade; a hit breaks it.
func bind_item(c, slot: String, index: int) -> Dictionary:
	var cfg: Dictionary = ContentDB.stat_const("binding", {})
	if not Unlocks.is_unlocked(c.id, str(cfg.get("unlock", "binding"))): return fail("locked", {"text": Unlocks.locked_text("binding")})
	var found := _instance(c, slot, index)
	if found.is_empty() or not found.inst.get("sealed", false): return fail("not_sealed")
	if binding.has(c.id): return fail("busy")
	var grade := str(ContentDB.item(str(found.inst.id)).get("grade", "common"))
	var secs := float(cfg.get("seconds", {}).get(grade, 10))
	binding[c.id] = {"uid": int(found.inst.get("uid", -1)), "left": secs, "total": secs}
	emit("binding_started", {"actor": c.id, "item": str(found.inst.id), "seconds": secs})
	return ok({"seconds": secs})

func binding_progress(actor_id: String) -> float:
	var b: Dictionary = binding.get(actor_id, {})
	return 1.0 - float(b.left) / maxf(0.01, float(b.total)) if not b.is_empty() else -1.0

## Waking an Artifact Spirit: the owner's Spirit against the spirit's strength. A failed contest bruises the soul.
func subdue_spirit(c, slot: String, index: int) -> Dictionary:
	var cfg: Dictionary = ContentDB.stat_const("binding", {})
	var found := _instance(c, slot, index)
	if found.is_empty() or found.inst.get("sealed", false) or str(found.inst.get("spirit", "")) != "dormant": return fail("no_spirit")
	if spirit_cd.has(c.id): return fail("cooldown", {"text": Tx.t("sim.inventory.the_spirit_is_still_wary")})
	var chance := spirit_chance(c, str(found.inst.id))
	spirit_cd[c.id] = float(cfg.get("spirit_cooldown_s", 60))
	if Rng.stream(c.id, "spirit").randf() < chance:
		found.inst.spirit = "awake"
		emit("artifact_spirit_awakened", {"actor": c.id, "item": str(found.inst.id)})
		if found.slot != "": emit("equipment_changed", {"actor": c.id, "slot": found.slot, "old": found.inst.id, "new": found.inst.id})
		return ok({"awake": true, "chance": chance})
	game.progression.apply_injury(c.id, "soul", int(cfg.get("soul_injury", 1)))
	emit("artifact_spirit_resisted", {"actor": c.id, "item": str(found.inst.id)})
	return ok({"awake": false, "chance": chance})

func spirit_chance(c, item_id: String) -> float:
	var cfg: Dictionary = ContentDB.stat_const("binding", {})
	var strength := float(ContentDB.item(item_id).get("spirit", {}).get("strength", 30))
	var mine: float = c.stats.value("spirit")
	var lim: Array = cfg.get("spirit_chance", [0.1, 0.9])
	return clampf(mine / maxf(1.0, mine + strength), float(lim[0]), float(lim[1]))

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"equip": return equip(c, int(intent.get("index", -1)))
		"bind_item": return bind_item(c, str(intent.get("slot", "")), int(intent.get("index", -1)))
		"subdue_spirit": return subdue_spirit(c, str(intent.get("slot", "")), int(intent.get("index", -1)))
		"unequip": return unequip(c, str(intent.get("slot", "")))
		"use_item": return use_item(c, int(intent.get("index", -1)), bool(intent.get("confirm", false)))
		"set_treasure": return set_treasure(c, str(intent.get("item", "")), int(intent.get("slot", 0)))
		"choose_vessel": return choose_vessel(c, str(intent.get("item", "")))
		"swap_loadout": return swap_loadout(c)
		"set_spare_weapon": return set_spare_weapon(c, int(intent.get("index", -1)))
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
	if def.get("type") in ["key", "tool", "vessel"] or def.get("quest_item", false):
		for k in c.inventory.key_items:
			if k.id == item_id:
				# A second copy of a tool or a flight vessel is pointless: keep one.
				if not def.get("type") in ["tool", "vessel"]: k.count = int(k.count) + count
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
	var entry := pill_entry(item_id, fields)
	var key := stack_key(entry)
	for s in bag:
		if left <= 0: break
		if s != null and not s.has("uid") and stack_key(s) == key and int(s.count) < stack:
			var n := mini(left, stack - int(s.count))
			s.count = int(s.count) + n
			left -= n
	for i in bag.size():
		if left <= 0: break
		if bag[i] == null:
			var n := mini(left, stack)
			var fresh: Dictionary = entry.duplicate()
			fresh.count = n
			bag[i] = fresh
			left -= n
	var added_n := count - left
	if added_n > 0:
		c.inventory.new_items[item_id] = true
		emit("item_added", {"actor": c.id, "item": item_id, "count": added_n, "source": source})
		# The first treasure art carried goes straight into Treasure 1 (G2), so the button works when it appears.
		if def.has("treasure") and str(c.inventory.treasures[0]) == "" and str(c.inventory.treasures[1]) != item_id:
			c.inventory.treasures[0] = item_id
			emit("treasure_set", {"actor": c.id, "slot": 0, "item": item_id})
	if left > 0:
		var over := {"item": item_id, "count": left}
		for f in ["quality", "halo", "marks"]:
			if entry.has(f): over[f] = entry[f]
		emit("bag_full", {"actor": c.id, "items": [over]})
		if overflow:
			apply_overflow(c.id, [over])
			return count
	return added_n

## A new stack entry. Pills carry their refining quality and Halo charge (S15);
## a Common pill is a plain {id, count} so older saves read unchanged.
static func pill_entry(item_id: String, fields: Dictionary) -> Dictionary:
	var e := {"id": item_id, "count": 0}
	if ContentDB.item(item_id).get("pill", {}).is_empty(): return e
	var q := str(fields.get("quality", "common"))
	if q != "common": e.quality = q
	if float(fields.get("halo", 0.0)) > 0.0: e.halo = float(fields.halo)
	if int(fields.get("marks", 0)) > 0: e.marks = int(fields.marks)   # gold lines from the furnace (G1)
	return e

## Stacks merge only with the same item, quality and Halo charge.
static func stack_key(s: Dictionary) -> String:
	return "%s|%s|%.3f|%d" % [str(s.get("id", "")), str(s.get("quality", "common")), float(s.get("halo", 0.0)), int(s.get("marks", 0))]

## Potency of one pill from its quality (Flawed 50% to Pill Soul 220%) plus any Halo charge.
static func pill_potency(s: Dictionary) -> float:
	var q := str(s.get("quality", "common"))
	var marks := float(ContentDB.config("grades").get("pill", {}).get("marks", {}).get("per_line", 0.02)) * int(s.get("marks", 0))
	return float(ContentDB.config("grades").get("pill_qualities", {}).get(q, 1.0)) * (1.0 + float(s.get("halo", 0.0))) * (1.0 + marks)

## A Pill Halo stack in a storage chest grows 1% a day while the chest's room holds Qi density 2 or more,
## up to +20% (S44). The growth is worked out from the deposit time when the stack is looked at or taken out.
static func halo_now(s: Dictionary) -> float:
	var halo := float(s.get("halo", 0.0))
	if str(s.get("quality", "")) != "pill_halo" or not s.has("stored_utc"): return halo
	var h: Dictionary = ContentDB.config("grades").get("pill", {}).get("halo", {})
	if float(s.get("stored_density", 1.0)) < float(h.get("min_density", 2.0)): return halo
	var days := floorf(maxf(0.0, Clock.now_utc() - float(s.stored_utc)) / 86400.0)
	return minf(float(h.get("cap", 0.2)), halo + days * float(h.get("per_day", 0.01)))

## What does not fit waits in the mail for three days.
func apply_overflow(actor_id: String, items: Array) -> void:
	game.mail.apply_overflow(actor_id, items)
	emit("overflow_mailed", {"actor": actor_id, "items": items})

## Forge enhancement: Crafting pays and rolls; Inventory owns the instance and says so.
## A piece takes a new set of affixes (S47 reroll); worn, it changes the wearer's stats.
func apply_affixes(actor_id: String, inst: Dictionary, affixes: Array, slot: String) -> void:
	inst.affixes = affixes
	if slot != "": emit("equipment_changed", {"actor": actor_id, "slot": slot, "old": inst.id, "new": inst.id})

func apply_enhance(actor_id: String, inst: Dictionary, level: int, slot: String) -> void:
	inst.enhance = level
	if slot != "": emit("equipment_changed", {"actor": actor_id, "slot": slot, "old": inst.id, "new": inst.id})

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
	if ProgressionRules.level(c) < need: return Tx.t("sim.inventory.requires_level") % need
	for attr in def.get("attribute_req", {}):
		if c.stats.value(attr) < float(def.attribute_req[attr]): return Tx.t("sim.inventory.requires") % [attr.capitalize(), int(def.attribute_req[attr])]
	var slot := str(def.get("slot", ""))
	var slot_unlock := {"weapon": "weapons", "cape": "cape_slot", "talisman": "spirit_sense"}
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

# ------------------------------------------------------------------ dual loadout (S47, Heart Tempering 1)
## A second weapon waits in the spare slot; Swap trades it with the one in hand. Each weapon keeps its own technique
## bar (Progression swaps the bars on loadout_swapped).
func swap_loadout(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "dual_loadout"): return fail("locked", {"text": Unlocks.locked_text("dual_loadout")})
	var spare = c.inventory.loadout.get("spare")
	if spare == null: return fail("no_spare", {"text": Tx.t("sim.inventory.no_spare_weapon")})
	if game.combat.is_busy(c.id): return fail("busy")
	var held = c.inventory.equipped.get("weapon")
	c.inventory.equipped["weapon"] = spare
	c.inventory.loadout["spare"] = held
	var active := "b" if str(c.inventory.loadout.get("active", "a")) == "a" else "a"
	c.inventory.loadout["active"] = active
	emit("equipment_changed", {"actor": c.id, "slot": "weapon", "old": held.id if held else "", "new": spare.id})
	emit("loadout_swapped", {"actor": c.id, "active": active, "item": str(spare.id), "weapon": str(spare.id)})
	return ok({"active": active, "weapon": str(spare.id)})

## Put a bag weapon in the spare slot (the one there goes back to the bag); index -1 takes the spare out.
func set_spare_weapon(c, index: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "dual_loadout"): return fail("locked", {"text": Unlocks.locked_text("dual_loadout")})
	var old = c.inventory.loadout.get("spare")
	if index < 0:
		if old == null: return fail("empty")
		var free := -1
		for i in c.inventory.bag.size():
			if c.inventory.bag[i] == null:
				free = i
				break
		if free < 0: return fail("bag_full")
		c.inventory.bag[free] = old
		c.inventory.loadout["spare"] = null
		return ok()
	if index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var inst: Dictionary = c.inventory.bag[index]
	var def := ContentDB.item(str(inst.id))
	if def.get("type") != "equipment" or str(def.get("slot", "")) != "weapon": return fail("not_weapon", {"text": Tx.t("sim.inventory.spare_is_a_weapon")})
	var why := wear_check(c, def)
	if why != "": return fail("cannot_wear", {"text": why})
	c.inventory.loadout["spare"] = inst
	c.inventory.bag[index] = old
	return ok()

func unequip(c, slot: String) -> Dictionary:
	var inst = c.inventory.equipped.get(slot)
	if inst == null: return fail("empty")
	if slot == "gourd": return fail("gourd_required", {"text": Tx.t("sim.inventory.you_always_carry_a_spirit")})
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
		if ContentDB.parts.get(map[slot], {}).has(look):
			o[map[slot]] = look
			var dye := str(inst.get("dye", ContentDB.item(inst.id).get("dye", "")))
			if dye != "" and map[slot] in ["shirt", "pants"]: o[map[slot] + "_dye"] = dye
	return o

# ------------------------------------------------------------------ use (S15 limits)
func use_warning(c, def: Dictionary) -> String:
	var p: Dictionary = def.get("pill", {})
	if p.is_empty() and def.has("raw"): return Tx.t("sim.inventory.eat_raw_warning") % int(def.raw.get("toxicity", 10))
	if p.is_empty(): return ""
	var cause := str(p.get("cause", ""))
	if c.cultivator.state == "bottleneck" and cause != "" and def.get("use", []).size() > 0:
		var needed := {}
		for r in game.progression.query_requirements(c):
			if not r.ok: needed[str(r.cause)] = true
		if not needed.is_empty() and not needed.has(cause) and "add_progress" in str(def.use):
			return Tx.t("sim.inventory.this_pill_will_not_help") % ", ".join(needed.keys()).capitalize()
	var grade_gap := StatRules.grade_index(str(def.get("grade", "plain"))) - StatRules.grade_index(LootRules.grade_for_ilv(maxi(1, ProgressionRules.level(c))))
	if grade_gap >= 2: return Tx.t("sim.inventory.this_pill_is_two_grades")
	if c.cultivator.toxicity + float(p.get("toxicity", 0)) > c.stats.value("toxicity_tolerance"): return Tx.t("sim.inventory.toxicity_above_tolerance_the_pill")
	return ""

func use_item(c, index: int, confirm: bool) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var s: Dictionary = c.inventory.bag[index]
	var def := ContentDB.item(str(s.id))
	if not def.has("use"): return fail("not_usable")
	if game.combat.is_wounded(c.id): return fail("wounded")
	# Items that start a system instead of applying effects; each owner validates before consuming.
	match str(def.get("use_action", "")):
		"appraise": return game.workshop.appraise(c, index)
		"incubate": return game.pets.incubate_egg(c, index)
		"tame": return game.pets.attempt_tame(c, str(s.id), -1.0)
		"absorb_flame": return game.crafting.absorb_flame(c, index)
	# Natural treasures answer once in each great realm (the Mindwell Lotus).
	var great_realm := str(ContentDB.realm(c.cultivator.realm_key).get("realm", ""))
	var once := str(def.get("use_limit", "")) == "realm"
	if once and str(c.cultivator.treasure_uses.get(str(s.id), "")) == great_realm:
		return fail("once_per_realm", {"text": Tx.t("sim.inventory.once_per_realm") % ContentDB.item_name(str(s.id))})
	var group := str(def.get("pill", def.get("food", {})).get("group", "utility"))
	var cd_key := "item:" + group
	if c.pools.cooldown(cd_key) > 0.0: return fail("cooldown", {"remaining": c.pools.cooldown(cd_key)})
	var warning := use_warning(c, def)
	if warning != "" and not confirm: return fail("confirm", {"text": warning})
	var factor := 1.0
	var p: Dictionary = def.get("pill", {})
	var quality := str(s.get("quality", "common"))
	var pill_cfg: Dictionary = ContentDB.config("grades").get("pill", {})
	# Eaten raw (a herb, a beast core): a third of a pill's strength at twice the toxicity (G1).
	if p.is_empty() and def.has("raw"):
		p = {"toxicity": float(def.raw.get("toxicity", 10)), "group": "raw"}   # data already carries the doubled toxicity
		quality = "common"
	# Lifetime resistance (G1): each dose of a family weakens the next; a Pill Grain slips past it.
	var family := ProgressionRules.pill_family(def)
	if family != "" and quality != "pill_grain":
		factor *= ProgressionRules.resistance_factor(c.cultivator, family)
		game.progression.apply_pill_dose(c.id, family)
	if not p.is_empty():
		# Quality (S15): a Flawed pill poisons more, a Pill Grain less.
		var tox := float(p.get("toxicity", 0)) * float(pill_cfg.get("toxicity", {}).get(quality, 1.0))
		factor *= pill_potency(s)
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
	if once:
		c.cultivator.treasure_uses[str(s.id)] = great_realm
		emit("natural_treasure_used", {"actor": c.id, "treasure": str(s.id)})
	# A Pill Soul carries its recipe's own unique effect (S44 soul_effect), every time.
	var soul_effect := ""
	if quality == "pill_soul":
		for extra in pill_cfg.get("soul", {}).get("effects", []):
			if str(extra.get("id", "")) != str(def.get("soul_effect", "")): continue
			soul_effect = str(extra.id)
			game.apply_effects(c.id, [extra], "pill_soul:" + str(s.id))
			emit("pill_soul_awakened", {"actor": c.id, "item": s.id, "effect": soul_effect})
	emit("item_used", {"actor": c.id, "item": s.id, "factor": factor})
	if def.has("pill"): emit("pill_used", {"actor": c.id, "item": s.id, "factor": factor, "quality": quality, "family": family,
		"resistance": ProgressionRules.resistance_count(c.cultivator, family)})
	return ok({"factor": factor, "quality": quality, "soul_effect": soul_effect, "family": family})

## A treasure set in one of the HUD's Treasure buttons (G2). The treasure stays in the bag; "" clears the slot.
func set_treasure(c, item: String, slot: int) -> Dictionary:
	if slot < 0 or slot > 1: return fail("bad_slot")
	if not Unlocks.is_unlocked(c.id, "treasures" if slot == 0 else "treasure_slot_2"):
		return fail("locked", {"text": Unlocks.locked_text("treasures" if slot == 0 else "treasure_slot_2")})
	if item != "":
		if not ContentDB.item(item).has("treasure") or c.inventory.count(item) <= 0: return fail("not_a_treasure")
		if c.inventory.treasures[1 - slot] == item: c.inventory.treasures[1 - slot] = ""
	c.inventory.treasures[slot] = item
	emit("treasure_set", {"actor": c.id, "slot": slot, "item": item})
	return ok()

## The vessel ridden in flight (G2): a flight item carried in the key pouch, or "" to fly unaided.
func choose_vessel(c, item: String) -> Dictionary:
	if item != "" and (not ContentDB.item(item).has("flight") or c.inventory.count(item) <= 0): return fail("not_a_vessel")
	c.inventory.vessel = item
	emit("vessel_changed", {"actor": c.id, "item": item})
	emit("system_used", {"actor": c.id, "system": "flight_vessel"})
	return ok()

func move_item(c, from: int, to: int) -> Dictionary:
	var bag: Array = c.inventory.bag
	if from < 0 or to < 0 or from >= bag.size() or to >= bag.size() or bag[from] == null: return fail("bad_index")
	var a = bag[from]
	var b = bag[to]
	if b != null and not ContentDB.is_equipment(str(a.id)) and stack_key(a) == stack_key(b):
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
			var part: Dictionary = s.duplicate()
			part.count = count
			bag[i] = part
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
