"""E1 room specs (R4, the peaks): the Hidden Vale, the player's own sect, behind Crane Falls (docs/architecture/room_engine.md).
The Vale Gate (its teleport stone, the defence circle), the Sect Grounds (every sect building's slot, shown once it is
raised; the storehouse, the shrine, the alarm bell) and the Back Mountain (the Qi spring, the treasure plot, the Vale
Serpent's lost art). A sheltered valley among the peaks: blossom, maples and bamboo, paved courts on terraces."""
from content.rooms.spec import room

# The Vale Gate: the road in from the falls through the vale's mouth, between the cliffs and a stream. Banners and
# stone lanterns stand either side of the road where the side view's gate arch stood; the teleport stone waits by the
# road where travellers arrive, and the sect's defence circle lies on a stone terrace under the cliff.
HV_VALE_GATE = room(
    "hv_vale_gate", size=(40, 26), biome="hidden_vale",
    bands=[("crown", 0, 3, dict(level=5, paint="r", wall=True)),
           ("lawn", 3, 9, dict(level=0, paint="f")),
           ("road", 12, 3, dict(paint="p", walk=True)),
           ("meadow", 15, 6, dict(level=0)),
           ("stream", 21, 5, dict(water=True, wavy=True))],
    features=[("terrace", (24, 4, 12, 6), dict(level=1, paint="p", flights=[29]))],
    stairs="auto",
    ways={"path": ("w", "road"), "east": ("e", "road")},
    spawn="path",
    anchors={"stone_hv": "verge.n@8", "defence_hv": "terrace.top"},
    props=[("banner_jade", 17, 11), ("banner_jade", 22, 11), ("lantern", 16, 15), ("lantern", 23, 15)],
    flora={"lawn": dict(density=0.4), "meadow": dict(density=0.36)},
    foes="auto")

# The Sect Grounds: the sect's lawns climbing in two terraces under the cliffs, each fronted by a paved walk where
# its buildings' slots stand, the road and the lower lawn below. The great buildings' slots line the upper walk (the
# treasury, the main hall's pagoda, the meditation pavilion, the beast pavilion, the alchemy hall); the hall's altar,
# the mission hall, the forge, the library, the watchtower, the guest house, the mirror and the ancestral shrine stand
# on the walk below; on the lawn the herb terraces' beds, the array's nodes, the storehouse chest, the shrine, the
# alarm bell, a lotus pond and the training posts (the raiders of a defence come in at the lawn's west and east,
# cells 9 and 46 of row 26). Each building is drawn once it is raised; until then the lawns and their trees.
HV_SECT_GROUNDS = room(
    "hv_sect_grounds", size=(56, 30), biome="hidden_vale",
    bands=[("crown", 0, 3, dict(level=6, paint="r", wall=True)),
           ("upper", 3, 8, dict(level=2, flights=[9, 28, 46])),
           ("court", 11, 7, dict(level=1, flights=[28])),
           ("road", 19, 3, dict(paint="p", walk=True)),
           ("lawn", 22, 8, dict(level=0))],
    features=[("upper_walk", (0, 8, 56, 3), dict(paint="p")), ("court_walk", (0, 15, 56, 3), dict(paint="p")),
              ("axis", (25, 10, 7, 9), dict(paint="p")),
              ("pond", (33, 24, 11, 6), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"beast_pavilion_hv": "upper.front@4", "treasury_hv": "upper.front@15", "hall_pagoda": "upper.front@28",
             "pavilion_hv": "upper.front@39", "alchemy_hall_hv": "upper.front@51", "mission_hall_hv": "court.front@12",
             "forge_hv": "court.front@20", "sect_hall": "court.front@32", "library_hv": "court.front@24",
             "outpost_hv": "court_walk@36", "mirror_hv": "court.front@36", "guest_house_hv": "court.front@45",
             "ancestral_shrine_hv": "court.front@52", "hall_gate": "verge.s@3", "terrace_bed_0": "lawn@8",
             "terrace_bed_1": "lawn@11", "terrace_bed_2": "lawn@14", "storage_hv": "verge.s@18",
             "array_node_0": "lawn@25", "array_node_1": "lawn@31", "shrine_hv": "verge.s@38", "defence_bell": "verge.s@50"},
    props=[("banner_jade", 7, 10), ("banner_jade", 49, 10), ("lantern", 26, 17), ("lantern", 33, 17),
           ("post", 49, 25), ("post", 52, 27), ("weapon_rack", 48, 28)],
    flora={"upper": dict(density=0.4), "court": dict(density=0.4), "lawn": dict(density=0.34)},
    foes="auto",
    pins={"drop": [(46, 26)]})   # the defence's east raiders come in here

# The Back Mountain: the sect's quiet ground behind the grounds, where disciples sit. A glade by a spring pool (the
# Qi spring on its bank, the mist lotus at its edge), the scholar's rock with the Vale Serpent's writing, the treasure
# plot in its ring of stones; meditation mats and incense; terraces of rock climb north-east under the peaks to the
# spirit shard vein and, on the highest, the cloudtop orchid.
HV_BACK_MOUNTAIN = room(
    "hv_back_mountain", size=(56, 30), biome="hidden_vale",
    bands=[("crown", 0, 4, dict(level=6, paint="r", wall=True)),
           ("ledges", 4, 9, dict(level=1, wavy="s", flights=[12, 30])),
           ("path", 14, 3, dict(paint="d", walk=True, w=40)),
           ("glade", 17, 13, dict(level=0))],
    features=[("ledge_100", (30, 4, 26, 8), dict(level=2, paint="r", shape="round", flights=[49])),
              ("ledge_200", (40, 4, 16, 6), dict(level=3, paint="r", shape="round")),
              ("pool", (10, 19, 18, 9), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", "path")},
    spawn="west",
    anchors={"herb_1": "bank@14", "spring_hv": "bank@24", "lost_vale_serpent": "glade@32", "plot_hv": "glade@42",
             "ore_3": "ledge_100@36", "herb_2": "ledge_200@48"},
    props=[("mat", 30, 23), ("mat", 34, 25), ("incense", 33, 22), ("shrine_small", 6, 8), ("lantern", 28, 18)],
    flora={"ledges": dict(density=0.45), "glade": dict(density=0.36)},
    foes="auto")

ROOMS = [HV_VALE_GATE, HV_SECT_GROUNDS, HV_BACK_MOUNTAIN]
