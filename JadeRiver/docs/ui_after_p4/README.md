# The UI after P4 (the style guide applied)

The pages and the HUD re-taken once the apply list of `docs/ui_style_guide.md` §11 had landed (§12 records it), for
comparison with the mockups (`docs/mockups/` 00–05) and with the P2 inventory's pictures (`docs/ui_inventory/`).
They are 1280 × 720 as captured, reduced to 256 colours; `.gdignore` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays through Acts I–III, from its last checkpoint
`ls6_end` (Sphere Lord 3, Sect Master of the Jade Sect, a sect of its own, a Reed Otter active, in the Wardens' Hall).
None uses `--unlock-all`, `--max-character` or the Max Test character. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://valley_cp/ls6_end --load-slot <extra> --wait=2 --capture --shot=<name>
```

| Pictures | Extra arguments |
|---|---|
| `hud_rest`, `hud_fight`, `hud_tracker`, `hud_pet_wheel` | none; `--foe=admiral_voss:1 --foe=scarlet_kiln_disciple:2`; `--guide-demo`; `--pet-wheel` |
| `menu`, `inventory`, `inventory_key`, `character`, `character_stats`, `character_wardrobe`, `characters` | `--open-page=menu`, `inventory[:key]`, `character[:stats\|wardrobe]`, `characters` |
| `cultivation`, `cultivation_body`, `cultivation_paths`, `cultivation_dao`, `cultivation_seclusion`, `breakthrough` | `--open-page=cultivation[:body\|vows\|dao\|seclusion]`, `breakthrough` |
| `techniques`, `quests`, `quests_daily`, `world_map`, `world_map_ranking`, `calendar` | `--open-page=techniques`, `quests[:daily]`, `world_map[:ranking]`, `calendar` |
| `codex`, `codex_collection`, `mail`, `shop`, `settings`, `settings_controls`, `relations` | `--open-page=codex[:collection]`, `mail`, `shop`, `settings[:controls]`, `relations` |
| `spirit_animals`, `your_sect`, `your_sect_expeditions`, `posts`, `works`, `training_sect` | `--open-page=spirit_animals`, `your_sect[:expeditions]`, `posts`, `works`, `training_sect` |
| `crafts`, `crafts_alchemy`, `crafts_forge` | `--open-page=crafts`, `alchemy`, `forge` |
| `dialogue` | `--talk=warden_commander_yao` |
| `welcome`, `teleport`, `exchange`, `mercy`, `gift`, `fates`, `beast_arena`, `core_exchange`, `pouches` | `--open-page=<id>`; `mercy:scarlet_kiln_warden`, `gift:aunt_ping`; `--offer-fates --open-page=fates` |

What to look for, against the mockups and the P2 pictures:

- **Words.** Primary labels and page titles carry the 2 px ink outline of option C on the bright jade (decision 10);
  every word sits on the type scale, none under 14; red words are `RED_TEXT`, violet `SOUL_TEXT`.
- **Windows.** Content sits 32 px in and 80 under the title, tabs are 48 tall; Welcome, Teleport, Exchange, Mercy,
  Gift, Fates, the Beast Arena, the Core Exchange and the Pouches use the standard windows; the dialogue strip sits
  inside the safe area.
- **Marks.** The character you play (Characters, Roll-Call), your Heaven Ranking row and the Body rung you climb carry a
  gold ◆ instead of the selection glow; Settings' toggles are on in the selected art, Off in `MIST`.
- **The Character page** draws the figure at 3x (6 screen px per art px) with the worn slots round it; the Bag keeps its
  2x figure between its slot columns, its grid 16 px from the detail panel.
- **The HUD.** The rings are the HD kit's `hud_ring`; the tracker's plate (`PLATE`, 0.72) sits under the status row, not
  over it; bar values read "a / b"; the log is outlined. The ring layout, party chips and boss bar of the mockups are
  P5a's.

Checked by eye for clipping, overlap and contrast. Found and fixed before this set was taken: the tracker's plate hid
the status icons; menu tile names touched their frames; a Welcome row's value ran into its label; the vow rows on the
Paths tab were shorter than their buttons. Left as they were, for P5a: an NPC's name over the world can sit under the
HUD's rings (G4), and the world map is still the region graph the approved painted map (mockup 16) replaces.
A capture runs on the real clock, so the Welcome page counts the few seconds since the checkpoint was loaded.
