# SPDX-License-Identifier: MIT
"""CAD stills of the exported Tomo by DreamMachina (formerly evoKin V.01) STLs (matplotlib, flat-shaded).
CAD only; imposed poses, not dynamics. Writes renders/cad/v01_hug_handle.png, v01_arms_open_tilt.png
and v01_shoulder_turret_exploded.png."""
import numpy as np, trimesh, os, sys, json, math, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from trimesh.transformations import rotation_matrix as Rm, translation_matrix as Tm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
os.makedirs("renders/cad", exist_ok=True)
import groove_geo as gg
R_AX=gg.eggr(78)+8.5; HX=R_AX*math.cos(math.radians(-35)); HY=R_AX*math.sin(math.radians(-35))
HL=[HX,HY,0]; HR=[-HX,HY,0]; TILT_AX=[0,6.0,119.0]
SW=json.load(open("results/summary_sweep.json")); GRIP={g["d_mm"]:g for g in SW["hug"]["grip"]}
COL=dict(torso_front="#e8893a",torso_back="#c8742f",yaw_collar="#8a9aa8",tray="#7a5a3a",
         neck_turret="#5d6d7e",tilt_hub="#e74c3c",head_back="#d9a441",head_front="#efc35a",
         arm_L="#3d85c6",arm_R="#6aa84f",paw_pad_L="#3a2a22",paw_pad_R="#3a2a22",
         yaw_coupler="#6b6b6b",yaw_retainer_A="#9aa0a6",yaw_retainer_B="#9aa0a6",yaw_thrust_washer="#c0392b",
         dummy_servo_yaw="#2c3e50",dummy_servo_tilt="#2c3e50",dummy_horn_yaw="#f1c40f",dummy_horn_tilt="#f1c40f",
         dummy_speaker="#1abc9c",dummy_amp="#16a085",dummy_mic="#27ae60",dummy_pi="#8e44ad",dummy_cam="#9b59b6")
TURRET={"neck_turret","yaw_coupler","yaw_retainer_A","yaw_retainer_B","dummy_servo_tilt","dummy_horn_yaw"}
HEAD={"head_back","head_front","tilt_hub","dummy_cam","dummy_horn_tilt"}
ARML={"arm_L","paw_pad_L"}; ARMR={"arm_R","paw_pad_R"}
M={}
for p in COL:
    m=trimesh.load(stl_path(p))
    if len(m.faces)>9000:
        try: m=m.simplify_quadric_decimation(face_count=9000)
        except Exception: pass
    M[p]=m
def T(p,yaw=0,tilt=0,aL=0,aR=0):
    if p in HEAD: return Rm(np.radians(yaw),[0,0,1],[0,0,0])@Rm(np.radians(tilt),[1,0,0],TILT_AX)
    if p in TURRET: return Rm(np.radians(yaw),[0,0,1],[0,0,0])
    if p in ARML: return Rm(np.radians(aL),[0,0,1],HL)
    if p in ARMR: return Rm(np.radians(-aR),[0,0,1],HR)
    return np.eye(4)
def rod(d,h=90):
    c=trimesh.creation.cylinder(radius=d/2,height=h,sections=48)
    z=np.array([0,0,1.0]); v=np.cross(z,gg.U); c.apply_transform(Rm(math.atan2(np.linalg.norm(v),gg.U[2]),v/np.linalg.norm(v)))
    c.apply_translation(gg.FR+gg.U*19.0+gg.N*(d/2+0.1)); return c
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
            for i,(lo,hi) in enumerate(clip): k&=(cc[:,i]>lo)&(cc[:,i]<hi)
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
NAME="Tomo by DreamMachina (formerly evoKin V.01)"
FOOT="CAD only — unprinted STLs in imposed poses. Not a physical fit-check, not child-ready, bench power only."
SHELL=["torso_front","torso_back","tray","yaw_collar","yaw_thrust_washer","neck_turret","head_back","head_front",
       "arm_L","arm_R","paw_pad_L","paw_pad_R"]
