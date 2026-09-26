"""Status icons: 12x12 art px (24x24 screen), colour-keyed ASCII (see asciiart.KEY).

Colour language: injuries carry a red crack; stability is one stepped foundation
that fills and changes colour (red -> yellow -> jade -> gold); debuffs use warm or
sickly hues; buffs add a green up-arrow; cultivation states use jade/gold.
"""
from asciiart import parse, sprite
from registry import register

FAM, GROUP = 'status', 'status'

S = {}
S['injury_body'] = """
.NN.......
NNNN......
NNNNn.....
.nNNNn....
..nNNR....
....rRr...
....RNNn..
.....nNNNN
......nNNN
.......NN.
"""
S['injury_meridian'] = """
...CCCC...
.CCc..cCC.
.C......C.
C......RR.
C.......R.
C......RR.
C.......R.
.C.....R..
.CCc..cC..
...CCCC...
"""
S['injury_soul'] = """
....V.....
...VV.....
...VUV.V..
..VVUV.VV.
.VVUUVVVV.
.VVURrVVV.
.VURRUUVv.
.VVRUVVVv.
..VVVVVv..
...vvvv...
"""
_PYR = """
....44....
....44....
...3333...
...3333...
..222222..
..222222..
1111111111
1111111111
"""


def _pyramid(filled, top, base, crack=False, sparkle=False):
    rows = parse(_PYR)
    out = []
    for j, r in enumerate(rows):
        s = ''
        for ch in r:
            if ch == '.':
                s += '.'
            else:
                lvl = int(ch)
                if lvl <= filled:
                    s += top if j % 2 == 0 else base
                else:
                    s += 'D'
        out.append(s)
    if crack:
        out[6] = out[6][:4] + 'r' + out[6][5:]
        out[7] = out[7][:5] + 'r' + out[7][6:]
        out[4] = out[4][:4] + 'D' + out[4][5:]
    if sparkle:
        out[0] = out[0][:1] + 'Z' + out[0][2:]
    return out


S['injury_soul'] = S['injury_soul']
S['toxicity'] = """
......VV..
.....VUGV.
......VV..
..GGG.....
.GLLGG.VV.
.GLGGG.VU.
.GGGGgG...
..GGggG...
...GGG....
"""
S['hollowing'] = """
...hhhh...
.hhHHHHhh.
.hH....Hh.
hH..WW..Hh
hH.WWWW.Hh
hH.WWWW.Hh
hH..WW..Hh
.hH....Hh.
.hhHHHHhh.
...hhhh...
"""
S['composure'] = """
....C.....
...CIC....
...CCC....
....C.....
..........
.KKKKKKKK.
..........
..JJJJJJ..
..........
...JJJJ...
"""
S['poison'] = """
....G.....
...GG.....
...GLG....
..GLGGG...
.GLGGGGG..
.GLGGGgG..
.GGGGGgG..
..GGGgG...
...ggg....
"""
S['burn'] = """
....O.....
...OO.....
...OYO.O..
..OOYO.OO.
.OOYYOOOO.
.OYYZYYOO.
.OYZZZYOo.
..OYZYOo..
...OOOo...
"""
S['slow'] = """
wwwwwwwwww
.wIIIIIIw.
..wIIIIw..
...wIIw...
....ww....
...wIYw...
..wIYYIw..
.wYYYYYYw.
wwwwwwwwww
"""
S['stun'] = """
.Y.....Y..
YZY...YZY.
.Y.....Y..
....Y.....
...YZY....
....Y.....
.yyyyyyy..
y.......y.
.yyyyyyy..
"""
S['root'] = """
...EEEE...
..EEEEEE..
...eEEe...
....EE....
..E.EE.E..
.EE.EE.EE.
E..E..E..E
E.E....E.E
..E....E..
"""
S['bleed'] = """
..R.......
.RR.......
.RPR...R..
RPRRR.RR..
RRRRr.RPR.
.RRr.RPRRR
.....RRRRr
......RRr.
"""
S['freeze'] = """
....I....
.I..I..I.
..I.I.I..
...III...
IIIIWIIII
...III...
..I.I.I..
.I..I..I.
....I....
"""
S['shock'] = """
.....YYY..
....YYY...
...YYY....
..YYYYYY..
.....YYY..
....YYY...
...YY.....
..YY......
..Y.......
"""
S['qi_seal'] = """
...CCCC...
.CCIICCCC.
.CIICCCCC.
CCRCCCCRCC
CCCRCCRCCC
CCCCRRCCCC
CCCCRRCCCC
CCCRCCRCCc
.CRCCCCRc.
..CCCCcc..
"""
S['vulnerable'] = """
hhhhhhhhhh
hwwwwRwwwh
hwwwRRwwwh
hwwwwRRwwh
hwwwRRwwwh
.hwwwRwwh.
.hwwRwwwh.
..hwwRwh..
...hhhh...
"""
S['confusion'] = """
..VVVVV...
.V.....V..
V..VVV..V.
V.V...V.V.
V.V.U.V.V.
V.V..UV.V.
V..V....V.
.V..VVVV..
..V.......
"""
S['fear'] = """
..WWWWWW..
.WWWWWWWU.
WWkkWWkkWU
WWkkWWkkWU
WWWWWWWWWU
WWWWkkWWWU
WWWkkkkWWU
WWWWkkWWWU
WW.WW.WW.U
W...W...U.
"""
S['buff_attack'] = """
....W...G.
...WWw.GGG
...WWw..G.
...WWw..G.
...WWw....
...WWw....
.yyyyyyy..
....rr....
....rr....
...yyyy...
"""
S['buff_defense'] = """
........G.
BBBBBBBGGG
BIIIIBB.G.
BIBBBBB.G.
BIBBBBB...
.BIBBBB...
.BBBBBb...
..BBBb....
...Bb.....
"""
S['buff_speed'] = """
........G.
KK..KK.GGG
.KK..KK.G.
..KK..KKG.
..KK..KK..
.KK..KK...
KK..KK....
"""
S['exhausted'] = """
.w........
wIw.......
wIw..hhh..
.w...hhh..
.....hhh..
...hhhhhhh
....hhhhh.
.....hhh..
......h...
"""
S['meditating'] = """
....KK....
...KKKK...
.K.KKKK.K.
.KK.KK.KK.
..KKKKKK..
KJ.KKKK.JK
.JJJJJJJJ.
..JJJJJJ..
"""
S['consolidating'] = """
....y....
...yYy...
..yYyYy..
.yYyZyYy.
yYyZyZyYy
.yYyZyYy.
..yYyYy..
...yYy...
....y....
"""
S['bottleneck'] = """
..hhhhhh..
..hwwwwh..
...hwwh...
...hwwh...
RRRRRRRRRR
rrrrrrrrrr
...hwwh...
..hwwwwh..
.hwwwwwwh.
hhhhhhhhhh
"""
S['spawn_protection'] = """
..ZZZZZZ..
.Z......Z.
Z..yyyy..Z
Z.yYYYYy.Z
Z.yYZYYy.Z
Z.yYYYYy.Z
Z..yYYy..Z
Z...yy...Z
.Z......Z.
..ZZZZZZ..
"""

