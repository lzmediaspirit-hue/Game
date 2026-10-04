class_name TopdownLight
extends RefCounted
## Decision 40, runtime light (docs/redesign/art_bible.md §14.2 and §14.11): every colour, alpha, length and count of
## the top-down world's runtime light, in this one block, matched to the Terrain v2 contract. The tiles bake their
## static light (lips, rims, AO, the step's cast shade, patches, water depth); the runtime owns what depends on the
## room and the hour:
##   - cast shadows of tall props, buildings and drops of two levels or more, baked once per room (TopdownShadows);
##   - the colour grade per area and per hour, night and its lights, cloud shade and particles (TopdownAtmosphere).
## One sun, high in the north-west: shadows fall to the lower right, a translucent blue-violet, never black or grey.

# ------------------------------------------------------------------ the contract's colours (§14.2, palette.py)
const SUN := Color("ffe9a6")          ## `SUN`: the warm light on lit edges
const SHADOW := Color("241f4f")       ## `SHADOW`: every shadow, always translucent
const MIST := Color("afc9d1")         ## `MIST`: mist over water and low ground
const TONE_SHADE := Color("0e4a58")   ## the shade patches' tint (§14.2 after the polish pass), and the drifting cloud shade's
const PETAL := Color("e7a0be")        ## `PETAL` step 1: blossom

# ------------------------------------------------------------------ cast shadows (TopdownShadows)
## Where a shadow falls: a point h art px high casts at (+0.45 h, +0.20 h) from its foot on screen.
const SUN_STEP := Vector2(0.45, 0.2)
## A cast shadow's alpha: its body, and its 2 px stepped edge (no blur, no dither); on the water at most the edge's.
const SHADOW_BODY := 0.41
const SHADOW_EDGE := 0.25
const SHADOW_RIM_PX := 2
const WATER_SHADOW := 0.25
## The height (art px) under which the grid casts nothing at runtime: a step of one level is the tiles' own `shade_w`
## east of it and `ao_n` south of it. From two levels up the drop casts, its first px south of the face left to `ao_n`
## and the next px and the first NEAR_PX east of it at the edge's alpha, so over the baked shade the total darkening
## stays at or under 0.6 (the stacking cap).
const GRID_MIN_H := 32
const NEAR_PX := 4
## A body's contact shadow (the blob under feet: the player, villagers, foes) in the shadows' colour: its rim and its
## core as fractions of the blob's alpha (at the player's 0.55: 0.41 and a core of 0.6).
const BLOB := Color("241f4f")
const BLOB_RIM := 0.75
const BLOB_CORE := 0.58
## The props whose sprite casts its silhouette (the others are flat or on the water). Buildings and crate stacks with a
## standable top cast as blocks of their height, like the grid.
const CASTS := ["bamboo", "banner_cloud", "banner_jade", "barrel", "boulder", "dead_tree", "incense", "lantern", "lantern_red",
	"notice", "pine", "post", "shrub", "weapon_rack", "willow",
	# The foliage kit's solid pieces (art bible §14.12); its trees are left out, their crowns' shade is baked in the sheet.
	"bush", "bush_azalea", "bush_wide", "hedge_2", "hedge_3", "hedge_4", "fence_2", "fence_3", "fence_4", "rock_mossy",
	"rock_small", "shrine_small", "pot_bonsai", "pot_orchid"]

