"""Part 7 event contract: every event in the Part 4 catalogue, the system that emits it
and the scripts that make up that system. tests/contract_tests checks the code against it:
each event is emitted only by its system, and something consumes it.
"""
from common import write

# Part 4 · Event catalogue, by emitting system.
CATALOGUE = {
    "Progression": [
        "progress_changed", "bottleneck_reached", "breakthrough_started", "breakthrough_succeeded",
        "breakthrough_failed", "realm_changed", "consolidation_finished", "stability_changed", "injury_added",
        "injury_healed", "meditation_started", "meditation_stopped", "meditation_tick", "qi_backlash",
        "offline_claimed", "insight_gained", "dao_tier_up", "method_changed", "technique_equipped",
        "technique_mastery_up", "attributes_changed", "meridian_gate_opened", "toxicity_changed",
        "aptitude_revealed", "body_level_changed", "purity_changed", "soul_changed", "attunement_changed"],
    "Combat": [
        "attack_started", "hit_landed", "status_applied", "status_expired", "actor_defeated",
        "player_gravely_wounded", "hit_missed", "technique_used", "resource_changed", "stats_changed",
        "player_revived"],
    "World": [
        "loot_dropped", "room_left", "room_entered", "object_interacted", "node_depleted", "node_regrown",
        "hidden_portal_revealed", "teleport_discovered", "zone_entered", "zone_ceiling_reached", "hazard_warned",
        "hazard_struck"],
    "Enemies": [
        "enemy_aggro", "enemy_spawned", "elite_spawned", "field_boss_spawned", "field_boss_defeated"],
    "Crafting": [
        "craft_step_result", "craft_started", "craft_completed", "profession_rank_up", "fish_caught"],
    "Economy": [
        "currency_changed", "shop_restocked", "auction_bid_placed", "auction_outbid", "auction_won"],
    "Pets": [
        "egg_hatched", "pet_retreated", "pet_bonded", "pet_level_up", "bond_changed", "pet_evolved",
        "trait_revealed"],
    "Inventory": [
        "item_added", "item_removed", "bag_full", "overflow_mailed", "equipment_changed", "item_used",
        "pill_used", "draught_expired"],
    "Quest": [
        "quest_offered", "quest_accepted", "objective_progressed", "quest_ready", "quest_completed",
        "flag_set", "codex_entry_unlocked"],
    "Unlocks": [
        "unlock_offered", "system_unlocked", "hud_element_revealed"],
    "Account": [
        "collection_page_completed", "daily_reset", "weekly_reset", "app_paused", "app_resumed",
        "account_highest_realm_changed", "slot_unlocked", "character_switched", "idle_collected",
        "legacy_recorded", "character_created"],
    "Mail": [
        "mail_received", "mail_claimed"],
    "TrainingSect": [
        "sect_joined", "sect_rank_changed", "contribution_changed", "reputation_changed"],
    "Companion": [
        "companion_downed", "companion_revived"],
    "Achievement": [
        "achievement_progressed", "achievement_unlocked", "title_changed", "path_above_found"],
    "Notifier": [
        "notification_scheduled"],
    "Sect": [
        "sect_founded", "prestige_gained", "sect_level_changed", "building_upgraded", "expedition_returned",
        "defence_warning", "defence_result", "building_damaged"],
}
# Build Prompt v2 · Traversal, depth and living-world events (S43-S49), as far as those systems are built.
# The karma rows move to Relations when that authority exists (S49); until then Progression keeps the ledger.
DEPTH = {
    "Progression": ["pill_resistance_changed", "foundation_changed", "heart_demon_changed", "residue_changed", "merit_changed", "sin_changed",
                    "debt_recorded", "debt_called", "body_trial_passed", "body_tier_reached", "physique_awakened", "core_graded",
                    "fate_offered", "fate_chosen", "tribulation_started", "tribulation_bolt", "tribulation_result", "qi_deviation",
                    "inner_art_learned", "inner_art_equipped", "stance_changed", "vow_taken", "vow_broken", "false_realm_changed",
                    "epiphany", "soul_escaped"],
    "Crafting": ["flame_absorbed", "pill_cloud", "items_salvaged", "enhancement_inherited", "affixes_rerolled", "affix_locked", "talisman_crafted",
                 "relic_restored", "furnace_blast", "recipe_page_found", "recipe_deduced", "experiment_result", "guild_exam_started",
                 "guild_exam_failed", "guild_rank_changed", "commission_completed", "pill_tribulation_result", "pill_soul_flight",
                 "herb_harvested", "seed_found", "herb_planted", "bed_watered", "bed_enriched", "herb_aged", "spring_bottled", "transplant_result",
                 "rack_started", "rack_collected", "garden_raided", "herb_appraised"],
    "Combat": ["treasure_used", "sword_released", "sword_returned", "sword_intent_changed", "artifact_detonated", "talisman_used", "combo_landed", "killing_intent_changed"],
    "Inventory": ["loadout_swapped", "natal_grew", "natal_broken", "item_blooded"],
    "Movement": ["jumped", "landed", "wall_kicked", "art_used", "climb_started", "climb_finished", "fell_out", "mover_boarded",
                 "volume_entered", "volume_left"],
    "Enemies": ["enemy_leashed"],
    "World": ["ambush_sprung", "herb_ripening", "guardian_spawned"],
}
for _sys, _names in DEPTH.items():
    CATALOGUE[_sys] = CATALOGUE.get(_sys, []) + _names

