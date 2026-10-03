"""Herbs by age (S44 nature and roles, S45 ages and seeds; decision 45's fixed cultivation for a root eaten raw).

A herb family is one kind of plant; its members are its ages (10, 100, 1,000 or, in the Azure Expanse, 10,000 years),
each with its grade. A perfect harvest keeps the age, a miss or an early pick drops one tier, and an older herb stands
in for a younger one of its family in a recipe (garden.json). The engine names an aged herb "<Family> (100 yr)" and its
id "<family>_100"; the ten-year herb is the family's own id and name, unless `young_age` (ginseng says its age at ten).

- `nature`: hot herbs drive the Extraction band up, cold ones draw it down (S44);
- `roles` (each age): the recipe slots it can fill (principal, minister, assistant, envoy);
- `raw=dict(use=[...], toxicity=N)` (each age): eaten raw in need, 30% of its pill at twice the toxicity (gap report G1);
  `qi(share)` pays decision 45's fixed cultivation for the age's grade;
- `seed=dict(grade, desc, sources=...)`: the family's seed, for a garden bed (the section "seeds").
Where a herb grows (world.py's nodes) and what else hands it out (drops, chests, rewards) are named in `sources`.
"""
from content.items.dsl import effect, family, member, qi

PMA = ["principal", "minister", "assistant"]
PM = ["principal", "minister"]
MAE = ["minister", "assistant", "envoy"]
PAE = ["principal", "assistant", "envoy"]
GROWS = dict(gather=True, garden=True)   # every herb grows on a node and in a garden bed


def age(n, grade, desc, roles, raw=None, **kw):
    return member(n, grade, desc=desc, roles=roles, raw=raw, **kw)


def raw(toxicity, *use):
    return dict(use=list(use), toxicity=toxicity)