# ------------------------------------------------------------------ colour grade (per area, then per hour)
## A grade (§14.2: the tiles are graded already): highlights at most 4% toward `hi` (SUN; the marsh and the peaks
## MIST), darks at most 4% toward SHADOW, and saturation at most +5%. Chosen by the room's backdrop.
const GRADES := {
	"day": {"sun": 0.03, "shade": 0.03, "sat": 1.03, "hi": SUN},
	"village": {"sun": 0.04, "shade": 0.03, "sat": 1.05, "hi": SUN},
	"marsh": {"sun": 0.04, "shade": 0.04, "sat": 0.92, "hi": MIST},
	"jade": {"sun": 0.03, "shade": 0.03, "sat": 1.04, "hi": SUN},
	"cloud": {"sun": 0.03, "shade": 0.04, "sat": 1.0, "hi": MIST},
	"peak": {"sun": 0.04, "shade": 0.04, "sat": 0.95, "hi": MIST},
	"interior": {"sun": 0.04, "shade": 0.03, "sat": 1.0, "hi": SUN},
	"dusk": {"sun": 0.04, "shade": 0.04, "sat": 1.0, "hi": SUN},
	"night": {"sun": 0.0, "shade": 0.04, "sat": 0.9, "hi": SUN},
}
## T3: the area of the Lantern Star Field and the star field past it (their backdrops are the side view's night skies):
## the night grade at the story's night, whatever the clock says, a little mist.
const STARLIT := {"grade": "night", "clock": false, "hour": "night_story", "mist": 0.6, "motes": 0.0}
## T3: the star field past the Lantern Star Field (R9's zones): starlit, and the drop past their islands' brinks is the
## starry void, not a sea of cloud (TopdownVista reads `void`).
const STAR_VOID := {"grade": "night", "clock": false, "hour": "night_story", "mist": 0.6, "motes": 0.0, "void": true}
## T3: a room whose backdrop is the outdoors' but which lies under rock (the Clan Hearth's cavern behind the Hold Gate):
## its own area.
const ROOM_AREAS := {"ir_clan_hearth": "cave"}
## An area: its grade, whether the game's clock turns its hours (outdoors), its fixed hour otherwise, and how much mist
## and how many motes it holds (x the particle caps below).
const AREAS := {
	"valley_day": {"grade": "village", "clock": true, "mist": 0.6, "motes": 1.0},
	"marsh": {"grade": "marsh", "clock": true, "mist": 1.6, "motes": 0.5},
	"sect_jade": {"grade": "jade", "clock": true, "mist": 0.4, "motes": 1.0},
	"sect_cloud": {"grade": "cloud", "clock": true, "mist": 0.6, "motes": 0.8},
	"mist_peak": {"grade": "peak", "clock": true, "mist": 1.2, "motes": 0.6},
	"bamboo": {"grade": "jade", "clock": true, "mist": 0.6, "motes": 1.0},
	"interior": {"grade": "interior", "clock": false, "hour": "lamplit", "mist": 0.0, "motes": 0.4},
	"cave": {"grade": "interior", "clock": false, "hour": "lamplit", "mist": 0.0, "motes": 0.3},
	"valley_dusk": {"grade": "dusk", "clock": false, "hour": "dusk", "mist": 0.8, "motes": 0.6},
	"valley_night": {"grade": "night", "clock": false, "hour": "night_story", "mist": 1.0, "motes": 0.0},
	# T3 (topdown_mechanics.md, the R7, R8 and R9 rooms' light): the tomb's halls are lamp-lit, as a cave; the sky-sea
	# and star-field zones lie under the side view's night skies, starlit whatever the clock says; the Lantern Heart is
	# lit from within, as a cave.
	"sunscar_tomb": {"grade": "interior", "clock": false, "hour": "lamplit", "mist": 0.0, "motes": 0.3},
	"skyport_wreck": STARLIT, "lantern_harbor": STARLIT, "star_shoals": STARLIT, "blackmast_haven": STARLIT,
	"wyrmnest_isles": STARLIT, "warden_citadel": STAR_VOID, "orbit_ruins": STAR_VOID, "ashen_reach": STAR_VOID,
	"nebula_deep": STAR_VOID, "starsea": STAR_VOID,
	"lantern_heart": {"grade": "interior", "clock": false, "hour": "lamplit", "mist": 0.0, "motes": 0.6},
	"": {"grade": "day", "clock": true, "mist": 0.6, "motes": 1.0},
}
## The night tint (§14.2: it stays `#8FA0C8`): the ambient light the night layer multiplies the world by after dark.
const NIGHT := Color("8fa0c8")
## The hours: the ambient light the night layer multiplies the world by, how bright the lights burn (0 by day), the
## light the player carries (a pale glow round the feet after dark, so the body reads), how strong the sun's cast
## shadows are (faint under the moon), the grade's share (x its sun and shade, x its saturation), and what flies. The
## clock's four phases (Clock.time_of_day) cross-fade over HOUR_FADE of the day; a night room keeps "night_story", an
## interior "lamplit".
const HOURS := {
	"morning": {"ambient": Color(1.0, 0.98, 0.96), "lights": 0.0, "carry": 0.0, "shadows": 0.85, "grade": 0.8, "sat": 0.98,
		"motes": 1.0, "fireflies": 0.0, "clouds": 0.6, "mist": 1.8, "glints": 0.7},
	"day": {"ambient": Color(1, 1, 1), "lights": 0.0, "carry": 0.0, "shadows": 1.0, "grade": 1.0, "sat": 1.0,
		"motes": 1.0, "fireflies": 0.0, "clouds": 1.0, "mist": 1.0, "glints": 1.0},
	"evening": {"ambient": Color(1.0, 0.93, 0.86), "lights": 0.5, "carry": 0.0, "shadows": 0.8, "grade": 1.0, "sat": 1.0,
		"motes": 0.8, "fireflies": 0.3, "clouds": 0.5, "mist": 1.2, "glints": 0.6},
	"night": {"ambient": NIGHT, "lights": 1.0, "carry": 0.3, "shadows": 0.35, "grade": 1.0, "sat": 0.95,
		"motes": 0.0, "fireflies": 1.0, "clouds": 0.0, "mist": 1.2, "glints": 0.0},
	"night_story": {"ambient": NIGHT, "lights": 1.0, "carry": 0.3, "shadows": 0.35, "grade": 1.0, "sat": 1.0,
		"motes": 0.0, "fireflies": 1.0, "clouds": 0.0, "mist": 1.0, "glints": 0.0},
	"lamplit": {"ambient": Color(0.9, 0.87, 0.85), "lights": 0.8, "carry": 0.0, "shadows": 0.6, "grade": 1.0, "sat": 1.0,
		"motes": 1.0, "fireflies": 0.0, "clouds": 0.0, "mist": 0.0, "glints": 0.0},
	"dusk": {"ambient": Color(0.92, 0.85, 0.86), "lights": 0.75, "carry": 0.0, "shadows": 0.6, "grade": 1.0, "sat": 1.0,
		"motes": 0.6, "fireflies": 0.6, "clouds": 0.0, "mist": 1.0, "glints": 0.4},
}
const HOUR_FADE := 0.04
## The light the player carries after dark: its colour and radius (art px); its strength is the hour's `carry`.
const CARRY := Color(1.0, 0.94, 0.82)
const CARRY_RADIUS := 44.0
## Weather (a room with a `weather` region, CalendarRules): rain and storms close the sky in (less saturated, no sun
## in the grade, no motes, no cloud shade), fog veils it and thickens the mist.
const WEATHER := {
	"rain": {"sat": 0.9, "sun": 0.0, "mist": 1.2},
	"storm": {"sat": 0.85, "sun": 0.0, "mist": 1.2},
	"fog": {"sat": 0.92, "sun": 0.3, "mist": 2.0},
}

