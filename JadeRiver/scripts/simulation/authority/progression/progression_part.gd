class_name ProgressionPart
extends RefCounted
## Base of ProgressionAuthority's parts (audit 45, S10). A part holds one section of the authority's work and no state
## of its own: the authority makes one of each, keeps the state and forwards its public methods to them, so every caller
## still calls Game.progression.<method>. In a part:
##   - the authority's state and its public methods are reached through `progression`, as any caller would
##     (progression.channels, progression.apply_insight);
##   - a helper that another part keeps to itself is called on that part (progression.realms.fail_breakthrough);
##   - emit, ok, fail, t and log_line work as they do in an authority.

var _authority: WeakRef   # weak: the authority holds its parts, and Game builds new authorities on every boot
var game   # the Game autoload, as Authority.game

## The authority this part belongs to.
var progression: ProgressionAuthority:
	get: return _authority.get_ref()

func _init(authority: ProgressionAuthority) -> void:
	_authority = weakref(authority)
	game = authority.game

func emit(name: String, payload: Dictionary) -> void:
	progression.emit(name, payload)

static func ok(extra: Dictionary = {}) -> Dictionary:
	return Authority.ok(extra)

static func fail(reason: String, extra: Dictionary = {}) -> Dictionary:
	return Authority.fail(reason, extra)

func t(key: String, args := {}) -> String:
	return progression.t(key, args)

func log_line(actor: String, text: String, kind := "info") -> void:
	progression.log_line(actor, text, kind)
