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

## What the views ask of the game every frame, for each thing, person and way of the room (its view, its plate or gate
## and the HUD's minimap and tracker): whether it shows (WorldAuthority.object_visible), a person's quest marker
## (QuestAuthority.npc_marker), a way's state, the quest tracker and the quest direction's step. Each answer is kept for
## the frame and asked again as soon as the game moves on (Game.revision: an intent, a tick, effects) or another room
## or character is asked about. The views asked the authorities for all of them several times a frame (the
## requirements' texts, a look through every foe, every quest): over a millisecond of the Marsh Edge fight's frame.
static var _memo := FrameMemo.new()
static func _frame_memo(c) -> Dictionary:
	return _memo.table(Game.room_rt.get_instance_id() if Game.room_rt != null else 0, c.get_instance_id() if c is Object else 0)

static func object_visible(c, o: Dictionary) -> bool:
	var id := str(o.get("id", ""))
	if id == "": return Game.world.object_visible(c, o)
	var m := _frame_memo(c)
	var k := "v:" + id
	if not m.has(k): m[k] = Game.world.object_visible(c, o)
	return m[k]

static func npc_marker(c, npc: String) -> String:
	if c == null: return ""
	var m := _frame_memo(c)
	var k := "m:" + npc
	if not m.has(k): m[k] = Game.quest.npc_marker(c, npc)
	return m[k]

## A way's state (WorldAuthority.portal_state), asked by its plate, its gate, its mark and the minimap: shared, so read
## only.
static func portal_state(c, p: Dictionary) -> Dictionary:
	var id := str(p.get("id", ""))
	if id == "" or c == null: return Game.world.portal_state(c, p)
	var m := _frame_memo(c)
	var k := "p:" + id
	if not m.has(k): m[k] = Game.world.portal_state(c, p)
	return m[k]

## The quest tracker's entries (QuestAuthority.tracker), for the HUD's plate: shared, so read only.
static func quest_tracker(c) -> Array:
	if c == null: return []
	var m := _frame_memo(c)
	if not m.has("t"): m["t"] = Game.quest.tracker(c)
	return m["t"]

## The quest direction's next step from this room (WorldAuthority.guide_step), for the minimap's mark.
static func guide_step(c) -> Dictionary:
	if c == null: return {}
	var m := _frame_memo(c)
	if not m.has("g"): m["g"] = Game.world.guide_step(c)
	return m["g"]

## An event's effects and sounds, as both views play them: the first of its rows in the cue table (data/cues.json, `to`
## "world"; Cues) whose `when` holds, its steps in order. False for an event the table does not answer (a view's own:
## building a room, a figure's pose, a cast's form).
static func play(host, name: String, p: Dictionary) -> bool:
	if Cues.rows("world", name).is_empty(): return false
	var row := Cues.pick("world", name, p)
	if not row.is_empty(): _steps(host, name, row.do, p)
	return true

## Where a row's effect plays (its `at`, moved by its `off`): the player's feet; the payload's point on the ground
## (x, y) or in the air (x, y - alt), the feet's when it has none; the view of the payload's thing; over the head of the
## payload's foe. No thing's view, or a hidden foe, skips the effect.
const ANCHORS := ["feet", "ground", "point", "object", "foe"]
## The answers a row hands to code (`call`): a blow's hit and its words (CombatFx), a drop's views, what a use did, the
## melody's scattered notes.
const HANDLERS := ["combat_hit", "combat_word", "loot_views", "use_parts", "melody_notes"]
## FxLayer's own effects a step may name besides its kinds (FxLayer.KINDS): a rising word, and the parry.
const FX_CALLS := ["label", "parry"]
const _PLACE := ["fx", "at", "off", "flip"]
const _NO_OFF := [0.0, 0.0]

## A row's steps in order: an effect, a sound of the bank (Audio.play), a shake, the payload thing's hit flash, a handler.
static func _steps(host, name: String, steps: Array, p: Dictionary) -> void:
	var fx: FxLayer = host.fx_layer()
	var me: Vector2 = host.feet()
	for s in steps:
		if s.has("fx"):
			var at = _at(host, s, p, me)
			if at == null: continue
			match str(s.fx):
				"label": fx.label(at, Cues.text(s.get("text", ""), p), Cues.color(s.get("color", "PAPER"), p), int(s.get("size", 22)))
				"parry": fx.parry(at, host.facing())
				var kind: fx.add(kind, at, _params(s, p))
		elif s.has("sound"): Audio.play(str(s.sound))
		elif s.has("shake"): host.add_shake(float(s.shake))
		elif s.has("hit_flash"):
			var ov = host.object_views.get(str(p.get("object", "")))
			if ov: ov.hit_flash = float(s.hit_flash)
		elif s.has("call"): _handle(str(s.call), host, name, p, me)

