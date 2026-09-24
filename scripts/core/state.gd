# Profile state, derived stats and versioned save migration. Pure data — no scene access.
class_name State
extends RefCounted

const C = preload("res://scripts/data/content.gd")

const HAIR_IDS = ["topknot", "windswept", "silver_tail", "plum_bob"]
const CLOTHES_IDS = ["river_traveler", "crimson_adept", "cloud_scholar", "jade_sentinel"]


static func new_profile(name: String, hair := "plum_bob", clothes := "river_traveler", weapon := "spear") -> Dictionary:
	var starter := "training_sword" if weapon == "sword" else "training_spear"
	var p := {
		"id": "d%08x" % (randi() & 0x7fffffff),
		"name": name.strip_edges().substr(0, 16) if name.strip_edges() != "" else "New Disciple",
		"look": {"hair": hair, "clothes": clothes},
		"starter_weapon": weapon,
		"level": 1, "xp": 0,
		"realm": 0, "insight": 0, "essence": 0,
		"hp": -1, "qi": -1,
		"meridians": [],
		"body": {"endurance": 0, "guard": 0, "mobility": 0},
		"soul": 0,
		"dao": null,
		"mastery": {"sword": 0, "spear": 0},
		"cls": null,
		"abilities": {"known": ["step"], "slots": [null, null, null]},
		"prof": {"mining": 0, "herbalism": 0, "fishing": 0, "smithing": 0, "alchemy": 0},
		"items": {starter: 1},
		"coins": 20,
		"equip": {"weapon": starter, "hat": null, "gourd": null},
		"quests": {},
		"flags": {},
		"bosses": {},
		"stats": {"kills": {}, "crafted": {}, "gathered": {}},
		"discovered": {"areas": {"jr_town": true, "outskirts": true}, "nodes": {}},
		"research": {},
		"commissions": {"day": "", "counts": {}, "active": {}},
		"tracked": null,
		"area": "jr_town", "x": 200.0, "depth": 40.0,
		"assignment": null,
		"quickslots": ["mend_pill", "qi_pill"],
		"created": int(Time.get_unix_time_from_system()),
	}
	for ch in C.CHAPTERS:
		p.quests[ch.id] = {"state": "unoffered", "step": 0, "base": 0}
	p.quests["ch1"].state = "active"
	var s := stats(p)
	p.hp = s.max_hp
	p.qi = s.max_qi
	return p


static func new_save() -> Dictionary:
	return {"version": C.SAVE_VERSION, "slots": [null, null, null], "bank": {}, "settings": default_settings(), "last_slot": 0}


static func default_settings() -> Dictionary:
	return {"text_scale": 1.0, "left_handed": false, "show_stick": true, "button_scale": 1.0, "reduce_fx": false, "sound": true}


static func mastery_rank(p: Dictionary, family: String) -> int:
	return int(p.mastery.get(family, 0)) / 20


static func prof_level(xp: int) -> int:
	var lv := 1
	while lv < C.PROF_XP.size() - 1 and xp >= C.PROF_XP[lv + 1]:
		lv += 1
	return lv


static func prof_lv(p: Dictionary, prof: String) -> int:
	return prof_level(int(p.prof.get(prof, 0)))


static func xp_to_next(level: int) -> int:
	return int(round(55.0 * pow(level, 1.45)))


static func meridian_cap(realm: int) -> int:
	return mini(6, (realm + 1) * 2)


static func stats(p: Dictionary) -> Dictionary:
	var w: Dictionary = C.ITEMS.get(p.equip.weapon, {})
	var cls: Dictionary = C.CLASSES[p.cls].bonus if p.cls != null else {}
	var level: int = p.level
	var realm: int = p.realm
	var hp: int = 100 + (level - 1) * 8 + realm * C.REALM_BONUS.hp + int(p.body.endurance) * 10 + int(cls.get("hp", 0))
	var qi: int = 50 + realm * C.REALM_BONUS.qi + int(cls.get("qi", 0))
	var atk: int = 10 + (level - 1) * 2 + realm * C.REALM_BONUS.atk + int(w.get("atk", 0))
	var def: int = 5 + (level - 1)
	for id in p.meridians:
		for m in C.MERIDIANS:
			if m.id == id:
				hp += int(m.bonus.get("hp", 0))
				qi += int(m.bonus.get("qi", 0))
				atk += int(m.bonus.get("atk", 0))
				def += int(m.bonus.get("def", 0))
	var fam: String = w.get("family", "spear")
	return {
		"max_hp": hp, "max_qi": qi, "atk": atk, "def": def,
		"family": fam,
		"reach": 30.0 if fam == "sword" else 42.0,
		"guard": 0.6 + int(p.body.guard) * 0.08,
		"speed": 1.0 + int(p.body.mobility) * 0.04,
		"step_cd": 1.0 - int(p.body.mobility) * 0.08,
		"art_cost": 1.0 - float(cls.get("artCost", 0.0)),
		"dmg_mul": 1.0 + float(cls.get("swordDmg" if fam == "sword" else "spearDmg", 0.0)),
		"atk_speed": 1.0 + float(cls.get("atkSpeed", 0.0)),
	}


