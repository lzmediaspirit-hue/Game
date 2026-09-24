class_name Authority
extends RefCounted
## Base for every authority: validates intents, changes the state it owns and
## emits events. Authorities never draw and never write another owner's state;
## they call the owner's public apply_* commands instead.

var game  # the Game autoload (GameAuthority facade)

func _init(g) -> void:
	game = g

## Intent types this authority accepts.
func intents() -> Array:
	return []

func handle(_intent: Dictionary) -> Dictionary:
	return fail("unknown_intent")

func tick(_delta: float) -> void:
	pass

func subscribe() -> void:
	pass

func emit(name: String, payload: Dictionary) -> void:
	GameEvents.emit_event(name, payload)

static func ok(extra: Dictionary = {}) -> Dictionary:
	var d := {"ok": true}
	d.merge(extra, true)
	return d

static func fail(reason: String, extra: Dictionary = {}) -> Dictionary:
	var d := {"ok": false, "reason": reason}
	d.merge(extra, true)
	return d

func char_of(intent: Dictionary):
	return game.character(str(intent.get("actor", game.active_id)))

func t(key: String, args := {}) -> String:
	return ContentDB.text(key, args)

func log_line(actor: String, text: String, kind := "info") -> void:
	emit("system_log", {"actor": actor, "text": text, "kind": kind})
