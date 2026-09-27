"""P6 moments (docs/moments_design.md): data/moments.json, one row per moment kind with its trigger, filters, priority,
duration, input lock, queue rule, layers, art and a sample payload, and the settings MomentView plays them by.

MomentView (scripts/presentation/moment_view.gd) plays the rows from events; MomentRules resolves their matchers, text
and colours. data_validation's moments_data_suite checks every row against the event contract, FxLayer's kinds,
data/audio.json, the strings and UiKit's colour tokens. Colours are UiKit token names or data ids (element:, grade:,
quality:), never hex; text is a string key or a data name, never literal words.
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
    return r


ACTIVE = {"actor": "active"}
BREAKTHROUGH_MERGES = [merge("level_changed", "level"), merge("realm_changed"), merge("system_unlocked", "unlocks", most=2)]


# ------------------------------------------------------------------ the rows (§2.1, §2.2)
def rows():
    return [
        row("breakthrough_channel", "breakthrough_started", ACTIVE, 0, 3.0,
            [fx(0.0, "ring", color="QI", radius=90, dur="payload.duration")],
            {"actor": "c1", "from": "qi_kindling_9", "to": "qi_unfurling_1", "risk": "low", "duration": 3.0}, "P6a"),
        row("breakthrough_minor", "breakthrough_succeeded", ACTIVE, 60, 1.8,
            [fx(0.0, "spiral", color="PALE_GOLD", offset=[0, -20], dur=1.6),
             text(0.0, {"realm": "payload.to"}, 28, "PALE_GOLD", offset=[0, -150], dur=2.5),
             shake(0.0, 0.2), sound(0.0, "breakthrough"), buzz(0.0, 120)],
            {"actor": "c1", "from": "qi_kindling_3", "to": "qi_kindling_4", "major": False, "formation": ""}, "P6a",
            merge=BREAKTHROUGH_MERGES),
        row("breakthrough_failed", "breakthrough_failed", ACTIVE, 60, 2.4,
            [text(0.0, key("world_view.breakthrough_failed"), 24, "RED", offset=[0, -150], dur=2.5), sound(0.0, "fail")],
            {"actor": "c1", "failure_id": "energy_instability", "losses": 0.2, "injuries": ["meridian"], "recovery": "Rest, restoration pill"},
            "P6a", merge=[merge("tribulation_result", "tribulation", when={"survived": False})]),
        row("realm_phenomenon", "heavenly_phenomenon", dict(ACTIVE, kind="cloud"), 0, 5.5,
            [fx(0.0, "heaven_cloud", color="HEAVEN_CLOUD", offset=[0, -20], dur=5.5), bark(0.0, "world_view.phenomenon_cloud", 900, 4.0)],
            {"actor": "c1", "kind": "cloud", "realm": "qi_unfurling_1", "room": "wp_west", "people": 2}, "P6a"),
        row("tribulation", "tribulation_started", ACTIVE, 80, 1.6,
            [fx(0.0, "heaven_storm", color="HEAVEN_BOLT", offset=[0, -20], dur=6.0), sound(0.0, "thunder"), shake(0.0, 0.25),
             bark(0.0, "world_view.phenomenon_storm", 900, 4.0)],
            {"actor": "c1", "from": "cloud_stride_9", "to": "spirit_awakening_1", "bolts": 9, "waves": 3}, "P6a",
            merge=[merge("heavenly_phenomenon", when={"kind": "lightning"})], hold_until=["tribulation_result"], max_s=120.0),
        row("level_up", "level_changed", ACTIVE, 0, 1.0,
            [text(0.0, key("world_view.level", "payload.level"), 22, "PALE_GOLD", offset=[0, -160], dur=2.0), sound(0.0, "level")],
            {"actor": "c1", "level": 12}, "P6a"),
        row("body_level", "body_level_changed", ACTIVE, 0, 2.0,
            [text(0.0, key("world_view.body_level", "payload.value"), 20, "BODY", offset=[0, -140], dur=2.0)],
            {"actor": "c1", "value": 4}, "P6a"),
        row("weapon_awakened", "weapon_awakened", ACTIVE, 50, 1.6,
            [fx(0.0, "wave", color="PALE_GOLD", radius=140, dur=0.8), sound(0.0, "breakthrough")],
            {"actor": "c1", "item": "stone_drum_gauntlets", "skill": "Mountain Drum", "legend": True}, "P6a"),
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
    write("moments.json", {"entries": rows(), "settings": SETTINGS, "vfx_tiers": VFX_TIERS})
