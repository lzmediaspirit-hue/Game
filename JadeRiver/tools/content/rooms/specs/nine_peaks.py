"""E1 room specs (R7, Act II's chapter 13): Nine Peaks, the Alliance's seat among the peaks of the Azure Expanse
(docs/architecture/room_engine.md, "Nine Peaks to the Tomb of Sunscar (R7)"). The sky-ship lands at the Alliance Gate;
the Hall of Nine and its Auction Pavilion; the Presence Terrace on the last peak, its Trial Hall, and the road down to
the Gale Canyons. A sect-capital of paved courts on granite terraces under the crags (the Cloud Sect's terraces'
look, `sect_terraces`), guardian lions and banners at its gates, the cloud sea under its brinks."""
from content.rooms.spec import room

CRAGS = dict(level=6, paint="r", wall=True)   # the peaks behind every court


# The Alliance Gate: where the sky-ship from Cloudgate Port ties up. Its dock juts south off the brink over the cloud
# sea; the Alliance's road runs east from it between two guardian lions and the Alliance's banners, past the gate
# guard, the war gong's ring and the teleport stone, to the Hall of Nine. North of the road a granite terrace under
# the crags holds the gate's shrine among pines and plum; south of it a lawn falls to the brink.
NP_ALLIANCE_GATE = room(
    "np_alliance_gate", size=(56, 28), biome="sect_terraces", level=1,
    bands=[("crown", 0, 3, CRAGS),
           ("terrace", 3, 9, dict(level=2, wavy="s", flights=[14, 44])),
           ("road", 13, 3, dict(paint="p", walk=True)),
           ("brink", 22, 6, dict(level=0)),
           ("lawn", 16, 7, dict(level=1, wavy="s"))],
    features=[("gate_court", (20, 11, 17, 10), dict(paint="p")),
              ("slip", (1, 18, 13, 11), dict(level=0, shape="round")),       # the brink cut back round the dock
              ("dock", (6, 16, 3, 12), dict(level=1, paint="w"))],
    stairs="auto",
    ways={"ferry": ("s", 7, dict(arrive=4)), "east": ("e", "road")},
    spawn="ferry",
    anchors={"shrine_np_gate": "terrace@15", "npc_alliance_guard_np": "road.s@30", "war_gong_np": "gate_court@33",
             "stone_nine_peaks": "verge.s@46", "sign_np": "verge.n@52"},
    props=[("guardian_lion", 23, 11), ("guardian_lion", 33, 11), ("guardian_lion", 23, 17), ("guardian_lion", 33, 17),
           ("banner_cloud", 20, 11), ("banner_jade", 36, 11), ("banner_jade", 20, 17), ("banner_cloud", 36, 17),
           ("lantern", 5, 16), ("lantern", 9, 16), ("post", 5, 23), ("post", 9, 23), ("post", 5, 27), ("post", 9, 27),
           ("crates", 10, 17), ("barrel", 3, 17)],
    flora={"terrace": dict(density=0.42), "lawn": dict(density=0.36), "brink": dict(density=0.4)},
    foes="auto")


# The Hall of Nine: the Alliance's great hall on its granite platform under the crags, a grand stair down to the court
# where the envoy and Elder Zhong receive the newcomers; the ancestral altar in the garden west of it; the Auction
# Pavilion's house on the court to the east, its door path down to the road; banners at the court's ends, lanterns
# along it; south of the road a forecourt round a lotus pond where the broker waits.
NP_HALL_OF_NINE = room(
    "np_hall_of_nine", size=(56, 28), biome="sect_terraces", level=1,
    bands=[("crown", 0, 3, CRAGS),
           ("terrace", 3, 9, dict(level=2, wavy="s", w=17, flights=[9])),
           ("road", 15, 3, dict(paint="p", walk=True)),
           ("garden", 18, 10, dict(level=1))],
    features=[("platform", (17, 3, 22, 8), dict(level=3, paint="s", flights=[27])),
              ("east_garden", (39, 3, 17, 5), dict(level=2, wavy="s")),
              ("court", (14, 11, 28, 11), dict(paint="p")),
              ("pond", (21, 21, 14, 6), dict(water=True, shape="round"))],
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road"),
          "pavilion_door": ("door", "auction", dict(path=(15, "p")))},
    spawn="west",
    anchors={"ancestral_altar": "terrace@10", "npc_envoy_lanshi": "court@23", "npc_elder_zhong": "court@31",
             "npc_broker_mu_np": "verge.s@7"},
    props=[("hall", 24, 4), ("house", 45, 8, "auction"), ("lantern", 18, 9), ("lantern", 37, 9),
           ("banner_jade", 9, 14), ("banner_cloud", 47, 14),
           {"kind": "lantern", "along": "road", "every": 8, "row": 14, "start": 3},
           {"kind": "lantern", "along": "road", "every": 8, "row": 18, "start": 7},
           ("guardian_lion", 23, 12), ("guardian_lion", 31, 12)],
    flora={"terrace": dict(density=0.45), "east_garden": dict(density=0.45), "garden": dict(density=0.36),
           "pond": ["tall_grass", "cattails", "lotus_pads"]},
    foes="auto")


