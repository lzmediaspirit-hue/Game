"""S49 the living world: calendar.json (world events on the account calendar, weather tables, heavenly phenomena),
fortune_deck.json (rare vignettes, paced by each character's Fortune meter), rankings.json (the Heaven Ranking),
tower.json (the Trial Tower) and activity.json (daily activity chests).

Every event repeats on a fixed rhythm from the account's creation day (every N days from an offset, or once a week on
a UTC weekday) and lasts some hours. A seeded draw from the account seed picks the room and the hour, so two devices
with the same save see the same calendar (CalendarRules). Story entries, first visits and quest-bound vaults are
never behind the cycle; only repeat runs are, and only up to a realm cap.
"""
import glob
import json
import os

from common import DATA, entries


def rift_rooms():
    """The valley's field rooms with beasts: a spatial rift can tear open in any of them (world.py places the tear)."""
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "rooms", "*.json"))):
        d = json.load(open(f))
        if d.get("zone") == "jade_river_valley" and d.get("type") == "field" and d.get("spawns"):
            out.append(d["id"])
    return out


def events():
    return [
        # The weekly Beast Tide (V7d) keeps its own weekly reset; the calendar shows it.
        {"id": "beast_tide", "name": "Beast Tide", "weekly_reset": True, "room": "sf_gate",
         "desc": "Once a week the beasts come down on Stoneford Gate. Ring the gong to meet them."},
        # Part 8: every 3 days for an hour, in a random field room; its beasts three levels stronger.
        {"id": "spatial_rift", "name": "Spatial Rift", "every_days": 3, "offset_days": 1, "duration_h": 1,
         "hours": [9, 11, 13, 15, 17, 19, 20], "rooms": rift_rooms(), "level_bonus": 3, "loot": "chest_dungeon",
         "desc": "A tear opens in a field room for an hour. Touch it and the land's beasts pour out three levels stronger; beat them for what the rift leaves behind."},
        # Part 8 reopenings: repeat runs only, up to a realm cap; the story entry, the vault and the first visit stay open.
        {"id": "shrine_reopening", "name": "The Drowned Shrine Surfaces", "every_days": 5, "offset_days": 0, "duration_h": 24,
         "room": "ds_abbots_sanctum", "boss": "drowned_abbot", "cap_below": "heart_tempering_1",
         "desc": "Every fifth day the shrine rises for a day and the Abbot wakes again. Repeat runs at Qi Unfurling 9 and below."},
        # Part 8: the valley's auction day, every Saturday on Market Street (Spirit Stones; seeds, recipes, eggs).
        {"id": "auction_day", "name": "Auction Day", "weekday": 5, "duration_h": 24, "room": "sf_market",
         "desc": "Every Saturday an auctioneer sets up on Market Street: rare seeds, recipe scrolls and spirit eggs, for Spirit Stones."},
        # Part 8: a treasure birth every four days: a Spirit Fruit ripens in a field room, rival cultivators come for
        # it, and a guardian beast wakes. Clear them and the fruit is yours.
        {"id": "treasure_birth", "name": "A Spirit Fruit Ripens", "every_days": 4, "offset_days": 3, "duration_h": 6,
         "hours": [8, 10, 12, 14, 16], "rooms": [r for r in rift_rooms() if r not in ("lf_reed_shallows", "wp_west")],
         "rivals": "rogue_cultivator", "guardian": "fruit_guardian", "level_bonus": 2, "item": "spirit_fruit",
         "desc": "Every fourth day a Spirit Fruit ripens somewhere in the valley. Rival cultivators come for it, and its guardian wakes."},
        # Part 8: the weekly gathering trial on the Jade Herb Terraces; the ranking pays Foundation-pill recipes.
        {"id": "gathering_trial", "name": "The Herb Terraces Trial", "weekday": 2, "duration_h": 24, "room": "ja_herb_terraces",
         "rivals": ["Herb-girl Yan", "Apprentice Tao", "Old Scribe Bai", "Sister Wen of the Cloud Sect", "Farmer Gu"],
         "rival_score": [6, 22], "rewards": {"1": {"learn": "foundation_guard_pill", "item": "foundation_guard_pill", "count": 3},
                                              "2": {"learn": "foundation_guard_pill", "item": "foundation_guard_pill", "count": 1},
                                              "3": {"learn": "foundation_guard_pill"}, "rest": {"item": "mist_lotus", "count": 2}},
         "desc": "Every Wednesday the Jade Sect weighs what each gatherer brings in from the Terraces. The top three learn the Foundation Guard Pill."},
        {"id": "waterfall_reopening", "name": "The Waterfall Cave Opens", "every_days": 5, "offset_days": 2, "duration_h": 24,
         "room": "wg_waterfall_cave", "cap_below": "cloud_stride_1",
         "desc": "Every fifth day the falls thin and the cave's inner cache can be reached again. Repeat visits at Heart Tempering 9 and below."},
    ]


