extends RefCounted
## The preview and debug flags of the command line (decision 45, S7; docs/architecture/shell.md; the flags are listed in
## README.md, "Preview and debug arguments"). main.gd loads this script only when the game starts with arguments after
## "--" (OS.get_cmdline_user_args), so a player's game, which has none, never reads it. It is not in scripts/shell/:
## the shell never writes game state (contract_tests), and these flags do nothing else.
##   godot --path . -- --preview-world --room=lf_village --give=herbal_tea:3 --open-page=inventory --capture --shot=bag
##
## A run goes in steps, each a table of rows read in a fixed order:
##   1. before the boot (before_boot): the preview saves, --load=, --log-events;
##   2. the screen (OPEN, ROOM); with --preview-world, --load-slot or a room, the preview character is made (or the
##      loaded one taken), placed in the room (PLACE) and enters the world;
##   3. the state the picture shows (STEPS), table by table;
##   4. with --capture: the wait, then CAPTURE, and the picture saved as ../<shot>-preview.png; the game quits.
## A row is [flag, handler, needs]:
##   - flag: "--name=" takes a value; "--name" none; "--name[=]" either. In an EACH table a row runs once for each time
##     its flag is given, in the order the flags are given; in a ONCE table it runs once if its flag (or any flag of a
##     list) is given, in the table's order;
##   - handler: a function of this script, given the whole argument ("--foe=ashborn_raider:2"). The row holds the
##     function itself, never its name (contract_tests: no script calls a method by a name), so the tables are
##     variables, not constants;
##   - needs (optional): what must be there for the row to run, else it is skipped (_has).
## A handler that waits (a timer) holds every row after it, so a picture is taken once all before it has played.

const EACH := 0
const ONCE := 1

## The screen the preview opens on.
var OPEN := [ONCE, [
	["--topdown-proto", _topdown_proto],       # redesign Phase 1: the top-down prototype room, the real HUD
	["--topdown-tutorial", _topdown_tutorial], # Phase 4: the top-down game, as the title's hidden entry opens it
	["--preview-selection", _selection],
	["--preview-create", _creation],
]]
var ROOM := [EACH, [
	["--room=", _room],
	["--text-size=", _text_size],
]]
## The preview character placed in its room (--room=), before it enters the world.
var PLACE := [
	[EACH, [["--at=", _at]]],
	[ONCE, [["--unlock-all", _unlock_all], ["--debug-sect", _debug_sect]]],
]

## The state the picture shows, set up in turn.
var STEPS := [
	# The character, its account and its room (S38 debug tools; the S45 to S49 previews).
	[EACH, [
		["--pet=", _pet, ["active"]],
		["--mine=", _mine, ["sect"]],
		["--assault=", _assault, ["active"]],
		["--mount=", _mount, ["active"]],
		["--bag=", _bag, ["active"]],
		["--arena=", _arena, ["active"]],
		["--deed=", _deed, ["active"]],
		["--companion=", _companion, ["active"]],
		["--hearts=", _hearts, ["active"]],
		["--grudge=", _grudge, ["active"]],
		["--event=", _event, ["active"]],
		["--weather=", _weather],
		["--challenge", _challenge, ["active"]],
		["--fortune=", _fortune, ["active"]],
		["--tower=", _tower, ["active"]],
		["--climb=", _climb, ["active"]],
		["--activity=", _activity],
		["--phenomenon=", _phenomenon, ["active"]],
		["--egg=", _egg, ["active"]],
		["--give=", _give, ["active"]],
		["--realm=", _realm, ["active"]],
		["--wield=", _wield, ["active"]],
		["--relic=", _relic, ["active"]],
		["--awaken=", _awaken, ["active"]],
		["--join=", _join, ["active"]],
		["--foe=", _foe, ["active", "actor"]],
		["--defeat-foe[=]", _defeat_foe, ["room"]],
		["--pick-up[=]", _pick_up, ["room"]],
		["--equip=", _equip, ["active"]],
		["--hold=", _hold, ["moments"]],
		["--false-realm=", _false_realm, ["active"]],
		["--vessel=", _vessel, ["active"]],
	]],
	# Pages, talk and the room's people.
	[EACH, [
		["--open-page=", _open_page],
		["--tap=", _tap, ["page"]],
		["--preview-t=", _preview_t, ["technique_preview"]],
		["--talk=", _talk],
		["--interact=", _interact],
		["--shot=", _shot],
		["--posts-demo", _posts_demo, ["active", "room"]],
		["--welcome-demo", _welcome_demo, ["active", "room"]],
		["--guide-demo", _guide_demo, ["active"]],
		["--offer-fates", _offer_fates, ["active"]],
	]],
	[ONCE, [
		["--ride", _ride, ["world"]],
		["--fly", _fly, ["world"]],
	]],
	[EACH, [["--herb-ripe=", _herb_ripe, ["room"]]]],
	# Powers and things in play, held for the picture.
	[ONCE, [
		["--garden-preview", _garden_preview, ["room"]],
		["--tap-preview", _tap_preview, ["hud"]],
		[["--melody", "--throw", "--illusion"], _melody_throw_illusion, ["active"]],
		[["--swarm", "--arrays"], _swarm_arrays, ["active"]],
		["--beetle-swarm", _beetle_swarm, ["active"]],
		["--pet-wheel", _pet_wheel, ["hud"]],
	]],
	# The HUD, pressed as the player presses it.
	[EACH, [
		["--toggle=", _toggle, ["active"]],
		["--fan=", _fan, ["hud"]],
		["--tap-points=", _tap_points, ["hud"]],
		["--use-item=", _use_item, ["active", "hud"]],
	]],
	# The moments (P6).
	[EACH, [
		["--moment=", _moment, ["moments"]],
		["--breakthrough[=]", _breakthrough, ["moments", "active"]],
	]],
]

