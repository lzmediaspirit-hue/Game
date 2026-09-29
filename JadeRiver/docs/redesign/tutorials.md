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
   - A card explains that part in plain words, with a step count, **Next** and **Skip**.
   - A page tour has 3 to 6 steps.
   - A step with a "try it" lets taps through its spotlight. It moves on by itself once it is done: a point spent, a
     tab opened, or a card tapped.
   - The HUD's own controls get short tours of 1 to 3 steps: the meditate button, the technique buttons, dodge and
     guard, the Qi bar, the animal's button.
3. **The "?"** sits beside each page's close button while the page (on its tab) has a tour. It plays the tour again.
4. **Settings → Controls → Replay tutorials.** Every page shows its tour again on its next opening.

The coach never starts or shows in these cases; it waits and shows once they are over:
- in a fight: a foe near, or blows traded in the last 8 s (the HUD's fight hold, `Combat.in_combat`);
- during a staged scene or a moment;
- during a talk or an event page: the dialogue, a gift, mercy, fates, revival, welcome back;
- while a page asks its own question (its confirm dialog);
- while a page is a game in play (fishing, the guqin).

Only one guide shows at a time. The others wait in a queue, highest priority first. Only one tour plays on each
opening of a page. A tab's own tour waits until its system is open (a craft's tab shows only why it is shut until then).
A guide to a passing state that has passed (the points spent another way, the bottleneck broken) leaves the queue. A
guide whose page the player opened first is done when it opens.

## 2. Data: `tools/data/tutorials.py` → `data/tutorials.json`

One entry per system or page (64 in all). Each entry has:
- `page` and `tab`: a `main.gd` `PAGES` id, or `hud`;
- `trigger`: `unlock`, `points`, `item`, `bottleneck`, `technique`, or `page` (the page's first opening only);
- `chain`: the guidance steps, of three kinds:
  - `hud`: a HUD button, with no page open;
  - `place`: a thing in the world;
  - `page`: a page on top, on a tab. The last page step may be the element to use, with a `try`.
- `hint`: the first card's line;
- `tour`: the steps, each an anchor, a line and an optional `try` (`{event}`, `{tab}` or `{tap}`);
- `priority`, and `prologue` for the Prologue's systems.

The builder also writes:
- the page map (`PAGES` id → script), so `collection`, `seasons` and `achievements` are one page (the Codex), and
  `seclusion`, `heart` and `body` are the Cultivation page;
- the points pools (the same getters as the HUD's badges).

It checks every entry, and fails the build on any of these:
- a page it does not know;
- a line missing from `tools/data/ui_strings.json`;
- a line over 92 characters;
- a tour of the wrong size;
- a triggered guide with no chain.

The text lives in `tools/data/ui_strings.json`, under these keys:
- `ui.tutorial.<entry>.<n>`: the tour steps;
- `.hint`: the first card's line;
- `.do`: the element step;
- `ui.tutorial.go.*`: the generic "Tap %s." and "Open the %s tab.".

## 3. Runtime

| Part | Where | What it does |
|---|---|---|
| Rules | `scripts/core/tutorial_rules.gd` | Triggers, which chain step is on screen, the tours of a page and tab, and a place step's nearest thing. |
| Authority | `scripts/simulation/authority/tutorial_authority.gd` | Each character's `tutorials` record: `seen`, `guided`, `queue`, `at`. It queues a guide when its trigger first holds and records progress through `tutorial_step`, `tutorial_done`, `tutorial_replay` and `tutorial_goal`. |
| Coach | `scripts/ui/tutorial_coach.gd` | The overlay on its own canvas layer (25, over the pages and under the fade): the dim with its spotlight, the pixel hand (nearest neighbour, original art), the ring, the "!", the card and its buttons. It decides what shows every frame from the queue and the screen. |
| Page anchors | `scripts/ui/page.gd` `tour_rect` | Every tap region names an anchor by its action (`meridian`, `meridian:body`). Every tab is `tab:<id>`. The shared parts are `tabs`, `close`, `help`, `title`, `content` and `window`. A page adds its own with `tour_mark` (the cultivation stair, the techniques chart and dock, the mail's letter, and so on). |
| HUD anchors | `scripts/hud.gd` `tour_rect` | A control by its role in `hit_targets` (`icon:menu`, `points:meridian`, `skill`, `attack`, …) or a plate (`minimap`, `portrait`, `tracker`, `progress`, `log`). The HUD agent's rework of the technique buttons keeps these names. |

Tours use anchor names only, never node paths.

**Input.** Dimming and blocking work like this:
- While a tour dims the screen, the coach takes every touch except in the spotlight (and only there when the step has
  a try). It also keeps those touches from the HUD's own `_input` (`hud.coach`).
- A guide takes only its card's buttons.
- A tour that dims the play screen lets go of whatever the thumbs held, such as the stick or a guard.

**Saving.** The record is saved per character in the character's save.
- A tour in progress keeps its step, so a reload resumes it.
- A save from before the tutorials, or a character that skipped the Prologue, counts what it already has as known.
  There is no flood of old lessons.
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

**Not covered:**
- The talks and events (dialogue, gift, mercy, fates, revival, welcome back) have no tour.
- World activities with no page or control of their own (mining, netting, shrines and so on) are taught by the quests
  that open them.
- The late HUD powers (Spirit Sense, Presence, the Sphere, treasures, the weapon swap) get their HUD tours when the
  game reaches them. The suite lists them.

## 6. Tests

`tests/tutorials.tscn`, registered in `tools/run_tests.sh`. It runs on the real shell and checks:
1. **The data:** every page is known and the page map is current; every line wraps to at most two lines at the
   largest text size; every page-opening unlock has a guide and a tour; every `PAGES` page has a tour, except the
   talks.
2. **Every anchor** (318 of them) is found on its page or the HUD.
3. **The foundation path, end to end**, through real taps: the points granted by a Level, the hand on the Menu
   button, the Menu, Cultivation, the tab, the +1 spent, the tour step by step, all the points spent, nothing left.
4. **Nothing shows while it should wait:** in a fight, just after blows, in a staged scene or in a talk. It shows
   again after.
5. **Save and load:** a tour resumes at its step, and a legacy save queues nothing.
6. **The queue:** two unlocks at once, by priority; Later.
7. **Replay:** the "?" replays without recording; Replay tutorials clears what was seen.
8. **Places:** the table's place for a system that lives at places (else the nearest thing by route), and the
   direction mark leads there; every such step leads to a place that opens its page.

`tools/dev/tutorial_capture.tscn` takes the screenshots in `feedback/tutorials/`.
