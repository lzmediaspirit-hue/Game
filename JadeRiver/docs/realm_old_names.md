# The old scrolls' names · a Codex cross-reference

Decision 1 of `docs/roadmap_master_ui.md` §6 (conflict C1): Jade River keeps its own nineteen great realms. The Codex
adds one entry per great realm giving "the names the old scrolls use": the nearest rung on the ladder most readers of
cultivation stories already know. A reader who meets Heart Tempering can then place it at once.

Nothing else changes. `data/realms.json`, the strings, quests, docs and tests keep the game's names. The old names
appear only in these Codex entries.

## Rules

- **One old rung per great realm.** The old ladder's rungs are wider than Jade River's, so two realms often share one
  rung. Each entry then says which half it is (lower and upper layers, early and late).
- **Shared words only.** The rungs are the genre's common vocabulary, which comes from the inner-alchemy ladder: Qi
  Refining, Foundation Establishment, Core Formation, Nascent Soul and on. Where English renderings differ, the Codex uses
  the plainest one, and the table lists the others for reference only.
- **No one work's coinage.** A name that belongs to a single serial's own ladder stays out of the Codex text. For
  example, "Immortal Ascension" is the name of one serial's sixth rung, so the entries say a cultivator "ascends" and
  keep "Ascension" only as the step into the immortal ranks.
- **In-world voice.** Each entry is a sect scholar's note that sets the valley's register beside scrolls copied far
  away. It never names a book, an author or the real world.
- **The mapping follows C1's sketch.** Qi Kindling ≈ Qi Refining, Heart Tempering ≈ Foundation Establishment, Cloud
  Stride and Spirit Awakening ≈ Core Formation, Heaven Glimpse ≈ Nascent Soul; the rest is placed by lifespan
  (`max_years` in `realms.json`, from `tools/data/realms.py:87-90`), by what the realm unlocks, and by its energy.
- **A known overlap.** The Qi Refining Pill is the pill for Heart Tempering 9 → Cloud Stride 1, while the old rung
  named Qi Refining is Qi Kindling. The Cloud Stride entry says why the pill has that name.

## The table

| # | Great realm | Levels | Sub-levels | Max years | The old scrolls' name (in the Codex) | Also met as (reference only) | Why it maps there |
|---|---|---|---|---|---|---|---|
| 0 | Mortal | 0 | 1 | 80 | Mortal | — | No method yet; the ordinary span |
| 1 | Bone Forging | 1–9 | 9 stages | 100 | Body Refining | Body Tempering, Bone Tempering | The body stages before Qi: they grow by training, and the first Qi arrives only at stage 7. The old ladders set body refining below Qi Refining |
| 2 | Qi Kindling | 10–18 | 9 stages | 120 | Qi Refining (lower layers) | Qi Condensation, Qi Gathering | The first technique and the first Primal Qi held in the meridians; a span barely above a mortal's, as the old rung's |
| 3 | Qi Unfurling | 19–27 | 9 stages | 150 | Qi Refining (upper layers) | Qi Condensation (late) | Still Primal Qi. Heaven's Cleansing at its gate is the old ladders' marrow-washing, and Qi first leaves the body (ranged Qi at Qi Unfurling 1), which they place in Qi Refining's top layers |
| 4 | Heart Tempering | 28–36 | 9 stages | 200 | Foundation Establishment | Foundation Building | The last Primal Qi realm and a 200-year span, the old rung's usual figure; the Heart Trial at its end is the classic heart-demon trial before the core |
| 5 | Cloud Stride | 37–45 | 9 stages | 300 | Core Formation (early) | Golden Core, Gold Elixir | The Qi condenses into a core on entry, and Core Forging grades it (9 to 5, or 4); True Qi replaces Primal Qi; flight opens; the first heavenly tribulation is out of it |
| 6 | Spirit Awakening | 46–54 | 9 stages | 500 | Core Formation (late) | Golden Core (complete) | The core is whole and the Mind Lake and Spirit Sense open; 500 years, the golden core's usual span; the step out asks for a Dao at tier 4 |
| 7 | Heaven Glimpse | 55–63 | 3 orders | 800 | Nascent Soul (early) | Primordial Infant | The first realm of orders, Heavenly Dao insight and the valley's ceiling; a six-bolt tribulation into it; the span nears the nascent soul's thousand years |
| 8 | Sage | 64–72 | 3 orders | 1,200 | Nascent Soul (late) | — | From Sage the soul flees a broken body to the shrine (`stats.json` `soul_escape`), the nascent soul's own mark; a new energy (Sage Qi ×1.7) and 1,200 years |
| 9 | Sage Sovereign | 73–81 | 3 orders | 2,000 | Spirit Transformation (early) | Deity Transformation, Soul Formation, Spirit Severing | 2,000 years; the step out asks for a Soul pool of 1,500 and the Presence Trial: the soul, not the body, is now the centre |
| 10 | Will Manifest | 82–90 | 3 orders | 3,000 | Spirit Transformation (late) | — | Presence: the will pressing on weaker foes, the old scrolls' "might" of a high cultivator |
| 11 | Sphere Lord | 91–99 | 3 orders | 5,000 | Void Refining (early) | Void Tempering, Dao Seeking | The Sphere reshapes the ground around the cultivator (a domain); 5,000 years |
| 12 | Law Touching | 100–108 | 3 orders | 8,000 | Void Refining (late) | — | Law Qi and World Laws: the laws of a world answer; 8,000 years |
| 13 | Monarch | 109–117 | 3 orders | 12,000 | Body Integration | Unity, Fusion | Monarch Qi; Monarch's Weight; the Throne-Sworn draw on one world as their own: body, soul and world as one; over ten thousand years |
| 14 | Half-Heaven Monarch | 118 | 1 | 20,000 | Great Vehicle (early) | Mahayana, Great Accomplishment | Half a step into heaven; the Dao Sigil screen opens |
| 15 | Dao Sigil | 119 | 1 | 30,000 | Great Vehicle (complete) | — | Realm, Daos, Presence and Sphere pressed into one foundation; the seven powers refined |
| 16 | Heaven's Threshold | 120 | 1 | 50,000 | Tribulation Crossing | Tribulation Transcendence | The last rung before the heavens: the ten-wave tribulation and the Inner World forming, the only breakthrough whose failure takes something back |
| 17 | Inner Heaven | 121–165 | 9 ranks | 100,000 | The immortal ranks, entered by Ascension | True Immortal and above | Heavenforce (×3.5) in place of Qi and a world carried inside; nine ranks like the old immortal grades |
| 18 | World Genesis | 166+ | 1 | Without end | Dao Ancestor | Creator, Origin | Makes, restores and mends worlds; no stages and no end of years |

