"""
Purpose:
    Master PBR Material Assigner for Tennis Court, Net, and Surrounding Environment.
"""

import unreal


def _apply_material_params(actor, color_rgba, roughness=0.8, metallic=0.0):
    """Utility to create dynamic material instance and apply basic parameters."""
    base_mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    if not base_mat or not actor:
        return None

    comp = actor.static_mesh_component
    dyn_mat = comp.create_dynamic_material_instance(0, base_mat)
    if dyn_mat:
        dyn_mat.set_vector_parameter_value("Color", color_rgba)
        dyn_mat.set_scalar_parameter_value("Roughness", roughness)
        dyn_mat.set_scalar_parameter_value("Metallic", metallic)
    return dyn_mat


def apply_court_materials():
    """Applies high-realism materials to all court components and environment."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    updated_count = 0

    for actor in all_actors:
        label = actor.get_actor_label()
        tags = [str(t) for t in actor.tags]

        # 1. Inner Court Surface (US Open Cobalt Blue)
        if label == "TennisCourt_Surface_Inner":
            _apply_material_params(actor, unreal.LinearColor(0.012, 0.04, 0.22, 1.0), roughness=0.85)
            updated_count += 1

        # 2. Outer Court Buffer (Tournament Forest Green)
        elif label == "TennisCourt_Surface_Outer" or label == "TennisCourt_Surface":
            _apply_material_params(actor, unreal.LinearColor(0.02, 0.09, 0.03, 1.0), roughness=0.9)
            updated_count += 1

        # 3. Court Lines & Net Top Tape (Matte White)
        elif any("TennisCourt_Line_" in t for t in tags) or "TopBand" in label or "CenterStrap" in label:
            _apply_material_params(actor, unreal.LinearColor(0.9, 0.9, 0.9, 1.0), roughness=0.4)
            updated_count += 1

        # 4. Net Mesh Grid (Dark Translucent Grey)
        elif label == "TennisNet_Mesh":
            _apply_material_params(actor, unreal.LinearColor(0.01, 0.01, 0.01, 0.5), roughness=0.95)
            updated_count += 1

        # 5. Net Posts & Light Poles (Dark Steel/Metallic)
        elif "NetPost" in label or "LightPole" in label:
            _apply_material_params(actor, unreal.LinearColor(0.03, 0.03, 0.04, 1.0), roughness=0.2, metallic=0.85)
            updated_count += 1

        # 6. Fence Wire Grid (Dark Mesh Grey)
        elif "Fence_" in label:
            _apply_material_params(actor, unreal.LinearColor(0.05, 0.05, 0.05, 0.6), roughness=0.8)
            updated_count += 1

        # 7. Backline Sponsor Boards (Deep Navy Blue)
        elif "SponsorBoard" in label:
            _apply_material_params(actor, unreal.LinearColor(0.005, 0.015, 0.06, 1.0), roughness=0.3)
            updated_count += 1

        # 8. Umpire Chair & Player Benches (Clean White Plastic/Aluminum)
        elif "UmpireChair" in label or "PlayerBench" in label:
            _apply_material_params(actor, unreal.LinearColor(0.8, 0.8, 0.82, 1.0), roughness=0.3)
            updated_count += 1

        # 9. Light Heads (Emissive White Material)
        elif "_Head" in label:
            _apply_material_params(actor, unreal.LinearColor(1.0, 1.0, 0.9, 1.0), roughness=0.1)
            updated_count += 1

    unreal.log(f"[material_builder] Applied complete environment shaders to {updated_count} actors.")
    return updated_count