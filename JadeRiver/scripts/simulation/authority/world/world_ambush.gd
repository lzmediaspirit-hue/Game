class_name WorldAmbush
extends WorldPart
## WorldAuthority's part: bandit ambushes (S48 hidden cultivation): a road room with an `ambush` may spring one as you
## come in. The rest between two is the authority's `ambush_cd`.

## The chance that a road's ambush springs on this entry. Bandits judge the realm you show, not the one you hold:
## past their reach they leave you be, and a false realm (Concealment) looks like easy prey and doubles the odds.
func ambush_chance(c, amb: Dictionary) -> float:
	var k: Dictionary = ContentDB.stat_const("ambush", {})
	var cu: CultivatorState = c.cultivator
	var shown := ProgressionRules.level_for(game.progression.shown_realm(c), cu.progress_fraction())
	var lv: Array = amb.get("level", [1, 1])
	if shown > int(lv[1]) + int(k.get("reach", 8)): return 0.0
	var chance := float(k.get("chance", 0.06))
	if cu.false_realm != "": chance *= float(k.get("concealed_mult", 2.0))
	return chance

## A road room with an `ambush` rolls once as you come in: never on a first visit, never during a room event and not
## again until the cooldown has run.
func on_room_entered_ambush(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	var rt: RoomRuntime = game.room_rt
	if c == null or rt == null or p.get("first_visit", false) or rt.event.get("active", false): return
	var amb: Dictionary = rt.def.get("ambush", {})
	if amb.is_empty() or float(world.ambush_cd.get(c.id, 0.0)) > 0.0: return
	if amb.has("requires") and not RequirementRules.passes(amb.requires, game.ctx(c)): return
	if Rng.stream(c.id, "ambush").randf() >= ambush_chance(c, amb): return
	spring_ambush(c, amb)

## The gang drops in on both sides of you. They are summoned foes: they fight like the road's own and scatter if
## you leave.
func spring_ambush(c, amb: Dictionary) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null: return
	var k: Dictionary = ContentDB.stat_const("ambush", {})
	world.ambush_cd[c.id] = float(k.get("cooldown_s", 900))
	var rng := Rng.stream(c.id, "ambush")
	var lv: Array = amb.get("level", [1, 1])
	var at := Vector2(float(c.position.get("x", 400)), float(c.position.get("y", 850)))
	var n := int(amb.get("count", 2))
	var off := float(k.get("offset", 360))
	for i in n:
		var dx := (1.0 if i % 2 == 0 else -1.0) * (off + 90.0 * floorf(i / 2.0))
		# On the floor round the player, on its own level (not in a wall, the water or a roof).
		var spot := rt.topdown.place_near(at + Vector2(dx, 0.0), rt.topdown.floor_at(at))
		game.enemies.spawn_at(str(amb.enemy), spot, rng.randi_range(int(lv[0]), int(lv[1])))
	emit("ambush_sprung", {"actor": c.id, "room": rt.room_id, "enemy": str(amb.enemy), "count": n, "concealed": c.cultivator.false_realm != ""})
