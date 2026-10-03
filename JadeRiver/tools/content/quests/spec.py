"""E5, the quest engine: the spec a side quest or a daily job is written in (docs/architecture/quest_engine.md).

A spec is a Python literal in tools/content/quests/specs/<module>.py (a module's `QUESTS` list, or a named list that
specs/__init__.py SECTIONS places). It says what the quest asks and who asks it; the engine (engine.py) derives where it
leads, when it opens and what it pays, and writes the quests.json row story.py places.

  side(id, *steps, giver, name=None, offer=(), done=(), progress=(), after=(), during=(), realm=AUTO, needs=(),
       gives=(), pay=AUTO, target_room=AUTO, hand_in=None, requires=AUTO, **keys)
    steps        what the quest asks, in order: the templates below, each an objective (escort is two)
    giver        an NPC engine id (or a one-off row of story.py); `hand_in` another one ("" hands in anywhere)
    name         the title, "The Muddy Wash"; by default the id's words (common.titled)
    offer, done  what the giver says on offering it and on handing it in (offer_text, complete_text); `progress`
                 what they say while it is under way
    after        the quests it follows (quest_done each); `during` quests it is offered while under way (quest_active)
    realm        the realm it opens at: AUTO is the realm of the middle Level of the target room's band, for a quest that
                 follows no other (one that follows another opens when the story gets there); a realm key pins it,
                 None leaves it out
    needs        the other conditions, after the realm (an unlock, a companion owned)
    requires     a whole `requires` pinned (the conditions above are then ignored)
    target_room  AUTO: the room the first step that names a place leads to (below); a room pins it, None leaves it out
    gives        what it gives besides its pay, in order: item(...), fx(...); PAY stands where the pay goes (first when
                 it is not named)
    pay          AUTO: the band table's currency and amount at the quest's tier (bands.py); a number pins the amount
                 (the band's currency), a reward dict (taels(n), stones(n), crystals(n)) pins both, None pays nothing
    keys         the row's other keys, after the derived ones: chapter, on_accept, offered_by_unlock, marker,
                 giver_any, hand_in_any, time_limit_s, fail_text, ...; the row takes requires, offered_by_unlock,
                 chapter and target_room first (ORDER), then the rest in the spec's order. `row={key: value}` pins
                 a key of the finished row (DROP takes one out)

  The templates (each makes one objective; `text` is the quest log's line, a default from the names when left out):
    clear(enemy, count=1, text=None)              defeat so many of a foe (kill). Leads to the room where most of them
                                                  spawn (a spawn gated by `requires` aside), then the lowest band
    fetch(item, count=1, text=None, consume=True) bring what foes drop or nodes yield (collect, handed over unless
                                                  consume=False). Leads to where its droppers spawn and its herbs,
                                                  ores, swarms and sighting stones are, the most of them
    deliver(item, count=1, text=None)             bring what is made or bought (deliver, always handed over). No room
    gather(item, count=1, text=None, craft=None)  gather at nodes (gather_node). Leads to the room with the most nodes
    talk(npc, text=None)                          talk to someone (talk_to). Leads to their room, unless they are the
                                                  giver or the one it is handed in to
    spar(opponent=None, text=None)                win a spar (win_spar). Leads to the room of their spar post or of
                                                  them, unless they are the giver
    escort(npc, to, text=None, meet=None)         meet someone and see them to a room (talk_to, reach_room). Leads to
                                                  `to`
    reach(room, text=None)                        reach a room (reach_room). Leads there
    step(kind, text, count=1, **fields)           any other objective, as story.py's o() writes it (set_flag,
                                                  use_system, hit_object, meditate_seconds, buy_item, ...). No room

  daily(id, name, *jobs, requires=None)   a template of the daily mission board (mission_templates.json)
  job(name, step, levels=AUTO)            one job it may post: a template step, posted while the character's Level
                                          is within `levels` (lo, hi); AUTO: from the band of the foe or node it
                                          names (engine.py job_levels)
"""
import copy


class SpecError(Exception):
    pass


class _Mark:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __deepcopy__(self, memo):
        return self


AUTO = _Mark("AUTO")   # derive this value
DROP = _Mark("DROP")   # take this key out of the finished row
PAY = _Mark("PAY")     # where the band's pay stands among a quest's rewards

# A row's derived keys, in the order story.py's hand rows had them; a spec's other keys follow in its own order.
ORDER = ("requires", "offered_by_unlock", "chapter", "target_room")


# ------------------------------------------------------------------------------------------------ the row's parts
def o(kind, text, count=1, **kw):
    """An objective. Items a quest asks for are either handed over when it is turned in (`consume`, and every deliver)
    or only counted (proof you gathered them, or a craft step's ingredients): each collect says which."""
    d = {"kind": kind, "text": text, "count": count}
    if kind == "deliver":
        d["consume"] = True
    assert kind != "collect" or isinstance(kw.get("consume"), bool), "collect objective %r must say consume=True/False" % text
    d.update(kw)
    return d


