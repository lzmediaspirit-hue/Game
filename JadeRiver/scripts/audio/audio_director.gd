extends Node
## `Audio` autoload (S36; decision 43's sound pass, docs/redesign/sound.md). Presentation only: no rule code plays
## audio, and a missing file is silent. Its tables are data/sound.json (tools/data/sound.py, read through SoundBank)
## and the manifest data/audio.json (tools/audio/build_audio.py: every sound's file, level and length, each track's
## grid and combat stem).
##   - The mix: buses Master, Music, Ambience, SFX and UI, each driven by its Settings slider; a high-pass and a
##     limiter on Master; the music (and half as much the beds) ducking under stingers, barks, talks and scenes.
##   - Voices: a pool with priorities. A sound's rule caps how many of it sound at once and how close two may start;
##     a new sound steals the quietest older voice of a lower priority when the pool is full, else it is dropped, so a
##     crowd of foes never clips or smears. The player's own sounds rank above the same from a foe.
##   - Positional sounds (`at`, world units): quieter with distance from the listener (the player's feet, which the
##     top-down world sets), silent past the far distance.
##   - Layered hits: the weapon family's transient, the struck body's material, the family's tail when the hit-stop
##     lets go, an accent for a crit or finisher, the chain's last blow and a weave cancel; blows landing together (one
##     swing through a crowd) sound as one, a little louder.
##   - The room's ambient bed (its base loops and the layer of the hour), crossfaded on a room change.
##   - The music: the room's track and its combat stem in sync, the stem brought in on the next beat when foes near
##     the player turn on it and taken out on a bar line a few seconds after the last one falls or gives up; a track
##     with no stem crossfades to the battle theme instead; a boss's own theme; and the stingers.
## Others' calls (the living world's critters and work): `world_sound(id, at, gain_db)`, `step_at(surface, at, who)`.

const BUSES := ["Music", "Ambience", "SFX", "UI"]
## Events answered with one sound (a boss's phase, a level and the rest sound through their moments, data/moments.json).
const EVENT_SFX := {"quest_accepted": "quest_accept", "mail_received": "mail", "meditation_started": "meditate",
	"qi_backlash": "backlash", "node_gathered": "gather", "fish_caught": "fish_bite", "craft_completed": "forge",
	"field_boss_spawned": "boss_roar", "item_bought": "coin", "item_sold": "coin"}
const UI_EVENTS := ["quest_accepted", "mail_received"]
const SFX_ALIAS := {"ui_back": "ui_close", "ui_error": "error", "punch": "swing", "hit_light": "hit"}
const SILENT := -80.0
const STING_RANK := {"sting_breakthrough": 5, "sting_victory": 4, "sting_elite": 3, "sting_rare": 2, "sting_quest": 2, "sting_unlock": 1}

## One music or bed player and its level: `k` is its fade (linear amplitude, moving toward `target` at `rate` a
## second), `trim_db` a standing offset (a track under its stem in a fight), `base_db` the manifest's level.
class Lane:
	var player: AudioStreamPlayer
	var id := ""
	var base_db := 0.0
	var trim_db := 0.0
	var k := 0.0
	var target := 0.0
	var rate := 1.0
	var stop_at_zero := false
	var free_at_zero := false
	var duck_share := 1.0
	func _init(p: AudioStreamPlayer) -> void:
		player = p
	func fade(to: float, secs: float, stop := false) -> void:
		target = clampf(to, 0.0, 1.0)
		rate = absf(target - k) / secs if secs > 0.0 else INF
		stop_at_zero = stop and target <= 0.0
	func advance(delta: float) -> void:
		if k != target: k = move_toward(k, target, rate * delta) if rate < INF else target
		if k <= 0.0 and target <= 0.0 and stop_at_zero and player.playing: player.stop()
	func db() -> float:
		return base_db + trim_db + linear_to_db(maxf(k, 0.0001))

var enabled := true
var clock := 0.0                    ## seconds of this node's own time (advance), for gaps, merges and holds
var listener := Vector2.INF         ## the player's feet in a room on the grid; INF: nothing is positional
var streams: Dictionary = {}
# voices
var voices: Array = []              ## the SFX pool (AudioStreamPlayer)
var ui_voices: Array = []
var vinfo: Dictionary = {}          ## player -> {id, rule, prio, start, gain}
var last_start: Dictionary = {}     ## rule prefix -> clock of its last start
var stats := {"played": 0, "dropped": 0, "stolen": 0, "merged": 0, "peak": 0, "peak_rule": {}}
var history: Array = []             ## the last sounds played [{id, t, gain, bus}] (the audio suite reads it)
var pending: Array = []            ## [{t, fn, what}]: sounds and music moves waiting (the hit's tail, a beat)
# hits
var last_hit_t := -9.0
var hit_merge := 0
var last_hit_voice: AudioStreamPlayer   ## the last hit's transient, raised a little by each blow merged into it
var rr: Dictionary = {}             ## round robins: key -> next index
# music
var explore: Lane                   ## the room's track
var explore_old: Lane               ## the track crossfading out on a room change
var stem: Lane                      ## the track's combat stem, started with it and kept in step
var alt: Lane                       ## the battle theme or a boss's theme
var alt_old: Lane
var sting: Lane
var sting_queue := ""
var sting_queue_t := 0.0
var current_music := ""
var mode := "explore"               ## explore, fight, boss
var boss_track := ""
var calm_t := 0.0
var fight_check_t := 0.0
var fighting := false
var fight_had_elite := false
var last_victory_t := -99.0
# beds
var bed_id := ""
var bed_lanes: Array = []           ## Lane (base loops and the hour's layers)
var bed_hour := ""
var hour_check_t := 0.0
var hour_source: Callable           ## the top-down world's hour (TopdownLight), else the clock's
# ducking
var holds: Dictionary = {}          ## name -> {db, until (clock; INF while held)}
var duck_db := 0.0
var last_room := ""
# compatibility
var current_ambience := ""
var music_a: AudioStreamPlayer
var music_b: AudioStreamPlayer
var ambience: AudioStreamPlayer

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_buses()
	var pool := int(mix().get("voices", {}).get("pool", 24))
	for i in pool:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		voices.append(p)
	for i in int(mix().get("voices", {}).get("ui_pool", 6)):
		var p := AudioStreamPlayer.new()
		p.bus = "UI"
		add_child(p)
		ui_voices.append(p)
	explore = _lane("Music")
	explore_old = _lane("Music")
	stem = _lane("Music")
	alt = _lane("Music")
	alt_old = _lane("Music")
	sting = _lane("Music")
	sting.k = 1.0
	sting.target = 1.0
	music_a = explore.player
	music_b = explore_old.player
	ambience = AudioStreamPlayer.new()   # kept for callers of the old API; the beds are bed_lanes
	ambience.bus = "Ambience"
	add_child(ambience)
	GameEvents.event.connect(_on_event)
	apply_settings()