## With --capture, once the picture's wait is over.
var CAPTURE := [
	[EACH, [["--auto-path=", _auto_path, ["active"]], ["--auto-hunt", _auto_hunt, ["active"]]]],
	[EACH, [["--wait=", _wait]]],
	[EACH, [["--hazard=", _hazard]]],
]

var main               ## the shell (scripts/main.gd)
var args: Array        ## the arguments after "--"
var room := ""         ## --room=: the room the preview character starts in
var shot := ""         ## --shot=: the picture's name (the screen's when none is given)
var moment_t := -1.0   ## P6: with --capture, the picture is taken this many seconds after a moment starts

## main's views, read at each use (the world view is remade when the world is entered again).
var world:
	get: return main.world
var hud:
	get: return main.hud
var moments:
	get: return main.moments

func _init(shell: Node, user_args: Array) -> void:
	main = shell
	args = user_args

# ------------------------------------------------------------------ running the tables
## Before Game.boot: every preview plays on saves of its own (debug tools, S38: --load= plays from a copy of any save
## folder, e.g. a valley_run checkpoint), and --log-events prints the event stream.
func before_boot() -> void:
	Saves.use_folder("user://preview_saves/")
	for a in args:
		if str(a).begins_with("--load="): _load(str(a))
	if "--log-events" in args:
		GameEvents.event.connect(func(n: String, p: Dictionary): if n not in ["resource_changed", "meditation_tick"]: print("[event] ", n, " ", p))

## Once the title is up: the screen, the preview character, the state, and with --capture the picture.
func run() -> void:
	await _run(OPEN)
	await _run(ROOM)
	if "--load-slot" in args or "--preview-world" in args or room != "": await _enter()
	shot = main.screen
	for stage in STEPS: await _run(stage)
	if "--capture" in args: await _capture()

func _run(stage: Array) -> void:
	if stage[0] == ONCE:
		for row in stage[1]:
			if _given(row[0]) and _met(row): await (row[1] as Callable).call("")
		return
	for a in args:
		for row in stage[1]:
			if _matches(str(a), str(row[0])):
				if _met(row): await (row[1] as Callable).call(str(a))
				break

static func _matches(a: String, flag: String) -> bool:
	if flag.ends_with("[=]"): return a.begins_with(flag.trim_suffix("[=]"))
	if flag.ends_with("="): return a.begins_with(flag)
	return a == flag

func _given(flag) -> bool:
	if flag is Array: return (flag as Array).any(func(f): return f in args)
	return flag in args

func _met(row: Array) -> bool:
	return row.size() < 3 or (row[2] as Array).all(_has)

## What a row needs.
func _has(need: String) -> bool:
	match need:
		"active": return Game.active() != null
		"actor": return Game.actor_state(Game.active_id) != null
		"sect": return Game.sect.founded()
		"room": return Game.room_rt != null
		"world": return is_instance_valid(world)
		"hud": return is_instance_valid(hud)
		"moments": return is_instance_valid(moments)
		"page": return main.top_page() != null
		"technique_preview": return main.top_page() != null and main.top_page().get("stage") is TechniquePreview
	push_error("debug_args: no need %s" % need)
	return false

## A flag's value: what follows its "=".
static func _val(a: String) -> String:
	return a.substr(a.find("=") + 1)

func _after(seconds: float) -> void:
	await main.get_tree().create_timer(seconds).timeout

# ------------------------------------------------------------------ before the boot
func _load(a: String) -> void:
	var src := _val(a)
	if not src.ends_with("/"): src += "/"
	# The copy is named after its source, so two previews of different checkpoints run at once do not clobber each
	# other's copy.
	var dst := "user://loaded_%s/" % src.trim_suffix("/").get_file()
	DirAccess.make_dir_recursive_absolute(dst)
	for f in DirAccess.get_files_at(dst): DirAccess.remove_absolute(dst + f)
	for f in DirAccess.get_files_at(src): DirAccess.copy_absolute(src + f, dst + f)
	Saves.use_folder(dst)

