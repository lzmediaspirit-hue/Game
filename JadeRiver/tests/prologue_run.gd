extends Node
## Scripted Prologue run (S27 test): drives the real authorities through intents
## only, from a new character to Bone Forging 2, checking the HUD reveal order and
## that no weapon appears before the Weapon Hall. Movement is a bound ActorState
## placed next to targets (the world scene is not needed). The story's own quests and
## fights carry the character to Bone Forging 2: no test shortcut. `play_s` keeps an
## estimate of the player's time (the simulated seconds, walking at run speed, and
## reading the dialogue), which tutorial_order's first-hour pacing check reads. Run headless:
##   godot --headless --path . res://tests/prologue_run.tscn

var failures := 0
var checks := 0
var reveal_log: Array = []
var events: Array = []
var st: ActorState
var verbose := false
## The first-hour clock (research player_motivation P2): an estimate of the seconds a new player spends, as the walk
## plays. The simulated time the walk steps; the walking between the points it stands at, room by room, at the pace of
## a thumb on the joystick (a portal's far side is where the walk out ends); a look round each room the first time;
## and the time to read each line of dialogue and tap on.
var play_s := 0.0
## Extra fields of the new character's create_character intent (topdown_tutorial: {"view": "topdown"}).
var create_extra := {}
var _clock_room := ""
var _rooms_seen := {}
const WALK_SPEED := 150.0    # player.gd runs at 205; a thumb on the joystick weaves
const LOOK_S := 15.0         # a room seen for the first time
const READ_S := 3.0          # a line of dialogue, read
const TAP_S := 1.5           # a tap on the dialogue page
const USE_S := 2.0           # an interaction: pick up, inspect, pray
const HIT_S := 0.45          # one blow of the combo on a stump or dummy

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)
	elif verbose:
		print("ok: ", what)

func _ready() -> void:
	verbose = "--verbose" in OS.get_cmdline_user_args()
	call_deferred("_main")

func _main() -> void:
	run()
	print("prologue_run: %d checks, %d failures" % [checks, failures])
	end_suite()

## End the suite: drop this run's own save folder and quit with the result.
func end_suite() -> void:
	_remove_tree(run_root())
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ determinism
## Every scripted run plays the same on any machine under any load: the dice are seeded (start_new), the clock is
## simulated (Clock.simulate: "now" starts at START_UTC and moves only as Game.tick steps the fixed 0.05 s simulation,
## never with the wall clock), every wait is counted in simulated seconds, and the saves live in a folder of this run's
## own (run_root), never one shared with another run of the suite on the same machine.
const START_UTC := 1789997760.0   # the start of an in-game morning (a multiple of the 48-minute day)
const RUN_SEED := 20260925

## This run's own folder under user:// (other runs of the suite, in other checkouts too, share user://).
func run_root() -> String:
	return "user://test_runs/%s_%d/" % [str(get_script().resource_path).get_file().get_basename(), OS.get_process_id()]

func _remove_tree(dir: String) -> void:
	if not DirAccess.dir_exists_absolute(dir): return
	for d in DirAccess.get_directories_at(dir): _remove_tree(dir + d + "/")
	for f in DirAccess.get_files_at(dir): DirAccess.remove_absolute(dir + f)
	DirAccess.remove_absolute(dir)

# ------------------------------------------------------------------ helpers
## Called after every tick of the simulation (tests/tutorial_order.gd watches what the HUD shows of each fight).
var tick_watch := Callable()

func step(seconds: float) -> void:
	play_s += seconds
	var t := 0.0
	while t < seconds:
		Game.tick(0.05)
		if tick_watch.is_valid(): tick_watch.call()
		story_guidance()
		t += 0.05

func submit(i: Dictionary) -> Dictionary:
	var r := Game.submit(i)
	story_guidance()
	return r

## Decision 39: the staged scenes, where a walk plays them (topdown_tutorial, story_scenes): a SceneDirector with no
## view. `settle_scenes` runs the scene on the stage on the director's clock while it holds the stage (a cut, a live
## part, a hand-off that ends by itself), a cut's seconds on the play clock (the simulation stands still in a cut, as
## in the game); it stops at a hand-off that waits on the player, whose deed is the walk's next step.
var scene_director: SceneDirector = null

func settle_scenes(limit_s := 120.0) -> void:
	if scene_director == null: return
	var t := 0.0
	for next in 6:   # a scene over, the next one waiting may take the stage
		scene_director.poll()
		if not scene_director.busy(): return
		while scene_director.busy() and t < limit_s:
			if scene_director.in_cut(): play_s += 0.1
			scene_director.advance(0.1)
			t += 0.1

# ------------------------------------------------------------------ story guidance
## Story guidance (docs/tutorial_order.md): tutorial_order and valley_run hold every step of the story to it. After each
## step that moves the story (a quest taken, offered or finished, a realm, an unlock, a sect chosen), once the tracker is
## on the HUD:
##   1. the tracker is never empty while the built story has a quest left;
##   2. every entry's target (the room its step is in, its giver's room, a hunting ground) is a real room the character
##      can walk to from where it stands (a story instance entered by its event aside), and the direction mark leads
##      toward the first story entry's (the minimap marks this room's way out to it);
##   3. between main quests the first entry is the story's next quest: its giver stands in the room it names, a head
##      marker calling the player over, or it waits on a Level and names a hunting ground whose foes suit the Level;
##   4. the moment a sect is chosen the character is recorded as its member, and the sect's first quest (the Entry
##      Trial) is under way at the head of the tracker, with its target and the direction mark.
var guidance := false
var guidance_steps := 0
var _story_moved := ""
var _sect_chosen := ""

## --keep=<label>,... saves the character as it stands at the named points of the walk (tutorial_order's step labels,
## and the points inside the steps below) to user://tutorial_cp/<label>/, for screenshots from a brand-new character.
func keep(label: String) -> void:
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--keep=") and label in str(a).trim_prefix("--keep=").split(","):
			Game.save_all()
			_copy_dir(Saves.repo.root, "user://tutorial_cp/%s/" % label.to_lower().replace(" ", "_").replace("'", ""))

## A checkpoint of the run in `dir`: the saves as they stand, and the run's simulated clock and its skips beside them
## (`<dir>.clock`), so timed state (auction lots, cooldowns) resumes in step (valley_run's sections; topdown_tutorial's
## second sect, taken from the fair).
func save_checkpoint(dir: String) -> void:
	Game.save_all()
	_copy_dir(Saves.repo.root, dir)
	var f := FileAccess.open(dir.trim_suffix("/") + ".clock", FileAccess.WRITE)
	if f != null: f.store_string(JSON.stringify({"utc": "%.3f" % Clock.override_utc, "offset": "%.3f" % Clock.debug_offset_s}))

