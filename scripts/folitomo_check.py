# SPDX-License-Identifier: MIT
"""Folitomo skin variant: do the leaf ears, crown sprout, bud and tail leaf clear the rigid parts, the soft sleeves and the
bag handle across the head travel (pan +-42, nod +-10) and the arm travel (0..60)? Reads stl/variants/folitomo/*.stl (build
with scripts/build_variant.sh folitomo) and the default exported parts. Writes results/variants/folitomo/folitomo_check.json.
Soft goods are felt: a contact would only bend a leaf, but the target is still 0 mm3 overlap and a few mm of clearance."""
import numpy as np, trimesh, json, os, sys, time, itertools, math
from trimesh.transformations import rotation_matrix as Rm
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
sys.path.insert(0, "scripts")
import groove_geo as gg
import handle_path
VAR = "folitomo"; V = f"stl/variants/{VAR}/"
OUT = f"results/variants/{VAR}"; os.makedirs(OUT, exist_ok=True)
TOL = 0.05; MIN_CLR = 3.0
YAW_SOFT = (-42, 42); TILT_SOFT = (-10, 10); ARM_TRAVEL = (0, 60)
TILT_AX = np.array([0, 6.0, 119.0])
R_AX = gg.eggr(78) + 8.5; HX = R_AX * math.cos(math.radians(-35)); HY = R_AX * math.sin(math.radians(-35))
HL = np.array([HX, HY, 0.0]); HR = np.array([-HX, HY, 0.0])
ld = lambda p: trimesh.load(p)
HEADV = {n: ld(V + n + ".stl") for n in ("fol_ear_L", "fol_ear_R", "fol_sprout", "fol_bud")}
TAIL = ld(V + "fol_tail.stl")
RIG = "torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer neck_turret tilt_hub head_back head_front arm_L arm_R paw_pad_L paw_pad_R".split()
REF = "dummy_servo_yaw dummy_servo_tilt dummy_horn_yaw dummy_horn_tilt dummy_cam sleeve_proxy_L sleeve_proxy_R fur_proxy_torso soft_body".split()
sys.path.insert(0, "scripts"); from stl_paths import stl_path
M = {n: ld(stl_path(n)) for n in RIG + REF}
TURRET = {"neck_turret", "yaw_coupler", "yaw_retainer_A", "yaw_retainer_B", "dummy_servo_tilt", "dummy_horn_yaw"}
HEAD = {"head_back", "head_front", "tilt_hub", "dummy_cam", "dummy_horn_tilt"}
ARML = {"arm_L", "paw_pad_L", "sleeve_proxy_L"}; ARMR = {"arm_R", "paw_pad_R", "sleeve_proxy_R"}
def T(p, y, t, aL, aR):
    if p in HEAD: return Rm(np.radians(y), [0, 0, 1], [0, 0, 0]) @ Rm(np.radians(t), [1, 0, 0], TILT_AX)
    if p in TURRET: return Rm(np.radians(y), [0, 0, 1], [0, 0, 0])
    if p in ARML: return Rm(np.radians(aL), [0, 0, 1], HL)
    if p in ARMR: return Rm(np.radians(-aR), [0, 0, 1], HR)
    return np.eye(4)
def pose(m, p, y, t, aL, aR): c = m.copy(); c.apply_transform(T(p, y, t, aL, aR)); return c
HT = lambda y, t: Rm(np.radians(y), [0, 0, 1], [0, 0, 0]) @ Rm(np.radians(t), [1, 0, 0], TILT_AX)
# the bag handle: Ø12.5 tube round its centre line; distance from a leaf vertex to the line minus the radius
HP = np.array(handle_path.handle_points(VAR)); HR_ = handle_path.HANDLE_D / 2
def handle_clear(mesh, step=1):
    P = mesh.vertices[::step]; A = HP[:-1]; B = HP[1:]; AB = B - A; L2 = (AB ** 2).sum(1)
    best = 1e9
    for i in range(0, len(P), 400):
        Q = P[i:i + 400, None, :]; t = np.clip(((Q - A) * AB).sum(2) / L2, 0, 1)
        d = np.linalg.norm(Q - (A + t[..., None] * AB), axis=2).min(1); best = min(best, float(d.min()))
    return best - HR_
def mindist(a, b, n=2500):
    pts = a.sample(n, seed=3); bb = b.bounds
    near = np.all((pts > bb[0] - 12) & (pts < bb[1] + 12), axis=1)
    if not near.any(): return 99.0
    d = -trimesh.proximity.signed_distance(b, pts[near]); return float(d.min())
def ov(a, b, pad=0.01): return bool(np.all(a[0] - pad <= b[1]) and np.all(b[0] - pad <= a[1]))
def inter(a, b): return float(trimesh.boolean.intersection([a, b], engine="manifold").volume)
poses = set()
for y in np.arange(-50, 50.01, 2.0): poses.add((round(y, 2), 0.0, 0.0, 0.0))
for t in np.arange(-15, 15.01, 2.5): poses.add((0.0, round(t, 2), 0.0, 0.0))
for y in (-47, -42, -21, 0, 21, 42, 47):
    for t in (-12, -10, -5, 0, 5, 10, 12): poses.add((float(y), float(t), 0.0, 0.0))
for aL in (0, 30, 60):
    for aR in (0, 30, 60):
        for (y, t) in ((-42, 10), (42, -10), (42, 10), (-42, -10), (0, 0)): poses.add((float(y), float(t), float(aL), float(aR)))
