# Less walking in the sect stretch (decision 42)

The user played the prototype APK (build 108) and said: **"There should be less monotone walking between places in
the sect quest."** This page measures the walking the sect stretch asked for, from the sect choice to the
end-of-prototype gate, for both sects. It then says what was changed and measures again.

## How the walking was measured

`tools/data/sect_walks.py` walks every trip the quests ask for, one stop to the next: a giver, a step's place, a
hand-in. It walks each trip the way the tracker's go button does:

- **The rooms** are the fewest ways from room to room (`WorldRules.route`). The sect's transfer arrays count as ways
  once the token knows both ends, as they do for auto-path.
- **Inside a room** it follows the auto-path's own path on the height grid (`TopdownRoom.find_path`: eight directions,
  stairs, a hop up a level) from where one arrives to the next way or the stop.
- **The seconds** are plain walking at the sprint pace. Sprint is the default now (decision 42's controls):
  `movement.json`'s top-down `sprint`, 216 units a second (about 1.4 times the walk's 154), 6.75 tiles a second. At
  that pace a room of the stretch (56–72 tiles wide) takes about 9 seconds to cross.
- **Not counted:** an array's step, a way's fade, a scene's cuts, fights, and time spent at a stop.

`python3 tools/data/sect_walks.py --before` prints the tables below for the stretch as it was. It uses the old stops
and no arrays, on today's layouts. `python3 tools/data/sect_walks.py` prints the stretch as it is now.

## Before: build 108

The stretch after the sect choice, as the quests led it:

1. The Entry Trial, Shen Lian's spar, the steward's chores (side) and the Weapon Hall. These stay on the Fairground and
   the sect's gate, and they were fine.
2. **Strange Tracks.** The mentor's note sent the player from the Weapon Hall across the whole valley to the Marsh Edge:
   through Stoneford, the Willow Path, the village and the Reed Shallows. Then the player walked back up to the mentor's
   peak.
3. **The Humming Token.** From the peak down to the marsh again, and back up again.
4. **Mei Qing's Errand.** From the peak to Artisan Row, from there to the marsh, and back to Artisan Row.
5. **Grey at the Edges.** Back up to the peak.
6. **The Level hunt.** Down to the marsh.
7. **The First Current.** To the Lotus Ferry.
8. **The lessons.** Up to the peak for Eyes for Qi, down to the Reed Shallows and back up. Then out to the training yard
   for the Outer Trial, and back up to the peak.

<!-- BEFORE -->

### The Jade Sect, before

