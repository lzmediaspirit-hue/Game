class_name CombatRiders
extends CombatPart
## CombatAuthority's part for what a landed blow carries after its damage: the weapon families' riders (armour break,
## the fan's lift, the brush's talisman), the Soul line's marks, the Poison Body, weapon oils, and the skills an
## Artifact Spirit or an awakened weapon strikes on its own. State: `combat.searched`, `combat.poison_touch`,
## `combat.spirit_hits`, `combat.awaken_hits`.

## S47 v1.1 families: the heavy sabre breaks armour (sundered: hits ignore part of its defence); the fan's wind lifts a
## foe into the air, helpless until it lands (not a boss, a flyer or anything that cannot be moved).
func weapon_after_hit(c, e: EnemyState, attack: Dictionary) -> void:
	var ab: Dictionary = attack.get("armour_break", {})
	if not ab.is_empty() and not e.pools.steadfast.has("sundered"):
		var chance := float(ab.get("chance", 0.3)) * float(ProgressionRules.path_flag(c, "armour_break_mult", 1.0))
		if Rng.stream(c.id, "weapon").randf() < chance:
			combat.apply_status_to_enemy(e, {"id": "sundered", "power": 1.0, "remaining": float(ab.get("duration_s", 4)), "source": c.id})
	var up := float(attack.get("knockup_s", 0.0))
	if up > 0.0 and not e.is_boss() and not e.def.get("knockback_immune", false) and not e.def.get("flying", false) \
			and not e.pools.steadfast.has("launched") and not e.pools.has_status("launched"):
		combat.apply_status_to_enemy(e, {"id": "launched", "power": 1.0, "remaining": up, "duration": up, "source": c.id})
	# v1.2 the brush's talisman: one on a foe at a time, written by a technique.
	var tal: Dictionary = attack.get("talisman", {})
	if not tal.is_empty() and float(e.ai.get("talisman_until", 0.0)) <= game.sim_time and not e.pools.steadfast.has(str(tal.id)):
		e.ai["talisman_until"] = game.sim_time + float(tal.remaining)
		combat.apply_status_to_enemy(e, {"id": str(tal.id), "power": float(tal.power), "remaining": float(tal.remaining), "source": c.id})
	# S48 the Soul line: Sense Lock fixes the soul's eye on the foe; Soul Search marks an elite for its memories.
	var lock := float(attack.get("sense_lock_s", 0.0))
	if lock > 0.0:
		combat.apply_status_to_enemy(e, {"id": "sense_locked", "power": 1.0, "remaining": lock, "source": c.id})
		e.hidden = false
	var search := float(attack.get("soul_search_s", 0.0))
	if search > 0.0 and (e.elite or e.is_boss() or e.role == "elite"):
		combat.apply_status_to_enemy(e, {"id": "soul_searched", "power": 1.0, "remaining": search, "source": c.id})
		combat.searched[str(e.uid)] = {"actor": c.id, "t": search}
	poison_body(c, e)
	_spirit_skill(c, attack)

## S47 Artifact Spirit depth: an awake spirit strikes on its own every so many blows of its blade (its skill), weighed
## by its affinity and level. A spirit its wielder cannot control keeps its skill to itself. S47 weapon awakening: an
## awakened weapon strikes on its own too (its family's skill, or a legend's own), on a count of its own.
func _spirit_skill(c, attack: Dictionary) -> void:
	var src := str(attack.get("source", ""))
	if not (src == "basic" or src.begins_with("tech:")): return
	var w = c.inventory.equipped.get("weapon")
	if not (w is Dictionary): return
	if str(w.get("spirit", "")) == "awake" and not w.get("sealed", false) and StatRules.spirit_controlled(c, w):
		var sk: Dictionary = ContentDB.item(str(w.id)).get("spirit", {}).get("skill", {})
		if not sk.is_empty() and _count_to(combat.spirit_hits, c.id, int(sk.get("every_hits", 8))):
			_skill_strike(c, sk, float(sk.get("mult", 1.5)) * StatRules.spirit_power(c, w), "spirit:" + str(w.id), str(w.id))
	if w.get("awakened", false):
		var ak := CraftingAuthority.awakened_skill(str(w.id))
		if not ak.is_empty() and _count_to(combat.awaken_hits, c.id, int(ak.get("every_hits", 12))):
			_skill_strike(c, ak, float(ak.get("mult", 1.5)), "awakened:" + str(w.id), str(w.id))

