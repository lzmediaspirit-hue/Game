class_name SceneDirector
extends Node
## Decision 39 (docs/redesign/story_staging.md): plays the staged scenes of data/scenes.json in the top-down world. A
## scene starts when its trigger comes (an event, or the character standing in its room) and its requirement holds, the
## stage is free (no page open, no moment on the screen, no fight for a cut) and the Quest authority lets it begin
## (scene_begin: not seen before). Its steps then run in order: the people walk, face, emote, strike a pose and speak (a
## balloon over the head, or the dialogue page's portrait strip), the camera pans, follows, zooms and shakes, the screen
## fades, flashes and shows a title card, the world plays its effects, sounds and moments, doors open and weather turns.
##
## Three modes: a cut holds the simulation still (Game.pause) and the controls (the HUD's scene_lock) under a letterbox,
## the HUD faded away; a hand-off gives the controls back with a prompt over what to do (a thing, a person, a foe, a
## way, a HUD control) until an event says it is done; a live part plays around the player. A cut never starts in a
## fight, and one a fight breaks into goes on live. A tap moves a line on; a hold skips to the next hand-off (the
## skipped part's checkpoints still asked for). Reduce motion cuts the camera instead of panning it, keeps the letterbox
## and the title from sliding, stills the rain and holds the shake.
##
## Presentation that only asks: its checkpoints (`mark`, `handoff`) go to the Quest authority, which keeps where the
## scene is and applies their effects once, and the end marks it seen. A scene cut short by quitting resumes at its
## last checkpoint, its people where the script had put them. The people of the room go home when it ends. Headless
## (no world: the suites) every step runs on the same clock and is written to `logged`.

var world: Node = null            ## the TopdownWorld (live), or null headless
var hud: Node = null
var moments: Node = null
var headless := true              ## main.gd clears it: the stage is drawn and the world's people moved
var run = null                    ## the scene playing (see _start)
var queue: Array = []             ## scene ids whose trigger came, waiting for the stage
var logged: Array = []            ## {scene, i, do}: each step as it begins (the last 400)
var finished: Array = []          ## {scene, skipped, left}: each scene as it ended
var homeward: Array = []          ## the room's people walking back to their places after a scene
var hold_t := -1.0                ## how long a press has been held in a cut (-1: none)
var fight_override = null         ## tests: true or false stands in for the room
var pages_override = null         ## tests: true or false stands in for the page stack
var reduce_override = null        ## tests: Reduce motion on or off
var stage: Node2D = null
var _by_event: Dictionary = {}    ## event -> [scene rows] it triggers
var _eval_t := 0.0
var _tried: Dictionary = {}       ## scene id -> true: refused by the authority in this room
var _paused := false
var _thunder_t := 0.0
var _drew := false
var hitstop_t := 0.0              ## a staged hit-stop's time left (the stage's clock held)
var _lb_carry := 0.0              ## the letterbox a cut ended with, for a cut that follows straight on
var _lb_carry_t := -1.0

func _ready() -> void:
	for r in ContentDB.all("scenes"):
		var ev := str(r.get("trigger", {}).get("event", ""))
		if ev != "":
			if not _by_event.has(ev): _by_event[ev] = []
			_by_event[ev].append(r)
	GameEvents.event.connect(_on_event)
	if headless: return
	var cl := CanvasLayer.new()
	cl.layer = 6   # over the HUD (5), under a moment's cards (8), the shell (15) and the pages (20)
	add_child(cl)
	stage = SceneStage.new()
	stage.director = self
	cl.add_child(stage)

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)
	if run != null: _end_mode()

func _process(delta: float) -> void:
	advance(delta)

## True while a cut holds the stage (the simulation still, the controls the director's).
func in_cut() -> bool:
	return run != null and run.mode == "cut"

## True while the script runs on the stage's own clock: a cut, a live part, or a hand-off that ends by itself in time.
func busy() -> bool:
	if run == null: return false
	if run.mode != "hand": return true
	var st: Dictionary = run.row.steps[run.i] if run.i < (run.row.steps as Array).size() else {}
	return float(st.get("s", 0.0)) > 0.0

## The seconds of a press held toward a skip, 0..1 of the hold it needs.
func skip_k() -> float:
	return clampf(hold_t / float(SceneRules.cfg().get("skip_hold_s", 0.8)), 0.0, 1.0) if hold_t >= 0.0 else 0.0

func reduce_motion() -> bool:
	return bool(reduce_override) if reduce_override != null else UiKit.reduce_motion()

## Look for a scene to start now (the suites call it after each step of their walk).
func poll() -> void:
	_eval_t = 0.0
	advance(0.0)

## One frame: a scene to start, the script's steps, the people and the camera, the skip held, and the mode.
func advance(delta: float) -> void:
	if run != null and (Game.active() == null or Game.active_id != str(run.actor)):
		_finish(true, true)   # another character took the stage
	if run != null and (Game.room_rt == null or Game.room_rt.room_id != str(run.row.room)):
		_leave()   # the character walked out of the scene's room
	if run == null:
		_lb_carry_t -= delta
		_eval_t -= delta
		if _eval_t <= 0.0:
			_eval_t = 0.25
			var pick := _pick()
			if not pick.is_empty(): _start(pick)
	if run != null:
		# A fight breaks in: the scene goes on around it (unless the scene holds the fight itself: `hold_fight`).
		if run.mode == "cut" and _in_fight() and not run.row.get("hold_fight", false): run.mode = "live"
		# Decision 45: a staged hit-stop holds the stage's clock, its effects and the struck foe a moment.
		var d := delta
		if hitstop_t > 0.0:
			hitstop_t -= delta
			d = 0.0
		if world is TopdownWorld: world.stage_hold = hitstop_t > 0.0
		_play(d)
	if run != null:
		_actors(delta if hitstop_t <= 0.0 else 0.0)
		_camera(delta)
		_weather(delta)
	_homeward(delta)
	if hold_t >= 0.0:
		hold_t += delta
		if hold_t >= float(SceneRules.cfg().get("skip_hold_s", 0.8)) and in_cut():
			hold_t = -1.0
			skip()
	_apply_mode(delta)

