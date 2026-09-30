"""
Master Builder: Calls all court scripts in precise sequence.
"""
import unreal
from Court.surface_builder import build_court_surface
from Court.lines_builder import build_court_lines
from Court.net_builder import build_net_and_posts
from Court.environment_builder import build_court_environment
from Court.material_builder import apply_court_materials
from Court.lighting_and_camera import setup_guaranteed_daylight

def build_tennis_court():
    unreal.log("=== Starting Full Tennis Court Assembly ===")
    
    # 1. Build Geometry
    build_court_surface()
    build_court_lines()
    build_net_and_posts()
    build_court_environment()
    
    # 2. Apply Materials
    apply_court_materials()
    
    # 3. Apply Lighting
    setup_guaranteed_daylight()
    
    unreal.log("=== Tennis Court Assembly Completed Successfully! ===")

if __name__ == "__main__":
    build_tennis_court()