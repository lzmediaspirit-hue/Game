"""One data-driven generator per layer kind. Each takes a skeleton and a spec from a set (figure/sets/) and returns the
solids that layer is cast from, so every look of a kind is a few numbers in its set:

  torso  shirts, coats, robes      legs   trousers          feet   shoes, boots          head   hats
  back   capes                     hands  gauntlets         hair   hair styles
  blade  a blade in the hand (short blade, jian)            pole   a pole in the hands (spear, staff)

A weapon family with a shape of its own gets its own generator here, kinds/<family>.py, using figure/weapons.py for
how it is held: sabre, fan, brush, flute, bell (the flute and the bell ring with sound.py) and bow.
"""
