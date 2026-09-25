class_name ClimbableView
extends Node2D
## A ladder, rope, vine or chain (S43 rule 5), drawn from its foot on the ground line to its top step.
var def: Dictionary = {}

static func make(d: Dictionary) -> ClimbableView:
	var v := ClimbableView.new()
	v.def = d
	var at: Array = d.at
	v.z_index = 1500 + int(float(at[1])) - 2
	return v

func _draw() -> void:
	var at: Array = def.at
	var top_at: Array = def.get("top_at", def.at)
	var foot := Vector2(float(at[0]), float(at[1]) - float(def.get("bottom_alt", 0)))
	var head := Vector2(float(top_at[0]), float(top_at[1]) - float(def.get("top_alt", 88)))
	match str(def.get("kind", "ladder")):
		"rope", "vine":
			var col := Color("8a6a3c") if str(def.kind) == "rope" else Color("4f7a3a")
			var pts := PackedVector2Array()
			for i in 13:
				var t := i / 12.0
				pts.append(foot.lerp(head, t) + Vector2(sin(t * 9.0) * 2.0, 0))
			draw_polyline(pts, col.darkened(0.3), 5.0)
			draw_polyline(pts, col, 3.0)
			if str(def.kind) == "vine":
				for i in range(1, 12, 2):
					var p := foot.lerp(head, i / 12.0)
					draw_circle(p + Vector2(4 if i % 4 == 1 else -4, 0), 3.0, Color("6a9a4a"))
		"chain":
			var n := int(foot.distance_to(head) / 10.0)
			for i in n:
				var p := foot.lerp(head, (i + 0.5) / float(n))
				draw_arc(p, 4.0, 0, TAU, 8, Color("8c9296"), 2.0)
		_:
			# A bamboo ladder: two rails and rungs every 14 units.
			for dx in [-12.0, 10.0]:
				draw_line(foot + Vector2(dx, 0), head + Vector2(dx, 0), Color("5d4a2a"), 4.0)
				draw_line(foot + Vector2(dx, 0), head + Vector2(dx, 0), Color("a88a4f"), 2.0)
			var steps := int(foot.distance_to(head) / 14.0)
			for i in range(1, steps + 1):
				var p := foot.lerp(head, float(i) / float(steps + 1))
				draw_line(p + Vector2(-11, 0), p + Vector2(9, 0), Color("4a3a22"), 4.0)
				draw_line(p + Vector2(-11, -1), p + Vector2(9, -1), Color("c2a364"), 2.0)