static func realm_name(p: Dictionary) -> String:
	return C.REALMS[p.realm].name


static func cap(s: String) -> String:
	return s.substr(0, 1).to_upper() + s.substr(1) if s != "" else s


# Requirement list shared by Skills page, hotbar and (later) a server.
static func ability_reqs(p: Dictionary, id: String) -> Array:
	var a: Dictionary = C.ABILITIES[id]
	var r: Dictionary = a.get("req", {})
	var out := []
	if r.has("mastery"):
		var have := int(p.mastery.get(a.family, 0))
		out.append({"label": "%s Mastery %d" % [cap(a.family), r.mastery], "have": have, "need": r.mastery, "ok": have >= r.mastery, "icon": a.family})
	if r.has("parent"):
		var k: bool = p.abilities.known.has(r.parent)
		out.append({"label": "Learn " + C.ABILITIES[r.parent].name, "have": 1 if k else 0, "need": 1, "ok": k, "icon": "scroll"})
	if r.has("cls"):
		var ok: bool = p.cls == r.cls
		out.append({"label": C.CLASSES[r.cls].name, "have": 1 if ok else 0, "need": 1, "ok": ok, "icon": "class"})
	if r.has("realm"):
		var ok2: bool = int(p.realm) >= int(r.realm)
		out.append({"label": C.REALMS[r.realm].name + " Realm", "have": 1 if ok2 else 0, "need": 1, "ok": ok2, "icon": "realm"})
	return out


static func can_learn(p: Dictionary, id: String) -> bool:
	for r in ability_reqs(p, id):
		if not r.ok:
			return false
	return true


# ---------------------------------------------------------------- migration
# Legacy 0.7 offline saves (v1–v3) keep realm, insight, items, mastery, quests and bank.
# Never relabel insight as essence; never demote; never duplicate starter supplies.
# Returns {save, migrated, future, error}
static func migrate(raw) -> Dictionary:
	if typeof(raw) != TYPE_DICTIONARY:
		return {"save": new_save(), "migrated": false}
	var v := int(raw.get("version", 0))
	if v > C.SAVE_VERSION:
		return {"future": true}
	var s: Dictionary = raw.duplicate(true)
	if v <= 1:
		s = _v1_to_v2(s)
	if v <= 2:
		s = _v2_to_v3(s)
	if v <= 3:
		s = _v3_to_v4(s)
	if not validate(s):
		return {"error": true}
	return {"save": s, "migrated": v != C.SAVE_VERSION}


static func _v1_to_v2(s: Dictionary) -> Dictionary:
	if s.has("character"):
		return {"version": 2, "characters": [s.character, null, null], "shared_storage": s.get("storage", {})}
	s.version = 2
	return s


static func _v2_to_v3(s: Dictionary) -> Dictionary:
	var chars := []
	for c in s.get("characters", []):
		if c is Dictionary:
			if not c.has("meridians"):
				c.meridians = 0
		chars.append(c)
	while chars.size() < 3:
		chars.append(null)
	return {"version": 3, "characters": chars.slice(0, 3), "shared_storage": s.get("shared_storage", {})}


static func _v3_to_v4(s: Dictionary) -> Dictionary:
	var out := new_save()
	out.bank = s.get("shared_storage", {}).duplicate(true)
	var slots := []
	for c in s.get("characters", []).slice(0, 3):
		slots.append(_legacy_char(c) if c is Dictionary else null)
	while slots.size() < 3:
		slots.append(null)
	out.slots = slots
	return out


