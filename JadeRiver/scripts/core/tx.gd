class_name Tx
extends RefCounted
## Player-facing text (Part 7 · Strings): every line the player reads comes from
## data/strings/en.json by key. The UI strings are authored in tools/data/ui_strings.json.

static func t(key: String) -> String:
	return ContentDB.text(key)

## A counted line: the "_one" form of `key` when `count` is 1 and the strings have one, else `key` itself; the caller
## formats it (I12: "Raise · 1 shards", "5 shard").
static func plural(key: String, count: int) -> String:
	return t(key + "_one") if count == 1 and ContentDB.strings.has(key + "_one") else t(key)

## A time left, a wait, a cooldown or a duration in words, in the one style (I14, docs/ui_style_guide.md §4): "2 d 5 h"
## (unless `days` is false), "1 h 6 m", "3 h", "12 m", "45 s". Minutes round up, so a wait never reads shorter than it
## is. The simulation's messages and the pages (UiKit.span) both write durations through it.
static func span(seconds: float, days := true) -> String:
	var s := maxi(0, int(ceil(seconds)))
	if days and s >= 86400: return t("ui.span_dh") % [s / 86400, (s % 86400) / 3600] if (s % 86400) / 3600 > 0 else t("ui.span_d") % (s / 86400)
	if s >= 3600: return t("ui.span_hm") % [s / 3600, (s % 3600) / 60] if (s % 3600) / 60 > 0 else t("ui.span_h") % (s / 3600)
	if s >= 60: return t("ui.span_m") % ceili(s / 60.0)
	return t("ui.span_s") % s
