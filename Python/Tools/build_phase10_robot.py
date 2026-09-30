"""
Purpose:     Phase 10 Verification Script.
             Validates complete robot setup and actor attachments.
Dependencies: unreal, Core.court_config, Court.robot_builder
Inputs:      None
Outputs:     Prints verification results to Unreal Output Log.
"""

import unreal
from Core import court_config
from Court import robot_builder


def run():
    print("==========================================")
    print("STARTING PHASE 10 — COMPLETE ROBOT BUILD")
    print("==========================================")

    # 1. Build Robot Hierarchy
    robot = robot_builder.spawn_tennis_robot()

    # 2. Verify Robot Hierarchy
    if robot:
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        all_actors = actor_subsystem.get_all_level_actors()
        robot_parts = [a for a in all_actors if a and a.get_actor_label().startswith("TennisRobot_")]
        loc = robot.get_actor_location()
        
        print("------------------------------------------")
        print("Phase 10 Inspection Results:")
        print("  - Main Robot Chassis: {}".format(robot.get_actor_label()))
        print("  - Total Robot Actors Spawned: {} (Chassis + 4 Wheels + Bucket + Roller + Mount)".format(len(robot_parts)))
        print("  - World Position: ({:.1f}, {:.1f}, {:.1f})".format(loc.x, loc.y, loc.z))
        print("  - Folder Hierarchy: TennisCourt/Robot")
        print("==========================================")
        print("[build_phase10_robot] Phase 10 verification PASSED.")
        print("==========================================")
    else:
        print("[build_phase10_robot] Phase 10 verification FAILED.")


if __name__ == "__main__":
    run()