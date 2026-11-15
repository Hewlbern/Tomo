# SPDX-License-Identifier: MIT
"""Two stills of the actual exported v3 STLs. CAD only; imposed poses, not dynamics."""
import numpy as np, trimesh, json, os, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from trimesh.transformations import rotation_matrix as Rm, translation_matrix as Tm
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
os.makedirs("renders", exist_ok=True)

COL=dict(torso_front="#e8893a",torso_back="#c8742f",yaw_collar="#8a9aa8",
         head_back="#d9a441",head_front="#efc35a",
         arm_L="#3d85c6",arm_R="#6aa84f",
         shoulder_bracket_L="#2f5f8f",shoulder_bracket_R="#4f7a3a",
         tray="#7a5a3a", clasp_drum="#5b3d1f",
         yaw_coupler="#6b6b6b", yaw_retainer_A="#9aa0a6", yaw_retainer_B="#9aa0a6",
         yaw_thrust_washer="#c0392b",  # highlight: new washer
         dummy_servo_yaw="#2c3e50", dummy_servo_clasp="#2c3e50",
         dummy_horn_yaw="#f1c40f", dummy_horn_clasp="#f1c40f",
         dummy_speaker="#1abc9c", dummy_amp="#16a085", dummy_mic="#27ae60",
         dummy_pi="#8e44ad", dummy_cam="#9b59b6")
# explode offsets (highlight the fixes)
EX=dict(torso_front=[0,-28,0], torso_back=[0,28,0],
        head_front=[0,-36,18], head_back=[0,28,18],
        yaw_collar=[0,0,8], yaw_thrust_washer=[0,0,16],
        yaw_coupler=[0,0,22], yaw_retainer_A=[18,0,6], yaw_retainer_B=[-18,0,6],
        tray=[0,0,-14], clasp_drum=[0,12,-6],
        dummy_servo_yaw=[0,-8,4], dummy_servo_clasp=[0,14,-8],
        dummy_horn_yaw=[0,-8,10], dummy_horn_clasp=[0,14,-2],
        dummy_speaker=[0,-40,0], dummy_amp=[20,16,-14], dummy_mic=[16,-36,8],
        dummy_pi=[0,-18,-14], dummy_cam=[0,-48,22],
        arm_L=[25,0,0], arm_R=[-25,0,0],
        shoulder_bracket_L=[20,0,0], shoulder_bracket_R=[-20,0,0])
HIGHLIGHT={"yaw_thrust_washer","dummy_speaker","dummy_amp","dummy_mic","dummy_horn_yaw","dummy_horn_clasp"}

PARTS=list(COL)
M={}
for p in PARTS:
    try:
        path=stl_path(p)
    except FileNotFoundError:
        print("missing", p); continue
    m=trimesh.load(path)
    if len(m.faces)>8000:
        try: m=m.simplify_quadric_decimation(face_count=8000)
        except Exception: pass
    M[p]=m

Lv=np.array([0.35,-0.75,0.55]); Lv/=np.linalg.norm(Lv)
CLIP=None
def add(ax,m,col,T=np.eye(4),alpha=1.0):
    v=trimesh.transform_points(m.vertices,T); tri=v[m.faces]
    if CLIP is not None:
        cc=tri.mean(1)
        k=(cc[:,0]>CLIP[0])&(cc[:,0]<CLIP[1])&(cc[:,1]>CLIP[2])&(cc[:,1]<CLIP[3])&(cc[:,2]>CLIP[4])&(cc[:,2]<CLIP[5])
        tri=tri[k]
        if not len(tri): return
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); n/=np.linalg.norm(n,axis=1)[:,None]+1e-9
    sh=0.42+0.58*np.abs(n@Lv); c=np.array(matplotlib.colors.to_rgb(col))
    ax.add_collection3d(Poly3DCollection(tri,facecolors=np.c_[np.clip(c*sh[:,None],0,1),np.full(len(sh),alpha)],edgecolors="none",linewidths=0))

def explode_T(p):
    return Tm(EX.get(p,[0,0,0]))

def frame(ax, view, lim, parts=None, use_explode=False, alpha_map=None):
    for p,m in M.items():
        if parts and p not in parts: continue
        T=explode_T(p) if use_explode else np.eye(4)
        a=1.0 if not alpha_map else alpha_map.get(p,1.0)
        add(ax,m,COL[p],T,a)
    ax.set_xlim(lim[0],lim[1]); ax.set_ylim(lim[2],lim[3]); ax.set_zlim(lim[4],lim[5])
    ax.set_box_aspect((lim[1]-lim[0],lim[3]-lim[2],lim[5]-lim[4]),zoom=1.25)
    ax.set_proj_type("ortho"); ax.set_axis_off()
    ev,az={"front":(8,-90),"rear":(12,90),"rear34":(18,130),"side":(6,0),"section":(8,0),"iso":(18,-50)}[view]
    ax.view_init(ev,az)

