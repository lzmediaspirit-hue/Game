class_name Cues
extends RefCounted
## Decision 45, phase 2 (E6): the reading half of the cue table, data/cues.json (tools/data/cues.py,
## docs/architecture/cues.md). A row answers an event for one player (`to`: "world" is WorldShared.play); of an
## event's rows the first whose `when` holds plays its steps. This reads the rows, their conditions and the values,
## colours and texts in them; each player does the steps (WorldShared the world's). Static and side-free: it reads
## data, the payload and the active character, and writes nothing.

static var _index := {}   # to -> {event -> [row] in the table's order}
static var _indexed := false
const _NONE: Array = []
const _NO_ROWS: Dictionary = {}

## The rows of `event` for player `to` ([] for an event it does not answer).
static func rows(to: String, event: String) -> Array:
	if not _indexed:
		_indexed = true
		for r in ContentDB.all("cues"):
			var by_event: Dictionary = _index.get_or_add(str(r.get("to", "")), {})
			if not by_event.has(str(r.get("event", ""))): by_event[str(r.get("event", ""))] = []
			by_event[str(r.get("event", ""))].append(r)
	return _index.get(to, _NO_ROWS).get(event, _NONE)

## The first of `event`'s rows for `to` whose `when` holds for payload `p`; {} when none does.
static func pick(to: String, event: String, p: Dictionary) -> Dictionary:
	for r in rows(to, event):
		if holds(r.get("when", {}), p): return r
	return {}

## True when every key of `when` holds: "actor" or "target" "active" is the active character; "@active" (true: there is
## one) and "@<path>" (a value of the active character, "@pools.max_qi"; no match without one); "@revealed" and
## "@unlocked" (S6: an element of the screen the active character has had revealed, "hud:system_log", and a system it
## has unlocked); any other key the payload's value. A value tests as its own type (a payload that leaves the key out
## holds false, 0 or ""), a list for one of its values, {"gt": n}, {"ge": n}, {"lt": n} and {"le": n} against a number,
## and {"not": v} for anything `v` does not hold for.
static func holds(when: Dictionary, p: Dictionary) -> bool:
	for k in when:
		var key := str(k)
		var want = when[k]
		if key == "@revealed":
			if not Game.is_revealed(str(want)): return false
			continue
		if key == "@unlocked":
			if not Unlocks.is_unlocked(Game.active_id, str(want)): return false
			continue
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
	if want is Dictionary:
		if want.has("not"): return not _test(got, want["not"])
		var n := float(got) if got != null else 0.0
		if want.has("gt"): return n > float(want.gt)
		if want.has("ge"): return n >= float(want.ge)
		if want.has("lt"): return n < float(want.lt)
		if want.has("le"): return n <= float(want.le)
		return false
	if want is bool: return (got != null and bool(got)) == want
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

## A text: moments.json's sources (MomentRules.text): a string key with its arguments (`plural` the count that picks its
## "_one" twin, `suffix` a value the key ends in), a data name, a payload value, the first of several that says
## something; a mark written as it is ("!", "·"). The HUD's notices (S6) add {"join": [text, ...]}, the texts one after
## another, and a key's arguments and count may be the numbers and words of Cues.arg.
static func text(spec, p: Dictionary) -> String:
	if spec is Dictionary and not spec.has("if") and not spec.has("if_slot"):
		if spec.has("key"):
			var k := str(spec["key"]) + (MomentRules.id_of(arg(spec["suffix"], p)) if spec.has("suffix") else "")
			var s := Tx.plural(k, int(arg(spec["plural"], p))) if spec.has("plural") else Tx.t(k)
			var args: Array = (spec.get("args", []) as Array).map(func(a): return arg(a, p))
			return s % args if not args.is_empty() else s
		if spec.has("join"): return "".join(PackedStringArray((spec["join"] as Array).map(func(x): return text(x, p))))
	return MomentRules.text(spec, p)

## A key's argument (S6): a value as it is ("payload.<key>", {"payload": key, "or": d}, a number written out); a number
## made of one: {"int": ref} (with "times": k, of its product), {"float": ref}, {"round": ref, "times": k}, {"neg": ref}
## and {"count": ref} (a list's size); the words of one: {"span": ref, "times": k} a duration (UiKit.span), {"fmt": ref}
## a sum (UiKit.fmt), {"title": ref} an id as words ("wood_root": "Wood Root"), {"lower": ref}, {"pet_name": ref} the
## active character's spirit animal of that uid ("your spirit animal" when it has none); or any text.
static func arg(spec, p: Dictionary):
	if not (spec is Dictionary) or spec.has("payload"): return value(spec, p)
	if spec.has("int"): return int(float(value(spec["int"], p)) * float(spec["times"])) if spec.has("times") else int(value(spec["int"], p))
	if spec.has("float"): return float(value(spec["float"], p))
	if spec.has("round"): return int(round(float(value(spec["round"], p)) * float(spec.get("times", 1.0))))
	if spec.has("neg"): return -int(value(spec["neg"], p))
	if spec.has("count"):
		var v = value(spec["count"], p)
		return v.size() if v is Array or v is Dictionary else 0
	if spec.has("span"): return UiKit.span(float(value(spec["span"], p)) * float(spec.get("times", 1.0)))
	if spec.has("fmt"): return UiKit.fmt(int(value(spec["fmt"], p)))
	if spec.has("title"): return str(value(spec["title"], p)).replace("_", " ").capitalize()
	if spec.has("lower"): return str(value(spec["lower"], p)).to_lower()
	if spec.has("pet_name"):
		var c = Game.active()
		var uid := str(value(spec["pet_name"], p))
		for pt in (c.pets if c else []):
			if str(pt.uid) == uid: return str(pt.name)
		return Tx.t("hud.your_spirit_animal")
	return text(spec, p)
