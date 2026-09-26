class_name ZoneGeometry
extends RefCounted
## Shared by the local simulation and a future authoritative zone server.
var surfaces: Array[WalkSurface]=[]
var index: Dictionary={}
var obstacles: Array[Dictionary]=[]
var bounds: Rect2
var climbables: Array=[]                 # S43: ladders, ropes, vines and chains (climb mode)
var void_altitude=-250.0                 # below this a fall returns to the last safe position (S43 rule 6)
# S43 volumes and movers. `time` is the room's simulation clock: movers are a pure function of it.
var volumes: Array=[]                    # {id, kind, rect: Rect2, lo, hi, ...parameters}
var movers: Array=[]                     # {surface, path, speed, wait_s, mode, trigger_t}
var time=0.0
var crumbles: Dictionary={}              # surface id -> {start, broken_at}
var water_goals: Dictionary={}           # rising water: volume id -> {from, to, t0, over}
var nav_cache: Dictionary={}             # S43 rule 11: navigation graphs by movement profile
func configure(data: Dictionary):
	surfaces.clear()
	index.clear()
	obstacles.clear()
	volumes.clear()
	movers.clear()
	nav_cache.clear()
	crumbles.clear()
	water_goals.clear()
	time=0.0
	var r=data.bounds
	bounds=Rect2(r[0],r[1],r[2],r[3])
	for spec in data.surfaces:
		var surface=WalkSurface.new(spec)
		assert(not index.has(surface.id),"Duplicate surface ID")
		surfaces.append(surface)
		index[surface.id]=surface
	# S43 blocks: a solid box whose top is a walkable surface with every edge open.
	for b in data.get("blocks",[]):
		var r2: Array=b.rect
		var top=float(b.top)
		var surface_spec={"id":str(b.id),"rect":r2,"height":top,"kind":"block","stratum":"platform","block_kind":str(b.get("kind","crate")),"cracked":bool(b.get("cracked",false))}
		var top_surface=WalkSurface.new(surface_spec)
		assert(not index.has(top_surface.id),"Duplicate surface ID")
		surfaces.append(top_surface)
		index[top_surface.id]=top_surface
		obstacles.append({"id":str(b.id),"block":true,"footprint":Rect2(r2[0],r2[1],r2[2],r2[3]),"base":float(b.get("base",0.0)),
			"height":top-float(b.get("base",0.0)),"radius":6.0,"step":8.0,"wall_faces":bool(b.get("wall_faces",true)),"blocks":true})
	climbables=data.get("climbables",[]).duplicate(true)
	for v in data.get("volumes",[]):
		var vol: Dictionary=v.duplicate(true)
		var vr: Array=v.rect
		vol.rect=Rect2(float(vr[0]),float(vr[1]),float(vr[2]),float(vr[3]))
		var alt: Array=v.get("alt",[-1000.0,1000.0])
		vol.lo=float(alt[0])
		vol.hi=float(alt[1])
		if not vol.has("id"): vol.id="%s_%d" % [str(v.kind),volumes.size()]
		volumes.append(vol)
	for m in data.get("movers",[]):
		var mv: Dictionary=m.duplicate(true)
		mv.trigger_t=-1.0
		var ms: WalkSurface=index.get(str(m.surface))
		if ms: ms.moving=true
		movers.append(mv)
	var lowest=0.0
	for s in surfaces: lowest=minf(lowest,s.base+minf(0.0,s.rise))
	void_altitude=float(data.get("void_altitude",lowest-250.0))
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
		if not obstacle.get("blocks",true) or obstacle.get("disabled",false): continue
		# A block lets an actor within 8 of its top step over it (S43); other volumes need the full height.
		if altitude>=float(obstacle.get("base",0))+float(obstacle.get("height",9999))-float(obstacle.get("step",0.0)): continue
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
		if s.stratum=="ground" and not s.disabled and s.contains(point) and absf(s.height_at(point)-height)<8: return true
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
	var best: WalkSurface=previous if previous.contains(point) and not previous.disabled else null
	for candidate in surfaces:
		if candidate==previous or candidate.disabled or not candidate.contains(point): continue
		# Ladders are the one bridge between layers: a walker steps on or off them wherever heights meet.
		if candidate.stratum!=previous.stratum and candidate.kind!="ladder" and previous.kind!="ladder": continue
		if absf(candidate.height_at(point)-height)>8.0: continue
		if best==null or (candidate.rise!=0 and previous.rise==0): best=candidate
	return best