# ------------------------------------------------------------------ lights (night, dusk and lamp-lit rooms)
## A light's pool on the world: its colour, radius (art px) and the stepped bands of its falloff (fraction of the
## radius, strength), a 1 px checker between bands; `flame` is the small glow drawn over the night on a lamp. The pools
## are baked into one light map per room, so their number costs nothing a frame.
const LIGHT_KINDS := {
	"lantern": {"color": Color("ffc978"), "radius": 46, "bands": [[0.32, 0.95], [0.62, 0.62], [1.0, 0.3]], "flame": Color("fff1b8")},
	"lantern_red": {"color": Color("ffa46a"), "radius": 42, "bands": [[0.32, 0.9], [0.62, 0.58], [1.0, 0.28]], "flame": Color("ffd2a0")},
	"ember": {"color": Color("ff9d58"), "radius": 20, "bands": [[0.4, 0.6], [1.0, 0.28]], "flame": Color("ffc080")},
	"fire": {"color": Color("ffae62"), "radius": 54, "bands": [[0.3, 0.95], [0.6, 0.6], [1.0, 0.3]], "flame": Color("ffe0a0")},
	"door": {"color": Color("ffd08a"), "radius": 30, "bands": [[0.45, 0.7], [1.0, 0.34]]},
	"jade": {"color": Color("88e8c8"), "radius": 30, "bands": [[0.4, 0.62], [1.0, 0.28]], "flame": Color("c8fff0")},
	# T3: a star lantern's pale starlight (Lanternfall's, R8).
	"star": {"color": Color("d4e8ff"), "radius": 50, "bands": [[0.32, 1.0], [0.62, 0.7], [1.0, 0.36]], "flame": Color("f6faff")},
}
## Props that give light: the kind and where the flame sits in the sprite (px from its top-left).
const PROP_LIGHTS := {"lantern": ["lantern", 8, 12], "lantern_red": ["lantern_red", 12, 15], "incense": ["ember", 8, 9],
	# Decision 43's furnishings (tools/art/topdown/furnish.py): a stove's fire mouth, a forge's bed of coals.
	"stove": ["fire", 16, 25], "forge": ["fire", 13, 7],
	# T3: R8's star lantern, its starlight in the glass (tools/art/topdown/furnish.py `star_lantern`); R7's iron brazier
	# (the tomb's halls, the Hold) and R6's cook fire (the herders' camp), their flames (arid.py, furnish.py).
	"star_lantern": ["star", 11, 15], "brazier": ["fire", 8, 9], "cook_fire": ["fire", 16, 22],
	# T3: R9's (tools/art/topdown/starfield.py): the Wardens' post lamps and caged stars, the Ashborn pyres, the Lantern
	# Heart's wick pillars and flame basins.
	"warden_lamp": ["star", 8, 12], "lantern_cage": ["star", 16, 21], "ash_pyre": ["fire", 16, 22], "wick_pillar": ["fire", 8, 10],
	"flame_basin": ["fire", 16, 16]}