func _lane(bus: String) -> Lane:
	var p := AudioStreamPlayer.new()
	p.bus = bus
	add_child(p)
	return Lane.new(p)

func mix() -> Dictionary:
	return SoundBank.section("mix")

# ------------------------------------------------------------------ buses and the Settings sliders
## The buses under Master (made once), Master's high-pass and limiter, and each bus's level from its slider.
func _buses() -> void:
	for bus in BUSES:
		if AudioServer.get_bus_index(bus) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, bus)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")
	var m: Dictionary = mix().get("master", {})
	var has_hp := false
	var has_lim := false
	for i in AudioServer.get_bus_effect_count(0):
		var fx := AudioServer.get_bus_effect(0, i)
		has_hp = has_hp or fx is AudioEffectHighPassFilter
		has_lim = has_lim or fx is AudioEffectHardLimiter
	if not has_hp:
		var hp := AudioEffectHighPassFilter.new()
		hp.cutoff_hz = float(m.get("highpass_hz", 45.0))
		AudioServer.add_bus_effect(0, hp)
	if not has_lim:
		var lim := AudioEffectHardLimiter.new()
		lim.ceiling_db = float(m.get("limiter_ceiling_db", -0.5))
		lim.release = float(m.get("limiter_release_s", 0.1))
		AudioServer.add_bus_effect(0, lim)

func apply_settings() -> void:
	var s: Dictionary = Game.account.settings if Game and Game.account else {}
	for b in mix().get("buses", [{"name": "Music", "setting": "music"}, {"name": "Ambience", "setting": "ambience"},
			{"name": "SFX", "setting": "sfx"}, {"name": "UI", "setting": "ui"}]):
		var idx := AudioServer.get_bus_index(str(b.name))
		if idx >= 0: AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(0.0001, float(s.get(str(b.setting), b.get("default", 0.7))))))
	var m: Dictionary = mix().get("master", {})
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(0.0001, float(s.get(str(m.get("setting", "master")), m.get("default", 1.0))))))

# ------------------------------------------------------------------ streams
func _stream(kind: String, id: String) -> AudioStream:
	var key := kind + ":" + id
	if streams.has(key): return streams[key]
	var e: Dictionary = SoundBank.manifest().get(kind, {}).get(id, {})
	var path := str(e.get("file", ""))
	var st: AudioStream = load(path) if path != "" and ResourceLoader.exists(path) else null
	if st != null and (kind == "music" or bool(e.get("loop", false))):
		if st is AudioStreamWAV:
			# Loop points in samples from the stream length: correct for PCM and compressed imports alike.
			var wav := st as AudioStreamWAV
			wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
			wav.loop_begin = 0
			wav.loop_end = int(wav.get_length() * float(wav.mix_rate))
		elif st is AudioStreamOggVorbis:
			(st as AudioStreamOggVorbis).loop = true
	streams[key] = st
	return st

func _vol(kind: String, id: String, fallback: float) -> float:
	return float(SoundBank.manifest().get(kind, {}).get(id, {}).get("volume_db", fallback))

