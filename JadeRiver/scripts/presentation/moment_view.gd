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
var hold_at := -1.0               # --moment=<id>:<t>, --hold=<t>[:<row>]: the rows' clock stops at t (for one row, if named)
var hold_row := ""
var clock := 0.0
var seen: Dictionary = {}         # enemy uids met since the room was entered (first_in_room)
var heard: Dictionary = {}        # sfx -> clock when last played (the same sound within 0.1 s plays once)
var recent: Dictionary = {}       # row id and payload -> clock (the same row within 0.5 s plays once)
var arrivals := 0
var before: Dictionary = {}       # the stats a stat rise compares with (§2.3): taken at a breakthrough's start, refreshed when idle
var snap_t := 0.0
var last_seen: Dictionary = {}    # event -> its last payload ("slot.last.<event>.<key>")
var canvases: Array = []          # the drawers under and over the HUD (none headless)
var drew := false
static var _flash_ms := -100000   # the flash limiter (§5.10): one screen flash or tint a second, from every source
const DIM_RINGS := [[0.0, 0.3], [160.0, 0.5], [420.0, 1.2], [800.0, 1.9], [2600.0, 1.9]]   # radius, share of the dim: clear round the actor, deep far off (mockup 05)
static var _pill: StyleBoxFlat
const CONTROL := ["room_entered", "room_left", "character_switched"]

func _ready() -> void:
	cfg = ContentDB.config("moments").get("settings", {})
	load_rows(ContentDB.all("moments"))
	GameEvents.event.connect(_on_event)
	if world == null: return
	for n in [4, 8]:   # under the HUD (5), and over it but under the shell (15) and the pages (20)
		var cl := CanvasLayer.new()
		cl.layer = n
		add_child(cl)
		var d := Node2D.new()
		d.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		d.draw.connect(_draw_screen.bind(d, "under" if n == 4 else "over"))
		cl.add_child(d)
		canvases.append(d)

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
	if hold_at >= 0.0 and playing != null and float(playing.st) >= hold_at and hold_row in ["", str(playing.row.id)]: delta = 0.0
	clock += delta
	for pl in active.duplicate(): _run_world(pl, delta)
	_resolve()
	_run_screen(delta)
	snap_t += delta
	if snap_t >= float(cfg.get("snapshot_s", 1.0)) and playing == null and queue.is_empty():
		snap_t = 0.0
		before = stats_now()
	var busy := playing != null or fading != null or active.any(func(pl): return pl.held and float(pl.st) >= 0.0)
	if busy or drew:
		for d in canvases: d.queue_redraw()
	drew = busy

## True while a row holds the screen (the HUD holds its toasts back meanwhile).
func screen_busy() -> bool:
	return playing != null

## The active character's numbers a stat rise shows (moments.json `stats`), and the share of HP kept.
func stats_now() -> Dictionary:
	var c = Game.active()
	if c == null: return {}
	var out := {"hp_pct": int(round(100.0 * c.pools.hp / maxf(1.0, c.pools.max_hp)))}
	for id in ContentDB.config("moments").get("stats", []):
		match str(id):
			"level": out[id] = ProgressionRules.level(c)
			"lifespan": out[id] = ProgressionRules.lifespan_of(c)
			"max_hp", "max_qi", "max_soul": out[id] = float(c.pools.get(str(id)))
			_: out[id] = c.stats.value(str(id))
	return out

## The flash limiter: true, and the gap starts again, when no screen flash or tint played in the last `gap_s`.
static func claim_flash(gap_s: float) -> bool:
	var now := Time.get_ticks_msec()
	if now - _flash_ms < int(gap_s * 1000.0): return false
	_flash_ms = now
	return true

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
		last_seen[str(e[0])] = e[1]
		match str(e[0]):
			"breakthrough_started": if mine: before = stats_now()
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
				if hud: hud.drop_toasts_from(evs[j][1])   # what the row says for it, the HUD need not say again
	for pl in plays:
		if not gone.has(pl.i): _accept(pl)

