# SPDX-License-Identifier: MIT
#!/usr/bin/env python3
"""Photoreal Cycles renders of Tomo by DreamMachina (formerly evoKin V.01): orange furry teddy,
Mirumi-style passive spring hug arms, head pan + tilt.

STLs are in millimetres, Z-up, -Y face, exported at yaw=0, tilt=0, arms closed (0 = hugging, + = open).
This script scales them 0.001 (Blender metres) and poses moving parts with the
same imposed kinematics as scripts/sim_v01.py.

Usage (from any cwd):
  blender -b -P render_blender.py -- --preview
  blender -b -P render_blender.py -- --final
  blender -b -P render_blender.py -- --shot hero_hug --final
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

# -----------------------------------------------------------------------------
# Paths and constants
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
STL = ROOT / "stl"
OUT = ROOT / "renders" / "blender"

def resolve_stl(filename):
    name = Path(filename).name
    for folder in (STL, STL / "templates", STL / "reference"):
        candidate = folder / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{name} not found under {STL}")
BLEND = OUT / "evokin_v01_fur.blend"
S = 0.001  # mm -> m

# Official / CAD numbers (mm)
EYE_X, EYE_Z, HD = 13.0, 120.0, 74.0
# Flange just proud of the head surface (~y=-35.1 at the eye)
BEZEL_Y = -36.2
HL = (49.95, -16.19, 0.0)   # left hip hinge (vertical, z axis); right is mirrored in x
HR = (-49.95, -16.19, 0.0)
TILT_AX = (0.0, 6.0, 119.0) # head tilt axis along x through y=6, z=119 (+ = nose down)
REST_L, REST_R = 0.0, 0.0   # STL export pose: arms closed on their rest stops
ARM_OPEN = 40.0             # open stop
GF, G_SLOPE = -30.0, 0.25   # groove floor y = GF - G_SLOPE*(z-30) (leans 14°)
GZ0, GZ1, GR = 12.0, 62.0, 8.0
HANDLE_D = 12.5             # round bag handle
try:
    import json as _json
    _G = _json.load(open(ROOT / "results" / "summary_sweep.json"))["hug"]["grip"]
    HUG_OPEN = next(g["open_deg"] for g in _G if g.get("d_mm") == HANDLE_D)
except Exception:
    HUG_OPEN = 4.39         # arm opening on a Ø12.5 handle (sim_v01.py)

HEAD_PARTS = {
    "head_back", "head_front", "tilt_hub", "dummy_cam", "dummy_horn_tilt",
    "bezel_L", "bezel_R", "eye_L", "eye_R", "eye_rim_L", "eye_rim_R", "fur_head",
}
TURRET_PARTS = {"neck_turret", "yaw_coupler", "yaw_retainer_A", "yaw_retainer_B",
                "dummy_servo_tilt", "dummy_horn_yaw"}

ARM_L_PARTS = {"arm_L", "paw_pad_L", "sleeve_proxy_L", "fur_arm_L"}
ARM_R_PARTS = {"arm_R", "paw_pad_R", "sleeve_proxy_R", "fur_arm_R"}
GLOBAL = [None]             # optional whole-robot matrix (hanging pose)

# Deep saturated marmalade. AgX + studio lights wash mid oranges to peach,
# so the albedo is deliberately darker and redder than the target grade.
FUR_SRGB = (186, 58, 0)
FUR_TIP_SRGB = (220, 88, 6)
FUR_ROOT_SRGB = (108, 28, 0)


def argv_after_dd():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return []


def parse_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--preview", action="store_true")
    p.add_argument("--final", action="store_true")
    p.add_argument("--shot", default="all",
                   choices=["all", "hero_hug", "arms_open", "cutaway"])
    p.add_argument("--samples", type=int, default=0)
    p.add_argument("--width", type=int, default=0)
    p.add_argument("--skip-hair", action="store_true")
    ns = p.parse_args(argv_after_dd())
    if not ns.final and not ns.preview:
        ns.preview = True  # safe default if invoked bare
    return ns


def srgb_lin(rgb, a=1.0):
    def u(x):
        x = x / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (u(rgb[0]), u(rgb[1]), u(rgb[2]), a)


def hex_lin(h, a=1.0):
    h = h.lstrip("#")
    return srgb_lin(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), a)


def mm(*xyz):
    return Vector(xyz) * S


def rot_z_about(angle_deg, pivot_mm):
    T = Matrix.Translation(mm(*pivot_mm))
    R = Matrix.Rotation(math.radians(angle_deg), 4, "Z")
    return T @ R @ T.inverted()


def rot_x_about(angle_deg, pivot_mm):
    T = Matrix.Translation(mm(*pivot_mm))
    R = Matrix.Rotation(math.radians(angle_deg), 4, "X")
    return T @ R @ T.inverted()


def _pose_local(name, yaw, arm_l, arm_r, tilt):
    if name in HEAD_PARTS:
        return rot_z_about(yaw, (0, 0, 0)) @ rot_x_about(tilt, TILT_AX)
    if name in TURRET_PARTS:
        return rot_z_about(yaw, (0, 0, 0))
    if name in ARM_L_PARTS:
        return rot_z_about(arm_l, HL)
    if name in ARM_R_PARTS:
        return rot_z_about(-arm_r, HR)
    return Matrix.Identity(4)


def pose_matrix(name, yaw, arm_l, arm_r, tilt=0.0):
    m = _pose_local(name, yaw, arm_l, arm_r, tilt)
    return (GLOBAL[0] @ m) if GLOBAL[0] is not None else m


# -----------------------------------------------------------------------------
# Scene bootstrap
# -----------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    # World
    world = bpy.data.worlds.new("StudioWorld")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = srgb_lin((214, 210, 204))
    bg.inputs["Strength"].default_value = 0.18
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def _deselect():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)


def import_stl(path, name):
    _deselect()
    if not Path(path).exists():
        raise FileNotFoundError(path)
    # Import at native mm, then bake 0.001 into the mesh. More reliable than
    # global_scale, which was applied inconsistently across a batch of files.
    bpy.ops.wm.stl_import(
        filepath=str(path),
        global_scale=1.0,
        forward_axis="Y",
        up_axis="Z",
        use_scene_unit=False,
        use_mesh_validate=True,
    )
    selected = list(bpy.context.selected_objects)
    if not selected:
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        selected = [meshes[-1]]
    obj = selected[0]
    if len(selected) > 1:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
    obj.name = name
    # Clear any object transform, bake mm -> m into vertices.
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    obj.data.transform(Matrix.Diagonal((S, S, S, 1.0)))
    obj.data.update()
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def new_empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    return e


# -----------------------------------------------------------------------------
# Materials
# -----------------------------------------------------------------------------
def _principled(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-280, 0)
    out.location = (200, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return nt, bsdf, out


def mat_plastic(name, color, rough=0.35, metallic=0.0, alpha=1.0, spec=0.4):
    mat = bpy.data.materials.new(name)
    nt, bsdf, out = _principled(mat)
    bsdf.inputs["Base Color"].default_value = color if len(color) == 4 else (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if alpha < 1.0 - 1e-6:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.blend_method = "BLEND"
        mat.shadow_method = "NONE" if hasattr(mat, "shadow_method") else mat.blend_method
        mat.use_backface_culling = False
    return mat


def mat_eye_glass():
    mat = bpy.data.materials.new("EyeGlass")
    nt, bsdf, out = _principled(mat)
    # Almost-black glossy "safety eye" with a glass coat
    bsdf.inputs["Base Color"].default_value = srgb_lin((8, 6, 6))
    bsdf.inputs["Metallic"].default_value = 0.05
    bsdf.inputs["Roughness"].default_value = 0.035
    bsdf.inputs["Specular IOR Level"].default_value = 0.85
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Coat Roughness"].default_value = 0.02
    bsdf.inputs["Coat IOR"].default_value = 1.5
    # very low transmission so it stays dark but has a refraction highlight
    try:
        bsdf.inputs["IOR"].default_value = 1.5
    except KeyError:
        pass
    return mat


def mat_pad():
    mat = bpy.data.materials.new("PawPad")
    nt, bsdf, out = _principled(mat)
    bsdf.inputs["Base Color"].default_value = srgb_lin((168, 104, 86))
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Sheen Weight"].default_value = 0.35
    bsdf.inputs["Sheen Roughness"].default_value = 0.5
    try:
        bsdf.inputs["Subsurface Weight"].default_value = 0.18
        bsdf.inputs["Subsurface Radius"].default_value = (0.4, 0.15, 0.1)
        bsdf.inputs["Subsurface Scale"].default_value = 0.008
    except KeyError:
        pass
    return mat


def mat_fur_hair(name="FurHair", color=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    hair = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.parametrization = "COLOR"
    try:
        hair.model = "CHIANG"
    except Exception:
        pass
    col = color or srgb_lin(FUR_SRGB)
    def _set(node, key, val):
        if key in node.inputs:
            node.inputs[key].default_value = val
    _set(hair, "Color", col)
    _set(hair, "Roughness", 0.28)
    _set(hair, "Radial Roughness", 0.32)
    _set(hair, "Coat", 0.04)
    _set(hair, "Random Color", 0.06)
    _set(hair, "Random Roughness", 0.08)
    nt.links.new(hair.outputs["BSDF"], out.inputs["Surface"])
    print("HAIR sockets:", [i.name for i in hair.inputs], "param", hair.parametrization, flush=True)
    return mat


def mat_fur_undercoat():
    return mat_fur_hair("FurUndercoat", srgb_lin(FUR_ROOT_SRGB))


def mat_fur_guard():
    return mat_fur_hair("FurGuard", srgb_lin(FUR_SRGB))


def mat_shell_xray(name, color, alpha=0.14):
    mat = bpy.data.materials.new(name)
    nt, bsdf, out = _principled(mat)
    c = color if len(color) == 4 else (*color[:3], 1)
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["Alpha"].default_value = alpha
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    mat.blend_method = "BLEND"
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"
    # hide from shadow so internals stay readable
    return mat


def assign(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


# -----------------------------------------------------------------------------
# Mesh helpers
# -----------------------------------------------------------------------------
def apply_object_scale(obj):
    mw = obj.matrix_world.copy()
    obj.data.transform(Matrix.Diagonal((*obj.scale, 1.0)))
    obj.scale = (1, 1, 1)
    # keep location/rotation
    loc, rot, _ = mw.decompose()
    obj.location = loc
    obj.rotation_euler = rot.to_euler()


def make_uv_sphere(name, location, scale_m, segments=48, rings=28):
    _deselect()
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=1.0, location=(0, 0, 0)
    )
    sph = bpy.context.active_object
    sph.name = name
    # bake scale + translation into the mesh so pose matrices stay clean
    sph.data.transform(Matrix.Diagonal((*scale_m, 1.0)))
    sph.data.transform(Matrix.Translation(location))
    sph.data.update()
    sph.location = (0, 0, 0)
    sph.rotation_euler = (0, 0, 0)
    sph.scale = (1, 1, 1)
    for p in sph.data.polygons:
        p.use_smooth = True
    return sph


def density_group(obj, name, pred):
    """Vertex group from pred(world_co_mm). pred may return bool or a 0..1 weight."""
    vg = obj.vertex_groups.new(name=name)
    mw = obj.matrix_world
    buckets = {}
    for v in obj.data.vertices:
        world_m = mw @ v.co
        world_mm = (world_m.x / S, world_m.y / S, world_m.z / S)
        w = pred(world_mm)
        w = 1.0 if w is True else (0.0 if w is False else float(w))
        w = 0.0 if w < 0 else (1.0 if w > 1 else w)
        key = round(w, 3)
        buckets.setdefault(key, []).append(v.index)
    for w, idx in buckets.items():
        if idx:
            vg.add(idx, w, "REPLACE")
    return vg


def torso_fur_ok(pt):
    x, y, z = pt
    if z > 85.5 or z < -2:
        return False
    # belly groove: keep the channel bare so a strap / handle sits in it
    if abs(x) < GR + 2.0 and GZ0 - 6 < z < GZ1 + 6 and y < -15:
        return False
    # hip hinges: no hair on the knuckles
    for hx in (HL[0], HR[0]):
        if ((x - hx) ** 2 + (y - HL[1]) ** 2) ** 0.5 < 11.0 and 14 < z < 46:
            return False
    return True


def groove_fur_emitter(obj):
    """Press a channel into the torso fur ellipsoid along the leaning belly groove."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    inv = mw.inverted()
    for v in bm.verts:
        w = mw @ v.co
        x, y, z = w.x / S, w.y / S, w.z / S
        if y > -10 or abs(x) > GR + 3:
            continue
        zc = min(max(z, GZ0), GZ1)
        c = GF - G_SLOPE * (zc - 30.0) - GR          # capsule centre line (y)
        dz = z - zc
        rr = GR + 1.0                                 # 1 mm of pile on the liner
        q = rr * rr - x * x - dz * dz
        if q <= 0:
            continue
        yb = c + math.sqrt(q)                         # back wall of the channel
        if y < yb:
            nw = inv @ Vector((x * S, yb * S, z * S))
            v.co = nw
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def head_fur_ok(pt):
    """Weight 1 everywhere on the head except a soft well around each eye."""
    x, y, z = pt
    if z < 88.0:
        return 0.0
    w = 1.0
    if y < 5.0:
        for sx in (1, -1):
            r = ((x - sx * EYE_X) ** 2 + (z - EYE_Z) ** 2) ** 0.5
            # no hair over the visible eyeball; full coat by ~11 mm
            if r < 6.4:
                return 0.0
            if r < 11.0:
                w = min(w, (r - 6.4) / (11.0 - 6.4))
    return w


