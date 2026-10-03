"""Stoneford's foes: the Sect Fair's trial halls (the Trial Puppet, the entry trial's opponent)."""
from content.monsters import species

species("trial_puppet", plan="humanoid.puppet", size=1.58,
        palette=["timber", "timber_dark", "brass", "puppet_jade", "rope"], accents=("puppet_jade", "brass"), elite=False, shadow=(11, 4),
        cycle=12.0,
        data=dict(level=2, role="trial", element="none", page=None, drops=[("entry_token", 1.0)], attacks=[("counter_palm", 0.5, 44, 1.0)],
                  ai="guard_counter", speed=60, width=22, height=60, knockback_immune=True, no_death_penalty=True),
        sound=dict(body="wood"))
