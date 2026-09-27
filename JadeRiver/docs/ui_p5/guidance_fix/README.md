# Guidance fix (docs/tutorial_order.md, CHANGELOG "Guidance")

Screenshots from a brand-new character: **Tester** as `tests/tutorial_order.gd` plays it, fists-first, saved at points
of its walk with `--keep="Morning Tide teas,Granny's Remedy taken,Both recruiters met,Crab Trouble,A Disciple's Chores"`
(to `user://tutorial_cp/<point>/`, in a scratch `XDG_DATA_HOME`); one from the `qu1` checkpoint `tests/valley_run.gd`
writes as it plays the story (Qi Unfurling 1). None uses the Max Test character, `--max-character` or `--unlock-all`.
1280 × 720 as captured, reduced to 256 colours. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://tutorial_cp/<point> --load-slot <extra> --capture --shot=<name>
```

| Picture | Point | Extra arguments | What it shows |
|---|---|---|---|
| `sect_chosen.png` | both_recruiters_met | `--talk=recruiter_qing_lan --tap=640,600 --tap=640,600 --tap=1032,536` (Join the Jade Sect) | The moment after the sect choice: the fair completed, the Entry Trial under way at the head of the tracker ("➤ Hunt at Willow Path West", "Reach Bone Forging 2"), its go button, the minimap's mark on the east edge toward the Willow Path; the log records the membership (the Jade Current Scripture, the Jade Token) |
| `gap_next_giver.png` | a_disciples_chores | — | Between two main quests (A Disciple's Chores done, Fish-Gutting Fists not taken): "◇ Next: Fish-Gutting Fists", "➤ Fairground · Stoneford", "Talk to Shen Lian", the go button, the mark on the minimap's west edge toward the Fairground |
| `gap_next_level.png` | valley_run `qu1` | `--load=user://valley_cp/qu1` | Between main quests, waiting on a Level: "◇ Next: The Shrine Surfaces", "Reach Level 21 (Qi Unfurling 3)", "➤ Hunt at Bend Shore", the go button and the mark toward it |
| `quick_use_asked.png` | grannys_remedy_taken | — | Granny's Remedy just taken, at rest: the Quick-use slot drawn empty beside the attack button, glowing and named "Quick-use", as the steps say ("Bag: put Herbal Tea in Quick-use", "Drink a Herbal Tea: tap Quick-use") |
| `hut_door_held.png` | morning_tide_teas | `--room=lf_fishers_hut --at=660,700 --wait=4` | Morning Tide with the teas taken and the Bag not yet opened: the hut's door drawn shut, its plate saying "Before you go: Open your Bag" (a try to leave says the same); the teas stay taken after the reload |
| `fight_by_herb.png` | crab_trouble | `--room=lf_reed_shallows --at=790,700` | Reedtail Rats within the fight range beside a Willow Moss patch in the Reed Shallows: the attack button keeps the fist and attacks, the herb's Gather waits in the context slot on ring 2 |
| `tea_at_rest.png` | grannys_remedy_taken | `--use-item=herbal_tea:0.5` | The Herbal Tea tapped from Quick-use at rest at half HP: "+21 HP" over the player, the heal still to come in pale jade on the HP bar, the tea's icon with "5 s" in the status row, the log line "Herbal Tea: +21 HP over 5 s" (before the log is revealed) |
| `tea_full_hp.png` | grannys_remedy_taken | `--use-item=herbal_tea` | The prologue's case, the tea at full HP: "HP already full" over the player and in the log line, the heal still running under the tea's icon |
| `tea_in_fight.png` | crab_trouble | `--room=lf_reed_shallows --at=790,700 --use-item=herbal_tea:0.4` | The tea in a fight beside the Reedtail Rats: "+21 HP", the bar's pale jade run, the tea's icon with its seconds, the log line |
