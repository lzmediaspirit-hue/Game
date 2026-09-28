# The story staged: in-engine scenes and a playable opening (decision 39)

Decision 39 (`docs/roadmap_master_ui.md` §6): the story is staged, not only told. People walk, face, emote and speak
in the world, the camera moves, things happen, and the opening teaches the player by what happens rather than by
menus. This page has three parts. §1 is a short study of how top-down action RPGs stage their stories. §2 lists the
principles taken from it. §3 describes what was built: the scene system and the opening rewritten as scenes.

Each claim in §1 is marked. **Confirmed** means a source below says it. **Inferred** means it is our reading of the
sources or of common practice, and nobody has checked it against the game. Web access was limited: searches worked,
but fetching pages was blocked, so the confirmed claims rest on search-result summaries of the pages cited.

---

## 1. How top-down action RPGs stage their stories

### 1.1 CrossCode and Alabaster Dawn (Radical Fish Games)

- **CrossCode's cutscenes are in-engine.** They are made of dialogue and animation, and the characters in dialogue
  have portraits with facial expressions. The developers spent a lot of time on cutscenes so that play stays fluent
  and the story still carries. *Confirmed* [1][2].
- **CrossCode also has side messages.** These are short lines at the lower left of the screen that run while you
  play, so the story goes on while you move. The last 50 can be read again from the pause menu. *Confirmed* [1][2].
  - The lesson for us: the story has two channels. A cut takes over the screen; a live line lets play continue.
    *Inferred.*
- **Alabaster Dawn adds a "Cinematics system"** for cutscenes shown from outside the usual in-game view. Its 2025 demo
  had "a good bunch of" scripted cutscenes, two bosses and a dungeon. *Confirmed* [3][4].
  - Most of its story beats still play in the normal top-down view, with the camera and the people moving on the map.
    *Inferred* from the demo reports and CrossCode's practice.
- **Players asked for dialogue skipping in CrossCode.** It came up on the game's forum [5]. *Confirmed* that the
  question was asked. *Inferred:* the answer is to make skipping safe and quick, not to leave it out.

### 1.2 Speech, emotes and scripts elsewhere

- **Speech balloons over heads and "emotion balloons" are a standard tool.** A "!" for surprise, a heart, an anger
  vein, a silent "..." and so on, shown over a character for a moment. RPG Maker has them as a built-in event command
  [6]. *Confirmed.*
- **Stardew Valley scripts its events the same way.** An event is a list of commands: move an actor by tiles, face a
  direction, emote, speak (a dialogue box), move the camera ("viewport move") and fade [7]. *Confirmed.* It is the same
  vocabulary as ours: actor steps, camera steps, screen steps.
