"""
Purpose: Fixed Daylight & Exposure setup for UE5 Lumen.
"""
import unreal

LIGHT_FOLDER_PATH = "TennisCourt/Lighting"

def _actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def setup_guaranteed_daylight():
    subsystem = _actor_subsystem()

    # 1. Spawn/Configure Directional Light (Sun)
    sun_actor = None
    for actor in subsystem.get_all_level_actors():
        if actor and isinstance(actor, unreal.DirectionalLight):
            sun_actor = actor
            break

    if not sun_actor:
        sun_actor = subsystem.spawn_actor_from_class(
            unreal.DirectionalLight, 
            unreal.Vector(0, 0, 1500), 
            unreal.Rotator(-45.0, 135.0, 0.0)
        )
        sun_actor.set_actor_label("TennisCourt_Sunlight")
        sun_actor.set_folder_path(unreal.Name(LIGHT_FOLDER_PATH))

    sun_actor.root_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    sun_comp = sun_actor.light_component
    sun_comp.set_intensity(10.0)
    sun_comp.set_light_color(unreal.LinearColor(1.0, 0.95, 0.88, 1.0))

    # 2. Configure SkyLight
    sky_actor = None
    for actor in subsystem.get_all_level_actors():
        if actor and isinstance(actor, unreal.SkyLight):
            sky_actor = actor
            break

    if sky_actor:
        sky_actor.root_component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        sky_comp = sky_actor.light_component
        sky_comp.set_intensity(2.0)
        sky_comp.recapture_sky()

    # 3. PostProcess Volume (Fix Auto-Exposure)
    pp_actor = None
    for actor in subsystem.get_all_level_actors():
        if actor and isinstance(actor, unreal.PostProcessVolume):
            pp_actor = actor
            break

    if not pp_actor:
        pp_actor = subsystem.spawn_actor_from_class(
            unreal.PostProcessVolume, 
            unreal.Vector(0, 0, 0), 
            unreal.Rotator(0, 0, 0)
        )
        pp_actor.set_actor_label("TennisCourt_PostProcess")
        pp_actor.set_folder_path(unreal.Name(LIGHT_FOLDER_PATH))

    pp_actor.set_editor_property("unbound", True)
    pp_settings = pp_actor.settings
    
    # Force Fixed Brightness Exposure
    pp_settings.set_editor_property("override_auto_exposure_method", True)
    pp_settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp_settings.set_editor_property("override_auto_exposure_bias", True)
    pp_settings.set_editor_property("auto_exposure_bias", 10.0)

    unreal.log("[lighting] Fixed Daylight and Auto-Exposure Applied.")