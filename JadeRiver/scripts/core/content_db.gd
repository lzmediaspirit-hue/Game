extends Node
## S01 · Content database. Reads the data files, validates cross references and serves read-only lookups by stable ID.
## Nothing here changes once read.
##
## File shapes: a list table is {"schema_version": n, "entries": [{"id": ...}, ...]};
## a config table is {"schema_version": n, ...fields}. Rooms live in data/rooms/,
## dialogue trees in data/dialogue/, player-facing text in data/strings/en.json.
##
## BUG-11 (decision 45, S4): the game's thread no longer reads every table at boot (techniques.json alone took 133 to
## 191 ms). It reads only the realms, the recipes (their indexes) and the strings; a loading thread reads the rest one
## table at a time beside the boot, and a lookup that comes before the thread has its table reads it there and then
## (never waiting on the thread). Every lookup answers as it did when boot read everything: the same rows, the same
## order, the same errors. Reading `tables`, `lists`, `configs` or `load_errors` whole reads every table first.

const DATA_DIR := "res://data/"
## Files that keep their own shape outside the tables: the looks' catalogue (parts.json, ContentDB.parts) and the v0.13
## street tools/data/world.py builds Gate Street from (world.json).
const LEGACY_FILES := ["parts.json", "world.json"]
## The tables boot reads: the ladder's and the recipes' indexes are built from them (realm_order, used_in).
const AT_BOOT := ["realms", "recipes"]
## The groups read whole, beside the tables (named so that no data file can be).
const ROOMS := "@rooms"
const DIALOGUE := "@dialogue"
const PARTS := "@parts"

var tables: Dictionary:          # table -> {id: entry}
	get:
		_read_all()
		return _tables
var lists: Dictionary:           # table -> [entry] in authored order
	get:
		_read_all()
		return _lists
var configs: Dictionary:         # table -> Dictionary
	get:
		_read_all()
		return _configs
var rooms: Dictionary:           # room id -> room data
	get:
		if not _rooms_in: _read(ROOMS)
		return _rooms
var dialogue: Dictionary:        # dialogue id -> tree
	get:
		if _unread.has(DIALOGUE): _read(DIALOGUE)
		return _dialogue
var strings: Dictionary = {}     # key -> text
var parts: Dictionary:           # appearance catalogue (parts.json)
	get:
		if _unread.has(PARTS): _read(PARTS)
		return _parts
var realm_order: Array = []      # realm sub-level keys in ladder order
var realm_index: Dictionary = {} # key -> position in realm_order
var _realm_for_level: Dictionary = {} # level -> realm_key_for_level (a foe's stats ask it at every blow)
var room_zone: Dictionary:       # room id -> zone id
	get:
		if not _rooms_in: _read(ROOMS)
		return _room_zone
var used_in: Dictionary = {}     # item id -> [recipe ids]
var load_errors: Array[String]:
	get:
		_read_all()
		return _load_errors
var loaded := false

var _tables: Dictionary = {}
var _lists: Dictionary = {}
var _configs: Dictionary = {}
var _rooms: Dictionary = {}
var _dialogue: Dictionary = {}
var _parts: Dictionary = {}
var _room_zone: Dictionary = {}
var _load_errors: Array[String] = []
var _files: Array = []           # the tables in the data folder's order (a whole read keeps them in it)
var _unread: Dictionary = {}     # table or group -> true until it is read
var _rooms_in := false           # the rooms are read (asked at every room lookup)
var _reader: _Reader = null      # the loading thread's work, while it runs

func _ready() -> void:
	load_all()

