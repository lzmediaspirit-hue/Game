class_name ZoneGeometry
extends RefCounted
## A room's surfaces for the shared simulation: on the grid one stand-in ground the size of the room
## (TopdownRoom.geometry_def), so the authorities' ActorState tells ground from air; the room's clock, which the grid's
## rafts, lifts and lanterns ride (TopdownTraverse.time); and the movers' rule they ride by (mover_offset). The side
## view's solids, ladders, volumes, movers, crumbling floors, rising water and navigation graph went with the side view
## in S12a; S12c retired its last volume query (Combat's shallow water before a dodge reads ActorState.wading, from the
## motor's wading floors).
var surfaces: Array[WalkSurface]=[]
var index: Dictionary={}
var bounds: Rect2
var time=0.0                             # the room's clock
func configure(data: Dictionary):
	surfaces.clear()
	index.clear()
	time=0.0
	var r=data.bounds
	bounds=Rect2(r[0],r[1],r[2],r[3])
	for spec in data.surfaces:
		var surface=WalkSurface.new(spec)
		assert(not index.has(surface.id),"Duplicate surface ID")
		surfaces.append(surface)
		index[surface.id]=surface
## Advance the room's clock.
func advance(dt: float) -> void:
	time+=dt
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
			if float(m.get("trigger_t",-1.0))<0.0: return Vector3.ZERO
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
