class_name WorldContext
extends WorldPart
## WorldAuthority's part: using a thing: interact (the intent) and the context button (Part 9.9), which offers the thing
## in reach that claims it most, with its verb.

## The world's resource nodes: things worked for a yield or a training (a herb, a vein, a pool, a swarm, a trail, a
## star ring, a bed or plot, a Temper drum). While the craft or the body level they ask is not there yet, they stay in
## the world as a promise and never take the context button (query_context, resource_node).
const RESOURCE_NODES := ["herb_patch", "ore_vein", "fishing_spot", "insect_swarm", "beast_trail", "star_sight", "garden_bed", "treasure_plot"]

## `pick` (S45): go straight to the harvest at a rare herb, past the Pick / Dig it up choice.
func interact(c, object_id: String, pick := false) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	var o = game.room_rt.object_def(object_id)
	if o.is_empty(): return fail("unknown_object")
	var st: ActorState = game.actor_state(c.id)
	var at: Array = o.get("at", [0, 0])
	if st != null and st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) > reach_of(o) + 20.0:
		return fail("too_far")
	if st != null and absf(st.altitude - float(o.get("alt", 0.0))) > WorldAuthority.REACH_ALT:
		return fail("out_of_reach", {"text": Tx.t("sim.world.out_of_reach_from_here")})
	var avail := world.object_available(c, o)
	if avail.get("dormant", false) and not game.account.codex.has("seasons"): game.quest.apply_codex("seasons")
	if not avail.ok and o.type != "npc":
		return fail("unavailable", {"text": avail.text})
	if o.type == "herb_patch" and o.has("ripen") and not game.account.codex.has("rare_herbs"): game.quest.apply_codex("rare_herbs")
	var result := ok({"type": o.type})
	match str(o.type):
		"npc":
			if o.has("chase"): return world.start_chase(c, o)   # S43 rule 15: the rooftop thief bolts
			return game.quest.talk(c, str(o.npc))
		"route_stone":
			return world.start_run(c, o)
		"shrine":
			c.last_shrine = {"room": game.room_rt.room_id, "x": float(at[0]), "y": float(at[1]), "object": object_id}
			game.combat.apply_resource_change(c.id, "hp", c.pools.max_hp, "shrine")
			if c.pools.max_qi > 0: game.combat.apply_resource_change(c.id, "qi", c.pools.max_qi, "shrine")
			GameEvents.save_pending = true
			result.text = Tx.t("sim.world.the_shrine_remembers_you_wounds")
		"herb_patch", "ore_vein", "fishing_spot", "star_sight", "insect_swarm":
			# S45: with a Spirit Spade and Expert gathering, a rare herb can be dug up whole instead of picked.
			if o.type == "herb_patch" and o.has("ripen") and not pick and game.crafting.can_transplant(c):
				return ok({"dialogue": {"npc": "", "speaker": ContentDB.item_name(str(o.item)), "portrait": {}, "lines": [Tx.t("sim.world.rare_herb_choice")],
					"choices": [{"text": Tx.t("sim.world.pick_it"), "page": "_harvest", "args": {"object": object_id}},
						{"text": Tx.t("sim.world.dig_it_up") % int(round(game.crafting.transplant_death(c) * 100.0)), "intent": {"type": "transplant", "object": object_id}},
						{"text": Tx.t("sim.world.leave_it"), "close": true}]}})
			return game.crafting.gather(c, o)
		"starsea_dock":
			return world.set_sail(c, str(o.get("route", "")))
		"gravity_switch":
			return world.toggle_gravity(c, object_id)   # v1.2 the Orbit Ruins' jade switches
		"beast_trail":
			return ok({"dialogue": game.posts.trail_dialogue(c, o)})   # S50 V10c Beast Snaring
		"ancestral_altar":
			return ok({"dialogue": game.posts.altar_dialogue(c, o)})   # S50 V10c Ancestral Rites
		"chest":
			var s: Dictionary = game.room_rt.objects.get(object_id, {})
			s.state = "open"
			world.room_mem(c, game.room_rt.room_id).opened[world.open_key(o)] = true
			var chest_lv := int(o.get("level", 0))
			if chest_lv <= 0: chest_lv = ProgressionRules.level(c)   # a chest of no fixed level fits its finder (the grotto)
			var drop := LootRules.roll(str(o.get("loot", "chest_valley")), Rng.stream(c.id, "loot"), chest_lv,
				c.stats.value("drop_rate"), c.stats.value("coin_find"))
			world.loot.drop_loot(c, drop, Vector2(float(at[0]), float(at[1])), "chest")
		"transfer_array":
			# Decision 42: the node learns the token, and the travel picker asks where to (array_view).
			world.attune_array(c, object_id)
			result.open_page = "transfer_array"
			result.page_args = {"object": object_id}
		"teleport_stone":
			var sid := str(o.get("stone", object_id))
			if not game.account.teleports.has(sid):
				game.account.teleports[sid] = true
				emit("teleport_discovered", {"actor": c.id, "id": sid})
			result.open_page = "teleport"
		"lifting_stone":
			emit("object_hit", {"actor": c.id, "object": object_id, "type": o.type, "x": float(at[0]), "y": float(at[1]), "hits": 1})
			result.channel = 3.0
		"pickup":
			var item := str(o.get("item", ""))
			var mem := world.room_mem(c, game.room_rt.room_id)
			mem.opened[object_id] = true
			game.room_rt.objects[object_id] = {"state": "open"}
			game.inventory.apply_add(c.id, item, int(o.get("count", 1)), "pickup")
		"inspect":
			result.text = str(o.get("text", ""))
			if o.has("open_page"): result.open_page = str(o.open_page)
			if o.has("page_args"): result.page_args = o.page_args
			# Some things teach you something the first time you look (a Codex entry): once per character.
			if o.has("effects") and not c.quests.has_flag("inspected_" + object_id):
				game.quest.apply_flag(c.id, "inspected_" + object_id)
				game.apply_effects(c.id, o.effects, "inspect:" + object_id)
		"rite_circle":
			return game.quest.start_set_piece(c, str(o.get("event", "")))
		"storage_chest":
			result.open_page = "storage"
			PlaceRules.note_use(game, c, "storage")   # decision 43: the first use at the place (earned remote access)
		"letter_box":
			result.open_page = "mail"   # decision 43: the letter box at home, a courier post in a town
		"meditation_mat":
			result.open_page = "cultivation"   # decision 43: sit and cultivate where the Qi gathers
		"bath_station":
			# S44: the bath is a seclusion focus, chosen on the Seclusion page.
			result.open_page = "seclusion"
		"cooking_pot", "alchemy_furnace", "earth_vent", "forge_anvil", "formation_table", "garden_bed", "chart_table", "shipyard_slip":
			result.open_page = str(o.get("page", {"cooking_pot": "cooking", "alchemy_furnace": "alchemy", "earth_vent": "alchemy", "forge_anvil": "forge",
				"formation_table": "formations", "garden_bed": "garden", "chart_table": "charts", "shipyard_slip": "vessels"}[o.type]))
		"notice_board":
			result.open_page = "notice_board"
			PlaceRules.read_board(game, c)   # decision 43: its papers read, the gold "!" goes
		"signpost":
			result.text = str(o.get("text", ""))
		"insight_stone":
			result.text = str(o.get("text", Tx.t("sim.world.meditate_here")))
			# P13a: a stele that holds a lost art gives it to a rubbing once its condition holds; until then, and after,
			# it is only a stone to meditate at (roadmap decision 19: it never says what it holds).
			if game.progression.read_stele(c, object_id):
				result.text = Tx.t("sim.world.rubbing_taken")
			# S49 leisure arts: a chess problem is carved beside every insight stone; one answer a day.
			elif game.progression.chess_open(c, object_id):
				return ok({"dialogue": {"npc": "", "speaker": Tx.t("sim.world.chess_speaker"), "portrait": {}, "lines": [Tx.t("sim.world.chess_line")],
					"choices": [{"text": Tx.t("sim.world.chess_study"), "page": "chess", "args": {"site": object_id}},
						{"text": Tx.t("sim.world.chess_meditate"), "close": true}]}})
		"qi_spring":
			# S45: a gardener bottles the spring's water, three bottles a day; otherwise it is a place to meditate.
			var sw: Dictionary = game.crafting.bottle_spring_water(c) if Unlocks.is_unlocked(c.id, "herb_garden") else {}
			result.text = str(sw.get("text", o.get("text", Tx.t("sim.world.meditate_here"))))
		"spar_post":
			return game.quest.start_spar_from_object(c, o)
		"defence_drum":
			return game.sect.start_defence(c)
		"egg_nest":
			# S46: the fallen King's nest gives each character one Rare egg per opening.
			var king := ContentDB.entry("beast_kings", str(o.get("king", "")))
			game.quest.apply_flag(c.id, world.nests.nest_flag(str(o.get("king", ""))))
			game.inventory.apply_add(c.id, str(king.get("nest", {}).get("item", "rare_spirit_egg")), 1, "king_nest")
			result.text = Tx.t("sim.world.nest_egg")
		"beast_tide_drum":
			return world.start_beast_tide(c)
		"spirit_mine":
			return game.sect.mine_dialogue(c, str(o.get("mine", "")))
		"rift_tear":
			return game.calendar.open_rift(c)
		"treasure_birth":
			return game.calendar.open_treasure(c, o)
		"beast_trial_stone":
			return world.start_beast_trial(c)
		"treasure_plot":
			var tp: Dictionary = game.crafting.tend_treasure_plot(c, o)
			result.text = str(tp.get("text", ""))
		"treasure_tree":
			var tt: Dictionary = game.progression.consult_jade_tree(c)
			result.text = str(tt.get("text", ""))
		"bell":
			var bs: Dictionary = game.room_rt.objects.get(object_id, {})
			bs.state = "open"
			game.room_rt.objects[object_id] = bs
			emit("bell_rung", {"actor": c.id, "object": object_id})
		_:
			pass
	if o.has("set_flag"): game.quest.apply_flag(c.id, str(o.set_flag))
	emit("object_interacted", {"actor": c.id, "object": object_id, "type": o.type, "room": game.room_rt.room_id})
	return result

