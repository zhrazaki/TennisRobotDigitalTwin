"""
Purpose:     Phase 11 (Realistic Human Target) - Spawns a human opponent at the
             far END of the court facing the robot, with a clean primitive-built
             tennis racket in the right hand.
             Tries Engine Manny meshes first; falls back to a primitive body so
             the player is NEVER invisible.
Dependencies: unreal, Core.court_config
"""

import math
import unreal
from Core import court_config

# Racket offset if hand-socket attach is unavailable (player-local cm/deg).
RACKET_REL_LOC = unreal.Vector(12.0, -32.0, 88.0)
RACKET_REL_ROT = unreal.Rotator(0.0, 0.0, 0.0)
# GLB prop orientation: the mesh lies flat (long axis ~Y). Roll it upright,
# head up. Tune from screenshot if the handle points the wrong way.
RACKET_MESH_ROT_PITCH = 0.0
RACKET_MESH_ROT_YAW = 0.0
RACKET_MESH_ROT_ROLL = -90.0


def _mesh_rot():
    r = unreal.Rotator(0.0, 0.0, 0.0)
    r.pitch = RACKET_MESH_ROT_PITCH
    r.yaw = RACKET_MESH_ROT_YAW
    r.roll = RACKET_MESH_ROT_ROLL
    return r
HAND_SOCKET_NAME = "hand_r"
# Robot world position (X, Y) — player yaw is computed to face it.
ROBOT_X = -1000.0
ROBOT_Y = 0.0


def _yaw_rot(yaw_deg):
    """Build yaw-only rotation via attribute assignment (avoids any
    Rotator() positional-arg order ambiguity + kills phantom roll)."""
    r = unreal.Rotator(0.0, 0.0, 0.0)
    r.pitch = 0.0
    r.yaw = float(yaw_deg)
    r.roll = 0.0
    return r

# Known Manny locations across UE5 versions / templates (first hit wins).
MESH_CANDIDATES = [
    "/Game/Characters/Mannequins/Meshes/SKM_Manny",
    "/Game/Characters/Mannequins/Meshes/SKM_Quinn",
    "/Engine/EngineMeshes/SkeletalMesh/SK_Mannequin_Female",
    "/Engine/EngineMeshes/SkeletalMesh/SK_Mannequin",
    "/Engine/Tutorial/Subtitles/Mannequin",
]


def _actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _paint(comp, color, roughness=0.6, metallic=0.0):
    base_mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    if base_mat and comp:
        dyn = comp.create_dynamic_material_instance(0, base_mat)
        if dyn:
            dyn.set_vector_parameter_value("Color", color)
            dyn.set_scalar_parameter_value("Roughness", roughness)
            dyn.set_scalar_parameter_value("Metallic", metallic)


CHARACTER_DISK_CANDIDATES = [
    "F:/unreal project/TennisRobotSim/TennisRobotSim 5.5/realistic_male_character.glb",
    "F:/unreal project/TennisRobotSim/TennisRobotSim/realistic_male_character.glb",
]
CHARACTER_IMPORT_PATH = "/Game/Characters/Imported"
CHARACTER_TARGET_HEIGHT_CM = 180.0
# Extra yaw if the model doesn't face +X like Manny (tune from screenshot).
CHARACTER_YAW_OFFSET = 0.0


def _try_load_mesh():
    for path in MESH_CANDIDATES:
        m = unreal.EditorAssetLibrary.load_asset(path)
        if m:
            print("[player_spawner] Using skeletal mesh: %s" % path)
            return (m, path)
    print("[player_spawner] WARNING: no Manny mesh found, using primitive body.")
    return (None, None)


def _apply_idle_animation(sk_comp, mesh_path):
    """Put the Manny AnimBlueprint on so the player idles naturally instead
    of staring in a stiff reference pose. Searches /Game (pack layout
    varies) instead of guessing one path. Best-effort: logs and skips."""
    try:
        want = "ABP_Quinn" if mesh_path and "Quinn" in mesh_path else "ABP_Manny"
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        flt = unreal.ARFilter(class_names=["AnimBlueprint"],
                              package_paths=["/Game"],
                              recursive_paths=True)
        found = {}
        for a in reg.get_assets(flt):
            n = str(a.asset_name)
            if n in ("ABP_Manny", "ABP_Quinn"):
                found[n] = str(a.package_name)
        pkg = found.get(want) or (sorted(found.values())[0] if found else None)
        if not pkg:
            print("[player_spawner] No ABP_Manny/ABP_Quinn anywhere under /Game.")
            return False
        abp = unreal.EditorAssetLibrary.load_asset(pkg)
        sk_comp.set_editor_property("animation_mode",
                                    unreal.AnimationMode.ANIMATION_BLUEPRINT)
        gc = getattr(abp, "generated_class", None)
        sk_comp.set_editor_property("anim_class", gc() if callable(gc) else gc)
        print("[player_spawner] Idle animation: %s" % pkg)
        return True
    except Exception as e:
        print("[player_spawner] Idle animation skipped (%s)" % e)
    return False


