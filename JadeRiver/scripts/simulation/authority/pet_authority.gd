class_name PetAuthority
extends Authority
## S22 · Spirit animals: bonded companions that fight, gather and cultivate with
## their owner. They never die: at 0 HP they retreat into their token for 60 s
## (or until the owner meditates).

var ally_uid := 0              # the active animal's ally in this room (0 when none)
var allies: Dictionary = {}    # pet uid -> ally uid in the current room (S46 command capacity)
var essence_check := 0.0
var guardian_cd: Dictionary = {}   # actor -> seconds before Guardian Spirit can take another blow (transient)

func intents() -> Array:
	return ["set_active_pet", "set_pet_role", "feed_pet", "pet_command", "rename_pet", "choose_starter", "attempt_tame", "incubate_egg", "hatch_egg", "evolve_pet", "breed",
		"lock_pet", "devour_core", "sell_cores", "rest_pets", "offer_contract", "incubate_input", "set_party",
		"learn_skill_book", "equip_pet", "unequip_pet", "fuse_pets", "pet_breakthrough",
		"set_pet_bag", "swap_pet_from_bag", "set_mount"]

func subscribe() -> void:
	GameEvents.subscribe("room_entered", _on_room_entered, 45)
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 75)
	GameEvents.subscribe("meditation_tick", _on_meditation_tick, 75)
	GameEvents.subscribe("hit_landed", _on_player_hit, 75)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"set_active_pet":
			var uid := str(intent.get("pet", ""))
			if uid != "" and _pet(c, uid).is_empty(): return fail("unknown_pet")
			var why := call_blocked(c, uid)
			if why != "": return fail("cannot_call", {"text": why})
			c.active_pet = uid
			c.party_pets.erase(uid)
			if uid == c.mount_pet: _clear_mount(c)
			_spawn(c)
			emit("pet_changed", {"actor": c.id, "pet": uid})
			return ok()
		"set_pet_bag": return set_pet_bag(c, str(intent.get("pet", "")), bool(intent.get("on", true)))
		"swap_pet_from_bag": return swap_from_bag(c, str(intent.get("pet", "")))
		"set_mount": return set_mount(c, str(intent.get("pet", "")), intent.get("on", null))
		"set_pet_role":
			var p := _pet(c, str(intent.get("pet", c.active_pet)))
			if p.is_empty(): return fail("unknown_pet")
			var role := str(intent.get("role", "combat"))
			if not role in ["combat", "gatherer", "cultivation", "mount", "guard"]: return fail("bad_role")
			if mount_only(p) and role != "mount": return fail("mount_only", {"text": Tx.t("sim.pet.mount_only") % str(p.name)})
			if role == "mount":
				if not mountable(p): return fail("not_mountable", {"text": Tx.t("sim.pet.too_small_to_carry_you")})
				if not Unlocks.is_unlocked(c.id, str(growth().get("mount_unlock", "mounts"))): return fail("locked", {"text": Unlocks.locked_text("mounts")})
			p.role = role
			# S46 Mount slot: the mount carries you in its own slot, so a combat animal can walk beside you.
			if role == "mount":
				if c.mount_pet != "" and c.mount_pet != str(p.uid):
					var old := _pet(c, c.mount_pet)
					if not old.is_empty() and not mount_only(old): old.role = "combat"
				c.mount_pet = str(p.uid)
				c.riding = true
				if c.active_pet == str(p.uid): c.active_pet = ""
				c.party_pets.erase(str(p.uid))
			elif c.mount_pet == str(p.uid): _clear_mount(c)
			emit("pet_changed", {"actor": c.id, "pet": p.uid})
			if role == "mount": emit("system_used", {"actor": c.id, "system": "mount"})
			_spawn(c)   # a mount carries you instead of following
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
		"breed": return breed(c, str(intent.get("a", "")), str(intent.get("b", "")))
		"rename_pet":
			var p3 := _pet(c, str(intent.get("pet", c.active_pet)))
			if p3.is_empty(): return fail("unknown_pet")
			var nm := str(intent.get("name", p3.name)).strip_edges().left(16)
			if nm == "": return fail("empty_name")
			p3.name = nm
			emit("pet_changed", {"actor": c.id, "pet": p3.uid})
			return ok()
		"lock_pet":
			var p4 := _pet(c, str(intent.get("pet", c.active_pet)))
			if p4.is_empty(): return fail("unknown_pet")
			p4.locked = bool(intent.get("locked", not p4.get("locked", false)))
			emit("pet_changed", {"actor": c.id, "pet": p4.uid})
			return ok({"locked": p4.locked})
		"devour_core": return devour_core(c, str(intent.get("pet", c.active_pet)), str(intent.get("item", "")))
		"sell_cores": return sell_cores(c, str(intent.get("item", "")), maxi(1, int(intent.get("count", 1))))
		"rest_pets": return rest_pets(c)
		"offer_contract": return offer_contract(c, str(intent.get("pet", c.active_pet)), str(intent.get("kind", "")))
		"incubate_input": return incubate_input(c, int(intent.get("egg", 0)), str(intent.get("kind", "")), str(intent.get("item", "")))
		"set_party": return set_party(c, str(intent.get("pet", "")), bool(intent.get("on", true)))
		"learn_skill_book": return learn_skill_book(c, str(intent.get("pet", c.active_pet)), str(intent.get("book", "")))
		"equip_pet": return equip_pet(c, str(intent.get("pet", c.active_pet)), int(intent.get("index", -1)))
		"unequip_pet": return unequip_pet(c, str(intent.get("pet", c.active_pet)), str(intent.get("slot", "")))
		"fuse_pets": return fuse_pets(c, str(intent.get("keep", "")), str(intent.get("sacrifice", "")), bool(intent.get("confirm", false)))
		"pet_breakthrough": return pet_breakthrough(c, str(intent.get("pet", c.active_pet)), intent.get("support", []), str(intent.get("branch", "")))
	return fail("unknown_intent")

func _pet(c, uid: String) -> Dictionary:
	for p in c.pets:
		if str(p.uid) == uid: return ensure_fields(p)
	return {}

## S46 depth fields, filled on animals from older saves with neutral values (a hatch or tame rolls real ones).
func ensure_fields(p: Dictionary) -> Dictionary:
	if p.has("purity"): return p
	var band: Array = growth().get("purity", {}).get(str(p.get("rarity", "common")), [5, 15])
	p.purity = int(round((float(band[0]) + float(band[1])) * 0.5))
	p.growth = 1.0
	var apt := {}
	for st in growth().get("aptitude", {}).get("stats", ["hp", "attack", "defence", "speed"]): apt[str(st)] = 1.0
	p.aptitude = apt
	p.contract = "master"
	p.learned_skills = []
	p.equipment = {}
	p.wounded = false
	p.knockouts = []
	p.core_grade = ""
	p.variant = false
	p.locked = false
	return p

## A newborn or newly tamed animal's bloodline: purity by rarity, hidden growth and aptitude, a 1% colour variant.
func _roll_bloodline(c, p: Dictionary) -> void:
	ensure_fields(p)
	var rng := Rng.stream(c.id if c != null else "account", "bloodline")
	var band: Array = growth().get("purity", {}).get(str(p.get("rarity", "common")), [5, 15])
	p.purity = rng.randi_range(int(band[0]), int(band[1]))
	var gr: Array = growth().get("growth", [0.8, 1.3])
	p.growth = snappedf(rng.randf_range(float(gr[0]), float(gr[1])), 0.01)
	var ap: Dictionary = growth().get("aptitude", {})
	var ar: Array = ap.get("range", [0.8, 1.2])
	for st in ap.get("stats", ["hp", "attack", "defence", "speed"]): p.aptitude[str(st)] = snappedf(rng.randf_range(float(ar[0]), float(ar[1])), 0.01)
	p.variant = rng.randf() < float(growth().get("colour_variant", 0.01))

## Growth and aptitude stay hidden until the animal is a Juvenile (S46).
func aptitude_known(p: Dictionary) -> bool:
	return stage_index(str(p.get("stage", "hatchling"))) >= stage_index("juvenile")

## What an animal's hidden gifts and any Grievous Wound make of one of its stats.
func stat_mult(p: Dictionary, stat: String) -> float:
	ensure_fields(p)
	var m := float(p.get("growth", 1.0)) * float(p.get("aptitude", {}).get(stat, 1.0))
	if p.get("wounded", false): m *= float(growth().get("grievous", {}).get("mult", 0.8))
	if int(p.get("awakened", 0)) >= 2: m *= 1.0 + float(growth().get("awakening", {}).get("form_bonus", 0.1))
	if str(p.get("contract", "master")) == "blood": m *= 1.0 + float(growth().get("contracts", {}).get("blood", {}).get("stats", 0.15))
	m *= 1.0 + gear_bonus(p, stat) + core_bonus(p)
	return m

func active_pet(c) -> Dictionary:
	return _pet(c, c.active_pet) if c != null else {}

func gatherer_active(actor_id: String) -> bool:
	var c = game.character(actor_id)
	return c != null and active_pet(c).get("role", "") == "gatherer"

