# Tutorial order fix (docs/tutorial_order.md)

Screenshots from a brand-new character: **Tester** as `tests/tutorial_order.gd` plays it, fists-first, saved after two
of its steps with `--keep="A Quiet River,Crab Trouble"` (to `user://tutorial_cp/a_quiet_river/` and `crab_trouble/`,
in a scratch `XDG_DATA_HOME`). None uses the Max Test character, `--max-character` or `--unlock-all`. 1280 × 720 as
captured, reduced to 256 colours. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://tutorial_cp/<step> --load-slot <extra> --capture --shot=<name>
```

| Picture | Step | Extra arguments | What it shows |
|---|---|---|---|
| `first_fight_rats.png` | crab_trouble | `--room=lf_reed_shallows --at=1330,780 --wait=2` | The first room with foes, open since Crab Trouble: the HP bar on the player panel, and the two Reedtail Rats that turned on the player showing their HP bars before either is hurt (the others, idle, show only their names) |
| `old_ma_store_door.png` | a_quiet_river | `--room=lf_village --at=1720,860 --wait=1` | Old Ma's Store with its door in the right bay under a blue shop curtain, the arrow over it and its plate drawn above the facade |
| `quest_offer_old_ma.png` | a_quiet_river | `--room=lf_old_ma_store --at=790,770 --talk=old_ma --tap=1032,536` (three taps) | Old Ma offering Ma's Delivery on the dialogue page |
| `quest_accepted_talk_closed.png` | a_quiet_river | the same with a fourth tap, on Accept | The talk closed by itself on accepting (no Farewell to tap): the quest and "New: Coins and Shops" toasts, the purse, the tracker |
