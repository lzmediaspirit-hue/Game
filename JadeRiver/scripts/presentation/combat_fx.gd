class_name CombatFx
extends RefCounted
## The fight's effects from the combat events, for both world views (the side view's world.gd and the top-down room of
## the redesign, Phase 2): a technique's cast at its tier (P6e, docs/moments_design.md §5) and a blow's number and
## spark. Positions are the effects layer's (world units, 1 unit = 1 screen px). On the top-down plane a cast turns to
## its aim (`aim`), mirrored so no sheet draws upside down. `host` is the view that shakes the camera (add_shake).

var fx: FxLayer
var host
var chest := 56.0                 ## a figure's chest over its feet (the side view's; the top-down body is shorter)
var cast_shake: Dictionary = {}   # "tech:<id>" -> true until the cast's first hit shakes (tiers 3 and up)

func _init(layer: FxLayer, view, chest_height := 56.0) -> void:
	fx = layer
	host = view
	chest = chest_height

## P6e a technique cast at its tier: a ring at the feet (from tier 2), a wash of its element over the screen (from tier
## 3, under the flash limiter), and its shape, drawn at the reach it really strikes (§5.4): a slash, a wave along the
## reach, a ring at it with echo rings inside, a rain of streaks, a pillar on the foe (`target_at`), or a ring and
## motes round the caster. A bolt is drawn by its projectile.
## Decision 23: with the technique's form animation (`vfx.anim`, data/fx_art.json) the cast plays that sheet instead of
## the procedural shape, timed so its impact frame lands on the pose's hit frame (`windup`, the timeline's hit_at),
## facing the cast, sized to the hitbox and at its tier's band; an area's edge (a ring at the true reach, §5.4) and
## a heal's radius are still drawn at the reach. The procedural shapes remain for a technique without a sheet.
func cast(tech: String, at: Vector2, facing: int, col: Color, windup: float, target_at: Vector2, aim := Vector2.ZERO) -> void:
	var t := ContentDB.entry("techniques", tech)
	var n := MomentRules.tier_numbers("tech:" + tech)
	var tier := int(t.get("vfx", {}).get("tier", 1))
	var reach := float(t.hitbox.x[1])
	var turn := 0.0
	if aim != Vector2.ZERO:
		facing = 1 if aim.x >= 0.0 else -1
		turn = (aim * facing).angle()
	var up := Vector2(0, -(chest - 6.0))
	if float(n.shake_s) > 0.0: cast_shake["tech:" + tech] = true
	if float(n.cast_ring_r) > 0.0: fx.add("ring", at, {"color": col, "radius": float(n.cast_ring_r), "dur": 0.3})
	if float(n.tint_alpha) > 0.0: fx.add("tint", at, {"color": Color(col, float(n.tint_alpha)), "dur": 0.4})
	var shape := str(t.get("vfx", {}).get("shape", "strike"))
	var form := str(t.get("vfx", {}).get("anim", ""))
	if not FxLayer.form_spec(form).is_empty():
		_cast_form(t, form, facing, turn, tier, reach, at, windup, target_at)
		if shape == "ring": fx.add("wave", at, {"color": col, "radius": reach, "size": n.wave_width, "dur": 0.45})
		if shape == "domain" and t.has("heal_radius"): fx.add("ring", at, {"color": Color(col, 0.7), "radius": float(t.heal_radius), "dur": 0.6})
		return
	match shape:
		"strike": fx.add("slash", at + Vector2(facing * 40, 0).rotated(turn) + up, {"color": col, "facing": facing, "turn": turn, "radius": 46.0 + 6.0 * (tier - 1), "dur": 0.3})
		"wave": fx.add("talisman_wave", at + up, {"color": col, "facing": facing, "radius": reach, "size": 20 + 2 * tier, "dur": 0.4})
		"ring":
			for i in int(n.echoes) + 1:
				fx.add("wave", at, {"color": col, "radius": reach * [1.0, 0.7, 0.4, 0.55][i], "size": n.wave_width, "dur": 0.45, "delay": 0.08 * i})
		"rain": fx.add("rain", at + Vector2(facing * reach * 0.5, 0).rotated(turn), {"color": col, "radius": reach * 0.5, "height": 240.0, "dur": 0.5,
			"count": MomentRules.particle_count(3 * int(t.get("hits", 1)) + 2 * tier)})
		"pillar": fx.add("pillar", target_at, {"color": col, "radius": 12.0 + 4.0 * tier, "height": 300.0, "dur": 0.35})
		"domain":
			fx.add("ring", at, {"color": col, "radius": float(t.get("heal_radius", reach)), "dur": 0.6})
			fx.add("motes", at + Vector2(0, -10), {"color": col, "dur": 0.8})

