# Unlock tutorials: every new system teaches itself

Roadmap decision 43 (`docs/roadmap_master_ui.md` §6). The user asked for this:

> I want the game to teach the player how to use new systems that unlocked. For example, when the player first gets
> foundation points the game should navigate the player to the right screen to spend those points, or when he unlocks
> the techniques page, the player should get a tutorial for each new system he unlocks and understand how this system
> page works.

This note says what was built. Screenshots of the coach at the phone layout are in `feedback/tutorials/`.

---

## 1. What the player sees

1. **A guide.** It starts when a system opens: an unlock, the first of a resource (foundation points, Realisations,
   Bench points, Post Art points), the first piece of gear in the bag, or the first bottleneck.
   - A hand and a pulsing gold ring mark the next thing to tap.
   - On a HUD button there is also a red "!" badge.
   - A small card says why, in one or two lines, with **Later**.
   - The guide goes one step at a time: the HUD button (or a place in the world), then the page, then the tab, then
     the element to use. With the first foundation points that is the Menu button, the Cultivation tablet, the
     Foundation tab, and then the +1 to spend on.
   - Each step comes from what is on screen, so a shortcut works too. The points badge, for example, opens the tab
     straight away, and the guide then points at the +1.
   - Nothing on screen is dimmed and nothing is blocked while a guide shows.
2. **A tour.** It plays the first time a page (or one of its tabs) opens.
   - The screen is dimmed except for a spotlight on one part of the page.
   - A card explains that part in plain words, with a step count, **Next** and **Skip**. The phone's Back (or Escape)
     skips it too, and leaves the page open (decision 45).
   - A page tour has 3 to 6 steps.
   - A step with a "try it" lets taps through its spotlight. It moves on by itself once it is done: a point spent, a
     tab opened, or a card tapped.
   - The HUD's own controls get short tours of 1 to 4 steps: the meditate button, the technique buttons, dodge and
     guard, the Qi bar, the animal's button, and the late powers (below).
3. **A late HUD power** (decision 44: Spirit Sense, the Presence, the Sphere, treasures, the weapon swap) gets both.
   - The guide's hand, ring and "!" point at the power's own button. A button that waits in the folded fan has the hand
     on the fan first ("New in the fan: Sense. Tap the fan to open it.").
   - A tap on the button itself is the coach's: it does not use the power, it plays the power's tour there. Later
     passes the whole lesson by, as the HUD has no "?" to play it again.
   - The tour lights the button, then what it costs (the SL or QI bar on the panel), then a "try it". Its spotlight lets
     a tap through, and the step ends when the power is used: a pulse, the Presence held, the Sphere raised, a swap.
   - Where a page manages the power, the guide goes on after the tour: the Sphere's to Cultivation's Dao tab, the
     treasures' to the Bag.
   - A control that is not there yet is led to first: the swap's guide goes to the Bag to set a spare weapon, and Swap
     then comes out on the ring.
   - A Treasure button comes out only in a fight, when the coach waits. So its tour plays at rest and lights the place
     where the button will be, drawn faint there with the treasure it holds, and it has no "try it".
4. **The "?"** sits beside each page's close button while the page (on its tab) has a tour. It plays the tour again.
5. **Settings → Controls → Replay tutorials.** Every page shows its tour again on its next opening.

The coach never starts or shows in these cases; it waits and shows once they are over:
- in a fight: a foe near, or blows traded in the last 8 s (the HUD's fight hold, `Combat.in_combat`);
- during a staged scene or a moment;
- during a talk or an event page: the dialogue, a gift, mercy, fates, revival, welcome back;
- while a page asks its own question (its confirm dialog);
- while a page is a game in play (fishing, the guqin).

Only one guide shows at a time. The others wait in a queue, highest priority first, and after the player closes a card the
next waits a moment (1.2 s) on that screen. A HUD lesson on screen keeps it until it ends. Only one tour plays on each
opening of a page. A tab's own tour waits until its system is open (a craft's tab shows only why it is shut until then).
A guide to a passing state that has passed (the points spent another way, the bottleneck broken) leaves the queue. A
guide whose page the player opened first is done when it opens.

