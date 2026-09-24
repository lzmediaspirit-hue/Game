class_name ZoneGeometry
extends RefCounted
## Shared by the local simulation and a future authoritative zone server.
var surfaces: Array[WalkSurface]=[]
var index: Dictionary={}
var obstacles: Array[Dictionary]=[]
var bounds: Rect2
func configure(data: Dictionary):
	surfaces.clear()
	index.clear()
	obstacles.clear()
	var r=data.bounds
	bounds=Rect2(r[0],r[1],r[2],r[3])
	for spec in data.surfaces:
		var surface=WalkSurface.new(spec)
		assert(not index.has(surface.id),"Duplicate surface ID")
		surfaces.append(surface)
		index[surface.id]=surface
	for spec in data.get("objects",[]):
		var obstacle=spec.duplicate(true)
		if obstacle.get("blocks",true):
			var footprint_data=obstacle.footprint
			obstacle.footprint=Rect2(footprint_data[0],footprint_data[1],footprint_data[2],footprint_data[3])
		if obstacle.has("occlusion"):
			var o=obstacle.occlusion
			obstacle.occlusion=Rect2(o[0],o[1],o[2],o[3])
		obstacles.append(obstacle)
func is_ground_actor(state: ActorState) -> bool:
	return state.surface.stratum=="ground" if state.surface else state.air_stratum=="ground"
func blocks(point: Vector2,state: ActorState) -> bool:
	return blocks_at(point,state.altitude,state.surface.stratum if state.surface else state.air_stratum)
func blocks_at(point: Vector2,altitude: float,stratum: String) -> bool:
	for obstacle in obstacles:
		if not obstacle.get("blocks",true): continue
		if altitude>=float(obstacle.get("base",0))+float(obstacle.get("height",9999)): continue
		var shape: WalkSurface=index.get(obstacle.get("support_shape",""))
		if shape and not shape.contains(point): continue
		if (obstacle.footprint as Rect2).grow(float(obstacle.get("radius",11))).has_point(point): return true
	return false
func nearest_free(point: Vector2,altitude: float,stratum: String,require_support=true) -> Vector2:
	if not blocks_at(point,altitude,stratum) and (not require_support or stratum!="ground" or supported_ground(point,altitude)): return point
	for radius in range(12,241,12):
		for direction in [Vector2.RIGHT,Vector2.LEFT,Vector2.DOWN,Vector2.UP,Vector2(1,1).normalized(),Vector2(-1,1).normalized(),Vector2(1,-1).normalized(),Vector2(-1,-1).normalized()]:
			var candidate=(point+direction*radius).clamp(bounds.position+Vector2(12,4),bounds.end-Vector2(12,12))
			if not blocks_at(candidate,altitude,stratum) and (not require_support or stratum!="ground" or supported_ground(candidate,altitude)): return candidate
	return point
func supported_ground(point: Vector2,height: float) -> bool:
	for s in surfaces:
		if s.stratum=="ground" and s.contains(point) and absf(s.height_at(point)-height)<8: return true
	return false
func resolve_motion(start: Vector2,target: Vector2,state: ActorState) -> Vector2:
	if not blocks(target,state): return target
	var x_only=Vector2(target.x,start.y)
	var y_only=Vector2(start.x,target.y)
	var x_ok=not blocks(x_only,state)
	var y_ok=not blocks(y_only,state)
	if x_ok and y_ok: return x_only if absf(target.x-start.x)>=absf(target.y-start.y) else y_only
	if x_ok: return x_only
	if y_ok: return y_only
	return start
func ground_contains(point: Vector2) -> bool:
	for candidate in surfaces:
		if candidate.stratum=="ground" and candidate.contains(point): return true
	return false
func constrain_air_motion(start: Vector2,target: Vector2,height: float) -> Vector2:
	if ground_contains(target): return target
	for candidate in surfaces:
		if candidate.contains(target) and height>=candidate.height_at(target): return target
	if ground_contains(start):
		for slide in [Vector2(target.x,start.y),Vector2(start.x,target.y)]:
			if ground_contains(slide): return slide
		return start
	# Falling off an elevated surface beyond the ground edge returns to its nearest ground boundary.
	var best=start
	var distance=INF
	for candidate in surfaces:
		if candidate.stratum!="ground": continue
		var point=target.clamp(candidate.bounds.position+Vector2(4,4),candidate.bounds.end-Vector2(4,4))
		if point.distance_squared_to(target)<distance:
			best=point
			distance=point.distance_squared_to(target)
	return best
func occluder_at(state: ActorState) -> Dictionary:
	if not is_ground_actor(state): return {}
	for obstacle in obstacles:
		if not obstacle.has("occlusion"): continue
		if state.altitude>=float(obstacle.get("height",9999)): continue
		var area: Rect2=obstacle.occlusion
		if area.has_point(state.plane) and state.plane.y<float(obstacle.get("front_y",area.end.y)):
			return obstacle
	return {}
func walk_target(point: Vector2,height: float,previous: WalkSurface) -> WalkSurface:
	var best: WalkSurface=previous if previous.contains(point) else null
	for candidate in surfaces:
		if candidate==previous or candidate.stratum!=previous.stratum or not candidate.contains(point): continue
		if absf(candidate.height_at(point)-height)>8.0: continue
		if best==null or (candidate.rise!=0 and previous.rise==0): best=candidate
	return best
func landing_target(point: Vector2,previous_height: float,next_height: float) -> WalkSurface:
	var best: WalkSurface
	for candidate in surfaces:
		var height=candidate.height_at(point)
		if candidate.contains(point) and height<=previous_height+0.001 and height>=next_height-0.001:
			if blocks_at(point,height,candidate.stratum): continue
			if best==null or height>best.height_at(point): best=candidate
	return best
func landing_contact(point: Vector2,previous_height: float,next_height: float,departed="") -> Dictionary:
	var best: Dictionary={}
	var best_height=-INF
	var best_distance=INF
	for candidate in surfaces:
		if candidate.id==departed: continue
		var height=candidate.height_at(point)
		if height>previous_height+0.001 or height<next_height-0.001: continue
		var contact=point if candidate.contains(point) else candidate.contact_point(point)
		if not contact.is_finite() or blocks_at(contact,height,candidate.stratum): continue
		var distance=point.distance_squared_to(contact)
		if height>best_height or (is_equal_approx(height,best_height) and distance<best_distance):
			best={"surface":candidate,"point":contact}
			best_height=height
			best_distance=distance
	return best
func render_depth(state: ActorState) -> int:
	var depth=1500+int(state.plane.y)
	for candidate in surfaces:
		if (candidate.stratum=="platform" or candidate.base>0 or candidate.rise!=0) and candidate.contains(state.plane) and state.altitude>=candidate.height_at(state.plane)-0.001:
			depth=maxi(depth,1502+int(candidate.bounds.end.y))
	return depth