# ------------------------------------------------------------------ triggers
func _on_event(n: String, p: Dictionary) -> void:
	var c = Game.active()
	if c == null: return
	if run != null:
		run.heard.append([n, p])
		if run.heard.size() > 96: run.heard = run.heard.slice(-64)
	match n:
		"scene_started":   # the authority let a scene begin: into the log, at the checkpoint it begins from
			logged.append({"scene": str(p.get("scene", "")), "i": int(p.get("at", 0)), "do": "begin"})
		"scene_marked":   # a checkpoint the authority kept: the scene resumes from here
			if run != null and str(p.get("scene", "")) == str(run.id): run.kept = int(p.get("step", 0))
		"character_switched":
			queue.clear()
			homeward.clear()
		"room_entered":
			if str(p.get("actor", "")) == str(c.id):
				_tried.clear()
				homeward.clear()
				queue = queue.filter(func(id): return str(SceneRules.row(id).get("room", "")) == str(p.get("room", "")))
		"scene_ended":   # the authority's word that a scene is over, however it ended
			if str(p.get("actor", "")) == str(c.id): queue.erase(str(p.get("scene", "")))
	for r in _by_event.get(n, []):
		if matches(r.trigger.get("when", {}), p) and not queue.has(str(r.id)): queue.append(str(r.id))
	_eval_t = 0.0

## MomentRules' matchers, with "active" standing for the active character's id wherever it is a value.
func matches(when: Dictionary, p: Dictionary) -> bool:
	var w := {}
	for k in when:
		w[k] = Game.active_id if str(when[k]) == "active" and not str(k) in ["actor", "target"] else when[k]
	return MomentRules.matches(w, p, {"active": Game.active_id})

## The next scene the stage can take: one cut short to resume here, then one whose trigger came, then one this room
## plays as it stands. A scene cut short in another room is closed (seen).
func _pick() -> Dictionary:
	var c = Game.active()
	if c == null or Game.room_rt == null or Game.room_rt.topdown == null or not _stage_free(): return {}
	var here: String = Game.room_rt.room_id
	for id in c.quests.scenes:
		var st: Dictionary = c.quests.scenes[id]
		if not st.has("at"): continue
		var row := SceneRules.row(str(id))
		# A fight's moment (`resume: false`, decision 45) is not taken up again: its trigger plays it whole when it comes.
		if str(row.get("room", "")) == here and not row.get("resume", true): continue
		if str(row.get("room", "")) == here: return row
		Game.submit({"type": "scene_end", "scene": str(id), "skipped": true})
		return {}
	for id in queue.duplicate():
		var row := SceneRules.row(str(id))
		if _can_play(c, row, here): return row
		if row.is_empty() or _seen(c, row) or _tried.has(str(id)): queue.erase(id)
	for row in ContentDB.all("scenes"):
		if not row.has("trigger") and _can_play(c, row, here): return row
	return {}

func _seen(c, row: Dictionary) -> bool:
	return c.quests.scenes.get(str(row.get("id", "")), {}).get("done", false) and not row.get("repeat", false)

func _can_play(c, row: Dictionary, here: String) -> bool:
	if row.is_empty() or str(row.get("room", "")) != here or _seen(c, row) or _tried.has(str(row.id)): return false
	if not RequirementRules.passes(row.get("requires", {}), Game.ctx(c)): return false
	# A scene that holds the fight itself (`hold_fight`, decision 45: the first boss's waking and its rescue) is a cut in
	# the fight's middle: the simulation held still, the foes with it.
	return row.get("live", false) or row.get("hold_fight", false) or not _in_fight()

## No page over the world and no moment on the screen.
func _stage_free() -> bool:
	if _pages_open(): return false
	return not (is_instance_valid(moments) and moments.screen_busy())

func _pages_open() -> bool:
	if pages_override != null: return bool(pages_override)
	return is_instance_valid(hud) and hud.blocked

func _in_fight() -> bool:
	if fight_override != null: return bool(fight_override)
	return MomentView.in_fight(float(ContentDB.config("moments").get("settings", {}).get("fight_radius", 400)))