func landing_target(point: Vector2,previous_height: float,next_height: float) -> WalkSurface:
	var best: WalkSurface
	for candidate in surfaces:
		if candidate.disabled: continue
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
		if candidate.id==departed or candidate.disabled: continue
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

## A wall face at this point and height: a block side (unless it has wall_faces false) or any other solid volume.
func wall_face_at(point: Vector2,altitude: float,stratum: String) -> bool:
	for obstacle in obstacles:
		if not obstacle.get("blocks",true) or obstacle.get("disabled",false) or (obstacle.get("block",false) and not obstacle.get("wall_faces",true)): continue
		if altitude>=float(obstacle.get("base",0))+float(obstacle.get("height",9999)): continue
		if altitude<float(obstacle.get("base",0)): continue
		var shape: WalkSurface=index.get(obstacle.get("support_shape",""))
		if shape and not shape.contains(point): continue
		if (obstacle.footprint as Rect2).grow(float(obstacle.get("radius",11))).has_point(point): return true
	return false
## A shot at this point and height hits something solid: a block or a building's wall (S43 rule 10).
## Platform decks and scenery do not stop it.
func stops_shot(point: Vector2,altitude: float) -> bool:
	for obstacle in obstacles:
		if obstacle.get("disabled",false) or not obstacle.get("blocks",true): continue
		if not (obstacle.get("block",false) or str(obstacle.get("surface",""))!=""): continue
		if altitude<float(obstacle.get("base",0)) or altitude>=float(obstacle.get("base",0))+float(obstacle.get("height",0)): continue
		var shape: WalkSurface=index.get(obstacle.get("support_shape",""))
		if shape and not shape.contains(point): continue
		if (obstacle.footprint as Rect2).has_point(point): return true
	return false
## Ledge mantle (S43 rule 4): the top of a surface or block 0-24 units above `altitude` whose near side is
## within `reach` of the actor in the direction it pushes, at the same depth. {} when there is none.
func mantle_contact(point: Vector2,altitude: float,push: int,rise: float,reach: float,departed:="") -> Dictionary:
	if push==0: return {}
	var best: Dictionary={}
	var best_h=INF
	for s in surfaces:
		if s.id==departed or s.rise!=0.0 or s.kind=="ladder" or s.disabled: continue
		var top=s.base
		if top<altitude-0.01 or top>altitude+rise: continue
		if point.y<s.bounds.position.y or point.y>=s.bounds.end.y: continue
		var near_x=s.bounds.position.x if push>0 else s.bounds.end.x
		var gap=(near_x-point.x)*push
		if gap<-2.0 or gap>reach: continue
		var p=Vector2(near_x+push*6.0,point.y)
		if not s.contains(p) or blocks_at(p,top,s.stratum): continue
		if top<best_h:
			best={"surface":s,"point":p}
			best_h=top
	return best
## The climbable within `radius` of a plane point at either end (its foot on the ground, or its top), or {}.
func climbable_near(point: Vector2,altitude: float,radius:=28.0) -> Dictionary:
	for c in climbables:
		var at: Array=c.at
		var top_at: Array=c.get("top_at",c.at)
		if Vector2(float(at[0]),float(at[1])).distance_to(point)<=radius and absf(altitude-float(c.bottom_alt))<12.0: return c.merged({"from_top":false})
		if Vector2(float(top_at[0]),float(top_at[1])).distance_to(point)<=radius and absf(altitude-float(c.top_alt))<12.0: return c.merged({"from_top":true})
	return {}

