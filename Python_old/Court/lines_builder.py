"""
Purpose:
    Builds all official tennis court lines on top of the Phase 2 surface
    mesh using procedural engine planes, positioned precisely according to
    Core.coordinate_system.

Dependencies:
    - Core/court_config.py
    - Core/coordinate_system.py
    - unreal (Unreal Engine Python API)
"""

import unreal

from Core.court_config import get_court_config
from Core.coordinate_system import (
    get_baseline_x,
    get_center_marks,
    get_center_service_line,
    get_doubles_sideline_y,
    get_service_line_x,
    get_singles_sideline_y,
)

LINES_FOLDER_PATH = "TennisCourt/Lines"
LINE_TAG_PREFIX = "TennisCourt_Line_"


def destroy_existing_lines():
    """Finds and destroys all existing line actors to prevent duplicates."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    destroyed_count = 0
    for actor in all_actors:
        actor_tags = actor.tags
        for tag in actor_tags:
            if str(tag).startswith(LINE_TAG_PREFIX):
                actor_subsystem.destroy_actor(actor)
                destroyed_count += 1
                break

    if destroyed_count > 0:
        unreal.log(f"[lines_builder] Cleared {destroyed_count} previous line actors.")


def _spawn_line_plane(name, center_x, center_y, size_x, size_y, ground_z_offset=0.5):
    """
    Spawns a single line segment as a static mesh plane.
    Offset Z is set to 0.5cm to avoid Z-fighting with surface.
    """
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    
    location = unreal.Vector(center_x, center_y, ground_z_offset)
    rotation = unreal.Rotator(0.0, 0.0, 0.0)

    actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, location, rotation
    )

    actor.set_actor_label(name)
    actor.set_folder_path(unreal.Name(LINES_FOLDER_PATH))
    actor.tags = [unreal.Name(f"{LINE_TAG_PREFIX}{name}")]

    # Load default Engine Plane Mesh
    plane_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    actor.static_mesh_component.set_static_mesh(plane_mesh)

    # Set white basic material so lines are clearly visible
    white_mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    if white_mat:
        actor.static_mesh_component.set_material(0, white_mat)

    # Calculate scale relative to default 100x100 cm Engine Plane
    scale_x = size_x / 100.0
    scale_y = size_y / 100.0
    
    actor.set_actor_scale3d(unreal.Vector(scale_x, scale_y, 1.0))

    # Set mobility and collision properties
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    actor.static_mesh_component.set_collision_profile_name("NoCollision")

    return actor


def build_court_lines(ground_z_offset=0.5):
    """Computes and builds all standard tennis court lines based on CourtConfig."""
    cfg = get_court_config()
    std_w = cfg.line_width_cm
    base_w = cfg.baseline_width_cm

    x_base_pos, x_base_neg = get_baseline_x()
    x_svc_pos, x_svc_neg = get_service_line_x()
    y_dbl_pos, y_dbl_neg = get_doubles_sideline_y()
    y_sgl_pos, y_sgl_neg = get_singles_sideline_y()

    court_length = cfg.court_length_cm
    doubles_width = cfg.doubles_width_cm
    singles_width = cfg.singles_width_cm
    svc_line_span = singles_width

    created_lines = {}

    # 1. Baselines
    created_lines["Baseline_Far"] = _spawn_line_plane(
        "Baseline_Far", x_base_pos, 0.0, base_w, doubles_width, ground_z_offset
    )
    created_lines["Baseline_Near"] = _spawn_line_plane(
        "Baseline_Near", x_base_neg, 0.0, base_w, doubles_width, ground_z_offset
    )

    # 2. Service Lines
    created_lines["ServiceLine_Far"] = _spawn_line_plane(
        "ServiceLine_Far", x_svc_pos, 0.0, std_w, svc_line_span, ground_z_offset
    )
    created_lines["ServiceLine_Near"] = _spawn_line_plane(
        "ServiceLine_Near", x_svc_neg, 0.0, std_w, svc_line_span, ground_z_offset
    )

    # 3. Doubles Sidelines
    created_lines["DoublesSideline_Right"] = _spawn_line_plane(
        "DoublesSideline_Right", 0.0, y_dbl_pos, court_length, std_w, ground_z_offset
    )
    created_lines["DoublesSideline_Left"] = _spawn_line_plane(
        "DoublesSideline_Left", 0.0, y_dbl_neg, court_length, std_w, ground_z_offset
    )

    # 4. Singles Sidelines
    created_lines["SinglesSideline_Right"] = _spawn_line_plane(
        "SinglesSideline_Right", 0.0, y_sgl_pos, court_length, std_w, ground_z_offset
    )
    created_lines["SinglesSideline_Left"] = _spawn_line_plane(
        "SinglesSideline_Left", 0.0, y_sgl_neg, court_length, std_w, ground_z_offset
    )

    # 5. Center Service Line
    center_svc = get_center_service_line()
    for segment in center_svc:
        name = segment["name"]
        start_x = segment["start"][0]
        end_x = segment["end"][0]
        length = abs(end_x - start_x)
        center_x = (start_x + end_x) / 2.0

        created_lines[name] = _spawn_line_plane(
            name, center_x, 0.0, length, std_w, ground_z_offset
        )

    # 6. Center Marks
    center_marks = get_center_marks()
    for mark in center_marks:
        name = mark["name"]
        start_x = mark["start"][0]
        end_x = mark["end"][0]
        length = abs(end_x - start_x)
        center_x = (start_x + end_x) / 2.0

        created_lines[name] = _spawn_line_plane(
            name, center_x, 0.0, length, std_w, ground_z_offset
        )

    unreal.log(f"[lines_builder] Successfully built {len(created_lines)} court line actors.")
    return created_lines