func _accept(pl: Dictionary) -> void:
	var row: Dictionary = pl.row
	for v in row.get("variants", []):   # a row's variant for some payloads (a Dao's sixth tier writes the large band)
		if MomentRules.matches(v.get("when", {}), pl.p, _ctx()):
			row = row.duplicate()
			row.merge(v, true)
			pl.row = row
			break
	if int(row.priority) > 0: pl.slots.merge({"now": stats_now(), "before": before.duplicate(), "last": last_seen.duplicate()})
	var key := str(row.id) + str(pl.p)
	if clock - float(recent.get(key, -9.0)) < 0.5: return
	recent[key] = clock
	if recent.size() > 64: recent.clear()
	if row.get("when", {}).has("first_in_room"): seen[int(pl.p.get("enemy", 0))] = true
	arrivals += 1
	pl.merge({"wt": 0.0, "st": -1.0, "sw": 0.0, "wait": 0.0, "n": arrivals, "fired": {}, "muted": {}, "held": not row.get("hold_until", []).is_empty(), "fade": 0.0})
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
		"fountain":
			var f: Dictionary = MomentRules.cfg().get("fountain", {}).get(str(p.get("source", "")), {})
			e.bounce = f.is_empty() or s.get("reduce_motion", false)   # Reduce motion keeps today's bounce
			if world and not e.bounce: _fountain(p, f)
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

## The loot fountain (§5.8): each piece's view leaves the drop point in turn, the rare ones last so they land on top
## (the first of them chimes as it lands); the bigger the drop, the higher and longer the arc, up to its caps.
func _fountain(p: Dictionary, f: Dictionary) -> void:
	var items: Array = p.get("items", [])
	var n := float(items.size())
	var ap: Array = f.apex
	var fl: Array = f.flight
	var apex := minf(float(ap[0]) + float(ap[1]) * n, float(ap[2]))
	var flight := minf(float(fl[0]) + float(fl[1]) * n, float(fl[2]))
	var views := {}
	for v in world.room_layer.get_children():
		if v is LootView: views[v.uid] = v
	var order: Array = items.filter(func(i): return not MomentRules.is_rare(i)) + items.filter(func(i): return MomentRules.is_rare(i))
	var drop := Vector2(float(p.get("x", 0.0)), float(p.get("y", 0.0)))
	var chimed := false
	for i in order.size():
		var rare := MomentRules.is_rare(order[i])
		if views.has(int(order[i].uid)): views[int(order[i].uid)].launch(drop, i * float(f.gap), apex, flight, "rare_chime" if rare and not chimed else "")
		chimed = chimed or rare
	if f.has("flash"): world.fx.add("flash", drop + Vector2(0, -30), {"color": MomentRules.color(f.flash), "radius": 90.0, "dur": 0.3})

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
		var was := float(playing.st)
		playing.st = was + delta
		_log_screen(playing, was)
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
		playing.sw = playing.wt
		_log_screen(playing, -1.0)
		if float(best.row.get("lock_s", 0.0)) > 0.0 and not _in_fight(): _set_lock(minf(float(best.row.lock_s), float(cfg.get("max_lock_s", 1.5))))
	if lock > 0.0: _set_lock(0.0 if _in_fight() else maxf(0.0, lock - delta))
	# While the world is dimmed for a moment the HUD recedes with it, so the band and the stats read clear (mockup 05).
	if hud:
		var dim := _layer(playing, "dim") if playing != null else {}
		var down := not dim.is_empty() and float(playing.st) < float(dim.get("until", playing.row.duration_s))
		hud.modulate.a = move_toward(hud.modulate.a, 0.3 if down else 1.0, delta * 3.0)

## Screen layers whose time came between `from` and now: into the log, and a flash past the flash limiter is muted.
func _log_screen(pl: Dictionary, from: float) -> void:
	var s: Dictionary = Game.account.settings
	var layers: Array = pl.row.layers
	for i in layers.size():
		var L: Dictionary = layers[i]
		if not MomentRules.LAYER_KINDS.get(str(L.kind), "") in ["under", "over"] or float(L.t) <= from or float(L.t) > float(pl.st): continue
		var e := {"t": snappedf(float(pl.st), 0.001), "row": str(pl.row.id), "layer": str(L.kind), "motion": not s.get("reduce_motion", false)}
		if L.has("alpha"): e.alpha = _alpha(L)
		if str(L.kind) == "flash" and not claim_flash(float(cfg.get("flash_gap_s", 1.0))):
			pl.muted[i] = true
			e.muted = true
		logged.append(e)