# ------------------------------------------------------------------ S43 volumes
## Every volume holding this point at this altitude.
func volumes_at(point: Vector2,altitude: float) -> Array:
	var out: Array=[]
	for v in volumes:
		if (v.rect as Rect2).has_point(point) and altitude>=float(v.lo)-0.5 and altitude<=float(v.hi)+0.5: out.append(v)
	return out
## The first volume of a kind holding this point at this altitude, or {}.
func volume_at(point: Vector2,altitude: float,kind: String) -> Dictionary:
	for v in volumes:
		if str(v.kind)!=kind and not (kind=="water_deep" and str(v.kind)=="rising_water"): continue
		if (v.rect as Rect2).has_point(point) and altitude>=float(v.lo)-0.5 and altitude<=float(v.hi)+0.5: return v
	return {}
## Deep water (still or rising) whose surface is above this altitude here, or {}.
func water_at(point: Vector2,altitude: float) -> Dictionary:
	var w=volume_at(point,altitude,"water_deep")
	return w if not w.is_empty() and altitude<float(w.hi)-0.01 else {}
## Wind strength now (S43): a 4 s cycle, strong for its first 1.5 s, a breeze the rest.
func wind_strength(v: Dictionary) -> float:
	var cycle=float(v.get("cycle",4.0))
	var phase=fposmod(time+float(v.get("phase",0.0)),cycle)
	return 1.0 if phase<float(v.get("strong_s",1.5)) else float(v.get("calm",0.3))
## The distance from a point on a surface to its nearest open edge (INF when every edge is closed).
func open_edge_distance(s: WalkSurface,point: Vector2) -> float:
	var d=INF
	var r=s.bounds
	if str(s.edges.get("w","open"))=="open": d=minf(d,point.x-r.position.x)
	if str(s.edges.get("e","open"))=="open": d=minf(d,r.end.x-point.x)
	if str(s.edges.get("n","open"))=="open": d=minf(d,point.y-r.position.y)
	if str(s.edges.get("s","open"))=="open": d=minf(d,r.end.y-point.y)
	return d

# ------------------------------------------------------------------ S43 room clock: movers, crumbling, rising water
## Advance the room's clock: movers take their places, crumbled floors fall and return, water rises.
func advance(dt: float) -> void:
	time+=dt
	for m in movers:
		var s: WalkSurface=index.get(str(m.surface))
		if s==null: continue
		var o=mover_offset(m,time)
		s.set_offset(o)
		for ob in obstacles:
			if ob.get("block",false) and str(ob.id)==s.id:
				if not ob.has("origin"):
					ob.origin=(ob.footprint as Rect2).position
					ob.origin_base=float(ob.base)
				ob.footprint=Rect2(ob.origin+Vector2(o.x,o.y),(ob.footprint as Rect2).size)
				ob.base=float(ob.origin_base)+o.z
	for sid in crumbles.keys():
		var cr: Dictionary=crumbles[sid]
		var cs: WalkSurface=index.get(sid)
		var vol: Dictionary=crumble_volume(sid)
		if cs==null: continue
		if not cs.disabled and time-float(cr.start)>=float(vol.get("break_s",0.8)):
			cs.disabled=true
			cr.broken_at=time
		elif cs.disabled and float(cr.get("broken_at",-1.0))>=0.0 and time-float(cr.broken_at)>=float(vol.get("return_s",5.0)):
			cs.disabled=false
			crumbles.erase(sid)
	for vid in water_goals.keys():
		var g: Dictionary=water_goals[vid]
		for v in volumes:
			if str(v.id)!=vid: continue
			var k=clampf((time-float(g.t0))/maxf(0.01,float(g.over)),0.0,1.0)
			v.hi=lerpf(float(g.from),float(g.to),k)
			if k>=1.0:
				water_goals.erase(vid)
				# A flood that holds, then drains back to its old level.
				if g.has("back"): water_goals[vid]={"from":float(g.to),"to":float(g.back),"t0":time+float(g.get("hold",0.0)),"over":float(g.over)}
