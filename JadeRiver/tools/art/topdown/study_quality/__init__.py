"""Decision 42's character-quality study: the player and the villagers drawn three or four ways, for the user to choose.

This is a study, not the game's pipeline. Nothing here is read by the game or by build_character.py; the shipped
sheets, manifests and code paths stay as they are. It reuses the Phase 3 doll (figure/: skeleton, poses, generators,
palettes) unchanged and draws it with a new rasteriser:

  hifi.py       the rasteriser: the doll cast at several samples per pixel, shaded in seven-step hue-shifted ramps
                under the §14 sun, rim-lit, selectively outlined (tinted, lighter on the lit side, lighter inner lines),
                its stair-steps anti-aliased within the pixel style; faces stamped from hand-drawn glyphs
  looks.py      the study's subset and its hand-tuned detail: hair clusters and sheen, cloth folds, the faces' glyphs
  options.py    the options: B (38 px, the world's density), C (76 px, twice the density), D (48 px, the world's
                density)
  build_study.py  writes each option's sheets and index in the game's own format into study_quality/build/ (ignored
                by git and by Godot)
  study_capture.gd / .tscn  shoots the scenes in the game with its own compositor (TopdownFigure) on those sheets
  compose.py    the side-by-side boards, the close-ups and the animated strips in docs/redesign/feedback/

The write-up is docs/redesign/feedback/character_quality.md.
"""
