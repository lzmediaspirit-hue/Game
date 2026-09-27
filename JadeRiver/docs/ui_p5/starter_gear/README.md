# The equip prompt and the tracker at Bone Forging 3

1280 × 720 as captured, reduced to 256 colours. Every picture is a brand-new character played by
`tests/tutorial_order.gd` with `XDG_DATA_HOME` in a scratch folder and `--keep="The Weapon Hall"` or
`--keep="Bone Forging 3"` (not the Max Test save), captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://tutorial_cp/<checkpoint>> --load-slot --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `equip_prompt_empty_slot.png` | the_weapon_hall | `--give=training_spear` | A piece for an empty slot: the card at the right, under the purse and clear of the ring, with the icon, "Empty weapon slot", the name, the gain the Bag's card names first (Qi attack) and Combat Power, Equip and ×; the time left drains along its foot |
| `equip_prompt_better.png` | the_weapon_hall | `--give=hemp_robe:1:perfect` | A piece better than the one worn (a Perfect Hemp Robe over the plain one): "Better than your robe", Max HP and Combat Power |
| `tracker_bf3_weapon_hall.png` | bone_forging_3 | — | At Bone Forging 3, Fish-Gutting Fists done: the tracker's Next is The Weapon Hall (Talk to Master Kong) and the minimap's mark points west toward it, where it pointed to the hunt for Level 4 at Willow Path West |

## The first weapon

Starter gear (`grades.json` `drop.starter`): the same way, from `--keep="Crab Trouble taken"` (Crab Trouble just
taken, in the Reed Shallows, Guo's training gauntlets worn). `--pick-up[=s]` and `--equip=item` are debug tools like
the others (the pick_up and equip intents).

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `first_weapon_drop.png` | crab_trouble_taken | `--defeat-foe=2 --hold=1.0:rare_drop` | The first kill in the first rooms drops the first weapon, a Training Short Blade: the "Your first weapon" strip and the beam over the piece |
| `first_weapon_equip_prompt.png` | crab_trouble_taken | `--defeat-foe=2 --pick-up=2.2` | Picked up: the log says so and the equip prompt offers it, better than the gauntlets (Soul attack and Combat Power up), with Equip |
| `character_first_weapon.png` | crab_trouble_taken | `--defeat-foe=2 --pick-up=1.5 --equip=training_short_blade --open-page=character` | Worn: the Character page's weapon slot holds it and the figure carries it; physical attack 12, the par character's at Level 1 |
