class_name ObjectView
extends Node2D
## A world object (Part 9.9 state sets): shrine, nodes, breakables, chests,
## stations, boards, stones, fishing ripples, quest pickups. Reads RoomRuntime
## object state; shows a verb prompt when it is the context target.

const DEFAULT_PROP := {"shrine": "shrine", "qi_spring": "qi_spring", "bath_station": "bath_tub", "training_stump": "training_stump", "lifting_stone": "lifting_stone",
	"training_dummy": "training_dummy", "jar": "jar", "crate": "crate", "wine_jar": "wine_jar", "chest": "chest", "storage_chest": "storage_chest",
	"notice_board": "notice_board", "signpost": "signpost", "teleport_stone": "teleport_stone", "insight_stone": "insight_stone",
	"cooking_pot": "cooking_pot", "alchemy_furnace": "alchemy_furnace", "forge_anvil": "forge_anvil", "fishing_spot": "fishing_ripple",
	"rite_circle": "rite_circle", "bell": "small_bell", "spar_post": "weapon_rack", "inspect": "grey_patch", "herb_patch": "willow_moss_patch",
	"ore_vein": "copper_vein", "formation_table": "formation_node", "garden_bed": "treasure_plot",
	"defence_drum": "small_bell", "treasure_plot": "treasure_plot", "treasure_tree": "nine_bough_jade_tree",
	"star_sight": "star_sight_stone", "chart_table": "star_chart_table", "shipyard_slip": "shipyard_slip", "starsea_dock": "cloud_skiff",
	"air_pocket": "qi_spring", "earth_vent": "gas_vent", "egg_nest": "beast_nest", "beast_tide_drum": "small_bell", "beast_trial_stone": "rite_circle",
	"rift_tear": "portal_swirl", "spirit_mine": "spirit_shard_vein", "insect_swarm": "glowfly_swarm"}
## V10 Insect Netting: the colour of each swarm's drifting motes.
const SWARM_MOTE := {"glowfly": "d8f06a", "reed_cicada": "b8c47a", "jade_scarab": "6fd8a0", "silk_moth": "f2ead0",
	"thunder_mantis": "9aa8ff", "frost_cricket": "c8f0ff", "ember_locust": "ff9a4a", "starwing_mote": "ffe08a"}

var def: Dictionary = {}
var object_id := ""
var t := 0.0
var focus := false
var hit_flash := 0.0
var prop_id := ""
var badge: Node2D   # a pickup's floating item icon, smoothed (icons are 64 px art drawn smaller)

func setup(o: Dictionary) -> void:
	def = o
	object_id = str(o.id)
	prop_id = str(o.get("prop", DEFAULT_PROP.get(str(o.type), "")))
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var at: Array = o.get("at", [0, 0])
	position = Vector2(float(at[0]), float(at[1]) - float(o.get("alt", 0)))
	var decal := bool(SpriteCache.prop(prop_id).get("decal", false)) or str(o.type) in ["fishing_spot", "rite_circle", "inspect"]
	z_index = (1500 + int(float(at[1])) - 60) if decal else (1500 + int(float(at[1])))
	if o.get("z_back", false): z_index = -1500
	if str(o.type) == "pickup":
		badge = Node2D.new()
		badge.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		badge.z_index = 1
		badge.draw.connect(_draw_badge)
		add_child(badge)

