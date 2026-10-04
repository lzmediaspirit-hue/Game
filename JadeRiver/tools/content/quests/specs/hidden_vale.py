"""The Hidden Vale's letters: founding your own sect (S20). Courier Lin's letters are handed in anywhere. Placed by
story.py's side_quests() (section act1), after the companions' favours."""
from content.quests.spec import side, step

QUESTS = [
    side("a_hall_of_our_own", step("use_system", "Found your sect", system="found_sect"), giver="courier_lin", hand_in="",
         offered_by_unlock=True, offer="(A letter) The Hidden Vale beyond Crane Falls could hold a sect. Yours."),
    side("first_recruits", step("use_system", "Recruit NPC disciples", 2, system="recruit"), giver="courier_lin", hand_in="",
         after="a_hall_of_our_own", offer="A sect needs people."),
    side("walls_of_the_vale", step("use_system", "Win a defence event", system="defence_won"), giver="courier_lin", hand_in="",
         after="first_recruits", offer="Defend the Vale."),
]
