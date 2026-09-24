# A body in the world (player, enemy, NPC). Plain data + small helpers; the World drives it.
class_name Actor
extends RefCounted

var kind := "enemy"         # player | enemy | npc
var type := ""              # enemy type or npc id
var def: Dictionary = {}
var x := 0.0
var d := 40.0
var h := 0.0
var vz := 0.0
var grounded := true
var surf := "ground"
var ignore := ""            # surface ignored while dropping through
var ignore_t := 0
var facing := 1
var hp := 1.0
var max_hp := 1.0
var atk := 1.0
var state := "idle"
var t := 0                  # frames in current state
var anim := 0.0
var flash := 0
var inv := 0                # invulnerability frames
var stun := 0
var kb := 0.0               # knockback velocity (x)
var cd := 0                 # attack cooldown frames
var alive := true
var dead_t := 0
var home_x := 0.0
var home_d := 0.0
var home_surf := "ground"
var spawn: Dictionary = {}
var boss_id := ""
var scale := 1.0
var phase := 1
var hit_ids := {}           # per-swing hit registry
var burn := 0
var burn_dmg := 0.0
var aggro := false
var tele := Vector3.ZERO    # telegraph target for bosses
var extra := {}


func set_state(s: String) -> void:
	if state != s:
		state = s
		t = 0


func foot_y(base_y: float) -> float:
	return base_y + d - h
