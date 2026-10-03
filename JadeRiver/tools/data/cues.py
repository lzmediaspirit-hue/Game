"""Decision 45, phase 2 (E6, audit 45 §6.6): the cue table, data/cues.json (docs/architecture/cues.md).

    python3 tools/data/cues.py            # write it (build_data.py runs it too)
    python3 tools/data/cues.py --check    # fail unless the file is current (tools/data/README.md)

How the game answers an event on screen and in the ears, one row an answer: an event, who plays the row (`to`), when
it holds (`when`) and what it does, in order (`do`): an effect of the effects layer, a sound of the sound bank, a
shake, a thing's hit flash, or a named handler for the few answers that are code. The world views play the rows `to`
"world" (WorldShared.play, for the top-down room and the side view alike). The HUD plays the rows `to` "hud" (S6:
HudNotices, the HUD half of E6): a line in its log or a toast. The reading is Cues (scripts/presentation/cues.gd).

Of an event's rows for one player the first whose `when` holds plays, as a match arm did. Sounds are the sound bank's
ids (data/audio.json), never copies; text is a string key or a data name (MomentRules.text, as moments.json's), and
a key's arguments may be the numbers and words of Cues.arg (the HUD's).

The build checks each row's shape, that its event is one the game emits (the event contract, or an emit of that name
in scripts/), that its sounds are in data/audio.json and that its string keys are in data/strings/en.json. The game's
side (FxLayer's kinds, WorldShared's anchors and handlers, UiKit's colour tokens, the HUD's code arms) is checked by
tests/cue_tests.gd, which also plays every row.
"""
import json
import os
import re

from common import DATA, ROOT, SCHEMA_VERSION, emit, fail, read, run_cli

# ------------------------------------------------------------------ the vocabulary
TO = ["world", "hud"]                             # who plays a row: WorldShared.play, HudNotices.play
ANCHORS = ["feet", "ground", "point", "object", "foe"]
FLIPS = ["side"]                                  # an offset's x turned by the payload's side (a wall kicked off)
STEPS = ["fx", "sound", "shake", "hit_flash", "call", "log", "toast"]
STEPS_OF = {"world": ["fx", "sound", "shake", "hit_flash", "call"], "hud": ["log", "toast"]}
TOAST_STYLES = ["unlock", "gold", "quest", "danger"]   # the HUD's toast kinds (HudTopStack colours them)
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


def tx(key, *args, plural=None, suffix=None):
    """A string key, formatted with its arguments (text sources). `plural`: the count that picks the key's "_one" twin
    (Tx.plural); `suffix`: a value the key ends in ("ui.relations.align_" and the payload's word)."""
    s = {"key": key, "args": list(args)} if args else {"key": key}
    if plural is not None:
        s["plural"] = plural
    if suffix is not None:
        s["suffix"] = suffix
    return s


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


# ------------------------------------------------------------------ the HUD's notices (HudNotices.play, S6)
# A HUD row says an event in the log, a toast, or both:
#   {"log": text, "color": token, "always": true?}   a line of the log ("always": shown before the log is revealed);
#   {"toast": text, "style": one of TOAST_STYLES, "sub": text?}   a toast at the top centre, with its second line.
def log(text, color, always=False):
    s = {"log": text, "color": color}
    if always:
        s["always"] = True
    return s


def toast(text, style, sub=None):
    s = {"toast": text, "style": style}
    if sub is not None:
        s["sub"] = sub
    return s


def hrow(event, *do, when=None, name=None):
    return row(event, *do, when=when, name=name, to="hud")


# A payload value as an argument, with the default its absence takes ("payload.<key>" leaves "" out).
def p(key, default=None):
    return "payload." + key if default is None else payload(key, default)


def i(key, default=None, times=None):
    """A whole number (int); with `times`, of the product (int(float(v) * times))."""
    s = {"int": p(key, default)}
    if times is not None:
        s["times"] = times
    return s


def f(key, default=None):
    return {"float": p(key, default)}


def item(key="item"):
    return {"item": p(key)}


def name(table, key):
    return name_of(table, p(key))


def field(table, key, fld):
    return {"field_of": table, "id": p(key), "field": fld}


def pet(key="pet"):
    return {"pet_name": p(key)}


def span(key, default=None, times=None):
    s = {"span": p(key, default)}
    if times is not None:
        s["times"] = times
    return s


def ui(prefix, key, default=None):
    """The string of key `prefix` + the payload's value (Tx.t("ui.relations.align_" + word))."""
    return tx(prefix, suffix=p(key, default))


def join(*parts):
    return {"join": list(parts)}


SHOWN_LOG = {"@revealed": "hud:system_log"}       # the log is the player's (hud.shown("system_log"))
NOT_EMPTY = {"not": ""}


