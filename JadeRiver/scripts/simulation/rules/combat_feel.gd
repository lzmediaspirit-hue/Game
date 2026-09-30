class_name CombatFeel
extends RefCounted
## Decision 38 · the combat feel of the top-down world, read from one table (data/combat_feel.json, built by
## tools/data/combat_feel.py). Only the feel and technique come from the reference game (timing, hit-stop, smears,
## impact readability, camera kick, knockback); the look stays wuxia (the FX sheets of data/fx_topdown.json).
##
## A blow has a weight (light, medium, heavy, finisher) that sets its hit-stop, the camera's kick and shake, its impact
## mark and the hop its knockback gives. A combo step has three phases derived from its family's own timing
## (weapon_families.json): anticipation up to one smear frame before the hit, the active window of the smear's bright
## frames, and the recovery; a dodge cancels the anticipation or the late recovery, never the active window. Decision 42
## weaves them: a technique cuts a basic step's recovery and a basic attack a technique's, once the blow has landed
## (`weave`). Decision 43 smooths the chain (`flow`): the presses go in their order, one action's hit-stop has a cap,
## each step pulls toward its foe, and a blow the chain goes on from leaves its foe in the next step's reach.
## Settings: under Reduce motion there is no hit-stop; the kick and shake follow Screen shake and Reduce motion
## (MomentRules.shake_amp).

static func cfg() -> Dictionary:
	return ContentDB.config("combat_feel")

static func weight(name: String) -> Dictionary:
	var w: Dictionary = cfg().get("weights", {})
	return w.get(name, w.get("medium", {}))

## A weight moved `by` steps along light, medium, heavy, finisher (a crit is one heavier).
static func heavier(name: String, by := 1) -> String:
	var order: Array = cfg().get("order", ["light", "medium", "heavy", "finisher"])
	return str(order[clampi(order.find(name) + by, 0, order.size() - 1)])

## Hit-stop for a blow of weight `w` (a crit holds a couple of frames more).
static func hitstop_s(w: String, crit := false) -> float:
	var f := int(weight(w).get("hitstop_f", 4)) + (int(cfg().get("crit_hitstop_f", 2)) if crit else 0)
	return f * float(cfg().get("frame_s", 1.0 / 60.0))

## No hit-stop under Reduce motion (decision 38).
static func hitstop_on() -> bool:
	return not (Game.account != null and bool(Game.account.settings.get("reduce_motion", false)))

static func family(fam_id: String) -> Dictionary:
	return cfg().get("families", {}).get(fam_id, cfg().get("families", {}).get("fists", {}))

## Decision 45 · the charged attack (combat_feel.json `charge`): {full_s, full} for a weapon family, the seconds of charge
## that fill it and its ratio over one basic hit when full.
static func charge_of(fam_id: String) -> Dictionary:
	var ch: Dictionary = cfg().get("charge", {})
	var row: Array = ch.get("families", {}).get(fam_id, [ch.get("full_s", 0.5), ch.get("full", 2.3)])
	return {"full_s": float(row[0]), "full": float(row[1])}

## How far a charge of `charge_s` seconds has filled, 0..1.
static func charge_k(fam_id: String, charge_s: float) -> float:
	return clampf(charge_s / maxf(0.01, float(charge_of(fam_id).full_s)), 0.0, 1.0)

## The charged blow's damage over one basic hit (the family's first step) after `charge_s` seconds: from the plain
## finisher's (its last step's mult over its first's; 1 for a one-step family) up to the family's full ratio in a
## straight line, held there once full.
static func charge_ratio(fam: Dictionary, charge_s: float) -> float:
	var combo: Array = fam.get("combo", [])
	if combo.is_empty(): return 1.0
	var start := float(combo[-1].get("mult", 1.0)) / maxf(0.01, float(combo[0].get("mult", 1.0)))
	var full := maxf(start, float(charge_of(str(fam.get("id", "fists"))).full))
	return lerpf(start, full, charge_k(str(fam.get("id", "fists")), charge_s))

