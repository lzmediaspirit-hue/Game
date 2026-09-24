extends SceneTree
var checks=0
var failures: Array[String]=[]
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		failures.append(label)
		push_error(label)
func actor_on(surface: WalkSurface) -> ActorState:
	var actor=ActorState.new()
	actor.surface=surface
	actor.plane=surface.nearest_supported(surface.bounds.get_center())
	actor.altitude=surface.base
	return actor
func traverse(zone: ZoneGeometry,surface: WalkSurface,rate: int,speed: float,drift: float,direction: int) -> bool:
	var actor=actor_on(surface)
	var end_x=surface.bounds.position.x+surface.bounds.size.x*(0.79 if direction==1 else 0.17)
	for frame in rate*2:
		if (actor.plane.x-end_x)*direction>=-0.01: return true
		var velocity=Vector2(direction,drift).normalized()*speed
		var step=minf(1.0/rate,absf(end_x-actor.plane.x)/absf(velocity.x))
		MovementSolver.advance(actor,zone,step,velocity)
		if actor.surface!=surface or not surface.contains(actor.plane):
			return false
	return false
func run():
	for theme in ["forest","cave"]:
		var zone=ZoneGeometry.new()
		zone.configure(ZoneLayout.compile(MapGenerator.generate(theme,7)))
		for id in ["ascent_00","cloud_00"]:
			if not zone.index.has(id): continue
			var surface: WalkSurface=zone.index[id]
			check(not surface.contact_point(surface.bounds.position-Vector2(30,30)).is_finite(),"Distant misses cannot snap onto "+surface.kind)
			var replay_actor=actor_on(surface)
			replay_actor.surface=null
			replay_actor.altitude+=20
			replay_actor.departed_surface=surface.id
			var restored=ActorState.new()
			var authority=LocalAuthority.new(restored,zone)
			check(authority.restore_authoritative_snapshot(replay_actor.snapshot(1)) and restored.departed_surface==surface.id,"Replay retains intentional exit "+surface.kind)
			check(MovementSolver.jump(restored) and restored.departed_surface=="","Jump can return to departed platform "+surface.kind)
			for rate in [20,30,60,120]:
				for drift in [-1.0,-0.65,-0.35,-0.15,0.0,0.15,0.35,0.65,1.0]:
					for direction in [-1,1]:
						for speed in [205.0,348.5]:
							check(traverse(zone,surface,rate,speed,drift,direction),"Traverse "+surface.kind+" at "+str(rate)+" FPS, drift="+str(drift)+", direction="+str(direction)+", speed="+str(speed))
				# Land with feet overlapping a narrow band, rather than requiring
				# the actor's single center pixel to cross an opaque mask cell.
				for offset in [-8.0,8.0]:
					var actor=actor_on(surface)
					actor.plane.y+=offset
					actor.surface=null
					actor.altitude=surface.base+18
					actor.vertical_speed=-100
					for frame in rate/2: MovementSolver.advance(actor,zone,1.0/rate,Vector2.ZERO)
					check(actor.surface==surface,"Foot overlap landing "+surface.kind+" offset="+str(offset))
				# The true horizontal ends remain open: never walk on invisible air.
				for direction in [-1,1]:
					var actor=actor_on(surface)
					var left=false
					for frame in rate:
						MovementSolver.advance(actor,zone,1.0/rate,Vector2(direction,0)*205)
						if actor.surface!=surface: left=true
					check(left,"Real platform end permits falling "+surface.kind)
				# An intentional depth-only move can still leave the platform.
				var actor=actor_on(surface)
				for frame in rate: MovementSolver.advance(actor,zone,1.0/rate,Vector2.DOWN*205)
				check(actor.surface!=surface,"Deliberate downward exit "+surface.kind)
	print("PLATFORM_CONTACT: ",checks-failures.size(),"/",checks)
	quit(1 if not failures.is_empty() else 0)