def item(i, n=1):
    return {"kind": "grant_item", "item": i, "count": n}


def fx(kind, **kw):
    d = {"kind": kind}
    d.update(kw)
    return d


def currency(cur, n):
    return {"kind": "grant_currency", "currency": cur, "amount": n}


def taels(n):
    return currency("silver_tael", n)


def stones(n):
    return currency("spirit_stone", n)


def crystals(n):
    return currency("sage_crystal", n)


# ------------------------------------------------------------------------------------------------ the templates
class Step(dict):
    """An objective a template made, with what the engine needs to find where it leads (`lead`: the kind of place and
    what to look for) and, for a daily job, the order the mission board writes its keys in (`board`)."""

    def __init__(self, obj, lead=None, board=None, verb=None):
        super().__init__(obj)
        self.lead = lead
        self.board = board
        self.verb = verb

    def __deepcopy__(self, memo):
        return Step(copy.deepcopy(dict(self), memo), self.lead, self.board, self.verb)


def clear(enemy, count=1, text=None, **kw):
    return Step(o("kill", text, count, enemy=enemy, **kw), ("spawn", enemy), ("kind", "enemy", "count", "text"), "Defeat")


def fetch(item_id, count=1, text=None, consume=True, **kw):
    return Step(o("collect", text, count, item=item_id, consume=consume, **kw), ("source", item_id),
                ("kind", "item", "count", "text", "consume"), "Bring")


def deliver(item_id, count=1, text=None, **kw):
    return Step(o("deliver", text, count, item=item_id, **kw), None, ("kind", "item", "count", "text", "consume"), "Deliver")


def gather(item_id, count=1, text=None, craft=None, **kw):
    if craft:
        kw = dict(item=item_id, craft=craft, **kw)
    else:
        kw = dict(item=item_id, **kw)
    return Step(o("gather_node", text, count, **kw), ("node", item_id), ("kind", "item", "count", "text"), "Gather")


def talk(npc, text=None, **kw):
    return Step(o("talk_to", text, npc=npc, **kw), ("npc", npc), None, "Talk to")


def spar(opponent=None, text=None, **kw):
    if opponent:
        kw = dict(opponent=opponent, **kw)
    return Step(o("win_spar", text, **kw), ("spar", opponent) if opponent else None, ("kind", "count", "text"), "Win a spar")


def reach(room, text=None, **kw):
    return Step(o("reach_room", text, room=room, **kw), ("room", room), None, "Reach")


def escort(npc, to, text=None, meet=None):
    return [Step(o("talk_to", meet, npc=npc), None, None, "Meet"),
            Step(o("reach_room", text, room=to), ("room", to), None, "See")]


def step(kind, text, count=1, **kw):
    return Step(o(kind, text, count, **kw), None, ("kind",) + tuple(kw) + ("count", "text"))


TEMPLATES = {"clear": clear, "fetch": fetch, "deliver": deliver, "gather": gather, "talk": talk, "spar": spar,
             "escort": escort, "reach": reach, "step": step}


# ------------------------------------------------------------------------------------------------ a quest, a job
def side(qid, *steps, giver, name=None, offer=(), done=(), progress=(), after=(), during=(), realm=AUTO, needs=(),
         gives=(), pay=AUTO, target_room=AUTO, hand_in=None, requires=AUTO, kind="side", row=None, **keys):
    flat = []
    for s in steps:
        flat += list(s) if isinstance(s, list) else [s]
    for s in flat:
        if not isinstance(s, Step):
            raise SpecError("%s: a step is a template's (clear, fetch, ...), not %r" % (qid, s))
    if isinstance(after, str):
        after = (after,)
    if isinstance(during, str):
        during = (during,)
    if isinstance(offer, str):
        offer = (offer,)
    if isinstance(done, str):
        done = (done,)
    if isinstance(progress, str):
        progress = (progress,)
    return {"id": qid, "name": name, "kind": kind, "giver": giver, "hand_in": hand_in, "steps": flat,
            "offer": list(offer), "done": list(done), "progress": list(progress), "after": list(after),
            "during": list(during), "realm": realm, "needs": list(needs), "requires": requires, "gives": list(gives),
            "pay": pay, "target_room": target_room, "keys": dict(keys), "row": dict(row or {})}


def daily(did, name, *jobs, requires=None):
    return {"id": did, "name": name, "jobs": list(jobs), "requires": requires}


def job(name, s, levels=AUTO):
    if not isinstance(s, Step) or not s.board:
        raise SpecError("job %r: its step is a template's that the mission board writes" % name)
    return {"name": name, "step": s, "levels": levels}
