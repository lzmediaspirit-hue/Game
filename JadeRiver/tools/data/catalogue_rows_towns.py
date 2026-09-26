"""V9f3 · the Part 8 room verticality catalogue rows V2d left partial (towns). Runs after catalogue.run(ROOMS) and
before the movement and verticality passes (tools/data/world.py build()). Fill run(); keep to this group's rooms."""
from catalogue import authored, drop_decor, obj, surf


def _w():
    import world
    return world


# ------------------------------------------------------------------ helpers
def drop_surfaces(r, ids):
    """Remove surfaces (and the climbables and movers that serve them) by id."""
    ids = set(ids)
    r.d["surfaces"] = [s for s in r.d["surfaces"] if s["id"] not in ids]
    r.d["climbables"] = [c for c in r.d.get("climbables", []) if c.get("top") not in ids and c.get("bottom") not in ids]
    r.d["movers"] = [m for m in r.d.get("movers", []) if m["surface"] not in ids]


def depth_stairs(r, sid, x, y_back, w, depth, hi, lo=0):
    """Depth stairs (S43, ground stratum): `hi` at the back edge down to `lo` at the front edge, like the v0.3 rear
    stairs of the Pavilion Rooftops. (Room.stairs puts the back at 0 and the front below the ground.)"""
    return r.surface(sid, [x, y_back, w, depth], hi, kind="stairs", stratum="ground", rise=-(hi - lo), rise_axis="y",
                     open_edges=False)


def terrace(r, sid, rect, h):
    """A raised ground terrace (ground stratum): paved on top, a stone face down to the ground in front."""
    return r.surface(sid, rect, h, kind="ground", stratum="ground", open_edges=False)


def raised_door(r, pid, s, x, to, to_portal, label, door_dy=6, **kw):
    """A door on a raised surface. Portals sit on the plane only (no altitude), so the doorway is placed at the back of
    the surface, more than a portal's reach (44) behind the ground's back edge: only someone standing up there can
    take it. The door art stands on the surface; the portal's own plate is drawn at plane height, behind the building
    (or the cliff) in front of it, so it never floats in the air. `surface` tells the auto-path which tier to climb."""
    y0 = s["rect"][1]
    assert y0 + 6 + 44 < 620, (r.id, pid)
    r.decor("door", [x, y0 + door_dy], alt=s["height"])
    return r.portal(pid, "door", [x, y0 + 6], to, to_portal, press_up=True, facade=True, label=label, surface=s["id"], **kw)


def standable_prop(r, prop, x, y, fw, fd, top):
    """A prop you can stand on (a weapon rack, a crate): scenery with a walkable top at `top` (the movement pass's
    standable blocks). The prop art is the look; its top is solid ground for anyone who jumps onto it."""
    return r.block(prop, x, y, fw, fd, top, standable=True)


# ------------------------------------------------------------------ Willow Path
def willow_path(R):
    # Willow Path West: the training stumps and lifting stones become blocks you can stand on (the stumps at 60, the
    # standard block top nearest the row's 50; the stones at 40). Each block sits exactly over its object, drawn with
    # the same art, so the stumps still take hits and the stones are still lifted (body training, Dou's lesson).
    r = R["wp_west"]
    for i in range(3):
        x, y = obj(r, "stump_%d" % i)["at"]
        r.solid("stump_block_%d" % i, [x - 19, y - 20, 38, 24], 60, kind="stump")
    for oid in ("lift_1", "lift_2"):
        x, y = obj(r, oid)["at"]
        r.solid(oid + "_block", [x - 27, y - 18, 54, 22], 40, kind="lifting")

    # Willow Path East: Old Pan trades from the top of his cart (60), beside the wheel ruts; a roadside shrine stands
    # further on, its roof at 88 (one jump from the road).
    r = R["wp_east"]
    cart = next(b for b in r.d["blocks"] if b["id"] == "merchant_cart")
    cx = cart["rect"][0] + cart["rect"][2] // 2
    # He stands at the deck's front lip, so he is drawn in front of the cart's side boards, on its bed.
    obj(r, "npc_old_pan_wp").update({"at": [cx, cart["rect"][1] + cart["rect"][3] + 2], "alt": cart["top"], "surface": "merchant_cart"})
    obj(r, "pan_spot").update({"at": [cx + 110, 790], "prop": "grey_patch"})
    r.painted("roadside_shrine", "hall", 2050, 300, 110, 88, front=700)
    r.decor("incense_burner", [2050, 740])
    clear_blocks_of_spawns(r)