# ------------------------------------------------------------------ a scene
## The scene begins (the Quest authority says so), its people bound to their views, and, if it was cut short before,
## the script run on without a sound to its last checkpoint.
func _start(row: Dictionary) -> void:
	var id := str(row.id)
	var r := Game.submit({"type": "scene_begin", "scene": id})
	queue.erase(id)
	if not r.get("ok", false):
		_tried[id] = true
		return
	run = {"row": row, "id": id, "actor": Game.active_id, "i": 0, "t": 0.0, "begun": false, "mode": "live" if row.get("live", false) else "cut", "actors": {},
		"heard": [], "heard_from": 0, "letterbox": false, "lb": 0.0, "fade": 0.0, "fade_from": 0.0, "fade_to": 0.0, "fade_s": 0.0, "fade_t": 9.0,
		"title": {}, "flash": {}, "weather": "", "prompt": {}, "tapped": false, "page": false,
		"cam": {}, "zoom": 1.0, "zoom_from": 1.0, "zoom_to": 1.0, "zoom_s": 0.0, "zoom_t": 9.0, "view": _view_center(), "nodes": []}
	# A cut straight after a cut keeps the bars where the last one left them (no slide out and in between the two).
	if _lb_carry_t > 0.0: run.lb = _lb_carry
	_lb_carry_t = -1.0
	var grid: TopdownRoom = Game.room_rt.topdown
	for name in row.get("actors", {}):
		var h := SceneRules.home(row, str(name), Game.room_rt.def, grid)
		if h.is_empty(): continue
		run.actors[name] = {"name": str(name), "pos": h.at, "alt": float(h.alt), "home": h.at, "home_alt": float(h.alt), "facing": Vector2.DOWN,
			"pose": "idle", "pose_t": -1.0, "emote": "", "emote_t": 0.0, "say": "", "path": [], "speed": 0.0, "extra": h.extra,
			"npc": str(h.get("npc", "")), "prop": str(h.get("prop", "")), "object": str(h.get("object", "")), "visible": not h.get("hidden", false),
			"moved": false, "label": null, "fig": null, "prop_view": null}
		_bind(run.actors[name])
	run.actors["player"] = {"name": "player", "pos": player_pos(), "alt": 0.0, "home": player_pos(), "home_alt": 0.0, "facing": Vector2.DOWN,
		"pose": "", "pose_t": -1.0, "emote": "", "emote_t": 0.0, "say": "", "path": [], "speed": 0.0, "extra": false, "npc": "",
		"prop": "", "object": "", "visible": true, "moved": false, "label": null, "fig": null, "prop_view": null}
	var at := int(r.get("at", 0))
	if at > 0: _forward(at, false, false)

## Run the script: each step begins, and holds the stage until it is done; instant steps pass in the same frame.
func _play(delta: float) -> void:
	if _pages_open() and (run.page or run.mode == "cut"): return   # a page is up (the portrait strip, or the Bag): it waits
	run.t = float(run.t) + delta
	var steps: Array = run.row.steps
	for guard in 64:
		if run == null: return
		if int(run.i) >= steps.size():
			_finish(false)
			return
		var st: Dictionary = steps[run.i]
		if not run.begun:
			_begin(st)
			if run.has("jump"):
				run.i = int(run.jump)
				run.erase("jump")
				run.begun = false
				continue
		if not _done(st): return
		_end(st)
		run.i = int(run.i) + 1
		run.begun = false

func _begin(st: Dictionary) -> void:
	run.begun = true
	run.t = 0.0
	run.tapped = false
	run.heard_from = (run.heard as Array).size()
	logged.append({"scene": run.id, "i": int(run.i), "do": str(st.do)})
	if logged.size() > 400: logged.pop_front()
	var a: Dictionary = run.actors.get(str(st.get("actor", "")), {})
	var s: Dictionary = Game.account.settings
	match str(st.do):
		"move": _walk(a, st)
		"face": _face(a, st.get("to", "s"))
		"emote":
			a.emote = str(st.emote)
			a.emote_t = float(st.get("s", SceneRules.cfg().get("emote_s", 1.2)))
		"pose":
			a.pose = str(st.pose)
			a.pose_t = float(st.get("s", -1.0))
			_pose_view(a)
		"say":
			if str(st.get("box", "balloon")) == "portrait" and is_instance_valid(hud) and a.get("npc", "") != "":
				run.page = true   # the dialogue page's strip, the speaker's portrait framed at its left
				hud.dialogue_requested.emit({"speaker": ContentDB.name_of("npcs", str(a.npc)), "npc": str(a.npc), "lines": [str(st.text)],
					"portrait": ContentDB.entry("npcs", str(a.npc)).get("outfit", {})})
			else:
				a.say = str(st.text)
				a.say_t = 0.0
		"camera": _aim(st.get("to", "player"), 0.0 if reduce_motion() else float(st.get("s", 1.0)))
		"zoom":
			run.zoom_from = float(run.zoom)
			run.zoom_to = float(st.get("z", 1.0))
			run.zoom_s = 0.0 if reduce_motion() else float(st.get("s", 0.8))
			run.zoom_t = 0.0
		"shake": if world and not reduce_motion() and s.get("screen_shake", true): world.add_shake(float(st.get("s", 0.2)), float(st.get("amp", -1.0)))
		"letterbox": run.letterbox = bool(st.get("on", true))
		"fade":
			run.fade_from = float(run.fade)
			run.fade_to = 1.0 if str(st.get("to", "black")) == "black" else 0.0
			run.fade_s = maxf(0.001, float(st.get("s", 1.0)))
			run.fade_t = 0.0
		"flash":
			if MomentView.claim_flash(1.0): run.flash = {"t": 0.0, "s": float(st.get("s", 0.3)), "color": MomentRules.color(st.color) if st.has("color") else UiKit.PALE_GOLD}
		"title": run.title = {"title": str(st.title), "sub": str(st.get("sub", "")), "t": 0.0, "s": float(st.get("s", 2.6))}
		"spawn":
			if st.has("at"):
				a.pos = _spot(st.at, a)
				a.alt = _floor(a)
			a.visible = true
			_bind(a)
		"despawn":
			a.visible = false
			_unbind(a)
		# Decision 45: a story art's own effect (the FX pipeline's story sheets: the elders' arts, the river boiling) where
		# a target stands; a foe of the room staged (its figure's pose, a struck flash); a hit-stop on the stage's clock.
		"art": if world is TopdownWorld: world.tfx.story(str(st.art), _ground_of(st.get("at", "player")), float(st.get("scale", 1.0)))
		"foe": _stage_foes({str(st.get("foe", "")): {"pose": str(st.get("pose", "")), "flash": bool(st.get("flash", false))}})
		"hitstop": hitstop_t = 0.0 if reduce_motion() else float(st.get("s", 0.1))
		"door": _door(str(st.portal))
		"weather": run.weather = "" if str(st.kind) == "clear" else str(st.kind)
		"moment": if is_instance_valid(moments): moments.play_row(str(st.row))
		"fx":
			var at := where(st.get("at", "player"))
			if world and at != Vector2.INF:
				var fp := {"color": MomentRules.color(st.color) if st.has("color") else UiKit.PAPER, "dur": float(st.get("dur", 0.5))}
				for k in ["radius", "count", "size", "height"]:
					if st.has(k): fp[k] = st[k]
				if fp.has("count"): fp.count = MomentRules.particle_count(int(fp.count))
				world.fx_layer().add(str(st.fx), at, fp)
		"sound": if world: Audio.play(str(st.sfx))
		"branch": run.jump = int(SceneRules.labels(run.row).get(str(st.then if RequirementRules.passes(st.get("if", {}), Game.ctx()) else st.get("else", "")), run.i))
		"goto": run.jump = int(SceneRules.labels(run.row).get(str(st.label), run.i))
		"mark": Game.submit({"type": "scene_mark", "scene": run.id, "step": int(run.i)})
		"handoff":
			Game.submit({"type": "scene_mark", "scene": run.id, "step": int(run.i)})
			run.mode = "hand"
			run.cam = {}
			run.prompt = {"text": str(st.prompt), "at": st.get("at", "player"), "t": 0.0}

