# SPDX-License-Identifier: MIT
#!/usr/bin/env python3
"""Photoreal Cycles renders of Tomo by DreamMachina (formerly evoKin V.01): long-pile ivory / pink plush,
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
# One egg of revolution (cad/evokin_v01.scad begg): R 46 at z 58, ellipse below, superellipse n=3.4 above, top z 148
R_EGG, ZEQ, H_EGG, N_UP = 46.0, 58.0, 148.0, 3.4


def eggr(z, o=0.0):
    if z < ZEQ:
        b = ZEQ - o
        u = (z - ZEQ) / b
        return (R_EGG - o) * math.sqrt(max(0.0, 1 - u * u))
    a = H_EGG - ZEQ - o
    u = abs(z - ZEQ) / a
    return (R_EGG - o) * max(0.0, 1 - u ** N_UP) ** (1 / N_UP)


SEAM_C, SEAM_Z = 119.0, 101.0
SEAM_R = math.hypot(eggr(SEAM_Z), SEAM_C - SEAM_Z)   # face-cap seam sphere, centre (0, 0, 119)
EYE_X, EYE_Z = 10.5, 114.0      # lighter Tomo: 8 mm safety eyes, set lower and closer (cad eye_x / eye_z)
EYE_SKIN_Y = -math.sqrt(eggr(EYE_Z) ** 2 - EYE_X ** 2)   # ≈ -41.8
NOSE_Z = 110.0                   # camera 'nose' window (cad nose_z)
NOSE_SKIN_Y = -eggr(NOSE_Z)
FUR_BASE = 2.0                   # fur backing sits this far outside the printed shell (mm)
_RAX = eggr(78.0) + 8.5
HL = (_RAX * math.cos(math.radians(-35)), _RAX * math.sin(math.radians(-35)), 0.0)   # left SHOULDER hinge (vertical)
HR = (-HL[0], HL[1], 0.0)
TILT_AX = (0.0, 6.0, 119.0) # head tilt axis along x through y=6, z=119 (+ = nose down)
REST_L, REST_R = 0.0, 0.0   # STL export pose: arms closed on their rest stops
ARM_OPEN = 60.0             # open stop (thick-arm pass; was 30)
# centre belly groove (two-arms pass): floor line G_FR + t*G_U (scripts/groove_geo.py), outward normal G_N, capsule t -12..42, R8
G_FR = Vector((0.0, -38.7962, 32.9239))
G_U = Vector((0.0, -0.1025, 0.9947))
G_N = Vector((0.0, -0.9947, -0.1025))
G_T0, G_T1, GR = -12.0, 42.0, 8.0
G_MIDT = 15.0
HANDLE_D = 12.5             # round bag handle
try:
    import json as _json
    _G = _json.load(open(ROOT / "results" / "summary_sweep.json"))["hug"]["grip"]
    _g = next(g for g in _G if g.get("d_mm") == HANDLE_D)
    HUG_OPEN_L, HUG_OPEN_R = _g["L"]["open_deg"], _g["R"]["open_deg"]
except Exception:
    HUG_OPEN_L, HUG_OPEN_R = 6.75, 6.34   # arm openings on a Ø12.5 handle (sim_v01.py)

HEAD_PARTS = {
    "head_back", "head_front", "tilt_hub", "dummy_cam", "dummy_horn_tilt",
    "eye_L", "eye_R", "nose", "fur_head",
}
TURRET_PARTS = {"neck_turret", "yaw_coupler", "yaw_retainer_A", "yaw_retainer_B",
                "dummy_servo_tilt", "dummy_horn_yaw"}

ARM_L_PARTS = {"arm_L", "paw_pad_L", "sleeve_proxy_L", "fur_arm_L"}
ARM_R_PARTS = {"arm_R", "paw_pad_R", "sleeve_proxy_R", "fur_arm_R"}
GLOBAL = [None]             # optional whole-robot matrix (hanging pose)

# Mirumi-like colourways (sRGB albedo; AgX lifts pale tones, so keep them a touch darker than the target)
PALETTES = {
    "ivory": dict(fur=(222, 206, 180), tip=(240, 232, 214), root=(172, 150, 120), pad=(176, 156, 128)),
    "pink":  dict(fur=(236, 172, 186), tip=(248, 208, 218), root=(196, 124, 140), pad=(196, 124, 140)),
}

# (legacy note) AgX + studio lights wash mid tones out,
# so the albedo is deliberately darker and redder than the target grade.
FUR_SRGB = PALETTES["ivory"]["fur"]
FUR_TIP_SRGB = PALETTES["ivory"]["tip"]
FUR_ROOT_SRGB = PALETTES["ivory"]["root"]


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
                   choices=["all", "hero_hug", "arms_open", "mirumi_angle", "cutaway"])
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


def _groove_local(p):
    """(t along the floor line, n along G_N from the capsule axis, w across) for a point in mm."""
    q = Vector(p) - G_FR
    t = q.dot(G_U)
    tc = min(max(t, G_T0), G_T1)
    c = G_FR + G_U * tc + G_N * GR                   # capsule axis point
    d = Vector(p) - c
    return t, tc, d.dot(G_N), d - G_N * d.dot(G_N), c


def torso_fur_ok(pt):
    x, y, z = pt
    if z < -2:
        return False
    # centre belly groove: keep the channel bare so a handle sits in it
    t, tc, dn, dw, c = _groove_local(pt)
    if (Vector(pt) - c).length < GR + 2.0 and y < -10:
        return False
    # shoulder knuckles stay under the coat (Mirumi: no visible hardware)
    return True


def groove_fur_emitter(obj):
    """Press a channel into the body fur egg along the centre belly groove."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    inv = mw.inverted()
    rr = GR + 1.0                                     # 1 mm of pile on the liner
    for v in bm.verts:
        w = mw @ v.co
        p = (w.x / S, w.y / S, w.z / S)
        if p[1] > -10:
            continue
        t, tc, dn, dw, c = _groove_local(p)
        dt = t - tc
        q = rr * rr - dw.length_squared - dt * dt
        if q <= 0:
            continue
        nb = -math.sqrt(q)                            # back wall of the channel along G_N
        if dn > nb:
            np_ = Vector(p) - G_N * (dn - nb)
            v.co = inv @ (np_ * S)
    bm.to_mesh(obj.data)
    obj.data.update()
    bm.free()


