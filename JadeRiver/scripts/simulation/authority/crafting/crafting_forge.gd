class_name CraftingForge
extends CraftingPart
## CraftingAuthority's part: gear upkeep at the forge (S14, S47): enhancing with pity, inheriting, salvage, affix
## rerolls and locks, restoring a Shattered Relic, awakening a weapon, and mending a furnace.

# ------------------------------------------------------------------ gear upkeep (S14, S47)
func upkeep(key: String, fallback):
	return ContentDB.config("forge_upkeep").get(key, fallback)

## The salvage.json row for an item's grade: the metal it is forged and enhanced with, and what Salvage returns.
## Grades past the table use its last row.
func grade_row(item_id: String) -> Dictionary:
	var g := str(ContentDB.item(item_id).get("grade", "plain"))
	if ContentDB.has_entry("salvage", g): return ContentDB.entry("salvage", g)
	var rows: Array = ContentDB.all("salvage")
	return rows[-1] if not rows.is_empty() else {"metal": "copper_ore", "returns": []}

## The piece an intent names: by uid, worn or carried, else by worn slot or bag index ({inst, slot, index}, or {}).
func _target(c, intent: Dictionary) -> Dictionary:
	var at: Dictionary = c.inventory.locate(int(intent.get("uid", -1)))
	return at if not at.is_empty() else c.inventory.at_slot(str(intent.get("slot", "")), int(intent.get("index", -1)))

func uid_at(c, index: int) -> int:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return -1
	return int(c.inventory.bag[index].get("uid", -1))

## The chance an enhancement from the item's current level succeeds: sure up to +5, then 12% less a level,
## plus the item's pity (+5% for each failure since its last success) and any essence fed in.
func enhance_chance(inst: Dictionary, essence := 0) -> float:
	var lvl := int(inst.get("enhance", 0))
	if lvl < int(upkeep("risky_from", 5)): return 1.0
	var base := 1.0 - float(upkeep("fail_step", 0.12)) * (lvl - int(upkeep("risky_from", 5)) + 1)
	return clampf(base + float(inst.get("pity", 0.0)) + float(upkeep("essence_step", 0.025)) * essence, 0.0, 1.0)

## What an enhancement costs: {metal, count, taels, shards}.
func enhance_cost(inst: Dictionary) -> Dictionary:
	var lvl := int(inst.get("enhance", 0))
	var gi := StatRules.grade_index(str(ContentDB.item(str(inst.id)).get("grade", "plain")))
	return {"metal": str(grade_row(str(inst.id)).get("metal", "copper_ore")), "count": 2 * (lvl + 1), "taels": 20 * (lvl + 1) * (gi + 1),
		"shards": maxi(0, lvl - 4)}

## Why an enhancement cannot be paid for now ("" when it can): the metal, taels, shards and essence it needs.
func enhance_check(c, inst: Dictionary, essence := 0) -> String:
	if int(inst.get("enhance", 0)) >= 10: return Tx.t("ui.forge.max")
	var cost := enhance_cost(inst)
	if c.inventory.count(str(cost.metal)) < int(cost.count): return Tx.t("sim.crafting.needs_2") % [int(cost.count), ContentDB.item_name(str(cost.metal))]
	if game.economy.balance("silver_tael") < int(cost.taels): return Tx.plural("ui.forge.taels", int(cost.taels)) % int(cost.taels)
	if int(cost.shards) > 0 and c.inventory.count("spirit_stone_shard") < int(cost.shards): return Tx.t("sim.crafting.needs_spirit_stone_shards")
	if c.inventory.count("refining_essence") < essence: return Tx.t("sim.crafting.needs_2") % [essence, ContentDB.item_name("refining_essence")]
	return ""

## Why a reroll cannot be paid for now ("" when it can).
func reroll_check(c, inst: Dictionary) -> String:
	if (inst.get("affixes", []) as Array).is_empty(): return Tx.t("sim.crafting.no_affixes")
	var cost := reroll_cost(inst, c)
	if c.inventory.count("refining_essence") < int(cost.essence): return Tx.t("sim.crafting.needs_2") % [int(cost.essence), ContentDB.item_name("refining_essence")]
	if game.economy.balance("silver_tael") < int(cost.taels): return Tx.plural("ui.forge.taels", int(cost.taels)) % int(cost.taels)
	return ""

