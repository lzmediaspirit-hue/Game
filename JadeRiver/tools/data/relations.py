"""S49 karma, bonds and the living world: karma.json.

A deed is what the world remembers: merit and sin (the karma ledger), a push along the righteous-demonic
alignment, and personal Fame. Deeds fire three ways:
- from an effect, {"kind": "deed", "deed": id} (quest rewards, dialogue choices);
- from code, RelationsAuthority.apply_deed (a patient healed);
- from an event, when "event" is set and every "match" key equals the payload's value.
Flags: once (only the first time), once_key (once per value of that payload key, e.g. each boss once),
per_count (times the payload's count), in_town (only in a town room, where people watch).
"""
from common import entries


def deed(id, name, merit=0, sin=0, alignment=0, fame=0, **kw):
    d = {"id": id, "name": name, "merit": merit, "sin": sin, "alignment": alignment, "fame": fame}
    d.update(kw)
    return d


def on(event, **match):
    return {"event": event, "match": match}


# Quests that ease another's lot (gap report G1, v2 Part 8): merit on completion. Part 8 sets cleansing a Hollowed
# village or well at +30.
QUEST_DEEDS = {
    "grannys_remedy": ("Eased Granny Liu's cough", 5, 2),
    "the_rite": ("Kept the Rite for the drowned", 10, 3),
    "the_infirmary": ("Tended the infirmary", 10, 3),
    "what_remains": ("Laid the dead to rest", 10, 3),
    "passing_it_on": ("Passed a kindness on", 10, 3),
    "guos_old_wound": ("Mended Uncle Guo's old wound", 10, 3),
    "cleansing_the_well": ("Cleansed the Hollowed well", 30, 5),
    "grey_roofs": ("Cleansed the Grey Pools village", 30, 5),
    "dous_kite_returns": ("Brought Little Dou's kite home", 5, 2),
    "a_second_try": ("Gave a failed disciple a second try", 5, 2),
}
QUEST_FAME = {"cleansing_the_well": 15, "grey_roofs": 15}


def deeds():
    rows = []
    for qid, (name, merit, al) in QUEST_DEEDS.items():
        rows.append(deed(qid, name, merit=merit, alignment=al, fame=QUEST_FAME.get(qid, 0), once=True))
    rows += [
        # Dialogue choices (story.py): the Hollow Night rescues, the tomb, Elder Gu's fate, his ledger.
        deed("rescue_dou", "Carried Little Dou through the Hollow Night", merit=10, alignment=3, once=True),
        deed("rescue_granny", "Carried Granny Liu through the Hollow Night", merit=10, alignment=3, once=True),
        deed("rescue_ma", "Carried Old Ma through the Hollow Night", merit=10, alignment=3, once=True),
        deed("tomb_resealed", "Resealed the tomb", merit=20, alignment=5, fame=10, once=True),
        deed("gu_freed", "Freed Elder Gu", merit=15, alignment=5, once=True),
        deed("gu_left", "Left Elder Gu to the sands", sin=10, alignment=-5, once=True),
        deed("ledger_burned", "Burned the smugglers' ledger", merit=20, alignment=5, once=True),
        deed("ledger_returned", "Sold the ledger back to its owners", sin=10, alignment=-10, once=True),
        # Code: each patient treated with the Healing craft (Part 8: +2 merit).
        deed("heal_patient", "Healed a patient", merit=2),
        # Events.
        deed("black_market", "Bought in a back room", sin=2, alignment=-1, per_count=True, **on("item_bought", shop="free_market")),
        deed("beast_tide_held", "Held the gate against the Beast Tide", merit=10, alignment=2, fame=10, **on("beast_tide_result", won=True)),
        deed("tournament_qualifier", "Qualified for the Valley Tournament", fame=20, once=True, **on("quest_completed", quest="the_valley_tournament")),
        deed("tournament_bracket", "Reached the tournament's last eight", fame=60, once=True, **on("quest_completed", quest="the_bracket")),
        deed("tournament_finals", "Fought in the tournament finals", fame=150, once=True, **on("quest_completed", quest="the_valley_finals")),
        deed("field_boss_felled", "Felled a field lord", fame=10, once_key="def", **on("actor_defeated", victim_kind="enemy", role="field_boss")),
        deed("story_boss_felled", "Defeated a great foe", fame=15, once_key="def", **on("actor_defeated", victim_kind="enemy", role="story_boss")),
        deed("dungeon_boss_felled", "Cleared a lair", fame=5, once_key="def", **on("actor_defeated", victim_kind="enemy", role="dungeon_boss")),
        deed("arena_win", "Won in the Beast Arena", fame=2, **on("arena_battle", won=True)),
        # Personal Fame lives on what people see: a spar in a town square is public.
        deed("public_spar_won", "Won a spar in public", fame=3, in_town=True, **on("spar_ended", winner="player")),
        deed("public_spar_lost", "Lost a spar in public", fame=-5, in_town=True, **on("spar_ended", winner="opponent")),
        deed("young_master_humbled", "Humbled a young master", fame=15, **on("spar_ended", opponent="young_master", winner="player")),
        deed("young_master_lost", "Lost to a young master", fame=-10, **on("spar_ended", opponent="young_master", winner="opponent")),
        deed("challenge_declined", "Declined a young master's challenge", fame=-5),
        # Part 8: mercy and its opposite, when a named foe throws down their weapon.
        deed("spared_foe", "Spared a foe who yielded", merit=10, alignment=3),
        deed("killed_yielded", "Killed a foe who had yielded", sin=15, alignment=-8),
        deed("bounty_claimed", "Claimed a bounty", fame=10, alignment=1),
        # Part 8: the night peddler on the Caravan Road (+5 sin a purchase).
        deed("night_peddler", "Bought from the night peddler", sin=5, alignment=-1, per_count=True, **on("item_bought", shop="night_peddler")),
    ]
    return rows


