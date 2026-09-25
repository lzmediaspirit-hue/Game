extends Control
## S24 · The play screen. Every element stays hidden until the unlock service
## reveals it. Controls send intents (or ask the shell to open a page); nothing
## here changes game state. Positions follow the S24 table (1280 × 720) and are
## mirrored for the left-handed option.
##
## The QI bar exists only once the character has a QI pool (Bone Forging 7): a
## Mortal or early Bone Forging disciple has no Qi, so no QI bar is drawn.

var font = preload("res://art/fonts/CormorantGaramond.ttf")
var frame_style: StyleBox
var player: Node2D
var world: Node2D
var skill_page := 0
var scroll_progress := 1.0
var scroll_direction := -1
var touches: Dictionary = {}
var joystick_id := -999
var joystick_origin := Vector2.ZERO
var joystick_pos := Vector2.ZERO
var mouse_down := false
var left_handed := false

# S24 positions (right-handed); mirrored when left-handed.
var slots := [Vector2(1036, 634), Vector2(1030, 536), Vector2(1088, 455), Vector2(1185, 425)]
var attack_center := Vector2(1165, 605)
var jump_center := Vector2(933, 640)
var meditate_center := Vector2(841, 640)
var sense_center := Vector2(749, 640)
var quick_center := Vector2(887, 555)
var pet_center := Vector2(975, 555)
var guard_center := Vector2(799, 555)
var minimap_rect := Rect2(1032, 16, 232, 140)
var icon_row := [["menu", Vector2(1058, 188)], ["bag", Vector2(1116, 188)], ["map", Vector2(1174, 188)], ["mail", Vector2(1232, 188)]]

const GOLD := Color("d5bd85")
signal page_changed(page: int)
signal open_page(page: String, args: Dictionary)
signal dialogue_requested(convo: Dictionary)
signal fishing_requested(object_id: String)

var log_lines: Array = []          # [{text, t, color}]
var toasts: Array = []             # [{text, t, kind}]
var banner := {"text": "", "sub": "", "t": 0.0}
# S40 captions: sound-only cues written out when the player turns captions on.
const CAPTIONS := {"boss_phase": "boss_roar", "field_boss_spawned": "distant_roar", "bell_rung": "bell", "mail_received": "letter",
	"qi_backlash": "backlash", "defence_warning": "war_drums", "attack_started": "wind_up", "enemy_aggro": "noticed"}
var caption := {"text": "", "t": 9.0}
var context: Dictionary = {}
var channel := {"object": "", "t": 0.0, "dur": 0.0, "action": ""}
var cultivate_hold := 0.0
var cultivate_pressed := false
var guard_hold := 0.0
var guard_pressed := false
var pulses: Dictionary = {}        # element -> seconds of reveal pulse
var boss_uid := 0
var t := 0.0
var hint_timer := 0.0

func _ready() -> void:
	frame_style = UiKit.style("minor_panel")
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if Game and GameEvents:
		GameEvents.event.connect(_on_event)
		left_handed = bool(Game.account.settings.get("left_handed", false))
	_apply_hand()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)

func _apply_hand() -> void:
	if not left_handed: return
	for i in slots.size(): slots[i] = _mirror(slots[i])
	for k in ["attack_center", "jump_center", "meditate_center", "sense_center", "quick_center", "pet_center", "guard_center"]:
		set(k, _mirror(get(k)))

func _mirror(p: Vector2) -> Vector2:
	return Vector2(1280.0 - p.x, p.y)

func bound() -> bool:
	return is_instance_valid(player) and player.actor_id != "" and Game.active() != null

func shown(element: String) -> bool:
	return not bound() or Game.is_revealed("hud:" + element)

func scroll_skills(direction: int) -> void:
	if scroll_progress < 1.0: return
	if bound() and not Unlocks.is_unlocked(Game.active_id, "technique_page_2"): return
	scroll_direction = direction
	scroll_progress = 0.0
	skill_page = (skill_page + 1) % 2
	page_changed.emit(skill_page)
	if bound(): Game.active().skill_page = skill_page

func advance_scroll(delta: float) -> void:
	scroll_progress = minf(1.0, scroll_progress + delta / 0.36)

func _process(delta: float) -> void:
	t += delta
	advance_scroll(delta)
	for l in log_lines: l.t += delta
	log_lines = log_lines.filter(func(l): return l.t < 6.0)
	for tt in toasts: tt.t += delta
	toasts = toasts.filter(func(tt): return tt.t < 3.2)
	banner.t += delta
	caption.t = float(caption.t) + delta
	for k in pulses.keys():
		pulses[k] -= delta
		if pulses[k] <= 0: pulses.erase(k)
	if cultivate_pressed:
		cultivate_hold += delta
		if cultivate_hold >= float(ContentDB.curve("meditation.hold_page_s", 0.6)) if Game else 0.6:
			cultivate_pressed = false
			cultivate_hold = -99.0
			open_page.emit("cultivation", {})
	if guard_pressed:
		guard_hold += delta
		if guard_hold > 0.18 and bound() and not Game.combat.timeline(Game.active_id).guard:
			Game.submit({"type": "guard_start"})
	_tick_channel(delta)
	if bound() and world: context = world.context
	queue_redraw()

func _tick_channel(delta: float) -> void:
	if channel.object == "" or not bound(): return
	if player.last_axis.length() > 0.2:
		channel.object = ""
		player.channel_time = 0.0
		player.channel_action = ""
		return
	channel.t += delta
	player.channel_time = channel.t
	player.channel_action = channel.action
	if channel.t >= channel.dur:
		var obj: String = channel.object
		channel.object = ""
		player.channel_time = 0.0
		player.channel_action = ""
		if channel.action in ["gather", "mine"]:
			var r := Game.submit({"type": "complete_node", "object": obj})
			if r.ok: add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(r.item)), int(r.count)], UiKit.BRIGHT_JADE)

func _notification(what):
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		touches.clear()
		joystick_id = -999
		mouse_down = false
		if is_instance_valid(player):
			player.movement = Vector2.ZERO
			player.joystick_engaged = false
			player.reset_sprint()

