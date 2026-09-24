extends SceneTree
var failures: Array[String]=[]
var checks=0
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		failures.append(label)
		push_error(label)
func run():
	for theme in ["forest","village","cave"]:
		var zone=ZoneGeometry.new()
		zone.configure(ZoneLayout.compile(MapGenerator.generate(theme,7)))
		var targets=["ascent_00","ascent_01","ascent_02","cloud_00","building_00","building_01"]
		for s in zone.surfaces:
			if s.id.begins_with("tree_") and s.id.ends_with("_branch_0"): targets.append(s.id)
		for rate in [30,60,120]:
			for id in targets:
				if not zone.index.has(id): continue
				var target: WalkSurface=zone.index[id]
				var source: WalkSurface=zone.index.river_walk
				if id=="ascent_01": source=zone.index.ascent_00
				if id=="ascent_02": source=zone.index.ascent_01
				if id=="cloud_00": source=zone.index.ascent_05
				if id=="building_01": source=zone.index.building_01_balcony_0
				var actor=ActorState.new()
				actor.surface=source
				actor.plane=source.nearest_supported(Vector2(target.bounds.get_center().x,target.bounds.end.y+28))
				if not is_finite(target.landing_lane(actor.plane.x)): continue # Horizontal transfer is covered separately.
				actor.altitude=source.height_at(actor.plane)
				MovementSolver.jump(actor)
				for frame in rate*2: MovementSolver.advance(actor,zone,1.0/rate,Vector2.UP*205)
				check(actor.surface==target,"Hold UP to land and stand: "+theme+" "+id+" at "+str(rate))
				check(actor.surface!=null and actor.surface.contains(actor.plane),"Assisted feet have visible support")
				MovementSolver.advance(actor,zone,1.0/rate,Vector2.ZERO)
				check(actor.landing_assist=="","Releasing UP removes assist")
				var before=actor.plane
				MovementSolver.advance(actor,zone,0.1,Vector2.DOWN*205)
				check(actor.plane.y>before.y,"Downward escape remains available")
	# Unreachable height, unrelated columns and downward steering must not snap.
	var zone=ZoneGeometry.new()
	zone.configure(ZoneLayout.compile(MapGenerator.generate("forest",7)))
	for axis in [Vector2.UP,Vector2.DOWN]:
		var actor=ActorState.new()
		actor.surface=zone.index.river_walk
		actor.plane=Vector2(3000,850)
		MovementSolver.jump(actor)
		for frame in 120: MovementSolver.advance(actor,zone,1.0/120,axis*205)
		check(actor.landing_assist=="" and actor.surface==zone.index.river_walk,"Empty-space jump does not capture unrelated platforms")
	var actor=ActorState.new()
	actor.surface=zone.index.river_walk
	actor.plane=Vector2(4425,580)
	var authority=LocalAuthority.new(actor,zone)
	authority.jump()
	authority.move(1,Vector2.UP,0.3,205)
	var copy=ActorState.new()
	var replica=LocalAuthority.new(copy,zone)
	check(actor.landing_assist!="" and replica.restore_authoritative_snapshot(authority.snapshot()),"Assisted airborne state survives trusted snapshot restore")
	for frame in 60:
		authority.move(frame+2,Vector2.UP,1.0/60,205)
		replica.move(frame+2,Vector2.UP,1.0/60,205)
	check(actor.plane.is_equal_approx(copy.plane) and is_equal_approx(actor.altitude,copy.altitude) and actor.surface==copy.surface,"Assisted landing replays deterministically")
	print("UPWARD_LANDING: ",checks-failures.size(),"/",checks)
	quit(1 if not failures.is_empty() else 0)
