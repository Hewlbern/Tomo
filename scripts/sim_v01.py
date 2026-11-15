# SPDX-License-Identifier: MIT
"""evoKin V.01 reproducible verification: imposed-motion kinematics on the EXPORTED STLs.
Head pan (yaw about z) and two arms on the shared x-axis shoulder line (y=13, z=60) whose forearms
overlap across the middle and close on each other (the clasp). Firmware interlock: armL - armR >= DMIN.
Not dynamics. No contact mechanics, no friction, no print tolerance, no soft-body."""
import numpy as np, trimesh, json, csv, itertools, time, os, sys
from trimesh.transformations import rotation_matrix as Rm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
TOL=0.05
SH=np.array([0,13.0,60.0]); REST_L=-15.0; REST_R=-25.0   # export pose (0 = forward, + = up)
REST=REST_L                                       # kept for the head-only rows
YAW_SOFT=(-42,42); ARM_SOFT=(-45,30); DMIN=7.5     # interlock: left forearm always over the right
FORE_R=71.0; FORE_RIN=66.0
PRINTED="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer head_back head_front arm_L arm_R shoulder_bracket_L shoulder_bracket_R".split()
PROXY="sleeve_proxy_L sleeve_proxy_R fur_proxy_torso".split()
DUMMIES="dummy_servo_yaw dummy_horn_yaw dummy_servo_arm_L dummy_servo_arm_R dummy_horn_arm_L dummy_horn_arm_R dummy_pi dummy_cam dummy_speaker dummy_amp dummy_mic".split()
M={p:trimesh.load(stl_path(p)) for p in PRINTED+PROXY+DUMMIES}
HEAD=["head_back","head_front","yaw_coupler","yaw_retainer_A","yaw_retainer_B","dummy_cam"]
ARML=["arm_L","sleeve_proxy_L","dummy_horn_arm_L"]; ARMR=["arm_R","sleeve_proxy_R","dummy_horn_arm_R"]
def T(p,y,aL,aR):
    if p in HEAD: return Rm(np.radians(y),[0,0,1],[0,0,0])
    if p in ARML: return Rm(np.radians(-(aL-REST_L)),[1,0,0],SH)
    if p in ARMR: return Rm(np.radians(-(aR-REST_R)),[1,0,0],SH)
    return np.eye(4)
def pose(p,y,aL,aR): m=M[p].copy(); m.apply_transform(T(p,y,aL,aR)); return m
out=dict(tolerance_mm3=TOL, naming="arm_L = critter's own LEFT = +x; arm_R = -x",
         arm_angle="0 = arm straight forward (-y), + = up; rotation about the x axis through y=13, z=60",
         travel=f"yaw {YAW_SOFT}, each arm {ARM_SOFT}, interlock armL - armR >= {DMIN} deg",
         note="Washer is fixed on the collar journal (does not yaw). Seam lips are NOT excluded: any front/back overlap is a defect.")
# ---- transform validation against OpenSCAD-posed exports in check/
val=[]
if os.path.isdir("check"):
    for f in sorted(os.listdir("check")):
        if not f.endswith(".stl"): continue
        if "_y30" in f: p=f.split("_y30")[0]; y,aL,aR=30,REST_L,REST_R
        else:
            p,a=f[:-4].rsplit("_a",1); a=float(a); y=0; aL=a if p=="arm_L" else REST_L; aR=a if p=="arm_R" else REST_R
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
compliant={("sleeve_proxy_L","sleeve_proxy_R"):"paw fur on paw fur at the clasp",
           ("arm_L","sleeve_proxy_R"):"paw fur compressed in the clasp",("arm_R","sleeve_proxy_L"):"paw fur compressed in the clasp",
           ("sleeve_proxy_L","fur_proxy_torso"):"2 mm sleeve fur brushing 4 mm torso fur",("sleeve_proxy_R","fur_proxy_torso"):"2 mm sleeve fur brushing 4 mm torso fur",
           ("sleeve_proxy_L","head_front"):"sleeve fur on head",("sleeve_proxy_R","head_front"):"sleeve fur on head",
           ("sleeve_proxy_L","head_back"):"sleeve fur on head",("sleeve_proxy_R","head_back"):"sleeve fur on head"}
def key(a,b,d): return d.get((a,b)) or d.get((b,a))
def ov(a,b,pad=0.01): return np.all(a[0]-pad<=b[1]) and np.all(b[0]-pad<=a[1])
poses=set()
for y in np.arange(-48,48.01,0.5): poses.add((round(y,2),REST_L,REST_R))
for a in np.arange(-70,60.01,0.5): poses.add((0.0,round(a,2),REST_R)); poses.add((0.0,REST_L,round(a,2)))
G=(-45,-30,-15,0,15,30)
for y in np.arange(-45,45.01,15):
    for aL in G:
        for aR in G: poses.add((round(y,2),float(aL),float(aR)))
