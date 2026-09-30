class_name Cues
extends RefCounted
## Decision 45, phase 2 (E6): the reading half of the cue table, data/cues.json (tools/data/cues.py,
## docs/architecture/cues.md). A row answers an event for one player (`to`: "world" is WorldShared.play); of an
## event's rows the first whose `when` holds plays its steps. This reads the rows, their conditions and the values,
## colours and texts in them; each player does the steps (WorldShared the world's). Static and side-free: it reads
## data, the payload and the active character, and writes nothing.

static var _index := {}   # "to:event" -> [row] in the table's order
static var _indexed := false
const _NONE: Array = []

## The rows of `event` for player `to` ([] for an event it does not answer).
static func rows(to: String, event: String) -> Array:
	if not _indexed:
		_indexed = true
		for r in ContentDB.all("cues"):
			var k := "%s:%s" % [r.get("to", ""), r.get("event", "")]
			if not _index.has(k): _index[k] = []
			_index[k].append(r)
	return _index.get(to + ":" + event, _NONE)

## The first of `event`'s rows for `to` whose `when` holds for payload `p`; {} when none does.
static func pick(to: String, event: String, p: Dictionary) -> Dictionary:
	for r in rows(to, event):
		if holds(r.get("when", {}), p): return r
	return {}

## True when every key of `when` holds: "actor" or "target" "active" is the active character; "@active" (true: there is
## one) and "@<path>" (a value of the active character, "@pools.max_qi"; no match without one); any other key the
## payload's value. A value tests as its own type (a payload that leaves the key out holds false, 0 or ""), a list for
## one of its values and {"gt": n} for more than n.
static func holds(when: Dictionary, p: Dictionary) -> bool:
	for k in when:
		var key := str(k)
		var want = when[k]
		if key in ["actor", "target"] and str(want) == "active": want = Game.active_id
		var got = _active(key) if key.begins_with("@") else p.get(key)
		if key.begins_with("@") and got == null: return false
		if not _test(got, want): return false
	return true

static func _test(got, want) -> bool:
	if want is Array:
		for w in want:
			if _test(got, w): return true
		return false
	if want is Dictionary: return want.has("gt") and (float(got) if got != null else 0.0) > float(want.gt)
	if want is bool: return got != null and bool(got) == want
	if want is float or want is int: return (float(got) if got != null else 0.0) == float(want)
	return (str(got) if got != null else "") == str(want)

static func _active(key: String):
	var c = Game.active()
	if key == "@active": return c != null
	if c == null: return null
	var node = c
	for part in key.trim_prefix("@").split("."):
		node = node.get(part) if node is Object or node is Dictionary else null
	return node

## A value in a row: a number or word as written; "payload.<key>" (MomentRules.value); {"payload": key, "or": d} with
## its default; {"const": "<stats.json path>", "or": d}; {"field_of": table, "id": ref, "field": f, "or": d} a data
## row's field; {"treasure": f, "or": d} the used treasure's (CombatAuthority.treasure_of); {"if": when, "then": a,
## "else": b}. A number source may carry "times": k.
static func value(spec, p: Dictionary):
	if spec is String: return MomentRules.value(spec, p)
	if not (spec is Dictionary): return spec
	if spec.has("if"): return value(spec.get("then") if holds(spec["if"], p) else spec.get("else"), p)
	var v = null
	if spec.has("payload"): v = p.get(str(spec.payload), spec.get("or"))
	elif spec.has("const"): v = ContentDB.stat_const(str(spec["const"]), spec.get("or", 0.0))
	elif spec.has("field_of"): v = ContentDB.entry(str(spec.field_of), str(value(spec.id, p))).get(str(spec.field), spec.get("or"))
	elif spec.has("treasure"): v = CombatAuthority.treasure_of(str(p.get("treasure", ""))).get(str(spec.treasure), spec.get("or"))
	return float(v) * float(spec.times) if spec.has("times") else v

## A colour: a UiKit token or MomentRules' element:, grade:, quality: and dao: ids; "#rrggbb"; [token, alpha];
## [r, g, b, a]; "array:<ref>" an array's engraving (FxLayer.ARRAY_COLOURS, the guard's by default); {"if": …}.
static func color(spec, p := {}) -> Color:
	if spec is Array:
		if spec.size() == 2: return Color(color(spec[0], p), float(spec[1]))
		return Color(float(spec[0]), float(spec[1]), float(spec[2]), float(spec[3]) if spec.size() > 3 else 1.0)
	if spec is Dictionary: return color(value(spec, p), p)
	var s := str(spec)
	if s.begins_with("#"): return Color(s)
	if s.begins_with("array:"): return FxLayer.ARRAY_COLOURS.get(str(MomentRules.value(s.trim_prefix("array:"), p)), FxLayer.ARRAY_COLOURS.guard)
	return MomentRules.color(s, p)

## A text: moments.json's sources (MomentRules.text): a string key with its arguments, a data name, a payload value,
## the first of several that says something; a mark written as it is ("!", "·").
static func text(spec, p: Dictionary) -> String:
	return MomentRules.text(spec, p)
