class_name HudActions
extends HudPart
## What a control asks of the game: the context in reach (talk, gather, open, enter, climb), the harvest's hold and tap,
## a place's pose before its page, Keeping Post, the quick slots, the Draught, the treasures, the weapon swap, the
## Presence and the Sphere.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

func tick_channel(delta: float) -> void:
	if hud.channel.object == "" or not hud.bound(): return
	if hud.player.last_axis.length() > 0.2:
		hud.channel.object = ""
		hud.player.channel_time = 0.0
		hud.player.channel_action = ""
		return
	hud.channel.t += delta
	hud.player.channel_time = hud.channel.t
	hud.player.channel_action = hud.channel.action
	if hud.channel.t >= hud.channel.dur:
		var obj: String = hud.channel.object
		hud.channel.object = ""
		if hud.channel.action == "gather" and not (hud.channel.get("tap", {}) as Dictionary).is_empty():
			var tp: Dictionary = hud.channel.tap
			hud.tapping = {"object": obj, "t": 0.0, "ring": float(tp.get("ring_s", 1.0)), "target": float(tp.get("target", 0.7)), "window": float(tp.get("window", 0.12))}
			return
		hud.player.channel_time = 0.0
		hud.player.channel_action = ""
		if hud.channel.action in ["gather", "mine"]:
			var r := Game.submit({"type": "complete_node", "object": obj})
			if r.ok: hud.add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(r.item)), int(r.count)], UiKit.BRIGHT_JADE)

func tick_tap(delta: float) -> void:
	if hud.tapping.object == "" or not hud.bound(): return
	hud.tapping.t += delta
	if hud.tapping.t >= float(hud.tapping.ring): finish_tap(1.0)

## The tap landed (or the ring ran out): `timing` is how far the ring had shrunk, 0..1.
func finish_tap(timing: float) -> void:
	var obj: String = hud.tapping.object
	hud.tapping.object = ""
	hud.player.channel_time = 0.0
	hud.player.channel_action = ""
	var r := Game.submit({"type": "complete_node", "object": obj, "timing": timing})
	if not r.ok:
		if r.has("text"): hud.add_log(str(r.text), UiKit.MIST)
		return
	hud.add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(r.item)), int(r.count)], UiKit.GOLD if r.get("perfect", false) else UiKit.BRIGHT_JADE)
	hud.pulses["tap:" + ("perfect" if r.get("perfect", false) else "miss")] = 0.6

## A tap on a points badge asks the shell for its system's page, on the tab where the points are spent.
func open_points(id: String) -> void:
	for row in Hud.POINT_SYSTEMS:
		if str(row.id) != id: continue
		hud.open_page.emit(str(row.page), {"tab": str(row.tab)} if str(row.tab) != "" else {})
		Audio.ui("ui_open")

func tap_cultivate() -> void:
	var c = Game.active()
	if c.cultivator.state == "bottleneck" and not c.cultivator.meditating:
		hud.open_page.emit("breakthrough", {})
		return
	hud.player.meditate()

## S50 node plate: beside a gathering node, the Chance a post there would have for its first output (cached).
func node_plate(c) -> String:
	if not str(hud.context.get("type", "")) in ["herb_patch", "ore_vein", "fishing_spot", "insect_swarm"] or not Unlocks.is_unlocked(c.id, "keeping_post"): return ""
	var key := "%s:%d" % [str(hud.context.get("object", "")), int(hud.t)]
	if key != hud._plate_key and Game.room_rt != null:
		hud._plate_key = key
		var r: Dictionary = Game.posts.rates_at(c, Game.room_rt.object_def(str(hud.context.get("object", ""))))
		var outs: Array = r.get("outputs", [])
		hud._plate_text = " · %d%%" % int(round(100.0 * float(outs[0].chance))) if not outs.is_empty() else " · —"
	return hud._plate_text

func keep_post() -> void:
	if not hud.bound(): return
	var r := Game.submit({"type": "take_post", "object": str(hud.context.get("object", ""))})
	if not r.get("ok", false):
		hud.add_log(str(r.get("text", Tx.t("hud.post_fail"))), UiKit.MIST)
		return
	hud.open_page.emit("posts", {})

## The pose of the place `object_id` of the room is (open, tend, sit), or "".
func place_pose_of(object_id: String) -> String:
	if Game.room_rt == null: return ""
	return str(PlaceRules.at_object(Game.room_rt.room_id, object_id).get("pose", ""))

func _play_place_pose(pose: String, page: String, args: Dictionary) -> void:
	hud.place_pending = {"page": page, "args": args, "t": Hud.PLACE_POSE_S}
	var at = hud.player.get("plane") if is_instance_valid(hud.player) else null
	if is_instance_valid(hud.player) and hud.player.has_method("play_place_pose"): hud.player.play_place_pose(pose)   # side view: no place poses
	var p: Vector2 = at if at is Vector2 else Vector2.ZERO
	# each id written out, so audio_tests finds it among the sounds
	match pose:
		"open": Audio.world_sound("place_open", p, 0.0)
		"tend": Audio.world_sound("place_tend", p, 0.0)
		"sit": Audio.world_sound("place_sit", p, 0.0)

func tick_place_pose(delta: float) -> void:
	if hud.place_pending.is_empty(): return
	hud.place_pending.t = float(hud.place_pending.t) - delta
	if float(hud.place_pending.t) <= 0.0: open_place_page()

