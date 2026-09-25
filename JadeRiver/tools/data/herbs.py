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
    })
    entries("seasons", [{"id": sid, "name": name, "desc": desc} for sid, name, desc in SEASONS], week_s=604800)
