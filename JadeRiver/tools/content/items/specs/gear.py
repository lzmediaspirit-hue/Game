"""Gear by family × grade (S47, P7b item_plan §2.9): the banded bases the equipment roll picks from (LootRules.is_banded),
nine grades a family. A weapon family is `gear(family, archetype=...)` over tools/data/gear.py ARCHETYPES (the archetype
that lists it); an armour family is a slot; the gourds are one family. Each grade's word, metal and binder come from the
tables here, so a new grade is a row in each and a new family one gear() line.

Every banded base drops (the equipment roll, by the Level band of its grade); from Common up the forge makes it (BANDS:
the grade's metal, a second metal and a binder; Sovereign and Will need a Master smith); the shops below sell some.
"""
from common import all_of, flag, realm
from content.items.dsl import gear, member, per
from gear import ARCHETYPES

GRADES = ["plain", "common", "earth", "heaven", "mystic", "spirit", "sage", "sovereign", "will"]
# P7b (item_plan §2.9, G1): Sovereign and Will, the Lantern Star Field's grades: driftsteel weapons and starsilk armour,
# lanternsteel and lanternsilk.
GRADE_WORD = {"plain": "training", "common": "iron", "earth": "jadeiron", "heaven": "cloudsteel", "mystic": "mistjade", "spirit": "stormsteel",
              "sage": "sunsteel", "sovereign": "driftsteel", "will": "lanternsteel"}
# The attribute a family asks for at each grade (the bow Agility, the staff and heavy sabre Body, the flute and brush
# Insight, the bell Essence).
ATTRIBUTE_REQ = {"plain": 8, "common": 18, "earth": 30, "heaven": 50, "mystic": 65, "spirit": 80, "sage": 92, "sovereign": 100, "will": 110}
# Garment dyes (data/parts.json "_dyes"): plain hemp is undyed brown, better cloth takes richer colour.
GRADE_DYE = {"plain": {"robe": "earth", "trousers": "earth"}, "common": {"robe": "grey", "trousers": "ink"},
             "earth": {"robe": "indigo", "trousers": "ink"}, "heaven": {"robe": "cloud", "trousers": "grey"},
             "mystic": {"robe": "white", "trousers": "jade"}, "spirit": {"robe": "indigo", "trousers": "cloud"},
             "sage": {"robe": "ochre", "trousers": "crimson"}, "sovereign": {"robe": "rose", "trousers": "indigo"},
             "will": {"robe": "white", "trousers": "ink"}}
# The forge's band of each grade: (metal, second metal, binder). P7b (item_plan §2.9): driftsteel from the Driftglass
# Bank, lanternsteel from the lantern cages' metal; a Master smith knows both, as the Mistjade Furnace.
BANDS = {"common": ("copper_ore", "riverstone", "boar_hide"), "earth": ("jadeiron", "riverstone", "jade_scale"),
         "heaven": ("cloudsteel_ore", "jadeiron", "cloud_feather"), "mystic": ("mystic_ore", "cloudsteel_ore", "roc_feather"),
         "spirit": ("stormsteel_ore", "mystic_ore", "spark_pelt"), "sage": ("sunglass_ore", "stormsteel_ore", "scorpion_stinger"),
         "sovereign": ("driftglass", "sunglass_ore", "jelly_silk"), "will": ("drone_shell", "driftglass", "cinder_ash")}
MASTER = {"requires_ranks": {"smithing": "master"}, "default": True}
# Decision 45: the spaces of the bag with no gourd worn, and of the Starter Spirit Gourd (stats.json bag.base).
BAG_BASE = 50


def forged(armour=False, learn=None):
    """A banded base's forge blueprint at its grade (none for Plain)."""
    def recipe(m):
        g = m["grade"]
        if g not in BANDS:
            return None
        metal, second, binder = BANDS[g]
        r = dict(craft="smithing", block="smithing.armour" if armour else "smithing.weapons")
        if armour:
            r.update(id="bp_{id}", inputs=[(metal, 3), (binder, 4)])
        else:
            r.update(inputs=[(metal, 6), (second, 3 if g == "common" else 4), (binder, 2)])
        if g in ("sovereign", "will"):
            r.update(MASTER)
        if learn:
            r["learn"] = learn
        return r
    return recipe


