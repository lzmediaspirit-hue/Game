class_name CombatPlates
extends CombatPart
## CombatAuthority's part for Array Plates in a fight (S48). State: `combat.arrays`, the plates laid in this room.

## An Array Plate laid at your feet: a guarding array (defence while you stand in it), a killing array (Qi damage to
## every foe inside each second) or a binding array (foes inside slowed). The Formation Dao lengthens them (+10% from
## tier 1) and sharpens the killing array (+20% a tier); each plate laid teaches it a little.
func deploy_array(actor_id: String, e: Dictionary) -> void:
	var c = game.character(actor_id)
	if c == null or game.room_rt == null: return
	var pv := combat.player_view(c)
	var tier := combat._dao_tier(c, "formation")
	var power: float = 1.0 + c.stats.value("array_power")
	var living := StatRules.set_flag(c, "living_array")
	var secs: float = float(e.get("duration", 10)) * (1.1 if tier >= 1 else 1.0) * power
	var a := {"actor": c.id, "kind": str(e.get("array", "guard")), "x": float(pv.x), "y": float(pv.y),
		"radius": float(e.get("radius", 150)) * (1.0 + float(living.get("wider", 0.0))), "t": secs, "tick": 0.0,
		"mult": float(e.get("mult", 0.5)) * (1.0 + 0.2 * tier) * power, "slow": float(e.get("slow", 0.4)), "defense": float(e.get("defense", 0.15)),
		"talisman": living.get("talismans", {}).get(str(e.get("array", "guard")), {}), "marked": {}}
	combat.arrays.append(a)
	game.progression.apply_insight(c.id, "formation", 3.0, "array_plate")
	emit("array_deployed", {"actor": c.id, "kind": a.kind, "x": a.x, "y": a.y, "radius": a.radius, "duration": secs})

func tick_arrays(delta: float) -> void:
	var arrays: Array = combat.arrays
	if arrays.is_empty(): return
	for a in arrays.duplicate():
		a.t = float(a.t) - delta
		if float(a.t) <= 0.0:
			arrays.erase(a)
			emit("array_faded", {"actor": str(a.actor), "kind": str(a.kind)})
			continue
		a.tick = float(a.tick) - delta
		if float(a.tick) > 0.0: continue
		var c = game.character(str(a.actor))
		if c == null or game.room_rt == null: continue
		var here := Vector2(float(a.x), float(a.y))
		var tal: Dictionary = a.talisman
		if not tal.is_empty():
			for e in combat._enemies_within(here, float(a.radius)):
				if a.marked.has(e.uid) or e.pools.steadfast.has(str(tal.id)): continue
				a.marked[e.uid] = true
				combat._apply_status_to_enemy(e, {"id": str(tal.id), "power": float(tal.get("power", 1)), "remaining": float(tal.get("duration_s", 1.0)), "source": c.id})
		match str(a.kind):
			"killing":
				a.tick = 1.0
				var pv := combat.player_view(c)
				var atk := {"damage_type": "qi", "element": "none", "mult": [float(a.mult), float(a.mult)], "range": [0.95, 1.05], "source": "array:killing",
					"dao_tier": combat._dao_tier(c, "formation")}
				for e in combat._enemies_within(here, float(a.radius)):
					combat._player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
			"binding":
				a.tick = 0.5
				for e in combat._enemies_within(here, float(a.radius)):
					if not e.pools.steadfast.has("slow"): combat._apply_status_to_enemy(e, {"id": "slow", "power": float(a.slow), "remaining": 1.0, "source": c.id})
			_:
				a.tick = 0.5
				var st: ActorState = game.actor_state(c.id)
				if st != null and st.plane.distance_to(here) <= float(a.radius):
					c.stats.add_modifier({"stat": "physical_defense", "op": "pct_add", "value": float(a.defense), "duration": 0.8, "source": "array:guard"})
					combat.refresh_stats(c.id)
