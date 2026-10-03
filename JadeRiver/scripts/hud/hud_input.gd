class_name HudInput
extends HudPart
## A finger on the play screen (the keys are the HUD's own _input): what a touch lands on, the aiming gestures of Attack
## and the techniques, the pet wheel, the holds, and the technique page's scroll.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

func role_at(p: Vector2) -> String:
	# The equip prompt's two buttons (clear of every control; the rest of its card lets a tap through).
	var prompt := hud.equip_prompt.role_at(p) if hud.bound() else ""
	if prompt != "": return prompt
	# Where round controls overlap, the nearest centre wins (§7).
	var best := ""
	var best_d := INF
	for tg in hud.layout.hit_targets():
		var d := p.distance_to(tg.center)
		if d < float(tg.r) and d < best_d:
			best = str(tg.role)
			best_d = d
	if best != "": return best
	if hud.minimap_rect.has_point(p) and hud.shown("minimap"): return "minimap"
	var panel := hud.layout.panel_rect(Game.active())
	if panel.has_point(p) and hud.shown("player_panel"): return "portrait"
	var go := ""
	var go_d := INF
	for tp in hud.tracker_paths:
		if (tp.rect as Rect2).has_point(p) and hud.shown("quest_tracker") and p.distance_to((tp.rect as Rect2).get_center()) < go_d:
			go = "path:" + str(tp.target)
			go_d = p.distance_to((tp.rect as Rect2).get_center())
	if go != "": return go
	if hud.tracker_rect.has_point(p) and hud.shown("quest_tracker"): return "tracker"
	if Rect2(0, 704, 1280, 16).has_point(p) and hud.shown("progress_bar"): return "progress"
	if (p.x < 640) != hud.left_handed: return "joystick"
	return "none"

func press(id: int, p: Vector2):
	var role := role_at(p)
	hud.touches[id] = {"role": role, "start": p, "swiped": false}
	# Top-down redesign, Phase 2 (decision 30): Attack and the techniques aim. A touch is read as a tap (on release) or,
	# held or dragged, as an aim (AimGesture); the world shows the aim on the ground while the thumb is down.
	if aims() and (role == "attack" or role == "skill"):
		hud.touches[id]["gesture"] = AimGesture.new(role, hud.attack_center if role == "attack" else _nearest_slot_center(p))
		if role == "attack": return
	match role:
		"joystick":
			if hud.joystick_id == -999:
				hud.joystick_id = id
				hud.joystick_origin = p
				hud.joystick_pos = p
				hud.player.joystick_engaged = true
		"attack": primary()
		"jump":
			hud.player.jump()
			hud.player.jump_held = true   # S43: held while falling it glides, or from Cloud Stride 1 flies
			hud.player.fly_up = true      # held Jump climbs while flying
		"meditate":
			if hud.bound():
				hud.cultivate_pressed = true
				hud.cultivate_hold = 0.0
			else:
				hud.player.meditate()
		"skill":
			# The nearest drawn slot of the page (ring 1's circles overlap; the nearest centre wins, and an empty slot is
			# not there to win).
			var near_i := -1
			for i in hud.slots.size():
				if hud.layout.slot_filled(i + hud.skill_page * 4) and (near_i < 0 or p.distance_to(hud.slots[i]) < p.distance_to(hud.slots[near_i])): near_i = i
			if near_i >= 0: hud.touches[id]["slot"] = near_i + hud.skill_page * 4
		"page": scroll_skills(-1)
		"fan": toggle_fan()
		"guard":
			if hud.player.state.flying: hud.player.fly_down = true   # held Evade descends while flying; a tap dashes (S43)
			hud.guard_pressed = true
			hud.guard_hold = 0.0
		"quick:0", "quick:1", "quick:2": hud.actions.use_quick(int(role.right(1)))
		"draught": hud.actions.drink_draught()
		"sense":
			if hud.bound():
				var sr := Game.submit({"type": "sense_pulse"})
				if not sr.ok and sr.has("text"): hud.add_log(str(sr.text), UiKit.MIST)
		"presence": hud.actions.toggle_presence()
		"sphere": hud.actions.toggle_sphere()
		"pet":
			if hud.bound():
				hud.pet_pressed = true
				hud.pet_hold = 0.0
				hud.pet_wheel = false
		"context": hud.actions.use_context()
		"post": hud.actions.keep_post()
		"treasure:0", "treasure:1": hud.actions.use_treasure(int(role.get_slice(":", 1)))
		"swap": hud.actions.swap_weapon()
		"prompt:equip":
			var er := hud.equip_prompt.equip(Game.active())
			if not er.get("ok", false) and er.has("text"): hud.add_log(str(er.text), UiKit.MIST)
		"prompt:close": hud.equip_prompt.dismiss()
		"minimap": hud.open_page.emit("world_map", hud.minimap.place_at(p))
		"portrait": hud.open_page.emit("character", {})
		"tracker": hud.open_page.emit("quests", {})
		"auto_hunt":
			var ac = Game.active()
			var ah := Game.submit({"type": "set_auto_hunt", "on": not Game.world.auto_hunting(ac.id)})
			if not ah.get("ok", false) and ah.has("text"): hud.add_log(str(ah.text), UiKit.MIST)
		"progress": hud.open_page.emit("cultivation", {})
		_:
			if role.begins_with("points:") and hud.bound(): hud.actions.open_points(role.trim_prefix("points:"))
			if role.begins_with("pets:") and hud.bound():
				var parts := role.split(":")
				var res := {}
				match parts[1]:
					"active", "party": hud.open_page.emit("spirit_animals", {})
					"companion": hud.open_page.emit("companions", {})
					"bag": res = Game.submit({"type": "swap_pet_from_bag", "pet": parts[2]})
					"mount": res = Game.submit({"type": "set_mount"})
				if not res.is_empty() and not res.get("ok", false) and res.has("text"): hud.add_log(str(res.text), UiKit.MIST)
			if role.begins_with("path:") and hud.bound():
				var target := role.trim_prefix("path:")
				var pc = Game.active()
				var ap := Game.submit({"type": "auto_path", "target": "" if Game.world.auto_path_target(pc) == target else target})
				if not ap.get("ok", false) and ap.has("text"): hud.add_log(str(ap.text), UiKit.MIST)
			if role.begins_with("icon:"):
				var which := role.trim_prefix("icon:")
				hud.open_page.emit({"menu": "menu", "bag": "inventory", "map": "world_map", "mail": "mail"}[which], {})
				Audio.ui("ui_open")
	# In a fight the open fan is a quick pick: a toggle taken from it folds it again, out of the ring's way.
	if hud.fight and hud.fan_open and role in Hud.FAN_ROLE.values(): hud.fan_open = false

