class_name CraftingGarden
extends CraftingPart
## CraftingAuthority's part: the herb garden (S45): beds, seeds and harvests, the Verdant Dew Vial and spring water, the
## processing racks, raids on unguarded beds and transplanting a rare herb; and the Evergreen Heart Tree.

# ------------------------------------------------------------------ S45 garden beds
## Beds are room objects; each character keeps its own record of every bed it tends, keyed "room:object":
## {herb, progress (0..1), updated (utc), grow_s, soil}. Growth is settled from the clock, so it runs offline.
func beds(c) -> Dictionary:
	if not (c.crafting.get("garden") is Dictionary): c.crafting["garden"] = {}
	return c.crafting.garden

func bed_def(key: String) -> Dictionary:
	var room := key.get_slice(":", 0)
	for o in ContentDB.room(room).get("objects", []):
		if str(o.get("id", "")) == key.get_slice(":", 1) and str(o.get("type", "")) == "garden_bed": return o
	return {}

func bed_record(c, key: String) -> Dictionary:
	var b := beds(c)
	if not b.has(key): b[key] = {"herb": "", "progress": 0.0, "updated": 0.0, "grow_s": 1.0, "soil": 0}
	return b[key]

## Low / Mid / High: the bed's own grade plus the Spirit Soil worked into it.
func bed_grade(c, key: String) -> String:
	var grades: Array = ContentDB.config("garden").get("field_grades", ["low", "mid", "high"])
	var i := grades.find(str(bed_def(key).get("field_grade", "low"))) + int(bed_record(c, key).get("soil", 0))
	return str(grades[clampi(i, 0, grades.size() - 1)])

## Can this bed hold a herb of this grade?
func bed_holds(c, key: String, herb: String) -> bool:
	var cap := str(ContentDB.config("garden").get("field_cap", {}).get(bed_grade(c, key), "earth"))
	return StatRules.grade_index(str(ContentDB.item(herb).get("grade", "plain"))) <= StatRules.grade_index(cap)

## A room's Qi speeds its beds by half its bonus.
func bed_speed(key: String) -> float:
	var qi := float(ContentDB.room(key.get_slice(":", 0)).get("qi", 1.0))
	return maxf(0.25, 1.0 + (qi - 1.0) * float(ContentDB.config("garden").get("qi_growth", 0.5)))

func settle_bed(c, key: String) -> Dictionary:
	var rec := bed_record(c, key)
	var now := Clock.now_utc()
	if str(rec.herb) != "" and float(rec.updated) > 0.0:
		var el := Clock.elapsed_since(float(rec.updated))
		if el.valid: rec.progress = minf(1.0, float(rec.progress) + float(el.elapsed) * bed_speed(key) / maxf(1.0, float(rec.grow_s)))
	rec.updated = now
	return rec

## What the Garden page shows for a bed.
func bed_view(c, key: String) -> Dictionary:
	var rec := settle_bed(c, key)
	var left := (1.0 - float(rec.progress)) * float(rec.grow_s) / bed_speed(key) if str(rec.herb) != "" else 0.0
	return {"key": key, "herb": str(rec.herb), "age": HerbRules.item_age(str(rec.herb)) if str(rec.herb) != "" else 0, "progress": float(rec.progress),
		"seconds": left, "ready": str(rec.herb) != "" and float(rec.progress) >= 1.0, "grade": bed_grade(c, key), "soil": int(rec.get("soil", 0))}

## The beds a character can tend in a room.
func room_beds(c, room_id: String) -> Array:
	var out: Array = []
	for o in ContentDB.room(room_id).get("objects", []):
		if str(o.get("type", "")) == "garden_bed" and game.world.object_visible(c, o) and (not o.has("requires") or RequirementRules.passes(o.requires, game.ctx(c))):
			out.append(room_id + ":" + str(o.id))
	return out

