class_name StatRules
extends RefCounted
## S10/S11/S14 · Attributes, derived stats, equipment values and Combat Power.
## `rebuild` is called by the owning authority whenever a source changes; it only
## touches the character's StatBlock and pool maxima.

const ATTRIBUTES := ["body", "agility", "essence", "spirit", "insight", "fortune"]
const PERMANENT_PREFIXES := ["gear:", "set:", "title:", "injury:", "gate:", "legacy:", "collection:", "jade:", "pet:", "sect:", "aptitude:"]

static func poly(spec: Dictionary, x: float) -> float:
	return float(spec.get("a", 0)) + float(spec.get("b", 0)) * x + float(spec.get("c", 0)) * x * x

static func pool_base(pool: String, lv: int, realm_key: String) -> float:
	var spec: Dictionary = ContentDB.stat_const("pools.%s" % pool, {})
	if spec.is_empty(): return 0.0
	if spec.has("from_realm") and not ProgressionRules.at_least(realm_key, str(spec.from_realm)): return 0.0
	var x := float(lv) - float(spec.get("offset", 0))
	return poly(spec, x)

static func weapon_attack(ilv: float) -> float:
	return poly(ContentDB.stat_const("equipment.weapon_attack", {}), ilv)

static func armour_defence(ilv: float) -> float:
	return poly(ContentDB.stat_const("equipment.armour_defence", {}), ilv)

static func quality_mult(q: String) -> float:
	return float(ContentDB.config("grades").get("qualities", {}).get(q, {}).get("mult", 1.0))

static func grade_index(grade: String) -> int:
	return (ContentDB.config("grades").get("order", []) as Array).find(grade)

static func family_of_weapon(instance) -> String:
	if instance == null: return "fists"
	return str(ContentDB.item(instance.id).get("family", "fists"))

static func family(c) -> Dictionary:
	return ContentDB.entry("weapon_families", family_of_weapon(c.inventory.equipped.get("weapon")))

## Item multiplier from quality, enhancement and the energy-type limit (S14).
static func instance_mult(instance, energy_type: String) -> float:
	var def := ContentDB.item(instance.id)
	var m := quality_mult(str(instance.get("quality", "common")))
	m *= 1.0 + float(ContentDB.stat_const("equipment.enhance_per_level", 0.05)) * int(instance.get("enhance", 0))
	var order := ["none", "primal_qi", "true_qi", "sage_qi", "law_qi", "monarch_qi", "heavenforce"]
	var made := order.find(str(def.get("energy_type", "none")))
	var wearer := order.find(energy_type)
	if made >= 0 and wearer >= 0 and wearer - made >= 2: m *= float(ContentDB.stat_const("equipment.energy_type_penalty", 0.5))
	if int(instance.get("durability", 100)) <= 0: m *= 0.5
	return m

## Stat modifiers granted by one equipped instance (base stats, affixes, inlays).
static func instance_modifiers(slot: String, instance, energy_type: String) -> Array:
	var out: Array = []
	if instance == null: return out
	var def := ContentDB.item(instance.id)
	var ilv := float(instance.get("ilv", def.get("ilv", 1)))
	var mult := instance_mult(instance, energy_type)
	var src := "gear:" + slot
	var share: Dictionary = ContentDB.stat_const("equipment.slot_share", {})
	var arm := armour_defence(ilv) * mult
	match slot:
		"robe":
			out.append({"stat": "physical_defense", "op": "flat", "value": arm * float(share.get("robe", 0.4)), "source": src})
			out.append({"stat": "qi_resistance", "op": "flat", "value": arm * 0.2, "source": src})
			out.append({"stat": "max_hp", "op": "flat", "value": ilv * 3.0 * mult, "source": src})
		"trousers":
			out.append({"stat": "physical_defense", "op": "flat", "value": arm * float(share.get("trousers", 0.3)), "source": src})
			out.append({"stat": "evasion", "op": "flat", "value": ilv * 0.5 * mult, "source": src})
			out.append({"stat": "max_hp", "op": "flat", "value": ilv * 2.0 * mult, "source": src})
		"boots":
			out.append({"stat": "physical_defense", "op": "flat", "value": arm * float(share.get("boots", 0.15)), "source": src})
			out.append({"stat": "evasion", "op": "flat", "value": ilv * 0.4 * mult, "source": src})
			out.append({"stat": "move_speed", "op": "pct_add", "value": 0.01 * (grade_index(str(def.get("grade", "plain"))) + 1), "source": src})
		"hat":
			out.append({"stat": "physical_defense", "op": "flat", "value": arm * float(share.get("hat", 0.15)), "source": src})
			out.append({"stat": "soul_defense", "op": "flat", "value": arm * 0.3, "source": src})
			out.append({"stat": "accuracy", "op": "flat", "value": ilv * 0.5 * mult, "source": src})
		"cape":
			for el in def.get("resist", []):
				out.append({"stat": "elemental_resistance", "op": "flat", "value": 0.1, "source": src, "condition": {"element": el}})
		"talisman":
			out.append({"stat": "max_soul", "op": "flat", "value": ilv * 5.0 * mult, "source": src})
			out.append({"stat": "soul_defense", "op": "flat", "value": arm * 0.4, "source": src})
	for a in instance.get("affixes", []):
		out.append({"stat": str(a.stat), "op": str(a.get("op", "flat")), "value": float(a.value), "source": src + ":affix"})
	for j in instance.get("inlays", []):
		var jd := ContentDB.item(str(j))
		if jd.has("jade"):
			var tier := clampi(grade_index(str(def.get("grade", "plain"))) - 1, 0, 2)
			out.append({"stat": str(jd.jade.attribute), "op": "flat", "value": float(jd.jade["values"][tier]), "source": "jade:" + slot})
	return out

