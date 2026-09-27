extends Node
## Read-only stat-scaling probe (docs/research/stat_scaling_research.md). It loads COPIES of the valley_run
## checkpoints (user://valley_cp/<section>, the progressed "Tester" in slot 1; never the Max Tester) and a fresh
## character, and reports what the rules give today: pools, attacks, Combat Power, damage per hit and per second
## against the level's own monsters, the monsters' blows against the character, and the formula curves to Level 166.
## Nothing under res:// or user://valley_cp is written; the copies live in user://stat_probe_work/.
## Run headless (after valley_run has written its checkpoints):
##   godot --headless --path . res://tools/dev/stat_probe.tscn -- [--out=/abs/path/probe.json]

const CP_ROOT := "user://valley_cp/"
const WORK := "user://stat_probe_work/"
const SECTIONS := ["bf2", "bf5", "bf8", "qk1", "qk5", "qu1", "qu5", "ht1", "ht5", "cs1", "cs5", "sa1", "sa5", "hg1", "ae1",
	"ae3", "ae5", "ae_end", "ls2_end", "ls4_end", "ls6_end"]
const ROLLS := 4000

var out := {"characters": [], "curve": [], "bosses": []}

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var path := ""
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--out="): path = str(a).trim_prefix("--out=")
	_fresh()
	for s in SECTIONS:
		if _load(s):
			_measure(s, Game.active())
			if s == SECTIONS[SECTIONS.size() - 1]: _ceiling(Game.active())
	_curve()
	_bosses()
	if path != "":
		var f := FileAccess.open(path, FileAccess.WRITE)
		if f != null: f.store_string(JSON.stringify(out, "  "))
	print("stat_probe: %d characters measured" % (out.characters as Array).size())
	get_tree().quit(0)

# ------------------------------------------------------------------ loading (copies only)
func _clear(folder: String) -> void:
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)

func _load(section: String) -> bool:
	var from := CP_ROOT + section + "/"
	if not DirAccess.dir_exists_absolute(from):
		print("no checkpoint ", section)
		return false
	_clear(WORK)
	for f in DirAccess.get_files_at(from): DirAccess.copy_absolute(from + f, WORK + f)
	Clock.debug_offset_s = 0.0
	if FileAccess.file_exists(CP_ROOT + section + ".clock"):
		Clock.debug_offset_s = float(FileAccess.get_file_as_string(CP_ROOT + section + ".clock"))
	# Pin the clock to the moment the checkpoint was saved, so no offline time is claimed and timed buffs and the
	# calendar stand as they were.
	var acc = JSON.parse_string(FileAccess.get_file_as_string(WORK + "account.json"))
	var saved := float(acc.get("clock", {}).get("last_active_utc", -1.0)) if acc is Dictionary else -1.0
	Clock.override_utc = saved - Clock.debug_offset_s if saved > 0.0 else -1.0
	Saves.use_folder(WORK)
	Game.boot()
	Game.autosave_enabled = false
	if not Game.submit({"type": "enter_character", "slot": 1}).get("ok", false): return false
	Game.submit({"type": "enter_world"})
	return Game.active() != null and str(Game.active().name) != "Max Tester"

## A new character with nothing on it, measured at Mortal (Level 0) and, with only its realm moved, Bone Forging 1.
func _fresh() -> void:
	_clear(WORK)
	Saves.use_folder(WORK)
	Clock.override_utc = 1767225600.0
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 2026
	Rng.restore("account", {}, 2026)
	Game.submit({"type": "create_character", "slot": 1, "name": "Probe", "appearance": {"hair": "topknot"}})
	Game.submit({"type": "enter_character", "slot": 1})
	var c = Game.active()
	_measure("new (Mortal)", c)
	c.cultivator.realm_key = "bone_forging_1"
	StatRules.rebuild(c)
	_measure("new, set to Bone Forging 1", c)
	Clock.override_utc = -1.0   # the checkpoints run on the real clock plus their saved offset, as valley_run resumes them

# ------------------------------------------------------------------ measuring
func _enemy_view(def: Dictionary, lv: int) -> Dictionary:
	return CombatRules.foe(StatRules.mob_stats(def, lv), lv, str(def.get("element", "none")))

