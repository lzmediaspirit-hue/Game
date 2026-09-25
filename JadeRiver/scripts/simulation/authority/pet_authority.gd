class_name PetAuthority
extends Authority
## S22 · Spirit animals: bonded companions that fight, gather and cultivate with
## their owner. They never die: at 0 HP they retreat into their token for 60 s
## (or until the owner meditates).

var ally_uid := 0

func intents() -> Array:
	return ["set_active_pet", "set_pet_role", "feed_pet", "pet_command", "rename_pet", "choose_starter", "attempt_tame", "incubate_egg", "hatch_egg", "evolve_pet"]

func subscribe() -> void:
	GameEvents.subscribe("room_entered", _on_room_entered, 45)
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 75)
	GameEvents.subscribe("meditation_tick", _on_meditation_tick, 75)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"set_active_pet":
			var uid := str(intent.get("pet", ""))
			if uid != "" and _pet(c, uid).is_empty(): return fail("unknown_pet")
			c.active_pet = uid
			_spawn(c)
			emit("pet_changed", {"actor": c.id, "pet": uid})
			return ok()
		"set_pet_role":
			var p := _pet(c, str(intent.get("pet", c.active_pet)))
			if p.is_empty(): return fail("unknown_pet")
			var role := str(intent.get("role", "combat"))
			if not role in ["combat", "gatherer", "cultivation"]: return fail("bad_role")
			p.role = role
			emit("pet_changed", {"actor": c.id, "pet": p.uid})
			return ok()
		"feed_pet":
			var p2 := _pet(c, str(intent.get("pet", c.active_pet)))
			var item := str(intent.get("item", ""))
			if p2.is_empty(): return fail("unknown_pet")
			if c.inventory.count(item) <= 0: return fail("no_food")
			if not ContentDB.item(item).get("food", {}).get("pet_food", false) and not item in ContentDB.entry("pets", str(p2.species)).get("favourite_foods", []):
				return fail("not_pet_food")
			game.inventory.apply_remove(c.id, item, 1, "feed_pet")
			p2.hunger_day = Clock.reset_day(Clock.now_utc())
			apply_bond(c.id, 0.5 if item in ContentDB.entry("pets", str(p2.species)).get("favourite_foods", []) else 0.2, str(p2.uid))
			emit("pet_fed", {"actor": c.id, "pet": p2.uid})
			return ok()
		"pet_command":
			emit("pet_commanded", {"actor": c.id, "command": str(intent.get("command", "follow"))})
			return ok()
		"choose_starter": return choose_starter(c, str(intent.get("species", "")))
		"attempt_tame": return attempt_tame(c, str(intent.get("offering", "")), float(intent.get("result", -1.0)))
		"incubate_egg": return incubate_egg(c, int(intent.get("index", -1)))
		"hatch_egg": return hatch_egg(c, int(intent.get("index", 0)))
		"evolve_pet": return evolve(c, str(intent.get("pet", c.active_pet)), str(intent.get("branch", "")))
		"rename_pet":
			var p3 := _pet(c, str(intent.get("pet", c.active_pet)))
			if p3.is_empty(): return fail("unknown_pet")
			p3.name = str(intent.get("name", p3.name)).left(16)
			return ok()
	return fail("unknown_intent")

func _pet(c, uid: String) -> Dictionary:
	for p in c.pets:
		if str(p.uid) == uid: return p
	return {}

func active_pet(c) -> Dictionary:
	return _pet(c, c.active_pet) if c != null else {}

func gatherer_active(actor_id: String) -> bool:
	var c = game.character(actor_id)
	return c != null and active_pet(c).get("role", "") == "gatherer"

