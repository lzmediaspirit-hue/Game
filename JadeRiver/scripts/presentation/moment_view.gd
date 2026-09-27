class_name MomentView
extends Node
## P6 moments (docs/moments_design.md §4): plays the rows of data/moments.json from events. The events of one pass are
## gathered and resolved together at the next frame: each is matched to its rows, and a row takes the events its
## `merge` names into its slots (a breakthrough takes its level and its unlocks), so theirs do not play. World layers
## (FX, text, shake, sound, barks, the loot fountain) run on the row's own clock from the moment it is accepted;
## screen layers take the one screen slot by priority, under the HUD or over it. A row may hold world input for at
## most settings.max_lock_s, never in a fight, and a tap skips it.
##
## Presentation only: it listens to GameEvents.event, reads the active character, the room and the settings, and never
## writes game state (contract_tests checks). Rows run on frame time and stand still while the game is paused. With no
## world and no HUD (the headless suites) every layer is written to `logged` and every toast to `toasts_posted`.

var world: Node = null            # world.gd, or null headless
var hud: Node = null              # hud.gd, or null headless
var rows: Array = []
var by_event: Dictionary = {}     # event -> [row]
var watched: Dictionary = {}      # every event gathered: triggers, merges, holds, and the room and switch events
var cfg: Dictionary = {}          # moments.json settings
var pending: Array = []           # [name, payload] gathered since the last frame
var active: Array = []            # accepted plays whose world layers still run
var queue: Array = []             # plays waiting for the screen slot
var playing = null                # the play on screen
var fading = null                 # a play cut by a higher one, fading out
var lock := 0.0
var logged: Array = []            # {t, row, layer, ...}: every layer as it starts, headless or not (the last 200)
var toasts_posted: Array = []
var fight_override = null         # tests: true or false stands in for the room
var pages_override = null         # tests: true or false stands in for the page stack
var hold_at := -1.0               # --moment=<id>:<t> stops the rows' clock at t
var clock := 0.0
var seen: Dictionary = {}         # enemy uids met since the room was entered (first_in_room)
var heard: Dictionary = {}        # sfx -> clock when last played (the same sound within 0.1 s plays once)
var recent: Dictionary = {}       # row id and payload -> clock (the same row within 0.5 s plays once)
var arrivals := 0
const CONTROL := ["room_entered", "room_left", "character_switched"]

func _ready() -> void:
	cfg = ContentDB.config("moments").get("settings", {})
	load_rows(ContentDB.all("moments"))
	GameEvents.event.connect(_on_event)

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)
	_set_lock(0.0)

## The rows to play: moments.json, or fixture rows in the tests.
func load_rows(list: Array) -> void:
	rows = list
	by_event.clear()
	watched.clear()
	for e in CONTROL: watched[e] = true
	for r in rows:
		if not by_event.has(r.event): by_event[r.event] = []
		by_event[r.event].append(r)
		watched[r.event] = true
		for m in r.get("merge", []): watched[m.event] = true
		for h in r.get("hold_until", []): watched[h] = true
	clear()

func clear() -> void:
	pending.clear()
	active.clear()
	queue.clear()
	playing = null
	fading = null
	recent.clear()
	_set_lock(0.0)

func _on_event(name: String, p: Dictionary) -> void:
	if watched.has(name): pending.append([name, p])

func _process(delta: float) -> void:
	if not Game.paused: advance(delta)

## One frame: the running rows' world layers, then this frame's events, then the screen slot and the lock.
func advance(delta: float) -> void:
	if hold_at >= 0.0 and playing != null and float(playing.st) >= hold_at: delta = 0.0
	clock += delta
	for pl in active.duplicate(): _run_world(pl, delta)
	_resolve()
	_run_screen(delta)

## Seconds of input lock left (0 when none).
func lock_left() -> float:
	return lock

## A press while a row holds input: a row that skips jumps to its skip point and gives input back. True if consumed.
func press() -> bool:
	if lock <= 0.0: return false
	if playing != null and str(playing.row.get("skip", "")) == "tap":
		var to := float(playing.row.get("skip_to_s", 0.0))
		playing.st = maxf(float(playing.st), to)
		for i in (playing.row.layers as Array).size():
			if float(playing.row.layers[i].t) <= to: playing.fired[i] = maxi(1, int(playing.fired.get(i, 0)))
		playing.wt = maxf(float(playing.wt), to)
		_set_lock(0.0)
	return true

