# Visibility fix (CHANGELOG "Visibility")

Before and after pictures of the worst cases `tests/visibility_suite.gd` found. Each was captured from the same copy
of the `ae6` checkpoint that `tests/valley_run.gd` writes as it plays the story, run in a scratch `XDG_DATA_HOME`.
None uses the Max Test character, `--max-character` or `--unlock-all`. "Before" is the build before the fix. They
are 1280 × 720 as captured and reduced to 256 colours. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://valley_cp/ae6 --load-slot <extra> --wait=1 --capture --shot=<name>
```

| Pictures | Extra arguments | What it shows |
|---|---|---|
| `west_gate_before/after.png` | `--room=lf_village --at=260,840` | The village's West Gate to the Willow Path: before, only its plate showed (an open `gate` way drew no art). After, the road gate stands at the room's west edge. The cooking pot on the Fisher's Hut roof shows too; before, it drew behind the roof. |
| `hut_loft_float_before/after.png` | `--room=lf_fishers_hut --at=760,760` | Lu's float in the hut loft: before, it drew behind the loft's deck. After, it lies on the loft (`ObjectView.depth`, `ZoneGeometry.depth_at`). |
| `cave_entry_door_before/after.png` | `--room=wg_waterfall_cave --at=360,800` | The Waterfall Cave's way back out to the Rapids Terraces: before, only its plate showed. After, a door stands at it. The things set on the cave's ledges show too. |
| `hermit_deck_before/after.png` | `--room=rm_hermit_stilt_house --at=760,830` | The stilt house's stairs way (now a door) and the hermit's tea pot on his deck, which drew under the deck's planks before. |