# The scripts that make up each system (an authority plus its rule and brain helpers).
SYSTEMS = {
    "Progression": ["progression_authority"], "Combat": ["combat_authority"], "World": ["world_authority"],
    "Sect": ["sect_authority"], "Pets": ["pet_authority"], "Inventory": ["inventory_authority"],
    "Quest": ["quest_authority"], "Account": ["account_authority"], "Enemies": ["enemy_authority", "enemy_brain"],
    "Crafting": ["crafting_authority", "workshop_authority"], "TrainingSect": ["training_sect_authority"],
    "Achievement": ["achievement_authority"], "Economy": ["economy_authority"], "Unlocks": ["unlock_service"],
    "Mail": ["mail_authority"], "Companion": ["companion_authority"], "Notifier": ["notifier"],
    "Movement": ["local_authority", "movement_solver"],
}

# A second system that may also announce the event, and why.
ALSO = {
    "attack_started": ("Enemies", "Enemy wind-ups are started by the Enemies system that runs the brain; Combat announces the player's."),
}

# Reactors that read state every frame instead of listening, so no subscriber is required.
POLLED = {
    "progress_changed": "HUD bars read the cultivator each frame.",
    "stats_changed": "HUD and pages read the StatBlock each frame.",
    "status_applied": "HUD status icons read active statuses each frame.",
    "status_expired": "HUD status icons read active statuses each frame.",
    "technique_equipped": "The HUD skill arc reads the technique slots each frame.",
    "toxicity_changed": "The HUD icon and Cultivation page read toxicity.",
    "meditation_stopped": "Allies and the lotus ring read the meditating flag.",
    "node_depleted": "Room objects are drawn from their state.",
    "node_regrown": "Room objects are drawn from their state.",
    "insight_gained": "The Dao page reads insight; one per technique use is too frequent for a notice.",
    "achievement_progressed": "The Achievements page reads the counters.",
    "quest_offered": "NPC markers read the offer list.",
    "idle_collected": "The shell opens the welcome page from the collect result.",
    "offline_claimed": "The shell opens the welcome page from the enter result.",
    "mail_claimed": "Open pages redraw on every event.",
    "shop_restocked": "Open pages redraw on every event.",
    "craft_started": "The crafts page drives its own mini-game.",
    "notification_scheduled": "Handed to the platform notifier on phones; nothing to show on desktop.",
    "weekly_reset": "No weekly content in Act I.",
    "residue_changed": "The Cultivation page's Heart tab reads residue.",
    "pill_resistance_changed": "Pill tooltips and the Heart tab read each family's count.",
    "foundation_changed": "The Heart tab and the risk preview read the foundation share.",
    "jumped": "The player node plays its own jump pose and sound when the press succeeds.",
    "climb_started": "The player node reads its climbing state for the climb pose.",
    "climb_finished": "The player node reads its climbing state for the climb pose.",
    "debt_recorded": "The Cultivation page's Heart tab lists debts; the callback is debt_called.",
    "mover_boarded": "The player node reads rider_of; movers carry their riders in the solver.",
    "volume_left": "The player node reads the water state and volumes each frame.",
    "enemy_leashed": "Enemy views read the return state; the out-of-reach rule is the brain's own business.",
}


def build():
    events = {}
    for system, names in CATALOGUE.items():
        for n in names:
            files = list(SYSTEMS[system])
            row = {"system": system, "files": files}
            if n in ALSO:
                row["files"] = files + SYSTEMS[ALSO[n][0]]
                row["also"] = ALSO[n][0]
                row["note"] = ALSO[n][1]
            if n in POLLED:
                row["polled"] = POLLED[n]
            events[n] = row
    write("event_contract.json", {"schema_version": 1, "events": events})
