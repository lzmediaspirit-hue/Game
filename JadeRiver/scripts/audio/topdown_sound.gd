class_name TopdownSound
extends Node
## Decision 43's sound pass in a room on the height grid (docs/redesign/sound.md): what the top-down world's sounds
## need from its view, read each frame, played through the `Audio` autoload.
##   - The listener: the player's feet, so foes, villagers and the world's sounds fall off with distance.
##   - The hour: the room's light (TopdownLight.look), so the bed's day and night layers follow what the eye sees.
##   - The player's feet: a step on each frame of the walk or run where a foot lands (SoundBank.contact_frames: the
##     data's fractions of the cycle), on the surface under it (a paint mark, a prop's top, water); a landing by its
##     height and surface, a splash into water.
##   - Others' feet: the foes that walk (on their sheet's walk cycle, else a cadence) and the villagers a route moves
##     (their walk's own contacts), quieter, at their place.
## Its world calls landed() and splashed() from the motor's events; the rest it reads.

var world                       ## the TopdownWorld
var last_frame := -1
var last_anim := ""
var foe_phase: Dictionary = {}  ## foe uid -> [cycle phase 0..1, last contact index]
var npc_frame: Dictionary = {}  ## villager node id -> last frame
var people: Array = []          ## the Person figures in the room (refreshed now and then)
var people_t := 0.0

func _init(w) -> void:
	world = w
	name = "Sound"

func _ready() -> void:
	Audio.hour_source = hour

func _exit_tree() -> void:
	if Audio.hour_source == Callable(self, "hour"): Audio.hour_source = Callable()
	Audio.listener = Vector2.INF

## The room's hour as its light shows it (morning, day, evening, night; a night room's night_story; lamplit indoors).
func hour() -> String:
	if world == null or world.room == null: return Clock.time_of_day()
	var def: Dictionary = Game.room_rt.def if world.live and Game.room_rt != null and Game.room_rt.topdown == world.room else world.room.def
	return str(TopdownLight.look(def, -1.0 if TopdownAtmosphere.extras_on() else 0.375).hour)

func surface(p: Vector2, z := INF) -> String:
	return SoundBank.surface_at(world.room, p, z)

func _process(delta: float) -> void:
	if world == null or world.player == null or world.player.motor == null: return
	var m: TopdownMotor = world.player.motor
	Audio.listener = m.pos
	_player_feet()
	_foe_feet(delta)
	people_t -= delta
	if people_t <= 0.0:
		people_t = 1.0
		people = world.sorted.get_children().filter(func(n): return n is TopdownPlaces.Figure and n.art is TopdownPlaces.Person)
	_people_feet()

## A step on each contact frame of the walk or the run, on the surface under the feet.
func _player_feet() -> void:
	var pl = world.player
	var anim := str(pl.anim)
	var m: TopdownMotor = pl.motor
	if not anim in ["walk", "run"] or not m.grounded:
		last_anim = anim
		last_frame = -1
		return
	var frame := int(pl.frame)
	if anim == last_anim and frame == last_frame: return
	var entering := anim != last_anim
	var from := last_frame
	last_anim = anim
	last_frame = frame
	var frames := int(TopdownFigure.spec(str(pl.pose)).get("frames", 8))
	if entering:
		if frame == 0: Audio.step(surface(m.pos, m.z), Vector2.INF, "player", anim)
		return
	# a contact frame reached since the last frame drawn (a slow frame may skip past it: it still steps, once)
	for c in SoundBank.contact_frames(anim, frames):
		if posmod(int(c) - from - 1, frames) < posmod(frame - from, frames):
			Audio.step(surface(m.pos, m.z), Vector2.INF, "player", anim)
			return

## Foes that walk: a step at each half of their walk cycle (the foe sheet's walk action; a cadence without one),
## at their place; none for the ones that fly or hover.
func _foe_feet(delta: float) -> void:
	if Game.room_rt == null: return
	var st := SoundBank.section("steps")
	var species: Dictionary = world.room.tileset.get("foes", {}).get("species", {})
	var min_speed := float(st.get("foe_min_speed", 18.0))
	var seen := {}
	for e in Game.room_rt.living_enemies():
		seen[e.uid] = true
		if e.hover > 2.0 or bool(e.def.get("movement", {}).get("fly", false)) or str(e.action) != "walk" or e.velocity.length() < min_speed:
			foe_phase.erase(e.uid)
			continue
		var cycle := float(st.get("foe_cadence_s", 0.34)) * 2.0
		var walk: Dictionary = species.get(e.def_id, {}).get("actions", {}).get("walk", {})
		if not walk.is_empty():
			var fr: Dictionary = walk.get("frames", {})
			var n := 0
			for k in fr: n = maxi(n, (fr[k] as Array).size())
			if n > 0: cycle = float(n) / maxf(1.0, float(walk.get("fps", 6)))
		var ph: Array = foe_phase.get(e.uid, [0.0, -1])
		ph[0] = fposmod(float(ph[0]) + delta / maxf(0.1, cycle), 1.0)
		var contacts: Array = st.get("contacts", {}).get("walk", [0.0, 0.5])
		var at := -1
		for i in contacts.size():
			if float(ph[0]) >= float(contacts[i]): at = i
		if at != int(ph[1]):
			ph[1] = at
			if at >= 0: Audio.step(surface(e.plane, e.altitude), e.plane, "foe", "walk")
		foe_phase[e.uid] = ph
	for uid in foe_phase.keys():
		if not seen.has(uid): foe_phase.erase(uid)

## Villagers a route walks: a step on their walk's contact frames, where they are.
func _people_feet() -> void:
	for f in people:
		if not is_instance_valid(f) or not f.visible: continue
		var art = f.art
		var key: int = f.get_instance_id()
		if str(art.action) != "walk":
			npc_frame.erase(key)
			continue
		var fr := TopdownFigure.frame_at("walk", float(art.t))
		var from := int(npc_frame.get(key, -1))
		if from == fr: continue
		npc_frame[key] = fr
		if from < 0: continue
		var n := int(TopdownFigure.spec("walk").get("frames", 8))
		for c in SoundBank.contact_frames("walk", n):
			if posmod(int(c) - from - 1, n) < posmod(fr - from, n):
				Audio.step_at(surface(f.plane), f.plane, "npc")
				break

## A jump: the push-off scuffs the surface it leaves, under the jump's own whoosh.
func jumped() -> void:
	var m: TopdownMotor = world.player.motor
	Audio.play(str(SoundBank.section("steps").get("jump", "jump")), "SFX", {"player": true})
	Audio.step(surface(m.pos, m.z), Vector2.INF, "player", "walk")

## The motor's landing: by its height and the surface under the feet.
func landed(fall: float) -> void:
	var m: TopdownMotor = world.player.motor
	Audio.land(surface(m.pos, m.z), fall)

## A fall into water.
func splashed(fall: float) -> void:
	if fall > 12.0: Audio.play(str(SoundBank.section("world").get("splash", "splash")), "SFX", {"player": true})
	else: Audio.step(SoundBank.section("steps").get("water", "water"), Vector2.INF, "player", "run")
