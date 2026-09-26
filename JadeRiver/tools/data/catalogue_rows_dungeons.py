"""V9f3 · the Part 8 room verticality catalogue rows V2d left partial (dungeons and story rooms). Runs after
catalogue.run(ROOMS) and before the movement and verticality passes (tools/data/world.py build()).

Each room here is built to its catalogue row (Build Prompt v2, Part 8, "Fields, dungeons and secret places") and marked
vertical="authored", so the movement and verticality passes leave it as built; tools/data/room_lint.py still checks it.
Every portal, quest object, event and spawn the story and the tests use stays where it works:
  - the Mudwater Hideout key is the Caravan Road drop that opens the Stockade, so the tower's key is a spare;
  - Lu's inscriptions, the Riverbreath rite circle and its wave points, the Abbot's bells and vault, the monastery's
    insight stone and jade tree, the story events' fixed spawns and waves all keep their places on dry ground.
"""


def _w():
    import world
    return world


def authored(r):
    r.d["vertical"] = "authored"


def surf(r, sid):
    return next(s for s in r.d["surfaces"] if s["id"] == sid)


def obj(r, oid):
    return next(o for o in r.d["objects"] if o["id"] == oid)


def of_type(r, *types):
    return [o for o in r.d["objects"] if o["type"] in types]


def put(o, at, alt=0, sid=None):
    """Move an object to a spot on a tier (or back to the ground)."""
    o["at"] = list(at)
    if alt:
        o["alt"] = alt
        if sid:
            o["surface"] = sid
    else:
        o.pop("alt", None)
        o.pop("surface", None)
    return o


def drop_surfaces(r, ids):
    """Remove surfaces and everything that hangs on them (climbables, movers, crumble volumes)."""
    ids = set(ids)
    r.d["surfaces"] = [s for s in r.d["surfaces"] if s["id"] not in ids]
    r.d["climbables"] = [c for c in r.d.get("climbables", []) if c.get("top") not in ids and c.get("bottom") not in ids]
    r.d["movers"] = [m for m in r.d.get("movers", []) if m["surface"] not in ids]
    r.d["volumes"] = [v for v in r.d.get("volumes", []) if v.get("surface") not in ids]


def drop_decor(r, prop, near=None, radius=60):
    r.d["decor"] = [d for d in r.d["decor"] if not (d["prop"] == prop and (
        near is None or abs(d["at"][0] - near[0]) + abs(d["at"][1] - near[1]) <= radius))]


def crumble(r, sid, break_s=0.8, return_s=5.0):
    """S43 crumble: the surface gives way 0.8 s after a foot lands on it and comes back after 5 s."""
    s = surf(r, sid)
    return r.volume("crumble", s["rect"], surface=sid, break_s=break_s, return_s=return_s, vid=sid + "_crumble")


def swing(r, sid, length, amp_deg, period_s, phase_deg=0.0):
    """A lantern on its rope: a pendulum `length` long, `amp_deg` either side, every `period_s` (zone_geometry.gd)."""
    m = {"surface": sid, "mode": "swing", "length": length, "amp_deg": amp_deg, "period_s": period_s, "phase_deg": phase_deg, "path": []}
    r.d.setdefault("movers", []).append(m)
    return m


def circle(r, sid, radius, period_s, phase_deg=0.0):
    """A lantern that goes round: from its own height up to 2 x radius above it and back, every `period_s`."""
    m = {"surface": sid, "mode": "circle", "radius": radius, "period_s": period_s, "phase_deg": phase_deg, "path": []}
    r.d.setdefault("movers", []).append(m)
    return m


def spawn_points(r, enemy, points, surface="ground"):
    """Re-place a spawn's points (and its surface) by hand."""
    for sp in r.d["spawns"]:
        if sp["enemy"] == enemy and not sp.get("elite") and not sp.get("boss"):
            sp["points"] = [list(p) for p in points]
            sp["surface"] = surface
            return sp
    raise KeyError((r.id, enemy))


def mid(s, dx=0.0):
    """A point on a surface (or a block top): its middle in depth, `dx` along from its centre. Where actors stand."""
    x, y, w, d = s["rect"]
    return [int(x + w / 2 + dx), int(y + d / 2)]