# ------------------------------------------------------------------ the screen and the preview character
func _topdown_proto(_a: String) -> void:
	main.enter_topdown_proto(false)

func _topdown_tutorial(_a: String) -> void:
	main.enter_topdown_tutorial(false)

func _selection(_a: String) -> void:
	main.show_selection()

func _creation(_a: String) -> void:
	main.show_creation(1)

func _room(a: String) -> void:
	room = _val(a)

## Debug tools (S38): preview at a text size (0 small, 1 normal, 2 large).
func _text_size(a: String) -> void:
	Game.account.settings["text_size"] = clampi(int(_val(a)), 0, 2)

## The preview character (made in slot 1 when there is none, unless --load-slot plays the loaded save's), placed in the
## room when one is given, and in the world.
func _enter() -> void:
	var loaded := "--load-slot" in args   # --room= with it starts the loaded character in that room
	if not loaded and Game.character("c1") == null:
		Game.submit({"type": "create_character", "slot": 1, "name": Tx.t("main.preview"), "appearance": {"hair": "topknot", "shirt": "disciple"}})
	if room != "" and Game.character("c1") != null:
		Game.character("c1").position = {"room": room, "portal": "", "x": 0.0, "y": 0.0, "facing": 1}
		for stage in PLACE: await _run(stage)
	main.enter_world(1)

## --at=x,y starts the preview at a point in the room.
func _at(a: String) -> void:
	var ch = Game.character("c1")
	var xy := _val(a).split(",")
	ch.position.x = float(xy[0])
	ch.position.y = float(xy[1]) if xy.size() > 1 else 840.0

func _unlock_all(_a: String) -> void:
	Unlocks.debug_force_all = true

## A founded sect with every building at level 1, for previews.
func _debug_sect(_a: String) -> void:
	var b := {}
	for row in ContentDB.all("sect_buildings"): b[str(row.id)] = 1
	Game.account.sect = {"name": Tx.t("main.preview_sect"), "emblem": [0, 0], "level": 6, "prestige": 0, "buildings": b, "queue": [],
		"disciples": [], "candidates": [], "expeditions": [], "candidate_day": -1}

# ------------------------------------------------------------------ the character, its account and its room
## --pet=species[:stage[:purity[:hearts]]] grants an animal and makes it active (S46 previews).
func _pet(a: String) -> void:
	var pa := _val(a).split(":")
	Game.pets.apply_grant(Game.active().id, pa[0])
	var np: Dictionary = Game.active().pets[Game.active().pets.size() - 1]
	if pa.size() > 1: np.stage = pa[1]
	if pa.size() > 2: Game.pets.add_purity(Game.active(), np, int(pa[2]) - int(np.purity))
	if pa.size() > 3: np.bond = float(pa[3])
	Game.active().active_pet = str(np.uid)

## --mine=id[:contested] gives the (debug) sect a spirit mine with ten hours in its carts and two disciples, one on guard
## (S49 territory previews); --assault=id starts the fight for one.
func _mine(a: String) -> void:
	var ma := _val(a).split(":")
	var now := Clock.now_utc()
	if Game.sect.sect().disciples.is_empty():
		var names: Array = ContentDB.config("disciples").get("names", [])
		for k in 2:
			Game.sect.sect().disciples.append({"name": str(names[k % names.size()]) if not names.is_empty() else "", "strength": 3 - k, "spirit": 2 + k * 2,
				"craft": 1 + k, "trait": "green_thumb", "level": 4 - k * 2})
	var all: Dictionary = Game.sect.sect().get("mines", {})
	all[ma[0]] = {"collected": now - 36000.0, "contest": now + 180000.0, "contested": ma.size() > 1, "until": now + 5.5 * 3600.0 if ma.size() > 1 else 0.0,
		"guards": [0], "n": 0}
	Game.sect.sect().mines = all

func _assault(a: String) -> void:
	Game.submit({"type": "assault_mine", "mine": _val(a)})

## --mount=species grants an animal and puts it in the Mount slot, riding (S46 previews).
func _mount(a: String) -> void:
	Game.pets.apply_grant(Game.active().id, _val(a))
	var mp: Dictionary = Game.active().pets[Game.active().pets.size() - 1]
	Unlocks.force_unlock(Game.active().id, "mounts")
	Game.pets.set_mount(Game.active(), str(mp.uid), null)

## --bag=species[,species] grants animals and carries them in the Spirit Beast Bag.
func _bag(a: String) -> void:
	Game.inventory.apply_add(Game.active().id, "beast_bag_star", 1, "debug")
	var keep: String = Game.active().active_pet
	for sp in _val(a).split(","):
		Game.pets.apply_grant(Game.active().id, sp)
		Game.active().pet_bag.append(str(Game.active().pets[Game.active().pets.size() - 1].uid))
	Game.active().active_pet = keep