## Enhance (S14, S47): never destroys an item or takes a level. A failure spends the materials and adds 5% pity to
## the item, shown on it; a success clears the pity. Refining Essence (from Salvage) steadies an attempt, 2.5% each.
## The roll is on the affix stream, so it is deterministic per character.
func enhance(c, intent: Dictionary) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var at := _target(c, intent)
	if at.is_empty() or not ContentDB.is_equipment(str(at.inst.id)): return fail("not_equipment")
	var inst: Dictionary = at.inst
	var lvl := int(inst.get("enhance", 0))
	if lvl >= 10: return fail("max")
	var cost := enhance_cost(inst)
	if c.inventory.count(str(cost.metal)) < int(cost.count): return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(cost.count), ContentDB.item_name(str(cost.metal))]})
	if game.economy.balance("silver_tael") < int(cost.taels): return fail("insufficient_funds")
	if int(cost.shards) > 0 and c.inventory.count("spirit_stone_shard") < int(cost.shards): return fail("materials", {"text": Tx.t("sim.crafting.needs_spirit_stone_shards")})
	var essence := clampi(int(intent.get("essence", 0)), 0, int(upkeep("essence_max", 4))) if lvl >= int(upkeep("risky_from", 5)) else 0
	if c.inventory.count("refining_essence") < essence: return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [essence, ContentDB.item_name("refining_essence")]})
	var chance := enhance_chance(inst, essence)
	game.inventory.apply_remove(c.id, str(cost.metal), int(cost.count), "enhance")
	game.economy.apply_currency("silver_tael", -int(cost.taels), "enhance")
	if int(cost.shards) > 0: game.inventory.apply_remove(c.id, "spirit_stone_shard", int(cost.shards), "enhance")
	if essence > 0: game.inventory.apply_remove(c.id, "refining_essence", essence, "enhance")
	var success := chance >= 1.0 or Rng.stream(c.id, "affix").randf() < chance
	if success:
		inst.pity = 0.0
		game.inventory.apply_enhance(c.id, inst, lvl + 1, str(at.slot))
		# S47 weapon awakening: a Heaven-grade (or better) weapon at +10 is ready to be woken.
		if lvl + 1 >= 10 and awaken_grade_ok(str(inst.id)): game.quest.apply_flag(c.id, "forged_plus10")
	else:
		inst.pity = snappedf(float(inst.get("pity", 0.0)) + float(upkeep("pity_step", 0.05)), 0.001)
	emit("item_enhanced", {"actor": c.id, "item": inst.id, "level": int(inst.get("enhance", 0)), "success": success, "pity": float(inst.get("pity", 0.0))})
	emit("system_used", {"actor": c.id, "system": "enhance"})
	return ok({"success": success, "level": int(inst.get("enhance", 0)), "pity": float(inst.get("pity", 0.0)), "chance": chance})

