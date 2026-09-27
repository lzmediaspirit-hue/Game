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

## P7b (item_plan §4.1): the equipment roll's rules (grades.json `drop`).
static func drop_cfg() -> Dictionary:
	return ContentDB.config("grades").get("drop", {})

## Roll a loot table. Returns {items: [{item, count}], coins, equipment: [drop specs]}. `extra`: no_equipment (no
## equipment and no named piece), needs (quest items still wanted), elite (the foe is an elite, by role or by spawn).
static func roll(table_id: String, rng: RandomNumberGenerator, level: int, drop_rate: float, coin_find: float, extra := {}) -> Dictionary:
	var table := ContentDB.entry("loot_tables", table_id)
	var out := {"items": [], "coins": 0, "equipment": [], "lost": []}   # lost: P13a lost manuals rolled (not handed out)
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
	# P13a lost manuals (technique_plan §5.3, §5.6): rolled on every kill like a named row, never raised by drop rate,
	# and never handed out here: ProgressionAuthority.lost_drops keeps one only while its art is still lost (with pity).
	for r in table.get("lost", []):
		out.lost.append({"art": str(r.art), "item": str(r.item), "pity": int(r.get("pity", 0)), "hit": rng.randf() < float(r.get("chance", 0.0))})
	# Quest drops: only while the quest is active and the item is still missing (`extra.needs`).
	var needs: Dictionary = extra.get("needs", {})
	for q in table.get("quest_drops", []):
		if needs.has(str(q.item)) and needs[str(q.item)] == str(q.get("quest", "")) and rng.randf() < float(q.get("chance", 1.0)):
			out.items.append({"item": q.item, "count": rng.randi_range(int(q.count[0]), int(q.count[1]))})
	var coins: Dictionary = table.get("coins", {})
	if not coins.is_empty() and rng.randf() < float(coins.get("chance", 0.0)):
		out.coins = coins_for(level, float(coins.get("mult", 1)), coin_find)
	if extra.get("no_equipment", false): return out
	var eq: Dictionary = table.get("equipment", {})
	if not eq.is_empty() and rng.randf() < float(eq.get("chance", 0.0)) * dr:
		out.equipment.append({"level": level, "min_quality": str(eq.get("min_quality", "flawed")), "starter": bool(table.get("starter", false))})
	# P7b named rows (item_plan §4.2): each rolls on every kill like a rare row, `elite_named` only for an elite; a named
	# piece drops at its source's quality floor, raised to `named_floor`.
	var order: Array = ContentDB.config("grades").get("quality_order", [])
	var floor_q := str(eq.get("min_quality", "flawed"))
	if order.find(floor_q) < order.find(str(drop_cfg().get("named_floor", "common"))): floor_q = str(drop_cfg().get("named_floor", "common"))
	for key in (["named", "elite_named"] if extra.get("elite", false) else ["named"]):
		for r in table.get(key, []):
			if rng.randf() < float(r.get("chance", 0.0)) * dr: out.equipment.append({"item": str(r.item), "min_quality": floor_q})
	return out

## A beast taken whole by the Taming Cauldron (S47): its materials, each at full count, with no roll.
static func capture_materials(table_id: String) -> Array:
	var out: Array = []
	var seen := {}
	for g in _material_rows(ContentDB.entry("loot_tables", table_id)):
		var id := str(g.get("item", ""))
		var def := ContentDB.item(id)
		if id == "" or seen.has(id) or def.get("quest_item", false) or str(def.get("type", "")) in ["egg", "scroll", "manual"]: continue
		seen[id] = true
		out.append({"item": id, "count": int(g.get("count", [1, 1])[1])})
	return out

## A table's material rows: the guaranteed ones and every group's picks.
static func _material_rows(table: Dictionary) -> Array:
	var rows: Array = table.get("guaranteed", []).duplicate()
	for group in table.get("groups", []): rows.append_array(group.get("pick", []))
	return rows

## Can a kill on this table drop this item (a material row or a quest drop)?
static func drops_item(table_id: String, item: String) -> bool:
	var table := ContentDB.entry("loot_tables", table_id)
	for r in _material_rows(table) + table.get("quest_drops", []):
		if str(r.get("item", "")) == item: return true
	return false

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

