"""S13 enemies.json and S32 loot_tables.json (Part 8 monsters and bosses)."""
from common import entries, titled
from legends import CHAINS as LEGENDS


def atk(id, windup, reach, mult=1.0, depth=26, alt=(-30, 60), **extra):   # S43 rule 10: the melee band
    d = {"id": id, "windup_s": windup, "active_s": extra.pop("active", 0.18), "recover_s": extra.pop("recover", 0.45),
         "hitbox": {"x": [-6, reach], "depth": depth, "alt": list(alt)}, "mult": mult}
    d.update(extra)
    return d


def mob(id, levels, role, element, page, drops, attacks, ai="melee", art=None, width=22, height=40, **extra):
    lv = levels if isinstance(levels, (list, tuple)) else (levels, levels)
    row = {"id": id, "name": extra.pop("name", titled(id)), "level": list(lv), "role": role, "element": element,
           "race": extra.pop("race", "beast"), "energy": extra.pop("energy", "none"),
           "ai": {"profile": ai, "aggro_range": extra.pop("aggro", 200), "flee_below": extra.pop("flee", 0.0),
                  "move_speed": extra.pop("speed", 90), "patrol": extra.pop("patrol", 140)},
           "attacks": attacks, "loot": extra.pop("loot", id), "drops": drops,
           "tameable": extra.pop("tameable", False),
           "collection": {"page": page, "kills_to_fill": 50} if page else None,
           "art": art or {"creature": id}, "half_width": width, "height": height}
    row.update(extra)
    # S43 rule 11: how the species gets about a vertical room (the navigation graph uses it).
    if "movement" not in row:
        prof = row["ai"]["profile"]
        fly = bool(row.get("flying", False))
        boss = role.endswith("boss")
        jump = MOVE_JUMP.get(id, 530 if prof in ("duelist", "humanoid", "leaper") or row["race"] == "human" else (430 if prof == "melee" else 0))
        row["movement"] = {"jump": 0 if fly or boss else jump, "climb": (row["race"] == "human" or id in CLIMBERS) and not boss,
                           "fly": fly, "drop": not boss and not fly}
    return row


# S46 / Part 8: ghosts and constructs are not beasts; demonic beasts need a Purifying Offering to tame; hollowed ones
# must be cleansed first. Each of these tames into its own species.
GHOSTS = {"paper_talisman_ghost", "mirror_wisp", "weeping_lantern"}
CONSTRUCTS = {"trial_puppet", "stone_guardian", "jade_sentinel", "river_sentinel", "gate_guardian"}
DEMONIC = {"green_viper": "green_viper", "mud_hound": "mud_hound", "mist_vulture": "mist_vulture"}
HOLLOWED = {"hollowed_boarlet": "cleansed_boarlet", "hollow_stag": "pale_stag"}


