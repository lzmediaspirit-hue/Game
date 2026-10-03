"""E1 room specs (R5): the Tidebreak Front, the Wardens' last fortress against the Hollow Tide and the grey beyond it
(docs/architecture/room_engine.md). The Bastion's yard behind its great wall, with the skiff dock over the cloud sea
and the great bell; the Tide battle on the wall's outer terrace round the great lantern (instanced); and east of the
Bastion the grey fields the Tide has drunk: the Greyfall Breach in the outer wall, the Hollow Wake and the Drone Hive,
whose far edge thins into the Nebula Deep. A wall that must read as one runs east and west, so its face shows."""
from content.rooms.spec import room

# What grows on the grey: dead trees and grey reeds, stumps, the odd rock and fallen log.
GREY = ["dead_tree", "grey_reeds", "stump", "rock_small", "grey_reeds", "dead_tree", "log"]


# The Tidebreak Bastion: the Wardens' yard of flagstones under the great wall and its two towers, the granite road
# through it from the skiff dock in the west to the east gate between two more towers. The great lantern's cage stands
# on its dais against the wall, star lanterns along the road; Quartermaster Bai keeps his armoury west of the cage,
# Captain Duan stands before it, Tinker Mei has her bench by the east tower; the great bell hangs on its own dais south
# of the road. The rock falls away past the yard's south edge into the cloud sea, where the skiffs come in.
TF_TIDEBREAK_BASTION = room(
    "tf_tidebreak_bastion", size=(64, 26), biome="bastion",
    bands=[("yard", 0, 26, dict(level=0, paint="p")),
           ("rim", 21, 5, dict(level=0, paint="r", wavy=True)),
           ("wall", 0, 4, dict(level=4, paint="s", wall=True)),
           ("road", 12, 4, dict(paint="s", walk=True))],
    features=[("wall_tower", (4, 0, 5, 6), dict(level=5, paint="s", wall=True)),   # the great wall's towers
              ("wall_tower_2", (38, 0, 5, 6), dict(level=5, paint="s", wall=True)),
              ("tower_ne", (56, 4, 8, 7), dict(level=3, paint="s")),
              ("tower_se", (56, 17, 8, 5), dict(level=3, paint="s")),
              ("cage_dais", (19, 4, 7, 4), dict(level=1, paint="s")),
              ("bell_dais", (34, 18, 6, 3), dict(level=1, paint="s")),
              ("garden", (45, 5, 8, 4), dict(paint="g")),
              ("dock", (4, 20, 4, 6), dict(level=0, paint="w"))],
    stairs="auto",
    ways={"skiff": ("s", 6), "east": ("e", "road")},
    spawn=(10, 13),
    anchors={"shrine_tf_bastion": (10, 18), "tide_horn": (37, 19), "npc_warden_captain_duan": (25, 10),
             "npc_quartermaster_bai": (16, 9), "npc_tinker_mei": (47, 18)},
    props=[("lantern", 19, 4), ("lantern", 25, 4), ("lantern", 21, 5), ("lantern", 23, 5),
           ("lantern", 13, 11), ("lantern", 28, 11), ("lantern", 43, 11), ("lantern", 13, 16), ("lantern", 28, 16),
           ("lantern", 43, 16), ("lantern", 4, 19), ("lantern", 7, 19),
           ("weapon_rack", 12, 4), ("weapon_rack", 14, 4), ("crates", 10, 6), ("barrel", 12, 7), ("barrel", 17, 5),
           ("forge", 44, 20), ("desk", 49, 17), ("crates", 50, 20), ("barrel", 52, 19), ("sacks", 43, 17),
           ("notice", 31, 9), ("banner_jade", 55, 9), ("banner_cloud", 55, 17), ("water_jar", 33, 5), ("sacks", 35, 5),
           ("barrel", 36, 5)],
    flora={"yard": dict(density=0.12), "rim": {"kinds": ["rock_small", "tall_grass", "rock_mossy"], "density": 0.3},
           "garden": {"kinds": ["tree_pine", "bush", "tall_grass"], "density": 0.9}})


