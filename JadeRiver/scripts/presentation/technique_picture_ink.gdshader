shader_type canvas_item;
// Decision 42: a technique picture in one ink (TechniquePicture). A pixel's lightness picks a colour on its element's
// ramp: `deep` at 0, `mid` at MID, `light` at 1. What is drawn says how by its modulate:
//   red 0             the ground, its stars and the form's marks, painted as lightness: taken as it is;
//   red 1, green 1    the figure's layers: their lightness mapped by the picture's tone. A card's presses it toward the
//                     dark (a dark shape with light touches on the mid ground, as the reference draws it); a button's
//                     lifts it (a light figure over a dark ground, so it reads at a thumb's size), its outline pixels
//                     (under `cut`) kept dark;
//   red 1, green 0    the figure's rim: its silhouette at lightness `rim`, a pixel out on each side under it.

uniform vec4 deep : source_color;
uniform vec4 mid : source_color;
uniform vec4 light : source_color;
uniform float cut = 0.0;      // below it a figure pixel keeps its own lightness (the outline)
uniform float base = -0.182;  // the figure's lightness: base + gain * its own
uniform float gain = 1.3;
uniform float rim = 0.9;

const float MID = 0.4;

varying vec4 ink;

void vertex() {
	ink = COLOR;
}

void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float l = dot(t.rgb, vec3(0.299, 0.587, 0.114));
	if (ink.r > 0.5) {
		l = ink.g > 0.5 ? (l < cut ? l : clamp(base + gain * l, 0.0, 1.0)) : rim;
	}
	vec3 c = l < MID ? mix(deep.rgb, mid.rgb, l / MID) : mix(mid.rgb, light.rgb, (l - MID) / (1.0 - MID));
	COLOR = vec4(c, t.a * ink.a);
}
