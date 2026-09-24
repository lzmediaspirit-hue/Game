extends Node2D
const Avatar=preload("res://scripts/avatar.gd")
var world: Node2D
var state=ActorState.new()
var authority: LocalAuthority
var command_sequence=0
var plane: Vector2:
	get: return state.plane
	set(value): state.plane=value
var altitude: float:
	get: return state.altitude
	set(value): state.altitude=value
var air_base: float:
	get: return state.air_base
	set(value): state.air_base=value
var jump_height: float:
	get: return maxf(0,altitude-(surface.height_at(plane) if surface else air_base))
var vertical_speed: float:
	get: return state.vertical_speed
	set(value): state.vertical_speed=value
var surface: WalkSurface:
	get: return state.surface
	set(value): state.surface=value
var velocity: Vector2:
	get: return state.velocity
	set(value): state.velocity=value
var movement=Vector2.ZERO
var speed=205.0
var attack_time=0.0
const COMBOS={"swing":["swing_1","swing_2","swing_3"],"attack":["thrust_1","thrust_2","thrust_3"],"punch":["punch_1","punch_2","punch_3"]}
const COMBO_WINDOW=0.45
var combo_index=-1
var combo_queue=0
var combo_window=0.0
var attack_duration=0.0
var attack_weapon=""
var bow_release_time=-1.0
var meditating=false
var qi=100.0
var hp=100.0
var facing=1
var avatar: Node2D
var outfit: Dictionary
var joystick_engaged=false
var drag_seconds=0.0
var sprinting=false
var last_axis=Vector2.ZERO
var sprint_direction=Vector2.ZERO
signal attack_started(family: String,plane_position: Vector2,elevation: float,direction: int)
signal arrow_released(plane_position: Vector2,elevation: float,direction: int)
func _ready():
	authority=LocalAuthority.new(state,world.geometry)
	avatar=Avatar.new()
	avatar.outfit=outfit.duplicate(true)
	avatar.scale=Vector2.ONE
	add_child(avatar)
func jump():
	if authority.jump():
		meditating=false
		attack_time=0
		reset_combo()
		avatar.externally_timed=false
		bow_release_time=-1
		avatar.play("jump")
		avatar.elapsed=0
		avatar.playback_speed=1
func attack():
	if attack_weapon!="" and attack_weapon!=str(avatar.outfit.weapon):
		attack_time=0
		bow_release_time=-1
		reset_combo()
	if attack_time>0:
		if combo_index>=0: combo_queue=mini(combo_queue+1,2-combo_index)
		return
	meditating=false
	if avatar.outfit.weapon=="bow":
		reset_combo()
		begin_attack("bow")
	else:
		combo_index=combo_index+1 if combo_window>0 and combo_index<2 else 0
		begin_attack(combo_action())
func combo_action() -> String:
	return COMBOS[Wardrobe.attack_for(avatar.outfit)][combo_index]
func reset_combo():
	combo_index=-1
	combo_queue=0
	combo_window=0
func begin_attack(family: String):
	var spec=Wardrobe.parts._actions[family]
	attack_duration=float(spec.frames)/spec.fps
	attack_time=attack_duration
	attack_weapon=str(avatar.outfit.weapon)
	combo_window=0
	reset_sprint()
	bow_release_time=0.55 if family=="bow" else -1.0
	avatar.hide_bow_arrow=false
	avatar.play(family)
	avatar.elapsed=0
	avatar.externally_timed=true
	avatar.playback_speed=1
	attack_started.emit(family,plane,altitude,facing)
func advance_attack(delta: float):
	var remaining=delta
	while remaining>0 and attack_time>0:
		var consumed=minf(remaining,attack_time)
		attack_time=maxf(0,attack_time-consumed)
		remaining-=consumed
		avatar.elapsed=attack_duration-attack_time
		if bow_release_time>=0:
			bow_release_time-=consumed
			if bow_release_time<=0:
				bow_release_time=-1
				avatar.hide_bow_arrow=true
				arrow_released.emit(plane,altitude,facing)
		if attack_time<=0:
			if combo_queue>0 and combo_index<2:
				combo_queue-=1
				combo_index+=1
				begin_attack(combo_action())
			else:
				combo_window=COMBO_WINDOW if combo_index in [0,1] else 0.0
				avatar.externally_timed=false
	if attack_time<=0:
		combo_window=maxf(0,combo_window-remaining)
		if combo_window<=0: reset_combo()
func meditate():
	if surface!=null and attack_time<=0:
		reset_combo()
		meditating=not meditating
func reset_sprint():
	drag_seconds=0
	sprinting=false
	sprint_direction=Vector2.ZERO
func _physics_process(delta):
	var keyboard=Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN))-float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	step(delta,(keyboard+movement).limit_length())
func step(delta: float,axis: Vector2):
	if not is_finite(delta) or delta<=0 or delta>3.0 or not axis.is_finite(): return
	axis=axis.limit_length()
	last_axis=axis
	if attack_time>0 and attack_weapon!=str(avatar.outfit.weapon):
		attack_time=0
		bow_release_time=-1
		reset_combo()
	advance_attack(delta)
	if attack_time<=0: avatar.externally_timed=false
	if axis.length()>0.12: meditating=false
	if axis.x!=0 and attack_time<=0: facing=1 if axis.x>0 else -1
	if absf(axis.x)>0.12 and attack_time<=0 and not meditating:
		var horizontal=Vector2(signf(axis.x),0)
		if sprint_direction!=horizontal:
			reset_sprint()
			sprint_direction=horizontal
		drag_seconds+=delta
		sprinting=drag_seconds>2.0
	else: reset_sprint()
	var factor=0.3 if attack_time>0 else (1.7 if sprinting else 1.0)
	command_sequence+=1
	authority.move(command_sequence,axis if not meditating else Vector2.ZERO,delta,speed*factor)
	if absf(velocity.x)<5: reset_sprint()
	if altitude < -250: world.recover_to_safe()
	if meditating: qi=minf(100,qi+12*delta)
	avatar.facing=facing
	avatar.playback_speed=1.7 if sprinting and surface!=null else 1.0
	if attack_time<=0: avatar.play("meditate" if meditating else ("jump" if surface==null else ("walk" if velocity.length()>5 else "idle")))
	sync_visual()
func sync_visual():
	position=Vector2(plane.x,plane.y-altitude).snapped(Vector2(2,2))
	z_index=world.geometry.render_depth(state)
	queue_redraw()
func _draw():
	if meditating: draw_arc(Vector2(0,-4),28,0,TAU,24,Color(0.4,0.85,0.76,0.4),2,false)