def _find_character_assets():
    """Find imported realistic-character meshes (skeletal preferred).
    Returns (skeletal_pkgs, static_pkgs)."""
    skel, stat = [], []
    try:
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        for class_name, bucket in (("SkeletalMesh", skel), ("StaticMesh", stat)):
            flt = unreal.ARFilter(class_names=[class_name],
                                  package_paths=["/Game"],
                                  recursive_paths=True)
            for a in reg.get_assets(flt):
                pkg = str(a.package_name)
                n = str(a.asset_name).lower()
                if ("manny" in n or "quinn" in n or "mannequin" in n):
                    continue
                if pkg.startswith(CHARACTER_IMPORT_PATH + "/") or any(
                        k in n for k in ("realistic", "male_character", "malecharacter", "male")):
                    bucket.append(pkg)
    except Exception as e:
        print("[character] search failed (%s)" % e)
    return skel, stat


def _import_character_glb():
    """One-click import of the dropped realistic_male_character.glb."""
    import os
    src = next((p for p in CHARACTER_DISK_CANDIDATES if os.path.isfile(p)), None)
    if not src:
        print("[character] realistic_male_character.glb not found next to the .uproject.")
        return
    try:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        task = unreal.AssetImportTask()
        task.filename = src
        task.destination_path = CHARACTER_IMPORT_PATH
        task.replace_existing = True
        task.automated = True
        task.save = True
        tools.import_asset_tasks([task])
        print("[character] imported %s -> %s" % (src, CHARACTER_IMPORT_PATH))
    except Exception as e:
        print("[character] auto-import failed (%s)." % e)
        print("[character] Fallback: drag the .glb into the Content Browser manually.")


def _mesh_z_height(mesh):
    """Z height of one mesh part (0.0 if unreadable). Assembly scale is
    computed ONCE from the tallest part and applied to ALL parts equally."""
    try:
        ext = mesh.get_bounds().box_extent
    except Exception:
        try:
            _o, ext = mesh.get_bounds()
        except Exception as e:
            print("[character] bounds failed (%s)" % e)
            return 0.0
    try:
        return float(ext.z) * 2.0
    except Exception:
        return 0.0


def _read_glb_nodes(glb_path):
    import struct, json, math
    try:
        with open(glb_path, "rb") as f:
            data = f.read()
        if len(data) < 20 or struct.unpack("<I", data[0:4])[0] != 0x46546C67:
            return {}, 0
        clen = struct.unpack("<I", data[12:16])[0]
        js = json.loads(data[20:20 + clen].decode("utf-8", errors="replace"))
    except Exception as e:
        print("[character] GLB parse failed (%s)" % e)
        return {}, 0
    nodes = js.get("nodes", [])
    if not nodes:
        return {}, 0

    def _compose(t, q, s):
        l = math.sqrt(sum(v * v for v in q)) or 1.0
        x, y, z, w = [v / l for v in q]
        xx, yy, zz = x * x, y * y, z * z
        xy, xz, yz = x * y, x * z, y * z
        wx, wy, wz = w * x, w * y, w * z
        sx, sy, sz = s
        return [
            [(1 - 2 * (yy + zz)) * sx, 2 * (xy - wz) * sy, 2 * (xz + wy) * sz, t[0]],
            [2 * (xy + wz) * sx, (1 - 2 * (xx + zz)) * sy, 2 * (yz - wx) * sz, t[1]],
            [2 * (xz - wy) * sx, 2 * (yz + wx) * sy, (1 - 2 * (xx + yy)) * sz, t[2]],
            [0, 0, 0, 1]]

    def _mul(a, b):
        return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

    local = []
    for n in nodes:
        if "matrix" in n:
            m = n["matrix"]
            local.append([[m[j * 4 + i] for j in range(4)] for i in range(4)])
        else:
            local.append(_compose(n.get("translation", [0, 0, 0]),
                                  n.get("rotation", [0, 0, 0, 1]),
                                  n.get("scale", [1, 1, 1])))
    has_parent = set()
    for n in nodes:
        for c in n.get("children", []):
            has_parent.add(c)
    roots = []
    for sc in js.get("scenes", [{}]):
        roots += sc.get("nodes", [])
    if not roots:
        roots = [i for i in range(len(nodes)) if i not in has_parent]
    glob = {}
    rotated = 0
    ident = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    stack = [(r, ident) for r in roots if 0 <= r < len(nodes)]
    while stack:
        idx, pm = stack.pop()
        g = _mul(pm, local[idx])
        n = nodes[idx]
        if "name" in n and n["name"]:
            k = _norm_key(n["name"])
            if k and k not in glob:
                glob[k] = (g[0][3], g[1][3], g[2][3])
        q = n.get("rotation", [0, 0, 0, 1])
        if abs(abs(q[3]) - 1.0) > 0.001:
            rotated += 1
        for c in n.get("children", []):
            if 0 <= c < len(nodes):
                stack.append((c, g))
    return glob, rotated


