"""Decision 45, phase 2 (E6, audit 45 §6.6): the cue table, data/cues.json (docs/architecture/cues.md).

    python3 tools/data/cues.py            # write it (build_data.py runs it too)
    python3 tools/data/cues.py --check    # fail unless the file is current (tools/data/README.md)

How the game answers an event on screen and in the ears, one row an answer: an event, who plays the row (`to`), when
it holds (`when`) and what it does, in order (`do`): an effect of the effects layer, a sound of the sound bank, a
shake, a thing's hit flash, or a named handler for the few answers that are code. The world views play the rows `to`
"world" (WorldShared.play, for the top-down room and the side view alike); the reading is Cues
(scripts/presentation/cues.gd), which the HUD's notices (the HUD half of E6) are meant to share.

Of an event's rows for one player the first whose `when` holds plays, as a match arm did. Sounds are the sound bank's
ids (data/audio.json), never copies; text is a string key or a data name (MomentRules.text, as moments.json's).

The build checks each row's shape, that its event is one the game emits (the event contract, or an emit of that name
in scripts/), that its sounds are in data/audio.json and that its string keys are in data/strings/en.json. The game's
side (FxLayer's kinds, WorldShared's anchors and handlers, UiKit's colour tokens) is checked by tests/cue_tests.gd,
which also plays every row.
"""
import json
import os
import re

from common import DATA, ROOT, SCHEMA_VERSION, emit, fail, read, run_cli

# ------------------------------------------------------------------ the vocabulary
TO = ["world"]                                    # who plays a row (the HUD half adds "hud")
ANCHORS = ["feet", "ground", "point", "object", "foe"]
FLIPS = ["side"]                                  # an offset's x turned by the payload's side (a wall kicked off)
STEPS = ["fx", "sound", "shake", "hit_flash", "call"]
ACTIVE = {"actor": "active"}                      # the payload's actor is the active character


def row(event, *do, when=None, name=None, to="world"):
    """One answer to `event`: its steps in order. `name` tells apart an event's rows (its id: to.event.name)."""
    r = {"id": ".".join([to, event] + ([name] if name else [])), "to": to, "event": event}
    if when:
        r["when"] = when
    r["do"] = list(do)
    return r


def fx(kind, at="feet", off=None, flip=None, **params):
    """An effect of the effects layer (FxLayer.add's kinds, or its `label` and `parry`) at an anchor, moved by `off`
    ([x, y]; its x turned by the payload's side with `flip`), with FxLayer's own parameters."""
    s = {"fx": kind}
    if at != "feet":
        s["at"] = at
    if off:
        s["off"] = list(off)
    if flip:
        s["flip"] = flip
    s.update(params)
    return s


def label(text, color, size, **kw):
    """A word that rises like a number (FxLayer.label)."""
    return fx("label", text=text, color=color, size=size, **kw)


def sound(sid):
    return {"sound": sid}


def shake(s):
    return {"shake": s}


def call(handler):
    return {"call": handler}


def payload(key, default):
    """A payload value with its default when the payload leaves it out."""
    return {"payload": key, "or": default}


def when(cond, then, otherwise):
    return {"if": cond, "then": then, "else": otherwise}


def tx(key, *args):
    """A string key, formatted with its arguments (text sources)."""
    return {"key": key, "args": list(args)} if args else {"key": key}


def name_of(table, ref):
    return {"name_of": table, "id": ref}


HAZARD = name_of("hazards", "payload.hazard")


