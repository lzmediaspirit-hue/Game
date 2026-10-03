class_name CombatTreasures
extends CombatPart
## CombatAuthority's part for treasures and throwables (gap report G2, S47): the HUD's two Treasure buttons and their
## lingering effects, the quick-use throwables, and self-detonation. State: `combat.treasure_fx`, `combat.captured`.

## What a treasure does (treasures.json, S47), from its bag item id; {} if the item is not a treasure.
static func treasure_of(item_id: String) -> Dictionary:
	var tid := str(ContentDB.item(item_id).get("treasure", ""))
	return ContentDB.entry("treasures", tid) if tid != "" else {}

## Its Soul cost: a treasure also draws on the Soul from Spirit Awakening 1 (S47).
static func treasure_soul_cost(c, t: Dictionary) -> float:
	if c.pools.max_soul <= 0.0 or not ProgressionRules.at_least(c.cultivator.realm_key, "spirit_awakening_1"): return 0.0
	return float(t.get("soul", 0))

func _treasure_attack(t: Dictionary, source: String, dtype := "physical", element := "none") -> Dictionary:
	var m := float(t.get("mult", 1.0))
	return {"damage_type": dtype, "element": element, "mult": [m, m], "range": [1.0, 1.0], "knockback": float(t.get("knockback", 0.0)), "source": source}

## One of the HUD's Treasure buttons. Each treasure is one action with a cooldown and a flat QI cost (S47);
## a talisman treasure spends one of its charges instead.
func use_treasure(c, slot: int) -> Dictionary:
	if slot < 0 or slot > 1: return fail("bad_slot")
	var id := str(c.inventory.treasures[slot])
	if id == "": return fail("empty")
	if not Unlocks.is_unlocked(c.id, "treasures" if slot == 0 else "treasure_slot_2"): return fail("locked")
	if c.inventory.count(id) <= 0:
		c.inventory.treasures[slot] = ""
		return fail("missing")
	var why := combat.can_act(c)
	if why != "": return fail(why)
	var t := treasure_of(id)
	if t.is_empty(): return fail("unknown_treasure")
	var cd_key := "treasure:" + id
	if c.pools.cooldown(cd_key) > 0.0: return fail("cooldown", {"remaining": c.pools.cooldown(cd_key)})
	var cost := float(t.get("qi", 0))
	if cost > 0.0 and (c.pools.max_qi <= 0.0 or c.pools.qi < cost): return fail("no_qi", {"text": Tx.t("sim.combat.treasure_no_qi")})
	var soul := treasure_soul_cost(c, t)
	if soul > 0.0 and c.pools.soul < soul: return fail("no_soul", {"text": Tx.t("sim.combat.treasure_no_soul")})
	var pv := combat.player_view(c)
	var here := Vector2(float(pv.x), float(pv.y))
	var tl := combat.timeline(c.id)
	var out := {"action": str(t.action), "treasure": id, "targets": 0, "x": pv.x, "y": pv.y}
	var fxs: Dictionary = combat.treasure_fx.get(c.id, {})
	match str(t.action):
		"bell":
			for e in combat._enemies_within(here, float(t.get("radius", 150))):
				if not e.is_boss(): combat._apply_status_to_enemy(e, {"id": "stun", "power": 1.0, "remaining": float(t.get("stun_s", 1.0)), "source": c.id})
				if float(t.get("seal_s", 0)) > 0.0:
					combat._apply_status_to_enemy(e, {"id": "qi_seal", "power": 1.0, "remaining": float(t.seal_s), "source": c.id})
				out.targets = int(out.targets) + 1
		"pagoda":
			# One foe, an elite first if one is in reach; bosses are too great for it.
			var tgt: EnemyState = null
			for e in combat._enemies_within(here, float(t.get("range", 320))):
				if e.is_boss(): continue
				if tgt == null or (e.elite and not tgt.elite) or (e.elite == tgt.elite and e.plane.distance_to(here) < tgt.plane.distance_to(here)): tgt = e
			if tgt == null:
				var near_boss := combat._nearest_enemy(here, float(t.get("range", 320)))
				if near_boss != null and near_boss.is_boss(): return fail("immune", {"text": Tx.t("sim.combat.pagoda_boss")})
				return fail("no_target", {"text": Tx.t("sim.combat.treasure_no_target")})
			combat._apply_status_to_enemy(tgt, {"id": "stun", "power": 1.0, "remaining": float(t.get("imprison_s", 4.0)), "source": c.id})
			out.targets = 1
			out.x = tgt.plane.x
			out.y = tgt.plane.y
		"mirror":
			fxs.reflect = float(t.get("reflect_s", 2.0))
		"seal":
			var atk := _treasure_attack(t, "treasure:" + id, str(t.get("damage_type", "qi")), "earth")
			for e in combat._enemies_within(here, float(t.get("radius", 120))):
				combat._player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
				out.targets = int(out.targets) + 1
		"cauldron":
			var best: EnemyState = null
			for e in combat._enemies_within(here, float(t.get("range", 260))):
				if e.is_boss() or str(e.def.get("race", "beast")) != "beast": continue
				if e.pools.hp > e.pools.max_hp * float(t.get("below", 0.2)): continue
				if best == null or e.plane.distance_to(here) < best.plane.distance_to(here): best = e
			if best == null: return fail("no_target", {"text": Tx.t("sim.combat.cauldron_no_target")})
			combat.captured[str(best.uid)] = true
			out.x = best.plane.x
			out.y = best.plane.y
			combat._damage_enemy(best, best.pools.hp + 1.0, c.id, "physical", "none", false, {"source": "treasure:" + id})
			out.targets = 1
		"banner":
			fxs.wisps = {"left": float(t.get("duration", 10)), "tick": 1.0, "n": int(t.get("wisps", 3)), "mult": float(t.get("mult", 0.6)),
				"range": float(t.get("range", 280))}
		"swarm":
			var sw := combat.swarm.start_swarm(c, true, float(t.get("duration", 12)))
			if not sw.get("ok", false): return sw
			out.targets = int(sw.get("swarm", 0))
		"gourd":
			fxs.gourd = float(t.get("absorb_s", 3.0))
			fxs.gourd_r = float(t.get("radius", 240.0))
		"palm":
			# Elder Hu's Heaven-Splitting Palm: 600% Qi Attack along a line before you, one charge a use.
			var facing := int(tl.facing)
			var atk := {"damage_type": "qi", "element": "metal", "mult": [float(t.get("mult", 6.0)), float(t.get("mult", 6.0))], "range": [1.0, 1.0],
				"knockback": 160.0, "source": "treasure:" + id}
			for e in combat._enemies_in(pv, facing, {"x": [0, float(t.get("reach", 540))], "depth": float(t.get("depth", 70)), "alt": [-40, 160]}, false):
				combat._player_hits_enemy(c, pv, e, atk, facing)
				out.targets = int(out.targets) + 1
			out.facing = facing
			out.reach = float(t.get("reach", 540))
		_:
			return fail("unknown_treasure")
	combat.treasure_fx[c.id] = fxs
	if cost > 0.0: combat.apply_resource_change(c.id, "qi", -cost, "treasure")
	if soul > 0.0: combat.apply_resource_change(c.id, "soul", -soul, "treasure")
	if float(t.get("cooldown_s", 0)) > 0.0: c.pools.cooldowns[cd_key] = float(t.cooldown_s)
	if t.has("charges"):
		var idx: int = c.inventory.first_index(id)
		if idx >= 0:
			var stack: Dictionary = c.inventory.bag[idx]
			var left := int(stack.get("charges", int(t.charges))) - 1
			out.charges = maxi(0, left)
			if left <= 0:
				game.inventory.apply_remove_index(c.id, idx, 1, "charges_spent")
				c.inventory.treasures[slot] = ""
			else:
				stack.charges = left
			emit("bag_changed", {"actor": c.id})
	tl.flinch = 0.0
	out.actor = c.id
	emit("treasure_used", out)
	emit("system_used", {"actor": c.id, "system": "treasure"})
	return ok(out)