## The charged blow's own multiplier: the first step's times charge_ratio.
static func charged_mult(fam: Dictionary, charge_s: float) -> float:
	var combo: Array = fam.get("combo", [])
	return (float(combo[0].get("mult", 1.0)) if not combo.is_empty() else 1.0) * charge_ratio(fam, charge_s)

## A combo step's weight: the family's for that step, `finisher` for a dragged (charged) finisher.
static func step_weight(fam_id: String, index: int, charged := false) -> String:
	var f := family(fam_id)
	if charged: return str(f.get("charged", "finisher"))
	var steps: Array = f.get("steps", ["light"])
	return str(steps[clampi(index, 0, steps.size() - 1)])

## The weight of a player's blow from its attack and the striker's timeline: a basic step's, a technique's form, a
## counter or the Plunge heavy, anything else medium; a crit one heavier.
static func weight_of(attack: Dictionary, tl: Dictionary, crit := false) -> String:
	var src := str(attack.get("source", ""))
	var w := "medium"
	if src == "basic": w = step_weight(str(tl.get("family", "fists")), int(tl.get("combo", 0)), bool(tl.get("charged", false)))
	elif src.begins_with("tech:"):
		var t := ContentDB.entry("techniques", src.trim_prefix("tech:"))
		w = str(cfg().get("forms", {}).get(str(t.get("form", t.get("vfx", {}).get("anim", ""))), {}).get("weight", "medium"))
	elif src in ["counter", "plunge"]: w = "heavy"
	return heavier(w) if crit else w

## A foe's blow on the player: by the foe's role, heavy when it takes a big share of the health.
static func foe_weight(e: EnemyState, share := 0.0) -> String:
	var f: Dictionary = cfg().get("foes", {})
	if share >= float(f.get("big_hit_share", 0.15)): return str(f.get("big_hit", "heavy"))
	var role := "boss" if e != null and e.is_boss() else ("elite" if e != null and (e.elite or e.role == "elite") else "normal")
	return str(f.get("roles", {}).get(role, "light"))

## The lead of a family's smear (its first frame, before the hit) and its active window (its three bright frames), at
## the family's smear rate, scaled like the step by the attack speed.
static func smear_fps(fam_id: String) -> float:
	return float(family(fam_id).get("smear_fps", 20))

## The phases of combo step `index` of weapon family `fam` (its weapon_families.json entry) at attack speed `speed`:
## {anticipation, active, recovery, duration, hit_at, cancel_from} in seconds; `cancel_from` is when in the recovery a
## dodge may cancel it (the finisher, or a dragged one, later).
static func phases(fam: Dictionary, index: int, speed := 1.0, finisher := false) -> Dictionary:
	var combo: Array = fam.get("combo", [])
	if combo.is_empty(): return {}
	var step: Dictionary = combo[clampi(index, 0, combo.size() - 1)]
	var f := family(str(fam.get("id", "fists")))
	var fps := smear_fps(str(fam.get("id", "fists"))) * speed
	var dur := float(step.duration) / speed
	var hit := float(step.hit_at) / speed
	var lead := 1.0 / fps
	var active := 3.0 / fps
	var antic := hit - lead
	var rec := dur - antic - active
	var last := finisher or index >= combo.size() - 1
	var share := float(f.get("finisher_after", 0.6)) if last else float(f.get("recovery_after", 0.3))
	return {"anticipation": antic, "active": active, "recovery": rec, "duration": dur, "hit_at": hit, "lead": lead,
		"cancel_from": antic + active + maxf(0.0, rec) * share}

## A technique's phases: its wind-up, its active window, the quarter second after (CombatAuthority's timeline).
static func technique_phases(t: Dictionary) -> Dictionary:
	var antic := float(t.get("windup_s", 0.2))
	var active := float(t.get("active_s", 0.2))
	var rec := 0.25
	return {"anticipation": antic, "active": active, "recovery": rec, "duration": antic + active + rec, "hit_at": antic,
		"cancel_from": antic + active + rec * float(cfg().get("technique_recovery_after", 0.3))}

