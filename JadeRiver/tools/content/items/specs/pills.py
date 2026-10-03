"""Pills (S44, Part 8; decision 45's fixed cultivation): one family a pill, each its row, recipe, shop lines, the
lines that sell its recipe, its icon (the vessel by kind, the grade's kit) and the sources the engine does not write.

A pill: `pill(id, grade, mark, toxicity, desc, use, cause=, group=, ...)` as items.py wrote it, plus
- `resist`: its S44 lifetime-resistance family (accumulation, body, insight, soul, support);
- `soul`: its Pill Soul when not its group's (kinds.SOUL_BY_GROUP);
- `extra`: the row's own keys (burst, support, then...), after soul_effect;
- `recipe=dict(inputs, time_s, element, learn={shop: line}, ...)`: the alchemy recipe (economy.py's block "alchemy"
  unless `block=`), its element (S44 affinity), and where its recipe scroll is sold;
- `icon=dict(vessel, pill, ink[, mark, extra])`: tools/icons/families/pills.py (the vessel defaults to the group's);
- `sources`: `shop={shop: line}` (written), and what hands it out elsewhere (chest, drop, reward..., checked).
A shop line is `{}` or its own keys: price, realm / flag (a requires of one), requires, rotation, currency, daily.
"""
from common import all_of, flag, realm
from content.items.dsl import DROP, curve, effect, family, qi


def pill(id, grade, mark, toxicity, desc, use, cause=None, group="restoration", **kw):
    return family("pill." + id, kind="pill", tiers=(grade,), mark=mark, toxicity=toxicity, desc=desc, use=use, cause=cause,
                  group=group, **kw)


def recipe(inputs, time_s=None, element="earth", **kw):
    r = {"inputs": inputs}
    if time_s is not None:
        r["time_s"] = time_s
    r.update(kw)
    r["element"] = element
    return r


