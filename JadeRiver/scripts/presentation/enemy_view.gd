class_name EnemyView
extends Node2D
## Presentation of one EnemyState (monsters, bosses, spar opponents, pets and
## companions). Reads state every frame; never changes it. Creatures use their
## sprite sheet; humanoids use the layered avatar (the player-creation engine).

const Avatar = preload("res://scripts/avatar.gd")

var uid := 0
var sprite: CreatureSprite
var avatar: Node2D
var last_action := ""
var hp_timer := 0.0
var name_text := ""
var badge := "white"
var level_text := ""
var elite := false
var boss := false
var ally := false
var flying := false
var death_fade := 1.0
var tell := 0.0
var burrowed := false   # a burrower travelling under the ground: only its mound shows
var t := 0.0
## P5a (G4): the label's box in local coordinates at no offset, its kind for the layout pass (WorldLabels), and the
## offset in whole rows that world.gd gives it so no two labels touch.
var label_box := Rect2()
var label_kind := "foe"
var label_offset := Vector2.ZERO
var tag: Node2D   # the label's own canvas item, above every figure (WorldLabels.LABEL_Z)
## Redesign Phase 2: only the label (level, name, HP bar, the tell, statuses); the top-down room draws the figure.
var label_only := false
## Redesign Phase 4: only the figure (the avatar or the creature sheet, its action, facing, flash and an ally's blink),
## no label and no shadow: the top-down room's stand-in for a companion, a spirit animal or a foe its foe sheet does not
## draw (TopdownPlaces.stand_in), placed and shadowed by the room's FoeView at half size.
var art_only := false

func setup(e: EnemyState) -> void:
	uid = e.uid
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ally = e.team == "ally"
	elite = e.elite
	boss = e.is_boss()
	flying = bool(e.def.get("flying", false))
	label_kind = "ally" if ally else ("boss" if boss else ("elite" if elite else "foe"))
	name_text = e.display_name()
	var art: Dictionary = e.def.get("art", {"creature": e.def_id})
	if label_only: pass   # the top-down room draws the figure itself (redesign Phase 2)
	elif art.has("avatar"):
		avatar = Avatar.new()
		var outfit = art.avatar
		if outfit is String and outfit == "player":
			outfit = InventoryAuthority.outfit_for(Game.active()) if Game.active() else Wardrobe.defaults()
			if e.def_id == "the_reflection": name_text = Tx.t("view.reflection")
		var o: Dictionary = (outfit as Dictionary).duplicate()
		if art.has("tint"): o.tint = str(art.tint)   # a heart demon wears your face in crimson (G1)
		for k in ["hat", "cape", "weapon"]:
			if not o.has(k): o[k] = "none"
		avatar.outfit = o
		if o.has("tint"): avatar.modulate = Color(str(o.tint))
		if e.def_id == "the_reflection": avatar.modulate = Color(0.75, 0.85, 1.0, 0.85)
		add_child(avatar)
	else:
		sprite = CreatureSprite.new()
		sprite.creature_id = str(art.get("creature", e.def_id))
		sprite.fallback_size = Vector2(e.half_width() * 2.0, e.height())
		sprite.fallback_color = SpriteCache.element_color(e.element).darkened(0.35)
		add_child(sprite)
		if e.def.get("hollow_tint", false): sprite.set_tint(Color(0.8, 0.85, 0.88))
		# S46 form change: an animal at 90 purity stands larger in its lineage's colour.
		if art.has("tint"): sprite.set_tint(Color(str(art.tint)))
		if art.has("scale"): sprite.scale = Vector2.ONE * float(art.scale)
	if not art_only: tag = WorldLabels.make_tag(self, _draw_tag)
	_update_badge(e)
	sync(e, 0.0)

func _update_badge(e: EnemyState) -> void:
	var c = Game.active()
	if c == null or ally: return
	level_text = Tx.t("view.lv") % e.level
	var rank := WorldAuthority.beast_rank(e.def, e.level)
	if rank > 0: level_text = Tx.t("view.lv_rank") % [e.level, rank]   # S46: a beast shows its rank
	badge = CombatRules.badge_color(ProgressionRules.realm_index(c.cultivator.realm_key), e.realm_index, ProgressionRules.level(c), e.level)

