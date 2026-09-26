"""Build Prompt v2, Part 8: the room verticality catalogue, row by row.

Each function shapes the rooms of one region to their catalogue rows: tiers at the catalogue's heights,
the pieces named (ladders, ropes, blocks, rafts, lookouts), and what is up there. A shaped room is marked
vertical="authored", so the generic movement and verticality passes leave it alone; the room lint
(tools/data/room_lint.py) still checks it.

Runs after the rooms are built and before the movement pass.
"""


def _w():
    import world
    return world


def authored(r):
    r.d["vertical"] = "authored"


def drop_decor(r, prop, near=None, radius=60):
    """Remove a decor prop (it becomes a block or is replaced by a tier)."""
    keep = []
    for d in r.d["decor"]:
        if d["prop"] == prop and (near is None or abs(d["at"][0] - near[0]) + abs(d["at"][1] - near[1]) <= radius):
            continue
        keep.append(d)
    r.d["decor"] = keep


def obj(r, oid):
    return next(o for o in r.d["objects"] if o["id"] == oid)


def surf(r, sid):
    return next(s for s in r.d["surfaces"] if s["id"] == sid)


def obj_near(r, otype, x, y=None):
    """The object of a type nearest a point (generated objects are numbered by build order)."""
    cands = [o for o in r.d["objects"] if o["type"] == otype]
    return min(cands, key=lambda o: abs(o["at"][0] - x) + (abs(o["at"][1] - y) if y is not None else 0))


def clear_tiers(r, keep=()):
    """Drop a room's raised surfaces (all but `keep`) and the climbables to them; whatever stood on them
    comes down to the ground behind, for the passes to lift again."""
    gone = {x["id"] for x in r.d["surfaces"] if x.get("stratum") == "platform" and x["id"] not in keep}
    for o in r.d["objects"]:
        if float(o.get("alt", 0)) > 0 and (o.get("surface") in gone or o.get("surface") is None):
            o["alt"] = 0
            o.pop("surface", None)
    r.d["surfaces"] = [x for x in r.d["surfaces"] if x["id"] not in gone]
    r.d["climbables"] = [c for c in r.d.get("climbables", []) if c.get("top") not in gone and c.get("bottom") not in gone]
    r.d["movers"] = [m for m in r.d.get("movers", []) if m["surface"] not in gone]


def later_chest(r, sid, x, y, alt, art):
    W = _w()
    return r.chest([x, y], loot=W._zone_chest(r), level=max(1, r.d["level_range"][1]), alt=alt, surface=sid, oid="chest_" + sid)