## The Codex entries

Each entry has an `id`, a `title` and a `body`, the shape of `codex()` in `tools/data/story.py`. The rows below are
ready to add there.

**Suggested unlock:** each realm's entry is added to the account's Codex the first time any character enters that great
realm, the way `heavenly_tribulation` is added when first met (`progression_authority.gd:533`). The header entry and the
Mortal and Bone Forging entries come with the Codex itself. Unlocking by realm keeps later realms' names hidden until
they are reached, as the existing `realms` entry does ("… and beyond the valley, more").

| id | Title | Body |
|---|---|---|
| `old_scrolls` | The old scrolls | Scrolls copied far from this valley name the realms by an older ladder. Its rungs are wider than ours, so two of our realms often stand on one of theirs. This register sets their names beside ours, one realm at a time. |
| `old_scrolls_mortal` | Mortal · the old scrolls | The old scrolls have no rung for this: they write "mortal" and start counting at the first breath of Qi. A mortal body keeps its eighty years or so, and the scrolls do not pretend otherwise. |
| `old_scrolls_bone_forging` | Bone Forging · the old scrolls | The old scrolls call this labour Body Refining and set it below the ladder, a threshold rather than a rung. It is the work we do at the stumps and stones: the bones first, and the first Qi only at the seventh stage. |
| `old_scrolls_qi_kindling` | Qi Kindling · the old scrolls | The old scrolls call the first rung of Qi "Qi Refining", and count it in layers where we count stages. Our Qi Kindling is its lower layers: the breath is caught and kept, but it does not yet leave the body. |
| `old_scrolls_qi_unfurling` | Qi Unfurling · the old scrolls | Our Qi Unfurling is the upper layers of the old scrolls' Qi Refining. They too wash the marrow at its gate, as Heaven's Cleansing does, and they too say the Qi first leaves the hand here. |
| `old_scrolls_heart_tempering` | Heart Tempering · the old scrolls | The old scrolls call this rung Foundation Establishment and give it two hundred years, as we do. At its end they set a trial of the heart, where a cultivator meets the demons they carried in; our Heart Trial is that door. |
| `old_scrolls_cloud_stride` | Cloud Stride · the old scrolls | Here the old scrolls say the Qi condenses into a core, and they call the rung Core Formation, or the Golden Core. They grade the core as we do, and a poor grade is carried for the rest of the road. The pill our furnaces call Qi Refining is named for the work it does here, not for the old rung of that name. |
| `old_scrolls_spirit_awakening` | Spirit Awakening · the old scrolls | The old scrolls still count this as Core Formation, its later half, when the core is whole and the spirit's eye opens. They give it five hundred years, and so do we. |
| `old_scrolls_heaven_glimpse` | Heaven Glimpse · the old scrolls | Where we glimpse heaven, the old scrolls say a Nascent Soul is born: a small self of spirit that grows out of the core. They divide it in three, as we divide Heaven Glimpse into orders. |
| `old_scrolls_sage` | Sage · the old scrolls | The old scrolls keep the Nascent Soul through what we call Sage, and they say what we say: a Sage's soul can leave a broken body and flee to safety. Their thousand years is close to our twelve hundred. |
| `old_scrolls_sage_sovereign` | Sage Sovereign · the old scrolls | The old scrolls call the next rung Spirit Transformation, when the soul, not the body, becomes the centre of the cultivator. They say a trial of will stands at its end, as our Presence Trial does. |
| `old_scrolls_will_manifest` | Will Manifest · the old scrolls | The old scrolls keep Spirit Transformation here too, and write of its later half as the time when a cultivator's will weighs on the weaker. What they call might, we call Presence. |
| `old_scrolls_sphere_lord` | Sphere Lord · the old scrolls | Past the soul the old scrolls set Void Refining, when a cultivator begins to shape the space around them. Our Sphere is that shaping, drawn as a circle. |
| `old_scrolls_law_touching` | Law Touching · the old scrolls | The old scrolls end Void Refining where we begin to touch the Laws: the void is refined until the laws of a world answer. They put eight thousand years on it, as we do. |
| `old_scrolls_monarch` | Monarch · the old scrolls | The old scrolls call this rung Body Integration: body, soul and world become one. A Monarch's Weight is their oneness with heaven and earth, and a Throne-Sworn Monarch is their cultivator who has made one world their own. |
| `old_scrolls_half_heaven_monarch` | Half-Heaven Monarch · the old scrolls | The old scrolls call the last long rung before the heavens the Great Vehicle, and count its first step as half a step into heaven. Half-Heaven Monarch is that step. |
| `old_scrolls_dao_sigil` | Dao Sigil · the old scrolls | The old scrolls close the Great Vehicle when everything a cultivator is has been pressed into one foundation. Our Dao Sigil is that pressing, with the seven powers set in it one by one. |
| `old_scrolls_heavens_threshold` | Heaven's Threshold · the old scrolls | The old scrolls call this rung Tribulation Crossing: the cultivator stands where the heavens try them one last time before they rise. Ours adds the forming of a world, the one breakthrough that can take back what it gave. |
| `old_scrolls_inner_heaven` | Inner Heaven · the old scrolls | Here the old scrolls say the cultivator ascends and becomes an immortal, and they count the immortal ranks from the True Immortal upward. Our Inner Heaven is that ascent with a world carried inside; its nine ranks answer to their grades. |
| `old_scrolls_world_genesis` | World Genesis · the old scrolls | The old scrolls stop counting here and call one who makes and mends worlds a Dao Ancestor. They give no end of years, and neither do we. |