func apply_grant(actor_id: String, species: String, born: Dictionary = {}) -> void:
	var c = game.character(actor_id)
	var sp := ContentDB.entry("pets", species)
	if c == null or sp.is_empty(): return
	var uid := "%s_%d" % [species, c.pets.size() + 1]
	while not _pet(c, uid).is_empty(): uid += "b"
	var pet := {"uid": uid, "species": species, "name": str(sp.get("name", species)), "level": 1, "xp": 0.0, "bond": 1.0,
		"role": str(sp.get("strength_role", "combat")), "stage": "hatchling", "hunger_day": Clock.reset_day(Clock.now_utc()),
		"rarity": str(born.get("rarity", "common")), "branch": "", "traits": born.get("traits", _roll_traits(c)), "revealed": 0}
	_roll_bloodline(c, pet)
	# An egg you warmed yourself: its hatchling knows you (3 hearts) and keeps what you dripped into it.
	if born.has("hearts"): pet.bond = float(born.hearts)
	if float(born.get("purity_bonus", 0.0)) != 0.0: pet.purity = clampi(int(pet.purity) + int(born.purity_bonus), 0, 100)
	c.pets.append(pet)
	if c.active_pet == "": c.active_pet = uid
	emit("pet_bonded", {"actor": actor_id, "pet": uid, "species": species})
	_check_awakening(c, pet)
	_spawn(c)

func apply_bond(actor_id: String, amount: float, uid := "") -> void:
	var c = game.character(actor_id)
	var p := active_pet(c) if uid == "" else _pet(c, uid)
	if p.is_empty(): return
	if amount > 0.0: amount *= 1.0 + _trait_sum(p, "bond_gain")
	var before := int(float(p.bond))
	p.bond = clampf(float(p.bond) + amount, 0.0, 10.0)
	if int(float(p.bond)) != before:
		emit("bond_changed", {"actor": actor_id, "pet": p.uid, "value": p.bond})
		# At 10 hearts the animal may offer an Equal Contract (S46).
		var need := int(growth().get("contracts", {}).get("equal", {}).get("hearts", 10))
		if before < need and int(float(p.bond)) >= need and equal_contract_open(c, p): emit("contract_offered", {"actor": actor_id, "pet": str(p.uid)})

# ------------------------------------------------------------------ rarity and breeding (S22)
func rarity_def(id: String) -> Dictionary:
	var all: Array = growth().get("rarities", [])
	for r in all:
		if str(r.id) == id: return r
	return all[0] if not all.is_empty() else {"id": "common", "power": 1.0}

func rarity_power(p: Dictionary) -> float:
	return float(rarity_def(str(p.get("rarity", "common"))).get("power", 1.0))

func family_of(p: Dictionary) -> String:
	return str(ContentDB.entry("pets", str(p.get("species", ""))).get("family", str(p.get("species", ""))))

## Why this character cannot breed right now ("" when the gates are open).
func breeding_blocked(c) -> String:
	var cfg: Dictionary = growth().get("breeding", {})
	if not Unlocks.is_unlocked(c.id, str(cfg.get("unlock", "pet_breeding"))): return Unlocks.locked_text(str(cfg.get("unlock", "pet_breeding")))
	var need := int(cfg.get("pavilion_level", 4))
	if game.sect.level_building(str(cfg.get("pavilion", "beast_pavilion"))) < need: return Tx.t("sim.pet.breeding_needs_the_pavilion") % need
	for e in c.eggs:
		if e.get("bred", false): return Tx.t("sim.pet.one_pair_at_a_time")
	if c.eggs.size() >= int(ContentDB.config("eggs").get("max_incubating", 1)): return Tx.t("sim.pet.one_egg_at_a_time")
	return ""

## Adults of the same family as `p` (never itself).
func breed_partners(c, p: Dictionary) -> Array:
	var stage := str(growth().get("breeding", {}).get("stage", "adult"))
	if stage_index(str(p.get("stage", ""))) < stage_index(stage): return []
	return c.pets.filter(func(o): return str(o.uid) != str(p.uid) and family_of(o) == family_of(p) and stage_index(str(o.get("stage", ""))) >= stage_index(stage))

## Two Adults of one family make an egg (24 h, then it hatches in 2-24 h): the higher rarity,
## sometimes one step more; traits drawn from both parents, sometimes a new one.
func breed(c, a_uid: String, b_uid: String) -> Dictionary:
	var why := breeding_blocked(c)
	if why != "": return fail("locked", {"text": why})
	var a := _pet(c, a_uid)
	var b := _pet(c, b_uid)
	if a.is_empty() or b.is_empty() or a_uid == b_uid: return fail("unknown_pet")
	if not breed_partners(c, a).has(b): return fail("not_a_pair", {"text": Tx.t("sim.pet.two_adults_of_one_family")})
	var cfg: Dictionary = growth().get("breeding", {})
	var rng := Rng.stream(c.id, "pet")
	var order: Array = growth().get("rarities", []).map(func(r): return str(r.id))
	var ri := maxi(order.find(str(a.get("rarity", "common"))), order.find(str(b.get("rarity", "common"))))
	if rng.randf() < float(cfg.get("rarity_step", 0.2)): ri += 1
	ri = clampi(ri, 0, maxi(0, order.find(str(cfg.get("bred_rarity_cap", "epic")))))
	var pool: Array = []
	for t in (a.get("traits", []) as Array) + (b.get("traits", []) as Array):
		if not pool.has(t): pool.append(t)
	var n := int(growth().get("traits_per_pet", 3))
	var traits: Array = []
	while traits.size() < n and not pool.is_empty():
		traits.append(pool.pop_at(rng.randi_range(0, pool.size() - 1)))
	if rng.randf() < float(cfg.get("mutation", 0.2)) or traits.size() < n:
		var fresh: Array = ContentDB.all("pet_traits").map(func(t): return str(t.id)).filter(func(t): return not traits.has(t))
		if not fresh.is_empty():
			var t_new: String = fresh[rng.randi_range(0, fresh.size() - 1)]
			if traits.size() >= n: traits[rng.randi_range(0, traits.size() - 1)] = t_new
			else: traits.append(t_new)
	var species := str(a.species) if rng.randf() < 0.5 else str(b.species)
	var hatch: Array = cfg.get("hatch_hours", [2, 24])
	var hours := float(cfg.get("hours", 24)) + rng.randf_range(float(hatch[0]), float(hatch[1]))
	c.eggs.append({"species": species, "hatch_utc": Clock.now_utc() + hours * 3600.0, "bred": true, "rarity": order[ri] if ri < order.size() else "common",
		"traits": traits, "parents": [str(a.name), str(b.name)]})
	emit("pets_bred", {"actor": c.id, "a": a_uid, "b": b_uid, "species": species, "rarity": order[ri] if ri < order.size() else "common", "hours": hours})
	emit("system_used", {"actor": c.id, "system": "breed"})
	return ok({"species": species, "hours": hours, "rarity": order[ri] if ri < order.size() else "common"})

# ------------------------------------------------------------------ mounts (S22)
var dismounted: Dictionary = {}   # actor -> seconds before they can ride again

func mountable(p: Dictionary) -> bool:
	return ContentDB.entry("pets", str(p.get("species", ""))).has("mount")

## The mount spec of the animal carrying this character, or {} when on foot (S46: the Mount slot, while riding).
func mount_of(c) -> Dictionary:
	if c == null or dismounted.has(c.id): return {}
	_migrate_mount(c)
	if not c.riding or c.mount_pet == "": return {}
	var p := _pet(c, c.mount_pet)
	if p.is_empty(): return {}
	return ContentDB.entry("pets", str(p.species)).get("mount", {})

## Saves from before the Mount slot rode the active animal in the Mount role.
func _migrate_mount(c) -> void:
	if c.mount_pet != "": return
	var p := active_pet(c)
	if p.is_empty() or str(p.get("role", "")) != "mount": return
	c.mount_pet = str(p.uid)
	c.riding = true
	c.active_pet = ""

func mount_pet_of(c) -> Dictionary:
	return _pet(c, c.mount_pet) if c != null and c.mount_pet != "" else {}

func mount_only(p: Dictionary) -> bool:
	return ContentDB.entry("pets", str(p.get("species", ""))).get("mount_only", false)

func _clear_mount(c) -> void:
	c.mount_pet = ""
	c.riding = false

## The Mount button: climb on or off; with a pet, put that animal in the Mount slot first.
func set_mount(c, uid: String, on) -> Dictionary:
	if uid != "":
		var p := _pet(c, uid)
		if p.is_empty(): return fail("unknown_pet")
		return handle({"type": "set_pet_role", "actor": c.id, "pet": uid, "role": "mount"})
	if c.mount_pet == "" or _pet(c, c.mount_pet).is_empty(): return fail("no_mount", {"text": Tx.t("sim.pet.no_mount")})
	var want: bool = (not c.riding) if on == null else bool(on)
	if want and dismounted.has(c.id): return fail("thrown", {"text": Tx.t("sim.pet.thrown")})
	c.riding = want
	emit("pet_changed", {"actor": c.id, "pet": c.mount_pet})
	_spawn(c)
	return ok({"riding": c.riding})

func mount_speed(c) -> float:
	if mount_of(c).is_empty(): return 1.0
	var m := mount_of(c)
	return float(m.get("speed", growth().get("mount_speed", 1.5))) * (1.0 + gear_bonus(mount_pet_of(c), "mount_speed"))   # a Reed Saddle (S46)

## Flying mounts halve the QI of flight once the rider is strong enough to steer one (Cloud Stride 5).
func flight_qi_mult(c) -> float:
	var m := mount_of(c)
	if m.get("flying", false) and ProgressionRules.at_least(c.cultivator.realm_key, str(growth().get("flying_mount_realm", "cloud_stride_5"))):
		return float(growth().get("flying_mount_qi", 0.5))
	return 1.0