| # | Quest | To | Rooms walked | Plain walk |
|---|---|---|---|---|
| 1 | Entry Trial | the trial bell | Fairground → Entry Trial (Jade) | 7 s |
| 2 | Entry Trial | the Trial Puppet | Entry Trial (Jade) | 2 s |
| 3 | Fish-Gutting Fists | Shen Lian | Entry Trial (Jade) → Fairground | 7 s |
| 4 | A Disciple's Chores (side) | the steward | Fairground → Gate Street | 9 s |
| 5 | A Disciple's Chores (side) | the first spot | Gate Street | 2 s |
| 6 | A Disciple's Chores (side) | the second spot | Gate Street | 1 s |
| 7 | A Disciple's Chores (side) | the grey stain | Gate Street | 3 s |
| 8 | A Disciple's Chores (side) | hand in | Gate Street | 1 s |
| 9 | The Weapon Hall | the weapon master | Gate Street → Weapon Hall and Forge | 3 s |
| 10 | The Weapon Hall | the dummies | Weapon Hall and Forge | 1 s |
| 11 | The Weapon Hall | hand in | Weapon Hall and Forge | 1 s |
| 12 | Strange Tracks | the first grey patch | Weapon Hall and Forge → … (9 rooms) → Marsh Edge | 78 s |
| 13 | Strange Tracks | the second | Marsh Edge | 3 s |
| 14 | Strange Tracks | the third | Marsh Edge | 3 s |
| 15 | Strange Tracks | hand in to the mentor | Marsh Edge → … (12 rooms) → Elder Hu's Peak | 117 s |
| 16 | The Humming Token | the Hollowed Boarlets | Elder Hu's Peak → … (12 rooms) → Marsh Edge | 114 s |
| 17 | The Humming Token | hand in to the mentor | Marsh Edge → … (12 rooms) → Elder Hu's Peak | 115 s |
| 18 | Mei Qing's Errand | Mei Qing | Elder Hu's Peak → … (5 rooms) → Artisan Row | 55 s |
| 19 | Mei Qing's Errand | reed frogs (moss), boarlets (hides) | Artisan Row → … (6 rooms) → Marsh Edge | 59 s |
| 20 | Mei Qing's Errand | hand in | Marsh Edge → … (6 rooms) → Artisan Row | 59 s |
| 21 | Grey at the Edges | report to the mentor | Artisan Row → … (5 rooms) → Elder Hu's Peak | 56 s |
| 22 | (the Level) | hunt to Bone Forging 7 | Elder Hu's Peak → … (12 rooms) → Marsh Edge | 114 s |
| 23 | The First Current | Lu | Marsh Edge → Reed Shallows → Lotus Ferry Village | 17 s |
| 24 | The First Current | the Qi spring | Lotus Ferry Village | 5 s |
| 25 | The First Current | hand in | Lotus Ferry Village | 5 s |
| 26 | Eyes for Qi (lesson) | the mentor | Lotus Ferry Village → … (10 rooms) → Elder Hu's Peak | 99 s |
| 27 | Eyes for Qi (lesson) | meditate, moss | Elder Hu's Peak → … (11 rooms) → Reed Shallows | 104 s |
| 28 | Eyes for Qi (lesson) | hand in | Reed Shallows → … (11 rooms) → Elder Hu's Peak | 105 s |
| 29 | Outer Trial (lesson) | three spars | Elder Hu's Peak → … (2 rooms) → Pavilion Rooftops | 25 s |
| 30 | Outer Trial (lesson) | hand in to the mentor | Pavilion Rooftops → … (2 rooms) → Elder Hu's Peak | 26 s |

Total plain walking 1197 s (19.9 min) over 30 trips and 165 rooms walked; 12 trips over 35 s; the longest 117 s; back-and-forth: 15-16 (Marsh Edge ↔ Elder Hu's Peak), 16-17 (Elder Hu's Peak ↔ Marsh Edge), 19-20 (Artisan Row ↔ Marsh Edge), 27-28 (Elder Hu's Peak ↔ Reed Shallows), 29-30 (Elder Hu's Peak ↔ Pavilion Rooftops).

### The Cloud Sect, before

