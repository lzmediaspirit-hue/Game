extends Node
## The GameEvents bus (Part 2). Authorities emit events only after their state
## changed. Events raised during a simulation tick are queued and delivered after
## the tick in emission order; reactions may queue further events, delivered in the
## same pass up to a depth limit (Part 4 · Ordering and determinism).
##
## Authorities subscribe with a priority (lower first) so reactions run in the fixed
## owner order. Presentation listens to the `event` signal, which fires after every
## authority reacted, and never changes state.

signal event(name: String, payload: Dictionary)

const MAX_DEPTH := 8
## Events that make the unlock service re-evaluate (S02). Sets (name -> true): every emitted event asks both, so each
## asks one hash lookup, not a walk down a list (BUG-03).
const UNLOCK_TRIGGERS := {"realm_changed": true, "quest_accepted": true, "quest_completed": true,
	"account_highest_realm_changed": true, "sect_level_changed": true, "flag_set": true, "profession_rank_up": true,
	"dao_tier_up": true, "slot_unlocked": true, "item_added": true, "body_level_changed": true, "purity_changed": true,
	"soul_changed": true, "room_entered": true, "objective_progressed": true, "character_created": true,
	"training_sect_joined": true, "sect_joined": true}
## Events that request an immediate save checkpoint (Part 2 · Persistence).
const SAVE_TRIGGERS := {"breakthrough_succeeded": true, "breakthrough_failed": true, "craft_completed": true,
	"quest_completed": true, "system_unlocked": true, "slot_unlocked": true, "character_switched": true, "item_bought": true,
	"item_sold": true, "sect_founded": true, "character_created": true, "player_revived": true,
	"collection_seal_claimed": true}
const _NONE: Array = []

var _queue: Array = []
var _subscribers: Dictionary = {}   # name -> Array[[priority, order, Callable]], never changed in place (below)
var _order := 0
var _delivering := false
var max_depth_reached := 0
var unlock_pending := false
var save_pending := false
var log_tail: Array = []            # debug overlay: last events
var delivered_count := 0

## A name's list of listeners is replaced, never changed in place, so a delivery walks the list it began with without
## copying it for every event (BUG-03): a listener added or removed while an event is delivered joins or leaves from the
## next event on, as when each delivery walked a copy.
func subscribe(name: String, callable: Callable, priority: int = 100) -> void:
	var subs: Array = _subscribers.get(name, _NONE)
	for s in subs:
		if s[2] == callable: return
	_order += 1
	subs = subs.duplicate()
	subs.append([priority, _order, callable])
	subs.sort_custom(func(a, b): return a[0] < b[0] or (a[0] == b[0] and a[1] < b[1]))
	_subscribers[name] = subs

func unsubscribe_object(target: Object) -> void:
	for name in _subscribers:
		_subscribers[name] = _subscribers[name].filter(func(s): return s[2].get_object() != target)

func clear_subscribers() -> void:
	_subscribers.clear()

## Queue an event. Payloads carry IDs and plain values, never Nodes.
func emit_event(name: String, payload: Dictionary = {}) -> void:
	_queue.append([name, payload, 0])
	if name in UNLOCK_TRIGGERS: unlock_pending = true
	if name in SAVE_TRIGGERS: save_pending = true

## Deliver queued events. Called by Game after each tick and after each intent.
func flush() -> void:
	if _delivering: return
	_delivering = true
	var index := 0
	while index < _queue.size():
		var item: Array = _queue[index]
		index += 1
		var name: String = item[0]
		var payload: Dictionary = item[1]
		var depth: int = item[2]
		max_depth_reached = maxi(max_depth_reached, depth)
		var before := _queue.size()
		if depth <= MAX_DEPTH:
			for s in _subscribers.get(name, _NONE):
				if s[2].is_valid(): s[2].call(payload)
		else:
			push_warning("Event depth limit reached for " + name)
		for j in range(before, _queue.size()): _queue[j][2] = depth + 1
		delivered_count += 1
		log_tail.append(name)
		if log_tail.size() > 12: log_tail.pop_front()
		event.emit(name, payload)
	_queue.clear()
	_delivering = false

func pending() -> int:
	return _queue.size()
