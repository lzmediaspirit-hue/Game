class_name MovementSolver
extends RefCounted
const GRAVITY=1150.0
const JUMP_IMPULSE=530.0
const MAX_STEP=1.0/120.0
static func jump(state: ActorState) -> bool:
	if state.flying: return false
	if state.surface:
		state.jumps_used=0
		state.wall_step_used=false
		state.air_stratum=state.surface.stratum
		state.air_base=state.altitude
		state.air_peak=state.altitude
	elif state.jumps_used>=2: return false
	state.jumps_used+=1
	state.landing_assist=""
	state.departed_surface=""
	state.vertical_speed=JUMP_IMPULSE
	state.surface=null
	return true
## Which side (-1 left, 1 right) has a solid wall within reach of an airborne actor, or 0.
static func wall_side(state: ActorState,zone: ZoneGeometry) -> int:
	for side in [-1,1]:
		var probe=state.plane+Vector2(side*26.0,0)
		if zone.bounds.has_point(probe) and zone.blocks_at(probe,state.altitude+24.0,state.air_stratum): return side
	return 0
## Wall-Step (secret art, Heart Tempering 4): in the air beside a wall, kick off it once for a fresh
## jump. Returns the wall's side (the caller pushes the body away from it) or 0 when there is none.
static func wall_step(state: ActorState,zone: ZoneGeometry) -> int:
	if state.flying or state.surface or state.wall_step_used: return 0
	var side=wall_side(state,zone)
	if side==0: return 0
	state.wall_step_used=true
	state.vertical_speed=JUMP_IMPULSE*0.95
	state.departed_surface=""
	state.landing_assist=""
	state.air_base=state.altitude
	return side
## Take off from the ground or from the top of a jump. Speed and ceiling come from data.
static func start_flight(state: ActorState,climb_speed: float,ceiling: float) -> bool:
	if state.flying: return false
	if state.surface: state.air_stratum=state.surface.stratum
	state.flying=true
	state.fly_climb_speed=climb_speed
	state.fly_ceiling=ceiling
	state.surface=null
	state.vertical_speed=0
	state.departed_surface=""
	state.landing_assist=""
	state.air_base=state.altitude
	state.climb=0.0
	return true
## Stop holding the air: the actor falls under gravity from here.
static func stop_flight(state: ActorState):
	state.flying=false
	state.climb=0.0
	state.vertical_speed=0
	state.jumps_used=2
static func advance(state: ActorState,zone: ZoneGeometry,delta: float,velocity: Vector2):
	# Bounded substeps prevent missed thin surfaces, stair entrances, and long-frame tunnelling.
	var remaining=delta
	while remaining>0.000001:
		var dt=minf(remaining,MAX_STEP)
		integrate(state,zone,dt,velocity)
		remaining-=dt
static func land(state: ActorState,contact: Dictionary,velocity: Vector2):
	state.surface=contact.surface
	state.plane=contact.point
	state.altitude=state.surface.height_at(state.plane)
	state.vertical_speed=0
	state.jumps_used=0
	state.wall_step_used=false
	state.departed_surface=""
	state.landing_assist=state.surface.id if velocity.y< -20 and state.surface.stratum=="platform" else ""
	state.velocity=Vector2(velocity.x,0)
static func integrate(state: ActorState,zone: ZoneGeometry,dt: float,velocity: Vector2):
	var start=state.plane
	var next=start+velocity*dt
	next=next.clamp(zone.bounds.position+Vector2(12,4),zone.bounds.end-Vector2(12,12))
	next=PlatformLanding.guide(state,zone,next,velocity,GRAVITY)
	if state.surface:
		next=state.surface.follow_walk(next,velocity)
		var prospective=zone.walk_target(next,state.altitude,state.surface)
		# Evaluate a stair step at its destination height before checking its wall.
		if prospective and not zone.blocks_at(next,prospective.height_at(next),prospective.stratum):
			state.altitude=prospective.height_at(next)
		next=zone.resolve_motion(start,next,state)
		var target=zone.walk_target(next,state.altitude,state.surface)
		if target:
			state.surface=target
			state.plane=next
			state.altitude=target.height_at(next)
		elif state.surface.open_edges:
			state.departed_surface=state.surface.id
			state.air_stratum=state.surface.stratum
			state.plane=next
			state.air_base=state.altitude
			state.air_peak=state.altitude
			state.surface=null
			state.vertical_speed=0
			state.jumps_used=1
		else:
			# Resolve both axes, including x-facing walls and terrace side boundaries.
			var best_slide=start
			var best_target: WalkSurface
			for slide in [Vector2(next.x,start.y),Vector2(start.x,next.y)]:
				var slide_target=zone.walk_target(slide,state.altitude,state.surface)
				if slide_target and not zone.blocks(slide,state) and slide.distance_squared_to(start)>best_slide.distance_squared_to(start):
					best_slide=slide
					best_target=slide_target
			if best_target:
				state.surface=best_target
				state.plane=best_slide
				state.altitude=best_target.height_at(best_slide)
	elif state.flying:
		# Hold altitude; climb with input up to the ceiling; descending onto a surface lands.
		next=zone.constrain_air_motion(start,next,state.altitude)
		var previous=state.altitude
		state.altitude=minf(state.fly_ceiling,state.altitude+state.climb*state.fly_climb_speed*dt)
		state.air_peak=maxf(state.air_peak,state.altitude)
		if state.climb<0:
			var touch=zone.landing_contact(next,previous,state.altitude,"")
			if not touch.is_empty():
				state.flying=false
				state.climb=0.0
				land(state,touch,velocity)
				return
		state.plane=zone.resolve_motion(start,next,state)
	else:
		next=zone.constrain_air_motion(start,next,state.altitude)
		var previous=state.altitude
		state.altitude+=state.vertical_speed*dt-0.5*GRAVITY*dt*dt
		state.air_peak=maxf(state.air_peak,maxf(previous,state.altitude))
		state.vertical_speed-=GRAVITY*dt
		# Resolve the top crossing before the wall test: the end-of-step foot
		# height can be slightly below a roof despite having landed on its top.
		if state.vertical_speed<=0:
			var landing=zone.landing_contact(next,previous,state.altitude,state.departed_surface)
			if landing.is_empty():
				landing=PlatformLanding.projected_contact(state,zone,start,next,previous)
			if not landing.is_empty():
				# The rendered foot remains on the same pixel during depth registration.
				# Finalize this exact candidate, rather than repeating a height test in
				# the old depth plane and discarding a valid projected contact.
				land(state,landing,velocity)
				return
		state.plane=zone.resolve_motion(start,next,state)
		if state.vertical_speed<=0:
			var landed=zone.landing_contact(state.plane,previous,state.altitude,state.departed_surface)
			if not landed.is_empty():
				land(state,landed,velocity)
			elif zone.blocks(state.plane,state):
				# A masked roof edge may expose the solid facade underneath.
				# Slide outside that volume rather than trapping a falling actor in it.
				state.plane=zone.nearest_free(state.plane,state.altitude,state.air_stratum,false)
	state.velocity=(state.plane-start)/dt
