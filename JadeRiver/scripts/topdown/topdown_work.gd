class_name TopdownWork
extends RefCounted
## Decision 43, the living world (docs/redesign/art_bible.md §14.13): a villager's or a disciple's work loop, for a
## figure of the room (TopdownPlaces.Figure). The loop (data/topdown/life.json `loops`, built by
## tools/data/topdown_life.py) is a few steps at each work spot, each a character action held for some seconds with a
## cue for the view (dust off a broom, sparks off an anvil), and a walk between the spots; a tool held while at it (a
## broom, a rod) or carried between the spots and set down at them (a shoulder pole, a basket), and a weapon worn for it
## (a disciple's training sword).
##   - The spots lie within the leash of the person's own spot (life.json `leash` tiles, checked as the data is built),
##     so standing beside a worker the talk is always in reach of the World authority's rule round that spot.
##   - At the player's side (the context's focus, a talk) or with the player close by, they stop, turn to the player and
##     wait; they take up the work again a moment after the player leaves.
##   - Someone whose marker calls (a quest waiting, QuestAuthority.marker_calls) walks back to their first spot (their
##     own) and works there without leaving it, so the marker and the talk stay where the quest's tracker points.
##   - A staged scene has them while it plays (decision 39); they start again from where it left them.
## The loop runs on its own clock (no random draw): the same room plays the same way, each worker at its own phase.

const NOTICE := 72.0        ## world units: the player this close stops a worker, who turns to the player
const RESUME_S := 1.2       ## seconds after the player leaves before the work starts again
const ARRIVE := 2.0         ## world units: close enough to a spot
const CARRIED := ["pole", "basket"]   ## tools carried between the spots and set down at them

var loop: Dictionary = {}
var spots: Array = []       ## [ground point (world units), facing row, steps (Array)]
var home := Vector2.ZERO    ## the person's own spot (world units)
var alt := 0.0
var name := ""
# The state.
var at := 0                 ## the spot being worked, or walked to
var walking := false
var step := 0
var t := 0.0
var pos := Vector2.ZERO
var action := "idle"
var row := "s"
var tool := ""              ## held: broom, rod, pole, basket
var tool_down := ""         ## set on the ground beside them: pole (its baskets), basket
var paused := 0.0           ## > 0: stopped for the player (counting down once the player has gone)
var homing := false         ## the marker calls: working at the first spot only
var step_cue := ""          ## the cue of the step under way
var cue := ""               ## the cue of a step begun this frame ("" otherwise), for the view's effects
var hit := false            ## the step's action reached its hit frame this frame (a chop, a hammer blow)
var _hit_done := false

## A loop for the person whose own spot is `home_p` (world units) at height `z`: `w` is the room's entry for them
## ({loop, spots}), `loops` the data's loop table.
func _init(w: Dictionary, loops: Dictionary, home_p: Vector2, z: float, who := "") -> void:
	loop = loops.get(str(w.get("loop", "")), {})
	home = home_p
	alt = z
	name = who
	for s in w.get("spots", []):
		var p := TopdownRoom.cell_point(s)
		var steps: Array = loop.get("at", [])
		if (s as Array).size() > 3: steps = (loop.get("steps", {}) as Dictionary).get(str(s[3]), steps)
		spots.append([p, str(s[2]) if (s as Array).size() > 2 else "s", steps])
	pos = home
	if spots.is_empty(): return
	pos = spots[0][0]
	_begin(0)
	# Each worker starts at its own phase of its first step: a hash of its name.
	var h := 0
	for ch in who: h = (h * 31 + ch.unicode_at(0)) & 0xFFFF
	t = float(h % 1000) / 1000.0 * 1.5
	cue = ""

## Is this a loop that moves between spots?
func moves() -> bool:
	return spots.size() > 1

