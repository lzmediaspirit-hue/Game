"""P6 moments (docs/moments_design.md): data/moments.json, one row per moment kind with its trigger, filters, priority,
duration, input lock, queue rule, layers, art and a sample payload, and the settings MomentView plays them by.

MomentView (scripts/presentation/moment_view.gd) plays the rows from events; MomentRules resolves their matchers, text
and colours. data_validation's moments_data_suite checks every row against the event contract, FxLayer's kinds,
data/audio.json, the strings and UiKit's colour tokens. Colours are UiKit token names or data ids (element:, grade:,
quality:, dao:), never hex; text is a string key or a data name, never literal words.
"""
import json
import os

from common import DATA, write
from techniques import PARTICLES, TIER_BY_REALM, VFX_SHAPES

SETTINGS = {"max_lock_s": 1.5, "queue_max": 4, "stale_s": 6.0, "cut_fade_s": 0.15, "flash_gap_s": 1.0, "shake_amp_per_s": 16,
            "fight_radius": 400, "snapshot_s": 1.0, "merge_rare_s": 1.5}

# §5.2 the escalation curve by technique tier (the realm band that teaches it). Tier 1 is today's look. Reduce motion
# thins every particle burst to tier 1's count and Battery saver to tier 2's.
_TIER_COLS = ["spark_count", "spark_size", "spark_reach", "core_r", "cast_ring_r", "wave_width", "echoes", "number_size",
              "shake_s", "shake_amp", "tint_alpha"]
VFX_TIERS = [dict(zip(["tier"] + _TIER_COLS, r)) for r in [
    (1, 8, 6, 28, 10, 0, 8, 0, 22, 0.0, 0.0, 0.0),
    (2, 10, 6, 32, 12, 40, 9, 0, 22, 0.0, 0.0, 0.0),
    (3, 12, 8, 38, 16, 60, 10, 1, 24, 0.06, 1.0, 0.06),
    (4, 14, 8, 44, 20, 80, 12, 1, 24, 0.08, 1.5, 0.08),
    (5, 16, 10, 50, 24, 100, 14, 2, 26, 0.10, 2.0, 0.10),
    (6, 18, 10, 56, 28, 120, 16, 2, 28, 0.12, 2.0, 0.14),
    (7, 20, 12, 64, 32, 140, 18, 3, 30, 0.14, 2.5, 0.18)]]
# §5.5 multi-hit numbers (a stack: one target, one technique, within stack_s) and §5.7 the numbers shortened from 10,000.
NUMBERS = {"stack_s": 0.3, "step_s": 0.06, "step_px": 18, "sway_px": 12, "cap": 6, "total_from": 3, "total_after_s": 0.1,
           "total_up_px": 24, "total_plus_px": 2, "short_from": 10000}
# The Techniques page's live preview (TechniquePreview): the imp that takes the art and its size, the stage's scale
# (screen px a room px), the loop's beats (s), Battery saver's step rate and pause, how many imps each form strikes (a
# single strike one, a multi-hit or area form a pack) and how the imps meet the forms that are not plain blows.
TECHNIQUE_PREVIEW = {"foe": "pebble_imp", "foe_scale": 0.75, "scale": 1.25, "lead_s": 0.4, "after_s": 0.9, "pause_s": 0.8,
                     "battery_pause_s": 1.6, "battery_fps": 30,
                     "foes": {"strike": 1, "thrust": 2, "lunge": 2, "blink": 1, "pillar": 1, "echo": 2, "counter": 1, "seal": 1,
                              "snare": 1, "ward": 1, "flurry": 3, "volley": 3, "rain": 3, "sweep": 3, "wave": 3, "burst": 3,
                              "swarm": 3, "chorus": 3, "domain": 3, "arc": 3, "seeker": 3, "return": 3, "plunge": 3, "release": 3},
                     "plays": {"ward": "ward", "counter": "counter", "snare": "bind", "seal": "bind"}}