# ------------------------------------------------------------------ Lotus Ferry and the Prologue
def lotus_ferry(R):
    W = _w()
    all_of, qactive, qdone, flag = W.all_of, W.qactive, W.qdone, W.flag
    after_kite = all_of(qdone("the_runaway_kite"))

    # Fisher's Hut: a loft at 88, seen before Jump exists; its ladder opens after The Runaway Kite.
    r = R["lf_fishers_hut"]
    r.surface("loft", [860, 580, 300, 70], 88, kind="balcony")
    r.ladder("loft_ladder", 900, 650, 88, top="loft", requires=after_kite,
             locked_text="The loft ladder wobbles. Aunt Ping says: after you've learned to land on your feet.")
    r.obj("lu_float", "inspect", [1040, 612], alt=88, prop="driftwood",
          text="Lu's old cork float, painted red and white a long time ago. Someone kept it very carefully.",
          effects=[{"kind": "codex", "entry": "lu_float"}])
    # Shown once the ladder holds: a glowing fourth tea in the prologue muddled Aunt Ping's "three teas".
    r.obj("tea_loft", "pickup", [1120, 612], alt=88, item="herbal_tea", count=1, prop="none", label="Herbal Tea",
          visible_if=after_kite, hidden_if=all_of(flag("tea_loft")), set_flag="tea_loft")
    authored(r)

    # Lotus Ferry Village: Home Lane blocks and roofs, the Village Square roof chain and the Ferry Docks lookout.
    r = R["lf_village"]
    # Home Lane: crates (40 in front of 80), a fence you walk around, the well, ladders to both cottage roofs.
    drop_decor(r, "well", near=(700, 700))
    drop_decor(r, "fence_wood", near=(140, 668))
    r.solid("lane_crate_low", [600, 748, 50, 44], 40, kind="crate")
    r.solid("lane_crate_high", [604, 704, 50, 42], 80, kind="crate")
    r.solid("lane_well", [668, 660, 64, 40], 60, kind="well")
    r.solid("lane_fence", [760, 800, 150, 24], 60, kind="fence")
    r.ladder("hut_ladder", 300, 690, 124, top="fishers_hut")
    r.ladder("granny_ladder", 1120, 690, 128, top="granny_hut")
    r.obj("pings_ladle", "pickup", [500, 632], alt=124, item="aunt_pings_ladle", count=1, prop="cooking_pot", label="Aunt Ping's Ladle",
          requires=all_of(qactive("the_lost_ladle")), hidden_if=all_of(qdone("the_lost_ladle")),
          locked_text="Something glints on the roof.")
    # Village Square: the hall ladder, the store roof one jump above the hall, a stall awning below the inn.
    r.ladder("store_ladder", 1860, 690, 168, top="old_ma_store")
    drop_decor(r, "market_stall", near=(2240, 770))
    r.surface("stall_awning", [2170, 700, 180, 70], 88, kind="awning")
    r.solid("stall_counter", [2200, 780, 120, 40], 40, kind="stall")
    # Ferry Docks: stacked crates, the moored boat's deck at 60 and the mast lookout at 150; the tower's ladder.
    r.solid("dock_crate_low", [2840, 740, 50, 44], 40, kind="crate")
    r.solid("dock_crate_high", [2846, 698, 50, 42], 80, kind="crate")
    r.surface("boat_deck", [3350, 896, 150, 62], 60, kind="deck")
    r.surface("mast_lookout", [3398, 856, 80, 60], 150, kind="stilt")
    r.ladder("mast_ladder", 3440, 916, 150, depth=40, bottom="boat_deck", top="mast_lookout", base=60)
    r.breakable([3440, 884], kind="jar")
    r.d["objects"][-1].update({"alt": 150, "id": "gull_nest"})
    # Net-drying and shed decks on stilts carry the roof route from the inn down to the boat.
    r.surface("net_deck", [2700, 650, 200, 64], 100, kind="stilt")
    r.ladder("net_deck_ladder", 2720, 714, 100, top="net_deck")
    r.surface("shed_deck", [3000, 650, 220, 64], 100, kind="stilt")
    r.ladder("shed_deck_ladder", 3190, 714, 100, top="shed_deck")
    r.ladder("tower_ladder", 3620, 690, 312, top="watch_tower")
    surf(r, "watch_tower")["optional"] = True   # the Race to the Tower finish: an optional climb
    obj(r, "tower_bell").update({"at": [3660, 656], "alt": 312})
    authored(r)

    # Old Ma's Store: shelves (blocks 110), a storeroom loft (after The Runaway Kite) with Straw Sandals.
    r = R["lf_old_ma_store"]
    drop_decor(r, "shelf")
    r.solid("shelf_west", [250, 656, 100, 40], 110, kind="table")
    r.solid("shelf_east", [930, 656, 100, 40], 110, kind="table")
    r.surface("storeroom_loft", [700, 580, 360, 70], 88, kind="balcony")
    r.ladder("storeroom_ladder", 740, 650, 88, top="storeroom_loft", requires=after_kite,
             locked_text="Old Ma: \"The storeroom? Learn to jump first, then we'll talk.\"")
    r.obj("sandals_loft", "pickup", [960, 612], alt=88, item="straw_sandals", count=1, prop="storage_chest", label="Straw Sandals",
          hidden_if=all_of(flag("sandals_loft")), set_flag="sandals_loft")
    r.obj("old_net_floor", "pickup", [430, 820], item="old_net", count=1, prop="none", label="Old Net",
          requires=all_of(qactive("mas_delivery")), hidden_if=all_of(flag("old_net_found")), set_flag="old_net_found",
          locked_text="A tangle of old net under the shelf.")
    authored(r)

    # Granny Liu's Herb Hut: a drying mezzanine at 88 with herb jars and a Willow Moss bundle.
    r = R["lf_granny_liu_hut"]
    r.surface("drying_mezzanine", [120, 580, 330, 70], 88, kind="balcony")
    r.ladder("mezzanine_ladder", 420, 650, 88, top="drying_mezzanine")
    for x in (170, 250):
        r.breakable([x, 612], kind="jar")
        r.d["objects"][-1]["alt"] = 88
    r.obj("moss_bundle", "pickup", [340, 612], alt=88, item="willow_moss", count=2, prop="willow_moss_patch", label="Willow Moss",
          hidden_if=all_of(flag("moss_bundle")), set_flag="moss_bundle")
    authored(r)

    # Night in the village: the same roofs are the safe tier; Hollow Minnows cannot jump.
    r = R["lf_village_night"]
    r.ladder("hut_ladder_n", 300, 690, 124, top="fishers_hut_n")
    r.ladder("granny_ladder_n", 1120, 690, 128, top="granny_hut_n")
    r.ladder("store_ladder_n", 1860, 690, 168, top="old_ma_store_n")
    r.ladder("hall_ladder_n", 1962, 690, 88, top="village_hall_n")
    r.solid("night_crate_hut", [610, 704, 50, 44], 80, kind="crate")
    r.solid("night_crate_granny", [770, 704, 50, 44], 80, kind="crate")
    authored(r)

    # Lu's Boat: the cabin roof at 88, a ladder, the meditation spot under the stars.
    r = R["lf_lu_boat"]
    r.surface("cabin_roof", [700, 626, 240, 70], 88, kind="deck")
    r.ladder("cabin_ladder", 720, 696, 88, depth=40, bottom="deck", top="cabin_roof")
    r.obj("star_mat", "inspect", [860, 660], alt=88, prop="meditation_mat",
          text="Up here the river is all stars. Sit, and let the Qi come to you.")
    authored(r)

    # Reed Shallows: drifting driftwood rafts, a stilt hut and stilt decks at 100, reed bundles and a rock.
    r = R["lf_reed_shallows"]
    for sid, path in (("driftwood_a", [[140, 0, 0]]), ("driftwood_b", [[-120, 0, 0]]), ("driftwood_c", [[160, 0, 0]])):
        s = surf(r, sid)
        s["rect"][3] = 60
        s["rect"][1] -= 14
        r.mover(sid, path, speed=26, wait_s=2.0)
    r.surface("stilt_deck_a", [1500, 650, 200, 64], 100, kind="stilt")
    r.surface("stilt_deck_b", [1810, 650, 180, 64], 100, kind="stilt")
    r.surface("stilt_hut", [2090, 646, 230, 70], 100, kind="stilt")
    r.ladder("stilt_ladder", 2130, 716, 100, top="stilt_hut")
    r.ladder("stilt_deck_ladder", 1540, 714, 100, top="stilt_deck_a")
    obj_near(r, "herb_patch", 2380).update({"at": [2260, 680], "alt": 100})
    r.solid("reed_bundle_a", [980, 700, 60, 40], 40, kind="hay")
    r.solid("reed_bundle_b", [1620, 820, 60, 40], 40, kind="hay")
    r.solid("snapper_rock", [2060, 800, 90, 60], 80, kind="rock")
    jars = [o for o in r.d["objects"] if o["type"] == "jar"]
    for o, (x, y, alt) in zip(jars[:2], [(1600, 680, 100), (1900, 680, 100)]):
        o["at"] = [x, y]
        o["alt"] = alt
    authored(r)