The same rows as `codex()` entries:

```python
        {"id": "old_scrolls", "title": "The old scrolls", "body": "Scrolls copied far from this valley name the realms by an older ladder. Its rungs are wider than ours, so two of our realms often stand on one of theirs. This register sets their names beside ours, one realm at a time."},
        {"id": "old_scrolls_mortal", "title": "Mortal · the old scrolls", "body": "The old scrolls have no rung for this: they write \"mortal\" and start counting at the first breath of Qi. A mortal body keeps its eighty years or so, and the scrolls do not pretend otherwise."},
        {"id": "old_scrolls_bone_forging", "title": "Bone Forging · the old scrolls", "body": "The old scrolls call this labour Body Refining and set it below the ladder, a threshold rather than a rung. It is the work we do at the stumps and stones: the bones first, and the first Qi only at the seventh stage."},
        {"id": "old_scrolls_qi_kindling", "title": "Qi Kindling · the old scrolls", "body": "The old scrolls call the first rung of Qi \"Qi Refining\", and count it in layers where we count stages. Our Qi Kindling is its lower layers: the breath is caught and kept, but it does not yet leave the body."},
        {"id": "old_scrolls_qi_unfurling", "title": "Qi Unfurling · the old scrolls", "body": "Our Qi Unfurling is the upper layers of the old scrolls' Qi Refining. They too wash the marrow at its gate, as Heaven's Cleansing does, and they too say the Qi first leaves the hand here."},
        {"id": "old_scrolls_heart_tempering", "title": "Heart Tempering · the old scrolls", "body": "The old scrolls call this rung Foundation Establishment and give it two hundred years, as we do. At its end they set a trial of the heart, where a cultivator meets the demons they carried in; our Heart Trial is that door."},
        {"id": "old_scrolls_cloud_stride", "title": "Cloud Stride · the old scrolls", "body": "Here the old scrolls say the Qi condenses into a core, and they call the rung Core Formation, or the Golden Core. They grade the core as we do, and a poor grade is carried for the rest of the road. The pill our furnaces call Qi Refining is named for the work it does here, not for the old rung of that name."},
        {"id": "old_scrolls_spirit_awakening", "title": "Spirit Awakening · the old scrolls", "body": "The old scrolls still count this as Core Formation, its later half, when the core is whole and the spirit's eye opens. They give it five hundred years, and so do we."},
        {"id": "old_scrolls_heaven_glimpse", "title": "Heaven Glimpse · the old scrolls", "body": "Where we glimpse heaven, the old scrolls say a Nascent Soul is born: a small self of spirit that grows out of the core. They divide it in three, as we divide Heaven Glimpse into orders."},
        {"id": "old_scrolls_sage", "title": "Sage · the old scrolls", "body": "The old scrolls keep the Nascent Soul through what we call Sage, and they say what we say: a Sage's soul can leave a broken body and flee to safety. Their thousand years is close to our twelve hundred."},
        {"id": "old_scrolls_sage_sovereign", "title": "Sage Sovereign · the old scrolls", "body": "The old scrolls call the next rung Spirit Transformation, when the soul, not the body, becomes the centre of the cultivator. They say a trial of will stands at its end, as our Presence Trial does."},
        {"id": "old_scrolls_will_manifest", "title": "Will Manifest · the old scrolls", "body": "The old scrolls keep Spirit Transformation here too, and write of its later half as the time when a cultivator's will weighs on the weaker. What they call might, we call Presence."},
        {"id": "old_scrolls_sphere_lord", "title": "Sphere Lord · the old scrolls", "body": "Past the soul the old scrolls set Void Refining, when a cultivator begins to shape the space around them. Our Sphere is that shaping, drawn as a circle."},
        {"id": "old_scrolls_law_touching", "title": "Law Touching · the old scrolls", "body": "The old scrolls end Void Refining where we begin to touch the Laws: the void is refined until the laws of a world answer. They put eight thousand years on it, as we do."},
        {"id": "old_scrolls_monarch", "title": "Monarch · the old scrolls", "body": "The old scrolls call this rung Body Integration: body, soul and world become one. A Monarch's Weight is their oneness with heaven and earth, and a Throne-Sworn Monarch is their cultivator who has made one world their own."},
        {"id": "old_scrolls_half_heaven_monarch", "title": "Half-Heaven Monarch · the old scrolls", "body": "The old scrolls call the last long rung before the heavens the Great Vehicle, and count its first step as half a step into heaven. Half-Heaven Monarch is that step."},
        {"id": "old_scrolls_dao_sigil", "title": "Dao Sigil · the old scrolls", "body": "The old scrolls close the Great Vehicle when everything a cultivator is has been pressed into one foundation. Our Dao Sigil is that pressing, with the seven powers set in it one by one."},
        {"id": "old_scrolls_heavens_threshold", "title": "Heaven's Threshold · the old scrolls", "body": "The old scrolls call this rung Tribulation Crossing: the cultivator stands where the heavens try them one last time before they rise. Ours adds the forming of a world, the one breakthrough that can take back what it gave."},
        {"id": "old_scrolls_inner_heaven", "title": "Inner Heaven · the old scrolls", "body": "Here the old scrolls say the cultivator ascends and becomes an immortal, and they count the immortal ranks from the True Immortal upward. Our Inner Heaven is that ascent with a world carried inside; its nine ranks answer to their grades."},
        {"id": "old_scrolls_world_genesis", "title": "World Genesis · the old scrolls", "body": "The old scrolls stop counting here and call one who makes and mends worlds a Dao Ancestor. They give no end of years, and neither do we."},
```
