"""P6 moments (docs/moments_design.md): data/moments.json, one row per moment kind with its trigger, filters, priority,
duration, input lock, queue rule, layers, art and a sample payload, and the settings MomentView plays them by.

MomentView (scripts/presentation/moment_view.gd) plays the rows from events; MomentRules resolves their matchers, text
and colours. data_validation's moments_data_suite checks every row against the event contract, FxLayer's kinds,
data/audio.json, the strings and UiKit's colour tokens. Colours are UiKit token names or data ids (element:, grade:,
quality:, dao:), never hex; text is a string key or a data name, never literal words.
"""
from common import write

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
# §2.3 the stat rise, in order; only the numbers that changed are shown, at most seven.
STATS = ["level", "max_hp", "max_qi", "max_soul", "physical_attack", "qi_attack", "soul_attack", "crit_chance", "lifespan"]
# §6: a Dao's effects take its element's colour; the other families take these.
DAO_COLOURS = {"weapon": "PALE_GOLD", "craft": "BRIGHT_JADE", "rare": "SOUL"}


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
        row("breakthrough_minor", "breakthrough_succeeded", dict(ACTIVE, major=False), 60, 1.8,
            [strip(0.1, 170, {"transition": ["payload.from", "payload.to"]}, 30, "PALE_GOLD",
                   sub=key("moment.level_up", "slot.level.level", if_slot="level"), sub_size=20, sub_color="BRIGHT_JADE"),
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
             {"t": 1.4, "kind": "stats", "at": [880, 318], "row_h": 36, "gap_s": 0.12},
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
            [band(0.0, 170, key("hud.tribulation_started", "payload.bolts"), 34, "PALE_GOLD", sub=key("hud.tribulation_hint"), sub_size=18,
                  wipe_s=0.3),
             {"t": 0.0, "kind": "vignette", "color": "INK", "alpha": 0.25, "edge": 180, "sides": ["top"], "held": True},
             fx(0.0, "heaven_storm", color="HEAVEN_BOLT", offset=[0, -20], dur=6.0, repeat_s=5.0), sound(0.0, "thunder"),
             shake(0.0, 0.25), bark(0.0, "world_view.phenomenon_storm", 900, 4.0)],
            {"actor": "c1", "from": "cloud_stride_9", "to": "spirit_awakening_1", "bolts": 9, "waves": 3}, "P6b",
            merge=[merge("heavenly_phenomenon", when={"kind": "lightning"})], hold_until=["tribulation_result"], max_s=120.0,
            toast=key("hud.tribulation_started", "payload.bolts", kind="danger")),
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
             shake(0.0, 0.12), sound(0.0, "breakthrough"), bark(0.0, "world_view.pill_cloud_bark", 700, 3.5)],
            {"actor": "c1", "recipe": "qi_gathering_pill", "quality": "pill_halo"}, "P6a"),
        row("boss_phase", "boss_phase", {}, 90, 1.2, [shake(0.0, 0.3), sound(0.0, "boss_roar")],
            {"enemy": 1, "phase": 2, "action": "summon"}, "P6a", stale_s=1.0),
        row("trial_opens", "room_event_started", ACTIVE, 60, 1.8,
            [text(0.0, key("event.", suffix="payload.event"), 30, "RED", at="camera", offset=[0, -180], dur=3.0)],
            {"actor": "c1", "room": "wp_west", "event": "heart_trial", "duration": 90.0}, "P6a", scope="room"),
    ]


def build():
    write("moments.json", {"entries": rows(), "settings": SETTINGS, "stats": STATS, "dao_colours": DAO_COLOURS, "vfx_tiers": VFX_TIERS})
