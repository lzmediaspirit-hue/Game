# Moments: screenshots

In-game captures of the moments system (`docs/moments_design.md`, roadmap P6), taken on the build that closes P6 from
`valley_run` checkpoints (`user://valley_cp/<section>`), at 1280×720 with the capture renderer. Each is reproducible with
`godot --path . -- <flags> --capture --shot=<name>`.

| Shot | Row | Checkpoint and flags |
|---|---|---|
| `breakthrough_major_1.0s.png` | `breakthrough_major`, the band and seal being written (mockup 05, beat 2) | `ae1`: `--load-slot --breakthrough=1.0` |
| `breakthrough_major_2.4s.png` | `breakthrough_major`, the full frame: band, seal, the stats that rose (mockup 05, beat 3) | `ae1`: `--load-slot --breakthrough=2.4` |
| `breakthrough_minor.png` | `breakthrough_minor`, the step and Level on the slim strip | `ls6`: `--load-slot --breakthrough=0.9` |
| `breakthrough_failed.png` | `breakthrough_failed`, why and how to recover | `ls6_end`: `--load-slot --moment=breakthrough_failed:0.8` |
| `tribulation.png` | `tribulation`, the band under the shadowed sky | `ls6_end`: `--load-slot --moment=tribulation:0.9` |
| `boss_intro.png` | `boss_intro`, Big Toad Tan turning on you in his den | `ls6_end`: `--load-slot --room=mh_boss_den --at=1560,840 --hold=1.0 --wait=4` |
| `boss_phase.png` | `boss_phase`, the numeral card under the boss bar at his 49% | `ls6_end`: `--load-slot --room=mh_boss_den --at=1300,840 --hold=0.6:boss_phase --foe=big_toad_tan:1:0.49` |
| `boss_defeated.png` | `boss_defeated` with the Untouched line; a rare find's beam at the right | `ls6_end`: `--load-slot --room=mh_boss_den --at=1250,840 --hold=1.2:boss_defeated --defeat-foe=4` |
| `loot_fountain.png` | `loot_fountain`, his real drop in flight 0.55 s after the fall | `ls6_end`: `--load-slot --room=mh_boss_den --at=1850,860 --hold=0.55:loot_fountain --defeat-foe=4` |
| `title_earned.png` | a progression card: a title, with its seal | `ls6_end`: `--load-slot --moment=title_earned:1.0` |
| `dao_tier.png` | a progression card: a Dao tier with its line | `ls6_end`: `--load-slot --moment=dao_tier:1.0` |
| `weapon_awakened.png` | a progression card: a weapon awakened | `ls6_end`: `--load-slot --moment=weapon_awakened:0.6` |
| `rare_drop.png` | `rare_drop`, the strip naming the find in its colour | `ls6_end`: `--load-slot --moment=rare_drop:1.0` |
| `story_beat.png` | `story_beat`, a chapter closing | `ls6_end`: `--load-slot --moment=story_beat:1.2` |
| `trial_opens.png` | `trial_opens`, the band in pale gold | `ls6_end`: `--load-slot --moment=trial_opens:0.8` |
| `escalation.png` | the escalation curve (§5): one technique per tier on three Wild Boarlets, Cursive Storm's rain and four stacked hits with their total, Flying Blades' three hits and total | `qk5`: `--load-slot --room=wp_east --at=180,760 --foe=wild_boarlet:3 --cast=<technique>:<t>` (t 0.02, the rain 0.3, the total 0.45; a side-view picture, the flag gone in S12a) |

`--moment` plays a row with its sample payload; `--breakthrough`, `--defeat-foe` and the den's aggro are the real path;
`--cast` draws a technique's cast and hits at its tier without submitting anything. The ink band reads faintly over the
dark cave; its words carry the moment there.
