extends Node
## Named, seeded random streams (Part 2 · Randomness). Rules take a stream as an
## argument and never create their own. Seeds and positions are saved so a fight,
## a drop, a craft or a breakthrough replays exactly from a saved seed.

const CHARACTER_STREAMS := ["combat", "loot", "crafting", "breakthrough", "taming", "affix", "world", "fishing", "pet", "minigame"]
const ACCOUNT_STREAMS := ["sect", "account"]

var _streams: Dictionary = {}   # owner -> {name: RandomNumberGenerator}
var _seeds: Dictionary = {}     # owner -> base seed

static func mix(seed_value: int, name: String) -> int:
	return hash(str(seed_value) + ":" + name) & 0x7fffffffffff

func ensure(owner: String, seed_value: int) -> void:
	if _streams.has(owner): return
	_seeds[owner] = seed_value
	_streams[owner] = {}

func stream(owner: String, name: String) -> RandomNumberGenerator:
	if not _streams.has(owner): ensure(owner, hash(owner) & 0x7fffffff)
	var owned: Dictionary = _streams[owner]
	if not owned.has(name):
		var rng := RandomNumberGenerator.new()
		rng.seed = mix(int(_seeds[owner]), name)
		owned[name] = rng
	return owned[name]

func forget(owner: String) -> void:
	_streams.erase(owner)
	_seeds.erase(owner)

## Streams are saved as strings: JSON numbers cannot hold 64-bit state exactly.
func snapshot(owner: String) -> Dictionary:
	var out := {"seed": str(_seeds.get(owner, 0)), "streams": {}}
	for name in _streams.get(owner, {}):
		out.streams[name] = str(_streams[owner][name].state)
	return out

func restore(owner: String, data: Dictionary, fallback_seed: int) -> void:
	forget(owner)
	var seed_value := int(str(data.get("seed", str(fallback_seed))))
	if seed_value == 0: seed_value = fallback_seed
	ensure(owner, seed_value)
	for name in data.get("streams", {}):
		var rng := stream(owner, name)
		rng.state = int(str(data.streams[name]))

## Stateless helper for rules: pick a weighted entry from [{weight: w, ...}].
static func weighted(rng: RandomNumberGenerator, entries: Array, key := "weight") -> Dictionary:
	var total := 0.0
	for e in entries: total += float(e.get(key, 1))
	if total <= 0.0 or entries.is_empty(): return {}
	var roll := rng.randf() * total
	for e in entries:
		roll -= float(e.get(key, 1))
		if roll < 0.0: return e
	return entries.back()
