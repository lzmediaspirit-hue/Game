extends Node
## The only source of wall time (Part 2 · Time). Simulation time advances in ticks
## elsewhere; this service answers "what time is it" for offline gains, resets,
## build and batch timers. A backward clock grants nothing and resets the reference.

var debug_offset_s := 0.0          # debug console: shift time forward
var override_utc := -1.0           # tests: pin the clock
var override_tz_offset_s := -99999 # tests: pin the local time zone offset
## Tests: a simulated clock. Once pinned with `simulate`, "now" moves only as the simulation ticks (Game.tick calls
## `advance`) and by the debug offset, never with the wall clock, so a scripted run plays the same on a busy machine.
var simulated := false

func simulate(utc: float, tz_offset_s := 0) -> void:
	override_utc = utc
	override_tz_offset_s = tz_offset_s
	debug_offset_s = 0.0
	simulated = true

func advance(delta: float) -> void:
	if simulated and override_utc >= 0.0: override_utc += delta

func now_utc() -> float:
	if override_utc >= 0.0: return override_utc + debug_offset_s
	return Time.get_unix_time_from_system() + debug_offset_s

## A file-name-safe date and time for exports ("2026-09-25_14-03-12").
func file_stamp() -> String:
	return Time.get_datetime_string_from_unix_time(int(now_utc()), false).replace(":", "-").replace("T", "_")

func tz_offset_s() -> int:
	if override_tz_offset_s != -99999: return override_tz_offset_s
	return int(Time.get_time_zone_from_system().get("bias", 0)) * 60

func local_dict(utc: float) -> Dictionary:
	return Time.get_datetime_dict_from_unix_time(int(utc) + tz_offset_s())

## Seconds elapsed since `last_utc`, never negative. Returns {elapsed, valid}.
## `valid` is false when the clock moved backward: the caller grants nothing and
## stores the new reference.
func elapsed_since(last_utc: float) -> Dictionary:
	if last_utc <= 0.0: return {"elapsed": 0.0, "valid": true}
	var now := now_utc()
	if now + 1.0 < last_utc: return {"elapsed": 0.0, "valid": false}
	return {"elapsed": maxf(0.0, now - last_utc), "valid": true}

## The reset "day number": days since epoch shifted so a day starts at 04:00 local.
func reset_day(utc: float) -> int:
	var hour_s := float(ContentDB.curve("resets.daily_hour", 4)) * 3600.0
	return int(floor((utc + tz_offset_s() - hour_s) / 86400.0))

## Monday-04:00 week number. Unix day 0 (1970-01-01) was a Thursday.
func reset_week(utc: float) -> int:
	return int(floor((reset_day(utc) + 3) / 7.0))

## Seconds in one in-game day (S37: 48 real minutes).
func game_day_s() -> float:
	return float(ContentDB.curve("time_of_day.day_minutes", 48)) * 60.0

## The in-game day index of a moment.
func game_day(utc: float) -> int:
	return int(floor(utc / game_day_s()))

## How far through its in-game day a moment is, 0..1.
func day_fraction(utc: float = -1.0) -> float:
	if utc < 0: utc = now_utc()
	return fmod(utc, game_day_s()) / game_day_s()

## S37 · In-game time of day: four 12-minute phases.
func time_of_day(utc: float = -1.0) -> String:
	var t := day_fraction(utc)
	if t < 0.25: return "morning"
	if t < 0.5: return "day"
	if t < 0.75: return "evening"
	return "night"