## Forget every table and start reading again (boot): AT_BOOT's tables and the strings now, the rest on the loading
## thread or when asked for.
func load_all() -> void:
	_stop_reader()
	_tables.clear(); _lists.clear(); _configs.clear(); _rooms.clear(); _dialogue.clear(); _parts = {}
	strings.clear(); _load_errors.clear(); realm_order.clear(); realm_index.clear(); _realm_for_level.clear()
	_stats_at.clear(); _movement_at.clear(); _curves_at.clear()
	_room_zone.clear(); used_in.clear(); _files.clear(); _unread.clear(); _rooms_in = false
	for file in DirAccess.get_files_at(DATA_DIR):
		if not file.ends_with(".json") or file in LEGACY_FILES: continue
		_files.append(file.get_basename())
		_unread[file.get_basename()] = true
	for group in [PARTS, ROOMS, DIALOGUE]: _unread[group] = true
	for table in AT_BOOT: _read(table)
	var errors: Array[String] = []
	var en = _parse(DATA_DIR + "strings/en.json", errors)
	_load_errors.append_array(errors)
	if en is Dictionary: strings = en.get("strings", {})
	for entry in _lists.get("realms", []):
		realm_index[entry.key] = realm_order.size()
		realm_order.append(entry.key)
	for recipe in _lists.get("recipes", []):
		for input in recipe.get("inputs", []):
			if not used_in.has(input.item): used_in[input.item] = []
			used_in[input.item].append(recipe.id)
	loaded = true
	_reader = _Reader.new()
	if _unread.has("techniques"): _reader.todo.append("techniques")   # the largest first
	for t in _files: if _unread.has(t) and t != "techniques": _reader.todo.append(t)
	for g in [ROOMS, DIALOGUE, PARTS]: if _unread.has(g): _reader.todo.append(g)
	_reader.thread.start(_work.bind(_reader), Thread.PRIORITY_LOW)
	set_process(true)

## Each frame, what the loading thread has read is handed over, until it is done.
func _process(_delta: float) -> void:
	if _reader == null:
		set_process(false)
		return
	var got := _reader.take()
	for t in got: _install(t, got[t])
	if _reader.finished():
		_stop_reader()
		set_process(false)

func _exit_tree() -> void:
	_stop_reader()

func _stop_reader() -> void:
	if _reader == null: return
	_reader.stop()
	if _reader.thread.is_started(): _reader.thread.wait_to_finish()
	var got := _reader.take()
	for t in got: _install(t, got[t])
	_reader = null

## Read `table` (or a group) now: the loading thread's copy when it has it, else read here.
func _read(table: String) -> void:
	if not _unread.has(table): return
	var got = _reader.claim(table) if _reader != null else null
	_install(table, got if got != null else _read_table(table))

## Every table read (a whole `tables`, `lists`, `configs` or `load_errors` was asked for).
func _read_all() -> void:
	if _unread.is_empty(): return
	for t in _files: _read(t)
	for g in [PARTS, ROOMS, DIALOGUE]: _read(g)

func _install(table: String, got: Dictionary) -> void:
	if not _unread.has(table): return
	_unread.erase(table)
	_load_errors.append_array(got.errors)
	match table:
		ROOMS:
			_rooms.merge(got.rooms)
			_room_zone.merge(got.room_zone)
			_rooms_in = true
		DIALOGUE: _dialogue.merge(got.dialogue)
		PARTS: _parts = got.parts if got.parts is Dictionary else {}
		_:
			if got.has("by_id"):
				_tables[table] = got.by_id
				_lists[table] = got.ordered
			if got.has("config"): _configs[table] = got.config
	# The last one in: the tables are kept in the data folder's order, as a boot that read everything left them.
	if _unread.is_empty():
		for d in [_tables, _lists, _configs]:
			var by_file := {}
			for t in _files: if d.has(t): by_file[t] = d[t]
			d.clear()
			d.merge(by_file)

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

static func _parse(path: String, errors: Array[String]):
	if not FileAccess.file_exists(path): return null
	var parser := JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path)) != OK:
		errors.append("%s: JSON error line %d: %s" % [path, parser.get_error_line(), parser.get_error_message()])
		return null
	return parser.data

