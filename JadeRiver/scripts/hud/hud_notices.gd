class_name HudNotices
extends HudPart
## The game's events as the player reads them: the log's lines, the toasts, the captions and the room's banner
## (hud._on_event).
## A part of the HUD (audit 45, S6): HudPart says how a part works.

## World news (the calendar's events, the seasons, the Heaven Ranking's shifts, a treasure born elsewhere) reaches the
## player only once the calendar is theirs (the World menu's unlock, after the Prologue), never while a staged scene
## holds the stage, and only of a place they know: a room they have been in, and in the top-down world never one past
## the prototype's gate. The prototype's QA found a late-game event's toast ("The Drowned Shrine Surfaces · Abbot's
## Sanctum") over a brand-new player's village and the Hollow Night's timer.
func world_news(room := "") -> bool:
	var c = Game.active()
	if c == null or not Unlocks.is_unlocked(c.id, "world_menu"): return false
	if hud.scene_lock or (hud.scenes != null and hud.scenes.get("run") != null): return false
	if room != "" and (not Game.account.visited_rooms.has(room) or QuestAuthority.past_gate(c, room)): return false
	return true

## A calendar event's own room (or the first of its rooms) for world_news: "" when it names none.
func _event_room(ev: Dictionary) -> String:
	if str(ev.get("room", "")) != "": return str(ev.room)
	var rooms: Array = ev.get("rooms", [])
	for r in rooms:
		if Game.account.visited_rooms.has(str(r)) and not QuestAuthority.past_gate(Game.active(), str(r)): return str(r)
	return str(rooms[0]) if not rooms.is_empty() else ""

func _pet_name(uid: String) -> String:
	var c = Game.active()
	for pt in (c.pets if c else []):
		if str(pt.uid) == uid: return str(pt.name)
	return Tx.t("hud.your_spirit_animal")

## Wind-ups only from bosses and elites, notices only from monsters off screen.
func caption_worthy(name: String, p: Dictionary) -> bool:
	if name == "attack_started":
		var e = Game.room_rt.enemies.get(int(str(p.get("actor", "0")))) if Game.room_rt and str(p.get("actor", "")).is_valid_int() else null
		return e != null and (e.is_boss() or e.elite)
	if name == "enemy_aggro":
		var e2 = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
		var st = Game.actor_state(Game.active_id)
		return e2 != null and st != null and Game.room_rt.out_of_view(e2.plane, e2.altitude, st)
	return true

## Vibration on phones, when the player allows it (S40 haptics toggle).
func _buzz(ms: int) -> void:
	if Game.account.settings.get("haptics", true) and OS.has_feature("mobile"): Input.vibrate_handheld(ms)

## Does the world in view draw a plate for the way `portal_id` (which says its refusal itself)?
func _way_plate(portal_id: String) -> bool:
	if not is_instance_valid(hud.world) or not "portal_views" in hud.world: return false
	for pv in hud.world.portal_views:
		if is_instance_valid(pv) and str(pv.def.get("id", "")) == portal_id: return true
	return false

## What a spar opponent says at a moment of the spar ("start", "won", "lost"), quoted with their name, or "" when they
## have no line for it (enemies.json `spar_lines`).
static func spar_line(opponent: String, moment: String) -> String:
	var line := str(ContentDB.entry("enemies", opponent).get("spar_lines", {}).get(moment, ""))
	return "" if line == "" else "%s: “%s”" % [ContentDB.name_of("enemies", opponent), line]

## Before the quest tracker is revealed (the prologue), a new quest's first step rides under its toast...
func _first_step(qid: String) -> String:
	var c = Game.active()
	if c == null or hud.shown("quest_tracker") or not c.quests.active.has(qid): return ""
	var objs: Array = Game.quest.quest_def(c, qid).get("objectives", [])
	if objs.is_empty(): return ""
	var need := int(objs[0].get("count", 1))
	return str(objs[0].get("text", "")) + ("  0/%d" % need if need > 1 else "")

## ...and each step forward shows as its own toast: "Pick up Herbal Tea  2/3", ticked when done.
func _objective_toast(qid: String) -> void:
	var c = Game.active()
	if c == null or hud.shown("quest_tracker"): return
	var st: Dictionary = c.quests.active.get(qid, {})
	if st.is_empty(): return
	for line in Game.quest.steps_forward(c, qid, hud.objective_seen.get(qid, [])):
		var txt := str(line.text) + ("  %d / %d" % [int(line.have), int(line.need)] if int(line.need) > 1 else "")
		hud.toast(("✓ " if line.done else "") + txt, "quest")
	hud.objective_seen[qid] = (st.progress as Array).duplicate()

## Each frame: the log's lines and the toasts age and go, and so do the room's name, a fortune card, a caption and the
## reveal pulses.
func age(delta: float) -> void:
	for l in hud.log_lines: l.t += delta
	hud.log_lines = hud.log_lines.filter(func(l): return l.t < 6.0)
	# While a moment holds the screen (P6) the toasts wait under it, so the two never cover each other; a toast the top
	# stack had no room for waits for the one above it to go.
	if not hud.top_stack.moment_on_screen():
		var n := hud.toasts.size() if not hud.is_visible_in_tree() else maxi(1, hud.toasts_fit)
		for i in mini(n, hud.toasts.size()): hud.toasts[i].t += delta
		hud.toasts = hud.toasts.filter(func(tt): return tt.t < float(tt.get("life", 3.2)))
	if not hud.top_stack.band_on_top(): hud.banner.t += delta   # the room's name keeps its time for after a band over it
	hud.vignette.t = float(hud.vignette.t) + delta
	hud.caption.t = float(hud.caption.t) + delta
	for k in hud.pulses.keys():
		hud.pulses[k] -= delta
		if hud.pulses[k] <= 0: hud.pulses.erase(k)

