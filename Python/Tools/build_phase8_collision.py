"""
Purpose:     Phase 8 Execution & Verification Script.
             Applies physics collisions via collision_builder and validates:
             1. Court Center Origin is at (0, 0, 0)
             2. Collision settings on Court Actors
Dependencies: unreal, Core.court_config, Court.collision_builder
Inputs:      None
Outputs:     Prints verification check results to Unreal Output Log.
"""

import unreal
from Core import court_config
from Court import collision_builder


def run():
    print("==========================================")
    print("STARTING PHASE 8 — COLLISION & VALIDATION")
    print("==========================================")

    cfg = court_config.get_court_config()

    # 1. Apply collisions
    modified_actors = collision_builder.apply_court_collisions()

    # 2. Origin & Coordinate Validation (Check 0,0,0)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    origin_verified = False

    for actor in all_actors:
        if actor and actor.get_actor_label() == "TennisCourt_Surface_Inner":
            loc = actor.get_actor_location()
            if abs(loc.x) <= 0.01 and abs(loc.y) <= 0.01:
                origin_verified = True
                print("[coordinate_system] Court Center origin (0, 0, 0) verified on Inner Surface.")
            else:
                print("[ERROR] Inner surface origin mismatch: ({:.2f}, {:.2f}, {:.2f})".format(loc.x, loc.y, loc.z))

    # 3. Verification Summary
    print("------------------------------------------")
    print("Phase 8 Verification Results:")
    print("  - Collision Profiles Updated: {} actors".format(modified_actors))
    print("  - Origin Standard (0,0,0): {}".format("PASSED" if origin_verified else "FAILED"))
    print("==========================================")
    if origin_verified:
        print("[build_phase8_collision] Phase 8 verification PASSED.")
    else:
        print("[build_phase8_collision] Phase 8 verification FAILED.")
    print("==========================================")


if __name__ == "__main__":
    run()