def beast_ranks(M):
    """Beast rank 1-9 from the Level band (1-9 is rank 1, 10-18 rank 2 ... 73+ rank 9), for beasts only; their nature
    (spirit, demonic, hollowed); and a core on death at 2% per rank from rank 2 (rolled in the World, S46)."""
    for m in M:
        if m["id"] in GHOSTS:
            m["race"] = "ghost"
        elif m["id"] in CONSTRUCTS:
            m["race"] = "construct"
        if m["race"] != "beast":
            continue
        m["beast_rank"] = min(9, (int(m["level"][0]) - 1) // 9 + 1)
        m["nature"] = "demonic" if m["id"] in DEMONIC else ("hollowed" if m["id"] in HOLLOWED else "spirit")
        if m["id"] in DEMONIC or m["id"] in HOLLOWED:
            m["tameable"] = True
            m["tame_species"] = DEMONIC.get(m["id"]) or HOLLOWED[m["id"]]


# Species that jump harder or softer than their profile suggests, and those that climb (S43 rule 11).
MOVE_JUMP = {"reed_frog": 600, "bamboo_monkey": 600, "cliff_ape": 530, "pebble_imp": 430, "mossback_toad": 430}
CLIMBERS = {"bamboo_monkey", "cliff_ape"}


HUMAN = {
    "mudwater_bandit": {"hair": "short_knot", "hair_color": 5, "shirt": "sleeveless", "pants": "martial", "shoes": "boots", "weapon": "dagger", "hat": "tied"},
    "bandit_archer": {"hair": "ponytail", "hair_color": 0, "shirt": "sleeveless", "pants": "cuffed", "shoes": "boots", "weapon": "bow", "hat": "tied"},
    "gorge_bandit_adept": {"hair": "long_tied", "hair_color": 2, "shirt": "vneck", "pants": "martial", "shoes": "folded", "weapon": "sword", "hat": "none"},
    # S47 rogue cultivators: what they carry in the open is what they drop.
    "rogue_cultivator": {"hair": "flowing", "hair_color": 1, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "sword", "hat": "none"},
    "rogue_treasure_adept": {"hair": "topknot", "hair_color": 4, "shirt": "scholar", "pants": "loose", "shoes": "slippers", "weapon": "none", "hat": "guan"},
    "drowned_acolyte": {"hair": "short_knot", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "slippers", "weapon": "staff", "hat": "none", "tint": "#9fc6c9"},
    "big_toad_tan": {"hair": "topknot", "hair_color": 5, "shirt": "sleeveless", "pants": "loose", "shoes": "boots", "weapon": "staff", "hat": "none"},
    "drowned_abbot": {"hair": "flowing", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "slippers", "weapon": "staff", "hat": "none", "tint": "#8fb7c2"},
    "elder_gu": {"hair": "long_tied", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "folded", "weapon": "none", "hat": "none"},
    "shen_lian": {"hair": "high_pony", "hair_color": 2, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "none", "hat": "none"},
    "wen_zhao": {"hair": "flowing", "hair_color": 0, "shirt": "cardigan", "pants": "martial", "shoes": "folded", "weapon": "sword", "hat": "none"},
    "young_master": {"hair": "flowing", "hair_color": 0, "shirt": "cardigan", "pants": "martial", "shoes": "folded", "weapon": "sword", "hat": "guan",
                     "shirt_dye": "crimson", "pants_dye": "ink"},
    # S49 Heaven Ranking: the valley's ranked cultivators you can challenge (existing parts and dyes only).
    "cloud_first_disciple": {"hair": "high_pony", "hair_color": 0, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "sword", "hat": "none",
                             "shirt_dye": "cloud"},
    "jade_first_disciple": {"hair": "topknot", "hair_color": 1, "shirt": "cardigan", "pants": "martial", "shoes": "folded", "weapon": "sword", "hat": "guan",
                            "shirt_dye": "jade"},
    "iron_crane_guo": {"hair": "short_knot", "hair_color": 2, "shirt": "sleeveless", "pants": "martial", "shoes": "boots", "weapon": "staff", "hat": "none",
                       "shirt_dye": "ink"},
    "hua_guard_captain": {"hair": "short_knot", "hair_color": 0, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "sword", "hat": "tied",
                          "shirt_dye": "crimson", "pants_dye": "ink"},
    # S49 heavenly phenomena: an older disciple who saw the clouds gather over you (existing parts and dyes only).
    "jealous_senior": {"hair": "long_tied", "hair_color": 3, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "sword", "hat": "none",
                       "shirt_dye": "grey", "pants_dye": "ink"},
    # S49 friendly duels: the four companions, as they look beside you.
    "duel_lan_yue": {"hair": "flowing", "hair_color": 4, "shirt": "cardigan", "pants": "scholar", "shoes": "slippers", "weapon": "staff", "hat": "none", "shirt_dye": "indigo"},
    "duel_tie_niu": {"hair": "short_knot", "hair_color": 0, "shirt": "sleeveless", "pants": "martial", "shoes": "boots", "weapon": "none", "hat": "none", "shirt_dye": "earth"},
    "duel_qiu_feng": {"hair": "high_pony", "hair_color": 0, "shirt": "vneck", "pants": "cuffed", "shoes": "boots", "weapon": "bow", "hat": "none", "shirt_dye": "jade"},
    "duel_bai_ling": {"hair": "ponytail", "hair_color": 2, "shirt": "disciple", "pants": "straight", "shoes": "slippers", "weapon": "sword", "hat": "none", "shirt_dye": "cloud"},
    # S49 grudges and bounties: named bandits, their hunters, and the men who settle scores.
    "mudwater_lieutenant": {"hair": "short_knot", "hair_color": 5, "shirt": "sleeveless", "pants": "martial", "shoes": "boots", "weapon": "sword", "hat": "headband",
                            "shirt_dye": "earth", "pants_dye": "ink"},
    "kuai_shan": {"hair": "short_knot", "hair_color": 5, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "spear", "hat": "tied", "shirt_dye": "ink"},
    "tan_the_younger": {"hair": "topknot", "hair_color": 0, "shirt": "sleeveless", "pants": "loose", "shoes": "boots", "weapon": "staff", "hat": "none", "shirt_dye": "ochre"},
    "gorge_chief": {"hair": "long_tied", "hair_color": 1, "shirt": "vneck", "pants": "martial", "shoes": "folded", "weapon": "sword", "hat": "guan", "shirt_dye": "grey"},
    "mudwater_cutthroat": {"hair": "ponytail", "hair_color": 5, "shirt": "sleeveless", "pants": "cuffed", "shoes": "boots", "weapon": "dagger", "hat": "tied", "shirt_dye": "ink"},
    "gorge_stalker": {"hair": "high_pony", "hair_color": 0, "shirt": "vneck", "pants": "cuffed", "shoes": "boots", "weapon": "bow", "hat": "headband", "shirt_dye": "grey"},
    "gu_enforcer": {"hair": "topknot", "hair_color": 0, "shirt": "scholar", "pants": "scholar", "shoes": "folded", "weapon": "staff", "hat": "weimao", "shirt_dye": "indigo"},
    "one_eye_pang": {"hair": "short_knot", "hair_color": 4, "shirt": "sleeveless", "pants": "martial", "shoes": "boots", "weapon": "dagger", "hat": "headband", "shirt_dye": "crimson"},
    "ferryman_lou": {"hair": "long_tied", "hair_color": 0, "shirt": "cardigan", "pants": "loose", "shoes": "folded", "weapon": "staff", "hat": "weimao", "shirt_dye": "earth"},
    "knife_hand_sui": {"hair": "ponytail", "hair_color": 1, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "dagger", "hat": "none", "shirt_dye": "crimson",
                       "pants_dye": "ink"},
    # S49 territory: the three rival sects that hold the spirit-stone mines (existing parts and dyes only).
    "ironpine_disciple": {"hair": "short_knot", "hair_color": 4, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "spear", "hat": "tied",
                          "shirt_dye": "ochre", "pants_dye": "ink"},
    "ironpine_warden": {"hair": "long_tied", "hair_color": 2, "shirt": "cardigan", "pants": "martial", "shoes": "folded", "weapon": "spear", "hat": "guan",
                        "shirt_dye": "ochre", "pants_dye": "earth", "cape": "solid"},
    "blackreed_disciple": {"hair": "ponytail", "hair_color": 1, "shirt": "vneck", "pants": "cuffed", "shoes": "boots", "weapon": "dagger", "hat": "weimao",
                           "shirt_dye": "ink", "pants_dye": "ink"},
    "blackreed_warden": {"hair": "flowing", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "folded", "weapon": "sword", "hat": "weimao",
                         "shirt_dye": "ink", "pants_dye": "indigo", "cape": "tattered"},
    "scarlet_kiln_disciple": {"hair": "high_pony", "hair_color": 0, "shirt": "disciple", "pants": "martial", "shoes": "boots", "weapon": "sword", "hat": "none",
                              "shirt_dye": "crimson", "pants_dye": "ink"},
    "scarlet_kiln_warden": {"hair": "topknot", "hair_color": 5, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "staff", "hat": "guan",
                            "shirt_dye": "crimson", "pants_dye": "crimson", "cape": "solid"},
    "trial_disciple": {"hair": "topknot", "hair_color": 0, "shirt": "disciple", "pants": "loose", "shoes": "slippers", "weapon": "none", "hat": "none"},
    "alliance_champion": {"hair": "topknot", "hair_color": 0, "shirt": "disciple", "pants": "martial", "shoes": "boots", "weapon": "spear", "hat": "guan",
                          "shirt_dye": "indigo", "pants_dye": "ink"},
    "ironroot_warden": {"hair": "short_knot", "hair_color": 4, "shirt": "sleeveless", "pants": "martial", "shoes": "boots", "weapon": "staff", "hat": "headband",
                        "shirt_dye": "earth", "pants_dye": "earth"},
    "canyon_brigand": {"hair": "ponytail", "hair_color": 3, "shirt": "vneck", "pants": "cuffed", "shoes": "boots", "weapon": "dagger", "hat": "weimao",
                       "shirt_dye": "ochre", "pants_dye": "earth"},
    # Phase E · the Starsea: pirates of the comet sails, deserters of the Alliance, and the Trial Hall's phantoms.
    "starsea_pirate": {"hair": "short_knot", "hair_color": 0, "shirt": "sleeveless", "pants": "cuffed", "shoes": "boots", "weapon": "sword", "hat": "headband",
                       "shirt_dye": "indigo", "pants_dye": "ink"},
    "nine_peaks_disciple": {"hair": "topknot", "hair_color": 2, "shirt": "disciple", "pants": "martial", "shoes": "boots", "weapon": "sword", "hat": "guan",
                            "shirt_dye": "grey", "pants_dye": "ink", "cape": "tattered"},
    "pirate_captain": {"hair": "long_tied", "hair_color": 5, "shirt": "vneck", "pants": "cuffed", "shoes": "boots", "weapon": "sword", "hat": "headband",
                       "shirt_dye": "crimson", "pants_dye": "ink", "cape": "tattered"},
    "presence_phantom": {"hair": "topknot", "hair_color": 0, "shirt": "scholar", "pants": "scholar", "shoes": "folded", "weapon": "none", "hat": "guan",
                         "shirt_dye": "white", "pants_dye": "white", "tint": "#b4a6ee"},
    "ninth_presence": {"hair": "flowing", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "folded", "weapon": "staff", "hat": "guan",
                       "shirt_dye": "white", "pants_dye": "white", "cape": "solid", "tint": "#d9ccff"},
}
NAMES = {"mudwater_lieutenant": "Lieutenant Kuai", "kuai_shan": "Kuai Shan", "tan_the_younger": "Tan the Younger", "gorge_chief": "Chief Yan Bo",
         "mudwater_cutthroat": "Mudwater Cutthroat", "gorge_stalker": "Gorge Stalker", "gu_enforcer": "Gu Family Enforcer",
         "one_eye_pang": "One-Eye Pang", "ferryman_lou": "Ferryman Lou", "knife_hand_sui": "Knife-Hand Sui",
         "duel_lan_yue": "Lan Yue", "duel_tie_niu": "Tie Niu", "duel_qiu_feng": "Qiu Feng", "duel_bai_ling": "Bai Ling",
         "young_master": "Young Master Luo Heng", "jealous_senior": "Senior Brother Hao Qian", "cloud_first_disciple": "Yun Zhiqiu", "jade_first_disciple": "Bai Yuheng",
         "iron_crane_guo": "\"Iron Crane\" Guo Ming", "hua_guard_captain": "Captain Lou Chen", "rogue_cultivator": "Rogue Cultivator", "rogue_treasure_adept": "Rogue Mirror Adept", "pirate_captain": "Comet Captain Rao", "nine_peaks_disciple": "Rogue Nine Peaks Disciple", "presence_phantom": "Presence of a Seat",
         "ninth_presence": "The Ninth Presence", "ironpine_disciple": "Ironpine Disciple", "ironpine_warden": "Warden Dai Song",
         "blackreed_disciple": "Blackreed Disciple", "blackreed_warden": "Warden Qu Heng", "scarlet_kiln_disciple": "Scarlet Kiln Disciple",
         "scarlet_kiln_warden": "Warden Rong Yan"}


def human(id):
    o = dict(HUMAN[id])
    o["name"] = NAMES.get(id, titled(id))
    o["body"] = "light"
    return {"avatar": o}


def d(item, chance=0.6, count=(1, 1), weight=1):
    return {"item": item, "chance": chance, "count": list(count), "weight": weight}


def build():
    M = [
        mob("mudshell_crab", 1, "normal", "water", "valley_shore", [d("crab_shell", 0.7), d("river_mud", 0.4)],
            [atk("pinch", 0.4, 40)], ai="slow_melee", speed=55, width=20, height=26, aggro=0),
        mob("reedtail_rat", 2, "normal", "none", "valley_shore", [d("rat_tail", 0.6)], [atk("bite", 0.35, 36)],
            ai="melee", speed=120, flee=0.25, width=18, height=22, aggro=150),
        mob("old_snapper", 3, "elite", "water", "valley_shore", [d("snapper_claw", 1.0)],
            [atk("claw_slam", 0.6, 74, 1.4, depth=34, knockback=40)], ai="snapper", speed=45, width=40, height=56,
            phases=[{"below": 0.5, "action": "dig_in", "duration": 3.0, "invulnerable": True}], appears_after={"item": "crab_shell", "count": 5},
            # Tuned for a Mortal with bare fists (83 HP, no defence): about 135 HP and a 9-point claw, so a player who
            # never steps out of the slam still wins with a tea or two, and one who reads the tell barely gets touched.
            hp_mult=0.24, attack_mult=0.33),
        mob("hollow_minnow", 1, "event", "hollow", None, [], [atk("nibble", 0.45, 30, 0.8)], ai="flyer", speed=80,
            hp_override=5, width=14, height=18, flying=True, hollowing=1),
        mob("hollowed_eel", 10, "event", "hollow", None, [], [atk("lunge", 1.0, 120, 0.5, depth=60, knockback=80)],
            ai="event_eel", invulnerable=True, width=60, height=120, flying=True),
        mob("trial_puppet", 2, "trial", "none", None, [d("entry_token", 1.0)], [atk("counter_palm", 0.5, 44, 1.0)],
            ai="guard_counter", speed=60, width=22, height=60, knockback_immune=True, no_death_penalty=True),
        mob("wild_boarlet", (1, 2), "normal", "earth", "willow_path", [d("boar_hide", 0.5), d("tough_meat", 0.5)],
            [atk("charge", 0.45, 40, 1.0, dash=70)], ai="charger", speed=80, width=22, height=30),
        mob("mossback_toad", (2, 3), "normal", "wood", "willow_path", [d("toad_oil", 0.5), d("moss", 0.5)],
            [atk("tongue_lash", 0.4, 110, 0.9)], ai="ranged_melee", speed=50, tameable=True, width=20, height=26),
        mob("rock_beetle", (4, 5), "normal", "earth", "quarry", [d("beetle_shell", 0.6), d("copper_ore", 0.3)],
            [atk("roll", 0.5, 40, 1.1, dash=90)], ai="charger", speed=60, width=20, height=24),
        mob("pebble_imp", (4, 6), "normal", "earth", "quarry", [d("riverstone", 0.5), d("pebble_core", 0.08)],
            [atk("pebble_throw", 0.4, 300, 0.9, projectile={"speed": 380, "art": "pebble"})], ai="ranged", speed=70, width=16, height=32,
            keep_distance=180),
        mob("stone_tortoise", (5, 7), "normal", "earth", "quarry", [d("tortoise_plate", 0.5), d("jadeiron", 0.15)],
            [atk("slam", 0.6, 80, 1.2, depth=40, both_sides=True, knockback=60)], ai="slow_melee", speed=35, width=36, height=40,
            hp_mult=1.4),
        mob("ironclaw_mole", (5, 7), "normal", "earth", "quarry", [d("mole_claw", 0.5), d("ore_dust", 0.6)],
            [atk("burst_claw", 0.6, 44, 1.2)], ai="burrower", speed=70, tameable=True, width=20, height=26),
        mob("reed_frog", (4, 6), "normal", "wood", "marsh", [d("frog_leg", 0.6), d("willow_moss", 0.3)],
            [atk("jump_kick", 0.35, 40, 1.0, dash=80)], ai="charger", speed=90, width=16, height=22),
        mob("marsh_leech", (5, 7), "normal", "water", "marsh", [d("leech_oil", 0.6)],
            [atk("latch", 0.4, 38, 0.8, dash=50, drain=0.3)], ai="melee", speed=40, width=20, height=16),
        mob("greyfin", (7, 11), "normal", "hollow_water", "marsh", [d("tiny_hollow_shard", 0.4)],
            [atk("leap_bite", 0.5, 44, 1.0, dash=100)], ai="leaper", speed=70, width=18, height=22, hollowing=3),
        mob("hollowed_boarlet", (7, 12), "normal", "hollow_earth", "marsh", [d("hollow_shard", 0.12), d("grey_hide", 0.5)],
            [atk("double_charge", 0.45, 40, 1.0, dash=70, repeat=2)], ai="charger", speed=85, width=22, height=30, hollowing=4),
        mob("bamboo_monkey", (10, 12), "normal", "wood", "bamboo", [d("bamboo_shoot", 0.6)],
            [atk("shoot_toss", 0.4, 280, 0.9, projectile={"speed": 420, "art": "bamboo"})], ai="ranged", speed=120, agile=True,
            tameable=True, width=18, height=34, steals_coins=True, keep_distance=150),
        mob("green_viper", (11, 14), "normal", "wood", "bamboo", [d("viper_fang", 0.5), d("venom_sac", 0.3)],
            [atk("strike", 0.35, 46, 1.0, status={"id": "poison", "chance": 0.35, "power": 0.02, "duration_s": 5})],
            ai="melee", speed=85, width=24, height=18),
        mob("thornback_boar", (13, 15), "elite", "wood", "bamboo", [d("thorn_hide", 1.0), d("ember_pepper", 0.6, (1, 2))],
            [atk("thorn_charge", 0.55, 50, 1.2, dash=110, knockback=60)], ai="charger", speed=80, width=34, height=44, thorns=0.1),
        mob("mudwater_bandit", (14, 19), "normal", "none", "road", [d("cloth", 0.5), d("rat_tail", 0.0)],
            [atk("slash", 0.4, 60, 1.0), atk("qi_strike", 0.55, 90, 1.3, damage_type="qi")], ai="humanoid", art=human("mudwater_bandit"),
            race="human", energy="primal_qi", speed=100, width=18, height=90, coin_mult=2.0, equipment_chance=0.05, faction="mudwater"),
        mob("stone_guardian", (17, 19), "normal", "earth", "road", [d("guardian_stone", 0.25), d("mountain_seal", 0.02)],
            [atk("fist_slam", 0.6, 70, 1.3, depth=36, knockback=60)], ai="slow_melee", speed=45, width=28, height=60, knockback_immune=True),
        mob("bandit_archer", (16, 20), "normal", "none", "road", [d("arrows", 0.6), d("bow_parts", 0.3)],
            [atk("arrow", 0.6, 420, 1.0, projectile={"speed": 600, "art": "arrow"})], ai="ranged", art=human("bandit_archer"),
            race="human", energy="primal_qi", speed=90, width=18, height=90, keep_distance=260, equipment_chance=0.05, faction="mudwater"),
        mob("mud_hound", (16, 20), "normal", "earth", "road", [d("hound_fang", 0.5)], [atk("bite", 0.35, 44, 1.0)],
            ai="melee", speed=130, pack=True, width=22, height=28),
        mob("jade_carp", (19, 22), "normal", "water", "bend", [d("jade_scale", 0.5), d("jade_carp_fish", 0.15)],
            [atk("tail_slap", 0.5, 50, 1.0, dash=90)], ai="leaper", speed=70, width=22, height=24),
        mob("tide_crab", (20, 23), "normal", "water", "bend", [d("tide_shell", 0.5), d("pearl", 0.15)],
            [atk("pinch", 0.45, 46, 1.1)], ai="guard_counter", speed=50, width=24, height=30, front_guard=0.6),
        mob("drowned_acolyte", (21, 25), "normal", "water", "shrine", [d("prayer_beads", 0.4), d("manual_page", 0.04)],
            [atk("staff_strike", 0.45, 80, 1.0), atk("bell_chant", 0.8, 0, 0.0, buff_allies=0.15)], ai="caster",
            art=human("drowned_acolyte"), race="human", energy="primal_qi", width=18, height=90),
        mob("paper_talisman_ghost", (22, 26), "normal", "soul", "shrine", [d("talisman_paper", 0.5), d("ink", 0.3)],
            [atk("talisman_throw", 0.5, 300, 1.0, damage_type="soul", projectile={"speed": 400, "art": "talisman"})],
            ai="flyer_ranged", speed=70, flying=True, width=20, height=40, weak_to="fire", phases_walls=True),
        mob("rapids_lizard", (28, 31), "normal", "water", "gorge", [d("lizard_scale", 0.5), d("pearl", 0.1)],
            [atk("tail_whip", 0.4, 60, 1.0, both_sides=True)], ai="melee", speed=130, width=26, height=22),
        mob("gorge_bandit_adept", (29, 33), "normal", "none", "gorge", [d("cloth", 0.4), d("manual_page", 0.06), d("manual_ember_burst", 0.03)],
            [atk("sword_arc", 0.45, 80, 1.1), atk("crescent", 0.6, 300, 1.2, damage_type="qi", projectile={"speed": 520, "art": "qi_arc"})],
            ai="humanoid", art=human("gorge_bandit_adept"), race="human", energy="primal_qi", width=18, height=90, guards=True,
            coin_mult=2.0, equipment_chance=0.06, faction="gorge"),
        # S47 rogue cultivators: elites whose visible weapon or treasure is a guaranteed drop, with a sealed pouch.
        mob("rogue_cultivator", (24, 26), "elite", "metal", None, [d("serpent_tongue_jian", 1.0), d("sealed_storage_pouch", 1.0)],
            [atk("serpent_thrust", 0.45, 90, 1.25), atk("sword_qi", 0.7, 320, 1.15, damage_type="qi", projectile={"speed": 540, "art": "qi_arc"})],
            ai="humanoid", art=human("rogue_cultivator"), race="human", energy="primal_qi", width=18, height=90, guards=True),
        mob("rogue_treasure_adept", (48, 50), "elite", "water", None, [d("bright_mirror", 1.0), d("sealed_storage_pouch", 1.0, (1, 2))],
            [atk("palm_of_tides", 0.5, 70, 1.2), atk("mirror_flash", 0.8, 300, 1.2, damage_type="qi", projectile={"speed": 520, "art": "qi_arc"})],
            ai="humanoid", art=human("rogue_treasure_adept"), race="human", energy="true_qi", width=18, height=90, guards=True),
        mob("boulder_serpent", (32, 35), "normal", "earth", "gorge", [d("serpent_scale", 0.5), d("jadeiron", 0.2)],
            [atk("boulder_roll", 0.6, 50, 1.2, dash=160)], ai="charger", speed=60, width=34, height=34),
        mob("mist_vulture", (34, 36), "normal", "wind", "gorge", [d("vulture_plume", 0.5)],
            [atk("dive", 0.6, 60, 1.2, dash=120)], ai="flyer", speed=100, flying=True, width=26, height=40),
        mob("cloudwing_crane", (37, 40), "normal", "wind", "cliffs", [d("cloud_feather", 0.5)],
            [atk("swoop", 0.5, 60, 1.0, dash=120)], ai="flyer", speed=110, flying=True, width=26, height=50),
        mob("stormwing_hawk", (38, 43), "normal", "thunder", "cliffs", [d("storm_feather", 0.5)],
            [atk("lightning_dive", 0.55, 60, 1.2, dash=140, status={"id": "shock", "chance": 0.3, "power": 0.2, "duration_s": 3})],
            ai="flyer", speed=140, flying=True, width=22, height=34,
            pet_book={"item": "pet_book_thunder_roar", "chance": 0.25, "elite_only": True}),   # S46: only the elite
        mob("cliff_ape", (41, 45), "normal", "earth", "cliffs", [d("ape_fur", 0.5), d("cloudtop_orchid", 0.05)],
            [atk("smash", 0.5, 60, 1.2), atk("boulder_throw", 0.7, 320, 1.3, projectile={"speed": 360, "art": "boulder"})],
            ai="humanoid", speed=90, width=28, height=56),
        mob("mist_wolf", (46, 50), "normal", "water", "mist_peak", [d("mist_pelt", 0.5)], [atk("lunge", 0.4, 50, 1.0, dash=60)],
            ai="melee", speed=150, pack=True, tameable=True, width=28, height=34, hidden_in_fog=True),
        mob("mirror_wisp", (47, 51), "normal", "soul", "mist_peak", [d("mirror_dust", 0.5)],
            [atk("soul_flash", 0.6, 240, 1.1, damage_type="soul", projectile={"speed": 500, "art": "soul_bolt"})],
            ai="flyer_ranged", speed=70, flying=True, width=18, height=30),
        mob("weeping_lantern", (50, 55), "normal", "soul", "mist_peak", [d("lantern_wick", 0.4), d("soul_wax", 0.4)],
            [atk("flare", 0.7, 90, 1.0, damage_type="soul", depth=50, both_sides=True,
                 status={"id": "confusion", "chance": 0.3, "power": 1, "duration_s": 2})], ai="flyer", speed=50, flying=True, width=18, height=44,
            elite_first_defeat=["mist_lantern_flame"]),   # the valley's Heavenly Flame (Part 8): the monastery's elite lantern carries it
        mob("jade_sentinel", (52, 56), "normal", "earth", "mist_peak", [d("jade_core", 0.08), d("formation_stone", 0.5)],
            [atk("halberd_sweep", 0.6, 90, 1.2, depth=36)], ai="slow_melee", speed=50, width=26, height=64, linked=True),
        mob("hollow_stag", (55, 59), "normal", "hollow_wood", "summit", [d("hollow_antler", 0.4), d("hollow_shard", 0.2)],
            [atk("antler_charge", 0.5, 60, 1.2, dash=140)], ai="charger", speed=120, width=30, height=56, hollowing=5, cleansable=True),
        mob("cloudpeak_roc", (58, 63), "normal", "wind", "summit", [d("roc_feather", 0.5), d("mystic_ore", 0.1)],
            [atk("wing_gust", 0.7, 160, 1.0, depth=60, knockback=120)], ai="flyer", speed=110, flying=True, width=40, height=50),
        # Azure Expanse (Act II) · Thunderhorn Plains
        mob("spark_weasel", (64, 66), "normal", "thunder", "azure", [d("spark_pelt", 0.45), d("storm_shard", 0.35)],
            [atk("static_bite", 0.35, 50, 1.0, dash=70),
             atk("spark_bolt", 0.55, 260, 1.1, damage_type="qi", projectile={"speed": 560, "art": "qi_arc"},
                 status={"id": "shock", "chance": 0.2, "power": 0.15, "duration_s": 2})],
            ai="leaper", speed=170, pack=True, width=24, height=22, tameable=False),
        mob("thunderhorn_rhino", (64, 69), "normal", "thunder", "azure", [d("thunder_horn", 0.4), d("storm_shard", 0.5, (1, 2)), d("tough_meat", 0.4)],
            [atk("thunder_charge", 0.7, 60, 1.35, dash=160, knockback=120, status={"id": "shock", "chance": 0.3, "power": 0.2, "duration_s": 3})],
            ai="charger", speed=95, width=40, height=50),
        # Azure Expanse (Act II) · Rimefrost Heights and Mirrorwater Lake
        mob("frost_lynx", (67, 70), "normal", "water", "azure", [d("rime_fang", 0.4), d("storm_shard", 0.45), d("frost_lotus", 0.08)],
            [atk("rime_pounce", 0.45, 70, 1.15, dash=120, status={"id": "slow", "chance": 0.35, "power": 0.3, "duration_s": 3})],
            ai="leaper", speed=160, pack=True, width=30, height=34, tameable=False),
        mob("snow_ape", (68, 72), "normal", "earth", "azure", [d("snow_ape_hide", 0.45), d("storm_shard", 0.5, (1, 2)), d("tough_meat", 0.3)],
            [atk("ice_slam", 0.8, 90, 1.45, depth=40, knockback=100, status={"id": "freeze", "chance": 0.15, "power": 1.0, "duration_s": 1.5}),
             atk("ice_throw", 0.9, 280, 1.1, projectile={"speed": 420, "art": "ice_shard"})],
            ai="slow_melee", speed=80, width=36, height=60),
        mob("azure_carp_dragonet", (68, 72), "normal", "water", "azure", [d("dragonet_scale", 0.45), d("storm_shard", 0.4)],
            [atk("water_orb", 0.7, 300, 1.15, damage_type="qi", projectile={"speed": 380, "art": "water_orb"})],
            ai="flyer_ranged", speed=90, flying=True, width=30, height=30),
        mob("river_sentinel", (70, 75), "normal", "water", "azure", [d("sentinel_core", 0.3), d("storm_shard", 0.6, (1, 2))],
            [atk("trident_sweep", 0.85, 110, 1.5, depth=40, knockback=90)],
            ai="guard_counter", speed=55, width=30, height=70, tameable=False),
        # Azure Expanse (Act II) · Gale Canyons
        mob("wind_kite", (73, 76), "normal", "wind", "azure", [d("kite_silk", 0.45), d("storm_shard", 0.5, (1, 2))],
            [atk("gust_dive", 0.55, 120, 1.25, dash=140, knockback=90)],
            ai="flyer", speed=140, flying=True, width=34, height=34, tameable=False),
        mob("canyon_harpy", (74, 78), "normal", "wind", "azure", [d("harpy_plume", 0.45), d("storm_shard", 0.55, (1, 2))],
            [atk("talon_rake", 0.5, 80, 1.3, dash=90, status={"id": "bleed", "chance": 0.25, "power": 0.015, "duration_s": 4}),
             atk("screech", 0.8, 220, 0.9, damage_type="soul", depth=80, status={"id": "slow", "chance": 0.4, "power": 0.3, "duration_s": 3})],
            ai="flyer", speed=120, flying=True, width=34, height=44, tameable=False),
        # Act II · Phase D: the Sunscar Desert and the Tomb of Sunscar.
        mob("sandstorm_scorpion", (73, 78), "normal", "earth", "azure", [d("scorpion_stinger", 0.45), d("storm_shard", 0.5, (1, 2)),
                                                                         d("sunglass_ore", 0.08)],
            [atk("tail_sting", 0.55, 76, 1.25, status={"id": "poison", "chance": 0.4, "power": 0.012, "duration_s": 5}),
             atk("pincer_snap", 0.4, 46, 1.0)],
            ai="melee", speed=115, pack=True, width=34, height=30),
        mob("dune_worm", (77, 81), "normal", "earth", "azure", [d("worm_glass_tooth", 0.45), d("storm_shard", 0.6, (1, 3))],
            [atk("sand_burst", 0.7, 130, 1.5, depth=50, knockback=110),
             atk("glass_spit", 0.8, 300, 1.1, projectile={"speed": 460, "art": "pebble"})],
            ai="burrower", speed=100, width=44, height=80),
        mob("terracotta_warden", 77, "normal", "earth", "azure", [d("terracotta_shard", 0.5), d("storm_shard", 0.5, (1, 2))],
            [atk("ge_chop", 0.8, 96, 1.3, depth=36, knockback=90)],
            ai="slow_melee", speed=70, width=22, height=100, race="construct", weak_to="water"),
        mob("tomb_king", 77, "dungeon_boss", "earth", "azure", [d("sun_crown_fragment", 1.0, (2, 3)), d("storm_shard", 1.0, (12, 18)),
                                                                d("sunglass_ore", 1.0, (3, 5))],
            [atk("glaive_sweep", 0.75, 190, 1.35, depth=70, knockback=120, both_sides=True, shatter=True),   # S47: breaks a natal weapon
             atk("sand_crescent", 0.9, 380, 1.2, damage_type="qi", projectile={"speed": 460, "art": "sand_crescent"}),
             atk("sun_flare", 1.1, 260, 1.5, damage_type="qi", depth=90, status={"id": "burn", "chance": 0.5, "power": 0.01, "duration_s": 4})],
            ai="boss_king", race="undead", energy="sage_qi", width=40, height=170, weak_to="water", hp_mult=0.35, attack_mult=0.8,
            phases=[{"below": 0.6, "action": "summon", "summon": "terracotta_warden", "summon_level": 74},
                    {"below": 0.3, "action": "enrage", "cooldown": 0.65, "damage": 1.3}], first_defeat=["sunscar_throne_ember"]),
        mob("canyon_brigand", (73, 76), "normal", "wind", None, [d("storm_shard", 0.5), d("spirit_stone_shard", 0.4, (1, 2))],
            [atk("dagger_flurry", 0.35, 50, 1.1), atk("throwing_knife", 0.5, 240, 1.0, projectile={"speed": 600, "art": "arrow"})],
            ai="duelist", art=human("canyon_brigand"), race="human", energy="sage_qi", width=18, height=90),
        # Act II · Phase E: the Skyport Wreck and the Starsea.
        mob("starsea_pirate", (79, 81), "normal", "metal", "azure", [d("comet_iron", 0.4), d("storm_shard", 0.55, (1, 2)),
                                                                    d("spirit_stone_shard", 0.4, (1, 2)), d("will_tempering_pill", 0.04)],
            [atk("cutlass_combo", 0.4, 70, 1.2), atk("boarding_hook", 0.6, 260, 1.0, projectile={"speed": 560, "art": "arrow"})],
            ai="duelist", art=human("starsea_pirate"), race="human", energy="sage_qi", width=18, height=90, pack=True),
        mob("nine_peaks_disciple", (76, 78), "normal", "metal", "azure", [d("alliance_badge", 0.45), d("storm_shard", 0.5, (1, 2))],
            [atk("peak_sword", 0.45, 84, 1.2), atk("nine_step_lunge", 0.7, 160, 1.3, dash=120, knockback=70)],
            ai="duelist", art=human("nine_peaks_disciple"), race="human", energy="sage_qi", width=18, height=90,
            name="Rogue Nine Peaks Disciple"),
        mob("pirate_captain", 80, "story_boss", "metal", None, [d("comet_iron", 1.0, (3, 5)), d("storm_shard", 1.0, (10, 15)),
                                                               d("will_tempering_pill", 1.0, (1, 2))],
            [atk("comet_cleave", 0.6, 130, 1.4, depth=50, knockback=110), atk("anchor_throw", 0.9, 330, 1.25, projectile={"speed": 520, "art": "pebble"}),
             atk("boarding_call", 1.0, 0, 0.0, summon="starsea_pirate")],
            ai="duelist", art=human("pirate_captain"), race="human", energy="sage_qi", width=20, height=94, name="Comet Captain Rao",
            hp_mult=1.5, attack_mult=0.9, phases=[{"below": 0.4, "action": "enrage", "cooldown": 0.7, "damage": 1.25},
                                                  # S48: cornered, the Captain burns his nascent soul (a telegraphed blast).
                                                  {"below": 0.12, "action": "self_detonate", "windup": 3.0, "radius": 280, "damage": 0.6}],
            first_defeat=["comet_tail_flame"]),
        mob("presence_phantom", 81, "normal", "none", None, [], [atk("weight_of_a_seat", 0.55, 90, 1.1, damage_type="qi")],
            ai="duelist", art=human("presence_phantom"), race="human", energy="sage_qi", width=18, height=90, name="Presence of a Seat"),
        mob("ninth_presence", 81, "normal", "none", None, [], [atk("ninth_seat_palm", 0.7, 120, 1.3, damage_type="qi", depth=50, knockback=100),
                                                              atk("crown_of_nine", 1.1, 240, 1.2, damage_type="soul", depth=90, both_sides=True,
                                                                  status={"id": "slow", "chance": 0.6, "power": 0.3, "duration_s": 3})],
            ai="duelist", art=human("ninth_presence"), race="human", energy="sage_qi", width=20, height=96, name="The Ninth Presence",
            hp_mult=12.0, attack_mult=1.2),
        mob("alliance_champion", 72, "trial", "metal", None, [], [atk("peak_thrust", 0.45, 110, 1.2, depth=30),
                                                                 atk("nine_step_sweep", 0.7, 150, 1.3, depth=50, knockback=90)],
            ai="duelist", art=human("alliance_champion"), race="human", width=18, height=90, spar=True),
        mob("ironroot_warden", 70, "trial", "earth", None, [], [atk("root_staff", 0.5, 90, 1.2, depth=36, knockback=80),
                                                               atk("iron_root_stomp", 0.9, 160, 1.3, depth=70, both_sides=True)],
            ai="duelist", art=human("ironroot_warden"), race="human", width=20, height=92, spar=True),
        # Bosses
        mob("big_toad_tan", 18, "dungeon_boss", "none", None, [d("mudwater_manual", 1.0)],
            [atk("club_swing", 0.55, 90, 1.2, depth=34, knockback=60), atk("call_bandits", 1.0, 0, 0.0, summon="mudwater_bandit")],
            ai="boss_tan", art=human("big_toad_tan"), race="human", energy="primal_qi", width=24, height=96,
            phases=[{"below": 0.5, "action": "drink_wine", "heal": 0.1, "breakable": "wine_jar"}], unique_drop="mudwater_cleaver",
            # The first dungeon boss teaches the pattern (dodge the club, break the wine jars) rather than walls it.
            hp_mult=0.6, attack_mult=0.8, pet_book={"item": "pet_book_frenzy", "chance": 0.35}, faction="mudwater", named=True),
        mob("riverbed_serpent", 25, "field_boss", "water", "bend", [d("serpent_core", 1.0), d("serpent_scale", 1.0, (2, 4))],
            [atk("bite", 0.6, 110, 1.3, depth=40), atk("tail_flood", 1.0, 260, 1.0, depth=80, both_sides=True)], ai="boss_serpent",
            width=70, height=150, respawn_min=45, flying=True, phases=[{"below": 0.5, "action": "flood"}]),
        mob("thousand_eye_toad", 68, "field_boss", "water", "azure", [d("mirror_eye", 1.0), d("storm_shard", 1.0, (6, 10)),
                                                                    d("dragonet_scale", 1.0, (2, 3))],
            [atk("belly_slam", 0.8, 140, 1.4, depth=60, knockback=140, both_sides=True),
             atk("tongue_lash", 0.6, 240, 1.2, depth=40),
             atk("mirror_gaze", 1.2, 0, 0.0, summon="azure_carp_dragonet")],
            ai="boss_toad", width=80, height=100, respawn_min=45,
            phases=[{"below": 0.5, "action": "summon"}], first_defeat=["cold_lamp_flame"]),
        mob("drowned_abbot", 27, "dungeon_boss", "water", None, [d("riverbreath_scroll", 1.0), d("drowned_robe", 1.0)],
            [atk("bell_shockwave", 0.7, 180, 1.2, depth=70, both_sides=True, knockback=80),
             atk("summon_ghosts", 1.2, 0, 0.0, summon="paper_talisman_ghost")], ai="boss_abbot", art=human("drowned_abbot"),
            race="human", energy="primal_qi", width=22, height=96, weak_to="fire",
            phases=[{"below": 0.66, "action": "flood"}, {"below": 0.33, "action": "summon"}], first_defeat=["bronze_bell", "shattered_moon_blade"]),
        mob("the_reflection", 36, "story_boss", "none", None, [], [atk("mirror_strike", 0.45, 70, 1.0)], ai="reflection",
            art={"avatar": "player"}, race="human", energy="primal_qi", width=18, height=90),
        # Gap report G1: every 25 on the heart-demon meter brings one of these into the Trial of Reflections.
        mob("heart_demon", 36, "normal", "none", None, [], [atk("whisper_of_doubt", 0.5, 70, 0.8, damage_type="soul")],
            ai="duelist", art={"avatar": "player", "tint": "#b0283c"}, race="human", energy="primal_qi", width=18, height=90,
            name="Heart Demon", hp_mult=0.5),
        mob("elder_gu", 53, "story_boss", "water", None, [d("smuggler_ledger", 1.0)], [atk("tide_palm", 0.5, 90, 1.2, damage_type="qi")],
            ai="humanoid", art=human("elder_gu"), race="human", energy="true_qi", width=18, height=90, flees_after_s=60, invulnerable=True),
        mob("hollow_behemoth", 58, "story_boss", "hollow_earth", None, [d("siege_medal", 1.0), d("mistjade_robe", 1.0)],
            [atk("stampede", 0.7, 90, 1.4, dash=240, knockback=120, shatter=True), atk("drone_burst", 1.0, 200, 1.0, both_sides=True, depth=70)],
            ai="boss_behemoth", width=80, height=140, hollowing=8),
        mob("gate_guardian", 63, "story_boss", "earth", None, [], [atk("ring_sweep", 0.7, 180, 1.3, both_sides=True, depth=70, knockback=100),
                                                                   atk("soul_gaze", 0.9, 320, 1.1, damage_type="soul", projectile={"speed": 500, "art": "soul_bolt"})],
            ai="boss_guardian", width=60, height=180, phases=[{"below": 0.66, "action": "soul_phase"}, {"below": 0.33, "action": "flight_phase"}]),
        mob("shen_lian", 4, "trial", "none", None, [], [atk("fish_gutting_fist", 0.4, 46, 1.0)], ai="duelist", art=human("shen_lian"),
            race="human", width=18, height=90, spar=True),
        mob("wen_zhao", 44, "trial", "wind", None, [], [atk("cloud_cut", 0.4, 80, 1.1), atk("crescent", 0.6, 300, 1.2, damage_type="qi",
                                                                                                  projectile={"speed": 540, "art": "qi_arc"})],
            ai="duelist", art=human("wen_zhao"), race="human", width=18, height=90, spar=True),
        mob("sparring_disciple", 10, "trial", "none", None, [], [atk("palm", 0.45, 46, 1.0)], ai="duelist", art=human("trial_disciple"),
            race="human", width=18, height=90, spar=True),
        # S49 Fame: a young master of a good family who hears your name and wants to prove he is better. He spars at
        # the challenged cultivator's own level.
        mob("young_master", 20, "trial", "fire", None, [], [atk("peacock_slash", 0.42, 70, 1.05),
                                                            atk("golden_crescent", 0.65, 280, 1.15, damage_type="qi",
                                                                projectile={"speed": 520, "art": "qi_arc"})],
            ai="duelist", art=human("young_master"), race="human", width=18, height=90, spar=True, name="Young Master Luo Heng"),
        # S49 Heaven Ranking: challenge the one ranked directly above you (they spar at their own Level that week).
        mob("cloud_first_disciple", 30, "trial", "wind", None, [], [atk("drifting_cut", 0.38, 80, 1.1), atk("cloud_crescent", 0.6, 300, 1.2, damage_type="qi",
                                                                                                          projectile={"speed": 560, "art": "qi_arc"})],
            ai="duelist", art=human("cloud_first_disciple"), race="human", width=18, height=90, spar=True, name="Yun Zhiqiu"),
        mob("jade_first_disciple", 31, "trial", "wood", None, [], [atk("jade_edge", 0.4, 80, 1.12), atk("verdant_thrust", 0.55, 120, 1.25, dash=170)],
            ai="duelist", art=human("jade_first_disciple"), race="human", width=18, height=90, spar=True, name="Bai Yuheng"),
        mob("iron_crane_guo", 34, "trial", "metal", None, [], [atk("crane_staff", 0.5, 90, 1.2, knockback=80), atk("iron_beak", 0.7, 100, 1.35, dash=200)],
            ai="duelist", art=human("iron_crane_guo"), race="human", width=20, height=92, spar=True, name="\"Iron Crane\" Guo Ming"),
        mob("hua_guard_captain", 24, "trial", "none", None, [], [atk("guard_cut", 0.4, 76, 1.1), atk("shield_rush", 0.6, 90, 1.2, dash=160, knockback=90)],
            ai="duelist", art=human("hua_guard_captain"), race="human", width=18, height=90, spar=True, name="Captain Lou Chen"),
        # S49 heavenly phenomena: a senior who cannot bear to see the heavens answer someone else. He spars at your
        # new level, right after the breakthrough.
        mob("jealous_senior", 20, "trial", "metal", None, [], [atk("envy_cut", 0.4, 72, 1.08), atk("thrust_through", 0.55, 110, 1.2, dash=160)],
            ai="duelist", art=human("jealous_senior"), race="human", width=18, height=90, spar=True, name="Senior Brother Hao Qian"),
        # S49 territory: the rival sects' mine guards and wardens. They come at the mine's own Level (territory.json).
        mob("ironpine_disciple", 10, "normal", "earth", None, [d("spirit_stone_shard", 0.5), d("cloth", 0.4)],
            [atk("pine_spear", 0.45, 96, 1.05), atk("rooted_lunge", 0.65, 150, 1.2, dash=150, knockback=60)],
            ai="humanoid", art=human("ironpine_disciple"), race="human", energy="primal_qi", width=18, height=90, name="Ironpine Disciple"),
        mob("ironpine_warden", 12, "elite", "earth", None, [d("spirit_stone_shard", 1.0, (2, 4)), d("manual_page", 0.25)],
            [atk("iron_bough_sweep", 0.55, 110, 1.25, both_sides=True, knockback=90), atk("pine_needle_rain", 0.8, 320, 1.1, damage_type="qi",
                                                                                         projectile={"speed": 520, "art": "qi_arc"}),
             atk("mountain_brace", 1.0, 150, 1.45, dash=180, knockback=120)],
            ai="duelist", art=human("ironpine_warden"), race="human", energy="primal_qi", width=20, height=92, name="Warden Dai Song"),
        mob("blackreed_disciple", 14, "normal", "water", None, [d("spirit_stone_shard", 0.5), d("leech_oil", 0.3)],
            [atk("reed_knife", 0.35, 60, 1.0), atk("marsh_needle", 0.55, 280, 1.0, projectile={"speed": 600, "art": "arrow"})],
            ai="humanoid", art=human("blackreed_disciple"), race="human", energy="primal_qi", width=18, height=90, name="Blackreed Disciple"),
        mob("blackreed_warden", 16, "elite", "water", None, [d("spirit_stone_shard", 1.0, (2, 4)), d("manual_page", 0.25)],
            [atk("black_tide_cut", 0.45, 90, 1.2), atk("drowning_crescent", 0.75, 320, 1.2, damage_type="qi", projectile={"speed": 520, "art": "qi_arc"}),
             atk("reed_step_thrust", 0.9, 130, 1.4, dash=200)],
            ai="duelist", art=human("blackreed_warden"), race="human", energy="primal_qi", width=18, height=90, name="Warden Qu Heng"),
        mob("scarlet_kiln_disciple", 64, "normal", "fire", None, [d("spirit_stone_shard", 0.6, (1, 2)), d("storm_shard", 0.3)],
            [atk("kiln_edge", 0.4, 84, 1.15), atk("ember_arc", 0.6, 300, 1.15, damage_type="qi", projectile={"speed": 540, "art": "qi_arc"},
                                                  status={"id": "burn", "chance": 0.3, "power": 0.01, "duration_s": 4})],
            ai="duelist", art=human("scarlet_kiln_disciple"), race="human", energy="sage_qi", width=18, height=90, name="Scarlet Kiln Disciple"),
        mob("scarlet_kiln_warden", 66, "elite", "fire", None, [d("spirit_stone_shard", 1.0, (3, 5)), d("storm_shard", 0.6, (1, 2))],
            [atk("furnace_staff", 0.5, 110, 1.3, knockback=100), atk("slag_rain", 0.85, 340, 1.15, damage_type="qi", projectile={"speed": 480, "art": "qi_arc"},
                                                                      status={"id": "burn", "chance": 0.5, "power": 0.012, "duration_s": 4}),
             atk("bellows_rush", 1.0, 150, 1.45, dash=220, knockback=130)],
            ai="duelist", art=human("scarlet_kiln_warden"), race="human", energy="sage_qi", width=20, height=92, name="Warden Rong Yan"),
        # S49 treasure births: the beast that wakes when a Spirit Fruit ripens (the room's level, +2).
        mob("fruit_guardian", 20, "elite", "wood", None, [d("thorn_hide", 1.0, (2, 3))],
            [atk("thorn_charge", 0.55, 60, 1.3, dash=220, knockback=110), atk("root_stamp", 0.8, 120, 1.2, both_sides=True, depth=60)],
            ai="charger", art={"creature": "thornback_boar"}, width=46, height=60, hp_mult=3.0, name="Fruit-Guardian Boar"),
        # S49 grudges. The Mudwater lieutenant yields at a fifth of his health: spare him (he remembers) or not (his
        # brother hunts you on the Caravan Road).
        mob("mudwater_lieutenant", 19, "elite", "none", None, [d("cloth", 1.0), d("mudwater_manual", 0.3)],
            [atk("slash", 0.4, 64, 1.15), atk("mud_cut", 0.6, 100, 1.3, damage_type="qi", knockback=60)], ai="humanoid",
            art=human("mudwater_lieutenant"), race="human", energy="primal_qi", width=18, height=90, faction="mudwater", named=True,
            surrenders=True, spare_debt="lieutenant_spared", kill_debt="lieutenant_killed", hp_mult=1.6, name="Lieutenant Kuai"),
        mob("kuai_shan", 20, "elite", "none", None, [d("cloth", 1.0)], [atk("spear_thrust", 0.45, 110, 1.2, depth=30),
                                                                      atk("sweep", 0.7, 120, 1.25, both_sides=True, knockback=80)],
            ai="humanoid", art=human("kuai_shan"), race="human", energy="primal_qi", width=18, height=90, faction="mudwater", named=True,
            hp_mult=1.8, name="Kuai Shan"),
        # Settling scores: a duel with Big Toad Tan's brother ends the Mudwater grudge; Chief Yan Bo's ends Old Scores.
        mob("tan_the_younger", 20, "trial", "none", None, [], [atk("staff_crack", 0.5, 80, 1.15, knockback=70), atk("belly_charge", 0.75, 90, 1.2, dash=180)],
            ai="duelist", art=human("tan_the_younger"), race="human", width=20, height=92, spar=True, name="Tan the Younger"),
        mob("gorge_chief", 33, "trial", "none", None, [], [atk("gorge_cut", 0.42, 80, 1.15), atk("echo_crescent", 0.65, 300, 1.2, damage_type="qi",
                                                                                            projectile={"speed": 540, "art": "qi_arc"})],
            ai="duelist", art=human("gorge_chief"), race="human", width=18, height=90, spar=True, name="Chief Yan Bo"),
        # Hunters: sent when a grudge passes its threshold. They fight at your level.
        mob("mudwater_cutthroat", 18, "elite", "none", None, [d("cloth", 1.0)], [atk("stab", 0.35, 50, 1.2), atk("lunge", 0.6, 90, 1.3, dash=160)],
            ai="humanoid", art=human("mudwater_cutthroat"), race="human", energy="primal_qi", width=18, height=90, faction="mudwater", hunter=True,
            name="Mudwater Cutthroat"),
        mob("gorge_stalker", 32, "elite", "none", None, [d("arrows", 1.0)], [atk("arrow", 0.55, 420, 1.15, projectile={"speed": 640, "art": "arrow"})],
            ai="ranged", art=human("gorge_stalker"), race="human", energy="primal_qi", width=18, height=90, keep_distance=280, faction="gorge",
            hunter=True, name="Gorge Stalker"),
        mob("gu_enforcer", 26, "elite", "water", None, [d("cloth", 1.0)], [atk("ledger_staff", 0.45, 80, 1.15), atk("tide_palm", 0.6, 240, 1.2,
                                                                                                             damage_type="qi", projectile={"speed": 500, "art": "qi_arc"})],
            ai="humanoid", art=human("gu_enforcer"), race="human", energy="true_qi", width=18, height=90, faction="smugglers", hunter=True,
            name="Gu Family Enforcer"),
        # Bounties: named targets posted on the town boards.
        mob("one_eye_pang", 20, "elite", "none", None, [d("cloth", 1.0), d("spirit_jade", 0.5)], [atk("cleave", 0.45, 70, 1.25),
                                                                                              atk("dirty_trick", 0.6, 60, 1.0, status={"id": "slow", "chance": 0.5, "power": 0.3, "duration_s": 3})],
            ai="humanoid", art=human("one_eye_pang"), race="human", energy="primal_qi", width=18, height=90, faction="mudwater", named=True,
            bounty=True, hp_mult=2.0, name="One-Eye Pang"),
        mob("ferryman_lou", 27, "elite", "water", None, [d("pearl", 1.0)], [atk("pole_sweep", 0.5, 90, 1.2, both_sides=True),
                                                                          atk("river_palm", 0.65, 240, 1.2, damage_type="qi", projectile={"speed": 500, "art": "qi_arc"})],
            ai="humanoid", art=human("ferryman_lou"), race="human", energy="true_qi", width=18, height=90, faction="smugglers", named=True,
            bounty=True, hp_mult=2.0, name="Ferryman Lou"),
        mob("knife_hand_sui", 34, "elite", "none", None, [d("manual_page", 1.0)], [atk("knife_flurry", 0.35, 60, 1.25), atk("thrown_knife", 0.55, 320, 1.1,
                                                                                                                      projectile={"speed": 700, "art": "arrow"})],
            ai="humanoid", art=human("knife_hand_sui"), race="human", energy="primal_qi", width=18, height=90, faction="gorge", named=True,
            bounty=True, hp_mult=2.0, name="Knife-Hand Sui"),
        # S49: a friendly duel with a companion at 3 hearts, at your own level.
        mob("duel_lan_yue", 20, "trial", "water", None, [], [atk("staff_sweep", 0.45, 64, 1.0, depth=34),
                                                            atk("tide_palm", 0.6, 240, 1.05, damage_type="qi", projectile={"speed": 480, "art": "qi_arc"})],
            ai="duelist", art=human("duel_lan_yue"), race="human", width=18, height=90, spar=True, name="Lan Yue"),
        mob("duel_tie_niu", 20, "trial", "earth", None, [], [atk("iron_fist", 0.4, 48, 1.15, knockback=70), atk("ox_charge", 0.7, 90, 1.2, dash=180)],
            ai="duelist", art=human("duel_tie_niu"), race="human", width=20, height=92, spar=True, name="Tie Niu"),
        mob("duel_qiu_feng", 20, "trial", "wood", None, [], [atk("reed_shot", 0.5, 320, 1.0, projectile={"speed": 620, "art": "arrow"}),
                                                            atk("kick_away", 0.35, 50, 0.9, knockback=90)],
            ai="duelist", art=human("duel_qiu_feng"), race="human", width=18, height=90, spar=True, name="Qiu Feng"),
        mob("duel_bai_ling", 20, "trial", "wind", None, [], [atk("line_cut", 0.42, 70, 1.05), atk("biting_array", 0.8, 200, 1.2, damage_type="qi", depth=60, both_sides=True)],
            ai="duelist", art=human("duel_bai_ling"), race="human", width=18, height=90, spar=True, name="Bai Ling"),
    ]
    # Starter spirit animals exist as enemy templates (non-hostile wild versions from Qi Unfurling 7).
    for pid, el in [("reed_otter", "water"), ("ember_fox", "fire"), ("jade_crane_chick", "wind")]:
        M.append(mob(pid, (19, 24), "normal", el, None, [], [atk("nip", 0.4, 36, 0.8)], ai="wild_pet", tameable=True, width=18, height=28,
                     passive=True))
    # S46: the Riverstone Ox grazes Quarry Rim from Cloud Stride 1; a mount-only spirit beast, tamed like the others.
    M.append(mob("riverstone_ox", (37, 38), "normal", "earth", None, [], [atk("horn_toss", 0.5, 50, 0.9)], ai="wild_pet", tameable=True,
                 width=30, height=46, passive=True))
    beast_ranks(M)
    entries("enemies.json", M)

    tables = []
    # Key items drop only while a quest still needs them (S32 quest drops).
    QUEST_DROPS = {"mudwater_bandit": [{"item": "mudwater_key", "chance": 0.3, "count": [1, 1], "quest": "the_caravan_road"}],
                   "dune_worm": [{"item": "sun_seal_shard", "chance": 0.5, "count": [1, 1], "quest": "the_sealed_gate"}],
                   "tomb_king": [{"item": "sunscar_seal", "chance": 1.0, "count": [1, 1], "quest": "the_tomb_king"}],
                   "starsea_pirate": [{"item": "ledger_page", "chance": 0.35, "count": [1, 1], "quest": "the_skyport_wreck"}]}
    # S47 legendary chains: each piece drops from its foe while that chain's quest still wants it.
    for ch in LEGENDS:
        for pid, pname, src, chance, zone in ch["pieces"]:
            QUEST_DROPS.setdefault(src, []).append({"item": pid, "chance": chance, "count": [1, 1], "quest": "legend_" + ch["id"]})
    for m in M:
        role = m["role"]
        drops = m.get("drops", [])
        table = {"id": m["loot"], "groups": [], "coins": {}, "equipment": {}, "rare": []}
        if role == "normal":
            table["groups"] = [{"chance": 0.6, "pick": [dict(x, weight=x.get("weight", 1)) for x in drops if x["chance"] > 0.2]}]
            table["rare"] = [x for x in drops if x["chance"] <= 0.2 and x["chance"] > 0]
            table["coins"] = {"chance": 0.2 * m.get("coin_mult", 1.0), "mult": 1}
            table["equipment"] = {"chance": m.get("equipment_chance", 0.03), "min_quality": "flawed"}
        elif role == "elite":
            table["guaranteed"] = [dict(x) for x in drops]
            table["coins"] = {"chance": 1.0, "mult": 6}
            table["equipment"] = {"chance": 0.25, "min_quality": "fine"}
            table["rare"] = [{"item": "manual_page", "chance": 0.05, "count": [1, 1]}]
        elif role in ("dungeon_boss", "field_boss", "story_boss"):
            table["guaranteed"] = [dict(x) for x in drops]
            table["coins"] = {"chance": 1.0, "mult": 40}
            table["equipment"] = {"chance": 1.0, "min_quality": "superior"} if role != "story_boss" else {}
        else:
            table["guaranteed"] = [dict(x) for x in drops if x["chance"] >= 1.0]
        if m["id"] in QUEST_DROPS:
            table["quest_drops"] = QUEST_DROPS[m["id"]]
        tables.append(table)
    tables.append({"id": "jar_valley_low", "groups": [{"chance": 0.5, "pick": [{"item": "rice", "weight": 2, "count": [1, 1]},
                   {"item": "willow_moss", "weight": 2, "count": [1, 2]}, {"item": "herbal_tea", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.5, "mult": 1}, "rare": [], "equipment": {}})
    tables.append({"id": "jar_valley_mid", "groups": [{"chance": 0.6, "pick": [{"item": "rice_ball", "weight": 2, "count": [1, 1]},
                   {"item": "spirit_stone_shard", "weight": 1, "count": [1, 1]}, {"item": "healing_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.6, "mult": 2}, "rare": [], "equipment": {}})
    tables.append({"id": "chest_valley", "guaranteed": [{"item": "spirit_stone_shard", "count": [1, 3], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "healing_pill", "weight": 2, "count": [1, 2]}, {"item": "manual_page", "weight": 1, "count": [1, 1]},
                                                         {"item": "qi_gathering_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 5}, "rare": [], "equipment": {"chance": 0.3, "min_quality": "fine"}})
    # Gu's Warehouse vault (S47): the Little Pagoda he hoarded, and his silver.
    tables.append({"id": "gus_vault", "guaranteed": [{"item": "little_pagoda", "count": [1, 1], "chance": 1.0}],
                   "groups": [], "coins": {"chance": 1.0, "mult": 12}, "rare": [], "equipment": {}})
    # The Drowned Abbot's sealed vault (SA3, S44): the Nine-Dragon Cauldron he kept, and a dungeon chest's worth besides.
    tables.append({"id": "abbots_vault", "guaranteed": [{"item": "nine_dragon_cauldron", "count": [1, 1], "chance": 1.0},
                                                        {"item": "spirit_soil", "count": [1, 1], "chance": 1.0},
                                                        {"item": "spirit_stone_shard", "count": [2, 4], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [1, 2]}, {"item": "foundation_guard_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [], "equipment": {}})
    # S46: the chest on the ledge beside Crane Falls keeps the Herb Whisper skill book.
    tables.append({"id": "falls_pool_chest", "guaranteed": [{"item": "pet_book_herb_whisper", "count": [1, 1], "chance": 1.0},
                                                             {"item": "mist_lotus", "count": [1, 2], "chance": 1.0}],
                   "groups": [], "coins": {"chance": 1.0, "mult": 6}, "rare": [], "equipment": {}})
    tables.append({"id": "chest_dungeon", "guaranteed": [{"item": "spirit_stone_shard", "count": [2, 4], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [1, 2]}, {"item": "foundation_guard_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [], "equipment": {"chance": 0.6, "min_quality": "fine"}})
    # Act II (S32): jars and chests of the Azure Expanse. Coins here are paid in Spirit Stones (zone coin_scale).
    tables.append({"id": "jar_expanse", "groups": [{"chance": 0.6, "pick": [{"item": "storm_shard", "weight": 2, "count": [1, 2]},
                   {"item": "spirit_stone_shard", "weight": 2, "count": [1, 2]}, {"item": "qi_restoration_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.6, "mult": 2}, "rare": [], "equipment": {}})
    tables.append({"id": "chest_expanse", "guaranteed": [{"item": "storm_shard", "count": [3, 6], "chance": 1.0},
                                                         {"item": "spirit_stone_shard", "count": [2, 4], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [1, 2]}, {"item": "stormsteel_ore", "weight": 2, "count": [1, 2]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [], "equipment": {"chance": 0.6, "min_quality": "fine"}})
    tables.append({"id": "chest_tomb", "guaranteed": [{"item": "storm_shard", "count": [6, 10], "chance": 1.0},
                                                      {"item": "sunglass_ore", "count": [2, 3], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [2, 3]},
                                                       {"item": "sovereign_settling_pill", "weight": 1, "count": [1, 1]},
                                                       {"item": "ember_cactus", "weight": 1, "count": [1, 2]}]}],
                   "coins": {"chance": 1.0, "mult": 16}, "rare": [], "equipment": {"chance": 0.8, "min_quality": "fine"}})
    # The pirates' strongbox on the Pirate Deck (chapter 15) and the Starsea Launch's cache.
    tables.append({"id": "chest_wreck", "guaranteed": [{"item": "storm_shard", "count": [6, 10], "chance": 1.0},
                                                       {"item": "comet_iron", "count": [2, 3], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [2, 3]},
                                                       {"item": "will_tempering_pill", "weight": 1, "count": [1, 2]},
                                                       {"item": "sky_ink", "weight": 1, "count": [2, 3]}]}],
                   "coins": {"chance": 1.0, "mult": 16}, "rare": [], "equipment": {"chance": 0.8, "min_quality": "fine"}})
    entries("loot_tables.json", tables)
    return M


if __name__ == "__main__":
    build()
