class_name ProgressionCondition
extends ProgressionPart
## ProgressionAuthority's part: the cultivator's condition: stability, injuries, toxicity and residue, pill
## resistance and pills on loan (S44), the heart demon (G1), soul, purity and lifespan.

# ------------------------------------------------------------------ stability, injuries, toxicity and the heart demon
func step_stability(c, direction: int) -> void:
	var order: Array = ContentDB.curve("stability_order", ["unstable", "settling", "stable", "solid"])
	var i := order.find(c.cultivator.stability)
	var target := clampi(i + direction, 0, 2 if direction > 0 else order.size() - 1)
	if direction > 0 and i >= 2: return
	if target == i: return
	c.cultivator.stability = order[target]
	emit("stability_changed", {"actor": c.id, "word": c.cultivator.stability})

func tick_injuries(c, delta: float, mult: float) -> void:
	var cu: CultivatorState = c.cultivator
	if cu.injuries.is_empty(): return
	if cu.stability == "unstable": mult /= float(ContentDB.curve("injuries.unstable_slow", 1.5))
	for kind in cu.injuries.keys():
		var inj: Dictionary = cu.injuries[kind]
		inj.time_left = float(inj.time_left) - delta * mult
		if inj.time_left <= 0.0:
			inj.severity = int(inj.severity) - 1
			if inj.severity <= 0:
				cu.injuries.erase(kind)
				emit("injury_healed", {"actor": c.id, "kind": kind, "severity": 0})
			else:
				inj.time_left = _heal_time(int(inj.severity))
				emit("injury_healed", {"actor": c.id, "kind": kind, "severity": inj.severity})

func _heal_time(severity: int) -> float:
	var times: Dictionary = ContentDB.curve("injuries.natural_heal_s", {})
	return float(times.get(["minor", "moderate", "severe"][clampi(severity - 1, 0, 2)], 600))

func apply_injury(actor_id: String, kind: String, severity: int) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("injuries", kind): return
	var inj: Dictionary = c.cultivator.injuries.get(kind, {"severity": 0, "time_left": 0.0})
	inj.severity = clampi(int(inj.severity) + severity, 1, 3)
	inj.time_left = _heal_time(int(inj.severity))
	c.cultivator.injuries[kind] = inj
	emit("injury_added", {"actor": c.id, "kind": kind, "severity": inj.severity})

func apply_cure_injury(actor_id: String, kind: String, max_severity: int) -> void:
	var c = game.character(actor_id)
	if c == null or not c.cultivator.injuries.has(kind): return
	var inj: Dictionary = c.cultivator.injuries[kind]
	if int(inj.severity) <= max_severity:
		c.cultivator.injuries.erase(kind)
		emit("injury_healed", {"actor": c.id, "kind": kind, "severity": 0})
	else:
		inj.severity = int(inj.severity) - max_severity
		emit("injury_healed", {"actor": c.id, "kind": kind, "severity": inj.severity})

func apply_toxicity(actor_id: String, amount: float) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cultivator.toxicity = maxf(0.0, c.cultivator.toxicity + amount)
	if amount > 0.0: apply_residue(c.id, amount * float(ContentDB.stat_const("pill_life", {}).get("residue_share", 0.05)))
	emit("toxicity_changed", {"actor": c.id, "value": c.cultivator.toxicity})
	if amount > 0 and c.cultivator.toxicity > c.stats.value("toxicity_tolerance"):
		apply_injury(c.id, "meridian", 1)

## Residue (G1): the part of toxicity that never drains on its own. Negative amounts clear it.
func apply_residue(actor_id: String, amount: float) -> void:
	var c = game.character(actor_id)
	if c == null or amount == 0.0: return
	c.cultivator.residue = maxf(0.0, c.cultivator.residue + amount)
	emit("residue_changed", {"actor": c.id, "value": c.cultivator.residue})

## One dose of a resistance family (S44): every 5 doses add 1 to its count.
func apply_pill_dose(actor_id: String, family: String) -> void:
	var c = game.character(actor_id)
	if c == null or family == "": return
	var r: Dictionary = c.cultivator.pill_resistance.get(family, {"count": 0, "doses": 0})
	r.doses = int(r.get("doses", 0)) + 1
	var per := int(ContentDB.stat_const("pill_life", {}).get("doses_per_count", 5))
	if int(r.doses) >= per:
		r.doses = int(r.doses) - per
		r.count = int(r.get("count", 0)) + 1
	c.cultivator.pill_resistance[family] = r
	emit("pill_resistance_changed", {"actor": c.id, "family": family, "count": int(r.count), "doses": int(r.doses)})

func on_buff_expired(p: Dictionary) -> void:
	var then: Array = ContentDB.item(str(p.get("source", ""))).get("then", [])
	if not then.is_empty(): game.apply_effects(str(p.get("actor", "")), then, "then:" + str(p.source))

## The heart-demon meter (G1), 0-100.
func apply_heart_demon(actor_id: String, amount: float, source: String) -> void:
	var c = game.character(actor_id)
	if c == null or amount == 0.0: return
	# S48: some physiques (Hollow-Touched) make every gain larger.
	if amount > 0.0:
		for pid in c.cultivator.physiques: amount *= float(ContentDB.entry("physiques", str(pid)).get("heart_demon_mult", 1.0))
		# S48 the Blood path doubles every gain.
		if ProgressionAuthority.walks(c, "blood"): amount *= float(ContentDB.stat_const("paths", {}).get("blood", {}).get("heart_demon_mult", 2.0))
	var before := int(ProgressionRules.heart_demon_steps(c.cultivator))
	c.cultivator.heart_demon = clampf(c.cultivator.heart_demon + amount, 0.0, 100.0)
	if amount > 0.0 and not game.account.codex.has("heart_demons"): game.quest.apply_codex("heart_demons")
	emit("heart_demon_changed", {"actor": c.id, "value": c.cultivator.heart_demon, "delta": amount, "source": source,
		"step_crossed": ProgressionRules.heart_demon_steps(c.cultivator) != before})

## The Sovereign Settling Pill: what is left of this stage's consolidation ends on the next tick.
func apply_settle(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null or c.cultivator.consolidation_left <= 0.0: return
	c.cultivator.consolidation_left = 0.001

## Set the stability word (Scar of Failure starts a realm Unstable, S48).
func apply_stability(actor_id: String, word: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cultivator.stability = word
	c.cultivator.stability_progress = 0.0
	emit("stability_changed", {"actor": c.id, "word": word})

func apply_soul(actor_id: String, amount: float) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var before := int(c.cultivator.soul_cultivation / 10.0)
	c.cultivator.soul_cultivation = maxf(0.0, c.cultivator.soul_cultivation + amount)
	if int(c.cultivator.soul_cultivation / 10.0) != before: emit("soul_changed", {"actor": c.id, "value": c.cultivator.soul_cultivation})

func apply_purity(actor_id: String, points: float) -> void:
	var c = game.character(actor_id)
	if c == null or c.cultivator.purity <= 1: return
	c.cultivator.purity_points += points
	var per := float(ContentDB.curve("purity_points_per_grade", 100))
	while c.cultivator.purity_points >= per and c.cultivator.purity > 1:
		c.cultivator.purity_points -= per
		c.cultivator.purity -= 1
		emit("purity_changed", {"actor": c.id, "value": c.cultivator.purity})

## S49 lifespan as flavour: a longevity treasure adds years to the span the realm grants (display only).
func apply_longevity(actor_id: String, years: int) -> void:
	var c = game.character(actor_id)
	if c == null or years == 0: return
	c.cultivator.longevity += years