# The Auction Pavilion: a hall of dark boards behind the Hall of Nine's court. The auction block stands on its dais
# under the lot board's screens, Auctioneer Tong beside it; the bidders' mats in rows before it; scroll shelves of the
# catalogues down the west wall, the strongroom's cabinets down the east, red lanterns at the door.
NP_AUCTION_PAVILION = room(
    "np_auction_pavilion", size=(24, 14), base="w", walls=dict(high=4),
    features=[("dais", (7, 1, 10, 4), dict(level=1, paint="w")),            # the auction block's dais
              ("cheek", (10, 5, 1, 2), dict(level=2, paint="w")),           # its steps' cheeks, a level over it
              ("cheek_2", (13, 5, 1, 2), dict(level=2, paint="w"))],
    stairs=[(11, 5, 2, 2, 0, 1, "w")],
    ways={"entry": ("s", 4.5)},
    spawn="entry",
    anchors={"auction_block": (11.5, 2), "npc_auctioneer_tong": (14.5, 3)},
    props=[("screen", 7, 1), ("screen", 15, 1), ("lantern_red", 7, 4), ("lantern_red", 16, 4),
           ("scroll_shelf", 1, 1), ("scroll_shelf", 3, 1), ("desk", 1, 4), ("cabinet", 19, 1), ("cabinet", 21, 1),
           ("crates", 21, 4), ("mat", 6, 8), ("mat", 10, 8), ("mat", 14, 8), ("mat", 6, 10), ("mat", 10, 10),
           ("mat", 14, 10), ("lantern_red", 2, 12), ("lantern_red", 7, 12), ("pot_bonsai", 21, 11), ("pot_orchid", 1, 9)])


# The Presence Terrace: the Alliance's last peak, a round paved terrace where its champions spar, the Trial Hall on the
# granite terrace above it (its door down a flight to the arena), a rock knoll in the east where the star-sighting
# stone looks out over the Expanse; the road comes in from the Hall of Nine in the west and leaves east, down the
# mountain's flank to the Gale Canyons' toll.
NP_PRESENCE_TERRACE = room(
    "np_presence_terrace", size=(56, 28), biome="sect_terraces", level=1,
    bands=[("crown", 0, 3, CRAGS),
           ("terrace", 3, 9, dict(level=2, wavy="s", x=22, w=19, flights=[31])),
           ("road", 14, 3, dict(paint="p", walk=True)),
           ("brink", 23, 5, dict(level=0)),
           ("flank", 17, 7, dict(level=1, wavy="s"))],
    features=[("hall_court", (3, 3, 19, 9), dict(level=2, paint="s", flights=[12])),
              ("knoll", (41, 3, 15, 9), dict(level=2, paint="r", shape="round", flights=[47])),
              ("crag", (47, 3, 7, 4), dict(level=3, paint="r", shape="round")),
              ("arena", (16, 13, 26, 11), dict(paint="s", shape="round"))],
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road"), "trial_door": ("door", "trial_hall")},
    spawn="west",
    anchors={"spar_np": (26, 19), "npc_champion_qiao": (33, 18), "sight_presence_terrace": "knoll@46",
             "sign_np_terrace": "verge.n@53"},
    props=[("hall", 8, 3, "trial_hall"), ("lantern", 4, 9), ("lantern", 20, 9), ("banner_jade", 17, 13),
           ("banner_cloud", 40, 13), ("lantern", 20, 21), ("lantern", 37, 21)],
    flora={"terrace": dict(density=0.42), "flank": dict(density=0.38), "brink": dict(density=0.4),
           "knoll": ["tree_pine", "rock_mossy", "rock_small"]},
    foes="auto")


# The Trial Hall: where the Alliance's eight elders sit in judgement. Their eight seats on the dais along the back wall,
# four either side of the empty ninth under the pressure pillar; the Presence Trial's circle on the floor before them;
# Trial Master Wen by the east wall; the Alliance's banners and lanterns down the hall.
NP_TRIAL_HALL = room(
    "np_trial_hall", size=(28, 16), base="s", walls=dict(high=5),
    features=[("dais", (1, 1, 26, 4), dict(level=1, paint="w")),            # the elders' dais
              ("pillar", (13, 1, 2, 2), dict(level=5, paint="s")),          # the pressure pillar
              ("cheek", (5, 5, 1, 2), dict(level=2, paint="w")),            # the dais's steps' cheeks
              ("cheek_2", (8, 5, 1, 2), dict(level=2, paint="w")),
              ("cheek_3", (19, 5, 1, 2), dict(level=2, paint="w")),
              ("cheek_4", (22, 5, 1, 2), dict(level=2, paint="w"))],
    stairs=[(6, 5, 2, 2, 0, 1, "w"), (20, 5, 2, 2, 0, 1, "w")],
    ways={"entry": ("s", 4.5)},
    spawn="entry",
    anchors={"presence_gate": (13.5, 9), "npc_trial_master_wen": (22, 9)},
    props=[("mat", 1, 2), ("mat", 4, 2), ("mat", 8, 2), ("mat", 10, 3), ("mat", 16, 3), ("mat", 18, 2),
           ("mat", 22, 2), ("mat", 25, 2), ("incense", 12, 3), ("incense", 15, 3), ("banner_jade", 3, 1),
           ("banner_cloud", 7, 1), ("banner_jade", 20, 1), ("banner_cloud", 24, 1), ("lantern", 1, 6),
           ("lantern", 26, 6), ("lantern", 9, 13), ("lantern", 18, 13), ("pot_bonsai", 1, 13), ("pot_orchid", 26, 13)])

ROOMS = [NP_ALLIANCE_GATE, NP_HALL_OF_NINE, NP_AUCTION_PAVILION, NP_PRESENCE_TERRACE, NP_TRIAL_HALL]