# NPC affinity (S49, Part 8): 0-5 hearts. One gift per NPC a day; what they love is worth a heart, what they like
# a little less, anything else a courtesy. Hearts pay out once each (a recipe taught, a keepsake), open the NPC's
# shop discount (3 and 5 hearts), a companion's friendly duel (3), sworn siblings (4) and a Dao Companion (5).
def learn(recipe):
    return {"kind": "learn_recipe", "recipe": recipe}


def give(item, n=1):
    return {"kind": "grant_item", "item": item, "count": n}


AFFINITY = {
    # Part 8's favourite gifts.
    "aunt_ping": {"loved": ["riverfish_soup"], "liked": ["herbal_tea", "jade_carp_fish", "jade_carp_congee"],
                  "rewards": {"3": [learn("riverfish_soup")], "5": [learn("jade_carp_congee")]}},
    "granny_liu": {"loved": ["mist_lotus"], "liked": ["herbal_tea", "lotus_root_tea", "clear_mind_pill"],
                   "rewards": {"3": [learn("healing_pill")], "5": [give("calm_heart_incense", 2)]}},
    "old_ma": {"loved": ["pearl"], "liked": ["dusty_curio", "old_net", "river_minnow"], "rewards": {"5": [give("spirit_jade", 3)]}},
    "mei_qing": {"loved": ["cloudtop_orchid"], "liked": ["mist_lotus", "cloudtop_orchid_broth", "spirit_jade"],
                 "rewards": {"5": [learn("cloudtop_orchid_broth")]}},
    "lan_yue": {"loved": ["lotus_root_tea"], "liked": ["herbal_tea", "mist_lotus", "jade_carp_congee"], "rewards": {"3": [learn("lotus_root_tea")]}},
    "tie_niu": {"loved": ["boar_bone_broth"], "liked": ["roast_fish", "ember_pepper_stew", "thunderhorn_stew"], "rewards": {"3": [learn("boar_bone_broth")]}},
    "qiu_feng": {"loved": ["vulture_plume"], "liked": ["storm_feather", "roast_fish", "toad_oil_dumplings"], "rewards": {"3": [learn("roast_fish")]}},
    "bai_ling": {"loved": ["formation_stone"], "liked": ["spirit_paper", "spirit_jade", "lantern_wick"], "rewards": {"3": [give("formation_stone", 2)]}},
    # The build's other named NPCs.
    "little_dou": {"loved": ["dusty_curio"], "liked": ["rice_ball", "reed_perch", "roast_fish"], "rewards": {"3": [give("rice_ball", 5)]}},
    "lu_boatman": {"loved": ["rice_wine"], "liked": ["roast_fish", "river_minnow", "herbal_tea"], "rewards": {"3": [give("jade_carp_fish", 3)]}},
    "uncle_guo": {"loved": ["ember_pepper_stew"], "liked": ["rice_wine", "boar_bone_broth", "roast_fish"], "rewards": {"3": [learn("ember_pepper_stew")]}},
    "shen_lian": {"loved": ["roast_fish"], "liked": ["river_minnow", "rice_ball", "reed_perch"], "rewards": {"3": [give("clear_mind_pill", 2)]}},
    "elder_hu": {"loved": ["spirit_jade"], "liked": ["herbal_tea", "manual_page", "mist_lotus"], "rewards": {"3": [give("manual_page", 3)]}},
    "elder_sung": {"loved": ["storm_feather"], "liked": ["herbal_tea", "manual_page", "cloudtop_orchid"], "rewards": {"3": [give("manual_page", 3)]}},
}
# One person, two NPC rows (a stall and the sect; a fisher kid and a rival): affinity is kept under one id.
AFFINITY_ALIAS = {"mei_qing_sect": "mei_qing", "shen_lian_npc": "shen_lian"}
# The mentors' legacy arts (Inner Arts), passed on in "The Elder's Last Lesson".
LEGACY = {"elder_hu": "lotus_mind_legacy", "elder_sung": "drifting_cloud_legacy"}


