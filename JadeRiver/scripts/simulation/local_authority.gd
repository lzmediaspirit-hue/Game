class_name LocalAuthority
extends RefCounted
## The traversal events a body's state collects (jumped, landed, wall_kicked, art_used, climb_started,
## climb_finished, fell_out, mover_boarded, volume_entered, volume_left) go out on the event bus for presentation,
## achievements and quests. The top-down player fills them from its motor (TopdownPlayer: since S12c every one of
## them, the jumps, landings, falls out of a room and volumes as well), Combat when it starts an art on the body
## (Plunge, glide, dash). The side view's movement authority (the body moved by intent through the side solver) went
## with the side view in S12a.

## Emit a body's pending traversal events.
static func announce(body: ActorState,actor:="") -> void:
	for e in body.events:
		var p: Dictionary=e.duplicate()
		var n=str(p.name)
		p.erase("name")
		p.actor=actor if actor!="" else body.entity_id
		GameEvents.emit_event(n,p)
	body.events.clear()
