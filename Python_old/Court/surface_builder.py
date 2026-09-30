"""
Purpose:
    Spawns (or rebuilds) a two-tone official tennis court surface structure:
    1. Outer Margin Pad (Outfield - Green): Covers the full court length + run-off area.
    2. Inner Play Surface (Infield - Blue): Placed precisely over the doubles play zone.

    Maintains full idempotency, collision setups, and clean folder organisation.
"""

import unreal
from Core.court_config import get_court_config
from Core import coordinate_system as cs

SURFACE_TAG_PREFIX = "TennisCourt_Surface_"
SURFACE_FOLDER_PATH = "TennisCourt/Court"
PLACEHOLDER_MESH_PATH = "/Engine/BasicShapes/Plane.Plane"
ENGINE_PLANE_SIZE_CM = 100.0


def _actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def destroy_existing_surface():
    """Finds and destroys all previously built surface actors."""
    subsystem = _actor_subsystem()
    destroyed_count = 0
    for actor in subsystem.get_all_level_actors():
        if actor is None:
            continue
        tags = [str(t) for t in actor.tags]
        if any(t.startswith(SURFACE_TAG_PREFIX) for t in tags) or actor.get_actor_label().startswith("TennisCourt_Surface"):
            subsystem.destroy_actor(actor)
            destroyed_count += 1

    if destroyed_count > 0:
        print(f"[surface_builder] Cleared {destroyed_count} existing surface actors.")


def build_court_surface(rebuild: bool = True):
    """
    Spawns the two-tone court pad structure (Outer Margin + Inner Court).
    """
    if rebuild:
        destroy_existing_surface()

    cfg = get_court_config()
    total_length_cm, total_width_cm = cs.get_surface_dimensions()

    plane_mesh = unreal.EditorAssetLibrary.load_asset(PLACEHOLDER_MESH_PATH)
    if plane_mesh is None:
        raise RuntimeError(f"Could not load base mesh '{PLACEHOLDER_MESH_PATH}'.")

    subsystem = _actor_subsystem()
    created_actors = {}

    # ----------------------------------------------------
    # 1. Outer Margin Pad (Outfield - Green Run-off Area)
    # ----------------------------------------------------
    outer_actor = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0)
    )
    outer_mesh_comp = outer_actor.static_mesh_component
    outer_mesh_comp.set_static_mesh(plane_mesh)

    outer_scale_x = total_length_cm / ENGINE_PLANE_SIZE_CM
    outer_scale_y = total_width_cm / ENGINE_PLANE_SIZE_CM
    outer_actor.set_actor_scale3d(unreal.Vector(outer_scale_x, outer_scale_y, 1.0))

    outer_mesh_comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    outer_mesh_comp.set_collision_profile_name("BlockAll")

    outer_actor.set_actor_label("TennisCourt_Surface_Outer")
    outer_actor.set_folder_path(SURFACE_FOLDER_PATH)
    outer_actor.set_editor_property("tags", [unreal.Name(f"{SURFACE_TAG_PREFIX}Outer")])
    created_actors["Outer"] = outer_actor

    # ----------------------------------------------------
    # 2. Inner Play Surface (Infield - Blue Court Zone)
    # Z-offset = 0.05cm to prevent Z-fighting flickering
    # ----------------------------------------------------
    inner_actor = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.05), unreal.Rotator(0.0, 0.0, 0.0)
    )
    inner_mesh_comp = inner_actor.static_mesh_component
    inner_mesh_comp.set_static_mesh(plane_mesh)

    inner_scale_x = cfg.court_length_cm / ENGINE_PLANE_SIZE_CM
    inner_scale_y = cfg.doubles_width_cm / ENGINE_PLANE_SIZE_CM
    inner_actor.set_actor_scale3d(unreal.Vector(inner_scale_x, inner_scale_y, 1.0))

    inner_mesh_comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    inner_mesh_comp.set_collision_profile_name("BlockAll")

    inner_actor.set_actor_label("TennisCourt_Surface_Inner")
    inner_actor.set_folder_path(SURFACE_FOLDER_PATH)
    inner_actor.set_editor_property("tags", [unreal.Name(f"{SURFACE_TAG_PREFIX}Inner")])
    created_actors["Inner"] = inner_actor

    print(
        f"[surface_builder] Built Two-Tone Court Surface:\n"
        f"  - Outer Pad: {total_length_cm:.1f}cm x {total_width_cm:.1f}cm\n"
        f"  - Inner Pad: {cfg.court_length_cm:.1f}cm x {cfg.doubles_width_cm:.1f}cm"
    )
    return created_actors