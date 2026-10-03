class_name ProgressionInsight
extends ProgressionPart
## ProgressionAuthority's part: insight into the Daos and their tiers, a rare Dao opened by a teacher, epiphany (S48),
## the Nine-Bough Jade Tree, and the insight sites' chess problems (S49).

# ------------------------------------------------------------------ insight and the Daos
func apply_insight(actor_id: String, dao: String, amount: float, context: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("daos", dao): return
	if not Unlocks.is_unlocked(c.id, "dao_tree") and not context.begins_with("kill") and not Unlocks.is_unlocked(c.id, "weapon_dao"): return
	# A teacher's lesson is measured out exactly (apply_open_dao); everything else is damped when repeated and
	# goes through the insight rate.
	if not context.begins_with("teacher:"):
		var mem: Dictionary = c.cultivator.insight_memory
		var window := float(ContentDB.curve("insight_repeat_window_s", 60))
		var key := context.get_slice(":", 0) + ":" + context.get_slice(":", 1) + ":" + context.get_slice(":", 2)
		if mem.has(key) and game.sim_time - float(mem[key]) < window: amount *= float(ContentDB.curve("insight_repeat_factor", 0.2))
		mem[key] = game.sim_time
		if mem.size() > 64: mem.clear()
		amount *= 1.0 + c.stats.value("insight_rate") + game.relations.insight_share(c)   # S49: a Dao Companion beside you
		# S48 Dao Echo: the chosen Dao learns faster and every other Dao slower.
		for rec in c.cultivator.fates:
			if rec.has("dao") and str(rec.dao) != "": amount *= 1.2 if str(rec.dao) == dao else 0.9
	# A rare Dao grows only after a teacher has opened it (apply_open_dao).
	if str(ContentDB.entry("daos", dao).get("family", "")) == "rare" and not c.cultivator.daos.has(dao): return
	var d: Dictionary = c.cultivator.daos.get(dao, {"tier": 0, "insight": 0.0})
	d.insight = float(d.insight) + amount
	# A Dao deepens as far as the land's Laws allow: its valley cap, or the cap of the zone you stand in.
	var ddef := ContentDB.entry("daos", dao)
	var zone_id := str(ContentDB.room_zone.get(str(c.position.get("room", "")), ""))
	var cap := maxi(int(ddef.get("valley_cap", 6)), int(ddef.get("zone_caps", {}).get(zone_id, 0)))
	var tier := mini(ProgressionRules.dao_tier_for(float(d.insight)), cap)
	var gained := tier > int(d.tier)
	d.tier = maxi(int(d.tier), tier)
	c.cultivator.daos[dao] = d
	if context != "epiphany": roll_epiphany(c, context)
	emit("insight_gained", {"actor": c.id, "dao": dao, "amount": amount})
	if gained:
		emit("dao_tier_up", {"actor": c.id, "dao": dao, "tier": d.tier})
		# A tier can teach a technique (S47: Sword Dao tier 3 teaches Sword Release).
		var effects: Array = ddef.get("effects", [])
		for ti in mini(int(d.tier), effects.size()):
			if effects[ti] is Dictionary and effects[ti].has("learn_technique"): progression.apply_learn_technique(c.id, str(effects[ti].learn_technique))

## A teacher of the Expanse opens a rare Dao: the first tier's insight comes with the lesson.
func apply_open_dao(actor_id: String, dao: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("daos", dao) or c.cultivator.daos.has(dao): return
	c.cultivator.daos[dao] = {"tier": 0, "insight": 0.0}
	var first: Array = ContentDB.curve("dao_tiers", [100])
	# A teacher opens the Dao at tier 1: exactly the first tier's insight, untouched by the insight rate or a
	# Dao Echo fate (S48), with a hair's margin.
	apply_insight(actor_id, dao, float(first[0]) + 0.01, "teacher:" + dao)

# ------------------------------------------------------------------ epiphany (S48)
## Epiphany: a rare flash while insight comes in from Contemplate or a fight. Five times the insight for a minute,
## sometimes a free step of mastery; then two hours of play before the next.
func roll_epiphany(c, context: String) -> void:
	var cu: CultivatorState = c.cultivator
	var k: Dictionary = ContentDB.stat_const("epiphany", {})
	if cu.epiphany_cooldown > 0.0 or not context.get_slice(":", 0) in k.get("contexts", []): return
	var rng := Rng.stream(c.id, "fortune")
	var chance: float = float(k.get("chance", 0.002)) * (1.0 + float(k.get("insight_weight", 0.01)) * c.stats.value("insight"))
	if rng.randf() >= chance: return
	trigger_epiphany(c, rng)

func trigger_epiphany(c, rng: RandomNumberGenerator) -> void:
	var cu: CultivatorState = c.cultivator
	var k: Dictionary = ContentDB.stat_const("epiphany", {})
	cu.epiphany_cooldown = float(k.get("cooldown_s", 7200))
	game.combat.apply_buff(c.id, {"stat": "insight_rate", "op": "flat", "value": float(k.get("insight_mult", 5.0)) - 1.0,
		"duration": float(k.get("buff_s", 60)), "source": "epiphany"}, "epiphany")
	var gift := ""
	if rng.randf() < float(k.get("mastery_chance", 0.25)):
		# The free "variant": the most-used technique takes a step of mastery for nothing.
		var best := ""
		for tid in cu.technique_use:
			if best == "" or int(cu.technique_use[tid]) > int(cu.technique_use[best]): best = str(tid)
		if best != "" and cu.mastery.has(best) and int(cu.mastery[best].get("tier", 1)) < 6:
			cu.mastery[best].tier = int(cu.mastery[best].get("tier", 1)) + 1
			cu.mastery[best].points = 0.0
			gift = best
			emit("technique_mastery_up", {"actor": c.id, "technique": best, "tier": int(cu.mastery[best].tier)})
	if not game.account.codex.has("epiphany"): game.quest.apply_codex("epiphany")
	emit("epiphany", {"actor": c.id, "technique": gift, "seconds": float(k.get("buff_s", 60))})

# ------------------------------------------------------------------ natural treasures
## The Nine-Bough Jade Tree answers only a mind stuck at an Understanding bottleneck, once per
## realm stage: a large share of the strongest Dao's gap to its next tier.
func consult_jade_tree(c) -> Dictionary:
	var stuck := false
	if c.cultivator.state == "bottleneck":
		for r in progression.query_requirements(c):
			if not r.ok and str(r.cause) == "understanding": stuck = true
	if not stuck: return ok({"text": Tx.t("sim.progression.the_jade_leaves_are_still")})
	if str(c.cultivator.treasure_uses.get("nine_bough_jade_tree", "")) == c.cultivator.realm_key:
		return ok({"text": Tx.t("sim.progression.the_tree_has_answered")})
	var dao := ""
	var best := -1.0
	for d in c.cultivator.daos:
		if float(c.cultivator.daos[d].get("insight", 0.0)) > best:
			best = float(c.cultivator.daos[d].get("insight", 0.0))
			dao = str(d)
	if dao == "": dao = "sword"
	var tiers: Array = ContentDB.curve("dao_tiers", [100, 300, 800, 2000, 5000, 12000])
	var tier := int(c.cultivator.daos.get(dao, {}).get("tier", 0))
	var gap := float(tiers[mini(tier, tiers.size() - 1)]) - maxf(0.0, best)
	var cfg: Dictionary = ContentDB.stat_const("treasures", {})
	var amount := maxf(float(cfg.get("jade_tree_min_insight", 500)), gap * float(cfg.get("jade_tree_share", 0.75)))
	apply_insight(c.id, dao, amount, "nine_bough_jade_tree")
	c.cultivator.treasure_uses["nine_bough_jade_tree"] = c.cultivator.realm_key
	emit("natural_treasure_used", {"actor": c.id, "treasure": "nine_bough_jade_tree", "dao": dao, "amount": amount})
	return ok({"text": Tx.t("sim.progression.the_tree_answers") % ContentDB.name_of("daos", dao), "dao": dao, "amount": amount})

# ------------------------------------------------------------------ S49 leisure arts: chess
## An insight site's chess problem today (chess.json), the same on every device.
func chess_of(site: String) -> Dictionary:
	var all: Array = ContentDB.all("chess")
	if all.is_empty(): return {}
	var r := Rng.keyed(int(game.account.rng_seed), "chess:%s:%d" % [site, Clock.reset_day(Clock.now_utc())])
	return all[r.randi_range(0, all.size() - 1)]

func chess_open(c, site: String) -> bool:
	return int(c.cooldowns.get("chess:" + site, -1)) != Clock.reset_day(Clock.now_utc())

## One answer a day at each site: the right point gives insight into your deepest Dao.
func solve_chess(c, site: String, choice: String) -> Dictionary:
	var pz := chess_of(site)
	if pz.is_empty() or site == "": return fail("no_problem")
	if not chess_open(c, site): return fail("done", {"text": Tx.t("sim.progression.chess_done")})
	c.cooldowns["chess:" + site] = Clock.reset_day(Clock.now_utc())
	var right := choice == str(pz.answer)
	if right: apply_insight_best(c.id, float(ContentDB.config("chess").get("insight", 30)), "chess")
	emit("chess_solved", {"actor": c.id, "puzzle": str(pz.id), "site": site, "right": right})
	return ok({"right": right, "answer": str(pz.answer)})

## Insight into the Dao you know best (or, before any Dao, a little realm progress): the hermit's chess problem, and
## the insight sites' problems.
func apply_insight_best(actor_id: String, amount: float, context := "fortune") -> void:
	var c = game.character(actor_id)
	if c == null: return
	var best := ProgressionRules.strongest_dao(c)
	if best != "" and Unlocks.is_unlocked(c.id, "dao_tree"): apply_insight(c.id, best, amount, context + ":chess:" + str(Clock.reset_day(Clock.now_utc())))
	# Decision 45: a fixed amount of cultivation for the insight it would have given (30 insight: +120), not 2% of the stage.
	else: progression.apply_progress(c.id, amount * float(ContentDB.curve("insight_fallback_per_point", 4)), context)
