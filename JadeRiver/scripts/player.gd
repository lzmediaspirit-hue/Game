extends Node2D
## Local input sampling and animation for the playing character. Movement runs
## through LocalAuthority (validated, sequenced commands). In room mode every
## action is an intent to Game; attack timing, meditation and resources come from
## the authorities and the avatar only follows them.
const Avatar = preload("res://scripts/avatar.gd")
var world: Node2D
var actor_id := ""                 # "" = legacy regression mode (no Game authority)
var state = ActorState.new()
var authority: LocalAuthority
var command_sequence = 0
var plane: Vector2:
	get: return state.plane
	set(value): state.plane = value
var altitude: float:
	get: return state.altitude
	set(value): state.altitude = value
var air_base: float:
	get: return state.air_base
	set(value): state.air_base = value
var jump_height: float:
	get: return maxf(0, altitude - (surface.height_at(plane) if surface else air_base))
var vertical_speed: float:
	get: return state.vertical_speed
	set(value): state.vertical_speed = value
var surface: WalkSurface:
	get: return state.surface
	set(value): state.surface = value
var velocity: Vector2:
	get: return state.velocity
	set(value): state.velocity = value
var movement = Vector2.ZERO
var speed = 205.0
var attack_time = 0.0
const COMBOS = {"swing": ["swing_1", "swing_2", "swing_3"], "attack": ["thrust_1", "thrust_2", "thrust_3"], "punch": ["punch_1", "punch_2", "punch_3"]}
const COMBO_WINDOW = 0.45
var combo_index = -1
var combo_queue = 0
var combo_window = 0.0
var attack_duration = 0.0
var attack_weapon = ""
var bow_release_time = -1.0
var _meditating = false
var meditating: bool:
	get: return Game.character(actor_id).cultivator.meditating if bound() else _meditating
	set(value): _meditating = value
var _qi = 100.0
var _hp = 100.0
var qi: float:
	get: return Game.character(actor_id).pools.qi if bound() else _qi
	set(value): _qi = value
var hp: float:
	get: return Game.character(actor_id).pools.hp if bound() else _hp
	set(value): _hp = value
var facing = 1
var avatar: Node2D
var outfit: Dictionary
var joystick_engaged = false
var drag_seconds = 0.0
var sprinting = false
var last_axis = Vector2.ZERO
var sprint_direction = Vector2.ZERO
var channel_time := 0.0             # gather/mine/lift channels driven by the HUD
var channel_action := ""
signal attack_started(family: String, plane_position: Vector2, elevation: float, direction: int)
signal arrow_released(plane_position: Vector2, elevation: float, direction: int)

func bound() -> bool:
	return actor_id != "" and Game.character(actor_id) != null

func _ready():
	if authority == null: authority = LocalAuthority.new(state, world.geometry)
	avatar = Avatar.new()
	avatar.outfit = outfit.duplicate(true)
	for k in ["hat", "cape"]:
		if not avatar.outfit.has(k): avatar.outfit[k] = "none"
	avatar.scale = Vector2.ONE
	add_child(avatar)
	if bound(): set_physics_process(false)

# ------------------------------------------------------------------ actions
func jump():
	if bound():
		if Game.combat.is_wounded(actor_id) or Game.character(actor_id).pools.blocked("move"): return
		if not Unlocks.is_unlocked(actor_id, "jump"): return
		if meditating: Game.submit({"type": "stop_meditation", "reason": "jump"})
	if authority.jump():
		_meditating = false
		attack_time = 0
		reset_combo()
		avatar.externally_timed = false
		bow_release_time = -1
		avatar.play("jump")
		avatar.elapsed = 0
		avatar.playback_speed = 1
		if bound(): Audio.play("jump")

func attack():
	if bound():
		var r := Game.submit({"type": "basic_attack", "facing": facing})
		if r.ok and r.has("facing"): facing = int(r.facing)
		return
	if attack_weapon != "" and attack_weapon != str(avatar.outfit.weapon):
		attack_time = 0
		bow_release_time = -1
		reset_combo()
	if attack_time > 0:
		if combo_index >= 0: combo_queue = mini(combo_queue + 1, 2 - combo_index)
		return
	_meditating = false
	if avatar.outfit.weapon == "bow":
		reset_combo()
		begin_attack("bow")
	else:
		combo_index = combo_index + 1 if combo_window > 0 and combo_index < 2 else 0
		begin_attack(combo_action())

func use_technique(slot: int) -> Dictionary:
	var r := Game.submit({"type": "use_technique", "slot": slot, "facing": facing})
	if r.ok and r.has("facing"): facing = int(r.facing)
	return r

