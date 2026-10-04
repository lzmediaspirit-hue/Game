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

# M4. The Ninth Presence (the Trial Hall's ninth seat): your own Presence grown old, a towering spectral sage pale violet
# with the hall's light, in a scholar's long white robe with wide sleeves and a pale cape, a jade guan on its long white
# hair, a long white beard, its eyes glowing; floating, its hem thinning into mist; a staff of white jade crowned with nine
# lights in its right hand and the crown of nine lights behind its head. Its tell is the crown gathered up over its head
# into a blaze (held: its crown of nine's too), and its palm strikes as the nine lights are thrown out round it.
species("ninth_presence", plan="humanoid.presence", share=True, size=2.7, elite=False, shadow=(11, 4), cycle=11.0, view=True,
        canvas=(170, 170),
        palette=["pres_skin", "pres_robe", "pres_hair", "pres_gold", "pres_sash", "pres_cape", "pres_jade", "pres_cap", "maw"],
        data=dict(level=81, role="normal", element="none", page=None, drops=[],
                  attacks=[("ninth_seat_palm", 0.7, 120, 1.3, dict(damage_type="qi", depth=50, knockback=100)),
                           ("crown_of_nine", 1.1, 240, 1.2, dict(damage_type="soul", depth=90, both_sides=True,
                                                                 status={"id": "slow", "chance": 0.6, "power": 0.3, "duration_s": 3}))],
                  ai="duelist",
                  art=person("The Ninth Presence", hair="flowing", hair_color=1, shirt="scholar", pants="scholar", shoes="folded", weapon="staff",
                             hat="guan", shirt_dye="white", pants_dye="white", cape="solid", tint="#d9ccff"),
                  race="human", energy="sage_qi", width=20, height=96, name="The Ninth Presence",
                  hp_mult=12.0, attack_mult=1.2))