func bed_check(c, key: String) -> String:
	if not Unlocks.is_unlocked(c.id, "herb_garden"): return Unlocks.locked_text("herb_garden")
	if bed_def(key).is_empty(): return Tx.t("sim.crafting.no_such_bed")
	# Decision 43: beds are tended where they grow, and from anywhere after the first harvest (earned remote access).
	if (game.room_rt == null or game.room_rt.room_id != key.get_slice(":", 0)) and not PlaceRules.remote_open(c, "herb_garden"):
		return Tx.t("sim.crafting.bed_elsewhere")
	return ""

func plant_seed(c, key: String, seed: String) -> Dictionary:
	var why := bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var fam := str(ContentDB.item(seed).get("seed", {}).get("family", ""))
	if fam == "" or c.inventory.count(seed) <= 0: return fail("no_seed")
	var rec := settle_bed(c, key)
	if str(rec.herb) != "": return fail("planted", {"text": Tx.t("sim.crafting.bed_taken")})
	var herb := str(ContentDB.config("garden").get("families", {}).get(fam, {}).get("10", ""))
	if not bed_holds(c, key, herb): return fail("soil", {"text": Tx.t("sim.crafting.soil_too_poor") % ContentDB.item_name(herb)})
	game.inventory.apply_remove(c.id, seed, 1, "garden")
	rec.herb = herb
	rec.progress = 0.0
	rec.grow_s = float(ContentDB.config("garden").get("grow_hours", {}).get(fam, 4)) * 3600.0
	rec.updated = Clock.now_utc()
	rec.raid_day = Clock.reset_day(Clock.now_utc())
	emit("herb_planted", {"actor": c.id, "bed": key, "herb": herb})
	emit("system_used", {"actor": c.id, "system": "plant_seed"})
	return ok({"herb": herb})

## Bottled spring water hurries the herb in a bed by a quarter of its growth.
func water_bed(c, key: String) -> Dictionary:
	var why := bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var rec := settle_bed(c, key)
	if str(rec.herb) == "" or float(rec.progress) >= 1.0: return fail("nothing_to_water")
	if c.inventory.count("spring_water") <= 0: return fail("no_water", {"text": Tx.t("sim.crafting.no_spring_water")})
	game.inventory.apply_remove(c.id, "spring_water", 1, "garden")
	rec.progress = minf(1.0, float(rec.progress) + float(ContentDB.config("garden").get("water", {}).get("growth", 0.25)))
	emit("bed_watered", {"actor": c.id, "bed": key, "progress": float(rec.progress)})
	return ok({"progress": float(rec.progress)})

func harvest_bed(c, key: String) -> Dictionary:
	var why := bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var rec := settle_bed(c, key)
	if str(rec.herb) == "" or float(rec.progress) < 1.0: return fail("not_ready")
	var herb := str(rec.herb)
	var g := ContentDB.config("garden")
	var rng := Rng.stream(c.id, "garden")
	var y: Array = g.get("bed_yield", {}).get("young" if HerbRules.item_age(herb) <= 10 else "aged", [1, 1])
	var count := rng.randi_range(int(y[0]), int(y[1]))
	game.inventory.apply_add(c.id, herb, count, "garden")
	var seed := str(g.get("seeds", {}).get(HerbRules.family(herb), ""))
	if seed != "" and HerbRules.item_age(herb) <= 10 and rng.randf() < float(g.get("seed_back", 0.2)):
		game.inventory.apply_add(c.id, seed, 1, "garden")
		emit("seed_found", {"actor": c.id, "seed": seed, "object": key})
	else:
		seed = ""
	rec.herb = ""
	rec.progress = 0.0
	crafting.add_xp(c, "herb_gathering", float(ContentDB.curve("profession_xp.gather", 5)))
	emit("herb_harvested", {"actor": c.id, "object": key, "item": herb, "age": HerbRules.item_age(herb), "perfect": false, "early": false, "bed": true})
	PlaceRules.note_use(game, c, "herb_garden")   # decision 43: the first harvest opens the tending from anywhere
	return ok({"item": herb, "count": count, "seed": seed})