# ------------------------------------------------------------------ input
func role_at(p: Vector2) -> String:
	if p.distance_to(attack_center) < 74: return "attack"
	if p.distance_to(jump_center) < 36 and shown("jump"): return "jump"
	if p.distance_to(meditate_center) < 36 and shown("cultivate"): return "meditate"
	if p.distance_to(sense_center) < 36 and shown("sense"): return "sense"
	if p.distance_to(quick_center) < 30 and shown("quick_use"): return "quick"
	if p.distance_to(pet_center) < 30 and shown("pet"): return "pet"
	if p.distance_to(guard_center) < 30 and shown("guard"): return "guard"
	for center in slots:
		if p.distance_to(center) < 43 and shown("skills"): return "skill"
	if minimap_rect.has_point(p) and shown("minimap"): return "minimap"
	for ic in icon_row:
		if p.distance_to(ic[1]) < 27 and shown(ic[0]): return "icon:" + str(ic[0])
	if Rect2(16, 16, 360, 104).has_point(p) and shown("player_panel"): return "portrait"
	if Rect2(16, 128, 300, 150).has_point(p) and shown("quest_tracker"): return "tracker"
	if Rect2(0, 704, 1280, 16).has_point(p) and shown("progress_bar"): return "progress"
	if (p.x < 640) != left_handed: return "joystick"
	return "none"

func press(id: int, p: Vector2):
	var role := role_at(p)
	touches[id] = {"role": role, "start": p, "swiped": false}
	match role:
		"joystick":
			if joystick_id == -999:
				joystick_id = id
				joystick_origin = p
				joystick_pos = p
				player.joystick_engaged = true
		"attack": primary()
		"jump":
			player.jump()
			player.fly_up = true    # held Jump climbs while flying
		"meditate":
			if bound():
				cultivate_pressed = true
				cultivate_hold = 0.0
			else:
				player.meditate()
		"skill":
			for i in slots.size():
				if p.distance_to(slots[i]) < 43:
					touches[id]["slot"] = i + skill_page * 4
		"guard":
			if player.state.flying:
				player.fly_down = true   # held Guard descends while flying
			else:
				guard_pressed = true
				guard_hold = 0.0
		"quick": use_quick()
		"sense":
			if bound():
				var sr := Game.submit({"type": "sense_pulse"})
				if not sr.ok and sr.has("text"): add_log(str(sr.text), UiKit.MIST)
		"pet": if bound(): open_page.emit("spirit_animals", {})
		"minimap": open_page.emit("world_map", {})
		"portrait": open_page.emit("character", {})
		"tracker": open_page.emit("quests", {})
		"progress": open_page.emit("cultivation", {})
		_:
			if role.begins_with("icon:"):
				var which := role.trim_prefix("icon:")
				open_page.emit({"menu": "menu", "bag": "inventory", "map": "world_map", "mail": "mail"}[which], {})
				Audio.ui("ui_open")

func drag(id: int, p: Vector2):
	if not touches.has(id): return
	if id == joystick_id:
		var delta = p - joystick_origin
		joystick_pos = p
		player.movement = delta.limit_length(76) / 76 if delta.length() > 9 else Vector2.ZERO
	elif touches[id].role == "skill" and not touches[id].swiped:
		var delta = p - touches[id].start
		if absf(delta.y) > 40 and absf(delta.y) > absf(delta.x):
			scroll_skills(-1 if delta.y < 0 else 1)
			touches[id].swiped = true

func release(id: int):
	var info: Dictionary = touches.get(id, {})
	touches.erase(id)
	if id == joystick_id:
		joystick_id = -999
		player.movement = Vector2.ZERO
		player.joystick_engaged = false
		player.reset_sprint()
	if info.get("role", "") == "meditate" and bound():
		if cultivate_hold >= 0.0 and cultivate_pressed:
			cultivate_pressed = false
			tap_cultivate()
		cultivate_pressed = false
	if info.get("role", "") == "skill" and not info.get("swiped", false) and info.has("slot") and bound():
		var r: Dictionary = player.use_technique(int(info.slot))
		if not r.ok and r.get("reason", "") in ["no_qi", "cooldown", "wrong_weapon", "sealed", "needs_flight"]:
			add_log({"no_qi": Tx.t("hud.not_enough_qi"), "cooldown": Tx.t("hud.not_ready"), "wrong_weapon": str(r.get("text", Tx.t("hud.wrong_weapon"))), "sealed": Tx.t("hud.your_qi_is_sealed"), "needs_flight": Tx.t("hud.only_in_flight")}[r.reason], UiKit.MIST)
	if info.get("role", "") == "jump": player.fly_up = false
	if info.get("role", "") == "guard": player.fly_down = false
	if info.get("role", "") == "guard" and bound() and guard_pressed:
		guard_pressed = false
		if guard_hold <= 0.18:
			Game.submit({"type": "dodge", "direction": player.last_axis, "facing": player.facing})
		Game.submit({"type": "guard_end"})

func tap_cultivate() -> void:
	var c = Game.active()
	if c.cultivator.state == "bottleneck" and not c.cultivator.meditating:
		open_page.emit("breakthrough", {})
		return
	player.meditate()

func primary() -> void:
	if not bound():
		player.attack()
		return
	if channel.object != "": return
	if not context.is_empty() and not _enemy_close():
		use_context()
		return
	if Unlocks.is_unlocked(Game.active_id, "attack"): player.attack()
	elif not context.is_empty(): use_context()

func _enemy_close() -> bool:
	if Game.room_rt == null: return false
	for e in Game.room_rt.living_enemies():
		if e.team == "enemy" and not e.def.get("passive", false) and e.plane.distance_to(player.plane) < 150.0: return true
	return false

func use_context() -> void:
	if context.has("portal"):
		world.request_portal(str(context.portal))
		return
	var r := Game.submit({"type": "interact", "object": str(context.get("object", ""))})
	if not r.ok:
		if r.has("text"): add_log(str(r.text), UiKit.MIST)
		return
	if r.has("dialogue"):
		dialogue_requested.emit(r.dialogue)
		return
	if r.has("open_page"):
		open_page.emit(str(r.open_page), {"object": str(context.get("object", ""))})
		return
	if str(r.get("minigame", "")) == "fishing":
		fishing_requested.emit(str(context.object))
		return
	if float(r.get("channel", 0.0)) > 0.0:
		channel = {"object": str(context.object), "t": 0.0, "dur": float(r.channel), "action": str(r.get("action", "gather"))}
		return
	if r.has("text") and str(r.text) != "": add_log(str(r.text), UiKit.PAPER)

func use_quick() -> void:
	if not bound(): return
	var r := Game.submit({"type": "use_quick"})
	if not r.ok:
		if r.get("reason", "") == "none_left": add_log(Tx.t("hud.no_left") % ContentDB.item_name(str(r.item)), UiKit.MIST)
		elif r.get("reason", "") == "cooldown": add_log(Tx.t("hud.not_ready_yet"), UiKit.MIST)
		elif r.has("text"): add_log(str(r.text), UiKit.MIST)

## Pages and dialogue block world input; held controls are released at once.
var blocked := false

