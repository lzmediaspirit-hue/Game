class_name CombatFlight
extends CombatPart
## CombatAuthority's part for flight (S18) and the movement arts Plunge and Falling Leaf Glide (S43). The
## movement solver moves the body; Combat owns whether it may and pays the QI. State: `combat.flying`, `combat.gliding`.

# ------------------------------------------------------------------ flight (S18)
## Cloud Stride lets Qi hold the body in the air. The movement solver moves it; Combat
## owns whether it may, and pays the QI every second.
func start_flight(c) -> Dictionary:
	var cfg: Dictionary = ContentDB.stat_const("flight", {})
	if not Unlocks.is_unlocked(c.id, str(cfg.get("unlock", "flight"))): return fail("locked", {"text": Unlocks.locked_text("flight")})
	if combat.flying.has(c.id): return fail("already_flying")
	if combat.wounded.has(c.id) or c.pools.blocked("move"): return fail("blocked")
	if not flight_allowed(c.id):
		return fail("no_flight", {"text": Tx.t("sim.combat.no_flight_here")})
	if c.pools.qi < c.pools.max_qi * float(cfg.get("start_qi_pct", 0.1)) or c.pools.max_qi <= 0.0:
		return fail("no_qi", {"text": Tx.t("sim.combat.not_enough_qi_to_fly")})
	combat.flying[c.id] = true
	emit("flight_started", {"actor": c.id})
	emit("system_used", {"actor": c.id, "system": "flight"})
	return ok({"climb": float(cfg.get("climb", 220)), "ceiling": float(cfg.get("ceiling", 340))})

## Flight is refused indoors, on sect grounds, in dungeons, in rooms that forbid it and inside a no_flight
## volume (S43); gliding still works there.
func flight_allowed(actor_id: String) -> bool:
	var room: Dictionary = game.room_rt.def if game.room_rt else {}
	if room.get("no_flight", false) or str(room.get("type", "")) in ContentDB.stat_const("flight.no_flight_types", ["interior"]): return false
	var st: ActorState = game.actor_state(actor_id)
	if st != null and game.room_rt and not game.room_rt.geometry.volume_at(st.plane, st.altitude, "no_flight").is_empty(): return false
	return true

func stop_flight(actor_id: String, reason: String) -> void:
	if not combat.flying.has(actor_id): return
	combat.flying.erase(actor_id)
	emit("flight_ended", {"actor": actor_id, "reason": reason})

func is_flying(actor_id: String) -> bool:
	return combat.flying.has(actor_id)

## The flight vessel ridden (S47): what the air costs.
func vessel_qi_mult(c) -> float:
	return float(ContentDB.item(str(c.inventory.vessel)).get("flight", {}).get("qi_mult", 1.0)) if str(c.inventory.vessel) != "" else 1.0

## S48 Cloud Lung and the flight_qi stat: what the air costs this body.
func air_qi_mult(c) -> float:
	var gate := float(ContentDB.stat_const("gates", {}).get("flight_qi_mult", 0.8)) if StatRules.gate_flag(c, "flight_qi_20") else 1.0   # S10 Essence 50
	return maxf(0.5, (1.0 + c.stats.value("flight_qi")) * gate)

func tick_flight(c, delta: float) -> void:
	if not combat.flying.has(c.id): return
	if combat.wounded.has(c.id):
		stop_flight(c.id, "wounded")
		return
	if not flight_allowed(c.id):
		stop_flight(c.id, "no_flight")
		return
	var cfg: Dictionary = ContentDB.stat_const("flight", {})
	var cost = maxf(float(cfg.get("qi_min_per_s", 2.0)), c.pools.max_qi * float(cfg.get("qi_pct_per_s", 0.02))) * delta * game.pets.flight_qi_mult(c) \
		* vessel_qi_mult(c) * air_qi_mult(c)
	if c.pools.qi <= cost:
		stop_flight(c.id, "no_qi")
		return
	combat.apply_resource_change(c.id, "qi", -cost, "flight", 0.0, true)
	_air_distance(c, delta)

## The ground covered in the air counts toward Cloud Lung (S48).
func _air_distance(c, delta: float) -> void:
	var st: ActorState = game.actor_state(c.id)
	if st != null: game.progression.add_air_distance(c.id, absf(st.velocity.x) * delta)

