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
const GLIDE_FALL=120.0               # Falling Leaf Glide: the fastest descent
const GLIDE_DRIFT=1.1                # and 10% faster across
const AIR_DASH_HOLD=0.25             # Swallow Dart: the height held while darting 140
const PLUNGE_SPEED=900.0
const SHALLOW_FACTOR=0.7             # volumes (S43 rule 1)
const SWIM_FACTOR=0.6
const SINK_FACTOR=0.3
const SINK_S=1.0                     # deep water swallows a body in 1 s ...
const SINK_DEPTH=40.0
const SWIM_S=30.0                    # ... or 30 s with Breath Control
const SKIM_MIN_SPEED=60.0            # Water Skimming: slower than this counts as stopping
const SKIM_STILL_S=0.5
const UPDRAFT_SPEED=220.0
const UPDRAFT_EASE=3.0
const BOUNCE_SPEED=700.0
const WIND_EDGE=48.0                 # wind is 1.5x within this of an open edge
const ICE_TRACTION=380.0             # ice (v1.1): underfoot the body gains or sheds at most this much speed a second
## Jump: from a surface, within coyote time after walking off one, or (with Cloud Ladder Step)
## once more in the air. A press that cannot jump is buffered for 0.12 s and fires on landing.
static func jump(state: ActorState) -> bool:
	if state.flying or not state.climbing.is_empty() or state.plunging: return false
	# A body sinking in deep water cannot push off; a swimmer or a skimmer can.
	if state.surface and not state.water.is_empty() and float(state.water.get("swim_left",0.0))<=0.0 and not state.water.get("skimming",false): return false
	if state.surface or state.coyote_left>0.0:
		if state.surface:
			state.air_stratum=state.surface.stratum
			state.air_base=state.altitude
			state.air_peak=state.altitude
		state.jumps_used=1
		state.wall_step_used=false
		state.wall_kicks=0
		state.coyote_left=0.0
		state.vertical_speed=float(state.jump_impulse)
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
	state.gliding=false
	state.water={}
	state.sink_depth=0.0
	state.events.append({"name":"jumped","jumps":state.jumps_used})
	return true
## Swallow Dart (S43, Qi Kindling 7): in the air, hold the height for 0.25 s while the dash carries you 140.
## Once per airtime. Combat checks the art and the shared dodge cooldown and moves the body.
static func air_dash(state: ActorState) -> bool:
	if state.surface or state.flying or state.air_dash_used or state.plunging or not state.climbing.is_empty(): return false
	if not state.arts.get("air_dash",false): return false
	state.air_dash_used=true
	state.dash_hold=AIR_DASH_HOLD
	state.vertical_speed=0.0
	state.gliding=false
	state.events.append({"name":"art_used","art":"air_dash"})
	return true
## Plunge (S43, Bone Forging 4): drop straight down at 900; the landing strikes (Combat resolves it).
static func plunge(state: ActorState) -> bool:
	if state.surface or state.flying or state.plunging or not state.climbing.is_empty() or not state.arts.get("plunge",false): return false
	state.plunging=true
	state.gliding=false
	state.dash_hold=0.0
	state.vertical_speed=-PLUNGE_SPEED
	state.events.append({"name":"art_used","art":"plunge"})
	return true
## Falling Leaf Glide (S43, Qi Kindling 3): Jump held while descending. Combat pays 2 QI a second.
static func glide(state: ActorState,on: bool) -> bool:
	if not on:
		state.gliding=false
		return true
	if state.surface or state.flying or state.plunging or not state.climbing.is_empty() or not state.arts.get("glide",false): return false
	if not state.gliding: state.events.append({"name":"art_used","art":"glide"})
	state.gliding=true
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
	state.gliding=false
	state.plunging=false
	return true
## Stop holding the air: the actor falls under gravity from here.
static func stop_flight(state: ActorState):
	state.flying=false
	state.climb=0.0
	state.vertical_speed=0
	state.jumps_used=2
