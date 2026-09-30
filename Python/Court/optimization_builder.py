"""
Purpose:     Phase 9 - Final optimization and polish module.
             Enforces Static mobility for baked performance, organizes
             actor hierarchies in the Outliner, and optimizes shadow properties.
Dependencies: unreal, Core.court_config
Inputs:      None
Outputs:     Returns optimization status dictionary with metrics.
"""

import unreal
from Core import court_config


def optimize_court_scene() -> dict:
    """
    Applies static mesh optimizations, organizes actor folders in the Outliner,
    and returns a summary of optimized elements.
    """
    cfg = court_config.get_court_config()
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    stats = {
        "static_mobility_applied": 0,
        "outliner_organized": 0,
        "cast_shadows_enabled": 0
    }

    for actor in all_actors:
        if not actor:
            continue

        actor_label = actor.get_actor_label()
        tags = [str(t) for t in actor.tags]
        is_court_actor = any("Tennis" in t or "Court" in t for t in tags) or "TennisCourt_" in actor_label

        if is_court_actor:
            # 1. Set Mobility to Static for light baking & efficiency
            root_comp = actor.get_editor_property("root_component")
            if root_comp:
                root_comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
                stats["static_mobility_applied"] += 1

            # 2. Assign proper Outliner folder structure
            if "Surface" in actor_label:
                actor.set_folder_path("TennisCourt/Court")
            elif "Line" in actor_label or "TennisCourt_Line_" in actor_label:
                actor.set_folder_path("TennisCourt/Lines")
            elif "Net" in actor_label or "Post" in actor_label:
                actor.set_folder_path("TennisCourt/Net")
            elif "Fence" in actor_label or "Light" in actor_label or "Env" in actor_label:
                actor.set_folder_path("TennisCourt/Environment")
            stats["outliner_organized"] += 1

            # 3. Enable shadow casting on StaticMeshComponents
            mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if mesh_comp:
                mesh_comp.set_editor_property("cast_shadow", True)
                stats["cast_shadows_enabled"] += 1

    print("[optimization_builder] Optimized {} actors (Static Mobility & Folder Hierarchy).".format(stats["outliner_organized"]))
    return stats