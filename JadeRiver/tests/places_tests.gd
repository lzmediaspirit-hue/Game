extends Node
## Decision 43, systems as places (docs/redesign/systems_as_places.md "As built"): tests/places_suite.gd on saves of its
## own. Run headless:  godot --headless --path . res://tests/places_tests.tscn

var checks := 0
var failures := 0

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var suite = load("res://tests/places_suite.gd").new()
	await suite.run_all(self, get_tree())
	print("places_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)
