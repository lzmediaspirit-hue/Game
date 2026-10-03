class_name CombatHeals
extends CombatPart
## CombatAuthority's part for heals: heals over time on you (S15) and on your companions and pets (S47 v1.1), the
## healing song around the caster, and the sect roles' support variants (S48). State: `combat.hots`, `combat.ally_hots`.

func apply_heal(actor_id: String, pct: float, amount: float, over_s: float, source: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var total := heal_total(c, pct, amount)
	if over_s > 0.0:
		# A fifth at once, the rest spread over the time given; it runs in a fight too, and resting does not multiply it.
		combat.apply_resource_change(actor_id, "hp", total * 0.2, source)
		var list: Array = combat.hots.get(actor_id, [])
		list.append({"per_s": total * 0.8 / over_s, "left": over_s, "total": over_s, "source": source})
		combat.hots[actor_id] = list
	else:
		combat.apply_resource_change(actor_id, "hp", total, source)

## The HP a heal of `pct` of max HP plus `amount` gives this character (S48 Mercy raises it).
static func heal_total(c, pct: float, amount: float) -> float:
	return (amount + c.pools.max_hp * pct) * (1.0 + c.stats.value("healing_received"))

## The heals over time still running on a character, for the HUD's status row: [{source, left, total, per_s}].
func hots_of(actor_id: String) -> Array:
	return combat.hots.get(actor_id, [])

func tick_hots(c, delta: float) -> void:
	var list: Array = combat.hots.get(c.id, [])
	if list.is_empty(): return
	if combat.wounded.has(c.id):
		combat.hots.erase(c.id)
		return
	var gain := 0.0
	for h in list:
		var step := minf(delta, float(h.left))
		gain += float(h.per_s) * step
		h.left = float(h.left) - step
	combat.hots[c.id] = list.filter(func(h): return float(h.left) > 0.0)
	if gain > 0.0 and c.pools.hp < c.pools.max_hp: combat.apply_resource_change(c.id, "hp", gain, "heal", 0.0, true)

func tick_ally_hots(delta: float) -> void:
	var ally_hots: Dictionary = combat.ally_hots
	if ally_hots.is_empty() or game.room_rt == null: return
	for uid in ally_hots.keys():
		var e: EnemyState = game.room_rt.enemies.get(uid)
		if e == null or not e.alive:
			ally_hots.erase(uid)
			continue
		var list: Array = ally_hots[uid]
		for h in list:
			var step := minf(delta, float(h.left))
			e.pools.hp = minf(e.pools.max_hp, e.pools.hp + float(h.per_s) * step)
			h.left = float(h.left) - step
		list = list.filter(func(h): return float(h.left) > 0.0)
		if list.is_empty(): ally_hots.erase(uid)
		else: ally_hots[uid] = list

## A healing song around the caster (Clear Heart Melody): the caster and every ally within the radius recover
## `pct` of their health each second for `seconds`. Returns how many allies it reached.
func heal_circle(c, pct: float, seconds: float, radius: float, source: String) -> int:
	apply_heal(c.id, pct * seconds, 0.0, seconds, source)
	if game.room_rt == null: return 0
	var pv := combat.player_view(c)
	var at := Vector2(float(pv.x), float(pv.y))
	var n := 0
	for e in game.room_rt.living_enemies():
		if e.team != "ally" or e.plane.distance_to(at) > radius: continue
		var list: Array = combat.ally_hots.get(e.uid, [])
		list.append({"per_s": e.pools.max_hp * pct, "left": seconds})
		combat.ally_hots[e.uid] = list
		n += 1
	# S48 the Buddhist path: healing an ally is merit (a few times a day).
	if n > 0: game.relations.apply_daily_deed(c.id, "heal_ally", int(ContentDB.stat_const("paths", {}).get("buddhist", {}).get("heal_ally_daily", 5)))
	return n

# ------------------------------------------------------------------ sect role variants (S48)
## The support variant: a heal for you and your allies near you (Mending Current) or a shield for you and a heal for
## your allies (Guarding Cloud). It grows with the crafts you have ranked up and the Lotus branch.
func sect_support_mult(c) -> float:
	var cfg: Dictionary = ContentDB.config("sect_roles")
	var ranks := 0
	for craft in c.professions: ranks += game.crafting.rank_index(str(c.professions[craft].get("rank", "apprentice")))
	var craft_bonus := minf(float(cfg.get("profession_cap", 0.5)), float(cfg.get("profession_scaling", 0.05)) * ranks)
	return (1.0 + craft_bonus) * (1.0 + ProgressionRules.sect_tree_flag(c, "support_heal_mult"))

func sect_support(c, v: Dictionary) -> void:
	var mult := sect_support_mult(c)
	var pct := float(v.get("heal_pct", 0.0)) * mult
	if pct > 0.0 and not v.get("allies_only", false): apply_heal(c.id, pct, 0.0, 0.0, "sect_support")
	if float(v.get("shield_pct", 0.0)) > 0.0:
		combat.raise_shield(c, c.pools.max_hp * float(v.shield_pct) * mult, float(v.get("shield_s", 4)))
	if pct <= 0.0 or game.room_rt == null: return
	var pv := combat.player_view(c)
	var at := Vector2(float(pv.x), float(pv.y))
	for e in game.room_rt.living_enemies():
		if e.team == "ally" and e.plane.distance_to(at) <= float(v.get("radius", 220)):
			e.pools.hp = minf(e.pools.max_hp, e.pools.hp + e.pools.max_hp * pct)
