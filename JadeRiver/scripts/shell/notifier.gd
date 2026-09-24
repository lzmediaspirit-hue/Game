extends Node
## `Notifier` autoload (S37): local notifications, at most 3 per day, never between
## 22:00 and 08:00, each type switchable in Settings. On desktop they are logged;
## an Android plugin can replace `_deliver` without touching game rules.
var sent_today := 0
var day := -1

func schedule(type: String, title: String, body: String, at_utc: float) -> bool:
	var settings: Dictionary = Game.account.settings.get("notifications", {})
	if not settings.get(type, true): return false
	var d := Clock.reset_day(Clock.now_utc())
	if d != day:
		day = d
		sent_today = 0
	if sent_today >= 3: return false
	var hour := int(Clock.local_dict(at_utc).get("hour", 12))
	if hour >= 22 or hour < 8: return false
	sent_today += 1
	GameEvents.emit_event("notification_scheduled", {"type": type, "time": at_utc, "title": title})
	_deliver(title, body, at_utc)
	return true

func _deliver(title: String, _body: String, _at: float) -> void:
	print_verbose("NOTIFY: ", title)
