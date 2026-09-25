class_name MailAuthority
extends Authority
## S41 · One account-wide inbox: letters, rewards, overflow and warnings. Letters
## sent before Mail unlocks are queued and appear then. Claiming with a full bag
## keeps the items attached; unclaimed attachments are never deleted silently.

const CAP := 100

func intents() -> Array:
	return ["read_mail", "claim_mail", "claim_all", "delete_mail"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"read_mail":
			var m := _find(int(intent.get("id", -1)))
			if m.is_empty(): return fail("unknown")
			m.read = true
			emit("mail_read", {"actor": c.id, "id": m.id})
			return ok()
		"claim_mail": return claim(c, int(intent.get("id", -1)))
		"claim_all":
			var n := 0
			for m in visible(c):
				if not m.get("claimed", false) and not m.get("attachments", []).is_empty():
					if claim(c, int(m.id)).ok: n += 1
			return ok({"claimed": n})
		"delete_mail":
			var m2 := _find(int(intent.get("id", -1)))
			if m2.is_empty(): return fail("unknown")
			if not m2.get("claimed", false) and not m2.get("attachments", []).is_empty(): return fail("unclaimed")
			game.account.mail.erase(m2)
			return ok()
	return fail("unknown_intent")

func _find(id: int) -> Dictionary:
	for m in game.account.mail:
		if int(m.id) == id: return m
	return {}

func visible(c) -> Array:
	if c == null or not Unlocks.is_unlocked(c.id, "mail"): return []
	return game.account.mail.filter(func(m): return str(m.to) in [c.id, "all"])

func unread(c) -> int:
	var n := 0
	for m in visible(c):
		if not m.get("read", false): n += 1
	return n

func apply_send(to: String, template: String, attachments: Array, args: Dictionary) -> void:
	var tpl := ContentDB.entry("mail_templates", template)
	var subject := str(tpl.get("subject", template.capitalize()))
	var body := str(tpl.get("body", ""))
	for k in args:
		subject = subject.replace("{" + k + "}", str(args[k]))
		body = body.replace("{" + k + "}", str(args[k]))
	_add({"to": to, "from": str(tpl.get("from", "The Valley")), "subject": subject, "body": body, "attachments": attachments.duplicate(true),
		"expires_utc": 0.0})

func apply_overflow(actor_id: String, items: Array) -> void:
	_add({"to": actor_id, "from": "Spirit Gourd", "subject": "Overflow", "body": "Your gourd was full. These items waited for you.",
		"attachments": items.duplicate(true), "expires_utc": Clock.now_utc() + 3 * 86400.0, "overflow": true})

func _add(letter: Dictionary) -> void:
	var acc: AccountState = game.account
	letter.id = acc.mail_next_id
	acc.mail_next_id += 1
	letter.received_utc = Clock.now_utc()
	letter.read = false
	letter.claimed = letter.get("attachments", []).is_empty()
	acc.mail.push_front(letter)
	# Cap: the oldest claimed letters go first; unclaimed attachments are never dropped.
	while acc.mail.size() > CAP:
		var removed := false
		for i in range(acc.mail.size() - 1, -1, -1):
			if acc.mail[i].get("claimed", false):
				acc.mail.remove_at(i)
				removed = true
				break
		if not removed: break
	emit("mail_received", {"letter": letter.id, "to": letter.to})

func claim(c, id: int) -> Dictionary:
	var m := _find(id)
	if m.is_empty() or m.get("claimed", false): return fail("nothing")
	var left: Array = []
	for a in m.get("attachments", []):
		var added := 0
		if a.has("instance") and not (a.instance as Dictionary).is_empty():
			added = game.inventory.apply_add_instance(c.id, a.instance, "mail", false)
		elif a.has("currency"):
			game.economy.apply_currency(str(a.currency), int(a.amount), "mail")
			added = 1
		else:
			added = game.inventory.apply_add(c.id, str(a.item), int(a.get("count", 1)), "mail", {}, false)
		if added < int(a.get("count", 1)) and not a.has("currency") and not a.has("instance"):
			var rest: Dictionary = a.duplicate()
			rest.count = int(a.get("count", 1)) - added
			left.append(rest)
		elif added == 0:
			left.append(a)
	m.attachments = left
	m.claimed = left.is_empty()
	m.read = true
	emit("mail_claimed", {"letter": id, "actor": c.id})
	return ok({"complete": left.is_empty()})

func tick(_delta: float) -> void:
	var acc: AccountState = game.account
	if game.tick_count % 300 != 0: return
	var now := Clock.now_utc()
	for m in acc.mail.duplicate():
		if float(m.get("expires_utc", 0.0)) > 0.0 and now > float(m.expires_utc): acc.mail.erase(m)