func _on_player_hit(p: Dictionary) -> void:
	var c = game.character(str(p.get("target", "")))
	if c == null or mount_of(c).is_empty(): return
	if float(p.get("amount", 0)) >= c.pools.max_hp * float(growth().get("dismount_hp_pct", 0.15)):
		dismounted[c.id] = float(growth().get("dismount_s", 10))
		emit("dismounted", {"actor": c.id})
		_spawn(c)   # it lands beside you and follows until you climb back on

func _on_room_entered(_p: Dictionary) -> void:
	_spawn(game.active())

## A pet on Guard duty (S45) keeps pests and thieves off the garden while you are away.
func guard_pet(c) -> Dictionary:
	for p in c.pets:
		if str(p.get("role", "")) == "guard": return p
	return {}

func _spawn(c) -> void:
	if c == null or game.room_rt == null: return
	# Uids restart in every room: only remove entries that really are our animals.
	for puid in allies:
		var old: EnemyState = game.room_rt.enemies.get(allies[puid])
		if old != null and old.team == "ally" and old.pet_owner == c.id and str(old.ai.get("pet", "")) == str(puid): game.room_rt.enemies.erase(allies[puid])
	allies.clear()
	ally_uid = 0
	_apply_pockets(c)
	if game.room_rt.def.get("type", "") == "interior": return
	var i := 0
	var walking: Array = party(c)
	# Thrown from the saddle (S22), the mount lands beside you and follows until you climb back on.
	if dismounted.has(c.id) and not mount_pet_of(c).is_empty(): walking.append(mount_pet_of(c))
	for p in walking:
		var a := _make_ally(c, p, i)
		allies[str(p.uid)] = a.uid
		if str(p.uid) == c.active_pet: ally_uid = a.uid
		i += 1

func _make_ally(c, p: Dictionary, i: int) -> EnemyState:
	var sp := ContentDB.entry("pets", str(p.species))
	var st: ActorState = game.actor_state(c.id)
	var a := EnemyState.new()
	a.uid = game.room_rt.uid()
	a.def_id = str(sp.get("art", p.species))
	var art := {"creature": str(sp.get("art", p.species))}
	var form := form_of(p)
	if not form.is_empty():
		art.scale = float(form.get("scale", 1.0))
		art.tint = str(form.get("tint", "#ffffff"))
	a.def = {"name": str(p.name), "art": art, "half_width": 16, "height": 30, "ally": true,
		"movement": sp.get("movement", {"jump": 530, "climb": false, "fly": false, "drop": true})}
	a.team = "ally"
	a.pet_owner = c.id
	a.level = int(p.level)
	a.pools.max_hp = c.pools.max_hp * float(growth().get("hp_share", 0.4)) * rarity_power(p) * stat_mult(p, "hp")
	a.pools.hp = a.pools.max_hp
	a.plane = (st.plane if st else Vector2(c.position.x, c.position.y)) + Vector2(-50 - i * 40, 12 + i * 14)
	AllyBrain.settle(game, a, st)
	a.ai = {"state": "follow", "timer": 0.0, "offset": 56 + i * 40, "depth_offset": 14 + i * 14, "speed": 200, "pet": str(p.uid),
		"free_cast": true, "skill_cd": 0.0, "calm": 0.0, "sup_t": 0.0}
	a.stats = {"attack": 0.0}
	game.room_rt.enemies[a.uid] = a
	emit("ally_spawned", {"uid": a.uid, "kind": "pet"})
	return a

func tick(delta: float) -> void:
	for actor in dismounted.keys():
		dismounted[actor] = float(dismounted[actor]) - delta
		if float(dismounted[actor]) <= 0.0:
			dismounted.erase(actor)
			_spawn(game.character(actor))
	var c = game.active()
	if c == null: return
	_tick_essence_blood(c, delta)
	if guardian_cd.has(c.id): guardian_cd[c.id] = maxf(0.0, float(guardian_cd[c.id]) - delta)
	if game.room_rt == null or allies.is_empty(): return
	for puid in allies.keys():
		var a: EnemyState = game.room_rt.enemies.get(allies[puid])
		if a == null or str(a.ai.get("pet", "")) != str(puid): continue
		var p := _pet(c, str(puid))
		if p.is_empty(): continue
		var power := pet_power(c, p) * _skill_mult(c, p, a, delta)
		var was_down: bool = a.ai.state == "downed"
		# Frenzy (S46): after a kill its wind-ups and recoveries run 15% faster.
		if float(a.ai.get("frenzy", 0.0)) > 0.0:
			a.ai.frenzy = float(a.ai.frenzy) - delta
			if str(a.ai.state) in ["windup", "recover"]: a.ai.timer = float(a.ai.timer) - delta * float(a.ai.get("frenzy_speed", 0.15))
		AllyBrain.think(game, a, delta, power, 36.0)
		_roar(c, p, a, delta)
		if was_down and a.ai.state != "downed":
			emit("pet_returned", {"actor": c.id, "uid": a.uid, "pet": str(puid)})
		_suppress(c, p, a, delta)

## One animal's strike: a share of the owner's attack, by stage, care, traits, rarity, gifts and role.
func pet_power(c, p: Dictionary) -> float:
	var power: float = c.stats.value("physical_attack") * inherit_share(p) * care_mult(p) * (1.0 + _trait_sum(p, "pet_damage")) * rarity_power(p) * stat_mult(p, "attack")
	power *= 1.0 + role_match(p) if p.get("role", "combat") == "combat" else 0.6
	return power

## Combat brought the animal to 0 HP: it retreats into its token (S22), never dies.
func apply_retreat(a: EnemyState) -> void:
	a.ai.state = "downed"
	a.ai.timer = float(growth().get("retreat_s", 60))
	a.action_time = 0.0
	var c = game.active()
	var puid := str(a.ai.get("pet", c.active_pet if c else ""))
	emit("pet_retreated", {"actor": c.id if c else "", "uid": a.uid, "pet": puid})
	if c == null: return
	var p := _pet(c, puid)
	_knocked_out(c, p)
	# A Blood Contract binds the two of you: its knockout bruises your soul.
	if str(p.get("contract", "")) == "blood":
		game.progression.apply_injury(c.id, "soul", int(growth().get("contracts", {}).get("blood", {}).get("soul_injury", 1)))

## S46 Grievous Wound: three knockouts inside five minutes leave the animal at 80% until it rests or is dosed.
func _knocked_out(c, p: Dictionary) -> void:
	if p.is_empty(): return
	var g: Dictionary = growth().get("grievous", {})
	var now: float = game.sim_time
	var kos: Array = (p.get("knockouts", []) as Array).filter(func(t): return now - float(t) <= float(g.get("window_s", 300)))
	kos.append(now)
	p.knockouts = kos
	if kos.size() >= int(g.get("knockouts", 3)) and not p.get("wounded", false):
		p.wounded = true
		p.knockouts = []
		emit("pet_wounded", {"actor": c.id, "pet": str(p.uid)})

## A Beast Revival Pill (or a rest at the Beast Hall) mends a Grievous Wound.
func heal_wound(actor_id: String, uid := "") -> bool:
	var c = game.character(actor_id)
	if c == null: return false
	var healed := false
	for p in c.pets:
		if (uid == "" or str(p.uid) == uid) and ensure_fields(p).get("wounded", false):
			p.wounded = false
			p.knockouts = []
			healed = true
			emit("pet_healed", {"actor": c.id, "pet": str(p.uid)})
	if healed: _spawn(c)
	return healed

## Rest your animals at the Beast Hall (Hermit Yao) or your sect's Beast Pavilion: every Grievous Wound mends.
func rest_pets(c) -> Dictionary:
	if not _at_beast_hall(c): return fail("not_here", {"text": Tx.t("sim.pet.rest_where")})
	if not heal_wound(c.id): return fail("none_wounded", {"text": Tx.t("sim.pet.none_wounded")})
	return ok()

func _at_beast_hall(c) -> bool:
	return game.workshop.npc_here(c, ["hermit_yao"]) or (game.room_rt != null and game.room_rt.room_id == str(ContentDB.config("defence").get("room", "")))

# ------------------------------------------------------------------ beast cores (S46)
## A core of the animal's own element feeds its growth.
func devour_core(c, uid: String, item: String) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	var core: Dictionary = ContentDB.item(item).get("core", {})
	if not core.has("tier"): return fail("not_a_core")
	if c.inventory.count(item) <= 0: return fail("no_core")
	var el := str(ContentDB.entry("pets", str(p.species)).get("element", ""))
	if str(core.element) != el: return fail("wrong_element", {"text": Tx.t("sim.pet.wrong_element") % [str(p.name), ContentDB.name_of("elements", el)]})
	game.inventory.apply_remove(c.id, item, 1, "devour")
	var xp := float(growth().get("cores", {}).get("xp", {}).get(str(core.tier), 60))
	add_xp(c, p, xp)
	emit("core_devoured", {"actor": c.id, "pet": str(p.uid), "item": item, "xp": xp})
	return ok({"xp": xp})

func add_xp(c, pet: Dictionary, amount: float) -> void:
	pet.xp = float(pet.xp) + amount
	for i in 20:
		var need := float(ContentDB.curve("pet_xp.base", 20)) * pow(int(pet.level), float(ContentDB.curve("pet_xp.per_level_pow", 1.5)))
		if float(pet.xp) < need or int(pet.level) >= 100: break
		pet.xp = float(pet.xp) - need
		pet.level = int(pet.level) + 1
		emit("pet_level_up", {"actor": c.id, "pet": pet.uid, "level": pet.level})

