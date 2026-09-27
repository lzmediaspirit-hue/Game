"""P13a · The technique grammar (docs/technique_plan.md §3): an art is FORM x FAMILY x ELEMENT x PATH x RING.

Only tables live here; tools/data/technique_gen.py walks the cells of the trees and writes the rows, and
tools/data/technique_hand.py holds the arts made by hand (today's 56 re-homed, the keystones, the Dao arts and the
Lost Arts). Every name the generator builds comes from the word lists below, so a translation translates the lists
and the patterns, not four thousand names.
"""

# ----------------------------------------------------------------------------------------------------------------------
# Rings (§1.4, §3.5): one per grade band. grade, the band's first Level, the act, vfx.tier, extra targets, reach bonus.
RINGS = {
    1: ("common", 0, 1, 1, 0, 0.0), 2: ("earth", 19, 1, 2, 0, 0.0), 3: ("heaven", 37, 1, 3, 0, 0.0), 4: ("mystic", 55, 1, 3, 0, 0.0),
    5: ("spirit", 64, 2, 4, 1, 0.02), 6: ("sage", 73, 2, 4, 1, 0.04), 7: ("sovereign", 82, 3, 5, 1, 0.06), 8: ("will", 91, 3, 5, 1, 0.08),
    9: ("sphere", 100, 4, 6, 2, 0.10), 10: ("law", 109, 4, 6, 2, 0.12), 11: ("monarch", 121, 5, 7, 2, 0.14),
    12: ("inner_heaven", 141, 5, 7, 2, 0.16), 13: ("genesis", 166, 6, 7, 2, 0.18),
}
GRADE_BONUS = {"common": 0.0, "earth": 0.10}   # every later grade +20% (the research's skill bucket; flat from ring 3)
ACT_EDGE = {1: 4, 2: 6, 3: 8, 4: 10, 5: 12, 6: 13}   # the last ring of each act: its notables and keystones
BUILT_ACT = 3                                          # v1.2.x builds Acts I-III; later rings are generated and locked
# The form budget of each ring (§3.5, re-tuned by P13a against P12's par character, §6.1): the multiplier of a ring's
# art over its form's ring-1 line, before the grade. It rises through Act I as the heavier arts open and eases after it
# as mastery, the Dao, the Qi edge and the tree carry more of the technique's lead over a basic blow.
RING_BUDGET = {1: 0.94, 2: 1.03, 3: 1.13, 4: 1.45, 5: 1.41, 6: 1.30, 7: 1.25, 8: 1.20, 9: 1.18, 10: 1.10, 11: 0.99, 12: 0.83, 13: 0.72}


def grade_bonus(ring):
    return GRADE_BONUS.get(RINGS[ring][0], 0.20)


# ----------------------------------------------------------------------------------------------------------------------
# Trees (§2.1): the nine elements techniques use, Space from ring 7 and Time from ring 9. key: (element, first ring, Dao).
TREES = {
    "wood": ("wood", 1, "wood"), "fire": ("fire", 1, "fire"), "earth": ("earth", 1, "earth"), "metal": ("metal", 1, "metal"),
    "water": ("water", 1, "water"), "wind": ("wind", 1, "wind"), "thunder": ("thunder", 1, "thunder"), "soul": ("soul", 1, "soul"),
    "formless": ("none", 1, ""), "space": ("space", 7, "space"), "time": ("time", 9, "time"),
}
TREE_OF = {v[0]: k for k, v in TREES.items()}   # element -> tree

# Sectors (§4.1): sixteen, in four kin groups of four. v1.3 brings the families marked with its version; until then a
# tree has twelve. dao: the weapon Dao the gate shows ("" for the free hand: its arts take the tree's own Dao).
KIN = {"voice": ("any", "fists", "flute", "bell"), "edges": ("jian", "dual_blades", "short_blade", "heavy_sabre"),
       "reach": ("spear", "staff", "whip", "rope_dart"), "distance": ("bow", "fan", "umbrella", "brush")}
SECTORS = [f for k in KIN for f in KIN[k]]
KIN_OF = {f: k for k in KIN for f in KIN[k]}
LATER_FAMILIES = {"dual_blades": "1.3", "whip": "1.3", "rope_dart": "1.3", "umbrella": "1.3"}
FAMILY_DAO = {"fists": "fist", "jian": "sword", "spear": "spear", "short_blade": "blade", "staff": "staff", "bow": "bow",
              "heavy_sabre": "blade", "fan": "fan", "flute": "music", "brush": "brush", "bell": "music",
              "dual_blades": "blade", "whip": "whip", "rope_dart": "blade", "umbrella": "umbrella"}
# A family's reach for its arts (techniques.py's table), and its two affinity paths (§2.4).
FAMILY_REACH = {"any": 110, "fists": 70, "flute": 240, "bell": 200, "jian": 100, "dual_blades": 80, "short_blade": 70,
                "heavy_sabre": 110, "spear": 150, "staff": 120, "whip": 170, "rope_dart": 200, "bow": 480, "fan": 180,
                "umbrella": 130, "brush": 150}
