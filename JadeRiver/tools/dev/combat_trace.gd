extends Node
## Decision 43 · the combat feel, frame by frame. Real chains played through the top-down world's own loop at 60 fps
## (the hit-stop's hold, the body's step, Game.tick, the events, the figure's sync), the presses sent as the HUD sends
## them (Attack's tap, a technique's tap, Dodge, the stick), against sturdy foes in the prototype square, on the tool's
## own saves. Each frame is logged (the presses, the hit-stop, the action, its phase and clock, the combo and what waits
## to follow it, the figure's pose, frame and row, the facing, the body's speed, the target's distance and HP), and each
## chain is summed up: the frames from each press to its action, the dead frames (a press waiting while nothing plays),
## the hit-stop's frames and the presses kept through it, the facing's turns (how far the aim ends from the foe the
## stick points at, the rows skipped in one frame), the pull toward the foe at each step and the distance after each
## knockback against the reach, and the frames from a dodge or a sprint pressed out of a chain to the body leaving.
##   godot --headless --path . res://tools/dev/combat_trace.tscn -- [--out=/abs/dir] [--tag=before]
## Writes <out>/<tag>_<chain>_<family>.csv and <out>/<tag>_summary.json (out defaults to user://combat_trace/).

const SAVES := "user://combat_trace_saves/"
const DT := 1.0 / 60.0
## Each chain: [name, family, frames, presses, the art in slot 0 (optional)]; a press is [frame, kind, arg]: "attack",
## "tech" (slot), "dodge", "stick" (a Vector2 held from that frame), "attack_in_stop" (Attack the first frame a
## hit-stop holds), "tech_in_stop".
const CHAINS := [
	["weave", "fists", 100, [[0, "attack"], [16, "attack"], [32, "tech", 0], [50, "attack"], [66, "attack"]]],
	["weave_knock", "fists", 110, [[0, "attack"], [30, "tech", 0], [60, "attack"], [76, "attack"]], "mole_cuts"],
	["weave", "jian", 110, [[0, "attack"], [18, "attack"], [36, "tech", 0], [56, "attack"], [74, "attack"]]],
	["mash", "fists", 90, [[0, "attack"], [6, "attack"], [12, "attack"], [18, "attack"], [24, "attack"], [30, "attack"], [36, "attack"]]],
	["late_taps", "jian", 110, [[0, "attack"], [40, "attack"], [80, "attack"]]],
	["in_stop", "jian", 90, [[0, "attack"], [1, "attack_in_stop"], [40, "tech_in_stop"]]],
	["turn", "fists", 80, [[0, "attack"], [8, "stick", Vector2(0, 1)], [12, "attack"], [30, "stick", Vector2.ZERO], [32, "attack"]]],
	["dodge_out", "jian", 70, [[0, "attack"], [18, "attack"], [30, "stick", Vector2(-1, 0)], [30, "dodge"]]],
	["dodge_heavy", "heavy_sabre", 70, [[0, "attack"], [23, "stick", Vector2(-1, 0)], [23, "dodge"]]],
	["sprint_out", "jian", 80, [[0, "attack"], [18, "attack"], [30, "stick", Vector2(-1, 0)]]],
	["sprint_out", "fists", 70, [[0, "attack"], [14, "attack"], [24, "stick", Vector2(-1, 0)]]],
	["knock", "fists", 110, [[0, "attack"], [16, "attack"], [32, "attack"], [60, "attack"]]],
	["knock", "jian", 120, [[0, "attack"], [18, "attack"], [36, "attack"], [70, "attack"]]],
]
const WEAPON := {"fists": "", "jian": "training_jian", "heavy_sabre": "training_heavy_sabre"}

var w
var c
var out_dir := "user://combat_trace/"
var tag := "trace"
var summary := {}

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--out="): out_dir = str(a).trim_prefix("--out=").trim_suffix("/") + "/"
		if str(a).begins_with("--tag="): tag = str(a).trim_prefix("--tag=")
	DirAccess.make_dir_recursive_absolute(SAVES)
	for f in DirAccess.get_files_at(SAVES): DirAccess.remove_absolute(SAVES + f)
	DirAccess.make_dir_recursive_absolute(out_dir if out_dir.begins_with("user://") else out_dir)
	Saves.use_folder(SAVES)
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 43
	Rng.restore("account", {}, 43)
	Game.submit({"type": "create_character", "slot": 1, "name": "Trace", "appearance": {"hair": "topknot", "shirt": "disciple"}, "skip_prologue": true})
	Game.submit({"type": "enter_character", "slot": 1})
	c = Game.active()
	Unlocks.debug_force_all = true
	w = TopdownWorld.new()
	w.sim_frozen = true
	add_child(w)
	await get_tree().process_frame
	c.cultivator.realm_key = "bone_forging_7"
	for tid in ["flowing_palm", "cloudpiercing_stroke"]:
		if not c.cultivator.techniques_known.has(tid): c.cultivator.techniques_known.append(tid)
	for ch in CHAINS: _chain(ch)
	var f := FileAccess.open(out_dir + tag + "_summary.json", FileAccess.WRITE)
	if f != null: f.store_string(JSON.stringify(summary, "  ", false))
	print("combat_trace: %s" % JSON.stringify(_totals()))
	get_tree().quit(0)

