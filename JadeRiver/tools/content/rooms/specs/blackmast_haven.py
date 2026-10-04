"""E1 room specs (R8): Blackmast Haven, the pirates' cove wedged among black rock islands (docs/architecture/room_engine.md).
Chapter 18's The Purser's Ledger (the Blackmast Docks), Gunners' Battery (its cannons spiked, the purser found in the
Smugglers' Cove by Spirit Sense) and The Admiral (Admiral Voss on his Flagship Deck). Timber docks and boardwalks along
the black rock, the pirates' ships moored in the cove with their black masts, a tavern under red lamps, the battery's
guns behind a parapet over the lanes; the flagship rides at anchor in the deep water."""
from content.rooms.spec import room
from content.rooms.specs.skysea import hull

# The Blackmast Docks: the haven's boardwalk runs along the foot of the black rock, the island's yard above it with the
# tavern under its red lamps, a shed and the shrine; a crag of rock over the yard holds a lookout (the two chests the
# pirates hid there). South of the boardwalk the cove: three piers out into the starsea's water and two pirate ships
# moored between them, black masts crowding the water; Deckhand Mo, escaped from the flagship, hides by the west pier.
BM_BLACKMAST_DOCKS = room(
    "bm_blackmast_docks", size=(64, 28), biome="blackmast", level=1,
    bands=[("crags", 0, 3, dict(level=4, paint="r", wall=True, wavy="s")),
           ("yard", 3, 7, dict(level=1, paint="r")),
           ("boardwalk", 10, 3, dict(paint="w", walk=True)),
           ("cove", 13, 15, dict(water=True))],
    features=[("crag", (33, 3, 9, 5), dict(level=2, paint="r", shape="round", flights=[37])),
              ("pier", (4, 13, 4, 15), dict(level=1, paint="w")),
              ("pier_2", (28, 13, 4, 9), dict(level=1, paint="w")),
              ("pier_3", (56, 13, 4, 13), dict(level=1, paint="w"))]
             + hull("ship", 8, 16, 13, 6, dict(level=2, paint="w"), bow=6)
             + [("ship_stern", (8, 16, 4, 6), dict(level=3, paint="w")),
                ("gangway", (15, 13, 2, 3), dict(level=2, paint="w"))]                # the ship's gangway to the boardwalk
             + hull("brig", 32, 15, 14, 7, dict(level=2, paint="w"), bow=6),
    stairs="auto",
    ways={"west": ("w", "boardwalk"), "east": ("e", "boardwalk")},
    spawn="west",
    anchors={"sign_bm": "boardwalk.n@9", "shrine_bm_docks": "yard@12", "npc_deckhand_mo": "pier@5", "jar_1": "yard@16",
             "jar_2": "ship_stern@10", "chest_ledge_mv_1": "crag@35", "chest_cloud_mv": "crag@39", "jar_3": "brig@41",
             "jar_4": "yard@55"},
    props=[("house", 19, 4), ("storehouse", 46, 4), ("lantern_red", 18, 8), ("lantern_red", 25, 8), ("lantern_red", 45, 8),
           ("lantern_red", 50, 8), ("pirate_banner", 7, 9), ("pirate_banner", 22, 9), ("pirate_banner", 48, 9),
           ("barrel", 26, 6), ("barrel", 27, 7), ("powder_keg", 31, 8), ("powder_keg", 42, 8), ("pirate_cannon", 52, 8),
           ("crates", 2, 5), ("sacks", 4, 5), ("black_mast", 14, 19), ("black_mast", 37, 18), ("black_mast", 43, 18),
           ("post", 4, 27), ("post", 7, 27), ("post", 28, 21), ("post", 31, 21), ("post", 56, 25), ("post", 59, 25)],
    flora={"yard": dict(density=0.24), "cove": {"kinds": ["cattails"], "density": 0.12}},
    foes="auto")


