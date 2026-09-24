class_name RoomTravel
extends RefCounted
## Gate traversal is a crossing, not proximity or touching a world boundary.
const BODY_RADIUS=16.0
const FOOT_DEPTH=10.0
const BODY_HEIGHT=90.0
var gates: Array=[]
var previous=Vector2(INF,INF)
var previous_height=0.0
var armed=""
static func specs(width: float) -> Array:
	return [{"id":"west_gate","x":150.0,"direction":-1,"y_min":838.0,"y_max":894.0,"half_width":110.0,"clearance":230.0},
		{"id":"east_gate","x":width-150,"direction":1,"y_min":838.0,"y_max":894.0,"half_width":110.0,"clearance":230.0}]
static func arrival(width: float,direction: int) -> Vector2:
	return Vector2(300 if direction>0 else width-300,866)
func reset(point: Vector2,height=0.0):
	previous=point
	previous_height=height
	armed=""
func advance(state: ActorState) -> int:
	if not previous.is_finite():
		reset(state.plane,state.altitude)
		return 0
	var from=previous
	var height=maxf(previous_height,state.altitude)
	previous=state.plane
	previous_height=state.altitude
	var ground=(state.surface.stratum if state.surface else state.air_stratum)=="ground"
	for gate in gates:
		var direction=int(gate.direction)
		var a=(from.x-float(gate.x))*direction
		var b=(state.plane.x-float(gate.x))*direction
		var extent=float(gate.half_width)+BODY_RADIUS
		var clear=ground and height+BODY_HEIGHT<=float(gate.clearance) and minf(from.y,state.plane.y)>=float(gate.y_min)+FOOT_DEPTH and maxf(from.y,state.plane.y)<=float(gate.y_max)-FOOT_DEPTH
		if not clear or b<=-extent:
			if armed==gate.id: armed=""
			continue
		if a<=-extent and b> -extent: armed=gate.id
		if armed==gate.id and a<extent and b>=extent:
			armed=""
			return direction
	return 0
