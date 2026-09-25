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
var fly_up := false                 # held Jump while flying (touch); Space on the keyboard
var fly_down := false               # held Guard while flying (touch); K on the keyboard
var kick_t := 0.0                   # Wall-Step: the body is pushed away from the wall for a moment
var kick_dir := 0
var climb_hold := 0.0               # S43: seconds the joystick has been held toward a ladder
var jump_held := false              # S43: the Jump button is down (touch); Space on the keyboard
var hold_spent := false             # this press already started a glide or a flight
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
		# S43 rule 5: a jump lets go of a ladder, rope or vine, sideways with the joystick.
		if not state.climbing.is_empty():
			authority.release_climb(int(signf(last_axis.x)), true)
			avatar.play("jump")
			avatar.elapsed = 0
			Audio.play("jump")
			return
		# S43 rule 3: joystick toward the camera + Jump drops through the platform underfoot.
		if surface != null and last_axis.y >= 0.7 and absf(last_axis.x) < 0.3 and authority.drop_through():
			avatar.play("jump")
			return
		# Wall-Step (S43): in the air, pushing into a wall face, kick off it (three kicks per airtime).
		if surface == null and not state.flying:
			var side: int = authority.wall_step(int(signf(last_axis.x)))
			if side != 0:
				kick_dir = -side
				kick_t = 0.2
				facing = kick_dir
				avatar.play("jump")
				avatar.elapsed = 0
				Audio.play("jump")
				return
		hold_spent = false   # a new press: holding it may glide or fly once it starts to fall (S43)
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

func take_off(quiet := false) -> bool:
	var r := Game.submit({"type": "start_flight"})
	if not r.get("ok", false):
		if r.has("text") and not quiet: world.fx.add("text", position + Vector2(0, -130), {"text": str(r.text), "color": UiKit.MIST, "size": 18, "dur": 1.6})
		return false
	authority.fly(true, float(r.climb), float(r.ceiling))
	Audio.play("jump")
	return true

## S43: Jump held while descending. From Cloud Stride 1 (where flight is allowed and QI holds) the body takes
## to the air; otherwise Falling Leaf Glide slows the fall. Letting go ends a glide.
func _hold_jump(c) -> void:
	var holding := jump_held or Input.is_physical_key_pressed(KEY_SPACE)
	if surface != null or not state.climbing.is_empty() or state.flying or state.plunging:
		if state.gliding and surface != null: Game.submit({"type": "glide", "on": false})
		return
	if not holding:
		if state.gliding: Game.submit({"type": "glide", "on": false})
		return
	if hold_spent or state.vertical_speed >= 0.0 or state.gliding: return
	hold_spent = true
	if Unlocks.is_unlocked(actor_id, "flight") and Game.combat.flight_allowed(actor_id) and take_off(true): return
	Game.submit({"type": "glide", "on": true})

func land_from_flight(reason: String) -> void:
	if state.flying: authority.fly(false)
	if bound() and Game.combat.is_flying(actor_id): Game.submit({"type": "stop_flight", "reason": reason})