## The normal foes whose Level band holds `lv` (the ones a character of that Level fights), or a generic one.
func _foes_at(lv: int) -> Array:
	var foes: Array = []
	for e in ContentDB.all("enemies"):
		var r: Array = e.get("level", [0, 0])
		if str(e.get("role", "")) == "normal" and not e.get("passive", false) and lv >= int(r[0]) and lv <= int(r[r.size() - 1]):
			foes.append(e)
	if foes.is_empty(): foes.append({"id": "generic", "role": "normal", "element": "wood"})
	return foes

func _avg_hit(att: Dictionary, def: Dictionary, attack: Dictionary, seed: int) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var total := 0.0
	var landed := 0
	var crits := 0
	var top := 0
	for i in ROLLS:
		var r := CombatRules.resolve(att, def, attack, rng)
		if r.miss: continue
		landed += 1
		total += float(r.amount)
		top = maxi(top, int(r.amount))
		if r.crit: crits += 1
	return {"per_swing": total / float(ROLLS), "per_hit": total / maxf(1.0, float(landed)), "hit_rate": float(landed) / float(ROLLS),
		"crit_rate": float(crits) / maxf(1.0, float(landed)), "max": top}

func _best_technique(c) -> Dictionary:
	var best := {}
	var best_v := 0.0
	var fam := str(StatRules.family(c).get("id", "fists"))
	for tid in c.cultivator.technique_slots:
		if tid == null or str(tid) == "": continue
		var t := ContentDB.entry("techniques", str(tid))
		if not str(t.get("damage_type", "")) in ["physical", "qi", "soul"]: continue
		var tf := str(t.get("family", "any"))
		if tf != "any" and tf != fam and not (tf == "fists" and fam == "gauntlets"): continue
		var m: Array = t.get("mult", [1, 1])
		var v := (float(m[0]) + float(m[1])) * 0.5 * maxi(1, int(t.get("hits", 1)))
		if v > best_v:
			best_v = v
			best = t
	return best