func tick_treasures(c, delta: float) -> void:
	var fxs: Dictionary = combat.treasure_fx.get(c.id, {})
	if fxs.is_empty(): return
	for k in ["reflect", "gourd"]:
		if float(fxs.get(k, 0.0)) > 0.0: fxs[k] = maxf(0.0, float(fxs[k]) - delta)
	# S47 talismans: Iron Wall's shield fades when its time is up; Wind Step's free dodge lapses unused.
	if fxs.has("shield_t"):
		fxs.shield_t = float(fxs.shield_t) - delta
		if float(fxs.shield_t) <= 0.0:
			fxs.erase("shield_t")
			c.pools.shield = 0.0
	if fxs.has("free_dodge"):
		fxs.free_dodge = float(fxs.free_dodge) - delta
		if float(fxs.free_dodge) <= 0.0: fxs.erase("free_dodge")
	var w: Dictionary = fxs.get("wisps", {})
	if not w.is_empty():
		w.left = float(w.left) - delta
		w.tick = float(w.tick) - delta
		if float(w.tick) <= 0.0 and game.room_rt:
			w.tick = float(w.tick) + 1.0
			var pv := combat.player_view(c)
			var here := Vector2(float(pv.x), float(pv.y))
			var targets := combat._enemies_within(here, float(w.range))
			targets.sort_custom(func(a, b): return a.plane.distance_to(here) < b.plane.distance_to(here))
			var atk := {"damage_type": "qi", "element": "none", "mult": [float(w.mult), float(w.mult)], "range": [1.0, 1.0], "source": "treasure:wisp_banner"}
			for i in mini(int(w.n), targets.size()):
				var e: EnemyState = targets[i]
				combat._player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
				emit("wisp_struck", {"actor": c.id, "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.height() * 0.6})
		if float(w.left) <= 0.0: fxs.erase("wisps")

# ------------------------------------------------------------------ throwables (G2)
## A throwable from the quick-use slot (G2): needles, knives, a thunderclap pellet. Any weapon family can throw.
func apply_throw(actor_id: String, e: Dictionary) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var pv := combat.player_view(c)
	var facing := int(combat.timeline(c.id).facing)
	var n := int(e.get("count", 1))
	for i in n:
		combat.projectiles.spawn_projectile({"team": "player", "owner": c.id, "x": float(pv.x) + facing * 24, "y": float(pv.y) + (i - (n - 1) * 0.5) * 6.0,
			"alt": float(pv.alt) + 56 + i * 3, "dir": facing, "speed": float(e.get("speed", 600)), "range": float(e.get("range", 380)),
			"pierce": int(e.get("pierce", 0)), "art": str(e.get("art", "needle")), "delay": i * 0.05, "element": "none",
			"attack": _treasure_attack(e, "throw:" + str(e.get("art", "needle"))), "burst": float(e.get("burst", 0.0)),
			"cloud": e.get("cloud", {})})
	emit("system_used", {"actor": c.id, "system": "throw"})

## A thunderclap pellet bursts where it lands: everything close by takes the blow and is thrown back.
func burst(c, p: Dictionary, first: EnemyState) -> void:
	var at := Vector2(float(p.x), float(p.y))
	var pv := combat.player_view(c)
	for e in combat._enemies_within(at, float(p.burst)):
		if e == first: continue
		combat._player_hits_enemy(c, pv, e, p.attack, 1 if e.plane.x >= at.x else -1)
	# A poison pill leaves a cloud (S44): its status on everything inside, the first foe too.
	var cloud: Dictionary = p.get("cloud", {})
	if not cloud.is_empty():
		for e in combat._enemies_within(at, float(p.burst)):
			if e.alive and not e.pools.steadfast.has(str(cloud.status)):
				combat._apply_status_to_enemy(e, {"id": str(cloud.status), "power": float(cloud.get("power", 0.02)), "remaining": float(cloud.get("duration_s", 5.0)), "source": c.id})
	emit("projectile_burst", {"actor": c.id, "x": p.x, "y": p.y, "alt": p.alt, "radius": p.burst, "cloud": str(cloud.get("status", ""))})

# ------------------------------------------------------------------ self-detonation (S47)
## Self-detonation (S47): a spare artifact (an unworn piece of equipment, or a treasure) bursts around you for
## damage by its grade, and is destroyed. The one thing the game ever destroys, and only after you confirm.
func self_detonate(c, index: int, confirm: bool) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var inst: Dictionary = c.inventory.bag[index]
	var def := ContentDB.item(str(inst.id))
	if not (ContentDB.is_equipment(str(inst.id)) or def.has("treasure")) or str(def.get("slot", "")) == "tool_furnace": return fail("not_artifact", {"text": Tx.t("sim.combat.detonate_what")})
	if c.inventory.locked.has(int(inst.get("uid", -1))): return fail("locked_item", {"text": Tx.t("ui.forge.locked_item")})
	var reason := combat.can_act(c)
	if reason != "": return fail(reason)
	if not confirm: return fail("confirm", {"text": Tx.t("sim.combat.detonate_confirm") % ContentDB.item_name(str(inst.id))})
	var gi := StatRules.grade_index(str(def.get("grade", "plain")))
	var power := float(ContentDB.stat_const("detonation.base", 1.5)) + float(ContentDB.stat_const("detonation.per_grade", 0.75)) * gi
	var pv := combat.player_view(c)
	var n := 0
	if game.room_rt:
		for e in game.room_rt.living_enemies():
			if e.team != "enemy" or e.hidden: continue
			if e.plane.distance_to(Vector2(float(pv.x), float(pv.y))) > float(ContentDB.stat_const("detonation.radius", 180)): continue
			combat._player_hits_enemy(c, pv, e, {"damage_type": "qi", "element": "none", "mult": [power, power], "range": [1.0, 1.0], "source": "detonation",
				"knockback": 140.0}, 1 if e.plane.x >= float(pv.x) else -1)
			n += 1
	game.inventory.apply_remove_index(c.id, index, 1, "self_detonate")
	emit("artifact_detonated", {"actor": c.id, "item": str(inst.id), "grade": str(def.get("grade", "plain")), "targets": n,
		"x": pv.x, "y": pv.y, "alt": pv.alt})
	return ok({"targets": n, "power": power})