func state_name() -> String:
	var rt: RoomRuntime = Game.room_rt
	var st: Dictionary = rt.objects.get(object_id, {}) if rt else {}
	var s := str(st.get("state", "ready"))
	var c = Game.active()
	match str(def.type):
		"herb_patch":
			# S45: a rare herb out of season lies bare, like a picked patch.
			if s == "depleted" or (def.has("season") and not HerbRules.in_season(def, Clock.now_utc())): return "depleted"
			return "ready"
		"star_sight": return "idle" if s == "depleted" else "active"   # the engraved stars glow while a reading waits
		"insect_swarm": return "depleted" if s == "depleted" else "ready"
		"spirit_mine": return "full"
		"ore_vein": return "depleted" if s == "depleted" else ("cracked" if int(st.get("hits", 0)) > 0 else "full")
		"jar", "crate", "wine_jar": return "broken" if s == "broken" else "intact"
		"chest": return "open" if s == "open" else "closed"
		"shrine": return "active" if c and str(c.last_shrine.get("object", "")) == object_id and str(c.last_shrine.get("room", "")) == rt.room_id else "idle"
		"qi_spring": return "active" if c and Unlocks.is_unlocked(c.id, "qi_springs") else "dormant"
		"air_pocket": return "active"
		"teleport_stone": return "active" if Game.account.teleports.has(str(def.get("stone", object_id))) else "inactive"
		"insight_stone": return "glow" if c and c.cultivator.meditating else "idle"
		"cooking_pot": return "steam"
		"alchemy_furnace": return "lit"
		"forge_anvil": return "sparks"
		"training_stump", "training_dummy": return "hit" if hit_flash > 0.0 else "idle"
		"bell": return "ringing" if s == "open" else "idle"
		"rite_circle": return "active" if Game.room_rt and Game.room_rt.event.get("active", false) else "idle"
		"treasure_plot": return "fruit" if c and _my_tree(c) and bool(Game.crafting.evergreen_state(c).get("ready", false)) else "idle"
		"inspect":
			# A door or gate drawn from a flag (the Tomb of Sunscar's gate: sealed, then open).
			var sf: Dictionary = def.get("state_flag", {})
			if not sf.is_empty(): return str(sf.on) if c and c.quests.has_flag(str(sf.flag)) else str(sf.off)
	return "idle"

## Rich earth shows the player's Evergreen Heart Tree once it is planted here.
func _my_tree(c) -> bool:
	var st: Dictionary = Game.crafting.evergreen_state(c)
	return bool(st.get("planted", false)) and str(st.get("object", "")) == object_id and Game.room_rt != null and str(st.get("room", "")) == Game.room_rt.room_id

func current_prop() -> String:
	var c = Game.active()
	if str(def.get("type", "")) == "treasure_plot" and c and _my_tree(c): return "evergreen_heart_tree"
	return prop_id

func _process(delta: float) -> void:
	t += delta
	hit_flash = maxf(0.0, hit_flash - delta)
	var c = Game.active()
	visible = c == null or Game.world.object_visible(c, def)
	if def.type == "pickup" and Game.room_rt and Game.room_rt.objects.get(object_id, {}).get("state", "") == "open": visible = false
	queue_redraw()
	if badge: badge.queue_redraw()