def spot(s, dx=0.0):
    """Where an object sits on a surface or block top: near its back edge. An object is drawn by its own depth and a
    platform by its front edge, so an object in the middle of a deck is half hidden by the planks; at the back it shows."""
    x, y, w, d = s["rect"]
    return [int(x + w / 2 + dx), int(y + min(14, d / 2))]


# ------------------------------------------------------------------ Mudwater Hideout
def stockade(R):
    """Stockade: 0 · palisade 160 · watchtowers 180. Two palisades cross the yard (wall blocks 160, stake by stake) from the
    back wall to a gate at the front; two timber watchtowers at 180 stand inside them, climbed by ladder or from a crate
    stack. Bandit archers hold the towers; the west tower keeps the gatekeeper's spare key, both keep a chest. The key that
    opens the Stockade is the Caravan Road drop (The Caravan Road), so the tower's key is a spare that shows only to a
    character who has lost theirs: a key object that locked the Tunnels would change the Mudwater Hideout quest."""
    W = _w()
    r = R["mh_stockade"]
    drop_decor(r, "stockade_wall")
    r.decor("stockade_wall", [1250, 650])   # the painted inner gatehouse at the back of the middle yard
    # The palisades: stakes 160 high from the back wall across the yard, the gate a 90-wide opening at the front (a gate
    # in the middle of the depth would hide behind the wall's own top from this camera).
    for i, x in enumerate((560, 1900)):
        for k in range(9):   # stake by stake, so the wall reads as a palisade from this camera
            r.solid("palisade_%d_%d" % (i, k), [x, 620 + k * 28, 36, 28], 160, kind="fence")
    # The watchtowers, each with a ladder and a crate stack (40 in front of 80) one jump below the deck.
    for sid, x, lad, crate_x in (("watchtower_w", 680, 700, 874), ("watchtower_e", 1680, 1840, 1616)):
        r.surface(sid, [x, 620, 180, 70], 180, kind="scaffold")
        r.ladder(sid + "_ladder", lad, 690, 180, top=sid)
        r.solid(sid + "_crate_high", [crate_x, 704, 50, 42], 80, kind="crate")
        r.solid(sid + "_crate_low", [crate_x, 748, 50, 44], 40, kind="crate")
    tw, te = surf(r, "watchtower_w"), surf(r, "watchtower_e")
    # The Hideout key is the Caravan Road drop that opened the gate: the tower keeps a spare for anyone who lost theirs.
    r.obj("tower_key", "pickup", spot(tw, -60), alt=180, surface="watchtower_w", item="mudwater_key", count=1, prop="none",
          label="Gate Key", set_flag="stockade_tower_key",
          hidden_if={"any": [W.flag("stockade_tower_key"), {"kind": "item_owned", "item": "mudwater_key", "count": 1}]})
    chest = of_type(r, "chest")[0]
    put(chest, spot(te, -40), 180, "watchtower_e")
    # The yard's second chest (it stood on a generic ledge before this row; its id is kept for saves).
    r.chest(spot(tw, 0), loot="chest_dungeon", level=20, alt=180, surface="watchtower_w", oid="chest_ledge_mv_1")
    jars = of_type(r, "jar", "crate")
    put(jars[0], spot(tw, 60), 180, "watchtower_w")
    put(jars[1], spot(te, 50), 180, "watchtower_e")
    for o, at in zip(jars[2:], ((300, 900), (1300, 700), (2300, 720))):
        put(o, at)
    # Archers on the towers (S43 tier natives), bandits and hounds in the yards on either side of the gates.
    r.spawn("bandit_archer", [mid(tw, 10)], 1, level=[16, 19], surface="watchtower_w")
    r.spawn("bandit_archer", [mid(te, 10)], 1, level=[16, 19], surface="watchtower_e")
    spawn_points(r, "mudwater_bandit", [[300, 780], [900, 760], [1150, 880], [1420, 780], [1650, 900], [2200, 800]])
    spawn_points(r, "mud_hound", [[1000, 900], [1300, 700], [2100, 900], [2350, 760]])
    authored(r)