| # | Quest | To | Rooms walked | Plain walk |
|---|---|---|---|---|
| 1 | Entry Trial | the trial bell | Fairground → Entry Trial (Cloud) | 5 s |
| 2 | Entry Trial | the Trial Puppet | Entry Trial (Cloud) | 2 s |
| 3 | Fish-Gutting Fists | Shen Lian | Entry Trial (Cloud) → Fairground | 5 s |
| 4 | A Disciple's Chores (side) | the steward | Fairground → Cliff Stair | 4 s |
| 5 | A Disciple's Chores (side) | the first spot | Cliff Stair | 2 s |
| 6 | A Disciple's Chores (side) | the second spot | Cliff Stair | 2 s |
| 7 | A Disciple's Chores (side) | the grey stain | Cliff Stair | 3 s |
| 8 | A Disciple's Chores (side) | hand in | Cliff Stair | 1 s |
| 9 | The Weapon Hall | the weapon master | Cliff Stair → Sword Court → Weapon Hall and Forge | 12 s |
| 10 | The Weapon Hall | the dummies | Weapon Hall and Forge | 1 s |
| 11 | The Weapon Hall | hand in | Weapon Hall and Forge | 1 s |
| 12 | Strange Tracks | the first grey patch | Weapon Hall and Forge → … (10 rooms) → Marsh Edge | 80 s |
| 13 | Strange Tracks | the second | Marsh Edge | 3 s |
| 14 | Strange Tracks | the third | Marsh Edge | 3 s |
| 15 | Strange Tracks | hand in to the mentor | Marsh Edge → … (11 rooms) → Elder Sung's Peak | 106 s |
| 16 | The Humming Token | the Hollowed Boarlets | Elder Sung's Peak → … (11 rooms) → Marsh Edge | 101 s |
| 17 | The Humming Token | hand in to the mentor | Marsh Edge → … (11 rooms) → Elder Sung's Peak | 103 s |
| 18 | Mei Qing's Errand | Mei Qing | Elder Sung's Peak → … (4 rooms) → Artisan Row | 42 s |
| 19 | Mei Qing's Errand | reed frogs (moss), boarlets (hides) | Artisan Row → … (6 rooms) → Marsh Edge | 59 s |
| 20 | Mei Qing's Errand | hand in | Marsh Edge → … (6 rooms) → Artisan Row | 59 s |
| 21 | Grey at the Edges | report to the mentor | Artisan Row → … (4 rooms) → Elder Sung's Peak | 44 s |
| 22 | (the Level) | hunt to Bone Forging 7 | Elder Sung's Peak → … (11 rooms) → Marsh Edge | 101 s |
| 23 | The First Current | Lu | Marsh Edge → Reed Shallows → Lotus Ferry Village | 17 s |
| 24 | The First Current | the Qi spring | Lotus Ferry Village | 5 s |
| 25 | The First Current | hand in | Lotus Ferry Village | 5 s |
| 26 | Eyes for Qi (lesson) | the mentor | Lotus Ferry Village → … (9 rooms) → Elder Sung's Peak | 87 s |
| 27 | Eyes for Qi (lesson) | meditate, moss | Elder Sung's Peak → … (10 rooms) → Reed Shallows | 92 s |
| 28 | Eyes for Qi (lesson) | hand in | Reed Shallows → … (10 rooms) → Elder Sung's Peak | 93 s |
| 29 | Outer Trial (lesson) | three spars | Elder Sung's Peak → Array Court → Sword Court | 19 s |
| 30 | Outer Trial (lesson) | hand in to the mentor | Sword Court → Array Court → Elder Sung's Peak | 20 s |