## A banded base: what the equipment roll picks from (P7a, P7b). Named pieces come from their own sources, legendary
## weapons from their chains, imitation relics from the forge; sets, pet gear and the gourd, cape, talisman and furnace
## slots never drop at random.
static func is_banded(a: Dictionary) -> bool:
	return not (a.has("set") or a.get("relic", false) or a.has("legend") or a.has("imitation") or a.has("named") or a.has("pet_gear")
		or str(a.get("slot", "")) in drop_cfg().get("pool_skip_slots", []))

## The top Level an equipment roll reaches: the last Level of the highest grade that has banded bases.
static func drop_level_cap() -> int:
	var grades := {}
	for a in ContentDB.all("artifacts"):
		if is_banded(a): grades[str(a.grade)] = true
	var top := 1
	for band in ContentDB.stat_const("grade_bands", []):
		if grades.has(str(band[0])): top = maxi(top, int(band[2]))
	return top

## A drop's quality from its source's floor (grades.json drop.quality: the shares from flawed to perfect); each Fortune
## point moves the roll toward the best.
static func roll_quality(rng: RandomNumberGenerator, min_quality: String, fortune: float) -> String:
	var order: Array = ContentDB.config("grades").get("quality_order", ["flawed", "common", "fine", "superior", "perfect"])
	var shares: Array = drop_cfg().get("quality", {}).get(min_quality, [])
	var r := rng.randf() - fortune * float(drop_cfg().get("fortune_shift", 0.001))
	var acc := 0.0
	for q in range(shares.size() - 1, -1, -1):
		if float(shares[q]) <= 0.0: continue
		acc += float(shares[q])
		if r < acc: return str(order[q])
	return min_quality

## Build a banded piece from an equipment roll (S32, P7b item_plan §4.1): iLv = the foe's Level ± 2 up to the highest
## banded grade's top Level; a weapon on `weapon_share` of rolls while weapons are open (one in three of those in the
## family in hand), else one of the four armour slots, among the banded bases of that iLv's grade.
static func make_equipment(rng: RandomNumberGenerator, level: int, min_quality: String, fortune: float, allow_weapons: bool, uid: int, family := "") -> Dictionary:
	var cfg := drop_cfg()
	var spread := int(cfg.get("level_spread", 2))
	var ilv := clampi(level + rng.randi_range(-spread, spread), 1, drop_level_cap())
	var bases := banded_bases(grade_for_ilv(ilv))
	var weapons: Array = bases.weapons if allow_weapons else []
	var armour: Array = bases.armour
	var pool := armour
	if not weapons.is_empty() and (armour.is_empty() or rng.randf() < float(cfg.get("weapon_share", 0.4))):
		pool = weapons
		var own := weapons.filter(func(a): return str(a.get("family", "")) == family)
		if not own.is_empty() and rng.randf() < float(cfg.get("family_bias", 0.3333)): pool = own
	if pool.is_empty(): return {}
	var base: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
	return make_instance(base.id, ilv, roll_quality(rng, min_quality, fortune), rng, uid)

## The banded bases of a grade: {weapons, armour}.
static func banded_bases(grade: String) -> Dictionary:
	var out := {"weapons": [], "armour": []}
	for a in ContentDB.all("artifacts"):
		if a.get("grade") != grade or not is_banded(a): continue
		(out.weapons if str(a.slot) == "weapon" else out.armour).append(a)
	return out

## Starter gear (grades.json drop.starter): a first-room foe's piece from a spec (`level`, `min_quality`), one of the
## plain bases of the starter families or of the four armour slots (a weapon on `weapon_share` of rolls), at the par
## character's item Level for the foe's Level, a weapon never above par quality there, so no weapon outruns early par
## (docs/research/stat_scaling_research.md §6). The first weapon (`first`, of `family`) is exactly its `min_quality`.
static func make_starter(rng: RandomNumberGenerator, spec: Dictionary, fortune: float, uid: int) -> Dictionary:
	var level := int(spec.get("level", 1))
	var ilv := starter_ilv(level)
	var bases := banded_bases(grade_for_ilv(ilv))
	var families: Array = [spec.family] if spec.has("family") else drop_cfg().get("starter", {}).get("families", [])
	var weapons: Array = bases.weapons.filter(func(a): return str(a.get("family", "")) in families)
	var pool: Array = weapons if spec.has("family") or rng.randf() < float(drop_cfg().get("weapon_share", 0.4)) else bases.armour
	if pool.is_empty(): return {}
	var base: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
	var q := str(spec.get("min_quality", "flawed"))
	if not spec.get("first", false): q = roll_quality(rng, q, fortune)
	if str(base.slot) == "weapon": q = starter_quality(q, level)
	return make_instance(base.id, ilv, q, rng, uid)

