# Sprite and animation compatibility rules

These requirements apply to every item and animation added to this game.

1. A new item must be reviewed in every registered movement, idle, jump, attack,
   bow and meditation animation, for both facings and every supported dye.
   Check frame counts, timing, feet registration, hand grips, layer order and
   the occlusion outline. Provide matching sprites or a reviewed attachment rig;
   silently substituting idle equipment during another action is forbidden.
2. A new animation must be added to the action catalog and to every existing
   body, hair, shirt, pants, shoes and weapon layer. Author matching poses or a
   reviewed rig for all equipment before enabling the animation. Intentionally
   absent conditional layers need an explicit hidden entry, not a missing key.
3. Run the animation contract tests and inspect the rendered compatibility
   gallery. Numerical checks cannot certify visual alignment. Keep original
   artwork and nearest-neighbor pixel rendering. Avoid unused assets and caches;
   the user permits the source ZIP to exceed 30 MB when needed.
4. Every new movement animation starts from the main unclothed body sprite.
   Redraw the new movement on that body first and review its anatomy, feet,
   joints, timing and both facings. Then draw matching clothing, hair and
   equipment poses over the approved body frames. Do not derive a new body
   movement by deforming a clothed composite or use garment art as its base.