## Plays a row with its sample payload (the --moment preview) and, from `at` on, holds it there.
func preview(id: String, at := -1.0) -> void:
	for r in rows:
		if str(r.id) == id:
			var p: Dictionary = (r.sample as Dictionary).duplicate(true)
			if p.has("actor"): p.actor = Game.active_id
			if p.has("target"): p.target = Game.active_id
			hold_at = at
			pending.append([str(r.event), p])

# ------------------------------------------------------------------ gather, match, merge
func _ctx() -> Dictionary:
	return {"active": Game.active_id, "seen": seen}

func _resolve() -> void:
	if pending.is_empty(): return
	var evs := pending
	pending = []
	var ctx := _ctx()
	for e in evs:
		var mine := str(e[1].get("actor", "")) == Game.active_id
		match str(e[0]):
			"room_entered": if mine: seen.clear()
			"room_left": if mine: _end_scope("room")
			"character_switched":
				clear()
				return
		for pl in active:
			if pl.held and str(e[0]) in pl.row.get("hold_until", []): pl.held = false
	var plays: Array = []
	for i in evs.size():
		for r in by_event.get(evs[i][0], []):
			if MomentRules.matches(r.get("when", {}), evs[i][1], ctx): plays.append({"row": r, "p": evs[i][1], "i": i, "slots": {}})
	var gone := {}
	for pl in plays:
		if gone.has(pl.i): continue
		for m in pl.row.get("merge", []):
			for j in evs.size():
				if j == pl.i or gone.has(j) or evs[j][0] != m.event or not MomentRules.matches(m.get("when", {}), evs[j][1], ctx): continue
				var into := str(m.get("into", ""))
				if m.has("max"):
					if (pl.slots.get(into, []) as Array).size() >= int(m.max): continue
					pl.slots[into] = pl.slots.get(into, []) + [evs[j][1]]
				elif into != "": pl.slots[into] = evs[j][1]
				gone[j] = true
	for pl in plays:
		if not gone.has(pl.i): _accept(pl)

func _accept(pl: Dictionary) -> void:
	var row: Dictionary = pl.row
	var key := str(row.id) + str(pl.p)
	if clock - float(recent.get(key, -9.0)) < 0.5: return
	recent[key] = clock
	if recent.size() > 64: recent.clear()
	if row.get("when", {}).has("first_in_room"): seen[int(pl.p.get("enemy", 0))] = true
	arrivals += 1
	pl.merge({"wt": 0.0, "st": -1.0, "wait": 0.0, "n": arrivals, "fired": {}, "held": not row.get("hold_until", []).is_empty(), "fade": 0.0})
	active.append(pl)
	_run_world(pl, 0.0)
	if int(row.priority) <= 0: return
	if str(row.get("in_fight", "play")) == "toast" and _in_fight():
		_post_toast(pl)
		return
	if int(row.priority) >= 90 and playing != null and int(playing.row.priority) < int(row.priority): _cut()
	queue.append(pl)
	if queue.size() > int(cfg.get("queue_max", 4)):
		var low = queue[0]
		for q in queue:
			if int(q.row.priority) < int(low.row.priority) or (int(q.row.priority) == int(low.row.priority) and int(q.n) > int(low.n)): low = q
		queue.erase(low)
		_post_toast(low)

func _cut() -> void:
	fading = playing
	fading.fade = float(cfg.get("cut_fade_s", 0.15))
	_post_toast(playing)
	playing = null
	_set_lock(0.0)

## A row whose screen part cannot play (cut, stale, the queue full, in a fight) leaves its line as a toast, if it has one.
func _post_toast(pl: Dictionary) -> void:
	var src: Dictionary = pl.row.get("toast", {})
	var s := MomentRules.text(src, pl.p, pl.slots)
	if s == "": return
	toasts_posted.append(s)
	if hud: hud.toast(s, str(src.get("kind", "gold")))

func _end_scope(scope: String) -> void:
	for pl in active.duplicate():
		if str(pl.row.get("scope", "actor")) != scope: continue
		active.erase(pl)
		queue.erase(pl)
		if playing == pl:
			playing = null
			_set_lock(0.0)