## --arena=solo|trio fights one Beast Arena challenge (S46 previews).
func _arena(a: String) -> void:
	Game.pets.arena_challenge(Game.active(), _val(a))

## --deed=id applies one karma.json deed (S49 Relations previews); repeatable.
func _deed(a: String) -> void:
	Game.relations.apply_deed(Game.active().id, _val(a))

## --companion=id adds a fellow disciple to the party (S26/S49 previews).
func _companion(a: String) -> void:
	Game.companions.apply_add(Game.active().id, _val(a))

## --hearts=npc:n sets that person's hearts (S49 affinity previews).
func _hearts(a: String) -> void:
	var hp := _val(a).split(":")
	Game.relations.apply_affinity(Game.active().id, hp[0], int(hp[1]) * 100 - Game.relations.points(Game.active(), hp[0]) if hp.size() > 1 else 100, "debug")

## --grudge=faction:n sets a faction's grudge (S49 previews).
func _grudge(a: String) -> void:
	var gp := _val(a).split(":")
	Game.relations.apply_grudge(Game.active().id, gp[0], int(gp[1]) - Game.relations.grudge(Game.active(), gp[0]) if gp.size() > 1 else 30, "debug")

## --event=id moves the clock ten minutes into that world event's next opening (S49).
func _event(a: String) -> void:
	var up: Dictionary = Game.calendar.upcoming_of(_val(a))
	if not up.is_empty(): Clock.debug_offset_s += maxf(0.0, float(up.start) + 600.0 - Clock.now_utc())

## --weather=rain|fog|storm previews a sky in rooms that have weather (S49).
func _weather(a: String) -> void:
	Game.calendar.debug_weather = _val(a)

## A young master's challenge waits in this room (S49 Fame previews).
func _challenge(_a: String) -> void:
	Game.relations.offer_challenge(Game.active(), "young_master")

## --fortune=card turns up that fortune encounter here, meter or not (S49 previews).
func _fortune(a: String) -> void:
	var card := ContentDB.entry("fortune_deck", _val(a))
	if not card.is_empty(): Game.relations.fortune_check(Game.active(), str((card.get("triggers", ["room_entered"]) as Array)[0]), str(card.id))

## --tower=N marks the Trial Tower cleared to floor N (S49 previews).
func _tower(a: String) -> void:
	Game.active().tower["cleared"] = int(_val(a))

## --climb=N starts Trial Tower floor N (S49 previews).
func _climb(a: String) -> void:
	Game.world.climb_tower(Game.active(), int(_val(a)))

## --activity=N sets today's activity points (S49 chest previews).
func _activity(a: String) -> void:
	Game.accounts.activity()["points"] = int(_val(a))

## --phenomenon=cloud|lightning shows the heavens answering a breakthrough here (S49).
func _phenomenon(a: String) -> void:
	Game.calendar.raise_phenomenon(Game.active().id, _val(a), Game.active().cultivator.realm_key)

## --egg=species puts a warming egg in the nest (S46 incubation previews).
func _egg(a: String) -> void:
	Game.active().eggs.append({"species": _val(a), "hatch_utc": Clock.now_utc() + 7200.0})

## --give=item[:count[:quality]] puts items in the bag for previews.
func _give(a: String) -> void:
	var g := _val(a).split(":")
	if ContentDB.item(g[0]).has("draught"): Game.inventory.apply_draught(Game.active().id, g[0], int(g[1]) if g.size() > 1 else 1, "debug")
	else: Game.inventory.apply_add(Game.active().id, g[0], int(g[1]) if g.size() > 1 else 1, "debug", {"quality": g[2]} if g.size() > 2 else {})

## --realm=key previews at a realm; every aptitude shows.
func _realm(a: String) -> void:
	var c = Game.active()
	c.cultivator.realm_key = _val(a)
	for k in c.cultivator.aptitude: c.cultivator.aptitude[k].revealed = true
	Game.combat.refresh_stats(c.id)

## --wield=item puts a weapon straight into the hand (S47 v1.1 weapon family previews).
func _wield(a: String) -> void:
	var c = Game.active()
	var id := _val(a)
	Game.inventory.apply_add_equipment(c.id, id, 14, "common", "debug")
	var i: int = c.inventory.first_index(id)
	if i >= 0:
		var was = c.inventory.equipped.get("weapon")
		c.inventory.equipped["weapon"] = c.inventory.bag[i]
		c.inventory.bag[i] = was
		Game.combat.refresh_stats(c.id)