def sold(*tables):
    """Shop lines merged from several {shop: {grade: line}} tables."""
    out = {}
    for t in tables:
        for shop, by_grade in t.items():
            out.setdefault(shop, {}).update(by_grade)
    return out


# Where the banded gear sells.
SMITH = {"stoneford_smith": {"plain": {}, "common": dict(realm="qi_kindling_1")}}           # Stoneford: training and iron
SMITH_ROTATION = {"stoneford_smith": {"earth": dict(rotation=True)}}                       # and a jadeiron piece a day
ALLIANCE = {"alliance_factor": {"spirit": {}}}                                              # Cloudgate: stormsteel
IRONROOT_SAGE = {"ironroot_clan": {"sage": dict(requires=all_of(flag("clan_ironroot"), realm("sage_sovereign_1")))}}   # for kin
IRONROOT = sold({"ironroot_clan": {"spirit": {}}}, IRONROOT_SAGE)                         # the Ironroot forge
LANTERN = {"bastion_armoury": {"sovereign": dict(realm="will_manifest_1")}, "lanternwright": {"will": dict(realm="sphere_lord_2")}}
STORMSTEEL_RECIPES = {"stormsteel_smith": {"spirit": dict(price=40, realm="sage_1")}}       # Hong sells the stormsteel blueprints
DROPS = dict(drop=True)                                                                     # the banded equipment roll


def weapon(fam, look, name, attribute=None, shops=(), recipes=None, **sources):
    archetype = next(a for a, x in ARCHETYPES.items() if fam in x["families"])
    return gear(fam, kind="weapon", tiers=GRADES, words=GRADE_WORD, id="{word}_%s" % fam, name="{Word} %s" % name, appearance=look,
                archetype=archetype, attribute=attribute, attribute_req=per(ATTRIBUTE_REQ),
                # The weapon slot is open from the start, and a training weapon asks nothing of its wearer: a first-hour
                # foe may drop one (grades.json drop.starter), and the Weapon Hall hands out three.
                ilv=per(plain=5, default=None), extra=per(plain=dict(source=["weapon_hall"]), default=None),
                recipe=forged(learn=recipes), sources=dict(DROPS, shop=sold(LANTERN, *shops), **sources))


def armour(slot, rows, shops=(), recipes=None, **sources):
    """An armour slot over the grades: rows = [(grade, id, name, look)]."""
    ms = [member(g, g, id=i, name=n, appearance=look, dye=GRADE_DYE[g][slot] if slot in ("robe", "trousers") else None,
                 ilv=1 if i == "plain_straw_hat" else None) for g, i, n, look in rows]
    return gear(slot, kind="armour", members=ms, slot=slot, recipe=forged(armour=True, learn=recipes),
                sources=dict(DROPS, shop=sold(LANTERN, *shops), **sources))


