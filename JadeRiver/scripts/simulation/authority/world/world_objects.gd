extends "res://scripts/simulation/authority/world/world_part.gd"
## World · room objects: whether one shows to a character and is open to it, the states they keep (opened, broken,
## depleted and regrowing), blows on jars and training posts, jade gravity switches, shrines attuned in passing and the
## first Spirit Fruit's announcement.

## S45 treasure births (on the S49 calendar): World announces the fruit ripening in its room.
func on_world_event_started(p: Dictionary) -> void:
	if str(p.get("event", "")) != "treasure_birth": return
	emit("treasure_birth_announced", {"room": str(p.get("room", "")), "item": str(CalendarRules.event("treasure_birth").get("item", "spirit_fruit")),
		"ends": float(p.get("ends", 0.0)), "first": false})

## The character's own first Spirit Fruit (an early surprise, CalendarAuthority.open_first_fruit): announced once, the
## moment its tree shows in the room the character stands in (on arrival, or as The Willow Path is done there).
func announce_first_fruit(_p := {}) -> void:
	var c = game.active()
	if c == null or game.room_rt == null or c.quests.has_flag("first_fruit_seen"): return
	for o in game.room_rt.def.get("objects", []):
		if not o.get("first", false) or str(o.get("type", "")) != "treasure_birth" or not object_visible(c, o): continue
		game.quest.apply_flag(c.id, "first_fruit_seen")
		emit("treasure_birth_announced", {"room": game.room_rt.room_id, "item": str(CalendarRules.event("treasure_birth").get("item", "spirit_fruit")),
			"ends": 0.0, "first": true})
		return

