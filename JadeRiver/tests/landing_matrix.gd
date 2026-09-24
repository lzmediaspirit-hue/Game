extends SceneTree
var checks=0
var failures: Array[String]=[]
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok: failures.append(label)
func run():
	# Start from what the player sees below a branch, not an invisible floor
	# coordinate under the platform. No feedback controller steers to its center.
	for theme in MapGenerator.profiles():
		var zone=ZoneGeometry.new()
		zone.configure(ZoneLayout.compile(MapGenerator.generate(theme,7)))
		for target in zone.surfaces:
			if target.stratum!="platform" or target.base>100: continue
			var lane=target.nearest_supported(target.bounds.get_center())
			for rate in [4,20,30,60,120]:
				for axis in [Vector2.ZERO,Vector2.UP,Vector2(0.25,-1).normalized(),Vector2(-0.25,-1).normalized()]:
					var actor=ActorState.new()
					actor.surface=zone.index.river_walk
					actor.plane=Vector2(lane.x,maxf(484,lane.y-target.base+45))
					if zone.blocks(actor.plane,actor): continue
					MovementSolver.jump(actor)
					var landed=false
					for frame in rate*2:
						MovementSolver.advance(actor,zone,1.0/rate,axis*205)
						if actor.surface==target or actor.departed_surface==target.id:
							landed=true
							break
					check(landed,"Visual approach "+theme+" "+target.id+" axis="+str(axis)+" fps="+str(rate))
	await directional_cases()
	for failure in failures.slice(0,20): print("FAIL: ",failure)
	print("LANDING_MATRIX: ",checks-failures.size(),"/",checks)
	quit(1 if not failures.is_empty() else 0)
func directional_cases():
	var masks=JSON.parse_string(FileAccess.get_file_as_string("res://data/surface_masks.json"))
	for kind in ["tree_branch","cloud","rock_ledge","roof","balcony"]:
		var spec=MapGenerator.surface("target",[900,1000,240,80],88,kind)
		if masks.has(kind): spec.support_mask=masks[kind]
		if kind=="roof": spec.support_mask=masks.roof_even
		var zone=ZoneGeometry.new()
		zone.configure(ZoneLayout.compile({"bounds":[0,0,2000,2000],"objects":[],"surfaces":[MapGenerator.surface("floor",[0,0,2000,2000],0,"ground","ground"),spec]}))
		var target=zone.index.target
		var lane=target.nearest_supported(target.bounds.get_center())
		var flight=(530.0+sqrt(530.0*530-2*1150*88))/1150
		for rate in [20,30,60,120]:
			for speed in [80.0,205.0,348.5]:
				for angle in 8:
					var axis=Vector2.RIGHT.rotated(angle*TAU/8)
					var actor=ActorState.new()
					actor.surface=zone.index.floor
					actor.plane=lane-axis*speed*flight
					if zone.blocks(actor.plane,actor): continue
					MovementSolver.jump(actor)
					var landed=false
					for frame in rate*2:
						MovementSolver.advance(actor,zone,1.0/rate,axis*speed)
						if actor.surface==target or actor.departed_surface==target.id:
							landed=true
							break
					check(landed,"Eight-way contact "+str([kind,rate,speed,angle]))
		# Reachable double jump and forbidden single jump use the same visible aim.
		for jumps in [1,2]:
			var elevated=spec.duplicate(true)
			elevated.height=200
			zone.configure(ZoneLayout.compile({"bounds":[0,0,2000,2000],"objects":[],"surfaces":[MapGenerator.surface("floor",[0,0,2000,2000],0,"ground","ground"),elevated]}))
			var actor=ActorState.new()
			actor.surface=zone.index.floor
			actor.plane=Vector2(lane.x,lane.y-200+45)
			MovementSolver.jump(actor)
			for frame in 180:
				if frame==27 and jumps==2: MovementSolver.jump(actor)
				MovementSolver.advance(actor,zone,1.0/60,Vector2.ZERO)
			check((actor.surface==zone.index.target)==(jumps==2),"Height budget "+kind+" jumps="+str(jumps))