# The Tide Breaks (instanced): the outer terrace of the Bastion's wall, where the Tide comes for the great lantern. The
# lantern burns in its cage on a granite dais against the wall in the middle; a barricade of crates and barrels crosses
# the terrace on each side of it, a gap in each where the road runs, the lines the Wardens hold; the Tide comes from
# both ends, up over the rim from the cloud sea. The way back to the Bastion is the road west along the wall's foot.
def _barricade(x):
    """A line of the Wardens' barricade across the terrace at column x: crates and barrels from the wall's foot to the
    rim, a gap where the road runs."""
    return [("crates", x, 4), ("barrel", x, 5), ("barrel", x + 1, 5), ("crates", x, 6), ("crates", x, 7), ("sacks", x, 8),
            ("barrel", x + 1, 8), ("crates", x, 14), ("sacks", x, 15), ("barrel", x + 1, 15), ("crates", x, 16),
            ("crates", x, 17)]


SI_TIDE_BATTLE = room(
    "si_tide_battle", size=(60, 24), biome="bastion",
    bands=[("terrace", 0, 24, dict(level=0, paint="p")),
           ("rim", 19, 5, dict(level=0, paint="r", wavy=True)),
           ("wall", 0, 4, dict(level=4, paint="s", wall=True))],
    features=[("road", (0, 10, 60, 4), dict(paint="s")),                       # the road along the wall's foot
              ("lantern_dais", (25, 4, 10, 6), dict(level=1, paint="s"))],
    stairs="auto",
    ways={"exit": ("w", 11.5)},
    spawn=(30, 12),
    anchors={"great_lantern": (29.5, 6)},
    props=[("lantern", 25, 4), ("lantern", 34, 4), ("lantern", 2, 4), ("lantern", 57, 4), ("weapon_rack", 20, 4),
           ("weapon_rack", 38, 4), ("sacks", 23, 16), ("sacks", 36, 16), ("lantern", 22, 9), ("lantern", 37, 9)]
          + _barricade(16) + _barricade(42),
    flora={"terrace": dict(density=0.1), "rim": {"kinds": ["rock_small", "grey_reeds", "rock_mossy"], "density": 0.35}},
    event={"waves": [[(4, 18), (56, 9)],                                       # the drones, at both ends
                     [(6, 21), (54, 19)]]})                                    # the wyrmlings, up over the rim


# The Greyfall Breach: the Bastion's outer wall across the grey, broken in the middle where the Tide came through.
# The Wardens' road comes in from the Bastion along the wall's south side, turns north through the breach and runs on
# east through the grey to the Hollow Wake; the wall steps down at the breach's ragged edges, rubble in the gap. Shen
# Lian holds the breach, the warning bell beside it on the Wardens' side; the drones' hives stand in the grey north of
# the wall, where the stand's waves come from; a rock outcrop rises each side of it.
TF_GREYFALL_BREACH = room(
    "tf_greyfall_breach", size=(64, 28), biome="tidebreak",
    bands=[("grey", 0, 28, dict(level=0)),
           ("wall", 13, 3, dict(level=3, paint="s", wall=True))],
    features=[("breach", (26, 13, 11, 3), dict(level=0, paint="r")),
              ("broken", (26, 13, 2, 3), dict(level=2, paint="s", wall=True)),    # the wall stepping down at the gap
              ("broken_2", (35, 13, 2, 3), dict(level=1, paint="s", wall=True)),
              ("rubble", (25, 10, 13, 9), dict(paint="r", shape="round")),
              ("road", (0, 20, 33, 3), dict(paint="p", walk=True)),             # the Wardens' road from the Bastion
              ("road_n", (29, 7, 4, 16), dict(paint="d", walk=True)),           # north through the breach
              ("road_e", (29, 7, 35, 3), dict(paint="d", walk=True)),           # and east through the grey
              ("outcrop", (42, 0, 10, 5), dict(level=1, paint="r", shape="round")),
              ("outcrop_2", (8, 23, 10, 4), dict(level=1, paint="r", shape="round"))],
    stairs="auto",
    ways={"west": ("w", 21), "east": ("e", 8)},
    spawn="west",
    anchors={"jar_1": "outcrop_2@12", "crate_2": "outcrop@46", "jar_3": "road_e.s2@41", "crate_4": "road_e.n2@56",
             "npc_shen_lian_breach": (31, 14), "greyfall_stand": (26, 18)},
    props=[("drone_hive", 14, 4), ("drone_hive", 22, 2), ("drone_hive", 38, 3), ("drone_hive", 55, 2),
           ("drone_hive", 59, 11), ("boulder", 28, 12), ("boulder", 34, 12), ("rock_small", 33, 16),
           ("boulder", 27, 16), ("boulder", 34, 17), ("boulder", 25, 12), ("rock_small", 36, 12),
           ("lantern", 18, 19), ("lantern", 24, 19), ("lantern", 10, 19), ("lantern", 6, 23), ("barrel", 21, 17),
           ("crates", 15, 17), ("weapon_rack", 2, 17)],
    flora={"grey": dict(density=0.32), "rubble": {"kinds": ["rock_small", "grey_reeds"], "density": 0.6}},
    event={"waves": [[(40, 5), (50, 10), (58, 4)],                            # the Greyfall stand: the drones
                     [(45, 11), (54, 7)]]},                                   # and the wyrmlings, out of the grey
    foes="auto")