func _process(delta: float) -> void:
	var rt: RoomRuntime = Game.room_rt
	var e: EnemyState = rt.enemies.get(uid) if rt else null
	if e == null:
		queue_free()
		return
	sync(e, delta)

func sync(e: EnemyState, delta: float) -> void:
	if not art_only:   # the stand-in is placed by the top-down room's FoeView
		position = Vector2(e.plane.x, e.plane.y - e.altitude - e.hover).snapped(Vector2(2, 2))
		z_index = 1500 + int(e.plane.y) + (40 if flying else 0)
	visible = not (e.hidden and not ally) or e.ai.state == "windup"
	if e.hidden and ally: visible = false
	# A burrower under the ground shows a travelling mound instead of vanishing (fog still hides the rest).
	burrowed = e.hidden and not ally and e.ai.state != "windup" and str(e.def.get("ai", {}).get("profile", "")) == "burrower" and e.alive
	if burrowed: visible = true
	if sprite: sprite.visible = not burrowed
	if avatar: avatar.visible = not burrowed
	t += delta
	var action := e.action
	if e.ai.state == "stagger": action = "hurt"
	if e.flash > 0.0 and action in ["idle", "walk"]: action = "hurt"
	if action != last_action:
		last_action = action
		if sprite: sprite.play(action, true)
		if avatar: _avatar_action(e, action)
	if sprite:
		sprite.facing = e.facing
		sprite.set_flash(e.flash / 0.12 if e.flash > 0 else 0.0)
	if avatar:
		avatar.facing = e.facing
		if e.flash > 0.0: avatar.modulate = Color(2, 2, 2) if int(e.flash * 60) % 2 == 0 else Color.WHITE
		elif avatar.outfit.has("tint"): avatar.modulate = Color(str(avatar.outfit.tint))   # phantoms keep their colour after a hit
		elif e.def_id == "the_reflection": avatar.modulate = Color(0.75, 0.85, 1.0, 0.85)
		else: avatar.modulate = Color.WHITE
	if not e.alive:
		death_fade = maxf(0.0, 1.0 - e.dead_time / 1.4)
		modulate.a = death_fade if avatar else 1.0
	if e.flash > 0.0 or e.pools.hp < e.pools.max_hp: hp_timer = 4.0
	hp_timer = maxf(0.0, hp_timer - delta)
	tell = 1.0 if e.ai.state == "windup" and not ally else maxf(0.0, tell - delta * 4.0)
	queue_redraw()
	if tag: tag.queue_redraw()

func _avatar_action(e: EnemyState, action: String) -> void:
	var weapon := str(avatar.outfit.get("weapon", "none"))
	var attack = {"none": "punch_2", "sword": "swing_1", "spear": "thrust_1", "dagger": "thrust_1", "staff": "thrust_3", "bow": "bow"}.get(weapon, "punch_2")
	match action:
		"walk": avatar.play("walk")
		"windup":
			avatar.play(attack)
			avatar.externally_timed = true
			avatar.elapsed = 0.05
		"attack":
			avatar.externally_timed = false
			avatar.play(attack)
			avatar.elapsed = 0.1
		"death":
			avatar.externally_timed = false
			avatar.play("meditate")
		_:
			avatar.externally_timed = false
			avatar.play("idle")

## The hump of earth a burrower pushes up as it travels, with grains thrown back behind it.
func _draw_mound(ground: Vector2, w: float) -> void:
	var mat := str(Game.room_rt.def.get("ground", {}).get("material", "earth")) if Game.room_rt else "earth"
	var lit: Color = Color("e2c48e") if mat == "sand" else Color("8a6a48")
	var dark: Color = Color("a8804e") if mat == "sand" else Color("5a4230")
	var r := maxf(18.0, w * 0.9)
	var bob := sin(t * 10.0) * 1.5
	var hump := PackedVector2Array()
	for i in 13:
		var a := PI * i / 12.0
		hump.append((ground + Vector2(-cos(a) * r, -sin(a) * (10.0 + bob))).snapped(Vector2(2, 2)))
	draw_colored_polygon(hump, dark)
	var top := PackedVector2Array()
	for i in 9:
		var a := PI * (0.15 + 0.7 * i / 8.0)
		top.append((ground + Vector2(-cos(a) * r * 0.7, -sin(a) * (8.0 + bob) - 1.0)).snapped(Vector2(2, 2)))
	draw_polyline(top, lit, 2.0)
	var back := -float(sign(e_facing())) if e_facing() != 0 else -1.0
	for i in 5:
		var life := fposmod(t * 2.2 + i * 0.21, 1.0)
		var p := ground + Vector2(back * (r * 0.6 + life * 26.0), -6.0 - sin(life * PI) * 14.0)
		draw_rect(Rect2(p.snapped(Vector2(2, 2)), Vector2(2, 2)), Color(lit, 1.0 - life))