func apply_grant(actor_id: String, species: String) -> void:
	var c = game.character(actor_id)
	var sp := ContentDB.entry("pets", species)
	if c == null or sp.is_empty(): return
	var uid := "%s_%d" % [species, c.pets.size() + 1]
	var pet := {"uid": uid, "species": species, "name": str(sp.get("name", species)), "level": 1, "xp": 0.0, "bond": 1.0,
		"role": str(sp.get("strength_role", "combat")), "stage": "hatchling", "hunger_day": Clock.reset_day(Clock.now_utc()), "rarity": "common",
		"branch": "", "traits": _roll_traits(c), "revealed": 0}
	c.pets.append(pet)
	if c.active_pet == "": c.active_pet = uid
	emit("pet_bonded", {"actor": actor_id, "pet": uid, "species": species})
	_spawn(c)

func apply_bond(actor_id: String, amount: float, uid := "") -> void:
	var c = game.character(actor_id)
	var p := active_pet(c) if uid == "" else _pet(c, uid)
	if p.is_empty(): return
	if amount > 0.0: amount *= 1.0 + _trait_sum(p, "bond_gain")
	var before := int(float(p.bond))
	p.bond = clampf(float(p.bond) + amount, 0.0, 10.0)
	if int(float(p.bond)) != before: emit("bond_changed", {"actor": actor_id, "pet": p.uid, "value": p.bond})

func _on_room_entered(_p: Dictionary) -> void:
	_spawn(game.active())

func _spawn(c) -> void:
	if c == null or game.room_rt == null: return
	# Uids restart in every room: only remove the entry if it really is our pet.
	var old: EnemyState = game.room_rt.enemies.get(ally_uid) if ally_uid != 0 else null
	if old != null and old.team == "ally" and old.pet_owner == c.id: game.room_rt.enemies.erase(ally_uid)
	ally_uid = 0
	var p := active_pet(c)
	if p.is_empty() or game.room_rt.def.get("type", "") == "interior": return
	var sp := ContentDB.entry("pets", str(p.species))
	var st: ActorState = game.actor_state(c.id)
	var a := EnemyState.new()
	a.uid = game.room_rt.uid()
	a.def_id = str(sp.get("art", p.species))
	a.def = {"name": str(p.name), "art": {"creature": str(sp.get("art", p.species))}, "half_width": 16, "height": 30, "ally": true}
	a.team = "ally"
	a.pet_owner = c.id
	a.level = int(p.level)
	a.pools.max_hp = c.pools.max_hp * float(growth().get("hp_share", 0.4))
	a.pools.hp = a.pools.max_hp
	a.plane = (st.plane if st else Vector2(c.position.x, c.position.y)) + Vector2(-50, 12)
	a.ai = {"state": "follow", "timer": 0.0, "offset": 56, "depth_offset": 14, "speed": 200}
	a.stats = {"attack": 0.0}
	game.room_rt.enemies[a.uid] = a
	ally_uid = a.uid
	emit("ally_spawned", {"uid": a.uid, "kind": "pet"})

func tick(delta: float) -> void:
	var c = game.active()
	if c == null or game.room_rt == null or ally_uid == 0: return
	var a: EnemyState = game.room_rt.enemies.get(ally_uid)
	if a == null: return
	var p := active_pet(c)
	var power: float = c.stats.value("physical_attack") * inherit_share(p) * care_mult(p) * (1.0 + trait_bonus(c, "pet_damage"))
	power *= 1.0 + role_match(p) if p.get("role", "combat") == "combat" else 0.6
	var was_down: bool = a.ai.state == "downed"
	AllyBrain.think(game, a, delta, power, 36.0)
	if was_down and a.ai.state != "downed":
		emit("pet_returned", {"actor": c.id, "uid": a.uid, "pet": str(p.get("uid", ""))})