func combo_action() -> String:
	return COMBOS[Wardrobe.attack_for(avatar.outfit)][combo_index]

func reset_combo():
	combo_index = -1
	combo_queue = 0
	combo_window = 0

func begin_attack(family: String):
	var spec = Wardrobe.parts._actions[family]
	attack_duration = float(spec.frames) / spec.fps
	attack_time = attack_duration
	attack_weapon = str(avatar.outfit.weapon)
	combo_window = 0
	reset_sprint()
	bow_release_time = 0.55 if family == "bow" else -1.0
	avatar.hide_bow_arrow = false
	avatar.play(family)
	avatar.elapsed = 0
	avatar.externally_timed = true
	avatar.playback_speed = 1
	attack_started.emit(family, plane, altitude, facing)

func advance_attack(delta: float):
	var remaining = delta
	while remaining > 0 and attack_time > 0:
		var consumed = minf(remaining, attack_time)
		attack_time = maxf(0, attack_time - consumed)
		remaining -= consumed
		avatar.elapsed = attack_duration - attack_time
		if bow_release_time >= 0:
			bow_release_time -= consumed
			if bow_release_time <= 0:
				bow_release_time = -1
				avatar.hide_bow_arrow = true
				arrow_released.emit(plane, altitude, facing)
		if attack_time <= 0:
			if combo_queue > 0 and combo_index < 2:
				combo_queue -= 1
				combo_index += 1
				begin_attack(combo_action())
			else:
				combo_window = COMBO_WINDOW if combo_index in [0, 1] else 0.0
				avatar.externally_timed = false
	if attack_time <= 0:
		combo_window = maxf(0, combo_window - remaining)
		if combo_window <= 0: reset_combo()

func meditate():
	if bound():
		var r := Game.submit({"type": "toggle_meditation"})
		if not r.ok and r.has("text") and world and world.fx:
			world.fx.add("text", position + Vector2(0, -130), {"text": str(r.text), "color": UiKit.MIST, "size": 18, "dur": 1.6})
		return
	if surface != null and attack_time <= 0:
		reset_combo()
		_meditating = not _meditating

func reset_sprint():
	drag_seconds = 0
	sprinting = false
	sprint_direction = Vector2.ZERO

# ------------------------------------------------------------------ simulation step
func keyboard_axis() -> Vector2:
	return Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))

func _physics_process(delta):
	step(delta, (keyboard_axis() + movement).limit_length())

## Room mode: called by the world before Game.tick so movement runs first (Part 4 ordering).
func physics_step(delta: float) -> void:
	var axis: Vector2 = (keyboard_axis() + movement).limit_length()
	var c = Game.character(actor_id)
	if c != null and c.pools.has_status("confusion"): axis = -axis
	if Input.is_physical_key_pressed(KEY_SHIFT) and absf(axis.x) > 0.12: drag_seconds = maxf(drag_seconds, 2.01)
	step(delta, axis)

func step(delta: float, axis: Vector2):
	if not is_finite(delta) or delta <= 0 or delta > 3.0 or not axis.is_finite(): return
	axis = axis.limit_length()
	last_axis = axis
	if not bound():
		_legacy_step(delta, axis)
		return
	var c = Game.character(actor_id)
	var tl: Dictionary = Game.combat.timeline(actor_id)
	var busy: bool = Game.combat.is_busy(actor_id)
	var wounded: bool = Game.combat.is_wounded(actor_id)
	if axis.length() > 0.12 and meditating:
		if int(c.cultivator.meridians.get("agility", 0)) < 100 or channel_time > 1.0:
			Game.submit({"type": "stop_meditation", "reason": "moved"})
	if axis.length() > 0.12: channel_time = 0.0
	if wounded: axis = Vector2.ZERO
	if axis.x != 0 and not busy: facing = 1 if axis.x > 0 else -1
	if busy: facing = int(tl.facing)
	if absf(axis.x) > 0.12 and not busy and not meditating:
		var horizontal := Vector2(signf(axis.x), 0)
		if sprint_direction != horizontal:
			reset_sprint()
			sprint_direction = horizontal
		drag_seconds += delta
		sprinting = drag_seconds > float(ContentDB.stat_const("move.sprint_after_s", 2.0))
	else:
		reset_sprint()
	speed = c.stats.value("move_speed") if c.stats.value("move_speed") > 0 else 205.0
	var factor: float = Game.combat.move_factor(actor_id)
	if sprinting: factor *= float(ContentDB.stat_const("move.sprint", 1.7))
	factor *= _area_factor()
	var forced: Dictionary = Game.combat.forced_motion(actor_id)
	command_sequence += 1
	if not forced.is_empty():
		var v: Vector2 = forced.velocity
		authority.move(command_sequence, v.normalized(), delta, v.length())
	else:
		authority.move(command_sequence, axis if not meditating else Vector2.ZERO, delta, speed * factor)
	if absf(velocity.x) < 5: reset_sprint()
	if altitude < -250: world.recover_to_safe()
	_animate(c, tl, busy, wounded)
	sync_visual()