func _draw() -> void:
	var st := state_name()
	var drawn := false
	if def.type == "pickup":
		# A warm pool of light on the ground under anything to take; the prop (if any) stands in it.
		var pulse := 0.5 + 0.5 * sin(t * 3.0)
		draw_set_transform(Vector2(0, -2), 0.0, Vector2(1.0, 0.34))
		draw_circle(Vector2.ZERO, 34.0 + 5.0 * pulse, Color(1.0, 0.84, 0.42, 0.14 + 0.08 * pulse))
		draw_circle(Vector2.ZERO, 20.0, Color(1.0, 0.9, 0.6, 0.20))
		draw_set_transform(Vector2.ZERO)
		drawn = true
		if prop_id != "" and prop_id != "none":
			SpriteCache.draw_prop(self, current_prop(), st, t, Vector2.ZERO, bool(def.get("flip", false)))
	elif prop_id != "":
		var rare: bool = def.type == "herb_patch" and def.has("ripen")
		var hs: Dictionary = Game.world.herb_state(def) if rare else {}
		var ripe: bool = rare and hs.ripe and not hs.dormant and st == "ready"
		if ripe:
			# A ripe rare herb shimmers gold (S45).
			draw_circle(Vector2(0, -14), 34.0 + 3.0 * sin(t * 3.0), Color(1.0, 0.82, 0.35, 0.14))
			draw_circle(Vector2(0, -14), 22.0 + 2.0 * sin(t * 3.0), Color(1.0, 0.86, 0.45, 0.22))
			for i in 6:
				var a := t * 1.6 + i * TAU / 6.0
				var sp := Vector2(cos(a) * 24.0, -18.0 + sin(a * 1.3) * 14.0)
				draw_circle(sp, 2.4, Color(1.0, 0.95, 0.7, 0.95))
				draw_line(sp - Vector2(4, 0), sp + Vector2(4, 0), Color(1.0, 0.9, 0.55, 0.7), 1.0)
				draw_line(sp - Vector2(0, 4), sp + Vector2(0, 4), Color(1.0, 0.9, 0.55, 0.7), 1.0)
		if def.type == "treasure_birth":
			# S49: a Spirit Fruit ripe on the tree, pale jade and gold, breathing light.
			var fp := Vector2(18, -120)
			draw_circle(fp, 26.0 + 3.0 * sin(t * 2.4), Color(0.6, 1.0, 0.8, 0.16))
			draw_circle(fp, 9.0, Color("9fe8c8"))
			draw_circle(fp + Vector2(3, 2), 5.0, Color("f2c85a"))
		if def.type == "rift_tear":
			# S49 spatial rift: a violet tear in the air, the swirl inside it, motes drawn in.
			for k in 3:
				draw_circle(Vector2(0, -60), 70.0 - k * 18.0 + 4.0 * sin(t * 2.0 + k), Color(0.55, 0.25, 0.85, 0.10 + k * 0.06))
			for i in 8:
				var a := -t * 1.2 + i * TAU / 8.0
				var r := 60.0 - fmod(t * 30.0 + i * 9.0, 50.0)
				draw_circle(Vector2(cos(a) * r, -60.0 + sin(a) * r * 0.7), 2.2, Color(0.85, 0.7, 1.0, 0.9))
		drawn = SpriteCache.draw_prop(self, current_prop(), st, t, Vector2.ZERO, bool(def.get("flip", false)))
		if rare and not ripe and st == "ready": draw_circle(Vector2(0, -14), 22.0, Color(0.05, 0.1, 0.1, 0.25))   # still growing
	if def.type == "herb_patch" and def.has("ripen"): _draw_sensed()
	if def.type == "insect_swarm" and st == "ready": _draw_swarm()
	_draw_post_flag()
	if not drawn and def.type != "pickup":
		draw_rect(Rect2(-12, -24, 24, 24), UiKit.BRONZE)
	if def.type == "earth_vent": _draw_earth_fire()
	if def.type == "spirit_mine": _draw_mine()
	if def.type == "garden_bed": _draw_bed_herb()
	if focus and def.type != "pickup":
		var c = Game.active()
		var avail: Dictionary = Game.world.object_available(c, def) if c else {"ok": true}
		var label := Game.world._verb(def)
		var h := SpriteCache.prop_size(current_prop()).y if prop_id != "" else 40.0
		UiKit.draw_nameplate(self, label if avail.ok else str(avail.get("text", "")), "", -h - 12,
			UiKit.PALE_GOLD if avail.ok else UiKit.MIST, UiKit.MIST, 18)

## Height of a pickup's prop, so its icon floats clear of it.
func _pickup_top() -> float:
	if prop_id == "" or prop_id == "none": return 0.0
	return SpriteCache.prop_size(current_prop()).y - 8.0

## A pickup's item icon bobbing in a gold ring over the spot, a few glints turning round it, and its name
## (with the verb when it is the context target) on a plate above: readable from across the room.
func _draw_badge() -> void:
	var pulse := 0.5 + 0.5 * sin(t * 3.0)
	var c := Vector2(0, -_pickup_top() - 34.0 + sin(t * 3.0) * 4.0)
	badge.draw_circle(c, 29.0 + 3.0 * pulse, Color(1.0, 0.84, 0.42, 0.16 + 0.10 * pulse))
	badge.draw_circle(c, 23.0, Color(0.03, 0.08, 0.09, 0.72))
	badge.draw_arc(c, 23.0, 0.0, TAU, 40, Color(UiKit.PALE_GOLD, 0.65 + 0.35 * pulse), 2.5, true)
	var ic := SpriteCache.icon(str(def.get("item", "")))
	if ic: badge.draw_texture_rect(ic, Rect2(c - Vector2(19, 19), Vector2(38, 38)), false)
	for i in 3:
		var a := t * 1.8 + i * TAU / 3.0
		var sp := c + Vector2(cos(a) * 32.0, sin(a) * 32.0 * 0.8)
		var r := 3.0 + 1.5 * sin(t * 5.0 + i)
		badge.draw_line(sp - Vector2(r, 0), sp + Vector2(r, 0), Color(1.0, 0.95, 0.7, 0.9), 1.5)
		badge.draw_line(sp - Vector2(0, r), sp + Vector2(0, r), Color(1.0, 0.95, 0.7, 0.9), 1.5)
	var name_text := str(def.get("label", ContentDB.item_name(str(def.get("item", "")))))
	var sub := ""
	var col := UiKit.PALE_GOLD
	if focus:
		var who = Game.active()
		var avail: Dictionary = Game.world.object_available(who, def) if who else {"ok": true}
		sub = Game.world._verb(def) if avail.ok else str(avail.get("text", ""))
		if not avail.ok: col = UiKit.MIST
	UiKit.draw_nameplate(badge, name_text, sub, c.y - 36.0, col, UiKit.BRIGHT_JADE if focus else UiKit.MIST, 18 if focus else 16)