def hug():
    g=GRIP[12.5]; aL=g["L"]["open_deg"]; aR=g["R"]["open_deg"]
    M["rod"]=rod(12.5); COL["rod"]="#8b4513"
    fig=plt.figure(figsize=(16,9),dpi=130); pose=dict(aL=aL,aR=aR)
    ax=fig.add_subplot(121,projection="3d"); draw(ax,SHELL+["rod"],pose,view=(10,-70))
    ax.set_title(f"Front 3/4 — hugging a Ø12.5 round handle lying diagonally in the belly groove\n"
                 f"(left arm open {aL}°, {g['L']['pad_normal_force_N']} N; right arm open {aR}°, {g['R']['pad_normal_force_N']} N)",fontsize=11)
    ax=fig.add_subplot(122,projection="3d"); draw(ax,SHELL+["rod"],pose,view=(0,-90),lim=(-80,80,-80,40,-5,155))
    ax.set_title("Front: shoulder hinges just under the face; the left arm crosses the handle high (C_L),\nthe right arm low under the belly (C_R); TPU pads at both crossings",fontsize=11)
    fig.suptitle(f"{NAME} — Mirumi proportions: one egg, shoulder arms, diagonal grip (zero power to hold)",fontsize=14)
    fig.text(0.5,0.02,FOOT,ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.9,0.0)
    fig.savefig("renders/cad/v01_hug_handle.png",facecolor="white"); plt.close(fig); del M["rod"]; print("wrote renders/cad/v01_hug_handle.png")
def opened():
    fig=plt.figure(figsize=(16,9),dpi=130)
    ax=fig.add_subplot(121,projection="3d"); draw(ax,SHELL,dict(yaw=30,tilt=-10,aL=30,aR=30),view=(14,-62))
    o=SW["hug"]["open"]
    ax.set_title(f"Arms on the 30° open stop (pads ↔ belly L {o['pad_L_to_belly_mm']} / R {o['pad_R_to_belly_mm']} mm)\nhead pan +30°, looking up 10°",fontsize=11)
    ax=fig.add_subplot(122,projection="3d"); draw(ax,SHELL,dict(yaw=0,tilt=10,aL=0,aR=0),view=(2,0),lim=(-80,80,-90,70,-5,155))
    ax.set_title("Side — face cap nodding 10° inside the egg (tilt axis y=6, z=119)\narms closed on their rest stops",fontsize=11)
    fig.suptitle(f"{NAME} — hand-opened arms (0–30°) and head pan ±42° / tilt ±10° (2 × FS90MG)",fontsize=14)
    fig.text(0.5,0.02,FOOT,ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.9,0.0)
    fig.savefig("renders/cad/v01_arms_open_tilt.png",facecolor="white"); plt.close(fig); print("wrote renders/cad/v01_arms_open_tilt.png")
def exploded():
    fig=plt.figure(figsize=(16,9),dpi=130)
    ax=fig.add_subplot(121,projection="3d")
    ex={"arm_L":[0,0,-24],"paw_pad_L":[0,0,-24]}
    parts=["torso_front","arm_L","paw_pad_L"]
    draw(ax,parts,dict(),explode=ex,alpha={"torso_front":0.45},lim=(10,75,-65,0,40,100),view=(22,-40),clip=[(14,200),(-200,200),(30,110)])
    ax.set_title("Left shoulder hinge, arm dropped 24 mm: torso ear (spigot + stop lug + rear post) → arm knuckle\n"
                 "(spring recess, relief for 0–30°). M3 × 30 pin thread-formed into the ear, washer + nyloc under the knuckle.",fontsize=10)
    ax=fig.add_subplot(122,projection="3d")
    ex={"head_back":[0,22,30],"head_front":[0,-40,30],"tilt_hub":[-14,0,0],"dummy_cam":[0,-40,30]}
    parts=["yaw_collar","neck_turret","dummy_servo_tilt","dummy_horn_tilt","tilt_hub","head_back","head_front","dummy_cam","dummy_servo_yaw"]
    draw(ax,parts,dict(),explode=ex,alpha={"head_back":0.5,"head_front":0.35},lim=(-60,60,-90,60,60,180),view=(14,-60))
    ax.set_title("Neck, exploded: pan FS90MG in the collar → neck_turret (yaw) carries the tilt FS90MG;\n"
                 "tilt_hub (red) keys into head_back, M3 idler pivot on the other side",fontsize=10)
    fig.suptitle(f"{NAME} — shoulder hinge and pan/tilt neck",fontsize=14)
    fig.text(0.5,0.02,FOOT+"  Yellow = assumed horn envelope (measure on arrival).",ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.88,0.0)
    fig.savefig("renders/cad/v01_shoulder_turret_exploded.png",facecolor="white"); plt.close(fig); print("wrote renders/cad/v01_shoulder_turret_exploded.png")
hug(); opened(); exploded(); print("ok")
