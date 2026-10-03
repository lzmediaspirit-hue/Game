"""The Streams Pills (decision 45, phase 3: the first family written as a spec only): cultivation speed from Cloud Stride
to Will Manifest, where the incense (Plain, Common) and the Qi Flow Pill (Earth) leave off.

Each rung opens more of the meridians to the Qi around the sitter: +{pct}% to `accumulation_rate` for {minutes} minutes,
the rung's curves.SPEED (a tenth more a grade above Earth). One works at a time (the source `streams_pill`: a new pill
takes over from one still at work, StatBlock.add_modifier); they stack with the incense and the Qi Flow Pill, and count
toward the accumulation family's lifetime resistance (S44). Its toxicity is curves.PILL_TOXICITY's, its price the
game's for its Level (LootRules.value_of), its brewing time curves.RECIPE_TIME's. Each grade's pill sells where that
grade's cultivators sit, and its recipe beside it; its icon is the gourd of a lifting draught in the grade's kit.
"""
from content.items.dsl import curve, effect, family, per

FAMILIES = [
    family("pill.streams", kind="pill", tiers=("heaven", "mystic", "sage", "sovereign"),
           words={"heaven": "three", "mystic": "five", "sage": "seven", "sovereign": "nine"},
           id="{word}_streams_pill", name="{Word} Streams Pill",
           desc="It opens {word} streams of the meridians to the Qi around you: cultivation +{pct}% for {minutes} minutes. A new pill takes "
                "over from one still at work.",
           mark="spiral_up", toxicity=curve("toxicity"), cause="energy", group="buff", resist="accumulation",
           use=[effect("add_modifier", stat="accumulation_rate", op="flat", value=curve("speed"), duration=curve("speed", "seconds"),
                       source="streams_pill")],
           recipe=dict(inputs=per(heaven=[("cloudtop_orchid", 1), ("mist_lotus", 2), ("cloud_feather", 1)],
                                  mystic=[("riverreed_ginseng_1000", 1), ("soulbell_flower", 2), ("roc_feather", 1)],
                                  sage=[("ember_cactus", 1), ("frost_lotus", 1), ("harpy_plume", 2)],
                                  sovereign=[("star_lotus", 1), ("frost_lotus", 1), ("comet_plume", 2)]),
                       time_s=curve("recipe_time"), element="earth",
                       # The recipe sells beside the pill, for about twice the pill's price.
                       learn={"alchemist_guild": {"heaven": dict(price=1900, flag="guild_alchemy_expert"),
                                                  "mystic": dict(price=2900, flag="guild_alchemy_expert")},
                              "port_apothecary": {"sage": dict(price=45)},
                              "lanternfall_apothecary": {"sovereign": dict(price=5)}}),
           icon=dict(vessel="buff", pill="cyan", ink=("qi", -1)),
           sources=dict(shop={"mei_qing": {"heaven": dict(realm="cloud_stride_1"), "mystic": dict(realm="heaven_glimpse_1")},
                              "condensing_hall": {"sage": dict(realm="sage_sovereign_1")},
                              "lanternfall_apothecary": {"sovereign": dict(realm="will_manifest_1")}})),
]
