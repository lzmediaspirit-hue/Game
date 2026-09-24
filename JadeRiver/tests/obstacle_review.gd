extends SceneTree
var failed=0
var checks=0
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		failed+=1
		push_error(label)
func actor(zone,point,height=0.0,support="river_walk"):
	var state=ActorState.new()
	state.plane=point
	state.altitude=height
	state.surface=zone.index[support]
	return state
func run():
	var data=ZoneLayout.compile(JSON.parse_string(FileAccess.get_file_as_string("res://data/world.json")))
	var zone=ZoneGeometry.new()
	zone.configure(data)
	var count=zone.surfaces.size()
	zone.configure(data)
	check(zone.surfaces.size()==count,"Configuration must be reusable")
	for rate in [30,60,120]:
		var dt=1.0/rate
		var state=actor(zone,Vector2(285,725))
		for i in rate: MovementSolver.advance(state,zone,dt,Vector2(205,0))
		check(state.plane.x<315,"Walking cannot pass through rock")
		state=actor(zone,Vector2(285,725))
		MovementSolver.jump(state)
		for i in rate: MovementSolver.advance(state,zone,dt,Vector2(205,0))
		check(state.plane.x>410 and state.surface!=null,"Jump clears low rock")
		state=actor(zone,Vector2(840,660))
		MovementSolver.jump(state)
		for i in int(rate*0.8): MovementSolver.advance(state,zone,dt,Vector2(205,0))
		check(state.surface!=null and state.surface.id=="jade_roof","Ground jump reaches low roof")
		state=actor(zone,Vector2(2030,660))
		MovementSolver.jump(state)
		for i in rate: MovementSolver.advance(state,zone,dt,Vector2(205,0))
		check(state.plane.x<2080,"High building remains solid during jump")
	for surface in zone.surfaces:
		for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
			var state=actor(zone,surface.bounds.get_center(),surface.height_at(surface.bounds.get_center()),surface.id)
			MovementSolver.jump(state)
			for i in 240: MovementSolver.advance(state,zone,1.0/120,direction*205)
			check(state.plane.is_finite() and is_finite(state.altitude),"Finite movement: "+surface.id)
			check(state.surface==null or state.surface.contains(state.plane),"Support bounds: "+surface.id)
	var state=actor(zone,Vector2(620,820))
	var authority=LocalAuthority.new(state,zone)
	check(authority.restore_authoritative_snapshot(JSON.parse_string(JSON.stringify(authority.snapshot()))),"Network JSON round trip")
	print("OBSTACLE_REVIEW: ",checks-failed,"/",checks)
	quit(1 if failed else 0)