## Resume a checkpoint into the working folder `work`: the saves and the clock restored, the character back in its world
## where it stood. False when there is none, or it does not load.
func resume_checkpoint(dir: String, work: String) -> bool:
	if not DirAccess.dir_exists_absolute(dir): return false
	_copy_dir(dir, work)
	Clock.simulate(START_UTC)
	var clock := dir.trim_suffix("/") + ".clock"
	if FileAccess.file_exists(clock):
		var saved = JSON.parse_string(FileAccess.get_file_as_string(clock))
		if saved is Dictionary:
			Clock.override_utc = float(str(saved.get("utc", START_UTC)))
			Clock.debug_offset_s = float(str(saved.get("offset", 0.0)))
	Saves.use_folder(work)
	Game.boot()
	Game.autosave_enabled = false
	if not submit({"type": "enter_character", "slot": 1}).get("ok", false): return false
	if not submit({"type": "enter_world"}).get("ok", false): return false
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	return true

## Start holding the story to its guidance (after the game has booted).
func watch_story() -> void:
	guidance = true
	GameEvents.event.connect(func(n: String, p: Dictionary):
		if n in ["quest_completed", "quest_accepted", "quest_offered", "realm_changed", "system_unlocked"]:
			_story_moved = "%s %s" % [n, str(p.get("quest", p.get("realm", p.get("system", ""))))]
		if n == "sect_joined": _sect_chosen = str(p.get("sect", "")))

## A tracker entry whose lines ask for the breakthrough (the Cultivate button at a bottleneck).
static func _breakthrough_entry(e: Dictionary) -> bool:
	var asks := [Tx.t("hud.bottleneck_tap_cultivate_to_break"), Tx.t("hud.bottleneck_reached_see_the_cultivation")]
	return (e.get("lines", []) as Array).any(func(l): return str(l.get("text", "")) in asks)

func story_guidance() -> void:
	if not guidance or (_story_moved == "" and _sect_chosen == "") or c() == null or Game.room_rt == null: return
	var at := "%s, in %s" % [_story_moved if _story_moved != "" else "a sect chosen", room()]
	_story_moved = ""
	guidance_steps += 1
	var here := room()
	var tr: Array = Game.quest.tracker(c())
	var under_way: bool = c().quests.active.keys().any(func(q): return QuestAuthority.leads(str(Game.quest.quest_def(c(), str(q)).get("kind", ""))))
	if Game.is_revealed("hud:quest_tracker") and (under_way or not Game.quest.story_waiting(c(), QuestAuthority.STORY_KINDS).is_empty()):
		check(not tr.is_empty(), "story guidance (%s): the tracker is not empty" % at)
	for e in tr:
		var t := str(e.get("target_room", ""))
		# Decision 41: past the prototype's gate a top-down character's tracker leads nowhere, and says so.
		if e.get("gate", false):
			check(t == "" and str(c().view) == "topdown" and _story_past_gate(), "story guidance (%s): '%s' leads nowhere only at the prototype's end" % [at, e.name])
			continue
		# At a bottleneck one breakthrough short of the Level the story waits on, the Next entry is the breakthrough: it
		# names no room (there is nowhere to go), only what to tap.
		if str(e.kind) == "next" and t == "" and _breakthrough_entry(e):
			check(str(c().cultivator.state) == "bottleneck", "story guidance (%s): '%s' asks for a breakthrough only at a bottleneck" % [at, e.name])
			continue
		if str(e.kind) == "next": check(t != "", "story guidance (%s): the next entry '%s' names where to go" % [at, e.name])
		if t == "": continue
		check(not ContentDB.room(t).is_empty() and _walks_to_room(t), "story guidance (%s): '%s' leads to %s, a room the character can walk to" % [at, e.name, t])
	if not tr.is_empty() and str(tr[0].kind) == "next" and not tr[0].get("gate", false) and not (str(tr[0].target_room) == "" and _breakthrough_entry(tr[0])):
		var nx: Dictionary = tr[0]
		var t0 := str(nx.target_room)
		if nx.get("hunt", false):
			var lv := ProgressionRules.level(c())
			var lr: Array = ContentDB.room(t0).get("level_range", [0, 0])
			check(str(ContentDB.room(t0).get("type", "")) == "field" and lv >= int(lr[0]), "story guidance (%s): '%s' waits on a Level and names a hunting ground for Level %d (%s %s)" % [at, nx.name, lv, t0, str(lr)])
		else:
			var d := ContentDB.entry("quests", str(nx.quest))
			var giver := QuestAuthority.own_npc(c(), d.get("giver_any", d.get("giver", "")))
			check(giver == "" or Game.quest.npc_rooms(c(), giver).has(t0), "story guidance (%s): '%s' names %s, who stands in %s" % [at, nx.name, giver, t0])
			# ... and there the P1 head marker calls the player over to them (the gold mark, or the jade-ringed repeat one).
			if c().quests.offered.has(str(nx.quest)) and giver != "":
				check(QuestAuthority.marker_calls(Game.quest.npc_marker(c(), giver)), "story guidance (%s): %s's head marker calls the player to '%s' (%s)" % [at, giver, nx.name, Game.quest.npc_marker(c(), giver)])
	var lead: Array = tr.filter(func(e): return QuestAuthority.leads(str(e.kind)) and str(e.get("target_room", "")) not in ["", here])
	if not lead.is_empty() and not ContentDB.room(str(lead[0].target_room)).get("instanced", false):
		check(Game.world.guide_target(c()) == str(lead[0].target_room) and not Game.world.guide_step(c()).is_empty(),
			"story guidance (%s): the direction mark leads toward %s ('%s'; %s)" % [at, str(lead[0].target_room), lead[0].name, str(Game.world.guide_step(c()))])
	if _sect_chosen != "":
		check(str(c().training_sect.get("id", "")) == _sect_chosen, "story guidance: the chosen sect (%s) is recorded (%s)" % [_sect_chosen, str(c().training_sect)])
		var first: Dictionary = tr[0] if not tr.is_empty() else {}
		check(c().quests.is_active("entry_trial") and str(first.get("quest", "")) == "entry_trial" and str(first.get("target_room", "")) != ""
			and (str(first.target_room) == here or Game.world.guide_target(c()) == str(first.target_room)),
			"story guidance: right after the sect choice its first quest leads the tracker with its target and the mark (%s)" % str(first))
		_sect_chosen = ""

## Decision 41: the story's next quest (the first of the story waiting, what holds it followed back) is played past the
## prototype's gate: its own room, or every room its giver stands in, has no top-down layout yet.
func _story_past_gate() -> bool:
	var waiting: Array = Game.quest.story_waiting(c(), QuestAuthority.STORY_KINDS)
	if waiting.is_empty(): return false
	var first: Dictionary = waiting[0]
	for r in first.get("requires", {}).get("all", []):
		var sub := ContentDB.entry("quests", str(r.get("quest", ""))) if str(r.get("kind", "")) == "quest_done" else {}
		if not sub.is_empty() and not c().quests.is_done(str(sub.id)): first = sub
	return Game.quest.beyond_prototype(c(), first)

