class_name FieldAuthority
extends Authority
## S28 · Field powers (v1.2). Presence from Will Manifest 1: an aura, level 1-10 trained by use, that presses
## weaker foes in reach by the S12 Pressure contest (slower, weaker blows). A foe with a Presence of its own
## meets yours at a visible boundary, and the harder push presses the other side (FieldRules.clash).
## Presence costs Soul while it is held. Levels and experience live on the cultivator (field_powers).

var on: Dictionary = {}          # actor -> true while the Presence is held
var self_loss: Dictionary = {}   # actor -> output and speed lost to a stronger Presence (0-0.5)
var clashes: Dictionary = {}     # actor -> {enemy, boundary, winner} while two Presences meet
var pressed: Dictionary = {}     # enemy uid -> true while the player's Presence presses it (kill experience)

func intents() -> Array:
	return ["toggle_presence"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"toggle_presence": return toggle_presence(c, intent.get("on", null))
	return fail("unknown_intent")

func subscribe() -> void:
	GameEvents.subscribe("actor_defeated", _on_defeated, 50)
	GameEvents.subscribe("room_entered", func(_p): clashes.clear(); pressed.clear(), 50)
	GameEvents.subscribe("player_gravely_wounded", func(p): _release(str(p.get("actor", "")), "wounded"), 50)

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
		var ew := FieldRules.enemy_will(e.level, e.role, e.elite)
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
