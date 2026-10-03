class_name CombatPart
extends RefCounted
## Base of CombatAuthority's parts (audit 45, S8; docs/architecture/authority_parts.md). A part holds one section of
## the authority's work and no state of its own: the authority makes one of each, keeps the state and forwards its
## public methods to them, so every caller still calls Game.combat.<method>. In a part:
##   - the authority's state and its methods are reached through `combat` (combat.flying, combat.player_view);
##   - a helper that another part keeps to itself is called on that part (combat.projectiles.spawn_projectile);
##   - emit, ok and fail work as they do in an authority.

var _authority: WeakRef   # weak: the authority holds its parts, and Game builds new authorities on every boot
var game   # the Game autoload, as Authority.game

## The authority this part belongs to.
var combat: CombatAuthority:
	get: return _authority.get_ref()

func _init(authority: CombatAuthority) -> void:
	_authority = weakref(authority)
	game = authority.game

func emit(name: String, payload: Dictionary) -> void:
	combat.emit(name, payload)

static func ok(extra: Dictionary = {}) -> Dictionary:
	return Authority.ok(extra)

static func fail(reason: String, extra: Dictionary = {}) -> Dictionary:
	return Authority.fail(reason, extra)
