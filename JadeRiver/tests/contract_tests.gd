extends Node
## Event contract (Part 7 · Quality gates): every event in the Part 4 catalogue
## (data/event_contract.json, built by tools/data/contract.py) is emitted only by
## the scripts of its system, and something reacts to it — a subscriber, a HUD or
## page handler, an achievement or quest rule — unless the contract says the
## reactor reads state every frame instead. Strings: no player-facing text is
## written in the player-facing scripts; it comes from data/strings via Tx.t(key).
## Forbidden patterns: gameplay code takes randomness from named Rng streams and
## time from Clock.
## Run headless:  godot --headless --path . res://tests/contract_tests.tscn

var checks := 0
var failures := 0
var sources: Dictionary = {}   # script name (no extension) -> Array of lines

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	_read_scripts("res://scripts/")
	var contract: Dictionary = ContentDB.config("event_contract").get("events", {})
	check(contract.size() >= 100, "the contract lists the catalogue (%d events)" % contract.size())
	var data_text := _data_text()
	var emit_re := RegEx.create_from_string("\\bemit(_event)?\\(")
	for ev in contract:
		var row: Dictionary = contract[ev]
		var owners: Array = row.get("files", [])
		var q := "\"%s\"" % ev
		var owned := false
		var foreign: Array = []
		var consumed := false
		for name in sources:
			var mine: bool = name in owners
			var lines: Array = sources[name]
			for i in lines.size():
				var line: String = lines[i]
				if not line.contains(q): continue
				var emits := emit_re.search(line) != null
				if mine: owned = true
				if emits and not mine: foreign.append("%s:%d" % [name, i + 1])
				# An owner choosing between event names (`x := "a" if … else "b"`) is not a reaction.
				if not emits and not (mine and line.contains(" if ") and line.contains(":=")): consumed = true
		check(owned, "%s is emitted by %s (%s)" % [ev, row.get("system", "?"), ", ".join(owners)])
		check(foreign.is_empty(), "%s is emitted only by %s, not %s" % [ev, row.get("system", "?"), ", ".join(foreign)])
		var by_data := data_text.contains("\"event\": " + q)
		check(consumed or by_data or row.has("polled"), "%s has a reactor" % ev)
	_strings_gate()
	_forbidden_patterns()
	print("contract_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

func _read_scripts(dir: String) -> void:
	for sub in DirAccess.get_directories_at(dir): _read_scripts(dir + sub + "/")
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".gd"):
			sources[f.get_basename()] = FileAccess.get_file_as_string(dir + f).split("\n")

## Data rules that react to events (achievements, quest objectives) name them as "event": "…".
func _data_text() -> String:
	var out := ""
	for f in DirAccess.get_files_at("res://data/"):
		if f.ends_with(".json") and f != "event_contract.json": out += FileAccess.get_file_as_string("res://data/" + f)
	return out

# ------------------------------------------------------------------ strings (Part 7)
## The same rules as tools/dev/extract_strings.py: a literal that reads like text is not
## allowed in the player-facing scripts unless it is an id, a technical token, a key,
## a comparison, a membership list, a const, a signature default or debug output.
const STRING_SCOPE := ["res://scripts/ui/", "res://scripts/hud.gd", "res://scripts/shell/", "res://scripts/main.gd", "res://scripts/world.gd",
	"res://scripts/player.gd", "res://scripts/presentation/enemy_view.gd", "res://scripts/presentation/loot_view.gd",
	"res://scripts/presentation/portal_view.gd", "res://scripts/presentation/npc_view.gd", "res://scripts/simulation/authority/",
	"res://scripts/core/requirement_rules.gd", "res://scripts/core/unlock_service.gd"]
const TECH := ["UI", "SFX", "Music", "Ambience", "Master", "MobileHUD", "Room", "HUD"]

