"""S13 enemies.json and S32 loot_tables.json (Part 8 monsters and bosses).

A species with a spec in the monster engine (tools/content/monsters, audit 45 §6.2) has its row made from its spec
(`spec_row`, through mob(), atk() and d() here) and says its own loot extras (starter, early finds, quest drops); the
rows below are the hand-written foes', and a spec's row sits where it always did (a new spec's comes after them)."""
import os
import sys

from common import entries, titled, run_cli
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # tools/: the content engines
from content import monsters as MON  # noqa: E402
from legends import CHAINS as LEGENDS
import technique_hand as LOST_HAND
LOST_MANUALS = {s["src"]["item"]: s["id"] for s in LOST_HAND.LOST if s["src"]["kind"] == "drop"}   # P13a: manual -> lost art


def atk(id, windup, reach, mult=1.0, depth=26, alt=(-30, 60), **extra):   # S43 rule 10: the melee band
    d = {"id": id, "windup_s": windup, "active_s": extra.pop("active", 0.18), "recover_s": extra.pop("recover", 0.45),
         "hitbox": {"x": [-6, reach], "depth": depth, "alt": list(alt)}, "mult": mult}
    d.update(extra)
    return d


# Decision 27: a card fills at 50 and is studied through at its mark here (the page's second seal): 500 for a common
# beast, fewer for an elite and a boss, which cannot be met as often.
MASTER = {"normal": 500, "elite": 200}