## One table (or group) read from its files, as boot read it: a list table's rows expanded and indexed, with the errors
## met. Run on the loading thread (_work) or the game's own (_read): it touches nothing but its files.
static func _read_table(t: String) -> Dictionary:
	var errors: Array[String] = []
	var got := {"errors": errors}
	match t:
		ROOMS:
			var rooms := {}
			var zones := {}
			for file in DirAccess.get_files_at(DATA_DIR + "rooms/"):
				if not file.ends_with(".json"): continue
				var room = _parse(DATA_DIR + "rooms/" + file, errors)
				if room is Dictionary and room.has("id"):
					if rooms.has(room.id): errors.append("Duplicate room id " + room.id)
					rooms[room.id] = room
					zones[room.id] = str(room.get("zone", ""))
				else:
					errors.append("Unreadable room file: " + file)
			got.rooms = rooms
			got.room_zone = zones
		DIALOGUE:
			var trees := {}
			if DirAccess.dir_exists_absolute(DATA_DIR + "dialogue/"):
				for file in DirAccess.get_files_at(DATA_DIR + "dialogue/"):
					if not file.ends_with(".json"): continue
					var tree = _parse(DATA_DIR + "dialogue/" + file, errors)
					if tree is Dictionary:
						for id in tree.get("trees", {}):
							trees[id] = tree.trees[id]
			got.dialogue = trees
		PARTS:
			got.parts = _parse(DATA_DIR + "parts.json", errors)
		_:
			var data = _parse(DATA_DIR + t + ".json", errors)
			if not (data is Dictionary):
				errors.append("Unreadable data file: " + t + ".json")
				return got
			if data.has("entries"):
				var by_id := {}
				var ordered: Array = []
				var defaults: Dictionary = data.get("defaults", {})
				var memo := {}   # the table's merged pairs of layers (expand)
				for entry in data.entries:
					if not (entry is Dictionary) or not entry.has("id"):
						errors.append("%s: entry without id" % t)
						continue
					if not defaults.is_empty(): entry = expand(entry, defaults, memo)
					if by_id.has(entry.id): errors.append("%s: duplicate id %s" % [t, entry.id])
					by_id[entry.id] = entry
					ordered.append(entry)
				got.by_id = by_id
				got.ordered = ordered
			got.config = data   # a table's own constants sit beside its entries (tribulations.json, fates.json)
	return got

## The loading thread: the reader's list read one table at a time, each skipped when the game has claimed it.
static func _work(reader: _Reader) -> void:
	while true:
		var t := reader.next()
		if t == "": break
		reader.put(t, _read_table(t))

## What the loading thread and the game share, under one lock: the thread's list, what each side has claimed, and what
## the thread has read and not handed over yet.
class _Reader extends RefCounted:
	var thread := Thread.new()
	var todo: Array = []
	var _mutex := Mutex.new()
	var _claimed := {}      # table -> true: read, or being read, by one side
	var _done := {}         # table -> what the thread read
	var _stop := false
	var _over := false

	## The thread's next table to read ("" when there is none left, or it was told to stop).
	func next() -> String:
		_mutex.lock()
		var t := ""
		while not _stop and not todo.is_empty():
			var n: String = todo.pop_front()
			if _claimed.has(n): continue
			_claimed[n] = true
			t = n
			break
		_over = t == ""
		_mutex.unlock()
		return t

	func put(t: String, got: Dictionary) -> void:
		_mutex.lock()
		_done[t] = got
		_mutex.unlock()

	func stop() -> void:
		_mutex.lock()
		_stop = true
		_mutex.unlock()

	func finished() -> bool:
		_mutex.lock()
		var f := _over
		_mutex.unlock()
		return f

	## What the thread has read, handed over (and forgotten here).
	func take() -> Dictionary:
		_mutex.lock()
		var d := _done
		_done = {}
		_mutex.unlock()
		return d

	## The game wants `t` now: the thread's copy when it has one, else null, and the game reads it itself. The thread
	## then skips it, or if it has it in hand already, its copy comes too late and is let go (_install): the game never
	## waits on the thread, however busy the device.
	func claim(t: String):
		_mutex.lock()
		var got = _done.get(t)
		if got != null: _done.erase(t)
		else: _claimed[t] = true
		_mutex.unlock()
		return got