# ------------------------------------------------------------------ Willow Path, Stoneford and the sects
def willow_stoneford_sects(R):
    W = _w()
    all_of = W.all_of

    # Willow Path West: willow and pine branches at 100, a fallen log to jump; the chest sits on a pine top at 240,
    # +140 above the branches (later: double jump). A high willow crown at 200 stands well clear of it.
    r = R["wp_west"]
    for sid, x in (("willow_branch_a", 140), ("pine_branch", 520), ("willow_branch_b", 900), ("willow_branch_c", 1280)):
        r.surface(sid, [x, 620, 260, 70], 100, kind="tree_branch")
    r.surface("pine_top", [1640, 600, 220, 70], 240, kind="tree_branch", later="double_jump")
    later_chest(r, "pine_top", 1750, 635, 240, "double_jump")
    r.surface("willow_low", [1960, 650, 180, 70], 100, kind="tree_branch")
    r.surface("willow_crown", [2180, 620, 240, 70], 200, kind="tree_branch")
    r.solid("fallen_log", [1010, 800, 150, 44], 60, kind="log")

    # Willow Path East: the wandering merchant's cart (a block to stand on) by the wheel ruts.
    r = R["wp_east"]
    r.solid("merchant_cart", [1170, 760, 130, 50], 60, kind="cart")

    # Market Street: awnings at 88 between the shop roofs (158-168), the bell tower at 312 with a copy of the
    # notice board, and a Spirit Stone shard lodged in the tea house gutter.
    r = R["sf_market"]
    r.surface("awning_west", [790, 640, 220, 70], 88, kind="awning")
    r.surface("awning_east", [1520, 640, 220, 70], 88, kind="awning")
    r.surface("bell_tower", [2290, 622, 180, 68], 312, kind="roof", art="watch_tower")
    r.ladder("bell_tower_ladder", 2380, 690, 312, top="bell_tower")
    surf(r, "bell_tower")["optional"] = True   # a lookout by ladder, like the Ferry's watchtower
    r.obj("board_sf_tower", "notice_board", [2380, 652], alt=312)
    r.obj("gutter_shard", "pickup", [1300, 640], alt=158, item="spirit_stone_shard", count=1, prop="spirit_shard_vein",
          label="Spirit Stone Shard", hidden_if=all_of(W.flag("gutter_shard")), set_flag="gutter_shard")

    # Artisan Row: scaffolds at 90 and 180 with a ladder between them, ore crates on the planks; the workshop chimney
    # top at 330 is +150 above the high scaffold (later: double jump) and holds the tinkerer's lost gear.
    r = R["sf_artisan_row"]
    r.surface("scaffold_low", [640, 640, 220, 70], 90, kind="scaffold")
    r.surface("scaffold_high", [660, 570, 200, 70], 180, kind="scaffold")
    r.ladder("scaffold_ladder", 840, 710, 90, top="scaffold_low")
    r.ladder("scaffold_ladder_high", 700, 640, 180, depth=40, bottom="scaffold_low", top="scaffold_high", base=90)
    r.surface("workshop_chimney", [880, 560, 80, 60], 330, kind="chimney", later="double_jump")
    r.obj("tinkerers_gear", "pickup", [920, 590], alt=330, item="tinkerers_gear", count=1, prop="none", label="Tinkerer's Gear",
          hidden_if=all_of(W.flag("tinkerers_gear")), set_flag="tinkerers_gear")
    for x, y, alt in ((700, 675, 90), (780, 605, 180)):
        r.breakable([x, y], loot="jar_valley_low", kind="crate", level=2)
        r.d["objects"][-1].update({"alt": alt})

    # Stoneford Gate: the walltop walkway at 160 over the quarry road, climbed by stone steps (40, 80, 110) or from
    # the gatehouse roof; the old guard tower is an optional lookout by ladder.
    r = R["sf_gate"]
    r.surface("walltop", [530, 610, 480, 70], 160, kind="walltop")
    for i, (x, top) in enumerate(((820, 40), (880, 80), (940, 110))):
        r.solid("gate_step_%d" % i, [x, 690, 60, 50], top, kind="wall")
    surf(r, "guard_tower")["optional"] = True

    # Entry Trials. Jade: a roof climb 88 -> 176 -> 264 over two moving planks, with ladders as the fallback.
    # Cloud: ledges 100 -> 200 -> 300 joined by ropes, one of them crumbling. The bell (and the puppet) wait at the top.
    for s_ in ("jade", "cloud"):
        r = R["sf_trial_" + s_]
        clear_tiers(r)
        if s_ == "jade":
            r.surface("roof_1", [280, 640, 220, 70], 88, kind="balcony")
            r.surface("plank_1", [540, 660, 120, 60], 88, kind="deck")
            r.mover("plank_1", [[0, 0, 88]], speed=40, wait_s=1.2)
            r.surface("roof_2", [700, 630, 200, 70], 176, kind="balcony")
            r.surface("plank_2", [940, 650, 110, 60], 176, kind="deck")
            r.mover("plank_2", [[0, 0, 88]], speed=40, wait_s=1.2)
            r.surface("roof_3", [1080, 610, 170, 80], 264, kind="balcony")
            r.ladder("roof_1_ladder", 320, 710, 88, top="roof_1")
            r.ladder("roof_2_ladder", 860, 700, 176, top="roof_2")
            r.ladder("roof_3_ladder", 1210, 690, 264, top="roof_3")
            top_id, bell = "roof_3", [1160, 648, 264]
        else:
            r.surface("ledge_1", [300, 680, 220, 70], 100, kind="rock_ledge")
            r.surface("ledge_2", [300, 610, 220, 70], 200, kind="rock_ledge")
            r.ladder("ledge_2_rope", 460, 680, 200, depth=40, kind="rope", bottom="ledge_1", top="ledge_2", base=100)
            r.surface("crumbling_ledge", [560, 610, 160, 70], 200, kind="boards")
            r.volume("crumble", [560, 610, 160, 70], surface="crumbling_ledge", break_s=1.0, return_s=5.0, vid="trial_crumble")
            r.ladder("crumbling_ledge_rope", 640, 680, 200, kind="rope", top="crumbling_ledge")
            r.surface("ledge_3", [760, 590, 240, 70], 300, kind="rock_ledge")
            r.ladder("ledge_3_rope", 960, 660, 300, kind="rope", top="ledge_3")
            r.ladder("ledge_1_rope", 480, 750, 100, kind="rope", top="ledge_1")
            top_id, bell = "ledge_3", [880, 625, 300]
        obj(r, "trial_bell").update({"at": bell[:2], "alt": bell[2], "surface": top_id})
        authored(r)

    # Sword Court (Cloud): plum-blossom poles 60-110 (40 wide: an optional footwork drill) and pillar pairs 160 high,
    # 120 apart, for Wall-Step practice.
    r = R["cm_sword_court"]
    for i, (x, y, h) in enumerate(((1760, 800, 60), (1830, 770, 80), (1900, 805, 110), (1970, 775, 80), (2040, 800, 60))):
        r.surface("plum_pole_%d" % i, [x, y, 40, 40], h, kind="pole", optional=True)
    for i, x in enumerate((2200, 2360)):
        r.solid("sword_pillar_%d" % i, [x, 700, 40, 40], 160, kind="pillar")

    # Elder Sung's Peak: a ledge at 100, the west peak at 200 behind it (rope), a rope bridge at 200 to the far peak
    # at 300 where the Elder waits; ladders at both ends of the bridge.
    r = R["cm_elder_sung_peak"]
    clear_tiers(r)
    r.surface("west_ledge", [240, 650, 220, 70], 100, kind="rock_ledge")
    r.surface("west_peak", [280, 580, 220, 70], 200, kind="rock_ledge")
    r.ladder("west_peak_rope", 420, 650, 200, depth=40, kind="rope", bottom="west_ledge", top="west_peak", base=100)
    r.surface("peak_bridge", [500, 590, 400, 60], 200, kind="rope_bridge")
    r.ladder("peak_bridge_ladder_w", 560, 650, 200, top="peak_bridge")
    r.ladder("peak_bridge_ladder_e", 840, 650, 200, top="peak_bridge")
    r.surface("far_peak", [900, 560, 220, 80], 300, kind="rock_ledge")
    r.ladder("far_peak_rope", 1060, 640, 300, kind="rope", top="far_peak")
    obj(r, "npc_elder_sung").update({"at": [1000, 600], "alt": 300})

    # Libraries (both sects): floor 2 at 120 and floor 3 at 240, their ladders sealed by rank.
    for rid in ("ja_library", "cm_cloud_library"):
        r = R[rid]
        r.surface("library_floor_2", [120, 620, 420, 70], 120, kind="balcony", optional=True)
        r.surface("library_floor_3", [120, 550, 420, 70], 240, kind="balcony", optional=True)
        r.ladder("floor_2_ladder", 480, 690, 120, top="library_floor_2",
                 requires=all_of({"kind": "sect_rank_at_least", "rank": "outer_disciple"}),
                 locked_text="The second floor is for Outer Disciples and above.")
        r.ladder("floor_3_ladder", 180, 620, 240, depth=40, bottom="library_floor_2", top="library_floor_3", base=120,
                 requires=all_of({"kind": "sect_rank_at_least", "rank": "inner_disciple"}),
                 locked_text="The third floor is for Inner Disciples and above.")
        for i, (x, y, alt) in enumerate(((250, 650, 120), (400, 650, 120), (250, 580, 240), (400, 580, 240))):
            r.decor("scroll_rack", [x, y], layer="play", alt=alt)
        r.obj("floor_2_shelves", "inspect", [320, 655], alt=120, prop="none",
              text="Manuals of the middle grade, catalogued by element. Ask the librarian to borrow one.", open_page="library")
        r.obj("floor_3_shelves", "inspect", [320, 585], alt=240, prop="none",
              text="The sect's deeper arts. Even the dust here feels expensive.", open_page="library")