## A starter piece's item Level: the par character's at the foe's Level (its weapon `par.weapon_lag` Levels behind).
static func starter_ilv(level: int) -> int:
	return maxi(1, level - int(ContentDB.stat_const("par.weapon_lag", 3)))

## A starter weapon's quality: the one rolled, lowered to the par character's at the foe's Level.
static func starter_quality(rolled: String, level: int) -> String:
	var order: Array = ContentDB.config("grades").get("quality_order", [])
	var top := str(StatRules.par_step("quality", level))
	return top if order.find(rolled) > order.find(top) else rolled

## What a drop spec makes: a named piece (`item`) at its own iLv and its source's quality, starter gear (`starter`) or
## a banded piece.
static func make_drop(rng: RandomNumberGenerator, spec: Dictionary, fortune: float, allow_weapons: bool, uid: int, family := "") -> Dictionary:
	if spec.get("starter", false): return make_starter(rng, spec, fortune, uid)
	if not spec.has("item"):
		return make_equipment(rng, int(spec.get("level", 1)), str(spec.get("min_quality", "flawed")), fortune, allow_weapons, uid, family)
	var def := ContentDB.item(str(spec.item))
	if def.is_empty(): return {}
	return make_instance(str(spec.item), int(def.get("ilv", 1)), roll_quality(rng, str(spec.get("min_quality", "common")), fortune), rng, uid)

static func make_instance(item_id: String, ilv: int, quality: String, rng: RandomNumberGenerator, uid: int) -> Dictionary:
	var def := ContentDB.item(item_id)
	var inst := {"uid": uid, "id": item_id, "count": 1, "ilv": ilv, "quality": quality, "affixes": [], "enhance": 0,
		"bound": false, "durability": 100, "inlays": []}
	if def.get("relic", false):
		inst.sealed = true   # S14: found artifacts keep their power sealed until bound
		if def.has("spirit"): inst.spirit = "dormant"
	var n := int(ContentDB.config("grades").get("qualities", {}).get(quality, {}).get("affixes", 0))
	var pool := affix_pool(def, [])
	for i in n:
		if pool.is_empty() or rng == null: break
		var a: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
		pool.erase(a)
		var v := rng.randf_range(float(a.range[0]), float(a.range[1])) + float(a.get("per_level", 0.0)) * ilv
		inst.affixes.append({"id": a.id, "stat": a.stat, "op": a.op, "value": snappedf(v, 0.001)})
	return inst

## The random affixes a piece can roll: its slot's, but not the ones only named pieces carry (P7b) or `exclude`.
static func affix_pool(def: Dictionary, exclude: Array) -> Array:
	var slot := str(def.get("slot", ""))
	return ContentDB.all("affixes").filter(func(a): return slot in a.get("slots", []) and not a.get("named_only", false) and not str(a.id) in exclude)

## One affix for an item from its slot's pool, avoiding ids already on it (S47 reroll).
static func roll_affix(item_id: String, ilv: int, rng: RandomNumberGenerator, exclude: Array) -> Dictionary:
	var pool := affix_pool(ContentDB.item(item_id), exclude)
	if pool.is_empty() or rng == null: return {}
	var a: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
	var v := rng.randf_range(float(a.range[0]), float(a.range[1])) + float(a.get("per_level", 0.0)) * ilv
	return {"id": a.id, "stat": a.stat, "op": a.op, "value": snappedf(v, 0.001)}

# ------------------------------------------------------------------ prices (S39)
const TYPE_MULT := {"material": 0.25, "herb": 0.25, "ore": 0.25, "beast_part": 0.25, "core": 0.5, "hollow": 0.25, "fish": 0.4,
	"food": 1.0, "pill": 2.0, "talisman": 2.0, "tool": 3.0, "taming": 1.0, "jade": 2.0, "scroll": 1.5, "other": 0.5, "egg": 3.0,
	"insect": 0.3, "critter": 0.35, "wisp": 0.2}

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
