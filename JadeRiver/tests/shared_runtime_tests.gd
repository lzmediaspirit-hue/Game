extends "res://tests/lib/suite.gd"
## Decision 45, phase 2 (S4): the shared runtime's own checks (docs/architecture/shared_runtime.md). HashNoise answers
## bit for bit as the copies it replaced did; FrameMemo keeps and drops answers as the hand-rolled caches did; the
## GameEvents sets and listener lists keep their order and semantics (BUG-03); the TopdownFx cap holds with loops alive
## and never drops the effect just begun (BUG-04); Figures makes the figure each view draws; and ContentDB's tables,
## read when first asked for or on the loading thread (BUG-11), answer every lookup as a boot that read everything did.
## Run headless:  godot --headless --path . res://tests/shared_runtime_tests.tscn

func _main() -> void:
	_noise()
	await _frame_memo()
	_events()
	_fx_cap()
	_figures()
	await _content()
	end_suite()

# ------------------------------------------------------------------ HashNoise (DUP-02)
## The copies as they were (FxLayer._hash, HazardView._h, MapPage._rnd, BeastKit.noise, the Bag's _hash; and
## TopdownTerrain.h01 and vnoise), compared bit for bit over grids.
static func _old_sin(i: int, salt: int) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(salt) * 78.233) * 43758.5453, 1.0)

static func _old_sin_int(a: int, b: int) -> float:   # MapPage._rnd and the Bag's _hash multiplied the ints as they came
	return fposmod(sin(a * 12.9898 + b * 78.233) * 43758.5453, 1.0)

