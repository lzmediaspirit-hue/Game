### V9f3 · Dungeons and story rooms climb (Part 8 room verticality catalogue)

Thirteen rooms of the Mudwater Hideout, the Drowned Shrine, Mist Peak, Summit Ridge and the story instances now follow
their rows in the Part 8 room verticality catalogue. Each is built by hand (`tools/data/catalogue_rows_dungeons.py`).
The room lint checks all of them. Every portal, quest object, story event and spawn works as before.

- **Stockade** (Mudwater Hideout):
  - Two wooden palisades, 160 high, cross the yard from the back wall. Each has a gate at the front.
  - Two timber watchtowers stand at 180. Climb them by ladder, or jump up from a stack of crates.
  - A bandit archer holds each tower. Each tower has a chest.
  - The west tower keeps the gatekeeper's spare gate key. It shows only if you have lost your own key. The key that
    opens the Stockade is still the Caravan Road drop.
- **Tunnels:**
  - Two spike pits. Their floors hurt (bleeding) and are drawn as beds of sharpened stakes.
  - Crumbling planks at 60 cross each pit. Each plank gives way a moment after you land on it and comes back 5 s later.
    Low log beams (40) sit at each lip of the pits.
  - A narrow dry path runs along the back wall past both pits.
  - Jars wait on the crumbling planks.
  - A timber landing at 60 between the pits holds the chest. Archers keep the landing and the pit lips.
  - The old rotten boards at 100 are gone.
- **Loot Cave:**
  - Three pairs of stalagmites. Each pair is a low one (80) and a high one (160); the low one is the step up.
  - Crates to climb and break.
  - The loot sits on the high stalagmites: the chest and jars.
  - Archers stand on the low stalagmites.
- **Flooded Gate:**
  - The gate's basin is flooded with deep water, and a current drains it west through the gate.
  - Three planks float on the water, drifting back and forth. Ride them across, or swim with Breath Control.
  - An old sluice deck at 60 on the far bank (ladder) holds the chest and jars.
  - The broken gate lintel at 200 above it is still a Paths Above ledge (double jump).
- **Hall of Lanterns:**
  - A chain of lantern platforms hangs across the hall. Three swing on their ropes. Two go round in a circle, and each
    of those lifts you a tier: from 100 to 200, and from 200 to 300.
  - Time your jumps to the swings. The chain ends at the lantern loft (300), where the chest is.
  - Rock ledges at 100 and 200, with ropes and a chain, are the safe way up and the rests between.
  - Two of Lu's inscriptions are now on the ledges.
  - Paper Talisman Ghosts drift between the tiers.
- **Scripture Well:**
  - The well is a descent. Climb the rope to the rim at 300, then drop down the ledges at 200 (the bucket chain) and
    100 to the flooded bottom.
  - The bottom is deep water: Breath Control's swim, beside the flooded shaft to the Drowned Grotto.
  - Lu's inscriptions are cut into the rim and the ledges; two are new.
  - Talisman ghosts float down the shaft. The rim holds the chest.
  - The Riverbreath rite circle and its waves keep their dry ground.
  - The catalogue asks for a shaft that goes below the floor, to −300. The engine draws the floor as one slab at 0, so
    no pit can be shown yet. The well descends from a high rim instead.
- **Abbot's Sanctum:**
  - The four bell ledges (100 and 200) each have a rope. The high ledges also have a stone lion plinth (80) to jump from.
  - At two thirds of his health the Drowned Abbot floods the sanctum. The water rises to 30, holds for 14 s and
    drains. The ledges and plinths stay dry.
- **Forgotten Monastery:**
  - The main hall's roof rises to 176. Two ruined side halls have roofs at 88. Each has a ladder.
  - Between them are rotten upper floors (176 and 88) that crumble underfoot.
  - Formation remnants on the three roofs can be read.
  - A hidden stair runs from the west hall to the east side of the main hall. It is two hidden doors that lead to each
    other; Spirit Sense finds them.
  - The Soulbell Flower grows on the west roof. The chest is on the main hall.
  - The insight stone and the Nine-Bough Jade Tree keep their places.
- **Ascension Gate:**
  - Six cloud platforms at 200 ring the open sky in front of the arch. They give footing at 200 during the Gate
    Guardian's flight phase, which works as before.
  - Fallen ring stones (60) are the step up for anyone not flying. The arch (220) keeps its ladder.
- **Frozen Shrine:**
  - Rock ledges at 100 (ropes) stand at either end.
  - Between them, icicle platforms at 200 crack and fall under a foot, and lead to the shrine ledge.
  - The rare Soulbell Flower grows on the shrine ledge, beside the shrine's chest. The Mystic ore vein is on the west
    ledge.
  - The ice sheets on the ground are unchanged.
- **Trial of Reflections:**
  - A mirror arena: two ledges at 100, left and right, each the mirror of the other.
  - Each has a rope and a step stone. A bronze mirror stands at the back.
  - The Reflection's fight starts and ends as before.
- **Gu's Warehouse:**
  - Crate stacks (40 and 80) stand under two catwalks at 176 along the back wall. Ladders lead up.
  - Rafters at 264 run above the catwalks and over the open middle of the floor, where the bandits stand. This is the
    stealth route; Concealment suits it.
  - Gu's strongbox, with the Little Pagoda, is hidden up in the east rafters.
- **Siege of Two Sects:**
  - The wall's battlement walkway at 160 replaces the two broken ramparts at 100. Climb it by stone steps (40, 80, 110)
    or a ladder.
  - A tower at 240 (ladder) stands at each end, facing east, where the Hollow and the Behemoth come.
  - The siege event, its waves and the Behemoth are unchanged.

Not yet possible without new engine work or art:
- **Scripture Well:** the drop below the floor (see above).
- **Trial of Reflections:** the Reflection does not use the tiers. As a story boss it neither jumps nor climbs.
- **Abbot's Sanctum:** the Abbot fights on the floor. He neither jumps nor climbs, like every boss.
- **Siege of Two Sects:** the Behemoth has no weak points to aim at.
- **Art:** the lantern platforms use the timber deck art. The ruined roofs use the painted halls, which are whole.