## How far from a thing the context button offers it and interact takes it: its `radius`; a person's as much further
## as the people are drawn bigger (decision 43, TopdownRoom.PEOPLE), so a talk starts from the same gap between two
## bodies.
func reach_of(o: Dictionary) -> float:
	var r := float(o.get("radius", 110))
	if str(o.get("type", "")) == "npc": r *= TopdownRoom.PEOPLE
	return r

## Context action for the Attack button (Part 9.9): quest target → NPC → loot → gather → travel.
func query_context(c) -> Dictionary:
	if game.room_rt == null or c == null: return {}
	var st: ActorState = game.actor_state(c.id)
	if st == null: return {}
	var best := {}
	var best_score := INF
	for o in game.room_rt.def.get("objects", []):
		if not offers_context(o): continue
		var at: Array = o.get("at", [0, 0])
		var d: float = st.plane.distance_to(Vector2(float(at[0]), float(at[1])))
		# M18: a chest on the ledge above never takes the button from the herb at your feet (interact would refuse it).
		# Out of reach first: the HUD asks every frame, and whether a thing shows (its requirements) is the dear part.
		if d > reach_of(o) or absf(st.altitude - float(o.get("alt", 0.0))) > WorldAuthority.REACH_ALT: continue
		if not world.object_visible(c, o): continue
		if o.has("chase") and str(world.chases.get(c.id, {}).get("object", "")) == str(o.id): continue   # he is off over the roofs
		var avail := world.object_available(c, o)
		if avail.get("spent", false): continue
		# A resource node not open to the character yet offers nothing (the prototype's QA: the Reed Shallows' herbs said
		# "You don't know which leaves are worth picking yet" from the button in the first fight).
		if avail.get("locked", false) and resource_node(o): continue
		var calls: bool = o.type == "npc" and QuestAuthority.marker_calls(game.quest.npc_marker(c, str(o.npc)))
		var score: float = context_rank(o, calls) * 1000.0 + d
		if score < best_score:
			best_score = score
			best = {"object": str(o.id), "type": o.type, "label": verb(o), "ok": avail.ok, "text": avail.text, "npc": str(o.get("npc", ""))}
	if best.is_empty():
		for p in game.room_rt.def.get("portals", []):
			if not context_portal(p): continue
			if world.portal_near(c, p):
				var ps := world.portal_state(c, p)
				if ps.get("hidden", false): continue
				best = {"portal": str(p.id), "type": "portal", "label": Tx.t("sim.world.enter"), "ok": ps.open, "text": ps.text, "target": str(p.get("to", ""))}
				break
	return best