# -----------------------------------------------------------------------------
# Hair
# -----------------------------------------------------------------------------
def add_hair(obj, name, length_m, count, children, material,
             clump=0.55, rough=0.10, kink_amp=0.04, kink_freq=4.0,
             length_rand=0.18, density_vg=None, root_m=0.00040, tip_m=0.00010):
    # Ensure a material slot for hair
    if material.name not in [m.name for m in obj.data.materials]:
        obj.data.materials.append(material)
    mat_index = list(obj.data.materials).index(
        next(m for m in obj.data.materials if m.name == material.name)
    ) + 1  # particle material_slot is 1-based "Default Material" style

    mod = obj.modifiers.new(name, "PARTICLE_SYSTEM")
    psys = obj.particle_systems[-1]
    psys.name = name
    ps = psys.settings
    ps.name = name + "Settings"
    ps.type = "HAIR"
    ps.use_advanced_hair = True
    ps.emit_from = "FACE"
    ps.use_emit_random = True
    ps.count = int(count)
    ps.hair_length = length_m
    ps.length_random = length_rand
    ps.hair_step = 5
    ps.display_step = 3
    ps.render_step = 4
    ps.use_hair_bspline = True
    ps.shape = -0.6
    # Default particle_size is 0.05 m (5 cm) and will fill the frame.
    # Keep every radius term in millimetres-as-metres, never 1.0 m.
    # Cycles strip radius is particle_size * root/tip_radius. Keep the product
    # in millimetres, never the 0.05 m default (that fills the frame).
    ps.particle_size = 1.0
    ps.radius_scale = 1.0
    ps.root_radius = root_m
    ps.tip_radius = tip_m
    try:
        ps.use_multiplier = False
    except Exception:
        pass
    ps.child_type = "NONE"
    ps.child_percent = max(2, min(6, children // 3))
    ps.rendered_child_count = int(children)
    ps.child_length = 0.92
    ps.child_length_threshold = 0.1
    ps.child_radius = max(0.004, length_m * 0.8)
    ps.child_size = 1.0
    ps.clump_factor = clump
    ps.clump_shape = 0.15
    ps.roughness_endpoint = rough
    ps.roughness_end_shape = 0.4
    ps.roughness_1 = rough * 0.5
    ps.roughness_1_size = 0.03
    ps.roughness_2 = rough * 0.25
    ps.roughness_2_size = 0.008
    ps.kink = "CURL"
    ps.kink_amplitude = kink_amp * length_m
    ps.kink_frequency = kink_freq
    ps.kink_shape = 0.2
    ps.kink_amplitude_random = 0.35
    # material
    try:
        ps.material_slot = obj.data.materials[mat_index - 1].name
    except Exception:
        try:
            ps.material = mat_index
        except Exception:
            pass
    if density_vg is not None:
        psys.vertex_group_density = density_vg.name
    # hide emitter later (per-mode)
    return psys


def set_emitter_visible(obj, visible):
    # Hair instancer visibility
    obj.show_instancer_for_render = visible
    obj.show_instancer_for_viewport = visible
    obj.hide_render = not visible and not obj.particle_systems
    # If it has hair, keep the object renderable so hair renders, hide mesh
    if obj.particle_systems:
        obj.hide_render = False
        obj.show_instancer_for_render = visible


# -----------------------------------------------------------------------------
# Assembly
# -----------------------------------------------------------------------------
PART_FILES = {
    # printed / structural
    "torso_front": "torso_front.stl",
    "torso_back": "torso_back.stl",
    "head_front": "head_front.stl",
    "head_back": "head_back.stl",
    "tray": "tray.stl",
    "yaw_collar": "yaw_collar.stl",
    "yaw_coupler": "yaw_coupler.stl",
    "yaw_retainer_A": "yaw_retainer_A.stl",
    "yaw_retainer_B": "yaw_retainer_B.stl",
    "yaw_thrust_washer": "yaw_thrust_washer.stl",
    "neck_turret": "neck_turret.stl",
    "tilt_hub": "tilt_hub.stl",
    "arm_L": "arm_L.stl",
    "arm_R": "arm_R.stl",
    "hip_cap_L": "hip_cap_L.stl",
    "hip_cap_R": "hip_cap_R.stl",
    "paw_pad_L": "paw_pad_L.stl",
    "paw_pad_R": "paw_pad_R.stl",
    "sleeve_proxy_L": "sleeve_proxy_L.stl",
    "sleeve_proxy_R": "sleeve_proxy_R.stl",
    "fur_proxy_torso": "fur_proxy_torso.stl",
    "dummy_servo_yaw": "dummy_servo_yaw.stl",
    "dummy_servo_tilt": "dummy_servo_tilt.stl",
    "dummy_horn_yaw": "dummy_horn_yaw.stl",
    "dummy_horn_tilt": "dummy_horn_tilt.stl",
    "dummy_pi": "dummy_pi.stl",
    "dummy_cam": "dummy_cam.stl",
    "dummy_speaker": "dummy_speaker.stl",
    "dummy_amp": "dummy_amp.stl",
    "dummy_mic": "dummy_mic.stl",
}


# Contrasting colours for the cutaway (linear)
CUT_COLORS = {
    "torso_front": hex_lin("E8893A"),
    "torso_back": hex_lin("C8742F"),
    "head_front": hex_lin("EFC35A"),
    "head_back": hex_lin("D9A441"),
    "tray": hex_lin("7A5A3A"),
    "yaw_collar": hex_lin("8A9AA8"),
    "yaw_coupler": hex_lin("6B6B6B"),
    "yaw_retainer_A": hex_lin("9AA0A6"),
    "yaw_retainer_B": hex_lin("9AA0A6"),
    "yaw_thrust_washer": hex_lin("C0392B"),
    "neck_turret": hex_lin("5D6D7E"),
    "tilt_hub": hex_lin("E74C3C"),
    "arm_L": hex_lin("3D85C6"),
    "arm_R": hex_lin("6AA84F"),
    "hip_cap_L": hex_lin("2F5F8F"),
    "hip_cap_R": hex_lin("4F7A3A"),
    "paw_pad_L": hex_lin("3A2A22"),
    "paw_pad_R": hex_lin("3A2A22"),
    "dummy_servo_yaw": hex_lin("2C3E50"),
    "dummy_servo_tilt": hex_lin("2C3E50"),
    "dummy_horn_yaw": hex_lin("F1C40F"),
    "dummy_horn_tilt": hex_lin("F1C40F"),
    "dummy_pi": hex_lin("8E44AD"),
    "dummy_cam": hex_lin("9B59B6"),
    "dummy_speaker": hex_lin("1ABC9C"),
    "dummy_amp": hex_lin("16A085"),
    "dummy_mic": hex_lin("27AE60"),
}


def place_bezel(name, sx):
    obj = import_stl(resolve_stl("bezel.stl"), name)
    obj.location = mm(sx * EYE_X, BEZEL_Y, EYE_Z)
    obj.rotation_euler = (math.radians(-90), 0, 0)
    bpy.context.view_layer.update()
    return obj


def place_eye(name, sx):
    # Dark glossy safety-eye. 7 mm sphere, front ~3 mm proud of the bezel
    # flange so it reads as an eye from the front, not just a chrome ring.
    r = 0.0070
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=40, ring_count=20, radius=r,
        location=mm(sx * EYE_X, BEZEL_Y + 2.0, EYE_Z),
    )
    obj = bpy.context.active_object
    obj.name = name
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def place_eye_rim(name, sx):
    """Thin dark washer sitting on the fur surface, like a safety-eye flange.
    The CAD bezel is a 27 mm mounting ring that nearly meets in the middle
    and reads as a raccoon mask if left visible on the hero."""
    _deselect()
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0076,
        minor_radius=0.0011,
        major_segments=36,
        minor_segments=10,
        location=mm(sx * EYE_X, -39.0, EYE_Z),
        rotation=(math.radians(90), 0, 0),
    )
    obj = bpy.context.active_object
    obj.name = name
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def inflate_mesh(obj, offset_m):
    """Push vertices along normals so a skinny printed arm can carry a plush coat."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for v in bm.verts:
        v.co = v.co + v.normal.normalized() * offset_m
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def make_solid_arm_emitter(src, name):
    """Plump sock from the printed arm: voxel remesh + light smooth + 2 mm inflate.

    V.01 arms are an L (upper arm + forearm blade across the belly), so a convex
    hull would fill the triangle in front of the body. Remesh the solid arm itself.
    """
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(src.data)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    em = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(em)
    em.matrix_world = src.matrix_world.copy()
    em.scale = (1, 1, 1)
    # even faces for hair
    rem = em.modifiers.new("arm_remesh", "REMESH")
    rem.mode = "VOXEL"
    rem.voxel_size = 0.0028
    rem.use_smooth_shade = True
    bpy.context.view_layer.objects.active = em
    _deselect()
    em.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier="arm_remesh")
    except Exception as e:
        print("remesh apply failed", e, flush=True)
    sm = em.modifiers.new("arm_smooth", "SMOOTH")
    sm.factor = 1.0
    sm.iterations = 6
    try:
        bpy.ops.object.modifier_apply(modifier="arm_smooth")
    except Exception as e:
        print("smooth apply failed", e, flush=True)
    inflate_mesh(em, 0.0020)
    for p in em.data.polygons:
        p.use_smooth = True
    return em


def build_assembly(skip_hair=False, preview=False):
    objs = {}
    for name, fn in PART_FILES.items():
        objs[name] = import_stl(resolve_stl(fn), name)

    objs["bezel_L"] = place_bezel("bezel_L", +1)
    objs["bezel_R"] = place_bezel("bezel_R", -1)
    objs["eye_L"] = place_eye("eye_L", +1)
    objs["eye_R"] = place_eye("eye_R", -1)
    objs["eye_rim_L"] = place_eye_rim("eye_rim_L", +1)
    objs["eye_rim_R"] = place_eye_rim("eye_rim_R", -1)

    # ---- materials (hero defaults; cutaway swaps later)
    mats = {}
    mats["print_body"] = mat_plastic("PrintBody", srgb_lin((226, 130, 52)), rough=0.45)
    mats["print_head"] = mat_plastic("PrintHead", srgb_lin((232, 180, 80)), rough=0.45)
    mats["print_dark"] = mat_plastic("PrintDark", srgb_lin((50, 44, 40)), rough=0.4)
    mats["print_bracket"] = mat_plastic("PrintBracket", srgb_lin((42, 46, 50)), rough=0.38)
    mats["bezel"] = mat_plastic("Bezel", srgb_lin((12, 10, 10)), rough=0.35, metallic=0.08, spec=0.35)
    mats["eye"] = mat_eye_glass()
    mats["pad"] = mat_pad()
    mats["fur_under"] = mat_fur_undercoat()
    mats["fur_guard"] = mat_fur_guard()
    mats["fur_clay"] = mat_plastic("FurClay", srgb_lin(FUR_ROOT_SRGB), rough=0.92, spec=0.08)
    # soft sheen on the undercoat so it reads a little like pile even without hair
    try:
        bsdf = mats["fur_clay"].node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Sheen Weight"].default_value = 0.25
            bsdf.inputs["Sheen Roughness"].default_value = 0.4
            bsdf.inputs["Sheen Tint"].default_value = srgb_lin(FUR_TIP_SRGB)
    except Exception:
        pass
    mats["cut"] = {k: mat_plastic("Cut_" + k, v, rough=0.4) for k, v in CUT_COLORS.items()}
    mats["xray_fur"] = mat_shell_xray("XrayFur", srgb_lin(FUR_SRGB), 0.11)
    mats["xray_torso"] = mat_shell_xray("XrayTorso", srgb_lin((232, 137, 58)), 0.18)
    mats["xray_head"] = mat_shell_xray("XrayHead", srgb_lin((239, 195, 90)), 0.16)

    assign(objs["torso_front"], mats["print_body"])
    assign(objs["torso_back"], mats["print_body"])
    assign(objs["fur_proxy_torso"], mats["print_body"])
    assign(objs["head_front"], mats["print_head"])
    assign(objs["head_back"], mats["print_head"])
    assign(objs["arm_L"], mats["print_dark"])
    assign(objs["arm_R"], mats["print_dark"])
    assign(objs["sleeve_proxy_L"], mats["print_dark"])
    assign(objs["sleeve_proxy_R"], mats["print_dark"])
    assign(objs["hip_cap_L"], mats["print_bracket"])
    assign(objs["hip_cap_R"], mats["print_bracket"])
    assign(objs["paw_pad_L"], mats["pad"])
    assign(objs["paw_pad_R"], mats["pad"])
    assign(objs["bezel_L"], mats["bezel"])
    assign(objs["bezel_R"], mats["bezel"])
    assign(objs["eye_rim_L"], mats["bezel"])
    assign(objs["eye_rim_R"], mats["bezel"])
    assign(objs["eye_L"], mats["eye"])
    assign(objs["eye_R"], mats["eye"])
    for k in ("tray", "yaw_collar", "yaw_coupler", "yaw_retainer_A", "yaw_retainer_B",
              "yaw_thrust_washer", "neck_turret", "tilt_hub"):
        assign(objs[k], mats["print_dark"])
    for k in list(CUT_COLORS):
        if k in objs:
            # keep hero mats; cutaway reassigns
            pass

    # ---- fur emitters (clean ellipsoids, not the thin CAD shells)
    # torso: tegg(-4) = scale (50, 44, 54) mm at z=50
    fur_t = make_uv_sphere(
        "fur_torso",
        location=mm(0, 0, 50),
        scale_m=(0.050, 0.044, 0.054),
        segments=128 if not preview else 96,
        rings=64 if not preview else 48,
    )
    groove_fur_emitter(fur_t)
    assign(fur_t, mats["fur_clay"])
    vg_t = density_group(fur_t, "fur_density", torso_fur_ok)
    objs["fur_torso"] = fur_t

    # head: hegg(-3.5) ≈ (45.5, 40.5, 35.5) mm at z=118
    fur_h = make_uv_sphere(
        "fur_head",
        location=mm(0, 0, 118),
        scale_m=(0.0455, 0.0405, 0.0355),
        segments=48 if not preview else 36,
        rings=28 if not preview else 20,
    )
    assign(fur_h, mats["fur_clay"])
    # Do not punch holes in the head mesh: vertex-deleted sockets read as a
    # jagged mask, and the 27 mm CAD bezels showed through them. Hair is
    # kept off the eyeballs with a soft density well instead; the glossy
    # spheres sit proud of the coat like safety eyes.
    vg_h = density_group(fur_h, "fur_density", head_fur_ok)
    objs["fur_head"] = fur_h

    # arm fur: use a slightly inflated copy of sleeve + a paw-region sphere-ish
    # by emitting from the sleeve proxies and the arm solids with a density
    # group that kills the pulley hub (near the pivot).
    def arm_fur_ok_side(side):
        def pred(pt):
            x, y, z = pt
            # No hair on the hip knuckle; keep the inner paw bare so the TPU pad shows.
            hx = HL[0] if side == "L" else HR[0]
            if ((x - hx) ** 2 + (y - HL[1]) ** 2) ** 0.5 < 11.0:
                return 0.0
            if abs(x) < 13.0 and y > -48.0:
                return 0.0
            return 1.0
        return pred

    for side in ("L", "R"):
        src = objs[f"arm_{side}"]
        em = make_solid_arm_emitter(src, f"fur_arm_{side}")
        assign(em, mats["fur_clay"])
        vg = density_group(em, "fur_density", arm_fur_ok_side(side))
        objs[f"fur_arm_{side}"] = em
        objs[f"_vg_arm_{side}"] = vg

    objs["_vg_torso"] = vg_t
    objs["_vg_head"] = vg_h

    # Hair counts: preview uses fewer parents / children
    if not skip_hair:
        mul_c = 0.55 if preview else 1.0
        mul_k = 1.0
        # torso
        add_hair(fur_t, "torso_under", length_m=0.0055, count=int(12000 * mul_c),
                 children=int(10 * mul_k) or 6, material=mats["fur_under"],
                 clump=0.45, rough=0.12, kink_amp=0.05, kink_freq=7,
                 density_vg=vg_t, root_m=0.00016, tip_m=0.00005)
        add_hair(fur_t, "torso_guard", length_m=0.0070, count=int(7000 * mul_c),
                 children=int(8 * mul_k) or 5, material=mats["fur_guard"],
                 clump=0.32, rough=0.22, kink_amp=0.12, kink_freq=5,
                 density_vg=vg_t, root_m=0.00012, tip_m=0.00003)
        # head: a little shorter, tidier around the face
        add_hair(fur_h, "head_under", length_m=0.0050, count=int(9000 * mul_c),
                 children=int(10 * mul_k) or 6, material=mats["fur_under"],
                 clump=0.4, rough=0.1, kink_amp=0.04, kink_freq=7,
                 density_vg=vg_h, root_m=0.00014, tip_m=0.00004)
        add_hair(fur_h, "head_guard", length_m=0.0065, count=int(5000 * mul_c),
                 children=int(8 * mul_k) or 5, material=mats["fur_guard"],
                 clump=0.3, rough=0.2, kink_amp=0.1, kink_freq=5.5,
                 density_vg=vg_h, root_m=0.00011, tip_m=0.000028)
        for side in ("L", "R"):
            em = objs[f"fur_arm_{side}"]
            vg = em.vertex_groups["fur_density"]
            add_hair(em, f"arm_{side}_under", length_m=0.0050, count=int(8000 * mul_c),
                     children=int(8 * mul_k) or 5, material=mats["fur_under"],
                     clump=0.4, rough=0.12, kink_amp=0.05, kink_freq=6,
                     density_vg=vg, root_m=0.00014, tip_m=0.00004)
            add_hair(em, f"arm_{side}_guard", length_m=0.0060, count=int(4500 * mul_c),
                     children=int(7 * mul_k) or 4, material=mats["fur_guard"],
                     clump=0.28, rough=0.2, kink_amp=0.1, kink_freq=5,
                     density_vg=vg, root_m=0.00011, tip_m=0.00003)

    return objs, mats


def apply_pose(objs, yaw, arm_l=REST_L, arm_r=REST_R, tilt=0.0):
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "matrix_world"):
            continue
        obj.matrix_world = pose_matrix(name, yaw, arm_l, arm_r, tilt) @ Matrix.Identity(4)
        # bezels and eyes already have a local transform (location/rotation).
        # pose_matrix for head parts is a yaw about Z at the origin, which must
        # be PRE-multiplied around their existing local matrix.
    # Re-do bezels/eyes/fur_head carefully: they have non-zero rest local mats.
    # Import-posed objects (STLs) have identity rest (geometry already in world).
    # Objects with a rest local matrix (bezel, eye, fur_head, fur_torso):
    #   world = R_yaw @ rest_local
    rest_local = {}
    # We need to store rest matrices the first time. Stash on the object.
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "matrix_world"):
            continue
        if "rest_mw" not in obj:
            obj["rest_mw"] = [list(row) for row in obj.matrix_world]
        rest = Matrix([obj["rest_mw"][0], obj["rest_mw"][1], obj["rest_mw"][2], obj["rest_mw"][3]])
        obj.matrix_world = pose_matrix(name, yaw, arm_l, arm_r, tilt) @ rest
    bpy.context.view_layer.update()


# The first call of apply_pose as written would stash already-posed matrices if
# we pose before stashing. We'll stash immediately after assembly at the export pose.


REST_MW = {}


def stash_rest(objs):
    REST_MW.clear()
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "matrix_world"):
            continue
        REST_MW[name] = obj.matrix_world.copy()


def apply_pose_v2(objs, yaw, arm_l=REST_L, arm_r=REST_R, tilt=0.0):
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "matrix_world"):
            continue
        rest = REST_MW.get(name)
        if rest is None:
            continue
        obj.matrix_world = pose_matrix(name, yaw, arm_l, arm_r, tilt) @ rest
    bpy.context.view_layer.update()


# -----------------------------------------------------------------------------
# Studio
# -----------------------------------------------------------------------------
def add_area(name, loc, rot_deg, size, power, color=(1, 0.98, 0.94, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    lam = bpy.context.active_object
    lam.name = name
    lam.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    lam.data.shape = "RECTANGLE"
    lam.data.size = size[0]
    lam.data.size_y = size[1]
    lam.data.energy = power
    lam.data.color = color[:3]
    lam.data.use_shadow = True
    try:
        lam.data.spread = 90
    except Exception:
        pass
    return lam


def build_cutter():
    """A block that bites the near-front quarter (critter +x, -y) so the
    cutaway looks into the torso and yaw stack from the hero camera."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=mm(70, -70, 80))
    cutter = bpy.context.active_object
    cutter.name = "cutaway_cutter"
    cutter.scale = mm(160, 160, 200)
    # apply scale into mesh, keep location
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cutter.display_type = "WIRE"
    cutter.hide_render = True
    cutter.hide_viewport = True
    return cutter


