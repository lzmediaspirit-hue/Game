class_name CombatSwarm
extends CombatPart
## CombatAuthority's part for the sword swarm (S47 v1.1): swords orbiting you, each striking in turn, from the Sword
## Swarm technique or the Nine Swords Array treasure. State: `combat.sword_swarm` (not saved).

## How many swords would answer: 3 at Sword Dao 5, 9 with the Nine Swords Array (released, or set in a Treasure
## slot), 36 with it at Original Application (tier 6). Spirit is the control demand: one sword for each 10 Spirit.
func swarm_count(c, with_treasure: bool) -> int:
	var cfg: Dictionary = ContentDB.stat_const("sword_swarm", {})
	var counts: Array = cfg.get("counts", [3, 9, 36])
	var tier := combat._dao_tier(c, "sword")
	var has_set: bool = with_treasure or "nine_sword_array" in c.inventory.treasures
	var n := 0
	if tier >= 5: n = int(counts[0])
	if has_set: n = int(counts[1])
	if has_set and tier >= 6: n = int(counts[2])
	if n <= 0: return 0
	var cap := maxi(1, int(floor(c.stats.value("spirit") / float(cfg.get("spirit_per_sword", 10)))))
	return mini(n, cap)

## The Sword Swarm technique: a toggle like Sword Release, paid in QI.
func toggle_sword_swarm(c, t: Dictionary) -> Dictionary:
	if combat.sword_swarm.has(c.id):
		end_swarm(c, "recalled")
		return ok({"swarm": 0})
	var reason := combat.can_act(c)
	if reason != "": return fail(reason)
	if c.pools.cooldown("tech:sword_swarm") > 0.0: return fail("cooldown")
	var cost := combat.technique_cost(c, t)
	if c.pools.max_qi <= 0.0 or c.pools.qi < cost: return fail("no_qi")
	var r := start_swarm(c, false, float(ContentDB.stat_const("sword_swarm", {}).get("duration_s", 12.0)))
	if not r.get("ok", false): return r
	combat.apply_resource_change(c.id, "qi", -cost, "technique")
	c.pools.cooldowns["tech:sword_swarm"] = float(t.get("cooldown_s", 30))
	emit("technique_used", {"actor": c.id, "technique": "sword_swarm", "hits": 0, "targets": 0})
	return r

func start_swarm(c, from_treasure: bool, secs: float) -> Dictionary:
	var n := swarm_count(c, from_treasure)
	if n <= 0: return fail("locked", {"text": Tx.t("sim.combat.swarm_locked")})
	if combat.sword_released.has(c.id): combat.sword.return_sword(c, "swarm")
	combat.sword_swarm[c.id] = {"t": secs, "n": n, "next": 0.2, "i": 0}
	emit("sword_released", {"actor": c.id, "weapon": "swarm", "swarm": n})
	return ok({"swarm": n})

func swarm_of(actor_id: String) -> int:
	return int(combat.sword_swarm.get(actor_id, {}).get("n", 0))

func end_swarm(c, why: String) -> void:
	if not combat.sword_swarm.has(c.id): return
	combat.sword_swarm.erase(c.id)
	emit("sword_returned", {"actor": c.id, "reason": why, "swarm": true})

## Each sword strikes in turn: one strike every 1.2 s / n, at 0.9 / sqrt(n) of the jian's attack (so more swords
## add damage, but not in proportion).
func tick_swarm(c, delta: float) -> void:
	if not combat.sword_swarm.has(c.id): return
	if combat.wounded.has(c.id):
		end_swarm(c, "lost")
		return
	var s: Dictionary = combat.sword_swarm[c.id]
	s.t = float(s.t) - delta
	if float(s.t) <= 0.0:
		end_swarm(c, "time")
		return
	s.next = float(s.next) - delta
	if float(s.next) > 0.0 or game.room_rt == null: return
	var cfg: Dictionary = ContentDB.stat_const("sword_swarm", {})
	var n := maxi(1, int(s.n))
	s.next = float(cfg.get("strike_every_s", 1.2)) / n
	var pv := combat.player_view(c)
	var foe := combat._nearest_enemy(Vector2(float(pv.x), float(pv.y)), float(cfg.get("seek_radius", 420)))
	if foe == null: return
	s.i = (int(s.i) + 1) % n
	var ang := TAU * float(s.i) / n
	var orbit := float(cfg.get("orbit", 46))
	var from := Vector2(float(pv.x) + cos(ang) * orbit, float(pv.y) + sin(ang) * orbit * 0.3)
	var dir := 1 if foe.plane.x >= from.x else -1
	var m := float(cfg.get("mult_total", 0.9)) / sqrt(float(n))
	combat.projectiles.spawn_projectile({"team": "player", "owner": c.id, "x": from.x, "y": from.y, "alt": float(pv.alt) + 70.0 + sin(ang) * 16.0, "dir": dir,
		"speed": 900.0, "range": absf(foe.plane.x - from.x) + 90.0, "pierce": 0, "seek": true, "art": "flying_sword",
		"attack": {"damage_type": "physical", "element": "metal", "mult": [m, m], "range": [0.95, 1.05], "source": "flying_sword",
			"dao_tier": combat._dao_tier(c, "sword")}})