def make_egg_fur(name, o, part, segments=128, rings=96):
    """Fur emitter on the egg of revolution offset o (negative = outside the shell), split at the seam sphere:
    part='body' keeps what is outside SEAM_R+1.5, part='cap' what is inside SEAM_R-1.5 (rides with the head)."""
    import bmesh

    def seam_dist(z):
        return math.hypot(eggr(z, o), SEAM_C - z)
    # body coat stops 1.5 mm outside the seam sphere; the cap coat is a soft lip that runs 3 mm PAST the seam,
    # a hair outside the body coat, so the 3 mm running gap is always covered (it slides over the body pile)
    lim = SEAM_R + 1.5 if part == "body" else SEAM_R + 3.0
    # find the seam height on this offset egg
    lo, hi = 60.0, H_EGG - o - 0.01
    for _ in range(60):
        mid = (lo + hi) / 2
        if seam_dist(mid) > lim:
            lo = mid
        else:
            hi = mid
    zs = (lo + hi) / 2
    z0, z1 = (o, zs) if part == "body" else (zs, H_EGG - o)
    # profile samples in the superellipse/ellipse parameter so the poles are dense enough
    prof = []
    for k in range(rings + 1):
        z = z0 + (z1 - z0) * (0.5 - 0.5 * math.cos(math.pi * k / rings))
        prof.append((eggr(z, o), z))
    bm = bmesh.new()
    ringsv = []
    for (r, z) in prof:
        if r < 1e-3:
            ringsv.append([bm.verts.new((0, 0, z * S))])
            continue
        ringsv.append([bm.verts.new((r * math.cos(2 * math.pi * k / segments) * S,
                                     r * math.sin(2 * math.pi * k / segments) * S, z * S)) for k in range(segments)])
    for a, b in zip(ringsv[:-1], ringsv[1:]):
        if len(a) == 1 and len(b) > 1:
            for k in range(segments):
                bm.faces.new((a[0], b[(k + 1) % segments], b[k]))
        elif len(b) == 1 and len(a) > 1:
            for k in range(segments):
                bm.faces.new((a[k], a[(k + 1) % segments], b[0]))
        else:
            for k in range(segments):
                bm.faces.new((a[k], a[(k + 1) % segments], b[(k + 1) % segments], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def head_fur_ok(pt):
    """Weight 1 everywhere on the head except small trimmed wells round the eyes and the nose (Mirumi trims its face)."""
    x, y, z = pt
    w = 1.0
    if y < 5.0:
        for (cx, cz, r0, r1) in ((EYE_X, EYE_Z, 4.6, 8.0), (-EYE_X, EYE_Z, 4.6, 8.0), (0.0, NOSE_Z, 2.6, 5.5)):
            r = ((x - cx) ** 2 + (z - cz) ** 2) ** 0.5
            if r < r0:
                return 0.0
            if r < r1:
                w = min(w, 0.15 + 0.85 * (r - r0) / (r1 - r0))
    return w


# -----------------------------------------------------------------------------
# Hair
# -----------------------------------------------------------------------------
DROOP = [0.55]


def _arm_flow(hinge, tip_psi, tip_z, tip_off, k=1.1, droop=0.35):
    r = eggr(tip_z) + tip_off
    tip = (r * math.cos(math.radians(tip_psi)), r * math.sin(math.radians(tip_psi)), tip_z)
    d = [tip[i] - hinge[i] for i in range(3)]
    n = math.sqrt(sum(c * c for c in d))
    return (k * d[0] / n, k * d[1] / n, k * d[2] / n - droop)


# shoulder -> mitten direction in the arm's rest frame (symmetric paths end at [-82.5, 48, 5.3] / [-97.5, 48, 5.3] in cad)
ARM_FLOW = {"L": _arm_flow((44.58, -31.21, 78.0), -82.5, 48, 5.3), "R": _arm_flow((-44.58, -31.21, 78.0), -97.5, 48, 5.3)}


def add_hair(obj, name, length_m, count, children, material,
             clump=0.55, rough=0.10, kink_amp=0.04, kink_freq=4.0,
             length_rand=0.18, density_vg=None, root_m=0.00040, tip_m=0.00010, align=None):
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
    # comb the pile downwards so it drapes like plush (and the cap coat falls over the face seam).
    # hair_length only rescales normal_factor, so set it first and give the downward comb in the same units
    # (strand length grows by ~sqrt(1 + DROOP^2); the lengths below already allow for it).
    al = align if align is not None else (0.0, 0.0, -DROOP[0])
    ps.hair_length = length_m / (1.0 + sum(c * c for c in al)) ** 0.5
    ps.object_align_factor = tuple(c * ps.normal_factor for c in al)
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


def place_eye(name, sx):
    """8 mm glossy black safety eye: a 4 mm-radius dome sitting on the trimmed fur backing."""
    _deselect()
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=40, ring_count=20, radius=0.0036,
        location=mm(sx * EYE_X, EYE_SKIN_Y - FUR_BASE - 1.0, EYE_Z),
    )
    obj = bpy.context.active_object
    obj.name = name
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def place_nose(name):
    """Tiny dark nose over the Ø3.5 camera window."""
    obj = make_uv_sphere(name, mm(0.0, NOSE_SKIN_Y - FUR_BASE - 0.6, NOSE_Z), (0.0024, 0.0013, 0.0017), 32, 16)
    return obj


def place_foot(name, sx):
    """Stubby plush foot sewn to the skin at the bottom front (soft goods, no hardware)."""
    return make_uv_sphere(name, mm(sx * 15.0, -30.0, 6.5), (0.0095, 0.0125, 0.0065), 40, 20)


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


def make_solid_arm_emitter(src, name, inflate=0.0020):
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
    inflate_mesh(em, inflate)
    for p in em.data.polygons:
        p.use_smooth = True
    return em


def build_assembly(skip_hair=False, preview=False):
    objs = {}
    for name, fn in PART_FILES.items():
        objs[name] = import_stl(resolve_stl(fn), name)

    objs["eye_L"] = place_eye("eye_L", +1)
    objs["eye_R"] = place_eye("eye_R", -1)
    objs["nose"] = place_nose("nose")
    objs["fur_foot_L"] = place_foot("fur_foot_L", +1)
    objs["fur_foot_R"] = place_foot("fur_foot_R", -1)

    # ---- materials (hero defaults; cutaway swaps later)
    mats = {}
    mats["print_body"] = mat_plastic("PrintBody", srgb_lin((226, 130, 52)), rough=0.45)
    mats["print_head"] = mat_plastic("PrintHead", srgb_lin((232, 180, 80)), rough=0.45)
    mats["print_dark"] = mat_plastic("PrintDark", srgb_lin((50, 44, 40)), rough=0.4)
    mats["print_bracket"] = mat_plastic("PrintBracket", srgb_lin((42, 46, 50)), rough=0.38)
    mats["nose"] = mat_plastic("Nose", srgb_lin((34, 22, 20)), rough=0.3, spec=0.5)
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
    assign(objs["paw_pad_L"], mats["pad"])
    assign(objs["paw_pad_R"], mats["pad"])
    assign(objs["nose"], mats["nose"])
    assign(objs["fur_foot_L"], mats["fur_clay"])
    assign(objs["fur_foot_R"], mats["fur_clay"])
    assign(objs["eye_L"], mats["eye"])
    assign(objs["eye_R"], mats["eye"])
    for k in ("tray", "yaw_collar", "yaw_coupler", "yaw_retainer_A", "yaw_retainer_B",
              "yaw_thrust_washer", "neck_turret", "tilt_hub"):
        assign(objs[k], mats["print_dark"])
    for k in list(CUT_COLORS):
        if k in objs:
            # keep hero mats; cutaway reassigns
            pass

    # ---- fur emitters: the one egg (begg(-4)) split at the face-cap seam sphere. The cap coat rides with the head.
    fur_t = make_egg_fur("fur_torso", -FUR_BASE, "body", segments=160 if not preview else 112, rings=110 if not preview else 70)
    groove_fur_emitter(fur_t)
    assign(fur_t, mats["fur_clay"])
    vg_t = density_group(fur_t, "fur_density", torso_fur_ok)
    objs["fur_torso"] = fur_t

    fur_h = make_egg_fur("fur_head", -FUR_BASE - 0.8, "cap", segments=128 if not preview else 96, rings=48 if not preview else 32)
    assign(fur_h, mats["fur_clay"])
    # Do not punch holes in the head mesh: hair is kept off the eyeballs with a soft density well instead;
    # the glossy spheres sit proud of the coat like safety eyes.
    vg_h = density_group(fur_h, "fur_density", head_fur_ok)
    objs["fur_head"] = fur_h

    # arm fur: use a slightly inflated copy of sleeve + a paw-region sphere-ish
    # by emitting from the sleeve proxies and the arm solids with a density
    # group that kills the pulley hub (near the pivot).
    from mathutils import kdtree

    def arm_fur_ok_side(side):
        pad = objs[f"paw_pad_{side}"]
        pv = [pad.matrix_world @ v.co for v in pad.data.vertices]
        kd = kdtree.KDTree(len(pv))
        for k, v in enumerate(pv):
            kd.insert(v / S, k)
        kd.balance()

        def pred(pt):
            x, y, z = pt
            # Knuckle furred over (no visible hardware); only the TPU pads at the handle crossings stay short.
            _, _, dist = kd.find(Vector(pt))
            if dist < 2.0:
                return 0.0
            if dist < 6.0:
                return 0.5
            return 1.0
        return pred

    for side in ("L", "R"):
        # Thick Mirumi-style arm: emit from the stuffed soft-sleeve proxy (Ø16–21 mm tube, shoulder cap, mitten paw)
        src = objs[f"sleeve_proxy_{side}"]
        em = make_solid_arm_emitter(src, f"fur_arm_{side}", inflate=0.0003)
        assign(em, mats["fur_clay"])
        vg = density_group(em, "fur_density", arm_fur_ok_side(side))
        objs[f"fur_arm_{side}"] = em
        objs[f"_vg_arm_{side}"] = vg

    objs["_vg_torso"] = vg_t
    objs["_vg_head"] = vg_h

    # Hair counts: preview uses fewer parents / children
    if not skip_hair:
        mul_c = 0.55 if preview else 1.35
        mul_k = 1.0
        # Long, soft, dense pile (Mirumi-like): a 7 mm undercoat and 11–12 mm guard hairs combed down; feet too.
        add_hair(fur_t, "torso_under", length_m=0.0085, count=int(16000 * mul_c),
                 children=int(10 * mul_k) or 6, material=mats["fur_under"],
                 clump=0.35, rough=0.18, kink_amp=0.08, kink_freq=4,
                 density_vg=vg_t, root_m=0.00015, tip_m=0.00004)
        add_hair(fur_t, "torso_guard", length_m=0.0175, count=int(9000 * mul_c),
                 children=int(9 * mul_k) or 5, material=mats["fur_guard"],
                 clump=0.65, rough=0.32, kink_amp=0.25, kink_freq=2.5,
                 density_vg=vg_t, root_m=0.00011, tip_m=0.00002)
        add_hair(fur_h, "head_under", length_m=0.0080, count=int(10000 * mul_c),
                 children=int(10 * mul_k) or 6, material=mats["fur_under"],
                 clump=0.35, rough=0.16, kink_amp=0.08, kink_freq=4,
                 density_vg=vg_h, root_m=0.00014, tip_m=0.00004)
        add_hair(fur_h, "head_guard", length_m=0.0170, count=int(6500 * mul_c),
                 children=int(9 * mul_k) or 5, material=mats["fur_guard"],
                 clump=0.62, rough=0.30, kink_amp=0.22, kink_freq=2.5,
                 density_vg=vg_h, root_m=0.00010, tip_m=0.00002)
        for side in ("L", "R"):
            em = objs[f"fur_arm_{side}"]
            vg = em.vertex_groups["fur_density"]
            # groom: lay the pile along the arm toward the mitten paw (plus a little droop)
            al = ARM_FLOW[side]
            add_hair(em, f"arm_{side}_under", length_m=0.0060, count=int(12000 * mul_c),
                     children=int(8 * mul_k) or 5, material=mats["fur_under"],
                     clump=0.35, rough=0.14, kink_amp=0.06, kink_freq=4,
                     density_vg=vg, root_m=0.00013, tip_m=0.00004, align=al)
            add_hair(em, f"arm_{side}_guard", length_m=0.0100, count=int(7000 * mul_c),
                     children=int(8 * mul_k) or 4, material=mats["fur_guard"],
                     clump=0.6, rough=0.26, kink_amp=0.18, kink_freq=2.5,
                     density_vg=vg, root_m=0.00010, tip_m=0.00002, align=al)
        for side in ("L", "R"):
            ft = objs[f"fur_foot_{side}"]
            add_hair(ft, f"foot_{side}", length_m=0.0080, count=int(2500 * mul_c),
                     children=8, material=mats["fur_guard"], clump=0.4, rough=0.25, kink_amp=0.15, kink_freq=3,
                     root_m=0.00011, tip_m=0.00003)

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
    "eye_L", "eye_R", "nose", "fur_foot_L", "fur_foot_R",
    "studio_ground", "studio_back",
}
# hide raw printed shells and internals on the finished look
HERO_HIDE = {
    "torso_front", "torso_back", "head_front", "head_back",
    "tray", "yaw_collar", "yaw_coupler", "yaw_retainer_A", "yaw_retainer_B",
    "yaw_thrust_washer",
    "neck_turret", "tilt_hub",
    "arm_L", "arm_R", "sleeve_proxy_L", "sleeve_proxy_R",
    "fur_proxy_torso",
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
    for n in ("eye_L", "eye_R", "nose"):
        if n in objs:
            set_hide(objs[n], False)
            set_emitter_visible(objs[n], True)


def set_mode_cutaway(objs, mats):
    for name, obj in objs.items():
        if name.startswith("_") or not hasattr(obj, "hide_render"):
            continue
        # no hair in the cutaway — it obscures the internals
        enable_hair(obj, False)
        if name in CUT_HIDE or name.startswith("fur_arm") or name.startswith("fur_foot") or name in ("fur_torso", "fur_head"):
            # show the designed fur_proxy as the transparent coat; hide GN ellipsoids
            if name in ("fur_torso", "fur_head"):
                set_hide(obj, True)
                continue
            if name.startswith("fur_arm") or name.startswith("fur_foot"):
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
    # keep eyes/nose/pads readable
    for n in ("eye_L", "eye_R", "nose"):
        set_hide(objs[n], False)


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


BAG_TOP = 96.0     # mm: top of the tote; Tomo sits on it (Mirumi pose) and hugs the handle's upright leg
LEAN = math.degrees(math.atan2(-G_U.y, G_U.z))   # ≈5.9 deg: tips back so the groove line (and the handle leg) is vertical


def seat_matrix():
    """Whole-robot pose: sitting on the bag top, tipped back ≈6° so the handle upright in its belly groove is vertical."""
    return Matrix.Translation(mm(0, 0, BAG_TOP)) @ Matrix.Rotation(math.radians(-LEAN), 4, "X")


def handle_points():
    """Robot-frame centre line of a Ø12.5 bag handle: its upright leg rises out of the bag top straight up the centre
    belly groove between the two paws, then (above the paws) bends away over the robot's right shoulder (-x), bowing
    forward to clear the face, arches over and drops back into the bag on the far side, like Mirumi on a tote."""
    pts = []
    r = HANDLE_D / 2.0 + 0.15
    T1 = 26.0                                           # leave the groove line here (z ≈ 59, above the paws)
    for k in range(0, 41):
        t = -40.0 + (T1 + 40.0) * k / 40.0
        pts.append(G_FR + G_U * t + G_N * r)
    p0 = pts[-1]
    RB = 62.0
    for k in range(1, 61):
        ph = math.pi * k / 60.0
        bow = 20.0 * math.sin(min(ph, math.pi / 2))     # forward bow off the face, held on the far side
        q = Vector((-RB + RB * math.cos(ph), p0.y - bow, p0.z + RB * math.sin(ph)))
        if ph > math.pi / 2:
            q.y = (p0.y - 20.0) + ((-12.0) - (p0.y - 20.0)) * ((ph - math.pi / 2) / (math.pi / 2))
        pts.append(q)
    last = pts[-1]
    for k in range(1, 13):
        pts.append(Vector((last.x, last.y, last.z - (last.z + 8.0) * k / 12.0)))
    return pts


def make_handle_and_bag():
    """A curved leather handle (Ø12.5) and a tote; Tomo sits on the tote and hugs the handle's upright leg."""
    M = seat_matrix()
    cd = bpy.data.curves.new("bag_handle_curve", "CURVE")
    cd.dimensions = "3D"
    sp = cd.splines.new("POLY")
    pts = [M @ (p * S) for p in handle_points()]
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
    cd.bevel_depth = HANDLE_D / 2.0 * S
    cd.bevel_resolution = 6
    cd.use_fill_caps = True
    handle = bpy.data.objects.new("bag_handle", cd)
    bpy.context.scene.collection.objects.link(handle)
    sm = handle.modifiers.new("handle_subsurf", "SUBSURF")
    sm.levels = 1
    sm.render_levels = 2
    leather = mat_plastic("HandleLeather", srgb_lin((24, 22, 22)), rough=0.32, spec=0.5)
    handle.data.materials.append(leather)
    xs = [p.x / S for p in pts]
    x0, x1 = min(xs) - 40.0, max(xs) + 70.0
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=mm((x0 + x1) / 2, -4.0, BAG_TOP / 2))
    bag = bpy.context.active_object
    bag.name = "tote_bag"
    bag.scale = mm(x1 - x0, 100.0, BAG_TOP)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bv = bag.modifiers.new("bag_bevel", "BEVEL")
    bv.width = 0.008
    bv.segments = 8
    for poly in bag.data.polygons:
        poly.use_smooth = True
    assign(bag, mat_plastic("ToteLeather", srgb_lin((30, 28, 28)), rough=0.38, spec=0.45))
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
    for name in ("torso_front", "head_front", "arm_L", "fur_torso", "fur_head", "nose", "eye_L"):
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
    shots = ["hero_hug", "arms_open", "mirumi_angle", "cutaway"] if args.shot == "all" else [args.shot]
    props = make_handle_and_bag()
    CAM0 = ((0, -10, 72), (240, -460, 158), 80)

    def show_props(on):
        for o in props:
            o.hide_render = not on
            o.hide_viewport = not on

    HERO = ((-6, -20, BAG_TOP + 70), (210, -500, 70), 62)
    def set_palette(name):
        P = PALETTES[name]
        for key, col in (("fur_under", P["root"]), ("fur_guard", P["fur"])):
            n = mats[key].node_tree.nodes.get("Principled Hair BSDF")
            if n is None:
                n = next(x for x in mats[key].node_tree.nodes if x.type == "BSDF_HAIR_PRINCIPLED")
            n.inputs["Color"].default_value = srgb_lin(col)
        b = mats["fur_clay"].node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = srgb_lin(P["root"])
            try:
                b.inputs["Sheen Tint"].default_value = srgb_lin(P["tip"])
            except Exception:
                pass
        pb = mats["pad"].node_tree.nodes.get("Principled BSDF")
        if pb:
            pb.inputs["Base Color"].default_value = srgb_lin(P["pad"])

    SHOT_PALETTE = {"hero_hug": "ivory", "arms_open": "ivory", "mirumi_angle": "pink", "cutaway": "ivory"}
    for shot in shots:
        set_palette(SHOT_PALETTE[shot])
        show_props(False)
        GLOBAL[0] = None
        set_camera(*CAM0)
        if shot in ("hero_hug", "mirumi_angle"):
            # sitting on the tote, both arms closed round the upright Ø12.5 handle leg in the centre belly groove
            GLOBAL[0] = seat_matrix()
            apply_pose_v2(objs, yaw=-14 if shot == "hero_hug" else -8, arm_l=HUG_OPEN_L, arm_r=HUG_OPEN_R,
                          tilt=4 if shot == "hero_hug" else 2)
            show_props(True)
            set_cutters(objs, False)
            set_mode_hero(objs)
            if shot == "hero_hug":
                set_camera(*HERO)
                path = OUT / ("01_hero_hug_handle_preview.png" if preview else "01_hero_hug_handle.png")
            else:
                # roughly the framing of Mirumi's product photo: front-on, slightly from its left, at chest height
                set_camera((-12, -10, BAG_TOP + 66), (70, -560, 10), 58)
                path = OUT / ("03_mirumi_angle_preview.png" if preview else "03_mirumi_angle.png")
            shift_lights(BAG_TOP)
            render_shot(path)
            shift_lights(-BAG_TOP)
            continue
        elif shot == "arms_open":
            # arms pulled open to the 60° stop by hand, head panned (tilt 0: looking up opens the fur seam)
            apply_pose_v2(objs, yaw=20, arm_l=ARM_OPEN, arm_r=ARM_OPEN, tilt=0)
            set_cutters(objs, False)
            set_mode_hero(objs)
            set_camera((0, -18, 76), (230, -470, 150), 66)
            path = OUT / ("02_arms_open_preview.png" if preview else "02_arms_open.png")
        else:
            apply_pose_v2(objs, yaw=0, arm_l=0, arm_r=0, tilt=8)
            set_mode_cutaway(objs, mats)
            set_cutters(objs, True)
            set_camera((0, -10, 76), (240, -460, 170), 74)
            path = OUT / ("04_cutaway_shoulder_tilt_preview.png" if preview else "04_cutaway_shoulder_tilt.png")
        render_shot(path)

    # save the blend in the seated hero pose
    set_palette("ivory")
    GLOBAL[0] = seat_matrix()
    show_props(True)
    apply_pose_v2(objs, yaw=-14, arm_l=HUG_OPEN_L, arm_r=HUG_OPEN_R, tilt=4)
    set_cutters(objs, False)
    set_mode_hero(objs)
    set_camera(*HERO)
    shift_lights(BAG_TOP)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print(f"SAVED {BLEND}", flush=True)


if __name__ == "__main__":
    main()
