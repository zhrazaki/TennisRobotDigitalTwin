"""
Purpose:
    Builds surrounding court infrastructure (Standalone Version):
    - High Perimeter Wire Fence & Sponsor Boards
    - Elevated Umpire Chair & Player Benches
    - 4x Stadium Floodlight Towers
"""

import unreal

ENV_FOLDER_PATH = "TennisCourt/Environment"
ENV_TAG_PREFIX = "TennisCourt_Env_"

# Standard ITF Dimensions (cm)
SURFACE_LENGTH_CM = 3657.6
SURFACE_WIDTH_CM = 1828.8
NET_SPAN_CM = 640.08


def _actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def clear_environment_actors():
    """Removes previous environment actors."""
    subsystem = _actor_subsystem()
    destroyed_count = 0
    for actor in subsystem.get_all_level_actors():
        if actor is None:
            continue
        tags = [str(t) for t in actor.tags]
        if any(t.startswith(ENV_TAG_PREFIX) for t in tags) or "TennisEnv_" in actor.get_actor_label():
            subsystem.destroy_actor(actor)
            destroyed_count += 1

    if destroyed_count > 0:
        unreal.log(f"[environment_builder] Cleared {destroyed_count} previous environment actors.")


def build_court_environment():
    """Spawns fence walls, sponsor boards, light posts, umpire chair, and benches."""
    clear_environment_actors()
    subsystem = _actor_subsystem()

    cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")

    half_len = SURFACE_LENGTH_CM / 2.0  # 1828.8 cm
    half_wid = SURFACE_WIDTH_CM / 2.0   # 914.4 cm
    fence_h = 300.0  # 3 meters height

    created_actors = {}

    # 1. Perimeter Chain-Link Fence Walls (4 sides)
    fence_configs = [
        ("Fence_Back_Pos", unreal.Vector(half_len, 0.0, fence_h / 2.0), unreal.Vector(0.05, half_wid * 2.0 / 100.0, fence_h / 100.0)),
        ("Fence_Back_Neg", unreal.Vector(-half_len, 0.0, fence_h / 2.0), unreal.Vector(0.05, half_wid * 2.0 / 100.0, fence_h / 100.0)),
        ("Fence_Side_Pos", unreal.Vector(0.0, half_wid, fence_h / 2.0), unreal.Vector(half_len * 2.0 / 100.0, 0.05, fence_h / 100.0)),
        ("Fence_Side_Neg", unreal.Vector(0.0, -half_wid, fence_h / 2.0), unreal.Vector(half_len * 2.0 / 100.0, 0.05, fence_h / 100.0)),
    ]

    for name, pos, scale in fence_configs:
        actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, pos, unreal.Rotator(0, 0, 0))
        actor.set_actor_label(f"TennisEnv_{name}")
        actor.set_folder_path(unreal.Name(ENV_FOLDER_PATH))
        actor.set_editor_property("tags", [unreal.Name(f"{ENV_TAG_PREFIX}{name}")])
        actor.static_mesh_component.set_static_mesh(cube_mesh)
        actor.set_actor_scale3d(scale)
        created_actors[name] = actor

    # 2. Sponsor Boards (Lower dark walls at backlines)
    board_h = 90.0
    sponsor_configs = [
        ("SponsorBoard_Pos", unreal.Vector(half_len - 10.0, 0.0, board_h / 2.0), unreal.Vector(0.1, (half_wid * 1.6) / 100.0, board_h / 100.0)),
        ("SponsorBoard_Neg", unreal.Vector(-(half_len - 10.0), 0.0, board_h / 2.0), unreal.Vector(0.1, (half_wid * 1.6) / 100.0, board_h / 100.0)),
    ]

    for name, pos, scale in sponsor_configs:
        actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, pos, unreal.Rotator(0, 0, 0))
        actor.set_actor_label(f"TennisEnv_{name}")
        actor.set_folder_path(unreal.Name(ENV_FOLDER_PATH))
        actor.set_editor_property("tags", [unreal.Name(f"{ENV_TAG_PREFIX}{name}")])
        actor.static_mesh_component.set_static_mesh(cube_mesh)
        actor.set_actor_scale3d(scale)
        created_actors[name] = actor

    # 3. 4x Stadium Floodlight Poles
    light_h = 800.0
    pole_offset_x = half_len * 0.7
    pole_offset_y = half_wid + 50.0
    poles_pos = [
        ("LightPole_1", unreal.Vector(pole_offset_x, pole_offset_y, light_h / 2.0)),
        ("LightPole_2", unreal.Vector(-pole_offset_x, pole_offset_y, light_h / 2.0)),
        ("LightPole_3", unreal.Vector(pole_offset_x, -pole_offset_y, light_h / 2.0)),
        ("LightPole_4", unreal.Vector(-pole_offset_x, -pole_offset_y, light_h / 2.0)),
    ]

    for name, pos in poles_pos:
        # Vertical Pole
        pole_actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, pos, unreal.Rotator(0, 0, 0))
        pole_actor.set_actor_label(f"TennisEnv_{name}")
        pole_actor.set_folder_path(unreal.Name(ENV_FOLDER_PATH))
        pole_actor.set_editor_property("tags", [unreal.Name(f"{ENV_TAG_PREFIX}{name}")])
        pole_actor.static_mesh_component.set_static_mesh(cylinder_mesh)
        pole_actor.set_actor_scale3d(unreal.Vector(0.25, 0.25, light_h / 100.0))
        created_actors[name] = pole_actor

        # Top Light Head Box
        head_pos = unreal.Vector(pos.x, pos.y, light_h)
        head_actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, head_pos, unreal.Rotator(0, 0, 0))
        head_actor.set_actor_label(f"TennisEnv_{name}_Head")
        head_actor.set_folder_path(unreal.Name(ENV_FOLDER_PATH))
        head_actor.set_editor_property("tags", [unreal.Name(f"{ENV_TAG_PREFIX}{name}_Head")])
        head_actor.static_mesh_component.set_static_mesh(cube_mesh)
        head_actor.set_actor_scale3d(unreal.Vector(0.8, 1.5, 0.6))

    # 4. Elevated Umpire Chair (Beside Net)
    umpire_pos = unreal.Vector(0.0, NET_SPAN_CM + 120.0, 100.0)
    umpire_actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, umpire_pos, unreal.Rotator(0, 0, 0))
    umpire_actor.set_actor_label("TennisEnv_UmpireChair")
    umpire_actor.set_folder_path(unreal.Name(ENV_FOLDER_PATH))
    umpire_actor.set_editor_property("tags", [unreal.Name(f"{ENV_TAG_PREFIX}UmpireChair")])
    umpire_actor.static_mesh_component.set_static_mesh(cube_mesh)
    umpire_actor.set_actor_scale3d(unreal.Vector(0.8, 0.8, 2.0))
    created_actors["UmpireChair"] = umpire_actor

    # 5. Player Benches (Left & Right of Umpire)
    bench_y = NET_SPAN_CM + 140.0
    bench_positions = [
        ("PlayerBench_1", unreal.Vector(250.0, bench_y, 25.0)),
        ("PlayerBench_2", unreal.Vector(-250.0, bench_y, 25.0)),
    ]
    for name, pos in bench_positions:
        bench_actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, pos, unreal.Rotator(0, 0, 0))
        bench_actor.set_actor_label(f"TennisEnv_{name}")
        bench_actor.set_folder_path(unreal.Name(ENV_FOLDER_PATH))
        bench_actor.set_editor_property("tags", [unreal.Name(f"{ENV_TAG_PREFIX}{name}")])
        bench_actor.static_mesh_component.set_static_mesh(cube_mesh)
        bench_actor.set_actor_scale3d(unreal.Vector(1.8, 0.6, 0.5))
        created_actors[name] = bench_actor

    unreal.log(f"[environment_builder] Successfully built {len(created_actors)} environment objects.")
    return created_actors