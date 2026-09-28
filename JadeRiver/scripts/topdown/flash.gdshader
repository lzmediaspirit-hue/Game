shader_type canvas_item;
// Decision 38: a struck body's hurt flash, shared by the player and the foes of the top-down world. `white` 1 turns the
// sprite's pixels white (the first frames of a blow), keeping its alpha; the modulate colour tints it after.
uniform float white = 0.0;

void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	COLOR = vec4(mix(c.rgb, vec3(1.0), white), c.a);
}
