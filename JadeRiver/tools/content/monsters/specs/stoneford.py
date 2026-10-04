"""Stoneford's foes: the Sect Fair's trial halls (the Trial Puppet, the entry trial's opponent), and Elder Gu, the trade
house's master (M2), fought in his warehouse."""
from content.monsters import person, species

species("trial_puppet", plan="humanoid.puppet", size=1.58,
        palette=["timber", "timber_dark", "brass", "puppet_jade", "rope"], accents=("puppet_jade", "brass"), elite=False, shadow=(11, 4),
        cycle=12.0,
        data=dict(level=2, role="trial", element="none", page=None, drops=[("entry_token", 1.0)], attacks=[("counter_palm", 0.5, 44, 1.0)],
                  ai="guard_counter", speed=60, width=22, height=60, knockback_immune=True, no_death_penalty=True),
        sound=dict(body="wood"))

# M2. Elder Gu, the trade house's master, cornered in his warehouse (a story boss who cannot be beaten there; he flees):
# sculpted, a boss of his own build, not the shared figure body. Portly and stately in a voluminous crimson robe trimmed
# in gold with wide sleeves, his hands folded in them, a black sash, his dark teal cape over his shoulders, grey hair tied
# back in a tail, a drooping grey moustache and goatee, a gold abacus at his belt. His tell is the river's tide gathering
# into an orb in his right palm as he draws it back (held); his blow throws it as a palm strike that bursts in a wave.
species("elder_gu", plan="humanoid.elder", share=True, size=2.4, elite=False, shadow=(12, 4), cycle=11.0, view=True,
        palette=["folk_skin", "gu_hair", "gu_robe", "gu_gold", "gu_sash", "gu_cape", "gu_shoe", "rs_orb", "maw"],
        data=dict(level=53, role="story_boss", element="water", page=None, drops=[("smuggler_ledger", 1.0)],
                  attacks=[("tide_palm", 0.5, 90, 1.2, dict(damage_type="qi"))], ai="humanoid",
                  art=person("Elder Gu", hair="long_tied", hair_color=1, shirt="scholar", pants="scholar", shoes="folded", weapon="none",
                             hat="none"),
                  race="human", energy="true_qi", width=18, height=90, flees_after_s=60, invulnerable=True,
                  # P1: Gu cannot be beaten here, so his phases run on the clock: hired blades at 20 s, a cornered rat at 40 s.
                  phases=[{"after_s": 20, "action": "summon", "summon": "gorge_bandit_adept", "summon_level": 50},
                          {"after_s": 40, "action": "enrage", "cooldown": 0.7, "damage": 1.25}]))
