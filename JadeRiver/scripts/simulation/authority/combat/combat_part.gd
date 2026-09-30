class_name CombatPart
extends RefCounted
## The base of CombatAuthority's parts (docs/architecture/authority_parts.md). A part holds one section of the
## authority's rules. The state stays on the authority, and callers outside it still call the authority, which forwards.

var game   # the Game autoload, as an authority has it

## The authority this part belongs to. It is read through the Game, never kept: a part and its authority holding each
## other would never be freed (RefCounted has no cycle collector), and Game.reset_state builds new ones.
var combat: CombatAuthority:
	get: return game.combat

func _init(g) -> void:
	game = g

func emit(name: String, payload: Dictionary) -> void:
	GameEvents.emit_event(name, payload)

static func ok(extra: Dictionary = {}) -> Dictionary:
	return Authority.ok(extra)

static func fail(reason: String, extra: Dictionary = {}) -> Dictionary:
	return Authority.fail(reason, extra)
