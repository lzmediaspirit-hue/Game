"""Icon registry: every icon is a function returning a finished `pix.Canvas`."""

# family folder -> art canvas size (art px); exported at x2
FAMILY_SIZE = {
    'items': 32,
    'equipment': 32,
    'techniques': 32,
    'hud': 16,
    'status': 12,
    'markers': 12,
}

REGISTRY = {}   # id -> dict(family, group, fn)
ORDER = []      # registration order (used for contact sheets)


def register(family, ident, fn, group=None):
    if family not in FAMILY_SIZE:
        raise ValueError('unknown family %s' % family)
    if ident in REGISTRY:
        raise ValueError('duplicate icon id %s' % ident)
    REGISTRY[ident] = {'family': family, 'group': group or family, 'fn': fn}
    ORDER.append(ident)


def icon(family, ident, group=None):
    """Decorator form: @icon('items', 'willow_moss', 'herbs')."""
    def deco(fn):
        register(family, ident, fn, group)
        return fn
    return deco
