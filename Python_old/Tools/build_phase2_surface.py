"""
Purpose:
    Phase 2 deliverable script. Builds the placeholder court surface pad
    via Court/surface_builder.py, then reads the spawned actor back and
    verifies its size and position match Core's configuration exactly.
    This is the "usable result" for Phase 2: a real, collidable, correctly
    sized/placed actor in the level.

Dependencies:
    - Python/Core/court_config.py
    - Python/Core/coordinate_system.py
    - Python/Court/surface_builder.py
    - `unreal` module (Editor-only — run this inside the Editor).

Inputs:
    None. Run the file directly / call run().

Outputs:
    - The "TennisCourt_Surface" actor in the level (see surface_builder.py
      for exact properties).
    - Printed verification report.

How to run inside Unreal Editor 5.5 (macOS):
    (Assuming <ProjectRoot>/Python is already on sys.path — see Phase 1
    instructions if not.)
        import Tools.build_phase2_surface as p2
        p2.run()
    Re-running is always safe — the surface actor is rebuilt from scratch
    each time (see surface_builder.build_surface(rebuild=True)).
"""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PYTHON_ROOT = os.path.normpath(os.path.join(_THIS_DIR, ".."))
if _PYTHON_ROOT not in sys.path:
    sys.path.append(_PYTHON_ROOT)

from Core.court_config import get_court_config
from Core import coordinate_system as cs
from Court import surface_builder


def _verify(actor):
    cfg = get_court_config()
    expected_length_cm, expected_width_cm = cs.get_surface_dimensions()
    eps = cfg.EPSILON_CM

    scale = actor.get_actor_scale3d()
    actual_length_cm = scale.x * surface_builder.ENGINE_PLANE_SIZE_CM
    actual_width_cm = scale.y * surface_builder.ENGINE_PLANE_SIZE_CM

    location = actor.get_actor_location()

    print("-" * 70)
    print("PHASE 2 VERIFICATION")
    print("-" * 70)
    print("Actor label:            %s" % actor.get_actor_label())
    print("Folder path:            %s" % actor.get_folder_path())
    print("Location:               (%.2f, %.2f, %.2f)" % (location.x, location.y, location.z))
    print(
        "Size (expected):        %.2f cm x %.2f cm"
        % (expected_length_cm, expected_width_cm)
    )
    print("Size (actual):          %.2f cm x %.2f cm" % (actual_length_cm, actual_width_cm))

    assert abs(actual_length_cm - expected_length_cm) < eps, "Surface length does not match config!"
    assert abs(actual_width_cm - expected_width_cm) < eps, "Surface width does not match config!"
    assert abs(location.x) < eps and abs(location.y) < eps and abs(location.z) < eps, (
        "Surface is not centered at the origin!"
    )

    mesh_component = actor.static_mesh_component
    collision_profile = mesh_component.get_collision_profile_name()
    print("Collision profile:      %s" % collision_profile)
    assert collision_profile == "BlockAll", "Surface collision profile is not BlockAll!"

    print("-" * 70)
    print("[build_phase2_surface] Phase 2 verification PASSED.")


def run():
    actor = surface_builder.build_surface(rebuild=True)
    _verify(actor)


if __name__ == "__main__":
    run()
