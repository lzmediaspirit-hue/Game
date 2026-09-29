shader_type canvas_item;
// Decision 42: a technique picture in one ink (TechniquePicture). A pixel's lightness picks a colour on its element's
// ramp: `deep` at 0, `mid` at MID, `light` at 1. What is drawn says how by its modulate:
//   red 0             the ground, its stars and the form's marks, painted as lightness: taken as it is;
//   red 1, green 1    the figure's layers: their lightness pressed toward the dark (the figure reads as a dark shape
//                     with light touches, its face and its highlights, on the mid ground);
//   red 1, green 0    the figure's rim: its silhouette in the light, drawn a pixel out on each side under it.

uniform vec4 deep : source_color;
uniform vec4 mid : source_color;
uniform vec4 light : source_color;

const float MID = 0.4;

varying vec4 ink;

void vertex() {
	ink = COLOR;
}

void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float l = dot(t.rgb, vec3(0.299, 0.587, 0.114));
	if (ink.r > 0.5) {
		l = ink.g > 0.5 ? clamp((l - 0.14) * 1.3, 0.0, 1.0) : 0.9;
	}
	vec3 c = l < MID ? mix(deep.rgb, mid.rgb, l / MID) : mix(mid.rgb, light.rgb, (l - MID) / (1.0 - MID));
	COLOR = vec4(c, t.a * ink.a);
}
