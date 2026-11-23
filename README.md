# TennisRobotSim — Procedural Tennis Court Simulation Environment

![Unreal Engine](https://img.shields.io/badge/Unreal_Engine-5.5-0E1128?logo=unrealengine&logoColor=white)
![Python](https://img.shields.io/badge/Python-Editor_Scripting-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Court Standard](https://img.shields.io/badge/Dimensions-ITF_Standard-1B7A43)

A fully procedural tennis court and robot environment for Unreal Engine 5.5, built entirely through the Python Editor Scripting API — no C++, no hand-placed actors. The entire scene (court surface, lines, net, lighting, robot, opponent player, and camera) is generated from a single validated source of ITF dimensions, so any run reproduces the same geometry exactly.

**Course:** Robotics — School of Electrical and Computer Engineering, University of Tehran

## Why This Project

Building robot simulation environments by hand in the Unreal Editor does not scale: every change must be repeated manually, dimensions drift from reality, and results cannot be reproduced. This project treats the level itself as generated code:

- The court is dimensioned from the official ITF rules (Appendix II), loaded from a single JSON file and converted to centimeters (1 Unreal Unit = 1 cm).
- Every builder phase derives its numbers from that shared configuration — no hardcoded coordinates anywhere outside `Core/`.
- Re-running the build is safe: each phase destroys and rebuilds only its own tagged actors (idempotency).
- Validation is numeric, not just visual: phases assert positions, sizes, and consistency at runtime.

The end goal is a digital-twin foundation for a ball-collecting robot: a perception camera, physics-based tennis balls, and a ROS 2 bridge. The current milestone is the complete, reproducible scene; perception and dynamics are documented under [Roadmap](#roadmap).

## Technical Architecture

The Python side is split so that pure math is testable outside the editor and only the builders touch the `unreal` API:

```
Data/court_dimensions.json      Single source of raw ITF numbers (feet/inches)
        │
        ▼
Python/Core/                    Pure Python, no unreal imports
  units.py                      Unit conversion (ft/in → cm, cm → ft)
  court_config.py               Loads JSON, converts to cm, derives values,
                                cross-validates, exposes a cached singleton
  coordinate_system.py          Encodes the world-space convention and turns
                                dimensions into concrete 3D points/lines
        │
        ▼
Python/Court/                   Editor-side builders (import unreal)
  surface_builder.py, lines_builder.py, net_builder.py, material_builder.py,
  collision_builder.py, optimization_builder.py, environment_builder.py,
  robot_builder.py, player_spawner.py
        │
        ▼
Python/Tools/                   Executable phase scripts + verification
Python/Sensors/                 Robot camera (CineCamera attachment)
```

**Coordinate convention** (encoded once in `coordinate_system.py`):

| Component | Definition |
|---|---|
| Unit | 1 Unreal Unit = 1 centimeter |
| Origin (0, 0, 0) | Geometric center of the court, at ground level (net center strap) |
| +X | Toward the far baseline |
| +Y | Toward the right doubles sideline |
| +Z | Up (Unreal standard) |

## Court Geometry (ITF Standard)

Raw values are stored once in `Data/court_dimensions.json`; `court_config.py` converts them and self-validates three independent geometric identities (e.g. `singles width + 2 × inset == doubles width`) before any builder runs.

| Parameter | Value |
|---|---|
| Court length | 2377.44 cm (78 ft) |
| Doubles width | 1097.28 cm (36 ft) |
| Singles width | 822.96 cm (27 ft) |
| Service line distance from net | 640.08 cm (21 ft) |
| Net height (center / posts) | 91.44 / 106.68 cm |
| Line width (standard / baseline) | 5.08 / 10.16 cm |
| Full pad (court + run-off area) | 3657.6 × 1828.8 cm |

## Build Pipeline

`run_all_phases.py` executes the whole chain in order and stops on the first failure with a traceback. Each phase is also runnable individually.

| Phase | Module | What it produces |
|---|---|---|
| 1 | `validate_phase1_config.py` | Config validation report + viewport debug markers |
| 2 | `build_phase2_surface.py` | Two-tone surface: green outer pad, blue infield (offset 0.5 mm to prevent Z-fighting) |
| 3 | `build_phase3_lines.py` | All 12 official line actors (baselines, service lines, sidelines, center service lines, center marks), raised 1 mm above the surface |
| 4 | `build_phase4_net.py` | Net assembly: 2 posts, a parametric string grid (161 vertical + 11 horizontal strands = 172 members, 1 cm thick at 8 cm spacing), white band, center strap |
| 5 | `build_phase5_materials.py` | PBR materials across court, net, and environment (US Open blue/green scheme, steel posts, dark net mesh) |
| 6–7 | `environment_builder.py` | 3 m perimeter fence, sponsor boards, umpire chair, benches, 4 floodlight towers — implemented but **not yet wired into `run_all_phases.py`** |
| 8 | `build_phase8_collision.py` | `BlockAll` collision + query/physics on court actors; verifies court center at (0, 0, 0) |
| 9 | `build_phase9_polish.py` | Static mobility for all court actors, Outliner organization, shadow settings |
| 10 | `build_phase10_robot.py` | Ball-collector robot: chassis (100×70×20 cm), 4 wheels, ball storage basket, front collection roller, camera mount — spawned in the backcourt on its side of the court |
| 11 | `build_phase11_vision_setup.py` | Opponent player imported from `realistic_male_character.glb` (7-part scene graph parsed, normalized to 180 cm, placed facing the robot), real-scale racket from `tennis_racquet.glb` (68 cm), and a CineCamera on the robot mount (30 cm forward, 60 cm up, 5° downward pitch) |

### Engineering Notes

A few problems shaped the implementation:

- **Idempotency** — re-running phases originally duplicated actors; every builder now purges its own previously tagged actors first.
- **Editor module caching** — `run_all_phases.py` purges cached project modules from `sys.modules`, so code edits apply without restarting the editor.
- **Unreal console imports** — modules are loaded by file path via `importlib.util`, which works both from the Output Log Python tab and the Cmd tab.
- **GLB import** — the character model has a 7-node hierarchy with a misaligned origin; the spawner parses the glTF scene graph and rebuilds node transforms (metric → cm, Y-up → Z-up) instead of hand-adjusting.
- **Pose baking** — `dump_racket_pose.py` captures a manually arranged racket pose from the viewport and bakes it into `player_spawner.py` as relative constants, making hand-tuned placement reproducible.

## Current Status

**Working:**

- Full scene rebuildable from one command, with numeric validation at multiple phases
- Complete visual composition: court, lines, parametric net, materials, robot, opponent player with racket, robot camera

**Not yet implemented** (documented honestly, not claimed):

- Tennis ball with physics (diameter 6.7 cm, mass 57 g, restitution ≈ 0.7)
- Robot motion — the robot is currently a static assembly with no drive logic
- Camera frame capture (`SceneCaptureComponent2D` → PNG) — the camera is visual-only for now
- ROS 2 bridge and YOLO perception dataset/training
- Saving the scene as the official project map (generated actors currently live in the open working level)

## Roadmap

1. **Project stabilization** — save `TennisCourt_Main.umap`, set it as `GameDefaultMap`, integrate the environment builder as phase 6
2. **Ball physics** — sphere with proper mass/restitution, drop-test verification, configurable ball launcher
3. **Robot mobility** — controllable Pawn with differential-drive movement, odometry, virtual IMU
4. **Perception dataset** — frame capture with automatic pseudo-labeling by projecting 3D ball/player positions into image space, randomized scenes, YOLO training/evaluation
5. **ROS 2 bridge** — camera topic (`/camera/image_raw`), odometry, `cmd_vel` control, closed-loop test
6. **Collection behavior** — YOLO-based ball detection, navigation to balls, roller actuation, performance logging

## Getting Started

### Requirements

- Unreal Engine 5.5 (developed on 5.5.4), Windows
- Python Editor Script Plugin enabled (built into the engine; the `.uproject` opens with it available)

### Running the Build

1. Open `TennisRobotSim.uproject`.
2. In the Output Log, switch to the **Cmd** tab and run:

   ```
   py "<path-to-project>/Python/Tools/run_all_phases.py"
   ```

   Or use **Tools → Execute Python Script** and select `run_all_phases.py`.
3. Watch the log: each phase prints its own verification report; the chain stops at the first failed assertion.

Re-running is safe — every phase rebuilds its own output from scratch.

## Repository Structure

```
TennisRobotSim 5.5/
├── TennisRobotSim.uproject        Project descriptor (UE 5.5)
├── realistic_male_character.glb   Opponent player model (imported by phase 11)
├── tennis_racquet.glb             Racket model (imported by phase 11)
├── Config/                        Engine and game settings
├── Content/                       UE assets and generated levels
│   ├── Maps/                      Level assets
│   ├── Robot/, TennisProps/, Characters/, Environment/   Scene assets
│   └── ...
├── Data/
│   └── court_dimensions.json      Single source of ITF court numbers
├── Python/
│   ├── Core/                      Pure config + math (no unreal imports)
│   ├── Court/                     Editor-side procedural builders
│   ├── Sensors/                   Robot camera setup
│   └── Tools/                     Executable phase scripts and utilities
└── Python_old/                    Legacy scripts kept for reference (superseded by Python/)
```

## Attribution

- Court dimensions from the **ITF Rules of Tennis, Appendix II** (see `Data/court_dimensions.json`).
- Built on **Unreal Engine 5.5** with the Python Editor Scripting API; primitive geometry uses engine basic shapes (`/Engine/BasicShapes`).
- Opponent player and racket models are third-party glTF assets imported at build time; their placement and pose-baking tooling are original to this project.

All procedural generation, validation, and tooling in `Python/` is original work for this project.