## Spirit Soil raises a bed's field grade one step, for good.
func apply_spirit_soil(c, key: String) -> Dictionary:
	var why := bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	if c.inventory.count("spirit_soil") <= 0: return fail("no_soil")
	var grades: Array = ContentDB.config("garden").get("field_grades", ["low", "mid", "high"])
	if bed_grade(c, key) == str(grades.back()): return fail("max", {"text": Tx.t("sim.crafting.bed_at_best")})
	game.inventory.apply_remove(c.id, "spirit_soil", 1, "garden")
	var rec := bed_record(c, key)
	rec.soil = int(rec.get("soil", 0)) + 1
	emit("bed_enriched", {"actor": c.id, "bed": key, "grade": bed_grade(c, key)})
	return ok({"grade": bed_grade(c, key)})

# ------------------------------------------------------------------ the Verdant Dew Vial and spring water
## One dew a day, offline too, up to the vial's three. {dew, cap, next_s, has}
func dew_state(c) -> Dictionary:
	var k: Dictionary = ContentDB.config("garden").get("dew", {})
	var has := crafting.tool_power(c, "garden_dew") > 0.0
	if not (c.crafting.get("dew") is Dictionary): c.crafting["dew"] = {"count": 0, "last": 0.0}
	var d: Dictionary = c.crafting.dew
	var every := float(k.get("every_s", 86400))
	var cap := int(k.get("cap", 3))
	if not has: return {"dew": 0, "cap": cap, "next_s": 0.0, "has": false}
	var now := Clock.now_utc()
	if float(d.last) <= 0.0: d.last = now
	var el := Clock.elapsed_since(float(d.last))
	if not el.valid: d.last = now
	var n := int(floor(float(el.elapsed) / every)) if el.valid else 0
	if n > 0:
		d.count = mini(cap, int(d.count) + n)
		d.last = float(d.last) + n * every
	if int(d.count) >= cap: d.last = now   # a full vial doesn't bank time toward the next drop
	return {"dew": int(d.count), "cap": cap, "next_s": maxf(0.0, float(d.last) + every - now), "has": true}

## How old the land's Qi lets a bed's herb grow: a thousand years in the valley, ten thousand in the Azure Expanse.
func dew_age_cap(key: String) -> int:
	var k: Dictionary = ContentDB.config("garden").get("dew", {})
	var zone := str(ContentDB.room(key.get_slice(":", 0)).get("zone", ""))
	return int(k.get("expanse_age_cap", 10000)) if zone in k.get("expanse_zones", ["azure_expanse"]) else int(k.get("valley_age_cap", 1000))

## A drop of dew ages the herb in a bed one tier, as far as the land's Qi allows (dew_age_cap).
func use_dew(c, key: String) -> Dictionary:
	var why := bed_check(c, key)
	if why != "": return fail("bed", {"text": why})
	var ds := dew_state(c)
	if int(ds.dew) <= 0: return fail("no_dew", {"text": Tx.t("sim.crafting.no_dew")})
	var rec := settle_bed(c, key)
	if str(rec.herb) == "": return fail("empty")
	var older: Array = HerbRules.older_than(str(rec.herb))
	var cap_age := dew_age_cap(key)
	if older.is_empty() or HerbRules.item_age(str(older[0])) > cap_age:
		return fail("age_cap", {"text": Tx.t("sim.crafting.dew_age_top" if older.is_empty() or cap_age > int(ContentDB.config("garden").get("dew", {}).get("valley_age_cap", 1000))
			else "sim.crafting.dew_age_cap")})
	if not bed_holds(c, key, str(older[0])): return fail("soil", {"text": Tx.t("sim.crafting.soil_too_poor") % ContentDB.item_name(str(older[0]))})
	c.crafting.dew.count = int(c.crafting.dew.count) - 1
	var was := str(rec.herb)
	rec.herb = str(older[0])
	emit("herb_aged", {"actor": c.id, "bed": key, "from": was, "herb": str(rec.herb), "age": HerbRules.item_age(str(rec.herb))})
	return ok({"herb": str(rec.herb)})