Total plain walking 1077 s (17.9 min) over 30 trips and 156 rooms walked; 12 trips over 35 s; the longest 106 s; back-and-forth: 15-16 (Marsh Edge ↔ Elder Sung's Peak), 16-17 (Elder Sung's Peak ↔ Marsh Edge), 19-20 (Artisan Row ↔ Marsh Edge), 27-28 (Elder Sung's Peak ↔ Reed Shallows).

<!-- /BEFORE -->

What the tables show:

- **About 18–20 minutes of plain walking** in a stretch whose quests take about as long again to play. Twelve trips
  per sect were over 35 seconds; the longest took two minutes.
- **Five back-and-forths.** The two errands at the marsh sent the player up the mentor's peak and straight back down
  twice: Strange Tracks' report, then The Humming Token. Mei Qing's Errand went Artisan Row → marsh → Artisan Row. The
  lessons went peak → Reed Shallows → peak and peak → training yard → peak.
- **The same empty rooms, over and over.** In the Jade Sect's stretch the East Terrace and the Herb Terraces were each
  crossed eleven times without a stop. Gate Street, the Fairground, Stoneford's Market Street and gate, and both
  Willow Path rooms were crossed ten times each. In the Cloud Sect's stretch the Sword Court and the Array Court were
  crossed eleven times each, and the same valley rooms ten times each. Nothing waited in them for a player just passing
  through.

## What was changed

Three things, in the order the brief gives them. Each is chosen for a xianxia sect.

### 1. The errands come to the player

The marsh is where chapter 2 happens, so its errands are now done there in one visit:

- **Strange Tracks is done at the third grey patch.** It no longer waits for a report on the peak. The River Token hums
  (the scene `grey_rises`: a jade ring on the player, grey mist gathering where the patches lie, the player's own words
  in a balloon). **The Humming Token** starts on the spot (`next`, `auto_accept`). The grey boarlets it asks for rise
  in the same room.
- **The mentor comes down to the marsh.** Once the fifth boarlet falls and The Humming Token is ready, Elder Hu, or
  Elder Sung, lands beside the player in a column of the sect's light (the scene `mentor_descends_*`). He takes the
  hand-in there. He stands at the marsh only while the quest waits for him (`quest_ready`, a new requirement kind), and
  is hidden on his peak meanwhile (`quest_not_ready`), so the tracker never points two ways.
- **Mei Qing tends the watchers at the marsh's watch post.** She is there from the Weapon Hall's end until her errand is
  done, and not in Artisan Row. Her moss (from the reed frogs) and her grey hides (from the boarlets) are taken, found
  and handed in without leaving the room. The tracker now counts a collect step's foes wherever they are, so her moss
  leads to the frogs beside her. Before, it led to a two-moss bundle in Granny Liu's hut, back in the village
  (`QuestAuthority._item_places`).
- **The Outer Trial is handed in to the training hall's master**, in the yard where its spars are won, not back up on
  the peak.

### 2. The sect's transfer array (传送阵)

A transfer array is the classic way a sect moves its disciples between its halls and its outposts. Each sect keeps
three:

- one on its gate's plaza (Gate Street, the Cliff Stair), beside the steward and the teleport stone;
- one on its mentor's peak;
- one at the Marsh Edge's watch post. Both sects keep this one, because both have watchers on the grey there. It sends
  each disciple back to their own sect's arrays.

How it works:

- **Earned and taught by the story.** The Weapon Hall done, the disciple's token opens the arrays (the unlock
  `transfer_array`). As the player steps out with the mentor's note, the steward stops them. He walks to the ring,
  points, and hands over the controls with "Step onto the array: tap Travel" (the scene `array_lesson_*`). The lesson
  keys the token to the gate's array and to the watch post's.
- **The first walk up the grounds is on foot.** The mentor's peak does not know the token yet, so Grey at the Edges
  sends the player up through the sect's grounds for the first time. At the top the mentor keys his own array (the
  scene `mentor_peak_*`: "My peak's array knows your token now. The sect is yours to cross in a breath"). After that,
  the peak, the gate and the marsh are one tap apart.
- **A place, not a menu.** The array is a stone disc set in the paving. Its runes are dark until the token opens them,
  then they glow and turn in the sect's colour: jade, cloud-steel, or both at the watch post (`transfer_array*` in
  `tools/props/defs_structures.py`). You stand in the ring and tap Travel. It asks where to, among the arrays the token
  knows (a choice on the dialogue page), and you come out on the far one in a column of the sect's light. It is free,
  because these are the sect's own arrays. The teleport stones still charge shards and still open at Qi Kindling 3, as
  "Stones That Move You" teaches: they are for the world beyond the sect.
- **The tracker takes it.** An array is a way to each node of its network (`WorldRules.ways_out`, its links in
  `array_links`). `WorldAuthority.portal_open` lets a character take one only if the token knows both ends and the node
  is their own sect's. So the route, the direction mark on the minimap, the tracker's go button and auto-path all use
  it. Auto-path walks the body to the node and steps onto it (`auto_path_board` → `array_travel`).
- **The gate stays closed.** An array never leads past the end-of-prototype gate (`array_open` asks
  `prototype_gate`).

Checked against the systems-as-places study (`docs/redesign/systems_as_places.md`):

- **§2's travel networks as places** (OSRS's spirit trees and fairy rings, Stardew's paired Mini-Obelisks). The array
  is one: a thing in the world that you walk to and use.
- **Rule 4, services cluster at the arrival point.** The gate's array stands on the plaza with the steward, the
  teleport stone and the shrine.
- **Rule 5, remote access earned, never taken.** Nothing that was in the menu moved out of it. The array adds a way;
  it removes none.
- **Rule 3, no daily chore of walking.** The sect's everyday places are now one tap from its gate.
- **§4.10's teleport verdict ("Place, as now, plus a home stone").** Unchanged: the array is the sect's own network,
  not the teleport page.