func drag(id: int, p: Vector2):
	if not hud.touches.has(id): return
	if id == hud.joystick_id:
		var delta = p - hud.joystick_origin
		hud.joystick_pos = p
		hud.player.movement = delta.limit_length(76) / 76 if delta.length() > 9 else Vector2.ZERO
	elif hud.touches[id].has("gesture"):
		(hud.touches[id].gesture as AimGesture).drag(p)
	elif hud.touches[id].role == "pet" and hud.pet_wheel:
		hud.pet_pick = _wheel_pick(p)
	elif hud.touches[id].role == "skill" and not hud.touches[id].swiped:
		var delta = p - hud.touches[id].start
		if absf(delta.y) > 40 and absf(delta.y) > absf(delta.x):
			scroll_skills(-1 if delta.y < 0 else 1)
			hud.touches[id].swiped = true

func release(id: int):
	var info: Dictionary = hud.touches.get(id, {})
	hud.touches.erase(id)
	if id == hud.joystick_id:
		hud.joystick_id = -999
		hud.player.movement = Vector2.ZERO
		hud.player.joystick_engaged = false
		hud.player.reset_sprint()
	if info.get("role", "") == "meditate" and hud.bound():
		if hud.cultivate_hold >= 0.0 and hud.cultivate_pressed:
			hud.cultivate_pressed = false
			hud.actions.tap_cultivate()
		hud.cultivate_pressed = false
	if info.has("gesture"):
		_release_aim(info)
		return
	if info.get("role", "") == "skill" and not info.get("swiped", false) and info.has("slot") and hud.bound():
		_technique_said(hud.player.use_technique(int(info.slot)))
	if info.get("role", "") == "pet" and hud.bound() and hud.pet_pressed:
		hud.pet_pressed = false
		if hud.pet_wheel:
			hud.pet_wheel = false
			if hud.pet_pick >= 0: _pet_wheel_do(str(Hud.PET_WHEEL[hud.pet_pick]))
		else:
			hud.open_page.emit("spirit_animals", {})
	if info.get("role", "") == "attack": attack_up()
	if info.get("role", "") == "jump":
		hud.player.fly_up = false
		hud.player.jump_held = false
	if info.get("role", "") == "guard": hud.player.fly_down = false
	if info.get("role", "") == "guard" and hud.bound() and hud.guard_pressed:
		hud.guard_pressed = false
		if hud.guard_hold <= 0.18:
			dodge()
		Game.submit({"type": "guard_end"})

## The fan opens and closes (decision 20). At rest the choice is kept: it opens again after the next fight if left open.
func toggle_fan() -> void:
	hud.fan_open = not hud.fan_open
	if not hud.fight: hud.fan_rest_open = hud.fan_open
	Audio.ui("ui_tap")