func _strings_gate() -> void:
	var lit := RegEx.create_from_string("(?<![&^\\w])\"((?:[^\"\\\\]|\\\\.)*)\"")
	var in_list := RegEx.create_from_string("\\bin\\s*\\[[^\\]]*\\]")
	var skip := RegEx.create_from_string("^\\s*(#|(static\\s+)?func\\s|const\\s)|\\b(print|prints|printerr|push_warning|push_error|assert)\\(")
	var found: Array = []
	for path in _scope_files():
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in lines.size():
			var line: String = lines[i]
			if skip.search(line) != null: continue
			var lists: Array = []
			for m in in_list.search_all(line): lists.append([m.get_start(), m.get_end()])
			for m in lit.search_all(line):
				var s := m.get_string(1)
				if not _reads_as_text(s): continue
				if lists.any(func(r): return m.get_start() >= r[0] and m.get_start() < r[1]): continue
				var after := line.substr(m.get_end()).strip_edges(true, false)
				var before := line.substr(0, m.get_start()).strip_edges(false, true)
				if after.begins_with(":") and not after.begins_with(":="): continue
				if before.ends_with("==") or before.ends_with("!=") or after.begins_with("==") or after.begins_with("!="): continue
				found.append("%s:%d %s" % [path.get_file(), i + 1, s])
	for f in found.slice(0, 20): print("  text in code: ", f)
	check(found.is_empty(), "no player-facing text in the scripts (%d found; move it with tools/dev/extract_strings.py)" % found.size())

func _reads_as_text(s: String) -> bool:
	var raw := s.replace("\\n", "\n").replace("\\\"", "\"")
	if raw.strip_edges() in TECH or raw.strip_edges() == "": return false
	if raw.begins_with("res:") or raw.begins_with("user:") or raw.begins_with("--") or raw.begins_with("#"): return false
	if raw.contains("/") and not raw.contains(" "): return false
	if RegEx.create_from_string("^[a-z0-9_.:%\\-]+$").search(raw) != null: return false
	if RegEx.create_from_string("[A-Za-z]{2,}").search(raw) == null: return false
	return raw.strip_edges().contains(" ") or RegEx.create_from_string("^[A-Z]").search(raw.strip_edges()) != null

func _scope_files() -> Array:
	var out: Array = []
	for p in STRING_SCOPE:
		if str(p).ends_with("/"):
			for sub in _walk(str(p)): out.append(sub)
		else:
			out.append(p)
	return out

func _walk(dir: String) -> Array:
	var out: Array = []
	for sub in DirAccess.get_directories_at(dir): out.append_array(_walk(dir + sub + "/"))
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".gd"): out.append(dir + f)
	return out

# ------------------------------------------------------------------ forbidden patterns (Part 7)
## Seeded generators that are allowed: the stream service itself, the map layout (seeded by the
## room's map seed), the daily shop rotation (seeded by day and account seed) and the enemy
## authority's placeholder, which is swapped for the character's "world" stream on room entry.
const RNG_OK := ["rng_service.gd", "map_generator.gd", "economy_authority.gd", "enemy_authority.gd"]

func _forbidden_patterns() -> void:
	var raw_rng := RegEx.create_from_string("(?<![.\\w])(randi|randf|randf_range|randi_range|randfn)\\(|RandomNumberGenerator\\.new\\(")
	var clock := RegEx.create_from_string("\\bTime\\.get_|\\bOS\\.get_(unix|ticks|datetime|date|time)")
	var bad_rng: Array = []
	var bad_clock: Array = []
	for path in _walk("res://scripts/simulation/") + _walk("res://scripts/core/"):
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in lines.size():
			var line: String = lines[i]
			if line.strip_edges().begins_with("#"): continue
			if raw_rng.search(line) != null and not path.get_file() in RNG_OK: bad_rng.append("%s:%d" % [path.get_file(), i + 1])
			if clock.search(line) != null and path.get_file() != "clock_service.gd": bad_clock.append("%s:%d" % [path.get_file(), i + 1])
	check(bad_rng.is_empty(), "gameplay randomness comes from named Rng streams %s" % str(bad_rng))
	check(bad_clock.is_empty(), "gameplay time comes from Clock %s" % str(bad_clock))
