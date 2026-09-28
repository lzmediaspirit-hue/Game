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
