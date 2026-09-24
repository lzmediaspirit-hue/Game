extends Node
## `Audio` autoload (S36): buses Master, Music, Ambience, SFX, UI; music per room
## type with a 1 s crossfade; sound effects mapped from events. Presentation only:
## no rule code plays audio. Missing files are silent.

const BUSES := ["Music", "Ambience", "SFX", "UI"]
const EVENT_SFX := {"quest_accepted": "quest_accept", "quest_completed": "quest_complete", "system_unlocked": "unlock",
	"level_changed": "level", "mail_received": "mail", "meditation_started": "meditate", "qi_backlash": "backlash",
	"node_gathered": "gather", "fish_caught": "fish_bite", "craft_completed": "forge", "room_entered": "portal",
	"boss_phase": "boss_roar", "field_boss_spawned": "boss_roar", "item_bought": "coin", "item_sold": "coin"}

var sfx_players: Array = []
var music_a: AudioStreamPlayer
var music_b: AudioStreamPlayer
var ambience: AudioStreamPlayer
var current_music := ""
var current_ambience := ""
var streams: Dictionary = {}
var fade := 0.0
var enabled := true

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for bus in BUSES:
		if AudioServer.get_bus_index(bus) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, bus)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")
	for i in 10:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		sfx_players.append(p)
	music_a = AudioStreamPlayer.new()
	music_b = AudioStreamPlayer.new()
	ambience = AudioStreamPlayer.new()
	for p in [music_a, music_b]:
		p.bus = "Music"
		add_child(p)
	ambience.bus = "Ambience"
	add_child(ambience)
	GameEvents.event.connect(_on_event)
	apply_settings()

func apply_settings() -> void:
	var s: Dictionary = Game.account.settings if Game else {}
	for pair in [["Music", "music"], ["Ambience", "ambience"], ["SFX", "sfx"], ["UI", "ui"]]:
		var idx := AudioServer.get_bus_index(pair[0])
		if idx >= 0: AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(0.0001, float(s.get(pair[1], 0.7)))))

func _stream(kind: String, id: String) -> AudioStream:
	var key := kind + ":" + id
	if streams.has(key): return streams[key]
	var e: Dictionary = ContentDB.config("audio").get(kind, {}).get(id, {})
	var path := str(e.get("file", ""))
	var st: AudioStream = load(path) if path != "" and ResourceLoader.exists(path) else null
	if st is AudioStreamWAV and (kind == "music" or id.ends_with("_ambience")):
		var wav := st as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = int(wav.data.size() / 2)
	streams[key] = st
	return st

func play(id: String, bus := "SFX") -> void:
	if not enabled or id == "": return
	var st := _stream("sfx", id)
	if st == null: return
	var vol := float(ContentDB.config("audio").get("sfx", {}).get(id, {}).get("volume_db", -4))
	for p in sfx_players:
		if not p.playing:
			p.stream = st
			p.bus = bus
			p.volume_db = vol
			p.pitch_scale = randf_range(0.95, 1.05)
			p.play()
			return

func ui(id := "ui_tap") -> void:
	play(id, "UI")

func music(id: String) -> void:
	if id == current_music: return
	current_music = id
	var st := _stream("music", id)
	var next := music_b if music_a.playing else music_a
	var prev := music_a if next == music_b else music_b
	if st:
		next.stream = st
		next.volume_db = -40.0
		next.play()
	var tw := create_tween().set_parallel(true)
	if st: tw.tween_property(next, "volume_db", float(ContentDB.config("audio").get("music", {}).get(id, {}).get("volume_db", -6)), 1.0)
	if prev.playing:
		tw.tween_property(prev, "volume_db", -40.0, 1.0)
		tw.chain().tween_callback(prev.stop)

func ambient(id: String) -> void:
	if id == current_ambience: return
	current_ambience = id
	var st := _stream("sfx", id) if id != "" else null
	if st == null:
		ambience.stop()
		return
	ambience.stream = st
	ambience.volume_db = -14.0
	ambience.play()

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

func _on_event(name: String, p: Dictionary) -> void:
	if name == "room_entered":
		var room := ContentDB.room(str(p.get("room", "")))
		music(music_for_room(room))
		ambient(str(room.get("ambience", "")))
	if name == "settings_changed": apply_settings()
	if EVENT_SFX.has(name): play(EVENT_SFX[name], "UI" if name in ["quest_accepted", "quest_completed", "system_unlocked", "mail_received"] else "SFX")
	if name == "actor_defeated": play("enemy_die")

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT]:
		AudioServer.set_bus_mute(0, true)
	elif what in [NOTIFICATION_APPLICATION_RESUMED, NOTIFICATION_APPLICATION_FOCUS_IN]:
		AudioServer.set_bus_mute(0, false)
