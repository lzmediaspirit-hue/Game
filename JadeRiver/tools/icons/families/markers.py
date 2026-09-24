"""Map / quest markers: 12x12 art px (24x24 screen), colour-keyed ASCII."""
from asciiart import parse, sprite
from registry import register

FAM, GROUP = 'markers', 'markers'

M = {}
M['quest_main'] = """
....yy....
...yYYy...
..yYkkYy..
.yYYkkYYy.
yYYYkkYYYy
yYZYkkYYYy
.yYYYYYYy.
..yYkkYy..
...yYYy...
....yy....
"""
M['quest_side'] = """
...bbbb...
.bBBBBBBb.
.bBBWWBBb.
bBBBWWBBBb
bBBBWWBBBb
bBBBWWBBBb
bBBBBBBBBb
.bBBWWBBb.
.bBBBBBBb.
...bbbb...
"""
M['quest_ready'] = """
..yyyyyy..
.yYZZYYYy.
yYYy..yYYy
.yy...yYYy
.....yYYy.
....yYYy..
....yYy...
..........
....yYy...
....yyy...
"""
M['npc'] = """
...NNNN...
..NNNNNn..
..NNNNNn..
..NNNNNn..
...NNNn...
..........
.NNNNNNNn.
NNNNNNNNNn
NNNNNNNNNn
"""
M['vendor'] = """
...yYYy...
..yYZZYy..
yy.yYYy.yy
yYyyYYyyYy
yYYYYYYYYy
.yYYYYYYy.
..yyyyyy..
"""
M['healer'] = """
....ee....
...RRRR...
...RPRR...
....RR....
..RRRRRR..
.RPPRRRRR.
.RPRWWRRr.
.RRWWWWRr.
..RRWWrr..
"""
M['forge_marker'] = """
.......Y..
......YOY.
.......Y..
hhhhhhhh..
Hwwwwwwhh.
..hhhhH...
...hhH....
..hhhhH...
.hhhhhhH..
"""
M['shrine_marker'] = """
....RR....
.RRRRRRRR.
RRRRRRRRRR
.r......r.
..NNNNNN..
..NkkkkN..
..NkyykN..
..NNNNNN..
.nnnnnnnn.
"""
M['portal_marker'] = """
..CCCCCC..
.CCIIIICC.
CCI....cCC
CI..CC..cC
CI.C..c.cC
CI.c.CC.cC
CI..cc..cC
CCc....cCC
.CCccccCC.
..CCCCCC..
"""
M['portal_sealed'] = """
..hhhhhh..
.hhwwwwhh.
hhw....Hhh
hw..hh..Hh
RRRRRRRRRR
rrrrrrrrrr
hw..HH..Hh
hhH....Hhh
.hhHHHHhh.
..hhhhhh..
"""
M['teleport_marker'] = """
....KK....
...KKKK...
..KKKKKK..
....KK....
....KK....
.JJJKKJJJ.
J..J..J..J
.JJJJJJJJ.
"""
M['elite_crown'] = """
y...yy...y
yy.yZYy.yy
yYyYYYYyYy
yYYYYYYYYy
yYYYRRYYYy
yyyyyyyyyy
"""
M['boss_skull'] = """
..NNNNNN..
.NNNNNNNN.
NNNNNNNNNn
NRRNNNNRRn
NRRNNNNRRn
NNNNkkNNNn
.NNNNNNNn.
..NkNkNk..
..NNNNNn..
"""
M['herb_marker'] = """
......GGG.
....GGGLG.
...GGLGG..
..GGLGG...
..GLGG....
...gg.....
..g.......
.g........
g.........
"""
M['ore_marker'] = """
....C.....
...CIC....
...CIC.C..
..CCIcCIC.
..CIIc.Cc.
.hhhhhhhhh
hhwwhhhhhH
.hHHHHHHH.
"""
M['fish_marker'] = """
....BBB...
..BBBBBB.B
.BIBBBBBBB
BkBBBBBBB.
.BBBBBBBBB
..BBBBBB.B
....BBB...
"""
M['player_arrow'] = """
....KK....
....KK....
...KKKK...
...KKKK...
..KKKKKK..
..KKKKKK..
.KKKjjKKK.
.KKj..jKK.
KKj....jKK
Kj......jK
"""

for _id, _art in M.items():
    register(FAM, _id, (lambda rows=parse(_art): sprite(rows)), GROUP)