## The character can walk there from where it stands: a route through the ways open to it, or as far as the room that
## hides the way (Spirit Sense shows it there); a story instance entered by its event counts as there.
func _walks_to_room(target: String) -> bool:
	var here := room()
	if target == here or ContentDB.room(target).get("instanced", false) or Game.room_rt.def.get("crossing", false): return true
	if not Game.world.route(c(), here, target).is_empty(): return true
	return WorldRules.rooms_with("hidden_to=" + target).any(func(h): return str(h) == here or not Game.world.route(c(), here, str(h)).is_empty())

func c():
	return Game.active()

func room() -> String:
	return Game.room_rt.room_id if Game.room_rt else ""

## Put the player's movement state at a ground point in the loaded room.
func place(p: Vector2, alt := 0.0) -> void:
	if st == null:
		st = ActorState.new()
		Game.bind_movement(Game.active_id, st)
	if _clock_room == room(): play_s += st.plane.distance_to(p) / WALK_SPEED   # walking here in the same room
	_clock_room = room()
	if not _rooms_seen.has(room()):
		_rooms_seen[room()] = true
		play_s += LOOK_S
	var best: WalkSurface = null
	for s in Game.room_rt.geometry.surfaces:
		if s.contains(p) and absf(s.height_at(p) - alt) < 10.0: best = s
	if best == null:
		for s in Game.room_rt.geometry.surfaces:
			if s.stratum == "ground" and s.contains(p): best = s
	st.surface = best
	st.plane = p
	st.altitude = best.height_at(p) if best else alt
	st.velocity = Vector2.ZERO
	var grid: TopdownRoom = Game.room_rt.topdown
	if grid != null:
		# On the height grid (redesign Phase 4, a top-down character): a spot a body can stand on, at its floor's height.
		st.plane = grid.nearest_standable(p)
		st.altitude = grid.floor_at(st.plane)

## Stand beside a thing to reach it: `off` from it in the side view (at `side_alt`); on the height grid the nearest
## spot at the thing's own height (TopdownRoom.spot_near).
func stand_by(o: Dictionary, off: Vector2, side_alt: float) -> void:
	var at := Vector2(float(o.at[0]), float(o.at[1]))
	var grid: TopdownRoom = Game.room_rt.topdown
	if grid != null: place(grid.spot_near(at, float(o.get("alt", 0.0)), at + off), float(o.get("alt", 0.0)))
	else: place(at + off, side_alt)

func obj_at(id: String) -> Vector2:
	var o: Dictionary = Game.room_rt.object_def(id)
	if o.is_empty():
		print("  no object ", id, " in ", room())
		return Vector2.ZERO
	return Vector2(float(o.at[0]), float(o.at[1]))

func go(portal: String) -> bool:
	var pd: Dictionary = Game.room_rt.portal_def(portal) if Game.room_rt else {}
	if st != null and pd.has("at"): play_s += st.plane.distance_to(Vector2(float(pd.at[0]), float(pd.at[1]))) / WALK_SPEED
	var r := submit({"type": "use_portal", "portal": portal, "crossing": true})
	if not r.get("ok", false): print("  portal ", portal, " in ", room(), " failed: ", r)
	if r.get("ok", false): place(Vector2(float(c().position.x), float(c().position.y)))
	return r.get("ok", false)

## Every room the character can walk to now through open portals, breadth-first from here: room -> [from room, portal].
func routes() -> Dictionary:
	var prev := {room(): ["", ""]}
	var queue := [room()]
	while not queue.is_empty():
		var r: String = queue.pop_front()
		for p in ContentDB.room(r).get("portals", []):
			var to := str(p.get("to", ""))
			if to == "" or prev.has(to) or ContentDB.room(to).is_empty() or ContentDB.room(to).get("instanced", false): continue
			if p.has("requires") and not RequirementRules.passes(p.requires, Game.ctx()): continue
			if Game.world.prototype_gate(c(), r, to): continue   # decision 41: a top-down character's gate at the prototype's end
			prev[to] = [r, str(p.id)]
			queue.append(to)
	return prev

## Walk to a room through open portals (breadth-first over the room graph).
func travel(target: String) -> bool:
	if room() == target: return true
	var prev := routes()
	if not prev.has(target): return false
	var path: Array = []
	var cur := target
	while cur != room():
		path.push_front(prev[cur][1])
		cur = prev[cur][0]
	for portal in path:
		if not go(portal): return false
	return room() == target

func npc_object(npc: String) -> Dictionary:
	for o in Game.room_rt.def.get("objects", []):
		if o.type == "npc" and str(o.npc) == npc and Game.world.object_visible(c(), o): return o
	return {}

func talk(npc: String) -> Dictionary:
	var o := npc_object(npc)
	if o.is_empty():
		print("  no visible npc ", npc, " in ", room())
		return {}
	stand_by(o, Vector2(-50, 20), 0.0)
	var r := submit({"type": "interact", "object": str(o.id)})
	play_s += READ_S * maxf(1.0, float((r.get("dialogue", {}).get("lines", []) as Array).size()))
	return r.get("dialogue", {})

## Talk and pick the first choice that has `key` (accept/hand_in/effects...).
func talk_choose(npc: String, key: String, value := "") -> bool:
	var d := talk(npc)
	for ch in d.get("choices", []):
		if ch.has(key) and (value == "" or str(ch.get(key)) == value or str(ch.get("text", "")).contains(value)):
			var r := submit({"type": "choose_dialogue", "npc": npc, "choice": ch})
			return r.get("ok", false)
	print("  ", npc, " offered no '", key, "' choice: ", d.get("lines", []), " ", d.get("choices", []))
	return false

func accept(npc: String, quest: String) -> void:
	var ok := talk_choose(npc, "accept", quest)
	check(ok and c().quests.is_active(quest), "accept %s from %s" % [quest, npc])

func hand_in(npc: String, quest: String) -> void:
	var ok := talk_choose(npc, "hand_in", quest)
	check(ok and c().quests.is_done(quest), "hand in %s to %s" % [quest, npc])

## The nearest point off shallow water, a step away from a foe (S43 volumes; on the height grid, any floor).
func _dry_ground_near(p: Vector2) -> Vector2:
	if Game.room_rt.topdown != null: return Game.room_rt.topdown.nearest_standable(p + Vector2(-34, -60))
	var geo: ZoneGeometry = Game.room_rt.geometry
	for dy in [-60, -100, -140, -180, -220, 60, 100]:
		var q := Vector2(p.x - 34.0, p.y + dy)
		if geo.volume_at(q, 0.0, "water_shallow").is_empty() and geo.volume_at(q, 0.0, "water_deep").is_empty() and geo.ground_contains(q) and not geo.blocks_at(q, 0.0, "ground"):
			return q
	return p + Vector2(-34, 0)

