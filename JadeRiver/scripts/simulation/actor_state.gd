class_name ActorState
extends RefCounted
## A body as the authorities see it: the top-down player's motor mirrored onto it each frame (TopdownPlayer), a walk's
## or a test's placed by hand. Simulation state contains no scene nodes, textures, input devices, or save paths. (The
## side view's solver state, its jumps, landings, ladders' timers, water and movers, went with the side view in S12a;
## S12c mirrors back what the authorities read of it: the wading, and the volumes the body is in.)
var entity_id="local-disciple"
var zone_id="jade_river"
var plane=Vector2(340,800)
var altitude=0.0
var vertical_speed=0.0
var velocity=Vector2.ZERO
var surface: WalkSurface             # the ground under the feet (the grid's stand-in), null in the air
var flying=false                     # Cloud Stride (S18), while Combat holds it
# S43 traversal: the movement arts the body knows, the climbable face it is on, the traversal events it collects.
var arts: Dictionary={"double_jump":true,"wall_step":true,"drop_through":true,"mantle":true,"climb":true}
var climbing: Dictionary={}          # {id, kind} while on a climbable face
var events: Array=[]                 # traversal events this step, for LocalAuthority.announce
# S43 movement arts (V2b).
var gliding=false                    # Falling Leaf Glide (Combat pays the QI)
var air_dash_used=false              # Swallow Dart: once per airtime
var dash_hold=0.0                    # Swallow Dart: seconds left of held altitude
var plunging=false                   # Plunge: dropping at 900/s
var plunge_impact: Dictionary={}     # where a plunge landed, for Combat to resolve {x, y, alt, surface}
var frozen_ground=false              # v1.2 a Water Sphere freezes the shallows under the bearer: no wading slowdown
var wading=false                     # S12c: the shallows drag at the feet (no dodge: Combat), from the motor
var volumes_in: Array=[]             # S12c: the side view's volumes the body is in, {id, kind} (volume_entered / volume_left)
## The body's movement mode (S43): ground, air, climb, glide or flight.
func mode() -> String:
	if not climbing.is_empty(): return "climb"
	if flying: return "flight"
	if surface==null: return "glide" if gliding else "air"
	return "ground"
