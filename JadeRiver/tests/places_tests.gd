extends "res://tests/lib/suite.gd"
## Decision 43, systems as places (docs/redesign/systems_as_places.md "As built"): tests/places_suite.gd on saves of its
## own. Run headless:  godot --headless --path . res://tests/places_tests.tscn

func _main() -> void:
	var suite = load("res://tests/places_suite.gd").new()
	await suite.run_all(self, get_tree())
	end_suite()
