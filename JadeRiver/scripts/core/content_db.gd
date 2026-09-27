extends Node
## S01 · Content database. Loads every data file once, validates cross references
## and serves read-only lookups by stable ID. Nothing here changes after boot.
##
## File shapes: a list table is {"schema_version": n, "entries": [{"id": ...}, ...]};
## a config table is {"schema_version": n, ...fields}. Rooms live in data/rooms/,
## dialogue trees in data/dialogue/, player-facing text in data/strings/en.json.

const DATA_DIR := "res://data/"
## Files that belong to the v0.13 engine and keep their original shape.
const LEGACY_FILES := ["parts.json", "poses.json", "world.json", "map_themes.json", "surface_masks.json", "movement_contracts.json"]

var tables: Dictionary = {}      # table -> {id: entry}
var lists: Dictionary = {}       # table -> [entry] in authored order
var configs: Dictionary = {}     # table -> Dictionary
var rooms: Dictionary = {}       # room id -> room data
var dialogue: Dictionary = {}    # dialogue id -> tree
var strings: Dictionary = {}     # key -> text
var parts: Dictionary = {}       # appearance catalogue (parts.json)
var realm_order: Array = []      # realm sub-level keys in ladder order
var realm_index: Dictionary = {} # key -> position in realm_order
var room_zone: Dictionary = {}   # room id -> zone id
var used_in: Dictionary = {}     # item id -> [recipe ids]
var load_errors: Array[String] = []
var loaded := false

func _ready() -> void:
	load_all()

func load_all() -> void:
	tables.clear(); lists.clear(); configs.clear(); rooms.clear(); dialogue.clear()
	strings.clear(); load_errors.clear(); realm_order.clear(); realm_index.clear()
	room_zone.clear(); used_in.clear()
	parts = _read_json(DATA_DIR + "parts.json")
	for file in DirAccess.get_files_at(DATA_DIR):
		if not file.ends_with(".json") or file in LEGACY_FILES: continue
		var data = _read_json(DATA_DIR + file)
		if not (data is Dictionary):
			load_errors.append("Unreadable data file: " + file)
			continue
		var table := file.get_basename()
		if data.has("entries"):
			var by_id := {}
			var ordered: Array = []
			var defaults: Dictionary = data.get("defaults", {})
			var memo := {}   # the table's merged pairs of layers (expand)
			for entry in data.entries:
				if not (entry is Dictionary) or not entry.has("id"):
					load_errors.append("%s: entry without id" % table)
					continue
				if not defaults.is_empty(): entry = expand(entry, defaults, memo)
				if by_id.has(entry.id): load_errors.append("%s: duplicate id %s" % [table, entry.id])
				by_id[entry.id] = entry
				ordered.append(entry)
			tables[table] = by_id
			lists[table] = ordered
			configs[table] = data   # a table's own constants sit beside its entries (tribulations.json, fates.json)
		else:
			configs[table] = data
	for file in DirAccess.get_files_at(DATA_DIR + "rooms/"):
		if not file.ends_with(".json"): continue
		var room = _read_json(DATA_DIR + "rooms/" + file)
		if room is Dictionary and room.has("id"):
			if rooms.has(room.id): load_errors.append("Duplicate room id " + room.id)
			rooms[room.id] = room
			room_zone[room.id] = str(room.get("zone", ""))
		else:
			load_errors.append("Unreadable room file: " + file)
	if DirAccess.dir_exists_absolute(DATA_DIR + "dialogue/"):
		for file in DirAccess.get_files_at(DATA_DIR + "dialogue/"):
			if not file.ends_with(".json"): continue
			var tree = _read_json(DATA_DIR + "dialogue/" + file)
			if tree is Dictionary:
				for id in tree.get("trees", {}):
					dialogue[id] = tree.trees[id]
	var en = _read_json(DATA_DIR + "strings/en.json")
	if en is Dictionary: strings = en.get("strings", {})
	for entry in lists.get("realms", []):
		realm_index[entry.key] = realm_order.size()
		realm_order.append(entry.key)
	for recipe in lists.get("recipes", []):
		for input in recipe.get("inputs", []):
			if not used_in.has(input.item): used_in[input.item] = []
			used_in[input.item].append(recipe.id)
	loaded = true

## P13a compact rows (technique_plan §7): a table may carry `defaults`, {key: {value: layer}}; each entry is its layers
## (the one its own `key` names, in order; dictionaries merge) with the entry's own keys over them, a dictionary of the
## entry merging one level into the layers' (technique_gen.compact writes them so). The layers merge two at a time and
## each merged pair is kept in `memo` (one per table: its rows share few pairs, a form with a ring, an element with a
## family), so a row costs a native copy, a small merge and a native merge of its own keys. The entry, fresh from the
## file, is used up.
static func expand(entry: Dictionary, defaults: Dictionary, memo := {}) -> Dictionary:
	var out := {}
	var keys: Array = defaults.keys()
	for i in range(0, keys.size(), 2):
		var v1 = entry.get(keys[i], "")
		var sel: String = str(i) + ":" + (str(int(v1)) if v1 is float else str(v1))
		if i + 1 < keys.size():
			var v2 = entry.get(keys[i + 1], "")
			sel += "|" + (str(int(v2)) if v2 is float else str(v2))
		if not memo.has(sel):
			var pair := {}
			for key in keys.slice(i, i + 2):
				var kv = entry.get(key, "")
				var layer = defaults[key].get(str(int(kv)) if kv is float else str(kv))
				if layer is Dictionary: _merge(pair, layer)
			memo[sel] = pair
		if out.is_empty(): out = (memo[sel] as Dictionary).duplicate(true)
		else: _merge(out, memo[sel])
	if not memo.has(""):   # the keys some layer gives a dictionary to (hitbox, vfx, mastery)
		var nested: Array = []
		for key in defaults:
			for layer in (defaults[key] as Dictionary).values():
				for k in layer:
					if layer[k] is Dictionary and not nested.has(k): nested.append(k)
		memo[""] = nested
	for k in memo[""]:
		var ev = entry.get(k)
		if ev is Dictionary and out.get(k) is Dictionary:
			var d: Dictionary = out[k]
			d.merge(ev, true)
			entry[k] = d
	out.merge(entry, true)
	return out