# §2.3 the stat rise, in order; only the numbers that changed are shown, before and after, at most seven. "aura" is the
# look the realm gives the character (AURAS), so a breakthrough that changes it says so on the card.
STATS = ["level", "max_hp", "max_qi", "max_soul", "physical_attack", "qi_attack", "soul_attack", "crit_chance", "lifespan", "aura"]
# Research player_motivation §5 change 10: the realm shows on the character. Each row is the realm from which the aura
# holds (the highest one reached wins): its UiKit colour, the rings at the feet, the motes rising and the halo behind
# the body. Drawn by the player node from the existing FX shapes (a ring, motes, a soft disc); no new body pose.
AURAS = [
    {"realm": "bone_forging_1", "color": "BRIGHT_JADE", "rings": 1, "motes": 0, "halo": 0.0},
    {"realm": "bone_forging_4", "color": "BRIGHT_JADE", "rings": 1, "motes": 4, "halo": 0.0},
    {"realm": "bone_forging_7", "color": "QI", "rings": 2, "motes": 6, "halo": 0.10},
    {"realm": "qi_kindling_1", "color": "QI", "rings": 2, "motes": 8, "halo": 0.14},
    {"realm": "qi_unfurling_1", "color": "PALE_GOLD", "rings": 2, "motes": 10, "halo": 0.16},
    {"realm": "heart_tempering_1", "color": "PALE_GOLD", "rings": 3, "motes": 12, "halo": 0.18},
    {"realm": "cloud_stride_1", "color": "GOLD", "rings": 3, "motes": 14, "halo": 0.20},
]
# §6: a Dao's effects take its element's colour; the other families take these.
DAO_COLOURS = {"weapon": "PALE_GOLD", "craft": "BRIGHT_JADE", "rare": "SOUL"}
# §5.8 the loot fountain by the drop's source: apex and flight as [base, per item, cap], the gap between launches, and a
# flash at the drop for a boss. Any other source (a foe, a jar) keeps today's bounce.
_BOSS_FOUNTAIN = {"apex": [120, 14, 200], "flight": [0.55, 0.04, 0.9], "gap": 0.05, "flash": "PALE_GOLD"}
_CHEST_FOUNTAIN = {"apex": [80, 10, 140], "flight": [0.45, 0.03, 0.7], "gap": 0.04}
FOUNTAIN = {"boss": _BOSS_FOUNTAIN, "field_boss": _BOSS_FOUNTAIN, "chest": _CHEST_FOUNTAIN, "tower": _CHEST_FOUNTAIN, "rift": _CHEST_FOUNTAIN}
BOSS_ROLES = ["field_boss", "dungeon_boss", "story_boss"]


def _entries(name):
    return json.load(open(os.path.join(DATA, name + ".json"), encoding="utf-8"))["entries"]


def rare():
    """§3.4 what a rare find is: a Perfect or Relic piece, a legend piece, a spirit animal's book, a treasure, or a named
    drop (a boss's unique drop, a first-defeat reward, a set piece, a legendary chain's piece). Coins never."""
    named = set()
    for e in _entries("enemies"):
        named.update([e["unique_drop"]] if e.get("unique_drop") else [])
        named.update(e.get("first_defeat", []) + e.get("elite_first_defeat", []))
    for s in _entries("sets"):
        named.update(s["pieces"])
    for chain in _entries("legendary_chains"):
        named.update(p["item"] for p in chain["pieces"])
    return {"qualities": ["perfect", "relic"], "types": ["legend_piece", "pet_book", "treasure", "treasure_art"],
            "items": {i: True for i in sorted(named)}}


def chapter_ends():
    """The main quest that closes each chapter: the last one listed whose next quest is none or in another chapter."""
    mains = [q for q in _entries("quests") if q.get("kind") == "main" and q.get("chapter") is not None]
    chapter = {q["id"]: str(q["chapter"]) for q in mains}
    ends = {}
    for q in mains:
        if not q.get("next") or chapter.get(q["next"]) != chapter[q["id"]]:
            ends[str(q["chapter"])] = q["id"]
    return {quest: ch for ch, quest in ends.items()}


# ------------------------------------------------------------------ layer and text helpers
def key(k, *args, **kw):
    """A string key, formatted with payload values ("payload.x") or other text sources."""
    return dict({"key": k}, **({"args": list(args)} if args else {}), **kw)


def fx(t, kind, at="actor", **kw):
    return dict({"t": t, "kind": "fx", "fx": kind, "at": at}, **kw)


def text(t, src, size, color, at="actor", **kw):
    return dict({"t": t, "kind": "text", "text": src, "size": size, "color": color, "at": at}, **kw)


