class_name ObjectView
extends Node2D
## A world object (Part 9.9 state sets): shrine, nodes, breakables, chests,
## stations, boards, stones, fishing ripples, quest pickups. Reads RoomRuntime
## object state; shows a verb prompt when it is the context target.

const DEFAULT_PROP := {"shrine": "shrine", "qi_spring": "qi_spring", "training_stump": "training_stump", "lifting_stone": "lifting_stone",
	"training_dummy": "training_dummy", "jar": "jar", "crate": "crate", "wine_jar": "wine_jar", "chest": "chest", "storage_chest": "storage_chest",
	"notice_board": "notice_board", "signpost": "signpost", "teleport_stone": "teleport_stone", "insight_stone": "insight_stone",
	"cooking_pot": "cooking_pot", "alchemy_furnace": "alchemy_furnace", "forge_anvil": "forge_anvil", "fishing_spot": "fishing_ripple",
	"rite_circle": "rite_circle", "bell": "small_bell", "spar_post": "weapon_rack", "inspect": "grey_patch", "herb_patch": "willow_moss_patch",
	"ore_vein": "copper_vein", "formation_table": "formation_node", "garden_bed": "willow_moss_patch",
	"defence_drum": "small_bell", "treasure_plot": "treasure_plot", "treasure_tree": "nine_bough_jade_tree",
	"star_sight": "star_sight_stone", "chart_table": "star_chart_table", "shipyard_slip": "shipyard_slip", "starsea_dock": "cloud_skiff",
	"air_pocket": "qi_spring", "earth_vent": "gas_vent"}

var def: Dictionary = {}
var object_id := ""
var t := 0.0
var focus := false
var hit_flash := 0.0
var prop_id := ""

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

func state_name() -> String:
	var rt: RoomRuntime = Game.room_rt
	var st: Dictionary = rt.objects.get(object_id, {}) if rt else {}
	var s := str(st.get("state", "ready"))
	var c = Game.active()
	match str(def.type):
		"herb_patch": return "depleted" if s == "depleted" else "ready"
		"star_sight": return "idle" if s == "depleted" else "active"   # the engraved stars glow while a reading waits
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

func _draw() -> void:
	var st := state_name()
	var drawn := false
	if def.type == "pickup" and not def.has("prop"):
		var ic := SpriteCache.icon(str(def.get("item", "")))
		if ic:
			var bob := sin(t * 3.0) * 3.0
			draw_texture_rect(ic, Rect2(-16, -34 + bob, 32, 32), false)
			drawn = true
	elif prop_id != "":
		drawn = SpriteCache.draw_prop(self, current_prop(), st, t, Vector2.ZERO, bool(def.get("flip", false)))
	if not drawn and def.type != "pickup":
		draw_rect(Rect2(-12, -24, 24, 24), UiKit.BRONZE)
	if def.type == "earth_vent": _draw_earth_fire()
	if focus:
		var c = Game.active()
		var avail: Dictionary = Game.world.object_available(c, def) if c else {"ok": true}
		var label := Game.world._verb(def)
		var h := SpriteCache.prop_size(current_prop()).y if prop_id != "" else 40.0
		UiKit.draw_outlined(self, label if avail.ok else str(avail.get("text", "")), Vector2(-120, -h - 8), 16,
			UiKit.PALE_GOLD if avail.ok else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 240)

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
