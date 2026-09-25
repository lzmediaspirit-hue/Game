extends Node
## Event contract (Part 7 · Quality gates): every event in the Part 4 catalogue
## (data/event_contract.json, built by tools/data/contract.py) is emitted only by
## the scripts of its system, and something reacts to it — a subscriber, a HUD or
## page handler, an achievement or quest rule — unless the contract says the
## reactor reads state every frame instead.
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