# ------------------------------------------------------------------ the world's cues (WorldShared.play)
def world():
    out = [
        # A foe turning on the player: "!" over its head.
        row("enemy_aggro", label("!", "GOLD", 26, at="foe", off=(0, -24))),
        row("loot_dropped", call("loot_views")),
    ]
    # The movement arts' feedback (S43).
    for art, step in [("air_dash", sound("dodge")),
                      ("glide", fx("dust", off=(0, -40), color=["BRIGHT_JADE", 0.5], dur=0.3)),
                      ("water_skimming", sound("water_step")),
                      ("bounce", sound("land"))]:
        out.append(row("art_used", step, when=dict(ACTIVE, art=art), name=art))
    out += [
        row("volume_entered", sound("water_step"), when=dict(ACTIVE, kind=["water_deep", "rising_water"])),
        row("wall_kicked", fx("spark", off=(14, -50), flip="side", color="PAPER", dur=0.25), when=ACTIVE),
        row("fell_out", fx("text", off=(0, -130), text=tx("hud.fell"), color="MIST", size=18, dur=1.4), when=ACTIVE),
        # P6e: its number and spark at its tier (FxLayer.hit), the shakes and the sound (CombatFx).
        row("hit_landed", call("combat_hit")),
    ]
    # A hazard's warning: its own sound, else the tell.
    for hz, sid in [("falling_rocks", "rumble"), ("lightning", "charge"), ("poison_mist", "hiss")]:
        out.append(row("hazard_warned", sound(sid), when={"hazard": hz}, name=hz))
    out += [
        row("hazard_warned", sound("tell"), name="other"),
        # A hazard striking the player: answered by an attribute, or passing harmless (its name).
        row("hazard_struck", label(tx("world_view.hazard_answered", HAZARD), "BRIGHT_JADE", 17, off=(0, -130)),
            when=dict(ACTIVE, answered=True), name="answered"),
        row("hazard_struck", label(HAZARD, "PALE_GOLD", 17, off=(0, -130)), when=dict(ACTIVE, amount=0), name="harmless"),
    ]
    # A blow that did not land says so where it happened (CombatFx.word).
    out += [row(ev, call("combat_word")) for ev in ["hit_missed", "hit_immune", "hit_dodged"]]
    out += [
        row("parried", fx("parry"), sound("parry")),
        row("actor_defeated", fx("dust", at="ground", dur=0.5)),
        row("object_hit", {"hit_flash": 0.15}, fx("spark", at="ground", off=(0, -30), color="PALE_GOLD", dur=0.2), sound("hit")),
        row("object_broken", fx("dust", at="object", dur=0.5), sound("break")),
        # S47: a spare artifact detonated.
        row("artifact_detonated",
            fx("wave", color="#ff9a5a", radius={"const": "detonation.radius", "or": 180}, dur=0.5),
            fx("flash", off=(0, -50), color="#ffe0a0", radius=90, dur=0.35),
            shake(0.35), sound("rumble")),
    ]
    # S47: a talisman's paper flares and burns away; an attack talisman bursts where it lands.
    lands = {"at": "point", "off": (0, -40)}
    for name, cond, steps in [
            ("flame", {"kind": "attack", "item": "flame_talisman"},
             [fx("wave", **lands, color="#ff8a4a", radius=90, dur=0.45), fx("flash", **lands, color="#fff0c0", radius=50, dur=0.3)]),
            ("attack", {"kind": "attack"},
             [fx("wave", **lands, color="#9fd8ff", radius=90, dur=0.45), fx("flash", **lands, color="#fff0c0", radius=50, dur=0.3)]),
            ("defence", {"kind": "defence"}, [fx("wave", off=(0, -50), color="#c8ccd0", radius=46, dur=0.6)]),
            ("other", None, [fx("spark", off=(0, -70), color="#e8d99a", dur=0.4)])]:
        out.append(row("talisman_used", *steps, sound("technique"), when=cond, name=name))
    out += [
        # S47 blood-drop bind: a bead of blood falls onto a piece worn for the first time.
        row("item_blooded", fx("spark", off=(0, -70), color="#c0303a", dur=0.5),
            fx("text", off=(0, -120), text="·", color="#d23a44", size=34, dur=0.9)),
        row("natal_broken", fx("flash", off=(0, -50), color="#ff6a5a", radius=70, dur=0.4), shake(0.3), sound("break")),
        row("array_deployed", fx("wave", at="ground", color="array:payload.kind", radius="payload.radius", dur=0.5), sound("forge")),
        row("artifact_skill_used",
            fx("wave", at="ground", color=when({"awakened": True}, "#ffd27a", "#b18de2"),
               radius=when({"ring": {"gt": 0}}, "payload.ring", 60), dur=when({"ring": {"gt": 0}}, 0.4, 0.3)),
            sound("surge"), when=ACTIVE),
        row("array_faded", sound("ui_close"), when=ACTIVE),
        # S47 v1.1 flute: the melody spreads as a jade ring, notes drifting up from the player.
        row("melody_pulse", fx("ring", at="ground", color=[0.56, 0.91, 0.81, 0.8], radius="payload.radius", dur=0.55),
            call("melody_notes")),
        row("melody_changed", fx("wave", color="#8fe8cf", radius=70, dur=0.5), sound("meditate"), when=dict(ACTIVE, on=True)),
    ]
    # S47: the flying sword leaving and returning.
    out += [row(ev, fx("spark", off=(0, -100), color="#dff3ff", dur=0.3), sound("forge")) for ev in ["sword_released", "sword_returned"]]
    # A treasure used (S47), by what it does; its reach is the treasure's radius.
    radius = {"treasure": "radius", "or": 150}
    for action, steps in [
            ("bell", [fx("wave", color="PALE_GOLD", radius=radius, dur=0.6), fx("wave", color="GOLD", radius=dict(radius, times=0.7), dur=0.45),
                      sound("bell")]),
            ("pagoda", [fx("pagoda", at="ground", color="BRIGHT_JADE", dur=4.0), sound("forge")]),
            ("mirror", [fx("flash", off=(0, -50), color="#bfe8ff", radius=60, dur=0.4)]),
            ("seal", [fx("seal_slam", color="BRIGHT_JADE", radius=radius, dur=0.7), shake(0.25), sound("break")]),
            ("cauldron", [fx("spiral", at="ground", off=(0, -30), color="QI", dur=1.0), sound("technique")]),
            ("banner", [fx("ring", color="QI", radius=110, dur=0.8), sound("technique")]),
            ("gourd", [fx("ring", color="SOUL", radius=110, dur=0.8), sound("technique")]),
            ("palm", [fx("talisman_wave", off=(0, -50), color="PALE_GOLD", radius=payload("reach", 540), facing=payload("facing", 1), dur=0.6),
                      shake(0.3), sound("breakthrough")])]:
        out.append(row("treasure_used", *steps, when={"action": action}, name=action))
    out += [
        row("wisp_struck", fx("spark", at="point", color="QI", dur=0.25)),
        row("projectile_reflected", fx("spark", at="point", color="#bfe8ff", dur=0.3)),
        row("projectile_absorbed", fx("spark", at="point", color="SOUL", dur=0.3)),
        row("projectile_burst", fx("wave", at="ground", color="#ffd76a", radius="payload.radius", dur=0.4),
            fx("flash", at="ground", off=(0, -30), color="#fff0b0", radius=50, dur=0.25), shake(0.15), sound("break")),
        # Meditation's motes: Qi's (a spring's jade) once the character has Qi, a mortal's breath before.
        row("meditation_tick", fx("motes", off=(0, -10), color=when({"spring": True}, "BRIGHT_JADE", "QI"), dur=1.0),
            when={"@pools.max_qi": {"gt": 0}}, name="qi"),
        row("meditation_tick", fx("motes", off=(0, -10), color="#f4ecd5", dur=1.0), when={"@active": True}, name="mortal"),
        # A tea, a pill, a draught, a food: what it did rises over the player (WorldShared's handler).
        row("item_used", call("use_parts"), when=ACTIVE),
        row("player_revived", fx("flash", off=(0, -40), color="BRIGHT_JADE", radius=60, dur=0.6)),
        row("projectile_ended", fx("spark", at="point", color="PAPER", dur=0.15)),
        row("dodged", fx("dust", dur=0.35), sound("dodge")),
        row("node_gathered", fx("motes", at="object", color="BRIGHT_JADE", dur=0.8), sound("pickup")),
        row("loot_picked", sound("coin"), when={"coins": {"gt": 0}}, name="coins"),
        row("loot_picked", sound("pickup"), name="item"),
        row("emote_played", fx("text", off=(0, -150), text={"first": [{"field_of": "emotes", "id": "payload.emote", "field": "text"}, "..."]},
                               color="PAPER", size=20, dur={"field_of": "emotes", "id": "payload.emote", "field": "seconds", "or": 1.8})),
        # An artifact's spirit speaking to its owner (the top-down room; the side view has the player say it).
        row("artifact_spirit_spoke", fx("text", off=(0, -110), text="payload.line", color="PAPER", size=17, dur=3.0), when=ACTIVE),
    ]
    return out


