class_name ProgressionVows
extends ProgressionPart
## ProgressionAuthority's part: vows, the Blood and Confucian paths, and Concealment's false realm (S48).

# ------------------------------------------------------------------ vows, paths and the false realm (S48)
## Take or let go of a vow. Taking one is free; letting it go breaks it (+15 heart demon).
func set_vow(c, vow: String, on: bool) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	if not ContentDB.has_entry("vows", vow): return fail("unknown_vow")
	if not Unlocks.is_unlocked(c.id, "vows"): return fail("locked", {"text": Unlocks.locked_text("vows")})
	if on:
		if vow in cu.vows: return ok()
		cu.vows.append(vow)
		emit("vow_taken", {"actor": c.id, "vow": vow})
		return ok({"vow": vow})
	if not vow in cu.vows: return ok()
	cu.vows.erase(vow)
	var cost := float(ContentDB.config("vows").get("break_heart_demon", 15))
	progression.apply_heart_demon(c.id, cost, "vow_broken")
	emit("vow_broken", {"actor": c.id, "vow": vow, "heart_demon": cost})
	return ok({"vow": vow, "broken": true})

## S48 paths as layers: the Blood path is an opt-in for a demonic heart (alignment -20 or lower, from Heart
## Tempering). Taking it lowers alignment and the training sect's regard and opens the Blood Dao; leaving it marks the
## heart (+10 heart demon). Never a class lock: every other technique stays open.
func set_path(c, path: String, on: bool) -> Dictionary:
	var cfg: Dictionary = ContentDB.stat_const("paths", {}).get(path, {})
	if not path in ["blood", "confucian"] or cfg.is_empty(): return fail("unknown_path")
	var gate := "vows" if path == "blood" else "confucian_path"
	if not Unlocks.is_unlocked(c.id, gate): return fail("locked", {"text": Unlocks.locked_text(gate)})
	var walking := bool(c.cultivator.paths.get(path, false))
	if on == walking: return ok({"path": path, "on": on})
	if on and path == "confucian":
		# v1.2 the Confucian path: for the upright (alignment 20 or higher), never beside the Blood path.
		if ProgressionRules.realm_index(c.cultivator.realm_key) < ProgressionRules.realm_index(str(cfg.get("min_realm", "will_manifest_1"))):
			return fail("realm", {"text": Tx.t("sim.progression.path_realm")})
		if c.relations.alignment < int(cfg.get("alignment_at_least", 20)): return fail("alignment", {"text": t("sim.progression.path_upright")})
		if walks(c, "blood"): return fail("exclusive", {"text": t("sim.progression.path_exclusive")})
		c.cultivator.paths[path] = true
		game.relations.apply_alignment(c.id, int(cfg.get("take_alignment", 5)), "confucian_path")
		emit("path_changed", {"actor": c.id, "path": path, "on": true})
		emit("system_used", {"actor": c.id, "system": "confucian_path"})
		return ok({"path": path, "on": true})
	if on and walks(c, "confucian"): return fail("exclusive", {"text": t("sim.progression.path_exclusive")})
	if on:
		if ProgressionRules.realm_index(c.cultivator.realm_key) < ProgressionRules.realm_index(str(cfg.get("min_realm", "heart_tempering_1"))):
			return fail("realm", {"text": Tx.t("sim.progression.path_realm")})
		if c.relations.alignment > int(cfg.get("alignment_at_most", -20)): return fail("alignment", {"text": Tx.t("sim.progression.path_alignment")})
		c.cultivator.paths[path] = true
		game.relations.apply_alignment(c.id, int(cfg.get("take_alignment", -10)), "blood_path")
		game.training.apply_reputation(c.id, "", int(cfg.get("take_reputation", -20)))
		if not c.cultivator.daos.has("blood"): c.cultivator.daos["blood"] = {"tier": 0, "insight": 0.0}   # the path opens the Blood Dao
	else:
		c.cultivator.paths.erase(path)
		progression.apply_heart_demon(c.id, float(cfg.get("leave_heart_demon", 10)), "path_left")
	emit("path_changed", {"actor": c.id, "path": path, "on": on})
	return ok({"path": path, "on": on})

static func walks(c, path: String) -> bool:
	return c != null and bool(c.cultivator.paths.get(path, false))

## A vow held that forbids this kind of act (fleeing_kill, burst_pill, presence, food_buff).
func vow_forbids(c, what: String) -> String:
	for v in c.cultivator.vows:
		if str(ContentDB.entry("vows", str(v)).get("forbids", "")) == what: return str(v)
	return ""

## Concealment's false realm: shown up to two great realms lower ("" shows the true realm).
func set_false_realm(c, realm: String) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	if realm == "":
		cu.false_realm = ""
		emit("false_realm_changed", {"actor": c.id, "realm": ""})
		return ok()
	if not "concealment" in cu.secret_arts: return fail("locked", {"text": Tx.t("sim.progression.false_realm_locked")})
	if ContentDB.realm(realm).is_empty() or not realm in false_realm_choices(c): return fail("too_far", {"text": Tx.t("sim.progression.false_realm_too_far")})
	cu.false_realm = realm
	emit("false_realm_changed", {"actor": c.id, "realm": realm})
	return ok({"realm": realm})

## The realms Concealment can show: the first stage of each great realm up to two below the true one.
func false_realm_choices(c) -> Array:
	var out := []
	var here := ProgressionRules.realm_index(c.cultivator.realm_key)
	var greats := []
	for key in ContentDB.realm_order:
		var g := ProgressionRules.great_realm(str(key))
		if not g in greats: greats.append(g)
	var mine := greats.find(ProgressionRules.great_realm(c.cultivator.realm_key))
	for gi in range(maxi(0, mine - int(ContentDB.stat_const("false_realm", {}).get("max_steps", 2))), mine):
		for key in ContentDB.realm_order:
			if ProgressionRules.great_realm(str(key)) == greats[gi] and ProgressionRules.realm_index(str(key)) < here:
				out.append(str(key))
				break
	return out

## The realm others see: the false one while Concealment holds it, else the true one.
func shown_realm(c) -> String:
	return c.cultivator.false_realm if c.cultivator.false_realm != "" else c.cultivator.realm_key