## Crafting gathered a node: World owns room objects, their regrowth and the character's memory of them.
func apply_node_depleted(c, object_id: String, regrow_s: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var st: Dictionary = rt.objects.get(object_id, {"state": "ready"})
	st.state = "depleted"
	st.timer = regrow_s
	rt.objects[object_id] = st
	world.room_mem(c, rt.room_id).nodes[object_id] = Clock.now_utc() + regrow_s
	emit("node_depleted", {"room": rt.room_id, "object": object_id})

func restore_object_states(c, rt: RoomRuntime) -> void:
	var mem := world.room_mem(c, rt.room_id)
	var now := Clock.now_utc()
	for o in rt.def.get("objects", []):
		var id := str(o.get("id", ""))
		var st := {"state": "ready", "timer": 0.0, "hits": 0}
		if o.type in ["herb_patch", "ore_vein", "star_sight", "insect_swarm"] and float(mem.nodes.get(id, 0.0)) > now:
			st.state = "depleted"
			st.timer = float(mem.nodes[id]) - now
		if o.type in ["chest"] and mem.opened.has(open_key(o)): st.state = "open"
		if o.type == "pickup" and mem.opened.has(id): st.state = "open"   # taken once (Aunt Ping's teas stay taken on a reload)
		if o.type in WorldAuthority.BREAKABLES and float(mem.broken.get(id, 0.0)) > now:
			st.state = "broken"
			st.timer = float(mem.broken[id]) - now
		rt.objects[id] = st

## Each tick: a depleted node or a broken jar whose timer has run is ready again.
func tick_regrowth(rt: RoomRuntime, delta: float) -> void:
	for id in rt.objects:
		var os: Dictionary = rt.objects[id]
		if os.get("state", "ready") in ["depleted", "broken"] and float(os.get("timer", 0.0)) > 0.0:
			os.timer = float(os.timer) - delta
			if float(os.timer) <= 0.0:
				os.state = "ready"
				os.hits = 0
				emit("node_regrown", {"room": rt.room_id, "object": id})

func object_visible(c, o: Dictionary) -> bool:
	if o.has("visible_if") and not RequirementRules.passes(o.visible_if, game.ctx(c)): return false
	if str(o.get("type", "")) == "npc" and in_spar(str(o.get("npc", ""))): return false
	if o.has("hidden_if") and RequirementRules.passes(o.hidden_if, game.ctx(c)): return false
	if str(o.get("type", "")) == "egg_nest" and world.nests.nest_closes(str(o.get("king", ""))) <= Clock.now_utc(): return false   # S46: only while open
	# S43 rule 15: a rooftop thief is on his street until you have chased him today (caught or not).
	if o.has("chase") and c != null and world.races.chase_done_today(c, str(o.id)) and str(world.chases.get(c.id, {}).get("object", "")) != str(o.id): return false
	return true

## A person fighting a spar (QuestAuthority.start_spar): their partner figure is them while the spar lasts; at its end
## the partner is gone at once (EnemyAuthority._finish_spar) and the person stands in their place again.
func in_spar(npc: String) -> bool:
	if npc == "" or game.room_rt == null: return false
	for e in game.room_rt.enemies.values():
		if e.alive and e.def.get("spar", false) and str(e.ai.get("partner", "")) == npc: return true
	return false

## A sealed climbable (S43: library floors, lofts) opens when its requirement is met.
func climbable_open(c, climbable: Dictionary) -> Dictionary:
	if climbable.has("requires") and not world.debug_open_ways and not RequirementRules.passes(climbable.requires, game.ctx(c)):
		return {"ok": false, "text": str(climbable.get("locked_text", RequirementRules.first_failure_text(climbable.requires, game.ctx(c))))}
	return {"ok": true}

## A chest that `reopens` with a calendar event is opened once per occurrence (S49); any other chest once.
func open_key(o: Dictionary) -> String:
	if str(o.get("reopens", "")) == "": return str(o.id)
	# S49 fortune: the Hidden Grotto's chest fills again for each fall that ends there.
	if str(o.reopens) == "fortune":
		var fc = game.active()
		return "%s@%d" % [str(o.id), int(fc.relations.fortune.get("grotto_n", 0)) if fc != null else 0]
	var occ: Dictionary = game.calendar.active_of(str(o.reopens))
	return "%s@%d" % [str(o.id), int(occ.get("k", -1))]

func object_available(c, o: Dictionary) -> Dictionary:
	if not object_visible(c, o): return {"ok": false, "text": "", "hidden": true}
	if o.has("requires") and not RequirementRules.passes(o.requires, game.ctx(c)):
		return {"ok": false, "locked": true, "text": str(o.get("locked_text", RequirementRules.first_failure_text(o.requires, game.ctx(c))))}
	var st: Dictionary = game.room_rt.objects.get(str(o.id), {})
	if st.get("state", "ready") in ["depleted", "broken", "open"]: return {"ok": false, "text": "", "spent": true}
	# S45: a rare herb out of its season lies dormant (seasons never gate progression).
	if o.type == "herb_patch" and not HerbRules.in_season(o, Clock.now_utc()):
		return {"ok": false, "text": Tx.t("sim.world.herb_dormant") % ContentDB.name_of("seasons", str(o.season)), "dormant": true}
	if o.type == "egg_nest" and c.quests.has_flag(world.nests.nest_flag(str(o.get("king", "")))): return {"ok": false, "text": Tx.t("sim.world.nest_taken")}
	if o.type == "beast_trial_stone" and int(c.cooldowns.get("grove_day", -1)) == Clock.reset_day(Clock.now_utc()):
		return {"ok": false, "text": Tx.t("sim.world.grove_done")}
	if o.type == "beast_tide_drum" and not world.nests.tide_due(c):
		return {"ok": false, "text": Tx.t("sim.world.tide_not_due") % Tx.span(maxi(1, world.nests.tide_days_left(c)) * 86400.0)}
	return {"ok": true, "text": ""}

func hittable_objects(pv: Dictionary, facing: int, hitbox: Dictionary) -> Array:
	var out: Array = []
	var c = game.active()
	if game.room_rt == null or c == null: return out
	for o in game.room_rt.def.get("objects", []):
		if not (o.type in WorldAuthority.BREAKABLES or o.type in WorldAuthority.TRAINING): continue
		if not object_visible(c, o): continue
		var st: Dictionary = game.room_rt.objects.get(str(o.id), {})
		if st.get("state", "ready") == "broken": continue
		var at: Array = o.get("at", [0, 0])
		var view := {"x": float(at[0]), "y": float(at[1]), "alt": float(o.get("alt", 0)), "half_width": 14.0, "height": 40.0}
		if CombatAuthority.hit_test(pv, facing, hitbox, view): out.append(o)
	return out

func apply_object_hit(actor_id: String, o: Dictionary) -> void:
	var c = game.character(actor_id)
	var id := str(o.id)
	var st: Dictionary = game.room_rt.objects.get(id, {"state": "ready", "hits": 0})
	st.hits = int(st.get("hits", 0)) + 1
	game.room_rt.objects[id] = st
	var at: Array = o.get("at", [0, 0])
	emit("object_hit", {"actor": actor_id, "object": id, "type": o.type, "x": float(at[0]), "y": float(at[1]), "hits": st.hits})
	if o.type in WorldAuthority.BREAKABLES and int(st.hits) >= int(o.get("hp", 1)):
		st.state = "broken"
		st.timer = float(o.get("respawn_s", 300))
		world.room_mem(c, game.room_rt.room_id).broken[id] = Clock.now_utc() + st.timer
		var drop := LootRules.roll(str(o.get("loot", "jar_valley_low")), Rng.stream(actor_id, "loot"), int(o.get("level", 1)),
			c.stats.value("drop_rate"), c.stats.value("coin_find"), {"no_equipment": true})
		world.loot.drop_loot(c, drop, Vector2(float(at[0]), float(at[1])), 0.0, "jar")
		emit("object_broken", {"actor": actor_id, "object": id, "type": o.type})

## v1.2 gravity switches: a jade switch turns its room's low-gravity volumes on or off (every volume tied to it).
func toggle_gravity(c, object_id: String) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	var st: Dictionary = game.room_rt.objects.get(object_id, {})
	var on := str(st.get("state", "up")) != "down"
	st["state"] = "down" if on else "up"
	game.room_rt.objects[object_id] = st
	game.room_rt.geometry.set_switch(object_id, on)
	emit("gravity_switched", {"actor": c.id, "room": str(game.room_rt.room_id), "switch": object_id, "on": on})
	emit("system_used", {"actor": c.id, "system": "gravity_switch"})
	return ok({"on": on, "text": world.t("sim.world.gravity_on") if on else world.t("sim.world.gravity_off")})

## Walking past a shrine is enough for it to remember you as a revival point
## (praying still heals). Nobody loses their respawn by forgetting to press Pray.
func attune_shrines(c, rt: RoomRuntime, st: ActorState) -> void:
	if st == null or c.last_shrine.get("room", "") == rt.room_id: return
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) != "shrine": continue
		var at: Array = o.get("at", [0, 0])
		if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) <= 160.0:
			c.last_shrine = {"room": rt.room_id, "x": float(at[0]), "y": float(at[1]), "object": str(o.id)}
			emit("shrine_attuned", {"actor": c.id, "room": rt.room_id, "object": str(o.id)})
			GameEvents.save_pending = true
			return
