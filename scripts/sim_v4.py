# SPDX-License-Identifier: MIT
"""critter v4 reproducible verification: imposed-motion kinematics on the EXPORTED v4 STLs.
Head pan (yaw about z) and two forward-swinging arms (rotation about the x-axis shoulder line y=13, z=60).
Not dynamics. No contact mechanics, no friction, no print tolerance, no soft-body."""
import numpy as np, trimesh, json, csv, itertools, time, os, sys
from trimesh.transformations import rotation_matrix as Rm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
TOL=0.05
SH=np.array([0,13.0,60.0]); REST=-20.0          # STLs are exported at arm angle -20 (0 = forward, + = up)
YAW_SOFT=(-42,42); ARM_SOFT=(-55,70)
PRINTED="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer head_back head_front arm_L arm_R shoulder_bracket_L shoulder_bracket_R".split()
PROXY="sleeve_proxy_L sleeve_proxy_R fur_proxy_torso".split()
DUMMIES="dummy_servo_yaw dummy_horn_yaw dummy_servo_arm_L dummy_servo_arm_R dummy_horn_arm_L dummy_horn_arm_R dummy_pi dummy_cam dummy_speaker dummy_amp dummy_mic".split()
M={p:trimesh.load(stl_path(p)) for p in PRINTED+PROXY+DUMMIES}
HEAD=["head_back","head_front","yaw_coupler","yaw_retainer_A","yaw_retainer_B","dummy_cam"]
ARML=["arm_L","sleeve_proxy_L","dummy_horn_arm_L"]; ARMR=["arm_R","sleeve_proxy_R","dummy_horn_arm_R"]
def T(p,y,aL,aR):
    if p in HEAD: return Rm(np.radians(y),[0,0,1],[0,0,0])
    if p in ARML: return Rm(np.radians(-(aL-REST)),[1,0,0],SH)
    if p in ARMR: return Rm(np.radians(-(aR-REST)),[1,0,0],SH)
    return np.eye(4)
def pose(p,y,aL,aR): m=M[p].copy(); m.apply_transform(T(p,y,aL,aR)); return m
out=dict(tolerance_mm3=TOL, naming="arm_L = critter's own LEFT = +x; arm_R = -x",
         arm_angle="0 = arm straight forward (-y), + = up; rotation about the x axis through y=13, z=60",
         note="Washer is fixed on the collar journal (does not yaw). Seam lips are NOT excluded: any front/back overlap is a defect.")
