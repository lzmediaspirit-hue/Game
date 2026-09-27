# The HUD after P5a

The play screen rebuilt to the approved mockups 01 (a fight) and 02 (at rest) (`docs/roadmap_master_ui.md` P5a, rows
G3, G4 and U28; decision 20, the toggles in the fan; `docs/ui_style_guide.md` §9 "As built"), and the world's name
labels laid out so they never stack (G4). Captured on this build, 1280 × 720, reduced to 256 colours; `.gdignore`
keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from copies of its checkpoints: `ls6_end`
(Sphere Lord 3, Lv 98), `ae_end` (Sage Sovereign 3, Lv 80), `qu5` (Qi Unfurling 4 at its bottleneck, Lv 22) and `bf2`
(Bone Forging 2, Lv 2), taken from this build's own `valley_run` into a separate user folder and loaded through
`--load`, which plays from a further copy. None uses `--unlock-all`, `--max-character` or the Max Test character.
Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://<folder>/<checkpoint> --load-slot <extra> --capture --shot=<name>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `hud_fight.png` | `ls6_end` | `--room=ar_ashborn_palisade --at=1500,840 --foe=ashborn_raider:2 --toggle=presence --wait=2` | A fight in the Ashborn Palisade: ring 1 out (jump, four techniques, dodge) with the "1/2" page tab; the fan closed with the held Presence pinned beside it (its Soul upkeep arc and level 5); the healing slot (Herbal Tea, none left); the party's HP lines over their heads in rows; the foes' labels in rows; the Hollowing meter; the log above the joystick's half, fitted with an ellipsis |
| `hud_rest.png` | `ls6_end` | `--room=lh_harbor_market --at=900,850 --wait=1` | Mockup 02's place, the Harbor Market beside Peddler Ning: the techniques folded into four beads on the attack ring, which is "Talk · Peddler Ning"; the fan open on its paper with all five toggles named; the healing slot resting; no party labels at rest; the Hollowing "46 ▼ lanterns"; Ning's plate lifted over her head because the open fan covers the rows under her feet |
| `hud_rest_fan_closed.png` | `ls6_end` | as `hud_rest`, with `--fan=closed --toggle=presence` | The same at rest with the fan closed: the Presence that is on stands pinned beside it (decision 20), and Ning's plate is back under her feet |
| `hud_rest_bottleneck.png` | `qu5` | none | At the bottleneck (mockup 02's state): the progress edge glowing gold, Stored Qi as a bright lane and "◆ Bottleneck reached · breakthrough ready · tap Cultivate"; Cultivate lit gold in the open fan; the ready seal on Menu; the tracker with its 48 px go button; two beads for the two techniques |
| `hud_boss.png` | `ls6_end` | `--room=ar_kharns_pyre --at=1100,840 --foe=general_kharn:1:0.47 --foe=ashborn_raider:1 --toggle=presence --wait=4` | Mockup 01's fight: General Kharn at 47%, "phase 2 of 3", the 60% notch passed ("Ashborn Pyre Keeper called ✓") and the 30% one lit next ("Enrage"); the purse resting in the arena; the held Presence pinned; the toasts under the boss bar |
| `hud_town.png` | `ae_end` | `--room=sf_artisan_row --at=1250,860 --wait=1` | A dense town, Artisan Row, nine NPCs (Elder Gu and Madam Hua share one spot): every plate drawn over the figures and none touching; the three with no free row under their feet (under the open fan, under the attack button, over another plate) lifted over their heads |
| `hud_early.png` | `bf2` | `--room=sf_fairground --at=1040,850 --wait=1` | Early, few unlocks: the HP bar alone, one status, "Talk · Qing Lan", the fan with Cultivate only (the paper still opens like a fan), no technique ring or beads; the three Festival Lantern plates in rows |
| `hud_early_fight.png` | `bf2` | none | The Entry Trial against the Trial Puppet: the fist, the fan folded, jump, the healing slot; nothing else is revealed yet |
| `compare_01_fight.png` | | | Mockup 01 at the left, `hud_boss.png` at the right |
| `compare_02_rest.png` | | | Mockup 02 at the left, `hud_rest.png` at the right |
| `compare_02_rest_bottleneck.png` | | | Mockup 02 at the left, `hud_rest_bottleneck.png` at the right |

## Beside the mockups

Compared side by side, and fixed while comparing:

- An NPC's plate that had no free row under the open fan was sent below the screen: a row that leaves the screen now
  costs dearly, and a plate under the feet goes over the head instead.
- Plates were hidden behind figures standing in front of them: labels now draw above every figure.
- The three pickup plates in the Fairground overlapped: the plates of ways and things join the layout pass.
- The otter's chip read "Reed…": a name too long for its chip gives its last word ("Otter", as mockup 01 has it).
- A wounded animal's chip showed an empty arc: a wound is a full red ring.
- With two Kharns in the arena the bar followed the one not fighting: it follows the boss furthest into its fight.
- The 30% caption was dropped when the summons' long name took its room: a caption leans away from its neighbour.
- A log line was clipped without an ellipsis: outlined words are measured in the face they are drawn in.
- A fan with one toggle was a sliver of paper: the paper spans at least 40°.

Left as the data has them, not the HUD: the attack glyph is the weapon in hand (a jian here, the brush in the
mockup); the healing slot holds the save's quick-use item (Herbal Tea, none left, dimmed with a red 0) where the
mockup has six Healing Pills; no treasure is set in the save, so none is drawn; the debug `--foe` sets foes five
Levels above the player (Kharn Lv 103), and the arena's own Kharn stands at the right; `ls6_end` is not at a
bottleneck, so the bottleneck is shown from `qu5`; the "Drowned Shrine Surfaces" toast is the live world event on
loading. As before P5a, the joystick's ring shows only under a thumb.

What to look for: the lower middle clear round the player in every picture; no label touching another or sitting under
a control; the fan open at rest and folded in a fight; empty slots not drawn; every control at least 48 px to the
touch (checked by `rules_tests` `hud_suite`, which also holds the cluster to the mockups' points and the clear zone;
`labels_suite` checks the label layout).
