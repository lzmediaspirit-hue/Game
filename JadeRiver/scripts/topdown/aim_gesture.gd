class_name AimGesture
extends RefCounted
## Top-down redesign, Phase 2 (decision 30): one thumb on the Attack button or a technique slot, read as a tap or an
## aim. A touch let go before `hold_s` without leaving the `dead_px` circle is a tap (the soft-locked attack or cast);
## held past `hold_s`, or dragged out of the circle, it aims: the direction from the button to the thumb is the
## direction on the ground (the ¾ view keeps screen and plane directions the same), and how far it is dragged
## (up to `drag_px`) sets how far a circle-at-a-point lands. Let go back on the button (within `cancel_px`) after
## dragging out and nothing happens. Left-handed layouts only move the button; the rule is the same.
##
## Decision 35, Attack's drag moves (`move`), on top of the tap and the aim:
## - a long drag, past `long_px`, is the combo's finisher step at once along the drag. Near a screen edge the line is
##   pulled in so the finisher's band out to the edge stays `zone_px` deep (a 48 px target), and never nearer the
##   button than `dead_px` + `zone_px`, so the aim's band keeps its 48 px too;
## - a drag down (toward the camera) within `plunge_deg` of straight down and past `plunge_px`, in the air, is the
##   Plunge when the body can plunge; otherwise it stays an aimed blow;
## - held still for `guard_s` (never leaving the dead circle) it becomes a guard, which the HUD starts (`holding`) and
##   marks (`guarding`); letting go ends it and strikes nothing. A refused guard (a weapon that cannot guard) leaves
##   the let-go a tap.

var kind := "attack"          ## attack or skill
var slot := -1
var origin := Vector2.ZERO    ## the button's centre on screen
var at := Vector2.ZERO        ## the thumb
var t := 0.0
var aiming := false
var left := false             ## the thumb has left the cancel circle at least once
var strayed := false          ## the thumb has left the dead circle at least once (no guard after that)
var guarding := false         ## the hold became a guard or a stance (the HUD started it); letting go ends it
var guard_kind := ""          ## guard or stance, while guarding
var refused := false          ## the hold's guard was refused: letting go is a tap
var screen := Rect2(0, 0, 1280, 720)   ## the HUD's canvas, whose edges pull the finisher's line in

static func conf(key: String, fallback = 0.0):
	return TopdownAim.cfg(key, fallback)

func _init(k: String, button: Vector2, s := -1) -> void:
	kind = k
	origin = button
	at = button
	slot = s

func advance(delta: float) -> void:
	t += delta
	if t >= float(conf("hold_s", 0.18)): aiming = true

func drag(p: Vector2) -> void:
	at = p
	var n := (p - origin).length()
	if n > float(conf("dead_px", 18)):
		aiming = true
		strayed = true
	if n > float(conf("cancel_px", 40)): left = true

## The aim on the ground: a unit direction (zero while the thumb sits on the button).
func dir() -> Vector2:
	var d := at - origin
	return d.normalized() if d.length() > float(conf("dead_px", 18)) else Vector2.ZERO

## How far along its reach the aim goes, 0..1, by the drag's length past the dead circle.
func reach_k() -> float:
	var dead := float(conf("dead_px", 18))
	return clampf(((at - origin).length() - dead) / maxf(1.0, float(conf("drag_px", 120)) - dead), 0.0, 1.0)

## What letting go does: tap, aim (with a direction) or cancel.
func release() -> String:
	if left and (at - origin).length() <= float(conf("cancel_px", 40)): return "cancel"
	if aiming and dir() != Vector2.ZERO: return "aim"
	return "tap"

## Decision 35: what letting go of Attack does now. `air`: the body is off the ground; `plunge_ok`: it can plunge.
## tap, aim, cancel, finisher (a long drag on the ground), plunge (a drag down in the air) or guard (held still).
func move(air := false, plunge_ok := false) -> String:
	if guarding: return "guard"
	var r := release()
	if r != "aim" or kind != "attack": return r
	if air: return "plunge" if plunge_ok and is_down() else "aim"
	return "finisher" if is_long() else "aim"

## Held still long enough to guard, and not yet guarding or refused.
func holding() -> bool:
	return kind == "attack" and not strayed and not guarding and not refused and t >= float(conf("guard_s", 0.3))

## How far the thumb must go along `d` for the finisher: `long_px`, pulled in near the screen's edges so the band from
## it to the edge stays `zone_px` deep, and never nearer the button than `dead_px` + `zone_px`.
func long_px(d: Vector2) -> float:
	var want := float(conf("long_px", 120))
	if d.length() < 0.001: return want
	var zone := float(conf("zone_px", 48))
	return clampf(edge_room(d.normalized()) - zone, float(conf("dead_px", 18)) + zone, want)

## The distance from the button's centre to the screen's edge along the unit `d`.
func edge_room(d: Vector2) -> float:
	var best := INF
	if d.x > 0.0001: best = minf(best, (screen.end.x - origin.x) / d.x)
	elif d.x < -0.0001: best = minf(best, (screen.position.x - origin.x) / d.x)
	if d.y > 0.0001: best = minf(best, (screen.end.y - origin.y) / d.y)
	elif d.y < -0.0001: best = minf(best, (screen.position.y - origin.y) / d.y)
	return best

## Past the finisher's line in the drag's direction.
func is_long() -> bool:
	var d := dir()
	return d != Vector2.ZERO and (at - origin).length() >= long_px(d)

## Down toward the camera: within `plunge_deg` of straight down, past `plunge_px`.
func is_down() -> bool:
	var d := dir()
	if d == Vector2.ZERO or (at - origin).length() < float(conf("plunge_px", 48)): return false
	return absf(rad_to_deg(d.angle_to(Vector2.DOWN))) <= float(conf("plunge_deg", 35))
