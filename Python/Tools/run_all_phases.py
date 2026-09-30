"""
Purpose: Run ALL build phases in order with one click.
Usage:
  Tools > Execute Python Script > select run_all_phases.py
  OR in Output Log (Python tab):
    import Tools.run_all_phases as all; all.run()
"""

import os
import sys

try:
    _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ not defined when exec'd from Unreal Cmd "py" console
    _THIS_DIR = os.path.normpath("F:/unreal project/TennisRobotSim/TennisRobotSim 5.5/Python/Tools")
_PYTHON_ROOT = os.path.normpath(os.path.join(_THIS_DIR, ".."))
# insert at 0 so our Core/Court/Tools packages win over anything else
if _PYTHON_ROOT in sys.path:
    sys.path.remove(_PYTHON_ROOT)
sys.path.insert(0, _PYTHON_ROOT)
# also add forward-slash variant (Unreal mixes separators)
_ALT_ROOT = _PYTHON_ROOT.replace("\\", "/")
if _ALT_ROOT not in sys.path:
    sys.path.insert(0, _ALT_ROOT)

import importlib.util


def _load(name, filename):
    path = os.path.join(_THIS_DIR, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run():
    print("##########################################")
    print("# RUNNING ALL PHASES 1 -> 11")
    print("##########################################")
    print("[run_all] PYTHON_ROOT=%s" % _PYTHON_ROOT)

    # Auto-purge cached project modules so file edits apply WITHOUT restart.
    for _m in list(sys.modules):
        top = _m.split(".")[0]
        if top in ("Court", "Core", "Sensors") or (
            _m.startswith("Tools.") and _m != "Tools.run_all_phases"
        ):
            try:
                del sys.modules[_m]
            except KeyError:
                pass

    # Load by file path -> works in BOTH modes:
    #  - Output Log Python tab (import mode)
    #  - Output Log Cmd tab with: py "F:/.../run_all_phases.py"
    p1 = _load("Tools.validate_phase1_config", "validate_phase1_config.py")
    p2 = _load("Tools.build_phase2_surface", "build_phase2_surface.py")
    p3 = _load("Tools.build_phase3_lines", "build_phase3_lines.py")
    p4 = _load("Tools.build_phase4_net", "build_phase4_net.py")
    p5 = _load("Tools.build_phase5_materials", "build_phase5_materials.py")
    p8 = _load("Tools.build_phase8_collision", "build_phase8_collision.py")
    p9 = _load("Tools.build_phase9_polish", "build_phase9_polish.py")
    p10 = _load("Tools.build_phase10_robot", "build_phase10_robot.py")
    p11 = _load("Tools.build_phase11_vision_setup", "build_phase11_vision_setup.py")

    phases = [
        ("Phase 1 - Validate Config", p1.run),
        ("Phase 2 - Surface", p2.run),
        ("Phase 3 - Lines", p3.run),
        ("Phase 4 - Net", p4.run),
        ("Phase 5 - Materials", p5.run),
        ("Phase 8 - Collision", p8.run),
        ("Phase 9 - Polish", p9.run),
        ("Phase 10 - Robot", p10.run),
        ("Phase 11 - Vision", p11.run),
    ]

    for name, fn in phases:
        print(f"\n===== {name} =====")
        try:
            fn()
        except Exception as e:
            print(f"[run_all] FAILED at {name}: {e}")
            import traceback
            traceback.print_exc()
            print("[run_all] Stopping here. Fix the error and re-run.")
            return

    print("\n##########################################")
    print("[run_all] ALL PHASES COMPLETED SUCCESSFULLY")
    print("##########################################")


if __name__ == "__main__":
    run()
