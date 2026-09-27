# The soul-ring system of Soul Land (Douluo Dalu): research for P8

Research for P8a in `docs/roadmap_master_ui.md` (row M41, decision 2 in §6, conflict C5 in §5). It covers the soul-ring
system of the Douluo Dalu (Soul Land) novels and their adaptations only: how rings are won from spirit beasts, the age
tiers and their colours and power, the ring abilities, the absorption limits and risks, bones as far as they touch
rings, and how the ring count follows rank. The adaptation built on it is `docs/soul_bands_design.md`.

Date of research: 2026-09-26. Jade River state: commit 6ef9c7a (P2 (e)).

The game never names the source (C5, C16). This page is the only place its terms appear.

---

## 0. Sources, method and confidence

**How this was researched.** Web search only. The network proxy refused every page fetch tried:
soulland.fandom.com, baike.baidu.com, en.wikipedia.org, appgamer.com and shapes.inc all answered "blocked by the network
egress proxy". So every claim below comes from the search engine's extract of the named page, not from the page itself.
Where an extract listed several pages and it was not clear which one said a thing, the claim says so and its confidence
drops. No chapter of the novel was read in full, and no episode was watched.

Many search results were fan fiction set in the same world (fan works on WebNovel, Scribble Hub, Sufficient Velocity,
Wattpad, FanFiction.net). They were read past and not used. Two other fan wikis that came up (STARD, Death's Adventure
Record) describe fan universes and were not used either.

**Confidence labels** (the house format of `idle_gathering_research.md` and `ui_reference_notes.md`):

- **[OFFICIAL]**: the publisher's or rights holder's own page. None was reachable for this topic; the label is kept for
  completeness.
