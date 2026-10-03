class_name CraftingPart
extends RefCounted
## Base of CraftingAuthority's parts (audit 45, S10). A part holds one section of the authority's work and no state of
## its own: the authority makes one of each, keeps the state and forwards its public methods to them, so every caller
## still calls Game.crafting.<method>. In a part:
##   - the authority's state and its public methods are reached through `crafting`, as any caller would
##     (crafting.pending, crafting.rank_of);
##   - a helper that another part keeps to itself is called on that part (crafting.furnaces.settle_tribulation);
##   - emit, ok and fail work as they do in an authority.

var _authority: WeakRef   # weak: the authority holds its parts, and Game builds new authorities on every boot
var game   # the Game autoload, as Authority.game

## The authority this part belongs to.
var crafting: CraftingAuthority:
	get: return _authority.get_ref()

func _init(authority: CraftingAuthority) -> void:
	_authority = weakref(authority)
	game = authority.game

func emit(name: String, payload: Dictionary) -> void:
	crafting.emit(name, payload)

static func ok(extra: Dictionary = {}) -> Dictionary:
	return Authority.ok(extra)

static func fail(reason: String, extra: Dictionary = {}) -> Dictionary:
	return Authority.fail(reason, extra)
