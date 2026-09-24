class_name PlatformLanding
extends RefCounted
## A depthless platform is aimed at in screen space. Resolve its visible top
## against the descending feet, then register the actor on the actual surface.
## Height/energy, depth distance and solid volumes still constrain each catch.
const MAX_DEPTH_CORRECTION=96.0
static func projected_contact(state: ActorState,zone: ZoneGeometry,start: Vector2,next: Vector2,previous_height: float) -> Dictionary:
	var before=start-Vector2(0,previous_height)
	var after=next-Vector2(0,state.altitude)
	if after.y<=before.y or state.vertical_speed>0 or state.departed_surface!="": return {}
	var best: Dictionary={}
	var highest=-INF
	for surface in zone.surfaces:
		if surface.stratum!="platform" or surface.id==state.departed_surface: continue
		if surface.base>state.air_peak+0.01 or surface.rise!=0: continue
		# Do not intercept a flight above a lower roof/balcony. Ordinary world-space
		# landing owns that crossing; projection only repairs a missed depth plane.
		if state.altitude>surface.base+0.01: continue
		var projected_plane=after+Vector2(0,surface.base)
		var depth_limit=maxf(MAX_DEPTH_CORRECTION,surface.base-state.air_base+WalkSurface.FOOT_CONTACT.y)
		if absf(projected_plane.y-next.y)>depth_limit: continue
		var contact=surface.contact_point(projected_plane,Vector2(9,2))
		if not contact.is_finite(): continue
		var top=contact.y-surface.base
		if before.y>top+2 or after.y<top-2: continue
		if zone.blocks_at(contact,surface.base,surface.stratum): continue
		if surface.base>highest:
			highest=surface.base
			best={"surface":surface,"point":contact}
	return best
static func guide(state: ActorState,zone: ZoneGeometry,next: Vector2,velocity: Vector2,gravity: float) -> Vector2:
	if velocity.y>=-20:
		state.landing_assist=""
		return next
	var target: WalkSurface=zone.index.get(state.landing_assist)
	if target and (not is_finite(target.landing_lane(next.x)) or (state.surface and state.surface!=target)):
		state.landing_assist=""
		target=null
	if target==null and state.surface==null and state.jumps_used>0:
		var apex=state.altitude+pow(maxf(0,state.vertical_speed),2)/(2*gravity)
		for candidate in zone.surfaces:
			if candidate.stratum!="platform" or candidate.base<=state.air_base+1 or candidate.base>apex: continue
			# Reject unrelated columns before scanning a shaped platform.
			if next.x<candidate.bounds.position.x+3 or next.x>=candidate.bounds.end.x-3: continue
			var lane=candidate.landing_lane(next.x)
			if not is_finite(lane) or lane-candidate.base>state.plane.y-state.air_base+2: continue
			var discriminant=state.vertical_speed*state.vertical_speed+2*gravity*(state.altitude-candidate.base)
			if discriminant<0: continue
			var flight=(state.vertical_speed+sqrt(discriminant))/gravity
			if state.plane.y-lane>absf(velocity.y)*flight+4: continue
			if target==null or candidate.base<target.base:
				target=candidate
				state.landing_y=lane
		if target: state.landing_assist=target.id
	if target:
		var lane=target.landing_lane(next.x)
		state.landing_y=lane
		# Brake depth at the landing lane. Horizontal steering and downward escape
		# remain available; releasing up or jumping again clears the hold.
		next.y=maxf(next.y,minf(state.plane.y,lane))
	return next
