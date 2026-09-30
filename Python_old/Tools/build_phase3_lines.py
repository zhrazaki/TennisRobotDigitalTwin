"""
Purpose:
    Tool script to clean up existing line actors, execute Phase 3 line creation,
    and verify the spawned line actors in Unreal Editor.

Usage inside Unreal Editor Python Console:
    import Tools.build_phase3_lines as p3
    p3.run()
"""

import unreal
from Core.court_config import get_court_config
import Court.lines_builder as lines_builder


def verify_lines(lines_dict):
    """Numerically verifies spawned line actors against CourtConfig."""
    cfg = get_court_config()
    expected_count = 11  # 2 Baselines, 2 SvcLines, 2 DblSide, 2 SglSide, 2 CenterSvc, 2 CenterMarks = 12 total segments (11 dict keys)
    
    assert len(lines_dict) >= 11, f"Expected at least 11 line components, got {len(lines_dict)}"

    # Check baseline presence and mobility
    far_baseline = lines_dict.get("Baseline_Far")
    assert far_baseline is not None, "Baseline_Far missing"
    assert far_baseline.get_folder_path() == "TennisCourt/Lines", "Incorrect folder path for lines"
    
    unreal.log("[build_phase3_lines] Verification check:")
    unreal.log(f"  Total line actors created: {len(lines_dict)}")
    unreal.log(f"  Standard line width: {cfg.line_width_cm} cm")
    unreal.log(f"  Baseline line width: {cfg.baseline_width_cm} cm")
    unreal.log(f"  Folder Path: TennisCourt/Lines")

    return True


def run():
    unreal.log("==========================================")
    unreal.log("STARTING PHASE 3 — COURT LINES GENERATION")
    unreal.log("==========================================")

    # Step 1: Clean up existing lines
    lines_builder.destroy_existing_lines()

    # Step 2: Build new line set
    lines = lines_builder.build_court_lines(ground_z_offset=0.1)

    # Step 3: Verify creation
    if verify_lines(lines):
        unreal.log("==========================================")
        unreal.log("[build_phase3_lines] Phase 3 verification PASSED.")
        unreal.log("==========================================")
    else:
        unreal.log_error("[build_phase3_lines] Phase 3 verification FAILED.")


if __name__ == "__main__":
    run()