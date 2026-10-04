"""The Nebula Deep's foes (M4; the Nebula Verge, the Eel Currents, the Crab Grottoes and the Leviathan's Maw, levels
94-99): the void crabs, the nebula eels and the Nebula Leviathan."""
from content.monsters import species

# M4. A crab of the Lantern Star Field whose carapace is a window onto the void (black-violet chitin, a silver rim, a pale
# violet underside; a black sky in its shell with a nebula swirl and stars in it), one great claw, glowing white-violet
# eyes. It raises its claws high as space tears round them (the tell, held: its blink claw's too) and slams them shut
# before it with a flash at the pinch; beaten, it flips onto its back and its stars go out.
species("void_crab", plan="crab.void", share=True, size=1.3,
        palette=["vc_chitin", "vc_silver", "vc_under", "vc_void", "vc_nebula", "vc_eye"], accents=("vc_void", "vc_nebula"), gold=("vc_eye",),
        shadow=(12, 4), cycle=10.0, sideways=True,
        data=dict(level=(94, 99), role="normal", element="space", page="lantern", drops=[("void_carapace", 0.45), ("star_shard", 0.5, (1, 3))],
                  attacks=[("void_pinch", 0.45, 70, 1.35, dict(depth=36)), ("blink_claw", 0.8, 240, 1.2, dict(dash=320, depth=40))],
                  ai="melee", speed=100, width=40, height=34, defence_mult=1.6, tameable=True),
        sound=dict(body="shell", tell="water"))
