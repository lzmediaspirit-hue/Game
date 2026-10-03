class_name HudNotices
extends HudPart
## The game's events as the player reads them: the log's lines, the toasts, the captions and the room's banner
## (hud.on_event).
## A part of the HUD (audit 45, S6): HudPart says how a part works.

## An event as the player reads it. Its caption first (a sound written out, when captions are on). Then, for most
## events, the first of its rows in the cue table (data/cues.json, `to: "hud"`; tools/data/cues.py) whose `when`
## holds: a log line, a toast or both (play). The events below are code: they open a page, set the banner, a fortune
## card or the equip prompt, ask the world or the calendar, or add up what they say. An event is a row or an arm, never
## both (cue_tests checks).
func handle(name: String, p: Dictionary) -> void:
	if not hud.bound(): return
	if Hud.CAPTIONS.has(name) and Game.account.settings.get("captions", false) and caption_worthy(name, p):
		hud.caption = {"text": Tx.t("hud.caption." + str(Hud.CAPTIONS[name])), "t": 0.0}
	if not Cues.rows("hud", name).is_empty():
		play(Cues.pick("hud", name, p), p)
		return
	match name:
		"item_added":
			if str(p.get("actor", "")) == Game.active_id and hud.shown("system_log"):
				hud.add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(p.item)), int(p.count)], UiKit.quality_color(str(p.get("quality", "common"))))
			# A piece better than the one worn (or for an empty slot): the equip prompt offers it (EquipPrompt).
			if str(p.get("actor", "")) == Game.active_id and hud.shown("bag"): hud.equip_prompt.offer(p)
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
		"sect_role_chosen":
			if str(p.get("actor", "")) == Game.active_id:
				hud.add_log(Tx.t("hud.sect_role_chosen") % str(ContentDB.entry("sect_roles", str(p.sect)).get("variants", {}).get(str(p.role), {}).get("name", "")), UiKit.PALE_GOLD)
		"sect_node_bought":
			if str(p.get("actor", "")) == Game.active_id:
				var br := TrainingSectAuthority.tree_branch(str(p.branch))
				var nodes: Array = br.get("nodes", [])
				var ni := int(p.node) - 1
				hud.add_log(Tx.t("hud.sect_node_bought") % [str(br.get("name", {}).get(str(p.sect), p.branch)), str(nodes[ni].get("desc", "")) if ni >= 0 and ni < nodes.size() else ""], UiKit.PALE_GOLD)
		"portal_blocked":
			# A shut way says why once, on its own plate at the way (WorldShared.request_portal lights it), not again in the
			# log (the prototype's QA saw "The road beyond is still being drawn." three times at once at the gate). A way with
			# no plate in view logs it, once while it repeats.
			var said := str(p.get("text", ""))
			if said == "" or _way_plate(str(p.get("portal", ""))): pass
			elif not hud.log_lines.is_empty() and str(hud.log_lines[-1].text) == said and float(hud.log_lines[-1].t) < 5.0: hud.log_lines[-1].t = 0.0
			else: hud.add_log(said, UiKit.MIST)
		"craft_completed":
			hud.add_log(Tx.t("hud.crafted") % [ContentDB.name_of("recipes", str(p.recipe)), str(p.quality).capitalize()], UiKit.quality_color(str(p.quality)))
			if str(p.quality).begins_with("pill_"): hud.toast(Tx.t("hud.rare_pill") % str(p.quality).capitalize(), "gold")
		"player_gravely_wounded":
			_buzz(200)
		"treasure_used":
			if p.has("charges"): hud.add_log(Tx.plural("hud.talisman_charges", int(p.charges)) % int(p.charges) if int(p.charges) > 0 else Tx.t("hud.talisman_spent"), UiKit.PALE_GOLD)
		# Gap report G1: the heart, the ledger, the flames and debts that come due.
		"heart_demon_changed":
			if str(p.get("source", "")) == "merit_milestone" and str(p.get("actor", "")) == Game.active_id: hud.add_log(Tx.t("hud.merit_milestone") % int(p.value), UiKit.GOLD)
			if p.get("step_crossed", false):
				if float(p.get("delta", 0)) > 0: hud.toast(Tx.t("hud.heart_demons_stir") % int(p.value), "danger")
				else: hud.add_log(Tx.t("hud.heart_demons_calm"), UiKit.BRIGHT_JADE)
		"foe_surrendered":
			if str(p.get("actor", "")) == Game.active_id: hud.open_page.emit("mercy", {"enemy": int(p.enemy), "def": str(p.def)})
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
		"post_left":
			if str(p.get("reason", "")) == "walked": hud.add_log(Tx.t("hud.post_left") % str(Game.character(str(p.actor)).name if Game.character(str(p.actor)) else ""), UiKit.MIST)
		"snare_collected":
			if str(p.get("actor", "")) == Game.active_id:
				var n := 0
				for id in p.get("items", {}): n += int(p.items[id])
				hud.add_log(Tx.t("hud.snare_caught") % n if n > 0 else Tx.t("hud.snare_empty"), UiKit.PALE_GOLD if n > 0 else UiKit.MIST)
		"post_vow_learned":
			hud.add_log(Tx.t("hud.post_vow_learned") % str(Game.posts.post_vow(str(p.vow)).get("name", "")), UiKit.PALE_GOLD)
		"lantern_light":
			if str(p.get("actor", "")) == Game.active_id and float(p.get("light", 100.0)) <= 30.0 and int(p.get("near", 0)) > 0:
				hud.add_log(Tx.t("hud.lantern_guttering"), UiKit.RED_TEXT)
		"young_master_challenge":
			if str(p.get("actor", "")) == Game.active_id:
				hud.toast(Tx.t("hud.jealous_senior") if str(p.get("enemy", "")) == "jealous_senior" else Tx.t("hud.young_master"), "quest")
				hud.open_page.emit("relations", {"tab": "fame"})
		"collection_seal_claimed":
			hud.toast(Tx.t("hud.seal_claimed") % [Tx.t("ui.codex.page_" + str(p.page)), Tx.t("ui.codex.seal_%d" % int(p.seal))], "gold",
				UiKit.seal_gift(ContentDB.collection_seal(str(p.page), int(p.seal))))
		"ranking_changed":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("beaten", "")) != "":
				hud.toast(Tx.t("hud.rank_climbed") % str(ContentDB.entry("rankings", str(p.beaten)).get("name", "")), "gold")
			elif str(p.get("actor", "")) == "" and world_news():
				hud.add_log(Tx.t("hud.ranking_shifts"), UiKit.MIST)
		"mine_contested":
			var mname := ContentDB.name_of("territory", str(p.mine))
			var rname := str(Game.sect.rival(str(p.sect)).get("name", ""))
			hud.toast(Tx.t("hud.mine_contested") % [rname, mname], "danger", Tx.t("hud.mine_contested_sub") % UiKit.span(float(p.until) - Clock.now_utc()))
			Notifier.schedule("defence", Tx.t("hud.mine_notify_title"), Tx.t("hud.mine_contested") % [rname, mname], Clock.now_utc())
		"mine_lost":
			hud.toast(Tx.t("hud.mine_lost") % [str(Game.sect.rival(str(p.sect)).get("name", "")), ContentDB.name_of("territory", str(p.mine))], "danger",
				Tx.plural("hud.mine_lost_sub", int(p.stones)) % int(p.stones) if int(p.get("stones", 0)) > 0 else "")
		"fortune_encounter":
			if str(p.get("actor", "")) == Game.active_id:
				var card := ContentDB.entry("fortune_deck", str(p.card))
				hud.vignette = {"title": str(card.get("name", "")), "text": str(card.get("text", "")), "t": 0.0}   # the fortune_card moment sounds it
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
		"experiment_result":
			var res := str(p.get("result", ""))
			if res.begins_with("learned:"): hud.toast(Tx.t("hud.experiment_found") % ContentDB.name_of("recipes", res.trim_prefix("learned:")), "unlock")
			elif res == "murky": hud.add_log(Tx.t("hud.experiment_murky"), UiKit.MIST)
		"pill_tribulation_result":
			if str(p.after) != str(p.before): hud.toast(Tx.t("hud.tribulation_changed") % Tx.t("ui.quality." + str(p.after)), "gold" if str(p.after) == "pill_soul" else "danger")
			else: hud.toast(Tx.t("hud.tribulation_held"), "gold")
		"tribulation_bolt":
			if str(p.phase) == "strike":
				Audio.play("thunder")
				if p.get("absorbed", false): hud.add_log(Tx.t("hud.bolt_absorbed"), UiKit.PALE_GOLD)
		"tribulation_result":
			if p.get("survived", false): hud.toast(Tx.t("hud.tribulation_survived") % [int(p.bolts) - int(p.struck), int(p.bolts)], "gold")
			else: hud.toast(Tx.t("hud.tribulation_failed"), "danger")
		"fate_offered":
			if str(p.get("actor", "")) == Game.active_id: hud.open_page.emit("fates", {})
		"killing_intent_changed":
			if int(p.stacks) >= int(ContentDB.stat_const("killing_intent", {}).get("max", 10)): hud.add_log(Tx.t("hud.killing_intent_full"), UiKit.RED_TEXT)
		"treasure_set":
			if str(p.item) != "": hud.add_log(Tx.t("hud.treasure_set") % [ContentDB.item_name(str(p.item)), int(p.slot) + 1], UiKit.PALE_GOLD)
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
		"contract_formed":
			var ck := str(p.get("kind", "equal"))
			hud.toast(Tx.t("hud.contract_formed_" + ck) % _pet_name(str(p.pet)), "unlock", Tx.t("hud.contract_formed_" + ck + "_sub"))
		"pet_core_formed":
			hud.toast(Tx.t("hud.pet_core_formed") % [_pet_name(str(p.pet)), str(Game.pets.core_grade_def(str(p.get("grade", ""))).get("name", ""))], "unlock", Tx.t("hud.pet_core_formed_sub"))
		"prestige_gained":
			if Game.sect.founded(): hud.add_log(Tx.t("hud.prestige") % int(p.amount), UiKit.PALE_GOLD)
		"spirit_affinity_changed":
			# S47: every tenth point of affinity, and the gifts, are worth a line.
			var aff := float(p.get("affinity", 0.0))
			if str(p.get("why", "")) != "use" or int(aff) % 10 == 0:
				hud.add_log(Tx.t("hud.spirit_affinity") % [ContentDB.item_name(str(p.item)), int(aff)], UiKit.SOUL_TEXT)
		"artifact_spirit_spoke":
			hud.add_log(Tx.t("hud.spirit_says") % [str(ContentDB.item(str(p.item)).get("spirit", {}).get("name", "")), str(p.get("line", ""))], UiKit.SOUL_TEXT)

## A row of the cue table for the HUD ({} when none of its event's rows holds): its steps in order, each a line of the
## log ({"log": text, "color": token, "always": bool}) or a toast ({"toast": text, "style": kind, "sub": text}).
func play(row: Dictionary, p: Dictionary) -> void:
	for s in row.get("do", []):
		if s.has("log"): hud.add_log(Cues.text(s["log"], p), Cues.color(s["color"], p), bool(s.get("always", false)))
		elif s.has("toast"): hud.toast(Cues.text(s["toast"], p), str(s.get("style", "unlock")), Cues.text(s["sub"], p) if s.has("sub") else "")

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