func _measure(label: String, c) -> void:
	var lv := ProgressionRules.level(c)
	var sb: StatBlock = c.stats
	var fam := StatRules.family(c)
	var pv: Dictionary = Game.combat.player_view(c)
	pv.x = 0.0
	var dealt := float(Game.combat.attune.get(c.id, {}).get("dealt", 1.0))
	var foes := _foes_at(lv)
	var steps: Array = fam.get("combo", [{"mult": 1.0, "duration": 0.5}])
	var mult_sum := 0.0
	var dur_sum := 0.0
	for st in steps:
		mult_sum += float(st.get("mult", 1.0))
		dur_sum += float(st.get("duration", 0.5))
	var combo_mult := mult_sum / float(steps.size())
	var swings_per_s := float(steps.size()) / maxf(0.1, dur_sum)
	var basic := {"damage_type": str(fam.get("damage_type", "physical")), "element": "none", "mult": [combo_mult, combo_mult],
		"range": fam.get("range", [0.9, 1.1]), "dao_tier": ProgressionRules.effective_dao_tier(c, str(fam.get("dao", ""))), "situation": 1.0,
		"attunement": dealt}
	var tech := _best_technique(c)
	var tech_attack := {}
	if not tech.is_empty():
		var gm := 1.0 + ProgressionRules.technique_grade_bonus(tech)
		var tm: Array = tech.get("mult", [1, 1])
		var mt := int(c.cultivator.mastery.get(str(tech.id), {"tier": 1}).get("tier", 1))
		tech_attack = {"damage_type": str(tech.get("damage_type", "physical")), "element": str(tech.get("element", "none")),
			"mult": [float(tm[0]) * gm, float(tm[1]) * gm], "range": fam.get("range", [0.9, 1.1]),
			"dao_tier": ProgressionRules.effective_dao_tier(c, str(tech.get("dao", ""))), "mastery_tier": mt - 1, "attunement": dealt}
	var rows: Array = []
	var hp_sum := 0.0
	var hit_sum := 0.0
	var swing_sum := 0.0
	var tech_sum := 0.0
	var taken_sum := 0.0
	var basic_max := 0
	var tech_max := 0
	var nc := pv.duplicate()   # the same blows with crits taken out: the par table's "before crits"
	nc.crit_chance = -10.0
	var basic_nc := 0.0
	var tech_nc := 0.0
	for i in foes.size():
		var ev := _enemy_view(foes[i], lv)
		var b := _avg_hit(pv, ev, basic, 1000 + i)
		var t := _avg_hit(pv, ev, tech_attack, 2000 + i) if not tech_attack.is_empty() else {"per_hit": 0.0}
		basic_nc += float(_avg_hit(nc, ev, basic, 1000 + i).per_hit)
		if not tech_attack.is_empty(): tech_nc += float(_avg_hit(nc, ev, tech_attack, 2000 + i).per_hit)
		var m := _avg_hit(ev, pv, {"damage_type": "physical", "element": str(foes[i].get("element", "none")), "mult": [1.0, 1.0]}, 3000 + i)
		hp_sum += float(ev.max_hp)
		hit_sum += float(b.per_hit)
		swing_sum += float(b.per_swing)
		tech_sum += float(t.per_hit)
		taken_sum += float(m.per_hit)
		basic_max = maxi(basic_max, int(b.max))
		tech_max = maxi(tech_max, int(t.get("max", 0)))
		rows.append({"foe": str(foes[i].get("id", "")), "hp": int(ev.max_hp), "basic_hit": int(b.per_hit), "hit_rate": snappedf(float(b.hit_rate), 0.01)})
	var n := float(foes.size())
	var mob_hp := hp_sum / n
	var aspd := 1.0 + sb.value("attack_speed")
	var dps := swing_sum / n * swings_per_s * aspd
	var weapon = c.inventory.equipped.get("weapon")
	var rec := {
		"label": label, "name": str(c.name), "realm": str(c.cultivator.realm_key), "level": lv, "energy": str(c.cultivator.energy_type),
		"might": snappedf(StatRules.might(c), 0.001),
		"qi_edge": snappedf(ProgressionRules.qi_edge(c.cultivator.energy_type, c.cultivator.purity), 0.001),
		"weapon": str(weapon.id) if weapon != null else "fists",
		"weapon_ilv": int(weapon.get("ilv", ContentDB.item(str(weapon.id)).get("ilv", 0))) if weapon != null else 0,
		"weapon_quality": str(weapon.get("quality", "")) if weapon != null else "",
		"weapon_enhance": int(weapon.get("enhance", 0)) if weapon != null else 0,
		"max_hp": int(sb.value("max_hp")), "max_qi": int(sb.value("max_qi")), "max_soul": int(sb.value("max_soul")),
		"physical_attack": int(sb.value("physical_attack")), "qi_attack": int(sb.value("qi_attack")), "soul_attack": int(sb.value("soul_attack")),
		"physical_defense": int(sb.value("physical_defense")), "crit_chance": snappedf(sb.value("crit_chance"), 0.001),
		"crit_damage": snappedf(sb.value("crit_damage"), 0.001), "attack_speed": snappedf(sb.value("attack_speed"), 0.001),
		"body": int(sb.value("body")), "agility": int(sb.value("agility")), "essence": int(sb.value("essence")),
		"cp": StatRules.combat_power(c), "attunement_dealt": dealt,
		"foes": rows, "mob_hp": int(mob_hp), "basic_hit": int(hit_sum / n), "basic_dps": int(dps),
		"technique": str(tech.get("id", "")), "technique_hit": int(tech_sum / n), "basic_max": basic_max, "technique_max": tech_max,
		"basic_nocrit": int(basic_nc / n), "technique_nocrit": int(tech_nc / n),
		"technique_crit": int(tech_nc / n * clampf(sb.value("crit_damage"), 1.0, float(ContentDB.stat_const("crit.damage_cap", 3.0)))),
		"ttk_s": snappedf(mob_hp / maxf(1.0, dps), 0.01), "hits_to_kill": ceili(mob_hp / maxf(1.0, hit_sum / n)),
		"mob_blow": int(taken_sum / n), "mob_blow_pct": snappedf(taken_sum / n / maxf(1.0, sb.value("max_hp")), 0.001),
		"blows_to_fall": ceili(sb.value("max_hp") / maxf(1.0, taken_sum / n)),
		"recommended_cp": _recommended_cp(lv)}
	var crit_sources := {}
	for mm in sb.modifiers:
		if str(mm.get("stat", "")) == "crit_chance": crit_sources[str(mm.get("source", ""))] = float(mm.get("value", 0.0))
	rec["crit_sources"] = crit_sources
	out.characters.append(rec)
	print("%-28s Lv%3d %-20s HP %7d  atk %6d/%6d  crit %.2f x%.2f  M %.2f Q %.2f  CP %6d (rec %5d)  hit %7d (%7d)  tech %7d (%7d, crit %7d; %s)  dps %7d  mobHP %8d  TTK %5.2fs  blow %5.1f%%" % [
		label, lv, rec.realm, rec.max_hp, rec.physical_attack, rec.qi_attack, rec.crit_chance, rec.crit_damage, rec.might, rec.qi_edge, rec.cp,
		rec.recommended_cp, rec.basic_hit, rec.basic_nocrit, rec.technique_hit, rec.technique_nocrit, rec.technique_crit, rec.technique, rec.basic_dps,
		rec.mob_hp, rec.ttk_s, 100.0 * rec.mob_blow_pct])

