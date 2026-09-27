extends Node
## Rules, replay and offline suites (Part 7 · Quality gates).
##   Rules:   each formula at its sample values (monster pools, damage steps, gap
##            factors, mastery, risk, offline caps).
##   Replay:  same seed plus same intents gives the same state.
##   Offline: caps, a backward clock, bottlenecks hold, no breakthrough while away.
##   Pets:    stage gates need all three conditions, branches, traits, resonance, hunger.
##   Weekly:  Sect Service ends on either path and survives the daily reset.
##   Saves:   a damaged file is restored from its .bak; the migration stamps the version.
##   Hazards: the answer a room asks, the cycle, strikes, pushes, pools and shelter (S17).
## Run headless:  godot --headless --path . res://tests/rules_tests.tscn

var checks := 0
var failures := 0

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func near(a: float, b: float, eps := 0.01) -> bool:
	return absf(a - b) <= eps * maxf(1.0, absf(b))

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	rules_suite()
	might_suite()
	replay_suite()
	offline_suite()
	pets_suite()
	weekly_suite()
	pills_suite()
	treasures_suite()
	hazards_suite()
	starsea_suite()
	movement_suite()
	g1_suite()
	g2_suite()
	traversal_suite()
	arts_volumes_suite()
	arts_combat_suite()
	nav_suite()
	paths_above_suite()
	forge_upkeep_suite()
	sword_loadout_suite()
	natal_wardrobe_suite()
	talisman_suite()
	herb_nature_suite()
	new_forms_suite()
	guild_suite()
	tribulation_suite()
	furnace_game_suite()
	expanse_herbs_suite()
	rooftop_routes_suite()
	ice_mount_suite()
	field_suite()
	hollow_tide_suite()
	post_suite()
	vigil_suite()
	station_suite()
	works_suite()
	guidance_suite()
	sphere_suite()
	ash_tide_suite()
	lantern_heart_suite()
	body_path_suite()
	heaven_suite()
	arts_suite()
	vows_suite()
	herbs_suite()
	garden_suite()
	herb_prep_suite()
	beasts_suite()
	bloodline_suite()
	pet_growth_suite()
	beast_world_suite()
	beast_arena_suite()
	relations_suite()
	bonds_suite()
	grudges_suite()
	calendar_suite()
	world_events_suite()
	fortune_suite()
	tower_activity_ranking_suite()
	mobile_conventions_suite()
	mortal_leisure_suite()
	territory_suite()
	depth_hooks_suite()
	v2_hooks_suite()
	weapon_families_suite()
	soul_poison_suite()
	blood_buddhist_suite()
	sect_roles_suite()
	swarm_array_puppet_suite()
	artifact_spirit_suite()
	awaken_legend_suite()
	aggro_cap_suite()
	emotes_suite()
	legacy_suite()
	drop_pool_suite()
	set_suite()
	boss_event_suite()
	moments_suite()
	tree_suite()
	tree_migration_suite()
	lost_arts_suite()
	tree_queries_suite()
	text_suite()
	ui_fixes_suite()
	icon_draw_suite()
	ui_style_suite()
	hud_suite()
	await labels_suite()
	await ui_suite()
	await identity_suite()
	await map_suite()
	fixes_suite()
	mockup_fixes_suite()
	max_character_suite()
	save_suite()
	print("rules_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ crowd cap on sight aggro
## Sight aggro stops at a crowd: with two ordinary foes on the player the rest hold back, and with an elite on the
## player every ordinary one does. A foe that is struck, an elite, or a summoned add always comes.
func aggro_cap_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for i in 3: Game.tick(0.05)   # the arrival (and its spawn protection) lands first
	for sid in ["stun", "slow", "spawn_protection"]: Game.combat.cure_status(c.id, sid)
	var engaged := func(list: Array) -> int:
		return list.filter(func(f): return str(f.ai.state) in ["aggro", "windup", "attack", "recover"]).size()
	var own := func(def_id: String, at: Vector2, elite := false) -> EnemyState:
		var f: EnemyState = Game.enemies.spawn_at(def_id, at, 2, {"elite": elite})
		f.summoned = false   # the room's own monsters, not a boss's adds
		return f
	for e0 in Game.room_rt.living_enemies(): e0.alive = false
	c.pools.hp = c.pools.max_hp
	var pack: Array = []
	for i in 4: pack.append(own.call("wild_boarlet", st.plane + Vector2(90 + i * 20, (i % 2) * 16)))
	for i in 6:
		Game.tick(0.05)
		c.pools.hp = c.pools.max_hp
	check(engaged.call(pack) == 2, "two ordinary foes come on sight; the others hold back (%d came)" % engaged.call(pack))
	var waiting: Array = pack.filter(func(f): return not str(f.ai.state) in ["aggro", "windup", "attack", "recover"])
	if not waiting.is_empty():
		waiting[0].threat[c.id] = 1.0   # struck
		for i in 4: Game.tick(0.05)
		check(str(waiting[0].ai.state) in ["aggro", "windup", "attack", "recover"], "a foe that is struck always joins (%s)" % str(waiting[0].ai.state))
	for e0 in Game.room_rt.living_enemies(): e0.alive = false
	var boss: EnemyState = own.call("wild_boarlet", st.plane + Vector2(80, 0), true)
	var near: Array = [own.call("wild_boarlet", st.plane + Vector2(120, 10)), own.call("wild_boarlet", st.plane + Vector2(-110, 0))]
	for i in 6:
		Game.tick(0.05)
		c.pools.hp = c.pools.max_hp
	check(str(boss.ai.state) != "idle" and engaged.call(near) == 0, "an elite on the player holds the ordinary foes back (%d came)" % engaged.call(near))
	var add: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(100, -10), 2)
	for i in 4: Game.tick(0.05)
	check(str(add.ai.state) in ["aggro", "windup", "attack", "recover"], "a summoned add joins the elite's fight")
	for e0 in Game.room_rt.living_enemies(): e0.alive = false

# ------------------------------------------------------------------ readable text
## The word fonts really are at their set weights (a "wght" string key is silently ignored and left Cormorant at
## its Light default), no word is set below the floor, and the text size setting scales every word and line.
## P4 (`docs/ui_style_guide.md`): on every page and tab, every tap target is at least 48 px on a side and no two
## buttons share a point, and no text is drawn under the minimum size.
## The P2 inventory's bugs add: pages that need a context open with a real one (an NPC's words, every shop, a fishing
## spot, every teleport stone known, a welcome with a post ledger), on a full character (every title and secret art,
## a Dao at every tier), and every view is also checked for buttons and words past the window (B4), words under a
## button (B16) and button labels wider than their button (B21).
func ui_suite() -> void:
	var main_script = load("res://scripts/main.gd")
	var force_was: bool = Unlocks.debug_force_all
	Unlocks.debug_force_all = true
	var c = Game.active()
	var keep := {"titles": c.cultivator.titles.duplicate(), "arts": c.cultivator.secret_arts.duplicate(), "daos": c.cultivator.daos.duplicate(true),
		"stones": Game.account.teleports.duplicate(), "inventory": c.inventory.snapshot()}
	# P5: a jian worn and another carried, and pills, so the Bag's card is drawn on each (restored at the end).
	Game.inventory.apply_add(c.id, "iron_jian", 2, "test")
	Game.inventory.apply_add(c.id, "healing_pill", 3, "test")
	Game.submit({"type": "equip", "index": c.inventory.first_index("iron_jian")})
	c.cultivator.titles = ContentDB.all("titles").map(func(e): return str(e.id))
	c.cultivator.secret_arts = ContentDB.all("secret_arts").map(func(e): return str(e.id))
	var dao_ids: Array = ContentDB.all("daos").map(func(e): return str(e.id))
	c.cultivator.daos = {}
	for tier in 7: c.cultivator.daos[dao_ids[tier]] = {"tier": tier, "insight": ProgressionRules.dao_next_need(tier - 1) if tier > 0 else 12.0}
	for s in ContentDB.all("teleport_stones"): Game.account.teleports[str(s.id)] = true
	var sect_was: Dictionary = Game.account.sect.duplicate(true)
	var ts_was: Dictionary = c.training_sect.duplicate(true)
	var seclusion_was: Dictionary = c.seclusion.duplicate(true)
	var contexts := _ui_contexts(c)
	var small: Array = []
	var overlaps: Array = []
	var outside: Array = []
	var under: Array = []
	var labels: Array = []
	var crossing: Array = []
	var cut: Array = []   # B18: views whose words were cut short; these now have the room to say everything
	var off_scale: Array = []   # P4: words asked for off the type scale or under UiKit.MIN_SIZE
	var windows: Array = []   # P4: windows off the standard set or outside the safe area
	var pitches: Array = []   # P4: list rows off the 8 px grid
	var whole := ["cultivation:body", "cultivation:vows", "beast_arena:-", "training_sect:role"]
	var blurred: Array = []   # P4b: icons drawn at a fractional scale of their art, or off the pixel grid
	var dim_words: Array = []   # P5: words on a page with its own surface that do not read on what they sit on
	var unshared: Array = []    # P5: a page with its own identity that lost a shared part (the close button, the inked title)
	var signatures := {}        # P5: layout signature -> the page that declared it
	var own_views := 0
	var fills := {}
	var icons_drawn := 0
	SpriteCache.draw_log = []
	var views := 0
	for id in main_script.PAGES:
		for a in contexts.get(str(id), [{}]):
			if a.has("_setup"): (a._setup as Callable).call()
			a = a.duplicate()
			a.erase("_setup")
			var pg: Page = load(str(main_script.PAGES[id])).new()
			pg.page_id = str(id)
			pg.text_log = []
			add_child(pg)
			pg.open(a)
			if str(id) == "dialogue":   # the last line, typed out: the choices show
				var dp = pg
				dp.line = maxi(0, dp.lines().size() - 1)
				dp.shown_chars = 9999.0
			for ti in maxi(1, pg.tabs.size()):
				if not pg.tabs.is_empty(): pg.tab = ti
				pg.text_log.clear()
				SpriteCache.draw_log.clear()
				pg.queue_redraw()
				await get_tree().process_frame
				await get_tree().process_frame
				views += 1
				var where := "%s%s:%s" % [id, "(%s)" % str(a.values()[0]).left(24) if not a.is_empty() else "", str(pg.tabs[ti].get("id", ti)) if not pg.tabs.is_empty() else "-"]
				for d in SpriteCache.draw_log:
					icons_drawn += 1
					var dr: Rect2 = d.rect
					if float(d.scale) < 1.0 or float(d.scale) != floorf(float(d.scale)) or dr.position != dr.position.round():
						blurred.append("%s %s %s at %.2fx" % [where, d.id, str(dr), float(d.scale)])
				# P4 (§2): a standard window inside the safe area, and list rows on the 8 px grid.
				if not pg.frameless and (not pg.frame_rect in Page.WINDOWS or not (Page.SAFE_AREA.encloses(pg.frame_rect) or pg.frame_rect == Page.WINDOW_SCREEN)): windows.append("%s %s" % [where, str(pg.frame_rect)])
				for aid in pg._areas:
					if fmod(float(pg._areas[aid].get("pitch", 0.0)), Page.GRID) != 0.0: pitches.append("%s %s at %s" % [where, aid, str(pg._areas[aid].pitch)])
				var inside := Rect2(Vector2.ZERO, Vector2(1280, 720)) if pg.frameless else pg.content
				var window := Rect2(Vector2.ZERO, Vector2(1280, 720)) if pg.frameless else pg.frame_rect
				var buttons: Array = []
				for r in pg._regions:
					if r.kind == "scroll": continue
					var full: Rect2 = r.get("full", r.rect)
					if full.size.x < Page.MIN_TAP or full.size.y < Page.MIN_TAP:
						small.append("%s %s %dx%d" % [where, r.id, int(full.size.x), int(full.size.y)])
					if r.kind == "button": buttons.append(r)
					if not window.grow(4).encloses(r.art): outside.append("%s %s at %s" % [where, r.id, str(r.art)])
				for i in buttons.size():
					for j in range(i + 1, buttons.size()):
						var both: Rect2 = (buttons[i].rect as Rect2).intersection(buttons[j].rect)
						if both.size.x > 0.5 and both.size.y > 0.5: overlaps.append("%s %s/%s" % [where, buttons[i].id, buttons[j].id])
				if pg.identity != null:
					own_views += 1
					_identity_view(pg, where, dim_words, unshared, signatures, fills)
				for tx in pg.text_log:
					if tx.has("ground") and not tx.get("panel", false): continue   # P5: a surface's ground, not a word
					if where in whole and str(tx.s).ends_with("…"): cut.append("%s \"%s\"" % [where, tx.s])
					if tx.has("size") and (int(tx.size) < UiKit.MIN_SIZE or not UiKit.on_scale(int(tx.size), bool(tx.display))):
						off_scale.append("%s \"%s\" at %d" % [where, str(tx.s).left(24), int(tx.size)])
					var tr: Rect2 = tx.rect
					if tx.get("panel", false):
						if not inside.grow(4).encloses(tr): outside.append("%s panel at %s" % [where, str(tr)])
						continue
					if tx.button != Rect2():
						if tr.size.x > (tx.button as Rect2).size.x - 6: labels.append("%s \"%s\" %d in %d" % [where, tx.s, int(tr.size.x), int(tx.button.size.x)])
						continue
					if not window.grow(4).encloses(tr): outside.append("%s \"%s\"" % [where, str(tx.s).left(30)])
					for b in buttons:
						var hit: Rect2 = tr.intersection(b.art)
						if hit.size.x > 3 and hit.size.y > 3 and not (b.art as Rect2).encloses(tr): under.append("%s \"%s\" under %s" % [where, str(tx.s).left(30), b.id])
					# Words that start in one card and run on into another, or over its edge (B17, B22).
					for pn in pg.text_log:
						if not pn.get("panel", false): continue
						var over: Rect2 = tr.intersection(pn.rect)
						if over.size.x > 3 and over.size.y > 3 and not (pn.rect as Rect2).grow(2).encloses(tr): crossing.append("%s \"%s\" over a card's edge" % [where, str(tx.s).left(30)])
			pg.queue_free()
	await get_tree().process_frame
	# B1: every Dao row, from Unaware to the top tier, draws its bar and its Contemplate button.
	var cp: Page = load(str(main_script.PAGES.cultivation)).new()
	add_child(cp)
	cp.open({"tab": "dao"})
	await get_tree().process_frame
	await get_tree().process_frame
	var rows: int = cp._regions.filter(func(r): return r.id == "contemplate").size()
	check(rows == mini(7, int((cp.content.size.y - 28.0) / 80.0)), "B1: every Dao row draws, up to the top tier (%d rows)" % rows)
	cp.queue_free()
	# B2: the Key Items tab offers the guqin's Play.
	var ip = load(str(main_script.PAGES.inventory)).new()
	add_child(ip)
	ip.open({"tab": "key"})
	for i in c.inventory.key_items.size():
		if str(c.inventory.key_items[i].id) == "guqin": ip.sel = {"key": i}
	await get_tree().process_frame
	await get_tree().process_frame
	check(ip._regions.any(func(r): return r.id == "use_key" and r.enabled), "B2: the guqin in the key-item pouch has a Play button")
	ip.queue_free()
	# B18: a paragraph cut short by its lines, and a line longer than its width, end with an ellipsis and keep to the width.
	var probe := GDScript.new()
	probe.source_code = "extends Page\nvar words := \"\"\nfunc draw_page() -> void:\n\tpara(Rect2(100, 100, 220, 400), words, 16, UiKit.PAPER, 2)\n" \
		+ "\ttext(Vector2(100, 400), words, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 220)\n\tpara(Rect2(100, 500, 220, 400), \"A short one.\", 16)\n"
	probe.reload()
	var pp = probe.new()
	pp.frameless = true
	pp.text_log = []
	pp.words = Tx.t("ui.cultivation.body_hint")
	add_child(pp)
	await get_tree().process_frame
	await get_tree().process_frame
	var said: Array = pp.text_log.map(func(tx): return str(tx.s))
	check(said.size() == 4 and not said[0].ends_with("…") and said[1].ends_with("…") and said[2].ends_with("…") and said[3] == "A short one."
		and pp.text_log.all(func(tx): return tx.rect.size.x <= 221.0), "B18: cut words end with an ellipsis inside their width (%s)" % str(said))
	pp.queue_free()
	# B15: the Menu names the same Level as the Cultivation badge (ProgressionRules.level), not the stage's first.
	var realm_was: String = c.cultivator.realm_key
	var qp_was: float = c.cultivator.qp
	c.cultivator.realm_key = "sphere_lord_3"
	c.cultivator.qp = c.cultivator.need() * 0.5
	var mp: Page = load(str(main_script.PAGES.menu)).new()
	mp.text_log = []
	add_child(mp)
	mp.open({})
	await get_tree().process_frame
	await get_tree().process_frame
	var want := ContentDB.realm_label("sphere_lord_3", ProgressionRules.level(c))
	check(mp.text_log.any(func(tx): return str(tx.s).ends_with(want)), "B15: the Menu says %s" % want)
	mp.queue_free()
	c.cultivator.realm_key = realm_was
	c.cultivator.qp = qp_was
	await get_tree().process_frame
	c.cultivator.titles = keep.titles
	c.cultivator.secret_arts = keep.arts
	c.cultivator.daos = keep.daos
	Game.account.teleports = keep.stones
	c.inventory.restore(keep.inventory)
	Game.combat.refresh_stats(c.id)
	Game.account.sect = sect_was
	c.training_sect = ts_was
	c.seclusion = seclusion_was
	Unlocks.debug_force_all = force_was
	SpriteCache.draw_log = null
	for o in overlaps + outside + under + labels + crossing + blurred + off_scale + windows + pitches: print("  ui_suite: ", o)
	check(icons_drawn > 1000 and blurred.is_empty(), "P4b: every icon on every page is drawn at a whole-number scale of its art, on whole pixels (%d drawn: %s)" % [icons_drawn, str(blurred.slice(0, 6))])
	check(views >= 200, "the ui_suite opened every page and tab, in every context (%d views)" % views)
	check(small.is_empty(), "every tap target is at least 48 px on a side (%s)" % str(small.slice(0, 6)))
	check(overlaps.is_empty(), "no two buttons share a point (%s)" % str(overlaps.slice(0, 6)))
	check(outside.is_empty(), "B4: no button or word runs past the window (%d: %s)" % [outside.size(), str(outside.slice(0, 8))])
	check(under.is_empty(), "B16: no words run under a button (%d: %s)" % [under.size(), str(under.slice(0, 8))])
	check(labels.is_empty(), "B21: every button label fits its button (%d: %s)" % [labels.size(), str(labels.slice(0, 8))])
	check(crossing.is_empty(), "B17, B22: no words run over the edge of a card (%d: %s)" % [crossing.size(), str(crossing.slice(0, 8))])
	check(cut.is_empty(), "B18: the Body hint and trials, the path cards, the arena help and the sect tree say all they have to (%s)" % str(cut))
	check(UiKit.size_for("text", 8) >= UiKit.size_for("text", UiKit.MIN_SIZE), "text asked for under the minimum size is drawn at the minimum")
	check(off_scale.is_empty(), "P4: every word on every page is asked for on the type scale, none under %d (%d: %s)" % [UiKit.MIN_SIZE, off_scale.size(), str(off_scale.slice(0, 8))])
	check(windows.is_empty(), "P4: every window is a standard one, inside the safe area (%s)" % str(windows.slice(0, 6)))
	check(pitches.is_empty(), "P4: every list's rows are on the 8 px grid (%s)" % str(pitches.slice(0, 6)))
	for o in dim_words + unshared: print("  ui_suite: ", o)
	check(dim_words.is_empty(), "P5: every word on a page with its own surface reads on what it sits on (%d: %s)" % [dim_words.size(), str(dim_words.slice(0, 6))])
	check(unshared.is_empty(), "P5: a page with its own identity keeps the shared close button, its inked title and a known surface (%s)" % str(unshared.slice(0, 6)))
	var own_pages := 0
	for id in main_script.PAGES:
		var p: Page = load(str(main_script.PAGES[id])).new()
		if p.identity != null: own_pages += 1
		p.free()
	check(signatures.size() == own_pages and (own_pages == 0 or own_views > own_pages), "P5: every page with its own identity was drawn, in every tab, with a layout signature no other shares (%d pages, %d views: %s)" % [own_pages, own_views, str(signatures)])

## The arguments the ui_suite opens a page with, when one needs a context: page id -> [args, ...].
func _ui_contexts(c) -> Dictionary:
	var talk := Game.submit({"type": "talk", "npc": "warden_commander_yao"})
	var convo: Dictionary = talk.get("dialogue", {})
	# A giver with three quests to offer: three Accepts and Not now, the most choices a conversation shows.
	var offers := convo.duplicate(true)
	offers.choices = []
	for q in ContentDB.all("quests").slice(0, 3): offers.choices.append({"text": Tx.t("sim.quest.accept") % str(q.get("name", q.id)), "accept": str(q.id)})
	offers.choices.append({"text": Tx.t("sim.quest.not_now"), "close": true})
	var items := {}
	for it in ContentDB.all("items").slice(0, 8): items[str(it.id)] = 12
	var welcome := {"gains": {"qp": 5200.0, "insight": 40.0, "coins": 380, "coin_currency": "silver_tael", "post": true}, "hours": 7.5, "capped": true,
		"post": {"kind": "post", "craft": "delving", "room": "wp_west", "hours": 7.5, "diligence": 0.6, "exp": 420.0, "level": 5, "level_before": 4,
			"items": items, "full": {"ore": 6.0}}}
	var ranks: Array = ContentDB.config("sect_ranks").get("order", [])
	# Your own sect, before founding and then founded with disciples, candidates and expeditions out (one back).
	var now := Clock.now_utc()
	var ds: Array = []
	for n in ["Wei", "Lan", "Qiu", "Hua", "Bo", "Mei"]: ds.append({"name": n, "level": 4, "trait": "green_thumb"})
	var ex: Array = ContentDB.all("expeditions").slice(0, 3).map(func(e): return {"region": str(e.id), "hours": 2, "disciples": [0], "done_utc": now + 3600.0})
	ex[0].done_utc = now - 60.0
	var sect := {"name": "Test", "emblem": [0, 0], "level": 3, "prestige": 120, "buildings": {"sect_hall": 1}, "queue": [], "disciples": ds,
		"candidates": ds.slice(0, 3).map(func(d): return {"name": d.name, "strength": 3, "spirit": 2, "craft": 4, "trait": "green_thumb"}),
		"expeditions": ex, "candidate_day": Clock.reset_day(now)}
	# P5 (decision 24): the Bag as it opens, and with its card open on the worn weapon, on a piece and on a pill in the bag.
	var bag: Array = [{}, {"tab": "weapon"}]
	for want in ["gear", "pills"]:
		for i in c.inventory.bag.size():
			if c.inventory.bag[i] != null and InventoryAuthority.bag_kind(str(c.inventory.bag[i].id)) == want:
				bag.append({"index": i})
				break
	return {"dialogue": [{"convo": convo}, {"convo": offers}], "revival": [{"actor": c.id}], "welcome": [welcome], "inventory": bag,
		"shop": ContentDB.all("shops").map(func(sh): return {"shop": str(sh.id)}), "fishing": [{"object": "fish_9"}], "teleport": [{}],
		"your_sect": [{"_setup": func(): Game.account.sect = {}}, {"_setup": func(): Game.account.sect = sect.duplicate(true)}],
		# An Elder of the Jade Sect: the next rank, Sect Master, is at the foot of the list (B5).
		"training_sect": [{"_setup": func(): c.training_sect.merge({"id": "jade_sect", "rank": str(ranks[maxi(0, ranks.size() - 2)])}, true)}],
		# In seclusion: the line that says so sits under the focus cards (B22).
		"seclusion": [{"_setup": func(): c.seclusion["focus"] = "accumulate"}],
		# The world map's three views (its tabs are the zones and the Heaven Ranking).
		"world_map": [{}, {"view": "resources"}, {"view": "objectives"}]}

## P5 (docs/page_identity.md §8): one view of a page with its own identity. Every word it draws in plain colour is
## measured on the ground it sits on: the last ground or panel drawn under its centre (Page.ground, Page.face, Page.panel),
## else the identity's surface; 4.5:1, or 3:1 from 20 px. Inked and outlined words and button labels are the kit's,
## measured by the ui_style_suite. The shared parts stay: the close button at the window's top right, the title inked on
## its mount, a surface from UiKit.SURFACE, a mount Page knows, an opening no longer than OPEN_MOTION_MAX, and a layout
## signature of its own.
func _identity_view(pg: Page, where: String, dim_words: Array, unshared: Array, signatures: Dictionary, fills: Dictionary) -> void:
	var idn: Page.Identity = pg.identity
	var sig_owner := str(signatures.get(idn.signature, pg.page_id))
	if sig_owner != pg.page_id: unshared.append("%s shares the signature %s with %s" % [where, idn.signature, sig_owner])
	signatures[idn.signature] = pg.page_id
	if not UiKit.SURFACE.has(idn.surface) or not idn.title_mount in ["plaque", "own"] or idn.open_s > Page.OPEN_MOTION_MAX or idn.signature == "":
		unshared.append("%s declares %s / %s / %.2f s / %s" % [where, idn.surface, idn.title_mount, idn.open_s, idn.signature])
	var close := Rect2(pg.frame_rect.end.x - 72, pg.frame_rect.position.y + 16, 52, 52)
	if not pg._regions.any(func(r): return r.id == "_close" and (r.art as Rect2) == close): unshared.append("%s has no close button at %s" % [where, str(close)])
	if pg.title != "" and not pg.text_log.any(func(tx): return str(tx.s) == pg.title and tx.get("outlined", false)): unshared.append("%s has no inked title" % where)
	var grounds: Array = []
	for tx in pg.text_log:
		if tx.has("ground"):
			grounds.append(tx)
			continue
		var col: Color = tx.get("col", Color.TRANSPARENT)
		if str(tx.s).strip_edges() == "" or col.a <= 0.0 or tx.get("outlined", false) or tx.get("button", Rect2()) != Rect2(): continue
		var at: Vector2 = (tx.rect as Rect2).get_center()
		var bg: Color = UiKit.SURFACE[idn.surface]
		var on := "surface " + idn.surface
		for i in range(grounds.size() - 1, -1, -1):
			if not (grounds[i].rect as Rect2).has_point(at): continue
			var gd = grounds[i].ground
			bg = gd if gd is Color else _fill_light(str(gd), fills)
			on = str(gd)
			break
		var need := 3.0 if int(tx.size) >= 20 else 4.5
		if _contrast(col, bg) < need: dim_words.append("%s \"%s\" on %s %.2f" % [where, str(tx.s).left(24), on, _contrast(col, bg)])

## P5 (docs/page_identity.md §8): the foundation, on a probe page that declares an identity. It draws its own surface in
## place of the shared window and keeps the shared parts (the close button at the window's top right, the title inked on
## its own mount, tabs in its own form with their 48 px targets); its words are measured on the ground they sit on, so a
## word too dim for its ground is caught. It opens by the reduced-motion rule (§6, docs/moments_design.md §4.6): its
## regions are live from the first frame, it moves over its opening (0.35 s at most) and a tap finishes it; under Reduce
## motion nothing moves and it only fades in, over 0.2 s. A page with no identity opens as it always did.
func identity_suite() -> void:
	var probe := GDScript.new()
	probe.source_code = "extends Page\nfunc _init() -> void:\n\ttitle = \"Probe\"\n\ttabs = [{\"id\": \"a\", \"label\": \"One\"}, {\"id\": \"b\", \"label\": \"Two\"}]\n" \
		+ "\tidentity = Identity.new(\"cloth\", false, \"own\", \"probe_signature\", 0.25)\n" \
		+ "func draw_page() -> void:\n\ttext(Vector2(300, 300), \"dim on cloth\", 14, UiKit.HOLLOW)\n\tground(Rect2(280, 380, 300, 60), UiKit.INK)\n" \
		+ "\ttext(Vector2(300, 420), \"clear on ink\", 14, UiKit.HOLLOW)\n\tbtn(Rect2(600, 400, 160, 56), \"Act\", \"act\", null, true)\n"
	probe.reload()
	var keep = Game.account.settings.get("reduce_motion", false)
	var got := {}
	for motion in [false, true]:
		Game.account.settings["reduce_motion"] = motion
		var pp: Page = probe.new()
		pp.text_log = []
		pp.page_id = "probe"
		add_child(pp)
		pp.open({})
		pp.opened = 0.0
		pp.queue_redraw()
		await get_tree().process_frame
		pp.opened = 0.0
		if not motion:
			var dim: Array = []
			var lost: Array = []
			_identity_view(pp, "probe", dim, lost, {}, {})
			check(dim.size() == 1 and str(dim[0]).contains("dim on cloth") and lost.is_empty(),
				"P5: a word too dim for the page's surface is caught, the same word on a ground it reads on is not (%s; %s)" % [str(dim), str(lost)])
			check(pp._regions.filter(func(r): return r.id == "_tab" and (r.rect as Rect2).size.y >= Page.MIN_TAP).size() == 2
				and pp.text_log.any(func(tx): return str(tx.s) == "Probe" and tx.get("outlined", false)),
				"P5: a page with its own identity keeps its tabs' targets and its title, inked on its own mount")
		got[motion] = {"unfold0": pp.unfold(), "alpha0": pp._open_alpha(), "live": pp._regions.filter(func(r): return r.id in ["_close", "_tab", "act"]).size()}
		pp.opened = 0.1
		got[motion]["unfold_mid"] = pp.unfold()
		pp.opened = 0.2
		got[motion]["alpha_02"] = pp._open_alpha()
		pp.opened = 0.0
		var press := InputEventMouseButton.new()
		press.button_index = MOUSE_BUTTON_LEFT
		press.pressed = true
		press.position = Vector2(4, 4)
		pp._gui_input(press)
		got[motion]["after_tap"] = pp.unfold()
		got[motion]["alpha_tap"] = pp._open_alpha()
		pp.queue_free()
	Game.account.settings["reduce_motion"] = keep
	var off: Dictionary = got[false]
	var on: Dictionary = got[true]
	check(int(off.live) == 4 and int(on.live) == 4, "P5: a page's regions are live from its first frame, in motion or not (%d, %d)" % [int(off.live), int(on.live)])
	check(float(off.unfold0) == 0.0 and float(off.unfold_mid) > 0.0 and float(off.unfold_mid) < 1.0 and float(off.after_tap) == 1.0 and float(off.alpha_tap) == 1.0,
		"P5: a page moves over its opening and a tap finishes it (%s)" % str(off))
	check(float(on.unfold0) == 1.0 and float(on.alpha0) == 0.0 and float(on.alpha_02) == 1.0, "P5: under Reduce motion nothing moves and the page fades in over 0.2 s (%s)" % str(on))
	var main_script = load("res://scripts/main.gd")
	var plain: Page = load(str(main_script.PAGES.menu)).new()
	add_child(plain)
	plain.open({})
	await get_tree().process_frame
	check(plain.identity == null and plain.unfold() == 1.0 and plain.modulate.a == 1.0, "P5: a page with no identity of its own opens as it did, at once")
	plain.queue_free()
	var slow: Array = []
	for id in main_script.PAGES:
		var p: Page = load(str(main_script.PAGES[id])).new()
		if p.identity != null and p.identity.open_s > Page.OPEN_MOTION_MAX: slow.append(id)
		p.free()
	check(slow.is_empty(), "P5: no page's opening runs past %.2f s (%s)" % [Page.OPEN_MOTION_MAX, str(slow)])
	await _bag_checks()
	await _post_checks()

## P5 (the Post family, docs/page_identity.md rows 12, 14, 23 and 44; mockups 13, 13_first and 14 v4; decisions 11, 21
## and 26). The Roll-Call hangs a tablet per character, soonest full first, each with its figure (the live Avatar at a
## whole 3 px an art px, clipped to its window), a Settle and a Switch under a character at a post, its vessel's tag
## reading what the pouch holds against what it can; a tap turns a tablet to its back, whose words read too. The Works
## cabinet's seven compartments are its tabs, each 48 px or more, each object drawn from its own drawing at its native 96
## on whole pixels, a locked one answering with what opens it, and the Seal Scripts show five rows at once. Welcome Back
## burns the coil to the time away out of the cap and lays every good in the tray. The Pouches chalk seven patterns, a
## deeper pouch larger.
func _post_checks() -> void:
	var c = Game.active()
	var main_script = load("res://scripts/main.gd")
	var force_was: bool = Unlocks.debug_force_all
	Unlocks.debug_force_all = true
	var open := func(id: String, a: Dictionary) -> Page:
		var pg: Page = load(str(main_script.PAGES[id])).new()
		pg.page_id = id
		pg.text_log = []
		add_child(pg)
		pg.open(a)
		return pg
	var dim: Array = []
	var lost: Array = []
	# The Roll-Call.
	var rc: Page = open.call("posts", {})
	await get_tree().process_frame
	await get_tree().process_frame
	var rs: Array = rc.rows()
	var shown: Array = rs.slice(0, rc.SHOWN)
	var tablets: Array = rc._regions.filter(func(r): return r.id == "turn")
	check(not rs.is_empty() and bool(rs[0].active) and tablets.size() == shown.size() and tablets.all(func(r): return (r.rect as Rect2).size.y >= Page.MIN_TAP),
		"P5 Roll-Call: a tablet per character on the rail, the one you play first (%d of %d)" % [tablets.size(), rs.size()])
	var keyed: Array = rs.slice(1).map(func(r): return 1e12 if (r.post as Dictionary).is_empty() else minf(1e11, float(r.fill_h)))
	check(range(keyed.size() - 1).all(func(i): return float(keyed[i]) <= float(keyed[i + 1])), "P5 Roll-Call: soonest full first (%s)" % str(keyed))
	var posted: Array = shown.filter(func(r): return not r.active and not (r.post as Dictionary).is_empty() and str(r.post.get("kind", "")) != "vigil")
	check(posted.all(func(r): return rc._regions.any(func(g): return g.id == "settle" and str(g.data) == str(r.id) and (g.rect as Rect2).size.y >= Page.MIN_TAP)
		and rc._regions.any(func(g): return g.id == "switch" and int(g.data) == int(r.slot))), "P5 Roll-Call: a Settle and a Switch under each character at a post")
	var said: Array = rc.text_log.map(func(tx): return str(tx.get("s", "")))
	check(posted.all(func(r): return said.has(UiKit.fmt(int(r.pouch))) and float(r.cap) > 0.0), "P5 Roll-Call: each vessel's tag says what its pouch holds")
	var figs: Array = rc.figs.values()
	check(figs.size() == shown.size() and figs.all(func(f): return (f.mask as CanvasItem).clip_children == CanvasItem.CLIP_CHILDREN_ONLY
		and (f.doll as Node2D).scale == Vector2(1.5, 1.5) and (f.doll as Node2D).global_position == (f.doll as Node2D).global_position.round()),
		"P5 Roll-Call: each tablet shows its character's live figure at 3 px an art px on whole pixels, clipped to its window")
	_identity_view(rc, "posts board", dim, lost, {}, {})
	rc.on_action("turn", str(rs[0].id))
	rc.opened = 9.0
	rc.t += 1.0
	rc.text_log.clear()
	rc.queue_redraw()
	await get_tree().process_frame
	check(bool(rc.turned.get(str(rs[0].id), false)) and rc.text_log.any(func(tx): return str(tx.get("s", "")) == str(rs[0].name) and tx.get("col") == UiKit.PALE_GOLD)
		and not (rc.figs[str(rs[0].id)].mask as Node2D).visible, "P5 Roll-Call: a tap turns a tablet to its back, the figure put away")
	_identity_view(rc, "posts back", dim, lost, {}, {})
	rc.queue_free()
	# Works: the curio cabinet.
	SpriteCache.draw_log = []
	var wk: Page = open.call("works", {"tab": "seals"})
	await get_tree().process_frame
	await get_tree().process_frame
	var cells: Array = wk._regions.filter(func(r): return r.id == "_tab")
	var objects: Array = SpriteCache.draw_log.filter(func(d): return str(d.id).begins_with("work_"))
	check(cells.size() == 7 and cells.all(func(r): return (r.rect as Rect2).size.x >= Page.MIN_TAP and (r.rect as Rect2).size.y >= Page.MIN_TAP),
		"P5 Works: the seven works are the cabinet's seven compartments, each a 48 px target")
	check(objects.size() == 7 and objects.all(func(d): return int(d.art) == 96 and float(d.scale) == 1.0 and (d.rect as Rect2).position == (d.rect as Rect2).position.round()),
		"P5 Works: each object is drawn from its own drawing at its native 96, on whole pixels (%s)" % str(objects.map(func(d): return [d.id, d.art, d.scale])))
	var seals: Dictionary = wk._areas.get("seals", {})
	check(not seals.is_empty() and int(((seals.rect as Rect2).size.y + Page.ROW_GAP) / float(seals.pitch)) >= 5, "P5 Works: the Seal Scripts show five rows at once (decision 26)")
	_identity_view(wk, "works seals", dim, lost, {}, {})
	Unlocks.debug_force_all = false
	wk.setup()
	var closed_cells: Array = wk.tabs.filter(func(tb): return str(tb.get("locked", "")) != "")
	wk.queue_redraw()
	await get_tree().process_frame
	check(closed_cells.all(func(tb): return wk._regions.any(func(r): return r.id == "_tab" and not r.enabled and str(r.reason) == str(tb.locked) and str(r.reason) != "")),
		"P5 Works: a work not yet open answers a tap with what opens it (%d closed)" % closed_cells.size())
	Unlocks.debug_force_all = true
	wk.queue_free()
	SpriteCache.draw_log = null
	# Welcome Back: the coil and the tray.
	var ctx: Dictionary = _ui_contexts(c).welcome[0]
	var wb: Page = open.call("welcome", ctx)
	await get_tree().process_frame
	await get_tree().process_frame
	var cap := float(ContentDB.curve("idle_cap_h", 12)) + float(Game.sect.idle_cap_bonus())
	var goods: Array = wb.ledger().goods
	check(is_equal_approx(wb.burnt(), clampf(float(ctx.hours) / cap, 0.0, 1.0)) and goods.size() == (ctx.post.items as Dictionary).size()
		and wb._regions.filter(func(r): return r.id == "item").size() == mini(goods.size(), 19) and wb._regions.any(func(r): return r.id == "store") and wb._regions.any(func(r): return r.id == "ok"),
		"P5 Welcome Back: the coil burnt to the time away out of the cap (%.2f), every good in the tray, the two choices under it" % wb.burnt())
	_identity_view(wb, "welcome", dim, lost, {}, {})
	wb.queue_free()
	# The Pouches: the chalk patterns.
	var pp: Page = open.call("pouches", {})
	await get_tree().process_frame
	await get_tree().process_frame
	var tiers: int = (ContentDB.config("posts").get("sewing", []) as Array).size()
	var sews: int = pp._regions.filter(func(r): return r.id == "sew" and (r.rect as Rect2).size.y >= Page.MIN_TAP).size()
	var finest: int = pp.CATS.filter(func(k): return int(Game.posts.pouch(c, k).get("tier", 0)) >= tiers).size()
	check(sews + finest == 7 and range(tiers).all(func(i): return pp.size_of(i + 1, tiers) > pp.size_of(i, tiers)),
		"P5 Pouches: seven patterns chalked, each with its Sew, a deeper pouch larger")
	_identity_view(pp, "pouches", dim, lost, {}, {})
	pp.queue_free()
	check(dim.is_empty() and lost.is_empty(), "P5 Post family: every word reads on what it sits on (%s; %s)" % [str(dim.slice(0, 6)), str(lost.slice(0, 3))])
	Unlocks.debug_force_all = force_was
	await get_tree().process_frame

## P5 (the Bag as concept B, decision 24; docs/page_identity.md row 3): the kinds split the bag with nothing lost; the
## eight worn slots ride the orbit; a tapped thing's card opens beside its space, clear of it and inside the window, its
## actions 48 px, its words read on the card; a piece's card shows what the rules say wearing it would do
## (StatRules.equip_change: it leaves the character untouched, its "before" is the character as it stands and its
## "after" what equipping the piece really gives); "···" brings Lock and Discard; a pill's card offers Use and Quick-use.
func _bag_checks() -> void:
	var c = Game.active()
	var keep: Dictionary = c.inventory.snapshot()
	var force_was: bool = Unlocks.debug_force_all
	Unlocks.debug_force_all = true
	Game.inventory.apply_add(c.id, "iron_jian", 1, "test")
	Game.inventory.apply_add(c.id, "healing_pill", 3, "test")
	Game.combat.refresh_stats(c.id)
	var wi: int = c.inventory.first_index("iron_jian")
	var pi: int = c.inventory.first_index("healing_pill")
	var stat_ids: Array = ContentDB.stat_const("stats", []).map(func(s): return str(s.id))
	var was: Array = stat_ids.map(func(s): return c.stats.value(s))
	var max_hp: float = c.pools.max_hp
	var rows: Array = StatRules.equip_change(c, "weapon", c.inventory.bag[wi])
	check(stat_ids.map(func(s): return c.stats.value(s)) == was and c.pools.max_hp == max_hp and c.inventory.bag[wi] != null,
		"P5 Bag: working out what a piece would change leaves the character untouched")
	check(rows.size() > 1 and str(rows[-1].stat) == "combat_power" and is_equal_approx(float(rows[-1].before), StatRules.combat_power(c))
		and rows.slice(0, -1).all(func(r): return is_equal_approx(float(r.before), c.stats.value(str(r.stat)))),
		"P5 Bag: the card's 'before' is the character as it stands (%d stats change)" % (rows.size() - 1))
	var CharacterPage = load("res://scripts/ui/pages/character_page.gd")
	var pg: Page = load(str(load("res://scripts/main.gd").PAGES.inventory)).new()
	pg.text_log = []
	pg.page_id = "inventory"
	add_child(pg)
	pg.open({"index": wi})
	await get_tree().process_frame
	await get_tree().process_frame
	var kinds: Array = ["gear", "pills", "materials", "other"].map(func(k): return pg._kind_count(c.inventory, k))
	check(kinds.reduce(func(a, b): return a + b, 0) == pg._kind_count(c.inventory, "all") and int(kinds[0]) >= 1 and int(kinds[1]) >= 1,
		"P5 Bag: the kinds split the bag with nothing lost (%s)" % str(kinds))
	check(pg._regions.filter(func(r): return r.id == "slot").size() == 8, "P5 Bag: the eight worn slots ride the orbit round the figure")
	var card: Array = pg._regions.filter(func(r): return r.id == "_card")
	var cell: Array = pg._regions.filter(func(r): return r.id == "bag" and int(r.data) == wi)
	check(card.size() == 1 and cell.size() == 1 and not (card[0].rect as Rect2).intersects(cell[0].rect) and pg.frame_rect.encloses(card[0].rect),
		"P5 Bag: a tapped piece's card opens beside its space, clear of it and inside the window")
	var acts: Array = pg._regions.filter(func(r): return r.id in ["equip", "spare", "more"])
	check(acts.size() == 3 and acts.all(func(r): return (r.rect as Rect2).size.x >= Page.MIN_TAP and (r.rect as Rect2).size.y >= Page.MIN_TAP),
		"P5 Bag: the piece's card offers Equip, Set as spare and '···', each 48 px or more")
	var said: Array = pg.text_log.map(func(tx): return str(tx.get("s", "")))
	var shown: Array = rows.filter(func(r): return pg._stat_key(str(r.stat)) != "" and str(r.stat) != "combat_power").slice(0, 3) + [rows[-1]]
	check(shown.all(func(r): return said.has(CharacterPage.stat_text(str(r.stat), float(r.after)))),
		"P5 Bag: the card shows the totals StatRules.equip_change gives (%s)" % str(shown.map(func(r): return CharacterPage.stat_text(str(r.stat), float(r.after)))))
	var dim: Array = []
	var lost: Array = []
	_identity_view(pg, "inventory card", dim, lost, {}, {})
	pg.more = true
	pg.text_log.clear()
	pg.queue_redraw()
	await get_tree().process_frame
	check(pg._regions.any(func(r): return r.id == "lock") and pg._regions.any(func(r): return r.id == "discard"), "P5 Bag: '···' brings Lock and Discard")
	_identity_view(pg, "inventory more", dim, lost, {}, {})
	pg.on_action("bag", pi)
	pg.text_log.clear()
	pg.queue_redraw()
	await get_tree().process_frame
	check(pg._regions.any(func(r): return r.id == "use" and r.enabled) and pg._regions.any(func(r): return r.id == "quick") and not pg.more,
		"P5 Bag: a pill's card offers Use and Quick-use, the '···' actions folded again")
	_identity_view(pg, "inventory pill", dim, lost, {}, {})
	check(dim.is_empty() and lost.is_empty(), "P5 Bag: every word on its cards reads on what it sits on (%s)" % str(dim.slice(0, 4)))
	pg.queue_free()
	var after: Array = rows.slice(0, -1).map(func(r): return float(r.after))
	var cp_after := float(rows[-1].after)
	Game.submit({"type": "equip", "index": wi})
	Game.combat.refresh_stats(c.id)
	var real: Array = rows.slice(0, -1).map(func(r): return c.stats.value(str(r.stat)))
	var near := func(a: float, b: float) -> bool: return absf(a - b) <= maxf(0.001, absf(b) * 0.0001)
	check(str(c.inventory.equipped.weapon.id) == "iron_jian" and range(real.size()).all(func(i): return near.call(real[i], after[i])) and near.call(StatRules.combat_power(c), cp_after),
		"P5 Bag: equipping the piece gives what its card said (Combat Power %d, said %d)" % [StatRules.combat_power(c), int(cp_after)])
	c.inventory.restore(keep)
	Game.combat.refresh_stats(c.id)
	Unlocks.debug_force_all = force_was

## P5 (docs/page_identity.md row 7, mockups 16 and 16_resources, decisions 17 and 25): the world map as the framed
## painting. The valley's nodes stand where tools/ui/build_valley_map.py painted each area, and every room of every
## zone shows at an area of its zone. The one layout pass leaves no plate or mark touching another, a node or the
## frame's furniture, and every word on the painting sits on a plate: on the real data, in every zone, view, kind and
## chosen area, with every area known and with few, at every text size; in the valley no plate is left out. Track Route
## and Walk there travel by auto_path and close the map; a locked zone's tag says why.
func map_suite() -> void:
	var map_script = load("res://scripts/ui/pages/map_page.gd")
	var vz: Dictionary = map_script._zone("jade_river_valley")
	var off: Array = []
	for r in ContentDB.zone("jade_river_valley").regions:
		if r.get("hidden", false): continue
		# build_valley_map.py MAP_RECT (24, 34, 424, 276) art px, drawn x2.
		var want := Vector2(48, 68) + Vector2(float(r.map[0]) * 848.0, float(r.map[1]) * 552.0)
		if (vz.anchor[str(r.id)] as Vector2).distance_to(want) > 0.5 or not ResourceLoader.exists("res://art/ui/maps/valley_%s.png" % r.id): off.append(str(r.id))
	var art := load("res://art/ui/maps/valley_map.png") as Texture2D
	check(art != null and art.get_size() == Vector2(1280, 640) and off.is_empty(), "P5 map: the valley's nodes stand where its painting drew each area, each with its picture (%s)" % str(off))
	var lost: Array = []
	for id in ContentDB.rooms:
		var zz: Dictionary = map_script._zone(str(ContentDB.room_zone.get(id, "")))
		if not str(zz.node_of.get(str(id), "")) in zz.order: lost.append(str(id))
	check(lost.is_empty(), "P5 map: every room of every zone shows at an area of its zone (%d lost: %s)" % [lost.size(), str(lost.slice(0, 6))])
	# The pass on a crowd round one point: what fits is placed clear of the rest, what does not is left out.
	var crowd: Array = []
	for i in 30: crowd.append({"id": i, "at": Vector2(400, 300) + Vector2(i % 3, i / 3) * 3.0, "r": 12.0, "sizes": [Vector2(120, 40), Vector2(90, 20)], "ways": map_script.PLATE_WAYS})
	var pin := Rect2(386, 286, 40, 60)
	var got: Dictionary = map_script.place(crowd, [pin], Rect2(200, 150, 420, 320))
	var boxes: Array = got.values().map(func(g): return g.rect)
	check(got.size() >= 4 and got.size() < 30 and _map_faults(boxes, [pin], [], Rect2(200, 150, 420, 320)).is_empty(),
		"P5 map: the layout pass places a crowd round one point with none touching and leaves out what fits nowhere (%d of 30)" % got.size())
	# The real views.
	var c = Game.active()
	var visited_was: Dictionary = Game.account.visited_rooms.duplicate()
	var size_was = Game.account.settings.get("text_size", 1)
	var force_was: bool = Unlocks.debug_force_all
	Unlocks.debug_force_all = true
	var pg: Page = map_script.new()
	pg.page_id = "world_map"
	pg.text_log = []
	add_child(pg)
	pg.open({})
	var faults: Array = []
	var left_out: Array = []
	var views := 0
	for known in ["all", "few"]:
		Game.account.visited_rooms = {}
		for id in ContentDB.rooms:
			var zz: Dictionary = map_script._zone(str(ContentDB.room_zone.get(id, "")))
			if known == "all" or zz.node_of.get(id, "") == zz.order[0]: Game.account.visited_rooms[id] = true
		for ts in 3:
			Game.account.settings["text_size"] = ts
			for ti in pg.tabs.size() - 1:
				pg.tab = ti
				pg._sync_tab()
				for v in ["areas", "resources", "objectives"]:
					for k in (["herb_patch", "ore_vein", "fishing_spot"] if v == "resources" else [""]):
						for pick in [0, 1]:
							var zz: Dictionary = map_script._zone(str(pg.tabs[ti].id))
							pg.view = v
							if k != "": pg.res_kind = k
							pg.res_item = ""
							pg.sel = str(zz.order[(zz.order.size() / 2) * pick])
							pg.text_log.clear()
							pg.queue_redraw()
							await get_tree().process_frame
							await get_tree().process_frame
							views += 1
							var where := "%s/%s/%s%s/%d/%s" % [known, pg.tabs[ti].id, v, k, ts, pg.sel]
							var L: Dictionary = pg.layout
							var rects: Array = L.plates.values().map(func(p): return p.rect) + L.marks.values().map(func(p): return p.rect)
							for f in _map_faults(rects, L.pins, L.keep, L.bounds): faults.append("%s %s" % [where, f])
							for tx in pg.text_log:
								var at: Vector2 = (tx.rect as Rect2).get_center()
								if tx.has("ground") or not (L.bounds as Rect2).has_point(at) or at.x >= 912.0 or L.keep.any(func(k): return k.has_point(at)): continue
								if not L.plates.values().any(func(p): return (p.rect as Rect2).grow(1).encloses(tx.rect)): faults.append("%s \"%s\" off its plate" % [where, str(tx.s)])
							if str(pg.tabs[ti].id) == "jade_river_valley" and not L.hidden.is_empty(): left_out.append("%s %s" % [where, str(L.hidden)])
	for f in faults.slice(0, 12): print("  map_suite: ", f)
	check(views >= 180 and faults.is_empty(), "P5 map: no plate or mark touches another, a node or the frame's furniture, and every word on the painting is on its plate, in every zone, view and text size (%d views, %d faults)" % [views, faults.size()])
	check(left_out.is_empty(), "P5 map: in the valley every plate finds a place (%s)" % str(left_out.slice(0, 4)))
	Game.account.visited_rooms = visited_was
	Game.account.settings["text_size"] = size_was
	# Travel: from the Willow Path, Track Route walks to Stoneford's nearest room by auto_path and closes the map.
	var room_was := str(c.position.get("room", ""))
	Game.world.load_room(c, "wp_west", "")
	GameEvents.flush()
	pg.tab = 0
	pg.view = "areas"
	pg._sync_tab()
	await get_tree().process_frame
	pg.on_action("sel", "stoneford")
	pg.queue_redraw()
	await get_tree().process_frame
	await get_tree().process_frame
	var closed := [0]
	pg.closed.connect(func(_p): closed[0] += 1)
	var track: Array = pg._regions.filter(func(r): return r.id == "track")
	var to := str(track[0].data) if not track.is_empty() else ""
	if not track.is_empty(): pg._activate(track[0])
	check(track.size() == 1 and to in vz.rooms.stoneford and Game.world.auto_path_target(c) == to and closed[0] == 1,
		"P5 map: Track Route walks to Stoneford (%s) by auto_path and closes the map" % to)
	Game.submit({"type": "auto_path", "target": ""})
	# Walk there: a tracked quest's room from its area's card (with no tracked quest on a route, the intent it sends).
	var walk_to := "sf_market"
	for tq in Game.quest.tracker(c):
		var qn := str(vz.node_of.get(str(tq.target_room), ""))
		if walk_to == "sf_market" and qn != "" and str(tq.target_room) != "wp_west" and not pg._route(c, qn, str(tq.target_room)).is_empty(): walk_to = str(tq.target_room)
	var walk: Array = []
	if walk_to != "sf_market":
		pg.on_action("sel", str(vz.node_of[walk_to]))
		pg.queue_redraw()
		await get_tree().process_frame
		await get_tree().process_frame
		walk = pg._regions.filter(func(r): return r.id == "walk")
		if not walk.is_empty(): pg._activate(walk[0])
	else:
		pg.on_action("walk", walk_to)
	check((walk_to == "sf_market" or walk.size() == 1) and Game.world.auto_path_target(c) == walk_to and closed[0] == 2,
		"P5 map: Walk there walks to the tracked quest's room (%s) by auto_path and closes the map" % walk_to)
	Game.submit({"type": "auto_path", "target": ""})
	# A locked zone's tag answers a tap with its reason and leaves the map where it was.
	var locked: Array = pg._regions.filter(func(r): return r.id == "_tab" and not r.enabled)
	var zone_was: String = pg.zone_id
	if not locked.is_empty(): pg._activate(locked[0])
	check(locked.is_empty() or (pg.toast == str(pg.tabs[int(locked[0].data)].locked) and pg.zone_id == zone_was), "P5 map: a locked zone's tag says why (%s)" % pg.toast)
	pg.queue_free()
	if room_was != "": Game.world.load_room(c, room_was, "")
	Unlocks.debug_force_all = force_was
	await get_tree().process_frame

## What is wrong with a layout: a box outside `bounds`, over a keep-out, on a pin, or touching another box.
func _map_faults(boxes: Array, pins: Array, keep: Array, bounds: Rect2) -> Array:
	var out: Array = []
	for i in boxes.size():
		var a: Rect2 = boxes[i]
		if not bounds.encloses(a): out.append("%s outside" % str(a))
		out.append_array(keep.filter(func(k): return a.intersects(k)).map(func(k): return "%s over %s" % [str(a), str(k)]))
		out.append_array(pins.filter(func(p): return a.grow(1).intersects(p)).map(func(p): return "%s on the node at %s" % [str(a), str(p.get_center())]))
		out.append_array(boxes.slice(i + 1).filter(func(b): return a.grow(1).intersects(b)).map(func(b): return "%s touches %s" % [str(a), str(b)]))
	return out

## P4 (docs/ui_style_guide.md §11): the style guide applied, checked on the sources. Colours are UiKit tokens (§1): no
## page, the HUD or Page itself carries a colour literal, only `Color(UiKit.X, alpha)` or a white modulate, and every
## grade has its colour.
func ui_style_suite() -> void:
	var sources: Array = ["res://scripts/hud.gd", "res://scripts/ui/page.gd"]
	for f in DirAccess.get_files_at("res://scripts/ui/pages/"):
		if f.ends_with(".gd"): sources.append("res://scripts/ui/pages/" + f)
	var hex := RegEx.create_from_string("Color\\(\\s*\"#?[0-9a-fA-F]{6,8}\"")
	var flt := RegEx.create_from_string("Color\\(\\s*-?[0-9.]+\\s*,\\s*-?[0-9.]+")
	var white := RegEx.create_from_string("^Color\\(\\s*1(\\.0)?\\s*,\\s*1(\\.0)?\\s*,\\s*1(\\.0)?\\s*[,)]")
	var literals: Array = []
	for path in sources:
		var lines := FileAccess.get_file_as_string(path).split("\n")
		for i in lines.size():
			var ln := lines[i]
			if ln.strip_edges().begins_with("#"): continue
			for m in hex.search_all(ln): literals.append("%s:%d %s" % [path.get_file(), i + 1, m.get_string()])
			for m in flt.search_all(ln):
				if white.search(ln.substr(m.get_start())) == null: literals.append("%s:%d %s" % [path.get_file(), i + 1, m.get_string()])
	check(literals.is_empty(), "P4: no page, the HUD or Page draws an off-token colour (%d: %s)" % [literals.size(), str(literals.slice(0, 6))])
	# States (§6): the pressed art is only the finger's. A page draws "pressed" where the press is read (_is_pressed), or on
	# the hot controls the furnace holds while a finger is down (`held`).
	var pressed_else: Array = []
	for path in sources:
		var plines := FileAccess.get_file_as_string(path).split("\n")
		for i in plines.size():
			if plines[i].contains("\"pressed\"") and not plines[i].contains("_is_pressed(") and not plines[i].contains("if held") and not plines[i].contains("state == \"pressed\"") and path.get_file() != "hud.gd":
				pressed_else.append("%s:%d" % [path.get_file(), i + 1])
	check(pressed_else.is_empty(), "P4: no page draws the pressed state but under the finger (%s)" % str(pressed_else))
	var g: Dictionary = ContentDB.config("grades")
	var bare: Array = (g.get("order", []) as Array).filter(func(k): return not (g.get("grade_colors", {}) as Dictionary).has(k))
	check(bare.is_empty(), "P4: every grade has its colour (%s)" % str(bare))
	# Type (§3): the HUD's words are asked for on the scale and never under UiKit.MIN_SIZE (the pages are checked as they
	# draw, in the ui_suite).
	var call := RegEx.create_from_string("UiKit\\.(draw_text|draw_outlined|draw_inked)\\(self")
	var size_arg := RegEx.create_from_string(",\\s*(\\d+),\\s*(UiKit\\.|Color\\(|lc\\b|col\\b|ring_col\\b|$)")
	var hud_lines := FileAccess.get_file_as_string("res://scripts/hud.gd").split("\n")
	var hud_calls := 0
	var hud_off: Array = []
	for i in hud_lines.size():
		if call.search(hud_lines[i]) == null: continue
		hud_calls += 1
		var sm := size_arg.search(hud_lines[i])
		var sz := int(sm.get_string(1)) if sm != null else -1
		var display := hud_lines[i].contains(", true, true)")
		if sm == null or sz < UiKit.MIN_SIZE or not UiKit.on_scale(sz, display): hud_off.append("hud.gd:%d at %d" % [i + 1, sz])
	check(hud_calls >= 40 and hud_off.is_empty(), "P4: every word on the HUD is asked for on the type scale, none under %d (%d calls: %s)" % [UiKit.MIN_SIZE, hud_calls, str(hud_off)])
	# Contrast (§1.4, decision 10): every text colour on every fill UiKit.TEXT_ON lists, measured on the HD kit's own art:
	# the lightest texel (95th percentile) inside the fill's nine-slice centre, over INK. Inked words are measured on INK.
	var fills := {}
	var low: Array = []
	var pairs := 0
	var tokens: Dictionary = (load("res://scripts/ui/ui_kit.gd") as GDScript).get_script_constant_map()
	var rows: Array = UiKit.TEXT_ON.duplicate()
	var g2: Dictionary = ContentDB.config("grades")
	for kind in ["grade_colors", "quality_colors"]:
		for k in g2.get(kind, {}): rows.append([Color(str(g2[kind][k])), ["@page"], 14, "%s %s" % [kind, k]])
	for row in rows:
		var col: Color = row[0] if row[0] is Color else tokens[str(row[0])]
		for f in row[1]:
			for fill in (["major_window", "minor_panel", "slot", "toast", "currency_pill"] if f == "@page" else [f]):
				var inked: bool = str(fill).ends_with("@ink")
				var bg: Color = UiKit.INK if inked else _fill_light(str(fill), fills)
				var need := 3.0 if int(row[2]) >= 20 else 4.5
				var r := _contrast(col, bg)
				pairs += 1
				if r < need: low.append("%s on %s %.2f < %.1f" % [row[3] if row.size() > 3 else row[0], fill, r, need])
	check(pairs > 80 and low.is_empty(), "P4: every text colour reads on every fill it is drawn on (%d pairs: %s)" % [pairs, str(low.slice(0, 6))])
	# Words over the world: plates at PLATE's alpha keep MIST at 4.5:1 over a white sky, and the HUD log is outlined.
	var over_white := Color(UiKit.PLATE.r * UiKit.PLATE.a + (1.0 - UiKit.PLATE.a), UiKit.PLATE.g * UiKit.PLATE.a + (1.0 - UiKit.PLATE.a), UiKit.PLATE.b * UiKit.PLATE.a + (1.0 - UiKit.PLATE.a))
	var hud_src := FileAccess.get_file_as_string("res://scripts/hud.gd")
	var log_fn := hud_src.substr(hud_src.find("func _draw_log()"), 600)
	check(_contrast(UiKit.MIST, over_white) >= 4.5 and log_fn.contains("UiKit.draw_outlined(") and not log_fn.contains("UiKit.draw_text("),
		"P4: plates over the world keep MIST at 4.5:1 over white (%.2f), and the HUD log is outlined" % _contrast(UiKit.MIST, over_white))


## WCAG 2 contrast of two opaque colours.
func _contrast(a: Color, b: Color) -> float:
	var la := _lum(a)
	var lb := _lum(b)
	return (maxf(la, lb) + 0.05) / (minf(la, lb) + 0.05)

func _lum(c: Color) -> float:
	var ch := func(v: float) -> float: return v / 12.92 if v <= 0.04045 else pow((v + 0.055) / 1.055, 2.4)
	return 0.2126 * ch.call(c.r) + 0.7152 * ch.call(c.g) + 0.0722 * ch.call(c.b)

## The lightest texel (95th percentile of luminance) a fill shows under text, composited over INK: the HD kit's art
## inside its nine-slice centre (the title plaque, which has none, from a fifth to seven tenths of its height; the
## minimap's header band for "minimap_frame:header"). A derived state (UiKit.DERIVED_TINT) is its normal art tinted
## over the window's mean, as UiKit draws it. The same sampling as tools/dev/ui_style_audit.py.
func _fill_light(spec: String, cache: Dictionary) -> Color:
	spec = spec.trim_suffix("@ink")
	if cache.has(spec): return cache[spec][0]
	if spec.begins_with("surface:"): return UiKit.SURFACE[spec.trim_prefix("surface:")]   # P5: a page's own flat material
	var asset := spec.get_slice(":", 0)
	var state := spec.get_slice(":", 1) if spec.contains(":") else "normal"
	var kit: Dictionary = ContentDB.config("ui_assets_hd")
	var e: Dictionary = kit.get(asset, {})
	var derived: bool = UiKit.DERIVED_TINT.has(state) and not e.has(state)
	var img: Image = (load(str(e.get("normal" if derived or state == "header" else state, ""))) as Texture2D).get_image()
	if img.is_compressed(): img.decompress()
	var k := int(kit.get("scale", 3))
	var m: Array = e.get("margins", [8, 8, 8, 8])
	var w := img.get_width()
	var h := img.get_height()
	var x0 := int(m[0]) * k
	var x1 := w - int(m[2]) * k
	var y0 := int(m[1]) * k
	var y1 := h - int(m[3]) * k
	if state == "header":
		x0 = 24 * k
		x1 = w - 24 * k
		y0 = 4 * k
		y1 = 20 * k
	if y1 <= y0:
		y0 = int(h * 0.2)
		y1 = int(h * 0.7)
	if x1 <= x0:
		x0 = w / 2 - 1
		x1 = w / 2 + 1
	var step := maxi(1, int(sqrt(float((x1 - x0) * (y1 - y0)) / 4000.0)))
	var seen: Array = []
	var total := Color(0, 0, 0)
	for y in range(y0, y1, step):
		for x in range(x0, x1, step):
			var px := img.get_pixel(x, y)
			var c := Color(UiKit.INK.r + (px.r - UiKit.INK.r) * px.a, UiKit.INK.g + (px.g - UiKit.INK.g) * px.a, UiKit.INK.b + (px.b - UiKit.INK.b) * px.a)
			seen.append([_lum(c), c])
			total += c
	var mean := total / float(seen.size())
	seen.sort_custom(func(p, q): return p[0] < q[0])
	var light: Color = seen[int(seen.size() * 0.95)][1]
	if derived:
		var tint: Color = UiKit.DERIVED_TINT[state]
		if not cache.has("major_window"): _fill_light("major_window", cache)
		var win: Color = cache["major_window"][1]
		light = Color(light.r * tint.r * tint.a + win.r * (1.0 - tint.a), light.g * tint.g * tint.a + win.g * (1.0 - tint.a), light.b * tint.b * tint.a + win.b * (1.0 - tint.a))
	cache[spec] = [light, mean]
	return light

## P4 (docs/ui_style_guide.md §7) and P5a (§9, mockups 01 and 02): the HUD's touch targets and its layout. In a fight
## and at rest, with the fan open or closed, every round control's hit circle is at least 48 across and at least its
## drawn radius + 4, and where two circles overlap a tap goes to the nearer centre; a tracker line's go button is
## 48 x 48; the player panel's whole height opens Character. The right-hand cluster stands where the mockups put it;
## no control or panel sits in the lower middle the mockups keep clear round the player at the common camera
## positions; the fan opens and closes, folds in a fight, and shows its toggles that are on while closed (decision 20);
## the techniques fold into beads at rest; an empty or locked slot is not drawn (review G3).
func hud_suite() -> void:
	var c = Game.active()
	if c == null: return
	var hud = load("res://scripts/hud.gd").new()
	add_child(hud)   # with no player bound every element shows, so every control is in the table
	var draught_was = c.inventory.draught
	var soul_was: float = c.pools.max_soul
	c.inventory.draught = {"id": "healing_pill", "count": 1}
	c.pools.max_soul = maxf(1.0, soul_was)
	# Each state: [in a fight, the fan open].
	var states := {"fight": [true, false], "fight, the fan open": [true, true], "rest, the fan open": [false, true], "rest, the fan closed": [false, false]}
	var small: Array = []
	var roles := {}
	var wrong: Array = []
	var overlaps := 0
	var in_zone: Array = []
	var zone: Rect2 = hud.CLEAR_ZONE
	var tables := {}
	for sname in states:
		hud.set_state(states[sname][0], states[sname][1])
		var targets: Array = hud.hit_targets()
		tables[sname] = targets
		for tg in targets:
			roles[str(tg.role)] = true
			if float(tg.r) < 24.0 or float(tg.r) < float(tg.drawn) + 4.0: small.append("%s: %s r%d" % [sname, tg.role, int(tg.r)])
			var d := float(tg.drawn)
			if not states[sname][1] and Rect2(tg.center - Vector2(d, d), Vector2(d, d) * 2.0).intersects(zone): in_zone.append("%s: %s" % [sname, tg.role])
		for x in range(360, 1280, 6):
			for y in range(0, 720, 6):
				var p := Vector2(x, y)
				var inside: Array = targets.filter(func(tg): return p.distance_to(tg.center) < float(tg.r))
				if inside.is_empty(): continue
				if inside.size() > 1: overlaps += 1
				inside.sort_custom(func(a, b): return p.distance_to(a.center) < p.distance_to(b.center))
				var got: String = hud.role_at(p)
				if got != str(inside[0].role) and wrong.size() < 6: wrong.append("%s: %s at %s (%s)" % [sname, got, str(p), inside[0].role])
	check(small.is_empty(), "P4: every HUD control's hit circle is 48 across and its drawn radius + 4, in every state (%s)" % str(small))
	var want := ["attack", "jump", "guard", "skill", "page", "fan", "meditate", "presence", "sphere", "sense", "pet", "quick", "draught", "treasure:0", "treasure:1", "swap", "icon:mail"]
	check(want.all(func(r): return roles.has(r)) and roles.size() >= 21, "P4, P5a: the tables hold every control of the cluster (%d roles; missing %s)" % [roles.size(), str(want.filter(func(r): return not roles.has(r)))])
	check(overlaps > 0 and wrong.is_empty(), "P4: where HUD circles overlap, a tap goes to the nearest centre (%d points in overlaps; %s)" % [overlaps, str(wrong)])
	var go: Rect2 = hud.go_hit(Rect2(300, 100, 48, 48))
	check(go.size == Vector2(48, 48) and go.encloses(Rect2(300, 100, 48, 48)), "P4: the tracker's go button is a 48 x 48 target")
	check(hud.panel_rect(c).size.y == 120.0 and hud.role_at(Vector2(100, 128)) == "portrait", "P4: the Soul row is part of the player panel's target")
	# The cluster where mockups 01 and 02 draw it (right-handed): ring 1 at R 132 round the attack button, the fan and ring 2
	# at R 214, the open fan's toggles at R 150 round the fan, the page tab.
	var at := func(role: String, table: Array) -> Array: return table.filter(func(tg): return str(tg.role) == role).map(func(tg): return tg.center)
	var fight: Array = tables["fight"]
	var near := func(a: Vector2, b: Vector2) -> bool: return a.distance_to(b) <= 1.5
	var ring1: Array = at.call("skill", fight)
	var mock1 := [Vector2(1033, 605), Vector2(1051, 539), Vector2(1099, 491), Vector2(1165, 473)]
	var placed := ring1.size() == 4 and range(4).all(func(i): return near.call(ring1[i], mock1[i]))
	placed = placed and near.call(at.call("attack", fight)[0], Vector2(1165, 605)) and near.call(at.call("jump", fight)[0], Vector2(1051, 671))
	placed = placed and near.call(at.call("guard", fight)[0], Vector2(1231, 491)) and near.call(at.call("fan", fight)[0], Vector2(964, 678))
	placed = placed and near.call(at.call("page", fight)[0], Vector2(1240, 672))
	check(placed, "P5a: ring 1, the fan and the page tab stand where mockup 01 draws them (%s)" % str(ring1))
	var r2: Array = hud.ring2_places([{"role": "presence", "home": "pin"}, {"role": "quick", "home": "quick"}, {"role": "treasure:0", "home": "treasure:0"}])
	check(near.call(r2[0].center, Vector2(951, 612)) and near.call(r2[1].center, Vector2(970, 518)) and near.call(r2[2].center, Vector2(1016, 451)),
		"P5a: ring 2 as mockup 01: the held Presence pinned beside the fan, the healing slot, the treasure (%s)" % str(r2.map(func(o): return o.center)))
	var open_fan: Array = ["meditate", "presence", "sphere", "sense", "pet"].map(func(r): return at.call(r, tables["rest, the fan open"])[0])
	var mock2 := [Vector2(814, 678), Vector2(825, 622), Vector2(856, 574), Vector2(903, 541), Vector2(959, 528)]
	check(range(5).all(func(i): return near.call(open_fan[i], mock2[i])), "P5a: the open fan's five toggles stand where mockup 02 draws them (%s)" % str(open_fan))
	# Ring 2 holds more than its six places without two rings touching, and stays on the screen.
	var many: Array = hud.ring2_places(["presence", "sphere", "quick", "draught", "treasure:0", "treasure:1", "context", "swap"].map(func(r): return {"role": r, "home": r}))
	var apart := true
	for i in many.size() - 1: apart = apart and (many[i].center as Vector2).distance_to(many[i + 1].center) >= 60.0
	check(apart and many.all(func(o): return o.center.x + 26.0 <= 1280.0 and o.center.y - 26.0 >= 0.0), "P5a: eight things on ring 2 keep 60 px apart, on the screen")
	# Rest and fight: the techniques, the healing slot and the treasures are out only in a fight; the fan folds in a fight
	# and pins what is on beside it, and opens at rest.
	var rest_roles: Array = tables["rest, the fan closed"].map(func(tg): return str(tg.role))
	var fight_roles: Array = fight.map(func(tg): return str(tg.role))
	check(not rest_roles.has("skill") and not rest_roles.has("quick") and not rest_roles.has("treasure:0") and not rest_roles.has("page")
		and fight_roles.count("skill") == 4 and fight_roles.has("quick"), "P5a: at rest the techniques fold into beads and the healing slot and treasures rest; in a fight they are out")
	var pinned: Array = at.call("presence", tables["rest, the fan closed"])
	check(pinned.size() == 1 and near.call(pinned[0], Vector2(951, 612)) and not rest_roles.has("meditate")
		and near.call(at.call("presence", tables["rest, the fan open"])[0], Vector2(825, 622)), "P5a: closed, the fan shows its toggle that is on pinned beside it; open, the toggle stands in the fan (decision 20)")
	hud.set_state(false, false)
	hud.press(7, hud.fan_center)
	hud.release(7)
	var opened: bool = hud.fan_open and hud.fan_rest_open
	hud.press(7, hud.fan_center)
	hud.release(7)
	var closed: bool = not hud.fan_open and not hud.fan_rest_open
	hud.set_state(true, true)
	hud.press(7, hud.presence_center)
	hud.release(7)
	check(opened and closed and not hud.fan_open, "P5a: a tap opens the fan and a tap closes it, the choice kept at rest; in a fight a toggle taken from it folds it")
	hud.set_state(false, true)
	hud.fan_rest_open = true
	hud.fight_override = true
	hud._tick_fight(0.1)
	var folded: bool = hud.fight and not hud.fan_open and hud.fight_k < 1.0
	hud.fight_override = false
	hud._tick_fight(hud.FIGHT_HOLD_S + 0.1)
	check(folded and not hud.fight and hud.fan_open, "P5a: a foe near folds the fan and brings the ring out; with none near it opens again as it was left")
	# Nothing in the lower middle round the player (the clear zone), in a fight or at rest with the fan closed; the open
	# fan at rest keeps off the player at the common camera positions (x 640 give or take the look-ahead, feet at 470 to
	# 640); the panels, the tracker's plate, the log and the top centre's toasts keep out of the zone too.
	check(in_zone.is_empty(), "P5a: no HUD control stands in the clear zone %s in a fight or at rest (%s)" % [str(zone), str(in_zone)])
	var bodies: Array = []
	for px in [560.0, 640.0, 720.0]:
		for feet in [470.0, 560.0, 640.0]: bodies.append(Rect2(px - 30.0, feet - 130.0, 60.0, 140.0))
	var on_player: Array = tables["rest, the fan open"].filter(func(tg): return bodies.any(func(b): return (b as Rect2).intersects(Rect2(tg.center - Vector2(tg.drawn, tg.drawn), Vector2(tg.drawn, tg.drawn) * 2.0))))
	check(on_player.is_empty(), "P5a: the open fan keeps off the player at the common camera positions (%s)" % str(on_player.map(func(tg): return tg.role)))
	var panels := [hud.panel_rect(c), hud.minimap_rect, Rect2(14, 0, 342, hud.TRACKER_FOOT), Rect2(20, 0, hud.LOG_W, hud.LOG_FOOT), Rect2(400, 92, 480, 84), Rect2(1040, 222, 222, 34)]
	check(panels.all(func(r): return not (r as Rect2).intersects(zone)), "P5a: the panel, the minimap, the tracker, the log, the boss bar and the purse keep out of the clear zone")
	# The left-handed option mirrors the cluster, and it still keeps out of the clear zone.
	hud.left_handed = true
	hud._layout()
	hud.set_state(true, false)
	var mirrored: Array = hud.hit_targets()
	var lh_zone: Array = mirrored.filter(func(tg): return Rect2(tg.center - Vector2(tg.drawn, tg.drawn), Vector2(tg.drawn, tg.drawn) * 2.0).intersects(zone))
	check(hud.attack_center == Vector2(115, 605) and hud.jump_center == Vector2(229, 671) and hud.fan_center == Vector2(316, 678)
		and hud.page_center == Vector2(40, 672) and lh_zone.is_empty() and hud.role_at(Vector2(900, 400)) == "joystick",
		"P5a: left-handed, the cluster is mirrored, the joystick takes the right half and the clear zone stays clear (%s)" % str(lh_zone.map(func(tg): return tg.role)))
	hud.left_handed = false
	hud._layout()
	var toasts_was: Array = hud.toasts
	hud.toasts = []
	for i in 3: hud.toast("probe", "gold", "a second line")
	var from_top: Array = hud.toast_rects(hud.TOP_STACK)
	var from_boss: Array = hud.toast_rects(hud.TOP_STACK_BOSS)
	check(from_top.size() == 2 and from_boss.size() == 1 and (from_top + from_boss).all(func(r): return (r as Rect2).end.y <= zone.position.y and (r as Rect2).size.x == 408.0),
		"P5a: toasts stand at the top centre, 408 wide, and stop above the clear zone; the rest wait (%d, %d)" % [from_top.size(), from_boss.size()])
	hud.toasts = toasts_was
	# Bound to the character: an empty or locked technique slot, an empty healing slot or treasure and a swap with no
	# spare are not drawn (G3); the techniques that are there keep their places.
	var stub_src := GDScript.new()
	stub_src.source_code = "extends Node2D\nvar actor_id := \"\"\nvar plane := Vector2.ZERO\nvar facing := 1\nvar altitude := 0.0\n"
	stub_src.reload()
	var stub = stub_src.new()
	stub.actor_id = str(Game.active_id)
	hud.player = stub
	hud.visible = false
	var force_was: bool = Unlocks.debug_force_all
	Unlocks.debug_force_all = true
	var slots_was: Array = c.cultivator.technique_slots.duplicate()
	var quick_was: String = c.inventory.quick_use
	var tre_was: Array = c.inventory.treasures.duplicate()
	var spare_was = c.inventory.loadout.get("spare")
	var n: int = ProgressionRules.technique_slot_count(c)
	var techs: Array = ContentDB.all("techniques").slice(0, 2).map(func(tq): return str(tq.id))
	c.cultivator.technique_slots = [techs[0], null, techs[1], ""] + [null, null, null, null]
	c.inventory.quick_use = ""
	c.inventory.treasures = ["", ""]
	c.inventory.loadout["spare"] = null
	c.inventory.draught = null
	hud.set_state(true, false)
	var bound_t: Array = hud.hit_targets()
	var expect: Array = [0, 2].filter(func(i): return i < n)
	var skills: Array = at.call("skill", bound_t)
	check(hud.bound() and skills.size() == expect.size() and range(expect.size()).all(func(k): return near.call(skills[k], mock1[expect[k]]))
		and not bound_t.any(func(tg): return str(tg.role) in ["quick", "treasure:0", "treasure:1", "swap", "draught"]),
		"G3: an empty or locked slot is not drawn; the techniques there keep their places (%d of %d slots open, %d drawn)" % [expect.size(), n, skills.size()])
	c.cultivator.technique_slots = slots_was
	c.inventory.quick_use = quick_was
	c.inventory.treasures = tre_was
	c.inventory.loadout["spare"] = spare_was
	Unlocks.debug_force_all = force_was
	hud.player = null
	stub.free()
	c.inventory.draught = draught_was
	c.pools.max_soul = soul_was
	hud.queue_free()

## P5a (review G4): world names never stack. WorldLabels.resolve places a crowd of labels in whole rows so no two
## touch and none sits under a HUD control; a plate under the feet with no room below goes over the head; labels
## that touch nothing keep their places; a second pass with last frame's rows gives the same places. Then the real
## views: two NPCs on the same spot (Elder Gu and Madam Hua in Artisan Row), three foes and a boss in a knot, and the
## party (a disciple, the puppet and an animal) at one height in a fight, laid out by WorldLabels.place_views as
## world.gd does each frame.
func labels_suite() -> void:
	var mk := func(id: String, kind: String, r: Rect2, flip: Vector2) -> Dictionary:
		return {"id": id, "kind": kind, "rect": r, "prev": Vector2.ZERO, "near": 0.0, "flip": flip}
	var no := Vector2.ZERO
	var items: Array = [
		mk.call("companion", "ally", Rect2(600, 500, 44, 9), no), mk.call("puppet", "ally", Rect2(604, 502, 44, 9), no), mk.call("pet", "ally", Rect2(606, 501, 34, 9), no),
		mk.call("boss", "boss", Rect2(700, 420, 150, 22), no), mk.call("foe", "foe", Rect2(720, 432, 190, 22), no),
		mk.call("npc1", "npc", Rect2(300, 600, 120, 42), Vector2(0, -250)), mk.call("npc2", "npc", Rect2(360, 600, 120, 42), Vector2(0, -250)),
		mk.call("npc3", "npc", Rect2(420, 600, 120, 42), Vector2(0, -250)), mk.call("alone", "foe", Rect2(100, 300, 120, 22), no)]
	var offs: Dictionary = WorldLabels.resolve(items, [])
	# Every offset is whole rows of its own box, from its place or from its place over the head.
	var whole := func(it: Dictionary) -> bool:
		var step: float = (it.rect as Rect2).size.y + WorldLabels.ROW_GAP
		var y: float = offs[it.id].y
		return absf(y / step - roundf(y / step)) < 0.01 or absf((y - float(it.flip.y)) / step - roundf((y - float(it.flip.y)) / step)) < 0.01
	check(WorldLabels.touching(items, offs).is_empty() and items.all(whole) and offs["alone"] == Vector2.ZERO,
		"G4: a crowd of labels (the party at one height, a boss over a foe, plates side by side) is laid out in rows with none touching (%s)" % str(WorldLabels.touching(items, offs)))
	for it in items: it.prev = offs[it.id]
	check(WorldLabels.resolve(items, []) == offs, "G4: with last frame's rows the layout holds still")
	var under := [mk.call("foe", "foe", Rect2(1000, 460, 160, 22), no)]
	var control := Rect2(1070, 440, 60, 60)   # a ring of the HUD's cluster
	var o2: Dictionary = WorldLabels.resolve(under, [control])
	check(not Rect2(under[0].rect.position + o2["foe"], under[0].rect.size).intersects(control) and o2["foe"].y < 0.0, "G4: a label under a HUD control moves up clear of it")
	var plate := [mk.call("npc", "npc", Rect2(760, 600, 130, 42), Vector2(0, -180))]
	var o3: Dictionary = WorldLabels.resolve(plate, [Rect2(700, 590, 300, 130)])
	check(o3["npc"] == Vector2(0, -180), "G4: a plate under the feet with no room below goes over the head (%s)" % str(o3["npc"]))
	# The real views in the room, laid out as world.gd lays them out.
	var c = Game.active()
	if c == null or Game.room_rt == null or Game.actor_state(c.id) == null: return
	var holder := Node2D.new()
	add_child(holder)
	var fight_was := WorldLabels.party_fight
	WorldLabels.party_fight = true
	var base: Vector2 = Game.actor_state(c.id).plane
	var foes: Array = []
	var views: Array = []
	for i in 3: foes.append(Game.enemies.spawn_at("wild_boarlet", base + Vector2(160 + i * 18, 4 * i), 5))
	var boss_def := ""
	for e0 in ContentDB.all("enemies"):
		if not (e0.get("phases", []) as Array).is_empty():
			boss_def = str(e0.id)
			break
	var boss_e: EnemyState = Game.enemies.spawn_at(boss_def, base + Vector2(190, -6), 5)
	if boss_e != null and not boss_e.is_boss(): boss_e.role = "story_boss"   # as its arena's spawn makes it
	foes.append(boss_e)
	foes[0].elite = true
	for i in 3:
		var a := EnemyState.new()
		a.uid = Game.room_rt.uid()
		a.def_id = "probe_ally_%d" % i
		a.def = {"name": "Probe", "art": {"creature": "wild_boarlet"} if i > 0 else {"avatar": "player"}, "half_width": 14, "height": 60 if i > 0 else 88, "ally": true}
		a.team = "ally"
		a.plane = base + Vector2(-80 + i * 6, 0)
		a.pools.max_hp = 100.0
		a.pools.hp = 70.0
		Game.room_rt.enemies[a.uid] = a
		foes.append(a)
	for e in foes:
		if e == null: continue
		var v := EnemyView.new()
		v.setup(e)
		v.set_process(false)
		holder.add_child(v)
		views.append({"id": "e%d" % e.uid, "view": v, "kind": v.label_kind, "near": absf(e.plane.x - base.x)})
	for i in 2:
		var nv := NpcView.new()
		nv.setup({"id": "probe_npc_%d" % i, "npc": ["elder_gu", "madam_hua"][i], "at": [base.x - 200.0, base.y]})
		nv.set_process(false)
		holder.add_child(nv)
		views.append({"id": "n%d" % i, "view": nv, "kind": "npc", "near": 200.0})
	await get_tree().process_frame
	await get_tree().process_frame
	var xf := Transform2D(0.0, Vector2(640.0 - base.x, 560.0 - base.y))
	var laid: Dictionary = WorldLabels.place_views(views, xf, [])
	var drawn: int = laid.items.size()
	var kinds := {}
	for it in laid.items: kinds[str(it.kind)] = true
	check(drawn == views.size() and kinds.has("ally") and kinds.has("boss") and kinds.has("foe") and kinds.has("npc") and WorldLabels.touching(laid.items, laid.offsets).is_empty(),
		"G4: the real labels (%d of %d: foes, a boss, the party's HP lines, two NPCs on one spot) are placed with none touching (%s; %s)" % [drawn, views.size(),
		str(WorldLabels.touching(laid.items, laid.offsets)), str(views.filter(func(v): return not laid.offsets.has(v.id)).map(func(v): return "%s %s %s" % [v.id, v.kind, str(v.view.label_box)]))])
	WorldLabels.party_fight = false
	for v in views: v.view.tag.queue_redraw()
	await get_tree().process_frame
	await get_tree().process_frame
	var calm: Dictionary = WorldLabels.place_views(views, xf, [])
	check(not calm.items.any(func(it): return str(it.kind) == "ally"), "G4: out of a fight the party shows no label (their names are on the HUD's chips)")
	WorldLabels.party_fight = fight_was
	for e in foes:
		if e == null: continue
		e.alive = false
		Game.room_rt.enemies.erase(e.uid)
	holder.queue_free()
	await get_tree().process_frame

## P4b (docs/mockups/icon_study): an icon is only ever drawn at a whole-number scale of its art, through
## SpriteCache.draw_icon. A legacy icon (32 art px in a 64 px PNG, 16 for a HUD glyph, 12 for a status icon) draws at
## 1x, 2x...; an HD icon at its native 64, 48 or 32 (`<id>@<px>` in the manifest). The ui_suite checks every page.
func icon_draw_suite() -> void:
	# The pills are HD (the first family converted); the first legacy item in the manifest stands for the rest until
	# every family has flipped.
	var m: Dictionary = ContentDB.configs["icon_manifest"]
	var legacy := ""
	for k in m:
		if not str(k).contains("@") and str(m[k]).begins_with("res://art/icons/items/") and not m.has(str(k) + "@64"):
			legacy = str(k)
			break
	var odd: Array = []
	for box in range(12, 133):
		for id in ["healing_pill", legacy, "jian", "stun"]:
			if id == "": continue
			var f := SpriteCache.icon_fit(id, box)
			if f.is_empty() or int(f["px"]) != int(f["art"]) * int(f["scale"]) or int(f["scale"]) < 1 or (int(f["px"]) > box and int(f["scale"]) > 1):
				odd.append("%s in %d" % [id, box])
	check(odd.is_empty(), "P4b: an HD item, a legacy item, a HUD glyph and a status icon fit every box at a whole-number scale of their art (%s)" % str(odd.slice(0, 6)))
	var hd_slot := SpriteCache.icon_fit("healing_pill", Page.SLOT - 12)
	var hd_small := SpriteCache.icon_fit("healing_pill", Page.SLOT_SMALL - 12)
	check(int(hd_slot["art"]) == 64 and int(hd_slot["scale"]) == 1 and int(hd_small["art"]) == 32 and int(hd_small["scale"]) == 1,
		"P4b: an HD item shows its 64 at 1:1 in the 76 px slot and its native 32 in the small slot")
	if legacy != "":
		var in_slot := SpriteCache.icon_fit(legacy, Page.SLOT - 12)
		var in_small := SpriteCache.icon_fit(legacy, Page.SLOT_SMALL - 12)
		check(int(in_slot["px"]) == 64 and int(in_slot["scale"]) == 2 and int(in_small["px"]) == 32 and int(in_small["scale"]) == 1,
			"P4b: a legacy item (%s) shows its 32 art px at 2x in the 76 px slot and at 1x in the small slot" % legacy)
	# An HD icon, as the icon build lists one: native renders at 64, 48 and 32.
	var probe := {"probe_hd": m["ember_burst"], "probe_hd@64": m["ember_burst"], "probe_hd@48": m["ember_burst"], "probe_hd@32": m["jian"]}
	m.merge(probe)
	SpriteCache._renders.clear()
	var got := {}
	for box in [64, 48, 32, 60, 100, 128]:
		var f := SpriteCache.icon_fit("probe_hd", box)
		got[box] = [int(f["art"]), int(f["scale"])]
	check(got == {64: [64, 1], 48: [48, 1], 32: [32, 1], 60: [48, 1], 100: [48, 2], 128: [64, 2]},
		"P4b: an HD icon uses its native 64, 48 and 32 renders, and whole multiples above them (%s)" % str(got))
	check(SpriteCache.icon_hd("probe_hd") and SpriteCache.icon_hd("healing_pill") and (legacy == "" or not SpriteCache.icon_hd(legacy)),
		"P4b: the manifest tells an HD icon from a legacy one")
	# P5 (decision 21): the seven Works objects render natively at 96 for the cabinet, and at 64.
	var works := ["work_post_arts", "work_seal", "work_stele", "work_favour", "work_furnace", "work_flag", "work_mirror"]
	check(works.all(func(w): return m.has(w + "@96") and int(SpriteCache.icon_fit(w, 96)["art"]) == 96 and int(SpriteCache.icon_fit(w, 96)["scale"]) == 1
		and int(SpriteCache.icon_fit(w, 64)["art"]) == 64), "P5: the Works objects have native 96 and 64 renders")
	for k in probe: m.erase(k)
	SpriteCache._renders.clear()
	# Nothing but the helper draws an icon texture.
	var strays: Array = []
	var dirs: Array = ["res://scripts/"]
	while not dirs.is_empty():
		var dir: String = dirs.pop_back()
		for sub in DirAccess.get_directories_at(dir): dirs.append(dir + sub + "/")
		for f in DirAccess.get_files_at(dir):
			if not f.ends_with(".gd") or f == "sprite_cache.gd": continue
			var src := FileAccess.get_file_as_string(dir + f)
			if src.contains("SpriteCache.icon(") or src.contains("icon_path(") or src.contains("art/icons/"): strays.append(f)
	check(strays.is_empty(), "P4b: only SpriteCache.draw_icon draws icon textures (%s)" % str(strays))

## The P2 UI inventory's bugs (docs/ui_inventory.md, "Found while inventorying"), each at its rule.
func ui_fixes_suite() -> void:
	var c = Game.active()
	if c == null: return
	# B1: tier n + 1 needs dao_tiers[n] insight in all; the top tier has no next target (the Dao tab indexed one ahead).
	var steps: Array = ContentDB.curve("dao_tiers", [])
	var agree := true
	for t in steps.size():
		var need := ProgressionRules.dao_next_need(t)
		if need != float(steps[t]) or ProgressionRules.dao_tier_for(need) != t + 1 or ProgressionRules.dao_tier_for(need - 1.0) != t: agree = false
	check(agree and ProgressionRules.dao_next_need(steps.size()) == 0.0, "B1: a Dao's next target is the next tier's threshold, and none at the top")
	# B2: the guqin is a tool in the key-item pouch, and from there it opens its page.
	Game.inventory.apply_add(c.id, "guqin", 1, "test")
	var gi := -1
	for i in c.inventory.key_items.size():
		if str(c.inventory.key_items[i].id) == "guqin": gi = i
	var gr := Game.submit({"type": "use_item", "key": gi})
	check(gi >= 0 and gr.get("ok", false) and str(gr.get("open_page", "")) == "guqin", "B2: the guqin in the key-item pouch opens its page")
	check(not Game.submit({"type": "use_item", "key": c.inventory.key_items.size()}).get("ok", false), "B2: an empty key slot uses nothing")
	# B3: a state neither kit drew is made from the normal art (it fell back to it silently): a selected row wears the
	# kit's glow, a disabled one is dimmed; a state the kit has keeps its own art.
	var plain := UiKit.style("minor_panel")
	var chosen := UiKit.style("minor_panel", "selected")
	var off := UiKit.style("minor_panel", "disabled")
	var tint: Color = off.modulate if off is HdStyleBox else (off.modulate_color if off is StyleBoxTexture else Color.WHITE)
	check(chosen is UiKit.LayeredBox and chosen != plain and off != plain and tint.v < 0.8, "B3: a selected panel glows and a disabled one is dimmed")
	check(not (UiKit.style("slot", "selected") is UiKit.LayeredBox) and not (UiKit.style("tab", "selected") is UiKit.LayeredBox), "B3: drawn states keep their art")
	check((plain.modulate if plain is HdStyleBox else Color.WHITE) == Color.WHITE, "B3: the normal panel stays untinted")
	# B12: a great breakthrough with no trial event names none (str(null) printed "Trial: <null>").
	var realm_was: String = c.cultivator.realm_key
	var qp_was: float = c.cultivator.qp
	var wrong: Array = []
	for key in ContentDB.realm_order:
		if not ProgressionRules.is_major(key): continue
		c.cultivator.realm_key = key
		var want = ProgressionRules.breakthrough_spec(key).get("event")
		if str(Game.progression.query_breakthrough(c).get("event", "?")) != ("" if want == null else str(want)): wrong.append(key)
	check(wrong.is_empty(), "B12: the breakthrough's trial is its event, or none (%s)" % str(wrong))
	# B15: a stage from Heaven Glimpse on spans three Levels; a character's own label carries its Level in the stage.
	c.cultivator.realm_key = "sphere_lord_3"
	c.cultivator.qp = c.cultivator.need() * 0.5
	var lv := ProgressionRules.level(c)
	check(lv == int(ContentDB.realm("sphere_lord_3").level) + 1 and ContentDB.realm_label("sphere_lord_3", lv).ends_with(str(lv))
		and ContentDB.realm_label("sphere_lord_3").ends_with(str(int(ContentDB.realm("sphere_lord_3").level))), "B15: halfway through Sphere Lord 3 is Level %d, and says so" % lv)
	c.cultivator.realm_key = realm_was
	c.cultivator.qp = qp_was
	# B11: a tracker objective keeps its count whole at the right end; the words give way.
	var hud_script = load("res://scripts/hud.gd")
	var words: String = hud_script.tracker_objective("· Net glowflies at the Reed Shallows beside the lotus ferry", "0/5", 290.0)
	check(words.ends_with("…") and UiKit.text_width(words, 16) + 10.0 + UiKit.text_width("0/5", 16) <= 290.0
		and hud_script.tracker_objective("· Talk to Aunt Ping", "0/5", 290.0) == "· Talk to Aunt Ping", "B11: the count stays whole beside \"%s\"" % words)
	# B21: words are measured at the size they are drawn: asked for under UiKit.MIN_SIZE, both are at the minimum (and
	# btn() stops stepping its label down there, then shortens it; the ui_suite checks every label fits its button).
	check(UiKit.text_width("Talisman", 12) == UiKit.text_width("Talisman", UiKit.MIN_SIZE) and UiKit.fit("Talisman", 12, 40) == UiKit.fit("Talisman", UiKit.MIN_SIZE, 40)
		and UiKit.text_width(UiKit.fit("Talisman", 12, 40), UiKit.MIN_SIZE) <= 40.0, "B21: a word is fitted at the size it is drawn")
	# B25: with no floor cleared, the Sweep button says why it sweeps none (it said every floor was swept).
	var tower = load("res://scripts/ui/pages/tower_page.gd")
	check(tower.sweep_label(0, 0) == Tx.t("ui.tower.sweep_none") and tower.sweep_label(0, 4) == Tx.t("ui.tower.swept_all")
		and tower.sweep_label(3, 4) == Tx.t("ui.tower.sweep") % 3 and tower.sweep_label(1, 4) == Tx.t("ui.tower.sweep_one") % 1, "B25: the Sweep label follows the floors cleared")
	# B20: a character keeping a post (S50 clears its idle task) shows its post on Characters, not "Idle: none".
	var chars = load("res://scripts/ui/pages/characters_page.gd").new()
	var post_was: Dictionary = Game.posts.state(c).post.duplicate(true)
	var idle_was: Dictionary = c.idle_task.duplicate(true)
	Game.posts.state(c).post = {"kind": "craft", "craft": "delving", "room": "wp_west", "object": "", "since": Clock.now_utc(), "paused": false}
	c.idle_task = {}
	var at_post: String = chars.task_line(c)
	Game.posts.state(c).post = {"kind": "vigil", "craft": "vigil", "room": "wp_west", "object": "", "since": Clock.now_utc(), "paused": false}
	var at_vigil: String = chars.task_line(c)
	Game.posts.state(c).post = {}
	check(at_post == Tx.t("ui.characters.post_at") % [str(ContentDB.entry("posts", "delving").get("short", "")), ContentDB.name_of("rooms", "wp_west")]
		and at_vigil == Tx.t("ui.characters.vigil_at") % ContentDB.name_of("rooms", "wp_west") and chars.task_line(c) == Tx.t("ui.characters.idle_none"),
		"B20: a post shows as the character's task (%s; %s)" % [at_post, at_vigil])
	Game.posts.state(c).post = post_was
	c.idle_task = idle_was
	chars.free()
	# I10: a sect rank reads by its name in sect_ranks.json; I11: pools show rounded and grouped, never above their most;
	# I12: a count of one takes the singular.
	var rk: Dictionary = ContentDB.config("sect_ranks").ranks[2]
	check(ContentDB.rank_name(str(rk.id)) == str(rk.name), "I10: rank %s reads as %s" % [rk.id, rk.name])
	check(UiKit.pool_values(31750.6, 31750.6) == ["31,751", "31,751"] and UiKit.pool_values(0.3, 100.0) == ["1", "100"]
		and UiKit.pool_values(31750.2, 31750.4) == ["31,750", "31,750"], "I11: pool values are grouped and agree with their most")
	check(Tx.plural("ui.teleport.shard", 1) == Tx.t("ui.teleport.shard_one") and Tx.plural("ui.teleport.shard", 5) == Tx.t("ui.teleport.shard")
		and Tx.plural("ui.teleport.shard", 0) == Tx.t("ui.teleport.shard") and Tx.plural("ui.tower.sweep", 1) % 1 == Tx.t("ui.tower.sweep_one") % 1, "I12: one shard, five shards")
	# B8 / I14: a time left in words, in the one style.
	check(UiKit.span(45) == Tx.t("ui.span_s") % 45 and UiKit.span(12 * 60) == Tx.t("ui.span_m") % 12 and UiKit.span(3960) == Tx.t("ui.span_hm") % [1, 6]
		and UiKit.span(2 * 86400 + 5 * 3600) == Tx.t("ui.span_dh") % [2, 5], "B8, I14: UiKit.span writes a duration in words")

func text_suite() -> void:
	var probe := "Pick up Herbal Tea"
	var light := FontVariation.new()
	light.base_font = load("res://art/fonts/CormorantGaramond.ttf")
	var bold_w := UiKit.display_font().get_string_size(probe, HORIZONTAL_ALIGNMENT_LEFT, -1, 40).x
	check(bold_w > light.get_string_size(probe, HORIZONTAL_ALIGNMENT_LEFT, -1, 40).x, "display font is Cormorant Bold, not its Light default")
	var plain := FontVariation.new()
	plain.base_font = load("res://art/fonts/SourceSerif4.ttf")
	check(UiKit.text_font().get_string_size(probe, HORIZONTAL_ALIGNMENT_LEFT, -1, 40).x != plain.get_string_size(probe, HORIZONTAL_ALIGNMENT_LEFT, -1, 40).x,
		"text font carries its weight and optical size")
	check(UiKit.font_for(probe, true, 16) == UiKit.label_font() and UiKit.font_for(probe, true, 26) == UiKit.display_font(), "small headings use the bold serif")
	check(UiKit.size_for(probe, 10) >= UiKit.MIN_SIZE, "no word below the minimum size")
	var keep = Game.account.settings.get("text_size", 1)
	Game.account.settings["text_size"] = 1
	var normal := UiKit.text_width(probe, 18)
	Game.account.settings["text_size"] = 2
	check(UiKit.text_width(probe, 18) > normal * 1.08 and UiKit.line_height(18) > 18 * 1.3 * 1.08, "Large text size widens words and lines")
	Game.account.settings["text_size"] = keep

# ------------------------------------------------------------------ Max Test character (debug tools)
## The Max Test APK's ready-made character: top realm, every system, art and technique, best gear, the whole map,
## animals and both sects; with its ways open, no built room is out of reach.
func max_character_suite() -> void:
	var folder := "user://max_character_suite/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	check(Game.accounts.create_max_character(1, "Max").get("ok", false), "the Max Test character is made where debug tools run")
	var c = Game.character("c1")
	if c == null: return
	var top := "mortal"
	for z in ContentDB.all("zones"):
		if ContentDB.realm_position(str(z.get("ceiling", ""))) > ContentDB.realm_position(top): top = str(z.ceiling)
	check(c.cultivator.realm_key == top, "stands at the top of this build's zones (%s)" % c.cultivator.realm_key)
	var locked: Array = []
	for e in ContentDB.all("unlocks"):
		if not c.cultivator.unlocked.has(str(e.id)): locked.append(str(e.id))
	check(locked.is_empty(), "every system unlocked (still locked: %s)" % str(locked))
	check(c.cultivator.techniques_known.size() == ContentDB.all("techniques").size() and c.cultivator.secret_arts.size() == ContentDB.all("secret_arts").size(),
		"every technique and movement art known")
	check(c.inventory.equipped.weapon != null and str(c.inventory.equipped.weapon.quality) == "perfect" and int(c.inventory.equipped.weapon.enhance) == 10,
		"the best gear worn at Perfect +10")
	check(c.inventory.bag.count(null) > 20 and not (Game.account.storage.get("items", []) as Array).is_empty(), "the bag has room; spare stacks wait in storage")
	check(Game.account.teleports.size() == ContentDB.all("teleport_stones").size() and Game.account.visited_rooms.size() == ContentDB.rooms.size(),
		"every teleport stone found and every room on the map")
	check(not c.pets.is_empty() and c.mount_pet != "" and not c.companions.roster.is_empty(), "animals, a mount and companions")
	var ranks: Array = ContentDB.config("sect_ranks").get("order", [])
	check(Game.sect.founded() and str(c.training_sect.get("rank", "")) == str(ranks.back()), "a founded sect and Elder of a training sect")
	check(str(c.position.room) == str(ContentDB.config("account_rules").get("skip_start", {}).get("room", "")), "starts where a skipped Prologue does")
	check(Game.economy.balance("silver_tael") >= 10000000, "silver to spend")
	Game.world.debug_open_ways = true
	var shut: Array = []
	for rid in ContentDB.rooms:
		for p in ContentDB.room(rid).get("portals", []):
			if ContentDB.room(str(p.get("to", ""))).is_empty(): continue
			if not Game.world.portal_state(c, p).get("open", false): shut.append("%s:%s" % [rid, p.id])
	check(shut.is_empty(), "with ways open no built room is out of reach (shut: %s)" % str(shut))
	Game.world.debug_open_ways = false

# ------------------------------------------------------------------ S43 Paths Above and the room catalogue
func paths_above_suite() -> void:
	# Every row names a real optional ledge (a surface or a block) marked for that later art.
	for e in ContentDB.all("paths_above"):
		var room := ContentDB.room(str(e.room))
		var named := false
		for s in room.get("surfaces", []) + room.get("blocks", []):
			if str(s.id) == str(e.surface) and str(s.get("later", "")) == str(e.art): named = true
		check(named, "Paths Above row %s names a later ledge" % e.id)
	check(ContentDB.has_entry("paths_above", "wp_west:pine_top") and ContentDB.has_entry("paths_above", "cf_behind_falls:shaft_top"),
		"the catalogue's later ledges (Willow Path West's pine top, the falls' Wall-Step shaft) are rows")
	# A cracked block (the Lower Pit slab over the shard) stops walking until a Plunge breaks it.
	var pit := ZoneGeometry.new()
	pit.configure(WorldAuthority.compile_geometry(ContentDB.room("sq_lower_pit")))
	var slab: WalkSurface = pit.index.get("cracked_slab")
	check(slab != null and slab.cracked and pit.wall_face_at(Vector2(1900, 810), 10.0, "ground"), "the Lower Pit slab is a cracked block that stops you")
	pit.break_surface("cracked_slab")
	check(slab != null and slab.disabled and not pit.wall_face_at(Vector2(1900, 810), 10.0, "ground"), "a broken slab no longer blocks")
	# The Jade trial's planks rise with the room clock; the libraries' upper floors are sealed by rank.
	var trial := ZoneGeometry.new()
	trial.configure(WorldAuthority.compile_geometry(ContentDB.room("sf_trial_jade")))
	check(trial.movers.size() == 2 and (trial.index.plank_1 as WalkSurface).moving, "the Jade trial has two moving planks")
	var sealed := 0
	for cl in ContentDB.room("ja_library").get("climbables", []):
		if cl.has("requires"): sealed += 1
	check(sealed == 2, "both library floors are sealed by rank (%d)" % sealed)
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Game.world.apply_teleport(c.id, "wp_west")
	Game.account.paths_above.erase("wp_west:pine_top")
	var heard := []
	var listen := func(n: String, p: Dictionary):
		if n == "path_above_found": heard.append(p)
	GameEvents.event.connect(listen)
	for sid in ["pine_top", "pine_top", "willow_branch_a"]:
		GameEvents.emit_event("landed", {"actor": c.id, "surface": sid, "fall_height": 0.0, "plunge": false})
		GameEvents.flush()
	GameEvents.event.disconnect(listen)
	check(Game.account.paths_above.has("wp_west:pine_top") and heard.size() == 1, "standing on a later ledge finds it, once (%d)" % heard.size())
	check(Game.account.snapshot().paths_above.has("wp_west:pine_top"), "found ledges are saved with the account")

# ------------------------------------------------------------------ S47 gear upkeep
func forge_upkeep_suite() -> void:
	var c = Game.active()
	if c == null: return
	Unlocks.force_unlock(c.id, "smithing")
	var add := func(id: String, quality := "common") -> Dictionary:
		Game.inventory.apply_add_equipment(c.id, id, int(ContentDB.item(id).get("ilv", 10)), quality, "test")
		var best: Dictionary = {}
		for it in c.inventory.bag:
			if it != null and str(it.id) == id and (best.is_empty() or int(it.uid) > int(best.uid)): best = it
		return best
	# Pity: from +5 a try can fail; each failure adds 5% to the next try on that piece, a success clears it.
	var jian: Dictionary = add.call("jadeiron_jian")
	jian.enhance = 5
	var row: Dictionary = Game.crafting.grade_row("jadeiron_jian")
	check(str(row.metal) == "jadeiron", "an Earth piece is enhanced with Jadeiron (salvage.json)")
	check(near(Game.crafting.enhance_chance(jian), 0.88), "the try from +5 is 88%% (%.2f)" % Game.crafting.enhance_chance(jian))
	Game.inventory.apply_add(c.id, "jadeiron", 200, "test")
	Game.inventory.apply_add(c.id, "spirit_stone_shard", 60, "test")
	Game.economy.apply_currency("silver_tael", 50000, "test")
	var fails := 0
	var saw_reset := false
	for i in 40:
		var before := float(jian.get("pity", 0.0))
		var r := Game.submit({"type": "enhance", "uid": int(jian.uid)})
		if not r.get("ok", false): break
		if r.success:
			saw_reset = saw_reset or before > 0.0
			check(near(float(jian.get("pity", 0.0)), 0.0, 0.0) or float(jian.get("pity", 0.0)) == 0.0, "a success clears the pity")
			if int(jian.enhance) >= 9: break
		else:
			fails += 1
			check(near(float(jian.pity), before + 0.05, 0.001), "a failure adds 5%% pity (%.2f -> %.2f)" % [before, float(jian.pity)])
		if int(jian.enhance) >= 9: break
	check(fails > 0 and saw_reset, "pity builds on failures and resets on a success (%d failures)" % fails)
	check(near(Game.crafting.enhance_chance({"id": "jadeiron_jian", "enhance": 7, "pity": 0.1}, 2), 1.0 - 0.36 + 0.1 + 0.05, 0.001),
		"pity and two Refining Essence add to the chance")
	# Inherit moves N - 2 for 2 Spirit Stones a level; the old piece goes back to +0.
	var old_jian: Dictionary = add.call("jadeiron_jian")
	old_jian.enhance = 7
	var new_jian: Dictionary = add.call("cloudsteel_jian") if ContentDB.has_entry("items", "cloudsteel_jian") else add.call("jadeiron_jian")
	Game.economy.apply_currency("spirit_stone", 50, "test")
	var stones0: int = Game.economy.balance("spirit_stone")
	var ih := Game.submit({"type": "inherit_enhancement", "from": int(old_jian.uid), "to": int(new_jian.uid)})
	check(ih.get("ok", false) and int(new_jian.enhance) == 5 and int(old_jian.enhance) == 0 and stones0 - Game.economy.balance("spirit_stone") == 10,
		"Inherit moves +7 as +5 for 10 Spirit Stones (%s)" % str(ih))
	var robe: Dictionary = add.call("jadeiron_robe")
	check(not Game.submit({"type": "inherit_enhancement", "from": int(new_jian.uid), "to": int(robe.uid)}).get("ok", true), "Inherit keeps to one slot")
	# Salvage: metal and essence by grade; locked pieces are never touched.
	var a: Dictionary = add.call("jadeiron_robe")
	var b: Dictionary = add.call("jadeiron_robe")
	c.inventory.locked[int(b.uid)] = true
	var ess0: int = c.inventory.count("refining_essence")
	var sv := Game.submit({"type": "salvage", "items": [int(a.uid), int(b.uid)]})
	check(sv.get("ok", false) and (sv.items as Array).size() == 1 and c.inventory.find_uid(int(b.uid)) >= 0 and c.inventory.find_uid(int(a.uid)) < 0,
		"Salvage takes the free piece and never the locked one")
	var earth_ess: int = ContentDB.entry("salvage", "earth").returns.filter(func(x): return str(x.item) == "refining_essence")[0].count
	check(c.inventory.count("refining_essence") - ess0 == earth_ess and earth_ess == 5, "an Earth piece gives 2 Jadeiron and 5 Refining Essence (3, half again since P7b)")
	c.inventory.locked.erase(int(b.uid))
	# Reroll: the locked affix stays, the reroll costs double, and the old roll can be kept.
	var fine: Dictionary = add.call("jadeiron_robe", "superior")
	check((fine.affixes as Array).size() >= 2, "a Superior piece has affixes to reroll")
	Game.inventory.apply_add(c.id, "refining_essence", 40, "test")
	var plain_cost: Dictionary = Game.crafting.reroll_cost(fine)
	check(Game.submit({"type": "lock_affix", "uid": int(fine.uid), "affix": 0}).get("ok", false), "lock the first affix")
	var locked_cost: Dictionary = Game.crafting.reroll_cost(fine)
	check(int(locked_cost.essence) == 2 * int(plain_cost.essence) and int(locked_cost.taels) == 2 * int(plain_cost.taels), "a locked affix doubles the reroll")
	var kept: Dictionary = (fine.affixes[0] as Dictionary).duplicate()
	var old_affixes: Array = (fine.affixes as Array).duplicate(true)
	var rr := Game.submit({"type": "reroll_affixes", "uid": int(fine.uid)})
	check(rr.get("ok", false) and str(rr.new[0].id) == str(kept.id) and near(float(rr.new[0].value), float(kept.value)), "the locked affix survives the reroll")
	check(Game.submit({"type": "choose_affixes", "uid": int(fine.uid), "keep": "old"}).get("ok", false) and str(fine.affixes) == str(old_affixes) and not fine.has("pending_affixes"),
		"keeping the old roll leaves the piece as it was")
	Game.submit({"type": "reroll_affixes", "uid": int(fine.uid)})
	var fresh: Array = (fine.pending_affixes as Array).duplicate(true)
	Game.submit({"type": "choose_affixes", "uid": int(fine.uid), "keep": "new"})
	check(str(fine.affixes) == str(fresh), "taking the new roll keeps it")
	# Tidy up the test pieces.
	for it in [jian, old_jian, new_jian, robe, b, fine]:
		var i: int = c.inventory.find_uid(int(it.uid))
		if i >= 0: Game.inventory.apply_remove_index(c.id, i, 1, "test")

# ------------------------------------------------------------------ S47 flying sword, Sword Intent, loadouts, self-detonation
func sword_loadout_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal"]: Game.combat.cure_status(c.id, sid)
	Unlocks.force_unlock(c.id, "dao_tree")
	# The Sword Dao's third tier teaches Sword Release.
	c.cultivator.techniques_known.erase("sword_release")
	c.cultivator.daos["sword"] = {"tier": 2, "insight": 0.0}
	var need := 0.0
	for t in 60:
		if ProgressionRules.dao_tier_for(need) >= 3: break
		need += 50.0
	Game.progression.apply_insight(c.id, "sword", need + 1.0, "test:sword:%d" % randi())
	check(int(c.cultivator.daos.sword.tier) >= 3 and c.cultivator.techniques_known.has("sword_release"), "Sword Dao tier 3 teaches Sword Release")
	# Sword Release needs a jian in hand; it flies for 8 s, strikes the nearest foe, and the hands fight with palms.
	Game.inventory.apply_add_equipment(c.id, "jadeiron_jian", 27, "common", "test")
	var ji: int = c.inventory.first_index("jadeiron_jian")
	var held_before = c.inventory.equipped.get("weapon")
	# The test character's realm may be below the jian's; it is put in hand directly (wearing rules are tested elsewhere).
	c.inventory.equipped["weapon"] = c.inventory.bag[ji]
	c.inventory.bag[ji] = held_before
	Unlocks.force_unlock(c.id, "attack")
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:sword_release")
	var heard := {}
	var listen := func(n: String, p: Dictionary):
		if n in ["sword_released", "sword_returned", "sword_intent_changed", "loadout_swapped", "artifact_detonated", "projectile_spawned"]:
			heard[n] = int(heard.get(n, 0)) + 1
			if n == "projectile_spawned" and str(p.get("art", "")) == "flying_sword": heard["sword_strike"] = int(heard.get("sword_strike", 0)) + 1
	GameEvents.event.connect(listen)
	var rel := Game.submit({"type": "toggle_sword_release"})
	check(rel.get("ok", false) and Game.combat.sword_released.has(c.id), "the jian is released (%s)" % str(rel))
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(200, 0), 2)
	for i in 30:
		Game.tick(0.05)
		GameEvents.flush()
	check(int(heard.get("sword_strike", 0)) >= 1, "the flying sword strikes the nearest foe (%d)" % int(heard.get("sword_strike", 0)))
	Game.combat.basic_attack(c, 1)
	var tl: Dictionary = Game.combat.timeline(c.id)
	check(str(tl.family) == "fists" and near(float((tl.get("step", {}) as Dictionary).get("mult", 1.0)), float(ContentDB.entry("weapon_families", "fists").combo[0].get("mult", 1.0)) * 0.8, 0.01),
		"while it flies, the hands fight with Qi palms at x0.8")
	for i in 200:
		Game.tick(0.05)
		GameEvents.flush()
		if not Game.combat.sword_released.has(c.id): break
	check(not Game.combat.sword_released.has(c.id) and int(heard.get("sword_returned", 0)) >= 1, "the sword returns after 8 s")
	# Sword Intent: consecutive jian hits stack to 10 (+1% penetration each) and fade 3 s after the last.
	if foe == null or not foe.alive: foe = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(40, 0), 2)
	for i in 12: Game.combat._feed_intent(c, foe, {"source": "basic"})
	check(int(Game.combat.sword_intent[c.id].stacks) == 10 and near(Game.combat.intent_penetration(c), 0.10, 0.001), "ten jian hits give ten stacks of Intent (+10% penetration)")
	for i in 70:
		Game.tick(0.05)
	GameEvents.flush()
	check(int(Game.combat.sword_intent[c.id].stacks) == 0, "Intent fades 3 s after the last jian hit")
	# Dual loadout: a spare weapon, a swap, and each weapon keeps its own technique bar.
	Unlocks.force_unlock(c.id, "dual_loadout")
	var spear_id := "iron_spear"
	Game.inventory.apply_add_equipment(c.id, spear_id, 10, "common", "test")
	var si: int = c.inventory.first_index(spear_id)
	var ss := Game.submit({"type": "set_spare_weapon", "index": si})
	check(ss.get("ok", false) or str(ss.get("reason", "")) == "cannot_wear", "a spare weapon follows the wearing rules (%s)" % str(ss))
	if not ss.get("ok", false):   # the test character has not passed the Entry Trial: the spear is placed directly
		c.inventory.loadout["spare"] = c.inventory.bag[si]
		c.inventory.bag[si] = null
	var bar_a: Array = c.cultivator.technique_slots.duplicate()
	var sw := Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	check(sw.get("ok", false) and str(c.inventory.equipped.weapon.id) == spear_id and str(c.inventory.loadout.spare.id) == "jadeiron_jian", "Swap puts the spear in hand and the jian in the spare slot")
	c.cultivator.technique_slots[0] = null
	var bar_b: Array = c.cultivator.technique_slots.duplicate()
	Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	check(str(c.cultivator.technique_slots) == str(bar_a), "swapping back brings the jian's own bar")
	Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	check(str(c.cultivator.technique_slots) == str(bar_b) and int(c.cultivator.daos.sword.tier) >= 3, "the spear's bar is kept too, and no Dao tier is touched")
	Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	# Self-detonation needs a confirmation, then the spare artifact is gone.
	Game.inventory.apply_add_equipment(c.id, "jadeiron_robe", 27, "common", "test")
	var ri: int = c.inventory.first_index("jadeiron_robe")
	var d1 := Game.submit({"type": "self_detonate", "index": ri})
	check(str(d1.get("reason", "")) == "confirm" and c.inventory.first_index("jadeiron_robe") == ri, "self-detonation asks first and destroys nothing")
	var d2 := Game.submit({"type": "self_detonate", "index": ri, "confirm": true})
	GameEvents.flush()
	check(d2.get("ok", false) and c.inventory.bag[ri] == null and int(heard.get("artifact_detonated", 0)) == 1, "confirmed, the spare artifact bursts and is gone")
	GameEvents.event.disconnect(listen)
	# Put things back.
	Game.submit({"type": "set_spare_weapon", "index": -1})
	var worn = c.inventory.equipped.get("weapon")
	c.inventory.equipped["weapon"] = held_before
	if held_before != null:
		var hb: int = c.inventory.find_uid(int(held_before.get("uid", -1)))
		if hb >= 0: c.inventory.bag[hb] = worn
	for id in ["jadeiron_jian", spear_id]:
		var k: int = c.inventory.first_index(id)
		if k >= 0: Game.inventory.apply_remove_index(c.id, k, 1, "test")
	if foe != null and foe.alive: foe.alive = false

# ------------------------------------------------------------------ S47 v1.1 weapon families: heavy sabre, fan, flute
## Put a fresh weapon of this id straight into the hand (wearing rules are tested elsewhere); returns what was held.
func _wield(c, item_id: String):
	Game.inventory.apply_add_equipment(c.id, item_id, 14, "common", "test")
	var i: int = c.inventory.first_index(item_id)
	var held = c.inventory.equipped.get("weapon")
	c.inventory.equipped["weapon"] = c.inventory.bag[i]
	c.inventory.bag[i] = null
	Game.combat.refresh_stats(c.id)
	return held

func _idle_hands(c) -> void:
	for i in 40:
		if not Game.combat.is_busy(c.id): break
		Game.tick(0.05)
	GameEvents.flush()

func weapon_families_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	Unlocks.force_unlock(c.id, "attack")
	Unlocks.force_unlock(c.id, "composure")
	for fam_id in ["heavy_sabre", "fan", "flute"]:
		var fam := ContentDB.entry("weapon_families", fam_id)
		var look := str(fam.get("appearance", [""])[0])
		check(not fam.is_empty() and Wardrobe.parts.weapon.has(look) and Wardrobe.parts._attack_by_weapon.has(look), "the %s family exists with its avatar weapon (%s)" % [fam_id, look])
		for grade in ["training", "iron", "jadeiron", "cloudsteel"]:
			check(ContentDB.entry("artifacts", "%s_%s" % [grade, fam_id]).get("family", "") == fam_id, "%s %s is a %s" % [grade, fam_id, fam_id])
	var heard := {"hits": {}, "arts": {}, "pulse": 0, "melody_off": ""}
	var listen := func(n: String, p: Dictionary):
		if n == "hit_landed" and str(p.get("target_kind", "")) == "enemy":
			heard.hits[str(p.target)] = int(heard.hits.get(str(p.target), 0)) + 1
		if n == "projectile_spawned": heard.arts[str(p.art)] = int(heard.arts.get(str(p.art), 0)) + 1
		if n == "melody_pulse": heard.pulse = int(heard.pulse) + 1
		if n == "melody_changed" and not p.get("on", false): heard.melody_off = str(p.get("reason", ""))
	GameEvents.event.connect(listen)
	var lv := ProgressionRules.level(c) + 12
	# The heavy sabre: slow, a cleave that reaches three foes in a line, and armour break.
	var held_before = _wield(c, "iron_heavy_sabre")
	check(str(StatRules.family(c).id) == "heavy_sabre", "an iron heavy sabre puts the heavy sabre family in hand")
	var foes: Array = []
	for i in 3: foes.append(Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(36 + i * 20, 0), lv))
	_idle_hands(c)
	heard.hits = {}
	Game.combat.basic_attack(c, 1)
	for i in 20:
		Game.tick(0.05)
	GameEvents.flush()
	var struck := 0
	for f in foes:
		if heard.hits.has(str(f.uid)): struck += 1
	check(struck >= 2, "one sabre cleave strikes several foes in a line (%d of 3)" % struck)
	var foe: EnemyState = foes[0]
	Game.combat._weapon_after_hit(c, foe, {"armour_break": {"chance": 1.0, "duration_s": 4}})
	check(foe.pools.has_status("sundered"), "an armour break leaves the foe Sundered")
	var pv := Game.combat.player_view(c)
	pv["accuracy"] = 99999.0
	var ev := Game.combat.enemy_view(foe)
	ev["physical_defense"] = 400.0
	var atk := {"damage_type": "physical", "element": "none", "mult": [1.0, 1.0], "range": [1.0, 1.0], "source": "test"}
	var r1 := CombatRules.resolve(pv, ev, atk, Rng.keyed(7, "sunder"))
	ev["sundered"] = false
	var r2 := CombatRules.resolve(pv, ev, atk, Rng.keyed(7, "sunder"))
	check(int(r1.amount) > int(r2.amount), "a Sundered foe takes more from every blow (%d > %d)" % [int(r1.amount), int(r2.amount)])
	# The fan: wind that lifts a foe (helpless until it lands) and a third stroke thrown out and back.
	_wield(c, "iron_fan")
	var foe2: EnemyState = foes[1]
	Game.combat._weapon_after_hit(c, foe2, {"knockup_s": 0.8})
	check(foe2.pools.has_status("launched") and foe2.pools.blocked("move") and foe2.pools.blocked("attack"), "the fan's wind launches a foe: it can neither move nor strike")
	for i in 8: Game.tick(0.05)
	check(foe2.hover > 20.0, "a launched foe rises into the air (%.0f)" % foe2.hover)
	for i in 14: Game.tick(0.05)
	check(not foe2.pools.has_status("launched") and foe2.hover == 0.0, "and lands when it ends")
	for f in foes:
		f.alive = false
	var target: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(130, 0), lv)
	_idle_hands(c)
	heard.hits = {}
	heard.arts = {}
	var fam_fan := ContentDB.entry("weapon_families", "fan")
	Game.combat._start_step(c, fam_fan, 2, 1)
	for i in 50:
		Game.tick(0.05)
	GameEvents.flush()
	check(int(heard.arts.get("fan", 0)) == 1, "the fan's third stroke throws the fan")
	check(int(heard.hits.get(str(target.uid), 0)) >= 2, "the thrown fan cuts on its way out and again on its way back (%d)" % int(heard.hits.get(str(target.uid), 0)))
	target.alive = false
	# The flute: a note of Qi at the tap; held, a melody aura that slows, heals and drains Composure.
	_wield(c, "iron_flute")
	_idle_hands(c)
	heard.arts = {}
	Game.combat.basic_attack(c, 1)
	for i in 14: Game.tick(0.05)
	GameEvents.flush()
	check(int(heard.arts.get("note", 0)) == 1, "a flute's tap sends a note")
	_idle_hands(c)
	var near_foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(120, 0), lv)
	var ally: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-80, 0), 5)
	ally.team = "ally"
	ally.pools.hp = ally.pools.max_hp * 0.5
	c.pools.composure = 100.0
	c.pools.hp = c.pools.max_hp * 0.6
	var hp0: float = c.pools.hp
	var on := Game.submit({"type": "channel_melody", "on": true})
	check(on.get("ok", false) and Game.combat.is_playing(c.id), "holding Attack with a flute plays the melody (%s)" % str(on))
	check(Game.combat.move_factor(c.id) <= 0.5 + 0.001, "the player walks at half pace while playing")
	for i in 22: Game.tick(0.05)
	GameEvents.flush()
	check(int(heard.pulse) >= 2, "the melody pulses every half second (%d)" % int(heard.pulse))
	check(near_foe.pools.has_status("slow"), "foes within the aura are slowed")
	check(ally.pools.hp > ally.pools.max_hp * 0.5 and c.pools.hp > hp0, "allies and the player recover health as it plays")
	check(c.pools.composure < 100.0 - 6.0, "the melody drains Composure (%.1f)" % c.pools.composure)
	Game.submit({"type": "channel_melody", "on": false})
	GameEvents.flush()
	check(not Game.combat.is_playing(c.id) and heard.melody_off == "released", "letting go ends it")
	c.pools.composure = 1.0
	Game.submit({"type": "channel_melody", "on": true})
	check(not Game.combat.is_playing(c.id), "it will not start with almost no Composure")
	c.pools.composure = 6.0
	Game.submit({"type": "channel_melody", "on": true})
	for i in 30: Game.tick(0.05)
	GameEvents.flush()
	check(not Game.combat.is_playing(c.id) and heard.melody_off == "composure", "it ends when Composure runs out")
	# Confusion and Fear now move a monster: a feared foe backs away instead of closing in.
	near_foe.ai.state = "aggro"
	near_foe.ai.timer = 0.0
	var d0: float = absf(near_foe.plane.x - st.plane.x)
	Game.combat.apply_enemy_status(near_foe, {"id": "fear", "power": 1.0, "remaining": 1.5, "source": c.id})
	for i in 10: Game.tick(0.05)
	check(absf(near_foe.plane.x - st.plane.x) > d0 + 10.0 and str(near_foe.ai.state) == "aggro", "a feared monster runs from its foe")
	# Clear Heart Melody: 4% a second for 6 s on the caster and every ally within 220.
	ally.pools.hp = ally.pools.max_hp * 0.5
	var healed := Game.combat.heal_circle(c, 0.04, 6.0, 220.0, "test")
	for i in 20: Game.tick(0.05)
	check(healed >= 1 and ally.pools.hp > ally.pools.max_hp * 0.52, "Clear Heart Melody heals the allies beside the player over time (%d, %.2f)" % [healed, ally.pools.hp / ally.pools.max_hp])
	var ch := ContentDB.entry("techniques", "clear_heart_melody")
	check(float(ch.get("allies_heal_pct", 0)) == 0.04 and not ch.has("buff"), "Clear Heart Melody is a healing song, not a resting buff")
	# Their techniques carry the families' traits, and the library ones are taught by the Mission Hall.
	check(ContentDB.entry("techniques", "thunder_dao_arc").has("armour_break"), "the heavy sabre's arc breaks armour")
	check(bool(ContentDB.entry("techniques", "returning_crane_fan").projectile.get("returning", false)), "Returning Crane Fan flies out and back")
	check(str(ContentDB.entry("techniques", "reed_song").projectile.get("art", "")) == "note", "Reed Song sends notes")
	var hall := ContentDB.entry("shops", "jade_sect")
	var taught := {}
	for sitem in hall.get("stock", []):
		if str(sitem.get("item", "")) == "technique_manual": taught[str(sitem.learn)] = true
	var missing := []
	for t in ContentDB.all("techniques"):
		if str(t.get("source", "")) in ["library_1", "library_2", "library_3"] and not taught.has(str(t.id)): missing.append(str(t.id))
	check(missing.is_empty() and taught.has("clear_heart_melody") and taught.has("gale_fan"), "the Jade Sect Mission Hall teaches every library technique (missing %s)" % str(missing))
	GameEvents.event.disconnect(listen)
	near_foe.alive = false
	ally.alive = false
	Game.combat.ally_hots.clear()
	c.inventory.equipped["weapon"] = held_before
	Game.combat.refresh_stats(c.id)
	c.pools.composure = 100.0

# ------------------------------------------------------------------ S48 the Soul line, the Poison path and the S10 meridian gates
func soul_poison_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear", "poison"]: Game.combat.cure_status(c.id, sid)
	var meridians_before: Dictionary = c.cultivator.meridians.duplicate()
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var tox_before: float = c.cultivator.toxicity
	var lv := ProgressionRules.level(c) + 12
	# The mentor's techniques now have a teacher, and the Soul Dao's first three tiers teach the Soul line.
	var grants := {}
	for q in ContentDB.all("quests"):
		for fx in q.get("rewards", []) + q.get("on_accept", []):
			if fx is Dictionary and str(fx.get("kind", "")) == "learn_technique": grants[str(fx.get("technique", ""))] = str(q.id)
	for tid in ["mirror_mind_spike", "soul_lantern_ward", "still_water_focus"]:
		check(grants.has(tid), "%s is taught by a quest (%s)" % [tid, str(grants.get(tid, "none"))])
	for tid in ["sense_lock", "phantom_double", "soul_search"]: c.cultivator.techniques_known.erase(tid)
	c.cultivator.daos["soul"] = {"tier": 0, "insight": 0.0}
	var need := 0.0
	for t in 200:
		if ProgressionRules.dao_tier_for(need) >= 3: break
		need += 50.0
	Game.progression.apply_insight(c.id, "soul", need + 1.0, "teacher:test")
	check(c.cultivator.techniques_known.has("sense_lock") and c.cultivator.techniques_known.has("phantom_double") and c.cultivator.techniques_known.has("soul_search"),
		"Soul Dao tiers 1-3 teach Sense Lock, Phantom Double and Soul Search (tier %d)" % int(c.cultivator.daos.soul.tier))
	# Spirit is a main stat for soul attacks, whatever the weapon.
	c.cultivator.meridians["spirit"] = 0
	Game.combat.refresh_stats(c.id)
	var soul0: float = c.stats.value("soul_attack")
	c.cultivator.meridians["spirit"] = 60
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("soul_attack") > soul0 * 1.3, "60 Spirit lifts soul attack by more than a third (%.0f -> %.0f)" % [soul0, c.stats.value("soul_attack")])
	# S10 meridian gates open exactly at their thresholds.
	c.cultivator.meridians["spirit"] = 24
	check(not StatRules.gate_flag(c, "sense_cost_25"), "Spirit 24 opens no gate")
	c.cultivator.meridians["spirit"] = 25
	check(StatRules.gate_flag(c, "sense_cost_25") and not StatRules.gate_flag(c, "fear_immune_weaker"), "Spirit 25 opens the Sense gate and no more")
	c.cultivator.meridians["spirit"] = 100
	check(StatRules.gate_flag(c, "fear_immune_weaker") and StatRules.gate_flag(c, "soul_ignore_20"), "Spirit 100 opens all three Spirit gates")
	c.cultivator.meridians["essence"] = 0
	var air0 := Game.combat.air_qi_mult(c)
	c.cultivator.meridians["essence"] = 50
	check(near(Game.combat.air_qi_mult(c), air0 * 0.8, 0.001), "Essence 50: flight costs 20% less QI")
	c.cultivator.daos["soul"] = {"tier": 4, "insight": 0.0}
	c.cultivator.meridians["insight"] = 99
	var t4 := ProgressionRules.effective_dao_tier(c, "soul")
	c.cultivator.meridians["insight"] = 100
	check(t4 == 4 and ProgressionRules.effective_dao_tier(c, "soul") == 5, "Insight 100: a Dao at Explanation gives one tier more")
	c.cultivator.meridians["insight"] = 25
	c.cooldowns.erase("free_reroll_wk")
	var fake := {"id": "iron_jian", "affixes": [{"id": "x"}]}
	check(bool(Game.crafting.reroll_cost(fake, c).get("free", false)), "Insight 25: one affix reroll a week is free")
	c.cooldowns["free_reroll_wk"] = Clock.reset_week(Clock.now_utc())
	check(not Game.crafting.reroll_cost(fake, c).get("free", false), "and only one")
	# Agility 50: a second dodge charge.
	Unlocks.force_unlock(c.id, "dodge_dash")
	c.pools.cooldowns.erase("dodge")
	c.pools.cooldowns.erase("dodge_2")
	c.cultivator.meridians["agility"] = 0
	Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	var d2 := Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	check(not d2.get("ok", false), "without the gate a second dodge waits for the cooldown")
	c.pools.cooldowns.erase("dodge")
	c.cultivator.meridians["agility"] = 50
	Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	var d3 := Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	check(d3.get("ok", false), "Agility 50: a second dodge charge (%s)" % str(d3))
	for i in 20: Game.tick(0.05)
	# Essence 25: the first technique of each fight costs no QI.
	_idle_hands(c)
	c.cultivator.meridians["essence"] = 25
	var slot_before = c.cultivator.technique_slots[0]
	c.cultivator.technique_slots[0] = "flowing_palm"
	if not c.cultivator.techniques_known.has("flowing_palm"): c.cultivator.techniques_known.append("flowing_palm")
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:flowing_palm")
	Game.combat.timeline(c.id)["fight_t"] = -999.0
	var q0: float = c.pools.qi
	var u1 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(u1.get("ok", false) and near(c.pools.qi, q0, 0.01), "Essence 25: the first technique of a fight is free (%s)" % str(u1))
	_idle_hands(c)
	c.pools.cooldowns.erase("tech:flowing_palm")
	var q1: float = c.pools.qi
	Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(c.pools.qi < q1, "the next one in the same fight is paid for")
	_idle_hands(c)
	c.cultivator.technique_slots[0] = slot_before
	# Sense Lock: a foe that evades everything cannot evade a locked soul.
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	foe.stats["evasion"] = 999999.0
	var heard := {"miss": 0, "hit": 0, "search": "", "broken": ""}
	var listen := func(n: String, p: Dictionary):
		if n == "hit_missed" and str(p.get("target", "")) == str(foe.uid): heard.miss = int(heard.miss) + 1
		if n == "hit_landed" and str(p.get("target", "")) == str(foe.uid): heard.hit = int(heard.hit) + 1
		if n == "soul_searched": heard.search = str(p.get("memory", "?"))
		if n == "illusion_broken": heard.broken = str(p.get("reason", ""))
	GameEvents.event.connect(listen)
	var atk := {"damage_type": "physical", "element": "none", "mult": [0.01, 0.01], "range": [1.0, 1.0], "source": "test"}
	for i in 30: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(int(heard.miss) >= 5, "an evasive foe dodges ordinary blows (%d of 30 missed)" % int(heard.miss))
	Game.combat._weapon_after_hit(c, foe, {"sense_lock_s": 8.0})
	heard.miss = 0
	for i in 30: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(foe.pools.has_status("sense_locked") and int(heard.miss) == 0, "Sense Locked, it cannot evade (%d missed)" % int(heard.miss))
	foe.alive = false
	# Phantom Double: foes near it turn on the illusion; three strikes break it; time also ends it.
	var foe2: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(150, 0), lv)
	Game.combat._cast_illusion(c, ContentDB.entry("techniques", "phantom_double"))
	var aim := EnemyBrain.target_position(Game.enemies, foe2)
	check(str(aim.get("id", "")) == "decoy", "a foe near the illusion hunts it instead of the player")
	var d: Dictionary = Game.combat.decoys[c.id]
	foe2.plane = Vector2(float(d.x) + 30.0, float(d.y))
	foe2.facing = -1
	var ev := Game.combat.enemy_view(foe2)
	for i in 3: Game.combat._strike_decoy(foe2, ev, {"x": [0, 60], "depth": 30, "alt": [-30, 60]}, {})
	GameEvents.flush()
	check(not Game.combat.decoys.has(c.id) and heard.broken == "struck", "three strikes break the illusion")
	heard.broken = ""
	Game.combat._cast_illusion(c, ContentDB.entry("techniques", "phantom_double"))
	for i in 240:
		Game.tick(0.05)
		if not Game.combat.decoys.has(c.id): break
	GameEvents.flush()
	check(not Game.combat.decoys.has(c.id) and heard.broken == "time", "the illusion fades when its time is up")
	foe2.alive = false
	# Soul Search: an elite searched and slain gives up a memory and an extra drop; a common foe is not marked.
	var common: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(80, 20), lv)
	Game.combat._weapon_after_hit(c, common, {"soul_search_s": 12.0})
	check(not Game.combat.searched.has(str(common.uid)), "Soul Search marks only elites and bosses")
	common.alive = false
	var elite: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(80, -20), lv, {"elite": true})
	Game.combat._weapon_after_hit(c, elite, {"soul_search_s": 12.0})
	check(Game.combat.searched.has(str(elite.uid)) and elite.pools.has_status("soul_searched"), "an elite is marked for Soul Search")
	Game.combat._damage_enemy(elite, elite.pools.hp + 10.0, c.id, "soul", "soul", false, {})
	for i in 4: Game.tick(0.05)
	GameEvents.flush()
	check(heard.search != "" and (heard.search == "?" or Game.account.codex.has(heard.search)), "a searched elite's death gives up a soul memory (%s)" % heard.search)
	# Soul Lantern Ward: a shield of 10% max HP for 6 s (P12: a share of the pool Might scales, as blows scale).
	c.pools.shield = 0.0
	if c.pools.max_soul <= 0.0: c.pools.max_soul = 100.0
	Game.combat._resolve_technique(c, ContentDB.entry("techniques", "soul_lantern_ward"))
	check(near(c.pools.shield, c.pools.max_hp * 0.1, 0.5), "Soul Lantern Ward shields 10%% of max HP (%.1f)" % c.pools.shield)
	for i in 130: Game.tick(0.05)
	check(c.pools.shield == 0.0, "and fades after 6 s")
	# The Poison Body: a poison art known and toxicity past half its tolerance turns hits into poison.
	var tol: float = c.stats.value("toxicity_tolerance")
	c.cultivator.techniques_known.erase("venom_needles")
	c.cultivator.toxicity = tol * 0.8
	check(not Game.combat.poison_body_active(c), "no Poison Body without a poison art")
	c.cultivator.techniques_known.append("venom_needles")
	check(Game.combat.poison_body_active(c), "a poison art and toxicity past half open the Poison Body")
	var pf: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	var tx0: float = c.cultivator.toxicity
	Game.combat._poison_body(c, pf)
	check(pf.pools.has_status("poison") and near(c.cultivator.toxicity, tx0 - 1.0, 0.01), "each hit turns a point of toxicity into poison on the foe")
	Game.combat._poison_body(c, pf)
	check(near(c.cultivator.toxicity, tx0 - 1.0, 0.01), "at most once per foe each half second")
	c.cultivator.toxicity = tol * 0.3
	check(not Game.combat.poison_body_active(c), "below half the tolerance it closes")
	pf.alive = false
	var peddler := ContentDB.entry("shops", "night_peddler")
	var sells := []
	for sitem in peddler.get("stock", []):
		if str(sitem.get("item", "")) == "technique_manual": sells.append(str(sitem.learn))
	check("venom_needles" in sells and "miasma_palm" in sells, "the night peddler sells both poison arts")
	GameEvents.event.disconnect(listen)
	c.cultivator.meridians = meridians_before
	c.cultivator.techniques_known = known_before
	c.cultivator.toxicity = tox_before
	c.cooldowns.erase("free_reroll_wk")
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 the Blood path and the Buddhist path (v1.1)
func blood_buddhist_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	Unlocks.force_unlock(c.id, "vows")
	var realm_before: String = c.cultivator.realm_key
	var align_before: int = c.relations.alignment
	var merit_before: int = c.relations.merit
	var hd_before: float = c.cultivator.heart_demon
	var vows_before: Array = c.cultivator.vows.duplicate()
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var slot_before = c.cultivator.technique_slots[0]
	var ts_before: Dictionary = c.training_sect.duplicate(true)
	var daos_had_blood: bool = c.cultivator.daos.has("blood")
	if ProgressionRules.realm_index(c.cultivator.realm_key) < ProgressionRules.realm_index("heart_tempering_1"): c.cultivator.realm_key = "heart_tempering_1"
	if str(c.training_sect.get("id", "")) == "": c.training_sect = {"id": "jade_sect", "rank": "outer_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	var sect := str(c.training_sect.id)
	var heard := {"path": 0}
	var listen := func(n: String, _p: Dictionary):
		if n == "path_changed": heard.path = int(heard.path) + 1
	GameEvents.event.connect(listen)
	# The Blood path: an opt-in for a demonic heart.
	c.cultivator.paths.erase("blood")
	c.relations.alignment = 0
	var r0 := Game.submit({"type": "set_path", "path": "blood", "on": true})
	check(not r0.get("ok", false) and str(r0.get("reason", "")) == "alignment", "a righteous or neutral heart cannot take the Blood path")
	c.relations.alignment = -30
	var rep0 := int(c.training_sect.get("reputation", {}).get(sect, 0))
	var r1 := Game.submit({"type": "set_path", "path": "blood", "on": true})
	GameEvents.flush()
	check(r1.get("ok", false) and ProgressionAuthority.walks(c, "blood") and int(heard.path) == 1, "at alignment -30 the Blood path is taken (%s)" % str(r1))
	check(c.relations.alignment == -40 and int(c.training_sect.reputation.get(sect, 0)) == rep0 - 20 and c.cultivator.daos.has("blood"),
		"taking it costs 10 alignment and 20 sect regard, and opens the Blood Dao")
	var snap: Dictionary = JSON.parse_string(JSON.stringify(c.cultivator.snapshot()))
	var copy := CultivatorState.new()
	copy.restore(snap)
	check(bool(copy.paths.get("blood", false)), "the path survives a save")
	c.cultivator.heart_demon = 10.0
	Game.progression.apply_heart_demon(c.id, 5.0, "test")
	check(near(c.cultivator.heart_demon, 20.0, 0.01), "on the Blood path the heart demon grows twice as fast")
	# Blood arts: health for power; blood essence pays first; the sect's regard falls with each.
	if not c.cultivator.techniques_known.has("crimson_palm"): c.cultivator.techniques_known.append("crimson_palm")
	c.cultivator.technique_slots[0] = "crimson_palm"
	_idle_hands(c)
	c.pools.hp = c.pools.max_hp
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:crimson_palm")
	Game.combat.blood_essence.erase(c.id)
	var rep1 := int(c.training_sect.reputation.get(sect, 0))
	var u1 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(u1.get("ok", false) and near(c.pools.hp, c.pools.max_hp * 0.95, 1.0), "Crimson Palm costs 5%% of health (%s)" % str(u1))
	check(int(c.training_sect.reputation.get(sect, 0)) == rep1 - 1, "and a point of the sect's regard")
	_idle_hands(c)
	c.pools.hp = c.pools.max_hp
	c.pools.cooldowns.erase("tech:crimson_palm")
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": false, "role": "normal"})
	check(near(Game.combat.essence_of(c.id), 10.0, 0.01), "a kill gives 10 blood essence")
	Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(near(c.pools.hp, c.pools.max_hp, 1.0) and near(Game.combat.essence_of(c.id), 5.0, 0.01), "blood essence pays the art's cost first")
	_idle_hands(c)
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": true, "role": "elite"})
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": false, "role": "boss"})
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": false, "role": "boss"})
	check(near(Game.combat.essence_of(c.id), 100.0, 0.01), "elites give 25, bosses 50, up to 100")
	Game.combat.blood_essence[c.id].t = Game.sim_time - 30.0
	for i in 20: Game.tick(0.05)
	check(Game.combat.essence_of(c.id) < 99.0, "unfed for 20 s, it drains")
	# Lifesteal: 3% (+1% a Blood Dao tier), twice that for a Blood art.
	c.cultivator.daos["blood"] = {"tier": 0, "insight": 0.0}
	check(near(Game.combat.blood_lifesteal(c), 0.03, 0.0001), "lifesteal is 3% at Blood Dao tier 0")
	c.pools.hp = c.pools.max_hp * 0.5
	var h0: float = c.pools.hp
	Game.combat._lifesteal(c, 1000.0, {"source": "basic"})
	check(near(c.pools.hp - h0, 30.0, 0.5), "a 1000 blow drinks back 30 health")
	h0 = c.pools.hp
	Game.combat._lifesteal(c, 1000.0, {"technique": "crimson_palm"})
	check(near(c.pools.hp - h0, 60.0, 0.5), "a Blood art drinks back twice that")
	# The sect's regard below zero closes the Mission Hall's manuals.
	c.training_sect.reputation[sect] = -5
	var hall := ContentDB.entry("shops", sect)
	var gated := {}
	for sitem in hall.get("stock", []):
		if str(sitem.get("item", "")) == "technique_manual" and str(sitem.get("learn", "")) == "tiger_rush": gated = sitem.get("requires", {})
	check(not gated.is_empty() and not RequirementRules.passes(gated, Game.ctx(c)), "with the sect's regard below zero the Mission Hall lends no manuals")
	c.training_sect.reputation[sect] = 10
	check(RequirementRules.passes(gated, Game.ctx(c)) or ProgressionRules.realm_index(c.cultivator.realm_key) < ProgressionRules.realm_index("qi_kindling_5"), "and at 10 it does again")
	# Leaving the path marks the heart.
	c.cultivator.heart_demon = 0.0
	var off := Game.submit({"type": "set_path", "path": "blood", "on": false})
	GameEvents.flush()
	check(off.get("ok", false) and not ProgressionAuthority.walks(c, "blood") and near(c.cultivator.heart_demon, 10.0, 0.01), "leaving the Blood path adds 10 heart demon")
	_idle_hands(c)
	c.pools.cooldowns.erase("tech:crimson_palm")
	var u3 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(str(u3.get("reason", "")) == "needs_blood_path", "off the path, Blood arts cannot be used")
	# The Buddhist path: merit milestones calm a vow-keeper's heart; healing allies is merit; the Golden Body needs a vow.
	c.cultivator.vows.clear()
	c.cultivator.heart_demon = 30.0
	c.relations.merit = 95
	Game.relations.apply_karma(c.id, 10, 0, "test")
	check(near(c.cultivator.heart_demon, 30.0, 0.01), "without a vow, merit milestones do not calm the heart")
	Game.submit({"type": "set_vow", "vow": "mercy", "on": true})
	c.relations.merit = 195
	Game.relations.apply_karma(c.id, 10, 0, "test")
	check(near(c.cultivator.heart_demon, 20.0, 0.01), "a vow-keeper crossing 200 merit loses 10 heart demon")
	var ally: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-60, 0), 5)
	ally.team = "ally"
	for k in c.relations.deeds.keys():
		if str(k).begins_with("heal_ally:"): c.relations.deeds.erase(k)
	var m0: int = c.relations.merit
	for i in 7: Game.combat.heal_circle(c, 0.01, 1.0, 220.0, "test")
	check(c.relations.merit == m0 + 5, "healing an ally is merit, five times a day (%d)" % (c.relations.merit - m0))
	ally.alive = false
	Game.combat.ally_hots.clear()
	if not c.cultivator.techniques_known.has("golden_body"): c.cultivator.techniques_known.append("golden_body")
	c.cultivator.technique_slots[0] = "golden_body"
	c.cultivator.vows.clear()
	_idle_hands(c)
	c.pools.composure = 100.0
	c.pools.cooldowns.erase("tech:golden_body")
	var g0 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(str(g0.get("reason", "")) == "needs_vow", "the Golden Body answers only a vow-keeper")
	c.cultivator.vows.append("plain_fare")
	var def0: float = c.stats.value("physical_defense")
	Game.combat._resolve_technique(c, ContentDB.entry("techniques", "golden_body"))
	check(c.stats.value("physical_defense") > def0 * 1.2, "the Golden Body hardens the body (+25%% defence: %.0f -> %.0f)" % [def0, c.stats.value("physical_defense")])
	# Where the arts are found.
	var peddler := ContentDB.entry("shops", "night_peddler")
	var blood_ok := 0
	for sitem in peddler.get("stock", []):
		if str(sitem.get("learn", "")) in ["crimson_palm", "blood_river_slash", "sanguine_lotus"]:
			for cond in sitem.get("requires", {}).get("all", []):
				if str(cond.get("kind", "")) == "alignment_at_most": blood_ok += 1
	check(blood_ok == 3, "the night peddler sells the three Blood arts to the demonic side only")
	var gb := false
	for sitem in ContentDB.entry("shops", "cloud_sect").get("stock", []):
		if str(sitem.get("learn", "")) == "golden_body": gb = true
	check(gb, "the Cloud Mission Hall lends the Golden Body")
	GameEvents.event.disconnect(listen)
	for m in c.stats.modifiers.duplicate():
		if str(m.get("source", "")).begins_with("tech:golden_body"): c.stats.remove_source(str(m.source))
	c.cultivator.paths.erase("blood")
	c.cultivator.realm_key = realm_before
	c.relations.alignment = align_before
	c.relations.merit = merit_before
	c.cultivator.heart_demon = hd_before
	c.cultivator.vows = vows_before
	c.cultivator.techniques_known = known_before
	c.cultivator.technique_slots[0] = slot_before
	c.training_sect = ts_before
	if not daos_had_blood: c.cultivator.daos.erase("blood")
	Game.combat.blood_essence.erase(c.id)
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 sect role variants and the sect tree (v0.9)
func sect_roles_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	var ts_before: Dictionary = c.training_sect.duplicate(true)
	var prof_before: Dictionary = c.professions.duplicate(true)
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var slot_before = c.cultivator.technique_slots[0]
	c.training_sect = {"id": "jade_sect", "rank": "service_disciple", "contribution": 2000, "reputation": {"jade_sect": 10}}
	var heard := {"role": 0, "node": 0}
	var listen := func(n: String, _p: Dictionary):
		if n == "sect_role_chosen": heard.role = int(heard.role) + 1
		if n == "sect_node_bought": heard.node = int(heard.node) + 1
	GameEvents.event.connect(listen)
	var r0 := Game.submit({"type": "set_sect_role", "role": "damage"})
	check(str(r0.get("reason", "")) == "rank", "a service disciple has no sect role yet")
	c.training_sect.rank = "outer_disciple"
	var r1 := Game.submit({"type": "set_sect_role", "role": "damage"})
	GameEvents.flush()
	check(r1.get("ok", false) and str(c.training_sect.role) == "damage" and int(c.training_sect.contribution) == 2000 and int(heard.role) == 1, "the first role is free")
	var v := ProgressionRules.signature_variant(c, "flowing_palm")
	check(near(float(v.get("mult", 0.0)), 0.25, 0.001) and ProgressionRules.signature_variant(c, "tiger_rush").is_empty(), "the damage variant touches only the signature line")
	var r2 := Game.submit({"type": "set_sect_role", "role": "support"})
	check(r2.get("ok", false) and int(c.training_sect.contribution) == 1950, "changing it costs 50 contribution")
	# The support variant heals on use, and grows with the crafts ranked up.
	c.professions = {}
	var m0: float = Game.combat.sect_support_mult(c)
	c.professions = {"healing": {"rank": "adept", "xp": 0.0}}
	check(near(m0, 1.0, 0.001) and Game.combat.sect_support_mult(c) > m0, "support healing grows with the crafts (%.2f)" % Game.combat.sect_support_mult(c))
	c.professions = {}
	if not c.cultivator.techniques_known.has("flowing_palm"): c.cultivator.techniques_known.append("flowing_palm")
	c.cultivator.technique_slots[0] = "flowing_palm"
	_idle_hands(c)
	c.pools.hp = c.pools.max_hp * 0.5
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:flowing_palm")
	var h0: float = c.pools.hp
	var u1 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(u1.get("ok", false) and c.pools.hp >= h0 + c.pools.max_hp * 0.039, "Mending Current heals the user by 4%% (%s)" % str(u1))
	_idle_hands(c)
	# The tree: bought in order with contribution; later nodes need a higher rank.
	var atk0: float = c.stats.value("physical_attack")
	var b1 := Game.submit({"type": "buy_sect_node", "branch": "edge"})
	GameEvents.flush()
	check(b1.get("ok", false) and int(c.training_sect.contribution) == 1890 and c.stats.value("physical_attack") > atk0 * 1.025 and int(heard.node) == 1,
		"the first Edge node costs 60 and adds 3%% attack (%.0f -> %.0f)" % [atk0, c.stats.value("physical_attack")])
	Game.submit({"type": "buy_sect_node", "branch": "edge"})
	var b3 := Game.submit({"type": "buy_sect_node", "branch": "edge"})
	check(str(b3.get("reason", "")) == "rank", "the third node waits for Inner Disciple")
	c.training_sect.rank = "core_disciple"
	for i in 3: Game.submit({"type": "buy_sect_node", "branch": "edge"})
	var b6 := Game.submit({"type": "buy_sect_node", "branch": "edge"})
	check(int(c.training_sect.tree.edge) == 5 and str(b6.get("reason", "")) == "complete", "a branch has five nodes")
	check(near(ProgressionRules.sect_tree_flag(c, "signature_cooldown"), -1.0, 0.001) and near(ProgressionRules.sect_tree_flag(c, "signature_mult"), 0.15, 0.001),
		"the Edge branch's flags add up")
	c.pools.cooldowns.erase("tech:flowing_palm")
	c.pools.qi = c.pools.max_qi
	Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(near(c.pools.cooldown("tech:flowing_palm"), float(ContentDB.entry("techniques", "flowing_palm").cooldown_s) - 1.0, 0.05), "signature arts are ready a second sooner")
	_idle_hands(c)
	c.training_sect.contribution = 0
	var b7 := Game.submit({"type": "buy_sect_node", "branch": "root"})
	check(str(b7.get("reason", "")) == "contribution", "no contribution, no node")
	# The Cloud support variant is a shield.
	c.training_sect = {"id": "cloud_sect", "rank": "outer_disciple", "contribution": 100, "reputation": {"cloud_sect": 10}, "role": "support"}
	c.pools.shield = 0.0
	Game.combat._sect_support(c, ProgressionRules.signature_variant(c, "jade_thrust"))
	check(near(c.pools.shield, c.pools.max_hp * 0.08, 1.0), "Guarding Cloud shields 8% of health")
	GameEvents.event.disconnect(listen)
	c.pools.shield = 0.0
	c.training_sect = ts_before
	c.professions = prof_before
	c.cultivator.techniques_known = known_before
	c.cultivator.technique_slots[0] = slot_before
	Game.combat.refresh_stats(c.id)


# ------------------------------------------------------------------ S47/S48 v1.1: the sword swarm, Array Plates in a fight, the combat puppet
func swarm_array_puppet_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	var daos_before: Dictionary = c.cultivator.daos.duplicate(true)
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var meridians_before: Dictionary = c.cultivator.meridians.duplicate()
	var treasures_before: Array = c.inventory.treasures.duplicate()
	var lv := ProgressionRules.level(c) + 12
	var heard := {"released": 0, "returned": "", "deployed": 0, "faded": 0}
	var listen := func(n: String, p: Dictionary):
		if n == "sword_released" and int(p.get("swarm", 0)) > 0: heard.released = int(p.swarm)
		if n == "sword_returned" and p.get("swarm", false): heard.returned = str(p.get("reason", ""))
		if n == "array_deployed": heard.deployed = int(heard.deployed) + 1
		if n == "array_faded": heard.faded = int(heard.faded) + 1
	GameEvents.event.connect(listen)
	# The swarm: 3 swords at Sword Dao 5, 9 with the Nine Swords Array, 36 with it at tier 6; one sword per 10 Spirit.
	c.cultivator.meridians["spirit"] = 100
	Game.combat.refresh_stats(c.id)
	var cap := int(floor(c.stats.value("spirit") / 10.0))
	c.cultivator.daos["sword"] = {"tier": 4, "insight": 0.0}
	check(Game.combat.swarm_count(c, false) == 0, "no swarm below Sword Dao 5")
	c.cultivator.daos["sword"] = {"tier": 5, "insight": 0.0}
	check(Game.combat.swarm_count(c, false) == mini(3, cap), "Sword Dao 5: three swords (%d)" % Game.combat.swarm_count(c, false))
	check(Game.combat.swarm_count(c, true) == mini(9, cap), "released from the Nine Swords Array: nine (%d)" % Game.combat.swarm_count(c, true))
	c.inventory.treasures[0] = "nine_sword_array"
	check(Game.combat.swarm_count(c, false) == mini(9, cap), "the Array set in a Treasure slot lifts the Dao swarm to nine")
	c.cultivator.daos["sword"] = {"tier": 6, "insight": 0.0}
	check(Game.combat.swarm_count(c, false) == mini(36, cap) and cap < 36, "Original Application: 36, held to what Spirit can steer (%d of %d)" % [Game.combat.swarm_count(c, false), cap])
	c.inventory.treasures = treasures_before.duplicate()
	c.cultivator.meridians["spirit"] = 0
	Game.combat.refresh_stats(c.id)
	var low := maxi(1, int(floor(c.stats.value("spirit") / 10.0)))
	check(low < cap and Game.combat.swarm_count(c, true) == mini(36, low), "less Spirit steers fewer swords (%d)" % Game.combat.swarm_count(c, true))
	c.cultivator.meridians["spirit"] = 100
	Game.combat.refresh_stats(c.id)
	# Sword Dao tier 5 teaches the Sword Swarm.
	c.cultivator.techniques_known.erase("sword_swarm")
	c.cultivator.daos["sword"] = {"tier": 0, "insight": 0.0}
	var need := 0.0
	for t in 400:
		if ProgressionRules.dao_tier_for(need) >= 5: break
		need += 50.0
	Game.progression.apply_insight(c.id, "sword", need + 1.0, "teacher:test")
	check(c.cultivator.techniques_known.has("sword_swarm"), "Sword Dao tier 5 teaches the Sword Swarm (tier %d)" % int(c.cultivator.daos.sword.tier))
	# The technique toggles the swarm, pays QI, and the swords strike a foe nearby on their own.
	c.cultivator.daos["sword"] = {"tier": 5, "insight": 0.0}
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(160, 0), lv)
	foe.pools.max_hp = 999999.0
	foe.pools.hp = 999999.0
	foe.stats["evasion"] = 0.0
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:sword_swarm")
	var qi0: float = c.pools.qi
	var sw := Game.combat.toggle_sword_swarm(c, ContentDB.entry("techniques", "sword_swarm"))
	GameEvents.flush()
	check(sw.get("ok", false) and Game.combat.swarm_of(c.id) == mini(3, cap) and heard.released == Game.combat.swarm_of(c.id) and c.pools.qi < qi0,
		"the Sword Swarm rises for QI (%s)" % str(sw))
	for i in 50:
		Game.tick(0.05)
		foe.plane = st.plane + Vector2(160, 0)
	check(foe.pools.hp < 999999.0, "the swarm strikes a foe nearby without a button (%.0f lost)" % (999999.0 - foe.pools.hp))
	var off := Game.combat.toggle_sword_swarm(c, ContentDB.entry("techniques", "sword_swarm"))
	GameEvents.flush()
	check(off.get("ok", false) and Game.combat.swarm_of(c.id) == 0 and heard.returned == "recalled", "pressed again, the swords come home")
	Game.combat.start_swarm(c, true, 0.5)
	for i in 14: Game.tick(0.05)
	GameEvents.flush()
	check(Game.combat.swarm_of(c.id) == 0 and heard.returned == "time", "the swarm returns when its time is up")
	Game.inventory.apply_add(c.id, "nine_sword_array", 1, "test")
	Unlocks.force_unlock(c.id, "treasures")
	c.inventory.treasures[0] = "nine_sword_array"
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.clear()
	var tr := Game.submit({"type": "use_treasure", "slot": 0})
	check(tr.get("ok", false) and Game.combat.swarm_of(c.id) == mini(9, cap), "the Nine Swords Array, released, orbits nine swords (%s)" % str(tr))
	Game.combat._end_swarm(c, "recalled")
	c.inventory.treasures = treasures_before.duplicate()
	Game.inventory.apply_remove(c.id, "nine_sword_array", 1, "test")
	c.cultivator.daos["sword"] = daos_before.get("sword", {"tier": 0, "insight": 0.0})
	# Array Plates: each lays an array at your feet; the Formation Dao lengthens them and sharpens the killing array.
	c.cultivator.daos["formation"] = {"tier": 0, "insight": 0.0}
	Game.combat.arrays.clear()
	var def0: float = c.stats.value("physical_defense")
	Game.inventory.apply_add(c.id, "array_plate", 1, "test")
	var ins0 := float(c.cultivator.daos.formation.get("insight", 0.0))
	var u := Game.submit({"type": "use_item", "index": c.inventory.first_index("array_plate")})
	GameEvents.flush()
	check(u.get("ok", false) and Game.combat.arrays.size() == 1 and str(Game.combat.arrays[0].kind) == "guard" and near(float(Game.combat.arrays[0].t), 12.0, 0.01)
		and int(heard.deployed) == 1, "an Array Plate lays a guarding array for 12 s (%s)" % str(u))
	check(float(c.cultivator.daos.formation.get("insight", 0.0)) > ins0, "each plate teaches the Formation Dao a little")
	for i in 3: Game.tick(0.05)
	check(c.stats.value("physical_defense") > def0 * 1.1, "inside its ring, Physical Defense rises (%.0f -> %.0f)" % [def0, c.stats.value("physical_defense")])
	Game.combat.arrays[0].t = 0.05
	for i in 3: Game.tick(0.05)
	GameEvents.flush()
	check(Game.combat.arrays.is_empty() and int(heard.faded) == 1, "the array fades when its time is up")
	var k: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	k.pools.max_hp = 999999.0
	k.pools.hp = 999999.0
	k.stats["evasion"] = 0.0
	Game.combat.deploy_array(c.id, {"array": "killing", "radius": 160, "duration": 10, "mult": 0.5})
	var m0 := float(Game.combat.arrays[-1].mult)
	for i in 25:
		Game.tick(0.05)
		k.plane = st.plane + Vector2(60, 0)
	check(k.pools.hp < 999999.0, "a killing array wounds every foe inside it (%.0f lost)" % (999999.0 - k.pools.hp))
	Game.combat.deploy_array(c.id, {"array": "binding", "radius": 160, "duration": 10, "slow": 0.4})
	for i in 12:
		Game.tick(0.05)
		k.plane = st.plane + Vector2(60, 0)
	check(k.pools.has_status("slow"), "a binding array slows every foe inside it")
	k.alive = false
	Game.combat.arrays.clear()
	c.cultivator.daos["formation"] = {"tier": 2, "insight": 0.0}
	Game.combat.deploy_array(c.id, {"array": "killing", "radius": 160, "duration": 10, "mult": 0.5})
	check(near(float(Game.combat.arrays[-1].mult), m0 * 1.4, 0.001) and near(float(Game.combat.arrays[-1].t), 11.0, 0.01),
		"Formation Dao 2: the killing array hits 40% harder and holds a tenth longer")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	GameEvents.flush()
	check(Game.combat.arrays.is_empty(), "arrays stay in the room they were laid in")
	c.cultivator.daos["formation"] = daos_before.get("formation", {"tier": 0, "insight": 0.0})
	# The combat puppet: built at the tinkerer's bench, takes a pet slot, one only; a construct that is repaired, not healed.
	var pets_before: Array = c.pets.duplicate(true)
	var active_before: String = c.active_pet
	var party_before: Array = c.party_pets.duplicate()
	c.pets = c.pets.filter(func(p): return str(p.species) != "combat_puppet")
	Unlocks.force_unlock(c.id, "puppetry")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	for it in [["spirit_wood", 8], ["puppet_core", 2], ["jadeiron", 4]]: Game.inventory.apply_add(c.id, str(it[0]), int(it[1]), "test")
	var wood0: int = c.inventory.count("spirit_wood")
	var b := Game.submit({"type": "build_puppet", "blueprint": "combat_puppet"})
	var pup := {}
	for p in c.pets:
		if str(p.species) == "combat_puppet": pup = p
	check(b.get("ok", false) and not pup.is_empty() and PetAuthority.is_construct(pup) and str(pup.stage) == "adult" and (pup.traits as Array).is_empty()
		and c.inventory.count("spirit_wood") == wood0 - 8, "the tinkerer builds a combat puppet into a pet slot (%s)" % str(b))
	for it in [["spirit_wood", 8], ["puppet_core", 2], ["jadeiron", 4]]: Game.inventory.apply_add(c.id, str(it[0]), int(it[1]), "test")
	check(str(Game.submit({"type": "build_puppet", "blueprint": "combat_puppet"}).get("reason", "")) == "one_puppet", "only one combat puppet")
	Game.inventory.apply_add(c.id, "roast_fish", 1, "test")
	check(str(Game.submit({"type": "feed_pet", "pet": str(pup.uid), "item": "roast_fish"}).get("reason", "")) == "construct", "a puppet does not eat")
	check(str(Game.submit({"type": "set_pet_role", "pet": str(pup.uid), "role": "gatherer"}).get("reason", "")) == "construct", "a puppet only fights")
	check(Game.pets.breed_partners(c, pup).is_empty() and not Game.pets.can_evolve(c, pup), "a puppet neither breeds nor grows")
	pup.wounded = true
	Game.pets.heal_wound(c.id)
	check(pup.wounded, "a Beast Revival Pill or rest does not mend a puppet")
	for it in [["spirit_wood", c.inventory.count("spirit_wood")]]: Game.inventory.apply_remove(c.id, str(it[0]), int(it[1]), "test")
	check(str(Game.submit({"type": "repair_puppet"}).get("reason", "")) == "materials", "a repair needs spirit wood")
	Game.inventory.apply_add(c.id, "spirit_wood", 2, "test")
	var rp := Game.submit({"type": "repair_puppet"})
	check(rp.get("ok", false) and not pup.wounded and c.inventory.count("spirit_wood") == 0, "the tinkerer repairs it for two spirit wood (%s)" % str(rp))
	check(str(Game.submit({"type": "repair_puppet"}).get("reason", "")) == "whole", "a whole puppet needs no repair")
	for it in ["puppet_core", "jadeiron", "roast_fish"]: Game.inventory.apply_remove(c.id, it, c.inventory.count(it), "test")
	c.pets = pets_before
	c.active_pet = active_before
	c.party_pets = party_before
	Game.world.apply_teleport(c.id, "wp_west")
	GameEvents.event.disconnect(listen)
	c.cultivator.daos = daos_before
	c.cultivator.techniques_known = known_before
	c.cultivator.meridians = meridians_before
	c.inventory.treasures = treasures_before
	Game.combat.refresh_stats(c.id)


# ------------------------------------------------------------------ S47 Artifact Spirit depth (v1.0) and imitation relics (v1.1)
func artifact_spirit_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	GameEvents.flush()
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	var held = c.inventory.equipped.get("weapon")
	var flags_before: Dictionary = c.quests.flags.duplicate()
	var lv := ProgressionRules.level(c) + 12
	var heard := {"skill": 0, "spoke": [], "grew": 0, "aff": 0}
	var listen := func(n: String, p: Dictionary):
		if n == "artifact_skill_used": heard.skill = int(heard.skill) + 1
		if n == "artifact_spirit_spoke": heard.spoke.append(str(p.get("kind", "")))
		if n == "artifact_spirit_grew": heard.grew = int(p.get("level", 0))
		if n == "spirit_affinity_changed": heard.aff = int(heard.aff) + 1
	GameEvents.event.connect(listen)
	# A bound Sleeping Blade in hand, its spirit asleep.
	var blade := LootRules.make_instance("sleeping_blade", 52, "fine", null, c.inventory.next_uid)
	c.inventory.next_uid += 1
	blade.erase("sealed")
	blade.bound = true
	c.inventory.equipped["weapon"] = blade
	Game.combat.refresh_stats(c.id)
	check(str(blade.spirit) == "dormant" and InventoryAuthority.spirit_weapon(c) == blade, "a bound relic in hand carries a sleeping spirit")
	# Use: a point of affinity for every 25 blows the blade lands.
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	foe.pools.max_hp = 999999.0
	foe.pools.hp = 999999.0
	var atk := {"damage_type": "physical", "element": "none", "mult": [0.01, 0.01], "range": [1.0, 1.0], "source": "basic", "never_miss": true}
	for i in 25: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(near(float(blade.get("spirit_affinity", 0.0)), 1.0), "25 blows with it: one point of affinity (%.1f)" % float(blade.get("spirit_affinity", 0.0)))
	# Gifts: three a day; its favourite counts double; it will not take just anything.
	check(str(Game.submit({"type": "gift_spirit", "item": "rice"}).get("reason", "")) == "not_a_gift", "the spirit will not take just anything")
	Game.inventory.apply_add(c.id, "refining_essence", 4, "test")
	var g1 := Game.submit({"type": "gift_spirit", "item": "refining_essence"})
	check(g1.get("ok", false) and near(float(g1.get("worth", 0.0)), 20.0) and "gift" in heard.spoke, "its favourite gift is worth 20, and it thanks you (%s)" % str(g1))
	Game.submit({"type": "gift_spirit", "item": "refining_essence"})
	Game.submit({"type": "gift_spirit", "item": "refining_essence"})
	check(str(Game.submit({"type": "gift_spirit", "item": "refining_essence"}).get("reason", "")) == "full", "three gifts a day")
	check(c.quests.has_flag("spirit_close:sleeping_blade"), "past affinity 30, its awakening quest moves on")
	# Waking: only where it slept.
	Game.inventory.spirit_cd.erase(c.id)
	check(str(Game.submit({"type": "subdue_spirit", "slot": "weapon"}).get("reason", "")) == "place", "it will not wake away from its resting place")
	Game.world.apply_teleport(c.id, "ds_abbots_sanctum")
	GameEvents.flush()
	for i in 12:
		Game.inventory.spirit_cd.erase(c.id)
		if Game.submit({"type": "subdue_spirit", "slot": "weapon"}).get("awake", false): break
	GameEvents.flush()
	check(str(blade.spirit) == "awake" and c.quests.has_flag("spirit_awake:sleeping_blade") and "awake" in heard.spoke, "it wakes in the Abbot's sanctum, and speaks")
	# Its gift grows with affinity: +10% crit damage at up to one and a half times.
	var p0 := StatRules.spirit_power(c, blade)
	var aff0 := float(blade.spirit_affinity)
	check(near(p0, 1.0 + 0.5 * aff0 / 100.0, 0.001), "the gift grows with affinity (x%.2f at %d)" % [p0, int(aff0)])
	# Devour: a weaker jian of its kind grows the spirit; a spear or a locked jian is not food.
	for i in 3: Game.inventory.apply_add_equipment(c.id, "iron_jian", 10, "common", "test")
	Game.inventory.apply_add_equipment(c.id, "iron_spear", 10, "common", "test")
	var foods: Array = Game.inventory.devour_candidates(c)
	var kinds := {}
	for i in foods: kinds[str(c.inventory.bag[int(i)].id)] = true
	check(kinds.has("iron_jian") and not kinds.has("iron_spear"), "only weaker blades of its own family are food")
	var lock_uid := int(c.inventory.bag[int(foods[0])].uid)
	c.inventory.locked[lock_uid] = true
	check(Game.inventory.devour_candidates(c).size() == foods.size() - 1, "a locked blade is never eaten")
	c.inventory.locked.erase(lock_uid)
	var crit0: float = c.stats.value("crit_damage")
	for i in 3:
		var cand: Array = Game.inventory.devour_candidates(c)
		var dv := Game.submit({"type": "devour_gear", "index": int(cand[0])})
		check(dv.get("ok", false), "devour %d (%s)" % [i + 1, str(dv)])
	GameEvents.flush()
	check(int(blade.get("spirit_level", 0)) == 1 and heard.grew == 1 and c.stats.value("crit_damage") > crit0, "three iron jian: the spirit grows to level 1 and its gift with it")
	# Its skill: every tenth blow of the blade the Waking Edge strikes on its own; a hand too weak to control it gets none.
	Game.combat.spirit_hits.erase(c.id)
	heard.skill = 0
	for i in 10: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(int(heard.skill) == 1, "the Waking Edge strikes on the tenth blow (%d)" % int(heard.skill))
	c.stats.add_modifier({"stat": "spirit", "op": "flat", "value": -99999.0, "duration": 30.0, "source": "test:weak"})
	Game.combat.refresh_stats(c.id)
	check(not StatRules.spirit_controlled(c, blade) and near(StatRules.spirit_power(c, blade), StatRules.spirit_power(null, blade) * 0.5, 0.001),
		"below its control demand the spirit gives half")
	heard.skill = 0
	for i in 10: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(int(heard.skill) == 0, "and keeps its skill to itself")
	c.stats.remove_prefix("test:weak")
	Game.combat.refresh_stats(c.id)
	# Barks wait out a quiet between them (chosen lines excepted).
	Game.inventory.bark_at.erase(c.id)
	heard.spoke = []
	Game.inventory.speak(c, blade, "kill")
	Game.inventory.speak(c, blade, "kill")
	GameEvents.flush()
	check(heard.spoke.size() == 1, "barks keep a quiet between them (%d)" % heard.spoke.size())
	foe.alive = false
	# Imitation relics: 60% of the original's gift, always on, no spirit; the smith copies a relic seen whole.
	var im := ContentDB.item("moonshadow_jian")
	var orig: Dictionary = ContentDB.item("moonlit_blade").spirit.effect
	check(near(float(im.imitation.effect.value), float(orig.value) * 0.6, 0.0001) and not im.get("relic", false) and not im.has("spirit"),
		"the Moonshadow Jian keeps 60% of the Moonlit Blade's gift, with no spirit")
	var copy := LootRules.make_instance("moonshadow_jian", 48, "common", null, 1)
	var mods := StatRules.instance_modifiers("weapon", copy, c.cultivator.energy_type, c)
	check(mods.any(func(m): return str(m.source).begins_with("imitation") and str(m.stat) == "qi_attack" and near(float(m.value), 0.048, 0.0001)) and not copy.get("sealed", false),
		"an imitation needs no binding: +4.8% Qi attack")
	var smith := ContentDB.entry("shops", "stoneford_smith")
	var scroll_req := {}
	for it in smith.get("stock", []):
		if str(it.get("learn", "")) == "moonshadow_jian": scroll_req = it.get("requires", {})
	check(str(ContentDB.entry("recipes", "moonshadow_jian").get("requires_ranks", {}).get("smithing", "")) == "expert"
		and JSON.stringify(scroll_req).contains("bound:moonlit_blade"), "Expert smiths copy it, once the Moonlit Blade has been bound")
	GameEvents.event.disconnect(listen)
	for it in ["iron_jian", "iron_spear", "refining_essence"]: Game.inventory.apply_remove(c.id, it, c.inventory.count(it), "test")
	c.inventory.equipped["weapon"] = held
	c.quests.flags = flags_before
	Game.world.apply_teleport(c.id, "wp_west")
	GameEvents.flush()
	Game.combat.refresh_stats(c.id)


# ------------------------------------------------------------------ S47 weapon awakening and legendary chains (v1.1+)
func awaken_legend_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	var held = c.inventory.equipped.get("weapon")
	var daos_before: Dictionary = c.cultivator.daos.duplicate(true)
	var flags_before: Dictionary = c.quests.flags.duplicate()
	Unlocks.force_unlock(c.id, "smithing")
	var heard := {"awoke": "", "skills": 0, "ring": 0.0}
	var listen := func(n: String, p: Dictionary):
		if n == "weapon_awakened": heard.awoke = str(p.get("skill", ""))
		if n == "artifact_skill_used" and p.get("awakened", false):
			heard.skills = int(heard.skills) + 1
			heard.ring = float(p.get("ring", 0.0))
	GameEvents.event.connect(listen)
	# The gates: Heaven grade or better, +10, the family's Dao at Explanation, a crystal, and a forge.
	Game.inventory.apply_add_equipment(c.id, "cloudsteel_jian", 45, "common", "test")
	var ji: int = c.inventory.first_index("cloudsteel_jian")
	var jian: Dictionary = c.inventory.bag[ji]
	jian.enhance = 9
	c.cultivator.daos["sword"] = {"tier": 3, "insight": 0.0}
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	GameEvents.flush()
	st.plane = Vector2(700, 780)
	check(Game.crafting.awaken_check(c, jian) == Tx.t("sim.crafting.awaken_plus10"), "only a weapon at +10 wakes")
	jian.enhance = 10
	check(Game.crafting.awaken_check(c, jian) == Tx.t("sim.crafting.awaken_dao") % ContentDB.name_of("daos", "sword"), "and only for a Sword Dao at Explanation")
	c.cultivator.daos["sword"] = {"tier": 4, "insight": 0.0}
	check(Game.crafting.awaken_check(c, jian) == Tx.t("sim.crafting.awaken_crystal"), "and it takes a Weapon Soul Crystal")
	Game.inventory.apply_add(c.id, "weapon_soul_crystal", 1, "test")
	st.plane = Vector2(2300, 820)
	check(Game.crafting.awaken_check(c, jian) == Tx.t("sim.crafting.you_need_a") % "forge", "at a forge")
	st.plane = Vector2(700, 780)
	Game.inventory.apply_add_equipment(c.id, "jadeiron_jian", 27, "common", "test")
	var earth: Dictionary = c.inventory.bag[c.inventory.first_index("jadeiron_jian")]
	earth.enhance = 10
	check(Game.crafting.awaken_check(c, earth) == Tx.t("sim.crafting.awaken_grade"), "an Earth-grade blade never wakes")
	var aw := Game.submit({"type": "awaken_weapon", "uid": int(jian.uid)})
	GameEvents.flush()
	check(aw.get("ok", false) and jian.get("awakened", false) and heard.awoke == "Sword Light" and c.inventory.count("weapon_soul_crystal") == 0
		and c.quests.has_flag("awakened:cloudsteel_jian"), "a +10 Cloudsteel Jian wakes with Sword Light (%s)" % str(aw))
	check(str(Game.submit({"type": "awaken_weapon", "uid": int(jian.uid)}).get("reason", "")) == "cannot", "a weapon wakes once")
	# Awake, it strikes on its own every twelfth blow of the blade.
	c.inventory.equipped["weapon"] = jian
	c.inventory.bag[c.inventory.find_uid(int(jian.uid))] = null
	Game.combat.refresh_stats(c.id)
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), ProgressionRules.level(c) + 12)
	foe.pools.max_hp = 999999.0
	foe.pools.hp = 999999.0
	var atk := {"damage_type": "physical", "element": "none", "mult": [0.01, 0.01], "range": [1.0, 1.0], "source": "basic", "never_miss": true}
	Game.combat.awaken_hits.erase(c.id)
	for i in 12: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(int(heard.skills) == 1, "an awakened jian's Sword Light strikes on the twelfth blow (%d)" % int(heard.skills))
	# A +10 Heaven piece raises the flag Smith Hong waits on.
	Game.inventory.apply_add_equipment(c.id, "cloudsteel_spear", 45, "common", "test")
	var sp: Dictionary = c.inventory.bag[c.inventory.first_index("cloudsteel_spear")]
	sp.enhance = 9
	sp.pity = 5.0
	c.quests.flags.erase("forged_plus10")
	var cost: Dictionary = Game.crafting.enhance_cost(sp)
	Game.inventory.apply_add(c.id, str(cost.metal), int(cost.count), "test")
	if int(cost.shards) > 0: Game.inventory.apply_add(c.id, "spirit_stone_shard", int(cost.shards), "test")
	Game.economy.apply_currency("silver_tael", int(cost.taels), "test")
	var en := Game.submit({"type": "enhance", "uid": int(sp.uid)})
	check(en.get("ok", false) and int(sp.get("enhance", 0)) == 10 and c.quests.has_flag("forged_plus10"), "forging a Heaven weapon to +10 is what Smith Hong asks (%s)" % str(en))
	# Legendary chains: one per weapon family, three pieces each, an Expert restore and the legend's own skill.
	var chains := ContentDB.all("legendary_chains")
	var fams := {}
	for ch in chains: fams[str(ch.family)] = true
	check(chains.size() == 9 and not fams.has("fists") and fams.has("gauntlets") and fams.has("flute"), "nine legendary chains, one per weapon family (%d)" % chains.size())
	var rd: Dictionary = chains[1]
	var q := ContentDB.entry("quests", str(rd.quest))
	var kinds: Array = q.get("objectives", []).map(func(o): return str(o.kind))
	check(kinds == ["collect", "collect", "collect", "craft", "set_flag"] and str(ContentDB.entry("recipes", str(rd.weapon)).get("requires_ranks", {}).get("smithing", "")) == "expert",
		"a chain: three pieces, an Expert restore, and its awakening (%s)" % str(kinds))
	var src := str(rd.pieces[0].source)
	var pid := str(rd.pieces[0].item)
	var d0 := LootRules.roll(src, Rng.keyed(4242, "legend"), 30, 1.0, 1.0, {"needs": {}})
	var d1 := LootRules.roll(src, Rng.keyed(4242, "legend"), 30, 1.0, 1.0, {"needs": {pid: str(rd.quest)}})
	check(not d0.items.any(func(it): return str(it.item) == pid) and d1.items.any(func(it): return str(it.item) == pid),
		"the %s drops from the %s only while its chain wants it" % [pid, src])
	var legend := LootRules.make_instance(str(chains[0].weapon), 64, "common", null, 1)
	var mods := StatRules.instance_modifiers("weapon", legend, c.cultivator.energy_type, c)
	check(mods.any(func(m): return str(m.source).begins_with("legend")) and str(CraftingAuthority.awakened_skill(str(chains[0].weapon)).get("name", "")) == "Mountain Drum",
		"a legend carries its own gift, and wakes with its own skill")
	# A ring skill: the Stone Drum Gauntlets awake strike every foe around them.
	legend.enhance = 10
	legend.awakened = true
	c.inventory.equipped["weapon"] = legend
	Game.combat.refresh_stats(c.id)
	heard.skills = 0
	Game.combat.awaken_hits.erase(c.id)
	for i in 10: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(int(heard.skills) == 1 and near(heard.ring, 170.0), "the Mountain Drum sounds on the tenth blow, a ring of 170")
	foe.alive = false
	GameEvents.event.disconnect(listen)
	for it in ["cloudsteel_spear", "jadeiron_jian", "cloudsteel_jian", "weapon_soul_crystal", str(cost.metal)]:
		Game.inventory.apply_remove(c.id, it, c.inventory.count(it), "test")
	c.inventory.equipped["weapon"] = held
	c.cultivator.daos = daos_before
	c.quests.flags = flags_before
	Game.world.apply_teleport(c.id, "wp_west")
	GameEvents.flush()
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S47 natal treasure, wardrobe, blood-drop, rogue cultivators
func natal_wardrobe_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Unlocks.force_unlock(c.id, "natal")
	Unlocks.force_unlock(c.id, "wardrobe")
	Game.inventory.apply_add_equipment(c.id, "jadeiron_jian", 27, "common", "test")
	var ji: int = c.inventory.first_index("jadeiron_jian")
	var held_before = c.inventory.equipped.get("weapon")
	var jian: Dictionary = c.inventory.bag[ji]
	c.inventory.equipped["weapon"] = jian
	c.inventory.bag[ji] = held_before
	# Natal: flag it, feed it ore (20 XP a grade step each): 5 Jadeiron -> 300 XP -> natal level 2, +4% stats.
	var mult0: float = StatRules.instance_mult(jian, c.cultivator.energy_type)
	check(Game.submit({"type": "flag_natal", "uid": int(jian.uid)}).get("ok", false) and jian.get("natal", false), "a jian becomes the Natal treasure")
	Game.inventory.apply_add(c.id, "jadeiron", 5, "test")
	var fd := Game.submit({"type": "feed_natal", "uid": int(jian.uid), "item": "jadeiron", "count": 5})
	check(fd.get("ok", false) and int(jian.natal_level) == 2 and near(float(jian.natal_xp), 300.0), "five Jadeiron feed it to natal level 2 (%s)" % str(fd))
	check(near(StatRules.instance_mult(jian, c.cultivator.energy_type), mult0 * 1.04, 0.001), "natal level 2 gives +4%")
	var cap: int = Game.inventory.natal_cap(jian)
	check(cap > int(jian.ilv) and int(jian.get("ilv_eff", jian.ilv)) == clampi(ProgressionRules.level(c), int(jian.ilv), cap),
		"its item level follows yours, up to the grade band above its own (cap %d)" % cap)
	# It breaks only to the listed causes: an ordinary blow leaves it whole, a boss's shatter breaks it.
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", Game.actor_state(c.id).plane + Vector2(40, 0), 2)
	c.pools.invulnerable = 0.0
	c.pools.statuses = c.pools.statuses.filter(func(x): return str(x.id) != "spawn_protection")
	Game.combat.timeline(c.id).dodge_t = 0.0
	Game.combat._enemy_hits_player(foe, c, Game.combat.enemy_view(foe), Game.combat.player_view(c), {"mult": 0.01})
	check(not jian.get("broken", false), "an ordinary blow never breaks a natal weapon")
	c.pools.invulnerable = 0.0
	Game.combat._enemy_hits_player(foe, c, Game.combat.enemy_view(foe), Game.combat.player_view(c), {"mult": 0.01, "shatter": true})
	GameEvents.flush()
	check(jian.get("broken", false) and StatRules.instance_mult(jian, c.cultivator.energy_type) == 0.0 and not c.cultivator.injuries.is_empty(),
		"a shatter blow breaks it: its stats go dark and an injury follows")
	Game.inventory.apply_add(c.id, "jadeiron", 20, "test")
	Game.economy.apply_currency("silver_tael", 5000, "test")
	check(Game.submit({"type": "reforge_natal", "uid": int(jian.uid)}).get("ok", false) and not jian.get("broken", false) and int(jian.natal_level) == 2,
		"a re-forge mends it and keeps its growth")
	check(Game.combat.natal_demand(jian) == 20.0, "control demand is 10 + 5 a natal level")
	# Wardrobe and blood-drop: the first wear adds the look and bleeds a Plain-to-Heaven piece once.
	Game.inventory.apply_add_equipment(c.id, "jadeiron_robe", 27, "common", "test")
	var robe: Dictionary = c.inventory.bag[c.inventory.first_index("jadeiron_robe")]
	var bled := []
	var listen := func(n: String, p: Dictionary):
		if n == "item_blooded": bled.append(p)
	GameEvents.event.connect(listen)
	Game.inventory._first_wear(c, robe, "robe")
	Game.inventory._first_wear(c, robe, "robe")
	GameEvents.flush()
	GameEvents.event.disconnect(listen)
	var look := str(robe.get("appearance", ContentDB.item("jadeiron_robe").get("appearance", "")))
	check(bled.size() == 1 and robe.get("blooded", false), "a first wear takes one drop of blood")
	check(Game.account.wardrobe_unlocked.has("shirt:" + look), "the look joins the wardrobe (%s)" % look)
	check(not Game.submit({"type": "set_appearance", "slot": "robe", "look": "never_worn_look"}).get("ok", true), "a look never worn cannot be chosen")
	check(Game.submit({"type": "set_appearance", "slot": "robe", "look": look}).get("ok", false) and str(c.inventory.appearance_override.robe) == look,
		"a worn look can stand in for the robe's own")
	Game.submit({"type": "set_appearance", "slot": "robe", "look": ""})
	# Rogue cultivators drop what they carry, and a sealed pouch that Appraisal opens.
	var drop: Dictionary = LootRules.roll("rogue_cultivator", Rng.stream(c.id, "loot"), 25, 0.0, 0.0)
	var got := (drop.get("items", []) as Array).map(func(x): return str(x.item))
	check(got.has("serpent_tongue_jian") and got.has("sealed_storage_pouch"), "a rogue cultivator always drops its jian and a sealed pouch (%s)" % str(got))
	Unlocks.force_unlock(c.id, "appraisal")
	Game.progression.apply_learn_secret_art(c.id, "appraisal_eye")
	Game.inventory.apply_add(c.id, "sealed_storage_pouch", 1, "test")
	var ap := Game.workshop.appraise(c, c.inventory.first_index("sealed_storage_pouch"))
	var table: Array = ContentDB.item("sealed_storage_pouch").get("appraise", [])
	check(ap.get("ok", false) and table.any(func(x): return str(x.item) == str(ap.item)), "Appraisal opens the pouch into something from its own table (%s)" % str(ap))
	# Put things back.
	for k in ["natal", "natal_xp", "natal_level", "ilv_eff"]: jian.erase(k)
	c.inventory.equipped["weapon"] = held_before
	if foe != null: foe.alive = false
	for id in ["jadeiron_jian", "jadeiron_robe"]:
		var k2: int = c.inventory.first_index(id)
		if k2 >= 0: Game.inventory.apply_remove_index(c.id, k2, 1, "test")
	c.cultivator.injuries.clear()

# ------------------------------------------------------------------ S47 talisman craft and Shattered Relics
func talisman_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Unlocks.force_unlock(c.id, "talisman")
	var learn: Array = []
	for r in ["flame_talisman", "iron_wall_talisman", "wind_step_talisman", "binding_talisman", "beast_blood_ink"]:
		learn.append({"kind": "learn_recipe", "recipe": r})
	Game.apply_effects(c.id, learn, "test")
	for need in [["talisman_paper", 12], ["cinnabar", 12], ["ember_pepper", 8], ["beetle_shell", 4], ["vulture_plume", 2], ["hound_fang", 2], ["rat_tail", 2]]:
		Game.inventory.apply_add(c.id, str(need[0]), int(need[1]), "test")
	# A broken stroke spoils the paper and nothing else.
	var paper0: int = c.inventory.count("talisman_paper")
	var cin0: int = c.inventory.count("cinnabar")
	var br := Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 0.9, "broken": true})
	check(str(br.get("reason", "")) == "spoiled" and c.inventory.count("talisman_paper") == paper0 - 1 and c.inventory.count("cinnabar") == cin0
		and c.inventory.count("flame_talisman") == 0, "a broken stroke spoils one sheet of paper and makes nothing")
	# Tracing score to quality: a clean, unhurried stroke writes a better talisman than a shaky one.
	var order: Array = ContentDB.config("grades").get("quality_order", ["flawed", "common", "fine", "superior", "perfect"])
	var good := Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 1.0})
	var poor := Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 0.1})
	check(good.get("ok", false) and poor.get("ok", false) and order.find(str(good.quality)) > order.find(str(poor.quality)),
		"a clean stroke writes a better talisman (%s) than a shaky one (%s)" % [str(good.get("quality", "")), str(poor.get("quality", ""))])
	check(Game.submit({"type": "trace_talisman", "recipe": "beast_blood_ink"}).get("ok", false) and c.inventory.count("beast_blood_ink") >= 1, "inks are made without tracing")
	# An attack talisman strikes at its own grade and quality, never the user's stats.
	var st: ActorState = Game.actor_state(c.id)
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal"]: Game.combat.cure_status(c.id, sid)
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), 2)
	foe.pools.max_hp = 99999.0
	foe.pools.hp = 99999.0
	var used_q := [""]
	var dealt := func() -> float:
		var hp0: float = foe.pools.hp
		for k in 8:
			var old: int = c.inventory.first_index("flame_talisman")
			if old < 0: break
			Game.inventory.apply_remove_index(c.id, old, int(c.inventory.bag[old].get("count", 1)), "test")
		Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 1.0})
		var idx: int = c.inventory.first_index("flame_talisman")
		if idx >= 0: used_q[0] = str(c.inventory.bag[idx].get("quality", "common"))
		Game.submit({"type": "use_item", "index": idx})
		return hp0 - foe.pools.hp
	var d1: float = dealt.call()
	var q1: String = str(used_q[0])
	Game.combat.apply_buff(c.id, {"stat": "qi_attack", "op": "pct_add", "value": 2.0, "duration": 30.0, "source": "test"}, "test")
	var d2: float = dealt.call()
	var qm := float(ContentDB.config("talismans").get("quality_mult", {}).get(q1, 1.0))
	var qm2 := float(ContentDB.config("talismans").get("quality_mult", {}).get(str(used_q[0]), 1.0))
	check(d1 > 0.0 and near(d1 / qm, d2 / qm2, 0.001) and near(d1, 90.0 * 1.8 * qm, 0.01), "a Flame Talisman deals 180%% at its own grade, whatever your Qi attack (%.0f, %.0f)" % [d1, d2])
	# Iron Wall shields 20% of max HP; Wind Step holds one free dodge; Binding roots a foe but not a boss.
	Game.submit({"type": "trace_talisman", "recipe": "iron_wall_talisman", "score": 0.6})
	c.pools.shield = 0.0
	Game.submit({"type": "use_item", "index": c.inventory.first_index("iron_wall_talisman")})
	check(c.pools.shield > c.pools.max_hp * 0.15, "Iron Wall shields about a fifth of your max HP (%.0f)" % c.pools.shield)
	Game.submit({"type": "trace_talisman", "recipe": "wind_step_talisman", "score": 0.6})
	Game.submit({"type": "use_item", "index": c.inventory.first_index("wind_step_talisman")})
	Unlocks.force_unlock(c.id, "dodge_dash")
	c.pools.cooldowns["dodge"] = 5.0
	var dg := Game.submit({"type": "dodge", "direction": Vector2(1, 0), "facing": 1})
	check(dg.get("ok", false) and not Game.combat.treasure_fx.get(c.id, {}).has("free_dodge"), "Wind Step spends its charge on a dodge the cooldown would refuse")
	Game.apply_effects(c.id, [{"kind": "learn_recipe", "recipe": "binding_talisman"}], "test")
	Game.inventory.apply_add(c.id, "binding_talisman", 1, "test")
	var bi := Game.submit({"type": "use_item", "index": c.inventory.first_index("binding_talisman")})
	check(bi.get("ok", false) and foe.pools.has_status("root"), "a Binding Talisman roots the nearest foe")
	# A Shattered Relic needs an Expert smith at a forge.
	Game.inventory.apply_add(c.id, "shattered_moon_blade", 1, "test")
	var rr := Game.submit({"type": "restore_relic", "index": c.inventory.first_index("shattered_moon_blade")})
	check(not rr.get("ok", true) and str(rr.get("reason", "")) in ["no_station", "rank"], "a Shattered Relic waits for an Expert smith at a forge (%s)" % str(rr.get("reason", "")))
	check(ContentDB.item("moonlit_blade").get("relic", false) and str(ContentDB.item("shattered_moon_blade").get("restores", "")) == "moonlit_blade",
		"the Moon Blade's shards restore into a relic")
	# Tidy up.
	if foe != null: foe.alive = false
	c.pools.shield = 0.0
	for id in ["flame_talisman", "iron_wall_talisman", "wind_step_talisman", "binding_talisman", "shattered_moon_blade", "beast_blood_ink"]:
		for k in 8:
			var at: int = c.inventory.first_index(id)
			if at < 0: break
			Game.inventory.apply_remove_index(c.id, at, int(c.inventory.bag[at].get("count", 1)), "test")

# ------------------------------------------------------------------ S44 herb natures, roles, conflicts and the furnace blast
func herb_nature_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	check(str(ContentDB.item("riverreed_ginseng_10").get("nature", "")) == "hot" and str(ContentDB.item("mist_lotus").get("nature", "")) == "cold"
		and str(ContentDB.item("willow_moss").get("nature", "")) == "neutral" and str(ContentDB.item("cloudtop_orchid").get("nature", "")) == "cold",
		"herbs carry Part 8's natures")
	check(near(Game.crafting.nature_shift("healing_pill"), 0.08) and near(Game.crafting.nature_shift("clear_mind_pill"), -0.08),
		"a hot Principal moves the Extraction band up 8%%; a cold one down")
	check(Game.crafting.role_of("healing_pill", "riverreed_ginseng_10") == "principal" and Game.crafting.role_of("healing_pill", "willow_moss") == "minister",
		"recipe order gives the roles: Principal, then Minister")
	# The substitute: Alchemy Dao tier 5, the same nature, and a role the herb can fill.
	var daos: Dictionary = c.cultivator.daos
	var had: Dictionary = daos.get("alchemy", {}).duplicate()
	daos["alchemy"] = {"tier": 4, "insight": 0.0}
	check(Game.crafting.substitute_check(c, "cleansing_pill", "riverreed_ginseng_100", "ember_pepper") != "", "below tier 5 no herb stands in for another")
	daos["alchemy"] = {"tier": 5, "insight": 0.0}
	check(Game.crafting.substitute_check(c, "cleansing_pill", "riverreed_ginseng_100", "ember_pepper") == "", "tier 5: hot Ember Pepper may stand in for hot ginseng as Assistant")
	check(Game.crafting.substitute_check(c, "cleansing_pill", "mist_lotus", "ember_pepper") != "", "a hot herb never stands in for a cold one")
	check(Game.crafting.substitute_check(c, "healing_pill", "riverreed_ginseng_10", "ember_pepper") != "", "Ember Pepper cannot be a Principal")
	# Every listed conflict blows the furnace: minor body injury, -10 durability, and the batch is lost.
	Unlocks.force_unlock(c.id, "alchemy")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	var fo: Dictionary = Game.room_rt.object_def("furnace_sf")
	Game.actor_state(c.id).plane = Vector2(float(fo.at[0]) - 40.0, float(fo.at[1]))
	c.inventory.bag.fill(null)
	c.inventory.furnace = null
	Game.inventory.apply_add(c.id, "jadeiron_furnace", 1, "test")
	c.cultivator.injuries.clear()
	Game.apply_effects(c.id, [{"kind": "learn_recipe", "recipe": "cleansing_pill"}], "test")
	for inp in ContentDB.entry("recipes", "cleansing_pill").inputs: Game.inventory.apply_add(c.id, str(inp.item), int(inp.count), "test")
	Game.inventory.apply_add(c.id, "ember_pepper", 1, "test")
	var bl := Game.crafting.craft(c, "cleansing_pill", 1, [1.0, 1.0, 1.0], "alchemy", "charcoal", {"from": "riverreed_ginseng_100", "to": "ember_pepper"})
	GameEvents.flush()
	check(str(bl.get("reason", "")) == "blast" and int(c.inventory.furnace.durability) == 90 and c.inventory.count("cleansing_pill") == 0
		and c.inventory.count("mist_lotus") == 0 and c.inventory.count("ember_pepper") == 0,
		"Ember Pepper meets Mist Lotus: the furnace blows, loses 10 durability, and the batch is gone")
	check(int(c.cultivator.injuries.get("body", {}).get("severity", 0)) >= 1, "the blast leaves a minor body injury")
	check((c.crafting.get("known_conflicts", []) as Array).has("ember_pepper+mist_lotus"), "the pair is remembered, so the page can warn next time")
	for row in ContentDB.all("herb_conflicts"):
		var pair: Array = row.herbs
		check(not Game.crafting.conflict_in([{"item": pair[0]}, {"item": pair[1]}]).is_empty(), "conflict %s blows the furnace" % row.id)
	# Tidy up.
	c.cultivator.injuries.clear()
	if had.is_empty(): daos.erase("alchemy")
	else: daos["alchemy"] = had
	c.inventory.bag.fill(null)

# ------------------------------------------------------------------ S44 new forms: Qi Flow, oils, the poison pill, the draught, baths
func new_forms_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	c.inventory.bag.fill(null)
	# The Qi Flow Pill: +20% accumulation for an hour; the toxicity comes due when it wears off.
	Game.inventory.apply_add(c.id, "qi_flow_pill", 1, "test")
	for k in ["item:buff", "item:utility", "item:healing"]: c.pools.cooldowns.erase(k)
	var acc0: float = c.stats.value("accumulation_rate")
	Game.apply_effects(c.id, ContentDB.item("qi_flow_pill").use, "item:qi_flow_pill")   # the effect itself (the test body is too young for an Earth pill)
	GameEvents.flush()
	check(c.stats.value("accumulation_rate") > acc0 + 0.15, "the Qi Flow Pill lifts accumulation (%.2f -> %.2f)" % [acc0, c.stats.value("accumulation_rate")])
	var tox0: float = cu.toxicity
	for m in c.stats.modifiers:
		if str(m.get("source", "")) == "qi_flow_pill": m.remaining = 0.01
	Game.combat.tick(0.05)
	GameEvents.flush()
	check(cu.toxicity >= tox0 + 14.0, "when the hour is up, +15 toxicity comes due (%.1f -> %.1f)" % [tox0, cu.toxicity])
	# Weapon oils: one at a time; each hit may carry the oil's status.
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	var st: ActorState = Game.actor_state(c.id)
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), 2)
	foe.pools.max_hp = 99999.0
	foe.pools.hp = 99999.0
	Game.inventory.apply_add(c.id, "viper_oil", 1, "test")
	Game.inventory.apply_add(c.id, "ember_oil", 1, "test")
	c.pools.cooldowns.erase("item:utility")
	Game.inventory.use_item(c, _bag_index(c, "viper_oil"), true)
	check(c.pools.has_status("viper_oil"), "Viper Oil is on the blade")
	var poisoned := 0
	for i in 60:
		foe.pools.statuses.clear()
		Game.combat._oil_strike(c, foe, Game.combat.enemy_view(foe))
		if foe.pools.has_status("poison"): poisoned += 1
	check(poisoned > 3 and poisoned < 25, "Viper Oil poisons about one hit in five (%d of 60)" % poisoned)
	c.pools.cooldowns.erase("item:utility")
	Game.inventory.use_item(c, _bag_index(c, "ember_oil"), true)
	check(c.pools.has_status("ember_oil") and not c.pools.has_status("viper_oil"), "a second oil wipes off the first")
	Game.combat.cure_status(c.id, "ember_oil")
	# The Viper Smoke Pill leaves a poison cloud: 4% of max HP a second for 5 s.
	foe.pools.statuses.clear()
	Game.combat._burst(c, {"x": foe.plane.x, "y": foe.plane.y, "alt": 0.0, "burst": 90.0, "attack": {"damage_type": "physical", "mult": [0.2, 0.2], "range": [1.0, 1.0]},
		"cloud": ContentDB.item("viper_smoke_pill").use[0].cloud}, null)
	var cloud_ok := false
	for s2 in foe.pools.statuses:
		if str(s2.id) == "poison" and near(float(s2.power), 0.04) and near(float(s2.remaining), 5.0): cloud_ok = true
	check(cloud_ok, "the smoke cloud poisons for 4%% of max HP a second, 5 s")
	foe.alive = false
	# The Riverreed Draught: two strikes, straight to the Draught slot, flat after ten minutes.
	check(Game.crafting.steps_for("riverreed_draught") == 2 and Game.crafting.steps_for("healing_pill") == 3, "a liquid takes two strikes (no Condensation)")
	Unlocks.force_unlock(c.id, "alchemy")
	var fo: Dictionary = Game.room_rt.object_def("furnace_sf")
	st.plane = Vector2(float(fo.at[0]) - 40.0, float(fo.at[1]))
	c.inventory.furnace = null
	Game.inventory.apply_add(c.id, "bronze_furnace", 1, "test")
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 2, "test")
	Game.inventory.apply_add(c.id, "river_minnow", 2, "test")
	c.inventory.draught = null
	var dr := Game.crafting.craft(c, "riverreed_draught", 1, [1.0, 1.0], "alchemy")
	check(dr.get("ok", false) and c.inventory.draught != null and int(c.inventory.draught.count) >= 1 and c.inventory.count("riverreed_draught") == 0,
		"the draught goes to the Draught slot, not the bag")
	c.pools.hp = c.pools.max_hp * 0.4
	c.pools.cooldowns.erase("item:healing")
	var dk := Game.submit({"type": "drink_draught"})
	for k in 40: Game.tick(0.1)
	check(dk.get("ok", false) and c.pools.hp > c.pools.max_hp * 0.6, "drinking it restores 30% HP")
	Game.inventory.apply_draught(c.id, "riverreed_draught", 1, "test")
	c.inventory.draught.made_utc = Clock.now_utc() - 601.0
	Game.inventory.tick(0.1)
	check(c.inventory.draught == null, "ten minutes after it is made, the draught goes flat")
	# Baths: the seclusion slot at a Bath station; a bath beyond the body injures it.
	Unlocks.force_unlock(c.id, "medicinal_bath")
	Unlocks.force_unlock(c.id, "seclusion")
	Game.world.apply_teleport(c.id, "ja_retreat")
	var bo: Dictionary = Game.room_rt.object_def("bath_ja_retreat")
	check(not bo.is_empty(), "the retreat rooms have a Bath station")
	if not bo.is_empty():
		st.plane = Vector2(float(bo.at[0]) - 40.0, float(bo.at[1]))
		c.cultivator.injuries.clear()
		cu.body_level = 5
		Game.inventory.apply_add(c.id, "copper_body_bath", 1, "test")
		cu.residue = 30.0
		var xp0: float = cu.body_xp
		var lv0: int = cu.body_level
		var sb := Game.submit({"type": "start_bath", "item": "copper_body_bath"})
		check(sb.get("ok", false) and str(c.seclusion.get("focus", "")) == "bath" and c.inventory.count("copper_body_bath") == 0, "the Copper Body Bath takes the seclusion slot")
		var cl := Game.progression.claim_offline(c, 3600.0)
		var g: Dictionary = cl.get("gains", {})
		check(near(float(g.get("body_xp", 0.0)), 600.0) and near(float(g.get("residue", 0.0)), 10.0) and not g.get("injured", false),
			"an hour in it: +600 body XP and 10 residue cleared, no harm at any body")
		Game.inventory.apply_add(c.id, "marrow_washing_bath", 1, "test")
		Game.submit({"type": "start_bath", "item": "marrow_washing_bath"})
		var cl2 := Game.progression.claim_offline(c, 3600.0)
		check(cl2.get("gains", {}).get("injured", false) and int(c.cultivator.injuries.get("body", {}).get("severity", 0)) >= 1,
			"a Marrow-Washing Bath before Copper Body injures the body")
		c.cultivator.injuries.clear()
		check(ProgressionRules.body_tier_index(cu) == 0 and cu.body_baths.has("copper") and not cu.body_baths.has("iron"),
			"a full Copper Body soak is recorded; a bath that injures is not")
	# Calm Heart Incense: heart demon -10. The Murky Pill sells for a tael.
	cu.heart_demon = 30.0
	Game.inventory.apply_add(c.id, "calm_heart_incense", 1, "test")
	c.pools.cooldowns.erase("item:utility")
	Game.inventory.use_item(c, _bag_index(c, "calm_heart_incense"), true)
	check(near(cu.heart_demon, 20.0), "Calm Heart Incense clears 10 heart demon (%.1f)" % cu.heart_demon)
	cu.heart_demon = 0.0
	check(LootRules.sell_price("murky_pill", null) <= 1, "a Murky Pill sells for a tael")
	c.inventory.bag.fill(null)
	cu.toxicity = 0.0

# ------------------------------------------------------------------ S44 ancient recipes, experiments, the Alchemist Guild
func guild_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	c.inventory.bag.fill(null)
	Unlocks.force_unlock(c.id, "alchemy")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	var st: ActorState = Game.actor_state(c.id)
	var fo: Dictionary = Game.room_rt.object_def("furnace_sf")
	st.plane = Vector2(float(fo.at[0]) - 40.0, float(fo.at[1]))
	# Deduce: 20% a page + 10% a Dao tier above the third, capped at 95%; a full set teaches it outright.
	var daos: Dictionary = c.cultivator.daos
	var had: Dictionary = daos.get("alchemy", {}).duplicate()
	daos["alchemy"] = {"tier": 3, "insight": 0.0}
	c.crafting["recipe_fragments"] = {}
	c.crafting.recipes.erase("method_conversion_pill")
	Game.apply_effects(c.id, [{"kind": "recipe_page", "recipe": "method_conversion_pill", "page": 1}], "test")
	check(near(Game.crafting.deduce_chance(c, "method_conversion_pill"), 0.2), "one page of three: a 20% chance")
	Game.apply_effects(c.id, [{"kind": "recipe_page", "recipe": "method_conversion_pill", "page": 2}], "test")
	daos["alchemy"] = {"tier": 5, "insight": 0.0}
	check(near(Game.crafting.deduce_chance(c, "method_conversion_pill"), 0.6), "two pages and Dao tier 5: 60%")
	c.crafting["recipe_fragments"] = {"sovereign_settling_pill": [1, 2, 3]}
	daos["alchemy"] = {"tier": 9, "insight": 0.0}
	check(near(Game.crafting.deduce_chance(c, "sovereign_settling_pill"), 0.95), "the chance never passes 95%")
	for inp in ContentDB.entry("recipes", "method_conversion_pill").inputs: Game.inventory.apply_add(c.id, str(inp.item), int(inp.count), "test")
	c.crafting["recipe_fragments"] = {"method_conversion_pill": [1, 2]}
	var dd := Game.submit({"type": "deduce_recipe", "recipe": "method_conversion_pill"})
	check(dd.get("ok", false) and c.inventory.count("manual_page") == 0, "a Deduce attempt spends one set of ingredients")
	c.crafting.recipes.erase("method_conversion_pill")
	c.crafting["recipe_fragments"] = {"method_conversion_pill": [1, 2]}
	Game.apply_effects(c.id, [{"kind": "recipe_page", "recipe": "method_conversion_pill", "page": 3}], "test")
	check(Game.crafting.knows(c, "method_conversion_pill"), "the last page of a set teaches the recipe")
	if had.is_empty(): daos.erase("alchemy")
	else: daos["alchemy"] = had
	check(ContentDB.room("mh_loot_cave").get("objects", []).any(func(o): return str(o.id) == "page_method_conversion_pill_1"), "the first page lies in the Mudwater Hideout")
	# Experiments: hidden recipes by their herbs; anything else a Murky Pill; the account log refuses a repeat.
	Unlocks.force_unlock(c.id, "experiments")
	c.inventory.furnace = null
	Game.inventory.apply_add(c.id, "bronze_furnace", 1, "test")
	Game.account.experiments.clear()
	c.crafting.recipes.erase("sunfire_pill")
	for h in ["riverreed_ginseng_10", "ember_pepper", "willow_moss"]: Game.inventory.apply_add(c.id, h, 3, "test")
	var ex1 := Game.submit({"type": "start_experiment", "herbs": ["ember_pepper", "riverreed_ginseng_10"]})
	check(ex1.get("ok", false) and str(ex1.get("recipe", "")) == "sunfire_pill" and Game.crafting.knows(c, "sunfire_pill"), "ginseng and Ember Pepper reveal the Sunfire Pill")
	var ex2 := Game.submit({"type": "start_experiment", "herbs": ["willow_moss", "ember_pepper"]})
	check(ex2.get("ok", false) and str(ex2.get("result", "")) == "murky" and c.inventory.count("murky_pill") == 1, "an idle mix makes a Murky Pill")
	var ex3 := Game.submit({"type": "start_experiment", "herbs": ["ember_pepper", "willow_moss"]})
	check(str(ex3.get("reason", "")) == "tried" and c.inventory.count("murky_pill") == 1, "the log refuses a mix already tried, in any order")
	check(Game.account.experiments.size() == 2, "the log is the account's")
	# The Alchemist Guild: the Adept exam counts Fine Healing Pills while the candle burns.
	Unlocks.force_unlock(c.id, "alchemist_guild")
	c.crafting["guild"] = {}
	c.crafting["guild_exam"] = {}
	var te := Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "expert"})
	check(not te.get("ok", false), "the Expert exam waits for the Adept badge")
	te = Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "adept"})
	check(te.get("ok", false) and near(float(te.time_s), 300.0), "the Adept exam: five minutes (a refine is five screens)")
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "healing_pill", "craft": "alchemy", "quality": "common", "count": 3})
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "healing_pill", "craft": "alchemy", "quality": "fine", "count": 3})
	GameEvents.flush()
	check(int(c.crafting.guild_exam.get("made", 0)) == 3 and Game.crafting.guild_rank(c, "alchemy") == "", "Common pills do not count; three Fine ones do")
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "healing_pill", "craft": "alchemy", "quality": "superior", "count": 2})
	GameEvents.flush()
	check(Game.crafting.guild_rank(c, "alchemy") == "adept" and c.quests.has_flag("guild_alchemy_adept"), "five Fine Healing Pills in time: Guild Adept")
	# Commissions: three a day, capped at a fifth of the day's income target.
	var orders: Array = Game.crafting.commissions(c)
	check(orders.size() == 3 and Game.crafting.commissions(c) == orders, "three orders a day, the same all day")
	var o: Dictionary = orders[0]
	Game.inventory.apply_add(c.id, str(o.item), int(o.count), "test", {"quality": "fine"})
	check(not Game.submit({"type": "deliver_commission", "id": str(o.id)}).get("ok", false), "an order is taken before it is delivered")
	Game.submit({"type": "accept_commission", "id": str(o.id)})
	var t0: int = Game.economy.balance("silver_tael")
	var dl := Game.submit({"type": "deliver_commission", "id": str(o.id), "pay": "taels"})
	var cap: int = Game.crafting.commission_cap(c)
	check(dl.get("ok", false) and Game.economy.balance("silver_tael") - t0 == mini(int(o.pay), cap) and Game.economy.balance("silver_tael") - t0 <= cap,
		"a delivered order pays 1.2x the pill's price, within the daily cap (%d of %d)" % [Game.economy.balance("silver_tael") - t0, cap])
	# The Expert exam teaches the Qi Flow Pill.
	c.crafting["guild_exam"] = {}
	Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "expert"})
	c.crafting.guild_exam.started = Game.sim_time - float(Game.crafting.guild_rank_def("alchemy", "expert").time_s) - 1.0
	Game.crafting.tick(0.1)
	GameEvents.flush()
	check(c.crafting.get("guild_exam", {}).is_empty() and Game.crafting.guild_rank(c, "alchemy") == "adept", "a burnt-out candle fails the exam")
	Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "expert"})
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "foundation_guard_pill", "craft": "alchemy", "quality": "superior", "count": 3})
	GameEvents.flush()
	check(Game.crafting.guild_rank(c, "alchemy") == "expert" and Game.crafting.knows(c, "qi_flow_pill"), "Guild Expert, and the Qi Flow Pill recipe")
	# The Master exam (v1.1) needs a Sage's hands and is sat at Cloudgate Port.
	var realm0: String = c.cultivator.realm_key
	c.cultivator.realm_key = "heaven_glimpse_9"
	var tm := Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "master"})
	check(not tm.get("ok", false) and str(tm.get("reason", "")) == "not_here", "the Master exam waits for the Sage realm")
	c.cultivator.realm_key = "sage_1"
	tm = Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "master"})
	check(not tm.get("ok", false) and str(tm.get("text", "")).contains(ContentDB.name_of("rooms", "ae_port_market")), "and is sat at Cloudgate Port (%s)" % str(tm.get("text", "")))
	Game.world.apply_teleport(c.id, "ae_port_market")
	tm = Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "master"})
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "storm_blood_pill", "craft": "alchemy", "quality": "superior", "count": 3, "auto": true})
	GameEvents.flush()
	check(tm.get("ok", false) and int(c.crafting.guild_exam.get("made", 0)) == 0, "at the port the candle is lit; the auto-refine queue never counts")
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "storm_blood_pill", "craft": "alchemy", "quality": "superior", "count": 3})
	GameEvents.flush()
	check(Game.crafting.guild_rank(c, "alchemy") == "master" and Game.crafting.knows(c, "sage_condensing_pill") and c.cultivator.titles.has("alchemist_master"),
		"three Superior Storm Blood Pills: Alchemist Master, and the Sage Condensing Pill recipe")
	# The Forge Guild (S49): any family of weapon at the rank's grade or above counts; armour and lower grades do not.
	Unlocks.force_unlock(c.id, "forge_guild")
	c.crafting["guild_exam"] = {}
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	check(Game.crafting.guilds_open(c).size() >= 2, "each guild opens with its own gate")
	check(Game.submit({"type": "take_guild_exam", "craft": "smithing", "rank": "adept"}).get("ok", false), "the Forge Guild's Adept exam begins at Smith Bao's")
	for row in [["iron_jian", "fine"], ["bp_jadeiron_hat", "perfect"], ["jadeiron_spear", "common"], ["jadeiron_jian", "fine"]]:
		GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": row[0], "craft": "smithing", "quality": row[1], "count": 1})
	GameEvents.flush()
	check(int(c.crafting.get("guild_exam", {}).get("made", 0)) == 1 and Game.crafting.guild_rank(c, "smithing") == "",
		"a common-grade blade, a hat and a Common spear do not count; a Fine Jadeiron Jian does")
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "cloudsteel_fan", "craft": "smithing", "quality": "superior", "count": 1})
	GameEvents.flush()
	check(Game.crafting.guild_rank(c, "smithing") == "adept" and c.quests.has_flag("guild_smithing_adept") and c.cultivator.titles.has("forge_adept"),
		"two Earth-grade (or better) weapons at Fine: Forge Adept")
	c.crafting.recipes.append("jadeiron_jian")
	var forders: Array = Game.crafting.commissions(c, "smithing")
	check(not forders.is_empty() and forders.all(func(fo2): return ContentDB.is_equipment(str(fo2.item))) and Game.crafting.commissions(c, "alchemy") != forders,
		"the Forge Guild's board orders pieces, on a board of its own")
	var fo1: Dictionary = forders[0]
	Game.submit({"type": "accept_commission", "id": str(fo1.id)})
	for i in int(fo1.count): Game.inventory.apply_add_equipment(c.id, str(fo1.item), 0, "fine", "test")
	var ft0: int = Game.economy.balance("silver_tael")
	var fdl := Game.submit({"type": "deliver_commission", "id": str(fo1.id), "pay": "taels"})
	check(fdl.get("ok", false) and c.inventory.count(str(fo1.item)) == 0 and Game.economy.balance("silver_tael") - ft0 == mini(int(fo1.pay), Game.crafting.commission_cap(c, "smithing")),
		"forged pieces fill a forge order, paid within the Forge Guild's own cap")
	# The Formation Guild: plates are etched, not rolled, so its exams count plates against the candle.
	Unlocks.force_unlock(c.id, "formation_guild")
	c.crafting["guild_exam"] = {}
	check(Game.submit({"type": "take_guild_exam", "craft": "formations", "rank": "adept"}).get("ok", false), "the Formation Guild's Adept exam begins")
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "killing_array_plate", "craft": "formations", "quality": "common", "count": 2})
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "array_plate", "craft": "formations", "quality": "common", "count": 4})
	GameEvents.flush()
	check(Game.crafting.guild_rank(c, "formations") == "adept" and c.inventory.count("formation_stone") >= 5, "four Array Plates: Formation Adept, and five formation stones")
	c.cultivator.realm_key = realm0
	c.crafting["guild"] = {}
	c.crafting["guild_exam"] = {}
	c.inventory.bag.fill(null)

# ------------------------------------------------------------------ S44 pill tribulation and the Pill Soul's flight
# ------------------------------------------------------------------ S48 the body ladder, physiques, roots, Core Forging
func body_path_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var realm_was := cu.realm_key
	var body_was := cu.body_level
	c.inventory.bag.fill(null)
	# Titles: the worn title's modifiers reach the stats (they were never applied before V5a).
	var had_titles: Array = cu.titles.duplicate()
	var title_was := cu.active_title
	cu.titles.append("fleet_footed")
	cu.active_title = ""
	Game.combat.refresh_stats(c.id)
	var ms0: float = c.stats.value("move_speed")
	cu.active_title = "fleet_footed"
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("move_speed") > ms0 + 0.5, "a worn title's modifier applies (Fleet-Footed: %.1f -> %.1f move speed)" % [ms0, c.stats.value("move_speed")])
	cu.titles = had_titles
	cu.active_title = title_was
	# Body tier needs level, trial and bath, one rung at a time.
	cu.body_tier = "mortal"
	cu.body_trials.clear()
	cu.body_baths.clear()
	cu.body_level = 20
	cu.physiques.clear()
	cu.realm_key = "qi_unfurling_5"
	Game.progression.pass_body_trial(c.id, "copper")
	check(cu.body_tier == "mortal", "the Copper trial alone does not open Copper Body")
	cu.body_trials.clear()
	cu.body_baths.append("copper")
	Game.progression._check_body_tier(c)
	check(cu.body_tier == "mortal", "the Copper bath alone does not open it either")
	Game.progression.pass_body_trial(c.id, "copper")
	check(cu.body_tier == "copper" and ProgressionRules.body_tier_index(cu) == 1, "trial and bath together: Copper Body")
	check(not cu.physiques.has("stone_marrow"), "Copper Body after Qi Unfurling 3 does not awaken Stone Marrow")
	Game.combat.refresh_stats(c.id)
	var mods := 0
	for m in c.stats.modifiers:
		if str(m.get("source", "")).begins_with("body_tier:copper"): mods += 1
	check(mods == 1, "Copper Body's gift is one Physical Defense modifier (%d)" % mods)
	Game.progression.pass_body_trial(c.id, "iron")
	cu.body_baths.append("iron")
	Game.progression._check_body_tier(c)
	check(cu.body_tier == "copper", "Iron Body waits for body level 36")
	cu.body_level = 35
	Game.progression.apply_body_xp(c.id, ProgressionRules.body_xp_needed(35) + 1.0, "test")
	check(cu.body_level == 36 and cu.body_tier == "iron" and c.crafting.recipes.has("jade_marrow_bath"),
		"reaching body level 36 with the trial and bath done opens Iron Body, which teaches the Jade Marrow Bath")
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("knockback_resistance") >= 0.10, "Iron Body: +10%% knockback resistance (%.2f)" % c.stats.value("knockback_resistance"))
	# The trials themselves are room events: the HP floor fails one, a kill count wins another.
	Game.world.apply_teleport(c.id, "wp_west")
	var sp := ContentDB.entry("set_pieces", "copper_body_trial")
	Game.world._start_event(c, Game.room_rt, sp.room_event)
	c.pools.hp = c.pools.max_hp * 0.4
	Game.world._tick_event(c, Game.room_rt, 0.1)
	check(not Game.room_rt.event.get("active", true), "falling below half HP ends the Copper trial")
	c.pools.hp = c.pools.max_hp
	Game.world.apply_teleport(c.id, "cp_pilgrim_stairs")
	var iron := ContentDB.entry("set_pieces", "iron_body_trial")
	Game.world._start_event(c, Game.room_rt, iron.room_event)
	for i in 5: Game.world._event_kill({"def": "stone_guardian", "victim_kind": "enemy"})
	check(not Game.room_rt.event.get("active", true), "five Stone Guardians in one run pass the Iron trial")
	# Gold Body is immune to Qi Seal; the flag lives on the tier.
	cu.body_tier = "gold"
	Game.combat.apply_status(c.id, "qi_seal", 5.0, 1.0)
	check(not c.pools.has_status("qi_seal"), "Gold Body shrugs off Qi Seal")
	cu.body_tier = "copper"
	# Copper Body: a body technique spends HP when QI runs short, never below a fifth.
	var tiger := ContentDB.entry("techniques", "tiger_rush")
	c.pools.qi = 0.0
	c.pools.hp = c.pools.max_hp
	check(Game.combat.body_hp_cost(c, tiger, 12.0) > 0.0, "Tiger Rush with no QI spends HP at Copper Body")
	check(near(Game.combat.body_hp_cost(c, tiger, 12.0), c.pools.max_hp * 12.0 / maxf(1.0, c.pools.max_qi)),
		"it spends the share of max HP that 12 QI is of max QI (P12: Might scales HP, not QI)")
	c.pools.hp = c.pools.max_hp * 0.2 + 1.0
	check(Game.combat.body_hp_cost(c, tiger, 12.0) == 0.0, "never below a fifth of HP")
	check(Game.combat.body_hp_cost(c, ContentDB.entry("techniques", "flowing_palm"), 8.0) == 0.0, "a technique that is not a body technique never spends HP")
	c.pools.hp = c.pools.max_hp
	# Physiques: gift and drawback, counters, the heart-demon multiplier.
	Game.combat.refresh_stats(c.id)
	var hp0: float = c.stats.value("max_hp")
	var qr0: float = c.stats.value("qi_resistance")
	Game.progression.awaken_physique(c.id, "jade_bone")
	Game.combat.refresh_stats(c.id)
	check(cu.physiques.has("jade_bone") and c.stats.value("max_hp") > hp0 and c.stats.value("qi_resistance") <= qr0,
		"Jade Bone: more HP, a little less Qi Resistance")
	cu.lifetime_stats["fire_pills"] = 49.0
	Game.progression._on_fire_pill({"actor": c.id, "craft": "alchemy", "recipe": "tiger_blood_pill", "count": 1})
	check(cu.physiques.has("ember_heart"), "the fiftieth Fire pill awakens Ember Heart")
	Game.progression._on_fire_pill({"actor": c.id, "craft": "alchemy", "recipe": "healing_pill", "count": 5})
	check(float(cu.lifetime_stats.get("fire_pills", 0)) == 50.0, "pills of other elements do not count")
	cu.heart_demon = 0.0
	cu.physiques.append("hollow_touched")
	Game.progression.apply_heart_demon(c.id, 10.0, "test")
	check(near(cu.heart_demon, 15.0), "Hollow-Touched: heart-demon gains x1.5 (%.1f)" % cu.heart_demon)
	Game.progression.apply_heart_demon(c.id, -10.0, "test")
	check(near(cu.heart_demon, 5.0), "drains are not multiplied")
	cu.heart_demon = 0.0
	cu.physiques.clear()
	cu.body_tier = "mortal"
	cu.realm_key = "bone_forging_9"
	cu.body_trials.clear()
	cu.body_baths.clear()
	cu.body_level = 17
	Game.progression.pass_body_trial(c.id, "copper")
	cu.body_baths.append("copper")
	cu.body_level = 18
	Game.progression._check_body_tier(c)
	check(cu.physiques.has("stone_marrow"), "Copper Body before Qi Unfurling 3 awakens Stone Marrow")
	cu.physiques.clear()
	# Named roots at the edges: +5% counts, above +10% is Heavenly, the strongest wind is Mutated.
	var apt_was: Dictionary = cu.aptitude.duplicate(true)
	var set_roots := func(vals: Dictionary) -> void:
		for el in ["water", "wood", "fire", "earth", "metal", "wind"]:
			cu.aptitude["element_" + el] = {"value": float(vals.get(el, 0.0)), "revealed": true}
	set_roots.call({"water": 0.11})
	check(ProgressionRules.root_name(cu) == "heavenly", "one element above +10%: Heavenly")
	set_roots.call({"water": 0.10})
	check(ProgressionRules.root_name(cu) == "faint", "exactly +10% is not Heavenly; one element counting alone is Faint")
	set_roots.call({"water": 0.05, "fire": 0.05})
	check(ProgressionRules.root_name(cu) == "true", "two elements at +5%: True")
	set_roots.call({"water": 0.05, "fire": 0.049})
	check(ProgressionRules.root_name(cu) == "faint", "+4.9% does not count")
	set_roots.call({"water": 0.06, "fire": 0.06, "earth": 0.06, "metal": 0.06})
	check(ProgressionRules.root_name(cu) == "mixed", "four elements at +5% or more: Mixed")
	set_roots.call({"wind": 0.07, "water": 0.06})
	check(ProgressionRules.root_name(cu) == "mutated", "wind the strongest: Mutated")
	cu.aptitude["element_fire"].revealed = false
	check(ProgressionRules.root_name(cu) == "", "no root name while the elements are hidden")
	cu.aptitude = apt_was
	# Core Forging: 9 minus the points that count (80% each), floor 5; a flawless Cleansing one more, floor 4.
	check(ProgressionRules.core_grade(0, false) == 9 and ProgressionRules.core_grade(0, true) == 8 and ProgressionRules.core_grade(5, false) == 5
		and ProgressionRules.core_grade(5, true) == 4 and ProgressionRules.core_grade(2, false) == 7, "core grade from points: 9, flawless 8, floor 5, flawless floor 4")
	cu.method_id = "jade_current_scripture"
	cu.residue = 0.0
	c.pools.composure = 100.0
	Game.world.apply_teleport(c.id, "cf_falls_pool")
	c.cultivator.pill_memory["heavenly_flame_pill"] = Game.sim_time - 60.0
	var pts: Array = Game.progression.core_forging_points(c)
	var met := 0
	for pt in pts:
		if pt.met: met += 1
	check(pts.size() == 5 and pts[0].met and pts[2].met and pts[3].met and pts[4].met, "a water method at the Falls Pool, Composure full, no residue, the pill an hour since: four points (%d)" % met)
	var grades := []
	for run in 2:
		Rng.restore(c.id, {}, 4242)
		cu.realm_key = "heart_tempering_9"
		cu.purity = 9
		Game.progression._forge_core(c)
		grades.append(cu.core_grade)
	check(grades[0] == grades[1] and cu.purity == cu.core_grade and cu.core_grade >= 5 and cu.core_grade <= 9 - 0,
		"the same seed forms the same core (%s)" % str(grades))
	c.cultivator.pill_memory.erase("heavenly_flame_pill")
	cu.core_grade = 0
	cu.purity = 9
	cu.realm_key = realm_was
	cu.body_level = body_was
	cu.body_tier = "mortal"
	cu.body_trials.clear()
	cu.body_baths.clear()
	cu.lifetime_stats.erase("fire_pills")
	cu.events_passed.erase("iron_body_trial")
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 heavenly tribulation, fates, Qi Deviation
func heaven_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var st: ActorState = Game.actor_state(c.id)
	var realm_was := cu.realm_key
	var hd_was := cu.heart_demon
	var sin_was: int = c.relations.sin
	c.inventory.bag.fill(null)
	# Bolt counts by realm, heart demon and sin.
	check(ProgressionRules.tribulation_bolts("heart_tempering_9", 0, 0) == 0, "no tribulation into Cloud Stride (the Heart Trial is the set piece)")
	check(ProgressionRules.tribulation_bolts("cloud_stride_9", 0, 0) == 3 and ProgressionRules.tribulation_bolts("spirit_awakening_9", 0, 0) == 6
		and ProgressionRules.tribulation_bolts("heaven_glimpse_3", 0, 0) == 9, "3 bolts into Spirit Awakening, 6 into Heaven Glimpse, 9 into Sage")
	check(ProgressionRules.tribulation_bolts("sage_3", 0, 0) == 18 and ProgressionRules.tribulation_bolts("sage_sovereign_3", 0, 0) == 27,
		"then waves of 9: 2 into Sage Sovereign, 3 into Will Manifest")
	check(ProgressionRules.tribulation_bolts("cloud_stride_9", 24.0, 99) == 3 and ProgressionRules.tribulation_bolts("cloud_stride_9", 25.0, 100) == 5
		and ProgressionRules.tribulation_bolts("cloud_stride_9", 50.0, 0, 2) == 7, "+1 per 25 heart demon, +1 per 100 sin, and a fate's extra bolts")
	check(near(ProgressionRules.tribulation_damage(1000.0, 0, 0.0, false), 200.0) and near(ProgressionRules.tribulation_damage(1000.0, 500, 0.0, false), 400.0)
		and near(ProgressionRules.tribulation_damage(1000.0, 0, 200.0, true), 200.0), "bolt damage: 20% max HP x (1 + sin/500) x (1 + heart demon/200), guard halves")
	# A tribulation run: every bolt lands on a character who stands still; one talisman takes one bolt.
	Game.world.apply_teleport(c.id, "cp_cleansing_summit")
	cu.realm_key = "cloud_stride_9"
	cu.heart_demon = 0.0
	c.relations.sin = 0
	cu.fates.clear()
	cu.fate_offer = []
	Game.combat.refresh_stats(c.id)
	c.pools.hp = c.pools.max_hp
	Game.inventory.apply_add(c.id, "lightning_rod_talisman", 1, "test")
	var starts := []
	var hook := func(n: String, p: Dictionary): if n == "tribulation_result": starts.append(p)
	GameEvents.event.connect(hook)
	Game.progression._start_tribulation(c, {"to": "spirit_awakening_1", "risk": "low", "from": "cloud_stride_9", "used": [], "causes": [], "bonus": 1.0})
	check(Game.progression.is_under_tribulation(c.id) and int(Game.progression.tribulation_view(c.id).total) == 3, "the cloud gathers: 3 bolts")
	var guard := 0
	while Game.progression.is_under_tribulation(c.id) and guard < 400:
		Game.progression._tick_tribulation(c, 0.1)
		GameEvents.flush()
		guard += 1
	var res: Dictionary = starts.back() if not starts.is_empty() else {}
	check(res.get("survived", false) and int(res.get("absorbed", 0)) == 1 and c.inventory.count("lightning_rod_talisman") == 0,
		"three bolts weathered; the Lightning Rod took one (%s)" % str(res))
	check(cu.realm_key == "spirit_awakening_1", "a weathered tribulation settles the breakthrough")
	var offer: Array = cu.fate_offer.duplicate()
	var distinct := {}
	for f in offer: distinct[f] = true
	check(offer.size() == 3 and distinct.size() == 3 and not offer.has("fox_spirits_favour"), "three distinct fate cards are offered (%s)" % str(offer))
	# Stepping out of the ring: the bolt misses.
	cu.realm_key = "cloud_stride_9"
	c.pools.hp = c.pools.max_hp
	Game.progression._start_tribulation(c, {"to": "spirit_awakening_1", "risk": "low", "from": "cloud_stride_9", "used": [], "causes": [], "bonus": -1.0})
	var home: Vector2 = st.plane
	guard = 0
	while Game.progression.is_under_tribulation(c.id) and guard < 400:
		var tv: Dictionary = Game.progression.tribulation_view(c.id)
		if not (tv.get("warn", {}) as Dictionary).is_empty(): st.plane = Vector2(float(tv.warn.x) + 400.0, float(tv.warn.y))
		Game.progression._tick_tribulation(c, 0.1)
		GameEvents.flush()
		guard += 1
	st.plane = home
	check(int(starts.back().get("struck", -1)) == 0 and bool(starts.back().get("survived", false)), "stepping out of every ring: no bolt lands (%s)" % str(starts.back()))
	check(cu.realm_key == "cloud_stride_9", "a weathered tribulation still rolls the breakthrough (forced to fail here)")
	# Brought to nothing under the heavens: a Bodily failure, not a grave wound.
	c.pools.hp = c.pools.max_hp * 0.1
	Game.progression._start_tribulation(c, {"to": "spirit_awakening_1", "risk": "low", "from": "cloud_stride_9", "used": [], "causes": [], "bonus": 1.0})
	guard = 0
	while Game.progression.is_under_tribulation(c.id) and guard < 400:
		Game.progression._tick_tribulation(c, 0.1)
		GameEvents.flush()
		guard += 1
	check(not starts.back().get("survived", true) and str(starts.back().get("failure", "")) == "bodily_failure" and c.pools.hp > 0.0 and cu.realm_key == "cloud_stride_9",
		"a bolt that would kill fails the breakthrough with the body and leaves the character standing")
	GameEvents.event.disconnect(hook)
	c.cultivator.injuries.clear()
	c.pools.hp = c.pools.max_hp
	# Fates: gifts and costs, realm-long costs that lapse, and what waits for the next tribulation or breakthrough.
	cu.realm_key = "cloud_stride_5"
	cu.fate_offer = []
	check(not Game.submit({"type": "choose_fate", "card": "iron_will"}).get("ok", false), "no fate can be chosen without an offer")
	cu.fate_offer = ["iron_will", "quiet_heart", "hungry_dantian"]
	check(not Game.submit({"type": "choose_fate", "card": "lucky_star"}).get("ok", false), "only an offered card can be chosen")
	Game.combat.refresh_stats(c.id)
	var will0: float = c.stats.value("will")
	var ms0: float = c.stats.value("move_speed")
	check(Game.submit({"type": "choose_fate", "card": "iron_will"}).get("ok", false) and cu.fate_offer.is_empty(), "choosing a card spends the offer")
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("will") >= will0 + 9.9 and c.stats.value("move_speed") < ms0, "Iron Will: +10 Will, slower this realm")
	cu.realm_key = "spirit_awakening_1"
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("will") >= will0 + 9.9 and near(c.stats.value("move_speed"), ms0), "in the next great realm the Will stays and the slowness lapses")
	cu.heart_demon = 30.0
	cu.fate_offer = ["quiet_heart", "hungry_dantian", "debt_of_heaven"]
	Game.submit({"type": "choose_fate", "card": "quiet_heart"})
	check(near(cu.heart_demon, 15.0), "Quiet Heart: heart demon -15")
	cu.pill_resistance = {}
	cu.fate_offer = ["hungry_dantian", "debt_of_heaven", "lucky_star"]
	Game.submit({"type": "choose_fate", "card": "hungry_dantian"})
	check(ProgressionRules.resistance_count(cu, "body") == 1 and ProgressionRules.resistance_count(cu, "accumulation") == 1 and ProgressionRules.resistance_count(cu, "soul") == 1, "Hungry Dantian: pill resistance +1 in every family")
	cu.pill_resistance = {}
	cu.purity = 6
	cu.fate_offer = ["debt_of_heaven", "lucky_star", "iron_will"]
	Game.submit({"type": "choose_fate", "card": "debt_of_heaven"})
	check(cu.purity == 5 and ProgressionRules.tribulation_bolts("cloud_stride_9", 0.0, 0, int(Game.progression._spend_fate_next(c, "tribulation_bolts"))) == 5
		and Game.progression._spend_fate_next(c, "tribulation_bolts") == 0.0, "Debt of Heaven: purity a grade better; the next tribulation alone gets 2 more bolts")
	cu.fate_offer = ["scar_of_failure", "lucky_star", "iron_will"]
	Game.submit({"type": "choose_fate", "card": "scar_of_failure"})
	check(cu.stability == "unstable" and near(Game.progression._spend_fate_next(c, "breakthrough_bonus"), 0.10), "Scar of Failure: unstable now, +10% on the next breakthrough")
	cu.stability = "stable"
	# The draw: distinct, by weight, never an unavailable card, the same for the same seed.
	var pool := ProgressionRules.fate_pool(Game.ctx(c))
	var draws := []
	for run in 2:
		Rng.restore(c.id, {}, 99)
		draws.append(ProgressionRules.draw_fates(pool, 3, Rng.stream(c.id, "breakthrough")))
	check(draws[0] == draws[1], "the same seed draws the same three cards")
	var never := true
	for i in 60:
		for f in ProgressionRules.draw_fates(pool, 3, Rng.stream(c.id, "breakthrough")):
			if str(f) == "fox_spirits_favour": never = false
	check(never, "a card not yet available (Fox Spirit's Favour, S46) is never drawn")
	# Blood Memory: a streak of 10 kills feeds the heart demon only with the fate.
	cu.heart_demon = 0.0
	for i in 10: Game.progression._count_streak(c)
	check(near(cu.heart_demon, 0.0), "a streak of 10 without Blood Memory costs nothing")
	cu.fates.append({"id": "blood_memory", "realm": ProgressionRules.great_realm(cu.realm_key)})
	for i in 10: Game.progression._count_streak(c)
	check(near(cu.heart_demon, 1.0), "Blood Memory: +1 heart demon at a streak of 10 (%.1f)" % cu.heart_demon)
	# Qi Deviation: only at Severe risk or on a Poor method.
	check(ProgressionRules.qi_deviates("severe", "good") and ProgressionRules.qi_deviates("low", "poor") and not ProgressionRules.qi_deviates("high", "excellent"),
		"Qi Deviation only at Severe risk or with a Poor method")
	c.pools.statuses.clear()
	var method_was := cu.method_id
	cu.method_id = "stonebody_canon"
	var earth_was: Dictionary = cu.aptitude.get("element_earth", {}).duplicate()
	cu.aptitude["element_earth"] = {"value": 0.08, "revealed": true}
	Game.progression._maybe_deviate(c, "high")
	check(not c.pools.has_status("qi_deviation"), "a failure at High risk on a good method does not deviate")
	Game.progression._maybe_deviate(c, "severe")
	var els := {}
	for i in 30: els[Game.combat.technique_element(c, ContentDB.entry("techniques", "flowing_palm"))] = true
	check(c.pools.has_status("qi_deviation") and els.size() >= 3, "at Severe risk the Qi deviates: techniques take random elements (%d seen)" % els.size())
	c.pools.statuses.clear()
	check(Game.combat.technique_element(c, ContentDB.entry("techniques", "flowing_palm")) == "water", "once it passes, techniques keep their own element")
	cu.aptitude["element_earth"] = earth_was
	cu.method_id = method_was
	cu.fates.clear()
	cu.fate_offer = []
	cu.realm_key = realm_was
	cu.heart_demon = hd_was
	c.relations.sin = sin_was
	cu.purity = 9
	c.cultivator.injuries.clear()
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 Inner Arts, stances, technique grades, combos
func arts_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var realm_was := cu.realm_key
	var weapon_was = c.inventory.equipped.get("weapon")
	check(ProgressionRules.inner_art_slot_count("bone_forging_9") == 0 and ProgressionRules.inner_art_slot_count("qi_unfurling_1") == 2
		and ProgressionRules.inner_art_slot_count("heart_tempering_1") == 3 and ProgressionRules.inner_art_slot_count("spirit_awakening_1") == 4,
		"Inner Art slots: 2 at Qi Unfurling 1, 3 at Heart Tempering 1, 4 at Spirit Awakening 1")
	cu.realm_key = "qi_unfurling_5"
	cu.inner_arts = []
	cu.inner_arts_known = []
	check(not Game.submit({"type": "equip_inner_art", "slot": 0, "art": "iron_shirt"}).get("ok", false), "an Inner Art not yet learned cannot be worn")
	Game.progression.apply_learn_inner_art(c.id, "iron_shirt")
	Game.progression.apply_learn_inner_art(c.id, "ember_channel")
	Game.progression.apply_learn_inner_art(c.id, "sword_heart")
	Game.progression.apply_learn_inner_art(c.id, "swallows_breath")
	Game.combat.refresh_stats(c.id)
	var pd0: float = c.stats.value("physical_defense")
	check(Game.submit({"type": "equip_inner_art", "slot": 0, "art": "iron_shirt"}).get("ok", false), "Iron Shirt worn in the first slot")
	check(c.stats.value("physical_defense") > pd0 * 1.07, "Iron Shirt: +8%% Physical Defense (%.1f -> %.1f)" % [pd0, c.stats.value("physical_defense")])
	check(not Game.submit({"type": "equip_inner_art", "slot": 2, "art": "ember_channel"}).get("ok", false), "the third slot is closed at Qi Unfurling")
	Game.submit({"type": "equip_inner_art", "slot": 1, "art": "iron_shirt"})
	check(str(cu.inner_arts[0]) == "" and str(cu.inner_arts[1]) == "iron_shirt", "an art moves to the slot it is put in")
	var fire_t := ContentDB.entry("techniques", "ember_burst")
	var cost0 := Game.combat.technique_cost(c, fire_t)
	var water_cost0 := Game.combat.technique_cost(c, ContentDB.entry("techniques", "rising_tide"))
	Game.submit({"type": "equip_inner_art", "slot": 0, "art": "ember_channel"})
	check(Game.combat.technique_cost(c, fire_t) < cost0 * 0.95 and near(Game.combat.technique_cost(c, ContentDB.entry("techniques", "rising_tide")), water_cost0),
		"Ember Channel: Fire techniques cost less, others do not")
	Game.submit({"type": "equip_inner_art", "slot": 0, "art": "swallows_breath"})
	check(near(c.stats.value("dodge_cooldown"), -0.15), "Swallow's Breath: the dodge cooldown 15%% shorter (%.2f)" % c.stats.value("dodge_cooldown"))
	# Weapon-linked: Sword Heart sleeps without a jian.
	cu.realm_key = "heart_tempering_1"
	Game.submit({"type": "equip_inner_art", "slot": 2, "art": "sword_heart"})
	c.inventory.equipped["weapon"] = null
	Game.combat.refresh_stats(c.id)
	check(int(ProgressionRules.path_flag(c, "sword_intent_max", 10)) == 10, "Sword Heart sleeps with bare hands")
	c.inventory.equipped["weapon"] = {"id": "iron_jian", "uid": 900001, "quality": "common"}
	Game.combat.refresh_stats(c.id)
	check(int(ProgressionRules.path_flag(c, "sword_intent_max", 10)) == 12, "with a jian in hand Sword Intent builds to 12")
	# Stances: one per family, and only with that weapon in hand.
	check(not Game.submit({"type": "set_stance", "family": "jian", "stance": "iron_horse"}).get("ok", false), "a stance belongs to its own family")
	var as0: float = c.stats.value("attack_speed")
	var wlp_known: bool = cu.techniques_known.has("willow_leaf_parry")
	cu.techniques_known.erase("willow_leaf_parry")
	check(str(Game.submit({"type": "set_stance", "family": "jian", "stance": "willow_leaf_parry"}).get("reason", "")) == "technique"
		and Game.submit({"type": "set_stance", "family": "jian", "stance": "guarding_blade"}).get("ok", false)
		and float(ProgressionRules.path_flag(c, "parry_counter", 0.0)) == 1.2, "without its technique the jian holds Guarding Blade, not Willow Leaf Parry")
	cu.techniques_known.append("willow_leaf_parry")
	check(Game.submit({"type": "set_stance", "family": "jian", "stance": "willow_leaf_parry"}).get("ok", false), "the jian takes Willow Leaf Parry")
	check(float(ProgressionRules.path_flag(c, "parry_counter", 0.0)) == 2.0 and c.stats.value("attack_speed") < as0, "held: a parry counters for 200%, attacks a little slower")
	Game.submit({"type": "set_stance", "family": "gauntlets", "stance": "iron_horse"})
	check(not ProgressionRules.path_flag(c, "knockback_immune", false), "Iron Horse sleeps while a jian is in hand")
	c.inventory.equipped["weapon"] = {"id": "iron_gauntlets", "uid": 900002, "quality": "common"}
	Game.combat.refresh_stats(c.id)
	check(ProgressionRules.path_flag(c, "knockback_immune", false) and ProgressionRules.path_flag(c, "parry_counter", null) == null,
		"with gauntlets, Iron Horse holds and the jian's stance does not")
	Game.submit({"type": "set_stance", "family": "gauntlets", "stance": ""})
	Game.submit({"type": "set_stance", "family": "jian", "stance": ""})
	check(cu.stances.is_empty(), "letting a stance go clears it")
	# Grades and combos.
	check(near(ProgressionRules.technique_grade_bonus(ContentDB.entry("techniques", "flowing_palm")), 0.0)
		and near(ProgressionRules.technique_grade_bonus(ContentDB.entry("techniques", "crescent_arc")), 0.10)
		and near(ProgressionRules.technique_grade_bonus(ContentDB.entry("techniques", "glimpse_of_heaven")), 0.20), "technique grades: Common +0, Earth +10%, Heaven +20%")
	check(str(ProgressionRules.combo_for("flowing_palm", "tiger_rush", 0.8).get("id", "")) == "palm_into_rush", "Flowing Palm then Tiger Rush within a second: a combo")
	check(ProgressionRules.combo_for("flowing_palm", "tiger_rush", 1.2).is_empty() and ProgressionRules.combo_for("tiger_rush", "flowing_palm", 0.2).is_empty(),
		"too slow, or the wrong order: no combo")
	c.inventory.equipped["weapon"] = weapon_was
	cu.inner_arts = []
	cu.inner_arts_known = []
	cu.stances = {}
	if not wlp_known: cu.techniques_known.erase("willow_leaf_parry")
	cu.realm_key = realm_was
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 vows, Killing Intent, epiphany, Blood Burning, the false realm
func vows_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var st: ActorState = Game.actor_state(c.id)
	var realm_was := cu.realm_key
	c.inventory.bag.fill(null)
	Game.world.apply_teleport(c.id, "wp_west")
	Unlocks.force_unlock(c.id, "vows")
	cu.vows.clear()
	cu.heart_demon = 0.0
	# Vows block what they forbid; letting one go breaks it (+15 heart demon).
	check(Game.submit({"type": "set_vow", "vow": "plain_fare", "on": true}).get("ok", false) and Game.submit({"type": "set_vow", "vow": "fasting", "on": true}).get("ok", false),
		"vows taken: Plain Fare and Fasting")
	Game.inventory.apply_add(c.id, "tiger_blood_pill", 1, "test")
	Game.inventory.apply_add(c.id, "rice_ball", 1, "test")
	Game.inventory.apply_add(c.id, "healing_pill", 1, "test")
	c.pools.cooldowns.clear()
	check(str(Game.inventory.use_item(c, _bag_index(c, "tiger_blood_pill"), true).get("reason", "")) == "vow", "Plain Fare refuses a burst pill")
	check(str(Game.inventory.use_item(c, _bag_index(c, "rice_ball"), true).get("reason", "")) == "vow", "Fasting refuses food that lends a buff")
	check(Game.inventory.use_item(c, _bag_index(c, "healing_pill"), true).get("ok", false), "a healing pill is no burst pill")
	check(near(cu.heart_demon, 0.0), "taking a vow costs nothing")
	Game.submit({"type": "set_vow", "vow": "plain_fare", "on": false})
	check(near(cu.heart_demon, 15.0) and not cu.vows.has("plain_fare"), "breaking a vow: +15 heart demon (%.1f)" % cu.heart_demon)
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("accumulation_rate") >= 0.05 - 0.0001, "Fasting's gift: +5% accumulation")
	Game.submit({"type": "set_vow", "vow": "fasting", "on": false})
	cu.heart_demon = 0.0
	# Mercy: a fleeing foe survives the blow that would have killed it.
	Game.submit({"type": "set_vow", "vow": "mercy", "on": true})
	var e: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(40, 0), 2)
	e.ai["fled"] = true
	var pv: Dictionary = Game.combat.player_view(c)
	var blow := {"damage_type": "physical", "element": "none", "mult": [8.0, 8.0], "range": [1.0, 1.0], "source": "test"}
	for i in 6:
		if not e.alive or e.pools.hp <= 1.01: break
		Game.combat._player_hits_enemy(c, pv, e, blow, 1)
	check(e.alive and e.pools.hp >= 1.0, "Mercy: the fleeing boarlet gets away with its life")
	Game.submit({"type": "set_vow", "vow": "mercy", "on": false})
	for i in 6:
		if not e.alive: break
		Game.combat._player_hits_enemy(c, pv, e, blow, 1)
	check(not e.alive, "without the vow the blow lands")
	GameEvents.flush()
	cu.heart_demon = 0.0
	# Killing Intent: kills in quick succession, +1% crit a stack, up to 10; Silence sheathes it.
	Game.combat.killing_intent.erase(c.id)
	var crit0 := float(Game.combat.player_view(c).crit_chance)
	for i in 12: Game.combat._gain_killing_intent(c, e)
	check(Game.combat.killing_intent_stacks(c.id) == 10 and near(float(Game.combat.player_view(c).crit_chance), crit0 + 0.10),
		"Killing Intent: 10 stacks at most, +10%% crit (%d)" % Game.combat.killing_intent_stacks(c.id))
	for i in 110: Game.combat._tick_sword(c, 0.1)
	check(Game.combat.killing_intent_stacks(c.id) == 0, "ten seconds without a kill and it fades")
	Game.submit({"type": "set_vow", "vow": "silence", "on": true})
	Game.combat._gain_killing_intent(c, e)
	check(Game.combat.killing_intent_stacks(c.id) == 0, "Silence keeps the killing intent sheathed")
	Game.submit({"type": "set_vow", "vow": "silence", "on": false})
	cu.heart_demon = 0.0
	# Epiphany: five times the insight for a minute, then two hours before another.
	cu.epiphany_cooldown = 0.0
	Game.progression.trigger_epiphany(c, Rng.stream(c.id, "fortune"))
	Game.combat.refresh_stats(c.id)
	check(near(cu.epiphany_cooldown, 7200.0) and c.stats.value("insight_rate") >= 3.9, "an epiphany: insight x5 and a two-hour cooldown")
	var seen := 0
	for i in 2000:
		var before := cu.epiphany_cooldown
		Game.progression._roll_epiphany(c, "tech:flowing_palm:x")
		if cu.epiphany_cooldown != before: seen += 1
	check(seen == 0, "no second epiphany while the mind rests")
	cu.epiphany_cooldown = 0.0
	# Blood Burning: 30% of max HP and a body injury for +50% attack.
	cu.realm_key = "sage_sovereign_1"
	Game.combat.refresh_stats(c.id)
	if not cu.techniques_known.has("blood_burning"): cu.techniques_known.append("blood_burning")
	var slots_was: Array = cu.technique_slots.duplicate()
	Unlocks.force_unlock(c.id, "technique_slots_2")
	cu.technique_slots[0] = "blood_burning"
	cu.injuries.clear()
	c.pools.hp = c.pools.max_hp
	c.pools.cooldowns.clear()
	var atk0: float = c.stats.value("physical_attack")
	var max0: float = c.pools.max_hp
	var bb := Game.combat.use_technique(c, 0, 1)
	var hp_after: float = c.pools.hp
	for i in 10: Game.combat.tick(0.1)
	Game.combat.refresh_stats(c.id)
	check(bb.get("ok", false) and absf(hp_after - max0 * 0.7) <= max0 * 0.02 and cu.injuries.has("body"),
		"Blood Burning costs 30%% of max HP and wounds the body (%.0f of %.0f)" % [hp_after, max0])
	check(c.stats.value("physical_attack") > atk0 * 1.4, "and burns +50%% attack (%.0f -> %.0f)" % [atk0, c.stats.value("physical_attack")])
	cu.technique_slots = slots_was
	cu.injuries.clear()
	# The false realm: Concealment shows up to two great realms lower.
	cu.realm_key = "heart_tempering_5"
	var had_conceal := cu.secret_arts.has("concealment")
	cu.secret_arts.erase("concealment")
	check(not Game.submit({"type": "set_false_realm", "realm": "qi_kindling_1"}).get("ok", false), "no false realm without Concealment")
	cu.secret_arts.append("concealment")
	var choices: Array = Game.progression.false_realm_choices(c)
	check(choices == ["qi_kindling_1", "qi_unfurling_1"], "two great realms lower at most (%s)" % str(choices))
	check(not Game.submit({"type": "set_false_realm", "realm": "bone_forging_1"}).get("ok", false), "three great realms lower is too far")
	check(Game.submit({"type": "set_false_realm", "realm": "qi_unfurling_1"}).get("ok", false) and Game.progression.shown_realm(c) == "qi_unfurling_1",
		"others now see Qi Unfurling 1")
	# ...and they talk to the weaker cultivator you show; bandits on the road see easy prey.
	var talk: Dictionary = Game.quest.talk(c, "alliance_guard").get("dialogue", {})
	check(str((talk.get("lines", [""]) as Array)[0]) == str(ContentDB.entry("npcs", "alliance_guard").concealed_lines[0]), "a veiled realm changes what people say")
	var amb: Dictionary = ContentDB.room("cr_caravan_road").get("ambush", {})
	check(near(Game.world.ambush_chance(c, amb), 0.12), "the Mudwater stragglers jump a veiled Heart Tempering at twice the odds (%.2f)" % Game.world.ambush_chance(c, amb))
	Game.submit({"type": "set_false_realm", "realm": ""})
	check(near(Game.world.ambush_chance(c, amb), 0.0), "unveiled at Heart Tempering 5 you are past their reach")
	cu.realm_key = "qi_kindling_8"
	check(near(Game.world.ambush_chance(c, amb), 0.06), "at Qi Kindling 8 the plain odds hold")
	Game.world.load_room(c, "cr_caravan_road", "")
	Game.world.ambush_cd.erase(c.id)
	var sprung := [0]
	var on_amb := func(n: String, _p: Dictionary) -> void:
		if n == "ambush_sprung": sprung[0] += 1
	GameEvents.event.connect(on_amb)
	Game.world.spring_ambush(c, amb)
	GameEvents.flush()
	GameEvents.event.disconnect(on_amb)
	var gang := 0
	for foe in Game.room_rt.living_enemies():
		if foe.summoned and foe.def_id == "mudwater_bandit": gang += 1
	check(gang == 2 and sprung[0] == 1 and float(Game.world.ambush_cd.get(c.id, 0.0)) > 0.0, "an ambush drops two bandits around you and rests (%d)" % gang)
	Game.world.ambush_cd.erase(c.id)
	cu.realm_key = "heart_tempering_5"
	if not had_conceal: cu.secret_arts.erase("concealment")
	# A teacher's lesson opens a rare Dao at exactly tier 1, even under a Dao Echo fate for another Dao.
	Unlocks.force_unlock(c.id, "dao_tree")
	var fates_was: Array = cu.fates.duplicate(true)
	cu.fates.append({"card": "dao_echo", "dao": "sword"})
	cu.daos.erase("blood")
	var room_was := str(c.position.get("room", ""))
	c.position.room = "ir_ancestor_hall"   # a rare Dao deepens only where the Expanse's Laws allow it
	Game.progression.apply_open_dao(c.id, "blood")
	c.position.room = room_was
	check(int(cu.daos.get("blood", {}).get("tier", 0)) == 1, "a teacher opens the Blood Dao at tier 1 under Dao Echo")
	cu.fates = fates_was
	cu.daos.erase("blood")
	# Nascent-soul escape: from Sage a grave wound costs 5% of the stage, not 10%.
	cu.realm_key = "sage_1"
	cu.state = "accumulating"
	cu.qp = cu.need() * 0.5
	Game.progression._on_gravely_wounded({"actor": c.id})
	check(near(cu.qp, cu.need() * 0.45), "from Sage the soul flees: 5%% lost (%.3f of the need left)" % (cu.qp / cu.need()))
	cu.realm_key = "cloud_stride_5"
	cu.qp = cu.need() * 0.5
	Game.progression._on_gravely_wounded({"actor": c.id})
	check(near(cu.qp, cu.need() * 0.4), "below Sage: 10% lost")
	cu.injuries.clear()
	cu.heart_demon = 0.0
	# A boss's nascent-soul self-detonation: telegraphed, then a blast that ends the fight.
	cu.realm_key = realm_was
	Game.combat.refresh_stats(c.id)
	c.pools.hp = c.pools.max_hp
	var boss: EnemyState = Game.enemies.spawn_at("pirate_captain", st.plane + Vector2(120, 0), 80)
	boss.pools.hp = boss.pools.max_hp * 0.35
	Game.enemies._check_phases(boss)
	boss.pools.hp = boss.pools.max_hp * 0.1
	Game.enemies._check_phases(boss)
	check(str(boss.ai.get("state", "")) == "detonating" and boss.invulnerable, "cornered, the Captain burns his nascent soul (a telegraph)")
	var hp_before: float = c.pools.hp
	for i in 40:
		if not boss.alive: break
		Game.enemies.tick(0.1)
	GameEvents.flush()
	check(not boss.alive and c.pools.hp < hp_before - c.pools.max_hp * 0.5, "the blast lands on whoever stays in the ring, and the Captain is gone")
	c.pools.hp = c.pools.max_hp
	cu.vows.clear()
	cu.heart_demon = 0.0
	c.inventory.bag.fill(null)

# ------------------------------------------------------------------ S45 rare herbs, the harvest tap, seeds, seasons
func herbs_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	Unlocks.force_unlock(c.id, "herb_gathering")
	var prof_was: Dictionary = c.professions.get("herb_gathering", {"rank": "apprentice", "xp": 0.0}).duplicate()
	c.professions["herb_gathering"] = {"rank": "adept", "xp": 1000.0}
	var had_conceal := cu.secret_arts.has("concealment")
	cu.secret_arts.erase("concealment")
	# The tap window by rank: 12% Apprentice ... 28% Grandmaster, around the ring's target.
	check(near(HerbRules.tap_window("apprentice"), 0.12) and near(HerbRules.tap_window("expert"), 0.20) and near(HerbRules.tap_window("grandmaster"), 0.28),
		"the tap window widens with rank: 12% / 20% / 28%")
	check(HerbRules.tap_perfect(0.759, "apprentice") and not HerbRules.tap_perfect(0.761, "apprentice") and HerbRules.tap_perfect(0.839, "grandmaster")
		and not HerbRules.tap_perfect(-1.0, "grandmaster"), "a tap is perfect only inside its band; no tap is a miss")
	check(Game.crafting.RANK_CAPS.herb_gathering.back()[1] == "grandmaster", "herb gathering can reach Grandmaster")
	# Ripening: dawn, every 2nd in-game day, 20 minutes.
	Game.world.load_room(c, "dw_bend_shore", "")
	var o: Dictionary = Game.room_rt.object_def("rare_ginseng_bs")
	var L := HerbRules.day_s()
	var centre := float(40000 + int(o.ripen.offset)) * L
	check(HerbRules.ripen_state(o, centre).ripe and HerbRules.ripen_state(o, centre + 590.0).ripe and HerbRules.ripen_state(o, centre - 590.0).ripe,
		"a hundred-year ginseng is ripe for 20 minutes around dawn")
	var after := HerbRules.ripen_state(o, centre + 610.0)
	check(not after.ripe and near(float(after.seconds), 2.0 * L - 1210.0, 1.0) and not HerbRules.ripen_state(o, centre + L).ripe,
		"then it grows for two in-game days (%.0f s to the next window)" % float(after.seconds))
	var st: ActorState = Game.actor_state(c.id)
	var pick := func(obj: Dictionary, timing: float) -> Dictionary:
		Game.room_rt.objects[str(obj.id)] = {"state": "ready", "timer": 0.0, "hits": 0}
		st.plane = Vector2(float(obj.at[0]) - 30.0, float(obj.at[1]))
		st.altitude = float(obj.get("alt", 0))
		var g := Game.submit({"type": "interact", "object": str(obj.id)})
		if not g.get("ok", false): return g
		Game.crafting.pending[c.id].started = Game.sim_time - 5.0
		return Game.submit({"type": "complete_node", "object": str(obj.id), "timing": timing})
	# Picked early, it is a tier younger even with a perfect tap.
	Clock.override_utc = centre + 700.0
	var early: Dictionary = pick.call(o, 0.7)
	check(early.get("ok", false) and str(early.get("item", "")) == "riverreed_ginseng_10" and early.get("early", false), "picked early: a ten-year root (%s)" % str(early.get("item", early)))
	# Ripe, the Tide Crab wakes as you reach for it, once per ripening.
	Clock.override_utc = centre
	var woke := [0]
	var on_wake := func(n: String, p: Dictionary) -> void:
		if n == "guardian_spawned": woke[0] += 1
	GameEvents.event.connect(on_wake)
	var guarded: Dictionary = pick.call(o, 0.7)
	var again: Dictionary = pick.call(o, 0.7)
	GameEvents.flush()
	var keeper: EnemyState = Game.room_rt.enemies.get(int(Game.room_rt.guardians.get("rare_ginseng_bs", -1)))
	check(str(guarded.get("reason", "")) == "guarded" and str(again.get("reason", "")) == "guarded" and woke[0] == 1 and keeper != null and keeper.elite
		and keeper.def_id == "tide_crab", "the Tide Crab guards the ripe root, and wakes once a ripening (%d)" % woke[0])
	# Lured past its leash, it no longer stops you: a perfect tap keeps the full hundred years.
	keeper.plane = Vector2(float(o.at[0]) + 700.0, keeper.plane.y)
	var ripe: Dictionary = pick.call(o, 0.7)
	check(ripe.get("ok", false) and str(ripe.get("item", "")) == "riverreed_ginseng_100" and ripe.get("perfect", false), "lured away: a perfect hundred-year root")
	# The next ripening wakes a new guardian; under Concealment an unaware one lets you pick, but a miss drops a tier.
	Clock.override_utc = centre + 2.0 * L
	pick.call(o, 0.7)
	GameEvents.flush()
	check(woke[0] == 2, "a new ripening, a new guardian (%d)" % woke[0])
	var keeper2: EnemyState = Game.room_rt.enemies.get(int(Game.room_rt.guardians.get("rare_ginseng_bs", -1)))
	cu.secret_arts.append("concealment")
	keeper2.ai["state"] = "idle"
	var unseen: Dictionary = pick.call(o, 0.0)
	check(unseen.get("ok", false) and str(unseen.get("item", "")) == "riverreed_ginseng_10" and not unseen.get("perfect", true), "picked unseen, but a missed tap: ten years")
	keeper2.ai["state"] = "aggro"
	check(str(pick.call(o, 0.7).get("reason", "")) == "guarded", "a guardian that has seen you still stops you")
	GameEvents.event.disconnect(on_wake)
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	# Seeds: a perfect harvest finds one about one time in ten, the same under the same seed.
	Game.world.load_room(c, "cf_falls_pool", "")
	var lotus: Dictionary = Game.room_rt.object_def("rare_lotus_fp")
	var lc := float(30000 * 3 + int(lotus.ripen.offset)) * L + 0.75 * L
	Clock.override_utc = lc
	var rng := Rng.stream(c.id, "crafting")
	var rng_was := rng.state
	var runs: Array = []
	for run in 2:
		rng.seed = 4242
		var seeds := 0
		for i in 80:
			if str(pick.call(lotus, 0.7).get("seed", "")) == "mist_lotus_seed": seeds += 1
		runs.append(seeds)
	rng.state = rng_was
	check(runs[0] == runs[1] and runs[0] >= 2 and runs[0] <= 18, "perfect harvests find Mist Lotus seeds at about 10%%, the same under a fixed seed (%d, %d of 80)" % [runs[0], runs[1]])
	check(ContentDB.config("garden").seeds.get("cloudtop_orchid", "") != "" and HerbRules.harvest_seed("cloudtop_orchid_100") == "",
		"Cloudtop Orchid seeds never come from a harvest")
	# Seasons: the Thicket Heart's hundred-year pepper flowers only in Summer.
	var summer := 1900000000.0
	while HerbRules.season(summer) != "summer": summer += 604800.0
	var pepper: Dictionary = ContentDB.room("bg_thicket_heart").objects.filter(func(x): return str(x.id) == "rare_pepper_th")[0]
	check(HerbRules.in_season(pepper, summer) and not HerbRules.in_season(pepper, summer + 604800.0) and HerbRules.season(summer + 604800.0) == "autumn",
		"seasons turn weekly, and the pepper flowers only in Summer")
	Game.world.load_room(c, "bg_thicket_heart", "")
	Clock.override_utc = summer + 604800.0
	var dormant: Dictionary = pick.call(pepper, 0.7)
	check(not dormant.get("ok", false) and Game.account.codex.has("seasons"), "out of season it lies dormant, and the Codex learns the seasons")
	# An older herb stands in for a younger one when the recipe's own runs short, and refines better.
	for id in ["riverreed_ginseng_10", "riverreed_ginseng_100", "riverreed_ginseng_1000"]:
		Game.inventory.apply_remove(c.id, id, c.inventory.count(id), "test")
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test")
	var a1: Dictionary = Game.crafting.with_aged(c, [{"item": "riverreed_ginseng_10", "count": 1}], 1)
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 1, "test")
	var a2: Dictionary = Game.crafting.with_aged(c, [{"item": "riverreed_ginseng_10", "count": 1}], 1)
	var a3: Dictionary = Game.crafting.with_aged(c, [{"item": "riverreed_ginseng_10", "count": 3}], 1)
	check(a1.inputs == [{"item": "riverreed_ginseng_100", "count": 1}] and int(a1.tiers) == 1, "a hundred-year root stands in for a ten-year one")
	check(a2.inputs == [{"item": "riverreed_ginseng_10", "count": 1}] and int(a2.tiers) == 0, "never while a ten-year root is to hand")
	check(a3.inputs == [{"item": "riverreed_ginseng_10", "count": 3}], "still short: the check asks for the recipe's own herb (%s)" % str(a3.inputs))
	Clock.override_utc = -1.0
	c.professions["herb_gathering"] = prof_was
	if had_conceal and not cu.secret_arts.has("concealment"): cu.secret_arts.append("concealment")
	if not had_conceal: cu.secret_arts.erase("concealment")

# ------------------------------------------------------------------ S45 garden beds, soil, water, dew, transplanting
func garden_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Unlocks.force_unlock(c.id, "herb_garden")
	Unlocks.force_unlock(c.id, "herb_gathering")
	var now := 1950000000.0
	Clock.override_utc = now
	Game.world.load_room(c, "ja_herb_terraces", "")
	var bed := "ja_herb_terraces:bed_0"
	var garden_was: Dictionary = Game.crafting.beds(c).duplicate(true)
	Game.crafting.beds(c).clear()
	for id in ["willow_moss_seed", "cloudtop_orchid_seed", "spring_water", "spirit_soil"]:
		Game.inventory.apply_remove(c.id, id, c.inventory.count(id), "test")
	Game.inventory.apply_add(c.id, "willow_moss_seed", 2, "test")
	Game.inventory.apply_add(c.id, "cloudtop_orchid_seed", 1, "test")
	# Soil caps the grade: a Low bed grows up to Earth; an orchid (Heaven) needs Spirit Soil first.
	var poor := Game.submit({"type": "plant_seed", "bed": bed, "seed": "cloudtop_orchid_seed"})
	check(not poor.get("ok", false) and str(poor.get("reason", "")) == "soil" and Game.crafting.bed_grade(c, bed) == "low", "a Low bed cannot grow a Heaven-grade orchid")
	Game.inventory.apply_add(c.id, "spirit_soil", 1, "test")
	check(Game.submit({"type": "apply_spirit_soil", "bed": bed}).get("ok", false) and Game.crafting.bed_grade(c, bed) == "mid", "Spirit Soil raises the bed to Mid, for good")
	check(Game.submit({"type": "plant_seed", "bed": bed, "seed": "cloudtop_orchid_seed"}).get("ok", false) and c.inventory.count("cloudtop_orchid_seed") == 0,
		"now the orchid takes")
	# Spring water: three bottles a day at a Qi spring, each +25% growth.
	var spring: Dictionary = {}
	for o in ContentDB.room("ja_elder_hu_peak").get("objects", []):
		if str(o.type) == "qi_spring": spring = o
	Unlocks.force_unlock(c.id, "qi_springs")
	var bottled := 0
	for i in 4:
		if Game.crafting.bottle_spring_water(c).get("ok", false): bottled += 1
	check(bottled == 3 and c.inventory.count("spring_water") == 3, "a spring gives three bottles a day (%d)" % bottled)
	Clock.override_utc = now + 86400.0
	check(Game.crafting.bottle_spring_water(c).get("ok", false), "and three more the next day")
	Clock.override_utc = now
	Game.crafting.settle_bed(c, bed)
	check(Game.submit({"type": "water_bed", "bed": bed}).get("ok", false) and near(float(Game.crafting.bed_view(c, bed).progress), 0.25, 0.001), "watering: +25% growth")
	# It grows on the clock, offline too: 8 hours for an orchid, the watered quarter already done.
	Clock.override_utc = now + 6.0 * 3600.0 - 60.0
	check(not Game.crafting.bed_view(c, bed).ready, "not yet at six hours less a minute")
	Clock.override_utc = now + 6.0 * 3600.0 + 1.0
	check(Game.crafting.bed_view(c, bed).ready, "ready after six hours (a quarter watered off eight)")
	var hv := Game.submit({"type": "harvest_bed", "bed": bed})
	check(hv.get("ok", false) and str(hv.get("item", "")) == "cloudtop_orchid" and int(hv.get("count", 0)) >= 2 and str(Game.crafting.bed_view(c, bed).herb) == "",
		"harvest: the orchids, and the bed is free (%s)" % str(hv))
	# The Verdant Dew Vial: a drop a day, offline too, three at most; a drop ages the herb one tier, to 1,000 years.
	Game.inventory.apply_add(c.id, "verdant_dew_vial", 1, "test")
	c.crafting["dew"] = {"count": 0, "last": 0.0}
	check(int(Game.crafting.dew_state(c).dew) == 0, "a new vial starts dry")
	Clock.override_utc = now + 6.0 * 3600.0 + 2.0 * 86400.0 + 10.0
	check(int(Game.crafting.dew_state(c).dew) == 2, "two days away: two drops")
	Clock.override_utc = now + 30.0 * 86400.0
	check(int(Game.crafting.dew_state(c).dew) == 3, "a month away: still three, the vial is full")
	Game.inventory.apply_add(c.id, "riverreed_ginseng_seed", 1, "test")
	Game.submit({"type": "plant_seed", "bed": bed, "seed": "riverreed_ginseng_seed"})
	var d1 := Game.submit({"type": "use_dew", "bed": bed})
	var d2 := Game.submit({"type": "use_dew", "bed": bed})
	var d3 := Game.submit({"type": "use_dew", "bed": bed})
	check(str(d1.get("herb", "")) == "riverreed_ginseng_100" and str(d2.get("herb", "")) == "riverreed_ginseng_1000" and not d3.get("ok", true)
		and int(Game.crafting.dew_state(c).dew) == 1, "dew ages the root to a hundred, then a thousand years, and no further in the valley")
	Game.crafting.beds(c).clear()
	Game.crafting.bed_record(c, bed).soil = 1
	# Transplanting: a Spirit Spade and Expert gathering; 25% it dies at Expert, 20% at Master.
	c.professions["herb_gathering"] = {"rank": "expert", "xp": 5000.0}
	check(not Game.crafting.can_transplant(c), "no spade, no transplant")
	Game.inventory.apply_add(c.id, "spirit_spade", 1, "test")
	check(Game.crafting.can_transplant(c) and near(Game.crafting.transplant_death(c), 0.25), "with a spade at Expert: 25% it dies")
	c.professions["herb_gathering"] = {"rank": "master", "xp": 20000.0}
	check(near(Game.crafting.transplant_death(c), 0.20), "at Master: 20%")
	c.professions["herb_gathering"] = {"rank": "expert", "xp": 5000.0}
	Game.world.load_room(c, "cf_falls_pool", "")
	var lotus: Dictionary = Game.room_rt.object_def("rare_lotus_fp")
	var L := HerbRules.day_s()
	Clock.override_utc = float(30000 * 3 + int(lotus.ripen.offset)) * L + 0.75 * L
	var st: ActorState = Game.actor_state(c.id)
	st.plane = Vector2(float(lotus.at[0]) - 30.0, float(lotus.at[1]))
	st.altitude = float(lotus.alt)
	var prompt := Game.submit({"type": "interact", "object": "rare_lotus_fp"})
	check(prompt.has("dialogue") and (prompt.dialogue.choices as Array).size() == 3, "with a spade, a rare herb asks: pick it or dig it up")
	var rng := Rng.stream(c.id, "garden")
	var rng_was := rng.state
	rng.seed = 777
	var lived := 0
	for i in 100:
		Game.room_rt.objects["rare_lotus_fp"] = {"state": "ready", "timer": 0.0, "hits": 0}
		Game.crafting.bed_record(c, bed).herb = ""
		var tr := Game.submit({"type": "transplant", "object": "rare_lotus_fp"})
		if tr.get("survived", false): lived += 1
	rng.state = rng_was
	check(lived >= 62 and lived <= 88, "three in four transplants live at Expert (%d of 100)" % lived)
	check(str(Game.crafting.bed_view(c, bed).herb) == "mist_lotus_100" or lived < 100, "a transplanted lotus keeps its hundred years in the bed")
	# Spirit Soil drops from strong beasts, on its own stream.
	var soil: Dictionary = ContentDB.config("garden").spirit_soil
	check(near(float(soil.chance), 0.01) and int(soil.min_level) == 19 and ContentDB.entry("loot_tables", "abbots_vault").guaranteed.any(func(g): return str(g.item) == "spirit_soil"),
		"Spirit Soil: 1% from rank 3+ beasts, and one in the Abbot's vault")
	Clock.override_utc = -1.0
	c.crafting["garden"] = garden_was
	for id in ["spirit_spade", "verdant_dew_vial"]: Game.inventory.apply_remove(c.id, id, 1, "test")

# ------------------------------------------------------------------ S45 racks, fakes and garden raids
func herb_prep_suite() -> void:
	var c = Game.active()
	if c == null: return
	Unlocks.force_unlock(c.id, "herb_garden")
	Unlocks.force_unlock(c.id, "appraisal")
	var now := 1960000000.0
	Clock.override_utc = now
	for id in ["mist_lotus", "riverreed_ginseng_10", "riverreed_ginseng_100", "willow_moss", "rice_wine", "dyed_root"]:
		Game.inventory.apply_remove(c.id, id, c.inventory.count(id), "test")
	Game.inventory.apply_add(c.id, "drying_rack", 1, "test")
	c.crafting["racks"] = []
	# Racks: steaming takes an hour; the herbs come back marked.
	Game.inventory.apply_add(c.id, "mist_lotus", 5, "test")
	var sr := Game.submit({"type": "start_rack", "kind": "steamed", "herb": "mist_lotus", "count": 5})
	check(sr.get("ok", false) and c.inventory.count("mist_lotus") == 0 and Game.crafting.racks(c).size() == 1, "five lotus go on the steaming rack")
	check(not Game.submit({"type": "collect_racks"}).get("ok", false), "nothing to take off before the hour")
	Clock.override_utc = now + 3601.0
	check(Game.submit({"type": "collect_racks"}).get("ok", false) and Game.inventory.count_prep(c, "mist_lotus", "steamed") == 5, "an hour later: five steamed lotus")
	# Wine-soaking wants a jar of rice wine for every five herbs, and four hours.
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 3, "test")
	check(str(Game.submit({"type": "start_rack", "kind": "wine", "herb": "riverreed_ginseng_10", "count": 3}).get("reason", "")) == "needs", "no rice wine, no soaking")
	Game.inventory.apply_add(c.id, "rice_wine", 1, "test")
	check(Game.submit({"type": "start_rack", "kind": "wine", "herb": "riverreed_ginseng_10", "count": 3}).get("ok", false) and c.inventory.count("rice_wine") == 0,
		"a jar of rice wine soaks three roots")
	Clock.override_utc = now + 3601.0 + 4.0 * 3600.0
	Game.submit({"type": "collect_racks"})
	check(Game.inventory.count_prep(c, "riverreed_ginseng_10", "wine") == 3, "four hours later: three wine-soaked roots")
	# A pill takes the prep of its principal herb when all of it was prepared.
	Game.inventory.apply_add(c.id, "willow_moss", 2, "test")
	var used: Dictionary = Game.crafting._consume(c, "healing_pill", [{"item": "riverreed_ginseng_10", "count": 1}, {"item": "willow_moss", "count": 2}], "riverreed_ginseng_10")
	check(str(used.prep) == "wine" and Game.inventory.count_prep(c, "riverreed_ginseng_10", "wine") == 2 and not used.fake, "a healing pill from a wine-soaked root is wine-soaked")
	check(near(InventoryAuthority.pill_potency({"id": "healing_pill", "prep": "wine"}), 1.1) and near(InventoryAuthority.pill_toxicity_mult({"id": "healing_pill", "prep": "steamed"}), 0.7),
		"wine-soaked: +10% potency; steamed: -30% toxicity")
	# Sealed herbs: some are fakes, each in its own slot until appraised; a fake in a recipe risks a Flawed pill.
	c.inventory.next_uid += 1
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test", {"unappraised": true, "fake": true, "seal": c.inventory.next_uid})
	c.inventory.next_uid += 1
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test", {"unappraised": true, "fake": false, "seal": c.inventory.next_uid})
	var sealed: Array = []
	for i in c.inventory.bag.size():
		var st = c.inventory.bag[i]
		if st != null and str(st.id) == "riverreed_ginseng_100": sealed.append(i)
	check(sealed.size() == 2 and Game.inventory.count_prep(c, "riverreed_ginseng_100", "") == 0, "two sealed roots, one slot each, not counted as appraised")
	var fake_i := -1
	for i in sealed:
		if c.inventory.bag[i].get("fake", false): fake_i = int(i)
	var had_loupe: bool = Game.crafting.tool_power(c, "appraisal") > 0.0
	var had_eye: bool = c.cultivator.secret_arts.has("appraisal_eye")
	Game.inventory.apply_remove(c.id, "appraisers_loupe", 1, "test")
	c.cultivator.secret_arts.erase("appraisal_eye")
	check(not Game.submit({"type": "appraise_item", "index": fake_i}).get("ok", false), "no loupe, no appraisal")
	Game.inventory.apply_add(c.id, "appraisers_loupe", 1, "test")
	if had_eye: c.cultivator.secret_arts.append("appraisal_eye")
	var ap := Game.submit({"type": "appraise_item", "index": fake_i})
	check(ap.get("ok", false) and ap.get("fake", false) and c.inventory.count("dyed_root") == 1 and c.inventory.count("riverreed_ginseng_100") == 1,
		"appraisal shows the fake: a dyed root")
	var used2: Dictionary = Game.crafting._consume(c, "cleansing_pill", [{"item": "riverreed_ginseng_100", "count": 1}], "mist_lotus")
	check(not used2.fake, "the genuine sealed root is no fake")
	if not had_loupe: Game.inventory.apply_remove(c.id, "appraisers_loupe", 1, "test")
	c.inventory.next_uid += 1
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test", {"unappraised": true, "fake": true, "seal": c.inventory.next_uid})
	check(Game.crafting._consume(c, "cleansing_pill", [{"item": "riverreed_ginseng_100", "count": 1}], "mist_lotus").fake, "an unappraised fake goes into the furnace unseen")
	# Garden raids: an unguarded bed can be hit while you are away; a Protection formation keeps it safe.
	var bed := "ja_herb_terraces:bed_1"
	var garden_was: Dictionary = Game.crafting.beds(c).duplicate(true)
	var forms_was = c.crafting.get("formations", []).duplicate(true)
	c.crafting["formations"] = []
	var raids: Dictionary = ContentDB.config("garden").raids
	var chance_was := float(raids.chance)
	raids.chance = 1.0
	var rec: Dictionary = Game.crafting.bed_record(c, bed)
	rec.herb = "willow_moss"
	rec.progress = 0.5
	rec.updated = Clock.now_utc()
	rec.raid_day = Clock.reset_day(Clock.now_utc()) - 3
	var mails_before: int = c.mail.size() if c.get("mail") is Array else 0
	var hit: Array = Game.crafting.check_raids(c)
	check(hit.size() >= 1 and (str(rec.herb) == "" or float(rec.progress) < 0.5), "an unguarded bed is raided while you are away (%s)" % str(hit))
	rec.herb = "willow_moss"
	rec.progress = 0.5
	rec.raid_day = Clock.reset_day(Clock.now_utc()) - 3
	c.crafting.formations = [{"type": "protection", "room": "ja_herb_terraces", "until_utc": Clock.now_utc() + 86400.0}]
	check(Game.crafting.check_raids(c).is_empty() and str(rec.herb) == "willow_moss" and near(float(rec.progress), 0.5), "a Protection formation keeps the raiders off")
	raids.chance = chance_was
	c.crafting["formations"] = forms_was
	c.crafting["garden"] = garden_was
	Clock.override_utc = -1.0

# ------------------------------------------------------------------ S46 beasts: bloodline, ranks, cores, wounds, taming
func beasts_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	Unlocks.force_unlock(c.id, "spirit_animals")
	Unlocks.force_unlock(c.id, "taming")
	# A new animal's bloodline: purity by rarity, hidden growth and aptitude.
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets[c.pets.size() - 1]
	var g: Dictionary = ContentDB.config("pet_growth")
	check(int(fox.purity) >= 5 and int(fox.purity) <= 15 and float(fox.growth) >= 0.8 and float(fox.growth) <= 1.3
		and float(fox.aptitude.attack) >= 0.8 and float(fox.aptitude.attack) <= 1.2 and str(fox.contract) == "master", "a Common fox: purity 5-15, growth and aptitude rolled, a master's contract")
	check(not Game.pets.aptitude_known(fox), "growth and aptitude stay hidden in a Hatchling")
	fox.stage = "juvenile"
	check(Game.pets.aptitude_known(fox), "a Juvenile shows them")
	var legacy := {"uid": "old_1", "species": "reed_otter", "rarity": "rare"}
	Game.pets.ensure_fields(legacy)
	check(int(legacy.purity) == 38 and near(float(legacy.growth), 1.0) and legacy.learned_skills == [] and not legacy.locked, "an animal from an older save gets neutral fields")
	# Beast rank and nature (Part 8): rank from the Level band, ghosts and constructs have none.
	var crab := ContentDB.entry("enemies", "tide_crab")
	check(int(crab.beast_rank) == 3 and str(crab.nature) == "spirit" and WorldAuthority.beast_rank(crab, 22) == 3 and WorldAuthority.beast_rank(crab, 73) == 9,
		"a Tide Crab is a rank 3 spirit beast")
	check(str(ContentDB.entry("enemies", "mud_hound").nature) == "demonic" and str(ContentDB.entry("enemies", "hollow_stag").nature) == "hollowed"
		and str(ContentDB.entry("enemies", "mirror_wisp").race) == "ghost" and not ContentDB.entry("enemies", "jade_sentinel").has("beast_rank"),
		"natures: demonic and Hollowed; ghosts and constructs are no beasts")
	# Cores: rank 2 and up at 2% a rank, by element and tier.
	check(WorldAuthority.beast_core_for(crab, 22) == "water_core_low" and near(WorldAuthority.core_chance(crab, 22), 0.06)
		and WorldAuthority.beast_core_for(ContentDB.entry("enemies", "reedtail_rat"), 2) == "" and WorldAuthority.beast_core_for(ContentDB.entry("enemies", "mirror_wisp"), 49) == "",
		"a rank 3 crab carries a Low Water Core 6% of the time; rank 1 beasts and ghosts carry none")
	# Devouring: only its own element.
	Game.inventory.apply_add(c.id, "fire_core_low", 2, "test")
	Game.inventory.apply_add(c.id, "water_core_low", 1, "test")
	var xp0 := float(fox.xp) + 20.0 * pow(int(fox.level), 1.5) * 0.0
	var lv0 := int(fox.level)
	check(Game.submit({"type": "devour_core", "pet": fox.uid, "item": "fire_core_low"}).get("ok", false) and (int(fox.level) > lv0 or float(fox.xp) > xp0),
		"the fox devours a fire core and grows")
	check(str(Game.submit({"type": "devour_core", "pet": fox.uid, "item": "water_core_low"}).get("reason", "")) == "wrong_element", "but will not touch a water core")
	# The Core Exchange at the Beast Hall: fixed stones by tier, 60 a day.
	check(str(Game.submit({"type": "sell_cores", "item": "fire_core_low", "count": 1}).get("reason", "")) == "not_here", "the Exchange is at the Beast Hall")
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	c.crafting.erase("core_exchange")
	Game.inventory.apply_add(c.id, "earth_core_peak", 5, "test")
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	var sold := Game.submit({"type": "sell_cores", "item": "earth_core_peak", "count": 5})
	check(sold.get("ok", false) and int(sold.count) == 3 and int(Game.account.currencies.get("spirit_stone", 0)) - stones0 == 60 and Game.pets.exchange_left(c) == 0,
		"peak cores at 20 stones: three a day fill the cap of 60 (%s)" % str(sold))
	# Grievous Wound: three knockouts in five minutes; the Beast Revival Pill mends it.
	c.active_pet = str(fox.uid)
	var hp0: float = Game.pets.stat_mult(fox, "hp")
	for i in 3: Game.pets._knocked_out(c, fox)
	GameEvents.flush()
	check(fox.wounded and near(Game.pets.stat_mult(fox, "hp"), hp0 * 0.8, 0.001), "three knockouts in five minutes: a Grievous Wound, -20%")
	Game.inventory.apply_add(c.id, "beast_revival_pill", 1, "test")
	Game.submit({"type": "use_item", "index": _bag_index(c, "beast_revival_pill"), "confirm": true})
	check(not fox.wounded, "a Beast Revival Pill mends it")
	fox.knockouts = []
	Game.pets._knocked_out(c, fox)
	Game.pets._knocked_out(c, fox)
	Game.sim_time += 400.0
	Game.pets._knocked_out(c, fox)
	check(not fox.wounded, "three knockouts spread over more than five minutes do not")
	# Taming by nature: a demonic hound takes only a Purifying Offering; a Hollowed boarlet must be cleansed first.
	var st: ActorState = Game.actor_state(c.id)
	var hound: EnemyState = Game.enemies.spawn_at("mud_hound", st.plane + Vector2(60, 0), 18)
	hound.pools.hp = hound.pools.max_hp * 0.1
	Game.inventory.apply_add(c.id, "bonding_offering_common", 3, "test")
	Game.inventory.apply_add(c.id, "purifying_offering", 3, "test")
	check(str(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("reason", "")) == "demonic", "a Bonding Offering does nothing for a demonic hound")
	var tp := Game.submit({"type": "attempt_tame", "offering": "purifying_offering"})
	check(tp.get("ok", false) and str(tp.get("species", "")) == "mud_hound", "a Purifying Offering can tame it")
	var boar: EnemyState = Game.enemies.spawn_at("hollowed_boarlet", st.plane + Vector2(60, 0), 10)
	boar.pools.hp = boar.pools.max_hp * 0.1
	check(str(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("reason", "")) == "hollowed", "a Hollowed boarlet cannot be tamed as it is")
	check(Game.submit({"type": "attempt_tame", "offering": "purifying_offering"}).get("cleansed", false) and boar.ai.get("cleansed", false), "the Purifying Offering cleanses it")
	var tb := Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"})
	check(tb.get("ok", false) and not tb.has("cleansed") and str(tb.get("species", "")) == "cleansed_boarlet", "then any offering can tame it")
	# The taming fix: struck down with an offering on quick-use, a tameable beast stays subdued at 1 HP.
	var otter: EnemyState = Game.enemies.spawn_at("reed_otter", st.plane + Vector2(60, 0), 20)
	c.inventory.quick_use = "bonding_offering_common"
	Game.combat._damage_enemy(otter, otter.pools.max_hp * 5.0, c.id, "physical", "none", false, {})
	check(otter.alive and near(otter.pools.hp, 1.0) and otter.ai.get("subdued_once", false), "a one-hit otter is subdued at 1 HP, not killed")
	Game.combat._damage_enemy(otter, 10.0, c.id, "physical", "none", false, {})
	check(not otter.alive, "only once: the next blow lands")
	c.inventory.quick_use = ""
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	c.pets = pets_was
	c.active_pet = active_was

## S46 · bloodline awakenings, suppression, contracts, command capacity, incubation input and beast medicine.
func bloodline_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var party_was: Array = c.party_pets.duplicate()
	var eggs_was: Array = c.eggs.duplicate(true)
	var realm_was: String = c.cultivator.realm_key
	var fates_was: Array = c.cultivator.fates.duplicate(true)
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	c.quests.flags.erase("equal_contract")
	c.cooldowns.erase("essence_blood")
	Unlocks.force_unlock(c.id, "spirit_animals")
	Unlocks.force_unlock(c.id, "spirit_eggs")
	Game.world.load_room(c, "lf_reed_shallows", "")
	var heard := {}
	GameEvents.event.connect(func(n, p): heard[n] = p)
	# Purity thresholds: 49 and 50, 89 and 90.
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets[c.pets.size() - 1]
	c.active_pet = str(fox.uid)
	fox.purity = 48
	Game.pets.add_purity(c, fox, 1)
	GameEvents.flush()
	check(int(fox.purity) == 49 and int(fox.get("awakened", 0)) == 0 and Game.pets.bloodline_skill(fox).is_empty(), "purity 49: no awakening yet")
	Game.pets.add_purity(c, fox, 1)
	GameEvents.flush()
	check(int(fox.awakened) == 1 and str(Game.pets.bloodline_skill(fox).get("name", "")) == "Nine-Tail Flame" and int(heard.get("bloodline_awakened", {}).get("step", 0)) == 1,
		"purity 50: the Nine-Tail Flame awakens")
	var m89 := Game.pets.stat_mult(fox, "attack")
	fox.purity = 88
	Game.pets.add_purity(c, fox, 1)
	check(int(fox.awakened) == 1 and Game.pets.form_of(fox).is_empty(), "purity 89: still its first form")
	Game.pets.add_purity(c, fox, 1)
	GameEvents.flush()
	check(int(fox.awakened) == 2 and str(Game.pets.form_of(fox).get("name", "")) == "Nine-Tail Fox" and near(Game.pets.stat_mult(fox, "attack"), m89 * 1.1, 0.001),
		"purity 90: the Nine-Tail Fox, +10% to every stat")
	check(int(heard.get("bloodline_awakened", {}).get("step", 0)) == 2, "each awakening is announced once")
	Game.pets.add_purity(c, fox, 50)
	check(int(fox.purity) == 100, "purity stops at 100")
	# Trait strength: +0.2% a point of purity.
	fox.traits = ["stormborn", "quick_paws", "loyal"]
	fox.revealed = 1
	fox.purity = 0
	var t0 := Game.pets._trait_sum(fox, "pet_damage")
	fox.purity = 100
	check(near(t0, 0.15) and near(Game.pets._trait_sum(fox, "pet_damage"), 0.15 * 1.2), "a pure bloodline strengthens its traits by 20%")
	# Suppression (the Pressure contest): an Epic, awakened fox cows a rank 1 rat, not a rank 9 boss.
	check(near(CombatRules.pressure_loss(2.0, 1.0), 0.25) and near(CombatRules.pressure_loss(1.0, 2.0), 0.0) and near(CombatRules.pressure_loss(9.0, 1.0), 0.5),
		"Pressure over Will: min(50%, 25% x (P/W - 1))")
	fox.rarity = "epic"
	var st: ActorState = Game.actor_state(c.id)
	var rat: EnemyState = Game.enemies.spawn_at("reedtail_rat", st.plane + Vector2(80, 0), 2)
	check(Game.pets.bloodline_tier(fox) == 6 and Game.pets.beast_tier(rat) == 1 and Game.pets.suppresses(fox, rat), "an Epic fox with both awakenings (tier 6) outranks a rank 1 rat (tier 1)")
	fox.rarity = "common"
	fox.awakened = 0
	check(not Game.pets.suppresses(fox, rat), "a Common fox (tier 1) does not")
	Unlocks.force_unlock(c.id, "taming")
	rat.pools.hp = rat.pools.max_hp * 0.1
	var plain := Game.pets.tame_chance(c, rat, "bonding_offering_common", 0.5)
	fox.rarity = "epic"
	fox.awakened = 2
	check(near(Game.pets.tame_chance(c, rat, "bonding_offering_common", 0.5), minf(plain + 0.1, float(ContentDB.config("taming").get("max", 0.95)))),
		"suppression adds +10% to the taming chance")
	Game.pets._spawn(c)
	var ally: EnemyState = Game.room_rt.enemies.get(Game.pets.ally_uid)
	check(ally != null and float(ally.def.art.get("scale", 1.0)) > 1.0, "the true form stands larger")
	if ally != null:
		ally.plane = rat.plane + Vector2(-40, 0)
		ally.ai.sup_t = 0.0
		Game.pets._suppress(c, fox, ally, 0.1)
		GameEvents.flush()
		check(rat.ai.get("suppressed", false) and rat.pools.has_status("fear") and heard.has("beast_suppressed"), "and its blood grips the rat with Fear")
	Game.enemies.release(rat)
	# Skill casts: the awakened skill hits x2.5 every 12 s.
	if ally != null:
		ally.ai.state = "windup"
		ally.ai.timer = 0.01
		ally.ai.skill_cd = 0.0
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 2.5) and float(ally.ai.skill_cd) > 11.0, "the bloodline skill lands at x2.5, then rests 12 s")
		ally.ai.timer = 0.01
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 1.0), "not again while it rests")
	# Contracts: Equal at 10 hearts, once per character; Blood with essence blood.
	fox.bond = 9.0
	check(str(Game.submit({"type": "offer_contract", "pet": fox.uid, "kind": "equal"}).get("reason", "")) == "hearts", "no Equal Contract at 9 hearts")
	heard.erase("contract_offered")
	Game.pets.apply_bond(c.id, 1.0, str(fox.uid))
	GameEvents.flush()
	check(heard.has("contract_offered"), "at 10 hearts the fox offers one")
	check(Game.submit({"type": "offer_contract", "pet": fox.uid, "kind": "equal"}).get("ok", false) and str(fox.contract) == "equal", "an Equal Contract is formed")
	if ally != null:
		ally = Game.room_rt.enemies.get(Game.pets.ally_uid)
		ally.ai.state = "windup"
		ally.ai.timer = 0.01
		ally.ai.skill_cd = 5.0
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 2.5) and not ally.ai.free_cast, "Equal: one free skill cast in a fight")
		ally.ai.timer = 0.01
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 1.0), "only one")
	Game.pets.apply_grant(c.id, "reed_otter")
	var otter: Dictionary = c.pets[c.pets.size() - 1]
	otter.bond = 10.0
	check(str(Game.submit({"type": "offer_contract", "pet": otter.uid, "kind": "equal"}).get("reason", "")) == "once", "one Equal Contract per character, ever")
	check(str(Game.submit({"type": "offer_contract", "pet": otter.uid, "kind": "blood"}).get("reason", "")) == "no_blood", "a Blood Contract needs essence blood")
	Game.inventory.apply_add(c.id, "beast_essence_blood", 3, "test")
	var om := Game.pets.stat_mult(otter, "hp")
	check(Game.submit({"type": "offer_contract", "pet": otter.uid, "kind": "blood"}).get("ok", false) and near(Game.pets.stat_mult(otter, "hp"), om * 1.15, 0.001)
		and c.inventory.count("beast_essence_blood") == 2, "a Blood Contract: +15% stats for a drop of essence blood")
	# Command capacity by realm, and the party beside you (called somewhere safe: the field needs the Beast Bag).
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	c.cultivator.realm_key = "heart_tempering_9"
	check(Game.pets.command_capacity(c) == 1, "one animal at a time before Spirit Awakening")
	check(str(Game.submit({"type": "set_party", "pet": otter.uid, "on": true}).get("reason", "")) == "capacity", "a second must wait")
	c.cultivator.realm_key = "spirit_awakening_1"
	check(Game.pets.command_capacity(c) == 2, "two from Spirit Awakening")
	check(Game.submit({"type": "set_party", "pet": otter.uid, "on": true}).get("ok", false) and Game.pets.allies.size() == 2 and Game.pets.party(c).size() == 2,
		"the otter walks beside the fox")
	c.cultivator.realm_key = "sage_1"
	check(Game.pets.command_capacity(c) == 3, "three from Sage")
	# A Blood-bound animal knocked out bruises its owner's soul.
	var inj0 := int(c.cultivator.injuries.get("soul", {}).get("severity", 0))
	var oa: EnemyState = Game.room_rt.enemies.get(int(Game.pets.allies.get(str(otter.uid), 0)))
	if oa != null: Game.pets.apply_retreat(oa)
	check(oa != null and int(c.cultivator.injuries.get("soul", {}).get("severity", 0)) == inj0 + 1, "the otter's knockout gives a soul injury")
	c.cultivator.injuries.erase("soul")
	Game.submit({"type": "set_party", "pet": otter.uid, "on": false})
	check(c.party_pets.is_empty() and Game.pets.allies.size() == 1, "sent home again")
	# Resonance flows both ways under an Equal Contract.
	fox.role = "combat"
	fox.stage = "adult"
	check(Game.pets.resonance(c) > 0.0, "an Equal animal resonates whatever its role")
	var xp0 := float(fox.xp)
	var lv0 := int(fox.level)
	GameEvents.emit_event("meditation_tick", {"actor": c.id})
	GameEvents.flush()
	check(float(fox.xp) > xp0 or int(fox.level) > lv0, "and your meditation feeds it")
	# Incubation input.
	c.eggs = [{"species": "reed_otter", "hatch_utc": Clock.now_utc() - 1.0}]
	var hp_before: float = c.pools.max_hp
	check(Game.submit({"type": "incubate_input", "egg": 0, "kind": "blood"}).get("ok", false) and near(c.pools.max_hp, hp_before * 0.9, hp_before * 0.02)
		and float(c.cooldowns.get("essence_blood", 0.0)) > Clock.now_utc() + 23.0 * 3600.0, "your essence blood: -10% max HP for 24 h")
	check(str(Game.submit({"type": "incubate_input", "egg": 0, "kind": "blood"}).get("reason", "")) == "already", "once per egg")
	Game.inventory.apply_add(c.id, "earth_core_low", 1, "test")
	check(str(Game.submit({"type": "incubate_input", "egg": 0, "kind": "element", "item": "earth_core_low"}).get("reason", "")) == "no_element", "no egg of earth answers an earth core")
	Game.inventory.apply_add(c.id, "fire_core_low", 1, "test")
	check(Game.submit({"type": "incubate_input", "egg": 0, "kind": "element", "item": "fire_core_low"}).get("ok", false) and str(c.eggs[0].species) == "ember_fox",
		"a fire core steers the egg to fire")
	check(Game.submit({"type": "incubate_input", "egg": 0, "kind": "reroll"}).get("ok", false) and (c.eggs[0].traits as Array).size() == 3, "essence blood rerolls a hidden trait")
	c.cultivator.fates.append({"id": "fox_spirits_favour", "realm": "sage", "next": {"egg_purity": 10}})
	var n0: int = c.pets.size()
	Game.submit({"type": "hatch_egg", "index": 0})
	var chick: Dictionary = c.pets[c.pets.size() - 1] if c.pets.size() > n0 else {}
	check(not chick.is_empty() and near(float(chick.bond), 3.0) and int(chick.purity) >= 25 and str(chick.species) == "ember_fox",
		"a self-warmed hatchling starts at 3 hearts with +10 purity and Fox Spirit's Favour's +10 (%s)" % str(chick.get("purity", "")))
	check(ProgressionRules.fate_pool(Game.ctx(c)).any(func(f): return str(f.id) == "fox_spirits_favour"), "Fox Spirit's Favour is in the deck once eggs are open")
	c.cooldowns["essence_blood"] = Clock.now_utc() - 1.0
	Game.pets.essence_check = 0.0
	Game.pets.tick(0.1)
	check(not c.cooldowns.has("essence_blood") and near(c.pools.max_hp, hp_before, hp_before * 0.02), "a day later your blood has recovered")
	# Beast medicine: essence blood lifts purity; the marrow pill needs a Juvenile and leaves no toxicity.
	c.active_pet = str(chick.uid)
	var pu0 := int(chick.purity)
	Game.submit({"type": "use_item", "index": _bag_index(c, "beast_essence_blood"), "confirm": true})
	check(int(chick.purity) == mini(100, pu0 + 10), "Beast Essence Blood: +10 purity")
	Game.inventory.apply_add(c.id, "beast_marrow_washing_pill", 2, "test")
	check(str(Game.submit({"type": "use_item", "index": _bag_index(c, "beast_marrow_washing_pill"), "confirm": true}).get("reason", "")) == "too_young"
		and c.inventory.count("beast_marrow_washing_pill") == 2, "the marrow pill waits for a Juvenile, and is not spent")
	chick.stage = "juvenile"
	chick.aptitude = {"hp": 1.1, "attack": 0.8, "defence": 1.0, "speed": 1.2}
	var tox0: float = c.cultivator.toxicity
	check(Game.submit({"type": "use_item", "index": _bag_index(c, "beast_marrow_washing_pill"), "confirm": true}).get("ok", false)
		and near(float(chick.aptitude.hp), 1.1) and near(float(chick.aptitude.speed), 1.2) and near(c.cultivator.toxicity, tox0), "it rolls only the weakest gift again, with no toxicity")
	c.pets = pets_was
	c.active_pet = active_was
	c.party_pets = party_was
	c.eggs = eggs_was
	c.cultivator.realm_key = realm_was
	c.cultivator.fates = fates_was
	c.quests.flags.erase("equal_contract")
	c.cooldowns.erase("essence_blood")
	Game.combat.refresh_stats(c.id)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S46 · skill books, pet gear, fusion, pet breakthroughs and Pet Core Formation.
func pet_growth_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var party_was: Array = c.party_pets.duplicate()
	var realm_was: String = c.cultivator.realm_key
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var cap0: int = c.inventory.capacity()
	Unlocks.force_unlock(c.id, "spirit_animals")
	c.inventory.bag.fill(null)
	Game.world.load_room(c, "lf_reed_shallows", "")
	c.cultivator.realm_key = "sage_1"
	Game.pets.apply_grant(c.id, "reed_otter")
	var otter: Dictionary = c.pets[c.pets.size() - 1]
	c.active_pet = str(otter.uid)
	c.party_pets = []
	# Skill books: no slots as a Hatchling; a Juvenile has 2; when full a new book takes a random slot.
	Game.inventory.apply_add(c.id, "pet_book_iron_hide", 1, "test")
	check(str(Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_iron_hide"}).get("reason", "")) == "cannot_learn"
		and c.inventory.count("pet_book_iron_hide") == 1, "a Hatchling cannot learn, and the book is kept")
	otter.stage = "juvenile"
	check(Game.pets.skill_slots(otter) == 2 and Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_iron_hide"}).get("ok", false)
		and Game.pets.has_skill(otter, "iron_hide"), "a Juvenile learns Iron Hide into its first slot")
	Game.inventory.apply_add(c.id, "pet_book_deep_pockets", 1, "test")
	Game.submit({"type": "use_item", "index": _bag_index(c, "pet_book_deep_pockets"), "confirm": true})
	check(Game.pets.has_skill(otter, "deep_pockets") and (otter.learned_skills as Array).size() == 2, "a book used from the gourd teaches the active animal")
	check(c.inventory.capacity() == cap0 + 6, "Deep Pockets: one more row in the gourd while it is active (%d)" % c.inventory.capacity())
	Game.inventory.apply_add(c.id, "pet_book_frenzy", 2, "test")
	var rng: RandomNumberGenerator = Rng.stream(c.id, "pet")
	var st0 := rng.state
	var learned0: Array = (otter.learned_skills as Array).duplicate()
	var r1 := Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_frenzy"})
	var after1: Array = (otter.learned_skills as Array).duplicate()
	check(r1.get("ok", false) and after1.size() == 2 and after1.has("frenzy") and learned0.has(str(r1.get("replaced", ""))), "slots full: Frenzy overwrites a random slot (%s)" % str(r1.get("replaced", "")))
	otter.learned_skills = learned0.duplicate()
	rng.state = st0
	Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_frenzy"})
	check(otter.learned_skills == after1, "under the same seed the same slot is overwritten")
	otter.learned_skills = ["iron_hide", "deep_pockets"]
	Game.pets._apply_pockets(c)
	# Iron Hide in combat; Herb Whisper beside you; Thunder Roar; Guardian Spirit; Frenzy after a kill.
	Game.pets._spawn(c)
	var ally: EnemyState = Game.room_rt.enemies.get(Game.pets.ally_uid)
	check(ally != null and near(Game.pets.damage_taken_mult(ally), 1.0 + Game.pets._trait_sum(otter, "pet_damage_taken") - 0.1), "Iron Hide: 10% less damage")
	check(Game.pets.whisper_range(c) == 0.0, "no Herb Whisper yet")
	otter.learned_skills = ["herb_whisper", "thunder_roar"]
	Game.pets._apply_pockets(c)
	check(c.inventory.capacity() == cap0 and near(Game.pets.whisper_range(c), 400.0), "Deep Pockets forgotten: the row goes; Herb Whisper reads herbs within 400")
	var st: ActorState = Game.actor_state(c.id)
	if ally != null:
		var rat: EnemyState = Game.enemies.spawn_at("reedtail_rat", ally.plane + Vector2(40, 0), 2)
		ally.ai.roar_cd = 0.0
		Game.pets._roar(c, otter, ally, 0.1)
		check(rat.pools.has_status("stun") and float(ally.ai.roar_cd) > 14.0, "Thunder Roar stuns a foe beside it, then rests 15 s")
		Game.enemies.release(rat)
		otter.learned_skills = ["guardian_spirit", "frenzy"]
		Game.pets.guardian_cd.erase(c.id)
		check(Game.pets.guardian_absorbs(c) and not Game.pets.guardian_absorbs(c), "Guardian Spirit takes one blow, then waits 30 s")
		Game.pets._on_actor_defeated({"victim_kind": "enemy", "level": 1})
		check(float(ally.ai.get("frenzy", 0.0)) > 5.0, "Frenzy: a kill quickens it for 6 s")
	# Pet gear: worn through the equip intent, +10% of base a level of enhancement; a saddle only on a mount.
	otter.learned_skills = []
	var hp0: float = Game.pets.stat_mult(otter, "hp")
	Game.inventory.apply_add_equipment(c.id, "bone_collar", 14, "common", "test")
	check(Game.submit({"type": "equip", "index": _bag_index(c, "bone_collar")}).get("ok", false) and otter.equipment.has("pet_collar")
		and near(Game.pets.stat_mult(otter, "hp"), hp0 * 1.1, 0.001), "a Bone Collar on the otter: +10% HP")
	otter.equipment.pet_collar.enhance = 2
	check(near(Game.pets.gear_bonus(otter, "hp"), 0.12), "enhanced +2: +12%")
	Game.inventory.apply_add_equipment(c.id, "reed_saddle", 14, "common", "test")
	check(str(Game.submit({"type": "equip_pet", "pet": otter.uid, "index": _bag_index(c, "reed_saddle")}).get("reason", "")) == "not_mountable", "a saddle only fits a mount")
	check(Game.submit({"type": "unequip_pet", "pet": otter.uid, "slot": "pet_collar"}).get("ok", false) and c.inventory.count("bone_collar") == 1, "taken off, back to the gourd")
	check(ContentDB.item("scale_talisman").has("pet_gear") and ContentDB.has_entry("recipes", "bone_collar"), "pet gear is forged")
	# Fusion: at the Beast Hall, never a locked animal, only when confirmed; half the purity gap carries over.
	Game.pets.apply_grant(c.id, "reed_otter")
	var spare: Dictionary = c.pets[c.pets.size() - 1]
	otter.purity = 20
	spare.purity = 60
	check(str(Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid, "confirm": true}).get("reason", "")) == "cannot_fuse", "fusion only at the Beast Hall")
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	spare.locked = true
	check(str(Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid, "confirm": true}).get("reason", "")) == "cannot_fuse", "a locked animal is never fused")
	spare.locked = false
	check(str(Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid}).get("reason", "")) == "confirm", "fusion asks for confirmation")
	var n0: int = c.pets.size()
	var fz := Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid, "confirm": true})
	check(fz.get("ok", false) and c.pets.size() == n0 - 1 and int(otter.purity) == 40, "fused: the spare is gone and half its purity above the otter's carries over (%d)" % int(otter.purity))
	# Fusion odds: about 30% for each trait and learned skill.
	var tries := 0
	var hits := 0
	for i in 60:
		Game.pets.apply_grant(c.id, "mossback_toad")
		var b: Dictionary = c.pets[c.pets.size() - 1]
		b.traits = ["stormborn", "keen_nose", "lucky_find"]
		b.learned_skills = []
		otter.traits = ["deep_diver", "iron_hide", "loyal"]
		otter.revealed = 0
		var f2 := Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": b.uid, "confirm": true})
		tries += 3
		hits += (f2.get("traits", []) as Array).size()
	var rate := float(hits) / float(tries)
	check(rate > 0.2 and rate < 0.4, "each trait carries over about 30%% of the time (%.2f over %d)" % [rate, tries])
	# Breakthroughs from Awakened on: evolve refuses, the breakthrough rolls; Core Formation grades the core.
	otter.stage = "adult"
	otter.level = 55
	otter.bond = 7.0
	otter.wounded = false
	check(str(Game.submit({"type": "evolve_pet", "pet": otter.uid}).get("reason", "")) == "breakthrough", "Adult to Awakened is a breakthrough, not a plain evolve")
	Game.inventory.apply_add(c.id, "water_core_mid", 1, "test")
	Game.inventory.apply_add(c.id, "beast_essence_blood", 1, "test")
	var base := Game.pets.breakthrough_chance(c, otter, [])
	check(near(Game.pets.breakthrough_chance(c, otter, ["water_core_mid", "beast_essence_blood"]), minf(0.95, base + 0.25)) and near(Game.pets.support_value(otter, "fire_core_mid"), 0.0),
		"a core of its own element and essence blood raise the chance; another element's core does not")
	var bcfg: Dictionary = ContentDB.config("pet_growth").breakthrough
	var base_was: float = float(bcfg.base)
	bcfg.base = 5.0
	var ok1 := Game.submit({"type": "pet_breakthrough", "pet": otter.uid, "support": ["water_core_mid"]})
	check(ok1.get("success", false) and str(otter.stage) == "awakened" and str(otter.get("core_grade", "")) != "" and c.inventory.count("water_core_mid") == 0,
		"a breakthrough: Awakened, a %s, the support spent" % str(otter.get("core_grade", "")))
	var cg: Dictionary = Game.pets.core_grade_def(str(otter.core_grade))
	check(near(Game.pets.core_bonus(otter), float(cg.get("bonus", 0.0))), "the core grade adds to every stat")
	bcfg.base = -5.0
	otter.level = 75
	otter.bond = 9.0
	c.cultivator.realm_key = "sphere_lord_1"
	var fb := Game.submit({"type": "pet_breakthrough", "pet": otter.uid, "support": []})
	check(not fb.get("success", true) and str(otter.stage) == "awakened" and (float(otter.bond) < 9.0 or otter.wounded), "a failure costs a heart or leaves a wound (%s)" % str(fb.get("lost", "")))
	bcfg.base = base_was
	c.pets = pets_was
	c.active_pet = active_was
	c.party_pets = party_was
	c.cultivator.realm_key = realm_was
	Game.pets._apply_pockets(c)
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S46 · the Spirit Beast Bag and field swaps, the Mount slot and mount-only species, rarity rolls, Beast Kings and
## their nests, the Beast Tide, and pets that never die.
func beast_world_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var bag_was: Array = c.pet_bag.duplicate()
	var realm_was: String = c.cultivator.realm_key
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var timers_was: Dictionary = Game.account.rooms.get("field_boss_timers", {}).duplicate()
	var keys_was: Array = c.inventory.key_items.duplicate(true)
	Unlocks.force_unlock(c.id, "spirit_animals")
	Unlocks.force_unlock(c.id, "mounts")
	c.inventory.bag.fill(null)
	c.cultivator.realm_key = "cloud_stride_1"
	c.pets = []
	c.active_pet = ""
	c.pet_bag = []
	c.mount_pet = ""
	c.riding = false
	# Rarity rolls: a wild tame is mostly Common, an elite never is, a King's egg is Rare or finer.
	var counts := {}
	for i in 300:
		var r: String = Game.pets.roll_rarity(c, "tame")
		counts[r] = int(counts.get(r, 0)) + 1
	check(int(counts.get("common", 0)) > 150 and int(counts.get("common", 0)) < 270, "a wild tame is Common about 70%% of the time (%s)" % str(counts))
	var ok_elite := true
	var ok_rare := true
	for i in 60:
		if Game.pets.roll_rarity(c, "tame_elite") == "common": ok_elite = false
		if not Game.pets.roll_rarity(c, "rare") in ["rare", "epic", "primordial"]: ok_rare = false
	check(ok_elite and ok_rare, "an elite is never Common; a nest egg is Rare or better")
	Unlocks.force_unlock(c.id, "spirit_eggs")
	Game.inventory.apply_add(c.id, "cloud_stag_egg", 1, "test")
	Game.submit({"type": "use_item", "index": _bag_index(c, "cloud_stag_egg"), "confirm": true})
	check(not c.eggs.is_empty() and str(c.eggs.back().species) == "cloud_stag" and c.eggs.back().has("rarity"), "the Beast Tide's egg holds a Cloud Stag")
	c.eggs = []
	# The Spirit Beast Bag: carried animals, swapped in the field but never in a fight.
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets.back()
	Game.pets.apply_grant(c.id, "reed_otter")
	var otter: Dictionary = c.pets.back()
	Game.pets.apply_grant(c.id, "mossback_toad")
	var toad: Dictionary = c.pets.back()
	c.active_pet = str(fox.uid)
	check(str(Game.submit({"type": "set_pet_bag", "pet": otter.uid, "on": true}).get("reason", "")) == "no_bag", "carrying needs a Spirit Beast Bag")
	Game.inventory.apply_add(c.id, "beast_bag_reed", 1, "test")
	Game.inventory.apply_add(c.id, "beast_bag_hide", 1, "test")
	check(Game.pets.bag_capacity(c) == 3, "the best bag counts: a Hide Beast Bag carries 3")
	check(Game.submit({"type": "set_pet_bag", "pet": otter.uid, "on": true}).get("ok", false) and c.pet_bag.has(str(otter.uid)), "pack the otter at the Beast Hall")
	Game.world.load_room(c, "lf_reed_shallows", "")
	check(str(Game.submit({"type": "set_active_pet", "pet": toad.uid}).get("reason", "")) == "cannot_call", "in the field an animal left at home cannot be called")
	check(str(Game.submit({"type": "set_pet_bag", "pet": toad.uid, "on": true}).get("reason", "")) == "not_safe", "nor packed")
	var sw := Game.submit({"type": "swap_pet_from_bag", "pet": otter.uid})
	check(sw.get("ok", false) and c.active_pet == str(otter.uid) and c.pet_bag.has(str(fox.uid)) and not c.pet_bag.has(str(otter.uid)),
		"swap from the bag: the otter comes out, the fox goes in")
	var st: ActorState = Game.actor_state(c.id)
	var rat: EnemyState = Game.enemies.spawn_at("reedtail_rat", st.plane + Vector2(120, 0), 2)
	rat.ai.state = "aggro"
	check(str(Game.submit({"type": "swap_pet_from_bag", "pet": fox.uid}).get("reason", "")) == "in_combat", "never in a fight")
	Game.enemies.release(rat)
	# The Mount slot: a combat animal and a mount together; mount-only species; the Mount button.
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	Game.pets.apply_grant(c.id, "riverstone_ox")
	var ox: Dictionary = c.pets.back()
	check(str(Game.submit({"type": "set_active_pet", "pet": ox.uid}).get("reason", "")) == "cannot_call"
		and str(Game.submit({"type": "set_pet_role", "pet": ox.uid, "role": "combat"}).get("reason", "")) == "mount_only", "a Riverstone Ox only carries you")
	check(Game.submit({"type": "set_mount", "pet": ox.uid}).get("ok", false) and c.mount_pet == str(ox.uid) and c.riding and c.active_pet == str(otter.uid),
		"the ox takes the Mount slot; the otter stays active")
	Game.world.load_room(c, "lf_reed_shallows", "")
	check(near(Game.pets.mount_speed(c), 1.5) and Game.pets.ally_uid != 0, "riding the ox at x1.5 while the otter walks beside you")
	Game.submit({"type": "set_mount", "on": false})
	check(not c.riding and near(Game.pets.mount_speed(c), 1.0), "the Mount button: off and walking")
	Game.pets.apply_grant(c.id, "cloud_stag")
	var stag: Dictionary = c.pets.back()
	Game.submit({"type": "set_mount", "pet": stag.uid})
	check(near(Game.pets.mount_speed(c), 1.6) and int(ContentDB.entry("pets", "cloud_stag").movement.jump) == 600 and str(ox.role) == "mount", "the Cloud Stag: x1.6, jump 600")
	# An older save rode the active animal in the Mount role: it moves to the Mount slot.
	c.mount_pet = ""
	c.riding = false
	var crane_like := stag
	c.active_pet = str(crane_like.uid)
	check(not Game.pets.mount_of(c).is_empty() and c.mount_pet == str(crane_like.uid) and c.active_pet == "", "an old mount moves into the Mount slot")
	c.active_pet = str(otter.uid)
	# Beast Kings: +10% to their zone's beasts while they live; lifted at once when they fall; the nest opens.
	var timers: Dictionary = Game.account.rooms.get("field_boss_timers", {})
	timers["riverbed_serpent"] = Clock.now_utc() + 3600.0
	Game.account.rooms["field_boss_timers"] = timers
	var plain: EnemyState = Game.enemies.spawn_at("tide_crab", st.plane + Vector2(300, 0), 22)
	var base_hp: float = plain.pools.max_hp
	var base_atk: float = float(plain.stats.attack)
	Game.enemies.release(plain)
	timers["riverbed_serpent"] = 0.0
	var buffed: EnemyState = Game.enemies.spawn_at("tide_crab", st.plane + Vector2(300, 0), 22)
	check(near(buffed.pools.max_hp, base_hp * 1.1, 0.5) and near(float(buffed.stats.attack), base_atk * 1.1, 0.05), "while the Riverbed Serpent lives, a valley crab is 10% stronger")
	GameEvents.emit_event("actor_defeated", {"victim_kind": "enemy", "def": "riverbed_serpent", "role": "field_boss", "room": "dw_serpents_shallows",
		"level": 25, "x": 0.0, "y": 0.0})
	GameEvents.flush()
	check(near(buffed.pools.max_hp, base_hp, 0.5) and not buffed.ai.get("king_buff", true), "the King falls: the buff lifts at once")
	Game.enemies.release(buffed)
	check(Game.world.nest_closes("riverbed_serpent") > Clock.now_utc() + 1700.0, "its nest opens for 30 minutes")
	var shore := {"enemy": "reed_otter", "king_alive": "riverbed_serpent"}
	timers["riverbed_serpent"] = Clock.now_utc() + 3600.0
	check(not Game.enemies._spawn_allowed(shore), "with the King dead, no extra paw-marked beasts")
	timers["riverbed_serpent"] = 0.0
	check(Game.enemies._spawn_allowed(shore), "while it lives they gather")
	Game.world.load_room(c, "dw_serpents_shallows", "")
	var nest: Dictionary = Game.room_rt.object_def("serpent_nest")
	check(Game.world.object_visible(c, nest), "the nest shows while it is open")
	Game.actor_state(c.id).plane = Vector2(float(nest.at[0]), float(nest.at[1]))
	Game.actor_state(c.id).altitude = float(nest.get("alt", 0))   # up on the high rock beside it
	var n0: int = c.inventory.count("rare_spirit_egg")
	var ni := Game.world.interact(c, "serpent_nest")
	check(c.inventory.count("rare_spirit_egg") == n0 + 1 and not Game.world.object_available(c, nest).ok, "one Rare Spirit Egg per opening %s" % str(ni.get("reason", "")))
	# The Beast Tide: once a week at Stoneford Gate; three waves whose Level follows yours; cores, an egg, Spirit Soil.
	Game.world.load_room(c, "sf_gate", "")
	c.cooldowns.erase("beast_tide_week")
	check(Game.world.tide_due(c), "the Beast Tide is due this week")
	var tw := Game.world.start_beast_tide(c)
	check(tw.get("ok", false) and Game.room_rt.event.get("active", false) and (Game.room_rt.event.waves as Array).size() == 3, "ring the gong: three waves")
	var w0: Dictionary = Game.room_rt.event.waves[0]
	check(Game.world.event_level(c, w0) == clampi(ProgressionRules.level(c) - 4, 10, 45), "the waves' Level follows yours, between 10 and 45")
	Game.room_rt.event.remaining = float(Game.room_rt.event.duration) - 40.0
	Game.room_rt.event.wave_timers[0] = 0.0
	var crabs := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "tide_crab").size()
	Game.world._tick_event(c, Game.room_rt, 0.01)
	check(Game.room_rt.living_enemies().filter(func(e): return e.def_id == "tide_crab").size() == crabs, "the first wave stops after its 30 seconds")
	var stag_eggs: int = c.inventory.count("cloud_stag_egg")
	c.quests.flags.erase("tide_stag_egg")
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(not Game.world.tide_due(c) and c.inventory.count("cloud_stag_egg") == stag_eggs + 1 and c.inventory.count("spirit_soil") >= 1,
		"held: the week's tide is spent; a Cloud Stag egg (Cloud Stride 1) and Spirit Soil")
	# Pets never die: at 0 HP an animal retreats into its token and comes back.
	Game.world.load_room(c, "lf_reed_shallows", "")
	Game.pets._spawn(c)
	var a: EnemyState = Game.room_rt.enemies.get(Game.pets.ally_uid)
	check(a != null, "the otter is out")
	if a != null:
		a.pools.hp = 0.0
		Game.pets.apply_retreat(a)
		check(str(a.ai.state) == "downed" and a.alive and c.pets.has(otter), "at 0 HP it retreats into its token, alive")
		c.cultivator.meditating = true
		AllyBrain.think(Game, a, 0.1, 1.0, 36.0)
		c.cultivator.meditating = false
		check(str(a.ai.state) == "follow" and near(a.pools.hp, a.pools.max_hp), "meditation calls it back whole")
	Game.account.rooms["field_boss_timers"] = timers_was
	c.pets = pets_was
	c.active_pet = active_was
	c.pet_bag = bag_was
	c.mount_pet = ""
	c.riding = false
	c.inventory.key_items = keys_was
	c.cultivator.realm_key = realm_was
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S46 · the Beast Arena's auto-battle and ladder, the Beast Trial Grove, Beast Taming Dao tiers, the Feeding Trough.
func beast_arena_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var arena_was: Dictionary = c.beast_arena.duplicate(true)
	var daos_was: Dictionary = c.cultivator.daos.duplicate(true)
	var sect_was: Dictionary = Game.account.sect.duplicate(true)
	var storage_was: Array = (Game.account.storage.get("items", []) as Array).duplicate(true)
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	Unlocks.force_unlock(c.id, "spirit_animals")
	c.inventory.bag.fill(null)
	c.pets = []
	c.party_pets = []
	c.pet_bag = []
	c.mount_pet = ""
	var bcfg: Dictionary = Game.pets.arena_cfg().battle
	# The auto-battle: pure and deterministic; the stronger side wins.
	var strong := PetRules.combatant({"species": "mist_wolf", "level": 40, "rarity": "rare", "stage": "adult"}, bcfg)
	var weak := PetRules.combatant({"species": "reed_otter", "level": 12, "rarity": "common", "stage": "hatchling"}, bcfg)
	var r1 := PetRules.battle([strong], [weak], bcfg, _seeded(7))
	var r2 := PetRules.battle([strong], [weak], bcfg, _seeded(7))
	check(str(r1.winner) == "a" and r1.log == r2.log, "the same seed fights the same fight, and the stronger animal wins")
	var sk := PetRules.combatant({"species": "ember_fox", "level": 20, "skill_mult": 2.5, "free_cast": true}, bcfg)
	var r3 := PetRules.battle([sk], [PetRules.combatant({"species": "ember_fox", "level": 20}, bcfg)], bcfg, _seeded(3))
	check(not (r3.log as Array).is_empty() and bool(r3.log[0].skill) and str(r3.log[0].side) == "a", "an Equal Contract's free cast opens the fight")
	# The ladder: challenge the tamer above you; a win takes their rank; five fights a day; 3v3 needs three.
	Game.pets.apply_grant(c.id, "mist_wolf")
	var wolf: Dictionary = c.pets.back()
	wolf.level = 60
	wolf.rarity = "epic"
	wolf.stage = "awakened"
	c.active_pet = str(wolf.uid)
	c.beast_arena = {}
	var st0: Dictionary = Game.pets.arena_state(c)
	check(int(st0.rank) == 11 and str(Game.pets.arena_opponent(c).id) == "farmhand_qiao", "unranked, the first opponent is Farmhand Qiao (rank 10)")
	check(str(Game.submit({"type": "arena_challenge", "mode": "trio"}).get("reason", "")) == "team", "a 3v3 needs three animals")
	var f1 := Game.submit({"type": "arena_challenge", "mode": "solo"})
	check(f1.get("won", false) and int(c.beast_arena.rank) == 10 and not (c.beast_arena.last.log as Array).is_empty(), "a Level 60 wolf beats him and takes rank 10")
	for i in 4: Game.submit({"type": "arena_challenge", "mode": "solo"})
	check(str(Game.submit({"type": "arena_challenge", "mode": "solo"}).get("reason", "")) == "no_fights", "five fights a day")
	# The week turns: rank 3 pays 15 Spirit Stones and a Beast Marrow Washing Pill; the ladder starts again.
	c.beast_arena.rank = 3
	c.beast_arena.week = Clock.reset_week(Clock.now_utc()) - 1
	var pills0: int = c.inventory.count("beast_marrow_washing_pill")
	Game.pets.arena_state(c)
	check(int(Game.account.currencies.get("spirit_stone", 0)) == stones0 + 15 and c.inventory.count("beast_marrow_washing_pill") == pills0 + 1
		and int(c.beast_arena.rank) == 11, "the week turns: rank 3 pays out, the ladder starts again")
	# The Trial Grove: once a day; the keeper's blows rally instead of striking; ten kills; the Guardian Spirit first.
	Game.world.load_room(c, "sf_beast_grove", "")
	Game.pets._spawn(c)
	c.cooldowns.erase("grove_day")
	check(Game.world.start_beast_trial(c).get("ok", false) and Game.room_rt.event.get("pet_trial", false), "the Grove's trial begins")
	check(str(Game.world.start_beast_trial(c).get("reason", "")) == "done", "once a day")
	var st: ActorState = Game.actor_state(c.id)
	var boar: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), 20)
	var hp0: float = boar.pools.hp
	Game.pets.rally_ready.erase(c.id)
	Game.combat._damage_enemy(boar, 50.0, c.id, "physical", "none", false, {})
	check(near(boar.pools.hp, hp0) and float(Game.pets.rally_until.get(c.id, 0.0)) > Game.sim_time, "your blow rallies the animals instead of striking")
	var pw := Game.pets.pet_power(c, wolf)
	Game.pets.rally_until.erase(c.id)
	check(near(pw, Game.pets.pet_power(c, wolf) * 1.25, 0.01), "rallied: +25%")
	Game.combat._damage_enemy(boar, 1e9, c.id, "physical", "none", false, {"source": "ally:1"})
	GameEvents.flush()
	check(int(Game.room_rt.event.get("kills", 0)) == 1, "the animals' kills count toward the ten")
	c.quests.flags.erase("grove_first_clear")
	var books0: int = c.inventory.count("pet_book_guardian_spirit")
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(c.inventory.count("pet_book_guardian_spirit") == books0 + 1, "the first clear gives the Guardian Spirit book")
	# Beast Taming Dao: elites from tier 3; eggs 10% sooner from tier 2; teachable from tier 4.
	Unlocks.force_unlock(c.id, "taming")
	Game.world.load_room(c, "lf_reed_shallows", "")
	st = Game.actor_state(c.id)
	var eo: EnemyState = Game.enemies.spawn_at("reed_otter", st.plane + Vector2(60, 0), 20, {"elite": true})
	eo.pools.hp = eo.pools.max_hp * 0.1
	Game.inventory.apply_add(c.id, "bonding_offering_common", 2, "test")
	c.cultivator.daos["beast_taming"] = {"tier": 2, "insight": 0.0}
	check(str(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("reason", "")) == "elite_tier", "an elite needs the Dao at tier 3")
	c.cultivator.daos["beast_taming"] = {"tier": 3, "insight": 0.0}
	check(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("ok", false), "at tier 3 the elite can be tried")
	check(not Game.workshop.teachable_daos(c).has("beast_taming"), "not yet teachable at tier 3")
	c.cultivator.daos["beast_taming"] = {"tier": 4, "insight": 0.0}
	check(Game.workshop.teachable_daos(c).has("beast_taming"), "teachable at tier 4")
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	# The Feeding Trough: with a Beast Pavilion, hungry animals eat from storage once a day.
	Game.account.sect = {"name": "Test", "level": 1, "buildings": {"beast_pavilion": 1}}
	Game.account.storage["items"] = [{"id": "roast_fish", "count": 2}]
	wolf.hunger_day = Clock.reset_day(Clock.now_utc()) - 2
	c.cooldowns.erase("trough_day")
	Game.pets._trough(c)
	check(int(wolf.hunger_day) == Clock.reset_day(Clock.now_utc()) and int(Game.account.storage.items[0].count) == 1, "the trough feeds the hungry wolf from storage")
	wolf.hunger_day = 0
	Game.pets._trough(c)
	check(int(wolf.hunger_day) == 0, "once a day")
	Game.account.sect = sect_was
	Game.account.storage["items"] = storage_was
	Game.account.currencies["spirit_stone"] = stones0
	c.cultivator.daos = daos_was
	c.beast_arena = arena_was
	c.pets = pets_was
	c.active_pet = active_was
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49: the Relations authority owns the karma ledger, alignment and Fame; deeds come from karma.json.
func relations_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var rel_was: Dictionary = c.relations.snapshot()
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var rel: RelationsState = c.relations
	rel.restore({})
	# A save from before S49 carries its ledger on the cultivator; it moves across.
	var old_save: Dictionary = c.snapshot()
	old_save.erase("relations")
	old_save.cultivator["merit"] = 77
	old_save.cultivator["sin"] = 5
	old_save.cultivator["debts"] = {"gu_repays": {"due_utc": 1.0, "mail": "gu_repays", "attachments": [], "paid": true}}
	old_save.cultivator["merit_used"] = {"cloud_stride": true}
	var moved := GameCharacter.new()
	moved.restore(old_save)
	check(moved.relations.merit == 77 and moved.relations.sin == 5 and moved.relations.debts.has("gu_repays") and moved.relations.merit_used.has("cloud_stride"),
		"an old save's merit, sin, debts and eased realms move to Relations")
	check(not moved.cultivator.snapshot().has("merit") and moved.snapshot().relations.merit == 77, "and are saved there from now on")
	# A named deed from an effect: merit, alignment and Fame together, once.
	Game.apply_effects(c.id, [{"kind": "deed", "deed": "cleansing_the_well"}], "test")
	GameEvents.flush()
	check(rel.merit == 30 and rel.alignment == 5 and rel.fame == 15, "cleansing the well: +30 merit, +5 alignment, +15 Fame (Part 8)")
	Game.apply_effects(c.id, [{"kind": "deed", "deed": "cleansing_the_well"}], "test")
	check(rel.merit == 30, "a once-only deed counts once")
	check(str(rel.ledger[0].reason) == "cleansing_the_well", "the ledger remembers the deed")
	Game.relations.apply_deed(c.id, "heal_patient")
	Game.relations.apply_deed(c.id, "heal_patient")
	check(rel.merit == 34, "each patient healed is +2 merit, again and again")
	# Event deeds: a spar won in a town square is public; the same spar in the wilds is not.
	Game.world.load_room(c, "sf_market", "")
	var f0 := rel.fame
	Game.relations._on_deed_event({"actor": c.id, "opponent": "sparring_disciple", "winner": "player", "room": "sf_market"}, "spar_ended")
	check(rel.fame == f0 + 3, "a public win: +3 Fame")
	Game.relations._on_deed_event({"actor": c.id, "opponent": "sparring_disciple", "winner": "opponent", "room": "sf_market"}, "spar_ended")
	check(rel.fame == f0 - 2, "a public defeat costs 5")
	Game.world.load_room(c, "lf_reed_shallows", "")
	Game.relations._on_deed_event({"actor": c.id, "opponent": "sparring_disciple", "winner": "opponent", "room": "lf_reed_shallows"}, "spar_ended")
	check(rel.fame == f0 - 2, "no one sees a spar in the reeds")
	var f1 := rel.fame
	var boss := {"victim": "9", "victim_kind": "enemy", "def": "riverbed_serpent", "role": "field_boss", "killer": c.id}
	Game.relations._on_deed_event(boss, "actor_defeated")
	Game.relations._on_deed_event(boss, "actor_defeated")
	boss.def = "thousand_eye_toad"
	Game.relations._on_deed_event(boss, "actor_defeated")
	check(rel.fame == f1 + 20, "each field lord felled is +10 Fame, the first time")
	# Fame tiers and the tier-up.
	rel.fame = 140
	var ups: Array = []
	var on_fame := func(p: Dictionary): if p.get("tier_up", false): ups.append(str(p.tier))
	GameEvents.subscribe("fame_changed", on_fame, 200)
	Game.relations.apply_fame(c.id, 20, "test")
	GameEvents.flush()
	check(str(Game.relations.fame_tier(c).id) == "rising" and ups == ["rising"], "150 Fame is Rising, and the step up is announced")
	Game.relations.apply_fame(c.id, -1000, "test")
	check(rel.fame == 0, "Fame never goes below 0")
	# Alignment: clamped, named, and a gate on optional things only.
	rel.alignment = 0
	var upright := {"all": [{"kind": "alignment_at_least", "value": 20}]}
	var shadowed := {"all": [{"kind": "alignment_at_most", "value": -20}]}
	check(not RequirementRules.passes(upright, {"char": c}) and not RequirementRules.passes(shadowed, {"char": c}), "a balanced cultivator is neither upright nor shadowed")
	Game.relations.apply_alignment(c.id, 500, "test")
	check(rel.alignment == 100 and Game.relations.alignment_word(c) == "righteous" and RequirementRules.passes(upright, {"char": c}), "alignment stops at +100 (Righteous)")
	Game.relations.apply_alignment(c.id, -130, "test")
	check(rel.alignment == -30 and Game.relations.alignment_word(c) == "shadowed" and RequirementRules.passes(shadowed, {"char": c}), "and leans the other way")
	var cloud := ContentDB.entry("shops", "cloud_sect")
	var incense := {}
	for row in cloud.get("stock", []):
		if str(row.item) == "calm_heart_incense": incense = row
	check(not RequirementRules.passes(incense.get("requires", {}), {"char": c}), "the Cloud Sect's incense is for the upright")
	check(RequirementRules.passes({"all": [{"kind": "realm_at_least", "realm": c.cultivator.realm_key}]}, {"char": c}), "alignment never touches a realm requirement")
	# A black-market purchase is a deed from the event, per item.
	rel.alignment = 0
	var sin0 := rel.sin
	Game.relations._on_deed_event({"actor": c.id, "shop": "free_market", "item": "manual_page", "count": 3}, "item_bought")
	check(rel.sin == sin0 + 6 and rel.alignment == -3, "three items from the back room: +6 sin, -3 alignment")
	# Young masters: from Rising Fame, a town may bring one out; answer him or lose face.
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	rel.fame = 100
	c.cooldowns.erase("young_master_day")
	for i in 40: Game.relations._on_room_entered({})
	check(Game.relations.challenge_of(c).is_empty(), "below Rising no one comes")
	rel.fame = 200
	var came := false
	for i in 60:
		c.cooldowns.erase("young_master_day")
		Game.relations._on_room_entered({})
		if not Game.relations.challenge_of(c).is_empty():
			came = true
			break
	check(came, "a Rising name draws a young master in town")
	Game.relations._on_room_entered({})
	check(Game.relations.challenge_of(c).is_empty(), "once a day at most")
	Game.relations.offer_challenge(c, "young_master")
	check(Game.submit({"type": "answer_challenge", "accept": false}).get("ok", false) and rel.fame == 195, "declining costs 5 Fame")
	check(not Game.submit({"type": "answer_challenge", "accept": true}).get("ok", false), "and the challenge is gone")
	Game.relations.offer_challenge(c, "young_master")
	check(Game.submit({"type": "answer_challenge", "accept": true}).get("ok", false), "accepting starts the spar")
	var ym: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "young_master": ym = e
	check(ym != null and ym.level == ProgressionRules.level(c), "he fights at your own level")
	if ym != null:
		Game.enemies.end_spar(ym, c.id)
		GameEvents.flush()
		check(rel.fame == 195 + 15 + 3, "humbling him in the square: +18 Fame")
	Game.relations.offer_challenge(c, "young_master")
	Game.world.load_room(c, "lf_reed_shallows", "")
	GameEvents.flush()
	check(Game.relations.challenge_of(c).is_empty(), "walking away lets the challenge lapse")
	GameEvents.unsubscribe_object(self)
	c.relations.restore(rel_was)
	c.cooldowns = cd_was
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0: NPC affinity (hearts, gifts once a day, heart rewards, discounts), companion duels, sworn siblings, the
## Dao Companion and the master's legacy.
func bonds_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var rel_was: Dictionary = c.relations.snapshot()
	var comp_was: Dictionary = c.companions.duplicate(true)
	var recipes_was: Array = c.crafting.recipes.duplicate()
	var arts_was: Array = c.cultivator.inner_arts_known.duplicate()
	var title_was: String = c.cultivator.active_title
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var rel: RelationsState = c.relations
	rel.restore({})
	c.inventory.bag.fill(null)
	Game.world.load_room(c, "lf_reed_shallows", "")
	# A gift a day: loved is a heart; the second gift that day is refused.
	Game.inventory.apply_add(c.id, "riverfish_soup", 2, "test")
	var r1: Dictionary = Game.submit({"type": "give_gift", "npc": "aunt_ping", "index": _bag_index(c, "riverfish_soup")})
	check(r1.get("ok", false) and str(r1.reaction) == "loved" and rel.hearts_of("aunt_ping") == 1, "Riverfish Soup is Aunt Ping's favourite: a whole heart")
	check(str(Game.submit({"type": "give_gift", "npc": "aunt_ping", "index": _bag_index(c, "riverfish_soup")}).get("reason", "")) == "gifted_today", "one gift a day")
	check(str(rel.affinity.aunt_ping.known.get("riverfish_soup", "")) == "loved", "and you remember what she loves")
	Game.inventory.apply_add(c.id, "rice_ball", 1, "test")
	Game.submit({"type": "give_gift", "npc": "granny_liu", "index": _bag_index(c, "rice_ball")})
	check(int(rel.affinity.granny_liu.points) == 15, "anything else is a courtesy (+15)")
	Game.inventory.apply_add(c.id, "training_jian", 1, "test")
	check(str(Game.submit({"type": "give_gift", "npc": "old_ma", "index": _bag_index(c, "training_jian")}).get("reason", "")) == "not_giftable"
		and not RelationsAuthority.giftable({"id": "kite", "count": 1}), "gear and key items stay with you")
	# One person, two rows: Mei Qing at her stall and in the sect keep one heart count.
	Game.inventory.apply_add(c.id, "cloudtop_orchid", 1, "test")
	Game.submit({"type": "give_gift", "npc": "mei_qing_sect", "index": _bag_index(c, "cloudtop_orchid")})
	check(rel.hearts_of("mei_qing") == 1 and rel.hearts_of("mei_qing_sect") == 1, "Mei Qing is one person wherever you meet her")
	# Hearts pay once: Aunt Ping teaches Riverfish Soup at three.
	c.crafting.recipes.erase("riverfish_soup")
	Game.relations.apply_affinity(c.id, "aunt_ping", 200, "test")
	check(rel.hearts_of("aunt_ping") == 3 and c.crafting.recipes.has("riverfish_soup"), "three hearts: Aunt Ping teaches her soup")
	c.crafting.recipes.erase("riverfish_soup")
	Game.relations.apply_affinity(c.id, "aunt_ping", -100, "test")
	Game.relations.apply_affinity(c.id, "aunt_ping", 100, "test")
	check(not c.crafting.recipes.has("riverfish_soup"), "and only once")
	check(RequirementRules.passes({"all": [{"kind": "hearts_at_least", "npc": "aunt_ping", "value": 3}]}, {"char": c}), "hearts_at_least reads the hearts")
	# Quests make friends.
	var gp: int = int(rel.affinity.get("granny_liu", {}).get("points", 0))
	Game.relations._on_quest_completed({"actor": c.id, "quest": "grannys_remedy"})
	check(int(rel.affinity.granny_liu.points) == gp + 30, "a quest done for Granny Liu: +30")
	# A keeper who likes you gives a little off.
	var dear := ""
	var price0 := 0
	for row in Game.economy.stock(c, "old_ma"):
		if int(row.price) > price0:
			price0 = int(row.price)
			dear = str(row.item)
	Game.relations.apply_affinity(c.id, "old_ma", 300, "test")
	var price1 := 0
	for row in Game.economy.stock(c, "old_ma"):
		if str(row.item) == dear: price1 = int(row.price)
	check(Game.relations.shop_discount(c, "old_ma") == 0.05 and price1 < price0, "three hearts with Old Ma: 5%% off (%d -> %d)" % [price0, price1])
	# Companions: a duel at three hearts, sworn at four, a Dao Companion at five.
	c.companions = {"roster": ["lan_yue", "tie_niu"], "active": ["lan_yue", "tie_niu"], "bond": {}, "downed": {}}
	Game.submit({"type": "set_active_companions", "ids": ["lan_yue", "tie_niu"]})
	check(str(Game.submit({"type": "companion_duel", "companion": "lan_yue"}).get("reason", "")) == "hearts", "no duel before three hearts")
	Game.relations.apply_affinity(c.id, "lan_yue", 300, "test")
	check(c.crafting.recipes.has("lotus_root_tea"), "three hearts with Lan Yue: her tea")
	check(Game.submit({"type": "companion_duel", "companion": "lan_yue"}).get("ok", false), "a friendly duel at three")
	var dz: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "duel_lan_yue": dz = e
	check(dz != null and dz.level == ProgressionRules.level(c), "Lan Yue duels at your level")
	var lp: int = int(rel.affinity.lan_yue.points)
	if dz != null:
		Game.enemies.end_spar(dz, c.id)
		GameEvents.flush()
	check(int(rel.affinity.lan_yue.points) == lp + 20, "winning the duel: +20")
	Game.relations._on_spar_ended({"actor": c.id, "opponent": "duel_lan_yue", "winner": "player"})
	check(int(rel.affinity.lan_yue.points) == lp + 20, "once a day")
	check(str(Game.submit({"type": "offer_bond", "kind": "sworn", "npc": "lan_yue"}).get("reason", "")) == "hearts", "sworn siblings need four hearts")
	Game.relations.apply_affinity(c.id, "lan_yue", 100, "test")
	var atk0: float = c.stats.value("physical_attack")
	check(Game.submit({"type": "offer_bond", "kind": "sworn", "npc": "lan_yue"}).get("ok", false) and (rel.bonds.sworn as Array).has("lan_yue"), "four hearts: sworn")
	check(c.stats.value("physical_attack") > atk0 and c.cultivator.titles.has("sworn_sibling"), "a sworn sibling in the party lifts your attack, and you share a title")
	check(str(Game.submit({"type": "offer_bond", "kind": "sworn", "npc": "lan_yue"}).get("reason", "")) == "already", "once")
	Game.relations.apply_affinity(c.id, "tie_niu", 500, "test")
	check(str(Game.submit({"type": "offer_bond", "kind": "dao_companion", "npc": "lan_yue"}).get("reason", "")) in ["hearts", "sworn"], "a sworn sibling is not a Dao Companion")
	check(Game.submit({"type": "offer_bond", "kind": "dao_companion", "npc": "tie_niu"}).get("ok", false), "five hearts: Tie Niu is your Dao Companion")
	Game.relations.apply_affinity(c.id, "lan_yue", 100, "test")
	check(str(Game.submit({"type": "offer_bond", "kind": "dao_companion", "npc": "lan_yue"}).get("reason", "")) in ["taken", "sworn"], "one Dao Companion only")
	check(Game.relations.bond_support(c) == 1 and near(Game.relations.insight_share(c), 0.1), "beside you: the support slot and +10% insight")
	c.cultivator.meditating = true
	check(near(Game.companions.paired_bonus(c), 0.25), "resonance meditation with the Dao Companion: +25%")
	c.cultivator.meditating = false
	Game.submit({"type": "set_active_companions", "ids": ["lan_yue"]})
	check(Game.relations.bond_support(c) == 0, "not when they stay behind")
	# The master: the personal-disciple trial binds you; the last lesson passes the legacy art.
	Game.relations._on_quest_completed({"actor": c.id, "quest": "the_mentors_gift"})
	var mentor := "elder_sung" if str(c.training_sect.get("id", "")) == "cloud_sect" else "elder_hu"
	check(str(rel.bonds.master) == mentor, "the mentor's trial makes %s your master" % mentor)
	c.cultivator.inner_arts_known.erase("lotus_mind_legacy")
	c.cultivator.inner_arts_known.erase("drifting_cloud_legacy")
	Game.apply_effects(c.id, [{"kind": "master_legacy"}], "test")
	check(c.cultivator.inner_arts_known.has("lotus_mind_legacy" if mentor == "elder_hu" else "drifting_cloud_legacy"), "the last lesson passes the master's legacy art")
	var sold := false
	for row in ContentDB.entry("shops", "jade_sect").get("stock", []):
		if str(row.get("learn", "")) in ["lotus_mind_legacy", "drifting_cloud_legacy"]: sold = true
	check(not sold, "legacy arts are never sold")
	c.relations.restore(rel_was)
	c.companions = comp_was
	c.crafting.recipes = recipes_was
	c.cultivator.inner_arts_known = arts_was
	c.cultivator.titles.erase("sworn_sibling")
	c.cultivator.active_title = title_was
	c.inventory.bag.fill(null)
	Game.combat.refresh_stats(c.id)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0: grudges and hunters, settling them, bounties, a named foe's surrender and Part 8's named debts.
func grudges_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var rel_was: Dictionary = c.relations.snapshot()
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var done_was: Dictionary = c.quests.done.duplicate()
	var flags_was: Dictionary = c.quests.flags.duplicate()
	var taels0 := int(Game.account.currencies.get("silver_tael", 0))
	var mail0: int = Game.account.mail.size()
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var rel: RelationsState = c.relations
	rel.restore({})
	# Named kills raise a faction's grudge; the rank and file do not.
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "mudwater_bandit", "killer": c.id})
	check(Game.relations.grudge(c, "mudwater") == 0, "an ordinary bandit is no one's name")
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "big_toad_tan", "killer": c.id})
	check(Game.relations.grudge(c, "mudwater") == 15, "killing Big Toad Tan: the Mudwater grudge +15")
	# Past the threshold, hunters wait on the roads they know, at your level; not every time, not too often.
	Game.relations.apply_grudge(c.id, "mudwater", 15, "test")
	Game.world.load_room(c, "cr_caravan_road", "")
	GameEvents.flush()
	var found := false
	for i in 40:
		c.cooldowns.erase("hunt_mudwater")
		for e in Game.room_rt.living_enemies():
			if e.def_id == "mudwater_cutthroat": Game.enemies.release(e)
		Game.relations._spawn_hunters(c)
		for e in Game.room_rt.living_enemies():
			if e.def_id == "mudwater_cutthroat" and e.level == ProgressionRules.level(c): found = true
		if found: break
	check(found, "at 30 the Mudwater send a cutthroat onto the Caravan Road, at your level")
	var n0 := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "mudwater_cutthroat").size()
	for i in 20: Game.relations._spawn_hunters(c)
	check(Game.room_rt.living_enemies().filter(func(e): return e.def_id == "mudwater_cutthroat").size() == n0, "then not again for a while")
	for e in Game.room_rt.living_enemies():
		if e.def_id == "mudwater_cutthroat": Game.enemies.release(e)
	# Settling: blood money, a duel with Tan's brother, a quest, or the story.
	Game.account.currencies["silver_tael"] = 500
	check(Game.submit({"type": "pay_grudge", "faction": "mudwater", "method": "blood_money"}).get("ok", false)
		and Game.relations.grudge(c, "mudwater") == 0 and int(Game.account.currencies.silver_tael) == 300, "200 taels of blood money settles the Mudwater")
	Game.relations.apply_grudge(c.id, "mudwater", 20, "test")
	check(Game.submit({"type": "pay_grudge", "faction": "mudwater", "method": "duel"}).get("ok", false), "or a duel with Tan the Younger")
	var tan: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "tan_the_younger": tan = e
	if tan != null:
		Game.enemies.end_spar(tan, c.id)
		GameEvents.flush()
	check(tan != null and Game.relations.grudge(c, "mudwater") == 0, "winning it settles the grudge")
	Game.relations.apply_grudge(c.id, "gorge", 25, "test")
	Game.relations._on_quest_completed({"actor": c.id, "quest": "old_scores"})
	check(Game.relations.grudge(c, "gorge") == 0, "Old Scores settles the Gorge Bandits")
	Game.relations._on_quest_completed({"actor": c.id, "quest": "gus_cargo"})
	Game.relations._on_quest_completed({"actor": c.id, "quest": "hidden_cargo"})
	check(Game.relations.grudge(c, "smugglers") == 40, "Gu's ring: +20 for the cargo, +20 for the hidden cargo")
	Game.relations._on_quest_completed({"actor": c.id, "quest": "gus_warehouse"})
	Game.relations.apply_grudge(c.id, "smugglers", 30, "test")
	check(Game.relations.grudge(c, "smugglers") == 0, "the warehouse ends it for good")
	# Bounties: the board's named targets wait in their rooms while the bounty is yours.
	c.cooldowns.erase("bounty_one_eye_pang")
	var bt: Dictionary = Game.submit({"type": "take_bounty", "id": "one_eye_pang"})
	check(bt.get("ok", false), "take the bounty on One-Eye Pang %s" % str(bt.get("reason", "")))
	Game.world.load_room(c, "cr_caravan_road", "")
	GameEvents.flush()
	var pang: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "one_eye_pang": pang = e
	check(pang != null and pang.elite, "One-Eye Pang is on the Caravan Road")
	var t1 := int(Game.account.currencies.get("silver_tael", 0))
	var f1 := rel.fame
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "one_eye_pang", "killer": c.id})
	check(int(Game.account.currencies.silver_tael) == t1 + 150 and rel.fame == f1 + 10 and rel.bounties.is_empty(), "the bounty pays 150 taels and +10 Fame")
	check(Game.relations.grudge(c, "mudwater") == 15, "and Pang was a name the Mudwater remember")
	check(str(Game.submit({"type": "take_bounty", "id": "one_eye_pang"}).get("reason", "")) == "today", "each bounty once a day")
	# A named foe yields: spare him (merit; he remembers) or finish him (sin; his brother hunts you).
	var st: ActorState = Game.actor_state(c.id)
	var lt: EnemyState = Game.enemies.spawn_at("mudwater_lieutenant", st.plane + Vector2(80, 0), 19)
	Game.combat._damage_enemy(lt, lt.pools.max_hp * 5.0, c.id, "physical", "none", false, {})
	GameEvents.flush()
	check(lt.alive and lt.ai.get("surrendered", false), "Lieutenant Kuai yields instead of dying")
	var hp_y := lt.pools.hp
	Game.combat._damage_enemy(lt, 500.0, c.id, "physical", "none", false, {})
	check(near(lt.pools.hp, hp_y), "a foe who has yielded is not struck")
	var m0 := rel.merit
	check(Game.submit({"type": "judge_foe", "enemy": lt.uid, "spare": true}).get("ok", false) and not lt.alive and rel.merit == m0 + 10, "sparing him: +10 merit")
	check(rel.debts.has("lieutenant_spared"), "and he remembers")
	c.quests.done["hidden_cargo"] = 1
	Game.relations.settle_debts(c)
	GameEvents.flush()
	check(bool(rel.debts.lieutenant_spared.paid) and c.quests.has_flag("warned_of_ambush") and Game.account.mail.size() > mail0, "before Gu's warehouse, his warning arrives")
	var lt2: EnemyState = Game.enemies.spawn_at("mudwater_lieutenant", st.plane + Vector2(80, 0), 19)
	Game.combat._damage_enemy(lt2, lt2.pools.max_hp * 5.0, c.id, "physical", "none", false, {})
	var s0 := rel.sin
	check(Game.submit({"type": "judge_foe", "enemy": lt2.uid, "spare": false}).get("ok", false) and not lt2.alive and rel.sin == s0 + 15, "killing a foe who yielded: +15 sin")
	rel.debts.lieutenant_killed.due_utc = 0.0
	Game.relations.settle_debts(c)
	GameEvents.flush()
	check(rel.hunters.size() == 1 and str(rel.hunters[0].enemy) == "kuai_shan", "his brother Kuai Shan comes hunting")
	Game.world.load_room(c, "cr_caravan_road", "")
	GameEvents.flush()
	var ks := false
	for e in Game.room_rt.living_enemies():
		if e.def_id == "kuai_shan": ks = true
	check(ks, "Kuai Shan waits on the Caravan Road")
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "kuai_shan", "killer": c.id})
	check(rel.hunters.is_empty(), "until he falls")
	# Little Dou's rescue is repaid in chapter 6 with a heaven herb.
	Game.apply_effects(c.id, [{"kind": "record_debt", "id": "dou_rescue"}], "test")
	check(str(rel.debts.dou_rescue.get("due_quest", "")) == "the_heart_trial", "Little Dou's debt falls due with the Heart Trial")
	c.quests.done["the_heart_trial"] = 1
	var mails: int = Game.account.mail.size()
	Game.relations.settle_debts(c)
	check(Game.account.mail.size() == mails + 1 and str(Game.account.mail[0].attachments[0].item) == "cloudtop_orchid", "Dou's letter brings a Cloudtop Orchid")
	# The night peddler: +5 sin a purchase.
	var s1 := rel.sin
	Game.relations._on_deed_event({"actor": c.id, "shop": "night_peddler", "item": "manual_page", "count": 2}, "item_bought")
	check(rel.sin == s1 + 10, "two things from the night peddler: +10 sin")
	check(not RequirementRules.passes(ContentDB.entry("shops", "night_peddler").requires, {"char": c}) or Clock.time_of_day() == "night", "his mat is out only at night")
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	c.relations.restore(rel_was)
	c.cooldowns = cd_was
	c.quests.done = done_was
	c.quests.flags = flags_was
	Game.account.currencies["silver_tael"] = taels0
	while Game.account.mail.size() > mail0: Game.account.mail.pop_front()
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0 world calendar: seeded and identical for the same save, events on their rhythm, repeat runs behind the
## cycle and a realm cap (first visits never), the spatial rift, seasons from the account's first week.
func calendar_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var realm_was: String = c.cultivator.realm_key
	var kills_was: Dictionary = c.collection_first_kills.duplicate()
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var created_was: float = Game.account.created_utc
	var seed_was: int = Game.account.rng_seed
	var over_was: float = Clock.override_utc
	var origin := 1_700_000_000.0
	Game.account.created_utc = origin
	Game.account.rng_seed = 424242
	var rift := CalendarRules.event("spatial_rift")
	var shrine := CalendarRules.event("shrine_reopening")
	var fall := CalendarRules.event("waterfall_reopening")
	# The same seed and first day give the same calendar on any device; another seed moves the rifts.
	var a := CalendarRules.schedule(origin + 40 * 86400.0, 424242, origin)
	var b := CalendarRules.schedule(origin + 40 * 86400.0, 424242, origin)
	check(a == b and not a.is_empty(), "the same save sees the same calendar")
	var differ := false
	for k in 12:
		if str(CalendarRules.occurrence(rift, k, 424242, origin).room) != str(CalendarRules.occurrence(rift, k, 7, origin).room): differ = true
	check(differ, "another seed opens the rifts elsewhere")
	# Rhythms: a rift every three days for an hour in a valley field room; the shrine every five days for a day;
	# the Waterfall Cave on the same rhythm, two days later.
	var r0 := CalendarRules.occurrence(rift, 0, 424242, origin)
	var r1 := CalendarRules.occurrence(rift, 1, 424242, origin)
	check(absf(float(r1.start) - float(r0.start) - 3 * 86400.0) <= 12 * 3600.0 and near(float(r0.end) - float(r0.start), 3600.0)
		and (rift.rooms as Array).has(str(r0.room)), "a rift every three days, for an hour, in a field room")
	var s0 := CalendarRules.occurrence(shrine, 0, 424242, origin)
	var f0 := CalendarRules.occurrence(fall, 0, 424242, origin)
	check(near(float(CalendarRules.occurrence(shrine, 1, 424242, origin).start) - float(s0.start), 5 * 86400.0)
		and near(float(f0.start) - float(s0.start), 2 * 86400.0) and near(float(s0.end) - float(s0.start), 86400.0), "reopenings every five days for a day, the cave two days after the shrine")
	check(CalendarRules.active(shrine, float(s0.start) + 3600.0, 424242, origin).get("k", -1) == 0
		and CalendarRules.active(shrine, float(s0.end) + 3600.0, 424242, origin).is_empty(), "open for its day, closed after")
	# Repeat runs only while open and at or below the cap; the first defeat never waits.
	c.cultivator.realm_key = "qi_unfurling_5"
	check(CalendarRules.repeat_open(shrine, float(s0.start) + 60.0, 424242, origin, c.cultivator.realm_key), "the Abbot again: open at Qi Unfurling 5")
	check(not CalendarRules.repeat_open(shrine, float(s0.start) + 60.0, 424242, origin, "heart_tempering_2"), "not at Heart Tempering (past the cap)")
	Clock.override_utc = float(s0.end) + 3600.0
	var spec := {"enemy": "drowned_abbot", "calendar": "shrine_reopening"}
	c.collection_first_kills.erase("drowned_abbot")
	check(Game.enemies._spawn_allowed(spec), "the first defeat is never behind the cycle")
	c.collection_first_kills["drowned_abbot"] = true
	check(not Game.enemies._spawn_allowed(spec), "a repeat waits for the shrine to surface")
	Clock.override_utc = float(s0.start) + 3600.0
	check(Game.enemies._spawn_allowed(spec), "and wakes while it has")
	# The Waterfall Cave's inner cache: once per opening.
	Clock.override_utc = float(f0.start) + 3600.0
	var cache := {}
	for o in ContentDB.room("wg_waterfall_cave").get("objects", []):
		if str(o.id) == "cave_inner_cache": cache = o
	check(not cache.is_empty() and Game.world.open_key(cache) == "cave_inner_cache@0", "the cache is keyed to this opening")
	# The spatial rift: its tear shows in its room while open; touching it pours out that room's beasts, stronger.
	Clock.override_utc = float(r0.start) + 600.0
	Game.world.load_room(c, str(r0.room), "")
	GameEvents.flush()
	var tear := {}
	for o in Game.room_rt.def.get("objects", []):
		if str(o.type) == "rift_tear": tear = o
	check(not tear.is_empty() and Game.world.object_visible(c, tear), "the tear shows in %s while the rift is open" % r0.room)
	c.cooldowns.erase("rift_k")
	var opened: Dictionary = Game.calendar.open_rift(c)
	check(opened.get("ok", false) and str(Game.room_rt.event.get("id", "")) == "spatial_rift", "touching it starts the rift")
	check(str(Game.calendar.open_rift(c).get("reason", "")) in ["done", "busy"], "once per rift")
	var top := 0
	for w in Game.room_rt.event.get("waves", []): top = maxi(top, int(w.level))
	var room_top := 0
	for sp in Game.room_rt.def.get("spawns", []):
		if not sp.get("boss", false) and not sp.has("requires"): room_top = maxi(room_top, int((sp.get("level", [0]) as Array).back()))
	check(top == room_top + 3, "its beasts come three levels stronger (%d over %d)" % [top, room_top])
	Game.world._end_event(c, Game.room_rt, false)
	Clock.override_utc = float(r0.end) + 600.0
	check(not Game.world.object_visible(c, tear), "the tear closes with the hour")
	# Seasons from the account's first week: spring first.
	HerbRules.origin_week = Clock.reset_week(origin)
	check(HerbRules.season(origin + 3600.0) == "spring" and HerbRules.season(origin + 7 * 86400.0 + 3600.0) != "spring", "spring comes first, from the account's first week")
	HerbRules.origin_week = 0
	if Game.room_rt.event.get("active", false): Game.world._end_event(c, Game.room_rt, false)
	Clock.override_utc = over_was
	Game.account.created_utc = created_was
	Game.account.rng_seed = seed_was
	c.cultivator.realm_key = realm_was
	c.collection_first_kills = kills_was
	c.cooldowns = cd_was
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0/v1.1: Auction Day on Market Street, a Spirit Fruit birth, the Herb Terraces trial, the weather.
func world_events_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var recipes_was: Array = c.crafting.recipes.duplicate()
	var created_was: float = Game.account.created_utc
	var seed_was: int = Game.account.rng_seed
	var over_was: float = Clock.override_utc
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	var econ_was: Dictionary = Game.account.economy.duplicate(true)
	var mail0: int = Game.account.mail.size()
	var origin := 1_700_000_000.0
	Game.account.created_utc = origin
	Game.account.rng_seed = 777
	c.inventory.bag.fill(null)
	# Auction Day: the valley's house opens only on Saturdays, its lots close with the day, a recipe is taught.
	var ad := CalendarRules.occurrence(CalendarRules.event("auction_day"), 1, 777, origin)
	check(int(Time.get_datetime_dict_from_unix_time(int(ad.start)).weekday) == 6, "Auction Day falls on a Saturday")
	Clock.override_utc = float(ad.start) - 3600.0
	Game.account.economy.erase("valley_auction")
	Game.economy.auction_roll("valley")
	check(Game.economy.auction_lots("valley").is_empty(), "no valley lots before the day")
	Clock.override_utc = float(ad.start) + 3600.0
	Game.economy.auction_roll("valley")
	var vlots: Array = Game.economy.auction_lots("valley")
	check(vlots.size() == 5 and vlots.all(func(l): return float(l.ends) <= float(ad.end) and str(l.get("house", "")) == "valley"), "five lots on the day, all closing with it")
	var valley_pool: Array = ContentDB.config("auction").get("valley", {}).get("pool", []).map(func(x): return str(x.item))
	check(vlots.all(func(l): return str(l.item) in valley_pool), "the lots come from the valley's pool: seeds, recipe scrolls, eggs, incense")
	var lot: Dictionary = {}
	for l in vlots:
		if str(l.get("learn", "")) != "": lot = l
	if lot.is_empty():
		lot = vlots[0]
		lot.learn = "cloudtop_orchid_broth"
		lot.item = "recipe_scroll"
	c.crafting.recipes.erase(str(lot.learn))
	Game.account.currencies["spirit_stone"] = 5000
	var won: Dictionary = Game.submit({"type": "auction_bid", "house": "valley", "lot": str(lot.id), "amount": int(lot.cap) + 5})
	check(won.get("top", false), "a bid above the house's limit holds the lot")
	Clock.override_utc = float(ad.end) + 60.0
	Game.economy._auction_close("valley")
	check(c.crafting.recipes.has(str(lot.learn)) and Game.account.mail.size() > mail0, "when the hammer falls the recipe is yours")
	check(str(Game.submit({"type": "auction_bid", "house": "valley", "lot": str(vlots[0].id), "amount": 999}).get("reason", "")) == "closed", "after the day the stall is gone")
	# A Spirit Fruit birth: two rivals and a guardian; beat all three and the fruit is yours, once.
	var tb := CalendarRules.occurrence(CalendarRules.event("treasure_birth"), 2, 777, origin)
	Clock.override_utc = float(tb.start) + 600.0
	Game.world.load_room(c, str(tb.room), "")
	GameEvents.flush()
	var tree := {}
	for o in Game.room_rt.def.get("objects", []):
		if str(o.type) == "treasure_birth": tree = o
	check(not tree.is_empty() and Game.world.object_visible(c, tree), "the fruit tree stands in %s while the fruit is ripe" % tb.room)
	c.cooldowns.erase("birth_k")
	check(Game.calendar.open_treasure(c).get("ok", false), "reaching for it wakes its guardians")
	var foes: Array = Game.room_rt.living_enemies().filter(func(e): return e.summoned)
	var defs: Array = foes.map(func(e): return e.def_id)
	check(defs.count("rogue_cultivator") == 2 and defs.has("fruit_guardian"), "two rival cultivators and the Fruit-Guardian Boar %s" % str(defs))
	for e in foes:
		Game.combat.apply_execute(e, c.id)
		GameEvents.flush()
	check(c.inventory.count("spirit_fruit") == 1 and not Game.room_rt.event.get("active", false), "all three down: the Spirit Fruit is yours")
	check(str(Game.calendar.open_treasure(c).get("reason", "")) == "taken", "one fruit per birth")
	# The Herb Terraces trial: herbs gathered there count; the ranking pays when the day ends.
	var gtr := CalendarRules.occurrence(CalendarRules.event("gathering_trial"), 1, 777, origin)
	Clock.override_utc = float(gtr.start) + 3600.0
	Game.world.load_room(c, "ja_herb_terraces", "")
	GameEvents.flush()
	c.cooldowns.erase("gtrial")
	Game.calendar._on_gathered({"actor": c.id, "item": "mist_lotus", "count": 30})
	check(int(c.cooldowns.gtrial.pts) == 30 and Game.calendar.trial_rank(c) == 1, "thirty herbs lead the valley's gatherers")
	check(Game.calendar.trial_rivals(int(gtr.k)) == Game.calendar.trial_rivals(int(gtr.k)), "the rivals' scores are fixed for the trial")
	c.crafting.recipes.erase("foundation_guard_pill")
	Game.calendar._pay_trial(c)
	check(not c.crafting.recipes.has("foundation_guard_pill"), "nothing is paid while the trial runs")
	Clock.override_utc = float(gtr.end) + 60.0
	Game.calendar._pay_trial(c)
	GameEvents.flush()
	check(c.crafting.recipes.has("foundation_guard_pill") and c.inventory.count("foundation_guard_pill") == 3, "first place: the Foundation Guard Pill recipe and three pills")
	var n3: int = c.inventory.count("foundation_guard_pill")
	Game.calendar._pay_trial(c)
	check(c.inventory.count("foundation_guard_pill") == n3, "paid once")
	# Weather: a storm feeds Thunder; rain widens the fishing window; clear skies take it all away.
	Game.combat.apply_weather(c.id, "storm")
	check(near(c.stats.conditional("elemental_power", "element", "thunder"), 0.10), "a storm: Thunder +10%")
	Game.combat.apply_weather(c.id, "clear")
	check(near(c.stats.conditional("elemental_power", "element", "thunder"), 0.0), "and it passes")
	check(near(float(ContentDB.config("calendar").weather_effects.rain.fishing_window), 0.2), "rain: fish bite eagerly (+20% window)")
	check(CalendarRules.weather("marsh", origin + 5000.0, 777) == CalendarRules.weather("marsh", origin + 5000.0, 777), "the weather is the same on every device")
	c.cooldowns = cd_was
	c.crafting.recipes = recipes_was
	c.inventory.bag.fill(null)
	Clock.override_utc = over_was
	Game.account.created_utc = created_was
	Game.account.rng_seed = seed_was
	Game.account.currencies["spirit_stone"] = stones0
	Game.account.economy = econ_was
	while Game.account.mail.size() > mail0: Game.account.mail.pop_front()
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 fortune encounters, heavenly phenomena and lifespan.
func fortune_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var fortune_was: Dictionary = c.relations.fortune.duplicate(true)
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var rel_was := [c.relations.merit, c.relations.alignment, c.relations.fame]
	var qp_was: float = c.cultivator.qp
	var daos_was: Dictionary = c.cultivator.daos.duplicate(true)
	var codex_had: bool = Game.account.codex.has("river_dream")
	var created_was: float = c.created_utc
	c.inventory.bag.fill(null)
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	# The meter: empty for a new hand, full after three hours of play, and it holds only one.
	c.relations.fortune = {}
	check(near(Game.relations.fortune_meter(c), 0.0), "a new character's Fortune meter starts empty")
	check(Game.relations.fortune_check(c, "room_entered").is_empty(), "no encounter while it is empty")
	Game.relations._fill_fortune(c, 3.0 * 3600.0 - 60.0)
	check(Game.relations.fortune_meter(c) < 1.0, "a minute short of three hours of play, not yet")
	Game.relations._fill_fortune(c, 120.0)
	check(near(Game.relations.fortune_meter(c), 1.0), "full after three hours of play, and no fuller")
	var fired := 0
	for i in 500:
		if not Game.relations.fortune_check(c, "room_entered").is_empty(): fired += 1
	GameEvents.flush()
	check(fired == 1, "a full meter turns up one encounter, then holds the rest back (%d in 500 rooms)" % fired)
	# The deck: where each card can come, what it asks, and once-only cards.
	var ids := func(trigger: String) -> Array: return Game.relations.fortune_cards(c, trigger).map(func(o): return str(o.card.id))
	check(not (ids.call("room_entered") as Array).has("hidden_cave") and (ids.call("fell_out") as Array).has("hidden_cave"), "the Hidden Cave comes only from a fall")
	var crane: bool = c.pets.any(func(pp): return str(pp.species) == "jade_crane")
	check((ids.call("room_entered") as Array).has("wounded_crane") == crane, "the wounded crane comes only to someone who keeps a Jade Crane")
	c.relations.fortune["seen"] = {"river_dream": 1}
	check(not (ids.call("room_entered") as Array).has("river_dream"), "the River dream comes once")
	var w0: float = Game.relations.fortune_cards(c, "room_entered").filter(func(o): return str(o.card.id) == "lost_child")[0].w
	c.relations.merit += 200
	var w1: float = Game.relations.fortune_cards(c, "room_entered").filter(func(o): return str(o.card.id) == "lost_child")[0].w
	check(w1 > w0, "merit makes a kind vignette likelier")
	c.relations.merit -= 200
	# A lost child walked home: merit.
	var m0: int = c.relations.merit
	check(str(Game.relations.fortune_check(c, "room_entered", "lost_child").get("id", "")) == "lost_child" and c.relations.merit == m0 + 10, "a lost child walked home: +10 merit")
	# The Hidden Cave: the fall ends in the grotto; its chest fills for each such fall; the way up leaves you where you fell.
	var at: Vector2 = Game.actor_state(c.id).plane
	Game.relations.fortune_check(c, "fell_out", "hidden_cave")
	GameEvents.flush()
	check(Game.room_rt.room_id == "hg_hidden_grotto", "a fall that draws the Hidden Cave ends in the Hidden Grotto")
	var chest := {}
	for o in Game.room_rt.def.get("objects", []):
		if str(o.id) == "grotto_chest": chest = o
	var k1 := Game.world.open_key(chest)
	check(Game.world.object_available(c, chest).get("ok", false), "an old chest waits on the ledge")
	check(Game.world.use_portal(c, "way_up", true).get("ok", false) and Game.room_rt.room_id == "rm_marsh_edge"
		and Game.actor_state(c.id).plane.distance_to(at) < 60.0, "the way up leaves you where you fell")
	GameEvents.flush()
	Game.relations.fortune_check(c, "fell_out", "hidden_cave")
	GameEvents.flush()
	check(Game.world.open_key(chest) != k1, "the chest fills again for the next such fall")
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	# The Hundred-Year Wine: the next Perfect batch is likelier to come out Grain.
	Game.apply_effects(c.id, [{"kind": "grain_blessing"}], "test")
	check(near(float(c.cooldowns.get("grain_blessing", 0.0)), 0.25), "the wine blesses the next batch (+25% Grain)")
	if Unlocks.is_unlocked(c.id, "perfect_timing"):
		Game.crafting.apply_grain_blessing(c.id, 1.0)
		check(Game.crafting._rare_pill_quality(c, [1.0, 1.0, 1.0], _seeded(3)) in ["pill_grain", "pill_halo", "pill_soul"], "blessed, a Perfect run comes out Grain or better")
	# Heavenly phenomena: a major breakthrough gathers clouds, a tribulation lightning; minor steps pass quietly.
	var seen: Array = []
	var on_ph := func(p: Dictionary): seen.append(str(p.kind))
	GameEvents.subscribe("heavenly_phenomenon", on_ph, 200)
	Game.calendar._on_breakthrough({"actor": c.id, "to": "qi_kindling_2", "major": false})
	Game.calendar._on_breakthrough({"actor": c.id, "to": "qi_unfurling_1", "major": true})
	Game.calendar._on_tribulation({"actor": c.id, "to": "cloud_stride_1"})
	GameEvents.flush()
	check(seen == ["cloud", "lightning"], "clouds for a major breakthrough, lightning for a tribulation, nothing for a minor step %s" % str(seen))
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	Game.relations.challenges.erase(c.id)
	var offered := false
	for i in 30:
		Game.relations._on_phenomenon({"actor": c.id, "kind": "cloud", "people": 3})
		if str(Game.relations.challenge_of(c).get("enemy", "")) == "jealous_senior": offered = true
		Game.relations.challenges.erase(c.id)
	check(offered, "where people saw it, a jealous senior may step out")
	Game.relations._on_phenomenon({"actor": c.id, "kind": "cloud", "people": 0})
	check(Game.relations.challenge_of(c).is_empty(), "with nobody there to see, nobody is jealous")
	GameEvents.unsubscribe_object(self)
	# Lifespan: display only. Each great realm's span, a year every four weeks, longevity treasures, ageing people.
	check(int(ContentDB.realm("mortal").max_years) == 80 and int(ContentDB.realm("bone_forging_1").max_years) == 100
		and int(ContentDB.realm("world_genesis").max_years) == 0, "a mortal lives 80 years, Bone Forging 100, World Genesis without end")
	c.created_utc = 1_700_000_000.0
	check(ProgressionRules.age_of(c, c.created_utc + 27.0 * 86400.0) == 16 and ProgressionRules.age_of(c, c.created_utc + 29.0 * 86400.0) == 17, "sixteen at the start, a year older every four weeks")
	check(ProgressionRules.npc_age("granny_liu", c, c.created_utc + 57.0 * 86400.0) == 85, "Granny Liu grows older alongside you")
	var span0 := ProgressionRules.lifespan_of(c)
	Game.inventory.apply_add(c.id, "longevity_peach", 1, "test")
	var pi: int = c.inventory.first_index("longevity_peach")
	Game.submit({"type": "use_item", "index": pi, "confirm": true})
	GameEvents.flush()
	check(ProgressionRules.lifespan_of(c) == span0 + 10 and c.inventory.count("longevity_peach") == 0, "eating a Longevity Peach adds ten years")
	# Restore.
	c.created_utc = created_was
	c.cultivator.longevity = 0
	c.relations.fortune = fortune_was
	c.cooldowns = cd_was
	c.relations.merit = int(rel_was[0])
	c.relations.alignment = int(rel_was[1])
	c.relations.fame = int(rel_was[2])
	c.cultivator.qp = qp_was
	c.cultivator.daos = daos_was
	if not codex_had: Game.account.codex.erase("river_dream")
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## S49 the Trial Tower with its sweep, daily activity chests and the Heaven Ranking.
func tower_activity_ranking_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var tower_was: Dictionary = c.tower.duplicate(true)
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var act_was: Dictionary = Game.account.activity.duplicate(true)
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	var fame_was: int = c.relations.fame
	var created_was: float = Game.account.created_utc
	var seed_was: int = Game.account.rng_seed
	c.inventory.bag.fill(null)
	# The tower: thirty floors, two Levels apart, a guardian every fifth.
	var floors: Array = ContentDB.all("tower")
	check(floors.size() == 30 and int(floors[0].level) == 4 and int(floors[29].level) == 62, "thirty floors, Level 4 to 62")
	check(floors.filter(func(f): return str(f.kind) == "guardian").size() == 6 and floors.all(func(f): return str(f.kind) != "guardian" or not (f.foes as Array).has(str(f.guardian))),
		"a guardian every fifth floor, never escorted by its own kind")
	c.tower = {}
	check(str(Game.world.climb_tower(c, 2).get("reason", "")) == "locked", "floor 2 waits for floor 1")
	check(Game.world.climb_tower(c, 1).get("ok", false) and Game.room_rt.room_id == "sf_trial_tower" and Game.room_rt.event.get("active", false),
		"climbing floor 1 starts its trial in the tower")
	GameEvents.flush()
	for e in Game.room_rt.living_enemies().filter(func(e2): return e2.summoned or e2.team == "enemy"):
		Game.combat.apply_execute(e, c.id)
		GameEvents.flush()
	check(Game.world.tower_cleared(c) == 1 and not Game.room_rt.event.get("active", false), "every foe down: floor 1 is cleared")
	check(int(Game.account.currencies.get("spirit_stone", 0)) == stones0 + int(floors[0].stones), "the first clear pays Spirit Stones")
	# A survive floor passes when the time runs out.
	c.tower["cleared"] = 1
	Game.world.climb_tower(c, 2)
	GameEvents.flush()
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(Game.world.tower_cleared(c) == 2, "floor 2 (survive): holding out clears it")
	# The sweep: every cleared floor once a day, straight to the bag.
	var silver0: int = Game.economy.balance("silver_tael")
	var sw := Game.world.sweep_tower(c)
	check(sw.get("ok", false) and int(sw.floors) == 2 and Game.economy.balance("silver_tael") > silver0, "sweeping gives both cleared floors' loot")
	check(str(Game.world.sweep_tower(c).get("reason", "")) == "nothing", "once a day")
	# Daily activity: sources, caps, the four chests.
	Game.account.activity = {}
	var a0: Dictionary = Game.accounts.activity()
	check(int(a0.points) == 0 and (a0.claimed as Array).is_empty(), "the day starts with no activity")
	for i in 20: Game.accounts.apply_activity("harvest")
	check(int(Game.accounts.activity().by.harvest) == 20, "harvests are capped at 20 points a day")
	check(str(Game.submit({"type": "claim_activity_chest", "tier": "chest_40"}).get("reason", "")) == "short", "the 40-point chest waits")
	check(Game.submit({"type": "claim_activity_chest", "tier": "chest_20"}).get("ok", false), "the 20-point chest opens")
	check(str(Game.submit({"type": "claim_activity_chest", "tier": "chest_20"}).get("reason", "")) == "claimed", "once a day")
	GameEvents.emit_event("quest_completed", {"actor": c.id, "quest": "daily_x", "name": "x", "kind": "daily"})
	GameEvents.emit_event("tower_floor_cleared", {"actor": c.id, "floor": 3, "first": false})
	GameEvents.flush()
	check(int(Game.accounts.activity().points) == 20 + 10 + 10, "a mission and a tower floor add 10 each (%d)" % int(Game.accounts.activity().points))
	# The Heaven Ranking: seeded, the same on every device, climbing week by week.
	var origin := 1_700_000_000.0
	Game.account.created_utc = origin
	Game.account.rng_seed = 4242
	var t1: Array = CalendarRules.rank_table(origin + 86400.0, 4242, origin)
	check(t1.size() == 7 and t1 == CalendarRules.rank_table(origin + 86400.0, 4242, origin), "seven seeded cultivators, the same table on every device")
	var sl := ContentDB.entry("rankings", "shen_lian")
	check(CalendarRules.rank_level(sl, 5) == 20 and CalendarRules.rank_level(sl, 100) == int(sl.cap), "Shen Lian climbs two Levels a week, to her ceiling")
	var sorted_ok := true
	for i in range(1, t1.size()): sorted_ok = sorted_ok and int(t1[i - 1].cp) >= int(t1[i].cp)
	check(sorted_ok, "strongest first")
	# Entering: by CP (top eight) or the tournament finals.
	# P12: the rivals' CP is the par character's at their Level, so the rule is read as written: a place in the top
	# eight (seven seeded rivals leave the eighth open) or a CP at least the eighth's.
	var entered := Game.calendar.rank_entered(c)
	var now_table := CalendarRules.rank_table(Clock.now_utc(), 4242, origin)
	var top := int(ContentDB.config("rankings").get("top", 8))
	check(entered == (now_table.size() < top or StatRules.combat_power(c) >= int(now_table[top - 1].cp)), "you enter at the top eight by CP")
	c.quests.done["the_valley_finals"] = 1
	check(Game.calendar.rank_entered(c) and Game.calendar.ranking(c).any(func(o): return o.get("player", false)), "or by reaching the tournament finals")
	var above := Game.calendar.rank_above(c)
	if not above.is_empty():
		var other: Array = Game.calendar.ranking(c).filter(func(o): return not o.get("player", false) and str(o.id) != str(above.id))
		if not other.is_empty(): check(str(Game.calendar.challenge_rank(c, str(other[0].id)).get("reason", "")) == "not_above", "only the one directly above can be challenged")
		c.cooldowns["rank_duel"] = str(above.id)
		var f0: int = c.relations.fame
		Game.calendar._on_rank_spar({"opponent": str(ContentDB.entry("rankings", str(above.id)).enemy), "winner": "player"})
		GameEvents.flush()
		var t2: Array = Game.calendar.ranking(c)
		var mine := -1
		var theirs := -1
		for i in t2.size():
			if t2[i].get("player", false): mine = i
			elif str(t2[i].id) == str(above.id): theirs = i
		check(mine >= 0 and mine < theirs and c.relations.fame > f0, "beat them in a spar and you hold their place for the week (+Fame)")
	c.quests.done.erase("the_valley_finals")
	# Restore.
	c.tower = tower_was
	c.cooldowns = cd_was
	c.relations.fame = fame_was
	Game.account.activity = act_was
	Game.account.currencies["spirit_stone"] = stones0
	Game.account.created_utc = created_was
	Game.account.rng_seed = seed_was
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## S49 mobile conventions: idle rooms, auto-hunt only where allowed, and quest auto-path over the room graph.
func mobile_conventions_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var idle_was: Dictionary = c.idle_task.duplicate(true)
	var hp_was: float = c.pools.hp
	# Idle Hunt and Gather only where the room allows them.
	check(Game.world.idle_allowed("rm_marsh_edge", "hunt") and not Game.world.idle_allowed("sf_market", "hunt") and Game.world.idle_allowed("sf_market", "rest"),
		"idle Hunt runs in the marsh, not on Market Street (rest goes anywhere)")
	if Unlocks.is_unlocked(c.id, "idle_tasks"):
		check(str(Game.accounts.set_idle_task(c, {"task": "hunt", "room": "sf_market"}).get("reason", "")) == "room", "idle hunting in a town is refused")
		check(Game.accounts.set_idle_task(c, {"task": "hunt", "room": "rm_marsh_edge"}).get("ok", false), "idle hunting in the marsh is accepted")
	# Auto-hunt: refused outside eligible rooms, on in a hunting room, off when a room event starts or health runs low.
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	check(str(Game.submit({"type": "set_auto_hunt", "on": true}).get("reason", "")) == "room" and not Game.world.auto_hunting(c.id), "auto-hunt is refused in a town")
	Game.world.load_room(c, "sf_trial_tower", "")
	GameEvents.flush()
	check(str(Game.submit({"type": "set_auto_hunt", "on": true}).get("reason", "")) == "room", "and in a trial")
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	for e in Game.room_rt.living_enemies():
		if e.is_boss(): Game.enemies.release(e)
	c.pools.hp = c.pools.max_hp
	check(Game.submit({"type": "set_auto_hunt", "on": true}).get("ok", false) and Game.world.auto_hunting(c.id), "auto-hunt turns on in the marsh")
	Game.world.start_room_event(c, {"id": "test_event", "duration": 30.0})
	Game.world._tick_auto_hunt(c, 1.0)
	GameEvents.flush()
	check(not Game.world.auto_hunting(c.id), "a room event turns it off")
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(Game.submit({"type": "set_auto_hunt", "on": true}).get("ok", false), "and it can go on again after")
	c.pools.hp = c.pools.max_hp * 0.1
	Game.world._tick_auto_hunt(c, 1.0)
	check(not Game.world.auto_hunting(c.id), "low health turns it off")
	c.pools.hp = c.pools.max_hp
	# Auto-path: the fewest rooms through open portals, the portal to take here, arriving, and stopping at danger.
	var r1: Array = Game.world.route(c, "wp_west", "sf_market")
	check(not r1.is_empty() and str(r1[0].room) == "wp_west" and str(r1.back().to) == "sf_market", "a route from the Willow Path to Market Street (%d rooms)" % r1.size())
	var linked := true
	for i in range(1, r1.size()): linked = linked and str(r1[i].room) == str(r1[i - 1].to)
	check(linked, "each step leaves from where the last one arrived")
	check(r1 == Game.world.route(c, "wp_west", "sf_market"), "the same route every time")
	var shut: Dictionary = {"to": "wp_east", "requires": {"all": [{"kind": "flag_set", "flag": "never_set_flag"}]}}
	check(not Game.world.portal_open(c, "lf_village", shut), "a portal whose requirement is unmet is not on any route")
	Game.world.load_room(c, "wp_west", "")
	GameEvents.flush()
	check(Game.submit({"type": "auto_path", "target": "sf_market"}).get("ok", false) and str(Game.world.auto_path_step(c).get("portal", "")) == str(r1[0].portal),
		"auto-path shows the portal to take in this room")
	check(not Game.world.auto_hunting(c.id), "auto-path and auto-hunt never run together")
	GameEvents.emit_event("hit_landed", {"attacker": "x", "target": c.id, "target_kind": "player", "amount": 1})
	GameEvents.flush()
	check(Game.world.auto_path_target(c) == "", "a blow stops auto-path")
	Game.submit({"type": "auto_path", "target": "sf_market"})
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	check(Game.world.auto_path_target(c) == "", "arriving ends it")
	check(str(Game.submit({"type": "auto_path", "target": "sf_market"}).get("reason", "")) == "here", "nothing to do where you already are")
	# Across the Starsea: the route sails from the shipyard's dock.
	var sea: Array = WorldRules.route("ae_shipyard", "sw_broken_pier", func(_r, _p): return true)
	check(sea.size() == 1 and sea[0].get("dock", false), "the Skyport Wreck is a voyage from the shipyard's dock")
	# Restore.
	Game.world.auto_hunt.clear()
	Game.world.auto_paths.clear()
	c.idle_task = idle_was
	c.pools.hp = hp_was
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## V9a: v2's remaining requirement and effect kinds, the treasure-birth announcement and the pet command wheel.
func v2_hooks_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var req := func(cond: Dictionary) -> bool: return RequirementRules.passes({"all": [cond]}, Game.ctx(c))
	# heart_demon_at_most and foundation_share_at_most (S48, S44).
	var hd_was: float = c.cultivator.heart_demon
	c.cultivator.heart_demon = 40.0
	check(req.call({"kind": "heart_demon_at_most", "value": 50}) and not req.call({"kind": "heart_demon_at_most", "value": 30}), "heart_demon_at_most")
	c.cultivator.heart_demon = hd_was
	var f_was: Dictionary = c.cultivator.foundation.duplicate()
	c.cultivator.foundation = {"realm": ProgressionRules.great_realm(c.cultivator.realm_key), "pill_qp": 40.0, "total_qp": 100.0}
	check(req.call({"kind": "foundation_share_at_most", "value": 0.5}) and not req.call({"kind": "foundation_share_at_most", "value": 0.3}), "foundation_share_at_most")
	c.cultivator.foundation = f_was
	# art_known and grant_art: v2's names for the secret (movement) arts.
	var arts_was: Array = c.cultivator.secret_arts.duplicate()
	c.cultivator.secret_arts.erase("breath_control")
	check(not req.call({"kind": "art_known", "art": "breath_control"}), "art_known: not yet")
	Game.apply_effects(c.id, [{"kind": "grant_art", "art": "breath_control"}], "test")
	GameEvents.flush()
	check(req.call({"kind": "art_known", "art": "breath_control"}), "grant_art teaches it")
	c.cultivator.secret_arts = arts_was
	# grant_fate: a fate given outright, as if chosen.
	var fates_was: Array = c.cultivator.fates.duplicate(true)
	var offer_was: Array = c.cultivator.fate_offer.duplicate()
	Game.apply_effects(c.id, [{"kind": "grant_fate", "fate": "lucky_star"}], "test")
	GameEvents.flush()
	check(c.cultivator.fates.any(func(f): return str(f.id) == "lucky_star") and c.cultivator.fate_offer == offer_was, "grant_fate adds the fate and leaves any offer alone")
	c.cultivator.fates = fates_was
	# absorb_flame as an effect: a flame given outright burns under every furnace.
	var flames_was: Array = (c.crafting.get("flames", []) as Array).duplicate()
	var fl: Array = flames_was.duplicate()
	fl.erase("comet_tail_flame")
	c.crafting["flames"] = fl
	Game.apply_effects(c.id, [{"kind": "absorb_flame", "flame": "comet_tail_flame"}], "test")
	GameEvents.flush()
	check((c.crafting.get("flames", []) as Array).has("comet_tail_flame"), "absorb_flame as an effect")
	c.crafting["flames"] = flames_was
	# treasure_birth_announced: World names the fruit and the room when the calendar starts a birth.
	var heard: Array = []
	GameEvents.subscribe("treasure_birth_announced", func(p): heard.append(p), 200)
	GameEvents.emit_event("world_event_started", {"event": "treasure_birth", "k": 1, "room": "wp_east", "ends": 0.0})
	GameEvents.flush()
	check(heard.size() == 1 and str(heard[0].room) == "wp_east" and str(heard[0].item) != "", "a treasure birth is announced with its room and fruit")
	GameEvents.unsubscribe_object(self)
	# The pet command wheel: a known order is kept for every animal out; an unknown one is refused.
	check(Game.submit({"type": "pet_command", "command": "stay"}).get("ok", false) and str(Game.pets.commands.get(c.id, "")) == "stay", "stay")
	check(not Game.submit({"type": "pet_command", "command": "dance"}).get("ok", true), "an unknown order is refused")
	Game.submit({"type": "pet_command", "command": "follow"})
	GameEvents.flush()

## v2 "Depth hooks": every S44-S49 field is written with a neutral value from the start, and round-trips through a
## save (as JSON) and a restore. The build's names for v2's fields are listed in docs/v2_audit.md (Deviations).
func depth_hooks_suite() -> void:
	var c = Game.active()
	if c == null: return
	var norm := func(v): return JSON.parse_string(JSON.stringify(v))
	# A new character carries every depth field, neutral.
	var fresh := GameCharacter.new()
	var fs: Dictionary = fresh.snapshot()
	var cu_keys := ["pill_resistance", "foundation", "residue", "heart_demon", "support_failures", "body_tier", "core_grade", "fates", "physiques",
		"vows", "inner_arts", "stances", "false_realm", "longevity", "epiphany_cooldown"]
	var rel_keys := ["merit", "sin", "debts", "alignment", "fame", "affinity", "bonds", "grudges", "bounties", "mortal", "fortune"]
	var inv_keys := ["treasures", "loadout", "furnace", "draught", "vessel"]
	var missing: Array = []
	for k in cu_keys:
		if not (fs.cultivator as Dictionary).has(k): missing.append("cultivator." + k)
	for k in rel_keys:
		if not (fs.relations as Dictionary).has(k): missing.append("relations." + k)
	for k in inv_keys:
		if not (fs.inventory as Dictionary).has(k): missing.append("inventory." + k)
	for k in ["pets", "pet_bag", "mount_pet", "party_pets", "tower", "beast_arena", "crafting"]:
		if not fs.has(k): missing.append(k)
	check(missing.is_empty(), "a new character carries every S44-S49 field (%s)" % ", ".join(missing))
	check(float(fs.cultivator.heart_demon) == 0.0 and float(fs.cultivator.residue) == 0.0 and (fs.cultivator.fates as Array).is_empty()
		and (fs.cultivator.vows as Array).is_empty() and int(fs.relations.merit) == 0 and int(fs.relations.sin) == 0 and int(fs.relations.alignment) == 0
		and int(fs.relations.fame) == 0, "and every one starts neutral")
	var acc_snap: Dictionary = AccountState.new().snapshot()
	check(acc_snap.has("calendar") and acc_snap.has("activity") and acc_snap.has("sect"), "the account carries the calendar, activity and sect blocks")
	# Non-neutral values survive a save and a restore.
	var ch := GameCharacter.new()
	ch.restore(c.snapshot())
	var cu: CultivatorState = ch.cultivator
	cu.heart_demon = 37.0
	cu.residue = 12
	cu.foundation = {"realm": ProgressionRules.great_realm(cu.realm_key), "pill_qp": 50.0, "total_qp": 200.0}
	cu.pill_resistance = {"accumulation": {"count": 1, "doses": 3}}
	cu.support_failures = {"bone_forging": 1}
	cu.fates = [{"id": "hungry_dantian", "realm": ProgressionRules.great_realm(cu.realm_key)}]
	cu.vows = ["no_burst_pills"]
	cu.stances = {"sword": "sword_flowing"}
	cu.epiphany_cooldown = 1234.0
	var rel: RelationsState = ch.relations
	rel.merit = 42
	rel.sin = 7
	rel.alignment = -25
	rel.fame = 88
	rel.grudges = {"mudwater": 30}
	rel.mortal = {"favour": 60, "day": 3}
	rel.affinity = {"mei_qing": {"points": 40, "gift_day": 5}}
	ch.tower = {"cleared": 3, "swept": {"1": 2}}
	ch.beast_arena = {"rank": 4}
	ch.inventory.treasures = ["bright_mirror", ""]
	var s1: Dictionary = ch.snapshot()
	var ch2 := GameCharacter.new()
	ch2.restore(norm.call(s1))
	var s2: Dictionary = ch2.snapshot()
	var lost: Array = []
	for k in cu_keys:
		if norm.call(s1.cultivator[k]) != norm.call(s2.cultivator[k]): lost.append("cultivator." + k)
	for k in rel_keys:
		if norm.call(s1.relations[k]) != norm.call(s2.relations[k]): lost.append("relations." + k)
	for k in inv_keys:
		if norm.call(s1.inventory[k]) != norm.call(s2.inventory[k]): lost.append("inventory." + k)
	for k in ["pets", "tower", "beast_arena", "crafting", "mount_pet", "pet_bag"]:
		if norm.call(s1[k]) != norm.call(s2[k]): lost.append(k)
	check(lost.is_empty(), "every depth field round-trips through save and restore (%s)" % ", ".join(lost))
	# The account's depth blocks too: the calendar, the activity chests, the sect's mines.
	var acc := AccountState.new()
	acc.restore(Game.account.snapshot())
	acc.calendar = {"active": {"spatial_rift": 3}, "told": {}, "weather": {"marsh": "rain"}, "season": "autumn"}
	acc.activity = {"day": 9, "points": 40, "claimed": [20]}
	acc.sect = {"name": "Test", "level": 3, "mines": {"lower_pit_seam": {"collected": 100.0, "contest": 200.0, "contested": false, "until": 0.0, "guards": [0], "n": 1}}}
	var a1: Dictionary = acc.snapshot()
	var acc2 := AccountState.new()
	acc2.restore(norm.call(a1))
	var a2: Dictionary = acc2.snapshot()
	check(norm.call(a1.calendar) == norm.call(a2.calendar) and norm.call(a1.activity) == norm.call(a2.activity) and norm.call(a1.sect) == norm.call(a2.sect),
		"the account's calendar, activity and sect (with its mines) round-trip")

## S49 territory: spirit mines taken from rival sects, their carts, the old holders' timers, the guards.
func territory_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var sect_was: Dictionary = Game.account.sect.duplicate(true)
	var stones0: int = Game.economy.balance("spirit_stone")
	var cfg: Dictionary = ContentDB.config("territory")
	var base_was: float = float(cfg.contest.base)
	var t0 := Clock.now_utc()
	var seen := {"claimed": 0, "contested": 0, "defended": [], "lost": [], "collected": 0}
	GameEvents.subscribe("mine_claimed", func(_p): seen.claimed += 1, 200)
	GameEvents.subscribe("mine_contested", func(_p): seen.contested += 1, 200)
	GameEvents.subscribe("mine_defended", func(p): seen.defended.append(str(p.by)), 200)
	GameEvents.subscribe("mine_lost", func(p): seen.lost.append(int(p.stones)), 200)
	GameEvents.subscribe("mine_collected", func(p): seen.collected += int(p.stones), 200)
	# Five mines in field rooms, each held by one of three rival sects with guards and a warden.
	var ms: Array = ContentDB.all("territory")
	var placed := 0
	for m in ms:
		if Game.sect.rival(str(m.sect)).is_empty(): continue
		for o in ContentDB.room(str(m.room)).get("objects", []):
			if str(o.type) == "spirit_mine" and str(o.get("mine", "")) == str(m.id): placed += 1
	check(ms.size() == 5 and placed == 5, "five mines, each a vein in its room and held by a rival sect")
	var armed := 0
	for r in cfg.sects:
		if not ContentDB.entry("enemies", str(r.disciple)).is_empty() and not ContentDB.entry("enemies", str(r.warden)).is_empty() \
			and not SpriteCache.prop(str(r.banner)).is_empty(): armed += 1
	check(armed == (cfg.sects as Array).size() and armed == 3, "every rival has guards, a warden and a banner")
	# No sect, no mine.
	Game.account.sect = {}
	check(Game.sect.assault_block(c, "lower_pit_seam") == Tx.t("sim.sect.mine_no_sect"), "only a sect can hold a mine")
	Game.account.sect = {"name": "Test", "emblem": [0, 0], "level": 1, "prestige": 0, "buildings": {"sect_hall": 1}, "queue": [], "candidates": [],
		"candidate_day": Clock.reset_day(t0), "expeditions": [], "disciples": [{"name": "Wei", "level": 5, "trait": "green_thumb"}, {"name": "Lan", "level": 3, "trait": "green_thumb"}]}
	check(Game.sect.mine_cap() == 1 and Game.sect.assault_block(c, "grey_pools_seep") == Tx.t("sim.sect.needs_sect_level") % 2, "a new sect holds one mine; the Grey Pools needs sect level 2")
	# Taking the Lower Pit: at the mine, its guards and the warden; the warden falls and the mine is yours.
	Game.world.load_room(c, "wp_west", "")
	GameEvents.flush()
	check(str(Game.submit({"type": "assault_mine", "mine": "lower_pit_seam"}).get("reason", "")) == "wrong_room", "you fight for a mine at the mine")
	Game.world.load_room(c, "sq_lower_pit", "")
	GameEvents.flush()
	Game.actor_state(c.id).plane = Vector2(1100, 870)
	Game.actor_state(c.id).altitude = 0.0
	var dlg: Dictionary = Game.world.interact(c, "mine_lower_pit_seam")
	var offers := false
	for choice in dlg.get("dialogue", {}).get("choices", []):
		if str(choice.get("intent", {}).get("type", "")) == "assault_mine": offers = true
	check(offers, "the vein offers to take the mine (%s)" % str(dlg).left(300))
	check(Game.submit({"type": "assault_mine", "mine": "lower_pit_seam"}).get("ok", false) and str(Game.room_rt.event.get("id", "")) == "mine_assault",
		"the fight for the mine starts")
	GameEvents.flush()
	var wardens: Array = Game.room_rt.living_enemies().filter(func(e): return e.def_id == "ironpine_warden")
	var guards: Array = Game.room_rt.living_enemies().filter(func(e): return e.def_id == "ironpine_disciple")
	check(wardens.size() == 1 and int(wardens[0].level) == 12 and guards.size() == 3 and guards.all(func(e): return int(e.level) == 9),
		"three Ironpine guards at Level 9 and their warden at 12")
	var p0: int = int(Game.sect.sect().prestige)
	Game.combat.apply_execute(wardens[0], c.id)
	GameEvents.flush()
	check(Game.sect.holds("lower_pit_seam") and not Game.room_rt.event.get("active", false) and seen.claimed == 1 and int(Game.sect.sect().prestige) == p0 + 30,
		"the warden falls: the mine is yours (+30 Prestige)")
	Game.sect.sect().level = 2
	check(Game.sect.assault_block(c, "grey_pools_seep") == Tx.plural("sim.sect.mine_cap", 1) % 1, "one more mine only at sect level 3")
	# The carts: a stone an hour, a day's worth at most; only whole stones leave.
	Clock.override_utc = t0 + 5.5 * 3600.0
	check(Game.sect.mine_stored("lower_pit_seam") == 5, "five and a half hours: five stones")
	check(Game.submit({"type": "collect_mine", "mine": "lower_pit_seam"}).get("ok", false) and Game.economy.balance("spirit_stone") == stones0 + 5, "collected")
	Clock.override_utc = t0 + 6.1 * 3600.0
	check(Game.sect.mine_stored("lower_pit_seam") == 1, "the half hour left behind still counts")
	Clock.override_utc = t0 + 60.0 * 3600.0
	check(Game.sect.mine_stored("lower_pit_seam") == 24, "the carts hold a day's worth")
	# Guards: posted and recalled; a guard cannot go on an expedition; more guards hold better.
	var ch0: float = Game.sect.guard_chance("lower_pit_seam")
	check(Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 0}).get("ok", false) and Game.sect.guard_chance("lower_pit_seam") > ch0,
		"a guard posted: the mine is likelier to hold")
	var exr := Game.submit({"type": "send_expedition", "region": "willow_path", "hours": 1, "disciples": [0]})
	check(str(exr.get("reason", "")) == "busy", "a guard stays at the mine (%s)" % str(exr))
	# (S25 expeditions: the one who is home goes, and comes back with the region's goods for every hour away.)
	var silver_ex: int = Game.economy.balance("silver_tael")
	var moss0: int = c.inventory.count("willow_moss")
	check(Game.submit({"type": "send_expedition", "region": "willow_path", "hours": 1, "disciples": [1]}).get("ok", false), "a disciple at home can go")
	check(str(Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 1}).get("reason", "")) == "busy", "and cannot stand guard while away")
	Clock.override_utc = t0 + 61.0 * 3600.0
	var back: Dictionary = Game.submit({"type": "collect_expedition", "index": 0})
	check(back.get("ok", false) and (not back.success or (Game.economy.balance("silver_tael") >= silver_ex + 60 and c.inventory.count("willow_moss") == moss0 + 3)),
		"the expedition comes home (%s)" % str(back))
	Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 1})
	Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 1})
	check((Game.sect.mines().lower_pit_seam.guards as Array) == [0], "a guard recalled")
	c.inventory.bag.fill(null)
	# The old holder comes back on its timer: hold it in person.
	var st: Dictionary = Game.sect.mines().lower_pit_seam
	var due: float = float(st.contest)
	var days := (due - t0) / 86400.0
	check(days >= 2.0 and days <= 4.0, "the Ironpine Gate come back within two to four days (%.1f)" % days)
	Clock.override_utc = due + 60.0
	Game.sect._tick_mines(Clock.now_utc())
	GameEvents.flush()
	check(bool(st.contested) and seen.contested == 1 and is_equal_approx(float(st.until), due + 12.0 * 3600.0), "a contest opens with twelve hours to answer it")
	check(Game.submit({"type": "defend_mine", "mine": "lower_pit_seam"}).get("ok", false) and str(Game.room_rt.event.get("id", "")) == "mine_defence", "holding the mine starts its fight")
	GameEvents.flush()
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(not bool(st.contested) and seen.defended == ["you"] and float(st.contest) > Clock.now_utc() + 2.0 * 86400.0 - 1.0, "held: the next visit is days away")
	# Away while they come: the guards decide it when the window closes; a lost mine takes its carts with it.
	cfg.contest.base = -5.0
	Clock.override_utc = float(st.contest) + 13.0 * 3600.0
	Game.sect._tick_mines(Clock.now_utc())
	GameEvents.flush()
	check(not Game.sect.holds("lower_pit_seam") and seen.lost.size() == 1 and int(seen.lost[0]) == 24, "the guards fall: the mine and its 24 stones are lost")
	check(Game.sect.guarding().is_empty(), "the guards come home")
	# Restore.
	cfg.contest.base = base_was
	Clock.override_utc = -1.0
	GameEvents.unsubscribe_object(self)
	Game.account.sect = sect_was
	Game.economy.apply_currency("spirit_stone", stones0 - Game.economy.balance("spirit_stone"), "test")
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## S49 the mortal kingdom (county jobs, favour, the relief fund, non-interference) and the leisure arts (guqin, chess).
func mortal_leisure_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var mortal_was: Dictionary = c.relations.mortal.duplicate(true)
	var rel_was := [c.relations.merit, c.relations.sin, c.relations.alignment, c.relations.fame]
	var titles_was: Array = c.cultivator.titles.duplicate()
	var active_title_was: String = c.cultivator.active_title
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var silver0: int = Game.economy.balance("silver_tael")
	var realm_was: String = c.cultivator.realm_key
	var qp_was: float = c.cultivator.qp
	var daos_was: Dictionary = c.cultivator.daos.duplicate(true)
	c.inventory.bag.fill(null)
	# County jobs: three a day, fit for your Level, taken as soon as the board is read; the same three all day.
	c.relations.mortal = {}
	var jobs: Array = Game.relations.county_jobs(c)
	check(jobs.size() == 3 and jobs.all(func(q): return c.quests.is_active(str(q)) and str(Game.quest.quest_def(c, str(q)).kind) == "mortal"), "three county jobs are posted and taken")
	check(Game.relations.county_jobs(c) == jobs, "the same jobs all day")
	# Favour: a job pays 10; the tiers name you and grant the county's titles; the top one earns a discount.
	var f0 := Game.relations.favour(c)
	Game.apply_effects(c.id, Game.quest.quest_def(c, str(jobs[0])).get("rewards", []), "test")
	GameEvents.flush()
	check(Game.relations.favour(c) == f0 + 10, "a finished county job earns favour")
	Game.relations.apply_favour(c.id, 150 - Game.relations.favour(c), "test")
	check(str(Game.relations.favour_tier(c).id) == "friend" and c.cultivator.titles.has("friend_of_the_county"), "150 favour: Friend of the County, and its title")
	check(Game.relations.shop_discount(c, "stoneford_tea") < 0.05 or not Game.relations.county_discount(c, "stoneford_tea") > 0.0, "no county discount yet")
	Game.relations.apply_favour(c.id, 400 - Game.relations.favour(c), "test")
	check(near(Game.relations.county_discount(c, "stoneford_tea"), 0.05) and Game.relations.shop_discount(c, "stoneford_tea") >= 0.05, "a Benefactor pays 5% less at Stoneford's tea house")
	check(near(Game.relations.county_discount(c, "alliance_factor"), 0.0), "and nothing off elsewhere")
	# The relief fund: silver for merit and favour, once a day at each size.
	Game.economy.apply_currency("silver_tael", 2000 - Game.economy.balance("silver_tael"), "test")
	var m0: int = c.relations.merit
	var fv: int = Game.relations.favour(c)
	check(Game.submit({"type": "donate_relief", "tier": "small"}).get("ok", false) and Game.economy.balance("silver_tael") == 1900
		and c.relations.merit == m0 + 1 and Game.relations.favour(c) == fv + 3, "100 silver to the relief fund: +1 merit, +3 favour")
	check(str(Game.submit({"type": "donate_relief", "tier": "small"}).get("reason", "")) == "today", "once a day at each size")
	check(str(Game.submit({"type": "donate_relief", "tier": "grand"}).get("reason", "")) == "silver", "a grand gift needs 10,000 silver")
	# Non-interference: a technique in a mortal town from Qi Kindling up is sin, once a minute at most.
	Game.world.load_room(c, "lf_village", "")
	GameEvents.flush()
	c.cultivator.realm_key = "qi_kindling_3"
	var s0: int = c.relations.sin
	GameEvents.emit_event("technique_used", {"actor": c.id, "technique": "x", "hits": 1, "targets": 0})
	GameEvents.emit_event("technique_used", {"actor": c.id, "technique": "x", "hits": 1, "targets": 0})
	GameEvents.flush()
	check(c.relations.sin == s0 + 5, "a technique among the villagers of Lotus Ferry: +5 sin, once a minute (%d)" % (c.relations.sin - s0))
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	var s1: int = c.relations.sin
	c.relations.mortal["warned_s"] = -INF
	GameEvents.emit_event("technique_used", {"actor": c.id, "technique": "x", "hits": 1, "targets": 0})
	GameEvents.flush()
	check(c.relations.sin == s1, "in the wild it is only a technique")
	c.cultivator.realm_key = realm_was
	# The guqin: needs the instrument; the better the playing, the faster meditation runs; then the hands rest.
	c.cooldowns.erase("guqin_until")
	check(str(Game.submit({"type": "play_guqin", "score": 1.0}).get("reason", "")) == "no_guqin", "no guqin, no music")
	Game.inventory.apply_add(c.id, "guqin", 1, "test")
	var acc0: float = c.stats.value("accumulation_rate")
	var gq := Game.submit({"type": "play_guqin", "score": 1.0})
	check(gq.get("ok", false) and near(float(gq.bonus), 0.15) and near(c.stats.value("accumulation_rate"), acc0 + 0.15), "a perfect piece: meditation +15% for half an hour")
	check(str(Game.submit({"type": "play_guqin", "score": 1.0}).get("reason", "")) == "resting", "then the fingers rest")
	check(near(float(Game.progression.play_guqin(c, 0.0).get("bonus", -1.0)), -1.0), "(still resting)")
	# Chess at an insight site: today's problem is the same on every device; the right point, once a day.
	var pz: Dictionary = Game.progression.chess_of("insight_hu")
	check(not pz.is_empty() and pz == Game.progression.chess_of("insight_hu"), "an insight site's problem for today is fixed")
	c.cooldowns.erase("chess:insight_hu")
	var wrong := "A" if str(pz.answer) != "A" else "B"
	check(not Game.submit({"type": "solve_chess", "site": "insight_hu", "choice": wrong}).get("right", true), "a wrong point is wrong")
	check(str(Game.submit({"type": "solve_chess", "site": "insight_hu", "choice": str(pz.answer)}).get("reason", "")) == "done", "one answer a day at each stone")
	c.cooldowns.erase("chess:insight_hu")
	var q0: float = c.cultivator.qp
	var ins0: float = 0.0
	for d in c.cultivator.daos: ins0 += float(c.cultivator.daos[d].get("insight", 0.0))
	check(Game.submit({"type": "solve_chess", "site": "insight_hu", "choice": str(pz.answer)}).get("right", false), "the right point is right")
	var ins1: float = 0.0
	for d in c.cultivator.daos: ins1 += float(c.cultivator.daos[d].get("insight", 0.0))
	check(ins1 > ins0 or c.cultivator.qp > q0 or c.cultivator.state != "accumulating", "and brings insight (or, before any Dao, a little progress)")
	# Restore.
	c.relations.mortal = mortal_was
	c.relations.merit = int(rel_was[0])
	c.relations.sin = int(rel_was[1])
	c.relations.alignment = int(rel_was[2])
	c.relations.fame = int(rel_was[3])
	c.cultivator.titles = titles_was
	c.cultivator.active_title = active_title_was
	c.cooldowns = cd_was
	c.cultivator.qp = qp_was
	c.cultivator.daos = daos_was
	for q in jobs:
		c.quests.active.erase(str(q))
		c.quests.tracked.erase(str(q))
		c.quests.daily.erase(str(q))
	Game.economy.apply_currency("silver_tael", silver0 - Game.economy.balance("silver_tael"), "test")
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

func _seeded(seed: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = seed
	return r

func tribulation_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	c.inventory.bag.fill(null)
	var t1 := Game.crafting.begin_tribulation(c, "soul_soothing_pill", 1, "pill_halo", "charcoal", {})
	check(str(t1.get("pending", "")) == "tribulation" and (t1.bolts as Array).size() == 3, "a Heaven pill faces 3 bolts")
	var last := {}
	for i in 3: last = Game.crafting.tribulation_shield(c, i, 0.05)
	var got := str(last.get("quality", ""))
	if str(last.get("pending", "")) == "soul": got = str(Game.crafting.catch_pill_soul(c, 0.0).get("quality", ""))
	check(got in ["pill_halo", "pill_soul"] and c.inventory.count("soul_soothing_pill") >= 1, "every bolt held: the Halo holds (or rises), and the pills are yours (%s)" % got)
	Game.crafting.begin_tribulation(c, "soul_soothing_pill", 1, "pill_halo", "charcoal", {})
	Game.crafting.tribulation_shield(c, 0, 0.0)
	Game.crafting.tribulation_shield(c, 1, 0.9)
	var miss := Game.crafting.tribulation_shield(c, 2, 0.0)
	check(str(miss.get("quality", "")) == "perfect", "one bolt missed: the pills drop to Perfect")
	check((Game.crafting.begin_tribulation(c, "sage_condensing_pill", 1, "pill_halo", "charcoal", {}).bolts as Array).size() == 5, "a Mystic pill faces 5 bolts")
	Game.crafting.tribulations.erase(c.id)
	check((Game.crafting.begin_tribulation(c, "sovereign_settling_pill", 1, "pill_halo", "charcoal", {}).bolts as Array).size() == 9, "a Sage pill: 9 bolts, the most there are")
	Game.crafting.tribulations.erase(c.id)
	# The Pill Soul flees; a missed catch settles the batch as Pill Halo, never loses it.
	Game.crafting.begin_tribulation(c, "soul_soothing_pill", 2, "pill_soul", "charcoal", {})
	var fl := {}
	for i in 3: fl = Game.crafting.tribulation_shield(c, i, 0.0)
	check(str(fl.get("pending", "")) == "soul", "a Soul pill that comes through flees the furnace")
	var n0: int = c.inventory.count("soul_soothing_pill")
	var cp := Game.crafting.catch_pill_soul(c, 0.8)
	check(not cp.get("caught", true) and str(cp.get("quality", "")) == "pill_halo" and c.inventory.count("soul_soothing_pill") >= n0 + 2,
		"a missed catch: the batch settles as Pill Halo, not lost")
	# A tribulation left unfinished settles when the next craft begins: every unanswered bolt struck.
	Game.crafting.begin_tribulation(c, "soul_soothing_pill", 1, "pill_halo", "charcoal", {})
	var before: int = c.inventory.count("soul_soothing_pill")
	Game.crafting.craft_step(c, "healing_pill", "alchemy", 0.0)
	check(not Game.crafting.tribulations.has(c.id) and c.inventory.count("soul_soothing_pill") == before + 1, "an abandoned tribulation settles, and its pills still come")
	# A shop that sells several recipe scrolls sells the one asked for.
	Game.economy.apply_currency("silver_tael", 5000, "test")
	c.crafting.recipes.erase("qi_refining_pill")
	var realm_was: String = c.cultivator.realm_key
	if ProgressionRules.realm_index(realm_was) < ProgressionRules.realm_index("heart_tempering_5"): c.cultivator.realm_key = "heart_tempering_5"
	var bs := Game.submit({"type": "buy", "shop": "mei_qing_recipes", "item": "recipe_scroll", "count": 1, "learn": "qi_refining_pill"})
	check(bs.get("ok", false) and c.crafting.recipes.has("qi_refining_pill"), "the Recipe Box sells the Qi Refining scroll asked for, not the first on the shelf")
	c.cultivator.realm_key = realm_was
	c.inventory.bag.fill(null)

## V9e2 · the five-screen furnace (S15/S44): the plan drawn when the furnace is lit, each screen scored within range, a
## scorched herb (early: that herb is lost), a cracked pill (late: the batch is lost), a liquid done at Fusion, the fire
## put out, what Spirit Sense tells of sealed herbs, and the same hand with the same seed making the same pills.
func furnace_game_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	c.inventory.bag.fill(null)
	Unlocks.force_unlock(c.id, "alchemy")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	var st: ActorState = Game.actor_state(c.id)
	var fo: Dictionary = Game.room_rt.object_def("furnace_sf")
	st.plane = Vector2(float(fo.at[0]) - 40.0, float(fo.at[1]))
	var furnace_was = c.inventory.furnace
	c.inventory.furnace = null   # one pill at a time, no furnace bonuses
	var give := func(recipe: String, n: int) -> void:
		for inp in ContentDB.entry("recipes", recipe).inputs: Game.inventory.apply_add(c.id, str(inp.item), int(inp.count) * n, "test")
	var r := "healing_pill"
	for rid in [r, "riverreed_draught"]: Game.crafting.apply_learn_recipe(c.id, rid)
	check(not Game.submit({"type": "start_refine", "recipe": r, "count": 1}).get("ok", false), "no herbs: the furnace will not light")
	give.call(r, 3)
	var p := Game.submit({"type": "start_refine", "recipe": r, "count": 1, "fire": "charcoal", "array": "water"})
	if not p.get("ok", false):
		check(false, "lit: a plan of two herbs, Extraction first (%s)" % str(p))
		return
	check(p.get("ok", false) and (p.plan.herbs as Array).size() == 2 and str(p.plan.stage) == "extraction", "lit: a plan of two herbs, Extraction first %s" % str(p.get("text", "")))
	var herbs: Array = p.plan.herbs
	var ginseng := str(herbs[0].item)
	var moss := str(herbs[1].item)
	check(float(herbs[0].centre) > 0.5 and near(float(herbs[1].centre), 0.5), "a hot herb's band sits high on the gauge; a neutral one in the middle")
	check(Game.crafting.suited_array(r) == "water" and float(herbs[0].width) > Game.crafting.heat_band(c, "charcoal", r, "flame"),
		"Still Water answers a hot Principal: its bands are wider than under Rising Flame")
	check(p.plan.order == [0, 1], "the recipe's order: Principal, then Minister")
	var faint := 0
	for sp in herbs[0].specks: if sp.faint: faint += 1
	check(faint == (herbs[0].specks as Array).size() - Game.crafting.impurities_seen(c, (herbs[0].specks as Array).size()),
		"impurities beyond what Crafting perception shows are faint")
	check(str(Game.submit({"type": "refine_input", "step": "fusion", "value": {}}).get("reason", "")) == "wrong_step", "Fusion waits for Extraction")
	check(str(Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": 1, "held": 1.0}}).get("reason", "")) == "wrong_herb",
		"the herbs go in in the recipe's order")
	# An early mistake: the scorched herb's share is lost, the rest kept, and the refine waits for another.
	var g0: int = c.inventory.count(ginseng)
	var m0: int = c.inventory.count(moss)
	var sc := Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": 0, "held": 0.1, "taps": 0}})
	check(sc.get("scorched", false) and sc.get("retry", false) and c.inventory.count(ginseng) == g0 - int(herbs[0].count) and c.inventory.count(moss) == m0,
		"a scorched herb is lost; the other herbs stay in the bag")
	check(int(Game.crafting.refine_session(c).at) == 0, "the refine waits on the same herb")
	var e1 := Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": 0, "held": 5.0, "taps": 99}})
	check(e1.get("ok", false) and near(float(e1.score), 1.0), "the hand's report is held to what could happen: full marks and no more")
	var e2 := Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": 1, "held": 0.6, "taps": 0}})
	check(e2.get("ok", false) and float(e2.score) < 0.6 and str(e2.stage) == "fusion", "a middling hold scores less; then Fusion")
	check(str(Game.submit({"type": "refine_input", "step": "fusion", "value": {"order": [0, 0]}}).get("reason", "")) == "bad_input",
		"an essence merged twice is no fusion")
	var fu := Game.submit({"type": "refine_input", "step": "fusion", "value": {"order": [1, 0], "marks": [0.0, 0.0, 0.0]}})
	check(fu.get("ok", false) and not fu.get("in_order", true) and float(fu.score) < 0.5 and str(fu.stage) == "condensation",
		"merged out of order: Fusion scores low; then Condensation")
	# A late mistake: the pill cracks and the whole batch is lost.
	var g1: int = c.inventory.count(ginseng)
	var m1: int = c.inventory.count(moss)
	var cr := Game.submit({"type": "refine_input", "step": "condensation", "value": {"offset": 0.5}})
	check(cr.get("cracked", false) and c.inventory.count(ginseng) == g1 - 1 and c.inventory.count(moss) == m1 - 2 and c.inventory.count("healing_pill") == 0
		and Game.crafting.refine_session(c).is_empty(), "condensed too late: the pill cracks, the batch is lost, nothing made")
	# Early only weakens: the pill is made, the screen scores low.
	Game.submit({"type": "start_refine", "recipe": r, "count": 1, "array": "water"})
	for i in 2: Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": i, "held": 0.95, "taps": 3}})
	Game.submit({"type": "refine_input", "step": "fusion", "value": {"order": [0, 1], "marks": [0.0, 0.0, 0.0]}})
	var weak := Game.submit({"type": "refine_input", "step": "condensation", "value": {"offset": -0.5}})
	check(weak.get("ok", false) and float(weak.step_score) < 0.5 and float(weak.step_score) >= 0.2 and c.inventory.count("healing_pill") >= 1,
		"condensed early: a weak pill, but a pill")
	# Putting out the fire: the herbs already in it are lost, the rest stay.
	give.call(r, 1)
	var g2: int = c.inventory.count(ginseng)
	var m2: int = c.inventory.count(moss)
	Game.submit({"type": "start_refine", "recipe": r, "count": 1})
	Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": 0, "held": 0.9}})
	var out := Game.submit({"type": "cancel_refine"})
	check(out.get("ok", false) and c.inventory.count(ginseng) == g2 - 1 and c.inventory.count(moss) == m2 and Game.crafting.refine_session(c).is_empty(),
		"put out mid-refine: the extracted herb is lost, the rest kept")
	# A liquid has no Condensation: it is done at Fusion.
	c.inventory.bag.fill(null)
	give.call("riverreed_draught", 1)
	var lq := Game.submit({"type": "start_refine", "recipe": "riverreed_draught", "count": 1})
	for i in (lq.plan.herbs as Array).size(): Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": i, "held": 0.95, "taps": 3}})
	var ld := Game.submit({"type": "refine_input", "step": "fusion", "value": {"order": lq.plan.order, "marks": [0.0, 0.0, 0.0]}})
	check(ld.get("ok", false) and ld.has("quality") and (ld.scores as Array).size() == 2, "a liquid is done when the essences are one: two screens scored")
	# Spirit Sense on the Ingredients screen: sealed roots the batch would use; a dyed fake shows only to a perceptive eye.
	c.inventory.bag.fill(null)
	Game.inventory.apply_add(c.id, ginseng, 1, "test")
	Game.inventory.apply_add(c.id, moss, 2, "test", {"unappraised": true, "fake": true, "seal": 901})
	var sealed := 0
	var fakes := 0
	for e in Game.crafting.sense_herbs(c, r, 1):
		if str(e.item) == moss:
			sealed += int(e.sealed)
			fakes = int(e.fakes)
	var sees: bool = c.stats.value("crafting_perception") >= float(Game.crafting.furnace_game().get("sense_fakes", 0.04))
	check(sealed >= 1 and (fakes > 0 if sees else fakes == -1), "Spirit Sense counts the sealed roots; perception tells a fake (%d sealed, %d)" % [sealed, fakes])
	# The same hand with the same seed makes the same pills; a clean run scores full marks on every screen.
	var got: Array = []
	var last := {}
	for run in 2:
		c.inventory.bag.fill(null)
		give.call(r, 1)
		Rng.restore(c.id, {}, 777)
		var lp := Game.submit({"type": "start_refine", "recipe": r, "count": 1, "array": "water"})
		for i in (lp.plan.herbs as Array).size():
			Game.submit({"type": "refine_input", "step": "extraction", "value": {"herb": i, "held": 0.95, "taps": (lp.plan.herbs[i].specks as Array).size()}})
		Game.submit({"type": "refine_input", "step": "fusion", "value": {"order": lp.plan.order, "marks": [0.0, 0.0, 0.0]}})
		last = Game.submit({"type": "refine_input", "step": "condensation", "value": {"offset": 0.0}})
		got.append(str(last.get("quality", "")))
	check(got[0] == got[1] and got[0] != "", "the same seed and the same hand make the same pills (%s)" % str(got))
	var full := true
	for x in last.get("scores", []): if not near(float(x), 1.0): full = false
	check(full and (last.get("scores", []) as Array).size() == 3 and got[0] in ["fine", "superior", "perfect", "pill_grain", "pill_halo", "pill_soul"],
		"a clean run scores full marks on all three screens and makes a Fine pill or better (%s)" % got[0])
	# The page plays the same screens: a steady hand on the fan, the essences tapped in order, the array turned on
	# each mark and the pill condensed on the ring, frame by frame.
	c.inventory.bag.fill(null)
	give.call(r, 1)
	var page = load("res://scripts/ui/pages/crafts_page.gd").new()
	page.page_id = "alchemy"
	page.args = {"tab": r}
	page.setup()
	page.on_action("craft", null)
	check(page.screen == "furnace", "the page: Ingredients, then the Furnace screen")
	page.on_action("light", null)
	check(str(Game.crafting.refine_session(c).get("stage", "")) == "extraction", "the page lights the furnace: Extraction")
	var frames := 0
	while str(Game.crafting.refine_session(c).get("stage", "")) == "extraction" and frames < 3000:
		var rs: Dictionary = Game.crafting.refine_session(c)
		var h: Dictionary = rs.herbs[int(rs.at)]
		page.fanning = float(page.play.get("heat", 0.3)) < page._band_mid(h, float(page.play.get("t", 0.0)) + 0.1)
		for j in (h.specks as Array).size():
			if float(page.play.get("t", -1.0)) > float(h.specks[j].t) + 0.2: page.on_action("speck", j)
		page._tick_furnace(1.0 / 60.0)
		frames += 1
	var rs2: Dictionary = Game.crafting.refine_session(c)
	check(str(rs2.get("stage", "")) == "fusion" and float(rs2.extraction[0]) > 0.8 and float(rs2.extraction[1]) > 0.8,
		"a steady hand on the fan holds the heat in the band (%s)" % str(rs2.get("extraction", [])))
	page._tick_furnace(1.0 / 60.0)
	for i in rs2.order: page.on_action("orb", int(i))
	var kf: Dictionary = Game.crafting.furnace_game().fusion
	frames = 0
	while str(Game.crafting.refine_session(c).get("stage", "")) == "fusion" and frames < 1000:
		var at: int = (page.play.get("offs", []) as Array).size()
		if at < rs2.marks.size() and float(page.play.get("t", -1.0)) / float(kf.seconds) >= float(rs2.marks[at]): page._hot("turn")
		page._tick_furnace(1.0 / 60.0)
		frames += 1
	var rs3: Dictionary = Game.crafting.refine_session(c)
	check(str(rs3.get("stage", "")) == "condensation" and float(rs3.fusion) > 0.85, "merged in order, the array turned on its marks (%.2f)" % float(rs3.get("fusion", 0.0)))
	var kc: Dictionary = Game.crafting.furnace_game().condensation
	frames = 0
	while not Game.crafting.refine_session(c).is_empty() and frames < 1000:
		if float(page.play.get("t", -1.0)) >= float(kc.seconds): page._hot("condense")
		else: page._tick_furnace(1.0 / 60.0)
		frames += 1
	check(Game.crafting.refine_session(c).is_empty() and c.inventory.count(r) >= 1 and page.screen == "ingredients",
		"condensed on the ring: the pill is made and the page is back at Ingredients")
	page.free()
	c.inventory.furnace = furnace_was
	c.inventory.bag.fill(null)

## V9e3 · the Cloud Herb Terraces and the ten-thousand-year tier (S45, Part 8, v1.1): each sect's disciples gather for
## the weekly trial on their own terraces, against the other sect's gatherers; the Verdant Dew Vial ages a herb past a
## thousand years only in an Azure Expanse bed; the Expanse's high ledges grow ten-thousand-year ginseng.
func expanse_herbs_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var sect_was: Dictionary = c.training_sect.duplicate(true)
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var created_was: float = Game.account.created_utc
	var seed_was: int = Game.account.rng_seed
	var over_was: float = Clock.override_utc
	# The Cloud Sect's terraces lie east of the Array Court, herbs on the ground and up the terraces.
	var cm := ContentDB.room("cm_herb_terraces")
	var herbs := 0
	var raised := 0
	for o in cm.get("objects", []):
		if str(o.type) == "herb_patch":
			herbs += 1
			if float(o.get("alt", 0)) > 0.0: raised += 1
	var linked := false
	for e in ContentDB.room("cm_array_court").get("portals", []):
		if str(e.get("type", "")) == "edge" and str(e.get("to", "")) == "cm_herb_terraces": linked = true
	check(str(cm.get("sect", "")) == "cloud_sect" and herbs >= 3 and raised >= 2 and linked, "the Cloud Herb Terraces: east of the Array Court, herbs up the terraces")
	# Each sect's trial on its own terraces; a disciple of neither gathers on the Jade Sect's.
	c.training_sect["id"] = "cloud_sect"
	check(Game.calendar.trial_room(c) == "cm_herb_terraces", "a Cloud Sect disciple's trial is on the Cloud Herb Terraces")
	c.training_sect["id"] = "jade_sect"
	check(Game.calendar.trial_room(c) == "ja_herb_terraces", "a Jade Sect disciple's, on the Jade Sect's")
	c.training_sect["id"] = ""
	check(Game.calendar.trial_room(c) == "ja_herb_terraces", "no sect: the Jade Sect's terraces, open to the valley")
	var origin := 1_700_000_000.0
	Game.account.created_utc = origin
	Game.account.rng_seed = 777
	var gtr := CalendarRules.occurrence(CalendarRules.event("gathering_trial"), 1, 777, origin)
	var jade: Array = Game.calendar.trial_rivals(int(gtr.k), "ja_herb_terraces")
	var cloud: Array = Game.calendar.trial_rivals(int(gtr.k), "cm_herb_terraces")
	check(jade == Game.calendar.trial_rivals(int(gtr.k)) and cloud == Game.calendar.trial_rivals(int(gtr.k), "cm_herb_terraces")
		and cloud.any(func(rv): return "Jade Sect" in str(rv.name)) and jade.any(func(rv): return "Cloud Sect" in str(rv.name)),
		"each terraces has the other sect's gatherers, fixed for the trial (the Jade draw unchanged)")
	# Herbs count only on your own sect's terraces.
	Clock.override_utc = float(gtr.start) + 3600.0
	c.training_sect["id"] = "cloud_sect"
	c.cooldowns.erase("gtrial")
	Game.world.load_room(c, "ja_herb_terraces", "")
	GameEvents.flush()
	Game.calendar._on_gathered({"actor": c.id, "item": "willow_moss", "count": 5})
	check(not c.cooldowns.has("gtrial"), "a Cloud disciple's herbs from the Jade terraces do not count")
	Game.world.load_room(c, "cm_herb_terraces", "")
	GameEvents.flush()
	Game.calendar._on_gathered({"actor": c.id, "item": "willow_moss", "count": 30})
	check(int(c.cooldowns.get("gtrial", {}).get("pts", 0)) == 30 and str(c.cooldowns.gtrial.room) == "cm_herb_terraces" and Game.calendar.trial_rank(c) == 1,
		"on the Cloud terraces they do: thirty herbs lead the Jade Sect's gatherers")
	# The Verdant Dew Vial: past a thousand years only in an Azure Expanse bed.
	check(Game.crafting.dew_age_cap("ja_herb_terraces:bed_0") == 1000 and Game.crafting.dew_age_cap("tp_herders_camp:bed_tp_0") == 10000,
		"the valley holds a herb at a thousand years; the Expanse at ten thousand")
	check(HerbRules.ages().back() == 10000 and HerbRules.older_than("riverreed_ginseng_1000") == ["riverreed_ginseng_10000"],
		"the ginseng line runs to ten thousand years")
	var bed := "tp_herders_camp:bed_tp_0"
	Game.world.load_room(c, "tp_herders_camp", "")
	GameEvents.flush()
	Unlocks.force_unlock(c.id, "herb_garden")
	Game.inventory.apply_add(c.id, "verdant_dew_vial", 1, "test")
	c.crafting["dew"] = {"count": 3, "last": Clock.now_utc()}
	var rec := Game.crafting.bed_record(c, bed)
	rec.herb = "riverreed_ginseng_1000"
	rec.progress = 0.5
	rec.updated = Clock.now_utc()
	rec.grow_s = 3600.0
	var d1 := Game.submit({"type": "use_dew", "bed": bed})
	var d2 := Game.submit({"type": "use_dew", "bed": bed})
	check(str(d1.get("herb", "")) == "riverreed_ginseng_10000" and not d2.get("ok", true) and str(d2.get("reason", "")) == "age_cap"
		and str(Game.crafting.bed_view(c, bed).grade) == "high", "in the herders' high bed the dew ages a thousand-year root to ten thousand, and no further")
	check(Game.crafting.bed_holds(c, bed, "riverreed_ginseng_10000"), "a high bed holds a Mystic-grade root")
	Game.crafting.beds(c).erase(bed)
	Game.inventory.apply_remove(c.id, "verdant_dew_vial", 1, "test")
	# Ten-thousand-year ginseng ripens on the Expanse's high ledges, a Master's pick, guarded.
	var nodes := 0
	for rid in ["rf_snow_ape_ledges", "gc_harpy_roosts"]:
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("item", "")) == "riverreed_ginseng_10000" and str(o.get("rank", "")) == "master" and float(o.get("alt", 0)) >= 150.0 \
					and o.has("guardian") and int(o.get("age", 0)) == 10000:
				nodes += 1
	check(nodes == 2, "two ten-thousand-year ginseng nodes on the Expanse's high ledges, each guarded (%d)" % nodes)
	var valley := 0
	for r in ContentDB.all("rooms"):
		if str(r.get("zone", "")) == "azure_expanse": continue
		for o in r.get("objects", []):
			if str(o.get("item", "")) == "riverreed_ginseng_10000": valley += 1
	check(valley == 0, "none grows in the valley")
	c.training_sect = sect_was
	c.cooldowns = cd_was
	Game.account.created_utc = created_was
	Game.account.rng_seed = seed_was
	Clock.override_utc = over_was
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## V9f1 · S43 rule 15 traversal content: the daily rooftop thief of Market Street and Gate Street, and the Cloud Sect's
## timed Cloud Steps with its weekly board.
func rooftop_routes_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var over_was: float = Clock.override_utc
	var realm_was: String = c.cultivator.realm_key
	if ProgressionRules.realm_index(realm_was) < ProgressionRules.realm_index("qi_kindling_3"): c.cultivator.realm_key = "qi_kindling_3"
	# The route: he waits, runs at his speed (a climb counts half its height), and is gone after the last wait.
	var route := [[0, 700, 0, 1.0], [200, 700, 0, 0.5], [200, 700, 100, 0.0]]
	var p0 := WorldAuthority.chase_point(route, 200.0, 0.5)
	var p1 := WorldAuthority.chase_point(route, 200.0, 1.5)
	var len := WorldAuthority.chase_length(route, 200.0)
	check(near(float(p0.x), 0.0) and not p0.moving and near(float(p1.x), 100.0) and p1.moving and near(len, 1.0 + 1.0 + 0.5 + 0.25),
		"the thief waits, then runs at his pace (%.2f s in all)" % len)
	check(WorldAuthority.chase_point(route, 200.0, len + 0.1).done and not WorldAuthority.chase_point(route, 200.0, len - 0.1).done, "past his last wait he is gone")
	# Every waypoint stands on the street or a named roof at that roof's height.
	for pair in [["sf_market", "thief_sf"], ["ja_gate_street", "thief_ja"]]:
		var rdef := ContentDB.room(str(pair[0]))
		var th: Dictionary = {}
		for o in rdef.get("objects", []):
			if str(o.id) == str(pair[1]): th = o
		var standing := true
		var roofs := 0
		for w in th.get("chase", {}).get("route", []):
			if float(w[2]) <= 0.0: continue
			var on := false
			for sd in rdef.get("surfaces", []):
				var rr: Array = sd.rect
				if near(float(sd.height), float(w[2]), 0.5) and float(w[0]) >= float(rr[0]) and float(w[0]) <= float(rr[0]) + float(rr[2]) \
						and float(w[1]) >= float(rr[1]) and float(w[1]) <= float(rr[1]) + float(rr[3]): on = true
			if on: roofs += 1
			else: standing = false
		check(not th.is_empty() and str(th.get("npc", "")) == "rooftop_thief" and standing and roofs >= 5, "%s: the thief's route runs over %d roof stops, each on a roof" % [pair[0], roofs])
	# Catch him: speak and he bolts; not in the first moment; reach him at his height and the purse is yours.
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	var st: ActorState = Game.actor_state(c.id)
	var th2: Dictionary = Game.room_rt.object_def("thief_sf")
	c.cooldowns.erase("chase_thief_sf")
	st.plane = Vector2(390, 800)
	st.altitude = 0.0
	check(Game.world.object_visible(c, th2) and str(Game.world.query_context(c).get("label", "")) == Tx.t("sim.world.chase"),
		"the thief loiters in the street: Chase! (%s, %s)" % [str(Game.world.object_visible(c, th2)), str(Game.world.query_context(c))])
	var t0 := Game.economy.balance("silver_tael")
	var go := Game.submit({"type": "interact", "object": "thief_sf"})
	check(go.get("ok", false) and Game.world.chases.has(c.id), "speak to him and he bolts")
	Game.world._tick_chase(c, Game.room_rt, st)
	check(Game.world.chases.has(c.id), "standing beside him as he goes does not catch him")
	Game.sim_time += 3.0
	var at3: Dictionary = Game.world.chase_view(c)
	st.plane = Vector2(float(at3.x), float(at3.y))
	st.altitude = 0.0
	Game.world._tick_chase(c, Game.room_rt, st)
	check(Game.world.chases.has(c.id) or float(at3.alt) <= 40.0, "from the street below you cannot lay a hand on him (he is at %d)" % int(at3.alt))
	st.altitude = float(at3.alt)
	Game.world._tick_chase(c, Game.room_rt, st)
	GameEvents.flush()
	check(not Game.world.chases.has(c.id) and Game.economy.balance("silver_tael") == t0 + 150 and Game.world.chase_done_today(c, "thief_sf")
		and not Game.world.object_visible(c, th2), "on his roof at his height: caught, 150 taels, and he is gone for the day")
	var again := Game.submit({"type": "interact", "object": "thief_sf"})
	check(not again.get("ok", false) and not Game.world.chases.has(c.id), "one chase a street a day (%s)" % str(again))
	# The next day he runs again; left alone, he is over the wall and away with nothing paid.
	Clock.override_utc = Clock.now_utc() + 86400.0
	st.plane = Vector2(390, 800)
	st.altitude = 0.0
	var t1 := Game.economy.balance("silver_tael")
	Game.submit({"type": "interact", "object": "thief_sf"})
	Game.sim_time += WorldAuthority.chase_length(th2.chase.route, float(th2.chase.speed)) + 1.0
	st.plane = Vector2(100, 900)
	Game.world._tick_chase(c, Game.room_rt, st)
	check(not Game.world.chases.has(c.id) and Game.economy.balance("silver_tael") == t1 and Game.world.chase_done_today(c, "thief_sf"),
		"too slow: he is over the far wall, nothing paid")
	# The Cloud Steps: a timed climb; the week's board, medals once each, and the top three paid once a week.
	var cs := ContentDB.room("cm_cliff_stair")
	var stone: Dictionary = {}
	for o in cs.get("objects", []):
		if str(o.type) == "route_stone": stone = o
	var rt: Dictionary = stone.get("route", {})
	var tops := 0
	for sd in cs.get("surfaces", []):
		if near(float(sd.height), 300.0, 0.5): tops += 1
	check(not rt.is_empty() and tops >= 1 and near(float(rt.finish.alt), 300.0, 0.5), "the Cliff Stair climbs to a 300 ledge, the Cloud Steps' bell at the top")
	var wk: int = Game.calendar.rank_week()
	check(Game.world.route_board(rt, wk) == Game.world.route_board(rt, wk) and Game.world.route_board(rt, wk).size() == (rt.rivals as Array).size(),
		"the week's board is the same on every device")
	c.cooldowns.erase("route_cloud_steps")
	var contrib0 := int(c.training_sect.get("contribution", 0))
	var slow := Game.world.finish_route(c, rt, 30.0)
	check(str(slow.medal) == "" and int(slow.rank) >= 1, "a slow run: no medal")
	# Under the gold par and under the fastest a rival can draw (`rival_s`), whatever the account's seed drew this week.
	var quick := minf(float(rt.pars.gold), float(rt.rival_s[0])) - 0.5
	var fast := Game.world.finish_route(c, rt, quick)
	check(str(fast.medal) == "gold" and int(fast.rank) == 1 and near(float(fast.best), quick)
		and (Game.world.route_record(c, "cloud_steps").medals as Array).size() == 3, "inside the gold par: first place, and all three medals' rewards")
	var contrib1 := int(c.training_sect.get("contribution", 0))
	Game.world.finish_route(c, rt, quick - 0.5)
	check(int(c.training_sect.get("contribution", 0)) == contrib1, "medals and the week's reward pay once")
	# Run it for real: touch the stone, stand at the bell.
	c.cultivator.realm_key = "bone_forging_3" if ProgressionRules.realm_index(c.cultivator.realm_key) < ProgressionRules.realm_index("bone_forging_3") else c.cultivator.realm_key
	Game.world.load_room(c, "cm_cliff_stair", "")
	GameEvents.flush()
	st = Game.actor_state(c.id)
	st.plane = Vector2(260, 830)
	st.altitude = 0.0
	var begun := Game.submit({"type": "interact", "object": "cloud_steps_stone"})
	var t_start: float = Game.sim_time
	Game.sim_time += 11.5
	st.plane = Vector2(float(rt.finish.at[0]), float(rt.finish.at[1]))
	st.altitude = 300.0
	var got: Array = []
	GameEvents.subscribe("route_finished", func(pp): got.append(pp), 200)
	Game.world._tick_run(c, Game.room_rt, st)
	GameEvents.flush()
	check(begun.get("ok", false) and got.size() == 1 and near(float(got[0].seconds), 11.5, 0.11) and got[0].finished, "at the bell: the run is timed (%s)" % str(got))
	st.plane = Vector2(260, 830)
	st.altitude = 0.0
	Game.submit({"type": "interact", "object": "cloud_steps_stone"})
	Game.sim_time += float(rt.limit_s) + 1.0
	got.clear()
	Game.world._tick_run(c, Game.room_rt, st)
	GameEvents.flush()
	check(got.size() == 1 and not got[0].finished and not Game.world.runs.has(c.id), "the incense burns down: the run does not count")
	c.cooldowns = cd_was
	c.cultivator.realm_key = realm_was
	Clock.override_utc = over_was
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## V9f2 · the v1.1 ice traction rule, and mounts in a vertical world (S43 rule 12): a ground mount jumps with its
## species impulse and cannot Wall-Step; any mount puts you down for a ladder or rope and takes you back at the landing.
## S28 v1.2 · Presence (Will Manifest): the Pressure contest against weaker foes, clashes with a foe's Presence
## (resolved by the S12 Pressure rule: the harder push presses the other side), levels, Soul upkeep, the requirement.
func field_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	check(near(CombatRules.pressure_loss(150.0, 100.0), 0.125) and near(CombatRules.pressure_loss(90.0, 100.0), 0.0)
		and near(CombatRules.pressure_loss(1000.0, 100.0), 0.5), "the Pressure rule: min(50%, 25% x (Pressure / Will - 1)), nothing under the Will")
	check(near(FieldRules.enemy_will(85, "normal"), 90.0) and near(FieldRules.enemy_will(90, "dungeon_boss"), 95.0 * 1.3)
		and near(FieldRules.enemy_will(85, "normal", true), 90.0 * 1.15), "a foe's Will is 5 + its Level, x1.15 for elites and x1.3 for bosses")
	check(near(FieldRules.pressure(90, 5), 95.0 * 1.3) and near(FieldRules.pressure(90, 0), 0.0) and near(FieldRules.pressure(90, 1, 10.0), 95.0 * 1.06 + 10.0),
		"Pressure = (5 + Level) x (1 + 6% a Presence level) + the pressure stat; no Presence, no Pressure")
	var k := FieldRules.clash(150.0, 90.0, 120.0, 100.0)
	check(near(k.loss_a, 0.0) and near(k.loss_b, CombatRules.pressure_loss(150.0, 120.0)) and near(k.boundary, 150.0 / 270.0),
		"two Presences meet: the harder push presses the other side's own Presence by the Pressure rule, and holds %.0f%% of the ground" % (100.0 * k.boundary))
	var k2 := FieldRules.clash(100.0, 90.0, 160.0, 100.0)
	check(near(k2.loss_a, CombatRules.pressure_loss(160.0, 100.0)) and near(k2.loss_b, 0.0), "and the weaker side is the one pressed, never both")
	var k3 := FieldRules.clash(0.0, 90.0, 120.0, 100.0)
	check(near(k3.loss_a, CombatRules.pressure_loss(120.0, 90.0)), "with no Presence held, the Will alone stands against a foe's")
	check(FieldRules.level_for(0.0) == 1 and FieldRules.level_for(450.0) == 5 and FieldRules.level_for(449.0) == 4 and FieldRules.level_for(1e6) == 10,
		"Presence levels 1-10 by experience (level 5 at 450)")
	# In a room: Will Manifest 1 and the Presence unlocked.
	var back := str(c.position.get("room", "lf_village"))
	Game.world.apply_teleport(c.id, "bg_whispering_bamboo")
	var realm0: String = c.cultivator.realm_key
	var fp0: Dictionary = c.cultivator.field_powers.duplicate(true)
	c.cultivator.realm_key = "will_manifest_1"
	Game.combat.refresh_stats(c.id)
	var locked := Game.submit({"type": "toggle_presence"})
	check(not locked.get("ok", true) and str(locked.get("reason", "")) == "locked", "no Presence before it is unlocked")
	Unlocks.force_unlock(c.id, "presence")
	c.pools.soul = c.pools.max_soul
	Game.room_rt.enemies.clear()
	var here: Vector2 = Game.actor_state(c.id).plane
	var weak: EnemyState = Game.enemies.spawn_at("star_jellyfish", here + Vector2(120, 0), 70)
	var far: EnemyState = Game.enemies.spawn_at("star_jellyfish", here + Vector2(900, 0), 70)
	var strong: EnemyState = Game.enemies.spawn_at("star_jellyfish", here + Vector2(150, 20), 95)
	check(Game.submit({"type": "toggle_presence"}).get("ok", false) and Game.field.is_on(c.id), "hold the Presence")
	var soul0: float = c.pools.soul
	Game.field.tick(0.5)
	var p: float = Game.field.pressure_of(c)
	check(near(FieldAuthority.enemy_loss(weak), CombatRules.pressure_loss(p, FieldRules.enemy_will(70, "normal")), 0.001) and FieldAuthority.enemy_loss(weak) > 0.0,
		"a weaker foe in reach is pressed: %.1f%% slower and weaker" % (100.0 * FieldAuthority.enemy_loss(weak)))
	check(near(FieldAuthority.enemy_loss(far), 0.0) and near(FieldAuthority.enemy_loss(strong), 0.0), "not one out of reach, nor one whose Will stands above the Pressure")
	check(c.pools.soul < soul0 and near(soul0 - c.pools.soul, c.pools.max_soul * 0.0025 * 0.5, 0.01), "holding it costs Soul (0.25% a second)")
	check(Game.field.presence_xp(c) > 0.0, "and trains it while it presses something")
	# A foe with a Presence of its own: the two meet and the stronger one presses.
	strong.def = strong.def.duplicate()
	strong.def["presence"] = 10
	strong.level = 120   # well above the test character's trained Will
	strong.role = "dungeon_boss"
	Game.field.tick(0.1)
	var cl: Dictionary = Game.field.clash_of(c.id)
	var foe_p := FieldAuthority.enemy_pressure(strong)
	var want := CombatRules.pressure_loss(foe_p, maxf(c.stats.value("will"), p))
	check(not cl.is_empty() and str(cl.winner) == "foe" and near(Game.field.loss_of(c.id), want, 0.001),
		"a boss's stronger Presence meets yours at a boundary and presses you (%.1f%%)" % (100.0 * Game.field.loss_of(c.id)))
	check(near(Game.combat.move_factor(c.id), 1.0 - want, 0.01) or Game.combat.move_factor(c.id) < 1.0, "pressed, you move slower")
	Game.submit({"type": "toggle_presence", "on": false})
	Game.field.tick(0.1)
	check(near(FieldAuthority.enemy_loss(weak), 0.0) and Game.field.clash_of(c.id).is_empty() and Game.field.loss_of(c.id) >= want - 0.001,
		"let go: the weak foe is free, and the boss now presses your Will alone, at least as hard")
	# Levels and the Sphere Lord requirement (Presence level 5).
	var req := {"all": [{"kind": "presence_level_at_least", "value": 5}]}
	check(not RequirementRules.passes(req, Game.ctx(c)), "Presence level 5 is not met at level %d" % Game.field.presence_level(c))
	Game.field.apply_presence_xp(c.id, 450.0, "test")
	check(Game.field.presence_level(c) >= 5 and RequirementRules.passes(req, Game.ctx(c)), "trained to level %d, it is" % Game.field.presence_level(c))
	# Out of Soul, it falls away.
	Game.submit({"type": "toggle_presence", "on": true})
	c.pools.soul = 0.1
	Game.field.tick(0.5)
	check(not Game.field.is_on(c.id), "with no Soul left the Presence falls away")
	Game.room_rt.enemies.clear()
	c.cultivator.unlocked.erase("presence")
	c.cultivator.field_powers = fp0
	c.cultivator.realm_key = realm0
	Game.combat.refresh_stats(c.id)
	c.pools.soul = c.pools.max_soul
	Game.world.apply_teleport(c.id, back)

## S28 v1.2 · the Hollow Tide: capped under half in the valley, free in the Lantern Star Field; at 50% techniques cost more
## and Composure drains; at 100% the body is lost for a moment, allies turn, and the meter falls back to 80.
func hollow_tide_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	var events: Array = []
	var grab := func(n, p): if str(n) == "hollow_seizure": events.append(p)
	GameEvents.event.connect(grab)
	var ward: float = c.stats.value("hollow_ward")
	var per := 1.0 - clampf(ward, 0.0, 0.8)   # the Hollow Ward keeps part of every gain out
	Game.world.apply_teleport(c.id, "bg_whispering_bamboo")
	c.pools.hollowing = 0.0
	Game.combat.apply_resource_change(c.id, "hollowing", 200.0, "test")
	check(near(c.pools.hollowing, 49.0), "in the valley the Hollowing stops at 49%% (%.0f)" % c.pools.hollowing)
	Game.world.apply_teleport(c.id, "dr_jellyfish_shallows")
	check(near(Game.combat.hollow_cap(), 100.0), "the Lantern Star Field lets it fill")
	c.pools.hollowing = 0.0
	Game.combat.apply_resource_change(c.id, "hollowing", 60.0 / per, "test")
	check(near(c.pools.hollowing, 60.0, 0.5) and CombatAuthority.hollow_burdened(c), "over half (%.0f%%) the burden begins" % c.pools.hollowing)
	var tdef := {}
	for t in c.cultivator.techniques_known:
		tdef = ContentDB.entry("techniques", str(t))
		if float(tdef.get("qi_cost", 0)) > 0: break
	var heavy: float = Game.combat.technique_cost(c, tdef)
	c.pools.hollowing = 10.0
	var light: float = Game.combat.technique_cost(c, tdef)
	check(tdef.is_empty() or near(heavy, light * 1.25, 0.01), "techniques cost 25%% more under the burden (%.1f / %.1f)" % [heavy, light])
	c.pools.hollowing = 60.0
	var comp_ok := Unlocks.is_unlocked(c.id, "composure")
	c.pools.composure = 50.0
	Game.combat._tick_pools(c, 1.0)
	check(not comp_ok or c.pools.composure < 50.0, "and Composure drains instead of recovering (%.1f)" % c.pools.composure)
	# At full: the seizure.
	var st: ActorState = Game.actor_state(c.id)
	Game.room_rt.enemies.clear()
	var ally: EnemyState = Game.enemies.spawn_at("star_jellyfish", st.plane + Vector2(80, 0), 82, {"team": "ally"})
	events.clear()
	Game.combat.apply_resource_change(c.id, "hollowing", 200.0, "test")
	GameEvents.flush()
	check(c.pools.has_status("hollow_seizure") and c.pools.blocked("move") and c.pools.blocked("attack") and c.pools.blocked("technique"),
		"at 100% the Tide takes the body: no moving, striking or casting")
	check(ally != null and ally.team == "enemy" and events.size() == 1 and int(events[0].get("turned", 0)) == 1, "the ally beside you turns on you")
	check(near(c.pools.hollowing, 80.0), "and the meter falls back to 80%% (%.0f)" % c.pools.hollowing)
	check("hollow_touched" in c.cultivator.physiques, "surviving it awakens Hollow-Touched")
	for i in 22: Game.combat.tick(0.5)
	check(ally.team == "ally" and not c.pools.has_status("hollow_seizure"), "ten seconds on, the ally is itself again and the body is yours")
	# Cleansing.
	var h0: float = c.pools.hollowing
	Game.apply_effects(c.id, [{"kind": "cleanse_hollowing", "amount": 40}], "test")
	check(near(c.pools.hollowing, h0 - 40.0, 0.5), "a cleansing draws 40 out (%.0f -> %.0f)" % [h0, c.pools.hollowing])
	# A lit lantern: the harbour draws it out four times as fast.
	Game.world.apply_teleport(c.id, "lh_harbor_market")
	c.pools.hollowing = 40.0
	c.cultivator.meditating = false
	Game.combat._tick_pools(c, 60.0)
	check(near(c.pools.hollowing, 36.0, 0.2), "under a lit lantern a minute takes 4 points, not 1 (%.1f)" % c.pools.hollowing)
	GameEvents.event.disconnect(grab)
	Game.room_rt.enemies.clear()
	c.pools.statuses.clear()
	c.pools.hollowing = 0.0
	c.cultivator.physiques.erase("hollow_touched")
	Game.combat.refresh_stats(c.id)
	Game.world.apply_teleport(c.id, back)

## S50 Keeping Post (V10a, docs/idle_gathering_design.md): the formulas with their worked examples, then a post
## taken, settled, filled to capacity, sent to the Storehouse; incense, sewing, migration and the save.
func post_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	check(PostRules.xp_to_next(1) == 7.0 and PostRules.xp_to_next(10) == 1645.0 and PostRules.xp_to_next(30) == 169535.0,
		"craft EXP to the next level: 7 at 1, 1,645 at 10, 169,535 at 30")
	check(PostRules.level_for(0.0) == 1 and PostRules.level_for(7.0) == 2 and PostRules.level_for(3663.0) == 10 and PostRules.level_for(3662.0) == 9,
		"levels come from total EXP (level 10 at 3,663)")
	var f := PostRules.finesse(6.0, 10.0, 1)
	check(near(f, 81.1, 0.005), "the worked example: a power-6 pick, attribute 10, level 1 gives Finesse %.1f (about 81)" % f)
	var y := PostRules.yield_of(81.1, 25.0)
	check(near(float(y.chance), pow(81.1 / 250.0, 0.4), 0.001) and near(float(y.abundance), 1.0), "Chance = (Finesse / (10 x Toughness))^0.4: %.0f%% on copper" % (100.0 * float(y.chance)))
	check(near(float(PostRules.yield_of(4.9, 25.0).chance), 0.0) and near(float(PostRules.yield_of(250.0, 25.0).chance), 1.0),
		"no chance below 2.5% of the full mark; full at ten times the Toughness")
	var ab := PostRules.yield_of(16.0 * 250.0, 25.0)
	check(near(float(ab.abundance), 2.0) and near(float(PostRules.yield_of(81.0 * 250.0, 25.0).abundance), 3.0)
		and near(float(PostRules.yield_of(81.0 * 250.0, 25.0, 0.1).abundance), 4.0),
		"past full, Abundance = floor(r^(0.25 + Flow)): 2 at sixteen times the mark, 3 at 81 times, 4 there with the most Flow")
	check(near(float(PostRules.yield_of(81.0, 25.0, 0.0, 0.5).windfall), 1.9375), "Windfall chains up to four extra: 1 + w + w^2 + w^3 + w^4")
	check(near(PostRules.swing_seconds(3.0), 14.4) and near(PostRules.swing_seconds(10.0), 6.0) and near(PostRules.swing_seconds(3.0, 100.0), 7.2),
		"a swing takes 6 x (1 + (10 - speed) / 5) s, less with speed bonuses")
	check(near(PostRules.diligence("craft"), 0.52) and near(PostRules.diligence("martial"), 0.40) and near(PostRules.diligence("craft", -90.0), 0.01),
		"Diligence: 52% for crafts, 40% for the Vigil, never below 1%")
	check(near(PostRules.capacity(PostRules.compartment_cap(0)), 40.0) and near(PostRules.capacity(PostRules.compartment_cap(1)), 100.0)
		and near(PostRules.capacity(PostRules.compartment_cap(13)), 140000.0), "a pouch holds four compartments: 10 each unsewn, 25 at the first tier, 35,000 at the last")
	var sa := PostRules.settle_amounts(5.0, {"copper_ore": 10.0, "willow_moss": 4.0}, {"copper_ore": "ore", "willow_moss": "herb"}, {"ore": 30.0, "herb": 0.0}, {"ore": 40.0, "herb": 40.0})
	check(near(float(sa.items.copper_ore), 10.0) and near(float(sa.items.willow_moss), 20.0) and near(float(sa.full.get("ore", -1.0)), 1.0) and not sa.full.has("herb"),
		"a settle stops each category when its pouch fills (ore after an hour) and not the others")
	var r1 := RandomNumberGenerator.new()
	r1.seed = 7
	var r2 := RandomNumberGenerator.new()
	r2.seed = 7
	check(PostRules.draw(12.4, r1) == PostRules.draw(12.4, r2) and PostRules.draw(3.0, null) == 3, "whole numbers are drawn from the seed")
	var r := PostRules.rates(81.1, [{"item": "copper_ore", "toughness": 25.0, "exp": 12.0, "weight": 1.0}], 3.0, 0.52)
	check(float(r.items.copper_ore) >= 70.0 and float(r.items.copper_ore) <= 100.0, "a new delver's copper post: %.0f ore an hour (70-100)" % float(r.items.copper_ore))
	check(3663.0 / float(r.exp_h) >= 3.0 and 3663.0 / float(r.exp_h) <= 6.0, "and craft level 10 in %.1f hours of posts (3-6)" % (3663.0 / float(r.exp_h)))
	# In a room: the Reed Shallows' glowfly swarm.
	var back := str(c.position.get("room", "lf_village"))
	var posts0: Dictionary = c.posts.duplicate(true)
	var store0: Dictionary = Game.account.storehouse.duplicate()
	for u in ["keeping_post", "insect_netting", "herb_gathering", "pouch_sewing"]: Unlocks.force_unlock(c.id, u)
	Game.world.apply_teleport(c.id, "lf_reed_shallows")
	var swarm: Dictionary = Game.room_rt.object_def("swarm_glowfly")
	check(not swarm.is_empty() and Game.posts.craft_of_object(swarm) == "netting", "the Reed Shallows have a glowfly swarm to net")
	var far := Game.submit({"type": "take_post", "object": "swarm_glowfly"})
	Game.actor_state(c.id).plane = Vector2(float(swarm.at[0]), float(swarm.at[1]))
	var took := Game.submit({"type": "take_post", "object": "swarm_glowfly"})
	check(took.get("ok", false) and Game.posts.at_post(c) and bool(Game.posts.post_of(c).get("paused", false)),
		"keep post at the swarm (paused while this character is played)")
	var gated := Game.posts.rates_at(c, {"type": "insect_swarm", "outputs": [{"item": "jade_scarab", "weight": 1.0}]})
	check((gated.get("outputs", []) as Array).is_empty(), "a jade scarab swarm yields nothing below Netting 12")
	# Switched away for two hours.
	Game.posts.post_of(c)["paused"] = false
	Game.posts.post_of(c)["since"] = Clock.now_utc() - 7200.0
	var xp0: float = Game.posts.xp(c, "netting")
	var led: Dictionary = Game.posts.settle_post(c).get("ledger", {})
	check(near(float(led.get("hours", 0.0)), 2.0, 0.01) and int(led.get("items", {}).get("glowfly", 0)) > 0 and Game.posts.xp(c, "netting") > xp0,
		"two hours away: %d glowflies and %.0f Netting EXP" % [int(led.get("items", {}).get("glowfly", 0)), Game.posts.xp(c, "netting") - xp0])
	Game.posts.post_of(c)["since"] = Clock.now_utc() - 3600.0 * 200.0
	var xp1: float = Game.posts.xp(c, "netting")
	var led2: Dictionary = Game.posts.settle_post(c).get("ledger", {})
	check(led2.get("full", {}).has("insect") and Game.posts.held(c, "insect") <= Game.posts.capacity(c, "insect") + 1.0 and Game.posts.xp(c, "netting") > xp1,
		"two hundred hours: the insect pouch filled (%d of %d) and stopped; the EXP went on" % [int(Game.posts.held(c, "insect")), int(Game.posts.capacity(c, "insect"))])
	Game.posts.post_of(c)["since"] = Clock.now_utc() + 50000.0
	var back_clock := Game.posts.settle_post(c)
	check(back_clock.get("clock_moved_back", false), "a clock moved back settles nothing")
	var held_n := int(Game.posts.held(c, "insect"))
	Game.submit({"type": "send_to_storehouse", "character": c.id})
	check(int(Game.account.storehouse.get("glowfly", 0)) >= held_n and int(Game.posts.held(c, "insect")) == 0, "the pouch empties into the Storehouse")
	var w := Game.submit({"type": "withdraw_storehouse", "item": "glowfly", "count": 3})
	check(not w.get("ok", true), "the Storehouse opens only in a town or a safe room")
	# Hand harvesting trains the craft.
	var dx0: float = Game.posts.xp(c, "delving")
	Unlocks.force_unlock(c.id, "mining")
	Game.posts.apply_hand_harvest(c.id, "copper_ore", 1)
	check(near(Game.posts.xp(c, "delving") - dx0, 12.0), "a copper ore dug by hand gives 12 Delving EXP")
	# Hour Incense burned at another character's post.
	var other := GameCharacter.new()
	other.id = "c12"
	other.slot = 12
	other.name = "Post Tester"
	other.position.room = "lf_reed_shallows"
	Game.characters["c12"] = other
	other.posts = {"post": {"kind": "craft", "craft": "netting", "room": "lf_reed_shallows", "object": "swarm_glowfly", "since": Clock.now_utc(), "paused": false},
		"crafts": {"netting": {"xp": 0.0}}, "pouch": {}}
	Unlocks.force_unlock("c12", "insect_netting")
	Game.inventory.apply_add(c.id, "hour_incense_2", 1, "test")
	var inc := Game.submit({"type": "burn_incense", "character": "c12", "item": "hour_incense_2"})
	check(inc.get("ok", false) and near(float(inc.get("hours", 0.0)), 2.0) and Game.posts.xp(other, "netting") > 0.0,
		"Hour Incense gives a post two hours of work at once")
	var rows: Array = Game.posts.roll_call()
	check(rows.any(func(x): return str(x.id) == "c12" and not (x.post as Dictionary).is_empty()), "the Roll-Call lists every character and its post")
	Game.posts.post_of(other)["since"] = Clock.now_utc() - 3600.0
	var all := Game.submit({"type": "settle_all"})
	check(all.get("ok", false) and int(Game.posts.held(other, "insect")) == 0, "Settle all sends every other post's haul to the Storehouse")
	# Migration: an old idle Gather task becomes a post.
	other.posts = {}
	other.idle_task = {"task": "gather", "room": "lf_reed_shallows", "item": "willow_moss", "started_utc": Clock.now_utc() - 600.0}
	Game.posts.migrate_idle(other)
	check(str(Game.posts.post_of(other).get("craft", "")) == "foraging" and other.idle_task.is_empty(), "an old idle Gather task becomes a Foraging post")
	Game.characters.erase("c12")
	# Sewing.
	Game.economy.apply_currency("silver_tael", 500, "test")
	Game.inventory.apply_add(c.id, "cloth", 2, "test")
	var tier0 := int(Game.posts.pouch(c, "ore").get("tier", 0))
	var sew := Game.submit({"type": "sew_pouch", "category": "ore"})
	check(sew.get("ok", false) and int(Game.posts.pouch(c, "ore").tier) == tier0 + 1, "Tailor Xun sews the ore pouch a tier deeper")
	# The save keeps posts and the Storehouse.
	var snap: Dictionary = c.snapshot()
	var twin := GameCharacter.new()
	twin.restore(snap)
	check(twin.posts.get("crafts", {}).get("netting", {}).get("xp", -1.0) == c.posts.crafts.netting.xp, "a save keeps craft EXP and posts")
	var acc := AccountState.new()
	acc.restore(Game.account.snapshot())
	check(int(acc.storehouse.get("glowfly", 0)) == int(Game.account.storehouse.get("glowfly", 0)), "and the account keeps its Storehouse")
	c.posts = posts0
	Game.account.storehouse = store0
	Game.world.apply_teleport(c.id, back)

## S50 V10b the Vigil: kills an hour from the two caps, Sweep, survivability on provisions, a settle with loot,
## coins and realm progress, Bestiary Leaves and their bonus, migration of the old idle Hunt.
func vigil_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var kp := PostRules.kills_per_hour(8.0, 12.0, 1.0, 0.7, 30.0, 40.0, 0.9)
	check(near(float(kp.spawn_h), 3600.0 * 8.0 / 12.1) and near(float(kp.fighter_h), 3600.0 / (1.0 + 0.7 * maxf((30.0 / 40.0 + 0.52) / 0.9, 1.0)))
		and near(float(kp.kills_h), floorf(minf(float(kp.spawn_h), float(kp.fighter_h)))), "kills an hour: the lesser of the spawn cap and the fighter's pace")
	check(int(PostRules.sweep(100.0, 60.0).tier) == 0 and int(PostRules.sweep(800.0, 100.0).tier) == 3 and near(float(PostRules.sweep(800.0, 100.0).mult), 1.5),
		"Sweep: tier floor(log2(max hit / HP)) from twice the HP; tier 3 fells half again as many")
	var sv0 := PostRules.survivability(1000.0, 500.0, 600.0, 250.0, 0, 10.0)
	var sv1 := PostRules.survivability(1000.0, 2000.0, 0.0, 250.0, 100, 10.0)
	var sv2 := PostRules.survivability(1000.0, 10000.0, 0.0, 250.0, 0, 10.0)
	check(near(float(sv0.alive), 1.0) and near(float(sv1.alive), 1.0) and int(sv1.food_used) == 80 and float(sv2.alive) < 0.5,
		"survivability: regeneration or provisions keep the fight going; with neither the fighter keeps falling (%.0f%%)" % (100.0 * float(sv2.alive)))
	var back := str(c.position.get("room", "lf_village"))
	var posts0: Dictionary = c.posts.duplicate(true)
	var leaves0: Dictionary = Game.account.leaves.duplicate()
	Unlocks.force_unlock(c.id, "keeping_post")
	Game.world.apply_teleport(c.id, "bg_whispering_bamboo")
	var pr: Dictionary = Game.posts.vigil_profile(c, "bg_whispering_bamboo")
	print("  vigil at bg_whispering_bamboo, Lv %d: %.0f kills/h (spawn %.0f, blade %.0f), hit %.0f%%, avg %.0f vs HP %.0f, sweep %d, taken %.0f/h, regen %.0f/h"
		% [ProgressionRules.level(c), float(pr.kills_h), float(pr.spawn_h), float(pr.fighter_h), 100.0 * float(pr.hit), float(pr.avg_hit), float(pr.hp),
		int(pr.sweep_tier), float(pr.dmg_h), float(pr.regen_h)])
	check(not pr.is_empty() and float(pr.kills_h) > 0.0 and near(float(pr.diligence), 0.40), "a Vigil in the Whispering Bamboo hunts at 40% Martial Diligence")
	check(not Game.posts.vigil_profile(c, "lf_village").size() > 0 or not Game.posts.vigil_allowed("lf_village"), "no Vigil where nothing may be hunted")
	var took := Game.submit({"type": "take_vigil"})
	check(took.get("ok", false) and str(Game.posts.post_of(c).get("kind", "")) == "vigil", "keep vigil in the room")
	Game.posts.post_of(c)["paused"] = false
	Game.posts.post_of(c)["since"] = Clock.now_utc() - 4.0 * 3600.0
	var led: Dictionary = Game.posts.settle_post(c).get("ledger", {})
	check(int(led.get("kills", 0)) > 0 and float(led.get("qp", 0.0)) > 0.0, "four hours of Vigil: %d beasts, %d kinds of loot, realm progress" % [int(led.get("kills", 0)), (led.get("items", {}) as Dictionary).size()])
	var kind := Game.posts.leaf_kind("bamboo_monkey")
	var b0 := Game.posts.leaf_bonus(kind)
	Game.posts.apply_leaf(c.id, "bamboo_monkey", 5)
	check(Game.posts.leaf_tier("bamboo_monkey") >= 2 and Game.posts.leaf_bonus(kind) > b0, "five Bamboo Monkey leaves: tier %d, +%.0f%% %s" % [Game.posts.leaf_tier("bamboo_monkey"), Game.posts.leaf_bonus(kind), kind])
	var other := GameCharacter.new()
	other.id = "c12"
	other.idle_task = {"task": "hunt", "room": "bg_whispering_bamboo", "started_utc": Clock.now_utc() - 600.0}
	Game.posts.migrate_idle(other)
	check(str(Game.posts.post_of(other).get("kind", "")) == "vigil" and other.idle_task.is_empty(), "an old idle Hunt task becomes a Vigil")
	var no_hunt := Game.submit({"type": "set_idle_task", "task": {"task": "hunt"}})
	check(not no_hunt.get("ok", true), "with Keeping Post, hunting while away is a Vigil, not an idle task")
	c.posts = posts0
	Game.account.leaves = leaves0
	Game.world.apply_teleport(c.id, back)

## S50 V10c: Beast Snaring, Ancestral Rites with Spirit Wisps and Post Vows, and the Apprentice Bench.
func station_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	check(near(PostRules.snare_catch(40.0, 35.0, 10.0), 10.0 * pow(40.0 / 35.0, 0.25)) and near(PostRules.snare_catch(30.0, 35.0, 10.0), 0.0),
		"a snare holds nothing when Finesse is under the beast's Toughness, and (F / T)^0.25 more above it")
	check(near(PostRules.rite_charge_rate(4.0, 1), 6.0 / (5.7 - 0.2 * pow(4.0, 1.3) - 1.0 / 40.0)) and near(PostRules.rite_charge_cap(1), 75.0),
		"rite charge: 6 / max(5.7 - 0.2 x speed^1.3 - level/40, 0.57) an hour, up to 50 + 25 a tablet tier")
	var rr := PostRules.rite_result(100.0, 25.0, 50.0)
	check(int(rr.wave) >= 1 and float(rr.wisps) > 5.0 and near(PostRules.bench_rate(100.0), 36.0), "an altar defence calls wisps by the wave held; an apprentice makes 36 hemp cord an hour")
	var back := str(c.position.get("room", "lf_village"))
	var posts0: Dictionary = c.posts.duplicate(true)
	var vows0: Dictionary = Game.account.post_vows.duplicate()
	for u in ["keeping_post", "beast_snaring", "ancestral_rites", "apprentice_bench"]: Unlocks.force_unlock(c.id, u)
	if c.inventory.count("hemp_snare_kit") <= 0: Game.inventory.apply_add(c.id, "hemp_snare_kit", 1, "test")
	if c.inventory.count("wood_rite_tablet") <= 0: Game.inventory.apply_add(c.id, "wood_rite_tablet", 1, "test")
	# Snaring at the Reed Shallows' jade frog trail.
	Game.world.apply_teleport(c.id, "lf_reed_shallows")
	var trail: Dictionary = Game.room_rt.object_def("trail_jade_frog")
	check(not trail.is_empty(), "the Reed Shallows have a jade frog trail")
	Game.actor_state(c.id).plane = Vector2(float(trail.at[0]), float(trail.at[1]))
	check(Game.submit({"type": "set_snare", "object": "trail_jade_frog", "snare": "snare_1h"}).get("ok", false), "set an hour's snare on the trail")
	var early := Game.submit({"type": "collect_snare", "object": "trail_jade_frog"})
	check(not early.get("ok", true) and str(early.get("reason", "")) == "not_ready", "a snare cannot be taken up before its time")
	Game.posts.my_snare(c, "trail_jade_frog")["done"] = Clock.now_utc() - 1.0
	var sx0: float = Game.posts.xp(c, "snaring")
	var got := Game.submit({"type": "collect_snare", "object": "trail_jade_frog"})
	check(got.get("ok", false) and int(got.get("items", {}).get("jade_frog", 0)) >= 2 and Game.posts.xp(c, "snaring") > sx0,
		"an hour's snare holds %d jade frogs and gives Snaring EXP" % int(got.get("items", {}).get("jade_frog", 0)))
	# The rites at the County Hall altar.
	Game.world.apply_teleport(c.id, "sf_county_hall")
	var altar: Dictionary = Game.room_rt.object_def("ancestral_altar")
	check(not altar.is_empty(), "the County Hall keeps an ancestral altar")
	Game.actor_state(c.id).plane = Vector2(float(altar.at[0]), float(altar.at[1]))
	check(Game.posts.rite_charge(c) >= 10.0, "the first rite needs no waiting: %.0f charge" % Game.posts.rite_charge(c))
	var w0: int = c.inventory.count("spirit_wisp")
	var rite := Game.submit({"type": "hold_rite", "object": "ancestral_altar"})
	check(rite.get("ok", false) and c.inventory.count("spirit_wisp") > w0 and near(Game.posts.rite_charge(c), 0.0, 0.5),
		"hold the rites: wave %d, %d Spirit Wisps, the charge spent" % [int(rite.get("wave", 0)), c.inventory.count("spirit_wisp") - w0])
	# Post Vows.
	Game.inventory.apply_add(c.id, "spirit_wisp", 40, "test")
	Game.account.post_vows.erase("vow_short_lamp")
	check(Game.submit({"type": "learn_post_vow", "vow": "vow_short_lamp"}).get("ok", false) and Game.account.post_vows.has("vow_short_lamp"),
		"learn the Vow of the Short Lamp with Spirit Wisps")
	check(Game.submit({"type": "pledge_post_vow", "vow": "vow_short_lamp", "on": true}).get("ok", false) and near(Game.posts.vow_sum(c, "post_hours"), 10.0)
		and near(Game.posts.vow_sum(c, "craft_exp_pct"), 25.0), "hold it: +25% craft EXP, posts stop after 10 hours")
	Game.submit({"type": "pledge_post_vow", "vow": "vow_short_lamp", "on": false})
	# The Apprentice Bench.
	check(Game.submit({"type": "bench_assign", "slot": 0, "item": "hemp_cord"}).get("ok", false), "set an apprentice to hemp cord")
	Game.posts.bench(c)["updated"] = Clock.now_utc() - 3600.0
	Game.posts._bench_settle(c)
	var stock := float(Game.posts.bench(c).stock.get("hemp_cord", 0.0))
	check(stock > 0.0 and stock <= Game.posts.bench_capacity(c) + 0.01, "an hour at the bench: %.0f hemp cord (capacity %.0f)" % [stock, Game.posts.bench_capacity(c)])
	var col := Game.submit({"type": "bench_collect"})
	check(col.get("ok", false) and int(col.get("items", {}).get("hemp_cord", 0)) > 0, "the components come off the bench into the pouch")
	c.posts = posts0
	Game.account.post_vows = vows0
	Game.world.apply_teleport(c.id, back)

func works_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	check(near(PostRules.curve("add", 3.0, 0.0, 4.0), 12.0) and near(PostRules.curve("decay", 20.0, 40.0, 40.0), 10.0) and near(PostRules.curve("decay", 20.0, 40.0, 0.0), 0.0),
		"the account curves: add = x1 L; decay = x1 L / (L + x2)")
	check(PostRules.art_points(11) == 5, "a Post Art point for every two craft levels")
	var ladder := ["copper_ore", "riverstone", "jadeiron"]
	var s0 := PostRules.seal_cost(0, ladder)
	var s5 := PostRules.seal_cost(5, ladder)
	check(str(s0.item) == "copper_ore" and int(s0.count) == 25 and str(s5.item) == "riverstone" and int(s5.count) == int(ceil(25.0 * pow(1.12, 5))),
		"a seal costs ceil(25 x 1.12^L) of its ladder's item for the level band (%d %s at level 5)" % [int(s5.count), str(s5.item)])
	var t5 := PostRules.stele_cost(5)
	check(int(PostRules.stele_cost(0).taels) == 150 and int(t5.taels) == int(floor(150.0 * pow(1.22, 5))) and str(t5.item) == "riverstone" and int(t5.count) == 17,
		"a stele costs floor(150 x 1.22^L) taels and ceil(10 x 1.1^L) ore")
	check(near(PostRules.finesse(6.0, 10.0, 1, 0.0, [], 1.5), PostRules.finesse(7.5, 10.0, 1)), "stele power adds to the tool's power")
	var back := str(c.position.get("room", "lf_village"))
	var posts0: Dictionary = c.posts.duplicate(true)
	var works0: Dictionary = Game.account.works.duplicate(true)
	var store0: Dictionary = Game.account.storehouse.duplicate()
	for u in ["keeping_post", "post_arts", "seal_scripts", "guardian_steles", "magistrates_favours"]: Unlocks.force_unlock(c.id, u)
	Game.account.works = {}
	c.posts["arts"] = {}
	Game.posts.apply_craft_xp(c.id, "delving", 400.0, "test")
	var lv := Game.posts.level(c, "delving")
	check(Game.posts.art_points_free(c) == PostRules.art_points(Game.posts.total_craft_levels(c)) and Game.posts.art_points_free(c) >= 1,
		"%d craft levels give %d Post Art points" % [Game.posts.total_craft_levels(c), Game.posts.art_points_free(c)])
	# Arts: Dreaming Artisan raises Craft Diligence; Steady Hand multiplies Finesse.
	var d0 := Game.posts.diligence_of(c)
	check(Game.submit({"type": "learn_post_art", "art": "dreaming_artisan"}).get("ok", false) and near(Game.posts.diligence_of(c) - d0, 20.0 / 41.0 / 100.0, 0.0005),
		"Dreaming Artisan 1: Craft Diligence +%.2f%%" % (100.0 * (Game.posts.diligence_of(c) - d0)))
	var f0 := Game.posts.finesse_of(c, "delving")
	c.posts.arts["steady_hand"] = 60
	check(near(Game.posts.finesse_of(c, "delving") - 12.0, (f0 - 12.0) * 1.15, 0.01), "Steady Hand 60 multiplies Finesse (above its flat 12) by 1.15")
	c.posts.arts.erase("steady_hand")
	check(not Game.submit({"type": "collect_snare", "object": "nowhere", "remote": true}).get("ok", true), "without Hunter's Recall no snare is taken up from afar")
	# Seals: paid from the Storehouse; a character draws on a seal only up to its craft level.
	Game.account.storehouse["copper_ore"] = 5000
	Game.account.storehouse["riverstone"] = 5000
	for i in lv + 2: Game.submit({"type": "inscribe_seal", "seal": "seal_open_vein"})
	check(Game.posts.seal_level("seal_open_vein") == mini(lv + 2, 10) and int(Game.account.storehouse.get("riverstone", 0)) < 5000,
		"inscribe the Seal of the Open Vein to level %d with stored copper ore (%d left, Delving %d)" % [Game.posts.seal_level("seal_open_vein"), int(Game.account.storehouse.get("copper_ore", 0)), lv])
	check(near(Game.posts.seal_sum(c, "finesse_flat", "delving"), 3.0 * mini(lv, Game.posts.seal_level("seal_open_vein"))) and near(Game.posts.seal_sum(c, "finesse_flat", "angling"), 0.0),
		"a Delving level %d character uses the seal to level %d: +%.0f flat Finesse, and only for Delving" % [lv, mini(lv, Game.posts.seal_level("seal_open_vein")), Game.posts.seal_sum(c, "finesse_flat", "delving")])
	Game.account.storehouse.erase("hemp_cord")
	var fail := Game.submit({"type": "inscribe_seal", "seal": "seal_deep_pouch"})
	check(not fail.get("ok", true) and str(fail.get("reason", "")) == "materials", "a seal without its goods in the Storehouse is refused")
	# Steles: taels and ore; the tool bites harder.
	Game.economy.apply_currency("silver_tael", 1000, "test")
	var f1 := Game.posts.finesse_of(c, "delving")
	check(Game.submit({"type": "raise_stele", "craft": "delving"}).get("ok", false) and near(Game.posts.stele_power("delving"), 0.3)
		and Game.posts.finesse_of(c, "delving") > f1, "raise the Stele of Vein Delving: +0.3 tool power, Finesse %.1f -> %.1f" % [f1, Game.posts.finesse_of(c, "delving")])
	# Favours: once each, for good.
	Game.economy.apply_currency("silver_tael", 10000, "test")
	Game.account.storehouse["jadeiron"] = 300
	Game.account.storehouse["reed_cicada"] = 200
	var d1 := Game.posts.diligence_of(c)
	check(Game.submit({"type": "seek_favour", "favour": "favour_of_the_guilds"}).get("ok", false) and near(Game.posts.diligence_of(c) - d1, 0.03)
		and not Game.account.storehouse.has("jadeiron"), "the Favour of the Guilds: Craft Diligence +3%, the tribute taken")
	check(not Game.submit({"type": "seek_favour", "favour": "favour_of_the_guilds"}).get("ok", true), "a favour is granted only once")
	var snap: Dictionary = Game.account.snapshot()
	check(int(snap.get("works", {}).get("seals", {}).get("seal_open_vein", 0)) == Game.posts.seal_level("seal_open_vein") and snap.works.favours.has("favour_of_the_guilds"),
		"the works are saved with the account")
	check(Game.submit({"type": "reset_post_arts"}).get("ok", false) and Game.posts.arts(c).is_empty(), "forget every art for taels")
	# V10d2 · the Calcination Furnace.
	check(PostRules.calcination_cost(1, 3) == 3 and PostRules.calcination_cost(4, 3) == 24 and PostRules.calcination_fire(4) == 6
		and PostRules.calcination_rank_need(1) == 20 and PostRules.calcination_rank_need(2) == int(floor(20.0 * pow(2.0, 1.8))),
		"a line burns floor(rank^1.5) x qty, banks floor(rank^1.3) fire, ranks up at floor(20 x rank^1.8) refined")
	var sc10 := PostRules.seal_cost(10, ladder)
	var sc14 := PostRules.seal_cost(14, ladder)
	check(str(sc10.get("salt", "")) == "cinnabar_salt" and int(sc10.salt_count) == 4 and str(sc14.get("salt", "")) == "verdigris_salt"
		and int(sc14.salt_count) == int(ceil(4.0 * pow(1.18, 4))) and not PostRules.seal_cost(9, ladder).has("salt"), "seals past level 10 want Essence Salts too")
	for u in ["calcination", "formation_flags", "mirror_of_echoes"]: Unlocks.force_unlock(c.id, u)
	Game.account.works = {}
	Game.account.storehouse["copper_ore"] = 300
	Game.account.storehouse["willow_moss"] = 200
	check(Game.submit({"type": "calcine_line", "line": "cinnabar_salt", "on": true}).get("ok", false) and not Game.posts.line_open("verdigris_salt"),
		"light the Cinnabar line; the Verdigris line waits for rank 3")
	Game.posts.salt_line("cinnabar_salt")["since"] = Clock.now_utc() - 3600.0 - 60.0
	Game.posts.calcination_settle()
	check(int(Game.posts.salt_line("cinnabar_salt").fire) == 4 and int(Game.account.storehouse.get("copper_ore", 0)) == 288
		and int(Game.account.storehouse.get("willow_moss", 0)) == 192, "an hour: four cycles, 12 copper and 8 moss burned, 4 fire banked")
	Game.account.storehouse["willow_moss"] = 3
	Game.posts.salt_line("cinnabar_salt")["since"] = Clock.now_utc() - 3600.0
	Game.posts.calcination_settle()
	check(int(Game.posts.salt_line("cinnabar_salt").fire) == 5, "a line burns only what the Storehouse can feed (one more cycle on 3 moss)")
	Game.posts.salt_line("cinnabar_salt")["refined"] = 16
	var rf := Game.submit({"type": "refine_line", "line": "cinnabar_salt"})
	check(rf.get("ok", false) and int(Game.account.storehouse.get("cinnabar_salt", 0)) == 5 and int(rf.rank) == 2,
		"refine: 5 Cinnabar Salt into the Storehouse, the line ranks up to 2")
	# Formation Flags.
	Game.world.apply_teleport(c.id, "lf_reed_shallows")
	var dl0 := Game.posts.diligence_of(c)
	check(Game.submit({"type": "plant_flag", "kind": "plain"}).get("ok", false) and near(Game.posts.flag_sum("lf_reed_shallows", "craft_diligence"), 1.0)
		and near(Game.posts.diligence_of(c) - dl0, 0.01), "a plain flag over the Reed Shallows: Craft Diligence +1% for its posts")
	check(not Game.submit({"type": "plant_flag", "kind": "deep"}).get("ok", true), "one flag to a room")
	check(Game.submit({"type": "raise_flag", "index": 0}).get("ok", false) and near(Game.posts.flag_sum("lf_reed_shallows", "craft_diligence"), 1.1)
		and int(Game.account.storehouse.get("cinnabar_salt", 0)) == 0, "raise it with 5 Cinnabar Salt: +1.1%")
	# The Mirror of Echoes.
	var sect0: Dictionary = Game.account.sect.duplicate(true)
	if not Game.account.sect.has("buildings"): Game.account.sect["buildings"] = {}
	Game.account.sect.buildings["mirror_of_echoes"] = 5
	c.posts["arts"] = {"echo_sampling": 10}
	var moss: Dictionary = {}
	for o in Game.room_rt.def.get("objects", []):
		if str(o.get("type", "")) == "herb_patch" and str(o.get("item", "")) == "willow_moss": moss = o
	Game.actor_state(c.id).plane = Vector2(float(moss.at[0]), float(moss.at[1]))
	check(Game.submit({"type": "take_post", "object": str(moss.id)}).get("ok", false), "keep post at the willow moss")
	check(Game.posts.mirror_slot_count() == 2, "a level 5 Mirror has two slots")
	var ec := Game.submit({"type": "echo_inscribe", "slot": 0})
	var want := 10.75 / 100.0 * 1.25
	check(ec.get("ok", false) and near(float(ec.share), want, 0.0001), "Echo Sampling 10 in a level 5 Mirror echoes %.2f%% of the post" % (100.0 * float(ec.get("share", 0.0))))
	var per_h := float(ec.get("items", {}).get("willow_moss", 0.0))
	Game.account.storehouse.erase("willow_moss")
	Game.posts.works().mirror["since"] = Clock.now_utc() - 10.0 * 3600.0
	Game.posts.mirror_settle()
	check(per_h > 0.0 and int(Game.account.storehouse.get("willow_moss", 0)) == int(floor(per_h * 10.0)),
		"ten hours of echo: %d willow moss into the Storehouse" % int(Game.account.storehouse.get("willow_moss", 0)))
	# Auto-Settle.
	check(Game.submit({"type": "set_post_option", "key": "auto_settle", "on": true}).get("ok", false) and Game.posts.works().auto_settle, "turn Auto-Settle on")
	check(not Game.submit({"type": "set_post_option", "key": "granary", "on": true}).get("ok", true), "the Granary Seal needs its favour")
	Game.submit({"type": "leave_post"})
	Game.account.sect = sect0
	Game.world.apply_teleport(c.id, back)
	c.posts = posts0
	Game.account.works = works0
	Game.account.storehouse = store0

## P1 (docs/roadmap_master_ui.md): the four head markers through one NPC's quests, and the way to a quest's room.
func guidance_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var q0: Dictionary = c.quests.snapshot()
	var back := str(c.position.get("room", "lf_village"))
	c.quests.active = {}
	c.quests.done = {}
	c.quests.tracked = []
	c.quests.offered = {"the_ancestors_regard": true}
	check(Game.quest.npc_marker(c, "magistrate_qian") == "side", "a first quest on offer: the blue side mark (%s)" % Game.quest.npc_marker(c, "magistrate_qian"))
	c.quests.done = {"the_ancestors_regard": 1}
	c.quests.offered = {"the_county_tribute": true}
	check(Game.quest.npc_marker(c, "magistrate_qian") == "again", "another quest from someone you have helped: the jade-ringed mark")
	c.quests.offered = {}
	c.quests.active = {"the_county_tribute": {"state": "active", "progress": [0], "accepted_tick": 0}}
	check(Game.quest.npc_marker(c, "magistrate_qian") == "progress", "their quest under way: the grey bubble")
	check(not QuestAuthority.marker_calls("progress") and QuestAuthority.marker_calls("again"), "the grey bubble does not call the player over")
	c.quests.active["the_county_tribute"]["state"] = "ready"
	check(Game.quest.npc_marker(c, "magistrate_qian") == "ready", "done and ready to hand in: the question mark")
	# The way there: the tracker names the room, the minimap marks this room's exit on the route.
	c.quests.active = {"glowflies": {"state": "active", "progress": [0], "accepted_tick": 0}}
	c.quests.done = {"fists_first": 1}   # the village's east gate opens after Fists First
	c.quests.tracked = ["glowflies"]
	Game.world.apply_teleport(c.id, "lf_village")
	check(Game.world.guide_target(c) == "lf_reed_shallows", "the tracked quest leads to the Reed Shallows")
	var gs: Dictionary = Game.world.guide_step(c)
	var r: Array = Game.world.route(c, "lf_village", "lf_reed_shallows")
	check(not gs.is_empty() and not r.is_empty() and str(gs.next) == str(r[0].to) and str(gs.portal) == str(r[0].portal),
		"the minimap marks the exit toward %s (%s; route %s; room %s)" % [str(gs.get("next", "")), str(gs.get("portal", "")), str(r.slice(0, 2)), str(Game.room_rt.room_id)])
	check(WorldAuthority.place_name("sf_county_hall").begins_with(str(ContentDB.room("sf_county_hall").name)) and " · " in WorldAuthority.place_name("sf_county_hall"),
		"the tracker names it: %s" % WorldAuthority.place_name("sf_county_hall"))
	Game.world.apply_teleport(c.id, "lf_reed_shallows")
	check(Game.world.guide_step(c).is_empty(), "no mark once there")
	# M20: the mark follows the objective under way, not only the quest's room. The hermit's cave lies behind a hidden
	# way on Rimefrost Summit: until Spirit Sense shows it, the mark leads as far as the Summit.
	c.quests.active = {"frost_and_silence": {"state": "active", "progress": [0, 0, 0], "accepted_tick": 0}}
	c.quests.tracked = ["frost_and_silence"]
	Game.world.apply_teleport(c.id, "rf_snow_ape_ledges")
	var fs: Dictionary = Game.world.guide_step(c)
	check(Game.world.guide_target(c) == "rf_hermits_ice_cave" and str(fs.get("next", "")) == "rf_rimefrost_summit",
		"the first objective leads to the hermit's cave, the mark as far as the Summit that hides its way (%s)" % str(fs))
	# A key the bandits drop on the Caravan Road is marked there, not on the Stockade it opens; an NPC who stands in both
	# sects' grounds is visited in the character's own.
	var road := ContentDB.entry("quests", "the_caravan_road")
	check(Game.quest.objective_room(c, road, road.objectives[1]) == "cr_caravan_road", "the Hideout key is marked where the bandits drop it")
	var sect_was: Dictionary = c.training_sect.duplicate()
	var arenas: Array = []
	for sect in ["jade_sect", "cloud_sect"]:
		c.training_sect = {"id": sect}
		arenas.append(Game.quest.npc_rooms(c, "arena_master")[0])
	c.training_sect = sect_was
	check(arenas == ["ja_east_terrace", "cm_sword_court"], "the arena master is found in the character's own sect (%s)" % str(arenas))
	# The hand-in is marked where the NPC stands now: after the Hollow Night, Aunt Ping in the village lane, not the hut.
	c.quests.done = {"morning_tide": 1}
	c.quests.flags["night_active"] = true
	check(Game.quest.npc_rooms(c, "aunt_ping") == ["lf_village"], "after the Hollow Night Aunt Ping is looked for in the lane (%s)" % str(Game.quest.npc_rooms(c, "aunt_ping")))
	c.quests.restore(q0)
	Game.world.apply_teleport(c.id, back)

## v1.2 Phase C: gravity switches in the Orbit Ruins, the Sphere (radius, power, element effects, clash, the Qi it
## costs), the Space Dao's six tiers and the Confucian path's gates.
func sphere_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	# -- Rules.
	check(near(FieldRules.sphere_radius(1), 180.0) and near(FieldRules.sphere_radius(5), 260.0) and near(FieldRules.sphere_radius(6), 320.0),
		"a Sphere reaches 160 + 20 a Dao tier, and 40 more at the sixth")
	check(near(FieldRules.sphere_power(90, 3), 95.0 * 1.24) and near(FieldRules.sphere_power(90, 6), 95.0 * 1.58) and near(FieldRules.sphere_power(90, 0), 0.0),
		"its power is (5 + Level) x (1 + 8% a tier, +10% at tier 6); no tier, no Sphere")
	var wet := FieldRules.sphere_effects("water", ["water"])
	check(near(float(FieldRules.sphere_effects("water", []).slow), 0.2) and wet.get("freeze", false) and near(float(wet.slow), 0.35),
		"a Water Sphere slows by a fifth; over water it freezes the surface and slows by more")
	check(near(float(FieldRules.sphere_effects("fire", ["grass"]).burn_pct), 0.02) and FieldRules.sphere_effects("earth", []).get("vulnerable", false),
		"fire burns hotter on grass; earth leaves what it holds open to harm")
	check(FieldRules.feeds("fire", "fire") and FieldRules.feeds("wood", "fire") and not FieldRules.feeds("water", "fire") and not FieldRules.feeds("", "fire"),
		"ground feeds a technique of its own element or the one it generates (wood feeds fire)")
	# -- The Space Dao and tier 6.
	var space: Dictionary = ContentDB.entry("daos", "space")
	check(space.get("tiers", []).size() == 6, "the Space Dao has six tiers")
	check(ContentDB.entry("daos", "sword").get("tiers", []).size() >= 6 and ContentDB.entry("daos", "water").get("tiers", []).size() >= 6,
		"weapon and element Daos reach a sixth tier (Original Application)")
	# -- Gravity switches (the Inverted Hall).
	Game.world.apply_teleport(c.id, "or_inverted_hall")
	var st: ActorState = Game.actor_state(c.id)
	var geo = Game.room_rt.geometry
	var in_a := Vector2(1000, 800)
	check(near(geo.gravity_at(in_a, 0.0), 1.0), "with its switch up the hall pulls as hard as anywhere")
	st.plane = Vector2(700, 800)
	st.altitude = 0.0
	var heard := {"g": 0, "sphere": 0, "clash": ""}
	var listen := func(n: String, p: Dictionary):
		if n == "gravity_switched": heard.g = int(heard.g) + 1
		if n == "sphere_toggled" and p.get("on", false): heard.sphere = int(heard.sphere) + 1
		if n == "sphere_clash": heard.clash = str(p.get("winner", ""))
	GameEvents.event.connect(listen)
	var down := Game.submit({"type": "interact", "object": "switch_hall_a"})
	check(down.get("ok", false) and near(geo.gravity_at(in_a, 0.0), 0.45) and int(heard.g) == 1 and str(Game.room_rt.objects.switch_hall_a.state) == "down",
		"press the jade switch down: the air lightens to 45%% (%s)" % str(down))
	check(near(geo.gravity_at(Vector2(1600, 800), 0.0), 1.0), "only over its own half of the hall")
	var g := MovementSolver.GRAVITY
	var j := MovementSolver.JUMP_IMPULSE
	var dj := MovementSolver.DOUBLE_JUMP_IMPULSE
	var high := 0.0
	var low := 0.0
	for sf in Game.room_rt.def.surfaces:
		if str(sf.id) == "gallery_high": high = float(sf.height)
		if str(sf.id) == "gallery_low": low = float(sf.height)
	check(low + j * j / (2.0 * g) + dj * dj / (2.0 * g) < high and j * j / (2.0 * g * 0.45) + dj * dj / (2.0 * g * 0.45) >= high,
		"the high gallery (%.0f) is out of reach of any jump, even from the low one (%.0f), and within a light double jump from the floor" % [high, low])
	Game.submit({"type": "interact", "object": "switch_hall_a"})
	check(near(geo.gravity_at(in_a, 0.0), 1.0) and str(Game.room_rt.objects.switch_hall_a.state) == "up", "press it again and the weight comes back")
	# -- The Sphere.
	var realm0: String = c.cultivator.realm_key
	var daos0: Dictionary = c.cultivator.daos.duplicate(true)
	var inj0: Dictionary = c.cultivator.injuries.duplicate(true)
	c.cultivator.realm_key = "sphere_lord_1"
	Game.combat.refresh_stats(c.id)
	c.cultivator.unlocked.erase("sphere")
	var locked := Game.submit({"type": "toggle_sphere"})
	check(not locked.get("ok", true) and str(locked.get("reason", "")) == "locked", "no Sphere before it is unlocked")
	Unlocks.force_unlock(c.id, "sphere")
	c.cultivator.daos = {"water": {"tier": 3, "insight": 0.0}, "fist": {"tier": 1, "insight": 0.0}}
	var sd: Dictionary = Game.field.sphere_of(c)
	check(str(sd.get("element", "")) == "water" and int(sd.tier) == 3 and near(float(sd.radius), 220.0), "the Sphere is drawn from the strongest combat Dao: %s" % str(sd))
	c.pools.qi = c.pools.max_qi
	Game.field.sphere_cd.erase(c.id)
	Game.room_rt.enemies.clear()
	st.plane = Vector2(1000, 800)
	var near_e: EnemyState = Game.enemies.spawn_at("orbit_moth", st.plane + Vector2(150, 0), 88)
	var far_e: EnemyState = Game.enemies.spawn_at("orbit_moth", st.plane + Vector2(700, 0), 88)
	var up := Game.submit({"type": "toggle_sphere"})
	check(up.get("ok", false) and Game.field.sphere_on(c.id) and int(heard.sphere) == 1 and Game.field.sphere_element(c) == "water",
		"raise the Sphere (%s)" % str(up))
	var qi0: float = c.pools.qi
	Game.field.tick(1.05)
	GameEvents.flush()
	check(c.pools.qi < qi0 and near(qi0 - c.pools.qi, c.pools.max_qi * 0.004 * 1.05, 0.05), "it costs 0.4% of the Qi a second")
	check(near_e.pools.statuses.any(func(x): return str(x.id) == "slow") and not far_e.pools.statuses.any(func(x): return str(x.id) == "slow"),
		"a foe inside it is slowed; one outside is not")
	# A weaker foe's Sphere breaks against yours.
	near_e.def = near_e.def.duplicate()
	near_e.def["sphere"] = {"element": "fire", "tier": 1}
	near_e.level = 60
	Game.field.tick(1.05)
	GameEvents.flush()
	check(heard.clash == "you" and near_e.ai.get("sphere_broken", false) and Game.field.sphere_on(c.id), "a weaker Sphere breaks against yours")
	# A stronger one breaks yours: a meridian injury and a wait.
	far_e.def = far_e.def.duplicate()
	far_e.def["sphere"] = {"element": "sword", "tier": 6}
	far_e.level = 140
	far_e.role = "dungeon_boss"
	far_e.plane = st.plane + Vector2(400, 0)
	Game.field.tick(1.05)
	GameEvents.flush()
	check(heard.clash == "foe" and not Game.field.sphere_on(c.id), "a stronger Sphere breaks yours")
	var again := Game.submit({"type": "toggle_sphere"})
	check(not again.get("ok", true) and str(again.get("reason", "")) == "broken", "and a broken Sphere cannot be raised again at once")
	# The sword Domain needs a jian in hand.
	c.cultivator.daos = {"sword": {"tier": 4, "insight": 0.0}}
	var sw: Dictionary = Game.field.sphere_of(c)
	var jian := str(StatRules.family(c).get("id", "")) == "jian"
	check((str(sw.element) == "sword" and sw.domain) if jian else (str(sw.element) == "metal" and not sw.domain),
		"a Sword Dao Sphere is the Sword Domain only with a jian in hand (%s)" % str(sw))
	Game.field.sphere_cd.erase(c.id)
	# -- The Confucian path.
	var al0: int = c.relations.alignment
	var paths0: Dictionary = c.cultivator.paths.duplicate()
	c.cultivator.paths.erase("confucian")
	c.cultivator.paths.erase("blood")
	c.cultivator.unlocked.erase("confucian_path")
	var r0 := Game.submit({"type": "set_path", "path": "confucian", "on": true})
	check(not r0.get("ok", false) and str(r0.get("reason", "")) == "locked", "the written word waits for its unlock")
	Unlocks.force_unlock(c.id, "confucian_path")
	c.relations.alignment = 0
	var r1 := Game.submit({"type": "set_path", "path": "confucian", "on": true})
	check(not r1.get("ok", false) and str(r1.get("reason", "")) == "alignment", "only an upright heart may walk it")
	c.relations.alignment = 30
	c.cultivator.paths["blood"] = true
	var r2 := Game.submit({"type": "set_path", "path": "confucian", "on": true})
	check(not r2.get("ok", false) and str(r2.get("reason", "")) == "exclusive", "never beside the Blood path")
	c.cultivator.paths.erase("blood")
	var r3 := Game.submit({"type": "set_path", "path": "confucian", "on": true})
	check(r3.get("ok", false) and ProgressionAuthority.walks(c, "confucian") and c.relations.alignment == 35, "walk it: +5 alignment (%s)" % str(r3))
	var hollow: EnemyState = Game.enemies.spawn_at("hollowed_wyrmling", st.plane + Vector2(900, 0), 88)
	check(CombatAuthority._unrighteous(hollow) and not CombatAuthority._unrighteous(near_e), "Righteous Qi knows the Hollow from a moth")
	var tech: Dictionary = ContentDB.entry("techniques", "upright_glyph")
	check(tech.get("confucian_path", false) and near(float(tech.get("insight_scale", 0.0)), 0.5), "the glyphs follow Insight and belong to the path")
	GameEvents.event.disconnect(listen)
	Game.room_rt.enemies.clear()
	c.relations.alignment = al0
	c.cultivator.paths = paths0
	c.cultivator.unlocked.erase("confucian_path")
	c.cultivator.unlocked.erase("sphere")
	c.cultivator.daos = daos0
	c.cultivator.realm_key = realm0
	c.cultivator.injuries = inj0
	Game.combat.refresh_stats(c.id)
	c.pools.qi = c.pools.max_qi
	Game.world.apply_teleport(c.id, back)

## v1.2 Phase D: the brush's talismans, the bell's ring, the Copperjaw swarm, the lantern defence, ground fire, Dao caps
## carried from zone to zone, and the judge_foe objective (Kharn spared or slain).
func ash_tide_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	var back := str(c.position.get("room", "lf_village"))
	var realm0: String = c.cultivator.realm_key
	c.cultivator.realm_key = "sphere_lord_1"
	Game.combat.refresh_stats(c.id)
	Game.world.apply_teleport(c.id, "ar_cinder_fields")
	Game.room_rt.enemies.clear()
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	c.pools.invulnerable = 0.0
	Unlocks.force_unlock(c.id, "attack")
	var lv := ProgressionRules.level(c)
	var heard := {"hits": {}, "failed": "", "judged": ""}
	var listen := func(n: String, p: Dictionary):
		if n == "hit_landed" and str(p.get("target_kind", "")) == "enemy": heard.hits[str(p.target)] = int(heard.hits.get(str(p.target), 0)) + 1
		if n == "room_event_failed": heard.failed = str(p.get("reason", ""))
		if n == "foe_judged": heard.judged = "%s:%s" % [str(p.get("def", "")), str(p.get("spared", ""))]
	GameEvents.event.connect(listen)
	# -- Dao caps carry forward: what the Expanse allowed, the Field allows.
	var bt: Dictionary = ContentDB.entry("daos", "beast_taming")
	check(int(bt.zone_caps.get("lantern_star_field", 0)) >= int(bt.zone_caps.get("azure_expanse", 0)) and int(bt.zone_caps.get("lantern_star_field", 0)) == 4,
		"Beast Taming keeps its Expanse cap (4) in the Lantern Star Field")
	check(int(ContentDB.entry("daos", "blood").zone_caps.get("lantern_star_field", 0)) == 4, "and so do the rare Daos")
	# -- The brush: each technique writes a talisman by its element, one on a foe at a time.
	var held = _wield(c, "ink_warden_brush")
	check(str(StatRules.family(c).id) == "brush" and str(StatRules.family(c).get("damage_type", "")) == "qi", "the Ink-Warden's Brush puts the brush in hand (Qi strikes)")
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	Game.combat._weapon_after_hit(c, foe, {"talisman": {"id": "burn", "power": 0.006, "remaining": 4.0}})
	check(foe.pools.has_status("burn"), "a Fire talisman sets the foe burning")
	Game.combat._weapon_after_hit(c, foe, {"talisman": {"id": "slow", "power": 0.3, "remaining": 4.0}})
	check(not foe.pools.has_status("slow"), "one talisman on a foe at a time")
	foe.alive = false
	var known0: Array = c.cultivator.techniques_known.duplicate()
	var slot0 = c.cultivator.technique_slots[0]
	Unlocks.force_unlock(c.id, "technique_slots_2")
	if not c.cultivator.techniques_known.has("splashed_ink"): c.cultivator.techniques_known.append("splashed_ink")
	c.cultivator.technique_slots[0] = "splashed_ink"
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:splashed_ink")
	var foe2: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(80, 0), lv)
	_idle_hands(c)
	var used := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	for i in 20: Game.tick(0.05)
	GameEvents.flush()
	check(used.get("ok", false) and foe2.pools.has_status("qi_seal"), "Splashed Ink (no element) writes a sealing talisman: the foe's Qi is sealed (%s)" % str(used))
	foe2.alive = false
	c.cultivator.technique_slots[0] = slot0
	c.cultivator.techniques_known = known0
	# -- The bell rings out on both sides of its bearer.
	_wield(c, "wardens_handbell")
	var ahead: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(90, 0), lv)
	var behind: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-90, 0), lv)
	_idle_hands(c)
	heard.hits = {}
	Game.combat.basic_attack(c, 1)
	for i in 20: Game.tick(0.05)
	GameEvents.flush()
	check(heard.hits.has(str(ahead.uid)) and heard.hits.has(str(behind.uid)), "a bell's strike rings out ahead and behind (%s)" % str(heard.hits))
	ahead.alive = false
	behind.alive = false
	c.inventory.equipped["weapon"] = held
	Game.combat.refresh_stats(c.id)
	# -- The Copperjaw swarm: rules.
	var k: Dictionary = Game.pets.swarm_cfg()
	var s1 := PetRules.swarm_settle({"pop": 100.0, "food": 5, "queen": false, "rolled_h": 0}, 10, k, func(_h): return 0.99)
	check(near(float(s1.pop), 100.0 * pow(1.08, 5) * pow(0.98, 5), 0.001) and int(s1.food) == 0 and not s1.queen,
		"five fed hours grow it 8%% an hour, five unfed shrink it 2%% (%.1f)" % float(s1.pop))
	var s2 := PetRules.swarm_settle({"pop": 100.0, "food": 3, "queen": false, "rolled_h": 0}, 3, k, func(_h): return 0.0)
	check(s2.queen and near(float(s2.pop), 100.0 * 1.08 * pow(1.12, 2), 0.001), "a Queen rises on a lucky hour and the swarm grows half again as fast after")
	check(near(PetRules.swarm_bite(1000.0, false, false, k), 0.12 * log(1001.0)) and near(PetRules.swarm_bite(1000.0, false, true, k), 0.06 * log(1001.0))
		and near(PetRules.swarm_bite(1000.0, true, false, k), 0.15 * log(1001.0)), "its bite is 0.12 × ln(1 + population), half on Wood, a quarter more with a Queen")
	var capped := PetRules.swarm_settle({"pop": 4900.0, "food": 50, "queen": false, "rolled_h": 0}, 50, k, func(_h): return 0.99)
	check(near(float(capped.pop), 5000.0), "and never grows past 5,000")
	# -- The swarm: the box, feeding, time and release.
	var swarm0: Dictionary = c.swarm.duplicate(true)
	c.swarm = {}
	c.cultivator.unlocked.erase("beetle_swarm")
	check(not Game.submit({"type": "feed_swarm", "item": "driftglass", "count": 1}).get("ok", true), "no swarm before its unlock")
	Unlocks.force_unlock(c.id, "beetle_swarm")
	Game.inventory.apply_add(c.id, "copperjaw_box", 1, "test")
	Game.inventory.apply_add(c.id, "driftglass", 3, "test")
	check(not Game.submit({"type": "feed_swarm", "item": "herbal_tea", "count": 1}).get("ok", true), "the beetles eat ore, and nothing else")
	var fed := Game.submit({"type": "feed_swarm", "item": "driftglass", "count": 3})
	check(fed.get("ok", false) and int(c.swarm.food) == 24 and c.inventory.count("driftglass") == 0, "three driftglass is 24 hours of food (%s)" % str(fed))
	c.swarm["since_utc"] = float(c.swarm.since_utc) - 3.0 * 3600.0
	var now_sw: Dictionary = Game.pets.swarm_of(c)
	check(near(float(now_sw.pop), 50.0 * pow(1.08, 3), 0.01) or bool(now_sw.get("queen", false)), "three hours away and it has grown (%.1f)" % float(now_sw.pop))
	var bite_foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(120, 0), lv)
	heard.hits = {}
	var rel := Game.submit({"type": "use_item", "index": c.inventory.first_index("copperjaw_box")})
	check(rel.get("ok", false) and c.inventory.count("copperjaw_box") == 1 and Game.pets.swarming.has(c.id), "open the box: the swarm goes out and the box stays (%s)" % str(rel))
	for i in 24: Game.tick(0.05)
	GameEvents.flush()
	check(int(heard.hits.get(str(bite_foe.uid), 0)) >= 1, "it chews a foe near you")
	check(not Game.submit({"type": "use_item", "index": c.inventory.first_index("copperjaw_box")}).get("ok", true), "and it cannot be opened again while it is out")
	for i in 180: Game.tick(0.05)
	check(not Game.pets.swarming.has(c.id), "after 8 s it comes home")
	bite_foe.alive = false
	c.cooldowns.erase("swarm")
	c.swarm = swarm0
	# -- Ground fire: standing in it burns; standing clear does not.
	Game.combat.cure_status(c.id, "spawn_protection")
	c.pools.invulnerable = 0.0
	c.pools.hp = c.pools.max_hp
	Game.combat.ground_fires.append({"x": st.plane.x, "y": st.plane.y, "r": 80.0, "t": 3.0, "tick": 0.0, "pct": 0.1, "source": "test"})
	var hp0: float = c.pools.hp
	Game.tick(0.05)
	check(c.pools.hp < hp0 and near(hp0 - c.pools.hp, c.pools.max_hp * 0.05, 0.05), "a burning patch underfoot takes a twentieth of max HP each half second (%.0f)" % (hp0 - c.pools.hp))
	st.plane.x += 300.0
	var hp1: float = c.pools.hp
	for i in 12: Game.tick(0.05)
	check(near(c.pools.hp, hp1, 0.001) or c.pools.hp >= hp1, "step out of it and it burns no more")
	Game.combat.ground_fires.clear()
	# -- The judge_foe objective: Kharn kneels, and the choice completes the quest step.
	Game.quest.apply_start(c.id, "kharns_pyre")
	var kharn: EnemyState = Game.enemies.spawn_at("general_kharn", st.plane + Vector2(120, 0), 92)
	Game.relations.apply_surrender(c, kharn)
	var j := Game.submit({"type": "judge_foe", "enemy": kharn.uid, "spare": true})
	GameEvents.flush()
	check(j.get("ok", false) and heard.judged == "general_kharn:true", "spare Kharn (%s)" % str(j))
	check(int(c.quests.active.get("kharns_pyre", {}).get("progress", [0, 0])[1]) == 1, "and the judgement counts for Kharn's Pyre")
	c.quests.active.erase("kharns_pyre")
	c.quests.offered.erase("kharns_pyre")
	# -- The lantern defence (the Tide battle's room).
	Game.world.apply_teleport(c.id, "si_tide_battle")
	check(Game.room_rt.event.get("active", false) and near(float(Game.room_rt.event.get("light", 0.0)), 100.0), "the Tide battle begins with the great lantern at full light")
	Game.room_rt.enemies.clear()
	Game.room_rt.event.wave_timers = [999.0, 999.0]
	var lantern_at: Array = Game.room_rt.object_def("great_lantern").at
	var la := Vector2(float(lantern_at[0]), float(lantern_at[1]))
	st.plane = la + Vector2(600, 0)
	var d1: EnemyState = Game.enemies.spawn_at("hollow_drone", la + Vector2(40, 0), 92)
	d1.ai["state"] = "stagger"
	d1.ai["timer"] = 99.0
	var l0 := float(Game.room_rt.event.light)
	for i in 20: Game.tick(0.05)
	check(float(Game.room_rt.event.light) < l0 and near(l0 - float(Game.room_rt.event.light), 3.0, 0.2), "a foe beside the lantern dims it 3 a second (%.1f)" % float(Game.room_rt.event.light))
	d1.alive = false
	st.plane = la + Vector2(30, 0)
	var l1 := float(Game.room_rt.event.light)
	for i in 20: Game.tick(0.05)
	check(float(Game.room_rt.event.light) > l1, "standing beside it without striking relights it")
	Game.room_rt.event.light = 0.5
	var d2: EnemyState = Game.enemies.spawn_at("hollow_drone", la + Vector2(20, 0), 92)
	d2.ai["state"] = "stagger"
	d2.ai["timer"] = 99.0
	st.plane = la + Vector2(600, 0)
	for i in 10: Game.tick(0.05)
	GameEvents.flush()
	check(not Game.room_rt.event.get("active", true) and heard.failed == "lantern", "when the lantern goes out the battle is lost")
	GameEvents.event.disconnect(listen)
	Game.room_rt.enemies.clear()
	c.cultivator.unlocked.erase("beetle_swarm")
	c.cultivator.realm_key = realm0
	Game.combat.refresh_stats(c.id)
	c.pools.hp = c.pools.max_hp
	Game.world.apply_teleport(c.id, back)

## v1.2 Phase E: the Void Crab's shell, the Leviathan as a field boss with a Presence and a Sphere, the Law recipes, the
## Lantern Heart's flame, and the Greyfall stand.
func lantern_heart_suite() -> void:
	var c = Game.active()
	if c == null: return
	var crab := StatRules.mob_stats(ContentDB.entry("enemies", "void_crab"), 96)
	var eel := StatRules.mob_stats(ContentDB.entry("enemies", "nebula_eel"), 96)
	check(near(float(crab.physical_defense), float(eel.physical_defense) * 1.6), "a Void Crab's shell holds 60% more defence than an eel at its level")
	var lev: Dictionary = ContentDB.entry("enemies", "nebula_leviathan")
	check(str(lev.role) == "field_boss" and int(lev.get("presence", 0)) == 5 and str(lev.sphere.element) == "space" and lev.phases.size() == 2,
		"the Nebula Leviathan: a field boss with Presence 5, a Sphere of Space and two phases")
	check(ContentDB.entry("pets", "void_crab").get("tame", false), "the Void Crab can be tamed (a star-tier beast)")
	for pid in ["law_condensing_pill", "law_touching_pill"]:
		var rc := ContentDB.entry("recipes", pid)
		check(not rc.is_empty() and str(rc.outputs[0].item) == pid, "the %s has a recipe (Sphere Lord 3, Stargazer Ming)" % pid)
	var flames0: Array = c.crafting.get("flames", []).duplicate()
	c.crafting["flames"] = flames0.filter(func(f): return f != "lantern_heart_flame")
	Game.crafting.apply_absorb_flame(c.id, "lantern_heart_flame")
	check("lantern_heart_flame" in c.crafting.get("flames", []), "the Lantern Heart's flame is absorbed like any Heavenly Flame")
	c.crafting["flames"] = flames0
	var obs: Dictionary = ContentDB.entry("shops", "observatory")
	check(obs.get("stock", []).any(func(r): return str(r.item) == "sphere_comprehension_stone"),
		"Stargazer Ming sells another Sphere Comprehension Stone, so a failed Sphere Lord breakthrough never strands a player")
	var sp: Dictionary = ContentDB.entry("set_pieces", "greyfall_stand")
	check(not sp.is_empty() and sp.room_event.on_complete.any(func(e): return str(e.get("flag", "")) == "shen_lian_taken"),
		"the Greyfall stand ends with Shen Lian on the far side of the Tide")

func ice_mount_suite() -> void:
	var z := ZoneGeometry.new()
	z.configure({"bounds": [0, 480, 3000, 480], "surfaces": [
		{"id": "ground", "rect": [0, 560, 3000, 400], "height": 0, "kind": "ground", "stratum": "ground", "open_edges": false}],
		"volumes": [{"id": "glaze", "kind": "ice", "rect": [1000, 560, 1000, 400], "alt": [-10, 20], "traction": 380}]})
	var dt := 1.0 / 120.0
	# Off the ice the body answers at once; on it, speed only eases toward what it asks for.
	var dry := _trav_actor(z, "ground", Vector2(300, 800))
	MovementSolver.advance(dry, z, dt, Vector2(205, 0))
	var ice := _trav_actor(z, "ground", Vector2(1200, 800))
	_trav_run(ice, z, 0.1, Vector2(205, 0))
	check(near(dry.velocity.x, 205.0, 1.0) and ice.velocity.x > 30.0 and ice.velocity.x < 45.0, "on ice a body gains speed slowly (%.0f after 0.1 s)" % ice.velocity.x)
	_trav_run(ice, z, 1.0, Vector2(205, 0))
	var x0: float = ice.plane.x
	_trav_run(ice, z, 0.25, Vector2.ZERO)
	check(ice.velocity.x > 80.0 and ice.plane.x - x0 > 25.0, "let go and it slides on (%.0f further, still %.0f a second)" % [ice.plane.x - x0, ice.velocity.x])
	_trav_run(ice, z, 1.0, Vector2.ZERO)
	check(ice.velocity.length() < 1.0, "and slides to a stop")
	dry.plane = Vector2(300, 800)
	_trav_run(dry, z, 0.5, Vector2(205, 0))
	_trav_run(dry, z, dt, Vector2.ZERO)
	check(dry.velocity.length() < 1.0, "off the ice it stops dead")
	var air := _trav_actor(z, "ground", Vector2(1500, 800))
	MovementSolver.jump(air)
	MovementSolver.advance(air, z, dt, Vector2(205, 0))
	check(near(air.velocity.x, 205.0, 1.0), "in the air over ice, control stays total")
	# A ground mount's jump: the Cloud Stag's 600 reaches about 156 where a foot jump reaches 122.
	var stag := _trav_actor(z, "ground", Vector2(300, 800))
	stag.jump_impulse = 600.0
	MovementSolver.jump(stag)
	var peak := 0.0
	while stag.surface == null or stag.vertical_speed > 0.0:
		MovementSolver.advance(stag, z, dt, Vector2.ZERO)
		peak = maxf(peak, stag.altitude)
		if stag.surface != null: break
	check(near(peak, 600.0 * 600.0 / 2300.0, 3.0), "a 600 impulse jumps to about 156 (%.0f)" % peak)
	# The Hall of Lanterns' movers (Part 8): a swing on its rope and a circle, pure functions of the room clock.
	var sw := {"mode": "swing", "length": 100, "amp_deg": 30, "period_s": 4.0}
	var o0: Vector3 = z.mover_offset(sw, 0.0)
	var o1: Vector3 = z.mover_offset(sw, 1.0)
	var ci: Vector3 = z.mover_offset({"mode": "circle", "radius": 50, "period_s": 4.0}, 1.0)
	check(o0.length() < 0.01 and near(o1.x, 50.0, 0.1) and near(o1.z, -13.4, 0.1) and near(ci.x, 50.0, 0.1) and near(ci.z, 50.0, 0.1),
		"a swinging lantern sways on its rope (%s); a circling one goes round (%s)" % [str(o1), str(ci)])
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var mount_was := str(c.mount_pet)
	var riding_was: bool = c.riding
	check(near(Game.pets.mount_jump(c), 530.0) or not Game.pets.mount_of(c).is_empty(), "on foot a rider jumps 530")
	Game.pets.apply_grant(c.id, "cloud_stag")
	var sg: Dictionary = c.pets.back()
	Unlocks.force_unlock(c.id, "mounts")
	Game.pets.dismounted.erase(c.id)
	Game.submit({"type": "set_mount", "pet": sg.uid})
	Game.submit({"type": "set_mount", "on": true})
	check(Game.pets.ground_mounted(c) and near(Game.pets.mount_jump(c), 600.0), "on the Cloud Stag: its own 600 jump")
	Game.pets.apply_grant(c.id, "jade_crane")
	var cr: Dictionary = c.pets.back()
	Game.submit({"type": "set_mount", "pet": cr.uid})
	Game.submit({"type": "set_mount", "on": true})
	check(not Game.pets.ground_mounted(c) and near(Game.pets.mount_jump(c), 530.0), "a flying mount's rider jumps as on foot (the crane flies instead)")
	Game.submit({"type": "set_mount", "pet": sg.uid})
	Game.submit({"type": "set_mount", "on": true})
	# A ladder puts you down; stepping off at the top puts you back up.
	var st: ActorState = Game.actor_state(c.id)
	GameEvents.emit_event("climb_started", {"actor": c.id, "climbable": "test_ladder"})
	GameEvents.flush()
	check(Game.pets.mount_of(c).is_empty() and Game.pets.climb_off.has(c.id), "a climb puts the rider down off the stag")
	st.climbing = {"id": "test_ladder"}
	GameEvents.emit_event("landed", {"actor": c.id, "surface": "x", "fall_height": 0.0})
	GameEvents.flush()
	check(Game.pets.climb_off.has(c.id), "still on the ladder: still on foot")
	st.climbing = {}
	GameEvents.emit_event("climb_finished", {"actor": c.id, "climbable": "test_ladder", "end": "top"})
	GameEvents.flush()
	check(not Game.pets.climb_off.has(c.id) and Game.pets.ground_mounted(c), "off the ladder at the top: back on the stag")
	c.mount_pet = mount_was
	c.riding = riding_was

# ------------------------------------------------------------------ P12 Might (docs/research/stat_scaling_research.md §6)
func might_suite() -> void:
	var t: Array = ContentDB.stat_const("might.table", [])
	check(t.size() == 201 and near(StatRules.might_at(1), 1.0) and near(StatRules.might_at(9), 1.05) and near(StatRules.might_at(10), 1.3),
		"Might: 1.00 at Bone Forging 1, 1.05 at its top, 1.30 at Qi Kindling 1")
	var rising := true
	for lv in range(2, t.size()): rising = rising and float(t[lv]) > float(t[lv - 1])
	check(rising, "Might rises at every Level from 1 to 200")
	var majors := true
	for lv in [19, 28, 37, 46, 55, 64, 73, 82, 91, 100, 109, 166]: majors = majors and absf(StatRules.might_at(lv) / StatRules.might_at(lv - 1) - 1.1706) < 0.001
	check(majors, "each great realm's major breakthrough multiplies Might by 1.17 (1.30^0.6)")
	check(near(StatRules.might_at(118) / StatRules.might_at(117), 1.1, 0.001) and near(StatRules.might_at(120) / StatRules.might_at(119), 1.1, 0.001),
		"the advanced states are x1.10 each")
	check(near(StatRules.might_at(99), 15.31, 0.001) and near(StatRules.might_at(165), 152.76, 0.001), "Might 15.31 at Level 99, 152.8 at 165")
	# Player and monster of a Level share one Might; it scales the attacks, HP and defences, never max Qi or max Soul.
	var c = Game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var realm_was := cu.realm_key
	var qp_was := cu.qp
	var shared := true
	var cut_same := true
	for key in ["qi_kindling_1", "cloud_stride_4", "sage_2", "sphere_lord_3"]:
		cu.realm_key = key
		cu.qp = 0.0
		StatRules.rebuild(c)
		var lv := ProgressionRules.level(c)
		shared = shared and near(StatRules.might(c), float(StatRules.mob_stats({"role": "normal"}, lv).might))
		var d := StatRules.armour_defence(lv) * 0.8
		cut_same = cut_same and near(CombatRules.defence_reduction(d * StatRules.might_at(lv), lv, 0.0, StatRules.might_at(lv)), CombatRules.defence_reduction(d, lv, 0.0), 0.0001)
	check(shared, "a player and a monster of the same Level have the same Might")
	check(cut_same, "a same-Level defence cut is what it was before Might")
	var sb: StatBlock = c.stats
	var m := StatRules.might(c)
	var before := {"max_hp": sb.value("max_hp"), "physical_attack": sb.value("physical_attack"), "max_qi": sb.value("max_qi"), "max_soul": sb.value("max_soul"),
		"physical_defense": sb.value("physical_defense")}
	sb.remove_source("might")
	var mods_ok := near(before.max_hp / sb.value("max_hp"), m) and near(before.physical_attack / sb.value("physical_attack"), m) \
		and near(before.physical_defense / maxf(0.001, sb.value("physical_defense")), m) and near(before.max_qi, sb.value("max_qi")) and near(before.max_soul, sb.value("max_soul"))
	check(mods_ok, "Might (x%.2f) multiplies max HP, attack and defence and leaves max Qi and max Soul alone" % m)
	# Combat Power has no energy term: the same sheet on another energy weighs the same.
	StatRules.rebuild(c)
	var cp := StatRules.combat_power(c)
	var energy_was := cu.energy_type
	cu.energy_type = "none"
	check(StatRules.combat_power(c) == cp, "Combat Power does not read the energy type")
	cu.energy_type = energy_was
	# The damage formula: one additive bucket, a product of final damage, the Qi edge on Qi and Soul blows only.
	var rng := RandomNumberGenerator.new()
	var a := {"physical_attack": 1000.0, "qi_attack": 1000.0, "level": 1, "crit_chance": -10.0}
	var foe := {"role": "normal"}
	var flat := {"never_miss": true, "range": [1.0, 1.0]}
	var hit := func(extra: Dictionary, def: Dictionary, attack: Dictionary) -> int:
		var at := a.duplicate()
		at.merge(extra, true)
		return int(CombatRules.resolve(at, def, attack, rng).amount)
	check(hit.call({}, foe, flat) == 1000, "a plain blow of 1,000 attack lands 1,000")
	check(hit.call({"damage_pct": 0.1, "elemental_power": 0.2}, foe, flat) == 1300, "damage% and elemental power add in one bucket (x1.30, not x1.32)")
	check(hit.call({"boss_damage": 0.5}, foe, flat) == 1000 and hit.call({"boss_damage": 0.5}, {"role": "elite"}, flat) == 1500
		and hit.call({"boss_damage": 0.5}, {"role": "field_boss"}, flat) == 1500, "boss damage counts against elites and bosses only")
	check(hit.call({"damage_pct": 0.1, "final_damage": 1.2}, foe, flat) == 1320, "final damage multiplies the bucket (1.1 x 1.2)")
	var qi_blow := {"never_miss": true, "range": [1.0, 1.0], "damage_type": "qi"}
	check(hit.call({"qi_edge": 1.15}, foe, qi_blow) == 1150 and hit.call({"qi_edge": 1.15}, foe, flat) == 1000, "the Qi edge lifts Qi blows only")
	check(near(ProgressionRules.qi_edge("sage_qi", 9), 1.15) and near(ProgressionRules.qi_edge("true_qi", 6), 1.13) and near(ProgressionRules.qi_edge("heavenforce", 9), 1.3),
		"the Qi edge: Sage 1.15, True Qi 1.10 +1% a purity grade, Heavenforce 1.30")
	# A share of an elite's or a boss's health a second is capped at 60% of the caster's attack.
	check(near(CombatRules.hp_share(10000.0, "field_boss", 1000.0), 600.0) and near(CombatRules.hp_share(10000.0, "normal", 1000.0), 10000.0)
		and near(CombatRules.hp_share(10000.0, "elite", 0.0), 10000.0), "a share of a boss's health is capped at 60% of the caster's attack; normal foes are not")
	# UiKit.short: five characters or fewer; fmt turns to it from ten million.
	var shorts := [[9876.0, "9,876"], [10000.0, "10.0K"], [18200.0, "18.2K"], [136000.0, "136K"], [99960.0, "100K"], [999600.0, "1.00M"],
		[1270000.0, "1.27M"], [191000000.0, "191M"], [1.2e9, "1.20B"], [3.4e12, "3.40T"]]
	var short_ok := true
	for s in shorts: short_ok = short_ok and UiKit.short(float(s[0])) == str(s[1])
	check(short_ok, "UiKit.short: 9,876, 18.2K, 136K, 1.27M, 1.20B")
	check(UiKit.fmt(12345678.0) == "12.3M" and UiKit.fmt(9999999.0) == "9,999,999", "fmt groups to 9,999,999 and is short above")
	check(UiKit.pool_values(427000.0, 427000.0) == ["427K", "427K"] and UiKit.pool_values(99000.0, 99999.0) == ["99,000", "99,999"], "bars of 100,000 or more show short")
	# The save migration: saved health grows with Might so its share holds; it runs once.
	var saved := Saves.migrate_character({"version": 3, "cultivator": {"realm_key": "sphere_lord_3", "progress": 0.7}, "pools": {"hp": 1000.0, "qi": 50.0}})
	check(near(float(saved.pools.hp), 1000.0 * StatRules.might_at(99)) and near(float(saved.pools.qi), 50.0) and int(saved.minor) == GameCharacter.MINOR,
		"an old save's health grows by the Might of its Level (Qi kept)")
	check(near(float(Saves.migrate_character(saved).pools.hp), 1000.0 * StatRules.might_at(99)), "and only once")
	# Chapter floors: every main quest of a chapter asks at least its floor; no main quest has a ceiling.
	var floors: Dictionary = ContentDB.config("quests").get("chapter_floors", {})
	var floored := true
	var ceilings := false
	for q in ContentDB.all("quests"):
		if str(q.get("kind", "")) != "main": continue
		var own := "mortal"
		for r in q.get("requires", {}).get("all", []):
			if str(r.get("kind", "")) == "realm_at_least": own = str(r.realm)
			if str(r.get("kind", "")) in ["realm_below", "level_below"]: ceilings = true
		if floors.has(str(q.get("chapter", ""))): floored = floored and ProgressionRules.at_least(own, str(floors[str(q.chapter)]))
	check(floors.size() == 21 and floored and not ceilings, "every main quest of chapters 2-22 asks its chapter's floor, and none a ceiling")
	cu.realm_key = realm_was
	cu.qp = qp_was
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ formulas
func rules_suite() -> void:
	# S13 / P12: a monster's HP and attack come from the par tables (stats.json mob.hp_table, attack_table). Level 10 keeps
	# the spec's 290 HP (3.5 par blows, 220, fall below today's polynomial, which the table keeps as its floor); its
	# attack is the table's 53: a blow of 8% of par HP (589 x 0.08 = 47) before par's armour cut of 11%.
	var normal := StatRules.mob_stats({"role": "normal"}, 10)
	check(near(normal.max_hp, 290.0), "normal monster at Level 10 has 290 HP (%.1f)" % normal.max_hp)
	check(near(normal.attack, 53.0), "normal monster attack at Level 10 is 53, from the par table (%.1f)" % normal.attack)
	var elite := StatRules.mob_stats({"role": "normal"}, 10, true)
	check(near(elite.max_hp, 290.0 * 6.0) and near(elite.attack, 53.0 * 1.5), "elites are 6x HP and 1.5x attack")
	var boss := StatRules.mob_stats({"role": "dungeon_boss"}, 18)
	check(near(boss.max_hp, float(ContentDB.stat_const("mob.hp_table", [])[18]) * 80.0), "a dungeon boss without a par time is 80x a normal foe's HP")
	check(near(StatRules.mob_stats({"role": "dungeon_boss", "par_s": 90}, 18).max_hp, float(StatRules.par(18).dps) * 90.0),
		"a boss with a par time has the par character's DPS times it (Big Toad Tan's 90 s)")
	check(near(StatRules.mob_stats({"role": "normal", "hp_mult": 0.5}, 10).max_hp, 145.0), "hp_mult scales one monster")
	# S13 kill progress gap factors: 5+ above x1.2, within 4 x1.0, 5-9 below x0.5, 10+ below x0.1.
	check(near(ProgressionRules.gap_factor(6), 1.2), "5+ levels above: x1.2")
	check(near(ProgressionRules.gap_factor(0), 1.0) and near(ProgressionRules.gap_factor(-4), 1.0), "within 4 levels: x1.0")
	check(near(ProgressionRules.gap_factor(-6), 0.5), "5-9 below: x0.5")
	check(near(ProgressionRules.gap_factor(-12), 0.1), "10+ below: x0.1")
	# S12 combat steps
	check(near(CombatRules.hit_chance(100.0, 0.0), 1.0), "hit chance caps at 100%")
	check(CombatRules.hit_chance(100.0, 1000.0) >= 0.55, "hit chance never below the floor")
	var dr := CombatRules.defence_reduction(1e9, 1, 0.0)
	check(dr <= 0.75 + 1e-6, "defence reduction caps at 75%% (%.3f)" % dr)
	check(CombatRules.defence_reduction(100.0, 10, 0.4) < CombatRules.defence_reduction(100.0, 10, 0.0), "penetration lowers defence")
	check(CombatRules.realm_gap_factor(3, 1) > 1.0 and CombatRules.realm_gap_factor(1, 3) < 1.0, "realm gap favours the higher realm")
	check(near(CombatRules.realm_gap_factor(2, 2), 1.0), "same realm: no gap factor")
	# S18 attunement at 0.5x, 1x and 1.15x the requirement; a zone that asks nothing changes nothing.
	var half := CombatRules.attunement_factors(5.0, 10.0)
	check(near(half.dealt, 0.65) and near(half.taken, 1.5), "attunement at half: 65%% dealt, 150%% taken")
	var full := CombatRules.attunement_factors(10.0, 10.0)
	check(near(full.dealt, 1.0) and near(full.taken, 1.0), "attunement met: no change")
	var over := CombatRules.attunement_factors(11.5, 10.0)
	check(near(over.dealt, 1.1) and near(over.taken, 1.0), "attunement 1.15x: dealt capped at 110%%")
	var none := CombatRules.attunement_factors(0.0, 0.0)
	check(near(none.dealt, 1.0) and near(none.taken, 1.0), "no requirement: no attunement factor")
	# S09 mastery doubles per tier; S05 risk words
	check(near(ProgressionRules.mastery_needed(1), 100.0) and near(ProgressionRules.mastery_needed(3), 400.0), "mastery 100 / 200 / 400")
	check(ProgressionRules.risk_index(0, false, 0, 0, false) == 0 and ProgressionRules.risk_index(5, true, 3, 0, false) == 3, "risk index clamps 0..3")
	check(ProgressionRules.risk_index(1, false, 0, 1, false) == 0, "a support cancels one unmet soft requirement")
	check(ProgressionRules.success_chance("low") > ProgressionRules.success_chance("severe"), "lower risk, better odds")
	# S07 offline window
	var span := ProgressionRules.offline_minutes(20.0 * 3600.0, 12.0)
	check(near(span.minutes, 720.0) and span.capped, "offline caps at 12 hours")
	check(near(ProgressionRules.offline_minutes(3600.0, 12.0).minutes, 60.0), "an hour away is an hour")
	# Body XP grows linearly per level (S29)
	check(ProgressionRules.body_xp_needed(5) > ProgressionRules.body_xp_needed(1), "body levels get dearer")

# ------------------------------------------------------------------ replay
## Two runs from the same seed with the same intents must end in the same state.
func _run_once(folder: String) -> String:
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Clock.override_utc = 1767225600.0   # fixed "now"
	Clock.debug_offset_s = 0.0
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 12345
	Rng.restore("account", {}, 12345)
	Game.submit({"type": "create_character", "slot": 1, "name": "Replay", "appearance": {"hair": "topknot"}})
	Game.submit({"type": "enter_character", "slot": 1})
	var c = Game.active()
	Rng.restore(c.id, {}, 777)
	Game.submit({"type": "enter_world"})
	var st := ActorState.new()
	Game.bind_movement(c.id, st)
	st.surface = Game.room_rt.geometry.surfaces[0]
	st.plane = Vector2(330, 780)
	# A fixed script of intents and ticks.
	for i in 400:
		if i % 20 == 0: Game.submit({"type": "basic_attack", "facing": 1})
		if i == 100: Game.submit({"type": "start_meditation"})
		if i == 300: Game.submit({"type": "stop_meditation"})
		Game.tick(0.05)
	var snap: Dictionary = c.snapshot()
	snap.erase("last_active_utc")
	return JSON.stringify(snap)

func replay_suite() -> void:
	var a := _run_once("user://replay_a/")
	var b := _run_once("user://replay_b/")
	check(a == b, "same seed and intents replay to the same character state")
	check(a.length() > 200, "replay produced a real snapshot")

# ------------------------------------------------------------------ offline
func offline_suite() -> void:
	var c = Game.active()
	if c == null:
		check(false, "offline suite needs a character")
		return
	var cu = c.cultivator
	# Seclusion is locked before Bone Forging 7: pretend we are there for the rule checks.
	cu.realm_key = "bone_forging_7"
	Game.progression.apply_learn_method(c.id, "riverbreath_fragment")
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	var before: float = cu.qp
	var r := Game.progression.claim_offline(c, -3600.0)
	check(r.get("ok", false) and near(cu.qp, before), "a backward clock gains nothing")
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	var r12: Dictionary = Game.progression.claim_offline(c, 12.0 * 3600.0)
	var gained_12: float = cu.qp - before
	cu.qp = before
	cu.state = "accumulating"
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	Game.progression.claim_offline(c, 48.0 * 3600.0)
	var gained_48: float = cu.qp - before
	check(gained_12 > 0.0, "offline seclusion accumulates progress (%.1f)" % gained_12)
	check(near(gained_48, gained_12, 0.02) or cu.state == "bottleneck", "offline gains stop at the 12-hour cap")
	# Offline never breaks through: fill to the bottleneck and claim a long absence.
	cu.qp = cu.need() * 0.99
	cu.state = "accumulating"
	var realm_before: String = cu.realm_key
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	Game.progression.claim_offline(c, 12.0 * 3600.0)
	check(cu.realm_key == realm_before, "offline progress never breaks through")
	check(cu.state == "bottleneck" or cu.qp <= cu.need(), "a full bar waits at the bottleneck")
	# Offline factor: realm progress while away is 10% of the meditation rate.
	var rate := ProgressionRules.meditation_rate(c, 1.0, Game.progression.accumulation_bonus(c))
	check(near(float(r12.get("gains", {}).get("qp", 0.0)), rate * float(ContentDB.curve("offline_factor", 0.1)) * 720.0, 0.05), "offline factor 0.1 of the meditation rate")
	Clock.override_utc = -1.0

# ------------------------------------------------------------------ pets (S22)
func pets_suite() -> void:
	var c = Game.active()
	if c == null:
		check(false, "pet suite needs a character")
		return
	c.cultivator.realm_key = "qi_unfurling_5"
	Game.pets.apply_grant(c.id, "reed_otter")
	var p: Dictionary = c.pets[c.pets.size() - 1]
	c.active_pet = str(p.uid)
	check((p.traits as Array).size() == 3 and int(p.revealed) == 0, "a new animal carries three hidden traits")
	# Juvenile: Level 15, 3 hearts, owner at Heart Tempering. Each gate alone is not enough.
	p.level = 15
	p.bond = 1.0
	check(not Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false), "level alone does not evolve")
	p.bond = 3.0
	check(not Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false), "level and hearts without the owner's realm do not evolve")
	c.cultivator.realm_key = "heart_tempering_1"
	p.level = 14
	check(not Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false), "hearts and realm without the level do not evolve")
	p.level = 15
	check(Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false) and str(p.stage) == "juvenile", "all three gates: Hatchling to Juvenile")
	check(int(p.revealed) == 1 and Game.pets.revealed_traits(p).size() == 1, "Juvenile reveals the first trait")
	# Adult needs a branch from the species.
	p.level = 35
	p.bond = 5.0
	c.cultivator.realm_key = "spirit_awakening_1"
	check(Game.submit({"type": "evolve_pet", "pet": p.uid}).get("reason", "") == "choose_branch", "Adult asks for a branch")
	check(Game.submit({"type": "evolve_pet", "pet": p.uid, "branch": "Tide Otter"}).get("ok", false) and str(p.branch) == "Tide Otter", "Adult takes one of the two branches")
	# Resonance: Cultivation role from Spirit Awakening 1, Adult +10%; hunger costs 30%.
	p.role = "cultivation"
	p.hunger_day = Clock.reset_day(Clock.now_utc())
	var fed: float = Game.pets.resonance(c) - Game.pets.trait_bonus(c, "resonance")
	check(near(fed, 0.10), "Adult resonance is +10%% (%.3f)" % fed)
	p.hunger_day = Clock.reset_day(Clock.now_utc()) - 2
	check(near(Game.pets.care_mult(p), 0.7), "a hungry animal works at 70%")
	check(Game.progression.accumulation_bonus(c) >= Game.pets.resonance(c) - 0.0001, "resonance feeds accumulation")
	p.role = "combat"
	check(near(Game.pets.resonance(c), 0.0), "no resonance outside the Cultivation role")
	# Rarity scales strength; breeding pairs two Adults of one family (Heaven Glimpse 1, Beast Pavilion 4).
	p.rarity = "rare"
	check(near(Game.pets.rarity_power(p), 1.25), "a Rare animal is 25% stronger")
	p.rarity = "common"
	Game.pets.apply_grant(c.id, "mossback_toad")
	var toad: Dictionary = c.pets[c.pets.size() - 1]
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets[c.pets.size() - 1]
	toad.stage = "adult"
	fox.stage = "adult"
	toad.rarity = "fine"
	c.eggs.clear()
	var sect_before: Dictionary = Game.account.sect.duplicate(true)
	check(str(Game.pets.breed(c, str(p.uid), str(toad.uid)).get("reason", "")) == "locked", "breeding waits for its unlock")
	Unlocks.force_unlock(c.id, "pet_breeding")
	Game.account.sect = {"name": "Test", "level": 4, "buildings": {"beast_pavilion": 3}}
	check(str(Game.pets.breed(c, str(p.uid), str(toad.uid)).get("text", "")).contains("Beast Pavilion"), "breeding needs Beast Pavilion 4")
	Game.account.sect.buildings.beast_pavilion = 4
	check(str(Game.pets.breed(c, str(p.uid), str(fox.uid)).get("reason", "")) == "not_a_pair", "an otter and a fox are not one family")
	check(Game.pets.breed_partners(c, p).has(toad) and not Game.pets.breed_partners(c, p).has(fox), "otter and toad are both river animals")
	Clock.override_utc = 1900000000.0
	var br: Dictionary = Game.pets.breed(c, str(p.uid), str(toad.uid))
	check(br.get("ok", false) and c.eggs.size() == 1 and c.eggs[0].get("bred", false), "two river Adults make an egg %s" % str(br))
	var egg: Dictionary = c.eggs[0] if not c.eggs.is_empty() else {}
	var order := ["common", "fine", "rare", "epic", "primordial"]
	check(order.find(str(egg.get("rarity", ""))) >= 1, "the child takes at least the higher parent rarity (%s)" % str(egg.get("rarity", "")))
	var parent_traits: Array = (p.traits as Array) + (toad.traits as Array)
	var inherited: int = (egg.get("traits", []) as Array).filter(func(t): return parent_traits.has(t)).size()
	check((egg.get("traits", []) as Array).size() == 3 and inherited >= 2, "its traits come from the parents, at most one new")
	check(float(egg.get("hatch_utc", 0.0)) - Clock.now_utc() >= 26.0 * 3600.0 - 1.0, "breeding takes a day before the egg can hatch")
	check(str(Game.pets.breed(c, str(p.uid), str(toad.uid)).get("reason", "")) == "locked", "one pair at a time")
	check(not Game.pets.hatch_egg(c, 0).get("ok", false), "the egg is not ready yet")
	Clock.override_utc += 49.0 * 3600.0
	var n_before: int = c.pets.size()
	check(Game.pets.hatch_egg(c, 0).get("ok", false) and c.pets.size() == n_before + 1, "the bred egg hatches")
	var child: Dictionary = c.pets[c.pets.size() - 1]
	check(str(child.rarity) == str(egg.get("rarity", "")) and child.traits == egg.get("traits", []), "the hatchling keeps the egg's rarity and traits")
	check(str(child.species) in ["reed_otter", "mossback_toad"], "and one parent's species")
	Clock.override_utc = -1.0
	Game.account.sect = sect_before

# ------------------------------------------------------------------ weekly mission (S20)
func weekly_suite() -> void:
	var c = Game.active()
	if c == null: return
	Game.quest.start_weekly(true)
	var id := "weekly_%d" % Clock.reset_week(Clock.now_utc())
	check(c.quests.is_active(id), "Sect Service is offered for the week")
	Game.quest.start_daily(true)
	check(c.quests.is_active(id), "the daily reset leaves the weekly mission alone")
	# Either path finishes it: here, one field boss.
	GameEvents.emit_event("actor_defeated", {"victim": "0", "victim_kind": "enemy", "def": "cloudpeak_roc", "role": "field_boss", "killer": c.id, "level": 40,
		"room": str(c.position.get("room", "")), "x": 400.0, "y": 800.0, "alt": 0.0, "elite": false, "summoned": false, "first_hit_by_player": true})
	GameEvents.flush()
	check(c.quests.done.has(id) and not c.quests.is_active(id), "a field boss completes Sect Service")
	Game.quest.start_weekly(true)
	check(not c.quests.is_active(id), "Sect Service is offered once a week")

# ------------------------------------------------------------------ pill qualities (S15)
func _pill_stacks(c, id: String) -> Array:
	var out: Array = []
	for i in c.inventory.bag.size():
		var s = c.inventory.bag[i]
		if s != null and str(s.id) == id: out.append(i)
	return out

func _use_fresh(c, index: int) -> Dictionary:
	c.pools.cooldowns.clear()
	c.cultivator.toxicity = 0.0
	c.cultivator.pill_memory.clear()
	return Game.inventory.use_item(c, index, true)

func pills_suite() -> void:
	var c = Game.active()
	if c == null: return
	c.cultivator.realm_key = "heart_tempering_1"
	var pill := "healing_pill"
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	Game.inventory.apply_add(c.id, pill, 2, "test")
	Game.inventory.apply_add(c.id, pill, 2, "test", {"quality": "pill_grain"})
	Game.inventory.apply_add(c.id, pill, 1, "test", {"quality": "pill_grain"})
	var idx := _pill_stacks(c, pill)
	check(idx.size() == 2 and int(c.inventory.bag[idx[1]].count) == 3, "a Pill Grain stacks apart from Common pills")
	check(c.inventory.count(pill) == 5, "the bag counts every quality of a pill")
	check(not c.inventory.bag[idx[0]].has("quality"), "a Common pill is a plain stack (older saves read unchanged)")
	Game.inventory.move_item(c, idx[1], idx[0])
	check(_pill_stacks(c, pill).size() == 2, "moving a Pill Grain onto Common pills swaps instead of merging")
	check(near(InventoryAuthority.pill_potency({"id": pill}), 1.0) and near(InventoryAuthority.pill_potency({"id": pill, "quality": "flawed"}), 0.5)
		and near(InventoryAuthority.pill_potency({"id": pill, "quality": "pill_soul"}), 2.2), "potency: Flawed 50%, Common 100%, Pill Soul 220%")
	var grain := -1
	for i in _pill_stacks(c, pill):
		if str(c.inventory.bag[i].get("quality", "")) == "pill_grain": grain = i
	var used := _use_fresh(c, grain)
	check(near(float(used.get("factor", 0.0)), 1.8), "a Pill Grain works at 180%% (%s)" % str(used))
	check(near(c.cultivator.toxicity, float(ContentDB.item(pill).pill.toxicity) * 0.5), "and leaves half the toxicity")
	Game.inventory.apply_add(c.id, pill, 1, "test", {"quality": "flawed"})
	var flawed := -1
	for i in _pill_stacks(c, pill):
		if str(c.inventory.bag[i].get("quality", "")) == "flawed": flawed = i
	_use_fresh(c, flawed)
	check(near(c.cultivator.toxicity, float(ContentDB.item(pill).pill.toxicity) * 1.5), "a Flawed pill poisons more")
	# Grain, Halo and Soul need every strike perfect, from Heart Tempering 1 (perfect timing).
	Unlocks.force_unlock(c.id, "perfect_timing")
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	check(Game.crafting._rare_pill_quality(c, [0.95, 0.6, 0.95], rng) == "perfect", "one imperfect strike: no rare quality")
	check(Game.crafting._rare_pill_quality(c, [1.0, 1.0], rng) == "perfect", "an unfinished run: no rare quality")
	var got := {}
	for i in 4000:
		var q := Game.crafting._rare_pill_quality(c, [1.0, 0.9, 0.95], rng)
		got[q] = int(got.get(q, 0)) + 1
	var boost: float = 1.0 + Game.crafting.furnace_bonus(c) + 0.1 * int(c.cultivator.daos.get("alchemy", {}).get("tier", 0))
	var rare: Dictionary = ContentDB.config("grades").pill.rare
	check(near(float(got.get("pill_grain", 0)) / 4000.0, float(rare.pill_grain) * boost, 0.03), "a perfect run rolls Pill Grain about %d%% of the time (%s)" % [int(float(rare.pill_grain) * boost * 100), str(got)])
	check(got.has("pill_halo") and got.has("pill_soul") and int(got.get("pill_soul", 0)) < int(got.get("pill_halo", 0)), "Halo is rarer than Grain, Soul rarer still")
	# Pill Halo grows 1% a day in a storage chest in a room of Qi density 2 or more, up to +20% (S44).
	var day := 86400.0
	check(near(InventoryAuthority.halo_now({"quality": "pill_halo", "stored_utc": Clock.now_utc() - 5 * day, "stored_density": 1.0}), 0.0),
		"a Pill Halo stored in thin Qi does not grow")
	check(near(InventoryAuthority.halo_now({"quality": "pill_halo", "stored_utc": Clock.now_utc() - 5.5 * day, "stored_density": 2.2}), 0.05),
		"five days in a dense-Qi chest: Halo +5%")
	check(near(InventoryAuthority.halo_now({"quality": "pill_halo", "stored_utc": Clock.now_utc() - 60 * day, "stored_density": 2.2}), 0.2),
		"Halo growth stops at +20% (240% potency)")
	Unlocks.force_unlock(c.id, "storage")
	var dens0 = Game.room_rt.def.get("qi_density", 1.0)
	Game.room_rt.def.qi_density = 2.2
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	Game.inventory.apply_add(c.id, pill, 1, "test", {"quality": "pill_halo"})
	var n_store: int = Game.account.storage.get("items", []).size()
	check(Game.accounts.deposit(c, _bag_index(c, pill), 1).get("ok", false), "a Halo pill goes into the storage chest")
	Game.room_rt.def.qi_density = dens0
	var stored: Dictionary = Game.account.storage.items[n_store]
	stored.stored_utc = float(stored.stored_utc) - 10 * day
	Game.accounts.withdraw(c, n_store)
	var halo_i := _bag_index(c, pill)
	check(halo_i >= 0 and near(float(c.inventory.bag[halo_i].get("halo", 0.0)), 0.1) and not c.inventory.bag[halo_i].has("stored_utc"),
		"taken out after ten days in the pavilion's chest: Halo +10%")
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	# A Pill Soul always carries its recipe's own unique effect.
	Game.inventory.apply_add(c.id, pill, 8, "test", {"quality": "pill_soul"})
	var awakened := 0
	for n in 8:
		var soul := -1
		for i in _pill_stacks(c, pill):
			if str(c.inventory.bag[i].get("quality", "")) == "pill_soul": soul = i
		if soul < 0: break
		if str(_use_fresh(c, soul).get("soul_effect", "")) != "": awakened += 1
	check(awakened == 8 and str(ContentDB.item(pill).get("soul_effect", "")) == "mend_meridians", "a Healing Pill Soul mends the meridians, every time (%d of 8)" % awakened)
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null

# ------------------------------------------------------------------ natural treasures (Part 5)
func treasures_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu = c.cultivator
	cu.realm_key = "spirit_awakening_8"
	cu.state = "accumulating"
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	c.pools.cooldowns.clear()
	# Mindwell Lotus: +500 Soul, once in each great realm.
	Game.inventory.apply_add(c.id, "mindwell_lotus", 2, "test")
	var soul0: float = cu.soul_cultivation
	check(Game.inventory.use_item(c, c.inventory.first_index("mindwell_lotus"), true).get("ok", false) and near(cu.soul_cultivation, soul0 + 500.0),
		"the Mindwell Lotus adds 500 Soul")
	c.pools.cooldowns.clear()
	check(str(Game.inventory.use_item(c, c.inventory.first_index("mindwell_lotus"), true).get("reason", "")) == "once_per_realm", "a second lotus in the same great realm is refused")
	cu.realm_key = "heaven_glimpse_1"
	c.pools.cooldowns.clear()
	check(Game.inventory.use_item(c, c.inventory.first_index("mindwell_lotus"), true).get("ok", false), "the next great realm, the lotus answers again")
	check(ContentDB.item("mindwell_lotus").get("sell", true) == false and ContentDB.item("evergreen_heart_fruit").get("sell", true) == false, "natural treasures are never sold")
	cu.realm_key = "spirit_awakening_8"
	# Evergreen Heart Tree: planted once, first fruit after a day, then one per season.
	Clock.override_utc = 1800000000.0
	c.crafting.erase("evergreen")
	var plot := {"id": "plot_test", "type": "treasure_plot"}
	check(str(Game.crafting.tend_treasure_plot(c, plot).get("text", "")) == Tx.t("sim.crafting.rich_earth_waits"), "rich earth waits for a seed")
	Game.inventory.apply_add(c.id, "evergreen_heart_seed", 1, "test")
	Game.crafting.tend_treasure_plot(c, plot)
	check(bool(Game.crafting.evergreen_state(c).planted) and c.inventory.count("evergreen_heart_seed") == 0, "the seed is planted")
	Game.crafting.tend_treasure_plot(c, plot)
	check(c.inventory.count("evergreen_heart_fruit") == 0, "no fruit on the first day")
	Clock.override_utc += 25.0 * 3600.0
	Game.crafting.tend_treasure_plot(c, plot)
	Game.crafting.tend_treasure_plot(c, plot)
	check(c.inventory.count("evergreen_heart_fruit") == 1, "one fruit after a day, and only one")
	Clock.override_utc += 7.0 * 86400.0
	Game.crafting.tend_treasure_plot(c, plot)
	check(c.inventory.count("evergreen_heart_fruit") == 2, "another fruit the next season")
	check(str(Game.crafting.tend_treasure_plot(c, {"id": "elsewhere", "type": "treasure_plot"}).get("text", "")).contains("grows in"), "one tree per character")
	# The fruit lifts you from a grave wound where you fell, at full health.
	Game.combat._gravely_wound(c, "hp")
	c.pools.hp = 0.0
	check(Game.combat.choose_revival(c, "fruit").get("ok", false) and near(c.pools.hp, c.pools.max_hp) and c.inventory.count("evergreen_heart_fruit") == 1,
		"an Evergreen Heart fruit revives in place at full health")
	check(not Game.combat.is_wounded(c.id), "and the wound is gone")
	Clock.override_utc = -1.0
	# Nine-Bough Jade Tree: only at an Understanding bottleneck, once per realm stage.
	cu.realm_key = "spirit_awakening_9"
	Unlocks.force_unlock(c.id, "dao_tree")
	cu.daos = {"sword": {"tier": 3, "insight": 900.0}}
	cu.state = "accumulating"
	check(str(Game.progression.consult_jade_tree(c).get("text", "")) == Tx.t("sim.progression.the_jade_leaves_are_still"), "no answer away from a bottleneck")
	cu.state = "bottleneck"
	var jt: Dictionary = Game.progression.consult_jade_tree(c)
	var gained := float(cu.daos.sword.insight) - 900.0
	check(gained >= 0.75 * 1100.0 - 1.0, "at the Dao-tier wall it gives three quarters of the gap to the next tier (%.0f, %s)" % [gained, str(jt)])
	var ins: float = float(cu.daos.sword.insight)
	Game.progression.consult_jade_tree(c)
	check(near(float(cu.daos.sword.insight), ins), "the tree answers once per realm stage")
	cu.state = "accumulating"
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	# Library floor 3 formations (S16): Restraint slows monsters 30%, Concealment hides you.
	var here := str(c.position.get("room", ""))
	var saved: Array = c.crafting.get("formations", []).duplicate(true)
	c.crafting.formations = [{"type": "restraint", "room": here, "until_utc": Clock.now_utc() + 3600.0},
		{"type": "concealment", "room": here, "until_utc": Clock.now_utc() + 3600.0}]
	check(near(Game.workshop.formation_effect(c, "enemy_slow"), 0.3) and Game.workshop.formation_effect(c, "conceal") > 0.0, "Restraint and Concealment take effect where they stand")
	c.crafting.formations[0].until_utc = Clock.now_utc() - 1.0
	check(near(Game.workshop.formation_effect(c, "enemy_slow"), 0.0), "an unfuelled formation does nothing")
	c.crafting.formations = saved

# ------------------------------------------------------------------ hazards (S17)
## Run a hazard to the end of its phase and one tick on.
func _hazard_step(hs: Dictionary) -> void:
	hs.t = float(hs.dur) + 0.01
	Game.tick(0.05)

func _hazard_room(c, room: String, at: Vector2) -> Dictionary:
	Game.world.apply_teleport(c.id, room)
	var st: ActorState = Game.actor_state(c.id)
	for s in Game.room_rt.geometry.surfaces:
		if s.stratum == "ground" and s.contains(at): st.surface = s
	st.plane = at
	st.altitude = 0.0
	Game.combat.cure_status(c.id, "spawn_protection")
	for s in ["stun", "slow", "shock", "bleed", "poison"]: Game.combat.cure_status(c.id, s)
	c.pools.invulnerable = 0.0   # i-frames left over from the revival checks above
	c.pools.hp = c.pools.max_hp
	var hid: String = str(Game.room_rt.def.get("hazards", [""])[0])
	return Game.room_rt.hazards.get(hid, {})

## Pin an attribute for a check (override), or release it (value < 0).
func _answer(c, stat: String, value: float) -> void:
	c.stats.remove_source("test_hazard")
	if value >= 0.0: c.stats.add_modifier({"stat": stat, "op": "override", "value": value, "duration": 600.0, "source": "test_hazard"})
	Game.combat.refresh_stats(c.id)

## Run the cycle round to the start of the next active phase.
func _hazard_to_active(hs: Dictionary, on: Vector2 = Vector2.INF) -> void:
	for i in 5:
		_hazard_step(hs)
		if hs.phase == "tell" and on.is_finite(): hs.spots = [[on.x, on.y, 0.0]] + hs.spots.slice(1)
		if hs.phase == "active": return

func hazards_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	var gust := ContentDB.entry("hazards", "wind_gust")
	check(HazardRules.need(gust, ContentDB.room("gc_windbridge")) == 116, "the Windbridge's gusts ask Body 116 (1.4 x (5 + 78))")
	check(near(HazardRules.effect_scale(0.0, 100.0), 1.0) and near(HazardRules.effect_scale(50.0, 100.0), 0.75) and HazardRules.effect_scale(100.0, 100.0) == 0.0,
		"a hazard's push or status falls to half as the answer nears and stops once it is met")
	check(near(HazardRules.damage_scale(120.0, 100.0), 0.35) and near(HazardRules.damage_scale(0.0, 100.0), 1.0), "an answered strike still lands, at 35%")
	var events: Array = []
	var grab := func(n, p): if str(n).begins_with("hazard_"): events.append([str(n), p])
	GameEvents.event.connect(grab)
	# Falling rocks: a quiet tell, a warning, then the strike on the marked spot.
	var spot := Vector2(900, 820)
	var hs := _hazard_room(c, "sq_quarry_rim", spot)
	_answer(c, "body", 1.0)
	check(hs.get("phase", "") == "cooldown", "hazards start in their cooldown: nothing falls on arrival")
	_hazard_step(hs)
	check(hs.phase == "tell" and hs.spots.size() == 2, "the quiet tell picks two spots")
	hs.spots[0] = [spot.x, spot.y, 0.0]
	_hazard_step(hs)
	GameEvents.flush()
	check(hs.phase == "warn" and events.any(func(e): return e[0] == "hazard_warned"), "a warning comes before the strike")
	var hp0: float = c.pools.hp
	_hazard_step(hs)
	check(hs.phase == "active" and c.pools.hp < hp0 and c.pools.has_status("stun"), "the rock lands on the marked spot and stuns (%.0f)" % (hp0 - c.pools.hp))
	var full_hit: float = (hp0 - c.pools.hp) / c.pools.max_hp   # as a share of max HP: Body also raises max HP
	# Answered: Body over the need, the blow is lighter and nothing stuns.
	_answer(c, "body", 400.0)
	Game.combat.cure_status(c.id, "stun")
	c.pools.hp = c.pools.max_hp
	hp0 = c.pools.hp
	events.clear()
	_hazard_to_active(hs, spot)
	GameEvents.flush()
	var struck: Array = events.filter(func(e): return e[0] == "hazard_struck")
	check(c.pools.hp < hp0 and (hp0 - c.pools.hp) / c.pools.max_hp < full_hit * 0.6 and not c.pools.has_status("stun"), "answered, the rock hurts less and does not stun")
	check(not struck.is_empty() and struck[-1][1].get("answered", false), "the blow is reported as answered")
	_answer(c, "body", 1.0)
	# A dodge through the strike avoids it.
	c.pools.hp = c.pools.max_hp
	hs.phase = "warn"
	hs.spots = [[spot.x, spot.y, 0.0]]
	Game.combat.timeline(c.id).dodge_t = 0.3
	_hazard_step(hs)
	check(near(c.pools.hp, c.pools.max_hp), "a dodge through the strike avoids it")
	Game.combat.timeline(c.id).dodge_t = 0.0
	# Wind gusts push downwind while active, less for a stronger body, not at all once answered.
	hs = _hazard_room(c, "gc_windbridge", Vector2(1500, 820))
	_answer(c, "body", 58.0)
	_hazard_to_active(hs)
	var push := Game.world.hazard_drift(c.id)
	check(near(absf(push.x), 230.0 * 0.75) and signf(push.x) == float(hs.dir), "a gust pushes downwind, three quarters as hard for half the Body (%.0f px/s)" % push.x)
	_answer(c, "body", 400.0)
	Game.tick(0.05)
	check(Game.world.hazard_drift(c.id) == Vector2.ZERO, "an answering Body holds its footing")
	_answer(c, "body", 1.0)
	# The rapids pull downstream in the shallows, harder in a surge.
	hs = _hazard_room(c, "wg_rapids_terraces", Vector2(1500, 920))
	Game.tick(0.05)
	var calm_pull := Game.world.hazard_drift(c.id).x
	_hazard_to_active(hs)
	var surge_pull := Game.world.hazard_drift(c.id).x
	check(calm_pull < 0.0 and surge_pull < calm_pull * 2.0, "the shallows pull downstream, harder in a surge (%.0f, %.0f)" % [calm_pull, surge_pull])
	Game.actor_state(c.id).plane = Vector2(1500, 700)
	Game.tick(0.05)
	check(Game.world.hazard_drift(c.id) == Vector2.ZERO, "out of the water, no pull")
	# Hollow puddles taint and slow whoever stands in them while they rise.
	hs = _hazard_room(c, "rm_grey_pools", Vector2(600, 900))
	_answer(c, "spirit", 1.0)
	var hol: float = c.pools.hollowing
	_hazard_to_active(hs)
	check(c.pools.hollowing > hol and c.pools.has_status("slow"), "a Hollow puddle taints and slows")
	_answer(c, "body", 1.0)
	# Bitter cold slows in the open; a shrine shelters.
	hs = _hazard_room(c, "rf_rimefrost_summit", Vector2(1600, 820))
	_hazard_to_active(hs)
	check(c.pools.has_status("slow"), "the freezing blast stiffens the limbs in the open")
	hs = _hazard_room(c, "rf_rimefrost_summit", Vector2(360, 760))
	_hazard_to_active(hs)
	check(not c.pools.has_status("slow"), "a shrine gives shelter from the cold")
	# Safe rooms never carry hazards; the map lists what a room asks.
	var bad: Array = []
	for id in ContentDB.rooms:
		var r: Dictionary = ContentDB.rooms[id]
		if r.get("safe", false) and not r.get("hazards", []).is_empty(): bad.append(id)
	check(bad.is_empty(), "no hazards in safe rooms %s" % str(bad))
	var sm: Array = HazardRules.summary(c, ContentDB.room("sr_windswept_ridge"))
	check(sm.size() == 1 and str(sm[0].stat) == "body" and int(sm[0].need) == 91, "the map shows the ridge's gusts and the Body they ask (91)")
	GameEvents.event.disconnect(grab)
	_answer(c, "", -1.0)
	for s in ["stun", "slow", "shock", "bleed", "poison"]: Game.combat.cure_status(c.id, s)
	c.pools.hollowing = 0.0
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ the Starsea and Act II systems (v1.1)
func starsea_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	# S18: a dock asks for the Starsea's survival (Sage 3), a vessel and the route's chart, in that order.
	Game.world.apply_teleport(c.id, "ae_skydock")
	check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "wrong_dock", "a route sails only from its own dock")
	Game.world.apply_teleport(c.id, "ae_shipyard")
	var had := Unlocks.is_unlocked(c.id, "starsea")
	if not had: check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "locked", "the Starsea is closed before Sage 3")
	Unlocks.force_unlock(c.id, "starsea")
	check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "no_vessel", "no vessel, no voyage")
	Game.inventory.apply_add(c.id, "cloud_skiff", 1, "test")
	check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "no_chart", "no chart, no voyage")
	Game.inventory.apply_add(c.id, "star_chart_wreck", 1, "test")
	var r := Game.world.set_sail(c, "wreck_run")
	check(r.get("ok", false) and Game.room_rt.room_id == "ss_starsea_crossing" and near(float(Game.room_rt.event.remaining), 70.0, 0.5),
		"a skiff crosses the Wreck Run in 70 s")
	Game.room_rt.event.remaining = 0.01
	Game.tick(0.05)
	GameEvents.flush()
	check(Game.room_rt.room_id == "sw_broken_pier", "the crossing ends in port at the Broken Pier")
	Game.inventory.apply_add(c.id, "storm_sloop", 1, "test")
	r = Game.world.set_sail(c, "wreck_run_home")
	check(r.get("ok", false) and near(float(Game.room_rt.event.remaining), 70.0 / 1.5, 0.5), "a storm sloop crosses half again as fast")
	Game.world.apply_teleport(c.id, "ae_shipyard")
	check(not Game.world.voyages.has(c.id), "leaving the crossing abandons the voyage")
	Game.world.apply_teleport(c.id, "sw_starsea_launch")
	# v1.2: the Lantern Run is charted and open (Act III): the storm sloop crosses it to Lanternfall Harbor.
	var no_chart := Game.world.set_sail(c, "lantern_run")
	check(c.inventory.count("star_chart_lantern") > 0 or str(no_chart.get("reason", "")) != "planned", "the Lantern Run is no longer only planned")
	if c.inventory.count("star_chart_lantern") == 0: Game.inventory.apply_add(c.id, "star_chart_lantern", 1, "test")
	Game.world.apply_teleport(c.id, "sw_starsea_launch")
	r = Game.world.set_sail(c, "lantern_run")
	check(r.get("ok", false) and Game.room_rt.room_id == "ss_lantern_crossing" and near(float(Game.room_rt.event.remaining), 90.0 / 1.5, 0.5),
		"the Lantern Run: a storm sloop crosses in 60 s")
	Game.room_rt.event.remaining = 0.01
	Game.tick(0.05)
	GameEvents.flush()
	check(Game.room_rt.room_id == "lh_arrival_quay" and str(ContentDB.zone_of_room(Game.room_rt.room_id).get("id", "")) == "lantern_star_field",
		"and makes port at Lanternfall, in the Lantern Star Field")
	for k in ["cloud_skiff", "storm_sloop", "star_chart_wreck"]: Game.inventory.apply_remove(c.id, k, 1, "test")
	# The star wind strips Qi; Spirit holds it in.
	if c.pools.max_qi > 0.0:
		var hs := _hazard_room(c, "sw_riven_peak", Vector2(1500, 820))
		hs = Game.room_rt.hazards.get("star_wind", {})
		_answer(c, "spirit", 1.0)
		c.pools.qi = c.pools.max_qi
		_hazard_to_active(hs)
		check(c.pools.qi < c.pools.max_qi * 0.97, "the star wind strips Qi (%.0f%%)" % (100.0 * c.pools.qi / c.pools.max_qi))
		_answer(c, "spirit", 9999.0)
		c.pools.qi = c.pools.max_qi
		_hazard_to_active(hs)
		_hazard_to_active(hs)
		check(near(c.pools.qi, c.pools.max_qi, 1.0), "enough Spirit keeps every drop of it")
		_answer(c, "", -1.0)
	# The Presence of the eight seats is answered by Will (S17 Weight zones).
	var pres := ContentDB.entry("hazards", "presence")
	check(str(pres.answer) == "will" and HazardRules.need(pres, ContentDB.room("si_presence_trial")) == 189, "the Presence Trial asks Will 189 (2.2 x (5 + 81))")
	# S18: an Expanse Outpost lends every member of the sect its Storm Ward.
	var saved: Dictionary = Game.account.sect.duplicate(true)
	var base := Game.progression.attunement_value(c, "azure_expanse")
	Game.account.sect = {"level": 8, "buildings": {"expanse_outpost": 3}, "damaged": {}}
	check(near(Game.progression.attunement_value(c, "azure_expanse") - base, 3.0), "an Expanse Outpost at level 3 adds 3 Storm Ward")
	check(Game.sect.outpost_attunement("jade_river_valley") == 0.0, "and nothing in the valley")
	Game.account.sect = saved
	# Paired cultivation only while meditating.
	check(Game.companions.paired_bonus(c) == 0.0, "no paired bonus while not meditating")
	# Rare Daos: closed until a teacher opens them; each tier adds its modifiers. Zone caps: the Expanse's Laws go deeper.
	Game.world.apply_teleport(c.id, "ae_landing")
	Unlocks.force_unlock(c.id, "dao_tree")
	var daos_saved: Dictionary = c.cultivator.daos.duplicate(true)
	c.cultivator.daos.erase("blood")
	Game.progression.apply_insight(c.id, "blood", 500.0, "test:blood:a")
	check(not c.cultivator.daos.has("blood"), "a rare Dao cannot be contemplated before a teacher opens it")
	StatRules.rebuild(c)
	var hp0: float = c.stats.value("max_hp")
	Game.progression.apply_open_dao(c.id, "blood")
	StatRules.rebuild(c)
	check(int(c.cultivator.daos.get("blood", {}).get("tier", 0)) == 1 and c.stats.value("max_hp") > hp0 * 1.04,
		"a teacher opens the Blood Dao at tier 1: +5%% max HP (%.0f -> %.0f)" % [hp0, c.stats.value("max_hp")])
	Game.world.apply_teleport(c.id, "lf_village")
	c.cultivator.daos["thunder"] = {"tier": 0, "insight": 0.0}
	Game.progression.apply_insight(c.id, "thunder", 3000.0, "test:thunder:valley")
	var valley_tier := int(c.cultivator.daos.thunder.tier)
	Game.world.apply_teleport(c.id, "ae_landing")
	Game.progression.apply_insight(c.id, "thunder", 10.0, "test:thunder:expanse")
	check(valley_tier == 2 and int(c.cultivator.daos.thunder.tier) == 4, "the Thunder Dao stops at tier 2 in the valley and deepens in the Expanse (%d, %d)" % [valley_tier, int(c.cultivator.daos.thunder.tier)])
	c.cultivator.daos = daos_saved
	StatRules.rebuild(c)
	# The Elder's token (Sage Sovereign 1): home to the training sect for no shards.
	if not c.training_sect.is_empty():
		var sid := str(c.training_sect.id)
		var stone := "jade_academy" if sid == "jade_sect" else "cloud_monastery"
		var fee := Game.world.teleport_fee(stone, c)
		Game.apply_effects(c.id, [{"kind": "upgrade_sect_token"}], "test")
		check(fee > 0 and Game.world.teleport_fee(stone, c) == 0, "an Elder's token calls its bearer home for free")
		Game.inventory.apply_remove(c.id, sid.replace("_sect", "") + "_elder_token", 1, "test")
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ world movement (S17, S30)
## Run the real solver: the body leaves the ground with `jumps` presses (the second at the top of the
## first) while drifting toward `toward`; returns the surface it comes to rest on.
func _jump_to(geo: ZoneGeometry, from: Vector2, toward: Vector2, jumps: int) -> ActorState:
	var st := ActorState.new()
	st.plane = from
	st.surface = geo.landing_target(from, 1.0, -1.0)
	st.altitude = 0.0
	MovementSolver.jump(st)
	var pressed := 1
	for i in 240:
		var v := (toward - st.plane).limit_length(1.0) * 205.0 if st.plane.distance_to(toward) > 4.0 else Vector2.ZERO
		MovementSolver.advance(st, geo, 1.0 / 60.0, v)
		if pressed < jumps and st.surface == null and st.vertical_speed <= 0.0:
			MovementSolver.jump(st)
			pressed += 1
		if st.surface != null and i > 5: break
	return st

func movement_suite() -> void:
	var c = Game.active()
	if c == null: return
	var back := str(c.position.get("room", "lf_village"))
	check(near(MovementSolver.JUMP_IMPULSE * MovementSolver.JUMP_IMPULSE / (2.0 * MovementSolver.GRAVITY), 122.1, 0.5),
		"a single jump peaks at 122 units; Cloud Ladder Step adds 80 (about 202)")
	# A field made climbable: a jump onto the low ledge, a double jump onto the high one (where the chest waits).
	Game.world.apply_teleport(c.id, "tp_thunderhorn_flats")
	var geo: ZoneGeometry = Game.room_rt.geometry
	var low: WalkSurface = geo.index.get("ledge_mv_0")
	var high: WalkSurface = geo.index.get("ledge_mv_1")
	check(low != null and high != null and geo.index.has("cloud_mv"), "the Thunderhorn Flats have ledges and a cloud ledge")
	if low and high:
		var under := Vector2(low.bounds.get_center().x, low.bounds.end.y + 30.0)
		var st1 := _jump_to(geo, under, low.bounds.get_center(), 1)
		check(st1.surface == low and near(st1.altitude, 100.0, 0.5), "one jump lands on the 100-unit ledge (%s)" % (st1.surface.id if st1.surface else "air"))
		var st1b := _jump_to(geo, Vector2(high.bounds.get_center().x, high.bounds.end.y + 30.0), high.bounds.get_center(), 1)
		check(st1b.surface == null or st1b.surface != high, "one jump does not reach the 176-unit ledge")
		var st2 := _jump_to(geo, Vector2(high.bounds.get_center().x, high.bounds.end.y + 30.0), high.bounds.get_center(), 2)
		check(st2.surface == high and near(st2.altitude, 176.0, 0.5), "a double jump reaches it (%s)" % (st2.surface.id if st2.surface else "air"))
		var chest: Dictionary = Game.room_rt.object_def("chest_ledge_mv_1")
		check(not chest.is_empty() and float(chest.get("alt", 0)) >= high.base - 1.0, "the chest waits up high (on the room's highest tier, S43)")
		var cloud: WalkSurface = geo.index.get("cloud_mv")
		var st3 := _jump_to(geo, Vector2(cloud.bounds.get_center().x, cloud.bounds.end.y + 30.0), cloud.bounds.get_center(), 2)
		check(st3.surface != cloud, "the cloud ledge is above double-jump reach: it is for fliers")
	# A standable crate on the Skydock's yard.
	Game.world.apply_teleport(c.id, "ae_shipyard")
	geo = Game.room_rt.geometry
	var crate_top: WalkSurface = null
	for srf in geo.surfaces:
		if srf.kind == "support" and srf.id.begins_with("crate_"): crate_top = srf
	check(crate_top != null, "a crate in the yard has a top to stand on")
	if crate_top:
		var st4 := _jump_to(geo, crate_top.bounds.get_center() + Vector2(0, 40), crate_top.bounds.get_center(), 1)
		check(st4.surface == crate_top, "a jump lands on the crate (%s)" % (st4.surface.id if st4.surface else "air"))
	# Wall-Step: in the air, pushing into a building's facade, there is a wall to kick off (S43).
	Game.world.apply_teleport(c.id, "lf_village")
	geo = Game.room_rt.geometry
	var roof: WalkSurface = geo.index.get("old_ma_store")
	if roof:
		var st5 := ActorState.new()
		st5.plane = Vector2(roof.bounds.position.x - 8.0, roof.bounds.end.y - 20.0)
		st5.altitude = 60.0
		st5.air_stratum = "ground"
		st5.jumps_used = 2
		var side := MovementSolver.wall_step(st5, geo, 1)
		check(side == 1 and near(st5.vertical_speed, 450.0), "Wall-Step kicks off the store's facade (within 12 units, pushing in)")
		check(MovementSolver.wall_step(st5, geo) == 0, "not without pushing into the wall")
		var st6 := ActorState.new()
		st6.plane = Vector2(roof.bounds.position.x - 200.0, roof.bounds.end.y - 20.0)
		st6.altitude = 60.0
		check(MovementSolver.wall_step(st6, geo, 1) == 0, "no wall, no kick")
	# The rooms: count how many give the jump something to do.
	var flat: Array = []
	for rid in ContentDB.rooms:
		var def: Dictionary = ContentDB.room(rid)
		var up := false
		for srf in def.get("surfaces", []):
			if str(srf.get("stratum", "")) == "platform" or str(srf.get("kind", "")) in ["roof", "stairs", "ladder"]: up = true
		for sc in def.get("scenery", []):
			if sc.get("standable", false) or float(sc.get("height", 999)) <= 80.0: up = true
		if not up and not str(def.get("type", "")) in ["interior", "insight", "home", "story", "event", "sect"]: flat.append(rid)
	check(flat.size() <= 3, "fields, towns and dungeons all have something to climb %s" % str(flat))
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ what pills cost (gap report G1)
func _bag_index(c, id: String) -> int:
	for i in c.inventory.bag.size():
		if c.inventory.bag[i] != null and str(c.inventory.bag[i].id) == id: return i
	return -1

func g1_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var back := str(c.position.get("room", "lf_village"))
	cu.realm_key = "heart_tempering_3"
	cu.state = "accumulating"
	cu.qp = 0.0
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	# Lifetime resistance (S44): every 5 doses of a family add 1 to its count; a pill works at 1 / (1 + 0.25 x count).
	cu.pill_resistance.clear()
	check(ProgressionRules.pill_family(ContentDB.item("qi_gathering_pill")) == "accumulation" and ProgressionRules.pill_family(ContentDB.item("healing_pill")) == ""
		and ProgressionRules.pill_family(ContentDB.item("foundation_guard_pill")) == "support", "pill families come from data; healing pills are exempt")
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 6, "test")
	var factors: Array = []
	for i in 6: factors.append(snappedf(float(_use_fresh(c, _bag_index(c, "qi_gathering_pill")).get("factor", 0)), 0.01))
	check(factors == [1.0, 1.0, 1.0, 1.0, 1.0, 0.8], "five Qi pills at full strength, the sixth at 80%% (%s)" % str(factors))
	check(ProgressionRules.resistance_count(cu, "accumulation") == 1 and int(cu.pill_resistance.accumulation.doses) == 1, "count 1 and one dose toward the next")
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 1, "test", {"quality": "pill_grain"})
	var rg := _use_fresh(c, _bag_index(c, "qi_gathering_pill"))
	check(near(float(rg.get("factor", 0)), InventoryAuthority.pill_potency({"quality": "pill_grain"})) and int(cu.pill_resistance.accumulation.doses) == 1,
		"a Pill Grain ignores lifetime resistance and adds no dose")
	cu.pill_resistance.accumulation.count = 3
	Game.progression._advance(c, "heart_tempering_4", true)
	check(ProgressionRules.resistance_count(cu, "accumulation") == 1, "a major breakthrough: count 3 drops by 1, then halves (1)")
	var old := CultivatorState.new()
	old.restore({"pill_resistance": {"qi": 7}, "foundation": {"realm": "heart_tempering", "total": 10.0, "pill": 4.0}, "support_fails": {"x": {"a": 1, "b": 2}}})
	check(old.pill_resistance.get("accumulation", {}).get("count", -1) == 1 and int(old.pill_resistance.accumulation.doses) == 2
		and near(float(old.foundation.pill_qp), 4.0) and int(old.support_failures.get("x", 0)) == 2, "a version 4 save migrates to the v2 shapes")
	# Raw herbs: weak and poisonous, and they count toward resistance.
	cu.realm_key = "heart_tempering_3"
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 1, "test")
	var raw_i := _bag_index(c, "riverreed_ginseng_10")
	c.pools.cooldowns.clear()
	check(str(Game.inventory.use_item(c, raw_i, false).get("reason", "")) == "confirm", "eating a herb raw asks first")
	_use_fresh(c, raw_i)
	check(near(cu.toxicity, 20.0) and int(cu.pill_resistance.accumulation.doses) == 2, "a raw ginseng root: toxicity 20, one more accumulation dose")
	# Residue: 5% of toxicity stays; each 10 costs 1% accumulation.
	cu.residue = 0.0
	Game.progression.apply_toxicity(c.id, 100.0)
	check(near(cu.residue, 5.0) and near(ProgressionRules.residue_penalty(cu), 0.0), "100 toxicity leaves 5 residue (no penalty yet)")
	Game.progression.apply_toxicity(c.id, 300.0)
	check(near(ProgressionRules.residue_penalty(cu), 0.02), "20 residue: accumulation -2%")
	Game.apply_effects(c.id, [{"kind": "add_toxicity", "amount": -1000}], "test")
	check(near(cu.residue, 20.0), "a Purging Pill does not touch residue")
	cu.toxicity = 0.0
	c.inventory.bag.fill(null)
	# Foundation: Qi from pills beyond 30% of the great realm leaves it hollow.
	cu.realm_key = "heart_tempering_9"
	cu.foundation = {}
	Game.progression.apply_progress(c.id, cu.need() * 0.2, "meditation")
	check(not ProgressionRules.foundation_hollow(cu), "meditated Qi keeps the foundation sound")
	Game.progression.apply_progress(c.id, cu.need() * 0.5, "item:qi_gathering_pill")
	check(ProgressionRules.foundation_hollow(cu) and near(ProgressionRules.foundation_share(cu), 0.5 / 0.7, 0.02), "pill Qi past 30%% of the realm's Qi leaves it hollow (%.2f)" % ProgressionRules.foundation_share(cu))
	var q := Game.progression.query_breakthrough(c)
	var hollow_row := false
	for row in q.results:
		if str(row.get("kind", "")) == "foundation" and not row.ok and not row.hard: hollow_row = true
	check(q.get("hollow", false) and hollow_row, "a major breakthrough counts a hollow foundation as an unmet soft requirement")
	c.seclusion = {"spot": "", "focus": "settle_foundation", "started_utc": 0.0, "cap_h": 12, "density": 1.0}
	var settled := Game.progression.claim_offline(c, 9 * 3600.0)
	check(not ProgressionRules.foundation_hollow(cu) and near(cu.residue, 0.0) and float(settled.gains.get("foundation", 0)) > 0.0,
		"nine hours settling (5 points and 5 residue an hour) make the foundation sound and burn off the residue (%.2f)" % ProgressionRules.foundation_share(cu))
	# Heart demons: a changed method feeds them; each 25 is a risk step; Calm Incense clears them.
	cu.heart_demon = 0.0
	cu.methods_known = ["riverbreath_fragment", "jade_current_scripture"]
	cu.method_id = "riverbreath_fragment"
	Game.progression.switch_method(c, "jade_current_scripture", false)
	check(near(cu.heart_demon, 10.0), "switching method feeds the heart demon (+10)")
	Game.progression.apply_heart_demon(c.id, 45.0, "test")
	var q2 := Game.progression.query_breakthrough(c)
	check(int(q2.get("heart_demon_steps", 0)) == 2, "55 heart demon is two risk steps at a major breakthrough")
	check(ProgressionRules.risk_index(0, false, 0, 0, false, 2) == 2 and ProgressionRules.risk_index(0, false, 0, 0, false, -1) == 0, "risk steps add and merit subtracts, within Low..Severe")
	Game.inventory.apply_add(c.id, "myriad_year_calm_incense", 1, "test")
	_use_fresh(c, _bag_index(c, "myriad_year_calm_incense"))
	check(near(cu.heart_demon, 35.0), "Myriad-Year Calm Incense clears 20")
	# Karma: merit eases one breakthrough per great realm; sin feeds the demon; the back room is a sin.
	var rel: RelationsState = c.relations
	rel.merit = 0
	rel.merit_used.clear()
	Game.apply_effects(c.id, [{"kind": "add_merit", "amount": 100, "reason": "test"}], "test")
	check(ProgressionRules.merit_step(c) == 1 and int(Game.progression.query_breakthrough(c).get("merit", 0)) == 1, "100 merit eases a great breakthrough")
	rel.merit_used[ProgressionRules.great_realm(cu.realm_key)] = true
	check(ProgressionRules.merit_step(c) == 0, "once in each great realm")
	var hd0 := cu.heart_demon
	Game.apply_effects(c.id, [{"kind": "add_sin", "amount": 30, "reason": "test"}], "test")
	check(rel.sin >= 30 and near(cu.heart_demon, hd0 + 3.0), "sin feeds the heart demon (+1 per 10 sin)")
	Game.quest.apply_flag(c.id, "path_independent")
	Unlocks.force_unlock(c.id, "shop")
	Game.economy.apply_currency("spirit_stone", 100, "test")
	var sin0: int = rel.sin
	var bought := Game.economy.buy(c, "free_market", "manual_page", 1, -1)
	GameEvents.flush()
	check(bought.get("ok", false) and rel.sin == sin0 + 2, "Broker Mu's back room stains the ledger (+2 sin) %s" % str(bought.get("reason", "")))
	# A named debt comes due as a letter.
	var mails0: int = Game.account.mail.size() if Game.account.get("mail") is Array else 0
	Game.apply_effects(c.id, [{"kind": "record_debt", "id": "test_debt", "due_h": 0.0, "mail": "gu_repays", "attachments": [{"currency": "spirit_stone", "amount": 1}]}], "test")
	Game.relations.debt_clock = 0.0
	Game.relations.tick(0.1)
	check(bool(rel.debts.get("test_debt", {}).get("paid", false)), "a debt that falls due is repaid by letter")
	rel.debts.erase("test_debt")
	# Furnace and fire (S44): the furnace slot holds one furnace instance; the bronze one holds three; charcoal stops
	# at Perfect; a named furnace or a flame reaches Soul.
	Unlocks.force_unlock(c.id, "alchemy")
	c.inventory.furnace = null
	c.inventory.bag.fill(null)
	Game.inventory.apply_add(c.id, "bronze_furnace", 1, "test")
	var fu: Dictionary = Game.crafting.furnace_of(c)
	check(str(fu.id) == "bronze_furnace" and int(fu.batch) == 3 and c.inventory.furnace != null and c.inventory.furnace.has("uid"),
		"the first furnace goes into the empty furnace slot, three to a batch")
	check(near(float(fu.get("yield", 1.0)), 0.0) and near(float(fu.get("filter", 1.0)), 0.0), "the bronze furnace has no filter and no extra pill")
	check(Game.crafting.rare_allowed(fu, "charcoal").is_empty() and Game.crafting.rare_allowed(fu, "earth_fire") == ["pill_grain"]
		and "pill_soul" in Game.crafting.rare_allowed(fu, "heavenly_flame"), "charcoal stops at Perfect, Earth Fire reaches Grain, a Heavenly Flame reaches Soul")
	check("pill_soul" in Game.crafting.rare_allowed(ContentDB.item("nine_dragon_cauldron").furnace, "charcoal"), "the Nine-Dragon Cauldron reaches Soul on any fire")
	var nd: Dictionary = ContentDB.item("nine_dragon_cauldron").furnace
	check(int(nd.batch) == 8 and near(float(nd.band), 0.12) and str(nd.get("element", "")) == "water", "the Nine-Dragon Cauldron: eight a batch, +12% heat, Water")
	check(str(ContentDB.room("ds_abbots_sanctum").get("objects", []).filter(func(o): return str(o.get("id", "")) == "vault")[0].get("loot", "")) == "abbots_vault"
		and ContentDB.entry("loot_tables", "abbots_vault").get("guaranteed", []).any(func(g): return str(g.item) == "nine_dragon_cauldron"),
		"the Nine-Dragon Cauldron waits in the Drowned Abbot's sealed vault")
	var batch_try := Game.crafting.craft(c, "healing_pill", 4, [], "alchemy")
	check(str(batch_try.get("reason", "")) == "batch", "a bronze furnace refuses a batch of four")
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var any_rare := false
	for i in 400:
		if Game.crafting._rare_pill_quality(c, [1.0, 1.0, 1.0], rng, []) != "perfect": any_rare = true
	check(not any_rare, "no rare quality ever comes out of charcoal")
	# A better furnace sits in the bag until you set it; enhancement steadies its heat 1% a level.
	Game.inventory.apply_add(c.id, "jadeiron_furnace", 1, "test")
	check(str(Game.crafting.furnace_of(c).id) == "bronze_furnace", "a second furnace waits in the bag")
	var jf: int = _bag_index(c, "jadeiron_furnace")
	check(Game.submit({"type": "equip", "index": jf}).get("ok", false) and str(Game.crafting.furnace_of(c).id) == "jadeiron_furnace"
		and c.inventory.count("bronze_furnace") == 1, "setting a furnace swaps the old one back into the bag")
	check(near(Game.crafting.band_mult(c, "beast_fire"), 1.2), "Beast Fire in a Jadeiron Furnace widens the band by 20%")
	c.inventory.furnace.enhance = 3
	check(near(float(Game.crafting.furnace_of(c).band), 0.08), "a +3 Jadeiron Furnace holds its heat 3%% steadier (%.2f)" % float(Game.crafting.furnace_of(c).band))
	c.inventory.furnace.enhance = 0
	# The filter takes out its share of each miss; a furnace of the pill's element adds 5%.
	check(str(ContentDB.entry("recipes", "qi_refining_pill").get("element", "")) == "water", "Qi Refining is a Water pill")
	var qr := ContentDB.entry("recipes", "qi_refining_pill")
	var base_q: float = Game.crafting.quality_score(c, "alchemy", {}, qr, [0.5, 0.5, 0.5])
	check(near(Game.crafting.quality_score(c, "alchemy", Game.crafting.furnace_of(c), qr, [0.5, 0.5, 0.5]) - base_q, 0.05),
		"a Jadeiron Furnace strains out a tenth of each miss (+0.05 on half-missed strikes)")
	check(near(Game.crafting.quality_score(c, "alchemy", ContentDB.item("nine_dragon_cauldron").furnace, qr, [0.5, 0.5, 0.5]) - base_q, 0.15),
		"the Nine-Dragon Cauldron: a fifth of each miss, and +5% for a Water pill")
	# Durability: a cracked furnace refines nothing until it is mended at a forge.
	c.inventory.furnace.durability = 0
	check(Game.crafting.furnace_of(c).get("cracked", false) and str(Game.crafting.craft(c, "healing_pill", 1, [], "alchemy").get("reason", "")) == "cracked",
		"a cracked furnace refuses to refine")
	var mend := Game.crafting.mend_cost(c.inventory.furnace)
	check(str(mend.metal) == "jadeiron" and int(mend.count) == 20, "mending a Jadeiron Furnace from nothing takes 20 jadeiron")
	c.inventory.furnace.durability = 100
	# Beast Fire burns a core of rank 2 or more; a Pebble Imp's core is too weak.
	for k in 4:
		var old_core: int = _bag_index(c, "pebble_core")
		if old_core < 0: break
		c.inventory.bag[old_core] = null
	check(not "beast_fire" in Game.crafting.fires_available(c), "no core, no Beast Fire")
	Game.inventory.apply_add(c.id, "pebble_core", 1, "test")
	check(not "beast_fire" in Game.crafting.fires_available(c), "a rank-1 Pebble Core is too weak for Beast Fire")
	Game.inventory.apply_add(c.id, "serpent_core", 1, "test")
	check("beast_fire" in Game.crafting.fires_available(c) and Game.crafting._core_to_burn(c) == "serpent_core", "a rank-2 core lights Beast Fire")
	# Old saves: furnaces in the key-item pouch become furnace instances, the best in the slot.
	var inv2 := InventoryState.new()
	inv2.restore({"bag": [], "key_items": [{"id": "bronze_furnace", "count": 1}, {"id": "earth_vein_furnace", "count": 1}, {"id": "old_pickaxe", "count": 1}]})
	check(inv2.furnace != null and str(inv2.furnace.id) == "jadeiron_furnace" and inv2.count("bronze_furnace") == 1 and inv2.count("old_pickaxe") == 1,
		"an old save's furnaces become instances: the Jadeiron in the slot, the bronze in the bag")
	# The valley's Heavenly Flame rides the Forgotten Monastery's elite Weeping Lantern.
	check((ContentDB.entry("enemies", "weeping_lantern").get("elite_first_defeat", []) as Array).has("mist_lantern_flame")
		and not (ContentDB.entry("enemies", "drowned_abbot").get("first_defeat", []) as Array).has("cold_lamp_flame"),
		"the Mist Lantern Flame comes from the Weeping Lantern elite")
	c.inventory.bag.fill(null)
	Game.world.apply_teleport(c.id, "wg_rapids_terraces")
	var vent: Dictionary = Game.room_rt.object_def("earth_vent_wg")
	check(not vent.is_empty(), "Whitewater Gorge has an Earth Fire vent")
	if not vent.is_empty():
		Game.actor_state(c.id).plane = Vector2(float(vent.at[0]) + 60.0, float(vent.at[1]))
		check("earth_fire" in Game.crafting.fires_available(c) and Game.crafting.station_near(c, ["alchemy_furnace", "earth_vent"]),
			"at the vent: Earth Fire, and the vent serves as a furnace")
	# Pill marks: a Pill Soul carries all nine; each is +2%.
	check(Game.crafting._roll_marks("pill_soul", rng) == 9 and Game.crafting._roll_marks("flawed", rng) == 0, "marks: Soul nine, Flawed none")
	check(near(InventoryAuthority.pill_potency({"quality": "common", "marks": 5}), 1.1), "five marks: +10%")
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 2, "test", {"quality": "fine", "marks": 3})
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 1, "test", {"quality": "fine"})
	var marked = c.inventory.bag[_bag_index(c, "qi_gathering_pill")]
	check(int(marked.get("marks", 0)) == 3 and int(marked.count) == 2, "a refined stack keeps its gold marks, apart from an unmarked one")
	# A Heavenly Flame is absorbed once; a second copy gutters into Spirit Stones.
	c.crafting["flames"] = []
	Game.inventory.apply_add(c.id, "cold_lamp_flame", 2, "test")
	var fr := Game.inventory.use_item(c, _bag_index(c, "cold_lamp_flame"), true)
	check(fr.get("ok", false) and (c.crafting.flames as Array).has("cold_lamp_flame") and Game.account.codex.has("cold_lamp_flame"),
		"the Cold Lamp Flame is absorbed and entered in the Codex")
	check("heavenly_flame" in Game.crafting.fires_available(c), "an absorbed flame burns under any furnace")
	var ss0: int = Game.economy.balance("spirit_stone")
	Game.inventory.use_item(c, _bag_index(c, "cold_lamp_flame"), true)
	check(Game.economy.balance("spirit_stone") == ss0 + 20, "a second copy gutters into 20 Spirit Stones")
	# The Reflection brings a heart demon for every 25.
	var ev: Dictionary = ContentDB.room("si_trial_of_reflections").get("event", {})
	check(str(ev.get("heart_demons", "")) == "heart_demon" and ContentDB.has_entry("enemies", "heart_demon"), "the Trial of Reflections summons heart demons")
	check((ev.get("on_complete", []) as Array).any(func(e): return str(e.get("kind", "")) == "add_heart_demon" and int(e.get("amount", 0)) == -30),
		"passing the Heart Trial clears 30 heart demon")
	var cleansing := ContentDB.entry("set_pieces", "heavens_cleansing")
	check(str(cleansing.get("room_event", {}).get("on_flawless", [{}])[0].get("kind", "")) == "clear_residue", "a flawless Heaven's Cleansing clears residue")
	c.inventory.bag.fill(null)
	cu.heart_demon = 0.0
	cu.residue = 0.0
	cu.foundation = {}
	cu.pill_resistance.clear()
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ treasures, throwables, talismans, vessels (gap report G2)
func _g2_foe(def_id: String, at: Vector2, boss := false) -> EnemyState:
	var e: EnemyState = Game.enemies.spawn_at(def_id, at, 12)
	if e != null and boss: e.role = "field_boss"
	return e

func _g2_ready(c) -> void:
	Game.room_rt.enemies.clear()
	Game.room_rt.projectiles.clear()
	Game.combat.treasure_fx.clear()
	c.pools.cooldowns.clear()
	c.pools.qi = c.pools.max_qi
	c.pools.hp = c.pools.max_hp * 0.5

func g2_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	var events: Array = []
	var grab := func(n, p): events.append([str(n), p])
	GameEvents.event.connect(grab)
	Game.world.apply_teleport(c.id, "bg_whispering_bamboo")
	for st_id in ["stun", "slow", "shock", "spawn_protection"]: Game.combat.cure_status(c.id, st_id)
	var here: Vector2 = Game.actor_state(c.id).plane
	Game.combat.timeline(c.id).facing = 1
	var realm0: String = c.cultivator.realm_key
	c.cultivator.realm_key = "heart_tempering_5"
	Game.combat.refresh_stats(c.id)
	c.inventory.bag.fill(null)
	var treasures := ["bronze_bell", "little_pagoda", "bright_mirror", "mountain_seal", "taming_cauldron", "wisp_banner", "sealing_gourd"]
	for id in treasures: Game.inventory.apply_add(c.id, id, 1, "test")
	# Two Treasure buttons: the first at Heart Tempering 1 with "A Treasure in Hand", the second at Spirit Awakening 1.
	var tu := ContentDB.entry("unlocks", "treasures")
	check(str(tu.get("reveals", [""])[0]) == "hud:treasure_1" and str(tu.get("quest", "")) == "a_treasure_in_hand" and ContentDB.has_entry("unlocks", "treasure_slot_2"),
		"the Treasure buttons are unlocks that reveal HUD buttons; the first comes with A Treasure in Hand")
	var tq: Dictionary = ContentDB.entry("quests", "a_treasure_in_hand")
	check(str(tq.get("on_accept", [{}])[0].get("item", "")) == "practice_bell" and near(float(CombatAuthority.treasure_of("practice_bell").get("stun_s", 0)), 0.5)
		and int(CombatAuthority.treasure_of("practice_bell").get("qi", 0)) == 15, "the Practice Bell: stun 0.5 s for 15 QI, given on acceptance")
	Unlocks.force_unlock(c.id, "treasures")
	Unlocks.force_unlock(c.id, "treasure_slot_2")
	var r := Game.submit({"type": "set_treasure", "slot": 0, "item": "bronze_bell"})
	check(r.get("ok", false) and c.inventory.treasures[0] == "bronze_bell", "the Bronze Bell sits in Treasure 1")
	Game.submit({"type": "set_treasure", "slot": 1, "item": "bronze_bell"})
	check(c.inventory.treasures == ["", "bronze_bell"], "set in Treasure 2, it leaves Treasure 1")
	check(str(Game.submit({"type": "set_treasure", "slot": 0, "item": "iron_needles"}).get("reason", "")) == "not_a_treasure", "only a treasure art fits a Treasure button")
	# The Bronze Bell: stun 1 s and Qi Seal 3 s within 150; a boss keeps its feet.
	_g2_ready(c)
	var a := _g2_foe("bamboo_monkey", here + Vector2(80, 0))
	var b := _g2_foe("bamboo_monkey", here + Vector2(-120, 10))
	var far := _g2_foe("bamboo_monkey", here + Vector2(600, 0))
	var boss := _g2_foe("ember_fox", here + Vector2(60, -10), true)
	var qi0: float = c.pools.qi
	r = Game.submit({"type": "use_treasure", "slot": 1})
	check(r.get("ok", false) and int(r.get("targets", 0)) == 3, "the bell reaches everyone within 150 (%s)" % str(r.get("targets", r.get("reason", ""))))
	check(a.pools.has_status("stun") and b.pools.has_status("stun") and not far.pools.has_status("stun"), "foes close by are stunned; a far one is not")
	check(not boss.pools.has_status("stun") and boss.pools.has_status("qi_seal"), "a boss is not stunned, only Qi-sealed")
	check(near(qi0 - c.pools.qi, 30.0), "the bell costs 30 QI (%.1f)" % (qi0 - c.pools.qi))
	check(str(Game.submit({"type": "use_treasure", "slot": 1}).get("reason", "")) == "cooldown", "then it rests for 20 s")
	c.pools.cooldowns.clear()
	c.pools.qi = 20.0
	check(str(Game.submit({"type": "use_treasure", "slot": 1}).get("reason", "")) == "no_qi", "without the Qi it stays silent")
	# From Spirit Awakening 1 a treasure also draws on the Soul: a third of its QI cost.
	c.cultivator.realm_key = "spirit_awakening_1"
	Game.combat.refresh_stats(c.id)
	_g2_ready(c)
	if c.pools.max_soul <= 0.0: c.pools.set_max("soul", 300.0)   # the Soul pool opens with the SA1 unlock
	c.pools.soul = c.pools.max_soul
	var soul0: float = c.pools.soul
	Game.submit({"type": "use_treasure", "slot": 1})
	check(c.pools.max_soul > 0.0 and near(soul0 - c.pools.soul, 10.0), "at Spirit Awakening the bell also costs 10 Soul (%.1f)" % (soul0 - c.pools.soul))
	c.cultivator.realm_key = "heart_tempering_5"
	Game.combat.refresh_stats(c.id)
	# The Little Pagoda: a prison for one foe (an elite first), never a boss.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "little_pagoda"})
	_g2_foe("ember_fox", here + Vector2(60, 0), true)
	check(str(Game.submit({"type": "use_treasure", "slot": 0}).get("reason", "")) == "immune" and c.pools.cooldown("treasure:little_pagoda") == 0.0
		and near(c.pools.qi, c.pools.max_qi), "the pagoda cannot hold a boss, and a failed throw costs nothing")
	var small := _g2_foe("bamboo_monkey", here + Vector2(40, 0))
	r = Game.submit({"type": "use_treasure", "slot": 0})
	var held := false
	for st in small.pools.statuses: if st.id == "stun" and near(float(st.remaining), 4.0): held = true
	check(r.get("ok", false) and held, "the nearest foe is held for 4 s")
	# The Bright Mirror sends an arrow back at the archer.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "bright_mirror"})
	var archer := _g2_foe("bandit_archer", here + Vector2(200, 0))
	archer.facing = -1
	Game.submit({"type": "use_treasure", "slot": 0})
	var hp_c: float = c.pools.hp
	var hp_a: float = archer.pools.hp
	Game.combat.spawn_enemy_projectile(archer, archer.def.attacks[0])
	events.clear()
	for i in 12: Game.combat._tick_projectiles(0.05)
	GameEvents.flush()
	check(events.any(func(e): return e[0] == "projectile_reflected") and near(c.pools.hp, hp_c) and archer.pools.hp < hp_a,
		"the arrow turns back and strikes its archer (%.0f)" % (hp_a - archer.pools.hp))
	# The Sealing Gourd drinks it instead.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "sealing_gourd"})
	archer = _g2_foe("bandit_archer", here + Vector2(200, 0))
	archer.facing = -1
	Game.submit({"type": "use_treasure", "slot": 0})
	hp_c = c.pools.hp
	Game.combat.spawn_enemy_projectile(archer, archer.def.attacks[0])
	events.clear()
	Game.combat._tick_projectiles(0.05)
	GameEvents.flush()
	check(events.any(func(e): return e[0] == "projectile_absorbed") and Game.room_rt.projectiles.is_empty() and near(c.pools.hp, hp_c),
		"the gourd swallows the arrow before it lands")
	# The Mountain Seal: 250% Qi Attack to all within 120.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "mountain_seal"})
	var s1 := _g2_foe("bamboo_monkey", here + Vector2(60, 0))
	var s2 := _g2_foe("bamboo_monkey", here + Vector2(-90, 0))
	var s_hp := s1.pools.hp
	r = Game.submit({"type": "use_treasure", "slot": 0})
	check(r.get("ok", false) and int(r.targets) == 2 and s1.pools.hp < s_hp and s2.pools.hp < s_hp, "the seal comes down on both foes")
	# The Wisp Banner: three wisps strike the nearest foes each second.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "wisp_banner"})
	var w1 := _g2_foe("bamboo_monkey", here + Vector2(100, 0))
	var w_hp := w1.pools.hp
	Game.submit({"type": "use_treasure", "slot": 0})
	events.clear()
	Game.combat._tick_treasures(c, 1.0)
	GameEvents.flush()
	check(events.filter(func(e): return e[0] == "wisp_struck").size() == 1 and w1.pools.hp < w_hp, "a second in, the wisps find the only foe")
	for i in 10: Game.combat._tick_treasures(c, 1.0)
	check(not Game.combat.treasure_fx.get(c.id, {}).has("wisps"), "after 10 s the banner furls")
	# The Taming Cauldron: a worn-down beast is taken whole, as materials, with no loot roll.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "taming_cauldron"})
	var beast := _g2_foe("bamboo_monkey", here + Vector2(60, 0))
	var man := _g2_foe("bandit_archer", here + Vector2(30, 0))
	man.pools.hp = 1.0
	check(str(Game.submit({"type": "use_treasure", "slot": 0}).get("reason", "")) == "no_target", "a healthy beast (or any person) cannot be taken")
	beast.pools.hp = beast.pools.max_hp * 0.1
	events.clear()
	r = Game.submit({"type": "use_treasure", "slot": 0})
	GameEvents.flush()
	var taken: Array = events.filter(func(e): return e[0] == "beast_captured")
	var mats := LootRules.capture_materials("bamboo_monkey")
	check(r.get("ok", false) and not beast.alive and man.alive and taken.size() == 1 and mats.size() > 0 and int(taken[0][1].items) == mats.size()
		and Game.combat.captured.is_empty(), "the worn beast is taken whole, as its fixed materials (%s)" % str(mats))
	# Throwables: needles fly three at a time and share a 1.2 s cooldown.
	_g2_ready(c)
	Game.inventory.apply_add(c.id, "iron_needles", 5, "test")
	var t1 := _g2_foe("bamboo_monkey", here + Vector2(150, 0))
	t1.pools.max_hp = 1e7   # P12: under Might the character fells a Level 12 monkey with one needle; this one takes all three
	t1.pools.hp = t1.pools.max_hp
	var t_hp := t1.pools.hp
	r = Game.inventory.use_item(c, _bag_index(c, "iron_needles"), true)
	check(r.get("ok", false) and Game.room_rt.projectiles.size() == 3 and c.inventory.count("iron_needles") == 4, "one bundle throws three needles")
	check(str(Game.inventory.use_item(c, _bag_index(c, "iron_needles"), true).get("reason", "")) == "cooldown" and near(c.pools.cooldown("item:throw"), 1.2),
		"throwables share a 1.2 s cooldown")
	for i in 10: Game.combat._tick_projectiles(0.05)
	check(t1.pools.hp < t_hp and Game.room_rt.projectiles.is_empty(), "the needles land (%.0f)" % (t_hp - t1.pools.hp))
	# Shots fly at chest height but still strike a creature under the line (a rat is 22 tall).
	_g2_ready(c)
	var rat := _g2_foe("reedtail_rat", here + Vector2(120, 0))
	Game.combat._spawn_projectile({"team": "player", "owner": c.id, "x": here.x + 28, "y": here.y, "alt": Game.actor_state(c.id).altitude + 58.0, "dir": 1,
		"speed": 620, "range": 480, "pierce": 0, "art": "arrow", "attack": {"damage_type": "physical", "element": "none", "mult": [1.0, 1.0], "range": [1.0, 1.0]}})
	for i in 6: Game.combat._tick_projectiles(0.05)
	check(rat.pools.hp < rat.pools.max_hp, "an arrow at chest height strikes a rat beneath it")
	# A thunderclap pellet bursts: the foe behind the one it hits is caught too.
	_g2_ready(c)
	Game.inventory.apply_add(c.id, "thunderclap_pellet", 1, "test")
	var p1 := _g2_foe("bamboo_monkey", here + Vector2(150, 0))
	var p2 := _g2_foe("bamboo_monkey", here + Vector2(230, 0))
	var p_hp := p2.pools.hp
	events.clear()
	Game.inventory.use_item(c, _bag_index(c, "thunderclap_pellet"), true)
	for i in 10: Game.combat._tick_projectiles(0.05)
	GameEvents.flush()
	check(events.any(func(e): return e[0] == "projectile_burst") and p2.pools.hp < p_hp and p1.pools.hp < p1.pools.max_hp, "the pellet bursts and catches the foe behind")
	# Elder Hu's Talisman: three charges of 600% Qi Attack from a Treasure button, charges only.
	_g2_ready(c)
	Game.inventory.apply_add(c.id, "elder_hus_talisman", 1, "test")
	Game.submit({"type": "set_treasure", "slot": 0, "item": "elder_hus_talisman"})
	var big := _g2_foe("bamboo_monkey", here + Vector2(200, 0))
	var big_hp := big.pools.hp
	r = Game.submit({"type": "use_treasure", "slot": 0})
	check(r.get("ok", false) and big.pools.hp < big_hp and int(r.get("charges", 0)) == 2 and near(c.pools.qi, c.pools.max_qi),
		"one charge of the palm strikes the monkey; two charges left, no Qi spent")
	check(Game.submit({"type": "use_treasure", "slot": 0}).get("ok", false), "charges only: no cooldown between them")
	Game.submit({"type": "use_treasure", "slot": 0})
	check(c.inventory.count("elder_hus_talisman") == 0 and c.inventory.treasures[0] == "", "the third charge spends the paper and empties the button")
	# Flight vessels: kept once in the key pouch, chosen for flight.
	Game.inventory.apply_add(c.id, "flying_sword_vessel", 1, "test")
	Game.inventory.apply_add(c.id, "flying_sword_vessel", 1, "test")
	check(c.inventory.count("flying_sword_vessel") == 1 and c.inventory.key_items.any(func(k): return k.id == "flying_sword_vessel"), "a vessel is kept once, in the key pouch")
	check(Game.submit({"type": "choose_vessel", "item": "flying_sword_vessel"}).get("ok", false) and near(Game.combat.vessel_qi_mult(c), 0.8),
		"the Flying Sword: flight costs 20% less Qi")
	check(not Game.submit({"type": "choose_vessel", "item": "bronze_bell"}).get("ok", false), "a bell is not a vessel")
	var saved: Dictionary = c.inventory.snapshot()
	var inv2 := InventoryState.new()
	inv2.restore(saved)
	check(inv2.vessel == "flying_sword_vessel" and inv2.treasures == c.inventory.treasures, "treasures and the vessel survive a save")
	Game.submit({"type": "choose_vessel", "item": ""})
	check(c.inventory.vessel == "" and near(Game.combat.vessel_qi_mult(c), 1.0), "dismounted, you fly on Qi alone")
	# Tidy up.
	GameEvents.event.disconnect(grab)
	_g2_ready(c)
	c.inventory.treasures = ["", ""]
	c.inventory.bag.fill(null)
	c.inventory.key_items = c.inventory.key_items.filter(func(k): return k.id != "flying_sword_vessel")
	c.cultivator.realm_key = realm0
	Game.combat.refresh_stats(c.id)
	c.pools.hp = c.pools.max_hp
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ traversal (Build Prompt v2 S43)
func _trav_zone() -> ZoneGeometry:
	var z := ZoneGeometry.new()
	z.configure({"bounds": [0, 480, 3000, 480], "surfaces": [
		{"id": "ground", "rect": [0, 560, 3000, 400], "height": 0, "kind": "ground", "stratum": "ground", "open_edges": false},
		{"id": "deck", "rect": [200, 600, 400, 100], "height": 100, "kind": "roof", "stratum": "platform"},
		{"id": "loft", "rect": [1150, 600, 200, 88], "height": 88, "kind": "roof", "stratum": "platform"}],
		"blocks": [{"id": "crate", "rect": [800, 700, 60, 60], "base": 0, "top": 60, "kind": "crate"},
			{"id": "wall", "rect": [1600, 560, 40, 400], "base": 0, "top": 300, "kind": "wall"}],
		"climbables": [{"id": "ladder", "kind": "ladder", "at": [1250, 725], "top_at": [1250, 680], "bottom_alt": 0, "top_alt": 88, "bottom": "ground", "top": "loft"}]})
	return z

func _trav_actor(z: ZoneGeometry, sid: String, at: Vector2, arts := {}) -> ActorState:
	var st := ActorState.new()
	st.surface = z.index[sid]
	st.plane = at
	st.altitude = st.surface.height_at(at)
	st.arts = {"double_jump": false, "wall_step": false, "drop_through": true, "mantle": true, "climb": true}
	st.arts.merge(arts, true)
	return st

func _trav_run(st: ActorState, z: ZoneGeometry, secs: float, v: Vector2, dt := 1.0 / 120.0) -> void:
	var t := 0.0
	while t < secs - 0.0001:
		MovementSolver.advance(st, z, dt, v)
		t += dt

func traversal_suite() -> void:
	var z := _trav_zone()
	# Rule 1: platform back edges are closed, the others open; a block top is open all round.
	var d: WalkSurface = z.index.deck
	check(d.edges == {"n": "closed", "s": "open", "e": "open", "w": "open"} and (z.index.ground as WalkSurface).edges.n == "closed"
		and (z.index.crate as WalkSurface).edges.n == "open", "platforms close their back edge by default; blocks are open all round")
	var st := _trav_actor(z, "deck", Vector2(400, 620))
	_trav_run(st, z, 1.0, Vector2(0, -205))
	check(st.surface == d and st.plane.y >= 600.0, "walking north off a roof is stopped by its closed back edge")
	_trav_run(st, z, 1.5, Vector2(0, 205))
	check(st.surface != null and st.surface.id == "ground", "walking south off it drops to the ground")
	# Blocks stop walking, can be stood on, and a 60 block can be jumped over at walk speed.
	st = _trav_actor(z, "ground", Vector2(760, 730))
	_trav_run(st, z, 0.8, Vector2(205, 0))
	check(st.plane.x < 800.0 and st.surface.id == "ground", "a crate stops a walker (x %.0f)" % st.plane.x)
	st = _trav_actor(z, "ground", Vector2(700, 730))
	MovementSolver.jump(st)
	_trav_run(st, z, 1.4, Vector2(205, 0))
	check(st.surface != null and st.surface.id == "ground" and st.plane.x > 866.0, "a 60 block is jumped over at walk speed (x %.0f)" % st.plane.x)
	st = _trav_actor(z, "ground", Vector2(775, 730))
	MovementSolver.jump(st)
	_trav_run(st, z, 0.3, Vector2(205, 0))
	_trav_run(st, z, 1.0, Vector2.ZERO)
	check(st.surface != null and st.surface.id == "crate" and near(st.altitude, 60.0), "a crate can be stood on")
	# Rule 2: coyote time, jump buffer and the fixed jump, at three frame rates.
	for dt in [1.0 / 30.0, 1.0 / 60.0, 1.0 / 120.0]:
		st = _trav_actor(z, "deck", Vector2(400, 690))
		_trav_run(st, z, 0.1, Vector2(0, 205), dt)
		var off := st.surface == null
		var coy := MovementSolver.jump(st)
		check(off and coy and near(st.vertical_speed, 530.0) and st.jumps_used == 1, "a jump just after walking off an edge is still a ground jump (dt %.3f)" % dt)
		st = _trav_actor(z, "ground", Vector2(1000, 800))
		MovementSolver.jump(st)
		while st.vertical_speed > -480.0: MovementSolver.advance(st, z, 1.0 / 240.0, Vector2.ZERO)
		var early := MovementSolver.jump(st)
		st.events.clear()
		_trav_run(st, z, 0.2, Vector2.ZERO, dt)
		var names: Array = st.events.map(func(e): return e.name)
		check(not early and names.find("landed") >= 0 and names.find("jumped", names.find("landed")) > 0,
			"a jump pressed just before landing fires on landing (dt %.3f) %s" % [dt, str(names)])
	st = _trav_actor(z, "ground", Vector2(1000, 800))
	MovementSolver.jump(st)
	var peak := 0.0
	for i in 240:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
		peak = maxf(peak, st.altitude)
	check(near(peak, 122.1, 0.01), "the base jump peaks at 122 (%.1f)" % peak)
	# Cloud Ladder Step: a second jump of +80 from where it is used; none without the art.
	st = _trav_actor(z, "ground", Vector2(1000, 800))
	MovementSolver.jump(st)
	while st.vertical_speed > 0.0: MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
	check(not MovementSolver.jump(st), "no double jump without Cloud Ladder Step")
	st = _trav_actor(z, "ground", Vector2(1000, 800), {"double_jump": true})
	MovementSolver.jump(st)
	while st.vertical_speed > 0.0: MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
	var from_h: float = st.altitude
	check(MovementSolver.jump(st) and near(st.vertical_speed, 430.0), "Cloud Ladder Step jumps again at impulse 430")
	peak = 0.0
	for i in 240:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
		peak = maxf(peak, st.altitude)
	check(near(peak - from_h, 80.4, 0.02) and near(peak, 202.0, 0.02), "+80 from where it is used; about 202 from the ground (%.0f)" % peak)
	# Wall-Step: push into a wall face within 12 and kick (vertical 450), three times per airtime.
	st = _trav_actor(z, "ground", Vector2(1590, 800), {"wall_step": true})
	MovementSolver.jump(st)
	_trav_run(st, z, 0.2, Vector2.ZERO)
	check(MovementSolver.wall_step(st, z, 0) == 0, "no Wall-Step without pushing into the wall")
	var kicks := 0
	for i in 4:
		if MovementSolver.wall_step(st, z, 1) != 0: kicks += 1
	check(kicks == 3 and near(st.vertical_speed, 450.0), "three Wall-Step kicks per airtime at vertical speed 450 (%d)" % kicks)
	# Rule 3: drop through a platform, never the ground or a block.
	st = _trav_actor(z, "deck", Vector2(400, 650))
	check(MovementSolver.drop_through(st), "drop through the deck")
	_trav_run(st, z, 1.2, Vector2.ZERO)
	check(st.surface != null and st.surface.id == "ground", "and land on the ground below it")
	check(not MovementSolver.drop_through(st), "the ground cannot be dropped through")
	st = _trav_actor(z, "crate", Vector2(830, 730))
	check(not MovementSolver.drop_through(st), "nor a block")
	# Rule 4: a just-missed ledge within 24 up and 16 across is mantled.
	st = _trav_actor(z, "ground", Vector2(190, 650))
	st.surface = null
	st.altitude = 84.0
	st.air_peak = 110.0
	st.vertical_speed = -50.0
	st.jumps_used = 1
	MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(205, 0))
	check(st.surface == d and near(st.altitude, 100.0), "a ledge 16 above is mantled")
	# Rule 5: climb a ladder, stop, reach the top, come down, jump off, be knocked off.
	st = _trav_actor(z, "ground", Vector2(1250, 740))
	var ladder: Dictionary = z.climbable_near(st.plane, st.altitude)
	check(not ladder.is_empty() and MovementSolver.start_climb(st, ladder, false), "the ladder is in reach and can be climbed")
	_trav_run(st, z, 0.2, Vector2(0, -205))
	var mid: float = st.altitude
	_trav_run(st, z, 0.2, Vector2.ZERO)
	check(near(mid, 32.0, 0.05) and near(st.altitude, mid), "climbing at 160 a second, and stopping on the rungs (%.0f)" % mid)
	for i in 120:
		if st.climbing.is_empty(): break
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(0, -205))
	check(st.climbing.is_empty() and st.surface != null and st.surface.id == "loft", "the top step lands on the loft")
	var down_from: Dictionary = z.climbable_near(st.plane, st.altitude)
	check(not down_from.is_empty() and MovementSolver.start_climb(st, down_from, true), "climb back down from the top")
	for i in 120:
		if st.climbing.is_empty(): break
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(0, 205))
	check(st.climbing.is_empty() and st.surface.id == "ground", "the foot steps onto the ground")
	MovementSolver.start_climb(st, z.climbable_near(st.plane, st.altitude), false)
	_trav_run(st, z, 0.2, Vector2(0, -205))
	check(MovementSolver.release_climb(st, 1, true) and st.surface == null and st.vertical_speed > 0.0, "a jump lets go of the ladder")
	st = _trav_actor(z, "ground", Vector2(1250, 740))
	MovementSolver.start_climb(st, z.climbable_near(st.plane, st.altitude), false)
	check(MovementSolver.release_climb(st, -1, false) and st.surface == null and near(st.vertical_speed, 0.0), "a hit knocks the climber off")
	# Rule 6: the void lies 250 below the lowest surface.
	check(near(z.void_altitude, -250.0), "void altitude defaults to 250 below the lowest surface")
	# Traversal events are recorded for the authority to announce.
	st = _trav_actor(z, "ground", Vector2(1000, 800))
	MovementSolver.jump(st)
	check(st.events.any(func(e): return e.name == "jumped"), "a jump records a jumped event")
	# Room data reaches the room's geometry: blocks, climbables and the void (the World authority compiles it).
	var echo := ZoneGeometry.new()
	echo.configure(WorldAuthority.compile_geometry(ContentDB.room("wg_echo_cliffs")))
	check(echo.index.has("shaft_west") and echo.wall_face_at(Vector2(1356, 690), 120.0, "ground"), "the Echo Cliffs shaft walls are in the room's geometry")
	var ferry := ZoneGeometry.new()
	ferry.configure(WorldAuthority.compile_geometry(ContentDB.room("lf_village")))
	check(ferry.climbables.size() >= 1, "the Lotus Ferry hall ladder is in the room's geometry")

# ------------------------------------------------------------------ S43 movement arts, volumes and movers (V2b)
func _vol_zone() -> ZoneGeometry:
	var z := ZoneGeometry.new()
	z.configure({"bounds": [0, 480, 4000, 480], "surfaces": [
		{"id": "ground", "rect": [0, 560, 4000, 400], "height": 0, "kind": "ground", "stratum": "ground", "open_edges": false},
		{"id": "raft", "rect": [2000, 700, 90, 40], "height": 10, "kind": "raft", "stratum": "platform"},
		{"id": "boards", "rect": [2600, 650, 200, 70], "height": 100, "kind": "bridge", "stratum": "platform"},
		{"id": "cracked", "rect": [3200, 650, 200, 70], "height": 100, "kind": "rock_ledge", "stratum": "platform", "cracked": true}],
		"blocks": [{"id": "drum", "rect": [1900, 740, 60, 60], "base": 0, "top": 40, "kind": "drum"}],
		"volumes": [
			{"id": "shallow", "kind": "water_shallow", "rect": [100, 800, 300, 100], "alt": [-50, 10]},
			{"id": "deep", "kind": "water_deep", "rect": [500, 800, 300, 100], "alt": [-100, 10]},
			{"id": "drain", "kind": "current", "rect": [900, 800, 200, 100], "alt": [-50, 10], "push": [-80, 0]},
			{"id": "draft", "kind": "updraft", "rect": [1200, 560, 150, 400], "alt": [0, 300]},
			{"id": "gale", "kind": "wind", "rect": [1500, 560, 300, 400], "alt": [-50, 600], "push": [-100, 0]},
			{"id": "pad", "kind": "bounce", "rect": [1900, 740, 60, 60], "alt": [30, 50]},
			{"id": "rot", "kind": "crumble", "rect": [2600, 650, 200, 70], "surface": "boards"},
			{"id": "flood", "kind": "rising_water", "rect": [3600, 560, 300, 400], "alt": [-100, -20],
				"rise": [{"event": "boss_phase", "match": {"action": "flood"}, "to": 30, "over_s": 4.0, "hold_s": 2.0, "back_to": -20}]}],
		"movers": [{"surface": "raft", "path": [[300, 0, 0]], "speed": 100, "wait_s": 1.0, "mode": "pingpong"}]})
	return z

func _fall_until_landed(st: ActorState, z: ZoneGeometry, v := Vector2.ZERO, limit := 4.0) -> float:
	var t := 0.0
	while st.surface == null and t < limit:
		MovementSolver.advance(st, z, 1.0 / 120.0, v)
		t += 1.0 / 120.0
	return t

func arts_volumes_suite() -> void:
	var z := _vol_zone()
	# Falling Leaf Glide: descent capped at 120/s, 10% faster across; from an apex jump about 1.5 s and 300 flat.
	var st := _trav_actor(z, "ground", Vector2(2900, 900))
	MovementSolver.jump(st)
	check(not MovementSolver.glide(st, true), "no glide without Falling Leaf Glide")
	st = _trav_actor(z, "ground", Vector2(2900, 900), {"glide": true})
	var x0: float = st.plane.x
	MovementSolver.jump(st)
	var air := 0.0
	while st.vertical_speed > 0.0:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(205, 0))
		air += 1.0 / 120.0
	check(MovementSolver.glide(st, true) and st.gliding, "Jump held while falling glides")
	_trav_run(st, z, 0.3, Vector2(205, 0))
	check(st.vertical_speed >= -120.01, "a glide falls no faster than 120 a second (%.1f)" % st.vertical_speed)
	air += 0.3 + _fall_until_landed(st, z, Vector2(205, 0))
	var flat: float = st.plane.x - x0
	check(air > 1.4 and air < 1.7 and flat > 280.0 and flat < 360.0 and not st.gliding, "an apex glide lasts about 1.5 s and 300 units (%.2f s, %.0f)" % [air, flat])
	# Swallow Dart: in the air the body holds its height for 0.25 s while it darts 140; once per airtime.
	st = _trav_actor(z, "ground", Vector2(2900, 900), {"air_dash": true})
	MovementSolver.jump(st)
	_trav_run(st, z, 0.3, Vector2.ZERO)
	var alt0: float = st.altitude
	x0 = st.plane.x
	check(MovementSolver.air_dash(st), "Evade in the air darts")
	_trav_run(st, z, 0.25, Vector2(560, 0))
	check(near(st.altitude, alt0, 0.5) and near(st.plane.x - x0, 140.0, 1.0), "the dart holds the height and covers 140 (%.1f, %.0f)" % [st.altitude - alt0, st.plane.x - x0])
	check(not MovementSolver.air_dash(st), "one dart per airtime")
	_fall_until_landed(st, z)
	check(not st.air_dash_used, "landing gives the dart back")
	# Plunge: straight down at 900; the landing is left for Combat; a cracked floor breaks under it.
	st = _trav_actor(z, "ground", Vector2(2900, 900), {"plunge": true})
	MovementSolver.jump(st)
	_trav_run(st, z, 0.4, Vector2.ZERO)
	x0 = st.plane.x
	check(MovementSolver.plunge(st) and near(st.vertical_speed, -900.0), "Down + Attack in the air plunges at 900")
	var drop := _fall_until_landed(st, z, Vector2(205, 0))
	check(near(st.plane.x, x0, 0.5) and drop < 0.16 and not st.plunge_impact.is_empty() and not st.plunging, "a plunge drops straight and leaves an impact (%.2f s)" % drop)
	st = _trav_actor(z, "ground", Vector2(3300, 690), {"plunge": true})
	st.surface = null
	st.altitude = 220.0
	st.air_peak = 220.0
	st.jumps_used = 1
	MovementSolver.plunge(st)
	_fall_until_landed(st, z)
	check((z.index.cracked as WalkSurface).disabled and st.surface != null and st.surface.id == "ground", "a plunge breaks a cracked floor and falls through it")
	# Shallow water: x0.7.
	st = _trav_actor(z, "ground", Vector2(120, 850))
	_trav_run(st, z, 1.0, Vector2(205, 0))
	check(near(st.plane.x - 120.0, 143.5, 1.5), "shallow water slows walking to x0.7 (%.1f)" % (st.plane.x - 120.0))
	# Deep water: sinks in 1 s without an art; Breath Control swims at x0.6; Water Skimming runs across while sprinting.
	st = _trav_actor(z, "ground", Vector2(520, 850))
	_trav_run(st, z, 0.5, Vector2.ZERO)
	check(st.events.any(func(e): return e.name == "volume_entered" and str(e.volume) == "deep") and near(st.sink_depth, 20.0, 1.0) and not st.drowned,
		"deep water pulls a body down (%.1f) and says so" % st.sink_depth)
	check(not MovementSolver.jump(st), "a sinking body cannot jump out")
	_trav_run(st, z, 0.6, Vector2.ZERO)
	check(st.drowned and near(st.sink_depth, 40.0), "after 1 s it has sunk 40 and must be recovered")
	st = _trav_actor(z, "ground", Vector2(520, 850), {"breath_control": true})
	_trav_run(st, z, 1.0, Vector2(205, 0))
	check(not st.drowned and st.mode() == "swim" and near(st.plane.x - 520.0, 123.0, 1.5), "Breath Control swims at x0.6 (%.1f)" % (st.plane.x - 520.0))
	st = _trav_actor(z, "ground", Vector2(470, 850), {"water_skimming": true})
	st.sprinting = true
	_trav_run(st, z, 0.6, Vector2(348, 0))
	check(not st.drowned and st.water.get("skimming", false) and st.sink_depth == 0.0 and st.events.any(func(e): return e.name == "art_used" and e.art == "water_skimming"),
		"Water Skimming runs on deep water while sprinting")
	_trav_run(st, z, 0.55, Vector2.ZERO)
	check(not st.water.get("skimming", true), "stopping for half a second ends the skim")
	_trav_run(st, z, 1.1, Vector2.ZERO)
	check(st.drowned, "and then the water takes you")
	# Current: pushes a body standing in it.
	st = _trav_actor(z, "ground", Vector2(1050, 850))
	_trav_run(st, z, 1.0, Vector2.ZERO)
	check(near(st.plane.x - 1050.0, -80.0, 1.0), "a current pushes 80 a second (%.1f)" % (st.plane.x - 1050.0))
	# Updraft: a fall turns into a rise toward +220.
	st = _trav_actor(z, "ground", Vector2(1275, 800))
	st.surface = null
	st.altitude = 150.0
	st.air_peak = 150.0
	st.vertical_speed = -200.0
	st.jumps_used = 1
	_trav_run(st, z, 1.0, Vector2.ZERO)
	check(st.surface == null and st.altitude > 150.0 and st.vertical_speed > 100.0, "an updraft lifts a falling body (alt %.0f, vz %.0f)" % [st.altitude, st.vertical_speed])
	# Wind: strong for 1.5 s of every 4, a breeze (x0.3) the rest.
	st = _trav_actor(z, "ground", Vector2(1650, 800))
	z.time = 0.0
	_trav_run(st, z, 0.5, Vector2.ZERO)
	var gust: float = st.plane.x - 1650.0
	z.time = 2.0
	var x1: float = st.plane.x
	_trav_run(st, z, 0.5, Vector2.ZERO)
	check(near(gust, -50.0, 1.0) and near(st.plane.x - x1, -15.0, 1.0), "wind gusts at full push, then a breeze (%.1f, %.1f)" % [gust, st.plane.x - x1])
	# Bounce: landing on the drum launches at 700 (apex about 213 above it).
	st = _trav_actor(z, "ground", Vector2(1930, 770))
	st.surface = null
	st.altitude = 120.0
	st.air_peak = 120.0
	st.jumps_used = 1
	_fall_until_landed(st, z)
	var bounced := st.surface == null and near(st.vertical_speed, 700.0, 30.0)
	var top := 0.0
	for i in 240:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
		top = maxf(top, st.altitude)
	check(bounced and near(top, 40.0 + 213.0, 4.0), "a bounce pad throws you back up about 213 (%.0f)" % (top - 40.0))
	# Crumble: the boards give way 0.8 s after a foot lands and come back 5 s later.
	st = _trav_actor(z, "boards", Vector2(2700, 690))
	for i in 60:
		MovementSolver.advance(st, z, 1.0 / 60.0, Vector2.ZERO)
		z.advance(1.0 / 60.0)
	_fall_until_landed(st, z)
	check((z.index.boards as WalkSurface).disabled and st.surface != null and st.surface.id == "ground", "crumbling boards drop whoever stands on them")
	z.advance(5.1)
	check(not (z.index.boards as WalkSurface).disabled, "and return after 5 s")
	# Movers: the offset is a pure function of the room clock, and riders ride along.
	var m: Dictionary = z.movers[0]
	check(z.mover_offset(m, 0.5) == Vector3.ZERO and near(z.mover_offset(m, 2.0).x, 100.0) and near(z.mover_offset(m, 4.5).x, 300.0)
		and near(z.mover_offset(m, 6.0).x, 200.0) and z.mover_offset(m, 8.0 + 0.5) == Vector3.ZERO, "a pingpong mover waits, travels, waits and returns")
	var replay := func() -> Vector2:
		var zz := _vol_zone()
		var rider := _trav_actor(zz, "raft", Vector2(2040, 720))
		for i in 150:
			zz.advance(1.0 / 60.0)
			MovementSolver.advance(rider, zz, 1.0 / 60.0, Vector2(20, 0) if i % 50 < 10 else Vector2.ZERO)
		return rider.plane
	var p1: Vector2 = replay.call()
	var p2: Vector2 = replay.call()
	check(p1 == p2 and p1.x > 2100.0, "a rider is carried by its mover, the same on every replay (%s)" % str(p1))
	# Rising water follows its event, holds, then drains.
	z.on_event("boss_phase", {"action": "flood"})
	z.advance(4.0)
	var flood: Dictionary = z.volumes[7]
	var risen := near(float(flood.hi), 30.0)
	z.advance(2.0 + 4.0 + 0.1)
	check(risen and near(float(flood.hi), -20.0), "a boss phase floods the arena, and it drains after its hold")
	st = _trav_actor(z, "ground", Vector2(3700, 800))
	z.on_event("boss_phase", {"action": "flood"})
	z.advance(4.0)
	_trav_run(st, z, 0.5, Vector2.ZERO)
	check(st.sink_depth > 0.0, "rising water is deep water while it stands")

## Movement arts through the Game: Plunge strikes, glide costs QI, Swallow Dart shares the dodge cooldown,
## sect grounds refuse flight and a climber cannot use techniques.
func arts_combat_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "bg_whispering_bamboo")
	for sid in ["stun", "slow", "shock", "spawn_protection"]: Game.combat.cure_status(c.id, sid)
	check(str(Game.submit({"type": "plunge"}).get("reason", "")) == "locked", "Plunge must be learned")
	for art in ["plunge", "falling_leaf_glide", "swallow_dart"]: Game.progression.apply_learn_secret_art(c.id, art)
	check(Game.combat.knows_art(c, "plunge") and Game.combat.knows_art(c, "glide") and Game.combat.knows_art(c, "air_dash"), "learned arts are known by their movement name")
	var geo: ZoneGeometry = Game.room_rt.geometry
	var foe: EnemyState = Game.enemies.spawn_at("green_viper", st.plane + Vector2(30, 0), 12)
	check(foe != null, "a foe to plunge on")
	var here: Vector2 = st.plane
	st.surface = null
	st.altitude = 150.0
	st.air_peak = 150.0
	st.vertical_speed = 0.0
	st.jumps_used = 1
	var r := Game.submit({"type": "plunge"})
	check(r.get("ok", false) and st.plunging, "Plunge in the air %s" % str(r))
	check(str(Game.submit({"type": "plunge"}).get("reason", "")) in ["cooldown", "not_airborne"], "one Plunge at a time; then it rests 4 s")
	var hp0 := 0.0
	if foe:
		foe.plane = here + Vector2(30, 0)
		foe.altitude = 0.0
		hp0 = foe.pools.hp
	_fall_until_landed(st, geo)
	Game.tick(0.05)
	check(st.plunge_impact.is_empty() and (foe == null or foe.pools.hp < hp0), "the Plunge lands a blow within 60")
	check(foe == null or not foe.alive or foe.pools.has_status("stun"), "and stuns for half a second")
	# Glide costs 2 QI a second, and stops when you land.
	c.pools.qi = c.pools.max_qi
	st.surface = null
	st.altitude = 200.0
	st.vertical_speed = -10.0
	r = Game.submit({"type": "glide", "on": true})
	var qi0: float = c.pools.qi
	for i in 20: Game.tick(0.05)
	check(r.get("ok", false) and Game.combat.is_gliding(c.id) and near(qi0 - c.pools.qi, 2.0, 0.3), "gliding drains 2 QI a second (%.2f)" % (qi0 - c.pools.qi))
	_fall_until_landed(st, geo)
	Game.tick(0.05)
	check(not Game.combat.is_gliding(c.id), "landing ends the glide")
	# Swallow Dart: an Evade tap in the air, once per airtime, on the dodge's cooldown.
	var had_dodge: bool = c.cultivator.unlocked.has("dodge_dash")
	c.cultivator.unlocked["dodge_dash"] = true
	c.pools.cooldowns.erase("dodge")
	st.surface = null
	st.altitude = 100.0
	st.vertical_speed = 0.0
	st.air_dash_used = false
	r = Game.submit({"type": "dodge", "direction": Vector2(1, 0), "facing": 1})
	check(r.get("air_dash", false) and st.air_dash_used and c.pools.cooldown("dodge") > 0.0, "Evade in the air is Swallow Dart %s" % str(r))
	if not had_dodge: c.cultivator.unlocked.erase("dodge_dash")
	_fall_until_landed(st, geo)
	# Sect grounds refuse flight; techniques wait while climbing.
	var room0: Dictionary = Game.room_rt.def
	Game.room_rt.def = room0.duplicate()
	Game.room_rt.def.type = "sect"
	check(not Game.combat.flight_allowed(c.id), "no flight on sect grounds")
	Game.room_rt.def = room0
	st.climbing = {"id": "test_ladder", "kind": "ladder"}
	var slot0 = c.cultivator.technique_slots[0] if c.cultivator.technique_slots.size() > 0 else null
	if slot0 != null and str(slot0) != "":
		check(str(Game.submit({"type": "use_technique", "slot": 0, "facing": 1}).get("reason", "")) == "climbing", "techniques wait while you climb")
	check(str(Game.submit({"type": "basic_attack", "facing": 1}).get("reason", "")) == "climbing", "and so do attacks")
	st.climbing = {}

# ------------------------------------------------------------------ S43 rules 10-12: bands, shots, navigation, allies (V2c)
func nav_suite() -> void:
	# Rule 10: the melee band is -30..+60 of the attacker's height, Qi arcs -10..+80.
	var ground := {"x": 0.0, "y": 800.0, "alt": 0.0}
	var melee := {"x": [0, 60], "depth": 30, "alt": ContentDB.movement("combat_bands.melee", [])}
	var qi_arc := {"x": [0, 60], "depth": 30, "alt": ContentDB.movement("combat_bands.qi_arc", [])}
	var on_roof := {"x": 30.0, "y": 800.0, "alt": 88.0, "half_width": 14.0, "height": 88.0}
	var mid_jump := {"x": 30.0, "y": 800.0, "alt": 40.0, "half_width": 14.0, "height": 88.0}
	check(not CombatAuthority.hit_test(ground, 1, melee, on_roof) and CombatAuthority.hit_test(ground, 1, melee, mid_jump),
		"a ground fighter cannot strike a target on an 88 roof, but can strike it mid-jump")
	check(CombatAuthority.hit_test(ground, 1, qi_arc, {"x": 30.0, "y": 800.0, "alt": 75.0, "half_width": 14.0, "height": 40.0})
		and not CombatAuthority.hit_test(ground, 1, melee, {"x": 30.0, "y": 800.0, "alt": 75.0, "half_width": 14.0, "height": 40.0}), "a Qi arc reaches 80 up; a blow reaches 60")
	var jb: Array = ContentDB.entry("weapon_families", "jian").altitude
	var vb: Array = ContentDB.entry("enemies", "green_viper").attacks[0].hitbox.alt
	check(near(float(jb[0]), -30.0) and near(float(jb[1]), 60.0) and near(float(vb[0]), -30.0) and near(float(vb[1]), 60.0), "weapons and monsters strike in the melee band")
	# Shots stop at blocks and walls, never at platform decks.
	var z := _trav_zone()
	check(z.stops_shot(Vector2(830, 730), 40.0) and not z.stops_shot(Vector2(830, 730), 70.0) and not z.stops_shot(Vector2(400, 650), 58.0),
		"a shot stops at a crate below its top, flies over it, and passes a roof deck")
	# Rule 11: the navigation graph, by species movement.
	var jumper := {"jump": 530, "climb": false, "drop": true}
	var g: Dictionary = z.nav_graph(jumper)
	var kinds := func(from: String, to: String) -> Array:
		return g.get(from, []).filter(func(e): return e.to == to).map(func(e): return e.kind)
	check(kinds.call("ground", "deck") == ["jump"] and kinds.call("deck", "ground") == ["drop"] and kinds.call("ground", "crate") == ["jump"],
		"a jumper can hop onto a 100 deck and a crate and drop back down")
	check(kinds.call("ground", "wall").is_empty(), "a 300 wall is out of a 530 jump")
	check(z.nav_graph({"jump": 0, "climb": false, "drop": true}).get("ground", []).filter(func(e): return e.to == "deck").is_empty(), "a species that cannot jump stays below")
	var climber: Dictionary = z.nav_graph({"jump": 0, "climb": true, "drop": true})
	check(climber.get("ground", []).any(func(e): return e.to == "loft" and e.kind == "climb"), "a climber takes the ladder to the loft")
	var z2 := _trav_zone()
	check(str(z2.nav_graph(jumper)) == str(g), "the graph is identical on two builds of the same room")
	check(z.nav_path("ground", "deck", jumper).size() == 1 and z.nav_path("deck", "loft", {"jump": 0, "climb": true, "drop": true}).size() == 2,
		"paths chain drop and climb edges")
	# In a real room: a jumping monster follows the player onto a ledge; one that cannot jump gives up.
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wg_echo_cliffs")
	for sid in ["stun", "slow", "shock", "spawn_protection"]: Game.combat.cure_status(c.id, sid)
	var geo: ZoneGeometry = Game.room_rt.geometry
	for e0 in Game.room_rt.living_enemies(): e0.alive = false
	var ledge: WalkSurface = geo.index.get("ledge_0")
	st.surface = ledge
	st.plane = ledge.bounds.get_center()
	st.altitude = ledge.height_at(st.plane)
	st.vertical_speed = 0.0
	c.pools.hp = c.pools.max_hp
	var hunter: EnemyState = Game.enemies.spawn_at("mudwater_bandit", Vector2(ledge.bounds.get_center().x + 60, 860), 16)
	var plodder: EnemyState = Game.enemies.spawn_at("stone_tortoise", Vector2(ledge.bounds.get_center().x - 60, 860), 5)
	for e1 in [hunter, plodder]:
		e1.ai.state = "aggro"
		e1.ai.timer = 99.0
		e1.threat[c.id] = 1.0
	var on_ledge := false
	var unreach := 0.0
	for i in 240:
		Game.tick(0.05)
		c.pools.hp = c.pools.max_hp
		if hunter.surface_id == "ledge_0": on_ledge = true
		unreach = maxf(unreach, float(plodder.ai.get("unreach", 0.0)))
		st.surface = ledge
		st.altitude = ledge.height_at(st.plane)
	check(on_ledge, "a bandit jumps up the ledge after you")
	check(unreach >= 2.0, "a tortoise that cannot jump finds you out of reach (%.1f s)" % unreach)
	check(str(plodder.ai.state) == "return" or bool(plodder.ai.get("leashed", false)) or plodder.surface_id == plodder.home_surface, "after 6 s it goes home to heal")
	# Rule 12: an ally that cannot reach its owner blinks to them after 2 s.
	var high: WalkSurface = geo.index.get("ledge_2")
	st.surface = high
	st.plane = high.bounds.get_center()
	st.altitude = high.height_at(st.plane)
	var pal := EnemyState.new()
	pal.team = "ally"
	pal.def = {"name": "Test", "movement": {"jump": 0, "climb": false, "fly": false, "drop": true}}
	pal.plane = Vector2(st.plane.x - 100, 860)
	pal.surface_id = "ground"
	pal.ai = {"state": "follow", "timer": 0.0, "offset": 56, "depth_offset": 14, "speed": 200}
	for e2 in Game.room_rt.living_enemies(): e2.alive = false
	for i in 50: AllyBrain.think(Game, pal, 0.05, 1.0, 36.0)
	check(pal.surface_id == "ledge_2" and near(pal.altitude, 300.0), "an ally that cannot follow blinks to its owner after 2 s")
	pal.plane = Vector2(st.plane.x + 900, 860)
	pal.surface_id = "ground"
	AllyBrain.think(Game, pal, 0.05, 1.0, 36.0)
	check(pal.plane.distance_to(st.plane) < 120.0, "and at once when more than 480 away")

# ------------------------------------------------------------------ emotes (S34)
## The Account Legacy (P10 finding F1): the unlock exists at Bone Forging 1 for the whole account, a save that reached
## great realms before it existed has them recorded once when it arrives, and each record adds 2% to accumulation.
## P7a finding: the banded equipment roll never makes a legendary weapon or an imitation relic.
## P9 finding: a dungeon boss's fall is announced as boss_defeated, clean only when no grave wound came first in the
## room, so the Untouched achievement can be earned.
# ------------------------------------------------------------------ P6 moments
## docs/moments_design.md §7.1: a MomentView with no world and no HUD, fed through its event handler and stepped by
## hand. Case 1 runs every real row; cases 3–10 run on fixture rows, so the gather, merge, queue, cut, lock and settings
## are proved before the real rows have screen parts.
func moments_suite() -> void:
	var c = Game.active()
	if c == null: return
	var was: Dictionary = Game.account.settings.duplicate(true)
	var mv := MomentView.new()
	add_child(mv)
	mv.set_process(false)
	mv.fight_override = false
	mv.pages_override = false
	var run := func(s: float) -> void:
		for i in int(round(s * 60.0)): mv.advance(1.0 / 60.0)
	var feed := func(ev: String, p: Dictionary) -> void:
		var q := p.duplicate(true)
		for k in ["actor", "target"]:
			if q.has(k): q[k] = c.id
		mv._on_event(ev, q)
	var played := func(id: String) -> Array: return mv.logged.filter(func(e): return str(e.row) == id)
	# 1. Every real row fires from its sample and ends on time, each layer logged within a frame of its t.
	var real: Array = ContentDB.all("moments")
	for r in real:
		mv.load_rows(real)
		mv.logged.clear()
		feed.call(str(r.event), r.sample)
		mv.advance(0.0)
		var on: bool = (mv.playing != null and mv.playing.row.id == r.id) or mv.queue.any(func(q): return q.row.id == r.id) or not played.call(str(r.id)).is_empty()
		check(on, "moment %s plays from its sample" % r.id)
		run.call(float(r.duration_s) + 0.1)
		for h in r.get("hold_until", []): feed.call(str(h), {"actor": c.id, "survived": true})
		run.call(2.0 / 60.0)
		check(mv.playing == null and mv.queue.is_empty() and not mv.active.any(func(q): return q.row.id == r.id), "moment %s ends on time and frees the screen" % r.id)
		var late: Array = []
		for L in r.layers:
			if L.has("if_slot") or str(L.kind) in ["caption", "camera"]: continue
			if not played.call(str(r.id)).any(func(e): return str(e.layer) == str(L.kind) and absf(float(e.t) - float(L.t)) <= 1.0 / 60.0 + 0.001): late.append("%s@%s" % [L.kind, L.t])
		check(late.is_empty(), "moment %s: every layer starts within a frame of its time %s" % [r.id, str(late)])
	# Fixture rows for cases 3-10.
	var fx_row := func(id: String, event: String, pri: int, dur: float, layers: Array, extra := {}) -> Dictionary:
		var r := {"id": id, "event": event, "when": {}, "priority": pri, "duration_s": dur, "lock_s": 0.0, "skip": "", "skip_to_s": 0.0,
			"stale_s": 6.0, "in_fight": "play", "scope": "actor", "merge": [], "hold_until": [], "max_s": 0.0,
			"toast": {"key": "world_view.level", "args": [pri]}, "layers": layers, "art": [], "sample": {}, "step": "test"}
		r.merge(extra, true)
		return r
	var band := {"t": 0.0, "kind": "band", "y": 138}
	var fixtures: Array = [
		fx_row.call("major", "breakthrough_succeeded", 70, 4.0, [{"t": 0.0, "kind": "dim", "alpha": 0.45}, {"t": 0.0, "kind": "sound", "sfx": "breakthrough"},
			{"t": 0.0, "kind": "fx", "fx": "spark", "at": "actor", "count": 16}, {"t": 0.0, "kind": "buzz", "ms": 120}, {"t": 0.0, "kind": "camera", "to": "actor"},
			{"t": 0.2, "kind": "flash", "alpha": 0.35}, {"t": 0.6, "kind": "shake", "s": 0.2}, {"t": 0.6, "kind": "band", "y": 138},
			{"t": 0.6, "kind": "letterbox", "height": 64}],
			{"when": {"actor": "active", "major": true}, "lock_s": 1.5, "skip": "tap", "skip_to_s": 2.4,
			"merge": [{"event": "level_changed", "into": "level"}, {"event": "realm_changed", "into": ""}, {"event": "system_unlocked", "into": "unlocks", "max": 2}]}),
		fx_row.call("cloud", "heavenly_phenomenon", 0, 5.5, [{"t": 0.0, "kind": "fx", "fx": "heaven_cloud", "at": "actor"}], {"when": {"kind": "cloud"}}),
		fx_row.call("level", "level_changed", 0, 1.0, [{"t": 0.0, "kind": "sound", "sfx": "level"}]),
		fx_row.call("title", "title_changed", 40, 1.2, [band], {"when": {"earned": true}, "in_fight": "toast"}),
		fx_row.call("dao", "dao_tier_up", 50, 1.2, [band], {"in_fight": "toast"}),
		fx_row.call("rare", "loot_dropped", 40, 1.2, [band], {"in_fight": "toast", "stale_s": 9.0}),
		fx_row.call("phase", "boss_phase", 90, 1.2, [band, {"t": 0.0, "kind": "sound", "sfx": "boss_roar"}], {"stale_s": 1.0, "toast": {}}),
		fx_row.call("intro", "enemy_aggro", 90, 2.0, [{"t": 0.0, "kind": "letterbox", "height": 64}], {"scope": "room", "stale_s": 1.5, "toast": {}}),
		fx_row.call("trial", "room_event_started", 60, 1.8, [band], {"scope": "room"}),
		fx_row.call("long", "quest_completed", 95, 8.0, [band], {"toast": {}})]
	mv.load_rows(fixtures)
	var burst := func() -> void:
		feed.call("breakthrough_succeeded", {"actor": "", "from": "will_manifest_3", "to": "sphere_lord_1", "major": true, "formation": ""})
		feed.call("level_changed", {"actor": "", "level": 91})
		feed.call("realm_changed", {"actor": "", "from": "will_manifest_3", "to": "sphere_lord_1", "major": true, "level": 91})
		feed.call("system_unlocked", {"actor": "", "system": "sphere", "toast": true, "label": "the Sphere"})
		feed.call("system_unlocked", {"actor": "", "system": "sphere_domain", "toast": true, "label": "the Domain"})
		feed.call("heavenly_phenomenon", {"actor": "", "kind": "cloud", "realm": "sphere_lord_1", "room": "x", "people": 0})
		feed.call("title_changed", {"actor": "", "title": "sphere_lord", "earned": true})
	# 3. Gather and merge.
	mv.logged.clear()
	burst.call()
	mv.advance(0.0)
	check(mv.playing != null and mv.playing.row.id == "major" and mv.playing.slots.has("level") and (mv.playing.slots.get("unlocks", []) as Array).size() == 2,
		"one pass: the major breakthrough plays with its level and two unlocks absorbed")
	check(mv.logged.filter(func(e): return str(e.get("sfx", "")) != "").size() == 1 and played.call("cloud").size() == 1 and played.call("level").is_empty(),
		"the breakthrough's sound plays once; the phenomenon's clouds play; the absorbed level plays nothing of its own")
	check(mv.queue.size() == 1 and mv.queue[0].row.id == "title", "the title waits for the screen")
	# 4. Queue order: priority, then arrival.
	feed.call("loot_dropped", {"room": "x", "items": [], "x": 0, "y": 0})
	feed.call("dao_tier_up", {"actor": "", "dao": "sword", "tier": 3})
	var order: Array = []
	for i in 600:
		mv.advance(1.0 / 60.0)
		if mv.playing != null and (order.is_empty() or order.back() != mv.playing.row.id): order.append(mv.playing.row.id)
	check(order == ["major", "dao", "title", "rare"], "after the breakthrough: the Dao tier, then the title and the rare drop by arrival (%s)" % str(order))
	# 5. A cut: a boss phase 1.0 s into the breakthrough.
	mv.clear()
	mv.toasts_posted.clear()
	burst.call()
	run.call(1.0)
	feed.call("boss_phase", {"enemy": 7, "phase": 2, "action": ""})
	mv.advance(1.0 / 60.0)
	check(mv.playing != null and mv.playing.row.id == "phase" and mv.fading != null and mv.fading.row.id == "major" and mv.toasts_posted.size() == 1,
		"a boss phase cuts the breakthrough, which leaves its toast")
	run.call(0.15)
	check(mv.fading == null, "the cut row fades out within 0.15 s")
	run.call(8.0)
	check(not mv.logged.any(func(e): return str(e.row) == "major" and float(e.t) > 1.1 and str(e.layer) == "band"), "the cut row does not come back")
	# 6. Stale and full.
	mv.clear()
	mv.toasts_posted.clear()
	feed.call("quest_completed", {"actor": "", "quest": "q", "name": "Q", "kind": "main"})
	mv.advance(0.0)
	for i in 3: feed.call("dao_tier_up", {"actor": "", "dao": "sword", "tier": i + 1})
	for i in 2: feed.call("title_changed", {"actor": "", "title": "t%d" % i, "earned": true})
	mv.advance(0.0)
	check(mv.queue.size() == 4 and mv.toasts_posted.size() == 1, "a fifth waiting row drops the lowest to its toast at once")
	feed.call("boss_phase", {"enemy": 7, "phase": 3, "action": ""})
	mv.advance(0.0)
	run.call(1.1)
	check(not mv.queue.any(func(q): return q.row.id == "phase") and mv.toasts_posted.size() == 2, "a waiting boss phase drops after 1.0 s, with no toast")
	run.call(6.0)
	check(mv.queue.is_empty() and mv.toasts_posted.size() == 5, "every row that waited past its stale time drops to its toast (%d)" % mv.toasts_posted.size())
	# 7. Pages and fights.
	mv.clear()
	mv.logged.clear()
	mv.pages_override = true
	burst.call()
	mv.advance(0.0)
	check(mv.playing == null and not played.call("major").is_empty() and mv.queue.any(func(q): return q.row.id == "major"), "under a page the world layers play and the screen part waits")
	mv.pages_override = false
	mv.advance(1.0 / 60.0)
	check(mv.playing != null and mv.playing.row.id == "major", "the screen part starts when the page closes")
	mv.clear()
	mv.toasts_posted.clear()
	mv.fight_override = true
	burst.call()
	mv.advance(0.0)
	check(mv.toasts_posted.size() == 1 and not mv.queue.any(func(q): return q.row.id == "title") and mv.lock_left() == 0.0,
		"in a fight the title is a toast, and the breakthrough takes no lock")
	mv.fight_override = false
	# 8. Room change.
	mv.clear()
	mv.toasts_posted.clear()
	feed.call("enemy_aggro", {"enemy": 3, "target": "", "def": "big_toad_tan"})
	mv.advance(0.0)
	feed.call("room_event_started", {"actor": "", "room": "x", "event": "heart_trial", "duration": 60})
	feed.call("title_changed", {"actor": "", "title": "t9", "earned": true})
	mv.advance(0.0)
	feed.call("room_left", {"actor": c.id, "room": "x", "portal": ""})
	mv.advance(0.0)
	check(not (mv.playing != null and mv.playing.row.id == "intro") and not mv.queue.any(func(q): return q.row.id == "trial") and mv.toasts_posted.is_empty()
		and ((mv.playing != null and mv.playing.row.id == "title") or mv.queue.any(func(q): return q.row.id == "title")),
		"leaving the room ends the boss intro and the waiting trial with no toast; the title survives")
	# 9. Settings.
	var put := func(k: String, v) -> void: Game.account.settings[k] = v
	mv.clear()
	mv.logged.clear()
	put.call("screen_shake", false)
	put.call("flashes", false)
	put.call("reduce_motion", true)
	put.call("haptics", false)
	burst.call()
	run.call(1.0)
	var shakes: Array = played.call("major").filter(func(e): return str(e.layer) == "shake")
	check(not shakes.is_empty() and shakes.all(func(e): return float(e.amp) == 0.0), "with Screen shake off every shake is still")
	var flash: Array = played.call("major").filter(func(e): return str(e.layer) == "flash")
	check(flash.size() == 1 and near(float(flash[0].alpha), 0.35 * 0.3), "with Bright flashes off a flash is 0.3 of its alpha")
	check(not played.call("major").any(func(e): return str(e.layer) in ["camera", "buzz"]), "with Reduce motion no camera move, with Vibration off no buzz")
	check(played.call("major").filter(func(e): return str(e.layer) in ["band", "letterbox"]).all(func(e): return not e.motion), "with Reduce motion bands and letterboxes do not slide")
	var sp: Array = played.call("major").filter(func(e): return str(e.layer) == "fx")
	check(sp.size() == 1 and int(sp[0].count) == int(MomentRules.tier(1).spark_count), "with Reduce motion a burst has tier 1's particles")
	put.call("damage_numbers", false)
	var fl := FxLayer.new()
	fl.number(Vector2.ZERO, "12", UiKit.PAPER)
	fl.label(Vector2.ZERO, Tx.t("world_view.miss"), UiKit.MIST)
	check(fl.fx.size() == 1, "with Damage numbers off no damage number rises; Miss still does")
	fl.free()
	for k in ["screen_shake", "flashes", "reduce_motion", "haptics", "damage_numbers"]: Game.account.settings[k] = was.get(k, k != "reduce_motion")
	if not was.has("reduce_motion"): Game.account.settings.erase("reduce_motion")
	# 10. The lock.
	for r in fixtures:
		mv.clear()
		mv.load_rows([r])
		feed.call(str(r.event), {"actor": "", "major": true, "earned": true, "kind": "cloud", "enemy": 1, "target": ""})
		var most := 0.0
		for i in int(float(r.duration_s) * 60.0) + 2:
			mv.advance(1.0 / 60.0)
			most = maxf(most, mv.lock_left())
			if mv.playing != null and float(mv.playing.st) > float(r.lock_s) + 1.0 / 60.0 and mv.lock_left() > 0.0: most = 99.0
		check(most <= minf(float(r.lock_s), 1.5), "moment %s holds input at most its lock (%.2f s)" % [r.id, most])
	mv.load_rows(fixtures)
	burst.call()
	run.call(0.5)
	check(mv.lock_left() > 0.0 and mv.press() and mv.lock_left() == 0.0 and near(float(mv.playing.st), 2.4), "a tap during the breakthrough's lock skips to 2.4 s and gives input back")
	mv.clear()
	mv.fight_override = true
	burst.call()
	mv.advance(0.0)
	check(mv.lock_left() == 0.0, "no lock starts in a fight")
	mv.fight_override = false
	mv.clear()
	burst.call()
	run.call(0.3)
	mv.fight_override = true
	mv.advance(1.0 / 60.0)
	check(mv.lock_left() == 0.0, "a running lock ends the frame a fight starts")
	mv.fight_override = false
	# The real rows (P6b on): cases 3, 7, 9, 10 and 11 again, F4, and case 2 through the real authorities.
	var fresh := func() -> void:
		mv.load_rows(real)
		mv.logged.clear()
		mv.toasts_posted.clear()
	fresh.call()
	burst.call()
	mv.advance(0.0)
	check(mv.playing != null and mv.playing.row.id == "breakthrough_major" and mv.playing.slots.has("level") and (mv.playing.slots.get("unlocks", []) as Array).size() == 2
		and mv.logged.filter(func(e): return str(e.get("sfx", "")) == "breakthrough").size() == 1 and not played.call("realm_phenomenon").is_empty()
		and mv.queue.any(func(q): return q.row.id == "title_earned"), "the major breakthrough takes its level and unlocks and rings once; the clouds play; the title waits")
	run.call(0.5)
	check(mv.lock_left() > 0.0 and mv.press() and mv.lock_left() == 0.0 and near(float(mv.playing.st), 2.4), "a tap in the breakthrough's first 1.5 s skips to 2.4 s and gives input back")
	var longest := 0.0
	for r in real:
		fresh.call()
		feed.call(str(r.event), r.sample)
		for i in int(float(r.duration_s) * 60.0) + 2:
			mv.advance(1.0 / 60.0)
			longest = maxf(longest, mv.lock_left())
	check(longest <= 1.5, "F4: no moment holds input for more than 1.5 s (%.2f s)" % longest)
	fresh.call()
	mv.pages_override = true
	burst.call()
	mv.advance(0.0)
	check(mv.playing == null and played.call("breakthrough_major").any(func(e): return str(e.layer) == "fx"), "under a page the breakthrough's light gathers and its name waits")
	mv.pages_override = false
	mv.advance(1.0 / 60.0)
	check(mv.playing != null and mv.playing.row.id == "breakthrough_major", "the breakthrough's name is written when the page closes")
	fresh.call()
	mv.toasts_posted.clear()
	mv.fight_override = true
	burst.call()
	mv.advance(0.0)
	check(mv.toasts_posted.size() == 1 and mv.lock_left() == 0.0 and mv.playing != null and mv.playing.row.id == "breakthrough_major",
		"in a fight the title is a toast and the breakthrough plays without a lock")
	mv.fight_override = false
	for k in ["screen_shake", "flashes", "haptics"]: put.call(k, false)
	put.call("reduce_motion", true)
	fresh.call()
	burst.call()
	run.call(1.0)
	var major: Array = played.call("breakthrough_major")
	check(major.filter(func(e): return str(e.layer) == "shake").all(func(e): return float(e.amp) == 0.0) and not major.any(func(e): return str(e.layer) == "buzz")
		and major.filter(func(e): return str(e.layer) == "band").all(func(e): return not e.motion)
		and major.filter(func(e): return str(e.get("fx", "")) == "converge").all(func(e): return int(e.count) == int(MomentRules.tier(1).spark_count)),
		"the settings hold on the real breakthrough: no shake, no buzz, the band fades, the motes thin to tier 1's")
	fresh.call()
	feed.call("tribulation_started", ContentDB.entry("moments", "tribulation").sample)
	mv.advance(0.0)
	check(played.call("tribulation").filter(func(e): return str(e.layer) == "vignette").all(func(e): return near(float(e.alpha), 0.25 * 0.3)), "with Bright flashes off the tribulation's shadow is 0.3 of its alpha")
	for k in ["screen_shake", "flashes", "haptics", "reduce_motion"]: Game.account.settings[k] = was.get(k, k != "reduce_motion")
	# 11. A held row: the storm is laid again every 5 s until the result, and ends at max_s without one.
	fresh.call()
	feed.call("tribulation_started", ContentDB.entry("moments", "tribulation").sample)
	mv.advance(0.0)
	run.call(11.0)
	var storms: Array = played.call("tribulation").filter(func(e): return str(e.get("fx", "")) == "heaven_storm")
	check(storms.size() == 3 and mv.active.any(func(q): return q.row.id == "tribulation"), "the tribulation's storm is laid again every 5 s while it holds (%d)" % storms.size())
	feed.call("tribulation_result", {"actor": "", "survived": true, "struck": 1, "absorbed": 0, "bolts": 9, "failure": ""})
	run.call(2.0 / 60.0)
	check(not mv.active.any(func(q): return q.row.id == "tribulation"), "the tribulation ends with its result")
	feed.call("tribulation_started", ContentDB.entry("moments", "tribulation").sample)
	mv.advance(0.0)
	run.call(121.0)
	check(not mv.active.any(func(q): return q.row.id == "tribulation"), "a tribulation with no result ends at its 120 s guard")
	# 2. Real events: a minor breakthrough at a bottleneck and a level gained by meditating.
	var cu: CultivatorState = c.cultivator
	var keep := [cu.realm_key, cu.state, cu.qp, cu.breakthrough_cooldown, Unlocks.debug_force_all]
	Unlocks.debug_force_all = true   # the suite's character has not been taught to cultivate
	fresh.call()
	cu.realm_key = "bone_forging_2"
	cu.state = "bottleneck"
	cu.qp = cu.need()
	cu.breakthrough_cooldown = 0.0
	var bt := Game.submit({"type": "start_breakthrough", "support_items": []})
	mv.advance(0.0)
	check(bool(bt.get("ok", false)) and mv.playing != null and mv.playing.row.id == "breakthrough_minor" and mv.playing.slots.has("level"),
		"a real minor breakthrough writes its strip with the level it gave (%s)" % str(bt))
	fresh.call()
	cu.realm_key = "heaven_glimpse_1"
	cu.state = "accumulating"
	cu.qp = 0.0
	Game.progression.apply_progress(c.id, 0.0, "meditation", 0.5)
	GameEvents.flush()
	mv.advance(0.0)
	check(played.call("level_up").any(func(e): return str(e.get("sfx", "")) == "gong_short"), "a level gained by meditating sounds its short gong")
	cu.realm_key = keep[0]
	cu.state = keep[1]
	cu.qp = keep[2]
	cu.breakthrough_cooldown = keep[3]
	Unlocks.debug_force_all = keep[4]
	Game.combat.refresh_stats(c.id)
	# P6c: Big Toad Tan's den. A real aggro opens the intro once a visit; his 49% opens the phase card; a fall cuts nothing.
	var room_was: String = Game.room_rt.room_id if Game.room_rt else "lf_village"
	Game.world.load_room(c, "mh_boss_den", "")
	GameEvents.flush()
	var st2: ActorState = Game.actor_state(c.id)
	var toad: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "big_toad_tan": toad = e
	if toad == null: toad = Game.enemies.spawn_at("big_toad_tan", st2.plane + Vector2(160, 0), 18)
	fresh.call()
	mv.advance(0.0)
	c.pools.hp = c.pools.max_hp
	for sid in ["stun", "slow", "spawn_protection"]: Game.combat.cure_status(c.id, sid)
	st2.plane = toad.plane + Vector2(-140, 0)
	for i in 40:
		Game.tick(0.05)
		c.pools.hp = c.pools.max_hp
		mv.advance(0.05)
		if not played.call("boss_intro").is_empty(): break
	check((mv.playing != null and mv.playing.row.id == "boss_intro") or played.call("boss_intro").any(func(e): return str(e.get("sfx", "")) == "boss_sting"),
		"Big Toad Tan's first aggro in his den opens the boss intro")
	check(MomentRules.text({"first": [{"boss": "epithet", "id": "payload.def"}, {"key": "moment.boss.level", "args": ["enemy.level"]}]},
		{"enemy": toad.uid, "def": "big_toad_tan"}) == Tx.t("moment.boss.level") % toad.level, "before P9's epithets the intro names his level")
	var stings := func() -> int: return mv.logged.filter(func(e): return str(e.get("sfx", "")) == "boss_sting").size()
	var intros: int = stings.call()
	feed.call("enemy_aggro", {"enemy": toad.uid, "target": "", "def": "big_toad_tan"})
	run.call(2.1)
	check(stings.call() == intros and mv.playing == null, "his second aggro in the same visit opens nothing")
	toad.pools.hp = toad.pools.max_hp * 0.49
	Game.enemies._check_phases(toad)
	GameEvents.flush()
	mv.advance(0.0)
	check(mv.playing != null and mv.playing.row.id == "boss_phase", "at 49%% his phase card cuts in (%s)" % str(mv.playing.row.id if mv.playing else ""))
	# Case 5 on the real rows: a boss phase 1.0 s into the major breakthrough cuts it, and it leaves its toast.
	fresh.call()
	burst.call()
	run.call(1.0)
	feed.call("boss_phase", {"enemy": toad.uid, "phase": 1, "action": ""})
	mv.advance(1.0 / 60.0)
	check(mv.playing != null and mv.playing.row.id == "boss_phase" and mv.fading != null and mv.toasts_posted.size() == 1, "a phase card cuts the breakthrough, which leaves its toast")
	# Case 8 on the real rows: leaving the room ends the intro with no toast.
	fresh.call()
	feed.call("room_entered", {"actor": c.id, "room": "mh_boss_den"})
	feed.call("enemy_aggro", {"enemy": toad.uid, "target": "", "def": "big_toad_tan"})
	mv.advance(0.0)
	feed.call("room_left", {"actor": c.id, "room": "mh_boss_den", "portal": ""})
	mv.advance(0.0)
	check(mv.playing == null and mv.toasts_posted.is_empty(), "leaving the den ends his intro, with no toast")
	# The fall: a clean kill writes the Untouched line and takes the achievement in; the drop says it is a boss's.
	fresh.call()
	var drops: Array = []
	var grab := func(n: String, p: Dictionary): if n == "loot_dropped": drops.append(p)
	GameEvents.event.connect(grab)
	Game.world._on_actor_defeated({"victim": str(toad.uid), "victim_kind": "enemy", "def": "big_toad_tan", "role": "dungeon_boss", "killer": c.id,
		"x": toad.plane.x, "y": toad.plane.y, "level": toad.level})
	GameEvents.flush()
	GameEvents.event.disconnect(grab)
	check(not drops.is_empty() and drops.all(func(p): return str(p.get("source", "")) == "boss"), "a boss's drop says so (source boss)")
	feed.call("boss_defeated", {"room": "mh_boss_den", "enemy": "big_toad_tan", "role": "dungeon_boss", "clean": true})
	feed.call("achievement_unlocked", {"actor": "", "id": "untouched", "name": "Untouched"})
	for d in drops: mv._on_event("loot_dropped", d)
	mv.advance(0.0)
	check(mv.playing != null and mv.playing.row.id == "boss_defeated" and mv.playing.slots.has("untouched")
		and MomentRules.text({"key": "moment.boss.untouched", "if": "clean"}, mv.playing.p) != "", "his fall is written with the Untouched line")
	check(played.call("loot_fountain").any(func(e): return str(e.layer) == "fountain" and not e.bounce), "his drop flies out in a fountain")
	put.call("reduce_motion", true)
	fresh.call()
	for d in drops: mv._on_event("loot_dropped", d)
	mv.advance(0.0)
	check(played.call("loot_fountain").any(func(e): return str(e.layer) == "fountain" and e.bounce), "with Reduce motion the drop only bounces")
	Game.account.settings["reduce_motion"] = was.get("reduce_motion", false)
	fresh.call()
	mv._on_event("loot_dropped", {"room": "x", "items": [], "x": 0.0, "y": 0.0, "source": "jar"})
	mv.advance(0.0)
	check(played.call("loot_fountain").is_empty(), "a jar's drop keeps today's bounce")
	# P6d. Case 14: the rare rule.
	var legend_piece := ""
	for it in ContentDB.all("items"):
		if str(it.get("type", "")) == "legend_piece": legend_piece = str(it.id)
	check(MomentRules.is_rare({"item": "training_spear", "quality": "perfect"}) and MomentRules.is_rare({"item": legend_piece}) and MomentRules.is_rare({"item": "jade_current_hat"})
		and not MomentRules.is_rare({"item": "", "coins": 50}) and not MomentRules.is_rare({"item": "willow_moss", "quality": "common"}),
		"rare: a Perfect piece, a legend piece and a set piece; not coins, not a common herb")
	# Case 4 on the real rows: after the breakthrough, the Dao tier (50), then the title and the rare find (40) by arrival.
	var find := {"room": "x", "items": [{"uid": 901, "item": "mudwater_cleaver", "count": 1, "coins": 0, "quality": "common"}], "x": 0.0, "y": 0.0, "source": "enemy"}
	fresh.call()
	burst.call()
	mv._on_event("loot_dropped", find)
	feed.call("dao_tier_up", {"actor": "", "dao": "sword", "tier": 3})
	var seq: Array = []
	for i in 720:
		mv.advance(1.0 / 60.0)
		if mv.playing != null and (seq.is_empty() or seq.back() != mv.playing.row.id): seq.append(mv.playing.row.id)
	check(seq == ["breakthrough_major", "dao_tier", "title_earned", "rare_drop"], "the queue after a breakthrough: %s" % str(seq))
	# Rare finds within 1.5 s share one strip.
	fresh.call()
	mv._on_event("loot_dropped", find)
	mv.advance(0.0)
	run.call(0.5)
	mv._on_event("loot_dropped", {"room": "x", "items": [{"uid": 902, "item": "jade_current_hat", "count": 1, "coins": 0, "quality": "common"}], "x": 0.0, "y": 0.0, "source": "chest"})
	mv.advance(0.0)
	var strips: Array = mv.active.filter(func(q): return q.row.id == "rare_drop" and not q.joined)
	check(strips.size() == 1 and (strips[0].slots.rare as Array).size() == 2 and mv.queue.is_empty(), "two rare finds 0.5 s apart share one strip")
	# A chapter's last main quest waits for its dialogue page, then closes the chapter; another main quest does not.
	fresh.call()
	mv.pages_override = true
	feed.call("quest_completed", {"actor": "", "quest": "strange_tracks", "name": "Strange Tracks", "kind": "main"})
	feed.call("quest_completed", {"actor": "", "quest": "mudwater_hideout", "name": "Mudwater Hideout", "kind": "main"})
	mv.advance(0.0)
	check(mv.playing == null and mv.queue.size() == 1 and mv.queue[0].row.id == "story_beat", "the chapter's close waits for the dialogue page")
	mv.pages_override = false
	mv.advance(1.0 / 60.0)
	check(mv.playing != null and mv.playing.row.id == "story_beat" and MomentRules.text({"chapter_of": "payload.quest"}, mv.playing.p) == Tx.t("moment.story.chapter") % "3",
		"then Chapter 3 closes on Mudwater Hideout")
	# P6e. Case 12: the escalation curve. One technique per tier the data has: its tier's row, a spark laid with it
	# carries that count and size, a companion's blow of it one tier lower, a basic blow tier 1.
	var by_tier := {}
	for t in ContentDB.all("techniques"): by_tier[int(t.vfx.tier)] = str(t.id)
	check(by_tier.size() >= 5, "techniques reach five tiers of the curve (%s)" % str(by_tier.keys()))
	var fl2 := FxLayer.new()
	for n in by_tier:
		var row := MomentRules.tier_numbers("tech:" + str(by_tier[n]))
		fl2.add("spark", Vector2.ZERO, {"count": row.spark_count, "size": row.spark_size, "radius": row.spark_reach})
		check(int(row.tier) == n and int(fl2.fx.back().count) == int(MomentRules.tier(n).spark_count) and int(fl2.fx.back().size) == int(MomentRules.tier(n).spark_size),
			"tier %d (%s): its sparks are %d of %d px" % [n, by_tier[n], int(row.spark_count), int(row.spark_size)])
		check(int(MomentRules.tier_numbers("ally:tech:" + str(by_tier[n])).tier) == maxi(1, n - 1), "a companion's %s draws a tier lower" % by_tier[n])
	check(int(MomentRules.tier_numbers("").tier) == 1 and int(MomentRules.tier_numbers("ally:c1").tier) == 1, "a basic blow and a companion's own blow draw at tier 1")
	check(MomentRules.particle_style("brush", "fire") == "ink" and MomentRules.particle_style("", "fire") == "ember" and MomentRules.particle_style("", "none", "soul") == "ring"
		and MomentRules.particle_style("jian", "water") == "square", "spark styles: the brush's ink, fire's embers, Soul's rings, else squares")
	# A tier-3 cast's tint: none with Reduce motion, 0.3 of its alpha with Bright flashes off, one a second.
	fl2.fx.clear()
	MomentView._flash_ms = -100000
	put.call("reduce_motion", true)
	fl2.add("tint", Vector2.ZERO, {"color": Color(UiKit.GOLD, 0.1)})
	put.call("reduce_motion", false)
	put.call("flashes", false)
	fl2.add("tint", Vector2.ZERO, {"color": Color(UiKit.GOLD, 0.1)})
	fl2.add("tint", Vector2.ZERO, {"color": Color(UiKit.GOLD, 0.1)})
	check(fl2.fx.size() == 1 and near(float(fl2.fx[0].color.a), 0.03), "a tint: none with Reduce motion, dimmed with Bright flashes off, one a second")
	fl2.free()
	# Case 13: multi-hit numbers. Three hits of Flying Blades on one foe rise 18 px apart, 0.06 s apart, swaying, then a
	# total in pale gold; seven give six numbers and a total of seven.
	put.call("damage_numbers", true)
	var key := "e1tech:flying_blades"
	var fl3 := FxLayer.new()
	for i in 3: fl3.number(Vector2(100, 200), UiKit.short(4000.0), UiKit.PAPER, 24, false, key, 4000.0)
	var nums: Array = fl3.fx.filter(func(e): return e.kind == "number")
	var laid := nums.size() == 3
	for i in nums.size():
		laid = laid and near(float(nums[i].pos.y), 200.0 - 18.0 * i) and near(float(nums[i].t), -0.06 * i) and near(float(nums[i].pos.x), 100.0 + (12.0 if i % 2 == 0 else -12.0))
	check(laid, "three hits: 18 px apart, 0.06 s apart, on alternating sides")
	for i in 30: fl3._process(1.0 / 60.0)
	var tot: Array = fl3.fx.filter(func(e): return e.kind == "number" and e.color == UiKit.PALE_GOLD)
	check(tot.size() == 1 and str(tot[0].text) == UiKit.short(12000.0) and int(tot[0].size) == 26 and fl3.stacks.is_empty(), "then their total, 12.0K, a size up")
	fl3.fx.clear()
	for i in 7: fl3.number(Vector2(100, 200), UiKit.short(3000.0), UiKit.PAPER, 24, false, key, 3000.0)
	check(fl3.fx.size() == 6, "seven hits show six numbers")
	for i in 40: fl3._process(1.0 / 60.0)
	check(fl3.fx.filter(func(e): return e.color == UiKit.PALE_GOLD).map(func(e): return str(e.text)) == [UiKit.short(21000.0)], "and a total of all seven")
	fl3.fx.clear()
	for i in 2: fl3.number(Vector2(100, 200), "10", UiKit.PAPER, 24, false, key, 10.0)
	for i in 40: fl3._process(1.0 / 60.0)
	check(not fl3.fx.any(func(e): return e.color == UiKit.PALE_GOLD), "two hits add up to no total")
	fl3.free()
	# Decision 23, case 15: technique animations. Every technique names a built form; a cast's sprite takes its element's
	# row at its tier's band (Reduce motion the calmest, Battery saver the middle at most), a sub-element its parent's
	# row and `none` the formless one; scales snap to halves; a form plays for its frames' length, facing the cast.
	var fxa: Dictionary = ContentDB.config("fx_art")
	var n_el: int = (fxa.elements as Array).size()
	check(fxa.forms.size() == 24 and ContentDB.all("techniques").all(func(t): return fxa.forms.has(str(t.vfx.get("anim", "")))), "every technique names one of the 24 built forms")
	var was_rm = Game.account.settings.get("reduce_motion")
	var was_bs = Game.account.settings.get("battery_saver")
	put.call("reduce_motion", false)
	put.call("battery_saver", false)
	check(FxLayer.band_of(1) == 0 and FxLayer.band_of(2) == 0 and FxLayer.band_of(3) == 1 and FxLayer.band_of(5) == 2 and FxLayer.band_of(7) == 2, "bands: tiers 1-2, 3-4 and 5-7")
	put.call("battery_saver", true)
	check(FxLayer.band_of(5) == 1, "Battery saver plays a tier-5 form at the middle band")
	put.call("reduce_motion", true)
	check(FxLayer.band_of(5) == 0, "Reduce motion plays it at the calmest")
	put.call("reduce_motion", false)
	put.call("battery_saver", false)
	check(FxLayer.form_row("water", 0) == 0 and FxLayer.form_row("fire", 2) == 2 * n_el + 2 and FxLayer.form_row("none", 1) == n_el + 8 and FxLayer.form_row("ice", 1) == n_el,
		"rows: water first, fire's at the third band, formless for none, ice with water")
	check(FxLayer.snap_scale(1.3) == 1.5 and FxLayer.snap_scale(1.3, true) == 1.0 and FxLayer.snap_scale(0.1) == 0.5 and FxLayer.snap_scale(9.0) == 4.0, "sprite scales snap to halves inside 0.5 to 4")
	var fl4 := FxLayer.new()
	var strike: Dictionary = fxa.forms.strike
	fl4.play_form("strike", "wind", 3, Vector2(10, 20), -1, {"scale": 1.5, "delay": 0.1})
	check(fl4.fx.size() == 1 and str(fl4.fx[0].kind) == "anim" and int(fl4.fx[0].facing) == -1 and near(float(fl4.fx[0].t), -0.1)
		and near(float(fl4.fx[0].dur), float(strike.frames) / float(strike.fps)) and int(fl4.fx[0].row) == n_el + 5 and near(float(fl4.fx[0].scale), 1.5),
		"a Wind strike at tier 3: an anim facing left, 0.1 s off, for its frames, at wind's row of the middle band")
	fl4.play_form("strike", "wind", 1, Vector2.ZERO, 1, {"start": 0.2})
	check(near(float(fl4.fx[1].dur), float(strike.frames) / float(strike.fps) - 0.2) and FxLayer.form_frame(strike, 0.2 + 0.05) == int(0.25 * float(strike.fps)),
		"started part-way in, it plays the rest and reads its frame from where it began")
	check(fl4.play_form("no_such_form", "wind", 1, Vector2.ZERO, 1).is_empty() and fl4.fx.size() == 2, "a form without a sheet plays nothing")
	fl4.free()
	if was_rm == null: Game.account.settings.erase("reduce_motion")
	else: Game.account.settings.reduce_motion = was_rm
	if was_bs == null: Game.account.settings.erase("battery_saver")
	else: Game.account.settings.battery_saver = was_bs
	# A counted text picks its "_one" twin (P4 plurals): one bolt, nine bolts.
	var bolts := {"key": "hud.tribulation_started", "args": ["payload.bolts"], "plural": "payload.bolts"}
	check(MomentRules.text(bolts, {"bolts": 1}) == Tx.t("hud.tribulation_started_one") % 1 and MomentRules.text(bolts, {"bolts": 9}) == Tx.t("hud.tribulation_started") % 9,
		"a moment's counted line is singular for one")
	for k in ["flashes", "reduce_motion", "damage_numbers"]: Game.account.settings[k] = was.get(k, k != "reduce_motion")
	if not was.has("reduce_motion"): Game.account.settings.erase("reduce_motion")
	Game.world.load_room(c, room_was, "")
	GameEvents.flush()
	mv.queue_free()

func boss_event_suite() -> void:
	var c = Game.active()
	if c == null: return
	var seen: Array = []
	var grab := func(n: String, p: Dictionary): if n == "boss_defeated": seen.append(p)
	GameEvents.event.connect(grab)
	var room := Game.room_rt.room_id if Game.room_rt else "lf_village"
	Game.enemies.wounded_here = false
	Game.enemies._on_defeated({"victim": "e1", "victim_kind": "enemy", "def": "big_toad_tan", "role": "dungeon_boss", "killer": c.id, "room": room})
	GameEvents.flush()
	check(seen.size() == 1 and bool(seen[0].get("clean", false)), "a dungeon boss beaten with no grave wound is a clean boss_defeated")
	Game.enemies.wounded_here = true
	Game.enemies._on_defeated({"victim": "e2", "victim_kind": "enemy", "def": "big_toad_tan", "role": "dungeon_boss", "killer": c.id, "room": room})
	GameEvents.flush()
	check(seen.size() == 2 and not bool(seen[1].get("clean", true)), "after a grave wound in the room it is not clean")
	Game.enemies._on_defeated({"victim": "e3", "victim_kind": "enemy", "def": "mudshell_crab", "role": "normal", "killer": c.id, "room": room})
	GameEvents.flush()
	check(seen.size() == 2, "an ordinary foe announces no boss_defeated")
	GameEvents.event.disconnect(grab)
	Game.enemies.wounded_here = false

## P7a, P7b (item_plan §4.1): the equipment roll. Only banded bases, up to the highest banded grade's top Level; 40%
## weapons, a third of those in the family in hand; qualities from the source's floor; named rows and their floor;
## the archetype affixes never rolled at random.
func drop_pool_suite() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var cap := LootRules.drop_level_cap()
	var bad: Array = []
	var top := 0
	for level in [64, 70, 76, 81, 90, 99]:
		for i in 400:
			var inst: Dictionary = LootRules.make_equipment(rng, level, "common", 0.0, true, i)
			if inst.is_empty(): continue
			var def: Dictionary = ContentDB.item(str(inst.id))
			top = maxi(top, int(inst.ilv))
			if def.has("legend") or def.has("imitation") or def.has("named") or def.has("set") or def.has("pet_gear") or str(def.slot) in ["gourd", "cape", "talisman", "tool_furnace"]:
				bad.append(str(inst.id))
	check(bad.is_empty(), "no legendary weapon, imitation relic, named, set or pet piece and no gourd, cape, talisman or furnace from an ordinary equipment drop (%s)" % str(bad.slice(0, 4)))
	var cap_grade := LootRules.grade_for_ilv(cap)
	check(top == cap and ContentDB.all("artifacts").any(func(a): return LootRules.is_banded(a) and str(a.grade) == cap_grade)
		and not ContentDB.all("artifacts").any(func(a): return LootRules.is_banded(a) and StatRules.grade_index(str(a.grade)) > StatRules.grade_index(cap_grade)),
		"the item Level stops at %d, the top of the highest grade with banded bases (%s; highest made %d)" % [cap, cap_grade, top])
	# Which base: weapons on 40% of rolls, a third of those in the wielded family; armour only with weapons locked.
	var fams := {}
	for a in ContentDB.all("artifacts"):
		if LootRules.is_banded(a) and str(a.slot) == "weapon" and str(a.grade) == "earth": fams[str(a.family)] = true
	var tally := func(family: String, weapons: bool) -> Dictionary:
		var t := {"n": 0, "weapon": 0, "own": 0}
		for i in 3000:
			var inst: Dictionary = LootRules.make_equipment(rng, 30, "flawed", 0.0, weapons, i, family)
			var def: Dictionary = ContentDB.item(str(inst.id))
			t.n += 1
			if str(def.slot) == "weapon":
				t.weapon += 1
				if str(def.family) == "jian": t.own += 1
		return t
	var jian: Dictionary = tally.call("jian", true)
	var any: Dictionary = tally.call("", true)
	var want := 1.0 / 3.0 + (2.0 / 3.0) / fams.size()
	check(absf(float(jian.weapon) / jian.n - 0.4) < 0.03, "40%% of rolls make a weapon (%.3f)" % (float(jian.weapon) / jian.n))
	check(absf(float(jian.own) / jian.weapon - want) < 0.05, "a jian in hand: %.3f of weapon drops are jians (%.3f expected of %d families)" % [float(jian.own) / jian.weapon, want, fams.size()])
	check(absf(float(any.own) / any.weapon - 1.0 / fams.size()) < 0.04, "bare hands: jians come as often as any family (%.3f)" % (float(any.own) / any.weapon))
	check(int(tally.call("jian", false).weapon) == 0, "weapons locked: armour only")
	# Qualities from the source's floor.
	var shares := {}
	for i in 4000:
		var q := LootRules.roll_quality(rng, "flawed", 0.0)
		shares[q] = int(shares.get(q, 0)) + 1
	var want_q: Array = LootRules.drop_cfg().get("quality", {}).get("flawed", [])
	var order: Array = ContentDB.config("grades").get("quality_order", [])
	var off := 0.0
	for qi in want_q.size(): off = maxf(off, absf(float(shares.get(order[qi], 0)) / 4000.0 - float(want_q[qi])))
	check(off < 0.03 and not shares.has("perfect"), "a normal foe's drops: 55%% Flawed, 30%% Common, 12%% Fine, 3%% Superior, no Perfect (%s)" % str(shares))
	var boss := {}
	for i in 2000: boss[LootRules.roll_quality(rng, "superior", 0.0)] = true
	check(boss.keys().all(func(q): return q in ["superior", "perfect"]), "a boss's drops start at Superior")
	# Named rows: every kill (elite_named only for an elite), at the source's floor raised to Common; none with no_equipment.
	var t_id := "_named_test"
	ContentDB.tables["loot_tables"][t_id] = {"id": t_id, "equipment": {"chance": 0.0, "min_quality": "flawed"},
		"named": [{"item": "serpent_tongue_jian", "chance": 1.0}], "elite_named": [{"item": "ink_warden_brush", "chance": 1.0}]}
	var plain := LootRules.roll(t_id, rng, 30, 0.0, 0.0)
	var elite := LootRules.roll(t_id, rng, 30, 0.0, 0.0, {"elite": true})
	check(plain.equipment.size() == 1 and str(plain.equipment[0].get("item", "")) == "serpent_tongue_jian" and str(plain.equipment[0].min_quality) == "common",
		"a named row drops its piece at the Common floor (%s)" % str(plain.equipment))
	check(elite.equipment.size() == 2 and LootRules.roll(t_id, rng, 30, 0.0, 0.0, {"no_equipment": true}).equipment.is_empty(),
		"an elite rolls the elite_named rows too; a roll with no equipment rolls no named row")
	ContentDB.tables["loot_tables"].erase(t_id)
	var named_inst := LootRules.make_drop(rng, plain.equipment[0], 0.0, true, 1)
	check(str(named_inst.get("id", "")) == "serpent_tongue_jian" and int(named_inst.ilv) == int(ContentDB.item("serpent_tongue_jian").ilv)
		and str(named_inst.quality) in ["common", "fine", "superior", "perfect"], "a named drop is made at its own iLv (%s)" % str(named_inst))
	# The archetype affixes are the named pieces' fixed affixes, never a random roll.
	var only_named: Array = ContentDB.all("affixes").filter(func(a): return a.get("named_only", false)).map(func(a): return str(a.id))
	var rolled := {}
	for gid in ["jadeiron_gourd", "sunsteel_gourd", "cloudsilk_hat", "stormsteel_bow"]:
		for i in 200:
			for a in LootRules.make_instance(gid, 60, "perfect", rng, i).affixes: rolled[str(a.id)] = true
			rolled[str(LootRules.roll_affix(gid, 60, rng, []).get("id", ""))] = true
	check(only_named.size() == 5 and not only_named.any(func(a): return rolled.has(a)), "no named-only affix (%s) from a random roll" % str(only_named))
	check(rolled.has("qi_attack_pct") and rolled.has("soul_attack_pct") and rolled.has("max_soul_pct"), "the new random affixes roll (%s)" % str(rolled.keys()))

## P7b (item_plan §2.1, §3.1): named pieces and sets. A named piece's fixed affixes (half again on its path) and its
## element; the paths; a set counted across its weapon variants, its 2-piece doubled on the path; each archetype line's
## 6-piece mechanic, read by the rule that owns it. The archetype sets come with the named pieces (item_plan §6 step 8),
## so the test set is built from each line in gear.json.
func set_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear", "bleed", "poison", "burn"]: Game.combat.cure_status(c.id, sid)
	var cu: CultivatorState = c.cultivator
	var equipped_before: Dictionary = c.inventory.equipped.duplicate()
	var daos_before: Dictionary = cu.daos.duplicate(true)
	var body_before := str(cu.body_tier)
	var known_before: Array = cu.techniques_known.duplicate()
	var vows_before: Array = cu.vows.duplicate()
	var paths_before: Dictionary = cu.paths.duplicate()
	var realm_before := str(cu.realm_key)
	var tox_before: float = cu.toxicity
	var total := func(mods: Array, stat: String, suffix: String) -> float:
		var v := 0.0
		for m in mods:
			if str(m.stat) == stat and str(m.get("source", "")).ends_with(suffix): v += float(m.value)
		return v
	# A named piece: its fixed affix; half again while its path is held; +2% elemental power of its element.
	var tags: Dictionary = ContentDB.item("serpent_tongue_jian").named
	var fixed: Dictionary = tags.fixed[0]
	var jian := LootRules.make_instance("serpent_tongue_jian", 30, "common", null, 1)
	cu.daos["sword"] = {"tier": 2, "insight": 0.0}
	var off_path := StatRules.instance_modifiers("weapon", jian, "primal_qi", c)
	var el: Array = off_path.filter(func(m): return str(m.stat) == "elemental_power")
	check(near(total.call(off_path, str(fixed.stat), ":fixed"), float(fixed.value), 0.001) and el.size() == 1 and near(float(el[0].value), 0.02, 0.001)
		and str(el[0].condition.element) == str(tags.element), "the Serpent-Tongue Jian carries its fixed %s and +2%% %s power" % [fixed.stat, tags.element])
	cu.daos["sword"] = {"tier": 3, "insight": 0.0}
	check(StatRules.holds_path(c, "sword_dao") and near(total.call(StatRules.instance_modifiers("weapon", jian, "primal_qi", c), str(fixed.stat), ":fixed"), float(fixed.value) * 1.5, 0.001),
		"Sword Dao 3 holds the sword path: the fixed affix counts half again")
	# The other paths (gear.json `paths`).
	cu.body_tier = "mortal"
	check(not StatRules.holds_path(c, "body_ladder"), "a mortal body holds no body path")
	cu.body_tier = "copper"
	check(StatRules.holds_path(c, "body_ladder"), "Copper Body holds the body ladder")
	cu.techniques_known.erase("venom_needles")
	check(not StatRules.holds_path(c, "poison") or ProgressionRules.knows_poison_art(c), "no poison path without a poison art")
	cu.techniques_known.append("venom_needles")
	check(StatRules.holds_path(c, "poison"), "a poison art known holds the Poison path")
	cu.vows.clear()
	cu.daos["music"] = {"tier": 2, "insight": 0.0}
	check(not StatRules.holds_path(c, "buddhist"), "no vow and Music Dao 2: not on the Buddhist path")
	cu.daos["music"] = {"tier": 3, "insight": 0.0}
	check(StatRules.holds_path(c, "buddhist"), "Music Dao 3 stands in for a vow")
	cu.daos["formation"] = {"tier": 3, "insight": 0.0}
	cu.paths.erase("confucian")
	cu.realm_key = "will_manifest_1"
	check(StatRules.holds_path(c, "confucian"), "before Will Manifest 2, Formation Dao 3 stands in for the Confucian path")
	cu.realm_key = "will_manifest_2"
	check(not StatRules.holds_path(c, "confucian"), "from Will Manifest 2 only walking the path counts")
	cu.paths["confucian"] = true
	check(StatRules.holds_path(c, "confucian"), "walking the Confucian path holds it")
	cu.realm_key = realm_before
	cu.paths = paths_before.duplicate()
	for d in ["sword", "music", "formation"]:
		if daos_before.has(d): cu.daos[d] = daos_before[d].duplicate()
		else: cu.daos.erase(d)
	cu.body_tier = "mortal"
	# A test set of each line: two weapon variants and five more pieces; six can be worn at once.
	var set_id := "_line_test"
	var ids := {"weapon": ["_lt_jian", "_lt_fan"], "hat": ["_lt_hat"], "robe": ["_lt_robe"], "trousers": ["_lt_trousers"], "boots": ["_lt_boots"], "talisman": ["_lt_charm"]}
	var pieces: Array = []
	for slot in ids:
		for id in ids[slot]:
			ContentDB.tables["artifacts"][id] = {"id": id, "name": id, "type": "equipment", "slot": slot, "grade": "heaven", "ilv": 45, "set": set_id,
				"family": "jian" if id == "_lt_jian" else ("fan" if id == "_lt_fan" else ""), "energy_type": "true_qi"}
			pieces.append(id)
	var uid := [800000]
	var wear := func(list: Array) -> void:
		for slot in ids: c.inventory.equipped[slot] = null
		for id in list:
			uid[0] += 1
			c.inventory.equipped[str(ContentDB.item(id).slot)] = LootRules.make_instance(id, 45, "common", null, uid[0])
		Game.combat.refresh_stats(c.id)
	var six := ["_lt_jian", "_lt_hat", "_lt_robe", "_lt_trousers", "_lt_boots", "_lt_charm"]
	var lines: Dictionary = ContentDB.config("gear").get("lines", {})
	var archetypes: Dictionary = ContentDB.config("gear").get("archetypes", {})
	var flags_seen := []
	for line in lines:
		var ln: Dictionary = lines[line]
		var flag_row: Dictionary = {}
		for k in ln.flag:
			if k != "tiers": flag_row[k] = ln.flag[k]
		for k in ln.flag.tiers: flag_row[k] = ln.flag.tiers[k][0]
		ContentDB.tables["sets"][set_id] = {"id": set_id, "pieces": pieces, "archetype": line, "tier": 1, "path": str(archetypes[line].path),
			"bonuses": {"2": ln["2"], "4": ln["4"], "6": (ln["6"] as Array) + [flag_row]}}
		var two: Dictionary = ln["2"][0]
		wear.call(["_lt_fan", "_lt_hat"])
		var mods := StatRules.set_modifiers(c)
		var held := StatRules.holds_path(c, str(archetypes[line].path))
		check(StatRules.set_counts(c).get(set_id, 0) == 2 and near(total.call(mods, str(two.stat), ":2"), float(two.value) * (2.0 if held else 1.0), 0.0001)
			and total.call(mods, str(ln["4"][0].stat), ":4") == 0.0, "%s line: two pieces (a weapon variant among them) give the 2-piece bonus" % line)
		wear.call(six.slice(0, 5))
		check(StatRules.set_flag(c, str(ln.flag.flag)).is_empty() and near(total.call(StatRules.set_modifiers(c), str(ln["4"][0].stat), ":4"), float(ln["4"][0].value), 0.0001),
			"%s line: five pieces give the 4-piece bonus and no mechanic" % line)
		wear.call(six)
		var fl := StatRules.set_flag(c, str(ln.flag.flag))
		check(StatRules.set_counts(c).get(set_id, 0) == 6 and not fl.is_empty() and fl.keys().all(func(k): return flag_row[k] == fl[k]),
			"%s line: six pieces give %s at tier I's values (%s)" % [line, ln.flag.flag, str(fl)])
		flags_seen.append(str(ln.flag.flag))
	check(flags_seen.size() == 6, "six lines, six mechanics (%s)" % str(flags_seen))
	# The path doubling, on the body line: Copper Body doubles the 2-piece's +5% HP.
	var body_ln: Dictionary = lines.body
	ContentDB.tables["sets"][set_id] = {"id": set_id, "pieces": pieces, "archetype": "body", "tier": 1, "path": "body_ladder",
		"bonuses": {"2": body_ln["2"], "6": [{"flag": "unbroken", "below": 0.3, "shield_s": 5, "cooldown_s": 60, "shield": 0.10}]}}
	wear.call(["_lt_jian", "_lt_hat"])
	var hp_off: float = total.call(StatRules.set_modifiers(c), "max_hp", ":2")
	cu.body_tier = "copper"
	check(near(total.call(StatRules.set_modifiers(c), "max_hp", ":2"), hp_off * 2.0, 0.0001) and near(hp_off, 0.05, 0.0001), "Copper Body: the body set's 2-piece counts double (+10% HP)")
	cu.body_tier = "mortal"
	# Unbroken: a blow that would take you below 30% HP raises a 10% shield first; once a minute.
	wear.call(six)
	c.pools.shield = 0.0
	c.pools.cooldowns.erase("unbroken")
	c.pools.hp = c.pools.max_hp * 0.35
	Game.combat._damage_player(c, c.pools.max_hp * 0.08, "test", "physical", {})
	check(near(c.pools.hp, c.pools.max_hp * 0.35, 0.01) and c.pools.shield > 0.0 and c.pools.cooldown("unbroken") > 59.0,
		"Unbroken: the blow that would break 30%% lands on a shield of 10%% (hp %.2f)" % (c.pools.hp / c.pools.max_hp))
	c.pools.shield = 0.0
	Game.combat._damage_player(c, c.pools.max_hp * 0.08, "test", "physical", {})
	check(c.pools.hp < c.pools.max_hp * 0.3 and c.pools.shield == 0.0, "only once a minute")
	c.pools.hp = c.pools.max_hp
	c.pools.cooldowns.erase("unbroken")
	# Honed Intent: two more stacks of Sword Intent, fading half as fast.
	ContentDB.tables["sets"][set_id].bonuses = {"6": [{"flag": "honed_intent", "fade_mult": 2.0, "stacks": 2}]}
	wear.call(six)
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), 5)
	Game.combat.sword_intent.erase(c.id)
	var most := int(ProgressionRules.path_flag(c, "sword_intent_max", ContentDB.stat_const("sword_intent.max", 10))) + 2
	for i in most + 3: Game.combat._feed_intent(c, foe, {"source": "basic"})
	check(int(Game.combat.sword_intent[c.id].stacks) == most and near(float(Game.combat.sword_intent[c.id].t), 2.0 * float(ContentDB.stat_const("sword_intent.fade_s", 3.0)), 0.001),
		"Honed Intent: Sword Intent builds two stacks higher (%d) and holds twice as long" % most)
	Game.combat.sword_intent.erase(c.id)
	# Venom Hand: the Poison Body opens at 35% of tolerance; oils take on more hits.
	ContentDB.tables["sets"][set_id].bonuses = {"6": [{"flag": "venom_hand", "threshold": 0.35, "oil_chance": 1.0}]}
	var tol: float = c.stats.value("toxicity_tolerance")
	cu.toxicity = tol * 0.4
	wear.call([])
	check(not Game.combat.poison_body_active(c), "at 40% of tolerance the Poison Body is closed")
	wear.call(six)
	check(near(Game.combat.poison_body_threshold(c), 0.35, 0.001) and Game.combat.poison_body_active(c), "Venom Hand: it opens at 35%")
	Game.combat.apply_status(c.id, "viper_oil", 60.0, 1.0)
	var oiled := 0
	for i in 12:
		foe.pools.statuses.clear()
		Game.combat._oil_strike(c, foe, Game.combat.enemy_view(foe))
		if foe.pools.has_status("poison"): oiled += 1
	check(oiled == 12, "Venom Hand's oil takes on the hits its row names (%d of 12 at 100%%)" % oiled)
	Game.combat.cure_status(c.id, "viper_oil")
	cu.toxicity = tox_before
	# Kin-Bond: your animal takes 15% less.
	ContentDB.tables["sets"][set_id].bonuses = {"6": [{"flag": "kin_bond", "taken": 0.85, "per_band": 0.01}]}
	var pets_before: Array = c.pets.duplicate()
	Game.pets.apply_grant(c.id, "reed_otter")
	var otter: Dictionary = c.pets.back()
	var mate: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-60, 0), 5)
	mate.team = "ally"
	mate.pet_owner = c.id
	mate.ai["pet"] = str(otter.uid)
	wear.call([])
	var taken0 := Game.pets.damage_taken_mult(mate)
	wear.call(six)
	check(near(Game.pets.damage_taken_mult(mate), taken0 * 0.85, 0.001), "Kin-Bond: the animal takes 15%% less (%.3f -> %.3f)" % [taken0, Game.pets.damage_taken_mult(mate)])
	# Pet damage (a stat): the animal's strike grows with it.
	wear.call([])
	var pw0 := Game.pets.pet_power(c, otter)
	var trait_pd := Game.pets._trait_sum(otter, "pet_damage")
	c.set_meta("extra_modifiers", [{"stat": "pet_damage", "op": "flat", "value": 0.5, "source": "gear:test"}])
	Game.combat.refresh_stats(c.id)
	check(near(Game.pets.pet_power(c, otter), pw0 * (1.5 + trait_pd) / (1.0 + trait_pd), 0.001), "pet damage +50%% strengthens the animal's strike (%.1f -> %.1f)" % [pw0, Game.pets.pet_power(c, otter)])
	c.remove_meta("extra_modifiers")
	mate.alive = false
	c.pets = pets_before
	# Array power (a stat) and Living Array: longer, harder plates; wider rings; the brush's talisman on each foe once.
	Game.combat.arrays.clear()
	cu.daos["formation"] = {"tier": 0, "insight": 0.0}
	Game.combat.deploy_array(c.id, {"array": "killing", "radius": 160, "duration": 10, "mult": 0.5})
	var base_a: Dictionary = Game.combat.arrays.back()
	c.set_meta("extra_modifiers", [{"stat": "array_power", "op": "flat", "value": 0.2, "source": "gear:test"}])
	ContentDB.tables["sets"][set_id].bonuses = {"6": [{"flag": "living_array", "wider": 0.15,
		"talismans": {"killing": {"id": "sundered", "power": 1, "duration_s": 4.0}, "binding": {"id": "root", "power": 1, "duration_s": 1.0}}}]}
	wear.call(six)
	Game.combat.deploy_array(c.id, {"array": "killing", "radius": 160, "duration": 10, "mult": 0.5})
	var a: Dictionary = Game.combat.arrays.back()
	check(near(float(a.t), float(base_a.t) * 1.2, 0.001) and near(float(a.mult), float(base_a.mult) * 1.2, 0.001),
		"array power +20%: the plate lasts and strikes a fifth more")
	check(near(float(a.radius), 160.0 * 1.15, 0.01), "Living Array: its ring is 15% wider")
	var inside: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(170, 0), 5)
	inside.pools.max_hp = 999999.0
	inside.pools.hp = 999999.0
	for i in 3:
		Game.tick(0.05)
		inside.plane = st.plane + Vector2(170, 0)
	check(inside.pools.has_status("sundered") and a.marked.has(inside.uid), "a foe inside the killing array's ring is Sundered")
	inside.pools.statuses.clear()
	for i in 3:
		Game.tick(0.05)
		inside.plane = st.plane + Vector2(170, 0)
	check(not inside.pools.has_status("sundered"), "once each")
	inside.alive = false
	Game.combat.arrays.clear()
	c.remove_meta("extra_modifiers")
	# Melody power (a stat) and Sustained Note: the melody's slow and heals grow; its first seconds cost no Composure.
	ContentDB.tables["sets"][set_id].bonuses = {"6": [{"flag": "sustained_note", "free_s": 3.0, "ally_heal": 0.01}]}
	ContentDB.tables["artifacts"]["_lt_jian"].family = "flute"
	wear.call(six)
	_idle_hands(c)
	c.pools.composure = 100.0
	check(Game.submit({"type": "channel_melody", "on": true}).get("ok", false), "the flute of the test set plays")
	for i in 50: Game.tick(0.05)
	check(near(c.pools.composure, 100.0, 0.01) or c.pools.composure >= 99.9, "Sustained Note: the first 3 s cost no Composure (%.1f)" % c.pools.composure)
	for i in 30: Game.tick(0.05)
	check(c.pools.composure < 99.0, "then the melody drains Composure (%.1f)" % c.pools.composure)
	Game.submit({"type": "channel_melody", "on": false})
	var slow_foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(100, 0), 5)
	c.set_meta("extra_modifiers", [{"stat": "melody_power", "op": "flat", "value": 0.5, "source": "gear:test"}])
	Game.combat.refresh_stats(c.id)
	c.pools.composure = 100.0
	Game.submit({"type": "channel_melody", "on": true})
	for i in 12:
		Game.tick(0.05)
		slow_foe.plane = st.plane + Vector2(100, 0)
	var slowed: Array = slow_foe.pools.statuses.filter(func(s): return str(s.id) == "slow")
	check(not slowed.is_empty() and near(float(slowed[0].power), 0.45, 0.001), "melody power +50%%: the melody slows by 45%%, not 30%% (%s)" % str(slowed))
	Game.submit({"type": "channel_melody", "on": false})
	slow_foe.alive = false
	var ally: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-60, 0), 5)
	ally.team = "ally"
	ally.pools.hp = ally.pools.max_hp * 0.2
	var chm := ContentDB.entry("techniques", "clear_heart_melody")
	Game.combat._resolve_technique(c, chm)
	var hot: Array = Game.combat.ally_hots.get(ally.uid, [])
	check(not hot.is_empty() and near(float(hot.back().per_s), ally.pools.max_hp * float(chm.allies_heal_pct) * 1.5, 0.01),
		"melody power +50%: Clear Heart Melody heals half again")
	ally.alive = false
	Game.combat.ally_hots.erase(ally.uid)
	# The bell's ring carries further with melody power.
	ContentDB.tables["artifacts"]["_lt_jian"].family = "bell"
	wear.call(six)
	var ringer: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-200, 0), 5)
	ringer.pools.max_hp = 999999.0
	ringer.stats["evasion"] = 0.0
	var ring := func() -> float:
		ringer.pools.hp = 999999.0
		_idle_hands(c)
		Game.combat.basic_attack(c, 1)
		for i in 14:
			Game.tick(0.05)
			ringer.plane = st.plane + Vector2(-200, 0)
		return 999999.0 - ringer.pools.hp
	var reached: float = ring.call()
	c.remove_meta("extra_modifiers")
	Game.combat.refresh_stats(c.id)
	check(reached > 0.0 and ring.call() == 0.0, "melody power +50%: the bell's ring reaches a foe 200 behind; without it, not (reach 160)")
	ringer.alive = false
	# Put everything back.
	ContentDB.tables["sets"].erase(set_id)
	for id in pieces: ContentDB.tables["artifacts"].erase(id)
	c.inventory.equipped = equipped_before
	cu.daos = daos_before
	cu.body_tier = body_before
	cu.techniques_known = known_before
	cu.vows = vows_before
	foe.alive = false
	Game.combat.refresh_stats(c.id)

func legacy_suite() -> void:
	var entry: Dictionary = ContentDB.entry("unlocks", "account_legacy")
	check(str(entry.get("scope", "")) == "account", "the Account Legacy is an account-wide unlock")
	var c = Game.active()
	if c == null: return
	var acc: AccountState = Game.account
	var legacy_was: Dictionary = acc.legacy.duplicate()
	var top_was: String = acc.highest_realm
	var bonus_before: float = Game.progression.accumulation_bonus(c)
	acc.legacy.clear()
	acc.highest_realm = "heart_tempering_2"
	Game.accounts._backfill_legacy(c.id)
	GameEvents.flush()
	check(acc.legacy.has("qi_kindling") and acc.legacy.has("qi_unfurling") and acc.legacy.has("heart_tempering"),
		"the backfill records every great realm the account reached (%s)" % str(acc.legacy.keys()))
	check(not acc.legacy.has("bone_forging") and not acc.legacy.has("cloud_stride"), "but not Bone Forging, and nothing above the highest")
	var n := acc.legacy.size()
	Game.accounts._backfill_legacy(c.id)
	check(acc.legacy.size() == n, "a second backfill records nothing new")
	var bonus_three: float = Game.progression.accumulation_bonus(c)
	acc.legacy.clear()
	check(near(bonus_three - Game.progression.accumulation_bonus(c), 0.06), "three records add 6% to accumulation")
	# The old scrolls' names open with the realms the account has reached, and no further.
	var codex_was: Dictionary = acc.codex.duplicate()
	for k in acc.codex.keys(): if str(k).begins_with("old_scrolls"): acc.codex.erase(k)
	Game.accounts._grant_old_scrolls()
	GameEvents.flush()
	check(acc.codex.has("old_scrolls") and acc.codex.has("old_scrolls_mortal") and acc.codex.has("old_scrolls_heart_tempering"),
		"the old scrolls' entries open up to the account's highest realm")
	check(not acc.codex.has("old_scrolls_cloud_stride") and not acc.codex.has("old_scrolls_world_genesis"), "and later realms stay hidden")
	acc.codex = codex_was
	acc.legacy = legacy_was
	acc.highest_realm = top_was
	check(near(Game.progression.accumulation_bonus(c), bonus_before), "state restored")

func emotes_suite() -> void:
	var starting := ContentDB.all("emotes").filter(func(e): return str(e.get("achievement", "")) == "")
	check(starting.size() >= 6, "six emotes from the start (%d)" % starting.size())
	check(Game.submit({"type": "emote", "emote": "bow"}).get("ok", false), "a starting emote plays")
	var done: Dictionary = Game.account.achievements.done
	var had := done.has("valley_champion")
	done.erase("valley_champion")
	check(str(Game.submit({"type": "emote", "emote": "champion"}).get("reason", "")) == "locked", "an achievement emote waits for its achievement")
	done["valley_champion"] = true
	check(Game.submit({"type": "emote", "emote": "champion"}).get("ok", false), "and plays once it is earned")
	if not had: done.erase("valley_champion")

# ------------------------------------------------------------------ saves (Part 7 · Save migration)
func save_suite() -> void:
	var folder := "user://save_suite/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	var repo := RepositoryLocal.new(folder)
	check(repo.save_character(1, {"version": 3, "name": "First"}) == OK, "a character saves")
	check(repo.save_character(1, {"version": 3, "name": "Second"}) == OK, "saving again keeps the previous file as .bak")
	var f := FileAccess.open(repo.character_path(1), FileAccess.WRITE)
	f.store_string("{ this is not json")
	f.close()
	var back: Dictionary = repo.load_character(1)
	check(str(back.get("name", "")) == "First" and repo.last_recovered.has("char_1.json"), "a damaged save is restored from its .bak")
	# S40: a manual export carries the account and characters; importing it restores them.
	repo.save_account({"version": 3, "account_id": "export-test", "characters": {"1": {}}})
	var saved_repo = Saves.repo
	Saves.repo = repo
	var path := Saves.export_bundle([1])
	check(path != "" and FileAccess.file_exists(path), "a save exports to one file (%s)" % path)
	repo.save_account({"version": 3, "account_id": "changed", "characters": {}})
	check(Saves.import_bundle(path) == OK and str(repo.load_account().get("account_id", "")) == "export-test", "importing the export restores the account")
	check(str(repo.load_character(1).get("name", "")) != "", "and its characters")
	check(Saves.import_bundle("user://no_such_file.json") != OK, "a missing or foreign file is refused")
	check(Saves.list_exports().any(func(e): return str(e.path) == path), "exports are listed for restoring")
	DirAccess.remove_absolute(path)
	Saves.repo = saved_repo
	var old: Dictionary = Saves.migrate_character({"name": "Old", "version": 2})
	check(int(old.get("version", 0)) == Saves.VERSION, "an older character file is brought to the current version")

# ------------------------------------------------------------------ regression tests for the code review (docs/review-code.md)
## A fresh account in its own folder, one character standing in its first room (the suites after this one boot their own).
func _fix_world(folder := "user://fixes_suite/") -> Object:
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	Game.account.slots_unlocked = 2
	Game.submit({"type": "create_character", "slot": 1, "name": "Fixes"})
	Game.submit({"type": "enter_character", "slot": 1})
	var c = Game.active()
	Game.submit({"type": "enter_world"})
	var st := ActorState.new()
	Game.bind_movement(c.id, st)
	st.surface = Game.room_rt.geometry.surfaces[0]
	st.plane = Vector2(float(c.position.x), float(c.position.y))
	for sid in ["spawn_protection"]: Game.combat.cure_status(c.id, sid)
	return c

func fixes_suite() -> void:
	var utc0 := Clock.override_utc
	var tz0 := Clock.override_tz_offset_s
	Clock.override_utc = 1767225600.0
	var c = _fix_world()
	if c == null:
		check(false, "the fixes suite needs a character")
		return
	_fix_ticks(c)
	_fix_buyback(c)
	_fix_uids(c)
	_fix_full_bag(c)
	_fix_commissions(c)
	_fix_wind_step(c)
	_fix_strongest_dao(c)
	_fix_fall(c)
	_fix_page_writes(c)
	Clock.override_utc = utc0
	Clock.override_tz_offset_s = tz0
	HerbRules.origin_week = 0

## B1: the Relations and Calendar authorities run with the game clock.
func _fix_ticks(c) -> void:
	var meter := Game.relations.fortune_meter(c)
	for i in 20: Game.tick(0.25)
	check(Game.relations.fortune_meter(c) > meter, "playing fills the Fortune meter (Game.tick runs Relations)")
	check(Game.account.calendar.has("season"), "the calendar keeps the season as the game runs (Game.tick runs the Calendar)")
	check(HerbRules.origin_week == Clock.reset_week(Game.account.created_utc), "and counts the seasons from the account's first week")

## B2: buyback gives back the stack that was sold, and only charges for what fits.
func _fix_buyback(c) -> void:
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	Game.economy.apply_currency("silver_tael", 100000, "test")
	Game.inventory.apply_add(c.id, "healing_pill", 3, "test", {"quality": "superior", "marks": 2})
	check(Game.economy.sell(c, _bag_index(c, "healing_pill"), 3).get("ok", false), "three Superior pills sell")
	check(Game.economy.buyback(c, 0).get("ok", false), "and are bought back")
	var i := _bag_index(c, "healing_pill")
	check(i >= 0 and str(c.inventory.bag[i].get("quality", "")) == "superior" and int(c.inventory.bag[i].get("marks", 0)) == 2
		and int(c.inventory.bag[i].count) == 3, "a bought-back stack keeps its quality and marks (%s)" % str(c.inventory.bag[i] if i >= 0 else {}))
	# Room for one of three: one comes back, two stay on the list, and one is paid for.
	var stack := int(ContentDB.item("healing_pill").get("stack", 99))
	c.inventory.bag[i] = {"id": "healing_pill", "count": stack - 1, "quality": "superior", "marks": 2}
	for j in c.inventory.bag.size():
		if c.inventory.bag[j] == null: c.inventory.bag[j] = {"id": "healing_pill", "count": stack, "quality": "flawed"}
	Game.account.economy.buyback = [{"entry": {"id": "healing_pill", "count": 3, "quality": "superior", "marks": 2}, "price": 300, "day": 0}]
	var silver := Game.economy.balance("silver_tael")
	check(Game.economy.buyback(c, 0).get("ok", false), "a buyback with room for one of three goes through")
	var left: Array = Game.account.economy.buyback
	check(int(c.inventory.bag[i].count) == stack and silver - Game.economy.balance("silver_tael") == 100 and left.size() == 1
		and int(left[0].entry.count) == 2 and int(left[0].price) == 200, "one comes back for a third of the price; two wait on the list (%s)" % str(left))
	for j in c.inventory.bag.size(): c.inventory.bag[j] = null
	Game.account.economy.buyback = []

## B3: every instance in a bag has its own uid (a withdrawal from the shared chest, a split of a locked stack).
func _uids_unique(ch) -> bool:
	var seen := {}
	for inst in ch.inventory.bag + ch.inventory.equipped.values() + [ch.inventory.furnace]:
		if not (inst is Dictionary) or not inst.has("uid"): continue
		if seen.has(int(inst.uid)): return false
		seen[int(inst.uid)] = true
	return true

func _fix_uids(c) -> void:
	Unlocks.force_unlock(c.id, "storage")
	Game.submit({"type": "create_character", "slot": 2, "name": "Second"})
	var c2 = Game.character("c2")
	check(c2 != null, "a second character for the shared chest")
	if c2 == null: return
	Game.inventory.apply_add_equipment(c.id, "training_jian", 1, "common", "test")
	var n_store: int = Game.account.storage.get("items", []).size()
	check(Game.accounts.deposit(c, _bag_index(c, "training_jian"), 1).get("ok", false), "the first character stores a jian")
	Game.inventory.apply_add_equipment(c2.id, "hemp_robe", 1, "common", "test")
	var robe: Dictionary = c2.inventory.bag[_bag_index(c2, "hemp_robe")]
	c2.inventory.locked[int(robe.uid)] = true
	check(Game.accounts.withdraw(c2, n_store).get("ok", false), "the second character takes it out")
	var jian: Dictionary = c2.inventory.bag[_bag_index(c2, "training_jian")]
	check(_uids_unique(c2) and not c2.inventory.locked.has(int(jian.uid)), "the jian gets a uid of its own in the new bag (%d, robe %d)" % [int(jian.uid), int(robe.uid)])
	var fresh := LootRules.make_instance("training_spear", 1, "common", null, c2.inventory.next_uid)
	Game.inventory.apply_add_instance(c2.id, fresh, "test")
	check(_uids_unique(c2), "and the next piece minted there does not collide with it")
	# A split of a locked stack is a new, unlocked stack.
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	Game.inventory.apply_add(c.id, "healing_pill", 10, "test")
	Game.submit({"type": "lock_item", "index": 0})
	check(Game.submit({"type": "split_stack", "index": 0, "count": 4}).get("ok", false), "a locked stack splits")
	var part = c.inventory.bag[1]
	check(part != null and not part.has("uid") and _uids_unique(c), "the new part carries no copy of the lock's uid (%s)" % str(part))
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null

## B4: standing by loot with a full bag says so once, not every tick.
func _fix_full_bag(c) -> void:
	var st: ActorState = Game.actor_state(c.id)
	var rt: RoomRuntime = Game.room_rt
	for i in c.inventory.bag.size(): c.inventory.bag[i] = {"id": "healing_pill", "count": 99, "quality": "flawed"}
	rt.loot.append({"uid": rt.uid(), "item": "rice_ball", "count": 1, "coins": 0, "instance": {}, "x": st.plane.x, "y": st.plane.y, "alt": st.altitude,
		"ttl": 60.0, "age": 1.0, "quality": "common"})
	var seen := [0]
	var count_full := func(name: String, _p: Dictionary) -> void:
		if name == "bag_full": seen[0] += 1
	GameEvents.event.connect(count_full)
	for i in 30: Game.tick(0.05)
	GameEvents.event.disconnect(count_full)
	check(seen[0] == 1, "a full bag beside loot is announced once, not every tick (%d)" % seen[0])
	c.inventory.bag[0] = null
	for i in 3: Game.tick(0.05)
	check(c.inventory.count("rice_ball") == 1, "and the loot is picked up as soon as there is room")
	rt.loot.clear()
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null

## B5 and B6: a guild order never takes a locked piece, and the board turns over with the daily reset.
func _fix_commissions(c) -> void:
	c.crafting["guild"] = {"smithing": "adept"}
	var day := CraftingAuthority.commission_day()
	c.crafting["commission_state_smithing"] = {"day": day, "paid": 0, "orders": [{"id": "smithing_t_0", "item": "hemp_robe", "count": 1, "quality": "common",
		"pay": 50, "accepted": true, "done": false}]}
	Game.inventory.apply_add_equipment(c.id, "hemp_robe", 1, "common", "test")
	var i := _bag_index(c, "hemp_robe")
	c.inventory.locked[int(c.inventory.bag[i].uid)] = true
	var r := Game.crafting.deliver_commission(c, "smithing_t_0", "taels")
	check(not r.get("ok", false) and c.inventory.count("hemp_robe") == 1, "a locked piece is never handed to a guild order (%s)" % str(r))
	for j in c.inventory.bag.size(): c.inventory.bag[j] = null
	Clock.override_tz_offset_s = -8 * 3600
	var noon := 1767225600.0 + 20.0 * 3600.0   # 20:00 UTC is 12:00 at UTC-8
	Clock.override_utc = noon
	var a := CraftingAuthority.commission_day()
	Clock.override_utc = noon + 5.0 * 3600.0     # 01:00 UTC the next day is 17:00 the same local day
	check(CraftingAuthority.commission_day() == a, "the guild boards turn over with the daily reset, not at midnight UTC")
	Clock.override_utc = 1767225600.0
	Clock.override_tz_offset_s = -99999

## B7: a Wind Step charge is spent only by a dodge that happens.
func _fix_wind_step(c) -> void:
	var st: ActorState = Game.actor_state(c.id)
	Unlocks.force_unlock(c.id, "dodge_dash")
	c.pools.cooldowns["dodge"] = 5.0
	Game.combat.treasure_fx[c.id] = {"free_dodge": 1.0}
	var geo: ZoneGeometry = Game.room_rt.geometry
	geo.volumes.append({"id": "test_shallows", "kind": "water_shallow", "rect": Rect2(st.plane - Vector2(50, 50), Vector2(100, 100)), "lo": -20.0, "hi": 20.0})
	var r := Game.submit({"type": "dodge", "direction": Vector2(1, 0), "facing": 1})
	check(str(r.get("reason", "")) == "in_water" and float(Game.combat.treasure_fx[c.id].get("free_dodge", 0.0)) > 0.0,
		"a dodge refused in shallow water keeps the Wind Step charge (%s)" % str(r))
	geo.volumes.pop_back()
	check(Game.submit({"type": "dodge", "direction": Vector2(1, 0), "facing": 1}).get("ok", false) and not Game.combat.treasure_fx[c.id].has("free_dodge"),
		"on dry ground the charge is spent on the dodge")
	c.pools.cooldowns.clear()
	Game.combat.treasure_fx.erase(c.id)
	Game.combat.timeline(c.id).forced_t = 0.0

## B9: one answer to "the Dao you know best": the highest tier first, then the most insight.
func _fix_strongest_dao(c) -> void:
	Unlocks.force_unlock(c.id, "dao_tree")
	c.cultivator.daos = {"sword": {"tier": 6, "insight": 12500.0}, "fist": {"tier": 5, "insight": 30000.0}}
	check(str(Game.field.sphere_of(c).get("dao", "")) == "sword", "the Sphere is drawn from the tier-6 Dao")
	Game.progression.apply_insight_best(c.id, 10.0, "chess")
	check(float(c.cultivator.daos.sword.insight) > 12500.0 and near(float(c.cultivator.daos.fist.insight), 30000.0),
		"and the chess problem teaches the same Dao (%s)" % str(c.cultivator.daos))
	c.cultivator.daos = {}

## The fall's cost is Combat's answer to fell_out (the world scene no longer writes HP): 5% of max HP on the road,
## nothing in the Prologue's village.
func _fix_fall(c) -> void:
	c.pools.hp = c.pools.max_hp
	GameEvents.emit_event("fell_out", {"actor": c.id, "recovered_to": {}})
	GameEvents.flush()
	check(near(c.pools.hp, c.pools.max_hp), "a fall in the Prologue's village costs nothing")
	Game.world.apply_teleport(c.id, "wp_west")
	GameEvents.flush()
	c.pools.hp = c.pools.max_hp
	GameEvents.emit_event("fell_out", {"actor": c.id, "recovered_to": {}})
	GameEvents.flush()
	check(near(c.pools.hp, c.pools.max_hp * (1.0 - float(ContentDB.stat_const("move.fall_cost_pct", 0.05)))),
		"a fall on the Willow Path costs 5%% of max HP (%.1f of %.1f)" % [c.pools.hp, c.pools.max_hp])
	c.pools.hp = c.pools.max_hp

## B19: what the Bag, Works, Roll-Call's Bench and Spirit Animals pages wrote themselves, their authorities now write
## behind intents (and contract_tests checks the pages write nothing).
func _fix_page_writes(c) -> void:
	Game.inventory.apply_add(c.id, "spirit_stone_shard", 1, "test")
	check(c.inventory.new_items.has("spirit_stone_shard"), "a piece just picked up is new in the Bag")
	check(Game.submit({"type": "mark_item_seen", "item": "spirit_stone_shard"}).get("ok", false) and not c.inventory.new_items.has("spirit_stone_shard"),
		"looking at it takes the dot away (mark_item_seen)")
	var now := Clock.now_utc()
	var posts: Dictionary = ContentDB.config("posts")
	Unlocks.force_unlock(c.id, "apprentice_bench")
	var b: Dictionary = Game.posts.bench(c)
	var part := str(posts.bench.components[0].item)
	b.slots = [part]
	b.updated = now - 3600.0
	check(Game.submit({"type": "settle_works", "part": "bench"}).get("ok", false) and near(float(b.updated), now) and float(b.stock.get(part, 0.0)) > 0.0,
		"the Apprentice Bench settles an hour's work when its page asks")
	var sd: Dictionary = posts.salts[0]
	var ln: Dictionary = Game.posts.salt_line(str(sd.id))
	ln.on = true
	ln.since = now - 7200.0
	check(Game.submit({"type": "settle_works", "part": "furnace"}).get("ok", false) and float(ln.since) > now - float(sd.get("cycle_s", 900)),
		"the Calcination Furnace catches up when its page asks")
	var m: Dictionary = Game.posts.works().mirror
	m.since = now - 3600.0
	check(Game.submit({"type": "settle_works", "part": "mirror"}).get("ok", false) and near(float(m.since), now), "so does the Mirror of Echoes")
	check(not Game.submit({"type": "settle_works", "part": "garden"}).get("ok", true), "an unknown work is refused")
	var legacy := {"uid": "old_2", "species": "reed_otter", "rarity": "rare"}
	check(int(Game.pets.filled(legacy).get("purity", 0)) == 38 and not legacy.has("purity"),
		"Spirit Animals reads an older animal with its neutral fields and does not write them")

# ------------------------------------------------------------------ fixes found by the P3 mockups
## Open items the mockup agents found while drawing (docs/mockups/README.md), each at its rule.
func mockup_fixes_suite() -> void:
	var c = _fix_world("user://mockup_fixes/")
	if c == null:
		check(false, "the mockup fixes suite needs a character")
		return
	_mock_sect_materials(c)
	_mock_treasury(c)
	_mock_stat_formats(c)
	_mock_locked_text(c)
	_mock_stances(c)

## Every weapon family has a stance a character holds without buying anything (the jian's only stance was Willow Leaf
## Parry, a technique bought at the library); Willow Leaf Parry stays the better jian stance.
func _mock_stances(c) -> void:
	Unlocks.force_unlock(c.id, "stances")
	var known_was: Array = c.cultivator.techniques_known.duplicate()
	c.cultivator.techniques_known = []
	var without: Array = []
	for wf in ContentDB.all("weapon_families"):
		var held := false
		for st in ContentDB.all("stances"):
			if str(st.family) == str(wf.id) and not held: held = Game.submit({"type": "set_stance", "family": str(wf.id), "stance": str(st.id)}).get("ok", false)
		if not held: without.append(str(wf.id))
	check(without.is_empty(), "every weapon family has a stance held without buying anything (none for %s)" % str(without))
	var wlp := ContentDB.entry("stances", "willow_leaf_parry")
	var basic := ContentDB.entry("stances", str(c.cultivator.stances.get("jian", "")))
	check(str(basic.get("id", "")) != "willow_leaf_parry" and float(wlp.flags.parry_counter) > float(basic.get("flags", {}).get("parry_counter", 0.0))
		and not ProgressionRules.stance_known(c, wlp), "the jian's basic stance is %s; Willow Leaf Parry, counter for counter the better, needs its technique" % basic.get("name", "none"))
	c.cultivator.stances = {}
	c.cultivator.techniques_known = known_was

## One rule for why a system is locked: every unmet condition, not only the first; a quest that is all that is left,
## with its giver (the Bench at bf8 named only Qi Kindling 1; the hub's Works tile at qu5 named Keeping Post, done).
func _mock_locked_text(c) -> void:
	var cu = c.cultivator
	var realm_was: String = cu.realm_key
	var done_was: Dictionary = c.quests.done.duplicate()
	var quest_line := func(key: String, quest: String, giver: String) -> String:
		return Tx.t(key) % [ContentDB.name_of("quests", quest), ContentDB.name_of("npcs", giver)]
	cu.realm_key = "bone_forging_8"
	c.quests.done.erase("keeping_post")
	var both := Unlocks.locked_text("apprentice_bench")
	check(both == Tx.t("req.reach") % ContentDB.name_of("realms", "qi_kindling_1") + Tx.t("unlock_text.sep") + Tx.t("req.complete") % ContentDB.name_of("quests", "keeping_post"),
		"the Bench at Bone Forging 8 names both of its conditions (%s)" % both)
	cu.realm_key = "qi_kindling_1"
	var one := Unlocks.locked_text("apprentice_bench")
	check(one == quest_line.call("unlock_text.complete_quest", "keeping_post", "fisher_wen"), "at Qi Kindling 1 Keeping Post is all that is left: it and its giver (%s)" % one)
	c.quests.done["keeping_post"] = 1
	var own := Unlocks.locked_text("apprentice_bench")
	check(own == quest_line.call("unlock_text.take_quest", "an_apprentices_hands", "tinkerer_yu"), "every condition met: the Bench's own quest and its giver (%s)" % own)
	# qu5: the hub's Works tile (menu_page gates it on post_arts and shows its locked text) waits on Elder Hu's An Idle Art.
	cu.realm_key = "qi_unfurling_5"
	var menu = load("res://scripts/ui/pages/menu_page.gd").new()
	var gate := ""
	for e in menu.ENTRIES:
		if str(e[0]) == "works": gate = str(e[3])
	menu.free()
	var works := Unlocks.locked_text(gate)
	check(gate == "post_arts" and works == quest_line.call("unlock_text.take_quest", "an_idle_art", "elder_hu"), "the hub's Works at Qi Unfurling 5 (%s)" % works)
	cu.realm_key = realm_was
	c.quests.done = done_was

## A stat's format matches what is shown: a percent stat is a share (a new character's value under 10), and move_speed,
## shown as the speed itself (242), is a number.
func _mock_stat_formats(c) -> void:
	var shares: Array = []
	for s in ContentDB.stat_const("stats", []):
		if str(s.get("format", "")) == "percent" and absf(float(c.stats.value(str(s.id)))) >= 10.0: shares.append("%s %.0f" % [s.id, c.stats.value(str(s.id))])
	check(shares.is_empty(), "every percent stat is a share (%s)" % str(shares))
	check(UiKit.affix_text({"stat": "move_speed", "op": "flat", "value": 20.0}) == "+20 move speed", "+20 move speed reads as a speed, not 2000%")

## The Treasury's output names what it gives: spaces in the storage chest for each level.
func _mock_treasury(c) -> void:
	Unlocks.force_unlock(c.id, "storage")
	Game.account.sect = {"name": "Test", "level": 1, "prestige": 0, "buildings": {"sect_hall": 1, "treasury": 2}, "queue": []}
	var per := int(ContentDB.entry("sect_buildings", "treasury").get("output", {}).get("storage_slots_per_level", 0))
	var base := Game.accounts.storage_size() - Game.sect.treasury_bonus()
	check(per > 0 and Game.accounts.storage_size() == base + 2 * per, "a Treasury at level 2 adds %d storage spaces a level (%d in all)" % [per, Game.accounts.storage_size()])
	Game.account.sect = {}

## A sect build takes its materials from the bag, then the Storehouse, then the storage chest (the Treasury was blocked
## with 49 Copper Ore in storage).
func _mock_sect_materials(c) -> void:
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	Game.account.sect = {"name": "Test", "emblem": [0, 0], "level": 1, "prestige": 0, "buildings": {"sect_hall": 1}, "queue": [], "candidates": [],
		"candidate_day": Clock.reset_day(Clock.now_utc()), "expeditions": [], "disciples": []}
	Game.economy.apply_currency("silver_tael", 100000, "test")
	var need := int(Game.sect.building_cost("treasury", 1).materials.copper_ore)
	Game.inventory.apply_add(c.id, "copper_ore", 3, "test")
	Game.account.storehouse = {"copper_ore": 5}
	Game.account.storage = {"items": [{"id": "copper_ore", "count": need - 9}]}
	check(Game.inventory.count_owned(c, "copper_ore") == need - 1 and str(Game.submit({"type": "upgrade_building", "building": "treasury"}).get("reason", "")) == "materials",
		"one ore short across the bag, the Storehouse and storage: the Treasury waits")
	Game.account.storage.items[0].count = need - 8
	var r := Game.submit({"type": "upgrade_building", "building": "treasury"})
	check(r.get("ok", false) and c.inventory.count("copper_ore") == 0 and Game.account.storehouse.is_empty() and Game.account.storage.items.is_empty(),
		"with %d between them the Treasury is raised, and all three are spent (%s)" % [need, str(r)])
	Game.account.sect = {}
	Game.account.storage = {"items": []}

# ------------------------------------------------------------------ P13a the element trees (docs/technique_plan.md §4)
## Realise and let go, leaves first; the ring, route, path, keystone and rest gates; the free reset once a great realm;
## the heavy-art cap; the tree's passives and their cap; Realisations; taught arts light for free.
func tree_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var snap := cu.snapshot()
	var bag_was: Array = c.inventory.bag.duplicate(true)
	var T = TechniqueTreeRules
	# The shape: a v1.2.x tree holds 96 passages, 180 arts, 36 notables and 12 keystones (with the heart, its six trunk
	# tiers and twelve gates, the plan's 343 nodes).
	var built := T.nodes_of("water").filter(func(n): return T.node(n).act <= 3)
	var kinds := {}
	for n in built: kinds[str(T.node(n).kind)] = int(kinds.get(str(T.node(n).kind), 0)) + 1
	check(built.size() == 324 and int(kinds.get("passage", 0)) == 96 and int(kinds.get("art", 0)) == 180 and int(kinds.get("notable", 0)) == 36
		and int(kinds.get("keystone", 0)) == 12, "the Water tree of v1.2.x: 324 nodes beside its heart, trunk and gates (%s)" % str(kinds))
	check(T.cell("formless", "spear", 1).o.has("jade_thrust") and T.cell("formless", "spear", 1).o.has("dragon_tail_sweep")
		and T.cell("earth", "any", 2).p.has("stone_skin") and T.cell("earth", "any", 2).p.has("golden_body"), "today's arts keep their cells, twins and all (§4.8)")
	check(T.home("sword_release").is_empty() and T.home("rising_tide").is_empty(), "Dao arts and lost arts are off the cells")
	# A clean slate at Heart Tempering 3 (Level 30) with no Daos and one art known.
	cu.realm_key = "heart_tempering_3"
	cu.qp = 0.0
	cu.tree = {"v": 1, "realised": {}, "resets": {}, "pity": {}}
	cu.daos = {}
	cu.techniques_known = ["flowing_palm"]
	cu.mastery = {"flowing_palm": {"tier": 5, "points": 0.0}}
	cu.technique_slots = [null, null, null, null, null, null, null, null]
	cu.technique_bars = {}
	cu.vows = []
	cu.paths = {}
	var lv := ProgressionRules.level(c)
	var r0: Dictionary = T.realisations(c)
	check(int(r0.total) == lv + 2 * ProgressionRules.realm_index(cu.realm_key) + 3 and int(r0.spent) == 0,
		"Realisations: Level %d + 2 x %d majors + Dao tiers 0 + mastery past tier 2 (3) = %d" % [lv, ProgressionRules.realm_index(cu.realm_key), int(r0.total)])
	cu.daos = {"water": {"tier": 2, "insight": 400.0}, "sword": {"tier": 1, "insight": 120.0}}
	check(int(T.realisations(c).total) == int(r0.total) + 3, "every Dao's tiers add to the pool")
	Game.combat.timeline(c.id).fight_t = -999.0
	var p1 := T.passage("water", "any", 1)
	var p2 := T.passage("water", "any", 2)
	var art1: String = T.cell("water", "any", 1).o[0]   # Flowing Palm: taught, so already lit
	var art2 := ""
	for a in T.cell("water", "any", 2).o:
		if not cu.techniques_known.has(a): art2 = str(a)
	check(T.realise_block(c, art1, Game.ctx(c)) == "known", "a taught art cannot be realised: it is lit already")
	check(T.realise_block(c, p2, Game.ctx(c)) == "route", "a node needs the one inside it (ring 2 before ring 1: %s)" % T.realise_block(c, p2, Game.ctx(c)))
	var r := Game.submit({"type": "realise_node", "node": p1})
	check(r.get("ok", false) and cu.tree.realised.has(p1) and int(T.realisations(c).spent) == 1, "a free-hand passage realised from its open gate for 1 (%s)" % str(r))
	check(T.realise_block(c, T.passage("water", "jian", 1), Game.ctx(c)) == "", "the jian's gate opens with its Dao")
	check(T.realise_block(c, T.passage("water", "spear", 1), Game.ctx(c)) == "gate", "an unused weapon's gate is shut")
	check(Game.submit({"type": "realise_node", "node": art2}).get("reason", "") == "route", "an art needs its ring's passage")
	check(Game.submit({"type": "realise_node", "node": p2}).get("ok", false), "the passage of ring 2")
	r = Game.submit({"type": "realise_node", "node": art2})
	check(r.get("ok", false) and cu.techniques_known.has(art2) and int(T.realisations(c).spent) == 4, "an orthodox art realised for 2 is learned (%s)" % str(r))
	# The ring's Level, the act, the path.
	var p3 := T.passage("water", "any", 3)
	check(T.realise_block(c, p3, Game.ctx(c)) == "level", "ring 3 waits for Level 37")
	check(T.realise_block(c, T.passage("water", "any", 9), Game.ctx(c)) == "act_locked", "rings past Act III are locked behind their act")
	var path_art: String = T.cell("water", "any", 2).p[0]
	var want := str(ContentDB.entry("techniques", path_art).get("path", ""))
	check(T.realise_block(c, path_art, Game.ctx(c)) == ("" if T.walks(c, want) else "path"), "a path art needs its path (%s) walked" % want)
	# Leaves first, not while slotted; the refund is whole.
	check(T.unrealise_block(c, p2) == "leaf", "a passage with a realised art beyond it waits")
	Game.progression.equip_technique(c, 0, art2)
	check(Game.submit({"type": "unrealise_node", "node": art2}).get("reason", "") == "slotted", "an art in a slot cannot be let go")
	Game.progression.equip_technique(c, 0, "")
	r = Game.submit({"type": "unrealise_node", "node": art2})
	check(r.get("ok", false) and not cu.techniques_known.has(art2) and cu.mastery.has(art2) and int(T.realisations(c).spent) == 2,
		"letting an art go gives back its 2 and unlearns it; its mastery waits (%s)" % str(r))
	check(Game.submit({"type": "unrealise_node", "node": p2}).get("ok", false) and int(T.realisations(c).spent) == 1, "then its passage")
	# Out of combat only.
	Game.combat.timeline(c.id).fight_t = Game.sim_time
	check(Game.submit({"type": "realise_node", "node": p2}).get("reason", "") == "in_combat", "nothing is realised in a fight")
	Game.combat.timeline(c.id).fight_t = -999.0
	# The notables and the channels between neighbouring sectors (§4.1): at Level 60 a route to ring 4.
	cu.realm_key = "heaven_glimpse_2"
	for ring in range(2, 5): Game.submit({"type": "realise_node", "node": T.passage("water", "any", ring)})
	var nt := T.notable("water", "any", 1)
	check(Game.submit({"type": "realise_node", "node": nt}).get("ok", false), "the act's notable at its last ring (cost %d)" % T.cost(nt))
	var fams := T.sectors()
	var nb := T.notable("water", str(fams[1]), 1)
	check(T.realise_block(c, nb, Game.ctx(c)) == "" or T.realise_block(c, nb, Game.ctx(c)) == "realisations", "a channel joins the neighbouring sector's notable")
	var ks := T.keystone_at("water", "voice", 1)
	check(T.realise_block(c, ks, Game.ctx(c)) == "source", "a keystone waits for its source (%s)" % T.realise_block(c, ks, Game.ctx(c)))
	# Passives: two power passages (rings 1 and 3) and the notable feed the damage bucket of Water free-hand arts, within the
	# Level's cap; the other rings cut their Qi cost.
	var tp: Dictionary = T.passives(c, {"element": "water", "family": "any"})
	check(near(float(tp.damage), minf(0.05, T.tree_cap(ProgressionRules.level(c)))) and near(float(tp.cost), 0.04),
		"passages and a notable: +%d%% damage (cap %d%%), -%d%% Qi" % [int(round(float(tp.damage) * 100)), int(round(T.tree_cap(ProgressionRules.level(c)) * 100)), int(round(float(tp.cost) * 100))])
	check(near(float(T.passives(c, {"element": "fire", "family": "any"}).damage), 0.0) and near(float(T.passives(c, {"element": "water", "family": "jian"}).damage), 0.0),
		"only the tree's own element and sector")
	check(near(T.tree_cap(99), 0.15) and near(T.tree_cap(165), 0.25) and T.tree_cap(50) < 0.15, "the trees add at most +15% by Level 99, +25% by 165")
	# Reset: free once in a great realm, then for a Clear Heart Incense; realised arts leave their slots.
	var spent_before := int(T.realisations(c).spent)
	r = Game.submit({"type": "reset_tree", "tree": "water"})
	check(r.get("ok", false) and bool(r.get("free", false)) and int(r.get("refund", 0)) == spent_before and T.realised(c).is_empty(), "the first reset in a realm is free (%s)" % str(r))
	Game.submit({"type": "realise_node", "node": p1})
	check(Game.submit({"type": "reset_tree", "tree": "water"}).get("reason", "") == "needs_incense", "the second takes a Clear Heart Incense")
	Game.inventory.apply_add(c.id, "clear_heart_incense", 1, "test")
	check(Game.submit({"type": "reset_tree", "tree": "water"}).get("ok", false) and c.inventory.count("clear_heart_incense") == 0, "and burns it")
	# A realised art later taught gives its Realisations back.
	Game.submit({"type": "realise_node", "node": p1})
	Game.submit({"type": "realise_node", "node": p2})
	Game.submit({"type": "realise_node", "node": art2})
	Game.progression.apply_learn_technique(c.id, art2)
	check(not cu.tree.realised.has(art2) and cu.techniques_known.has(art2), "a realised art taught by a teacher is taught now; its node's cost comes back")
	# Heavy arts: one keystone or lost art to a ring of four (§6.3).
	cu.techniques_known.append_array(["rising_tide", "ember_burst", "rain_of_reeds"])
	Unlocks.debug_force_all = true
	check(Game.progression.equip_technique(c, 0, "rising_tide").get("ok", false) and Game.progression.equip_technique(c, 1, "ember_burst").get("reason", "") == "heavy_cap"
		and Game.progression.equip_technique(c, 4, "ember_burst").get("ok", false), "a second heavy art waits for the other ring")
	Unlocks.debug_force_all = false
	# A generated art reads as words from its form, verb and path.
	var gen: Dictionary = ContentDB.entry("techniques", art2)
	var words := T.describe(gen)
	check(words.length() > 20 and not "{" in words and not "technique." in words, "a generated art says what it does: %s" % words)
	cu.restore(snap)
	c.inventory.bag = bag_was
	Game.combat.refresh_stats(c.id)

## P13a Realisations and the save migration (technique_plan §4.3, §4.9): a character like Tester at ls6_end (Sphere Lord
## 3, Level 98) from before the trees keeps every art and its mastery, and the routes to its arts light for 29 of its
## 136 Realisations: 107 left to place. The routes survive a save.
func tree_migration_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var snap := cu.snapshot()
	var T = TechniqueTreeRules
	var old := snap.duplicate(true)
	old.erase("tree")
	old["realm_key"] = "sphere_lord_3"
	old["qp"] = ContentDB.realm("sphere_lord_3").get("accumulate_needed", 100) * 0.4
	old["daos"] = {"sword": {"tier": 5, "insight": 5000.0}, "blood": {"tier": 2, "insight": 300.0}, "fist": {"tier": 2, "insight": 300.0},
		"life_death": {"tier": 1, "insight": 100.0}, "soul": {"tier": 1, "insight": 100.0}, "space": {"tier": 1, "insight": 100.0}}
	var known := ["flowing_palm", "still_water_focus", "crescent_arc", "cloud_descent", "mirror_mind_spike", "soul_lantern_ward", "sense_lock",
		"upright_glyph", "sword_release", "sword_swarm", "glimpse_of_heaven", "splashed_ink", "blood_burning"]
	var mastery := {}
	for tid in known: mastery[tid] = {"tier": 1, "points": 0.0}
	mastery.flowing_palm = {"tier": 5, "points": 40.0}
	mastery.crescent_arc = {"tier": 3, "points": 12.0}
	old["techniques"] = {"known": known.duplicate(), "slots": ["flowing_palm", "crescent_arc", null, null, null, null, null, null], "mastery": mastery.duplicate(true),
		"use": {}, "bars": {}}
	cu.restore(old)
	check(int(cu.tree.get("v", 0)) == 0 and T.realised(c).is_empty(), "a save from before the trees has no tree yet")
	check(ProgressionRules.level(c) == 98, "the character stands at Level 98 (%d)" % ProgressionRules.level(c))
	Game.progression.migrate_tree(c)
	var r: Dictionary = T.realisations(c)
	var passages := T.realised(c).keys().filter(func(n): return str(n).begins_with("p:"))
	check(passages.size() == 29 and T.realised(c).size() == 29, "the routes to its arts light: 29 passages (%d)" % passages.size())
	check(int(r.total) == 136 and int(r.spent) == 29 and int(r.free) == 107, "Realisations 98 + 22 + 12 + 4 = 136: 29 placed, 107 to place (%s)" % str(r))
	check(known.all(func(t): return cu.techniques_known.has(t)) and int(cu.mastery.flowing_palm.tier) == 5 and int(cu.mastery.crescent_arc.tier) == 3
		and cu.technique_slots[0] == "flowing_palm", "every art still known, its mastery and slots unchanged")
	check(T.realised(c).has(T.passage("formless", "brush", 8)) and T.realised(c).has(T.passage("metal", "any", 7)) and not T.realised(c).has(T.passage("formless", "brush", 9)),
		"Splashed Ink's route runs up the brush to ring 8; Upright Glyph's up the free hand to 7")
	Game.progression.migrate_tree(c)
	check(T.realised(c).size() == 29, "the migration runs once")
	# The Dao arts of tiers already reached are taught.
	cu.tree = {}
	cu.tree["realised"] = {}
	cu.daos["water"] = {"tier": 3, "insight": 900.0}
	Game.progression.migrate_tree(c)
	check(cu.techniques_known.has("mirror_of_still_water") and not cu.techniques_known.has("great_river_turns_back"), "the Water Dao's third tier teaches its Dao art")
	# The tree rides in the save.
	var back := CultivatorState.new()
	back.restore(cu.snapshot())
	check(back.tree.realised.size() == T.realised(c).size() and int(back.tree.v) == 1, "the realised nodes survive a save")
	cu.restore(snap)

## P13a Lost Arts (technique_plan §5; roadmap §6 decision 19): the board the page reads counts an unfound art and says
## nothing else of it (no id, name or source); a found art has its full card and still no source. Found by kind, found
## twice for a Manual Page; a stele gives its rubbing once its condition holds; a foe's manual is sure by its pity; Lu's
## journal teaches the Ferryman's Oar by pages.
func lost_arts_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var snap := cu.snapshot()
	var bag_was: Array = c.inventory.bag.duplicate(true)
	var flags_was: Dictionary = c.quests.flags.duplicate(true)
	var T = TechniqueTreeRules
	var rows: Array = ContentDB.all("lost_arts")
	var found_ev: Array = []
	GameEvents.subscribe("lost_art_found", func(p): found_ev.append(p), 200)
	cu.realm_key = "sphere_lord_3"   # Level 98: Acts I-III reached
	for row in rows:
		var kind_list: Array = cu.inner_arts_known if str(row.kind) == "inner" else (cu.secret_arts if str(row.kind) == "secret" else cu.techniques_known)
		kind_list.erase(str(row.id))
	for f in c.quests.flags.keys():
		if str(f).begins_with("journal_") or str(f).begins_with("found_"): c.quests.flags.erase(f)
	# Nothing found: only counts.
	var v: Dictionary = Game.progression.lost_arts_view(c)
	var acts: Array = v.get("acts", [])
	var totals := 0
	for a in acts: totals += int(a.total)
	check(acts.size() == 3 and totals == 60 and acts.all(func(a): return int(a.found) == 0 and (a.arts as Array).is_empty()) and (v.get("lineages", []) as Array).is_empty(),
		"nothing found: the board holds three acts' counts, 0 of %d, and no cards (%s)" % [totals, str(acts.map(func(a): return [a.found, a.total]))])
	var leaks := func(view: Dictionary, row: Dictionary) -> Array:
		var text := JSON.stringify(view)
		var out: Array = []
		var table: String = {"inner": "inner_arts", "secret": "secret_arts"}.get(str(row.kind), "techniques")
		var words: Array = [str(row.id), str(ContentDB.entry(table, str(row.id)).get("name", ""))]
		for key in ["room", "object", "npc", "enemy", "item", "quest", "line"]:
			if row.src.has(key): words.append(str(row.src[key]))
		for w in words:
			if w != "" and w in text: out.append(w)
		return out
	var leaked: Array = []
	for row in rows: leaked.append_array(leaks.call(v, row))
	check(leaked.is_empty(), "decision 19: the board names no unfound art, draws none and says where none is (%s)" % str(leaked))
	var realm_was := cu.realm_key
	cu.realm_key = "heart_tempering_3"
	check((Game.progression.lost_arts_view(c).acts as Array).size() == 1, "a character in Act I sees Act I's count alone")
	cu.realm_key = realm_was
	# Found: its card, and still no source; the rest still unnamed.
	Game.apply_effects(c.id, [{"kind": "learn_lost_art", "art": "rain_of_reeds"}], "test")
	GameEvents.flush()
	v = Game.progression.lost_arts_view(c)
	var card: Dictionary = (v.acts[0].arts as Array)[0] if not (v.acts[0].arts as Array).is_empty() else {}
	var rr: Dictionary = ContentDB.entry("lost_arts", "rain_of_reeds")
	check(cu.techniques_known.has("rain_of_reeds") and c.quests.has_flag("found_rain_of_reeds") and int(v.acts[0].found) == 1
		and str(card.get("name", "")) == ContentDB.name_of("techniques", "rain_of_reeds") and str(card.get("desc", "")) != "",
		"found: Rain of Reeds is learned and its full card is on the board (%s)" % str(card))
	check(not card.has("src") and not str(rr.src.room) in JSON.stringify(v) and not str(rr.src.object) in JSON.stringify(v), "a found art's card never says where it was found")
	check(found_ev.size() == 1 and str(found_ev[0].art) == "rain_of_reeds" and int(found_ev[0].act) == 1, "lost_art_found is announced")
	leaked = []
	for row in rows:
		if str(row.id) != "rain_of_reeds": leaked.append_array(leaks.call(v, row))
	check(leaked.is_empty(), "the other unfound arts stay unnamed (%s)" % str(leaked))
	var pages0: int = c.inventory.count("manual_page")
	Game.progression.apply_learn_lost_art(c.id, "rain_of_reeds")
	check(c.inventory.count("manual_page") == pages0 + 1 and cu.techniques_known.count("rain_of_reeds") == 1, "found twice, it is a Manual Page")
	Game.progression.apply_learn_lost_art(c.id, "mist_lamp_meditation")
	Game.progression.apply_learn_lost_art(c.id, "grey_footfall")
	check(cu.inner_arts_known.has("mist_lamp_meditation") and cu.secret_arts.has("grey_footfall"), "an Inner Art and a Secret Art are learned as what they are")
	# A stele: a stone until its rubbing's condition holds.
	check(T.lost_at("insight_hu").any(func(row): return str(row.id) == "willowbark_script"), "Elder Hu's insight stone holds a stele")
	cu.daos = {"wood": {"tier": 1, "insight": 100.0}}
	while c.inventory.count("rubbing_kit") > 0: Game.inventory.apply_remove(c.id, "rubbing_kit", 1, "test")
	check(not Game.progression.read_stele(c, "insight_hu") and not cu.techniques_known.has("willowbark_script"), "without a Rubbing Kit it is only a stone")
	Game.inventory.apply_add(c.id, "rubbing_kit", 1, "test")
	check(Game.progression.read_stele(c, "insight_hu") and cu.techniques_known.has("willowbark_script"), "with a kit and the Wood Dao, its rubbing teaches Willowbark Script")
	check(not Game.progression.read_stele(c, "insight_hu") and c.inventory.count("rubbing_kit") == 1, "then it is a stone again, and the kit is kept")
	# A foe's manual: rolled like a named row on every kill, kept only while its art is lost, sure by its pity-th kill.
	var table := str(ContentDB.entry("enemies", "gorge_bandit_adept").get("loot", "gorge_bandit_adept"))
	var lost_rows: Array = (ContentDB.entry("loot_tables", table).get("lost", []) as Array).filter(func(r): return str(r.art) == "ember_burst")
	var row_eb: Dictionary = lost_rows[0] if not lost_rows.is_empty() else {"pity": 0, "item": ""}
	var rng := RandomNumberGenerator.new()
	rng.seed = 13
	var rolled: Array = LootRules.roll(table, rng, 30, 1.0, 0.0, {"no_equipment": true}).get("lost", [])
	check(rolled.size() == 1 and str(rolled[0].art) == "ember_burst" and not LootRules.roll(table, rng, 30, 1.0, 0.0, {}).items.any(func(it): return str(it.item) == str(row_eb.item)),
		"a kill rolls Ember Burst's manual beside its loot, and never hands it out itself")
	cu.tree.pity = {}
	var miss: Array = [{"art": "ember_burst", "item": str(row_eb.item), "pity": int(row_eb.pity), "hit": false}]
	var kills := 0
	var got: Array = []
	while got.is_empty() and kills < 100:
		kills += 1
		got = Game.progression.lost_drops(c, miss)
	check(kills == int(row_eb.pity) and int(row_eb.pity) > 0 and str(got[0].item) == str(row_eb.item) and not cu.tree.pity.has("ember_burst"),
		"never lucky, Ember Burst's manual still drops by kill %d (pity %d), and the count starts again" % [kills, int(row_eb.pity)])
	var hit: Array = [{"art": "ember_burst", "item": str(row_eb.item), "pity": int(row_eb.pity), "hit": true}]
	check(not Game.progression.lost_drops(c, hit).is_empty(), "a lucky roll drops it at once")
	Game.inventory.apply_add(c.id, str(row_eb.item), 1, "test")
	check(Game.progression.lost_drops(c, hit).is_empty(), "not while one is carried")
	cu.techniques_known.append("ember_burst")
	while c.inventory.count(str(row_eb.item)) > 0: Game.inventory.apply_remove(c.id, str(row_eb.item), 1, "test")
	check(Game.progression.lost_drops(c, hit).is_empty() and Game.progression.lost_drops(c, miss).is_empty(), "an art already found drops no manual")
	check(not (ContentDB.entry("loot_tables", table).get("rare", []) as Array).any(func(r): return str(r.item) == str(row_eb.item)), "and it is in no random roll")
	# Lu's journal: five pages teach the first piece of the Ferryman's Oar.
	var jf: Array = ContentDB.config("lost_arts").get("journal_flags", [])
	for i in 4: Game.quest.apply_flag(c.id, str(jf[i]))
	GameEvents.flush()
	check(not cu.techniques_known.has("oar_across_the_current"), "four pages are not enough")
	Game.quest.apply_flag(c.id, str(jf[4]))
	GameEvents.flush()
	v = Game.progression.lost_arts_view(c)
	var lin: Array = v.get("lineages", [])
	check(cu.techniques_known.has("oar_across_the_current") and lin.size() == 1 and str(lin[0].id) == "ferrymans_oar" and int(lin[0].found) == 1
		and (lin[0].arts as Array).size() == 1, "the fifth page teaches Oar Across the Current and opens the lineage's card with its one piece")
	check(not "ferry_pole_vault" in JSON.stringify(v) and not ContentDB.name_of("techniques", "ferry_pole_vault") in JSON.stringify(v), "the lineage never names its missing pieces")
	GameEvents.unsubscribe_object(self)
	cu.restore(snap)
	c.inventory.bag = bag_was
	c.quests.flags = flags_was
	Game.combat.refresh_stats(c.id)

## P13a the page's reads (technique_plan §4.10): the trees' tabs and one tree's nodes, each with its state and why it
## is closed, as the authority answers them (the page builds on these in P13b).
func tree_queries_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var snap := cu.snapshot()
	var T = TechniqueTreeRules
	cu.realm_key = "heart_tempering_3"
	cu.tree = {"v": 1, "realised": {}, "resets": {}, "pity": {}}
	cu.daos = {}
	cu.techniques_known = ["flowing_palm"]
	cu.technique_slots = [null, null, null, null, null, null, null, null]
	Game.combat.timeline(c.id).fight_t = -999.0
	var tabs: Array = Game.progression.tree_tabs(c)
	var by := {}
	for tab in tabs: by[str(tab.tree)] = tab
	check(tabs.size() == 11 and str(tabs[0].tree) == str(T.trees()[0]) and by.has("formless") and str(by.formless.element) == "none",
		"eleven tabs in the trees' order, Formless for the element-less arts (%s)" % str(tabs.map(func(t): return t.tree)))
	check(bool(by.water.open) and not bool(by.space.open) and not bool(by.time.open) and int(by.water.known) == 1 and str(by.water.name) != "",
		"at Level %d the nine element trees are open, Space and Time not yet; Water knows Flowing Palm" % ProgressionRules.level(c))
	var p1 := T.passage("water", "any", 1)
	Game.submit({"type": "realise_node", "node": p1})
	check(int(Game.progression.tree_tabs(c)[T.trees().find("water")].realised) == 1, "a realised node counts on its tab")
	var view: Dictionary = Game.progression.tree_view(c, "water")
	var nodes := {}
	for n in view.nodes: nodes[str(n.id)] = n
	var p2 := T.passage("water", "any", 2)
	var p9 := T.passage("water", "any", 9)
	check(nodes.size() == T.nodes_of("water").size() and str(nodes[p1].state) == "realised" and str(nodes["flowing_palm"].state) == "taught"
		and str(nodes[p2].state) == "open" and int(nodes[p2].cost) == T.cost(p2), "the tree's view: realised, taught and open nodes, with their costs")
	check(str(nodes[p9].state) == "locked" and str(nodes[p9].why) == "act_locked" and int(view.realisations.spent) == 1,
		"a later act's ring is locked and says why; the view carries the Realisations")
	# The tree reaches the fight (§6.2): ring 1's passage adds to the art's damage bucket, ring 2's cuts its Qi.
	var fp := ContentDB.entry("techniques", "flowing_palm")
	var cost0: float = Game.combat.technique_cost(c, fp)
	Game.submit({"type": "realise_node", "node": p2})
	var cost1: float = Game.combat.technique_cost(c, fp)
	check(near(float(T.passives(c, fp).damage), 0.01) and cost1 < cost0 and cost1 / cost0 > 0.97,
		"Flowing Palm: +1%% damage from ring 1's passage, and ring 2's cuts its Qi %.1f to %.1f" % [cost0, cost1])
	cu.restore(snap)