# ------------------------------------------------------------------ voices
## Play one sound. opts: gain_db, pitch, at (world units: positional), player (the player's own: ranks higher),
## prio (added to its rule's). Returns the voice, or null when the sound is missing, too far, merged or dropped.
func play(id: String, bus := "SFX", opts := {}) -> AudioStreamPlayer:
	if not enabled or id == "": return null
	id = str(SFX_ALIAS.get(id, id))
	if id.begins_with("sting_"):
		stinger(id)
		return null
	var st := _stream("sfx", id)
	if st == null: return null
	var gain := _vol("sfx", id, -4.0) + float(opts.get("gain_db", 0.0))
	if opts.has("at"):
		var g := distance_db(opts.at)
		if g <= SILENT: return null
		gain += g
	var rule := SoundBank.voice_rule(id)
	var vm: Dictionary = mix().get("voices", {})
	var prio := int(rule[1]) + (int(vm.get("player_bonus", 20)) if opts.get("player", false) else 0) + int(opts.get("prio", 0))
	var pool: Array = ui_voices if bus == "UI" else voices
	var key := str(rule[0]) if str(rule[0]) != "" else id   # the catch-all rule counts and spaces each sound on its own
	if clock - float(last_start.get(key, -9.0)) < float(rule[3]):
		stats.merged += 1
		return null
	var slot: AudioStreamPlayer = null
	var same: Array = []
	for v in pool:
		if v.playing and vinfo.has(v) and str(vinfo[v].rule) == key: same.append(v)
	if same.size() >= int(rule[2]):
		slot = _weakest(same, prio)
		if slot == null:
			stats.dropped += 1
			return null
	if slot == null:
		for v in pool:
			if not v.playing:
				slot = v
				break
	if slot == null:
		slot = _weakest(pool, prio - 1)
		if slot == null:
			stats.dropped += 1
			return null
	if slot.playing: stats.stolen += 1
	slot.stop()
	slot.stream = st
	slot.bus = bus
	slot.volume_db = gain
	slot.pitch_scale = clampf(float(opts.get("pitch", randf_range(0.97, 1.03))), 0.5, 2.0)
	slot.play()
	vinfo[slot] = {"id": id, "rule": key, "prio": prio, "start": clock, "gain": gain}
	last_start[key] = clock
	stats.played += 1
	_remember(id, gain, bus, bool(opts.get("player", false)))
	var n := 0
	var nr := 0
	for v in pool:
		if v.playing:
			n += 1
			if vinfo.has(v) and str(vinfo[v].rule) == key: nr += 1
	stats.peak = maxi(int(stats.peak), n)
	stats.peak_rule[key] = maxi(int(stats.peak_rule.get(key, 0)), nr)
	return slot

## The voice a sound of priority `prio` may take from `list`: the lowest priority at or under it, the quietest and
## oldest of those; null when every one outranks it.
func _weakest(list: Array, prio: int) -> AudioStreamPlayer:
	var best: AudioStreamPlayer = null
	var best_score := INF
	for v in list:
		var info: Dictionary = vinfo.get(v, {"prio": 0, "start": -99.0, "gain": -99.0})
		if int(info.prio) > prio: continue
		var score := float(info.prio) * 1000.0 + float(info.gain) * 4.0 + (float(info.start) - clock)
		if score < best_score:
			best_score = score
			best = v
	return best

func _remember(id: String, gain: float, bus: String, mine := false) -> void:
	history.append({"id": id, "t": clock, "gain": gain, "bus": bus, "player": mine})
	if history.size() > 256: history.pop_front()

## The ids played since `since` (the director's clock) that start with `prefix`.
func played(prefix := "", since := -INF, mine_only := false) -> Array:
	var out: Array = []
	for h in history:
		if float(h.t) >= since and str(h.id).begins_with(prefix) and (not mine_only or h.player): out.append(str(h.id))
	return out

## How many voices sound now (the audio suite's voice limit).
func voices_playing(ui := false) -> int:
	var n := 0
	for v in (ui_voices if ui else voices):
		if v.playing: n += 1
	return n

func ui(id := "ui_tap") -> void:
	play(id, "UI")

## Distance attenuation from the listener: 0 dB within `near`, falling (log-distance) to `floor_db` at `far`,
## silent past it.
func distance_db(at: Vector2) -> float:
	if listener == Vector2.INF: return 0.0
	var d: Dictionary = mix().get("distance", {})
	var near := float(d.get("near", 96.0))
	var far := float(d.get("far", 900.0))
	var dist := at.distance_to(listener)
	if dist <= near: return 0.0
	if dist >= far: return SILENT
	return float(d.get("floor_db", -24.0)) * log(dist / near) / log(far / near)

## A world sound at a place (the living world's critters and work, a door, a splash): positional, a little under the
## fight's sounds in the voice pool.
func world_sound(id: String, at: Vector2, gain_db := 0.0) -> AudioStreamPlayer:
	return play(id, "SFX", {"at": at, "gain_db": gain_db, "prio": -10})

func _later(secs: float, fn: Callable, what := "") -> void:
	if secs <= 0.0:
		fn.call()
		return
	pending.append({"t": secs, "fn": fn, "what": what})

func _jitter(sec: Dictionary) -> Dictionary:
	return {"db": randf_range(-1.0, 1.0) * float(sec.get("vol_jitter_db", 1.5)), "pitch": 1.0 + randf_range(-1.0, 1.0) * float(sec.get("pitch_jitter", 0.035))}

func _next(key: String, list: Array) -> String:
	if list.is_empty(): return ""
	var i := int(rr.get(key, randi() % list.size()))
	rr[key] = (i + 1) % list.size()
	return str(list[i % list.size()])

