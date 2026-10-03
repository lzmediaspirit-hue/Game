class_name CombatSword
extends CombatPart
## CombatAuthority's part for the flying sword and the intents (S47, S48): natal overcharge, Sword Release, Sword Intent
## from consecutive jian hits and Killing Intent from kills in quick succession (both fade in `tick_sword`).
## State: `combat.sword_released`, `combat.sword_intent`, `combat.killing_intent` (none saved).

# ------------------------------------------------------------------ natal overcharge (S47)
## S47 natal overcharge: a natal weapon asks 10 + 5 x its natal level of Spirit to command. Below that, each
## technique drawn through it has a 5% chance to break it.
func natal_demand(inst: Dictionary) -> float:
	return float(ContentDB.stat_const("natal.demand_base", 10)) + float(ContentDB.stat_const("natal.demand_per_level", 5)) * int(inst.get("natal_level", 0))

func natal_overcharge(c) -> void:
	var inst: Dictionary = game.inventory.natal_of(c)
	if inst.is_empty() or c.inventory.equipped.get("weapon") != inst or inst.get("broken", false): return
	if StatRules.attribute(c, "spirit") >= natal_demand(inst): return
	if Rng.stream(c.id, "combat").randf() < float(ContentDB.stat_const("natal.overcharge_chance", 0.05)): game.inventory.natal_break(c, "overcharge")

# ------------------------------------------------------------------ Sword Release (S47)
func knows_sword_release(c) -> bool:
	return c.cultivator.techniques_known.has("sword_release")

## Sword Release: the jian leaves the hand and strikes on its own, homing on the nearest foe (60% of the jian's
## attack, 1.5 strikes a second) for up to 8 s or until recalled; meanwhile the hands fight with Qi palms.
func toggle_sword_release(c) -> Dictionary:
	if combat.sword_released.has(c.id):
		return_sword(c, "recalled")
		return ok({"released": false})
	if not knows_sword_release(c): return fail("locked", {"text": Tx.t("sim.combat.sword_release_locked")})
	if str(StatRules.family(c).get("id", "")) != "jian": return fail("wrong_weapon", {"text": Tx.t("sim.combat.needs_a") % "jian"})
	var reason := combat.can_act(c)
	if reason != "": return fail(reason)
	if c.pools.cooldown("tech:sword_release") > 0.0: return fail("cooldown")
	var t := ContentDB.entry("techniques", "sword_release")
	var cost := combat.technique_cost(c, t)
	if c.pools.max_qi <= 0.0 or c.pools.qi < cost: return fail("no_qi")
	combat.apply_resource_change(c.id, "qi", -cost, "technique")
	c.pools.cooldowns["tech:sword_release"] = float(t.get("cooldown_s", 12))
	combat.sword_released[c.id] = {"t": float(t.get("release_s", 8.0)), "next": 0.15}
	emit("sword_released", {"actor": c.id, "weapon": str(c.inventory.equipped.weapon.id)})
	emit("technique_used", {"actor": c.id, "technique": "sword_release", "hits": 0, "targets": 0})
	return ok({"released": true})

func return_sword(c, why: String) -> void:
	if not combat.sword_released.has(c.id): return
	combat.sword_released.erase(c.id)
	emit("sword_returned", {"actor": c.id, "reason": why})

## The intents fade, then the released sword strikes its next foe.
func tick_sword(c, delta: float) -> void:
	var ki: Dictionary = combat.killing_intent.get(c.id, {})
	if not ki.is_empty() and float(ki.t) > 0.0:
		ki.t = float(ki.t) - delta
		if float(ki.t) <= 0.0:
			combat.killing_intent.erase(c.id)
			emit("killing_intent_changed", {"actor": c.id, "stacks": 0})
	var si: Dictionary = combat.sword_intent.get(c.id, {})
	if not si.is_empty() and int(si.stacks) > 0:
		si.t = float(si.t) - delta
		if float(si.t) <= 0.0:
			si.stacks = 0
			emit("sword_intent_changed", {"actor": c.id, "stacks": 0})
	if not combat.sword_released.has(c.id): return
	if combat.wounded.has(c.id) or str(StatRules.family(c).get("id", "")) != "jian":
		return_sword(c, "lost")
		return
	var s: Dictionary = combat.sword_released[c.id]
	s.t = float(s.t) - delta
	if float(s.t) <= 0.0:
		return_sword(c, "time")
		return
	s.next = float(s.next) - delta
	if float(s.next) > 0.0 or game.room_rt == null: return
	var t := ContentDB.entry("techniques", "sword_release")
	s.next = 1.0 / float(t.get("strikes_per_s", 1.5))
	var pv := combat.player_view(c)
	var foe := combat._nearest_enemy(Vector2(float(pv.x), float(pv.y)), float(t.get("seek_radius", 420)))
	if foe == null: return
	var from := Vector2(float(pv.x) - int(pv.facing) * 20.0, float(pv.y))
	var dir := 1 if foe.plane.x >= from.x else -1
	var m: Array = t.get("mult", [0.6, 0.6])
	combat.projectiles.spawn_projectile({"team": "player", "owner": c.id, "x": from.x, "y": from.y, "alt": float(pv.alt) + 70.0, "dir": dir, "speed": 900.0,
		"range": absf(foe.plane.x - from.x) + 90.0, "pierce": 0, "seek": true, "art": "flying_sword",
		"attack": {"damage_type": "physical", "element": "metal", "mult": m, "range": [0.95, 1.05], "source": "flying_sword",
			"dao_tier": combat._dao_tier(c, "sword")}})