def bonds():
    rows = [
        {"id": "dao_companion", "name": "Dao Companion", "hearts": 5, "max": 1, "from": "companions",
         # Beside you (in the party): one risk step off every major breakthrough, +10% insight, and resonance
         # meditation (+25% while you both sit).
         "support_steps": 1, "insight": 0.10, "resonance": 0.25},
        {"id": "sworn", "name": "Sworn Siblings", "hearts": 4, "max": 3, "from": "companions", "title": "sworn_sibling",
         # Each sworn sibling in the party.
         "per_sibling": [{"stat": "physical_attack", "op": "pct_add", "value": 0.03}, {"stat": "qi_attack", "op": "pct_add", "value": 0.03},
                         {"stat": "physical_defense", "op": "pct_add", "value": 0.03}]},
        {"id": "master", "name": "Master", "from": "mentors", "formed_by": "the_mentors_gift", "inheritance": "the_elders_last_lesson",
         "mentors": {"jade_sect": "elder_hu", "cloud_sect": "elder_sung"}, "legacy": LEGACY},
    ]
    entries("bonds", rows,
            affinity={"per_heart": 100, "max_hearts": 5, "loved": 100, "liked": 40, "other": 15, "quest": 30, "duel": 20,
                      "discount": [[3, 0.05], [5, 0.10]], "duel_hearts": 3})
    return rows