## A mover's offset at room time t: loop, pingpong, trigger (one trip out and back once stood on), swing (a pendulum
## on a `length` rope through `amp_deg` either side, every `period_s`) or circle (round a `radius` every `period_s`).
func mover_offset(m: Dictionary,t: float) -> Vector3:
	var mode0=str(m.get("mode","pingpong"))
	if mode0=="swing" or mode0=="circle":
		var a=TAU*t/maxf(0.5,float(m.get("period_s",3.0)))+deg_to_rad(float(m.get("phase_deg",0.0)))
		if mode0=="swing":
			var th=deg_to_rad(float(m.get("amp_deg",30.0)))*sin(a)
			var ln=float(m.get("length",120.0))
			return Vector3(ln*sin(th),0.0,-ln*(1.0-cos(th)))
		var r=float(m.get("radius",60.0))
		return Vector3(r*sin(a),0.0,r*(1.0-cos(a)))
	var pts: Array=[Vector3.ZERO]
	for p in m.get("path",[]):
		pts.append(Vector3(float(p[0]),float(p[1]),float(p[2]) if p.size()>2 else 0.0))
	var mode=str(m.get("mode","pingpong"))
	if mode=="loop": pts.append(Vector3.ZERO)
	var total=0.0
	for i in range(1,pts.size()): total+=pts[i].distance_to(pts[i-1])
	var speed=maxf(1.0,float(m.get("speed",60.0)))
	var wait=float(m.get("wait_s",1.0))
	var leg=total/speed
	if total<=0.0: return Vector3.ZERO
	var d=0.0
	if mode=="loop":
		var tt=fposmod(t,leg+wait)
		if tt<wait: return Vector3.ZERO
		d=(tt-wait)*speed
	else:
		var tt=fposmod(t,2.0*(leg+wait))
		if mode=="trigger":
			if float(m.trigger_t)<0.0: return Vector3.ZERO
			tt=t-float(m.trigger_t)
			if tt>=2.0*leg+wait:
				m.trigger_t=-1.0
				return Vector3.ZERO
			tt+=wait   # a trigger leaves at once
		if tt<wait: d=0.0
		elif tt<wait+leg: d=(tt-wait)*speed
		elif tt<2.0*wait+leg: d=total
		else: d=total-(tt-2.0*wait-leg)*speed
	return _along(pts,clampf(d,0.0,total))
static func _along(pts: Array,d: float) -> Vector3:
	var left=d
	for i in range(1,pts.size()):
		var seg: float=pts[i].distance_to(pts[i-1])
		if left<=seg and seg>0.0: return pts[i-1].lerp(pts[i],left/seg)
		left-=seg
	return pts[pts.size()-1]
## A body stepped onto a trigger mover: it sets off (once, until it returns).
func trigger_mover(surface_id: String) -> void:
	for m in movers:
		if str(m.surface)==surface_id and str(m.get("mode",""))=="trigger" and float(m.trigger_t)<0.0: m.trigger_t=time
func is_mover(surface_id: String) -> bool:
	for m in movers:
		if str(m.surface)==surface_id: return true
	return false
func crumble_volume(surface_id: String) -> Dictionary:
	for v in volumes:
		if str(v.kind)=="crumble" and str(v.get("surface",""))==surface_id: return v
	return {}
## A body stands on this surface: a crumbling floor starts to go (S43).
func touch(surface_id: String) -> void:
	if crumbles.has(surface_id) or crumble_volume(surface_id).is_empty(): return
	crumbles[surface_id]={"start":time,"broken_at":-1.0}
## A Plunge breaks a cracked floor for the rest of the visit.
func break_surface(surface_id: String) -> void:
	var s: WalkSurface=index.get(surface_id)
	if s: s.disabled=true
	for ob in obstacles:
		if str(ob.get("id",""))==surface_id: ob.disabled=true
