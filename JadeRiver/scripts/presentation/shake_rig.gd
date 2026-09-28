class_name ShakeRig
extends RefCounted
## The camera rig's shake (P6), for both world views: the longer shake and the stronger amplitude win; none with
## Screen shake off or Reduce motion on (MomentRules.shake_amp). `offset` is this frame's jolt in screen px.
## Decision 38: a kick is a single jolt that eases back: the world on screen knocked the way a blow went (the camera
## the other way), under the same settings.

var left := 0.0    ## seconds of shake left
var k := 0.0       ## px of amplitude per second left
var kick_v := Vector2.ZERO   ## the kick's jolt (screen px) at its start
var kick_left := 0.0
var kick_s := 0.12

## `amp` is the starting amplitude in px (default s × shake_amp_per_s: 4 px at 0.25 s).
func add(s: float, amp := -1.0) -> void:
	var a := MomentRules.shake_amp(s, amp)
	if a <= 0.0 or s <= 0.0: return
	k = maxf(k if left > 0.0 else 0.0, a / s)
	left = maxf(left, s)

## A kick of `px` screen px along `dir` over `secs`; a stronger one replaces a weaker one under way.
func kick(dir: Vector2, px: float, secs := 0.12) -> void:
	var a := MomentRules.shake_amp(secs, px)
	if a <= 0.0 or dir.length() < 0.01: return
	if kick_left > 0.0 and kick_v.length() * (kick_left / kick_s) > a: return
	kick_v = dir.normalized() * a
	kick_s = secs
	kick_left = secs

func offset(delta: float) -> Vector2:
	left = maxf(0.0, left - delta)
	kick_left = maxf(0.0, kick_left - delta)
	var jolt := -kick_v * pow(kick_left / maxf(kick_s, 0.001), 2.0) if kick_left > 0.0 else Vector2.ZERO
	return jolt + (Vector2(randf_range(-1, 1), randf_range(-0.75, 0.75)) * k * left if left > 0.0 else Vector2.ZERO)