# Grudges (S49 v1.0, Part 8): each faction keeps a grudge against you. Killing its named people raises it; past the
# threshold its hunters come for you in the field. Blood money, a duel or a quest settles it. A town board posts
# bounties on named targets (which are themselves named kills).
FACTIONS = [
    {"id": "mudwater", "name": "Mudwater Bandits", "threshold": 30, "per_named": 15, "hunter": "mudwater_cutthroat",
     "hunt_rooms": ["cr_caravan_road", "wp_west", "wp_east", "rm_marsh_edge"],
     "blood_money": {"currency": "silver_tael", "amount": 200}, "duel": "tan_the_younger"},
    {"id": "gorge", "name": "Gorge Bandits", "threshold": 30, "per_named": 15, "hunter": "gorge_stalker",
     "hunt_rooms": ["wg_gorge_mouth", "wg_echo_cliffs", "wg_rapids_terraces"],
     "blood_money": {"currency": "silver_tael", "amount": 400}, "quest": "old_scores"},
    # Elder Gu's ring: story-bound. The cargo you turn up raises it; breaking the warehouse ends it for good.
    {"id": "smugglers", "name": "Stoneford Smugglers", "threshold": 50, "per_named": 15, "hunter": "gu_enforcer",
     "hunt_rooms": ["dw_bend_shore", "cr_caravan_road", "lf_reed_shallows"],
     "story": {"raise": {"gus_cargo": 20, "hidden_cargo": 20}, "clear": "gus_warehouse"}},
]
BOUNTIES = [
    {"id": "one_eye_pang", "target": "one_eye_pang", "room": "cr_caravan_road", "faction": "mudwater",
     "reward": {"currency": "silver_tael", "amount": 150}, "realm": "qi_kindling_7",
     "text": "One-Eye Pang robs the carts on the Caravan Road. Stoneford pays for his head."},
    {"id": "ferryman_lou", "target": "ferryman_lou", "room": "dw_bend_shore", "faction": "smugglers",
     "reward": {"currency": "silver_tael", "amount": 260}, "realm": "qi_unfurling_1",
     "text": "Ferryman Lou runs Gu's goods past the Bend at dusk. The magistrate wants him stopped."},
    {"id": "knife_hand_sui", "target": "knife_hand_sui", "room": "wg_echo_cliffs", "faction": "gorge",
     "reward": {"currency": "silver_tael", "amount": 420}, "realm": "qi_unfurling_6",
     "text": "Knife-Hand Sui leads the Gorge Bandits' raids from the Echo Cliffs. Bring him down."},
]
# Hunters wait for you at most this often, and not every time.
HUNT = {"chance": 0.35, "cooldown_s": 1800}


def factions():
    entries("factions", FACTIONS, bounties=BOUNTIES, hunt=HUNT, max_bounties=2)


def build():
    bonds()
    factions()
    entries("karma", deeds(),
            # 100 merit eases one major breakthrough by a risk step, once in each great realm.
            merit_step=100,
            # Personal Fame tiers (v2 S49): Unknown, Noted, Rising, Renowned, Legendary.
            fame_tiers=[{"id": "unknown", "name": "Unknown", "min": 0},
                        {"id": "noted", "name": "Noted", "min": 50},
                        {"id": "rising", "name": "Rising", "min": 150},
                        {"id": "renowned", "name": "Renowned", "min": 400},
                        {"id": "legendary", "name": "Legendary", "min": 1000}],
            # The righteous-demonic axis in words, by the highest value each covers.
            alignment_words=[{"id": "demonic", "name": "Demonic", "max": -60},
                             {"id": "shadowed", "name": "Shadowed", "max": -20},
                             {"id": "balanced", "name": "Balanced", "max": 19},
                             {"id": "upright", "name": "Upright", "max": 59},
                             {"id": "righteous", "name": "Righteous", "max": 100}],
            # From Rising Fame a young master may be waiting when you walk into a town (once a day): accept and
            # spar at your level, or decline and lose a little face.
            young_master={"fame": 150, "chance": 0.25, "enemy": "young_master", "decline_deed": "challenge_declined"},
            # Part 8 named debts: when each falls due and what comes of it (a letter, a flag, a hunter).
            debts={"dou_rescue": {"due_quest": "the_heart_trial", "mail": "dou_repays", "attachments": [{"item": "cloudtop_orchid", "count": 1}]},
                   "lieutenant_spared": {"due_quest": "hidden_cargo", "mail": "lieutenant_warning", "flag": "warned_of_ambush",
                                         "attachments": [{"item": "thunderclap_pellet", "count": 3}]},
                   "lieutenant_killed": {"due_h": 0.25, "mail": "kuai_threat", "hunter": {"enemy": "kuai_shan", "room": "cr_caravan_road"}}})


if __name__ == "__main__":
    build()
