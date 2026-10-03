class_name FieldAuthority
extends Authority
## S28 · Field powers (v1.2). Presence from Will Manifest 1: an aura, level 1-10 trained by use, that presses
## weaker foes in reach by the S12 Pressure contest (slower, weaker blows). A foe with a Presence of its own
## meets yours at a visible boundary, and the harder push presses the other side (FieldRules.clash).
## Presence costs Soul while it is held. Levels and experience live on the cultivator (field_powers).
## The Sphere (Sphere Lord 1): a circle of the strongest combat Dao's element, held for Qi. Once a second it works on
## the foes inside it by its element and the room's terrain; it feeds techniques of its element by a tenth; where it
## overlaps a foe's Sphere the weaker one breaks, and a broken Sphere is a meridian injury (FieldRules.sphere_*).

var on: Dictionary = {}          # actor -> true while the Presence is held
var self_loss: Dictionary = {}   # actor -> output and speed lost to a stronger Presence (0-0.5)
var clashes: Dictionary = {}     # actor -> {enemy, boundary, winner} while two Presences meet
var pressed: Dictionary = {}     # enemy uid -> true while the player's Presence presses it (kill experience)
var spheres: Dictionary = {}     # actor -> true while the Sphere is held
var sphere_cd: Dictionary = {}   # actor -> sim time when a broken Sphere can be raised again
var sphere_t: Dictionary = {}    # actor -> seconds toward the next pulse
var sphere_pulses: Dictionary = {}   # actor -> pulses so far (the Thunder Sphere's every-other shock)

