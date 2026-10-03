class_name CombatRevival
extends CombatPart
## CombatAuthority's part for being gravely wounded and getting up again: at the shrine, here with a Revival
## Talisman, or whole with an Evergreen Heart fruit. State: `combat.wounded`.

func gravely_wound(c, cause: String) -> void:
	# The Prologue (before the Willow Path unlocks progress from fights) carries no penalty (S27), and nor does a fall
	# before Bone Forging 5 (the early grace, P12).
	var grace: bool = Unlocks.is_unlocked(c.id, "kill_progress") and ProgressionRules.death_grace(c.cultivator.realm_key)
	var no_penalty: bool = not Unlocks.is_unlocked(c.id, "kill_progress") or grace or bool(game.room_rt.def.get("no_death_penalty", false) if game.room_rt else false)
	combat.wounded[c.id] = {"cause": cause, "timer": 0.0, "no_penalty": no_penalty, "grace": grace}
	var tl := combat.timeline(c.id)
	tl.action = ""
	tl.guard = false
	if c.cultivator.meditating: game.progression.stop_meditation(c, "wounded")
	emit("player_gravely_wounded", {"actor": c.id, "cause": cause, "no_penalty": no_penalty,
		"talisman": c.inventory.count("revival_talisman"), "can_revive_here": revive_here_allowed(c)})

func revive_here_allowed(c) -> Dictionary:
	if c.inventory.count("revival_talisman") <= 0: return {"ok": false, "text": Tx.t("sim.combat.no_revival_talisman")}
	if game.room_rt and game.room_rt.def.get("no_revive_here", false): return {"ok": false, "text": Tx.t("sim.combat.not_allowed_here")}
	var until := float(c.cooldowns.get("revival_talisman_utc", 0.0))
	if Clock.now_utc() < until: return {"ok": false, "text": Tx.t("sim.combat.talisman_recovering_ds") % Tx.span(until - Clock.now_utc())}
	return {"ok": true, "text": ""}

## An Evergreen Heart fruit (natural treasure) lifts you where you fell, whole.
func fruit_revival_allowed(c) -> Dictionary:
	if c.inventory.count("evergreen_heart_fruit") <= 0: return {"ok": false, "text": ""}
	if game.room_rt and game.room_rt.def.get("no_revive_here", false): return {"ok": false, "text": Tx.t("sim.combat.not_allowed_here")}
	return {"ok": true, "text": ""}

func choose_revival(c, where: String) -> Dictionary:
	var wounded: Dictionary = combat.wounded
	if not wounded.has(c.id): return fail("not_wounded")
	var info: Dictionary = wounded[c.id]
	var death: Dictionary = ContentDB.stat_const("death", {})
	if info.get("grace", false): game.quest.apply_flag(c.id, "death_grace_told")   # the revival page has explained it once
	if where == "fruit":
		var fruit := fruit_revival_allowed(c)
		if not fruit.ok: return fail("not_allowed", {"text": fruit.text})
		game.inventory.apply_remove(c.id, "evergreen_heart_fruit", 1, "revive")
		wounded.erase(c.id)
		c.pools.hp = c.pools.max_hp
		if c.pools.max_soul > 0: c.pools.soul = c.pools.max_soul
		c.pools.statuses.clear()
		c.pools.invulnerable = float(ContentDB.stat_const("treasures", {}).get("fruit_invuln_s", 3))
		emit("player_revived", {"actor": c.id, "where": "fruit"})
		emit("natural_treasure_used", {"actor": c.id, "treasure": "evergreen_heart_fruit"})
	elif where == "here":
		var allowed := revive_here_allowed(c)
		if not allowed.ok: return fail("not_allowed", {"text": allowed.text})
		game.inventory.apply_remove(c.id, "revival_talisman", 1, "revive")
		c.cooldowns["revival_talisman_utc"] = Clock.now_utc() + float(death.get("talisman_cooldown_s", 300))
		wounded.erase(c.id)
		c.pools.hp = c.pools.max_hp * float(death.get("talisman_hp", 0.3))
		c.pools.invulnerable = float(death.get("talisman_invuln_s", 5))
		emit("player_revived", {"actor": c.id, "where": "here"})
	else:
		wounded.erase(c.id)
		c.pools.hp = c.pools.max_hp * (1.0 if info.no_penalty else float(death.get("wake_hp", 0.5)))
		if c.pools.max_soul > 0: c.pools.soul = maxf(c.pools.soul, c.pools.max_soul * 0.3)
		c.pools.statuses.clear()
		c.pools.invulnerable = float(ContentDB.stat_const("combat.spawn_protection_s", 1.5))
		emit("player_revived", {"actor": c.id, "where": "shrine"})
		game.world.apply_return_to_shrine(c.id)
	for pool in ["hp", "soul"]:
		emit("resource_changed", {"actor": c.id, "pool": pool, "value": c.pools.get_value(pool), "max": c.pools.get_max(pool)})
	return ok()