def _norm_key(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def _match_node(asset_name, node_map):
    key = _norm_key(asset_name)
    if key in node_map:
        return node_map[key]
    for k, v in node_map.items():
        if key and k and (key in k or k in key):
            return v
    return None


def _build_fallback_body(subsystem):
    """Simple ~175cm figure so the player is always visible. Returns group."""
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    cyl = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
    sph = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
    skin = unreal.LinearColor(0.85, 0.65, 0.50, 1.0)
    shirt = unreal.LinearColor(0.80, 0.10, 0.10, 1.0)
    pants = unreal.LinearColor(0.05, 0.05, 0.08, 1.0)

    group = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    group.set_actor_label("OpponentPlayer_Body")
    group.tags = ["OpponentPlayer", "YOLOTarget", "Person"]
    group.set_folder_path("TennisCourt/Opponent")

    def _p(name, mesh, loc, scale, color):
        a = subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, 0))
        a.set_actor_label(name)
        a.set_folder_path("TennisCourt/Opponent")
        a.set_editor_property("tags", [unreal.Name("OpponentPlayer"), unreal.Name("YOLOTarget")])
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        c.set_collision_profile_name("NoCollision")
        _paint(c, color, roughness=0.8)
        a.set_actor_scale3d(scale)
        a.attach_to_actor(group, unreal.Name(),
                          unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
        return a

    _p("OpponentPlayer_Body_Torso", cyl, unreal.Vector(0, 0, 105),
       unreal.Vector(0.28, 0.28, 0.60), shirt)
    _p("OpponentPlayer_Body_Head", sph, unreal.Vector(0, 0, 162),
       unreal.Vector(0.24, 0.24, 0.24), skin)
    _p("OpponentPlayer_Body_LegL", cyl, unreal.Vector(0, 10, 40),
       unreal.Vector(0.14, 0.14, 0.80), pants)
    _p("OpponentPlayer_Body_LegR", cyl, unreal.Vector(0, -10, 40),
       unreal.Vector(0.14, 0.14, 0.80), pants)
    _p("OpponentPlayer_Body_ArmL", cyl, unreal.Vector(0, 24, 105),
       unreal.Vector(0.10, 0.10, 0.60), skin)
    # Right arm raised toward racket side
    _p("OpponentPlayer_Body_ArmR", cyl, unreal.Vector(10, -24, 120),
       unreal.Vector(0.10, 0.10, 0.55), skin)
    return group


RACKET_DISK_CANDIDATES = [
    "F:/unreal project/TennisRobotSim/TennisRobotSim 5.5/tennis_racquet.glb",
    "F:/unreal project/TennisRobotSim/TennisRobotSim/tennis_racquet.glb",
]
RACKET_IMPORT_PATH = "/Game/TennisProps"
RACKET_TARGET_LONGEST_CM = 68.0  # real racket length; GLB auto-scaled to this
# Manual override (0.0 = auto). If the racket is still wrong-sized, read the
# "[racket] using ..." log line and set this = 68 / reported_world_size.
RACKET_MANUAL_SCALE = 0.0
# Snap target = hand bone + this player-local offset (fwd, right/out, up).
# Outward pushes the butt clear of the torso so the racket never clips it.
RACKET_HAND_OFFSET = (16.0, -8.0, -8.0)
# Baked manual pose (from dump_racket_pose.py, player-LOCAL frame).
# The user arranged both meshes by hand; these numbers reproduce that exact
# pose on every rebuild. Verified: rel yaw = 27.63-180, rel loc = -R(180)*d.
RACKET_BAKED = True
RACKET_BAKED_REL_LOC = (16.57, 72.74, 118.22)
RACKET_BAKED_PITCH = -12.95
RACKET_BAKED_REL_YAW = -152.37
RACKET_BAKED_ROLL = -145.87
RACKET_BAKED_SCALE = 0.0592
# Lean of the top so the frame clears the body while the butt stays in the
# palm: ROLL swings it outward (world X), PITCH brings it forward toward
# the net (world Y, negative = forward).
RACKET_LEAN_ROLL = -25.0
RACKET_LEAN_PITCH = -15.0


def _find_racket_meshes():
    """Find real racket meshes: name match anywhere, else anything mesh-like
    inside our GLB import folder (Interchange names them Object_2...)."""
    named, folder = [], []
    try:
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        flt = unreal.ARFilter(class_names=["StaticMesh"],
                              package_paths=["/Game"],
                              recursive_paths=True)
        for a in reg.get_assets(flt):
            pkg = str(a.package_name)
            n = str(a.asset_name).lower()
            if "racquet" in n or "racket" in n:
                named.append(pkg)
            elif pkg.startswith(RACKET_IMPORT_PATH + "/"):
                folder.append(pkg)
    except Exception as e:
        print("[racket] search failed (%s)" % e)
    return named or sorted(set(folder))


def _import_racket_glb():
    """One-click import of the dropped tennis_racquet.glb. Returns package."""
    import os
    src = next((p for p in RACKET_DISK_CANDIDATES if os.path.isfile(p)), None)
    if not src:
        print("[racket] tennis_racquet.glb not found next to the .uproject.")
        return None
    try:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        task = unreal.AssetImportTask()
        task.filename = src
        task.destination_path = RACKET_IMPORT_PATH
        task.replace_existing = True
        task.automated = True
        task.save = True
        tools.import_asset_tasks([task])
        print("[racket] imported %s -> %s" % (src, RACKET_IMPORT_PATH))
    except Exception as e:
        print("[racket] auto-import failed (%s)." % e)
        print("[racket] Fallback: drag tennis_racquet.glb into the Content Browser manually (enable the glTF importer plugin if asked).")
    return _find_imported_racket()


def _mount_baked(parent, subsystem, pkgs, player_loc, yaw_deg):
    """Reproduce the hand-arranged pose (no reads, no attach, no drift)."""
    yr = math.radians(float(yaw_deg))
    c, s = math.cos(yr), math.sin(yr)
    rx, ry, rz = RACKET_BAKED_REL_LOC
    wloc = unreal.Vector(float(player_loc.x) + rx * c - ry * s,
                         float(player_loc.y) + rx * s + ry * c,
                         float(player_loc.z) + rz)
    wrot = unreal.Rotator(0.0, 0.0, 0.0)
    wrot.pitch = float(RACKET_BAKED_PITCH)
    wrot.yaw = float(yaw_deg) + float(RACKET_BAKED_REL_YAW)
    wrot.roll = float(RACKET_BAKED_ROLL)
    sc = float(RACKET_BAKED_SCALE)
    parent.set_actor_location(wloc, False, True)
    parent.set_actor_rotation(wrot, True)
    kids = []
    for pkg in pkgs:
        m = unreal.EditorAssetLibrary.load_asset(pkg)
        if not m:
            continue
        child = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, wloc, wrot)
        child.set_actor_label("OpponentPlayer_Racket_" + pkg.rsplit("/", 1)[-1])
        child.set_folder_path("TennisCourt/Opponent/Racket")
        child.set_editor_property("tags", [unreal.Name("OpponentPlayer"), unreal.Name("Racket")])
        cc = child.static_mesh_component
        cc.set_static_mesh(m)
        cc.set_collision_profile_name("NoCollision")
        cc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        child.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        kids.append(child)
    print("[racket] BAKED pose at (%.2f, %.2f, %.2f) x%.4f" % (wloc.x, wloc.y, wloc.z, sc))
    return kids