def tunnels(R):
    """Tunnels: 0 · 60 · pits. Two spike pits (a hazard volume under a bed of stakes) crossed by crumbling planks at 60,
    with low beams (logs, 40) at each lip; a timber landing at 60 between the pits holds the chest. The back wall keeps a
    narrow dry path past each pit. Jars ride the crumbling planks."""
    r = R["mh_tunnels"]
    drop_surfaces(r, ["rotten_boards"])
    for tag, x0 in (("a", 860), ("b", 1500)):
        # The pit: the stakes hurt only on its floor (altitude up to 20); planks at 60 stay above them.
        r.volume("hazard", [x0, 690, 300, 270], alt=[-10, 20], vid="spike_pit_" + tag, hazard="spike_traps",
                 damage_pct=0.05, pulse_s=0.8, status={"id": "bleed", "s": 3.0, "power": 0.01})
        for k, (dx, y) in enumerate(((60, 720), (190, 760), (110, 850), (240, 900), (40, 930))):
            r.decor("thorn_thicket", [x0 + dx, y], layer="play", flip=bool(k % 2))
        for k in range(3):
            sid = "plank_%s%d" % (tag, k)
            r.surface(sid, [x0 + 5 + k * 100, 770, 90, 70], 60, kind="boards")
            crumble(r, sid)
        r.solid("beam_%s_west" % tag, [x0 - 60, 770, 50, 70], 40, kind="log")
        r.solid("beam_%s_east" % tag, [x0 + 305, 770, 50, 70], 40, kind="log")
    # The timber landing between the pits (a low beam at 60) and its step.
    r.surface("timber_landing", [1240, 630, 200, 70], 60, kind="scaffold")
    r.solid("landing_step", [1300, 712, 60, 44], 40, kind="log")
    land = surf(r, "timber_landing")
    put(of_type(r, "chest")[0], spot(land, 30), 60, "timber_landing")
    jars = of_type(r, "jar", "crate")
    put(jars[0], spot(surf(r, "plank_a1")), 60, "plank_a1")
    put(jars[1], spot(surf(r, "plank_b1")), 60, "plank_b1")
    put(jars[2], spot(land, -60), 60, "timber_landing")
    for o, at in zip(jars[3:], ((420, 720), (2250, 900))):
        put(o, at)
    put(of_type(r, "ore_vein")[0], (2280, 690))
    # Archers (S43 tier natives): two keep the landing, one at each far lip of the pits on a beam; hounds work the floor.
    blk = lambda b: next(x for x in r.d["blocks"] if x["id"] == b)
    spawn_points(r, "bandit_archer", [mid(land, -40), mid(land, 50)], surface="timber_landing")["max"] = 2
    r.spawn("bandit_archer", [mid(blk("beam_a_west"))], 1, level=[16, 19], surface="beam_a_west")
    r.spawn("bandit_archer", [mid(blk("beam_b_east"))], 1, level=[16, 19], surface="beam_b_east")
    spawn_points(r, "mud_hound", [[520, 880], [1340, 790], [2100, 880], [2400, 700]])
    authored(r)


def loot_cave(R):
    """Loot Cave: 0 · stalagmite tops 80 / 160. Three stalagmite pairs (blocks 80 and 160, the low one a step to the high),
    crate stacks to climb; the loot piles (the chest, jars) sit on the high stalagmites, archers on the low ones."""
    r = R["mh_loot_cave"]
    for i, (x, y) in enumerate(((520, 650), (1000, 640), (1620, 650))):
        r.solid("stalagmite_low_%d" % i, [x, y + 66, 70, 60], 80, kind="stalagmite")
        r.solid("stalagmite_high_%d" % i, [x + 90, y, 70, 60], 160, kind="stalagmite")
    r.solid("loot_crate_low", [760, 820, 56, 44], 40, kind="crate")
    r.solid("loot_crate_high", [764, 776, 56, 42], 80, kind="crate")
    r.solid("loot_crate_east", [2000, 700, 56, 44], 40, kind="crate")
    top = lambda b: next(x for x in r.d["blocks"] if x["id"] == b)
    put(of_type(r, "chest")[0], spot(top("stalagmite_high_1")), 160, "stalagmite_high_1")
    jars = of_type(r, "jar", "crate")
    put(jars[0], spot(top("stalagmite_high_0")), 160, "stalagmite_high_0")
    put(jars[1], spot(top("stalagmite_high_2")), 160, "stalagmite_high_2")
    for o, at in zip(jars[2:], ((300, 900), (1400, 720), (2200, 700))):
        put(o, at)
    sp = spawn_points(r, "bandit_archer", [mid(top("stalagmite_low_0"))], surface="stalagmite_low_0")
    sp["max"] = 1
    r.spawn("bandit_archer", [mid(top("stalagmite_low_2"))], 1, level=[17, 20], surface="stalagmite_low_2")
    spawn_points(r, "mudwater_bandit", [[400, 820], [900, 880], [1300, 800], [1800, 900], [2150, 820]])
    authored(r)


