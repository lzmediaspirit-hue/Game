"""The Thunderhorn Plains' foes (M3; Act II, the Azure Expanse: the Stormgrass Verge, the Thunderhorn Flats and the
Lightning Scar, levels 64-69): the spark weasels, the stormgrass stags and the thunderhorn rhinos."""
from content.monsters import species

# M3. A long, low golden weasel of the storm plains (they run in packs): golden fur darker over its back, a white bib
# and belly, slate socks and small round ears, electric-blue eyes, its slim tail ending in a white-hot spark that
# crackles. It arches its back with its tail raised as the spark charges, arcs jumping off it (the tell, held: its bite's
# and its bolt's), and darts in to bite, lightning jumping off its jaws; beaten, it curls up on its side.
species("spark_weasel", plan="quadruped.mustelid", share=True, size=1.45,
        parts=dict(head=dict(eyes=dict(colour="SW_EYE")),
                   tail=dict(kind="brush", root=(-7.8, 1.0), n=8, length=9.0, r=(0.7, 1.0, 0.45), rest=10.0, droop=-12.0, tip=0.2,
                             flame=False, spark=True)),
        mats=dict(coat="sw_fur", pale="sw_white", dark="sw_sock", sock="sw_sock", tip="sw_spark"),
        motion={"idle": "sniff", "walk": "lope", "windup": "arch_charge", "attack": ("lunge_bite", {"zap": (1, 2)}), "hurt": "flinch",
                "death": "curl_side"},
        palette=["sw_fur", "sw_white", "sw_sock", "sw_spark"], accents=("sw_spark",), shadow=(10, 3), cycle=11.0, view=True,
        data=dict(level=(64, 66), role="normal", element="thunder", page="azure", drops=[("spark_pelt", 0.45), ("storm_shard", 0.35)],
                  attacks=[("static_bite", 0.35, 50, 1.0, dict(dash=70)),
                           ("spark_bolt", 0.55, 260, 1.1, dict(damage_type="qi", projectile={"speed": 560, "art": "qi_arc"},
                                                               status={"id": "shock", "chance": 0.2, "power": 0.15, "duration_s": 2}))],
                  ai="leaper", speed=170, pack=True, width=24, height=22, tameable=False))

# M3. A stag of the storm plains (wood): a pale storm-grey hide, the slate storm-grass grown over its back and down its nape in a
# mane like a storm cloud, a white belly and throat, calm dark eyes, whole branching antlers with storm-grass caught in their tines. Its row
# borrows the Cloud Stag's side-view sheet (the mount's); on the grid it has its own look. It drops its head with its
# antlers levelled and stamps a forehoof, the grass mane bristling (the tell, held), and charges to toss; beaten, its
# legs fold and it rolls onto its side.
species("stormgrass_stag", plan="quadruped.cervid", share=True, size=2.2,
        parts=dict(coat=dict(kind="saddle", chest=(-0.1, 5.0), belly=-0.45, saddle=0.25, reach=9.0),
                   crest=dict(kind="hackles", n=8, step=1.05, length=1.5, r=0.5, **{"from": 4.8}),
                   head=dict(eyes=dict(colour="INKY"), mist=False, antlers=dict(broken=(), tufts=True))),
        mats=dict(hide="ss_hide", head="ss_hide", stripe="ss_hide", coat="ss_hide", saddle="ss_grass", grass="ss_grass", pale="ss_pale",
                  antler="ss_antler", hoof="ss_hoof"),
        opts=dict(hollowed=False),
        palette=["ss_hide", "ss_grass", "ss_pale", "ss_antler", "ss_hoof"], shadow=(14, 4), cycle=13.0, view=True,
        data=dict(level=(64, 68), role="normal", element="wood", page="azure",
                  drops=[("tough_meat", 0.45), ("storm_shard", 0.5, (1, 2)), ("cloudtop_orchid", 0.05)],
                  attacks=[("antler_charge", 0.5, 60, 1.25, dict(dash=140, knockback=80))], ai="charger", speed=120, width=30, height=56,
                  art={"creature": "cloud_stag"}))

# M3. A heavy slate-blue rhino whose great horn stores lightning: a hide hanging in deep folds, rounded armour plates down
# its spine, a long head with a hooked lip, a long nasal horn curving up and back with a second behind it, small eyes. It
# lowers its head and paws the ground, snorting steam, as arcs crawl up its horn (the tell, held), and charges, the horn
# discharging on the hit; beaten, its legs buckle and it rolls onto its side.
species("thunderhorn_rhino", plan="quadruped.bovid", share=True, size=2.2,
        parts=dict(coat=dict(kind="folds", at=(3.4, -2.2), belly=-0.45),
                   crest=dict(kind="pebbles", stones=((4.6, 0.0, 2.0), (2.4, 0.0, 2.2), (0.2, 0.0, 2.3), (-2.0, 0.0, 2.2), (-4.2, 0.0, 2.0),
                                                      (-6.0, 0.0, 1.6)), moss=0),
                   head=dict(kind="rhino", at=((8.6, -0.6), (0.2, 0.5)), rest=-8.0, pitch=(-4.0, 14.0), skull=(3.0, 2.7, 2.5),
                             horn=((4.4, 0.0, -0.4), (5.5, 0.0, 1.5), (5.8, 0.0, 3.6), (5.0, 0.0, 5.4)), horn_r=(1.2, 0.9, 0.52, 0.12),
                             horn2=((2.2, 0.0, 1.0), (2.6, 0.0, 2.0), (2.4, 0.0, 2.8)), ears=((-1.2, 1.9, 2.0), (0.55, 0.4, 1.1)))),
        mats=dict(hide="tr_hide", head="tr_hide", stripe="tr_hide", hoof="tr_hoof", snout="tr_lip", lip="tr_lip", bristle="tr_fold",
                  horn="tr_horn", pebble="tr_plate", moss="tr_fold", fold="tr_fold"),
        motion={"windup": ("paw_ground", {"snort": (1, 3), "charge": (0.3, 0.6, 0.9, 1.0)}), "attack": ("charge_toss", {"zap": (1, 2)})},
        palette=["tr_hide", "tr_fold", "tr_plate", "tr_horn", "tr_lip", "tr_hoof"], shadow=(15, 4), cycle=14.0, view=True,
        data=dict(level=(64, 69), role="normal", element="thunder", page="azure",
                  drops=[("thunder_horn", 0.4), ("storm_shard", 0.5, (1, 2)), ("tough_meat", 0.4)],
                  attacks=[("thunder_charge", 0.7, 60, 1.35, dict(dash=160, knockback=120,
                                                                  status={"id": "shock", "chance": 0.3, "power": 0.2, "duration_s": 3}))],
                  ai="charger", speed=95, width=40, height=50))