for y in (-42,0,42):                       # interlock edge: blades at minimum gap across the travel
    for aR in np.arange(ARM_SOFT[0],ARM_SOFT[1]-DMIN+0.01,7.5): poses.add((y,round(aR+DMIN,2),round(aR,2)))
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
  head_yaw_range=[-48,48,0.5],arm_range=[-70,60,0.5],cross_grid="yaw -45..45 step 15 x armL x armR in {-45,-30,-15,0,15,30}, plus the interlock edge armL = armR + 7.5 at yaw -42/0/42",
  excluded_pairs={f"{a}|{b}":v for (a,b),v in excluded.items()},compliant_pairs={f"{a}|{b}":v for (a,b),v in compliant.items()})
with open("results/interference_events.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["yaw","armL","armR","a","b","vol_mm3","compliant"]); w.writeheader(); w.writerows(rows)
inT=lambda r:(YAW_SOFT[0]<=r["yaw"]<=YAW_SOFT[1] and ARM_SOFT[0]<=r["armL"]<=ARM_SOFT[1] and ARM_SOFT[0]<=r["armR"]<=ARM_SOFT[1]
              and r["armL"]-r["armR"]>=DMIN-1e-6)
out["rigid_overlaps_in_travel"]=[r for r in rows if inT(r) and not r["compliant"]]
out["compliant_contacts_in_travel"]=[r for r in rows if inT(r) and r["compliant"]][:50]
def first(cond,keyf):
    ev=[r for r in rows if cond(r) and not r["compliant"]]; return min(ev,key=keyf) if ev else None
out["stop_engagement"]=dict(
  yaw_pos=first(lambda r:r["yaw"]>0 and r["armL"]==REST_L and r["armR"]==REST_R,lambda r:r["yaw"]),
  yaw_neg=first(lambda r:r["yaw"]<0 and r["armL"]==REST_L and r["armR"]==REST_R,lambda r:-r["yaw"]),
  armL_up=first(lambda r:r["yaw"]==0 and r["armL"]>REST_L and r["armR"]==REST_R,lambda r:r["armL"]),
  armL_down_blade_contact=first(lambda r:r["yaw"]==0 and r["armL"]<REST_L and r["armR"]==REST_R,lambda r:-r["armL"]),
  armR_up_blade_contact=first(lambda r:r["yaw"]==0 and r["armR"]>REST_R and r["armL"]==REST_L,lambda r:r["armR"]))
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
    arm=pose("arm_L",0,a,REST_R); sl=pose("sleeve_proxy_L",0,a,REST_R)
    mc[f"a{int(a)}"]=dict(arm_to_torso_back=round(mindist(arm,M["torso_back"]),2),arm_to_torso_front=round(mindist(arm,M["torso_front"]),2),
        arm_to_cap=round(mindist(arm,M["shoulder_bracket_L"]),2),arm_to_head_y0=round(mindist(arm,M["head_back"]),2),
        sleeve_to_fur=round(mindist(sl,M["fur_proxy_torso"]),2))
worst=dict(arm_to_shell=min(min(v["arm_to_torso_back"],v["arm_to_torso_front"]) for v in mc.values()),
           arm_to_cap=min(v["arm_to_cap"] for v in mc.values()),arm_to_head=min(v["arm_to_head_y0"] for v in mc.values()),
           sleeve_to_fur=min(v["sleeve_to_fur"] for v in mc.values()))
# desk plane: the bear stands on z=0 (torso bottom). Rigid arm and paw must stay above it over the soft travel.
worst["arm_lowest_z_mm"]=round(min(min(float(pose("arm_L",0,a,REST_R).bounds[0][2]),float(pose("arm_R",0,REST_L,a).bounds[0][2])) for a in np.arange(ARM_SOFT[0],ARM_SOFT[1]+0.01,1.0)),2)
worst["sleeve_lowest_z_mm"]=round(min(float(pose("sleeve_proxy_L",0,a,REST_R).bounds[0][2]) for a in np.arange(ARM_SOFT[0],ARM_SOFT[1]+0.01,1.0)),2)
# eye bezels (separate part, not in the sweep): flange bottom at z = 120 - 13.5 = 106.5 within |x| <= 26.5, y -42..-30.
fr=[pose("arm_L",y,ARM_SOFT[1],REST_R) for y in (0,)]
v=fr[0].vertices; sel=(np.abs(v[:,0])<=26.5)&(v[:,1]<-28)
worst["arm_top_z_under_bezels_mm"]=round(float(v[sel,2].max()),2)
worst["ok"]=(worst["arm_to_shell"]>=0.4 and worst["arm_to_cap"]>=0.4 and worst["arm_to_head"]>=0.4 and worst["arm_lowest_z_mm"]>=2.0
             and worst["arm_top_z_under_bezels_mm"]<=106.5-2.0)
out["arm_min_clearance_by_angle_mm"]=mc; out["arm_min_clearance_mm"]=worst
# ---- clasp closure + grip clearance (V.01) ----
def blade_gap(aL,aR):
    L=pose("arm_L",0,aL,aR); R=pose("arm_R",0,aL,aR)
    pts=L.sample(30000,seed=5); pts=pts[np.abs(pts[:,0])<=20]
    return float(trimesh.proximity.closest_point(R,pts)[1].min()), L, R
clasp=dict(definition="grip gap = smallest rigid distance between the two forearm blades in the overlap zone (|x| <= 18); fur/fabric on the paws not included")
curve=[]
for mean in (-30,-10,10):
    for d in (DMIN,10,15,20,25,30,35):
        aL,aR=mean+d/2,mean-d/2
        if not(ARM_SOFT[0]<=aR and aL<=ARM_SOFT[1]): continue
        g,_,_=blade_gap(aL,aR); curve.append(dict(mean=mean,delta=d,armL=aL,armR=aR,gap_mm=round(g,2)))
clasp["gap_curve"]=curve
gmin=min(c["gap_mm"] for c in curve if c["delta"]==DMIN); gmax=max(c["gap_mm"] for c in curve)
_,L0,R0=blade_gap(-10+DMIN/2,-10-DMIN/2)
xl=L0.bounds[:,0]; xr=R0.bounds[:,0]
clasp["overlap_x_mm"]=round(float(min(xl[1],xr[1])-max(xl[0],xr[0])),2)
clasp["closed_gap_mm"]=round(gmin,2); clasp["max_gap_in_travel_mm"]=round(gmax,2)
# delta (deg) per mm of gap, fitted at mean -10
c10=[c for c in curve if c["mean"]==-10]; A=np.polyfit([c["gap_mm"] for c in c10],[c["delta"] for c in c10],1)
clasp["delta_deg_for_gap"]=dict(slope_deg_per_mm=round(float(A[0]),3),offset_deg=round(float(A[1]),2),
    gap25_delta_deg=round(float(A[0]*25+A[1]),1),gap0_delta_deg=round(float(A[1]),1))
clasp["closure_ok"]=bool(gmin<=1.0 and gmin>=0.3 and gmax>=25.0 and clasp["overlap_x_mm"]>=30)
# grip clearance: a Ø d test cylinder along x at r = FORE_R on the mean angle, blades opened until it just fits
def cyl(d,mean):
    c=trimesh.creation.cylinder(radius=d/2,height=140,sections=48); c.apply_transform(Rm(np.pi/2,[0,1,0]))
    c.apply_translation([0,SH[1]-FORE_R,SH[2]]); c.apply_transform(Rm(np.radians(-mean),[1,0,0],SH)); return c
grip=[]
for d in (4,8,12,20,25):
    for mean in (-30,-10,10):
        lo,hi=0.0,60.0
        for _ in range(22):                     # smallest delta at which the cylinder clears both blades (touching)
            mid=(lo+hi)/2; aL,aR=mean+mid/2,mean-mid/2
            Lp=pose("arm_L",0,aL,aR); Rp=pose("arm_R",0,aL,aR); c=cyl(d,mean)
            vv=trimesh.boolean.intersection([Lp,c],engine="manifold").volume+trimesh.boolean.intersection([Rp,c],engine="manifold").volume
            if vv>TOL: lo=mid
            else: hi=mid
        aL,aR=mean+hi/2,mean-hi/2; c=cyl(d,mean)
        intravel=ARM_SOFT[0]<=aR and aL<=ARM_SOFT[1] and hi>=DMIN
        cp=c.sample(4000,seed=2); cp=np.vstack([cp,c.vertices])
        sh=min(-float(trimesh.proximity.signed_distance(M[t],cp).max()) for t in ("torso_front","torso_back"))
        fur=-float(trimesh.proximity.signed_distance(M["fur_proxy_torso"],cp).max())
        hd=min(-float(trimesh.proximity.signed_distance(M[t],cp).max()) for t in ("head_front","head_back"))
        grip.append(dict(d_mm=d,mean_deg=mean,armL=round(aL,2),armR=round(aR,2),delta_deg=round(hi,2),in_travel=bool(intravel),
                         clear_to_shell_mm=round(sh,2),clear_to_torso_fur_mm=round(fur,2),clear_to_head_mm=round(hd,2)))
clasp["grip_clearance"]=grip
clasp["grip_ok"]=all(g["clear_to_shell_mm"]>=0.5 for g in grip if g["in_travel"]) and any(g["in_travel"] for g in grip if g["d_mm"]==25)
out["clasp"]=clasp
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
print(json.dumps({k:out[k] for k in ["transform_validation_max_dev_mm","sweep","rigid_overlaps_in_travel","stop_engagement","arm_min_clearance_mm","static_ok","clasp"]},indent=1,default=float))
