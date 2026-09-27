# P5 · The Beasts family: Spirit Animals, Core Exchange, Beast Arena

Screenshots of the Beasts family built to its rows in `docs/page_identity.md` (16, 34, 36) and its family in §2 (straw
and rough timber: `straw`, `wood`, `sand`, `clay`), Spirit Animals beside its mockup `10_spirit_animals`. The Core
Exchange and the Beast Arena have no mockup. They are 1280 × 720 as captured, reduced to 256 colours; the `.gdignore` of
`docs/ui_p5/` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of this build's own
valley_run checkpoints (run with `--cp=user://valley_cp/` under a scratch `XDG_DATA_HOME`, then copied): `ls6_end`
(Sphere Lord 3 in the Lantern Star Field, six animals, the Copperjaw swarm) and `qu5` (Qi Unfurling 5, before the first
animal). None uses the Max Tester save, `--max-character` or `--unlock-all`. Each was captured headlessly from
`JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `spirit_animals.png` | ls6_end | `--open-page=spirit_animals` | The bestiary on the Reed Otter: out on its post (1 of 3, two posts open), the stable of six, its leaf (Lv 24, 1,762 / 2,351; 1.2 of 10 hearts; grievously wounded), its growth as stones with the Juvenile gates (Level 15 met, 3 hearts not yet, Heart Tempering 1 met) and what Juvenile opens, bloodline purity 14 with the stops at 50 (Ancestral Tide) and 90 (the Tide-Mother Otter form), its four skills, traits hidden; the leaf's foot; the tack wall with Rest, the four roles (Gatherer lit, +25% as a gatherer by nature), the three gear places, the nest and the swarm's chip |
| `compare_10_spirit_animals.png` | — | — | Mockup 10 above, `spirit_animals.png` below |
| `spirit_animals_grow.png` | ls6_end | `… --tap=437,630` | Grow: aptitude hidden until Juvenile, the contract, the three gates and Evolve locked until they are met |
| `spirit_animals_fuse.png` | ls6_end | `… --tap=813,630` | Fuse: the rule, where it can be done (the Beast Hall or the sect's Pavilion), every other animal with its Fuse |
| `spirit_animals_monkey.png` | ls6_end | `… --tap=225,408` | The Bamboo Monkey chosen from its stall: Set active, Beside You and Carry (locked: no Spirit Beast Bag), Combat lit as a fighter by nature, hungry, its bloodline's Hundred Staff Storm and Cloud-Staff Ape |
| `spirit_animals_swarm.png` | ls6_end | `… --tap=283,136` | The Swarm tab (the chip at the tack wall's foot opens it too): the Copperjaw swarm, its Queen and the ores to feed it |
| `spirit_animals_early.png` | qu5 | `--open-page=spirit_animals` | No animal yet: the leaf says where the first comes from, one post open and two locked with the realm that opens each, the nest |
| `spirit_animals_text_large.png` | ls6_end | `--text-size=2 --open-page=spirit_animals` | Settings › Text size › Large: the words grow in place and shorten with an ellipsis where a line is full |
| `core_exchange.png` | ls6_end | `--open-page=core_exchange` | The Beast Hall's wall: the two Peak Star Cores on the peak shelf, the chosen one over the urn's mouth with Sell one and Sell all, 6,441 Spirit Stones, 60 still to pay today, the prices, the stones heaped under the spout, the wounded otter on the straw with Rest your animals, the day's tally (0 of 60) |
| `core_exchange_early.png` | qu5 | `--open-page=core_exchange` | No cores yet: the empty shelves say where cores come from; the fresh straw and Rest locked |
| `beast_arena.png` | ls6_end | `--open-page=beast_arena` | The pit before any fight: the ten tamers' banners round the rim from Jing Mo at rank 1, yours (unranked) in jade after Farmhand Qiao's in gold, each tamer's lead animal; the next tamer's two teams and how the arena works; 1v1 and 3v3 at the gate |
| `beast_arena_fight.png` | ls6_end | `… --tap=541,612 --wait=3` | After a 1v1 won: you at rank 10, Farmhand Qiao stepped down to 11, Herb-girl Yan next; the fight replayed as two bars in the pit and Victory |
| `beast_arena_early.png` | qu5 | `--open-page=beast_arena` | No animal yet: both challenges locked with why |

## Against mockup 10

Matches: the kit's window, plaque and tabs (Stable, Swarm); the command line across from the tabs; "Beside you · 1 of
3" with three posts, "Reed Otter is out" and the open posts counted; "The stable · 6 animals", a row an animal with its
art, name and "Lv · role · element", the wounded one's red mark; the paper leaf between two rollers with the name, level,
what it is, the animal at 3x, the level bar with its numbers, bond as ten hearts, the Grievous Wound in red; "Growth" as
six stones from Hatchling to Primordial (the one it is lit jade, the next ringed gold, Primordial faint for a line that
never reaches it), the next stage's gates ticked and what it opens; "Bloodline purity" with its bar and the stops at 50
and 90, what the next one wakes and each stop's words under it; the skills as chips; the traits hidden; the tack wall:
Care with Rest and the four roles (the one it has lit), its nature and the +25%; Gear with Collar, Talisman and Saddle;
the Nest; the Copperjaw swarm's chip with its count and food.

Differences, each on purpose:

1. **The leaf's foot** (Grow, Feed, Teach, Breed, Fuse): the mockup has no room for what the Care and Growth tabs held
   besides what it shows (feeding and devouring, the books to teach, the contracts and breakthrough with its support,
   breeding, fusion). Each turns the leaf's lower half, and its button turns it back; Grow is lit when the next stage is
   ready. So the traits line is one line, and the favourite foods moved to Feed.
2. **Lock and rename** sit on the leaf: the padlock at its top right, and a tap on the name (the dotted line under it).
3. **Carry is not offered for the animal that is out**, as before (it cannot go in the bag while it walks beside you);
   for another animal the care row is Set active, Beside You and Carry.
4. **The stable's rows** carry a low timber rail under each animal, the stall's half-door it looks over (row 16's
   stable, the Beasts family's timber), and the leaf's animal stands on a bed of straw.
5. **The numbers are this build's** (Lv 24 and 1,762 / 2,351; 1.2 hearts; the swarm at 606 of 5,000 with no food); the
   command line says "Your Soul commands 3 at once" since ls6_end already commands three, and a gate reads "3 hearts"
   without "1.1 now" (the hearts are beside it). The nest's line says where an egg comes from generally, not that one waits
   in storage.
6. **An empty gear place** shows the bag's pet gear on the leaf to put on (none in ls6_end, so it answers "No pet gear in
   your bag").

## The other two (no mockup; rows 34 and 36)

- **Core Exchange**: the Beast Hall's rough timber wall with the title on a board hung by two ropes; the shelves at the
  left, a tier a shelf with its price on a board (a drag scrolls when there are more); the glazed urn (HD `core_urn`) in
  the centre with the chosen core bobbing at its mouth and the deal under it; the Spirit Stones spilled from the spout
  into a heap at the right; the straw bed in the corner holds the wounded animals and Rest your animals; the bamboo tally
  across the foot darkens a notch for every Spirit Stone paid today.
- **Beast Arena**: the pit seen from the stands, an oval of raked sand inside a fence; the ladder as eleven banners (ten
  tamers and you, placed at your rank) clockwise from the top, each cloth flying outward with its rank inked on it and
  the holder's name on a board as long as the name; the gate at the pit's foot carries the two challenges.

Not shown in a still: the openings (the animal walking out onto its leaf, the urn rising, the banners running up their
poles), a sold core dropping into the urn with a stone out of the spout, and your banner raised by a challenge; with
Reduce motion on the pages only fade in and nothing moves, which the `identity_suite` checks for every page.