def mob(id, levels, role, element, page, drops, attacks, ai="melee", art=None, width=22, height=40, **extra):
    lv =levels if isinstance(levels, (list, tuple)) else (levels, levels)
    if "equipment_chance" in extra:
        EQUIPMENT_CHANCE[id] = extra.pop("equipment_chance")
    row = {"id": id, "name": extra.pop("name", titled(id)), "level": list(lv), "role": role, "element": element,
           "race": extra.pop("race", "beast"), "energy": extra.pop("energy", "none"),
           "ai": {"profile": ai, "aggro_range": extra.pop("aggro", 200), "flee_below": extra.pop("flee", 0.0),
                  "move_speed": extra.pop("speed", 90), "patrol": extra.pop("patrol", 140)},
           "attacks": attacks, "loot": extra.pop("loot", id), "drops": drops,
           "tameable": extra.pop("tameable", False),
           "collection": {"page": page, "kills_to_fill": 50, "kills_to_master": MASTER.get(role, 100)} if page else None,
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
# Hollowed beasts with no cleansed species to tame into (v1.2): Hollowed in nature, never tamed.
HOLLOW_UNTAMED = {"hollowed_wyrmling"}


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
        m["nature"] = "demonic" if m["id"] in DEMONIC else ("hollowed" if m["id"] in HOLLOWED or m["id"] in HOLLOW_UNTAMED else "spirit")
        if m["id"] in DEMONIC or m["id"] in HOLLOWED:
            m["tameable"] = True
            m["tame_species"] = DEMONIC.get(m["id"]) or HOLLOWED[m["id"]]


# Species that jump harder or softer than their profile suggests, and those that climb (S43 rule 11).
MOVE_JUMP = {"reed_frog": 600, "bamboo_monkey": 600, "cliff_ape": 530, "pebble_imp": 430, "mossback_toad": 430}
CLIMBERS = {"bamboo_monkey", "cliff_ape"}


# The people's outfits (the side view's avatar; the top-down figure dresses them in the same). A species with a spec in
# the monster engine says its own (content.monsters.person: the Mudwater bandits and archers, Lieutenant Kuai, Big Toad
# Tan, the drowned acolytes and their abbot, the rogue cultivators and the rogue mirror adept, the gorge's bandit adepts, Elder
# Gu).
HUMAN = {
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
    # M4: the Starsea's pirates, deserters and Trial Hall phantoms, Blackmast's gunners and Admiral, and the Ashborn are
    # monster engine species now: their outfits are their specs' person() (tools/content/monsters/specs).
}
NAMES = {"kuai_shan": "Kuai Shan", "tan_the_younger": "Tan the Younger", "gorge_chief": "Chief Yan Bo",
         "mudwater_cutthroat": "Mudwater Cutthroat", "gorge_stalker": "Gorge Stalker", "gu_enforcer": "Gu Family Enforcer",
         "one_eye_pang": "One-Eye Pang", "ferryman_lou": "Ferryman Lou", "knife_hand_sui": "Knife-Hand Sui",
         "duel_lan_yue": "Lan Yue", "duel_tie_niu": "Tie Niu", "duel_qiu_feng": "Qiu Feng", "duel_bai_ling": "Bai Ling",
         "young_master": "Young Master Luo Heng", "jealous_senior": "Senior Brother Hao Qian", "cloud_first_disciple": "Yun Zhiqiu", "jade_first_disciple": "Bai Yuheng",
         "iron_crane_guo": "\"Iron Crane\" Guo Ming", "hua_guard_captain": "Captain Lou Chen",
         "ironpine_disciple": "Ironpine Disciple", "ironpine_warden": "Warden Dai Song",
         "blackreed_disciple": "Blackreed Disciple", "blackreed_warden": "Warden Qu Heng", "scarlet_kiln_disciple": "Scarlet Kiln Disciple",
         "scarlet_kiln_warden": "Warden Rong Yan"}


def human(id):
    o = dict(HUMAN[id])
    o["name"] = NAMES.get(id, titled(id))
    o["body"] = "light"
    return {"avatar": o}


def d(item, chance=0.6, count=(1, 1), weight=1):
    return {"item": item, "chance": chance, "count": list(count), "weight": weight}


# P7b (item_plan §4.1): each source's equipment roll, its chance and quality floor (about 6 pieces an hour of hunting).
# A bandit, brigand or pirate carries more (mob(equipment_chance=...), kept in EQUIPMENT_CHANCE for its loot table).
# The first rooms' foes (STARTER) roll starter gear a little more often (docs/research/player_motivation.md §3.4); the
# first weapon and the pity of their first pieces are grades.json drop.starter's.
EQUIPMENT = {"normal": (0.012, "flawed"), "elite": (0.08, "common"), "boss": (1.0, "superior"), "event": (0.012, "flawed"),
             "starter": (0.02, "flawed"), "starter_elite": (0.25, "common"),
             "jar": (0.01, "flawed"), "chest": (0.3, "fine"), "chest_deep": (0.5, "fine"), "chest_rich": (0.6, "fine")}


EQUIPMENT_CHANCE = {}


def rare(item, chance, count=(1, 1)):
    return {"item": item, "chance": chance, "count": list(count)}


def equipment(kind, chance=None):
    c, q = EQUIPMENT[kind]
    return {"chance": c if chance is None else chance, "min_quality": q}


# The foes of the valley's first rooms (the Reed Shallows, Willow Path West and East): their tables are marked `starter`
# (LootRules.make_starter; the first weapon and the pity in WorldAuthority._starter_drop). A species spec says it itself
# (`loot=dict(starter=True)`); the set below is the hand-written foes' (none now).
STARTER = set() | {i for i in MON.ids() if MON.loot(i).get("starter")}


# P7b (item_plan §3.4, §4.2): named rows, each rolled on every kill like a rare row (`elite_named`: only by an elite).
# Big Toad Tan's and the Drowned Abbot's are their boss signatures until P9 adds the pity (boss_design §4.1, §4.3).
NAMED_ROWS = {"big_toad_tan": {"named": [{"item": "mudwater_robe", "chance": 0.08}]},
              "drowned_abbot": {"named": [{"item": "drowned_hat", "chance": 0.08}, {"item": "drowned_boots", "chance": 0.08}]},
              "cloudpeak_roc": {"named": [{"item": "crane_trousers", "chance": 0.002}]}}

# Early surprises (docs/research/player_motivation.md item 7, §3.4): the first monsters carry rare rows, a river pearl
# (sold for coin) and a manual page. `find` marks a rare find: its drop plays the rare-find moment (MomentRules.is_rare).
_EARLY = [{"item": "pearl", "chance": 0.02, "count": [1, 1], "find": True}, {"item": "manual_page", "chance": 0.005, "count": [1, 1], "find": True}]
# A species spec names its own (`loot=dict(finds="early")` for these, or its rows: the Hollow Night's minnows' grey
# sliver, the first Hollow shard the story puts in your hand).
EARLY_FINDS = {i: (_EARLY if MON.loot(i)["finds"] == "early" else MON.loot(i)["finds"]) for i in MON.ids() if MON.loot(i).get("finds")}


def spec_row(id):
    """A species spec's enemies.json row (tools/content/monsters), made by mob(), atk() and d() as a hand row is."""
    return MON.row(id, mob, atk, d)


# P12 par times in seconds (research §6.2 and docs/boss_design.md §2.4).
BOSS_PAR_S = {"big_toad_tan": 90, "riverbed_serpent": 120, "drowned_abbot": 180, "the_reflection": 90, "hollow_behemoth": 150,
              "gate_guardian": 120, "thousand_eye_toad": 180, "tomb_king": 150, "pirate_captain": 150, "admiral_voss": 240,
              "general_kharn": 240, "nebula_leviathan": 300}


def build():
    # A spec_row is a species written once in the monster engine (tools/content/monsters/specs): its data, sheets and
    # voice in one place. It keeps its place among the hand rows, so the table does not move.
    M = [
        spec_row("mudshell_crab"),
        spec_row("reedtail_rat"),
        spec_row("old_snapper"),
        spec_row("hollow_minnow"),
        spec_row("hollowed_eel"),
        spec_row("trial_puppet"),
        spec_row("wild_boarlet"),
        spec_row("mossback_toad"),
        spec_row("rock_beetle"),
        spec_row("pebble_imp"),
        spec_row("stone_tortoise"),
        spec_row("ironclaw_mole"),
        spec_row("reed_frog"),
        spec_row("marsh_leech"),
        spec_row("greyfin"),
        spec_row("hollowed_boarlet"),
        spec_row("bamboo_monkey"),
        spec_row("green_viper"),
        spec_row("thornback_boar"),
        spec_row("mudwater_bandit"),
        spec_row("stone_guardian"),
        spec_row("bandit_archer"),
        spec_row("mud_hound"),
        spec_row("jade_carp"),
        spec_row("tide_crab"),
        spec_row("drowned_acolyte"),
        spec_row("paper_talisman_ghost"),
        spec_row("rapids_lizard"),
        spec_row("gorge_bandit_adept"),
        # S47 rogue cultivators: elites whose visible weapon or treasure is a guaranteed drop, with a sealed pouch.
        spec_row("rogue_cultivator"),
        spec_row("rogue_treasure_adept"),
        spec_row("boulder_serpent"),
        spec_row("mist_vulture"),
        spec_row("cloudwing_crane"),
        spec_row("stormwing_hawk"),
        spec_row("cliff_ape"),
        spec_row("mist_wolf"),
        spec_row("mirror_wisp"),
        spec_row("weeping_lantern"),
        spec_row("jade_sentinel"),
        spec_row("hollow_stag"),
        spec_row("cloudpeak_roc"),
        # Azure Expanse (Act II) · Thunderhorn Plains
        spec_row("spark_weasel"),
        spec_row("thunderhorn_rhino"),
        # P7b (item_plan §2.10, §5.3): the Stormgrass Stag grazes the Thunderhorn Plains on the Cloud Stag's side-view sheet
        # (M3: on the grid it has its own); a wood beast of rank 8, its core roll gives the peak wood core.
        spec_row("stormgrass_stag"),
        # Azure Expanse (Act II) · Rimefrost Heights and Mirrorwater Lake
        spec_row("frost_lynx"),
        spec_row("snow_ape"),
        spec_row("azure_carp_dragonet"),
        spec_row("river_sentinel"),
        # Azure Expanse (Act II) · Gale Canyons
        spec_row("wind_kite"),
        spec_row("canyon_harpy"),
        # Act II · Phase D: the Sunscar Desert and the Tomb of Sunscar.
        spec_row("sandstorm_scorpion"),
        spec_row("dune_worm"),
        spec_row("terracotta_warden"),
        spec_row("tomb_king"),
        spec_row("canyon_brigand"),
        # Act II · Phase E: the Skyport Wreck and the Starsea.
        spec_row("starsea_pirate"),
        spec_row("nine_peaks_disciple"),
        spec_row("pirate_captain"),
        # v1.2 · the Lantern Star Field (Act III, docs/act3_design.md) · Phase A: the Drifting Shoals.
        spec_row("star_jellyfish"),
        spec_row("comet_sparrow"),
        # v1.2 · Phase B: Blackmast Haven and the Wyrmnest Isles.
        spec_row("pirate_gunner"),
        spec_row("nest_guardian"),
        spec_row("hollowed_wyrmling"),
        spec_row("admiral_voss"),
        # v1.2 · Phase C: the Orbit Ruins.
        spec_row("gravity_golem"),
        spec_row("orbit_moth"),
        # v1.2 · Phase D: the Ashen Reach (the Ashborn legions) and the Tidebreak Front (the Hollow's drones).
        spec_row("ashborn_raider"),
        spec_row("ashborn_pyre_keeper"),
        spec_row("hollow_drone"),
        # General Kharn: an enemy, not a villain. At a fifth of his health he kneels: spare him (the Ashborn remember it) or
        # finish him.
        spec_row("general_kharn"),
        # v1.2 · Phase E: the Nebula Deep. Eels swim the nebula (flyers); Void Crabs blink through their shells.
        spec_row("nebula_eel"),
        spec_row("void_crab"),
        # The Nebula Leviathan (field boss, 99): it swallows the current, breathes the void, and holds a Sphere of Space.
        spec_row("nebula_leviathan"),
        # The Presence Court's aspirant duel (chapter 20): Shen Lian, a Star Warden aspirant with a Sword Domain.
        mob("shen_lian_aspirant", 91, "trial", "metal", None, [], [atk("starfall_thrust", 0.45, 120, 1.25, depth=36),
                                                                    atk("domain_cut", 0.8, 200, 1.1, depth=70, both_sides=True)],
            ai="duelist", art=human("shen_lian"), race="human", energy="sage_qi", width=18, height=90, spar=True, name="Shen Lian",
            presence=3, sphere={"element": "sword", "tier": 3}),
        spec_row("presence_phantom"),
        spec_row("ninth_presence"),
        spec_row("alliance_champion"),
        spec_row("ironroot_warden"),
        # Bosses
        spec_row("big_toad_tan"),
        spec_row("riverbed_serpent"),
        spec_row("thousand_eye_toad"),
        spec_row("drowned_abbot"),
        spec_row("the_reflection"),
        # Gap report G1: every 25 on the heart-demon meter brings one of these into the Trial of Reflections.
        mob("heart_demon", 36, "normal", "none", None, [], [atk("whisper_of_doubt", 0.5, 70, 0.8, damage_type="soul")],
            ai="duelist", art={"avatar": "player", "tint": "#b0283c"}, race="human", energy="primal_qi", width=18, height=90,
            name="Heart Demon", hp_mult=0.5),
        spec_row("elder_gu"),
        spec_row("hollow_behemoth"),
        spec_row("gate_guardian"),
        # Shen Lian's spar (Fish-Gutting Fists) is a lesson: he spars at the player's own Level (`spar_level` "match", as
        # the sparring disciples do), his fist winds up as long as Old Snapper's claw (a tell a thumb can read), and he
        # says what the spar teaches as it starts and as it ends (`spar_lines`, the HUD). A Level-4 double beat the
        # prototype's Level-2 QA player.
        mob("shen_lian", 4, "trial", "none", None, [], [atk("fish_gutting_fist", 0.6, 46, 1.0)], ai="duelist", art=human("shen_lian"),
            race="human", width=18, height=90, spar=True, spar_level="match",
            spar_lines={"start": "Watch my shoulder. When it drops, step aside, then hit back!",
                        "lost": "Again! Step aside when my shoulder drops, then hit back.",
                        "won": "You read my shoulder. Fine, you won. This time."}),
        mob("wen_zhao", 44, "trial", "wind", None, [], [atk("cloud_cut", 0.4, 80, 1.1), atk("crescent", 0.6, 300, 1.2, damage_type="qi",
                                                                                                  projectile={"speed": 540, "art": "qi_arc"})],
            ai="duelist", art=human("wen_zhao"), race="human", width=18, height=90, spar=True),
        mob("sparring_disciple", 10, "trial", "none", None, [], [atk("palm", 0.45, 46, 1.0)], ai="duelist", art=human("trial_disciple"), spar_level="match",
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
        spec_row("fruit_guardian"),
        # S49 grudges. The Mudwater lieutenant yields at a fifth of his health: spare him (he remembers) or not (his
        # brother hunts you on the Caravan Road).
        spec_row("mudwater_lieutenant"),
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
        M.append(spec_row(pid) if pid in MON.load() else
                 mob(pid, (19, 24), "normal", el, None, [], [atk("nip", 0.4, 36, 0.8)], ai="wild_pet", tameable=True, width=18, height=28,
                     passive=True))
    # S46: the Riverstone Ox grazes Quarry Rim from Cloud Stride 1; a mount-only spirit beast, tamed like the others.
    M.append(spec_row("riverstone_ox"))
    # The species specs not placed above (a new species needs no row here): after the hand rows, in the specs' order.
    M += MON.rows({m["id"] for m in M}, mob, atk, d)
    beast_ranks(M)
    # P12 (research §6.2): a boss's health is the par character's DPS at its Level times its par time, in place of the
    # role's factor and the old hp_mult (StatRules.mob_stats). Elder Gu cannot be hurt and flees on his clock.
    for row in M:
        if row["id"] in BOSS_PAR_S:
            row["par_s"] = BOSS_PAR_S[row["id"]]
            row.pop("hp_mult", None)
    entries("enemies.json", M)

    tables = []
    # Key items drop only while a quest still needs them (S32 quest drops).
    QUEST_DROPS = {"mudwater_bandit": [{"item": "mudwater_key", "chance": 0.3, "count": [1, 1], "quest": "the_caravan_road"}],
                   "dune_worm": [{"item": "sun_seal_shard", "chance": 0.5, "count": [1, 1], "quest": "the_sealed_gate"}],
                   "tomb_king": [{"item": "sunscar_seal", "chance": 1.0, "count": [1, 1], "quest": "the_tomb_king"}],
                   "starsea_pirate": [{"item": "ledger_page", "chance": 0.35, "count": [1, 1], "quest": "the_skyport_wreck"}]}
    # A species spec names its own (`loot=dict(quest=[...])`: Guo's three shells, Mei Qing's three grey hides).
    for sid in MON.ids():
        if MON.loot(sid).get("quest"):
            QUEST_DROPS.setdefault(sid, []).extend(dict(x) for x in MON.loot(sid)["quest"])
    # S47 legendary chains: each piece drops from its foe while that chain's quest still wants it.
    for ch in LEGENDS:
        for pid, pname, src, chance, zone in ch["pieces"]:
            QUEST_DROPS.setdefault(src, []).append({"item": pid, "chance": chance, "count": [1, 1], "quest": "legend_" + ch["id"]})
    for m in M:
        role = m["role"]
        drops = m.get("drops", [])
        table = {"id": m["loot"], "groups": [], "coins": {}, "equipment": {}, "rare": []}
        if role == "normal":
            # A group rolls once and picks one row by weight, so a picked row keeps no chance of its own (P7a).
            table["groups"] = [{"chance": 0.6, "pick": [dict({k: v for k, v in x.items() if k != "chance"}, weight=x.get("weight", 1)) for x in drops if x["chance"] > 0.2]}]
            table["rare"] = [x for x in drops if x["chance"] <= 0.2 and x["chance"] > 0]
            table["coins"] = {"chance": 0.2 * m.get("coin_mult", 1.0), "mult": 1}
            table["equipment"] = equipment("starter" if m["id"] in STARTER else "normal", EQUIPMENT_CHANCE.get(m["id"]))
        elif role == "elite":
            table["guaranteed"] = [dict(x) for x in drops]
            table["coins"] = {"chance": 1.0, "mult": 6}
            table["equipment"] = equipment("starter_elite" if m["id"] in STARTER else "elite")
            table["rare"] = [{"item": "manual_page", "chance": 0.05, "count": [1, 1]}]
        elif role in ("dungeon_boss", "field_boss", "story_boss"):
            table["guaranteed"] = [dict(x) for x in drops]
            table["coins"] = {"chance": 1.0, "mult": 40}
            table["equipment"] = equipment("boss")
        elif role == "event":
            table["guaranteed"] = [dict(x) for x in drops if x["chance"] >= 1.0]
            table["equipment"] = equipment("event")
        else:
            table["guaranteed"] = [dict(x) for x in drops if x["chance"] >= 1.0]
            # P1: every loot table rolls equipment or says why not. A spar or trial opponent is not looted.
            table["no_equipment"] = "spar"
        if m["id"] in STARTER:
            table["starter"] = True
        if m["id"] in QUEST_DROPS:
            table["quest_drops"] = QUEST_DROPS[m["id"]]
        table.update(NAMED_ROWS.get(m["id"], {}))
        table["rare"] = table["rare"] + [dict(x) for x in EARLY_FINDS.get(m["id"], [])]
        # P13a Lost Arts (technique_plan §5.3): a lost manual is never in the random roll; LootRules rolls it like a named
        # row (drop rate does not raise it) and ProgressionAuthority keeps it only while its art is not yet found, sure by
        # the pity-th kill.
        # Another foe that carries the same manual (Lieutenant Kuai and the Mudwater Manual) keeps its rate, without pity.
        lost = [{"item": s["src"]["item"], "art": s["id"], "chance": s["src"]["chance"], "pity": s["src"].get("pity", 0)}
                for s in LOST_HAND.LOST if s["src"]["kind"] == "drop" and s["src"]["enemy"] == m["id"] and s["src"]["chance"] < 1.0]
        lost += [{"item": x["item"], "art": LOST_MANUALS[x["item"]], "chance": x["chance"], "pity": 0} for x in table.get("rare", []) + table.get("guaranteed", [])
                 if x["item"] in LOST_MANUALS and x.get("chance", 1.0) < 1.0 and x["item"] not in {r["item"] for r in lost}]
        if lost:
            table["lost"] = lost
            moved = {r["item"] for r in lost}
            table["rare"] = [x for x in table["rare"] if x["item"] not in moved]
            table["guaranteed"] = [x for x in table.get("guaranteed", []) if x["item"] not in moved or x.get("chance", 1.0) >= 1.0]
        tables.append(table)
    tables.append({"id": "jar_valley_low", "groups": [{"chance": 0.5, "pick": [{"item": "rice", "weight": 2, "count": [1, 1]},
                   {"item": "willow_moss", "weight": 2, "count": [1, 2]}, {"item": "herbal_tea", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.5, "mult": 1}, "rare": [], "equipment": equipment("jar")})
    tables.append({"id": "jar_valley_mid", "groups": [{"chance": 0.6, "pick": [{"item": "rice_ball", "weight": 2, "count": [1, 1]},
                   {"item": "spirit_stone_shard", "weight": 1, "count": [1, 1]}, {"item": "healing_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.6, "mult": 2}, "rare": [], "equipment": equipment("jar")})
    tables.append({"id": "chest_valley", "guaranteed": [{"item": "spirit_stone_shard", "count": [1, 3], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "healing_pill", "weight": 2, "count": [1, 2]}, {"item": "manual_page", "weight": 1, "count": [1, 1]},
                                                         {"item": "qi_gathering_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 5}, "rare": [], "equipment": equipment("chest")})
    # Gu's Warehouse vault (S47): the Little Pagoda he hoarded, and his silver.
    tables.append({"id": "gus_vault", "guaranteed": [{"item": "little_pagoda", "count": [1, 1], "chance": 1.0}],
                   "groups": [], "coins": {"chance": 1.0, "mult": 12}, "rare": [], "equipment": {}, "no_equipment": "set_reward"})
    # The Drowned Abbot's sealed vault (SA3, S44): the Nine-Dragon Cauldron he kept, and a dungeon chest's worth besides.
    tables.append({"id": "abbots_vault", "guaranteed": [{"item": "nine_dragon_cauldron", "count": [1, 1], "chance": 1.0},
                                                        {"item": "spirit_soil", "count": [1, 1], "chance": 1.0},
                                                        {"item": "spirit_stone_shard", "count": [2, 4], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [1, 2]}, {"item": "foundation_guard_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [], "equipment": {}, "no_equipment": "set_reward"})
    # S46: the chest on the ledge beside Crane Falls keeps the Herb Whisper skill book.
    tables.append({"id": "falls_pool_chest", "guaranteed": [{"item": "pet_book_herb_whisper", "count": [1, 1], "chance": 1.0},
                                                             {"item": "mist_lotus", "count": [1, 2], "chance": 1.0}],
                   "groups": [], "coins": {"chance": 1.0, "mult": 6}, "rare": [], "equipment": {}, "no_equipment": "set_reward"})
    tables.append({"id": "chest_dungeon", "guaranteed": [{"item": "spirit_stone_shard", "count": [2, 4], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [1, 2]}, {"item": "foundation_guard_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [], "equipment": equipment("chest_deep")})
    # Act II (S32): jars and chests of the Azure Expanse. Coins here are paid in Spirit Stones (zone coin_scale).
    tables.append({"id": "jar_expanse", "groups": [{"chance": 0.6, "pick": [{"item": "storm_shard", "weight": 2, "count": [1, 2]},
                   {"item": "spirit_stone_shard", "weight": 2, "count": [1, 2]}, {"item": "qi_restoration_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.6, "mult": 2}, "rare": [], "equipment": equipment("jar")})
    tables.append({"id": "chest_expanse", "guaranteed": [{"item": "storm_shard", "count": [3, 6], "chance": 1.0},
                                                         {"item": "spirit_stone_shard", "count": [2, 4], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [1, 2]}, {"item": "stormsteel_ore", "weight": 2, "count": [1, 2]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [rare("hour_incense_72", 0.03), rare("wandering_incense", 0.02)], "equipment": equipment("chest_deep")})
    tables.append({"id": "chest_tomb", "guaranteed": [{"item": "storm_shard", "count": [6, 10], "chance": 1.0},
                                                      {"item": "sunglass_ore", "count": [2, 3], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [2, 3]},
                                                       {"item": "sovereign_settling_pill", "weight": 1, "count": [1, 1]},
                                                       {"item": "ember_cactus", "weight": 1, "count": [1, 2]}]}],
                   "coins": {"chance": 1.0, "mult": 16}, "rare": [rare("spirit_stone_high", 0.05)], "equipment": equipment("chest_rich")})
    # The pirates' strongbox on the Pirate Deck (chapter 15) and the Starsea Launch's cache.
    tables.append({"id": "chest_wreck", "guaranteed": [{"item": "storm_shard", "count": [6, 10], "chance": 1.0},
                                                       {"item": "comet_iron", "count": [2, 3], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [2, 3]},
                                                       {"item": "will_tempering_pill", "weight": 1, "count": [1, 2]},
                                                       {"item": "sky_ink", "weight": 1, "count": [2, 3]}]}],
                   "coins": {"chance": 1.0, "mult": 16}, "rare": [rare("spirit_stone_high", 0.05)], "equipment": equipment("chest_rich")})
    # v1.2 (S32): jars and chests of the Lantern Star Field. Coins are paid in Sage Crystals (zone coin_scale).
    tables.append({"id": "jar_lantern", "groups": [{"chance": 0.6, "pick": [{"item": "star_shard", "weight": 2, "count": [1, 2]},
                   {"item": "spirit_stone_shard", "weight": 1, "count": [2, 3]}, {"item": "qi_restoration_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.6, "mult": 2}, "rare": [], "equipment": equipment("jar")})
    tables.append({"id": "chest_lantern", "guaranteed": [{"item": "star_shard", "count": [4, 8], "chance": 1.0},
                                                         {"item": "spirit_stone_shard", "count": [3, 5], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [2, 3]}, {"item": "driftglass", "weight": 2, "count": [1, 2]},
                                                       {"item": "will_tempering_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [rare("wandering_incense", 0.03)], "equipment": equipment("chest_deep")})
    entries("loot_tables.json", tables)
    return M


if __name__ == "__main__":
    raise SystemExit(run_cli(build))
