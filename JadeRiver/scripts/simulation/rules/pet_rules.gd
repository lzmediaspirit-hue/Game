class_name PetRules
extends RefCounted
## S46 · Pure spirit-animal rules: an arena combatant built from an animal's record, and the Beast Arena's
## auto-battle. Pure: the battle takes its RNG stream as an argument and changes nothing outside what it returns.

## A combatant: {name, species, hp, max_hp, atk, def, interval, skill_mult, free_cast}. `p` carries species, level,
## rarity and stage (and a name); `mults` are the animal's own multipliers (hp, attack, defence, speed), 1 for a tamer's.
static func combatant(p: Dictionary, cfg: Dictionary, mults: Dictionary = {}) -> Dictionary:
	var lv := int(p.get("level", 1))
	var rp := 1.0
	for r in ContentDB.config("pet_growth").get("rarities", []):
		if str(r.id) == str(p.get("rarity", "common")): rp = float(r.get("power", 1.0))
	var sb := float(cfg.get("stage_bonus", {}).get(str(p.get("stage", "juvenile")), 1.0))
	var hp := (float(cfg.get("hp_base", 60)) + float(cfg.get("hp_per_level", 12)) * lv) * rp * sb * float(mults.get("hp", 1.0))
	var atk := (float(cfg.get("atk_base", 8)) + float(cfg.get("atk_per_level", 2.2)) * lv) * rp * sb * float(mults.get("attack", 1.0))
	return {"name": str(p.get("name", ContentDB.name_of("pets", str(p.get("species", ""))))), "species": str(p.get("species", "")),
		"hp": hp, "max_hp": hp, "atk": atk, "def": maxf(0.5, float(mults.get("defence", 1.0))),
		"interval": float(cfg.get("interval", 1.6)) / maxf(0.5, float(mults.get("speed", 1.0))),
		"skill_mult": float(p.get("skill_mult", 1.0)), "free_cast": bool(p.get("free_cast", false))}

## Two teams fight until one falls or time runs out (then the side with more health left, as a share, wins). Each
## combatant strikes the first standing foe; an awakened skill lands every `skill_every` seconds; an Equal Contract's
## free cast is the opening blow. Returns {winner: "a"|"b", t, log: [{t, side, i, target, dmg, skill}], a, b}.
static func battle(team_a: Array, team_b: Array, cfg: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var sides := {"a": team_a.map(func(x): return (x as Dictionary).duplicate()), "b": team_b.map(func(x): return (x as Dictionary).duplicate())}
	for key in sides:
		for m in sides[key]:
			m.timer = float(m.interval) * 0.5
			m.skill_t = float(cfg.get("skill_every", 12.0))
	var step := float(cfg.get("step_s", 0.2))
	var t := 0.0
	var log: Array = []
	while t < float(cfg.get("max_s", 60.0)):
		t += step
		for key in ["a", "b"]:
			var foes: Array = sides["b" if key == "a" else "a"]
			for i in (sides[key] as Array).size():
				var m: Dictionary = sides[key][i]
				if float(m.hp) <= 0.0: continue
				m.timer = float(m.timer) - step
				m.skill_t = float(m.skill_t) - step
				if float(m.timer) > 0.0: continue
				m.timer = float(m.interval)
				var ti := _first_standing(foes)
				if ti < 0: break
				var mult := 1.0
				var skill := false
				if m.get("free_cast", false):
					mult = maxf(2.5, float(m.skill_mult))
					m.free_cast = false
					skill = true
				elif float(m.skill_mult) > 1.0 and float(m.skill_t) <= 0.0:
					mult = float(m.skill_mult)
					m.skill_t = float(cfg.get("skill_every", 12.0))
					skill = true
				var v := float(cfg.get("variance", 0.1))
				var dmg: float = float(m.atk) * mult * rng.randf_range(1.0 - v, 1.0 + v) / float(foes[ti].def)
				foes[ti].hp = maxf(0.0, float(foes[ti].hp) - dmg)
				log.append({"t": snappedf(t, 0.01), "side": key, "i": i, "target": ti, "dmg": snappedf(dmg, 0.1), "skill": skill})
			if _first_standing(foes) < 0:
				return {"winner": key, "t": t, "log": log, "a": sides.a, "b": sides.b}
	var share_a := _health_share(sides.a)
	var share_b := _health_share(sides.b)
	return {"winner": "a" if share_a >= share_b else "b", "t": t, "log": log, "a": sides.a, "b": sides.b}

static func _first_standing(team: Array) -> int:
	for i in team.size():
		if float(team[i].hp) > 0.0: return i
	return -1

static func _health_share(team: Array) -> float:
	var hp := 0.0
	var mx := 0.0
	for m in team:
		hp += float(m.hp)
		mx += float(m.max_hp)
	return hp / maxf(1.0, mx)