# ------------------------------------------------------------------ the Drowned Shrine
def flooded_gate(R):
    """Flooded Gate: 0 · floating planks · current. The gate's basin is still flooded (deep water) and the flood drains
    west through it (a current push); planks float on it, drifting back and forth. The old sluice deck (60, ladder) on the
    far bank keeps the chest."""
    r = R["ds_flooded_gate"]
    r.deep_water("gate_flood", [920, 690, 640, 270])
    r.volume("current", [920, 690, 640, 270], alt=[-100, 10], push=[-110, 0], vid="flood_current")
    for sid, rect, dx, speed, wait in (("float_plank_0", [940, 720, 150, 60], 260, 38, 1.5),
                                       ("float_plank_1", [1380, 800, 150, 60], -300, 34, 1.2),
                                       ("float_plank_2", [1000, 880, 150, 60], 380, 42, 1.8)):
        r.surface(sid, rect, 30, kind="raft")
        r.mover(sid, [[dx, 0, 0]], speed=speed, wait_s=wait)
    r.surface("sluice_deck", [1620, 630, 220, 70], 60, kind="stilt")
    r.ladder("sluice_ladder", 1800, 700, 60, top="sluice_deck")
    deck = surf(r, "sluice_deck")
    put(of_type(r, "chest")[0], spot(deck, -60), 60, "sluice_deck")
    # The gate's broken lintel at 200 over the sluice, +140 above the deck: a Paths Above ledge (later: double jump).
    # It keeps the id of the generic ledge it replaces, so a found ledge and an opened chest stay found in old saves.
    r.surface("ledge_mv_1", [1860, 600, 240, 70], 200, kind="rock_ledge", later="double_jump")
    r.chest(spot(surf(r, "ledge_mv_1")), loot="chest_dungeon", level=27, alt=200, surface="ledge_mv_1", oid="chest_ledge_mv_1")
    jars = of_type(r, "jar")
    put(jars[0], spot(deck, 20), 60, "sluice_deck")
    put(jars[1], spot(deck, 80), 60, "sluice_deck")
    for o, at in zip(jars[2:], ((260, 720), (700, 900), (2300, 720))):
        put(o, at)
    spawn_points(r, "drowned_acolyte", [[400, 780], [700, 860], [1850, 860], [2100, 760], [2300, 900]])
    authored(r)


