"""The top-down character (redesign Phase 3, decision 32): the game's real character, redrawn for the 3/4 top-down view.

The figure is modelled as a small 3D doll (a skeleton posed per frame, clothed in solid primitives), ray-cast at 1 art
px per pixel through a fixed orthographic camera, cel-shaded into each material's ramp and outlined as the art bible
asks. Every layer (body, hair, shirt, trousers, shoes, gauntlets, weapons) is cast from the same pose, so layers stay
registered to the body in every action and facing (AGENTS.md rules 1-4). See tools/art/topdown/build_character.py.
"""