## A Qi spring gives three bottles a reset day (S45).
func bottle_spring_water(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "herb_garden"): return fail("locked")
	var per := int(ContentDB.config("garden").get("water", {}).get("per_day", 3))
	var day := Clock.reset_day(Clock.now_utc())
	if not (c.crafting.get("spring") is Dictionary) or int(c.crafting.spring.get("day", -1)) != day: c.crafting["spring"] = {"day": day, "count": 0}
	if int(c.crafting.spring.count) >= per: return fail("spent", {"text": Tx.t("sim.crafting.spring_spent")})
	game.inventory.apply_add(c.id, "spring_water", 1, "spring")
	c.crafting.spring.count = int(c.crafting.spring.count) + 1
	var left := per - int(c.crafting.spring.count)
	emit("spring_bottled", {"actor": c.id, "left": left})
	return ok({"text": Tx.t("sim.crafting.spring_bottled") % left, "left": left})

# ------------------------------------------------------------------ processing racks (S45)
## Herbs on the drying rack: [{kind, herb, count, done}]. They finish on the clock, offline too.
func racks(c) -> Array:
	if not (c.crafting.get("racks") is Array): c.crafting["racks"] = []
	return c.crafting.racks

func start_rack(c, kind: String, herb: String, count: int) -> Dictionary:
	var g: Dictionary = ContentDB.config("garden").get("racks", {})
	var rk: Dictionary = g.get(kind, {}) if g.get(kind) is Dictionary else {}
	if rk.is_empty(): return fail("unknown_rack")
	if crafting.tool_power(c, "alchemy") <= 0.0: return fail("no_rack", {"text": Tx.t("sim.crafting.need_drying_rack")})
	if racks(c).size() >= int(g.get("slots", 2)): return fail("racks_full", {"text": Tx.t("sim.crafting.racks_full")})
	if str(ContentDB.item(herb).get("type", "")) != "herb": return fail("not_herb")
	count = clampi(count, 1, int(g.get("max", 10)))
	if game.inventory.count_prep(c, herb, "") < count: return fail("too_few", {"text": Tx.t("sim.crafting.rack_too_few") % ContentDB.item_name(herb)})
	var jars := 0
	if rk.has("needs"):
		jars = int(ceil(count / float(rk.get("per", 5))))
		if c.inventory.count(str(rk.needs)) < jars: return fail("needs", {"text": Tx.t("sim.crafting.rack_needs") % [jars, ContentDB.item_name(str(rk.needs))]})
		game.inventory.apply_remove(c.id, str(rk.needs), jars, "rack")
	game.inventory.take_ranked(c.id, herb, count, "rack", func(st): return (0 if str(st.get("prep", "")) == "" else 2) + (1 if st.get("unappraised", false) else 0))
	var job := {"kind": kind, "herb": herb, "count": count, "done": Clock.now_utc() + float(rk.get("hours", 1)) * 3600.0}
	racks(c).append(job)
	emit("rack_started", {"actor": c.id, "kind": kind, "herb": herb, "count": count, "seconds": float(job.done) - Clock.now_utc()})
	return ok({"done": float(job.done)})

## Takes every finished rack's herbs off: they come back marked steamed or wine-soaked.
func collect_racks(c) -> Dictionary:
	var now := Clock.now_utc()
	var got := 0
	for job in racks(c).duplicate():
		if float(job.done) > now: continue
		game.inventory.apply_add(c.id, str(job.herb), int(job.count), "rack", {"prep": str(job.kind)})
		racks(c).erase(job)
		got += int(job.count)
		emit("rack_collected", {"actor": c.id, "kind": str(job.kind), "herb": str(job.herb), "count": int(job.count)})
	if got == 0: return fail("nothing_ready")
	return ok({"count": got})