## --relic=item[:awake[:affinity]] holds a bound relic, its spirit asleep or awake, and has the spirit speak once (S47
## Artifact Spirit previews).
func _relic(a: String) -> void:
	var c = Game.active()
	var ra := _val(a).split(":")
	var inst := LootRules.make_instance(ra[0], int(ContentDB.item(ra[0]).get("ilv", 50)), "fine", null, c.inventory.take_uid())
	inst.erase("sealed")
	inst.bound = true
	if ra.size() > 1 and ra[1] == "awake": inst.spirit = "awake"
	if ra.size() > 2: inst.spirit_affinity = float(ra[2])
	var was = c.inventory.equipped.get("weapon")
	c.inventory.equipped["weapon"] = inst
	if was != null: Game.inventory.apply_add_instance(c.id, was, "debug")
	for fid in ["iron_jian", "iron_spear"]: Game.inventory.apply_add_equipment(c.id, fid, 10, "common", "debug")
	Game.inventory.apply_add(c.id, str(ContentDB.item(ra[0]).get("spirit", {}).get("favourite", "refining_essence")), 3, "debug")
	Game.combat.refresh_stats(c.id)
	Game.inventory.speak(c, inst, "awake" if str(inst.spirit) == "awake" else "gift", true)

## --awaken=item[:awake] holds that weapon at +10 with its Dao at Explanation and a Weapon Soul Crystal in the bag,
## awakened already with ":awake" (S47 weapon awakening previews).
func _awaken(a: String) -> void:
	var c = Game.active()
	var ka := _val(a).split(":")
	var inst := LootRules.make_instance(ka[0], int(ContentDB.item(ka[0]).get("ilv", 45)), "fine", null, c.inventory.take_uid())
	inst.enhance = 10
	if ka.size() > 1 and ka[1] == "awake": inst.awakened = true
	var was = c.inventory.equipped.get("weapon")
	c.inventory.equipped["weapon"] = inst
	if was != null: Game.inventory.apply_add_instance(c.id, was, "debug")
	var dao := str(ContentDB.entry("weapon_families", str(ContentDB.item(ka[0]).get("family", ""))).get("dao", "sword"))
	c.cultivator.daos[dao] = {"tier": 4, "insight": 0.0}
	Unlocks.force_unlock(c.id, "smithing")
	Game.inventory.apply_add(c.id, "weapon_soul_crystal", 1, "debug")
	Game.combat.refresh_stats(c.id)

## --join=sect[:rank] joins a training sect at a rank with 2000 contribution (sect role previews).
func _join(a: String) -> void:
	var ja := _val(a).split(":")
	var c = Game.active()
	c.training_sect = {}
	Game.training.apply_join(c.id, ja[0])
	if ja.size() > 1:
		for rk in ContentDB.config("sect_ranks").get("order", []):
			Game.training.apply_rank(c.id, str(rk))
			if str(rk) == ja[1]: break
	Game.training.apply_contribution(c.id, 2000, "debug")

## --foe=enemy[:count[:hp]] sets foes in front of the player (combat previews), at a share of their HP if given (a boss
## past a phase, P6).
func _foe(a: String) -> void:
	var fa := _val(a).split(":")
	var st: ActorState = Game.actor_state(Game.active_id)
	for k in (int(fa[1]) if fa.size() > 1 else 1):
		var foe: EnemyState = Game.enemies.spawn_at(fa[0], st.plane + Vector2(110 + k * 60, -10 + (k % 2) * 20), ProgressionRules.level(Game.active()) + 5)
		if foe and fa.size() > 2: foe.pools.hp = foe.pools.max_hp * float(fa[2])

## --defeat-foe[=s] defeats the first foe in the room after s seconds (default 1) through Combat, with its real drop (P6
## previews of a boss's fall and the loot fountain).
func _defeat_foe(a: String) -> void:
	await _after(float(a.get_slice("=", 1)) if a.contains("=") else 1.0)
	for e in Game.room_rt.living_enemies():
		if e.team == "enemy":
			Game.combat.defeat(e, Game.active_id)
			break
	if moment_t < 0.0: moment_t = moments.hold_at if is_instance_valid(moments) and moments.hold_at >= 0.0 else 0.3   # with --capture: the drop in the air

## --pick-up[=s] picks up everything lying in the room after s seconds (default 1), through the pick_up intent (previews
## of the equip prompt a find raises).
func _pick_up(a: String) -> void:
	await _after(float(a.get_slice("=", 1)) if a.contains("=") else 1.0)
	for l in Game.room_rt.loot.duplicate(): Game.submit({"type": "pick_up", "uid": int(l.uid)})

## --equip=item wears the newest piece of that item in the bag, through the equip intent.
func _equip(a: String) -> void:
	var eb: Array = Game.active().inventory.bag
	var newest := -1
	for i in eb.size():
		if eb[i] != null and str(eb[i].id) == _val(a) and (newest < 0 or int(eb[i].get("uid", 0)) > int(eb[newest].get("uid", 0))): newest = i
	if newest >= 0: Game.submit({"type": "equip", "index": newest})

## --hold=t[:row] holds the moment on screen (or only that row) once it reaches t s (pictures of real ones).
func _hold(a: String) -> void:
	var ho := _val(a).split(":")
	moments.hold_at = float(ho[0])
	moments.hold_row = ho[1] if ho.size() > 1 else ""