## Things of the room (by type, or by the prop they show) that give light, lifted this many art px over their spot.
const OBJECT_LIGHTS := {"cooking_pot": ["fire", 6], "alchemy_furnace": ["fire", 10], "forge_anvil": ["fire", 6], "shrine": ["ember", 12],
	"qi_spring": ["jade", 4], "teleport_stone": ["jade", 14], "lotus_lantern": ["lantern", 6]}
## Buildings with a door (the layout's door columns) spill a warm pool at their doorway after dark.
const DOOR_LIGHT := "door"

# ------------------------------------------------------------------ particles and cloud shade (few and cheap)
## Every particle on screen at once, all kinds together; each kind's own cap; Reduce motion halves them.
const MAX_PARTICLES := 48
## Each kind: its cap, life (s), colour and alpha (§14.2: at art resolution, never blurred, 1-2 px). Pollen motes drift
## in sunlight and fireflies blink at night (both SUN), leaves and petals fall from trees, mist wisps lie over water and
## marsh (MIST at 0.15-0.30), glints wink on sunlit water.
const PARTICLES := {
	"mote": {"cap": 14, "life": [5.0, 9.0], "color": SUN, "alpha": 0.85},
	"firefly": {"cap": 12, "life": [4.0, 8.0], "color": SUN, "alpha": 0.95},
	"leaf": {"cap": 8, "life": [4.0, 6.0], "alpha": 0.95},
	"mist": {"cap": 12, "life": [7.0, 12.0], "color": MIST, "alpha": 0.3},
	"glint": {"cap": 6, "life": [0.25, 0.45], "color": Color("eafff6"), "alpha": 0.9},
}
## What falls from which tree: willow and bamboo drop leaves, flowering shrubs petals, the Hollowing's dead trees ash.
const FALLS := {"willow": Color("9fcf6a"), "bamboo": Color("b4d86c"), "shrub": PETAL, "dead_tree": Color("a9adb0"),
	# The foliage kit's trees (§14.12): leaves from the green crowns, red leaves from the maple, petals from the blossom.
	"tree_camphor": Color("7fb85a"), "tree_ribbons": Color("7fb85a"), "tree_willow": Color("9fcf6a"),
	"bamboo_grove": Color("b4d86c"), "tree_maple": Color("d8642e"), "tree_plum": Color("f4d6e0"), "tree_peach": PETAL,
	"bush_azalea": PETAL}
