class_name WorldShared
extends RefCounted
## The room presentation both world views share (redesign Phase 4, one code path per concern): the side view
## (world.gd) and the top-down view (topdown/topdown_world.gd) play the game's events as the same effects, offer the
## same thing on the context button, place the names over the world the same way and ask for a way out the same way.
## Presentation only: it reads state and submits intents.
##
## A view hands itself in as `host`, which offers:
##   fx_layer()    the effects layer (FxLayer), in world units with y lifted by height (the side view's own space)
##   combat_fx     CombatFx round it
##   object_views  {object id: view} (a `position` in fx units, a `hit_flash` and a `focus`), npc_views,
##                 enemy_views {uid: view}, portal_views [view]
##   feet()        the player's feet in fx units;  facing()  +1 or -1
##   add_shake(s)  the camera rig's one writer;  loot_parent()  where a LootView goes
##   transfer_cooldown  seconds before another way may be asked for

## An event's effects and sounds, as both views play them. False for an event this does not handle (a view's own:
## building a room, a figure's pose, a cast's form).
static func play(host, name: String, p: Dictionary) -> bool:
	var fx: FxLayer = host.fx_layer()
	var me: Vector2 = host.feet()
	match name:
		"enemy_aggro":
			var foe: EnemyState = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
			if foe and not foe.hidden: fx.label(Vector2(foe.plane.x, foe.plane.y - foe.altitude - foe.height() - 24), "!", UiKit.GOLD, 26)
		"loot_dropped":
			for l in p.get("items", []):
				var lv = LootView.new()
				lv.setup(l)
				host.loot_parent().add_child(lv)
		"art_used":
			if str(p.get("actor", "")) == Game.active_id:
				match str(p.get("art", "")):
					"air_dash": Audio.play("dodge")
					"glide": fx.add("dust", me + Vector2(0, -40), {"color": Color(UiKit.BRIGHT_JADE, 0.5), "dur": 0.3})
					"water_skimming": Audio.play("water_step")
					"bounce": Audio.play("land")
		"volume_entered":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("kind", "")) in ["water_deep", "rising_water"]: Audio.play("water_step")
		"wall_kicked":
			if str(p.get("actor", "")) == Game.active_id:
				fx.add("spark", me + Vector2(-int(p.get("side", 1)) * -14, -50), {"color": UiKit.PAPER, "dur": 0.25})
		"fell_out":
			if str(p.get("actor", "")) == Game.active_id:
				fx.add("text", me + Vector2(0, -130), {"text": Tx.t("hud.fell"), "color": UiKit.MIST, "size": 18, "dur": 1.4})
		"hit_landed":
			host.combat_fx.hit(p)   # P6e: its number and spark at its tier (FxLayer.hit), the shakes and the sound (CombatFx)
		"hazard_warned":
			var sfx := {"falling_rocks": "rumble", "lightning": "charge", "poison_mist": "hiss"}
			Audio.play(str(sfx.get(str(p.hazard), "tell")))
		"hazard_struck":
			if str(p.get("actor", "")) == Game.active_id:
				var hname := ContentDB.name_of("hazards", str(p.hazard))
				var over := me + Vector2(0, -130)
				if p.get("answered", false): fx.label(over, Tx.t("world_view.hazard_answered") % hname, UiKit.BRIGHT_JADE, 17)
				elif int(p.get("amount", 0)) == 0: fx.label(over, hname, UiKit.PALE_GOLD, 17)
		"hit_missed", "hit_immune", "hit_dodged": host.combat_fx.word(name, p, me)
		"parried":
			fx.parry(me, host.facing())
			Audio.play("parry")
		"actor_defeated":
			fx.add("dust", Vector2(float(p.x), float(p.y)), {"dur": 0.5})
		"object_hit":
			if host.object_views.has(str(p.object)): host.object_views[str(p.object)].hit_flash = 0.15
			fx.add("spark", Vector2(float(p.x), float(p.y) - 30), {"color": UiKit.PALE_GOLD, "dur": 0.2})
			Audio.play("hit")
		"object_broken":
			var ov = host.object_views.get(str(p.object))
			if ov: fx.add("dust", ov.position, {"dur": 0.5})
			Audio.play("break")
		# S47: a spare artifact detonated, and the flying sword leaving and returning.
		"artifact_detonated":
			fx.add("wave", me, {"color": Color("ff9a5a"), "radius": float(ContentDB.stat_const("detonation.radius", 180)), "dur": 0.5})
			fx.add("flash", me + Vector2(0, -50), {"color": Color("ffe0a0"), "radius": 90.0, "dur": 0.35})
			host.add_shake(0.35)
			Audio.play("rumble")
		"talisman_used":
			# S47: the paper flares and burns away; attack talismans burst where they land.
			var tat := Vector2(float(p.get("x", me.x)), float(p.get("y", me.y)) - float(p.get("alt", 0.0)) - 40.0)
			match str(p.get("kind", "")):
				"attack":
					fx.add("wave", tat, {"color": Color("ff8a4a") if str(p.get("item", "")) == "flame_talisman" else Color("9fd8ff"), "radius": 90.0, "dur": 0.45})
					fx.add("flash", tat, {"color": Color("fff0c0"), "radius": 50.0, "dur": 0.3})
				"defence": fx.add("wave", me + Vector2(0, -50), {"color": Color("c8ccd0"), "radius": 46.0, "dur": 0.6})
				_: fx.add("spark", me + Vector2(0, -70), {"color": Color("e8d99a"), "dur": 0.4})
			Audio.play("technique")
		"item_blooded":
			# S47 blood-drop bind: a bead of blood falls onto a piece worn for the first time.
			fx.add("spark", me + Vector2(0, -70), {"color": Color("c0303a"), "dur": 0.5})
			fx.add("text", me + Vector2(0, -120), {"text": "·", "color": Color("d23a44"), "size": 34, "dur": 0.9})
		"natal_broken":
			fx.add("flash", me + Vector2(0, -50), {"color": Color("ff6a5a"), "radius": 70.0, "dur": 0.4})
			host.add_shake(0.3)
			Audio.play("break")
		"array_deployed":
			var ac: Color = FxLayer.ARRAY_COLOURS.get(str(p.get("kind", "")), FxLayer.ARRAY_COLOURS.guard)
			fx.add("wave", Vector2(float(p.x), float(p.y)), {"color": ac, "radius": float(p.radius), "dur": 0.5})
			Audio.play("forge")
		"artifact_skill_used":
			if str(p.get("actor", "")) == Game.active_id:
				var ring := float(p.get("ring", 0.0))
				fx.add("wave", Vector2(float(p.x), float(p.y)), {"color": Color("ffd27a") if p.get("awakened", false) else Color("b18de2"),
					"radius": ring if ring > 0.0 else 60.0, "dur": 0.4 if ring > 0.0 else 0.3})
				Audio.play("surge")
		"array_faded":
			if str(p.get("actor", "")) == Game.active_id: Audio.play("ui_close")
		"melody_pulse":
			# S47 v1.1 flute: the melody spreads as a jade ring, notes drifting up from the player.
			fx.add("ring", Vector2(float(p.x), float(p.y)), {"color": Color(0.56, 0.91, 0.81, 0.8), "radius": float(p.radius), "dur": 0.55})
			for i in 2:
				fx.add("note", me + Vector2(randf_range(-26, 26), -96 - i * 14), {"color": Color("8fe8cf") if i == 0 else UiKit.PALE_GOLD,
					"vel": Vector2(randf_range(-10, 10), -46.0), "dur": 1.2, "size": 18 + i * 4, "radius": randf() * 6.0})
		"melody_changed":
			if str(p.get("actor", "")) == Game.active_id and p.get("on", false):
				fx.add("wave", me, {"color": Color("8fe8cf"), "radius": 70.0, "dur": 0.5})
				Audio.play("meditate")
		"sword_released", "sword_returned":
			fx.add("spark", me + Vector2(0, -100), {"color": Color("dff3ff"), "dur": 0.3})
			Audio.play("forge")
		"treasure_used": _treasure(host, p, me)
		"wisp_struck":
			fx.add("spark", Vector2(float(p.x), float(p.y) - float(p.alt)), {"color": UiKit.QI, "dur": 0.25})
		"projectile_reflected", "projectile_absorbed":
			fx.add("spark", Vector2(float(p.x), float(p.y) - float(p.alt)), {"color": Color("bfe8ff") if name == "projectile_reflected" else UiKit.SOUL, "dur": 0.3})
		"projectile_burst":
			fx.add("wave", Vector2(float(p.x), float(p.y)), {"color": Color("ffd76a"), "radius": float(p.radius), "dur": 0.4})
			fx.add("flash", Vector2(float(p.x), float(p.y) - 30.0), {"color": Color("fff0b0"), "radius": 50.0, "dur": 0.25})
			host.add_shake(0.15)
			Audio.play("break")
		"meditation_tick":
			if Game.active() and Game.active().pools.max_qi > 0:
				fx.add("motes", me + Vector2(0, -10), {"color": UiKit.QI if not p.get("spring", false) else UiKit.BRIGHT_JADE, "dur": 1.0})
			elif Game.active():
				fx.add("motes", me + Vector2(0, -10), {"color": Color("f4ecd5"), "dur": 1.0})
		"item_used":
			# A tea, a pill, a draught, a food: what it did rises over the player (the heal it gives, the Qi, the buff),
			# with motes in its colour; a heal at full HP says "HP already full" rather than nothing.
			if str(p.get("actor", "")) == Game.active_id:
				var parts := UiKit.use_parts(p.get("effects", []), p.get("gains", {}))
				var k := 0
				for part in parts:
					if k >= 3: break
					fx.label(me + Vector2(0, -130 - 24 * k), str(part.get("float", part.text)), part.color, 26 if part.has("float") and k == 0 else 18)
					k += 1
				if not parts.is_empty(): fx.add("motes", me + Vector2(0, -10), {"color": parts[0].color, "dur": 1.0})
		"player_revived":
			fx.add("flash", me + Vector2(0, -40), {"color": UiKit.BRIGHT_JADE, "radius": 60, "dur": 0.6})
		"projectile_ended":
			fx.add("spark", Vector2(float(p.x), float(p.y) - float(p.alt)), {"color": UiKit.PAPER, "dur": 0.15})
		"dodged":
			fx.add("dust", me, {"dur": 0.35})
			Audio.play("dodge")
		"node_gathered":
			var ov2 = host.object_views.get(str(p.object))
			if ov2: fx.add("motes", ov2.position, {"color": UiKit.BRIGHT_JADE, "dur": 0.8})
			Audio.play("pickup")
		"loot_picked":
			Audio.play("coin" if int(p.get("coins", 0)) > 0 else "pickup")
		"emote_played":
			var em: Dictionary = ContentDB.entry("emotes", str(p.emote))
			fx.add("text", me + Vector2(0, -150), {"text": str(em.get("text", "...")), "color": UiKit.PAPER, "size": 20, "dur": float(em.get("seconds", 1.8))})
		_:
			return false
	return true