## --false-realm=key previews Concealment's false realm (S48).
func _false_realm(a: String) -> void:
	if not "concealment" in Game.active().cultivator.secret_arts: Game.active().cultivator.secret_arts.append("concealment")
	Game.submit({"type": "set_false_realm", "realm": _val(a)})

## --vessel=item previews a flight vessel (G2); pair it with --fly.
func _vessel(a: String) -> void:
	var id := _val(a)
	Game.inventory.apply_add(Game.active().id, id, 1, "debug")
	Game.submit({"type": "choose_vessel", "item": id})

# ------------------------------------------------------------------ pages, talk and the room's people
## --open-page=id[:tab].
func _open_page(a: String) -> void:
	await _after(0.8)
	var spec := _val(a).split(":")
	main.open_page(spec[0], {"tab": spec[1]} if spec.size() > 1 else {})

## --tap=x,y taps the top page there (a press and a release), for previews of a page's states.
func _tap(a: String) -> void:
	await _after(0.6)
	var xy := _val(a).split(",")
	for down in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.pressed = down
		ev.position = Vector2(float(xy[0]), float(xy[1]))
		main.top_page()._gui_input(ev)

## --preview-t=s holds the Techniques page's preview s into its loop, for pictures of its frames.
func _preview_t(a: String) -> void:
	await _after(0.3)
	main.top_page().stage.hold(float(_val(a)))

## --talk=npc.
func _talk(a: String) -> void:
	await _after(0.8)
	var r := Game.submit({"type": "talk", "npc": _val(a)})
	if r.get("ok", false) and r.has("dialogue"): main.open_page("dialogue", {"convo": r.dialogue})

## --interact=object uses a room object as if pressed (a thief to chase, a route stone).
func _interact(a: String) -> void:
	await _after(0.8)
	Game.submit({"type": "interact", "object": _val(a)})

func _shot(a: String) -> void:
	shot = _val(a)

## Two more characters keeping post at this room's nodes, hours in, for Roll-Call previews (S50).
func _posts_demo(_a: String) -> void:
	var nodes: Array = Game.room_rt.def.get("objects", []).filter(func(o): return Game.posts.craft_of_object(o) != "")
	for k in mini(2, nodes.size()):
		var slot := 2 + k
		Game.account.slots_unlocked = maxi(Game.account.slots_unlocked, slot)
		if not Game.characters.has("c%d" % slot): Game.submit({"type": "create_character", "slot": slot, "name": [Tx.t("main.wen_ruo"), Tx.t("main.bai_lin")][k], "skip_prologue": true})
		var oc = Game.character("c%d" % slot)
		if oc == null: continue
		for u in ["keeping_post", "insect_netting", "herb_gathering", "mining", "fishing"]: Unlocks.force_unlock(oc.id, u)
		oc.posts = {"post": {"kind": "craft", "craft": Game.posts.craft_of_object(nodes[k]), "room": Game.room_rt.room_id,
			"object": str(nodes[k].id), "since": Clock.now_utc() - 3600.0 * (2.5 + 9.0 * k), "paused": false}, "crafts": {}, "pouch": {}}
		oc.position.room = Game.room_rt.room_id

## The active character comes in from 7.5 hours at its post (or at this room's first node), for Welcome Back previews
## (P5): the real Return Ledger of the post authority, opened as entering the world does.
func _welcome_demo(_a: String) -> void:
	var c = Game.active()
	var node: Array = Game.room_rt.def.get("objects", []).filter(func(o): return Game.posts.craft_of_object(o) != "")
	if not Game.posts.has_post(c) and not node.is_empty():
		c.posts["post"] = {"kind": "craft", "craft": Game.posts.craft_of_object(node[0]), "room": Game.room_rt.room_id, "object": str(node[0].id)}
	if Game.posts.has_post(c): Game.posts.post_of(c).merge({"paused": false, "since": Clock.now_utc() - 3600.0 * 7.5}, true)
	var welcome := {}
	AccountAuthority.with_ledger(welcome, Game.posts.on_entered(c))
	await _after(0.8)
	if not welcome.is_empty(): main.open_page("welcome", welcome)

## Quest states that show every head marker in Lotus Ferry and a tracked quest leading out (P1).
func _guide_demo(_a: String) -> void:
	var gq = Game.active().quests
	gq.done["fists_first"] = 1
	gq.done["crab_trouble"] = 1
	gq.active["guos_old_wound"] = {"state": "active", "progress": [0], "accepted_tick": 0}
	gq.offered["the_muddy_wash"] = true
	gq.active["glowflies"] = {"state": "active", "progress": [0], "accepted_tick": 0}
	gq.tracked = ["glowflies"]

## A fate offer for previews of the picker (S48).
func _offer_fates(_a: String) -> void:
	Game.active().cultivator.fate_offer = ["thunder_tempered", "lucky_star", "scar_of_failure"]