def _mount_real_racket(parent, subsystem, expected, baked_anchor=None):
    """Place the real GLB meshes DIRECTLY at world spots (no attach calls:
    they silently fail in this editor build, stranding parts at origin).
    Parent + every mesh part go to `expected` with upright rotation and a
    deterministic per-part scale. Returns child list (empty = primitive)."""
    pkgs = _find_racket_meshes()
    if not pkgs:
        _import_racket_glb()
        pkgs = _find_racket_meshes()
    if not pkgs:
        return []
    if RACKET_BAKED and baked_anchor is not None:
        _ploc, _pyaw = baked_anchor
        return _mount_baked(parent, subsystem, pkgs, _ploc, _pyaw)
    meshes = []
    longest = 0.0
    for pkg in pkgs:
        m = unreal.EditorAssetLibrary.load_asset(pkg)
        if not m:
            print("[racket] found %s but load failed." % pkg)
            continue
        meshes.append((pkg, m))
        ext = None
        try:
            ext = m.get_bounds().box_extent
        except Exception:
            try:
                _o, ext = m.get_bounds()
            except Exception as e:
                print("[racket] bounds failed for %s (%s)" % (pkg, e))
        if ext is not None:
            try:
                longest = max(longest, float(ext.x), float(ext.y), float(ext.z))
            except Exception:
                pass
    if not meshes:
        return []
    longest *= 2.0
    if RACKET_MANUAL_SCALE > 0.0:
        s = float(RACKET_MANUAL_SCALE)
        print("[racket] MANUAL scale x%.4f" % s)
    elif longest > 0.01:
        s = RACKET_TARGET_LONGEST_CM / longest
    else:
        s = 1.0
        print("[racket] bounds unknown, scale 1.0")
    mrot = _mesh_rot()
    parent.set_actor_location(expected, False, True)
    parent.set_actor_rotation(mrot, True)
    parent.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    kids = []
    for pkg, m in meshes:
        child = subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor, expected, mrot)
        child.set_actor_label("OpponentPlayer_Racket_" + pkg.rsplit("/", 1)[-1])
        child.set_folder_path("TennisCourt/Opponent/Racket")
        child.set_editor_property("tags", [unreal.Name("OpponentPlayer"), unreal.Name("Racket")])
        cc = child.static_mesh_component
        cc.set_static_mesh(m)
        cc.set_collision_profile_name("NoCollision")
        cc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        child.set_actor_scale3d(unreal.Vector(s, s, s))
        kids.append(child)
    print("[racket] using %d mesh(es) x%.4f (import longest=%.2f) at (%.1f, %.1f, %.1f)" % (
        len(meshes), s, longest, expected.x, expected.y, expected.z))
    return kids


