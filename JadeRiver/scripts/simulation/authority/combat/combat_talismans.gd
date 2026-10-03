class_name CombatTalismans
extends CombatPart
## CombatAuthority's part for talismans used from the bag (S47). The brush's talismans, written by its techniques, are
## a hit's rider (CombatRiders).

## Use a talisman from the bag. Attack talismans strike at the talisman's own grade and quality, never the user's
## stats; Iron Wall shields; Wind Step holds a free dodge; the Veil hides you; Binding roots (bosses shrug it off).
func use_talisman(c, index: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var s: Dictionary = c.inventory.bag[index]
	var tal := ContentDB.entry("talismans", str(s.id))
	if tal.is_empty() or str(tal.get("kind", "")) in ["revival", "tribulation"]: return fail("not_usable", {"text": Tx.t("sim.combat.talisman_passive")})
	var reason := combat.can_act(c)
	if reason != "": return fail(reason)
	var cfg: Dictionary = ContentDB.config("talismans")
	var qmult := float(cfg.get("quality_mult", {}).get(str(s.get("quality", "common")), 1.0))
	var pv := combat.player_view(c)
	var at := Vector2(float(pv.x), float(pv.y))
	var hits := 0
	match str(tal.kind):
		"attack":
			var base := float(cfg.get("base_power", {}).get(str(tal.get("grade", "common")), 90.0))
			var amount := base * float(tal.get("power", 1.0)) * qmult
			var facing := int(pv.facing)
			var center := at + Vector2(facing * minf(float(tal.get("range", 300)), 160.0), 0)
			var foe := combat._nearest_enemy(at + Vector2(facing * 80, 0), float(tal.get("range", 300)))
			if foe != null: center = foe.plane
			for e in game.room_rt.living_enemies() if game.room_rt else []:
				if e.team != "enemy" or e.hidden or e.plane.distance_to(center) > float(tal.get("radius", 80)): continue
				combat._damage_enemy(e, amount, c.id, "qi", str(tal.get("element", "none")), false, {"source": "talisman"}, facing)
				if e.alive and tal.has("status") and not e.pools.steadfast.has(str(tal.status.id)):
					combat._apply_status_to_enemy(e, {"id": str(tal.status.id), "power": float(tal.status.get("power", 1)), "remaining": float(tal.status.get("duration_s", 2)), "source": c.id})
				hits += 1
			at = center
		"defence":
			combat.raise_shield(c, c.pools.max_hp * float(tal.get("shield_pct", 0.2)) * qmult, float(tal.get("duration_s", 6)))
		"movement":
			var fx2: Dictionary = combat.treasure_fx.get(c.id, {})
			if str(tal.get("effect", "")) == "free_dodge": fx2.free_dodge = float(tal.get("duration_s", 60))
			else: combat.apply_status(c.id, "veiled", float(tal.get("duration_s", 10)) * qmult, 1.0)
			combat.treasure_fx[c.id] = fx2
		"sealing":
			var foe2 := combat._nearest_enemy(at, float(tal.get("range", 260)))
			if foe2 == null: return fail("no_target", {"text": Tx.t("sim.combat.no_target_near")})
			if foe2.is_boss() or foe2.pools.steadfast.has("root"): emit("hit_immune", {"attacker": c.id, "target": str(foe2.uid), "x": foe2.plane.x, "y": foe2.plane.y, "alt": foe2.altitude})
			else: combat._apply_status_to_enemy(foe2, {"id": "root", "power": 1.0, "remaining": float(tal.status.get("duration_s", 2)) * qmult, "source": c.id})
			at = foe2.plane
			hits = 1
	game.inventory.apply_remove_index(c.id, index, 1, "talisman")
	emit("talisman_used", {"actor": c.id, "item": str(s.id), "kind": str(tal.kind), "targets": hits, "x": at.x, "y": at.y, "alt": pv.alt})
	return ok({"kind": str(tal.kind), "targets": hits})