func _area_factor() -> float:
	if world == null or not world.room_mode or surface == null: return 1.0
	for area in world.room_def.get("areas", []):
		if str(area.get("kind", "")) != "shallows": continue
		var r: Array = area.rect
		if Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])).has_point(plane) and altitude < 1.0:
			return float(area.get("speed", ContentDB.stat_const("move.shallows_factor", 0.7)))
	return 1.0

func _animate(c, tl: Dictionary, busy: bool, wounded: bool) -> void:
	avatar.facing = facing
	avatar.playback_speed = 1.7 if sprinting and surface != null else 1.0
	if wounded:
		avatar.externally_timed = false
		avatar.play("meditate")
		modulate = Color(0.6, 0.6, 0.7)
		return
	modulate = Color(1, 1, 1, 0.55 + 0.45 * float(int(Time.get_ticks_msec() / 80) % 2)) if c.pools.invulnerable > 0.0 or c.pools.has_status("spawn_protection") else Color.WHITE
	if busy and str(tl.action) != "":
		var action := str(tl.action)
		if not Wardrobe.parts._actions.has(action): action = "punch_1"
		if avatar.action != action: avatar.play(action)
		var spec: Dictionary = Wardrobe.parts._actions[action]
		avatar.externally_timed = true
		avatar.elapsed = clampf(float(tl.t) / maxf(0.01, float(tl.duration)), 0.0, 0.999) * float(spec.frames) / float(spec.fps)
		avatar.hide_bow_arrow = action == "bow" and float(tl.t) >= float(tl.hit_at)
		return
	avatar.externally_timed = false
	if channel_action != "" and channel_time > 0.0:
		avatar.play({"gather": "punch", "mine": "swing", "lift": "attack", "fish": "idle"}.get(channel_action, "idle"))
		return
	avatar.play("meditate" if meditating else ("jump" if surface == null else ("walk" if velocity.length() > 5 else "idle")))

func _legacy_step(delta: float, axis: Vector2) -> void:
	if attack_time > 0 and attack_weapon != str(avatar.outfit.weapon):
		attack_time = 0
		bow_release_time = -1
		reset_combo()
	advance_attack(delta)
	if attack_time <= 0: avatar.externally_timed = false
	if axis.length() > 0.12: _meditating = false
	if axis.x != 0 and attack_time <= 0: facing = 1 if axis.x > 0 else -1
	if absf(axis.x) > 0.12 and attack_time <= 0 and not _meditating:
		var horizontal = Vector2(signf(axis.x), 0)
		if sprint_direction != horizontal:
			reset_sprint()
			sprint_direction = horizontal
		drag_seconds += delta
		sprinting = drag_seconds > 2.0
	else: reset_sprint()
	var factor = 0.3 if attack_time > 0 else (1.7 if sprinting else 1.0)
	command_sequence += 1
	authority.move(command_sequence, axis if not _meditating else Vector2.ZERO, delta, speed * factor)
	if absf(velocity.x) < 5: reset_sprint()
	if altitude < -250: world.recover_to_safe()
	if _meditating: _qi = minf(100, _qi + 12 * delta)
	avatar.facing = facing
	avatar.playback_speed = 1.7 if sprinting and surface != null else 1.0
	if attack_time <= 0: avatar.play("meditate" if _meditating else ("jump" if surface == null else ("walk" if velocity.length() > 5 else "idle")))
	sync_visual()

func sync_visual():
	position = Vector2(plane.x, plane.y - altitude).snapped(Vector2(2, 2))
	z_index = world.geometry.render_depth(state)
	queue_redraw()

func _draw():
	if meditating: draw_arc(Vector2(0, -4), 28, 0, TAU, 24, Color(0.4, 0.85, 0.76, 0.4), 2, false)
	if bound():
		var tl: Dictionary = Game.combat.timeline(actor_id)
		if tl.guard:
			draw_arc(Vector2(facing * 18, -48), 30, -1.2 if facing > 0 else PI - 1.2 + 0.4, 1.2 if facing > 0 else PI + 1.2 - 0.4, 12, Color(UiKit.PALE_GOLD, 0.7), 3)