## The phase a timeline is in: "" when idle, else anticipation, active or recovery.
static func phase_of(tl: Dictionary, c = null) -> String:
	var ph := timeline_phases(tl, c)
	if ph.is_empty() or str(tl.get("action", "")) == "" or float(tl.t) >= float(tl.duration): return ""
	var t := float(tl.t)
	if t < float(ph.anticipation): return "anticipation"
	if t < float(ph.anticipation) + float(ph.active): return "active"
	return "recovery"

static func timeline_phases(tl: Dictionary, c = null) -> Dictionary:
	if str(tl.get("action", "")) == "": return {}
	if str(tl.get("technique", "")) != "": return technique_phases(ContentDB.entry("techniques", str(tl.technique)))
	var fam := ContentDB.entry("weapon_families", str(tl.get("family", "fists")))
	var speed: float = 1.0 + (float(c.stats.value("attack_speed")) if c != null else 0.0)
	return phases(fam, int(tl.get("combo", 0)), speed, bool(tl.get("charged", false)))

## What a dodge does to a blow under way (decision 38's cancel rule): "free" when nothing is under way, "cancel" in the
## anticipation (the blow is dropped) or once the recovery's cancel point has passed, "committed" otherwise.
static func dodge_cancel(tl: Dictionary, c = null) -> String:
	var phase := phase_of(tl, c)
	if phase == "": return "free"
	if phase == "anticipation": return "cancel"
	if phase == "recovery" and float(tl.t) >= float(timeline_phases(tl, c).get("cancel_from", 0.0)): return "cancel"
	return "committed"

## Decision 42 · animation canceling (combat_feel.json `weave`).
static func weave_cfg() -> Dictionary:
	return cfg().get("weave", {})

## When in the blow under way a press of `kind` ("technique" or "basic") may cut it: the start of its recovery (the end
## of its active frames, after its hit) plus `<kind>_after` of the recovery; INF when nothing is under way.
static func weave_from(tl: Dictionary, kind: String, c = null) -> float:
	var ph := timeline_phases(tl, c)
	if ph.is_empty(): return INF
	var share := clampf(float(weave_cfg().get("technique_after" if kind == "technique" else "basic_after", 0.0)), 0.0, 1.0)
	return float(ph.anticipation) + float(ph.active) + maxf(0.0, float(ph.recovery)) * share

## What a press of `kind` does to the action under way (decision 42, the weave of basic attacks and techniques):
##   "free"   nothing is under way;
##   "cancel" a technique during a basic step, or a basic attack during a technique, once that blow has landed and its
##            recovery has run to its cut (weave_from): it ends there and the press begins at once;
##   "wait"   before that (the anticipation, the active window), or a technique during a technique: the press waits in
##            the player's buffer (`buffer_s`) and goes when the answer changes;
##   "chain"  a basic attack during a basic step: the combo's own queue (the next step after this one).
static func weave(tl: Dictionary, kind: String, c = null) -> String:
	var phase := phase_of(tl, c)
	if phase == "": return "free"
	var basic_now := str(tl.get("technique", "")) == ""
	if kind == "basic" and basic_now: return "chain"
	if kind == "technique" and not basic_now: return "wait"
	# Decision 43: a technique goes after a basic step already queued (the presses in their order).
	if kind == "technique" and waits_ahead(tl): return "wait"
	if phase != "recovery" or not bool(tl.get("hit_done", false)): return "wait"
	return "cancel" if float(tl.t) >= weave_from(tl, kind, c) - 0.0001 else "wait"

## Decision 43 · the chain's flow (combat_feel.json `flow`).
static func flow() -> Dictionary:
	return cfg().get("flow", {})

## A basic step (or a dragged finisher) waits queued behind the blow under way: a press after it goes after it.
static func waits_ahead(tl: Dictionary) -> bool:
	return bool(flow().get("in_order", true)) and str(tl.get("technique", "")) == "" \
		and (int(tl.get("queued", 0)) > 0 or not (tl.get("finisher_q", {}) as Dictionary).is_empty())

## The most hit-stop one action adds in all, seconds.
static func hitstop_cap_s() -> float:
	return float(flow().get("hitstop_cap_f", 10)) * float(cfg().get("frame_s", 1.0 / 60.0))