static func _old_h01(x: int, y: int, s: int) -> float:
	var n := (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
	n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
	return float((n ^ (n >> 16)) & 0xFFFF) / 65536.0

static func _old_vnoise(x: float, y: float, s: int) -> float:
	var x0 := floori(x)
	var y0 := floori(y)
	var tx := x - x0
	var ty := y - y0
	tx = tx * tx * (3.0 - 2.0 * tx)
	ty = ty * ty * (3.0 - 2.0 * ty)
	var a := lerpf(_old_h01(x0, y0, s), _old_h01(x0 + 1, y0, s), tx)
	var b := lerpf(_old_h01(x0, y0 + 1, s), _old_h01(x0 + 1, y0 + 1, s), tx)
	return lerpf(a, b, ty)

func _noise() -> void:
	var n := 0
	var bad := []
	for i in range(-3000, 3001, 7):
		for salt in range(-50, 151, 3):
			var v := HashNoise.scatter(i, salt)
			n += 1
			if v != _old_sin(i, salt) or v != _old_sin_int(i, salt) or v < 0.0 or v >= 1.0: bad.append([i, salt])
	check(bad.is_empty(), "HashNoise.scatter equals the five sin-hash copies bit for bit over %d points %s" % [n, str(bad.slice(0, 5))])
	n = 0
	bad = []
	for x in range(-400, 401, 3):
		for y in range(-300, 301, 7):
			for s in [0, 1, 5, 6, 43, 77, 2246822519, -9]:
				n += 1
				if HashNoise.cell(x, y, s) != _old_h01(x, y, s): bad.append([x, y, s])
	check(bad.is_empty(), "HashNoise.cell equals TopdownTerrain.h01 bit for bit over %d cells %s" % [n, str(bad.slice(0, 5))])
	n = 0
	bad = []
	for x in range(-600, 600):
		for y in [-37.5, -1.25, 0.0, 0.3, 2.71, 19.9, 88.125]:
			for s in [0, 3, 11]:
				n += 1
				if HashNoise.value(x / 7.0, y + x / 3.0, s) != _old_vnoise(x / 7.0, y + x / 3.0, s): bad.append([x, y, s])
	check(bad.is_empty(), "HashNoise.value equals TopdownTerrain.vnoise bit for bit over %d points %s" % [n, str(bad.slice(0, 5))])

# ------------------------------------------------------------------ FrameMemo (DUP-01)
var _asked := 0
func _ask(v):
	_asked += 1
	return v

## On to the next frame (Engine.get_process_frames moved).
func _next_frame() -> void:
	var f := Engine.get_process_frames()
	while Engine.get_process_frames() == f: await get_tree().process_frame

func _frame_memo() -> void:
	var m := FrameMemo.new()
	_asked = 0
	var a1 = m.value(["a"], _ask.bind(1))
	var a2 = m.value(["a"], _ask.bind(2))
	check(a1 == 1 and a2 == 1 and _asked == 1, "a memo answers a key asked again in the frame from what it kept")
	m.value(["b"], _ask.bind(3))
	check(m.value(["a"], _ask.bind(4)) == 4 and _asked == 3, "one kept answer by default: another key asked between works the first out again")
	Game.revision += 1
	check(m.value(["a"], _ask.bind(5)) == 5, "a revision moved drops the answer")
	var key := [1, {"x": 1}]
	m.value(key, _ask.bind(6))
	key[1]["x"] = 2
	check(m.value(key, _ask.bind(7)) == 7, "a key changed after it was asked is not matched stale (the memo kept a copy)")
	var still := FrameMemo.new(1, false)
	still.value(null, _ask.bind(8))
	Game.revision += 1
	check(still.value(null, _ask.bind(9)) == 8, "a memo off the revision keeps its answer through it")
	await _next_frame()
	check(m.value(key, _ask.bind(10)) == 10 and still.value(null, _ask.bind(11)) == 11, "the next frame drops every answer")
	var ttl := FrameMemo.new(3, false, 2)
	ttl.value("k", _ask.bind(12))
	await _next_frame()
	await _next_frame()
	check(ttl.value("k", _ask.bind(13)) == 12, "an answer held for 3 frames is kept 2 frames on")
	await _next_frame()
	check(ttl.value("k", _ask.bind(14)) == 14, "and worked out again on the third")
	ttl.value("j", _ask.bind(15))
	ttl.value("i", _ask.bind(16))
	check(ttl.value("k", _ask.bind(17)) == 17 and ttl.value("i", _ask.bind(18)) == 16, "a third key past two kept starts the memo over")
	var t := FrameMemo.new()
	var d1 := t.table(1, 2)
	d1.x = 1
	check(is_same(t.table(1, 2), d1), "a table is the same Dictionary for the same frame, revision and scope")
	var d2 := t.table(1, 3)
	check(not is_same(d2, d1) and d2.is_empty() and d1.x == 1, "another scope gets a new table (the old one untouched)")
	Game.revision += 1
	check(not is_same(t.table(1, 3), d2), "a revision moved gets a new table")
	var re := FrameMemo.new()
	var bump := func():
		Game.revision += 1
		return re.value("inner", _ask.bind(19))
	var inner = re.value("outer", bump)
	check(inner == 19 and re.value("outer", _ask.bind(20)) == 20, "an answer worked out while the revision moved is not kept for the new one")

# ------------------------------------------------------------------ GameEvents (BUG-03)
class Listener extends RefCounted:
	var name := ""
	var log: Array
	var on_call: Callable
	func _init(n: String, l: Array) -> void:
		name = n
		log = l
	func hear(_p: Dictionary) -> void:
		log.append(name)
		if on_call.is_valid(): on_call.call()

func _events() -> void:
	var unlock := ["realm_changed", "quest_accepted", "quest_completed", "account_highest_realm_changed",
		"sect_level_changed", "flag_set", "profession_rank_up", "dao_tier_up", "slot_unlocked", "item_added",
		"body_level_changed", "purity_changed", "soul_changed", "room_entered", "objective_progressed",
		"character_created", "training_sect_joined", "sect_joined"]
	var save := ["breakthrough_succeeded", "breakthrough_failed", "craft_completed", "quest_completed",
		"system_unlocked", "slot_unlocked", "character_switched", "item_bought", "item_sold", "sect_founded",
		"character_created", "player_revived", "collection_seal_claimed"]
	check(GameEvents.UNLOCK_TRIGGERS.size() == unlock.size() and unlock.all(func(n): return n in GameEvents.UNLOCK_TRIGGERS),
		"the unlock triggers are the 18 they were")
	check(GameEvents.SAVE_TRIGGERS.size() == save.size() and save.all(func(n): return n in GameEvents.SAVE_TRIGGERS),
		"the save triggers are the 13 they were")
	var was := [GameEvents.unlock_pending, GameEvents.save_pending]
	GameEvents.unlock_pending = false
	GameEvents.save_pending = false
	var heard: Array = []
	var a := Listener.new("a", heard)
	var b := Listener.new("b", heard)
	var c := Listener.new("c", heard)
	var late := Listener.new("late", heard)
	GameEvents.subscribe("s4_probe", a.hear)
	GameEvents.subscribe("s4_probe", b.hear, 50)
	GameEvents.subscribe("s4_probe", c.hear)
	GameEvents.subscribe("s4_probe", a.hear)
	GameEvents.emit_event("s4_probe")
	check(not GameEvents.unlock_pending and not GameEvents.save_pending, "an event that is no trigger sets neither flag")
	GameEvents.flush()
	check(heard == ["b", "a", "c"], "listeners hear in priority order, then in the order they came, each once (%s)" % str(heard))
	heard.clear()
	# b, first, adds a listener and takes c away while the event is delivered: the delivery keeps the list it began with.
	b.on_call = func():
		GameEvents.subscribe("s4_probe", late.hear, 10)
		GameEvents.unsubscribe_object(c)
	GameEvents.emit_event("s4_probe")
	GameEvents.flush()
	check(heard == ["b", "a", "c"], "a listener added or removed during a delivery joins or leaves from the next event (%s)" % str(heard))
	b.on_call = Callable()
	heard.clear()
	GameEvents.emit_event("s4_probe")
	GameEvents.flush()
	check(heard == ["late", "b", "a"], "and the next event is heard by the list as it then stands (%s)" % str(heard))
	for l in [a, b, c, late]: GameEvents.unsubscribe_object(l)
	GameEvents.unlock_pending = was[0]
	GameEvents.save_pending = was[1]

# ------------------------------------------------------------------ TopdownFx cap (BUG-04)
class FakeWorld extends Node2D:
	var sorted := Node2D.new()
	var room = null
	func _init() -> void:
		add_child(sorted)

func _fx_cap() -> void:
	var w := FakeWorld.new()
	add_child(w)
	var fx := TopdownFx.new(w)
	var sheet: Dictionary = TopdownFx.cfg().get("dust", {})
	var loops: Array = []
	for i in TopdownFx.MAX_NODES: loops.append(fx.play(sheet, 0, {"loop": true}))
	check(fx.nodes.size() == TopdownFx.MAX_NODES, "the effects fill to the cap with loops")
	var one := fx.play(sheet, 0, {"frames": 6})
	check(fx.nodes.size() == TopdownFx.MAX_NODES and fx.nodes.has(one) and not fx.nodes.has(loops[0]),
		"a one-shot begun with the cap full of loops plays, and the oldest loop goes (%d)" % fx.nodes.size())
	for i in 10: fx.play(sheet, 0, {"loop": true})
	check(fx.nodes.size() == TopdownFx.MAX_NODES and not fx.nodes.has(one), "loops begun past the cap keep it (the one-shot went first)")
	var first := fx.play(sheet, 0, {"frames": 6})
	var second := fx.play(sheet, 0, {"frames": 6})
	check(fx.nodes.has(second) and not fx.nodes.has(first) and fx.nodes.size() == TopdownFx.MAX_NODES,
		"with one-shots alive the oldest one-shot goes, as before")
	var order := fx.nodes.duplicate()
	fx.advance(10.0)
	check(fx.nodes.size() == order.size() - 1 and not fx.nodes.has(second) and fx.nodes == order.filter(func(n): return n != second),
		"advance drops the finished one-shots and keeps the rest in their order")
	fx.clear()
	w.queue_free()

# ------------------------------------------------------------------ Figures (DUP-03; one figure since S12a)
func _figures() -> void:
	var o := {"body": "light", "hair": "topknot", "shirt": "disciple", "pants": "loose", "shoes": "slippers"}
	var d := Figures.for_character()
	check(d is TopdownDoll and d.scale == Vector2.ONE, "a character's figure is the top-down one, undressed, at its own scale")
	var d2 := Figures.for_outfit(o, 5, "s")
	var d3 := Figures.for_outfit(o, 3)
	check(d2.scale == Vector2.ONE * 5 and d2.row == "s" and d3.scale == Vector2.ONE * 3 and d3.row == TopdownDoll.PORTRAIT_ROW,
		"a dressed figure at a whole scale, facing the row asked (the portrait's when none is)")
	var other := {"body": "light", "hair": "short_knot", "shirt": "scholar", "pants": "martial", "shoes": "boots"}
	Figures.dress(d, other)
	check(d.outfit == other, "dressing a figure puts on the outfit")
	var chip := Figures.chip(null, Rect2(-14, -40, 28, 30))
	check(chip is TopdownDoll and chip.clip == Rect2(-14, -40, 28, 30), "a chip's head and shoulders")
	var ci := Node2D.new()
	Figures.draw_on(null, ci, Vector2.ZERO, 1.0)   # no figure: nothing, and no error
	for f in [d, d2, d3, chip, ci]: f.free()

# ------------------------------------------------------------------ ContentDB (BUG-11)
## Every table, group and index as a boot that read everything found them: read here afresh, as the old load_all did.
func _fresh() -> Dictionary:
	var out := {"tables": {}, "lists": {}, "configs": {}, "rooms": {}, "room_zone": {}, "dialogue": {}}
	for file in DirAccess.get_files_at("res://data/"):
		if not file.ends_with(".json") or file in ContentDB.LEGACY_FILES: continue
		var data = JSON.parse_string(FileAccess.get_file_as_string("res://data/" + file))
		if not (data is Dictionary): continue
		var t := file.get_basename()
		if data.has("entries"):
			var by_id := {}
			var ordered: Array = []
			var memo := {}
			for e in data.entries:
				if not (e is Dictionary) or not e.has("id"): continue
				if not (data.get("defaults", {}) as Dictionary).is_empty(): e = ContentDB.expand(e, data.defaults, memo)
				by_id[e.id] = e
				ordered.append(e)
			out.tables[t] = by_id
			out.lists[t] = ordered
		out.configs[t] = data
	for file in DirAccess.get_files_at("res://data/rooms/"):
		if not file.ends_with(".json"): continue
		var room = JSON.parse_string(FileAccess.get_file_as_string("res://data/rooms/" + file))
		out.rooms[room.id] = room
		out.room_zone[room.id] = str(room.get("zone", ""))
	for file in DirAccess.get_files_at("res://data/dialogue/"):
		if not file.ends_with(".json"): continue
		var tree = JSON.parse_string(FileAccess.get_file_as_string("res://data/dialogue/" + file))
		for id in tree.get("trees", {}): out.dialogue[id] = tree.trees[id]
	out.parts = JSON.parse_string(FileAccess.get_file_as_string("res://data/parts.json"))
	return out

func _same_as(f: Dictionary, what: String) -> void:
	var bad: Array = []
	for t in f.configs:
		if ContentDB.config(t) != f.configs[t]: bad.append("config " + t)
		if f.lists.has(t):
			if ContentDB.all(t) != f.lists[t]: bad.append("all " + t)
			var ids: Array = f.tables[t].keys()
			if not ids.is_empty() and (ContentDB.entry(t, str(ids[0])) != f.tables[t][ids[0]] or not ContentDB.has_entry(t, str(ids[-1]))):
				bad.append("entry " + t)
			if not ContentDB.has_table(t): bad.append("has_table " + t)
	for rid in f.rooms:
		if ContentDB.room(rid) != f.rooms[rid] or ContentDB.room_zone.get(rid) != f.room_zone[rid]: bad.append("room " + rid)
	if ContentDB.dialogue != f.dialogue: bad.append("dialogue")
	if ContentDB.parts != f.parts: bad.append("parts")
	if not ContentDB.entry("no_such_table", "x").is_empty() or not ContentDB.all("no_such_table").is_empty() or ContentDB.has_table("no_such_table"):
		bad.append("a table that is not")
	check(bad.is_empty(), "%s: every table, room, tree and the parts answer as a full boot read them %s" % [what, str(bad.slice(0, 6))])

func _content() -> void:
	var f := _fresh()
	# 1. As the game found them (boot read a few, the thread or the lookups the rest).
	_same_as(f, "as booted")
	check(ContentDB.load_errors.is_empty(), "the data reads without errors %s" % str(ContentDB.load_errors))
	check(ContentDB.tables.keys() == f.tables.keys() and ContentDB.lists.keys() == f.lists.keys() and ContentDB.configs.keys() == f.configs.keys(),
		"the whole tables, lists and configs stand in the data folder's order")
	# 2. Read again: boot reads only its few tables on the game's thread; a lookup takes its own table and nothing else.
	ContentDB.load_all()
	var unread: Dictionary = ContentDB.get("_unread")
	check(unread.has("techniques") and not unread.has("realms") and not unread.has("recipes") and not ContentDB.realm_order.is_empty() and not ContentDB.used_in.is_empty(),
		"boot reads the realms and recipes (their indexes) and leaves techniques.json to the loading thread")
	var n := unread.size()
	var tid: String = str(f.lists.techniques[7].id)
	check(ContentDB.entry("techniques", tid) == f.tables.techniques[tid] and not unread.has("techniques") and unread.size() == n - 1,
		"a first lookup reads its own table only")
	# 3. The loading thread: a lookup meets it part-way, and the rest come in frame by frame.
	ContentDB.load_all()
	await get_tree().process_frame
	check(ContentDB.entry("items", str(f.lists.items[3].id)) == f.lists.items[3] and ContentDB.room(str(f.rooms.keys()[5])) == f.rooms[f.rooms.keys()[5]],
		"a lookup while the thread reads answers as a full read")
	for i in 600:
		if unread.is_empty(): break
		await get_tree().process_frame
	check(unread.is_empty(), "the loading thread reads every table within 600 frames (%d left)" % unread.size())
	_same_as(f, "read by the thread")
	check(ContentDB.tables.keys() == f.tables.keys() and ContentDB.configs.keys() == f.configs.keys(), "and they stand in the data folder's order")