## Inherit (S47): move an item's enhancement, less two levels, onto another piece for the same slot, for 2 Spirit
## Stones a level moved. The old piece goes back to +0; the new one keeps its own level if that is higher.
func inherit(c, from_uid: int, to_uid: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var a: Dictionary = c.inventory.locate(from_uid)
	var b: Dictionary = c.inventory.locate(to_uid)
	if a.is_empty() or b.is_empty() or from_uid == to_uid: return fail("not_equipment")
	var da := ContentDB.item(str(a.inst.id))
	var db := ContentDB.item(str(b.inst.id))
	if not ContentDB.is_equipment(str(a.inst.id)) or not ContentDB.is_equipment(str(b.inst.id)) or str(da.get("slot", "")) != str(db.get("slot", "")):
		return fail("wrong_slot", {"text": Tx.t("sim.crafting.inherit_same_slot")})
	var moved := int(a.inst.get("enhance", 0)) - int(upkeep("inherit_loss", 2))
	if moved <= int(b.inst.get("enhance", 0)): return fail("nothing_to_move", {"text": Tx.t("sim.crafting.inherit_nothing")})
	var stones := moved * int(upkeep("inherit_stones_per_level", 2))
	if game.economy.balance("spirit_stone") < stones: return fail("insufficient_funds", {"text": Tx.plural("sim.crafting.inherit_stones", stones) % stones})
	game.economy.apply_currency("spirit_stone", -stones, "inherit")
	game.inventory.apply_enhance(c.id, b.inst, moved, str(b.slot))
	game.inventory.apply_enhance(c.id, a.inst, 0, str(a.slot))
	a.inst.pity = 0.0
	emit("enhancement_inherited", {"actor": c.id, "item": b.inst.id, "from": a.inst.id, "levels": moved, "stones": stones})
	emit("system_used", {"actor": c.id, "system": "inherit"})
	return ok({"levels": moved, "stones": stones})

## What salvaging a set of bag items would return (locked, bound and worn pieces are never salvaged).
func salvage_preview(c, uids: Array) -> Dictionary:
	var returns := {}
	var items: Array = []
	for u in uids:
		var i: int = c.inventory.find_uid(int(u))
		if i < 0 or c.inventory.bag[i] == null: continue
		var inst: Dictionary = c.inventory.bag[i]
		if not ContentDB.is_equipment(str(inst.id)) or inst.get("bound", false) or c.inventory.locked.has(int(inst.get("uid", -1))): continue
		if not ContentDB.item(str(inst.id)).get("sell", true): continue   # a named piece (the Nine-Dragon Cauldron) is never broken up
		items.append(int(inst.uid))
		for r in grade_row(str(inst.id)).get("returns", []):
			returns[str(r.item)] = int(returns.get(str(r.item), 0)) + int(r.count)
	return {"items": items, "returns": returns}

## Salvage (S47): dismantle gear into its grade's metal and Refining Essence. Locked items are never touched.
func salvage(c, uids: Array) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var pv := salvage_preview(c, uids)
	if pv.items.is_empty(): return fail("cannot_salvage")
	var ids: Array = []
	for u in pv.items:
		var i: int = c.inventory.find_uid(int(u))
		ids.append(str(c.inventory.bag[i].id))
		game.inventory.apply_remove_index(c.id, i, 1, "salvage")
	for item_id in pv.returns: game.inventory.apply_add(c.id, str(item_id), int(pv.returns[item_id]), "salvage")
	emit("items_salvaged", {"actor": c.id, "items": ids, "returned": pv.returns})
	emit("system_used", {"actor": c.id, "system": "salvage"})
	return ok({"items": ids, "returned": pv.returns})

## What rerolling an item's affixes costs: {essence, taels}; a locked affix doubles it. S10 Insight 25: one reroll a
## week is free ({free: true}).
func reroll_cost(inst: Dictionary, c = null) -> Dictionary:
	if c != null and free_reroll_ready(c): return {"essence": 0, "taels": 0, "free": true}
	var gi := StatRules.grade_index(str(ContentDB.item(str(inst.id)).get("grade", "plain")))
	var ess: Array = upkeep("reroll_essence", [1])
	var mult := int(upkeep("lock_mult", 2)) if int(inst.get("locked_affix", -1)) >= 0 else 1
	return {"essence": int(ess[mini(gi, ess.size() - 1)]) * mult, "taels": int(upkeep("reroll_taels", 60)) * (gi + 1) * mult}

func free_reroll_ready(c) -> bool:
	return StatRules.gate_flag(c, "extra_reroll") and int(c.cooldowns.get("free_reroll_wk", -1)) != Clock.reset_week(Clock.now_utc())

## Reroll (S47 affix lock): every affix but the locked one is rolled again on the affix stream. The new roll waits
## beside the old one until you choose which to keep.
func reroll(c, uid: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "smithing"): return fail("locked")
	var at: Dictionary = c.inventory.locate(uid)
	if at.is_empty() or not ContentDB.is_equipment(str(at.inst.id)): return fail("not_equipment")
	var inst: Dictionary = at.inst
	if (inst.get("affixes", []) as Array).is_empty(): return fail("no_affixes", {"text": Tx.t("sim.crafting.no_affixes")})
	var cost := reroll_cost(inst, c)
	if c.inventory.count("refining_essence") < int(cost.essence): return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(cost.essence), ContentDB.item_name("refining_essence")]})
	if game.economy.balance("silver_tael") < int(cost.taels): return fail("insufficient_funds")
	if cost.get("free", false): c.cooldowns["free_reroll_wk"] = Clock.reset_week(Clock.now_utc())
	if int(cost.essence) > 0: game.inventory.apply_remove(c.id, "refining_essence", int(cost.essence), "reroll")
	if int(cost.taels) > 0: game.economy.apply_currency("silver_tael", -int(cost.taels), "reroll")
	var lock := int(inst.get("locked_affix", -1))
	var old: Array = inst.affixes
	var fresh: Array = []
	var taken: Array = []
	if lock >= 0 and lock < old.size(): taken.append(str(old[lock].id))
	var rng := Rng.stream(c.id, "affix")
	for i in old.size():
		if i == lock:
			fresh.append(old[i].duplicate())
			continue
		var a := LootRules.roll_affix(str(inst.id), int(inst.get("ilv", 1)), rng, taken)
		if a.is_empty(): a = old[i].duplicate()
		taken.append(str(a.id))
		fresh.append(a)
	inst.pending_affixes = fresh
	emit("affixes_rerolled", {"actor": c.id, "item": inst.id, "uid": uid, "old": old, "new": fresh})
	return ok({"old": old, "new": fresh, "cost": cost})