# ------------------------------------------------------------------ checks
def emitted_events():
    """Every event name the scripts emit by name (a line that calls emit or emit_event with it quoted)."""
    names = set()
    emit = re.compile(r"\bemit(?:_event)?\(")
    quoted = re.compile(r'"([a-z0-9_]+)"')
    for base, _dirs, files in os.walk(os.path.join(ROOT, "scripts")):
        for f in files:
            if not f.endswith(".gd"):
                continue
            with open(os.path.join(base, f), encoding="utf-8") as fh:
                for line in fh:
                    if emit.search(line):
                        names.update(quoted.findall(line))
    return names


def _keys(node, out):
    """The string keys a text source names ({"key": ...}), anywhere in a step."""
    if isinstance(node, dict):
        if "key" in node:
            out.append(node["key"])
        for v in node.values():
            _keys(v, out)
    elif isinstance(node, list):
        for v in node:
            _keys(v, out)
    return out


def problems(rows):
    errs = []
    events = set(read("event_contract")["events"]) | emitted_events()
    sfx = set(read("audio")["sfx"])
    with open(os.path.join(DATA, "strings", "en.json"), encoding="utf-8") as f:
        strings = json.load(f)["strings"]
    seen = {}
    for r in rows:
        rid = r["id"]
        if r["to"] not in TO:
            errs.append(f"{rid}: played by {r['to']}, not one of {TO}")
        if r["event"] not in events:
            errs.append(f"{rid}: {r['event']} is no event the game emits")
        key = (r["to"], r["event"])
        if seen.get(key) == "open":
            errs.append(f"{rid}: follows a row of {r['event']} with no `when`, so it never plays")
        seen[key] = "when" if r.get("when") else "open"
        if not r["do"]:
            errs.append(f"{rid}: does nothing")
        for s in r["do"]:
            kinds = [k for k in STEPS if k in s]
            if len(kinds) != 1:
                errs.append(f"{rid}: a step is one of {STEPS} ({s})")
            if "fx" in s and s.get("at", "feet") not in ANCHORS:
                errs.append(f"{rid}: {s['fx']} at {s['at']}, not one of {ANCHORS}")
            if "fx" in s and s.get("flip", "side") not in FLIPS:
                errs.append(f"{rid}: {s['fx']} flipped by {s['flip']}, not one of {FLIPS}")
            if "sound" in s and s["sound"] not in sfx:
                errs.append(f"{rid}: sound {s['sound']} is not in data/audio.json")
            for k in _keys(s, []):
                if k not in strings:
                    errs.append(f"{rid}: string key {k} is not in data/strings/en.json")
    return errs


NOTE = ("Built by tools/data/cues.py; never edit by hand. Decision 45 (E6): each event's effects, sounds and shakes as "
        "rows, a row a line (docs/architecture/cues.md).")


def text(rows):
    """The table as the game reads it (a list table: `entries`, each with its id), a row a line so a diff reads as rows."""
    lines = ["  " + json.dumps(r, ensure_ascii=False) for r in rows]
    return ('{\n "schema_version": %d,\n "_note": %s,\n "entries": [\n' % (SCHEMA_VERSION, json.dumps(NOTE, ensure_ascii=False))
            + ",\n".join(lines) + "\n ]\n}\n")


def build():
    rows = world()
    ids = [r["id"] for r in rows]
    fail("cues", problems(rows) + [f"{i}: its id twice" for i in sorted({i for i in ids if ids.count(i) > 1})])
    emit(os.path.join(DATA, "cues.json"), text(rows))
    return f"{len(rows)} rows for {len({r['event'] for r in rows})} events"


if __name__ == "__main__":
    raise SystemExit(run_cli(build))
