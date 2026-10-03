"""E1 room specs: Greyreed Hamlet, north of the Grey Pools (docs/architecture/room_engine.md; R1, the main story's path
past chapter 3). Grey Roofs and Cleansing the Well are played here: the grey lanterns on the hall's and the granary's
roofs, the well in the square."""
from content.rooms.spec import room

# Greyreed Hamlet: a grey, silent hamlet on the marsh. Its lane runs under a bank of dead trees past Elder Gao's hall,
# the two homes and the granary (a crate stack beside the hall and the granary is the way onto each roof, where the
# grey lanterns stand); the square south of the lane round the well, the shrine's yard to the east, and the boardwalk
# south over the reeds to the Grey Pools.
GH_HAMLET_SQUARE = room(
    "gh_hamlet_square", size=(56, 28), biome="grey_marsh",
    bands=[("bank", 0, 5, dict(level=1, paint="m")), ("lane", 12, 3, dict(paint="d", walk=True)),
           ("commons", 15, 8, dict(level=0)), ("reeds", 23, 5, dict(water=True, wavy=True))],
    features=[("square", (19, 15, 16, 7), dict(paint="p")), ("shrine_yard", (45, 15, 9, 5), dict(paint="p")),
              ("well", (25, 16, 3, 3), dict(level=1, paint="s")), ("well_water", (26, 17, 1, 1), dict(water=True)),
              ("boardwalk", (26, 21, 3, 7), dict(level=0, paint="w"))],
    ways={"marsh": ("s", 27)},
    spawn="marsh",
    props=[("house", 4, 8, "house_a"), ("hall", 14, 8, "grey_hall"), ("crates", 22, 10), ("house", 29, 8, "house_b"),
           ("storehouse", 41, 8, "granary"), ("crates", 45, 10), ("water_jar", 11, 10), ("drying_rack", 36, 10),
           ("barrel", 40, 10), ("laundry_line", 7, 17), ("net_rack", 12, 18), ("fish_basket", 38, 17)],
    paths=[("house_a", 12), ("grey_hall", 12), ("house_b", 12), ("granary", 12)],
    anchors={"grey_lantern_hall": (18, 8), "lit_lantern_hall": (18, 8), "grey_lantern_granary": (42, 8),
             "lit_lantern_granary": (42, 8), "well_cleanse": "well.s@26", "npc_hamlet_elder_gao": "square@30",
             "npc_hamlet_trader_min": "lane.s@44", "shrine_gh": "shrine_yard@50"},
    flora={"bank": dict(density=0.45)})

ROOMS = [GH_HAMLET_SQUARE]
