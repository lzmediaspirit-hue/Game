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

func setup(e: EnemyState) -> void:
	uid = e.uid
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ally = e.team == "ally"
	elite = e.elite
	boss = e.is_boss()
	flying = bool(e.def.get("flying", false))
	name_text = e.display_name()
	var art: Dictionary = e.def.get("art", {"creature": e.def_id})
	if art.has("avatar"):
		avatar = Avatar.new()
		var outfit = art.avatar
		if outfit is String and outfit == "player":
			outfit = InventoryAuthority.outfit_for(Game.active()) if Game.active() else Wardrobe.defaults()
			name_text = "Reflection"
		var o: Dictionary = (outfit as Dictionary).duplicate()
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
	_update_badge(e)
	sync(e, 0.0)

func _update_badge(e: EnemyState) -> void:
	var c = Game.active()
	if c == null or ally: return
	level_text = "Lv %d" % e.level
	badge = CombatRules.badge_color(ProgressionRules.realm_index(c.cultivator.realm_key), e.realm_index, ProgressionRules.level(c), e.level)

func _process(delta: float) -> void:
	var rt: RoomRuntime = Game.room_rt
	var e: EnemyState = rt.enemies.get(uid) if rt else null
	if e == null:
		queue_free()
		return
	sync(e, delta)

func sync(e: EnemyState, delta: float) -> void:
	position = Vector2(e.plane.x, e.plane.y - e.altitude - e.hover).snapped(Vector2(2, 2))
	z_index = 1500 + int(e.plane.y) + (40 if flying else 0)
	visible = not (e.hidden and not ally) or e.ai.state == "windup"
	if e.hidden and ally: visible = false
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
		elif e.def_id != "the_reflection" and not avatar.outfit.has("tint"): avatar.modulate = Color.WHITE
	if not e.alive:
		death_fade = maxf(0.0, 1.0 - e.dead_time / 1.4)
		modulate.a = death_fade if avatar else 1.0
	if e.flash > 0.0 or e.pools.hp < e.pools.max_hp: hp_timer = 4.0
	hp_timer = maxf(0.0, hp_timer - delta)
	tell = 1.0 if e.ai.state == "windup" and not ally else maxf(0.0, tell - delta * 4.0)
	queue_redraw()

func _avatar_action(e: EnemyState, action: String) -> void:
	var weapon := str(avatar.outfit.get("weapon", "none"))
	var attack := {"none": "punch_2", "sword": "swing_1", "spear": "thrust_1", "dagger": "thrust_1", "staff": "thrust_3", "bow": "bow"}.get(weapon, "punch_2")
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

func _draw() -> void:
	var rt: RoomRuntime = Game.room_rt
	var e: EnemyState = rt.enemies.get(uid) if rt else null
	if e == null: return
	var ground := Vector2(0, e.altitude + e.hover)
	var w := e.half_width()
	draw_set_transform(ground, 0.0, Vector2(1, 0.28))
	draw_circle(Vector2.ZERO, w * 1.1, Color(0.01, 0.035, 0.04, 0.35 * (death_fade if not e.alive else 1.0)))
	draw_set_transform(Vector2.ZERO)
	if not e.alive or not visible: return
	var top := -e.height() - 16.0
	if avatar: top = -104.0
	if tell > 0.0 and not ally:
		UiKit.draw_outlined(self, "!", Vector2(-40, top - 14), 26, Color(UiKit.RED, tell), HORIZONTAL_ALIGNMENT_CENTER, 80)
	if ally:
		UiKit.draw_outlined(self, name_text, Vector2(-80, top), 16, Color("8fd3ff"), HORIZONTAL_ALIGNMENT_CENTER, 160)
		return
	var show_hp := hp_timer > 0.0 or elite or boss
	if Game.is_revealed("hud:enemy_hp_bars") or boss:
		if show_hp and not boss:
			var bw := clampf(w * 2.2, 40, 90)
			var r := Rect2(-bw * 0.5, top + 6, bw, 6)
			draw_rect(r.grow(2), UiKit.INK)
			draw_rect(r, Color("3a1418"))
			draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(e.pools.hp / maxf(1.0, e.pools.max_hp), 0, 1), r.size.y)), UiKit.RED)
	var label := "%s  %s" % [level_text, name_text] if not boss else name_text
	var col := UiKit.badge_color(badge)
	if elite: col = UiKit.GOLD
	UiKit.draw_outlined(self, label, Vector2(-110, top), 16, col, HORIZONTAL_ALIGNMENT_CENTER, 220)
	if elite:
		var cx := -UiKit.text_width(label, 16) * 0.5 - 12
		draw_colored_polygon(PackedVector2Array([Vector2(cx - 7, top - 4), Vector2(cx - 7, top - 12), Vector2(cx - 3, top - 8),
			Vector2(cx, top - 14), Vector2(cx + 3, top - 8), Vector2(cx + 7, top - 12), Vector2(cx + 7, top - 4)]), UiKit.GOLD)
	var sx := -float(e.pools.statuses.size()) * 7.0
	for s in e.pools.statuses:
		var ic := SpriteCache.icon(str(ContentDB.entry("status_effects", str(s.id)).get("icon", s.id)))
		if ic: draw_texture_rect(ic, Rect2(sx, top - 30, 14, 14), false)
		sx += 14