## Is the step done: a walk arrived, a line read or tapped on, a wait out, an event heard, a hand-off's deed done.
func _done(st: Dictionary) -> bool:
	var t := float(run.t)
	var a: Dictionary = run.actors.get(str(st.get("actor", "")), {})
	var waits: bool = st.get("wait", true)
	match str(st.do):
		"move": return not waits or (a.path as Array).is_empty()
		"say":
			if run.page: return not _pages_open() and t > 0.1
			return (run.tapped and t > 0.25) or t >= SceneRules.read_s(str(st.text))
		"wait": return t >= float(st.get("s", 1.0))
		"camera", "zoom": return not waits or t >= (0.0 if reduce_motion() else float(st.get("s", 1.0)))
		"emote", "pose": return not st.get("wait", false) or t >= float(st.get("s", 1.0))
		"fade", "title": return t >= float(st.get("s", 2.6 if str(st.do) == "title" else 1.0))
		"moment":
			if is_instance_valid(moments): return t > 0.2 and not moments.screen_busy()
			return t >= SceneRules.step_s(st)
		"wait_input": return run.tapped or (headless and t >= float(SceneRules.cfg().get("tap_s", 1.0)))
		"wait_event": return _heard(st.get("until", [])) or (float(st.get("s", 0.0)) > 0.0 and t >= float(st.s))
		"handoff":
			if st.has("done_if") and RequirementRules.passes(st.done_if, Game.ctx()): return true
			return _heard(st.get("until", [])) or (float(st.get("s", 0.0)) > 0.0 and t >= float(st.s))
	return true

func _end(st: Dictionary) -> void:
	match str(st.do):
		"say":
			run.actors.get(str(st.get("actor", "")), {}).erase("say")
			run.page = false
		"title": run.title = {}
		"handoff":
			run.prompt = {}
			run.mode = "live" if str(st.get("then", "cut")) == "live" or run.row.get("live", false) else "cut"
			run.view = _view_center()

func _heard(until: Array) -> bool:
	var heard: Array = run.heard
	for k in range(int(run.heard_from), heard.size()):
		for u in until:
			if str(heard[k][0]) == str(u.get("event", "")) and matches(u.get("when", {}), heard[k][1]): return true
	return false

## A tap in a cut: the line on the stage moves on.
func tap() -> void:
	if run != null: run.tapped = true

## Skip what is left of the cut: the script runs on at once to its next hand-off (or its end), everything it would
## have asked the authorities for asked, the people where it would have left them.
func skip() -> void:
	if run == null or run.mode != "cut": return
	_forward(-1, true, true)
	if run != null and int(run.i) >= (run.row.steps as Array).size(): _finish(true)
	elif run != null: _play(0.0)   # the hand-off begins at once