## The Core Exchange (the Beast Hall): fixed Spirit Stones a core by tier, up to 60 a day.
func exchange_left(c) -> int:
	var cfg: Dictionary = growth().get("cores", {})
	var day := Clock.reset_day(Clock.now_utc())
	var ex: Dictionary = c.crafting.get("core_exchange", {}) if c.crafting.get("core_exchange") is Dictionary else {}
	if int(ex.get("day", -1)) != day: return int(cfg.get("daily_cap", 60))
	return maxi(0, int(cfg.get("daily_cap", 60)) - int(ex.get("paid", 0)))

func sell_cores(c, item: String, count: int) -> Dictionary:
	if not _at_beast_hall(c): return fail("not_here", {"text": Tx.t("sim.pet.exchange_where")})
	var core: Dictionary = ContentDB.item(item).get("core", {})
	if not core.has("tier"): return fail("not_a_core")
	count = mini(count, c.inventory.count(item))
	var price := int(growth().get("cores", {}).get("price", {}).get(str(core.tier), 1))
	count = mini(count, exchange_left(c) / maxi(1, price))
	if count <= 0: return fail("cap", {"text": Tx.t("sim.pet.exchange_cap")})
	game.inventory.apply_remove(c.id, item, count, "core_exchange")
	game.economy.apply_currency("spirit_stone", price * count, "core_exchange")
	var day := Clock.reset_day(Clock.now_utc())
	var ex: Dictionary = c.crafting.get("core_exchange", {}) if c.crafting.get("core_exchange") is Dictionary else {}
	if int(ex.get("day", -1)) != day: ex = {"day": day, "paid": 0}
	ex.paid = int(ex.paid) + price * count
	c.crafting["core_exchange"] = ex
	emit("cores_sold", {"actor": c.id, "item": item, "count": count, "stones": price * count})
	return ok({"count": count, "stones": price * count})

func _on_actor_defeated(p: Dictionary) -> void:
	var c = game.active()
	var pet := active_pet(c)
	if pet.is_empty() or p.get("victim_kind", "") != "enemy": return
	add_xp(c, pet, int(p.get("level", 1)))
	# Frenzy (S46): every animal beside you that knows it quickens after a kill.
	if game.room_rt == null: return
	for puid in allies:
		var q := _pet(c, str(puid))
		var fr: Dictionary = ContentDB.entry("pet_skill_books", "frenzy").get("frenzy", {})
		var a: EnemyState = game.room_rt.enemies.get(allies[puid])
		if a != null and has_skill(q, "frenzy"):
			a.ai.frenzy = float(fr.get("seconds", 6.0))
			a.ai.frenzy_speed = float(fr.get("speed", 0.15))

func _on_meditation_tick(_p: Dictionary) -> void:
	var c = game.active()
	if active_pet(c).is_empty(): return
	if game.tick_count % 60 == 0: apply_bond(c.id, 0.01)
	# The other way of an Equal Contract: your cultivation feeds the animal.
	for p in party(c):
		if str(p.get("contract", "")) == "equal": add_xp(c, p, float(growth().get("contracts", {}).get("equal", {}).get("xp_per_tick", 0.5)))

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
	out.append({"ok": int(p.get("level", 1)) >= int(nx.get("level", 0)), "text": Tx.t("sim.pet.level") % int(nx.get("level", 0))})
	out.append({"ok": float(p.get("bond", 0.0)) >= float(nx.get("bond", 0)), "text": Tx.t("sim.pet.hearts") % int(nx.get("bond", 0))})
	var realm := str(nx.get("realm", ""))
	var realm_ok := realm == "" or ProgressionRules.at_least(c.cultivator.realm_key, realm)
	out.append({"ok": realm_ok, "text": Tx.t("sim.pet.you_at") % ContentDB.name_of("realms", realm)})
	return out

func can_evolve(c, p: Dictionary) -> bool:
	var gates := evolve_gates(c, p)
	return not gates.is_empty() and gates.all(func(g): return g.ok)

func evolve(c, uid: String, branch: String) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	var nx := next_stage(p)
	if nx.is_empty(): return fail("final_stage", {"text": Tx.t("sim.pet.it_has_grown_as_far")})
	for g in evolve_gates(c, p):
		if not g.ok: return fail("not_ready", {"text": Tx.t("sim.pet.needs") + str(g.text)})
	var branches: Array = ContentDB.entry("pets", str(p.species)).get("branches", [])
	if nx.get("branch", false):
		if not branch in branches: return fail("choose_branch", {"text": Tx.t("sim.pet.choose_how_it_grows"), "branches": branches})
		p.branch = branch
	# From Awakened on a stage-up is a breakthrough with support items (S46).
	if stage_index(str(nx.id)) >= stage_index(str(growth().get("breakthrough", {}).get("from", "awakened"))) and not p.get("_breaking", false):
		return fail("breakthrough", {"text": Tx.t("sim.pet.needs_breakthrough")})
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
	# Every point of bloodline purity strengthens the traits by 0.2% (S46).
	return total * (1.0 + float(p.get("purity", 0)) * float(growth().get("awakening", {}).get("trait_per_purity", 0.002)))

## Resonance: an active animal in the Cultivation role adds to accumulation (Spirit Awakening 1+).
## An Equal Contract lets it flow both ways: an Equal animal beside you resonates at half strength whatever its role.
func resonance(c) -> float:
	var gate := str(growth().get("resonance_unlock", "spirit_awakening_1"))
	if c == null or not ProgressionRules.at_least(c.cultivator.realm_key, gate): return 0.0
	var total := 0.0
	for p in party(c):
		var share := 1.0 if str(p.get("role", "")) == "cultivation" and str(p.uid) == c.active_pet else 0.0
		if share == 0.0 and str(p.get("contract", "")) == "equal": share = float(growth().get("contracts", {}).get("equal", {}).get("resonance_share", 0.5))
		if share == 0.0: continue
		var base := float(stage_def(str(p.get("stage", "hatchling"))).get("resonance", 0.0)) + _trait_sum(p, "resonance")
		total += base * (1.0 + role_match(p)) * care_mult(p) * share
	return total

# ------------------------------------------------------------------ starter, taming, eggs (S22)
## The hermit's three young ones: one choice per character, ever.
func choose_starter(c, species: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "spirit_animals"): return fail("locked", {"text": Unlocks.locked_text("spirit_animals")})
	if not ContentDB.entry("pets", species).get("starter", false): return fail("not_starter")
	if c.quests.has_flag("starter_chosen"): return fail("already_chosen", {"text": Tx.t("sim.pet.your_first_companion_has_already")})
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
	if suppressed_by_party(c, e): chance += float(growth().get("suppression", {}).get("tame_bonus", 0.1))   # S46
	return clampf(chance, float(cfg.get("min", 0.05)), float(cfg.get("max", 0.95)))

## Use a Bonding Offering beside a weakened paw-marked monster. `result` is the calm
## mini-game score (0..1), or -1 when the offering was used from quick-use.
func attempt_tame(c, offering: String, result: float) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "taming"): return fail("locked", {"text": Unlocks.locked_text("taming")})
	if offering == "" or not offering in ContentDB.config("taming").get("offerings", []): return fail("bad_offering")
	if c.inventory.count(offering) <= 0: return fail("no_offering")
	var e := tame_target(c)
	if e == null: return fail("no_target", {"text": Tx.t("sim.pet.weaken_a_paw_marked_spirit")})
	var species := tame_species(e)
	if species == "": return fail("no_species")
	# S46 natures: a demonic beast takes only a Purifying Offering; a Hollowed one must be cleansed by one first.
	var purifying := str(ContentDB.config("taming").get("purifying", "purifying_offering"))
	var nature := str(e.def.get("nature", "spirit"))
	if nature == "demonic" and offering != purifying: return fail("demonic", {"text": Tx.t("sim.pet.needs_purifying")})
	if nature == "hollowed" and not e.ai.get("cleansed", false):
		if offering != purifying: return fail("hollowed", {"text": Tx.t("sim.pet.needs_cleansing")})
		game.inventory.apply_remove(c.id, offering, 1, "taming")
		e.ai["cleansed"] = true
		emit("beast_cleansed", {"actor": c.id, "enemy": e.uid, "def": e.def_id})
		return ok({"cleansed": true, "species": species})
	game.inventory.apply_remove(c.id, offering, 1, "taming")
	var chance := tame_chance(c, e, offering, result)
	var success := Rng.stream(c.id, "taming").randf() < chance
	game.enemies.release(e)
	emit("tame_attempted", {"actor": c.id, "species": species, "success": success, "chance": chance})
	if success:
		apply_grant(c.id, species, {"rarity": roll_rarity(c, "tame_elite" if e.elite else "tame")})
		game.progression.apply_insight(c.id, "beast_taming", 5.0, "taming")
		log_line(c.id, Tx.t("sim.pet.the_calms_and_bonds_with") % ContentDB.name_of("pets", species), "loot")
	else:
		log_line(c.id, Tx.t("sim.pet.the_bolts_into_the_reeds") % ContentDB.name_of("pets", species), "warn")
	return ok({"success": success, "species": species, "chance": chance})