def hall_of_lanterns(R):
    """Hall of Lanterns: 0 · swinging lanterns 100-200. A chain of lantern platforms on ropes: swinging ones (swing movers)
    and two that go round (circle movers), each carrying you a tier higher (100 to 200, 200 to 300). The jumps are timed
    to the swings. Rock ledges at 100 and 200 with ropes are the safe way up and the rests between; the lantern loft at 300
    at the end of the chain keeps the chest. Paper Talisman Ghosts float between the tiers."""
    r = R["ds_hall_of_lanterns"]
    r.surface("lantern_ledge_west", [220, 640, 240, 70], 100, kind="rock_ledge")
    r.ladder("lantern_ledge_west_rope", 260, 710, 100, kind="rope", top="lantern_ledge_west")
    r.surface("lantern_rest", [1260, 620, 240, 70], 200, kind="rock_ledge")
    r.ladder("lantern_rest_rope", 1290, 690, 200, kind="rope", top="lantern_rest")
    r.ladder("lantern_rest_chain", 1470, 690, 200, kind="chain", top="lantern_rest")
    # The chain, west to east. Neighbours swing against each other: jump when they come close (a walker's jump makes
    # about 150 on the level; at rest the gaps are 100 to 140, and the swings open and close them by up to 96).
    chain = [("lantern_0", [570, 650, 120, 60], 100, ("swing", 110, 25, 3.2, 0)),
             ("lantern_1", [830, 640, 120, 60], 100, ("circle", 50, 4.4, 0)),
             ("lantern_2", [1080, 630, 120, 60], 200, ("swing", 110, 25, 3.2, 180)),
             ("lantern_3", [1620, 630, 120, 60], 200, ("swing", 110, 25, 3.2, 90)),
             ("lantern_4", [1880, 640, 120, 60], 200, ("circle", 50, 4.4, 180))]
    for sid, rect, h, move in chain:
        r.surface(sid, rect, h, kind="branch", optional=True)
        if move[0] == "swing":
            swing(r, sid, *move[1:])
        else:
            circle(r, sid, *move[1:])
    r.surface("lantern_loft", [2080, 600, 240, 70], 300, kind="rock_ledge", optional=True)
    for x in (640, 1140, 1680):
        r.decor("lantern_string", [x, 380], layer="back")
    put(of_type(r, "chest")[0], spot(surf(r, "lantern_loft")), 300, "lantern_loft")
    jars = of_type(r, "jar")
    put(jars[0], spot(surf(r, "lantern_ledge_west"), 60), 100, "lantern_ledge_west")
    put(jars[1], spot(surf(r, "lantern_rest"), 70), 200, "lantern_rest")
    for o, at in zip(jars[2:], ((700, 900), (1600, 720), (2300, 880))):
        put(o, at)
    # Lu's four inscriptions (Lu's Handwriting): two on the ledges, two on the hall floor.
    put(obj(r, "inscription_ds_hall_of_lanterns_1"), spot(surf(r, "lantern_ledge_west"), -40), 100, "lantern_ledge_west")
    put(obj(r, "inscription_ds_hall_of_lanterns_2"), spot(surf(r, "lantern_rest"), -20), 200, "lantern_rest")
    spawn_points(r, "paper_talisman_ghost", [mid(surf(r, "lantern_ledge_west"), 20)], surface="lantern_ledge_west")["max"] = 1
    r.spawn("paper_talisman_ghost", [mid(surf(r, "lantern_rest"), 40)], 1, level=[22, 25], surface="lantern_rest")
    r.spawn("paper_talisman_ghost", [[2150, 800], [1900, 900]], 1, level=[22, 25])
    spawn_points(r, "drowned_acolyte", [[480, 880], [1050, 820], [1600, 880], [2050, 760]])
    authored(r)


def scripture_well(R):
    """Scripture Well: the shaft. The catalogue asks a shaft descending 0 -> -300 (void_altitude -550); the engine's floor
    is one slab at 0 that the terrain painter carries 640 past each end and the camera stops at its front, so no pit can
    be drawn. The well is built as a descent from a high rim instead: the rim at 300 (rope), ledges at 200 (the bucket
    chain) and 100 down the shaft face, and the flooded bottom (deep water: Breath Control's swim) at the foot, beside
    the flooded shaft to the Drowned Grotto. Lu's inscriptions are cut into the ledges."""
    r = R["ds_scripture_well"]
    r.surface("well_rim", [980, 570, 260, 70], 300, kind="rock_ledge")
    r.ladder("well_rim_rope", 1010, 640, 300, kind="rope", top="well_rim")
    r.surface("well_ledge_200", [1300, 590, 260, 70], 200, kind="rock_ledge")
    r.ladder("well_bucket_chain", 1530, 660, 200, kind="chain", top="well_ledge_200")
    r.surface("well_ledge_100", [1000, 650, 240, 70], 100, kind="rock_ledge")
    r.ladder("well_ledge_100_rope", 1030, 720, 100, kind="rope", top="well_ledge_100")
    r.deep_water("well_pool", [1100, 660, 360, 120])
    rim, l2, l1 = surf(r, "well_rim"), surf(r, "well_ledge_200"), surf(r, "well_ledge_100")
    put(obj(r, "inscription_ds_scripture_well_0"), spot(rim, 40), 300, "well_rim")
    lines = [("well_ledge_200", l2, "Lu's hand again, lower down the shaft: \"The river does not fight the stone. It goes round, "
                                     "and in a thousand years the stone is gone.\""),
             ("well_ledge_100", l1, "Scratched just above the water line, in a hurry: \"Breathe out before you go under. "
                                     "The well gives back what you do not hold.\"")]
    for i, (sid, s, text) in enumerate(lines, start=1):
        r.obj("inscription_ds_scripture_well_%d" % i, "inspect", spot(s, -30), alt=int(s["height"]), surface=sid,
              prop="scholar_rock", text=text, set_flag="inscription_ds_scripture_well_%d" % i)
    put(of_type(r, "chest")[0], spot(rim, -60), 300, "well_rim")
    jars = of_type(r, "jar")
    put(jars[0], spot(l2, 60), 200, "well_ledge_200")
    put(jars[1], spot(l1, 70), 100, "well_ledge_100")
    for o, at in zip(jars[2:], ((400, 720), (2000, 900), (2300, 720))):
        put(o, at)
    # The ghosts float down the shaft between the ledges; the Riverbreath rite's waves keep their dry ground.
    spawn_points(r, "paper_talisman_ghost", [mid(rim, 90)], surface="well_rim")["max"] = 1
    r.spawn("paper_talisman_ghost", [mid(l2, -80)], 1, level=[23, 26], surface="well_ledge_200")
    r.spawn("paper_talisman_ghost", [[500, 800], [2150, 820], [2250, 920]], 2, level=[23, 26])
    authored(r)


