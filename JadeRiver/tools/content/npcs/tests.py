"""The NPC engine's own tests (engine.py --check runs them; docs/architecture/npc_engine.md, "The checks")."""
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def run():
    failed = []
    for fn in TESTS:
        try:
            fn()
        except Exception as e:  # noqa: BLE001  a test's failure, whatever it raised
            failed.append("test %s: %s: %s" % (fn.__name__, type(e).__name__, e))
    return len(TESTS), failed