- **Portrait boxes versus balloons:**
  - a portrait box gives a face and a long line room (CrossCode's dialogue [1]);
  - a balloon keeps your eyes on the scene and on who is speaking (RPG Maker, Stardew [6][7]).

  Games use both: the box for a conversation, the balloon for a line in passing. *Inferred.*

### 1.3 Teaching through what happens

- **A Link to the Past (1991)** opens in the rain. Link walks out of his house, soldiers blocking the way teach the
  controls when he talks to them, and his dying uncle gives him the sword and teaches the spin attack [8]. The lesson
  is part of the story. *Confirmed.*
- **Half-Life 2's "pick up that can"** teaches a verb (pick up and throw) through a guard's order within the story,
  instead of separating long cutscenes from separate tutorials [9]. *Confirmed.*
- **Hodent's onboarding rules:** teach one thing at a time, by doing, in context, when it is needed
  (`docs/research/player_motivation.md` §1.9, [20] there). *Confirmed.*

### 1.4 Skipping, letterbox and accessibility

- **Hold to skip.** A skip on any single key loses scenes by accident. Holding the button while a ring fills prevents
  that, and the ring shows that a hold is needed [10][11]. *Confirmed.*
- **Accessibility.** The Game Accessibility Guidelines ask for a way to bypass anything that is not the core
  mechanic [12]. *Confirmed.* Cutscenes fall under that. *Inferred.*
- **Letterbox bars** tell the player that control has been taken away. They are common across games, and this is
  *inferred* from practice with no single source. The moments already use the same bars (`docs/moments_design.md`
  §3.3).

## 2. Principles for Jade River's staged story

1. **Show it in the world.** People walk to each other, face, emote and speak where they stand. The camera goes to
   what matters and comes back to you. Title cards are only for chapter-like beats: dawn, the night, the fair.
2. **Keep scenes short:** 10–40 s of staged time each. This is checked in the data, and every scene's cuts count on
   the first hour's play clock.
3. **Teach by handing over.** A scene sets up a need, such as a crab at Washer Mei, a graze from a falling jar or a
   race. Then it hands you the controls with a gentle in-world prompt over the thing to act on, and waits for you to
   do it. It never waits for you to open a menu without also ending by itself.
4. **Two channels.** A cut holds the game still under the letterbox. A live part plays around you while you act.
   A fight always wins: a cut never starts in one, and a fight that breaks into a cut turns it live.
5. **Always skippable, never lost.** A tap moves a line on. A hold skips to the next hand-off. What the skipped part
   asked of the game still happens: a checkpoint's graze, a flag.
6. **Authorities own the state.** A scene asks, and the Quest authority decides and keeps: begun, checkpoints, seen.
   A scene cut short by quitting resumes at its last checkpoint. A scene you have seen never plays again.
7. **Respect Reduce motion.** The camera cuts instead of panning, the bars and the title fade in instead of sliding,
   the rain holds still, there is no shake, and flashes follow the Bright flashes setting.
8. **Original writing.** Lotus Ferry's own people, places and lines. The references inform the system only.

---

## 3. As built (2026-09-28)

### 3.1 The scene system

| Piece | File | What it does |
|---|---|---|
| Data | `tools/data/scenes.py` → `data/scenes.json` | Each scene has a room on the grid, a requirement, an optional trigger event, its actors and its steps; `settings` holds the paces, reading times, the 10–40 s bounds, the hold to skip and the letterbox |
| Rules | `scripts/presentation/scene_rules.gd` (`SceneRules`) | The step kinds, where an actor starts, paths on foot, how long each step holds the stage, and `problems()`, the validation the suites run |
| Director | `scripts/presentation/scene_director.gd` (`SceneDirector`) | Starts scenes (on a trigger, or on standing in the room), runs the steps, moves the people and the camera, handles the modes, skip, resume and input. With no view it runs headless on the same clock |
| Stage | `scripts/presentation/scene_stage.gd` (`SceneStage`) | Draws weather, speech balloons (docked at the screen's edge with a name when the speaker is off screen), emotes, the hand-off prompt (a chevron and plate over a thing, or a ring round a HUD control), the letterbox, fades, flashes, the title card (the moments' ink band) and "Hold to skip" |
| Authority | `QuestAuthority` `scene_begin`, `scene_mark`, `scene_end`; `QuestState.scenes` | Keeps a scene's checkpoint and whether it has been seen, applies a checkpoint's effects once (from `SCENE_EFFECTS`: flags, and a graze that never takes HP under 40%), and emits `scene_started`, `scene_marked` and `scene_ended` |
| Hooks | `TopdownWorld` (`stage_cam`, `stage_zoom`, `figures`, `fade_labels`, `PropView.place_at`), `TopdownPlaces.person`, `topdown_player.stage_pose`, `HUD.scene_lock`, `MomentView` (`in_fight`, `letterbox`, `draw_title`, `play_row`), `UiKit.wrap` | Shared code, with nothing copied. A cut fades out the HUD and the names over the world |

**Steps:**

- **Actors:** `move` (waypoints walked around obstacles by the room's path search, a walk or a run; a prop sails
  straight), `face` (eight rows), `emote` (`!`, `?`, `...`, note, heart, anger, sweat, idea), `pose` (the top-down
  figure's actions), `say` (a balloon, or `box: portrait` for the dialogue page's portrait strip).
- **Camera:** `camera` (pan to, then follow, an actor, a cell, a thing, a way or a foe), `zoom`, `shake`,
  `letterbox`.
- **Screen:** `fade`, `flash` (under the flash limiter), `title`.
- **World:** `spawn` and `despawn` (extra people and props), `door`, `weather` (storm, rain, clear), `moment` (a
  moments row), `fx`, `sound`.
- **Flow:** `wait`, `wait_input`, `wait_event`, `branch` (on a requirement: quest, flag, sect), `label`, `goto`, `mark`
  (a checkpoint, with effects).
- **Hand-off:** `handoff`. It has a prompt, a target, and `until` events (the Quest matchers, with `"active"` for the
  character). It can also have `done_if` (a requirement), a timeout, and `then` (cut or live).

**The three modes:**

- **Cut:** `Game.pause`, `HUD.scene_lock`, the letterbox, the HUD and labels faded.
- **Hand-off:** play resumes with the prompt showing.
- **Live:** the script runs while you play.

### 3.2 The opening as a playable story

Every beat of `docs/tutorial_order.md` from waking to the sect choice has a scene. Guo, the gate and Lu's boat keep
their quests, gates and tests as they were. Staged times are measured by `SceneRules.length`.

| Step | Scene (room) | What happens | What it teaches by doing |
|---|---|---|---|
| 0–1 | `opening_dawn` (Fisher's Hut) | Title "Jade River: Lotus Ferry, the hour before dawn". Aunt Ping wakes you, fetches the tea and gives it to you, and says you have your mother's stubborn chin. Lu wants you at the docks | The Bag, through a gift (a prompt that ends by itself); walking, with the door as the hand-off |
| 2 | `river_dawn` (Home Lane) | A boat slips by on the river. Washer Mei and Aunt Ping talk about grey water. The wind takes Little Dou's kite onto the inn roof | The world's small life; the kite is the lost item the next lesson looks for |
| 2 | `four_errands` | Lu's four errands, shown where they wait: Guo at his stump, Dou, Old Ma's door, Granny's door | Where to go, in any order |
| 3a | `guo_fists` | Guo shows jab, cross, jab on his stump | Attack: "Punch the stump" |
| 3b | `kite_route` | Dou shows the way up: crates, the hall roof, the jump to the inn | Jump, shown on the route |
| 3e | `tower_race` | Shen Lian counts down and runs for the tower | Sprint, by a chase: "Race him to the bell" |
| 3d | `granny_jar` | A jar falls from the herb loft and grazes you (a real graze, through a checkpoint) | Bag → Quick-use, then drink: the healing slot, taught by an injury |
| 4 | `east_gate` | Guo opens the East Gate (the camera goes to the gate, which glows) | Where the fight is |
| 4 | `crabs_mei` (Reed Shallows) | The crabs have Washer Mei backed against the reeds. She thanks you and walks home | The first fight: "Drive off a crab" (its drop, the first weapon, is hers to point at) |
| 6 | `hollow_rises` (the night) | Title "That Night", a storm, the river boils, Dou's cry, Granny's call for the hut | The night's task |
| 7 | `river_token` (Lu's Boat) | Lu names the Hollowed eel and your gift, then sits to meditate | Cultivate: "Meditate: tap Cultivate" |
| 7 | `first_breakthrough` | After the breakthrough's moment: a zoom, and Lu's "Bone Forging: your first step". Handed the token, he shows Flowing Palm on the river and says why you leave: the sects choose at Stoneford this spring. Go west | The breakthrough as a scene; the reason to leave home |
| 8 | `market_thief` (Market Street) | A purse snatched at the tea house, the thief gone over the west road | The rooftop thief, foretold |
| 9 | `fair_arrival` (Fairground) | Title "The Recruitment Fair". The recruiters call over each other; Shen Lian finds you | The choice ahead |
| 9 | `sect_chosen` | Your sect's recruiter welcomes you and its name is written over the crowd; Shen Lian's rivalry begins | The choice, marked |

There are 15 scenes, each 10–26 s staged. In the top-down walk, the first hour's clock includes their cuts and still
meets its pacing (`tests/tutorial_order.gd` invariant 14).

### 3.3 Tests

- **`story_scenes`** (new, in `tools/run_tests.sh`) checks:
  - that every scene validates (`SceneRules.problems`);
  - the opening in the character's own view: Aunt Ping's figure walks, the cut holds the game still, and the
    hand-off gives it back and keeps a checkpoint;
  - that the opening resumes after a reload at its last checkpoint, with Aunt Ping where the script put her;
  - that a seen scene never replays;
  - that a hold skips to the next hand-off and the skipped graze still lands;
  - that the camera cuts under Reduce motion;
  - that a fight turns a cut live.
- **`topdown_tutorial`** plays every scene of the tutorial to its end on a headless director as the walk reaches it.
  The walk's own actions satisfy the hand-offs. The cut time counts on the play clock, and every earlier invariant
  and check still passes.
- **The event contract** gains `scene_started`, `scene_marked`, `scene_ended`, and four events the hand-offs wait on
  that it had missed: `page_opened`, `quest_failed`, `object_hit` and `quick_use_changed`.

**Screenshots** (`tools/dev/topdown_capture.tscn -- --story`, in `docs/redesign/phase5/story/`):

- 01–05: the opening, its walk strip and both hand-offs;
- 06–08: dawn in Home Lane;
- 09: Lu's errands;
- 10–12: Granny's jar and prompts;
- 13: the gate;
- 14–15: the crabs;
- 16–17: the night;
- 18–20: Lu's boat and the breakthrough;
- 21: the thief;
- 22–25: the fair, the portrait box and the sect chosen.

### 3.4 Not built, or different

- **No new body poses** (`AGENTS.md`). The people and the player are the top-down figure (`TopdownFigure`, decision
  32), in the actions its manifest has (`data/topdown/character.json`: idle, walk, run, the strikes, cast, meditate,
  hurt and so on, and the side view's names it plays under another). `SceneRules` checks every `pose` against it.
- **Scenes play only in rooms on the height grid**, so a side-view character sees none.
- **Zoom is a whole-view zoom** of the pixel viewport (1.25 in the breakthrough). It is not integer-scaled.
- **Actors' movement is presentation.** A scene's people walk home when it ends. Nothing they do is saved, except
  where a resumed scene's script puts them.
- **The portrait box is the dialogue page's own strip.** It is used once, for the recruiter's welcome in
  `sect_chosen`. Every other line is a balloon, which keeps the scenes short.

## Sources

1. CrossCode, *Wikipedia*. <https://en.wikipedia.org/wiki/CrossCode>
2. Radical Fish Games, "CrossCode Recap 2013". <https://www.radicalfishgames.com/?p=1504>; and CrossCode, *TV Tropes*. <https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/CrossCode>
3. Radical Fish Games, "2025 Wrap-Up & Introducing a New Feature". <https://www.radicalfishgames.com/?p=7879>
4. Radical Fish Games, "Alabaster Dawn Demo Release". <https://www.radicalfishgames.com/?p=7730>; press sheet <https://www.radicalfishgames.com/presskit/sheet.php?p=alabaster_dawn>
5. "Dialogue Skipping?", CrossCode Steam discussions. <https://steamcommunity.com/app/368340/discussions/0/3220528325740587546/>
6. "Show Balloon Icon", *RPG Maker Wiki*. <https://rpgm.fandom.com/wiki/Show_Balloon_Icon>
7. "Modding: Event data", *Stardew Valley Wiki*. <https://stardewvalleywiki.com/Modding:Event_data>
8. The Legend of Zelda: A Link to the Past, *Wikipedia*. <https://en.wikipedia.org/wiki/The_Legend_of_Zelda:_A_Link_to_the_Past>; "Link's Uncle", *Zelda Wiki*. <https://zelda.fandom.com/wiki/Link%27s_Uncle>
9. "'Pick up that can': Storytelling in Half-Life 2", *Game Developer*. <https://www.gamedeveloper.com/design/-quot-pick-up-that-can-quot-storytelling-in-half-life-2>
10. Febucci, "Unity Skip Cutscene Button: Timeline Implementation [With Hold-to-Skip]". <https://blog.febucci.com/2019/02/skip-cutscenes-button/>
11. "Problem: Unclear Cutscene Skip", *itch.io*. <https://itch.io/blog/644198/problem-unclear-cutscene-skip>
12. Game Accessibility Guidelines, "Offer a means to bypass gameplay elements that aren't part of the core mechanic". <https://gameaccessibilityguidelines.com/offer-a-means-to-bypass-gameplay-elements-that-arent-part-of-the-core-mechanic-via-settings-or-in-game-skip-option/>