## Open the page a place's pose is playing before (at once on a second tap); the pose holds while it is open, and ends
## now if no page came up.
func open_place_page() -> void:
	if hud.place_pending.is_empty(): return
	var p := hud.place_pending
	hud.place_pending = {}
	hud.open_page.emit(str(p.page), p.args)
	if not hud.blocked and is_instance_valid(hud.player) and hud.player.has_method("end_place_pose"): hud.player.end_place_pose()   # side view: no place poses

## The context's button: what the world offers in reach (talk, gather, open, enter, climb); while a harvest it began
## shrinks its ring round the button, the tap that lands it.
func use_context() -> void:
	if not hud.place_pending.is_empty():
		open_place_page()   # decision 44: a second tap skips the place's pose
		return
	if hud.tapping.object != "":
		finish_tap(float(hud.tapping.t) / maxf(0.01, float(hud.tapping.ring)))
		return
	if hud.channel.object != "": return
	if str(hud.context.get("type", "")) == "climbable":   # side view: only world.gd offers a ladder or a rope
		hud.side_view.climb()
		return
	if hud.context.has("portal"):
		hud.world.request_portal(str(hud.context.portal))
		return
	if str(hud.context.get("type", "")) == "mercy":
		hud.open_page.emit("mercy", {"enemy": int(hud.context.enemy), "def": str(hud.context.def)})
		return
	after_interact(Game.submit({"type": "interact", "object": str(hud.context.get("object", ""))}), str(hud.context.get("object", "")))

## S45: "Pick it" at a rare herb (from the Pick / Dig it up choice) starts the ordinary hold and tap.
func begin_harvest(object_id: String) -> void:
	if object_id == "" or not hud.bound(): return
	after_interact(Game.submit({"type": "interact", "object": object_id, "pick": true}), object_id)

func after_interact(r: Dictionary, object_id: String) -> void:
	if not r.ok:
		if r.has("text"): hud.add_log(str(r.text), UiKit.MIST)
		return
	if r.has("dialogue"):
		hud.dialogue_requested.emit(r.dialogue)
		return
	if r.has("open_page"):
		var pa := {"object": object_id}
		pa.merge(r.get("page_args", {}), true)
		var pose := place_pose_of(object_id)
		if pose != "":
			_play_place_pose(pose, str(r.open_page), pa)
			return
		hud.open_page.emit(str(r.open_page), pa)
		return
	if str(r.get("minigame", "")) == "fishing":
		hud.fishing_requested.emit(object_id)
		return
	if float(r.get("channel", 0.0)) > 0.0:
		hud.channel = {"object": object_id, "t": 0.0, "dur": float(r.channel), "action": str(r.get("action", "gather")), "tap": r.get("tap", {})}
		if r.get("early", false): hud.add_log(Tx.t("hud.herb_early"), UiKit.MIST)
		return
	if r.has("text") and str(r.text) != "": hud.add_log(str(r.text), UiKit.PAPER)

## S47 dual loadout: trade the weapon in hand for the spare; with no spare, the bag opens to choose one.
func swap_weapon() -> void:
	if not hud.bound(): return
	var r := Game.submit({"type": "swap_loadout"})
	if not r.ok:
		if r.get("reason", "") == "no_spare": hud.open_page.emit("inventory", {})
		elif r.has("text"): hud.add_log(str(r.text), UiKit.MIST)

func use_treasure(slot: int) -> void:
	if not hud.bound(): return
	var tid := str(Game.active().inventory.treasures[slot])
	if tid == "" or Game.active().inventory.count(tid) <= 0:
		hud.open_page.emit("inventory", {})   # an empty Treasure button opens the bag to choose one
		return
	var r := Game.submit({"type": "use_treasure", "slot": slot})
	if not r.ok:
		if r.get("reason", "") == "cooldown": hud.add_log(Tx.t("hud.not_ready_yet"), UiKit.MIST)
		elif r.has("text"): hud.add_log(str(r.text), UiKit.MIST)

func drink_draught() -> void:
	if not hud.bound(): return
	var r := Game.submit({"type": "drink_draught"})
	if not r.get("ok", false) and str(r.get("text", "")) != "": hud.add_log(str(r.text), UiKit.MIST)

## Decision 45: a tap on quick slot `slot` (0-2) uses what it holds; an empty one opens the Bag, where it is filled.
func use_quick(slot := 0) -> void:
	if not hud.bound(): return
	if str(Game.active().inventory.quick[slot]) == "":
		hud.open_page.emit("inventory", {})   # nothing in it yet: the Bag, where an item is put in Quick-use
		return
	var r := Game.submit({"type": "use_quick", "slot": slot})
	if not r.ok:
		if r.get("reason", "") == "none_left": hud.add_log(Tx.t("hud.no_left") % ContentDB.item_name(str(r.item)), UiKit.MIST)
		elif r.get("reason", "") == "cooldown": hud.add_log(Tx.t("hud.not_ready_yet"), UiKit.MIST)
		elif r.has("text"): hud.add_log(str(r.text), UiKit.MIST)

## S28 v1.2: raise or lower the Sphere (the reason shows in the log when it cannot be raised).
func toggle_sphere() -> void:
	var r := Game.submit({"type": "toggle_sphere"})
	if not r.get("ok", false): hud.add_log(str(r.get("text", Tx.t("hud.sphere_fail"))), UiKit.MIST)

## S28 v1.2: hold or release the Presence (the reason shows in the log when it cannot be held).
func toggle_presence() -> void:
	if not hud.bound(): return
	var r := Game.submit({"type": "toggle_presence"})
	if not r.get("ok", false): hud.add_log(Tx.t("hud.presence_fail_" + str(r.get("reason", "locked"))), UiKit.MIST)
