"""Top-down terrain palette (docs/redesign/art_bible.md §2).

Every ramp runs dark -> light. Terrain ramps have seven steps: 0 is the deepest shade (cracks, the underside of a
lip), 3 is the base, 5 the sunlit side and 6 the specular rim. Shadows shift toward blue-green and highlights toward
warm gold, as docs/art-contracts.md asks; nothing is shaded with pure black or white.

Where a Style A ramp from tools/icons/palette.py fits, the terrain ramp extends it (named in the comment), so a tile
and an item icon of the same material share their hues. The values are copied, not imported, so an icon retune never
moves the world art by accident.
"""
from __future__ import annotations


def c(h: str, a: int = 255) -> tuple:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def ramp(*hexes: str) -> list:
    return [c(h) for h in hexes]


def alpha(col: tuple, a: int) -> tuple:
    return (col[0], col[1], col[2], a)


CLEAR = (0, 0, 0, 0)

# Contract tokens (docs/art-contracts.md).
INK = c("071015")
NIGHT = c("0A2027")
TEAL = c("0D3035")
JSHADOW = c("15514F")
JADE = c("2C9E8F")
BJADE = c("67D6BD")
BRONZE = c("9A6A35")
GOLD = c("E5B84C")
PGOLD = c("FFE6A1")
PAPER = c("E8E1CF")
MIST = c("AFC9D1")
QI = c("32BED1")

# Outlines: props take a dark hue of their own material on the lit (upper-left) side and this ink-teal on the shaded
# side; terrain has no outlines.
LINE = c("0E1A1E")
LINE_SOFT = c("26363A")

# ---- ground tops -------------------------------------------------------------------------------------------------
# Grass: Style A 'leaf' stretched to seven steps and warmed at the top, so a sunlit meadow reads bright.
GRASS = ramp("123A27", "1D5634", "2C743C", "448F43", "63AA4C", "8FC65C", "C4E484")
# Path earth: between Style A 'clay' and 'straw'; a warm ochre that sits under the green.
DIRT = ramp("3B281B", "5A3E28", "7A5A38", "9A774B", "B79463", "D2B282", "E8D3A6")
# Paving flags: Style A 'warmstone', extended. Warm grey so a town square reads sunny, not cold.
PAVE = ramp("2B2825", "46403A", "625A51", "80766A", "9E9383", "BCB19D", "D9D0BC")
# Dressed granite (terrace walls, the promenade, stairs): Style A 'stone', extended. Cooler than the paving.
STONE = ramp("1A2226", "2A353B", "405058", "5E6F76", "83949A", "AAB8B9", "D0DAD6")
# Karst cliff rock: blue-grey limestone with warm lit tops.
ROCK = ramp("1C2427", "2E3A3D", "455354", "5F6E6C", "7F8C86", "A5AEA3", "CBD0C0")
# Bank soil under the grass lip.
EARTH = ramp("261811", "3E271B", "583A27", "745035", "916A47", "AE875E", "C9A77C")
# Moss on stone and rock.
MOSS = ramp("15321F", "224A28", "356535", "4E8240", "6FA04C", "9CC266", "C8DC8A")

# ---- water -------------------------------------------------------------------------------------------------------
# The Jade River: Style A 'jade' pushed toward the river's deep teal. The water is the one big field of the game's
# signature colour.
WATER = ramp("0A2A2E", "0F3E41", "15544F", "1D6C61", "2A8876", "4CA992", "8BD5BC", "D6F5E6")
FOAM = c("E6FAF0")

# ---- built materials ---------------------------------------------------------------------------------------------
WOOD = ramp("24150B", "3F2616", "623E23", "875A33", "AB7A47", "CB9C64", "E2BF8A")        # Style A 'wood'
DARKWOOD = ramp("1A1009", "311F12", "4E331E", "6E4B2B", "90683D")                       # Style A 'darkwood'
ROOF = ramp("141A1F", "222B32", "323E46", "46545C", "5E6D74", "7D8C90", "A3B0B0")      # grey fired roof tile
PLASTER = ramp("6E685B", "9A917D", "BDB39C", "D6CEB8", "E8E1CF", "F6F1E3")              # Style A 'paper'
RED = ramp("35101A", "641B26", "962A2F", "C23D37", "DE5A45", "F2866A")                  # red lacquer (Style A 'red')
LANTERN = ramp("7A2418", "B83A22", "E2582C", "F58A3A", "FFC35E", "FFF0B0")              # a lit paper lantern
GOLDR = ramp("6E4A1C", "A8772F", "E5B84C", "FFE6A1", "FFF8E2")                          # Style A 'gold'
BRONZER = ramp("2E1E10", "4F3520", "7A5230", "9A6A35", "C8964F", "EDCB86")              # Style A 'bronze'