static func set_modifiers(c) -> Array:
	var counts := {}
	for slot in c.inventory.equipped:
		var inst = c.inventory.equipped[slot]
		if inst == null: continue
		var s := str(ContentDB.item(inst.id).get("set", ""))
		if s != "": counts[s] = int(counts.get(s, 0)) + 1
	var out: Array = []
	for s in counts:
		var bonuses: Dictionary = ContentDB.entry("sets", s).get("bonuses", {})
		for need in bonuses:
			if counts[s] >= int(need):
				for b in bonuses[need]:
					var m: Dictionary = b.duplicate(true)
					m["source"] = "set:%s:%s" % [s, need]
					out.append(m)
	return out

## Attribute track bonuses before modifiers (S10).
static func attribute_bases(c, lv: int) -> Dictionary:
	var a: Dictionary = ContentDB.stat_const("attributes", {})
	var base := float(a.get("base", 5)) + float(a.get("per_level", 1)) * lv
	var out := {}
	for attr in ATTRIBUTES: out[attr] = base
	out.fortune = float(a.get("base", 5))
	out.body += float(a.get("body_per_body_level", 1)) * c.cultivator.body_level
	if c.cultivator.energy_type == "true_qi":
		out.essence += float(a.get("essence_per_purity_grade", 3)) * (9 - c.cultivator.purity)
	var m := ProgressionRules.method(c.cultivator.method_id)
	if not m.is_empty():
		out.essence += float(a.get("essence_per_capacity", 10)) * (float(m.get("capacity", 1.0)) - 1.0)
	out.spirit += float(a.get("spirit_per_soul_points", 0.1)) * c.cultivator.soul_cultivation
	var tiers := 0
	for d in c.cultivator.daos: tiers += int(c.cultivator.daos[d].get("tier", 0))
	out.insight += float(a.get("insight_per_dao_tier", 2)) * tiers
	for ch in c.cultivator.meridians:
		if out.has(ch): out[ch] += float(c.cultivator.meridians[ch])
	var origin := ContentDB.entry("origins", c.cultivator.origin)
	for attr in origin.get("bonus", {}): out[attr] += float(origin.bonus[attr])
	return out