AFFINITY = {"any": ("blood", "buddhist"), "fists": ("body", "buddhist"), "flute": ("buddhist", "poison"), "bell": ("buddhist", "confucian"),
            "jian": ("blood", "confucian"), "dual_blades": ("blood", "poison"), "short_blade": ("blood", "poison"), "heavy_sabre": ("body", "blood"),
            "spear": ("body", "confucian"), "staff": ("body", "buddhist"), "whip": ("body", "poison"), "rope_dart": ("body", "poison"),
            "bow": ("poison", "confucian"), "fan": ("poison", "confucian"), "umbrella": ("buddhist", "confucian"), "brush": ("buddhist", "confucian")}

# ----------------------------------------------------------------------------------------------------------------------
# The 24 forms (§3.2). role: the class rule 3 reads (burst, area, control, self, allies, movement); shape: vfx.shape;
# type: damage type ("qi*" is Qi, or physical for the bow); hits x targets; the ring-1 multiplier line; cooldown; Qi;
# pose preferences (cN: the family's N-th combo step; a literal action when the family's combo has it, or always for
# jump and meditate_burst); the families that can draw it; the first ring it opens on; extra row fields.
F = {}


def form(fid, role, shape, dtype, hits, targets, mult, cd, qi, pose, fams, opens=1, **extra):
    F[fid] = dict(role=role, shape=shape, dtype=dtype, hits=hits, targets=targets, mult=mult, cd=cd, qi=qi, pose=pose,
                  fams=set(fams.split()), opens=opens, extra=extra)


ALL = "any fists flute bell jian dual_blades short_blade heavy_sabre spear staff whip rope_dart bow fan umbrella brush"
form("strike", "burst", "strike", "physical", 1, 1, (1.50, 1.80), 6, 12, ["c3"], ALL)
form("flurry", "burst", "strike", "physical", 3, 1, (0.55, 0.65), 4, 10, ["punch*", "c1"], "any fists jian dual_blades short_blade spear staff whip brush")
form("thrust", "burst", "strike", "physical", 1, 2, (1.40, 1.70), 4, 10, ["thrust_1", "thrust_3", "c1"], "fists jian dual_blades short_blade spear staff rope_dart umbrella",
     reach_mult=1.3)
form("lunge", "movement", "strike", "physical", 1, 4, (1.50, 1.80), 6, 12, ["thrust_3", "punch_2", "jump"], "any fists jian dual_blades short_blade heavy_sabre spear staff whip rope_dart",
     dash=140)
form("sweep", "area", "ring", "physical", 1, 6, (1.00, 1.40), 5, 11, ["c3"], "fists bell jian dual_blades heavy_sabre spear staff whip rope_dart fan umbrella",
     both_sides=True, reach_mult=1.2)
form("arc", "area", "bolt", "qi", 1, 8, (0.90, 1.20), 5, 14, ["swing_2", "punch_2", "c2"], "any fists jian dual_blades heavy_sabre spear whip bow fan brush",
     projectile={"speed": 620, "range": 360, "count": 1, "pierce": 8})
form("volley", "burst", "bolt", "physical", 2, 1, (0.70, 0.90), 4, 10, ["bow", "swing_1", "c1"], "flute short_blade rope_dart bow fan umbrella",
     projectile={"speed": 680, "range": 380, "count": 2}, opens=1)
form("rain", "area", "rain", "qi*", 5, 5, (0.45, 0.60), 8, 20, ["bow", "swing_3", "meditate_burst"], "any flute jian spear bow fan umbrella brush",
     reach=420, depth=70, opens=2)
form("pillar", "burst", "pillar", "qi", 1, 1, (1.50, 1.80), 10, 16, ["meditate_burst"], "any flute bell jian bow brush", reach=260, opens=2)
form("wave", "area", "wave", "qi", 1, 8, (1.10, 1.40), 6, 14, ["c3", "punch_3"], "any fists flute bell jian heavy_sabre spear staff whip bow fan brush",
     reach=300, depth=60)
form("burst", "area", "ring", "qi", 1, 8, (1.40, 1.70), 9, 20, ["meditate_burst"], "any fists flute bell heavy_sabre staff whip rope_dart bow fan umbrella brush",
     both_sides=True, reach=160, depth=70, opens=2)
form("seeker", "burst", "bolt", "qi", 3, 3, (0.50, 0.70), 5, 12, ["attack", "swing_1", "c1"], "any flute jian short_blade whip rope_dart bow brush",
     projectile={"speed": 600, "range": 360, "count": 3, "seek": True})