func incubate_egg(c, index: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "spirit_eggs"): return fail("locked", {"text": Unlocks.locked_text("spirit_eggs")})
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	if str(ContentDB.item(str(c.inventory.bag[index].id)).get("use_action", "")) != "incubate": return fail("not_an_egg")
	var cfg := ContentDB.config("eggs")
	if c.eggs.size() >= int(cfg.get("max_incubating", 1)): return fail("busy", {"text": Tx.t("sim.pet.one_egg_at_a_time")})
	var egg_def := ContentDB.item(str(c.inventory.bag[index].id))
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
	# S46: a special egg names its species (the Cloud Stag) or its rarity (a Beast King's nest); a plain one rolls both.
	if egg_def.has("egg_species"): species = str(egg_def.egg_species)
	var rarity := roll_rarity(c, str(egg_def.get("egg_rarity", "egg")))
	game.inventory.apply_remove_index(c.id, index, 1, "incubate")
	c.eggs.append({"species": species, "hatch_utc": Clock.now_utc() + h * 3600.0, "rarity": rarity})
	emit("egg_incubated", {"actor": c.id, "hours": h})
	emit("system_used", {"actor": c.id, "system": "egg_incubated"})
	return ok({"hours": h})

func hatch_egg(c, index: int) -> Dictionary:
	if index < 0 or index >= c.eggs.size(): return fail("bad_index")
	var egg: Dictionary = c.eggs[index]
	if Clock.now_utc() < float(egg.hatch_utc): return fail("not_ready", {"text": Tx.t("sim.pet.it_is_still_warm_and")})
	c.eggs.remove_at(index)
	var born: Dictionary = egg.duplicate(true)
	born.hearts = float(growth().get("incubation", {}).get("hatch_hearts", 3))
	born.purity_bonus = float(egg.get("purity_bonus", 0)) + game.progression.spend_fate_next(c, "egg_purity")   # Fox Spirit's Favour
	apply_grant(c.id, str(egg.species), born)
	emit("egg_hatched", {"actor": c.id, "species": egg.species})
	return ok({"species": egg.species})

# ------------------------------------------------------------------ bloodline (S46)
## Raise an animal's bloodline purity (0-100); crossing 50 wakes its ancestral skill, 90 its true form.
func add_purity(c, p: Dictionary, amount: int) -> int:
	ensure_fields(p)
	var before := int(p.purity)
	p.purity = clampi(before + amount, 0, 100)
	if int(p.purity) != before: emit("pet_changed", {"actor": c.id, "pet": str(p.uid)})
	_check_awakening(c, p)
	return int(p.purity) - before

## Beast Essence Blood (an Effect): the active animal drinks it.
func apply_purity(actor_id: String, amount: float, _source := "") -> void:
	var c = game.character(actor_id)
	var p := active_pet(c)
	if p.is_empty(): return
	var got := add_purity(c, p, int(round(amount)))
	log_line(c.id, Tx.t("sim.pet.purity_up") % [str(p.name), got, int(p.purity)], "loot")

func _check_awakening(c, p: Dictionary) -> void:
	var cfg: Dictionary = growth().get("awakening", {})
	var sp := ContentDB.entry("pets", str(p.get("species", "")))
	var woke := false
	for step in [[1, int(cfg.get("skill_at", 50)), "bloodline_skill"], [2, int(cfg.get("form_at", 90)), "form_change"]]:
		if int(p.get("awakened", 0)) >= int(step[0]) or int(p.get("purity", 0)) < int(step[1]): continue
		p.awakened = int(step[0])
		woke = true
		emit("bloodline_awakened", {"actor": c.id, "pet": str(p.uid), "step": int(step[0]), "name": str(sp.get(str(step[2]), {}).get("name", "")),
			"purity": int(p.purity)})
	if woke and allies.has(str(p.uid)): _spawn(c)   # the new form shows at once

## The ancestral skill woken at 50 purity ({} before).
func bloodline_skill(p: Dictionary) -> Dictionary:
	if int(p.get("awakened", 0)) < 1: return {}
	return ContentDB.entry("pets", str(p.get("species", ""))).get("bloodline_skill", {})

## The lineage form taken at 90 purity ({} before).
func form_of(p: Dictionary) -> Dictionary:
	if int(p.get("awakened", 0)) < 2: return {}
	return ContentDB.entry("pets", str(p.get("species", ""))).get("form_change", {})

## The name to show for a skill cast before any awakening: the species' third skill.
func _signature_skill(p: Dictionary) -> String:
	var skills: Array = ContentDB.entry("pets", str(p.get("species", ""))).get("skills", [])
	return str(skills[mini(2, skills.size() - 1)]) if not skills.is_empty() else str(p.get("name", ""))

## S46 casts: an awakened bloodline skill every 12 s of a fight, and an Equal Contract's free cast once a fight.
## Returns the multiplier for the strike this frame (1.0 when no skill goes with it).
func _skill_mult(c, p: Dictionary, a: EnemyState, delta: float) -> float:
	var eq: Dictionary = growth().get("contracts", {}).get("equal", {})
	a.ai.skill_cd = maxf(0.0, float(a.ai.get("skill_cd", 0.0)) - delta)
	var st: ActorState = game.actor_state(c.id)
	var fighting := false
	if st != null:
		for e in game.room_rt.living_enemies():
			if e.team == "enemy" and not e.hidden and not e.def.get("passive", false) and e.plane.distance_to(st.plane) < 400.0:
				fighting = true
				break
	if fighting: a.ai.calm = 0.0
	else:
		a.ai.calm = float(a.ai.get("calm", 0.0)) + delta
		if float(a.ai.calm) >= float(eq.get("calm_s", 5.0)): a.ai.free_cast = true   # the fight is over
	# Only the strike that lands this frame carries a skill.
	if str(a.ai.get("state", "")) != "windup" or float(a.ai.timer) - delta > 0.0: return 1.0
	var skill := bloodline_skill(p)
	if str(p.get("contract", "")) == "equal" and a.ai.get("free_cast", false):
		a.ai.free_cast = false
		emit("pet_skill_cast", {"actor": c.id, "pet": str(p.uid), "skill": str(skill.get("name", _signature_skill(p))), "free": true})
		return maxf(float(eq.get("free_cast_mult", 2.5)), float(skill.get("mult", 1.0)))
	if not skill.is_empty() and float(a.ai.skill_cd) <= 0.0:
		a.ai.skill_cd = float(growth().get("awakening", {}).get("skill_cd", 12.0))
		emit("pet_skill_cast", {"actor": c.id, "pet": str(p.uid), "skill": str(skill.get("name", "")), "free": false})
		return float(skill.get("mult", 2.5))
	return 1.0

# ------------------------------------------------------------------ suppression (S46, the S12 Pressure contest)
## An animal's bloodline tier: its rarity step (Common 1 ... Primordial 5) plus its awakenings.
func bloodline_tier(p: Dictionary) -> int:
	var order: Array = growth().get("rarities", []).map(func(r): return str(r.id))
	return 1 + maxi(0, order.find(str(p.get("rarity", "common")))) + int(p.get("awakened", 0))

## A wild beast's: its rank halved (rounded up), one more for an elite, two for a boss. 0 for non-beasts.
func beast_tier(e: EnemyState) -> int:
	var cfg: Dictionary = growth().get("suppression", {})
	var rank := WorldAuthority.beast_rank(e.def, e.level)
	if rank <= 0: return 0
	var t := ceili(float(rank) / float(cfg.get("rank_div", 2)))
	if e.is_boss(): t += int(cfg.get("boss", 2))
	elif e.elite: t += int(cfg.get("elite", 1))
	return t

func suppresses(p: Dictionary, e: EnemyState) -> bool:
	var will := beast_tier(e)
	return will > 0 and CombatRules.pressure_loss(float(bloodline_tier(p)), float(will)) > 0.0

func suppressed_by_party(c, e: EnemyState) -> bool:
	for p in party(c):
		if suppresses(p, e): return true
	return false

## Once a second an animal presses its blood on the wild beasts near it: each weaker one is gripped by Fear, once.
func _suppress(c, p: Dictionary, a: EnemyState, delta: float) -> void:
	var cfg: Dictionary = growth().get("suppression", {})
	a.ai.sup_t = float(a.ai.get("sup_t", 0.0)) - delta
	if float(a.ai.sup_t) > 0.0 or str(a.ai.get("state", "")) == "downed": return
	a.ai.sup_t = float(cfg.get("every_s", 1.0))
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden or e.ai.get("suppressed", false) or e.plane.distance_to(a.plane) > float(cfg.get("reach", 260)): continue
		if not suppresses(p, e): continue
		e.ai["suppressed"] = true
		game.combat.apply_enemy_status(e, {"id": "fear", "power": 1.0, "remaining": float(cfg.get("fear_s", 2.0)), "source": c.id})
		emit("beast_suppressed", {"actor": c.id, "pet": str(p.uid), "enemy": e.uid, "def": e.def_id})

# ------------------------------------------------------------------ contracts (S46)
## At 10 hearts an animal may offer the one Equal Contract a character ever makes.
func equal_contract_open(c, p: Dictionary) -> bool:
	var need := float(growth().get("contracts", {}).get("equal", {}).get("hearts", 10))
	return str(p.get("contract", "master")) != "equal" and float(p.get("bond", 0.0)) >= need and not c.quests.has_flag("equal_contract")

