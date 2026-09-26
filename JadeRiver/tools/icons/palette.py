"""Palette tokens (docs/art-contracts.md) and shared hue-shifted ramps.

Ramps run dark -> light. Five-step ramps use index 2 as the base colour,
3 as the lit side and 4 as the specular / rim highlight.
"""
from pix import Ramp, hramp, rgb, mix  # noqa: F401

# Contract tokens --------------------------------------------------------------
INK = '#071015'
RIVER_NIGHT = '#0A2027'
DEEP_TEAL = '#0D3035'
JADE_SHADOW = '#15514F'
JADE = '#2C9E8F'
BRIGHT_JADE = '#67D6BD'
AGED_BRONZE = '#9A6A35'
WARM_GOLD = '#E5B84C'
PALE_GOLD = '#FFE6A1'
PAPER = '#E8E1CF'
MIST_BLUE = '#AFC9D1'
WARNING_RED = '#E45858'
QI_CYAN = '#32BED1'
SOUL_VIOLET = '#9B78D1'
HOLLOW_GREY = '#87949A'
WHITE = '#FFFDF4'

R = {}


def _r(name, cols, out=None):
    R[name] = Ramp(cols, out)
    return R[name]


# Core materials -----------------------------------------------------------------
_r('jade',      ['#0F3D3B', '#15514F', '#2C9E8F', '#67D6BD', '#CFF7E6'], '#082322')
_r('deepjade',  ['#0A2A2A', '#0F3D3B', '#15514F', '#2C9E8F', '#67D6BD'], '#051617')
_r('gold',      ['#6E4A1C', '#A8772F', '#E5B84C', '#FFE6A1', '#FFF8E2'], '#2E1D0B')
_r('bronze',    ['#3E2918', '#664525', '#9A6A35', '#C8964F', '#EDCB86'], '#1E130A')
_r('paper',     ['#5F5B50', '#9E9580', '#CFC6AE', '#E8E1CF', '#FFFBEF'], '#2A2822')
_r('mist',      ['#33505E', '#5E8394', '#AFC9D1', '#D9EBEF', '#F6FDFD'], '#15252D')
_r('red',       ['#4D1624', '#8C2A38', '#D44B4E', '#F2826A', '#FFC9A8'], '#24080E')
_r('qi',        ['#0B3B52', '#166E8C', '#32BED1', '#8AEBEE', '#E2FFFB'], '#05202D')
_r('violet',    ['#2A1B48', '#51398A', '#9B78D1', '#C9AEF2', '#F2E7FF'], '#140C26')
_r('hollow',    ['#384246', '#5A676D', '#87949A', '#BFCACD', '#EEF3F2'], '#171D20')
_r('iron',      ['#232C33', '#434F59', '#73828C', '#A9B7BD', '#E0EAEC'], '#0E1418')
_r('stone',     ['#252C31', '#3E4950', '#65727A', '#94A0A5', '#C8D0D1'], '#0F1416')
_r('warmstone', ['#2E2A27', '#4E4741', '#7A7064', '#A89C8A', '#D3C9B4'], '#141110')
_r('wood',      ['#35200F', '#5A391D', '#87592F', '#B5824B', '#DCB27A'], '#180D05')
_r('darkwood',  ['#1E130B', '#382415', '#5A3B22', '#80582F', '#A67B45'], '#0D0704')
_r('straw',     ['#55401C', '#8A6A2F', '#C29F56', '#E2CB85', '#FBEFC2'], '#241A0B')
_r('hemp',      ['#474034', '#736753', '#A5967A', '#CDBF9F', '#EDE3C9'], '#1D1A14')
_r('leaf',      ['#0E3322', '#1B5A36', '#35894A', '#72BD55', '#C2E68A'], '#061A10')
_r('moss',      ['#193322', '#2C5230', '#4E7F3B', '#86AE52', '#C8DC8A'], '#0C190F')
_r('bamboo',    ['#1C3A1C', '#2F6230', '#5A9A44', '#98C862', '#DDF0A0'], '#0C1C0C')
_r('copper',    ['#421D14', '#7C3A22', '#BD6937', '#E69A5A', '#FFD49B'], '#1E0C07')
_r('fire',      ['#5A1812', '#A6341C', '#EB6A28', '#FFB142', '#FFF19E'], '#260A06')
_r('ember',     ['#4E1410', '#8E2418', '#D2452A', '#F58A3A', '#FFD27A'], '#220806')
_r('flesh',     ['#4A1A1F', '#843236', '#BF594D', '#E69277', '#FFD0B2'], '#200A0C')
_r('bone',      ['#555043', '#8F8672', '#CDC4AA', '#EBE4D0', '#FFFEF4'], '#24211A')
_r('sky',       ['#27455F', '#4A7597', '#8BB5D2', '#C8E2F1', '#F4FBFF'], '#101E2A')
_r('ice',       ['#1D4A63', '#347FA0', '#6FC3DF', '#B7EEF7', '#F2FFFF'], '#0B2130')
_r('cloud',     ['#5E7385', '#8FA6B7', '#C5D5DF', '#E9F1F4', '#FFFFFF'], '#1E2A33')
_r('silver',    ['#3C4852', '#6A7A86', '#A6B5BF', '#D5E0E5', '#FAFFFF'], '#161D22')
_r('mistjade',  ['#28173F', '#482C72', '#7B55AE', '#B18DE2', '#E7D8FF'], '#120A20')
_r('plum',      ['#2A1330', '#4B2350', '#74397A', '#A060A2', '#D39AD0'], '#130816')
_r('navy',      ['#121C33', '#1F2F52', '#34497A', '#5670A6', '#8FA7D2'], '#070B16')
_r('indigo',    ['#1A2238', '#2B3858', '#46587E', '#6D82A8', '#A2B5D2'], '#0A0E18')
_r('leather',   ['#2A1810', '#4A2B1A', '#704226', '#9A6238', '#C48C58'], '#130A06')
_r('clay',      ['#3F2317', '#6B3A24', '#9C5A35', '#C98A55', '#E8B889'], '#1C0E08')
_r('porcelain', ['#5A6C74', '#93A8B0', '#D4E0E0', '#F0F5F0', '#FFFFFF'], '#1C2529')
_r('fur',       ['#2E221A', '#4F3B2B', '#76593F', '#A2805A', '#C9A77C'], '#140E0A')
_r('greyfur',   ['#2D3336', '#4B5559', '#737F83', '#A1ABAD', '#CED5D4'], '#121618')
_r('rice',      ['#6A6456', '#A69E88', '#E0D9C4', '#F5F0E0', '#FFFFFA'], '#2A271F')
_r('broth',     ['#4F2A12', '#83491E', '#B8742E', '#DCA24E', '#F4D38A'], '#231105')
_r('tea',       ['#3A3A12', '#5E5F1E', '#8C8C35', '#B8B85C', '#E1E09A'], '#191A07')
_r('pink',      ['#5A2A40', '#9A4A6A', '#D98AA6', '#F4BCCD', '#FFE6EE'], '#2A1220')
_r('lotuspink', ['#6A3552', '#B0628A', '#E7A0BE', '#F8D2E0', '#FFF1F6'], '#2E1424')
_r('yellow',    ['#5E4A10', '#9C7C1C', '#E0B92E', '#F8E070', '#FFF8C8'], '#281F06')
_r('seal',      ['#4A0E14', '#861C22', '#C8322E', '#EE5F48', '#FF9E80'], '#200608')
_r('talisman',  ['#6A5316', '#A88A2E', '#E3C659', '#F6E28E', '#FFF6CC'], '#2A200A')
_r('pearl',     ['#6B6478', '#A39DB3', '#DAD6E6', '#F2F0F8', '#FFFFFF'], '#26232E')
_r('scale_green', ['#123524', '#1F5A3A', '#3A8C5A', '#6CC08A', '#B8EAC4'], '#07180F')
_r('eel',       ['#1C2A22', '#304536', '#4E6A4E', '#7E9A6C', '#B8CC98'], '#0B120D')
_r('salmon',    ['#5A1E1E', '#9C3A32', '#D9664A', '#F59A6E', '#FFD0A8'], '#260C0B')
_r('toad',      ['#2E3A14', '#4E6020', '#7A8C34', '#AABB5C', '#D8E498'], '#141A08')
_r('venom',     ['#233410', '#3E5E14', '#6E9A1E', '#A8D23E', '#E2F88A'], '#101806')
_r('oil',       ['#4A3208', '#8A5E12', '#C9922A', '#EDC25C', '#FFEBA8'], '#201404')
_r('ink',       ['#05090C', '#0D161C', '#1A2830', '#2E424C', '#4E6670'], '#020405')
_r('shadow',    ['#120E1E', '#231B36', '#3A2E56', '#5D4C82', '#8E7BB6'], '#07050D')
_r('storm',     ['#1E2C4A', '#35507E', '#5A82B8', '#95BCE6', '#E0F2FF'], '#0B1224')
_r('sand',      ['#4E3A22', '#7C6038', '#AE8D58', '#D6BA82', '#F2E0B4'], '#211709')
_r('earth',     ['#36220F', '#5C3A18', '#8C5E2A', '#BC8A48', '#E2BB78'], '#170E05')
_r('mud',       ['#2A2016', '#46362A', '#665240', '#8C765E', '#B39E84'], '#110C08')
_r('wax',       ['#5C5140', '#9A8A66', '#D8C79A', '#F0E4BE', '#FFFBEA'], '#262116')
_r('cyan',      ['#0B3B52', '#166E8C', '#32BED1', '#8AEBEE', '#E2FFFB'], '#05202D')
# Act II · Starsea: comet iron, a pale blue-grey metal (ingot and the storm sloop's keel)
_r('cometiron', ['#2C3A4E', '#52667E', '#8FA3BA', '#CAD8E6', '#F4FAFF'], '#111A26')
# Act III · Lantern Star Field: fallen starlight, pale gold (#F3E3A6) to star-white, its shadows drifting to
# night indigo; lantern bronze, the metal of the star cages
_r('starlight', ['#5E4C74', '#C49A56', '#EACA76', '#F3E3A6', '#FFFBEA'], '#211A31')
_r('lanternbronze', ['#3A2416', '#6A4222', '#A8703A', '#D8A25A', '#F4D494'], '#1A0F08')
STAR_GLOW = '#F3E3A6'

