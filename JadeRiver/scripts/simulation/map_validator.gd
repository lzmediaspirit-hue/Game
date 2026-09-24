class_name MapValidator
extends RefCounted
## Generation failures are data errors, never silently accepted layouts.
static func validate(data: Dictionary,simulate_routes=true) -> Array[String]:
	var errors: Array[String]=[]
	var ids={}
	var bounds_data=data.bounds
	var map_bounds=Rect2(bounds_data[0],bounds_data[1],bounds_data[2],bounds_data[3])
	for spec in data.surfaces:
		if ids.has(spec.id): errors.append("Duplicate surface: "+spec.id)
		ids[spec.id]=true
		var r=spec.rect
		var rect=Rect2(r[0],r[1],r[2],r[3])
		if not rect.position.is_finite() or not rect.size.is_finite() or rect.size.x<=0 or rect.size.y<=0: errors.append("Invalid surface bounds: "+spec.id)
		elif not map_bounds.encloses(rect): errors.append("Surface outside map: "+spec.id)
		if not is_finite(float(spec.height)): errors.append("Invalid elevation: "+spec.id)
	if not errors.is_empty(): return errors
	var gate_ids={}
	for gate in data.get("gates",[]):
		if gate_ids.has(gate.id): errors.append("Duplicate gate: "+str(gate.id))
		gate_ids[gate.id]=true
		if int(gate.direction) not in [-1,1]: errors.append("Invalid gate direction")
		var extent=float(gate.half_width)+RoomTravel.BODY_RADIUS
		if float(gate.x)-extent<12 or float(gate.x)+extent>map_bounds.end.x-12: errors.append("Gate exit is outside actor bounds")
		if float(gate.y_max)-float(gate.y_min)<=RoomTravel.FOOT_DEPTH*2 or float(gate.clearance)<RoomTravel.BODY_HEIGHT: errors.append("Gate opening cannot fit actor")
	if not errors.is_empty(): return errors
	var zone=ZoneGeometry.new()
	zone.configure(ZoneLayout.compile(data))
	var spawn=Vector2(data.spawn[0],data.spawn[1])
	if zone.blocks_at(spawn,0,"ground"): errors.append("Spawn is blocked")
	for x in range(12,int(MapGenerator.WIDTH)-12,16):
		var depths=[804,850,908]
		for gate in data.get("gates",[]):
			if absf(x-float(gate.x))<126: depths=[850,866,880]
		for y in depths:
			if zone.blocks_at(Vector2(x,y),0,"ground"): errors.append("Road blocked at %s,%s"%[x,y])
	for i in data.parcels.size():
		var a=data.parcels[i].rect
		for j in range(i+1,data.parcels.size()):
			var b=data.parcels[j].rect
			if Rect2(a[0],a[1],a[2],a[3]).intersects(Rect2(b[0],b[1],b[2],b[3])):
				errors.append("Overlapping parcels")
	var reachable={"river_walk":true}
	var trees=0
	for obj in data.objects:
		if str(obj.id).begins_with("tree_"): trees+=1
	if trees!=int(data.profile.tree_count): errors.append("Tree allocation does not match profile")
	var rocks=0
	for obj in data.objects:
		if str(obj.id).begins_with("rock_"): rocks+=1
	if rocks!=int(data.profile.rock_count): errors.append("Rock allocation does not match profile")
	# Full simulated traversal belongs in regression checks, not a mobile region swap.
	if not simulate_routes: return errors
	for route in data.routes:
		if not zone.index.has(route.from) or not zone.index.has(route.to):
			errors.append("Missing route surface")
			continue
		var source: WalkSurface=zone.index[route.from]
		var target: WalkSurface=zone.index[route.to]
		if route.mode=="walk":
			var walker=ActorState.new()
			walker.surface=source
			walker.plane=Vector2(target.bounds.get_center().x,target.bounds.end.y+2)
			walker.altitude=source.height_at(walker.plane)
			for step in 360:
				MovementSolver.advance(walker,zone,1.0/120,(target.bounds.get_center()-walker.plane).limit_length(205.0/120)*120)
			if walker.surface!=target: errors.append("Unreachable ground connection: "+target.id)
			elif reachable.has(source.id): reachable[target.id]=true
			continue
		var actor=ActorState.new()
		actor.surface=source
		# Start within the source nearest the target's center, with a foot margin.
		actor.plane=target.bounds.get_center().clamp(source.bounds.position+Vector2(8,8),source.bounds.end-Vector2(8,8))
		actor.plane=source.nearest_supported(actor.plane)
		if source.id=="river_walk":
			actor.plane=Vector2(target.bounds.get_center().x,target.bounds.end.y+18)
			# Follow the reserved road from spawn, then approach the first platform.
			var walker=ActorState.new()
			walker.surface=source
			walker.plane=spawn
			var waypoints=[Vector2(actor.plane.x,850),actor.plane]
			if target.bounds.end.y<MapGenerator.REAR:
				waypoints=[Vector2(48,850),Vector2(48,MapGenerator.GROUND_REAR+90),Vector2(actor.plane.x,MapGenerator.GROUND_REAR+90),actor.plane]
			for waypoint in waypoints:
				var limit=4000
				while walker.plane.distance_to(waypoint)>0.5 and limit>0:
					MovementSolver.advance(walker,zone,1.0/30,(waypoint-walker.plane).limit_length(205.0/30)*30)
					limit-=1
				if limit==0: errors.append("Blocked ground approach: "+target.id)
			actor.plane=walker.plane
		actor.altitude=source.height_at(actor.plane)
		if zone.blocks(actor.plane,actor): errors.append("Jump begins inside solid: "+target.id)
		MovementSolver.jump(actor)
		var landed=false
		var aim=target.nearest_supported(actor.plane) if route.mode=="double_jump" else target.nearest_supported(target.bounds.get_center())
		if route.mode=="double_jump": aim=target.nearest_supported(aim.lerp(target.bounds.get_center(),0.08))
		for step in 360:
			if route.mode=="double_jump" and actor.vertical_speed<=40 and actor.jumps_used==1: MovementSolver.jump(actor)
			var offset=aim-actor.plane
			var velocity=offset.limit_length(205.0/120)*120
			MovementSolver.advance(actor,zone,1.0/120,velocity)
			if actor.surface:
				landed=actor.surface.id==target.id
				break
		if not landed: errors.append("Unreachable route: "+route.from+" -> "+route.to)
		elif reachable.has(source.id): reachable[target.id]=true
	for s in zone.surfaces:
		if not reachable.has(s.id): errors.append("No route from spawn: "+s.id)
	return errors