def add_boolean_cut(obj, cutter, name="cutaway_bool"):
    # remove existing
    for m in list(obj.modifiers):
        if m.name == name:
            obj.modifiers.remove(m)
    mod = obj.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    try:
        mod.solver = "FAST"
    except Exception:
        pass
    mod.object = cutter
    mod.show_render = False
    mod.show_viewport = False
    return mod


def set_cutters(objs, on):
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "modifiers"):
            continue
        for m in obj.modifiers:
            if m.name == "cutaway_bool":
                m.show_render = on
                m.show_viewport = on


def build_studio():
    # Seamless cove: large ground + back wall, slightly curved via a bent plane
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 0.05, 0))
    ground = bpy.context.active_object
    ground.name = "studio_ground"
    mat = mat_plastic("StudioFloor", srgb_lin((226, 222, 216)), rough=0.55, spec=0.2)
    assign(ground, mat)

    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 1.05, 2.0))
    wall = bpy.context.active_object
    wall.name = "studio_back"
    wall.rotation_euler = (math.radians(90), 0, 0)
    assign(wall, mat)

    # Soft key (front-right, slightly high), warm
    add_area("key", loc=(0.32, -0.42, 0.38), rot_deg=(62, 0, 38),
             size=(0.45, 0.35), power=9.0, color=(1.0, 0.90, 0.78, 1))
    # Fill (front-left), cooler / dimmer
    add_area("fill", loc=(-0.38, -0.30, 0.24), rot_deg=(72, 0, -40),
             size=(0.50, 0.40), power=4.2, color=(0.95, 0.93, 0.90, 1))
    # Rim / kicker from back-right above
    add_area("rim", loc=(0.20, 0.45, 0.42), rot_deg=(55, 0, 200),
             size=(0.30, 0.18), power=5.0, color=(1.0, 0.92, 0.80, 1))
    # Gentle top
    add_area("top", loc=(0.0, -0.05, 0.70), rot_deg=(0, 0, 0),
             size=(0.6, 0.5), power=2.2, color=(1.0, 0.95, 0.88, 1))