func set_blocked(value: bool) -> void:
	if value and not blocked: _notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	blocked = value

func _input(event):
	if blocked: return
	if event is InputEventMouse and event.device == -1: return
	if event is InputEventScreenTouch:
		if event.pressed and not event.canceled: press(event.index, event.position)
		else: release(event.index)
	elif event is InputEventScreenDrag: drag(event.index, event.position)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		mouse_down = event.pressed
		if event.pressed: press(-1, event.position)
		else: release(-1)
	elif event is InputEventMouseMotion and mouse_down: drag(-1, event.position)
	elif event is InputEventKey and not event.echo:
		if not bound():
			if event.pressed:
				match event.physical_keycode:
					KEY_SPACE: player.jump()
					KEY_J: player.attack()
					KEY_M: player.meditate()
					KEY_TAB: scroll_skills(-1)
			return
		var kc: int = event.physical_keycode
		if event.pressed:
			match kc:
				KEY_SPACE: player.jump()
				KEY_J, KEY_ENTER: primary()
				KEY_F: if not context.is_empty(): use_context()
				KEY_C: if shown("cultivate"): tap_cultivate()
				KEY_K:
					if shown("guard") and not player.state.flying:
						guard_pressed = true
						guard_hold = 0.0
				KEY_Q: if shown("quick_use"): use_quick()
				KEY_TAB: if shown("menu"): open_page.emit("menu", {})
				KEY_I, KEY_B: if shown("bag"): open_page.emit("inventory", {})
				KEY_M: if shown("map"): open_page.emit("world_map", {})
				KEY_L: if shown("quest_tracker"): open_page.emit("quests", {})
				KEY_E: if shown("pet"): open_page.emit("spirit_animals", {})
				KEY_P: if shown("cultivate"): open_page.emit("cultivation", {})
				KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8:
					if shown("skills"): player.use_technique(kc - KEY_1)
		else:
			if kc == KEY_K and guard_pressed:
				guard_pressed = false
				if guard_hold <= 0.18: Game.submit({"type": "dodge", "direction": player.last_axis, "facing": player.facing})
				Game.submit({"type": "guard_end"})

# ------------------------------------------------------------------ events
func add_log(text: String, color = UiKit.PAPER) -> void:
	log_lines.append({"text": text, "t": 0.0, "color": color})
	while log_lines.size() > 5: log_lines.pop_front()

func _pet_name(uid: String) -> String:
	var c = Game.active()
	for pt in (c.pets if c else []):
		if str(pt.uid) == uid: return str(pt.name)
	return Tx.t("hud.your_spirit_animal")

## Wind-ups only from bosses and elites, notices only from monsters off screen.
func _caption_worthy(name: String, p: Dictionary) -> bool:
	if name == "attack_started":
		var e = Game.room_rt.enemies.get(int(str(p.get("actor", "0")))) if Game.room_rt and str(p.get("actor", "")).is_valid_int() else null
		return e != null and (e.is_boss() or e.elite)
	if name == "enemy_aggro":
		var e2 = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
		var st = Game.actor_state(Game.active_id)
		return e2 != null and st != null and absf(e2.plane.x - st.plane.x) > 640.0
	return true

## Vibration on phones, when the player allows it (S40 haptics toggle).
func _buzz(ms: int) -> void:
	if Game.account.settings.get("haptics", true) and OS.has_feature("mobile"): Input.vibrate_handheld(ms)

func _draw_caption() -> void:
	if caption.text == "" or float(caption.t) > 2.6: return
	var a := clampf((2.6 - float(caption.t)) / 0.4, 0.0, 1.0)
	var w := 520.0
	draw_rect(Rect2(640 - w / 2.0, 604, w, 30), Color(0, 0, 0, 0.55 * a))
	UiKit.draw_text(self, "[" + str(caption.text) + "]", Vector2(640 - w / 2.0, 625), 17, Color(UiKit.PAPER, a), HORIZONTAL_ALIGNMENT_CENTER, w)

func toast(text: String, kind := "unlock") -> void:
	toasts.append({"text": text, "t": 0.0, "kind": kind})
	while toasts.size() > 3: toasts.pop_front()