## The same Level 98 character with the best its road offers under today's rules (in memory only): every piece Perfect
## and +10, the weapon's three affixes at their tops, Glimpse of Heaven slotted at mastery tier 6, the Sword Dao at 6.
func _ceiling(c) -> void:
	for slot in c.inventory.equipped:
		var inst = c.inventory.equipped[slot]
		if inst == null: continue
		inst["quality"] = "perfect"
		inst["enhance"] = 10
		if slot == "weapon":
			inst["affixes"] = [{"id": "attack_pct", "stat": "physical_attack", "op": "pct_add", "value": 0.08},
				{"id": "crit", "stat": "crit_chance", "op": "flat", "value": 0.03}, {"id": "crit_damage", "stat": "crit_damage", "op": "flat", "value": 0.15}]
	c.cultivator.daos["sword"] = {"insight": 12000.0, "tier": 6}
	c.cultivator.technique_slots[0] = "glimpse_of_heaven"
	c.cultivator.mastery["glimpse_of_heaven"] = {"points": 0.0, "tier": 6}
	StatRules.rebuild(c)
	_measure("ceiling (ls6_end, best road)", c)

func _recommended_cp(lv: int) -> int:
	var best := 0
	var gap := 999
	for id in ContentDB.rooms:
		var r: Dictionary = ContentDB.rooms[id]
		var lr: Array = r.get("level_range", [0, 0])
		if int(r.get("recommended_cp", 0)) <= 0 or lr.size() < 2: continue
		var d := absi(int((int(lr[0]) + int(lr[1])) / 2) - lv)
		if d < gap:
			gap = d
			best = int(r.recommended_cp)
	return best

# ------------------------------------------------------------------ the formulas alone, Level 0 to 166
func _curve() -> void:
	for lv in range(0, 201):
		var key := ContentDB.realm_key_for_level(lv)
		var normal := StatRules.mob_stats({"role": "normal"}, lv)
		var par := StatRules.par(lv)
		out.curve.append({"level": lv, "realm": key, "might": StatRules.might_at(lv),
			"qi_edge": snappedf(ProgressionRules.qi_edge(str(ContentDB.realm(key).get("energy", "none")), 9), 0.01),
			"mob_hp": int(normal.max_hp), "mob_attack": int(normal.attack), "elite_hp": int(StatRules.mob_stats({"role": "normal"}, lv, true).max_hp),
			"weapon_attack": int(StatRules.weapon_attack(maxf(1.0, lv))), "hp_pool_base": int(StatRules.pool_base("hp", lv, key)),
			"mob_defence_cut": snappedf(CombatRules.defence_reduction(float(normal.physical_defense), lv, 0.0, StatRules.might_at(lv)), 0.001),
			"par_basic": int(par.get("basic", 0)), "par_technique": int(par.get("technique", 0)), "par_hp": int(par.get("max_hp", 0)),
			"par_dps": int(par.get("dps", 0)), "par_cp": int(par.get("cp", 0))})

func _bosses() -> void:
	for e in ContentDB.all("enemies"):
		if not str(e.get("role", "")) in ["field_boss", "dungeon_boss", "story_boss"]: continue
		var lv := int((e.get("level", [0]) as Array)[0])
		var s := StatRules.mob_stats(e, lv)
		out.bosses.append({"id": str(e.id), "role": str(e.role), "level": lv, "hp": int(s.max_hp), "attack": int(s.attack)})