def _build_racket(subsystem, player_actor, expected_racket=None, baked_anchor=None):
    """~68cm racket: grip + throat + smooth 16-seg oval ring + string bed.
    Attached actor-relative (upright, beside the right hand). Actor-attach
    is used instead of the hand bone socket on purpose: the player is
    static, and the bone's unknown orientation can bury the racket in
    the torso where it looks 'missing'."""
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    cyl = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
    if not cube or not cyl:
        print("[player_spawner] WARNING: basic meshes missing, racket skipped.")
        return None

    parent = subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    parent.set_actor_label("OpponentPlayer_Racket")
    parent.tags = ["OpponentPlayer", "Racket"]
    parent.set_folder_path("TennisCourt/Opponent/Racket")
    # MOVABLE: the engine aborts attaching a static component to the
    # (movable) skeletal mesh, leaving the racket behind at the origin.
    if parent.static_mesh_component:
        parent.static_mesh_component.set_editor_property(
            "mobility", unreal.ComponentMobility.MOVABLE)

    # Real GLB racket wins when available; primitive fallback below.
    kids = _mount_real_racket(parent, subsystem, expected_racket, baked_anchor)
    if kids:
        if not RACKET_BAKED:
            _normalize_racket_size(kids)
        print("[player_spawner] Racket built (real GLB mesh).")
        return (parent, kids)

    frame = unreal.LinearColor(0.55, 0.05, 0.05, 1.0)   # dark red frame
    strings = unreal.LinearColor(0.90, 0.90, 0.88, 1.0)
    grip = unreal.LinearColor(0.02, 0.02, 0.02, 1.0)

    made = []

    def _part(name, mesh, loc, scale, color, rot=None, rough=0.5):
        a = subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor, loc, rot or unreal.Rotator(0, 0, 0))
        a.set_actor_label(name)
        a.set_folder_path("TennisCourt/Opponent/Racket")
        a.set_editor_property("tags", [unreal.Name("OpponentPlayer"), unreal.Name("Racket")])
        comp = a.static_mesh_component
        comp.set_static_mesh(mesh)
        comp.set_collision_profile_name("NoCollision")
        comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        _paint(comp, color, roughness=rough)
        a.set_actor_scale3d(scale)
        a.attach_to_actor(parent, unreal.Name(),
                          unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
        made.append(a)
        return a

    # Grip + butt + throat (racket +Z = up, origin at butt)
    _part("OpponentPlayer_Racket_Handle", cyl, unreal.Vector(0, 0, 13.5),
          unreal.Vector(0.045, 0.045, 0.27), grip, rough=0.9)
    _part("OpponentPlayer_Racket_Throat", cube, unreal.Vector(0, 0, 31.0),
          unreal.Vector(0.025, 0.07, 0.10), frame, rough=0.35)

    # Oval ring head: 16 tangent-oriented segments (roll about X = Y-Z plane)
    ry, rz, cz = 13.5, 16.0, 52.0
    for i in range(16):
        t = math.radians(i * 22.5)
        y = ry * math.cos(t)
        z = cz + rz * math.sin(t)
        roll = math.degrees(math.atan2(ry * math.sin(t), rz * math.cos(t)))
        _part(f"OpponentPlayer_Racket_Frame_{i:02d}", cube,
              unreal.Vector(0, y, z),
              unreal.Vector(0.022, 0.030, 0.062), frame,
              rot=unreal.Rotator(0.0, 0.0, roll), rough=0.35)

    # String bed: verticals + horizontals clipped to ellipse
    for i, y in enumerate([float(v) for v in range(-12, 13, 3)]):
        if abs(y) >= ry:
            continue
        half = rz * math.sqrt(max(0.0, 1.0 - (y / ry) ** 2))
        _part(f"OpponentPlayer_Racket_StrV_{i}", cube,
              unreal.Vector(0, y, cz),
              unreal.Vector(0.005, 0.005, (half * 2.0) / 100.0), strings, rough=0.6)
    for j, dz in enumerate([float(v) for v in range(-15, 16, 3)]):
        if abs(dz) >= rz:
            continue
        w = ry * math.sqrt(max(0.0, 1.0 - (dz / rz) ** 2))
        _part(f"OpponentPlayer_Racket_StrH_{j}", cube,
              unreal.Vector(0, 0, cz + dz),
              unreal.Vector(0.005, (w * 2.0) / 100.0, 0.005), strings, rough=0.6)

    print("[player_spawner] Racket built (grip + ring + string bed).")
    _attach_racket_parent(subsystem, parent, player_actor, expected_racket)
    return (parent, made)


def _attach_racket_parent(subsystem, parent, player_actor, expected=None, rel_rot=None):
    """Attach holder next to the right hand + verify placement.
    `expected` (world) is preferred: reads taken right after spawning a
    skeletal actor can lag a tick behind, while the preset math is exact."""
    if rel_rot is None:
        rel_rot = RACKET_REL_ROT
    # Attach (movable->movable so the engine does not abort), then verify.
    # teleport=True: editor moves must stick even with collision around.
    parent.attach_to_actor(player_actor, unreal.Name(),
                           unreal.AttachmentRule.KEEP_WORLD,
                           unreal.AttachmentRule.KEEP_WORLD,
                           unreal.AttachmentRule.KEEP_WORLD, False)
    parent.set_actor_relative_location(RACKET_REL_LOC, False, True)
    parent.set_actor_relative_rotation(rel_rot, False, True)
    if expected is None:
        # Fallback reference from live transform (may lag after spawn).
        prot = player_actor.get_actor_rotation()
        ploc = player_actor.get_actor_location()
        yr = math.radians(prot.yaw)
        c, s = math.cos(yr), math.sin(yr)
        rx, ry = RACKET_REL_LOC.x, RACKET_REL_LOC.y
        expected = unreal.Vector(ploc.x + rx * c - ry * s,
                                 ploc.y + rx * s + ry * c,
                                 ploc.z + RACKET_REL_LOC.z)
    wloc = parent.get_actor_location()
    print("[player_spawner] racket loc=(%.1f, %.1f, %.1f) expected=(%.1f, %.1f, %.1f)" % (
        wloc.x, wloc.y, wloc.z, expected.x, expected.y, expected.z))
    if wloc.distance(expected) > 1.0:
        # Attach silently failed: teleport parent (children ride along).
        parent.set_actor_location(expected, False, True)
        wloc = parent.get_actor_location()
        print("[player_spawner] racket corrected to (%.1f, %.1f, %.1f)" % (
            wloc.x, wloc.y, wloc.z))


def _normalize_racket_size(kids):
    """Closed-loop on the freestanding parts: measure world size, rescale
    parts until longest == 68cm. Log-only if the bounds API is unavailable."""
    try:
        for _i in range(3):
            res = unreal.GameplayStatics.get_actor_array_bounds(kids, False)
            _e = res[1]
            wlong = max(float(_e.x), float(_e.y), float(_e.z)) * 2.0
            if wlong < 0.01:
                print("[racket] world bounds unknown, keeping scale.")
                return
            if abs(wlong - RACKET_TARGET_LONGEST_CM) / RACKET_TARGET_LONGEST_CM < 0.05:
                print("[racket] world size OK: %.1fcm." % wlong)
                return
            f = RACKET_TARGET_LONGEST_CM / wlong
            for k in kids:
                cur = k.get_actor_scale3d()
                k.set_actor_scale3d(unreal.Vector(cur.x * f, cur.y * f, cur.z * f))
        print("[racket] size normalize done, final longest=%.1fcm." % wlong)
    except Exception as e:
        print("[racket] size normalize skipped (%s)" % e)


def _snap_butt_to_hand(parent, parts, sk_comp, yaw_deg=None):
    """Put the racket BUTT exactly on the right-hand bone."""
    if sk_comp is None:
        return
    try:
        hand = sk_comp.get_socket_location("hand_r")
    except Exception as e:
        print("[racket] hand socket read failed (%s)" % e)
        return
    try:
        res = unreal.GameplayStatics.get_actor_array_bounds(parts, False)
        _o, _e = res[0], res[1]
    except Exception as e:
        print("[racket] butt measure failed (%s)" % e)
        return
    hx, hy, hz = float(hand.x), float(hand.y), float(hand.z)
    bx, by = float(_o.x), float(_o.y)
    bz = float(_o.z) - float(_e.z)
    # Target = hand bone + outward offset (player-local) so the handle sits
    # in the palm with the frame clear of the torso.
    fx, fy, fz = RACKET_HAND_OFFSET
    if yaw_deg is not None:
        _yr = math.radians(float(yaw_deg))
        _c, _s = math.cos(_yr), math.sin(_yr)
        ox, oy = fx * _c - fy * _s, fx * _s + fy * _c
    else:
        ox, oy = fx, fy
    tx, ty, tz = hx + ox, hy + oy, hz + fz
    print("[racket] hand=(%.1f, %.1f, %.1f) butt=(%.1f, %.1f, %.1f) target=(%.1f, %.1f, %.1f)" % (
        hx, hy, hz, bx, by, bz, tx, ty, tz))
    dx, dy, dz = tx - bx, ty - by, tz - bz
    dist = (dx * dx + dy * dy + dz * dz) ** 0.5
    if dist < 0.5:
        print("[racket] butt already in hand.")
        return
    movers = []
    if parent is not None:
        movers.append(parent)
    for p in (parts or []):
        if p is not None and p != parent:
            movers.append(p)
    olds = []
    for a in movers:
        try:
            _l = a.get_actor_location()
            olds.append((float(_l.x), float(_l.y), float(_l.z)))
        except Exception:
            olds.append(None)
    try:
        _pl = parent.get_actor_location()
        parent.set_actor_location(
            unreal.Vector(float(_pl.x) + dx, float(_pl.y) + dy, float(_pl.z) + dz),
            False, True)
    except Exception as e:
        print("[racket] parent shift failed (%s)" % e)
        return
    for a, ol in zip(movers, olds):
        if a == parent or ol is None:
            continue
        try:
            _nl = a.get_actor_location()
            mx = float(_nl.x) - ol[0]
            my = float(_nl.y) - ol[1]
            mz = float(_nl.z) - ol[2]
            moved = (mx * mx + my * my + mz * mz) ** 0.5
            if moved < dist * 0.5:
                a.set_actor_location(
                    unreal.Vector(float(_nl.x) + dx, float(_nl.y) + dy, float(_nl.z) + dz),
                    False, True)
        except Exception:
            pass
    print("[racket] butt snapped to hand (shifted %.1fcm)." % dist)
    # Lean top outward+forward, orbiting about the butt pivot (all parts
    # carry near-pure X-roll orientation, so Euler addition stays exact
    # enough for a near-symmetric racket, no quat math needed).
    try:
        la = math.radians(float(RACKET_LEAN_ROLL))
        lc, ls = math.cos(la), math.sin(la)
        pa = math.radians(float(RACKET_LEAN_PITCH))
        pc, ps = math.cos(pa), math.sin(pa)
        for a in movers:
            try:
                _al = a.get_actor_location()
                _ar = a.get_actor_rotation()
                vx = float(_al.x) - tx
                vy = float(_al.y) - ty
                vz = float(_al.z) - tz
                if vx * vx + vy * vy + vz * vz > 0.04:
                    # Stage 1: roll about world X (outward).
                    ry = vy * lc - vz * ls
                    rz = vy * ls + vz * lc
                    # Stage 2: pitch about world Y (forward, toward net).
                    rx = vx * pc + rz * ps
                    rz2 = -vx * ps + rz * pc
                    a.set_actor_location(
                        unreal.Vector(tx + rx, ty + ry, tz + rz2), False, True)
                nr = unreal.Rotator(0.0, 0.0, 0.0)
                nr.pitch = float(_ar.pitch) + float(RACKET_LEAN_PITCH)
                nr.yaw = float(_ar.yaw)
                nr.roll = float(_ar.roll) + float(RACKET_LEAN_ROLL)
                a.set_actor_rotation(nr, True)
            except Exception:
                pass
        print("[racket] lean roll=%.1f pitch=%.1f applied." % (
            float(RACKET_LEAN_ROLL), float(RACKET_LEAN_PITCH)))
    except Exception as e:
        print("[racket] lean skipped (%s)" % e)


def spawn_opponent_player(preset: str = "baseline"):
    """Spawns the opponent at the far END of the court facing the robot,
    with a racket in the right hand."""
    cfg = court_config.get_court_config()
    actor_subsystem = _actor_subsystem()

    # Collect FIRST, destroy after (destroying while iterating the live list
    # skips actors and leaves stale bodies/rackets floating mid-court).
    doomed = [a for a in actor_subsystem.get_all_level_actors()
              if a and "OpponentPlayer" in a.get_actor_label()]
    for a in doomed:
        try:
            actor_subsystem.destroy_actor(a)
        except Exception:
            pass

    half = getattr(cfg, "half_length_cm", 1188.72)
    half_w = getattr(cfg, "half_doubles_width_cm", 548.64)

    preset_offsets = {
        "center": unreal.Vector(half * 0.70, 0.0, 0.0),
        "left": unreal.Vector(half * 0.70, -half_w * 0.60, 0.0),
        "right": unreal.Vector(half * 0.70, half_w * 0.60, 0.0),
        # Behind the far baseline, like a real receiver
        "baseline": unreal.Vector(half + 250.0, 0.0, 0.0),
    }

    target_loc = preset_offsets.get(preset, preset_offsets["baseline"])
    target_loc.z = 0.0  # feet exactly on the ground plane
    # Face the robot: yaw from +X axis toward (ROBOT - player), pitch/roll = 0
    yaw = math.degrees(math.atan2(ROBOT_Y - target_loc.y, ROBOT_X - target_loc.x))
    target_rot = _yaw_rot(yaw)

    skel_pkgs, stat_pkgs = _find_character_assets()
    if not skel_pkgs and not stat_pkgs:
        _import_character_glb()
        skel_pkgs, stat_pkgs = _find_character_assets()

    player_actor = None
    sk_comp = None
    anchor_is_skeletal = False
    mesh_path = None

    if stat_pkgs and not skel_pkgs:
        # Realistic STATIC character: GLB node transforms place each part
        # (one shared spawn shredded node-local assemblies). Uniform scale
        # from the tallest part preserves proportions. Custom yaw offset
        # applies ONLY here (Manny keeps facing the robot).
        trot = _yaw_rot(yaw + float(CHARACTER_YAW_OFFSET))
        yr = math.radians(float(yaw + float(CHARACTER_YAW_OFFSET)))
        yc, ys = math.cos(yr), math.sin(yr)
        import os
        glb_src = next((p for p in CHARACTER_DISK_CANDIDATES if os.path.isfile(p)), None)
        node_map, nrot = _read_glb_nodes(glb_src) if glb_src else ({}, 0)
        loaded = []
        tallest = 0.0
        for pkg in stat_pkgs:
            m = unreal.EditorAssetLibrary.load_asset(pkg)
            if not m:
                continue
            h = _mesh_z_height(m)
            loaded.append((pkg, m, h))
            tallest = max(tallest, h)
        uni = (CHARACTER_TARGET_HEIGHT_CM / tallest) if tallest > 1.0 else 1.0
        print("[character] uniform scale x%.4f (tallest=%.1fcm, %d parts)" % (
            uni, tallest, len(loaded)))
        bodies = []
        matched = 0
        for i, (pkg, m, h) in enumerate(loaded):
            aname = pkg.rsplit("/", 1)[-1]
            t = _match_node(aname, node_map)
            if t is None:
                ploc = target_loc
                print("[character] no node match for %s (at origin)" % aname)
            else:
                # GLB meters/Y-up -> UE cm/Z-up, scaled, yawed into place.
                ox, oy, oz = t[0] * 100.0, -t[2] * 100.0, t[1] * 100.0
                ploc = unreal.Vector(
                    float(target_loc.x) + uni * (ox * yc - oy * ys),
                    float(target_loc.y) + uni * (ox * ys + oy * yc),
                    float(target_loc.z) + uni * oz)
                matched += 1
            a = actor_subsystem.spawn_actor_from_class(
                unreal.StaticMeshActor, ploc, trot)
            a.set_actor_label("OpponentPlayer_Target" if player_actor is None
                              else "OpponentPlayer_Part_%d" % i)
            a.tags = ["OpponentPlayer", "YOLOTarget", "Person"]
            a.set_folder_path("TennisCourt/Opponent")
            comp = a.static_mesh_component
            comp.set_static_mesh(m)
            comp.set_collision_profile_name("BlockAll")
            a.set_actor_scale3d(unreal.Vector(uni, uni, uni))
            a.set_actor_location(ploc, False, True)
            a.set_actor_rotation(trot, True)
            if player_actor is None:
                player_actor = a
            bodies.append(a)
        print("[character] node-matched %d/%d parts%s." % (
            matched, len(loaded),
            ", %d rotated nodes (placement approximate)" % nrot if nrot else ""))
        if bodies:
            # Ground: GLB origin is usually the model CENTER, so lift the
            # whole assembly until the feet touch z=0.
            try:
                _res = unreal.GameplayStatics.get_actor_array_bounds(bodies, False)
                _bo, _be = _res[0], _res[1]
                _minz = float(_bo.z) - float(_be.z)
                if abs(_minz) > 0.5:
                    for b in bodies:
                        try:
                            _bl = b.get_actor_location()
                            b.set_actor_location(unreal.Vector(
                                float(_bl.x), float(_bl.y), float(_bl.z) - _minz),
                                False, True)
                        except Exception:
                            pass
                    print("[character] grounded (lifted %.1fcm)." % (-_minz))
            except Exception as e:
                print("[character] grounding skipped (%s)" % e)
        if player_actor is not None:
            print("[player_spawner] Realistic static character (%d part(s))." % len(loaded))

    if player_actor is None:
        player_actor = actor_subsystem.spawn_actor_from_class(
            unreal.SkeletalMeshActor, target_loc, target_rot)

        if not player_actor:
            return None

        # Force upright + grounded (kills any inherited tilt)
        player_actor.set_actor_location(target_loc, False, True)
        player_actor.set_actor_rotation(target_rot, True)

        player_actor.set_actor_label("OpponentPlayer_Target")
        player_actor.tags = ["OpponentPlayer", "YOLOTarget", "Person"]
        player_actor.set_folder_path("TennisCourt/Opponent")

        mesh = None
        if skel_pkgs:
            mesh = unreal.EditorAssetLibrary.load_asset(skel_pkgs[0])
            mesh_path = skel_pkgs[0]
            if mesh:
                print("[player_spawner] Using character skeletal mesh: %s" % mesh_path)
        if mesh is None:
            mesh, mesh_path = _try_load_mesh()
        sk_comp = player_actor.skeletal_mesh_component
        anchor_is_skeletal = False
        if mesh and sk_comp:
            sk_comp.set_skeletal_mesh_asset(mesh)
            sk_comp.set_collision_profile_name("BlockAll")
            # Mesh component itself must be unrotated inside the actor
            sk_comp.set_relative_location(unreal.Vector(0, 0, 0), False, False)
            sk_comp.set_relative_rotation(unreal.Rotator(0, 0, 0), False, False)
            if mesh_path and ("Manny" in mesh_path or "Quinn" in mesh_path):
                _apply_idle_animation(sk_comp, mesh_path)
                anchor_is_skeletal = True
            print(f"[player_spawner] Opponent at '{preset}' + racket.")
        else:
            # No engine mesh in this project -> primitive body moved to target
            body = _build_fallback_body(actor_subsystem)
            body.set_actor_location(target_loc, False, True)
            body.set_actor_rotation(target_rot, True)
            # Re-target the racket anchor to the visible body group
            player_actor = body
            print(f"[player_spawner] Opponent (primitive body) at '{preset}' + racket.")

    yr0 = math.radians(yaw)
    c0, s0 = math.cos(yr0), math.sin(yr0)
    expected_racket = unreal.Vector(
        target_loc.x + RACKET_REL_LOC.x * c0 - RACKET_REL_LOC.y * s0,
        target_loc.y + RACKET_REL_LOC.x * s0 + RACKET_REL_LOC.y * c0,
        target_loc.z + RACKET_REL_LOC.z)
    _racket_parent, _racket_parts = _build_racket(
        actor_subsystem, player_actor, expected_racket, (target_loc, yaw))
    # Final enforcement AFTER all attaches: upright + grounded
    player_actor.set_actor_location(target_loc, False, True)
    player_actor.set_actor_rotation(_yaw_rot(yaw), True)
    loc = player_actor.get_actor_location()
    rot = player_actor.get_actor_rotation()
    print("[player_spawner] FINAL loc=(%.1f, %.1f, %.1f) rot=(P=%.1f Y=%.1f R=%.1f)" % (
        loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll))
    if not RACKET_BAKED:
        _snap_butt_to_hand(_racket_parent, _racket_parts, sk_comp if anchor_is_skeletal else None, yaw)
    return player_actor