- **[WIKI]**: a community encyclopedia (the Soul Land Fandom wiki, Baidu Baike's English pages, Wikipedia). Medium to
  high on the novel's rules; the Fandom wiki mixes novel and animation, and says so only sometimes.
- **[GUIDE]**: a third-party guide, or a chapter page whose edition (licensed or fan translation) could not be
  confirmed. Medium.
- **[PLAYER]**: one reader's or viewer's post, a fan blog, a question-and-answer page, or a fan summary site. Low to
  medium; used only where a WIKI source agrees or where the text says it stands alone.
- **[INFERRED]**: my reading or synthesis. Treat it as a design suggestion.

Sources are cited as `[S3 · WIKI]`; the full list with page titles and URLs is §11. Every citation here is to a
search-engine extract (fetches were refused), so "(extract)" is not repeated on each line.

---

## 1. The work in brief

- *Douluo Dalu* is a xuanhuan novel series by Tang Jia San Shao, serialised on the Qidian site from 2008
  [S23 · WIKI] [S24 · WIKI]. The first book follows Tang San; later books (*Soul Land II* to *IV*) move thousands of
  years on in the same world [S28 · PLAYER] [S10 · WIKI].
- The animated *Soul Land* began weekly on Tencent Video on 20 January 2018 [S25 · WIKI]. A live-action series,
  *Douluo Continent*, aired in 2021 on Tencent Video and CCTV [S26 · WIKI].
- Mobile games adapt the ring system into slots and hunts (§8) [S21 · GUIDE] [S22 · GUIDE].
- Everyone awakens a **martial soul** (an animal, a plant or a tool) at six; those with innate soul power can become
  **soul masters** [S20 · PLAYER]. The rest of this page is about what a soul master adds to that martial soul from
  beasts.

---

## 2. How a ring is won

- A **soul ring** is part of what a **soul beast** leaves when it dies, when it sacrifices itself, or when it makes a
  contract with a human [S1 · WIKI].
- **Only the one who delivers the killing blow can absorb the ring**, and only while at a cultivation bottleneck: rank
  10, 20, 30 and so on [S1 · WIKI]. Innate full soul power is rank 10, so a gifted child already stands at the first
  bottleneck and advances once a suitable ring is found [S1 · WIKI] [S3 · WIKI].
- So a ring is **hunted, not found**. The master chooses a beast whose nature suits the martial soul, and the kind of
  beast shapes the skill. Tang San's mentor Yu Xiaogang held that a plant martial soul can take an animal's ring, and
  picked a hundred-year snake for Tang San's Blue Silver Grass because the grass is tough and snakes bind and poison
  [S12 · WIKI] [S14 · WIKI].
- The kill is a hunt in the forest with guards: Tang San's first ring came from a Datura Snake of a little over 400
  years in the Spirit Hunting Forest [S13 · WIKI] [S14 · WIKI].
- **A ring can be stored only with special means.** In the later books the Tang Sect's soul tools strip the killer's
  aura from a dying beast, which leaves an ownerless ring that can be kept and absorbed later [S1 · WIKI].
- **Later books add living alternatives.** *Soul Land II* and *III* introduce **soul spirits**: a beast binds its
  spirit and life to a master and lives on in them, a complement to rings rather than a kill [S10 · WIKI]. The Spirit
  Pagoda was founded to make artificial soul spirits and cut the killing of beasts, which were near extinction
  [S11 · WIKI] [S28 · PLAYER]. A master who receives a soul spirit has 24 hours to absorb it, or it dies [S10 · WIKI].
  (The sources disagree on whether soul spirits start in book II or III; §10.)
- **A ring can be given.** Xiao Wu, a soft-boned rabbit of more than 100,000 years in human form, sacrifices herself for
  Tang San; her soul is kept within one of his rings [S19 · WIKI].

Not found: how long an unabsorbed ring lasts after a kill in the first book. Only the soul spirit's 24 hours is stated.

---

## 3. Age tiers, colours and power

A beast's age is its cultivation, and the ring takes its colour from it.

| Age of the beast | Ring colour | Notes |
|---|---|---|
| 10–99 years | White | Very weak [S2 · WIKI] |
| 100–999 years | Yellow | The common first and second rings [S2 · WIKI] [S20 · PLAYER] |
| 1,000–9,999 years | Purple | Strong [S2 · WIKI] [S1 · WIKI] |
| 10,000–99,999 years | Black | Very strong; typical of elite masters [S2 · WIKI] [S1 · WIKI] |
| 100,000 years and more | Red | Extremely powerful; usually only Titled Douluo hold one [S2 · WIKI] [S1 · WIKI] |
| 200,000 years and more | Orange or gold | Later books [S1 · WIKI] [S10 · WIKI] |
| 1,000,000 years and more | Gold, tinted by the beast's attribute | Later books; the sources disagree (§10) [S1 · WIKI] [S10 · WIKI] |

What age means for the beast and the ring:

- Beasts are graded as 10, 100, 1,000, 10,000 and 100,000-year beasts [S7 · WIKI].
- A 10,000-year beast's soul and mind rise to about a human's intelligence, so its ring carries a heavy shock to the
  absorber's soul [S2 · WIKI; the extract listed several pages, attribution medium].
- At 100,000 years a beast is about as strong as a Titled Douluo and faces a choice: live on (most die within a
  thousand years) or be reborn as a human and cultivate again [S7 · WIKI] [S20 · PLAYER].
- Some beasts of royal or noble blood are intelligent before 100,000 years, sometimes helped by a heaven-and-earth
  treasure [S7 · WIKI].
- **The older the ring, the stronger its skill and the larger the boost to soul power** [S4 · WIKI] [S1 · WIKI].

---

## 4. Ring abilities (soul skills)

- A **soul skill** comes from the beast's abilities and the martial soul's own nature together, and differs from master
  to master for the same beast [S4 · WIKI].
- **One skill per ring**, unless the ring is 100,000 years or older (two skills); a million-year ring may give up to four
  [S4 · WIKI].
- **A skill grows with its master.** Its effect is not a fixed value and can rise as the master cultivates
  [S4 · WIKI].
- The beast's traits carry across. Tang San's grass took the Datura Snake's toughness and the paralysing (not the
  deadly) part of its venom: a vine that binds a foe up to 50 metres away and paralyses it [S14 · WIKI].
- Tang San's first four rings as the wiki lists them [S15 · WIKI]:

  | Ring | Beast | Skill |
  |---|---|---|
  | 1 | Datura Snake | Bind (entangle and restrain) |
  | 2 | Ghost Vine | Parasite (seeds on the foe that burst later) |
  | 3 | Man-Faced Demon Spider | Spider Web Restraint (a strong bind) |
  | 4 | Pit Demon Spider | Blue Silver Prison (a group bind) and Blue Silver Thrust |

  A pattern shows: one martial soul, one line of skills (binding), each beast adding its own twist.
