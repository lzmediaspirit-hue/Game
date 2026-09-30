extends RefCounted
## One part of the World authority (docs/architecture/authority_parts.md): a section of its rules in a file of its own.
## WorldAuthority makes its parts as it is made and forwards its public methods to them, so every caller still asks
## `Game.world`. The state other code reads stays on the authority (`world.chases`, `world.voyages` ...); a part keeps
## only its own timers and caches. A part calls a sibling through the authority (`world.loot.drop_loot`).

var game   # the Game autoload (GameAuthority facade)
var _world: WeakRef

## The authority this part belongs to. Held weakly: the authority holds its parts, and a strong hold both ways would keep
## every authority GameAuthority.build_authorities replaces alive.
var world: WorldAuthority:
	get: return _world.get_ref()

func _init(authority: WorldAuthority) -> void:
	_world = weakref(authority)
	game = authority.game

func emit(name: String, payload: Dictionary) -> void:
	GameEvents.emit_event(name, payload)

static func ok(extra: Dictionary = {}) -> Dictionary:
	return Authority.ok(extra)

static func fail(reason: String, extra: Dictionary = {}) -> Dictionary:
	return Authority.fail(reason, extra)