## Keep the new roll or the old one; either way the pending roll is gone.
func choose_affixes(c, uid: int, keep_new: bool) -> Dictionary:
	var at: Dictionary = c.inventory.locate(uid)
	if at.is_empty() or not at.inst.has("pending_affixes"): return fail("nothing_pending")
	if keep_new: game.inventory.apply_affixes(c.id, at.inst, at.inst.pending_affixes, str(at.slot))
	at.inst.erase("pending_affixes")
	return ok({"kept": "new" if keep_new else "old"})

## Lock one affix against the next rerolls (-1 unlocks).
func lock_affix(c, uid: int, affix: int) -> Dictionary:
	var at: Dictionary = c.inventory.locate(uid)
	if at.is_empty() or not ContentDB.is_equipment(str(at.inst.id)): return fail("not_equipment")
	if affix >= (at.inst.get("affixes", []) as Array).size(): return fail("no_affix")
	if affix < 0: at.inst.erase("locked_affix")
	else: at.inst.locked_affix = affix
	emit("affix_locked", {"actor": c.id, "item": at.inst.id, "affix": affix})
	return ok({"locked": affix})

## Restore a Shattered Relic at the forge (S47): Expert smithing, Cloudsteel and Refining Essence make it whole again,
## a relic with its spirit still asleep (bind it to wake it, S14).
func restore_relic(c, index: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var shard := str(c.inventory.bag[index].id)
	var target := str(ContentDB.item(shard).get("restores", ""))
	if target == "": return fail("not_a_relic")
	if not crafting.station_near(c, ["forge_anvil"]): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "forge"})
	if crafting.rank_index(crafting.rank_of(c, "smithing")) < crafting.rank_index("expert"): return fail("rank", {"text": Tx.t("sim.crafting.relic_needs_expert")})
	for need in [["cloudsteel_ore", 6], ["refining_essence", 6]]:
		if c.inventory.count(str(need[0])) < int(need[1]): return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(need[1]), ContentDB.item_name(str(need[0]))]})
	if game.economy.balance("silver_tael") < 3000: return fail("insufficient_funds")
	game.inventory.apply_remove(c.id, "cloudsteel_ore", 6, "restore_relic")
	game.inventory.apply_remove(c.id, "refining_essence", 6, "restore_relic")
	game.economy.apply_currency("silver_tael", -3000, "restore_relic")
	game.inventory.apply_remove_index(c.id, c.inventory.first_index(shard), 1, "restore_relic")
	var def := ContentDB.item(target)
	var inst := LootRules.make_instance(target, int(def.get("ilv", 1)), "fine", Rng.stream(c.id, "affix"), c.inventory.take_uid())
	game.inventory.apply_add_instance(c.id, inst, "restore_relic")
	emit("relic_restored", {"actor": c.id, "item": target, "from": shard})
	emit("system_used", {"actor": c.id, "system": "restore_relic"})
	return ok({"item": target})

## S47 weapon awakening (v1.1): a weapon of Heaven grade or better, forged to +10, wakes at a forge with a Weapon Soul
## Crystal for one whose Dao of that weapon has reached Explanation (tier 4). It glows, and strikes on its own every so
## many blows: its family's skill, or a legend's own.
static func awaken_grade_ok(item_id: String) -> bool:
	var def := ContentDB.item(item_id)
	return str(def.get("slot", "")) == "weapon" and StatRules.grade_index(str(def.get("grade", "plain"))) >= StatRules.grade_index("heaven")