- **The seventh ring** is a qualitative step: at the rank-70 bottleneck the seven-ringed master gains the **martial soul
  true body**, a giant or enlarged form of the martial soul [S9 · WIKI].

---

## 5. Absorption limits and risks

### 5.1 A limit per ring

Yu Xiaogang's theory in the first book gives an age limit for each ring [S2 · WIKI] [S12 · WIKI]:

| Ring | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| Age limit (years) | 423 | 764 | 1,760 | 5,000 | 12,000 | 20,000 | 50,000 | under 100,000 | 100,000 |

- The novel later shows the theory to be wrong as a single rule: the limit depends on the martial soul's quality, the
  body's strength and the soul power, so masters differ, and with enough of all three even a first ring could be
  100,000 years [S2 · WIKI].
- Every bottleneck has an **optimal age**, the oldest ring that can be absorbed without real risk. Younger rings are safe
  but give less [S1 · WIKI].
- A 10,000-year ring is said to need at least rank 50, when body and mind have matured and the soul's shock is smaller
  [S1 · WIKI].
- A strong body raises the limit and speeds absorption at any age [S2 · WIKI; one extract, attribution medium].
- The live-action audience's summary: at ranks 10 and 20 a beast may not be older than 1,000 years, and the first ring
  is usually yellow [S20 · PLAYER].

### 5.2 What happens above the limit

- A ring older than the limit can be **rejected**: heavy injury or death [S1 · WIKI]. The strongest wording in the
  extracts is that the body **explodes**, and that meridians ("spirit pathways") and the soul-power pool too narrow for
  the flood **rupture**, crippling or killing [S1 · WIKI; that results page also listed fan fiction, so medium-low].
- Exceptional physique, soul power and will make the odds better, and a few masters have succeeded [S1 · WIKI].
- **The canonical case.** Tang San's third ring came from a Man-Faced Demon Spider over his limit. Its violent power
  almost broke out through his body again and again; each time his body held, he took in a sliver, and the ring slowly
  weakened, with the energy "cleansing" his body in great pain [S17 · GUIDE]. He came through and also gained an
  external bone (§7) [S16 · GUIDE]. The spider's age differs by source: over 2,000 years against a 1,760-year limit
  [S16 · GUIDE], or 10,000 years in a fan blog on the animation [S18 · PLAYER] (§10).
- **Absorption is a long, seated process**, and the absorber is in no state to fight [INFERRED from S17]. The soul
  spirit's 24-hour window (§2) is the only stated deadline.

---

## 6. Progression: ring count follows rank

Rank runs from 1 to 100; each ten ranks is a title and a bottleneck, and each bottleneck needs one more ring
[S3 · WIKI] [S1 · WIKI]:

| Ranks | Title (translations vary) | Rings |
|---|---|---|
| 1–10 | Spirit Scholar | 0 (the first ring breaks rank 10) |
| 11–20 | Spirit Master | 1 |
| 21–30 | Spirit Grandmaster | 2 |
| 31–40 | Spirit Elder | 3 |
| 41–50 | Spirit Ancestor | 4 |
| 51–60 | Spirit King | 5 |
| 61–70 | Spirit Emperor | 6 |
| 71–80 | Spirit Sage (also "Soul Saint") | 7 (martial soul true body) |
| 81–90 | Spirit Douluo | 8 |
| 91–99 | Titled Douluo (91–94), Super Douluo (95–98), Limit Douluo (99) | 9 |
| 100 | God | — |

- The **"best configuration"** for a nine-ringed master is two yellow, two purple and five black. A single red ring is
  rarer and better than any best configuration [S1 · WIKI].
- A master can hold at most nine rings, as a body can hold at most six bones [S5 · WIKI].

---

## 7. Bones, as far as they touch rings

- A **soul bone** is what a beast's body leaves at death, besides its ring. Drops are very rare, rarer the younger the
  beast; a 100,000-year beast leaves one for certain, and resentment, a willing death or gratitude raise the odds
  [S6 · WIKI].
- Six kinds: skull, torso, left and right arm, left and right leg; the torso is the strongest [S5 · WIKI] [S6 · WIKI].
- A bone's skills are fixed by the beast's core abilities and do not change with the absorber. Bones of beasts up to
  10,000 years give one skill; 100,000-year bones give at least two [S5 · WIKI].