FAMILIES = [
    # Weapons, in the order the forge and the equipment roll list them (FAMILY_APPEARANCE).
    weapon("gauntlets", "gauntlets", "Gauntlets", shops=(SMITH, ALLIANCE, IRONROOT), recipes=STORMSTEEL_RECIPES),
    weapon("jian", "sword", "Jian", shops=(SMITH, SMITH_ROTATION, ALLIANCE, IRONROOT), recipes=STORMSTEEL_RECIPES),
    weapon("spear", "spear", "Spear", shops=(SMITH, SMITH_ROTATION, ALLIANCE, IRONROOT), recipes=STORMSTEEL_RECIPES),
    weapon("short_blade", "dagger", "Short Blade", shops=(SMITH, ALLIANCE), recipes=STORMSTEEL_RECIPES),
    weapon("staff", "staff", "Staff", "body", shops=(SMITH, ALLIANCE, IRONROOT), recipes=STORMSTEEL_RECIPES),
    weapon("bow", "bow", "Bow", "agility", shops=(SMITH, ALLIANCE), recipes=STORMSTEEL_RECIPES),
    # S47 v1.1 families
    weapon("heavy_sabre", "sabre", "Heavy Sabre", "body", shops=(SMITH, SMITH_ROTATION)),
    weapon("fan", "fan", "Fan", shops=(SMITH, SMITH_ROTATION)),
    weapon("flute", "flute", "Flute", "insight", shops=(SMITH, SMITH_ROTATION)),
    # P7b (item_plan §2.9): the brush and the bell at every grade, so the formation master and the bell musician hold a
    # weapon of their own from Level 1 (G4)
    weapon("brush", "brush", "Brush", "insight", shops=(SMITH, SMITH_ROTATION)),
    weapon("bell", "bell", "Bell", "essence", shops=(SMITH, SMITH_ROTATION)),
    # Armour, a slot a family.
    armour("hat", [("plain", "plain_straw_hat", "Plain Straw Hat", "straw"), ("common", "bamboo_hat", "Bamboo Hat", "straw"),
                   ("earth", "jadeiron_hat", "Jadeiron Circlet", "headband"), ("heaven", "cloudsilk_hat", "Cloudsilk Band", "tied"),
                   ("mystic", "mistjade_hat", "Mistjade Circlet", "headband"), ("spirit", "stormsilk_hat", "Stormsilk Crown", "guan"),
                   # Sage grade (Sunscar, Sage Sovereign realm): sunsilk worked with desert glass; the veiled hat keeps the sun off.
                   ("sage", "sunsilk_hat", "Sunsilk Veil", "weimao"), ("sovereign", "starsilk_hat", "Starsilk Band", "tied"),
                   ("will", "lanternsilk_hat", "Lanternsilk Crown", "guan")],
           shops=({"stoneford_smith": {"common": {}}, "gu_trade_house": {"earth": dict(rotation=True)}}, ALLIANCE), reward=["plain"]),
    armour("robe", [("plain", "hemp_robe", "Hemp Robe", "sleeveless"), ("common", "cotton_robe", "Cotton Robe", "disciple"),
                    ("earth", "jadeiron_robe", "Jadeiron-Trimmed Robe", "cardigan"), ("heaven", "cloudsilk_robe", "Cloudsilk Robe", "vneck"),
                    ("mystic", "mistjade_robe", "Mistjade Robe", "scholar"), ("spirit", "stormsilk_robe", "Stormsilk Robe", "vneck"),
                    ("sage", "sunsilk_robe", "Sunsilk Robe", "scholar"), ("sovereign", "starsilk_robe", "Starsilk Robe", "disciple"),
                    ("will", "lanternsilk_robe", "Lanternsilk Robe", "cardigan")],
           shops=({"stoneford_smith": {"common": {}, "earth": dict(rotation=True)}, "gu_trade_house": {"heaven": dict(rotation=True)}}, ALLIANCE,
                  IRONROOT), recipes=STORMSTEEL_RECIPES),
    armour("trousers", [("plain", "hemp_trousers", "Hemp Trousers", "loose"), ("common", "cotton_trousers", "Cotton Trousers", "straight"),
                        ("earth", "jadeiron_trousers", "Jadeiron-Trimmed Trousers", "martial"),
                        ("heaven", "cloudsilk_trousers", "Cloudsilk Trousers", "cuffed"), ("mystic", "mistjade_trousers", "Mistjade Trousers", "scholar"),
                        ("spirit", "stormsilk_trousers", "Stormsilk Trousers", "martial"), ("sage", "sunsilk_trousers", "Sunsilk Trousers", "cuffed"),
                        ("sovereign", "starsilk_trousers", "Starsilk Trousers", "straight"),
                        ("will", "lanternsilk_trousers", "Lanternsilk Trousers", "martial")],
           shops=({"stoneford_smith": {"common": {}}}, ALLIANCE)),
    armour("boots", [("plain", "straw_sandals", "Straw Sandals", "slippers"), ("common", "cloth_boots", "Cloth Boots", "boots"),
                     ("earth", "jadeiron_boots", "Jadeiron Greaves", "folded"), ("heaven", "cloudsilk_boots", "Cloudsilk Boots", "boots"),
                     ("mystic", "mistjade_boots", "Mistjade Boots", "folded"), ("spirit", "stormsilk_boots", "Stormsilk Boots", "boots"),
                     ("sage", "sunsilk_boots", "Sunsilk Boots", "folded"), ("sovereign", "starsilk_boots", "Starsilk Slippers", "slippers"),
                     ("will", "lanternsilk_boots", "Lanternsilk Boots", "boots")],
           shops=({"stoneford_smith": {"common": {}}}, ALLIANCE, IRONROOT)),
    # Decision 45: the bag starts at 50 (stats.json bag.base); each gourd up the ladder adds its 5 on top of that, as it
    # added them on top of 25 before (the Starter Spirit Gourd 50, from 25; the Lantern Gourd 90, from 65).
    gear("spirit_gourd", kind="gourd", members=[
        member("plain", id="starter_gourd", name="Starter Spirit Gourd", bag=BAG_BASE, quick=5, ilv=1,
               sources=dict(mark="story", drop=False, shop=False)),        # the starting kit (AccountAuthority)
        member("common", id="bamboo_gourd", name="Bamboo Gourd", bag=BAG_BASE + 5, quick=8),
        member("earth", id="jadeiron_gourd", name="Jadeiron Gourd", bag=BAG_BASE + 10, quick=10),
        member("heaven", id="cloud_gourd", name="Cloud Gourd", bag=BAG_BASE + 15, quick=12),
        member("mystic", id="mistjade_gourd", name="Mistjade Gourd", bag=BAG_BASE + 20, quick=15),
        member("spirit", id="stormsteel_gourd", name="Stormsteel Gourd", bag=BAG_BASE + 25, quick=16),
        member("sage", id="sunsteel_gourd", name="Sunsteel Gourd", bag=BAG_BASE + 30, quick=18),
        member("sovereign", id="driftglass_gourd", name="Driftglass Gourd", bag=BAG_BASE + 35, quick=19),
        member("will", id="lantern_gourd", name="Lantern Gourd", bag=BAG_BASE + 40, quick=20)],
        sources=dict(shop=sold({"stoneford_general": {"common": {}},
                                "stoneford_smith": {"earth": dict(rotation=True), "heaven": dict(realm="cloud_stride_1"),
                                                    "mystic": dict(realm="heaven_glimpse_1")},
                                "gu_trade_house": {"earth": dict(rotation=True)}, "port_peddler": {"mystic": {}},
                                "alliance_factor": {"spirit": dict(realm="sage_1")}}, IRONROOT_SAGE, LANTERN))),
]


