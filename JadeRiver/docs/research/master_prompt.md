# Jade River — Full Review, Expansion & QA Master Prompt

## Role & Context

You are working on **Jade River**, a 2D pixel-art, xianxia-themed, MapleStory-style mobile game (Godot, landscape orientation). Act as a combined team: senior game designer, 2D MMORPG game psychologist, QA tester, content designer, and technical reviewer.

Use the **deep-research skill** for any task that requires external research (MapleStory, Idleon, Douluo Dalu, game psychology). Spawn dedicated research agents where specified. Work through the phases in order; each phase lists its deliverable and acceptance criteria.

**Global rules:**
- Every document you produce must be written in prompt-engineering style: each finding or recommendation phrased as an actionable instruction that a future agent could execute directly (what to do, where, how, and the acceptance criteria) — not vague commentary.
- Add every approved change to the roadmap.
- Fix bugs directly in code as you find them; the review document describes findings and resolutions, **not** an open bug list.
- Split all game logic and documentation into two tracks: **Single Player (now)** and **Online (future)**. Every system must state how it behaves in each track.

---

## Phase 1 — World Structure & Exploration Audit

**Goal:** The game must never feel like there is one linear way to play.

1. Audit the current world map. Compare its structure to MapleStory's world design: many interconnected maps, distinct biomes, towns as hubs, travel between regions as content in itself.
2. Produce a world-expansion plan: number of maps per region, biome variety (forests, mountains, rivers, deserts, spirit realms, sect grounds, etc.), portal/travel connections, and hidden/optional maps that reward exploration.
3. Design an **on-screen animation system** (same pixel-art style and theme) for key scenarios: realm breakthroughs, story beats, boss intros, rare drops, and any other moment that benefits from visual punctuation. Specify trigger, duration, and art requirements for each animation type.

**Deliverable:** World & Exploration section of the Full Review doc + roadmap entries.
**Acceptance:** A player can chart multiple viable routes through the world; travel and exploration are core activities, not filler.

---

## Phase 2 — Item Economy & Build Diversity

**Goal:** A diverse cultivation world where no two players (in a future online mode) look or build the same.

1. Research how many items MapleStory carries (weapons, armor, accessories, consumables, materials) and derive a realistic target item count for an MMORPG of this scope.
2. Design new items to reach that target, organized by: slot, rarity tier, realm requirement, elemental affinity, cultivation-path synergy, and set bonuses. Ensure multiple distinct build archetypes (body cultivator, sword dao, alchemist, beast tamer, etc.) each have full gear paths.
3. Generate a **wiki-style document with one entry per item**: name, icon description, slot, stats, rarity, level/realm requirement, how to obtain (drop/craft/shop/quest), and lore line.

**Deliverable:** Item Wiki document + item-design section in the Full Review + roadmap entries.
**Acceptance:** Two players following different paths would naturally end up with visibly different gear and stats.

---

## Phase 3 — Player-Experience Playthrough (UX/QA Pass 1)

**Goal:** Experience the game exactly as a new player would.

1. Play the game start to current end. Log everything that hurts the experience:
   - UI/UX friction, unclear feedback, confusing menus
   - Collision problems, invisible walls, terrain snags
   - Interaction conflicts — e.g., the training dummy triggers an NPC-talk action instead of attack; conversations that force a manual exit every time
   - Overlapping objects that block proper interaction
   - Houses/shops with no visible door or entrance
   - Quest flow gaps, dead ends, missing guidance
2. Fix each bug/issue in code as you find it. Record each as: *finding → root cause → fix applied → verification*.
3. Analyze long-term engagement: research the psychology of why MapleStory retains players for years (progression pacing, social loops, daily reasons to log in, "one more level" design) and write concrete instructions for building the same pull into Jade River — the player must **always have a reason to keep playing**.

**Deliverable:** UX Findings section (written as user-experience narrative + resolutions) in the Full Review; all found bugs fixed.

---

## Phase 4 — Game Psychology & Sensory Design

**Goal:** Apply the psychology of 2D platformer/MMORPG appeal deliberately.

Acting as a professional 2D-MMORPG game psychologist, research and document:
1. **Visual reward escalation** — e.g., MapleStory high-level skills hitting many monsters at once with screen-filling particles; how multi-hit numbers, particles, and screen shake drive dopamine response. Define Jade River's skill-VFX escalation curve per realm.
2. **Color psychology** — which palettes drive engagement, rarity color-coding, damage-number colors, environment mood palettes per biome.
3. **Feedback loops** — hit-stop, sound, knockback, loot fountains, level-up fanfare.
4. Write an implementation plan: for each finding, state exactly what to change/add in Jade River (system, asset, parameter), phrased as executable instructions.

**Deliverable:** Psychology & Feel section of the Full Review + roadmap entries.

---

## Phase 5 — Quest Guidance & Side Content

**Goal:** The player always knows where the next main quest is and how to get there.

1. Implement main-quest tracking: current objective always visible, with directional guidance (arrow/minimap marker/route hint) to the target map.
2. Add side quests across the world, big-world style.
3. Implement NPC quest indicators above heads (MapleStory convention):
   - **Exclamation mark** — NPC has a new quest available
   - **Exclamation mark in a different color** — player completed a quest for this NPC *and* the NPC has another new quest
   - **Question mark** — quest completed, ready to turn in to this NPC
   - **Three dots in a grey speech bubble** — quest in progress