## One more blow on a counter; true (and the count starts again) when it reaches `every`.
func _count_to(counts: Dictionary, actor_id: String, every: int) -> bool:
	var n := int(counts.get(actor_id, 0)) + 1
	if n < every:
		counts[actor_id] = n
		return false
	counts[actor_id] = 0
	return true

## A skill that strikes on its own: a ring around the wielder, or projectiles that pass through every foe in their path.
func _skill_strike(c, sk: Dictionary, m: float, source: String, item_id: String) -> void:
	var pv := combat.player_view(c)
	var atk := {"damage_type": str(sk.get("damage_type", "qi")), "element": str(sk.get("element", "none")), "mult": [m, m], "range": [0.95, 1.05], "source": source}
	var here := Vector2(float(pv.x), float(pv.y))
	if str(sk.get("shape", "")) == "ring":
		for e in combat._enemies_within(here, float(sk.get("reach", 160))):
			combat.player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
	else:
		var n := maxi(1, int(sk.get("count", 1)))
		for i in n:
			combat.projectiles.spawn_projectile({"team": "player", "owner": c.id, "x": here.x, "y": here.y + (i - (n - 1) * 0.5) * 14.0, "alt": float(pv.alt) + 60.0,
				"dir": int(combat.timeline(c.id).facing), "speed": 760.0, "range": float(sk.get("reach", 260)), "pierce": 99, "art": str(sk.get("art", "flying_sword")),
				"attack": atk, "delay": i * 0.08})
	emit("artifact_skill_used", {"actor": c.id, "item": item_id, "skill": str(sk.get("name", "")), "x": here.x, "y": here.y,
		"ring": float(sk.get("reach", 0)) if str(sk.get("shape", "")) == "ring" else 0.0, "awakened": source.begins_with("awakened")})

## S48 the Poison Body (v1.1): with a poison art known and toxicity past half its tolerance, each hit turns a point of
## the body's own toxicity into poison on the foe (once per foe per half second).
func poison_body_active(c) -> bool:
	if c == null: return false
	var tol: float = maxf(1.0, c.stats.value("toxicity_tolerance"))
	return float(c.cultivator.toxicity) > tol * poison_body_threshold(c) and ProgressionRules.knows_poison_art(c)

## The share of toxicity tolerance past which the Poison Body opens (Venom Hand lowers it).
func poison_body_threshold(c) -> float:
	return float(StatRules.set_flag(c, "venom_hand").get("threshold", ContentDB.stat_const("poison_body", {}).get("threshold", 0.5)))

func poison_body(c, e: EnemyState) -> void:
	if not e.alive or e.pools.steadfast.has("poison") or not poison_body_active(c): return
	var cfg: Dictionary = ContentDB.stat_const("poison_body", {})
	if game.sim_time - float(combat.poison_touch.get(e.uid, -99.0)) < float(cfg.get("per_foe_s", 0.5)): return
	combat.poison_touch[e.uid] = game.sim_time
	game.progression.apply_toxicity(c.id, -float(cfg.get("toxicity_per_hit", 1.0)))
	combat.apply_status_to_enemy(e, {"id": "poison", "power": float(cfg.get("power", 0.02)), "remaining": float(cfg.get("duration_s", 4.0)), "source": c.id})

## A weapon oil on the blade (S44): each hit may carry its status to the foe. Rolled on its own stream, so a
## fight without oil keeps the combat stream's sequence.
func oil_strike(c, e: EnemyState, ev: Dictionary) -> void:
	var venom := StatRules.set_flag(c, "venom_hand")
	for st in c.pools.statuses:
		var oil: Dictionary = ContentDB.entry("status_effects", str(st.id)).get("oil", {})
		if oil.is_empty() or e.pools.steadfast.has(str(oil.status)): continue
		var applied := CombatRules.status_roll({"id": str(oil.status), "chance": float(venom.get("oil_chance", oil.get("chance", 0.2))), "power": float(oil.get("power", 0.02)),
			"duration_s": float(oil.get("duration_s", 4.0))}, ev, Rng.stream(c.id, "oil"))
		if not applied.is_empty():
			applied.source = c.id
			combat.apply_status_to_enemy(e, applied)