def abbots_sanctum(R):
    """Abbot's Sanctum: 0 · 100 · 200 · rising water. The four small bells hang over the ledges at 100 and 200 (V2d);
    each ledge now has its rope, the high ones a plinth (80) to jump from. At two thirds of his health the Abbot floods the
    sanctum (rising water keyed to his "flood" phase, as in Serpent's Shallows): the ledges and plinths stay dry."""
    r = R["ds_abbots_sanctum"]
    for i in range(4):
        s = surf(r, "bell_ledge_%d" % i)
        x, y, w, d = s["rect"]
        r.ladder("bell_ledge_%d_rope" % i, x + 30, y + d, int(s["height"]), kind="rope", top=s["id"])
        if s["height"] > 100:
            r.solid("bell_plinth_%d" % i, [x + w - 70, y + d + 12, 60, 50], 80, kind="statue")
    r.volume("rising_water", [260, 700, 2060, 260], alt=[-100, -20], vid="sanctum_flood",
             rise=[{"event": "boss_phase", "match": {"action": "flood"}, "to": 30, "over_s": 4.0, "hold_s": 14.0, "back_to": -20}])
    authored(r)


# ------------------------------------------------------------------ Mist Peak and Summit Ridge
def forgotten_monastery(R):
    """Forgotten Monastery: 0 · ruined roofs 88 / 176 · crumbling floors. The main hall's roof at 176, two ruined side halls
    at 88, and between them the rotten upper floors that give way underfoot (crumble). Formation remnants still hum on the
    roofs; a hidden stair (two hidden portals, found with Spirit Sense) runs under the ruins from the west hall to the east
    of the main hall. The insight stone and the Nine-Bough Jade Tree keep their ground."""
    r = R["mp_forgotten_monastery"]
    surf(r, "monastery_hall")["height"] = 176
    r.ladder("monastery_hall_ladder", 1600, 690, 176, top="monastery_hall")
    r.painted("west_ruin", "two_storey", 700, 420, 120, 88, front=690)
    r.ladder("west_ruin_ladder", 560, 690, 88, top="west_ruin")
    r.painted("east_ruin", "gate", 3000, 400, 110, 88, front=690)
    r.ladder("east_ruin_ladder", 3160, 690, 88, top="east_ruin")
    # The rotten floors: the collapsed upper storey between the west hall and the main hall, and the east gallery.
    r.surface("west_floor", [960, 600, 220, 70], 176, kind="boards")
    crumble(r, "west_floor")
    r.surface("east_gallery", [2290, 640, 220, 70], 88, kind="boards")
    crumble(r, "east_gallery")
    r.solid("fallen_beam", [2500, 740, 80, 50], 40, kind="rubble")
    r.solid("fallen_masonry", [1260, 760, 90, 60], 60, kind="rubble")
    wr, er, hall = surf(r, "west_ruin"), surf(r, "east_ruin"), surf(r, "monastery_hall")
    # Formation remnants on the roofs (the old ground nodes go up with them).
    drop_decor(r, "formation_node")
    remnant = ("A cracked formation flag, still humming. Whoever set it meant to keep something in, not out.",
               "Three array stones in a ring, one of them split. The Qi here runs the wrong way round.",
               "A formation plate worn smooth by rain. The last line of its seal reads: \"until the gate opens\".")
    for i, (s, dx) in enumerate(((wr, -120), (hall, 200), (er, 90))):
        r.obj("formation_remnant_%d" % i, "inspect", spot(s, dx), alt=int(s["height"]), surface=s["id"], prop="formation_node",
              text=remnant[i])
    # The hidden stair: two hidden doors that lead to each other, shown by Spirit Sense.
    r.portal("hidden_cellar", "hidden", [420, 720], "mp_forgotten_monastery", "hidden_stair", press_up=True, label="A hidden stair")
    r.portal("hidden_stair", "hidden", [2260, 720], "mp_forgotten_monastery", "hidden_cellar", press_up=True, label="A hidden stair")
    put(of_type(r, "herb_patch")[0], spot(wr, 100), 88, "west_ruin")
    put(of_type(r, "ore_vein")[0], (2900, 760))
    put(of_type(r, "chest")[0], spot(hall, -200), 176, "monastery_hall")
    jars = of_type(r, "jar")
    put(jars[0], spot(surf(r, "west_floor")), 176, "west_floor")
    put(jars[1], spot(surf(r, "east_gallery")), 88, "east_gallery")
    put(jars[2], spot(er, -90), 88, "east_ruin")
    for o, at in zip(jars[3:], ((1450, 900), (2850, 930), (3500, 900))):
        put(o, at)
    authored(r)