func interact(id: String) -> Dictionary:
	var o: Dictionary = Game.room_rt.object_def(id)
	if o.is_empty(): return {"ok": false, "reason": "no_object", "text": "no %s in %s" % [id, room()]}
	stand_by(o, Vector2(-30, 10), float(o.get("alt", 0.0)))
	play_s += USE_S
	return submit({"type": "interact", "object": id})

func hit_object(id: String, times: int) -> void:
	var o: Dictionary = Game.room_rt.object_def(id)
	stand_by(o, Vector2(-30, 10), float(o.get("alt", 0.0)))
	play_s += HIT_S * times
	for i in times: Game.world.apply_object_hit(c().id, o)
	GameEvents.flush()

## Where a blow at a foe standing at `p` aims: on the height grid the stick points at it, as a player's thumb does (the
## top-down view turns the body to the stick; the walk has no view, so it says so in the intent); none in the side
## view, where the facing is enough.
func aim_at(p: Vector2) -> Vector2:
	if Game.room_rt == null or Game.room_rt.topdown == null or st == null or p.distance_to(st.plane) <= 0.5: return Vector2.ZERO
	return (p - st.plane).normalized()

## Fight `count` enemies of one kind with the basic combo, standing beside each.
## `careful` = false plays like a new player: no resting before a fight and no stepping out of wind-ups.
func fight(def_id: String, count: int, limit_s := 240.0, retreat_below := 0.0, allow_elite := false, careful := true) -> int:
	var tally := {"killed": 0, "attacker": 0}
	var t := 0.0
	var heard := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("def", "")) == def_id: tally.killed += 1
		if n == "hit_landed" and str(p.get("target_kind", "")) == "player" and str(p.get("attacker", "")).is_valid_int(): tally.attacker = int(str(p.attacker))
		if verbose and n == "hit_landed" and str(p.get("target_kind", "")) == "player":
			var att = Game.room_rt.enemies.get(int(str(p.get("attacker", "0")))) if str(p.get("attacker", "")).is_valid_int() else null
			print("    hit by ", att.def_id if att else p.get("attacker"), " for ", p.amount, " hp ", c().pools.hp)
		if verbose and n == "player_gravely_wounded": print("    WOUNDED ", p)
		if verbose and n in ["hit_missed", "attack_whiffed", "hit_immune"] and str(p.get("attacker", p.get("actor", ""))).begins_with("c"): print("    ", n)
	GameEvents.event.connect(heard)
	var target: EnemyState = null
	while int(tally.killed) < count and t < limit_s:
		# Keep one target until it falls; prefer anything already attacking us.
		# Whatever keeps hitting us (a ranged thrower, say) comes first.
		var hitter: EnemyState = Game.room_rt.enemies.get(int(tally.attacker)) if int(tally.attacker) != 0 else null
		# ...except during a boss fight: focus the boss and let companions handle its summons.
		var on_boss: bool = target != null and target.alive and target.def_id == def_id and target.role in ["dungeon_boss", "field_boss", "story_boss", "elite"]
		# ...unless a summoned add is wearing us down: a careful player clears it first.
		var add_first: bool = hitter != null and hitter.summoned and c().pools.hp < c().pools.max_hp * 0.6
		if hitter != null and hitter.alive and hitter.team != "ally" and hitter != target and (not on_boss or add_first):
			target = hitter
			tally.attacker = 0
		if target == null or not target.alive or not Game.room_rt.enemies.has(target.uid):
			target = null
			for e in Game.room_rt.living_enemies():
				if e.team != "ally" and str(e.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"] and st != null and e.plane.distance_to(st.plane) < 160.0:
					target = e
			if target == null:
				for e in Game.room_rt.living_enemies():
					if e.def_id == def_id and e.team != "ally" and (allow_elite or not e.elite or str(e.def.get("role", "")) == "elite"):
						if target == null or st == null or e.plane.distance_to(st.plane) < target.plane.distance_to(st.plane): target = e
		if target == null:
			step(0.5)
			t += 0.5
			continue
		# Rest before engaging a new target when hurt, like a careful player.
		if careful and c().pools.hp < c().pools.max_hp * 0.8 and target.pools.hp >= target.pools.max_hp and str(target.ai.get("state", "")) in ["idle", "patrol", "return"]:
			var rt := 0.0
			place(target.spawn_point + Vector2(-420, 0) if target.spawn_point.x > 500 else target.spawn_point + Vector2(420, 0))
			while c().pools.hp < c().pools.max_hp * 0.95 and rt < 90.0:
				step(1.0)
				rt += 1.0
		# Bosses: roll through the strike late in its wind-up (dash i-frames), as a practised player does.
		if str(target.ai.get("state", "")) == "windup" and target.role in ["dungeon_boss", "field_boss", "story_boss"] and Unlocks.is_unlocked(c().id, "dodge_dash"):
			if float(target.ai.get("timer", 1.0)) <= 0.2:
				var dr := submit({"type": "dodge", "direction": Vector2.ZERO, "facing": 1})
				# No dodging in shallow water (S43): a practised player steps up onto dry ground instead.
				if str(dr.get("reason", "")) == "in_water": place(_dry_ground_near(target.plane))
			step(0.05)
			t += 0.05
			continue
		# Read the tell: step out of the lane during a wind-up, as the Snapper lesson teaches.
		if careful and str(target.ai.get("state", "")) == "windup" and (target.role != "normal" or target.elite):
			place(target.plane + Vector2(-34, 70 if target.plane.y < 860 else -70))
			step(0.7)
			t += 0.7
			continue
		# Guard-and-counter foes block until they have countered: strike during recovery.
		if str(target.def.get("ai", {}).get("profile", "")) == "guard_counter" and str(target.ai.get("state", "")) in ["windup", "attack"]:
			# Step out of the counter, then punish its recovery.
			place(target.plane + Vector2(-80 if st == null or st.plane.x <= target.plane.x else 80, 0))
			step(0.1)
			t += 0.1
			continue
		var side := -34.0 if st == null or st.plane.x <= target.plane.x else 34.0
		place(target.plane + Vector2(side, 0))
		# On the height grid a player stands beside the foe on its own floor: not up a flight of stairs or a ledge beside
		# it (a tree, a rock or a hedge beside the foe can put the first spot there).
		if Game.room_rt.topdown != null and absf(st.altitude - target.altitude) > 8.0:
			for off in [Vector2(-side, 0), Vector2(0, 34), Vector2(0, -34)]:
				place(target.plane + off)
				if absf(st.altitude - target.altitude) <= 8.0: break
		var hp_before := target.pools.hp
		if Game.combat.is_wounded(c().id):
			var here := room()
			# A Revival Talisman brings you back on the spot, so a boss keeps its wounds.
			if c().inventory.count("revival_talisman") > 0 and submit({"type": "choose_revival", "where": "here"}).get("ok", false):
				target = null
				continue
			submit({"type": "choose_revival", "where": "shrine"})
			place(Vector2(float(c().position.x), float(c().position.y)))
			step(1.0)
			if verbose: print("  revived at ", room(), "; walking back to ", here)
			var rest_t := 0.0
			while c().pools.hp < c().pools.max_hp * 0.95 and rest_t < 120.0:
				step(1.0)
				rest_t += 1.0
			if verbose: print("  after rest ", rest_t, "s: hp ", snappedf(c().pools.hp, 0.1), "/", snappedf(c().pools.max_hp, 0.1), " injuries ", c().cultivator.injuries, " wounded ", Game.combat.is_wounded(c().id), " statuses ", c().pools.statuses)
			travel(here)
			target = null
			continue
		# Techniques on cooldown first (a player spends Qi), then the basic combo.
		var aim_v := aim_at(target.plane)
		for slot_i in ProgressionRules.technique_slot_count(c()):
			if c().cultivator.technique_slots[slot_i] != null and str(c().cultivator.technique_slots[slot_i]) != "":
				if submit({"type": "use_technique", "slot": slot_i, "facing": 1 if target.plane.x >= st.plane.x else -1, "aim": aim_v}).get("ok", false): break
		var ar := submit({"type": "basic_attack", "facing": 1 if target.plane.x >= st.plane.x else -1, "aim": aim_v})
		if verbose and allow_elite and OS.get_cmdline_user_args().has("--trace") and int(t * 10) % 300 == 0:
			print("    [%ds] %s hp %d  me %d/%d  atk %.0f  injuries %s  statuses %s  target %s" % [int(t), def_id, int(target.pools.hp), int(c().pools.hp), int(c().pools.max_hp), c().stats.value("physical_attack"), str(c().cultivator.injuries.keys()), str(c().pools.statuses.map(func(x): return x.id)), target.def_id])
		step(0.2)
		t += 0.2
		if verbose and (t < 3.0 or def_id == "trial_puppet") and int(tally.killed) == 0: print("  attack ", def_id, " ", ar, " hp ", hp_before, " -> ", target.pools.hp, " me ", c().pools.hp, " at ", st.plane, " alt ", st.altitude, " surf ", st.surface.id if st.surface else "-", " vs ", target.plane, " ealt ", target.altitude, " st ", target.ai.get("state", ""))
		if c().pools.hp < c().pools.max_hp * 0.4 and Unlocks.is_unlocked(c().id, "quick_use"):
			for heal in ["healing_pill", "herbal_tea"]:
				if c().inventory.count(heal) > 0:
					var hr := submit({"type": "use_item", "index": c().inventory.first_index(heal), "confirm": true})
					if hr.get("ok", false): break
		elif retreat_below > 0.0 and c().pools.hp < c().pools.max_hp * retreat_below:
			break
	GameEvents.event.disconnect(heard)
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	if verbose: print("  fight ", def_id, ": killed ", tally.killed, " in ", snappedf(t, 0.1), "s, hp ", snappedf(c().pools.hp, 0.1))
	return int(tally.killed)

# ------------------------------------------------------------------ the dialogue page
## Open a conversation on the real dialogue page and tap through it to its last line (or until it closes).
func _page(convo: Dictionary) -> Dictionary:
	var out := {"page": load(str(load("res://scripts/main.gd").PAGES.dialogue)).new(), "closed": false}
	out.page.closed.connect(func(_p): out.closed = true)
	add_child(out.page)
	out.page.open({"convo": convo})
	for i in 20:
		if out.closed or (out.page.at_end() and out.page.shown_chars >= out.page.current().length() and not (out.page.convo.get("choices", []) as Array).is_empty()): break
		out.page.on_action("advance", null)
		play_s += TAP_S   # a tap: the rest of a line, or the next
	return out

## Talk to an NPC by the context button on the real dialogue page, tap to the last line and pick the choice that does
## `key` (accept or hand_in) for a quest. True when it took, and the page then closed itself or went on to the same
## person's next quest to take or hand in (M17): after taking a quest nobody has to tap "Farewell", and a trade, a gift
## or a farewell alone never keeps the conversation open.
func _choose_on_page(npc: String, key: String, qid: String) -> bool:
	var talk := interact(str(npc_object(npc).get("id", "")))
	var on := _page(talk.get("dialogue", {}))
	var before: Dictionary = on.page.convo
	var choices: Array = before.get("choices", [])
	for i in choices.size():
		if str(choices[i].get(key, "")) == qid and not on.closed: on.page.on_action("choose", i)
	var now: Dictionary = on.page.convo
	var went_on: bool = not on.closed and now != before and now.has("quest")
	on.page.queue_free()
	story_guidance()
	var took: bool = (c().quests.is_active(qid) or c().quests.is_done(qid)) if key == "accept" else c().quests.is_done(qid)
	if verbose: print("  %s %s on the page: %s" % [key, qid, "closed itself" if on.closed else ("went on to %s" % now.get("quest", "") if went_on else "left open")])
	return took and (on.closed or went_on)

# ------------------------------------------------------------------ the steps
## A save folder's files copied over another's (the runs' checkpoints).
func _copy_dir(from: String, to: String) -> void:
	DirAccess.make_dir_recursive_absolute(to)
	for f in DirAccess.get_files_at(to): DirAccess.remove_absolute(to + f)
	for f in DirAccess.get_files_at(from): DirAccess.copy_absolute(from + f, to + f)

## Each step starts where its quest giver stands; a step taken in another order may start elsewhere.
func back_to(target: String) -> void:
	if room() != target: travel(target)

## A new character in the Fisher's Hut, on a fixed seed (every run plays the same dice).
func start_new(folder: String) -> void:
	folder = run_root() + folder
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Clock.simulate(START_UTC)
	Game.boot()
	Game.autosave_enabled = false
	# A fixed seed: every run of the suite plays the same dice (character streams derive from it).
	Game.account.rng_seed = RUN_SEED
	Rng.restore("account", {}, RUN_SEED)
	GameEvents.event.connect(func(n, p):
		if n == "hud_element_revealed": reveal_log.append(str(p.element))
		if n in ["quest_accepted", "quest_completed", "system_unlocked", "realm_changed", "room_entered", "quest_failed"]: events.append([n, p]))
	var made := {"type": "create_character", "slot": 1, "name": "Tester", "appearance": {"hair": "topknot"}}
	made.merge(create_extra)
	var r := submit(made)
	check(r.ok, "create character")
	check(submit({"type": "enter_character", "slot": 1}).ok, "enter character")
	check(submit({"type": "enter_world"}).ok and room() == "lf_fishers_hut", "starts in the Fisher's Hut")
	place(Vector2(float(c().position.x), float(c().position.y)))   # where the character woke
	check(c().pools.max_qi == 0.0, "no QI pool before cultivation")
	check(c().inventory.equipped.get("weapon") == null, "no weapon at start")
	check(not Game.is_revealed("hud:attack") and not Game.is_revealed("hud:qi_bar"), "attack and QI hidden at start")

## 1 Morning Tide (research player_motivation §3.3): under way the moment the character wakes, Aunt Ping's tea already
## in hand and the hut's door open: no step before the way out, no door shut for a menu. A second cup waits on the
## table for whoever looks.
func step_morning_tide() -> void:
	check(c().quests.is_active("morning_tide"), "Morning Tide is under way from the start")
	check(c().inventory.count("herbal_tea") >= 1, "Aunt Ping's tea is in hand from the start (%d)" % c().inventory.count("herbal_tea"))
	check(Game.is_revealed("hud:bag"), "Bag revealed with Morning Tide")
	check(Game.world.portal_state(c(), Game.room_rt.portal_def("exit")).open, "the hut's door is open from the start")
	# The hut must show its way out and its tea plainly (a player stuck in the hut could not see the door, and took
	# the jar props for clods of earth).
	var hut: Dictionary = Game.room_rt.def
	if Game.room_rt.topdown != null:   # on the height grid: a doorway in the hut's front wall (TopdownRoom.entrance)
		check(Game.room_rt.topdown.entrance("exit") == "wall", "the hut's exit is a doorway in its front wall (%s)" % Game.room_rt.topdown.entrance("exit"))
	else:
		var exit_view := PortalView.new()
		exit_view.setup(Game.room_rt.portal_def("exit"), hut)
		check(exit_view.wall_y != INF and not SpriteCache.prop("door").is_empty(), "the hut's exit draws a door on the back wall")
		exit_view.free()
	for o in hut.get("objects", []):
		if str(o.get("item", "")) == "herbal_tea" and Game.world.object_visible(c(), o):
			check(str(o.get("prop", "")) == "none" and SpriteCache.icon("herbal_tea") != null, "tea %s shows as its icon" % o.id)
	talk("aunt_ping")   # a word with Aunt Ping on the way out, as a player does
	check(interact("tea_table").get("ok", false) and c().inventory.count("herbal_tea") == 2, "the second cup on the table is there to take")
	keep("Morning Tide")
	check(go("exit") and room() == "lf_village", "step out to Home Lane")
	check(c().quests.is_done("morning_tide"), "Morning Tide completes on stepping outside")
	check(c().quests.is_active("a_quiet_river"), "A Quiet River follows automatically")
	check(Game.is_revealed("hud:minimap") and Game.is_revealed("hud:quest_tracker"), "minimap and tracker revealed")

## 2 A Quiet River: Lu at the docks sends you round the village.
func step_quiet_river() -> void:
	talk("lu_boatman")
	hand_in("lu_boatman", "a_quiet_river")

## 3 The Runaway Kite: a jump from the hall roof to the inn.
func step_kite() -> void:
	back_to("lf_village")
	accept("little_dou", "the_runaway_kite")
	check(Game.is_revealed("hud:jump"), "Jump revealed")
	check(interact("kite").get("ok", false), "take the kite from the inn roof")
	hand_in("little_dou", "the_runaway_kite")

## 5 Granny's Remedy (in the herb hut): the quick-use slot, a tea, the shrine.
func step_granny() -> void:
	back_to("lf_village")
	check(go("granny_door"), "enter Granny Liu's hut")
	accept("granny_liu", "grannys_remedy")
	check(Game.is_revealed("hud:hp_bar") and Game.is_revealed("hud:quick_use"), "HP bar and quick-use revealed")
	keep("Granny's Remedy taken")
	submit({"type": "set_quick_use", "item": "herbal_tea"})
	var q := submit({"type": "use_quick"})
	if not q.ok and q.get("reason", "") == "confirm": q = submit({"type": "use_item", "index": c().inventory.first_index("herbal_tea"), "confirm": true})
	check(interact("shrine_granny").get("ok", false), "pray at the shrine")
	hand_in("granny_liu", "grannys_remedy")
	check(go("exit"), "back to the village")

## 4 Ma's Delivery: sell the old net (one step); two rice balls bought as a player might, not asked for.
func step_ma() -> void:
	back_to("lf_village")
	check(go("store_door"), "enter Old Ma's store")
	accept("old_ma", "mas_delivery")
	check(Game.is_revealed("hud:currency"), "currency revealed")
	check(interact("old_net_floor").get("ok", false), "find the Old Net under the storeroom shelf")
	var net = c().inventory.first_index("old_net")
	check(net >= 0 and submit({"type": "sell", "index": net, "count": 1}).ok, "sell the old net")
	var buy := submit({"type": "buy", "shop": "old_ma", "item": "rice_ball", "count": 2})
	check(buy.ok, "buy two rice balls %s (taels %d)" % [str(buy), Game.economy.balance("silver_tael", c())])
	hand_in("old_ma", "mas_delivery")
	check(go("exit"), "leave the store")

## 7 Fists First: the stump and the dummy.
func step_fists() -> void:
	back_to("lf_village")
	accept("uncle_guo", "fists_first")
	check(Game.is_revealed("hud:attack"), "Attack revealed")
	hit_object("stump_guo", 5)
	hit_object("dummy_guo", 3)
	hand_in("uncle_guo", "fists_first")
	var worn = c().inventory.equipped.get("weapon")
	check(worn != null and str(worn.id) == "training_gauntlets", "Fists First hands out the training gauntlets, worn at once (%s)" % str(worn))
	check(not Game.world.portal_state(c(), Game.room_rt.portal_def("east_gate")).open or c().quests.is_active("crab_trouble"),
		"the East Gate stays shut after Fists First until Guo sends you to the crabs")

## 6 Race to the Tower (optional; fail once, then win).
func step_race() -> void:
	back_to("lf_village")
	accept("shen_lian_npc", "race_to_the_tower")
	step(26.0)
	check(not c().quests.is_active("race_to_the_tower"), "race fails when time runs out")
	accept("shen_lian_npc", "race_to_the_tower")
	check(interact("tower_bell").get("ok", false), "ring the tower bell")
	hand_in("shen_lian_npc", "race_to_the_tower")
	check(c().cultivator.titles.has("fleet_footed"), "title Fleet-Footed earned")

## 9 Crab Trouble: the four lessons done, Guo has it at once (no walk back to Lu); the East Gate opens, three shells,
## which drop while he wants them, and Old Snapper in the Reed Shallows.
func step_crabs() -> void:
	back_to("lf_village")
	check(c().quests.offered.has("crab_trouble") and Game.quest.npc_marker(c(), "uncle_guo") == "main",
		"with the fourth lesson done Guo offers Crab Trouble (marker %s)" % Game.quest.npc_marker(c(), "uncle_guo"))
	accept("uncle_guo", "crab_trouble")
	check(Game.is_revealed("hud:enemy_hp_bars") and Game.is_revealed("hud:system_log"), "enemy HP bars and log revealed")
	check(go("east_gate") and room() == "lf_reed_shallows", "the East Gate opens with Crab Trouble")
	keep("Crab Trouble taken")
	# The first kill in the first rooms drops the character's first weapon (grades.json drop.starter), marked for its
	# moment (the first-weapon strip and beam), and it is picked up.
	var first := {"kills": 0, "at": -1, "item": ""}
	var seen := func(n: String, p: Dictionary):
		if n == "actor_defeated" and str(p.get("victim_kind", "")) == "enemy": first.kills += 1
		if n == "loot_dropped" and p.get("first_weapon", false) and int(first.at) < 0:
			first.at = int(first.kills)
			first.item = str((p.items as Array).filter(func(i): return i.get("first", false))[0].item)
	GameEvents.event.connect(seen)
	var guard := 0
	while c().inventory.count("crab_shell") < 3 and guard < 30:
		fight("mudshell_crab", 1, 30.0)
		step(0.6)
		for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
		guard += 1
	GameEvents.event.disconnect(seen)
	var fam := str(LootRules.drop_cfg().get("starter", {}).get("first_family", ""))
	check(int(first.at) == 1 and str(ContentDB.item(str(first.item)).get("family", "")) == fam and c().inventory.count(str(first.item)) >= 1,
		"the first kill in the Reed Shallows drops the first weapon, a %s, picked up (%s)" % [fam, str(first)])
	check(c().inventory.count("crab_shell") >= 3 and guard <= 3, "three crab shells from three crabs (have %d after %d fights)" % [c().inventory.count("crab_shell"), guard])
	step(1.5)
	# The first elite is beaten by a player who neither rests first nor reads its claw; reading it only makes it easy.
	check(fight("old_snapper", 1, 120.0, 0.0, false, false) == 1, "Old Snapper defeated without resting or dodging (hp %d/%d)" % [int(c().pools.hp), int(c().pools.max_hp)])
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	check(travel("lf_village"), "back to the village")
	var sandals: int = c().inventory.count_including_equipped("straw_sandals")
	hand_in("uncle_guo", "crab_trouble")
	# Paid in what the player does not have yet: the hat, and Ping's bone broth (the starting kit wears Straw Sandals, so
	# no second pair; the prototype's polish).
	check(c().inventory.count_including_equipped("plain_straw_hat") >= 1 and c().inventory.count("boar_bone_broth") >= 1
		and c().inventory.count_including_equipped("straw_sandals") == sandals,
		"Plain Straw Hat and a Boar Bone Broth received, and no second pair of Straw Sandals (%d)" % c().inventory.count_including_equipped("straw_sandals"))

## 10 Evening on the River: dinner, the docks at sunset, and the night falls.
func step_evening() -> void:
	accept("lu_boatman", "evening_on_the_river")
	check(Game.is_revealed("hud:menu"), "Menu revealed")
	talk("aunt_ping")
	talk("lu_boatman")
	check(room() == "lf_village_night", "the night falls (room %s)" % room())
	check(c().quests.is_active("the_hollow_night"), "The Hollow Night begins")

## P4 The night: three villagers to the hut, then hold out until Lu comes.
func step_night() -> void:
	for npc in ["little_dou", "granny_liu", "old_ma"]:
		talk_choose(npc, "effects")
	check(c().quests.has_flag("dou_safe") and c().quests.has_flag("granny_safe") and c().quests.has_flag("ma_safe"), "villagers guided to the hut")
	place(obj_at("hut_refuge") + Vector2(14, -4))   # at the hut's door
	step(62.0)
	check(c().quests.has_flag("night_survived"), "survived the night")
	check(room() == "lf_lu_boat", "carried to Lu's boat (room %s)" % room())

## P5 Lu's Boat: the first breakthrough.
func step_river_token() -> void:
	check(c().quests.is_active("the_river_token"), "The River Token begins")
	check(Game.is_revealed("hud:cultivate") and Game.is_revealed("hud:progress_bar"), "Cultivate and progress bar revealed")
	check(c().cultivator.methods_known.has("riverbreath_fragment"), "Riverbreath method learned")
	place(obj_at("boat_spring") + Vector2(0, -10))   # at the spring on the deck
	submit({"type": "start_meditation"})
	var med := 0.0
	while c().cultivator.state != "bottleneck" and med < 600.0:
		step(1.0)
		med += 1.0
	submit({"type": "stop_meditation"})
	check(c().cultivator.state == "bottleneck", "progress bar full after %ds of meditation" % int(med))
	submit({"type": "report_page_opened", "page": "cultivation"})
	var b := submit({"type": "start_breakthrough", "support_items": []})
	check(b.ok, "start the first breakthrough %s" % str(b))
	step(4.0)
	check(c().cultivator.realm_key == "bone_forging_1", "Bone Forging 1 (realm %s)" % c().cultivator.realm_key)
	hand_in("lu_boatman", "the_river_token")
	# Research §5 change 3: Lu teaches the first technique with the first breakthrough, in its slot, costing no Qi.
	check(c().cultivator.techniques_known.has("flowing_palm") and c().cultivator.technique_slots[0] == "flowing_palm" and Game.is_revealed("hud:skills"),
		"Lu teaches Flowing Palm at Bone Forging 1, slotted on the skill ring (%s)" % str(c().cultivator.technique_slots))
	check(Game.combat.technique_cost(c(), ContentDB.entry("techniques", "flowing_palm")) == 0.0, "in the body stages Flowing Palm costs no Qi")
	check(c().pools.max_qi == 0.0, "still no QI pool in the body stages")
	check(not Game.is_revealed("hud:qi_bar"), "QI bar still hidden at Bone Forging 1")

## P6 The Willow Path: the shrine, the stump and five Wild Boarlets.
func step_willow_path() -> void:
	check(c().quests.is_active("the_willow_path"), "The Willow Path begins at Bone Forging 1")
	check(Unlocks.is_unlocked(c().id, "mail") and Unlocks.is_unlocked(c().id, "kill_progress"), "mail and kill progress unlocked")
	check(go("deck") and go("west_gate") and room() == "wp_east", "West Gate open after the night")
	check(go("west") and room() == "wp_west", "Willow Path West")
	check(interact("shrine_wp").get("ok", false), "pray at the Willow Path shrine")
	var palm := {"n": 0}
	var cast := func(n, p): if n == "technique_used" and str(p.get("technique", "")) == "flowing_palm": palm.n += 1
	GameEvents.event.connect(cast)
	check(fight("wild_boarlet", 5, 200.0) >= 5, "five Wild Boarlets")
	var tries := 0
	while c().quests.is_active("the_willow_path") and tries < 6:
		fight("wild_boarlet", 1, 120.0, 0.0, true)
		tries += 1
	GameEvents.event.disconnect(cast)
	check(int(palm.n) > 0, "Flowing Palm is cast on the boarlets, with no Qi pool (%d casts)" % int(palm.n))
	check(c().quests.is_done("the_willow_path"), "The Willow Path complete: no stump quota, the palm, five boarlets and the herd's elite")

## The sects a player can join at the fair, and where each one's early story stands: its recruiter, its Entry Trial's
## way and room, its gate (the steward's chores), its Weapon Hall and weapon master, and the mentor on his peak. The
## walk joins `sect` (Jade; topdown_tutorial plays the Cloud Sect's stretch too).
const SECTS := {
	"jade": {"id": "jade_sect", "recruiter": "recruiter_qing_lan", "trial": "trial_jade", "trial_room": "sf_trial_jade",
		"gate": "ja_gate_street", "steward": "jade_steward", "weapon_hall": "ja_weapon_hall", "weapon_master": "jade_weapon_master",
		"mentor": "elder_hu", "peak": "ja_elder_hu_peak"},
	"cloud": {"id": "cloud_sect", "recruiter": "recruiter_mo_yun", "trial": "trial_cloud", "trial_room": "sf_trial_cloud",
		"gate": "cm_cliff_stair", "steward": "cloud_steward", "weapon_hall": "cm_weapon_hall", "weapon_master": "cloud_weapon_master",
		"mentor": "elder_sung", "peak": "cm_elder_sung_peak"}}
var sect := "jade"

## Where the sect the walk joins keeps `what` (SECTS).
func sect_at(what: String) -> String:
	return str(SECTS[sect][what])

## P7 Stoneford and the Recruitment Fair: both recruiters, then the sect.
func step_fair() -> void:
	check(go("west") and go("west") and go("west") and go("west") and room() == "sf_fairground", "walk to the Fairground (room %s)" % room())
	check(c().quests.is_active("the_recruitment_fair") or c().quests.offered.has("the_recruitment_fair"), "Recruitment Fair offered")
	accept("recruiter_qing_lan", "the_recruitment_fair")
	talk("recruiter_mo_yun")
	keep("Both recruiters met")
	join_sect()

## Join `sect` with its recruiter's Join choice; the membership is recorded and the fair is done.
func join_sect() -> void:
	check(talk_choose(sect_at("recruiter"), "effects", "Join"), "join the %s" % sect_at("id"))
	check(str(c().training_sect.get("id", "")) == sect_at("id"), "member of the %s (%s)" % [sect_at("id"), str(c().training_sect)])
	check(c().quests.is_done("the_recruitment_fair"), "Recruitment Fair complete")

## A realm step the story has filled: break through when the bar is full, as the HUD asks. True once at `realm`.
func break_through(realm: String) -> bool:
	for i in 3:
		if ProgressionRules.at_least(c().cultivator.realm_key, realm): break
		if c().cultivator.state != "bottleneck": break
		submit({"type": "start_breakthrough", "support_items": []})
		step(4.0)
	return ProgressionRules.at_least(c().cultivator.realm_key, realm)

## P8 The Entry Trial: the bell, then the Trial Puppet; no realm step to grind for. The story's own quests and fights
## (the Willow Path, the fair, the trial) carry the character to Bone Forging 2 (research §5 change 5).
func step_entry_trial() -> void:
	if room() != "sf_fairground": check(travel("sf_fairground"), "return to the Fairground")
	check(c().quests.is_active("entry_trial"), "Entry Trial active")
	check(go(sect_at("trial")) and room() == sect_at("trial_room"), "enter the sect's trial ground (room %s)" % room())
	check(interact("trial_bell").get("ok", false), "reach the trial bell")
	step(1.5)
	check(fight("trial_puppet", 1, 120.0) == 1, "Trial Puppet beaten")
	check(c().quests.is_done("entry_trial"), "Entry Trial complete")
	check(str(c().training_sect.get("rank", "")) == "service_disciple", "Service Disciple")
	check(break_through("bone_forging_2"), "the story's own quests and fights carry the character to Bone Forging 2, no hunting (realm %s, %d%%)"
		% [c().cultivator.realm_key, int(100.0 * c().cultivator.progress_fraction())])
	check(c().inventory.equipped.get("weapon") != null, "a weapon in hand through the Prologue (the weapon slot is open from the start)")

# ------------------------------------------------------------------ the run
func run() -> void:
	start_new("saves/")
	step_morning_tide()
	step_quiet_river()
	step_kite()
	step_granny()   # before Ma, so coins are tested later
	step_ma()
	step_fists()
	step_race()
	step_crabs()
	step_evening()
	step_night()
	step_river_token()
	step_willow_path()
	step_fair()
	step_entry_trial()
	# HUD reveal order (S27): each element appears exactly at its step.
	var order := ["hud:joystick", "hud:context", "hud:bag", "hud:room_banner", "hud:minimap", "hud:quest_tracker", "hud:jump"]
	var idx := -1
	var in_order := true
	for el in order:
		var i := reveal_log.find(el)
		if i < idx: in_order = false
		idx = i
	check(in_order, "HUD reveal order: %s" % str(reveal_log.slice(0, 12)))
	check(reveal_log.find("hud:attack") > reveal_log.find("hud:jump"), "Attack after Jump")
	check(reveal_log.find("hud:cultivate") > reveal_log.find("hud:menu"), "Cultivate after Menu")
	if verbose:
		for e in events: print(e)

## Spar through an npc service or a practice post until one spar ends; true when won.
func spar_with(start_intent: Callable) -> bool:
	var result := {"done": false, "won": false}
	var heard := func(n: String, p: Dictionary):
		if n == "spar_ended":
			result.done = true
			result.won = str(p.get("winner", "")) == "player"
	GameEvents.event.connect(heard)
	var r: Dictionary = start_intent.call()
	if not r.get("ok", false): print("  spar start: ", r)
	var t := 0.0
	while not result.done and t < 120.0:
		var foe: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.def.get("spar", false): foe = e
		if foe == null:
			step(0.3)
			t += 0.3
			continue
		if str(foe.ai.get("state", "")) == "windup":
			place(foe.plane + Vector2(-34, 70 if foe.plane.y < 860 else -70))
			step(0.6)
			t += 0.6
			continue
		place(foe.plane + Vector2(-34 if st.plane.x <= foe.plane.x else 34, 0))
		submit({"type": "basic_attack", "facing": 1 if foe.plane.x >= st.plane.x else -1, "aim": aim_at(foe.plane)})
		step(0.2)
		t += 0.2
	GameEvents.event.disconnect(heard)
	return bool(result.won)

## A spar offered in `npc`'s talk (Shen Lian's, an arena master's), chosen.
func _spar_service(npc: String) -> Dictionary:
	var d := talk(npc)
	for ch in d.get("choices", []):
		if ch.has("spar"): return submit({"type": "choose_dialogue", "npc": npc, "choice": ch})
	return {"ok": false, "reason": "no spar choice"}

