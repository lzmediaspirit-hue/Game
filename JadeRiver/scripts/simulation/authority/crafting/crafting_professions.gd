class_name CraftingProfessions
extends CraftingPart
## CraftingAuthority's part: profession ranks and their XP, the grade a realm may craft, the best tool carried for a
## craft, and whether a station stands near.

# ------------------------------------------------------------------ professions
func rank_of(c, craft: String) -> String:
	return str(c.professions.get(craft, {}).get("rank", "apprentice"))

func rank_index(rank: String) -> int:
	var ranks: Array = ContentDB.curve("profession_ranks", [])
	for i in ranks.size():
		if ranks[i][0] == rank: return i
	return 0

func rank_cap(c, craft: String) -> int:
	var cap := 0
	for row in CraftingAuthority.RANK_CAPS.get(craft, [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"]]):
		if ProgressionRules.at_least(c.cultivator.realm_key, str(row[0])): cap = rank_index(str(row[1]))
	return cap

func add_xp(c, craft: String, xp: float) -> void:
	var p: Dictionary = c.professions.get(craft, {"rank": "apprentice", "xp": 0.0})
	p.xp = float(p.xp) + xp
	var ranks: Array = ContentDB.curve("profession_ranks", [])
	var idx := rank_index(str(p.rank))
	var cap := rank_cap(c, craft)
	while idx + 1 < ranks.size() and idx + 1 <= cap and float(p.xp) >= float(ranks[idx + 1][1]):
		idx += 1
		p.rank = ranks[idx][0]
		emit("profession_rank_up", {"actor": c.id, "craft": craft, "rank": p.rank})
	c.professions[craft] = p

func grade_cap(c) -> String:
	var g := "plain"
	for row in CraftingAuthority.GRADE_CAP:
		if ProgressionRules.at_least(c.cultivator.realm_key, str(row[0])): g = str(row[1])
	return g

func tool_power(c, craft: String) -> float:
	var best := 0.0
	for s in c.inventory.bag:
		if s == null: continue
		var t: Dictionary = ContentDB.item(str(s.id)).get("tool", {})
		if str(t.get("craft", "")) == craft: best = maxf(best, float(t.get("power", 1.0)))
	for k in c.inventory.key_items:
		var t2: Dictionary = ContentDB.item(str(k.id)).get("tool", {})
		if str(t2.get("craft", "")) == craft: best = maxf(best, float(t2.get("power", 1.0)))
	return best

func station_near(c, types: Array) -> bool:
	var st: ActorState = game.actor_state(c.id)
	if game.room_rt == null: return false
	for o in game.room_rt.def.get("objects", []):
		if o.type in types:
			if st == null: return true
			var at: Array = o.get("at", [0, 0])
			if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) < 180.0: return true
	return false
