# Input state shared by keyboard and touch. Edge flags are consumed by the World each tick.
class_name Ctl
extends RefCounted

var move := Vector2.ZERO     # x = along level, y = depth (down = toward camera)
var guard := false           # held
var jump := false
var attack := false
var dash := false
var interact := false
var meditate := false
var arts := [false, false, false]
var pills := [false, false]
var dash_dir := 0            # from swipe


func clear_edges() -> void:
	jump = false
	attack = false
	dash = false
	interact = false
	meditate = false
	arts = [false, false, false]
	pills = [false, false]
	dash_dir = 0


func reset() -> void:
	clear_edges()
	move = Vector2.ZERO
	guard = false