func _on_event(name: String, p: Dictionary) -> void:
	if not bound(): return
	if CAPTIONS.has(name) and Game.account.settings.get("captions", false) and _caption_worthy(name, p):
		caption = {"text": Tx.t("hud.caption." + str(CAPTIONS[name])), "t": 0.0}
	match name:
		"item_added":
			if str(p.get("actor", "")) == Game.active_id and shown("system_log"):
				add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(p.item)), int(p.count)], UiKit.quality_color(str(p.get("quality", "common"))))
		"currency_changed":
			if int(p.get("delta", 0)) > 0 and shown("system_log") and str(p.get("source", "")) != "sell":
				add_log("+%d %s" % [int(p.delta), ContentDB.text("currency." + str(p.currency))], UiKit.PALE_GOLD)
		"system_unlocked":
			if p.get("toast", true) and str(p.get("label", "")) != "": toast(Tx.t("hud.new") + str(p.label))
		"hud_element_revealed":
			pulses[str(p.element)] = 1.2
		"quest_accepted":
			toast(Tx.t("hud.quest") + str(p.get("name", "")), "quest")
		"quest_completed":
			toast(Tx.t("hud.completed") + str(p.get("name", "")), "quest")
		"objective_progressed":
			pass
		"room_entered":
			var room := ContentDB.room(str(p.room))
			var zone := ContentDB.zone_of_room(str(p.room))
			banner = {"text": str(room.get("name", "")), "sub": str(room.get("region_name", zone.get("name", ""))), "t": 0.0}
			channel.object = ""
			# S17: a room's hazards and the attribute that answers them, once per entry.
			for hz in HazardRules.summary(Game.active(), room):
				add_log(Tx.t("hud.hazard") % [hz.name, Tx.t("ui.cultivation." + str(hz.stat)), int(hz.need), int(hz.have)],
					UiKit.BRIGHT_JADE if hz.answered else UiKit.PALE_GOLD)
		"bottleneck_reached":
			toast(Tx.t("hud.bottleneck_tap_cultivate_to_break") if not p.get("major", false) else Tx.t("hud.bottleneck_reached_see_the_cultivation"), "gold")
		"breakthrough_failed":
			add_log(Tx.t("hud.breakthrough_failed") + ContentDB.text("failure." + str(p.failure_id)), UiKit.RED)
		"achievement_unlocked":
			toast(Tx.t("hud.achievement") + str(p.get("name", "")), "gold")
		"title_changed":
			if p.get("earned", false): toast(Tx.t("hud.title_earned") + ContentDB.name_of("titles", str(p.title)), "gold")
		"mail_received":
			if Unlocks.is_unlocked(Game.active_id, "mail"): add_log(Tx.t("hud.a_letter_arrived"), UiKit.PALE_GOLD)
		"bag_full":
			add_log(Tx.t("hud.your_gourd_is_full"), UiKit.RED)
		"system_log":
			add_log(str(p.text), UiKit.PAPER)
		"portal_blocked":
			add_log(str(p.get("text", "")), UiKit.MIST)
		"field_boss_spawned", "elite_spawned":
			var def := ContentDB.entry("enemies", str(p.def))
			toast(Tx.t("hud.appears") % str(def.get("name", "")), "danger")
		"injury_added":
			add_log(Tx.t("hud.injury_severity") % [str(p.kind).capitalize(), int(p.severity)], UiKit.RED)
		"aptitude_revealed":
			toast(Tx.t("hud.aptitude_revealed") % str(p.aptitude).replace("_", " ").capitalize(), "gold")
		"craft_completed":
			add_log(Tx.t("hud.crafted") % [ContentDB.name_of("recipes", str(p.recipe)), str(p.quality).capitalize()], UiKit.quality_color(str(p.quality)))
			if str(p.quality).begins_with("pill_"): toast(Tx.t("hud.rare_pill") % str(p.quality).capitalize(), "gold")
		"breakthrough_succeeded":
			_buzz(120)
		"player_gravely_wounded":
			_buzz(200)
		"pets_bred":
			toast(Tx.t("hud.pets_bred") % ceili(float(p.get("hours", 24.0))), "gold")
		"treasure_planted":
			toast(Tx.t("hud.treasure_planted"), "gold")
		"treasure_harvested":
			toast(Tx.t("hud.treasure_harvested") % ContentDB.item_name(str(p.get("item", ""))), "gold")
		"treasure_used":
			toast(Tx.t("hud.treasure_used." + str(p.treasure)), "gold")
		# Gap report G1: the heart, the ledger, the flames and debts that come due.
		"heart_demon_changed":
			if p.get("step_crossed", false):
				if float(p.get("delta", 0)) > 0: toast(Tx.t("hud.heart_demons_stir") % int(p.value), "danger")
				else: add_log(Tx.t("hud.heart_demons_calm"), UiKit.BRIGHT_JADE)
		"karma_changed":
			if int(p.get("delta_merit", 0)) > 0: add_log(Tx.t("hud.merit_gained") % int(p.delta_merit), UiKit.PALE_GOLD)
			if int(p.get("delta_sin", 0)) > 0: add_log(Tx.t("hud.sin_gained") % int(p.delta_sin), Color("e07a7a"))
		"flame_absorbed":
			toast(Tx.t("hud.flame_absorbed") % ContentDB.item_name(str(p.flame)), "gold")
		"karma_debt_repaid":
			toast(Tx.t("hud.debt_" + str(p.debt)), "quest")
		"room_event_flawless":
			toast(Tx.t("hud.flawless") , "gold")
		"pill_soul_awakened":
			toast(Tx.t("hud.pill_soul") % Tx.t("hud.pill_soul_effect." + str(p.effect)), "gold")
		"spar_ended":
			toast(Tx.t("hud.spar_won") if p.get("winner", "") == "player" else Tx.t("hud.spar_lost_try_again"), "quest")
		"quest_ready":
			toast(Tx.t("hud.ready_to_hand_in") + str(Game.quest.quest_def(Game.active(), str(p.quest)).get("name", "")), "quest")
		"codex_entry_unlocked":
			add_log(Tx.t("hud.codex") + str(ContentDB.entry("codex", str(p.entry)).get("title", "")), UiKit.PALE_GOLD)
		"teleport_discovered":
			toast(Tx.t("hud.teleport_stone_attuned"), "gold")
		"hidden_portal_revealed":
			toast(Tx.t("hud.a_hidden_path_opens"), "gold")
		"meridian_gate_opened":
			toast(Tx.t("hud.meridian_gate_opened") % str(p.get("channel", "")).replace("_", " ").capitalize(), "gold")
		"stability_changed":
			add_log(Tx.t("hud.your_foundation_is") % str(p.get("word", "")).to_lower(), UiKit.MIST)
		"overflow_mailed":
			add_log(Tx.t("hud.no_room_in_your_gourd"), UiKit.PALE_GOLD)
		"egg_hatched":
			toast(Tx.t("hud.the_egg_hatched_a") % ContentDB.name_of("pets", str(p.species)), "gold")
		"bond_changed":
			add_log(Tx.t("hud.hearts") % [_pet_name(str(p.pet)), int(float(p.value))], UiKit.RED)
		"field_boss_defeated":
			toast(Tx.t("hud.is_defeated") % ContentDB.name_of("enemies", str(p.enemy)), "gold")
		"defence_warning":
			toast(Tx.t("hud.raiders_at_the_gates_hold"), "danger")
		"defence_result":
			toast(Tx.t("hud.the_raid_is_beaten_back") if p.get("won", false) else Tx.t("hud.the_raiders_broke_through"), "gold" if p.get("won", false) else "danger")
		"building_upgraded":
			add_log(Tx.t("hud.reached_level") % [ContentDB.name_of("sect_buildings", str(p.building)), int(p.level)], UiKit.PALE_GOLD)
		"prestige_gained":
			if Game.sect.founded(): add_log(Tx.t("hud.prestige") % int(p.amount), UiKit.PALE_GOLD)
		"expedition_returned":
			add_log(Tx.t("hud.expedition_to") % [ContentDB.name_of("expeditions", str(p.region)), Tx.t("hud.returned_with_spoils") if p.get("success", false) else Tx.t("hud.came_back_empty_handed")], UiKit.PALE_GOLD)
		"reputation_changed":
			add_log(Tx.t("hud.reputation") % [str(p.faction).replace("_", " ").capitalize(), int(p.value)], UiKit.MIST)
		"dismounted":
			add_log(Tx.t("hud.dismounted"), UiKit.RED)
		"item_bound":
			toast(Tx.t("hud.item_bound") % ContentDB.item_name(str(p.item)), "gold")
		"binding_interrupted":
			add_log(Tx.t("hud.binding_broken"), UiKit.RED)
		"artifact_spirit_awakened":
			toast(Tx.t("hud.spirit_awake") % ContentDB.item_name(str(p.item)), "gold")
		"pet_evolved":
			toast(Tx.t("hud.grows_into_a") % [_pet_name(str(p.pet)), str(p.get("branch", "")) if str(p.get("branch", "")) != "" else str(Game.pets.stage_def(str(p.stage)).get("name", ""))], "gold")
		"trait_revealed":
			toast(Tx.t("hud.shows_a_trait") % [_pet_name(str(p.pet)), ContentDB.name_of("pet_traits", str(p.trait))], "gold")
		"pet_level_up":
			add_log(Tx.t("hud.reached_level") % [_pet_name(str(p.pet)), int(p.level)], UiKit.PALE_GOLD)
		"pet_retreated":
			add_log(Tx.t("hud.your_spirit_animal_retreats_into"), UiKit.MIST)
		"pet_returned":
			add_log(Tx.t("hud.your_spirit_animal_is_back"), UiKit.MIST)
		"companion_downed":
			add_log(Tx.t("hud.is_down") % ContentDB.name_of("companions", str(p.get("companion", ""))), UiKit.RED)
		"companion_revived":
			add_log(Tx.t("hud.is_back_on_their_feet") % ContentDB.name_of("companions", str(p.get("companion", ""))), UiKit.MIST)
		"building_damaged":
			toast(Tx.t("hud.raiders_damaged_your_repair_it") % ContentDB.name_of("sect_buildings", str(p.building)), "danger")
		"zone_ceiling_reached":
			toast(Tx.t("hud.this_land_can_take_you"), "gold")
		"auction_bid_placed":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.auction_bid_placed") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("bid", 0))], UiKit.PALE_GOLD)
		"auction_outbid":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.auction_outbid") % ContentDB.item_name(str(p.get("item", ""))), UiKit.MIST)
		"auction_won":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.auction_won") % ContentDB.item_name(str(p.get("item", ""))), "gold")

