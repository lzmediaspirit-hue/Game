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
			for entry in data.entries:
				if not (entry is Dictionary) or not entry.has("id"):
					load_errors.append("%s: entry without id" % table)
					continue
				if by_id.has(entry.id): load_errors.append("%s: duplicate id %s" % [table, entry.id])
				by_id[entry.id] = entry
				ordered.append(entry)
			tables[table] = by_id
			lists[table] = ordered
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

## "Qi Kindling 3 · Lv 12"
func realm_label(key: String) -> String:
	var r := realm(key)
	if r.is_empty(): return key
	return "%s · Lv %d" % [text("realm." + key), int(r.level)]

func item(id: String) -> Dictionary:
	var e := entry("items", id)
	if e.is_empty(): e = entry("artifacts", id)
	return e

func is_equipment(id: String) -> bool:
	return has_entry("artifacts", id)

func stat_const(path: String, fallback = 0.0):
	# Dotted lookup into stats.json, e.g. "crit.base".
	var node = config("stats")
	for part in path.split("."):
		if node is Dictionary and node.has(part): node = node[part]
		else: return fallback
	return node

## Dotted lookup into movement.json (S43: every traversal constant), e.g. "glide.qi_per_s".
func movement(path: String, fallback = 0.0):
	var node = config("movement")
	for part in path.split("."):
		if node is Dictionary and node.has(part): node = node[part]
		else: return fallback
	return node

func curve(path: String, fallback = 0.0):
	var node = config("curves")
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

# ---------------------------------------------------------------- validation
## Cross-reference validation (Part 7 · Data validation). Returns readable errors.
func validate() -> Array[String]:
	var errors: Array[String] = []
	errors.append_array(load_errors)
	var validator = load("res://scripts/core/data_validator.gd")
	if validator: errors.append_array(validator.validate(self))
	return errors
