class_name CombatAuthority
extends Authority
## S11/S12/S30/S31 · Owns the ResourcePools (HP, QI, Soul, Composure, Hollowing),
## StatBlock recalculation, active attacks and projectiles, status effects,
## cooldowns and combat timers. One damage pipeline (CombatRules) for everyone.

var actors: Dictionary = {}          # actor id -> combat timeline for players/companions
var wounded: Dictionary = {}         # actor -> {cause, timer, no_penalty}
var spar: Dictionary = {}            # active spar {opponent uid, actor}
var hitstop := 0.0

const STAT_EVENTS := ["realm_changed", "level_changed", "equipment_changed", "injury_added", "injury_healed", "title_changed",
	"attributes_changed", "method_changed", "dao_tier_up", "body_level_changed", "purity_changed", "soul_changed",
	"legacy_recorded", "consolidation_finished", "aptitude_revealed", "collection_page_completed"]

func intents() -> Array:
	return ["basic_attack", "use_technique", "guard_start", "guard_end", "dodge", "choose_revival", "start_flight", "stop_flight", "use_treasure",
		"plunge", "glide"]

var attune: Dictionary = {}          # actor -> {dealt, taken} for the zone they stand in (S18)
var flying: Dictionary = {}          # actor -> true while flight holds them up (S18); QI pays for it
var gliding: Dictionary = {}         # actor -> true while Falling Leaf Glide holds them (S43); 2 QI a second
var treasure_fx: Dictionary = {}     # actor -> {reflect, gourd, gourd_r, wisps}: a treasure's lingering effect (G2)
var captured: Dictionary = {}        # enemy uid -> true: taken by the Beast-Taking Cauldron (World doubles its materials)

func subscribe() -> void:
	for ev in STAT_EVENTS:
		GameEvents.subscribe(ev, _on_stat_source, 20)
	GameEvents.subscribe("attunement_changed", func(p): attune[str(p.get("actor", ""))] = {"dealt": float(p.dealt), "taken": float(p.taken)}, 20)
	GameEvents.subscribe("room_entered", func(p): if flying.has(str(p.get("actor", ""))): stop_flight(str(p.actor), "room"), 20)

func _on_stat_source(p: Dictionary) -> void:
	refresh_stats(str(p.get("actor", "")))

