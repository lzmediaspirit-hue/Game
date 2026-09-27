"""Icon registry: every icon is a function returning a finished `pix.Canvas` (legacy) and, once its family is
being converted, an HD drawing `draw(p)` painted by a `pix.PixelPainter` (see README, "How to convert a family").

A family module (families/<name>.py) declares its art size in `ART`: the legacy size of its folder (FAMILY_SIZE)
until every icon in it has an HD drawing, then the HD size (HD_SIZE). The build follows it: a legacy family
builds its legacy canvases exactly as before; an HD family builds its HD drawings at 1:1 plus the native
renders in VARIANTS, and a missing HD drawing in it is an error, so a family converts whole.
"""
import sys

# family folder -> legacy art canvas size (art px); exported at x2
FAMILY_SIZE = {
    'items': 32,
    'equipment': 32,
    'techniques': 32,
    'hud': 16,
    'status': 12,
    'markers': 12,
}
# family folder -> HD icon-space size (art px), exported 1:1
HD_SIZE = {'items': 64, 'equipment': 64, 'techniques': 64, 'hud': 32, 'status': 24, 'markers': 24}
# family folder -> the native renders an HD icon also gets, as `<id>@<px>.png`: 48 for the HUD technique ring,
# 32 for the HUD item rings and the pages' small slots, 12 for the status icons over an enemy's name
VARIANTS = {'items': (32,), 'equipment': (32,), 'techniques': (48, 32), 'hud': (), 'status': (12,), 'markers': ()}

REGISTRY = {}   # id -> dict(family, group, fn, module)
ORDER = []      # registration order (used for contact sheets)
HD = {}         # id -> HD drawing draw(p)


def register(family, ident, fn, group=None):
    if family not in FAMILY_SIZE:
        raise ValueError('unknown family %s' % family)
    if ident in REGISTRY:
        raise ValueError('duplicate icon id %s' % ident)
    REGISTRY[ident] = {'family': family, 'group': group or family, 'fn': fn, 'module': fn.__module__}
    ORDER.append(ident)


def icon(family, ident, group=None):
    """Decorator form: @icon('items', 'willow_moss', 'herbs')."""
    def deco(fn):
        register(family, ident, fn, group)
        return fn
    return deco


def drawn(family, ident, group=None):
    """Decorator for an icon that is only an HD drawing (a converted family's new icons): registers the drawing as
    both the icon and its HD drawing. `@drawn('status', 'burn')`."""
    def deco(draw):
        register(family, ident, draw, group)
        hd(ident, draw)
        return draw
    return deco


def hd(ident, fn=None):
    """Give icon `ident` its HD drawing: `hd('healing_pill', draw)` or `@hd('healing_pill')`."""
    def put(f):
        if ident in HD:
            raise ValueError('duplicate HD drawing %s' % ident)
        HD[ident] = f
        return f
    return put(fn) if fn is not None else put


def module_name(ident):
    """The family module an icon belongs to ('pills', 'weapons', ...)."""
    return REGISTRY[ident]['module'].rsplit('.', 1)[-1]


def art_size(ident):
    """The art size the icon builds at: its module's ART (the folder's legacy size when it declares none)."""
    e = REGISTRY[ident]
    return getattr(sys.modules[e['module']], 'ART', FAMILY_SIZE[e['family']])


def is_hd(ident):
    e = REGISTRY[ident]
    size = art_size(ident)
    if size not in (FAMILY_SIZE[e['family']], HD_SIZE.get(e['family'])):
        raise ValueError('%s: ART = %s, expected %s (legacy) or %s (HD)' % (ident, size, FAMILY_SIZE[e['family']], HD_SIZE.get(e['family'])))
    return size == HD_SIZE.get(e['family'])