# P7b (item_plan §2.9, G5, G6): banded ladders of pet gear and furnaces, forged at the forge. A pet piece gains 1% of its
# stat a grade (defence half that) from the first piece of its kind (the named S46 piece at its base grade, items.py);
# its blueprint is its grade's metal and a beast part, known to every smith (the forge's grade cap gates it by realm).
PET_STEP = {"hp": 0.01, "attack": 0.01, "defence": 0.005, "mount_speed": 0.01}
PET_INPUTS = {"common": [("copper_ore", 2), ("hound_fang", 2)], "earth": [("jadeiron", 2), ("serpent_scale", 2)],
              "heaven": [("cloudsteel_ore", 2), ("ape_fur", 2)], "mystic": [("mystic_ore", 2), ("roc_feather", 2)],
              "spirit": [("stormsteel_ore", 2), ("snow_ape_hide", 2)], "sage": [("sunglass_ore", 2), ("harpy_plume", 2)],
              "sovereign": [("driftglass", 2), ("guardian_scale", 2)], "will": [("drone_shell", 2), ("wyrm_ash", 2)]}


def pet_ladder(slot, word, base_grade, base, first, text):
    ms = []
    for g in GRADES[GRADES.index(first):]:
        if g == base_grade:
            continue
        stats = {k: round(v + PET_STEP[k] * (GRADES.index(g) - GRADES.index(base_grade)), 3) for k, v in base.items()}
        ms.append(member(g, g, id="%s_%s" % (GRADE_WORD[g], word.lower().replace(" ", "_")), name="%s %s" % (GRADE_WORD[g].capitalize(), word),
                         stats=stats, desc=text.format(**{k: "%g" % (v * 100) for k, v in stats.items()})))
    return gear(slot, kind="pet_gear", members=ms, slot=slot,
                recipe=lambda m: dict(craft="smithing", inputs=PET_INPUTS[m["grade"]], default=True, block="smithing.pet_gear"))