# ---------------------------------------------------------------- lookups
func entry(table: String, id: String) -> Dictionary:
	var t = _tables.get(table)
	if t == null:
		if not _unread.has(table): return {}
		_read(table)
		t = _tables.get(table, {})
	return t.get(id, {})

func has_entry(table: String, id: String) -> bool:
	var t = _tables.get(table)
	if t == null:
		if not _unread.has(table): return false
		_read(table)
		t = _tables.get(table, {})
	return t.has(id)

func all(table: String) -> Array:
	var l = _lists.get(table)
	if l == null:
		if not _unread.has(table): return []
		_read(table)
		return _lists.get(table, [])
	return l

## Whether the data holds a list table of that name (lists.has, reading only that table).
func has_table(table: String) -> bool:
	if _unread.has(table): _read(table)
	return _lists.has(table)

func config(name: String) -> Dictionary:
	var c = _configs.get(name)
	if c == null:
		if not _unread.has(name): return {}
		_read(name)
		return _configs.get(name, {})
	return c

func room(id: String) -> Dictionary:
	if not _rooms_in: _read(ROOMS)
	return _rooms.get(id, {})

## Decision 27: a collection page's seal `seal` (1 or 2) from account_rules.json: its condition, its gift's modifiers
## and effects. Empty for a page or seal the data does not hold.
func collection_seal(page: String, seal: int) -> Dictionary:
	for s in config("account_rules").get("collection_seals", {}).get("pages", {}).get(page, []):
		if int(s.get("seal", 0)) == seal: return s
	return {}

func zone(id: String) -> Dictionary:
	return entry("zones", id)

func zone_of_room(room_id: String) -> Dictionary:
	if not _rooms_in: _read(ROOMS)
	return zone(_room_zone.get(room_id, ""))

func realm(key: String) -> Dictionary:
	return entry("realms", key)

func realm_position(key: String) -> int:
	return int(realm_index.get(key, -1))

func realm_key_for_level(level: int) -> String:
	# Worked out once a Level (the ladder is read in load_all, which forgets these): it walked the whole ladder each time.
	if _realm_for_level.has(level): return _realm_for_level[level]
	var best := "mortal"
	for key in realm_order:
		if int(realm(key).level) <= level: best = key
	_realm_for_level[level] = best
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
	if _stats_at.has(path): return _stats_at[path]
	return _dotted(config("stats"), path, fallback, _stats_at)

## Dotted lookup into movement.json (S43: every traversal constant), e.g. "glide.qi_per_s".
func movement(path: String, fallback = 0.0):
	if _movement_at.has(path): return _movement_at[path]
	return _dotted(config("movement"), path, fallback, _movement_at)

## Dotted lookup into curves.json, e.g. "resets.daily_hour".
func curve(path: String, fallback = 0.0):
	if _curves_at.has(path): return _curves_at[path]
	return _dotted(config("curves"), path, fallback, _curves_at)

## The constants found by path, for the three lookups above (each asked by name many times a tick: a foe's radius and
## reach, the sight and leash, gravity). Only what is found is kept (a missing one answers its caller's own fallback),
## and load_all forgets them with the data they came from.
var _stats_at: Dictionary = {}
var _movement_at: Dictionary = {}
var _curves_at: Dictionary = {}

func _dotted(node, path: String, fallback, found = null):
	for part in path.split("."):
		if node is Dictionary and node.has(part): node = node[part]
		else: return fallback
	if found != null: found[path] = node
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