def fortune_deck():
    """Part 8's eight vignettes. Each lists the moments it can come on (entering a room, gathering, a void-fall
    recovery), a weight that Fortune raises, and extra weight from merit or sin. A card marked once comes once per
    character. Effects are ordinary effects, plus the fortune-only ones: fortune_grotto (the fall ends in a hidden
    cave), grain_blessing (the next alchemy batch) and insight_best (insight into your deepest Dao)."""
    def card(id, name, text, triggers, weight, effects, **kw):
        c = {"id": id, "name": name, "text": text, "triggers": triggers, "weight": weight, "effects": effects}
        c.update(kw)
        return c
    return [
        card("hidden_cave", "A Hidden Cave", "You do not land where you fell. A draught of cold air, moss underfoot: a cave no map shows, and "
             "an old chest under a fall of roots.", ["fell_out"], 6, [{"kind": "fortune_grotto"}]),
        card("remnant_ring", "A Remnant Soul in a Ring", "A cracked bronze ring in the grass. A thin old voice speaks from it: "
             "\"Carry me a while.\" It recites a page of its art before it fades.", ["room_entered", "node_gathered"], 4,
             [{"kind": "grant_item", "item": "manual_page", "count": 3}]),
        card("hermit_chess", "The Hermit's Chess Problem", "An old man at a stone board does not look up. \"White lives in three.\" "
             "You stand there until you see it, and something else comes clear with it.", ["room_entered"], 4,
             [{"kind": "insight_best", "amount": 40}], requires={"all": [{"kind": "room_type", "value": "field"}]}),
        card("wounded_crane", "A Wounded Crane", "A Jade Crane beats one wing in the reeds, an arrow through the other. Your own crane "
             "keeps watch while you draw the shaft and bind the wing.", ["room_entered", "node_gathered"], 3,
             [{"kind": "add_bond_species", "species": "jade_crane", "amount": 2}, {"kind": "deed", "deed": "crane_mended"}],
             requires={"all": [{"kind": "pet_owned", "species": "jade_crane"}]}),
        card("buried_wine", "A Jar of Hundred-Year Wine", "Your hand finds a sealed jar under the roots. The clay is black with age; "
             "the wine inside smells of a hundred autumns.", ["node_gathered"], 3, [{"kind": "grant_item", "item": "hundred_year_wine", "count": 1}]),
        card("lost_child", "A Lost Child", "A child sits by the path, too frightened to cry. You walk them home, and a mother runs out "
             "to meet you.", ["room_entered"], 4, [{"kind": "deed", "deed": "lost_child_home"}], merit_weight=2,
             requires={"all": [{"kind": "room_type", "value": "field"}]}),
        card("meteor_fragment", "A Meteor Fragment", "A streak of light, a thump in the next field. The stone is still warm: Cloudsteel, "
             "fallen from somewhere far above the ledges.", ["room_entered", "node_gathered"], 3,
             [{"kind": "grant_item", "item": "cloudsteel_ore", "count": 3}]),
        card("river_dream", "A Dream of the River", "You doze for a moment and dream of the River: every land on its banks, every one "
             "who ever drank from it. You wake knowing something you did not learn.", ["room_entered"], 2,
             [{"kind": "codex", "entry": "river_dream"}, {"kind": "add_progress", "pct_of_need": 0.03}], once=True),
    ]


