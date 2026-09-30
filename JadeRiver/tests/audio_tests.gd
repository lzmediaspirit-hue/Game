extends Node
## audio_tests (decision 43, the sound pass; docs/redesign/sound.md): nobody listens during the build, so this suite
## checks what can be checked without ears.
##   1. every sound id the data and the code name has a file: data/sound.json's, the moments' sound layers, the
##      director's event sounds, each literal id in an Audio call in scripts/, each room's music mood and bed; each
##      combat stem is as long as its track and shares its grid;
##   2. the buses exist under Master with its high-pass and limiter, and each Settings slider (All sound too) drives
##      its bus;
##   3. footsteps pick by surface (the tile set's marks, a prop's top, water), land on the walk and run cycles'
##      contact frames, and a sprint in the prototype room steps on its own surface at the run's cadence;
##   4. the layered hit: the weapon's transient and the struck body at once, the tail after the hit-stop, a crit's
##      accent, blows landing together merged;
##   5. the fight music: foes that stay calm or fight out of reach bring nothing; foes turning on the player bring the
##      combat stem in on the next beat; it stays while they fight and leaves on a bar a few seconds after the last
##      falls; Old Snapper brings his own theme;
##   6. the beds: each top-down room's bed, the hour's layers, the crossfade on a change; the stingers duck the music;
##   7. the voice limit holds under the fifteen-monster fight (the pool, and each rule's cap);
##   8. the living world (decision 44): every sound it can raise has a file (the critters' of the table, each work cue
##      of data/topdown/life.json, the blows, the places', the takes; every cue topdown_life.gd names is one of them); a
##      cue raised in the room plays once where it happens; takes play in turn, varied in pitch; a busy village sounds
##      at most three critters and three people at work at once, and never keeps a sound of the fight from a voice.
## Run headless:  godot --headless --path . res://tests/audio_tests.tscn

