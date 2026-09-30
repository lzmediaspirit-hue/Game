class_name ProgressionAttunement
extends ProgressionPart
## ProgressionAuthority's part: attunement to a zone's land and its four jades (S18).

# ------------------------------------------------------------------ attunement (S18)
## S18 attunement: jades plus small bonuses (character state, per zone) against what the room asks.
func attunement_required(room_id: String) -> float:
	var room := ContentDB.room(room_id)
	if room.has("attunement_required"): return float(room.attunement_required)
	if room.get("safe", false): return 0.0   # towns, camps and halls ask nothing of the blood
	var att = ContentDB.zone_of_room(room_id).get("attunement")
	return float((att.get("required", [0]) as Array)[0]) if att is Dictionary else 0.0

## The attunement the character brings to where they stand: jades (and permanent bonuses) for
## that zone, plus temporary bonuses such as a Storm Blood Pill.
func attunement_value(c, zone_id: String) -> float:
	if c == null or zone_id == "": return 0.0
	return float(c.cultivator.attunement.get(zone_id, 0.0)) + c.stats.value("attunement_bonus") + game.sect.outpost_attunement(zone_id)

func attunement_factors(c) -> Dictionary:
	var room_id := str(c.position.get("room", ""))
	var zone_id := str(ContentDB.zone_of_room(room_id).get("id", ""))
	return CombatRules.attunement_factors(attunement_value(c, zone_id), attunement_required(room_id))

func _emit_attunement(c) -> void:
	var room_id := str(c.position.get("room", ""))
	var zone_id := str(ContentDB.zone_of_room(room_id).get("id", ""))
	var f := attunement_factors(c)
	progression.last_attune[c.id] = "%.3f|%.3f" % [f.dealt, f.taken]
	emit("attunement_changed", {"actor": c.id, "zone": zone_id, "value": attunement_value(c, zone_id),
		"required": attunement_required(room_id), "dealt": f.dealt, "taken": f.taken})

func refresh_attunement(c) -> void:
	if c == null: return
	var f := attunement_factors(c)
	if str(progression.last_attune.get(c.id, "1.000|1.000")) != "%.3f|%.3f" % [f.dealt, f.taken]: _emit_attunement(c)

func on_zone_entered(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	_emit_attunement(c)

## S18: four attunement jades per zone, each levelled with that zone's shards. The zone's
## attunement total is the sum of its jades (times their value per level).
func jade_levels(c, zone_id: String) -> Array:
	var att = ContentDB.zone(zone_id).get("attunement")
	var n := int((att.get("jades", []) as Array).size()) if att is Dictionary else 0
	var levels: Array = (c.cultivator.attunement_jades.get(zone_id, []) as Array).duplicate()
	while levels.size() < n: levels.append(0)
	return levels

func jade_cost(zone_id: String, level: int) -> int:
	var att = ContentDB.zone(zone_id).get("attunement")
	var cost: Dictionary = att.get("cost", {}) if att is Dictionary else {}
	return int(cost.get("base", 1)) + int(cost.get("per_level", 1)) * level

func attune_jade(c, zone_id: String, index: int) -> Dictionary:
	var att = ContentDB.zone(zone_id).get("attunement")
	if not (att is Dictionary): return fail("no_attunement")
	if not Unlocks.is_unlocked(c.id, str(att.get("unlock", ""))): return fail("locked", {"text": Unlocks.locked_text(str(att.get("unlock", "")))})
	var levels := jade_levels(c, zone_id)
	if index < 0 or index >= levels.size(): return fail("bad_jade")
	var level := int(levels[index])
	if level >= int(att.get("jade_max", 15)): return fail("maxed", {"text": Tx.t("sim.progression.jade_at_its_peak")})
	var cost := jade_cost(zone_id, level)
	var shard := str(att.get("shard", ""))
	if c.inventory.count(shard) < cost:
		return fail("missing", {"text": Tx.t("sim.progression.jade_needs_shards") % [cost, ContentDB.item_name(shard)]})
	game.inventory.apply_remove(c.id, shard, cost, "attune")
	levels[index] = level + 1
	c.cultivator.attunement_jades[zone_id] = levels
	var total := 0.0
	for l in levels: total += float(l) * float(att.get("jade_value", 1.0))
	c.cultivator.attunement[zone_id] = total
	emit("system_used", {"actor": c.id, "system": "attune_jade"})
	_emit_attunement(c)
	return ok({"zone": zone_id, "index": index, "level": level + 1, "attunement": total})