## The script run on without a stage: to step `to` (-1: to the next hand-off, or the end), each step's lasting effect
## applied (where the people stand and face, who is on, the letterbox, the camera, the weather, the fade) and, with
## `ask`, every checkpoint asked of the Quest authority.
func _forward(to: int, stop_at_hand: bool, ask: bool) -> void:
	var steps: Array = run.row.steps
	run.title = {}
	run.prompt = {}
	for a in run.actors.values():
		a.erase("say")
		a.emote = ""
	for guard in 256:
		var i := int(run.i)
		if i >= steps.size() or (to >= 0 and i >= to): break
		var st: Dictionary = steps[i]
		var a: Dictionary = run.actors.get(str(st.get("actor", "")), {})
		match str(st.do):
			"handoff":
				if stop_at_hand: break
				if ask: Game.submit({"type": "scene_mark", "scene": run.id, "step": i})
				run.mode = "live" if str(st.get("then", "cut")) == "live" else "cut"
			"mark": if ask: Game.submit({"type": "scene_mark", "scene": run.id, "step": i})
			"move":
				if a.name != "player" and not (st.get("to", []) as Array).is_empty():
					a.pos = _spot(st.to.back(), a)
					a.alt = _floor(a)
					a.path = []
					a.moved = true
					_sync_view(a)
			"face": _face(a, st.get("to", "s"))
			"pose":
				if not st.has("s"):
					a.pose = str(st.pose)
					_pose_view(a)
			"spawn":
				if st.has("at"):
					a.pos = _spot(st.at, a)
					a.alt = _floor(a)
				a.visible = true
				_bind(a)
			"despawn":
				a.visible = false
				_unbind(a)
			"letterbox": run.letterbox = bool(st.get("on", true))
			"camera": _aim(st.get("to", "player"), 0.0)
			"zoom": run.zoom = float(st.get("z", 1.0))
			"weather": run.weather = "" if str(st.kind) == "clear" else str(st.kind)
			"fade":
				run.fade = 1.0 if str(st.get("to", "black")) == "black" else 0.0
				run.fade_t = 9.0
			"branch", "goto":
				var lb := str(st.label) if str(st.do) == "goto" else str(st.then if RequirementRules.passes(st.get("if", {}), Game.ctx()) else st.get("else", ""))
				run.i = int(SceneRules.labels(run.row).get(lb, i)) + 1
				continue
		run.i = i + 1
	run.begun = false
	run.t = 0.0
	run.zoom_t = 9.0
	run.zoom_to = run.zoom
	if float(run.fade) > 0.0 and int(run.i) < steps.size() and str(steps[run.i].do) == "handoff": run.fade = 0.0   # a hand-off is never dark

## The character left the room in the middle of a scene: the rest of it run on (its checkpoints asked), and it is
## over: played out if it had already handed over the controls, skipped if it was still in a cut.
func _leave() -> void:
	var was_cut: bool = run.mode == "cut"
	_forward(-1, false, true)
	_finish(was_cut, true)

func _finish(skipped: bool, left := false) -> void:
	_lb_carry = float(run.lb) if run.mode == "cut" and run.letterbox else 0.0
	_lb_carry_t = 0.3 if _lb_carry > 0.0 else -1.0
	hitstop_t = 0.0
	_stage_foes({})
	Game.submit({"type": "scene_end", "scene": run.id, "skipped": skipped})
	finished.append({"scene": run.id, "skipped": skipped, "left": left})
	for a in run.actors.values():
		if a.name == "player":
			if world and is_instance_valid(world.player): world.player.stage_pose = ""
			continue
		if a.extra: _unbind(a)
		elif not left and (a.moved or str(a.pose) != "idle"):
			a.path = _route(a, a.home)
			a.erase("say")
			a.emote = ""
			homeward.append(a)
		elif is_instance_valid(a.fig): a.fig.staged = false
	run = null
	_end_mode()

# ------------------------------------------------------------------ the people
## A person of the room bound to their figure and label (the figure staged: the scene says where they face and what
## they do; the label's own barks held while they act), an extra given views of its own, a prop its sprite.
func _bind(a: Dictionary) -> void:
	if headless or not (world is TopdownWorld) or not a.visible: return
	if a.object != "":
		a.label = world.npc_views.get(a.object)
		a.fig = world.figures.get(a.object)
	elif a.npc != "" and a.fig == null:
		var made := TopdownPlaces.person(world.room, {"id": "scene_" + str(a.name), "type": "npc", "npc": a.npc, "at": [a.pos.x, a.pos.y], "alt": a.alt},
			world.sorted, world.overlay, world.player)
		a.label = made[0]
		a.fig = made[1]
		a.label.modulate.a = world.labels_a   # as the room's own names stand now
	elif a.prop != "" and a.prop_view == null:
		var art: Dictionary = world.room.tileset.get("props", {}).get(a.prop, {})
		var fp: Array = art.get("footprint", [1, 1])
		a.prop_view = TopdownWorld.PropView.new(world, {"art": art, "cell": TopdownRoom.cell_of(a.pos), "size": Vector2i(int(fp[0]), int(fp[1])),
			"level": int(a.alt / TopdownRoom.LEVEL) if a.alt >= 0.0 else -1})
		world.sorted.add_child(a.prop_view)
	if is_instance_valid(a.label):
		a.label.bark_time = 0.0
		a.label.bark_timer = 999.0
	if is_instance_valid(a.fig): a.fig.staged = true
	_sync_view(a)
	_pose_view(a)

func _unbind(a: Dictionary) -> void:
	if a.extra:
		for k in ["label", "fig", "prop_view"]:
			if is_instance_valid(a.get(k)): a[k].queue_free()
	elif is_instance_valid(a.get("fig")): a.fig.staged = false   # the room's own again: its rest facing and pose
	a.label = null
	a.fig = null
	a.prop_view = null