# ------------------------------------------------------------------ riding, flight, herbs and powers
## Riding a mount (a Jade Crane is granted when there is no mountable animal).
func _ride(_a: String) -> void:
	await _after(0.3)
	var c = Game.active()
	var mount_uid := ""
	for pt in c.pets:
		if Game.pets.mountable(pt): mount_uid = str(pt.uid)
	if mount_uid == "":
		Game.pets.apply_grant(c.id, "jade_crane")
		mount_uid = str(c.pets[c.pets.size() - 1].uid)
	Game.submit({"type": "set_active_pet", "pet": mount_uid})
	Game.submit({"type": "set_pet_role", "pet": mount_uid, "role": "mount"})

## Flight (Cloud Stride), with a filled Qi pool: Combat takes it up as the player's held jump would, and the body
## climbs for 0.9 s.
func _fly(_a: String) -> void:
	await _after(0.5)
	var c = Game.active()
	c.pools.max_qi = maxf(c.pools.max_qi, 400.0)
	c.pools.qi = c.pools.max_qi
	Unlocks.force_unlock(c.id, "flight")
	if not Game.submit({"type": "start_flight"}).get("ok", false) or not is_instance_valid(world.player): return
	world.player.motor.fly(true)
	world.player.fly_up = true
	await _after(0.9)
	if is_instance_valid(world.player): world.player.fly_up = false

## --herb-ripe=object moves the clock to a rare herb's next ripening, in its season (S45).
func _herb_ripe(a: String) -> void:
	var ho: Dictionary = Game.room_rt.object_def(_val(a))
	for i in 40:
		if ho.is_empty(): break
		var hs := HerbRules.ripen_state(ho, Clock.now_utc())
		if HerbRules.in_season(ho, Clock.now_utc()) and hs.ripe: break
		Clock.debug_offset_s += 604800.0 if not HerbRules.in_season(ho, Clock.now_utc()) else float(hs.seconds) + 120.0

## This room's garden beds filled to show every state (S45).
func _garden_preview(_a: String) -> void:
	var gc = Game.active()
	var keys: Array = Game.crafting.room_beds(gc, Game.room_rt.room_id)
	var fill := [["willow_moss", 0.45, 0], ["cloudtop_orchid", 0.8, 1], ["riverreed_ginseng_100", 1.0, 0]]
	for i in mini(keys.size(), fill.size()):
		var rec: Dictionary = Game.crafting.bed_record(gc, str(keys[i]))
		rec.herb = str(fill[i][0])
		rec.progress = float(fill[i][1])
		rec.soil = int(fill[i][2])
		rec.grow_s = 8.0 * 3600.0
		rec.updated = Clock.now_utc()
	for it in [["spring_water", 2], ["spirit_soil", 1], ["verdant_dew_vial", 1], ["willow_moss_seed", 3], ["ember_pepper_seed", 2]]:
		Game.inventory.apply_add(gc.id, str(it[0]), int(it[1]), "debug")
	gc.crafting["dew"] = {"count": 2, "last": Clock.now_utc() - 3600.0}
	Game.inventory.apply_add(gc.id, "drying_rack", 1, "debug")
	Game.inventory.apply_add(gc.id, "mist_lotus", 6, "debug")
	Game.inventory.apply_add(gc.id, "riverreed_ginseng_10", 4, "debug")
	Game.inventory.apply_add(gc.id, "rice_wine", 1, "debug")
	gc.crafting["racks"] = [{"kind": "steamed", "herb": "mist_lotus", "count": 5, "done": Clock.now_utc() + 1400.0}]

## The harvest ring held part-way through its shrink (S45).
func _tap_preview(_a: String) -> void:
	await _after(1.0)
	hud.tapping = {"object": "preview", "t": 660.0, "ring": 1000.0, "target": 0.7, "window": 0.16}

## --melody holds the flute's melody; --throw throws the fan (S47 v1.1 previews); --illusion leaves Phantom Double's
## illusion and steps the player aside (S48 the Soul line). One of them, in that order.
func _melody_throw_illusion(_a: String) -> void:
	await _after(1.0 if "--melody" in args or "--illusion" in args else 2.2)
	Unlocks.force_unlock(Game.active_id, "composure")
	if "--melody" in args: Game.submit({"type": "channel_melody", "on": true})
	elif "--illusion" in args:
		Game.combat.cast_illusion(Game.active(), ContentDB.entry("techniques", "phantom_double"))
		if is_instance_valid(world) and world.player: world.player.state.plane += Vector2(-150, 30)
	else: Game.combat.start_step(Game.active(), ContentDB.entry("weapon_families", "fan"), 2, 1)

