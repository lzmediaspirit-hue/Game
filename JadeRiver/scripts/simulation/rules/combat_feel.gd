class_name CombatFeel
extends RefCounted
## Decision 38 · the combat feel of the top-down world, read from one table (data/combat_feel.json, built by
## tools/data/combat_feel.py). Only the feel and technique come from the reference game (timing, hit-stop, smears,
## impact readability, camera kick, knockback); the look stays wuxia (the FX sheets of data/fx_topdown.json).
##
## A blow has a weight (light, medium, heavy, finisher) that sets its hit-stop, the camera's kick and shake, its impact
## mark and the hop its knockback gives. A combo step has three phases derived from its family's own timing
## (weapon_families.json): anticipation up to one smear frame before the hit, the active window of the smear's bright
## frames, and the recovery; a dodge cancels the anticipation or the late recovery, never the active window.
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

## The top-down pose of a technique's form (combat_feel.json `forms`): an action of the character's catalogue, a
## `combo_N` being the wielded family's step N.
static func form_pose(t: Dictionary, fam: Dictionary) -> String:
	var p := str(cfg().get("forms", {}).get(str(t.get("vfx", {}).get("anim", t.get("form", ""))), {}).get("pose", "cast"))
	if not p.begins_with("combo_"): return p
	var combo: Array = fam.get("combo", [])
	if combo.is_empty(): return "cast"
	return str(combo[clampi(int(p.trim_prefix("combo_")) - 1, 0, combo.size() - 1)].action)

## The lunge toward the target a combo step carries (world units), longer for a dash attack.
static func lunge(fam_id: String, index: int, dash := false) -> float:
	var l: Array = family(fam_id).get("lunge", [0])
	var v := float(l[clampi(index, 0, l.size() - 1)]) if not l.is_empty() else 0.0
	return v * 2.0 + 16.0 if dash else v
