"""S47 legendary chains (v1.1+): one questline per weapon family, shards -> restore -> awaken.

Each chain gathers three pieces: one from an old foe of the valley and two from the Azure Expanse. An Expert smith
restores them into a Mystic-grade legend, and a +10 legend awakens into its own skill (weapon awakening, S47). The
chains go on in later zones (a Spirit-grade reforging in the Outer Heavens, v1.4, and a Sage-grade one, v1.5); those
steps are listed here and are not built yet. Bare fists have no weapon to restore: the Fist Dao's chain is the
gauntlets'.
"""
from common import entries

# id, family, name, a line of lore, its gift (always on), three pieces (id, name, source, drop chance, zone),
# and the skill its awakening adds.
CHAINS = [
    {"id": "stone_drum", "family": "gauntlets", "weapon": "stone_drum_gauntlets", "name": "Stone Drum Gauntlets", "tint": "#c9a060",
     "lore": "A monk of the old river temple beat these like a drum, and the mountain answered.",
     "effect": {"stat": "physical_defense", "op": "pct_add", "value": 0.08},
     "pieces": [("stone_drum_knuckle", "Stone Drum Knuckle", "gorge_stalker", 0.5, "jade_river_valley"),
                ("stone_drum_cuff", "Stone Drum Cuff", "thunderhorn_rhino", 0.12, "azure_expanse"),
                ("stone_drum_heart", "Stone Drum Heart", "thousand_eye_toad", 1.0, "azure_expanse")],
     "skill": {"name": "Mountain Drum", "every_hits": 10, "mult": 2.4, "damage_type": "physical", "element": "earth", "shape": "ring", "reach": 170}},
    {"id": "riverlight", "family": "jian", "weapon": "riverlight_jian", "name": "Riverlight Jian", "tint": "#8fe0ff",
     "lore": "Forged in the shallows at dawn, so the saying goes, and quenched in the river's first light.",
     "effect": {"stat": "qi_attack", "op": "pct_add", "value": 0.08},
     "pieces": [("riverlight_hilt", "Riverlight Hilt", "drowned_abbot", 1.0, "jade_river_valley"),
                ("riverlight_blade", "Riverlight Blade", "azure_carp_dragonet", 0.12, "azure_expanse"),
                ("riverlight_soul", "Riverlight Soul Bead", "tomb_king", 1.0, "azure_expanse")],
     "skill": {"name": "Riverlight Cut", "every_hits": 10, "mult": 2.4, "damage_type": "qi", "element": "water", "art": "moon_crescent", "reach": 320}},
    {"id": "heron_reach", "family": "spear", "weapon": "heron_reach_spear", "name": "Heron's Reach", "tint": "#f2f2e8",
     "lore": "Its bearer stood in the reeds so still that herons landed on the shaft.",
     "effect": {"stat": "crit_chance", "op": "flat", "value": 0.04},
     "pieces": [("heron_spearhead", "Heron Spearhead", "knife_hand_sui", 0.5, "jade_river_valley"),
                ("heron_shaft", "Heron Shaft", "cloudpeak_roc", 0.12, "azure_expanse"),
                ("heron_tassel", "Heron Tassel", "scarlet_kiln_warden", 0.6, "azure_expanse")],
     "skill": {"name": "Heron Strike", "every_hits": 10, "mult": 2.6, "damage_type": "physical", "element": "metal", "art": "flying_sword", "reach": 380}},
    {"id": "reedwhisper", "family": "short_blade", "weapon": "reedwhisper_dagger", "name": "Reedwhisper Dagger", "tint": "#9fd07a",
     "lore": "It makes no more sound than wind in the reeds. Its last owner was never heard coming.",
     "effect": {"stat": "evasion", "op": "pct_add", "value": 0.08},
     "pieces": [("reedwhisper_edge", "Reedwhisper Edge", "one_eye_pang", 0.5, "jade_river_valley"),
                ("reedwhisper_grip", "Reedwhisper Grip", "frost_lynx", 0.12, "azure_expanse"),
                ("reedwhisper_sheath", "Reedwhisper Sheath", "tomb_king", 1.0, "azure_expanse")],
     "skill": {"name": "Whisper Through Reeds", "every_hits": 8, "mult": 1.8, "damage_type": "physical", "element": "wood", "art": "flying_sword", "reach": 300}},
    {"id": "ferryman", "family": "staff", "weapon": "ferrymans_pole", "name": "The Ferryman's Pole", "tint": "#b08a5a",
     "lore": "A ferryman poled the dead across the river with it for three hundred years, and never once lost his footing.",
     "effect": {"stat": "max_hp", "op": "pct_add", "value": 0.06},
     "pieces": [("ferryman_iron_cap", "Ferryman's Iron Cap", "ferryman_lou", 0.6, "jade_river_valley"),
                ("ferryman_oak_shaft", "Ferryman's Oak Shaft", "river_sentinel", 0.12, "azure_expanse"),
                ("ferryman_knot", "Ferryman's Knot", "thousand_eye_toad", 1.0, "azure_expanse")],
     "skill": {"name": "Pole the Current", "every_hits": 10, "mult": 2.2, "damage_type": "physical", "element": "water", "shape": "ring", "reach": 190}},
    {"id": "mountainsplit", "family": "heavy_sabre", "weapon": "mountainsplit_sabre", "name": "Mountainsplit Sabre", "tint": "#d8dde0",
     "lore": "They say it split a hill in two. The hill, they add, had it coming.",
     "effect": {"stat": "physical_attack", "op": "pct_add", "value": 0.06},
     "pieces": [("mountainsplit_spine", "Mountainsplit Spine", "riverbed_serpent", 1.0, "jade_river_valley"),
                ("mountainsplit_edge", "Mountainsplit Edge", "snow_ape", 0.12, "azure_expanse"),
                ("mountainsplit_guard", "Mountainsplit Guard", "scarlet_kiln_warden", 0.6, "azure_expanse")],
     "skill": {"name": "Split the Mountain", "every_hits": 12, "mult": 3.0, "damage_type": "physical", "element": "earth", "shape": "ring", "reach": 150}},
    {"id": "seven_winds", "family": "fan", "weapon": "seven_winds_fan", "name": "Seven Winds Fan", "tint": "#c8e0f0",
     "lore": "Six winds answer anyone who waves it. The seventh answers only a friend.",
     "effect": {"stat": "qi_attack", "op": "pct_add", "value": 0.06},
     "pieces": [("seven_winds_rib", "Seven Winds Rib", "rogue_treasure_adept", 0.5, "jade_river_valley"),
                ("seven_winds_silk", "Seven Winds Silk", "wind_kite", 0.12, "azure_expanse"),
                ("seven_winds_pin", "Seven Winds Pin", "canyon_harpy", 0.12, "azure_expanse")],
     "skill": {"name": "The Seventh Wind", "every_hits": 10, "mult": 2.2, "damage_type": "qi", "element": "wind", "art": "sand_crescent", "reach": 340}},
    {"id": "crane_mourning", "family": "flute", "weapon": "crane_mourning_flute", "name": "Crane Mourning Flute", "tint": "#e8e4f8",
     "lore": "Carved from the wing bone of a crane that outlived its mate. Every tune it plays is a little sad.",
     "effect": {"stat": "soul_attack", "op": "pct_add", "value": 0.08},
     "pieces": [("crane_mouthpiece", "Crane Bone Mouthpiece", "big_toad_tan", 1.0, "jade_river_valley"),
                ("crane_jade_body", "Crane Jade Body", "spark_weasel", 0.12, "azure_expanse"),
                ("crane_tassel", "Crane Tassel", "thousand_eye_toad", 1.0, "azure_expanse")],
     "skill": {"name": "Crane's Lament", "every_hits": 10, "mult": 2.0, "damage_type": "soul", "element": "none", "art": "note", "reach": 340}},
    {"id": "dragonfly", "family": "bow", "weapon": "dragonfly_bow", "name": "Dragonfly Bow", "tint": "#7ad0c0",
     "lore": "Light as a dragonfly's wing, and its arrows turn in the air the way a dragonfly does.",
     "effect": {"stat": "crit_damage", "op": "flat", "value": 0.12},
     "pieces": [("dragonfly_limb", "Dragonfly Limb", "gu_enforcer", 0.5, "jade_river_valley"),
                ("dragonfly_string", "Dragonfly String", "sandstorm_scorpion", 0.12, "azure_expanse"),
                ("dragonfly_sight", "Dragonfly Sight", "tomb_king", 1.0, "azure_expanse")],
     "skill": {"name": "Dragonfly Volley", "every_hits": 8, "mult": 1.6, "damage_type": "physical", "element": "wind", "art": "arrow", "reach": 420, "count": 3}},
]

