"""The foes' colours: five-step ramps (deep, shadow, base, light, highlight) per material, taken from each creature's
side-view sheet (art/creatures/) as the earlier top-down foes were, so each stays recognisable; render.ramp7 turns them
into the figure's seven steps toward the §14 sun and shadow. And how each material takes the light (render.MATS's keys:
`hi` may reach the bright step, `glossy` a sheen or a glint, `thin`/`line` hold a pixel-wide part unbroken, `th` its
own thresholds, `rim` how warm its rim)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # tools/art/topdown

from palette import c  # noqa: E402


def _r(*h):
    return [c(x) for x in h]


RAMPS = {
    # mud crab
    "shell": _r("3A2A30", "5A4034", "7E5A3E", "A07A52", "C4A276"),
    "shell_rim": _r("2E2226", "453235", "634739", "7C5A40", "8E6444"),
    "shell_pale": _r("6A5040", "927254", "B09068", "C8AA80", "DEC89E"),
    "crab_leg": _r("2E2226", "453235", "684B3B", "8E6444", "A9805A"),
    "claw": _r("40303A", "684B3B", "8E6444", "B08158", "C9A07A"),
    "claw_tip": _r("124F4A", "257F78", "46BAA6", "7FDCC6", "A4F2DC"),
    "eye": _r("0A1A1D", "1A1216", "1A1216", "2B2A2E", "5B6363"),
    # reed rat
    "fur": _r("2E2630", "3D3340", "5F5052", "7E6E66", "977F68"),
    "fur_light": _r("5F5052", "7C6C66", "977F68", "B8A488", "C7B397"),
    "pink": _r("6E3E48", "B56D72", "CF918A", "E39A92", "F2C0B6"),
    "tail_a": _r("1F3A20", "33552F", "4B7036", "6E9A44", "82AD4F"),
    "tail_b": _r("1A301B", "2A4828", "3F6232", "5C8A3E", "76A248"),
    # boarlet
    "hide": _r("241611", "3A2520", "5A3A27", "7E5230", "925F35"),
    "hide_head": _r("22140F", "36221A", "52382A", "714A32", "8A5C3A"),
    "stripe": _r("5A3A22", "8A6440", "AC8252", "C8A06A", "E0C08C"),
    "hoof": _r("120B0B", "1C110E", "2B1C17", "3F2A22", "553A2E"),
    "snout": _r("4A2A26", "7F4A3C", "8F5A52", "B07A6E", "C99A8E"),
    "bristle": _r("120B0B", "1C110E", "2B1C17", "422B28", "5C3A28"),
    "tusk": _r("8A7A58", "B8A87E", "E9DCB8", "F4ECD2", "FFF8E6"),
    # hollowed boarlet: the boarlet with its colour drunk out of it, pale ash stripes, grey strands
    "h_hide": _r("343C3C", "525A5A", "767E7C", "9AA09C", "BCC0BA"),
    "h_head": _r("2A3030", "444C4C", "626A68", "828A86", "A0A6A2"),
    "h_stripe": _r("5C6563", "8A928D", "D2D5CD", "E2E3DC", "F0F0EA"),
    "h_snout": _r("4A4E4E", "6A6E6C", "8E908C", "A8AAA4", "C0C2BC"),
    "h_bristle": _r("1A2020", "283030", "3A4444", "505A5A", "687272"),
    "strand": _r("7C8886", "A3AEAB", "C9D0CC", "E2E6E1", "F2F4F0"),
    # trial puppet: carved timber, brass ball joints, the sect's jade sash and back plate
    "timber": _r("3A2412", "5E3C1E", "875A30", "AE7C46", "CFA064"),
    "timber_dark": _r("24160A", "3A2412", "5E3C1E", "7A5028", "96683A"),
    "brass": _r("3A2810", "5E4420", "8A6630", "B08A48", "E4C47A"),
    "puppet_jade": _r("0F3A36", "17564F", "2C8A7C", "4CB6A2", "8AE0CC"),
    "rope": _r("4A3A22", "6E5832", "9A8250", "C2AA74", "DCC898"),
    # reed frog: leaf green with a gold stripe down each flank and a pale belly
    "frog": _r("123A1E", "1E5A2A", "2F8A38", "5BB64A", "8ED866"),
    "frog_belly": _r("5A6A2A", "8A9A40", "BFC468", "DCD88A", "EEE8B0"),
    "frog_stripe": _r("6A5A14", "A89024", "D8C040", "F0DC60", "FFF090"),
    "frog_sac": _r("8A8A40", "B8B45C", "E2DA8A", "F2ECB4", "FBF6D8"),
    "frog_eye": _r("6A5010", "A8861E", "E0C040", "F2DA60", "FFF0A0"),
    # marsh leech (decision 44): a wet, dark olive back going to black on the flanks (their highlights pale and cool,
    # for the sheen), a paler khaki belly, a fleshy lip round a dark maw
    "leech": _r("0A0D07", "141B0D", "222D16", "35441F", "A6B89A"),
    "leech_dark": _r("060708", "0C0F0A", "151A10", "242D1B", "8A9C86"),
    "leech_belly": _r("3A3822", "5A5634", "7C784C", "9E9A66", "BEB886"),
    "leech_lip": _r("2E1616", "4C2826", "6E3E3A", "8E5850", "AA7468"),
    "leech_maw": _r("0A0507", "160B0E", "241216", "361E22", "4A2C2E"),
    # reed otter: a sleek brown coat, a pale muzzle and throat
    "otter": _r("2A1A10", "4A2E1A", "6E4426", "8E5C34", "A87444"),
    "otter_pale": _r("7A6040", "A88A64", "C8AA82", "DCC4A0", "EEDCBC"),
    "otter_dark": _r("1A100A", "2A1A10", "3E2616", "56361E", "6E4426"),
    # Old Snapper: a dark green shell grown over with moss, khaki skin, a pale hooked beak, the red crusher claw
    "snap_shell": _r("111A16", "1A2621", "2A392C", "3D5034", "61784A"),
    "snap_moss": _r("24401E", "335024", "4A6A2C", "6A8C3A", "92B452"),
    "snap_moss_lit": _r("335024", "4A6A2C", "6A8C3A", "8CAE4C", "B0CE6E"),
    "snap_skin": _r("33372F", "4F4F3E", "736E4F", "A29A6C", "BDB587"),
    "snap_belly": _r("4F493C", "786C52", "A7966B", "D0C08E", "E6D9AC"),
    "snap_beak": _r("5C5242", "958561", "CBB98A", "F0E2B6", "F8EDCB"),
    "crusher": _r("4A262B", "763C33", "A95C3D", "DE9463", "EDB287"),
    "crusher_tip": _r("1D1519", "2E2024", "44302F", "74514B", "8E6A62"),
    "weed": _r("2B3E2A", "425C33", "62803D", "93AE58", "B2C878"),
    "snap_eye": _r("7A4A0A", "B8741A", "F4B73A", "FAD27A", "FFF0B8"),
    # mossback toad: an olive-khaki hide, a mat of moss and fern sprouts on its back, a cream belly and throat sac
    "toad": _r("2A2C1E", "42462C", "5E623A", "7C7E4C", "9A9A62"),
    "toad_leg": _r("383A28", "56583A", "7A7A4C", "A09C64", "BAB47E"),
    "toad_belly": _r("766A55", "AA9870", "D9C690", "F3E6B8", "F8EFCE"),
    "toad_sac": _r("AD9A70", "D6C28E", "F2E3B2", "FBF3D6", "FCF7E6"),
    "toad_moss": _r("2A4A2A", "3E6630", "5A8A3A", "7EAE4E", "A2C866"),
    "toad_fern": _r("2F5A36", "4F8440", "7FB04C", "C2E27A", "D8F09A"),
    "tongue": _r("733946", "B0565F", "E0827F", "F6B7B0", "FAD0CA"),
    "toad_eye": _r("7A5A14", "B8861E", "E0A830", "F2C145", "FBE08A"),
    "maw": _r("1E0E12", "35191E", "4E242A", "6A3238", "8A4A4E"),
    # hollowed eel: a huge river eel drained grey, darker than the minnow so its bulk is no white blob; a pale belly
    "eel": _r("2A343C", "3E4A54", "58646E", "7A868E", "A2ACB0"),
    "eel_belly": _r("76838A", "9FABAD", "C9D0CD", "E0E5E0", "EEF0E9"),
    "eel_fin": _r("2F3840", "3F4A52", "58646C", "78848B", "A9B3B7"),
    "eel_mouth": _r("141A20", "1F2830", "2E3A44", "46545E", "6A7880"),
    # decision 45: the eel awakened, the first boss's second phase: its grey bruised toward violet and near black, a
    # sickly belly, its fins edged in dried-blood red, its maw a red wound, its strands turned to smoke
    "eel_wake": _r("100C16", "1E1828", "302840", "463C5A", "665C7E"),
    "eel_wake_belly": _r("2E2640", "463C5E", "625680", "84789E", "A89CBC"),
    "eel_wake_fin": _r("2A1420", "4A1E2C", "7A2E3A", "A8464C", "C87268"),
    "eel_wake_mouth": _r("1E060A", "3C0C14", "5E1620", "86222C", "B03A40"),
    "strand_wake": _r("3E3848", "5A5266", "7C7288", "9E94AA", "C0B8CA"),
    # hollow minnow: a small grey fish, dark back, pale belly, grey fins
    "minnow": _r("3E4A53", "5A6770", "808D94", "AAB5B8", "D6DDD9"),
    "minnow_back": _r("343E47", "4B565F", "67737B", "8D989D", "A9B2B6"),
    "minnow_belly": _r("7D8990", "A4AFB1", "CDD4D0", "E9ECE4", "F2F4EE"),
    "minnow_fin": _r("535F69", "77848C", "A3AEB3", "D3DBDB", "E4EAE8"),
    "mist": _r("5F6B72", "7F8B92", "A3AEB2", "C9D2D3", "E6ECEA"),
}

# How each material takes the light and resolves (render.MATS's keys).
PROPS = {
    "shell": {"glossy": True}, "shell_pale": {}, "shell_rim": {"hi": True},
    "crab_leg": {"hi": True, "thin": True}, "claw": {"hi": True, "glossy": True}, "claw_tip": {"hi": True, "glossy": True},
    "eye": {"hi": True, "glossy": True, "weight": 1.6},
    "fur": {"hi": True}, "fur_light": {"hi": True}, "pink": {"hi": True, "weight": 1.3},
    "tail_a": {"hi": True, "weight": 1.2}, "tail_b": {"hi": True, "weight": 1.2},
    "hide": {"hi": True}, "hide_head": {"hi": True}, "stripe": {"hi": True, "weight": 1.2}, "hoof": {"hi": True, "weight": 1.3},
    "snout": {"hi": True, "weight": 1.3}, "bristle": {"line": True, "weight": 1.2},
    "tusk": {"hi": True, "glossy": True, "thin": True, "weight": 1.8},
    "h_hide": {"hi": True}, "h_head": {"hi": True}, "h_stripe": {"hi": True, "weight": 1.2}, "h_snout": {"hi": True, "weight": 1.3},
    "h_bristle": {"line": True, "weight": 1.2}, "strand": {"hi": True, "line": True, "rim": 0.1},
    "timber": {"hi": True}, "timber_dark": {"hi": True}, "brass": {"hi": True, "glossy": True, "weight": 1.4},
    "puppet_jade": {"hi": True, "glossy": True, "weight": 1.5}, "rope": {"hi": True, "weight": 1.3},
    "frog": {"hi": True, "glossy": True}, "frog_belly": {"hi": True}, "frog_stripe": {"hi": True, "weight": 1.4},
    "frog_sac": {"hi": True, "glossy": True}, "frog_eye": {"hi": True, "glossy": True, "weight": 1.6},
    # The leech's wet skin: lit late (its back sits on the light step), so its sheen (sculpt.Part.sheen) is what reaches
    # the bright and highlight steps.
    "leech": {"hi": True, "glossy": True, "th": (-0.3, 0.2, 0.86, 0.99)},
    "leech_dark": {"hi": True, "glossy": True, "th": (-0.3, 0.2, 0.86, 0.99)},
    "leech_belly": {"hi": True}, "leech_lip": {"hi": True, "weight": 1.5}, "leech_maw": {"weight": 1.5},
    "otter": {"hi": True, "glossy": True}, "otter_pale": {"hi": True}, "otter_dark": {"hi": True},
    "snap_shell": {"hi": True, "glossy": True}, "snap_moss": {"hi": True}, "snap_moss_lit": {"hi": True},
    "snap_skin": {"hi": True}, "snap_belly": {"hi": True}, "snap_beak": {"hi": True, "glossy": True, "weight": 1.3},
    "crusher": {"hi": True, "glossy": True}, "crusher_tip": {"hi": True, "glossy": True, "weight": 1.3},
    "weed": {"hi": True, "line": True}, "snap_eye": {"hi": True, "glossy": True, "weight": 1.8},
    "toad": {}, "toad_leg": {"hi": True}, "toad_belly": {"hi": True}, "toad_sac": {"hi": True, "glossy": True},
    "toad_moss": {"hi": True}, "toad_fern": {"hi": True, "line": True}, "tongue": {"hi": True, "glossy": True, "weight": 1.5},
    "toad_eye": {"hi": True, "glossy": True, "weight": 1.6}, "maw": {"weight": 1.4},
    "eel": {"glossy": True}, "eel_belly": {"hi": True}, "eel_fin": {"hi": True, "thin": True},
    "eel_mouth": {"weight": 1.3},
    "minnow": {"hi": True, "glossy": True}, "minnow_back": {"hi": True}, "minnow_belly": {"hi": True},
    "minnow_fin": {"hi": True, "thin": True}, "mist": {"hi": True},
}

# Single colours laid on as marks and points.
GLINT = c("F4F0DE")
INKY = c("1A1216")
RAT_EYE = c("B8442E")
HOLLOW_EYE = c("E2F4EE")
EYE_HALO = c("CFE6EA")
WAKE_EYE = c("FF5A48")          # decision 45: the awakened eel's eyes, burning
WAKE_HALO = c("FFB08A")
GOLD_EYE = c("FFD35A")
GOLD_GLINT = c("FFF4C8")
DUST = c("C9B891", 210)
DUST_DIM = c("A8966E", 160)
QI = c("7FE6CC")
QI_DIM = c("4CB6A2", 200)
QI_BRIGHT = c("D6FFF2")
SPLASH = c("CFEFE8")
SPLASH_DIM = c("8CCFC0", 210)
MOTE = c("C9D2D3", 210)
MOTE_DIM = c("A3AEB2", 170)
LEECH_SPOT = c("A89A48")
LEECH_EYE = c("D2CC96")
LEECH_TOOTH = c("C9B79C")
WART = c("D5C48A")
BARNACLE = c("F4F2E6")
BARNACLE_SHADE = c("959C92")
TALON = c("DDD3B2")
CLAW_TOOTH = c("FDF3D8")
HOOK = c("443C31")
TOAD_MOUTH = c("35191E")
EEL_TOOTH = c("EEF0E6")
FISH_MOUTH = c("2A333B")
POOL = c("1F2830", 150)
FOAM = c("DCE4E4", 235)
RIPPLE = c("B7C4C8", 210)
RIPPLE_DIM = c("7F8E96", 160)


def palette(*names) -> dict:
    return {n: RAMPS[n] for n in names}


def props(*names) -> dict:
    return {n: PROPS.get(n, {}) for n in names}
