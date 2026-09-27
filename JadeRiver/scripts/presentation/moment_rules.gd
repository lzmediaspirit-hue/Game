class_name MomentRules
extends RefCounted
## The pure half of the moments system (docs/moments_design.md §3.4, §5): the matchers a row's `when` may use, the
## rare-drop rule, the text and colour sources of data/moments.json, and the closed lists data_validation checks the
## file against. Static and side-free: it reads data and the payload it is handed, and writes nothing.

## Matchers with a rule of their own; any other key of `when` tests the payload key of that name for equality.
const MATCHERS := ["actor", "target", "role_in", "first_in_room", "chapter_end", "rare", "source_in", "level_mod"]
## Every layer kind and where it plays: under or over the HUD (drawn by MomentView), through the HUD, or in the world.
const LAYER_KINDS := {"dim": "under", "vignette": "under", "flash": "under", "letterbox": "under",
	"band": "over", "strip": "over", "card": "over", "stats": "over", "chip": "over", "seal": "over", "stamps": "over", "subtitle": "over",
	"toast": "hud", "caption": "hud",
	"fx": "world", "text": "world", "shake": "world", "camera": "world", "sound": "world", "buzz": "world", "bark": "world",
	"fountain": "world", "beam": "world"}
const ANCHORS := ["actor", "enemy", "pet", "drop", "item", "camera"]
const SHAPES := ["strike", "wave", "ring", "rain", "pillar", "domain", "bolt"]
const STYLES := ["square", "ink", "ring", "ember", "shard"]

static var _tokens: Dictionary = {}

static func cfg() -> Dictionary:
	return ContentDB.config("moments")

## True when every matcher of `when` holds for payload `p`. `ctx`: `active` (the active character's id) and `seen`
## (the enemy uids already met in this room, for first_in_room).
static func matches(when: Dictionary, p: Dictionary, ctx: Dictionary) -> bool:
	for k in when:
		var want = when[k]
		var ok := true
		match str(k):
			"actor", "target": ok = str(p.get(k, "")) == str(ctx.get("active", ""))
			"role_in": ok = str(ContentDB.entry("enemies", str(p.get("def", p.get("enemy", "")))).get("role", "")) in want
			"first_in_room": ok = bool(want) != (ctx.get("seen", {}) as Dictionary).has(int(p.get("enemy", 0)))
			"chapter_end": ok = bool(want) == (cfg().get("chapter_ends", {}) as Dictionary).has(str(p.get("quest", "")))
			"rare": ok = bool(want) == (p.get("items", []) as Array).any(func(i): return is_rare(i))
			"source_in": ok = str(p.get("source", "")) in want
			"level_mod": ok = int(p.get("level", 0)) % maxi(1, int(want)) == 0
			_: ok = p.get(k) == want
		if not ok: return false
	return true

## A rare find (§3.4): a Perfect or Relic piece, a legend piece, a spirit animal's book, a treasure, or one of the named
## drops (a boss's unique drop, a first-defeat reward, a set piece, a legendary chain's piece). Coins never.
static func is_rare(i: Dictionary) -> bool:
	if int(i.get("coins", 0)) > 0: return false
	var r: Dictionary = cfg().get("rare", {})
	var id := str(i.get("item", ""))
	return str(i.get("quality", "")) in r.get("qualities", []) or str(ContentDB.item(id).get("type", "")) in r.get("types", []) \
		or (r.get("items", {}) as Dictionary).has(id)

## A reference inside a row: "payload.<key>", "slot.<slot>.<key>" (an absorbed event's payload), "item.<field>" (the
## payload item's data), or a plain value.
static func value(ref, p: Dictionary, slots := {}):
	if not (ref is String): return ref
	if ref.begins_with("payload."): return p.get(ref.trim_prefix("payload."), "")
	if ref.begins_with("slot."):
		var s = slots.get(ref.get_slice(".", 1), {})
		if s is Array: s = s[0] if not s.is_empty() else {}
		return (s as Dictionary).get(ref.get_slice(".", 2), "")
	if ref.begins_with("item."): return ContentDB.item(str(p.get("item", ""))).get(ref.trim_prefix("item."), "")
	return ref

## A text source (§3.4) as the words the player reads; "" when it names nothing.
static func text(src, p: Dictionary, slots := {}) -> String:
	if not (src is Dictionary): return str(value(src, p, slots))
	if src.is_empty(): return ""
	var v = value(src.values()[0], p, slots)
	if src.has("key"):
		var s := Tx.t(str(src.key) + (str(value(src.suffix, p, slots)) if src.has("suffix") else ""))
		var args: Array = (src.get("args", []) as Array).map(func(a): return text(a, p, slots) if a is Dictionary else value(a, p, slots))
		return s % args if not args.is_empty() else s
	if src.has("realm"): return ContentDB.realm_label(str(v))
	if src.has("realm_great"): return Tx.t("realm_great." + ProgressionRules.great_realm(str(v)))
	if src.has("transition"):
		return Tx.t("moment.transition") % [Tx.t("realm." + str(value(src.transition[0], p, slots))), Tx.t("realm." + str(value(src.transition[1], p, slots)))]
	if src.has("stage"): return str(int(ContentDB.realm(str(v)).get("sub", 0)))
	if src.has("name_of"): return ContentDB.name_of(str(src.name_of), str(value(src.id, p, slots)))
	if src.has("item"): return ContentDB.item_name(str(v))
	if src.has("craft"): return Tx.t("craft." + str(v))
	if src.has("boss"):
		var k := "boss.%s.%s" % [str(value(src.id, p, slots)), str(src.boss)]
		return Tx.t(k) if ContentDB.strings.has(k) else ""
	return str(v)   # {"payload": "payload.name"}: a value that is already player text

## A colour (§3.4, §6): a UiKit token name, or element:, grade: or quality: with an id or a reference.
static func color(spec, p := {}, slots := {}) -> Color:
	var s := str(spec)
	var id := str(value(s.get_slice(":", 1), p, slots))
	if s.begins_with("element:"): return SpriteCache.element_color(id)
	if s.begins_with("grade:"): return UiKit.grade_color(id)
	if s.begins_with("quality:"): return UiKit.quality_color(id)
	return tokens().get(s, UiKit.PAPER)

## One row of the escalation curve (§5.2), tier 1 to 7.
static func tier(n: int) -> Dictionary:
	var t: Array = cfg().get("vfx_tiers", [])
	return t[clampi(n, 1, t.size()) - 1] if not t.is_empty() else {}

## A shake's amplitude in px (§4.6): none with Screen shake off or Reduce motion on, else `amp`, or s × shake_amp_per_s.
static func shake_amp(s: float, amp := -1.0) -> float:
	var st: Dictionary = Game.account.settings
	if not st.get("screen_shake", true) or st.get("reduce_motion", false): return 0.0
	return amp if amp >= 0.0 else s * float(cfg().get("settings", {}).get("shake_amp_per_s", 16))

## A particle count under the settings: Reduce motion thins it to tier 1's sparks, Battery saver to tier 2's.
static func particle_count(n: int) -> int:
	var st: Dictionary = Game.account.settings
	if st.get("reduce_motion", false): return mini(n, int(tier(1).get("spark_count", n)))
	if st.get("battery_saver", false): return mini(n, int(tier(2).get("spark_count", n)))
	return n

## UiKit's colour tokens by name, the only colours a row may name.
static func tokens() -> Dictionary:
	if _tokens.is_empty():
		var consts: Dictionary = load("res://scripts/ui/ui_kit.gd").get_script_constant_map()
		for k in consts:
			if consts[k] is Color: _tokens[k] = consts[k]
	return _tokens