## A screen tint's alpha under the settings: Bright flashes off leaves 0.3 of a flash's or a vignette's (the dim stays).
func _alpha(L: Dictionary) -> float:
	return float(L.get("alpha", 1.0)) * (1.0 if Game.account.settings.get("flashes", true) or str(L.kind) == "dim" else 0.3)

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

# ------------------------------------------------------------------ the screen layers (§3.3), drawn from each play's time
func _draw_screen(ci: Node2D, canvas: String) -> void:
	var still: bool = Game.account.settings.get("reduce_motion", false)
	var plays: Array = active.filter(func(q): return q.held and float(q.st) >= 0.0 and q != playing and q != fading)
	if fading != null: plays.append(fading)
	if playing != null: plays.append(playing)
	for pl in plays:
		var own: bool = pl == playing or pl == fading
		var a := clampf(float(pl.fade) / float(cfg.get("cut_fade_s", 0.15)), 0.0, 1.0) if pl == fading else 1.0
		var out := clampf((float(pl.row.duration_s) - float(pl.st)) / 0.4, 0.0, 1.0)
		var layers: Array = pl.row.layers
		for i in layers.size():
			var L: Dictionary = layers[i]
			var held: bool = L.get("held", false) and pl.held
			if MomentRules.LAYER_KINDS.get(str(L.kind), "") != canvas or pl.muted.has(i) or not (own or held): continue
			var lt := (float(pl.wt) - float(pl.sw) if held else float(pl.st)) - float(L.t)
			var la := a * (1.0 if held else out) * (clampf((float(L.until) + 0.3 - float(pl.st)) / 0.3, 0.0, 1.0) if L.has("until") else 1.0)
			if lt >= 0.0 and la > 0.0: call("_draw_" + str(L.kind), ci, pl, L, lt, la, still)

func _t(pl: Dictionary, src) -> String:
	return MomentRules.text(src, pl.p, pl.slots)

func _col(pl: Dictionary, spec, fallback: Color) -> Color:
	return MomentRules.color(spec, pl.p, pl.slots) if spec != null else fallback

func _layer(pl: Dictionary, kind: String) -> Dictionary:
	for L in pl.row.layers:
		if str(L.kind) == kind: return L
	return {}

static func _in(lt: float, from: float, over: float) -> float:
	return clampf((lt - from) / maxf(0.001, over), 0.0, 1.0)

## Sizes are screen px (§2.2): Cormorant is drawn at 1.2x its layout size, so a display size is scaled back first.
static func _px(px: float, display: bool) -> int:
	return int(round(px / (UiKit.WORD_SCALE if display else 1.0)))

func _write(ci: Node2D, s: String, pos: Vector2, px: float, col: Color, display := false, align := HORIZONTAL_ALIGNMENT_CENTER, width := 1280.0, shadow := true) -> void:
	UiKit.draw_text(ci, s, pos, _px(px, display), col, align, width, shadow, display)

func _width(s: String, px: float, display := false) -> float:
	return UiKit.text_width(s, _px(px, display), display)

## A kit frame at an alpha (the kit's boxes are shared, so the tint is put back after).
func _box(ci: Node2D, asset: String, r: Rect2, a: float) -> void:
	var sb = UiKit.style(asset)
	if not (sb is HdStyleBox):
		ci.draw_style_box(sb, r)
		return
	var was: Color = sb.modulate
	sb.modulate = Color(was, was.a * a)
	ci.draw_style_box(sb, r)
	sb.modulate = was

## The ink band written left to right over `wipe_s` (the brush's tip leads), or faded in with Reduce motion.
func _ink(ci: Node2D, r: Rect2, lt: float, wipe_s: float, a: float, still: bool) -> void:
	var k := _in(lt, 0.0, 0.2 if still else wipe_s)
	if not still: r.size.x = lerpf(minf(r.size.x, r.size.y * 2.0), r.size.x, ease(k, 0.4))
	_box(ci, "ink_band", r, a * (k if still else minf(1.0, k * 4.0)))

