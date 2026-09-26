class_name LootRules
extends RefCounted
## S32 · Drop tables and S39 · prices. Pure: every roll takes an RNG stream.

static func coins_for(level: int, mult: float, coin_find: float) -> int:
	return maxi(1, int(round((1.0 + 0.5 * level) * mult * (1.0 + clampf(coin_find, 0.0, 1.0)))))

## S21: coins are counted in taels; a zone pays them in its everyday currency at its coin_scale
## (the Expanse pays Spirit Stones). Returns {currency, amount}; never rounds a drop down to zero.
static func zone_coins(room_id: String, taels: int) -> Dictionary:
	var zone := ContentDB.zone_of_room(room_id)
	var currency := str(zone.get("currency", {}).get("everyday", "silver_tael"))
	if taels <= 0: return {"currency": currency, "amount": 0}
	var scale := float(zone.get("coin_scale", 1.0))
	return {"currency": currency, "amount": maxi(1, int(round(taels * scale)))}

## Roll a loot table. Returns {items: [{item, count}], coins, equipment: [instance specs]}.
static func roll(table_id: String, rng: RandomNumberGenerator, level: int, drop_rate: float, coin_find: float, extra := {}) -> Dictionary:
	var table := ContentDB.entry("loot_tables", table_id)
	var out := {"items": [], "coins": 0, "equipment": []}
	if table.is_empty(): return out
	var dr := 1.0 + clampf(drop_rate, 0.0, 1.0)
	for g in table.get("guaranteed", []):
		if rng.randf() < float(g.get("chance", 1.0)):
			out.items.append({"item": g.item, "count": rng.randi_range(int(g.count[0]), int(g.count[1]))})
	for group in table.get("groups", []):
		var picks: Array = group.get("pick", [])
		if picks.is_empty(): continue
		if rng.randf() < minf(1.0, float(group.get("chance", 1.0)) * dr):
			var p := RngService_weighted(rng, picks)
			if not p.is_empty(): out.items.append({"item": p.item, "count": rng.randi_range(int(p.count[0]), int(p.count[1]))})
	for r in table.get("rare", []):
		if rng.randf() < float(r.get("chance", 0.0)) * dr:
			out.items.append({"item": r.item, "count": rng.randi_range(int(r.count[0]), int(r.count[1]))})
	# Quest drops: only while the quest is active and the item is still missing (`extra.needs`).
	var needs: Dictionary = extra.get("needs", {})
	for q in table.get("quest_drops", []):
		if needs.has(str(q.item)) and needs[str(q.item)] == str(q.get("quest", "")) and rng.randf() < float(q.get("chance", 1.0)):
			out.items.append({"item": q.item, "count": rng.randi_range(int(q.count[0]), int(q.count[1]))})
	var coins: Dictionary = table.get("coins", {})
	if not coins.is_empty() and rng.randf() < float(coins.get("chance", 0.0)):
		out.coins = coins_for(level, float(coins.get("mult", 1)), coin_find)
	var eq: Dictionary = table.get("equipment", {})
	if not eq.is_empty() and not extra.get("no_equipment", false) and rng.randf() < float(eq.get("chance", 0.0)) * dr:
		out.equipment.append({"level": level, "min_quality": str(eq.get("min_quality", "flawed"))})
	return out

## A beast taken whole by the Taming Cauldron (S47): its materials, each at full count, with no roll.
static func capture_materials(table_id: String) -> Array:
	var table := ContentDB.entry("loot_tables", table_id)
	var sources: Array = table.get("guaranteed", []).duplicate()
	for group in table.get("groups", []): sources.append_array(group.get("pick", []))
	var out: Array = []
	var seen := {}
	for g in sources:
		var id := str(g.get("item", ""))
		var def := ContentDB.item(id)
		if id == "" or seen.has(id) or def.get("quest_item", false) or str(def.get("type", "")) in ["egg", "scroll", "manual"]: continue
		seen[id] = true
		out.append({"item": id, "count": int(g.get("count", [1, 1])[1])})
	return out

static func RngService_weighted(rng: RandomNumberGenerator, entries: Array) -> Dictionary:
	var total := 0.0
	for e in entries: total += float(e.get("weight", 1))
	if total <= 0.0: return {}
	var roll := rng.randf() * total
	for e in entries:
		roll -= float(e.get("weight", 1))
		if roll < 0.0: return e
	return entries.back()

static func grade_for_ilv(ilv: int) -> String:
	for band in ContentDB.stat_const("grade_bands", []):
		if ilv >= int(band[1]) and ilv <= int(band[2]): return str(band[0])
	return "plain"