func _on_actor_defeated(p: Dictionary) -> void:
	var c = game.active()
	var pet := active_pet(c)
	if pet.is_empty() or p.get("victim_kind", "") != "enemy": return
	pet.xp = float(pet.xp) + int(p.get("level", 1))
	var need := float(ContentDB.curve("pet_xp.base", 20)) * pow(int(pet.level), float(ContentDB.curve("pet_xp.per_level_pow", 1.5)))
	if float(pet.xp) >= need and int(pet.level) < 100:
		pet.xp = float(pet.xp) - need
		pet.level = int(pet.level) + 1
		emit("pet_level_up", {"actor": c.id, "pet": pet.uid, "level": pet.level})

func _on_meditation_tick(_p: Dictionary) -> void:
	var c = game.active()
	if active_pet(c).is_empty(): return
	if game.tick_count % 60 == 0: apply_bond(c.id, 0.01)

# ------------------------------------------------------------------ growth (S22)
func growth() -> Dictionary:
	return ContentDB.config("pet_growth")

func stage_index(stage: String) -> int:
	var stages: Array = growth().get("stages", [])
	for i in stages.size():
		if str(stages[i].id) == stage: return i
	return 0

func stage_def(stage: String) -> Dictionary:
	var stages: Array = growth().get("stages", [])
	return stages[stage_index(stage)] if not stages.is_empty() else {}

func next_stage(p: Dictionary) -> Dictionary:
	var stages: Array = growth().get("stages", [])
	var i := stage_index(str(p.get("stage", "hatchling"))) + 1
	if i >= stages.size() or stages[i].get("primordial_only", false): return {}
	return stages[i]

## Share of the owner's attack: the species' own row when it has one, else the stage's.
func inherit_share(p: Dictionary) -> float:
	var stage := str(p.get("stage", "hatchling"))
	var own: Dictionary = ContentDB.entry("pets", str(p.get("species", ""))).get("inherit_owner", {})
	return float(own.get(stage, stage_def(stage).get("inherit", 0.2)))

## A role that matches the species' strength works harder (+25%).
func role_match(p: Dictionary) -> float:
	var sp := ContentDB.entry("pets", str(p.get("species", "")))
	return float(growth().get("role_match_bonus", 0.25)) if str(sp.get("strength_role", "")) == str(p.get("role", "")) else 0.0

## Fed today: full effect; hungry: 70%.
func care_mult(p: Dictionary) -> float:
	var hungry := Clock.reset_day(Clock.now_utc()) - int(p.get("hunger_day", 0)) >= 1
	return float(growth().get("hungry_mult", 0.7)) if hungry else 1.0

## Every gate for the next stage, each {ok, text}: level, hearts and the owner's realm.
func evolve_gates(c, p: Dictionary) -> Array:
	var nx := next_stage(p)
	if nx.is_empty(): return []
	var out: Array = []
	out.append({"ok": int(p.get("level", 1)) >= int(nx.get("level", 0)), "text": "Level %d" % int(nx.get("level", 0))})
	out.append({"ok": float(p.get("bond", 0.0)) >= float(nx.get("bond", 0)), "text": "%d hearts" % int(nx.get("bond", 0))})
	var realm := str(nx.get("realm", ""))
	var realm_ok := realm == "" or ProgressionRules.at_least(c.cultivator.realm_key, realm)
	out.append({"ok": realm_ok, "text": "You at %s" % ContentDB.name_of("realms", realm)})
	return out

func can_evolve(c, p: Dictionary) -> bool:
	var gates := evolve_gates(c, p)
	return not gates.is_empty() and gates.all(func(g): return g.ok)

func evolve(c, uid: String, branch: String) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	var nx := next_stage(p)
	if nx.is_empty(): return fail("final_stage", {"text": "It has grown as far as this land allows."})
	for g in evolve_gates(c, p):
		if not g.ok: return fail("not_ready", {"text": "Needs " + str(g.text)})
	var branches: Array = ContentDB.entry("pets", str(p.species)).get("branches", [])
	if nx.get("branch", false):
		if not branch in branches: return fail("choose_branch", {"text": "Choose how it grows.", "branches": branches})
		p.branch = branch
	var from := str(p.stage)
	p.stage = str(nx.id)
	emit("pet_evolved", {"actor": c.id, "pet": p.uid, "from": from, "stage": p.stage, "branch": str(p.get("branch", ""))})
	if nx.get("reveal_trait", false): _reveal_trait(c, p)
	return ok({"stage": p.stage})

