# Composes a preview sheet of generated art: godot --headless --path . --script tests/art_preview.gd
extends SceneTree

func put(dst: Image, tex: Texture2D, x: int, y: int) -> void:
	var im := tex.get_image()
	dst.blend_rect(im, Rect2i(Vector2i.ZERO, im.get_size()), Vector2i(x, y))

func _init() -> void:
	var t0 := Time.get_ticks_msec()
	var out := Image.create(480, 420, false, Image.FORMAT_RGBA8)
	out.fill(Color("#223"))
	var bg := Backgrounds.build("town", 1500, 480)
	for L in bg.layers:
		put(out, L.tex, 0, 0)
	put(out, Backgrounds.floor_tex("town", 480), 0, 180)
	put(out, Backgrounds.rail("town", 480, [300]).tex, 0, 158)
	var pl := {"skin": "#f2cfa8", "hair": "plum_bob", "hairColor": "#6e2250", "main": "#1f6b5a", "trim": "#d8b35a", "under": "#e8e0cc", "sash": "#b8862e", "eyes": "#8a1a24"}
	var poses := ["idle", "run", "run", "run", "run", "attack", "attack", "jump", "dash", "guard", "hurt", "sit", "dead"]
	var fr := [0, 0, 1, 2, 3, 0, 1, 0, 0, 0, 0, 0, 0]
	for i in poses.size():
		put(out, Sprites.humanoid(pl, poses[i], fr[i]).tex, 4 + i * 36, 196)
	var looks := ["raider", "archer", "heavy", "captain", "acolyte", "qiu", "wen", "suyin", "tao", "merchant"]
	for i in looks.size():
		put(out, Sprites.humanoid(Sprites.LOOKS[looks[i]], "idle", 0, 1.4 if looks[i] in ["captain", "qiu"] else 1.0).tex, 4 + i * 46, 236)
	put(out, Sprites.beast("wolf", 0).tex, 10, 300); put(out, Sprites.beast("spirit_wolf", 1, "attack").tex, 60, 300); put(out, Sprites.sentinel(0).tex, 110, 300)
	var st := ["shrine", "forge", "furnace", "research", "chest", "shop", "board", "seal"]
	for i in st.size():
		put(out, Props.station(st[i]).tex, 190 + i * 36, 296)
	var nd := [["vein", "#c96b3c"], ["crystal", "#8fe8ff"], ["herb", null], ["lotus", null], ["ginseng", null], ["fish", null]]
	for i in nd.size():
		put(out, Props.node(nd[i][0], nd[i][1], true).tex, 190 + i * 34, 360)
	put(out, Props.portal(false).tex, 400, 330); put(out, Props.rune("fire", true).tex, 450, 370)
	var d := Props.deck(Content.AREAS.outskirts.surfaces[1], "outskirts")
	put(out, d.tex, 0, 70)
	var ids := ["sword", "spear", "hat", "gourd", "pick", "ore", "ingot", "herb", "lotus", "ginseng", "fish", "eel", "dust", "hide", "core", "crystal", "pill", "coin", "insight", "meridian", "lock", "map", "bag", "anvil", "cultivate", "gear", "shield", "jump", "step", "art", "nova", "dragon", "crescent", "thrust"]
	for i in ids.size():
		put(out, Icons.get_icon(ids[i], "#c96b3c" if ids[i] in ["ore", "ingot"] else null), 4 + (i % 14) * 34, 2 + (i / 14) * 34)
	out.save_png("/tmp/claude-0/gd_prev.png")
	print("art ok in %d ms" % (Time.get_ticks_msec() - t0))
	quit()