func handle(name: String, p: Dictionary) -> void:
	if not hud.bound(): return
	if Hud.CAPTIONS.has(name) and Game.account.settings.get("captions", false) and caption_worthy(name, p):
		hud.caption = {"text": Tx.t("hud.caption." + str(Hud.CAPTIONS[name])), "t": 0.0}
	match name:
		"item_added":
			if str(p.get("actor", "")) == Game.active_id and hud.shown("system_log"):
				hud.add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(p.item)), int(p.count)], UiKit.quality_color(str(p.get("quality", "common"))))
			# A piece better than the one worn (or for an empty slot): the equip prompt offers it (EquipPrompt).
			if str(p.get("actor", "")) == Game.active_id and hud.shown("bag"): hud.equip_prompt.offer(p)
		"currency_changed":
			if int(p.get("delta", 0)) > 0 and hud.shown("system_log") and str(p.get("source", "")) != "sell":
				hud.add_log("+%d %s" % [int(p.delta), ContentDB.text("currency." + str(p.currency))], UiKit.PALE_GOLD)
		"system_unlocked":
			if p.get("toast", true) and str(p.get("label", "")) != "": hud.toast(Tx.t("hud.new") + str(p.label))
		"secret_art_learned":
			# S43: the first time a movement art is usable, its name and a one-line how-to.
			var art := ContentDB.entry("secret_arts", str(p.get("art", "")))
			if str(p.get("actor", "")) == Game.active_id and not art.is_empty():
				hud.toast(Tx.t("hud.new_art") + str(art.get("name", "")), "unlock", str(art.get("how_to", "")))
		"hud_element_revealed":
			hud.pulses[str(p.element)] = 1.2
		"quest_accepted":
			hud.toast(Tx.t("hud.quest") + str(p.get("name", "")), "quest", _first_step(str(p.get("quest", ""))))
		"quest_completed":
			# What the hand-in took from the bag, under the quest's name: "Gave 5 Willow Moss".
			hud.toast(Tx.t("hud.completed") + str(p.get("name", "")), "quest", Tx.t("hud.gave") % p.gave if str(p.get("gave", "")) != "" else "")
		"objective_progressed":
			if str(p.get("actor", "")) == Game.active_id: _objective_toast(str(p.get("quest", "")))
		"room_entered":
			var room := ContentDB.room(str(p.room))
			var zone := ContentDB.zone_of_room(str(p.room))
			hud.banner = {"text": str(room.get("name", "")), "sub": str(room.get("region_name", zone.get("name", ""))), "t": 0.0}
			hud.channel.object = ""
			# S17: a room's hazards and the attribute that answers them, once per entry.
			for hz in HazardRules.summary(Game.active(), room):
				hud.add_log(Tx.t("hud.hazard") % [hz.name, Tx.t("ui.cultivation." + str(hz.stat)), int(hz.need), int(hz.have)],
					UiKit.BRIGHT_JADE if hz.answered else UiKit.PALE_GOLD)
		"bottleneck_reached":
			hud.toast(Tx.t("hud.bottleneck_tap_cultivate_to_break") if not p.get("major", false) else Tx.t("hud.bottleneck_reached_see_the_cultivation"), "gold")
		"breakthrough_failed":
			hud.add_log(Tx.t("hud.breakthrough_failed") + ContentDB.text("failure." + str(p.failure_id)), UiKit.RED_TEXT)
		"achievement_unlocked":
			hud.toast(Tx.t("hud.achievement") + str(p.get("name", "")), "gold")
		"talisman_crafted":
			if p.get("spoiled", false): hud.add_log(Tx.t("hud.talisman_spoiled"), UiKit.MIST)
		"talisman_used":
			if str(p.get("kind", "")) == "movement": hud.add_log(Tx.t("hud.talisman_used") % ContentDB.item_name(str(p.get("item", ""))), UiKit.PALE_GOLD)
		"relic_restored":
			hud.toast(Tx.t("hud.relic_restored") % ContentDB.item_name(str(p.get("item", ""))), "gold")
		"natal_grew":
			if int(p.get("level", 0)) > 0: hud.add_log(Tx.t("hud.natal_grew") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("level", 0))], UiKit.GOLD)
		"natal_broken":
			hud.toast(Tx.t("hud.natal_broken") % ContentDB.item_name(str(p.get("item", ""))), "danger")
		"item_blooded":
			hud.add_log(Tx.t("hud.item_blooded") % ContentDB.item_name(str(p.get("item", ""))), UiKit.MIST)
		"loadout_swapped":
			hud.add_log(Tx.t("hud.loadout_swapped") % ContentDB.item_name(str(p.get("weapon", ""))), UiKit.PALE_GOLD)
		"sword_released":
			if int(p.get("swarm", 0)) > 0: hud.add_log(Tx.plural("hud.sword_swarm", int(p.swarm)) % int(p.swarm), UiKit.PALE_GOLD)
			else: hud.add_log(Tx.t("hud.sword_released"), UiKit.PALE_GOLD)
		"sword_returned":
			if str(p.get("reason", "")) != "recalled": hud.add_log(Tx.t("hud.swarm_returned" if p.get("swarm", false) else "hud.sword_returned"), UiKit.MIST)
		"sect_role_chosen":
			if str(p.get("actor", "")) == Game.active_id:
				hud.add_log(Tx.t("hud.sect_role_chosen") % str(ContentDB.entry("sect_roles", str(p.sect)).get("variants", {}).get(str(p.role), {}).get("name", "")), UiKit.PALE_GOLD)
		"sect_node_bought":
			if str(p.get("actor", "")) == Game.active_id:
				var br := TrainingSectAuthority.tree_branch(str(p.branch))
				var nodes: Array = br.get("nodes", [])
				var ni := int(p.node) - 1
				hud.add_log(Tx.t("hud.sect_node_bought") % [str(br.get("name", {}).get(str(p.sect), p.branch)), str(nodes[ni].get("desc", "")) if ni >= 0 and ni < nodes.size() else ""], UiKit.PALE_GOLD)
		"path_changed":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.path_blood_on" if p.get("on", false) else "hud.path_blood_off"), UiKit.RED_TEXT)
		"illusion_cast":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.illusion_cast"), UiKit.SOUL_TEXT)
		"illusion_broken":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("reason", "")) in ["struck", "time"]: hud.add_log(Tx.t("hud.illusion_broken"), UiKit.MIST)
		"soul_searched":
			if str(p.get("actor", "")) == Game.active_id:
				var mem := str(p.get("memory", ""))
				hud.add_log(Tx.t("hud.soul_searched") % str(ContentDB.entry("codex", mem).get("title", "")) if mem != "" else Tx.t("hud.soul_searched_none"), UiKit.SOUL_TEXT)
		"melody_changed":
			if str(p.get("actor", "")) == Game.active_id and not p.get("on", false) and str(p.get("reason", "")) in ["composure", "broken"]:
				hud.add_log(Tx.t("hud.melody_spent" if str(p.reason) == "composure" else "hud.melody_broken"), UiKit.MIST)
		"sword_intent_changed":
			if int(p.get("stacks", 0)) >= 10: hud.add_log(Tx.t("hud.sword_intent_full"), UiKit.GOLD)
		"artifact_detonated":
			hud.add_log(Tx.t("hud.detonated") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("targets", 0))], UiKit.RED_TEXT)
		"items_salvaged":
			hud.add_log(Tx.plural("hud.salvaged", (p.get("items", []) as Array).size()) % (p.get("items", []) as Array).size(), UiKit.PALE_GOLD)
		"enhancement_inherited":
			hud.add_log(Tx.t("hud.inherited") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("levels", 0))], UiKit.PALE_GOLD)
		"path_above_found":
			hud.toast(Tx.t("hud.path_above") % [int(p.get("found", 1)), int(p.get("total", 1))], "gold")
		"mail_received":
			if Unlocks.is_unlocked(Game.active_id, "mail"): hud.add_log(Tx.t("hud.a_letter_arrived"), UiKit.PALE_GOLD)
		"bag_full":
			hud.add_log(Tx.t("hud.your_gourd_is_full"), UiKit.RED_TEXT)
		"system_log":
			hud.add_log(str(p.text), UiKit.PAPER)
		"portal_blocked":
			# A shut way says why once, on its own plate at the way (WorldShared.request_portal lights it), not again in the
			# log (the prototype's QA saw "The road beyond is still being drawn." three times at once at the gate). A way with
			# no plate in view logs it, once while it repeats.
			var said := str(p.get("text", ""))
			if said == "" or _way_plate(str(p.get("portal", ""))): pass
			elif not hud.log_lines.is_empty() and str(hud.log_lines[-1].text) == said and float(hud.log_lines[-1].t) < 5.0: hud.log_lines[-1].t = 0.0
			else: hud.add_log(said, UiKit.MIST)
		"field_boss_spawned", "elite_spawned":
			var def := ContentDB.entry("enemies", str(p.def))
			hud.toast(Tx.t("hud.appears") % str(def.get("name", "")), "danger")
		"injury_added":
			hud.add_log(Tx.t("hud.injury_severity") % [str(p.kind).capitalize(), int(p.severity)], UiKit.RED_TEXT)
		"aptitude_revealed":
			hud.toast(Tx.t("hud.aptitude_revealed") % str(p.aptitude).replace("_", " ").capitalize(), "gold")
		"craft_completed":
			hud.add_log(Tx.t("hud.crafted") % [ContentDB.name_of("recipes", str(p.recipe)), str(p.quality).capitalize()], UiKit.quality_color(str(p.quality)))
			if str(p.quality).begins_with("pill_"): hud.toast(Tx.t("hud.rare_pill") % str(p.quality).capitalize(), "gold")
		"player_gravely_wounded":
			_buzz(200)
		"pets_bred":
			hud.toast(Tx.t("hud.pets_bred") % UiKit.span(float(p.get("hours", 24.0)) * 3600.0), "gold")
		"treasure_planted":
			hud.toast(Tx.t("hud.treasure_planted"), "gold")
		"treasure_harvested":
			hud.toast(Tx.t("hud.treasure_harvested") % ContentDB.item_name(str(p.get("item", ""))), "gold")
		"natural_treasure_used":
			hud.toast(Tx.t("hud.treasure_used." + str(p.treasure)), "gold")
		"treasure_used":
			if p.has("charges"): hud.add_log(Tx.plural("hud.talisman_charges", int(p.charges)) % int(p.charges) if int(p.charges) > 0 else Tx.t("hud.talisman_spent"), UiKit.PALE_GOLD)
		# Gap report G1: the heart, the ledger, the flames and debts that come due.
		"heart_demon_changed":
			if str(p.get("source", "")) == "merit_milestone" and str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.merit_milestone") % int(p.value), UiKit.GOLD)
			if p.get("step_crossed", false):
				if float(p.get("delta", 0)) > 0: hud.toast(Tx.t("hud.heart_demons_stir") % int(p.value), "danger")
				else: hud.add_log(Tx.t("hud.heart_demons_calm"), UiKit.BRIGHT_JADE)
		"merit_changed":
			if int(p.get("delta", 0)) > 0: hud.add_log(Tx.t("hud.merit_gained") % int(p.delta), UiKit.PALE_GOLD)
		"sin_changed":
			if int(p.get("delta", 0)) > 0: hud.add_log(Tx.t("hud.sin_gained") % int(p.delta), UiKit.RED_TEXT)
		# S49: alignment and Fame; a young master's challenge opens the Fame tab, where it is answered.
		"alignment_changed":
			if p.get("word_changed", false): hud.toast(Tx.t("hud.alignment_now") % Tx.t("ui.relations.align_" + str(p.word)), "gold")
		"fame_changed":
			if p.get("tier_up", false): hud.toast(Tx.t("hud.fame_tier") % Tx.t("ui.relations.fame_" + str(p.tier)), "unlock")
			elif int(p.get("delta", 0)) < 0: hud.add_log(Tx.t("hud.fame_lost") % -int(p.delta), UiKit.MIST)
			elif int(p.get("delta", 0)) > 0: hud.add_log(Tx.t("hud.fame_gained") % int(p.delta), UiKit.PALE_GOLD)
		"affinity_changed":
			if p.get("heart_up", false): hud.toast(Tx.plural("hud.heart_up", int(p.hearts)) % [ContentDB.name_of("npcs", str(p.npc)), int(p.hearts)], "gold")
		"bond_formed":
			hud.toast(Tx.t("hud.bond_" + str(p.kind)) % ContentDB.name_of("npcs", str(p.npc)), "unlock")
		"grudge_changed":
			var fname := ContentDB.name_of("factions", str(p.faction))
			if p.get("hunted", false) and int(p.get("delta", 0)) > 0: hud.toast(Tx.t("hud.grudge_hunted") % fname, "danger")
			elif int(p.get("value", 0)) == 0: hud.add_log(Tx.t("hud.grudge_settled") % fname, UiKit.BRIGHT_JADE)
			elif int(p.get("delta", 0)) > 0: hud.add_log(Tx.t("hud.grudge_rises") % fname, UiKit.RED_TEXT)
		"hunter_dispatched":
			hud.toast(Tx.t("hud.hunter_found_you") % ContentDB.name_of("enemies", str(p.enemy)), "danger")
		"bounty_taken":
			hud.add_log(Tx.t("hud.bounty_taken") % [ContentDB.name_of("enemies", str(p.bounty)), ContentDB.name_of("rooms", str(p.room))], UiKit.PALE_GOLD)
		"bounty_claimed":
			hud.toast(Tx.t("hud.bounty_claimed") % [ContentDB.name_of("enemies", str(p.bounty)), int(p.reward)], "gold")
		"foe_surrendered":
			if str(p.get("actor", "")) == Game.active_id: hud.open_page.emit("mercy", {"enemy": int(p.enemy), "def": str(p.def)})
		"foe_judged":
			hud.add_log(Tx.t("hud.foe_spared") % ContentDB.name_of("enemies", str(p.def)) if p.get("spared", false) else Tx.t("hud.foe_killed") % ContentDB.name_of("enemies", str(p.def)), UiKit.MIST)
		# S49 world calendar: what is under way, what is coming (a notification a day ahead), season and weather.
		"world_event_started":
			var ev := CalendarRules.event(str(p.event))
			var where := str(p.get("room", ""))
			if str(p.event) == "gathering_trial" and Game.active() != null: where = Game.calendar.trial_room(Game.active())   # your sect's terraces
			if world_news(where if where != "" else _event_room(ev)):
				hud.toast(Tx.t("hud.world_event_started") % str(ev.get("name", p.event)), "gold", ContentDB.name_of("rooms", where) if where != "" else "")
		"world_event_ended":
			var ev3 := CalendarRules.event(str(p.event))
			if world_news(_event_room(ev3)): hud.add_log(Tx.t("hud.world_event_ended") % str(ev3.get("name", p.event)), UiKit.MIST)
		"world_event_scheduled":
			var ev2 := CalendarRules.event(str(p.event))
			if world_news(str(p.get("room", "")) if str(p.get("room", "")) != "" else _event_room(ev2)):
				Notifier.schedule("world_event", str(ev2.get("name", p.event)), str(ev2.get("desc", "")), float(p.start))
		"season_changed":
			if world_news(): hud.toast(Tx.t("hud.season_changed") % ContentDB.name_of("seasons", str(p.season)), "gold")
		"weather_changed":
			if Game.room_rt != null and str(Game.room_rt.def.get("weather", "")) == str(p.region):
				hud.add_log(Tx.t("hud.weather_" + str(p.weather)), UiKit.MIST)
		"treasure_birth_announced":
			if world_news(str(p.room)) or (Game.room_rt != null and Game.room_rt.room_id == str(p.room)):
				hud.add_log(Tx.t("hud.treasure_birth") % [ContentDB.item_name(str(p.item)), ContentDB.name_of("rooms", str(p.room))], UiKit.PALE_GOLD)
		"treasure_claimed":
			hud.toast(Tx.t("hud.treasure_claimed") % ContentDB.item_name(str(p.item)), "gold")
		# S28 v1.2 the Hollow Tide at full: control lost for a moment, allies turned.
		"hollow_seizure":
			if str(p.get("actor", "")) == Game.active_id:
				hud.toast(Tx.t("hud.hollow_seizure"), "quest", Tx.t("hud.hollow_seizure_turned") % int(p.get("turned", 0)) if int(p.get("turned", 0)) > 0 else Tx.t("hud.hollow_seizure_sub"))
		# S50 Keeping Post: a post taken or left, a craft level, a pouch sewn, incense burned.
		"post_taken":
			if str(p.get("actor", "")) == Game.active_id:
				var what := Tx.t("hud.vigil") if str(p.craft) == "vigil" else str(ContentDB.entry("posts", str(p.craft)).get("short", ""))
				hud.add_log(Tx.t("hud.post_taken") % what, UiKit.BRIGHT_JADE)
		"post_left":
			if str(p.get("reason", "")) == "walked": hud.add_log(Tx.t("hud.post_left") % str(Game.character(str(p.actor)).name if Game.character(str(p.actor)) else ""), UiKit.MIST)
		"craft_leveled":
			if str(p.get("actor", "")) == Game.active_id:
				hud.toast(Tx.t("hud.craft_level") % [str(ContentDB.entry("posts", str(p.craft)).get("name", "")), int(p.level)], "gold", Tx.t("hud.craft_level_sub"))
		"pouch_sewn":
			hud.add_log(Tx.t("hud.pouch_sewn") % UiKit.fmt(int(float(p.get("cap", 0.0)))), UiKit.PALE_GOLD)
		"leaf_found":
			if p.get("new_tier", false): hud.toast(Tx.t("hud.leaf_tier") % [ContentDB.name_of("enemies", str(p.enemy)), int(p.tier)], "gold", Tx.t("hud.leaf_sub"))
		"snare_collected":
			if str(p.get("actor", "")) == Game.active_id:
				var n := 0
				for id in p.get("items", {}): n += int(p.items[id])
				hud.add_log(Tx.t("hud.snare_caught") % n if n > 0 else Tx.t("hud.snare_empty"), UiKit.PALE_GOLD if n > 0 else UiKit.MIST)
		"rite_held":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.rite_held") % int(p.wave), "gold", Tx.plural("hud.rite_wisps", int(p.wisps)) % int(p.wisps))
		"post_vow_learned":
			hud.add_log(Tx.t("hud.post_vow_learned") % str(Game.posts.post_vow(str(p.vow)).get("name", "")), UiKit.PALE_GOLD)
		"incense_burned":
			hud.add_log(Tx.t("hud.incense_burned") % UiKit.span(float(p.get("hours", 0.0)) * 3600.0), UiKit.PALE_GOLD)
		# S28 v1.2 Presence: held or let go, a new level, and two Presences meeting.
		"presence_toggled":
			if str(p.get("actor", "")) == Game.active_id:
				var why := str(p.get("reason", "choice"))
				if p.get("on", false): hud.add_log(Tx.t("hud.presence_on") % int(p.get("level", 1)), UiKit.PALE_GOLD)
				elif why == "soul": hud.add_log(Tx.t("hud.presence_soul"), UiKit.RED_TEXT)
				else: hud.add_log(Tx.t("hud.presence_off"), UiKit.MIST)
		"presence_leveled":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.presence_level") % int(p.level), "gold", Tx.t("hud.presence_level_sub"))
		"presence_clash":
			if str(p.get("actor", "")) == Game.active_id:
				hud.add_log(Tx.t("hud.presence_clash_" + str(p.get("winner", "even"))) % str(p.get("name", "")), UiKit.GOLD if str(p.get("winner", "")) == "you" else UiKit.RED_TEXT)
		"sphere_toggled":
			if str(p.get("actor", "")) == Game.active_id:
				var sw := str(p.get("reason", ""))
				if p.get("on", false): hud.add_log(Tx.t("hud.sphere_domain") if p.get("domain", false) else Tx.t("hud.sphere_on") % Tx.t("hud.el_" + str(p.get("element", "none"))), UiKit.PALE_GOLD)
				elif sw == "broken": hud.toast(Tx.t("hud.sphere_broken"), "danger", Tx.t("hud.sphere_broken_sub"))
				elif sw == "qi": hud.add_log(Tx.t("hud.sphere_qi"), UiKit.RED_TEXT)
				else: hud.add_log(Tx.t("hud.sphere_off"), UiKit.MIST)
		"sphere_clash":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("winner", "")) == "you":
				hud.toast(Tx.t("hud.sphere_clash_won") % str(p.get("name", "")), "gold", Tx.t("hud.sphere_clash_won_sub"))
		"presence_clash_ended":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.presence_clash_end"), UiKit.MIST)
		# v1.2 Phase D: the Copperjaw swarm and the lantern defence.
		"swarm_released":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.plural("hud.swarm_released", int(p.get("pop", 0))) % int(p.get("pop", 0)), UiKit.PALE_GOLD)
		"swarm_returned":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.swarm_returned"), UiKit.MIST)
		"swarm_queen":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.swarm_queen"), "gold", Tx.t("hud.swarm_queen_sub"))
		"swarm_fed":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.swarm_fed") % UiKit.span(float(p.get("food", 0)) * 3600.0), UiKit.MIST)
		"lantern_light":
			if str(p.get("actor", "")) == Game.active_id and float(p.get("light", 100.0)) <= 30.0 and int(p.get("near", 0)) > 0:
				hud.add_log(Tx.t("hud.lantern_guttering"), UiKit.RED_TEXT)
		# S43 rule 15: the rooftop thief and the Cloud Steps.
		"chase_started":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.chase_started"), "quest", Tx.t("hud.chase_hint"))
		"thief_caught":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.thief_caught") % float(p.get("seconds", 0.0)), "gold")
		"thief_escaped":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.thief_escaped"), "quest")
		"route_started":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.route_started"), "quest", Tx.plural("hud.route_hint", int(p.get("limit", 60))) % int(p.get("limit", 60)))
		"route_finished":
			if str(p.get("actor", "")) != Game.active_id: pass
			elif not p.get("finished", false): hud.toast(Tx.t("hud.route_failed"), "quest")
			else:
				var medal := str(p.get("medal", ""))
				hud.toast(Tx.t("hud.route_finished") % [float(p.seconds), int(p.rank), int(p.of)], "gold" if medal != "" else "quest",
					Tx.t("hud.route_medal_" + medal) if medal != "" else Tx.t("hud.route_best") % float(p.best))
		"gathering_trial_ranked":
			hud.toast(Tx.plural("hud.trial_ranked", int(p.points)) % [int(p.rank), int(p.of), int(p.points)], "gold" if int(p.rank) <= 3 else "quest")
		"rift_opened":
			hud.toast(Tx.t("hud.rift_opened") % int(p.level), "danger", Tx.t("hud.rift_hint"))
		"young_master_challenge":
			if str(p.get("actor", "")) == Game.active_id:
				hud.toast(Tx.t("hud.jealous_senior") if str(p.get("enemy", "")) == "jealous_senior" else Tx.t("hud.young_master"), "quest")
				hud.open_page.emit("relations", {"tab": "fame"})
		"tower_floor_cleared":
			if str(p.get("actor", "")) == Game.active_id:
				hud.toast(Tx.t("hud.tower_cleared") % int(p.floor), "gold", Tx.t("hud.tower_first") if p.get("first", false) else "")
		"tower_swept":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.plural("hud.tower_swept", int(p.floors)) % int(p.floors), UiKit.PALE_GOLD)
		"activity_chest_ready":
			hud.toast(Tx.plural("hud.activity_ready", int(p.points)) % int(p.points), "gold", Tx.t("hud.activity_ready_hint"))
		"activity_chest_claimed":
			hud.add_log(Tx.plural("hud.activity_claimed", int(p.points)) % int(p.points), UiKit.PALE_GOLD)
		"collection_seal_ready":   # decision 27
			hud.toast(Tx.t("hud.seal_ready") % [Tx.t("ui.codex.page_" + str(p.page)), Tx.t("ui.codex.seal_%d" % int(p.seal))], "gold", Tx.t("hud.seal_ready_hint"))
		"collection_seal_claimed":
			hud.toast(Tx.t("hud.seal_claimed") % [Tx.t("ui.codex.page_" + str(p.page)), Tx.t("ui.codex.seal_%d" % int(p.seal))], "gold",
				UiKit.seal_gift(ContentDB.collection_seal(str(p.page), int(p.seal))))
		"ranking_changed":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("beaten", "")) != "":
				hud.toast(Tx.t("hud.rank_climbed") % str(ContentDB.entry("rankings", str(p.beaten)).get("name", "")), "gold")
			elif str(p.get("actor", "")) == "" and world_news():
				hud.add_log(Tx.t("hud.ranking_shifts"), UiKit.MIST)
		"favour_changed":
			if str(p.get("actor", "")) == Game.active_id:
				if p.get("tier_up", false): hud.toast(Tx.t("hud.favour_tier") % Tx.t("ui.county.tier_" + str(p.tier)), "gold")
				elif int(p.get("delta", 0)) > 0: hud.add_log(Tx.t("hud.favour_up") % int(p.delta), UiKit.PALE_GOLD)
		"relief_donated":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.relief_given") % UiKit.fmt(int(p.silver)), UiKit.PALE_GOLD)
		# S49 territory: the spirit-stone mines (account level: every character hears of them).
		"mine_claimed":
			hud.toast(Tx.t("hud.mine_claimed") % ContentDB.name_of("territory", str(p.mine)), "gold", Tx.t("hud.mine_claimed_sub"))
		"mine_contested":
			var mname := ContentDB.name_of("territory", str(p.mine))
			var rname := str(Game.sect.rival(str(p.sect)).get("name", ""))
			hud.toast(Tx.t("hud.mine_contested") % [rname, mname], "danger", Tx.t("hud.mine_contested_sub") % UiKit.span(float(p.until) - Clock.now_utc()))
			Notifier.schedule("defence", Tx.t("hud.mine_notify_title"), Tx.t("hud.mine_contested") % [rname, mname], Clock.now_utc())
		"mine_defended":
			var dname := ContentDB.name_of("territory", str(p.mine))
			hud.toast(Tx.t("hud.mine_held_you") % dname if str(p.get("by", "")) == "you" else Tx.t("hud.mine_held_guards") % dname, "gold")
		"mine_lost":
			hud.toast(Tx.t("hud.mine_lost") % [str(Game.sect.rival(str(p.sect)).get("name", "")), ContentDB.name_of("territory", str(p.mine))], "danger",
				Tx.plural("hud.mine_lost_sub", int(p.stones)) % int(p.stones) if int(p.get("stones", 0)) > 0 else "")
		"mine_collected":
			hud.add_log(Tx.plural("hud.mine_collected", int(p.stones)) % [int(p.stones), ContentDB.name_of("territory", str(p.mine))], UiKit.PALE_GOLD)
		"pet_commanded":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.pet_commanded") % Tx.t("hud.pet_cmd_" + str(p.command)), UiKit.PALE_GOLD)
		"guqin_played":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.guqin_calm") % int(round(float(p.bonus) * 100.0)), UiKit.BRIGHT_JADE)
		"chess_solved":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.chess_right") if p.get("right", false) else Tx.t("hud.chess_wrong"), UiKit.PALE_GOLD if p.get("right", false) else UiKit.MIST)
		"auto_hunt_changed":
			if str(p.get("actor", "")) == Game.active_id:
				var why := str(p.get("reason", ""))
				if p.get("on", false): hud.add_log(Tx.t("hud.auto_hunt_on"), UiKit.BRIGHT_JADE)
				elif why not in ["off", "path"]: hud.add_log(Tx.t("sim.world.auto_hunt_" + why), UiKit.MIST)
				else: hud.add_log(Tx.t("hud.auto_hunt_off"), UiKit.MIST)
		"auto_path_started":
			# Decision 43: a walk to a place names the place ("the Storehouse"), else the room.
			var dest := str(p.get("name", "")) if str(p.get("name", "")) != "" else ContentDB.name_of("rooms", str(p.target))
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.auto_path_to") % dest, UiKit.PALE_GOLD)
		"auto_path_ended":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("reason", "")) != "cancelled":
				hud.add_log(Tx.t("hud.auto_path_" + str(p.get("reason", "arrived"))), UiKit.PALE_GOLD if str(p.get("reason", "")) == "arrived" else UiKit.MIST)
		"fortune_encounter":
			if str(p.get("actor", "")) == Game.active_id:
				var card := ContentDB.entry("fortune_deck", str(p.card))
				hud.vignette = {"title": str(card.get("name", "")), "text": str(card.get("text", "")), "t": 0.0}   # the fortune_card moment sounds it
		"heavenly_phenomenon":
			if str(p.get("actor", "")) == Game.active_id:
				hud.add_log(Tx.t("hud.phenomenon_" + str(p.get("kind", "cloud"))), UiKit.PALE_GOLD)
		"item_used":
			# A consumable names what it did (UiKit.use_parts): "Herbal Tea: +120 HP over 5 s". It reaches the player before
			# the log is revealed too (the prologue's tea), and the bars it touched flash.
			if str(p.get("actor", "")) == Game.active_id:
				var parts := UiKit.use_parts(p.get("effects", []), p.get("gains", {}))
				if not parts.is_empty():
					var words := PackedStringArray()
					for part in parts: words.append(str(part.text))
					hud.add_log(Tx.t("hud.use.line") % [ContentDB.item_name(str(p.get("item", ""))), " · ".join(words)], parts[0].color, true)
					for part in parts:
						if part.has("pool"): hud.pulses["bar:" + str(part.pool)] = 0.8
		"draught_expired":
			hud.toast(Tx.t("hud.draught_expired") % ContentDB.item_name(str(p.get("item", ""))), "danger")
		"flame_absorbed":
			hud.toast(Tx.t("hud.flame_absorbed") % ContentDB.item_name(str(p.flame)), "gold")
		"recipe_page_found":
			hud.toast(Tx.t("hud.recipe_page") % [ContentDB.name_of("recipes", str(p.recipe)), int(p.held), int(p.total)], "gold")
		"recipe_deduced":
			if p.get("success", false): hud.toast(Tx.t("hud.recipe_deduced") % ContentDB.name_of("recipes", str(p.recipe)), "unlock")
			else: hud.toast(Tx.t("hud.recipe_not_deduced") % ContentDB.name_of("recipes", str(p.recipe)), "danger")
		"experiment_result":
			var res := str(p.get("result", ""))
			if res.begins_with("learned:"): hud.toast(Tx.t("hud.experiment_found") % ContentDB.name_of("recipes", res.trim_prefix("learned:")), "unlock")
			elif res == "murky": hud.add_log(Tx.t("hud.experiment_murky"), UiKit.MIST)
		"guild_exam_started":
			hud.toast(Tx.t("hud.exam_started") % UiKit.span(float(p.get("time_s", 0))), "gold")
		"guild_exam_failed":
			hud.toast(Tx.t("hud.exam_failed"), "danger")
		"commission_completed":
			hud.add_log(Tx.plural("hud.commission_paid", int(p.get("paid", 0))) % int(p.get("paid", 0)) + (" " + Tx.t("hud.commission_capped") if p.get("capped", false) else ""), UiKit.PALE_GOLD)
		"pill_tribulation_result":
			if str(p.after) != str(p.before): hud.toast(Tx.t("hud.tribulation_changed") % Tx.t("ui.quality." + str(p.after)), "gold" if str(p.after) == "pill_soul" else "danger")
			else: hud.toast(Tx.t("hud.tribulation_held"), "gold")
		"pill_soul_flight":
			if not p.get("caught", false): hud.add_log(Tx.t("hud.soul_escaped"), UiKit.MIST)
		"furnace_blast":
			hud.toast(Tx.t("hud.furnace_blast") % int(p.get("durability", 0)), "danger")
		"debt_called":
			hud.toast(Tx.t("hud.debt_" + str(p.debt)), "quest")
		"room_event_flawless":
			hud.toast(Tx.t("hud.flawless") , "gold")
		"room_event_wave":
			if str(p.get("text", "")) != "": hud.add_log(str(p.text), UiKit.PALE_GOLD)
		"room_event_failed":
			if str(p.get("reason", "")) != "": hud.toast(Tx.t("hud.event_failed." + str(p.reason)), "danger")
		# S48: the body ladder, physiques and the core.
		"body_trial_passed":
			hud.toast(Tx.t("hud.body_trial_passed") % [ContentDB.name_of("body_tiers", str(p.tier)), ContentDB.item_name(str(p.get("bath", "")))], "gold")
		"physique_awakened":
			hud.toast(Tx.t("hud.physique_awakened") % ContentDB.name_of("physiques", str(p.physique)), "unlock")
		"core_graded":
			hud.toast(Tx.t("hud.core_graded") % int(p.grade), "gold")
		"tribulation_bolt":
			if str(p.phase) == "strike":
				Audio.play("thunder")
				if p.get("absorbed", false): hud.add_log(Tx.t("hud.bolt_absorbed"), UiKit.PALE_GOLD)
		"tribulation_result":
			if p.get("survived", false): hud.toast(Tx.t("hud.tribulation_survived") % [int(p.bolts) - int(p.struck), int(p.bolts)], "gold")
			else: hud.toast(Tx.t("hud.tribulation_failed"), "danger")
		"fate_offered":
			if str(p.get("actor", "")) == Game.active_id: hud.open_page.emit("fates", {})
		"fate_chosen":
			hud.toast(Tx.t("hud.fate_chosen") % ContentDB.name_of("fates", str(p.card)), "gold")
		"qi_deviation":
			hud.toast(Tx.t("hud.qi_deviation"), "danger", Tx.t("hud.qi_deviation_sub"))
		"inner_art_learned":
			hud.toast(Tx.t("hud.inner_art_learned") % ContentDB.name_of("inner_arts", str(p.art)), "unlock")
		"inner_art_equipped":
			if str(p.art) != "": hud.add_log(Tx.t("hud.inner_art_worn") % ContentDB.name_of("inner_arts", str(p.art)), UiKit.PALE_GOLD)
		"stance_changed":
			hud.add_log(Tx.t("hud.stance_on") % ContentDB.name_of("stances", str(p.stance)) if str(p.stance) != "" else Tx.t("hud.stance_off"), UiKit.PALE_GOLD)
		"vow_taken":
			hud.add_log(Tx.t("hud.vow_taken") % ContentDB.name_of("vows", str(p.vow)), UiKit.PALE_GOLD)
		"vow_broken":
			hud.toast(Tx.t("hud.vow_broken") % ContentDB.name_of("vows", str(p.vow)), "danger")
		"false_realm_changed":
			hud.add_log(Tx.t("hud.false_realm") % ContentDB.realm_label(str(p.realm)) if str(p.realm) != "" else Tx.t("hud.true_realm"), UiKit.MIST)
		"epiphany":
			hud.toast(Tx.t("hud.epiphany"), "gold", Tx.t("hud.epiphany_mastery") % ContentDB.name_of("techniques", str(p.technique)) if str(p.get("technique", "")) != "" else Tx.t("hud.epiphany_sub"))
		"boss_phase":
			if str(p.get("action", "")) == "self_detonate": hud.toast(Tx.t("hud.self_detonate"), "danger", Tx.t("hud.self_detonate_sub"))
		"soul_escaped":
			hud.toast(Tx.t("hud.soul_escaped_death"), "danger")
		"killing_intent_changed":
			if int(p.stacks) >= int(ContentDB.stat_const("killing_intent", {}).get("max", 10)): hud.add_log(Tx.t("hud.killing_intent_full"), UiKit.RED_TEXT)
		"combo_landed":
			hud.add_log(Tx.t("hud.combo") % [ContentDB.name_of("techniques", str(p.first)), ContentDB.name_of("techniques", str(p.second))], UiKit.GOLD)
		# Gap report G2: treasures and talismans.
		"beast_captured":
			hud.add_log(Tx.t("hud.beast_captured") % str(ContentDB.entry("enemies", str(p.def)).get("name", "")), UiKit.PALE_GOLD)
		"treasure_set":
			if str(p.item) != "": hud.add_log(Tx.t("hud.treasure_set") % [ContentDB.item_name(str(p.item)), int(p.slot) + 1], UiKit.PALE_GOLD)
		"pill_soul_awakened":
			hud.toast(Tx.t("hud.pill_soul") % Tx.t("hud.pill_soul_effect." + str(p.effect)), "gold")
		# A spar is a lesson: an opponent with lines of their own (Shen Lian) says what it teaches as it starts and ends.
		"spar_started":
			var said := spar_line(str(p.get("opponent", "")), "start")
			if said != "": hud.toast(Tx.t("hud.spar_begins"), "quest", said)
		"spar_ended":
			var won: bool = p.get("winner", "") == "player"
			hud.toast(Tx.t("hud.spar_won") if won else Tx.t("hud.spar_lost_try_again"), "quest", spar_line(str(p.get("opponent", "")), "won" if won else "lost"))
		"quest_ready":
			# Only a quest that waits to be handed in says so (one that completes itself, like the fair, is done by now).
			if str(Game.active().quests.active.get(str(p.quest), {}).get("state", "")) == "ready":
				hud.toast(Tx.t("hud.ready_to_hand_in") + str(Game.quest.quest_def(Game.active(), str(p.quest)).get("name", "")), "quest")
		"codex_entry_unlocked":
			hud.add_log(Tx.t("hud.codex") + str(ContentDB.entry("codex", str(p.entry)).get("title", "")), UiKit.PALE_GOLD)
		"teleport_discovered":
			hud.toast(Tx.t("hud.teleport_stone_attuned"), "gold")
		"hidden_portal_revealed":
			hud.toast(Tx.t("hud.a_hidden_path_opens"), "gold")
		"herb_ripening":
			hud.add_log(Tx.t("hud.herb_ripening") % ContentDB.item_name(str(p.item)), UiKit.GOLD)
		"herb_harvested":
			if p.get("perfect", false): hud.add_log(Tx.plural("hud.herb_perfect", int(p.age)) % [ContentDB.item_name(str(p.item)), int(p.age)], UiKit.GOLD)
		"seed_found":
			hud.toast(Tx.t("hud.seed_found") % ContentDB.item_name(str(p.seed)), "gold")
		"herb_planted":
			hud.add_log(Tx.t("hud.herb_planted") % ContentDB.item_name(str(p.herb)), UiKit.BRIGHT_JADE)
		"bed_watered":
			hud.add_log(Tx.t("hud.bed_watered") % int(float(p.progress) * 100.0), UiKit.BRIGHT_JADE)
		"bed_enriched":
			hud.toast(Tx.t("hud.bed_enriched") % Tx.t("ui.garden.grade_" + str(p.grade)), "gold")
		"herb_aged":
			hud.toast(Tx.plural("hud.herb_aged", int(p.age)) % [ContentDB.item_name(str(p.herb)), int(p.age)], "gold")
		"spring_bottled":
			hud.add_log(Tx.t("hud.spring_bottled") % int(p.left), UiKit.BRIGHT_JADE)
		"pet_wounded":
			hud.toast(Tx.t("hud.pet_wounded") % _pet_name(str(p.pet)), "danger", Tx.t("hud.pet_wounded_sub"))
		"pet_healed":
			hud.add_log(Tx.t("hud.pet_healed") % _pet_name(str(p.pet)), UiKit.BRIGHT_JADE)
		"bloodline_awakened":
			if int(p.get("step", 1)) >= 2: hud.toast(Tx.t("hud.bloodline_form") % [_pet_name(str(p.pet)), str(p.get("name", ""))], "unlock", Tx.t("hud.bloodline_form_sub"))
			else: hud.toast(Tx.t("hud.bloodline_skill") % [_pet_name(str(p.pet)), str(p.get("name", ""))], "unlock", Tx.t("hud.bloodline_skill_sub"))
		"contract_formed":
			var ck := str(p.get("kind", "equal"))
			hud.toast(Tx.t("hud.contract_formed_" + ck) % _pet_name(str(p.pet)), "unlock", Tx.t("hud.contract_formed_" + ck + "_sub"))
		"contract_offered":
			hud.toast(Tx.t("hud.contract_offered") % _pet_name(str(p.pet)), "unlock", Tx.t("hud.contract_offered_sub"))
		"pet_skill_cast":
			hud.add_log(Tx.t("hud.pet_skill_cast") % [_pet_name(str(p.pet)), str(p.get("skill", ""))], UiKit.PALE_GOLD)
		"beast_suppressed":
			hud.add_log(Tx.t("hud.beast_suppressed") % [_pet_name(str(p.pet)), ContentDB.name_of("enemies", str(p.get("def", "")))], UiKit.MIST)
		"egg_infused":
			hud.add_log(Tx.t("hud.egg_infused_" + str(p.get("kind", "blood"))), UiKit.BRIGHT_JADE)
		"party_changed":
			hud.add_log(Tx.plural("hud.party_changed", int(p.get("count", 1))) % int(p.get("count", 1)), UiKit.MIST)
		"pet_skill_learned":
			var rep := str(p.get("replaced", ""))
			if rep != "": hud.add_log(Tx.t("hud.pet_skill_replaced") % [_pet_name(str(p.pet)), ContentDB.name_of("pet_skill_books", str(p.skill)), ContentDB.name_of("pet_skill_books", rep)], UiKit.PALE_GOLD)
			else: hud.add_log(Tx.t("hud.pet_skill_learned") % [_pet_name(str(p.pet)), ContentDB.name_of("pet_skill_books", str(p.skill))], UiKit.BRIGHT_JADE)
		"pets_fused":
			hud.toast(Tx.t("hud.pets_fused") % _pet_name(str(p.keep)), "gold", Tx.t("hud.pets_fused_sub") % [(p.get("traits", []) as Array).size(), (p.get("skills", []) as Array).size(), int(p.get("purity", 0))])
		"pet_core_formed":
			hud.toast(Tx.t("hud.pet_core_formed") % [_pet_name(str(p.pet)), str(Game.pets.core_grade_def(str(p.get("grade", ""))).get("name", ""))], "unlock", Tx.t("hud.pet_core_formed_sub"))
		"pet_breakthrough":
			if p.get("success", false): hud.add_log(Tx.t("hud.pet_breakthrough_ok") % _pet_name(str(p.pet)), UiKit.BRIGHT_JADE)
			else: hud.toast(Tx.t("hud.pet_breakthrough_fail") % _pet_name(str(p.pet)), "danger", Tx.t("hud.pet_breakthrough_" + ("heart" if str(p.get("lost", "")) == "heart" else "wound")))
		"pet_fed":
			if p.get("trough", false): hud.add_log(Tx.t("hud.trough_fed") % _pet_name(str(p.pet)), UiKit.MIST)
		"arena_battle":
			if p.get("won", false): hud.toast(Tx.t("hud.arena_won") % int(p.get("rank", 11)), "gold", "")
			else: hud.add_log(Tx.t("hud.arena_lost"), UiKit.MIST)
		"arena_rewarded":
			hud.toast(Tx.plural("hud.arena_rewarded", int(p.get("spirit_stone", 0))) % [int(p.get("rank", 11)), int(p.get("spirit_stone", 0))], "gold", "")
		"beast_trial_result":
			if p.get("won", false): hud.toast(Tx.t("hud.trial_won"), "gold", ContentDB.item_name(str(p.get("item", ""))))
			else: hud.toast(Tx.t("hud.trial_lost"), "danger", "")
		"pet_swapped":
			hud.add_log(Tx.t("hud.pet_swapped") % _pet_name(str(p.pet)), UiKit.BRIGHT_JADE)
		"beast_king_spawned":
			hud.toast(Tx.t("hud.beast_king_spawned") % ContentDB.name_of("enemies", str(p.get("king", ""))), "danger", Tx.t("hud.beast_king_spawned_sub"))
		"king_nest_opened":
			hud.toast(Tx.t("hud.king_nest_opened"), "gold", Tx.t("hud.king_nest_opened_sub") % UiKit.span(float(p.get("minutes", 30)) * 60.0))
		"beast_tide_started":
			hud.toast(Tx.t("hud.beast_tide_started"), "danger", Tx.plural("hud.beast_tide_started_sub", int(float(p.get("duration", 90)))) % int(float(p.get("duration", 90))))
		"beast_tide_result":
			if p.get("won", false): hud.toast(Tx.t("hud.beast_tide_won"), "gold", Tx.t("hud.beast_tide_won_sub"))
		"pet_gear_changed":
			if str(p.get("item", "")) != "": hud.add_log(Tx.t("hud.pet_gear") % [_pet_name(str(p.pet)), ContentDB.item_name(str(p.item))], UiKit.MIST)
		"core_devoured":
			hud.add_log(Tx.t("hud.core_devoured") % [_pet_name(str(p.pet)), ContentDB.item_name(str(p.item)), int(float(p.xp))], UiKit.BRIGHT_JADE)
		"cores_sold":
			hud.add_log(Tx.plural("hud.cores_sold", int(p.stones)) % [int(p.count), ContentDB.item_name(str(p.item)), int(p.stones)], UiKit.PALE_GOLD)
		"beast_cleansed":
			hud.toast(Tx.t("hud.beast_cleansed") % ContentDB.name_of("enemies", str(p.def)), "gold", Tx.t("hud.beast_cleansed_sub"))
		"beast_subdued":
			hud.add_log(Tx.t("hud.beast_subdued") % [ContentDB.name_of("enemies", str(p.def)), UiKit.span(float(p.seconds))], UiKit.GOLD)
		"garden_raided":
			hud.toast(Tx.t("hud.raid_" + str(p.kind)) % ContentDB.item_name(str(p.herb)), "danger")
		"rack_started":
			hud.add_log(Tx.t("hud.rack_started") % [int(p.count), ContentDB.item_name(str(p.herb)), UiKit.span(float(p.seconds))], UiKit.BRIGHT_JADE)
		"rack_collected":
			hud.add_log(Tx.t("hud.rack_collected") % [int(p.count), ContentDB.item_name(str(p.herb)), Tx.t("ui.garden.done_" + str(p.kind))], UiKit.BRIGHT_JADE)
		"herb_appraised":
			if p.get("fake", false): hud.toast(Tx.t("hud.herb_fake") % ContentDB.item_name(str(p.item)), "danger")
		"transplant_result":
			if p.get("ok", false): hud.toast(Tx.t("hud.transplanted") % ContentDB.item_name(str(p.herb)), "gold", Tx.t("hud.transplanted_sub"))
			else: hud.toast(Tx.t("hud.transplant_died") % ContentDB.item_name(str(p.herb)), "danger")
		"guardian_spawned":
			hud.toast(Tx.t("hud.guardian") % ContentDB.name_of("enemies", str(p.enemy)), "danger", Tx.t("hud.guardian_sub"))
		"ambush_sprung":
			hud.toast(Tx.t("hud.ambush"), "danger", Tx.t("hud.ambush_concealed") if p.get("concealed", false) else Tx.t("hud.ambush_sub"))
		"meridian_gate_opened":
			hud.toast(Tx.t("hud.meridian_gate_opened") % str(p.get("channel", "")).replace("_", " ").capitalize(), "gold")
		"stability_changed":
			hud.add_log(Tx.t("hud.your_foundation_is") % str(p.get("word", "")).to_lower(), UiKit.MIST)
		"overflow_mailed":
			hud.add_log(Tx.t("hud.no_room_in_your_gourd"), UiKit.PALE_GOLD)
		"egg_hatched":
			hud.toast(Tx.t("hud.the_egg_hatched_a") % ContentDB.name_of("pets", str(p.species)), "gold")
		"bond_changed":
			hud.add_log(Tx.plural("hud.hearts", int(float(p.value))) % [_pet_name(str(p.pet)), int(float(p.value))], UiKit.RED_TEXT)
		"defence_warning":
			hud.toast(Tx.t("hud.raiders_at_the_gates_hold"), "danger")
		"defence_result":
			hud.toast(Tx.t("hud.the_raid_is_beaten_back") if p.get("won", false) else Tx.t("hud.the_raiders_broke_through"), "gold" if p.get("won", false) else "danger")
		"building_upgraded":
			hud.add_log(Tx.t("hud.reached_level") % [ContentDB.name_of("sect_buildings", str(p.building)), int(p.level)], UiKit.PALE_GOLD)
		"prestige_gained":
			if Game.sect.founded(): hud.add_log(Tx.t("hud.prestige") % int(p.amount), UiKit.PALE_GOLD)
		"expedition_returned":
			hud.add_log(Tx.t("hud.expedition_to") % [ContentDB.name_of("expeditions", str(p.region)), Tx.t("hud.returned_with_spoils") if p.get("success", false) else Tx.t("hud.came_back_empty_handed")], UiKit.PALE_GOLD)
		"reputation_changed":
			hud.add_log(Tx.t("hud.reputation") % [str(p.faction).replace("_", " ").capitalize(), int(p.value)], UiKit.MIST)
		"dismounted":
			if str(p.get("reason", "")) == "climb": hud.add_log(Tx.t("hud.dismount_climb"), UiKit.MIST)
			else: hud.add_log(Tx.t("hud.dismounted"), UiKit.RED_TEXT)
		"item_bound":
			hud.toast(Tx.t("hud.item_bound") % ContentDB.item_name(str(p.item)), "gold")
		"binding_interrupted":
			hud.add_log(Tx.t("hud.binding_broken"), UiKit.RED_TEXT)
		"artifact_spirit_awakened":
			hud.toast(Tx.t("hud.spirit_awake") % ContentDB.item_name(str(p.item)), "gold")
		"spirit_affinity_changed":
			# S47: every tenth point of affinity, and the gifts, are worth a line.
			var aff := float(p.get("affinity", 0.0))
			if str(p.get("why", "")) != "use" or int(aff) % 10 == 0:
				hud.add_log(Tx.t("hud.spirit_affinity") % [ContentDB.item_name(str(p.item)), int(aff)], UiKit.SOUL_TEXT)
		"artifact_spirit_grew":
			hud.toast(Tx.t("hud.spirit_grew") % [ContentDB.item_name(str(p.item)), int(p.get("level", 0))], "gold")
		"artifact_spirit_spoke":
			hud.add_log(Tx.t("hud.spirit_says") % [str(ContentDB.item(str(p.item)).get("spirit", {}).get("name", "")), str(p.get("line", ""))], UiKit.SOUL_TEXT)
		"artifact_skill_used":
			if p.get("awakened", false): hud.add_log(Tx.t("hud.awakened_skill") % str(p.get("skill", "")), UiKit.GOLD)
			else: hud.add_log(Tx.t("hud.spirit_skill") % str(p.get("skill", "")), UiKit.SOUL_TEXT)
		"trait_revealed":
			hud.toast(Tx.t("hud.shows_a_trait") % [_pet_name(str(p.pet)), ContentDB.name_of("pet_traits", str(p.trait))], "gold")
		"pet_level_up":
			hud.add_log(Tx.t("hud.reached_level") % [_pet_name(str(p.pet)), int(p.level)], UiKit.PALE_GOLD)
		"pet_retreated":
			hud.add_log(Tx.t("hud.your_spirit_animal_retreats_into"), UiKit.MIST)
		"pet_returned":
			hud.add_log(Tx.t("hud.your_spirit_animal_is_back"), UiKit.MIST)
		"companion_downed":
			hud.add_log(Tx.t("hud.is_down") % ContentDB.name_of("companions", str(p.get("companion", ""))), UiKit.RED_TEXT)
		"companion_revived":
			hud.add_log(Tx.t("hud.is_back_on_their_feet") % ContentDB.name_of("companions", str(p.get("companion", ""))), UiKit.MIST)
		"building_damaged":
			hud.toast(Tx.t("hud.raiders_damaged_your_repair_it") % ContentDB.name_of("sect_buildings", str(p.building)), "danger")
		"zone_ceiling_reached":
			hud.toast(Tx.t("hud.this_land_can_take_you"), "gold")
		"auction_bid_placed":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.auction_bid_placed") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("bid", 0))], UiKit.PALE_GOLD)
		"auction_outbid":
			if str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.auction_outbid") % ContentDB.item_name(str(p.get("item", ""))), UiKit.MIST)
		"auction_won":
			if str(p.get("actor", "")) == Game.active_id: hud.toast(Tx.t("hud.auction_won") % ContentDB.item_name(str(p.get("item", ""))), "gold")