## S49 territory: the holder's banner beside the vein; stones waiting glint over it, and a contested mine pulses red.
func _draw_mine() -> void:
	var id := str(def.get("mine", ""))
	var mine: bool = Game.sect.holds(id)
	var banner := "banner_your_sect" if mine else str(Game.sect.rival(str(ContentDB.entry("territory", id).get("sect", ""))).get("banner", ""))
	SpriteCache.draw_prop(self, banner, "idle", t, Vector2(62, 2))
	if not mine: return
	var st: Dictionary = Game.sect.mines().get(id, {})
	if bool(st.get("contested", false)):
		# A ring of red on the ground around the vein and the banner: someone has come for it.
		var a := 0.45 + 0.25 * sin(t * 4.0)
		draw_set_transform(Vector2(30, 0), 0.0, Vector2(1.0, 0.32))
		draw_arc(Vector2.ZERO, 92.0 + 4.0 * sin(t * 4.0), 0.0, TAU, 48, Color(0.95, 0.32, 0.3, a), 4.0)
		draw_arc(Vector2.ZERO, 80.0, 0.0, TAU, 48, Color(0.95, 0.32, 0.3, a * 0.4), 2.0)
		draw_set_transform(Vector2.ZERO)
	if Game.sect.mine_stored(id) > 0:
		# Stones waiting in the carts: a cyan shine on the vein and glints rising off it.
		draw_set_transform(Vector2(0, -10), 0.0, Vector2(1.0, 0.45))
		draw_circle(Vector2.ZERO, 44.0, Color(0.45, 0.9, 1.0, 0.14 + 0.05 * sin(t * 2.0)))
		draw_set_transform(Vector2.ZERO)
		for i in 6:
			var ph := fmod(t * 0.5 + i / 6.0, 1.0)
			var sp := Vector2(-28.0 + i * 11.0 + sin(t * 2.0 + i) * 3.0, -28.0 - ph * 46.0)
			var col := Color(0.6, 0.97, 1.0, 0.95 * (1.0 - ph))
			var r := 4.0 * (1.0 - ph * 0.5)
			draw_line(sp - Vector2(r, 0), sp + Vector2(r, 0), col, 2.0)
			draw_line(sp - Vector2(0, r), sp + Vector2(0, r), col, 2.0)

## A garden bed (S45) shows its herb's patch art, small as a seedling and full size when ready.
func _draw_bed_herb() -> void:
	var c = Game.active()
	if c == null or Game.room_rt == null: return
	var rec: Dictionary = Game.crafting.beds(c).get(Game.room_rt.room_id + ":" + object_id, {})
	if str(rec.get("herb", "")) == "": return
	var prop := str(ContentDB.config("garden").get("props", {}).get(HerbRules.family(str(rec.herb)), ""))
	if prop == "": return
	var g := clampf(float(rec.get("progress", 0.0)), 0.0, 1.0)
	var k := 0.45 + 0.55 * g
	draw_set_transform(Vector2(0, -6), 0.0, Vector2(k, k))
	SpriteCache.draw_prop(self, prop, "ready", t, Vector2.ZERO, false)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if g >= 1.0: draw_circle(Vector2(0, -20), 16.0 + 2.0 * sin(t * 3.0), Color(0.6, 1.0, 0.7, 0.18))