form("return", "area", "bolt", "physical", 2, 8, (0.80, 1.00), 6, 14, ["swing_3", "c3"], "bell dual_blades short_blade heavy_sabre spear rope_dart fan umbrella",
     projectile={"speed": 540, "range": 300, "count": 1, "pierce": 8, "returning": True}, opens=2)
form("snare", "control", "wave", "qi", 1, 3, (0.60, 0.80), 10, 14, ["meditate_burst"], "any fists flute bell short_blade spear staff whip rope_dart bow fan brush",
     reach=220, depth=60)
form("counter", "self", "strike", "stance", 1, 1, (2.00, 2.00), 8, 10, ["c1"], "fists flute bell jian dual_blades short_blade heavy_sabre spear staff whip rope_dart umbrella",
     stance_s=2.0)
form("ward", "self", "domain", "buff", 0, 0, (0.0, 0.0), 24, 16, ["meditate_burst"], "any fists flute bell heavy_sabre staff fan umbrella brush")
form("chorus", "allies", "domain", "buff", 0, 0, (0.0, 0.0), 22, 20, ["attack", "meditate_burst"], "any flute bell fan umbrella brush",
     allies_heal_pct=0.05, allies_heal_s=6, heal_radius=240)
form("blink", "movement", "strike", "physical", 1, 1, (2.00, 2.60), 12, 20, ["thrust_1", "c1"], "any fists jian dual_blades short_blade rope_dart bow fan",
     dash=200, reach=240, opens=2)
form("plunge", "movement", "ring", "physical", 1, 8, (1.60, 2.00), 8, 20, ["jump"], "any fists bell jian dual_blades short_blade heavy_sabre spear staff whip rope_dart bow umbrella",
     both_sides=True, reach=140, depth=60, opens=2)
form("release", "burst", "strike", "qi", 4, 1, (0.55, 0.65), 12, 20, ["c1"], "jian dual_blades heavy_sabre spear fan umbrella",
     projectile={"speed": 560, "range": 420, "count": 4, "seek": True}, opens=3)
form("swarm", "allies", "strike", "qi", 6, 1, (0.40, 0.50), 20, 24, ["meditate_burst"], "flute jian dual_blades short_blade bow brush",
     projectile={"speed": 500, "range": 460, "count": 6, "seek": True}, opens=3)
form("domain", "area", "domain", "qi", 4, 8, (0.50, 0.60), 16, 22, ["meditate_burst"], "any flute bell jian heavy_sabre staff whip bow fan umbrella brush",
     both_sides=True, reach=240, depth=90, opens=3)
form("seal", "control", "strike", "qi", 1, 2, (0.70, 0.85), 8, 16, ["c2"], "any fists flute bell dual_blades short_blade heavy_sabre staff whip rope_dart bow umbrella brush",
     reach=240, status={"id": "qi_seal", "chance": 1.0, "power": 1, "duration_s": 3.0})
form("echo", "burst", "strike", "physical", 2, 1, (0.80, 1.00), 7, 12, ["c2"], "any fists flute bell jian dual_blades short_blade heavy_sabre spear staff whip rope_dart bow brush", opens=2)
FORMS = F
ROLES = ("burst", "area", "control", "self", "allies", "movement")
PAR_FORM = "arc"   # the par character's main art (§6.1): the jian's Qi arc, the line P12's par table is set from


def ring_at(lv):
    return max(r for r in RINGS if RINGS[r][1] <= lv)


def par_art(lv):
    """The par main art's multiplier at a Level, grade included (stats.py's par table and balance_sim read it): the
    line of PAR_FORM at the band's ring, its verb priced apart (the par blow is struck without an element)."""
    r = ring_at(lv)
    return sum(FORMS[PAR_FORM]["mult"]) / 2.0 * RING_BUDGET[r] * (1 + grade_bonus(r))


def tree_cap(lv):
    """The most the trees add to one bucket at a Level (§6.2): +15% by Level 99, +25% by 165 (TechniqueTreeRules.tree_cap)."""
    c99, c165 = PASSIVES["cap_99"], PASSIVES["cap_165"]
    return c99 * lv / 99.0 if lv <= 99 else min(c165, c99 + (c165 - c99) * (lv - 99) / 66.0)