var checks := 0
var failures := 0
var main: Node

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var folder := "user://audio_test_saves/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	Unlocks.debug_force_all = true
	Game.submit({"type": "create_character", "slot": 1, "name": "Listener", "appearance": {"hair": "topknot"}})
	main.enter_world(1)
	for i in 3: await get_tree().process_frame
	_ids()
	_buses()
	_surfaces()
	main.enter_topdown_proto(false)
	for i in 3: await get_tree().process_frame
	await _feet()
	_hits()
	_fight_music()
	_beds_and_stingers()
	_life()
	await _crowd()
	main.return_to_selection()
	await get_tree().process_frame
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	print("audio_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

func _has(id: String) -> bool:
	return SoundBank.has_sound(id)

# ------------------------------------------------------------------ 1. ids
func _ids() -> void:
	var man := SoundBank.manifest()
	var missing: Array = []
	for kind in ["sfx", "music"]:
		for id in man.get(kind, {}):
			if not ResourceLoader.exists(str(man[kind][id].file)): missing.append(str(man[kind][id].file))
	check(missing.is_empty() and man.get("sfx", {}).size() > 150, "every sound in data/audio.json has its file (%d sounds, %d tracks; missing %s)" % [man.get("sfx", {}).size(), man.get("music", {}).size(), missing])
	var named: Array = SoundBank.named_ids().filter(func(id): return not _has(str(id)))
	check(named.is_empty() and SoundBank.named_ids().size() > 100, "every sound data/sound.json names exists (%d named; missing %s)" % [SoundBank.named_ids().size(), named])
	var layers: Array = []
	for row in ContentDB.config("moments").get("entries", []):
		var all: Array = row.get("layers", []).duplicate()
		for v in row.get("variants", []): all.append_array(v.get("layers", []))
		for L in all:
			if str(L.get("kind", "")) == "sound" and not _has(str(L.sfx)): layers.append(str(L.sfx))
	check(layers.is_empty(), "every moment's sound layer has a sound (missing %s)" % [layers])
	var ev: Array = Audio.EVENT_SFX.values().filter(func(id): return not _has(str(id)))
	for k in SoundBank.section("stinger_events"):
		var sid := str(SoundBank.section("stingers").get(str(SoundBank.section("stinger_events")[k]), ""))
		if not _has(sid): ev.append(k)
	for k in SoundBank.section("stingers"):
		if not _has(str(SoundBank.section("stingers")[k])): ev.append(k)
	check(ev.is_empty(), "the director's event sounds and every stinger exist (missing %s)" % [ev])
	# every literal id in an Audio call anywhere in scripts/
	var re := RegEx.new()
	re.compile("Audio\\.(play|ui|world_sound|stinger)\\(\"([a-z0-9_]+)\"")
	var in_code: Array = []
	var bad: Array = []
	for path in _scripts("res://scripts/"):
		for m in re.search_all(FileAccess.get_file_as_string(path)):
			var id := str(Audio.SFX_ALIAS.get(m.get_string(2), m.get_string(2)))
			in_code.append(id)
			if not _has(id): bad.append("%s in %s" % [id, path.get_file()])
	check(bad.is_empty() and in_code.size() > 60, "every literal sound id in the code's Audio calls exists (%d calls; missing %s)" % [in_code.size(), bad])
	# the rooms' music and beds
	var moods: Array = []
	var beds: Array = []
	for rid in ContentDB.rooms:
		var room: Dictionary = ContentDB.room(rid)
		var track := str(SoundBank.section("music").get("alias", {}).get(Audio.music_for_room(room), Audio.music_for_room(room)))
		if not man.get("music", {}).has(track): moods.append("%s:%s" % [rid, track])
		var b := SoundBank.bed(SoundBank.bed_of(rid, room))
		if b.is_empty(): beds.append(rid)
		for base in b.get("bases", []):
			if not _has(str(base[0])): beds.append("%s:%s" % [rid, base[0]])
		for role in ["day", "night"]:
			if str(b.get(role, "")) != "" and not _has(str(b[role])): beds.append("%s:%s" % [rid, b[role]])
	check(moods.is_empty() and beds.is_empty(), "every room's music mood is a track and its bed's loops exist (%d rooms; %s %s)" % [ContentDB.rooms.size(), moods, beds])
	# the combat stems: on their track's grid, as long as it
	var stems: Array = []
	var bad_stems: Array = []
	for id in man.get("music", {}):
		var e: Dictionary = man.music[id]
		if not e.has("stem"): continue
		stems.append(id)
		var s: Dictionary = man.music.get(str(e.stem), {})
		if s.is_empty() or str(s.get("stem_of", "")) != id or absf(float(s.get("loop_s", 0)) - float(e.get("loop_s", -1))) > 0.001 \
				or float(s.get("bpm", 0)) != float(e.get("bpm", -1)) or int(s.get("bar_beats", 0)) != int(e.get("bar_beats", -1)):
			bad_stems.append(id)
	check(stems.size() >= 5 and bad_stems.is_empty(), "each combat stem shares its track's grid and loop (%s; off %s)" % [stems, bad_stems])
	for boss in SoundBank.section("music").get("boss", {}).values():
		check(man.get("music", {}).has(str(boss)), "the boss theme %s exists" % boss)

func _scripts(dir: String) -> Array:
	var out: Array = []
	for f in DirAccess.get_files_at(dir):
		if str(f).ends_with(".gd"): out.append(dir + f)
	for d in DirAccess.get_directories_at(dir):
		out.append_array(_scripts(dir + d + "/"))
	return out

# ------------------------------------------------------------------ 2. buses
func _buses() -> void:
	var names: Array = []
	for i in AudioServer.bus_count: names.append(AudioServer.get_bus_name(i))
	var sends := true
	for b in ["Music", "Ambience", "SFX", "UI"]:
		var idx := AudioServer.get_bus_index(b)
		sends = sends and idx > 0 and AudioServer.get_bus_send(idx) == "Master"
	check(names[0] == "Master" and sends, "the buses Music, Ambience, SFX and UI send to Master (%s)" % [names])
	var hp := false
	var lim: AudioEffect = null
	for i in AudioServer.get_bus_effect_count(0):
		var fx := AudioServer.get_bus_effect(0, i)
		if fx is AudioEffectHighPassFilter: hp = true
		if fx is AudioEffectHardLimiter: lim = fx
	check(hp and lim != null and (lim as AudioEffectHardLimiter).ceiling_db < 0.0, "Master has its high-pass and a limiter under 0 dBFS")
	var keys := {"master": "Master", "music": "Music", "ambience": "Ambience", "sfx": "SFX", "ui": "UI"}
	var ok := true
	var seen: Array = []
	for key in keys:
		for v in [0.3, 0.9]:
			Game.submit({"type": "set_setting", "key": key, "value": v})
			GameEvents.flush()
			var got := AudioServer.get_bus_volume_db(AudioServer.get_bus_index(keys[key]))
			seen.append("%s %.1f" % [key, got])
			ok = ok and absf(got - linear_to_db(v)) < 0.01
		Game.submit({"type": "set_setting", "key": key, "value": AccountState.default_settings().get(key, 0.7)})
		GameEvents.flush()
	check(ok, "each Settings slider drives its bus, All sound the Master (%s)" % [", ".join(seen)])

# ------------------------------------------------------------------ 3. footsteps
func _surfaces() -> void:
	var ts = JSON.parse_string(FileAccess.get_file_as_string("res://data/topdown/proto_tileset.json"))
	var d := {"id": "case", "levels": ["0000000", "0000000", "00~~000", "0000000"], "paint": ["gdpwmrs", "ggggggg", "gg..ggg", "ggggggg"],
		"spawn": [0, 3], "props": [{"kind": "crates", "x": 4, "y": 3}]}
	var r := TopdownRoom.from_dict(d, ts)
	var want := {Vector2i(0, 0): "grass", Vector2i(1, 0): "dirt", Vector2i(2, 0): "stone", Vector2i(3, 0): "wood", Vector2i(4, 0): "reeds",
		Vector2i(5, 0): "stone", Vector2i(6, 0): "stone", Vector2i(2, 2): "water"}
	var got := {}
	var ok := true
	for c in want:
		var s := SoundBank.surface_at(r, (Vector2(c) + Vector2(0.5, 0.5)) * TopdownRoom.TILE, 0.0)
		got[c] = s
		ok = ok and s == want[c]
	var crate := SoundBank.surface_at(r, (Vector2(4.5, 3.5)) * TopdownRoom.TILE, TopdownRoom.LEVEL)
	check(ok and crate == "wood", "a step picks its surface: grass, dirt, paving, planks, reeds, rock and stone by their marks, water, a crate's top (%s, crate %s)" % [got, crate])
	var roof := {"id": "roof", "levels": ["00000000", "00000000", "00000000", "00000000"], "paint": ["gggggggg", "gggggggg", "gggggggg", "gggggggg"],
		"spawn": [0, 3], "props": [{"kind": "house", "x": 0, "y": 0}]}
	var rr := TopdownRoom.from_dict(roof, ts)
	check(SoundBank.surface_at(rr, Vector2(1.5, 1.5) * TopdownRoom.TILE, 2.0 * TopdownRoom.LEVEL) == "roof", "on a house's roof a step sounds on its tiles")
	var all_have := true
	for s in SoundBank.section("steps").get("surfaces", {}):
		all_have = all_have and SoundBank.steps_of(s).size() == 4 and _has(SoundBank.land_of(s))
	check(all_have, "every surface has four steps and a landing (%s)" % [SoundBank.section("steps").get("surfaces", {}).keys()])
	check(SoundBank.contact_frames("run", 8) == [0, 4] and SoundBank.contact_frames("walk", 8) == [0, 4] and SoundBank.contact_frames("run", 12) == [0, 6],
		"a foot lands on frames 0 and 4 of the eight-frame walk and run (0 and 6 of a twelve-frame cycle)")

## The player sprints over the prototype room: a step on each contact frame, on the surface under the feet.
func _feet() -> void:
	var w = main.world
	var p = w.player
	var start: float = Audio.clock
	p.motor.place(Vector2(6.5, 10.5) * 32.0)
	var n := 90
	var surfaces := {}
	for i in n:
		p.movement = Vector2.RIGHT
		surfaces[SoundBank.surface_at(w.room, p.motor.pos, p.motor.z)] = true
		await get_tree().process_frame
	p.movement = Vector2.ZERO
	var steps: Array = Audio.played("step_", start, true)   # the player's own (the room's foes walk too)
	var secs: float = Audio.clock - start
	var spec: Dictionary = TopdownFigure.spec("run")
	var expect: float = secs * float(spec.get("fps", 14.0)) / float(spec.get("frames", 8)) * 2.0
	var own := steps.filter(func(id): return surfaces.keys().any(func(s): return str(id).begins_with("step_" + str(s) + "_")))
	check(steps.size() >= 2 and absf(steps.size() - expect) <= maxf(3.0, expect * 0.35) and own.size() == steps.size(),
		"a sprint steps on the run's contact frames, on its surface (%d steps in %.2f s, the cycle gives %.1f; surfaces %s; %s)" % [steps.size(), secs, expect, surfaces.keys(), steps])

# ------------------------------------------------------------------ 4. hits
func _hits() -> void:
	var c = Game.active()
	var e: EnemyState = Game.enemies.spawn_at("mudshell_crab", main.world.player.motor.pos + Vector2(60, 0), 3)
	check(e != null, "a crab to strike")
	if e == null: return
	var tl: Dictionary = Game.combat.timeline(c.id)
	tl.family = "jian"
	tl.combo = 0
	var t0: float = Audio.clock + 0.2
	Audio.advance(0.2)
	Audio.hit({"attacker": c.id, "target": str(e.uid), "target_kind": "enemy", "x": e.plane.x, "y": e.plane.y, "weight": "light", "crit": false, "source": "basic", "element": "none"})
	var now: Array = Audio.played("", t0)
	var tail := Audio.pending.filter(func(q): return str(q.what) == "tail")
	check(now.any(func(id): return str(id).begins_with("hit_sword_")) and now.any(func(id): return str(id).begins_with("hit_on_shell_")) and tail.size() == 1,
		"a jian's blow on a crab: the sword's transient and the shell at once, the tail waiting (%s)" % [now])
	var stop := CombatFeel.hitstop_s("light")
	check(tail.size() == 1 and absf(float(tail[0].t) - stop) < 0.001, "the tail waits the blow's hit-stop (%.3f s)" % stop)
	Audio.advance(stop + 0.01)
	check(Audio.played("hit_tail_sword", t0).size() == 1, "the sword's tail rings when the hit-stop lets go")
	var t1: float = Audio.clock + 0.2
	Audio.advance(0.2)
	Audio.hit({"attacker": c.id, "target": str(e.uid), "target_kind": "enemy", "x": e.plane.x, "y": e.plane.y, "weight": "heavy", "crit": true, "source": "basic", "element": "none"})
	var merged0: int = Audio.stats.merged
	Audio.hit({"attacker": c.id, "target": str(e.uid), "target_kind": "enemy", "x": e.plane.x, "y": e.plane.y, "weight": "heavy", "crit": false, "source": "basic", "element": "none"})
	var lv: AudioStreamPlayer = Audio.last_hit_voice
	var raised: bool = lv != null and Audio.vinfo.has(lv) and lv.volume_db > float(Audio.vinfo[lv].gain) + 1.0
	check(Audio.played("hit_accent_crit", t1).size() == 1 and Audio.stats.merged > merged0 and Audio.played("hit_sword_", t1).size() == 1 and raised,
		"a crit rings its accent, and a second blow in the same instant merges into the first, a little louder")
	var t2: float = Audio.clock + 0.2
	Audio.advance(0.2)
	Audio.hit({"attacker": c.id, "target": str(e.uid), "target_kind": "enemy", "x": e.plane.x, "y": e.plane.y, "weight": "medium", "crit": false, "source": "tech:flowing_palm", "element": "water"})
	check(Audio.played("hit_el_water", t2).size() == 1, "a technique's blow sounds its element")
	tl.combo = 2
	var t3: float = Audio.clock + 0.2
	Audio.advance(0.2)
	Audio.hit({"attacker": c.id, "target": str(e.uid), "target_kind": "enemy", "x": e.plane.x, "y": e.plane.y, "weight": "heavy", "crit": false, "source": "basic", "element": "none"})
	check(Audio.played("hit_accent_chain", t3).size() == 1, "the chain's last blow rings the chain accent")
	tl.combo = 0
	Audio.advance(1.0)
	var def := ContentDB.entry("enemies", "trial_puppet")
	check(SoundBank.body_of(def) == "wood" and SoundBank.body_of(ContentDB.entry("enemies", "hollow_minnow")) == "slime" and SoundBank.body_of(ContentDB.entry("enemies", "wild_boarlet")) == "flesh"
		and SoundBank.death_of(ContentDB.entry("enemies", "paper_talisman_ghost")) == "die_spirit", "a foe's body and death by what it is: a puppet wood, a minnow slime, a boar flesh, a ghost dissolving")
	Game.combat.apply_execute(e, c.id)
	GameEvents.flush()

# ------------------------------------------------------------------ 5. the fight music
func _foes(kind: String, n: int, dist: float, state := "aggro") -> Array:
	var p = main.world.player
	var out: Array = []
	for i in n:
		var at: Vector2 = main.world.room.nearest_standable(p.motor.pos + Vector2.from_angle(TAU * i / maxf(1, n)) * dist)
		var e: EnemyState = Game.enemies.spawn_at(kind, at, 3)
		if e == null: continue
		e.altitude = main.world.room.height_at(at)
		e.ai.state = state
		out.append(e)
	return out

func _clear_foes() -> void:
	for e in Game.room_rt.living_enemies(): Game.combat.apply_execute(e, Game.active_id)
	GameEvents.flush()

func _run(secs: float, keep: Array = [], state := "aggro") -> void:
	var t := 0.0
	while t < secs:
		for e in keep:
			if e.alive: e.ai.state = state
		Audio.advance(0.05)
		t += 0.05

func _fight_music() -> void:
	Audio.set_process(false)
	_clear_foes()
	var ms: Dictionary = SoundBank.section("music")
	Audio.music("field")
	_run(0.5)
	var st: Dictionary = Audio.music_state()
	check(st.mode == "explore" and str(st.stem) == "field_combat" and float(st.stem_target) == 0.0 and Audio.stem.player.playing,
		"the field's track plays with its combat stem running silent beside it (%s)" % [st])
	var calm := _foes("wild_boarlet", 3, 90.0, "idle")
	_run(1.0, calm, "idle")
	check(Audio.music_state().mode == "explore", "foes near but calm bring no fight music")
	var far := _foes("wild_boarlet", 2, 100.0)
	for e in far: e.plane = Audio.listener + Vector2(float(ms.get("fight", {}).get("radius", 560)) + 300.0, 0.0)   # past the fight's reach
	_run(1.0, far)
	check(Audio.music_state().mode == "explore", "foes fighting out of reach bring no fight music")
	_clear_foes()
	var foes := _foes("wild_boarlet", 4, 100.0)
	Audio.advance(0.3)
	st = Audio.music_state()
	var beat := Audio.beat_s("field")
	check(st.mode == "fight" and (st.pending == "music" or float(st.stem_target) == 1.0), "foes turning on the player start the fight music (%s)" % [st])
	_run(beat + 0.1, foes)
	st = Audio.music_state()
	check(float(st.stem_target) == 1.0 and float(st.explore_trim_db) < 0.0, "the combat stem comes in on the next beat (within %.2f s), the tune a little under it (%s)" % [beat, st])
	_run(3.0 * beat, foes)
	check(float(Audio.music_state().stem_k) > 0.99, "the stem is fully in two beats later")
	for e in foes: Game.combat.apply_execute(e, Game.active_id)
	GameEvents.flush()
	var leave := float(ms.get("fight", {}).get("leave_after_s", 4.0))
	_run(leave * 0.5)
	check(Audio.music_state().mode == "fight" and float(Audio.music_state().stem_target) == 1.0, "the stem stays a moment after the last foe falls")
	_run(leave * 0.5 + 0.3)
	st = Audio.music_state()
	check(st.mode == "explore", "a few seconds after the last foe falls the fight is over (%s)" % [st])
	var bar := beat * float(Audio._grid("field").get("bar_beats", 4))
	_run(bar + 0.1)
	st = Audio.music_state()
	check(float(st.stem_target) == 0.0 and float(st.explore_trim_db) == 0.0, "the stem leaves on the next bar line (within %.2f s) and the tune comes back up (%s)" % [bar, st])
	# Old Snapper's own theme
	var snap := _foes("old_snapper", 1, 120.0)
	_run(0.5 + beat, snap)
	st = Audio.music_state()
	check(st.mode == "boss" and st.boss == "boss_snapper" and st.alt == "boss_snapper" and float(st.alt_target) == 1.0, "Old Snapper brings his own theme in on the beat (%s)" % [st])
	_clear_foes()
	_run(leave + 3.0)
	st = Audio.music_state()
	check(st.mode == "explore" and float(st.alt_target) == 0.0 and float(st.explore_target) == 1.0, "his theme hands back to the room's track when he falls (%s)" % [st])
	check(Audio.played("sting_victory", Audio.clock - leave - 3.1).size() >= 1 or Audio.last_victory_t > 0.0, "a fight that felled an elite ends on the victory stinger")
	# a track without a stem crossfades to the battle theme instead
	Audio.music("meditation")
	_run(1.5)
	var sm := _foes("wild_boarlet", 2, 100.0)
	_run(0.3 + Audio.beat_s("meditation") + 0.2, sm)
	st = Audio.music_state()
	check(st.mode == "fight" and st.alt == str(ms.get("fight", {}).get("fallback", "battle")) and float(st.explore_target) == 0.0, "a track with no stem crossfades to the battle theme on the beat (%s)" % [st])
	_clear_foes()
	_run(leave + 3.0)
	Audio.music("field")
	_run(1.5)
	Audio.set_process(true)

# ------------------------------------------------------------------ 6. beds and stingers
func _beds_and_stingers() -> void:
	Audio.set_process(false)
	var want := {"lf_village": "river_village", "lf_village_night": "river", "rm_marsh_edge": "marsh", "sf_market": "town", "ja_gate_street": "sect",
		"wp_east": "field", "lf_fishers_hut": "interior", "cm_cliff_stair": "sect_high"}
	var got := {}
	var ok := true
	for rid in want:
		got[rid] = SoundBank.bed_of(rid, ContentDB.room(rid))
		ok = ok and got[rid] == want[rid]
	check(ok, "each top-down room takes its bed: the village by the river, the marsh, the town, the sect, the path, indoors (%s)" % [got])
	Audio.hour_check_t = 999.0   # the test sets the hour itself
	Audio.bed("marsh", "day")
	_run(2.5)
	var roles := {}
	for l in Audio.bed_lanes:
		if str(l.player.get_meta("bed", "")) == "marsh": roles[str(l.player.get_meta("role", ""))] = l
	check(roles.has("base") and roles.has("day") and roles.has("night") and float(roles.base.k) > 0.99 and float(roles.day.k) > 0.5 and float(roles.night.k) == 0.0,
		"by day the marsh bed plays its water and reeds with the birds, the frogs silent")
	Audio.set_hour("night", 1.0)
	_run(1.2)
	check(float(roles.day.k) == 0.0 and float(roles.night.k) > 0.99, "at night the birds fall silent and the frogs come in")
	var old: Array = Audio.bed_lanes.duplicate()
	Audio.bed("town", "night")
	_run(0.5)
	var fading := old.all(func(l): return l.target == 0.0)
	var town := Audio.bed_lanes.filter(func(l): return str(l.player.get_meta("bed", "")) == "town" and str(l.player.get_meta("role", "")) == "base")
	check(fading and town.size() == 1 and float(town[0].target) > 0.9 and float(town[0].trim_db) < 0.0, "a new room's bed crossfades in over the last, the town hushed at night")
	_run(3.0)
	check(Audio.bed_lanes.all(func(l): return str(l.player.get_meta("bed", "")) == "town"), "the old bed's players are gone once faded")
	# stingers duck the music
	Audio.sting.player.stop()
	Audio.sting_queue = ""
	_run(2.0)
	var d0: float = Audio.duck_db
	Audio.stinger("sting_quest")
	_run(0.5)
	check(Audio.sting.player.playing and Audio.duck_db < d0 - 6.0, "a stinger plays on the Music bus and the music ducks under it (%.1f dB)" % Audio.duck_db)
	Audio.stinger("sting_unlock")
	check(Audio.sting.id == "sting_quest" and Audio.sting_queue == "sting_unlock", "a lesser stinger waits for the one playing")
	Audio.sting.player.stop()
	_run(1.5)
	check(Audio.played("sting_unlock", Audio.clock - 1.6).size() == 1, "and plays when it ends")
	Audio.sting.player.stop()
	_run(3.0)
	check(Audio.duck_db > -1.0, "the music comes back up after the stingers (%.1f dB)" % Audio.duck_db)
	Audio.set_process(true)

# ------------------------------------------------------------------ 8. the living world (decision 44)
func _life() -> void:
	Audio.set_process(false)
	var life: Dictionary = SoundBank.section("life")
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://data/topdown/life.json"))
	var cues: Array = data.get("cues", []) if data is Dictionary else []
	var ids: Array = SoundBank.life_ids(cues)
	for list in life.get("takes", {}).values(): ids.append_array(list)
	# the code's own names: each cue topdown_life.gd raises by name, and each flee's kind ("<kind>_flee")
	var src := FileAccess.get_file_as_string("res://scripts/topdown/topdown_life.gd")
	var re := RegEx.new()
	var code: Array = []
	re.compile("raise_cue\\(\"([a-z0-9_]+)\",")
	for m in re.search_all(src): code.append("life_" + m.get_string(1))
	re.compile("_flee\\(.*\"([a-z0-9_]+)\"\\)")
	for m in re.search_all(src): code.append("life_" + m.get_string(1) + "_flee")
	var missing: Array = ids.filter(func(id): return not _has(str(id)))
	var unnamed: Array = code.filter(func(id): return not ids.has(id))
	check(cues.size() >= 16 and code.size() >= 9 and missing.is_empty() and unnamed.is_empty() and life.get("places", []).size() == 3,
		"every sound the living world can raise has a file: %d critters, %d work cues and %d blows, %d places, %d takes (missing %s; raised in the code but not named %s)" % [
		life.get("critters", []).size(), cues.size(), life.get("blows", []).size(), life.get("places", []).size(), life.get("takes", {}).size(), missing, unnamed])
	var w = main.world
	var tl = w.life
	var at: Vector2 = w.player.motor.pos
	Audio.listener = at
	for v in Audio.voices: v.stop()
	# a cue raised in the room: once where it happens, not again within its gap
	var t0: float = Audio.clock + 0.2
	Audio.advance(0.2)
	if tl != null:
		TopdownLife.clock += 1.0
		tl.raise_cue("dog_bark", at)
		tl.raise_cue("dog_bark", at)
	var barks: Array = Audio.played("life_dog_bark", t0)
	check(tl != null and barks.size() == 1, "a village dog's bark raised in the room plays once where it happens (%s)" % [barks])
	# takes in turn, each varied a little in pitch
	var takes: Array = SoundBank.takes_of("life_work_sweep")
	var t1: float = Audio.clock + 0.2
	Audio.advance(0.2)
	for i in takes.size():
		Audio.world_sound("life_work_sweep", at)
		Audio.advance(0.15)
	var got: Array = Audio.played("life_work_sweep", t1)
	var distinct := {}
	for id in got: distinct[id] = true
	var pitches := {}
	for v in Audio.voices:
		if v.playing and Audio.vinfo.has(v) and str(Audio.vinfo[v].id).begins_with("life_work_sweep"): pitches[snappedf(v.pitch_scale, 0.0001)] = true
	var spread := float(life.get("pitch_jitter", 0.0))
	check(takes.size() >= 3 and got.size() == takes.size() and distinct.size() == takes.size() and pitches.size() >= 2
		and pitches.keys().all(func(p): return absf(float(p) - 1.0) <= spread + 0.0001),
		"a sweeper's strokes play their %d takes in turn, each at its own pitch within ±%.1f%% (%s; %s)" % [takes.size(), spread * 100.0, got, pitches.keys()])
	# a busy village: every critter's and every worker's sound asked at once, round and round
	for v in Audio.voices: v.stop()
	Audio.stats.peak_rule = {}
	var every: Array = life.get("critters", []) + life.get("work", []) + life.get("blows", [])
	for i in 40:
		Audio.world_sound(str(every[i % every.size()]), at + Vector2(16.0 * (i % 5), 0.0))
		Audio.advance(0.11)
	var pr: Dictionary = Audio.stats.peak_rule
	var busy := _life_voices()
	check(int(pr.get("life_", 0)) <= 3 and int(pr.get("life_work_", 0)) <= 3 and busy >= 3,
		"a busy village sounds at most three critters and three people at work at once (%d sounding; peaks %s)" % [busy, pr])
	# the fight starting in it: no sound of the fight goes without a voice while a life sound holds one
	var fight := ["hit_sword_a", "hit_on_flesh_a", "hit_tail_sword", "swing_sword", "step_grass_a", "land_grass", "die_flesh", "tell_beast",
		"cast_fire", "hit_el_fire", "splash", "loot_drop", "coin", "hurt", "door_open"]
	var stolen0: int = Audio.stats.stolen
	var crowded: Array = []
	var asked := 0
	for r in 3:
		for id in fight:
			asked += 1
			if Audio.play(id, "SFX", {"at": at}) == null and _life_voices() > 0: crowded.append(id)
			Audio.advance(0.11)
	check(crowded.is_empty() and Audio.stats.stolen > stolen0 and _life_voices() == 0,
		"the fight's %d sounds take the village's voices first: none goes unheard while a life sound plays (%s), and none of the village is left (%d)" % [asked, crowded, _life_voices()])
	for v in Audio.voices: v.stop()
	Audio.set_process(true)

func _life_voices() -> int:
	var n := 0
	for v in Audio.voices:
		if v.playing and Audio.vinfo.has(v) and str(Audio.vinfo[v].id).begins_with("life_"): n += 1
	return n

# ------------------------------------------------------------------ 7. the voice limit
## The fifteen-monster fight (perf_tests' crowd): fifteen foes fighting the player, its blows and techniques going
## off, their tells, steps and deaths: the pool never overflows and no sound passes its rule's cap.
func _crowd() -> void:
	var w = main.world
	var p = w.player
	_clear_foes()
	p.motor.place(Vector2(22.5, 18.5) * 32.0)
	var kinds := ["mudshell_crab", "reedtail_rat", "wild_boarlet"]
	for i in 15:
		var at: Vector2 = p.motor.pos + Vector2.from_angle(TAU * i / 15.0) * (70.0 + 12.0 * (i % 3))
		var e: EnemyState = Game.enemies.spawn_at(kinds[i % 3], at, 5)
		if e == null: continue
		e.altitude = w.room.height_at(at)
		e.threat[Game.active_id] = 1.0
	var pool := int(SoundBank.section("mix").get("voices", {}).get("pool", 24))
	# What Master puts out, after its limiter, recorded for the fight (the dummy driver mixes headless too).
	var rec := AudioEffectRecord.new()
	AudioServer.add_bus_effect(0, rec)
	rec.set_recording_active(true)
	Audio.stats.peak = 0
	Audio.stats.peak_rule = {}
	var played0: int = Audio.stats.played
	var worst := 0
	for i in 240:
		p.movement = Vector2.from_angle(i * 0.07) * 0.3
		Game.active().pools.hp = Game.active().pools.max_hp
		Game.combat.wounded.erase(Game.active_id)
		if i % 20 == 0: p.aim_attack(Vector2.from_angle(i * 0.4))
		if i % 45 == 10:
			Game.active().pools.cooldowns.clear()
			p.aim_technique((i / 45) % 4, Vector2.from_angle(i * 0.3), 0.6)
		if i == 200:
			for e in Game.room_rt.living_enemies(): Game.combat.apply_execute(e, Game.active_id)
		await get_tree().process_frame
		worst = maxi(worst, Audio.voices_playing())
	rec.set_recording_active(false)
	var wav := rec.get_recording()
	AudioServer.remove_bus_effect(0, AudioServer.get_bus_effect_count(0) - 1)
	var data: PackedByteArray = wav.data if wav != null else PackedByteArray()
	var loud := 0
	var over_ceiling := 0
	var ceiling := db_to_linear(float(SoundBank.section("mix").get("master", {}).get("limiter_ceiling_db", -0.5))) * 32768.0 + 64.0
	for i in range(0, data.size() - 1, 2):
		var s := absi(data.decode_s16(i))
		loud = maxi(loud, s)
		if s > ceiling: over_ceiling += 1
	print("audio crowd: Master recorded %d samples, peak %.1f dBFS" % [data.size() / 2, linear_to_db(maxf(loud, 1) / 32768.0)])
	check(data.size() > 1000 and loud > 100 and over_ceiling == 0, "the fifteen-monster fight never passes the limiter's ceiling on Master (peak %.1f dBFS over %d samples)" % [linear_to_db(maxf(loud, 1) / 32768.0), data.size() / 2])
	var over: Array = []
	for r in SoundBank.section("mix").get("voices", {}).get("rules", []):
		var key := str(r[0])
		if key != "" and int(Audio.stats.peak_rule.get(key, 0)) > int(r[2]): over.append("%s %d>%d" % [key, Audio.stats.peak_rule[key], r[2]])
	print("audio crowd: %d sounds asked, peak %d voices of %d, %d merged, %d dropped, %d stolen; per rule %s" % [Audio.stats.played - played0,
		Audio.stats.peak, pool, Audio.stats.merged, Audio.stats.dropped, Audio.stats.stolen, Audio.stats.peak_rule])
	check(Audio.stats.played - played0 > 30 and worst <= pool and int(Audio.stats.peak) <= pool and over.is_empty(),
		"the fifteen-monster fight holds the voice limit: at most %d of %d voices, no rule over its cap (%s)" % [Audio.stats.peak, pool, over])
	check(Audio.music_state().mode != "explore" or Audio.played("step_", -INF).size() > 0, "the crowd fight brought the fight music")
