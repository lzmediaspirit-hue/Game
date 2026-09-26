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
var jump_impulse=530.0               # S43 rule 12: a ground mount jumps with its species impulse (530 on foot)
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
# S43 movement arts and volumes (V2b).
var gliding=false                    # Falling Leaf Glide: descent capped at 120/s (Combat pays the QI)
var air_dash_used=false              # Swallow Dart: once per airtime
var dash_hold=0.0                    # Swallow Dart: seconds left of held altitude
var plunging=false                   # Plunge: dropping at 900/s
var plunge_impact: Dictionary={}     # where a plunge landed, for Combat to resolve {x, y, alt, surface}
var sprinting=false                  # set by the controller each step (Water Skimming, shallow water)
var water: Dictionary={}             # the deep water underfoot: {id, sink, swim_left, still, skimming}
var sink_depth=0.0                   # how far the body has sunk into deep water (presentation, 0-40)
var drowned=false                    # sank without the art: the controller returns the body to a safe spot
var rider_of=""                      # the mover surface carrying this body
var rider_offset=Vector3.ZERO        # the mover's offset when last carried
var volumes_in: Array=[]             # volume IDs the body is inside (volume_entered / volume_left)
var last_safe: Dictionary={}         # {room, surface, x, y}: where a fall returns the body (S43 rule 6)
## The body's movement mode (S43): ground, air, climb, mantle, glide, flight, swim or ride.
func mode() -> String:
	if not climbing.is_empty(): return "climb"
	if flying: return "flight"
	if mantle_left>0.0: return "mantle"
	if surface==null: return "glide" if gliding else "air"
	if not water.is_empty() and float(water.get("swim_left",0.0))>0.0 and not water.get("skimming",false): return "swim"
	if rider_of!="": return "ride"
	return "ground"
func snapshot(tick: int) -> Dictionary:
	return {"schema":2,"tick":tick,"entity_id":entity_id,"zone_id":zone_id,
		"x":plane.x,"y":plane.y,"altitude":altitude,"vz":vertical_speed,
		"vx":velocity.x,"vy":velocity.y,"surface":surface.id if surface else "","air_base":air_base,
		"air_stratum":air_stratum,"jumps_used":jumps_used,
		"landing_assist":landing_assist,"landing_y":landing_y,"departed_surface":departed_surface,"air_peak":air_peak}
