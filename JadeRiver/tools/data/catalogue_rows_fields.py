"""V9f3 · the Part 8 room verticality catalogue rows V2d left partial (fields). Runs after catalogue.run(ROOMS) and
before the movement and verticality passes (tools/data/world.py build()). Keep to this group's rooms.

Each function below shapes one room to its row of the "Room verticality catalogue" (Build Prompt v2, Part 8): the
tiers at the row's heights, the pieces it names (stilt decks, rafts, stepping stones, depth stairs, pillars, updraft
columns) and what is up there. A room built whole is marked authored (catalogue.authored), so the generic movement
and verticality passes leave it alone and the room lint (tools/data/room_lint.py) checks exactly what is here; a room
that only gains a piece or two is left to those passes.

Two engine limits shape some rows (see docs/v9f3_fields.md):
  - objects do not ride movers, so a chest or a herb "on" a raft or a boat sits on a moored one, and the moving ones
    carry the player to it;
  - flight holds at most 340 above the ground (stats flight.ceiling), so the ledges above that are reached by riding
    updraft columns (jump or glide into one and it lifts you to its top), not by flying.
"""
from catalogue import authored, drop_decor, obj, surf, clear_tiers


def _w():
    import world
    return world


# ------------------------------------------------------------------ helpers
def drop_surfaces(r, ids):
    """Remove surfaces (and the climbables and movers that use them); whatever stood on them comes down."""
    ids = set(ids)
    for o in r.d["objects"]:
        if o.get("surface") in ids:
            o["alt"] = 0
            o.pop("surface", None)
    r.d["surfaces"] = [s for s in r.d["surfaces"] if s["id"] not in ids]
    r.d["climbables"] = [c for c in r.d.get("climbables", []) if c.get("top") not in ids and c.get("bottom") not in ids]
    r.d["movers"] = [m for m in r.d.get("movers", []) if m["surface"] not in ids]


def put(o, x, y, alt=0, sid=None):
    """Stand an object at (x, y) on a surface `sid` at `alt` (or on the ground)."""
    o["at"] = [x, y]
    o["alt"] = alt
    if sid:
        o["surface"] = sid
    else:
        o.pop("surface", None)
    return o


def on(r, sid, frac=0.5, dy=0):
    """A point on a surface: `frac` of the way along it, in the middle of its depth; and its height."""
    s = surf(r, sid)
    x, y, w, d = s["rect"]
    return [int(x + w * frac), int(y + d / 2 + dy)], int(s["height"])


def place_on(r, o, sid, frac=0.5):
    at, h = on(r, sid, frac)
    return put(o, at[0], at[1], h, sid)


def of_type(r, otype):
    return [o for o in r.d["objects"] if o["type"] == otype]


def in_rect(p, rect, pad=0):
    x, y, w, d = rect
    return x - pad <= p[0] <= x + w + pad and y - pad <= p[1] <= y + d + pad


def dry_spawns(r, rects, y_to=None):
    """Spawn points that would wait in deep water step out onto the bank behind it."""
    for sp in r.d["spawns"]:
        pts = []
        for p in sp["points"]:
            for rect in rects:
                if in_rect(p, rect):
                    p = [p[0], (y_to if y_to is not None else rect[1] - 40)]
            pts.append(p)
        sp["points"] = pts