# ------------------------------------------------------------------ drawing
## A HUD button: jade-enamel face with a vertical sheen, a thin gold bezel, a gloss arc
## and, when active, a soft gold halo. Everything is anti-aliased so it stays round at any scale.
func ring(center: Vector2, radius: float, active := false, opacity := 1.0, gold := false) -> void:
	var tint := Color(1, 1, 1, opacity)
	var lit := active or gold
	draw_circle(center + Vector2(0, 4), radius + 4, Color(0, 0.02, 0.03, 0.42) * tint, true, -1.0, true)
	if lit:
		for i in 3:
			draw_arc(center, radius + 5 + i * 3, 0, TAU, 72, Color(UiKit.GOLD, (0.30 - i * 0.09) * opacity), 3.0, true)
	_disc(center, radius + 2.5, Color("f0d08a") if lit else Color("c6a262"), Color("7a5426") if lit else Color("5c4424"), tint)
	_disc(center, radius, Color("1d5157"), Color("061519"), tint)
	draw_arc(center, radius - 3.5, 0, TAU, 72, Color(0.40, 0.84, 0.74, 0.30 if lit else 0.2) * tint, 1.5, true)
	draw_arc(center, radius - 2.0, PI * 1.15, PI * 1.85, 36, Color(1, 1, 1, 0.12) * tint, maxf(2.0, radius * 0.07), true)

## Filled circle shaded from `top` to `bottom`.
func _disc(center: Vector2, radius: float, top: Color, bottom: Color, tint := Color.WHITE) -> void:
	var pts := PackedVector2Array()
	var cols := PackedColorArray()
	for i in 64:
		var a := TAU * i / 64.0
		var p := center + Vector2(cos(a), sin(a)) * radius
		pts.append(p)
		cols.append(top.lerp(bottom, (sin(a) + 1.0) * 0.5) * tint)
	draw_polygon(pts, cols)
	draw_arc(center, radius, 0, TAU, 64, bottom.lerp(top, 0.3) * tint, 1.0, true)

func glyph(id: String, center: Vector2, size := 32.0, color := Color.WHITE) -> void:
	var tex = SpriteCache.icon(id)
	if tex:
		draw_texture_rect(tex, Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)), false, color)

func skill_position(index: float) -> Vector2:
	var low := clampi(int(floor(index)), 0, 2)
	return slots[low].lerp(slots[low + 1], index - low)

func draw_skill_slot(center: Vector2, slot: int, opacity: float) -> void:
	ring(center, 33, false, opacity)
	if not bound(): return
	var c = Game.active()
	var n := ProgressionRules.technique_slot_count(c)
	if slot >= n:
		glyph("lock", center, 24, Color(1, 1, 1, 0.35 * opacity))
		return
	var tid = c.cultivator.technique_slots[slot]
	if tid == null or str(tid) == "":
		# An open slot: a faint cloud seal, so it reads as "waiting for a technique", not as broken.
		var motif: Texture2D = SpriteCache.tex("res://art/ui/slot_empty_motif__normal.png")
		if motif: draw_texture_rect(motif, Rect2(center - Vector2(22, 22), Vector2(44, 44)), false, Color(0.7, 1.0, 0.9, 0.35 * opacity))
		return
	var tex = SpriteCache.icon(str(tid))
	var tdef := ContentDB.entry("techniques", str(tid))
	var fam := str(StatRules.family(c).get("id", "fists"))
	var dim = tdef.get("family", "any") != "any" and not (tdef.family == fam or (tdef.family == "fists" and fam == "gauntlets"))
	if tex: draw_texture_rect(tex, Rect2(center - Vector2(24, 24), Vector2(48, 48)), false, Color(1, 1, 1, opacity * (0.35 if dim else 1.0)))
	var cd = c.pools.cooldown("tech:" + str(tid))
	if cd > 0.0:
		var total := float(tdef.get("cooldown_s", 5))
		var frac := clampf(cd / total, 0.0, 1.0)
		var pts := PackedVector2Array([center])
		for i in 25:
			var ang := -PI / 2 + TAU * frac * (i / 24.0)
			pts.append(center + Vector2(cos(ang), sin(ang)) * 30)
		if frac > 0.02: draw_colored_polygon(pts, Color(0, 0, 0, 0.6 * opacity))
		UiKit.draw_outlined(self, str(int(ceil(cd))), center + Vector2(-20, 7), 18, Color(UiKit.PAPER, opacity), HORIZONTAL_ALIGNMENT_CENTER, 40)
	elif c.pools.max_qi > 0 and c.pools.qi < Game.combat.technique_cost(c, tdef):
		draw_arc(center, 30, 0, TAU, 32, Color(UiKit.QI, 0.5 * opacity), 3)