def rankings():
    """Part 8's Heaven Ranking (valley seeds, v1.1). Each seeded cultivator starts at a Level and climbs a little every
    week of the account's calendar, up to a ceiling; a seeded wobble keeps the order moving. Their CP follows the room
    formula (20 + 18 x Level) times their talent. You enter at the top eight by CP, or by reaching the Valley
    Tournament finals; beat the one directly above you in a spar and you hold their place for the rest of the week."""
    def seed(id, name, title, level, per_week, cap, talent, enemy):
        return {"id": id, "name": name, "title": title, "level": level, "per_week": per_week, "cap": cap, "talent": talent, "enemy": enemy}
    return [
        seed("shen_lian", "Shen Lian", "Lotus Ferry's fisher girl, now a Cloud Sect disciple", 10, 2.0, 52, 1.15, "shen_lian"),
        seed("wen_zhao", "Wen Zhao", "Your rival since the Fairground", 18, 2.0, 58, 1.1, "wen_zhao"),
        seed("cloud_first", "Yun Zhiqiu", "First disciple of the Cloud Sect", 30, 1.5, 62, 1.1, "cloud_first_disciple"),
        seed("jade_first", "Bai Yuheng", "First disciple of the Jade Sect", 31, 1.5, 63, 1.08, "jade_first_disciple"),
        seed("iron_crane", "\"Iron Crane\" Guo Ming", "A rogue cultivator nobody has pinned down", 34, 1.0, 60, 1.05, "iron_crane_guo"),
        seed("hua_captain", "Captain Lou Chen", "Madam Hua's guard captain", 24, 1.0, 44, 1.0, "hua_guard_captain"),
        seed("gorge_chief", "Chief Yan Bo", "Chief of the Gorge Bandit Adepts", 33, 0.5, 40, 1.0, "gorge_chief"),
    ]


# The Trial Tower's foes: the valley's walkers and fliers by the Levels they are met at (fish and mounts left out).
TOWER_POOL = [("rock_beetle", 4, 5), ("pebble_imp", 4, 6), ("reed_frog", 4, 6), ("ironclaw_mole", 5, 7), ("marsh_leech", 5, 7),
              ("stone_tortoise", 5, 7), ("hollowed_boarlet", 7, 12), ("bamboo_monkey", 10, 12), ("green_viper", 11, 14),
              ("thornback_boar", 13, 15), ("mudwater_bandit", 14, 19), ("bandit_archer", 16, 20), ("mud_hound", 16, 20),
              ("ember_fox", 19, 24), ("reed_otter", 19, 24), ("paper_talisman_ghost", 22, 26), ("rogue_cultivator", 24, 26),
              ("rapids_lizard", 28, 31), ("gorge_bandit_adept", 29, 33), ("boulder_serpent", 32, 35), ("mist_vulture", 34, 36),
              ("cloudwing_crane", 37, 40), ("stormwing_hawk", 38, 43), ("cliff_ape", 41, 45), ("mist_wolf", 46, 50),
              ("mirror_wisp", 47, 51), ("weeping_lantern", 50, 55), ("jade_sentinel", 52, 56), ("hollow_stag", 55, 59),
              ("cloudpeak_roc", 58, 63)]


def _tower_foes(level, n=2):
    def dist(row):
        _, lo, hi = row
        return 0 if lo <= level <= hi else min(abs(level - lo), abs(level - hi))
    ranked = sorted(TOWER_POOL, key=lambda r: (dist(r), r[1]))
    return [r[0] for r in ranked[:n]]


