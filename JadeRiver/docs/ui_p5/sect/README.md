# P5 · The sect family: Menu, Your Sect, Sect, Characters

Screenshots of the sect family built to its rows in `docs/page_identity.md` (4, 24, 25, 32) and its family in §2
(red-lacquered pillars and dark timber, bronze and red paper): the Menu beside its approved mockup `03_hub`, Your Sect
beside `11_your_sect`. The Sect and Characters have no mockup and follow their rows. They are 1280 × 720 as captured,
reduced to 256 colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of this build's own
valley_run checkpoints (run with `--cp=user://valley_cp/` under a scratch `XDG_DATA_HOME`, then copied): `ls6_end`
(Sphere Lord 3, Sect Master of the Jade Sect, the Reed Lantern Sect at level 1), `qu5`, `qk5` and `bf2`. None uses the
Max Tester save, `--max-character` or `--unlock-all`. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `menu.png` | ls6_end | `--open-page=menu` | The hall: five bays under their plaques between red pillars; Quests sealed (4 chests to claim), Techniques "Slots set: 8 / 8", Sect "Sect Master", Your Sect "3 ask to join" with the new mark, Mail's count and its sender; the character line and three purses on the floor |
| `compare_03_hub.png` | — | — | Mockup 03 above, `menu.png` below |
| `menu_early.png` | bf2 | `--open-page=menu` | Bone Forging 2: the locked tablets dim, each saying what opens it (Spirit Animals, Companions, Your Sect, Characters, Crafts, Workshop, Roll-Call, Works) |
| `your_sect.png` | ls6_end | `--open-page=your_sect` | The courtyard: the Sect Grounds from the room's own backdrop and props, the Sect Hall's gate and pagoda raised, the other twelve buildings pale inside dashed scaffolds, each tagged; Fei and Jun in the yard, three candidates at the gate; the level bar with its stops; the Treasury's card (500 taels, 20 Copper, 1 h, Build, Open storage), the disciples (Recruit locked: the rooms are full), Beyond the Walls |
| `compare_11_your_sect.png` | — | — | Mockup 11 above, `your_sect.png` below |
| `your_sect_hall.png` | ls6_end | `… --tap=640,228` | The Sect Hall's tag tapped: its gate and pagoda ringed, the card's Lv 1 of 10, the next level's 1,760 taels and 40 Riverstone, the Riverstone short, Upgrade locked with its reason |
| `your_sect_expeditions.png` | ls6_end | `--open-page=your_sect:expeditions` | The Expeditions tab, as before |
| `your_sect_unfounded.png` | qk5 | `--open-page=your_sect` | Not yet founded: the empty grounds with every building's scaffold, the name field and Found (locked: Qi Unfurling 1) |
| `sect_qu5.png` | qu5 | `--open-page=training_sect` | The Jade Sect Academy's hall from its door: eight rows of cushions coloured by rank, Tester sitting on the Inner Disciple row, the Core Disciple row lit with its trial on the board at the right (Reach Cloud Stride 1), Missions and the Sect Shop as the side doors |
| `sect_role.png` | ls6_end | `--open-page=training_sect:role` | The Role tab: the signature line's two variants and the sect tree as lacquer tablets on two timber boards |
| `characters.png` | ls6_end | `--open-page=characters` | The roster handscroll: Tester under the red "Playing" seal and the Second Disciple painted standing, three open slots as blank paper, the roll at the end with the next gates on three tags; the one you play sets its task under the scroll |
| `characters_switch.png` | ls6_end | `… --tap=400,300` | The Second Disciple tapped: its realm and task, and Switch |

## Against mockup 03

Matches: the shared window and plaque; the lacquered hall with its lattice frieze and floor; five bays under plaques
(Self, World, Bonds, Works, System) with the same entries in the same order; each entry a teal tablet on the bay's gold
cord with a round seal behind its 32 px glyph, its name, and a line when something waits; the red ready seal, Mail's
count and the new mark in the corner; the locked tablets dim with the lock on the seal and what opens them; the red
pillars with gold capitals between the bays, lantern light at their tops; the character line and the purses on the floor.

Differences, each on purpose:

1. **The lines are this build's**: the mockup's "Inner disciple", "2 of 6 slots set" and "Jun asks to join" come from
   the game as "Sect Master", "Slots set: 8 / 8" (a count of a total without a plural) and "3 ask to join".
2. **Bottleneck and chests**: the seals are `MenuPage.ready_seals`, the same rule as the HUD's Menu seal (the bottleneck
   on Cultivation, chests ready on Quests); ls6_end is not at a bottleneck, so only Quests is sealed.
3. **The purses** run silver, spirit stones, contribution from the right, as the P4 page drew them.

## Against mockup 11

Matches: the tabs (Courtyard, Expeditions, Territory; the old Buildings and Disciples tabs are the courtyard and its
cards) with the sect's name and region at their right; the grounds as a painting across the window with the raised
buildings solid, the rest pale where the room places them, each tagged ("to raise", its level, or the sect level with
its lock); the chosen building ringed; the disciples in the yard, the candidates at the gate and how many ask to join;
the level and prestige with the bar and its stops, what each stop opens and the prestige a building adds; the three
cards (the building, the disciples, Beyond the Walls) with Build, Open storage and Recruit.

Differences, each on purpose:

1. **Every building has its place**: the room places all fourteen (the terrace beds and array nodes included), so there
   is no "have no place yet" note; the tags are placed by the World map's layout pass so none touches another or a
   figure.
2. **Scaffolds**: a building not raised stands pale inside a dashed bronze outline (row 24), not only the chosen one.
3. **Disciples are figures**: the sect's disciples stand as small live figures (1 px an art px) dressed by their names,
   not as round chips; the card lists them with an initial seal.
4. **Numbers are this build's**: the stop at level 2 reads 697 (the first whole prestige at or past 200 × 2^1.8), the
   Copper the Treasury asks for is counted in the bag, the Storehouse and the chest (as `upgrade` counts it), and
   Build's lock names the first reason `SectAuthority.upgrade_check` gives.
5. **The builders' line** under Beyond the Walls says what is being raised and how long is left.

## The Sect and Characters (no mockup; rows 25 and 32)

- **Sect**: the hall in one-point perspective drawn from tokens (the row's pixel plate is left for later); the title is
  the sect's full name; your standing and contribution on a tablet at the upper left; the next rank's trial on a board
  at the upper right with a leader to its row. The rows settle from the dais forward as the page opens.
- **Characters**: five stretches are unrolled at once; past five, ◀ ▶ turn the scroll. The gates hang on three tags
  under the roll, the rest counted. The scroll unrolls from the rod as the page opens.

Not shown in a still: the tablets' sway and the seal pressed on, a building's scaffold filling as it is begun, the rows
settling, the scroll unrolling; with Reduce motion on the pages only fade in, which the `identity_suite` checks.
