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

# M4. A ribbon eel that swims the nebula's clouds: a deep teal ribbon of a body in an S-wave with magenta nebula clouds and
# stars over its back, translucent violet fins along its back and belly meeting in a paddle at its tail, a magenta crown,
# a wide hinged jaw of pale fangs, a glowing cyan eye. It coils back into a tight S as its jaws gape and its eyes flare
# (the tell, held: its current coil's too) and lunges straight to bite, a void ripple before its snout; beaten, it
# unravels from its tail into teal and magenta wisps.
species("nebula_eel", plan="serpent.ribbon", share=True, size=2.2,
        palette=["neel_teal", "neel_mag", "neel_fin", "neel_mouth", "neel_fang"], accents=("neel_mag",), shadow=(16, 4), cycle=14.0, view=True,
        data=dict(level=(94, 99), role="normal", element="water", page="lantern", drops=[("eel_essence", 0.45), ("star_shard", 0.5, (1, 3))],
                  attacks=[("space_bite", 0.45, 80, 1.3, dict(dash=180, depth=40)),
                           ("current_coil", 0.9, 160, 1.0, dict(damage_type="qi", pull=110, both_sides=True, depth=60))],
                  ai="flyer_ranged", speed=150, flying=True, width=40, height=28),
        sound=dict(body="slime", tell="water"))

# M4. The field boss of the Nebula Deep: a colossal sky whale-serpent, a vast whale head (a domed crown over a rostrum, an
# arched mouth fringed with ivory baleen, a pleated jaw, a small ancient gold eye) on a serpent body sweeping back (deep
# indigo, a star-white belly in pleats, teal and magenta nebula bands down its flanks, constellations of lights on its
# back), translucent violet veils off its throat, down its back and fanned at its tail. It rears its head back as its mouth
# gapes and the void gathers in it while star lines spiral in (the tell, held: its current swallow's and its gravity
# crash's too), and lunges to breathe the void, a cone of darkness full of stars; beaten, its lights go out one by one
# and it sinks and fades.
species("nebula_leviathan", plan="serpent.leviathan", share=True, size=2.6, elite=False,
        palette=["nlev_hide", "nlev_belly", "nlev_teal", "nlev_mag", "nlev_veil", "nlev_baleen", "nlev_mouth", "nlev_void"],
        shadow=(34, 8), cycle=20.0, view=True, canvas=(280, 230),
        data=dict(level=99, role="field_boss", element="space", page="lantern",
                  drops=[("leviathan_scale", 1.0, (2, 3)), ("star_shard", 1.0, (20, 30)), ("eel_essence", 1.0, (2, 4)), ("will_tempering_pill", 1.0, (2, 3))],
                  attacks=[("current_swallow", 1.2, 300, 0.9, dict(depth=110, damage_type="qi", pull=220, both_sides=True)),
                           ("void_breath", 1.3, 460, 1.8, dict(depth=100, damage_type="qi")),
                           ("gravity_crash", 1.0, 160, 1.6, dict(depth=90, knockback=140, status={"id": "stun", "chance": 0.4, "power": 1.0, "duration_s": 1.0}))],
                  ai="duelist", speed=90, flying=True, width=160, height=90, hp_mult=2.2, attack_mult=0.9, presence=5,
                  sphere={"element": "space", "tier": 5}, knockback_immune=True, name="Nebula Leviathan",
                  phases=[{"below": 0.6, "action": "summon", "summon": "nebula_eel", "summon_level": 97},
                          {"below": 0.3, "action": "enrage", "cooldown": 0.7, "damage": 1.3}]),
        sound=dict(body="slime", tell="water"))
