# P5 · The way family: Cultivation, Breakthrough, Revival, Fates

Screenshots of the way family built to its rows in `docs/page_identity.md` (5, 9, 39, 40) and its family in §2 (stone,
sky and starlight: `sky_top` / `sky_bottom`, `SURFACE.stone`, `GOLD` light). Cultivation is drawn to its approved mockup
`04_cultivation_ascent`; Break Through on the gate opens into moment 05, drawn in `05_breakthrough`. Revival and Fates
have no mockup and follow their rows. Techniques, the family's first page, was built earlier (`docs/ui_p5/techniques/`).
They are 1280 × 720 as captured, reduced to 256 colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing
them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of this build's own
valley_run checkpoints (run with `--cp=user://valley_cp/` under a scratch `XDG_DATA_HOME`): `ht5` (Heart Tempering 4,
Level 31), `ls6_end` (Sphere Lord 3, Level 98), `qu5` (Qi Unfurling 4) and `bf2` (Bone Forging 2). None uses the Max
Tester save, `--max-character` or `--unlock-all`. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=1 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `cultivation_ascent.png` | ht5 | `--open-page=cultivation` | The Overview as mockup 04 draws it: the night mountain with all nineteen great realms on one path (four ticked, Heart Tempering lit, Cloud Stride "· Flight, Mounts"), the nine-step stair in its bands with the figure seated on step 4 and its bar inside the step, gold marks on the steps that open something, the gate to Cloud Stride on step 9; at the right the badge, the band chip, the method line, the bar, Stored Qi, the body's ledger, the next step and the chips of what it opens, the gate's asks, Meditate and Breakthrough |
| `compare_04_cultivation_ascent.png` | — | — | Mockup 04 above, `cultivation_ascent.png` below |
| `cultivation_peak.png` | ls6_end | `--open-page=cultivation` | Sphere Lord, a realm of three steps: wide steps, the figure at the peak before the gate to Law Touching, the gate's requirements from the rules with the risk and the chance |
| `cultivation_early.png` | bf2 | `--open-page=cultivation` | Bone Forging 2: Mortal ticked, Guard and Weapon Dao opening at the next step, the gate to Qi Kindling with its soft and hard asks; the Paths, Dao and Seclusion tabs locked |
| `cultivation_text_large.png` | ht5 | `--text-size=2 --open-page=cultivation` | Settings › Text size › Large: the words grow in place, the chips give way to "+2" |
| `tap_meridian_foundation.png` | ls6_end | `--tap-points=meridian --wait=2` | The Meridian "+" badge by the HP panel tapped: Cultivation opens on Foundation, as before |
| `breakthrough_gate.png` | ht5 | `--realm=heart_tempering_9 --open-page=breakthrough` | The heaven gate out of Heart Tempering: the title on the beam's gold-leafed plaque, "From Heart Tempering 9 · Cloud Stride 1" and the Heart Trial in the doorway, three requirement tablets on red cords (the method's with its Go), Risk and Chance cut into the pillars, Core Forging's checklist on the left stele, the Support stele at the right, the three empty dishes on the step and Break Through on the threshold, locked with why |
| `breakthrough_offering.png` | ht5 | `… --give=cleansing_pill:2 --give=foundation_guard_pill … --tap=978,300` | A support tapped on the stele: it lies in the first dish on the step and is ringed on the stele |
| `breakthrough_minor.png` | ht5 | `--open-page=breakthrough` | A minor step: one gold-leafed tablet says so; Risk None, Chance 100% |
| `breakthrough_moment.png` | ht5 | `--breakthrough=2.3` | What Break Through opens into, unchanged: the step's name on the ink band and the card "What the breakthrough gave" with each number before and after (the early-game rewrite) |
| `compare_05_breakthrough.png` | — | — | Mockup 05 (a great breakthrough) above, the build's minor-step moment below |
| `revival_grace.png` | bf2 | `--open-page=revival` | The first fall before Bone Forging 5: the lamp in its niche, the early grace told in full in its shadow ("Until Bone Forging 5 a fall costs nothing …"), what you keep in its light, Return to Willow Path West and Revive here (no talisman) |
| `revival.png` | qu5 | `--open-page=revival` | Past the grace: "You lose 10% of this stage's progress and may carry an injury." in red at the left |
| `fates.png` | ls6_end | `--offer-fates --open-page=fates` | Three fortune sticks fanned out of the bamboo cylinder under the stars, each slip with its name, its gift above and its cost below, Lucky Star sealed Rare, Take this fate at each slip's foot |