func offer_contract(c, uid: String, kind: String) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	var cfg: Dictionary = growth().get("contracts", {})
	match kind:
		"equal":
			if c.quests.has_flag("equal_contract"): return fail("once", {"text": Tx.t("sim.pet.equal_once")})
			if float(p.get("bond", 0.0)) < float(cfg.get("equal", {}).get("hearts", 10)):
				return fail("hearts", {"text": Tx.t("sim.pet.equal_hearts") % int(cfg.get("equal", {}).get("hearts", 10))})
			game.quest.apply_flag(c.id, "equal_contract")
		"blood":
			if str(p.get("contract", "master")) != "master": return fail("bound", {"text": Tx.t("sim.pet.already_bound")})
			var item := str(cfg.get("blood", {}).get("item", "beast_essence_blood"))
			if c.inventory.count(item) <= 0: return fail("no_blood", {"text": Tx.t("sim.pet.needs_item") % ContentDB.item_name(item)})
			game.inventory.apply_remove(c.id, item, 1, "blood_contract")
		_: return fail("bad_kind")
	p.contract = kind
	emit("contract_formed", {"actor": c.id, "pet": uid, "kind": kind})
	_spawn(c)
	return ok({"contract": kind})

# ------------------------------------------------------------------ command capacity (S46)
## Animals that may fight beside you at once, tied to Soul: 1, 2 from Spirit Awakening, 3 from Sage.
func command_capacity(c) -> int:
	var n := 1
	for step in growth().get("command", []):
		if str(step.get("realm", "")) == "" or ProgressionRules.at_least(c.cultivator.realm_key, str(step.realm)): n = maxi(n, int(step.get("count", 1)))
	return n

## The animals beside you: the active one first, then the party, up to the command capacity.
func party(c) -> Array:
	var out: Array = []
	if c == null: return out
	_migrate_mount(c)
	var act := active_pet(c)
	if not act.is_empty() and not str(act.get("role", "")) in ["guard", "mount"] and not mount_only(act): out.append(act)   # on Guard duty it stays home (S45)
	for uid in c.party_pets:
		if out.size() >= command_capacity(c): break
		var p := _pet(c, str(uid))
		if p.is_empty() or str(p.uid) == c.active_pet or str(p.get("role", "")) in ["guard", "mount"] or mount_only(p): continue
		out.append(p)
	return out

func set_party(c, uid: String, on: bool) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	if uid == c.active_pet: return fail("already_active")
	c.party_pets = c.party_pets.filter(func(u): return str(u) != uid and not _pet(c, str(u)).is_empty())
	if on:
		if str(p.get("role", "")) in ["guard", "mount"] or mount_only(p): return fail("busy", {"text": Tx.t("sim.pet.party_busy") % str(p.name)})
		var why := call_blocked(c, uid)
		if why != "": return fail("cannot_call", {"text": why})
		var cap := command_capacity(c)
		if c.party_pets.size() + 1 >= cap: return fail("capacity", {"text": Tx.t("sim.pet.capacity") % cap})
		c.party_pets.append(uid)
	_spawn(c)
	emit("party_changed", {"actor": c.id, "count": party(c).size()})
	return ok({"party": c.party_pets.duplicate()})

# ------------------------------------------------------------------ incubation input (S46)
## Once of each kind per egg: your own essence blood (+10 purity, -10% max HP for 24 h), a beast core to steer
## the element, or Beast Essence Blood to reroll one hidden trait.
func incubate_input(c, index: int, kind: String, item: String) -> Dictionary:
	if index < 0 or index >= c.eggs.size(): return fail("bad_index")
	var egg: Dictionary = c.eggs[index]
	var inputs: Array = egg.get("inputs", [])
	if kind in inputs: return fail("already", {"text": Tx.t("sim.pet.egg_already")})
	var cfg: Dictionary = growth().get("incubation", {})
	match kind:
		"blood":
			if float(c.cooldowns.get("essence_blood", 0.0)) > Clock.now_utc(): return fail("weak", {"text": Tx.t("sim.pet.still_weak")})
			egg.purity_bonus = float(egg.get("purity_bonus", 0)) + float(cfg.get("blood", {}).get("purity", 10))
			c.cooldowns["essence_blood"] = Clock.now_utc() + float(cfg.get("blood", {}).get("hours", 24)) * 3600.0
			game.combat.refresh_stats(c.id)
		"element":
			if egg.get("bred", false): return fail("bred", {"text": Tx.t("sim.pet.bred_egg")})
			var core: Dictionary = ContentDB.item(item).get("core", {})
			if not core.has("element"): return fail("not_a_core")
			if c.inventory.count(item) <= 0: return fail("no_core")
			var el := str(core.element)
			if str(ContentDB.entry("pets", str(egg.species)).get("element", "")) == el: return fail("same", {"text": Tx.t("sim.pet.egg_same_element")})
			var pool: Array = (ContentDB.config("eggs").get("species", []) as Array).filter(
				func(r): return str(ContentDB.entry("pets", str(r.species)).get("element", "")) == el)
			if pool.is_empty(): return fail("no_element", {"text": Tx.t("sim.pet.egg_no_element") % ContentDB.name_of("elements", el)})
			game.inventory.apply_remove(c.id, item, 1, "incubate_input")
			var rng := Rng.stream(c.id, "taming")
			var total := 0.0
			for r in pool: total += float(r.get("weight", 1))
			var roll := rng.randf() * total
			for r in pool:
				roll -= float(r.get("weight", 1))
				if roll <= 0.0:
					egg.species = str(r.species)
					break
		"reroll":
			var reroll_item := str(cfg.get("reroll_item", "beast_essence_blood"))
			if c.inventory.count(reroll_item) <= 0: return fail("no_blood", {"text": Tx.t("sim.pet.needs_item") % ContentDB.item_name(reroll_item)})
			game.inventory.apply_remove(c.id, reroll_item, 1, "incubate_input")
			if not egg.has("traits"): egg.traits = _roll_traits(c)
			var rng2 := Rng.stream(c.id, "pet")
			var fresh: Array = ContentDB.all("pet_traits").map(func(t): return str(t.id)).filter(func(t): return not (egg.traits as Array).has(t))
			if not fresh.is_empty(): egg.traits[rng2.randi_range(0, (egg.traits as Array).size() - 1)] = fresh[rng2.randi_range(0, fresh.size() - 1)]
		_: return fail("bad_kind")
	inputs.append(kind)
	egg.inputs = inputs
	emit("egg_infused", {"actor": c.id, "egg": index, "kind": kind})
	return ok({"kind": kind})

func _tick_essence_blood(c, delta: float) -> void:
	if not c.cooldowns.has("essence_blood"): return
	essence_check -= delta
	if essence_check > 0.0: return
	essence_check = 5.0
	if Clock.now_utc() >= float(c.cooldowns.essence_blood):
		c.cooldowns.erase("essence_blood")
		game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ beast medicine (S46)
## Beast Revival Pills, Beast Essence Blood and the Beast Marrow Washing Pill: each checks it can help before it is spent.
func use_pet_item(c, index: int) -> Dictionary:
	var s: Dictionary = c.inventory.bag[index]
	var id := str(s.id)
	var def := ContentDB.item(id)
	var p := active_pet(c)
	for e in def.get("use", []):
		match str(e.get("kind", "")):
			"heal_pet_wound":
				if not c.pets.any(func(x): return ensure_fields(x).get("wounded", false)): return fail("none_wounded", {"text": Tx.t("sim.pet.none_wounded")})
			"add_pet_purity":
				if p.is_empty(): return fail("no_pet", {"text": Tx.t("sim.pet.no_active")})
				if int(p.get("purity", 0)) >= 100: return fail("pure", {"text": Tx.t("sim.pet.pure") % str(p.name)})
			"wash_pet_marrow":
				if p.is_empty(): return fail("no_pet", {"text": Tx.t("sim.pet.no_active")})
				if not aptitude_known(p): return fail("too_young", {"text": Tx.t("sim.pet.gifts_hidden") % str(p.name)})
			"learn_pet_skill":
				var why := learn_blocked(p, str(e.get("skill", "")))
				if why != "": return fail("cannot_learn", {"text": why})
	game.inventory.apply_remove_index(c.id, index, 1, "pet_item")
	game.apply_effects(c.id, def.get("use", []), "item:" + id)
	return ok({"item": id})

## The Beast Marrow Washing Pill: the active animal's weakest aptitude is rolled again (no toxicity).
func wash_marrow(actor_id: String) -> String:
	var c = game.character(actor_id)
	var p := active_pet(c)
	if p.is_empty(): return ""
	var worst := ""
	for st in p.aptitude:
		if worst == "" or float(p.aptitude[st]) < float(p.aptitude[worst]): worst = str(st)
	if worst == "": return ""
	var ar: Array = growth().get("aptitude", {}).get("range", [0.8, 1.2])
	p.aptitude[worst] = snappedf(Rng.stream(c.id, "bloodline").randf_range(float(ar[0]), float(ar[1])), 0.01)
	emit("pet_changed", {"actor": c.id, "pet": str(p.uid)})
	log_line(c.id, Tx.t("sim.pet.marrow_washed") % [str(p.name), Tx.t("ui.pets.apt_" + worst), float(p.aptitude[worst])], "loot")
	_spawn(c)
	return worst

# ------------------------------------------------------------------ skill books (S46)
## Learned-skill slots open by stage: none as a Hatchling, 2 as a Juvenile, 3 as an Adult, 4 from Awakened.
func skill_slots(p: Dictionary) -> int:
	return int(growth().get("skill_slots", {}).get(str(p.get("stage", "hatchling")), 0))

func has_skill(p: Dictionary, skill: String) -> bool:
	return not p.is_empty() and (p.get("learned_skills", []) as Array).has(skill)

