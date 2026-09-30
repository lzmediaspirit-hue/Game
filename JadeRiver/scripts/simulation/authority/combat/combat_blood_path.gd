class_name CombatBloodPath
extends CombatPart
## CombatAuthority's part for the Blood path (S48): lifesteal while walking it, and the blood-essence meter that kills
## fill and Blood arts spend. State: `combat.blood_essence` (transient, not saved).

func _blood_cfg() -> Dictionary:
	return ContentDB.stat_const("paths", {}).get("blood", {})

## Lifesteal while walking the Blood path: 3% of the damage dealt, +1% a Blood Dao tier; Blood arts drink twice that.
func blood_lifesteal(c) -> float:
	if not ProgressionAuthority.walks(c, "blood"): return 0.0
	var cfg := _blood_cfg()
	return float(cfg.get("lifesteal_base", 0.03)) + float(cfg.get("lifesteal_per_tier", 0.01)) * combat._dao_tier(c, "blood")

func lifesteal(c, amount: float, attack: Dictionary) -> void:
	var ls := blood_lifesteal(c)
	if ls <= 0.0 or amount <= 0.0 or c.pools.hp >= c.pools.max_hp: return
	var tid := str(attack.get("technique", ""))
	if tid != "" and bool(ContentDB.entry("techniques", tid).get("blood_path", false)): ls *= float(_blood_cfg().get("blood_art_lifesteal_mult", 2.0))
	combat.apply_resource_change(c.id, "hp", amount * ls, "lifesteal", 0.0, true)

func essence_of(actor_id: String) -> float:
	return float(combat.blood_essence.get(actor_id, {}).get("v", 0.0))

func spend_essence(actor_id: String, amount: float) -> void:
	if not combat.blood_essence.has(actor_id): return
	combat.blood_essence[actor_id].v = maxf(0.0, float(combat.blood_essence[actor_id].v) - amount)

## Kills fill the blood-essence meter of one who walks the Blood path: 10 a foe, 25 an elite, 50 a boss (to 100).
func feed_blood_essence(p: Dictionary) -> void:
	if str(p.get("victim_kind", "")) != "enemy": return
	var c = game.character(str(p.get("killer", "")))
	if c == null or not ProgressionAuthority.walks(c, "blood"): return
	var cfg := _blood_cfg()
	var def := ContentDB.entry("enemies", str(p.get("def", "")))
	var gain := float(cfg.get("essence_kill", 10))
	if str(p.get("role", def.get("role", ""))) == "boss": gain = float(cfg.get("essence_boss", 50))
	elif bool(p.get("elite", false)): gain = float(cfg.get("essence_elite", 25))
	var be: Dictionary = combat.blood_essence.get(c.id, {"v": 0.0, "t": 0.0})
	be.v = minf(float(cfg.get("essence_max", 100)), float(be.v) + gain)
	be.t = game.sim_time
	combat.blood_essence[c.id] = be

func tick_blood(c, delta: float) -> void:
	var be: Dictionary = combat.blood_essence.get(c.id, {})
	if be.is_empty(): return
	if not ProgressionAuthority.walks(c, "blood"):
		combat.blood_essence.erase(c.id)
		return
	var cfg := _blood_cfg()
	if game.sim_time - float(be.t) > float(cfg.get("essence_decay_after_s", 20.0)):
		be.v = maxf(0.0, float(be.v) - float(cfg.get("essence_decay_per_s", 2.0)) * delta)