## Rising water (S43): a water volume's surface moves to `to` over `over_s`.
func raise_water(volume_id: String,to: float,over_s: float,hold_s:=-1.0,back_to:=NAN) -> void:
	for v in volumes:
		if str(v.id)!=volume_id: continue
		var g={"from":float(v.hi),"to":to,"t0":time,"over":over_s}
		if hold_s>=0.0 and not is_nan(back_to):
			g.hold=hold_s
			g.back=back_to
		water_goals[volume_id]=g
## A game event may start a rising-water script (a boss phase, a timer, a lever).
func on_event(event_name: String,payload: Dictionary) -> void:
	for v in volumes:
		for r in v.get("rise",[]):
			if str(r.get("event",""))!=event_name: continue
			var fits=true
			for k in r.get("match",{}):
				if str(payload.get(k,""))!=str(r.match[k]): fits=false
			if fits: raise_water(str(v.id),float(r.to),float(r.get("over_s",4.0)),float(r.get("hold_s",-1.0)),float(r.get("back_to",NAN)))

# ------------------------------------------------------------------ S43 rule 11: the navigation graph
const NAV_GAP=160.0                      # the widest gap a species hops across
const NAV_DROP_GAP=70.0
## The graph of surfaces and block tops a species with this movement {jump, climb, drop} can travel:
## {surface id: [{to, kind, from_pt, to_pt, from_alt, to_alt}]}. Built once per profile per room, the same
## on every build of the same room (surfaces in data order, nearest points by clamping).
func nav_graph(move: Dictionary) -> Dictionary:
	var impulse=float(move.get("jump",0.0))
	var key="%d_%s_%s" % [int(impulse),str(move.get("climb",false)),str(move.get("drop",true))]
	if nav_cache.has(key): return nav_cache[key]
	var max_rise=impulse*impulse/(2.0*MovementSolver.GRAVITY)*0.85
	var nodes: Array=[]
	for s in surfaces:
		if s.kind=="ladder" or s.moving or s.cracked: continue
		nodes.append(s)
	var g: Dictionary={}
	for a in nodes: g[a.id]=[]
	for a in nodes:
		for b in nodes:
			if a==b: continue
			var e=_nav_edge(a,b,impulse,max_rise,bool(move.get("drop",true)))
			if not e.is_empty(): g[a.id].append(e)
	if move.get("climb",false):
		for c in climbables:
			var bottom=str(c.get("bottom","")) if str(c.get("bottom",""))!="" else "ground"
			var top=str(c.get("top",""))
			if not g.has(bottom) or not g.has(top): continue
			var at: Array=c.at
			var top_at: Array=c.get("top_at",c.at)
			var foot=Vector2(float(at[0]),float(at[1]))
			var head=Vector2(float(top_at[0]),float(top_at[1]))
			g[bottom].append({"to":top,"kind":"climb","from_pt":foot,"to_pt":head,"from_alt":float(c.bottom_alt),"to_alt":float(c.top_alt)})
			g[top].append({"to":bottom,"kind":"climb","from_pt":head,"to_pt":foot,"from_alt":float(c.top_alt),"to_alt":float(c.bottom_alt)})
	nav_cache[key]=g
	return g