def tower():
    """Part 8's Trial Tower: 30 floors at Stoneford Fairground, each one room with a clear condition, two Levels a floor.
    Every fifth floor has a guardian. A cleared floor can be swept once a day for its loot, without the fight."""
    kinds = {1: "clear", 2: "survive", 3: "swift", 4: "survive", 0: "guardian"}
    rows = []
    for f in range(1, 31):
        lv = 4 + 2 * (f - 1)
        kind = kinds[f % 5]
        foes = _tower_foes(lv)
        row = {"id": "floor_%d" % f, "floor": f, "level": lv, "kind": kind, "foes": foes,
               "loot": "chest_valley" if f <= 12 else "chest_dungeon", "stones": 2 + f // 3}
        if kind == "clear":
            row.update(time_s=90, count=4)
        elif kind == "swift":
            row.update(time_s=45, count=3)
        elif kind == "survive":
            row.update(time_s=40 if f % 5 == 2 else 55)
        else:
            # The guardian ends the floor when it falls, so its escort is never its own kind.
            guardian = _tower_foes(lv + 4, 1)[0]
            row.update(time_s=120, guardian=guardian, guardian_level=lv + 4,
                       foes=[x for x in _tower_foes(lv, 4) if x != guardian][:2])
        rows.append(row)
    return rows


def activity():
    """Daily activity (S49 mobile conventions, v1.0): points from what you do each day fill four chests, for the whole
    account; they reset with the daily reset. Some sources are capped so one chore cannot fill the bar."""
    def tier(points, *rewards):
        return {"id": "chest_%d" % points, "points": points, "rewards": list(rewards)}
    return [
        tier(20, {"kind": "grant_currency", "currency": "silver_tael", "amount": 150}, {"kind": "grant_item", "item": "healing_pill", "count": 2}),
        tier(40, {"kind": "grant_currency", "currency": "silver_tael", "amount": 300}, {"kind": "grant_item", "item": "spirit_stone_shard", "count": 3}),
        tier(60, {"kind": "grant_currency", "currency": "spirit_stone", "amount": 5}, {"kind": "grant_item", "item": "manual_page", "count": 2}),
        tier(100, {"kind": "grant_currency", "currency": "spirit_stone", "amount": 15}, {"kind": "grant_item", "item": "spirit_jade", "count": 2}),
    ]


def build_extra():
    entries("rankings", rankings(), ref_cp=[20, 18], wobble=0.04, top=8, finals_quest="the_valley_finals", climb_deed="rank_climbed")
    entries("tower", tower(), room="sf_trial_tower", sweep_silver_per_floor=15)
    entries("activity", activity(),
            # Points per deed and the most each source can give in a day (0: no cap).
            sources={"mission": {"points": 10, "cap": 0}, "dungeon": {"points": 15, "cap": 0}, "craft": {"points": 4, "cap": 20},
                     "harvest": {"points": 2, "cap": 20}, "spar": {"points": 5, "cap": 15}, "tower": {"points": 10, "cap": 30},
                     "arena": {"points": 5, "cap": 15}, "beast_trial": {"points": 10, "cap": 10}})


def build():
    build_extra()
    entries("fortune_deck", fortune_deck(),
            # One encounter per three hours of play at most: the meter fills while you play and holds one.
            meter_h=3.0,
            # The chance of a vignette at each moment, while the meter is full (a fall is likelier to end strangely).
            chance={"room_entered": 0.05, "node_gathered": 0.04, "fell_out": 0.35},
            # Fortune raises the chance (+2% of it per point) and the weight of every card (+3% per point).
            fortune_chance=0.02, fortune_weight=0.03,
            # Merit and sin shift the deck: each merit_weight card gains this much weight per 100 merit.
            merit_per=100,
            # Never in the Prologue, a trial, a boss arena or while a room event runs.
            never_in=["prologue", "trial", "boss_arena", "story"],
            # The Hundred-Year Wine's blessing: the next batch's rare-pill chances, as if the furnace were this much better.
            wine_grain=0.25)
    entries("calendar", events(),
            # v1.1 weather (never gating): a seeded pick per region every three hours.
            weather_block_h=3,
            weather={"marsh": {"clear": 5, "rain": 3, "fog": 2}, "gorge": {"clear": 5, "rain": 3, "fog": 2},
                     "summit": {"clear": 4, "storm": 4, "fog": 1}},
            # What each weather does (never gating): rain makes fish bite eagerly and herbs come easier, fog helps you
            # slip a blow, a storm feeds Thunder techniques (+10%).
            weather_effects={"rain": {"fishing_window": 0.2, "stats": [{"stat": "gathering_power", "op": "pct_add", "value": 0.10}]},
                             "fog": {"stats": [{"stat": "evasion", "op": "pct_add", "value": 0.05}]},
                             "storm": {"stats": [{"stat": "elemental_power", "op": "flat", "value": 0.10, "condition": {"element": "thunder"}}]}},
            # How far ahead an event is announced (Calendar page, notifications).
            notice_h=24,
            # S49 lifespan as flavour: characters start at sixteen and a year passes every four weeks (a season a week).
            start_age=16, year_days=28,
            # S49 heavenly phenomena: a major breakthrough gathers clouds over the room; a tribulation darkens it.
            # People nearby congratulate you, and sometimes a jealous senior cannot let it pass (karma.json).
            phenomena={"cloud": {"from": "breakthrough_succeeded", "major": True}, "lightning": {"from": "tribulation_started"}})


if __name__ == "__main__":
    build()
