extends Node2D
## A stand-in for the top-down player (TopdownPlayer) under a HUD in the tests: the members the HUD reads and the calls
## it makes, each doing nothing but count. Since S12a the HUD drives only the top-down player (it aims on the plane,
## reads the motor's ground and facing, clears the aim it showed), so a bare stand-in has the top-down player's shape.

## The motor's few fields the HUD reads (TopdownMotor: on the ground, facing).
class Motor:
	var grounded := true
	var dir := Vector2.DOWN
	var flying := false

var actor_id := ""
var plane := Vector2.ZERO
var facing := 1
var altitude := 0.0
var hp := 100.0
var qi := 100.0
var meditating := false
var aim: Dictionary = {}
var motor := Motor.new()
var state := ActorState.new()
var movement := Vector2.ZERO
var joystick_engaged := false
var jump_held := false
var fly_up := false
var fly_down := false
var attack_time := 0.0
var channel_time := 0.0
var channel_action := ""
var last_axis := Vector2.ZERO
var attacks := 0   ## the attacks asked of it (a tap of Attack, an aimed blow, a finisher)
var posed: Array = []

func attack() -> void:
	attacks += 1

func aim_attack(_dir: Vector2, _aimed := true, _finisher := false, _charge_s := 0.0) -> Dictionary:
	attacks += 1
	return {"ok": true}

func finisher(_dir: Vector2, _charge_s := -1.0) -> Dictionary:
	attacks += 1
	return {"ok": true}

func jump() -> void: pass
func dodge() -> void: pass
func climb() -> bool: return false
func plunge_ready() -> bool: return false
func plunge() -> Dictionary: return {"ok": false}
func hold_guard() -> String: return ""
func release_guard() -> void: pass
func use_technique(_slot: int) -> Dictionary: return {"ok": false}
func aim_technique(_slot: int, _dir: Vector2, _k := -1.0, _aimed := true) -> Dictionary: return {"ok": false}
func preview_aim(_kind: String, _slot: int, _dir: Vector2, _k: float, _move := "aim") -> void: pass
func meditate() -> void: pass
func play_place_pose(p: String) -> void: posed.append(p)
func end_place_pose() -> void: posed.append("end")
func reset_sprint() -> void: pass
