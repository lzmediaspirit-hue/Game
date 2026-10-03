class_name WorldHerbs
extends WorldPart
## WorldAuthority's part: rare herbs (S45): a rare node ripens on its clock and in its season, says so once, and wakes
## its guardian as you climb toward it. Spirit Sense and an animal's Herb Whisper leave their readouts in the
## authority's `sensed_herbs`.

## A rare node's state now: {ripe, seconds, window, dormant}.
func herb_state(o: Dictionary) -> Dictionary:
	var now := Clock.now_utc()
	var st := HerbRules.ripen_state(o, now)
	st.dormant = not HerbRules.in_season(o, now)
	return st

## Once a second: a rare node that has just ripened says so, and its guardian wakes when you climb toward it.
func tick_rare_herbs(c, rt: RoomRuntime, delta: float) -> void:
	world.herb_clock -= delta
	if world.herb_clock > 0.0: return
	world.herb_clock = 1.0
	var st: ActorState = game.actor_state(c.id)
	var whisper: float = game.pets.whisper_range(c)   # S46 Herb Whisper: an animal beside you reads the herbs near you
	for o in rt.def.get("objects", []):
		if o.type != "herb_patch" or not o.has("ripen"): continue
		var os: Dictionary = rt.objects.get(str(o.id), {})
		var hs := herb_state(o)
		var hat: Array = o.get("at", [0, 0])
		if whisper > 0.0 and st != null and st.plane.distance_to(Vector2(float(hat[0]), float(hat[1]))) <= whisper:
			world.sensed_herbs[str(o.id)] = {"until": game.sim_time + 1.5, "utc": Clock.now_utc(), "ripe": hs.ripe, "seconds": float(hs.seconds), "dormant": hs.dormant,
				"season": str(o.get("season", "")), "spent": os.get("state", "ready") == "depleted"}
		var ripe: bool = hs.ripe and not hs.dormant and os.get("state", "ready") == "ready"
		if ripe and not os.get("ripe", false):
			emit("herb_ripening", {"actor": c.id, "room": rt.room_id, "object": str(o.id), "item": str(o.item), "seconds": float(hs.seconds)})
			if not game.account.codex.has("rare_herbs"): game.quest.apply_codex("rare_herbs")
		os.ripe = ripe
		rt.objects[str(o.id)] = os
		if ripe and st != null and guardian_wakes(o, st): wake_guardian(c, o, int(hs.window))

func guardian_wakes(o: Dictionary, st: ActorState) -> bool:
	var g: Dictionary = ContentDB.config("garden").get("guardian", {})
	var at: Array = o.get("at", [0, 0])
	# The side view measures across; on the height grid the approach is on the plane, from any side.
	var d: float = absf(st.plane.x - float(at[0])) if WorldAuthority.side_view(game.room_rt) else st.plane.distance_to(Vector2(float(at[0]), float(at[1])))
	return d <= float(g.get("wake_px", 480)) and st.altitude >= float(o.get("alt", 0)) - float(g.get("wake_below", 60))

## The guardian rises once per ripening (S45): an elite of the room's roster, on the ground under the node.
func wake_guardian(c, o: Dictionary, window: int) -> EnemyState:
	var gd: Dictionary = o.get("guardian", {})
	var rt: RoomRuntime = game.room_rt
	if gd.is_empty() or gd.get("boss", false) or rt == null: return null
	var mem := world.room_mem(c, rt.room_id)
	if not mem.has("guardians"): mem.guardians = {}
	if int(mem.guardians.get(str(o.id), -999)) == window: return null
	mem.guardians[str(o.id)] = window
	var at: Array = o.get("at", [0, 0])
	var under := Vector2(float(at[0]), 840.0)
	if not WorldAuthority.side_view(rt): under = rt.topdown.place_near(Vector2(float(at[0]), float(at[1])), 0.0, 6)   # the ground below the node, on the grid
	var e: EnemyState = game.enemies.spawn_at(str(gd.enemy), under, int(gd.get("level", -1)), {"elite": gd.get("elite", true)})
	if e == null: return null
	rt.guardians[str(o.id)] = e.uid
	emit("guardian_spawned", {"actor": c.id, "room": rt.room_id, "object": str(o.id), "enemy": str(gd.enemy), "uid": e.uid})
	return e

## Why a ripe node can't be picked yet ("" if it can). Kill the guardian, lure it past its leash, or pick the herb
## unseen: with Concealment, a guardian that hasn't noticed you doesn't stop you.
func herb_guard_text(c, o: Dictionary) -> String:
	var gd: Dictionary = o.get("guardian", {})
	var rt: RoomRuntime = game.room_rt
	if gd.is_empty() or rt == null: return ""
	var hs := herb_state(o)
	if not hs.ripe: return ""   # an early pick finds no guardian: they rise with the ripening
	var at: Array = o.get("at", [0, 0])
	var node := Vector2(float(at[0]), float(at[1]))
	var leash := float(ContentDB.config("garden").get("guardian", {}).get("leash_px", 600))
	var unseen: bool = "concealment" in c.cultivator.secret_arts
	var keeper: EnemyState = null
	if gd.get("boss", false):
		for e in rt.living_enemies():
			if e.def_id == str(gd.enemy) and e.plane.distance_to(node) <= leash: keeper = e
	else:
		if int(world.room_mem(c, rt.room_id).get("guardians", {}).get(str(o.id), -999)) != int(hs.window):
			keeper = wake_guardian(c, o, int(hs.window))
		else:
			var uid := int(rt.guardians.get(str(o.id), -1))
			var e2 = rt.enemies.get(uid)
			if e2 != null and e2.alive and e2.plane.distance_to(node) <= leash: keeper = e2
	if keeper == null: return ""
	if unseen and not str(keeper.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"]: return ""
	return Tx.t("sim.world.herb_guarded") % ContentDB.name_of("enemies", keeper.def_id)
