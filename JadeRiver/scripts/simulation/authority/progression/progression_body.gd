class_name ProgressionBody
extends ProgressionPart
## ProgressionAuthority's part: body XP and training, the body ladder's tiers, and the physiques earned by deeds with
## the lifetime counts they read (S48).

# ------------------------------------------------------------------ the body ladder and physiques (S48)
func apply_body_xp(actor_id: String, xp: float, _source: String) -> void:
	var c = game.character(actor_id)
	if c == null or xp <= 0.0: return
	var growth := float(ProgressionRules.method(c.cultivator.method_id).get("body_growth", 0.0))
	c.cultivator.body_xp += xp * (1.0 + growth)
	var leveled := false
	while c.cultivator.body_xp >= ProgressionRules.body_xp_needed(c.cultivator.body_level):
		c.cultivator.body_xp -= ProgressionRules.body_xp_needed(c.cultivator.body_level)
		c.cultivator.body_level += 1
		leveled = true
	if leveled:
		emit("body_level_changed", {"actor": c.id, "value": c.cultivator.body_level})
		check_body_tier(c)

## A Temper trial passed (the trial event's on_complete). The tier opens once its bath is taken too.
func pass_body_trial(actor_id: String, tier: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("body_tiers", tier): return
	if not tier in c.cultivator.body_trials: c.cultivator.body_trials.append(tier)
	emit("body_trial_passed", {"actor": c.id, "tier": tier, "bath": str(ContentDB.entry("body_tiers", tier).get("bath", ""))})
	check_body_tier(c)

## The next rung opens when the body level, the trial and the bath are all there; one rung at a time.
func check_body_tier(c) -> void:
	var cu: CultivatorState = c.cultivator
	for _i in 4:
		var need := ProgressionRules.body_tier_needs(cu)
		if need.is_empty() or not (need.level and need.trial and need.bath): return
		var t := ContentDB.entry("body_tiers", str(need.tier))
		cu.body_tier = str(t.id)
		for rid in t.get("teaches", []): game.apply_effects(c.id, [{"kind": "learn_recipe", "recipe": str(rid)}], "body_tier")
		if not game.account.codex.has("body_ladder"): game.quest.apply_codex("body_ladder")
		emit("body_tier_reached", {"actor": c.id, "tier": cu.body_tier, "name": str(t.get("name", ""))})
		# Stone Marrow: Copper Body before Qi Unfurling 3.
		var early := ContentDB.entry("physiques", "stone_marrow")
		if cu.body_tier == "copper" and not early.is_empty() and not ProgressionRules.at_least(cu.realm_key, str(early.get("before", "qi_unfurling_3"))):
			awaken_physique(c.id, "stone_marrow")

## A physique, earned by a deed: it stays for life, gift and drawback both.
func awaken_physique(actor_id: String, physique: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("physiques", physique) or physique in c.cultivator.physiques: return
	c.cultivator.physiques.append(physique)
	if not game.account.codex.has("physiques"): game.quest.apply_codex("physiques")
	emit("physique_awakened", {"actor": c.id, "physique": physique, "name": ContentDB.name_of("physiques", physique)})

## Lifetime counters (S48 physiques read them): add, then awaken any physique whose count is reached.
func add_lifetime(c, key: String, amount: float) -> void:
	if c == null or amount <= 0.0: return
	var v := float(c.cultivator.lifetime_stats.get(key, 0.0)) + amount
	c.cultivator.lifetime_stats[key] = v
	for ph in ContentDB.all("physiques"):
		if str(ph.get("earned", "")) == key and ph.has("count") and v >= float(ph.count): awaken_physique(c.id, str(ph.id))

## Yin Vessel: a night counts once the character has sat through a minute of it at the Falls Pool.
func falls_pool_second(c) -> void:
	var ls: Dictionary = c.cultivator.lifetime_stats
	var night := Clock.game_day(Clock.now_utc())
	if int(ls.get("falls_pool_night", -1)) != night:
		ls["falls_pool_night"] = night
		ls["falls_pool_s"] = 0.0
	if float(ls.falls_pool_s) >= 60.0: return
	ls["falls_pool_s"] = float(ls.falls_pool_s) + 1.0
	if float(ls.falls_pool_s) >= 60.0: add_lifetime(c, "falls_pool_nights", 1.0)

## Kills in a row, each within 10 s of the last. Blood Memory (a fate) feeds the heart demon at every 10.
func count_streak(c) -> void:
	var k: Dictionary = ContentDB.config("fates").get("streak", {})
	var sk: Dictionary = progression.streaks.get(c.id, {"n": 0, "t": -999.0})
	sk.n = int(sk.n) + 1 if game.sim_time - float(sk.t) <= float(k.get("window_s", 10.0)) else 1
	sk.t = game.sim_time
	progression.streaks[c.id] = sk
	if int(sk.n) % int(k.get("kills", 10)) == 0 and progression.fate_flag(c, "streak_heart_demon"): progression.apply_heart_demon(c.id, 1.0, "blood_memory")

## Ember Heart: every Fire pill refined counts, by the pill.
func on_fire_pill(p: Dictionary) -> void:
	if str(p.get("craft", "")) != "alchemy" or str(ContentDB.entry("recipes", str(p.get("recipe", ""))).get("element", "")) != "fire": return
	add_lifetime(game.character(str(p.get("actor", ""))), "fire_pills", float(p.get("count", 0)))

## Cloud Lung: the ground covered gliding or flying, in metres.
func add_air_distance(actor_id: String, px: float) -> void:
	var c = game.character(actor_id)
	if c == null or px <= 0.0: return
	add_lifetime(c, "air_metres", px / float(ContentDB.stat_const("body_path", {}).get("air_metre_px", 50)))

func on_object_hit(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	var type := str(p.get("type", ""))
	if type in ["training_stump", "training_dummy"] and Unlocks.is_unlocked(c.id, "body_training"):
		var per_hit := 1.0 / 60.0 / 1.4
		if ProgressionRules.is_body_stage(c.cultivator.realm_key) and Unlocks.is_unlocked(c.id, "cultivation"):
			progression.apply_progress(c.id, float(ContentDB.curve("training_qp_per_min", 40)) * per_hit, "training")
		apply_body_xp(c.id, float(ContentDB.curve("training_body_xp_per_min", 20)) * per_hit, "training")
	elif type == "lifting_stone" and Unlocks.is_unlocked(c.id, "body_training"):
		if ProgressionRules.is_body_stage(c.cultivator.realm_key) and Unlocks.is_unlocked(c.id, "cultivation"):
			progression.apply_progress(c.id, float(ContentDB.curve("training_qp_per_min", 40)) * 3.0 / 60.0, "training")
		apply_body_xp(c.id, float(ContentDB.curve("training_body_xp_per_min", 20)) * 4.5 / 60.0, "training")