static func advance(state: ActorState,zone: ZoneGeometry,delta: float,velocity: Vector2):
	carry(state,zone)
	# Bounded substeps prevent missed thin surfaces, stair entrances, and long-frame tunnelling.
	var remaining=delta
	while remaining>0.000001:
		var dt=minf(remaining,MAX_STEP)
		integrate(state,zone,dt,velocity)
		remaining-=dt
## A mover carries its riders by its own motion before they move (S43): the offset change since the
## last carry, so the result does not depend on frame timing.
static func carry(state: ActorState,zone: ZoneGeometry):
	var s: WalkSurface=state.surface
	if s==null or not s.moving:
		state.rider_of=""
		return
	if state.rider_of!=s.id:
		state.rider_of=s.id
		state.rider_offset=s.offset
		state.events.append({"name":"mover_boarded","mover":s.id})
		zone.trigger_mover(s.id)
		return
	var d: Vector3=s.offset-state.rider_offset
	state.rider_offset=s.offset
	if d==Vector3.ZERO: return
	state.plane+=Vector2(d.x,d.y)
	state.altitude=s.height_at(state.plane)
## Volumes entered and left this step (S43 events).
static func _track_volumes(state: ActorState,zone: ZoneGeometry,vols: Array):
	var ids: Array=[]
	for v in vols: ids.append(str(v.id))
	for id in ids:
		if id not in state.volumes_in:
			for v in vols:
				if str(v.id)==id: state.events.append({"name":"volume_entered","volume":id,"kind":str(v.kind)})
	for id in state.volumes_in:
		if id not in ids: state.events.append({"name":"volume_left","volume":id})
	state.volumes_in=ids
## How the volumes around the body change the velocity it asks for (S43 volume table).
static func _volume_velocity(state: ActorState,zone: ZoneGeometry,vols: Array,velocity: Vector2,dt:=0.0) -> Vector2:
	var v=velocity
	var ice: Dictionary={}
	for vol in vols:
		match str(vol.kind):
			"ice":
				ice=vol
			"water_shallow":
				if state.surface: v*=float(vol.get("speed",SHALLOW_FACTOR))
			"current":
				if state.surface:
					var push: Array=vol.get("push",[0,0])
					v+=Vector2(float(push[0]),float(push[1]))
			"wind":
				var wp: Array=vol.get("push",[0,0])
				var k=zone.wind_strength(vol)
				if state.surface and zone.open_edge_distance(state.surface,state.plane)<WIND_EDGE: k*=float(vol.get("edge_factor",1.5))
				v+=Vector2(float(wp[0]),float(wp[1]))*k
	# Ice (the v1.1 traction rule): on it, the body's speed only eases toward what it asks for, so it slides on and
	# slides to a stop. Air control stays total.
	if not ice.is_empty() and state.surface and dt>0.0:
		v=state.velocity.move_toward(v,float(ice.get("traction",ICE_TRACTION))*dt)
	return v
## Deep water underfoot (S43): Water Skimming runs across it while sprinting; Breath Control swims for 30 s;
## otherwise the body sinks 40 over 1 s and is returned to a safe spot.
static func _water(state: ActorState,zone: ZoneGeometry,dt: float,velocity: Vector2) -> Vector2:
	var w: Dictionary=zone.water_at(state.plane,state.altitude)
	if w.is_empty():
		state.water={}
		state.sink_depth=0.0
		return velocity
	if state.water.is_empty() or str(state.water.get("id",""))!=str(w.id):
		state.water={"id":str(w.id),"sink":0.0,"swim_left":SWIM_S if state.arts.get("breath_control",false) else 0.0,"still":0.0,
			"skimming":false,"announced":false}
	var wt: Dictionary=state.water
	var fast=velocity.length()>=SKIM_MIN_SPEED
	if state.arts.get("water_skimming",false) and state.sprinting and float(wt.sink)<=0.0 and (fast or wt.skimming):
		if fast: wt.still=0.0
		else: wt.still=float(wt.still)+dt
		wt.skimming=float(wt.still)<SKIM_STILL_S
		if wt.skimming and not wt.announced:
			wt.announced=true
			state.events.append({"name":"art_used","art":"water_skimming"})
	else:
		wt.skimming=false
	if wt.skimming:
		state.sink_depth=0.0
		return velocity
	if float(wt.swim_left)>0.0:
		wt.swim_left=maxf(0.0,float(wt.swim_left)-dt)
		state.sink_depth=SINK_DEPTH*0.5
		return velocity*SWIM_FACTOR
	wt.sink=minf(1.0,float(wt.sink)+dt/SINK_S)
	state.sink_depth=SINK_DEPTH*float(wt.sink)
	if float(wt.sink)>=1.0: state.drowned=true
	return velocity*SINK_FACTOR
