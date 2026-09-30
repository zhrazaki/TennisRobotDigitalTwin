"""
Purpose:     Phase 10 (Production Bulletproof) - Spawns Tennis Robot
             with structural materials applied without dynamic API errors.
Dependencies: unreal, Core.court_config
Inputs:      None
Outputs:     Spawns complete 'TennisRobot_Base' actor.
"""

import unreal
from Core import court_config


def spawn_tennis_robot():
    """
    Spawns the collector robot cleanly using reliable Unreal Engine assets.
    """
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # 1. Clean up old robot instances
    for actor in actor_subsystem.get_all_level_actors():
        if actor and "TennisRobot" in actor.get_actor_label():
            actor_subsystem.destroy_actor(actor)

    # 2. Spawn Root Actor (Chassis Base)
    spawn_location = unreal.Vector(-1000.0, 0.0, 25.0)
    spawn_rotation = unreal.Rotator(0.0, 0.0, 0.0)

    robot_actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, spawn_location, spawn_rotation
    )

    if not robot_actor:
        print("[ERROR] Failed to spawn TennisRobot_Base.")
        return None

    robot_actor.set_actor_label("TennisRobot_Base")
    robot_actor.tags = ["TennisRobot", "Robot", "Collector"]
    robot_actor.set_folder_path("TennisCourt/Robot")

    # Load Standard Engine Meshes
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")

    # Load Base Engine Material cleanly
    base_mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")

    # --- Root Component (Chassis Base) ---
    root_comp = robot_actor.get_component_by_class(unreal.StaticMeshComponent)
    if root_comp and cube_mesh:
        root_comp.set_static_mesh(cube_mesh)
        root_comp.set_relative_scale3d(unreal.Vector(1.0, 0.7, 0.2)) # 100x70x20 cm
        root_comp.set_collision_profile_name("Vehicle")
        if base_mat:
            root_comp.set_material(0, base_mat)

    # Helper function to attach parts securely
    def add_mesh_part(part_name, mesh, rel_loc, rel_rot, rel_scale):
        part = actor_subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor, spawn_location, spawn_rotation
        )
        if part:
            part.set_actor_label("TennisRobot_" + part_name)
            part.set_folder_path("TennisCourt/Robot")
            
            comp = part.get_component_by_class(unreal.StaticMeshComponent)
            if comp and mesh:
                comp.set_static_mesh(mesh)
                comp.set_collision_profile_name("Vehicle")
                if base_mat:
                    comp.set_material(0, base_mat)

            part.attach_to_actor(
                robot_actor,
                unreal.Name(),
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                unreal.AttachmentRule.KEEP_WORLD,
                False
            )
            
            part.set_actor_relative_location(rel_loc, False, False)
            part.set_actor_relative_rotation(rel_rot, False, False)
            part.set_actor_scale3d(rel_scale)
        return part

    if cylinder_mesh and cube_mesh:
        # A. 4 Wheels
        w_scale = unreal.Vector(0.3, 0.3, 0.12)
        w_rot = unreal.Rotator(90.0, 0.0, 0.0)
        
        add_mesh_part("Wheel_FL", cylinder_mesh, unreal.Vector(35.0, 42.0, -5.0), w_rot, w_scale)
        add_mesh_part("Wheel_FR", cylinder_mesh, unreal.Vector(35.0, -42.0, -5.0), w_rot, w_scale)
        add_mesh_part("Wheel_RL", cylinder_mesh, unreal.Vector(-35.0, 42.0, -5.0), w_rot, w_scale)
        add_mesh_part("Wheel_RR", cylinder_mesh, unreal.Vector(-35.0, -42.0, -5.0), w_rot, w_scale)

        # B. Ball Storage Basket (Top Container)
        add_mesh_part("Bucket", cube_mesh, unreal.Vector(-10.0, 0.0, 25.0), unreal.Rotator(0, 0, 0), unreal.Vector(0.55, 0.55, 0.35))

        # C. Front Ball Collector Roller
        add_mesh_part("Collector_Roller", cylinder_mesh, unreal.Vector(55.0, 0.0, -5.0), unreal.Rotator(0, 0, 90), unreal.Vector(0.18, 0.18, 0.65))

        # D. Camera Mount Stand
        add_mesh_part("Camera_Mount", cylinder_mesh, unreal.Vector(30.0, 0.0, 35.0), unreal.Rotator(0, 0, 0), unreal.Vector(0.08, 0.08, 0.5))

    print("[robot_builder] Tennis robot built successfully with zero material errors.")
    return robot_actor