def build_camera():
    # v4: front 3/4 from the critter's left-front, a little above eye height, so
    # the forward-reaching paws and the face both read. 80 mm lens at ~0.55 m.
    target = mm(0, -10, 72)
    loc = mm(240, -470, 230)
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.active_object
    cam.name = "hero_cam"
    direction = target - loc
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 80
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.05
    cam.data.clip_end = 12.0
    cam.data.dof.use_dof = False
    bpy.context.scene.camera = cam
    return cam


# -----------------------------------------------------------------------------
# Visibility / modes
# -----------------------------------------------------------------------------
HERO_SHOW = {
    "fur_torso", "fur_head", "fur_arm_L", "fur_arm_R",
    "eye_rim_L", "eye_rim_R", "eye_L", "eye_R",
    "studio_ground", "studio_back",
}
# hide raw printed shells and internals on the finished look
HERO_HIDE = {
    "torso_front", "torso_back", "head_front", "head_back",
    "tray", "yaw_collar", "yaw_coupler", "yaw_retainer_A", "yaw_retainer_B",
    "yaw_thrust_washer",
    "neck_turret", "tilt_hub",
    "arm_L", "arm_R", "sleeve_proxy_L", "sleeve_proxy_R",
    "fur_proxy_torso", "bezel_L", "bezel_R",
    "hip_cap_L", "hip_cap_R",
    "dummy_servo_yaw", "dummy_servo_tilt", "dummy_horn_yaw", "dummy_horn_tilt",
    "dummy_pi", "dummy_cam", "dummy_speaker", "dummy_amp", "dummy_mic",
}

