# SPDX-License-Identifier: MIT
"""CAD stills of the exported Tomo by DreamMachina (formerly evoKin V.01) STLs (matplotlib, flat-shaded).
CAD only; imposed poses, not dynamics. Writes renders/cad/v01_hug_handle.png, v01_arms_open_tilt.png
and v01_hip_turret_exploded.png."""
import numpy as np, trimesh, os, sys, json, math, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from trimesh.transformations import rotation_matrix as Rm, translation_matrix as Tm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
os.makedirs("renders/cad", exist_ok=True)
HX,HY=49.95,-16.19; HL=[HX,HY,0]; HR=[-HX,HY,0]; TILT_AX=[0,6.0,119.0]
GF=-30.0; G_ANG=math.atan(0.25); G_N=np.array([0,-math.cos(G_ANG),-math.sin(G_ANG)])
SW=json.load(open("results/summary_sweep.json")); GRIP={g["d_mm"]:g for g in SW["hug"]["grip"]}
COL=dict(torso_front="#e8893a",torso_back="#c8742f",yaw_collar="#8a9aa8",tray="#7a5a3a",
         neck_turret="#5d6d7e",tilt_hub="#e74c3c",head_back="#d9a441",head_front="#efc35a",
         arm_L="#3d85c6",arm_R="#6aa84f",hip_cap_L="#1f4e79",hip_cap_R="#38612a",paw_pad_L="#3a2a22",paw_pad_R="#3a2a22",
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
def rod(d):
    c=trimesh.creation.cylinder(radius=d/2,height=130,sections=48); c.apply_transform(Rm(G_ANG,[1,0,0]))
    c.apply_translation(np.array([0,GF,30])+G_N*(d/2)); return c
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
       "arm_L","arm_R","hip_cap_L","hip_cap_R","paw_pad_L","paw_pad_R"]
def hug():
    g=GRIP[12.5]; a=g["open_deg"]
    M["rod"]=rod(12.5); COL["rod"]="#8b4513"
    fig=plt.figure(figsize=(16,9),dpi=130); pose=dict(aL=a,aR=a)
    ax=fig.add_subplot(121,projection="3d"); draw(ax,SHELL+["rod"],pose,view=(14,-62))
    ax.set_title(f"Front 3/4 — hugging a Ø12.5 round handle in the belly groove\n(arms open {a}°, ≈{g['paw_force_N']} N per paw)",fontsize=11)
    ax=fig.add_subplot(122,projection="3d"); draw(ax,SHELL+["rod"],pose,view=(90,-90),lim=(-80,80,-80,40,-5,155),clip=[(-200,200),(-200,200),(-10,40)])
    ax.set_title("Top section at the arms (z < 40) \npaws close on the handle, rigid arm ≈1.5 mm clear; TPU pads take the squash",fontsize=11)
    fig.suptitle(f"{NAME} — Mirumi-style passive spring hug (torsion spring per hip, zero power to hold)",fontsize=14)
    fig.text(0.5,0.02,FOOT,ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.9,0.0)
    fig.savefig("renders/cad/v01_hug_handle.png",facecolor="white"); plt.close(fig); del M["rod"]; print("wrote renders/cad/v01_hug_handle.png")
def opened():
    fig=plt.figure(figsize=(16,9),dpi=130)
    ax=fig.add_subplot(121,projection="3d"); draw(ax,SHELL,dict(yaw=30,tilt=-10,aL=40,aR=40),view=(14,-62))
    o=SW["hug"]["open"]
    ax.set_title(f"Arms on the 40° open stop (pad ↔ belly {o['pad_to_belly_mm']} mm)\nhead pan +30°, looking up 10°",fontsize=11)
    ax=fig.add_subplot(122,projection="3d"); draw(ax,SHELL,dict(yaw=0,tilt=10,aL=0,aR=0),view=(2,0),lim=(-80,80,-90,70,-5,155))
    ax.set_title("Side — nodding 10° (tilt axis y=6, z=119)\narms closed on their rest stops",fontsize=11)
    fig.suptitle(f"{NAME} — hand-opened arms (0–40°) and head pan ±42° / tilt ±10° (2 × FS90MG)",fontsize=14)
    fig.text(0.5,0.02,FOOT,ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.9,0.0)
    fig.savefig("renders/cad/v01_arms_open_tilt.png",facecolor="white"); plt.close(fig); print("wrote renders/cad/v01_arms_open_tilt.png")
def exploded():
    fig=plt.figure(figsize=(16,9),dpi=130)
    ax=fig.add_subplot(121,projection="3d")
    ex={"hip_cap_L":[0,0,-22],"arm_L":[0,0,0],"paw_pad_L":[0,0,0]}
    parts=["torso_front","hip_cap_L","arm_L","paw_pad_L"]
    draw(ax,parts,dict(),explode=ex,alpha={"torso_front":0.45},lim=(20,80,-60,0,-25,50),view=(22,-40),clip=[(24,200),(-200,200),(-40,60)])
    ax.set_title("Left hip hinge, cap dropped 22 mm: torso ear (spigot + stop lug) → arm knuckle (spring recess,\n"
                 "relief for 0–40°) → hip_cap on 2 × M2.5. M3 pin, nyloc in the cap. Torsion spring in the knuckle recess.",fontsize=10)
    ax=fig.add_subplot(122,projection="3d")
    ex={"head_back":[0,22,30],"head_front":[0,-40,30],"tilt_hub":[-14,0,0],"dummy_cam":[0,-40,30]}
    parts=["yaw_collar","neck_turret","dummy_servo_tilt","dummy_horn_tilt","tilt_hub","head_back","head_front","dummy_cam","dummy_servo_yaw"]
    draw(ax,parts,dict(),explode=ex,alpha={"head_back":0.5,"head_front":0.35},lim=(-60,60,-90,60,60,180),view=(14,-60))
    ax.set_title("Neck, exploded: pan FS90MG in the collar → neck_turret (yaw) carries the tilt FS90MG;\n"
                 "tilt_hub (red) keys into head_back, M3 idler pivot on the other side",fontsize=10)
    fig.suptitle(f"{NAME} — hip hinge and pan/tilt neck",fontsize=14)
    fig.text(0.5,0.02,FOOT+"  Yellow = assumed horn envelope (measure on arrival).",ha="center",fontsize=8.5); plt.subplots_adjust(0.0,0.05,1.0,0.88,0.0)
    fig.savefig("renders/cad/v01_hip_turret_exploded.png",facecolor="white"); plt.close(fig); print("wrote renders/cad/v01_hip_turret_exploded.png")
hug(); opened(); exploded(); print("ok")