func e_facing() -> int:
	var e: EnemyState = Game.room_rt.enemies.get(uid) if Game.room_rt else null
	return e.facing if e else 1

func _draw() -> void:
	if label_only: return
	var rt: RoomRuntime = Game.room_rt
	var e: EnemyState = rt.enemies.get(uid) if rt else null
	if e == null: return
	# The shadow falls on the surface under the body (a ledge, or the ground below a hop), not always on y = 0.
	var under: WalkSurface = rt.geometry.surface_under(e.plane, e.altitude + 0.5) if e.altitude > 0.5 else null
	var ground := Vector2(0, e.altitude + e.hover - (under.height_at(e.plane) if under else 0.0))
	if rt.topdown != null: ground = Vector2(0, e.altitude + e.hover - rt.topdown.floor_at(e.plane))   # the grid's floor under it
	var w := e.half_width()
	if burrowed:
		_draw_mound(ground, w)
		return
	if not art_only:   # the top-down room draws the shadow on the floor under it
		draw_set_transform(ground, 0.0, Vector2(1, 0.28))
		draw_circle(Vector2.ZERO, w * 1.1, Color(0.01, 0.035, 0.04, 0.35 * (death_fade if not e.alive else 1.0)))
		draw_set_transform(Vector2.ZERO)
	if not e.alive or not visible: return
	# S43 rule 12: an ally's blink to its owner arrives in a puff of mist.
	var bt := float(e.ai.get("blink_t", 0.0)) if ally else 0.0
	if bt > 0.0:
		var k := bt / 0.5
		for i in 6:
			var a := TAU * float(i) / 6.0
			draw_circle(Vector2(cos(a) * (18.0 + 16.0 * (1.0 - k)), -30.0 + sin(a) * 10.0), 9.0 * k + 3.0, Color(0.9, 0.97, 0.95, 0.55 * k))

