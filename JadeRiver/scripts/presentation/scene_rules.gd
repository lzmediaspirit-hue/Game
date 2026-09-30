class_name SceneRules
extends RefCounted
## Decision 39 (docs/redesign/story_staging.md): the rules of a staged scene (data/scenes.json, built by
## tools/data/scenes.py), static and pure, shared by the SceneDirector that plays them and the suites that check them:
## the step kinds, where a scene's actors stand and walk, how long each step holds the stage, and each scene's problems.
##
## A scene is a list of steps played in a room on the height grid. Its actors are the room's own people (an NPC object),
## extras it brings on (a villager, a prop such as a passing boat) and the player's body. It asks the authorities for
## what it changes (QuestAuthority's scene_begin, scene_mark, scene_end: a checkpoint's effects) and draws the rest.

## Every step kind and what it works on: an actor, the camera, the screen, the world, the flow of the script, or the
## hand-off to the player.
const STEP_KINDS := {"move": "actor", "face": "actor", "emote": "actor", "pose": "actor", "say": "actor",
	"camera": "camera", "zoom": "camera", "shake": "camera", "letterbox": "camera", "hitstop": "camera",
	"fade": "screen", "flash": "screen", "title": "screen",
	"spawn": "world", "despawn": "world", "door": "world", "weather": "world", "moment": "world", "fx": "world", "sound": "world",
	"art": "world", "foe": "world",
	"wait": "flow", "wait_input": "flow", "wait_event": "flow", "branch": "flow", "label": "flow", "goto": "flow", "mark": "flow",
	"handoff": "hand"}
## The balloons over a head (research §2.3: the "!" of surprise, the "?" of doubt, a song, a heart, a vein of anger, a
## drop of sweat, a bulb of an idea, and silence).
const EMOTES := ["!", "?", "...", "note", "heart", "anger", "sweat", "idea"]
const WEATHER := ["storm", "rain", "clear"]
const BOXES := ["balloon", "portrait"]
## The HUD controls a hand-off may point at (their roles in HUD.hit_targets).
const HUD_ROLES := ["attack", "jump", "guard", "skill", "quick:0", "quick:1", "quick:2", "meditate", "context", "icon:bag", "icon:map", "icon:menu"]

static func cfg() -> Dictionary:
	return ContentDB.config("scenes").get("settings", {})

static func row(id: String) -> Dictionary:
	return ContentDB.entry("scenes", id)

## A layout cell [x, y] (fractions allowed) as a ground point in world units: the cell's centre.
static func point(at) -> Vector2:
	return TopdownRoom.cell_point(at) if at is Array else Vector2.ZERO

## How long a line holds the stage: read at an unhurried pace, never less than the floor, never more than the ceiling.
static func read_s(text: String) -> float:
	var s := cfg()
	return clampf(float(s.get("read_base_s", 1.0)) + float(s.get("read_word_s", 0.3)) * text.split(" ", false).size(),
		float(s.get("read_min_s", 2.0)), float(s.get("read_max_s", 6.0)))

## An actor's walking pace in world units a second: a stroll, or a run.
static func pace(step: Dictionary) -> float:
	return float(step.get("speed", cfg().get("run" if step.get("run", false) else "walk", 110.0)))

## The seconds a step holds the stage (the script waits for it), `dist` being a move's length in world units. A step
## that starts something and goes on (`wait: false`) holds nothing; a hand-off is the player's time, not the stage's.
static func step_s(step: Dictionary, dist := 0.0) -> float:
	var waits: bool = step.get("wait", true)
	match str(step.get("do", "")):
		"say": return read_s(str(step.get("text", "")))
		"wait", "fade", "title": return float(step.get("s", 2.5 if str(step.do) == "title" else 1.0))
		"move":
			# A walk to beside something where it stands (decision 45) is measured at its `est_s`.
			if (step.get("to", []) as Array).any(func(q): return q is Dictionary): return float(step.get("est_s", 1.5)) if waits else 0.0
			return dist / pace(step) if waits else 0.0
		"hitstop": return float(step.get("s", 0.1))
		"camera", "zoom": return float(step.get("s", 1.0)) if waits else 0.0
		"emote", "pose": return float(step.get("s", 1.0)) if step.get("wait", false) else 0.0
		"wait_input": return float(cfg().get("tap_s", 1.0))
		"wait_event": return float(step.get("s", 0.0))
		"moment": return float(ContentDB.entry("moments", str(step.get("row", ""))).get("duration_s", 0.0))
	return 0.0