static func _legacy_char(c: Dictionary) -> Dictionary:
	var weapon: String = C.ITEMS[c.weapon].family if c.has("weapon") and C.ITEMS.has(c.weapon) else str(c.get("starter", "spear"))
	var p := new_profile(str(c.get("name", "Disciple")), str(c.get("hair", "plum_bob")), str(c.get("outfit", "river_traveler")), weapon)
	p.level = maxi(1, int(c.get("level", 1)))
	p.xp = int(c.get("xp", 0))
	p.realm = clampi(int(c.get("realm_index", 0)), 0, C.REALMS.size() - 1)
	p.insight = maxi(0, int(c.get("cultivation", 0)))  # h.cultivation is insight
	var m: Dictionary = c.get("mastery", {})
	p.mastery = {"sword": int(m.get("sword", 0)), "spear": int(m.get("spear", 0))}
	p.items = {}
	for id in c.get("inventory", {}):
		var n := int(c.inventory[id])
		if C.ITEMS.has(id) and n > 0:
			p.items[id] = n
	if c.has("weapon") and C.ITEMS.has(c.weapon):
		p.items[c.weapon] = maxi(1, int(p.items.get(c.weapon, 0)))
		p.equip.weapon = c.weapon
	else:
		var st := "training_sword" if weapon == "sword" else "training_spear"
		p.items[st] = maxi(1, int(p.items.get(st, 0)))
		p.equip.weapon = st
	for slot in ["hat", "gourd"]:
		if c.has(slot) and C.ITEMS.has(c[slot]):
			p.equip[slot] = c[slot]
			p.items[c[slot]] = maxi(1, int(p.items.get(c[slot], 0)))
	p.coins = maxi(0, int(c.get("coins", 0)))
	for k in c.get("professions", {}):
		p.prof[k] = int(c.professions[k])
	p.meridians = []
	for i in mini(6, int(c.get("meridians", 0))):
		p.meridians.append(C.MERIDIANS[i].id)
	var done := clampi(int(c.get("chapter", 0)), 0, 3)
	for i in C.CHAPTERS.size():
		var ch: Dictionary = C.CHAPTERS[i]
		if i < done:
			p.quests[ch.id] = {"state": "complete", "step": ch.steps.size(), "base": 0}
			p.flags[ch.reward.flag] = true
		elif i == done:
			p.quests[ch.id] = {"state": "active", "step": 0, "base": 0}
		else:
			p.quests[ch.id] = {"state": "unoffered", "step": 0, "base": 0}
	if done >= 1:
		p.bosses["captain"] = true
		p.discovered.areas["lantern"] = true
		p.discovered.areas["bamboo"] = true
		for t in ["pick", "kit", "rod"]:
			p.items[t] = maxi(1, int(p.items.get(t, 0)))
	if done >= 2:
		p.bosses["sentinel"] = true
		p.discovered.areas["cloudrest"] = true
		p.discovered.areas["monastery"] = true
	if done >= 3:
		p.bosses["qiu"] = true
	# Grant technique credit for owned higher-grade weapons (never revoke gear).
	for id in p.items:
		var d: Dictionary = C.ITEMS[id]
		if d.kind == "weapon" and int(d.get("rank", 0)) > 0:
			p.mastery[d.family] = maxi(int(p.mastery[d.family]), int(d.rank) * 20)
	var s := stats(p)
	p.hp = s.max_hp
	p.qi = s.max_qi
	p.migrated_from = 3
	return p


static func validate(s: Dictionary) -> bool:
	if not (s.get("slots") is Array) or s.slots.size() != 3:
		return false
	if not s.has("bank"):
		s.bank = {}
	var st := default_settings()
	st.merge(s.get("settings", {}), true)
	s.settings = st
	for p in s.slots:
		if not (p is Dictionary):
			continue
		for id in p.items.keys():
			if not C.ITEMS.has(id) or int(p.items[id]) <= 0:
				p.items.erase(id)
			else:
				p.items[id] = int(p.items[id])
		if not p.items.has(p.equip.weapon):
			var stw := "training_sword" if p.get("starter_weapon", "spear") == "sword" else "training_spear"
			p.items[stw] = maxi(1, int(p.items.get(stw, 0)))
			p.equip.weapon = stw
		for ch in C.CHAPTERS:
			if not p.quests.has(ch.id):
				p.quests[ch.id] = {"state": "unoffered", "step": 0, "base": 0}
		_fix_ints(p)
	return true


# JSON round-trips turn ints into floats; restore the integer fields we index or compare.
static func _fix_ints(p: Dictionary) -> void:
	for k in ["level", "xp", "realm", "insight", "essence", "coins", "soul", "hp", "qi"]:
		if p.has(k):
			p[k] = int(p[k])
	for d in [p.items, p.mastery, p.prof, p.body, p.stats.kills, p.stats.crafted, p.stats.gathered, p.commissions.counts, p.commissions.active]:
		for k in d:
			d[k] = int(d[k])
	for q in p.quests.values():
		q.step = int(q.step)
		q.base = int(q.base)
	if p.dao is Dictionary:
		p.dao.xp = int(p.dao.xp)
	if p.assignment is Dictionary:
		p.assignment.start = int(p.assignment.start)