static func land(state: ActorState,contact: Dictionary,velocity: Vector2,zone: ZoneGeometry=null):
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
	state.gliding=false
	state.air_dash_used=false
	state.dash_hold=0.0
	var plunged=state.plunging
	state.events.append({"name":"landed","surface":state.surface.id,"fall_height":maxf(0.0,state.air_peak-state.altitude),"plunge":plunged})
	if plunged:
		state.plunging=false
		state.plunge_impact={"x":state.plane.x,"y":state.plane.y,"alt":state.altitude,"surface":state.surface.id}
	if zone:
		zone.touch(state.surface.id)
		# A bounce volume (drum, lotus pad, bent bamboo) launches the body straight back up (apex about 213).
		var b: Dictionary=zone.volume_at(state.plane,state.altitude,"bounce")
		if not b.is_empty() and not plunged:
			state.air_stratum=state.surface.stratum
			state.air_base=state.altitude
			state.air_peak=state.altitude
			state.departed_surface=""
			state.surface=null
			state.jumps_used=1
			state.vertical_speed=float(b.get("speed",BOUNCE_SPEED))
			state.events.append({"name":"art_used","art":"bounce"})
			return
	# A jump pressed just before landing fires now (S43 jump buffer).
	if state.buffer_left>0.0: jump(state)
