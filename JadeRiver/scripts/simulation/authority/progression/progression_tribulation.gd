class_name ProgressionTribulation
extends ProgressionPart
## ProgressionAuthority's part: the heavenly tribulation over a major breakthrough from Cloud Stride on (S48).

# ------------------------------------------------------------------ heavenly tribulation (S48)
## The cloud gathers over the room: bolts in turn, each telegraphed by a ring a second before it strikes where the
## ring was drawn. Timing comes from the breakthrough stream, the rings' places from the combat stream.
func start_tribulation(c, ch: Dictionary) -> void:
	var cu: CultivatorState = c.cultivator
	var from := str(ch.get("from", cu.realm_key))
	var k := ContentDB.config("tribulations")
	var extra := int(progression.spend_fate_next(c, "tribulation_bolts"))
	var total := ProgressionRules.tribulation_bolts(from, cu.heart_demon, c.relations.sin, extra)
	var row := ProgressionRules.tribulation_row(from)
	var per_wave := int(row.bolts)
	var rng := Rng.stream(c.id, "breakthrough")
	var times: Array = []
	var at := float(k.get("first_s", 2.0))
	for i in total:
		if i > 0 and i % per_wave == 0 and i < int(row.bolts) * int(row.get("waves", 1)): at += float(k.get("wave_pause_s", 3.0))
		times.append(at)
		var gap: Array = k.get("gap_s", [0.7, 1.4])
		at += float(k.get("warn_s", 1.0)) + rng.randf_range(float(gap[0]), float(gap[1]))
	progression.tribulations[c.id] = {"ch": ch, "times": times, "total": total, "index": 0, "t": 0.0, "warn": {}, "struck": 0, "absorbed": 0,
		"waves": int(row.get("waves", 1)), "per_wave": per_wave, "room": game.room_rt.room_id if game.room_rt else ""}
	if not game.account.codex.has("heavenly_tribulation"): game.quest.apply_codex("heavenly_tribulation")
	emit("tribulation_started", {"actor": c.id, "from": from, "to": str(ch.to), "bolts": total, "waves": int(row.get("waves", 1))})

func tick_tribulation(c, delta: float) -> void:
	if not progression.tribulations.has(c.id): return
	var tr: Dictionary = progression.tribulations[c.id]
	var k := ContentDB.config("tribulations")
	# Leaving the room breaks the rite: the Qi scatters as though interrupted.
	if game.room_rt == null or game.room_rt.room_id != str(tr.room):
		end_tribulation(c, false, "interruption")
		return
	tr.t = float(tr.t) + delta
	var warn_s := float(k.get("warn_s", 1.0))
	# The ring for the next bolt: drawn a second early, where the character stands (give or take).
	if int(tr.index) < int(tr.total) and (tr.warn as Dictionary).is_empty() and float(tr.t) >= float(tr.times[tr.index]):
		var st: ActorState = game.actor_state(c.id)
		var here: Vector2 = st.plane if st else Vector2(float(c.position.get("x", 600)), float(c.position.get("y", 860)))
		var rng := Rng.stream(c.id, "combat")
		var spread := float(k.get("spread", 60))
		# The side view's depth is a shallow strip; on the height grid the ground is seen whole, so the ring may fall
		# anywhere round the character.
		var depth_k := 0.3 if game.room_rt.topdown == null else 1.0
		var spot := here + Vector2(rng.randf_range(-spread, spread), rng.randf_range(-spread, spread) * depth_k)
		tr.warn = {"x": spot.x, "y": spot.y, "left": warn_s}
		emit("tribulation_bolt", {"actor": c.id, "index": int(tr.index), "total": int(tr.total), "phase": "warn", "x": spot.x, "y": spot.y, "warn_s": warn_s})
	if not (tr.warn as Dictionary).is_empty():
		tr.warn.left = float(tr.warn.left) - delta
		if float(tr.warn.left) <= 0.0:
			var spot2 := Vector2(float(tr.warn.x), float(tr.warn.y))
			tr.warn = {}
			var res: Dictionary = game.combat.apply_tribulation_strike(c, spot2, float(k.get("radius", 80)), float(k.get("depth", 45)))
			tr.index = int(tr.index) + 1
			if res.get("hit", false): tr.struck = int(tr.struck) + 1
			if res.get("absorbed", false): tr.absorbed = int(tr.absorbed) + 1
			emit("tribulation_bolt", {"actor": c.id, "index": int(tr.index) - 1, "total": int(tr.total), "phase": "strike", "x": spot2.x, "y": spot2.y,
				"hit": res.get("hit", false), "damage": float(res.get("damage", 0.0)), "absorbed": res.get("absorbed", false)})
			# Brought to nothing under the heavens: a breakthrough failure, not a grave wound.
			if res.get("lethal", false):
				end_tribulation(c, false, "bodily_failure")
				return
	if int(tr.index) >= int(tr.total) and (tr.warn as Dictionary).is_empty():
		end_tribulation(c, true, "")

func end_tribulation(c, survived: bool, failure: String) -> void:
	var tr: Dictionary = progression.tribulations[c.id]
	progression.tribulations.erase(c.id)
	emit("tribulation_result", {"actor": c.id, "survived": survived, "struck": int(tr.struck), "absorbed": int(tr.absorbed), "bolts": int(tr.total),
		"failure": failure})
	var ch: Dictionary = tr.ch
	if survived:
		progression.realms.settle_breakthrough(c, ch)
		return
	var rng := Rng.stream(c.id, "breakthrough")
	var from := str(ch.get("from", c.cultivator.realm_key))
	if not (ch.get("used", []) as Array).is_empty(): c.cultivator.support_failures[from] = int(c.cultivator.support_failures.get(from, 0)) + 1
	progression.realms.fail_breakthrough(c, failure if ContentDB.has_entry("failures", failure) else "interruption", rng)
	progression.realms.maybe_deviate(c, str(ch.risk))

func is_under_tribulation(actor_id: String) -> bool:
	return progression.tribulations.has(actor_id)

## The tribulation as the HUD and the room draw it: bolts done and total, and the ring waiting to strike.
func tribulation_view(actor_id: String) -> Dictionary:
	if not progression.tribulations.has(actor_id): return {}
	var tr: Dictionary = progression.tribulations[actor_id]
	return {"index": int(tr.index), "total": int(tr.total), "warn": (tr.warn as Dictionary).duplicate(), "struck": int(tr.struck),
		"warn_s": float(ContentDB.config("tribulations").get("warn_s", 1.0)), "radius": float(ContentDB.config("tribulations").get("radius", 80))}