## Where an actor stands when its scene begins: {at (world units), alt, npc (for a person), prop (for a thing), extra,
## object (the room's NPC object it is)}. `def` is the room's runtime definition (its places on the grid).
static func home(scene: Dictionary, name: String, def: Dictionary, grid: TopdownRoom) -> Dictionary:
	var a: Dictionary = scene.get("actors", {}).get(name, {})
	if a.has("object"):
		for o in def.get("objects", []):
			if str(o.get("id", "")) == str(a.object):
				var at := Vector2(float(o.at[0]), float(o.at[1]))
				return {"at": at, "alt": float(o.get("alt", 0.0)), "npc": str(o.get("npc", "")), "object": str(o.id), "extra": false}
		return {}
	if a.is_empty() or not a.has("at"): return {}
	var p := point(a.at)
	var alt := grid.floor_at(p) if grid != null else 0.0
	if a.has("prop"): alt = float(a.get("level", 0)) * TopdownRoom.LEVEL
	return {"at": p, "alt": alt, "npc": str(a.get("npc", "")), "prop": str(a.get("prop", "")), "object": "", "extra": true, "hidden": a.get("hidden", false)}

## The index of each label in a scene's steps.
static func labels(scene: Dictionary) -> Dictionary:
	var out := {}
	var steps: Array = scene.get("steps", [])
	for i in steps.size():
		if str(steps[i].get("do", "")) == "label": out[str(steps[i].get("name", ""))] = i
	return out

## The staged seconds of a scene, its cut parts only (the hand-offs are the player's): each move measured along its
## path from where the actor stands at that point of the script, taken in order.
static func length(scene: Dictionary, def: Dictionary, grid: TopdownRoom) -> float:
	var at := {}
	var total := 0.0
	for st in scene.get("steps", []):
		var dist := 0.0
		if str(st.get("do", "")) == "move":
			var who := str(st.get("actor", ""))
			if not at.has(who):
				var h := home(scene, who, def, grid)
				at[who] = h.get("at", Vector2.ZERO)
			for q in st.get("to", []):
				if q is Dictionary: continue   # beside something where it stands: measured at its est_s
				var p := point(q)
				if who != "player": dist += (at[who] as Vector2).distance_to(p)
				at[who] = p
		total += step_s(st, dist)
	return total

## A path on the grid through a move's waypoints for a walker: [world points], [] when a leg has no way on foot.
static func walk_path(grid: TopdownRoom, from: Vector2, to: Array) -> Array:
	var out: Array = []
	var cur := from
	for q in to:
		var goal := point(q)
		var a := TopdownRoom.cell_of(cur)
		var b := TopdownRoom.cell_of(goal)
		if a != b:
			var cells := grid.find_path(a, b, false, 4000)
			if cells.is_empty(): return []
			for k in cells.size() - 1: out.append((Vector2(cells[k]) + Vector2(0.5, 0.5)) * TopdownRoom.TILE)
		out.append(goal)
		cur = goal
	return out

