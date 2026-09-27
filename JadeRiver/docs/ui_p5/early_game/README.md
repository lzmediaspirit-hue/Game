# Early surprises (player_motivation.md item 7)

Two pictures from a brand-new character, never the Max Tester: `tests/tutorial_order.gd` plays the walk with its own
saves (a private `XDG_DATA_HOME`) and keeps the checkpoints `The River Token` and `First Spirit Fruit`
(`--keep="The River Token,First Spirit Fruit"`). Each shot loads one (1280 × 720, reduced to 256 colours):

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://tutorial_cp/<checkpoint> --load-slot --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `lucky_encounter.png` | the_river_token | `--room=lf_village --at=250,850 --auto-path=wp_east --wait=4` | The first walk through the West Gate onto the Willow Path: the sure first fortune card, the Remnant Soul in a Ring, its three manual pages in the log |
| `spirit_fruit_tree.png` | first_spirit_fruit | `--room=wp_west --at=1960,850 --wait=1` | The Willow Path done: the first Spirit Fruit ripe on its tree on Willow Path West, "Reach for it" on the context button (its guardian wakes) |
