"""E1, the room engine: the biomes a generated room draws from (docs/architecture/room_engine.md).

A biome is the look a room's spec asks for by name: the ground under it (`base`), the paint of the flights the engine
cuts (`stair`), and its foliage pools by the role of a band (`flora`): `wall` a cliff's foot, `ground` a meadow or a
terrace, `walk` a road's verges, `water` the bank, the shallows and the open water. A spec's own `flora` names bands and
replaces the pool for those; `density` is how thick the scatter lies (pieces per two cells of edge). Two knobs a
biome may set (R1): `tree_share`, the share of trees where trees grow (0.6; at a cliff's foot two thirds of it), and
`tree_gap`, how far apart its trees stand (5 cells).

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
    # R1: the main story's path past chapter 3 (the Reed Marsh, Greyreed, the Bamboo Grove, Crane Falls, Cleansing Peak).
    # The living reed marsh (the Sunken Causeway, the hermit's pond): marsh grass, willows and reeds, cattails in the
    # shallows and lotus out on the water.
    "reed_marsh": {
        "base": "m", "stair": "w", "density": 0.32,
        "flora": {"wall": ["tree_willow", "bush_wide", "rock_mossy"],
                  "ground": ["tree_willow", "bush", "tall_grass", "ferns", "reeds"],
                  "walk": ["tall_grass", "reeds", "rock_small", "bush"],
                  "water": ["tree_willow", "reeds", "tall_grass", "cattails", "lotus_pads"]},
    },
    # Where the Hollowing has drunk the marsh (the Grey Pools, Greyreed Hamlet): dead trees and grey reeds over pale
    # marsh grass, stumps and fallen logs, cattails still in the shallows.
    "grey_marsh": {
        "base": "m", "stair": "w", "density": 0.3,
        "flora": {"wall": ["dead_tree", "rock_mossy", "grey_reeds"],
                  "ground": ["dead_tree", "grey_reeds", "tall_grass", "stump", "log", "rock_small"],
                  "walk": ["grey_reeds", "rock_small", "stump", "tall_grass"],
                  "water": ["dead_tree", "grey_reeds", "cattails", "lotus_pads"]},
    },
    # The Bamboo Grove: tall bamboo clumps over ferns and mossy rocks, short canes and tall grass along the paths.
    "bamboo": {
        "base": "g", "stair": "w", "density": 0.36, "tree_share": 0.8, "tree_gap": 3,
        "flora": {"wall": ["bamboo_grove", "rock_mossy", "ferns"],
                  "ground": ["bamboo_grove", "ferns", "bamboo", "rock_mossy", "tall_grass", "stump"],
                  "walk": ["bamboo", "ferns", "rock_small", "tall_grass"],
                  "water": ["bamboo_grove", "ferns", "cattails", "lotus_pads"]},
    },
    # Crane Falls: pines and maples on the rock round the pool, mossy boulders and ferns in the spray.
    "falls": {
        "base": "g", "stair": "s", "density": 0.32,
        "flora": {"wall": ["tree_pine", "rock_mossy", "ferns"],
                  "ground": ["tree_pine", "tree_maple", "bush_wide", "ferns", "rock_mossy", "tall_grass"],
                  "walk": ["ferns", "rock_small", "tall_grass"],
                  "water": ["tree_maple", "ferns", "cattails", "lotus_pads"]},
    },
    # Cleansing Peak: wind-bent pines on the ledges, bare rock and boulders, little grass; granite steps.
    "mountain": {
        "base": "g", "stair": "s", "density": 0.26,
        "flora": {"wall": ["tree_pine", "rock_mossy", "rock_small"],
                  "ground": ["tree_pine", "rock_mossy", "rock_small", "bush", "tall_grass"],
                  "walk": ["rock_small", "tall_grass"],
                  "water": ["tall_grass", "cattails"]},
    },
    # R2 ------------------------------------------------------------------------------------------------------------
    # The Drowned Shrine: dressed granite walls round flagstone halls the river half fills (`q`, a floor under shallow
    # water), moss and ferns where the silt settled, cattails in the shallows, lotus on the deep pools. Lamp-lit
    # (TopdownLight's "cave"). No trees: nothing grows tall under the river.
    "drowned_shrine": {
        "base": "p", "stair": "s", "density": 0.34,
        "flora": {"wall": ["ferns", "rock_mossy", "rock_small"],
                  "ground": ["ferns", "rock_mossy", "ferns", "rock_small"],
                  "walk": ["ferns", "rock_small"],
                  "water": ["cattails", "lotus_pads"]},
    },
    # Whitewater Gorge: grey rock walls and ledges, pines clinging to them, mossy boulders and ferns at their feet, the
    # river white over its stones, reeds only where it slows.
    "gorge": {
        "base": "r", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_pine", "rock_mossy", "ferns", "rock_small"],
                  "ground": ["tree_pine", "rock_mossy", "ferns", "bush", "tall_grass"],
                  "walk": ["rock_small", "ferns", "rock_mossy"],
                  "water": ["tree_pine", "ferns", "cattails"]},
    },
    # A grotto under the river (the Drowned Grotto, the Waterfall Cave): the cave's rock round a floor of wet sand and
    # shallows (`h`), ferns and mossy rocks by the walls, cattails in the shallows.
    "grotto": {
        "base": "r", "stair": "s", "density": 0.26,
        "flora": {"wall": ["rock_mossy", "ferns", "rock_small"],
                  "ground": ["ferns", "rock_mossy", "rock_small"],
                  "walk": ["ferns", "rock_small"],
                  "water": ["cattails", "ferns"]},
    },
    # R4: the peaks (Mist Peak, Summit Ridge, the Hidden Vale; the Crane Cliffs take R1's `mountain`; Act II's
    # Rimefrost Heights reuses them).
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
                  "ground": ["tree_plum", "tree_camphor", "tree_maple", "tree_pine", "bush_azalea", "bush", "ferns", "tall_grass"],
                  "walk": ["bush_azalea", "rock_small", "ferns"],
                  "water": ["tree_willow", "cattails", "lotus_pads", "tall_grass"]},
    },
    # R5 ------------------------------------------------------------------------------------------------------------
    # The Tidebreak Front's grey fields past the Bastion (the Greyfall Breach, the Hollow Wake, the Drone Hive): bare grey
    # rock where the Tide has drunk the land, dead trees and grey reeds, stumps, fallen logs and broken stone, a little
    # grass still green where it sheltered; the drone hives are placed by the rooms.
    "tidebreak": {
        "base": "r", "stair": "s", "density": 0.26,
        "flora": {"wall": ["dead_tree", "rock_small", "rock_mossy"],
                  "ground": ["dead_tree", "grey_reeds", "rock_small", "stump", "log", "grey_reeds", "tall_grass"],
                  "walk": ["grey_reeds", "rock_small", "stump"],
                  "water": ["grey_reeds", "dead_tree", "cattails"]},
    },
    # A fortress of the Wardens (the Tidebreak Bastion): dressed granite and flagstones, little that grows, weeds in the
    # joints and stones fallen from the walls.
    "bastion": {
        "base": "p", "stair": "s", "density": 0.14,
        "flora": {"wall": ["rock_small", "tall_grass", "rock_mossy"],
                  "ground": ["rock_small", "tall_grass", "bush"],
                  "walk": ["rock_small"],
                  "water": ["tall_grass", "cattails"]},
    },
    # R7 ------------------------------------------------------------------------------------------------------------
    # Act II's dry country east of Nine Peaks (the art: tools/art/topdown/arid.py, none of it of the foliage kit, so the
    # ground laid after the scatter runs under every piece). Nine Peaks itself takes R3's `sect_terraces`.
    # The Gale Canyons: the canyon's floor bare red earth (R7's `earth` over its `lowest` level), every ledge, mesa and
    # wall above it sandstone (decision 44's sand, whose faces are its layered banks; the earth's would show a grass
    # lip), the trail a sandy wash; banded sandstone boulders and wind-carved hoodoos, grey wind-killed trees, dry
    # scrub; plank steps up the ledges, sandstone at their cheeks.
    "canyon": {
        "base": "g", "stair": "w", "density": 0.26, "cheek": "red_rock",
        "flora": {"wall": ["red_rock", "dead_tree", "dry_scrub", "hoodoo"],
                  "ground": ["red_rock", "dry_scrub", "dead_tree", "hoodoo", "dry_scrub"],
                  "walk": ["dry_scrub", "red_rock"],
                  "water": ["dry_scrub", "cattails", "tall_grass"]},
        "ground": {"sand": ["*"], "earth": ["lowest"]},
    },
    # The Sunscar Desert: decision 44's sand over everything (laid after the scatter, so it runs under every piece of the
    # arid kit), the caravan track trodden red earth; dunes and sandstone outcrops, cactus clumps, dry scrub, bleached
    # bones, a dead tree now and then; palms, reeds and grass only where there is water.
    "desert": {
        "base": "g", "stair": "s", "density": 0.22, "cheek": "red_rock",
        "flora": {"wall": ["red_rock", "dry_scrub", "cactus", "ribcage"],
                  "ground": ["dry_scrub", "cactus", "red_rock", "dry_scrub", "ribcage", "dead_tree"],
                  "walk": ["dry_scrub", "red_rock"],
                  "water": ["palm", "tall_grass", "cattails", "dry_scrub"]},
        "ground": {"sand": ["*"], "earth": ["walk"]},
    },
    # The Tomb of Sunscar: flagstone halls (`p`) inside walls of cut sandstone (a spec's walls of sand, whose faces are
    # its layered banks), sand drifted in through the cracks (`g` drifts the sand covers after the scatter), bones and
    # fallen stone in the drifts and nothing green; granite steps.
    "tomb": {
        "base": "p", "stair": "s", "density": 0.24,
        "flora": {"wall": ["ribcage", "red_rock"], "ground": ["ribcage", "red_rock"], "walk": ["red_rock"],
                  "water": ["red_rock"]},
        "ground": {"sand": ["*"]},
    },
    # Ironroot Hold: the clan's mountain of grey rock, the iron-root trees' roots breaking out of it, pines on its
    # ledges, boulders and stumps where the clan cut timber; trampled earth in its yards (a spec's `d`), its cavern's
    # floor by the walls rock rubble (`rubble`). Lamp and forge lit inside.
    "iron_hold": {
        "base": "r", "stair": "s", "density": 0.26, "rubble": True,
        "flora": {"wall": ["roots", "tree_pine", "boulder", "rock_small"],
                  "ground": ["tree_pine", "roots", "boulder", "rock_small", "stump", "rock_mossy"],
                  "walk": ["rock_small", "stump"],
                  "water": ["cattails", "ferns"]},
    },
    # R6: Act II's first zones, the Azure Expanse. Later zones reuse them (Nine Peaks the port's, the Gale Canyons the
    # plains', the Skyport Wreck the port's and the heights').
    # Cloudgate Port: a sky harbour's town on a floating island: paved streets and plank wharves, its lawns and the
    # island's rim planted with pines, plum and azaleas, hedges along the walks, rocks where the island's stone shows;
    # the sea of cloud past its south rim (topdown_life.VISTAS).
    "sky_port": {
        "base": "p", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_pine", "rock_mossy", "bush"],
                  "ground": ["tree_pine", "tree_plum", "bush_azalea", "bush", "hedge_2", "rock_small"],
                  "walk": ["bush", "bush_azalea", "rock_small"],
                  "water": ["tall_grass", "cattails", "lotus_pads"]},
    },
    # The Thunderhorn Plains: open storm grass to the horizon, few trees (wind-bent pines and lightning-killed dead
    # ones), boulders and mossy rocks the storms split, tall grass along the herds' trails.
    "storm_plains": {
        "base": "g", "stair": "s", "density": 0.26, "tree_share": 0.3, "tree_gap": 7,
        "flora": {"wall": ["tree_pine", "boulder", "rock_mossy", "tall_grass"],
                  "ground": ["tall_grass", "tree_pine", "dead_tree", "boulder", "rock_small", "bush", "tall_grass"],
                  "walk": ["tall_grass", "rock_small", "tall_grass"],
                  "water": ["tall_grass", "cattails"]},
    },
    # Mirrorwater Lake: wide still water under the sky, willows and maples on its shores and islands, mossy rocks, lotus
    # out on the water; the Reedless Shore earns its name (no reeds, no cattails).
    "mirror_lake": {
        "base": "g", "stair": "s", "density": 0.3,
        "flora": {"wall": ["tree_willow", "rock_mossy", "bush_wide"],
                  "ground": ["tree_willow", "tree_maple", "bush", "tall_grass", "rock_mossy", "ferns"],
                  "walk": ["tall_grass", "rock_small", "bush"],
                  "water": ["tree_willow", "tall_grass", "lotus_pads"]},
    },
    # R9 ------------------------------------------------------------------------------------------------------------
    # The star field's end (the art: tools/art/topdown/starfield.py, none of it of the foliage kit). R5's `bastion` (the
    # Wardens' Tidebreak fortress) is the Citadel's stone, and R5's cloud sea lies under every island's brink.
    # The Star Warden Citadel: the Wardens' white granite and flagstones on the Field's central island, its gardens kept
    # (pines, plum and hedges in their beds), star crystals where the island's rock shows, weeds in the joints; a
    # flight's open cheeks lined with star lanterns.
    "citadel": {
        "base": "p", "stair": "s", "density": 0.2, "cheek": "star_lantern",
        "flora": {"wall": ["tree_pine", "rock_mossy", "bush"],
                  "ground": ["tree_pine", "tree_plum", "hedge_2", "bush", "bush_azalea", "rock_mossy"],
                  "walk": ["bush", "rock_small"],
                  "water": ["tall_grass", "cattails", "lotus_pads"]},
    },
    # The Orbit Ruins: the first Wardens' observatory-temple broken and hanging in the dark, its rings and floors of
    # dressed granite on the island's grey rock; star crystals grown out of the rock, mossy fallen stones, ferns and the
    # odd grey tree in the cracks (the floating masonry, `orbit_stone`, is placed by the rooms).
    "orbit_ruins": {
        "base": "r", "stair": "s", "density": 0.28, "cheek": "boulder",
        "flora": {"wall": ["star_crystal", "rock_mossy", "rock_small", "ferns"],
                  "ground": ["star_crystal", "rock_mossy", "rock_small", "ferns", "dead_tree", "star_crystal"],
                  "walk": ["rock_small", "ferns", "star_crystal"],
                  "water": ["star_crystal", "rock_small"]},
    },
    # The Ashen Reach: the burnt plain where the Ashborn camp, dark earth under drifts of ash (the earth laid over all
    # after the scatter, R7's `earth`), its rises grey with ash; charred trees, beds of embers still glowing, boulders.
    # No piece of the foliage kit: the earth is never laid under one, and it would keep a tuft of meadow round it.
    "ashen": {
        "base": "g", "stair": "s", "density": 0.3, "cheek": "boulder",
        "flora": {"wall": ["charred_tree", "boulder", "ash_drift"],
                  "ground": ["charred_tree", "ash_drift", "embers", "boulder", "ash_drift"],
                  "walk": ["embers", "ash_drift", "boulder"],
                  "water": ["boulder", "ash_drift"]},
        "ground": {"earth": ["*"]},
    },
    # The Nebula Deep: reefs of dark rock and pale nebula sand in the luminous sea the nebula runs as (its water), coral
    # trees with their pink and cyan crowns, nebula coral and star crystals on the reefs, void crabs' shells cast up.
    "nebula": {
        "base": "r", "stair": "s", "density": 0.3, "cheek": "boulder",
        "flora": {"wall": ["coral_tree", "nebula_coral", "rock_mossy", "star_crystal"],
                  "ground": ["coral_tree", "nebula_coral", "star_crystal", "rock_small", "nebula_coral", "void_shell"],
                  "walk": ["nebula_coral", "rock_small", "ferns"],
                  "water": ["coral_tree", "nebula_coral", "rock_small"]},
    },
    # The Lantern Heart: the first lantern's halls, warm flagstones under bronze, gilt and the flame's own light; star
    # crystals where the old rock shows, blossom in the few beds kept by whoever keeps the Heart.
    "lantern_heart": {
        "base": "p", "stair": "s", "density": 0.2,
        "flora": {"wall": ["star_crystal", "rock_small"],
                  "ground": ["star_crystal", "tree_plum", "bush_azalea", "star_crystal", "tall_grass"],
                  "walk": ["star_crystal", "rock_small"],
                  "water": ["star_crystal", "lotus_pads"]},
    },
    # A vessel's deck on the Starsea (the crossings): planks over the sea, nothing growing; a flight's open cheeks are
    # closed by barrels lashed to the deck.
    "starsea": {
        "base": "~", "stair": "w", "density": 0.0, "cheek": "barrel",
        "flora": {"wall": [], "ground": [], "walk": [], "water": []},
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