func attack():
	if bound():
		# S43 Plunge: joystick toward the camera + Attack in the air.
		if surface == null and not state.flying and state.climbing.is_empty() and last_axis.y >= 0.7 and absf(last_axis.x) < 0.3:
			var pr := Game.submit({"type": "plunge"})
			if pr.get("ok", false):
				avatar.play("jump")
				Audio.play("dodge")
				return
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
	if emote_time > 0.0: emote_time -= delta
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
	var shallow: bool = surface != null and not world.geometry.volume_at(plane, altitude, "water_shallow").is_empty()
	if absf(axis.x) > 0.12 and not busy and not meditating and not shallow:
		var horizontal := Vector2(signf(axis.x), 0)
		if sprint_direction != horizontal:
			reset_sprint()
			sprint_direction = horizontal
		drag_seconds += delta
		sprinting = drag_seconds > float(ContentDB.stat_const("move.sprint_after_s", 2.0))
	else:
		reset_sprint()
	speed = c.stats.value("move_speed") if c.stats.value("move_speed") > 0 else 205.0
	var factor: float = Game.combat.move_factor(actor_id) * Game.pets.mount_speed(c)
	if sprinting: factor *= float(ContentDB.stat_const("move.sprint", 1.7))
	state.sprinting = sprinting
	var forced: Dictionary = Game.combat.forced_motion(actor_id)
	_sync_arts(c)
	var kick_speed := 0.0
	if kick_t > 0.0:
		# A Wall-Step kick carries the body 90 units away from the wall over 0.2 s (S43).
		kick_t -= delta
		axis = Vector2(kick_dir, axis.y * 0.3)
		kick_speed = MovementSolver.WALL_KICK_SPEED
	# S43 rule 5: hold toward a ladder's top (up at its foot, down at its top) for 0.3 s to climb on.
	if not state.climbing.is_empty():
		command_sequence += 1
		authority.move(command_sequence, Vector2(0, axis.y), delta, 205.0)
		climb_hold = 0.0
		_animate(c, tl, busy, wounded)
		sync_visual()
		return
	var near_climb: Dictionary = world.geometry.climbable_near(plane, altitude) if surface != null and not busy else {}
	if not near_climb.is_empty(): near_climb.speed_bonus = c.stats.value("climb_speed")
	var toward: bool = (axis.y < -0.7 and not near_climb.get("from_top", false)) or (axis.y > 0.7 and near_climb.get("from_top", false))
	if not near_climb.is_empty() and toward and absf(axis.x) < 0.3:
		climb_hold += delta
		if climb_hold >= 0.3:
			var open: Dictionary = Game.world.climbable_open(c, near_climb)
			if not open.get("ok", false):
				climb_hold = -1.0   # say it once per hold
				world.fx.add("text", position + Vector2(0, -130), {"text": str(open.get("text", "")), "color": UiKit.MIST, "size": 18, "dur": 1.8})
			elif authority.climb(near_climb):
				climb_hold = 0.0
				sync_visual()
				return
	else:
		climb_hold = 0.0
	if state.flying:
		# Combat stops paying (no QI, wounded, a new room): the body falls. Landing ends it too.
		if not Game.combat.is_flying(actor_id): authority.fly(false)
		var up := fly_up or Input.is_physical_key_pressed(KEY_SPACE)
		var down := fly_down or Input.is_physical_key_pressed(KEY_K)
		authority.set_climb(float(up) - float(down))
	_hold_jump(c)
	command_sequence += 1
	# Gusts and currents (S17) add their push to walking; a meditating body is anchored.
	var drift: Vector2 = Game.world.hazard_drift(actor_id) if not meditating and not wounded else Vector2.ZERO
	if not forced.is_empty():
		var v: Vector2 = forced.velocity
		authority.move(command_sequence, v.normalized(), delta, v.length())
	elif drift != Vector2.ZERO:
		var walk: Vector2 = axis.limit_length() * speed * factor + drift
		authority.move(command_sequence, walk.normalized(), delta, walk.length())
	elif kick_speed > 0.0:
		authority.move(command_sequence, Vector2(kick_dir, 0), delta, kick_speed)
	else:
		authority.move(command_sequence, axis if not meditating else Vector2.ZERO, delta, speed * factor)
	if absf(velocity.x) < 5: reset_sprint()
	if not state.flying and Game.combat.is_flying(actor_id): Game.submit({"type": "stop_flight", "reason": "landed"})
	if altitude < world.geometry.void_altitude: world.recover_to_safe()
	elif state.drowned:
		# Deep water without the art (S43 rule 6): back to the last safe spot.
		state.drowned = false
		state.water = {}
		state.sink_depth = 0.0
		world.recover_to_safe()
	_animate(c, tl, busy, wounded)
	_ride(c)
	sync_visual()

## S43: the movement arts this character knows reach the body's solver (double jump, Wall-Step, drop, mantle, climb).
func _sync_arts(c) -> void:
	state.arts = {"drop_through": Unlocks.is_unlocked(actor_id, "jump"), "mantle": true, "climb": true}
	for sa in c.cultivator.secret_arts:
		var art := str(ContentDB.entry("secret_arts", str(sa)).get("movement_art", ""))
		if art != "": state.arts[art] = true

## A hit knocks the body off a ladder, rope or vine (S43 rule 5).
func knock_off_climb() -> void:
	if not state.climbing.is_empty(): authority.release_climb(-facing, false)

## S22 Mount role: the animal is drawn under the rider, who stands on its back.
var mount_sprite: CreatureSprite
func _ride(c) -> void:
	var m: Dictionary = Game.pets.mount_of(c)
	if m.is_empty():
		if mount_sprite:
			mount_sprite.queue_free()
			mount_sprite = null
			avatar.position = Vector2.ZERO
		return
	if mount_sprite == null:
		mount_sprite = CreatureSprite.new()
		add_child(mount_sprite)
		move_child(mount_sprite, 0)
	mount_sprite.creature_id = str(m.get("art", ""))
	mount_sprite.scale = Vector2.ONE * float(m.get("scale", 1.0))
	mount_sprite.position = Vector2(0, -float(m.get("lift", 0)))
	mount_sprite.facing = facing
	mount_sprite.play("walk" if velocity.length() > 5 and surface != null else "idle")
	avatar.position = Vector2(0, -float(m.get("saddle", 40)))
	if str(avatar.action) in ["walk", "jump"]: avatar.play("idle")   # the rider stands; the animal walks