CUT_XRAY = {"fur_torso", "fur_head", "fur_proxy_torso", "torso_front", "torso_back",
            "head_front", "head_back"}
CUT_HIDE = {"sleeve_proxy_L", "sleeve_proxy_R"}


def set_hide(obj, hide):
    obj.hide_render = hide
    obj.hide_viewport = hide


def enable_hair(obj, on):
    for mod in obj.modifiers:
        if mod.type == "PARTICLE_SYSTEM":
            mod.show_render = on
            mod.show_viewport = on


def set_mode_hero(objs, show_emitters=False):
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "hide_render"):
            continue
        if name in HERO_HIDE:
            set_hide(obj, True)
            enable_hair(obj, False)
        else:
            set_hide(obj, False)
            enable_hair(obj, True)
            # Hide the fur-emitter mesh when hair is present; show it as clay
            # when we skipped hair, so the body is still visible.
            has_hair = bool(obj.particle_systems)
            if name.startswith("fur_"):
                # Keep a dark undercoat under the hair so the body and arms
                # don't go see-through if the coat is a little sparse.
                set_emitter_visible(obj, True)
                obj.hide_render = False
            else:
                set_emitter_visible(obj, True)
    for n in ("eye_L", "eye_R", "eye_rim_L", "eye_rim_R"):
        if n in objs:
            set_hide(objs[n], False)
            set_emitter_visible(objs[n], True)
    for n in ("bezel_L", "bezel_R", "hip_cap_L", "hip_cap_R"):
        if n in objs:
            set_hide(objs[n], True)


