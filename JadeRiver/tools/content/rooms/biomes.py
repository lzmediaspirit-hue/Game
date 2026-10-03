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
    # R3 -------------------------------------------------------------------------------------------------------------
    # A sect's terraced herb gardens on the mountain (the Cloud Sect's Herb Terraces): plum, pine and maple over the
    # terraces, hedges and azaleas along their lips, pines and mossy rocks under the crags, reeds round a terrace pond.
    "sect_terraces": {
        "base": "g", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_pine", "bush", "rock_mossy"],
                  "ground": ["tree_plum", "tree_pine", "tree_maple", "hedge_3", "bush_azalea", "bush", "ferns"],
                  "walk": ["bush", "rock_small", "tall_grass"],
                  "water": ["tall_grass", "cattails", "lotus_pads"]},
    },
    # A quarry in the hills behind Stoneford (Stonewall Quarry): bare cut rock, gravel and spoil, a few pines and
    # stumps where the trees were felled for the scaffolds, rocks along the haul roads.
    "quarry": {
        "base": "r", "stair": "s", "density": 0.24,
        "flora": {"wall": ["tree_pine", "rock_small", "stump"],
                  "ground": ["tree_pine", "rock_small", "rock_mossy", "stump", "tall_grass", "bush"],
                  "walk": ["rock_small", "stump"],
                  "water": ["cattails", "tall_grass"]},
    },
    # A bamboo grove (the Beast Trial Grove north of Market Street): bamboo thick round a mossy clearing, ferns and
    # mossy rocks under it, grass along the path.
    "bamboo_clearing": {
        "base": "g", "stair": "s", "density": 0.36,
        "flora": {"wall": ["bamboo_grove", "rock_mossy", "ferns"],
                  "ground": ["bamboo_grove", "tree_maple", "ferns", "rock_mossy", "tall_grass", "bush"],
                  "walk": ["ferns", "tall_grass", "rock_small"],
                  "water": ["cattails", "tall_grass", "lotus_pads"]},
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
