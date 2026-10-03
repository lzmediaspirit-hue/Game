"""E1 room specs (R8): the Skyport Wreck, the broken sky-port on the Riven Peak's rock at the Expanse's edge, where the
Wreck Run makes port (docs/architecture/room_engine.md). Chapter 15's The Skyport Wreck (the Broken Pier, Gu in chains
on the Pirate Deck), chapter 16's Lu's Last Page (the Riven Peak) and Stars Beyond (the Starsea Launch). The rock falls
away past every room's south edge into the cloud sea; the old port's paving, its snapped piers and its wrecked hulls lie
on it. The side view's ledges (100 to 320 units) are hull decks, outcrops and crags here, a flight up each."""
from content.rooms.spec import room
from content.rooms.specs.skysea import hull
from content.rooms.specs.story import octagon

# The Broken Pier: where the skiffs from Cloudgate come in. The one whole pier runs out from the old port's road to the
# brink at the west, the dock at its end; two more are snapped off short. North of the road the port's upper quay under
# the Riven Peak's cliff, where the great junk lies broken in two, its stern and its bow three levels up on the paving,
# its bare ribs in the gap between (the two chests the pirates stripped from it on its decks); a rock outcrop at each
# end. South of the road the rock falls a level to the brink over the clouds. The deserters of the Nine Peaks and the
# pirates prowl the road.
SW_BROKEN_PIER = room(
    "sw_broken_pier", size=(64, 28), biome="skyport", level=1,
    bands=[("crown", 0, 3, dict(level=5, paint="r", wall=True, wavy="s")),
           ("quay", 3, 10, dict(level=2, paint="p", flights=[18, 49])),        # the old port's quay wall runs straight
           ("apron", 13, 2, dict(paint="p")),
           ("road", 15, 3, dict(paint="p", walk=True)),
           ("lower", 18, 10, dict(level=0, wavy="n"))],
    features=hull("wreck", 26, 3, 10, 7, dict(level=3, paint="w", flights=[30]), bow=0, stern=4)
             + hull("wreck_fore", 40, 4, 6, 6, dict(level=3, paint="w", flights=[42]), bow=6)
             + [("outcrop", (8, 3, 8, 5), dict(level=3, paint="r", shape="round", flights=[12])),
                ("outcrop_2", (53, 3, 8, 6), dict(level=3, paint="r", shape="round", flights=[57])),
                ("pier", (3, 18, 5, 10), dict(level=1, paint="w")),                # the whole pier, out to the brink
                ("pier_2", (20, 18, 3, 6), dict(level=1, paint="w")),              # and two snapped short
                ("pier_3", (47, 18, 3, 4), dict(level=1, paint="w")),
                ("paving", (11, 19, 8, 4), dict(paint="p", shape="round")),        # the lower quay's paving, broken
                ("paving_2", (28, 19, 12, 5), dict(paint="p", shape="round")),
                ("paving_3", (52, 19, 9, 4), dict(paint="p", shape="round"))],
    stairs="auto",
    ways={"east": ("e", "road")},
    spawn=(5, 21),
    anchors={"dock_wreck": "pier.front@5", "shrine_sw_pier": "verge.n@11", "sign_sw": "lower@10", "jar_2": "outcrop@12",
             "ore_1": "quay.front@38", "chest_ledge_mv_1": "wreck@28", "chest_cloud_mv": "wreck_fore@43",
             "jar_4": "verge.s@41", "crate_3": "outcrop_2@57", "crate_5": "lower@57"},
    props=[("broken_mast", 31, 8), ("broken_mast", 44, 9), ("hull_ribs", 36, 9), ("starsea_anchor", 19, 9),
           ("lantern_red", 27, 6), ("lantern_red", 34, 5), ("pirate_banner", 25, 14), ("pirate_banner", 39, 14),
           ("post", 3, 27), ("post", 7, 27), ("post", 20, 23), ("post", 22, 23), ("post", 47, 21), ("post", 49, 21),
           ("crates", 23, 19), ("barrel", 25, 19), ("hull_ribs", 53, 24), ("broken_mast", 31, 25)],
    flora={"quay": {"kinds": ["rock_small", "tall_grass", "boulder", "dead_tree"], "density": 0.3},
           "apron": dict(density=0.0), "lower": dict(density=0.32)},
    foes="auto")


# The Pirate Deck: the pirates' junk moored in the old port's berth under the cliff, its deck three levels over the quay
# with its bow pointing east, the stern castle a level higher at the west (their strongbox), two black masts and a
# broken one, their ballistas at the rail; two gangways come down to the quay road, which runs east and west under it.
# Gu sits chained by the bow mast while The Skyport Wreck is under way. South of the road the rock falls a level to the
# brink over the clouds, an old anchor and a hull's ribs left on it.
SW_PIRATE_DECK = room(
    "sw_pirate_deck", size=(64, 28), biome="skyport", level=1,
    bands=[("crown", 0, 2, dict(level=5, paint="r", wall=True)),
           ("road", 16, 3, dict(paint="p", walk=True)),
           ("lower", 19, 9, dict(level=0, wavy="n"))],
    features=hull("deck", 10, 3, 42, 9, dict(level=3, paint="w", flights=[22, 44]), bow=8)
             + [("stern", (10, 3, 9, 5), dict(level=4, paint="w", flights=[14])),
                ("paving", (15, 20, 10, 4), dict(paint="p", shape="round")),      # the old berth's paving, broken
                ("paving_2", (36, 19, 12, 5), dict(paint="p", shape="round"))],
    stairs="auto",
    ways={"west": ("w", "road"), "east": ("e", "road")},
    spawn="west",
    anchors={"pirate_strongbox": "stern@13", "npc_gu_in_chains": "deck@46", "jar_1": "deck@27", "jar_2": "stern@17",
             "chest_ledge_mv_1": "deck@33", "page_sovereign_settling_pill_3": "verge.s@23", "lost_deck_cutter": "verge.s@42",
             "jar_3": "lower@31", "jar_4": "verge.n@38", "jar_5": "lower@57"},
    props=[("black_mast", 24, 8), ("black_mast", 36, 8), ("broken_mast", 49, 8), ("star_ballista", 19, 10),
           ("star_ballista", 40, 10), ("pirate_banner", 6, 15), ("pirate_banner", 31, 15), ("pirate_banner", 57, 15),
           ("barrel", 21, 4), ("crates", 29, 4), ("barrel", 31, 4), ("powder_keg", 51, 9), ("powder_keg", 52, 8),
           ("lantern_red", 11, 7), ("lantern_red", 50, 4), ("hull_ribs", 6, 22), ("starsea_anchor", 49, 22)],
    flora={"lower": dict(density=0.32)},
    foes="auto")