def set_mode_cutaway(objs, mats):
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "hide_render"):
            continue
        # no hair in the cutaway — it obscures the internals
        enable_hair(obj, False)
        if name in CUT_HIDE or name.startswith("fur_arm") or name in ("fur_torso", "fur_head"):
            # show the designed fur_proxy as the transparent coat; hide GN ellipsoids
            if name in ("fur_torso", "fur_head"):
                set_hide(obj, True)
                continue
            if name.startswith("fur_arm"):
                set_hide(obj, True)
                continue
        if name in CUT_HIDE:
            set_hide(obj, True)
            continue
        set_hide(obj, False)
        set_emitter_visible(obj, True)

    # transparent shells
    assign(objs["fur_proxy_torso"], mats["xray_fur"])
    set_hide(objs["fur_proxy_torso"], False)
    objs["fur_proxy_torso"].visible_shadow = False
    for n in ("torso_front", "torso_back"):
        assign(objs[n], mats["xray_torso"])
        objs[n].visible_shadow = False
    for n in ("head_front", "head_back"):
        assign(objs[n], mats["xray_head"])
        objs[n].visible_shadow = False
    # solid contrasting internals
    for k, mat in mats["cut"].items():
        if k in objs:
            assign(objs[k], mat)
            set_hide(objs[k], False)
    # keep eyes/bezels/pads readable
    for n in ("bezel_L", "bezel_R", "eye_L", "eye_R"):
        set_hide(objs[n], False)
    for n in ("eye_rim_L", "eye_rim_R"):
        if n in objs:
            set_hide(objs[n], True)


