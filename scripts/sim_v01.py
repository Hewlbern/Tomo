# SPDX-License-Identifier: MIT
"""Tomo (formerly evoKin V.01) reproducible verification: imposed-motion kinematics on the EXPORTED STLs.
Mirumi-style passive spring hug, Mirumi proportions: one egg body, face cap pans/tilts inside it; each arm turns
about a vertical SHOULDER hinge (left arm axis through (HX, HY), right at (-HX, HY)); the two arms are short and
symmetric; their paws nearly meet in front of a near-vertical handle in the centre belly groove (two-arms pass). 0 deg = closed on the rest stop, + = opened by
hand, printed open stop at 60 deg (thick-arm pass; was 30).
Head: pan (yaw about z, FS90 in the collar) and tilt/nod (about x through y=6, z=119, FS90 on the neck turret).
Not dynamics. No contact mechanics, no friction, no print tolerance, no soft-body. Spring force from the catalogue rate."""
import numpy as np, trimesh, json, csv, itertools, time, os, sys, math
from trimesh.transformations import rotation_matrix as Rm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
TOL=0.05
# ---- geometry constants (must match cad/evokin_v01.scad)
import groove_geo as gg
R_AX=gg.eggr(78)+8.5; PSI_H=-35.0
HX=R_AX*math.cos(math.radians(PSI_H)); HY=R_AX*math.sin(math.radians(PSI_H))
HL=np.array([HX,HY,0.0]); HR=np.array([-HX,HY,0.0])
TILT_AX=np.array([0,6.0,119.0])
G_FR=gg.FR; G_U=gg.U; G_N=gg.N; G_MID=G_FR+G_U*gg.MIDT     # centre groove floor line (point, direction), outward normal
YAW_SOFT=(-42,42); TILT_SOFT=(-10,10); ARM_TRAVEL=(0,60)
SPRING_K=0.3027/90*1000      # N·mm/deg, 3HPG6 / 3HPD1 catalogue: 2.679 lbf·in at 90°
SPRING_PRE=30.0              # deg of wind-up at the rest stop (90 at the 60 deg open stop = catalogue rating)
PRINTED="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer neck_turret tilt_hub head_back head_front arm_L arm_R paw_pad_L paw_pad_R".split()
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
         arm_angle=f"opening angle about the vertical shoulder hinge (left axis x={HX:.2f}, y={HY:.2f}, knuckle z 70-86; right mirrored); 0 = closed on the rest stop, + = open; printed open stop {ARM_TRAVEL[1]}°",
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
  ("fur_proxy_torso","torso_front"):"fur on shell (shoulder brackets poke through the 4 mm fur skin)",("fur_proxy_torso","torso_back"):"fur on shell",
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
def key(a,b,d):
    k=d.get((a,b)) or d.get((b,a))
    if k or d is not compliant: return k
    for x,y in ((a,b),(b,a)):
        if x.startswith("sleeve_proxy"): return f"soft stuffed fur sleeve ({x}) on {y}"
    return None
def ov(a,b,pad=0.01): return np.all(a[0]-pad<=b[1]) and np.all(b[0]-pad<=a[1])
poses=set()
for y in np.arange(-50,50.01,1.0): poses.add((round(y,2),0.0,0.0,0.0))
for t in np.arange(-25,25.01,0.5): poses.add((0.0,round(t,2),0.0,0.0))
for y in (-42,-21,0,21,42):
    for t in (-12,-6,0,6,12): poses.add((float(y),float(t),0.0,0.0))
for a in np.arange(-5,70.01,0.5): poses.add((0.0,0.0,round(a,2),0.0)); poses.add((0.0,0.0,0.0,round(a,2)))
for aL in (0,30,60):
    for aR in (0,30,60):
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
  head_yaw_range=[-50,50,1.0],head_tilt_range=[-25,25,0.5],arm_range=[-5,70,0.5],
  cross_grid="yaw {-42,-21,0,21,42} x tilt {-12,-6,0,6,12}; arms {0,30,60}² at (yaw,tilt) = (-42,12), (42,-12), (0,0)",
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
for a in (0,10,20,30,45,60):
    row={}
    for sd in ("L","R"):
        kw={"aL":a} if sd=="L" else {"aR":a}
        arm=pose(f"arm_{sd}",**kw); pad=pose(f"paw_pad_{sd}",**kw)
        row[f"arm_{sd}_to_torso_front"]=round(mindist(arm,M["torso_front"]),2); row[f"pad_{sd}_to_torso_front"]=round(mindist(pad,M["torso_front"]),2)
    row["arm_L_to_arm_R_both_at_angle"]=round(mindist(pose("arm_L",aL=a),pose("arm_R",aR=a)),2)
    mc[f"a{a}"]=row