func _draw_dim(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, _still: bool) -> void:
	var col := Color(_col(pl, L.get("color"), UiKit.INK), _alpha(L) * a * _in(lt, 0.0, float(L.get("fade_in", 0.3))))
	if not L.get("radial", false) or world == null or not is_instance_valid(world.player):
		ci.draw_rect(Rect2(0, 0, 1280, 720), col)
		return
	# Lighter round the actor and full from 450 px out (mockup 05's night wash): rings of 32 shaded quads.
	var at: Vector2 = world.player.get_global_transform_with_canvas().origin + Vector2(0, -80)
	for j in DIM_RINGS.size() - 1:
		var c0 := Color(col, col.a * DIM_RINGS[j][1])
		var c1 := Color(col, col.a * DIM_RINGS[j + 1][1])
		for i in 32:
			var u0 := Vector2.from_angle(TAU * i / 32.0) * Vector2(1.0, 0.8)
			var u1 := Vector2.from_angle(TAU * (i + 1) / 32.0) * Vector2(1.0, 0.8)
			var r0: float = DIM_RINGS[j][0]
			var r1: float = DIM_RINGS[j + 1][0]
			if r0 == 0.0: ci.draw_polygon(PackedVector2Array([at, at + u0 * r1, at + u1 * r1]), PackedColorArray([c0, c1, c1]))
			else: ci.draw_polygon(PackedVector2Array([at + u0 * r0, at + u0 * r1, at + u1 * r1, at + u1 * r0]), PackedColorArray([c0, c1, c1, c0]))

func _draw_vignette(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, _still: bool) -> void:
	var pulse := 1.0
	if float(L.get("pulse_hz", 0.0)) > 0.0 and Game.account.settings.get("flashes", true): pulse = 0.75 + 0.25 * sin(TAU * float(L.pulse_hz) * lt)
	var col := _col(pl, L.get("color"), UiKit.INK)
	var c0 := Color(col, _alpha(L) * a * pulse * _in(lt, 0.0, 0.4))
	var c1 := Color(col, 0.0)
	var e := float(L.get("edge", 160))
	var quads := {"top": [Vector2(0, 0), Vector2(1280, 0), Vector2(1280, e), Vector2(0, e)],
		"bottom": [Vector2(0, 720), Vector2(1280, 720), Vector2(1280, 720 - e), Vector2(0, 720 - e)],
		"left": [Vector2(0, 0), Vector2(0, 720), Vector2(e, 720), Vector2(e, 0)],
		"right": [Vector2(1280, 0), Vector2(1280, 720), Vector2(1280 - e, 720), Vector2(1280 - e, 0)]}
	for side in L.get("sides", quads.keys()):
		ci.draw_polygon(PackedVector2Array(quads[side]), PackedColorArray([c0, c0, c1, c1]))

func _draw_flash(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, _still: bool) -> void:
	var k := lt / maxf(0.01, float(L.get("dur", 0.25)))
	if k < 1.0: ci.draw_rect(Rect2(0, 0, 1280, 720), Color(_col(pl, L.get("color"), UiKit.PALE_GOLD), _alpha(L) * a * (1.0 - k)))