### 3. Something on the way

The walks that remain are short, and the one long walk left, the first one up through the grounds, has something in
every room. These are live scenes: the player keeps the controls and may walk on.

| Room | On the way | What it uses |
|---|---|---|
| Pavilion Rooftops (Jade) / Sword Court (Cloud) | The training hall's master calls out the disciple back from the marsh for a round at the practice post ("Mind the wind-up… Lose and you sweep it"). The Cloud master adds the plum-blossom poles | the spar post, a timed hand-off over it |
| East Terrace (Jade) / Array Court (Cloud) | The formation elder and the physician, overheard: the watchers came back grey to the elbow, and grey doesn't blow in from nowhere… the old maps mark a shrine under the river at Deepwater Bend (the Drowned Shrine of chapter 5) | balloons, a "?", a "!" and a turn to the listener |
| Herb Terraces (Jade) / Array Court (Cloud) | The gardener's favour: take a pot of lotus root tea up to the elder, "he forgets to drink when he's thinking". A side quest, `tea_for_the_elder`, handed in where the player is going anyway, for a Qi Gathering Pill | a quest, its item, a hand-off over the gardener |
| Marsh Edge | The watch post: its two watchers (one sitting, his arm gone grey), Mei Qing tending them, the array, both sects' banners | people with lines, the post's props |
| Marsh Edge | The token hums at the third patch, and the mentor comes down in a column of light | the scenes above |

## After: now

<!-- AFTER -->

### The Jade Sect, now

| # | Quest | To | Rooms walked | Plain walk |
|---|---|---|---|---|
| 1 | Entry Trial | the trial bell | Fairground → Entry Trial (Jade) | 7 s |
| 2 | Entry Trial | the Trial Puppet | Entry Trial (Jade) | 2 s |
| 3 | Fish-Gutting Fists | Shen Lian | Entry Trial (Jade) → Fairground | 7 s |
| 4 | A Disciple's Chores (side) | the steward | Fairground → Gate Street | 9 s |
| 5 | A Disciple's Chores (side) | the first spot | Gate Street | 2 s |
| 6 | A Disciple's Chores (side) | the second spot | Gate Street | 1 s |
| 7 | A Disciple's Chores (side) | the grey stain | Gate Street | 3 s |
| 8 | A Disciple's Chores (side) | hand in | Gate Street | 1 s |
| 9 | The Weapon Hall | the weapon master | Gate Street → Weapon Hall and Forge | 3 s |
| 10 | The Weapon Hall | the dummies | Weapon Hall and Forge | 1 s |
| 11 | The Weapon Hall | hand in | Weapon Hall and Forge | 1 s |
| 12 | Strange Tracks | the steward's lesson: the gate's transfer array | Weapon Hall and Forge → Gate Street | 4 s |
| 13 | Strange Tracks | the first grey patch (by the array) | Gate Street → Marsh Edge (by array) | 1 s |
| 14 | Strange Tracks | the second | Marsh Edge | 3 s |
| 15 | Strange Tracks | the third: the token hums | Marsh Edge | 3 s |
| 16 | The Humming Token | the Hollowed Boarlets, here | Marsh Edge | 3 s |
| 17 | The Humming Token | hand in: the mentor comes down | Marsh Edge | 3 s |
| 18 | Mei Qing's Errand | Mei Qing at the watch post | Marsh Edge | 2 s |
| 19 | Mei Qing's Errand | reed frogs (moss), boarlets (hides) | Marsh Edge | 5 s |
| 20 | Mei Qing's Errand | hand in at the watch post | Marsh Edge | 5 s |
| 21 | (on the way) | the hall master offers a spar | Marsh Edge → Gate Street → Pavilion Rooftops (by array) | 13 s |
| 22 | (on the way) | two elders overheard on the terrace | Pavilion Rooftops → East Terrace | 8 s |
| 23 | Tea for the Elder (side, on the way) | the gardener's favour | East Terrace → Herb Terraces | 8 s |
| 24 | Grey at the Edges | report to the mentor (and the tea) | Herb Terraces → Elder Hu's Peak | 10 s |
| 25 | (the Level) | hunt to Bone Forging 7 | Elder Hu's Peak → Marsh Edge (by array) | 7 s |
| 26 | The First Current | Lu | Marsh Edge → Reed Shallows → Lotus Ferry Village | 17 s |
| 27 | The First Current | the Qi spring | Lotus Ferry Village | 5 s |
| 28 | The First Current | hand in | Lotus Ferry Village | 5 s |
| 29 | Eyes for Qi (lesson) | the mentor | Lotus Ferry Village → … (2 rooms) → Elder Hu's Peak (by array) | 15 s |
| 30 | Eyes for Qi (lesson) | meditate, moss | Elder Hu's Peak → Marsh Edge → Reed Shallows (by array) | 8 s |
| 31 | Eyes for Qi (lesson) | hand in | Reed Shallows → Marsh Edge → Elder Hu's Peak (by array) | 8 s |
| 32 | Outer Trial (lesson) | three spars | Elder Hu's Peak → Gate Street → Pavilion Rooftops (by array) | 15 s |
| 33 | Outer Trial (lesson) | hand in to the hall master | Pavilion Rooftops | 2 s |

