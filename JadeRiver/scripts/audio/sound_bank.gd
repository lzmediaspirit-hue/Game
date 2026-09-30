class_name SoundBank
extends RefCounted
## Decision 43's sound pass (docs/redesign/sound.md): the lookups over data/sound.json (tools/data/sound.py) and the
## audio manifest data/audio.json (tools/audio/build_audio.py) that AudioDirector and TopdownSound share. Pure
## functions of the data: which surface lies under the feet, a foe's body, voice and death, a weapon's sound family,
## the bed of a room and the layers of an hour, a sound's voice rule.

static func cfg() -> Dictionary:
	return ContentDB.config("sound")

static func section(name: String) -> Dictionary:
	return cfg().get(name, {})

static func manifest() -> Dictionary:
	return ContentDB.config("audio")

## Is there a file for this sound id (an effect or a music track)?
static func has_sound(id: String) -> bool:
	var m := manifest()
	return m.get("sfx", {}).has(id) or m.get("music", {}).has(id)

static func entry(id: String) -> Dictionary:
	var m := manifest()
	return m.get("sfx", {}).get(id, m.get("music", {}).get(id, {}))

# ------------------------------------------------------------------ steps
## The surface under a ground point of a room on the height grid: a prop's top the body stands on (a roof, crates),
## water (wading), else the cell's paint mark (grass, dirt, paving, planks, reeds ...), else the default.
static func surface_at(room: TopdownRoom, p: Vector2, z := INF) -> String:
	var st := section("steps")
	var fallback := str(st.get("default", "dirt"))
	if room == null: return fallback
	var c := TopdownRoom.cell_of(p)
	if not room.inside(c.x, c.y): return fallback
	var top := room.top_at(c.x, c.y)
	if not top.is_empty() and (z == INF or z >= float(top.top) * TopdownRoom.LEVEL - 8.0):
		return str(st.get("prop_tops", {}).get(str(top.kind), "wood"))
	if room.is_water(c.x, c.y): return str(st.get("water", "water"))
	return str(st.get("paint", {}).get(room.paint_at(c.x, c.y), fallback))

## A surface's footstep round robin and its landing.
static func steps_of(surface: String) -> Array:
	var s: Dictionary = section("steps").get("surfaces", {})
	return s.get(surface, s.get(str(section("steps").get("default", "dirt")), {})).get("steps", [])

static func land_of(surface: String) -> String:
	var s: Dictionary = section("steps").get("surfaces", {})
	return str(s.get(surface, s.get(str(section("steps").get("default", "dirt")), {})).get("land", "land"))

## Where in a walk or run cycle a foot lands: the frames of a `frames`-long cycle (the fractions in the data, so a
## cycle drawn with more frames keeps its contacts).
static func contact_frames(gait: String, frames: int) -> Array:
	var out: Array = []
	for f in section("steps").get("contacts", {}).get(gait, [0.0, 0.5]):
		out.append(int(round(float(f) * frames)) % maxi(1, frames))
	return out

# ------------------------------------------------------------------ hits and foes
## A weapon family (weapon_families.json) as its sound family (sword, sabre, spear, fan, brush, flute, bell, bow, fists).
static func family_sound(weapon_family: String) -> String:
	return str(section("hits").get("family_of", {}).get(weapon_family, "fists"))

## A foe's blow as a weapon's sound family (claws and jaws as fists, a bandit's blade as a sword).
static func foe_family(def: Dictionary) -> String:
	return str(section("hits").get("foe_family", {}).get(str(def.get("race", "beast")), "fists"))

static func element_sound(element: String) -> String:
	return str(section("hits").get("element_of", {}).get(element, "qi"))

static func _by(table: Dictionary, def: Dictionary, prefix: String, fallback: String) -> String:
	var id := str(def.get("id", ""))
	if table.get(prefix, {}).has(id): return str(table[prefix][id])
	var nature := str(def.get("nature", ""))
	if table.get(prefix + "_by_nature", {}).has(nature): return str(table[prefix + "_by_nature"][nature])
	return str(table.get(prefix + "_by_race", {}).get(str(def.get("race", "")), fallback))