def ascension_gate(R):
    """Ascension Gate: 0 · rings 200 · flight phase. Ring platforms of cloud at 200 stand round the open sky in front of the
    arch (220, its ladder kept): footing at 200 for the Gate Guardian's flight phase (its boss_phase is unchanged).
    Fallen ring stones (60) are the step up for anyone not flying."""
    r = R["mp_ascension_gate"]
    r.ladder("ascension_arch_ladder", 1860, 690, 220, top="ascension_arch")
    for i, rect in enumerate(([760, 780, 220, 70], [1000, 690, 240, 70], [1280, 610, 240, 70],
                              [2320, 610, 240, 70], [2600, 690, 240, 70], [2860, 780, 220, 70])):
        r.surface("ring_%d" % i, rect, 200, kind="cloud")
    r.solid("ring_stone_west", [1420, 760, 80, 60], 60, kind="rubble")
    r.solid("ring_stone_east", [2340, 760, 80, 60], 60, kind="rubble")
    authored(r)


def frozen_shrine(R):
    """Frozen Shrine: 0 · 100 · icicle platforms (crumble). Rock ledges at 100 (ropes) at either end, and between them a
    run of icicle platforms at 200 that crack and fall under a foot (crumble) to the shrine's high ledge, where the
    Soulbell Flower grows (rare_herbs names it ledge_mv_1). The Mystic ore vein is on the west ledge. The ice sheets
    (shrine_ice, shrine_ice_2) are laid on the ground later by world.ice_sheets()."""
    r = R["sr_frozen_shrine"]
    r.surface("shrine_ledge_west", [260, 640, 240, 70], 100, kind="rock_ledge")
    r.ladder("shrine_ledge_west_rope", 300, 710, 100, kind="rope", top="shrine_ledge_west")
    for i, x in enumerate((580, 800)):
        r.surface("icicle_%d" % i, [x, 620, 160, 70], 200, kind="rock_ledge")
        crumble(r, "icicle_%d" % i)
    r.surface("ledge_mv_1", [1020, 610, 280, 70], 200, kind="rock_ledge")   # the Soulbell's ledge (world.rare_herbs)
    r.surface("icicle_2", [1380, 620, 160, 70], 200, kind="rock_ledge")
    crumble(r, "icicle_2")
    r.surface("shrine_ledge_east", [1620, 640, 240, 70], 100, kind="rock_ledge")
    r.ladder("shrine_ledge_east_rope", 1830, 710, 100, kind="rope", top="shrine_ledge_east")
    west, east = surf(r, "shrine_ledge_west"), surf(r, "shrine_ledge_east")
    r.chest(spot(surf(r, "ledge_mv_1"), 100), loot="chest_valley", level=63, alt=200, surface="ledge_mv_1", oid="chest_ledge_mv_1")
    put(of_type(r, "ore_vein")[0], spot(west, -40), 100, "shrine_ledge_west")
    jars = of_type(r, "jar")
    put(jars[0], spot(west, 70), 100, "shrine_ledge_west")
    put(jars[1], spot(east, 40), 100, "shrine_ledge_east")
    for o, at in zip(jars[2:], ((500, 900), (2450, 880))):
        put(o, at)
    authored(r)