# ------------------------------------------------------------------ movement arts (S43)
## The movement art a secret art grants (secret_arts.json `movement_art`), known to this character.
func knows_art(c, art: String) -> bool:
	for sa in c.cultivator.secret_arts:
		if str(ContentDB.entry("secret_arts", str(sa)).get("movement_art", "")) == art: return true
	return false

## Plunge (Bone Forging 4): Down + Attack in the air drops at 900; the landing strikes within 60.
func plunge(c) -> Dictionary:
	if not knows_art(c, "plunge"): return fail("locked")
	var why := combat.can_act(c)
	if why != "": return fail(why)
	if c.pools.cooldown("plunge") > 0.0: return fail("cooldown")
	var st: ActorState = game.actor_state(c.id)
	if st == null: return fail("no_body")
	st.arts["plunge"] = true
	if not MovementSolver.plunge(st): return fail("not_airborne")
	c.pools.cooldowns["plunge"] = float(ContentDB.movement("plunge.cooldown_s", 4.0))
	LocalAuthority.announce(st, c.id)
	return ok()

## The Plunge lands: 120% damage and a 0.5 s stun to foes within 60 of the landing, breakables broken (S43).
func resolve_plunge(c, st: ActorState) -> void:
	var at: Dictionary = st.plunge_impact
	st.plunge_impact = {}
	var here := Vector2(float(at.x), float(at.y))
	var radius := float(ContentDB.movement("plunge.radius", 60.0))
	var pv := combat.player_view(c)
	var hitbox := {"x": [-radius, radius], "depth": radius, "alt": ContentDB.movement("combat_bands.melee", [-30, 60])}
	var atk := {"damage_type": "physical", "element": "none", "mult": [float(ContentDB.movement("plunge.mult", 1.2)), float(ContentDB.movement("plunge.mult", 1.2))],
		"range": [1.0, 1.0], "knockback": 0.0, "source": "plunge"}
	for e in combat._enemies_within(here, radius):
		if not CombatAuthority.hit_test(pv, 1, hitbox, combat.enemy_view(e), true): continue
		combat.player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
		if e.alive and not e.is_boss():
			combat.apply_status_to_enemy(e, {"id": "stun", "power": 1.0, "remaining": float(ContentDB.movement("plunge.stun_s", 0.5)), "source": c.id})
	for o in game.world.hittable_objects(pv, 1, hitbox):
		game.world.apply_object_hit(c.id, o)
	emit("system_used", {"actor": c.id, "system": "plunge_strike"})

## Falling Leaf Glide (Qi Kindling 3): Jump held while descending. 2 QI a second while it lasts.
func glide(c, on: bool) -> Dictionary:
	var st: ActorState = game.actor_state(c.id)
	if not on:
		combat.gliding.erase(c.id)
		if st != null: MovementSolver.glide(st, false)
		return ok()
	if not knows_art(c, "glide"): return fail("locked")
	if combat.wounded.has(c.id) or c.pools.blocked("move"): return fail("blocked")
	if st == null: return fail("no_body")
	if c.pools.max_qi <= 0.0 or c.pools.qi < float(ContentDB.movement("glide.qi_per_s", 2.0)) * 0.25: return fail("no_qi", {"text": Tx.t("sim.combat.not_enough_qi_to_glide")})
	st.arts["glide"] = true
	if not MovementSolver.glide(st, true): return fail("not_airborne")
	combat.gliding[c.id] = true
	LocalAuthority.announce(st, c.id)
	return ok()

func is_gliding(actor_id: String) -> bool:
	return combat.gliding.has(actor_id)

func tick_glide(c, delta: float) -> void:
	if not combat.gliding.has(c.id): return
	var st: ActorState = game.actor_state(c.id)
	if st == null or not st.gliding:
		combat.gliding.erase(c.id)
		return
	var cost := float(ContentDB.movement("glide.qi_per_s", 2.0)) * delta * air_qi_mult(c)
	if c.pools.qi <= cost:
		combat.gliding.erase(c.id)
		MovementSolver.glide(st, false)
		return
	combat.apply_resource_change(c.id, "qi", -cost, "glide", 0.0, true)
	_air_distance(c, delta)
