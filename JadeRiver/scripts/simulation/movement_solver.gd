class_name MovementSolver
extends RefCounted
const GRAVITY=1150.0
const JUMP_IMPULSE=530.0
const MAX_STEP=1.0/120.0
# S43 rule 2 and the movement arts (numbers also in data/movement.json for the room lint and tests).
const DOUBLE_JUMP_IMPULSE=430.0      # Cloud Ladder Step: +80 from where it is used
const COYOTE_S=0.10
const BUFFER_S=0.12
const WALL_KICK_SPEED=450.0          # Wall-Step: +88, and 90 units away from the wall
const WALL_KICKS=3
const WALL_REACH=12.0
const MANTLE_RISE=24.0
const MANTLE_REACH=16.0
const CLIMB_SPEED=160.0
## Jump: from a surface, within coyote time after walking off one, or (with Cloud Ladder Step)
## once more in the air. A press that cannot jump is buffered for 0.12 s and fires on landing.
static func jump(state: ActorState) -> bool:
	if state.flying or not state.climbing.is_empty(): return false
	if state.surface or state.coyote_left>0.0:
		if state.surface:
			state.air_stratum=state.surface.stratum
			state.air_base=state.altitude
			state.air_peak=state.altitude
		state.jumps_used=1
		state.wall_step_used=false
		state.wall_kicks=0
		state.coyote_left=0.0
		state.vertical_speed=JUMP_IMPULSE
	elif state.jumps_used<2 and state.arts.get("double_jump",false):
		state.jumps_used=2
		state.vertical_speed=DOUBLE_JUMP_IMPULSE
		state.events.append({"name":"art_used","art":"double_jump"})
	else:
		state.buffer_left=BUFFER_S
		return false
	state.buffer_left=0.0
	state.landing_assist=""
	state.departed_surface=""
	state.surface=null
	state.events.append({"name":"jumped","jumps":state.jumps_used})
	return true
## Drop through (S43 rule 3): fall through the platform under the feet. Never a ground surface or a block.
static func drop_through(state: ActorState) -> bool:
	var s: WalkSurface=state.surface
	if s==null or s.stratum!="platform" or s.is_block or s.kind=="ladder" or not state.arts.get("drop_through",false): return false
	state.departed_surface=s.id
	state.air_stratum=s.stratum
	state.air_base=state.altitude
	state.air_peak=state.altitude
	state.surface=null
	state.vertical_speed=0.0
	state.jumps_used=1
	state.coyote_left=0.0
	state.events.append({"name":"art_used","art":"drop_through"})
	return true
## The side (-1 left, 1 right) of a wall face within 12 units that the actor pushes into, or 0.
## A wall face is any solid volume (a block's side, a building) at the actor's height (S43).
static func wall_side(state: ActorState,zone: ZoneGeometry,push:=0) -> int:
	if push==0: return 0   # Wall-Step needs a push into the wall (S43)
	for side in [push]:
		var probe=state.plane+Vector2(side*WALL_REACH,0)
		if zone.bounds.has_point(probe) and zone.wall_face_at(probe,state.altitude+24.0,state.air_stratum): return side
	return 0
## Wall-Step (S43, Heart Tempering 4): in the air and pushing into a wall face, kick off it: vertical
## speed 450 (+88) and 90 units away. Three kicks per airtime. Returns the wall's side or 0.
static func wall_step(state: ActorState,zone: ZoneGeometry,push:=0) -> int:
	if state.flying or state.surface or not state.climbing.is_empty() or not state.arts.get("wall_step",false): return 0
	if state.wall_kicks>=WALL_KICKS: return 0
	var side=wall_side(state,zone,push)
	if side==0: return 0
	state.wall_kicks+=1
	state.wall_step_used=true
	state.vertical_speed=WALL_KICK_SPEED
	state.departed_surface=""
	state.landing_assist=""
	state.air_base=state.altitude
	state.events.append({"name":"wall_kicked","side":side,"kicks":state.wall_kicks})
	state.events.append({"name":"art_used","art":"wall_step"})
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
	state.wall_kicks=0
	state.coyote_left=0.0
	state.departed_surface=""
	state.landing_assist=state.surface.id if velocity.y< -20 and state.surface.stratum=="platform" else ""
	state.velocity=Vector2(velocity.x,0)
	state.events.append({"name":"landed","surface":state.surface.id,"fall_height":maxf(0.0,state.air_peak-state.altitude)})
	# A jump pressed just before landing fires now (S43 jump buffer).
	if state.buffer_left>0.0: jump(state)
