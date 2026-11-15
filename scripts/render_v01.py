# SPDX-License-Identifier: MIT
"""CAD stills of the exported evoKin V.01 STLs (matplotlib, flat-shaded). CAD only; imposed poses, not dynamics.
Writes renders/cad/v01_clasp_pen.png, v01_clasp_open_head30.png and v01_shoulder_exploded.png."""
import numpy as np, trimesh, os, sys, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from trimesh.transformations import rotation_matrix as Rm, translation_matrix as Tm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
os.makedirs("renders/cad", exist_ok=True)
SH=np.array([0,13.0,60.0]); REST_L=-15.0; REST_R=-25.0; FORE_R=71.0
import json
_C=json.load(open("results/summary_sweep.json"))["clasp"]["grip_clearance"]
def gp(d,mean): g=next(x for x in _C if x["d_mm"]==d and x["mean_deg"]==mean); return g["armL"],g["armR"]
PEN_L,PEN_R=gp(8,-10); OPEN_L,OPEN_R=gp(25,-10)
def pen_mesh(d,aL,aR,length=140):
    c=trimesh.creation.cylinder(radius=d/2,height=length,sections=48); c.apply_transform(Rm(np.pi/2,[0,1,0]))
    c.apply_translation([0,SH[1]-FORE_R,SH[2]]); c.apply_transform(Rm(np.radians(-(aL+aR)/2),[1,0,0],SH)); return c
COL=dict(torso_front="#e8893a",torso_back="#c8742f",yaw_collar="#8a9aa8",
         head_back="#d9a441",head_front="#efc35a",
         arm_L="#3d85c6",arm_R="#6aa84f",
         shoulder_bracket_L="#1f4e79",shoulder_bracket_R="#38612a",
         tray="#7a5a3a", bezel="#333333",
         yaw_coupler="#6b6b6b", yaw_retainer_A="#9aa0a6", yaw_retainer_B="#9aa0a6",
         yaw_thrust_washer="#c0392b",
         dummy_servo_yaw="#2c3e50", dummy_servo_arm_L="#2c3e50", dummy_servo_arm_R="#2c3e50",
         dummy_horn_yaw="#f1c40f", dummy_horn_arm_L="#f1c40f", dummy_horn_arm_R="#f1c40f",
         dummy_speaker="#1abc9c", dummy_amp="#16a085", dummy_mic="#27ae60",
         dummy_pi="#8e44ad", dummy_cam="#9b59b6")
HEAD={"head_back","head_front","yaw_coupler","yaw_retainer_A","yaw_retainer_B","dummy_cam"}
ARML={"arm_L","dummy_horn_arm_L"}; ARMR={"arm_R","dummy_horn_arm_R"}
M={}
for p in COL:
    if p=="bezel": continue
    m=trimesh.load(stl_path(p))
    if len(m.faces)>9000:
        try: m=m.simplify_quadric_decimation(face_count=9000)
        except Exception: pass
    M[p]=m
def T(p,yaw=0,aL=REST_L,aR=REST_R):
    if p in HEAD: return Rm(np.radians(yaw),[0,0,1],[0,0,0])
    if p in ARML: return Rm(np.radians(-(aL-REST_L)),[1,0,0],SH)
    if p in ARMR: return Rm(np.radians(-(aR-REST_R)),[1,0,0],SH)
    return np.eye(4)
Lv=np.array([0.45,-0.7,0.6]); Lv/=np.linalg.norm(Lv)
def draw(ax,parts,pose,explode=None,alpha=None,lim=None,view=(16,-58),clip=None):
    tris=[]; cols=[]
    for p in parts:
        if p not in M: continue
        Tp=T(p,**pose)
        if explode and p in explode: Tp=Tm(explode[p])@Tp
        v=trimesh.transform_points(M[p].vertices,Tp); tri=v[M[p].faces]
        if clip is not None:
            cc=tri.mean(1); k=np.ones(len(cc),bool)
            for ax_i,(lo,hi) in enumerate(clip):
                k&=(cc[:,ax_i]>lo)&(cc[:,ax_i]<hi)
            tri=tri[k]
        if not len(tri): continue
        n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); n/=np.linalg.norm(n,axis=1)[:,None]+1e-9
        sh=0.40+0.60*np.clip(n@Lv,0,1)*0.85+0.15*np.abs(n@Lv)
        c=np.array(matplotlib.colors.to_rgb(COL[p])); a=(alpha or {}).get(p,1.0)
        tris.append(tri); cols.append(np.c_[np.clip(c*sh[:,None],0,1),np.full(len(sh),a)])
    ax.add_collection3d(Poly3DCollection(np.concatenate(tris),facecolors=np.concatenate(cols),edgecolors="none",linewidths=0))
    lim=lim or (-80,80,-80,80,-5,155)
    ax.set_xlim(lim[0],lim[1]); ax.set_ylim(lim[2],lim[3]); ax.set_zlim(lim[4],lim[5])
    ax.set_box_aspect((lim[1]-lim[0],lim[3]-lim[2],lim[5]-lim[4]),zoom=1.2)
    ax.set_proj_type("ortho"); ax.set_axis_off(); ax.view_init(*view)