func draw_skill_scroll() -> void:
	if scroll_progress >= 1:
		for i in slots.size(): draw_skill_slot(slots[i], i + skill_page * 4, 1.0)
		return
	var tt := scroll_progress * scroll_progress * (3 - 2 * scroll_progress)
	var shift := -scroll_direction * 4.0 * tt
	for page in 2:
		for i in 4:
			var index := i + shift + (scroll_direction * 4 if page == 1 else 0)
			if index < -0.35 or index > 3.35: continue
			var fade := minf(clampf((index + 0.35) / 0.35, 0, 1), clampf((3.35 - index) / 0.35, 0, 1))
			ring(skill_position(index), 33, false, fade)

func bar(r: Rect2, frac: float, fill: Color, label: String, value_text: String) -> void:
	draw_rect(r.grow(2), UiKit.INK)
	draw_rect(r, Color("17242c"))
	draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(frac, 0, 1), r.size.y)), fill)
	draw_line(r.position + Vector2(1, 2), r.position + Vector2(maxf(1, r.size.x * clampf(frac, 0, 1) - 1), 2), Color(1, 0.95, 0.8, 0.35), 2)
	UiKit.draw_text(self, label, r.position + Vector2(-34, 13), 16, GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	UiKit.draw_outlined(self, value_text, r.position + Vector2(0, 13), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

func _draw():
	if not is_instance_valid(player): return
	if not bound():
		_draw_legacy()
		return
	var c = Game.active()
	_draw_player_panel(c)
	if shown("quest_tracker"): _draw_tracker(c)
	if shown("minimap") and Game.account.settings.get("minimap", true): _draw_minimap(c)
	for ic in icon_row:
		if shown(ic[0]):
			ring(ic[1], 26, pulses.has("hud:" + ic[0]))
			glyph(ic[0], ic[1], 32)
			if ic[0] == "mail" and Game.mail.unread(c) > 0:
				draw_circle(ic[1] + Vector2(16, -16), 7, UiKit.RED)
	if shown("currency"):
		var cr := Rect2(1062, 222, 200, 34)
		draw_style_box(UiKit.style("currency_pill"), cr)
		glyph("coin", cr.position + Vector2(20, 17), 24)
		UiKit.draw_text(self, UiKit.fmt(Game.economy.balance("silver_tael")), cr.position + Vector2(38, 24), 18, UiKit.PALE_GOLD)
		if int(Game.account.currencies.get("spirit_stone", 0)) > 0:
			glyph("spirit_stone", cr.position + Vector2(128, 17), 22)
			UiKit.draw_text(self, str(Game.account.currencies.spirit_stone), cr.position + Vector2(144, 24), 18, UiKit.BRIGHT_JADE)
	_draw_controls(c)
	if shown("progress_bar"): _draw_progress(c)
	if shown("system_log"): _draw_log()
	_draw_banner()
	_draw_caption()
	_draw_toasts()
	_draw_boss()
	if joystick_id != -999:
		draw_arc(joystick_origin, 76, 0, TAU, 40, Color(1, 1, 1, 0.12), 2)
		draw_circle(joystick_origin + (joystick_pos - joystick_origin).limit_length(76), 18, Color(1, 1, 1, 0.14))
	if not Game.is_revealed("hud:joystick_hint_done") and Game.active().quests.has_flag("prologue_active") and t < 12.0:
		UiKit.draw_outlined(self, Tx.t("hud.drag_on_the_left_half"), Vector2(40, 470), 20, Color(UiKit.PAPER, 0.6 + 0.4 * sin(t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, 560)

func _draw_player_panel(c) -> void:
	if not shown("player_panel"): return
	# The panel grows by one row once the Soul bar exists (Spirit Awakening).
	var soul_row: bool = c.pools.max_soul > 0.0 and shown("soul_bar")
	var r := Rect2(16, 16, 360, 120 if soul_row else 104)
	draw_style_box(frame_style, r)
	# Portrait: a jade roundel with the realm seal.
	draw_circle(r.position + Vector2(46, 52), 34, UiKit.INK)
	draw_circle(r.position + Vector2(46, 52), 31, UiKit.DEEP_TEAL)
	draw_arc(r.position + Vector2(46, 52), 31, 0, TAU, 32, UiKit.GOLD if c.cultivator.state == "bottleneck" else UiKit.JADE, 2)
	UiKit.draw_text(self, c.name.substr(0, 1).to_upper(), r.position + Vector2(32, 66), 36, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true, true)
	UiKit.draw_text(self, c.name, r.position + Vector2(90, 30), 18, UiKit.PAPER)
	if shown("realm_badge"):
		UiKit.draw_text(self, ContentDB.realm_label(c.cultivator.realm_key), r.position + Vector2(90, 50), 15, UiKit.PALE_GOLD)
	var y := 60.0
	if shown("hp_bar"):
		bar(Rect2(r.position.x + 122, r.position.y + y, 222, 12), c.pools.hp / maxf(1.0, c.pools.max_hp), Color("c2474f"), Tx.t("hud.hp"), "%d/%d" % [int(c.pools.hp), int(c.pools.max_hp)])
		y += 17
	# No cultivation, no Qi: the QI bar appears only once a QI pool exists.
	if c.pools.max_qi > 0.0 and shown("qi_bar"):
		bar(Rect2(r.position.x + 122, r.position.y + y, 222, 10), c.pools.qi / c.pools.max_qi, UiKit.QI, Tx.t("hud.qi"), "%d/%d" % [int(c.pools.qi), int(c.pools.max_qi)])
		y += 15
	if soul_row:
		bar(Rect2(r.position.x + 122, r.position.y + y, 222, 10), c.pools.soul / c.pools.max_soul, UiKit.SOUL, Tx.t("hud.sl"), "%d/%d" % [int(c.pools.soul), int(c.pools.max_soul)])
	# Status stack (injuries, stability, toxicity, composure, buffs, statuses).
	var icons: Array = []
	for kind in c.cultivator.injuries: icons.append("injury_" + kind)
	if Unlocks.is_unlocked(c.id, "foundation") and c.cultivator.stability != "stable": icons.append("stability_" + c.cultivator.stability)
	if c.cultivator.state == "consolidating": icons.append("consolidating")
	if c.cultivator.toxicity > 0.5 * c.stats.value("toxicity_tolerance") and c.cultivator.toxicity > 5: icons.append("toxicity")
	if c.pools.hollowing > 5: icons.append("hollowing")
	if Unlocks.is_unlocked(c.id, "composure") and c.pools.composure < 100: icons.append("composure")
	for s in c.pools.statuses:
		if s.id != "spawn_protection": icons.append(str(ContentDB.entry("status_effects", str(s.id)).get("icon", s.id)))
	for m in c.stats.modifiers:
		if float(m.duration) >= 0 and not str(m.source).begins_with("heal:"):
			var ic := "buff_attack" if str(m.stat) in ["physical_attack", "qi_attack"] else ("buff_defense" if "defense" in str(m.stat) else "buff_speed")
			if not icons.has(ic): icons.append(ic)
	var x := r.position.x + 6.0
	for ic in icons.slice(0, 12):
		glyph(ic, Vector2(x + 12, r.end.y + 14), 24)
		x += 26

func _draw_tracker(c) -> void:
	var entries: Array = Game.quest.tracker(c)
	if entries.is_empty(): return
	if Game.room_rt and Game.room_rt.def.get("type", "") == "boss_arena": return
	var y := 146.0
	for q in entries:
		var col = UiKit.GOLD if q.kind in ["main", "prologue"] else Color("8fc8ff")
		if q.kind == "guided": col = Color("8fc8ff")
		UiKit.draw_text(self, ("◆ " if q.kind in ["main", "prologue"] else "● ") + str(q.name), Vector2(22, y), 17, col)
		y += 20
		for line in q.lines:
			var txt := str(line.text)
			if int(line.need) > 1: txt += "  %d/%d" % [int(line.have), int(line.need)]
			UiKit.draw_text(self, ("✓ " if line.done else "· ") + txt, Vector2(34, y), 15, UiKit.BRIGHT_JADE if line.done else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 280)
			y += 18
		y += 4
		if y > 290: break

func _draw_minimap(c) -> void:
	var r := minimap_rect
	draw_style_box(UiKit.style("minimap_frame"), r)
	var room := Game.room_rt.def if Game.room_rt else {}
	UiKit.draw_text(self, str(room.get("name", "")), r.position + Vector2(12, 18), 12, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24, true, true)
	var inner := Rect2(r.position + Vector2(8, 26), r.size - Vector2(16, 34))
	var b: Array = room.get("bounds", [0, 480, 1280, 480])
	var bw := float(b[2])
	var sx := inner.size.x / bw
	# Screen-space projection: x along the room, y = plane y - altitude, fitted to the
	# room's real extent (highest roof line down to the front of the ground strip).
	var top := 600.0
	var bottom := 700.0
	if Game.room_rt:
		for s0 in Game.room_rt.geometry.surfaces:
			top = minf(top, s0.bounds.position.y - s0.base - 20.0)
			bottom = maxf(bottom, s0.bounds.end.y)
	var sy := inner.size.y / maxf(1.0, bottom - top)
	var to_map := func(pos: Vector2, alt: float) -> Vector2:
		return inner.position + Vector2(pos.x * sx, (pos.y - alt - top) * sy)
	for s in Game.room_rt.geometry.surfaces if Game.room_rt else []:
		var y0: Vector2 = to_map.call(Vector2(s.bounds.position.x, s.bounds.position.y), s.base)
		var y1: Vector2 = to_map.call(Vector2(s.bounds.end.x, s.bounds.position.y), s.base)
		draw_line(y0, y1, Color(0.85, 0.92, 0.9, 0.55 if s.stratum == "ground" else 0.8), 2)
	for p in room.get("portals", []):
		var at: Array = p.at
		var st: Dictionary = Game.world.portal_state(c, p)
		if st.get("hidden", false): continue
		draw_circle(to_map.call(Vector2(float(at[0]), float(at[1])), 0.0), 4, Color("67d67a") if st.open else Color("7a8a8a"))
	for o in room.get("objects", []):
		if not Game.world.object_visible(c, o): continue
		var at2: Array = o.at
		var mp: Vector2 = to_map.call(Vector2(float(at2[0]), float(at2[1])), float(o.get("alt", 0)))
		if o.type == "npc":
			var mk: String = Game.quest.npc_marker(c, str(o.npc))
			draw_circle(mp, 3, UiKit.GOLD if mk in ["main", "ready"] else Color("f0e070"))
			if mk != "": draw_arc(mp, 6 + sin(t * 4.0) * 1.5, 0, TAU, 12, UiKit.GOLD, 1)
		elif o.type in ["shrine", "qi_spring", "teleport_stone"]:
			draw_rect(Rect2(mp - Vector2(3, 3), Vector2(6, 6)), UiKit.BRIGHT_JADE)
	if Game.room_rt and Game.account.settings.get("minimap_monsters", true):
		for e in Game.room_rt.enemies.values():
			if not e.alive or e.hidden: continue
			var ep: Vector2 = to_map.call(e.plane, e.altitude)
			var col = Color("8fd3ff") if e.team == "ally" else (UiKit.GOLD if e.elite or e.is_boss() else UiKit.RED)
			draw_circle(ep, 2.5, col)
	var pp: Vector2 = to_map.call(player.plane, player.altitude)
	draw_colored_polygon(PackedVector2Array([pp + Vector2(player.facing * 5, 0), pp + Vector2(-player.facing * 3, -4), pp + Vector2(-player.facing * 3, 4)]), Color.WHITE)

func _draw_controls(c) -> void:
	# Attack / context button.
	var ctx_glyph := ""
	if not context.is_empty() and (not _enemy_close() or not Unlocks.is_unlocked(c.id, "attack")):
		ctx_glyph = {"npc": "talk", "herb_patch": "gather", "ore_vein": "mine", "fishing_spot": "fish", "chest": "open", "storage_chest": "open",
			"portal": "enter", "cooking_pot": "cook", "alchemy_furnace": "alchemy", "earth_vent": "alchemy", "forge_anvil": "forge", "star_sight": "gather",
			"chart_table": "forge", "shipyard_slip": "forge", "starsea_dock": "enter"}.get(str(context.get("type", "")), "open")
	if shown("attack") or ctx_glyph != "":
		ring(attack_center, 66, Game.combat.is_busy(c.id) or channel.object != "", 1.0, pulses.has("hud:attack"))
		if ctx_glyph != "":
			glyph(ctx_glyph, attack_center, 64)
			UiKit.draw_outlined(self, str(context.get("label", "")), attack_center + Vector2(-60, 50), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 120)
		else:
			glyph(str(StatRules.family(c).get("hud_glyph", "fist")), attack_center, 64)
		if channel.object != "":
			draw_arc(attack_center, 60, -PI / 2, -PI / 2 + TAU * clampf(channel.t / maxf(0.01, channel.dur), 0, 1), 40, UiKit.BRIGHT_JADE, 5)
	if shown("skills"):
		draw_skill_scroll()
		if Unlocks.is_unlocked(c.id, "technique_page_2"):
			for i in 2: draw_circle(Vector2(1113 + i * 16, 501) if not left_handed else Vector2(167 - i * 16, 501), 3, GOLD if i == skill_page else Color("344d52"))
	if shown("jump"):
		ring(jump_center, 32, false, 1.0, pulses.has("hud:jump"))
		glyph("jump", jump_center)
	if shown("cultivate"):
		var gold: bool = c.cultivator.state == "bottleneck"
		ring(meditate_center, 32, c.cultivator.meditating, 1.0, gold or pulses.has("hud:cultivate"))
		if gold: draw_arc(meditate_center, 38 + sin(t * 4.0) * 2, 0, TAU, 40, Color(UiKit.GOLD, 0.6), 3)
		glyph("cultivate", meditate_center, 32, UiKit.GOLD if gold else Color.WHITE)
		if cultivate_pressed and cultivate_hold > 0.1:
			draw_arc(meditate_center, 36, -PI / 2, -PI / 2 + TAU * cultivate_hold / 0.6, 30, UiKit.PALE_GOLD, 3)
	if shown("sense"):
		ring(sense_center, 32)
		glyph("sense", sense_center)
	if shown("quick_use"):
		ring(quick_center, 26)
		var qid: String = c.inventory.quick_use
		if qid != "":
			var tex = SpriteCache.icon(qid)
			if tex: draw_texture_rect(tex, Rect2(quick_center - Vector2(18, 18), Vector2(36, 36)), false)
			UiKit.draw_outlined(self, str(c.inventory.count(qid)), quick_center + Vector2(4, 22), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 40)
			var cd := 0.0
			for k in c.pools.cooldowns:
				if str(k).begins_with("item:"): cd = maxf(cd, float(c.pools.cooldowns[k]))
			if cd > 0: draw_circle(quick_center, 24, Color(0, 0, 0, 0.5))
		else:
			glyph("quick_use", quick_center, 28)
	if shown("pet"):
		ring(pet_center, 26)
		glyph("pet", pet_center, 28)
	if shown("guard"):
		ring(guard_center, 26, Game.combat.timeline(c.id).guard)
		glyph("dodge" if Unlocks.is_unlocked(c.id, "dodge_dash") else "guard", guard_center, 28)
		var dcd = c.pools.cooldown("dodge")
		if dcd > 0: draw_arc(guard_center, 22, -PI / 2, -PI / 2 + TAU * (1.0 - dcd / 2.5), 20, UiKit.MIST, 3)

func _draw_progress(c) -> void:
	var cu: CultivatorState = c.cultivator
	var r := Rect2(0, 712, 1280, 8)
	draw_rect(r, Color(0, 0, 0, 0.6))
	var col = UiKit.GOLD if cu.state == "bottleneck" else UiKit.QI if c.pools.max_qi > 0 else Color("e8c89a")
	draw_rect(Rect2(r.position, Vector2(r.size.x * cu.progress_fraction(), r.size.y)), col)
	if cu.stored_qi > 0:
		draw_rect(Rect2(0, 710, 1280 * clampf(cu.stored_qi / maxf(1.0, cu.need()), 0, 1), 2), UiKit.PALE_GOLD)
	var pct := "%d%%" % int(cu.progress_fraction() * 100.0)
	UiKit.draw_outlined(self, pct, Vector2(560, 706), 14, col, HORIZONTAL_ALIGNMENT_CENTER, 160)

func _draw_log() -> void:
	var y := 596.0 if not left_handed else 596.0
	var x := 20.0 if not left_handed else 900.0
	for i in log_lines.size():
		var l: Dictionary = log_lines[i]
		var a = 1.0 if l.t < 5.0 else 6.0 - l.t
		UiKit.draw_text(self, str(l.text), Vector2(x, y + i * 20 - (log_lines.size() - 1) * 20 + 80), 16, Color(l.color, a), HORIZONTAL_ALIGNMENT_LEFT, 460)

func _draw_banner() -> void:
	if banner.text == "" or banner.t > 3.4 or not shown("room_banner"): return
	var a := clampf(banner.t / 0.3, 0, 1) * clampf((3.4 - banner.t) / 0.5, 0, 1)
	var slide := (1.0 - clampf(banner.t / 0.3, 0, 1)) * -30.0
	UiKit.draw_text(self, str(banner.text), Vector2(340, 76 + slide), 34, Color(UiKit.PALE_GOLD, a), HORIZONTAL_ALIGNMENT_CENTER, 600, true, true)
	if str(banner.sub) != "": UiKit.draw_text(self, str(banner.sub), Vector2(340, 100 + slide), 16, Color(UiKit.MIST, a), HORIZONTAL_ALIGNMENT_CENTER, 600)

func _draw_toasts() -> void:
	var y := 300.0
	for tt in toasts:
		var a := clampf(tt.t / 0.2, 0, 1) * clampf((3.2 - tt.t) / 0.4, 0, 1)
		var r := Rect2(820, y, 380, 44)
		var st = UiKit.style("toast")
		draw_style_box(st, r)
		var col = UiKit.PALE_GOLD if tt.kind in ["unlock", "gold"] else (UiKit.RED if tt.kind == "danger" else UiKit.BRIGHT_JADE)
		UiKit.draw_text(self, str(tt.text), r.position + Vector2(16, 28), 17, Color(col, a), HORIZONTAL_ALIGNMENT_LEFT, 350)
		y += 50

func _draw_boss() -> void:
	if Game.room_rt == null: return
	var boss: EnemyState = null
	for e in Game.room_rt.enemies.values():
		if e.alive and e.is_boss() and e.team == "enemy": boss = e
	if boss == null: return
	var r := Rect2(340, 118, 600, 14)
	draw_rect(r.grow(3), UiKit.INK)
	draw_rect(r, Color("3a1418"))
	draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(boss.pools.hp / boss.pools.max_hp, 0, 1), r.size.y)), UiKit.RED)
	UiKit.draw_outlined(self, Tx.t("hud.lv") % [boss.display_name(), boss.level], Vector2(340, 112), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 600)

func _draw_legacy() -> void:
	draw_style_box(frame_style, Rect2(22, 22, 310, 82))
	for row in 2:
		var y = 40 + row * 32
		var amount = player.hp if row == 0 else player.qi
		draw_string(font, Vector2(38, y + 13), Tx.t("hud.hp") if row == 0 else Tx.t("hud.qi"), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, GOLD)
		draw_rect(Rect2(75, y, 237, 16), Color("17242c"))
		draw_rect(Rect2(77, y + 2, 233 * amount / 100, 12), Color("ae5360") if row == 0 else Color("4bafaa"))
	draw_skill_scroll()
	ring(attack_center, 66, player.attack_time > 0)
	ring(jump_center, 32)
	ring(meditate_center, 32, player.meditating)
