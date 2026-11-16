# SPDX-License-Identifier: MIT
"""Tomo (formerly evoKin V.01) reproducible verification: imposed-motion kinematics on the EXPORTED STLs.
Mirumi-style passive spring hug: each arm turns about a vertical hip hinge (left arm axis through (HX, HY),
right mirrored); 0 deg = closed on the rest stop, + = opened by hand, printed open stop at 40 deg.
Head: pan (yaw about z, FS90MG in the collar) and tilt/nod (about x through y=6, z=119, FS90MG on the neck turret).
Not dynamics. No contact mechanics, no friction, no print tolerance, no soft-body. Spring force from the catalogue rate."""
import numpy as np, trimesh, json, csv, itertools, time, os, sys, math
from trimesh.transformations import rotation_matrix as Rm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
TOL=0.05
# ---- geometry constants (must match cad/evokin_v01.scad)
def ea(z): return 46*math.sqrt(1-((z-50)/50)**2)
def eb(z): return 40*math.sqrt(1-((z-50)/50)**2)
HX=(ea(38)+8.5)*math.cos(math.radians(-20)); HY=(eb(38)+8.5)*math.sin(math.radians(-20))
HL=np.array([HX,HY,0.0]); HR=np.array([-HX,HY,0.0])
TILT_AX=np.array([0,6.0,119.0]); GF=-30.0; G_SLOPE=0.25   # groove floor y = GF - G_SLOPE*(z-30)
G_ANG=math.atan(G_SLOPE); G_N=np.array([0,-math.cos(G_ANG),-math.sin(G_ANG)])   # outward normal of the floor line
YAW_SOFT=(-42,42); TILT_SOFT=(-10,10); ARM_TRAVEL=(0,40)
SPRING_K=0.3027/90*1000      # N·mm/deg, 3HPG6 / 3HPD1 catalogue: 2.679 lbf·in at 90°
SPRING_PRE=35.0              # deg of wind-up at the rest stop
PRINTED="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer neck_turret tilt_hub head_back head_front arm_L arm_R hip_cap_L hip_cap_R paw_pad_L paw_pad_R".split()
PROXY="sleeve_proxy_L sleeve_proxy_R fur_proxy_torso".split()
DUMMIES="dummy_servo_yaw dummy_horn_yaw dummy_servo_tilt dummy_horn_tilt dummy_pi dummy_cam dummy_speaker dummy_amp dummy_mic".split()
M={p:trimesh.load(stl_path(p)) for p in PRINTED+PROXY+DUMMIES}
TURRET=["neck_turret","yaw_coupler","yaw_retainer_A","yaw_retainer_B","dummy_servo_tilt"]
HEAD=["head_back","head_front","tilt_hub","dummy_cam","dummy_horn_tilt"]
ARML=["arm_L","paw_pad_L","sleeve_proxy_L"]; ARMR=["arm_R","paw_pad_R","sleeve_proxy_R"]
def T(p,y,t,aL,aR):
    if p in TURRET: return Rm(np.radians(y),[0,0,1],[0,0,0])
    if p in HEAD: return Rm(np.radians(y),[0,0,1],[0,0,0])@Rm(np.radians(t),[1,0,0],TILT_AX)
    if p in ARML: return Rm(np.radians(aL),[0,0,1],HL)
    if p in ARMR: return Rm(np.radians(-aR),[0,0,1],HR)
    return np.eye(4)
def pose(p,y=0,t=0,aL=0,aR=0): m=M[p].copy(); m.apply_transform(T(p,y,t,aL,aR)); return m
out=dict(tolerance_mm3=TOL, naming="arm_L = critter's own LEFT = +x; arm_R = -x",
         arm_angle=f"opening angle about the vertical hip hinge (left axis x={HX:.2f}, y={HY:.2f}); 0 = closed on the rest stop, + = open; printed open stop 40°",
         head=f"yaw about z (± = CCW/CW from above); tilt about x through y={TILT_AX[1]}, z={TILT_AX[2]}, + = nose down",
         travel=f"yaw {YAW_SOFT}, tilt {TILT_SOFT} (firmware), arms {ARM_TRAVEL} (printed stops, passive)",
         note="Washer is fixed on the collar journal (does not yaw). Seam lips are NOT excluded: any front/back overlap is a defect.")