func _draw_letterbox(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	var h := float(L.get("height", 64))
	var s := float(L.get("slide_s", 0.3))
	var k := minf(_in(lt, 0.0, s), clampf((float(pl.row.duration_s) - float(pl.st)) / s, 0.0, 1.0))
	var off := 0.0 if still else h * (1.0 - k)
	var col := Color(UiKit.INK, a * (k if still else 1.0))
	ci.draw_rect(Rect2(0, -off, 1280, h), col)
	ci.draw_rect(Rect2(0, 720 - h + off, 1280, h), col)

## The band (mockup 05): a letter-spaced line above, the title written on the ink, a line under it; `y` is the title's top.
func _band_rect(pl: Dictionary, L: Dictionary) -> Rect2:
	var px := float(L.get("size", 34))
	var w := clampf(_width(_t(pl, L.get("title", {})), px, true) + 260.0, 520.0, 1180.0)
	return Rect2(640.0 - w * 0.5, float(L.y) - 6.0, w, px * 1.3)

func _draw_band(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	var px := float(L.get("size", 34))
	var y := float(L.y)
	_ink(ci, _band_rect(pl, L), lt, float(L.get("wipe_s", 0.4)), 0.9 * a, still)
	var over := _t(pl, L.get("over", {}))
	if over != "": _spaced(ci, over, y - 13.0, 26.0, Color(UiKit.PALE_GOLD, a * _in(lt, 0.1, 0.2)), 4.0)
	var title := _t(pl, L.get("title", {}))
	var ta := a * _in(lt, 0.2, 0.3)
	if L.has("glow"):
		var g := Color(_col(pl, L.glow, UiKit.GOLD), 0.09 * ta)
		for i in 8: _write(ci, title, Vector2(0, y + px * 0.8) + Vector2(4, 0).rotated(TAU * i / 8.0), px, g, true, HORIZONTAL_ALIGNMENT_CENTER, 1280.0, false)
	_write(ci, title, Vector2(0, y + px * 0.8), px, Color(_col(pl, L.get("color"), UiKit.PALE_GOLD), ta), true)
	var sub := _t(pl, L.get("sub", {}))
	var sy := y + px * 1.35 + 16.0
	if sub != "": _write(ci, sub, Vector2(0, sy), float(L.get("sub_size", 20)), Color(_col(pl, L.get("sub_color"), UiKit.PAPER), a * _in(lt, 0.5, 0.2)))
	for line in _more(pl, L):
		sy += 26.0
		_write(ci, line, Vector2(0, sy), 18.0, Color(_col(pl, L.get("more_color"), UiKit.MIST), a * _in(lt, 0.6, 0.2)))

## A line of capitals letter-spaced by `spacing` px, centred on the screen.
func _spaced(ci: Node2D, s: String, baseline: float, px: float, col: Color, spacing: float) -> void:
	var w := -spacing
	for ch in s: w += _width(ch, px, true) + spacing
	var x := 640.0 - w * 0.5
	for ch in s:
		_write(ci, ch, Vector2(x, baseline), px, col, true, HORIZONTAL_ALIGNMENT_LEFT, -1.0)
		x += _width(ch, px, true) + spacing

## The strip: a slim ink band with a title, a line under it and any `more` lines; `y` is the title's top.
func _strip_rect(pl: Dictionary, L: Dictionary) -> Rect2:
	var px := float(L.get("size", 30))
	var spx := float(L.get("sub_size", 18))
	var sub := _t(pl, L.get("sub", {}))
	var w := clampf(maxf(_width(_t(pl, L.get("title", {})), px, true), _width(sub, spx)) + 220.0, 440.0, 1100.0)
	return Rect2(640.0 - w * 0.5, float(L.y) - 10.0, w, px * 1.2 + (spx * 1.4 if sub != "" else 0.0) + _more(pl, L).size() * 24.0 + 22.0)

func _more(pl: Dictionary, L: Dictionary) -> Array:
	return (L.get("more", []) as Array).map(func(s): return _t(pl, s)).filter(func(s): return s != "")

func _draw_strip(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	_ink(ci, _strip_rect(pl, L), lt, 0.25, 0.88 * a, still)
	var ta := a * _in(lt, 0.1, 0.2)
	var px := float(L.get("size", 30))
	var y := float(L.y) + px * 0.8
	_write(ci, _t(pl, L.get("title", {})), Vector2(0, y), px, Color(_col(pl, L.get("color"), UiKit.PALE_GOLD), ta), true)
	var sub := _t(pl, L.get("sub", {}))
	if sub != "":
		y += float(L.get("sub_size", 18)) * 1.4
		_write(ci, sub, Vector2(0, y), float(L.get("sub_size", 18)), Color(_col(pl, L.get("sub_color"), UiKit.MIST), ta))
	for line in _more(pl, L):
		y += 24.0
		_write(ci, line, Vector2(0, y), 17.0, Color(_col(pl, L.get("more_color"), UiKit.MIST), ta))

## A card in the kit's toast frame (the tribulation weathered): its lines and a bar, sliding in.
func _draw_card(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	if L.has("slot") and not pl.slots.has(str(L.slot)): return
	var rr: Array = L.rect
	var r := Rect2(float(rr[0]), float(rr[1]), float(rr[2]), float(rr[3]))
	if not still and str(L.get("slide_from", "")) == "left": r.position.x -= r.end.x * pow(1.0 - _in(lt, 0.0, 0.3), 2.0)
	var fa := a * (_in(lt, 0.0, 0.2) if still or str(L.get("frame", "toast")) == "" else 1.0)
	if str(L.get("frame", "toast")) != "": _box(ci, str(L.get("frame", "toast")), r, fa)
	var centre := str(L.get("align", "")) == "center"
	var y := r.position.y + 30.0
	for line in L.get("lines", []):
		var px := float(line.get("size", 16))
		var s := _t(pl, line.text)
		if s == "": continue
		if centre: y += px * 0.5
		_write(ci, s, Vector2(r.position.x + (0.0 if centre else 20.0), y), px, Color(_col(pl, line.get("color"), UiKit.PAPER), fa), line.get("display", false),
			HORIZONTAL_ALIGNMENT_CENTER if centre else HORIZONTAL_ALIGNMENT_LEFT, r.size.x - (0.0 if centre else 40.0))
		y += px * (0.85 if centre else 1.35)
	if L.has("bar"):
		var v := clampf(float(MomentRules.value(L.bar.value, pl.p, pl.slots)) / 100.0, 0.0, 1.0)
		var br := Rect2(r.position.x + 20.0, r.end.y - 26.0, 220.0, 10.0)
		ci.draw_rect(br.grow(2.0), Color(UiKit.INK, fa))
		ci.draw_rect(Rect2(br.position, Vector2(br.size.x * v, br.size.y)), Color(_col(pl, L.bar.get("color"), UiKit.RED), fa))
		_write(ci, _t(pl, L.bar.label), Vector2(br.end.x + 12.0, br.end.y + 1.0), 14.0, Color(UiKit.MIST, fa), false, HORIZONTAL_ALIGNMENT_LEFT, r.end.x - br.end.x - 16.0)

## The stat rise (§2.3): the numbers that rose since the snapshot, at most seven, one after another.
func _draw_stats(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	var was: Dictionary = pl.slots.get("before", {})
	var now: Dictionary = pl.slots.get("now", {})
	var at := Vector2(float(L.at[0]), float(L.at[1]))
	var n := 0
	for id in ContentDB.config("moments").get("stats", []):
		if n >= 7: break
		if not was.has(id) or not now.has(id) or float(now[id]) <= float(was[id]) + 0.0001: continue   # a rise shows what rose
		var k := a * _in(lt, n * float(L.get("gap_s", 0.12)), 0.25)
		var y := at.y + 20.0 + n * float(L.get("row_h", 36)) + (0.0 if still else 12.0 * (1.0 - k))
		n += 1
		if k <= 0.0: continue
		var val := _stat_text(str(id), float(now[id]))
		var up := Tx.t("moment.stat.from") % _stat_text(str(id), float(was[id])) if str(id) == "level" else Tx.t("moment.stat.up") % _stat_text(str(id), float(now[id]) - float(was[id]), true)
		var vw: float = UiKit.body_font().get_string_size(val, HORIZONTAL_ALIGNMENT_LEFT, -1, int(round(20 * UiKit.text_scale()))).x if UiKit.is_numeric(val) else UiKit.text_width(val, 20)
		UiKit.draw_outlined(ci, Tx.t("moment.stat." + str(id)), Vector2(at.x - 40.0, y), 16, Color(UiKit.MIST, k), HORIZONTAL_ALIGNMENT_RIGHT, 158)
		UiKit.draw_outlined(ci, val, Vector2(at.x + 128.0, y), 20, Color(UiKit.PAPER, k), HORIZONTAL_ALIGNMENT_LEFT, 200)
		UiKit.draw_outlined(ci, up, Vector2(at.x + 140.0 + vw, y), 16, Color(UiKit.BRIGHT_JADE, k), HORIZONTAL_ALIGNMENT_LEFT, 200)

static func _stat_text(id: String, v: float, delta := false) -> String:
	if UiKit._stat_is_percent(id): return "%.1f%%" % (v * 100.0)
	return Tx.t("moment.years") % UiKit.fmt(v) if id == "lifespan" and not delta else UiKit.fmt(v)

## The next-unlock chips (E5): what the new stage opens, one above another.
func _draw_chip(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	if _pill == null:
		_pill = StyleBoxFlat.new()
		_pill.set_corner_radius_all(18)
		_pill.set_border_width_all(1)
		_pill.anti_aliasing = true
	var list: Array = pl.slots.get(str(L.get("slot", "unlocks")), [])
	for i in list.size():
		var k := a * _in(lt, i * 0.15, 0.25)
		if k <= 0.0: continue
		var s := Tx.t("moment.opens") % str(list[i].get("label", ""))
		var ic := not SpriteCache.icon_fit(str(list[i].get("system", "")), 32.0).is_empty()
		var w := UiKit.text_width(s, 18) + (58.0 if ic else 28.0)
		var r := Rect2(minf(float(L.at[0]), 1264.0 - w), float(L.at[1]) - i * 46.0 + (0.0 if still else 8.0 * (1.0 - k)), w, 40.0)
		_pill.bg_color = Color(UiKit.INK.lerp(UiKit.GOLD, 0.12), 0.8 * k)
		_pill.border_color = Color(UiKit.GOLD, 0.55 * k)
		ci.draw_style_box(_pill, r)
		if ic: SpriteCache.draw_icon(ci, Rect2(r.position + Vector2(6, 4), Vector2(32, 32)), str(list[i].get("system", "")), Color(1, 1, 1, k))
		UiKit.draw_text(ci, s, r.position + Vector2(46.0 if ic else 14.0, 27.0), 18, Color(UiKit.PALE_GOLD, k))

## A vermilion seal stamped with a squash from 1.4x; `at` is a point, or "band"/"strip" for that layer's right end.
func _draw_seal(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	var px := float(L.get("size", 44))
	var at := Vector2(640, 200)
	if L.get("at") is Array: at = Vector2(float(L.at[0]), float(L.at[1])) + Vector2(px, px) * 0.5
	elif str(L.get("at", "")) in ["band", "strip"]:
		var host := _layer(pl, str(L.at))
		var hr := _band_rect(pl, host) if str(L.at) == "band" else _strip_rect(pl, host)
		at = Vector2(hr.end.x - px * 0.75, hr.get_center().y + px * 0.4)
	var s := 1.0 if still else lerpf(1.4, 1.0, _in(lt, 0.0, 0.12))
	var al := a * _in(lt, 0.0, 0.06)
	var h := px * 0.5
	ci.draw_set_transform(at, deg_to_rad(float(L.get("angle", -8))), Vector2(s, s))
	ci.draw_rect(Rect2(-h - 2.0, -h - 2.0, px + 4.0, px + 4.0), Color(UiKit.INK, al))
	ci.draw_rect(Rect2(-h, -h, px, px), Color(_col(pl, L.get("color"), UiKit.RED), al))
	ci.draw_rect(Rect2(-h + 3.0, -h + 3.0, px - 6.0, px - 6.0), Color(UiKit.PALE_GOLD, 0.55 * al), false, 1.5)
	var mark := _t(pl, L.get("text", {}))
	if mark != "": _write(ci, mark, Vector2(-h, px * 0.24), px * 0.7, Color(UiKit.PALE_GOLD, al), true, HORIZONTAL_ALIGNMENT_CENTER, px)
	ci.draw_set_transform(Vector2.ZERO)

## P9's seals of the fight, pressed one by one (`slot` holds their text sources).
func _draw_stamps(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, still: bool) -> void:
	var list: Array = pl.slots.get(str(L.get("slot", "stamps")), [])
	var px := float(L.get("size", 40))
	for i in list.size():
		var one := {"at": [float(L.at[0]) + i * (px + 12.0), float(L.at[1])], "size": px, "angle": -8 + (i % 2) * 10, "text": list[i]}
		_draw_seal(ci, pl, one, lt - i * float(L.get("gap_s", 0.3)), a, still)

## A line of speech under the card.
func _draw_subtitle(ci: Node2D, pl: Dictionary, L: Dictionary, lt: float, a: float, _still: bool) -> void:
	var s := _t(pl, L.get("text", {}))
	if s == "": return
	var fa := a * _in(lt, 0.0, 0.25)
	var w := _width(s, 20.0) + 48.0
	ci.draw_rect(Rect2(640.0 - w * 0.5, float(L.y) - 24.0, w, 34.0), Color(UiKit.INK, 0.55 * fa))
	_write(ci, s, Vector2(0, float(L.y)), 20.0, Color(UiKit.PAPER, fa))
