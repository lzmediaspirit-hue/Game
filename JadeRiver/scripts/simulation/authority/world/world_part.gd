class_name WorldPart
extends RefCounted
## Base of WorldAuthority's parts (audit 45, S9). A part holds one section of the authority's work and no state of its
## own: the authority makes one of each, keeps the state and forwards its public methods to them, so every caller still
## calls Game.world.<method>. In a part:
##   - the authority's state and its public methods are reached through `world`, as any caller would
##     (world.chases, world.load_room);
##   - a helper that another part keeps to itself is called on that part (world.loot.drop_loot);
##   - emit, ok and fail work as they do in an authority.

var _authority: WeakRef   # weak: the authority holds its parts, and Game builds new authorities on every boot
var game   # the Game autoload, as Authority.game

## The authority this part belongs to.
var world: WorldAuthority:
	get: return _authority.get_ref()

func _init(authority: WorldAuthority) -> void:
	_authority = weakref(authority)
	game = authority.game

func emit(name: String, payload: Dictionary) -> void:
	world.emit(name, payload)

static func ok(extra: Dictionary = {}) -> Dictionary:
	return Authority.ok(extra)

static func fail(reason: String, extra: Dictionary = {}) -> Dictionary:
	return Authority.fail(reason, extra)
