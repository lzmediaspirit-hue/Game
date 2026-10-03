class_name CombatPhantom
extends CombatPart
## CombatAuthority's part for Phantom Double (S48, the Soul line). An illusion of the caster stands where they were:
## foes within its radius (not bosses) turn on it until it has been struck its number of times or its time runs out.
## It fights no one. State: `combat.decoys` (not saved).

func cast_illusion(c, t: Dictionary) -> void:
	var pv := combat.player_view(c)
	var secs := float(t.get("illusion_s", 6.0)) + combat._dao_tier(c, "soul")
	combat.decoys[c.id] = {"x": float(pv.x), "y": float(pv.y), "alt": float(pv.alt), "t": secs, "hits": 0,
		"max_hits": int(t.get("illusion_hits", 3)), "radius": float(t.get("illusion_radius", 500)), "facing": int(pv.get("facing", 1))}
	emit("illusion_cast", {"actor": c.id, "x": float(pv.x), "y": float(pv.y), "alt": float(pv.alt), "duration": secs, "facing": int(pv.get("facing", 1))})

## Where an enemy should aim: the illusion when one draws it, else nothing (the brain uses the player).
func decoy_for(e: EnemyState, actor_id: String) -> Dictionary:
	var d: Dictionary = combat.decoys.get(actor_id, {})
	if d.is_empty() or e.is_boss() or e.team != "enemy": return {}
	if e.plane.distance_to(Vector2(float(d.x), float(d.y))) > float(d.radius): return {}
	return d

func tick_decoys(delta: float) -> void:
	var decoys: Dictionary = combat.decoys
	for aid in decoys.keys():
		var d: Dictionary = decoys[aid]
		d.t = float(d.t) - delta
		if float(d.t) <= 0.0:
			decoys.erase(aid)
			emit("illusion_broken", {"actor": aid, "reason": "time"})

## A foe's blow lands on the illusion instead: each strike wears it down.
func strike_decoy(e: EnemyState, ev: Dictionary, hitbox: Dictionary, attack: Dictionary) -> void:
	var c = game.active()
	if c == null or not combat.decoys.has(c.id): return
	var d: Dictionary = combat.decoys[c.id]
	var view := {"x": float(d.x), "y": float(d.y), "alt": float(d.alt), "half_width": combat.body_half_width(), "height": 60.0}
	if not CombatAuthority.hit_test(ev, e.facing, hitbox, view, attack.get("both_sides", false)): return
	d.hits = int(d.hits) + 1
	emit("hit_landed", {"attacker": str(e.uid), "target": "decoy", "target_kind": "decoy", "amount": 0, "type": "physical",
		"crit": false, "element": e.element, "x": float(d.x), "y": float(d.y), "alt": 60.0})
	if int(d.hits) >= int(d.max_hits):
		combat.decoys.erase(c.id)
		emit("illusion_broken", {"actor": c.id, "reason": "struck"})