# The Hollow Wake: the grey scar the Tide left running east, a trough between two low rises of drained rock, the track
# along its floor; grey pools standing in it, dead trees on the rises, three outcrops climbing from them. Lu's journal
# page lies on its rack by the first pool.
TF_HOLLOW_WAKE = room(
    "tf_hollow_wake", size=(64, 28), biome="tidebreak",
    bands=[("wake", 0, 28, dict(level=0)),
           ("rise", 0, 7, dict(level=1, paint="r", wavy=True)),
           ("rise_s", 21, 7, dict(level=1, paint="r", wavy=True)),
           ("track", 13, 3, dict(paint="d", walk=True))],
    features=[("outcrop", (11, 0, 8, 4), dict(level=2, paint="r", shape="round")),
              ("outcrop_2", (30, 23, 8, 5), dict(level=2, paint="r", shape="round")),
              ("outcrop_3", (47, 0, 8, 4), dict(level=2, paint="r", shape="round")),
              ("pool", (17, 9, 12, 3), dict(water=True, shape="round")),
              ("pool_2", (38, 17, 13, 3), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", "track"), "east": ("e", "track")},
    spawn="west",
    anchors={"jar_1": "outcrop.front@15", "crate_2": "outcrop_2@33", "jar_3": "track.s2@35", "crate_4": "rise@57",
             "chest_cloud_mv": "rise@24", "journal_wake": "track.s@24"},
    props=[("drone_hive", 6, 23), ("drone_hive", 27, 2), ("drone_hive", 45, 23), ("drone_hive", 59, 2)],
    flora={"rise": {"kinds": GREY, "density": 0.3}, "rise_s": {"kinds": GREY, "density": 0.3},
           "wake": dict(density=0.16), "pool": {"kinds": ["grey_reeds", "cattails"], "density": 0.5},
           "pool_2": {"kinds": ["grey_reeds", "cattails"], "density": 0.5}},
    foes="auto")


# The Drone Hive: the Hollow's hive mound in the grey, two tiers of rock thick with hives, the two chests on its crown;
# the track skirts it to the south and runs east to where the dark thins into the nebula.
TF_DRONE_HIVE = room(
    "tf_drone_hive", size=(64, 26), biome="tidebreak",
    bands=[("grey", 0, 26, dict(level=0)),
           ("ridge", 0, 3, dict(level=2, paint="r", wall=True, wavy=True)),
           ("track", 17, 4, dict(paint="d", walk=True))],
    features=[("mound", (20, 4, 24, 12), dict(level=1, paint="r", shape="round")),
              ("crown", (26, 5, 12, 7), dict(level=2, paint="r", shape="round"))],
    stairs="auto",
    ways={"west": ("w", "track"), "east": ("e", "track")},
    spawn="west",
    anchors={"jar_1": "mound@22", "crate_2": "mound@40", "jar_3": "track.s2@39", "crate_4": "track.n2@55",
             "chest_5": "crown@30", "chest_cloud_mv": "crown@34"},
    props=[("drone_hive", 27, 6), ("drone_hive", 35, 6), ("drone_hive", 22, 8), ("drone_hive", 40, 9),
           ("drone_hive", 8, 7), ("drone_hive", 50, 9), ("drone_hive", 57, 5), ("drone_hive", 6, 22),
           ("drone_hive", 48, 22), ("drone_hive", 58, 23)],
    flora={"grey": dict(density=0.28), "mound": {"kinds": ["rock_small", "grey_reeds", "dead_tree"], "density": 0.3}},
    foes="auto")

ROOMS = [TF_TIDEBREAK_BASTION, SI_TIDE_BATTLE, TF_GREYFALL_BREACH, TF_HOLLOW_WAKE, TF_DRONE_HIVE]
