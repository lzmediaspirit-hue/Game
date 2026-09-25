"""S49 the living world: calendar.json (world events on the account calendar, weather tables).

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


def build():
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
            notice_h=24)


if __name__ == "__main__":
    build()