Total plain walking 187 s (3.1 min) over 33 trips and 56 rooms walked; 0 trips over 35 s; the longest 17 s; back-and-forth: none.

### The Cloud Sect, now

| # | Quest | To | Rooms walked | Plain walk |
|---|---|---|---|---|
| 1 | Entry Trial | the trial bell | Fairground → Entry Trial (Cloud) | 5 s |
| 2 | Entry Trial | the Trial Puppet | Entry Trial (Cloud) | 2 s |
| 3 | Fish-Gutting Fists | Shen Lian | Entry Trial (Cloud) → Fairground | 5 s |
| 4 | A Disciple's Chores (side) | the steward | Fairground → Cliff Stair | 4 s |
| 5 | A Disciple's Chores (side) | the first spot | Cliff Stair | 2 s |
| 6 | A Disciple's Chores (side) | the second spot | Cliff Stair | 2 s |
| 7 | A Disciple's Chores (side) | the grey stain | Cliff Stair | 3 s |
| 8 | A Disciple's Chores (side) | hand in | Cliff Stair | 1 s |
| 9 | The Weapon Hall | the weapon master | Cliff Stair → Sword Court → Weapon Hall and Forge | 12 s |
| 10 | The Weapon Hall | the dummies | Weapon Hall and Forge | 1 s |
| 11 | The Weapon Hall | hand in | Weapon Hall and Forge | 1 s |
| 12 | Strange Tracks | the steward's lesson: the gate's transfer array | Weapon Hall and Forge → Sword Court → Cliff Stair | 11 s |
| 13 | Strange Tracks | the first grey patch (by the array) | Cliff Stair → Marsh Edge (by array) | 1 s |
| 14 | Strange Tracks | the second | Marsh Edge | 3 s |
| 15 | Strange Tracks | the third: the token hums | Marsh Edge | 3 s |
| 16 | The Humming Token | the Hollowed Boarlets, here | Marsh Edge | 3 s |
| 17 | The Humming Token | hand in: the mentor comes down | Marsh Edge | 3 s |
| 18 | Mei Qing's Errand | Mei Qing at the watch post | Marsh Edge | 2 s |
| 19 | Mei Qing's Errand | reed frogs (moss), boarlets (hides) | Marsh Edge | 5 s |
| 20 | Mei Qing's Errand | hand in at the watch post | Marsh Edge | 5 s |
| 21 | (on the way) | the hall master offers a spar | Marsh Edge → Cliff Stair → Sword Court (by array) | 13 s |
| 22 | Tea for the Elder (side, on the way) | the gardener's favour | Sword Court → Array Court | 6 s |
| 23 | (on the way) | two elders overheard in the court | Array Court | 2 s |
| 24 | Grey at the Edges | report to the mentor (and the tea) | Array Court → Elder Sung's Peak | 12 s |
| 25 | (the Level) | hunt to Bone Forging 7 | Elder Sung's Peak → Marsh Edge (by array) | 9 s |
| 26 | The First Current | Lu | Marsh Edge → Reed Shallows → Lotus Ferry Village | 17 s |
| 27 | The First Current | the Qi spring | Lotus Ferry Village | 5 s |
| 28 | The First Current | hand in | Lotus Ferry Village | 5 s |
| 29 | Eyes for Qi (lesson) | the mentor | Lotus Ferry Village → … (2 rooms) → Elder Sung's Peak (by array) | 18 s |
| 30 | Eyes for Qi (lesson) | meditate, moss | Elder Sung's Peak → Marsh Edge → Reed Shallows (by array) | 10 s |
| 31 | Eyes for Qi (lesson) | hand in | Reed Shallows → Marsh Edge → Elder Sung's Peak (by array) | 12 s |
| 32 | Outer Trial (lesson) | three spars | Elder Sung's Peak → Array Court → Sword Court | 19 s |
| 33 | Outer Trial (lesson) | hand in to the hall master | Sword Court | 4 s |