def sound(t, sfx, **kw):
    return dict({"t": t, "kind": "sound", "sfx": sfx}, **kw)


def shake(t, s):
    return {"t": t, "kind": "shake", "s": s}


def buzz(t, ms):
    return {"t": t, "kind": "buzz", "ms": ms}


def bark(t, prefix, radius, dur):
    return {"t": t, "kind": "bark", "key": prefix, "radius": radius, "dur": dur}


def band(t, y, title, size, color, **kw):
    """The ink band (mockup 05): an optional letter-spaced line `over` it, the title, a `sub` line under it."""
    return dict({"t": t, "kind": "band", "y": y, "title": title, "size": size, "color": color, "wipe_s": 0.4}, **kw)


def strip(t, y, title, size, color, **kw):
    """A slim ink band: a title, a `sub` line and any `more` lines."""
    return dict({"t": t, "kind": "strip", "y": y, "title": title, "size": size, "color": color}, **kw)


def merge(event, into="", when=None, most=None, keep_sound=False):
    m = {"event": event, "when": when or {}, "into": into, "keep_sound": keep_sound}
    if most:
        m["max"] = most
    return m


def row(rid, event, when, priority, duration, layers, sample, step, **kw):
    r = {"id": rid, "event": event, "when": when, "priority": priority, "duration_s": duration, "lock_s": 0.0, "skip": "",
         "skip_to_s": 0.0, "stale_s": SETTINGS["stale_s"], "in_fight": "play", "scope": "actor", "merge": [], "hold_until": [],
         "max_s": 0.0, "toast": {}, "layers": layers, "art": [], "sample": sample, "step": step}
    r.update(kw)
    if any(L["kind"] in ("band", "strip") for L in layers + [L for v in r.get("variants", []) for L in v["layers"]]):
        r["art"] = ["ink_band"]
    return r


ACTIVE = {"actor": "active"}
BREAKTHROUGH_MERGES = [merge("level_changed", "level"), merge("realm_changed"), merge("system_unlocked", "unlocks", most=2)]
OPENS = {"t": 0.5, "kind": "chip", "slot": "unlocks", "at": [960, 588]}
DAO = {"name_of": "daos", "id": "payload.dao"}
DAO_LINE = {"field_of": "daos", "id": "payload.dao", "field": "tiers", "at": "payload.tier"}
RANK = key("ui.guild.rank_", suffix="payload.rank")
PET_FORM = key("hud.grows_into_a", {"pet": "payload.pet"}, {"pet_form": "payload.stage", "branch": "payload.branch"})