## 2. Data: `tools/data/tutorials.py` → `data/tutorials.json`

One entry per system or page (70 in all). Each entry has:
- `page` and `tab`: a `main.gd` `PAGES` id, or `hud`;
- `trigger`: `unlock`, `points`, `item`, `bottleneck`, `technique`, or `page` (the page's first opening only);
- `chain`: the guidance steps, of three kinds:
  - `hud`: a HUD button, with no page open;
  - `place`: a thing in the world;
  - `page`: a page on top, on a tab. The last page step may be the element to use, with a `try`.
- `hint`: the first card's line;
- `tour`: the steps, each an anchor, a line and an optional `try` (`{event}`, `{tab}` or `{tap}`);
- `priority`, and `prologue` for the Prologue's systems;
- `since`: the tutorials record's version that brought the entry (2 for the late HUD powers; the file's `version`).

A HUD power's entry (`page: hud`, decision 44) may mark one `hud` step of its chain as its control (`tour: true`):
- the steps before it lead to the control, and the control step is its own button (with `name`, the fan's label, when
  the button waits in the fan);
- the tour plays at the control step, on a tap there;
- the steps after it lead on to the page that manages the power, once the tour is seen.

With no control step, the tour plays first and the whole chain follows it. A tour step may carry `ghost` (a HUD role):
the control is drawn faint in the spotlight while the play screen does not show it.

The builder also writes:
- the page map (`PAGES` id → script), so `collection`, `seasons` and `achievements` are one page (the Codex), and
  `seclusion`, `heart` and `body` are the Cultivation page;
