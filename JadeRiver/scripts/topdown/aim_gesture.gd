class_name AimGesture
extends RefCounted
## Top-down redesign, Phase 2 (decision 30): one thumb on the Attack button or a technique slot, read as a tap or an
## aim. A touch let go before `hold_s` without leaving the `dead_px` circle is a tap (the soft-locked attack or cast);
## held past `hold_s`, or dragged out of the circle, it aims: the direction from the button to the thumb is the
## direction on the ground (the ¾ view keeps screen and plane directions the same), and how far it is dragged
## (up to `drag_px`) sets how far a circle-at-a-point lands. Let go back on the button (within `cancel_px`) after
## dragging out and nothing happens. Left-handed layouts only move the button; the rule is the same.

var kind := "attack"          ## attack or skill
var slot := -1
var origin := Vector2.ZERO    ## the button's centre on screen
var at := Vector2.ZERO        ## the thumb
var t := 0.0
var aiming := false
var left := false             ## the thumb has left the cancel circle at least once

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
	if n > float(conf("dead_px", 18)): aiming = true
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