# ------------------------------------------------------------------ combat
## A blow landed (a hit_landed payload): three layers as one hit, varied, with its accents, the tail after the
## hit-stop (CombatFeel). A blow on the player: the foe's weapon family and the player's hurt.
func hit(p: Dictionary) -> void:
	var h := SoundBank.section("hits")
	var kind := str(p.get("target_kind", "enemy"))
	var at := Vector2(float(p.get("x", 0)), float(p.get("y", 0)))
	var weight := str(p.get("weight", "medium"))
	var crit := bool(p.get("crit", false))
	var m: Dictionary = h.get("mix", {})
	var wdb := float(h.get("weight_db", {}).get(weight, 0.0))
	var wp := float(h.get("weight_pitch", {}).get(weight, 1.0))
	if kind == "player":
		var foe = _enemy(str(p.get("attacker", "")))
		if foe != null:
			var fam := SoundBank.foe_family(foe.def)
			var jf := _jitter(h)
			play(_next("hit:" + fam, h.get("families", {}).get(fam, {}).get("transient", [])), "SFX", {"gain_db": wdb + jf.db - 2.0, "pitch": wp * jf.pitch})
		play(str(h.get("player_hurt", "hurt")), "SFX", {"player": true, "gain_db": float(m.get("player_hurt_db", 0.0))})
		return
	if kind not in ["enemy", "ally", "decoy"]:
		play("hit")
		return
	# One swing through a crowd: the blows within merge_s sound as the first, a little louder.
	if clock - last_hit_t < float(h.get("merge_s", 0.035)):
		hit_merge += 1
		stats.merged += 1
		if is_instance_valid(last_hit_voice) and last_hit_voice.playing and vinfo.has(last_hit_voice):
			var boost := minf(float(h.get("merge_max_db", 3.0)), float(h.get("merge_db", 1.5)) * hit_merge)
			last_hit_voice.volume_db = float(vinfo[last_hit_voice].gain) + boost
		return
	last_hit_t = clock
	hit_merge = 0
	var attacker := str(p.get("attacker", ""))
	var mine := Game.active_id != "" and attacker == Game.active_id
	var src := str(p.get("source", ""))
	var target = _enemy(str(p.get("target", "")))
	var body := SoundBank.body_of(target.def) if target != null else "flesh"
	var opts := {"player": mine}
	if not mine: opts["at"] = at
	var j := _jitter(h)
	var fam := ""
	var tl: Dictionary = Game.combat.timeline(attacker) if Game.combat != null and Game.character(attacker) != null else {}
	if src.begins_with("tech:"):
		var el := SoundBank.element_sound(str(p.get("element", "none")))
		last_hit_voice = play("hit_el_" + el, "SFX", opts.merged({"gain_db": wdb + float(m.get("element_db", -1.0)) + j.db, "pitch": wp * j.pitch}))
	else:
		fam = SoundBank.family_sound(str(tl.get("family", "fists"))) if not tl.is_empty() else "fists"
		last_hit_voice = play(_next("hit:" + fam, h.get("families", {}).get(fam, {}).get("transient", [])), "SFX",
			opts.merged({"gain_db": wdb + float(m.get("transient_db", 0.0)) + j.db, "pitch": wp * j.pitch}))
	var jb := _jitter(h)
	play(_next("body:" + body, h.get("bodies", {}).get(body, [])), "SFX", opts.merged({"gain_db": wdb + float(m.get("body_db", -1.0)) + jb.db, "pitch": wp * jb.pitch}))
	var acc: Dictionary = h.get("accents", {})
	if crit or weight == "finisher":
		play(str(acc.get("crit" if crit else "finisher", "hit_accent_crit")), "SFX", opts.merged({"gain_db": float(m.get("accent_db", -1.0))}))
	elif fam != "" and _chain_last(tl, src):
		play(str(acc.get("chain_last", "hit_accent_chain")), "SFX", opts.merged({"gain_db": float(m.get("accent_db", -1.0))}))
	if fam != "":
		var stop := CombatFeel.hitstop_s(weight, crit) if CombatFeel.hitstop_on() else 0.0
		var tail := str(h.get("families", {}).get(fam, {}).get("tail", ""))
		var tj := _jitter(h)
		_later(stop, func(): play(tail, "SFX", opts.merged({"gain_db": wdb + float(m.get("tail_db", -3.0)) + tj.db, "pitch": wp * tj.pitch})), "tail")

## The chain's last blow: the family's last combo step (or its dragged finisher).
func _chain_last(tl: Dictionary, src: String) -> bool:
	if src != "basic" or tl.is_empty(): return false
	var steps: Array = CombatFeel.family(str(tl.get("family", "fists"))).get("steps", [])
	return steps.size() > 1 and int(tl.get("combo", 0)) >= steps.size() - 1

## The player's basic attack starting: its family's swing, the chain's steps a little apart in pitch.
func swing(weapon_family: String, p := {}) -> void:
	var fam := SoundBank.family_sound(weapon_family)
	var combo := int(p.get("combo", 0))
	var pitch: float = [1.0, 1.05, 0.95][combo % 3] * (0.9 if p.get("finisher", false) else 1.0) * randf_range(0.97, 1.03)
	var id := str(SoundBank.section("hits").get("families", {}).get(fam, {}).get("swing", "swing"))
	play(id if SoundBank.has_sound(id) else "swing", "SFX", {"player": true, "pitch": pitch, "gain_db": 1.5 if p.get("finisher", false) else 0.0})

## A technique cast: its element's sound.
func cast(element: String, mine := true) -> void:
	var id := "cast_" + SoundBank.element_sound(element)
	play(id if SoundBank.has_sound(id) else "technique", "SFX", {"player": mine})

## A weave cancel (a technique cutting a basic step's recovery, or the reverse): a quick flick.
func weave() -> void:
	play(str(SoundBank.section("world").get("weave", "hit_accent_weave")), "SFX", {"player": true, "gain_db": -2.0})