var emote: Dictionary = {}   # the emote being played (S34) and its time left
var emote_time := 0.0

func play_emote(em: Dictionary) -> void:
	emote = em
	emote_time = float(em.get("seconds", 1.6))

## An emote holds its pose until it ends or the player moves, acts or rides.
func _emote_pose(c, busy: bool) -> bool:
	if emote_time > 0.0 and (busy or velocity.length() > 5.0 or meditating or not Game.pets.mount_of(c).is_empty()): emote_time = 0.0
	if emote_time <= 0.0:
		if not emote.is_empty():
			emote = {}
			avatar.rotation = 0.0
			avatar.position.y = 0.0
		return false
	var pose := str(emote.get("pose", "idle"))
	if not Wardrobe.parts._actions.has(pose): pose = "idle"
	avatar.play(pose)
	var t := float(emote.get("seconds", 1.6)) - emote_time
	avatar.rotation = float(emote.get("tilt", 0.0)) * facing * sin(clampf(t / 0.5, 0.0, 1.0) * PI * 0.5)
	if emote.get("bob", false): avatar.position.y = -absf(sin(t * 9.0)) * 5.0
	return true

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
	if state.flying:
		avatar.play("idle")
		return
	if state.gliding or state.plunging or state.dash_hold > 0.0:
		avatar.play("jump")
		return
	if _emote_pose(c, busy): return
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
	if altitude < world.geometry.void_altitude: world.recover_to_safe()
	if _meditating: _qi = minf(100, _qi + 12 * delta)
	avatar.facing = facing
	avatar.playback_speed = 1.7 if sprinting and surface != null else 1.0
	if attack_time <= 0: avatar.play("meditate" if _meditating else ("jump" if surface == null else ("walk" if velocity.length() > 5 else "idle")))
	sync_visual()

func sync_visual():
	# A body sinking or swimming in deep water shows lower in it (S43).
	position = Vector2(plane.x, plane.y - altitude + state.sink_depth).snapped(Vector2(2, 2))
	z_index = world.geometry.render_depth(state)
	queue_redraw()

func _draw():
	if meditating: draw_arc(Vector2(0, -4), 28, 0, TAU, 24, Color(0.4, 0.85, 0.76, 0.4), 2, false)
	if state.flying: _draw_cloud()
	if state.gliding: _draw_glide()
	if state.sink_depth > 0.0 or state.water.get("skimming", false): _draw_water_ring()
	if bound():
		if Game.combat.sword_released.has(actor_id): _draw_hover_sword()
		var tl: Dictionary = Game.combat.timeline(actor_id)
		if tl.guard:
			draw_arc(Vector2(facing * 18, -48), 30, -1.2 if facing > 0 else PI - 1.2 + 0.4, 1.2 if facing > 0 else PI + 1.2 - 0.4, 12, Color(UiKit.PALE_GOLD, 0.7), 3)

## S47 Sword Release: the jian hangs point-up above the shoulder between strikes, bobbing in a pale sheen of Qi.
func _draw_hover_sword() -> void:
	var t := Time.get_ticks_msec() / 1000.0
	var base := Vector2(-facing * 26, -104 + sin(t * 3.0) * 4.0)
	draw_circle(base + Vector2(0, -14), 16, Color(0.75, 0.95, 1.0, 0.18))
	draw_line(base + Vector2(0, 12), base + Vector2(0, -30), Color("2b2f33"), 5)
	draw_line(base + Vector2(0, 10), base + Vector2(0, -30), Color("dfe8ee"), 3)
	draw_line(base + Vector2(-1, 8), base + Vector2(-1, -26), Color(1, 1, 1, 0.8), 1)
	draw_colored_polygon(PackedVector2Array([base + Vector2(-2, -30), base + Vector2(2, -30), base + Vector2(0, -36)]), Color("f4fbff"))
	draw_line(base + Vector2(-7, 12), base + Vector2(7, 12), Color("b5892f"), 3)   # guard
	draw_line(base + Vector2(0, 13), base + Vector2(0, 22), Color("5a3a22"), 3)    # grip
	draw_circle(base + Vector2(0, 24), 2.5, Color("d9b25a"))

