extends Node2D
const Player=preload("res://scripts/player.gd")
const Terrain=preload("res://scripts/terrain.gd")
const Arrow=preload("res://scripts/arrow.gd")
const SceneryProp=preload("res://scripts/scenery_prop.gd")
const OcclusionOutline=preload("res://scripts/occlusion_outline.gd")
const MAP_REVISION=7
var travel=RoomTravel.new()
var geometry=ZoneGeometry.new()
var surfaces: Array[WalkSurface]=[]
var terrain_visuals: Array=[]
var props: Array[Node2D]=[]
var map_bounds: Rect2
var player: Node2D
var player_shadow: Node2D
var player_outline: Node2D
var camera: Camera2D
var outfit: Dictionary
var save_slot_index=-1
var skill_page=0
var save_timer=0.0
var last_safe: Dictionary={}
var save_error: Error=OK
var map_theme=""
var map_seed=1
var map_data: Dictionary={}
var transitions_enabled=false
var transition_pending=false
signal region_exit(theme: String,seed_value: int,direction: int)
func _ready():
	var data=JSON.parse_string(FileAccess.get_file_as_string("res://data/world.json"))
	if map_theme!="":
		if not WorldCatalog.valid_theme(map_theme): map_theme="village"
		data=MapGenerator.generate(map_theme,map_seed)
		var errors=MapValidator.validate(data,false)
		assert(errors.is_empty(),str(errors))
	map_data=data
	data=ZoneLayout.compile(data)
	geometry.configure(data)
	map_bounds=geometry.bounds
	surfaces=geometry.surfaces
	travel.gates=data.get("gates",[])
	for gate_spec in travel.gates:
		var gate=preload("res://scripts/room_gate.gd").new()
		gate.spec=gate_spec
		add_child(gate)
	for s in surfaces:
		add_terrain(s)
	for spec in data.get("objects",[]):
		if spec.get("art","none")=="none": continue
		var prop=SceneryProp.new()
		prop.spec=spec
		add_child(prop)
		props.append(prop)
	player=Player.new()
	if map_theme!="": player.state.zone_id=WorldCatalog.zone_id(map_theme,map_seed)
	player.world=self
	player.outfit=outfit.duplicate(true)
	player.plane=Vector2(data.spawn[0],data.spawn[1])
	player.surface=surfaces[0]
	add_child(player)
	player.arrow_released.connect(spawn_arrow)
	player_shadow=preload("res://scripts/shadow.gd").new()
	player_shadow.player=player
	player_shadow.world=self
	add_child(player_shadow)
	player_outline=OcclusionOutline.new()
	player_outline.source=player
	add_child(player_outline)
	camera=Camera2D.new()
	add_child(camera)
	restore_progress(outfit.get("progress",{}))
	travel.reset(player.plane,player.altitude)
	player.sync_visual()
	camera.position=camera_target()
	record_safe_position()
	update_sorting()
func camera_target() -> Vector2:
	var target=player.position+Vector2(player.velocity.x*0.25,-150)
	target.x=clampf(target.x,0 if map_theme!="" else 640,map_bounds.end.x if map_theme!="" else map_bounds.end.x-640)
	target.y=clampf(target.y,-750 if map_theme!="" else 180,730)
	return target
func _process(delta):
	if transitions_enabled and not transition_pending:
		var direction=travel.advance(player.state)
		if direction!=0:
			transition_pending=true
			region_exit.emit(WorldCatalog.neighbour(map_theme,direction),map_seed,direction)
	camera.position=camera.position.lerp(camera_target(),1-exp(-delta*5))
	camera.position=camera.position.snapped(Vector2(2,2))
	record_safe_position()
	update_occlusion()
	save_timer+=delta
	if save_timer>=5:
		save_timer=0
		save_game()
func by_id(id: String) -> WalkSurface: return geometry.index.get(id)
func walk_target(point: Vector2,current_height: float,previous: WalkSurface) -> WalkSurface:
	return geometry.walk_target(point,current_height,previous)
func landing_target(point: Vector2,previous_height: float,next_height: float) -> WalkSurface:
	return geometry.landing_target(point,previous_height,next_height)
func update_occlusion():
	var hidden=not geometry.occluder_at(player.state).is_empty()
	# Normal sprite depth lets scenery cover only overlapping pixels.
	player.visible=true
	player_shadow.visible=true
	player_outline.visible=hidden
	player_outline.sync()