func refresh_stats(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var changed := StatRules.rebuild(c)
	if not changed.is_empty():
		emit("stats_changed", {"actor": c.id, "changed_ids": changed})
		for pool in ["hp", "qi", "soul"]:
			emit("resource_changed", {"actor": c.id, "pool": pool, "value": c.pools.get_value(pool), "max": c.pools.get_max(pool)})

func timeline(actor_id: String) -> Dictionary:
	if not actors.has(actor_id):
		actors[actor_id] = {"action": "", "t": 0.0, "duration": 0.0, "hit_at": 0.0, "hit_done": true, "combo": -1, "window": 0.0,
			"queued": 0, "family": "fists", "technique": "", "guard": false, "guard_t": 0.0, "dodge_t": 0.0, "facing": 1,
			"forced": Vector2.ZERO, "forced_t": 0.0, "flinch": 0.0, "stance": 0.0, "last_attack_facing": 1, "hits": 0, "targets_hit": []}
	return actors[actor_id]

func is_busy(actor_id: String) -> bool:
	var tl := timeline(actor_id)
	return tl.action != "" and float(tl.t) < float(tl.duration)

func is_stunned(actor_id: String) -> bool:
	var c = game.character(actor_id)
	return c != null and (c.pools.blocked("attack") or c.pools.blocked("move"))

func is_wounded(actor_id: String) -> bool:
	return wounded.has(actor_id)

## Movement the presentation must feed into LocalAuthority this frame (dodge, dashes, knockback).
func forced_motion(actor_id: String) -> Dictionary:
	var tl := timeline(actor_id)
	if float(tl.forced_t) > 0.0: return {"velocity": tl.forced, "time": tl.forced_t}
	return {}

func move_factor(actor_id: String) -> float:
	var c = game.character(actor_id)
	if c == null: return 1.0
	if wounded.has(actor_id) or c.pools.blocked("move"): return 0.0
	var tl := timeline(actor_id)
	var f := 1.0
	if tl.guard: f *= float(ContentDB.stat_const("move.guard_factor", 0.5))
	# S43 rule 2: attacking on the ground slows you to x0.3; in the air you keep x0.8 and still make the gap.
	if is_busy(actor_id): f *= float(ContentDB.stat_const("move.air_attack_factor", 0.8)) if airborne(actor_id) else float(ContentDB.stat_const("move.attack_factor", 0.3))
	var slow = c.pools.status("slow")
	if not slow.is_empty(): f *= 1.0 - clampf(float(slow.power), 0.0, 0.5)
	if float(tl.flinch) > 0.0: f *= 0.2
	return f

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"basic_attack": return basic_attack(c, int(intent.get("facing", 1)))
		"use_technique": return use_technique(c, int(intent.get("slot", -1)), int(intent.get("facing", 1)))
		"guard_start": return guard(c, true)
		"guard_end": return guard(c, false)
		"dodge": return dodge(c, intent.get("direction", Vector2.ZERO), int(intent.get("facing", 1)))
		"choose_revival": return choose_revival(c, str(intent.get("where", "shrine")))
		"start_flight": return start_flight(c)
		"use_treasure": return use_treasure(c, int(intent.get("slot", 0)))
		"plunge": return plunge(c)
		"glide": return glide(c, bool(intent.get("on", true)))
		"stop_flight":
			stop_flight(c.id, str(intent.get("reason", "landed")))
			return ok()
	return fail("unknown_intent")

# ------------------------------------------------------------------ flight (S18)
## Cloud Stride lets Qi hold the body in the air. The movement solver moves it; Combat
## owns whether it may, and pays the QI every second.
func start_flight(c) -> Dictionary:
	var cfg: Dictionary = ContentDB.stat_const("flight", {})
	if not Unlocks.is_unlocked(c.id, str(cfg.get("unlock", "flight"))): return fail("locked", {"text": Unlocks.locked_text("flight")})
	if flying.has(c.id): return fail("already_flying")
	if wounded.has(c.id) or c.pools.blocked("move"): return fail("blocked")
	if not flight_allowed(c.id):
		return fail("no_flight", {"text": Tx.t("sim.combat.no_flight_here")})
	if c.pools.qi < c.pools.max_qi * float(cfg.get("start_qi_pct", 0.1)) or c.pools.max_qi <= 0.0:
		return fail("no_qi", {"text": Tx.t("sim.combat.not_enough_qi_to_fly")})
	flying[c.id] = true
	emit("flight_started", {"actor": c.id})
	emit("system_used", {"actor": c.id, "system": "flight"})
	return ok({"climb": float(cfg.get("climb", 220)), "ceiling": float(cfg.get("ceiling", 340))})

## Flight is refused indoors, on sect grounds, in dungeons, in rooms that forbid it and inside a no_flight
## volume (S43); gliding still works there.
func flight_allowed(actor_id: String) -> bool:
	var room: Dictionary = game.room_rt.def if game.room_rt else {}
	if room.get("no_flight", false) or str(room.get("type", "")) in ContentDB.stat_const("flight.no_flight_types", ["interior"]): return false
	var st: ActorState = game.actor_state(actor_id)
	if st != null and game.room_rt and not game.room_rt.geometry.volume_at(st.plane, st.altitude, "no_flight").is_empty(): return false
	return true

func stop_flight(actor_id: String, reason: String) -> void:
	if not flying.has(actor_id): return
	flying.erase(actor_id)
	emit("flight_ended", {"actor": actor_id, "reason": reason})

func is_flying(actor_id: String) -> bool:
	return flying.has(actor_id)

## The flight vessel ridden (S47): what the air costs.
func vessel_qi_mult(c) -> float:
	return float(ContentDB.item(str(c.inventory.vessel)).get("flight", {}).get("qi_mult", 1.0)) if str(c.inventory.vessel) != "" else 1.0

func _tick_flight(c, delta: float) -> void:
	if not flying.has(c.id): return
	if wounded.has(c.id):
		stop_flight(c.id, "wounded")
		return
	if not flight_allowed(c.id):
		stop_flight(c.id, "no_flight")
		return
	var cfg: Dictionary = ContentDB.stat_const("flight", {})
	var cost = maxf(float(cfg.get("qi_min_per_s", 2.0)), c.pools.max_qi * float(cfg.get("qi_pct_per_s", 0.02))) * delta * game.pets.flight_qi_mult(c) \
		* vessel_qi_mult(c)
	if c.pools.qi <= cost:
		stop_flight(c.id, "no_qi")
		return
	apply_resource_change(c.id, "qi", -cost, "flight", 0.0, true)

# ------------------------------------------------------------------ movement arts (S43)
## The movement art a secret art grants (secret_arts.json `movement_art`), known to this character.
func knows_art(c, art: String) -> bool:
	for sa in c.cultivator.secret_arts:
		if str(ContentDB.entry("secret_arts", str(sa)).get("movement_art", "")) == art: return true
	return false

## Plunge (Bone Forging 4): Down + Attack in the air drops at 900; the landing strikes within 60.
func plunge(c) -> Dictionary:
	if not knows_art(c, "plunge"): return fail("locked")
	var why := can_act(c)
	if why != "": return fail(why)
	if c.pools.cooldown("plunge") > 0.0: return fail("cooldown")
	var st: ActorState = game.actor_state(c.id)
	if st == null: return fail("no_body")
	st.arts["plunge"] = true
	if not MovementSolver.plunge(st): return fail("not_airborne")
	c.pools.cooldowns["plunge"] = float(ContentDB.movement("plunge.cooldown_s", 4.0))
	LocalAuthority.announce(st, c.id)
	return ok()

## The Plunge lands: 120% damage and a 0.5 s stun to foes within 60 of the landing, breakables broken (S43).
func _resolve_plunge(c, st: ActorState) -> void:
	var at: Dictionary = st.plunge_impact
	st.plunge_impact = {}
	var here := Vector2(float(at.x), float(at.y))
	var radius := float(ContentDB.movement("plunge.radius", 60.0))
	var pv := player_view(c)
	var hitbox := {"x": [-radius, radius], "depth": radius, "alt": ContentDB.movement("combat_bands.melee", [-30, 60])}
	var atk := {"damage_type": "physical", "element": "none", "mult": [float(ContentDB.movement("plunge.mult", 1.2)), float(ContentDB.movement("plunge.mult", 1.2))],
		"range": [1.0, 1.0], "knockback": 0.0, "source": "plunge"}
	var struck := 0
	for e in _enemies_within(here, radius):
		if not hit_test(pv, 1, hitbox, enemy_view(e), true): continue
		_player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
		if e.alive and not e.is_boss():
			_apply_status_to_enemy(e, {"id": "stun", "power": 1.0, "remaining": float(ContentDB.movement("plunge.stun_s", 0.5)), "source": c.id})
		struck += 1
	for o in game.world.hittable_objects(pv, 1, hitbox):
		game.world.apply_object_hit(c.id, o)
	emit("system_used", {"actor": c.id, "system": "plunge_strike"})
	if struck > 0: hitstop = float(ContentDB.stat_const("combat.hitstop_crit", 0.08))

## Falling Leaf Glide (Qi Kindling 3): Jump held while descending. 2 QI a second while it lasts.
func glide(c, on: bool) -> Dictionary:
	var st: ActorState = game.actor_state(c.id)
	if not on:
		gliding.erase(c.id)
		if st != null: MovementSolver.glide(st, false)
		return ok()
	if not knows_art(c, "glide"): return fail("locked")
	if wounded.has(c.id) or c.pools.blocked("move"): return fail("blocked")
	if st == null: return fail("no_body")
	if c.pools.max_qi <= 0.0 or c.pools.qi < float(ContentDB.movement("glide.qi_per_s", 2.0)) * 0.25: return fail("no_qi", {"text": Tx.t("sim.combat.not_enough_qi_to_glide")})
	st.arts["glide"] = true
	if not MovementSolver.glide(st, true): return fail("not_airborne")
	gliding[c.id] = true
	LocalAuthority.announce(st, c.id)
	return ok()

func is_gliding(actor_id: String) -> bool:
	return gliding.has(actor_id)

func _tick_glide(c, delta: float) -> void:
	if not gliding.has(c.id): return
	var st: ActorState = game.actor_state(c.id)
	if st == null or not st.gliding:
		gliding.erase(c.id)
		return
	var cost := float(ContentDB.movement("glide.qi_per_s", 2.0)) * delta
	if c.pools.qi <= cost:
		gliding.erase(c.id)
		MovementSolver.glide(st, false)
		return
	apply_resource_change(c.id, "qi", -cost, "glide", 0.0, true)

# ------------------------------------------------------------------ views
func player_view(c) -> Dictionary:
	var sb: StatBlock = c.stats
	var tl := timeline(c.id)
	var st: ActorState = game.actor_state(c.id)
	var v := {"kind": "player", "id": c.id, "level": ProgressionRules.level(c), "realm_index": ProgressionRules.realm_index(c.cultivator.realm_key),
		"element": str(ProgressionRules.method(c.cultivator.method_id).get("affinity", "none")),
		"physical_attack": sb.value("physical_attack"), "qi_attack": sb.value("qi_attack"), "soul_attack": sb.value("soul_attack"),
		"accuracy": sb.value("accuracy"), "crit_chance": sb.value("crit_chance"), "crit_damage": sb.value("crit_damage"),
		"penetration": sb.value("penetration"), "elemental_power": sb.value("elemental_power"),
		"energy_mult": ProgressionRules.energy_multiplier(c.cultivator.energy_type, c.cultivator.purity),
		"tenacity": sb.value("tenacity"), "evasion": sb.value("evasion"), "physical_defense": sb.value("physical_defense"),
		"qi_resistance": sb.value("qi_resistance"), "soul_defense": sb.value("soul_defense"),
		"vulnerable": c.pools.has_status("vulnerable"), "shocked": c.pools.has_status("shock"),
		"guarding": sb.value("guard") if tl.guard else 0.0, "facing": int(tl.facing),
		"x": st.plane.x if st else 0.0, "y": st.plane.y if st else 0.0, "alt": st.altitude if st else 0.0, "half_width": 14.0, "height": 88.0}
	for el in ["water", "wood", "fire", "earth", "metal"]:
		v["resist_" + el] = sb.conditional("elemental_resistance", "element", el)
		v["element_power_" + el] = sb.conditional("elemental_power", "element", el)
	return v

func enemy_view(e: EnemyState) -> Dictionary:
	var s := e.stats
	return {"kind": "enemy", "id": str(e.uid), "level": e.level, "realm_index": e.realm_index, "element": e.element,
		"physical_attack": float(s.attack), "qi_attack": float(s.attack), "soul_attack": float(s.attack), "accuracy": float(s.accuracy),
		"crit_chance": float(s.crit_chance), "crit_damage": float(s.crit_damage), "penetration": 0.0, "energy_mult": 1.0,
		"tenacity": float(s.tenacity), "evasion": float(s.evasion), "physical_defense": float(s.physical_defense),
		"qi_resistance": float(s.qi_resistance), "soul_defense": float(s.soul_defense),
		"vulnerable": e.pools.has_status("vulnerable"), "shocked": e.pools.has_status("shock"),
		"resist_" + CombatRules.parent_element(e.element): float(ContentDB.stat_const("mob.own_element_resistance", 0.3)),
		"guarding": float(e.def.get("front_guard", 0.0)) if e.ai.state == "guard" else 0.0,
		"x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover, "half_width": e.half_width(), "height": e.height()}

## 2.5D hit test (S12): x range in the facing direction, depth band, altitude overlap.
static func hit_test(a: Dictionary, facing: int, hitbox: Dictionary, t: Dictionary, both_sides := false) -> bool:
	var xr: Array = hitbox.get("x", [0, 40])
	var dx := (float(t.x) - float(a.x)) * facing
	if both_sides: dx = absf(float(t.x) - float(a.x))
	var hw := float(t.get("half_width", 16))
	if dx < float(xr[0]) - hw or dx > float(xr[1]) + hw: return false
	if absf(float(t.y) - float(a.y)) > float(hitbox.get("depth", 26)): return false
	var alt: Array = hitbox.get("alt", [0, 90])
	var a0 := float(a.alt) + float(alt[0])
	var a1 := float(a.alt) + float(alt[1])
	var t0 := float(t.alt)
	var t1 := float(t.alt) + float(t.get("height", 60))
	return a1 >= t0 and a0 <= t1

# ------------------------------------------------------------------ player attacks (S30)
func can_act(c) -> String:
	if wounded.has(c.id): return "wounded"
	if c.pools.blocked("attack"): return "stunned"
	if game.progression.is_channeling(c.id): return "breaking_through"
	if c.cultivator.meditating: game.progression.stop_meditation(c, "attack")
	return ""

func target_for(c, reach: float, depth: float, facing: int) -> Dictionary:
	# Auto-target: nearest enemy in the facing direction within reach and depth band;
	# otherwise turn toward the nearest enemy within 160 units.
	if game.room_rt == null: return {"facing": facing}
	var pv := player_view(c)
	var best: EnemyState = null
	var best_d := INF
	var turn_to := facing
	var nearest_any := INF
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden: continue
		var dx: float = e.plane.x - float(pv.x)
		var dy: float = absf(e.plane.y - float(pv.y))
		var dist := absf(dx)
		if dy <= depth and dx * facing >= -e.half_width() and dist <= reach + e.half_width() and dist < best_d:
			best = e
			best_d = dist
		var near := Vector2(dx, dy).length()
		if near < nearest_any and near <= float(ContentDB.stat_const("combat.auto_turn_range", 160)):
			nearest_any = near
			turn_to = 1 if dx >= 0 else -1
	if best: return {"facing": facing, "target": best.uid}
	return {"facing": turn_to}

## In the air: neither standing on a surface, climbing nor flying (S43).
func airborne(actor_id: String) -> bool:
	var st: ActorState = game.actor_state(actor_id)
	return st != null and st.surface == null and not st.flying and st.climbing.is_empty()

## Hands are busy on a ladder, rope, vine or chain: techniques wait unless flagged on_climb (S43 rule 5).
func climbing(actor_id: String) -> bool:
	var st: ActorState = game.actor_state(actor_id)
	return st != null and not st.climbing.is_empty()

func basic_attack(c, facing: int) -> Dictionary:
	var reason := can_act(c)
	if reason != "": return fail(reason)
	if climbing(c.id): return fail("climbing")
	if not Unlocks.is_unlocked(c.id, "attack"): return fail("locked")
	var tl := timeline(c.id)
	facing = 1 if facing >= 0 else -1
	var fam := StatRules.family(c)
	var combo: Array = fam.get("combo", [])
	if combo.is_empty(): return fail("no_combo")
	var in_air := airborne(c.id)
	if is_busy(c.id):
		if not in_air and int(tl.combo) >= 0 and int(tl.combo) < combo.size() - 1: tl.queued = mini(int(tl.queued) + 1, combo.size() - 1 - int(tl.combo))
		return ok({"queued": true})
	# S43 air attack: one hit, no combo, +10% damage.
	var index := 0 if in_air else (int(tl.combo) + 1 if float(tl.window) > 0.0 and int(tl.combo) < combo.size() - 1 else 0)
	var aim := target_for(c, float(fam.get("reach", 46)), float(fam.get("depth", 30)), facing)
	_start_step(c, fam, index, int(aim.facing))
	if in_air:
		tl.step = (tl.step as Dictionary).duplicate()
		tl.step.mult = float(tl.step.get("mult", 1.0)) * float(ContentDB.stat_const("move.air_attack_mult", 1.1))
		tl.air_attack = true
	else:
		tl.air_attack = false
	return ok({"action": tl.action, "duration": tl.duration, "facing": tl.facing, "combo": index, "air": in_air})

func _start_step(c, fam: Dictionary, index: int, facing: int) -> void:
	var tl := timeline(c.id)
	var step: Dictionary = fam.combo[index]
	var speed = 1.0 + c.stats.value("attack_speed")
	tl.action = str(step.action)
	tl.t = 0.0
	tl.duration = float(step.duration) / speed
	tl.hit_at = float(step.hit_at) / speed
	tl.hit_done = false
	tl.combo = index
	tl.window = 0.0
	tl.family = str(fam.id)
	tl.technique = ""
	tl.facing = facing
	tl.step = step
	tl.targets_hit = []
	if game.character(c.id).cultivator.meditating: game.progression.stop_meditation(c, "attack")
	emit("attack_started", {"actor": c.id, "action": tl.action, "technique": "", "windup": tl.hit_at, "duration": tl.duration, "facing": facing, "combo": index})

func use_technique(c, slot: int, facing: int) -> Dictionary:
	var reason := can_act(c)
	if reason != "": return fail(reason)
	if slot < 0 or slot >= ProgressionRules.technique_slot_count(c): return fail("slot_locked")
	var tid = c.cultivator.technique_slots[slot]
	if tid == null or str(tid) == "": return fail("empty_slot")
	var t := ContentDB.entry("techniques", str(tid))
	var tl := timeline(c.id)
	if is_busy(c.id): return fail("busy")
	if climbing(c.id) and not t.get("on_climb", false): return fail("climbing")
	var fam := StatRules.family(c)
	var tfam := str(t.get("family", "any"))
	if tfam != "any" and not (tfam == str(fam.id) or (tfam == "fists" and fam.id in ["fists", "gauntlets"])): return fail("wrong_weapon", {"text": Tx.t("sim.combat.needs_a") % tfam.replace("_", " ")})
	if c.pools.cooldown("tech:" + str(tid)) > 0.0: return fail("cooldown")
	if c.pools.has_status("qi_seal"): return fail("sealed")
	if t.get("flying_only", false):
		var st: ActorState = game.actor_state(c.id)
		if st == null or st.surface != null: return fail("needs_flight")
	var cost := technique_cost(c, t)
	if float(t.get("qi_cost", 0)) > 0 and (c.pools.max_qi <= 0.0 or c.pools.qi < cost): return fail("no_qi")
	if float(t.get("soul_cost", 0)) > 0 and c.pools.soul < float(t.soul_cost): return fail("no_soul")
	if float(t.get("composure_cost", 0)) > 0 and c.pools.composure < float(t.composure_cost): return fail("no_composure")
	apply_resource_change(c.id, "qi", -cost, "technique")
	if float(t.get("soul_cost", 0)) > 0: apply_resource_change(c.id, "soul", -float(t.soul_cost), "technique")
	if float(t.get("composure_cost", 0)) > 0:
		apply_resource_change(c.id, "composure", -float(t.composure_cost), "technique")
		c.pools.since_composure_use = 0.0
	c.pools.cooldowns["tech:" + str(tid)] = float(t.get("cooldown_s", 5))
	var aim := target_for(c, float(t.hitbox.x[1]), float(t.hitbox.get("depth", 30)), 1 if facing >= 0 else -1)
	var action := str(t.get("action", ""))
	if action == "" or action == "null": action = str(fam.combo[mini(2, fam.combo.size() - 1)].action)
	if action == "meditate_burst": action = str(fam.combo[0].action)
	tl.action = action
	tl.t = 0.0
	tl.duration = float(t.get("windup_s", 0.2)) + float(t.get("active_s", 0.2)) + 0.25
	tl.hit_at = float(t.get("windup_s", 0.2))
	tl.hit_done = false
	tl.combo = -1
	tl.queued = 0
	tl.technique = str(tid)
	tl.facing = int(aim.facing)
	tl.targets_hit = []
	tl.step = {}
	if t.has("dash"):
		var dist := float(t.dash)
		tl.forced = Vector2(tl.facing * dist / 0.2, 0)
		tl.forced_t = 0.2
	emit("attack_started", {"actor": c.id, "action": action, "technique": tid, "windup": tl.hit_at, "duration": tl.duration,
		"facing": tl.facing, "element": str(t.get("element", "none"))})
	return ok({"action": action, "duration": tl.duration, "facing": tl.facing, "technique": tid})

func technique_cost(c, t: Dictionary) -> float:
	var st: Dictionary = ContentDB.stat_const("technique_cost", {})
	var base := float(t.get("qi_cost", 0))
	var lv := ProgressionRules.level(c)
	var m: Dictionary = c.cultivator.mastery.get(str(t.id), {"tier": 1})
	var mastery_red := float(st.get("mastery_cost_per_tier", -0.05)) * (int(m.tier) - 1)
	var dao_tier := int(c.cultivator.daos.get(str(t.get("dao", "")), {}).get("tier", 0))
	var dao_red := -0.1 if dao_tier >= 2 else 0.0
	var comp := float(st.get("composure_zero_factor", 1.5)) if Unlocks.is_unlocked(c.id, "composure") and c.pools.composure <= 0.0 else 1.0
	return maxf(0.0, base * (1.0 + float(st.get("per_level", 0.04)) * lv) * (1.0 - c.stats.value("technique_cost")) * (1.0 + mastery_red + dao_red) * comp)

func guard(c, on: bool) -> Dictionary:
	if on and not Unlocks.is_unlocked(c.id, "guard"): return fail("locked")
	var tl := timeline(c.id)
	if on:
		if StatRules.family(c).get("guard", 0.0) <= 0.0: return fail("cannot_guard")
		tl.guard = true
		tl.guard_t = 0.0
		emit("system_used", {"actor": c.id, "system": "guard"})
	else:
		tl.guard = false
	emit("guard_changed", {"actor": c.id, "guard": tl.guard})
	return ok()

func dodge(c, direction, facing: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "dodge_dash"): return fail("locked")
	if wounded.has(c.id) or c.pools.blocked("move"): return fail("stunned")
	if c.pools.cooldown("dodge") > 0.0: return fail("cooldown")
	var dir: Vector2 = direction if direction is Vector2 and direction.length() > 0.2 else Vector2(1 if facing >= 0 else -1, 0)
	dir = dir.normalized()
	var conf: Dictionary = ContentDB.stat_const("combat", {})
	var tl := timeline(c.id)
	# Wind Blink (secret art, Spirit Awakening 5): a dodge in mid-air blinks 120 units along the wind
	# and holds the body up for a breath, so a gap too wide to jump can be crossed.
	var st: ActorState = game.actor_state(c.id)
	# Shallow water drags at the feet: no dodging in it (S43 volumes).
	if st != null and st.surface != null and game.room_rt and not game.room_rt.geometry.volume_at(st.plane, st.altitude, "water_shallow").is_empty():
		return fail("in_water")
	# Swallow Dart (Qi Kindling 7): an Evade tap in the air darts 140 and holds the height for 0.25 s,
	# once per airtime. It shares the dodge's cooldown.
	if st != null and st.surface == null and not st.flying and st.climbing.is_empty() and knows_art(c, "air_dash") and not st.air_dash_used \
			and c.pools.cooldown("dodge") <= 0.0:
		st.arts["air_dash"] = true
		if MovementSolver.air_dash(st):
			var ax := signf(dir.x) if absf(dir.x) > 0.2 else (1.0 if facing >= 0 else -1.0)
			var dash_s := float(ContentDB.movement("air_dash.hold_s", 0.25))
			tl.forced = Vector2(ax, 0) * float(ContentDB.movement("air_dash.distance", 140.0)) / dash_s
			tl.forced_t = dash_s
			var dcd := float(conf.get("dodge_cooldown_s", 2.5))
			if int(c.cultivator.meridians.get("agility", 0)) >= 25: dcd *= 0.8
			c.pools.cooldowns["dodge"] = dcd
			LocalAuthority.announce(st, c.id)
			return ok({"air_dash": true})
	if st != null and st.surface == null and not st.flying and "wind_blink" in c.cultivator.secret_arts and c.pools.cooldown("wind_blink") <= 0.0:
		var bx := signf(dir.x) if absf(dir.x) > 0.2 else (1.0 if facing >= 0 else -1.0)
		var blink := float(ContentDB.stat_const("combat.wind_blink_distance", 120))
		tl.forced = Vector2(bx, 0) * blink / 0.1
		tl.forced_t = 0.1
		tl.dodge_t = 0.15
		st.vertical_speed = maxf(st.vertical_speed, 140.0)
		c.pools.cooldowns["wind_blink"] = float(ContentDB.stat_const("combat.wind_blink_cooldown_s", 10))
		emit("dodged", {"actor": c.id, "direction": Vector2(bx, 0), "blink": true})
		return ok({"blink": true})
	var dist := float(conf.get("dodge_distance", 140))
	tl.forced = dir * dist / 0.22
	tl.forced_t = 0.22
	tl.dodge_t = float(conf.get("dodge_invuln_s", 0.25))
	var cd := float(conf.get("dodge_cooldown_s", 2.5))
	if int(c.cultivator.meridians.get("agility", 0)) >= 25: cd *= 0.8
	c.pools.cooldowns["dodge"] = cd
	if c.cultivator.meditating: game.progression.stop_meditation(c, "dodge")
	emit("dodged", {"actor": c.id, "direction": dir})
	return ok()

# ------------------------------------------------------------------ tick
func tick(delta: float) -> void:
	if hitstop > 0.0:
		hitstop -= delta
	var c = game.active()
	if c != null:
		_tick_player(c, delta)
		_tick_pools(c, delta)
		_tick_flight(c, delta)
		_tick_glide(c, delta)
		_tick_treasures(c, delta)
		var body: ActorState = game.actor_state(c.id)
		if body != null and not body.plunge_impact.is_empty(): _resolve_plunge(c, body)
	_tick_projectiles(delta)
	if game.room_rt:
		for e in game.room_rt.enemies.values():
			if e.alive: _tick_enemy_statuses(e, delta)

func _tick_player(c, delta: float) -> void:
	var tl := timeline(c.id)
	if float(tl.forced_t) > 0.0: tl.forced_t = maxf(0.0, float(tl.forced_t) - delta)
	if float(tl.dodge_t) > 0.0: tl.dodge_t = maxf(0.0, float(tl.dodge_t) - delta)
	if float(tl.flinch) > 0.0: tl.flinch = maxf(0.0, float(tl.flinch) - delta)
	if float(tl.stance) > 0.0: tl.stance = maxf(0.0, float(tl.stance) - delta)
	if tl.guard: tl.guard_t = float(tl.guard_t) + delta
	if wounded.has(c.id):
		wounded[c.id].timer = float(wounded[c.id].timer) + delta
		return
	if tl.action == "": return
	tl.t = float(tl.t) + delta
	if not tl.hit_done and float(tl.t) >= float(tl.hit_at):
		tl.hit_done = true
		if tl.technique != "": _resolve_technique(c, ContentDB.entry("techniques", tl.technique))
		else: _resolve_basic(c)
	if float(tl.t) >= float(tl.duration):
		var fam := ContentDB.entry("weapon_families", str(tl.family))
		if int(tl.queued) > 0 and tl.technique == "" and int(tl.combo) < fam.get("combo", []).size() - 1:
			tl.queued = int(tl.queued) - 1
			_start_step(c, fam, int(tl.combo) + 1, int(tl.facing))
		else:
			tl.window = float(ContentDB.stat_const("combat.combo_window_s", 0.5)) if tl.technique == "" and int(tl.combo) < fam.get("combo", []).size() - 1 else 0.0
			tl.action = ""
			tl.queued = 0
	if tl.action == "" and float(tl.window) > 0.0:
		tl.window = maxf(0.0, float(tl.window) - delta)
		if float(tl.window) <= 0.0: tl.combo = -1

func _tick_pools(c, delta: float) -> void:
	var p: ResourcePool = c.pools
	p.since_hit += delta
	p.since_composure_use += delta
	if p.invulnerable > 0.0: p.invulnerable = maxf(0.0, p.invulnerable - delta)
	for k in p.cooldowns.keys():
		p.cooldowns[k] = float(p.cooldowns[k]) - delta
		if float(p.cooldowns[k]) <= 0.0: p.cooldowns.erase(k)
	# Timed buffs.
	var expired: Array = c.stats.tick(delta)
	if not expired.is_empty():
		refresh_stats(c.id)
		for s in expired: emit("buff_expired", {"actor": c.id, "source": s})
	# Statuses (damage over time, expiry).
	for s in p.statuses.duplicate():
		if s.has("delay") and float(s.delay) > 0.0:
			s.delay = float(s.delay) - delta
			continue
		s.remaining = float(s.remaining) - delta
		var def := ContentDB.entry("status_effects", str(s.id))
		if def.get("dot", false):
			s.tick_s = float(s.get("tick_s", 0.0)) + delta
			if float(s.tick_s) >= 1.0:
				s.tick_s = float(s.tick_s) - 1.0
				var dmg := maxf(1.0, p.max_hp * float(s.get("power", 0.02)))
				_damage_player(c, dmg, "dot", str(s.id), {})
		if float(s.remaining) <= 0.0:
			p.statuses.erase(s)
			emit("status_expired", {"target": c.id, "effect": s.id})
	# Out-of-combat regeneration (S11) and Composure (S29).
	var regen_delay := float(ContentDB.stat_const("regen_per_s.combat_delay_s", 5))
	if not c.cultivator.meditating and p.since_hit >= regen_delay and not wounded.has(c.id) and not p.has_status("burn"):
		# Resting well away from a fight recovers faster (S11 regen, rest multiplier).
		var rest := float(ContentDB.stat_const("regen_per_s.rest_mult", 4.0)) if p.since_hit >= regen_delay * 2.0 else 1.0
		if p.hp < p.max_hp: apply_resource_change(c.id, "hp", p.max_hp * c.stats.value("hp_regen") * rest * delta, "regen", 0.0, true)
		if p.max_qi > 0 and p.qi < p.max_qi: apply_resource_change(c.id, "qi", p.max_qi * c.stats.value("qi_regen") * delta, "regen", 0.0, true)
		if p.max_soul > 0 and p.soul < p.max_soul: apply_resource_change(c.id, "soul", p.max_soul * c.stats.value("soul_regen") * delta, "regen", 0.0, true)
	if Unlocks.is_unlocked(c.id, "composure") and p.composure < 100.0 and p.since_composure_use >= float(ContentDB.stat_const("composure.recover_delay_s", 3)):
		apply_resource_change(c.id, "composure", float(ContentDB.stat_const("composure.recover_per_s", 10)) * delta, "regen", 0.0, true)
	if p.hollowing > 0.0 and not c.cultivator.meditating:
		apply_resource_change(c.id, "hollowing", -float(ContentDB.stat_const("hollowing.decay_per_min", 1)) / 60.0 * delta, "decay", 0.0, true)

func _tick_enemy_statuses(e: EnemyState, delta: float) -> void:
	for key in e.pools.steadfast.keys():
		e.pools.steadfast[key] = float(e.pools.steadfast[key]) - delta
		if float(e.pools.steadfast[key]) <= 0.0: e.pools.steadfast.erase(key)
	for s in e.pools.statuses.duplicate():
		s.remaining = float(s.remaining) - delta
		var def := ContentDB.entry("status_effects", str(s.id))
		if def.get("dot", false):
			s.tick_s = float(s.get("tick_s", 0.0)) + delta
			if float(s.tick_s) >= 1.0:
				s.tick_s = float(s.tick_s) - 1.0
				_damage_enemy(e, maxf(1.0, e.pools.max_hp * float(s.get("power", 0.02))), str(s.get("source", "")), "dot", str(s.id), false, {})
		if float(s.remaining) <= 0.0:
			e.pools.statuses.erase(s)
			if e.is_boss() and def.get("cc", false): e.pools.steadfast[str(s.id)] = float(ContentDB.stat_const("combat.steadfast_s", 8))
			emit("status_expired", {"target": str(e.uid), "effect": s.id})

# ------------------------------------------------------------------ resolution
func _resolve_basic(c) -> void:
	var tl := timeline(c.id)
	var fam := ContentDB.entry("weapon_families", str(tl.family))
	var step: Dictionary = tl.get("step", {})
	var pv := player_view(c)
	var facing := int(tl.facing)
	if fam.get("ranged", false):
		_spawn_projectile({"team": "player", "owner": c.id, "x": float(pv.x) + facing * 28, "y": float(pv.y), "alt": float(pv.alt) + 58,
			"dir": facing, "speed": float(fam.get("projectile_speed", 620)), "range": float(fam.get("reach", 480)), "pierce": 0,
			"art": "arrow", "attack": {"damage_type": "physical", "element": "none", "mult": [float(step.get("mult", 1.0)), float(step.get("mult", 1.0))],
			"range": fam.range, "source": "basic"}})
		return
	var hitbox := {"x": [-8, float(fam.get("reach", 46))], "depth": float(fam.get("depth", 30)), "alt": fam.get("altitude", [0, 90])}
	var mult := float(step.get("mult", 1.0))
	var max_targets := int(fam.get("line_targets", 1))
	var hit_any := false
	var targets := _enemies_in(pv, facing, hitbox, false)
	targets.sort_custom(func(a, b): return absf(a.plane.x - float(pv.x)) < absf(b.plane.x - float(pv.x)))
	var n := 0
	for e in targets:
		if n >= max_targets: break
		var attack := {"damage_type": "physical", "element": "none", "mult": [mult, mult], "range": fam.get("range", [0.9, 1.1]),
			"dao_tier": _dao_tier(c, str(fam.get("dao", ""))), "room_element": str(game.room_rt.def.get("element", "")) if game.room_rt else "",
			"knockback": float(step.get("knockback", fam.get("knockback_every_hit", 0))), "source": "basic"}
		if fam.has("backstab") and e.facing == facing: attack.situation = float(fam.backstab)
		_player_hits_enemy(c, pv, e, attack, facing)
		n += 1
		hit_any = true
	# Objects: training stumps, dummies, jars, crates and wine jars take basic hits.
	if game.room_rt:
		for o in game.world.hittable_objects(pv, facing, hitbox):
			game.world.apply_object_hit(c.id, o)
			hit_any = true
	if not hit_any: emit("attack_whiffed", {"actor": c.id})

func _resolve_technique(c, t: Dictionary) -> void:
	var tl := timeline(c.id)
	var pv := player_view(c)
	var facing := int(tl.facing)
	var fam := StatRules.family(c)
	var dtype := str(t.get("damage_type", "physical"))
	var m: Dictionary = c.cultivator.mastery.get(str(t.id), {"tier": 1})
	var tier := int(m.tier)
	var hits_total := 0
	if dtype == "buff":
		var b: Dictionary = t.get("buff", {})
		if b.has("stat"):
			apply_buff(c.id, {"stat": b.stat, "op": b.get("op", "pct_add"), "value": b.value, "duration": b.duration, "source": "tech:" + str(t.id)}, "technique")
		emit("technique_used", {"actor": c.id, "technique": t.id, "hits": 1, "targets": 0})
		return
	if dtype == "stance":
		tl.stance = float(t.get("stance_s", 2.0))
		tl.guard = true
		tl.guard_t = 0.0
		emit("system_used", {"actor": c.id, "system": "guard"})
		emit("technique_used", {"actor": c.id, "technique": t.id, "hits": 1, "targets": 0})
		return
	var attack := {"damage_type": "physical" if dtype == "movement" else dtype, "element": str(t.get("element", "none")),
		"mult": t.get("mult", [1, 1]), "range": fam.get("range", [0.9, 1.1]), "dao_tier": _dao_tier(c, str(t.get("dao", ""))),
		"mastery_tier": tier - 1, "room_element": str(game.room_rt.def.get("element", "")) if game.room_rt else "",
		"knockback": float(t.get("knockback", 0)), "ignore_armor": t.get("ignore_armor", false),
		"ignore_resistance": float(t.get("ignore_resistance", 0.0)), "penetration_bonus": float(t.get("penetration", 0.0)),
		"status": t.get("status", {}), "source": "tech:" + str(t.id), "technique": str(t.id)}
	if tier >= 3 and t.has("tier3"):
		var t3: Dictionary = t.tier3
		if t3.has("status"): attack.status = t3.status
		if t3.has("crit"): attack.crit_bonus = float(t3.crit)
	if t.has("projectile"):
		var pr: Dictionary = t.projectile
		var count := int(pr.get("count", 1)) + (1 if tier >= 3 and str(t.id) == "twin_reed_shot" else 0)
		for i in count:
			_spawn_projectile({"team": "player", "owner": c.id, "x": float(pv.x) + facing * 30, "y": float(pv.y) + (i - (count - 1) * 0.5) * 8.0,
				"alt": float(pv.alt) + 56 + i * 4, "dir": facing, "speed": float(pr.get("speed", 600)), "range": float(pr.get("range", 400)),
				"pierce": int(pr.get("pierce", 0)), "art": "qi_" + str(t.get("element", "none")) if dtype == "qi" else "arrow",
				"attack": attack, "delay": i * 0.08, "seek": pr.get("seek", false), "technique": str(t.id), "element": str(t.get("element", "none"))})
		emit("technique_used", {"actor": c.id, "technique": t.id, "hits": count, "targets": count})
		return
	var hitbox: Dictionary = t.get("hitbox", {"x": [0, 80], "depth": 30, "alt": [0, 110]})
	var targets := _enemies_in(pv, facing, hitbox, t.get("both_sides", false))
	targets.sort_custom(func(a, b): return absf(a.plane.x - float(pv.x)) < absf(b.plane.x - float(pv.x)))
	var max_targets := int(t.get("max_targets", 1))
	var n := 0
	var target_def := ""
	for e in targets:
		if n >= max_targets: break
		for h in maxi(1, int(t.get("hits", 1))):
			if not e.alive: break
			_player_hits_enemy(c, pv, e, attack, facing)
			hits_total += 1
		target_def = e.def_id
		n += 1
	emit("technique_used", {"actor": c.id, "technique": t.id, "hits": maxi(hits_total, 1), "targets": n, "target_def": target_def})

func _dao_tier(c, dao: String) -> int:
	return int(c.cultivator.daos.get(dao, {}).get("tier", 0))

func _enemies_in(pv: Dictionary, facing: int, hitbox: Dictionary, both_sides: bool) -> Array:
	var out: Array = []
	if game.room_rt == null: return out
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden: continue
		if hit_test(pv, facing, hitbox, enemy_view(e), both_sides): out.append(e)
	return out

func _player_hits_enemy(c, pv: Dictionary, e: EnemyState, attack: Dictionary, facing: int) -> void:
	if e.invulnerable or bool(e.def.get("invulnerable", false)):
		emit("hit_immune", {"attacker": c.id, "target": str(e.uid), "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover})
		return
	# Guard-and-counter (Trial Puppet): frontal hits are blocked while it stands guard;
	# a block triggers its counter, and it is open while recovering.
	if str(e.def.get("ai", {}).get("profile", "")) == "guard_counter" and str(e.ai.get("state", "")) in ["idle", "patrol", "aggro", "return"] and facing != e.facing:
		e.ai["counter"] = true
		emit("hit_blocked", {"attacker": c.id, "target": str(e.uid), "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.height()})
		return
	var rng := Rng.stream(c.id, "combat")
	var ev := enemy_view(e)
	if attack.has("crit_bonus"): pv = pv.duplicate(); pv.crit_bonus = attack.crit_bonus
	var dealt := float(attune.get(c.id, {}).get("dealt", 1.0))
	if dealt != 1.0:
		attack = attack.duplicate()
		attack.attunement = float(attack.get("attunement", 1.0)) * dealt
	var r := CombatRules.resolve(pv, ev, attack, rng)
	if r.miss:
		emit("hit_missed", {"attacker": c.id, "target": str(e.uid), "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover + e.height()})
		return
	e.threat[c.id] = float(e.threat.get(c.id, 0.0)) + float(r.amount)
	_damage_enemy(e, float(r.amount), c.id, r.type, r.element, r.crit, attack, facing)
	if e.alive and not attack.get("status", {}).is_empty():
		var s: Dictionary = attack.status
		if not e.pools.steadfast.has(str(s.id)):
			var applied := CombatRules.status_roll(s, ev, rng)
			if not applied.is_empty():
				applied.source = c.id
				_apply_status_to_enemy(e, applied)
	hitstop = float(ContentDB.stat_const("combat.hitstop_crit" if r.crit else "combat.hitstop", 0.05))

func _apply_status_to_enemy(e: EnemyState, s: Dictionary) -> void:
	for existing in e.pools.statuses:
		if existing.id == s.id:
			if float(s.power) >= float(existing.get("power", 0)): existing.merge(s, true)
			return
	e.pools.statuses.append(s)
	emit("status_applied", {"target": str(e.uid), "effect": s.id, "duration": s.remaining})

func _damage_enemy(e: EnemyState, amount: float, attacker: String, dtype: String, element: String, crit: bool, attack: Dictionary, facing := 0) -> void:
	if not e.alive: return
	if e.pools.has_status("freeze"):
		for s in e.pools.statuses.duplicate():
			if s.id == "freeze": e.pools.statuses.erase(s)
	e.pools.hp = maxf(0.0, e.pools.hp - amount)
	e.flash = 0.12
	if attacker.begins_with("c"): e.first_hit_by_player = true
	var kb := float(attack.get("knockback", 0.0))
	if kb > 0.0 and not e.def.get("knockback_immune", false) and not e.is_boss():
		e.knockback = kb * (facing if facing != 0 else 1)
	# Hit-stun (S30): a normal monster struck during its wind-up flinches, then shrugs
	# off further interrupts for a moment so it can never be stun-locked.
	if e.role == "normal" and not e.def.get("steadfast", false) and str(e.ai.get("state", "")) == "windup" \
			and float(e.ai.get("stun_guard", 0.0)) <= 0.0 and not attacker.begins_with("ally"):
		game.enemies.stagger(e, float(ContentDB.stat_const("combat.hit_stun_s", 0.35)))
		e.ai["stun_guard"] = float(ContentDB.stat_const("combat.hit_stun_guard_s", 1.6))
	emit("hit_landed", {"attacker": attacker, "target": str(e.uid), "target_kind": "enemy", "amount": int(amount), "type": dtype,
		"crit": crit, "element": element, "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover + e.height() * 0.8,
		"hp": e.pools.hp, "max": e.pools.max_hp, "source": str(attack.get("source", ""))})
	# Spars end at 10% HP; nobody dies (S42).
	if e.def.get("spar", false) and e.pools.hp <= e.pools.max_hp * 0.1:
		e.pools.hp = e.pools.max_hp * 0.1
		game.enemies.end_spar(e, attacker)
		return
	if e.pools.hp <= 0.0:
		var payload: Dictionary = game.enemies.defeat(e, attacker)
		if not payload.is_empty(): emit("actor_defeated", payload)

## Enemy strikes (called by EnemyAuthority at the hit moment of a melee attack).
func enemy_strike(e: EnemyState, attack: Dictionary) -> void:
	var c = game.active()
	if c == null or wounded.has(c.id): return
	var pv := player_view(c)
	var ev := enemy_view(e)
	var hitbox: Dictionary = attack.get("hitbox", {"x": [0, 40], "depth": 26, "alt": [0, 70]})
	if hit_test(ev, e.facing, hitbox, pv, attack.get("both_sides", false)):
		_enemy_hits_player(e, c, ev, pv, attack)
	_enemy_hits_allies(e, attack, ev)

## The same strike lands on companions and spirit animals inside its hitbox.
func _enemy_hits_allies(e: EnemyState, attack: Dictionary, ev: Dictionary) -> void:
	if game.room_rt == null: return
	var hitbox: Dictionary = attack.get("hitbox", {"x": [0, 40], "depth": 26, "alt": [0, 70]})
	for a in game.room_rt.enemies.values():
		if a.team != "ally" or not a.alive or a.ai.state == "downed" or a.hidden: continue
		var view := {"x": a.plane.x, "y": a.plane.y, "alt": 0.0, "half_width": a.half_width(), "height": a.height()}
		if not CombatAuthority.hit_test(ev, e.facing, hitbox, view, attack.get("both_sides", false)): continue
		var companion: bool = game.companions.is_companion_ally(a)
		var dmg := maxf(1.0, float(e.stats.attack) * float(attack.get("mult", 1.0)) * 0.8)
		if not companion: dmg *= maxf(0.1, 1.0 + game.pets.trait_bonus(game.active(), "pet_damage_taken"))
		a.pools.hp -= dmg
		a.flash = 0.12
		emit("hit_landed", {"attacker": str(e.uid), "target": str(a.uid), "target_kind": "ally", "amount": int(dmg), "type": "physical",
			"crit": false, "element": e.element, "x": a.plane.x, "y": a.plane.y, "alt": a.height()})
		if a.pools.hp <= 0.0:
			if companion: game.companions.apply_down(a)
			else: game.pets.apply_retreat(a)

func _enemy_hits_player(e: EnemyState, c, ev: Dictionary, pv: Dictionary, attack: Dictionary) -> void:
	var tl := timeline(c.id)
	if c.pools.invulnerable > 0.0 or float(tl.dodge_t) > 0.0 or c.pools.has_status("spawn_protection"):
		emit("hit_dodged", {"target": c.id, "attacker": str(e.uid)})
		return
	# Parry: a guard begun within the family's parry window before the hit negates it.
	var fam := StatRules.family(c)
	var frontal := signf(float(pv.x) - e.plane.x) != float(tl.facing) or absf(float(pv.x) - e.plane.x) < 4
	if tl.guard and frontal and float(tl.guard_t) <= float(fam.get("parry_s", 0.18)) and Unlocks.is_unlocked(c.id, "guard"):
		var stagger := float(ContentDB.stat_const("combat.parry_stagger_boss_s" if e.is_boss() else "combat.parry_stagger_s", 0.8))
		game.enemies.stagger(e, stagger)
		emit("parried", {"actor": c.id, "attacker": str(e.uid), "x": pv.x, "y": pv.y})
		if float(tl.stance) > 0.0:
			_player_hits_enemy(c, pv, e, {"damage_type": "physical", "element": "wood", "mult": [2.0, 2.0], "range": [1.0, 1.0], "source": "counter"}, int(tl.facing))
		return
	var m := float(attack.get("mult", 1.0)) * float(e.ai.get("enraged", {}).get("damage", 1.0))
	var a := {"damage_type": str(attack.get("damage_type", "physical")), "element": e.element, "mult": [m, m],
		"range": [0.9, 1.1], "knockback": float(attack.get("knockback", 0)), "attunement": float(attune.get(c.id, {}).get("taken", 1.0))}
	var guard_pv := pv.duplicate()
	if not (tl.guard and frontal): guard_pv.guarding = 0.0
	var r := CombatRules.resolve(ev, guard_pv, a, Rng.stream(c.id, "combat"))
	if r.miss:
		emit("hit_missed", {"attacker": str(e.uid), "target": c.id, "x": pv.x, "y": pv.y, "alt": float(pv.alt) + 90})
		return
	_damage_player(c, float(r.amount), str(e.uid), r.type, a, r.crit, e)
	if attack.has("status") and not attack.status.is_empty():
		var applied := CombatRules.status_roll(attack.status, pv, Rng.stream(c.id, "combat"))
		if not applied.is_empty(): apply_status(c.id, str(applied.id), float(applied.remaining), float(applied.power))
	if float(e.def.get("hollowing", 0)) > 0: apply_resource_change(c.id, "hollowing", float(e.def.hollowing), "hollow")
	if float(attack.get("drain", 0)) > 0: e.pools.hp = minf(e.pools.max_hp, e.pools.hp + r.amount * float(attack.drain))

## S17 · Damage from the room, not a foe. A dodge, invulnerability or arrival protection avoids it
## (returns -1).
func apply_hazard_damage(c, amount: float, dtype: String, element: String, source: String) -> float:
	var tl := timeline(c.id)
	if wounded.has(c.id) or c.pools.invulnerable > 0.0 or float(tl.dodge_t) > 0.0 or c.pools.has_status("spawn_protection"):
		emit("hit_dodged", {"target": c.id, "attacker": source})
		return -1.0
	_damage_player(c, amount, source, dtype, {"element": element})
	return amount

func _damage_player(c, amount: float, attacker: String, dtype: String, attack: Dictionary, crit := false, e: EnemyState = null) -> void:
	var p: ResourcePool = c.pools
	if wounded.has(c.id): return
	if p.shield > 0.0:
		var absorbed := minf(p.shield, amount)
		p.shield -= absorbed
		amount -= absorbed
	var pool := "soul" if dtype == "soul" and p.max_soul > 0 else "hp"
	var before := p.get_value(pool)
	p.set_value(pool, before - amount)
	p.since_hit = 0.0
	var tl := timeline(c.id)
	var kb := float(attack.get("knockback", 0))
	if amount >= p.max_hp * float(ContentDB.stat_const("combat.flinch_pct", 0.2)) or kb >= 60:
		tl.flinch = float(ContentDB.stat_const("combat.flinch_s", 0.4))
		if kb > 0 and e != null and not (int(c.cultivator.meridians.get("body", 0)) >= 50 and is_busy(c.id)):
			tl.forced = Vector2(signf(game.actor_state(c.id).plane.x - e.plane.x) * kb / 0.18, 0) if game.actor_state(c.id) else Vector2.ZERO
			tl.forced_t = 0.18
	var st: ActorState = game.actor_state(c.id)
	if spar.has(c.id) and p.hp <= p.max_hp * 0.1:
		p.hp = p.max_hp * 0.1
		game.enemies.player_lost_spar()
		return
	emit("hit_landed", {"attacker": attacker, "target": c.id, "target_kind": "player", "amount": int(round(amount)), "type": dtype,
		"crit": crit, "element": str(attack.get("element", "none")), "x": st.plane.x if st else 0.0, "y": st.plane.y if st else 0.0,
		"alt": (st.altitude if st else 0.0) + 92.0, "hp": p.hp, "max": p.max_hp, "pool": pool})
	emit("resource_changed", {"actor": c.id, "pool": pool, "value": p.get_value(pool), "max": p.get_max(pool)})
	# Lotus Heart Breathing (secret art, Spirit Awakening 5): below 30% HP the breath turns inward and
	# heals 2% a second for 5 s, once a minute.
	if pool == "hp" and p.hp > 0.0 and p.hp < p.max_hp * 0.3 and "lotus_heart_breathing" in c.cultivator.secret_arts and p.cooldown("lotus_heart") <= 0.0:
		p.cooldowns["lotus_heart"] = 60.0
		apply_heal(c.id, 0.10, 0.0, 5.0, "lotus_heart_breathing")
		emit("system_used", {"actor": c.id, "system": "lotus_heart_breathing"})
	if p.get_value(pool) <= 0.0:
		if int(c.cultivator.meridians.get("body", 0)) >= 100 and not tl.get("survived_lethal", false):
			tl.survived_lethal = true
			p.set_value(pool, 1.0)
			return
		if spar.has(c.id):
			p.set_value(pool, 1.0)
			return
		_gravely_wound(c, "soul" if pool == "soul" else "hp")

func _gravely_wound(c, cause: String) -> void:
	# The Prologue (before the Willow Path unlocks progress from fights) carries no penalty (S27).
	var no_penalty: bool = not Unlocks.is_unlocked(c.id, "kill_progress") or bool(game.room_rt.def.get("no_death_penalty", false) if game.room_rt else false)
	wounded[c.id] = {"cause": cause, "timer": 0.0, "no_penalty": no_penalty}
	var tl := timeline(c.id)
	tl.action = ""
	tl.guard = false
	if c.cultivator.meditating: game.progression.stop_meditation(c, "wounded")
	emit("player_gravely_wounded", {"actor": c.id, "cause": cause, "no_penalty": no_penalty,
		"talisman": c.inventory.count("revival_talisman"), "can_revive_here": revive_here_allowed(c)})

func revive_here_allowed(c) -> Dictionary:
	if c.inventory.count("revival_talisman") <= 0: return {"ok": false, "text": Tx.t("sim.combat.no_revival_talisman")}
	if game.room_rt and game.room_rt.def.get("no_revive_here", false): return {"ok": false, "text": Tx.t("sim.combat.not_allowed_here")}
	var until := float(c.cooldowns.get("revival_talisman_utc", 0.0))
	if Clock.now_utc() < until: return {"ok": false, "text": Tx.t("sim.combat.talisman_recovering_ds") % int(until - Clock.now_utc())}
	return {"ok": true, "text": ""}

## An Evergreen Heart fruit (natural treasure) lifts you where you fell, whole.
func fruit_revival_allowed(c) -> Dictionary:
	if c.inventory.count("evergreen_heart_fruit") <= 0: return {"ok": false, "text": ""}
	if game.room_rt and game.room_rt.def.get("no_revive_here", false): return {"ok": false, "text": Tx.t("sim.combat.not_allowed_here")}
	return {"ok": true, "text": ""}

func choose_revival(c, where: String) -> Dictionary:
	if not wounded.has(c.id): return fail("not_wounded")
	var info: Dictionary = wounded[c.id]
	var death: Dictionary = ContentDB.stat_const("death", {})
	if where == "fruit":
		var fruit := fruit_revival_allowed(c)
		if not fruit.ok: return fail("not_allowed", {"text": fruit.text})
		game.inventory.apply_remove(c.id, "evergreen_heart_fruit", 1, "revive")
		wounded.erase(c.id)
		c.pools.hp = c.pools.max_hp
		if c.pools.max_soul > 0: c.pools.soul = c.pools.max_soul
		c.pools.statuses.clear()
		c.pools.invulnerable = float(ContentDB.stat_const("treasures", {}).get("fruit_invuln_s", 3))
		emit("player_revived", {"actor": c.id, "where": "fruit"})
		emit("natural_treasure_used", {"actor": c.id, "treasure": "evergreen_heart_fruit"})
	elif where == "here":
		var allowed := revive_here_allowed(c)
		if not allowed.ok: return fail("not_allowed", {"text": allowed.text})
		game.inventory.apply_remove(c.id, "revival_talisman", 1, "revive")
		c.cooldowns["revival_talisman_utc"] = Clock.now_utc() + float(death.get("talisman_cooldown_s", 300))
		wounded.erase(c.id)
		c.pools.hp = c.pools.max_hp * float(death.get("talisman_hp", 0.3))
		c.pools.invulnerable = float(death.get("talisman_invuln_s", 5))
		emit("player_revived", {"actor": c.id, "where": "here"})
	else:
		wounded.erase(c.id)
		c.pools.hp = c.pools.max_hp * (1.0 if info.no_penalty else float(death.get("wake_hp", 0.5)))
		if c.pools.max_soul > 0: c.pools.soul = maxf(c.pools.soul, c.pools.max_soul * 0.3)
		c.pools.statuses.clear()
		c.pools.invulnerable = float(ContentDB.stat_const("combat.spawn_protection_s", 1.5))
		emit("player_revived", {"actor": c.id, "where": "shrine"})
		game.world.apply_return_to_shrine(c.id)
	for pool in ["hp", "soul"]:
		emit("resource_changed", {"actor": c.id, "pool": pool, "value": c.pools.get_value(pool), "max": c.pools.get_max(pool)})
	return ok()

# ------------------------------------------------------------------ projectiles
func _spawn_projectile(p: Dictionary) -> void:
	if game.room_rt == null: return
	p.uid = game.room_rt.uid()
	p.travelled = 0.0
	p.hits = []
	p.delay = float(p.get("delay", 0.0))
	game.room_rt.projectiles.append(p)
	emit("projectile_spawned", {"uid": p.uid, "team": p.team, "art": str(p.get("art", "arrow")), "element": str(p.get("element", "none"))})

func spawn_enemy_projectile(e: EnemyState, attack: Dictionary) -> void:
	var pr: Dictionary = attack.get("projectile", {})
	_spawn_projectile({"team": "enemy", "owner": str(e.uid), "x": e.plane.x + e.facing * e.half_width(), "y": e.plane.y,
		"alt": e.altitude + e.hover + e.height() * 0.55, "dir": e.facing, "speed": float(pr.get("speed", 400)),
		"range": float(attack.hitbox.x[1]), "pierce": 0, "art": str(pr.get("art", "pebble")), "enemy_attack": attack,
		"element": e.element})

func _tick_projectiles(delta: float) -> void:
	if game.room_rt == null: return
	var rt = game.room_rt
	var c = game.active()
	for p in rt.projectiles.duplicate():
		if float(p.delay) > 0.0:
			p.delay = float(p.delay) - delta
			continue
		var step := float(p.speed) * delta
		var remaining := minf(step, float(p.range) - float(p.travelled))
		var done := false
		while remaining > 0.001 and not done:
			var s := minf(remaining, 6.0)
			if p.get("seek", false) and p.team == "player":
				var tgt := _nearest_enemy(Vector2(p.x, p.y), 220.0)
				if tgt: p.y = move_toward(float(p.y), tgt.plane.y, 60.0 * delta)
			p.x = float(p.x) + float(p.dir) * s
			p.travelled = float(p.travelled) + s
			remaining -= s
			if rt.geometry.blocks_at(Vector2(p.x, p.y), float(p.alt), "ground") and p.team == "enemy" and float(p.alt) < 60:
				done = true
				break
			if p.team == "player":
				for e in rt.living_enemies():
					if e.team != "enemy" or e.hidden or p.hits.has(e.uid): continue
					# Shots fly at chest height; the band reaches down to the ground so a crab or a rat
					# under the line is struck too. Fired from the air, a shot still passes over them.
					var pv := {"x": p.x, "y": p.y, "alt": float(p.alt) - 20.0}
					if hit_test(pv, int(p.dir), {"x": [-12, 12], "depth": 26, "alt": [-56, 40]}, enemy_view(e)):
						p.hits.append(e.uid)
						if c != null:
							var view := player_view(c)
							_player_hits_enemy(c, view, e, p.attack, int(p.dir))
							if float(p.get("burst", 0.0)) > 0.0: _burst(c, p, e)
						if p.hits.size() > int(p.get("pierce", 0)):
							done = true
							break
			elif c != null and not wounded.has(c.id):
				var cv := player_view(c)
				var fxs: Dictionary = treasure_fx.get(c.id, {})
				# The Sealing Gourd drinks every missile that comes within its reach (S47).
				if float(fxs.get("gourd", 0.0)) > 0.0 and Vector2(float(p.x), float(p.y)).distance_to(Vector2(float(cv.x), float(cv.y))) < float(fxs.get("gourd_r", 240.0)):
					emit("projectile_absorbed", {"actor": c.id, "x": p.x, "y": p.y, "alt": p.alt})
					done = true
					break
				if hit_test({"x": p.x, "y": p.y, "alt": float(p.alt) - 20.0}, int(p.dir), {"x": [-10, 10], "depth": 24, "alt": [0, 40]}, cv) \
						and float(fxs.get("reflect", 0.0)) > 0.0:
					# The Bright Mirror sends it back at whoever threw it (S47).
					p.team = "player"
					p.dir = -int(p.dir)
					p.owner = c.id
					p.travelled = 0.0
					p.hits = []
					p.attack = {"damage_type": "qi", "element": str(p.get("element", "none")), "mult": [1.4, 1.4], "range": [1.0, 1.0], "source": "bright_mirror"}
					emit("projectile_reflected", {"actor": c.id, "x": p.x, "y": p.y, "alt": p.alt})
					break
				if hit_test({"x": p.x, "y": p.y, "alt": float(p.alt) - 20.0}, int(p.dir), {"x": [-10, 10], "depth": 24, "alt": [0, 40]}, cv):
					var e2: EnemyState = rt.enemies.get(int(str(p.owner)))
					if e2 != null:
						_enemy_hits_player(e2, c, enemy_view(e2), cv, p.enemy_attack)
					done = true
		if done or float(p.travelled) >= float(p.range):
			rt.projectiles.erase(p)
			emit("projectile_ended", {"uid": p.uid, "x": p.x, "y": p.y, "alt": p.alt})

# ------------------------------------------------------------------ treasures, throwables, talismans (gap report G2)
func _enemies_within(at: Vector2, radius: float) -> Array:
	var out: Array = []
	if game.room_rt == null: return out
	for e in game.room_rt.living_enemies():
		if e.team == "enemy" and not e.hidden and e.plane.distance_to(at) <= radius: out.append(e)
	return out

func _treasure_attack(t: Dictionary, source: String, dtype := "physical", element := "none") -> Dictionary:
	var m := float(t.get("mult", 1.0))
	return {"damage_type": dtype, "element": element, "mult": [m, m], "range": [1.0, 1.0], "knockback": float(t.get("knockback", 0.0)), "source": source}

## What a treasure does (treasures.json, S47), from its bag item id; {} if the item is not a treasure.
static func treasure_of(item_id: String) -> Dictionary:
	var tid := str(ContentDB.item(item_id).get("treasure", ""))
	return ContentDB.entry("treasures", tid) if tid != "" else {}

## Its Soul cost: a treasure also draws on the Soul from Spirit Awakening 1 (S47).
static func treasure_soul_cost(c, t: Dictionary) -> float:
	if c.pools.max_soul <= 0.0 or not ProgressionRules.at_least(c.cultivator.realm_key, "spirit_awakening_1"): return 0.0
	return float(t.get("soul", 0))

## One of the HUD's Treasure buttons. Each treasure is one action with a cooldown and a flat QI cost (S47);
## a talisman treasure spends one of its charges instead.
func use_treasure(c, slot: int) -> Dictionary:
	if slot < 0 or slot > 1: return fail("bad_slot")
	var id := str(c.inventory.treasures[slot])
	if id == "": return fail("empty")
	if not Unlocks.is_unlocked(c.id, "treasures" if slot == 0 else "treasure_slot_2"): return fail("locked")
	if c.inventory.count(id) <= 0:
		c.inventory.treasures[slot] = ""
		return fail("missing")
	var why := can_act(c)
	if why != "": return fail(why)
	var t := treasure_of(id)
	if t.is_empty(): return fail("unknown_treasure")
	var cd_key := "treasure:" + id
	if c.pools.cooldown(cd_key) > 0.0: return fail("cooldown", {"remaining": c.pools.cooldown(cd_key)})
	var cost := float(t.get("qi", 0))
	if cost > 0.0 and (c.pools.max_qi <= 0.0 or c.pools.qi < cost): return fail("no_qi", {"text": Tx.t("sim.combat.treasure_no_qi")})
	var soul := treasure_soul_cost(c, t)
	if soul > 0.0 and c.pools.soul < soul: return fail("no_soul", {"text": Tx.t("sim.combat.treasure_no_soul")})
	var pv := player_view(c)
	var here := Vector2(float(pv.x), float(pv.y))
	var tl := timeline(c.id)
	var out := {"action": str(t.action), "treasure": id, "targets": 0, "x": pv.x, "y": pv.y}
	var fxs: Dictionary = treasure_fx.get(c.id, {})
	match str(t.action):
		"bell":
			for e in _enemies_within(here, float(t.get("radius", 150))):
				if not e.is_boss(): _apply_status_to_enemy(e, {"id": "stun", "power": 1.0, "remaining": float(t.get("stun_s", 1.0)), "source": c.id})
				if float(t.get("seal_s", 0)) > 0.0:
					_apply_status_to_enemy(e, {"id": "qi_seal", "power": 1.0, "remaining": float(t.seal_s), "source": c.id})
				out.targets = int(out.targets) + 1
		"pagoda":
			# One foe, an elite first if one is in reach; bosses are too great for it.
			var tgt: EnemyState = null
			for e in _enemies_within(here, float(t.get("range", 320))):
				if e.is_boss(): continue
				if tgt == null or (e.elite and not tgt.elite) or (e.elite == tgt.elite and e.plane.distance_to(here) < tgt.plane.distance_to(here)): tgt = e
			if tgt == null:
				var near_boss := _nearest_enemy(here, float(t.get("range", 320)))
				if near_boss != null and near_boss.is_boss(): return fail("immune", {"text": Tx.t("sim.combat.pagoda_boss")})
				return fail("no_target", {"text": Tx.t("sim.combat.treasure_no_target")})
			_apply_status_to_enemy(tgt, {"id": "stun", "power": 1.0, "remaining": float(t.get("imprison_s", 4.0)), "source": c.id})
			out.targets = 1
			out.x = tgt.plane.x
			out.y = tgt.plane.y
		"mirror":
			fxs.reflect = float(t.get("reflect_s", 2.0))
		"seal":
			var atk := _treasure_attack(t, "treasure:" + id, str(t.get("damage_type", "qi")), "earth")
			for e in _enemies_within(here, float(t.get("radius", 120))):
				_player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
				out.targets = int(out.targets) + 1
		"cauldron":
			var best: EnemyState = null
			for e in _enemies_within(here, float(t.get("range", 260))):
				if e.is_boss() or str(e.def.get("race", "beast")) != "beast": continue
				if e.pools.hp > e.pools.max_hp * float(t.get("below", 0.2)): continue
				if best == null or e.plane.distance_to(here) < best.plane.distance_to(here): best = e
			if best == null: return fail("no_target", {"text": Tx.t("sim.combat.cauldron_no_target")})
			captured[str(best.uid)] = true
			out.x = best.plane.x
			out.y = best.plane.y
			_damage_enemy(best, best.pools.hp + 1.0, c.id, "physical", "none", false, {"source": "treasure:" + id})
			out.targets = 1
		"banner":
			fxs.wisps = {"left": float(t.get("duration", 10)), "tick": 1.0, "n": int(t.get("wisps", 3)), "mult": float(t.get("mult", 0.6)),
				"range": float(t.get("range", 280))}
		"gourd":
			fxs.gourd = float(t.get("absorb_s", 3.0))
			fxs.gourd_r = float(t.get("radius", 240.0))
		"palm":
			# Elder Hu's Heaven-Splitting Palm: 600% Qi Attack along a line before you, one charge a use.
			var facing := int(tl.facing)
			var atk := {"damage_type": "qi", "element": "metal", "mult": [float(t.get("mult", 6.0)), float(t.get("mult", 6.0))], "range": [1.0, 1.0],
				"knockback": 160.0, "source": "treasure:" + id}
			for e in _enemies_in(pv, facing, {"x": [0, float(t.get("reach", 540))], "depth": float(t.get("depth", 70)), "alt": [-40, 160]}, false):
				_player_hits_enemy(c, pv, e, atk, facing)
				out.targets = int(out.targets) + 1
			out.facing = facing
			out.reach = float(t.get("reach", 540))
		_:
			return fail("unknown_treasure")
	treasure_fx[c.id] = fxs
	if cost > 0.0: apply_resource_change(c.id, "qi", -cost, "treasure")
	if soul > 0.0: apply_resource_change(c.id, "soul", -soul, "treasure")
	if float(t.get("cooldown_s", 0)) > 0.0: c.pools.cooldowns[cd_key] = float(t.cooldown_s)
	if t.has("charges"):
		var idx: int = c.inventory.first_index(id)
		if idx >= 0:
			var stack: Dictionary = c.inventory.bag[idx]
			var left := int(stack.get("charges", int(t.charges))) - 1
			out.charges = maxi(0, left)
			if left <= 0:
				game.inventory.apply_remove_index(c.id, idx, 1, "charges_spent")
				c.inventory.treasures[slot] = ""
			else:
				stack.charges = left
			emit("bag_changed", {"actor": c.id})
	tl.flinch = 0.0
	out.actor = c.id
	emit("treasure_used", out)
	emit("system_used", {"actor": c.id, "system": "treasure"})
	return ok(out)

func _tick_treasures(c, delta: float) -> void:
	var fxs: Dictionary = treasure_fx.get(c.id, {})
	if fxs.is_empty(): return
	for k in ["reflect", "gourd"]:
		if float(fxs.get(k, 0.0)) > 0.0: fxs[k] = maxf(0.0, float(fxs[k]) - delta)
	var w: Dictionary = fxs.get("wisps", {})
	if not w.is_empty():
		w.left = float(w.left) - delta
		w.tick = float(w.tick) - delta
		if float(w.tick) <= 0.0 and game.room_rt:
			w.tick = float(w.tick) + 1.0
			var pv := player_view(c)
			var here := Vector2(float(pv.x), float(pv.y))
			var targets := _enemies_within(here, float(w.range))
			targets.sort_custom(func(a, b): return a.plane.distance_to(here) < b.plane.distance_to(here))
			var atk := {"damage_type": "qi", "element": "none", "mult": [float(w.mult), float(w.mult)], "range": [1.0, 1.0], "source": "treasure:wisp_banner"}
			for i in mini(int(w.n), targets.size()):
				var e: EnemyState = targets[i]
				_player_hits_enemy(c, pv, e, atk, 1 if e.plane.x >= here.x else -1)
				emit("wisp_struck", {"actor": c.id, "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.height() * 0.6})
		if float(w.left) <= 0.0: fxs.erase("wisps")

## A throwable from the quick-use slot (G2): needles, knives, a thunderclap pellet. Any weapon family can throw.
func apply_throw(actor_id: String, e: Dictionary) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var pv := player_view(c)
	var facing := int(timeline(c.id).facing)
	var n := int(e.get("count", 1))
	for i in n:
		_spawn_projectile({"team": "player", "owner": c.id, "x": float(pv.x) + facing * 24, "y": float(pv.y) + (i - (n - 1) * 0.5) * 6.0,
			"alt": float(pv.alt) + 56 + i * 3, "dir": facing, "speed": float(e.get("speed", 600)), "range": float(e.get("range", 380)),
			"pierce": int(e.get("pierce", 0)), "art": str(e.get("art", "needle")), "delay": i * 0.05, "element": "none",
			"attack": _treasure_attack(e, "throw:" + str(e.get("art", "needle"))), "burst": float(e.get("burst", 0.0))})
	emit("system_used", {"actor": c.id, "system": "throw"})

## A thunderclap pellet bursts where it lands: everything close by takes the blow and is thrown back.
func _burst(c, p: Dictionary, first: EnemyState) -> void:
	var at := Vector2(float(p.x), float(p.y))
	var pv := player_view(c)
	for e in _enemies_within(at, float(p.burst)):
		if e == first: continue
		_player_hits_enemy(c, pv, e, p.attack, 1 if e.plane.x >= at.x else -1)
	emit("projectile_burst", {"actor": c.id, "x": p.x, "y": p.y, "alt": p.alt, "radius": p.burst})

func _nearest_enemy(at: Vector2, radius: float) -> EnemyState:
	var best: EnemyState = null
	var d := radius
	for e in game.room_rt.living_enemies():
		if e.team != "enemy": continue
		var dist = e.plane.distance_to(at)
		if dist < d:
			d = dist
			best = e
	return best

# ------------------------------------------------------------------ apply_* commands
## The public command other authorities use to change a pool (Part 2).
func apply_resource_change(actor_id: String, pool: String, amount: float, source: String, pct := 0.0, quiet := false) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var p: ResourcePool = c.pools
	if pct != 0.0: amount += p.get_max(pool) * pct
	if pool == "hollowing" and amount > 0:
		amount *= 1.0 - clampf(c.stats.value("hollow_ward"), 0.0, 0.8)
		var cap := float(ContentDB.stat_const("hollowing.valley_cap", 49))
		p.set_value(pool, minf(cap, p.get_value(pool) + amount))
	else:
		p.set_value(pool, p.get_value(pool) + amount)
	if not quiet: emit("resource_changed", {"actor": c.id, "pool": pool, "value": p.get_value(pool), "max": p.get_max(pool), "source": source})

func apply_heal(actor_id: String, pct: float, amount: float, over_s: float, source: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var total = amount + c.pools.max_hp * pct
	if over_s > 0.0:
		apply_buff(actor_id, {"stat": "hp_regen", "op": "flat", "value": total / c.pools.max_hp / over_s, "duration": over_s, "source": "heal:" + source}, source)
		apply_resource_change(actor_id, "hp", total * 0.2, source)
	else:
		apply_resource_change(actor_id, "hp", total, source)

func apply_buff(actor_id: String, e: Dictionary, source: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.stats.add_modifier({"stat": str(e.stat), "op": str(e.get("op", "flat")), "value": float(e.value), "duration": float(e.get("duration", 60)),
		"source": str(e.get("source", source))})
	refresh_stats(actor_id)
	emit("buff_applied", {"actor": actor_id, "source": str(e.get("source", source)), "stat": str(e.stat), "duration": float(e.get("duration", 60))})

func apply_status(actor_id: String, status_id: String, duration: float, power: float, delay := 0.0) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("status_effects", status_id): return
	for s in c.pools.statuses:
		if s.id == status_id:
			if power >= float(s.get("power", 0)):
				s.power = power
				s.remaining = maxf(float(s.remaining), duration)
			return
	c.pools.statuses.append({"id": status_id, "remaining": duration, "power": power, "delay": delay})
	emit("status_applied", {"target": actor_id, "effect": status_id, "duration": duration})

func cure_status(actor_id: String, status_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	for s in c.pools.statuses.duplicate():
		if s.id == status_id:
			c.pools.statuses.erase(s)
			emit("status_expired", {"target": actor_id, "effect": status_id})

func apply_backlash(actor_id: String) -> void:
	var conf: Dictionary = ContentDB.stat_const("combat", {})
	apply_status(actor_id, "qi_backlash", float(conf.get("backlash_stun_s", 1.0)), 1.0)
	var c = game.character(actor_id)
	if c and c.pools.max_qi > 0: apply_resource_change(actor_id, "qi", -c.pools.max_qi * float(conf.get("backlash_qi_pct", 0.05)), "backlash")

## A pet or companion strike (AllyBrain) credits its owner.
func ally_hits_enemy(a: EnemyState, e: EnemyState, attack_power: float) -> void:
	var owner := a.pet_owner
	var c = game.character(owner)
	if c == null or not e.alive or e.invulnerable: return
	var view := {"level": a.level, "realm_index": ProgressionRules.realm_index(c.cultivator.realm_key), "element": "none",
		"physical_attack": attack_power, "accuracy": c.stats.value("accuracy"), "crit_chance": 0.05, "crit_damage": 1.5, "energy_mult": 1.0}
	var r := CombatRules.resolve(view, enemy_view(e), {"damage_type": "physical", "mult": [1.0, 1.0], "range": [0.85, 1.15]}, Rng.stream(owner, "pet"))
	if r.miss:
		emit("hit_missed", {"attacker": str(a.uid), "target": str(e.uid), "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover + e.height()})
		return
	e.threat[owner] = float(e.threat.get(owner, 0.0)) + float(r.amount)
	_damage_enemy(e, float(r.amount), owner, "physical", "none", r.crit, {"source": "ally:" + str(a.uid)}, a.facing)

func begin_spar(actor_id: String) -> void:
	spar[actor_id] = true

func end_spar(actor_id: String) -> void:
	spar.erase(actor_id)