Total plain walking 204 s (3.4 min) over 33 trips and 57 rooms walked; 0 trips over 35 s; the longest 19 s; back-and-forth: none.

<!-- /AFTER -->

What the tables show:

- **About 3–3.5 minutes of plain walking** for the whole stretch, down from 18–20. No trip is over 20 seconds. The
  arrays are taken six or seven times.
- **No back-and-forth.** The marsh's three errands are one visit. The lessons' trips from the peak are one array away,
  and the Outer Trial ends in its own yard.
- **No empty room is crossed again and again.** Only the Marsh Edge (three times, from its array to its west way) and
  one or two sect rooms are crossed without a stop. The first walk through the sect's grounds is its discovery, with
  something in each room.

## The check

`python3 tools/data/sect_walks.py --check`, run by `tools/run_tests.sh` ("sect_walks"), holds the stretch to two rules:

- **No plain walk over 35 seconds.** That is about four rooms crossed at the sprint pace. The old stretch had twelve
  trips per sect over it, up to two minutes. The new one's longest is 17–19 seconds (the Marsh Edge to Lu at the
  docks; the village to the mentor for Eyes for Qi), so the rule leaves room for a room or two more before it trips.
- **No immediate back-and-forth**: a trip straight back to the room the trip before came from, both at least 20
  seconds.

It also checks every stop against the built data:

- every stop's person or thing stands in that room;
- a stop marked as a giver or hand-in is that quest's own person;
- every wayside stop has a scene staged for that sect in that room;
- every quest of the stretch has its stops.

A quest that moves a step elsewhere, or a room that loses its array, fails the check until the itinerary follows.

The walk itself is played in the game by `tests/topdown_tutorial.gd`, for both sects:

- the steward's lesson, and the gate's array taken to the watch post;
- the token humming at the third patch;
- the mentor come down to the marsh, taking the hand-in, and gone again;
- Mei Qing's Errand taken and handed in at the watch post;
- the first walk up with its three things on the way, the gardener's tea carried up, and the mentor's word;
- the peak's array keyed (the way down to the marsh is one array);
- The First Current reached by the peak's array.

The tracker's go button is checked walking the body onto the Cliff Stair's array, up to Elder Sung's peak and back down
on it. The end-of-prototype gate stays shut and says why.

## The screens

`tools/dev/sect_capture.tscn` plays both sects' stretches in the game from `topdown_tutorial`'s checkpoints after the
Weapon Hall (`-- --keep="The Weapon Hall,The Weapon Hall (Cloud)"`). It saves these shots into
`docs/redesign/feedback/sect/`.

| The steward shows the array (Jade) | The hand-off | Where to? |
|---|---|---|
| ![](sect/a_jade_01_the_steward_shows_the_array.png) | ![](sect/a_jade_02_step_onto_the_array.png) | ![](sect/a_jade_03_the_array_asks_where_to.png) |