# ------------------------------------------------------------------ Sword Intent (S47)
## Sword Intent: consecutive jian hits stack (max 10, +1% penetration each); at 10 a weaker foe may fear (10%).
## It fades 3 s after the last jian hit.
func feed_intent(c, e: EnemyState, attack: Dictionary) -> void:
	var src := str(attack.get("source", ""))
	if not (src == "basic" or src == "flying_sword" or src.begins_with("tech:")): return
	if combat.sword_released.has(c.id) and src == "basic": return   # palms are not the sword
	if str(StatRules.family(c).get("id", "")) != "jian": return
	var si: Dictionary = combat.sword_intent.get(c.id, {"stacks": 0, "t": 0.0})
	var before := int(si.stacks)
	var honed := StatRules.set_flag(c, "honed_intent")
	var most := int(ProgressionRules.path_flag(c, "sword_intent_max", ContentDB.stat_const("sword_intent.max", 10))) + int(honed.get("stacks", 0))   # Sword Heart: 12
	si.stacks = mini(most, before + 1)
	si.t = float(ContentDB.stat_const("sword_intent.fade_s", 3.0)) * float(honed.get("fade_mult", 1.0))
	combat.sword_intent[c.id] = si
	if int(si.stacks) != before: emit("sword_intent_changed", {"actor": c.id, "stacks": int(si.stacks)})
	if int(si.stacks) >= 10 and e.alive and e.level < ProgressionRules.level(c) and not e.pools.steadfast.has("fear"):
		if Rng.stream(c.id, "combat").randf() < float(ContentDB.stat_const("sword_intent.fear_chance", 0.1)):
			combat.apply_status_to_enemy(e, {"id": "fear", "power": 1.0, "remaining": 2.0, "source": c.id})

func intent_penetration(c) -> float:
	if str(StatRules.family(c).get("id", "")) != "jian": return 0.0
	return 0.01 * int(combat.sword_intent.get(c.id, {}).get("stacks", 0))

# ------------------------------------------------------------------ Killing Intent (S48)
## S48 Killing Intent: a kill within 10 s of the last adds a stack (up to 10), +1% crit each. At 10, weaker foes
## nearby hesitate for half a second. The Silence vow keeps it sheathed.
func gain_killing_intent(c, victim: EnemyState) -> void:
	if game.progression.vow_forbids(c, "presence") != "": return
	var k: Dictionary = ContentDB.stat_const("killing_intent", {})
	var ki: Dictionary = combat.killing_intent.get(c.id, {"stacks": 0, "t": 0.0})
	var before := int(ki.stacks)
	ki.stacks = mini(int(k.get("max", 10)), before + 1) if float(ki.t) > 0.0 or before == 0 else 1
	ki.t = float(k.get("window_s", 10.0))
	combat.killing_intent[c.id] = ki
	if int(ki.stacks) != before: emit("killing_intent_changed", {"actor": c.id, "stacks": int(ki.stacks)})
	if int(ki.stacks) >= int(k.get("max", 10)) and game.room_rt:
		var lv := ProgressionRules.level(c)
		var st: ActorState = game.actor_state(c.id)
		for e in game.room_rt.living_enemies():
			if e == victim or e.team != "enemy" or e.is_boss() or e.level >= lv: continue
			if st != null and e.plane.distance_to(st.plane) > float(k.get("radius", 520)): continue
			game.enemies.stagger(e, float(k.get("hesitate_s", 0.5)))

func killing_intent_stacks(actor_id: String) -> int:
	return int(combat.killing_intent.get(actor_id, {}).get("stacks", 0))