## Rebuild every permanent modifier and base value. Returns the changed stat ids.
static func rebuild(c) -> Array:
	var sb: StatBlock = c.stats
	var before := sb.finals.duplicate()
	var lv := ProgressionRules.level(c)
	var realm_key: String = c.cultivator.realm_key
	for p in PERMANENT_PREFIXES: sb.remove_prefix(p)
	var energy: String = c.cultivator.energy_type
	for slot in c.inventory.equipped:
		for m in instance_modifiers(slot, c.inventory.equipped[slot], energy): sb.add_modifier(m)
	for m in set_modifiers(c): sb.add_modifier(m)
	# Injuries (S05): each severity step applies its listed penalties.
	for kind in c.cultivator.injuries:
		var sev := int(c.cultivator.injuries[kind].get("severity", 1))
		for e in ContentDB.entry("injuries", kind).get("effects", []):
			sb.add_modifier({"stat": e.stat, "op": e.op, "value": float(e.per_severity) * sev, "source": "injury:" + kind + ":" + str(e.stat)})
	# Title bonus (+1% to one stat, S34).
	var title := ContentDB.entry("titles", c.cultivator.active_title)
	if not title.is_empty() and title.has("stat"):
		sb.add_modifier({"stat": title.stat, "op": str(title.get("op", "pct_add")), "value": float(title.get("value", 0.01)), "source": "title:" + title.id})
	# Meridian gates at 25 points (stat gates only; flags are read by rules).
	var gates: Dictionary = ContentDB.stat_const("meridian_gates", {})
	for ch in gates:
		for need in gates[ch]:
			var g: Dictionary = gates[ch][need]
			if g.has("stat") and int(c.cultivator.meridians.get(ch, 0)) >= int(need):
				sb.add_modifier({"stat": g.stat, "op": g.op, "value": float(g.value), "source": "gate:%s:%s" % [ch, need]})
	# Aptitude (hidden then revealed, each at most ±15%, S08).
	for key in c.cultivator.aptitude:
		var ap: Dictionary = c.cultivator.aptitude[key]
		if key == "physique": sb.add_modifier({"stat": "max_hp", "op": "pct_add", "value": float(ap.get("value", 0)), "source": "aptitude:physique"})
		if key == "spirit_aptitude": sb.add_modifier({"stat": "max_soul", "op": "pct_add", "value": float(ap.get("value", 0)), "source": "aptitude:spirit"})
	for m in c.get_meta("extra_modifiers", []): sb.add_modifier(m)
	# Attributes first.
	var attr_base := attribute_bases(c, lv)
	for attr in attr_base: sb.set_base(attr, attr_base[attr])
	var A := {}
	for attr in ATTRIBUTES: A[attr] = sb.compute(attr)
	var fx: Dictionary = ContentDB.stat_const("attribute_effects", {})
	var fam := family(c)
	# Pools (S11).
	var hp_base = pool_base("hp", lv, realm_key) * (1.0 + float(fx.body.max_hp_pct) * A.body)
	var qi_base := pool_base("qi", lv, realm_key)
	var capacity := float(ProgressionRules.method(c.cultivator.method_id).get("capacity", 1.0))
	qi_base = qi_base * capacity * (1.0 + float(fx.essence.max_qi_pct) * A.essence)
	var soul_base = pool_base("soul", lv, realm_key) * (1.0 + float(fx.spirit.max_soul_pct) * A.spirit)
	sb.set_base("max_hp", hp_base)
	sb.set_base("max_qi", qi_base)
	sb.set_base("max_soul", soul_base)
	# Weapon family attack (S12): weapon attack × (1 + 0.8% first + 0.4% second) × enhancement.
	var weapon = c.inventory.equipped.get("weapon")
	var watk := 0.0
	if weapon == null or str(fam.get("id", "fists")) == "fists":
		watk = weapon_attack(maxf(1.0, lv)) * float(ContentDB.stat_const("equipment.fist_weapon_pct", 0.6))
	else:
		var wdef := ContentDB.item(weapon.id)
		watk = weapon_attack(float(weapon.get("ilv", wdef.get("ilv", 1)))) * instance_mult(weapon, energy)
	var scales: Array = fam.get("scales", ["body", "agility"])
	var fam_attack = watk * (1.0 + 0.008 * A.get(scales[0], 0) + 0.004 * A.get(scales[1] if scales.size() > 1 else scales[0], 0))
	sb.set_base("physical_attack", fam_attack)
	sb.set_base("qi_attack", fam_attack * (1.0 + float(fx.essence.qi_attack_pct) * A.essence) * (1.0 + float(fam.get("qi_attack_bonus", 0.0))))
	sb.set_base("soul_attack", fam_attack * (1.0 + float(fx.spirit.soul_attack_pct) * A.spirit))
	sb.set_base("accuracy", 10.0 + 2.0 * lv + float(fx.agility.accuracy) * A.agility + float(fx.insight.accuracy) * A.insight)
	sb.set_base("evasion", float(fx.agility.evasion) * A.agility)
	sb.set_base("crit_chance", float(ContentDB.stat_const("crit.base", 0.05)) + float(fx.agility.crit_chance) * A.agility
		+ float(fx.fortune.crit_chance) * A.fortune + float(fam.get("crit", 0.0)))
	sb.set_base("crit_damage", float(ContentDB.stat_const("crit.damage_base", 1.5)))
	sb.set_base("attack_speed", float(fx.agility.attack_speed) * A.agility)
	sb.set_base("penetration", float(fam.get("penetration", 0.0)))
	sb.set_base("physical_defense", float(fx.body.physical_defense) * A.body)
	sb.set_base("qi_resistance", float(fx.essence.qi_resistance) * A.essence)
	sb.set_base("soul_defense", float(fx.spirit.soul_defense) * A.spirit)
	sb.set_base("guard", float(fam.get("guard", 0.0)))
	sb.set_base("tenacity", float(fx.spirit.tenacity) * A.spirit)
	sb.set_base("will", float(fx.spirit.will) * A.spirit)
	var move_base := float(ContentDB.stat_const("move.base", 205))
	sb.set_base("move_speed", move_base * (1.0 + minf(float(ContentDB.stat_const("move.cap_pct", 0.4)), float(fx.agility.move_speed_pct) * A.agility)))
	sb.caps["move_speed"] = move_base * (1.0 + float(ContentDB.stat_const("move.cap_pct", 0.4)))
	sb.set_base("hp_regen", float(ContentDB.stat_const("regen_per_s.hp", 0.005)))
	sb.set_base("qi_regen", float(ContentDB.stat_const("regen_per_s.qi", 0.0075)) * (1.0 + float(fx.essence.qi_regen) * A.essence))
	sb.set_base("soul_regen", float(ContentDB.stat_const("regen_per_s.soul", 0.00375)))
	sb.set_base("toxicity_tolerance", float(ContentDB.stat_const("toxicity.tolerance_base", 30)) + float(fx.body.toxicity_tolerance) * A.body)
	sb.set_base("drop_rate", float(fx.fortune.drop_rate) * A.fortune)
	sb.set_base("coin_find", float(fx.fortune.coin_find) * A.fortune)
	sb.set_base("technique_cost", float(fx.essence.technique_cost) * A.essence)
	sb.set_base("insight_rate", float(fx.insight.insight_rate) * A.insight)
	sb.set_base("mastery_gain", float(fx.insight.mastery_gain) * A.insight)
	sb.set_base("crafting_control", float(fx.insight.crafting_control) * A.insight)
	sb.set_base("accumulation_rate", 0.0)
	sb.set_base("elemental_power", 0.0)
	sb.set_base("sense_radius", 300.0 * (1.0 + float(fx.spirit.sense_radius_pct) * A.spirit) if soul_base > 0 else 0.0)
	sb.set_base("hollow_ward", 0.0)
	sb.set_base("pressure", 0.0)
	for stat in ContentDB.stat_const("stats", []):
		if stat.get("cap") != null and not sb.caps.has(stat.id) and stat.id != "move_speed": sb.caps[stat.id] = float(stat.cap)
	sb.recalc()
	# A pool that does not exist yet cannot be created by gear or buffs.
	if qi_base <= 0.0: sb.finals["max_qi"] = 0.0
	if soul_base <= 0.0: sb.finals["max_soul"] = 0.0
	c.pools.set_max("hp", sb.value("max_hp"))
	c.pools.set_max("qi", sb.value("max_qi"))
	c.pools.set_max("soul", sb.value("max_soul"))
	var changed: Array = []
	for k in sb.finals:
		if not before.has(k) or absf(float(before[k]) - float(sb.finals[k])) > 0.0001: changed.append(k)
	return changed

