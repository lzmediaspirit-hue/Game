"""Decision 43 · the sound pass's tables, one file: data/sound.json (docs/redesign/sound.md).

    python3 tools/data/sound.py            # write it (build_data.py runs it too)
    python3 tools/data/sound.py --check    # fail unless the file is current

The sounds themselves are synthesized by tools/audio (build_audio.py writes data/audio.json, every id's file, level
and length); this table says which of them the game plays when, and how the mix treats them. AudioDirector (the
`Audio` autoload), TopdownSound and SoundBank read it.

- hits: a blow is three sounds played as one: the weapon family's transient, the struck body's material, and the
  family's tail when the hit-stop lets go (combat_feel.json's frames for the blow's weight), with a crit or finisher
  accent, the chain's last blow and a weave cancel; each varied in pitch and level, merged when one swing strikes a
  crowd.
- steps: the top-down floor under the feet (the tile set's paint marks, a prop's top, water), the frames of the walk
  and run cycles where a foot lands (as fractions of the cycle, so new frames keep them), landings by height, and
  the foes' and villagers' quieter steps with the distance falloff.
- foes: each foe's voice for its tell, its body, its death, by race and nature with named exceptions.
- beds: each place's ambient bed (a base loop or two and the layers of the hour), and which rooms take which: by id,
  then by the room's ambience mood, its type, its id's area prefix. Kept here, not in topdown_rooms.py, so the
  living world's edits there never meet these.
- music: the fight (who counts as fighting, how near, when the combat stem comes in and leaves, on the beat), the
  bosses' own themes, the stingers and the events that play them.
- mix: the buses and the Settings slider that drives each, the master limiter, the ducking under stingers, barks and
  scenes, and the voice limit with its priorities.
- life (decision 44): the living world's sounds, which TopdownLife raises as world sounds (the critters and the
  villagers at work), and the player's use of a place; the takes the director plays in turn, and their pitch spread.
  `--check` also proves that every one the code or data/topdown/life.json can raise has a sound (check_life).
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, ROOT, write  # noqa: E402
import combat_feel  # noqa: E402
import topdown_life  # noqa: E402  (decision 44: the work cues, CUES)

# ------------------------------------------------------------------ hits
# Weapon families (weapon_families.json ids) onto the nine sound families of tools/audio/sfx_pass.py.
FAMILY_SOUND = {"fists": "fists", "gauntlets": "fists", "jian": "sword", "short_blade": "sword", "spear": "spear",
                "staff": "spear", "heavy_sabre": "sabre", "fan": "fan", "flute": "flute", "brush": "brush", "bell": "bell",
                "bow": "bow", "none": "fists", "": "fists"}
# A foe's blow on the player: its race's family (claws and jaws strike as fists do; a bandit's blade as a sword).
FOE_FAMILY = {"beast": "fists", "human": "sword", "construct": "sabre", "ghost": "flute", "ashborn": "sabre", "undead": "sabre"}
# Technique elements onto the cast and hit sounds (the elements without their own voice sound as qi).
ELEMENT_SOUND = {"none": "qi", "fire": "fire", "water": "water", "wind": "wind", "thunder": "thunder", "earth": "earth",
                 "metal": "metal", "wood": "wood", "soul": "soul", "space": "space", "time": "time"}

HITS = {
    "family_of": FAMILY_SOUND,
    "foe_family": FOE_FAMILY,
    "element_of": ELEMENT_SOUND,
    "families": {f: {"transient": [f"hit_{f}_a", f"hit_{f}_b"], "tail": f"hit_tail_{f}", "swing": f"swing_{f}"}
                 for f in ("sword", "sabre", "spear", "fan", "brush", "flute", "bell", "bow", "fists")},
    "bodies": {m: [f"hit_on_{m}_a", f"hit_on_{m}_b"] for m in ("flesh", "shell", "wood", "slime")},
    # layer levels against the transient (dB): the body under it, the tail after the hit-stop, an accent over it
    "mix": {"transient_db": 0.0, "body_db": -1.0, "tail_db": -3.0, "accent_db": -1.0, "element_db": -1.0, "player_hurt_db": 0.0},
    # the blow's weight (combat_feel.json) moves the whole hit: lighter blows quieter and a touch higher
    "weight_db": {"light": -3.0, "medium": -1.5, "heavy": 0.0, "finisher": 1.0},
    "weight_pitch": {"light": 1.04, "medium": 1.0, "heavy": 0.96, "finisher": 0.92},
    "hitstop_f": {k: v["hitstop_f"] for k, v in combat_feel.WEIGHTS.items()},
    "crit_hitstop_f": 2,
    "pitch_jitter": 0.035,          # each layer's pitch, ± this share
    "vol_jitter_db": 1.5,           # each layer's level, ± this
    "merge_s": 0.035,               # blows landing within this of one another (a swing through a crowd) sound as one,
    "merge_db": 1.5,                # each one more adding this much, up to
    "merge_max_db": 3.0,
    "accents": {"crit": "hit_accent_crit", "finisher": "hit_accent_crit", "chain_last": "hit_accent_chain", "weave": "hit_accent_weave"},
    "player_hurt": "hurt",
    "object": "hit_on_wood_a",      # a thing struck (a dummy, a crate)
}

# ------------------------------------------------------------------ steps
# The tile set's paint marks (data/topdown/proto_tileset.json `paint`) onto surfaces; a prop's standable top by its
# kind; water cells (level -1) wade. Marks and props not listed step as `default`. `sand` and `snow` wait for their
# tiles (their sounds exist; a mark named for them picks them up here).
SURFACES = ["grass", "dirt", "stone", "wood", "sand", "water", "reeds", "roof", "snow"]
PAINT_SURFACE = {"g": "grass", "f": "grass", "b": "grass", "m": "reeds", "d": "dirt", "p": "stone", "s": "stone",
                 "r": "stone", "l": "stone", "w": "wood", "t": "roof", "a": "sand", "n": "snow"}
PROP_TOP_SURFACE = {"crates": "wood", "house": "roof", "hall": "roof", "storehouse": "roof", "boat": "wood"}
# The side view's ground materials (rooms' `ground.material`), for a room drawn without a height grid.
MATERIAL_SURFACE = {"earth": "dirt", "stone": "stone", "wood": "wood", "sand": "sand", "snow": "snow", "grass": "grass",
                    "water": "water", "marsh": "reeds", "roof": "roof"}

STEPS = {
    "surfaces": {s: {"steps": [f"step_{s}_{v}" for v in "abcd"], "land": f"land_{s}"} for s in SURFACES},
    "paint": PAINT_SURFACE,
    "prop_tops": PROP_TOP_SURFACE,
    "materials": MATERIAL_SURFACE,
    "water": "water",
    "default": "dirt",
    # where a foot lands in each cycle, as fractions of it (the walk and the run: frames 0 and 4 of 8, left then right;
    # tools/art/topdown/figure/actions.py _walk/_run put the stride's ends there)
    "contacts": {"walk": [0.0, 0.5], "run": [0.0, 0.5], "tiptoe": [0.0, 0.5]},
    "gain_db": {"walk": -4.0, "run": 0.0},
    "pitch": {"walk": 0.97, "run": 1.03},
    "pitch_jitter": 0.04,
    "vol_jitter_db": 1.5,
    # landings: none under min_fall (a hop down a step), louder with the height fallen; the body's weight (land_heavy)
    # over the surface's landing from heavy_fall up
    "land": {"min_fall": 6.0, "heavy_fall": 40.0, "heavy": "land_heavy", "gain_by_fall": [[6.0, -8.0], [20.0, -3.0], [60.0, 0.0], [160.0, 2.0]]},
    "jump": "jump",
    # others' feet: quieter, fading with distance from the player (world units), at most this many at once
    "foe_gain_db": -7.0,
    "npc_gain_db": -9.0,
    "foe_min_speed": 18.0,
    "foe_cadence_s": 0.34,         # a foe sheet with no walk action: a step this often while it moves
    "others_max": 6,
}

# ------------------------------------------------------------------ foes
# The voice of a foe's tell (its wind-up), its body when struck, and its death. By race, then nature, then the named
# exceptions (the creatures whose shell, slime or paper the race does not say).
SHELL = ["mudshell_crab", "old_snapper", "rock_beetle", "stone_tortoise", "ironclaw_mole", "tide_crab", "sandstorm_scorpion",
         "void_crab", "boulder_serpent", "pebble_imp", "mirror_wisp", "gravity_golem", "riverstone_ox"]
SLIME = ["hollow_minnow", "hollowed_eel", "marsh_leech", "reed_frog", "mossback_toad", "star_jellyfish", "greyfin", "jade_carp",
         "azure_carp_dragonet", "nebula_eel", "dune_worm", "thousand_eye_toad", "riverbed_serpent", "nebula_leviathan"]
WOOD = ["trial_puppet", "paper_talisman_ghost", "weeping_lantern", "stone_guardian", "jade_sentinel", "river_sentinel",
        "terracotta_warden", "gate_guardian"]
WATER_VOICE = SLIME + ["mudshell_crab", "tide_crab", "old_snapper", "void_crab", "reed_otter"]

FOES = {
    "body_by_race": {"beast": "flesh", "human": "flesh", "construct": "wood", "ghost": "slime", "ashborn": "flesh", "undead": "shell"},
    "body_by_nature": {"hollowed": "slime"},
    "body": dict({e: "shell" for e in SHELL}, **{e: "slime" for e in SLIME}, **{e: "wood" for e in WOOD}),
    "tell_by_race": {"beast": "tell_beast", "human": "tell_human", "construct": "tell_construct", "ghost": "tell_spirit",
                     "ashborn": "tell_human", "undead": "tell_construct"},
    "tell_by_nature": {"hollowed": "tell_spirit", "demonic": "tell_beast"},
    "tell": {e: "tell_water" for e in WATER_VOICE},
    "tell_tick": "tell",           # the readable tick every wind-up shares, under its voice
    "tell_tick_db": -6.0,
    "death_by_body": {"flesh": "die_flesh", "shell": "die_shell", "wood": "die_wood", "slime": "die_slime"},
    "death_by_race": {"ghost": "die_spirit"},
    "death_by_nature": {"hollowed": "die_spirit"},
    "role_db": {"normal": 0.0, "elite": 2.0, "trial": 0.0, "event": 0.0, "story_boss": 3.0, "dungeon_boss": 3.0, "field_boss": 3.0},
    "role_pitch": {"elite": 0.93, "story_boss": 0.86, "dungeon_boss": 0.86, "field_boss": 0.86},
}

# ------------------------------------------------------------------ beds
# A bed: its base loops [[sfx id, dB]] and the layer of each hour. `hours` (TopdownLight's names, or the clock's)
# maps an hour onto the day and night layers' levels in dB (absent: silent); `night_base_db` lowers the base at night.
HOURS = {"morning": {"day": 0.0}, "day": {"day": -2.0}, "evening": {"day": -8.0, "night": -6.0}, "dusk": {"day": -8.0, "night": -6.0},
         "night": {"night": 0.0}, "night_story": {"night": 0.0}, "lamplit": {}}
BEDS = {
    "river": {"bases": [["bed_river", 0.0]], "day": "bed_birds", "night": "bed_frogs"},
    "river_village": {"bases": [["bed_river", -2.0], ["bed_town", -9.0]], "day": "bed_birds", "night": "bed_frogs", "night_base_db": -3.0},
    "marsh": {"bases": [["bed_marsh", 0.0]], "day": "bed_birds", "night": "bed_frogs"},
    "bamboo": {"bases": [["bed_bamboo", 0.0]], "day": "bed_birds", "night": "bed_insects"},
    "pines": {"bases": [["bed_pines", 0.0]], "day": "bed_birds", "night": "bed_insects"},
    "field": {"bases": [["bed_field", 0.0]], "day": "bed_birds", "night": "bed_insects"},
    "town": {"bases": [["bed_town", 0.0]], "night": "bed_insects", "night_base_db": -9.0},
    "sect": {"bases": [["bed_sect", 0.0]], "day": "bed_birds", "night": "bed_insects"},
    "sect_high": {"bases": [["bed_sect", -2.0], ["bed_pines", -6.0]], "day": "bed_birds", "night": "bed_insects"},
    "cave": {"bases": [["bed_cave", 0.0]]},
    "interior": {"bases": [["bed_interior", 0.0]]},
}
BED_ROOMS = {
    "lf_village": "river_village", "lf_village_night": "river", "lf_reed_shallows": "marsh", "lf_lu_boat": "river",
    "lf_fishers_hut": "interior", "lf_granny_liu_hut": "interior", "lf_old_ma_store": "interior", "rm_marsh_edge": "marsh",
    "ja_weapon_hall": "interior", "cm_weapon_hall": "interior", "cm_cliff_stair": "sect_high", "cm_elder_sung_peak": "sect_high",
    "ja_elder_hu_peak": "sect_high", "sf_trial_cloud": "sect_high", "sf_trial_jade": "sect",
}
BED_AMBIENCE = {"river_ambience": "river", "night_ambience": "river", "water_ambience": "river", "waterfall_ambience": "river",
                "town_ambience": "town", "marsh_ambience": "marsh", "birds_ambience": "field", "bamboo_ambience": "bamboo",
                "wind_ambience": "pines"}
BED_TYPES = {"town": "town", "sect": "sect", "interior": "interior", "home": "interior", "rest": "interior", "dungeon": "cave",
             "secret": "cave", "field": "field", "path": "field", "trial": "sect", "insight": "sect", "boss_arena": "field", "story": "field"}
BED_PREFIX = {"lf_": "river", "rm_": "marsh", "ja_": "sect", "cm_": "sect_high", "sf_": "town", "wp_": "field"}

# ------------------------------------------------------------------ music
MUSIC = {
    # Room data names music by mood; the moods onto the synthesized tracks (the director's MUSIC_ALIAS moved here).
    "alias": {"home": "village_day", "reeds_day": "river", "night_hollow": "village_night", "field_earth": "field", "marsh": "river",
              "marsh_grey": "dungeon", "bamboo": "forest", "fair": "village_day", "trial": "battle", "field_mountain": "peak",
              "mist": "peak", "summit": "peak", "town": "village_day"},
    "fight": {
        # a foe fights when its brain is out of these states (enemy_brain.gd), is hostile, awake and within `radius`
        "calm_states": ["idle", "patrol", "return", "follow", "downed", "dug_in"],
        "radius": 560.0,
        "enter_fade_beats": 2.0,     # the stem comes in on the next beat, over this many beats
        "leave_after_s": 4.0,        # it leaves this long after the last foe fighting falls or gives up,
        "leave_fade_bars": 1.0,      # on the next bar line, over this many bars
        "explore_db": -2.0,          # the track under its stem in a fight
        "fallback": "battle",        # a track with no stem crossfades to this on the beat instead
        "fallback_fade_s": 1.2,
        "check_s": 0.25,
    },
    "boss": {"old_snapper": "boss_snapper", "hollowed_eel": "boss_eel"},
    "boss_roles": {"story_boss": "boss", "dungeon_boss": "boss", "field_boss": "boss"},
    "boss_fade_s": 1.0,
    "room_fade_s": 1.0,
}
STINGERS = {"quest_done": "sting_quest", "breakthrough": "sting_breakthrough", "rare_find": "sting_rare", "unlock": "sting_unlock",
            "elite": "sting_elite", "victory": "sting_victory"}
# Events the director answers with a stinger itself (the moments table plays the others as sound layers).
STINGER_EVENTS = {"quest_completed": "quest_done", "system_unlocked": "unlock"}

# ------------------------------------------------------------------ the mix
MIX = {
    # the buses under Master, each driven by its Settings slider (account settings keys; linear 0..1)
    "buses": [{"name": "Music", "setting": "music", "default": 0.7}, {"name": "Ambience", "setting": "ambience", "default": 0.6},
              {"name": "SFX", "setting": "sfx", "default": 0.8}, {"name": "UI", "setting": "ui", "default": 0.7}],
    "master": {"setting": "master", "default": 1.0, "limiter_ceiling_db": -0.5, "limiter_release_s": 0.1, "highpass_hz": 45.0},
    # ducking: the music (and a share of the beds) dips under these, attack and release in seconds
    "duck": {"stinger_db": -10.0, "bark_db": -4.0, "dialogue_db": -6.0, "scene_db": -4.0, "attack_s": 0.08, "release_s": 0.9,
             "ambience_share": 0.5},
    # positional sounds: full level within `near` of the listener (world units), falling to `floor_db` at `far`, and
    # silent past it
    "distance": {"near": 96.0, "far": 900.0, "floor_db": -24.0},
    # the voice limit: `pool` players for SFX and world sounds, `ui_pool` for the interface. Each sound's rule is the
    # first whose prefix it starts with: its priority (a new sound steals the quietest older voice of a lower one when
    # the pool is full), how many of it may sound at once, and the least gap between two of its starts. The player's
    # own sounds rank `player_bonus` higher than the same sound from a foe. The living world's (decision 44) rank under
    # everything the fight plays, a world sound 10 under its rule (Audio.world_sound): a busy village sounds at most
    # three critters and three people at work at once, and any blow, step or tell takes their voices first.
    "voices": {
        "pool": 24, "ui_pool": 6, "player_bonus": 20,
        "rules": [
            ["hurt", 95, 1, 0.08], ["hit_accent_", 85, 2, 0.05], ["cast_", 80, 2, 0.05], ["hit_on_", 70, 4, 0.025],
            ["hit_el_", 70, 3, 0.025], ["hit_tail_", 55, 3, 0.04], ["hit_", 75, 4, 0.025], ["hit", 70, 3, 0.03],
            ["dodge", 66, 1, 0.05], ["parry", 88, 1, 0.05], ["swing_", 64, 3, 0.04], ["swing", 64, 3, 0.04],
            ["land", 60, 2, 0.05], ["jump", 60, 1, 0.05], ["die_", 62, 3, 0.05], ["tell_", 50, 3, 0.08], ["tell", 52, 2, 0.06],
            ["step_", 30, 5, 0.04], ["splash", 58, 2, 0.08], ["loot_drop", 45, 2, 0.1], ["coin", 60, 2, 0.04], ["pickup", 60, 2, 0.05],
            ["door_", 70, 1, 0.2], ["place_", 50, 2, 0.15], ["life_work_", 22, 3, 0.1], ["life_", 26, 3, 0.1],
            ["", 45, 3, 0.03],
        ],
    },
}

# ------------------------------------------------------------------ the world's events
WORLD = {
    "door_types": ["interior", "home"],      # entering a room of these opens a door; leaving one closes it
    "door_open": "door_open", "door_close": "door_close",
    "loot_drop": "loot_drop",
    "splash": "splash",
    "talk_open": "talk_open", "talk_next": "talk_next", "bark": "bark", "scene_in": "scene_in",
    "weave": "hit_accent_weave",
}

# ------------------------------------------------------------------ the living world (decision 44)
# TopdownLife (scripts/topdown/topdown_life.gd `raise_cue`) plays a moment of life as the world sound "life_" + its
# name where it happens (Audio.world_sound: positional, under the fight). The names: the critters' below (a flee as
# "<kind>_flee", the frog's leap and plop, a hen's flap, a cat waking, a dog's bark), and the villagers' work cues
# (topdown_life.py CUES, data/topdown/life.json `cues`) as "work_<cue>", with the blow of a work cue whose tool lands
# (TopdownWork.hit: the axe's, the hammer's) as "work_<cue>_hit". The player's use of a place plays PLACE_SOUNDS.
LIFE_CRITTERS = ["sparrow_flee", "fish_flee", "frog_leap", "frog_plop", "hen_flap", "cat_wake", "dog_bark"]
LIFE_BLOWS = ["chop", "hammer"]
PLACE_SOUNDS = ["place_open", "place_tend", "place_sit"]
# How TopdownLife raises its cues, besides the calls with a literal name (check_life reads the code for both).
LIFE_RAISE_FORMS = ['"work_" + w.cue', 'sound + "_flee"']
TAKE_SUFFIXES = ["_b", "_c", "_d"]
MANIFEST = os.path.join(DATA, "audio.json")
LIFE_SCRIPT = os.path.join(ROOT, "scripts", "topdown", "topdown_life.gd")
LIFE_DATA = os.path.join(DATA, "topdown", "life.json")


def life_ids(cues=None) -> list:
    """Every sound id the living world and the places can ask for."""
    cues = topdown_life.CUES if cues is None else cues
    return ([f"life_{c}" for c in LIFE_CRITTERS] + [f"life_work_{c}" for c in cues] + [f"life_work_{b}_hit" for b in LIFE_BLOWS]
            + list(PLACE_SOUNDS))


def _manifest_sfx() -> dict:
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f).get("sfx", {})
    except (OSError, ValueError):
        return {}


def life_takes() -> dict:
    """A sound's takes, which the director plays in turn: `<id>` and each `<id>_b`, `<id>_c` ... the audio build made
    (tools/audio/life.py TAKES), read from data/audio.json so the two never disagree."""
    sfx = _manifest_sfx()
    out = {}
    for sid in life_ids():
        more = [sid + x for x in TAKE_SUFFIXES if sid + x in sfx]
        if more:
            out[sid] = [sid] + more
    return out


LIFE = {
    "critters": [f"life_{c}" for c in LIFE_CRITTERS],
    "work": [f"life_work_{c}" for c in topdown_life.CUES],
    "blows": [f"life_work_{b}_hit" for b in LIFE_BLOWS],
    "places": PLACE_SOUNDS,
    "pitch_jitter": 0.045,          # each play of a life or a place sound: ± this share of its pitch,
    "vol_jitter_db": 1.0,           # and ± this of its level
}


def check_life() -> list:
    """Every sound the living world can raise has a file: each critter named here, every work cue of the data
    (data/topdown/life.json `cues`, and the source's CUES), each blow, the places', every take. And the code raises nothing
    this table does not know: each `raise_cue` in topdown_life.gd names a listed critter or blow or is one of
    LIFE_RAISE_FORMS, and each `_flee(..., "<kind>")` is a listed "<kind>_flee". -> the problems found."""
    errs = []
    sfx = _manifest_sfx()
    try:
        with open(LIFE_DATA, encoding="utf-8") as f:
            data_cues = json.load(f).get("cues", [])
    except (OSError, ValueError):
        data_cues = []
        errs.append("no data/topdown/life.json to read the work cues from")
    src = ""
    if os.path.exists(LIFE_SCRIPT):
        with open(LIFE_SCRIPT, encoding="utf-8") as f:
            src = f.read()
    else:
        errs.append("no scripts/topdown/topdown_life.gd to read the critters' cues from")
    named = set(LIFE_CRITTERS) | {f"work_{b}_hit" for b in LIFE_BLOWS}
    calls = re.findall(r"\braise_cue\(([^\n]*?),\s*[A-Za-z_][A-Za-z0-9_.]*\)", src)
    for arg in calls:
        arg = arg.strip()
        lit = re.fullmatch(r'"([a-z0-9_]+)"', arg)
        if lit and lit.group(1) not in named:
            errs.append(f'topdown_life.gd raises "{lit.group(1)}": add it to LIFE_CRITTERS (or LIFE_BLOWS) and give it a sound')
        elif not lit and arg not in LIFE_RAISE_FORMS:
            errs.append(f"topdown_life.gd raises a cue as {arg}: tell LIFE_RAISE_FORMS in tools/data/sound.py which sounds it asks for")
    if src and len(calls) < len(LIFE_CRITTERS):
        errs.append(f"found only {len(calls)} raise_cue calls in topdown_life.gd: has the way it raises cues changed?")
    for kind in re.findall(r'\b_flee\(.*"([a-z0-9_]+)"\)', src):
        if f"{kind}_flee" not in LIFE_CRITTERS:
            errs.append(f'topdown_life.gd raises "{kind}_flee" (a flee): add it to LIFE_CRITTERS and give it a sound')
    extra = [c for c in data_cues if c not in topdown_life.CUES]
    if extra:
        errs.append(f"data/topdown/life.json has cues the source has not ({extra}): run tools/data/topdown_life.py")
    ids = life_ids(list(topdown_life.CUES) + extra)
    for takes in life_takes().values():
        ids += takes[1:]
    for sid in ids:
        e = sfx.get(sid)
        if e is None:
            errs.append(f"{sid} has no sound: make it in tools/audio/life.py and run tools/audio/build_audio.py {sid}")
        elif not os.path.exists(os.path.join(ROOT, str(e.get("file", "")).replace("res://", ""))):
            errs.append(f"{sid}: its file {e.get('file')} is missing")
    return errs


def payload() -> dict:
    return {
        "_note": "Built by tools/data/sound.py; never edit by hand. Decision 43: the sound pass (docs/redesign/sound.md).",
        "hits": HITS,
        "steps": STEPS,
        "foes": FOES,
        "beds": {"beds": BEDS, "hours": HOURS, "rooms": BED_ROOMS, "ambience": BED_AMBIENCE, "types": BED_TYPES, "prefix": BED_PREFIX,
                 "default": "field", "fade_s": 2.0},
        "music": MUSIC,
        "stingers": STINGERS,
        "stinger_events": STINGER_EVENTS,
        "mix": MIX,
        "world": WORLD,
        "life": dict(LIFE, takes=life_takes()),
    }


def sound_ids(node=None) -> set:
    """Every sound id the table names (for the builder's and the tests' cross-check with data/audio.json)."""
    out = set()
    node = payload() if node is None else node
    if isinstance(node, dict):
        for v in node.values():
            out |= sound_ids(v)
    elif isinstance(node, list):
        for v in node:
            out |= sound_ids(v)
    elif isinstance(node, str) and (node.startswith(("hit_", "step_", "land_", "swing_", "cast_", "tell", "die_", "bed_", "sting_",
                                                     "door_", "talk_", "boss_", "life_", "place_"))
                                    or node in ("hurt", "jump", "splash", "loot_drop", "bark", "scene_in")):
        out.add(node)
    return out


def build(check_only: bool = False) -> bool:
    path = os.path.join(DATA, "sound.json")
    life = check_life()
    for e in life:
        print(("FAIL: " if check_only else "warning: ") + e)
    if check_only:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            write("sound.json", payload(), folder=tmp)
            fresh = open(os.path.join(tmp, "sound.json"), encoding="utf-8").read()
        current = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if fresh != current:
            print("data/sound.json is not current: run python3 tools/data/sound.py")
            return False
        if life:
            return False
        print(f"sound.json is current; each of the living world's {len(life_ids())} sounds and their takes exists")
        return True
    write("sound.json", payload())
    return True


if __name__ == "__main__":
    sys.exit(0 if build("--check" in sys.argv) else 1)