# S48 Qi Deviation: the Qi spiral turned back on itself, one arm in the wrong colour.
S['qi_deviation'] = """
...CCCC...
.CC....R..
.C..CC..R.
C..C..C.R.
C.C.RR.CR.
C.C..R.C..
C..C..C...
.R..CC..C.
..RR...CC.
....RRRR..
"""
# S48 heart demon (25 and more): a red horned face in a dark flame.
S['heart_demon'] = """
.r......r.
.rR....Rr.
..rRrrRr..
.rrRRRRrr.
rrRYrrYRrr
rRRRRRRRRr
rRRrRRrRRr
.rRRrrRRr.
..rRRRRr..
...rrrr...
"""

S['sense_locked'] = """
....VV....
....VV....
..WWWWWW..
.WWUUUUWW.
VWWUkkUWWV
VWWUkkUWWV
.WWUUUUWW.
..WWWWWW..
....VV....
....VV....
"""
S['poison_body'] = """
...GGGG...
...GLLG...
...GGGG...
.GGGGGGGG.
G.GGLGGG.G
G.GGGGgG.G
..GGGGgg..
..GG..gg..
.gGG..GGg.
.g......g.
"""

ORDER = ['injury_body', 'injury_meridian', 'injury_soul', 'stability_unstable', 'stability_settling',
         'stability_stable', 'stability_solid', 'toxicity', 'hollowing', 'composure', 'poison', 'burn', 'slow',
         'stun', 'root', 'bleed', 'freeze', 'shock', 'qi_seal', 'vulnerable', 'confusion', 'fear', 'buff_attack',
         'buff_defense', 'buff_speed', 'exhausted', 'meditating', 'consolidating', 'bottleneck',
         'spawn_protection', 'qi_deviation', 'heart_demon', 'sense_locked', 'poison_body']

PYRAMIDS = {
    'stability_unstable': (1, 'P', 'R', True, False),
    'stability_settling': (2, 'Y', 'y', False, False),
    'stability_stable': (3, 'K', 'J', False, False),
    'stability_solid': (4, 'Z', 'y', False, True),
}

for _id in ORDER:
    if _id in PYRAMIDS:
        f, t, b, cr, sp = PYRAMIDS[_id]
        register(FAM, _id, (lambda f=f, t=t, b=b, cr=cr, sp=sp: sprite(_pyramid(f, t, b, cr, sp))), GROUP)
    else:
        register(FAM, _id, (lambda rows=parse(S[_id]): sprite(rows)), GROUP)