static func _merge(into: Dictionary, src: Dictionary) -> void:
	for k in src:
		var v = src[k]
		if v is Dictionary and into.get(k) is Dictionary:
			var d: Dictionary = (into[k] as Dictionary).duplicate()
			_merge(d, v)
			into[k] = d
		else:
			into[k] = v.duplicate(true) if v is Dictionary or v is Array else v

func _read_json(path: String):
	if not FileAccess.file_exists(path): return null
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path)) != OK:
		load_errors.append("%s: JSON error line %d: %s" % [path, parser.get_error_line(), parser.get_error_message()])
		return null
	return parser.data

# ---------------------------------------------------------------- lookups
func entry(table: String, id: String) -> Dictionary:
	return tables.get(table, {}).get(id, {})

func has_entry(table: String, id: String) -> bool:
	return tables.get(table, {}).has(id)

func all(table: String) -> Array:
	return lists.get(table, [])

func config(name: String) -> Dictionary:
	return configs.get(name, {})

func room(id: String) -> Dictionary:
	return rooms.get(id, {})

func zone(id: String) -> Dictionary:
	return entry("zones", id)

func zone_of_room(room_id: String) -> Dictionary:
	return zone(room_zone.get(room_id, ""))

func realm(key: String) -> Dictionary:
	return tables.get("realms", {}).get(key, {})

func level_of(key: String) -> int:
	return int(realm(key).get("level", 0))

func realm_position(key: String) -> int:
	return int(realm_index.get(key, -1))

func realm_key_for_level(level: int) -> String:
	var best := "mortal"
	for key in realm_order:
		if int(realm(key).level) <= level: best = key
	return best

func next_realm(key: String) -> String:
	var i := realm_position(key)
	if i < 0 or i + 1 >= realm_order.size(): return ""
	return realm_order[i + 1]

## "Qi Kindling 3 · Lv 12": the stage's first Level, or `level` for a character inside it. From Heaven Glimpse a stage
## spans three Levels (Inner Heaven five), so a character's own label passes ProgressionRules.level (B15).
func realm_label(key: String, level := -1) -> String:
	var r := realm(key)
	if r.is_empty(): return key
	return text("ui.realm_label") % [text("realm." + key), level if level >= 0 else int(r.level)]

## A training-sect rank's name from sect_ranks.json ("inner_disciple" → "Inner Disciple"), not its id capitalised (I10).
func rank_name(id: String) -> String:
	for rk in config("sect_ranks").get("ranks", []):
		if str(rk.get("id", "")) == id: return str(rk.get("name", id))
	return id.replace("_", " ").capitalize()

func item(id: String) -> Dictionary:
	var e := entry("items", id)
	if e.is_empty(): e = entry("artifacts", id)
	return e

func is_equipment(id: String) -> bool:
	return has_entry("artifacts", id)

## Dotted lookup into stats.json, e.g. "crit.base".
func stat_const(path: String, fallback = 0.0):
	return _dotted(config("stats"), path, fallback)

## Dotted lookup into movement.json (S43: every traversal constant), e.g. "glide.qi_per_s".
func movement(path: String, fallback = 0.0):
	return _dotted(config("movement"), path, fallback)

## Dotted lookup into curves.json, e.g. "resets.daily_hour".
func curve(path: String, fallback = 0.0):
	return _dotted(config("curves"), path, fallback)

func _dotted(node, path: String, fallback):
	for part in path.split("."):
		if node is Dictionary and node.has(part): node = node[part]
		else: return fallback
	return node

## Player-facing text by key (S40). Unknown keys fall back to a readable form so
## missing strings are visible in testing but never crash.
func text(key: String, args: Dictionary = {}) -> String:
	var value: String = strings.get(key, "")
	if value == "":
		value = key.get_slice(".", key.get_slice_count(".") - 1).replace("_", " ").capitalize()
	for k in args:
		value = value.replace("{" + str(k) + "}", str(args[k]))
	return value

func name_of(table: String, id: String) -> String:
	var e := entry(table, id)
	if table == "rooms": e = room(id)
	if e.has("name"): return str(e.name)
	return text(table.trim_suffix("s") + "." + id)

func item_name(id: String) -> String:
	var e := item(id)
	return str(e.get("name", id.replace("_", " ").capitalize()))
