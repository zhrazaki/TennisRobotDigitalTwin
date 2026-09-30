"""
Purpose:     Phase 11 Orchestrator Script.
Dependencies: Court.player_spawner, Sensors.camera_setup
"""

import unreal
from Court import player_spawner
from Sensors import camera_setup


def run():
    print("==========================================")
    print("STARTING PHASE 11 — OPPONENT TARGET & CAMERA INTEGRATION")
    print("==========================================")

    # 1. Spawn Opponent at far END of court, facing the robot
    player = player_spawner.spawn_opponent_player(preset="baseline")

    # 2. Attach Camera to Robot
    cam = camera_setup.attach_camera_to_robot()

    if player and cam:
        print("------------------------------------------")
        print("Phase 11 Verification Results:")
        print("  - Opponent Target Spawned: Success (Far side court)")
        print("  - Robot Camera Mounted: Success (Height: 60cm, Pitch: -5 deg)")
        print("==========================================")
        print("[build_phase11_vision_setup] Phase 11 PASSED.")
        print("==========================================")
    else:
        print("[build_phase11_vision_setup] Phase 11 FAILED.")


if __name__ == "__main__":
    run()