FOOT="CAD only — unprinted v3 STLs in an imposed pose. Not a physical fit-check, not child-ready, bench power only."

def exploded():
    fig=plt.figure(figsize=(16,9.2),dpi=140)
    ax=fig.add_subplot(111,projection="3d")
    frame(ax,"iso",(-95,95,-90,90,-10,170), use_explode=True)
    ax.text(0,-75,68,"Adafruit 3351\n3 W 4 Ω, 70×30×17\n(amp-matched)",color="#0e7a66",fontsize=8,ha="center")
    ax.text(8,8,128,"thrust washer (red)\n0.8 mm, 0.30 mm gap\n30° cone, no support on face",color="#922b21",fontsize=8,ha="center")
    ax.text(55,30,48,"FS90MG clasp seat\n27.7 mm span, 1.7 pilots\n4.0 mm horn gap",color="#1a252f",fontsize=8,ha="center")
    ax.text(-8,-55,155,"FS90MG yaw seat\ns_off=2.55 (8.7 from body end)",color="#1a252f",fontsize=8,ha="center")
    ax.text(70,5,18,"M2.5 2.8 / 2.1\nlip/groove 0.25\n0.4 mm chamfer",color="#6b3a12",fontsize=8,ha="center")
    ax.set_title("Critter v3 exploded — FS90MG seats, seam lip, thrust washer, electronics pockets\n(red = new washer, yellow = assumed horn envelope, teal = speaker / amp / mic)",fontsize=12)
    fig.text(0.5,0.015,FOOT,ha="center",fontsize=8.5)
    plt.subplots_adjust(0.02,0.04,0.98,0.93)
    fig.savefig("renders/v3_exploded_fixes.png",facecolor="white"); plt.close(fig)
    print("wrote renders/v3_exploded_fixes.png")

def section():
    """Zoomed mechanism views, not a jagged half-shell clip."""
    global CLIP
    fig=plt.figure(figsize=(16,8.4),dpi=140)
    # left: yaw internals, no triangle clip — translucent shells, solid stack
    ax=fig.add_subplot(121,projection="3d")
    yaw_solid=["yaw_collar","yaw_thrust_washer","yaw_coupler","yaw_retainer_A","yaw_retainer_B",
               "dummy_servo_yaw","dummy_horn_yaw"]
    yaw_ghost=["head_back","torso_front","torso_back"]
    amap={p:0.12 for p in yaw_ghost}
    CLIP=(-40,40,-40,40,50,150)
    frame(ax,"side",(-40,40,-40,40,70,150), parts=yaw_solid+yaw_ghost, use_explode=False, alpha_map=amap)
    ax.set_title("Yaw stack (side, shells ghosted)\nFS90MG → boss 88.3 → horn 88.3–90.3 → coupler on horn\nwasher 97.4–98.2, 0.30 mm gap, 30° cone",fontsize=9)
    ax.text(12,0,84,"FS90MG",color="#1a252f",fontsize=7)
    ax.text(12,0,89.3,"horn (assumed)",color="#b7950b",fontsize=7)
    ax.text(14,0,97.8,"washer + 0.3 gap",color="#922b21",fontsize=7)
    # right: clasp internals
    ax=fig.add_subplot(122,projection="3d")
    clasp_solid=["tray","clasp_drum","dummy_servo_clasp","dummy_horn_clasp","dummy_amp"]
    clasp_ghost=["torso_front","torso_back"]
    amap={p:0.12 for p in clasp_ghost}
    CLIP=(-45,45,-15,50,20,80)
    frame(ax,"side",(-40,40,-15,50,22,78), parts=clasp_solid+clasp_ghost, use_explode=False, alpha_map=amap)
    ax.set_title("Clasp servo (side, shells ghosted)\ncase top 51, boss 55.3, horn 55.3–57.3\ndrum 59.3 (4.0 mm above boss = 2.0 horn + 2.0 air)",fontsize=9)
    ax.text(14,20,51,"FS90MG",color="#1a252f",fontsize=7)
    ax.text(14,20,56.5,"horn 2.0",color="#b7950b",fontsize=7)
    ax.text(14,20,62,"drum + 2.0 air",color="#5b3d1f",fontsize=7)
    ax.text(8,8,42,"amp pocket",color="#0e6655",fontsize=7)
    CLIP=None
    fig.text(0.5,0.015,FOOT+"  Yellow = assumed horn envelope (not on the official drawing; measure on arrival).",ha="center",fontsize=8)
    plt.subplots_adjust(0.02,0.05,0.98,0.90,0.04)
    fig.savefig("renders/v3_yaw_and_servo_section.png",facecolor="white"); plt.close(fig)
    print("wrote renders/v3_yaw_and_servo_section.png")

exploded(); section()
print("ok")