poses = sorted(poses); rows = []; npairs = 0; nbool = 0; t0 = time.time(); worst_handle = 1e9; worst_handle_pose = None
# head-borne parts vs everything
for (y, t, aL, aR) in poses:
    HV = {n: m.copy() for n, m in HEADV.items()}
    for m in HV.values(): m.apply_transform(HT(y, t))
    PM = {p: (pose(M[p], p, y, t, aL, aR)) for p in M}
    for n, hm in HV.items():
        h = handle_clear(hm, 2)
        if h < worst_handle: worst_handle, worst_handle_pose = h, (y, t, aL, aR, n)
        for p, pm in PM.items():
            if p in ("soft_body", "fur_proxy_torso"): pass
            npairs += 1
            if not ov(hm.bounds, pm.bounds): continue
            nbool += 1; v = inter(hm, pm)
            if v > TOL: rows.append(dict(yaw=y, tilt=t, armL=aL, armR=aR, a=n, b=p, vol_mm3=round(v, 3)))
# tail leaf (static) vs the arms through the whole arm travel and everything else
tail_rows = []
for aL in np.arange(-5, 70.01, 5.0):
    for aR in np.arange(-5, 70.01, 5.0):
        for p in M:
            pm = pose(M[p], p, 0, 0, float(aL), float(aR))
            npairs += 1
            if not ov(TAIL.bounds, pm.bounds): continue
            nbool += 1; v = inter(TAIL, pm)
            if v > TOL and p not in ("soft_body",): tail_rows.append(dict(armL=float(aL), armR=float(aR), b=p, vol_mm3=round(v, 3)))
# soft-body contact (tail leaf is sewn on: contact with the ball is by design, reported but not a defect), leaf-vs-leaf
sb_tail = inter(TAIL, M["soft_body"])
lv = {}
for a, b in itertools.combinations(HEADV, 2): lv[f"{a}|{b}"] = round(inter(HEADV[a], HEADV[b]), 3)
# minimum clearances (mm) at the extreme poses, per part
clr = {}
for (y, t, aL, aR) in ((0, 0, 0, 0), (42, 10, 0, 0), (-42, 10, 0, 0), (42, -10, 0, 0), (-42, -10, 0, 0), (42, 10, 60, 60), (-42, 10, 60, 60), (0, 10, 60, 60)):
    HV = {n: m.copy() for n, m in HEADV.items()}
    for m in HV.values(): m.apply_transform(HT(y, t))
    row = {}
    for n, hm in HV.items():
        for p in ("torso_front", "arm_L", "arm_R", "sleeve_proxy_L", "sleeve_proxy_R", "soft_body", "neck_turret", "head_front"):
            pm = pose(M[p], p, y, t, aL, aR); d = mindist(hm, pm)
            if d < 30: row[f"{n}_to_{p}"] = round(d, 2)
        row[f"{n}_to_handle"] = round(handle_clear(hm, 2), 2)
    clr[f"yaw{y}_tilt{t}_armL{aL}_armR{aR}"] = row
tail_clr = {}
for a in (0, 60):
    for p in ("arm_L", "arm_R", "sleeve_proxy_L", "sleeve_proxy_R", "torso_back"):
        tail_clr[f"{p}_at_arms_{a}"] = round(mindist(TAIL, pose(M[p], p, 0, 0, a, a)), 2)
tail_clr["tail_to_handle"] = round(handle_clear(TAIL, 1), 2)
inT = lambda r: YAW_SOFT[0] <= r["yaw"] <= YAW_SOFT[1] and TILT_SOFT[0] <= r["tilt"] <= TILT_SOFT[1] and ARM_TRAVEL[0] <= r["armL"] <= ARM_TRAVEL[1] and ARM_TRAVEL[0] <= r["armR"] <= ARM_TRAVEL[1]
all_in = [r for r in rows if inT(r)]
out = dict(variant=VAR, tolerance_mm3=TOL, poses=len(poses), pair_tests=npairs, aabb_passed_to_boolean=nbool, seconds=round(time.time() - t0, 1),
           pose_grid="yaw -50..50 step 2 and tilt -15..15 step 2.5 singly; yaw {-47,-42,-21,0,21,42,47} x tilt {-12,-10,-5,0,5,10,12}; arms {0,30,60}^2 at 5 head corners; tail leaf: both arms -5..70 step 5",
           head_leaf_overlaps_in_soft_travel=all_in, head_leaf_overlaps_all=rows, tail_leaf_overlaps=tail_rows,
           tail_leaf_vs_soft_body_mm3_by_design=round(sb_tail, 3), leaf_vs_leaf_mm3=lv,
           min_clearance_mm=clr, tail_clearance_mm=tail_clr,
           worst_handle_clearance_mm=dict(value=round(worst_handle, 2), at=dict(zip(("yaw", "tilt", "armL", "armR", "part"), worst_handle_pose))),
           note="Leaves are 1.2 mm felt on a 0.6 mm wire rib: a brush would only bend them. The handle is the Ø12.5 tube of the renders (scripts/handle_path.py). Leaf bases are tucked into the head-ball / body skin on purpose (not counted).")
out["ok"] = (not all_in) and (not tail_rows) and worst_handle >= MIN_CLR
json.dump(out, open(f"{OUT}/folitomo_check.json", "w"), indent=1, default=float)
print(json.dumps({k: out[k] for k in ("poses", "pair_tests", "head_leaf_overlaps_in_soft_travel", "tail_leaf_overlaps", "worst_handle_clearance_mm", "tail_clearance_mm", "leaf_vs_leaf_mm3", "ok", "seconds")}, indent=1, default=float))