# -----------------------------------------------------------------------------
# Render
# -----------------------------------------------------------------------------
def configure_render(preview, samples, width):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_min_samples = 16 if preview else 32
    sc.cycles.adaptive_threshold = 0.03 if preview else 0.01
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.denoising_prefilter = "ACCURATE" if not preview else "FAST"
    sc.cycles.use_denoising_albedo = True
    sc.cycles.use_denoising_normal = True
    try:
        sc.cycles.denoising_use_gpu = False
    except Exception:
        pass
    sc.cycles.max_bounces = 8
    sc.cycles.transparent_max_bounces = 8
    sc.cycles.transmission_bounces = 8
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 4
    sc.cycles.volume_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.hair_type = "STRIP"
    sc.cycles.hair_subdivisions = 2 if preview else 3
    sc.render.resolution_x = width
    sc.render.resolution_y = int(width * 3 / 4)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.compression = 15
    sc.render.film_transparent = False
    sc.render.threads_mode = "AUTO"
    # Colour management
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = 0.05
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.cycles.film_exposure = 1.0


def render_shot(path):
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    print(f"RENDER -> {path}", flush=True)
    bpy.ops.render.render(write_still=True)
    print(f"WROTE {path} exists={Path(path).exists()} size={Path(path).stat().st_size if Path(path).exists() else 0}", flush=True)


HANG_Z = 132.0     # mm: lift of the robot hip origin in the hanging hero shot
BAG_TOP = 104.0    # mm: top edge of the tote bag under the hanging robot
ARC_R = 40.0       # mm: radius of the handle arch


def hang_matrix():
    """Whole-robot pose for hanging on a strap: lean back 14° so the groove line is vertical, then lift."""
    return Matrix.Translation(mm(0, 0, HANG_Z)) @ Matrix.Rotation(-math.atan(G_SLOPE), 4, "X")


def handle_axis_world():
    """Point on the Ø12.5 handle centre line (world, mm) and its x, after hang_matrix()."""
    ga = math.atan(G_SLOPE)
    r = HANDLE_D / 2.0
    c = Vector((0.0, GF - r * math.cos(ga), 30.0 - r * math.sin(ga)))
    w = hang_matrix() @ (c * S)
    top = hang_matrix() @ (Vector((0.0, GF - G_SLOPE * (GZ1 - 30.0) - r * math.cos(ga), GZ1 - r * math.sin(ga))) * S)
    return w / S, top / S