## A foe winding up: its voice by race and body, over the tick every tell shares; louder and lower for elites and
## bosses; where it stands.
func foe_tell(e) -> void:
	if e == null: return
	var f := SoundBank.section("foes")
	var role := str(e.role)
	var g := float(f.get("role_db", {}).get(role, 0.0)) + (2.0 if e.elite else 0.0)
	var pitch := float(f.get("role_pitch", {}).get(role, 1.0)) * randf_range(0.96, 1.04)
	play(SoundBank.tell_of(e.def), "SFX", {"at": e.plane, "gain_db": g, "pitch": pitch})
	play(str(f.get("tell_tick", "tell")), "SFX", {"at": e.plane, "gain_db": float(f.get("tell_tick_db", -6.0))})

## A foe fallen (an actor_defeated payload): its death by body, race or nature.
func foe_death(p: Dictionary) -> void:
	var def := ContentDB.entry("enemies", str(p.get("def", "")))
	var f := SoundBank.section("foes")
	var role := str(p.get("role", "normal"))
	var at := Vector2(float(p.get("x", 0)), float(p.get("y", 0)))
	var opts := {"gain_db": float(f.get("role_db", {}).get(role, 0.0)), "pitch": float(f.get("role_pitch", {}).get(role, 1.0)) * randf_range(0.95, 1.05)}
	if listener != Vector2.INF: opts["at"] = at
	var id := SoundBank.death_of(def) if not def.is_empty() else "enemy_die"
	play(id if SoundBank.has_sound(id) else "enemy_die", "SFX", opts)
	if bool(p.get("elite", false)) or role != "normal": fight_had_elite = true

func _enemy(uid: String):
	if Game.room_rt == null or not uid.is_valid_int(): return null
	return Game.room_rt.enemies.get(int(uid))

# ------------------------------------------------------------------ feet
## A footstep on `surface`. who: "player" (its gait "walk" or "run"), "foe" or "npc" (quieter, at `at`).
func step(surface: String, at := Vector2.INF, who := "player", gait := "run") -> AudioStreamPlayer:
	var st := SoundBank.section("steps")
	var list := SoundBank.steps_of(surface)
	if list.is_empty(): return null
	var j := _jitter(st)
	var opts := {"gain_db": float(st.get("gain_db", {}).get(gait, 0.0)) + j.db, "pitch": float(st.get("pitch", {}).get(gait, 1.0)) * j.pitch}
	if who == "player":
		opts["player"] = true
	else:
		opts.gain_db += float(st.get("foe_gain_db" if who == "foe" else "npc_gain_db", -8.0))
		if at != Vector2.INF: opts["at"] = at
	return play(_next("step:" + who + ":" + surface, list), "SFX", opts)

## Another's footstep (a villager's, a critter's): the living world's call.
func step_at(surface: String, at: Vector2, who := "npc") -> AudioStreamPlayer:
	return step(surface, at, who, "walk")

## A landing from `fall` world units onto `surface`: none for a hop down a step, louder the further it fell, the
## body's weight over it from a height.
func land(surface: String, fall: float) -> void:
	var l: Dictionary = SoundBank.section("steps").get("land", {})
	if fall < float(l.get("min_fall", 6.0)): return
	var pts: Array = l.get("gain_by_fall", [[6.0, -8.0], [60.0, 0.0]])
	var g := float(pts[0][1])
	for i in pts.size() - 1:
		var a: Array = pts[i]
		var b: Array = pts[i + 1]
		if fall >= float(a[0]): g = lerpf(float(a[1]), float(b[1]), clampf((fall - float(a[0])) / (float(b[0]) - float(a[0])), 0.0, 1.0))
	var id := SoundBank.land_of(surface)
	play(id if SoundBank.has_sound(id) else "land", "SFX", {"player": true, "gain_db": g, "pitch": randf_range(0.96, 1.04)})
	if fall >= float(l.get("heavy_fall", 40.0)): play(str(l.get("heavy", "land_heavy")), "SFX", {"player": true, "gain_db": g})

# ------------------------------------------------------------------ talk, barks, scenes
## A talk opening (true) or closing (false): the scroll's sound, and the music ducked while it is open.
func talk(open: bool) -> void:
	if open:
		if not holds.has("dialogue"): ui(str(SoundBank.section("world").get("talk_open", "talk_open")))
		duck("dialogue", float(mix().get("duck", {}).get("dialogue_db", -6.0)))
	else:
		unduck("dialogue")

func talk_next() -> void:
	ui(str(SoundBank.section("world").get("talk_next", "talk_next")))

## A bark over someone (a villager's line, a moment's): a small pip where they stand, the music dipping under it.
func bark(at := Vector2.INF) -> void:
	var opts := {"gain_db": 0.0}
	if at != Vector2.INF: opts["at"] = at
	play(str(SoundBank.section("world").get("bark", "bark")), "SFX", opts)
	duck("bark", float(mix().get("duck", {}).get("bark_db", -4.0)), 1.6)

## Duck the music (and half as much the beds) by `db` while `name` holds (`secs` <= 0: until unduck).
func duck(name: String, db: float, secs := 0.0) -> void:
	holds[name] = {"db": db, "until": clock + secs if secs > 0.0 else INF}

func unduck(name: String) -> void:
	holds.erase(name)

