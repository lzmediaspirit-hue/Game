# The first technique and the breakthrough card

1280 × 720 as captured. Every picture is a brand-new character played by `tests/tutorial_order.gd` with
`XDG_DATA_HOME` in a scratch folder and `--keep="The River Token,The Willow Path,The Weapon Hall"` (not the Max Test
save), captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://tutorial_cp/<checkpoint>> --load-slot --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `first_technique_moment.png` | the_river_token | `--moment=technique_learned:1.0` | On Lu's boat at Bone Forging 1: the `technique_learned` moment, "Flowing Palm · New technique · tap it on the skill ring"; the tracker already asks "Strike with Flowing Palm" on the Willow Path, and the jade aura ring is at the character's feet |
| `breakthrough_card_bf2.png` | the_willow_path | `--breakthrough=2.3` | Bone Forging 1 to 2: the strip and the card "What the breakthrough gave", each number that rose before → after with its gain (Level 1 → 2, Max HP 107 → 135 ▲28, Physical attack 7 → 10 ▲3 …) |
| `breakthrough_card_bf4.png` | the_weapon_hall | `--breakthrough=2.3` | Bone Forging 3 to 4 in the Weapon Hall: the same card, with the aura's change named on it (a jade ring → jade motes) |