# ---- plants ------------------------------------------------------------------------------------------------------
BAMBOO = ramp("12301A", "1C3A1C", "2F6230", "5A9A44", "98C862", "DDF0A0")               # Style A 'bamboo'
LEAF = ramp("0C2A1E", "164530", "236243", "388350", "5AA45B", "8DC877", "BFE39A")       # willow and shrubs
PAD = ramp("0E3530", "15503F", "22704D", "3A9159", "63B26A", "9AD08A")                  # lotus pads: blue-green
LOTUS = ramp("6A3552", "B0628A", "E7A0BE", "F8D2E0", "FFF1F6")                          # Style A 'lotuspink'
REED = ramp("2A2A12", "46461C", "6C6A2A", "98923E", "C4BC62")
# Mountain pines of the sect grounds: needles a cooler, deeper green than the willow, bark a warm red-brown.
PINE = ramp("0B221D", "123429", "1B4935", "276042", "3A7A4D", "5E9A5C", "8FBC76")
BARK = ramp("2A140C", "4A2616", "6C3A20", "8E522E", "B0703E")
# The Hollowing (the grey in the marsh): colour drained to a cold ash grey, a breath of teal in its shade.
HOLLOW = ramp("2B3232", "46504F", "66706D", "8A928D", "AEB3AC", "D2D5CD")
# The Cloud Sect's white and sky blue, for its banners.
CLOUD = ramp("3A5670", "5E83A3", "8DB2CC", "C4DAE6", "EEF5F7")

# ---- light and shade ---------------------------------------------------------------------------------------------
# Cast shadows and contact shade are a translucent deep teal laid over whatever is under them (the hue-shift rule).
SHADE = c("0B2A30")
WARM_RIM = c("FFF0C8")

# ==================================================================================================================
# Terrain v2 (decision 40; docs/redesign/art_bible.md "Terrain v2"). The tiles' own ramps, hue-shifted harder than the
# kit's: every ramp's dark end leans blue-violet or teal and its light end warm yellow, so a lit plane and its shade
# differ in hue as well as value (the "32-bit" look). The props and creatures keep the ramps above; these are the
# ground's, the faces', the water's and the buildings' drawn on the grid (and the house props' roofs and walls).
# ==================================================================================================================
# The sun: one light, high in the north-west. Its warm light on lips, west rims and lit planes:
SUN = c("FFE9A6")
# The shadow: a cool blue-violet laid translucently over whatever is under it (never black, never grey). Cast shadows
# use it at SHADOW_A; ambient occlusion steps down from AO_STEPS where a face meets the ground.
SHADOW = c("241F4F")
SHADOW_A = 104                      # 0.41: a cast shadow's body
AO_STEPS = (150, 104, 64, 30)       # 0.59, 0.41, 0.25, 0.12: the 4 px at the foot of a face, nearest first
# The low-frequency tone patches over meadows, earth and rock (never paving or granite): a whisper of sunlit yellow-green
# and of blue-green shade (TONE_A each), just enough to break a big field without staining it.
TONE_SUN = c("DDF27A")
TONE_SHADE = c("0E4A58")
TONE_A = (20, 30)                   # sun, shade

GRASS2 = ramp("123040", "144A40", "1B6641", "2B823D", "45A03A", "87C749", "CBE86C")   # base 4, tufts 3, tips 5
DIRT2 = ramp("35222E", "5A3531", "80523B", "A2704A", "BF8E5C", "D8AE77", "EECB98")    # base 3-4
PAVE2 = ramp("2A2330", "4A3F44", "6D6057", "8F8170", "AD9E88", "C8BAA0", "E3D8BE")    # warm grey-beige stone, base 4
STONE2 = ramp("1A1E33", "2A3249", "43506A", "63728A", "8594A6", "ADBAC6", "DDE4E6")   # dressed granite, cooler
ROCK2 = ramp("1E1D33", "2F3046", "474A5C", "62666C", "82857F", "A7A794", "CECAAE")    # karst: warm lit planes
EARTH2 = ramp("241B2B", "3A2932", "553A38", "714F41", "8E684D", "AA855F", "C5A47A")   # bank soil
MOSS2 = ramp("13283A", "1A3F3E", "285B42", "3F7845", "63964A", "90B656", "C4D67E")
WATER2 = ramp("0C1B33", "0F2C44", "114350", "155C5A", "1E7766", "2F9575", "5DBB93", "A9E6C9")  # deep -> glint
BED2 = ramp("2F4A45", "4C6F5E", "6F9377", "95B28C", "BCCDA2")                              # the shallows' bed
FOAM2 = c("E9FBF1")
ROOF2 = ramp("14131F", "1F2131", "2B3044", "3A4458", "4F5C6E", "6E7D8C", "9BAAB1")    # dark glazed tile
PLASTER2 = ramp("6F6679", "958D98", "B8B0AE", "D3CBBD", "E7E0CF", "F6F1E3")
TIMBER2 = ramp("1E1219", "362127", "53342C", "735036", "946D45")
WOOD2 = ramp("2A1A1C", "46291F", "683F28", "8B5B34", "AD7B46", "CB9C63", "E2BE88")
RED2 = ramp("3A1026", "661A2E", "922636", "BD3B3C", "D95B49", "EE8B6B")
LEAFFALL = ramp("6B3A1E", "A5602A", "D69A3C", "F0C862")                                # fallen leaves
PETAL = ramp("B0628A", "E7A0BE", "F8D2E0")                                              # blossom petals
FLOWER = [c("F4F0E0"), c("FFE07A"), c("F0A0C0"), c("A8B8F0"), c("F28A6A")]            # white, gold, pink, blue, coral