## Falling Leaf Glide: two pale leaves of Qi either side of the body and a faint trail.
func _draw_glide() -> void:
	var t := Time.get_ticks_msec() / 1000.0
	for side in [-1.0, 1.0]:
		var sway := sin(t * 5.0 + side) * 3.0
		var base := Vector2(side * 16, -54 + sway)
		var leaf := PackedVector2Array([base, base + Vector2(side * 34, -8), base + Vector2(side * 46, 4), base + Vector2(side * 30, 10)])
		draw_colored_polygon(leaf, Color(UiKit.BRIGHT_JADE, 0.45))
		draw_polyline(leaf + PackedVector2Array([leaf[0]]), Color(UiKit.JADE, 0.8), 1.5)
		draw_line(base, base + Vector2(side * 40, 1), Color(1, 1, 1, 0.5), 1.0)
	for k in 3:
		draw_line(Vector2(-facing * (10 + k * 10), -30 - k * 8), Vector2(-facing * (22 + k * 10), -26 - k * 8), Color(1, 1, 1, 0.25 - k * 0.07), 1.5)

## Deep water: a ripple ring at the waterline (skimming leaves a splash trail instead).
func _draw_water_ring() -> void:
	var t := Time.get_ticks_msec() / 1000.0
	var y: float = -state.sink_depth
	var skim: bool = state.water.get("skimming", false)
	var rw := 26.0 + sin(t * 6.0) * 3.0
	draw_arc(Vector2(0, y), rw, 0, TAU, 28, Color(0.85, 0.95, 1.0, 0.7), 2.0)
	draw_arc(Vector2(0, y), rw * 0.65, 0, TAU, 20, Color(0.6, 0.85, 0.95, 0.5), 1.5)
	if skim:
		for k in 3:
			draw_circle(Vector2(-facing * (18 + k * 14), y - 4 - k * 2), 3.0 - k * 0.6, Color(0.9, 0.97, 1.0, 0.7 - k * 0.2))

## A small rolling cloud under the feet while Qi holds the body in the air, or the ridden vessel (G2).
func _draw_cloud() -> void:
	var t := Time.get_ticks_msec() / 1000.0
	var sprite := ""
	if bound():
		var v := str(Game.character(actor_id).inventory.vessel)
		if v != "": sprite = str(ContentDB.item(v).get("flight", {}).get("sprite", ""))
	match sprite:
		"sword": _draw_sword_vessel(t); return
		"gourd": _draw_gourd_vessel(t); return
		"leaf": _draw_leaf_vessel(t); return
	var puffs := [Vector2(-26, 2), Vector2(-10, 7), Vector2(9, 6), Vector2(26, 2), Vector2(0, -1)]
	for i in puffs.size():
		var p: Vector2 = puffs[i] + Vector2(sin(t * 2.2 + i) * 2.0, cos(t * 1.7 + i * 1.3) * 1.5)
		var r := 13.0 - absf(p.x) * 0.14
		draw_circle(p + Vector2(0, 3), r + 2.0, Color(UiKit.JADE, 0.55))           # jade rim of an auspicious cloud
		draw_circle(p, r, Color(0.95, 0.99, 0.97, 0.95))
	for i in 2:   # curled tails
		var side := -1.0 if i == 0 else 1.0
		draw_arc(Vector2(side * 34, 0), 6, 0.0 if side > 0 else PI, TAU * 0.75 + (0.0 if side > 0 else PI), 10, Color(UiKit.JADE, 0.8), 2.0)
	draw_circle(Vector2(-7, -3), 5.0, Color(1, 1, 1, 0.95))

