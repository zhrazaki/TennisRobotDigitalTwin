"""
Purpose:
    Phase 1 deliverable script. Proves the central configuration +
    coordinate system are correct and internally consistent, prints a
    full report, and (when run inside the Unreal Editor) draws temporary
    debug lines/points in the level viewport so you can SEE the future
    court's exact footprint before any mesh exists.

    This is the "usable result" for Phase 1 — no geometry is created or
    saved, nothing is spawned, only editor debug drawing (non-persistent,
    purely visual, safe to run repeatedly).

Dependencies:
    - Python/Core/units.py
    - Python/Core/court_config.py
    - Python/Core/coordinate_system.py
    - `unreal` module (only for the drawing step; the validation/report
      step works fine outside the Editor too, e.g. from a plain
      terminal `python` for a quick sanity check).

Inputs:
    None. Run the file directly.

Outputs:
    - Printed validation report (Output Log if run in-Editor).
    - Debug lines/points drawn in the active editor viewport for
      DEBUG_DRAW_DURATION_SECONDS (see below), if `unreal` is available.

How to run inside Unreal Editor 5.5 (macOS):
    1. Window > Developer Tools > Output Log (so you can see prints).
    2. In the Output Log's Python console (or Window > Developer Tools
       > Python), run:
           import sys
           sys.path.append("/absolute/path/to/<project_root>/Python")
           import Tools.validate_phase1_config as v
           v.run()
       (If you edit Core/ or coordinate_system.py and re-run, call
        v.run(force_reload=True) to bypass the cached CourtConfig.)
    Alternatively: Editor Preferences > General > Python > "Additional
    Paths" > add "<project_root>/Python" once, restart the Editor, and
    just `import Tools.validate_phase1_config as v; v.run()` from then on.
"""

import os
import sys

# Make sure "Core" and "Tools" are importable even if the caller hasn't
# added Python/ to sys.path yet (belt-and-braces for a first run).
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PYTHON_ROOT = os.path.normpath(os.path.join(_THIS_DIR, ".."))
if _PYTHON_ROOT not in sys.path:
    sys.path.append(_PYTHON_ROOT)

from Core.court_config import get_court_config, CourtConfigError
from Core import coordinate_system as cs

DEBUG_DRAW_DURATION_SECONDS = 120.0
DEBUG_DRAW_Z_OFFSET = 2.0  # lift lines slightly above Z=0 so they're visible on a flat floor


def _print_report(cfg):
    print("=" * 70)
    print("TENNIS COURT — PHASE 1 VALIDATION REPORT")
    print("=" * 70)
    print(cfg.summary())
    print("-" * 70)
    points = cs.get_all_key_points()
    print("Origin:                 %s" % (points["origin"],))
    print("Doubles corners:")
    for c in points["doubles_corners"]:
        print("    %s" % (c,))
    print("Net line:                %s -> %s" % (points["net_line"]["start"], points["net_line"]["end"]))
    print("Net posts:               %s" % points["net_posts"])
    print("Service boxes:")
    for box in points["service_boxes"]:
        print("    %-10s corners=%s" % (box["name"], box["corners"]))
    print("Center marks:")
    for mark in points["center_marks"]:
        print("    %-16s start=%s end=%s" % (mark["name"], mark["start"], mark["end"]))
    print("=" * 70)


def _draw_debug(cfg):
    try:
        import unreal
    except ImportError:
        print("[validate_phase1_config] 'unreal' module not available — "
              "skipping viewport drawing (report above is still valid).")
        return

    # Resolve an editor world across UE5.x API variants.
    world = None
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        try:
            world = unreal.EditorLevelLibrary.get_editor_world()
        except Exception:
            world = None

    if world is None:
        print("[validate_phase1_config] Could not resolve an editor world — "
              "skipping viewport drawing (report above is still valid).")
        return

    def line(p1, p2, color):
        unreal.SystemLibrary.draw_debug_line(
            world,
            unreal.Vector(p1[0], p1[1], p1[2] + DEBUG_DRAW_Z_OFFSET),
            unreal.Vector(p2[0], p2[1], p2[2] + DEBUG_DRAW_Z_OFFSET),
            color,
            DEBUG_DRAW_DURATION_SECONDS,
            2.0,
        )

    def point(p, color, size=12.0):
        unreal.SystemLibrary.draw_debug_point(
            world,
            unreal.Vector(p[0], p[1], p[2] + DEBUG_DRAW_Z_OFFSET),
            size,
            color,
            DEBUG_DRAW_DURATION_SECONDS,
        )

    WHITE = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
    YELLOW = unreal.LinearColor(1.0, 1.0, 0.0, 1.0)
    CYAN = unreal.LinearColor(0.0, 1.0, 1.0, 1.0)
    RED = unreal.LinearColor(1.0, 0.0, 0.0, 1.0)

    points = cs.get_all_key_points()

    # Doubles outline.
    corners = points["doubles_corners"]
    for i in range(4):
        line(corners[i], corners[(i + 1) % 4], WHITE)

    # Singles outline.
    singles_corners = points["singles_corners"]
    for i in range(4):
        line(singles_corners[i], singles_corners[(i + 1) % 4], WHITE)

    # Net line + posts.
    line(points["net_line"]["start"], points["net_line"]["end"], CYAN)
    for post in points["net_posts"].values():
        point(post, CYAN, 16.0)

    # Service boxes + center service line.
    for box in points["service_boxes"]:
        c = box["corners"]
        for i in range(4):
            line(c[i], c[(i + 1) % 4], YELLOW)
    for seg in points["center_service_line"]:
        line(seg["start"], seg["end"], YELLOW)

    # Center marks + origin.
    for mark in points["center_marks"]:
        line(mark["start"], mark["end"], RED)
    point(points["origin"], RED, 20.0)

    print("[validate_phase1_config] Debug geometry drawn for %.0f seconds "
          "(white=doubles/singles lines, yellow=service boxes+center line, "
          "cyan=net, red=center marks/origin)." % DEBUG_DRAW_DURATION_SECONDS)


def run(force_reload: bool = False):
    try:
        cfg = get_court_config(force_reload=force_reload)
    except CourtConfigError as e:
        print("[validate_phase1_config] CONFIG ERROR: %s" % e)
        raise

    _print_report(cfg)

    try:
        cs.validate_layout()
        print("[validate_phase1_config] coordinate_system.validate_layout() PASSED")
    except AssertionError as e:
        print("[validate_phase1_config] coordinate_system.validate_layout() FAILED: %s" % e)
        raise

    _draw_debug(cfg)
    print("[validate_phase1_config] Phase 1 validation complete — OK.")


if __name__ == "__main__":
    run()