# ------------------------------------------------------------------ Fields, dungeons and secret places
def fields_and_dungeons(R):
    W = _w()
    all_of, flag = W.all_of, W.flag

    # Quarry Rim: scaffolds at 90 and 180 in a chain, a crane lift (0 <-> 180, trigger mover) beside the middle
    # scaffold, ore carts to stand on; copper veins on the scaffolds.
    r = R["sq_quarry_rim"]
    clear_tiers(r)
    for sid, x, y, h in (("scaffold_a", 300, 640, 90), ("scaffold_b", 520, 620, 180), ("scaffold_c", 860, 620, 180),
                         ("scaffold_d", 1220, 640, 90), ("scaffold_e", 1560, 620, 180)):
        r.surface(sid, [x, y, 220, 70], h, kind="scaffold")
    r.ladder("scaffold_a_ladder", 360, 710, 90, top="scaffold_a")
    r.ladder("scaffold_b_ladder", 660, 690, 180, top="scaffold_b")
    r.surface("crane_lift", [760, 700, 90, 60], 4, kind="deck")
    r.mover("crane_lift", [[0, 0, 176]], speed=60, wait_s=2.0, mode="trigger")
    r.solid("ore_cart_a", [1060, 800, 120, 60], 60, kind="cart")
    r.solid("ore_cart_b", [2000, 780, 120, 60], 60, kind="cart")
    for o, (x, y, alt, sid) in zip([o for o in r.d["objects"] if o["type"] == "ore_vein"][:2],
                                    ((400, 675, 90, "scaffold_a"), (1660, 655, 180, "scaffold_e"))):
        o.update({"at": [x, y], "alt": alt, "surface": sid})

    # Lower Pit: the west rim at 200 steps down to 100 and the floor; ropes to the rim; a cracked slab on the floor
    # breaks under a Plunge and gives up the Spirit Stone shard sealed beneath it.
    r = R["sq_lower_pit"]
    clear_tiers(r)
    r.surface("pit_rim", [140, 620, 300, 70], 200, kind="rock_ledge")
    r.surface("pit_shelf", [540, 630, 300, 70], 100, kind="rock_ledge")
    r.surface("pit_rim_east", [940, 620, 280, 70], 200, kind="rock_ledge")
    r.surface("pit_shelf_east", [1320, 640, 280, 70], 100, kind="rock_ledge")
    r.ladder("pit_rim_rope", 260, 690, 200, kind="rope", top="pit_rim")
    r.solid("cracked_slab", [1800, 760, 200, 100], 40, kind="slab", cracked=True)
    r.obj("pit_shard", "pickup", [1900, 810], item="spirit_stone_shard", count=3, prop="spirit_shard_vein", label="Spirit Stone Shards",
          hidden_if=all_of(flag("pit_shard")), set_flag="pit_shard")

    # Grey Pools: a pool of deep water with log rafts (30) drifting over it and a moored raft carrying a chest;
    # a lily pad throws you up to an optional ledge at 200.
    r = R["rm_grey_pools"]
    clear_tiers(r)
    r.surface("reed_bank", [140, 630, 260, 70], 100, kind="rock_ledge")
    r.surface("grey_crag", [500, 620, 240, 70], 200, kind="rock_ledge")
    r.surface("reed_bank_east", [840, 630, 260, 70], 100, kind="rock_ledge")
    r.surface("hamlet_bank", [1400, 630, 240, 70], 100, kind="rock_ledge")
    r.deep_water("grey_pool", [420, 760, 760, 170])
    for sp in r.d["spawns"]:   # nothing spawns in the pool: its points move to the east bank
        sp["points"] = [[1260 + 40 * i, p[1]] if 400 <= p[0] <= 1200 and p[1] >= 740 else p for i, p in enumerate(sp["points"])]
    r.surface("log_raft_a", [440, 790, 150, 60], 30, kind="raft")
    r.mover("log_raft_a", [[300, 0, 0]], speed=36, wait_s=1.5)
    r.surface("moored_raft", [900, 850, 160, 60], 30, kind="raft")
    r.chest([980, 880], loot=W._zone_chest(r), level=12, alt=30, surface="moored_raft", oid="chest_moored_raft")
    r.solid("lily_pad", [1900, 740, 80, 50], 10, kind="lily")
    r.volume("bounce", [1900, 740, 80, 50], alt=[0, 20], speed=700, vid="lily_bounce")
    r.surface("lily_ledge", [1860, 610, 220, 70], 200, kind="rock_ledge", optional=True)
    r.breakable([1960, 645], kind="jar", level=10)
    r.d["objects"][-1].update({"alt": 200, "surface": "lily_ledge"})

    # Sunken Causeway: broken causeway sections at 60 with 120 gaps (sprint them), an arch section at 100; a broken
    # pillar with a 300 top, +200 above the arch, holds jars (later: Wall-Step off the pillar and the arch wall).
    r = R["rm_sunken_causeway"]
    clear_tiers(r)
    for i, (x, w_, h) in enumerate(((140, 300, 60), (560, 300, 60), (980, 240, 100), (1340, 300, 60), (1760, 300, 60))):
        r.surface("causeway_%d" % i, [x, 660, w_, 80], h, kind="causeway")
    r.solid("broken_pillar", [2140, 640, 80, 60], 300, kind="stone_pillar", later="wall_step")
    r.solid("causeway_arch", [2340, 640, 40, 60], 160, kind="stone_pillar")
    for x in (2160, 2200):
        r.breakable([x, 670], kind="jar", level=10)
        r.d["objects"][-1].update({"alt": 300, "surface": "broken_pillar"})

    # Whispering Bamboo: bamboo platforms at 90 and 180, a bent bamboo that throws you to 233 (onto the 180 poles,
    # never the 330 top), and the chest on the 330 top, +150 above the 180 poles (later: double jump).
    r = R["bg_whispering_bamboo"]
    clear_tiers(r)
    for i, (x, y, h) in enumerate(((200, 650, 90), (430, 630, 180), (660, 650, 90), (890, 630, 180), (1120, 650, 90),
                                   (1350, 620, 180), (1800, 650, 90), (2030, 630, 180), (2260, 650, 90))):
        r.surface("bamboo_%d" % i, [x, y, 120, 60], h, kind="pole")
    r.surface("bamboo_top", [1560, 590, 100, 60], 330, kind="pole", later="double_jump")
    later_chest(r, "bamboo_top", 1610, 620, 330, "double_jump")
    r.solid("bent_bamboo", [1480, 720, 60, 40], 20, kind="bamboo")
    r.volume("bounce", [1480, 720, 60, 40], alt=[0, 30], speed=700, vid="bent_bamboo_bounce")
    for c in [c for c in r.d["objects"] if c["type"] == "chest" and c["id"] != "chest_bamboo_top"]:
        r.d["objects"].remove(c)

    # Caravan Road: a cliff ledge at 120 (ladder, or up from a broken cart), ledges to a rope bridge at 200 with
    # ladders at both ends and supply crates on it; broken carts along the road for cover.
    r = R["cr_caravan_road"]
    r.surface("cliff_ledge", [300, 610, 400, 80], 120, kind="rock_ledge")
    r.ladder("cliff_ledge_ladder", 380, 690, 120, top="cliff_ledge")
    r.solid("broken_cart_a", [560, 720, 120, 60], 60, kind="cart")
    r.surface("road_ledge", [820, 620, 260, 70], 100, kind="rock_ledge")
    r.surface("bridge_head_w", [1180, 610, 220, 70], 200, kind="rock_ledge")
    r.surface("caravan_bridge", [1400, 610, 500, 60], 200, kind="rope_bridge")
    r.ladder("caravan_bridge_ladder_w", 1440, 670, 200, top="caravan_bridge")
    r.ladder("caravan_bridge_ladder_e", 1860, 670, 200, top="caravan_bridge")
    r.surface("bridge_head_e", [1900, 610, 240, 70], 200, kind="rock_ledge")
    for x in (1560, 1720):
        r.breakable([x, 640], kind="crate", level=16, loot="jar_valley_mid")
        r.d["objects"][-1].update({"alt": 200, "surface": "caravan_bridge"})
    r.solid("broken_cart_b", [1100, 820, 120, 60], 60, kind="cart")
    r.solid("broken_cart_c", [2400, 780, 130, 60], 60, kind="cart")

    # Gorge Mouth: a rope bridge at 200 over the gorge between two cliffs, ladders at both ends.
    r = R["wg_gorge_mouth"]
    r.surface("gorge_step", [480, 640, 200, 70], 100, kind="rock_ledge")
    r.surface("gorge_cliff_w", [700, 610, 260, 80], 200, kind="rock_ledge")
    r.surface("gorge_bridge", [960, 610, 560, 60], 200, kind="rope_bridge")
    r.ladder("gorge_bridge_ladder_w", 1000, 670, 200, top="gorge_bridge")
    r.ladder("gorge_bridge_ladder_e", 1480, 670, 200, top="gorge_bridge")
    r.surface("gorge_cliff_e", [1520, 610, 260, 80], 200, kind="rock_ledge")

    # Boss Den: shelves at 88 carry "Big Toad" Tan's wine jars; break them from the shelf or with a Plunge.
    r = R["mh_boss_den"]
    for i, x in enumerate((300, 1100, 1900)):
        r.surface("wine_shelf_%d" % i, [x, 620, 300, 70], 88, kind="balcony")
        o = obj(r, "toad_wine_%d" % i)
        o.update({"at": [x + 150, 655], "alt": 88, "surface": "wine_shelf_%d" % i})

    # Abbot's Sanctum: the four small bells hang over platforms at 100 and 200; ring them all to silence the Abbot.
    r = R["ds_abbots_sanctum"]
    for i, (x, h) in enumerate(((420, 100), (1000, 200), (1580, 100), (2160, 200))):
        r.surface("bell_ledge_%d" % i, [x, 620, 220, 70], h, kind="rock_ledge")
        obj(r, "small_bell_%d" % i).update({"at": [x + 110, 655], "alt": h, "surface": "bell_ledge_%d" % i})

    # Collapsed Tunnel: rubble blocks (40, 80) and a wider shelf where the shard veins run.
    r = R["sq_collapsed_tunnel"]
    surf(r, "ledge_tunnel")["rect"] = [540, 626, 340, 70]
    r.solid("rubble_low", [300, 770, 80, 50], 40, kind="rubble")
    r.solid("rubble_high", [390, 740, 80, 60], 80, kind="rubble")

    # Behind the Falls: ledges at 100 and 200, then a Wall-Step shaft (walls 120 apart, no ledge inside) up to
    # a chest at 520, +320 above the 200 ledge (later: Wall-Step). Lu's journal page waits on the first ledge.
    r = R["cf_behind_falls"]
    clear_tiers(r)
    r.surface("falls_ledge_1", [300, 640, 240, 70], 100, kind="rock_ledge")
    r.surface("falls_ledge_2", [580, 600, 200, 70], 200, kind="rock_ledge")
    r.ladder("falls_ledge_2_rope", 700, 670, 200, kind="rope", top="falls_ledge_2")
    for i, x in enumerate((820, 980)):
        r.solid("shaft_wall_%d" % i, [x, 560, 40, 110], 520, kind="stone_pillar")
    r.surface("shaft_top", [820, 560, 200, 60], 520, kind="rock_ledge", later="wall_step")
    obj(r, "chest_1").update({"at": [920, 590], "alt": 520, "surface": "shaft_top"})
    obj(r, "journal_falls").update({"at": [420, 675], "alt": 100, "surface": "falls_ledge_1"})

    # Sect Grounds: its roofs come with its buildings (Part 8: "grows with your sect"); the room lint does not ask
    # a raised route of it.
    R["hv_sect_grounds"].d["vertical"] = "grows"


def run(R):
    lotus_ferry(R)
    willow_stoneford_sects(R)
    fields_and_dungeons(R)