# ------------------------------------------------------------------ music
## Play the room's track (a mood is resolved to a track); its combat stem starts with it, silent, in step.
func music(id: String) -> void:
	id = str(SoundBank.section("music").get("alias", {}).get(id, id))
	if id == current_music: return
	current_music = id
	var fade := float(SoundBank.section("music").get("room_fade_s", 1.0))
	# the old track and its stem fade out; the lanes swap
	var old := explore_old
	explore_old = explore
	explore = old
	explore_old.fade(0.0, fade, true)
	stem.fade(0.0, fade * 0.5, true)
	if mode != "explore": _leave_fight(true)
	var st := _stream("music", id)
	explore.id = id
	explore.trim_db = 0.0
	explore.base_db = _vol("music", id, -6.0)
	if st == null:
		explore.player.stop()
		return
	explore.player.stream = st
	explore.k = 0.0
	explore.fade(1.0, fade)
	var stem_id := str(SoundBank.manifest().get("music", {}).get(id, {}).get("stem", ""))
	var sst := _stream("music", stem_id) if stem_id != "" else null
	stem.id = stem_id if sst != null else ""
	explore.player.play()
	if sst != null:
		stem.player.stop()
		stem.player.stream = sst
		stem.base_db = _vol("music", stem_id, -6.0)
		stem.k = 0.0
		stem.target = 0.0
		stem.stop_at_zero = false
		stem.player.play()     # the same frame as its track: they start in the same mix and stay in step
	_apply_levels()

func music_for_room(room: Dictionary) -> String:
	if room.has("music"): return str(room.music)
	var night := Clock.time_of_day() == "night"
	match str(room.get("type", "field")):
		"town", "interior", "home": return "village_night" if night else "village_day"
		"sect": return "sect"
		"dungeon", "secret": return "dungeon"
		"boss_arena": return "boss"
		"insight", "rest": return "meditation"
	return "field"

## The track's grid (bpm, beats a bar, loop length) from the manifest.
func _grid(id: String) -> Dictionary:
	return SoundBank.manifest().get("music", {}).get(id, {})

## Seconds until the next beat (unit "beat") or bar line ("bar") of the lane's track, from where its player is; 0 when
## it has no grid or is not playing.
func until_next(l: Lane, unit := "beat") -> float:
	var g := _grid(l.id)
	var bpm := float(g.get("bpm", 0.0))
	if bpm <= 0.0 or not l.player.playing: return 0.0
	var beat := 60.0 / bpm
	var span := beat * (float(g.get("bar_beats", 4)) if unit == "bar" else 1.0)
	var pos := l.player.get_playback_position() + AudioServer.get_time_since_last_mix() - 0.025   # the notes sit 25 ms after the grid
	var loop_s := float(g.get("loop_s", l.player.stream.get_length() if l.player.stream else 0.0))
	if loop_s > 0.0: pos = fposmod(pos, loop_s)
	var nxt := ceilf((pos + 0.02) / span) * span
	return nxt - pos

func beat_s(id: String) -> float:
	var bpm := float(_grid(id).get("bpm", 0.0))
	return 60.0 / bpm if bpm > 0.0 else 0.5

## The fight as the music hears it: is a foe near the player fighting it, and is it a boss with a theme of its own?
func scan_fight() -> Dictionary:
	var out := {"fighting": false, "boss": ""}
	var c = Game.active() if Game else null
	if c == null or Game.room_rt == null: return out
	var f: Dictionary = SoundBank.section("music").get("fight", {})
	var calm: Array = f.get("calm_states", ["idle", "patrol", "return"])
	var radius := float(f.get("radius", 560.0))
	var bosses: Dictionary = SoundBank.section("music").get("boss", {})
	var roles: Dictionary = SoundBank.section("music").get("boss_roles", {})
	for e in Game.room_rt.living_enemies():
		if e.team != "enemy" or e.def.get("passive", false) or e.ai.get("surrendered", false): continue
		if str(e.ai.get("state", "idle")) in calm: continue
		var boss: bool = e.is_boss() or bosses.has(e.def_id)
		if not boss and (e.hidden or (listener != Vector2.INF and e.plane.distance_to(listener) > radius)): continue
		out.fighting = true
		if bosses.has(e.def_id): out.boss = str(bosses[e.def_id])
		elif e.is_boss() and roles.has(e.role) and out.boss == "": out.boss = str(roles[e.role])
	return out

func _fight_step(delta: float) -> void:
	var f: Dictionary = SoundBank.section("music").get("fight", {})
	fight_check_t -= delta
	if fight_check_t <= 0.0:
		fight_check_t = float(f.get("check_s", 0.25))
		var s := scan_fight()
		fighting = bool(s.fighting)
		if fighting:
			calm_t = 0.0
			if str(s.boss) != "" and (mode != "boss" or boss_track != str(s.boss)): _enter_boss(str(s.boss))
			elif mode == "explore": _enter_fight()
	if not fighting and mode != "explore":
		calm_t += delta
		if calm_t >= float(f.get("leave_after_s", 4.0)): _leave_fight()

## Foes turn on the player: the stem comes in on the next beat (or the battle theme, crossfaded on it).
func _enter_fight() -> void:
	mode = "fight"
	calm_t = 0.0
	var f: Dictionary = SoundBank.section("music").get("fight", {})
	_cancel("music")
	if stem.id != "" and stem.player.playing:
		var fade := float(f.get("enter_fade_beats", 2.0)) * beat_s(explore.id)
		var under := float(f.get("explore_db", -2.0))
		var stem_in := func():
			stem.fade(1.0, fade)
			explore.trim_db = under
		_later(until_next(explore, "beat"), stem_in, "music")
	else:
		var fb := str(f.get("fallback", "battle"))
		var fade2 := float(f.get("fallback_fade_s", 1.2))
		var theme_in := func():
			_play_alt(fb, fade2)
			explore.fade(0.0, fade2)
		_later(until_next(explore, "beat"), theme_in, "music")

