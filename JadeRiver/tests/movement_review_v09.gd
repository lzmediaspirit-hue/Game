extends SceneTree
var failures: Array[String]=[]
var checks=0
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		failures.append(label)
		push_error(label)
func actor_at(zone: ZoneGeometry,id: String,point: Vector2) -> ActorState:
	var actor=ActorState.new()
	actor.surface=zone.index[id]
	actor.plane=actor.surface.nearest_supported(point)
	actor.altitude=actor.surface.height_at(actor.plane)
	return actor
func walk(actor: ActorState,zone: ZoneGeometry,target: Vector2,rate: int) -> bool:
	for frame in rate*35:
		if actor.plane.distance_to(target)<0.5: return true
		var before=actor.plane
		MovementSolver.advance(actor,zone,1.0/rate,(target-actor.plane).limit_length(205.0/rate)*rate)
		if actor.plane.distance_to(before)<0.001: return false
	return false
func run():
	for theme in MapGenerator.profiles():
		var data=MapGenerator.generate(theme,7)
		var zone=ZoneGeometry.new()
		zone.configure(ZoneLayout.compile(data))
		for rate in [30,60,120]:
			var rear=Vector2(48,MapGenerator.GROUND_REAR+90)
			var walker=actor_at(zone,"river_walk",Vector2(48,850))
			check(walk(walker,zone,rear,rate),theme+" reach rear corridor at "+str(rate))
			check(walk(walker,zone,Vector2(5350,rear.y),rate),theme+" traverse behind all buildings at "+str(rate))
			check(walk(walker,zone,Vector2(5350,850),rate),theme+" return from rear corridor at "+str(rate))
			for s in zone.surfaces:
				if s.stratum!="platform": continue
				var actor=actor_at(zone,s.id,s.bounds.get_center())
				for frame in rate: MovementSolver.advance(actor,zone,1.0/rate,Vector2.ZERO)
				check(actor.surface==s and s.contains(actor.plane),theme+" stable support "+s.id)
				if s.kind in ["cloud","tree_branch","rock_ledge"]:
					check(s.projected_front()<MapGenerator.GROUND_REAR,theme+" floating art above ground "+s.id)
				if s.kind=="roof":
					var behind=actor_at(zone,"river_walk",Vector2(s.bounds.get_center().x,590))
					check(not zone.blocks(behind.plane,behind),"Behind building is walkable "+s.id)
					check(zone.render_depth(behind)<1500+int(s.bounds.end.y),"Behind building sorts behind facade "+s.id)
					for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
						actor=actor_at(zone,s.id,s.bounds.get_center())
						var valid=true
						for frame in rate*3:
							var before=actor.plane
							MovementSolver.advance(actor,zone,1.0/rate,direction*205)
							valid=valid and (actor.surface==null or actor.surface.contains(actor.plane)) and not zone.blocks(actor.plane,actor) and actor.plane.distance_to(before)<=205.0/rate+0.01
						check(valid,"Roof exit remains supported or falls outside solids "+theme+" "+s.id+str(direction))
			for route in data.routes:
				if route.mode=="walk": continue
				var source: WalkSurface=zone.index[route.from]
				var target: WalkSurface=zone.index[route.to]
				var start=target.bounds.get_center().clamp(source.bounds.position+Vector2(8,8),source.bounds.end-Vector2(8,8))
				if source.stratum=="ground": start=Vector2(target.bounds.get_center().x,target.bounds.end.y+18)
				var actor=actor_at(zone,source.id,start)
				var aim=target.nearest_supported(actor.plane) if route.mode=="double_jump" else target.nearest_supported(target.bounds.get_center())
				if route.mode=="double_jump": aim=target.nearest_supported(aim.lerp(target.bounds.get_center(),0.08))
				MovementSolver.jump(actor)
				for frame in rate*3:
					if route.mode=="double_jump" and actor.vertical_speed<=40 and actor.jumps_used==1: MovementSolver.jump(actor)
					MovementSolver.advance(actor,zone,1.0/rate,(aim-actor.plane).limit_length(205.0/rate)*rate)
					if actor.surface: break
				check(actor.surface==target,"Route "+theme+" "+route.from+" -> "+route.to+" at "+str(rate))
			var stair_actor=actor_at(zone,"river_walk",Vector2(5080,820))
			check(walk(stair_actor,zone,Vector2(5080,650),rate) and stair_actor.surface.id=="garden_terrace" and stair_actor.altitude==64,"Stairs ascend "+theme)
			check(walk(stair_actor,zone,Vector2(5080,820),rate) and stair_actor.surface.id=="river_walk" and stair_actor.altitude==0,"Stairs descend "+theme)
	# A descending foot crosses the roof height in the same step as its wall.
	var zone=ZoneGeometry.new()
	zone.configure(ZoneLayout.compile({"bounds":[0,0,500,500],"objects":[],"surfaces":[
		{"id":"floor","rect":[0,0,500,500],"height":0,"stratum":"ground","open_edges":false,"kind":"ground"},
		{"id":"roof","rect":[100,100,100,100],"height":88,"kind":"roof"}]}))
	for dt in [1.0/120,1.0/60,1.0/30,0.1,0.25]:
		var actor=ActorState.new()
		actor.plane=Vector2(99.8,150)
		actor.altitude=88.4
		actor.vertical_speed=-100
		actor.jumps_used=1
		MovementSolver.advance(actor,zone,dt,Vector2(120,0))
		check(actor.surface==zone.index.roof and actor.altitude==88,"Descending side landing at dt="+str(dt))
	# Small solids can be jumped over and stood upon, but cannot be walked through.
	zone.configure(ZoneLayout.compile({"bounds":[0,0,500,500],"surfaces":[
		{"id":"floor","rect":[0,0,500,500],"height":0,"stratum":"ground","open_edges":false,"kind":"ground"}],
		"objects":[{"id":"stone","art":"props","footprint":[180,180,40,40],"height":30,"radius":0}]}))
	var actor=actor_at(zone,"floor",Vector2(160,200))
	check(not walk(actor,zone,Vector2(240,200),60),"Small obstacle blocks walking")
	MovementSolver.jump(actor)
	for frame in 60: MovementSolver.advance(actor,zone,1.0/60,Vector2(120,0))
	check(actor.plane.x>240 and actor.surface==zone.index.floor,"Jump clears small obstacle")
	actor=actor_at(zone,"floor",Vector2(160,200))
	MovementSolver.jump(actor)
	for frame in 90: MovementSolver.advance(actor,zone,1.0/60,(Vector2(200,200)-actor.plane).limit_length(2)*60)
	check(actor.surface==zone.index.stone_top,"Land on small obstacle top")
	print("MOVEMENT_REVIEW_V09: ",checks-failures.size(),"/",checks)
	quit(1 if not failures.is_empty() else 0)