# ---- transform validation against OpenSCAD-posed exports in check/
val=[]
if os.path.isdir("check"):
    for f in sorted(os.listdir("check")):
        if not f.endswith(".stl"): continue
        if "_y30" in f: p=f.split("_y30")[0]; y,aL,aR=30,REST,REST
        else:
            p,a=f[:-4].rsplit("_a",1); a=float(a); y=0; aL=a if p=="arm_L" else REST; aR=a if p=="arm_R" else REST
        ref=trimesh.load("check/"+f); mine=pose(p,y,aL,aR)
        d=np.abs(trimesh.proximity.signed_distance(ref,mine.vertices[::max(1,len(mine.vertices)//600)])).max()
        val.append([p,y,aL,aR,round(float(d),4)])
out["transform_validation_max_dev_mm"]=val
MOV=HEAD+ARML+ARMR; ALL=list(M.keys())
excluded={
  ("sleeve_proxy_L","arm_L"):"sleeve envelope contains own arm",("sleeve_proxy_R","arm_R"):"sleeve envelope contains own arm",
  ("dummy_horn_arm_L","arm_L"):"horn screwed into hub pocket",("dummy_horn_arm_R","arm_R"):"horn screwed into hub pocket",
  ("dummy_horn_arm_L","sleeve_proxy_L"):"same arm",("dummy_horn_arm_R","sleeve_proxy_R"):"same arm",
  ("dummy_horn_arm_L","dummy_servo_arm_L"):"horn on its own spline/boss",("dummy_horn_arm_R","dummy_servo_arm_R"):"horn on its own spline/boss",
  ("fur_proxy_torso","torso_front"):"fur on shell",("fur_proxy_torso","torso_back"):"fur on shell (pods poke through the 4 mm fur skin)",
  ("fur_proxy_torso","shoulder_bracket_L"):"cap sits in the fur skin opening",("fur_proxy_torso","shoulder_bracket_R"):"cap sits in the fur skin opening",
  ("yaw_coupler","head_back"):"blade in slot",
  ("yaw_retainer_A","yaw_collar"):"retainer under lip",("yaw_retainer_B","yaw_collar"):"retainer under lip",
  ("yaw_retainer_A","head_back"):"screwed",("yaw_retainer_B","head_back"):"screwed",
  ("yaw_thrust_washer","yaw_collar"):"washer sits on journal top",
  ("yaw_coupler","dummy_horn_yaw"):"coupler on horn",("dummy_horn_yaw","dummy_servo_yaw"):"horn on boss",
  ("dummy_cam","head_front"):"camera mount",("dummy_cam","head_back"):"camera mount",
  ("dummy_speaker","torso_front"):"speaker in pocket",("dummy_amp","tray"):"amp in pocket",
  ("dummy_mic","torso_front"):"mic in pocket",
  ("dummy_servo_yaw","yaw_collar"):"yaw servo seated under hangers",
  ("dummy_pi","tray"):"Pi on standoffs",
  ("yaw_coupler","dummy_servo_yaw"):"coupler above servo",
}
compliant={("sleeve_proxy_L","fur_proxy_torso"):"2 mm sleeve fur brushing 4 mm torso fur",("sleeve_proxy_R","fur_proxy_torso"):"2 mm sleeve fur brushing 4 mm torso fur",
           ("sleeve_proxy_L","head_front"):"sleeve fur on head",("sleeve_proxy_R","head_front"):"sleeve fur on head",
           ("sleeve_proxy_L","head_back"):"sleeve fur on head",("sleeve_proxy_R","head_back"):"sleeve fur on head"}
def key(a,b,d): return d.get((a,b)) or d.get((b,a))
def ov(a,b,pad=0.01): return np.all(a[0]-pad<=b[1]) and np.all(b[0]-pad<=a[1])
poses=set()
for y in np.arange(-48,48.01,0.5): poses.add((round(y,2),REST,REST))
for a in np.arange(-80,85.01,0.5): poses.add((0.0,round(a,2),REST)); poses.add((0.0,REST,round(a,2)))
for y in np.arange(-45,45.01,15):
    for aL in (-55,-20,10,40,70):
        for aR in (-55,-20,10,40,70): poses.add((round(y,2),round(aL,2),round(aR,2)))
for y in (-42,42):
    for a in (-55,70): poses.add((y,a,a))
poses=sorted(poses); rows=[]; npairs=0; nbool=0; t0=time.time()
for (y,aL,aR) in poses:
    PM={p:(pose(p,y,aL,aR) if p in MOV else M[p]) for p in ALL}; B={p:PM[p].bounds for p in ALL}
    for a,b in itertools.combinations(ALL,2):
        if a not in MOV and b not in MOV: continue
        if key(a,b,excluded): continue
        npairs+=1
        if not ov(B[a],B[b]): continue
        nbool+=1
        v=float(trimesh.boolean.intersection([PM[a],PM[b]],engine="manifold").volume)
        if v>TOL: rows.append(dict(yaw=y,armL=aL,armR=aR,a=a,b=b,vol_mm3=round(v,3),compliant=key(a,b,compliant) or ""))
out["sweep"]=dict(poses=len(poses),pair_tests=npairs,aabb_passed_to_boolean=nbool,seconds=round(time.time()-t0,1),
  head_yaw_range=[-48,48,0.5],arm_range=[-80,85,0.5],cross_grid="yaw -45..45 step 15 x armL {-55,-20,10,40,70} x armR {-55,-20,10,40,70}",
  excluded_pairs={f"{a}|{b}":v for (a,b),v in excluded.items()},compliant_pairs={f"{a}|{b}":v for (a,b),v in compliant.items()})
with open("results/interference_events.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["yaw","armL","armR","a","b","vol_mm3","compliant"]); w.writeheader(); w.writerows(rows)
inT=lambda r:YAW_SOFT[0]<=r["yaw"]<=YAW_SOFT[1] and ARM_SOFT[0]<=r["armL"]<=ARM_SOFT[1] and ARM_SOFT[0]<=r["armR"]<=ARM_SOFT[1]
out["rigid_overlaps_in_travel"]=[r for r in rows if inT(r) and not r["compliant"]]
out["compliant_contacts_in_travel"]=[r for r in rows if inT(r) and r["compliant"]][:50]
def first(cond,keyf):
    ev=[r for r in rows if cond(r) and not r["compliant"]]; return min(ev,key=keyf) if ev else None
out["stop_engagement"]=dict(
  yaw_pos=first(lambda r:r["yaw"]>0 and r["armL"]==REST and r["armR"]==REST,lambda r:r["yaw"]),
  yaw_neg=first(lambda r:r["yaw"]<0 and r["armL"]==REST and r["armR"]==REST,lambda r:-r["yaw"]),
  armL_up=first(lambda r:r["yaw"]==0 and r["armL"]>REST and r["armR"]==REST,lambda r:r["armL"]),
  armL_down=first(lambda r:r["yaw"]==0 and r["armL"]<REST and r["armR"]==REST,lambda r:-r["armL"]))
# ---- minimum clearances of the rigid arm (no fur) to the torso shell, pod/cap and head across the soft travel
def mindist(a,b,n=3000):
    best=1e9
    for x,y in ((a,b),(b,a)):
        bb=y.bounds; pts=x.sample(n,seed=3)
        near=np.all((pts>bb[0]-20)&(pts<bb[1]+20),axis=1); pts=pts[near] if near.any() else pts[:50]
        for i in range(0,len(pts),500):
            d=-trimesh.proximity.signed_distance(y,pts[i:i+500]); best=min(best,float(d.min()))
    return best
mc={}
for a in list(np.arange(ARM_SOFT[0],ARM_SOFT[1],10))+[ARM_SOFT[1]]:
    arm=pose("arm_L",0,a,REST); sl=pose("sleeve_proxy_L",0,a,REST)
    mc[f"a{int(a)}"]=dict(arm_to_torso_back=round(mindist(arm,M["torso_back"]),2),arm_to_torso_front=round(mindist(arm,M["torso_front"]),2),
        arm_to_cap=round(mindist(arm,M["shoulder_bracket_L"]),2),arm_to_head_y0=round(mindist(arm,M["head_back"]),2),
        sleeve_to_fur=round(mindist(sl,M["fur_proxy_torso"]),2))
worst=dict(arm_to_shell=min(min(v["arm_to_torso_back"],v["arm_to_torso_front"]) for v in mc.values()),
           arm_to_cap=min(v["arm_to_cap"] for v in mc.values()),arm_to_head=min(v["arm_to_head_y0"] for v in mc.values()),
           sleeve_to_fur=min(v["sleeve_to_fur"] for v in mc.values()))
# desk plane: the bear stands on z=0 (torso bottom). Rigid arm and paw must stay above it over the soft travel.
worst["arm_lowest_z_mm"]=round(min(float(pose("arm_L",0,a,REST).bounds[0][2]) for a in np.arange(ARM_SOFT[0],ARM_SOFT[1]+0.01,1.0)),2)
worst["sleeve_lowest_z_mm"]=round(min(float(pose("sleeve_proxy_L",0,a,REST).bounds[0][2]) for a in np.arange(ARM_SOFT[0],ARM_SOFT[1]+0.01,1.0)),2)
worst["ok"]=worst["arm_to_shell"]>=0.4 and worst["arm_to_cap"]>=0.4 and worst["arm_to_head"]>=0.4 and worst["arm_lowest_z_mm"]>=2.0
out["arm_min_clearance_by_angle_mm"]=mc; out["arm_min_clearance_mm"]=worst
# static seam / washer / tray / cap checks
static_rows=[]
for a,b,why in [("torso_front","torso_back","seam lip/groove should clear 0.25 mm"),
                ("head_front","head_back","seam lip/groove should clear 0.25 mm"),
                ("yaw_thrust_washer","head_back","designed 0.30 mm axial gap"),
                ("tray","torso_front","tabs in pockets"),("tray","torso_back","tabs in pockets"),
                ("shoulder_bracket_L","torso_back","cap in pod rebate, 0.3 mm per side"),("shoulder_bracket_R","torso_back","cap in pod rebate, 0.3 mm per side"),
                ("dummy_servo_arm_L","torso_back","servo through pod opening"),("dummy_servo_arm_R","torso_back","servo through pod opening"),
                ("dummy_servo_arm_L","tray","arm servo above tray"),("dummy_servo_arm_R","tray","arm servo above tray"),
                ("dummy_servo_arm_L","shoulder_bracket_L","case top against cap"),("dummy_servo_arm_R","shoulder_bracket_R","case top against cap")]:
    v=float(trimesh.boolean.intersection([M[a],M[b]],engine="manifold").volume)
    static_rows.append(dict(a=a,b=b,vol_mm3=round(v,4),note=why,ok=v<=TOL))
out["static_pair_volumes"]=static_rows
out["static_ok"]=all(r["ok"] for r in static_rows)
json.dump(out,open("results/summary_sweep.json","w"),indent=1,default=float)
print(json.dumps({k:out[k] for k in ["transform_validation_max_dev_mm","sweep","rigid_overlaps_in_travel","stop_engagement","arm_min_clearance_mm","static_ok"]},indent=1,default=float))