func _roll_traits(c) -> Array:
	var pool: Array = ContentDB.all("pet_traits").map(func(t): return str(t.id))
	var rng := Rng.stream(c.id if c != null else "account", "pet")
	var out: Array = []
	while out.size() < mini(int(growth().get("traits_per_pet", 3)), pool.size()):
		var t: String = pool[rng.randi_range(0, pool.size() - 1)]
		if not out.has(t): out.append(t)
	return out

func _reveal_trait(c, p: Dictionary) -> void:
	if not p.has("traits"): p.traits = _roll_traits(c)   # animals from older saves
	var n := int(p.get("revealed", 0))
	if n >= (p.traits as Array).size(): return
	p.revealed = n + 1
	emit("trait_revealed", {"actor": c.id, "pet": p.uid, "trait": str(p.traits[n])})

func revealed_traits(p: Dictionary) -> Array:
	return (p.get("traits", []) as Array).slice(0, int(p.get("revealed", 0)))

## What the active animal's revealed traits add to one number (pet_traits.json `bonus`).
func trait_bonus(c, key: String) -> float:
	return _trait_sum(active_pet(c) if c != null else {}, key)

func _trait_sum(p: Dictionary, key: String) -> float:
	var total := 0.0
	for t in revealed_traits(p):
		total += float(ContentDB.entry("pet_traits", str(t)).get("bonus", {}).get(key, 0.0))
	return total

## Resonance: an active animal in the Cultivation role adds to accumulation (Spirit Awakening 1+).
func resonance(c) -> float:
	var p := active_pet(c)
	if p.is_empty() or str(p.get("role", "")) != "cultivation": return 0.0
	var gate := str(growth().get("resonance_unlock", "spirit_awakening_1"))
	if not ProgressionRules.at_least(c.cultivator.realm_key, gate): return 0.0
	var base := float(stage_def(str(p.get("stage", "hatchling"))).get("resonance", 0.0)) + trait_bonus(c, "resonance")
	return base * (1.0 + role_match(p)) * care_mult(p)

# ------------------------------------------------------------------ starter, taming, eggs (S22)
## The hermit's three young ones: one choice per character, ever.
func choose_starter(c, species: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "spirit_animals"): return fail("locked", {"text": Unlocks.locked_text("spirit_animals")})
	if not ContentDB.entry("pets", species).get("starter", false): return fail("not_starter")
	if c.quests.has_flag("starter_chosen"): return fail("already_chosen", {"text": "Your first companion has already chosen you."})
	game.quest.apply_flag(c.id, "starter_chosen")
	apply_grant(c.id, species)
	return ok({"species": species})

## Nearest paw-marked monster within reach and below the taming HP line.
func tame_target(c) -> EnemyState:
	if game.room_rt == null: return null
	var st: ActorState = game.actor_state(c.id)
	if st == null: return null
	var cfg := ContentDB.config("taming")
	var best: EnemyState = null
	var best_d := 240.0
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or not e.def.get("tameable", false): continue
		if e.pools.hp > e.pools.max_hp * float(cfg.get("hp_below", 0.3)): continue
		var d = e.plane.distance_to(st.plane)
		if d < best_d:
			best_d = d
			best = e
	return best

func tame_species(e: EnemyState) -> String:
	var sp := str(e.def.get("tame_species", e.def_id))
	if not ContentDB.has_entry("pets", sp): sp = sp.trim_suffix("_chick")
	return sp if ContentDB.has_entry("pets", sp) else ""