static func _treasure(host, p: Dictionary, me: Vector2) -> void:
	var fx: FxLayer = host.fx_layer()
	var at := Vector2(float(p.x), float(p.y))
	var tr_radius := float(CombatAuthority.treasure_of(str(p.treasure)).get("radius", 150))
	match str(p.action):
		"bell":
			fx.add("wave", me, {"color": UiKit.PALE_GOLD, "radius": tr_radius, "dur": 0.6})
			fx.add("wave", me, {"color": UiKit.GOLD, "radius": tr_radius * 0.7, "dur": 0.45})
			Audio.play("bell")
		"pagoda":
			fx.add("pagoda", at, {"color": UiKit.BRIGHT_JADE, "dur": 4.0})
			Audio.play("forge")
		"mirror":
			fx.add("flash", me + Vector2(0, -50), {"color": Color("bfe8ff"), "radius": 60.0, "dur": 0.4})
		"seal":
			fx.add("seal_slam", me, {"color": UiKit.BRIGHT_JADE, "radius": tr_radius, "dur": 0.7})
			host.add_shake(0.25)
			Audio.play("break")
		"cauldron":
			fx.add("spiral", at + Vector2(0, -30), {"color": UiKit.QI, "dur": 1.0})
			Audio.play("technique")
		"banner", "gourd":
			fx.add("ring", me, {"color": UiKit.QI if str(p.action) == "banner" else UiKit.SOUL, "radius": 110.0, "dur": 0.8})
			Audio.play("technique")
		"palm":
			fx.add("talisman_wave", me + Vector2(0, -50), {"color": UiKit.PALE_GOLD, "radius": float(p.get("reach", 540)), "facing": int(p.get("facing", 1)), "dur": 0.6})
			host.add_shake(0.3)
			Audio.play("breakthrough")

