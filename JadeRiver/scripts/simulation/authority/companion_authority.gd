class_name CompanionAuthority
extends Authority
## S26 · Up to two fellow disciples fight beside the player (an offline stand-in
## for a party). They use the same combat rules through AllyBrain, sit when the
## player meditates and are downed (never killed) at 0 HP.

var allies: Dictionary = {}   # companion id -> ally uid in the current room

func intents() -> Array:
	return ["set_active_companions"]

func subscribe() -> void:
	GameEvents.subscribe("room_entered", _on_room_entered, 46)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	if str(intent.type) == "set_active_companions":
		var ids: Array = intent.get("ids", [])
		var active: Array = []
		for id in ids:
			if c.companions.roster.has(id) and active.size() < 2: active.append(id)
		c.companions.active = active
		_spawn_all(c)
		emit("companions_changed", {"actor": c.id})
		return ok()
	return fail("unknown_intent")

func is_companion(id: String) -> bool:
	return id.begins_with("comp:")

func apply_add(actor_id: String, companion: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("companions", companion) or c.companions.roster.has(companion): return
	c.companions.roster.append(companion)
	if c.companions.active.size() < 2: c.companions.active.append(companion)
	emit("companion_joined", {"actor": actor_id, "companion": companion})
	_spawn_all(c)

func _on_room_entered(_p: Dictionary) -> void:
	_spawn_all(game.active())

func _spawn_all(c) -> void:
	if c == null or game.room_rt == null: return
	# Uids restart in every room: only remove entries that really are our companions.
	for id in allies:
		var old: EnemyState = game.room_rt.enemies.get(allies[id])
		if old != null and old.team == "ally" and old.def_id == str(id): game.room_rt.enemies.erase(allies[id])
	allies.clear()
	if game.room_rt.def.get("type", "") == "interior" or game.room_rt.def.get("solo", false): return
	var st: ActorState = game.actor_state(c.id)
	var i := 0
	for id in c.companions.active:
		var def := ContentDB.entry("companions", str(id))
		var a := EnemyState.new()
		a.uid = game.room_rt.uid()
		a.def_id = str(id)
		a.def = {"name": str(def.get("name", id)), "art": {"avatar": def.get("outfit", {})}, "half_width": 14, "height": 88, "ally": true}
		a.team = "ally"
		a.pet_owner = c.id
		a.level = ProgressionRules.level(c)
		a.pools.max_hp = c.pools.max_hp * 0.8
		a.pools.hp = a.pools.max_hp
		a.plane = (st.plane if st else Vector2(c.position.x, c.position.y)) + Vector2(-90 - i * 50, -16 + i * 30)
		a.ai = {"state": "follow", "timer": 0.0, "offset": 90 + i * 50, "depth_offset": -16 + i * 30, "speed": 210, "role": str(def.get("role", "brawler"))}
		a.stats = {"attack": 0.0}
		game.room_rt.enemies[a.uid] = a
		allies[str(id)] = a.uid
		emit("ally_spawned", {"uid": a.uid, "kind": "companion"})
		i += 1

func tick(delta: float) -> void:
	var c = game.active()
	if c == null or game.room_rt == null: return
	for id in allies:
		var a: EnemyState = game.room_rt.enemies.get(allies[id])
		if a == null: continue
		var def := ContentDB.entry("companions", str(id))
		var reach := 300.0 if def.get("role", "") == "archer" else 60.0
		# Healer: mend the player when hurt.
		if def.get("role", "") == "healer" and c.pools.hp < c.pools.max_hp * 0.5 and c.pools.cooldown("comp_heal") <= 0.0:
			game.combat.apply_resource_change(c.id, "hp", c.pools.max_hp * 0.15, "companion_heal")
			c.pools.cooldowns["comp_heal"] = 12.0
			emit("companion_healed", {"actor": c.id, "companion": id})
		AllyBrain.think(game, a, delta, c.stats.value("physical_attack") * 0.35, reach)

## Enemy attacks also hit companions and pets inside the hitbox.
func enemy_strike_companions(e: EnemyState, attack: Dictionary, ev: Dictionary) -> void:
	if game.room_rt == null: return
	var hitbox: Dictionary = attack.get("hitbox", {"x": [0, 40], "depth": 26, "alt": [0, 70]})
	for a in game.room_rt.enemies.values():
		if a.team != "ally" or not a.alive or a.ai.state == "downed" or a.hidden: continue
		var view := {"x": a.plane.x, "y": a.plane.y, "alt": 0.0, "half_width": a.half_width(), "height": a.height()}
		if CombatAuthority.hit_test(ev, e.facing, hitbox, view, attack.get("both_sides", false)):
			var dmg := maxf(1.0, float(e.stats.attack) * float(attack.get("mult", 1.0)) * 0.8)
			a.pools.hp -= dmg
			a.flash = 0.12
			emit("hit_landed", {"attacker": str(e.uid), "target": str(a.uid), "target_kind": "ally", "amount": int(dmg), "type": "physical",
				"crit": false, "element": e.element, "x": a.plane.x, "y": a.plane.y, "alt": a.height()})
			if a.pools.hp <= 0.0:
				a.ai.state = "downed"
				a.ai.timer = 30.0 if a.def_id in allies else 60.0
				a.action_time = 0.0
				emit("companion_downed" if allies.has(a.def_id) else "pet_retreated", {"uid": a.uid, "companion": a.def_id})
