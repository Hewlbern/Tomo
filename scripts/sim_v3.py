# SPDX-License-Identifier: MIT
"""critter v3 reproducible verification: imposed-motion kinematics on the EXPORTED v3 STLs.
Not dynamics. No contact mechanics, no cord stretch, no friction, no print tolerance, no soft-body."""
import numpy as np, trimesh, json, csv, itertools, time, os
from trimesh.transformations import rotation_matrix as Rm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
P=json.load(open("results/design_params.json"))
TOL=0.05
PRINTED="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer head_back head_front arm_L arm_R shoulder_bracket_L shoulder_bracket_R clasp_drum".split()
PROXY="paw_pad_L paw_pad_R sleeve_proxy_L sleeve_proxy_R fur_proxy_torso strap_env".split()
DUMMIES="dummy_servo_yaw dummy_servo_clasp dummy_horn_yaw dummy_horn_clasp dummy_pi dummy_cam dummy_speaker dummy_amp dummy_mic".split()
M={p:trimesh.load(stl_path(p)) for p in PRINTED+PROXY+DUMMIES}
HEAD=["head_back","head_front","yaw_coupler","yaw_retainer_A","yaw_retainer_B","dummy_cam"]
ARML=["arm_L","paw_pad_L","sleeve_proxy_L"]; ARMR=["arm_R","paw_pad_R","sleeve_proxy_R"]
PL=np.array([58,10,0.]); PR=np.array([-58,10,0.]); DC=np.array([0,20,0.]); ratio=P["r_q"]/P["r_d"]
def T(p,y,c):
    if p in HEAD: return Rm(np.radians(y),[0,0,1],[0,0,0])
    if p in ARML: return Rm(np.radians(c),[0,0,1],PL)
    if p in ARMR: return Rm(np.radians(-c),[0,0,1],PR)
    if p=="clasp_drum": return Rm(np.radians(-ratio*c),[0,0,1],DC)
    return np.eye(4)
def pose(p,y,c): m=M[p].copy(); m.apply_transform(T(p,y,c)); return m
out=dict(tolerance_mm3=TOL, naming="arm_L/bracket_L/pad_L = critter's own LEFT = +x; arm_R = -x",
         note="Washer is fixed on the collar journal (does not yaw). Seam lips are NOT excluded: any front/back overlap is a defect.")
