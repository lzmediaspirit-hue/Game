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


def _s(light, base, shadow, deep):
    """M1: a five-step ramp from a side-view sheet's material (pixel.material: light, base, shadow, deep), as E2 took the
    rock beetle's: a step under its deep, its deep, shadow and base, and its light as the highlight."""
    d = c(deep)
    return [tuple(int(round(v * 0.62)) for v in d[:3]) + (255,), d, c(shadow), c(base), c(light)]


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
    # rock beetle (E2, its side-view sheet's ramps): a carapace of rocky grey-brown plates and a paler pronotum, ochre
    # lichen on them, dark umber chitin underneath and on the legs, a curved ochre horn
    "beetle_rock": _r("2C2723", "473F37", "6C604F", "998B70", "C2B593"),
    "beetle_pronotum": _r("282320", "3F3833", "5E5446", "857861", "AEA185"),
    "beetle_lichen": _r("3E3020", "5E4A30", "8A6A3E", "B8904E", "E2C27A"),
    "beetle_chitin": _r("171211", "271F1D", "3B302B", "56463C", "7D675A"),
    "beetle_horn": _r("3A2A1A", "5C452E", "8C6A41", "C29B5B", "ECD49A"),
    # pebble imp (E2, its side-view sheet's ramps): warm grey-brown stone, its limbs a little darker, and the pebbles
    # studding it (ochre, slate, rust)
    "imp_stone": _r("2C2724", "463E39", "6C6052", "9B8B71", "C6B693"),
    "imp_limb": _r("292522", "403A36", "62584C", "8C7D66", "B6A586"),
    "peb_ochre": _r("3C2E22", "5E4734", "8B6945", "BB8F59", "E6BF7E"),
    "peb_slate": _r("272C2F", "3C4347", "5C6466", "838C8B", "B7BEBB"),
    "peb_rust": _r("33201C", "4F302B", "784A3C", "A7684E", "D49373"),
    # M1 (the monster engine's first batch past E2). Each from its side-view sheet's materials (tools/art/creatures/).
    # ember fox: orange-red fur, a white bib and muzzle, dark socks, cream ear insides
    "fox_fur": _s("ffb35e", "e06d2e", "ab4328", "6b2926"),
    "fox_white": _s("fffbf0", "f2e4cd", "ccb4a2", "927873"),
    "fox_sock": _s("70403a", "4b2a28", "361d1e", "241314"),
    "fox_ear_in": _s("fbe3c4", "e8bf98", "bf8f74", "8a6255"),
    # mud hound: wet mud browns and dried mud, a pale chest, a leather collar (its brass ring the puppet's brass)
    "hound_fur": _s("c7a574", "927350", "644f40", "3e3232"),
    "hound_mud": _s("6a5440", "4a3b30", "352b27", "231c1c"),
    "hound_pale": _s("e0cda2", "b8a17a", "88745c", "5a4c41"),
    "collar": _s("a4583a", "7a3b2a", "552822", "361a18"),
    "hound_nose": _s("5e4b4c", "3a2d31", "2a2025", "1b1418"),
    # stone tortoise: a shell of pale granite (its scute rim darker), moss on its ledges, a little pine and its bark; an
    # old grey-olive hide, a pale belly and beak
    "mtn_rock": _s("d6d0bd", "a39e8f", "72726b", "4b4e50"),
    "mtn_rim": _s("8e897a", "6a675c", "4c4b45", "333431"),
    "mtn_moss": _s("b9d86c", "7fa947", "557f39", "36572e"),
    "mtn_pine": _s("6f9c55", "3f6e44", "2c5139", "1d372b"),
    "mtn_bark": _s("9a7452", "6d4f38", "4c372a", "33251e"),
    "tort_skin": _s("b8ae8e", "888067", "5e5a4a", "3d3c33"),
    "tort_belly": _s("d9cc9e", "ae9f76", "7f735a", "554d3f"),
    "tort_beak": _s("e5d7a8", "b9a77a", "877858", "5a5040"),
    # jade carp: jade-green scales over a darker back, a pale gold belly, jade fins tipped in gold, gold whiskers
    "carp_scale": _s("a6ecc8", "3fae8a", "1f7a6c", "134c4c"),
    "carp_back": _s("5cc4a0", "1f7a6c", "165e58", "0e3a3c"),
    "carp_belly": _s("fff4c0", "f0d98a", "c2a85c", "86703e"),
    "carp_fin": _s("b8f2dc", "67d6bd", "2c9e8f", "1a6a66"),
    "carp_gold": _s("fff0a8", "e5b84c", "b0802e", "6e4e22"),
    # tide crab: a deep sea teal-blue shell, a paler shield claw, a pale rim, a sandy underside, teal legs, coral tips,
    # pearls
    "tide_shell": _s("7ecae4", "2f80aa", "1f567e", "163658"),
    "tide_claw": _s("b2f2e4", "4cbab0", "2a8088", "1c5264"),
    "tide_rim": _s("d4f4ec", "8fd4d0", "4fa0aa", "2e6a7c"),
    "tide_under": _s("f0e2c2", "c9b690", "948468", "625a4e"),
    "tide_leg": _s("7ccfd8", "3690a8", "23627e", "183f58"),
    "tide_tip": _s("f4a07c", "d8664e", "9a3e3c", "5e2230"),
    "pearl": _s("ffffff", "f6e2ea", "d0aec4", "8e7294"),
    # thornback boar: a dark umber hide and mane, wood-green vines and their leaves, pale woody thorns, a pink-brown snout,
    # dark hooves
    "tb_hide": _s("a57d59", "735442", "4c3a32", "2f2426"),
    "tb_mane": _s("5a4436", "3f2f29", "2d2222", "1e1719"),
    "tb_vine": _s("a9dc6a", "62a046", "3a6c3c", "23443a"),
    "tb_leaf": _s("c9f08a", "7fbf52", "4a8a44", "2b5a3c"),
    "tb_thorn": _s("f2e8b0", "c9b878", "8a7e4e", "565034"),
    "tb_snout": _s("d49a88", "a86e62", "7a4a48", "4e3036"),
    "tb_hoof": _s("5e4a44", "3e302e", "2c2222", "1c1617"),
    # bamboo monkey: gold fur under an olive-green mantle, pale peach skin (its face, hands and feet), the bamboo shoot's
    # cane and pale nodes, its leaf tuft
    "monkey_fur": _s("fbd98a", "d9a24c", "a06a36", "63432e"),
    "monkey_mantle": _s("bdc460", "879a3e", "56693a", "34452f"),
    "monkey_skin": _s("ffe4bd", "efbd92", "bd8468", "7d5048"),
    "bamboo_leaf": _s("b9ec7c", "62b34f", "34804a", "1f5040"),
    "bamboo_cane": _s("d9f59a", "8fd05e", "4f9a4a", "2b6040"),
    "bamboo_node": _s("f4f0c0", "d6d28a", "9aa45a", "5f6c3c"),
    # ironclaw mole: violet-black velvet and its sheen, a pink star nose and palms, iron-grey claws, brown dirt
    "mole_fur": _s("7c7189", "4b4356", "332d3d", "221e2a"),
    "mole_sheen": _s("9a90a8", "6c637a", "4a4357", "332d3d"),
    "mole_pink": _s("ffc4c4", "ec8f98", "b95f70", "7c3e4e"),
    "mole_iron": _s("e2e7ea", "9aa3aa", "646d76", "3d454d"),
    "mole_palm": _s("d99aa0", "b0707c", "80505c", "553644"),
    "mole_dirt": _s("b89163", "8a6841", "5f4830", "3f3023"),
    # green viper: bamboo-green scales, a pale yellow belly and flank stripe, an orange tail tip, a pink mouth
    "viper_scale": _s("c9f27e", "6ec24a", "358c45", "1e5a3e"),
    "viper_belly": _s("fff6b8", "eadc80", "bba955", "7e713c"),
    "viper_tail": _s("ffb070", "e3703f", "a8442f", "6a2a26"),
    "viper_mouth": _s("f59aa4", "d9667a", "9c3a50", "5e1e32"),
    # stone guardian: warm temple stone (its darker carving: mane, collar, bell), moss, a dark mouth
    "sg_stone": _s("dcd2b4", "aaa085", "777164", "4c4a52"),
    "sg_stone_dark": _s("a49c88", "7b7566", "57544f", "383840"),
    "sg_moss": _s("b8d46a", "80a445", "56793a", "3a562d"),
    "sg_mouth": _s("6a3a3a", "4a2629", "351c20", "24141a"),
    # jade crane chick: white down shading toward jade, jade wings and tail tuft, grey-green legs, a horn beak, a red crown
    "chick_down": _s("ffffff", "e6f3ee", "a9d3c5", "6ea596"),
    "chick_jade": _s("9cf0d2", "43b393", "277d6a", "17514a"),
    "chick_leg": _s("9fbab0", "6e8d85", "4e6a66", "35494a"),
    "chick_beak": _s("fff0b0", "e2c86a", "b0944a", "76663a"),
    "chick_crown": _s("ff9a8a", "e45858", "b33a44", "7a2432"),
    # paper talisman ghost: aged talisman paper (the back strips older), cinnabar ink
    "talisman": _s("fff4d2", "ecd8a0", "c4a86c", "8c7246"),
    "talisman_old": _s("e6d4a0", "cdb67c", "a28a58", "6e5a3a"),
    "cinnabar": _s("f08070", "cf3a3a", "962430", "5e1624"),
    "soul_void": _s("5a4290", "3a2a5c", "2a1a40", "1a0f2a"),
    # M2. Each from its side-view sheet's materials (tools/art/creatures/), as M1's.
    # riverbed serpent: jade scales, gold belly scutes and spines, a pale jade fin, ivory horns, a red maw; its water orb
    "rs_scale": _s("96f0c8", "2fa982", "1b7466", "114a4c"),
    "rs_belly": _s("fff2ac", "e5b84c", "b07e30", "6e4a22"),
    "rs_fin": _s("d2fff2", "6fdcc2", "2c9e8f", "15514f"),
    "rs_horn": _s("fff6d2", "e8d49c", "b09c6a", "6e6040"),
    "rs_gold": _s("fff2ac", "e5b84c", "b07e30", "6e4a22"),
    "rs_mouth": _s("e0707a", "a83a4c", "6e2034", "401222"),
    "rs_orb": _s("f2fffc", "a8ecec", "5cc0cc", "2e7a8e"),
    # rapids lizard: blue-green skin, a pale belly, a pale jade fin, a dark red maw
    "rl_skin": _s("7fd8c6", "28868f", "1b5a74", "133a52"),
    "rl_belly": _s("f2f6d6", "c8e2c0", "8fb4a0", "5a7c78"),
    "rl_fin": _s("e2fff6", "8cf0d6", "45bcb2", "23808a"),
    "rl_mouth": _s("c45a68", "8a2f40", "5e1c2c", "3a1020"),
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
    "beetle_rock": {"hi": True}, "beetle_pronotum": {"hi": True, "glossy": True}, "beetle_lichen": {"hi": True},
    "beetle_chitin": {"hi": True, "glossy": True, "thin": True}, "beetle_horn": {"hi": True, "glossy": True, "weight": 1.5},
    "imp_stone": {"hi": True}, "imp_limb": {"hi": True}, "peb_ochre": {"hi": True, "weight": 1.3},
    "peb_slate": {"hi": True, "weight": 1.3}, "peb_rust": {"hi": True, "weight": 1.3},
    # M1
    "fox_fur": {"hi": True}, "fox_white": {"hi": True, "weight": 1.2}, "fox_sock": {"hi": True, "weight": 1.2},
    "fox_ear_in": {"hi": True, "weight": 1.3},
    "hound_fur": {"hi": True}, "hound_mud": {"hi": True, "weight": 1.2}, "hound_pale": {"hi": True, "weight": 1.2},
    "collar": {"hi": True, "weight": 1.6, "line": True}, "hound_nose": {"hi": True, "glossy": True, "weight": 1.5},
    "mtn_rock": {"hi": True}, "mtn_rim": {"hi": True}, "mtn_moss": {"hi": True}, "mtn_pine": {"hi": True, "weight": 1.3},
    "mtn_bark": {"hi": True, "line": True, "weight": 1.4}, "tort_skin": {"hi": True}, "tort_belly": {"hi": True},
    "tort_beak": {"hi": True, "glossy": True, "weight": 1.3},
    "carp_scale": {"hi": True, "glossy": True}, "carp_back": {"hi": True, "glossy": True}, "carp_belly": {"hi": True},
    "carp_fin": {"hi": True, "thin": True}, "carp_gold": {"hi": True, "glossy": True, "line": True, "weight": 1.4},
    "tide_shell": {"glossy": True, "hi": True}, "tide_claw": {"hi": True, "glossy": True}, "tide_rim": {"hi": True},
    "tide_under": {}, "tide_leg": {"hi": True, "thin": True}, "tide_tip": {"hi": True, "glossy": True},
    "pearl": {"hi": True, "glossy": True, "weight": 1.6},
    "tb_hide": {"hi": True}, "tb_mane": {"hi": True, "weight": 1.2}, "tb_vine": {"hi": True, "weight": 1.3},
    "tb_leaf": {"hi": True, "weight": 1.4}, "tb_thorn": {"hi": True, "line": True, "weight": 1.5}, "tb_snout": {"hi": True, "weight": 1.3},
    "tb_hoof": {"hi": True, "weight": 1.3},
    "monkey_fur": {"hi": True}, "monkey_mantle": {"hi": True}, "monkey_skin": {"hi": True, "weight": 1.3},
    "bamboo_leaf": {"hi": True, "line": True, "weight": 1.4}, "bamboo_cane": {"hi": True, "line": True, "weight": 1.5},
    "bamboo_node": {"hi": True, "weight": 1.4},
    "mole_fur": {"hi": True}, "mole_sheen": {"hi": True}, "mole_pink": {"hi": True, "weight": 1.4},
    "mole_iron": {"hi": True, "glossy": True, "line": True, "weight": 1.6}, "mole_palm": {"hi": True, "weight": 1.3},
    "mole_dirt": {"hi": True},
    "viper_scale": {"hi": True, "glossy": True}, "viper_belly": {"hi": True, "weight": 1.2}, "viper_tail": {"hi": True, "weight": 1.3},
    "viper_mouth": {"weight": 1.3},
    "sg_stone": {"hi": True}, "sg_stone_dark": {"hi": True, "weight": 1.2}, "sg_moss": {"hi": True, "weight": 1.2},
    "sg_mouth": {"weight": 1.4},
    "chick_down": {"hi": True}, "chick_jade": {"hi": True, "weight": 1.2}, "chick_leg": {"hi": True, "line": True, "weight": 1.3},
    "chick_beak": {"hi": True, "glossy": True, "weight": 1.5}, "chick_crown": {"hi": True, "weight": 1.6},
    "talisman": {"hi": True, "thin": True}, "talisman_old": {"hi": True, "thin": True}, "cinnabar": {"hi": True, "weight": 1.5},
    "soul_void": {"weight": 1.8},
    # M2
    "rs_scale": {"hi": True, "glossy": True}, "rs_belly": {"hi": True, "weight": 1.2}, "rs_fin": {"hi": True, "thin": True},
    "rs_horn": {"hi": True, "glossy": True, "weight": 1.5}, "rs_gold": {"hi": True, "glossy": True, "line": True, "weight": 1.5},
    "rs_mouth": {"weight": 1.4}, "rs_orb": {"hi": True, "glossy": True, "weight": 1.4},
    "rl_skin": {"hi": True, "glossy": True}, "rl_belly": {"hi": True, "weight": 1.2}, "rl_fin": {"hi": True, "thin": True, "weight": 1.2},
    "rl_mouth": {"weight": 1.4},
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
# E2: the rock beetle's amber eye and the pale specks in its stone; the pebble imp's ember glow (its eyes and the crack
# in its belly), its grin and teeth; the greyfin's grey puddle (its side-view sheet's), its rim, the fish's dark shape
# under the surface and its teeth.
BEETLE_EYE = c("F0B23E")
SPECK = c("E6DCC0")
EMBER = c("FFBE45")
EMBER_CORE = c("FFF1B8")
EMBER_DIM = c("A8692C")
EMBER_GLOW = c("FFBE45", 120)
GRIN = c("2B1712")
IMP_TOOTH = c("F4EAD0")
PUDDLE = c("44525C")
PUDDLE_DEEP = c("2E3A43")
PUDDLE_RIM = c("9AA8AE")
PUDDLE_EDGE = c("0C1217")
PUDDLE_RIPPLE = c("7A8891")
FISH_TOOTH = c("F2F1E6")
# M1: the ember fox's amber eyes and its tail's flame (deep red, orange, pale gold), the mud hound's eyes, a canine's
# nose and teeth.
FOX_EYE = c("FFB62E")
FLAME_DEEP = c("E2452C")
FLAME = c("FF9A36")
FLAME_CORE = c("FFE9A6")
FLAME_GLOW = c("FF9A36", 150)
HOUND_EYE = c("F0B43C")
CANINE_NOSE = c("221214")
FANG = c("FFF6E2")
# M1: the stone tortoise's cracks.
CRACK = c("23272A")
# M1: the jade carp's gold eye.
CARP_EYE = c("F2C24A")
# M1: the thornback boar's fierce red eye and its dark rim.
TB_EYE = c("FF5A3C")
TB_EYE_DARK = c("A8201E")
# M1: the bamboo monkey's amber eye.
MONKEY_EYE = c("D4781E")
# M1: the green viper's gold eye and its red tongue.
VIPER_EYE = c("F6C945")
VIPER_TONGUE = c("E0303C")
# M1: the jade glow of the stone guardian's eyes and cracks (QI's, as light).
QI_GLOW = c("7FE6CC", 120)
# M1: the crane chick's dark eye, the wind its wings throw.
CHICK_EYE = c("2A1A12")
WIND = c("E6F4F0", 200)
# M1: the paper ghost's soul light (its eye holes, its wisps), the void in its eyes.
GHOST_GLOW = c("B89CF0")
GHOST_GLOW_HI = c("EFE6FF")
GHOST_VOID = c("1A0F2A")
GHOST_AURA = c("B89CF0", 140)
# M2: the riverbed serpent's gold eye (its core, glow and ring), its orb's glint and aura, and its clear river (the pool
# round it, lit at its foot, and the rings spreading).
RS_EYE_CORE = c("FFFBE0")
RS_EYE = c("FFD24A")
RS_EYE_RING = c("E0801E")
RS_EYE_GLOW = c("FFD24A", 140)
RS_ORB_GLINT = c("FFFFFF", 230)
RS_ORB_AURA = c("A8ECEC", 150)
RS_POOL = c("2E7A8A", 140)
RS_POOL_LIT = c("5CB4B4", 190)
RS_RIPPLE = c("D2F4EE", 210)
RS_RIPPLE_DIM = c("8CCFC0", 160)
# M2: the rapids lizard's amber eye.
LIZARD_EYE = c("F2B640")


def palette(*names) -> dict:
    return {n: RAMPS[n] for n in names}


def props(*names) -> dict:
    return {n: PROPS.get(n, {}) for n in names}
