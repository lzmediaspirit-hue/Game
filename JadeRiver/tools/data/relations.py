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
    ]
    return rows


def build():
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
            young_master={"fame": 150, "chance": 0.25, "enemy": "young_master", "decline_deed": "challenge_declined"})


if __name__ == "__main__":
    build()