# The chain's later steps, in zones not built yet (S47: legendary chains complete by v1.4-1.5).
LATER = [{"grade": "spirit", "zone": "outer_heavens", "version": "1.4", "step": "reforge"},
         {"grade": "sage", "zone": "outer_heavens", "version": "1.5", "step": "reforge"}]

RESTORE = {"station": "forge_anvil", "rank": "expert", "grade": "mystic", "materials": [("mystic_ore", 4), ("refining_essence", 8)]}


def piece_rows():
    """(item id, name, chain) for every piece, in order."""
    for ch in CHAINS:
        for i, (pid, pname, src, chance, zone) in enumerate(ch["pieces"]):
            yield pid, pname, ch, i


def build():
    rows = []
    for ch in CHAINS:
        rows.append({"id": ch["id"], "family": ch["family"], "weapon": ch["weapon"], "name": ch["name"],
                     "quest": "legend_" + ch["id"],
                     "pieces": [{"item": p[0], "source": p[2], "chance": p[3], "zone": p[4]} for p in ch["pieces"]],
                     "restore": {"recipe": ch["weapon"], "station": RESTORE["station"], "rank": RESTORE["rank"], "grade": RESTORE["grade"]},
                     "awaken": {"enhance": 10, "dao_tier": 4, "item": "weapon_soul_crystal", "skill": ch["skill"]},
                     "later": LATER})
    entries("legendary_chains", rows)


if __name__ == "__main__":
    build()