# ------------------------------------------------------------------ the world clock
func _run_world(pl: Dictionary, delta: float) -> void:
	pl.wt = float(pl.wt) + delta
	var layers: Array = pl.row.layers
	var left := false
	for i in layers.size():
		var L: Dictionary = layers[i]
		if not MomentRules.LAYER_KINDS.get(str(L.kind), "") in ["world", "hud"]: continue
		var n := int(pl.fired.get(i, 0))
		if n > 0 and not (pl.held and L.has("repeat_s")): continue
		if float(L.t) + float(L.get("repeat_s", 0.0)) * n > float(pl.wt):
			left = left or n == 0
			continue
		pl.fired[i] = n + 1
		_fire(pl, L)
	if pl.held and float(pl.wt) >= float(pl.row.get("max_s", 0.0)): pl.held = false
	if not left and not pl.held and float(pl.wt) >= float(pl.row.duration_s) and playing != pl and not queue.has(pl): active.erase(pl)

## A world or HUD layer, as it starts: into the world, or into the log when there is none.
func _fire(pl: Dictionary, L: Dictionary) -> void:
	var s: Dictionary = Game.account.settings
	var kind := str(L.kind)
	var p: Dictionary = pl.p
	var e := {"t": snappedf(float(pl.wt), 0.001), "row": str(pl.row.id), "layer": kind}
	var at := _anchors(L, p) if kind in ["fx", "text", "camera"] else []
	match kind:
		"sound":
			var id := str(L.sfx)
			if (L.has("if_slot") and (pl.slots.get(str(L.if_slot), []) as Array).is_empty()) or clock - float(heard.get(id, -9.0)) < 0.1: return
			heard[id] = clock
			e.sfx = id
			if world: Audio.play(id, str(L.get("bus", "SFX")))
		"buzz":
			if not s.get("haptics", true): return
			e.ms = int(L.ms)
			if world and OS.has_feature("mobile"): Input.vibrate_handheld(int(L.ms))
		"shake":
			e.s = float(L.s)
			e.amp = MomentRules.shake_amp(float(L.s), float(L.get("amp", -1.0)))
			if world: world.add_shake(e.s, e.amp)
		"camera":
			if s.get("reduce_motion", false): return
			e.to = str(L.get("to", "enemy"))
			if not at.is_empty(): world.hold_camera(at[0], float(L.get("in_s", 0.6)), float(L.get("hold_s", 0.9)), float(L.get("out_s", 0.4)))
		"caption":
			if not s.get("captions", false): return
			e.text = MomentRules.text(L.text, p, pl.slots)
			if hud: hud.caption = {"text": e.text, "t": 0.0}
		"toast":
			e.text = MomentRules.text(L.text, p, pl.slots)
			toasts_posted.append(e.text)
			if hud: hud.toast(e.text, str(L.get("toast_kind", "gold")))
		"fx":
			var fp := fx_params(L, p, pl.slots)
			e.merge(fp)
			for pos in at: world.fx.add(str(L.fx), pos, fp)
		"text":
			e.text = MomentRules.text(L.text, p, pl.slots)
			for pos in at:
				world.fx.add("text", pos, {"text": e.text, "color": MomentRules.color(L.color, p, pl.slots), "size": int(L.size), "dur": float(L.get("dur", 2.0))})
		"bark":
			if world: _bark(str(L.key), float(L.radius), float(L.dur))
	e.skipped = world == null or (kind in ["fx", "text", "camera"] and at.is_empty())
	logged.append(e)
	if logged.size() > 200: logged.pop_front()

## An fx layer's parameters for FxLayer.add, with the settings applied (Reduce motion and Battery saver thin the
## particles to their tier-1 and tier-2 counts).
func fx_params(L: Dictionary, p: Dictionary, slots := {}) -> Dictionary:
	var out := {"fx": str(L.fx), "color": MomentRules.color(L.get("color", ""), p, slots)}
	for k in ["radius", "dur", "count", "size", "height", "style", "facing"]:
		if L.has(k): out[k] = MomentRules.value(L[k], p, slots)
	if out.has("count"): out.count = MomentRules.particle_count(int(out.count))
	return out