## A Spirit Sense pulse (S45) reads a rare herb's time for a few seconds: how long it stays ripe, when it ripens,
## or the season it flowers in.
func _draw_sensed() -> void:
	var sn: Dictionary = Game.world.sensed_herbs.get(object_id, {})
	if sn.is_empty() or Game.sim_time > float(sn.get("until", 0.0)): return
	var left := float(sn.seconds) - (Clock.now_utc() - float(sn.get("utc", Clock.now_utc())))
	var text := ""
	if sn.get("dormant", false): text = Tx.t("ui.herb.sense_dormant") % ContentDB.name_of("seasons", str(sn.season))
	elif sn.get("spent", false): text = Tx.t("ui.herb.sense_spent")
	elif sn.get("ripe", false): text = Tx.t("ui.herb.sense_ripe") % UiKit.clock(left)
	else: text = Tx.t("ui.herb.sense_ripens") % UiKit.clock(left)
	var h := SpriteCache.prop_size(current_prop()).y if prop_id != "" else 40.0
	UiKit.draw_outlined(self, text, Vector2(-120, -h - 30), 15, Color("b9a7ff"), HORIZONTAL_ALIGNMENT_CENTER, 240)

## Earth Fire (G1): tongues of flame lick up out of the vent; an alchemist can set a furnace over it.
func _draw_earth_fire() -> void:
	for i in 5:
		var ph := t * (5.0 + i) + i * 1.7
		var x := -26.0 + i * 13.0 + sin(ph) * 2.0
		var h := 26.0 + 14.0 * absf(sin(ph * 0.8)) + (8.0 if i == 2 else 0.0)
		var w := 7.0 + (3.0 if i == 2 else 0.0)
		draw_colored_polygon(PackedVector2Array([Vector2(x - w, -2), Vector2(x + w, -2), Vector2(x + sin(ph * 1.3) * 3.0, -2 - h)]), Color(1.0, 0.45, 0.12, 0.75))
		draw_colored_polygon(PackedVector2Array([Vector2(x - w * 0.5, -2), Vector2(x + w * 0.5, -2), Vector2(x + sin(ph * 1.3) * 2.0, -2 - h * 0.6)]), Color(1.0, 0.85, 0.4, 0.85))
	draw_circle(Vector2(0, -8), 34.0, Color(1.0, 0.5, 0.15, 0.10 + 0.04 * sin(t * 6.0)))

## V10: a swarm's insects drift about it in loose loops.
func _draw_swarm() -> void:
	var col := Color(str(SWARM_MOTE.get(str(def.get("item", "")), "e8e0a0")))
	for i in 9:
		var a := t * (0.9 + 0.13 * i) + i * 0.7
		var p := Vector2(cos(a) * (26.0 + 5.0 * float(i % 3)), -46.0 + sin(a * 1.7) * 16.0 - float(i % 3) * 6.0)
		draw_circle(p, 2.6, Color(col, 0.28))
		draw_circle(p, 1.4, col)

## S50 Keeping Post: a jade pennant beside a node where one of your other characters keeps post.
func _draw_post_flag() -> void:
	if Game.room_rt == null or not str(def.type) in ["ore_vein", "herb_patch", "fishing_spot", "insect_swarm"]: return
	var n := 0
	for id in Game.characters:
		if str(id) == Game.active_id: continue
		var p: Dictionary = Game.posts.post_of(Game.character(str(id)))
		if str(p.get("object", "")) == object_id and str(p.get("room", "")) == Game.room_rt.room_id: n += 1
	if n == 0: return
	var base := Vector2(40, 0)
	draw_line(base, base + Vector2(0, -64), UiKit.BRONZE, 2.0)
	var wave := 2.0 * sin(t * 2.2)
	draw_colored_polygon(PackedVector2Array([base + Vector2(0, -64), base + Vector2(22, -58 + wave), base + Vector2(0, -50)]), Color("5fae8a"))
	for k in mini(n, 3) - 1:
		draw_circle(base + Vector2(6 + 6 * k, -44), 2.0, Color("5fae8a"))
