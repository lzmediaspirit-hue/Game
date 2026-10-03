class_name CombatAuthority
extends Authority
## S11/S12/S30/S31 · Owns the ResourcePools (HP, QI, Soul, Composure, Hollowing),
## StatBlock recalculation, active attacks and projectiles, status effects,
## cooldowns and combat timers. One damage pipeline (CombatRules) for everyone.
## The attack, tick and resolution flow is here. The systems around it are its parts in combat/, which work on the state
## kept here; what code outside calls on a part is forwarded at the end (docs/architecture/authority_parts.md).

var actors: Dictionary = {}          # actor id -> combat timeline for players/companions
var wounded: Dictionary = {}         # actor -> {cause, timer, no_penalty}
var spar: Dictionary = {}            # active spar {opponent uid, actor}
var hitstop := 0.0

const STAT_EVENTS := ["realm_changed", "level_changed", "equipment_changed", "injury_added", "injury_healed", "title_changed",
	"attributes_changed", "method_changed", "dao_tier_up", "body_level_changed", "purity_changed", "soul_changed",
	"legacy_recorded", "consolidation_finished", "aptitude_revealed", "collection_page_completed", "body_tier_reached", "physique_awakened",
	"inner_art_equipped", "stance_changed", "loadout_swapped", "fate_chosen", "sect_node_bought", "collection_seal_claimed"]

func intents() -> Array:
	return ["basic_attack", "use_technique", "guard_start", "guard_end", "dodge", "choose_revival", "start_flight", "stop_flight", "use_treasure",
		"plunge", "glide", "toggle_sword_release", "self_detonate", "channel_melody", "move_cancel"]

var attune: Dictionary = {}          # actor -> {dealt, taken} for the zone they stand in (S18)
var flying: Dictionary = {}          # actor -> true while flight holds them up (S18); QI pays for it
var gliding: Dictionary = {}         # actor -> true while Falling Leaf Glide holds them (S43); 2 QI a second
var treasure_fx: Dictionary = {}     # actor -> {reflect, gourd, gourd_r, wisps}: a treasure's lingering effect (G2)
var hots: Dictionary = {}            # actor -> [{per_s, left, total, source}]: heals over time, in a fight or out of one (S15)
var captured: Dictionary = {}        # enemy uid -> true: taken by the Beast-Taking Cauldron (World doubles its materials)
var sword_released: Dictionary = {}  # actor -> {t, next}: the jian flies on its own (S47 Sword Release; not saved)
var sword_intent: Dictionary = {}    # actor -> {stacks, t}: Sword Intent from consecutive jian hits (S47; not saved)
var killing_intent: Dictionary = {}  # actor -> {stacks, t}: kills in quick succession (S48; not saved)
var melody: Dictionary = {}          # actor -> {next}: the flute's held melody aura (S47 v1.1; not saved)
var ally_hots: Dictionary = {}       # ally uid -> [{per_s, left}]: heals over time on companions and pets (S47 v1.1)
var decoys: Dictionary = {}          # actor -> {x, y, alt, t, hits, max_hits, radius}: Phantom Double's illusion (S48 Soul line; not saved)
var searched: Dictionary = {}        # enemy uid (text) -> {actor, t}: a Soul Search mark; its death gives up memories and a hidden drop (S48)
var poison_touch: Dictionary = {}    # enemy uid -> sim time the Poison Body last touched it (S48 Poison path)
var arrays: Array = []               # quick-deployed Array Plates in this room: {actor, kind, x, y, radius, t, tick, ...} (S48)
var sword_swarm: Dictionary = {}     # actor -> {t, n, next, i}: the sword swarm orbiting you (S47 v1.1; not saved)
var spirit_hits: Dictionary = {}     # actor -> blows since the Artifact Spirit's skill last struck (S47; not saved)
var awaken_hits: Dictionary = {}     # actor -> blows since an awakened weapon's skill last struck (S47; not saved)
var blood_essence: Dictionary = {}   # actor -> {v, t}: the Blood path's meter, fed by kills (S48; transient, not saved)

# The parts (combat/*.gd), one system around the fight each.
var flight: CombatFlight             # flight and the movement arts
var phantom: CombatPhantom           # Phantom Double
var sword: CombatSword               # the flying sword, Sword Intent and Killing Intent
var swarm: CombatSwarm               # the sword swarm
var flute: CombatFlute               # the flute's melody
var heals: CombatHeals               # heals over time, the healing song, the sect roles' support
var blood_path: CombatBloodPath       # the Blood path
var plates: CombatPlates             # Array Plates
var talismans: CombatTalismans       # talismans from the bag
var projectiles: CombatProjectiles   # shots in flight
var treasures: CombatTreasures       # treasures, throwables, self-detonation
var revival: CombatRevival           # grave wounds and revival
var riders: CombatRiders             # what a landed blow carries after its damage

func _init(g) -> void:
	super(g)
	flight = CombatFlight.new(self)
	phantom = CombatPhantom.new(self)
	sword = CombatSword.new(self)
	swarm = CombatSwarm.new(self)
	flute = CombatFlute.new(self)
	heals = CombatHeals.new(self)
	blood_path = CombatBloodPath.new(self)
	plates = CombatPlates.new(self)
	talismans = CombatTalismans.new(self)
	projectiles = CombatProjectiles.new(self)
	treasures = CombatTreasures.new(self)
	revival = CombatRevival.new(self)
	riders = CombatRiders.new(self)

func subscribe() -> void:
	for ev in STAT_EVENTS:
		GameEvents.subscribe(ev, _on_stat_source, 20)
	GameEvents.subscribe("attunement_changed", func(p): attune[str(p.get("actor", ""))] = {"dealt": float(p.dealt), "taken": float(p.taken)}, 20)
	GameEvents.subscribe("room_entered", func(p): if flying.has(str(p.get("actor", ""))): flight.stop_flight(str(p.actor), "room"), 20)
	GameEvents.subscribe("room_entered", func(p): if melody.has(str(p.get("actor", ""))): flute.end_melody(game.character(str(p.actor)), "room"), 20)
	GameEvents.subscribe("room_entered", func(_p): ally_hots.clear(), 20)
	GameEvents.subscribe("room_entered", func(_p): _clear_room_marks(), 20)
	GameEvents.subscribe("actor_defeated", blood_path.feed_blood_essence, 20)
	GameEvents.subscribe("fell_out", _on_fell_out, 20)

func _on_stat_source(p: Dictionary) -> void:
	refresh_stats(str(p.get("actor", "")))

