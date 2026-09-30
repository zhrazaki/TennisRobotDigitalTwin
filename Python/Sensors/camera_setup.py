"""
Purpose:     Phase 11 - Spawns and attaches CineCamera to robot camera mount.
Dependencies: unreal
Inputs:      None
Outputs:     Attached CineCameraActor.
"""

import unreal


def attach_camera_to_robot():
    """Attaches a CineCameraActor to the TennisRobot_Base actor."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Clean existing cameras
    for actor in actor_subsystem.get_all_level_actors():
        if actor and "RobotCamera" in actor.get_actor_label():
            actor_subsystem.destroy_actor(actor)

    # Find Robot Base
    robot_base = None
    for actor in actor_subsystem.get_all_level_actors():
        if actor and actor.get_actor_label() == "TennisRobot_Base":
            robot_base = actor
            break

    if not robot_base:
        print("[ERROR] TennisRobot_Base missing! Cannot attach camera.")
        return None

    # Spawn Cine Camera
    spawn_loc = robot_base.get_actor_location()
    cam_actor = actor_subsystem.spawn_actor_from_class(
        unreal.CineCameraActor, spawn_loc, unreal.Rotator(0, 0, 0)
    )

    if cam_actor:
        cam_actor.set_actor_label("RobotCamera_RGB")
        cam_actor.tags = ["RobotCamera", "RGB_Sensor"]
        cam_actor.set_folder_path("TennisCourt/Robot")

        # Attach to robot base
        cam_actor.attach_to_actor(
            robot_base,
            unreal.Name(),
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            False
        )

        # Relative location (X: 30cm forward, Z: 60cm high on mount)
        cam_actor.set_actor_relative_location(unreal.Vector(30.0, 0.0, 60.0), False, False)
        cam_actor.set_actor_relative_rotation(unreal.Rotator(-5.0, 0.0, 0.0), False, False) # 5 deg pitch down

        cam_comp = cam_actor.get_cine_camera_component()
        if cam_comp:
            cam_comp.focus_settings.focus_method = unreal.CameraFocusMethod.DISABLE

        print("[camera_setup] Robot Camera attached successfully.")
        return cam_actor

    return None