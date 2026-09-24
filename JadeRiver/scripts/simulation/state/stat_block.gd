class_name StatBlock
extends RefCounted
## S11 · One stat engine for players, monsters, spirit animals and companions.
## Every stat change is a modifier; nothing writes a final stat directly.
## Stacking: base -> flat adds -> percent adds (summed) -> percent multipliers
## (multiplied) -> override -> caps. Finals are cached until a source changes.
##
## modifier = {stat, op (flat|pct_add|pct_mul|override), value, source, duration (-1 = permanent),
##             remaining, condition (optional)}

var base: Dictionary = {}
var modifiers: Array = []
var finals: Dictionary = {}
var dirty := true
var recalc_count := 0
var caps: Dictionary = {}          # stat -> absolute cap on the final value
var relative_caps: Dictionary = {} # stat -> max fraction above base (move speed +40%)

func set_base(stat: String, value: float) -> void:
	if base.get(stat, NAN) != value:
		base[stat] = value
		dirty = true

func set_bases(values: Dictionary) -> void:
	for k in values: set_base(k, float(values[k]))

func add_modifier(m: Dictionary) -> void:
	var mod := m.duplicate()
	mod["duration"] = float(mod.get("duration", -1))
	mod["remaining"] = float(mod.get("remaining", mod.duration))
	mod["op"] = str(mod.get("op", "flat"))
	# The same source and stat refreshes instead of stacking (buffs never stack with themselves).
	for i in modifiers.size():
		var old: Dictionary = modifiers[i]
		if old.get("source") == mod.get("source") and old.get("stat") == mod.get("stat") and mod.get("source", "") != "":
			modifiers[i] = mod
			dirty = true
			return
	modifiers.append(mod)
	dirty = true

func remove_source(source: String) -> bool:
	var before := modifiers.size()
	modifiers = modifiers.filter(func(m): return m.get("source") != source)
	if modifiers.size() != before:
		dirty = true
		return true
	return false

func remove_prefix(prefix: String) -> void:
	var before := modifiers.size()
	modifiers = modifiers.filter(func(m): return not str(m.get("source", "")).begins_with(prefix))
	if modifiers.size() != before: dirty = true

func has_source(source: String) -> bool:
	for m in modifiers:
		if m.get("source") == source: return true
	return false

## Advance timed modifiers. Returns the sources that expired.
func tick(delta: float) -> Array:
	var expired: Array = []
	for m in modifiers:
		if float(m.duration) < 0: continue
		m.remaining = float(m.remaining) - delta
		if float(m.remaining) <= 0 and not expired.has(m.source): expired.append(m.source)
	if not expired.is_empty():
		modifiers = modifiers.filter(func(m): return float(m.duration) < 0 or float(m.remaining) > 0)
		dirty = true
	return expired

func value(stat: String) -> float:
	if dirty: recalc()
	return float(finals.get(stat, base.get(stat, 0.0)))

func compute(stat: String) -> float:
	var v := float(base.get(stat, 0.0))
	var flat := 0.0
	var pct := 0.0
	var mul := 1.0
	var override = null
	for m in modifiers:
		if m.get("stat") != stat or m.has("condition"): continue
		match m.op:
			"flat": flat += float(m.value)
			"pct_add": pct += float(m.value)
			"pct_mul": mul *= 1.0 + float(m.value)
			"override": override = float(m.value)
	v = (v + flat) * (1.0 + pct) * mul
	if override != null: v = override
	if caps.has(stat): v = minf(v, float(caps[stat]))
	if relative_caps.has(stat) and base.has(stat):
		v = minf(v, float(base[stat]) * (1.0 + float(relative_caps[stat])))
	return v

## Conditional modifiers (element, zone, vs_realm_gap...) are summed on demand.
func conditional(stat: String, key: String, value_match) -> float:
	var total := 0.0
	for m in modifiers:
		if m.get("stat") != stat or not m.has("condition"): continue
		if m.condition.get(key) == value_match: total += float(m.value)
	return total

func recalc() -> void:
	var keys := {}
	for k in base: keys[k] = true
	for m in modifiers: keys[m.stat] = true
	finals.clear()
	for k in keys: finals[k] = compute(k)
	dirty = false
	recalc_count += 1

func snapshot() -> Dictionary:
	# Only timed modifiers persist (buffs); permanent ones are rebuilt from their sources.
	return {"timed": modifiers.filter(func(m): return float(m.duration) >= 0).duplicate(true)}

func restore_timed(d: Dictionary) -> void:
	for m in d.get("timed", []):
		if m is Dictionary and m.has("stat") and m.has("source"): add_modifier(m)