## The label over the figure, drawn on `tag` above every figure in the room (P5a, G4): a foe's statuses, level and
## name, danger marks or crown and HP bar as one box at its own offset; a party member's thin HP line, only in a fight.
func _draw_tag() -> void:
	label_box = Rect2()
	var rt: RoomRuntime = Game.room_rt
	var e: EnemyState = rt.enemies.get(uid) if rt else null
	if e == null or burrowed or not e.alive or not visible: return
	var ci := tag
	var w := e.half_width()
	var top := -e.height() - 16.0
	if avatar: top = -104.0
	if ally:
		# P5a (mockup 01): a companion, the puppet or the animal shows only a thin HP line over its head, and only in a
		# fight; its name is on the HUD's party chip. The line sits lower than a foe's label (its own offset, G4).
		label_kind = "ally"
		if WorldLabels.party_fight:
			var lw := 40.0 if avatar else 30.0
			var line := Rect2(-lw * 0.5, (top + 10.0 if avatar else top + 8.0) + label_offset.y, lw, 5)
			label_box = Rect2(line.position - label_offset, line.size).grow(2.0)
			var frac := clampf(e.pools.hp / maxf(1.0, e.pools.max_hp), 0.0, 1.0)
			ci.draw_rect(line.grow(1.5), UiKit.INK)
			ci.draw_rect(line, UiKit.BAR_TROUGH)
			ci.draw_rect(Rect2(line.position, Vector2(line.size.x * frac, line.size.y)), UiKit.BRIGHT_JADE if frac > 0.3 else UiKit.RED)
		return
	# P5a (G4): the whole label (statuses, level and name, the danger marks or the crown, the HP bar) is one box that the
	# layout pass moves by whole rows (label_offset) so it never touches another label or sits under a HUD control.
	label_kind = "boss" if boss else ("elite" if elite else "foe")
	var base := top
	top += label_offset.y
	if tell > 0.0:
		UiKit.draw_outlined(ci, "!", Vector2(-40, top - 14), 26, Color(UiKit.RED, tell), HORIZONTAL_ALIGNMENT_CENTER, 80)
	var label := "%s  %s" % [level_text, name_text] if not boss else name_text
	var tw := UiKit.text_width(label, 17, true)
	var box := Rect2(-tw * 0.5 - 4.0, base - 17.0, tw + 8.0, 22.0)
	if shows_hp_bar(e) and not boss:
		var bw := clampf(w * 2.2, 40, 90)
		var r := Rect2(-bw * 0.5, top + 6, bw, 6)
		box = box.merge(Rect2(-bw * 0.5 - 2.0, base + 4.0, bw + 4.0, 10.0))
		ci.draw_rect(r.grow(2), UiKit.INK)
		ci.draw_rect(r, Color("3a1418"))
		ci.draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(e.pools.hp / maxf(1.0, e.pools.max_hp), 0, 1), r.size.y)), UiKit.RED)
	var col := UiKit.badge_color(badge)
	if elite: col = UiKit.GOLD
	UiKit.draw_outlined(ci, label, Vector2(-130, top), 17, col, HORIZONTAL_ALIGNMENT_CENTER, 260)
	if not boss:
		_danger_marks(ci, tw * 0.5 + 8, top - 6, col)
		if badge in ["orange", "red", "green", "grey"]: box = box.merge(Rect2(tw * 0.5 + 2.0, base - 12.0, 26.0, 12.0))
	if elite:
		var cx := -UiKit.text_width(label, 16) * 0.5 - 12
		box = box.merge(Rect2(cx - 8.0, base - 15.0, 16.0, 12.0))
		ci.draw_colored_polygon(PackedVector2Array([Vector2(cx - 7, top - 4), Vector2(cx - 7, top - 12), Vector2(cx - 3, top - 8),
			Vector2(cx, top - 14), Vector2(cx + 3, top - 8), Vector2(cx + 7, top - 12), Vector2(cx + 7, top - 4)]), UiKit.GOLD)
	# Status icons at their native 12 px render, 14 apart.
	var sx := -float(e.pools.statuses.size()) * 7.0
	if not e.pools.statuses.is_empty(): box = box.merge(Rect2(sx, base - 30.0, 14.0 * e.pools.statuses.size(), 14.0))
	for s in e.pools.statuses:
		SpriteCache.draw_icon(ci, Rect2(sx, top - 30, 14, 14), str(ContentDB.entry("status_effects", str(s.id)).get("icon", s.id)))
		sx += 14
	label_box = box

## Does this foe show its HP: a boss always (on the HUD's boss bar); any other foe once the HUD shows foes' HP (Crab
## Trouble, before the first fight), over its head whenever it is in a fight, was just hurt, or is an elite.
func shows_hp_bar(e: EnemyState) -> bool:
	if ally or e == null or not e.alive: return false
	if boss: return true
	return Game.is_revealed("hud:enemy_hp_bars") and (hp_timer > 0.0 or elite or e.in_fight())

## Colour-blind-safe danger badge: shapes say what the colour says (S40 release checklist).
## ▲ tougher (5+ levels above), ▲▲ a realm or more above, ▽ weaker (5+ below), none otherwise.
func _danger_marks(ci: CanvasItem, x: float, y: float, col: Color) -> void:
	var ups: int = int({"orange": 1, "red": 2}.get(badge, 0))
	for i in ups:
		var cx: float = x + i * 11.0
		var tri := PackedVector2Array([Vector2(cx - 5, y + 4), Vector2(cx + 5, y + 4), Vector2(cx, y - 5)])
		ci.draw_colored_polygon(tri, UiKit.INK)
		ci.draw_colored_polygon(PackedVector2Array([Vector2(cx - 3.5, y + 3), Vector2(cx + 3.5, y + 3), Vector2(cx, y - 3)]), col)
	if badge in ["green", "grey"]:
		var down := PackedVector2Array([Vector2(x - 5, y - 4), Vector2(x + 5, y - 4), Vector2(x, y + 5)])
		ci.draw_colored_polygon(down, UiKit.INK)
		ci.draw_colored_polygon(PackedVector2Array([Vector2(x - 3.5, y - 3), Vector2(x + 3.5, y - 3), Vector2(x, y + 3)]), col)