# Weapon / armour grade material sets --------------------------------------------
_r('jadeiron',  ['#132B26', '#21483E', '#377061', '#5FA38A', '#A8DCC0'], '#08140F')
_r('cloudsteel', ['#2A4760', '#4D7797', '#8BB4D0', '#C8E2F1', '#F6FCFF'], '#101D29')
_r('mistjade_m', ['#26163E', '#452B70', '#7552AA', '#AC89DE', '#E4D4FF'], '#110A1E')
_r('silk_navy', ['#18233A', '#26385A', '#3C5584', '#6180B4', '#98B2DC'], '#080C16')
_r('violetsilk', ['#24163A', '#3E2764', '#5E3F94', '#8A6AC0', '#BCA4E6'], '#0F0819')

GRADE_ORDER = ['plain', 'common', 'earth', 'heaven', 'mystic', 'spirit', 'sage']

GRADES = {
    'plain': {
        'metal': R['wood'], 'metal2': R['wood'], 'grip': R['hemp'], 'wrap': R['hemp'],
        'accent': R['straw'], 'gem': None, 'glow': None, 'cloth': R['hemp'],
    },
    'common': {
        'metal': R['iron'], 'metal2': R['iron'], 'grip': R['leather'], 'wrap': R['darkwood'],
        'accent': R['bronze'], 'gem': None, 'glow': None, 'cloth': R['indigo'],
    },
    'earth': {
        'metal': R['jadeiron'], 'metal2': R['iron'], 'grip': R['leather'], 'wrap': R['deepjade'],
        'accent': R['bronze'], 'gem': R['jade'], 'glow': None, 'cloth': R['deepjade'],
    },
    'heaven': {
        'metal': R['cloudsteel'], 'metal2': R['silver'], 'grip': R['silk_navy'], 'wrap': R['silk_navy'],
        'accent': R['silver'], 'gem': R['qi'], 'glow': None, 'cloth': R['sky'],
    },
    'mystic': {
        'metal': R['mistjade_m'], 'metal2': R['mistjade_m'], 'grip': R['violetsilk'], 'wrap': R['plum'],
        'accent': R['gold'], 'gem': R['violet'], 'glow': '#B18DE2', 'cloth': R['mistjade'],
    },
    # Spirit grade (Azure Expanse, Sage realm): stormsteel - storm-blue steel, silver fittings, cyan spark
    'spirit': {
        'metal': R['storm'], 'metal2': R['silver'], 'grip': R['navy'], 'wrap': R['navy'],
        'accent': R['silver'], 'gem': R['cyan'], 'glow': '#7FD4FF', 'cloth': R['storm'],
    },
    # Sage grade (Sunscar): sunsteel, gold worked with desert glass; sunsilk in ochre and vermilion.
    'sage': {
        'metal': R['gold'], 'metal2': R['sand'], 'grip': R['clay'], 'wrap': R['red'],
        'accent': R['jade'], 'gem': R['ember'], 'glow': '#FFC870', 'cloth': R['sand'],
    },
}