# ------------------------------------------------------------------ garden raids (S45)
## Once a reset day, an unguarded planted bed may be raided while you are away: pests halve its growth, a thief takes
## the herb. Checked when you come back (enter the world, or a room). Returns the raids.
func check_raids(c) -> Array:
	var g: Dictionary = ContentDB.config("garden").get("raids", {})
	var now := Clock.now_utc()
	var today := Clock.reset_day(now)
	var out: Array = []
	for key in beds(c).keys():
		var rec: Dictionary = beds(c)[key]
		if str(rec.get("herb", "")) == "": continue
		var last := int(rec.get("raid_day", -1))
		rec.raid_day = today
		if last < 0 or today <= last: continue
		var rng := Rng.stream(c.id, "garden")
		for d in range(last + 1, mini(today, last + int(g.get("max_days", 14))) + 1):
			if _bed_guarded(c, str(key), d): continue
			if rng.randf() >= float(g.get("chance", 0.08)): continue
			settle_bed(c, str(key))
			var thief := rng.randf() < float(g.get("thief_share", 0.5))
			var herb := str(rec.herb)
			if thief: rec.herb = ""
			else: rec.progress = float(rec.progress) * 0.5
			out.append({"bed": str(key), "kind": "thief" if thief else "pests", "herb": herb})
			emit("garden_raided", {"actor": c.id, "bed": str(key), "kind": "thief" if thief else "pests", "herb": herb})
			game.mail.apply_send(c.id, "garden_raid_" + ("thief" if thief else "pests"), [], {"herb": ContentDB.item_name(herb),
				"place": str(ContentDB.room(str(key).get_slice(":", 0)).get("name", ""))})
			if thief: break
	return out

## A pet on Guard duty, or a Protection or Concealment formation burning in the bed's room that day, keeps raiders off.
func _bed_guarded(c, key: String, day: int) -> bool:
	if not game.pets.guard_pet(c).is_empty(): return true
	var guards: Array = ContentDB.config("garden").get("raids", {}).get("guards", [])
	var day_start := day * 86400.0 - Clock.tz_offset_s() + float(ContentDB.curve("resets.daily_hour", 4)) * 3600.0
	for f in _state_formations(c):
		if str(f.get("type", "")) in guards and str(f.get("room", "")) == key.get_slice(":", 0) and float(f.get("until_utc", 0.0)) >= day_start: return true
	return false

func _state_formations(c) -> Array:
	var list = c.crafting.get("formations", [])
	return list if list is Array else []

# ------------------------------------------------------------------ transplanting (S45)
## Can this character dig up a rare herb? A Spirit Spade and Expert gathering.
func can_transplant(c) -> bool:
	var need := str(ContentDB.config("garden").get("transplant", {}).get("rank", "expert"))
	return crafting.tool_power(c, "transplant") > 0.0 and crafting.rank_index(crafting.rank_of(c, "herb_gathering")) >= crafting.rank_index(need)

## The odds it dies on the way: 25% at Expert, 5% less per rank above.
func transplant_death(c) -> float:
	var t: Dictionary = ContentDB.config("garden").get("transplant", {})
	var above := crafting.rank_index(crafting.rank_of(c, "herb_gathering")) - crafting.rank_index(str(t.get("rank", "expert")))
	return maxf(0.0, float(t.get("death", 0.25)) - float(t.get("per_rank", 0.05)) * maxi(0, above))

## Dig a rare herb up whole and move it, at its age, to the first free bed that can hold it (grown and ready).
## Picked before it ripens it is a tier younger, as a pick would be. Either way the node is spent until its next
## ripening.
func transplant(c, object_id: String) -> Dictionary:
	var rt: RoomRuntime = game.room_rt
	if rt == null: return fail("no_room")
	var o := rt.object_def(object_id)
	if o.is_empty() or str(o.get("type", "")) != "herb_patch" or not o.has("ripen"): return fail("not_rare")
	if not can_transplant(c): return fail("cannot", {"text": Tx.t("sim.crafting.transplant_needs")})
	var avail: Dictionary = game.world.object_available(c, o)
	if not avail.ok: return fail("unavailable", {"text": str(avail.get("text", ""))})
	var guard: String = game.world.herb_guard_text(c, o)
	if guard != "": return fail("guarded", {"text": guard})
	var now := Clock.now_utc()
	var herb := HerbRules.aged_down(str(o.item), 0 if bool(HerbRules.ripen_state(o, now).ripe) else 1)
	var target := ""
	for key in beds(c).keys() + _known_bed_keys(c):
		if str(settle_bed(c, str(key)).herb) == "" and bed_holds(c, str(key), herb):
			target = str(key)
			break
	if target == "": return fail("no_bed", {"text": Tx.t("sim.crafting.no_free_bed") % ContentDB.item_name(herb)})
	game.world.apply_node_depleted(c, object_id, maxf(60.0, HerbRules.regrow_at(o, now) - now))
	var died := Rng.stream(c.id, "garden").randf() < transplant_death(c)
	if not died:
		var rec := bed_record(c, target)
		rec.herb = herb
		rec.progress = 1.0
		rec.grow_s = float(ContentDB.config("garden").get("grow_hours", {}).get(HerbRules.family(herb), 4)) * 3600.0
		rec.updated = now
		rec.raid_day = Clock.reset_day(now)
	emit("transplant_result", {"actor": c.id, "object": object_id, "herb": herb, "ok": not died, "bed": target})
	return ok({"herb": herb, "survived": not died, "bed": target})