## A lunge toward a foe `d` units off (the step's own lunge `own`, the weapon's `reach`): the step's own lunge, or
## further to come within `stand` of the reach of a foe farther off (by `extra` at most), never closer to it than `near`
## of the reach (and `gap`, the two bodies); no foe (d < 0): the step's own lunge.
static func pull(own: float, reach: float, d: float) -> float:
	if d < 0.0: return own
	var p: Dictionary = flow().get("pull", {})
	var most := own + float(p.get("extra", 24))
	var want := clampf(d - reach * float(p.get("stand", 0.5)), own, most)
	var closest := maxf(float(p.get("gap", 16)), reach * float(p.get("near", 0.4)))
	return clampf(minf(want, d - closest), 0.0, most)

## Does the chain go on from the blow under way: a basic step before the combo's last (not a dragged finisher), or a
## technique woven into a chain whose next step is not past the last.
static func chain_follows(tl: Dictionary) -> bool:
	if str(tl.get("action", "")) == "": return false
	var size: int = (ContentDB.entry("weapon_families", str(tl.get("family", "fists"))).get("combo", []) as Array).size()
	if str(tl.get("technique", "")) != "": return int(tl.get("chain", -1)) >= 0 and int(tl.chain) < size - 1
	return not bool(tl.get("charged", false)) and int(tl.get("combo", -1)) >= 0 and int(tl.combo) < size - 1

## The knockback a blow the chain goes on from may give a foe `d` units off: the rest of `keep_reach` of the weapon's
## `reach`, at least `min_knock`.
static func follow_knock(reach: float, d: float) -> float:
	var f := flow()
	return maxf(float(f.get("min_knock", 8)), reach * float(f.get("keep_reach", 0.75)) - d)

## The top-down pose of a technique's form (combat_feel.json `forms`): an action of the character's catalogue, a
## `combo_N` being the wielded family's step N.
static func form_pose(t: Dictionary, fam: Dictionary) -> String:
	var p := str(cfg().get("forms", {}).get(str(t.get("vfx", {}).get("anim", t.get("form", ""))), {}).get("pose", "cast"))
	if not p.begins_with("combo_"): return p
	var combo: Array = fam.get("combo", [])
	if combo.is_empty(): return "cast"
	return str(combo[clampi(int(p.trim_prefix("combo_")) - 1, 0, combo.size() - 1)].action)

## The top-down pose family `fam_id` plays (an action of the character's catalogue, or a side-view name that
## TopdownFigure.resolve maps): for a `move` (dash, air, throw, charge, parry, melody) the family's own pose for it, else
## the move's (`moves`); else the family's own pose for the side-view `action` its step or technique names (the heavy
## sabre's two-handed cuts, the bell's toll, the brush writing, the flute at the lips, the bow's draw), else the action.
static func top_pose(fam_id: String, action: String, move := "") -> String:
	var own: Dictionary = cfg().get("families", {}).get(fam_id, {}).get("poses", {})
	if move != "":
		if own.has(move): return str(own[move])
		var mv: Dictionary = cfg().get("moves", {})
		if mv.has(move): return str(mv[move])
	return str(own.get(action, action))

## The frames the flute's held melody loops through, [first, last] (its note on the second).
static func melody_loop() -> Array:
	return cfg().get("melody_loop", [1, 4])

## The weapon family that wears a weapon look (parts.json weapon; weapon_families.json `appearance`), fists for none.
static func family_of_look(look: String) -> String:
	if look == "" or look == "none": return "fists"
	for f in ContentDB.all("weapon_families"):
		if look in (f.get("appearance", []) as Array): return str(f.id)
	return "fists"

## The lunge toward the target a combo step carries (world units), longer for a dash attack.
static func lunge(fam_id: String, index: int, dash := false) -> float:
	var l: Array = family(fam_id).get("lunge", [0])
	var v := float(l[clampi(index, 0, l.size() - 1)]) if not l.is_empty() else 0.0
	return v * 2.0 + 16.0 if dash else v