## Where a world layer plays: its anchor's view (none headless, or when the view is gone), plus its offset.
func _anchors(L: Dictionary, p: Dictionary) -> Array:
	if world == null: return []
	var out: Array = []
	match str(L.get("at", L.get("to", "actor"))):
		"actor": if is_instance_valid(world.player): out.append(world.player.position)
		"camera": out.append(world.camera.position)
		"drop": out.append(Vector2(float(p.get("x", 0.0)), float(p.get("y", 0.0))))
		"enemy":
			var v = world.enemy_views.get(int(p.get("enemy", 0)))
			if is_instance_valid(v): out.append(v.position)
		"pet":
			for uid in world.enemy_views:
				var e = Game.room_rt.enemies.get(uid) if Game.room_rt else null
				if e and e.team == "ally" and e.pet_owner == Game.active_id and str(e.ai.get("pet", "")) == str(p.get("pet", "")) and is_instance_valid(world.enemy_views[uid]):
					out.append(world.enemy_views[uid].position)
	var off: Array = L.get("offset", [0, 0])
	return out.map(func(v): return v + Vector2(float(off[0]), float(off[1])))

## The people nearby say something (three lines by `prefix`_0.._2).
func _bark(prefix: String, radius: float, dur: float) -> void:
	var n := 0
	for id in world.npc_views:
		var nv = world.npc_views[id]
		if nv.visible and nv.position.distance_to(world.player.position) < radius:
			nv.bark = Tx.t("%s_%d" % [prefix, n % 3])
			nv.bark_time = dur
			n += 1

# ------------------------------------------------------------------ the screen slot
func _run_screen(delta: float) -> void:
	if fading != null:
		fading.fade = float(fading.fade) - delta
		if float(fading.fade) <= 0.0: fading = null
	if playing != null:
		playing.st = float(playing.st) + delta
		_log_screen(playing, float(playing.st) - delta)
		if float(playing.st) >= float(playing.row.duration_s): playing = null
	for q in queue.duplicate():
		q.wait = float(q.wait) + delta
		if float(q.wait) > float(q.row.get("stale_s", cfg.get("stale_s", 6.0))):
			queue.erase(q)
			_post_toast(q)
	if playing == null and not queue.is_empty() and not _pages_open():
		var best = queue[0]
		for q in queue:
			if int(q.row.priority) > int(best.row.priority): best = q
		queue.erase(best)
		playing = best
		playing.st = 0.0
		_log_screen(playing, -1.0)
		if float(best.row.get("lock_s", 0.0)) > 0.0 and not _in_fight(): _set_lock(minf(float(best.row.lock_s), float(cfg.get("max_lock_s", 1.5))))
	if lock > 0.0: _set_lock(0.0 if _in_fight() else maxf(0.0, lock - delta))

## Screen layers whose time came between `from` and now, into the log.
func _log_screen(pl: Dictionary, from: float) -> void:
	var s: Dictionary = Game.account.settings
	for L in pl.row.layers:
		var where := str(MomentRules.LAYER_KINDS.get(str(L.kind), ""))
		if not where in ["under", "over"] or float(L.t) <= from or float(L.t) > float(pl.st): continue
		var e := {"t": snappedf(float(pl.st), 0.001), "row": str(pl.row.id), "layer": str(L.kind), "motion": not s.get("reduce_motion", false)}
		if L.has("alpha"): e.alpha = float(L.alpha) * (1.0 if s.get("flashes", true) or str(L.kind) == "dim" else 0.3)
		logged.append(e)

func _set_lock(v: float) -> void:
	var was := lock > 0.0
	lock = v
	if hud and was != (lock > 0.0): hud.set_moment_lock(lock > 0.0)

func _pages_open() -> bool:
	if pages_override != null: return bool(pages_override)
	return hud != null and hud.blocked

## In a fight (§4.4): a living foe within fight_radius is after you, a boss is alive in the room, or a tribulation runs.
func _in_fight() -> bool:
	if fight_override != null: return bool(fight_override)
	var c = Game.active()
	if c == null or Game.room_rt == null: return false
	if Game.progression.is_under_tribulation(c.id): return true
	var st: ActorState = Game.actor_state(c.id)
	for e in Game.room_rt.living_enemies():
		if e.team != "enemy" or e.def.get("passive", false): continue
		if e.is_boss(): return true
		if st and str(e.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"] and e.plane.distance_to(st.plane) < float(cfg.get("fight_radius", 400)): return true
	return false