def move_area(r, kind, near, to, radius=40):
    """Move a room area (a Hollow puddle, a thorn thicket) and its decal to a new centre."""
    for a in r.d["areas"]:
        x, y, w, d = a["rect"]
        if a["kind"] == kind and abs(x + w / 2 - near[0]) <= radius and abs(y + d / 2 - near[1]) <= radius:
            a["rect"] = [to[0] - w // 2, to[1] - d // 2, w, d]
    for dc in r.d["decor"]:
        if dc["prop"] == kind and abs(dc["at"][0] - near[0]) <= radius and abs(dc["at"][1] - near[1]) <= radius:
            dc["at"] = [to[0], to[1]]


def lantern_text(where):
    return ("The lantern on the %s is furred with grey and cold as river stone. You wipe the grey away and a small "
            "flame catches inside." % where)


# ------------------------------------------------------------------ Stonewall Quarry
def lower_pit(R):
    """Lower Pit (3 tiers 200 · 100 · 0): falling rocks over the ropes and the floor; Riverstone on the ledges and the
    Jadeiron vein on the bottom tier. The catalogue pass already built the rim, the shelves and the cracked slab."""
    r = R["sq_lower_pit"]
    # Falling rocks (S17 strike): dust trickles from the pit wall, then a shadow marks where the rock lands. Strikes
    # land at floor height, so the floor and the lower rungs of the ropes are in the way and the ledges above are not.
    if "falling_rocks" not in r.d["hazards"]:
        r.d["hazards"].append("falling_rocks")
    ores = {o["item"]: o for o in of_type(r, "ore_vein")}
    at, h = on(r, "pit_shelf", 0.72)
    put(ores["riverstone"], at[0], at[1], h, "pit_shelf")
    at, h = on(r, "pit_rim_east", 0.6)
    put(ores["copper_ore"], at[0], at[1], h, "pit_rim_east")
    put(ores["jadeiron"], 700, 900)        # the bottom tier, out on the pit floor


def collapsed_tunnel(R):
    """Collapsed Tunnel (secret, 0 · rubble 40-80): a rubble heap with the shard vein behind it, and a cracked wall
    that a strong enough Body breaks open onto a second seam."""
    W = _w()
    all_of, flag = W.all_of, W.flag
    r = R["sq_collapsed_tunnel"]
    # The rubble heap: a low block to step on, a high one behind it; the shard vein waits behind them at the back wall.
    r.solid("rubble_heap_low", [870, 730, 80, 50], 40, kind="rubble")
    r.solid("rubble_heap_high", [940, 690, 90, 50], 80, kind="rubble")
    shard = next(o for o in of_type(r, "ore_vein") if o["item"] == "spirit_stone_shard")
    put(shard, 985, 660)
    # The cracked wall (S10: Body breaks cracked walls, threshold per object). Break it once and the seam behind it
    # can be mined like any vein.
    wall_flag = "tunnel_wall_broken"
    r.obj("cracked_wall", "inspect", [1175, 662], prop="rock_large", label="Cracked Wall",
          text="You set your shoulder to the cracked wall. It gives with a groan, and behind it a seam of Spirit Stone glitters.",
          requires=all_of({"kind": "attribute_at_least", "attribute": "body", "value": 20}),
          locked_text="The wall is cracked through and something glitters behind it. It would take a stronger body to "
                      "break it (Body 20).",
          set_flag=wall_flag, hidden_if=all_of(flag(wall_flag)))
    r.ore("spirit_stone_shard", [1175, 662], oid="ore_wall_seam", visible_if=all_of(flag(wall_flag)))


# ------------------------------------------------------------------ Reed Marsh and Greyreed
def marsh_edge(R):
    """Marsh Edge (0 · stilts 60-100): stilt decks across the reeds, reed bundles to step on, Reed Frogs hopping
    between the stilts and Willow Moss growing up on them."""
    r = R["rm_marsh_edge"]
    clear_tiers(r)
    decks = [("stilt_west", 260, 650, 200, 60), ("stilt_reeds", 580, 660, 200, 80), ("stilt_hut", 900, 640, 240, 100),
             ("stilt_pool", 1260, 650, 200, 60), ("stilt_nets", 1580, 660, 200, 80), ("stilt_lookout", 1900, 640, 240, 100),
             ("stilt_east", 2260, 650, 200, 60)]
    for sid, x, y, w, h in decks:
        r.surface(sid, [x, y, w, 90], h, kind="stilt")
    # A ladder on one side of every other deck (the kit's stilt deck); reed bundles (40) step up to the low ones.
    for sid, x in (("stilt_west", 290), ("stilt_hut", 1110), ("stilt_nets", 1610), ("stilt_lookout", 2110)):
        s = surf(r, sid)
        r.ladder(sid + "_ladder", x, s["rect"][1] + s["rect"][3], int(s["height"]), top=sid)
    r.solid("reed_bundle_a", [1300, 760, 60, 40], 40, kind="hay")
    r.solid("reed_bundle_b", [2290, 760, 60, 40], 40, kind="hay")
    r.solid("reed_bundle_c", [620, 770, 60, 40], 40, kind="hay")
    # Willow Moss up on the stilts; the ginseng stays down in the reeds.
    moss = [o for o in of_type(r, "herb_patch") if o["item"] == "willow_moss"]
    place_on(r, moss[0], "stilt_hut", 0.3)
    place_on(r, moss[1], "stilt_lookout", 0.7)
    jars = of_type(r, "jar")
    place_on(r, jars[0], "stilt_reeds", 0.5)
    place_on(r, jars[1], "stilt_nets", 0.5)
    for o in jars[2:] + [h for h in of_type(r, "herb_patch") if not h.get("alt")]:
        if any(in_rect(o["at"], s["rect"]) for s in r.d["surfaces"] if s["id"].startswith("stilt_")):
            o["at"] = [o["at"][0] + 40, 790]      # out from under the decks, onto the open reeds
    # Reed Frogs (tier natives) live on the stilts and hop between them when roused (their jump reaches 156).
    frogs = next(sp for sp in r.d["spawns"] if sp["enemy"] == "reed_frog" and not sp.get("elite"))
    lv = frogs.get("level")
    frogs.update({"surface": "stilt_reeds", "max": 3})
    frogs["points"] = [on(r, "stilt_reeds", f)[0] for f in (0.25, 0.75)]
    r.spawn("reed_frog", [on(r, "stilt_nets", f)[0] for f in (0.25, 0.75)], 2, respawn=12, level=lv, surface="stilt_nets")
    authored(r)


def grey_pools(R):
    """Grey Pools (0 · log rafts 30 · lily pads): a deep grey pool with log rafts on it; the chest waits on a raft
    moored out in the middle, reached on the raft that loops round the pool; a lily pad throws you to a 200 ledge."""
    W = _w()
    all_of, realm = W.all_of, W.realm
    r = R["rm_grey_pools"]
    # The pool moves east of the first Hollow puddle and deepens to the front of the room, with a bay reaching back
    # toward the reeds: the moored raft in the middle is more than a running jump (176) from every bank.
    pool = [700, 740, 620, 220]
    bay = [840, 680, 340, 60]
    r.d["volumes"] = [v for v in r.d["volumes"] if v["id"] != "grey_pool"]
    r.d["areas"] = [a for a in r.d["areas"] if a["kind"] != "water"]
    r.deep_water("grey_pool", pool)
    r.deep_water("grey_pool_bay", bay)
    move_area(r, "hollow_puddle", (900, 770), (480, 790))
    move_area(r, "hollow_puddle", (1200, 900), (1480, 910))
    for sp in r.d["spawns"]:            # nothing spawns in the pool: its points move out to the east bank
        sp["points"] = [[1400 + 40 * i, p[1]] if in_rect(p, pool) else p for i, p in enumerate(sp["points"])]
    # Rafts: a log raft drifting up and down the east side, and the loop raft. The loop raft waits at the north bank,
    # poles out along the back of the pool, down its west side to the moored raft, and home.
    drop_surfaces(r, ["log_raft_a", "moored_raft"])
    r.surface("log_raft_a", [1170, 760, 140, 60], 30, kind="raft")
    r.mover("log_raft_a", [[0, 130, 0]], speed=30, wait_s=2.0)
    r.surface("log_raft_loop", [720, 745, 150, 60], 30, kind="raft")
    r.mover("log_raft_loop", [[0, 105, 0], [250, 105, 0], [250, 0, 0]], speed=40, wait_s=2.5, mode="loop")
    r.surface("moored_raft", [970, 904, 140, 52], 30, kind="raft", optional=True)
    put(obj(r, "chest_moored_raft"), 1040, 930, 30, "moored_raft")
    # The reed bank's rope, and the rope bridge the hamlet door hangs under.
    r.ladder("reed_bank_rope", 270, 700, 100, kind="rope", top="reed_bank")
    r.surface("hamlet_bridge", [1100, 630, 300, 70], 100, kind="rope_bridge")
    jars = of_type(r, "jar")
    for o in jars:
        if in_rect(o["at"], [pool[0], pool[1], pool[2] + 60, pool[3]]):
            o["at"] = [o["at"][0] + 520 if o["at"][0] < 1000 else o["at"][0] + 80, 930]
    place_on(r, jars[0], "reed_bank", 0.2)
    place_on(r, jars[3], "hamlet_bank", 0.5)
    herb = of_type(r, "herb_patch")[0]
    if in_rect(herb["at"], pool):
        put(herb, 1540, 930)
    # Greyreed opens to those strong enough for Grey Roofs (Heart Tempering 1): Elder Gao gives that quest in the
    # hamlet, and its lanterns are on the hamlet's roofs.
    door = next(p for p in r.d["portals"] if p["id"] == "hamlet")
    door["requires"] = all_of(realm("heart_tempering_1"))
    authored(r)


def hermit_stilt_house(R):
    """Hermit's Stilt House (0 · house 120): the house's deck at 120 over the pond, a ladder up to it. The hermit keeps
    to the foot of his ladder, where his quests (Qi Unfurling 5 and 8) are asked and handed in."""
    r = R["rm_hermit_stilt_house"]
    # The deck runs in front of the house at the height of the porch in its art (117 over the ground line).
    r.surface("stilt_house_deck", [560, 690, 380, 60], 120, kind="stilt")
    r.ladder("stilt_house_ladder", 578, 750, 120, top="stilt_house_deck")
    surf(r, "stilt_house")["optional"] = True        # the thatch, one jump above the deck: a view, not a tier
    # The raft poles across the pond under the deck.
    s = surf(r, "pond_raft")
    s["rect"] = [612, 766, 100, 60]
    s["height"] = 14
    r.obj("hermit_mat", "inspect", [700, 720], alt=120, surface="stilt_house_deck", prop="meditation_mat",
          text="The hermit's mat, worn thin. From up here you can see every otter in the pond, and every otter can see you.")
    r.obj("hermit_tea", "inspect", [860, 720], alt=120, surface="stilt_house_deck", prop="cooking_pot",
          text="A kettle of reed tea gone cold. \"Drink it cold. The otters drink it cold.\"")
    authored(r)


def hamlet_square(R):
    """Hamlet Square (Greyreed, 0 · grey roofs 88 / 176): a roof chain from the grey hall (88) over the two homes to
    the granary (176); the well; the grey lanterns on the two grey roofs that Grey Roofs asks you to cleanse."""
    W = _w()
    all_of, flag, qactive = W.all_of, W.flag, W.qactive
    r = R["gh_hamlet_square"]
    # The hall and the granary: painted buildings scaled to the built tiers (as the Ferry's hall and inn are).
    r.painted("grey_hall", "hall", 935, 350, 110, 88, front=690)
    r.painted("grey_granary", "two_storey", 1800, 240, 120, 176, front=690)
    r.ladder("grey_granary_ladder", 1860, 690, 176, top="grey_granary")
    r.ladder("hamlet_house_a_ladder", 500, 690, 124, top="hamlet_house_a")
    r.ladder("hamlet_house_b_ladder", 1400, 690, 158, top="hamlet_house_b")
    # The well is a block now (60), one hop below the hall's eaves.
    drop_decor(r, "well", near=(900, 700))
    r.solid("hamlet_well", [870, 700, 64, 40], 60, kind="well")
    obj(r, "well_cleanse")["at"] = [902, 762]
    obj(r, "shrine_gh")["at"] = [2250, 712]
    # Grey Roofs: a lantern on each grey roof, cold until cleansed. A lit one takes its place.
    for sid, where, frac in (("grey_hall", "hall roof", 0.75), ("grey_granary", "granary roof", 0.3)):
        at, h = on(r, sid, frac, dy=20)
        f = "grey_lantern_" + sid.split("_")[1]
        r.obj(f, "inspect", at, alt=h, surface=sid, prop="stone_lantern", label="Grey Lantern", text=lantern_text(where),
              set_flag=f, requires=all_of(qactive("grey_roofs")),
              locked_text="A lantern gone grey and cold. Elder Gao will know what it needs.",
              hidden_if=all_of(flag(f)))
        r.obj("lit_lantern_" + sid.split("_")[1], "inspect", at, alt=h, surface=sid, prop="lantern_post",
              text="The lantern burns warm again. Below it the roof tiles have their colour back.", visible_if=all_of(flag(f)))
    authored(r)


# ------------------------------------------------------------------ Bamboo Grove and Crane Falls
def thicket_heart(R):
    """Thicket Heart (0 · canopy 100 / 200): canopy decks on vines across the thicket, with beast nests up in the
    canopy whose eggs you can take from Heart Tempering 5 (Spirit Eggs)."""
    W = _w()
    all_of, flag, unlock = W.all_of, W.flag, W.unlock
    r = R["bg_thicket_heart"]
    clear_tiers(r)
    # "route_2" keeps the name the rare-herb pass plants the hundred-year Ember Pepper on (world.rare_herbs).
    decks = [("canopy_west", 200, 630, 100), ("canopy_high_west", 560, 620, 200), ("canopy_mid", 920, 630, 100),
             ("route_2", 1280, 620, 200), ("canopy_east", 1640, 630, 100), ("canopy_high_east", 2000, 620, 200)]
    for sid, x, y, h in decks:
        r.surface(sid, [x, y, 260, 70], h, kind="canopy")
    for sid, x in (("canopy_west", 330), ("canopy_mid", 1050), ("canopy_east", 1770), ("canopy_high_west", 690),
                   ("canopy_high_east", 2200)):
        s = surf(r, sid)
        r.ladder(sid + "_vine", x, s["rect"][1] + s["rect"][3], int(s["height"]), kind="vine", top=sid)
    # Beast nests up in the canopy. The eggs keep warm there until you know how to raise one (Spirit Eggs, Heart
    # Tempering 5); each nest gives one egg.
    drop_decor(r, "beast_nest", near=(1500, 700))
    for i, sid in enumerate(("canopy_high_west", "canopy_high_east")):
        at, h = on(r, sid, 0.3 if i == 0 else 0.7)
        r.decor("beast_nest", at, alt=h)
        f = "thicket_nest_%d" % i
        r.obj("beast_nest_%d" % i, "pickup", [at[0], at[1] + 2], alt=h, surface=sid, item="spirit_egg", count=1, prop="none",
              label="Beast Nest", requires=all_of(unlock("spirit_eggs")),
              locked_text="A nest in the canopy, still warm. You would not know how to keep an egg alive yet (Spirit Eggs, "
                          "Heart Tempering 5).",
              set_flag=f, hidden_if=all_of(flag(f)))
    herbs = [o for o in of_type(r, "herb_patch") if not o.get("rare")]
    place_on(r, herbs[0], "canopy_east", 0.5)
    jars = of_type(r, "jar")
    place_on(r, jars[0], "canopy_west", 0.2)
    place_on(r, jars[1], "canopy_mid", 0.5)
    for c_ in of_type(r, "chest"):
        place_on(r, c_, "canopy_high_east", 0.25)
    authored(r)


def falls_pool(R):
    """Falls Pool (0 · rocks 60-100 · waterfall updraft): the pool is shallow round its rim and deep either side of the
    channel that leads behind the falls; stepping rocks cross it, and the Mist Lotus grows on the high rock."""
    r = R["cf_falls_pool"]
    r.d["areas"] = [a for a in r.d["areas"] if a["kind"] != "water"]
    r.area("shallows", [880, 800, 760, 40])                   # the rim, all along the back of the pool
    r.area("shallows", [880, 840, 80, 120])
    r.area("shallows", [1210, 840, 90, 120])                  # the channel behind the falls (its portal is here)
    r.area("shallows", [1560, 840, 80, 120])
    deep = [[960, 840, 250, 120], [1300, 840, 260, 120]]
    for i, rect in enumerate(deep):
        r.deep_water("falls_deep_%d" % i, rect)
    r.solid("falls_rock_west", [895, 875, 60, 44], 60, kind="rock")
    r.solid("falls_rock_mid", [1020, 885, 70, 44], 80, kind="rock")
    r.surface("lotus_rock", [1110, 858, 100, 64], 100, kind="rock_ledge")
    r.solid("falls_rock_east", [1340, 885, 70, 44], 80, kind="rock")
    r.solid("falls_rock_far", [1460, 875, 60, 44], 60, kind="rock")
    lotus = next(o for o in of_type(r, "herb_patch") if not o.get("rare"))
    place_on(r, lotus, "lotus_rock", 0.5)
    # The rock shelf at 100 below the chest ledge (a rope up; a jump on to the ledge).
    r.surface("falls_step", [480, 640, 160, 70], 100, kind="rock_ledge")
    r.ladder("falls_step_rope", 560, 710, 100, kind="rope", top="falls_step")
    # The spray lifts a glider (Leaf on the Wind) past the chest ledge.
    for v in r.d["volumes"]:
        if v["id"] == "falls_spray":
            v["alt"] = [0, 280]
    authored(r)


# ------------------------------------------------------------------ Cleansing Peak
def pilgrim_stairs(R):
    """Pilgrim Stairs (0 -> 80 -> 160 -> 240 by depth stairs · cliff shortcuts 100): the long stair climbs into the
    mountain in three flights with a landing after each; Stone Guardians keep the landings; ledges at 100 either side
    let a climber skip the first flight and landing."""
    r = R["cp_pilgrim_stairs"]
    clear_tiers(r)
    x0, x1 = 1236, 1536               # the stair; the ground either side is cut back to it (the stair is a wall)
    g = surf(r, "ground")
    g["rect"] = [0, 620, x0, 340]
    r.d["surfaces"].insert(0, {"id": "ground_front", "rect": [x0, 900, x1 - x0, 60], "height": 0, "kind": "ground",
                               "stratum": "ground", "open_edges": False})
    r.surface("ground_east", [x1, 620, 2560 - x1, 340], 0, kind="ground", stratum="ground", open_edges=False)
    w = x1 - x0
    for sid, y, d, top, rise in (("stair_flight_1", 800, 100, 80, 80), ("stair_flight_2", 680, 60, 160, 80),
                                 ("stair_flight_3", 560, 60, 240, 80)):
        r.surface(sid, [x0, y, w, d], top, kind="stairs", stratum="ground", rise=-rise, rise_axis="y", open_edges=False)
    for sid, y, d, h in (("landing_80", 740, 60, 80), ("landing_160", 620, 60, 160), ("landing_240", 480, 80, 240)):
        r.surface(sid, [x0, y, w, d], h, kind="ground", stratum="ground", open_edges=False)
    # Cliff shortcuts at 100 beside the second landing (skip the first flight), each with a boulder to step from, and
    # cliff ledges at 200 beyond them.
    r.surface("shortcut_west", [x0 - 200, 610, 200, 70], 100, kind="rock_ledge")
    r.surface("shortcut_east", [x1, 610, 200, 70], 100, kind="rock_ledge")
    r.solid("shortcut_west_boulder", [x0 - 150, 690, 70, 50], 60, kind="rock")
    r.solid("shortcut_east_boulder", [x1 + 80, 690, 70, 50], 60, kind="rock")
    r.surface("cliff_west", [x0 - 536, 620, 240, 70], 200, kind="rock_ledge")
    r.surface("cliff_east", [x1 + 294, 620, 240, 70], 200, kind="rock_ledge")
    r.ladder("cliff_west_rope", x0 - 416, 690, 200, kind="rope", top="cliff_west")
    r.ladder("cliff_east_rope", x1 + 414, 690, 200, kind="rope", top="cliff_east")
    # Stone Guardians: the road's watch (fought on the way up), and one on each landing.
    sg = next(sp for sp in r.d["spawns"] if sp["enemy"] == "stone_guardian")
    lv = sg.get("level")
    sg.update({"points": [[720, 860], [820, 780], [940, 900], [1060, 820]], "max": 3})
    for sid in ("landing_80", "landing_160", "landing_240"):
        r.spawn("stone_guardian", [on(r, sid, 0.5)[0]], 1, respawn=30, level=lv, surface=sid)
    brk = [o for o in r.d["objects"] if o["type"] in ("jar", "crate")]
    place_on(r, brk[1], "landing_80", 0.2)
    put(brk[0], 730, 700)
    put(brk[2], 2158, 720)
    authored(r)


def cleansing_summit(R):
    """Cleansing Summit (0 · pillars 60 / 120): stone pillars stand round the rite circle."""
    r = R["cp_cleansing_summit"]
    clear_tiers(r)
    for i, (x, y, top) in enumerate(((420, 770, 120), (618, 716, 60), (816, 770, 120), (470, 900, 60), (766, 900, 60))):
        r.solid("rite_pillar_%d" % i, [x, y, 44, 44], top, kind="pillar")
    authored(r)


# ------------------------------------------------------------------ Deepwater Bend and Whitewater Gorge
def bend_shore(R):
    """Bend Shore (0 · docks 60 · boats): docks run out over the deep bend of the river; a ferry boat plies between
    them, stepping stones cross the next stretch, and the Riverreed Ginseng grows on the roof of the sampan moored at
    the west dock (world.rare_herbs plants it on "sampan_roof")."""
    r = R["dw_bend_shore"]
    clear_tiers(r)
    river = [620, 860, 1340, 100]
    r.d["areas"] = [a for a in r.d["areas"] if a["kind"] != "shallows"]
    r.d["volumes"] = [v for v in r.d.get("volumes", []) if v["kind"] != "water_shallow"]
    r.deep_water("bend_river", river)
    r.area("shallows", [440, 860, 180, 100])
    r.area("shallows", [1960, 860, 200, 100])
    dry_spawns(r, [river], y_to=820)
    for sid, x in (("dock_west", 560), ("dock_mid", 1040), ("dock_east", 1500)):
        r.surface(sid, [x, 770, 220 if sid == "dock_mid" else 240, 110], 60, kind="stilt")
    r.ladder("dock_west_ladder", 578, 880, 60, top="dock_west")
    r.solid("dock_mid_crate", [1110, 720, 50, 44], 40, kind="crate")
    r.solid("dock_east_crate", [1680, 720, 50, 44], 40, kind="crate")
    # The moored sampan: its hull at 40 beside the west dock, its roof at 88 (the rare root and a chest up there).
    r.surface("moored_sampan", [820, 882, 200, 64], 40, kind="raft", optional=True)
    r.surface("sampan_roof", [850, 872, 170, 60], 88, kind="deck")
    W = _w()
    r.chest([870, 900], loot=W._zone_chest(r), level=r.d["level_range"][1], alt=88, surface="sampan_roof", oid="chest_sampan")
    # The ferry boat plies the stretch between the middle and east docks; stepping stones cross behind it.
    r.surface("ferry_boat", [1290, 900, 180, 60], 40, kind="raft")
    r.mover("ferry_boat", [[380, 0, 0]], speed=50, wait_s=2.5)
    for i, (x, top) in enumerate(((1290, 40), (1370, 60), (1450, 40))):
        r.solid("bend_stone_%d" % i, [x, 862, 50, 34], top, kind="rock")
    for i, (x, top) in enumerate(((1790, 40), (1880, 60))):
        r.solid("bend_stone_far_%d" % i, [x, 875, 56, 40], top, kind="rock")
    # The fishing spot at the end of the east dock.
    fish = of_type(r, "fishing_spot")[0]
    put(fish, 1690, 868, 60, "dock_east")
    jars = of_type(r, "jar")
    for o in jars:
        if in_rect(o["at"], river):
            o["at"] = [o["at"][0], 800]
    place_on(r, jars[0], "dock_west", 0.3)
    place_on(r, jars[1], "dock_east", 0.4)
    for o in of_type(r, "herb_patch"):
        if in_rect(o["at"], river):
            put(o, o["at"][0], 800)
    authored(r)


def rapids_terraces(R):
    """Rapids Terraces (0 · stepping stones 40-80 · current): a deep, fast stretch of the rapids with stepping stones
    across it and the salmon fishing spot on the big stone in the middle. The verticality pass keeps the terraces."""
    r = R["wg_rapids_terraces"]
    deep = [2240, 880, 860, 80]
    for a in r.d["areas"]:
        if a["kind"] == "shallows":
            a["rect"] = [600, 880, deep[0] - 600, 80]
    r.d["volumes"] = [v for v in r.d.get("volumes", []) if v["kind"] != "water_shallow"]
    r.volume("water_shallow", [600, 880, deep[0] - 600, 80], alt=[-50, 10])
    r.area("shallows", [deep[0] + deep[2], 880, 100, 80], current=-60)
    r.deep_water("rapids_deep", deep)
    r.area("current", deep, current=-100)
    r.volume("current", deep, alt=[-100, 10], push=[-120, 0], vid="rapids_current")
    stones = [(2262, 890, 40), (2380, 886, 60), (2500, 892, 80), (2760, 890, 40), (2880, 886, 60), (3000, 890, 40)]
    for i, (x, y, top) in enumerate(stones):
        r.solid("rapids_stone_%d" % i, [x, y, 60, 40], top, kind="rock")
    r.solid("salmon_stone", [2620, 884, 90, 56], 60, kind="rock")
    put(of_type(r, "fishing_spot")[0], 2665, 912, 60)
    dry_spawns(r, [deep])


def waterfall_cave(R):
    """Waterfall Cave (secret, 0 · 100 · 200): wet ledges up the back of the cave; the Mist Lotus, the Spirit Stone
    shard vein and Lu's journal page are up on them."""
    r = R["wg_waterfall_cave"]
    clear_tiers(r)
    r.surface("cave_ledge_low", [360, 640, 260, 70], 100, kind="rock_ledge")
    r.surface("cave_ledge_high", [700, 600, 240, 70], 200, kind="rock_ledge")
    r.surface("cave_ledge_east", [1000, 640, 220, 70], 100, kind="rock_ledge")
    r.ladder("cave_ledge_low_rope", 480, 710, 100, kind="rope", top="cave_ledge_low")
    r.ladder("cave_ledge_east_rope", 1110, 710, 100, kind="rope", top="cave_ledge_east")
    r.area("shallows", [420, 880, 860, 80])               # the falls' pool reaches into the cave
    r.decor("waterfall", [1180, 700], layer="back")
    at, h = on(r, "cave_ledge_low", 0.35)
    r.herb("mist_lotus", at, oid="cave_lotus", alt=h, surface="cave_ledge_low")
    at, h = on(r, "cave_ledge_east", 0.55)
    r.ore("spirit_stone_shard", at, oid="cave_shard_vein", alt=h, surface="cave_ledge_east")
    place_on(r, obj(r, "journal_cave"), "cave_ledge_high", 0.3)
    place_on(r, obj(r, "chest_1"), "cave_ledge_high", 0.75)
    obj(r, "cave_inner_cache")["at"] = [1160, 760]        # it stood outside the room (x 1700 in a 1280 room)
    authored(r)


# ------------------------------------------------------------------ Crane Cliffs
def updraft_column(r, vid, x, y, w, d, top):
    """An updraft column (S43): a body falling, gliding or flying inside it rises toward +220 up to `top`."""
    return r.volume("updraft", [x, y, w, d], alt=[0, top], vid=vid)


def cliff_faces(R):
    """Cliff Faces (0 · ledges to 600 · updraft columns): the cliff ledges at 200 and 300, and isolated crags at 400,
    500 and 600 above them, each beside an updraft column that lifts you to it (flight holds at 340)."""
    W = _w()
    r = R["cc_cliff_faces"]
    clear_tiers(r)
    for sid, rect, h in (("ledge_0", [600, 640, 280, 70], 200), ("ledge_1", [1300, 620, 280, 70], 300),
                         ("ledge_2", [2060, 630, 280, 70], 200), ("ledge_3", [3160, 640, 280, 70], 200)):
        r.surface(sid, rect, h, kind="rock_ledge")
    for sid, x in (("ledge_0", 740), ("ledge_2", 2200), ("ledge_3", 3300)):
        r.ladder(sid + "_rope", x, surf(r, sid)["rect"][1] + 70, 200, kind="rope", top=sid)
    r.surface("ledge_low", [960, 640, 220, 70], 100, kind="rock_ledge")
    r.ladder("ledge_low_rope", 1070, 710, 100, kind="rope", top="ledge_low")
    crags = [("crag_400", 1760, 600, 220, 400), ("crag_500", 2460, 590, 220, 500), ("crag_600", 2860, 580, 240, 600)]
    for sid, x, y, w, h in crags:
        r.surface(sid, [x, y, w, 70], h, kind="rock_ledge")
        updraft_column(r, "updraft_" + sid, x - 110, y, 110, 960 - y, h + 60)
    r.chest([2980, 615], loot="chest_dungeon", level=r.d["level_range"][1], alt=600, surface="crag_600", oid="chest_crag_600")
    herb = of_type(r, "herb_patch")[0]
    place_on(r, herb, "crag_400", 0.6)
    ore = of_type(r, "ore_vein")[0]
    place_on(r, ore, "ledge_1", 0.7)
    brk = [o for o in r.d["objects"] if o["type"] in ("jar", "crate")]
    place_on(r, brk[0], "ledge_0", 0.2)
    place_on(r, brk[1], "crag_500", 0.5)
    authored(r)


def sky_ledges(R):
    """Sky Ledges (400-900, flight only): cloud ledges climbing to 900, each over an updraft column; the Cloudtop
    Orchids and Cloudsteel veins are up on them, and a chest crowns the 900 cloud."""
    W = _w()
    r = R["cc_sky_ledges"]
    clear_tiers(r)
    # "ledge_1" and "ledge_2" keep the names the rare-herb pass uses (the rare orchid, and the second orchid).
    clouds = [("ledge_0", 360, 630, 240, 400), ("ledge_1", 760, 620, 260, 500), ("ledge_2", 1180, 610, 260, 600),
              ("cloud_700", 1600, 600, 240, 700), ("cloud_800", 1980, 590, 240, 800), ("cloud_900", 2320, 580, 200, 900)]
    for sid, x, y, w, h in clouds:
        r.surface(sid, [x, y, w, 70], h, kind="cloud")
        updraft_column(r, "updraft_" + sid, x - 100, y, 100, 960 - y, h + 60)
    # The lowest cloud drifts to and fro past its column (a mover: nothing is left lying on it).
    r.mover("ledge_0", [[140, 0, 0]], speed=30, wait_s=3.0)
    # The camera rises with the clouds (S43 rule 13: a room gives its camera bounds).
    r.d["camera"] = {"y_min": -420}
    herbs = [o for o in of_type(r, "herb_patch") if not o.get("rare")]
    place_on(r, herbs[0], "cloud_700", 0.2)
    ore = of_type(r, "ore_vein")[0]
    place_on(r, ore, "cloud_700", 0.5)
    at, h = on(r, "cloud_800", 0.35)
    r.ore("cloudsteel_ore", at, oid="ore_cloudsteel_high", alt=h, surface="cloud_800")
    brk = [o for o in r.d["objects"] if o["type"] in ("jar", "crate")]
    place_on(r, brk[0], "cloud_700", 0.8)
    place_on(r, brk[1], "cloud_800", 0.8)
    r.chest(on(r, "cloud_900", 0.5)[0], loot="chest_dungeon", level=r.d["level_range"][1], alt=900, surface="cloud_900",
            oid="chest_cloud_900")
    authored(r)


def run(rooms):
    lower_pit(rooms)
    collapsed_tunnel(rooms)
    marsh_edge(rooms)
    grey_pools(rooms)
    hermit_stilt_house(rooms)
    hamlet_square(rooms)
    thicket_heart(rooms)
    falls_pool(rooms)
    pilgrim_stairs(rooms)
    cleansing_summit(rooms)
    bend_shore(rooms)
    rapids_terraces(rooms)
    waterfall_cave(rooms)
    cliff_faces(rooms)
    sky_ledges(rooms)
