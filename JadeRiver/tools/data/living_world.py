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
            # How far ahead an event is announced (Calendar page, notifications).
            notice_h=24)


if __name__ == "__main__":
    build()