def hud():
    A = ACTIVE

    def when_a(**kw):
        return dict(A, **kw)

    out = [
        hrow("currency_changed", log(tx("hud.currency_gained", i("delta"), ui("currency.", "currency")), "PALE_GOLD"),
             when=dict(SHOWN_LOG, delta={"gt": 0}, source={"not": "sell"})),
        # What the hand-in took from the bag, under the quest's name: "Gave 5 Willow Moss".
        hrow("quest_completed", toast(join(tx("hud.completed"), p("name")), "quest", sub=tx("hud.gave", p("gave"))), when={"gave": NOT_EMPTY}, name="gave"),
        hrow("quest_completed", toast(join(tx("hud.completed"), p("name")), "quest")),
        hrow("bottleneck_reached", toast(tx("hud.bottleneck_reached_see_the_cultivation"), "gold"), when={"major": True}, name="major"),
        hrow("bottleneck_reached", toast(tx("hud.bottleneck_tap_cultivate_to_break"), "gold")),
        hrow("breakthrough_failed", log(join(tx("hud.breakthrough_failed"), ui("failure.", "failure_id")), "RED_TEXT")),
        hrow("achievement_unlocked", toast(join(tx("hud.achievement"), p("name")), "gold")),
        hrow("talisman_crafted", log(tx("hud.talisman_spoiled"), "MIST"), when={"spoiled": True}),
        hrow("talisman_used", log(tx("hud.talisman_used", item()), "PALE_GOLD"), when={"kind": "movement"}),
        hrow("relic_restored", toast(tx("hud.relic_restored", item()), "gold")),
        hrow("natal_grew", log(tx("hud.natal_grew", item(), i("level", 0)), "GOLD"), when={"level": {"gt": 0}}),
        hrow("natal_broken", toast(tx("hud.natal_broken", item()), "danger")),
        hrow("item_blooded", log(tx("hud.item_blooded", item()), "MIST")),
        hrow("loadout_swapped", log(tx("hud.loadout_swapped", item("weapon")), "PALE_GOLD")),
        hrow("sword_released", log(tx("hud.sword_swarm", i("swarm"), plural=i("swarm")), "PALE_GOLD"), when={"swarm": {"gt": 0}}, name="swarm"),
        hrow("sword_released", log(tx("hud.sword_released"), "PALE_GOLD")),
        hrow("sword_returned", log(tx("hud.swarm_returned"), "MIST"), when={"reason": {"not": "recalled"}, "swarm": True}, name="swarm"),
        hrow("sword_returned", log(tx("hud.sword_returned"), "MIST"), when={"reason": {"not": "recalled"}}),
        hrow("path_changed", log(tx("hud.path_blood_on"), "RED_TEXT"), when=when_a(on=True), name="on"),
        hrow("path_changed", log(tx("hud.path_blood_off"), "RED_TEXT"), when=A),
        hrow("illusion_cast", log(tx("hud.illusion_cast"), "SOUL_TEXT"), when=A),
        hrow("illusion_broken", log(tx("hud.illusion_broken"), "MIST"), when=when_a(reason=["struck", "time"])),
        hrow("soul_searched", log(tx("hud.soul_searched", field("codex", "memory", "title")), "SOUL_TEXT"), when=when_a(memory=NOT_EMPTY), name="memory"),
        hrow("soul_searched", log(tx("hud.soul_searched_none"), "SOUL_TEXT"), when=A),
        hrow("melody_changed", log(tx("hud.melody_spent"), "MIST"), when=when_a(on=False, reason="composure"), name="spent"),
        hrow("melody_changed", log(tx("hud.melody_broken"), "MIST"), when=when_a(on=False, reason="broken"), name="broken"),
        hrow("sword_intent_changed", log(tx("hud.sword_intent_full"), "GOLD"), when={"stacks": {"ge": 10}}),
        hrow("artifact_detonated", log(tx("hud.detonated", item(), i("targets", 0)), "RED_TEXT")),
        hrow("items_salvaged", log(tx("hud.salvaged", {"count": p("items")}, plural={"count": p("items")}), "PALE_GOLD")),
        hrow("enhancement_inherited", log(tx("hud.inherited", item(), i("levels", 0)), "PALE_GOLD")),
        hrow("path_above_found", toast(tx("hud.path_above", i("found", 1), i("total", 1)), "gold")),
        hrow("mail_received", log(tx("hud.a_letter_arrived"), "PALE_GOLD"), when={"@unlocked": "mail"}),
        hrow("bag_full", log(tx("hud.your_gourd_is_full"), "RED_TEXT")),
        hrow("system_log", log(p("text"), "PAPER")),
    ]
    out += [hrow(ev, toast(tx("hud.appears", field("enemies", "def", "name")), "danger")) for ev in ["field_boss_spawned", "elite_spawned"]]
    out += [
        hrow("injury_added", log(tx("hud.injury_severity", {"title": p("kind")}, i("severity")), "RED_TEXT")),
        hrow("aptitude_revealed", toast(tx("hud.aptitude_revealed", {"title": p("aptitude")}), "gold")),
        hrow("pets_bred", toast(tx("hud.pets_bred", span("hours", 24.0, times=3600.0)), "gold")),
        hrow("treasure_planted", toast(tx("hud.treasure_planted"), "gold")),
        hrow("treasure_harvested", toast(tx("hud.treasure_harvested", item()), "gold")),
        hrow("natural_treasure_used", toast(ui("hud.treasure_used.", "treasure"), "gold")),
        # Gap report G1: the ledger.
        hrow("merit_changed", log(tx("hud.merit_gained", i("delta")), "PALE_GOLD"), when={"delta": {"gt": 0}}),
        hrow("sin_changed", log(tx("hud.sin_gained", i("delta")), "RED_TEXT"), when={"delta": {"gt": 0}}),
        # S49: alignment, Fame, the people's hearts, grudges and bounties.
        hrow("alignment_changed", toast(tx("hud.alignment_now", ui("ui.relations.align_", "word")), "gold"), when={"word_changed": True}),
        hrow("fame_changed", toast(tx("hud.fame_tier", ui("ui.relations.fame_", "tier")), "unlock"), when={"tier_up": True}, name="tier"),
        hrow("fame_changed", log(tx("hud.fame_lost", {"neg": p("delta")}), "MIST"), when={"delta": {"lt": 0}}, name="lost"),
        hrow("fame_changed", log(tx("hud.fame_gained", i("delta")), "PALE_GOLD"), when={"delta": {"gt": 0}}, name="gained"),
        hrow("affinity_changed", toast(tx("hud.heart_up", name("npcs", "npc"), i("hearts"), plural=i("hearts")), "gold"), when={"heart_up": True}),
        hrow("bond_formed", toast(tx("hud.bond_", name("npcs", "npc"), suffix=p("kind")), "unlock")),
        hrow("grudge_changed", toast(tx("hud.grudge_hunted", name("factions", "faction")), "danger"), when={"hunted": True, "delta": {"gt": 0}}, name="hunted"),
        hrow("grudge_changed", log(tx("hud.grudge_settled", name("factions", "faction")), "BRIGHT_JADE"), when={"value": 0}, name="settled"),
        hrow("grudge_changed", log(tx("hud.grudge_rises", name("factions", "faction")), "RED_TEXT"), when={"delta": {"gt": 0}}, name="rises"),
        hrow("hunter_dispatched", toast(tx("hud.hunter_found_you", name("enemies", "enemy")), "danger")),
        hrow("bounty_taken", log(tx("hud.bounty_taken", name("enemies", "bounty"), name("rooms", "room")), "PALE_GOLD")),
        hrow("bounty_claimed", toast(tx("hud.bounty_claimed", name("enemies", "bounty"), i("reward")), "gold")),
        hrow("foe_judged", log(tx("hud.foe_spared", name("enemies", "def")), "MIST"), when={"spared": True}, name="spared"),
        hrow("foe_judged", log(tx("hud.foe_killed", name("enemies", "def")), "MIST")),
        hrow("treasure_claimed", toast(tx("hud.treasure_claimed", item()), "gold")),
        # S28 v1.2 the Hollow Tide at full: control lost for a moment, allies turned.
        hrow("hollow_seizure", toast(tx("hud.hollow_seizure"), "quest", sub=tx("hud.hollow_seizure_turned", i("turned", 0))),
             when=when_a(turned={"gt": 0}), name="turned"),
        hrow("hollow_seizure", toast(tx("hud.hollow_seizure"), "quest", sub=tx("hud.hollow_seizure_sub")), when=A),
        # S50 Keeping Post: a post taken, a craft level, a pouch sewn, a leaf, a rite, incense burned.
        hrow("post_taken", log(tx("hud.post_taken", tx("hud.vigil")), "BRIGHT_JADE"), when=when_a(craft="vigil"), name="vigil"),
        hrow("post_taken", log(tx("hud.post_taken", field("posts", "craft", "short")), "BRIGHT_JADE"), when=A),
        hrow("craft_leveled", toast(tx("hud.craft_level", field("posts", "craft", "name"), i("level")), "gold", sub=tx("hud.craft_level_sub")), when=A),
        hrow("pouch_sewn", log(tx("hud.pouch_sewn", {"fmt": p("cap", 0.0)}), "PALE_GOLD")),
        hrow("leaf_found", toast(tx("hud.leaf_tier", name("enemies", "enemy"), i("tier")), "gold", sub=tx("hud.leaf_sub")), when={"new_tier": True}),
        hrow("rite_held", toast(tx("hud.rite_held", i("wave")), "gold", sub=tx("hud.rite_wisps", i("wisps"), plural=i("wisps"))), when=A),
        hrow("incense_burned", log(tx("hud.incense_burned", span("hours", 0.0, times=3600.0)), "PALE_GOLD")),
        # S28 v1.2 Presence and the Sphere: held or let go, a new level, two meeting.
        hrow("presence_toggled", log(tx("hud.presence_on", i("level", 1)), "PALE_GOLD"), when=when_a(on=True), name="on"),
        hrow("presence_toggled", log(tx("hud.presence_soul"), "RED_TEXT"), when=when_a(reason="soul"), name="soul"),
        hrow("presence_toggled", log(tx("hud.presence_off"), "MIST"), when=A),
        hrow("presence_leveled", toast(tx("hud.presence_level", i("level")), "gold", sub=tx("hud.presence_level_sub")), when=A),
        hrow("presence_clash", log(tx("hud.presence_clash_", p("name"), suffix=p("winner", "even")), "GOLD"), when=when_a(winner="you"), name="won"),
        hrow("presence_clash", log(tx("hud.presence_clash_", p("name"), suffix=p("winner", "even")), "RED_TEXT"), when=A),
        hrow("sphere_toggled", log(tx("hud.sphere_domain"), "PALE_GOLD"), when=when_a(on=True, domain=True), name="domain"),
        hrow("sphere_toggled", log(tx("hud.sphere_on", ui("hud.el_", "element", "none")), "PALE_GOLD"), when=when_a(on=True), name="on"),
        hrow("sphere_toggled", toast(tx("hud.sphere_broken"), "danger", sub=tx("hud.sphere_broken_sub")), when=when_a(reason="broken"), name="broken"),
        hrow("sphere_toggled", log(tx("hud.sphere_qi"), "RED_TEXT"), when=when_a(reason="qi"), name="qi"),
        hrow("sphere_toggled", log(tx("hud.sphere_off"), "MIST"), when=A),
        hrow("sphere_clash", toast(tx("hud.sphere_clash_won", p("name")), "gold", sub=tx("hud.sphere_clash_won_sub")), when=when_a(winner="you")),
        hrow("presence_clash_ended", log(tx("hud.presence_clash_end"), "MIST"), when=A),
        # v1.2 Phase D: the Copperjaw swarm.
        hrow("swarm_released", log(tx("hud.swarm_released", i("pop", 0), plural=i("pop", 0)), "PALE_GOLD"), when=A),
        hrow("swarm_returned", log(tx("hud.swarm_returned"), "MIST"), when=A),
        hrow("swarm_queen", toast(tx("hud.swarm_queen"), "gold", sub=tx("hud.swarm_queen_sub")), when=A),
        hrow("swarm_fed", log(tx("hud.swarm_fed", span("food", 0, times=3600.0)), "MIST"), when=A),
        # S43 rule 15: the rooftop thief and the Cloud Steps.
        hrow("chase_started", toast(tx("hud.chase_started"), "quest", sub=tx("hud.chase_hint")), when=A),
        hrow("thief_caught", toast(tx("hud.thief_caught", f("seconds", 0.0)), "gold"), when=A),
        hrow("thief_escaped", toast(tx("hud.thief_escaped"), "quest"), when=A),
        hrow("route_started", toast(tx("hud.route_started"), "quest", sub=tx("hud.route_hint", i("limit", 60), plural=i("limit", 60))), when=A),
        hrow("route_finished", toast(tx("hud.route_failed"), "quest"), when=when_a(finished=False), name="failed"),
        hrow("route_finished", toast(tx("hud.route_finished", f("seconds"), i("rank"), i("of")), "gold", sub=tx("hud.route_medal_", suffix=p("medal"))),
             when=when_a(medal=NOT_EMPTY), name="medal"),
        hrow("route_finished", toast(tx("hud.route_finished", f("seconds"), i("rank"), i("of")), "quest", sub=tx("hud.route_best", f("best"))), when=A),
        hrow("gathering_trial_ranked", toast(tx("hud.trial_ranked", i("rank"), i("of"), i("points"), plural=i("points")), "gold"),
             when={"rank": {"le": 3}}, name="podium"),
        hrow("gathering_trial_ranked", toast(tx("hud.trial_ranked", i("rank"), i("of"), i("points"), plural=i("points")), "quest")),
        hrow("rift_opened", toast(tx("hud.rift_opened", i("level")), "danger", sub=tx("hud.rift_hint"))),
        hrow("tower_floor_cleared", toast(tx("hud.tower_cleared", i("floor")), "gold", sub=tx("hud.tower_first")), when=when_a(first=True), name="first"),
        hrow("tower_floor_cleared", toast(tx("hud.tower_cleared", i("floor")), "gold"), when=A),
        hrow("tower_swept", log(tx("hud.tower_swept", i("floors"), plural=i("floors")), "PALE_GOLD"), when=A),
        hrow("activity_chest_ready", toast(tx("hud.activity_ready", i("points"), plural=i("points")), "gold", sub=tx("hud.activity_ready_hint"))),
        hrow("activity_chest_claimed", log(tx("hud.activity_claimed", i("points"), plural=i("points")), "PALE_GOLD")),
        # Decision 27: a collection's seal.
        hrow("collection_seal_ready", toast(tx("hud.seal_ready", ui("ui.codex.page_", "page"), tx("ui.codex.seal_", suffix=i("seal"))), "gold",
                                            sub=tx("hud.seal_ready_hint"))),
        hrow("favour_changed", toast(tx("hud.favour_tier", ui("ui.county.tier_", "tier")), "gold"), when=when_a(tier_up=True), name="tier"),
        hrow("favour_changed", log(tx("hud.favour_up", i("delta")), "PALE_GOLD"), when=when_a(delta={"gt": 0}), name="up"),
        hrow("relief_donated", log(tx("hud.relief_given", {"fmt": p("silver")}), "PALE_GOLD"), when=A),
        # S49 territory: the spirit-stone mines (account level: every character hears of them).
        hrow("mine_claimed", toast(tx("hud.mine_claimed", name("territory", "mine")), "gold", sub=tx("hud.mine_claimed_sub"))),
        hrow("mine_defended", toast(tx("hud.mine_held_you", name("territory", "mine")), "gold"), when={"by": "you"}, name="you"),
        hrow("mine_defended", toast(tx("hud.mine_held_guards", name("territory", "mine")), "gold")),
        hrow("mine_collected", log(tx("hud.mine_collected", i("stones"), name("territory", "mine"), plural=i("stones")), "PALE_GOLD")),
        hrow("pet_commanded", log(tx("hud.pet_commanded", ui("hud.pet_cmd_", "command")), "PALE_GOLD"), when=A),
        hrow("guqin_played", log(tx("hud.guqin_calm", {"round": p("bonus"), "times": 100.0}), "BRIGHT_JADE"), when=A),
        hrow("chess_solved", log(tx("hud.chess_right"), "PALE_GOLD"), when=when_a(right=True), name="right"),
        hrow("chess_solved", log(tx("hud.chess_wrong"), "MIST"), when=A),
        hrow("auto_hunt_changed", log(tx("hud.auto_hunt_on"), "BRIGHT_JADE"), when=when_a(on=True), name="on"),
        hrow("auto_hunt_changed", log(tx("hud.auto_hunt_off"), "MIST"), when=when_a(reason=["off", "path"]), name="off"),
        hrow("auto_hunt_changed", log(tx("sim.world.auto_hunt_", suffix=p("reason")), "MIST"), when=A),
        # Decision 43: a walk to a place names the place ("the Storehouse"), else the room.
        hrow("auto_path_started", log(tx("hud.auto_path_to", p("name")), "PALE_GOLD"), when=when_a(name=NOT_EMPTY), name="place"),
        hrow("auto_path_started", log(tx("hud.auto_path_to", name("rooms", "target")), "PALE_GOLD"), when=A),
        hrow("auto_path_ended", log(tx("hud.auto_path_", suffix=p("reason", "arrived")), "PALE_GOLD"), when=when_a(reason="arrived"), name="arrived"),
        hrow("auto_path_ended", log(tx("hud.auto_path_", suffix=p("reason", "arrived")), "MIST"), when=when_a(reason={"not": "cancelled"})),
        hrow("heavenly_phenomenon", log(tx("hud.phenomenon_", suffix=p("kind", "cloud")), "PALE_GOLD"), when=A),
        hrow("draught_expired", toast(tx("hud.draught_expired", item()), "danger")),
        # The furnace, the recipes and the guilds.
        hrow("flame_absorbed", toast(tx("hud.flame_absorbed", item("flame")), "gold")),
        hrow("recipe_page_found", toast(tx("hud.recipe_page", name("recipes", "recipe"), i("held"), i("total")), "gold")),
        hrow("recipe_deduced", toast(tx("hud.recipe_deduced", name("recipes", "recipe")), "unlock"), when={"success": True}, name="deduced"),
        hrow("recipe_deduced", toast(tx("hud.recipe_not_deduced", name("recipes", "recipe")), "danger")),
        hrow("guild_exam_started", toast(tx("hud.exam_started", span("time_s", 0)), "gold")),
        hrow("guild_exam_failed", toast(tx("hud.exam_failed"), "danger")),
        hrow("commission_completed", log(join(tx("hud.commission_paid", i("paid", 0), plural=i("paid", 0)), " ", tx("hud.commission_capped")), "PALE_GOLD"),
             when={"capped": True}, name="capped"),
        hrow("commission_completed", log(tx("hud.commission_paid", i("paid", 0), plural=i("paid", 0)), "PALE_GOLD")),
        hrow("pill_soul_flight", log(tx("hud.soul_escaped"), "MIST"), when={"caught": False}),
        hrow("furnace_blast", toast(tx("hud.furnace_blast", i("durability", 0)), "danger")),
        hrow("debt_called", toast(tx("hud.debt_", suffix=p("debt")), "quest")),
        # A room event: flawless, a wave's words, failed.
        hrow("room_event_flawless", toast(tx("hud.flawless"), "gold")),
        hrow("room_event_wave", log(p("text"), "PALE_GOLD"), when={"text": NOT_EMPTY}),
        hrow("room_event_failed", toast(tx("hud.event_failed.", suffix=p("reason")), "danger"), when={"reason": NOT_EMPTY}),
        # S48: the body ladder, physiques, the core, fates, inner arts, stances, vows.
        hrow("body_trial_passed", toast(tx("hud.body_trial_passed", name("body_tiers", "tier"), item("bath")), "gold")),
        hrow("physique_awakened", toast(tx("hud.physique_awakened", name("physiques", "physique")), "unlock")),
        hrow("core_graded", toast(tx("hud.core_graded", i("grade")), "gold")),
        hrow("fate_chosen", toast(tx("hud.fate_chosen", name("fates", "card")), "gold")),
        hrow("qi_deviation", toast(tx("hud.qi_deviation"), "danger", sub=tx("hud.qi_deviation_sub"))),
        hrow("inner_art_learned", toast(tx("hud.inner_art_learned", name("inner_arts", "art")), "unlock")),
        hrow("inner_art_equipped", log(tx("hud.inner_art_worn", name("inner_arts", "art")), "PALE_GOLD"), when={"art": NOT_EMPTY}),
        hrow("stance_changed", log(tx("hud.stance_on", name("stances", "stance")), "PALE_GOLD"), when={"stance": NOT_EMPTY}, name="on"),
        hrow("stance_changed", log(tx("hud.stance_off"), "PALE_GOLD")),
        hrow("vow_taken", log(tx("hud.vow_taken", name("vows", "vow")), "PALE_GOLD")),
        hrow("vow_broken", toast(tx("hud.vow_broken", name("vows", "vow")), "danger")),
        hrow("false_realm_changed", log(tx("hud.false_realm", {"realm": p("realm")}), "MIST"), when={"realm": NOT_EMPTY}, name="false"),
        hrow("false_realm_changed", log(tx("hud.true_realm"), "MIST")),
        hrow("epiphany", toast(tx("hud.epiphany"), "gold", sub=tx("hud.epiphany_mastery", name("techniques", "technique"))),
             when={"technique": NOT_EMPTY}, name="mastery"),
        hrow("epiphany", toast(tx("hud.epiphany"), "gold", sub=tx("hud.epiphany_sub"))),
        hrow("boss_phase", toast(tx("hud.self_detonate"), "danger", sub=tx("hud.self_detonate_sub")), when={"action": "self_detonate"}),
        hrow("soul_escaped", toast(tx("hud.soul_escaped_death"), "danger")),
        hrow("combo_landed", log(tx("hud.combo", name("techniques", "first"), name("techniques", "second")), "GOLD")),
        # Gap report G2: treasures and talismans.
        hrow("beast_captured", log(tx("hud.beast_captured", field("enemies", "def", "name")), "PALE_GOLD")),
        hrow("pill_soul_awakened", toast(tx("hud.pill_soul", ui("hud.pill_soul_effect.", "effect")), "gold")),
        hrow("codex_entry_unlocked", log(join(tx("hud.codex"), field("codex", "entry", "title")), "PALE_GOLD")),
        hrow("teleport_discovered", toast(tx("hud.teleport_stone_attuned"), "gold")),
        hrow("hidden_portal_revealed", toast(tx("hud.a_hidden_path_opens"), "gold")),
        # S45 herbs and the garden.
        hrow("herb_ripening", log(tx("hud.herb_ripening", item()), "GOLD")),
        hrow("herb_harvested", log(tx("hud.herb_perfect", item(), i("age"), plural=i("age")), "GOLD"), when={"perfect": True}),
        hrow("seed_found", toast(tx("hud.seed_found", item("seed")), "gold")),
        hrow("herb_planted", log(tx("hud.herb_planted", item("herb")), "BRIGHT_JADE")),
        hrow("bed_watered", log(tx("hud.bed_watered", i("progress", times=100.0)), "BRIGHT_JADE")),
        hrow("bed_enriched", toast(tx("hud.bed_enriched", ui("ui.garden.grade_", "grade")), "gold")),
        hrow("herb_aged", toast(tx("hud.herb_aged", item("herb"), i("age"), plural=i("age")), "gold")),
        hrow("spring_bottled", log(tx("hud.spring_bottled", i("left")), "BRIGHT_JADE")),
        # Spirit animals.
        hrow("pet_wounded", toast(tx("hud.pet_wounded", pet()), "danger", sub=tx("hud.pet_wounded_sub"))),
        hrow("pet_healed", log(tx("hud.pet_healed", pet()), "BRIGHT_JADE")),
        hrow("bloodline_awakened", toast(tx("hud.bloodline_form", pet(), p("name")), "unlock", sub=tx("hud.bloodline_form_sub")),
             when={"step": {"ge": 2}}, name="form"),
        hrow("bloodline_awakened", toast(tx("hud.bloodline_skill", pet(), p("name")), "unlock", sub=tx("hud.bloodline_skill_sub"))),
        hrow("contract_offered", toast(tx("hud.contract_offered", pet()), "unlock", sub=tx("hud.contract_offered_sub"))),
        hrow("pet_skill_cast", log(tx("hud.pet_skill_cast", pet(), p("skill")), "PALE_GOLD")),
        hrow("beast_suppressed", log(tx("hud.beast_suppressed", pet(), name("enemies", "def")), "MIST")),
        hrow("egg_infused", log(tx("hud.egg_infused_", suffix=p("kind", "blood")), "BRIGHT_JADE")),
        hrow("party_changed", log(tx("hud.party_changed", i("count", 1), plural=i("count", 1)), "MIST")),
        hrow("pet_skill_learned", log(tx("hud.pet_skill_replaced", pet(), name("pet_skill_books", "skill"), name("pet_skill_books", "replaced")), "PALE_GOLD"),
             when={"replaced": NOT_EMPTY}, name="replaced"),
        hrow("pet_skill_learned", log(tx("hud.pet_skill_learned", pet(), name("pet_skill_books", "skill")), "BRIGHT_JADE")),
        hrow("pets_fused", toast(tx("hud.pets_fused", pet("keep")), "gold",
                                 sub=tx("hud.pets_fused_sub", {"count": p("traits")}, {"count": p("skills")}, i("purity", 0)))),
        hrow("pet_breakthrough", log(tx("hud.pet_breakthrough_ok", pet()), "BRIGHT_JADE"), when={"success": True}, name="ok"),
        hrow("pet_breakthrough", toast(tx("hud.pet_breakthrough_fail", pet()), "danger", sub=tx("hud.pet_breakthrough_heart")), when={"lost": "heart"}, name="heart"),
        hrow("pet_breakthrough", toast(tx("hud.pet_breakthrough_fail", pet()), "danger", sub=tx("hud.pet_breakthrough_wound"))),
        hrow("pet_fed", log(tx("hud.trough_fed", pet()), "MIST"), when={"trough": True}),
        hrow("arena_battle", toast(tx("hud.arena_won", i("rank", 11)), "gold"), when={"won": True}, name="won"),
        hrow("arena_battle", log(tx("hud.arena_lost"), "MIST")),
        hrow("arena_rewarded", toast(tx("hud.arena_rewarded", i("rank", 11), i("spirit_stone", 0), plural=i("spirit_stone", 0)), "gold")),
        hrow("beast_trial_result", toast(tx("hud.trial_won"), "gold", sub=item()), when={"won": True}, name="won"),
        hrow("beast_trial_result", toast(tx("hud.trial_lost"), "danger")),
        hrow("pet_swapped", log(tx("hud.pet_swapped", pet()), "BRIGHT_JADE")),
        # The beast king, its nest and the Beast Tide.
        hrow("beast_king_spawned", toast(tx("hud.beast_king_spawned", name("enemies", "king")), "danger", sub=tx("hud.beast_king_spawned_sub"))),
        hrow("king_nest_opened", toast(tx("hud.king_nest_opened"), "gold", sub=tx("hud.king_nest_opened_sub", span("minutes", 30, times=60.0)))),
        hrow("beast_tide_started", toast(tx("hud.beast_tide_started"), "danger",
                                         sub=tx("hud.beast_tide_started_sub", i("duration", 90), plural=i("duration", 90)))),
        hrow("beast_tide_result", toast(tx("hud.beast_tide_won"), "gold", sub=tx("hud.beast_tide_won_sub")), when={"won": True}),
        hrow("pet_gear_changed", log(tx("hud.pet_gear", pet(), item()), "MIST"), when={"item": NOT_EMPTY}),
        hrow("core_devoured", log(tx("hud.core_devoured", pet(), item(), i("xp")), "BRIGHT_JADE")),
        hrow("cores_sold", log(tx("hud.cores_sold", i("count"), item(), i("stones"), plural=i("stones")), "PALE_GOLD")),
        hrow("beast_cleansed", toast(tx("hud.beast_cleansed", name("enemies", "def")), "gold", sub=tx("hud.beast_cleansed_sub"))),
        hrow("beast_subdued", log(tx("hud.beast_subdued", name("enemies", "def"), span("seconds")), "GOLD")),
        hrow("garden_raided", toast(tx("hud.raid_", item("herb"), suffix=p("kind")), "danger")),
        hrow("rack_started", log(tx("hud.rack_started", i("count"), item("herb"), span("seconds")), "BRIGHT_JADE")),
        hrow("rack_collected", log(tx("hud.rack_collected", i("count"), item("herb"), ui("ui.garden.done_", "kind")), "BRIGHT_JADE")),
        hrow("herb_appraised", toast(tx("hud.herb_fake", item()), "danger"), when={"fake": True}),
        hrow("transplant_result", toast(tx("hud.transplanted", item("herb")), "gold", sub=tx("hud.transplanted_sub")), when={"ok": True}, name="ok"),
        hrow("transplant_result", toast(tx("hud.transplant_died", item("herb")), "danger")),
        hrow("guardian_spawned", toast(tx("hud.guardian", name("enemies", "enemy")), "danger", sub=tx("hud.guardian_sub"))),
        hrow("ambush_sprung", toast(tx("hud.ambush"), "danger", sub=tx("hud.ambush_concealed")), when={"concealed": True}, name="concealed"),
        hrow("ambush_sprung", toast(tx("hud.ambush"), "danger", sub=tx("hud.ambush_sub"))),
        # Cultivation, the sect and the world.
        hrow("meridian_gate_opened", toast(tx("hud.meridian_gate_opened", {"title": p("channel")}), "gold")),
        hrow("stability_changed", log(tx("hud.your_foundation_is", {"lower": p("word")}), "MIST")),
        hrow("overflow_mailed", log(tx("hud.no_room_in_your_gourd"), "PALE_GOLD")),
        hrow("egg_hatched", toast(tx("hud.the_egg_hatched_a", name("pets", "species")), "gold")),
        hrow("bond_changed", log(tx("hud.hearts", pet(), i("value"), plural=i("value")), "RED_TEXT")),
        hrow("defence_warning", toast(tx("hud.raiders_at_the_gates_hold"), "danger")),
        hrow("defence_result", toast(tx("hud.the_raid_is_beaten_back"), "gold"), when={"won": True}, name="won"),
        hrow("defence_result", toast(tx("hud.the_raiders_broke_through"), "danger")),
        hrow("building_upgraded", log(tx("hud.reached_level", name("sect_buildings", "building"), i("level")), "PALE_GOLD")),
        hrow("expedition_returned", log(tx("hud.expedition_to", name("expeditions", "region"), tx("hud.returned_with_spoils")), "PALE_GOLD"),
             when={"success": True}, name="spoils"),
        hrow("expedition_returned", log(tx("hud.expedition_to", name("expeditions", "region"), tx("hud.came_back_empty_handed")), "PALE_GOLD")),
        hrow("reputation_changed", log(tx("hud.reputation", {"title": p("faction")}, i("value")), "MIST")),
        hrow("dismounted", log(tx("hud.dismount_climb"), "MIST"), when={"reason": "climb"}, name="climb"),
        hrow("dismounted", log(tx("hud.dismounted"), "RED_TEXT")),
        # S47 artifacts: bound, a spirit awakening and growing, its skills.
        hrow("item_bound", toast(tx("hud.item_bound", item()), "gold")),
        hrow("binding_interrupted", log(tx("hud.binding_broken"), "RED_TEXT")),
        hrow("artifact_spirit_awakened", toast(tx("hud.spirit_awake", item()), "gold")),
        hrow("artifact_spirit_grew", toast(tx("hud.spirit_grew", item(), i("level", 0)), "gold")),
        hrow("artifact_skill_used", log(tx("hud.awakened_skill", p("skill")), "GOLD"), when={"awakened": True}, name="awakened"),
        hrow("artifact_skill_used", log(tx("hud.spirit_skill", p("skill")), "SOUL_TEXT")),
        hrow("trait_revealed", toast(tx("hud.shows_a_trait", pet(), name("pet_traits", "trait")), "gold")),
        hrow("pet_level_up", log(tx("hud.reached_level", pet(), i("level")), "PALE_GOLD")),
        hrow("pet_retreated", log(tx("hud.your_spirit_animal_retreats_into"), "MIST")),
        hrow("pet_returned", log(tx("hud.your_spirit_animal_is_back"), "MIST")),
        hrow("companion_downed", log(tx("hud.is_down", name("companions", "companion")), "RED_TEXT")),
        hrow("companion_revived", log(tx("hud.is_back_on_their_feet", name("companions", "companion")), "MIST")),
        hrow("building_damaged", toast(tx("hud.raiders_damaged_your_repair_it", name("sect_buildings", "building")), "danger")),
        hrow("zone_ceiling_reached", toast(tx("hud.this_land_can_take_you"), "gold")),
        # The auction house.
        hrow("auction_bid_placed", log(tx("hud.auction_bid_placed", item(), i("bid", 0)), "PALE_GOLD"), when=A),
        hrow("auction_outbid", log(tx("hud.auction_outbid", item()), "MIST"), when=A),
        hrow("auction_won", toast(tx("hud.auction_won", item()), "gold"), when=A),
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
    """The string keys a text source names ({"key": ...}), anywhere in a step; a key with a `suffix` as "<key>*" (one
    of the strings must begin with it)."""
    if isinstance(node, dict):
        if "key" in node:
            out.append(node["key"] + ("*" if "suffix" in node else ""))
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
            elif r["to"] in STEPS_OF and kinds[0] not in STEPS_OF[r["to"]]:
                errs.append(f"{rid}: a {kinds[0]} step is not one the {r['to']} plays ({STEPS_OF[r['to']]})")
            if "log" in s and "color" not in s:
                errs.append(f"{rid}: a log line names its colour")
            if "toast" in s and s.get("style") not in TOAST_STYLES:
                errs.append(f"{rid}: a toast's style is one of {TOAST_STYLES} ({s.get('style')})")
            if "fx" in s and s.get("at", "feet") not in ANCHORS:
                errs.append(f"{rid}: {s['fx']} at {s['at']}, not one of {ANCHORS}")
            if "fx" in s and s.get("flip", "side") not in FLIPS:
                errs.append(f"{rid}: {s['fx']} flipped by {s['flip']}, not one of {FLIPS}")
            if "sound" in s and s["sound"] not in sfx:
                errs.append(f"{rid}: sound {s['sound']} is not in data/audio.json")
            for k in _keys(s, []):
                if k.endswith("*") and not any(sk.startswith(k[:-1]) for sk in strings):
                    errs.append(f"{rid}: no string key begins with {k[:-1]}")
                elif not k.endswith("*") and k not in strings:
                    errs.append(f"{rid}: string key {k} is not in data/strings/en.json")
    return errs


NOTE = ("Built by tools/data/cues.py; never edit by hand. Decision 45 (E6, S6): each event's effects, sounds and shakes, "
        "and the HUD's log lines and toasts, as rows, a row a line (docs/architecture/cues.md).")


def text(rows):
    """The table as the game reads it (a list table: `entries`, each with its id), a row a line so a diff reads as rows."""
    lines = ["  " + json.dumps(r, ensure_ascii=False) for r in rows]
    return ('{\n "schema_version": %d,\n "_note": %s,\n "entries": [\n' % (SCHEMA_VERSION, json.dumps(NOTE, ensure_ascii=False))
            + ",\n".join(lines) + "\n ]\n}\n")


def build():
    rows = world() + hud()
    ids = [r["id"] for r in rows]
    fail("cues", problems(rows) + [f"{i}: its id twice" for i in sorted({i for i in ids if ids.count(i) > 1})])
    emit(os.path.join(DATA, "cues.json"), text(rows))
    return "; ".join(f"{to}: {sum(1 for r in rows if r['to'] == to)} rows for {len({r['event'] for r in rows if r['to'] == to})} events"
                     for to in TO)


if __name__ == "__main__":
    raise SystemExit(run_cli(build))
