class_name ShakeRig
extends RefCounted
## The camera rig's shake (P6), for both world views: the longer shake and the stronger amplitude win; none with
## Screen shake off or Reduce motion on (MomentRules.shake_amp). `offset` is this frame's jolt in screen px.

var left := 0.0    ## seconds of shake left
var k := 0.0       ## px of amplitude per second left

## `amp` is the starting amplitude in px (default s × shake_amp_per_s: 4 px at 0.25 s).
func add(s: float, amp := -1.0) -> void:
	var a := MomentRules.shake_amp(s, amp)
	if a <= 0.0 or s <= 0.0: return
	k = maxf(k if left > 0.0 else 0.0, a / s)
	left = maxf(left, s)

func offset(delta: float) -> Vector2:
	left = maxf(0.0, left - delta)
	return Vector2(randf_range(-1, 1), randf_range(-0.75, 0.75)) * k * left if left > 0.0 else Vector2.ZERO