- the points pools (the same getters as the HUD's badges).

It checks every entry, and fails the build on any of these:
- a page it does not know;
- a line missing from `tools/data/ui_strings.json`;
- a line over 92 characters;
- a tour of the wrong size;
- a triggered guide with no chain;
- more than one control step, or one that is not a HUD step of a HUD entry;
- a `since` past the file's `version`.

The text lives in `tools/data/ui_strings.json`, under these keys:
- `ui.tutorial.<entry>.<n>`: the tour steps;
- `.hint`: the first card's line;
- `.do`: the element step;
- a step's own `text` (the Sphere's `.page`, the swap's `.ready`);
- `ui.tutorial.go.*`: the generic "Tap %s.", "Open the %s tab." and "New in the fan: %s. Tap the fan to open it.".

## 3. Runtime

| Part | Where | What it does |
|---|---|---|
| Rules | `scripts/core/tutorial_rules.gd` | Triggers, which chain step is on screen, the tours of a page and tab, and a place step's nearest thing. For a HUD power: its control step (`tour_at`), the guide's step before or after the tour (`lesson_step`), where the guide ends (`chain_goal`), and the record's `version`. |
| Authority | `scripts/simulation/authority/tutorial_authority.gd` | Each character's `tutorials` record: `seen`, `guided`, `queue`, `at`, `v`. It queues a guide when its trigger first holds and records progress through `tutorial_step`, `tutorial_done`, `tutorial_replay` and `tutorial_goal`. A HUD power's guide stays queued after its tour while it has a page to lead to. |
| Coach | `scripts/ui/tutorial_coach.gd` | The overlay on its own canvas layer (25, over the pages and under the fade): the dim with its spotlight, the pixel hand (nearest neighbour, original art), the ring, the "!", the card and its buttons. It decides what shows every frame from the queue and the screen. A HUD entry is its lesson (`_hud_lesson`): the tour on the play screen, and a power's guide round it; a tap on the power's own button under the hand plays the tour (`control`). A thin anchor (a bar of the panel) is lit 3 px round instead of 8; a step's `ghost` is drawn faint in its spotlight. |
| Page anchors | `scripts/ui/page.gd` `tour_rect` | Every tap region names an anchor by its action (`meridian`, `meridian:body`). Every tab is `tab:<id>`. The shared parts are `tabs`, `close`, `help`, `title`, `content` and `window`. A page adds its own with `tour_mark` (the cultivation stair, the techniques chart and dock, the mail's letter, the Bag's first `gear`, `weapon` and `treasure_item` in view, and so on). |
| HUD anchors | `scripts/hud.gd` `tour_rect` | A control by its role in `hit_targets` (`icon:menu`, `points:meridian`, `skill`, `attack`, `fan`, `sense`, `presence`, `sphere`, `swap`, …) or a plate (`minimap`, `portrait`, `tracker`, `progress`, `log`, and the panel's `qi` and `soul` bars). A Treasure button (`treasure:0`, `treasure:1`) comes out only in a fight; at rest, once revealed, its anchor is where it will come out on ring 2. The HUD agent's rework of the technique buttons keeps these names. The controls are counted once a frame (`tour_targets`, shared with the HUD's own frame). |

Tours use anchor names only, never node paths.

**Input.** Dimming and blocking work like this:
- While a tour dims the screen, the coach takes every touch except in the spotlight (and only there when the step has
  a try). It also keeps those touches from the HUD's own `_input` (`hud.coach`).
- A guide takes only its card's buttons. Over a page its card takes the taps on it too, so a tap never reaches what it
  hides; on the play screen a thumb passes through it to the stick.
- A tour that dims the play screen lets go of whatever the thumbs held, such as the stick or a guard.
- Every finger is the HUD's or the coach's from its press to its release (decision 45). A press the coach took keeps
  its drags and its release from the HUD; one it did not take (a thumb on the stick sliding over a card) is never cut
  off.

**The card** (decision 45, "Bugs fixed" below):
- It waits until its page has come in (`Page.settled`: drawn, its opening motion over) and its anchor is on screen
  (up to 0.4 s, then it stands alone in the middle). It never shows in one place and then jumps.
- It is placed once for its step and stays there. It moves only when its anchor moves more than 12 px, and never while
  a finger is on it. Its places are:
  - around the anchor and the hand at rest (never the hand's bob);
  - off the page's title, close and "?";
  - on the play screen, off the HUD's controls and plates, and for a guide off the thumbs' places (the stick's side and
    the right thumb's cluster);
  - for an anchor too tall for any side, tight over or under it.
- Its buttons are 56 px tall and act on the finger's release. Their touch targets reach 8 px past them, and a release
  up to 24 px off still counts. A held button shows pressed. A phone's tap arrives twice, as the touch and as the mouse
  click made from it; the coach takes it once, as the touch.
- A tap that closes a card (Done, Skip, Later) guards the card's place for 0.35 s. The second tap of a double tap
  reaches nothing under it.
- It fades in over 0.12 s. Its buttons work from its first frame.
- A HUD lesson on screen keeps the screen until it ends. A guide queued after it with a higher priority waits.

**What it costs a frame.** When nothing is queued, the coach does almost nothing. It looks at the record and at the
page on top, and a page's tours are listed once per page and tab (`TutorialRules.tours_for`). While it shows, it looks
things up once a frame or once a step. Its own drawing (the dim, the ring's pulse, the hand's bob) runs each frame. The
card is drawn by a child node, only when the card changes. The authority checks the passing states (points, an item, a
bottleneck, a technique) every 0.5 s and every trigger every 5 s. An event checks only the kinds it can bring. The
numbers are in "Bugs fixed".

**Saving.** The record is saved per character in the character's save.
- A tour in progress keeps its step, so a reload resumes it.
- A save from before the tutorials, or a character that skipped the Prologue, counts what it already has as known.
  There is no flood of old lessons.
- So does a save from before a later batch of lessons: a record whose `v` is older than an entry's `since` counts that
  entry known when its system is already open. A Sphere Lord saved before decision 44 is not taught Spirit Sense. A
  new character's record starts at the current version.
- Nothing is queued while every system is forced open (the Max Tester, previews).

## 4. Places

A `place` step leads to a thing in the world. It is one of three things:
- a kind of object (the nearest notice board, teleport stone, storage chest, transfer array, garden bed or fishing
  spot);
- an object that opens a page (the exchange);
- a person with a service (a shop, Tailor Xun).

"Nearest" is by the ways open to the character (`WorldAuthority.route`).

While the step shows, the coach asks the Tutorial authority for `tutorial_goal`. `WorldAuthority.guide_target` then
leads there first, which reuses the quest direction mark:
- the minimap's gold exit and its chevron;
- the World map's lantern on that area (`map_page.gd`).

In the room itself, the hand points at the thing, over its label.

The systems-as-places table (`tools/data/places.py` → `data/places.json`, `docs/redesign/systems_as_places.md` "As
built") leads the steps of the systems that live at places. A step's `place` id is a row's id, or a system or a page
of the table (`PlaceRules.system_of`: "storage", "notice_board", "shop", "teleport", "garden"); the row a walk there
takes then leads (`PlaceRules.home`: the character's own sect's, the home one, the nearest), when the character sees
it (the village's board goes up after the prologue) and a way open to it leads there. The other steps (the transfer
array, the pouches, the exchange, fishing) keep the nearest thing they name. The tutorials suite checks that every
step of a system with places leads to a place that opens the page it teaches.

## 5. What is covered

**The prototype's pages first:**
- Menu, Bag, the first gear, Quests, Cultivation, Foundation, Breakthrough, Techniques, Realisations, Codex,
  Collection, Map, Calendar, Mail, Character, Sect, Shop, Notice Board, Transfer Array, Crafts, Settings and Emotes;
- the HUD's meditate button, technique buttons, dodge and guard, and Qi bar.

**Then the rest of `PAGES`:**
- Achievements, Seasons, Storage, Characters, the Roll-Call and its Bench, Pouches, Works and Post Arts, Teleport,
  Your Sect, Spirit Animals and the animal's button, Companions, the Beast Arena, the Core Exchange, Relations, the
  Trial Tower, the County Hall, the guqin, chess, the Exchange, the Auction, the Garden and Fishing;
- the Cultivation tabs: Seclusion, Body, Heart, Dao, Vows and Methods;
- the Crafts tabs: Cooking, Alchemy, Smithing, Talismans and Guild;
- the Workshop and its Formations.

**Then the late HUD powers (decision 44)**, each from the unlock that opens it (`tools/data/story.py`):

| Power | Unlock (where) | Control | Guide | Tour | Try it |
|---|---|---|---|---|---|
| Spirit Sense | `spirit_sense` (Spirit Awakening 1, "A Lake Inside") | `sense` in the fan | the hand on its button (the fan while folded) | the button; the SL bar: 10 Soul a pulse, 6 s between; try it | a pulse (`spirit_sense_pulsed`) |
| Presence | `presence` (Will Manifest 1 and "Will Manifest", "A Presence of One's Own") | `presence` in the fan | the hand on its button | the button: weaker foes in it slow and hit softer; the SL bar: Soul each second, tap again to let go; its level in the corner, try it | held (`presence_toggled`) |
| Sphere | `sphere` (Sphere Lord 1 and "Sphere Lord", "A Sphere of One's Own") | `sphere` in the fan | the hand on its button; after the tour, the Menu, Cultivation and the Dao tab | the button: a small world from the strongest Dao; the QI bar: its element works on foes in it, Qi each second; two Spheres meet and the weaker breaks and tears a meridian, try it | raised (`sphere_toggled`) |
| Treasures | `treasures` (Heart Tempering 1, "A Treasure in Hand") | `treasure:0` on ring 2, in a fight | after the tour, the Bag and the treasure in it | where the button comes out in a fight (the treasure drawn faint); the QI bar: a use costs Qi, then the treasure rests; the Bag chooses it | none: only a fight shows the button |
| The second Treasure button | `treasure_slot_2` (Spirit Awakening 1) | `treasure:1` | the Bag and a treasure in it (Treasure 2) | none | none |
| Weapon swap | `dual_loadout` (Heart Tempering 1) | `swap` on ring 2, once a spare is set | the Bag, a weapon, Set as spare; then the hand on Swap | the button: trades the weapon in hand for the spare, costs nothing; the techniques: each weapon keeps its own; try it (it waits while a blow or a dodge is under way) | a swap (`loadout_swapped`) |

**Not covered:**
- The talks and events (dialogue, gift, mercy, fates, revival, welcome back) have no tour.
- World activities with no page or control of their own (mining, netting, shrines and so on) are taught by the quests
  that open them.

## 6. Tests

`tests/tutorials.tscn`, registered in `tools/run_tests.sh`. It runs on the real shell and checks:
1. **The data:** every page is known and the page map is current; every line wraps to at most two lines at the
   largest text size; every page-opening unlock has a guide and a tour; every HUD control that opens after the
   Prologue has its lesson (no "later" list any more); every late HUD power has a guide from its unlock to its control
   and a tour of 2 to 4 steps that lights the control and, where it is used out of a fight, waits for its use; every
   `PAGES` page has a tour, except the talks.
2. **Every anchor** (318 of them) is found on its page or the HUD. The late powers' (29) are found on a character at
   the realm that opens each, once the power is unlocked: the button with the fan open and the fan while it is folded,
   a Treasure button's place at rest, Swap once a spare is set, and the pages' steps as they open.
3. **The foundation path, end to end**, through real taps: the points granted by a Level, the hand on the Menu
   button, the Menu, Cultivation, the tab, the +1 spent, the tour step by step, all the points spent, nothing left.
4. **Nothing shows while it should wait:** in a fight, just after blows, in a staged scene or in a talk. It shows
   again after.
5. **Save and load:** a tour resumes at its step, and a legacy save queues nothing.
6. **The queue:** two unlocks at once, by priority; Later.
7. **Replay:** the "?" replays without recording; Replay tutorials clears what was seen.
8. **Places:** the table's place for a system that lives at places (else the nearest thing by route), and the
   direction mark leads there; every such step leads to a place that opens its page.
9. **The late HUD powers.**
   - Spirit Sense end to end, through real taps: the hand and the "!" on the folded fan, waiting in a fight; the fan
     opened, the hand on Spirit Sense; its tap plays the tour without a pulse; the button, then the SL bar, then the
     try it with the hand; a pulse through the spotlight (Soul spent, 6 s to wait) ends it, nothing left queued.
   - The treasures' tour first at rest, then the guide to the Bag.
   - The Sphere's guide on to the Dao tab after its tour.
   - The weapon swap's guide to a weapon and Set as spare, then the hand on Swap, the tour, and a swap through the
     spotlight.
   - A save from before them (`v` 1) knows the powers it has; a current one is taught them.
10. **The card under a thumb** (decision 45, "Bugs fixed" below). These checks go through the phone's own input path:
    a touch at the window's pixels, which the engine also turns into a mouse click.
    - Buttons are 48 px or more, with touch targets past them. A held button shows pressed and acts on its release,
      even when the thumb rolls off its edge. A release far off lets it go.
    - Done and Skip close on the first tap, at a corner or an edge.
    - A guide's card stands still while its hand bobs, and Later works on the first tap even when held nine frames.
    - A double tap on Done acts once. Its second tap never reaches the HUD or the page under the card.
    - A page's tour waits while the page comes in. A tap on the card as it fades in acts, and the card never moves.
    - A tab's tour under way resumes only on its own tab.
    - A replay's Skip leaves nothing in its place.
    - A HUD lesson keeps the screen when a higher-priority guide is queued.
    - After Later, the next guide waits a moment.
    - A thumb on the stick slides over a guide's card and keeps walking. A press the tour took is never the HUD's.
    - A fight, a reload and a room change mid-tour: the tour comes back at its step.
    - Back and Escape skip a tour and keep its page. Replay tutorials does not start the Settings tour on the page
      already open.
    - The hidden coach costs under 100 µs a frame on the play screen and 200 µs over a page. Its lookups are made once,
      and a card that does not change is not drawn again.

`tools/dev/tutorial_play.tscn` plays the tutorials as a player on the prototype's QA walk, answering every card with a
finger. It shoots and checks each card and reports every miss as a "PLAY BUG". `--only=sweep` with `--from=<saves>`
plays every lesson a kept game has queued, then each Menu page's first opening. See "Bugs fixed".

`tools/dev/tutorial_capture.tscn` takes the screenshots in `feedback/tutorials/`; with `-- --late`, the late powers'
lessons in `feedback/tutorials/late_powers/` (each guide step and tour step, at the realm that opens each power).

## 7. Bugs fixed (decision 45)

The user played build 110 on an Android phone and wrote: "The tutorial that teaches how to use the buttons is a bit
laggy, sometimes when clicking done or skip it does nothing and doesn't close, and [it] has a lot of bugs in general."

**How it was played.** `tools/dev/tutorial_play.tscn` plays the prototype's QA walk (`tools/dev/prototype_qa.gd`) as a
player: from the title and a new character through the Prologue, the fair and the sect into chapter 2. It also plays
from checkpoints of the story walk:
- `tests/prologue_run.gd` keeps "Crab Trouble done" and "The River Token", and the QA walk has a `p_boat` step.
- `--only=sweep` plays every lesson a kept game has queued. At the River Token there were thirteen, from the Menu's to
  the Codex's. It then opens each page of the Menu once.

Every card the coach shows is answered by a finger through the phone's input path: a touch at the window's pixels
(`Input.parse_input_event`), which the engine also turns into a mouse click, as on Android. The walk was played at
1280×720 and at a 20:9 phone's 2400×1080 (the canvas scaled 1.5 between its bars). The finger:
- taps Next, Skip, Later and Done at a button's middle and near each edge;
- taps as the card comes, or after reading it;
- sometimes holds for nine frames, or taps twice in quick succession;
- taps through a "try it" spotlight;
- follows guides where they point.

Each card is shot and checked: that it stays inside the screen, keeps off its spotlight and the hand, holds its words
and has buttons of 48 px or more, and that it does not move once shown. Each tap is checked to act the first time. The
finger's misses and a reading of the code gave the list below. Each bug has a check in the `tutorials` suite (§6 item
10), driven by the same phone input, and each check was confirmed to fail with its fix undone.

| # | Bug | Cause | Fix |
|---|---|---|---|
| 1 | **Done, Skip and Later sometimes did nothing** (the report). | The card was placed round the pointing hand *as it bobbed* (4 px, five times a second), so in every guide and every tour step with a "try it", the card and its buttons moved each frame. The costs that chose its place moved with the hand, so it could even jump between places. A thumb pressed near a button's edge, lifted off it, and nothing happened. | The card is placed once per step, from the hand at rest. It moves again only when its anchor moves more than 12 px, and never while a finger is on it. |
| 2 | **A page's tour card showed in the middle, then jumped beside its anchor**: the shop's Next went from x 764–900 to 640–776, and a tap where it first showed did nothing. | The tour started on the page's first frame, before the page had drawn its anchors and while its parts slid in (up to 0.35 s). The card stood alone in the middle, then followed its sliding anchor. | The coach waits for the page to come in (`Page.settled`). A step whose anchor is not found yet waits up to 0.4 s before its card stands alone (`MISSING_S`, which was never used). |
| 3 | **Later and Done looked as if they did nothing** when lessons were queued. At the River Token thirteen were. The Menu's guide put off, the Foundation points' guide came up at once in the same place, its hand on the same Menu button. | The next guide showed in the same frame. | After the player closes a card, another lesson waits 1.2 s on the same screen (`REST_S`). The same lesson going on (a HUD power's guide after its tour, a page's tour after its guide) does not wait. |
| 4 | **A double tap on Done or Skip reached what was under the card**: a slot of the Bag, the HUD's Attack, a page's region. | The first tap closed the card, and the second landed on what lay beneath it. | A tap that closes a card guards its place for 0.35 s. |
| 5 | **A HUD lesson's card vanished mid-tour** when a guide with a higher priority was queued (the guard's tour under the Menu's guide). The tap meant for Next fell on the HUD. | The coach showed whatever headed the queue, and the queue is ordered by priority. | The HUD lesson on screen, or under way, keeps the screen until it ends. |
| 6 | **A tab's tour under way resumed on another tab**, lighting nothing. The Foundation tour at step 3, reopened on Overview, stood alone in the middle. | A tour in progress was matched to its page but not to its tab, and it ignored "one tour an opening". | It resumes only on its own tab, on an opening where no tour has played. A tour replayed from "?" and skipped leaves nothing in its place. |
| 7 | **A thumb on the stick that slid over a guide's card was cut off, and the character walked on alone.** | `holds()` decided by position for every event. So the drags and the release of a finger the HUD had taken were kept from the HUD once they crossed the card's buttons, or anywhere under a dim, and the stick never heard its release. | Every finger belongs to one owner from press to release. A press the coach took is the coach's to its release; one it did not take is never cut off. |
| 8 | **Back during a tour closed the page under it**, and the tour came back on the page's next opening. Skip was the only way out. | Back went to the page. | Back (and Escape) skips a tour that dims the screen. Back again closes the page. |
| 9 | **Settings → Replay tutorials started the Settings tour at once**, under the finger. | Replay cleared every tour seen, and the page already open had played no tour this opening. | The authority emits `tutorials_replayed`, and the coach counts the page open as toured. |
| 10 | **A guide's card covered the HUD's Talk button** in the village, and could sit where the thumbs rest, its Later under the stick's thumb. | The card was kept off only its anchor, the hand, and a page's title, close and "?". | On the play screen the card keeps off everything the HUD shows (`HUD.obstacle_rects`: its controls, plates, the equip prompt, the log). A guide's card also keeps off the thumbs' places, and a thumb passes through its body to the stick. Over a page, the card's body takes the taps on it, so they never reach what it hides. |
| 11 | **A card covered the top of the Cultivation stair.** | The stair is too tall for any side, and the fallback took the safe area's top. | It tries tight over or under the anchor, to the screen's edge, first. |
| 12 | **The gear guide's hand stayed on the piece after it was tapped**, though the card said "then Equip". | Its anchor was `gear` alone. | `equip\|gear`: the hand moves to Equip once the piece's card shows. |
| 13 | **The Cultivate tour lit nothing with the fan folded.** | Its first anchor was `meditate`, a button in the fan. | `meditate\|fan`, as the late powers' guides do. |
| 14 | **Guides showed over a HUD still fading back after a scene**, the hand and "!" on a faint button. | The coach checked only the scene's lock. | The coach waits for the HUD to be back. |
| 15 | **Buttons small for a thumb, a press that showed little, a tap that came twice.** | They were 136×48 px, and a tap had to press and lift inside the same button. A phone's tap came as the touch and again as the mouse click made from it; both reached the card, and only the first release clearing the press kept it from acting twice. | 136×56 px, with touch targets 8 px past them. A release up to 24 px off counts. A held button shows pressed, its label down 2 px. The mouse click made from a touch is ignored: a tap is taken once, as the touch, one finger at a time. |
| 16 | **Tour steps that lit nothing for a new player.** The Map's "Walk" step, and the last Settings step when Next was tapped instead of opening Controls. | The Walk button shows only on a quest's place. Replay tutorials is on the Controls tab. The suite's anchor check opens pages with everything in place, so it did not see this. | `walk\|card` (the place's card, where Walk comes) and `replay_tutorials\|tab:controls`. |
| 17 | **A guide's card half hid the tracker's go button.** | The card was as wide as its words at 512 px, plus its buttons. | A guide's words wrap at 400 px when they still fit two lines, so the card fits beside its button. |
| 18 | **The Qi pool's tour lit the whole panel** for "the blue bar on your panel". The pool now opens with the first technique at Bone Forging 1. | Its anchor was `portrait`. | `qi\|portrait`: the ring stands on the Qi bar. |
| 19 | **The lag.** | See below. | See below. |

**The lag.** Measured with `tools/dev/tutorial_prof.tscn` on this machine's desktop CPU; a phone's is several times
slower. The figures are microseconds a frame, the median over 400 frames of the coach's own work and drawing, with the
old code and the new run back to back three times each (the median of the three):

| The coach, a frame (µs) | Before | After |
|---|---:|---:|
| Hidden, on the play screen | 40 | 14 |
| Hidden, a page open (the Bag, its tour seen) | 531 | 35 |
| A guide's card on the HUD (the Menu button's) | 620 | 189 |
| A HUD tour (the guard's) | 636 | 165 |
| A page's tour (the Bag's) | 1,018 (p90 1,390) | 181 (p90 245) |
| A page's "?", on each drawing of the page | 188 | 2 |
| The authority's poll, every 0.5 s | 338 | 35 (every trigger, every 5 s: 322) |

The profiler's figures include its own timing of the coach's parts. Timed directly in the `tutorials` suite, the hidden
coach costs about 2 µs a frame on the play screen and 8 µs over a page.

Where the time went:
- With a page open, `_page_tour` went through all 70 entries twice a frame. It asked the authority's `state()`, and
  through it a config, three times for each entry. It did this whether or not a tour could play.
- The page's own "?" did the same on every drawing.
- `HUD.tour_rect` asked `hit_targets()` afresh for each anchor. Each call cost about 175 µs, because the points badges
  it counts walk the technique trees. The coach asked for an anchor up to four times a frame.
- The card's words were wrapped again every frame, and the whole card was drawn every frame: its text, the text's
  shadows and the Next label's ink outline.
- The authority checked every entry every 0.5 s (a 0.3 ms spike), and again on every item picked up.

Now:
- A frame with nothing queued stops at the record and the page on top.
- A page's tours are listed once per page and tab (`TutorialRules.tours_for`).
- The HUD's controls are counted once a frame and shared with the HUD's own frame (`HUD.tour_targets`).
- The words are wrapped once per step.
- The card is a child node (`CardView`), drawn again only when it changes. The coach's own drawing (the dim, the
  ring's pulse, the hand's bob) is a few rectangles, arcs and one texture.
- The poll checks only the passing states every 0.5 s, and every trigger every 5 s. An event checks only the kinds it
  can bring.

The `tutorials` suite holds the hidden coach to under 100 µs a frame on the play screen and 200 µs over a page. It
also checks that the lookups are made once and that a still card is not drawn again.

**The shots** (`feedback/tutorials/decision45/`):
- `before_shop_opening.png` and `after_shop_opening.png`: the shop's tour on the frame the page opens, the next one and
  the twelfth. Before, the card shows in the middle over a page not yet drawn (Next at x 764–900), then jumps beside
  the wares (Next at 640–776). After, it waits for the page, then shows beside the wares and stays there.
- `before_guide_play_screen.png` and `after_guide_play_screen.png`: the gear guide in the village. Before, its card sits
  over the Equip prompt, the people and Lu's plate, down to the Talk button. After, it is narrow and clear of the
  HUD's controls, plates and thumbs.
- `phone_guide.png` and `phone_tour.png`: the Menu's guide and a page's tour at a 20:9 phone's 2400×1080. The canvas is
  scaled 1.5 between its bars.
- `phone_tall_anchor.png`: the Cultivation stair's step, its card tight over the stair.
