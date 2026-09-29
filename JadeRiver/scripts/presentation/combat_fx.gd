class_name CombatFx
extends RefCounted
## The fight's effects from the combat events, for both world views (the side view's world.gd and the top-down room of
## the redesign, Phase 2). The effects layer draws them (FxLayer.cast, FxLayer.hit); this is the view's part around
## them: the first hit of a Heaven-grade cast shakes once (P6e), a heavy blow on the player or a crit shakes, the
## sound, and the words a blow that did not land leaves. `host` is the view that shakes its camera (add_shake).

var fx: FxLayer
var host
var cast_shake: Dictionary = {}   # "tech:<id>" -> true until the cast's first hit shakes (tiers 3 and up)

func _init(layer: FxLayer, view) -> void:
	fx = layer
	host = view

## A technique cast from `at` toward `target` (the foe it lands on, or its point), turned to `aim` on the plane, drawn at
## `reach` (the hitbox's by default).
func cast(tech: String, at: Vector2, facing: int, col: Color, windup: float, target: Vector2, aim := Vector2.ZERO, reach := -1.0) -> void:
	var t := ContentDB.entry("techniques", tech)
	if float(MomentRules.tier_numbers("tech:" + tech).shake_s) > 0.0: cast_shake["tech:" + tech] = true
	fx.cast(t, at, facing, col, target, windup, reach, aim)

## A blow landed (a hit_landed payload): its number and spark at its tier (§5.2, §5.5), the shakes and the sound.
func hit(p: Dictionary) -> void:
	var pos := Vector2(float(p.get("x", 0)), float(p.get("y", 0)) - float(p.get("alt", 60)))
	var kind := str(p.get("target_kind", "enemy"))
	var src := str(p.get("source", ""))
	var amount := int(p.get("amount", 0))
	fx.hit(pos, float(amount), src, str(p.get("element", "none")), str(p.get("type", "")), bool(p.get("crit", false)), str(p.get("target", "")),
		Game.is_revealed("hud:damage_numbers") or kind == "player", kind == "player")
	if cast_shake.has(src):
		cast_shake.erase(src)
		var n := MomentRules.tier_numbers(src)
		host.add_shake(float(n.shake_s), float(n.shake_amp))
	# Decision 38: the top-down world weighs every blow itself (its kick, shake and mark: CombatFeel, TopdownFx).
	if host.has_method("feel_hit"): host.feel_hit(p)
	else:
		if kind == "player" and Game.active() != null and amount > Game.active().pools.max_hp * 0.15: host.add_shake(0.25)
		if p.get("crit", false): host.add_shake(0.12)
	Audio.hit(p)   # decision 43: the weapon, the struck body and the tail as one layered hit

## A blow that did not land says so where it happened: Miss over the target, Immune over it, Evade over the player
## (at `player_at`, its figure's feet). Returns whether `name` was one of these.
func word(name: String, p: Dictionary, player_at: Vector2) -> bool:
	match name:
		"hit_missed": fx.label(Vector2(float(p.x), float(p.y) - float(p.get("alt", 60))), Tx.t("world_view.miss"), UiKit.MIST, 18)
		"hit_immune": fx.label(Vector2(float(p.x), float(p.y) - float(p.get("alt", 60)) - 40), Tx.t("world_view.immune"), UiKit.MIST, 18)
		"hit_dodged": fx.label(player_at + Vector2(0, -100), Tx.t("world_view.evade"), UiKit.BRIGHT_JADE, 18)
		_: return false
	return true