| Out at the watch post | The watch post | The token hums |
|---|---|---|
| ![](sect/a_jade_04_out_at_the_watch_post.png) | ![](sect/a_jade_05_the_watch_post.png) | ![](sect/a_jade_06_the_token_hums.png) |

| Elder Hu comes down | At the marsh | Mei Qing at the post |
|---|---|---|
| ![](sect/a_jade_07_the_mentor_comes_down.png) | ![](sect/a_jade_08_the_mentor_at_the_marsh.png) | ![](sect/a_jade_09_mei_qing_at_the_watch_post.png) |

| On the way: a spar offered | Elders overheard | The gardener's favour |
|---|---|---|
| ![](sect/a_jade_10_on_the_way_a_spar_offered.png) | ![](sect/a_jade_11_on_the_way_elders_overheard.png) | ![](sect/a_jade_12_on_the_way_the_gardeners_favour.png) |

| The peak's array keyed | The peak's array |
|---|---|
| ![](sect/a_jade_13_the_mentor_keys_his_array.png) | ![](sect/a_jade_14_the_peaks_array.png) |

| The Cloud Sect's lesson | Where to? | Elder Sung comes down |
|---|---|---|
| ![](sect/b_cloud_01_the_steward_shows_the_array.png) | ![](sect/b_cloud_03_the_array_asks_where_to.png) | ![](sect/b_cloud_07_the_mentor_comes_down.png) |

| On the way: the poles and the post | The gardener's favour | Elders overheard |
|---|---|---|
| ![](sect/b_cloud_10_on_the_way_a_spar_offered.png) | ![](sect/b_cloud_11_on_the_way_the_gardeners_favour.png) | ![](sect/b_cloud_12_on_the_way_elders_overheard.png) |

| Elder Sung's word | His peak's array |
|---|---|
| ![](sect/b_cloud_13_the_mentor_keys_his_array.png) | ![](sect/b_cloud_14_the_peaks_array.png) |

## Tests changed, and why

- **`tutorial_order`** (the side-view walk): Strange Tracks is now done at the third patch with The Humming Token under
  way, and the tracker keeps the player at the marsh. It no longer walks back up to the mentor for the report. It
  checks that the Weapon Hall opens the arrays, with the gate's and the watch post's keyed.
- **`topdown_tutorial`**:
  - The walk follows the route the tracker's go button follows, arrays included (`travel`, `take_array`).
  - The Humming Token is handed in at the marsh to the mentor who came down, and Mei Qing's Errand at the watch post.
    Before, the walk went up the peak and back, and to Artisan Row and back.
  - The Jade disciple now plays Mei Qing's Errand and Grey at the Edges too, so both sects' first walks up and their
    scenes are played.
  - After The Humming Token the tracker's Next is Mei Qing's Errand at the Marsh Edge, not at Artisan Row.
  - The First Current is reached by the peak's array.
  - Auto-path is checked through an array.
- **`valley_run`**: chapter 2 follows the new places, so the mentor is met at the marsh and Mei Qing at the watch post.
  Its outdated copper step is gone.
- **`data_validation`**: it knows the two new requirement kinds.
- **`story_scenes`**: it holds the new scenes to the same rules as every scene, with no change to the suite.

## Left, and for the user

- **The array's page is the dialogue page** with an empty portrait frame, like the rare herb's and the chess
  problem's choices. A compass-like page of its own (the teleport page's look) would suit it better.
- **Walking still works.** The long road through Stoneford and the valley is still there for a player who ignores the
  arrays, and the tracker takes the array only once the token knows both ends.
- **The Marsh Edge's reed frogs drop willow moss three times in ten.** Mei Qing's five moss still take about fifteen
  frogs before herb gathering opens. That is fighting, not walking, so it is left, but it could be a quest drop, as her
  hides are.
- **Elder Hu's descent is light, not a flying sword.** It is a column of the sect's light with a wave where he lands;
  there is no sword or cloud to ride in the figure set. The user may want a flying sword and a cloud drawn for the two
  mentors.