static func integrate(state: ActorState,zone: ZoneGeometry,dt: float,velocity: Vector2):
	state.coyote_left=maxf(0.0,state.coyote_left-dt)
	state.buffer_left=maxf(0.0,state.buffer_left-dt)
	state.mantle_left=maxf(0.0,state.mantle_left-dt)
	if not state.climbing.is_empty():
		_climb(state,zone,dt,velocity)
		return
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
		elif state.surface.edge_toward(next)=="open":
			# Walked off an open edge (S43 rule 1): a jump in the next 0.10 s is still a ground jump.
			state.departed_surface=state.surface.id
			state.air_stratum=state.surface.stratum
			state.plane=next
			state.air_base=state.altitude
			state.air_peak=state.altitude
			state.surface=null
			state.vertical_speed=0
			state.jumps_used=1
			state.coyote_left=COYOTE_S
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
				return
			elif zone.blocks(state.plane,state):
				# A masked roof edge may expose the solid facade underneath.
				# Slide outside that volume rather than trapping a falling actor in it.
				state.plane=zone.nearest_free(state.plane,state.altitude,state.air_stratum,false)
		if absf(velocity.x)>1.0 and state.vertical_speed<=0.0 and state.arts.get("mantle",false):
			var ledge=zone.mantle_contact(state.plane,state.altitude,signi(int(signf(velocity.x))),MANTLE_RISE,MANTLE_REACH,state.departed_surface)
			if not ledge.is_empty():
				# Ledge mantle (S43 rule 4): a "just missed" top within 24 up and 16 across pulls you onto it.
				state.air_peak=maxf(state.air_peak,float(ledge.surface.height_at(ledge.point)))
				land(state,ledge,Vector2(velocity.x,0))
				state.mantle_left=0.2
				state.events.append({"name":"art_used","art":"mantle"})
				return
	state.velocity=(state.plane-start)/dt

## Climb mode (S43 rule 5): the climber rides the climbable's line between its bottom and top heights.
## Up (into the screen) climbs, down descends; reaching an end steps onto that surface.
static func _climb(state: ActorState,zone: ZoneGeometry,dt: float,velocity: Vector2):
	var c: Dictionary=state.climbing
	var speed=CLIMB_SPEED*(1.0+clampf(float(c.get("speed_bonus",0.0)),0.0,0.5))
	var dir=0.0
	if absf(velocity.y)>1.0: dir=-signf(velocity.y)
	state.altitude=clampf(state.altitude+dir*speed*dt,float(c.bottom_alt),float(c.top_alt))
	state.vertical_speed=0.0
	state.velocity=Vector2.ZERO
	if dir>0 and state.altitude>=float(c.top_alt)-0.01:
		_leave_climb(state,zone,"top")
	elif dir<0 and state.altitude<=float(c.bottom_alt)+0.01:
		_leave_climb(state,zone,"bottom")
static func start_climb(state: ActorState,climbable: Dictionary,from_top: bool) -> bool:
	if state.flying or not state.arts.get("climb",false) or not state.climbing.is_empty(): return false
	state.climbing=climbable.duplicate()
	var at: Array=climbable.at
	state.plane=Vector2(float(at[0]),float(at[1]))
	state.altitude=float(climbable.top_alt) if from_top else float(climbable.bottom_alt)
	state.surface=null
	state.vertical_speed=0.0
	state.jumps_used=0
	state.wall_kicks=0
	state.events.append({"name":"climb_started","climbable":str(climbable.id)})
	return true
## Step off at an end of the climbable onto its surface there.
static func _leave_climb(state: ActorState,zone: ZoneGeometry,end: String):
	var c: Dictionary=state.climbing
	var point: Array=c.top_at if end=="top" else c.at
	var sid=str(c.get(end,""))
	var s: WalkSurface=zone.index.get(sid)
	state.climbing={}
	state.plane=Vector2(float(point[0]),float(point[1]))
	if s:
		state.surface=s
		state.altitude=s.height_at(state.plane)
	else:
		state.altitude=float(c.top_alt if end=="top" else c.bottom_alt)
		state.surface=zone.landing_target(state.plane,state.altitude+1.0,state.altitude-1.0)
	state.air_peak=state.altitude
	state.events.append({"name":"climb_finished","climbable":str(c.id),"end":end})
## Let go of the climbable: a jump off sideways (ropes and vines add 20%), or knocked off by a hit.
static func release_climb(state: ActorState,side: int,jumped: bool) -> bool:
	if state.climbing.is_empty(): return false
	var kind=str(state.climbing.get("kind","ladder"))
	var id=str(state.climbing.id)
	state.climbing={}
	state.air_stratum="platform"
	state.air_base=state.altitude
	state.air_peak=state.altitude
	state.surface=null
	state.jumps_used=1
	state.vertical_speed=JUMP_IMPULSE*0.6 if jumped else 0.0
	state.plane.x+=float(side)*(14.0 if kind=="ladder" else 17.0)
	state.events.append({"name":"climb_finished","climbable":id,"end":"jump" if jumped else "knocked"})
	return true