## Where the view shows the actor: the figure at its feet, the label over it, facing and pose; the body for the player.
func _sync_view(a: Dictionary) -> void:
	if headless: return
	if a.name == "player":
		if world and is_instance_valid(world.player) and not (a.path as Array).is_empty(): world.player.motor.place(a.pos)
		return
	if is_instance_valid(a.fig):
		a.fig.place(a.pos, a.alt)
		a.fig.art.look(a.facing)
	if is_instance_valid(a.label): a.label.position = Vector2(a.pos.x, a.pos.y - a.alt)
	if is_instance_valid(a.prop_view):
		var art: Dictionary = world.room.tileset.get("props", {}).get(a.prop, {})
		var fp: Array = art.get("footprint", [1, 1])
		var o: Array = art.get("origin", [0, 16])
		var cell: Vector2 = (a.pos as Vector2) / TopdownRoom.TILE - Vector2(float(fp[0]) * 0.5, 0.0)
		a.prop_view.place_at(Vector2(cell.x * TopdownWorld.T, (cell.y + 0.5) * TopdownWorld.T), -1 if a.alt < 0.0 else int(a.alt / TopdownRoom.LEVEL),
			Vector2(float(o[0]), float(o[1])))

func _pose_view(a: Dictionary) -> void:
	if headless: return
	var moving := not (a.path as Array).is_empty()
	if a.name == "player":
		if world and is_instance_valid(world.player): world.player.stage_pose = "walk" if moving else ("" if a.pose == "idle" else str(a.pose))
		return
	if is_instance_valid(a.fig): a.fig.art.play(("run" if float(a.speed) > float(SceneRules.cfg().get("walk", 110.0)) * 1.4 else "walk") if moving else TopdownFigure.resolve(str(a.pose)))

func _face(a: Dictionary, to) -> void:
	if a.is_empty(): return
	var dir := Vector2.DOWN
	if to is Array: dir = SceneRules.point(to) - a.pos
	else:
		match str(to):
			"n": dir = Vector2.UP
			"s": dir = Vector2.DOWN
			"e": dir = Vector2.RIGHT
			"w": dir = Vector2.LEFT
			_: dir = where(str(to)) - a.pos if where(str(to)) != Vector2.INF else Vector2.DOWN
	if dir.length() < 0.01: return
	a.facing = dir.normalized()
	if a.name == "player" and world and is_instance_valid(world.player): world.player.motor.face(a.facing)
	_sync_view(a)

## A walk along the step's waypoints, round what stands in the way (the room's path search); a prop sails straight.
func _walk(a: Dictionary, st: Dictionary) -> void:
	if a.is_empty(): return
	a.speed = SceneRules.pace(st)
	a.moved = true
	var to: Array = st.get("to", [])
	# A waypoint beside where something stands now (decision 45) is taken as its cell as the walk begins.
	var cells: Array = to.map(func(q): return q if q is Array else _cell_at(_spot(q, a)))
	a.path = cells.map(func(q): return SceneRules.point(q)) if a.prop != "" or a.name == "player" else SceneRules.walk_path(Game.room_rt.topdown, a.pos, cells)
	if (a.path as Array).is_empty() and not cells.is_empty(): a.pos = SceneRules.point(cells.back())   # no way on foot: there at once
	_pose_view(a)

func _route(a: Dictionary, goal: Vector2) -> Array:
	var p := SceneRules.walk_path(Game.room_rt.topdown, a.pos, [[goal.x / TopdownRoom.TILE - 0.5, goal.y / TopdownRoom.TILE - 0.5]]) if Game.room_rt and Game.room_rt.topdown else []
	return p if not p.is_empty() else [goal]

func _floor(a: Dictionary) -> float:
	if a.prop != "" or Game.room_rt == null or Game.room_rt.topdown == null: return float(a.alt)
	return Game.room_rt.topdown.floor_at(a.pos)

## The people walk on, their emotes and poses run out; the player's body is placed where the script walks it.
func _actors(delta: float) -> void:
	for a in run.actors.values():
		if a.name == "player" and (a.path as Array).is_empty(): a.pos = player_pos()
		if a.has("say_t"): a.say_t = float(a.say_t) + delta
		if _step_along(a, delta):
			if a.name == "player" and world and is_instance_valid(world.player): world.player.motor.vel = Vector2.ZERO
			_pose_view(a)
		if float(a.emote_t) > 0.0:
			a.emote_t = float(a.emote_t) - delta
			if float(a.emote_t) <= 0.0: a.emote = ""
		if float(a.pose_t) > 0.0:
			a.pose_t = float(a.pose_t) - delta
			if float(a.pose_t) <= 0.0:
				a.pose = "idle"
				_pose_view(a)

## One step of a walk; true the frame it arrives.
func _step_along(a: Dictionary, delta: float) -> bool:
	var path: Array = a.path
	if path.is_empty(): return false
	var left := float(a.speed) * delta
	while left > 0.0 and not path.is_empty():
		var goal: Vector2 = path[0]
		var d: Vector2 = goal - a.pos
		if d.length() > 0.5: a.facing = d.normalized()
		if d.length() <= left:
			a.pos = goal
			left -= d.length()
			path.pop_front()
		else:
			a.pos += d.normalized() * left
			left = 0.0
	a.alt = _floor(a)
	if a.name == "player" and world and is_instance_valid(world.player): world.player.motor.vel = a.facing * float(a.speed)
	_sync_view(a)
	return path.is_empty()