## Build an equipment instance from a drop spec (S32): iLv = monster Level ± 2 inside
## the grade band; quality and affixes from the `affix` stream and Fortune.
static func make_equipment(rng: RandomNumberGenerator, level: int, min_quality: String, fortune: float, allow_weapons: bool, uid: int) -> Dictionary:
	var ilv := clampi(level + rng.randi_range(-2, 2), 1, 81)   # to the Azure Expanse's top Level
	var grade := grade_for_ilv(ilv)
	var candidates: Array = []
	for a in ContentDB.all("artifacts"):
		if a.get("grade") != grade or a.has("set") or a.get("relic", false) or a.slot in ["gourd", "cape", "talisman", "tool_furnace"] or a.has("pet_gear"): continue
		if a.slot == "weapon" and not allow_weapons: continue
		candidates.append(a)
	if candidates.is_empty(): return {}
	var base: Dictionary = candidates[rng.randi_range(0, candidates.size() - 1)]
	var order: Array = ContentDB.config("grades").get("quality_order", ["flawed", "common", "fine", "superior", "perfect"])
	var q := order.find(min_quality)
	var roll := rng.randf() - fortune * 0.001
	if roll < 0.05: q += 3
	elif roll < 0.20: q += 2
	elif roll < 0.50: q += 1
	q = clampi(q, 0, 4)
	var quality: String = order[q]
	return make_instance(base.id, ilv, quality, rng, uid)

static func make_instance(item_id: String, ilv: int, quality: String, rng: RandomNumberGenerator, uid: int) -> Dictionary:
	var def := ContentDB.item(item_id)
	var inst := {"uid": uid, "id": item_id, "count": 1, "ilv": ilv, "quality": quality, "affixes": [], "enhance": 0,
		"bound": false, "durability": 100, "inlays": []}
	if def.get("relic", false):
		inst.sealed = true   # S14: found artifacts keep their power sealed until bound
		if def.has("spirit"): inst.spirit = "dormant"
	var n := int(ContentDB.config("grades").get("qualities", {}).get(quality, {}).get("affixes", 0))
	var pool: Array = []
	for a in ContentDB.all("affixes"):
		if def.get("slot", "") in a.get("slots", []): pool.append(a)
	for i in n:
		if pool.is_empty() or rng == null: break
		var a: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
		pool.erase(a)
		var v := rng.randf_range(float(a.range[0]), float(a.range[1])) + float(a.get("per_level", 0.0)) * ilv
		inst.affixes.append({"id": a.id, "stat": a.stat, "op": a.op, "value": snappedf(v, 0.001)})
	return inst

## One affix for an item from its slot's pool, avoiding ids already on it (S47 reroll).
static func roll_affix(item_id: String, ilv: int, rng: RandomNumberGenerator, exclude: Array) -> Dictionary:
	var def := ContentDB.item(item_id)
	var pool: Array = []
	for a in ContentDB.all("affixes"):
		if def.get("slot", "") in a.get("slots", []) and not str(a.id) in exclude: pool.append(a)
	if pool.is_empty() or rng == null: return {}
	var a: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
	var v := rng.randf_range(float(a.range[0]), float(a.range[1])) + float(a.get("per_level", 0.0)) * ilv
	return {"id": a.id, "stat": a.stat, "op": a.op, "value": snappedf(v, 0.001)}

# ------------------------------------------------------------------ prices (S39)
const TYPE_MULT := {"material": 0.25, "herb": 0.25, "ore": 0.25, "beast_part": 0.25, "core": 0.5, "hollow": 0.25, "fish": 0.4,
	"food": 1.0, "pill": 2.0, "talisman": 2.0, "tool": 3.0, "taming": 1.0, "jade": 2.0, "scroll": 1.5, "other": 0.5, "egg": 3.0,
	"insect": 0.3}

static func value_of(item_id: String, instance = null) -> int:
	var def := ContentDB.item(item_id)
	if def.is_empty(): return 0
	if def.has("value_override"): return int(def.value_override)
	if def.get("type") in ["key", "treasure", "currency_item"] or def.get("sell", true) == false: return 0
	var ilv := float(def.get("ilv", 1))
	if instance != null: ilv = float(instance.get("ilv", ilv))
	var base := 1.0 + 0.4 * pow(ilv, 1.5)
	if def.get("type") == "equipment":
		var q := "common" if instance == null else str(instance.get("quality", "common"))
		return maxi(1, int(round(base * 10.0 * StatRules.quality_mult(q))))
	return maxi(1, int(round(base * float(TYPE_MULT.get(def.get("type", "material"), 0.5)))))

static func buy_price(item_id: String) -> int:
	var def := ContentDB.item(item_id)
	if def.has("price"): return int(def.price)
	return maxi(1, value_of(item_id) * 4)

static func sell_price(item_id: String, instance = null) -> int:
	return value_of(item_id, instance)