func intents() -> Array:
	return ["toggle_presence", "toggle_sphere"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"toggle_presence": return toggle_presence(c, intent.get("on", null))
		"toggle_sphere": return toggle_sphere(c, intent.get("on", null))
	return fail("unknown_intent")

func subscribe() -> void:
	GameEvents.subscribe("actor_defeated", _on_defeated, 50)
	GameEvents.subscribe("room_entered", func(_p): clashes.clear(); pressed.clear(), 50)
	GameEvents.subscribe("player_gravely_wounded", func(p): _release(str(p.get("actor", "")), "wounded"); _drop_sphere(str(p.get("actor", "")), "wounded"), 50)

# ------------------------------------------------------------------ queries
func powers(c) -> Dictionary:
	return c.cultivator.field_powers.get("presence", {}) if c != null else {}

func presence_level(c) -> int:
	if c == null or not Unlocks.is_unlocked(c.id, "presence"): return 0
	return FieldRules.level_for(float(powers(c).get("xp", 0.0)))

func presence_xp(c) -> float:
	return float(powers(c).get("xp", 0.0))

func is_on(actor_id: String) -> bool:
	return on.has(actor_id)

## The player's Pressure while the Presence is held (0 when it is not).
func pressure_of(c) -> float:
	if c == null or not is_on(c.id): return 0.0
	return FieldRules.pressure(ProgressionRules.level(c), presence_level(c), c.stats.value("pressure"))

func radius_of(c) -> float:
	return FieldRules.radius(presence_level(c))

## Output and speed the player loses to a foe's stronger Presence (combat and movement multiply by 1 - this).
func loss_of(actor_id: String) -> float:
	return float(self_loss.get(actor_id, 0.0))

## Output and speed a foe loses to the player's Presence.
static func enemy_loss(e: EnemyState) -> float:
	return float(e.ai.get("pressed", 0.0))

func clash_of(actor_id: String) -> Dictionary:
	return clashes.get(actor_id, {})

## A foe's own Presence: its Pressure (0 when it has none) and its reach.
static func enemy_pressure(e: EnemyState) -> float:
	var pl := int(e.def.get("presence", 0))
	if pl <= 0: return 0.0
	var will := FieldRules.enemy_will(e.level, e.role, e.elite)
	return FieldRules.pressure(e.level, pl, 0.0, will / (5.0 + float(e.level)))

# ------------------------------------------------------------------ intents
func toggle_presence(c, want) -> Dictionary:
	var turn_on := not is_on(c.id) if want == null else bool(want)
	if not turn_on:
		_release(c.id, "choice")
		return ok({"on": false})
	if not Unlocks.is_unlocked(c.id, "presence"): return fail("locked")
	var vow: String = game.progression.vow_forbids(c, "presence")
	if vow != "": return fail("vow", {"vow": vow})
	if game.combat.is_wounded(c.id): return fail("wounded")
	if c.pools.soul < _soul_cost(c) * 2.0: return fail("soul")
	on[c.id] = true
	if not c.cultivator.field_powers.has("presence"): c.cultivator.field_powers["presence"] = {"xp": 0.0}
	emit("presence_toggled", {"actor": c.id, "on": true, "level": presence_level(c), "reason": "choice"})
	emit("system_used", {"actor": c.id, "system": "presence"})
	return ok({"on": true})

func _release(actor_id: String, reason: String) -> void:
	if not on.has(actor_id): return
	on.erase(actor_id)
	for uid in pressed.keys(): _unpress(uid)
	pressed.clear()
	emit("presence_toggled", {"actor": actor_id, "on": false, "reason": reason})

func _soul_cost(c) -> float:
	return c.pools.max_soul * float(ContentDB.stat_const("presence.soul_per_s_pct", 0.0025))

# ------------------------------------------------------------------ the Sphere
## The Sphere a character would raise: {element, dao, tier, radius, power, domain} from its strongest combat Dao
## (a weapon Dao takes its weapon's nature: the jian's Sword Dao is the Sword Domain). {} when it has none.
func sphere_of(c) -> Dictionary:
	if c == null: return {}
	var k: Dictionary = ContentDB.stat_const("sphere", {})
	var map: Dictionary = k.get("dao_element", {})
	var best := ProgressionRules.strongest_dao(c, func(d: String) -> bool:
		return str(ContentDB.entry("daos", d).get("family", "")) in ["weapon", "element"] or map.has(d))
	if best == "": return {}
	var tier := int(c.cultivator.daos[best].get("tier", 0))
	if tier <= 0: return {}
	var el := str(map.get(best, best))
	var domain := false
	if el == "sword":
		domain = str(StatRules.family(c).get("id", "")) == "jian"
		if not domain: el = "metal"
	return {"element": el, "dao": best, "tier": tier, "domain": domain, "radius": FieldRules.sphere_radius(tier),
		"power": FieldRules.sphere_power(ProgressionRules.level(c), tier, 1.0, c.stats.value("pressure"))}

func sphere_on(actor_id: String) -> bool:
	return spheres.has(actor_id)

## The element a held Sphere lends to the ground under its bearer ("" when none is held).
func sphere_element(c) -> String:
	if c == null or not sphere_on(c.id): return ""
	return str(sphere_of(c).get("element", ""))

## A foe's own Sphere: {element, tier, radius, power}, or {} (none, or broken this fight).
static func enemy_sphere(e: EnemyState) -> Dictionary:
	var sd = e.def.get("sphere", {})
	if not (sd is Dictionary) or sd.is_empty() or e.ai.get("sphere_broken", false): return {}
	var tier := int(sd.get("tier", 1))
	var will := FieldRules.enemy_will(e.level, e.role, e.elite)
	return {"element": str(sd.get("element", e.def.get("element", "none"))), "tier": tier, "radius": FieldRules.sphere_radius(tier),
		"power": FieldRules.sphere_power(e.level, tier, will / (5.0 + float(e.level)))}

func toggle_sphere(c, want) -> Dictionary:
	var turn_on := not sphere_on(c.id) if want == null else bool(want)
	if not turn_on:
		_drop_sphere(c.id, "choice")
		return ok({"on": false})
	if not Unlocks.is_unlocked(c.id, "sphere"): return fail("locked", {"text": Unlocks.locked_text("sphere")})
	if game.combat.is_wounded(c.id): return fail("wounded")
	if game.sim_time < float(sphere_cd.get(c.id, 0.0)):
		return fail("broken", {"text": t("sim.field.sphere_mending") % Tx.span(float(sphere_cd[c.id]) - game.sim_time)})
	var sd := sphere_of(c)
	if sd.is_empty(): return fail("no_dao", {"text": t("sim.field.sphere_no_dao")})
	if c.pools.qi < _sphere_cost(c) * 2.0: return fail("qi")
	spheres[c.id] = true
	sphere_t[c.id] = 0.0
	emit("sphere_toggled", {"actor": c.id, "on": true, "element": sd.element, "tier": sd.tier, "domain": sd.domain, "reason": "choice"})
	emit("system_used", {"actor": c.id, "system": "sphere"})
	return ok({"on": true, "element": sd.element, "domain": sd.domain})

func _drop_sphere(actor_id: String, reason: String) -> void:
	if not spheres.has(actor_id): return
	spheres.erase(actor_id)
	var st: ActorState = game.actor_state(actor_id)
	if st != null: st.frozen_ground = false
	emit("sphere_toggled", {"actor": actor_id, "on": false, "reason": reason})

func _sphere_cost(c) -> float:
	return c.pools.max_qi * float(ContentDB.stat_const("sphere.qi_per_s_pct", 0.004))

## Two Spheres overlap: the weaker breaks. The player's broken Sphere is a meridian injury and a wait to raise it again.
func _sphere_clash(c, e: EnemyState, mine: Dictionary, theirs: Dictionary) -> bool:
	var won := float(mine.power) > float(theirs.power)
	emit("sphere_clash", {"actor": c.id, "enemy": e.uid, "name": e.display_name(), "winner": "you" if won else "foe",
		"element": str(mine.element), "foe_element": str(theirs.element)})
	if won:
		e.ai["sphere_broken"] = true
		game.enemies.stagger(e, 1.5)
		return true
	var k: Dictionary = ContentDB.stat_const("sphere", {})
	sphere_cd[c.id] = game.sim_time + float(k.get("break_cooldown_s", 30))
	game.progression.apply_injury(c.id, "meridian", int(k.get("injury_severity", 1)))
	_drop_sphere(c.id, "broken")
	return false

## One tick of a held Sphere: Qi, the pulse on the foes inside, the bearer's gifts, and clashes.
func _sphere_tick(c, delta: float, at: Vector2) -> void:
	if not sphere_on(c.id): return
	var cost := _sphere_cost(c) * delta
	if c.pools.qi < cost:
		_drop_sphere(c.id, "qi")
		return
	game.combat.apply_resource_change(c.id, "qi", -cost, "sphere", 0.0, true)
	var sd := sphere_of(c)
	if sd.is_empty():
		_drop_sphere(c.id, "no_dao")
		return
	var k: Dictionary = ContentDB.stat_const("sphere", {})
	var fx := FieldRules.sphere_effects(str(sd.element), game.room_rt.def.get("terrain", []))
	var st: ActorState = game.actor_state(c.id)
	if st != null: st.frozen_ground = bool(fx.get("freeze", false))
	sphere_t[c.id] = float(sphere_t.get(c.id, 0.0)) + delta
	var tick_s := float(k.get("tick_s", 1.0))
	if float(sphere_t[c.id]) < tick_s: return
	sphere_t[c.id] = float(sphere_t[c.id]) - tick_s
	sphere_pulses[c.id] = int(sphere_pulses.get(c.id, 0)) + 1
	var last := tick_s * 1.3
	# The bearer's gifts, refreshed each pulse.
	if float(fx.get("speed", 0.0)) > 0.0: game.combat.apply_buff(c.id, {"stat": "move_speed", "op": "pct_add", "value": float(fx.speed), "duration": last, "source": "sphere"}, "sphere")
	if float(fx.get("crit", 0.0)) > 0.0: game.combat.apply_buff(c.id, {"stat": "crit_chance", "op": "flat", "value": float(fx.crit), "duration": last, "source": "sphere"}, "sphere")
	if float(fx.get("pen", 0.0)) > 0.0: game.combat.apply_buff(c.id, {"stat": "penetration", "op": "flat", "value": float(fx.pen), "duration": last, "source": "sphere"}, "sphere")
	if float(fx.get("regen_pct", 0.0)) > 0.0: game.combat.apply_resource_change(c.id, "hp", c.pools.max_hp * float(fx.regen_pct), "sphere", 0.0, true)
	var shocked := false
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden: continue
		var d: float = e.plane.distance_to(at)
		var theirs := enemy_sphere(e)
		if not theirs.is_empty() and d <= float(sd.radius) + float(theirs.radius):
			if not _sphere_clash(c, e, sd, theirs): return
		if d > float(sd.radius): continue
		if float(fx.get("slow", 0.0)) > 0.0: game.combat.apply_status_to_enemy(e, {"id": "slow", "power": float(fx.slow), "remaining": last, "source": c.id})
		if fx.get("vulnerable", false): game.combat.apply_status_to_enemy(e, {"id": "vulnerable", "power": 1.0, "remaining": last, "source": c.id})
		if float(fx.get("root_s", 0.0)) > 0.0: game.combat.apply_status_to_enemy(e, {"id": "root", "power": 1.0, "remaining": float(fx.root_s), "source": c.id})
		if float(fx.get("will_down", 0.0)) > 0.0: e.ai["will_down"] = float(fx.will_down)
		if float(fx.get("burn_pct", 0.0)) > 0.0: game.combat.sphere_strike(c, e, str(sd.element), float(fx.burn_pct) * 20.0, "burn")
		if float(fx.get("cut_pct", 0.0)) > 0.0: game.combat.sphere_strike(c, e, str(sd.element), float(fx.cut_pct), "cut")
		if float(fx.get("shock_pct", 0.0)) > 0.0 and not shocked and int(sphere_pulses[c.id]) % maxi(1, int(fx.get("shock_every", 2))) == 0:
			game.combat.sphere_strike(c, e, "thunder", float(fx.shock_pct), "shock")
			game.combat.apply_status_to_enemy(e, {"id": "shock", "power": 1.0, "remaining": 0.4, "source": c.id})
			shocked = true
	emit("sphere_pulse", {"actor": c.id, "element": str(sd.element), "radius": float(sd.radius), "x": at.x, "y": at.y})

# ------------------------------------------------------------------ tick
func tick(delta: float) -> void:
	var c = game.active()
	if c == null or game.room_rt == null: return
	var holding := is_on(c.id)
	if holding:
		var cost := _soul_cost(c) * delta
		if c.pools.soul < cost:
			_release(c.id, "soul")
			holding = false
		else:
			game.combat.apply_resource_change(c.id, "soul", -cost, "presence", 0.0, true)
	var st: ActorState = game.actor_state(c.id)
	var at: Vector2 = st.plane if st != null else Vector2(float(c.position.x), float(c.position.y))
	_sphere_tick(c, delta, at)
	var p := pressure_of(c)
	var r := radius_of(c) if holding else 0.0
	var will: float = c.stats.value("will")
	var worst := 0.0
	var meet := {}
	var meet_d := INF
	var now_pressed := {}
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden:
			_unpress_enemy(e)
			continue
		var d: float = e.plane.distance_to(at)
		var ep := enemy_pressure(e)
		var ew := FieldRules.enemy_will(e.level, e.role, e.elite) * (1.0 - float(e.ai.get("will_down", 0.0)))
		var loss_e := 0.0
		if ep > 0.0 and d <= FieldRules.radius(int(e.def.get("presence", 0))) + r:
			var k := FieldRules.clash(p, will, ep, ew)
			worst = maxf(worst, float(k.loss_a))
			loss_e = float(k.loss_b)
			if holding and d < meet_d:
				meet_d = d
				var winner := "even"
				if float(k.loss_a) > 0.0: winner = "foe"
				elif float(k.loss_b) > 0.0: winner = "you"
				meet = {"enemy": e.uid, "name": e.display_name(), "boundary": float(k.boundary), "winner": winner,
					"x": lerpf(at.x, e.plane.x, float(k.boundary)), "y": lerpf(at.y, e.plane.y, float(k.boundary))}
		elif holding and d <= r:
			loss_e = CombatRules.pressure_loss(p, ew)
		if loss_e > 0.0:
			e.ai["pressed"] = loss_e
			now_pressed[e.uid] = true
		else:
			_unpress_enemy(e)
	for uid in pressed.keys():
		if not now_pressed.has(uid): _unpress(uid)
	pressed = now_pressed
	if worst > 0.0: self_loss[c.id] = worst
	else: self_loss.erase(c.id)
	_track_clash(c, meet)
	if holding and (not now_pressed.is_empty() or not meet.is_empty()):
		var x: Dictionary = ContentDB.stat_const("presence", {})
		var gain := float(x.get("xp_per_s", 1.0)) * delta * (float(x.get("clash_xp_mult", 2.0)) if not meet.is_empty() else 1.0)
		apply_presence_xp(c.id, gain, "use")

func _track_clash(c, meet: Dictionary) -> void:
	var before: Dictionary = clashes.get(c.id, {})
	if meet.is_empty():
		if not before.is_empty():
			clashes.erase(c.id)
			emit("presence_clash_ended", {"actor": c.id, "enemy": before.enemy})
		return
	clashes[c.id] = meet
	if before.is_empty() or before.enemy != meet.enemy or str(before.winner) != str(meet.winner):
		emit("presence_clash", {"actor": c.id, "enemy": meet.enemy, "name": meet.name, "winner": meet.winner})

func _unpress_enemy(e: EnemyState) -> void:
	e.ai.erase("pressed")

func _unpress(uid) -> void:
	if game.room_rt == null: return
	var e = game.room_rt.enemies.get(uid)
	if e != null: e.ai.erase("pressed")

func _on_defeated(p: Dictionary) -> void:
	var c = game.active()
	if c == null or not is_on(c.id) or str(p.get("victim_kind", "")) != "enemy": return
	for uid in pressed:
		if str(uid) == str(p.get("victim", "")):
			apply_presence_xp(c.id, float(ContentDB.stat_const("presence.kill_xp", 3.0)), "kill")
			return

## The public command for Presence experience (use, kills, trainers and tests); announces a new level.
func apply_presence_xp(actor_id: String, amount: float, source: String) -> void:
	var c = game.character(actor_id)
	if c == null or amount <= 0.0 or not Unlocks.is_unlocked(actor_id, "presence"): return
	var before := presence_level(c)
	var fp: Dictionary = c.cultivator.field_powers.get("presence", {"xp": 0.0})
	fp.xp = float(fp.get("xp", 0.0)) + amount
	c.cultivator.field_powers["presence"] = fp
	var after := presence_level(c)
	if after > before: emit("presence_leveled", {"actor": actor_id, "level": after, "source": source})