FAMILIES = [
    family("herb.willow_moss", kind="herb", nature="neutral",
           members=[age(10, "plain", "Soft moss from willow roots. The base of many remedies.", ["assistant", "envoy"],
                        raw(10, effect("heal", pct=0.09, over_s=5)))],
           seed=dict(grade="plain", desc="Dust-fine spores of willow moss, wrapped in a leaf. Granny Liu sells them.",
                     sources=dict(shop={"granny_liu": dict(price=6), "greyreed": dict(price=6)}, garden=True, reward=True)),
           sources=dict(GROWS, shop={"old_ma": dict(rotation=True), "mei_qing": {}}, chest=True, craft=True, drop=True, reward=True)),
    family("herb.riverreed_ginseng", kind="herb", nature="hot", young_age=True,
           members=[age(10, "common", "A ten-year riverreed ginseng root.", PMA, raw(20, qi(0.024)),
                        sources=dict(shop={"mei_qing": {}}, reward=True)),
                    age(100, "earth", "A century-old root with golden hairs; strong and rare.", PMA, raw(30, qi(0.05)),
                        sources=dict(shop={"old_pan": dict(price=4, sealed=True, rotation=True)}, reward=True)),
                    # S45 aged herbs: rare nodes ripen them, and a garden bed can age a planted herb.
                    age(1000, "heaven", "A thousand-year root, gold to the tip. It grows on the rock the Riverbed Serpent sleeps around.",
                        PM, raw(40, qi(0.1))),
                    # v1.1: the valley's Qi holds a herb at a thousand years; ten-thousand-year roots are the Azure Expanse's.
                    age(10000, "mystic", "A ten-thousand-year root, pale as jade and warm as a hand. The valley's Qi is too thin to grow one: "
                        "it ripens only on the Expanse's high ledges, or in an Expanse garden bed.", PM)],
           seed=dict(grade="common", desc="Red ginseng berries with the seed still inside. Granny Liu sells them.",
                     sources=dict(shop={"granny_liu": dict(price=20), "greyreed": dict(price=20)}, garden=True, auction=True)),
           sources=GROWS),
    family("herb.ember_pepper", kind="herb", nature="hot",
           members=[age(10, "common", "A fiery red pepper that warms the meridians.", MAE,
                        raw(24, effect("add_modifier", stat="physical_attack", op="pct_add", value=0.06, duration=60, source="raw_ember_pepper")),
                        sources=dict(craft=True, drop=True, reward=True)),
                    age(100, "earth", "A century-old ember pepper, dark red and hot enough to blister the hand that picks it.", MAE,
                        raw(30, effect("add_modifier", stat="physical_attack", op="pct_add", value=0.1, duration=60, source="raw_ember_pepper_100")))],
           seed=dict(grade="common", desc="Flat, pale pepper seeds that are warm to hold. Granny Liu sells them.",
                     sources=dict(shop={"granny_liu": dict(price=14), "greyreed": dict(price=14)}, garden=True)),
           sources=GROWS),
    family("herb.mist_lotus", kind="herb", nature="cold",
           members=[age(10, "earth", "A pale lotus that only opens in waterfall mist.", PMA,
                        raw(16, effect("add_modifier", stat="insight_rate", op="flat", value=0.15, duration=540, source="raw_mist_lotus")),
                        sources=dict(shop={"mei_qing": dict(price=35, realm="heart_tempering_5"), "alchemist_guild": dict(price=35, flag="guild_alchemy_adept"),
                                           "old_pan": dict(price=3, rotation=True), "port_apothecary": {}}, chest=True, reward=True)),
                    age(100, "heaven", "A century-old mist lotus. Its petals never quite dry.", PMA,
                        raw(24, effect("add_modifier", stat="insight_rate", op="flat", value=0.3, duration=540, source="raw_mist_lotus_100")))],
           seed=dict(grade="earth", desc="A lotus seed from a perfect harvest. No shop in the valley sells them.", sources=dict(garden=True, auction=True)),
           sources=GROWS),
    family("herb.cloudtop_orchid", kind="herb", nature="cold",
           members=[age(10, "heaven", "An orchid that grows on ledges only flyers can reach.", PM, raw(30, effect("add_body_xp", amount=90)),
                        sources=dict(shop={"mei_qing": dict(price=120, realm="cloud_stride_5"), "port_apothecary": {}}, drop=True, mail=True)),
                    age(100, "mystic", "A century-old orchid from the highest ledge. It smells of thin air.", PM, raw(40, effect("add_body_xp", amount=220)))],
           seed=dict(grade="heaven", desc="Orchid seed finer than flour, sealed in wax. Only old inheritances hold them.",
                     sources=dict(reward=True, auction=True)),
           sources=GROWS),
    family("herb.soulbell_flower", kind="herb", nature="neutral",
           members=[age(10, "heaven", "Its bell-shaped petals ring softly against the soul.", PAE, raw(16, effect("add_soul", amount=15)),
                        sources=dict(shop={"alchemist_guild": dict(price=180, flag="guild_alchemy_master"), "port_apothecary": {}}, reward=True)),
                    age(100, "mystic", "A century-old soulbell. Its ring carries in the soul for a whole breath.", PAE, raw(24, effect("add_soul", amount=35)))],
           seed=dict(grade="heaven", desc="A soulbell seed that hums when you hold it to your ear. Only old inheritances hold them.",
                     sources=dict(reward=True, auction=True)),
           sources=GROWS),
    family("herb.frost_lotus", kind="herb", nature="cold",
           members=[age(10, "spirit", "A lotus that blooms in snow on Rimefrost Heights. Cold to the touch, clear to the mind.", PM,
                        raw(30, effect("cure_injury", injury="meridian", max_severity=1), effect("add_composure", amount=20)))],
           sources=dict(GROWS, shop={"alchemist_guild": dict(price=320, flag="guild_alchemy_master"), "lanternfall_apothecary": dict(price=3),
                                     "free_market": dict(price=9, rotation=True)}, drop=True, reward=True, auction=True)),
    family("herb.ember_cactus", kind="herb", nature="hot",
           members=[age(10, "sage", "A cactus flower that stores the Sunscar sun. It glows like a coal long after dusk.", PM,
                        raw(30, effect("heal", pct=0.1, over_s=5)))],
           sources=dict(GROWS, shop={"lanternfall_apothecary": dict(price=3)}, chest=True, reward=True)),
    # v1.2 · the Lantern Star Field.
    family("herb.star_lotus", kind="herb", nature="cold",
           members=[age(10, "sovereign", "A lotus of the Drifting Shoals' starlit shallows. A small star sleeps in every seed head.", PMA,
                        raw(30, effect("add_soul", amount=60)))],
           sources=dict(GROWS, shop={"lanternfall_apothecary": dict(price=5)}, drop=True)),
]

# items.json keeps the herbs in the order they came to the game (the valley's young herbs, S45's aged ones, then the
# far zones'), and the seeds in Granny Liu's order.
ORDER = {"herbs": ["willow_moss", "riverreed_ginseng_10", "riverreed_ginseng_100", "ember_pepper", "mist_lotus", "cloudtop_orchid",
                   "soulbell_flower", "frost_lotus", "riverreed_ginseng_1000", "riverreed_ginseng_10000", "ember_pepper_100",
                   "mist_lotus_100", "cloudtop_orchid_100", "soulbell_flower_100", "ember_cactus", "star_lotus"],
         "seeds": ["willow_moss_seed", "ember_pepper_seed", "riverreed_ginseng_seed", "mist_lotus_seed", "cloudtop_orchid_seed",
                   "soulbell_flower_seed"]}