## The step's point (ANCHORS), worked in whole floats and made a vector once, as the arms it replaced wrote it.
static func _at(host, s: Dictionary, p: Dictionary, me: Vector2):
	var x := me.x
	var y := me.y
	match str(s.get("at", "feet")):
		"feet": pass
		"ground", "point":
			x = float(p.get("x", me.x))
			y = float(p.get("y", me.y)) - (float(p.get("alt", 0.0)) if str(s.at) == "point" else 0.0)
		"object":
			var ov = host.object_views.get(str(p.get("object", "")))
			if not ov: return null
			x = ov.position.x
			y = ov.position.y
		"foe":
			var foe: EnemyState = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
			if foe == null or foe.hidden: return null
			x = foe.plane.x
			y = foe.plane.y - foe.altitude - foe.height()
		_: return null
	var off: Array = s.get("off", _NO_OFF)
	var dx := float(off[0]) * (int(p.get("side", 1)) if str(s.get("flip", "")) == "side" else 1)
	return Vector2(x + dx, y + float(off[1]))

## The step's parameters as FxLayer.add takes them: its colour and text resolved, the rest values (Cues.value).
static func _params(s: Dictionary, p: Dictionary) -> Dictionary:
	var out := {}
	for k in s:
		if k in _PLACE: continue
		match str(k):
			"color": out[k] = Cues.color(s[k], p)
			"text": out[k] = Cues.text(s[k], p)
			_: out[k] = Cues.value(s[k], p)
	return out

## The answers that are code (HANDLERS).
static func _handle(handler: String, host, name: String, p: Dictionary, me: Vector2) -> void:
	var fx: FxLayer = host.fx_layer()
	match handler:
		"combat_hit": host.combat_fx.hit(p)   # P6e: its number and spark at its tier (FxLayer.hit), the shakes and the sound (CombatFx)
		"combat_word": host.combat_fx.word(name, p, me)
		"loot_views":
			for l in p.get("items", []):
				var lv = LootView.new()
				lv.setup(l)
				host.loot_parent().add_child(lv)
		"use_parts":
			# A tea, a pill, a draught, a food: what it did rises over the player (the heal it gives, the Qi, the buff),
			# with motes in its colour; a heal at full HP says "HP already full" rather than nothing.
			var parts := UiKit.use_parts(p.get("effects", []), p.get("gains", {}))
			var k := 0
			for part in parts:
				if k >= 3: break
				fx.label(me + Vector2(0, -130 - 24 * k), str(part.get("float", part.text)), part.color, 26 if part.has("float") and k == 0 else 18)
				k += 1
			if not parts.is_empty(): fx.add("motes", me + Vector2(0, -10), {"color": parts[0].color, "dur": 1.0})
		"melody_notes":
			# S47 v1.1 flute: notes drifting up from the player, each its own way.
			for i in 2:
				fx.add("note", me + Vector2(randf_range(-26, 26), -96 - i * 14), {"color": Color("8fe8cf") if i == 0 else UiKit.PALE_GOLD,
					"vel": Vector2(randf_range(-10, 10), -46.0), "dur": 1.2, "size": 18 + i * 4, "radius": randf() * 6.0})

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
	var views: Array = []
	for uid in host.enemy_views:
		var v = host.enemy_views[uid]
		if is_instance_valid(v): views.append({"id": "e%d" % int(uid), "view": v, "kind": v.label_kind, "near": ((v.position - at) * axes).length()})
	for id in host.npc_views:
		var nv = host.npc_views[id]
		if is_instance_valid(nv): views.append({"id": "n" + str(id), "view": nv, "kind": "focus" if nv.focus else "npc", "near": ((nv.position - at) * axes).length()})
	for i in host.portal_views.size():
		var pv = host.portal_views[i]
		if is_instance_valid(pv): views.append({"id": "p%d" % i, "view": pv, "kind": "place", "near": ((pv.position - at) * axes).length()})
	for id in host.object_views:
		var ov = host.object_views[id]
		if is_instance_valid(ov): views.append({"id": "o" + str(id), "view": ov, "kind": "place", "near": ((ov.position - at) * axes).length()})
	return views

# ------------------------------------------------------------------ ways out
## Ask the World authority for a way out (walked through, or taken with the context button). A refusal (a shut door,
## a step first, the prototype's gate) is said once, by the way's own plate lit up at the way (PortalView.touch); only a
## way with no plate of its own has its line rise over the player instead.
static func request_portal(host, portal_id: String, crossing := false) -> void:
	if host.transfer_cooldown > 0.0: return
	host.transfer_cooldown = 0.6
	var r := Game.submit({"type": "use_portal", "portal": portal_id, "crossing": crossing})
	if not r.ok and r.has("text"):
		if touch_way(host, portal_id): return
		host.fx_layer().add("text", host.feet() + Vector2(0, -130), {"text": str(r.text), "color": UiKit.MIST, "size": 18, "dur": 1.6})

## Light the plate of the host's way `portal_id` (its refusal); false when the host has no plate for it.
static func touch_way(host, portal_id: String) -> bool:
	for pv in host.portal_views:
		if not is_instance_valid(pv) or str(pv.def.get("id", "")) != portal_id or Game.active() == null: continue
		pv.state = Game.world.portal_state(Game.active(), pv.def)
		if str(pv.state.get("text", "")) == "": return false
		pv.touch()
		return true
	return false
