# SPDX-License-Identifier: MIT
"""Tomo by DreamMachina: lightening windows in the four egg shells (torso_front/back, head_front/back).

Runs after scripts/build_stl.sh. For each shell it lays a hex grid of Ø12 round windows (16 mm pitch) over the egg
and keeps a window only where the shell is plain wall: inside a Ø18 test disc the part must have the same volume
(±1.5 %) as a plain 2.4 mm egg shell. Every boss, lip, seam edge, ear, groove liner, pocket, hole or grille therefore
keeps a solid land of >= 3 mm round it automatically. The base (z < 12) and the face (eyes, nose window) stay solid;
the fur skin covers the windows. Window list -> results/lightening.json; the posed head copies in check/ get the
same windows so scripts/sim_v01.py can still validate its transforms.
"""
import json, math, os, sys
import numpy as np, trimesh
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
sys.path.insert(0, "scripts")
import groove_geo as gg

D_WIN, PITCH, LAND, TOL = 14.0, 17.5, 3.5, 0.015
WALL = 2.4
ENG = "manifold"

def prof(o, n=96):
    pts = [(0.0, o)]
    for i in range(1, n):
        t = -90 + 180 * i / n
        if t < 0: pts.append(((gg.R - o) * math.cos(math.radians(t)), gg.ZEQ + (gg.ZEQ - o) * math.sin(math.radians(t))))
        else:
            c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
            pts.append(((gg.R - o) * c ** (2 / gg.NUP), gg.ZEQ + (gg.H - gg.ZEQ - o) * s ** (2 / gg.NUP)))
    pts.append((0.0, gg.H - o))
    return np.array(pts)

def solid(o): return trimesh.creation.revolve(prof(o), sections=144)
SHELL = trimesh.boolean.difference([solid(0.0), solid(WALL)], engine=ENG)

def cyl(c, n, r, z0, z1):
    """cylinder radius r along unit n, from c+z0*n to c+z1*n"""
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=32)
    m.apply_translation([0, 0, (z0 + z1) / 2])
    R = trimesh.geometry.align_vectors([0, 0, 1], n)
    m.apply_transform(R); m.apply_translation(c); return m

def vol(a, b):
    try:
        x = trimesh.boolean.intersection([a, b], engine=ENG); return float(x.volume) if len(x.faces) else 0.0
    except Exception: return 0.0

def candidates():
    out = []; z = 12.0 + D_WIN / 2; row = 0
    while z < gg.H - 6:
        r = gg.eggr(z); n = int(2 * math.pi * r // PITCH)
        if n >= 6:
            for k in range(n):
                psi = 360.0 * (k + 0.5 * (row % 2)) / n
                c = gg.on_egg(psi, z); nn = gg.normal(psi, z)
                out.append((psi, z, c, nn))
        # step along the meridian by ~PITCH*0.87 of arc length
        dz = PITCH * 0.866 / math.sqrt(1 + ((gg.eggr(z + 0.5) - gg.eggr(z - 0.5))) ** 2)
        z += max(4.0, dz); row += 1
    return out

def keep_out(part, c):
    x, y, z = c
    if z < 12: return True
    if part == "head_front" and abs(x) < 24 and z < 128: return True      # face: eyes, nose window, camera pod
    return False

def lighten(part, pose=None):
    P = trimesh.load(f"stl/{part}.stl")
    wins = []
    for psi, z, c, n in candidates():
        if keep_out(part, c): continue
        test = cyl(c, n, D_WIN / 2 + LAND, -WALL - 3.0, 1.0)
        if vol(test, P.bounding_box) <= 0: continue
        vs = vol(test, SHELL)
        if vs < 0.5 * math.pi * (D_WIN / 2 + LAND) ** 2 * WALL: continue
        vp = vol(test, P)
        if abs(vp - vs) <= TOL * vs: wins.append(dict(psi=round(psi, 3), z=round(z, 3), c=[float(v) for v in c], n=[float(v) for v in n]))
    return P, wins

def cutters(wins, T=None):
    cs = []
    for w in wins:
        m = cyl(np.array(w["c"]), np.array(w["n"]), D_WIN / 2, -WALL - 1.5, 1.0)
        if T is not None: m.apply_transform(T)
        cs.append(m)
    return trimesh.boolean.union(cs, engine=ENG) if cs else None

def Rm(a, ax, p):
    T = trimesh.transformations.rotation_matrix(a, ax, p); return T

if __name__ == "__main__":
    # optional subset: python3 scripts/lighten_shells.py head_front  (re-lightens only freshly exported parts)
    ALL = ("torso_front", "torso_back", "head_front", "head_back")
    todo = tuple(a for a in sys.argv[1:] if a in ALL) or ALL
    res = {}
    if todo != ALL and os.path.exists("results/lightening.json"):
        res = json.load(open("results/lightening.json")).get("parts", {})
    for part in todo:
        src = f"stl/{part}.stl"
        P, wins = lighten(part)
        v0 = P.volume
        if wins:
            C = cutters(wins); Q = trimesh.boolean.difference([P, C], engine=ENG)
            assert Q.is_watertight
            Q.export(src)
        else: Q = P
        res[part] = dict(windows=len(wins), volume_before_mm3=round(v0, 0), volume_after_mm3=round(Q.volume, 0),
                         removed_pct=round(100 * (1 - Q.volume / v0), 1), list=wins)
        print(part, len(wins), "windows,", round(100 * (1 - Q.volume / v0), 1), "% volume removed")
        # posed copies for the transform validation
        if part.startswith("head") and wins:
            f = f"check/{part}_y30_t10.stl"
            if os.path.exists(f):
                T = Rm(math.radians(30), [0, 0, 1], [0, 0, 0]) @ Rm(math.radians(10), [1, 0, 0], [0, 6.0, 119.0])
                R0 = trimesh.load(f); trimesh.boolean.difference([R0, cutters(wins, T)], engine=ENG).export(f)
    json.dump(dict(window_d_mm=D_WIN, pitch_mm=PITCH, land_mm=LAND, plain_wall_tolerance=TOL,
                   note="Windows only where the shell is plain 2.4 mm wall; the fur skin covers them.", parts=res),
              open("results/lightening.json", "w"), indent=1)
