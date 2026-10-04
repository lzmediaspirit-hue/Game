class_name MovementSolver
extends RefCounted
## The movement arts Combat starts on a body's state (ActorState: the authorities' mirror of the top-down motor), and
## the numbers the brains and the pets still read. The side view's solver (walking, jumping, climbing and landing on
## its surfaces, its water and its volumes) went with the side view in S12a: the TopdownMotor moves the body on the grid.
const GRAVITY=1150.0                 # a hop's fall where no grid gives its own (EnemyBrain.start_hop)
const AIR_DASH_HOLD=0.25             # Swallow Dart: the height held while darting 140
const PLUNGE_SPEED=900.0
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