## A foe's body when struck: flesh, shell, wood (puppets, constructs, paper) or slime (slime, water, the Hollow).
static func body_of(def: Dictionary) -> String:
	return _by(section("foes"), def, "body", "flesh")

## A foe's voice as it winds up (tell_beast, tell_human, tell_construct, tell_spirit, tell_water).
static func tell_of(def: Dictionary) -> String:
	return _by(section("foes"), def, "tell", "tell_beast")

## A foe's death: by its race or nature where they say (a ghost dissolves), else by its body.
static func death_of(def: Dictionary) -> String:
	var f := section("foes")
	var nature := str(def.get("nature", ""))
	if f.get("death_by_nature", {}).has(nature): return str(f.death_by_nature[nature])
	var race := str(def.get("race", ""))
	if f.get("death_by_race", {}).has(race): return str(f.death_by_race[race])
	return str(f.get("death_by_body", {}).get(body_of(def), "die_flesh"))

# ------------------------------------------------------------------ beds
## The bed of a room: by its id, its ambience mood, its type, its id's area prefix, else the default.
static func bed_of(room_id: String, def: Dictionary) -> String:
	var b := section("beds")
	if b.get("rooms", {}).has(room_id): return str(b.rooms[room_id])
	var mood := str(def.get("ambience", ""))
	if b.get("ambience", {}).has(mood): return str(b.ambience[mood])
	var kind := str(def.get("type", ""))
	if b.get("types", {}).has(kind): return str(b.types[kind])
	for pre in b.get("prefix", {}):
		if room_id.begins_with(str(pre)): return str(b.prefix[pre])
	return str(b.get("default", "field"))

static func bed(bed_id: String) -> Dictionary:
	return section("beds").get("beds", {}).get(bed_id, {})

## The layer levels of an hour ({"day": dB, "night": dB}; a layer absent is silent).
static func hour_layers(hour: String) -> Dictionary:
	return section("beds").get("hours", {}).get(hour, {"day": 0.0})

# ------------------------------------------------------------------ the mix
## A sound's voice rule [prefix, priority, most at once, least gap between starts]: the first whose prefix it starts
## with.
static func voice_rule(id: String) -> Array:
	for r in section("mix").get("voices", {}).get("rules", []):
		if id.begins_with(str(r[0])): return r
	return ["", 45, 3, 0.03]

# ------------------------------------------------------------------ the living world (decision 44)
## A life or place sound's takes, which the director plays in turn ([id] when it has one).
static func takes_of(id: String) -> Array:
	var t: Array = section("life").get("takes", {}).get(id, [])
	return t if not t.is_empty() else [id]

## Every sound the living world and the places can ask for: the critters' and the blows' (data/sound.json `life`), each
## work cue of `cues` (data/topdown/life.json) as "life_work_<cue>", the places'.
## Test hook: audio_tests checks each has a file.
static func life_ids(cues: Array) -> Array:
	var l := section("life")
	var out: Array = []
	out.append_array(l.get("critters", []))
	for c in cues: out.append("life_work_" + str(c))
	out.append_array(l.get("blows", []))
	out.append_array(l.get("places", []))
	return out

## Every sound id data/sound.json names (the audio suite checks each has a file).
## Test hook: audio_tests.
static func named_ids() -> Array:
	var out := {}
	_collect(cfg(), out, false)
	return out.keys()

static func _collect(node, out: Dictionary, in_voices: bool) -> void:
	if node is Dictionary:
		for k in node:
			if str(k) in ["voices", "_note", "hours", "calm_states", "alias", "rooms", "ambience", "types", "prefix", "paint", "prop_tops", "materials"]: continue
			_collect(node[k], out, in_voices)
	elif node is Array:
		for v in node: _collect(v, out, in_voices)
	elif node is String:
		var s := str(node)
		for pre in ["hit_", "step_", "land", "swing_", "cast_", "tell", "die_", "bed_", "sting_", "door_", "talk_", "boss_", "life_", "place_"]:
			if s.begins_with(pre): out[s] = true
		if s in ["hurt", "jump", "splash", "loot_drop", "bark", "scene_in"]: out[s] = true
