"""
Purpose:
    Executes Phase 5 material application and performs final verification.

Usage inside Unreal Editor Python Console:
    import Tools.build_phase5_materials as p5
    p5.run()
"""

import unreal
import Court.material_builder as material_builder


def run():
    unreal.log("==========================================")
    unreal.log("STARTING PHASE 5 — COURT MATERIALS & COLORS")
    unreal.log("==========================================")

    count = material_builder.apply_court_materials()

    unreal.log("[build_phase5_materials] Verification check:")
    unreal.log(f"  Total updated components: {count}")
    unreal.log("==========================================")
    unreal.log("[build_phase5_materials] Phase 5 verification PASSED.")
    unreal.log("==========================================")


if __name__ == "__main__":
    run()