## After a scene the room's people walk back to their places (quicker than a stroll if it is far), then stand as
## they stood.
func _homeward(delta: float) -> void:
	for a in homeward.duplicate():
		if Game.room_rt == null:
			homeward.erase(a)
			continue
		a.speed = maxf(float(SceneRules.cfg().get("walk", 110.0)), a.pos.distance_to(a.home) / float(SceneRules.cfg().get("home_s", 1.6)))
		if (a.path as Array).is_empty() or _step_along(a, delta):
			a.pos = a.home
			a.alt = float(a.home_alt)
			a.pose = "idle"
			_sync_view(a)
			_pose_view(a)
			if is_instance_valid(a.label): a.label.bark_timer = randf_range(6.0, 14.0)
			if is_instance_valid(a.fig): a.fig.staged = false
			homeward.erase(a)

func player_pos() -> Vector2:
	if world and is_instance_valid(world.get("player")) and world.player.get("motor") != null: return world.player.motor.pos
	var st: ActorState = Game.actor_state(Game.active_id)
	return st.plane if st else Vector2.ZERO

# ------------------------------------------------------------------ where things are
## A target's ground point in world units, lifted by its height (the effects layer's units): "player", an actor, a cell,
## "object:<id>", "portal:<id>", "enemy:<def>" (the nearest living one); INF for a HUD control or nothing.
func where(to) -> Vector2:
	if to is Array: return _lift(SceneRules.point(to))
	var s := str(to)
	if s == "player": return _lift(player_pos())
	if run != null and run.actors.has(s):
		var a: Dictionary = run.actors[s]
		return Vector2(a.pos.x, a.pos.y - float(a.alt))
	var what := s.get_slice(":", 1)
	if Game.room_rt == null: return Vector2.INF
	match s.get_slice(":", 0):
		"object":
			var o: Dictionary = Game.room_rt.object_def(what)
			if not o.is_empty(): return Vector2(float(o.at[0]), float(o.at[1]) - float(o.get("alt", 0.0)))
		"portal":
			var p: Dictionary = Game.room_rt.portal_def(what)
			if p.has("at"): return Vector2(float(p.at[0]), float(p.at[1]) - float(p.get("alt", 0.0)))
		"enemy":
			var best: EnemyState = null
			for e in Game.room_rt.living_enemies():
				if e.def_id == what and (best == null or e.plane.distance_to(player_pos()) < best.plane.distance_to(player_pos())): best = e
			if best != null: return Vector2(best.plane.x, best.plane.y - best.altitude)
	return Vector2.INF

## A target's ground point in world units, not lifted (a spot beside it, an art's anchor on the floor): "player", an
## actor, a cell, "object:<id>", "portal:<id>", "enemy:<def>" (the nearest living one); the player's where none is.
func _ground_of(to) -> Vector2:
	if to is Array: return SceneRules.point(to)
	var s := str(to)
	if run != null and run.actors.has(s) and s != "player": return run.actors[s].pos
	if s.begins_with("enemy:") and Game.room_rt != null:
		var best: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.def_id == s.get_slice(":", 1) and (best == null or e.plane.distance_to(player_pos()) < best.plane.distance_to(player_pos())): best = e
		if best != null: return best.plane
	if s.begins_with("object:") and Game.room_rt != null:
		var o: Dictionary = Game.room_rt.object_def(s.get_slice(":", 1))
		if not o.is_empty(): return Vector2(float(o.at[0]), float(o.at[1]))
	if s.begins_with("portal:") and Game.room_rt != null:
		var p: Dictionary = Game.room_rt.portal_def(s.get_slice(":", 1))
		if p.has("at"): return Vector2(float(p.at[0]), float(p.at[1]))
	return player_pos()

## Decision 45: a step's place, a cell [x, y] of the layout, or {"near": a target (SceneRules' kinds), "off": [cells
## right, cells down]} beside wherever that target stands now (the elders come to where the fight is); a person's spot
## is a place a body can stand.
func _spot(at, a: Dictionary) -> Vector2:
	if at is Array: return SceneRules.point(at)
	if not (at is Dictionary): return a.get("pos", player_pos())
	var off: Array = at.get("off", [0, 0])
	var p := _ground_of(at.get("near", "player")) + Vector2(float(off[0]), float(off[1])) * TopdownRoom.TILE
	var grid: TopdownRoom = Game.room_rt.topdown if Game.room_rt else null
	if grid != null and str(a.get("prop", "")) == "": p = grid.nearest_standable(p)
	return p

## The layout cell of a ground point, as a step's waypoint names one.
static func _cell_at(p: Vector2) -> Array:
	return [p.x / TopdownRoom.TILE - 0.5, p.y / TopdownRoom.TILE - 0.5]

## Decision 45: the room's foes a cut stages ({def: {pose, flash}}): the eel's figure held reared or struck while the
## simulation stands still; {} lets every foe's figure be its own again.
func _stage_foes(want: Dictionary) -> void:
	if not (world is TopdownWorld) or Game.room_rt == null: return
	for uid in world.foe_views:
		var v = world.foe_views[uid]
		var e: EnemyState = Game.room_rt.enemies.get(uid)
		if not is_instance_valid(v) or e == null: continue
		if want.is_empty():
			v.staged_act = ""
			continue
		if not want.has(e.def_id): continue
		var w: Dictionary = want[e.def_id]
		if str(w.get("pose", "")) != "": v.staged_act = str(w.pose)
		elif not w.get("flash", false): v.staged_act = ""   # neither: its figure its own again
		if w.get("flash", false): v.staged_white = 0.08

func _lift(p: Vector2) -> Vector2:
	var g: TopdownRoom = Game.room_rt.topdown if Game.room_rt else null
	return Vector2(p.x, p.y - (g.floor_at(p) if g else 0.0))