## Every bed the character can use, in rooms it has been to (a transplant looks for room in any of them).
func _known_bed_keys(c) -> Array:
	var out: Array = []
	for rid in ContentDB.rooms:
		if not game.account.visited_rooms.has(rid): continue
		for key in room_beds(c, str(rid)):
			if not out.has(key): out.append(key)
	return out

# ------------------------------------------------------------------ natural treasures
## The Evergreen Heart Tree: one per character, planted in rich earth; its first fruit comes a
## day later, then one each season. Pure query: where it grows and whether a fruit is ready.
func evergreen_state(c) -> Dictionary:
	var tree: Dictionary = c.crafting.get("evergreen", {})
	if tree.is_empty(): return {"planted": false}
	var cfg: Dictionary = ContentDB.stat_const("treasures", {})
	var season_s := float(cfg.get("season_days", 7)) * 86400.0
	var first_s := float(cfg.get("first_fruit_h", 24)) * 3600.0
	var age := Clock.now_utc() - float(tree.get("planted_utc", 0.0))
	var season := int(floor((age - first_s) / season_s)) if age >= first_s else -1
	var harvested := int(tree.get("harvested", -1))
	var ready := season > harvested
	var next_utc := float(tree.get("planted_utc", 0.0)) + first_s + (0.0 if season < 0 else float(harvested + 1) * season_s)
	return {"planted": true, "room": str(tree.get("room", "")), "object": str(tree.get("object", "")), "ready": ready,
		"season": season, "next_utc": next_utc}

## Interacting with rich earth: plant the seed, or pick the season's fruit from your tree.
func tend_treasure_plot(c, o: Dictionary) -> Dictionary:
	var here: String = game.room_rt.room_id if game.room_rt else ""
	var st := evergreen_state(c)
	if not st.planted:
		if c.inventory.count("evergreen_heart_seed") <= 0: return ok({"text": Tx.t("sim.crafting.rich_earth_waits")})
		game.inventory.apply_remove(c.id, "evergreen_heart_seed", 1, "plant")
		c.crafting["evergreen"] = {"room": here, "object": str(o.id), "planted_utc": Clock.now_utc(), "harvested": -1}
		emit("system_used", {"actor": c.id, "system": "plant_evergreen"})
		emit("treasure_planted", {"actor": c.id, "treasure": "evergreen_heart_tree", "room": here})
		return ok({"text": Tx.t("sim.crafting.you_plant_the_seed")})
	if str(st.room) != here or str(st.object) != str(o.id):
		return ok({"text": Tx.t("sim.crafting.your_tree_grows_in") % ContentDB.name_of("rooms", str(st.room))})
	if st.ready:
		game.inventory.apply_add(c.id, "evergreen_heart_fruit", 1, "evergreen")
		c.crafting.evergreen.harvested = int(st.season)
		emit("treasure_harvested", {"actor": c.id, "treasure": "evergreen_heart_tree", "item": "evergreen_heart_fruit"})
		return ok({"text": Tx.t("sim.crafting.you_pick_the_fruit")})
	var hours := maxf(1.0, ceilf((float(st.next_utc) - Clock.now_utc()) / 3600.0))
	return ok({"text": Tx.t("sim.crafting.next_fruit_in") % Tx.span(hours * 3600.0)})
