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
# Flight (S18, Cloud Stride 1): no gravity; climb is the vertical input (-1 descend .. 1 rise).
var wall_step_used=false   # Wall-Step (secret art): one kick off a wall per time in the air
var flying=false
var climb=0.0
var fly_climb_speed=220.0
var fly_ceiling=340.0
# S43 traversal. Movement arts the actor knows (an unbound legacy actor knows the old set); the
# coyote and jump-buffer timers; Wall-Step kicks per airtime; the climbable being climbed.
var arts: Dictionary={"double_jump":true,"wall_step":true,"drop_through":true,"mantle":true,"climb":true}
var coyote_left=0.0
var buffer_left=0.0
var wall_kicks=0
var climbing: Dictionary={}          # {id, kind, at, top_at, bottom_alt, top_alt, bottom, top} while in climb mode
var mantle_left=0.0                  # a ledge mantle in progress (presentation pose)
var events: Array=[]                 # traversal events this step, for the authority to announce
func snapshot(tick: int) -> Dictionary:
	return {"schema":2,"tick":tick,"entity_id":entity_id,"zone_id":zone_id,
		"x":plane.x,"y":plane.y,"altitude":altitude,"vz":vertical_speed,
		"vx":velocity.x,"vy":velocity.y,"surface":surface.id if surface else "","air_base":air_base,
		"air_stratum":air_stratum,"jumps_used":jumps_used,
		"landing_assist":landing_assist,"landing_y":landing_y,"departed_surface":departed_surface,"air_peak":air_peak}