static func integrate(state: ActorState,zone: ZoneGeometry,dt: float,velocity: Vector2):
	state.coyote_left=maxf(0.0,state.coyote_left-dt)
	state.buffer_left=maxf(0.0,state.buffer_left-dt)
	state.mantle_left=maxf(0.0,state.mantle_left-dt)
	if not state.climbing.is_empty():
		_climb(state,zone,dt,velocity)
		return
	var vols: Array=zone.volumes_at(state.plane,state.altitude) if not zone.volumes.is_empty() else []
	if not zone.volumes.is_empty(): _track_volumes(state,zone,vols)
	velocity=_volume_velocity(state,zone,vols,velocity,dt)
	if state.surface:
		if state.surface.disabled:
			# A crumbled or broken floor drops everyone on it.
			state.departed_surface=state.surface.id
			state.air_stratum=state.surface.stratum
			state.air_base=state.altitude
			state.air_peak=state.altitude
			state.surface=null
			state.vertical_speed=0.0
			state.jumps_used=1
			state.water={}
			state.sink_depth=0.0
		else:
			zone.touch(state.surface.id)
			if not zone.volumes.is_empty(): velocity=_water(state,zone,dt,velocity)
	elif state.plunging: velocity=Vector2.ZERO
	elif state.gliding: velocity*=GLIDE_DRIFT
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
		var lift=0.0
		if state.climb>=0.0 and not zone.volume_at(state.plane,state.altitude,"updraft").is_empty(): lift=UPDRAFT_SPEED*0.5
		state.altitude=minf(state.fly_ceiling,state.altitude+(state.climb*state.fly_climb_speed+lift)*dt)
		state.air_peak=maxf(state.air_peak,state.altitude)
		if state.climb<0:
			var touch=zone.landing_contact(next,previous,state.altitude,"")
			if not touch.is_empty():
				state.flying=false
				state.climb=0.0
				land(state,touch,velocity,zone)
				return
		state.plane=zone.resolve_motion(start,next,state)
	else:
		next=zone.constrain_air_motion(start,next,state.altitude)
		var previous=state.altitude
		var updraft: Dictionary={} if state.plunging or zone.volumes.is_empty() else zone.volume_at(state.plane,state.altitude,"updraft")
		if state.dash_hold>0.0:
			# Swallow Dart holds the height while it carries the body.
			state.dash_hold=maxf(0.0,state.dash_hold-dt)
			state.vertical_speed=0.0
		elif state.plunging:
			state.vertical_speed=-PLUNGE_SPEED
			state.altitude+=state.vertical_speed*dt
		elif not updraft.is_empty() and state.vertical_speed<float(updraft.get("speed",UPDRAFT_SPEED)):
			# An updraft eases the fall into a rise toward +220 while falling, gliding or flying.
			state.altitude+=state.vertical_speed*dt
			state.vertical_speed+=(float(updraft.get("speed",UPDRAFT_SPEED))-state.vertical_speed)*minf(1.0,UPDRAFT_EASE*dt)
		elif state.gliding and state.vertical_speed<=-GLIDE_FALL:
			state.vertical_speed=-GLIDE_FALL
			state.altitude+=state.vertical_speed*dt
		else:
			state.altitude+=state.vertical_speed*dt-0.5*GRAVITY*dt*dt
			state.vertical_speed-=GRAVITY*dt
			if state.gliding: state.vertical_speed=maxf(state.vertical_speed,-GLIDE_FALL)
		state.air_peak=maxf(state.air_peak,maxf(previous,state.altitude))
		# Resolve the top crossing before the wall test: the end-of-step foot
		# height can be slightly below a roof despite having landed on its top.
		if state.vertical_speed<=0:
			var landing=zone.landing_contact(next,previous,state.altitude,state.departed_surface)
			if landing.is_empty():
				landing=PlatformLanding.projected_contact(state,zone,start,next,previous)
			if not landing.is_empty() and state.plunging and landing.surface.cracked:
				# A Plunge breaks a cracked floor and keeps falling (S43 rule 10).
				zone.break_surface(landing.surface.id)
				landing={}
			if not landing.is_empty():
				# The rendered foot remains on the same pixel during depth registration.
				# Finalize this exact candidate, rather than repeating a height test in
				# the old depth plane and discarding a valid projected contact.
				land(state,landing,velocity,zone)
				return
		state.plane=zone.resolve_motion(start,next,state)
		if state.vertical_speed<=0:
			var landed=zone.landing_contact(state.plane,previous,state.altitude,state.departed_surface)
			if not landed.is_empty() and state.plunging and landed.surface.cracked:
				zone.break_surface(landed.surface.id)
				landed={}
			if not landed.is_empty():
				land(state,landed,velocity,zone)
				return
			elif zone.blocks(state.plane,state):
				# A masked roof edge may expose the solid facade underneath.
				# Slide outside that volume rather than trapping a falling actor in it.
				state.plane=zone.nearest_free(state.plane,state.altitude,state.air_stratum,false)
		if absf(velocity.x)>1.0 and state.vertical_speed<=0.0 and not state.plunging and state.arts.get("mantle",false):
			var ledge=zone.mantle_contact(state.plane,state.altitude,signi(int(signf(velocity.x))),MANTLE_RISE,MANTLE_REACH,state.departed_surface)
			if not ledge.is_empty():
				# Ledge mantle (S43 rule 4): a "just missed" top within 24 up and 16 across pulls you onto it.
				state.air_peak=maxf(state.air_peak,float(ledge.surface.height_at(ledge.point)))
				land(state,ledge,Vector2(velocity.x,0),zone)
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
	state.air_dash_used=false
	state.gliding=false
	state.plunging=false
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