# ---- transform validation against OpenSCAD-posed exports in check/
val=[]
if os.path.isdir("check"):
    for f in sorted(os.listdir("check")):
        if not f.endswith(".stl"): continue
        if "_y30_t10" in f: p=f.split("_y30_t10")[0]; y,t,aL,aR=30,10,0,0
        else:
            p,a=f[:-4].rsplit("_a",1); a=float(a); y=t=0; aL=a if p=="arm_L" else 0; aR=a if p=="arm_R" else 0
        ref=trimesh.load("check/"+f); mine=pose(p,y,t,aL,aR)
        d=np.abs(trimesh.proximity.signed_distance(ref,mine.vertices[::max(1,len(mine.vertices)//600)])).max()
        val.append([p,y,t,aL,aR,round(float(d),4)])
out["transform_validation_max_dev_mm"]=val
MOV=TURRET+HEAD+ARML+ARMR; ALL=list(M.keys())
excluded={
  ("sleeve_proxy_L","arm_L"):"sleeve envelope contains own arm",("sleeve_proxy_R","arm_R"):"sleeve envelope contains own arm",
  ("paw_pad_L","arm_L"):"TPU pad bonded on the paw",("paw_pad_R","arm_R"):"TPU pad bonded on the paw",
  ("paw_pad_L","sleeve_proxy_L"):"same arm",("paw_pad_R","sleeve_proxy_R"):"same arm",
  ("fur_proxy_torso","torso_front"):"fur on shell (hip brackets poke through the 4 mm fur skin)",("fur_proxy_torso","torso_back"):"fur on shell",
  ("fur_proxy_torso","hip_cap_L"):"hip cap sits in the fur skin opening",("fur_proxy_torso","hip_cap_R"):"hip cap sits in the fur skin opening",
  ("fur_proxy_torso","arm_L"):"knuckle sits in the fur skin opening",("fur_proxy_torso","arm_R"):"knuckle sits in the fur skin opening",
  ("yaw_coupler","neck_turret"):"blade in slot",
  ("yaw_retainer_A","yaw_collar"):"retainer under lip",("yaw_retainer_B","yaw_collar"):"retainer under lip",
  ("yaw_retainer_A","neck_turret"):"screwed to the turret skirt",("yaw_retainer_B","neck_turret"):"screwed to the turret skirt",
  ("yaw_thrust_washer","yaw_collar"):"washer sits on journal top",
  ("yaw_coupler","dummy_horn_yaw"):"coupler on horn",("dummy_horn_yaw","dummy_servo_yaw"):"horn on boss",
  ("yaw_coupler","dummy_servo_yaw"):"coupler above servo (spline in the coupler bore)",
  ("dummy_servo_tilt","neck_turret"):"tilt servo seated in the turret cradle",
  ("dummy_horn_tilt","dummy_servo_tilt"):"horn on its own spline/boss",("dummy_horn_tilt","tilt_hub"):"hub screwed to the horn",
  ("tilt_hub","dummy_servo_tilt"):"spline tip in the hub clearance bore (facet sliver)",
  ("tilt_hub","head_back"):"hub key in the head socket",
  ("dummy_cam","head_front"):"camera mount",("dummy_cam","head_back"):"camera mount",
  ("dummy_speaker","torso_front"):"speaker in pocket",("dummy_amp","tray"):"amp in pocket",
  ("dummy_mic","torso_front"):"mic in pocket",("dummy_mic","dummy_speaker"):"mic breakout beside speaker (pre-existing placeholder overlap)",
  ("dummy_mic","yaw_collar"):"pre-existing placeholder overlap (unchanged since v3)",
  ("dummy_servo_yaw","yaw_collar"):"yaw servo seated under hangers",
  ("dummy_pi","tray"):"Pi on standoffs",
}
compliant={("sleeve_proxy_L","sleeve_proxy_R"):"sleeve fur on sleeve fur",
           ("sleeve_proxy_L","fur_proxy_torso"):"2 mm sleeve fur on 4 mm torso fur",("sleeve_proxy_R","fur_proxy_torso"):"2 mm sleeve fur on 4 mm torso fur",
           ("paw_pad_L","fur_proxy_torso"):"TPU pad pressing torso fur",("paw_pad_R","fur_proxy_torso"):"TPU pad pressing torso fur",
           ("paw_pad_L","paw_pad_R"):"pads touching",("sleeve_proxy_L","torso_front"):"sleeve fur on shell",("sleeve_proxy_R","torso_front"):"sleeve fur on shell"}
def key(a,b,d): return d.get((a,b)) or d.get((b,a))
def ov(a,b,pad=0.01): return np.all(a[0]-pad<=b[1]) and np.all(b[0]-pad<=a[1])
poses=set()
for y in np.arange(-50,50.01,1.0): poses.add((round(y,2),0.0,0.0,0.0))
for t in np.arange(-25,25.01,0.5): poses.add((0.0,round(t,2),0.0,0.0))
for y in (-42,-21,0,21,42):
    for t in (-12,-6,0,6,12): poses.add((float(y),float(t),0.0,0.0))
for a in np.arange(-5,50.01,0.5): poses.add((0.0,0.0,round(a,2),0.0)); poses.add((0.0,0.0,0.0,round(a,2)))
for aL in (0,20,40):
    for aR in (0,20,40):
        for (y,t) in ((-42,12),(42,-12),(0,0)): poses.add((float(y),float(t),float(aL),float(aR)))
poses=sorted(poses); rows=[]; npairs=0; nbool=0; t0=time.time()
for (y,t,aL,aR) in poses:
    PM={p:(pose(p,y,t,aL,aR) if p in MOV else M[p]) for p in ALL}; B={p:PM[p].bounds for p in ALL}
    for a,b in itertools.combinations(ALL,2):
        if a not in MOV and b not in MOV: continue
        if key(a,b,excluded): continue
        npairs+=1
        if not ov(B[a],B[b]): continue
        nbool+=1
        v=float(trimesh.boolean.intersection([PM[a],PM[b]],engine="manifold").volume)
        if v>TOL: rows.append(dict(yaw=y,tilt=t,armL=aL,armR=aR,a=a,b=b,vol_mm3=round(v,3),compliant=key(a,b,compliant) or ""))
out["sweep"]=dict(poses=len(poses),pair_tests=npairs,aabb_passed_to_boolean=nbool,seconds=round(time.time()-t0,1),
  head_yaw_range=[-50,50,1.0],head_tilt_range=[-25,25,0.5],arm_range=[-5,50,0.5],
  cross_grid="yaw {-42,-21,0,21,42} x tilt {-12,-6,0,6,12}; arms {0,20,40}² at (yaw,tilt) = (-42,12), (42,-12), (0,0)",
  excluded_pairs={f"{a}|{b}":v for (a,b),v in excluded.items()},compliant_pairs={f"{a}|{b}":v for (a,b),v in compliant.items()})
with open("results/interference_events.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["yaw","tilt","armL","armR","a","b","vol_mm3","compliant"]); w.writeheader(); w.writerows(rows)
inT=lambda r:(YAW_SOFT[0]<=r["yaw"]<=YAW_SOFT[1] and TILT_SOFT[0]<=r["tilt"]<=TILT_SOFT[1]
              and ARM_TRAVEL[0]<=r["armL"]<=ARM_TRAVEL[1] and ARM_TRAVEL[0]<=r["armR"]<=ARM_TRAVEL[1])
out["rigid_overlaps_in_travel"]=[r for r in rows if inT(r) and not r["compliant"]]
out["compliant_contacts_in_travel"]=[r for r in rows if inT(r) and r["compliant"]][:50]
def first(cond,keyf):
    ev=[r for r in rows if cond(r) and not r["compliant"]]; return min(ev,key=keyf) if ev else None
z=lambda r,*k: all(r[x]==0 for x in k)
out["stop_engagement"]=dict(
  yaw_pos=first(lambda r:r["yaw"]>0 and z(r,"tilt","armL","armR"),lambda r:r["yaw"]),
  yaw_neg=first(lambda r:r["yaw"]<0 and z(r,"tilt","armL","armR"),lambda r:-r["yaw"]),
  tilt_down=first(lambda r:r["tilt"]>0 and z(r,"yaw","armL","armR"),lambda r:r["tilt"]),
  tilt_up=first(lambda r:r["tilt"]<0 and z(r,"yaw","armL","armR"),lambda r:-r["tilt"]),
  armL_closed_stop=first(lambda r:r["armL"]<0 and z(r,"yaw","tilt","armR"),lambda r:-r["armL"]),
  armL_open_stop=first(lambda r:r["armL"]>0 and z(r,"yaw","tilt","armR"),lambda r:r["armL"]),
  armR_closed_stop=first(lambda r:r["armR"]<0 and z(r,"yaw","tilt","armL"),lambda r:-r["armR"]),
  armR_open_stop=first(lambda r:r["armR"]>0 and z(r,"yaw","tilt","armL"),lambda r:r["armR"]))
# ---- minimum clearances
def mindist(a,b,n=3000):
    best=1e9
    for x,y in ((a,b),(b,a)):
        bb=y.bounds; pts=x.sample(n,seed=3)
        near=np.all((pts>bb[0]-20)&(pts<bb[1]+20),axis=1); pts=pts[near] if near.any() else pts[:50]
        for i in range(0,len(pts),500):
            d=-trimesh.proximity.signed_distance(y,pts[i:i+500]); best=min(best,float(d.min()))
    return best
mc={}
for a in (0,10,20,30,40):
    arm=pose("arm_L",aL=a); pad=pose("paw_pad_L",aL=a)
    mc[f"a{a}"]=dict(arm_to_torso_front=round(mindist(arm,M["torso_front"]),2),pad_to_torso_front=round(mindist(pad,M["torso_front"]),2),
                     arm_to_hip_cap=round(mindist(arm,M["hip_cap_L"]),2))
worst=dict(arm_to_shell=min(v["arm_to_torso_front"] for v in mc.values() if True),
           pad_to_shell=min(v["pad_to_torso_front"] for v in mc.values()),arm_to_hip_cap=min(v["arm_to_hip_cap"] for v in mc.values()))
worst["arm_lowest_z_mm"]=round(float(M["arm_L"].bounds[0][2]),2)   # rotation about z keeps z
worst["ok"]=worst["arm_to_hip_cap"]>=0.3 and worst["arm_lowest_z_mm"]>=2.0
out["arm_min_clearance_by_angle_mm"]=mc; out["arm_min_clearance_mm"]=worst
# head: rigid clearance head <-> turret / collar across the tilt clamp
hc={}
for t in (-12,-6,0,6,12):
    hb=pose("head_back",0,t); hf=pose("head_front",0,t); cam=pose("dummy_cam",0,t)
    hc[f"t{t}"]=dict(head_to_turret=round(min(mindist(hb,M["neck_turret"]),mindist(hf,M["neck_turret"])),2),
                     head_to_collar=round(min(mindist(hb,M["yaw_collar"]),mindist(hf,M["yaw_collar"])),2),
                     camera_to_tilt_servo=round(mindist(cam,M["dummy_servo_tilt"]),2),
                     head_to_tilt_servo=round(min(mindist(hb,M["dummy_servo_tilt"]),mindist(hf,M["dummy_servo_tilt"])),2))
out["head_tilt_clearance_mm"]=hc
# ---- passive hug: grip on round straps / handles and a flat strap
k=SPRING_K
def rod(d,lift=0.0):
    # Ø d strap/handle lying in the leaning groove, touching the floor line; lift = extra stand-off along the outward normal
    c=trimesh.creation.cylinder(radius=d/2,height=130,sections=64); c.apply_transform(Rm(G_ANG,[1,0,0]))
    c.apply_translation(np.array([0,GF,30])+G_N*(d/2+lift)); return c
def hits(obj,a,parts=("arm","paw_pad")):
    v=0.0
    for s,sgn in (("L",1),("R",1)):
        for p in parts:
            m=pose(f"{p}_{s}",aL=a,aR=a); v+=trimesh.boolean.intersection([m,obj],engine="manifold").volume
    return v
def clamp_angle(obj,parts=("arm","paw_pad")):
    if hits(obj,0.0,parts)<=TOL: return 0.0
    lo,hi=0.0,45.0
    for _ in range(24):
        mid=(lo+hi)/2
        if hits(obj,mid,parts)>TOL: lo=mid
        else: hi=mid
    return hi
def contact(obj,a,centre):
    pad=pose("paw_pad_L",aL=a); pts=pad.sample(40000,seed=7); pts=np.vstack([pts,pad.vertices])
    d=trimesh.proximity.signed_distance(obj,pts)   # >0 inside obj
    i=int(np.argmax(d)); cp=pts[i]
    u=np.array([0,-math.sin(G_ANG),math.cos(G_ANG)]); centre=centre+u*np.dot(cp-centre,u)   # axis point nearest the contact
    n=np.array([centre[0]-cp[0],centre[1]-cp[1],0.0]); n/=np.linalg.norm(n)   # force on the object, in plan, toward its axis
    r=cp-HL; lever=abs(r[0]*n[1]-r[1]*n[0])
    return cp,n,lever
grip=[]
for d in (10.0,12.5,15.0):
    c=rod(d); a=clamp_angle(c); a_rigid=clamp_angle(c,("arm",))
    cp,n,lever=contact(c,a,np.array([0,GF,30])+G_N*(d/2))
    Tq=k*(SPRING_PRE+a); F=Tq/lever
    rod_vs_torso=float(trimesh.boolean.intersection([c,M["torso_front"]],engine="manifold").volume)
    grip.append(dict(object=f"round Ø{d} lying in the groove (leans 14°)",d_mm=d,open_deg=round(a,2),rigid_arm_only_open_deg=round(a_rigid,2),
        rigid_arm_clear_of_object_mm=round(mindist(pose("arm_L",aL=a),c),2),
        spring_torque_Nmm=round(Tq,1),contact_point=np.round(cp,1).tolist(),lever_mm=round(lever,1),paw_force_N=round(F,2),
        push_into_groove_N=round(2*F*n[1]*-1*-1,2) if False else round(2*F*abs(n[1]),2),
        object_vs_torso_front_mm3=round(rod_vs_torso,3)))
# flat strap 25 x 2.5 across the groove mouth: slide it back until it touches the torso, then close the arms
def flat(y_back):
    b=trimesh.creation.box(extents=[25,2.5,130]); b.apply_transform(Rm(G_ANG,[1,0,0])); b.apply_translation([0,y_back-1.25,30]); return b
lo,hi=-50.0,-20.0
for _ in range(22):
    mid=(lo+hi)/2
    if trimesh.boolean.intersection([flat(mid),M["torso_front"]],engine="manifold").volume>TOL: hi=mid
    else: lo=mid
yb=lo; fb=flat(yb); af=clamp_angle(fb); cpf,nf,levf=contact(fb,af,np.array([cpx:=0,yb-1.25-50,0])) if False else (None,None,None)
pad=pose("paw_pad_L",aL=af); pts=np.vstack([pad.sample(40000,seed=7),pad.vertices]); dd=trimesh.proximity.signed_distance(fb,pts)
cpf=pts[int(np.argmax(dd))]; nf=np.array([0,1.0,0]); rf=cpf-HL; levf=abs(rf[0]*nf[1]-rf[1]*nf[0])
Tf=k*(SPRING_PRE+af)
grip.append(dict(object="flat strap 25 x 2.5 resting on the belly across the groove",d_mm=25,strap_back_face_y=round(yb,2),open_deg=round(af,2),
    rigid_arm_clear_of_object_mm=round(mindist(pose("arm_L",aL=af),fb),2),spring_torque_Nmm=round(Tf,1),contact_point=np.round(cpf,1).tolist(),
    lever_mm=round(levf,1),paw_force_N=round(Tf/levf,2),push_into_groove_N=round(2*Tf/levf,2)))
hug=dict(spring=dict(part="music-wire torsion spring, 0.048 in (1.22 mm) wire, 3/8 in (9.5 mm) OD, 90° legs (trim to ~6 mm); catalogue 3HPG6 (LH) / 3HPD1 (RH)",
                     rate_Nmm_per_deg=round(k,3),rated_torque_Nmm_at_90deg=302.7,preload_deg=SPRING_PRE,max_windup_deg=SPRING_PRE+ARM_TRAVEL[1],
                     torque_at_rest_Nmm=round(k*SPRING_PRE,1),torque_at_open_stop_Nmm=round(k*(SPRING_PRE+40),1)),
         grip=grip,
         assumption="Spring rate from the catalogue (2.679 lbf·in at 90°), linear; no friction in the hinge; force = torque / perpendicular lever from the hinge axis to the pad contact line. TPU pads assumed rigid for the angle (real pads add ~1 mm of squash). Not measured.")
# open: paw gap with both arms on the open stop
pl=pose("paw_pad_L",aL=40,aR=40); pr=pose("paw_pad_R",aL=40,aR=40)
hug["open"]=dict(open_stop_deg=40,pad_to_belly_mm=round(mindist(pl,M["torso_front"]),2),pad_tip_to_tip_mm=round(mindist(pl,pr),2),
                 pad_to_belly_at_closed_mm=round(mindist(pose("paw_pad_L"),M["torso_front"]),2))
ins=[]
for lift in np.arange(60,-0.01,-2.0):
    c=rod(15.0,lift); ins.append(hits(c,40.0))
hug["open"]["rod15_insertion_path_clear"]=bool(max(ins[:-3])<=TOL)
hug["open"]["note"]="Ø15 rod slid in along the groove normal from 60 mm out to the groove floor with both arms on the open stop; the last 3 steps are the clamp zone."
hug["ok"]=bool(all(g["open_deg"]<=ARM_TRAVEL[1] for g in grip) and hug["open"]["pad_to_belly_mm"]>=20 and hug["open"]["rod15_insertion_path_clear"]
               and all(g.get("rigid_arm_clear_of_object_mm",1)>=0.3 for g in grip))
out["hug"]=hug
# static checks
static_rows=[]
for a,b,why in [("torso_front","torso_back","seam lip/groove should clear 0.25 mm"),
                ("head_front","head_back","seam lip/groove should clear 0.25 mm"),
                ("yaw_thrust_washer","neck_turret","designed 0.30 mm axial gap"),
                ("tray","torso_front","tabs in pockets"),("tray","torso_back","tabs in pockets"),
                ("hip_cap_L","torso_front","cap under the web, 0.3 mm off the shell"),("hip_cap_R","torso_front","cap under the web, 0.3 mm off the shell"),
                ("dummy_servo_tilt","neck_turret","tilt servo in the cradle window"),("dummy_servo_tilt","head_back","static"),
                ("tilt_hub","dummy_horn_tilt","hub on horn face")]:
    v=float(trimesh.boolean.intersection([M[a],M[b]],engine="manifold").volume)
    static_rows.append(dict(a=a,b=b,vol_mm3=round(v,4),note=why,ok=v<=TOL))
out["static_pair_volumes"]=static_rows
out["static_ok"]=all(r["ok"] for r in static_rows)
json.dump(out,open("results/summary_sweep.json","w"),indent=1,default=float)
print(json.dumps({k:out[k] for k in ["transform_validation_max_dev_mm","sweep","rigid_overlaps_in_travel","stop_engagement","arm_min_clearance_mm","head_tilt_clearance_mm","hug","static_pair_volumes"]},indent=1,default=float))