# ------------------------------------------------------------------ the rows (§2.1, §2.2)
def rows():
    return [
        row("breakthrough_channel", "breakthrough_started", ACTIVE, 0, 3.0,
            [fx(0.0, "ring", color="QI", radius=90, dur="payload.duration")],
            {"actor": "c1", "from": "qi_kindling_9", "to": "qi_unfurling_1", "risk": "low", "duration": 3.0}, "P6a"),
        # Research §5 change 10: every realm step shows what it gave, before and after, on a card beside the strip.
        row("breakthrough_minor", "breakthrough_succeeded", dict(ACTIVE, major=False), 60, 3.6,
            [strip(0.1, 170, {"transition": ["payload.from", "payload.to"]}, 30, "PALE_GOLD",
                   sub=key("moment.level_up", "slot.level.level", if_slot="level"), sub_size=20, sub_color="BRIGHT_JADE"),
             {"t": 0.4, "kind": "stats", "at": [880, 318], "row_h": 36, "gap_s": 0.12, "frame": "toast", "title": key("moment.stats.title")},
             OPENS, fx(0.0, "spiral", color="PALE_GOLD", offset=[0, -20], dur=1.6), fx(0.0, "ring", color="PALE_GOLD", radius=70, dur=0.5),
             sound(0.0, "level"), buzz(0.0, 60)],
            {"actor": "c1", "from": "qi_kindling_3", "to": "qi_kindling_4", "major": False, "formation": ""}, "P6b",
            merge=BREAKTHROUGH_MERGES, toast=key("moment.breakthrough.toast", {"realm": "payload.to"})),
        # §2.3, mockup 05: the light gathers (0-0.6 s), the name is written (0.6-1.4 s), the stats rise (1.4-2.4 s).
        row("breakthrough_major", "breakthrough_succeeded", dict(ACTIVE, major=True), 70, 4.0,
            [{"t": 0.0, "kind": "dim", "color": "INK", "alpha": 0.45, "fade_in": 0.3, "until": 3.6, "radial": True},
             fx(0.0, "converge", offset=[0, -60], color="PALE_GOLD", count=16, radius=300, dur=0.6),
             fx(0.0, "pillar", color="PALE_GOLD", radius=90, height=660, dur=3.0),
             fx(0.0, "ring", color="PALE_GOLD", radius=130, count=3, dur=1.2),
             sound(0.0, "breakthrough"), buzz(0.0, 120),
             band(0.6, 138, {"realm_great": "payload.to"}, 92, "PALE_GOLD", glow="GOLD", over=key("moment.breakthrough.over"),
                  sub={"transition": ["payload.from", "payload.to"]}),
             sound(0.6, "brush_stroke"), shake(0.6, 0.2),
             {"t": 1.3, "kind": "seal", "at": "band", "size": 44, "angle": -8, "color": "RED", "text": {"stage": "payload.to"}},
             sound(1.3, "seal_press"),
             {"t": 1.4, "kind": "card", "slot": "tribulation", "rect": [72, 330, 352, 104], "slide_from": "left",
              "lines": [{"text": key("moment.tribulation.weathered"), "size": 18, "color": "PALE_GOLD"},
                        {"text": key("moment.tribulation.line", "slot.last.tribulation_started.waves", "slot.tribulation.bolts",
                                     "slot.tribulation.struck"), "size": 15, "color": "PAPER"}],
              "bar": {"value": "slot.now.hp_pct", "label": key("moment.tribulation.hp_kept", "slot.now.hp_pct"), "color": "RED"}},
             {"t": 1.4, "kind": "stats", "at": [880, 318], "row_h": 36, "gap_s": 0.12, "frame": "toast", "title": key("moment.stats.title")},
             dict(OPENS, t=2.0), sound(2.0, "unlock", bus="UI", if_slot="unlocks")],
            {"actor": "c1", "from": "will_manifest_3", "to": "sphere_lord_1", "major": True, "formation": ""}, "P6b",
            lock_s=1.5, skip="tap", skip_to_s=2.4,
            merge=BREAKTHROUGH_MERGES + [merge("tribulation_result", "tribulation", when={"survived": True})],
            toast=key("moment.breakthrough.toast", {"realm": "payload.to"})),
        row("breakthrough_failed", "breakthrough_failed", ACTIVE, 60, 2.4,
            [{"t": 0.0, "kind": "dim", "color": "INK", "alpha": 0.3, "fade_in": 0.2, "until": 1.2},
             strip(0.0, 170, key("world_view.breakthrough_failed"), 30, "RED", sub=key("failure.", suffix="payload.failure_id"),
                   sub_size=20, sub_color="PAPER",
                   more=[{"payload": "payload.recovery"},
                         key("moment.tribulation.struck", "slot.tribulation.struck", "slot.tribulation.bolts", if_slot="tribulation")]),
             fx(0.0, "spark", color="MIST", offset=[0, -60], count=12, style="shard", dur=0.6), sound(0.0, "fail")],
            {"actor": "c1", "failure_id": "energy_instability", "losses": 0.2, "injuries": ["meridian"], "recovery": "Rest, restoration pill"},
            "P6b", merge=[merge("tribulation_result", "tribulation", when={"survived": False})],
            toast=key("moment.failed.toast", key("failure.", suffix="payload.failure_id"), kind="danger")),
        row("realm_phenomenon", "heavenly_phenomenon", dict(ACTIVE, kind="cloud"), 0, 5.5,
            [fx(0.0, "heaven_cloud", color="HEAVEN_CLOUD", offset=[0, -20], dur=5.5), bark(0.0, "world_view.phenomenon_cloud", 900, 4.0)],
            {"actor": "c1", "kind": "cloud", "realm": "qi_unfurling_1", "room": "wp_west", "people": 2}, "P6a"),
        row("tribulation", "tribulation_started", ACTIVE, 80, 1.6,
            [band(0.0, 170, key("hud.tribulation_started", "payload.bolts", plural="payload.bolts"), 34, "PALE_GOLD", sub=key("hud.tribulation_hint"), sub_size=18,
                  wipe_s=0.3),
             {"t": 0.0, "kind": "vignette", "color": "INK", "alpha": 0.25, "edge": 180, "sides": ["top"], "held": True},
             fx(0.0, "heaven_storm", color="HEAVEN_BOLT", offset=[0, -20], dur=6.0, repeat_s=5.0), sound(0.0, "thunder"),
             shake(0.0, 0.25), bark(0.0, "world_view.phenomenon_storm", 900, 4.0)],
            {"actor": "c1", "from": "cloud_stride_9", "to": "spirit_awakening_1", "bolts": 9, "waves": 3}, "P6b",
            merge=[merge("heavenly_phenomenon", when={"kind": "lightning"})], hold_until=["tribulation_result"], max_s=120.0,
            toast=key("hud.tribulation_started", "payload.bolts", plural="payload.bolts", kind="danger")),
        row("level_up", "level_changed", ACTIVE, 0, 1.0,
            [fx(0.0, "ring", color="PALE_GOLD", radius=40, dur=0.4),
             text(0.0, key("world_view.level", "payload.level"), 22, "PALE_GOLD", offset=[0, -160], dur=2.0), sound(0.0, "gong_short")],
            {"actor": "c1", "level": 12}, "P6b"),
        row("body_level", "body_level_changed", ACTIVE, 0, 2.0,
            [text(0.0, key("world_view.body_level", "payload.value"), 20, "BODY", offset=[0, -140], dur=2.0)],
            {"actor": "c1", "value": 4}, "P6a"),
        row("body_tier", "body_tier_reached", ACTIVE, 50, 1.6,
            [strip(0.0, 170, {"payload": "payload.name"}, 30, "PALE_GOLD", sub=key("moment.body_tier.sub")),
             fx(0.0, "ring", color="BRONZE", radius=80, dur=0.6), fx(0.0, "dust", dur=0.5), sound(0.0, "bell")],
            {"actor": "c1", "tier": "iron", "name": "Iron Body"}, "P6b", merge=[merge("body_level_changed")],
            toast=key("moment.body_tier.toast", {"payload": "payload.name"})),
        row("dao_tier", "dao_tier_up", ACTIVE, 50, 1.8,
            [strip(0.0, 170, key("moment.dao.title", DAO, "payload.tier"), 30, "PALE_GOLD", sub=DAO_LINE),
             fx(0.0, "converge", color="dao:payload.dao", count=16, radius=160, dur=0.6), sound(0.4, "bell")],
            {"actor": "c1", "dao": "sword", "tier": 3}, "P6b", in_fight="toast", toast=key("moment.dao.toast", DAO, "payload.tier"),
            # A Dao's sixth tier writes the large band.
            variants=[{"when": {"tier": 6}, "duration_s": 2.4, "layers": [
                band(0.0, 150, key("moment.dao.title", DAO, "payload.tier"), 64, "PALE_GOLD", glow="GOLD", sub=DAO_LINE, sub_color="MIST"),
                fx(0.0, "converge", color="dao:payload.dao", count=16, radius=160, dur=0.6), sound(0.4, "bell")]}]),
        # Research §5 change 3: a technique taught (Lu's Flowing Palm, the Weapon Hall's art) is its own moment: its name
        # on the strip, where to find it under it, and the light gathering into the hands.
        row("technique_learned", "technique_learned", ACTIVE, 55, 2.2,
            [strip(0.0, 200, {"name_of": "techniques", "id": "payload.technique"}, 30, "PALE_GOLD",
                   sub=key("moment.technique.sub"), sub_size=20, sub_color="BRIGHT_JADE"),
             fx(0.0, "converge", color="PALE_GOLD", offset=[0, -40], count=14, radius=150, dur=0.6),
             fx(0.5, "ring", color="BRIGHT_JADE", radius=70, dur=0.5), sound(0.0, "unlock", bus="UI"), buzz(0.0, 40)],
            {"actor": "c1", "technique": "flowing_palm"}, "P6b", in_fight="toast",
            toast=key("moment.technique.toast", {"name_of": "techniques", "id": "payload.technique"})),
        row("title_earned", "title_changed", dict(ACTIVE, earned=True), 40, 1.6,
            [strip(0.0, 200, {"name_of": "titles", "id": "payload.title"}, 30, "PALE_GOLD", sub={"affixes_of": "titles", "id": "payload.title"}),
             {"t": 0.25, "kind": "seal", "at": "strip", "size": 40, "angle": -8, "color": "RED", "text": key("moment.title.seal")}, sound(0.25, "seal_press")],
            {"actor": "c1", "title": "fleet_footed", "earned": True}, "P6b", in_fight="toast",
            toast=key("moment.title.toast", {"name_of": "titles", "id": "payload.title"})),
        row("craft_mastery", "profession_rank_up", ACTIVE, 50, 1.6,
            [strip(0.0, 200, key("moment.craft.title", {"craft": "payload.craft"}, RANK), 30, "PALE_GOLD"),
             fx(0.0, "converge", color="BRIGHT_JADE", count=12, radius=120, dur=0.6), sound(0.0, "unlock", bus="UI")],
            {"actor": "c1", "craft": "alchemy", "rank": "adept"}, "P6b", in_fight="toast",
            toast=key("moment.craft.toast", {"craft": "payload.craft"}, RANK)),
        row("guild_rank", "guild_rank_changed", ACTIVE, 50, 1.6,
            [strip(0.0, 200, key("moment.craft.title", {"craft": "payload.craft"}, RANK), 30, "PALE_GOLD",
                   sub=key("moment.guild.title", {"name_of": "titles", "id": "slot.title.title"}, if_slot="title")),
             fx(0.0, "converge", color="BRIGHT_JADE", count=12, radius=120, dur=0.6), sound(0.0, "unlock", bus="UI")],
            {"actor": "c1", "craft": "alchemy", "rank": "adept", "title": "guild_adept"}, "P6b", in_fight="toast",
            merge=[merge("title_changed", "title", when={"earned": True})], toast=key("moment.craft.toast", {"craft": "payload.craft"}, RANK)),
        row("pet_evolution", "pet_evolved", ACTIVE, 50, 1.6,
            [strip(0.0, 200, PET_FORM, 28, "PALE_GOLD"),
             fx(0.0, "spiral", at="pet", color="PALE_GOLD", dur=1.2), fx(0.0, "ring", at="pet", color="PALE_GOLD", radius=60, dur=0.6),
             sound(0.0, "unlock", bus="UI")],
            {"actor": "c1", "pet": "p1", "from": "cub", "stage": "grown", "branch": ""}, "P6b", in_fight="toast", toast=PET_FORM),
        row("weapon_awakened", "weapon_awakened", ACTIVE, 50, 1.6,
            [strip(0.0, 200, {"item": "payload.item"}, 30, "grade:item.grade", sub=key("hud.weapon_awakened_sub", "payload.skill"),
                   sub_color="PAPER"),
             fx(0.0, "wave", color="PALE_GOLD", radius=140, dur=0.8), fx(0.0, "pillar", color="GOLD", radius=30, height=300, dur=0.8),
             sound(0.0, "bell")],
            {"actor": "c1", "item": "stone_drum_gauntlets", "skill": "Mountain Drum", "legend": True}, "P6b",
            toast=key("hud.weapon_awakened", {"item": "payload.item"})),
        row("rare_pill", "pill_cloud", {}, 0, 3.5,
            [fx(0.0, "pill_cloud", color="quality:payload.quality", offset=[0, -70], dur=3.5),
             text(0.0, key("world_view.pill_cloud_", suffix="payload.quality"), 26, "quality:payload.quality", offset=[0, -190], dur=3.0),
             shake(0.0, 0.12), sound(0.0, "rare_chime"), bark(0.0, "world_view.pill_cloud_bark", 700, 3.5)],
            {"actor": "c1", "recipe": "qi_gathering_pill", "quality": "pill_halo"}, "P6c"),
        # §2.4 until P9a: the first aggro of a boss since the room was entered; the boss does not wait, so no lock.
        row("boss_intro", "enemy_aggro", {"target": "active", "role_in": BOSS_ROLES, "first_in_room": True}, 90, 2.0,
            [{"t": 0.0, "kind": "letterbox", "height": 64, "slide_s": 0.3},
             {"t": 0.1, "kind": "card", "frame": "", "align": "center", "rect": [140, 212, 1000, 120],
              "lines": [{"text": {"name_of": "enemies", "id": "payload.def"}, "size": 56, "color": "PALE_GOLD", "display": True},
                        {"text": {"first": [{"boss": "epithet", "id": "payload.def"}, key("moment.boss.level", "enemy.level")]},
                         "size": 22, "color": "MIST"}]},
             {"t": 0.3, "kind": "subtitle", "y": 610, "text": {"boss": "intro", "id": "payload.def"}},
             sound(0.0, "boss_sting"), {"t": 0.0, "kind": "caption", "text": key("hud.caption.boss_sting")}],
            {"enemy": 1, "target": "c1", "def": "big_toad_tan"}, "P6c", stale_s=1.5, scope="room"),
        # The fight's stage in a numeral under the boss bar (P9 adds the phase's own card); a late one drops silently.
        row("boss_phase", "boss_phase", {}, 90, 1.2,
            [band(0.0, 176, key("moment.numeral.", suffix="payload.phase"), 40, "GOLD", wipe_s=0.2),
             shake(0.0, 0.3), sound(0.0, "boss_roar")],
            {"enemy": 1, "phase": 2, "action": "summon"}, "P6c", stale_s=1.0),
        row("boss_defeated", "boss_defeated", {}, 70, 2.4,
            [{"t": 0.0, "kind": "flash", "color": "PALE_GOLD", "alpha": 0.35, "dur": 0.25},
             band(0.0, 230, {"name_of": "enemies", "id": "payload.enemy"}, 44, "PALE_GOLD", wipe_s=0.3, sub=key("moment.boss.defeated"),
                  sub_size=22, sub_color="GOLD", more=[key("moment.boss.untouched", **{"if": "clean"})], more_color="BRIGHT_JADE"),
             shake(0.0, 0.25), sound(0.0, "boss_fall")],
            {"room": "mh_boss_den", "enemy": "big_toad_tan", "role": "dungeon_boss", "clean": True}, "P6c",
            merge=[merge("achievement_unlocked", "untouched", when={"id": "untouched"})],
            toast=key("hud.is_defeated", {"name_of": "enemies", "id": "payload.enemy"})),
        row("field_boss_defeated", "field_boss_defeated", {}, 70, 2.4,
            [{"t": 0.0, "kind": "flash", "color": "PALE_GOLD", "alpha": 0.35, "dur": 0.25},
             band(0.0, 230, {"name_of": "enemies", "id": "payload.enemy"}, 44, "PALE_GOLD", wipe_s=0.3, sub=key("moment.boss.defeated"),
                  sub_size=22, sub_color="GOLD"),
             shake(0.0, 0.25), sound(0.0, "boss_fall")],
            {"room": "dw_serpents_shallows", "enemy": "riverbed_serpent"}, "P6c", toast=key("hud.is_defeated", {"name_of": "enemies", "id": "payload.enemy"})),
        row("loot_fountain", "loot_dropped", {"source_in": sorted(FOUNTAIN)}, 0, 0.9,
            [{"t": 0.0, "kind": "fountain"}, sound(0.0, "coin")],
            {"room": "mh_boss_den", "items": [], "x": 640.0, "y": 820.0, "source": "boss", "first_weapon": False}, "P6c"),
        # A rare find: its names on a strip, a beam over each rare piece until it is picked up. Rare drops within
        # merge_rare_s join one strip (three names, then "+N"); it waits longer than most, as a find is worth seeing late.
        row("rare_drop", "loot_dropped", {"rare": True}, 40, 1.8,
            [strip(0.0, 206, key("moment.rare.title"), 18, "GOLD", names="rare", sub_size=24),
             {"t": 0.0, "kind": "beam", "height": 240, "width": 10, "pulse_hz": 0.6}, sound(0.0, "rare_chime"), buzz(0.0, 40)],
            {"room": "mh_boss_den", "items": [{"uid": 1, "item": "mudwater_cleaver", "count": 1, "coins": 0, "quality": "common"}],
             "x": 640.0, "y": 820.0, "source": "boss", "first_weapon": False}, "P6d", in_fight="toast", stale_s=8.0, join_s=SETTINGS["merge_rare_s"],
            toast=key("moment.rare.toast", {"item": "slot.rare.item"}),
            # A character's first weapon (grades.json drop.starter) is a find of its own: its beam and strip say so.
            variants=[{"when": {"first_weapon": True}, "layers": [
                strip(0.0, 206, key("moment.first_weapon.title"), 18, "GOLD", names="rare", sub_size=24),
                {"t": 0.0, "kind": "beam", "height": 240, "width": 10, "pulse_hz": 0.6}, sound(0.0, "rare_chime"), buzz(0.0, 40)],
                "toast": key("moment.first_weapon.toast", {"item": "slot.rare.item"})}]),
        # The main quest that closes a chapter, after its dialogue page closes.
        row("story_beat", "quest_completed", {"actor": "active", "kind": "main", "chapter_end": True}, 60, 2.6,
            [{"t": 0.0, "kind": "letterbox", "height": 48, "slide_s": 0.3},
             band(0.0, 300, {"payload": "payload.name"}, 44, "PALE_GOLD", over={"chapter_of": "payload.quest"}, over_size=22,
                  over_color="GOLD", sub=key("moment.story.done"), sub_color="MIST", wipe_s=0.3),
             sound(0.0, "bell")],
            {"actor": "c1", "quest": "mudwater_hideout", "name": "Mudwater Hideout", "kind": "main"}, "P6d", in_fight="toast",
            toast=key("moment.story.toast", {"payload": "payload.name"})),
        # Early surprises (docs/research/player_motivation.md item 7): a fortune card, the first Spirit Fruit, and a
        # common foe come as an elite. (A rare find from the first monsters plays rare_drop above.)
        row("fortune_card", "fortune_encounter", ACTIVE, 50, 2.0,
            [strip(0.0, 190, key("moment.fortune.title"), 18, "GOLD", sub={"name_of": "fortune_deck", "id": "payload.card"}, sub_size=28,
                   sub_color="PALE_GOLD"),
             fx(0.0, "converge", color="PALE_GOLD", count=12, radius=140, dur=0.6), sound(0.0, "rare_chime"), buzz(0.0, 40)],
            {"actor": "c1", "card": "remnant_ring", "trigger": "room_entered", "room": "wp_east"}, "P6d", in_fight="toast",
            toast=key("moment.fortune.toast", {"name_of": "fortune_deck", "id": "payload.card"})),
        row("first_fruit", "treasure_birth_announced", {"first": True}, 50, 2.2,
            [strip(0.0, 190, key("moment.fruit.title"), 30, "PALE_GOLD", sub=key("moment.fruit.sub"), sub_size=20, sub_color="BRIGHT_JADE"),
             sound(0.0, "bell")],
            {"room": "wp_west", "item": "spirit_fruit", "ends": 0.0, "first": True}, "P6d", in_fight="toast", scope="room",
            toast=key("moment.fruit.title")),
        row("elite_appears", "elite_spawned", {"random": True}, 30, 1.4,
            [strip(0.0, 190, key("moment.elite.title"), 18, "GOLD", sub={"name_of": "enemies", "id": "payload.def"}, sub_size=26, sub_color="PAPER"),
             sound(0.0, "boss_sting")],
            {"room": "wp_west", "enemy": 1, "def": "wild_boarlet", "level": 2, "random": True}, "P6d", in_fight="toast", scope="room",
            toast=key("moment.elite.title")),
        row("trial_opens", "room_event_started", ACTIVE, 60, 1.8,
            [band(0.0, 170, key("event.", suffix="payload.event"), 34, "PALE_GOLD", wipe_s=0.3), sound(0.0, "bell")],
            {"actor": "c1", "room": "wp_west", "event": "heart_trial", "duration": 90.0}, "P6d", scope="room",
            toast=key("event.", suffix="payload.event", kind="danger")),
    ]


def build():
    write("moments.json", {"entries": rows(), "settings": SETTINGS, "stats": STATS, "auras": AURAS, "dao_colours": DAO_COLOURS, "fountain": FOUNTAIN,
                           "rare": rare(), "chapter_ends": chapter_ends(), "vfx_tiers": VFX_TIERS, "vfx_bands": TIER_BY_REALM, "vfx_shapes": VFX_SHAPES,
                           "particles": PARTICLES, "numbers": NUMBERS, "technique_preview": TECHNIQUE_PREVIEW})