FOOT="CAD only — unprinted evoKin V.01 STLs in imposed poses. Not a physical fit-check, not child-ready, bench power only."
SHELL=["torso_front","torso_back","tray","yaw_collar","yaw_thrust_washer","yaw_coupler","yaw_retainer_A","yaw_retainer_B",
       "head_back","head_front","arm_L","arm_R","shoulder_bracket_L","shoulder_bracket_R","dummy_horn_arm_L","dummy_horn_arm_R"]
def front34():
    M["pen"]=pen_mesh(8,PEN_L,PEN_R); COL["pen"]="#d62728"
    fig=plt.figure(figsize=(16,9),dpi=130)
    pose=dict(yaw=0,aL=PEN_L,aR=PEN_R)
    ax=fig.add_subplot(121,projection="3d"); draw(ax,SHELL+["pen"],pose,view=(14,-62))
    ax.set_title(f"Front 3/4 — clasping a Ø8 × 140 mm pen (arm L {PEN_L:+.1f}°, arm R {PEN_R:+.1f}°)",fontsize=11)
    ax=fig.add_subplot(122,projection="3d"); draw(ax,SHELL+["pen"],pose,view=(2,0),lim=(-80,80,-90,70,-5,155))
    ax.set_title("Side — forearm blades overlap across the middle; the pen is squeezed between them",fontsize=11)
    fig.suptitle("evoKin V.01 — clasp around the middle (two FS90MG arm servos, blades close like scissors)",fontsize=14)
    fig.text(0.5,0.02,FOOT,ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.9,0.0)
    fig.savefig("renders/cad/v01_clasp_pen.png",facecolor="white"); plt.close(fig); del M["pen"]; print("wrote renders/cad/v01_clasp_pen.png")
def head30():
    fig=plt.figure(figsize=(16,9),dpi=130)
    ax=fig.add_subplot(121,projection="3d"); draw(ax,SHELL,dict(yaw=30,aL=OPEN_L,aR=OPEN_R),view=(14,-62))
    ax.set_title(f"Head panned +30°, clasp open to 25 mm (Δ = {OPEN_L-OPEN_R:.1f}°)",fontsize=11)
    ax=fig.add_subplot(122,projection="3d"); draw(ax,SHELL,dict(yaw=0,aL=-6.25,aR=-13.75),view=(4,-90))
    ax.set_title("Front — clasp closed (Δ = 7.5° interlock, ≈1 mm blade gap); left forearm over right",fontsize=11)
    fig.suptitle("evoKin V.01 — head pan (±42°) and clasp range (≈1–25 mm, arm travel −45°…+30°)",fontsize=14)
    fig.text(0.5,0.02,FOOT,ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.9,0.0)
    fig.savefig("renders/cad/v01_clasp_open_head30.png",facecolor="white"); plt.close(fig); print("wrote renders/cad/v01_clasp_open_head30.png")
def shoulder():
    fig=plt.figure(figsize=(16,9),dpi=130)
    ax=fig.add_subplot(121,projection="3d")
    ex={"shoulder_bracket_L":[14,0,0],"dummy_servo_arm_L":[6,0,0],"arm_L":[34,0,0],"dummy_horn_arm_L":[24,0,0]}
    parts=["torso_back","tray","dummy_servo_arm_L","shoulder_bracket_L","arm_L","dummy_horn_arm_L","dummy_pi","dummy_amp"]
    draw(ax,parts,dict(yaw=0,aL=0,aR=REST_R),explode=ex,alpha={"torso_back":0.35},lim=(-10,110,-45,75,10,110),view=(18,-30))
    ax.set_title("Left shoulder, exploded outward along the axis\npod (torso_back) → FS90MG → cap (shoulder_bracket_L) → horn → arm hub",fontsize=10)
    ax=fig.add_subplot(122,projection="3d")
    parts=["torso_back","tray","yaw_collar","dummy_servo_yaw","dummy_horn_yaw","yaw_coupler","dummy_servo_arm_L","dummy_servo_arm_R",
           "shoulder_bracket_L","shoulder_bracket_R","dummy_pi","dummy_amp","dummy_speaker"]
    draw(ax,parts,dict(yaw=0),alpha={"torso_back":0.25},lim=(-60,60,-45,45,10,100),view=(10,-90))
    ax.set_title("Inside the torso, from the front (torso_front removed)\nthree FS90MG: head pan (centre top) and one per shoulder, above the tray",fontsize=10)
    fig.suptitle("evoKin V.01 — shoulder drive and servo layout (unchanged from v4)",fontsize=14)
    fig.text(0.5,0.02,FOOT+"  Yellow = assumed horn envelope (measure on arrival).",ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.88,0.0)
    fig.savefig("renders/cad/v01_shoulder_exploded.png",facecolor="white"); plt.close(fig); print("wrote renders/cad/v01_shoulder_exploded.png")
front34(); head30(); shoulder(); print("ok")