func _nav_edge(a: WalkSurface,b: WalkSurface,impulse: float,max_rise: float,can_drop: bool) -> Dictionary:
	var inset=Vector2(4,4)
	var ta: Vector2=b.bounds.get_center().clamp(a.bounds.position+inset,a.bounds.end-inset)
	var lb: Vector2=ta.clamp(b.bounds.position+inset,b.bounds.end-inset)
	ta=lb.clamp(a.bounds.position+inset,a.bounds.end-inset)
	var ha=a.height_at(ta)
	var hb=b.height_at(lb)
	var rise=hb-ha
	var overlap=a.bounds.intersects(b.bounds)
	if overlap and rise<-8.0:
		# B lies under A: step off A through its nearest open edge onto B.
		if not can_drop: return {}
		for side in ["s","e","w","n"]:
			if str(a.edges.get(side,"open"))!="open": continue
			var out=ta
			match side:
				"s": out=Vector2(ta.x,a.bounds.end.y+6)
				"n": out=Vector2(ta.x,a.bounds.position.y-6)
				"e": out=Vector2(a.bounds.end.x+6,ta.y)
				"w": out=Vector2(a.bounds.position.x-6,ta.y)
			if b.contains(out) and not blocks_at(out,b.height_at(out),b.stratum):
				var edge_pt=out.clamp(a.bounds.position+Vector2(1,1),a.bounds.end-Vector2(1,1))
				return {"to":b.id,"kind":"drop","from_pt":edge_pt,"to_pt":out,"from_alt":ha,"to_alt":b.height_at(out)}
		return {}
	if overlap and rise>8.0:
		# B sits above A (a platform over the ground, a block top): jump straight up to it from beside or below.
		if impulse<=0.0 or rise>max_rise: return {}
		var take=ta
		if b.is_block:
			# A block's footprint is solid: take off just in front of it.
			take=Vector2(lb.x,b.bounds.end.y+8)
			if not a.contains(take): take=Vector2(lb.x,b.bounds.position.y-8)
			if not a.contains(take): return {}
			lb=Vector2(lb.x,b.bounds.end.y-6 if take.y>b.bounds.end.y else b.bounds.position.y+6)
		if blocks_at(take,a.height_at(take),a.stratum): return {}
		return {"to":b.id,"kind":"jump","from_pt":take,"to_pt":lb,"from_alt":a.height_at(take),"to_alt":b.height_at(lb)}
	var gap=ta.distance_to(lb)
	if gap<=2.0 and absf(rise)<=8.0:
		return {"to":b.id,"kind":"walk","from_pt":ta,"to_pt":lb,"from_alt":ha,"to_alt":hb}
	if rise<-8.0:
		if not can_drop or gap>NAV_DROP_GAP or a.edge_toward(lb)!="open": return {}
		return {"to":b.id,"kind":"drop","from_pt":ta,"to_pt":lb,"from_alt":ha,"to_alt":hb}
	if impulse<=0.0 or rise>max_rise or gap>NAV_GAP or a.edge_toward(lb)=="wall": return {}
	return {"to":b.id,"kind":"jump","from_pt":ta,"to_pt":lb,"from_alt":ha,"to_alt":hb}
## The cheapest chain of edges from one surface to another for this movement, or [] when there is none.
func nav_path(from_id: String,to_id: String,move: Dictionary) -> Array:
	if from_id==to_id: return []
	var g=nav_graph(move)
	if not g.has(from_id) or not g.has(to_id): return []
	var dist: Dictionary={from_id:0.0}
	var prev: Dictionary={}
	var open: Array=[from_id]
	while not open.is_empty():
		var best=0
		for i in open.size():
			if float(dist[open[i]])<float(dist[open[best]]): best=i
		var u=open[best]
		open.remove_at(best)
		if u==to_id: break
		for e in g[u]:
			var cost=float(dist[u])+40.0+(e.from_pt as Vector2).distance_to(e.to_pt)
			if not dist.has(e.to) or cost<float(dist[e.to]):
				dist[e.to]=cost
				prev[e.to]={"from":u,"edge":e}
				if e.to not in open: open.append(e.to)
	if not prev.has(to_id): return []
	var path: Array=[]
	var cur=to_id
	while cur!=from_id:
		path.push_front(prev[cur].edge)
		cur=prev[cur].from
	return path
## The surface under a point at an altitude (what a body there stands on or would land on), or null.
func surface_under(point: Vector2,altitude: float) -> WalkSurface:
	return landing_target(point,altitude+1.0,-INF)
