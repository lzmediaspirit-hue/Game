class_name RoomRuntime
extends RefCounted
## S17 · Live state of the loaded room: enemies, spawn slots, ground loot,
## projectiles, object states and the event timer. Scene-free; the World and
## Enemy authorities are its only writers.

var room_id := ""
var def: Dictionary = {}
var geometry := ZoneGeometry.new()
var enemies: Dictionary = {}          # uid -> EnemyState
var spawn_slots: Array = []           # [{spawn, point, enemy, elite, timer, uid, level_range, surface}]
var loot: Array = []                  # [{uid, item, count, instance, coins, x, y, ttl, age}]
var projectiles: Array = []           # [{uid, team, owner, x, y, alt, dir, speed, range, travelled, attack, pierce, hits, art, element}]
var objects: Dictionary = {}          # object id -> {state, timer, hits, cooldown}
var npcs_hidden: Dictionary = {}
var next_uid := 1
var elapsed := 0.0
var event: Dictionary = {}            # survival/escort events {id, remaining, ...}
var arrival_protection := 0.0
var first_visit := false

func uid() -> int:
	next_uid += 1
	return next_uid

func object_def(id: String) -> Dictionary:
	for o in def.get("objects", []):
		if str(o.get("id", "")) == id: return o
	return {}

func portal_def(id: String) -> Dictionary:
	for p in def.get("portals", []):
		if str(p.get("id", "")) == id: return p
	return {}

func width() -> float:
	return float(def.get("bounds", [0, 480, 1280, 480])[2])

func living_enemies() -> Array:
	var out: Array = []
	for u in enemies:
		var e: EnemyState = enemies[u]
		if e.alive: out.append(e)
	return out