## --swarm raises a nine-sword swarm; --arrays lays a guarding, a killing and a binding array side by side (S47/S48 v1.1
## previews).
func _swarm_arrays(_a: String) -> void:
	await _after(1.0)
	var dc = Game.active()
	if "--swarm" in args:
		dc.cultivator.daos["sword"] = {"tier": 5, "insight": 0.0}
		Game.combat.start_swarm(dc, true, 60.0)
	if "--arrays" in args and is_instance_valid(world) and world.player:
		var home: Vector2 = world.player.state.plane
		for k in [["guard", 0], ["killing", 340], ["binding", 680]]:
			world.player.state.plane = home + Vector2(float(k[1]), 0)
			Game.combat.deploy_array(dc.id, {"array": str(k[0]), "radius": 150, "duration": 60})
		world.player.state.plane = home

## The Copperjaw Box opened (v1.2 Phase D), so the swarm circles the character.
func _beetle_swarm(_a: String) -> void:
	await _after(1.0)
	Game.pets.release_swarm(Game.active())

## The Pet button's command wheel held open, Stay picked (v2 HUD previews).
func _pet_wheel(_a: String) -> void:
	await _after(1.0)
	hud.pet_wheel = true
	hud.pet_pick = 1

# ------------------------------------------------------------------ the HUD
## --toggle=presence|sphere holds a field power through its intent (P5a previews of the fan and its pinned toggles).
func _toggle(a: String) -> void:
	await _after(0.5)
	Game.submit({"type": "toggle_" + _val(a)})

## --fan=open|closed sets the HUD's fan.
func _fan(a: String) -> void:
	hud.fan_open = _val(a) == "open"
	hud.fan_rest_open = hud.fan_open

## --tap-points=kind taps a points badge through the HUD, as the player does (its page opens on its tab).
func _tap_points(a: String) -> void:
	await _after(1.0)
	var pid := "points:" + _val(a)
	for tg in hud.hit_targets():
		if str(tg.role) == pid:
			hud.press(90, tg.center)
			hud.release(90)

## --use-item=item[:hp] sets the HP share (default as it is), puts the item in Quick-use and taps it through the HUD, as
## the player does; with --capture the picture is taken 0.5 s after (feedback previews).
func _use_item(a: String) -> void:
	var ua := _val(a).split(":")
	var uc = Game.active()
	await _after(2.0)   # past the arrival's spawn protection
	if uc.inventory.count(ua[0]) <= 0: Game.inventory.apply_add(uc.id, ua[0], 1, "debug")
	if ua.size() > 1: uc.pools.hp = uc.pools.max_hp * float(ua[1])
	Game.submit({"type": "set_quick_use", "item": ua[0], "slot": 0})
	uc.pools.cooldowns.clear()
	hud.use_quick()
	moment_t = 0.5

# ------------------------------------------------------------------ moments (P6)
## --moment=id[:t] plays a moments.json row with its sample payload and holds it at t s; with --capture the picture is
## taken at t.
func _moment(a: String) -> void:
	var mo := _val(a).split(":")
	await _after(1.0)
	moment_t = float(mo[1]) if mo.size() > 1 else 2.0
	moments.preview(mo[0], moment_t)

## --breakthrough[=t] takes the character over its next step at once, through the progression authority (a great step
## when it stands at one), and holds its moment at t s (previews of the real stat rise).
func _breakthrough(a: String) -> void:
	await _after(1.5)
	var bc = Game.active()
	var nxt := ContentDB.next_realm(bc.cultivator.realm_key)
	moment_t = float(a.get_slice("=", 1)) if a.contains("=") else 2.4
	moments.hold_at = moment_t
	if nxt != "": Game.progression.advance(bc, nxt, bool(ContentDB.realm(nxt).get("major", false)))

# ------------------------------------------------------------------ --capture
## The picture: after 2.5 s, or just past the moment's t; then --auto-path= and --auto-hunt, --wait=s, --hazard=; saved
## as ../<shot>-preview.png beside the project, and the game quits.
func _capture() -> void:
	await _after(2.5 if moment_t < 0.0 else moment_t + 0.05)
	for stage in CAPTURE: await _run(stage)
	await RenderingServer.frame_post_draw
	main.get_tree().root.get_texture().get_image().save_png("res://../" + (shot if shot != "" else main.screen) + "-preview.png")
	main.get_tree().quit()

## --auto-path=room walks there (S49).
func _auto_path(a: String) -> void:
	Game.submit({"type": "auto_path", "target": _val(a)})

## --auto-hunt fights (S49).
func _auto_hunt(_a: String) -> void:
	Game.submit({"type": "set_auto_hunt", "on": true})

## --wait=s lets them run.
func _wait(a: String) -> void:
	await _after(float(_val(a)))

## --hazard=phase[:fraction] holds the room's hazards in one state.
func _hazard(a: String) -> void:
	var hz := _val(a).split(":")
	Game.world.debug_hazard_phase(hz[0], float(hz[1]) if hz.size() > 1 else 0.5)
	await _after(0.1)