## Why this animal cannot learn `skill` now ("" when it can).
func learn_blocked(p: Dictionary, skill: String) -> String:
	if p.is_empty(): return Tx.t("sim.pet.no_active")
	if not ContentDB.has_entry("pet_skill_books", skill): return Tx.t("sim.pet.not_a_book")
	if skill_slots(p) <= 0: return Tx.t("sim.pet.too_young_to_learn") % str(p.name)
	if has_skill(p, skill): return Tx.t("sim.pet.knows_skill") % [str(p.name), ContentDB.name_of("pet_skill_books", skill)]
	return ""

## Teach a skill book: into a free slot, or over a random one when the slots are full.
func learn_skill_book(c, uid: String, item: String) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	var skill := str(ContentDB.item(item).get("pet_book", ""))
	var why := learn_blocked(p, skill)
	if why != "": return fail("cannot_learn", {"text": why})
	if c.inventory.count(item) <= 0: return fail("no_book")
	game.inventory.apply_remove(c.id, item, 1, "skill_book")
	return ok(_learn(c, p, skill))

func apply_learn(actor_id: String, skill: String) -> void:
	var c = game.character(actor_id)
	var p := active_pet(c)
	if learn_blocked(p, skill) == "": _learn(c, p, skill)

func _learn(c, p: Dictionary, skill: String) -> Dictionary:
	var learned: Array = p.get("learned_skills", [])
	var replaced := ""
	if learned.size() < skill_slots(p): learned.append(skill)
	else:
		var i := Rng.stream(c.id, "pet").randi_range(0, skill_slots(p) - 1)
		replaced = str(learned[i])
		learned[i] = skill
	p.learned_skills = learned
	emit("pet_skill_learned", {"actor": c.id, "pet": str(p.uid), "skill": skill, "replaced": replaced})
	_apply_pockets(c)
	return {"skill": skill, "replaced": replaced}

## What an animal's learned skills add to one number (pet_skill_books.json `bonus`).
func _skill_sum(p: Dictionary, key: String) -> float:
	var total := 0.0
	for sk in p.get("learned_skills", []): total += float(ContentDB.entry("pet_skill_books", str(sk)).get("bonus", {}).get(key, 0.0))
	return total

## The share of a blow an animal takes: its traits (Iron Hide the trait) and learned skills (Iron Hide the book).
func damage_taken_mult(a: EnemyState) -> float:
	var c = game.character(a.pet_owner)
	if c == null: return 1.0
	var p := _pet(c, str(a.ai.get("pet", c.active_pet)))
	return maxf(0.1, 1.0 + _trait_sum(p, "pet_damage_taken") + _skill_sum(p, "pet_damage_taken"))

## Deep Pockets: the active animal carries a row of your gourd.
func _apply_pockets(c) -> void:
	var n := 0
	var p := active_pet(c)
	if has_skill(p, "deep_pockets"): n = int(ContentDB.entry("pet_skill_books", "deep_pockets").get("bag_slots", 6))
	game.inventory.apply_bonus_slots(c.id, n)

## Herb Whisper: how near a herb must be for its ripening time to show (0 when no animal beside you knows it).
func whisper_range(c) -> float:
	for p in party(c):
		if has_skill(p, "herb_whisper"): return float(ContentDB.entry("pet_skill_books", "herb_whisper").get("whisper", 400))
	return 0.0

## Thunder Roar: every 15 s of a fight, foes near the animal are stunned for a second (bosses stand firm).
func _roar(c, p: Dictionary, a: EnemyState, delta: float) -> void:
	if not has_skill(p, "thunder_roar") or str(a.ai.get("state", "")) == "downed": return
	var cfg: Dictionary = ContentDB.entry("pet_skill_books", "thunder_roar").get("roar", {})
	a.ai.roar_cd = maxf(0.0, float(a.ai.get("roar_cd", 0.0)) - delta)
	if float(a.ai.roar_cd) > 0.0: return
	var hit := 0
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden or e.plane.distance_to(a.plane) > float(cfg.get("radius", 130)): continue
		game.combat.apply_enemy_status(e, {"id": "stun", "power": 1.0, "remaining": float(cfg.get("stun_s", 1.0)), "source": c.id})
		hit += 1
	if hit == 0: return
	a.ai.roar_cd = float(cfg.get("every_s", 15.0))
	emit("pet_skill_cast", {"actor": c.id, "pet": str(p.uid), "skill": ContentDB.name_of("pet_skill_books", "thunder_roar"), "free": false})

## Guardian Spirit: true when an animal beside you takes this blow (then it rests 30 s).
func guardian_absorbs(c) -> bool:
	if c == null or float(guardian_cd.get(c.id, 0.0)) > 0.0: return false
	for p in party(c):
		if not has_skill(p, "guardian_spirit"): continue
		var a: EnemyState = game.room_rt.enemies.get(int(allies.get(str(p.uid), 0))) if game.room_rt else null
		if a == null or str(a.ai.get("state", "")) == "downed": continue
		guardian_cd[c.id] = float(ContentDB.entry("pet_skill_books", "guardian_spirit").get("guard_every_s", 30.0))
		emit("pet_skill_cast", {"actor": c.id, "pet": str(p.uid), "skill": ContentDB.name_of("pet_skill_books", "guardian_spirit"), "free": false})
		return true
	return false

# ------------------------------------------------------------------ pet gear (S46)
## A worn piece's share of one stat: its base, plus 10% of that a level of enhancement.
func gear_bonus(p: Dictionary, stat: String) -> float:
	var total := 0.0
	var per := float(growth().get("gear", {}).get("per_enhance", 0.1))
	for slot in p.get("equipment", {}):
		var inst = p.equipment[slot]
		if not (inst is Dictionary): continue
		total += float(ContentDB.item(str(inst.id)).get("pet_gear", {}).get(stat, 0.0)) * (1.0 + per * int(inst.get("enhance", 0)))
	return total

func equip_pet(c, uid: String, index: int) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("no_pet", {"text": Tx.t("sim.pet.no_active")})
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var def := ContentDB.item(str(c.inventory.bag[index].id))
	if not def.has("pet_gear"): return fail("not_pet_gear")
	var slot := str(def.slot)
	if slot == "pet_saddle" and not mountable(p): return fail("not_mountable", {"text": Tx.t("sim.pet.too_small_to_carry_you")})
	var inst: Dictionary = game.inventory.apply_remove_index(c.id, index, 1, "pet_gear")
	var old = p.equipment.get(slot)
	p.equipment[slot] = inst
	if old is Dictionary: game.inventory.apply_add_instance(c.id, old, "pet_gear")
	emit("pet_gear_changed", {"actor": c.id, "pet": uid, "slot": slot, "item": str(inst.id)})
	_spawn(c)
	return ok({"slot": slot})

func unequip_pet(c, uid: String, slot: String) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	var inst = p.equipment.get(slot)
	if not (inst is Dictionary): return fail("empty")
	if c.inventory.free_slots() <= 0: return fail("bag_full", {"text": Tx.t("sim.pet.bag_full")})
	p.equipment.erase(slot)
	game.inventory.apply_add_instance(c.id, inst, "pet_gear")
	emit("pet_gear_changed", {"actor": c.id, "pet": uid, "slot": slot, "item": ""})
	_spawn(c)
	return ok()

# ------------------------------------------------------------------ fusion (S46)
## Why these two cannot be fused ("" when they can): at the Beast Hall, two animals, the sacrifice unlocked.
func fusion_blocked(c, keep: Dictionary, sacrifice: Dictionary) -> String:
	if keep.is_empty() or sacrifice.is_empty() or str(keep.uid) == str(sacrifice.uid): return Tx.t("sim.pet.fuse_two")
	if sacrifice.get("locked", false): return Tx.t("sim.pet.fuse_locked") % str(sacrifice.name)
	if not _at_beast_hall(c): return Tx.t("sim.pet.fuse_where")
	return ""

## Sacrifice one animal to another: a 30% chance at each of its traits and learned skills, and half its purity above
## the kept one's. Needs a confirmation; locked animals are never fused. Its gear comes back to your gourd.
func fuse_pets(c, keep_uid: String, sac_uid: String, confirm: bool) -> Dictionary:
	var a := _pet(c, keep_uid)
	var b := _pet(c, sac_uid)
	var why := fusion_blocked(c, a, b)
	if why != "": return fail("cannot_fuse", {"text": why})
	if not confirm: return fail("confirm", {"text": Tx.t("sim.pet.fuse_confirm") % [str(b.name), str(a.name)]})
	var cfg: Dictionary = growth().get("fusion", {})
	var rng := Rng.stream(c.id, "pet")
	var got_traits: Array = []
	var traits: Array = a.get("traits", [])
	for t in b.get("traits", []):
		if traits.has(t) or rng.randf() >= float(cfg.get("trait_chance", 0.3)): continue
		# A new trait takes the place of one still hidden; with none hidden it joins the shown ones.
		if int(a.get("revealed", 0)) < traits.size(): traits[traits.size() - 1] = t
		elif traits.size() < int(cfg.get("max_traits", 5)):
			traits.append(t)
			a.revealed = int(a.get("revealed", 0)) + 1
		else: continue
		got_traits.append(t)
	a.traits = traits
	var got_skills: Array = []
	for sk in b.get("learned_skills", []):
		if has_skill(a, str(sk)) or skill_slots(a) <= 0 or rng.randf() >= float(cfg.get("skill_chance", 0.3)): continue
		_learn(c, a, str(sk))
		got_skills.append(sk)
	var gain := 0
	if int(b.get("purity", 0)) > int(a.get("purity", 0)): gain = int(floor((int(b.purity) - int(a.purity)) * float(cfg.get("purity_share", 0.5))))
	for slot in b.get("equipment", {}):
		if b.equipment[slot] is Dictionary: game.inventory.apply_add_instance(c.id, b.equipment[slot], "fusion")
	c.pets.erase(b)
	c.party_pets.erase(sac_uid)
	if c.active_pet == sac_uid: c.active_pet = keep_uid
	if gain > 0: add_purity(c, a, gain)
	emit("pets_fused", {"actor": c.id, "keep": keep_uid, "sacrifice": sac_uid, "traits": got_traits, "skills": got_skills, "purity": gain})
	_spawn(c)
	return ok({"traits": got_traits, "skills": got_skills, "purity": gain})