## Cloud shade: a few big soft shapes gliding over everything by day (px per second), in the shade patches' tint and
## fainter than them (they move).
const CLOUDS_PER_SCREEN := 1.2
const CLOUD_ALPHA := 0.08
const CLOUD_DRIFT := Vector2(7.0, 3.5)
## Tests and the capture tool: a fixed hour of the clock (0..1 through the game's day); < 0 follows Clock.
static var debug_hour := -1.0

# ------------------------------------------------------------------ the look of a room at an hour
## The area a room belongs to (AREAS), from its definition: a night room is the story's night whatever its backdrop.
static func area_of(def: Dictionary) -> Dictionary:
	if bool(def.get("night", false)): return AREAS.valley_night
	if ROOM_AREAS.has(str(def.get("id", ""))): return AREAS[ROOM_AREAS[str(def.id)]]
	return AREAS.get(str(def.get("backdrop", "")), AREAS[""])

## How far through the game's day it is (0..1): the capture tool's and tests' fixed hour, or the clock's.
static func day_fraction() -> float:
	return debug_hour if debug_hour >= 0.0 else Clock.day_fraction()

## The look of a room now: {grade: {sun, shade, sat, hi}, ambient, lights, carry, shadows, motes, fireflies, clouds,
## mist, glints, hour}. Outdoors the clock's hour cross-fades into the next at each phase's end; weather (a room with a
## `weather` region) closes the sky in.
static func look(def: Dictionary, frac := -1.0, weather := "clear") -> Dictionary:
	var area := area_of(def)
	var hour := {}
	var name := ""
	if bool(area.get("clock", false)):
		var t := fposmod(day_fraction() if frac < 0.0 else frac, 1.0)
		var phases := ["morning", "day", "evening", "night"]
		var i := mini(3, int(t * 4.0))
		var into := t * 4.0 - i   # 0..1 through this phase
		hour = HOURS[phases[i]]
		name = phases[i]
		var k := smoothstep(1.0 - HOUR_FADE * 4.0, 1.0, into)
		if k > 0.0: hour = _mix_hour(hour, HOURS[phases[(i + 1) % 4]], k * 0.5)
		var back := 1.0 - smoothstep(0.0, HOUR_FADE * 4.0, into)
		if back > 0.0: hour = _mix_hour(hour, HOURS[phases[(i + 3) % 4]], back * 0.5)
	else:
		name = str(area.get("hour", "day"))
		hour = HOURS[name]
	var g: Dictionary = GRADES[str(area.grade)]
	var grade := {"sun": float(g.sun) * float(hour.grade), "shade": float(g.shade) * float(hour.grade),
		"sat": minf(1.05, float(g.sat) * float(hour.sat)), "hi": g.hi}
	var out := {"hour": name, "grade": grade, "ambient": hour.ambient, "lights": float(hour.lights), "carry": float(hour.carry),
		"shadows": float(hour.shadows), "motes": float(hour.motes) * float(area.motes), "fireflies": float(hour.fireflies),
		"clouds": float(hour.clouds), "mist": float(hour.mist) * float(area.mist), "glints": float(hour.glints)}
	if WEATHER.has(weather):
		var wx: Dictionary = WEATHER[weather]
		grade.sat = float(grade.sat) * float(wx.sat)
		grade.sun = float(grade.sun) * float(wx.sun)
		for k in ["motes", "clouds", "glints"]: out[k] = float(out[k]) * float(wx.sun)
		if weather != "fog": out.fireflies = 0.0
		out.mist = float(out.mist) * float(wx.mist)
	return out

static func _mix_hour(a: Dictionary, b: Dictionary, k: float) -> Dictionary:
	var out := {}
	for key in a:
		var va = a[key]
		out[key] = (va as Color).lerp(b[key], k) if va is Color else lerpf(float(va), float(b[key]), k)
	return out

## Is the grade the identity (nothing to draw)?
static func plain_grade(g: Dictionary) -> bool:
	return float(g.sun) <= 0.0005 and float(g.shade) <= 0.0005 and is_equal_approx(float(g.sat), 1.0)