def par_tree(lv):
    """What the par character's tree adds to its main art's damage (§6.2): its Realisations placed along its sector's
    route in the Formless tree (a passage a ring, the power passages on the odd rings, each act's notable and its kin
    group's keystone), within the Level's cap."""
    r = ring_at(lv)
    route = PASSIVES["passage_power"] * ((r + 1) // 2)
    for act, edge in ACT_EDGE.items():
        if edge <= r:
            route += PASSIVES["notable"] + (PASSIVES["keystone"] if act <= BUILT_ACT else 0.0)
    return min(tree_cap(lv), route)

# ----------------------------------------------------------------------------------------------------------------------
# The element's verbs (§3.3). control: the status the control forms put on a foe; other: the fields the rest carry;
# ward: the buff a Ward raises; cost: what the element's arts cost besides Qi; particles: vfx.particles.
# Every verb is priced at +10% (§6.4) so Water's pull and Formless's +10% land on one line.
VERB_VALUE = 0.10
ELEMENTS = {
    "water": dict(control={"id": "slow", "chance": 1.0, "power": 0.2, "duration_s": 2.0}, other={"pull": 40}, particles="square",
                  ward=[{"stat": "qi_resistance", "op": "pct_add", "value": 0.25, "duration": 8}]),
    "wood": dict(control={"id": "root", "chance": 1.0, "power": 1, "duration_s": 1.8}, other={"status": {"id": "bloom", "chance": 1.0, "power": 0.01, "duration_s": 4}},
                 particles="square", ward=[{"stat": "physical_defense", "op": "pct_add", "value": 0.25, "duration": 8}]),
    "fire": dict(control={"id": "burn", "chance": 1.0, "power": 0.05, "duration_s": 3}, other={"status": {"id": "burn", "chance": 0.4, "power": 0.03, "duration_s": 3}},
                 particles="ember", ward=[{"stat": "qi_attack", "op": "pct_add", "value": 0.15, "duration": 8}]),
    "earth": dict(control={"id": "stun", "chance": 1.0, "power": 1, "duration_s": 0.7}, other={"knockback": 80}, particles="square",
                  ward=[{"stat": "physical_defense", "op": "pct_add", "value": 0.30, "duration": 8}]),
    "metal": dict(control="armour_break", other={"crit": 0.10}, particles="shard",
                  ward=[{"stat": "physical_defense", "op": "pct_add", "value": 0.20, "duration": 8}, {"stat": "crit_chance", "op": "flat", "value": 0.05, "duration": 8}]),
    "wind": dict(control="knockup", other={"reach": 0.15}, particles="square",
                 ward=[{"stat": "evasion", "op": "pct_add", "value": 0.25, "duration": 8}, {"stat": "move_speed", "op": "pct_add", "value": 0.10, "duration": 8}]),
    "thunder": dict(control={"id": "shock", "chance": 1.0, "power": 0.2, "duration_s": 0.6}, other={"status": {"id": "shock", "chance": 0.3, "power": 0.2, "duration_s": 0.6}},
                    particles="shard", ward=[{"stat": "attack_speed", "op": "flat", "value": 0.12, "duration": 8}]),
    "soul": dict(control={"id": "confusion", "chance": 0.6, "power": 1, "duration_s": 2.0}, other={"ignore_armor": True}, cost={"soul": 8},
                 particles="ring", ward=[{"stat": "soul_defense", "op": "pct_add", "value": 0.30, "duration": 8}]),
    "none": dict(control={"id": "root", "chance": 1.0, "power": 1, "duration_s": 1.5}, other={"penetration": 0.10}, mult=1.10, particles="square",
                 ward=[{"stat": "physical_defense", "op": "pct_add", "value": 0.15, "duration": 8}, {"stat": "qi_resistance", "op": "pct_add", "value": 0.15, "duration": 8}]),
    "space": dict(control={"pull": 80}, other={"ignore_resistance": 0.10}, particles="square",
                  ward=[{"stat": "evasion", "op": "pct_add", "value": 0.30, "duration": 8}]),
    "time": dict(control={"id": "slow", "chance": 1.0, "power": 0.3, "duration_s": 2.0}, other={"status": {"id": "slow", "chance": 0.5, "power": 0.15, "duration_s": 2.0}},
                 particles="ring", ward=[{"stat": "attack_speed", "op": "flat", "value": 0.10, "duration": 8}]),
}
FAMILY_PARTICLES = {"brush": "ink", "bell": "ring", "flute": "ring"}
PROJECTILE_ART = {"flute": "note", "bell": "note", "short_blade": "needle", "dual_blades": "needle", "fan": "fan"}

# ----------------------------------------------------------------------------------------------------------------------
# Paths (§3.4): the damage budget, the fields the art carries, the favoured forms, the epithets of its names.
PATHS = {
    "body": dict(budget=1.10, fields={"body": True}, forms=("strike", "wave", "lunge"), words=("Iron-Bone", "Marrow", "Bronze-Skin", "Sinew", "Tendon", "Hard-Bone")),
    "blood": dict(budget=1.25, fields={"blood_path": True}, forms=("lunge", "strike", "burst"), words=("Crimson", "Sanguine", "Vein-Red", "Red River", "Heartblood", "Scarlet")),
    "buddhist": dict(budget=0.90, fields={"needs_vow": True}, forms=("ward", "chorus", "domain"), words=("Vowbound", "Lotus", "Merciful", "Almsbowl", "Prayer-Bead", "Temple-Bell")),
    "poison": dict(budget=0.80, fields={"poison_path": True}, forms=("seeker", "snare", "volley"), words=("Venom", "Miasma", "Nightshade", "Marsh-Fever", "Scorpion-Tail", "Bitter-Root")),
    "confucian": dict(budget=1.00, fields={"confucian_path": True, "insight_scale": 0.5}, forms=("pillar", "domain", "seal"),
                      words=("Upright", "Benevolent", "Rite-Bound", "Loyal", "Filial", "Scholar's")),
}
PATH_ORDER = ("body", "blood", "buddhist", "poison", "confucian")
POISON_STATUS = {"id": "poison", "chance": 1.0, "power": 0.02, "duration_s": 5}
BUDDHIST_SHIELD = 0.06   # a Buddhist attack raises a shield of 6% of max HP
# Tree passives (§4.2, §6.2): a passage gives the element's power for its family (+1%) or a cut in its Qi cost (-2%),
# alternating by ring; a notable +3% damage to its sector's arts of the element; a keystone, while realised, +2% to its
# kin group's. Into the one additive damage bucket, at most +15% by Level 99 and +25% by Level 165.
PASSIVES = {"passage_power": 0.01, "passage_cost": -0.02, "notable": 0.03, "keystone": 0.02, "cap_99": 0.15, "cap_165": 0.25}
COSTS = {"passage": 1, "art": 2, "notable": 3, "keystone": 5}

# ----------------------------------------------------------------------------------------------------------------------
# Keystone templates (§3.7): the six shapes a keystone takes; rule 6 gives each kin group of a tree and act its own.
TEMPLATES = ("constructs", "field", "avatar", "finisher", "mirror", "procession")

# ----------------------------------------------------------------------------------------------------------------------
# Names (§3.8). Image words by element: rings 1-4 homely, 5-8 wild and far, 9-13 of laws and worlds; creatures for the
# forms with a body; places for "{Noun} of the {Place}".
IMAGES = {
    "water": (["Brook", "Ripple", "Spring", "Dew", "Ferry", "Current", "Undertow", "Eddy", "Drizzle", "Mist", "Flood", "Falls", "Deep Pool",
               "Whirlpool", "Backwater", "Rill", "Shallows", "Riffle", "Wellwater", "Millrace", "Rain-Pond", "Tidal Bore"],
              ["Glacier", "Hoarfrost", "Riptide", "Swell", "Shoal", "Maelstrom", "Star-Sea", "Moon-Tide", "Abyss", "Ice-Floe", "Breaker",
               "Sea-Fog", "Rime", "Deep Trench", "Northern Ice"],
              ["Headwater", "World-River", "Tide of Ages", "Deep Law", "First Spring", "Ocean of Hours", "Sunken Sky", "Last Tide"],
              ["Heron", "Kingfisher", "Carp", "Otter", "Turtle", "Eel", "Crab", "Water Snake"],
              ["Deep Pool", "Drowned Moon", "Nine Ferries", "Falling River", "Cold Spring", "Sunken Bell", "Black Current", "Silver Reach"]),
    "wood": (["Reed", "Willow", "Bamboo", "Moss", "Root", "Thorn", "Vine", "Seedling", "Bark", "Sap", "Bloom", "Bramble", "Pine-Needle",
              "Fern", "Burr", "Cedar", "Orchid", "Mulberry", "Blossom", "Green-Shoot"],
             ["Old Pine", "Iron-Bark", "Banyan", "Hanging Moss", "Pollen-Storm", "Deep Forest", "Camphor", "Thornwood", "Heartwood",
              "Strangler Fig", "Elder Grove", "Wild Orchard"],
             ["World-Tree", "First Seed", "Green Law", "Root of Ages", "Orchard of Worlds", "Everbloom", "Seed of Heaven"],
             ["Mantis", "Stag", "Cicada", "Silkworm", "Tree Frog", "Woodpecker", "Caterpillar", "Hare"],
             ["Hidden Grove", "Bamboo Sea", "Thousand Roots", "Green Hall", "Mossy Stair", "Old Orchard", "Willow Bank", "Spring Garden"]),
    "fire": (["Ember", "Spark", "Cinder", "Kiln", "Hearth", "Coal", "Smoke", "Wick", "Flare", "Brazier", "Torch", "Charcoal", "Firepit",
              "Bonfire", "Tinder", "Candle-Flame", "Soot", "Red Coal"],
             ["Pyre", "Magma", "Comet", "Sunscar", "Ash-Wind", "Furnace", "Wildfire", "Forge-Heart", "Scorch", "Cinder-Storm", "Red Sky",
              "Burning Plain"],
             ["Star-Core", "Burning Law", "First Flame", "Sun-Seed", "Kiln of Worlds", "Endless Pyre", "Heaven-Fire"],
             ["Firefly", "Red Kite", "Cinder Hound", "Kiln Cat", "Salamander", "Fire Rooster", "Red Fox"],
             ["Red Kiln", "Nine Hearths", "Ash Road", "Burning Stair", "Last Ember", "Smoke Hall", "Sunset Forge", "Scarlet Gate"]),
    "earth": (["Pebble", "Riverstone", "Clay", "Loam", "Quarry", "Boulder", "Dust", "Ridge", "Terrace", "Gravel", "Flagstone", "Cliff",
               "Slate", "Millstone", "Mudbrick", "Hillside", "Stone-Step", "Grindstone"],
              ["Landslide", "Sand-King", "Crystal", "Bedrock", "Mountain Root", "Dune", "Avalanche", "Basalt", "Canyon", "Rockfall",
               "Deep Stone", "Sandstorm"],
              ["World-Floor", "Weight of Laws", "First Mountain", "Deep Strata", "Pillar of Earth", "Unmoved Stone", "Stone Heaven"],
              ["Ox", "Tortoise", "Pangolin", "Badger", "Mole", "Boar", "Mountain Goat", "Ram-Ox"],
              ["Quiet Quarry", "Nine Terraces", "Stone Gate", "Old Mountain", "Sunken Road", "Red Cliff", "Dusty Hall", "Clay Pit"]),
    "metal": (["Iron", "Copper", "Bronze", "Needle", "Bell", "Edge", "Coin", "Chain", "Anvil", "Nail", "Wire", "Hook", "Whetstone", "Tin",
               "Silver", "Rivet", "Ploughshare", "Iron-Filing"],
              ["Starsteel", "Sunsteel", "Blade-Wind", "Gong", "Broadside", "Meteor Iron", "Quicksilver", "War-Bell", "Tempered Steel",
               "Iron Storm", "Bright Edge"],
              ["Law-Edge", "The Unbroken", "First Ore", "Endless Forge", "Iron Heaven", "Last Blade", "Mirror-Steel"],
              ["White Tiger", "Hawk", "Wasp", "Magpie", "Hornet", "Shrike", "Iron Crow"],
              ["Cold Anvil", "Nine Bells", "Iron Gate", "Bronze Hall", "Silver Stair", "Hidden Forge", "White Blade", "Copper Road"]),
    "wind": (["Breeze", "Gust", "Kite", "Feather", "Cloud", "Updraft", "Whirl", "Draught", "Chime", "Pinwheel", "Dandelion", "Thistledown",
              "Crosswind", "Hill-Wind", "Rooftop Wind", "Flag-Wind"],
             ["Gale", "Harpy Wind", "Sky-Road", "Storm-Front", "Jet-Stream", "Cyclone", "Typhoon", "Sky-River", "North Wind",
              "Canyon Wind", "High Cloud"],
             ["Wind Between Worlds", "First Breath", "Long Sky", "Heaven's Breath", "Endless Draught", "Sky of Laws"],
             ["Crane", "Egret", "Sparrow", "Kestrel", "Swift", "Gull", "Swallow", "Lark"],
             ["High Pass", "Nine Kites", "Open Sky", "Windy Stair", "Cloud Gate", "Far Ridge", "Hanging Bridge", "Bell Tower"]),
    "thunder": (["Spark-Drum", "Rumble", "Flash", "Static", "Drumhead", "Crackle", "Peal", "Bolt", "Thunderclap", "Rain-Drum",
                 "War Drum", "Storm-Spark", "Hail-Drum", "Low Rumble"],
                ["Storm-Horn", "Lightning Scar", "Thunder-Plain", "Storm-Eye", "Sky-Fire", "Forked Light", "Black Cloud", "Iron Sky"],
                ["Heaven's Drum", "The Verdict", "First Thunder", "Judging Sky", "Last Peal", "Thunder of Laws"],
                ["Ram", "Drum-Beast", "Stormbird", "Thunder-Hawk", "Storm Goat", "Lightning Eel"],
                ["Thunder Plain", "Storm Gate", "Nine Drums", "High Scar", "Black Sky", "Rolling Hills", "Iron Clouds", "Drum Tower"]),
    "soul": (["Lantern", "Dream", "Echo", "Shadow", "Reflection", "Whisper", "Candle", "Memory", "Sigh", "Mirror", "Silence", "Veil",
              "Dusk-Light", "Night Thought", "Faint Voice", "Half-Dream"],
             ["Mirror-Lake", "Spirit-Sea", "Ghost-Light", "Wisp", "Soul-Tide", "Far Dream", "Moonlit Mind", "Hollow Echo", "Night Bell"],
             ["Lamp Before Birth", "Last Reflection", "First Dream", "Mind of Heaven", "Endless Echo", "Silent Law"],
             ["Moth", "Owl", "Fox", "Lantern-Fish", "White Crow", "Night Cat", "Bat"],
             ["Still Lake", "Nine Lanterns", "Dreaming Hall", "Quiet Room", "Moon Mirror", "Veiled Stair", "Empty Shrine", "Dusk Garden"]),
    "none": (["Plain", "Empty", "Single", "Straight", "Bare", "Still", "Quiet", "Simple", "Open", "Level", "Clear", "True", "Even", "Unadorned"],
             ["Uncarved", "Unborn", "Nameless", "Boundless", "Uncoloured", "Unwritten", "Silent"],
             ["One Line", "Before Form", "First Stroke", "Empty Law", "Only Way", "Plain Heaven"],
             [],
             ["Empty Room", "Plain Road", "Bare Hill", "Open Door", "Still Water", "One Brush", "Blank Page", "Clear Sky"]),
    "space": (["Orbit", "Fold", "Gap", "Step-Between", "Tether", "Pivot", "Far Point", "Near Point", "Crossing", "Hollow"],
              ["Gravity", "Void-Rim", "Star-Well", "Horizon", "Far Shore", "Star-Chart", "Inverted Sky", "Axis"],
              ["Space Between Stars", "Last Orbit", "First Distance", "Folded Heaven", "Endless Reach", "Unmapped Sky"],
              [],
              ["Turning Stars", "Far Orbit", "Inverted Hall", "Silent Observatory", "Tilted Stair", "Seven Lamps", "Star Garden", "Bent Road"]),
    "time": (["Hour", "Water-Clock", "Dusk", "Dawn", "Noon", "Moment", "Candle-Hour", "Sundial", "Midnight", "Morning Bell"],
             ["Eclipse", "Hour Between", "Long Night", "Slow Moon", "Late Star", "Old Season"],
             ["Yesterday", "The Unwinding", "First Hour", "Last Hour", "Endless Day", "Hour of Laws"],
             [],
             ["Stopped Clock", "Long Dusk", "Nine Hours", "Old Calendar", "Grey Dawn", "Waiting Hall", "Quiet Hour", "Faded Moon"]),
}
# Nouns by form (§3.8); ("word", families) keeps a noun to the families it fits.
NOUNS = {
    "strike": ["Blow", "Cut", ("Palm", "any fists"), ("Fist", "fists"), "Cleave", "Stroke", ("Knuckle", "fists"), ("Toll", "bell"), ("Note", "flute"), ("Shot", "bow"), ("Script", "brush")],
    "flurry": ["Flurry", "Cuts", ("Palms", "any fists"), "Hundred Strikes", ("Jabs", "fists"), ("Strokes", "brush jian"), "Blows"],
    "thrust": ["Thrust", "Lance", "Piercing", ("Spearhead", "spear"), "Point"],
    "lunge": ["Rush", "Lunge", "Charge", "Leap", "Onrush"],
    "sweep": ["Sweep", "Tail", "Wheel", "Round Cut", "Scythe"],
    "arc": ["Crescent", "Arc", "Wave-Edge", "Half-Moon", "Sickle"],
    "volley": ["Shot", ("Arrows", "bow"), ("Knives", "short_blade dual_blades rope_dart"), "Volley", ("Notes", "flute"), ("Leaves", "fan umbrella")],
    "rain": ["Rain", "Downpour", "Hail", "Shower", "Cloudburst"],
    "pillar": ["Pillar", "Column", "Spike", "Spire", "Shaft"],
    "wave": ["Wave", "Surge", "Tremor", "Tide", "Rolling Wave"],
    "burst": ["Bloom", "Burst", "Lotus", "Blossom", "Flowering"],
    "seeker": ["Needles", "Swallows", ("Notes", "flute bell"), "Hunters", "Fireflies", "Homing Darts"],
    "return": ["Return", "Homecoming", "Boomerang", "Round Trip", "Return Flight"],
    "snare": ["Net", "Snare", "Grip", "Vines", "Knot", "Tether"],
    "counter": ["Parry", "Guard", "Answer", "Riposte", "Rebuke"],
    "ward": ["Mantle", "Skin", "Shell", "Focus", "Armour", "Robe"],
    "chorus": ["Melody", "Hymn", "Air", "Call", "Chant", "Lullaby"],
    "blink": ["Step", "Flicker", "Vanishing", "Shadow Step", "Blink"],
    "plunge": ["Descent", "Dive", "Fall", "Plunge", "Drop"],
    "release": ["Release", "Flight", "Loosing", "Freed Blade", "Wandering Edge"],
    "swarm": ["Swarm", "Host", "Flock", "Legion", "Hive"],
    "domain": ["Field", "Court", "Sea", "Circle", "Garden", "Precinct"],
    "seal": ["Seal", "Toll", "Knell", "Binding", "Lock"],
    "echo": ["Echo", "Twice-Strike", "Double Cut", "Answering Blow", "Second Stroke"],
}
FAMILY_WORD = {"jian": "Sword", "spear": "Spear", "staff": "Staff", "heavy_sabre": "Sabre", "short_blade": "Knife", "fists": "Fist",
               "bow": "Arrow", "fan": "Fan", "flute": "Flute", "bell": "Bell", "brush": "Brush", "any": "Palm",
               "dual_blades": "Twin Blade", "whip": "Whip", "rope_dart": "Rope Dart", "umbrella": "Parasol"}
NUMBERS = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}
VERBING = ["Splitting", "Cutting", "Rending", "Breaking", "Parting", "Crossing", "Swallowing", "Shaking", "Turning", "Piercing",
           "Scattering", "Sundering", "Cleaving", "Riding", "Climbing", "Spurning", "Quelling", "Waking"]