val=[]
for f in sorted(os.listdir("check")):
    if not f.endswith(".stl"): continue
    if "_y" in f:
        p=f.split("_y")[0]; y=45; c=45
    else:
        p,rest=f[:-4].rsplit("_c",1); y=0; c=float(rest)
    ref=trimesh.load("check/"+f); mine=pose(p,y,c)
    d=np.abs(trimesh.proximity.signed_distance(ref,mine.vertices[::max(1,len(mine.vertices)//600)])).max()
    val.append([p,y,c,round(float(d),3)])
out["transform_validation_max_dev_mm"]=val
MOV=HEAD+ARML+ARMR+["clasp_drum"]; ALL=list(M.keys())
excluded={
  ("paw_pad_L","arm_L"):"pad glued on own paw",("paw_pad_R","arm_R"):"pad glued on own paw",
  ("sleeve_proxy_L","arm_L"):"sleeve envelope contains own beam",("sleeve_proxy_R","arm_R"):"sleeve envelope contains own beam",
  ("sleeve_proxy_L","paw_pad_L"):"same arm",("sleeve_proxy_R","paw_pad_R"):"same arm",
  ("fur_proxy_torso","torso_front"):"fur on shell",("fur_proxy_torso","torso_back"):"fur on shell",
  ("yaw_coupler","head_back"):"blade in slot",
  ("yaw_retainer_A","yaw_collar"):"retainer under lip",("yaw_retainer_B","yaw_collar"):"retainer under lip",
  ("yaw_retainer_A","head_back"):"screwed",("yaw_retainer_B","head_back"):"screwed",
  ("yaw_thrust_washer","yaw_collar"):"washer sits on journal top",
  ("yaw_coupler","dummy_horn_yaw"):"coupler on horn",("clasp_drum","dummy_horn_clasp"):"drum on horn",
  ("dummy_horn_yaw","dummy_servo_yaw"):"horn on boss",("dummy_horn_clasp","dummy_servo_clasp"):"horn on boss",
  ("dummy_cam","head_front"):"camera mount",("dummy_cam","head_back"):"camera mount",
  ("dummy_speaker","torso_front"):"speaker in pocket",("dummy_amp","tray"):"amp in pocket",
  ("dummy_mic","torso_front"):"mic in pocket",
  ("dummy_servo_yaw","yaw_collar"):"yaw servo seated under hangers",
  ("dummy_servo_clasp","tray"):"clasp servo seated under shelf",
  ("dummy_pi","tray"):"Pi on standoffs",
  ("yaw_coupler","dummy_servo_yaw"):"coupler above servo",
  ("clasp_drum","dummy_servo_clasp"):"drum above servo",
}
compliant={("paw_pad_L","paw_pad_R"):"designed soft paw-to-paw meeting",("paw_pad_L","strap_env"):"pad on strap",("paw_pad_R","strap_env"):"pad on strap",
  ("sleeve_proxy_L","strap_env"):"sleeve on strap",("sleeve_proxy_R","strap_env"):"sleeve on strap"}
def key(a,b,d): return d.get((a,b)) or d.get((b,a))
def ov(a,b,pad=0.01): return np.all(a[0]-pad<=b[1]) and np.all(b[0]-pad<=a[1])
poses=set()
for y in np.arange(-48,48.01,0.5): poses.add((round(y,2),0.0))
for c in np.arange(-6,50.01,0.25): poses.add((0.0,round(c,2)))
for y in np.arange(-45,45.01,7.5):
    for c in np.arange(0,45.01,5): poses.add((round(y,2),round(c,2)))
for c in (-3,0,45,46):
    for y in (-45,45): poses.add((y,c))
poses=sorted(poses); rows=[]; npairs=0; nbool=0; t0=time.time()
for (y,c) in poses:
    PM={p:(pose(p,y,c) if p in MOV else M[p]) for p in ALL}; B={p:PM[p].bounds for p in ALL}
    for a,b in itertools.combinations(ALL,2):
        if a not in MOV and b not in MOV: continue
        if key(a,b,excluded): continue
        npairs+=1
        if not ov(B[a],B[b]): continue
        nbool+=1
        v=float(trimesh.boolean.intersection([PM[a],PM[b]],engine="manifold").volume)
        if v>TOL: rows.append(dict(yaw=y,clasp=c,a=a,b=b,vol_mm3=round(v,3),compliant=key(a,b,compliant) or ""))
out["sweep"]=dict(poses=len(poses),pair_tests=npairs,aabb_passed_to_boolean=nbool,seconds=round(time.time()-t0,1),
  head_yaw_range=[-48,48,0.5],arm_range=[-6,50,0.25],cross_grid="yaw -45..45 step 7.5 x clasp 0..45 step 5",
  excluded_pairs={f"{a}|{b}":v for (a,b),v in excluded.items()},compliant_pairs={f"{a}|{b}":v for (a,b),v in compliant.items()})
with open("results/interference_events.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["yaw","clasp","a","b","vol_mm3","compliant"]); w.writeheader(); w.writerows(rows)
inT=lambda r:-45<=r["yaw"]<=45 and P["th_stop_o"]<r["clasp"]<P["th_stop_c"]
out["rigid_overlaps_in_travel"]=[r for r in rows if inT(r) and not r["compliant"]]
out["compliant_contacts_in_travel_first"]={}
for k in compliant:
    ev=[r for r in rows if {r["a"],r["b"]}==set(k) and r["yaw"]==0]
    if ev: e=min(ev,key=lambda r:r["clasp"]); out["compliant_contacts_in_travel_first"]["|".join(k)]=dict(first_clasp=e["clasp"],vol_at_first=e["vol_mm3"])
def first(cond,keyf):
    ev=[r for r in rows if cond(r) and not r["compliant"]]; return min(ev,key=keyf) if ev else None
out["stop_engagement"]=dict(
  yaw_pos=first(lambda r:r["yaw"]>0 and r["clasp"]==0,lambda r:r["yaw"]),
  yaw_neg=first(lambda r:r["yaw"]<0 and r["clasp"]==0,lambda r:-r["yaw"]),
  clasp_close=first(lambda r:r["clasp"]>=45 and r["yaw"]==0,lambda r:r["clasp"]),
  clasp_open=first(lambda r:r["clasp"]<=0 and r["yaw"]==0,lambda r:-r["clasp"]))
# static seam / washer checks (not in the moving-pair loop when both are static)
static_rows=[]
for a,b,why in [("torso_front","torso_back","seam lip/groove should clear 0.25 mm"),
                ("head_front","head_back","seam lip/groove should clear 0.25 mm"),
                ("yaw_thrust_washer","head_back","designed 0.30 mm axial gap"),
                ("tray","torso_front","tabs in pockets"),
                ("tray","torso_back","tabs in pockets")]:
    v=float(trimesh.boolean.intersection([M[a],M[b]],engine="manifold").volume)
    static_rows.append(dict(a=a,b=b,vol_mm3=round(v,4),note=why,ok=v<=TOL))
out["static_pair_volumes"]=static_rows
json.dump(out,open("results/summary_sweep.json","w"),indent=1,default=float)
print(json.dumps({k:out[k] for k in ["transform_validation_max_dev_mm","sweep","rigid_overlaps_in_travel","compliant_contacts_in_travel_first","stop_engagement","static_pair_volumes"]},indent=1,default=float))
