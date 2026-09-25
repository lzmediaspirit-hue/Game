class_name EnemyState
extends RefCounted
## S13 · One live monster: StatBlock-equivalent stats, pools, AI state, spawn
## point, aggro target and threat list. Uses the same combat rules as players.

var uid := 0
var def_id := ""
var def: Dictionary = {}
var level := 1
var role := "normal"
var elite := false
var element := "none"
var realm_index := 0
var plane := Vector2.ZERO
var altitude := 0.0
var hover := 0.0                      # flying creatures hover above the ground plane
var surface_id := ""
var home_surface := ""                # S43: the surface it spawned on (patrol and return)
var hop: Dictionary = {}              # S43: a jump, drop or climb along a navigation edge in progress
var spawn_index := -1
var spawn_point := Vector2.ZERO
var facing := -1
var velocity := Vector2.ZERO
var stats: Dictionary = {}
var pools := ResourcePool.new()
var alive := true
var ai := {"state": "idle", "timer": 1.0, "target": "", "attack": 0, "patrol_x": 0.0, "hit_done": false, "phase": -1, "dash_left": 0.0}
var threat: Dictionary = {}
var action := "idle"                  # presentation hint: idle walk windup attack hurt death
var action_time := 0.0
var hurt_time := 0.0
var flash := 0.0
var dead_time := 0.0
var knockback := 0.0
var first_hit_by_player := false
var summoned := false
var invulnerable := false
var hidden := false
var pet_owner := ""                   # wild pets and tamed forms
var team := "enemy"

func half_width() -> float:
	return float(def.get("half_width", 20))

func height() -> float:
	return float(def.get("height", 40))

func is_boss() -> bool:
	return role in ["field_boss", "dungeon_boss", "story_boss"]

func display_name() -> String:
	return str(def.get("name", def_id))

func snapshot() -> Dictionary:
	return {"uid": uid, "def": def_id, "level": level, "elite": elite, "x": plane.x, "y": plane.y, "alt": altitude,
		"hp": pools.hp, "state": ai.state, "facing": facing}