func _view_center() -> Vector2:
	if world and world.has_method("view_center"): return world.view_center()
	return player_pos()

# ------------------------------------------------------------------ the camera and the screen
## Pan to a target over `s` seconds (0: cut there); a moving target (a person walking, the player) is followed.
func _aim(to, s: float) -> void:
	run.cam = {"to": to, "from": _cam_now(), "t": 0.0, "s": s}

func _cam_now() -> Vector2:
	var c: Dictionary = run.cam
	if c.is_empty(): return run.view
	var goal := where(c.to)
	if goal == Vector2.INF: goal = c.from
	return (c.from as Vector2).lerp(goal, smoothstep(0.0, 1.0, float(c.t) / float(c.s)) if float(c.s) > 0.0 else 1.0)

func _camera(delta: float) -> void:
	if not run.cam.is_empty(): run.cam.t = float(run.cam.t) + delta
	run.zoom_t = float(run.zoom_t) + delta
	if float(run.zoom_t) < float(run.zoom_s): run.zoom = lerpf(float(run.zoom_from), float(run.zoom_to), smoothstep(0.0, 1.0, float(run.zoom_t) / float(run.zoom_s)))
	else: run.zoom = float(run.zoom_to)
	run.fade_t = float(run.fade_t) + delta
	if float(run.fade_t) <= float(run.fade_s): run.fade = lerpf(float(run.fade_from), float(run.fade_to), float(run.fade_t) / float(run.fade_s))
	elif float(run.fade_t) < 9.0: run.fade = float(run.fade_to)
	if not run.title.is_empty(): run.title.t = float(run.title.t) + delta
	if not run.flash.is_empty():
		run.flash.t = float(run.flash.t) + delta
		if float(run.flash.t) > float(run.flash.s): run.flash = {}
	if not run.prompt.is_empty(): run.prompt.t = float(run.prompt.t) + delta
	var k := float(SceneRules.cfg().get("letterbox_s", 0.35))
	run.lb = move_toward(float(run.lb), 1.0 if run.letterbox and run.mode == "cut" else 0.0, delta / maxf(0.01, k))
	if not (world is TopdownWorld): return
	if run.mode == "cut" and not run.cam.is_empty():
		world.stage_cam = _cam_now()
		world.stage_snap = float(run.cam.s) <= 0.0 and float(run.cam.t) <= delta + 0.0001
	else:
		world.stage_cam = null
	world.stage_zoom = float(run.zoom) if run.mode == "cut" else 1.0

## The weather the scene calls: a storm's thunder every few seconds, the flash under the flash limiter.
func _weather(delta: float) -> void:
	if run.weather != "storm" or headless: return
	_thunder_t -= delta
	if _thunder_t <= 0.0:
		_thunder_t = randf_range(3.0, 5.0)
		Audio.play("thunder")
		if Game.account.settings.get("flashes", true) and MomentView.claim_flash(1.0): run.flash = {"t": 0.0, "s": 0.25, "color": UiKit.PAPER}

## A door opening where the scene shows it: a ring and the sound at the way (its state is the World authority's).
func _door(portal: String) -> void:
	var at := where("portal:" + portal)
	if world == null or at == Vector2.INF: return
	for k in 2: world.fx_layer().add("ring", at, {"color": UiKit.BRIGHT_JADE, "radius": 56.0, "dur": 1.2, "delay": k * 0.35})
	world.fx_layer().add("motes", at, {"color": UiKit.PALE_GOLD, "count": MomentRules.particle_count(10), "dur": 1.2})
	Audio.play("portal")

## The mode's hold on the game: a cut pauses the simulation and takes the controls, the HUD faded away; otherwise the
## player has both.
func _apply_mode(delta: float) -> void:
	var cut := in_cut()
	if cut != _paused:
		_paused = cut
		Game.pause(cut)
		if is_instance_valid(hud): hud.set_scene_lock(cut)
		if not cut: hold_t = -1.0
	# The HUD fades away in a cut; the moments (which dim it for their own cards) bring it back after.
	if is_instance_valid(hud) and not headless and (cut or not is_instance_valid(moments)):
		hud.modulate.a = move_toward(hud.modulate.a, 0.0 if cut else 1.0, delta * 4.0)
	# The names, markers and plates over the world give the stage to the balloons in a cut.
	if world is TopdownWorld and not headless and float(world.labels_a) != (0.0 if cut else 1.0): world.fade_labels(0.0 if cut else 1.0, delta)
	if stage and (run != null or _drew): stage.queue_redraw()   # once more after a scene, to clear it
	_drew = run != null

func _end_mode() -> void:
	if _paused:
		_paused = false
		Game.pause(false)
	if is_instance_valid(hud): hud.set_scene_lock(false)
	hold_t = -1.0
	hitstop_t = 0.0
	if world is TopdownWorld:
		world.stage_cam = null
		world.stage_zoom = 1.0
		world.stage_hold = false

# ------------------------------------------------------------------ input (from the HUD, in a cut)
## A press starts the hold toward a skip; let go soon, it is a tap.
func input(event: InputEvent) -> void:
	var down := false
	var up := false
	if event is InputEventScreenTouch or event is InputEventMouseButton or (event is InputEventKey and not event.is_echo()):
		down = event.pressed
		up = not event.pressed
	if down and hold_t < 0.0: hold_t = 0.0
	elif up and hold_t >= 0.0:
		if hold_t < 0.3: tap()
		hold_t = -1.0