def furnace(id, grade, name, desc, stats, inputs):
    """A furnace of the far zones' ladder: a Master smith's blueprint, known to every Master."""
    return member(grade, grade, id=id, name=name, desc=desc, stats=stats,
                  recipe=dict(craft="smithing", inputs=inputs, default=True, requires_ranks={"smithing": "master"}, block="smithing.furnaces"))


FAMILIES += [
    pet_ladder("pet_collar", "Collar", "common", {"hp": 0.10}, "earth", "+{hp}% HP for the animal that wears it."),
    pet_ladder("pet_talisman", "Beast Talisman", "earth", {"attack": 0.10, "defence": 0.05}, "common",
               "+{attack}% attack and +{defence}% defence for the animal that wears it."),
    pet_ladder("pet_saddle", "Saddle", "common", {"mount_speed": 0.10}, "earth", "A mount wearing it carries you {mount_speed}% faster."),
    # The furnace ladder on through Acts II and III (the valley's four furnaces and the Nine-Dragon Cauldron are named
    # pieces, items.py FURNACES).
    gear("banded", kind="furnace", members=[
        furnace("stormsteel_furnace", "spirit", "Stormsteel Furnace", "Blue-black stormsteel that drinks the lightning's heat. Ten pills to a batch.",
                {"band": 0.11, "batch": 10, "filter": 0.33, "yield": 0.16}, [("stormsteel_ore", 8), ("thunder_horn", 4), ("snow_ape_hide", 4)]),
        furnace("sunsteel_furnace", "sage", "Sunsteel Furnace", "Sunsteel set with desert glass that holds the fire's glow. Eleven pills to a batch.",
                {"band": 0.12, "batch": 11, "filter": 0.36, "yield": 0.17}, [("sunglass_ore", 8), ("scorpion_stinger", 4), ("worm_glass_tooth", 2)]),
        furnace("driftsteel_furnace", "sovereign", "Driftsteel Furnace",
                "Driftsteel walls lined with ground driftglass. Eleven pills to a batch, and little ash gets through.",
                {"band": 0.13, "batch": 11, "filter": 0.39, "yield": 0.18}, [("driftglass", 8), ("guardian_scale", 4), ("star_powder", 4)]),
        furnace("lanternsteel_furnace", "will", "Lanternsteel Furnace",
                "Cast from a lantern cage's metal; the fire in it never quite goes out. Twelve pills to a batch.",
                {"band": 0.14, "batch": 12, "filter": 0.42, "yield": 0.20}, [("drone_shell", 8), ("pyre_ember", 2), ("cinder_ash", 4)])]),
]
# artifacts.json lists the banded bases grade by grade, every family in its order within a grade; the forge's
# blueprints likewise.
ORDER = {"weapons": "grade", "armour": "grade", "smithing.weapons": "grade", "smithing.armour": "grade"}
# The weapon families' looks, as items.py's legendary weapons read them.
FAMILY_APPEARANCE = {f.stem: f.fields["appearance"] for f in FAMILIES if f.kind == "weapon"}