## S43 rule 6: a fall out of the room costs 5% of max HP (never below 1), except in the Prologue, towns and safe rooms.
func _on_fell_out(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	var room: Dictionary = game.room_rt.def if game.room_rt != null else {}
	if c == null or room.is_empty() or room.get("safe", false) or str(room.get("region", "")) == "lotus_ferry" or str(room.get("type", "")) in ["town", "prologue"]:
		return
	var cost: float = minf(c.pools.max_hp * float(ContentDB.stat_const("move.fall_cost_pct", 0.05)), c.pools.hp - 1.0)
	if cost > 0.0: apply_resource_change(c.id, "hp", -cost, "fall")

func _clear_room_marks() -> void:
	arrays.clear()
	ground_fires.clear()
	searched.clear()
	poison_touch.clear()
	for aid in decoys.keys():
		decoys.erase(aid)
		emit("illusion_broken", {"actor": aid, "reason": "room"})

## S49 weather (v1.1): the sky over this room lends its modifiers (calendar.json weather_effects); never gating.
func apply_weather(actor_id: String, weather: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.stats.remove_prefix("weather:")
	var mods: Array = ContentDB.config("calendar").get("weather_effects", {}).get(weather, {}).get("stats", [])
	for i in mods.size():
		var m: Dictionary = mods[i].duplicate(true)
		m.source = "weather:%s:%d" % [weather, i]
		c.stats.add_modifier(m)
	refresh_stats(actor_id)

func refresh_stats(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var qi_was: float = c.pools.max_qi
	var changed := StatRules.rebuild(c, game.account)
	# Decision 45: a Qi pool that opens now (with the first technique, at Bone Forging 1) opens full, so the art it came
	# with can be cast at once. A pool that grows keeps its fill (ResourcePool.set_max).
	if qi_was <= 0.0 and c.pools.max_qi > 0.0: c.pools.qi = c.pools.max_qi
	if not changed.is_empty():
		emit("stats_changed", {"actor": c.id, "changed_ids": changed})
		for pool in ["hp", "qi", "soul"]:
			emit("resource_changed", {"actor": c.id, "pool": pool, "value": c.pools.get_value(pool), "max": c.pools.get_max(pool)})

func timeline(actor_id: String) -> Dictionary:
	if not actors.has(actor_id):
		actors[actor_id] = {"action": "", "t": 0.0, "duration": 0.0, "hit_at": 0.0, "hit_done": true, "combo": -1, "window": 0.0,
			"queued": 0, "family": "fists", "technique": "", "guard": false, "guard_t": 0.0, "dodge_t": 0.0, "facing": 1,
			"forced": Vector2.ZERO, "forced_t": 0.0, "flinch": 0.0, "stance": 0.0, "last_attack_facing": 1, "hits": 0, "targets_hit": [],
			"finisher_q": {}, "chain": -1}
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
	f *= 1.0 - game.field.loss_of(actor_id)   # S28: pressed by a stronger Presence
	if float(tl.flinch) > 0.0: f *= 0.2
	if melody.has(actor_id): f *= float(StatRules.family(c).get("channel", {}).get("move_factor", 0.5))   # S47 v1.1: playing as you walk
	return f

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"basic_attack": return basic_attack(c, int(intent.get("facing", 1)), intent.get("aim", Vector2.ZERO), bool(intent.get("aimed", false)),
			bool(intent.get("finisher", false)), float(intent.get("charge_s", 0.0)))
		"use_technique": return use_technique(c, int(intent.get("slot", -1)), int(intent.get("facing", 1)), intent.get("aim", Vector2.ZERO),
			bool(intent.get("aimed", false)), float(intent.get("dist", -1.0)))
		"guard_start": return guard(c, true)
		"guard_end": return guard(c, false)
		"dodge": return dodge(c, intent.get("direction", Vector2.ZERO), int(intent.get("facing", 1)), bool(intent.get("moves", true)))
		"move_cancel": return move_cancel(c)
		"choose_revival": return choose_revival(c, str(intent.get("where", "shrine")))
		"start_flight": return start_flight(c)
		"use_treasure": return use_treasure(c, int(intent.get("slot", 0)))
		"toggle_sword_release": return toggle_sword_release(c)
		"self_detonate": return self_detonate(c, int(intent.get("index", -1)), bool(intent.get("confirm", false)))
		"channel_melody": return channel_melody(c, bool(intent.get("on", true)))
		"plunge": return plunge(c)
		"glide": return glide(c, bool(intent.get("on", true)))
		"stop_flight":
			stop_flight(c.id, str(intent.get("reason", "landed")))
			return ok()
	return fail("unknown_intent")

# ------------------------------------------------------------------ views
## Half the player's body across, for a blow to land on it: the side view's 14, on the height grid as much wider as the
## people there are drawn (decision 43, TopdownRoom.PEOPLE: 17).
func body_half_width() -> float:
	return roundf(14.0 * TopdownRoom.PEOPLE) if grid() != null else 14.0

func player_view(c) -> Dictionary:
	var tl := timeline(c.id)
	var st: ActorState = game.actor_state(c.id)
	var v := CombatRules.fighter(c)
	v.merge({"id": c.id, "vulnerable": c.pools.has_status("vulnerable"), "shocked": c.pools.has_status("shock"),
		"guarding": c.stats.value("guard") if tl.guard else 0.0, "facing": int(tl.facing),
		"x": st.plane.x if st else 0.0, "y": st.plane.y if st else 0.0, "alt": st.altitude if st else 0.0, "half_width": body_half_width(), "height": 88.0})
	v.crit_chance = float(v.crit_chance) + sword.killing_intent_stacks(c.id) * float(ContentDB.stat_const("killing_intent", {}).get("crit_per_stack", 0.01))
	v.penetration = float(v.penetration) + sword.intent_penetration(c)
	if grid() != null:   # redesign Phase 2: its blows go along its aim, between compatible heights
		v.aim = tl.get("aim", Vector2(tl.facing, 0))
		v.band = TopdownAim.band(airborne(c.id))
	return v

func enemy_view(e: EnemyState) -> Dictionary:
	var v := CombatRules.foe(e.stats, e.level, e.element)
	v.erase("max_hp")
	v.merge({"id": str(e.uid), "realm_index": e.realm_index, "role": e.role,
		"vulnerable": e.pools.has_status("vulnerable"), "shocked": e.pools.has_status("shock"), "sundered": e.pools.has_status("sundered"),
		"guarding": float(e.def.get("front_guard", 0.0)) if e.ai.state == "guard" else 0.0,
		"x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover, "half_width": e.half_width(), "height": e.height()}, true)
	if grid() != null:
		v.aim = e.aim_dir()
		v.band = TopdownAim.band(false)
	return v

## The loaded room's height grid when it is a top-down room (redesign Phase 2), else null.
func grid() -> TopdownRoom:
	return game.room_rt.topdown if game.room_rt != null else null

## Which way a push from `from` drives a body at `to`: away along the plane on the top-down grid, along x in the side
## view.
func away(from: Vector2, to: Vector2) -> Vector2:
	if grid() != null:
		var d := to - from
		return d.normalized() if d.length() > 0.01 else Vector2.RIGHT
	return Vector2(signf(to.x - from.x), 0)

## Hit-stop (redesign Phase 2): a view that freezes the fight for the blow's hitstop asks here each physics frame; while
## it runs the frame is spent (true) and the view holds the simulation still. Decision 43: a hit-stop of n frames holds n
## frames (the clock's rounding held one more before).
func hold_for_hitstop(delta: float) -> bool:
	if hitstop <= HITSTOP_EPS:
		hitstop = 0.0
		return false
	hitstop -= delta
	return true

const HITSTOP_EPS := 0.001

## Decision 43: a blow's hit-stop, within what its action may still add (CombatFeel.hitstop_cap_s: a many-hit art's
## blows share one cap, so hit-stop never stalls a chain); each blow's own frames stay its weight's.
func _add_hitstop(tl: Dictionary, want: float) -> void:
	var left := CombatFeel.hitstop_cap_s() - float(tl.get("stop_spent", 0.0))
	var before := hitstop
	hitstop = maxf(hitstop, minf(want, maxf(0.0, left)))
	tl.stop_spent = float(tl.get("stop_spent", 0.0)) + (hitstop - before)

## Redesign Phase 2: the body's facing on the plane, from its controller; between blows it is where a guard faces and
## where the next tap aims from.
func face_on_plane(actor_id: String, v: Vector2) -> void:
	if v.length() > 0.01 and not is_busy(actor_id): timeline(actor_id).aim = v.normalized()

## A view's aim: its `aim` on the plane, else its facing along x.
static func aim_of(v: Dictionary, facing: int) -> Vector2:
	return v.get("aim", Vector2(facing, 0))

## 2.5D hit test (S12): x range in the facing direction, depth band, altitude overlap. On the top-down plane (redesign
## Phase 2) the attacker's view carries its `aim`: the range runs along the aim and the depth band across it, and its
## `band` replaces the altitude overlap (TopdownAim: the target's feet within the attacker's height band). Without an
## aim the aim is the facing along x, which is the side view's test exactly.
static func hit_test(a: Dictionary, facing: int, hitbox: Dictionary, t: Dictionary, both_sides := false) -> bool:
	var xr: Array = hitbox.get("x", [0, 40])
	var aim: Vector2 = a.get("aim", Vector2(facing, 0))
	var d := Vector2(float(t.x) - float(a.x), float(t.y) - float(a.y))
	var dx := d.dot(aim)
	if both_sides: dx = absf(dx) if a.has("aim") else absf(d.x)
	var hw := float(t.get("half_width", 16))
	if dx < float(xr[0]) - hw or dx > float(xr[1]) + hw: return false
	if (absf(d.cross(aim)) if a.has("aim") else absf(d.y)) > float(hitbox.get("depth", 26)): return false
	if a.has("band"): return float(t.alt) - float(a.alt) >= float(a.band[0]) and float(t.alt) - float(a.alt) <= float(a.band[1])
	var alt: Array = hitbox.get("alt", [-30, 60])   # S43 rule 10: relative to the attacker's height
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

func target_for(c, reach: float, depth: float, facing: int, aim := Vector2.ZERO, aimed := false) -> Dictionary:
	# Auto-target: nearest enemy in the facing direction within reach and depth band;
	# otherwise turn toward the nearest enemy within 160 units.
	if game.room_rt == null: return {"facing": facing}
	if grid() != null: return _target_on_plane(c, reach, facing, aim, aimed)
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

## Redesign Phase 2 (decision 30): the aim on the plane. A tap (`aimed` false) soft-locks the nearest foe in the cone
## round `aim` (the stick or the facing); a dragged aim snaps to a foe within a few degrees of it and otherwise goes
## where it was dragged. {facing: its side for the pose's mirror, aim: the unit direction, target: the foe's uid}.
func _target_on_plane(c, reach: float, facing: int, aim: Vector2, aimed: bool) -> Dictionary:
	var st: ActorState = game.actor_state(c.id)
	var dir: Vector2 = aim.normalized() if aim.length() > 0.1 else timeline(c.id).get("aim", Vector2(facing, 0))
	var out := {"facing": 1 if dir.x >= 0.0 else -1, "aim": dir}
	if st == null: return out
	var foes: Array = game.room_rt.living_enemies()
	var air := airborne(c.id)
	var foe := TopdownAim.snap(foes, st.plane, st.altitude, dir, reach, air) if aimed else TopdownAim.soft_target(foes, st.plane, st.altitude, dir, air)
	if foe == null: return out
	var to: Vector2 = foe.plane - st.plane
	if to.length() > 0.5: dir = to.normalized()
	return {"facing": 1 if dir.x >= 0.0 else -1, "aim": dir, "target": foe.uid, "at": foe.plane}

## In the air: neither standing on a surface, climbing nor flying (S43).
func airborne(actor_id: String) -> bool:
	var st: ActorState = game.actor_state(actor_id)
	return st != null and st.surface == null and not st.flying and st.climbing.is_empty()

## Hands are busy on a ladder, rope, vine or chain: techniques wait unless flagged on_climb (S43 rule 5).
func climbing(actor_id: String) -> bool:
	var st: ActorState = game.actor_state(actor_id)
	return st != null and not st.climbing.is_empty()

## `finisher` (top-down decision 35, a long drag on Attack): the combo's last step at once, on the ground. Mid-chain it
## waits for the step under way to end, then comes in place of the steps between. Decision 45: it is the charged attack,
## `charge_s` the seconds the drag was held past the finisher's line (CombatFeel.charge_ratio: up to 1.8-2.5 basic hits);
## a one-step family (the bow, the flute) charges its one shot.
func basic_attack(c, facing: int, aim_in := Vector2.ZERO, aimed := false, finisher := false, charge_s := 0.0) -> Dictionary:
	var reason := can_act(c)
	if reason != "": return fail(reason)
	if climbing(c.id): return fail("climbing")
	if not Unlocks.is_unlocked(c.id, "attack"): return fail("locked")
	var tl := timeline(c.id)
	facing = 1 if facing >= 0 else -1
	var fam := StatRules.family(c)
	# S47: while the jian flies on its own, the hands fight with Qi palms (the fist family, at x0.8).
	var palms := sword_released.has(c.id)
	if palms: fam = ContentDB.entry("weapon_families", "fists")
	var combo: Array = fam.get("combo", [])
	if combo.is_empty(): return fail("no_combo")
	var in_air := airborne(c.id)
	finisher = finisher and not in_air
	if is_busy(c.id) and grid() != null and tl.technique != "":
		# Decision 42 (on the grid): a basic attack cuts a technique's recovery once its active frames have played, and
		# the chain the technique was woven into carries on; sooner the hands are busy (the player's buffer holds the
		# press until the cut, CombatFeel.weave).
		if CombatFeel.weave(tl, "basic", c) != "cancel": return fail("busy")
		var chain := int(tl.get("chain", -1))
		_weave_cut(c, "basic")
		if chain >= 0 and chain < combo.size() - 1:
			tl.combo = chain
			tl.window = float(ContentDB.stat_const("combat.combo_window_s", 0.5))
	if is_busy(c.id):
		if finisher and tl.technique == "" and int(tl.combo) >= 0 and int(tl.combo) < combo.size() - 1:
			tl.finisher_q = {"facing": facing, "aim": aim_in, "aimed": aimed, "charge_s": charge_s}
			tl.queued = 0
			return ok({"queued": true, "finisher": true})
		if not in_air and int(tl.combo) >= 0 and int(tl.combo) < combo.size() - 1:
			tl.queued = mini(int(tl.queued) + 1, combo.size() - 1 - int(tl.combo))
			# Decision 43: the queued step aims again as it starts, from the stick of the latest press (_aim_queued).
			tl.queue_aim = aim_in
			tl.queue_aimed = aimed
		return ok({"queued": true})
	# S43 air attack: one hit, no combo, +10% damage.
	var index := 0 if in_air else (int(tl.combo) + 1 if float(tl.window) > 0.0 and int(tl.combo) < combo.size() - 1 else 0)
	if finisher: index = combo.size() - 1
	tl.finisher_q = {}
	var aim := target_for(c, float(fam.get("reach", 46)), float(fam.get("depth", 30)), facing, aim_in, aimed)
	if aim.has("aim"): tl.aim = aim.aim
	tl.target_at = aim.get("at", null)   # decision 43: where the foe it picked stands (the step's pull toward it)
	_start_step(c, fam, index, int(aim.facing), finisher, charge_s)
	if palms:
		tl.step = (tl.step as Dictionary).duplicate()
		tl.step.mult = float(tl.step.get("mult", 1.0)) * float(ContentDB.stat_const("sword_release.palm_mult", 0.8))
	if in_air:
		tl.step = (tl.step as Dictionary).duplicate()
		tl.step.mult = float(tl.step.get("mult", 1.0)) * float(ContentDB.stat_const("move.air_attack_mult", 1.1))
		tl.air_attack = true
	else:
		tl.air_attack = false
	return ok({"action": tl.action, "duration": tl.duration, "facing": tl.facing, "combo": index, "air": in_air, "aim": aim.get("aim", Vector2(tl.facing, 0)),
		"finisher": finisher, "at": aim.get("at", null), "charge": float(tl.get("charge", 0.0))})

func _start_step(c, fam: Dictionary, index: int, facing: int, finisher := false, charge_s := 0.0) -> void:
	var tl := timeline(c.id)
	var step: Dictionary = fam.combo[index]
	tl.charge = 0.0
	if finisher:
		# Decision 45: the charged blow, its multiplier by the charge held (CombatFeel.charged_mult); `charge` its ratio
		# over one basic hit, for the combat text.
		step = step.duplicate()
		step.mult = CombatFeel.charged_mult(fam, charge_s)
		tl.charge = CombatFeel.charge_ratio(fam, charge_s)
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
	tl.chain = -1
	tl.charged = finisher   # decision 38: a dragged finisher weighs as the charged blow (CombatFeel)
	tl.starts = int(tl.get("starts", 0)) + 1   # decision 43: the player's view follows each new step once (its turn, its pull)
	tl.stop_spent = 0.0
	if game.character(c.id).cultivator.meditating: game.progression.stop_meditation(c, "attack")
	var ev := {"actor": c.id, "action": tl.action, "technique": "", "windup": tl.hit_at, "duration": tl.duration, "facing": facing, "combo": index}
	if finisher: ev.finisher = true
	if grid() != null: ev.aim = tl.get("aim", Vector2(facing, 0))
	emit("attack_started", ev)

func use_technique(c, slot: int, facing: int, aim_in := Vector2.ZERO, aimed := false, dist := -1.0) -> Dictionary:
	var reason := can_act(c)
	if reason != "": return fail(reason)
	if slot < 0 or slot >= ProgressionRules.technique_slot_count(c): return fail("slot_locked")
	var tid = c.cultivator.technique_slots[slot]
	if tid == null or str(tid) == "": return fail("empty_slot")
	var t := ContentDB.entry("techniques", str(tid))
	if str(t.get("damage_type", "")) == "sword_release": return sword.toggle_sword_release(c)
	if str(t.get("damage_type", "")) == "sword_swarm": return swarm.toggle_sword_swarm(c, t)
	var tl := timeline(c.id)
	# Decision 42 (on the grid): a technique cuts a basic step's recovery once its blow has landed; sooner the hands are
	# busy (the player's buffer holds the press until the cut, CombatFeel.weave). The cut is made once the technique is
	# sure to go, just before it is paid for.
	var weave: bool = grid() != null and is_busy(c.id) and CombatFeel.weave(tl, "technique", c) == "cancel"
	if is_busy(c.id) and not weave: return fail("busy")
	if climbing(c.id) and not t.get("on_climb", false): return fail("climbing")
	var fam := StatRules.family(c)
	var tfam := str(t.get("family", "any"))
	if tfam != "any" and not (tfam == str(fam.id) or (tfam == "fists" and fam.id in ["fists", "gauntlets"])): return fail("wrong_weapon", {"text": Tx.t("sim.combat.needs_a") % tfam.replace("_", " ")})
	# P13a a keystone is its kin group's: any weapon of the group (the Body and Voice group's work with anything held).
	if not TechniqueTreeRules.kin_holds(t, str(fam.id)): return fail("wrong_weapon", {"text": Tx.t("sim.combat.needs_kin") % Tx.t("technique.kin." + str(t.kin))})
	if c.pools.cooldown("tech:" + str(tid)) > 0.0: return fail("cooldown")
	if c.pools.has_status("qi_seal") and not StatRules.body_flag(c, "qi_seal_immune"): return fail("sealed")
	# S48 paths as layers: Blood arts need the Blood path; the Golden Body needs a vow held.
	if t.get("blood_path", false) and not ProgressionAuthority.walks(c, "blood"): return fail("needs_blood_path", {"text": Tx.t("sim.combat.needs_blood_path")})
	if t.get("confucian_path", false) and not ProgressionAuthority.walks(c, "confucian"): return fail("needs_confucian_path", {"text": Tx.t("sim.combat.needs_confucian_path")})
	if t.get("needs_vow", false) and c.cultivator.vows.is_empty(): return fail("needs_vow", {"text": Tx.t("sim.combat.needs_vow")})
	if t.get("flying_only", false):
		var st: ActorState = game.actor_state(c.id)
		if st == null or st.surface != null: return fail("needs_flight")
	var cost := technique_cost(c, t)
	# S48 sect tree: the Lotus branch's last node makes the signature arts cheaper.
	var sig := ProgressionRules.signature_variant(c, str(tid))
	if not sig.is_empty(): cost *= maxf(0.0, 1.0 + ProgressionRules.sect_tree_flag(c, "signature_cost"))
	# S10 Essence 25: the first technique of each fight costs no QI.
	var free_first: bool = StatRules.gate_flag(c, "first_technique_free") and game.sim_time - float(tl.get("fight_t", -999.0)) > float(ContentDB.stat_const("gates", {}).get("fight_gap_s", 8.0))
	if free_first: cost = 0.0
	# S48 Copper Body: a body technique the QI cannot pay for spends HP instead, never below a fifth of it.
	var hp_cost := body_hp_cost(c, t, cost)
	if float(t.get("qi_cost", 0)) > 0 and hp_cost <= 0.0 and not breath_only(c) and (c.pools.max_qi <= 0.0 or c.pools.qi < cost): return fail("no_qi")
	if float(t.get("soul_cost", 0)) > 0 and c.pools.soul < float(t.soul_cost): return fail("no_soul")
	if float(t.get("composure_cost", 0)) > 0 and c.pools.composure < float(t.composure_cost): return fail("no_composure")
	# Decision 42: the chain it is woven into (the basic step it cuts, or the one just ended within the combo's window)
	# carries on after it.
	var chain := -1
	if grid() != null and bool(CombatFeel.weave_cfg().get("chain_through", true)) and int(tl.combo) >= 0 \
			and (weave or (tl.action == "" and float(tl.window) > 0.0)):
		chain = int(tl.combo)
	if weave: _weave_cut(c, "technique")
	# S48 costly arts (Blood Burning): a share of max HP and a body injury, paid up front.
	if float(t.get("hp_cost_pct", 0.0)) > 0.0:
		var blood: float = c.pools.max_hp * float(t.hp_cost_pct)
		# S48 the Blood path: blood essence pays first, a point for each 1% of max HP.
		var covered := minf(blood_path.essence_of(c.id), float(t.hp_cost_pct) * 100.0) if t.get("blood_path", false) else 0.0
		blood -= c.pools.max_hp * covered / 100.0
		if c.pools.hp - blood < 1.0: return fail("no_hp", {"text": Tx.t("sim.combat.not_enough_blood")})
		if covered > 0.0: blood_path.spend_essence(c.id, covered)
		if blood > 0.0: apply_resource_change(c.id, "hp", -blood, "technique")
		if t.get("blood_path", false):
			game.training.apply_reputation(c.id, "", int(ContentDB.stat_const("paths", {}).get("blood", {}).get("use_reputation", -1)))
		if t.has("injury"): game.progression.apply_injury(c.id, str(t.injury.get("kind", "body")), int(t.injury.get("severity", 1)))
	if hp_cost > 0.0: apply_resource_change(c.id, "hp", -hp_cost, "technique")
	elif cost > 0.0: apply_resource_change(c.id, "qi", -cost, "technique")
	tl.fight_t = game.sim_time
	sword.natal_overcharge(c)
	if float(t.get("soul_cost", 0)) > 0: apply_resource_change(c.id, "soul", -float(t.soul_cost), "technique")
	if float(t.get("composure_cost", 0)) > 0:
		apply_resource_change(c.id, "composure", -float(t.composure_cost), "technique")
		c.pools.since_composure_use = 0.0
	c.pools.cooldowns["tech:" + str(tid)] = maxf(0.5, float(t.get("cooldown_s", 5)) + (ProgressionRules.sect_tree_flag(c, "signature_cooldown") if not sig.is_empty() else 0.0))
	if sig.has("heal_pct") or sig.has("shield_pct"): heals.sect_support(c, sig)
	var aim := target_for(c, TopdownAim.reach_of(t) if grid() != null else float(t.hitbox.x[1]), float(t.hitbox.get("depth", 30)), 1 if facing >= 0 else -1, aim_in, aimed)
	if aim.has("aim"):
		# Redesign Phase 2: the aim on the plane, and where a circle at a point lands: the drag's length, else the foe
		# it locked, else two thirds of the reach.
		tl.aim = aim.aim
		var st0: ActorState = game.actor_state(c.id)
		var from: Vector2 = st0.plane if st0 else Vector2.ZERO
		var d := dist if dist >= 0.0 else (from.distance_to(aim.at) if aim.has("at") else TopdownAim.reach_of(t) * 0.66)
		tl.at = TopdownAim.point_at(from, aim.aim, d, TopdownAim.reach_of(t))
	var action := str(t.get("action", "")) if t.get("action") != null else ""   # P13a: a null pose read as "<null>" before
	if action == "" or action == "null": action = str(fam.combo[mini(2, fam.combo.size() - 1)].action)
	if action == "meditate_burst": action = str(fam.combo[0].action)
	tl.action = action
	tl.t = 0.0
	tl.duration = float(t.get("windup_s", 0.2)) + float(t.get("active_s", 0.2)) + 0.25
	tl.hit_at = float(t.get("windup_s", 0.2))
	tl.hit_done = false
	tl.combo = -1
	tl.chain = chain
	tl.queued = 0
	tl.finisher_q = {}
	tl.technique = str(tid)
	tl.facing = int(aim.facing)
	tl.targets_hit = []
	tl.step = {}
	tl.starts = int(tl.get("starts", 0)) + 1
	tl.stop_spent = 0.0
	if t.has("dash"):
		tl.forced = aim_of(tl, tl.facing) * float(t.dash) / 0.2 if grid() != null else Vector2(tl.facing * float(t.dash) / 0.2, 0)
		tl.forced_t = 0.2
	var ev := {"actor": c.id, "action": action, "technique": tid, "windup": tl.hit_at, "duration": tl.duration,
		"facing": tl.facing, "element": str(t.get("element", "none"))}
	if grid() != null:
		ev.aim = tl.aim
		ev.at = tl.at
	emit("attack_started", ev)
	return ok({"action": action, "duration": tl.duration, "facing": tl.facing, "technique": tid, "aim": aim.get("aim", Vector2(tl.facing, 0))})

## In a fight: a blow struck or taken within the fight gap (8 s). Tree nodes are realised and let go only out of one.
func in_combat(c) -> bool:
	return game.sim_time - float(timeline(c.id).get("fight_t", -999.0)) < float(ContentDB.stat_const("gates", {}).get("fight_gap_s", 8.0))

## The body stages (stats.json technique_cost.free_without_pool): with no Qi pool yet a technique costs no Qi, only its
## cooldown.
## Decision 45: the pool Qi regenerates from: the pool, or stats.json regen_per_s.qi_floor_pool when that is more, so
## the small first pool (about 30 at Bone Forging 1) visibly refills (0.75 Qi a second at rest, 6 meditating).
static func qi_regen_pool(c) -> float:
	return maxf(c.pools.max_qi, float(ContentDB.stat_const("regen_per_s.qi_floor_pool", 0.0))) if c.pools.max_qi > 0.0 else 0.0

func breath_only(c) -> bool:
	return bool(ContentDB.stat_const("technique_cost", {}).get("free_without_pool", false)) and c.pools.max_qi <= 0.0

func technique_cost(c, t: Dictionary) -> float:
	if breath_only(c): return 0.0
	var st: Dictionary = ContentDB.stat_const("technique_cost", {})
	var base := float(t.get("qi_cost", 0))
	var lv := ProgressionRules.level(c)
	var m: Dictionary = c.cultivator.mastery.get(str(t.id), {"tier": 1})
	var mastery_red := float(st.get("mastery_cost_per_tier", -0.05)) * (int(m.tier) - 1)
	var dao_tier := ProgressionRules.effective_dao_tier(c, str(t.get("dao", "")))
	var dao_red := -0.1 if dao_tier >= 2 else 0.0
	var comp := float(st.get("composure_zero_factor", 1.5)) if Unlocks.is_unlocked(c.id, "composure") and c.pools.composure <= 0.0 else 1.0
	if hollow_burdened(c): comp *= float(ContentDB.stat_const("hollowing.cost_mult", 1.25))   # S28: the Hollowing's burden
	# S48 Ember Channel: some cost cuts hold only for one element's techniques.
	var cut: float = c.stats.value("technique_cost") + c.stats.conditional("technique_cost", "element", str(t.get("element", "none")))
	cut += float(TechniqueTreeRules.passives(c, t).get("cost", 0.0))   # P13a: the tree's even-ring passages (within the 30% cap)
	return maxf(0.0, base * (1.0 + float(st.get("per_level", 0.04)) * lv) * (1.0 - minf(0.3, cut)) * (1.0 + mastery_red + dao_red) * comp)

## S48: the HP a body technique spends when QI is short (Copper Body and above); 0 when it spends QI or cannot.
func body_hp_cost(c, t: Dictionary, qi_cost: float) -> float:
	if not t.get("body", false) or qi_cost <= 0.0 or c.pools.qi >= qi_cost or not StatRules.body_flag(c, "hp_techniques"): return 0.0
	var k: Dictionary = ContentDB.stat_const("body_path", {})
	var hp: float = c.pools.max_hp * qi_cost / maxf(1.0, c.pools.max_qi) * float(k.get("hp_share_per_qi_share", 1.0))   # P12: shares, as Might scales HP only
	return hp if c.pools.hp - hp >= c.pools.max_hp * float(k.get("hp_floor", 0.2)) else 0.0

## A technique's element; under Qi Deviation (S48) the Qi goes astray and each use takes a random one (combat stream).
func technique_element(c, t: Dictionary) -> String:
	if c.pools.has_status("qi_deviation"):
		var els: Array = ContentDB.stat_const("qi_deviation", {}).get("elements", ["water", "wood", "fire", "earth", "metal"])
		return str(els[Rng.stream(c.id, "combat").randi_range(0, els.size() - 1)])
	return str(t.get("element", "none"))

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

## `moves` false: the body's own controller carries the dodge (the top-down motor's dash, redesign Phase 2); Combat
## keeps the cooldown, the i-frames and the events, and gives no forced motion or air art.
func dodge(c, direction, facing: int, moves := true) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "dodge_dash"): return fail("locked")
	if wounded.has(c.id) or c.pools.blocked("move"): return fail("stunned")
	# S10 Agility 50: a second dodge charge, on its own cooldown.
	var charge := "dodge"
	var free := false
	if c.pools.cooldown("dodge") > 0.0:
		if StatRules.gate_flag(c, "dodge_second_charge") and c.pools.cooldown("dodge_2") <= 0.0:
			charge = "dodge_2"
		else:
			# A Wind Step Talisman's charge (S47) spends itself on a dodge the cooldown would refuse.
			if float(treasure_fx.get(c.id, {}).get("free_dodge", 0.0)) <= 0.0: return fail("cooldown")
			free = true
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
	# Decision 38 (on the grid): a dodge cancels a blow's anticipation or its late recovery, never its active window.
	if grid() != null:
		var rule := CombatFeel.dodge_cancel(tl, c)
		if rule == "committed": return fail("committed")
		if rule == "cancel": _cancel_blow(c)
	if free: treasure_fx[c.id].erase("free_dodge")   # spent only by a dodge that happens
	# Swallow Dart (Qi Kindling 7): an Evade tap in the air darts 140 and holds the height for 0.25 s,
	# once per airtime. It shares the dodge's cooldown.
	if moves and st != null and st.surface == null and not st.flying and st.climbing.is_empty() and flight.knows_art(c, "air_dash") and not st.air_dash_used \
			and c.pools.cooldown("dodge") <= 0.0:
		st.arts["air_dash"] = true
		if MovementSolver.air_dash(st):
			var ax := signf(dir.x) if absf(dir.x) > 0.2 else (1.0 if facing >= 0 else -1.0)
			var dash_s := float(ContentDB.movement("air_dash.hold_s", 0.25))
			tl.forced = Vector2(ax, 0) * float(ContentDB.movement("air_dash.distance", 140.0)) / dash_s
			tl.forced_t = dash_s
			c.pools.cooldowns["dodge"] = _dodge_cooldown(c)
			LocalAuthority.announce(st, c.id)
			return ok({"air_dash": true})
	if moves and st != null and st.surface == null and not st.flying and "wind_blink" in c.cultivator.secret_arts and c.pools.cooldown("wind_blink") <= 0.0:
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
	tl.forced_t = 0.22 if moves else 0.0
	tl.dodge_t = float(conf.get("dodge_invuln_s", 0.25))
	c.pools.cooldowns[charge] = _dodge_cooldown(c)
	if c.cultivator.meditating: game.progression.stop_meditation(c, "dodge")
	emit("dodged", {"actor": c.id, "direction": dir})
	return ok()

## Decision 43: the stick pushed out of a blow (the player's view asks when it is pushed past its tiptoe band and no
## press waits): past the blow's cancel point (the dodge's, CombatFeel.dodge_cancel), in its recovery, with no step queued
## after it, the blow ends there and the body moves off; sooner the blow goes on.
func move_cancel(c) -> Dictionary:
	if grid() == null or not bool(CombatFeel.flow().get("move_cancel", true)): return fail("off")
	var tl := timeline(c.id)
	if CombatFeel.phase_of(tl, c) != "recovery" or CombatFeel.dodge_cancel(tl, c) != "cancel": return fail("committed")
	if CombatFeel.waits_ahead(tl): return fail("queued")
	_cancel_blow(c)
	return ok()

## Decision 43: a queued step aims again as it starts, at the foe the stick of its press picks (the soft lock round it,
## as a tap aims), so a chain turns with the stick; the player's view turns the body and pulls it in (tl.starts).
func _aim_queued(c, fam: Dictionary, tl: Dictionary) -> Dictionary:
	if grid() == null: return {"facing": int(tl.facing)}
	var aim := target_for(c, float(fam.get("reach", 46)), float(fam.get("depth", 30)), int(tl.facing), tl.get("queue_aim", Vector2.ZERO), bool(tl.get("queue_aimed", false)))
	if aim.has("aim"): tl.aim = aim.aim
	tl.target_at = aim.get("at", null)
	return aim

## Decision 38: a dodge out of a blow. In its anticipation the blow is dropped (a combo step does not count, so the next
## press repeats it); in its late recovery the blow ends there. A combo keeps its window for the next step.
func _cancel_blow(c) -> void:
	var tl := timeline(c.id)
	var phase := CombatFeel.phase_of(tl, c)
	var basic: bool = tl.technique == ""
	if not tl.hit_done:
		tl.hit_done = true
		if basic: tl.combo = int(tl.combo) - 1
	var size: int = (ContentDB.entry("weapon_families", str(tl.family)).get("combo", []) as Array).size()
	tl.window = float(ContentDB.stat_const("combat.combo_window_s", 0.5)) if basic and int(tl.combo) >= 0 and int(tl.combo) < size - 1 else 0.0
	if tl.window <= 0.0: tl.combo = -1
	tl.action = ""
	tl.queued = 0
	tl.finisher_q = {}
	emit("attack_cancelled", {"actor": c.id, "phase": phase})

## Decision 42: the blow under way ends in its recovery, cut by the next press (a technique into a basic step's, a basic
## attack into a technique's; CombatFeel.weave). Its hit has landed, so nothing is dropped; the steps queued after it
## give way to the press.
func _weave_cut(c, into: String) -> void:
	var tl := timeline(c.id)
	emit("attack_cancelled", {"actor": c.id, "phase": "recovery", "into": into})
	tl.action = ""
	tl.queued = 0
	tl.finisher_q = {}

## The dodge's cooldown: Swallow's Breath (S48) shortens it, and so does the Agility 25 meridian gate (S10).
func _dodge_cooldown(c) -> float:
	var cd: float = float(ContentDB.stat_const("combat", {}).get("dodge_cooldown_s", 2.5)) * (1.0 + c.stats.value("dodge_cooldown"))
	return cd * 0.8 if StatRules.gate_flag(c, "dodge_cooldown_20") else cd

# ------------------------------------------------------------------ tick
func tick(delta: float) -> void:
	if hitstop > 0.0:
		hitstop = maxf(0.0, hitstop - delta)
	var c = game.active()
	if c != null:
		_tick_player(c, delta)
		_tick_pools(c, delta)
		flight.tick_flight(c, delta)
		flight.tick_glide(c, delta)
		treasures.tick_treasures(c, delta)
		sword.tick_sword(c, delta)
		swarm.tick_swarm(c, delta)
		heals.tick_hots(c, delta)
		flute.tick_melody(c, delta)
		blood_path.tick_blood(c, delta)
		var body: ActorState = game.actor_state(c.id)
		if body != null and not body.plunge_impact.is_empty(): flight.resolve_plunge(c, body)
	projectiles.tick_projectiles(delta)
	heals.tick_ally_hots(delta)
	phantom.tick_decoys(delta)
	plates.tick_arrays(delta)
	_tick_ground_fires(delta)
	for uid in searched.keys():
		searched[uid].t = float(searched[uid].t) - delta
		if float(searched[uid].t) <= -2.0: searched.erase(uid)   # a little grace: the death is judged after the blow
	if game.room_rt:
		for e in game.room_rt.enemies.values():
			if e.alive: _tick_enemy_statuses(e, delta)
			# S28: an ally turned by the Hollow Tide comes back to itself.
			if e.ai.has("turned"):
				e.ai.turned = float(e.ai.turned) - delta
				if float(e.ai.turned) <= 0.0:
					e.ai.erase("turned")
					e.team = "ally"

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
		var fq: Dictionary = tl.get("finisher_q", {})
		if not fq.is_empty() and tl.technique == "":
			# Decision 35: a finisher asked for mid-chain comes now, in place of the steps between.
			tl.finisher_q = {}
			tl.action = ""
			tl.queued = 0
			basic_attack(c, int(fq.facing), fq.aim, bool(fq.aimed), true, float(fq.get("charge_s", 0.0)))
		elif int(tl.queued) > 0 and tl.technique == "" and int(tl.combo) < fam.get("combo", []).size() - 1:
			tl.queued = int(tl.queued) - 1
			_start_step(c, fam, int(tl.combo) + 1, int(_aim_queued(c, fam, tl).facing))
		else:
			tl.window = float(ContentDB.stat_const("combat.combo_window_s", 0.5)) if tl.technique == "" and int(tl.combo) < fam.get("combo", []).size() - 1 else 0.0
			# Decision 42: a technique woven into a chain hands it on: the next basic attack is the step after the one it cut.
			var chain := int(tl.get("chain", -1)) if tl.technique != "" else -1
			if chain >= 0 and chain < StatRules.family(c).get("combo", []).size() - 1:
				tl.combo = chain
				tl.window = float(ContentDB.stat_const("combat.combo_window_s", 0.5))
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
		if p.max_qi > 0 and p.qi < p.max_qi: apply_resource_change(c.id, "qi", qi_regen_pool(c) * c.stats.value("qi_regen") * delta, "regen", 0.0, true)
		if p.max_soul > 0 and p.soul < p.max_soul: apply_resource_change(c.id, "soul", p.max_soul * c.stats.value("soul_regen") * delta, "regen", 0.0, true)
	var burdened := hollow_burdened(c)
	if burdened and Unlocks.is_unlocked(c.id, "composure") and p.composure > 0.0:
		# S28: over half Hollowed, Composure drains instead of recovering.
		apply_resource_change(c.id, "composure", -float(ContentDB.stat_const("hollowing.composure_drain_per_s", 2.0)) * delta, "hollow", 0.0, true)
	elif Unlocks.is_unlocked(c.id, "composure") and p.composure < 100.0 and p.since_composure_use >= float(ContentDB.stat_const("composure.recover_delay_s", 3)):
		apply_resource_change(c.id, "composure", float(ContentDB.stat_const("composure.recover_per_s", 10)) * delta, "regen", 0.0, true)
	if p.hollowing > 0.0 and not c.cultivator.meditating:
		# Resting under a lit lantern (the Field's harbours) draws the grey out four times as fast.
		var lamp := float(ContentDB.stat_const("hollowing.lantern_mult", 4)) if game.room_rt and game.room_rt.def.get("lantern", false) else 1.0
		apply_resource_change(c.id, "hollowing", -float(ContentDB.stat_const("hollowing.decay_per_min", 1)) / 60.0 * delta * lamp, "decay", 0.0, true)

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
				var caster = game.character(str(s.get("source", "")))
				var reach := 0.0 if caster == null else maxf(caster.stats.value("physical_attack"), maxf(caster.stats.value("qi_attack"), caster.stats.value("soul_attack")))
				_damage_enemy(e, maxf(1.0, CombatRules.hp_share(e.pools.max_hp * float(s.get("power", 0.02)), e.role, reach)), str(s.get("source", "")), "dot", str(s.id), false, {})
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
		# The bow looses an arrow; the flute (S47 v1.1) sends a note of Qi.
		projectiles.spawn_projectile({"team": "player", "owner": c.id, "x": float(pv.x) + facing * 28, "y": float(pv.y), "alt": float(pv.alt) + 58,
			"dir": facing, "speed": float(fam.get("projectile_speed", 620)), "range": float(fam.get("reach", 480)),
			"pierce": 1 if str(fam.get("damage_type", "physical")) == "qi" and StatRules.gate_flag(c, "projectile_pierce") else 0,
			"art": str(fam.get("projectile_art", "arrow")), "attack": {"damage_type": str(fam.get("damage_type", "physical")), "element": "none",
			"mult": [float(step.get("mult", 1.0)), float(step.get("mult", 1.0))], "range": fam.range, "source": "basic",
			"dao_tier": _dao_tier(c, str(fam.get("dao", ""))), "charge": float(tl.get("charge", 0.0))}})
		return
	if step.has("throw"):
		# The fan's third stroke (S47 v1.1): thrown, it flies out and comes back, lifting what it cuts both ways.
		var th: Dictionary = step.throw
		var tm := float(step.get("mult", 1.0))
		projectiles.spawn_projectile({"team": "player", "owner": c.id, "x": float(pv.x) + facing * 24, "y": float(pv.y), "alt": float(pv.alt) + 56,
			"dir": facing, "speed": float(th.get("speed", 520)), "range": float(th.get("range", 280)), "pierce": 99, "returning": true,
			"art": str(th.get("art", "fan")), "attack": {"damage_type": "physical", "element": "wind", "mult": [tm, tm], "range": fam.get("range", [0.9, 1.1]),
			"dao_tier": _dao_tier(c, str(fam.get("dao", ""))), "knockup_s": float(th.get("knockup_s", 0.8)), "source": "basic",
			"charge": float(tl.get("charge", 0.0))}})
		return
	var reach_m := float(ProgressionRules.path_flag(c, "reach_mult", 1.0))   # S48 Coiled Dragon
	if fam.get("ring", false): reach_m *= 1.0 + c.stats.value("melody_power")   # P7b: the bell's ring carries further
	var hitbox := {"x": [-8, float(fam.get("reach", 46)) * reach_m], "depth": float(fam.get("depth", 30)), "alt": fam.get("altitude", [-30, 60])}
	var mult := float(step.get("mult", 1.0))
	var max_targets := int(fam.get("line_targets", 1))
	var hit_any := false
	# v1.2 the bell rings out on both sides of its bearer; its strikes (and the brush's) carry the family's damage type.
	var targets := _enemies_in(pv, facing, hitbox, fam.get("ring", false))
	_nearest_first(targets, pv)
	var n := 0
	for e in targets:
		if n >= max_targets: break
		var attack := {"damage_type": str(fam.get("damage_type", "physical")), "element": "none", "mult": [mult, mult], "range": fam.get("range", [0.9, 1.1]),
			"dao_tier": _dao_tier(c, str(fam.get("dao", ""))), "room_element": str(game.room_rt.def.get("element", "")) if game.room_rt else "",
			"sphere_element": game.field.sphere_element(c),
			"knockback": float(step.get("knockback", fam.get("knockback_every_hit", 0))), "source": "basic", "charge": float(tl.get("charge", 0.0))}
		if fam.has("backstab") and e.facing == facing: attack.situation = float(fam.backstab)
		if fam.has("armour_break"):
			attack.armour_break = {"chance": float(step.get("armour_break", fam.armour_break.get("chance", 0.3))),
				"duration_s": float(fam.armour_break.get("duration_s", 4))}
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
		for b2 in t.get("buffs", []):
			apply_buff(c.id, {"stat": b2.stat, "op": b2.get("op", "pct_add"), "value": b2.value, "duration": b2.duration, "source": "tech:%s:%s" % [t.id, b2.stat]}, "technique")
		# Soul Lantern Ward: a shield of a share of max HP (P12: blows grow with Might, max Soul does not) that takes blows
		# of any kind until its time is up.
		if float(t.get("shield_hp_pct", 0.0)) > 0.0:
			raise_shield(c, c.pools.max_hp * float(t.shield_hp_pct), float(t.get("shield_s", 6)))
		var healed := 0
		if float(t.get("allies_heal_pct", 0.0)) > 0.0:
			var song: float = 1.0 + (c.stats.value("melody_power") if str(t.get("dao", "")) == "music" else 0.0)
			healed = heals.heal_circle(c, float(t.allies_heal_pct) * song, float(t.get("allies_heal_s", 6)), float(t.get("heal_radius", 220)), "tech:" + str(t.id))
		emit("technique_used", {"actor": c.id, "technique": t.id, "hits": 1, "targets": healed})
		return
	if dtype == "illusion":
		phantom.cast_illusion(c, t)
		emit("technique_used", {"actor": c.id, "technique": t.id, "hits": 1, "targets": 0})
		return
	if dtype == "stance":
		for b3 in t.get("buffs", []):
			apply_buff(c.id, {"stat": b3.stat, "op": b3.get("op", "pct_add"), "value": b3.value, "duration": b3.duration, "source": "tech:%s:%s" % [t.id, b3.stat]}, "technique")
		if float(t.get("shield_hp_pct", 0.0)) > 0.0: raise_shield(c, c.pools.max_hp * float(t.shield_hp_pct), float(t.get("shield_s", 3)))
		tl.stance = float(t.get("stance_s", 2.0))
		tl.guard = true
		tl.guard_t = 0.0
		emit("system_used", {"actor": c.id, "system": "guard"})
		emit("technique_used", {"actor": c.id, "technique": t.id, "hits": 1, "targets": 0})
		return
	var attack := {"damage_type": "physical" if dtype == "movement" else dtype, "element": technique_element(c, t),
		"mult": t.get("mult", [1, 1]), "range": fam.get("range", [0.9, 1.1]), "dao_tier": _dao_tier(c, str(t.get("dao", ""))),
		"mastery_tier": tier - 1, "room_element": str(game.room_rt.def.get("element", "")) if game.room_rt else "",
		"sphere_element": game.field.sphere_element(c),
		"knockback": float(t.get("knockback", 0)) - float(t.get("pull", 0)), "ignore_armor": t.get("ignore_armor", false), "never_miss": t.get("never_miss", false),
		"ignore_resistance": float(t.get("ignore_resistance", 0.0)), "penetration_bonus": float(t.get("penetration", 0.0)),
		"status": t.get("status", {}), "source": "tech:" + str(t.id), "technique": str(t.id),
		"tree_pct": float(TechniqueTreeRules.passives(c, t).get("damage", 0.0))}   # P13a: the damage bucket's tree share
	if t.has("armour_break"): attack.armour_break = t.armour_break
	# v1.2 the brush writes a talisman with every technique: its element's rider (weapon_families.brush.talisman).
	var tal_def: Dictionary = fam.get("talisman", {})
	if not tal_def.is_empty():
		var by: Dictionary = tal_def.get("by_element", {})
		var row: Dictionary = by.get(CombatRules.parent_element(str(attack.element)), by.get("none", {}))
		if not row.is_empty():
			attack.talisman = {"id": str(row.id), "power": float(row.get("power", 1.0)),
				"remaining": float(row.get("duration_s", tal_def.get("duration_s", 4.0)))}
	# v1.2 the Confucian path: a written word is as strong as the mind that writes it (Insight against 5 + Level).
	if float(t.get("insight_scale", 0.0)) > 0.0:
		var ratio := clampf(c.stats.value("insight") / (5.0 + float(ProgressionRules.level(c))), 0.5, 3.0)
		var k := float(t.insight_scale)
		var im := (1.0 - k) + k * ratio
		attack.mult = [float(attack.mult[0]) * im, float(attack.mult[1]) * im]
	if float(t.get("knockup_s", 0.0)) > 0.0: attack.knockup_s = float(t.knockup_s)
	if float(t.get("sense_lock_s", 0.0)) > 0.0: attack.sense_lock_s = float(t.sense_lock_s)
	if float(t.get("soul_search_s", 0.0)) > 0.0: attack.soul_search_s = float(t.soul_search_s)
	if float(t.get("crit", 0.0)) > 0.0: attack.crit_bonus = float(t.crit)   # P13a: Metal's second verb
	# P13a the Buddhist path: an attack art held with a vow also shields its caster.
	if float(t.get("shield_hp_pct", 0.0)) > 0.0: raise_shield(c, c.pools.max_hp * float(t.shield_hp_pct), float(t.get("shield_s", 6)))
	if tier >= 3 and t.has("tier3"):
		var t3: Dictionary = t.tier3
		if t3.has("status"): attack.status = t3.status
		if t3.has("crit"): attack.crit_bonus = float(attack.get("crit_bonus", 0.0)) + float(t3.crit)
	# S48 sect role variants: the damage variant and the Edge branch strike harder; the Jade support variant slows.
	var sigv := ProgressionRules.signature_variant(c, str(t.id))
	var sig_extra := 0
	if not sigv.is_empty():
		var sm := 1.0 + float(sigv.get("mult", 0.0)) + ProgressionRules.sect_tree_flag(c, "signature_mult")
		attack.mult = [float(attack.mult[0]) * sm, float(attack.mult[1]) * sm]
		attack.penetration_bonus = float(attack.get("penetration_bonus", 0.0)) + float(sigv.get("penetration", 0.0))
		sig_extra = int(sigv.get("extra_targets", 0))
		if sigv.has("slow") and (attack.get("status", {}) as Dictionary).is_empty(): attack.status = sigv.slow
	# S48: the technique's grade (+0 / 10 / 20%).
	var gm := 1.0 + ProgressionRules.technique_grade_bonus(t)
	attack.mult = [float(attack.mult[0]) * gm, float(attack.mult[1]) * gm]
	# S48 combos: this technique within a second of its partner carries a follow-up.
	var combo := ProgressionRules.combo_for(str(tl.get("last_tech", "")), str(t.id), game.sim_time - float(tl.get("last_tech_t", -99.0)))
	tl.last_tech = str(t.id)
	tl.last_tech_t = game.sim_time
	var cfx: Dictionary = combo.get("effect", {})
	var extra_targets := sig_extra
	var reach_mult := float(ProgressionRules.path_flag(c, "reach_mult", 1.0))
	match str(cfx.get("kind", "")):
		"extra_target":
			extra_targets = int(cfx.get("value", 1))
			reach_mult *= float(cfx.get("range", 1.0))
		"stun", "root":
			var base_s: Dictionary = (attack.status as Dictionary).duplicate() if not (attack.status as Dictionary).is_empty() else {"id": str(cfx.kind), "power": 1}
			base_s.id = str(cfx.kind)
			base_s.chance = 1.0
			base_s.duration_s = float(base_s.get("duration_s", 0.6)) + float(cfx.get("bonus_s", 0.3))
			attack.status = base_s
	if not combo.is_empty():
		emit("combo_landed", {"actor": c.id, "combo": str(combo.id), "first": str(combo.first), "second": str(combo.second)})
	if t.has("projectile"):
		var pr: Dictionary = t.projectile
		var count := int(pr.get("count", 1)) + (1 if tier >= 3 and str(t.id) == "twin_reed_shot" else 0)
		for i in count:
			projectiles.spawn_projectile({"team": "player", "owner": c.id, "x": float(pv.x) + facing * 30, "y": float(pv.y) + (i - (count - 1) * 0.5) * 8.0,
				"alt": float(pv.alt) + 56 + i * 4, "dir": facing, "speed": float(pr.get("speed", 600)), "range": float(pr.get("range", 400)),
				"pierce": int(pr.get("pierce", 0)) + (1 if dtype == "qi" and StatRules.gate_flag(c, "projectile_pierce") else 0),   # S10 Essence 100
				"art": str(pr.get("art", "qi_" + str(t.get("element", "none")) if dtype == "qi" else "arrow")),
				"returning": pr.get("returning", false),
				"attack": attack, "delay": i * 0.08, "seek": pr.get("seek", false), "technique": str(t.id), "element": str(t.get("element", "none"))})
		emit("technique_used", {"actor": c.id, "technique": t.id, "hits": count, "targets": count})
		return
	var hitbox: Dictionary = (t.get("hitbox", {"x": [0, 80], "depth": 30, "alt": [-10, 80]}) as Dictionary).duplicate(true)
	if reach_mult != 1.0: hitbox.x = [float(hitbox.x[0]), float(hitbox.x[1]) * reach_mult]
	var targets := _form_targets(pv, t, hitbox, tl.get("at", Vector2.ZERO)) if grid() != null else _enemies_in(pv, facing, hitbox, t.get("both_sides", false))
	_nearest_first(targets, pv)
	var max_targets := int(t.get("max_targets", 1)) + extra_targets
	var n := 0
	var target_def := ""
	var struck: Array = []
	for e in targets:
		if n >= max_targets: break
		for h in maxi(1, int(t.get("hits", 1))):
			if not e.alive: break
			_player_hits_enemy(c, pv, e, attack, facing)
			hits_total += 1
		target_def = e.def_id
		struck.append(e)
		n += 1
	_combo_after(c, pv, facing, cfx, struck, attack, hitbox)
	emit("technique_used", {"actor": c.id, "technique": t.id, "hits": maxi(hits_total, 1), "targets": n, "target_def": target_def})

## S48 combo follow-ups that come after the blow: a shockwave, a pull, a fresh bleed.
func _combo_after(c, pv: Dictionary, facing: int, cfx: Dictionary, struck: Array, attack: Dictionary, hitbox: Dictionary) -> void:
	match str(cfx.get("kind", "")):
		"shockwave":
			var at := Vector2(float(pv.x), float(pv.y)) + aim_of(pv, facing) * float(hitbox.x[1])
			var wave := attack.duplicate()
			var wm := float(cfx.get("mult", 0.6))
			wave.mult = [float(attack.mult[0]) * wm, float(attack.mult[1]) * wm]
			wave.source = "combo"
			for e in _enemies_within(at, float(cfx.get("radius", 120))):
				_player_hits_enemy(c, pv, e, wave, 1 if e.plane.x >= at.x else -1)
		"pull":
			for e in struck:
				if e.alive and not e.def.get("knockback_immune", false) and not e.is_boss():
					if grid() != null:
						e.knock_dir = away(Vector2(float(pv.x), float(pv.y)), e.plane)
						e.knockback = -float(cfx.get("value", 90))
					else: e.knockback = -float(cfx.get("value", 90)) * facing
		"bleed":
			for e in struck:
				if e.alive: _apply_status_to_enemy(e, {"id": "bleed", "power": float(cfx.get("power", 0.02)), "remaining": float(cfx.get("duration_s", 4)), "source": c.id})

## Targets nearest first: along x in the side view, on the plane top-down.
func _nearest_first(targets: Array, pv: Dictionary) -> void:
	var o := Vector2(float(pv.x), float(pv.y))
	if grid() != null: targets.sort_custom(func(a, b): return a.plane.distance_to(o) < b.plane.distance_to(o))
	else: targets.sort_custom(func(a, b): return absf(a.plane.x - o.x) < absf(b.plane.x - o.x))

func _dao_tier(c, dao: String) -> int:
	return ProgressionRules.effective_dao_tier(c, dao)   # S10 Insight 100 counts one tier more from Explanation

## Redesign Phase 2: the foes inside a technique's form on the plane (TopdownAim: a line, a cone, a circle at its point
## or round the caster) whose feet are within the height band: the caster's, or the ground's at a point form's centre.
func _form_targets(pv: Dictionary, t: Dictionary, hitbox: Dictionary, at: Vector2) -> Array:
	var out: Array = []
	var form := TopdownAim.form_of(t)
	var o := Vector2(float(pv.x), float(pv.y))
	var base := grid().height_at(at) if form == "point" else float(pv.alt)
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden: continue
		if not TopdownAim.compatible(e.altitude + e.hover - base, form != "point" and airborne(str(pv.id))): continue
		if TopdownAim.contains(form, o, pv.aim, at, float(hitbox.x[1]), float(hitbox.get("depth", 30)), e.plane, e.half_width()): out.append(e)
	return out

func _enemies_in(pv: Dictionary, facing: int, hitbox: Dictionary, both_sides: bool) -> Array:
	var out: Array = []
	if game.room_rt == null: return out
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden: continue
		if hit_test(pv, facing, hitbox, enemy_view(e), both_sides): out.append(e)
	return out

func _enemies_within(at: Vector2, radius: float) -> Array:
	var out: Array = []
	if game.room_rt == null: return out
	for e in game.room_rt.living_enemies():
		if e.team == "enemy" and not e.hidden and e.plane.distance_to(at) <= radius: out.append(e)
	return out

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
	# S48 stances: Low Shadow finds the back, Still Draw rewards standing still.
	var back = ProgressionRules.path_flag(c, "backstab_crit", null)
	if back != null and e.facing == facing:
		pv = pv.duplicate()
		pv.crit_bonus = float(pv.get("crit_bonus", 0.0)) + float(back)
	var still = ProgressionRules.path_flag(c, "still_damage", null)
	var body: ActorState = game.actor_state(c.id)
	if still != null and body != null and body.velocity.length() < 5.0:
		attack = attack.duplicate()
		var sm := 1.0 + float(still)
		attack.mult = [float(attack.mult[0]) * sm, float(attack.mult[1]) * sm]
	# v1.2 the Confucian path's Righteous Qi: a quarter more against the Hollow and the demonic.
	if ProgressionAuthority.walks(c, "confucian") and _unrighteous(e):
		attack = attack.duplicate()
		attack.situation = float(attack.get("situation", 1.0)) * (1.0 + float(ContentDB.stat_const("paths", {}).get("confucian", {}).get("righteous", 0.25)))
	# S28: a stronger Presence bearing down on you takes away part of every blow.
	var dealt: float = float(attune.get(c.id, {}).get("dealt", 1.0)) * (1.0 - game.field.loss_of(c.id))
	if dealt != 1.0:
		attack = attack.duplicate()
		attack.attunement = float(attack.get("attunement", 1.0)) * dealt
	# S48 Sense Lock: a locked foe cannot evade. S10 Spirit 100: soul attacks ignore a fifth of Soul Defence.
	if e.pools.has_status("sense_locked") and not attack.get("never_miss", false):
		attack = attack.duplicate()
		attack.never_miss = true
	if str(attack.get("damage_type", "")) == "soul" and StatRules.gate_flag(c, "soul_ignore_20"):
		attack = attack.duplicate()
		attack.ignore_resistance = float(attack.get("ignore_resistance", 0.0)) + float(ContentDB.stat_const("gates", {}).get("soul_ignore", 0.2))
	timeline(c.id).fight_t = game.sim_time
	var r := CombatRules.resolve(pv, ev, attack, rng)
	if r.miss:
		emit("hit_missed", {"attacker": c.id, "target": str(e.uid), "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover + e.height()})
		return
	e.threat[c.id] = float(e.threat.get(c.id, 0.0)) + float(r.amount)
	var amount := float(r.amount)
	# S43 rule 11: a melee monster that has not been able to reach you for 2 s takes half damage from you.
	if float(e.ai.get("unreach", 0.0)) >= 2.0: amount *= 0.5
	# S48 Mercy (a vow): a foe that has turned to flee is never struck down; it gets away with its life.
	if e.ai.get("fled", false) and amount >= e.pools.hp and game.progression.vow_forbids(c, "fleeing_kill") != "":
		amount = maxf(0.0, e.pools.hp - 1.0)
	# Decision 43: a blow the chain goes on from knocks its foe back no further than the chain's next step reaches.
	if grid() != null and float(attack.get("knockback", 0.0)) > 0.0 and CombatFeel.chain_follows(timeline(c.id)):
		var keep := CombatFeel.follow_knock(float(StatRules.family(c).get("reach", 46)), Vector2(float(pv.x), float(pv.y)).distance_to(e.plane))
		if keep < float(attack.knockback):
			attack = attack.duplicate()
			attack.knockback = keep
	_damage_enemy(e, amount, c.id, r.type, r.element, r.crit, attack, facing, away(Vector2(float(pv.x), float(pv.y)), e.plane) if grid() != null else Vector2.ZERO)
	blood_path.lifesteal(c, amount, attack)
	sword.feed_intent(c, e, attack)
	if e.alive and not attack.get("status", {}).is_empty():
		var s: Dictionary = attack.status
		if not e.pools.steadfast.has(str(s.id)):
			var applied := CombatRules.status_roll(s, ev, rng)
			if not applied.is_empty():
				applied.source = c.id
				_apply_status_to_enemy(e, applied)
	if e.alive: riders.oil_strike(c, e, ev)
	if e.alive: riders.weapon_after_hit(c, e, attack)
	# Decision 38: the hit-stop by the blow's weight (CombatFeel: a light step 3 frames up to a finisher's 8, a crit 2 more),
	# within the action's cap (decision 43).
	_add_hitstop(timeline(c.id), CombatFeel.hitstop_s(CombatFeel.weight_of(attack, timeline(c.id)), r.crit))

## Another authority lays a status on a monster (S46 bloodline suppression: Fear).
func apply_enemy_status(e: EnemyState, s: Dictionary) -> void:
	if e == null or not e.alive or e.pools.steadfast.has(str(s.get("id", ""))): return
	_apply_status_to_enemy(e, s)

func _apply_status_to_enemy(e: EnemyState, s: Dictionary) -> void:
	for existing in e.pools.statuses:
		if existing.id == s.id:
			if float(s.power) >= float(existing.get("power", 0)): existing.merge(s, true)
			return
	e.pools.statuses.append(s)
	emit("status_applied", {"target": str(e.uid), "effect": s.id, "duration": s.remaining})

## `push`: on the top-down plane, the way a knockback drives it (away from the attacker); zero pushes along x by `facing`.
func _damage_enemy(e: EnemyState, amount: float, attacker: String, dtype: String, element: String, crit: bool, attack: Dictionary, facing := 0, push := Vector2.ZERO) -> void:
	if not e.alive or e.ai.get("surrendered", false): return   # a foe who has yielded is judged, not struck (S49)
	# S46 Beast Trial Grove: the keeper's own blows do no harm there; they rally the animals instead.
	if game.room_rt != null and game.room_rt.event.get("pet_trial", false) and game.room_rt.event.get("active", false) \
			and game.character(attacker) != null and not str(attack.get("source", "")).begins_with("ally:"):
		game.pets.rally(game.character(attacker))
		return
	if e.pools.has_status("freeze"):
		for s in e.pools.statuses.duplicate():
			if s.id == "freeze": e.pools.statuses.erase(s)
	# Decision 45: a foe that cannot be beaten yet (the awakened eel) keeps its HP over its floor, whatever strikes it:
	# a blow, a technique, a burn, a treasure. What its hide turns is told (`glance`), never taken.
	var hide := float(e.ai.get("hp_floor", 0.0)) * e.pools.max_hp
	var glance := hide > 0.0 and e.pools.hp - amount < hide
	if glance: amount = maxf(0.0, e.pools.hp - hide)
	e.pools.hp = maxf(0.0, e.pools.hp - amount)
	e.flash = 0.12
	if attacker.begins_with("c"): e.first_hit_by_player = true
	var kb := float(attack.get("knockback", 0.0))
	if kb != 0.0 and not e.def.get("knockback_immune", false) and not e.is_boss():   # P13a: below 0, a pull (Water, Space)
		e.knockback = kb * (facing if facing != 0 else 1)
		if push != Vector2.ZERO:
			e.knock_dir = push
			e.knockback = kb
	# Hit-stun (S30): a normal monster struck during its wind-up flinches, by the player's blow or an ally's (pets and
	# companions interrupt too), then shrugs off further interrupts for a moment so it can never be stun-locked.
	if e.role == "normal" and not e.def.get("steadfast", false) and str(e.ai.get("state", "")) == "windup" \
			and float(e.ai.get("stun_guard", 0.0)) <= 0.0:
		game.enemies.stagger(e, float(ContentDB.stat_const("combat.hit_stun_s", 0.35)))
		e.ai["stun_guard"] = float(ContentDB.stat_const("combat.hit_stun_guard_s", 1.6))
	emit("hit_landed", {"attacker": attacker, "target": str(e.uid), "target_kind": "enemy", "amount": int(amount), "type": dtype,
		"crit": crit, "element": element, "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover + e.height() * 0.8,
		"hp": e.pools.hp, "max": e.pools.max_hp, "source": str(attack.get("source", "")),
		"weight": CombatFeel.weight_of(attack, actors.get(attacker, {}), crit), "floor": e.altitude,
		"charge": float(attack.get("charge", 0.0)), "glance": glance})   # decision 45: a charged blow's ratio over one basic hit (0: not charged)
	if glance: return
	# S49: a named foe who yields at a fifth of their health waits on the victor's judgement (spare or kill).
	if e.def.get("surrenders", false) and e.pools.hp <= e.pools.max_hp * 0.2 and game.character(attacker) != null:
		e.pools.hp = maxf(1.0, e.pools.max_hp * 0.2)
		game.relations.apply_surrender(game.character(attacker), e)
		return
	# Spars end at 10% HP; nobody dies (S42).
	if e.def.get("spar", false) and e.pools.hp <= e.pools.max_hp * 0.1:
		e.pools.hp = e.pools.max_hp * 0.1
		game.enemies.end_spar(e, attacker)
		return
	# S46 taming fix: a tameable beast struck down while a taming offering sits on quick-use stays subdued at 1 HP for
	# 10 s instead of dying (once), so a one-hit beast can still be tamed.
	if e.pools.hp <= 0.0 and e.def.get("tameable", false) and not e.ai.get("subdued_once", false) and game.character(attacker) != null:
		var qc = game.character(attacker)
		# Decision 45: the offering in any of the three quick slots.
		if qc.inventory.quick.any(func(q): return str(ContentDB.item(str(q)).get("use_action", "")) == "tame" and qc.inventory.count(str(q)) > 0):
			var sub := float(ContentDB.config("taming").get("subdue_s", 10.0))
			e.pools.hp = 1.0
			e.ai["subdued_once"] = true
			game.enemies.stagger(e, sub)
			emit("beast_subdued", {"actor": qc.id, "enemy": e.uid, "def": e.def_id, "seconds": sub})
			return
	if e.pools.hp <= 0.0: _defeat(e, attacker)

# ------------------------------------------------------------------ a foe's end
## S49: the victor finishes a foe who yielded (Relations' judgement). The death is Combat's to announce.
func apply_execute(e: EnemyState, attacker: String) -> void:
	if not e.alive: return
	e.pools.hp = 0.0
	_defeat(e, attacker)

## Decision 45: a foe slain by the story, not by a blow (the elders' arts on the first boss: the scene's checkpoint, or
## the rescue that comes without one). Its hide and its shelter go with it; `killer` names who (not a character, so no
## Killing Intent and no boss moment of the player's), and its loot falls for the character as any kill's does.
func slay(e: EnemyState, killer: String) -> void:
	if e == null or not e.alive: return
	# The player it held down beaten gets up (EnemyAuthority._eel_overwhelm's stun), and what they used against it
	# while it could not be beaten (the teas drunk, the pill swallowed) is theirs again (EnemyAuthority._eel_awaken).
	var c = game.active()
	if str(e.ai.get("state", "")) == "looming" and c != null: cure_status(c.id, "stun")
	var bag: Dictionary = e.ai.get("bag", {})
	if c != null:
		for id in bag:
			var lost: int = int(bag[id]) - c.inventory.count(str(id))
			if lost > 0: game.inventory.apply_add(c.id, str(id), lost, "story:" + e.def_id)
	e.ai.erase("bag")
	e.ai.erase("hp_floor")
	e.ai.state = "slain"
	e.invulnerable = false
	e.pools.hp = 0.0
	_defeat(e, killer)

## The effect `slay_foe` (a staged scene's checkpoint): every living foe of `def` in the loaded room, slain by `killer`.
func apply_slay(def_id: String, killer: String) -> void:
	if game.room_rt == null: return
	for e in game.room_rt.living_enemies():
		if e.def_id == def_id and e.team == "enemy": slay(e, killer)

## Decision 45: the awakened eel's last blow, when the player has slipped every surge (the river rises over the bank):
## it cannot be dodged, guarded or shielded, and takes the player down to the fight's floor (`floor_k` of their most
## HP; never lower, and never back up), knocked back from the river.
func overwhelm(c, e: EnemyState, floor_k: float) -> void:
	if c == null or wounded.has(c.id): return
	var p: ResourcePool = c.pools
	var st: ActorState = game.actor_state(c.id)
	var amount := maxf(0.0, p.hp - p.max_hp * floor_k)
	p.hp -= amount
	p.since_hit = 0.0
	var tl := timeline(c.id)
	tl.fight_t = game.sim_time
	tl.flinch = float(ContentDB.stat_const("combat.flinch_s", 0.4))
	if st != null and e != null:
		tl.forced = away(e.plane, st.plane) * 90.0 / 0.18
		tl.forced_t = 0.18
	if grid() != null: hitstop = maxf(hitstop, CombatFeel.hitstop_s("heavy", false))
	emit("hit_landed", {"attacker": str(e.uid) if e != null else "", "target": c.id, "target_kind": "player", "amount": int(round(amount)), "type": "physical",
		"crit": false, "element": "hollow", "x": st.plane.x if st else 0.0, "y": st.plane.y if st else 0.0,
		"alt": (st.altitude if st else 0.0) + 92.0, "hp": p.hp, "max": p.max_hp, "pool": "hp", "weight": "heavy", "floor": st.altitude if st else 0.0})
	emit("resource_changed", {"actor": c.id, "pool": "hp", "value": p.hp, "max": p.max_hp})

## A foe falls to `attacker`: Enemies records the defeat, Combat announces it, and a kill feeds Killing Intent.
func _defeat(e: EnemyState, attacker: String) -> void:
	var payload: Dictionary = game.enemies.defeat(e, attacker)
	if not payload.is_empty(): emit("actor_defeated", payload)
	var killer = game.character(attacker)
	if killer != null: sword.gain_killing_intent(killer, e)

## S48 boss self-detonation: the blast, then the boss is gone (the fight is won and the loot still falls).
func resolve_boss_detonation(e: EnemyState) -> void:
	var d: Dictionary = e.ai.get("detonation", {})
	var c = game.active()
	if c != null: apply_detonation_blast(c, e, float(d.get("radius", 280)), float(d.get("damage", 0.6)))
	e.invulnerable = false
	e.pools.hp = 0.0
	var payload: Dictionary = game.enemies.defeat(e, c.id if c != null else "")
	if not payload.is_empty():
		payload.self_detonated = true
		emit("actor_defeated", payload)

## S48 boss self-detonation: the blast reaches the player inside its ring; a dodge slips it, a guard halves it.
func apply_detonation_blast(c, e: EnemyState, radius: float, share: float) -> void:
	var st: ActorState = game.actor_state(c.id)
	if st == null or st.plane.distance_to(e.plane) > radius: return
	var tl := timeline(c.id)
	if float(tl.dodge_t) > 0.0 or c.pools.invulnerable > 0.0:
		emit("hit_dodged", {"target": c.id, "attacker": str(e.uid)})
		return
	var dmg: float = c.pools.max_hp * share * (0.5 if tl.guard else 1.0)
	_damage_player(c, dmg, str(e.uid), "qi", {"damage_type": "qi", "element": "none", "mult": [1.0, 1.0], "range": [1.0, 1.0], "knockback": 160.0}, false, e)

# ------------------------------------------------------------------ foes' blows and harm to the player
## Enemy strikes (called by EnemyAuthority at the hit moment of a melee attack).
func enemy_strike(e: EnemyState, attack: Dictionary) -> void:
	var c = game.active()
	if c == null or wounded.has(c.id): return
	var pv := player_view(c)
	var ev := enemy_view(e)
	var hitbox: Dictionary = attack.get("hitbox", {"x": [0, 40], "depth": 26, "alt": [-30, 60]})
	if hit_test(ev, e.facing, hitbox, pv, attack.get("both_sides", false)):
		_enemy_hits_player(e, c, ev, pv, attack)
	phantom.strike_decoy(e, ev, hitbox, attack)
	_enemy_hits_allies(e, attack, ev)
	# v1.2 Phase D: some blows leave the ground burning where they land (the Ashborn's cinders, Kharn's pyre).
	var gf: Dictionary = attack.get("ground_fire", {})
	if not gf.is_empty():
		var reach := float(gf.get("at", (hitbox.get("x", [0, 40]) as Array)[1]))
		var spots: Array = gf.get("ring", [])
		if spots.is_empty(): spots = [reach * e.facing]
		for dx in spots:
			# Along x in the side view; on the height grid along the blow's aim on the plane, on the foe's floor.
			var fp := e.plane + (e.aim_dir() * float(dx) * float(e.facing) if grid() != null else Vector2(float(dx), 0.0))
			ground_fires.append({"x": fp.x, "y": fp.y, "alt": e.altitude, "r": float(gf.get("radius", 70)), "t": float(gf.get("duration_s", 5.0)),
				"tick": 0.5, "pct": float(gf.get("pct_per_s", 0.03)), "source": str(e.uid)})
		emit("ground_fire", {"x": e.plane.x, "y": e.plane.y, "count": spots.size(), "duration": float(gf.get("duration_s", 5.0))})

## v1.2 Phase D: burning patches on the ground. Standing in one (not flying, not high above it) burns a share of max HP
## each half second; a dodge or invulnerability passes through it.
var ground_fires: Array = []

func _tick_ground_fires(delta: float) -> void:
	if ground_fires.is_empty(): return
	var c = game.active()
	var st: ActorState = game.actor_state(c.id) if c != null else null
	for f in ground_fires.duplicate():
		f.t = float(f.t) - delta
		if float(f.t) <= 0.0:
			ground_fires.erase(f)
			continue
		f.tick = float(f.tick) - delta
		if float(f.tick) > 0.0: continue
		f.tick = 0.5
		if st == null or st.flying: continue
		# Above it: the side view's 40 over the ground; on the height grid off the fire's own floor (a level up or down).
		if (st.altitude > 40.0 if grid() == null else absf(st.altitude - float(f.get("alt", 0.0))) > TopdownRoom.LEVEL * 0.5): continue
		if Vector2(float(f.x), float(f.y)).distance_to(st.plane) > float(f.r): continue
		apply_hazard_damage(c, c.pools.max_hp * float(f.pct) * 0.5, "dot", "fire", "ground_fire")

## The same strike lands on companions and spirit animals inside its hitbox.
func _enemy_hits_allies(e: EnemyState, attack: Dictionary, ev: Dictionary) -> void:
	if game.room_rt == null: return
	var hitbox: Dictionary = attack.get("hitbox", {"x": [0, 40], "depth": 26, "alt": [-30, 60]})
	for a in game.room_rt.enemies.values():
		if a.team != "ally" or not a.alive or a.ai.state == "downed" or a.hidden: continue
		# On the height grid the blow's band reads the ally's real height: a foe on the square does not reach a pet on
		# the terrace (the side view measures its altitude window from the ground).
		var view := {"x": a.plane.x, "y": a.plane.y, "alt": a.altitude + a.hover if grid() != null else 0.0, "half_width": a.half_width(), "height": a.height()}
		if not CombatAuthority.hit_test(ev, e.facing, hitbox, view, attack.get("both_sides", false)): continue
		var companion: bool = game.companions.is_companion_ally(a)
		var dmg := maxf(1.0, float(e.stats.attack) * float(attack.get("mult", 1.0)) * 0.8 * (1.0 - FieldAuthority.enemy_loss(e)))
		# P12: a foe's attack is set to pass its Level's armour, so an ally (health a share of its owner's) stands behind
		# its owner's armour, as its owner would.
		var owner = game.character(a.pet_owner)
		if owner != null: dmg *= 1.0 - CombatRules.defence_reduction(owner.stats.value("physical_defense"), e.level, 0.0, float(e.stats.get("might", 1.0)))
		if not companion: dmg *= game.pets.damage_taken_mult(a)
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
	# S46 Guardian Spirit: an animal beside you takes one blow meant for you every 30 s.
	if game.pets.guardian_absorbs(c):
		emit("hit_dodged", {"target": c.id, "attacker": str(e.uid), "guardian": true})
		return
	# Parry: a guard begun within the family's parry window before the hit negates it. An `unblockable` blow (the
	# awakened eel's, decision 45) passes a guard and a parry alike; only a dodge slips it.
	var fam := StatRules.family(c)
	var unblockable: bool = attack.get("unblockable", false)
	var frontal := signf(float(pv.x) - e.plane.x) != float(tl.facing) or absf(float(pv.x) - e.plane.x) < 4
	if pv.has("aim"): frontal = (e.plane - Vector2(float(pv.x), float(pv.y))).dot(pv.aim) >= 0.0   # facing the foe on the plane
	if unblockable: frontal = false
	if tl.guard and frontal and float(tl.guard_t) <= float(fam.get("parry_s", 0.18)) and Unlocks.is_unlocked(c.id, "guard"):
		var stagger := float(ContentDB.stat_const("combat.parry_stagger_boss_s" if e.is_boss() else "combat.parry_stagger_s", 0.8))
		game.enemies.stagger(e, stagger)
		emit("parried", {"actor": c.id, "attacker": str(e.uid), "x": pv.x, "y": pv.y})
		# Willow Leaf Parry: the technique's 2 s window, or the jian's stance held (S48), turns a parry into a counter.
		var counter = ProgressionRules.path_flag(c, "parry_counter", null)
		if float(tl.stance) > 0.0 or counter != null:
			var cm: float = float(counter) if counter != null else 2.0
			_player_hits_enemy(c, pv, e, {"damage_type": "physical", "element": "wood", "mult": [cm, cm], "range": [1.0, 1.0], "source": "counter"}, int(tl.facing))
		return
	# S47: a boss's telegraphed "shatter" blow that lands breaks a natal weapon in hand (guarding does not save it).
	if attack.get("shatter", false): game.inventory.natal_break(c, "shatter")
	var m := float(attack.get("mult", 1.0)) * float(e.ai.get("enraged", {}).get("damage", 1.0)) * (1.0 - FieldAuthority.enemy_loss(e))
	var a := {"damage_type": str(attack.get("damage_type", "physical")), "element": e.element, "mult": [m, m],
		"range": [0.9, 1.1], "knockback": float(attack.get("knockback", 0)), "pull": float(attack.get("pull", 0)),
		"attunement": float(attune.get(c.id, {}).get("taken", 1.0))}
	var guard_pv := pv.duplicate()
	if not (tl.guard and frontal): guard_pv.guarding = 0.0
	var r := CombatRules.resolve(ev, guard_pv, a, Rng.stream(c.id, "combat"))
	# A blow measured against the body itself (`hp_share`, the awakened eel's): that share of the player's most HP, whatever
	# they wear or their evasion; it never misses.
	if attack.has("hp_share"):
		r.miss = false
		r.crit = false
		r.amount = c.pools.max_hp * float(attack.hp_share)
	if r.miss:
		emit("hit_missed", {"attacker": str(e.uid), "target": c.id, "x": pv.x, "y": pv.y, "alt": float(pv.alt) + 90})
		return
	_damage_player(c, float(r.amount), str(e.uid), r.type, a, r.crit, e)
	if attack.has("status") and not attack.status.is_empty():
		var applied := CombatRules.status_roll(attack.status, pv, Rng.stream(c.id, "combat"))
		# S10 Spirit 50: fear and confusion from a weaker foe slide off.
		if not applied.is_empty() and str(applied.id) in ["fear", "confusion"] and StatRules.gate_flag(c, "fear_immune_weaker") and e.level < ProgressionRules.level(c):
			applied = {}
		if not applied.is_empty(): apply_status(c.id, str(applied.id), float(applied.remaining), float(applied.power))
	if float(e.def.get("hollowing", 0)) > 0: apply_resource_change(c.id, "hollowing", float(e.def.hollowing), "hollow")
	if float(attack.get("drain", 0)) > 0: e.pools.hp = minf(e.pools.max_hp, e.pools.hp + r.amount * float(attack.drain))

## S48 heavenly tribulation: one bolt lands where its ring was drawn. Cover does not help (roofs, shelter), a step
## out of the ring does, guarding halves it, and a Lightning Rod Talisman in the bag takes it whole and burns away.
## A bolt that would kill leaves the body at a tenth of its HP and reports `lethal`: the breakthrough fails.
func apply_tribulation_strike(c, at: Vector2, radius: float, depth: float) -> Dictionary:
	var st: ActorState = game.actor_state(c.id)
	var here: Vector2 = st.plane if st else at
	# The ring on the ground: the side view's flattened strip (radius across, depth deep); on the height grid, where the
	# ground is seen whole, a circle of the radius.
	if grid() != null:
		if here.distance_to(at) > radius: return {"hit": false}
	elif absf(here.x - at.x) > radius or absf(here.y - at.y) > depth: return {"hit": false}
	if c.inventory.count("lightning_rod_talisman") > 0:
		game.inventory.apply_remove(c.id, "lightning_rod_talisman", 1, "tribulation")
		return {"hit": true, "absorbed": true, "damage": 0.0}
	var tl := timeline(c.id)
	var cu = c.cultivator
	var dmg := ProgressionRules.tribulation_damage(c.pools.max_hp, int(c.relations.sin), float(cu.heart_demon), bool(tl.guard))
	var p: ResourcePool = c.pools
	var lethal := p.hp - dmg <= 0.0
	p.set_value("hp", p.max_hp * float(ContentDB.config("tribulations").get("survive_hp", 0.1)) if lethal else p.hp - dmg)
	p.since_hit = 0.0
	tl.flinch = float(ContentDB.stat_const("combat.flinch_s", 0.4))
	emit("hit_landed", {"attacker": "heaven", "target": c.id, "target_kind": "player", "amount": int(round(dmg)), "type": "qi", "crit": false,
		"element": "thunder", "x": here.x, "y": here.y, "alt": (st.altitude if st else 0.0) + 92.0, "hp": p.hp, "max": p.max_hp, "pool": "hp"})
	emit("resource_changed", {"actor": c.id, "pool": "hp", "value": p.hp, "max": p.max_hp})
	return {"hit": true, "absorbed": false, "damage": dmg, "lethal": lethal}

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
	if attacker != "" and dtype != "dot": timeline(c.id).fight_t = game.sim_time
	var ub := StatRules.set_flag(c, "unbroken")
	if not ub.is_empty() and dtype not in ["dot", "soul"] and p.cooldown("unbroken") <= 0.0 \
			and p.hp - maxf(0.0, amount - p.shield) < p.max_hp * float(ub.get("below", 0.3)):
		p.cooldowns["unbroken"] = float(ub.get("cooldown_s", 60))
		raise_shield(c, p.max_hp * float(ub.get("shield", 0.1)), float(ub.get("shield_s", 5)))
	if p.shield > 0.0:
		var absorbed := minf(p.shield, amount)
		p.shield -= absorbed
		amount -= absorbed
	var pool := "soul" if dtype == "soul" and p.max_soul > 0 else "hp"
	# Decision 45: while a foe that cannot be beaten is awake (the first boss), nothing takes the player under its floor;
	# a blow that reaches it ends that fight (the player overwhelmed, the elders' rescue), never the player.
	var floor_k: float = game.enemies.hold_floor(c) if pool == "hp" else -1.0
	var floored := false
	if floor_k >= 0.0 and p.hp - amount <= p.max_hp * floor_k:
		amount = maxf(0.0, p.hp - p.max_hp * floor_k)
		floored = true
	var before := p.get_value(pool)
	p.set_value(pool, before - amount)
	if floored: game.enemies.floor_reached(c)
	p.since_hit = 0.0
	var tl := timeline(c.id)
	var kb := float(attack.get("knockback", 0)) * (1.0 - clampf(c.stats.value("knockback_resistance"), 0.0, 0.9))   # S48 Iron Body, Body
	if ProgressionRules.path_flag(c, "knockback_immune", false): kb = 0.0   # Iron Horse
	if amount >= p.max_hp * float(ContentDB.stat_const("combat.flinch_pct", 0.2)) or kb >= 60:
		tl.flinch = float(ContentDB.stat_const("combat.flinch_s", 0.4))
		if kb > 0 and e != null and not (StatRules.gate_flag(c, "knockback_immune_attacking") and is_busy(c.id)):
			tl.forced = away(e.plane, game.actor_state(c.id).plane) * kb / 0.18 if game.actor_state(c.id) else Vector2.ZERO
			tl.forced_t = 0.18
	# v1.2 the Gravity Golem's well: a blow that drags the body toward the one who struck it (into the slam).
	var pull := float(attack.get("pull", 0)) * (1.0 - clampf(c.stats.value("knockback_resistance"), 0.0, 0.9))
	if pull > 0.0 and e != null and game.actor_state(c.id) != null and not ProgressionRules.path_flag(c, "knockback_immune", false):
		tl.forced = away(game.actor_state(c.id).plane, e.plane) * pull / 0.25
		tl.forced_t = 0.25
	var st: ActorState = game.actor_state(c.id)
	if spar.has(c.id) and p.hp <= p.max_hp * 0.1:
		p.hp = p.max_hp * 0.1
		game.enemies.player_lost_spar()
		return
	# Decision 38: a foe's blow weighs by its role, heavy when it takes a big share; on the grid it holds the fight too.
	var w := CombatFeel.foe_weight(e, amount / maxf(1.0, p.max_hp)) if e != null else "light"
	if e != null and grid() != null: hitstop = maxf(hitstop, CombatFeel.hitstop_s(w, crit))
	emit("hit_landed", {"attacker": attacker, "target": c.id, "target_kind": "player", "amount": int(round(amount)), "type": dtype,
		"crit": crit, "element": str(attack.get("element", "none")), "x": st.plane.x if st else 0.0, "y": st.plane.y if st else 0.0,
		"alt": (st.altitude if st else 0.0) + 92.0, "hp": p.hp, "max": p.max_hp, "pool": pool, "weight": w, "floor": st.altitude if st else 0.0})
	emit("resource_changed", {"actor": c.id, "pool": pool, "value": p.get_value(pool), "max": p.get_max(pool)})
	# Lotus Heart Breathing (secret art, Spirit Awakening 5): below 30% HP the breath turns inward and
	# heals 2% a second for 5 s, once a minute.
	if pool == "hp" and p.hp > 0.0 and p.hp < p.max_hp * 0.3 and "lotus_heart_breathing" in c.cultivator.secret_arts and p.cooldown("lotus_heart") <= 0.0:
		p.cooldowns["lotus_heart"] = 60.0
		heals.apply_heal(c.id, 0.10, 0.0, 5.0, "lotus_heart_breathing")
		emit("system_used", {"actor": c.id, "system": "lotus_heart_breathing"})
	if p.get_value(pool) <= 0.0:
		if StatRules.gate_flag(c, "survive_lethal") and not tl.get("survived_lethal", false):
			tl.survived_lethal = true
			p.set_value(pool, 1.0)
			return
		if spar.has(c.id):
			p.set_value(pool, 1.0)
			return
		revival.gravely_wound(c, "soul" if pool == "soul" else "hp")

# ------------------------------------------------------------------ apply_* commands
## The public command other authorities use to change a pool (Part 2).
func apply_resource_change(actor_id: String, pool: String, amount: float, source: String, pct := 0.0, quiet := false) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var p: ResourcePool = c.pools
	if pct != 0.0: amount += p.get_max(pool) * pct
	if pool == "hollowing" and amount > 0:
		amount *= 1.0 - clampf(c.stats.value("hollow_ward"), 0.0, 0.8)
		p.set_value(pool, minf(hollow_cap(), p.get_value(pool) + amount))
		# S48 Hollow-Touched (v1.2): wholly Hollowed and still standing.
		if p.hollowing >= float(ContentDB.stat_const("hollowing.seizure_at", 100)) and p.hp > 0.0:
			game.progression.awaken_physique(c.id, "hollow_touched")
			_hollow_seizure(c)
	else:
		p.set_value(pool, p.get_value(pool) + amount)
	if not quiet: emit("resource_changed", {"actor": c.id, "pool": pool, "value": p.get_value(pool), "max": p.get_max(pool), "source": source})

## S28 · How far the Hollowing can fill here: under half in the valley and the Expanse, all the way in the Lantern Star Field.
func hollow_cap() -> float:
	var h: Dictionary = ContentDB.stat_const("hollowing", {})
	var zone := str(ContentDB.zone_of_room(game.room_rt.room_id).get("id", "")) if game.room_rt else ""
	return float(h.get("zone_caps", {}).get(zone, h.get("valley_cap", 49)))

## S28 · At half, the Hollowing is a burden: techniques cost more and Composure drains.
static func hollow_burdened(c) -> bool:
	return c.pools.hollowing >= float(ContentDB.stat_const("hollowing.burden_at", 50))

## S28 · At full, the Tide takes the body for a moment (no moving, striking or casting), the allies beside you turn
## on you for a while, and the meter falls back to 80.
func _hollow_seizure(c) -> void:
	var h: Dictionary = ContentDB.stat_const("hollowing", {})
	apply_status(c.id, "hollow_seizure", float(h.get("seizure_s", 3.0)), 1.0)
	var turned := 0
	if game.room_rt:
		for e in game.room_rt.living_enemies():
			if e.team != "ally": continue
			e.team = "enemy"
			e.ai["turned"] = float(h.get("turn_s", 10.0))
			turned += 1
	c.pools.set_value("hollowing", float(h.get("after_seizure", 80)))
	emit("hollow_seizure", {"actor": c.id, "turned": turned})

## A shield that takes blows until its time is up (Iron Wall, Soul Lantern Ward, Guarding Cloud, Unbroken).
func raise_shield(c, amount: float, seconds: float) -> void:
	c.pools.shield = maxf(c.pools.shield, amount)
	var fx: Dictionary = treasure_fx.get(c.id, {})
	fx["shield_t"] = seconds
	treasure_fx[c.id] = fx

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
	if status_id == "qi_seal" and StatRules.body_flag(c, "qi_seal_immune"): return   # S48 Gold Body
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

## A Hollow or demonic foe (Righteous Qi bites deeper): Hollowed or demonic by nature, or carrying the Hollowing.
static func _unrighteous(e: EnemyState) -> bool:
	return str(e.def.get("nature", "")) in ["demonic", "hollowed"] or str(e.def.get("element", "")).begins_with("hollow") \
		or float(e.def.get("hollowing", 0.0)) > 0.0 or str(e.def.get("race", "")) in ["hollow", "demon"]

## v1.2 the Sphere's pulse: a cut, a burn or a shock of `mult` times the bearer's Qi attack that cannot miss.
func sphere_strike(c, e: EnemyState, element: String, mult: float, kind: String) -> void:
	if c == null or not e.alive or e.invulnerable: return
	var pv := player_view(c)
	var attack := {"damage_type": "qi", "element": element, "mult": [mult, mult], "range": [0.95, 1.05], "never_miss": true,
		"source": "sphere:" + kind, "sphere_kind": kind}
	_player_hits_enemy(c, pv, e, attack, 1 if e.plane.x >= pv.get("x", e.plane.x) else -1)

## v1.2 the Copperjaw swarm's bite: `mult` times the bearer's Qi attack as Metal, which cannot miss.
func swarm_strike(c, e: EnemyState, mult: float) -> void:
	if c == null or not e.alive or e.invulnerable: return
	var pv := player_view(c)
	_player_hits_enemy(c, pv, e, {"damage_type": "qi", "element": "metal", "mult": [mult, mult], "range": [0.95, 1.05], "never_miss": true,
		"source": "swarm"}, 1 if e.plane.x >= float(pv.get("x", e.plane.x)) else -1)

## A pet or companion strike (AllyBrain) credits its owner.
func ally_hits_enemy(a: EnemyState, e: EnemyState, attack_power: float) -> void:
	var owner := a.pet_owner
	var c = game.character(owner)
	if c == null or not e.alive or e.invulnerable: return
	var view := {"level": a.level, "realm_index": ProgressionRules.realm_index(c.cultivator.realm_key), "element": "none",
		"physical_attack": attack_power * (1.0 + (float(ContentDB.stat_const("sphere.pet_bonus", 0.1)) if Unlocks.is_unlocked(owner, "sphere") else 0.0)),
		"accuracy": c.stats.value("accuracy"), "crit_chance": 0.05, "crit_damage": 1.5,   # v1.2: a small Sphere for the pets of a Sphere Lord
		"might": StatRules.might(c)}   # P12: an ally strikes with its owner's Might against armour
	var r := CombatRules.resolve(view, enemy_view(e), {"damage_type": "physical", "mult": [1.0, 1.0], "range": [0.85, 1.15]}, Rng.stream(owner, "pet"))
	if r.miss:
		emit("hit_missed", {"attacker": str(a.uid), "target": str(e.uid), "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.hover + e.height()})
		return
	e.threat[owner] = float(e.threat.get(owner, 0.0)) + float(r.amount)
	_damage_enemy(e, float(r.amount), owner, "physical", "none", r.crit, {"source": "ally:" + str(a.uid)}, a.facing)

func begin_spar(actor_id: String) -> void:
	spar[actor_id] = true

## A spar is over, won or lost: nobody is hurt by it, and the player is made whole.
func end_spar(actor_id: String) -> void:
	spar.erase(actor_id)
	var c = game.character(actor_id)
	if c != null: apply_resource_change(actor_id, "hp", c.pools.max_hp, "spar")

# ------------------------------------------------------------------ the parts' faces
# Every public method that moved into a part, and the private ones that tests and tools call by name (S11 renames
# those), forwarded under the names they always had. The authority's own flow and the parts call a part directly.

# Flight and the movement arts (combat_flight.gd).
func start_flight(c) -> Dictionary: return flight.start_flight(c)
func stop_flight(actor_id: String, reason: String) -> void: flight.stop_flight(actor_id, reason)
func flight_allowed(actor_id: String) -> bool: return flight.flight_allowed(actor_id)
func is_flying(actor_id: String) -> bool: return flight.is_flying(actor_id)
func vessel_qi_mult(c) -> float: return flight.vessel_qi_mult(c)
func air_qi_mult(c) -> float: return flight.air_qi_mult(c)
func knows_art(c, art: String) -> bool: return flight.knows_art(c, art)
func plunge(c) -> Dictionary: return flight.plunge(c)
func glide(c, on: bool) -> Dictionary: return flight.glide(c, on)
func is_gliding(actor_id: String) -> bool: return flight.is_gliding(actor_id)

# Phantom Double (combat_phantom.gd).
func _cast_illusion(c, t: Dictionary) -> void: phantom.cast_illusion(c, t)
func decoy_for(e: EnemyState, actor_id: String) -> Dictionary: return phantom.decoy_for(e, actor_id)
func _strike_decoy(e: EnemyState, ev: Dictionary, hitbox: Dictionary, attack: Dictionary) -> void: phantom.strike_decoy(e, ev, hitbox, attack)

# The flying sword, Sword Intent and Killing Intent (combat_sword.gd).
func natal_demand(inst: Dictionary) -> float: return sword.natal_demand(inst)
func knows_sword_release(c) -> bool: return sword.knows_sword_release(c)
func toggle_sword_release(c) -> Dictionary: return sword.toggle_sword_release(c)
func _tick_sword(c, delta: float) -> void: sword.tick_sword(c, delta)
func _feed_intent(c, e: EnemyState, attack: Dictionary) -> void: sword.feed_intent(c, e, attack)
func intent_penetration(c) -> float: return sword.intent_penetration(c)
func _gain_killing_intent(c, victim: EnemyState) -> void: sword.gain_killing_intent(c, victim)
func killing_intent_stacks(actor_id: String) -> int: return sword.killing_intent_stacks(actor_id)

# The sword swarm (combat_swarm.gd).
func swarm_count(c, with_treasure: bool) -> int: return swarm.swarm_count(c, with_treasure)
func toggle_sword_swarm(c, t: Dictionary) -> Dictionary: return swarm.toggle_sword_swarm(c, t)
func start_swarm(c, from_treasure: bool, secs: float) -> Dictionary: return swarm.start_swarm(c, from_treasure, secs)
func swarm_of(actor_id: String) -> int: return swarm.swarm_of(actor_id)
func _end_swarm(c, why: String) -> void: swarm.end_swarm(c, why)

# The flute's melody (combat_flute.gd).
func channel_melody(c, on: bool) -> Dictionary: return flute.channel_melody(c, on)
func is_playing(actor_id: String) -> bool: return flute.is_playing(actor_id)

# Heals (combat_heals.gd).
func apply_heal(actor_id: String, pct: float, amount: float, over_s: float, source: String) -> void: heals.apply_heal(actor_id, pct, amount, over_s, source)
static func heal_total(c, pct: float, amount: float) -> float: return CombatHeals.heal_total(c, pct, amount)
func hots_of(actor_id: String) -> Array: return heals.hots_of(actor_id)
func heal_circle(c, pct: float, seconds: float, radius: float, source: String) -> int: return heals.heal_circle(c, pct, seconds, radius, source)
func sect_support_mult(c) -> float: return heals.sect_support_mult(c)
func _sect_support(c, v: Dictionary) -> void: heals.sect_support(c, v)

# The Blood path (combat_blood_path.gd).
func blood_lifesteal(c) -> float: return blood_path.blood_lifesteal(c)
func _lifesteal(c, amount: float, attack: Dictionary) -> void: blood_path.lifesteal(c, amount, attack)
func essence_of(actor_id: String) -> float: return blood_path.essence_of(actor_id)
func _feed_blood_essence(p: Dictionary) -> void: blood_path.feed_blood_essence(p)

# Array Plates (combat_plates.gd) and talismans (combat_talismans.gd).
func deploy_array(actor_id: String, e: Dictionary) -> void: plates.deploy_array(actor_id, e)
func use_talisman(c, index: int) -> Dictionary: return talismans.use_talisman(c, index)

# Projectiles (combat_projectiles.gd).
func _spawn_projectile(p: Dictionary) -> void: projectiles.spawn_projectile(p)
func spawn_enemy_projectile(e: EnemyState, attack: Dictionary) -> void: projectiles.spawn_enemy_projectile(e, attack)
func _tick_projectiles(delta: float) -> void: projectiles.tick_projectiles(delta)

# Treasures and throwables (combat_treasures.gd).
static func treasure_of(item_id: String) -> Dictionary: return CombatTreasures.treasure_of(item_id)
static func treasure_soul_cost(c, t: Dictionary) -> float: return CombatTreasures.treasure_soul_cost(c, t)
func use_treasure(c, slot: int) -> Dictionary: return treasures.use_treasure(c, slot)
func self_detonate(c, index: int, confirm: bool) -> Dictionary: return treasures.self_detonate(c, index, confirm)
func _tick_treasures(c, delta: float) -> void: treasures.tick_treasures(c, delta)
func apply_throw(actor_id: String, e: Dictionary) -> void: treasures.apply_throw(actor_id, e)
func _burst(c, p: Dictionary, first: EnemyState) -> void: treasures.burst(c, p, first)

# Grave wounds and revival (combat_revival.gd).
func _gravely_wound(c, cause: String) -> void: revival.gravely_wound(c, cause)
func revive_here_allowed(c) -> Dictionary: return revival.revive_here_allowed(c)
func fruit_revival_allowed(c) -> Dictionary: return revival.fruit_revival_allowed(c)
func choose_revival(c, where: String) -> Dictionary: return revival.choose_revival(c, where)

# What a landed blow carries after its damage (combat_riders.gd).
func _weapon_after_hit(c, e: EnemyState, attack: Dictionary) -> void: riders.weapon_after_hit(c, e, attack)
func poison_body_active(c) -> bool: return riders.poison_body_active(c)
func poison_body_threshold(c) -> float: return riders.poison_body_threshold(c)
func _poison_body(c, e: EnemyState) -> void: riders.poison_body(c, e)
func _oil_strike(c, e: EnemyState, ev: Dictionary) -> void: riders.oil_strike(c, e, ev)
