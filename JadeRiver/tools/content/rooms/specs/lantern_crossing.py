"""E1 room specs (R9): the Lantern Run's crossing, a Lanternfall skiff's deck on the Starsea between the Starsea Launch
and the Arrival Quay (docs/architecture/room_engine.md, "The star field's end (R9)"). The same kind of hull as the Wreck
Run's (`starsea.deck`), dressed as the lantern lanes' skiffs are: a fallen star in its bronze cage lashed amidships to
light the way, star lanterns along the rails, the cargo of a harbour run. The comet sparrows dive onto the bow; the
star jellyfish drift in over the forward waist."""
from content.rooms.specs.starsea import deck

SS_LANTERN_CROSSING = deck(
    "ss_lantern_crossing",
    props=[("storehouse", 7, 6), ("mast", 24, 11), ("lantern_cage", 34, 11), ("mast", 44, 11), ("star_lantern", 14, 6),
           ("star_lantern", 6, 16), ("star_lantern", 30, 6), ("star_lantern", 30, 17), ("star_lantern", 39, 6),
           ("star_lantern", 39, 17), ("star_lantern", 53, 7), ("star_lantern", 53, 16), ("crates", 18, 16),
           ("barrel", 20, 16), ("sacks", 21, 6), ("barrel", 22, 6), ("crates", 46, 6), ("sacks", 48, 16),
           ("barrel", 49, 16)],
    waves=[[(54, 11), (53, 13)],                                       # the comet sparrows
           [(47, 9), (49, 14)]])                                       # the star jellyfish

ROOMS = [SS_LANTERN_CROSSING]