static func awakened_skill(item_id: String) -> Dictionary:
	var def := ContentDB.item(item_id)
	if def.has("legend"): return def.legend.get("skill", {})
	return ContentDB.entry("weapon_families", str(def.get("family", ""))).get("awakened", {})

## Why a piece cannot be awakened now ("" when it can).
func awaken_check(c, inst: Dictionary) -> String:
	if inst.is_empty() or not awaken_grade_ok(str(inst.id)): return Tx.t("sim.crafting.awaken_grade")
	if inst.get("awakened", false): return Tx.t("sim.crafting.awaken_done")
	if awakened_skill(str(inst.id)).is_empty(): return Tx.t("sim.crafting.awaken_grade")
	if int(inst.get("enhance", 0)) < 10: return Tx.t("sim.crafting.awaken_plus10")
	var dao := str(ContentDB.entry("weapon_families", str(ContentDB.item(str(inst.id)).get("family", ""))).get("dao", ""))
	if int(c.cultivator.daos.get(dao, {}).get("tier", 0)) < 4: return Tx.t("sim.crafting.awaken_dao") % ContentDB.name_of("daos", dao)
	if c.inventory.count("weapon_soul_crystal") <= 0: return Tx.t("sim.crafting.awaken_crystal")
	if not crafting.station_near(c, ["forge_anvil"]): return Tx.t("sim.crafting.you_need_a") % "forge"
	return ""

func awaken_weapon(c, intent: Dictionary) -> Dictionary:
	var at := _target(c, intent)
	if at.is_empty(): return fail("not_equipment")
	var inst: Dictionary = at.inst
	var why := awaken_check(c, inst)
	if why != "": return fail("cannot", {"text": why})
	game.inventory.apply_remove(c.id, "weapon_soul_crystal", 1, "awaken")
	inst.awakened = true
	var sk := awakened_skill(str(inst.id))
	game.quest.apply_flag(c.id, "awakened:" + str(inst.id))
	emit("weapon_awakened", {"actor": c.id, "item": str(inst.id), "skill": str(sk.get("name", "")), "legend": ContentDB.item(str(inst.id)).has("legend")})
	emit("system_used", {"actor": c.id, "system": "awaken_weapon"})
	return ok({"skill": str(sk.get("name", ""))})

## Mend a furnace at the forge (S44): a blast costs it 10 durability, and at 0 it is cracked. Mending takes its grade's
## metal, two for each 10 durability lost, and brings it back to 100.
func mend_cost(inst: Dictionary) -> Dictionary:
	var lost := 100 - int(inst.get("durability", 100))
	return {"metal": str(grade_row(str(inst.id)).get("metal", "copper_ore")), "count": maxi(1, int(ceil(lost / 10.0)) * 2), "lost": lost}

func mend_furnace(c, uid: int) -> Dictionary:
	var at: Dictionary = c.inventory.locate(uid)
	if at.is_empty() and c.inventory.furnace != null: at = {"inst": c.inventory.furnace, "slot": "tool_furnace", "index": -1}
	if at.is_empty() or str(ContentDB.item(str(at.inst.id)).get("slot", "")) != "tool_furnace": return fail("not_a_furnace")
	var cost := mend_cost(at.inst)
	if int(cost.lost) <= 0: return fail("whole", {"text": Tx.t("sim.crafting.furnace_whole")})
	if not crafting.station_near(c, ["forge_anvil"]): return fail("no_station", {"text": Tx.t("sim.crafting.you_need_a") % "forge"})
	if c.inventory.count(str(cost.metal)) < int(cost.count):
		return fail("materials", {"text": Tx.t("sim.crafting.needs_2") % [int(cost.count), ContentDB.item_name(str(cost.metal))]})
	game.inventory.apply_remove(c.id, str(cost.metal), int(cost.count), "mend_furnace")
	game.inventory.apply_durability(c.id, at.inst, 100, str(at.slot))
	emit("system_used", {"actor": c.id, "system": "mend_furnace"})
	return ok({"item": str(at.inst.id)})