def clear_blocks_of_spawns(r):
    """Spawn points that fall inside a block step out in front of it."""
    for sp in r.d["spawns"]:
        for pt in sp["points"]:
            for b in r.d.get("blocks", []):
                x, y, w, h = b["rect"]
                if x - 20 <= pt[0] <= x + w + 20 and y - 20 <= pt[1] <= y + h + 20:
                    pt[1] = y + h + 40


# ------------------------------------------------------------------ Stoneford
def _shop_roof(r, sid, h, front=690):
    """A shop built from its prop art keeps the art on the street line; its walkable roof moves to height `h` (the
    roof face gives up what the facade gains, so the drawing does not move)."""
    W = _w()
    s = surf(r, sid)
    fh = W.PROPS[s["art"]]["frame"][1]
    s["height"] = h
    s["rect"] = [s["rect"][0], front - (fh - h), s["rect"][2], fh - h]
    return s


def market_street(R):
    """Market Street: 0 · awnings 88 · balconies 176 · rooftops 264 · bell tower 300. The shop roofs and the timber
    galleries between them make the 176 tier; the two-storey houses behind the shops carry the rooftops at 264; the bell
    tower is a lookout at 300 by its ladder. The daily thief runs over all of them (world.rooftop_routes)."""
    r = R["sf_market"]
    shops = [("general_store", "store_upper"), ("tea_house", "tea_upper"), ("warehouse_sf", "warehouse_upper")]
    for sid, upper in shops:
        s = _shop_roof(r, sid, 176)
        x0, y0, w, _ = s["rect"]
        # The upper storey stands behind the shop, its roof one jump above the shop roof.
        r.painted(upper, "two_storey", x0 + w // 2, w - 40, y0 - 482, 264, front=y0)
    # Galleries at 176 across the two gaps, behind the awnings: walked onto from the shop roofs at either end.
    gs, th, wh = (surf(r, s) for s, _ in shops)
    r.surface("gallery_west", [gs["rect"][0] + gs["rect"][2], 560, th["rect"][0] - gs["rect"][0] - gs["rect"][2], 64], 176, kind="balcony")
    r.surface("gallery_east", [th["rect"][0] + th["rect"][2], 560, wh["rect"][0] - th["rect"][0] - th["rect"][2], 64], 176, kind="balcony")
    # The bell tower: the watchtower art on the street line, its lookout at 300.
    drop_surfaces(r, ["bell_tower"])
    r.surface("bell_tower", [2290, 610, 180, 80], 300, kind="roof", art="watch_tower", optional=True)
    obj(r, "board_sf_tower").update({"at": [2380, 650], "alt": 300})
    # Ladders: one to each shop roof and gallery, one to each awning, and the bell-tower ladder.
    for sid, x in (("general_store", 380), ("tea_house", 1160), ("warehouse_sf", 1880)):
        r.ladder(sid + "_ladder", x, 690, 176, top=sid)
    r.ladder("gallery_west_ladder", gs["rect"][0] + gs["rect"][2] + 30, 624, 176, top="gallery_west")
    r.ladder("gallery_east_ladder", th["rect"][0] + th["rect"][2] + 30, 624, 176, top="gallery_east")
    for sid in ("awning_west", "awning_east"):
        a = surf(r, sid)
        r.ladder(sid + "_ladder", a["rect"][0] + a["rect"][2] - 30, a["rect"][1] + a["rect"][3], 88, top=sid)
    r.ladder("bell_tower_ladder", 2380, 690, 300, top="bell_tower")
    # The Spirit Stone shard lodged in the gutter where the tea house roof meets the house behind it.
    obj(r, "gutter_shard").update({"at": [th["rect"][0] + 140, th["rect"][1] + 6], "alt": 176, "surface": "tea_house"})
    authored(r)


def fairground(R):
    """Fairground: 0 · tent tops 100 · stage 60. Each recruiter tent has a stone stage (60) in front of it, and the
    recruiter stands on its front step (40), within talking reach of the crowd below (48); the tent's canopy is a top at
    100 with a guy rope up. The great drum throws you to the festival lanterns hung over it, too high for any jump."""
    W = _w()
    r = R["sf_fairground"]
    for side, npc in (("jade", "npc_recruiter_qing_lan"), ("cloud", "npc_recruiter_mo_yun")):
        x = next(d["at"][0] for d in r.d["decor"] if d["prop"] == "recruiter_tent_" + side)
        r.solid("stage_" + side, [x - 80, 740, 160, 50], 60, kind="wall")
        r.solid("stage_%s_step" % side, [x - 70, 790, 140, 36], 40, kind="wall")
        obj(r, npc).update({"at": [x, 810], "alt": 40, "surface": "stage_%s_step" % side})
        r.surface("tent_top_" + side, [x - 82, 612, 164, 62], 100, kind="awning")
        rope_x = x + 75 if side == "jade" else x - 75   # clear of the tent door
        r.ladder("tent_rope_" + side, rope_x, 674, 100, kind="rope", top="tent_top_" + side)
    drum = next(b for b in r.d["blocks"] if b["id"] == "fair_drum")
    cx = drum["rect"][0] + drum["rect"][2] // 2
    # The drum throws you to about 253 (40 + 213); a lantern is in reach within 48 of your height. A jump from a tent top
    # (100) peaks at 222 and one from a stage (60) at 182, so lanterns at 272-280 are the drum's alone.
    for i, (dx, dy, alt) in enumerate(((0, 20, 280), (-130, 10, 272), (130, 10, 272))):
        fid = "fair_lantern_%d" % i
        r.obj(fid, "pickup", [cx + dx, drum["rect"][1] + dy], alt=alt, item="jasmine_dew_tea", count=1, prop="lotus_lantern",
              label="Festival Lantern", hidden_if=W.all_of(W.flag(fid)), set_flag=fid)


# ------------------------------------------------------------------ the Jade Sect Academy
def jade_sect(R):
    W = _w()
    all_of, qdone = W.all_of, W.qdone

    # Gate Street: the mission hall's chest waits on the top of the roof chain (the 264 roof), off the thief's line.
    r = R["ja_gate_street"]
    r.chest([2230, 568], loot="chest_valley", level=4, alt=264, surface="cloud_roof", oid="chest_mission_hall")

    # Pavilion Rooftops: a herb pot on the pine branch, and a ladder from the terrace (80) to the 300 roof: the terrace
    # reaches along to the roof's east end, where the ladder stands.
    r = R["ja_pavilion_rooftops"]
    r.herb("willow_moss", [400, 688], oid="herb_pot_pine", alt=100, surface="pine_branch")
    heaven = surf(r, "heaven_roof")
    hx1 = heaven["rect"][0] + heaven["rect"][2]
    terrace(r, "terrace_walk", [hx1 - 20, 500, 1820 - (hx1 - 20), 60], 80)
    x = hx1 - 12
    r.d.setdefault("climbables", []).append({"id": "terrace_roof_ladder", "kind": "ladder", "at": [x, 538], "top_at": [x, heaven["rect"][1] + 12],
                                             "bottom_alt": 80, "top_alt": 300, "bottom": "terrace_walk", "top": "heaven_roof"})
    raised_door(r, "retreat_roof", heaven, 1500, "ja_retreat", "roof", "Retreat Rooms",
                requires=all_of(W.unlock("retreat_room")), locked_text="The retreat rooms are kept for inner disciples.")
    R["ja_retreat"].portal("roof", "door", [1160, 660], "ja_pavilion_rooftops", "retreat_roof", press_up=True, label="Pavilion Rooftops")

    # East Terrace: a raised terrace at 80 behind the square, up depth stairs flanked by stone lanterns (blocks, 40).
    # The cave abodes are cut into the cliff behind it; a personal disciple's door (Spirit Awakening 5, the same gate
    # as the door on Elder Hu's peak) leads into the abode.
    r = R["ja_east_terrace"]
    terrace(r, "abode_terrace", [1100, 500, 560, 80], 80)
    depth_stairs(r, "abode_stairs", 1290, 580, 200, 140, 80)
    for i, x in enumerate((1246, 1494)):
        r.solid("terrace_lantern_%d" % i, [x, 690, 40, 36], 40, kind="lantern")
    r.decor("cliff_face", [1260, 520], layer="back")
    r.decor("cliff_face", [1540, 520], layer="back", flip=True)
    r.decor("door", [1560, 506], alt=80)
    r.portal("abode", "door", [1560, 530], "ja_cave_abode", "terrace", press_up=True, facade=True, label="Cave Abode",
             surface="abode_terrace", requires=all_of(qdone("the_mentors_gift")),
             locked_text="The cave abodes of the elders' personal disciples. Not yours, not yet.")
    a = R["ja_cave_abode"]
    a.portal("terrace", "door", [1160, 700], "ja_east_terrace", "abode", press_up=True, label="East Terrace")

    # Alchemy Hall: the furnace on a stone platform (40); a mezzanine at 88 up a ladder, with the recipe shelf.
    r = R["ja_alchemy_hall"]
    r.solid("furnace_platform", [584, 776, 112, 48], 40, kind="wall")
    obj(r, "furnace_ja").update({"alt": 40, "surface": "furnace_platform"})
    r.surface("mezzanine", [60, 600, 380, 80], 88, kind="balcony")
    r.ladder("mezzanine_ladder", 410, 680, 88, top="mezzanine")
    for d in r.d["decor"]:
        if d["prop"] == "herb_drawers" and d["at"][0] < 640:
            d["at"] = [520, 660]
    r.decor("scroll_rack", [120, 606], alt=88)
    r.obj("recipe_shelf", "inspect", [260, 606], alt=88, surface="mezzanine", prop="shelf", label="Recipe Shelf",
          text="Pill recipes in cedar boxes, each tied with a coloured cord: the ones this hall has earned. Mei Qing knows every knot.")
    authored(r)

    weapon_halls(R)
    herb_terraces(R)
    elder_hu_peak(R)


def weapon_halls(R):
    """Weapon Hall and Forge (both sects): the weapon racks stand as blocks you can climb (110) and the training
    dummies wait on a raised sparring ring (40)."""
    for rid, dummies in (("ja_weapon_hall", ("dummy_wh_0", "dummy_wh_1")), ("cm_weapon_hall", ("dummy_cwh_0", "dummy_cwh_1"))):
        r = R[rid]
        racks = [d["at"][0] for d in r.d["decor"] if d["prop"] == "weapon_rack_full"]
        drop_decor(r, "weapon_rack_full")
        for x in racks:
            standable_prop(r, "weapon_rack_full", x, 676, 90, 24, 110)
        r.solid("sparring_ring", [200, 830, 300, 100], 40, kind="wall")
        for oid in dummies:
            obj(r, oid).update({"alt": 40, "surface": "sparring_ring"})
        authored(r)


def herb_terraces(R):
    """Herb Terraces (Jade): three ground terraces stepping up along the hillside, 40 · 80 · 120, each up its own
    depth stairs, with a garden bed on each and the herbs growing on them. (The weekly gathering trial is held here.)"""
    r = R["ja_herb_terraces"]
    drop_surfaces(r, ["terrace_1", "terrace_2"])
    tiers = []
    for i, (x, h) in enumerate(((560, 40), (1040, 80), (1520, 120))):
        sid = "terrace_%d" % (i + 1)
        terrace(r, sid, [x, 500, 480, 80], h)
        depth_stairs(r, "terrace_stairs_%d" % (i + 1), x + 20, 580, 160, 60 + h, h)
        tiers.append((sid, x, h))
    for i, (sid, x, h) in enumerate(tiers):
        obj(r, "bed_%d" % i).update({"at": [x + 330, 508], "alt": h, "surface": sid})
    obj(r, "herb_1").update({"at": [640, 508], "alt": 40, "surface": "terrace_1"})
    obj(r, "herb_2").update({"at": [1640, 508], "alt": 120, "surface": "terrace_3"})
    # Trees in the back row give way to the stairs.
    r.d["decor"] = [d for d in r.d["decor"] if not any(x <= d["at"][0] <= x + 200 for _, x, _ in tiers)]
    authored(r)


def elder_hu_peak(R):
    """Elder Hu's Peak: cliff ledges at 100 · 200 · 300 against the cliff, each up its own ladder and each one jump
    above the last. The meditation rock on the 300 ledge gathers Qi (a gathering formation's +0.5 density while you
    sit within reach of it)."""
    r = R["ja_elder_hu_peak"]
    drop_surfaces(r, ["ledge_peak_0", "ledge_peak_1"])
    for sid, rect, h, lx in (("cliff_ledge_100", [220, 560, 220, 80], 100, 250), ("cliff_ledge_200", [440, 540, 220, 80], 200, 630),
                             ("cliff_ledge_300", [660, 520, 240, 80], 300, 870)):
        r.surface(sid, rect, h, kind="rock_ledge")
        r.ladder(sid + "_ladder", lx, rect[1] + rect[3], h, top=sid)
    for x in (430, 750):
        r.decor("cliff_face", [x, 562], layer="back")
    r.obj("meditation_rock", "gathering_formation", [790, 530], alt=300, surface="cliff_ledge_300", prop="meditation_mat", radius=60,
          label="Meditation Rock")
    r.decor("boulder_moss", [790, 524], alt=300)
    authored(r)


# ------------------------------------------------------------------ the Cloud Sect Monastery
def cloud_sect(R):
    # Cliff Stair: depth stairs up to the landing (100), a rope from the landing to the high ledge (200), and the top
    # ledge (300, the Cloud Steps' finish) one jump on or up its own rope from the court.
    r = R["cm_cliff_stair"]
    st = surf(r, "stair_a")
    st.update({"height": 100, "rise": -100})   # the back of the stair meets the landing at 100, its foot the court
    surf(r, "landing")["kind"] = "ground"
    drop_surfaces(r, ["ledge_hi"])
    r.surface("ledge_hi", [1200, 490, 300, 70], 200, kind="rock_ledge")
    r.ladder("ledge_hi_rope", 1230, 560, 200, depth=40, kind="rope", bottom="landing", top="ledge_hi", base=100)
    top = surf(r, "ledge_top")
    top["rect"] = [1500, 560, 300, 80]
    r.ladder("ledge_top_rope", 1770, 640, 300, kind="rope", top="ledge_top")
    for x in (1300, 1620):
        r.decor("cliff_face", [x, 562], layer="back")
    # The Cloud Library's upper gate: a door on the top ledge, set in the cliff wall that rises behind it (the wall is
    # depth-sorted, in front of the doorway's plate and behind the ledge, the bell and anyone on the court).
    r.decor("cliff_face", [1660, top["rect"][1] + 12])
    raised_door(r, "library", top, 1640, "cm_cloud_library", "cliff_door", "Cloud Library", door_dy=16)
    R["cm_cloud_library"].portal("cliff_door", "door", [960, 660], "cm_cliff_stair", "library", press_up=True, label="Cliff Stair")
    authored(r)

    # Array Court: a stone dais (40) holds the formation table and the Formation Elder; the formation nodes stand on
    # low tables (blocks, 60) behind it.
    r = R["cm_array_court"]
    r.solid("array_dais", [860, 790, 480, 110], 40, kind="wall")
    obj(r, "formation_table_cm").update({"at": [1100, 840], "alt": 40, "surface": "array_dais"})
    obj(r, "npc_cloud_formation_elder").update({"at": [930, 830], "alt": 40, "surface": "array_dais"})
    for i, d in enumerate([d for d in r.d["decor"] if d["prop"] == "formation_node"]):
        x = d["at"][0]
        r.solid("formation_table_%d" % i, [x - 50, 720, 100, 44], 60, kind="table")
        d.update({"at": [x, 738], "alt": 60})


# ------------------------------------------------------------------ the Hidden Vale (your sect)
def hidden_vale(R):
    """Back Mountain: cliff ledges at 100 · 200 · 300 up the mountain behind the spring, ropes to each, the orchid on the
    top ledge and the Spirit Stone seam on the middle one. The Sect Grounds' roofs come with their buildings (Part 8:
    "grows with your sect"), which the room data cannot yet do: a surface has no condition, so the roofs would stand
    before the buildings do (docs/v9f3_towns.md)."""
    r = R["hv_back_mountain"]
    r.d["decor"] = [d for d in r.d["decor"] if not (d.get("layer", "play") == "play" and d["prop"] in ("pine_tree", "plum_tree")
                                                    and 1450 <= d["at"][0] <= 2350)]
    for sid, rect, h, rx in (("mountain_ledge_100", [1560, 560, 240, 80], 100, 1590), ("mountain_ledge_200", [1800, 540, 240, 80], 200, 2010),
                             ("mountain_ledge_300", [2040, 520, 260, 80], 300, 2270)):
        r.surface(sid, rect, h, kind="rock_ledge")
        r.ladder(sid + "_rope", rx, rect[1] + rect[3], h, kind="rope", top=sid)
    for x in (1680, 1960, 2200):
        r.decor("cliff_face", [x, 562], layer="back")
    obj(r, "herb_2").update({"at": [2160, 528], "alt": 300, "surface": "mountain_ledge_300"})
    obj(r, "ore_3").update({"at": [1900, 548], "alt": 200, "surface": "mountain_ledge_200"})
    authored(r)


def run(rooms):
    willow_path(rooms)
    market_street(rooms)
    fairground(rooms)
    jade_sect(rooms)
    cloud_sect(rooms)
    hidden_vale(rooms)