static func attribute(c, attr: String) -> float:
	return c.stats.value(attr)

## S11 Combat Power.
static func combat_power(c) -> int:
	var sb: StatBlock = c.stats
	var fam := family(c)
	var cp_conf: Dictionary = ContentDB.stat_const("cp", {})
	var atk := sb.value("physical_attack")
	var aspd := float(fam.get("hits_per_s", 1.0)) * (1.0 + sb.value("attack_speed"))
	var crit := sb.value("crit_chance")
	var defences := sb.value("physical_defense") + sb.value("qi_resistance") + sb.value("soul_defense")
	var e := ProgressionRules.energy_multiplier(c.cultivator.energy_type, c.cultivator.purity)
	var cp := (sb.value("max_hp") / float(cp_conf.get("hp_div", 10)) + atk * aspd * (1.0 + crit * (sb.value("crit_damage") - 1.0)) * float(cp_conf.get("attack_weight", 0.5))
		+ defences / float(cp_conf.get("defence_div", 4))) * e
	return int(round(cp))

## Monster stat templates by Level and role (S13).
static func mob_stats(def: Dictionary, lv: int, elite := false) -> Dictionary:
	var mob: Dictionary = ContentDB.stat_const("mob", {})
	var role := "elite" if elite else str(def.get("role", "normal"))
	var r: Dictionary = mob.get("roles", {}).get(role, {"hp": 1, "attack": 1, "defence": 0.8})
	var hp := poly(mob.hp, lv) * float(r.hp) * float(def.get("hp_mult", 1.0))
	if def.has("hp_override"): hp = float(def.hp_override)
	var attack := poly(mob.attack, lv) * float(r.attack) * float(def.get("attack_mult", 1.0))
	var acc := poly(mob.accuracy, lv)
	var eva := acc * float(mob.get("agile_evasion_pct" if def.get("agile", false) else "evasion_pct", 0.3))
	var defence := armour_defence(lv) * float(r.defence)
	return {"max_hp": hp, "attack": attack, "accuracy": acc, "evasion": eva, "physical_defense": defence,
		"qi_resistance": defence * 0.6, "soul_defense": defence * 0.5, "crit_chance": 0.05, "crit_damage": 1.5,
		"tenacity": 0.3 if role in ["field_boss", "dungeon_boss", "story_boss"] else 0.0, "role": role}