## A flying sword laid flat under the feet: a long jade-steel blade with a gold guard and a streaming tassel.
func _draw_sword_vessel(t: float) -> void:
	var f := float(facing)
	var bob := sin(t * 3.0) * 1.5
	var tip := Vector2(f * 54, 3 + bob)
	var guard := Vector2(-f * 24, 5 + bob)
	var back := Vector2(-f * 40, 6 + bob)
	# A soft jade aura carries the blade.
	for k in 3:
		draw_circle(Vector2(f * (12 - k * 14), 8 + bob), 16.0 - k * 2.0, Color(UiKit.BRIGHT_JADE, 0.10))
	for k in 3:   # a qi trail streaming behind the hilt
		var a := back + Vector2(-f * (6 + k * 11), sin(t * 6.0 + k) * 2.5)
		draw_line(a, a + Vector2(-f * 10, sin(t * 6.0 + k + 1) * 2.5), Color(UiKit.BRIGHT_JADE, 0.55 - k * 0.15), 4.0 - k)
	var n := Vector2(0, 5.0)
	var blade := PackedVector2Array([guard - n, tip - Vector2(f * 10, 1.5), tip, tip - Vector2(f * 10, -1.5), guard + n])
	draw_colored_polygon(blade, Color(0.8, 0.93, 0.93))
	draw_colored_polygon(PackedVector2Array([guard - n, tip - Vector2(f * 10, 1.5), tip, guard]), Color(0.93, 0.99, 1.0))   # the bright upper edge
	draw_line(guard, tip - Vector2(f * 6, 0), Color(0.5, 0.7, 0.72), 1.5)                                                    # the ridge
	draw_polyline(blade + PackedVector2Array([blade[0]]), Color(0.16, 0.26, 0.28), 1.5)
	draw_line(guard + Vector2(0, -9), guard + Vector2(0, 9), Color(0.35, 0.25, 0.1), 7.0)
	draw_line(guard + Vector2(0, -8), guard + Vector2(0, 8), UiKit.PALE_GOLD, 4.5)                                           # the gold guard
	draw_line(guard, back, Color(0.3, 0.14, 0.1), 6.0)                                                                       # the wrapped hilt
	for k in 3: draw_line(guard + (back - guard) * (0.2 + k * 0.28) + Vector2(0, -3), guard + (back - guard) * (0.3 + k * 0.28) + Vector2(0, 3), Color(0.55, 0.3, 0.2), 1.5)
	draw_circle(back, 4.0, UiKit.PALE_GOLD)
	var sway := sin(t * 5.0) * 3.0
	draw_polyline(PackedVector2Array([back, back + Vector2(-f * 5, 6), back + Vector2(-f * 9 + sway, 15)]), Color(0.8, 0.2, 0.18), 3.0)

## A jade gourd ridden side-saddle: a round body, a waist tie and a stopper.
func _draw_gourd_vessel(t: float) -> void:
	var f := float(facing)
	var bob := sin(t * 2.6) * 2.0
	var big := Vector2(-f * 8, 8 + bob)
	var small := Vector2(f * 16, 4 + bob)
	draw_circle(big + Vector2(0, 2), 17.0, Color(0.1, 0.3, 0.24, 0.5))
	draw_circle(big, 16.0, Color(0.36, 0.72, 0.56))
	draw_circle(small, 10.0, Color(0.36, 0.72, 0.56))
	draw_circle(big + Vector2(-5, -6), 5.0, Color(0.7, 0.93, 0.8, 0.7))   # glaze highlight
	draw_line(small + Vector2(-f * 9, -5), small + Vector2(-f * 9, 5), Color(0.75, 0.2, 0.18), 3.0)   # the red cord at the waist
	draw_rect(Rect2(small + Vector2(f * 8, -3) - Vector2(2 if f > 0 else 4, 0), Vector2(6, 6)), Color(0.45, 0.28, 0.14))
	draw_arc(big, 16.0, 0, TAU, 28, Color(0.12, 0.3, 0.24), 1.0)
	draw_arc(small, 10.0, 0, TAU, 20, Color(0.12, 0.3, 0.24), 1.0)

## A great maple leaf that sails on the wind, veined and tipped in autumn red.
func _draw_leaf_vessel(t: float) -> void:
	var f := float(facing)
	var tilt := sin(t * 2.0) * 0.08
	var pts := PackedVector2Array()
	for i in 20:
		var a := float(i) / 20.0 * TAU
		var lobe := 1.0 + 0.28 * absf(sin(a * 2.5))
		var p := Vector2(cos(a) * 40.0 * lobe, sin(a) * 9.0 * lobe)
		pts.append(p.rotated(tilt) + Vector2(0, 6))
	draw_colored_polygon(pts, Color(0.86, 0.38, 0.16))
	draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0.45, 0.16, 0.08), 1.0)
	var stem_end := Vector2(-f * 46, 8).rotated(tilt)
	draw_line(Vector2(f * 36, 6).rotated(tilt), stem_end, Color(0.55, 0.22, 0.1), 1.5)
	for k in 4:
		var x := -30.0 + k * 18.0
		draw_line(Vector2(x, 6).rotated(tilt), Vector2(x + f * 8, 0).rotated(tilt), Color(0.55, 0.22, 0.1, 0.8), 1.0)
		draw_line(Vector2(x, 6).rotated(tilt), Vector2(x + f * 8, 12).rotated(tilt), Color(0.55, 0.22, 0.1, 0.8), 1.0)