## A boss with a theme of its own joins the fight: its theme comes in on the next beat over whatever plays.
func _enter_boss(track: String) -> void:
	mode = "boss"
	boss_track = track
	calm_t = 0.0
	_cancel("music")
	var fade := float(SoundBank.section("music").get("boss_fade_s", 1.0))
	var ref: Lane = alt if alt.player.playing and alt.k > 0.0 else explore
	var boss_in := func():
		_play_alt(track, fade)
		explore.fade(0.0, fade)
		stem.fade(0.0, fade)
	_later(until_next(ref, "beat"), boss_in, "music")

## The fight is over: on the next bar line the stem leaves (or the theme hands back to the room's track), and a
## fight that felled an elite or a boss ends on the victory stinger.
func _leave_fight(now := false) -> void:
	var was := mode
	mode = "explore"
	boss_track = ""
	calm_t = 0.0
	_cancel("music")
	var f: Dictionary = SoundBank.section("music").get("fight", {})
	var ref: Lane = alt if alt.player.playing and alt.k > 0.0 else explore
	var bar := float(f.get("leave_fade_bars", 1.0)) * beat_s(ref.id) * float(_grid(ref.id).get("bar_beats", 4))
	var go := func():
		stem.fade(0.0, bar)
		explore.trim_db = 0.0
		explore.fade(1.0, bar)
		alt.fade(0.0, bar, true)
	if now: go.call()
	else: _later(until_next(ref, "bar"), go, "music")
	if not now and was != "explore" and fight_had_elite and clock - last_victory_t > 6.0:
		stinger(str(SoundBank.section("stingers").get("victory", "sting_victory")))
	fight_had_elite = false

func _play_alt(track: String, fade: float) -> void:
	if alt.id == track and alt.player.playing:
		alt.fade(1.0, fade)
		return
	var tmp := alt_old
	alt_old = alt
	alt = tmp
	alt_old.fade(0.0, fade, true)
	var st := _stream("music", track)
	alt.id = track
	if st == null: return
	alt.player.stream = st
	alt.base_db = _vol("music", track, -6.0)
	alt.k = 0.0
	alt.fade(1.0, fade)
	alt.player.play()

func _cancel(what: String) -> void:
	pending = pending.filter(func(p): return str(p.what) != what)

## What the music is doing (the audio suite reads it): the mode, the track, the stem's and the theme's levels and
## where they are going, and a move waiting for its beat.
func music_state() -> Dictionary:
	var waiting := ""
	for p in pending:
		if str(p.what) == "music": waiting = "music"
	return {"mode": mode, "track": current_music, "stem": stem.id, "stem_k": stem.k, "stem_target": stem.target,
		"explore_k": explore.k, "explore_target": explore.target, "explore_trim_db": explore.trim_db, "alt": alt.id,
		"alt_k": alt.k, "alt_target": alt.target, "boss": boss_track, "pending": waiting, "fighting": fighting, "calm_t": calm_t}

# ------------------------------------------------------------------ stingers
## A stinger (a quest done, a breakthrough, a rare find, an unlock, an elite, a victory) on the Music bus, the music
## ducked under it. One at a time: a lesser one waits for a greater one to end (a moment later it is dropped).
func stinger(id: String) -> void:
	if not enabled or id == "": return
	var st := _stream("sfx", id)
	if st == null: return
	if sting.player.playing and int(STING_RANK.get(sting.id, 0)) >= int(STING_RANK.get(id, 0)) and id != sting.id:
		sting_queue = id
		sting_queue_t = clock
		return
	sting.id = id
	sting.base_db = _vol("sfx", id, -6.0)
	sting.player.stream = st
	sting.player.play()
	_remember(id, sting.base_db, "Music")
	if id == "sting_victory": last_victory_t = clock
	duck("stinger", float(mix().get("duck", {}).get("stinger_db", -10.0)), float(SoundBank.entry(id).get("len_s", 2.0)) * 0.85)

# ------------------------------------------------------------------ beds
## The room's ambient bed: its base loops and the hour's layer, crossfaded from the last.
func bed(id: String, hour := "") -> void:
	var def := SoundBank.bed(id)
	if id == bed_id: return
	bed_id = id
	current_ambience = id
	var fade := float(SoundBank.section("beds").get("fade_s", 2.0))
	for l in bed_lanes:
		l.fade(0.0, fade, true)
		l.free_at_zero = true
	if def.is_empty(): return
	for b in def.get("bases", []): _bed_lane(str(b[0]), float(b[1]), "base")
	for role in ["day", "night"]:
		if str(def.get(role, "")) != "": _bed_lane(str(def[role]), 0.0, role)
	bed_hour = ""
	set_hour(hour if hour != "" else _hour(), fade)

func _bed_lane(sfx: String, db: float, role: String) -> void:
	var st := _stream("sfx", sfx)
	if st == null: return
	var l := _lane("Ambience")
	l.id = sfx
	l.base_db = _vol("sfx", sfx, -12.0) + db
	l.duck_share = float(mix().get("duck", {}).get("ambience_share", 0.5))
	l.player.stream = st
	l.player.set_meta("role", role)
	l.player.set_meta("bed", bed_id)
	# each loop from its own point, so a base and its layer never line up the same way twice
	l.player.play(randf() * maxf(0.0, st.get_length() - 0.1))
	bed_lanes.append(l)