## Everything wrong with a scene, as lines (the tests hold every scene to none): its room is on the grid; its trigger
## and hand-offs wait on events of the contract; its actors are the room's people, a person of npcs.json or a prop of
## the tile set, standing where a body can stand; every step is a known kind naming declared actors, known poses,
## emotes, sounds, effects, moments, doors and labels; every walk has a way on foot; the checkpoints' effects are ones
## a scene may use; and its staged time is within the settings' bounds.
## Test hook: data_validation and story_scenes.
static func problems(scene: Dictionary) -> Array:
	var out: Array = []
	var id := str(scene.get("id", "?"))
	var rid := str(scene.get("room", ""))
	if not TopdownRoom.has_layout(rid) or ContentDB.room(rid).is_empty(): return ["%s: room %s has no layout on the grid" % [id, rid]]
	var grid := TopdownRoom.load_room(rid)
	var def := grid.merge_def(ContentDB.room(rid))
	var events: Dictionary = ContentDB.config("event_contract").get("events", {})
	var trig: Dictionary = scene.get("trigger", {})
	if not trig.is_empty() and not events.has(str(trig.get("event", ""))): out.append("%s: trigger event %s is not in the contract" % [id, str(trig.get("event", ""))])
	var actors: Dictionary = scene.get("actors", {})
	# The top-down figure's actions (data/topdown/character.json), the player's and the people's alike, and the side
	# view's names it plays under another (its aliases).
	var poses: Array = (TopdownFigure.manifest().get("actions", {}) as Dictionary).keys() + (TopdownFigure.manifest().get("aliases", {}) as Dictionary).keys()
	for name in actors:
		var h := home(scene, str(name), def, grid)
		var a: Dictionary = actors[name]
		if h.is_empty(): out.append("%s: actor %s stands nowhere (%s)" % [id, name, str(a)])
		elif a.has("object") and not ContentDB.has_entry("npcs", str(h.npc)): out.append("%s: actor %s is no person of the room" % [id, name])
		elif a.has("npc") and not ContentDB.has_entry("npcs", str(a.npc)): out.append("%s: actor %s is no person of npcs.json" % [id, name])
		elif a.has("prop") and not grid.tileset.get("props", {}).has(str(a.prop)): out.append("%s: actor %s is no prop of the tile set" % [id, name])
		elif a.has("npc") and not grid.standable(TopdownRoom.cell_of(h.at)): out.append("%s: actor %s starts where no body stands" % [id, name])
	var marks := labels(scene)
	var sfx: Array = (ContentDB.config("audio").get("sfx", {}) as Dictionary).keys()
	var at := {}
	for i in (scene.get("steps", []) as Array).size():
		var st: Dictionary = scene.steps[i]
		var kind := str(st.get("do", ""))
		var where := "%s step %d (%s)" % [id, i, kind]
		if not STEP_KINDS.has(kind):
			out.append("%s: unknown step" % where)
			continue
		var who := str(st.get("actor", ""))
		if STEP_KINDS[kind] == "actor" or kind in ["spawn", "despawn"]:
			if who != "player" and not actors.has(who):
				out.append("%s: actor %s is not declared" % [where, who])
				continue
		match kind:
			"move":
				if (st.get("to", []) as Array).is_empty(): out.append("%s: goes nowhere" % where)
				var beside: Array = (st.get("to", []) as Array).filter(func(q): return q is Dictionary)
				for q in beside:
					if not _target_ok(q.get("near", ""), actors, def): out.append("%s: goes beside %s" % [where, str(q.get("near", ""))])
					if q.has("mirror") and not _target_ok(q.mirror, actors, def): out.append("%s: mirrors on %s" % [where, str(q.mirror)])
				if beside.is_empty() and who != "player" and str(actors[who].get("prop", "")) == "":
					if not at.has(who): at[who] = home(scene, who, def, grid).get("at", Vector2.ZERO)
					if walk_path(grid, at[who], st.get("to", [])).is_empty(): out.append("%s: %s has no way on foot to %s" % [where, who, str(st.get("to", []))])
				if not (st.get("to", []) as Array).is_empty() and beside.is_empty(): at[who] = point(st.to.back())
			"face":
				var to = st.get("to", "")
				if not (to is Array) and not str(to) in ["n", "s", "e", "w", "player"] and not actors.has(str(to)) and not (str(to).contains(":") and _target_ok(to, actors, def)): out.append("%s: faces %s" % [where, str(to)])
			"emote": if not str(st.get("emote", "")) in EMOTES: out.append("%s: emote %s" % [where, str(st.get("emote", ""))])
			"pose":
				if not str(st.get("pose", "")) in poses: out.append("%s: pose %s is not one %s has" % [where, str(st.get("pose", "")), who])
			"say":
				if str(st.get("text", "")).strip_edges() == "": out.append("%s: says nothing" % where)
				if not str(st.get("box", "balloon")) in BOXES: out.append("%s: box %s" % [where, str(st.get("box", ""))])
			"title": if str(st.get("title", "")) == "": out.append("%s: no title" % where)
			"camera": if not _target_ok(st.get("to", "player"), actors, def): out.append("%s: looks at %s" % [where, str(st.get("to", ""))])
			"fx":
				if not str(st.get("fx", "")) in FxLayer.KINDS: out.append("%s: fx %s" % [where, str(st.get("fx", ""))])
				if not _target_ok(st.get("at", "player"), actors, def): out.append("%s: at %s" % [where, str(st.get("at", ""))])
			"sound": if not str(st.get("sfx", "")) in sfx: out.append("%s: sound %s" % [where, str(st.get("sfx", ""))])
			"moment": if not ContentDB.has_entry("moments", str(st.get("row", ""))): out.append("%s: moment %s" % [where, str(st.get("row", ""))])
			"door": if def.get("portals", []).filter(func(p): return str(p.id) == str(st.get("portal", ""))).is_empty(): out.append("%s: door %s" % [where, str(st.get("portal", ""))])
			"weather": if not str(st.get("kind", "")) in WEATHER: out.append("%s: weather %s" % [where, str(st.get("kind", ""))])
			"spawn", "despawn":
				if not actors.get(who, {}).get("npc", actors.get(who, {}).get("prop", "")): out.append("%s: %s is no extra" % [where, who])
				if st.get("at") is Dictionary and not _target_ok(st.at.get("near", ""), actors, def): out.append("%s: spawns beside %s" % [where, str(st.at.get("near", ""))])
				if st.get("at") is Dictionary and st.at.has("mirror") and not _target_ok(st.at.mirror, actors, def): out.append("%s: mirrors on %s" % [where, str(st.at.mirror)])
			# Decision 45: a story art of the FX pipeline where a target stands, a foe of the room staged, a hit-stop.
			"art":
				if not (ContentDB.config("fx_topdown").get("story", {}).get("arts", {}) as Dictionary).has(str(st.get("art", ""))): out.append("%s: art %s is no story art of the FX sheets" % [where, str(st.get("art", ""))])
				if not _target_ok(st.get("at", "player"), actors, def): out.append("%s: at %s" % [where, str(st.get("at", ""))])
				if st.has("from") and not _target_ok(st.from, actors, def): out.append("%s: comes from %s" % [where, str(st.from)])
			"foe":
				var foe := str(st.get("foe", ""))
				var acts: Dictionary = grid.tileset.get("foes", {}).get("species", {}).get(foe, {}).get("actions", {}) if ContentDB.has_entry("enemies", foe) else {}
				if not ContentDB.has_entry("enemies", foe): out.append("%s: foe %s" % [where, foe])
				elif str(st.get("pose", "")) != "" and not acts.has(str(st.pose)): out.append("%s: %s has no %s on its sheet" % [where, foe, str(st.pose)])
				if st.has("dread") and not (st.dread is bool): out.append("%s: dread %s is no yes or no" % [where, str(st.dread)])
			"hitstop": if float(st.get("s", 0.0)) <= 0.0 or float(st.get("s", 0.0)) > 0.5: out.append("%s: a hit-stop of %.2f s" % [where, float(st.get("s", 0.0))])
			"branch", "goto":
				for k in ["then", "else", "label"]:
					if st.has(k) and not marks.has(str(st[k])): out.append("%s: no label %s" % [where, str(st[k])])
			"wait_event", "handoff":
				var until: Array = st.get("until", [])
				for u in until:
					if not events.has(str(u.get("event", ""))): out.append("%s: waits on %s, not in the contract" % [where, str(u.get("event", ""))])
				if until.is_empty() and not st.has("done_if") and float(st.get("s", 0.0)) <= 0.0: out.append("%s: waits for ever" % where)
				if kind == "handoff":
					if str(st.get("prompt", "")) == "": out.append("%s: no prompt" % where)
					if not _target_ok(st.get("at", "player"), actors, def): out.append("%s: prompt at %s" % [where, str(st.get("at", ""))])
		for e in st.get("effects", []):
			if not kind in ["mark", "handoff"] or not str(e.get("kind", "")) in QuestAuthority.SCENE_EFFECTS: out.append("%s: effect %s" % [where, str(e)])
	var s := length(scene, def, grid)
	var lo := float(cfg().get("min_s", 10.0))
	var hi := float(cfg().get("max_s", 40.0))
	if s < lo or s > hi: out.append("%s: staged for %.1f s, not %d-%d" % [id, s, int(lo), int(hi)])
	return out

## A target a step names: "player", an actor, a cell, or "object:<id>", "portal:<id>", "enemy:<def>", "hud:<role>".
static func _target_ok(to, actors: Dictionary, def: Dictionary) -> bool:
	if to is Array: return (to as Array).size() == 2
	var s := str(to)
	if s == "player" or actors.has(s): return true
	var kind := s.get_slice(":", 0)
	var what := s.get_slice(":", 1)
	match kind:
		"object": return def.get("objects", []).any(func(o): return str(o.id) == what)
		"portal": return def.get("portals", []).any(func(p): return str(p.id) == what)
		"enemy": return ContentDB.has_entry("enemies", what)
		"hud": return what in HUD_ROLES or s.trim_prefix("hud:") in HUD_ROLES
	return false