## The work's pose this frame: advance the loop by `delta`. `player` is the player's ground point (INF when there is
## none), `focus` whether the context offers this person, `calls` whether their marker calls the player over.
func advance(delta: float, player: Vector2, focus: bool, calls: bool) -> void:
	cue = ""
	hit = false
	if spots.is_empty(): return
	if focus or (player.x < INF and player.distance_to(pos) < NOTICE):
		# Stopped for the player: turned to them, standing (a meditation keeps its seat), what they carry set down.
		paused = RESUME_S
		if player.x < INF and player.distance_to(pos) > 1.0: row = TopdownMotor.nearest_row(player - pos, row, TopdownMotor.ROW_ANGLES, 10.0)
		if action != "meditate": action = "idle"
		_tools(false)
		return
	if paused > 0.0:
		paused -= delta
		if paused > 0.0: return
		_resume()
	if calls != homing:
		homing = calls
		if homing:
			at = 0
			_resume()
	t += delta
	if walking:
		var goal: Vector2 = spots[at][0]
		var speed := float(loop.get("speed", 36))
		var d := goal - pos
		if d.length() <= maxf(ARRIVE, speed * delta):
			pos = goal
			_begin(at)
		else:
			pos += d.normalized() * speed * delta
			row = TopdownMotor.nearest_row(d, row, TopdownMotor.ROW_ANGLES, 10.0)
			action = str(loop.get("walk", "walk"))
			_tools(true)
		return
	var steps: Array = spots[at][2]
	if steps.is_empty():
		action = "idle"
		return
	var st: Array = steps[step % steps.size()]
	var dur := float(st[1])
	if not _hit_done and t >= hit_at(str(st[0]), dur):
		_hit_done = true
		hit = true
	if t >= dur:
		t -= dur
		step += 1
		if step >= steps.size():
			# The steps done here: on to the next spot (a worker whose marker calls stays at the first).
			step = 0
			if moves() and not homing:
				at = (at + 1) % spots.size()
				walking = true
				step_cue = ""
				return
		_step_begin(steps[step % steps.size()])

## Take up the work where it stands: walk on to the spot if not there, else begin its steps.
func _resume() -> void:
	walking = pos.distance_to(spots[at][0]) > ARRIVE
	if not walking: _begin(at)
	else: step_cue = ""

func _begin(i: int) -> void:
	at = i
	walking = false
	step = 0
	t = 0.0
	row = str(spots[i][1])
	var steps: Array = spots[i][2]
	if not steps.is_empty(): _step_begin(steps[0])
	else: action = "idle"

func _step_begin(st: Array) -> void:
	action = TopdownFigure.resolve(str(st[0]))
	step_cue = str(st[2]) if st.size() > 2 else ""
	cue = step_cue
	_hit_done = false
	row = str(spots[at][1])
	_tools(false)

## What is held and what is set down: a broom or a rod stays in hand; a pole or a basket is carried on the way and set
## down at a spot.
func _tools(on_the_way: bool) -> void:
	var lt := str(loop.get("tool", ""))
	if lt in CARRIED:
		tool = lt if on_the_way else ""
		tool_down = "" if on_the_way else lt
	else:
		tool = lt if lt != "rod" or not on_the_way else ""
		tool_down = ""

## When in a step its blow lands: the action's hit frame on its own clock (a chop, a hammer blow), else its middle.
static func hit_at(act: String, dur: float) -> float:
	var sp := TopdownFigure.spec(act)
	var hf := int(sp.get("hit", -1))
	if hf < 0: return dur * 0.5
	return minf(dur * 0.9, float(hf) / maxf(1.0, float(sp.get("fps", 10.0))))

## The frame of the pose now (a one-shot holds its last frame).
func frame() -> int:
	return TopdownFigure.frame_at(action, t)

## Where the worker faces: a look round swings the head a row either way and back on the loop's clock.
func facing() -> String:
	if walking or paused > 0.0 or step_cue != "look": return row
	var rows := ["s", "se", "e", "ne", "n", "nw", "w", "sw"]
	var i := rows.find(row)
	if i < 0: return row
	return rows[posmod(i + [0, 1, 0, -1][int(t / 0.9) % 4], 8)]
