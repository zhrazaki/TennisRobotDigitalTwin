"""
Purpose:
    Builds a high-detail tennis net assembly:
    - Left & Right Net Posts with tension hardware
    - Main Net Mesh Grid
    - White Top Cable Band (5cm height)
    - Center Adjustment Strap
"""

import unreal
from Core.court_config import get_court_config
from Core.coordinate_system import get_net_post_positions

NET_FOLDER_PATH = "TennisCourt/Net"
NET_TAG_PREFIX = "TennisCourt_Net_"


def _actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def destroy_existing_net():
    """Removes all previously spawned net and post actors."""
    subsystem = _actor_subsystem()
    destroyed_count = 0
    for actor in subsystem.get_all_level_actors():
        if actor is None:
            continue
        tags = [str(t) for t in actor.tags]
        if any(t.startswith(NET_TAG_PREFIX) for t in tags) or "TennisNet_" in actor.get_actor_label():
            subsystem.destroy_actor(actor)
            destroyed_count += 1

    if destroyed_count > 0:
        unreal.log(f"[net_builder] Cleared {destroyed_count} previous net actors.")


def build_net_and_posts():
    """Builds Posts, Mesh, White Top Band, and Center Strap."""
    destroy_existing_net()

    cfg = get_court_config()
    subsystem = _actor_subsystem()
    posts = get_net_post_positions(ground_z=0.0)

    created_actors = {}

    cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")

    post_height = cfg.net_height_post_cm
    post_diameter = 10.0
    net_span = cfg.net_post_span_cm * 2.0
    net_center_h = cfg.net_height_center_cm
    band_height = 5.0  # 5cm Top Vinyl Band

    # 1. Net Posts
    for key, pos in posts.items():
        is_positive = pos[1] > 0
        actor_name = f"NetPost_{'Right' if is_positive else 'Left'}"

        post_actor = subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(pos[0], pos[1], post_height / 2.0),
            unreal.Rotator(0.0, 0.0, 0.0)
        )
        post_actor.set_actor_label(actor_name)
        post_actor.set_folder_path(unreal.Name(NET_FOLDER_PATH))
        post_actor.set_editor_property("tags", [unreal.Name(f"{NET_TAG_PREFIX}{actor_name}")])
        post_actor.static_mesh_component.set_static_mesh(cylinder_mesh)
        post_actor.set_actor_scale3d(unreal.Vector(post_diameter / 100.0, post_diameter / 100.0, post_height / 100.0))
        created_actors[actor_name] = post_actor

    # 2. Main Net Mesh — REAL grid (not a solid black box).
    # Parent group actor + thin string actors attached to it.
    # Net plane: X=0, span along Y, height along Z.
    mesh_height = net_center_h - band_height
    string_thickness = 1.0  # cm
    step_y = 8.0  # cm between vertical strings
    step_z = 8.0  # cm between horizontal strings

    net_parent = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0)
    )
    net_parent.set_actor_label("TennisNet_Mesh")
    net_parent.set_folder_path(unreal.Name(NET_FOLDER_PATH))
    net_parent.set_editor_property("tags", [unreal.Name(f"{NET_TAG_PREFIX}Mesh")])
    # No mesh on parent -> renders nothing, just a group holder.
    created_actors["TennisNet_Mesh"] = net_parent

    base_mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    dark_color = unreal.LinearColor(0.01, 0.01, 0.01, 1.0)

    def _spawn_string(name, loc, scale):
        actor = subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor, loc, unreal.Rotator(0.0, 0.0, 0.0)
        )
        if actor is None:
            return None
        actor.set_actor_label(name)
        actor.set_folder_path(unreal.Name(NET_FOLDER_PATH + "/Mesh"))
        actor.set_editor_property("tags", [unreal.Name(f"{NET_TAG_PREFIX}String_{name}")])
        comp = actor.static_mesh_component
        comp.set_static_mesh(cube_mesh)
        # Thin strings, no collision (perf + ball passes visually correct)
        comp.set_collision_profile_name("NoCollision")
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        if base_mat:
            dyn = comp.create_dynamic_material_instance(0, base_mat)
            if dyn:
                dyn.set_vector_parameter_value("Color", dark_color)
                dyn.set_scalar_parameter_value("Roughness", 0.95)
                dyn.set_scalar_parameter_value("Metallic", 0.0)
        actor.set_actor_scale3d(scale)
        actor.attach_to_actor(
            net_parent, unreal.Name(),
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD, False
        )
        return actor

    half_span = net_span / 2.0
    # Vertical strings
    y = -half_span
    vi = 0
    while y <= half_span + 0.01:
        _spawn_string(
            f"TennisNet_String_V{vi:03d}",
            unreal.Vector(0.0, y, mesh_height / 2.0),
            unreal.Vector(string_thickness / 100.0, string_thickness / 100.0, mesh_height / 100.0)
        )
        y += step_y
        vi += 1

    # Horizontal strings
    z = step_z / 2.0
    hi = 0
    while z < mesh_height:
        _spawn_string(
            f"TennisNet_String_H{hi:03d}",
            unreal.Vector(0.0, 0.0, z),
            unreal.Vector(string_thickness / 100.0, net_span / 100.0, string_thickness / 100.0)
        )
        z += step_z
        hi += 1

    unreal.log(f"[net_builder] Net grid: {vi} vertical + {hi} horizontal strings.")

    # 3. White Top Cable Band
    band_actor = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(0.0, 0.0, mesh_height + (band_height / 2.0)),
        unreal.Rotator(0.0, 0.0, 0.0)
    )
    band_actor.set_actor_label("TennisNet_TopBand")
    band_actor.set_folder_path(unreal.Name(NET_FOLDER_PATH))
    band_actor.set_editor_property("tags", [unreal.Name(f"{NET_TAG_PREFIX}TopBand")])
    band_actor.static_mesh_component.set_static_mesh(cube_mesh)
    band_actor.set_actor_scale3d(unreal.Vector(0.02, net_span / 100.0, band_height / 100.0))
    created_actors["TennisNet_TopBand"] = band_actor

    # 4. White Center Strap
    strap_actor = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(0.0, 0.0, net_center_h / 2.0),
        unreal.Rotator(0.0, 0.0, 0.0)
    )
    strap_actor.set_actor_label("TennisNet_CenterStrap")
    strap_actor.set_folder_path(unreal.Name(NET_FOLDER_PATH))
    strap_actor.set_editor_property("tags", [unreal.Name(f"{NET_TAG_PREFIX}CenterStrap")])
    strap_actor.static_mesh_component.set_static_mesh(cube_mesh)
    strap_actor.set_actor_scale3d(unreal.Vector(0.025, 0.05, net_center_h / 100.0))
    created_actors["TennisNet_CenterStrap"] = strap_actor

    unreal.log(f"[net_builder] Successfully built {len(created_actors)} net actors.")
    return created_actors