## Follow an hour (TopdownLight's names: morning, day, evening, night, night_story, lamplit, dusk; or the clock's):
## the day and night layers come and go, the town quietens at night.
func set_hour(hour: String, fade := 3.0) -> void:
	if hour == bed_hour: return
	bed_hour = hour
	var layers := SoundBank.hour_layers(hour)
	var def := SoundBank.bed(bed_id)
	var night := layers.has("night")
	for l in bed_lanes:
		if l.free_at_zero or str(l.player.get_meta("bed", "")) != bed_id: continue
		var role := str(l.player.get_meta("role", "base"))
		if role == "base":
			l.trim_db = float(def.get("night_base_db", 0.0)) if night and not layers.has("day") else 0.0
			l.fade(1.0, fade)
		else:
			l.fade(db_to_linear(float(layers[role])) if layers.has(role) else 0.0, fade)

func _hour() -> String:
	if hour_source.is_valid(): return str(hour_source.call())
	return Clock.time_of_day()

## Old callers: an ambience mood names a bed.
func ambient(id: String) -> void:
	var b := SoundBank.section("beds")
	bed(str(b.get("ambience", {}).get(id, id)))

# ------------------------------------------------------------------ the tick
func _process(delta: float) -> void:
	advance(delta)

## Advance by `delta` seconds: the waiting moves, the fight, the fades, the ducking, the hour (the audio suite calls it
## with its own steps).
func advance(delta: float) -> void:
	clock += delta
	for p in pending.duplicate():
		p.t -= delta
		if p.t <= 0.0:
			pending.erase(p)
			p.fn.call()
	if enabled and Game and Game.active() != null: _fight_step(delta)
	for l in [explore, explore_old, stem, alt, alt_old] + bed_lanes: l.advance(delta)
	for l in bed_lanes.duplicate():
		if l.free_at_zero and l.k <= 0.0:
			bed_lanes.erase(l)
			l.player.queue_free()
	if sting_queue != "" and not sting.player.playing:
		if clock - sting_queue_t < 3.0: stinger(sting_queue)
		sting_queue = ""
	# ducking: the deepest hold wins, reached over attack_s and let go over release_s
	var target := 0.0
	for name in holds.keys():
		if float(holds[name].until) < clock: holds.erase(name)
		else: target = minf(target, float(holds[name].db))
	if not sting.player.playing: holds.erase("stinger")
	var d: Dictionary = mix().get("duck", {})
	var tc := float(d.get("attack_s", 0.08)) if target < duck_db else float(d.get("release_s", 0.9))
	duck_db += (target - duck_db) * clampf(delta / maxf(tc, 0.001), 0.0, 1.0)
	hour_check_t -= delta
	if hour_check_t <= 0.0 and bed_id != "":
		hour_check_t = 5.0
		set_hour(_hour())
	_apply_levels()

func _apply_levels() -> void:
	for l in [explore, explore_old, stem, alt, alt_old]:
		l.player.volume_db = l.db() + duck_db
	sting.player.volume_db = sting.base_db
	for l in bed_lanes:
		l.player.volume_db = l.db() + duck_db * l.duck_share

# ------------------------------------------------------------------ events
func _on_event(name: String, p: Dictionary) -> void:
	match name:
		"room_entered":
			var rid := str(p.get("room", ""))
			var room := ContentDB.room(rid)
			var doors: Array = SoundBank.section("world").get("door_types", [])
			var was := str(ContentDB.room(last_room).get("type", "")) if last_room != "" else ""
			if last_room != "" and rid != last_room:
				var w: Dictionary = SoundBank.section("world")
				# through a door (into a room indoors or out of one): it opens, and shuts behind the one leaving
				if str(room.get("type", "")) in doors or was in doors:
					play(str(w.get("door_open", "door_open")))
					if was in doors: _later(0.55, func(): play(str(w.get("door_close", "door_close")), "SFX", {"gain_db": -5.0}), "door")
				else: play("portal", "SFX", {"gain_db": -4.0})
			last_room = rid
			listener = Vector2.INF
			music(music_for_room(room))
			bed(SoundBank.bed_of(rid, room))
		"settings_changed": apply_settings()
		"actor_defeated":
			if str(p.get("victim_kind", "enemy")) == "enemy": foe_death(p)
		"attack_cancelled":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("into", "")) != "": weave()
		"loot_dropped":
			var at := Vector2(float(p.get("x", 0)), float(p.get("y", 0)))
			play(str(SoundBank.section("world").get("loot_drop", "loot_drop")), "SFX", {"at": at} if listener != Vector2.INF else {})
		"scene_started":
			play(str(SoundBank.section("world").get("scene_in", "scene_in")), "UI")
			duck("scene", float(mix().get("duck", {}).get("scene_db", -4.0)))
		"scene_ended": unduck("scene")
	if EVENT_SFX.has(name): play(EVENT_SFX[name], "UI" if name in UI_EVENTS else "SFX")
	var se: Dictionary = SoundBank.section("stinger_events")
	if se.has(name): stinger(str(SoundBank.section("stingers").get(str(se[name]), "")))

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT]:
		AudioServer.set_bus_mute(0, true)
	elif what in [NOTIFICATION_APPLICATION_RESUMED, NOTIFICATION_APPLICATION_FOCUS_IN]:
		AudioServer.set_bus_mute(0, false)