## A thing worked for a yield or a training (RESOURCE_NODES), or a Temper drum (a body trial's circle).
static func resource_node(o: Dictionary) -> bool:
	return str(o.get("type", "")) in RESOURCE_NODES or str(o.get("event", "")).ends_with("_body_trial")

## Objects the context button offers: not the ones a blow breaks or trains on, nor decor, air pockets or a run's finish.
static func offers_context(o: Dictionary) -> bool:
	var kind := str(o.get("type", ""))
	return not (kind in WorldAuthority.BREAKABLES or kind in WorldAuthority.TRAINING or kind in ["decor", "air_pocket", "route_finish"])

## How strongly an object in reach claims the context button; the lowest rank wins and distance breaks ties within a
## rank. A pickup first, an NPC whose marker calls you over, any NPC, other objects, gathering last; a door or gate
## is offered only when no object is in reach.
static func context_rank(o: Dictionary, calls := false) -> float:
	match str(o.get("type", "")):
		"pickup": return 0.5
		"npc": return 1.0 if calls else 2.0
		"herb_patch", "ore_vein", "fishing_spot", "star_sight", "insect_swarm": return 4.0
	return 3.0

## A portal the context button can take ("Enter"): anything but a plain edge, which is walked through.
static func context_portal(p: Dictionary) -> bool:
	return str(p.get("type", "edge")) != "edge"