def make_handle_and_bag():
    """A curved round bag handle (Ø12.5) running through the belly groove, arching over to the
    robot's right, both legs stitched into the top of a leather tote under the robot."""
    p, top = handle_axis_world()
    y = p.y
    za = top.z + 4.0                      # arch starts just above the groove
    pts = [(0.0, BAG_TOP - 6.0), (0.0, za)]
    for i in range(1, 24):
        t = math.pi * i / 24.0
        pts.append((-ARC_R + ARC_R * math.cos(t), za + ARC_R * math.sin(t)))
    pts += [(-2 * ARC_R, za), (-2 * ARC_R, BAG_TOP - 6.0)]
    cd = bpy.data.curves.new("bag_handle_curve", "CURVE")
    cd.dimensions = "3D"
    sp = cd.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, (x, z) in enumerate(pts):
        sp.points[i].co = (x * S, y * S, z * S, 1.0)
    cd.bevel_depth = HANDLE_D / 2.0 * S
    cd.bevel_resolution = 6
    cd.use_fill_caps = True
    handle = bpy.data.objects.new("bag_handle", cd)
    bpy.context.scene.collection.objects.link(handle)
    # smooth the polyline corners a little
    sm = handle.modifiers.new("handle_subsurf", "SUBSURF")
    sm.levels = 1
    sm.render_levels = 2
    leather = mat_plastic("HandleLeather", srgb_lin((112, 62, 30)), rough=0.48, spec=0.35)
    handle.data.materials.append(leather)
    # tote body
    x0, x1 = -2 * ARC_R - 34.0, 34.0
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=mm((x0 + x1) / 2, y + 4.0, BAG_TOP / 2))
    bag = bpy.context.active_object
    bag.name = "tote_bag"
    bag.scale = mm(x1 - x0, 58.0, BAG_TOP)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bv = bag.modifiers.new("bag_bevel", "BEVEL")
    bv.width = 0.006
    bv.segments = 6
    for poly in bag.data.polygons:
        poly.use_smooth = True
    assign(bag, mat_plastic("ToteCanvas", srgb_lin((58, 70, 82)), rough=0.8, spec=0.15))
    return [handle, bag]


def set_camera(target_mm, offset_mm, lens):
    cam = bpy.context.scene.camera
    target = mm(*target_mm)
    loc = target + mm(*offset_mm)
    cam.location = loc
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    bpy.context.view_layer.update()


LIGHTS = ("key", "fill", "rim", "top")


def shift_lights(dz_mm):
    for n in LIGHTS:
        o = bpy.data.objects.get(n)
        if o:
            o.location.z += dz_mm * S


def main():
    args = parse_args()
    preview = bool(args.preview) and not bool(args.final)
    if args.width:
        width = args.width
    else:
        width = 800 if preview else 1600
    if args.samples:
        samples = args.samples
    else:
        samples = 24 if preview else 128

    print(f"=== Tomo (evoKin V.01) blender  preview={preview} width={width} samples={samples} shot={args.shot}", flush=True)
    reset_scene()
    objs, mats = build_assembly(skip_hair=args.skip_hair, preview=preview)
    stash_rest(objs)
    print("=== rest bounds (m) ===", flush=True)
    for name in ("torso_front", "head_front", "arm_L", "fur_torso", "fur_head", "bezel_L", "eye_L"):
        o = objs.get(name)
        if not o:
            print(" missing", name); continue
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
        print(f"  {name:16s} {min(xs):7.3f}..{max(xs):7.3f}  {min(ys):7.3f}..{max(ys):7.3f}  {min(zs):7.3f}..{max(zs):7.3f}", flush=True)
    build_studio()
    build_camera()
    cutter = build_cutter()
    for n in ("torso_front", "torso_back", "head_front", "head_back",
              "fur_proxy_torso"):
        if n in objs:
            add_boolean_cut(objs[n], cutter)
    configure_render(preview, samples, width)

    OUT.mkdir(parents=True, exist_ok=True)
    # save an unposed-ready blend once the studio is up (will re-save after)
    tag = "preview" if preview else "final"
    shots = ["hero_hug", "arms_open", "cutaway"] if args.shot == "all" else [args.shot]
    props = make_handle_and_bag()
    CAM0 = ((0, -10, 72), (240, -460, 158), 80)

    def show_props(on):
        for o in props:
            o.hide_render = not on
            o.hide_viewport = not on

    for shot in shots:
        show_props(False)
        GLOBAL[0] = None
        set_camera(*CAM0)
        if shot == "hero_hug":
            # hanging on a Ø12.5 round bag handle: handle in the belly groove, paws closed on it
            GLOBAL[0] = hang_matrix()
            apply_pose_v2(objs, yaw=-12, arm_l=HUG_OPEN, arm_r=HUG_OPEN, tilt=4)
            show_props(True)
            set_cutters(objs, False)
            set_mode_hero(objs)
            set_camera((-26, -20, HANG_Z + 56), (200, -520, 110), 60)
            shift_lights(HANG_Z)
            path = OUT / ("01_hero_hug_handle_preview.png" if preview else "01_hero_hug_handle.png")
            render_shot(path)
            shift_lights(-HANG_Z)
            continue
        elif shot == "arms_open":
            # paws pulled open to the 40° stop by hand, head panned and looking up
            apply_pose_v2(objs, yaw=20, arm_l=ARM_OPEN, arm_r=ARM_OPEN, tilt=-8)
            set_cutters(objs, False)
            set_mode_hero(objs)
            set_camera((0, -16, 70), (240, -460, 158), 72)
            path = OUT / ("02_arms_open_preview.png" if preview else "02_arms_open.png")
        else:
            apply_pose_v2(objs, yaw=0, arm_l=0, arm_r=0, tilt=8)
            set_mode_cutaway(objs, mats)
            set_cutters(objs, True)
            path = OUT / ("03_cutaway_hinge_tilt_preview.png" if preview else "03_cutaway_hinge_tilt.png")
        render_shot(path)

    # save the blend in the hanging hero pose
    GLOBAL[0] = hang_matrix()
    show_props(True)
    apply_pose_v2(objs, yaw=-12, arm_l=HUG_OPEN, arm_r=HUG_OPEN, tilt=4)
    set_cutters(objs, False)
    set_mode_hero(objs)
    set_camera((-26, -20, HANG_Z + 56), (200, -520, 110), 60)
    shift_lights(HANG_Z)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print(f"SAVED {BLEND}", flush=True)


if __name__ == "__main__":
    main()
