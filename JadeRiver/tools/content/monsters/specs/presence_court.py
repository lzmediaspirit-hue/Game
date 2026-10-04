"""The Presence Trial's foes (M4; the Trial Hall of the Nine Peaks, level 81): the Presences of the eight seats and the
Ninth Presence.

The phantoms are drawn as the player and the villagers are (plans/person.py), in the scholars' white the Trial Hall's
tint turns violet, their lower bodies thinning into mist (`phantom`). The Ninth Presence is a person of size, sculpted
(humanoid.presence)."""
from content.monsters import person, species

# M4. The Presence of a seat of the Trial Hall: an old scholar's phantom in white robes, a guan over its topknot, violet
# with the hall's light, its lower body thinning into mist. It fights bare-handed: its tell is the palm drawn back in a
# crouch, and the weight of its seat strikes.
species("presence_phantom", plan="person.fighter", share=True, size=1.0, elite=False, shadow=(8, 3), cycle=12.0,
        parts=dict(phantom=True),
        data=dict(level=81, role="normal", element="none", page=None, drops=[], attacks=[("weight_of_a_seat", 0.55, 90, 1.1, dict(damage_type="qi"))],
                  ai="duelist",
                  art=person("Presence of a Seat", hair="topknot", hair_color=0, shirt="scholar", pants="scholar", shoes="folded", weapon="none",
                             hat="guan", shirt_dye="white", pants_dye="white", tint="#b4a6ee"),
                  race="human", energy="sage_qi", width=18, height=90, name="Presence of a Seat"))