# ------------------------------------------------------------------ pet breakthroughs and core grade (S46)
func core_grade_def(id: String) -> Dictionary:
	for g in growth().get("core_grades", []):
		if str(g.id) == id: return g
	return {}

func core_bonus(p: Dictionary) -> float:
	return float(core_grade_def(str(p.get("core_grade", ""))).get("bonus", 0.0))

## What a support item adds to a breakthrough: a core of the animal's own element by tier, or essence blood.
func support_value(p: Dictionary, item: String) -> float:
	var sup: Dictionary = growth().get("breakthrough", {}).get("support", {})
	if sup.has(item): return float(sup[item])
	var core: Dictionary = ContentDB.item(item).get("core", {})
	if core.has("tier") and str(core.element) == str(ContentDB.entry("pets", str(p.get("species", ""))).get("element", "")): return float(sup.get(str(core.tier), 0.0))
	return 0.0

## The chance of a pet breakthrough with these support items (three at most, each one you hold).
func breakthrough_chance(c, p: Dictionary, support: Array) -> float:
	var cfg: Dictionary = growth().get("breakthrough", {})
	var chance := float(cfg.get("base", 0.55)) + float(p.get("purity", 0)) * float(cfg.get("per_purity", 0.002))
	for item in support.slice(0, int(cfg.get("max_support", 3))): chance += support_value(p, str(item))
	return clampf(chance, 0.0, float(cfg.get("cap", 0.95)))

## From Awakened on a stage-up is a breakthrough: the gates as for any stage, then a roll. A failure costs a heart
## or leaves a Grievous Wound. Adult to Awakened is Pet Core Formation: it also rolls the core grade.
func pet_breakthrough(c, uid: String, support: Array, branch: String) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	var nx := next_stage(p)
	if nx.is_empty(): return fail("final_stage", {"text": Tx.t("sim.pet.it_has_grown_as_far")})
	var cfg: Dictionary = growth().get("breakthrough", {})
	if stage_index(str(nx.id)) < stage_index(str(cfg.get("from", "awakened"))): return fail("not_a_breakthrough")
	for g in evolve_gates(c, p):
		if not g.ok: return fail("not_ready", {"text": Tx.t("sim.pet.needs") + str(g.text)})
	if p.get("wounded", false): return fail("wounded", {"text": Tx.t("sim.pet.heal_first") % str(p.name)})
	var used: Array = []
	var need := {}
	for item in support.slice(0, int(cfg.get("max_support", 3))):
		if support_value(p, str(item)) <= 0.0: continue
		need[str(item)] = int(need.get(str(item), 0)) + 1
		if c.inventory.count(str(item)) < int(need[str(item)]): return fail("no_support", {"text": Tx.t("sim.pet.needs_item") % ContentDB.item_name(str(item))})
		used.append(str(item))
	var chance := breakthrough_chance(c, p, used)
	for item in used: game.inventory.apply_remove(c.id, item, 1, "pet_breakthrough")
	var rng := Rng.stream(c.id, "pet")
	var success := rng.randf() < chance
	var result := {"success": success, "chance": chance}
	if success:
		var forming := str(p.stage) == "adult"
		p["_breaking"] = true
		var ev := evolve(c, uid, branch)
		p.erase("_breaking")
		if not ev.get("ok", false): return ev
		if forming: result.core_grade = _form_core(c, p, used.size(), rng)
	elif rng.randf() < float(cfg.get("fail_heart_share", 0.5)):
		p.bond = maxf(0.0, float(p.bond) - 1.0)
		result.lost = "heart"
	else:
		p.wounded = true
		result.lost = "wound"
		emit("pet_wounded", {"actor": c.id, "pet": uid})
	emit("pet_breakthrough", {"actor": c.id, "pet": uid, "success": success, "chance": chance, "lost": str(result.get("lost", ""))})
	return ok(result)

## Pet Core Formation: points from purity, growth, support and a roll set the grade and its bonus to every stat.
func _form_core(c, p: Dictionary, supports: int, rng: RandomNumberGenerator) -> String:
	var cp: Dictionary = growth().get("core_points", {})
	var pts := float(p.get("purity", 0)) * float(cp.get("per_purity", 0.5)) + (float(p.get("growth", 1.0)) - 0.8) * float(cp.get("per_growth", 60)) \
		+ supports * float(cp.get("per_support", 8)) + rng.randf() * float(cp.get("roll", 20))
	var grade := "cracked"
	for g in growth().get("core_grades", []):
		if pts >= float(g.get("min", 0)): grade = str(g.id)
	p.core_grade = grade
	emit("pet_core_formed", {"actor": c.id, "pet": str(p.uid), "grade": grade, "points": pts})
	_spawn(c)
	return grade

# ------------------------------------------------------------------ rarity rolls (S46)
## A tamed beast or a plain egg rolls its rarity (bred eggs keep their parents'); table: tame, tame_elite, egg, rare.
func roll_rarity(c, table: String) -> String:
	var weights: Dictionary = growth().get("rarity_roll", {}).get(table, {})
	if weights.is_empty(): return "common"
	var rng := Rng.stream(c.id if c != null else "account", "bloodline")
	var total := 0.0
	for k in weights: total += float(weights[k])
	var roll := rng.randf() * total
	for k in weights:
		roll -= float(weights[k])
		if roll <= 0.0: return str(k)
	return str(weights.keys()[0])

# ------------------------------------------------------------------ Spirit Beast Bag and field swaps (S46)
## Carried-pet slots: the best Spirit Beast Bag you own (0 without one).
func bag_capacity(c) -> int:
	var best := 0
	for st in (c.inventory.key_items as Array) + (c.inventory.bag as Array):
		if st == null: continue
		best = maxi(best, int(ContentDB.item(str(st.id)).get("beast_bag", {}).get("slots", 0)))
	return best

## A town, a sect, a rest stop or home: animals can be called from anywhere.
func safe_room() -> bool:
	return game.room_rt == null or str(game.room_rt.def.get("type", "")) in growth().get("safe_rooms", ["town", "sect", "rest", "home", "interior"])

## A foe near you is fighting (not idle, wandering or passive).
func in_combat(c) -> bool:
	if game.room_rt == null: return false
	var st: ActorState = game.actor_state(c.id)
	if st == null: return false
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden or e.def.get("passive", false): continue
		if not str(e.ai.get("state", "idle")) in ["aggro", "attack", "windup", "recover", "stagger", "detonating"]: continue
		if e.plane.distance_to(st.plane) <= float(growth().get("combat_reach", 600)): return true
	return false

## Why this animal cannot be called to your side here ("" when it can): never in a fight; in the field only from the bag.
func call_blocked(c, uid: String) -> String:
	if uid == "": return ""
	if in_combat(c): return Tx.t("sim.pet.not_in_combat")
	var p := _pet(c, uid)
	if mount_only(p): return Tx.t("sim.pet.mount_only") % str(p.name)
	if safe_room() or c.pet_bag.has(uid) or uid == c.active_pet or c.party_pets.has(uid): return ""
	return Tx.t("sim.pet.not_carried") % str(p.get("name", ""))

## Put an animal in the Spirit Beast Bag (or take it out), up to the bag's slots. Packing happens somewhere safe.
func set_pet_bag(c, uid: String, on: bool) -> Dictionary:
	var p := _pet(c, uid)
	if p.is_empty(): return fail("unknown_pet")
	c.pet_bag = c.pet_bag.filter(func(u): return str(u) != uid and not _pet(c, str(u)).is_empty())
	if on:
		var cap := bag_capacity(c)
		if cap <= 0: return fail("no_bag", {"text": Tx.t("sim.pet.no_bag")})
		if not safe_room(): return fail("not_safe", {"text": Tx.t("sim.pet.pack_safe")})
		if c.pet_bag.size() >= cap: return fail("bag_full", {"text": Tx.t("sim.pet.bag_slots") % cap})
		c.pet_bag.append(uid)
	emit("pet_changed", {"actor": c.id, "pet": uid})
	return ok({"bag": c.pet_bag.duplicate()})

## The field swap: a carried animal takes the active place; the one it replaces goes into its slot in the bag.
func swap_from_bag(c, uid: String) -> Dictionary:
	if not c.pet_bag.has(uid) or _pet(c, uid).is_empty(): return fail("not_carried", {"text": Tx.t("sim.pet.not_carried") % str(_pet(c, uid).get("name", ""))})
	if in_combat(c): return fail("in_combat", {"text": Tx.t("sim.pet.not_in_combat")})
	var old: String = c.active_pet
	var i: int = c.pet_bag.find(uid)
	if old != "" and not _pet(c, old).is_empty(): c.pet_bag[i] = old
	else: c.pet_bag.remove_at(i)
	c.active_pet = uid
	c.party_pets.erase(uid)
	_spawn(c)
	emit("pet_swapped", {"actor": c.id, "pet": uid, "from": old})
	emit("pet_changed", {"actor": c.id, "pet": uid})
	return ok({"from": old})