# ------------------------------------------------------------------ story instances
def trial_of_reflections(R):
    """Trial of Reflections: a mirror arena, 0 · 100 left and right. Two ledges at 100, one the mirror of the other, each
    with a rope and a step stone; a bronze mirror at the back. The Reflection is fixed on the floor (its event is kept):
    as a story boss it neither jumps nor climbs (enemies.py movement), so it cannot yet use the tiers as you do."""
    r = R["si_trial_of_reflections"]
    for side, x, rope_x, step_x in (("left", 220, 250, 390), ("right", 820, 1030, 830)):
        sid = "mirror_" + side
        r.surface(sid, [x, 640, 240, 70], 100, kind="rock_ledge")
        r.ladder(sid + "_rope", rope_x, 710, 100, kind="rope", top=sid)
        r.solid(sid + "_step", [step_x, 722, 60, 50], 40, kind="rock")
    r.decor("bronze_mirror", [640, 640], layer="back")
    authored(r)


def gus_warehouse(R):
    """Gu's Warehouse: 0 · crate stacks 80 · catwalks 176 · rafters 264. Crate stacks (40 in front of 80) under the two
    catwalks along the back wall; ladders; the rafters above the catwalks run over the open middle of the floor where the
    bandits stand, the stealth route (Concealment) to Gu's strongbox, hidden up in the east rafters."""
    r = R["si_gus_warehouse"]
    for prop in ("sack_pile", "barrel"):
        drop_decor(r, prop)
    for sid, x, lad, crate_x in (("catwalk_west", 240, 280, 880), ("catwalk_east", 1620, 2280, 1630)):
        r.surface(sid, [x, 600, 700, 60], 176, kind="balcony")
        r.ladder(sid + "_ladder", lad, 660, 176, top=sid)
        r.solid(sid + "_crate_high", [crate_x, 670, 56, 44], 80, kind="crate")
        r.solid(sid + "_crate_low", [crate_x, 716, 56, 44], 40, kind="crate")
    for i, (x, w) in enumerate(((620, 320), (1000, 280), (1340, 280), (1680, 320))):
        r.surface("rafter_%d" % i, [x, 540, w, 60], 264, kind="branch")
    r.ladder("rafter_0_ladder", 700, 600, 264, depth=40, bottom="catwalk_west", top="rafter_0", base=176)
    r.ladder("rafter_1_rope", 1140, 600, 264, kind="rope", top="rafter_1")
    r.ladder("rafter_2_rope", 1480, 600, 264, kind="rope", top="rafter_2")
    r.ladder("rafter_3_ladder", 1920, 600, 264, depth=40, bottom="catwalk_east", top="rafter_3", base=176)
    r.solid("barrel_stack", [520, 760, 50, 44], 40, kind="barrel")
    r.solid("sack_stack", [1760, 780, 70, 44], 40, kind="sack")
    put(obj(r, "gus_vault"), spot(surf(r, "rafter_3"), 80), 264, "rafter_3")
    authored(r)


def siege(R):
    """Siege of Two Sects: 0 · battlements 160 · towers 240. The wall's walkway at 160 (stone steps 40/80/110 and a ladder)
    between two towers at 240 (ladders), facing east where the Hollow comes; the siege event, its waves and the Behemoth
    keep their ground to the east."""
    r = R["si_siege"]
    drop_surfaces(r, ["rampart_0", "rampart_1"])
    drop_decor(r, "stockade_wall")
    drop_decor(r, "banner_cloud")
    r.surface("battlement", [640, 620, 1560, 70], 160, kind="walltop")
    for i, (x, top) in enumerate(((760, 40), (820, 80), (880, 110))):
        r.solid("battlement_step_%d" % i, [x, 700, 60, 50], top, kind="wall")
    r.ladder("battlement_ladder", 1500, 690, 160, top="battlement")
    for sid, x, lad in (("tower_west", 530, 460), ("tower_east", 2310, 2380)):
        r.painted(sid, "tower", x, 220, 90, 240, front=690)
        r.ladder(sid + "_ladder", lad, 690, 240, top=sid)
    for x in (1000, 1800):
        r.decor("banner_cloud" if x == 1000 else "banner_jade", [x, 650], layer="play", alt=160)
    authored(r)


def run(R):
    stockade(R)
    tunnels(R)
    loot_cave(R)
    flooded_gate(R)
    hall_of_lanterns(R)
    scripture_well(R)
    abbots_sanctum(R)
    forgotten_monastery(R)
    ascension_gate(R)
    frozen_shrine(R)
    trial_of_reflections(R)
    gus_warehouse(R)
    siege(R)