# The Riven Peak: the summit above the wreck. The trail crosses the peak's shoulder; north of it the crags climb in two
# steps (the first star-sighting stone and a chest on the lower, the second stone and a chest on the higher); south of
# it the slope falls toward the brink, split by the gully that gives the peak its name, Lu's last page on the knoll east
# of it where the stars are clearest, the third stone by the way east. Rock spires and dead trees stand in the wind.
SW_RIVEN_PEAK = room(
    "sw_riven_peak", size=(64, 30), biome="skyport", level=2,
    bands=[("crown", 0, 3, dict(level=7, paint="r", wall=True, wavy="s")),
           ("crags", 3, 10, dict(level=3, paint="r", wavy="s", flights=[8])),
           ("trail", 14, 3, dict(paint="d", walk=True)),
           ("brink", 25, 5, dict(level=0)),
           ("slope", 17, 9, dict(level=1, wavy="s"))],
    features=[("ledge", (12, 3, 11, 7), dict(level=4, paint="r", shape="round", flights=[17])),
              ("ledge_2", (33, 3, 12, 5), dict(level=5, paint="r", shape="round", flights=[39])),
              ("gully", (23, 17, 7, 11), dict(level=0, paint="r", shape="round")),   # where the peak is riven
              ("knoll", (46, 18, 12, 6), dict(level=2, paint="r", shape="round", flights=[52]))],
    stairs="auto",
    ways={"west": ("w", "trail"), "east": ("e", "trail")},
    spawn="west",
    anchors={"sight_riven_a": "ledge@17", "jar_1": "ledge@14", "chest_cloud_mv": "ledge@21", "sight_riven_b": "ledge_2@39",
             "chest_4": "ledge_2@36", "crate_2": "verge.s@32", "journal_riven": "knoll@51", "sight_riven_c": "verge.n@55",
             "jar_3": "slope@37"},
    props=[("broken_mast", 30, 12), ("rock_spire", 3, 9), ("rock_spire", 47, 10), ("rock_spire", 60, 7),
           ("rock_spire", 9, 21), ("rock_spire", 33, 22), ("starsea_anchor", 15, 22)],
    flora={"crags": dict(density=0.36), "slope": dict(density=0.34), "brink": dict(density=0.4)},
    foes="auto")


# The Starsea Launch: the peak's last point, a paved terrace over the cloud sea where the skiffs set out for the Lantern
# Star Field. The launch ring stands on its dais in the middle of a round floor of granite, its lamps following a line
# of stars; Warden He keeps it; the shrine, a little garden and the armillary west of it, the teleport stone east; a
# timber pier runs out to the brink at the east end, the skiff moored at its tip.
SW_STARSEA_LAUNCH = room(
    "sw_starsea_launch", size=(48, 26), biome="skyport", level=1,
    bands=[("crown", 0, 3, dict(level=5, paint="r", wall=True, wavy="s")),
           ("terrace", 3, 17, dict(level=1, paint="p")),
           ("road", 15, 3, dict(paint="p", walk=True)),
           ("brink", 21, 5, dict(level=0))],
    features=octagon("ring", 19, 4, 15, 11, 3, dict(paint="s"))                    # the launch ring's floor
             + [("dais", (24, 9, 5, 3), dict(level=2, paint="s")),
                ("garden", (2, 3, 9, 6), dict(level=2, paint="g", shape="round")),
                ("pier", (39, 18, 5, 8), dict(level=1, paint="w"))],
    stairs="auto",
    ways={"west": ("w", "road")},
    spawn="west",
    anchors={"launch_ring": "dais@26", "dock_launch": "pier.front@41", "shrine_sw_launch": "terrace@14",
             "stone_skyport": "verge.n@36", "npc_launch_warden_he": "verge.s@24"},
    props=[("armillary", 9, 11), ("starsea_anchor", 5, 19), ("lantern", 20, 8), ("lantern", 32, 8), ("lantern", 20, 13),
           ("lantern", 32, 13), ("star_lantern", 38, 18), ("star_lantern", 44, 18), ("post", 39, 25), ("post", 43, 25)],
    flora={"terrace": {"kinds": ["rock_small", "tall_grass"], "density": 0.14},
           "garden": {"kinds": ["tree_pine", "bush", "tall_grass"], "density": 0.9}, "brink": dict(density=0.36)},
    foes="auto")

ROOMS = [SW_BROKEN_PIER, SW_PIRATE_DECK, SW_RIVEN_PEAK, SW_STARSEA_LAUNCH]
