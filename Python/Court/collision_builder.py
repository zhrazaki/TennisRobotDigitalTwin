"""
Purpose:     Phase 8 - Configures collision profiles and physics properties
             for court actors (surface, lines, net, fence, environment)
             to prepare for robot navigation (ROS 2) and tennis ball simulation.
Dependencies: unreal, Core.court_config
Inputs:      None (Queries existing actors in the level)
Outputs:     Returns total count of modified collision actors.
"""

import unreal
from Core import court_config


def apply_court_collisions() -> int:
    """
    Scans the Unreal level for tennis court actors and enforces proper
    collision responses (BlockAll) for physics interactions.
    """
    cfg = court_config.get_court_config()
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    updated_count = 0

    for actor in all_actors:
        if not actor:
            continue

        actor_label = actor.get_actor_label()

        # Check if actor belongs to the TennisCourt or Environment groups
        tags = [str(t) for t in actor.tags]
        is_court_actor = any("Tennis" in t or "Court" in t for t in tags) or "TennisCourt_" in actor_label

        if is_court_actor:
            mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if mesh_comp:
                # Enable query & physics collisions
                mesh_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                # Setting collision profile to 'BlockAll' handles blocking all channels safely
                mesh_comp.set_collision_profile_name("BlockAll")
                
                # Turn off physics simulation (static meshes)
                mesh_comp.set_simulate_physics(False)

                updated_count += 1

    print("[collision_builder] Successfully applied BlockAll collision profile to {} actors.".format(updated_count))
    return updated_count