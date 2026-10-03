extends "res://tests/lib/suite.gd"
## Audit 45, S6: the HUD in parts (docs/architecture/hud.md). Its callers call it as before: every method it had before
## the split is still one of the HUD's, and a HUD made with new() (not in the tree, as the tests make it) has its parts.
## And the swap's place keeps clear of the context's label: ring 2's sixth place (292°, the weapon swap's) crossed the
## label's top corner by 3 px at 1280 × 720 until the label became CTX_LABEL_W 116 wide; nothing else moved.
## Run headless:  godot --headless --path . res://tests/hud_tests.tscn

## The HUD's methods before the split (hud.gd at audit 45's S6): the public ones, and the private ones tests and tools
## call by name. Each is still a method of the HUD, forwarded to its part.
const API := ["bound", "shown", "scroll_skills", "advance_scroll", "set_state", "finish_tap", "toggle_on", "ring2_places",
	"hit_targets", "tour_targets", "tour_rect", "point_badges", "open_points", "points_pop", "obstacle_rects",
	"log_rect", "panel_rect", "go_hit", "role_at", "press", "toggle_fan", "drag", "release", "armed",
	"tap_cultivate", "primary", "attack_first", "keep_post", "place_pose_of", "open_place_page", "use_context",
	"begin_harvest", "swap_weapon", "use_treasure", "drink_draught", "use_quick", "set_blocked", "set_moment_lock",
	"set_scene_lock", "world_news", "toggle_sphere", "toggle_presence", "add_log", "spar_line", "toast",
	"drop_toasts_from", "ring", "glyph", "skill_position", "draw_skill_slot", "draw_skill_scroll", "bar",
	"hub_ready", "tracker_objective", "place_marks", "minimap_place_at", "minimap_way", "context_label_rect",
	"attack_glyph", "attack_gesture", "armed_glow", "log_rows", "toast_sub_rows", "toast_rects", "_layout", "_on",
	"_slot_filled", "_fan_items", "_ring2", "_frame_badges", "_tick_points", "_context_shown", "_tick_fight",
	"_tick_aims", "_tick_place_pose", "_after_interact", "_caption_worthy", "_context_glyph", "_band_on_top",
	"_edge_point", "_on_event", "_notification"]

func _main() -> void:
	_facade()
	_swap_clear_of_label()
	end_suite()

func _facade() -> void:
	var hud = load("res://scripts/hud.gd").new()
	var gone: Array = API.filter(func(m): return not hud.has_method(m))
	check(gone.is_empty(), "every method the HUD had before its split is still the HUD's (%s)" % [gone])
	var parts := ["layout", "tours", "input", "actions", "notices", "controls", "panels", "minimap", "top_stack", "side_view"]
	var missing: Array = parts.filter(func(k): return not (hud.get(k) is HudPart) or hud.get(k).hud != hud)
	check(missing.is_empty(), "a HUD made with new() has its ten parts, each its own (%s)" % [missing])
	hud.free()

## Ring 2 with the context out (Talk) and a crowd round it, right- and left-handed: no circle of ring 2 (26 px) touches
## the context's words; the words stand where they stood, centred under the button.
func _swap_clear_of_label() -> void:
	var hud = load("res://scripts/hud.gd").new()
	var loads := [["context", "swap"], ["presence", "quick:0", "quick:1", "quick:2", "context", "swap"],
		["presence", "sphere", "quick:0", "quick:1", "quick:2", "draught", "treasure:0", "treasure:1", "context", "swap"],
		["presence", "quick:0", "quick:1", "quick:2", "draught", "context"]]
	var touching: Array = []
	var placed := true
	for lh in [false, true]:
		hud.left_handed = lh
		hud._layout()
		for roles in loads:
			var items: Array = hud.ring2_places(roles.map(func(r): return {"role": r, "home": r}))
			var ctx: Array = items.filter(func(o): return str(o.role) == "context")
			if ctx.is_empty(): continue
			hud.context_center = ctx[0].center
			var lab: Rect2 = hud.context_label_rect()
			placed = placed and is_equal_approx(lab.get_center().x, hud.context_center.x) and is_equal_approx(lab.position.y, hud.context_center.y + hud.CTX_R + 2.0)
			for o in items:
				if str(o.role) == "context" or (o.center as Vector2).distance_to(hud.attack_center) > hud.RING2_R + 10.0: continue
				var cp := Vector2(clampf(o.center.x, lab.position.x, lab.end.x), clampf(o.center.y, lab.position.y, lab.end.y))
				if cp.distance_to(o.center) < 26.0: touching.append("%s %s at %s" % ["left" if lh else "right", o.role, o.center])
	check(touching.is_empty() and placed, "no circle of ring 2 touches the context's words, the swap's among them, right- and left-handed (%s)" % [touching])
	hud.left_handed = false
	hud._layout()
	var swap_at: Vector2 = hud._on(hud.attack_center, hud.RING2_R, 292.0)
	check(swap_at == Vector2(1245, 407) and hud.attack_center == Vector2(1165, 605), "the swap and the cluster stand where they stood (%s, %s)" % [swap_at, hud.attack_center])
	hud.free()