## Each frame, the holds on the controls: Cultivate held opens its page, Pet held its wheel, Dodge held guards, and
## Attack held with a flute plays the melody.
func tick_holds(delta: float) -> void:
	if hud.cultivate_pressed:
		hud.cultivate_hold += delta
		if hud.cultivate_hold >= float(ContentDB.curve("meditation.hold_page_s", 0.6)) if Game else 0.6:
			hud.cultivate_pressed = false
			hud.cultivate_hold = -99.0
			hud.open_page.emit("cultivation", {})
	if hud.pet_pressed and not hud.pet_wheel:
		hud.pet_hold += delta
		if hud.pet_hold >= 0.45:
			hud.pet_wheel = true
			hud.pet_pick = -1
	if hud.guard_pressed:
		hud.guard_hold += delta
		if hud.guard_hold > 0.18 and hud.bound() and not hud.player.state.flying and not Game.combat.timeline(Game.active_id).guard:
			Game.submit({"type": "guard_start"})
	if hud.attack_pressed:
		hud.attack_hold += delta
		_try_melody()

func scroll_skills(direction: int) -> void:
	if hud.scroll_progress < 1.0: return
	if hud.bound() and not Unlocks.is_unlocked(Game.active_id, "technique_page_2"): return
	hud.scroll_direction = direction
	hud.scroll_progress = 0.0
	hud.skill_page = (hud.skill_page + 1) % 2
	if hud.bound(): Game.active().skill_page = hud.skill_page

func advance_scroll(delta: float) -> void:
	hud.scroll_progress = minf(1.0, hud.scroll_progress + delta / 0.36)

## A technique refused says why in the log (no Qi, not ready, the wrong weapon, sealed, only in flight).
func _technique_said(r: Dictionary) -> void:
	if not r.get("ok", false) and r.get("reason", "") in ["no_qi", "cooldown", "wrong_weapon", "sealed", "needs_flight"]:
		hud.add_log({"no_qi": Tx.t("hud.not_enough_qi"), "cooldown": Tx.t("hud.not_ready"), "wrong_weapon": str(r.get("text", Tx.t("hud.wrong_weapon"))), "sealed": Tx.t("hud.your_qi_is_sealed"), "needs_flight": Tx.t("hud.only_in_flight")}[r.reason], UiKit.MIST)

## The player aims on the plane (the top-down room, redesign Phase 2); the side view's facing is only left or right.
func aims() -> bool:
	return is_instance_valid(hud.player) and hud.player.has_method("aim_attack")   # side view: no aiming

## The drawn technique slot of the page nearest `p` (its aim starts from that button's centre).
func _nearest_slot_center(p: Vector2) -> Vector2:
	var best: Vector2 = hud.slots[0]
	for i in hud.slots.size():
		if hud.layout.slot_filled(i + hud.skill_page * 4) and p.distance_to(hud.slots[i]) < p.distance_to(best): best = hud.slots[i]
	return best

## Each held Attack or technique touch that aims shows its aim on the ground (the player's preview, the world's drawing).
func tick_aims(delta: float) -> void:
	if not aims(): return
	var shown_aim := false
	for id in hud.touches:
		var g = hud.touches[id].get("gesture")
		if g == null: continue
		g.advance(delta)
		if g.kind == "attack": _tick_hold(g)
		if (g.aiming or g.guarding) and not shown_aim:
			hud.player.preview_aim(g.kind, int(hud.touches[id].get("slot", -1)), g.dir(), g.reach_k(), armed(g))
			shown_aim = true
	if not shown_aim: hud.player.aim = {}

## Decision 35: Attack's drag moves are live while the character may attack and is not busy with a harvest tap or a
## channel (decision 42: a context in reach never takes the button).
func moves_live() -> bool:
	return hud.bound() and hud.tapping.object == "" and hud.channel.object == "" and attack_first()

## What an Attack or technique touch would do if let go now: tap, aim, cancel, or one of Attack's drag moves
## (finisher, plunge, guard) while they are live.
func armed(g: AimGesture) -> String:
	if g.kind != "attack" or not aims(): return g.release()
	if g.guarding: return "guard"
	if not moves_live(): return g.release()
	return g.move(not hud.player.motor.grounded, hud.player.plunge_ready())

## Attack held still past `guard_s`: the guard (or the slotted stance) starts on the ground; in the air it waits for
## the landing. A refused guard (a weapon that cannot guard), or a button that is not attacking, leaves the let-go a tap.
func _tick_hold(g: AimGesture) -> void:
	if not g.holding(): return
	if not moves_live():
		g.refused = true
		return
	if not hud.player.motor.grounded: return
	var got: String = hud.player.hold_guard()
	if got == "":
		g.refused = true
		return
	g.guarding = true
	g.guard_kind = got

