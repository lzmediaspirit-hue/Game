class_name FrameMemo
extends RefCounted
## Decision 45, phase 2 (S4, DUP-01): the game's one per-frame cache. A question asked several times a frame (a view's
## plate, the HUD's badges, a page's rows) is worked out once and its answer kept for the frame, or for `ttl_frames`
## frames, and dropped as soon as Game.revision moves (`on_revision`: the game changed, an intent, a tick or effects).
## It replaced seven hand-rolled caches (docs/architecture/shared_runtime.md). An owner keeps one FrameMemo for each
## question (a member, or a static var for a static owner):
##
##   var _badges := FrameMemo.new()                      # this frame, this revision, one answer
##   func badges() -> Array:
##       return _badges.value([c.get_instance_id(), override], func(): return point_badges(c))
##
##   static var _seen := FrameMemo.new()                 # a table of answers for this frame, revision and scope
##   var m := _seen.table(room_id, character_id)
##   if not m.has(k): m[k] = ask(k)
##
## `value` keeps up to `max_keys` answers by key (1: the last key asked only, as a hand-rolled key compare did); a key
## is compared by value and kept as a copy, so an array or dictionary the caller changes later never matches stale.
## `table` hands the kept Dictionary itself, for a hot path asked many times a frame (no Callable made per asking); its
## scopes are compared with ==, so pass them as the same types each time (ints, say). Use one of the two on a memo,
## not both. An answer worked out while the memo was started over (its compute asked the memo again under another
## revision or scope) is returned but not kept.

var ttl_frames := 1       ## an answer holds this many frames (1: only the frame it was worked out in)
var on_revision := true   ## an answer is dropped when Game.revision moves
var max_keys := 1         ## `value` keeps at most this many answers; one more starts the memo over (0: no cap)
var _kept := {}           ## key -> answer
var _born := {}           ## key -> the frame it was worked out (ttl_frames > 1)
var _frame := -1          ## the frame the memo was (re)started in
var _rev := -1
var _scope = null
var _scope2 = null
var _one := false         ## the single answer of a memo of one key and one frame, kept beside the table
var _one_key = null
var _one_answer = null

func _init(ttl := 1, revision := true, keys := 1) -> void:
	ttl_frames = maxi(1, ttl)
	on_revision = revision
	max_keys = keys

## `key`'s answer: the one kept while it holds, else `compute.call()`, kept and returned.
func value(key, compute: Callable) -> Variant:
	var now := Engine.get_process_frames()
	var rev: int = Game.revision if on_revision else 0
	if max_keys == 1 and ttl_frames == 1:
		# One answer for one frame (most owners): a compare, as the hand-rolled caches made.
		if _one and now == _frame and rev == _rev and typeof(key) == typeof(_one_key) and key == _one_key: return _one_answer
		_one = false
		_frame = now
		_rev = rev
		var answer = compute.call()
		if not _one and _frame == now and _rev == rev:   # not started over while it was worked out
			_one = true
			_one_key = key.duplicate(true) if key is Array or key is Dictionary else key
			_one_answer = answer
		return answer
	_roll(now, rev, null, null)
	if _kept.has(key) and (ttl_frames == 1 or now - int(_born[key]) < ttl_frames): return _kept[key]
	var kept := _kept
	var answer = compute.call()
	if is_same(kept, _kept):
		if max_keys > 0 and _kept.size() >= max_keys:
			_kept = {}
			_born = {}
		var k = key.duplicate(true) if key is Array or key is Dictionary else key
		_kept[k] = answer
		if ttl_frames > 1: _born[k] = now
	return answer

## The answers kept for this frame, revision and scope (up to two values compared by ==, such as the room and the
## character asked about): the caller reads and fills it. A new Dictionary as soon as any of them moves, so a caller
## still filling the old one never writes into the new.
func table(scope = null, scope2 = null) -> Dictionary:
	var now := Engine.get_process_frames()
	if now == _frame and scope == _scope and scope2 == _scope2 and (not on_revision or Game.revision == _rev): return _kept
	_roll(now, Game.revision if on_revision else 0, scope, scope2)
	return _kept

## Forget every answer (a test, or an owner whose inputs changed in a way the key does not show).
func drop() -> void:
	_kept = {}
	_born = {}
	_one = false
	_frame = -1

func _roll(now: int, rev: int, scope, scope2) -> void:
	if (ttl_frames == 1 and now != _frame) or rev != _rev or typeof(scope) != typeof(_scope) or scope != _scope \
			or typeof(scope2) != typeof(_scope2) or scope2 != _scope2:
		_kept = {}
		_born = {}
		_frame = now
		_rev = rev
		_scope = scope
		_scope2 = scope2