# ------------------------------------------------------------------ the context button
## What the context button offers where the player stands (the World authority's pick), else `climb` (a ladder in reach,
## the side view's), else a foe who has yielded to the player and waits for judgement (S49).
static func context(c, plane: Vector2, climb: Dictionary = {}) -> Dictionary:
	var ctx: Dictionary = Game.world.query_context(c) if c else {}
	if ctx.is_empty() and not climb.is_empty(): ctx = climb
	if ctx.is_empty() and c and Game.room_rt:
		for e in Game.room_rt.living_enemies():
			if e.ai.get("surrendered", false) and str(e.ai.get("judge", "")) == Game.active_id and e.plane.distance_to(plane) < 160.0:
				ctx = {"type": "mercy", "enemy": e.uid, "def": e.def_id, "label": Tx.t("hud.judge")}
				break
	return ctx

## The offer's target shows it (its plate), and a person offered turns to the player.
static func mark_focus(ctx: Dictionary, object_views: Dictionary, npc_views: Dictionary, face_x: float) -> void:
	var target := str(ctx.get("object", ""))
	for id in object_views: object_views[id].focus = target == id
	for id in npc_views:
		npc_views[id].focus = target == id
		if target == id: npc_views[id].face(face_x)

# ------------------------------------------------------------------ names over the world
## Every name over the room's figures, ways and things, nearest the player first (WorldLabels.place_views places them).
## `at` is the player on the labels' plane and `axes` weighs its axes: the side view measures across (Vector2(1, 0)),
## the top-down view on the whole plane (Vector2.ONE), so the names nearest the player keep their rows.
static func label_views(host, at: Vector2, axes := Vector2(1, 0)) -> Array:
	var near := func(v: Node2D) -> float: return ((v.position - at) * axes).length()
	var views: Array = []
	for uid in host.enemy_views:
		var v = host.enemy_views[uid]
		if is_instance_valid(v): views.append({"id": "e%d" % int(uid), "view": v, "kind": v.label_kind, "near": near.call(v)})
	for id in host.npc_views:
		var nv = host.npc_views[id]
		if is_instance_valid(nv): views.append({"id": "n" + str(id), "view": nv, "kind": "focus" if nv.focus else "npc", "near": near.call(nv)})
	for i in host.portal_views.size():
		if is_instance_valid(host.portal_views[i]): views.append({"id": "p%d" % i, "view": host.portal_views[i], "kind": "place", "near": near.call(host.portal_views[i])})
	for id in host.object_views:
		if is_instance_valid(host.object_views[id]): views.append({"id": "o" + str(id), "view": host.object_views[id], "kind": "place", "near": near.call(host.object_views[id])})
	return views

# ------------------------------------------------------------------ ways out
## Ask the World authority for a way out (walked through, or taken with the context button); a refusal (a shut door, a
## step first) rises over the player.
static func request_portal(host, portal_id: String, crossing := false) -> void:
	if host.transfer_cooldown > 0.0: return
	host.transfer_cooldown = 0.6
	var r := Game.submit({"type": "use_portal", "portal": portal_id, "crossing": crossing})
	if not r.ok and r.has("text"):
		host.fx_layer().add("text", host.feet() + Vector2(0, -130), {"text": str(r.text), "color": UiKit.MIST, "size": 18, "dur": 1.6})