func verb(o: Dictionary) -> String:
	if o.has("chase"): return Tx.t("sim.world.chase")
	match str(o.type):
		"npc": return Tx.t("sim.world.talk")
		"route_stone": return Tx.t("sim.world.begin")
		"herb_patch": return Tx.t("sim.world.gather")
		"ore_vein": return Tx.t("sim.world.mine")
		"fishing_spot": return Tx.t("sim.world.fish")
		"insect_swarm": return Tx.t("sim.world.net")
		"gravity_switch": return Tx.t("sim.world.turn")
		"beast_trail": return Tx.t("sim.world.snare")
		"ancestral_altar": return Tx.t("sim.world.rites")
		"chest", "storage_chest": return Tx.t("sim.world.open")
		"shrine": return Tx.t("sim.world.pray")
		"pickup": return Tx.t("sim.world.take")
		"lifting_stone": return Tx.t("sim.world.lift")
		"cooking_pot": return Tx.t("sim.world.cook")
		"alchemy_furnace", "earth_vent": return Tx.t("sim.world.refine")
		"forge_anvil": return Tx.t("sim.world.forge")
		"bath_station": return Tx.t("sim.world.bathe")
		"teleport_stone", "transfer_array": return Tx.t("sim.world.travel")
		"notice_board", "signpost", "inspect", "letter_box": return Tx.t("sim.world.read")
		"meditation_mat": return Tx.t("sim.world.sit")
		"rite_circle": return Tx.t("sim.world.begin")
		"spar_post": return Tx.t("sim.world.spar")
		"bell", "beast_tide_drum": return Tx.t("sim.world.ring")
		"rift_tear": return Tx.t("sim.world.touch")
		"treasure_birth": return Tx.t("sim.world.reach")
		"beast_trial_stone": return Tx.t("sim.world.begin")
		"egg_nest": return Tx.t("sim.world.take")
		"treasure_plot", "garden_bed": return Tx.t("sim.world.tend")
		"treasure_tree": return Tx.t("sim.world.sit_beneath")
		"star_sight": return Tx.t("sim.world.observe")
		"chart_table": return Tx.t("sim.world.chart")
		"shipyard_slip": return Tx.t("sim.world.build")
		"starsea_dock": return Tx.t("sim.world.set_sail")
		"spirit_mine": return Tx.t("sim.world.survey")
	return Tx.t("sim.world.use")