## Against the mockups

**04, Cultivation.** Matches: the shared window, plaque and eight tabs; the mountain panel with its two ridges, the
mist and the dashed path, done realms gold and ticked, this one lit and larger, the next two near (the next with what
it opens), the far ones in mist and the last ones veiled; the dotted leader to the stair; the great realm's name and
"Great realm 5 of 19"; nine steps rising in the Early, Middle, Late and Peak bands with their bars and chips, the step
reached ringed in pale gold with its fill, the figure seated on it; marks on the later steps; the gate on step 9 with
its posts, roof, gold beam and the next realm's name; the badge, the stage, the band chip, the method line, the bar,
Stored Qi, the next step with its chips, the gate's asks as red dots, Meditate and the locked Break Through.

Differences, each on purpose:

1. **The numbers are this build's.** ht5 carries 3,200 of 6,700; the gate's asks are what the rules check today (the
   Heart Trial and the Qi Refining Pill; the method supports the next realm, so it is not listed).
2. **Unlock chips are words, not icons.** They name `unlocks.json`'s systems opening at the next step (Formation
   Guild, Array plates, and "+1" for the rest); a later step that opens something carries a gold mark, not its icon.
3. **The body's ledger stays.** The old Overview's rows (body level, toxicity, injuries, purity, Presence) are kept as
   one line under the bar, so nothing it told is lost. Stability, method and energy are in the line over the bar.
4. **"Breakthrough" on the button** is the game's own word for it (the mockup wrote "Break Through").
5. **The stair follows the realm.** A realm of three steps (Heaven Glimpse to Monarch) or one draws wider steps; the
   bands are Early, Middle and Peak there.
6. **The other tabs** (Foundation, Body, Heart, Paths, Methods, Dao, Seclusion) keep their panels on the window, as the
   mockup does not redraw them; the meridian diagram P5b once named for Foundation is not drawn (see below).

**05, Breakthrough.** The mockup is the moment Break Through opens into (moment 05, built in P6), so the compare puts
the build's moment under it; it is unchanged by this part, card and aura included. The gate page itself has no
mockup and follows row 9. Differences from the row: the next realm is written in the doorway rather than on the beam's
plaque (the plaque carries the page's title, which Page inks), and the archway is drawn from tokens (coursed stone,
tiled roof, studded doors) rather than as a pixel prop, which can replace it. Supports are chosen from a stele at the
right and laid in the dishes, since a bag may hold more than three.

## Revival and Fates, against their rows

- **Revival (row 39).** One lamp in a dark stone niche; what the fall takes at its left in the shadow (red past the
  grace; in pale gold while a fall costs nothing), what you keep at its right in the light; the choices under the
  lamp. The flame gutters and steadies over 0.6 s as the page opens (decoration: none under Reduce motion or the
  battery saver). The lamp is drawn from tokens (bronze bowl and foot, an ember flame by `WayKit.flame`). The early
  grace (P12) is told here in full on the first fall before Bone Forging 5 and in a line after.
- **Fates (row 40).** The cylinder low in the centre, three sticks fanned from it, each slip carrying the name, the
  gift above and the cost below, Take this fate at its foot; the sticks rise one after another inside the 0.35 s
  opening (a tap shows all; under Reduce motion all three are there). Gift words are `JADE_SHADOW` and costs `BLOOD`,
  the colours that read on paper.

## For the user to decide

1. Whether Foundation should become the meridian diagram P5b named for U14 (it keeps its rows and +1 buttons now).
2. Whether the Breakthrough plaque should carry the next realm's name, as row 9 says, with the title moved elsewhere.
3. The archway and the life lamp are page-drawn; §5 lists both as pixel props if a painted look is wanted.