4. Verify indicators update correctly through the whole quest lifecycle.

**Deliverable:** Quest-guidance system implemented + section in the Full Review.

---

## Phase 6 — Drops, Sprites & Content Volume

1. **Monster drops:** ensure every monster has an equipment drop table (in addition to materials/currency). Balance drop rates by rarity and monster tier.
2. **Sprite audit:** review NPC, equipment, terrain, and monster sprites. Identify gaps and generate/spec whatever is missing. Prioritize **monster/enemy sprite diversity** — many visually distinct enemies per region.
3. Cross-link: every item in the Item Wiki must have at least one source; every monster must appear in the Monster Wiki with its full drop table.

**Deliverable:** **Monster & Drops Wiki** — one entry per monster: name, sprite description, region, level/realm, stats, behavior, and complete item-drop table with rates. Plus roadmap entries for new sprites.

---

## Phase 7 — Boss Design Research

1. Deep-research MapleStory and Legends of Idleon boss fights: mechanics, phases, telegraphs, attack patterns, arena design, enrage timers, reward structures, and what specifically makes those fights fun and re-runnable.
2. Compare against current Jade River bosses; identify every gap.
3. Write implementation instructions for bringing that boss-fight style into Jade River: phase design per boss, telegraphed attacks, mechanics that demand movement/skill, and reward loops.

**Deliverable:** Boss Design section of the Full Review + roadmap entries.

---

## Phase 8 — Soul Rings System (Douluo Dalu)

Create a **Fable 5 agent** dedicated to this task:

1. Deep-research the **Douluo Dalu** story and extract **only the Soul Ring system** (ignore all other systems from that setting).
2. Produce a full detailed explanation of soul rings: how they're obtained (hunting spirit beasts), beast age → ring color/power tiers, ring abilities, absorption limits/risks, and progression rules.
3. Design its adaptation for Jade River: how it fits the xianxia storyline and world logic, when it unlocks (start or mid-game — choose based on the internal logic of how soul rings work), how it interacts with cultivation realms, combat, and builds.
4. Add the system to the roadmap with implementation steps.

**Deliverable:** Soul Ring System design document (research + adaptation), prompt-engineering style.

---

## Phase 9 — Xianxia Theming & Realm Naming

1. Rename/verify all cultivation realms to use widely recognized xianxia terms, e.g.: Qi Refining, Foundation Establishment, Qi Condensation, Golden Core, Origin Spirit, Nascent Soul, Soul Formation, Enlightenment, Reborn, Transcendent (extend the ladder as needed).
2. Audit the entire game — story, items, locations, NPC dialogue, art direction notes — and shift anything wuxia-leaning toward **xianxia**: immortal cultivation, spirit qi, heavens/tribulations, sects and daos, rather than mortal martial arts.

**Deliverable:** Terminology & Theme section of the Full Review + applied renames.

---

## Phase 10 — Core Cultivation Loop (World Rule)

Verify and enforce this loop as a canonical game-world rule; correct any system that deviates:

1. **Cultivate to gain Qi.** Optionally find a Qi-rich location on the world map; the player chooses Cultivate to convert time into progress; higher-quality Qi locations are more efficient. Qi acts as experience for the current stage (modified by all other relevant factors).
2. **Reach a bottleneck.** Each realm has stages (Early / Middle / Late / Peak). When a stage fills, normal cultivation stops.
3. **Minor breakthroughs** advance within the same realm. They normally use a stage-appropriate pill (e.g., Qi Refining Pill), but not as a universal rule — breakthrough resources vary: pills, treasures, energy, techniques, Dao comprehension, bloodlines, or special opportunities.
4. **Major breakthroughs** move to the next realm and normally require some combination of: a breakthrough elixir, special treasures/materials, elemental or regional items, and sometimes a trial, dungeon, boss, or special quest. Material quality affects both breakthrough success chance and the stats gained afterward.

**Deliverable:** Cultivation Loop spec in the Full Review; code aligned to it.

---

## Phase 11 — Full QA Pass & Final Report

1. Run a second full QA pass across the whole game after all changes; fix every bug found.
2. Compile the **Full Review Document** containing all sections above (world, items, UX, psychology, quests, drops, bosses, theming, cultivation loop), each written in prompt-engineering style, with bugs already fixed (no open bug list).
3. In the same document, split the game architecture into **Single Player** (current) and **Online** (future) tracks, stating for each system what changes when online launches.
4. Update the roadmap with everything added across all phases, and add the **Full Review Document itself** to the work roadmap: register it as a deliverable and convert each of its sections' recommendations into scheduled roadmap tasks.

**Final deliverables checklist:**
- [ ] Full Review Document (all sections, prompt-engineering style, bugs fixed) — added to the work roadmap as its own deliverable, with each of its sections' recommendations broken into roadmap tasks
- [ ] Item Wiki (one entry per item)
- [ ] Monster & Drops Wiki (one entry per monster, full drop tables)
- [ ] Soul Ring System design document
- [ ] Updated roadmap
- [ ] All found bugs fixed in code and verified