- **Bones are not bound by the age limit** that governs rings; they grow with their master's strength [S5 · WIKI].
- Bones do not take up ring places. A master holds up to six standard bones beside nine rings, and rare **external
  bones** (Tang San's Eight Spider Lances, from the same spider as his third ring) grow with the user [S5 · WIKI]
  [S27 · PLAYER] [S16 · GUIDE].

What this means for rings: one kill can leave two separate things, a ring (the soul, bound to the killer, limited by
age) and sometimes a bone (the body, rare, unlimited by age, its own slots) [INFERRED from S1, S5, S6].

---

## 8. Adaptations

- **The animation** follows the novel's ring rules and colours; the wiki's episode pages give the same 423-year first
  limit and the Datura Snake [S13 · WIKI]. The wiki notes that some of Tang San's rings were changed for the animation
  (the third ring among them) [S18 · PLAYER].
- **The live-action series** keeps awakening at six, rings every ten levels and the colours; viewers summarise the
  first ring as usually yellow [S20 · PLAYER].
- **Mobile games** (*Soul Land: Advent of the Gods*) turn the system into slots and hunts [S21 · GUIDE]
  [S22 · GUIDE]:
  - a character gains a ring slot every ten levels, and each slot turns on a matching skill;
  - rings come from **spirit beast hunts**; the grade (age) of ring on offer depends on the difficulty the player has
    unlocked;
  - rings of the same slot give the same base stats but different effects;
  - a character's level caps its skills' level.

---

## 9. What the adaptation should keep [INFERRED]

1. **Win it by your own hand.** The killer alone takes the soul. It separates a band from a tamed beast cleanly.
2. **Choose the beast.** The fantasy is choosing a beast for its nature and hunting it, not a random drop.
3. **Age is the tier, and the tier is a colour.** A ring is read at a glance by its colour.
4. **The limit is personal and can be pushed.** A fixed per-slot table exists in the fiction, but the novel itself
   overturns it: body, soul and preparation move it. Going over is a gamble with harm on failure, and the reward is a
   ring that stays strong for a long time.
5. **The count follows rank.** Slots open at fixed steps of cultivation.
6. **One skill per ring, drawn from the beast, grown by the master.** The beast gives the shape, the master's own
   power gives the size.
7. **The body is separate.** Bones (for Jade River, beast cores) come from the same kill but do not use ring slots.
8. **Leave out** martial souls, the per-slot age table, the nine-ring configurations, the true body at seven, sacrifice
   and soul spirits: Jade River already has methods, Daos, contracts and spirit animals for those roles.

---

## 10. Gaps and conflicts

| Question | What the sources say | Used as |
|---|---|---|
| Million-year ring colour | "Purple red" in one extract of S1; "mostly gold" in another; gold with tints by attribute in S10; a white-gold ring for one mental beast | Not needed; Jade River has no tier above rank 9 |
| Where soul spirits start | Book II [S28 · PLAYER] or book III's Spirit Pagoda [S11 · WIKI]; S10 covers both | Not adopted |
| Tang San's third ring | Over 2,000 years, above a 1,760-year limit [S16 · GUIDE]; 10,000 years in the animation per a fan blog [S18 · PLAYER] | Only "over the limit, nearly failed" is used |
| How long an unabsorbed ring lasts | Not found for book I; 24 hours for a soul spirit [S10 · WIKI] | Jade River sets its own time (two minutes) |
| "The body explodes" | Stated in an extract whose results page also held fan fiction [S1 · WIKI]; "almost broke through his body" in the chapter extract [S17 · GUIDE] | Adopted as a named failure, softened to a survivable one |
| Absorption time | Not stated in a usable source | Jade River sets its own (18–24 s) |

---

## 11. Sources

Page titles as the search engine gave them. Every page was seen through the search engine's extract; no fetch
succeeded (§0).

| # | Page title | URL | Label |
|---|---|---|---|
| S1 | Soul Rings \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Soul_Rings | WIKI |
| S2 | Soul Ring_Baiduwiki | https://baike.baidu.com/en/item/Soul%20Ring/1429488 | WIKI |
| S3 | Spirit Ranks \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Spirit_Ranks | WIKI |
| S4 | Soul Skills \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Soul_Skills | WIKI |
| S5 | Soul Bone（a term in the fantasy novel Soul Land）_Baiduwiki | https://baike.baidu.com/en/item/Soul%20Bone/1473293 | WIKI |
| S6 | Soul Bones \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Soul_Bones | WIKI |
| S7 | Soul Beast \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Soul_Beast | WIKI |
| S8 | Soul Beast_Baiduwiki | https://baike.baidu.com/en/item/Soul%20Beast/1414511 | WIKI (listed with S2's extract on 10,000-year beasts; not cited alone) |
| S9 | Martial Souls \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Martial_Souls | WIKI |
| S10 | Soul Spirit \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Spirit_Souls | WIKI |
| S11 | Spirit Pagoda \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Spirit_Pagoda | WIKI |
| S12 | Yu Xiaogang \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Yu_Xiaogang | WIKI |
| S13 | Episode 007 \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Episode_007 | WIKI (the animation) |
| S14 | Datura Snake \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Datura_Snake | WIKI |
| S15 | Tang San/Abilities \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Tang_San/Abilities | WIKI |
| S16 | Soul Land Chapter 145 - Chapter 34: The Man-Faced Demon Spider Soul Ring Beyond Limits (Part 1)_1 - WebNovel | https://www.webnovel.com/book/soul-land_28854123108881805/chapter-34-the-man-faced-demon-spider-soul-ring-beyond-limits-(part-1)-1_77920581684625302 | GUIDE (novel chapter; edition not confirmed) |
| S17 | Soul Land -Douluo Dalu Chapter 146 - Tang San's Tyrannical Third Spirit Ability (1) - WebNovel | https://m.webnovel.com/book/soul-land--douluo-dalu_22741204305046205/tang-san%E2%80%99s-tyrannical-third-spirit-ability-(1)_63565801948500064 | GUIDE (novel chapter; edition not confirmed) |
| S18 | User blog:KhalilPhoenix/TANG SAN'S COMPLETE SPIRIT ABILITIES \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/User_blog:KhalilPhoenix/TANG_SAN'S_COMPLETE_SPIRIT_ABILITIES | PLAYER (fan blog) |
| S19 | Xiao Wu \| Soul Land Wiki \| Fandom | https://soulland.fandom.com/wiki/Xiao_Wu | WIKI |
| S20 | Background of martial soul, soul power, soul beast and soul ring in general (for non-anime watcher) - The Land of Warriors - MyDramaList | https://mydramalist.com/discussions/douluo-continent-2/132410-background-of-martial-soul-soul-power-soul-beast-and-soul-ring-in-general | PLAYER |
| S21 | Spirit Ring Guide - Soul Land: Advent of the Gods Wiki Guide | https://www.appgamer.com/soul-landadvent-of-the-gods/strategy-guide/spirit-ring-guide | GUIDE |
| S22 | Spirit Beast Hunt - Soul Land: Advent of the Gods Wiki Guide | https://www.appgamer.com/soul-landadvent-of-the-gods/strategy-guide/spirit-beast-hunt | GUIDE |
| S23 | Douluo Dalu（A fantasy novel series by Tang Jia San Shao.）_Baiduwiki | https://baike.baidu.com/en/item/Douluo%20Dalu/659076 | WIKI |
| S24 | Tang Jia San Shao - Wikipedia | https://en.wikipedia.org/wiki/Tang_Jia_San_Shao | WIKI |
| S25 | Soul Land（A web animation jointly produced by Tencent Penguin Pictures and Xuanji Technology.）_Baiduwiki | https://baike.baidu.com/en/item/Soul%20Land/986042 | WIKI |
| S26 | Douluo Continent - Wikipedia | https://en.wikipedia.org/wiki/Douluo_Continent | WIKI |
| S27 | Douluo Dalu (Soul Land) Spirit System \| Shapes | https://shapes.inc/fandom/douluo-dalu-soul-land/spirit-system | PLAYER (a fan summary site; used only beside S5) |
| S28 | Soul Land 2: The Peerless Tang Clan (TV Series 2023– ) - Plot - IMDb | https://www.imdb.com/title/tt28022382/plotsummary/ | PLAYER (user-written plot) |