# The Gunners' Battery: the haven's guns on its headland, east of the docks. The road crosses the battery's yard under
# the black cliff, a powder store on a raised deck at the west and a lookout higher at the middle; south of it the gun
# floor behind a parapet of granite across the headland, the three cannons in their embrasures over the lanes. The crack
# at the cliff's foot east of the lookout is the Smugglers' Cove, shown by Spirit Sense; the road goes on east to the
# gangway of the Admiral's flagship.
BM_GUNNERS_BATTERY = room(
    "bm_gunners_battery", size=(64, 28), biome="blackmast", level=1,
    bands=[("crags", 0, 4, dict(level=4, paint="r", wall=True, wavy="s")),
           ("road", 10, 3, dict(paint="d", walk=True)),
           ("floor", 14, 6, dict(level=1, paint="p")),
           ("parapet", 20, 2, dict(level=2, paint="s")),
           ("rocks", 22, 3, dict(level=0, paint="r", wavy="s")),
           ("lanes", 25, 3, dict(water=True, wavy="n"))],
    features=[("store", (10, 4, 7, 4), dict(level=2, paint="w", flights=[13])),
              ("lookout", (31, 4, 7, 4), dict(level=2, paint="w", flights=[34]))]
             + [("embrasure", (x, 20, 3, 2), dict(level=1, paint="p")) for x in (10, 18, 27, 36, 46, 55)],
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road"), "cove": dict(at=(43, 3), dir="n", arrive=(43, 5), span=2)},
    spawn="west",
    anchors={"jar_1": "store@14", "jar_2": "lookout@35", "cannon_0": "floor.front@11", "cannon_1": "floor.front@28",
             "cannon_2": "floor.front@47", "jar_3": "road.s@39", "journal_battery": "floor@41", "jar_4": "floor@56"},
    props=[("pirate_cannon", 18, 18), ("pirate_cannon", 36, 18), ("pirate_cannon", 55, 18), ("powder_keg", 22, 15),
           ("powder_keg", 23, 15), ("powder_keg", 40, 15), ("barrel", 41, 15), ("crates", 14, 8), ("powder_keg", 11, 5),
           ("pirate_banner", 30, 12), ("pirate_banner", 50, 12), ("lantern_red", 8, 13), ("lantern_red", 26, 13),
           ("lantern_red", 44, 13), ("star_ballista", 32, 4)],
    flora={"road": dict(density=0.2), "rocks": dict(density=0.3), "floor": dict(density=0.0)},
    foes="auto")


# The Smugglers' Cove: a sea cave behind the battery's cliff, its floor of rock round an inlet of black water where the
# smugglers' boat lies at its jetty. Their goods are stacked along the walls; Gu, the Blackmast's purser now, hides on the
# ledge at the back among the crates with his chests. The crack back to the battery is at the cave's west end.
BM_SMUGGLERS_COVE = room(
    "bm_smugglers_cove", size=(44, 24), biome="cave", level=4,
    features=[("front", (0, 15, 44, 9), dict(level=1, paint="r")),               # the cave's low front, nothing hidden
              ("cave", (2, 2, 40, 19), dict(level=0, paint="d", shape="round")),
              ("passage", (0, 11, 12, 3), dict(level=0, paint="d", walk=True)),
              ("ledge", (25, 3, 12, 6), dict(level=1, paint="r", shape="round", flights=[31])),
              ("inlet", (14, 13, 30, 7), dict(water=True, shape="round")),
              ("jetty", (22, 12, 3, 5), dict(level=0, paint="w"))],
    stairs="auto",
    ways={"entry": ("w", 12)},
    spawn="entry",
    anchors={"lost_cove_target": "cave@20", "npc_gu_the_purser": "ledge@31", "chest_1": "ledge@34",
             "chest_ledge_mv_1": "ledge@28"},
    props=[("crates", 8, 4), ("sacks", 10, 4), ("crates", 13, 3), ("powder_keg", 16, 4), ("barrel", 17, 4),
           ("crates", 38, 6), ("sacks", 36, 9), ("lantern_red", 6, 9), ("lantern_red", 22, 6), ("lantern_red", 38, 10),
           ("boat", 26, 15), ("barrel", 20, 11)],
    flora={"density": 0.18},
    foes="auto")


# The Flagship Deck: Admiral Voss's flagship at anchor in the haven's deep water, its gangway from the battery's pier at
# the west. A broad deck of black-tarred boards under three black masts, the quarterdeck a level up at the stern, the
# bow pointing east where his strongbox waits; the open deck between is where he makes his stand.
BM_FLAGSHIP_DECK = room(
    "bm_flagship_deck", size=(52, 26), biome="blackmast", base="~",
    features=hull("deck", 6, 4, 30, 17, dict(level=2, paint="w"), bow=10, stern=2)
             + [("quarterdeck", (6, 4, 8, 6), dict(level=3, paint="w", flights=[9])),
                ("gangway", (0, 11, 7, 3), dict(level=2, paint="w", walk=True))],
    stairs="auto",
    ways={"west": ("w", 12)},
    spawn="west",
    anchors={"chest_1": (40, 12)},
    props=[("black_mast", 18, 8), ("black_mast", 30, 8), ("broken_mast", 40, 9), ("pirate_banner", 15, 18),
           ("pirate_banner", 34, 18), ("pirate_cannon", 37, 17), ("pirate_cannon", 37, 6), ("powder_keg", 13, 18),
           ("barrel", 12, 18), ("lantern_red", 7, 6), ("lantern_red", 13, 6), ("crates", 22, 5)],
    flora={},
    foes=[[(31, 12)]])

ROOMS = [BM_BLACKMAST_DOCKS, BM_GUNNERS_BATTERY, BM_SMUGGLERS_COVE, BM_FLAGSHIP_DECK]
