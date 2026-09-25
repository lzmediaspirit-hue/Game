"""S45 herbs: seasons.json and garden.json (herb families and ages, the harvest tap, ripening phases, seeds).

Rare herb nodes themselves are placed in world.py (rare_herbs()); their fields are documented there.
"""
from common import entries, write
from items import HERB_AGE, SEEDS

# Four seasons of one real week each, turning with the weekly reset (Monday 04:00). They never gate progression:
# a node out of season lies dormant and shows when it will flower (the Codex calendar lists them).
SEASONS = [
    ("spring", "Spring", "Orchids open on the high ledges; the Sky Ledges' hundred-year orchid flowers."),
    ("summer", "Summer", "The river runs warm. Hundred-year ember peppers redden and the thousand-year root wakes."),
    ("autumn", "Autumn", "Mist settles on the slopes and the old soulbells ring."),
    ("winter", "Winter", "Most rare herbs sleep. The ones without a season keep their own time."),
]


def build():
    families = {}
    for item_id, (fam, age) in HERB_AGE.items():
        families.setdefault(fam, {})[str(age)] = item_id
    seeds = {fam: sid for sid, fam, _, _ in SEEDS}
    write("garden.json", {
        "schema_version": 1,
        # family -> {age: item}; ages step 10 -> 100 -> 1,000.
        "families": families,
        "ages": [10, 100, 1000],
        "seeds": seeds,
        # A perfect harvest can drop the family's seed (default 10%). Cloudtop Orchid and Soulbell seeds come only
        # from inheritances and secret realms, so their nodes drop none.
        "harvest_seeds": ["willow_moss", "riverreed_ginseng", "ember_pepper", "mist_lotus"],
        "seed_chance": 0.10,
        # An older herb standing in for a younger one lifts the craft's quality score by this much per age tier.
        "age_quality": 0.04,
        # The harvest tap: after the 1.5 s hold a ring shrinks over ring_s; tapping within the window around
        # `target` (a fraction of the shrink) is perfect. The window is a share of the ring by gathering rank.
        "harvest": {"ring_s": 1.0, "target": 0.7,
                    "window": {"apprentice": 0.12, "adept": 0.16, "expert": 0.20, "master": 0.24, "grandmaster": 0.28}},
        # Ripening: a node is ripe for `minutes` real minutes centred on its phase, every Nth in-game day (48 real
        # minutes long). Phases are instants in the day: dawn (morning begins), day (midday), dusk (night begins)
        # and night (midnight).
        "phases": {"dawn": 0.0, "day": 0.375, "dusk": 0.75, "night": 0.875},
        # A guardian wakes when you come within `wake_px` of a ripe node, no more than `wake_below` under its tier.
        "guardian": {"wake_px": 480, "wake_below": 60, "leash_px": 600},
        # Garden beds (V6b). A bed's field grade caps the grade of herb it can grow; Spirit Soil raises it a step for
        # good. Low beds line the sect terraces, Mid beds sit in a cave abode.
        "field_grades": ["low", "mid", "high"],
        # The patch art a bed shows for each family as it grows.
        "props": {"willow_moss": "willow_moss_patch", "riverreed_ginseng": "riverreed_ginseng_patch", "ember_pepper": "ember_pepper_bush",
                  "mist_lotus": "mist_lotus_patch", "cloudtop_orchid": "cloudtop_orchid_patch", "soulbell_flower": "soulbell_flower_patch",
                  "frost_lotus": "frost_lotus_patch", "ember_cactus": "ember_cactus_patch"},
        "field_cap": {"low": "earth", "mid": "heaven", "high": "mystic"},
        # Real hours from seed to harvest, sped by the room's Qi (half its bonus: a cave abode's 2.2 grows 1.6x).
        "grow_hours": {"willow_moss": 2, "ember_pepper": 3, "riverreed_ginseng": 4, "mist_lotus": 6, "cloudtop_orchid": 8,
                       "soulbell_flower": 8, "frost_lotus": 10, "ember_cactus": 10},
        "qi_growth": 0.5,
        "bed_yield": {"young": [2, 3], "aged": [1, 1]},
        "seed_back": 0.2,
        # Qi-spring water: bottled 3 times a reset day; each watering gives +25% growth.
        "water": {"per_day": 3, "growth": 0.25},
        # Transplanting a rare herb with a Spirit Spade, from Expert: 25% it dies, 5% less per rank above Expert.
        "transplant": {"rank": "expert", "death": 0.25, "per_rank": 0.05},
        # The Verdant Dew Vial: one dew per 24 h (offline too), holding 3; a dew ages a bed's herb one tier. The
        # valley's Qi holds a herb at 1,000 years; 10,000-year herbs are the Azure Expanse's (v1.1 extension).
        "dew": {"every_s": 86400, "cap": 3, "valley_age_cap": 1000},
        # Spirit Soil: 1% from beasts of rank 3 and above (Level 19+), and one in the Drowned Abbot's vault.
        "spirit_soil": {"chance": 0.01, "min_level": 19},
    })
    entries("seasons", [{"id": sid, "name": name, "desc": desc} for sid, name, desc in SEASONS], week_s=604800)
