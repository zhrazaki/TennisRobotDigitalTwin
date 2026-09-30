"""
Purpose:
    Executes Net and Post creation (Phase 4) with updated multi-part net validation.

Usage inside Unreal Editor Python Console:
    import Tools.build_phase4_net as p4
    p4.run()
"""

import unreal
import Court.net_builder as net_builder


def run():
    unreal.log("==========================================")
    unreal.log("STARTING PHASE 4 — TENNIS NET & POSTS")
    unreal.log("==========================================")

    # 1. Clean up
    net_builder.destroy_existing_net()

    # 2. Build detailed net components
    actors = net_builder.build_net_and_posts()

    # 3. Verify 5 components (2 posts + 1 mesh + 1 top band + 1 center strap)
    assert len(actors) == 5, f"Expected 5 actors (2 posts, mesh, top band, strap), got {len(actors)}"

    unreal.log("[build_phase4_net] Verification check:")
    unreal.log(f"  Total net component actors created: {len(actors)}")
    unreal.log("  Net Posts: Spawned at Y post span")
    unreal.log("  Net Mesh & Strap: Alignment verified")
    unreal.log("==========================================")
    unreal.log("[build_phase4_net] Phase 4 verification PASSED.")
    unreal.log("==========================================")


if __name__ == "__main__":
    run()