## Letting go of an aiming touch: a tap attacks or casts at the soft lock, an aim along its direction, a cancel does
## nothing. Attack's drag moves (decision 35): a finisher strikes the combo's last step along the drag, a plunge drops
## (an aimed blow down if it cannot), and a guard held on the button ends and strikes nothing.
func _release_aim(info: Dictionary) -> void:
	var g: AimGesture = info.gesture
	var what := armed(g)
	hud.player.aim = {}
	if info.role == "attack":
		var may: bool = hud.bound() and Unlocks.is_unlocked(Game.active_id, "attack")
		match what:
			"tap": primary()
			"aim": if may: hud.player.aim_attack(g.dir())
			"finisher": if may: hud.player.finisher(g.dir())
			"plunge":
				if not hud.player.plunge().get("ok", false) and may: hud.player.aim_attack(g.dir())
			"guard": hud.player.release_guard()
		attack_up()
	elif info.has("slot") and hud.bound():
		match what:
			"tap": _technique_said(hud.player.use_technique(int(info.slot)))
			"aim": _technique_said(hud.player.aim_technique(int(info.slot), g.dir(), g.reach_k()))

## A tap of Dodge: the combat authority's dodge, or the top-down prototype's own dash (redesign Phase 1).
func dodge() -> void:
	if hud.player.has_method("dodge"): hud.player.dodge()
	else: hud.side_view.dodge()   # side view

## Where each choice of the pet command wheel sits around the Pet button.
func wheel_pos(i: int) -> Vector2:
	var a := -PI / 2.0 + TAU * float(i) / float(Hud.PET_WHEEL.size())
	return hud.pet_center + Vector2(cos(a), sin(a)) * 104.0

func _wheel_pick(p: Vector2) -> int:
	if p.distance_to(hud.pet_center) < 40.0: return -1
	var best := -1
	var bd := 70.0
	for i in Hud.PET_WHEEL.size():
		var d := p.distance_to(wheel_pos(i))
		if d < bd:
			bd = d
			best = i
	return best

func _pet_wheel_do(choice: String) -> void:
	var res := {}
	match choice:
		"ride": res = Game.submit({"type": "set_mount"})
		"bag": hud.open_page.emit("spirit_animals", {})
		_: res = Game.submit({"type": "pet_command", "command": choice})
	if not res.is_empty() and not res.get("ok", false) and res.has("text"): hud.add_log(str(res.text), UiKit.MIST)

## The Attack button: it attacks, at rest as in a fight (decision 42); a harvest's hold or its tap (begun from the
## context's button) keeps the hands busy. Before the Attack lesson there is no button, and the J and Enter keys use the
## context.
func primary() -> void:
	if not hud.bound():
		hud.player.attack()
		return
	if hud.tapping.object != "" or hud.channel.object != "": return
	if attack_first():
		hud.player.attack()
		hud.attack_pressed = true
		hud.attack_hold = 0.0
	elif not hud.context.is_empty(): hud.actions.use_context()

## Held Attack with a flute plays the melody aura once the family's hold time has passed (S47 v1.1).
func _try_melody() -> void:
	if not hud.bound() or Game.combat.is_playing(Game.active_id): return
	var ch: Dictionary = StatRules.family(Game.active()).get("channel", {})
	if ch.is_empty() or hud.attack_hold < float(ch.get("hold_s", 0.35)): return
	var r := Game.submit({"type": "channel_melody", "on": true})
	if r.ok or str(r.get("reason", "")) == "busy": return   # a busy hand tries again next frame
	hud.attack_pressed = false
	if str(r.get("reason", "")) == "no_composure" and r.has("text"): hud.add_log(str(r.text), UiKit.MIST)

func attack_up() -> void:
	hud.attack_pressed = false
	hud.attack_hold = 0.0
	if hud.bound() and Game.combat.is_playing(Game.active_id): Game.submit({"type": "channel_melody", "on": false})

## The attack button's one rule: once the character may attack it attacks, always. A gathering node, a pickup, a
## person, a door or a ladder beside you never takes it: what the context offers has its own button on ring 2. An
## earlier fix held to this in a fight (a resource under the player had taken the button mid-fight); decision 42 holds
## to it at rest too (mockup 02's context on the big button is retired).
func attack_first() -> bool:
	return hud.bound() and Unlocks.is_unlocked(Game.active_id, "attack")

## The thumb on Attack's aiming gesture, or null.
func attack_gesture() -> AimGesture:
	for id in hud.touches:
		var g = hud.touches[id].get("gesture")
		if g != null and g.kind == "attack": return g
	return null
