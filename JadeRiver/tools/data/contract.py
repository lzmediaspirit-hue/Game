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
        "hidden_portal_revealed", "teleport_discovered", "zone_entered", "zone_ceiling_reached"],
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
        "pill_used"],
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
        "achievement_progressed", "achievement_unlocked", "title_changed"],
    "Notifier": [
        "notification_scheduled"],
    "Sect": [
        "sect_founded", "prestige_gained", "sect_level_changed", "building_upgraded", "expedition_returned",
        "defence_warning", "defence_result", "building_damaged"],
}

# The scripts that make up each system (an authority plus its rule and brain helpers).
SYSTEMS = {
    "Progression": ["progression_authority"], "Combat": ["combat_authority"], "World": ["world_authority"],
    "Sect": ["sect_authority"], "Pets": ["pet_authority"], "Inventory": ["inventory_authority"],
    "Quest": ["quest_authority"], "Account": ["account_authority"], "Enemies": ["enemy_authority", "enemy_brain"],
    "Crafting": ["crafting_authority", "workshop_authority"], "TrainingSect": ["training_sect_authority"],
    "Achievement": ["achievement_authority"], "Economy": ["economy_authority"], "Unlocks": ["unlock_service"],
    "Mail": ["mail_authority"], "Companion": ["companion_authority"], "Notifier": ["notifier"],
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
