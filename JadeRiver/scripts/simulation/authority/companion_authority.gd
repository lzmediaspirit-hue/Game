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
		a.def = {"name": str(def.get("name", id)), "art": {"avatar": def.get("outfit", {})}, "half_width": 14, "height": 88, "ally": true,
			"movement": {"jump": 530, "climb": true, "fly": false, "drop": true}}
		a.team = "ally"
		a.pet_owner = c.id
		a.level = ProgressionRules.level(c)
		a.pools.max_hp = c.pools.max_hp * 0.8
		a.pools.hp = a.pools.max_hp
		a.plane = (st.plane if st else Vector2(c.position.x, c.position.y)) + Vector2(-90 - i * 50, -16 + i * 30)
		AllyBrain.settle(game, a, st)
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
		var was_down: bool = a.ai.state == "downed"
		AllyBrain.think(game, a, delta, c.stats.value("physical_attack") * 0.35, reach)
		if was_down and a.ai.state != "downed":
			emit("companion_revived", {"actor": c.id, "uid": a.uid, "companion": str(id)})

## Paired cultivation (v1.1, Sage 1): meditating beside a fellow disciple who sits with you
## breathes the Qi between you both. One partner is enough; a downed one cannot pair.
func paired_bonus(c) -> float:
	if c == null or not c.cultivator.meditating or not Unlocks.is_unlocked(c.id, "paired_cultivation") or game.room_rt == null: return 0.0
	for id in allies:
		var a: EnemyState = game.room_rt.enemies.get(allies[id])
		if a != null and a.ai.get("state", "") != "downed": return float(ContentDB.curve("paired_cultivation", 0.15))
	return 0.0

## Is this ally in the room a fellow disciple (not a spirit animal)?
func is_companion_ally(a: EnemyState) -> bool:
	return allies.has(a.def_id) and int(allies[a.def_id]) == a.uid

## Combat brought a fellow disciple to 0 HP: downed, never killed; up again in 30 s.
func apply_down(a: EnemyState) -> void:
	a.ai.state = "downed"
	a.ai.timer = 30.0
	a.action_time = 0.0
	emit("companion_downed", {"actor": game.active_id, "uid": a.uid, "companion": a.def_id})
