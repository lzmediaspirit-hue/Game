class_name ActorState
extends RefCounted
## Simulation state contains no scene nodes, textures, input devices, or save paths.
var entity_id="local-disciple"
var zone_id="jade_river"
var plane=Vector2(340,800)
var altitude=0.0
var air_base=0.0
var vertical_speed=0.0
var velocity=Vector2.ZERO
var surface: WalkSurface
var air_stratum="ground"
var jumps_used=0
var landing_assist=""
var landing_y=0.0
var departed_surface=""
var air_peak=0.0
func snapshot(tick: int) -> Dictionary:
	return {"schema":2,"tick":tick,"entity_id":entity_id,"zone_id":zone_id,
		"x":plane.x,"y":plane.y,"altitude":altitude,"vz":vertical_speed,
		"vx":velocity.x,"vy":velocity.y,"surface":surface.id if surface else "","air_base":air_base,
		"air_stratum":air_stratum,"jumps_used":jumps_used,
		"landing_assist":landing_assist,"landing_y":landing_y,"departed_surface":departed_surface,"air_peak":air_peak}