func add_terrain(s: WalkSurface):
	var terrain=Terrain.new()
	terrain.surface=s
	terrain.ground_material=str(map_data.get("ground_material","stone"))
	if s.stratum=="ground" and s.base>0: terrain.ground_material="stone"
	terrain.generated=map_theme!=""
	add_child(terrain)
	terrain_visuals.append(terrain)
func update_sorting():
	for visual in terrain_visuals:
		var s: WalkSurface=visual.surface
		if s.stratum=="ground" and (map_theme=="" or (s.base==0 and s.rise==0)):
			visual.z_index=-1800 if s.kind=="stairs" else -2000+int(s.base)
		else:
			# Use projected foot depth, not raw elevation added to depth.
			# Ground actors always remain in front of background platform scenery.
			visual.z_index=1500+int(s.bounds.end.y)
			if s.kind=="roof":
				for obstacle in geometry.obstacles:
					if obstacle.get("surface","")==s.id:
						visual.z_index=1500+int(obstacle.get("front_y",s.bounds.end.y))
func spawn_arrow(origin: Vector2,elevation: float,direction: int):
	var projectile=Arrow.new()
	projectile.zone=geometry
	projectile.plane=origin+Vector2(direction*28,0)
	projectile.altitude=elevation+58
	projectile.direction=direction
	projectile.z_index=geometry.render_depth(player.state)+1
	add_child(projectile)
func record_safe_position():
	if player.surface:
		last_safe={"map_revision":MAP_REVISION,"surface":player.surface.id,"x":player.plane.x,"y":player.plane.y,"map_theme":map_theme,"map_seed":map_seed,"generator_version":MapGenerator.VERSION}
func save_game() -> Error:
	if save_slot_index<0: return OK
	record_safe_position()
	var data=player.avatar.outfit.duplicate(true)
	var state=last_safe.duplicate(true)
	state.merge({"hp":player.hp,"qi":player.qi,"facing":player.facing,"skill_page":skill_page},true)
	data["progress"]=state
	save_error=Wardrobe.save_slot(save_slot_index,data)
	if save_error!=OK: push_warning("Could not save Jade River progress: "+error_string(save_error))
	return save_error
func restore_progress(state: Dictionary):
	if int(state.get("map_revision",0)) not in [2,3,4,5,6,MAP_REVISION]: return
	if str(state.get("map_theme",""))!=map_theme: return
	if map_theme!="" and int(state.get("map_seed",map_seed))!=map_seed: return
	if map_theme!="" and int(state.get("generator_version",MapGenerator.VERSION)) not in [2,3,4,5,MapGenerator.VERSION]: return
	# Keep character progress even if an old map surface no longer exists.
	player.hp=clampf(float(state.get("hp",100)),0,100)
	player.qi=clampf(float(state.get("qi",100)),0,100)
	player.facing=-1 if state.get("facing",1)==-1 else 1
	skill_page=clampi(int(state.get("skill_page",0)),0,1)
	var s=by_id(str(state.get("surface","")))
	var p=Vector2(float(state.get("x",0)),float(state.get("y",0)))
	if s==null or not p.is_finite(): return
	if int(state.get("map_revision",0)) in [2,3]: p=p.clamp(s.bounds.position+Vector2.ONE,s.bounds.end-Vector2.ONE)
	if not s.contains(p): p=s.nearest_supported(p)
	player.surface=s
	player.altitude=s.height_at(p)
	player.plane=geometry.nearest_free(p,player.altitude,s.stratum)
	if not s.contains(player.plane):
		player.surface=surfaces[0]
		player.plane=Vector2(620,820)
	player.altitude=player.surface.height_at(player.plane)
func recover_to_safe():
	if last_safe.is_empty():
		player.plane=Vector2(340,800)
		player.surface=surfaces[0]
		player.altitude=0
	else:
		var hp=player.hp
		var qi=player.qi
		var facing=player.facing
		var page=skill_page
		restore_progress(last_safe)
		player.hp=hp
		player.qi=qi
		player.facing=facing
		skill_page=page
	player.velocity=Vector2.ZERO
	player.reset_sprint()
	player.sync_visual()
	player.vertical_speed=0
	player.state.jumps_used=0
	player.state.landing_assist=""
	player.state.departed_surface=""
	player.state.air_peak=player.altitude
	player.state.air_base=player.altitude
	player.state.air_stratum=player.surface.stratum
	travel.reset(player.plane,player.altitude)