## The kit for `fam`: its weapon in hand and its first technique in slot 0 (the free hand's palm, the jian's cut).
func _kit(fam: String) -> void:
	var wid: String = WEAPON[fam]
	c.inventory.equipped["weapon"] = null
	if wid != "":
		Game.inventory.apply_add(c.id, wid, 1, "trace")
		Game.submit({"type": "equip", "index": c.inventory.first_index(wid)})
	c.cultivator.technique_slots[0] = "cloudpiercing_stroke" if fam == "jian" else "flowing_palm"
	Game.combat.refresh_stats(c.id)

func _fresh(at: Vector2) -> void:
	var rt: RoomRuntime = Game.room_rt
	rt.enemies.clear()
	rt.spawn_slots.clear()
	rt.loot.clear()
	rt.projectiles.clear()
	var p = w.player
	p.motor.place(at)
	p.motor.dir = Vector2.RIGHT
	p.motor.row = "e"
	p.motor.dash_t = 0.0
	p.motor.since_dash = 99.0
	p.motor.dash_cd = 0.0
	p.dodge_buffer = 0.0
	p.weave = {}
	p.movement = Vector2.ZERO
	p.physics_step(0.0001)
	c.pools.hp = c.pools.max_hp
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.clear()
	for sid in ["spawn_protection", "stun", "slow", "root"]: Game.combat.cure_status(c.id, sid)
	Game.combat.wounded.erase(c.id)
	Game.combat.actors.erase(c.id)
	Game.combat.hitstop = 0.0

## A foe that lives through anything and neither walks nor strikes back (held by a long stun; its flinch and
## knockback still play).
func _sturdy(p: Vector2) -> EnemyState:
	var e: EnemyState = Game.enemies.spawn_at("wild_boarlet", p, 1)
	e.altitude = w.room.height_at(p)
	e.pools.max_hp = 1.0e15
	e.pools.hp = e.pools.max_hp
	e.ai.state = "idle"
	e.ai.timer = 99.0
	e.pools.statuses.append({"id": "stun", "remaining": 9999.0, "power": 1.0})
	return e

## One frame as TopdownWorld runs it: the hit-stop's hold, else the body's step and Game.tick; then the events and the
## figure's sync.
func _frame() -> bool:
	var held := false
	if CombatFeel.hitstop_on() and Game.combat.hold_for_hitstop(DT): held = true
	else:
		for e in w.player.physics_step(DT): w.feedback(e)
		Game.tick(DT)
	w.held = held
	GameEvents.flush()
	w.player.sync(DT)
	return held