HEAVY = {"strike", "lunge", "plunge", "blink", "sweep", "thrust", "wave"}   # forms that take "{Image}-{Verb}ing {Noun}"
BODY = {"strike", "thrust", "lunge", "sweep", "blink", "plunge", "counter", "echo", "flurry"}   # forms that take "{Creature} {Noun}"
MAX_NAME = 28

# Names from other works that no art may take, exactly or within an edit distance of 2 (§3.8): well-known named arts
# from other fiction and games, and real scripture titles. data_validation reads the list from technique_trees.json.
DENYLIST = [
    "Heart Sutra", "Diamond Sutra", "Lotus Sutra", "Platform Sutra", "Surangama Sutra", "Avatamsaka Sutra", "Tao Te Ching",
    "Dao De Jing", "Book of Changes", "I Ching", "Analects", "Art of War", "Classic of Mountains and Seas", "Yellow Court Classic",
    "Nine Yin Manual", "Nine Yang Manual", "Nine Yin Scripture", "Nine Yang Divine Skill", "Eighteen Dragon Subduing Palms",
    "Dragon Subduing Palm", "Six Meridians Divine Sword", "Heavenly Mountain Plum", "Sunflower Manual", "Sunflower Treasured Book",
    "Evil Warding Sword", "Nine Swords of Dugu", "Dugu Nine Swords", "Solitary Nine Swords", "Lingbo Weibu", "Graceful Waves Steps",
    "Northern Darkness", "Northern Darkness Divine Skill", "Toad Skill", "Toad Stance", "Beidou Formation", "Big Dipper Formation",
    "Heavenly Heart Sword", "Jade Maiden Heart Sutra", "Jade Maiden Sword", "Ninefold Sun", "Tai Chi Fist", "Tai Chi Sword",
    "Drunken Fist", "Drunken Boxing", "Wing Chun", "Iron Palm", "Iron Shirt", "Golden Bell Shield", "Golden Bell Cover",
    "Shaolin Fist", "Eagle Claw", "Tiger Crane", "Crane Style", "Snake Style", "Mantis Fist", "Praying Mantis Fist",
    "Lion's Roar", "Buddha's Palm", "Palm of the Buddha", "Tathagata Palm", "Ten Thousand Swords Return to One",
    "Myriad Swords Return to One", "Heavenly Demon Art", "Heavenly Demon Divine Art", "Blood Demon Art", "Nine Heavens Art",
    "Kamehameha", "Rasengan", "Chidori", "Shadow Clone", "Shadow Clone Jutsu", "Flying Thunder God", "Getsuga Tensho", "Bankai",
    "Hadoken", "Shoryuken", "Tatsumaki", "Sonic Boom", "Falcon Punch", "Omnislash", "Braver", "Meteor Strike", "Dragon Fist",
    "Spirit Bomb", "Final Flash", "Big Bang Attack", "Galick Gun", "Destructo Disc", "Solar Flare", "Hundred Crack Fist",
    "Hokuto Hyakuretsu Ken", "Fist of the North Star", "Gomu Gomu", "Gear Second", "Haki", "Susanoo", "Amaterasu", "Tsukuyomi",
    "Chakra Blade", "Wind Scar", "Iron Reaver", "Backlash Wave", "Dragon Slayer", "Fire Dragon's Roar", "Heaven's Wrath",
    "Hurricane Kick", "Rising Dragon", "Dragon Punch", "Whirlwind Kick", "Crane Kick", "Fatality", "Blade Dance", "Moonlight Sword",
    "Heaven Splitting Sword", "Sword Qi Rain", "Sword of Kings", "Excalibur", "Mjolnir", "Gungnir", "Ragnarok", "Armageddon",
    "Holy Light", "Divine Storm", "Chaos Control", "Limit Break", "Knights of the Round", "Bahamut", "Ultima", "Meteor",
    "Nine Transformations", "Seventy-Two Transformations", "Somersault Cloud", "Ruyi Jingu Bang", "Golden Cudgel",
    "Lotus Heart Sutra", "Great Compassion Mantra", "Om Mani Padme Hum", "Six Syllable Mantra", "Medicine Buddha Sutra",
    "Tibetan Book of the Dead", "Bardo Thodol", "Zhuangzi", "Liezi", "Huainanzi", "Neijing", "Yellow Emperor's Classic",
]