## A form's sheet on a cast: anchored by its `at` (the caster's chest or feet, the foe's feet or chest), sized by its
## `size` rule (band: bigger by tier, never past a strike's reach; reach: snapped down so a ring or a line never
## passes the hitbox; tile: repeated across the reach; travel: the crest crosses the reach over its life), and
## started so its impact frame lands on the hit frame: later when the wind-up is long, part-way in when it is short.
func _cast_form(t: Dictionary, form: String, facing: int, turn: float, tier: int, reach: float, at: Vector2, windup: float, target_at: Vector2) -> void:
	var a := FxLayer.form_spec(form)
	var band := FxLayer.band_of(tier)
	var span := float(a.span)
	var extra := {"turn": turn}
	var s := 1.0
	match str(a.size):
		"band":
			s = float(FxLayer.BAND_SCALE[band])
			if a.get("fit", false): s = minf(s, maxf(1.0, FxLayer.snap_scale(reach * 1.15 / span, true)))   # never past the reach, never under native
		"reach": s = maxf(1.0, FxLayer.snap_scale(reach / span, true))
		"stretch":   # a line along the reach: its exact length, the band's height
			s = reach / span
			extra.scale_y = float(FxLayer.BAND_SCALE[band])
		"tile":
			s = 1.0 if band < 2 else 1.5
			extra.tiles = maxi(1, ceili(reach / (float(a.cell[0]) * s)))
		"travel":
			s = float(FxLayer.BAND_SCALE[band])
			extra.travel = Vector2(facing * maxf(0.0, reach - span * s * 0.5), 0).rotated(turn)
	extra.scale = s
	var pos := at
	match str(a.at):
		"chest": pos = at + Vector2(0, -chest)
		"target": pos = target_at
		"target_chest": pos = target_at + Vector2(facing * 30, 0).rotated(turn) + Vector2(0, -(chest - 6.0))
	if windup >= 0.0:
		var lead := windup - float(a.impact) / float(a.fps)
		if lead >= 0.0: extra.delay = lead
		else: extra.start = -lead
	fx.play_form(form, str(t.get("element", "none")), tier, pos, facing, extra)

## A blow that did not land says so where it happened: Miss over the target, Immune over it, Evade over the player
## (at `player_at`, its figure's feet). Returns whether `name` was one of these.
func word(name: String, p: Dictionary, player_at: Vector2) -> bool:
	match name:
		"hit_missed": fx.label(Vector2(float(p.x), float(p.y) - float(p.get("alt", 60))), Tx.t("world_view.miss"), UiKit.MIST, 18)
		"hit_immune": fx.label(Vector2(float(p.x), float(p.y) - float(p.get("alt", 60)) - 40), Tx.t("world_view.immune"), UiKit.MIST, 18)
		"hit_dodged": fx.label(player_at + Vector2(0, -100), Tx.t("world_view.evade"), UiKit.BRIGHT_JADE, 18)
		_: return false
	return true

## A blow landed: its number (a technique's at its tier's size, stacked per foe, §5.5) and a spark in its element's
## colour and style; the first hit of a Heaven-grade cast shakes once, a heavy blow on the player or a crit shakes.
func hit(p: Dictionary) -> void:
	var pos := Vector2(float(p.get("x", 0)), float(p.get("y", 0)) - float(p.get("alt", 60)))
	var kind := str(p.get("target_kind", "enemy"))
	var amount := int(p.get("amount", 0))
	var color = UiKit.PAPER
	if kind == "player": color = UiKit.RED
	elif p.get("crit", false): color = UiKit.GOLD
	elif str(p.get("type", "")) == "qi": color = UiKit.QI
	elif str(p.get("type", "")) == "soul": color = UiKit.SOUL
	var src := str(p.get("source", ""))
	var n := MomentRules.tier_numbers(src)
	var tech := ContentDB.entry("techniques", src.trim_prefix("tech:")) if src.begins_with("tech:") else {}
	if Game.is_revealed("hud:damage_numbers") or kind == "player":
		fx.number(pos, UiKit.short(amount), color, int(n.number_size) if not tech.is_empty() else 22, bool(p.get("crit", false)),
			str(p.get("target", "")) + src if not tech.is_empty() else "", float(amount))
	fx.add("spark", pos + Vector2(0, 20), {"color": SpriteCache.element_color(str(p.get("element", "none"))), "dur": 0.25,
		"count": MomentRules.particle_count(int(n.spark_count)), "size": n.spark_size, "radius": n.spark_reach, "core": n.core_r,
		"style": tech.get("vfx", {}).get("particles", MomentRules.particle_style("", str(p.get("element", "none")), str(p.get("type", ""))))})
	if cast_shake.has(src):
		cast_shake.erase(src)
		host.add_shake(float(n.shake_s), float(n.shake_amp))
	if kind == "player" and Game.active() != null and amount > Game.active().pools.max_hp * 0.15: host.add_shake(0.25)
	if p.get("crit", false): host.add_shake(0.12)
	Audio.play("hit_crit" if p.get("crit", false) else ("hurt" if kind == "player" else "hit"))
