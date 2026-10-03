"""E1, the room engine: the biomes a generated room draws from (docs/architecture/room_engine.md).

A biome is the look a room's spec asks for by name: the ground under it (`base`), the paint of the flights the engine
cuts (`stair`), and its foliage pools by the role of a band (`flora`): `wall` a cliff's foot, `ground` a meadow or a
terrace, `walk` a road's verges, `water` the bank, the shallows and the open water. A spec's own `flora` names bands and
replaces the pool for those; `density` is how thick the scatter lies (pieces per two cells of edge).

The kinds are the foliage kit's (data/topdown/proto_tileset.json, `foliage`); each grows where the kit says (a tree or a
bush on meadow, flowers, marsh or rock; cattails on the land or in the shallows; lotus pads on the water)."""

BIOMES = {
    # The valley's meadows and roads (the Willow Path, the Caravan Road): plum, peach and camphor over the meadow, pines
    # under the rock, fences and bushes along the road, willows and tall grass by the water.
    "valley_road": {
        "base": "g", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_pine", "bush", "rock_mossy"],
                  "ground": ["tree_camphor", "tree_plum", "bush", "bush_azalea", "tall_grass"],
                  "walk": ["bush", "rock_small", "tall_grass", "fence_3"],
                  "water": ["tree_willow", "tall_grass", "cattails", "lotus_pads"]},
    },
    # A river shore (Deepwater Bend): willows and reeds, sand along the water, lotus out on it.
    "river_shore": {
        "base": "g", "stair": "s", "density": 0.32,
        "flora": {"wall": ["tree_pine", "bush_wide", "rock_mossy"],
                  "ground": ["tree_willow", "tree_maple", "bush", "ferns", "tall_grass"],
                  "walk": ["bush", "rock_small", "tall_grass"],
                  "water": ["tree_willow", "tall_grass", "cattails", "lotus_pads"]},
    },
    # A bandits' stockade in the hills at dusk: trampled earth inside a timber palisade, few plants, rocks and stumps.
    "stockade": {
        "base": "d", "stair": "w", "density": 0.22,
        "flora": {"wall": ["tree_pine", "rock_small", "stump"],
                  "ground": ["rock_small", "stump", "tall_grass", "bush"],
                  "walk": ["rock_small", "stump"],
                  "water": ["cattails", "tall_grass"]},
    },
    # A cave under the hills (the Mudwater tunnels): the rock mass round an earthen floor (`rubble`: the floor by a wall
    # is the wall's rock rubble, where the mossy rocks and ferns grow), cattails in the seep pools. Lamp-lit
    # (TopdownLight's "cave").
    "cave": {
        "base": "r", "stair": "s", "density": 0.2, "rubble": True,
        "flora": {"wall": ["rock_mossy", "rock_small", "ferns"],
                  "ground": ["rock_small", "ferns", "rock_mossy"],
                  "walk": ["rock_small", "ferns"],
                  "water": ["cattails", "ferns"]},
    },
    # R4: the peaks (Crane Cliffs, Mist Peak, Summit Ridge, the Hidden Vale; Act II's Rimefrost Heights reuses them).
    # The high mountains (the Crane Cliffs): bare rock shelves and thin alpine turf, wind-bent pines at the crags' feet,
    # mossy boulders and ferns; no broadleaf tree grows this high.
    "high_mountain": {
        "base": "g", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_pine", "rock_mossy", "rock_small", "ferns"],
                  "ground": ["tree_pine", "rock_mossy", "bush_wide", "ferns", "tall_grass", "rock_small"],
                  "walk": ["rock_small", "tall_grass", "ferns"],
                  "water": ["tall_grass", "cattails", "ferns"]},
    },
    # Mist Peak: the slopes in the soul-mist, pines and grey dead trees, ferns and wet turf (the mist lies over a
    # spec's `m` hollows, TopdownAtmosphere), mossy stones along the trail.
    "mist_peak": {
        "base": "g", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_pine", "dead_tree", "rock_mossy", "ferns"],
                  "ground": ["tree_pine", "dead_tree", "rock_mossy", "ferns", "tall_grass", "bush"],
                  "walk": ["rock_small", "ferns", "tall_grass"],
                  "water": ["tall_grass", "cattails", "ferns"]},
    },
    # The snow line (Summit Ridge): every floor under fresh snow and the walks trodden to packed snow (decision 44,
    # its `ground` the default for a spec that names none: "*" the whole room, "walk" the walks and their cuts), pines
    # and dead trees standing out of it, boulders and bare rocks.
    "snowfield": {
        "base": "r", "stair": "s", "density": 0.24,
        "flora": {"wall": ["tree_pine", "boulder", "rock_small"],
                  "ground": ["tree_pine", "dead_tree", "boulder", "rock_small", "rock_mossy"],
                  "walk": ["rock_small", "boulder"],
                  "water": ["rock_small"]},
        "ground": {"snow": ["*"], "snowpack": ["walk"]},
    },
    # The Hidden Vale: a sheltered sect valley among the peaks, plum and peach blossom, maples and bamboo, azaleas on
    # the lawns, willows and lotus on its water.
    "hidden_vale": {
        "base": "g", "stair": "s", "density": 0.32,
        "flora": {"wall": ["tree_pine", "bamboo_grove", "rock_mossy", "ferns"],
                  "ground": ["tree_plum", "tree_peach", "tree_maple", "bush_azalea", "bush", "ferns", "tall_grass"],
                  "walk": ["bush_azalea", "rock_small", "ferns"],
                  "water": ["tree_willow", "cattails", "lotus_pads", "tall_grass"]},
    },
    # Generic meadow (the default).
    "": {
        "base": "g", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_pine", "bush"], "ground": ["tree_camphor", "bush", "tall_grass"],
                  "walk": ["bush", "rock_small"], "water": ["tree_willow", "cattails", "lotus_pads"]},
    },
}


def get(name):
    if name not in BIOMES:
        raise ValueError("no biome %r (biomes.py: %s)" % (name, ", ".join(sorted(k for k in BIOMES if k))))
    return BIOMES[name]