worst=dict(arm_to_shell=min(v[k] for v in mc.values() for k in v if k.startswith("arm_") and k.endswith("torso_front")),
           pad_to_shell=min(v[k] for v in mc.values() for k in v if k.startswith("pad_")),
           arm_to_arm=min(v["arm_L_to_arm_R_both_at_angle"] for v in mc.values()),
           arm_L_closed_vs_arm_R_open=round(mindist(pose("arm_L"),pose("arm_R",aR=60)),2),
           arm_L_open_vs_arm_R_closed=round(mindist(pose("arm_L",aL=60),pose("arm_R")),2))
worst["arm_lowest_z_mm"]=round(float(min(M["arm_L"].bounds[0][2],M["arm_R"].bounds[0][2])),2)   # rotation about z keeps z
worst["note"]="arm_to_shell 0 = the stop lug resting on its relief face (by design); knuckle to ear is 0.4 mm"
worst["ok"]=worst["arm_to_arm"]>=1.0 and worst["arm_L_closed_vs_arm_R_open"]>=1.0 and worst["arm_L_open_vs_arm_R_closed"]>=1.0 and worst["arm_lowest_z_mm"]>=2.0
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
# ---- passive hug: grip on round handles / straps standing upright in the centre groove, and a flat strap
k=SPRING_K
def place(m,centre_along=gg.MIDT,lift=0.0,d=0.0):
    # z of the mesh -> groove line direction G_U; mesh centre on the floor line + G_N*(d/2+lift)
    z=np.array([0,0,1.0]); v=np.cross(z,G_U); s_=np.linalg.norm(v); ang=math.atan2(s_,np.dot(z,G_U))
    m.apply_transform(Rm(ang,v/s_)); m.apply_translation(G_FR+G_U*centre_along+G_N*(d/2+lift)); return m
def rod(d,lift=0.1): return place(trimesh.creation.cylinder(radius=d/2,height=50,sections=64),lift=lift,d=d)   # 50 mm handle segment centred on the paws (t -10..40)
def side_pose(p,sd,a): return pose(f"{p}_{sd}",**({"aL":a} if sd=="L" else {"aR":a}))
def hits(obj,sd,a,parts=("arm","paw_pad")):
    return sum(trimesh.boolean.intersection([side_pose(p,sd,a),obj],engine="manifold").volume for p in parts)
def clamp_angle(obj,sd,parts=("arm","paw_pad")):
    if hits(obj,sd,0.0,parts)<=TOL: return 0.0
    lo,hi=0.0,40.0
    for _ in range(22):
        mid=(lo+hi)/2
        if hits(obj,sd,mid,parts)>TOL: lo=mid
        else: hi=mid
    return hi
def contact(obj,sd,a,axis_pt,flat_=False):
    pad=side_pose("paw_pad",sd,a); pts=np.vstack([pad.sample(40000,seed=7),pad.vertices])
    d=trimesh.proximity.signed_distance(obj,pts); cp=pts[int(np.argmax(d))]
    if flat_: n=-G_N.copy()                                                   # flat strap: pad pushes on its face, into the groove
    else:
        c=axis_pt+G_U*np.dot(cp-axis_pt,G_U); n=c-cp; n/=np.linalg.norm(n)   # force on the object, toward its axis
    H=HL if sd=="L" else HR; r=cp-H
    lever=abs(r[0]*n[1]-r[1]*n[0])                                            # |(r x n)_z|: torque arm about the vertical hinge
    return cp,n,lever