func tame_chance(c, e: EnemyState, offering: String, result: float) -> float:
	var cfg := ContentDB.config("taming")
	var chance := float(cfg.get("base", 0.35)) + float(cfg.get("offering_bonus", {}).get(offering, 0.0))
	var gap := ProgressionRules.level(c) - e.level
	chance += gap * float(cfg.get("per_level_over", 0.03)) if gap >= 0 else -gap * float(cfg.get("per_level_under", -0.08))
	chance += int(c.cultivator.daos.get("beast_taming", {}).get("tier", 0)) * float(cfg.get("per_dao_tier", 0.05))
	if result >= 0.0: chance += (clampf(result, 0.0, 1.0) - 0.5) * 0.3
	return clampf(chance, float(cfg.get("min", 0.05)), float(cfg.get("max", 0.95)))

## Use a Bonding Offering beside a weakened paw-marked monster. `result` is the calm
## mini-game score (0..1), or -1 when the offering was used from quick-use.
func attempt_tame(c, offering: String, result: float) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "taming"): return fail("locked", {"text": Unlocks.locked_text("taming")})
	if offering == "" or not offering in ContentDB.config("taming").get("offerings", []): return fail("bad_offering")
	if c.inventory.count(offering) <= 0: return fail("no_offering")
	var e := tame_target(c)
	if e == null: return fail("no_target", {"text": "Weaken a paw-marked spirit beast below 30% first."})
	var species := tame_species(e)
	if species == "": return fail("no_species")
	game.inventory.apply_remove(c.id, offering, 1, "taming")
	var chance := tame_chance(c, e, offering, result)
	var success := Rng.stream(c.id, "taming").randf() < chance
	game.enemies.release(e)
	emit("tame_attempted", {"actor": c.id, "species": species, "success": success, "chance": chance})
	if success:
		apply_grant(c.id, species)
		game.progression.apply_insight(c.id, "beast_taming", 5.0, "taming")
		log_line(c.id, "The %s calms and bonds with you." % ContentDB.name_of("pets", species), "loot")
	else:
		log_line(c.id, "The %s bolts into the reeds." % ContentDB.name_of("pets", species), "warn")
	return ok({"success": success, "species": species, "chance": chance})

func incubate_egg(c, index: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "spirit_eggs"): return fail("locked", {"text": Unlocks.locked_text("spirit_eggs")})
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	if str(ContentDB.item(str(c.inventory.bag[index].id)).get("use_action", "")) != "incubate": return fail("not_an_egg")
	var cfg := ContentDB.config("eggs")
	if c.eggs.size() >= int(cfg.get("max_incubating", 1)): return fail("busy", {"text": "One egg at a time needs your warmth."})
	var rng := Rng.stream(c.id, "taming")
	var total := 0.0
	for r in cfg.get("species", []): total += float(r.get("weight", 1))
	var roll := rng.randf() * total
	var species := ""
	for r in cfg.get("species", []):
		roll -= float(r.get("weight", 1))
		if roll <= 0.0:
			species = str(r.species)
			break
	var hours: Array = cfg.get("hatch_hours", [2, 24])
	var h := rng.randf_range(float(hours[0]), float(hours[1]))
	game.inventory.apply_remove_index(c.id, index, 1, "incubate")
	c.eggs.append({"species": species, "hatch_utc": Clock.now_utc() + h * 3600.0})
	emit("egg_incubated", {"actor": c.id, "hours": h})
	emit("system_used", {"actor": c.id, "system": "egg_incubated"})
	return ok({"hours": h})

func hatch_egg(c, index: int) -> Dictionary:
	if index < 0 or index >= c.eggs.size(): return fail("bad_index")
	var egg: Dictionary = c.eggs[index]
	if Clock.now_utc() < float(egg.hatch_utc): return fail("not_ready", {"text": "It is still warm and quiet."})
	c.eggs.remove_at(index)
	apply_grant(c.id, str(egg.species))
	emit("egg_hatched", {"actor": c.id, "species": egg.species})
	return ok({"species": egg.species})
