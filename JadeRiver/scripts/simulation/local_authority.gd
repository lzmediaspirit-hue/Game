class_name LocalAuthority
extends RefCounted
## Offline authority boundary. Transport/authentication belong outside this class.
## Clients supply intent, never position, elevation, equipment, or movement speed.
var tick=0
var last_sequence=-1
var state: ActorState
var zone: ZoneGeometry
var actor_id=""                          # the character this body belongs to, for traversal events (S43)
func _init(actor: ActorState,geometry: ZoneGeometry):
	state=actor
	zone=geometry
func move(sequence: int,axis: Vector2,delta: float,server_speed: float) -> bool:
	if sequence<=last_sequence or not axis.is_finite() or not is_finite(delta) or delta<=0 or delta>3.0: return false
	if not is_finite(server_speed) or server_speed<0: return false
	last_sequence=sequence
	tick+=1
	MovementSolver.advance(state,zone,delta,axis.limit_length()*server_speed)
	_announce()
	return true
func jump() -> bool:
	var ok=MovementSolver.jump(state)
	_announce()
	return ok
func wall_step(push:=0) -> int:
	var side=MovementSolver.wall_step(state,zone,push)
	_announce()
	return side
## Drop through the platform underfoot (S43 rule 3).
func drop_through() -> bool:
	var ok=MovementSolver.drop_through(state)
	_announce()
	return ok
## Climb the ladder, rope, vine or chain in reach (S43 rule 5); {} climbable means the nearest one.
func climb(climbable:={}) -> bool:
	var c=climbable if not climbable.is_empty() else zone.climbable_near(state.plane,state.altitude)
	if c.is_empty() or state.surface==null: return false
	var ok=MovementSolver.start_climb(state,c,bool(c.get("from_top",false)))
	_announce()
	return ok
func release_climb(side: int,jumped: bool) -> bool:
	var ok=MovementSolver.release_climb(state,side,jumped)
	_announce()
	return ok
## A fall into the void returned the body to a safe position (S43 rule 6).
func fell_out(recovered_to: Dictionary) -> void:
	state.events.append({"name":"fell_out","recovered_to":recovered_to})
	_announce()
## Traversal events (jumped, landed, wall_kicked, art_used, climb_started, climb_finished, fell_out) go out
## on the event bus for presentation, achievements and quests.
func _announce() -> void:
	for e in state.events:
		var p: Dictionary=e.duplicate()
		var n=str(p.name)
		p.erase("name")
		p.actor=actor_id if actor_id!="" else state.entity_id
		GameEvents.emit_event(n,p)
	state.events.clear()
## Flight is granted by the Combat authority (which pays its QI); this only moves the body.
func fly(on: bool,climb_speed:=220.0,ceiling:=340.0) -> bool:
	if on: return MovementSolver.start_flight(state,climb_speed,ceiling)
	if state.flying: MovementSolver.stop_flight(state)
	return true
func set_climb(value: float) -> void:
	state.climb=clampf(value,-1.0,1.0) if is_finite(value) else 0.0
func snapshot() -> Dictionary: return state.snapshot(tick)
func restore_authoritative_snapshot(value: Dictionary) -> bool:
	# For trusted server snapshots or replay only; never expose this to client commands.
	if int(value.get("schema",0)) not in [1,2] or value.get("entity_id")!=state.entity_id or value.get("zone_id")!=state.zone_id: return false
	for key in ["tick","x","y","altitude","vz","vx","vy","air_base"]:
		if not (value.get(key) is int or value.get(key) is float) or not is_finite(float(value[key])): return false
	if int(value.tick)<tick: return false
	var position=Vector2(value.x,value.y)
	if not zone.bounds.has_point(position): return false
	var support: WalkSurface=zone.index.get(str(value.get("surface","")))
	if str(value.get("surface",""))!="" and support==null: return false
	if support and (not support.contains(position) or absf(value.altitude-support.height_at(position))>0.01): return false
	var stratum=support.stratum if support else str(value.get("air_stratum","ground"))
	if zone.blocks_at(position,float(value.altitude),stratum): return false
	var jumps=value.get("jumps_used",0 if support else 1)
	if not (jumps is int or jumps is float) or not is_finite(float(jumps)) or float(jumps)!=int(jumps) or int(jumps)<0 or int(jumps)>2: return false
	var assist=str(value.get("landing_assist",""))
	var lane=value.get("landing_y",0.0)
	var departed=str(value.get("departed_surface",""))
	var peak=value.get("air_peak",maxf(float(value.altitude),float(value.air_base)))
	if not (peak is int or peak is float) or not is_finite(float(peak)): return false
	if departed!="" and not zone.index.has(departed): return false
	if assist!="" and not zone.index.has(assist): return false
	if not (lane is int or lane is float) or not is_finite(float(lane)): return false
	state.plane=position
	state.altitude=value.altitude
	state.vertical_speed=value.vz
	state.velocity=Vector2(value.vx,value.vy)
	state.air_base=value.air_base
	state.air_stratum=str(value.get("air_stratum",support.stratum if support else "ground"))
	state.surface=support
	state.jumps_used=0 if support else int(jumps)
	state.landing_assist=assist
	state.landing_y=lane
	state.departed_surface=departed
	state.air_peak=peak
	state.flying=false
	tick=int(value.tick)
	return true