func _chain(ch: Array) -> void:
	var name := str(ch[0])
	var fam := str(ch[1])
	var n := int(ch[2])
	var presses: Array = ch[3]
	_kit(fam)
	if ch.size() > 4:
		if not c.cultivator.techniques_known.has(str(ch[4])): c.cultivator.techniques_known.append(str(ch[4]))
		c.cultivator.technique_slots[0] = str(ch[4])
	var base := Vector2(22.5, 19.5) * 32.0
	_fresh(base)
	var reach := float(StatRules.family(c).get("reach", 46))
	var foe := _sturdy(base + Vector2(minf(reach * 0.7, 40.0), 0))
	var side: EnemyState = null
	if name == "turn": side = _sturdy(base + Vector2(0, 44))
	for e in Game.room_rt.enemies.values(): e.ai.timer = 99.0
	var p = w.player
	var tl: Dictionary = Game.combat.timeline(c.id)
	var rows: Array = []
	var stick := Vector2.ZERO
	var pending_stop: Array = []   # presses waiting for the next held frame
	var prev_action := ""
	var prev_t := 0.0
	var starts: Array = []         # [frame, action, combo, technique, aim angle]
	var press_log: Array = []      # [frame, kind]
	var held_frames := 0
	var kept_in_stop := 0
	var sent_in_stop := 0
	var dead := 0
	var hit_d: Array = []          # the target's distance at each hit and once its knockback has run
	var last_hp: float = foe.pools.hp
	var knock_watch := -1
	var row_jumps := 0
	var prev_row: String = p.motor.row
	var leave := {"press": -1, "dash": -1, "fast": -1, "run": -1, "pos": Vector2.ZERO}
	var pulls: Array = []
	var hs_frames := 0
	for f in n:
		var sent := ""
		for pr in presses:
			if int(pr[0]) != f: continue
			match str(pr[1]):
				"attack":
					p.attack()
					sent += "A"
					press_log.append([f, "attack"])
				"tech":
					var r: Dictionary = p.use_technique(int(pr[2]))
					sent += "T" if r.get("ok", false) or not p.weave.is_empty() else "T!"
					press_log.append([f, "tech"])
				"dodge":
					p.dodge()
					sent += "D"
					leave.press = f
					leave.pos = p.motor.pos
				"stick":
					stick = pr[2]
					sent += "S"
					if name == "sprint_out" and stick != Vector2.ZERO:
						leave.press = f
						leave.pos = p.motor.pos
				"attack_in_stop", "tech_in_stop": pending_stop.append(str(pr[1]))
		p.movement = stick
		var in_stop: bool = Game.combat.hitstop > 0.0
		if in_stop and not pending_stop.is_empty():
			for k in pending_stop:
				sent_in_stop += 1
				if k == "attack_in_stop":
					var q0 := int(tl.get("queued", 0))
					p.attack()
					if int(tl.get("queued", 0)) > q0 or not p.weave.is_empty(): kept_in_stop += 1
					sent += "a"
					press_log.append([f, "attack"])
				else:
					var r: Dictionary = p.use_technique(0)
					if r.get("ok", false) or not p.weave.is_empty(): kept_in_stop += 1
					sent += "t"
					press_log.append([f, "tech"])
			pending_stop.clear()
		var held := _frame()
		if held: hs_frames += 1
		# A new action: the timeline's clock went back, or it began from rest.
		var act := str(tl.action)
		var began: bool = act != "" and (prev_action == "" or float(tl.t) < prev_t - 0.0001)
		if began:
			var aim: Vector2 = tl.get("aim", Vector2.RIGHT)
			starts.append([f, act, int(tl.combo), str(tl.technique), snappedf(rad_to_deg(aim.angle()), 0.1),
				snappedf(rad_to_deg((side.plane - p.motor.pos).angle()), 0.1) if side != null else 0.0])
			pulls.append({"f": f, "from": p.motor.pos, "d0": p.motor.pos.distance_to(foe.plane)})
		# Dead frames: a press waits (queued in Combat, in the weave buffer or the dodge buffer) while nothing plays.
		var waiting: bool = int(tl.get("queued", 0)) > 0 or not p.weave.is_empty() or p.dodge_buffer > 0.0
		if waiting and not Game.combat.is_busy(c.id) and not held: dead += 1
		if foe.pools.hp < last_hp:
			hit_d.append({"f": f, "at_hit": snappedf(p.motor.pos.distance_to(foe.plane), 0.1)})
			knock_watch = 20
		last_hp = foe.pools.hp
		if knock_watch > 0:
			knock_watch -= 1
			if knock_watch == 0 and not hit_d.is_empty(): hit_d[hit_d.size() - 1].after = snappedf(p.motor.pos.distance_to(foe.plane), 0.1)
		if p.motor.row != prev_row:
			if _row_steps(prev_row, p.motor.row) > 1: row_jumps += 1
			prev_row = p.motor.row
		if int(leave.press) >= 0:
			if int(leave.dash) < 0 and p.motor.dash_t > 0.0: leave.dash = f - int(leave.press)
			if int(leave.fast) < 0 and p.motor.vel.length() >= p.motor.sprint * 0.5 and p.motor.dash_t <= 0.0 and p.motor.push_t <= 0.0 \
					and not Game.combat.is_busy(c.id): leave.fast = f - int(leave.press)
			if int(leave.run) < 0 and p.anim in ["run", "walk", "dash", "dodge"]: leave.run = f - int(leave.press)
		for pl in pulls:
			if int(pl.f) + 8 == f: pl.pulled = snappedf(float(pl.d0) - p.motor.pos.distance_to(foe.plane), 0.1)
		rows.append([f, sent, int(held), snappedf(Game.combat.hitstop / DT, 0.1), act, str(tl.technique), CombatFeel.phase_of(tl, c) if act != "" else "",
			snappedf(float(tl.t), 0.001), int(tl.combo), int(tl.get("queued", 0)), str(p.weave.get("kind", "")), snappedf(p.dodge_buffer, 0.01),
			p.anim, p.pose, p.frame, p.motor.row, snappedf(rad_to_deg(p.motor.dir.angle()), 0.1), snappedf(p.motor.vel.length(), 0.1),
			snappedf(p.motor.pos.x, 0.1), snappedf(p.motor.pos.y, 0.1), snappedf(p.motor.pos.distance_to(foe.plane), 0.1), int(tl.get("window", 0.0) > 0.0)])
		prev_action = act
		prev_t = float(tl.t)
	p.movement = Vector2.ZERO
	# Press to action: each press's frame to the first action that began at or after it.
	var lat: Array = []
	var si := 0
	for pr in press_log:
		while si < starts.size() and int(starts[si][0]) < int(pr[0]): si += 1
		if si < starts.size():
			lat.append(int(starts[si][0]) - int(pr[0]))
			si += 1
		else: lat.append(-1)
	# The gaps between one action's end and the next's start, among the actions that followed a press.
	var gaps: Array = []
	for i in range(1, starts.size()):
		var gap := 0
		for fr in range(int(starts[i - 1][0]), int(starts[i][0])):
			var row: Array = rows[fr]
			if str(row[4]) == "" and int(row[2]) == 0: gap += 1
		gaps.append(gap)
	var turn := {}
	if side != null:
		# The step struck after the stick turned toward the second foe: how far its aim is from that foe, as seen from
		# where the body stood as the step began.
		for s in starts:
			if int(s[0]) >= 12:
				var want := float(s[5])
				turn = {"step_frame": int(s[0]), "aim": float(s[4]), "want": want, "off_deg": snappedf(absf(angle_difference(deg_to_rad(float(s[4])), deg_to_rad(want))) * 180.0 / PI, 0.1)}
				break
	var key := "%s_%s" % [name, fam]
	summary[key] = {"starts": starts, "press_to_action": lat, "gaps": gaps, "dead_frames": dead, "hitstop_frames": hs_frames,
		"sent_in_stop": sent_in_stop, "kept_in_stop": kept_in_stop, "row_jumps": row_jumps, "turn": turn, "hits": hit_d,
		"reach": reach, "pulls": pulls.map(func(pl): return pl.get("pulled", 0.0)), "leave": {"press": leave.press, "dash_f": leave.dash, "half_sprint_f": leave.fast, "moving_pose_f": leave.run},
		"total_frames": n}
	var csv := FileAccess.open(out_dir + "%s_%s.csv" % [tag, key], FileAccess.WRITE)
	if csv != null:
		csv.store_line("f,press,held,hitstop_f,action,technique,phase,t,combo,queued,weave,dodge_buf,anim,pose,frame,row,dir_deg,speed,x,y,foe_d,window")
		for r in rows: csv.store_line(",".join(r.map(func(v): return str(v))))
	print("%s: starts %s | press->action %s | gaps %s | dead %d | hit-stop %d f (in-stop presses kept %d/%d) | row jumps %d | turn %s | hits %s | reach %.0f | pulls %s | leave %s"
		% [key, str(starts.map(func(s): return "%d:%s%s" % [s[0], s[1] if str(s[3]) == "" else "T", "" if int(s[2]) < 0 else str(s[2])])), str(lat), str(gaps), dead, hs_frames,
			kept_in_stop, sent_in_stop, row_jumps, str(turn), str(hit_d), reach, str(summary[key].pulls), str(summary[key].leave)])

## Rows apart on the eight drawn rows (the shortest way round).
func _row_steps(a: String, b: String) -> int:
	var order := ["e", "se", "s", "sw", "w", "nw", "n", "ne"]
	var d := absi(order.find(a) - order.find(b))
	return mini(d, 8 - d)

func _totals() -> Dictionary:
	var dead := 0
	var gaps := 0
	var jumps := 0
	for k in summary:
		dead += int(summary[k].dead_frames)
		for g in summary[k].gaps: gaps += int(g)
		jumps += int(summary[k].row_jumps)
	return {"chains": summary.size(), "dead_frames": dead, "gap_frames": gaps, "row_jumps": jumps}