FAMILIES = [
    pill("healing_pill", "common", "heart", 5, "Cures a minor body injury and restores 30% HP over 5 s.",
         [effect("cure_injury", injury="body", max_severity=1), effect("heal", pct=0.3, over_s=5)], cause="structure", group="healing",
         recipe=recipe([("riverreed_ginseng_10", 1), ("willow_moss", 2)], 120, "wood", learn={"mei_qing": {}}),
         icon=dict(pill="red", ink=("red", 0)),
         sources=dict(shop={"mei_qing": {}, "jade_sect": {}, "cloud_sect": {}, "port_peddler": {}, "port_apothecary": {}, "lanternfall_goods": {}},
                      chest=True, reward=True)),
    pill("qi_restoration_pill", "common", "spiral", 5, "Restores 40% QI and cures a minor meridian injury.",
         [effect("restore_resource", pool="qi", pct=0.4), effect("cure_injury", injury="meridian", max_severity=1)], cause="energy",
         recipe=recipe([("willow_moss", 2), ("leech_oil", 1)], 120, "water"),
         icon=dict(pill="qi", ink=("qi", -1)),
         sources=dict(shop={"mei_qing": {}, "jade_sect": {}, "cloud_sect": {}, "port_peddler": {}, "port_apothecary": {}, "lanternfall_goods": {},
                            "oasis_keeper": {}}, chest=True, reward=True)),
    # Decision 45: a fixed +420 (8% of the stage at the middle of Common), said in its text.
    pill("qi_gathering_pill", "common", "spiral_up", 10, "{cult}.", [qi(0.08)], cause="energy", group="utility", resist="accumulation",
         recipe=recipe([("riverreed_ginseng_10", 2), ("moss", 2)], 180, "earth",
                       learn={"mei_qing_recipes": dict(price=120, realm="qi_kindling_3")}),
         icon=dict(pill="cyan", ink=("qi", -1)),
         sources=dict(shop={"mei_qing": {}}, chest=True, reward=True)),
    pill("bone_strengthening_pill", "common", "bone", 8, "Adds 150 body XP.", [effect("add_body_xp", amount=150)], cause="structure",
         group="utility", soul="iron_skin", resist="body",
         recipe=recipe([("tortoise_plate", 1), ("boar_hide", 1), ("riverreed_ginseng_10", 1)], 180, "earth",
                       learn={"mei_qing_recipes": dict(price=120, realm="qi_kindling_3")}),
         icon=dict(pill="bone", ink=("earth", -2)),
         sources=dict(shop={"mei_qing": dict(rotation=True), "ironroot_clan": {}})),
    pill("purging_pill", "common", "leaf", 0, "Purges 30 toxicity.", [effect("add_toxicity", amount=-30)], group="utility",
         recipe=recipe([("willow_moss", 3), ("river_mud", 1)], 120, "water"),
         icon=dict(vessel="loose", mark="drop_leaf", pill="oil", ink=("earth", -2)),
         sources=dict(shop={"granny_liu": dict(realm="qi_kindling_2"), "greyreed": {}})),
    pill("viper_antidote", "common", "leaf", 0, "Cures poison.", [effect("cure_status", status="poison")], group="utility",
         recipe=recipe([("venom_sac", 1), ("willow_moss", 1)], 90, "wood",
                       learn={"mei_qing_recipes": dict(price=80, realm="qi_kindling_3")}),
         icon=dict(vessel="loose", pill="leaf", ink=("leaf", -2)),
         sources=dict(shop={"oasis_keeper": {}})),
    pill("tiger_blood_pill", "common", "flame", 12, "+20% attack for 60 s, then exhaustion (-20% for 60 s).",
         [effect("add_modifier", stat="physical_attack", op="pct_add", value=0.2, duration=60, source="tiger_blood"),
          effect("apply_status", status="exhausted", delay=60, duration=60)], group="buff", soul="iron_skin", extra=dict(burst=True),
         recipe=recipe([("thorn_hide", 1), ("ember_pepper", 2)], 180, "fire",
                       learn={"mei_qing_recipes": dict(price=150, realm="qi_kindling_5")}),
         icon=dict(pill="ember", ink=("ember", -2))),
    pill("cleansing_pill", "common", "gate", 10, "Support item: lowers the risk of Heaven's Cleansing by one step.", [], cause="environment",
         group="utility", resist="support", extra=dict(support={"risk": -1, "event": "heavens_cleansing"}),
         recipe=recipe([("mist_lotus", 1), ("jade_scale", 2), ("riverreed_ginseng_100", 1)], 300, "water"),
         icon=dict(vessel="breakthrough", mark="gate_cloud", pill="pearl", ink=("navy", -1)),
         sources=dict(shop={"jade_sect": dict(realm="qi_kindling_9"), "cloud_sect": dict(realm="qi_kindling_9"), "greyreed": {}}, reward=True)),
    pill("foundation_guard_pill", "earth", "gate", 12, "Breakthrough support: lowers risk by one step.", [], cause="structure", group="utility",
         resist="support", extra=dict(support={"risk": -1}),
         recipe=recipe([("serpent_core", 1), ("riverreed_ginseng_100", 2), ("guardian_stone", 1)], 600, "earth",
                       learn={"alchemist_guild": dict(price=600, flag="guild_alchemy_adept")}),
         icon=dict(vessel="breakthrough", pill="gold", ink=("gold", -3)),
         sources=dict(shop={"mei_qing": dict(rotation=True), "jade_sect": dict(realm="qi_unfurling_1"), "cloud_sect": dict(realm="qi_unfurling_1")},
                      chest=True, reward=True)),
    pill("clear_mind_pill", "earth", "lamp", 8, "+50% insight rate for 30 minutes.",
         [effect("add_modifier", stat="insight_rate", op="flat", value=0.5, duration=1800, source="clear_mind")], cause="understanding",
         group="buff", soul="clear_mind", resist="insight",
         recipe=recipe([("mist_lotus", 1), ("jade_scale", 1), ("willow_moss", 2)], 300, "water",
                       learn={"alchemist_guild": dict(price=500, flag="guild_alchemy_adept")}),
         icon=dict(pill="sky", ink=("navy", -1)),
         sources=dict(shop={"mei_qing": dict(rotation=True), "jade_sect": {}, "cloud_sect": {}, "old_pan": dict(price=3, rotation=True),
                            "port_peddler": dict(rotation=True), "condensing_hall": {}, "lanternfall_apothecary": {}, "observatory": {},
                            "lanternwright": {}, "navigator": {}}, reward=True)),
    pill("meridian_reversal_pill", "earth", "arrows_loop", 10, "Resets all meridian points.", [effect("reset_meridians")], group="utility",
         recipe=recipe([("prayer_beads", 2), ("mist_lotus", 1)], 300, "metal",
                       learn={"alchemist_guild": dict(price=700, flag="guild_alchemy_adept")}),
         icon=dict(pill="qi", ink=("qi", -2))),
    # S44 ancient recipe: its three pages lie in dungeons and secret realms (world.py places them).
    pill("method_conversion_pill", "earth", "arrows", 10, "Halves the cost of switching cultivation methods.", [], group="utility",
         soul="clear_mind", extra=dict(method_conversion=True),
         recipe=recipe([("manual_page", 1), ("jade_scale", 2), ("mist_lotus", 1)], 300, "metal", fragments=3),
         icon=dict(pill="violet", ink=("violet", -2))),
    pill("qi_refining_pill", "earth", "spiral", 15, "Required to break through from Heart Tempering 9 to Cloud Stride 1.", [], cause="material",
         group="utility",
         recipe=recipe([("pearl", 2), ("mist_lotus", 2), ("serpent_core", 1)], 600, "water",
                       learn={"mei_qing_recipes": dict(price=800, realm="heart_tempering_5")}),
         icon=dict(vessel="breakthrough", pill="jade", ink=("qi", -2))),
    # S48 Core Forging: refined only over a Heavenly Flame; taken within the hour before the core forms, it is one preparation point.
    pill("heavenly_flame_pill", "earth", "flame", 6, "Refined over a Heavenly Flame. Taken within the hour before Heart Tempering 9 → Cloud Stride 1, "
         "it is one Core Forging preparation point. Composure +20.", [effect("add_composure", amount=20)], cause="energy", group="utility",
         recipe=recipe([("ember_pepper", 3), ("riverreed_ginseng_100", 1), ("serpent_core", 1)], None, "fire", fire="heavenly_flame",
                       block="heavenly_flame"),
         icon=dict(vessel="breakthrough", pill="fire", ink=("red", -2))),
    pill("soul_soothing_pill", "heaven", "eye", 8, "Cures a soul injury; +20% Soul for 10 minutes.",
         [effect("cure_injury", injury="soul", max_severity=3),
          effect("add_modifier", stat="max_soul", op="pct_add", value=0.2, duration=600, source="soul_soothing"),
          effect("add_soul", amount=50)], cause="soul", soul="clear_mind", resist="soul",
         recipe=recipe([("mirror_dust", 2), ("soul_wax", 1), ("mist_lotus", 1)], 600, "water"),
         icon=dict(pill="violet", ink=("violet", -1)),
         sources=dict(shop={"port_peddler": dict(rotation=True), "condensing_hall": {}, "lanternfall_apothecary": {}})),
    pill("mind_lake_opening_pill", "heaven", "eye_gate", 15, "Required to break through from Cloud Stride 9 to Spirit Awakening 1.", [],
         cause="material", group="utility", soul="clear_mind",
         recipe=recipe([("cloud_feather", 3), ("mist_lotus", 2), ("cloudtop_orchid", 1)], 900, "water"),
         icon=dict(vessel="breakthrough", pill="storm", ink=("navy", -1))),
    pill("sage_condensing_pill", "mystic", "knot", 20, "Required to break through from Heaven Glimpse 3 to Sage 1.", [], cause="material",
         group="utility",
         recipe=recipe([("roc_feather", 2), ("jade_core", 1), ("soulbell_flower", 2)], 1200, "metal"),
         icon=dict(vessel="breakthrough", pill="gold", ink=("plum", -1)),
         sources=dict(shop={"condensing_hall": dict(price=90, realm="heaven_glimpse_3"), "free_market": dict(price=80, rotation=True)},
                      reward=True)),
    # S44 ancient recipe (four pages).
    pill("sovereign_settling_pill", "sage", "knot", 15, "Settles a new Sage Sovereign stage at once: its consolidation ends.",
         [effect("settle_consolidation")], cause="structure", group="utility",
         recipe=recipe([("ember_cactus", 2), ("worm_glass_tooth", 1), ("frost_lotus", 1)], 1500, "fire", fragments=4),
         icon=dict(vessel="breakthrough", pill="ember", ink=("clay", -2)),
         sources=dict(shop={"condensing_hall": dict(price=120, realm="sage_sovereign_1")}, chest=True, reward=True)),
    pill("will_tempering_pill", "sage", "eye", 12, "+40 Will for 30 minutes: another's Presence weighs less on you.",
         [effect("add_modifier", stat="will", op="flat", value=40, duration=1800, source="will_tempering")], cause="soul", group="buff",
         icon=dict(pill="violet", ink=("navy", -1)),
         sources=dict(shop={"lanternfall_goods": dict(price=6), "observatory": dict(price=6), "lanternwright": dict(price=6)},
                      chest=True, drop=True, reward=True)),
    # v1.2 (S28): the Hollow Tide's cleansing: 40 points of Hollowing drawn out at once.
    pill("tide_cleansing_pill", "sovereign", "knot", 12, "Draws 40 points of Hollowing out of you at once.", [effect("cleanse_hollowing", amount=40)],
         cause="soul", group="restoration",
         recipe=recipe([("star_lotus", 2), ("wyrm_ash", 1), ("jelly_silk", 1)], 1200, "water", learn={"lanternfall_apothecary": dict(price=40)}),
         icon=dict(pill="driftteal", ink=("driftteal", -2)),
         sources=dict(reward=True)),
    pill("storm_blood_pill", "mystic", "bolt", 10, "+4 attunement in the zone you stand in for 30 minutes.",
         [effect("add_modifier", stat="attunement_bonus", op="flat", value=4, duration=1800, source="storm_blood")], group="buff",
         recipe=recipe([("spark_pelt", 1), ("storm_shard", 2), ("soulbell_flower", 1)], 900, "wood", after="sage_condensing_pill",
                       learn={"alchemist_guild": dict(price=2400, requires=all_of(flag("guild_alchemy_expert"), realm("heaven_glimpse_1"))),
                              "port_apothecary": dict(price=30)}),
         icon=dict(pill="storm", ink=("navy", -1)),
         sources=dict(shop={"oasis_keeper": {}, "free_market": {}, "herders_camp": {}}, reward=True)),
    # S44 / Part 8: the Qi Flow Pill is decision 45's Earth rung of the cultivation-speed ladder (curves.SPEED); its debt
    # comes due when its hour is up (`then`, applied on buff_expired). The Alchemist Guild's Expert reward teaches it.
    pill("qi_flow_pill", "earth", "spiral_up", 5, "+{pct}% accumulation for {minutes} minutes. When it wears off, the toxicity it held back comes "
         "due: +15.", [effect("add_modifier", stat="accumulation_rate", op="flat", value=curve("speed"), duration=curve("speed", "seconds"),
                              source="qi_flow_pill")],
         cause="energy", group="buff", resist="accumulation", extra=dict(then=[effect("add_toxicity", amount=15)]),
         recipe=recipe([("riverreed_ginseng_100", 1), ("jade_scale", 2), ("leech_oil", 1)], None, "earth", block="qi_flow"),
         icon=dict(pill="jade", ink=("qi", -2))),
    # S44 hidden recipes, found only by experiment.
    pill("sunfire_pill", "common", "flame", 8, "Found by experiment: ginseng and Ember Pepper. +12% attack for 10 minutes.",
         [effect("add_modifier", stat="physical_attack", op="pct_add", value=0.12, duration=600, source="sunfire_pill")], group="buff",
         extra=dict(burst=True),
         recipe=recipe([("riverreed_ginseng_10", 1), ("ember_pepper", 1)], None, "fire", hidden=True, block="hidden"),
         icon=dict(mark="sun", pill="yellow", ink=("red", -2))),
    pill("stillwater_pill", "earth", "drop_leaf", 6, "Found by experiment: Mist Lotus, Soulbell and willow moss. Composure +40, heart demon -5.",
         [effect("add_composure", amount=40), effect("add_heart_demon", amount=-5)], cause="soul", group="utility",
         recipe=recipe([("mist_lotus", 1), ("soulbell_flower", 1), ("willow_moss", 1)], None, "water", hidden=True, block="hidden"),
         icon=dict(pill="indigo", ink=("navy", -1))),
    pill("cloudstep_pill", "heaven", "arrows", 8, "Found by experiment: Cloudtop Orchid and willow moss. +10% move speed for 20 minutes.",
         [effect("add_modifier", stat="move_speed", op="pct_add", value=0.10, duration=1200, source="cloudstep_pill")], group="buff",
         recipe=recipe([("cloudtop_orchid", 1), ("willow_moss", 2)], None, "wood", hidden=True, block="hidden"),
         icon=dict(pill="cloud", ink=("navy", -1))),
    pill("murky_pill", "plain", "drop_leaf", 8, "What a failed experiment leaves: grey, gritty, and good for nothing but a stomach ache. A trader "
         "gives a tael for it.", [], group="utility", extra=dict(value_override=1),
         icon=dict(vessel="loose", pill="mud", ink=("earth", -2), extra="grit"),
         sources=dict(mark="system")),
    # v1.2 Phase E: the Law and Monarch pills, past the Lantern Star Field's ceiling (the last rows of items.json). Their
    # recipes are Will-grade; Stargazer Ming sells the Law pills' to a Sphere Lord 3.
    pill("law_condensing_pill", "law", "arrows", 20, "Converts Sage Qi toward Law Qi. (Later zones.)", [], cause=DROP, group="utility", soul=DROP,
         ilv=105, section="pills.later",
         recipe=recipe([("star_lotus", 2), ("void_carapace", 1), ("eel_essence", 1)], 1800, "metal", grade="will",
                       learn={"observatory": dict(price=150, realm="sphere_lord_3")}),
         icon=dict(vessel="breakthrough", mark="law", pill="storm", ink=("plum", -1))),
    pill("law_touching_pill", "law", "gate", 20, "Supports the attempt to touch a World Law. (Later zones.)", [], cause=DROP, group="utility",
         soul=DROP, ilv=106, section="pills.later",
         recipe=recipe([("star_lotus", 1), ("leviathan_scale", 1), ("eel_essence", 2)], 2400, "water", grade="will",
                       learn={"observatory": dict(price=200, realm="sphere_lord_3")}),
         icon=dict(vessel="breakthrough", mark="eye_gate", pill="pearl", ink=("plum", -1))),
    pill("monarch_condensing_pill", "monarch", "knot", 25, "Helps the Monarch conversion. (Later zones.)", [], cause=DROP, group="utility",
         soul=DROP, ilv=115, section="pills.later",
         icon=dict(vessel="breakthrough", mark="crown", pill="pearl", ink=("red", -2)),
         sources=dict(mark="later")),
    pill("sigil_anchor_pill", "monarch", "knot", 25, "Anchors the Dao Sigil. (Later zones.)", [], cause=DROP, group="utility", soul=DROP,
         ilv=120, section="pills.later",
         icon=dict(vessel="breakthrough", mark="anchor", pill="seal", ink=("plum", -1)),
         sources=dict(mark="later")),
]
