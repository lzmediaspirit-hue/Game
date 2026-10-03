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
    # A cave under the hills (the Mudwater tunnels): rock walls round an earthen floor, mossy rocks, ferns in the damp,
    # cattails in the seep pools. Lamp-lit (TopdownLight's "cave").
    "cave": {
        "base": "d", "stair": "s", "density": 0.2,
        "flora": {"wall": ["rock_mossy", "rock_small", "ferns"],
                  "ground": ["rock_small", "ferns", "rock_mossy"],
                  "walk": ["rock_small", "ferns"],
                  "water": ["cattails", "ferns"]},
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