def depth_into(soft,hard,n=6000):
    """How far the rigid object reaches into the soft sleeve (mm, 0 = no contact): max inside distance of hard-surface points."""
    if not ov(soft.bounds,hard.bounds): return 0.0
    pts=np.vstack([hard.sample(n,seed=3),hard.vertices[::max(1,len(hard.vertices)//3000)]])
    d=trimesh.proximity.signed_distance(soft,pts); return float(max(0.0,d.max()))
def grip_case(obj,label,d,axis_pt,flat_=False):
    res=dict(object=label,d_mm=d); tot=0.0; push=0.0
    for sd in ("L","R"):
        a=clamp_angle(obj,sd); ar=clamp_angle(obj,sd,("arm",))
        if a<=0.0:
            res[sd]=dict(open_deg=0.0,note="no contact at rest"); continue
        cp,n,lev=contact(obj,sd,a,axis_pt,flat_); Tq=k*(SPRING_PRE+a); F=Tq/lev
        res[sd]=dict(open_deg=round(a,2),rigid_arm_only_open_deg=round(ar,2),rigid_arm_clear_of_object_mm=round(mindist(side_pose("arm",sd,a),obj),2),
                     spring_torque_Nmm=round(Tq,1),contact_point=np.round(cp,1).tolist(),lever_mm=round(lev,1),pad_normal_force_N=round(F,2),
                     into_groove_N=round(F*float(np.dot(n,-G_N)),2))
        tot+=F; push+=F*float(np.dot(n,-G_N))
        sl=side_pose("sleeve_proxy",sd,a); res[sd]["soft_sleeve_squash_mm"]=round(depth_into(sl,obj),2)
    res["total_pad_force_N"]=round(tot,2); res["total_into_groove_N"]=round(push,2)
    res["object_vs_torso_front_mm3"]=round(float(trimesh.boolean.intersection([obj,M["torso_front"]],engine="manifold").volume),3)
    return res
grip=[]
for d in (10.0,12.5,15.0):
    grip.append(grip_case(rod(d),f"round Ø{d} upright in the centre groove ({math.degrees(math.acos(G_U[2])):.1f}° from the body vertical)",d,G_MID+G_N*(d/2)))
# flat strap 25 x 2.5 along the groove line, across the mouth: slide it back along -G_N until it touches the torso
def flat(lift):
    b=trimesh.creation.box(extents=[25,2.5,50])
    # box y (thickness) must lie along G_N: rotate about the line after aligning z
    z=np.array([0,0,1.0]); v=np.cross(z,G_U); ang=math.atan2(np.linalg.norm(v),np.dot(z,G_U)); R=Rm(ang,v/np.linalg.norm(v))
    yb=R[:3,:3]@np.array([0,1.0,0]); tgt=G_N; tw=math.atan2(np.dot(np.cross(yb,tgt),G_U),np.dot(yb,tgt))
    b.apply_transform(Rm(tw,G_U)@R); b.apply_translation(G_FR+G_U*gg.MIDT+G_N*(1.25+lift)); return b
lo,hi=0.0,20.0
for _ in range(22):
    mid=(lo+hi)/2
    if trimesh.boolean.intersection([flat(mid),M["torso_front"]],engine="manifold").volume>TOL: lo=mid
    else: hi=mid
fb=flat(hi); fg=grip_case(fb,"flat strap 25 x 2.5 across the groove mouth, along the groove line",25,G_MID+G_N*(1.25+hi),True)
fg["strap_back_face_lift_above_floor_mm"]=round(hi,2); grip.append(fg)
hug=dict(spring=dict(part="music-wire torsion spring, 0.048 in (1.22 mm) wire, 3/8 in (9.5 mm) OD, 90° legs (trim to ~6 mm); catalogue 3HPG6 (LH) / 3HPD1 (RH)",
                     rate_Nmm_per_deg=round(k,3),rated_torque_Nmm_at_90deg=302.7,preload_deg=SPRING_PRE,max_windup_deg=SPRING_PRE+ARM_TRAVEL[1],
                     torque_at_rest_Nmm=round(k*SPRING_PRE,1),torque_at_open_stop_Nmm=round(k*(SPRING_PRE+ARM_TRAVEL[1]),1)),
         grip=grip,
         assumption="Spring rate from the catalogue (2.679 lbf·in at 90°), linear; no hinge friction; the two symmetric arms close from either side and their paws press on the front quarters of the handle; pad normal force = spring torque / |(r x n)_z| at the deepest pad contact. TPU pads assumed rigid for the angle (real pads add ~1 mm of squash). Not measured.")
pl=side_pose("paw_pad","L",60); pr=side_pose("paw_pad","R",60)
hug["open"]=dict(open_stop_deg=60,pad_L_to_belly_mm=round(mindist(pl,M["torso_front"]),2),pad_R_to_belly_mm=round(mindist(pr,M["torso_front"]),2),
                 pad_to_belly_at_closed_mm=round(min(mindist(pose("paw_pad_L"),M["torso_front"]),mindist(pose("paw_pad_R"),M["torso_front"])),2))
# Mirumi-style loading: both arms on the open stop, bring the handle (Ø15 x 50 rod, axis along the groove line) in along
# a straight line in the plane perpendicular to its axis, from 90 mm out down to its seat on the groove floor; try
# approach directions theta from the groove normal (0 = straight in) toward +/-W (sideways). Rigid arms, pads and
# torso_front must stay clear; the soft sleeves are allowed to be pushed aside (squash reported).
W_=np.cross(G_U,G_N); W_/=np.linalg.norm(W_)
def rod_path(d,th,s_):
    c=rod(d,0.3); c.apply_translation((math.cos(math.radians(th))*G_N+math.sin(math.radians(th))*W_)*s_); return c
A_OPEN=float(ARM_TRAVEL[1]); appr={}
for th in (0,10,-10,20,-20,30,-30,45,-45,60,-60,75,-75,90,-90):
    clear=True
    for s_ in np.arange(90,-0.01,-3.0):
        r=rod_path(15.0,th,s_)
        if hits(r,"L",A_OPEN)+hits(r,"R",A_OPEN)>TOL or trimesh.boolean.intersection([r,M["torso_front"]],engine="manifold").volume>TOL: clear=False; break
    appr[th]=clear
best=next((th for th,c in appr.items() if c),None)
hug["open"]["rod15_insertion_path_clear"]=best is not None
hug["open"]["rod15_insertion_path"]=dict(approach_deg_from_groove_normal=best,clear_by_approach=appr) if best is not None else dict(clear_by_approach=appr)
if best is not None:
    hug["open"]["rod15_soft_sleeve_squash_mm"]=round(max(depth_into(side_pose("sleeve_proxy",sd,A_OPEN),rod_path(15.0,best,s_)) for sd in ("L","R") for s_ in np.arange(90,-0.01,-6.0)),2)
hug["open"]["note"]="Ø15 x 50 rod brought in on a straight line perpendicular to its axis (90 mm travel) onto the groove floor, both arms on the open stop; checked against both rigid arms, both pads and torso_front. NOTE: until the thick-arm pass this check iterated over an empty range (np.arange with the wrong step sign) and so always passed; with the old 30 deg stop no straight path exists."
rg=[g for g in grip]
hug["ok"]=bool(all(g[sd].get("open_deg",0)<=ARM_TRAVEL[1] for g in rg for sd in ("L","R"))
               and all(g[sd].get("open_deg",0)>0 for g in rg[:3] for sd in ("L","R"))
               and min(hug["open"]["pad_L_to_belly_mm"],hug["open"]["pad_R_to_belly_mm"])>=15 and hug["open"]["rod15_insertion_path_clear"]
               and all(g[sd].get("rigid_arm_clear_of_object_mm",1)>=0.3 for g in rg for sd in ("L","R")))
out["hug"]=hug
# soft sleeves: how far rigid parts press into the stuffed sleeves at the corner poses (soft goods, compliant)
ss={}
for (y,t,aL,aR) in ((0,0,0,0),(0,0,60,60),(42,10,0,0),(-42,10,0,0),(42,-10,0,0),(-42,-10,60,60),(0,0,60,0),(0,0,0,60)):
    row={}
    for sd,other in (("L","R"),("R","L")):
        sl=pose(f"sleeve_proxy_{sd}",y,t,aL,aR)
        for hp in ("torso_front","torso_back","head_front","head_back",f"arm_{other}",f"paw_pad_{other}"):
            hm=pose(hp,y,t,aL,aR) if hp in MOV else M[hp]
            dd=depth_into(sl,hm,3000)
            if dd>0.05: row[f"{hp}_into_sleeve_{sd}"]=round(dd,2)
        dd=depth_into(sl,pose(f"sleeve_proxy_{other}",y,t,aL,aR),3000)
        if dd>0.05 and sd=="L": row["sleeve_L_vs_sleeve_R"]=round(dd,2)
    ss[f"yaw{y}_tilt{t}_armL{aL}_armR{aR}"]=row
out["soft_sleeve_squash_mm"]=ss
# static checks
static_rows=[]
for a,b,why in [("torso_front","torso_back","seam lip/groove should clear 0.25 mm"),
                ("head_front","head_back","seam lip/groove should clear 0.25 mm"),
                ("yaw_thrust_washer","neck_turret","designed 0.30 mm axial gap"),
                ("tray","torso_front","tabs in pockets"),("tray","torso_back","tabs in pockets"),
                ("arm_L","arm_R","arms at rest must not touch"),("arm_L","torso_front","knuckle under the ear"),("arm_R","torso_front","knuckle under the ear"),
                ("head_front","torso_front","face cap vs body at rest"),("head_back","torso_back","face cap vs body at rest"),
                ("dummy_servo_tilt","neck_turret","tilt servo in the cradle window"),("dummy_servo_tilt","head_back","static"),
                ("tilt_hub","dummy_horn_tilt","hub on horn face")]:
    v=float(trimesh.boolean.intersection([M[a],M[b]],engine="manifold").volume)
    static_rows.append(dict(a=a,b=b,vol_mm3=round(v,4),note=why,ok=v<=TOL))
out["static_pair_volumes"]=static_rows
out["static_ok"]=all(r["ok"] for r in static_rows)
json.dump(out,open("results/summary_sweep.json","w"),indent=1,default=float)
print(json.dumps({k:out[k] for k in ["transform_validation_max_dev_mm","sweep","rigid_overlaps_in_travel","stop_engagement","arm_min_clearance_mm","head_tilt_clearance_mm","hug","static_pair_volumes"]},indent=1,default=float))
