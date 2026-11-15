# SPDX-License-Identifier: MIT
"""Quantitative contact/strap/loop/drive metrics for v3 from exported STLs + design params. Imposed kinematics only."""
import numpy as np, trimesh, json, csv, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
sys.path.insert(0,"scripts")
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
import importlib.util
P=json.load(open("results/design_params.json"))
from trimesh.transformations import rotation_matrix as Rm
names="torso_front torso_back tray clasp_drum arm_L arm_R shoulder_bracket_L shoulder_bracket_R paw_pad_L paw_pad_R sleeve_proxy_L sleeve_proxy_R fur_proxy_torso strap_env yaw_collar".split()
M={p:trimesh.load(stl_path(p)) for p in names}
for n in ("servo_yaw","servo_clasp","horn_yaw","horn_clasp","pi","cam","speaker","amp","mic"):
    M["dummy_"+n]=trimesh.load(stl_path("dummy_"+n))
PL=np.array([58,10,0.]); PR=np.array([-58,10,0.]); ratio=P["r_q"]/P["r_d"]
def T(p,c):
    if p.endswith("_L") and p!="strap_env": return Rm(np.radians(c),[0,0,1],PL)
    if p.endswith("_R"): return Rm(np.radians(-c),[0,0,1],PR)
    if p=="clasp_drum": return Rm(np.radians(-ratio*c),[0,0,1],[0,20,0])
    return np.eye(4)
def pose(p,c): m=M[p].copy(); m.apply_transform(T(p,c)); return m
def mindist(a,b,n=2500):
    """approx min surface distance (+ = clear, - = penetration depth): sampled surface points both ways, chunked"""
    best=1e9
    for x,y in ((a,b),(b,a)):
        bb=y.bounds; pts=x.sample(n,seed=3)
        near=np.all((pts>bb[0]-30)&(pts<bb[1]+30),axis=1)       # only points near the other part matter
        pts=pts[near] if near.any() else pts[:50]
        for i in range(0,len(pts),400):
            d=-trimesh.proximity.signed_distance(y,pts[i:i+400]); best=min(best,float(d.min()))
    return best
o={}
TH=P["th_c"]; ST=P["th_stop_c"]; SO=P["th_stop_o"]
# ---- centre meeting
cen={}
for c in (40,44,TH,ST):
    pl,pr,al,ar=pose("paw_pad_L",c),pose("paw_pad_R",c),pose("arm_L",c),pose("arm_R",c)
    cen[f"c{c}"]=dict(pad_to_pad_mm=round(mindist(pl,pr),3),core_to_core_mm=round(mindist(al,ar),3),
        padL_min_x=round(float(pl.bounds[0][0]),3),padR_max_x=round(float(pr.bounds[1][0]),3))
# alignment of tip faces at TH
pl,pr=pose("paw_pad_L",TH),pose("paw_pad_R",TH)
fl=pl.vertices[np.abs(pl.vertices[:,0]-pl.bounds[0][0])<0.05]; fr=pr.vertices[np.abs(pr.vertices[:,0]-pr.bounds[1][0])<0.05]
cen["tip_face_L_yz_range"]=[np.round(fl[:,1:].min(0),2).tolist(),np.round(fl[:,1:].max(0),2).tolist()]
cen["tip_face_R_yz_range"]=[np.round(fr[:,1:].min(0),2).tolist(),np.round(fr[:,1:].max(0),2).tolist()]
cen["tip_face_overlap_area_mm2"]=round(float((min(fl[:,1].max(),fr[:,1].max())-max(fl[:,1].min(),fr[:,1].min()))*(min(fl[:,2].max(),fr[:,2].max())-max(fl[:,2].min(),fr[:,2].min()))),1)
cen["pad_proxy"]="soft non-printed foam template: tip pad 3.40 mm, strap-face pad 4.20 mm thick; stiffness UNKNOWN"; cen["design_pad_overlap_at_th_c_mm"]=0.30; cen["design_pad_into_strap_at_th_c_mm"]=0.20; cen["nominal_core_gap_at_th_c_mm"]=6.5
# pad compression at stop: overlap along x
cen["pad_stack_overlap_at_stop_mm"]=round(float(pose("paw_pad_R",ST).bounds[1][0]-pose("paw_pad_L",ST).bounds[0][0]),3)
o["centre_meeting"]=cen
# ---- strap
S=M["strap_env"]; st={}
for c in (0,TH,ST):
    st[f"c{c}"]=dict(padL_to_strap=round(mindist(pose("paw_pad_L",c),S),3),padR_to_strap=round(mindist(pose("paw_pad_R",c),S),3),
       armL_core_to_strap=round(mindist(pose("arm_L",c),S),3),armR_core_to_strap=round(mindist(pose("arm_R",c),S),3),
       sleeveL_to_strap=round(mindist(pose("sleeve_proxy_L",c),S),3))
st["fur_proxy_to_strap"]=round(mindist(M["fur_proxy_torso"],S),3); st["torso_back_to_strap"]=round(mindist(M["torso_back"],S),3)
o["strap_56x12"]=st
# ---- loop topology at z slices: is the strap section enclosed (captive) or connected to the outside (enter/exit)?
import shapely
def shadow(m):
    """xy footprint of a part = union of its upward-facing triangles projected to xy (closed mesh -> exact shadow)"""
    f=m.faces[m.face_normals[:,2]>1e-6]; tri=m.vertices[f][:,:,:2]
    polys=shapely.polygons(np.concatenate([tri,tri[:,:1]],axis=1))
    polys=polys[shapely.area(polys)>1e-9]
    return shapely.union_all(polys).buffer(0)
loop={}
solid_parts=["torso_back","torso_front","shoulder_bracket_L","shoulder_bracket_R","arm_L","arm_R","paw_pad_L","paw_pad_R"]
def enclosed_at(sh,d):
    g=sh.buffer(d,join_style=2) if d>0 else sh
    free=box(-250,-250,250,250).difference(g); comps=list(getattr(free,'geoms',[free]))
    comp=[k for k in comps if k.contains(Point(0,50))]
    return (bool(comp) and not comp[0].intersects(box(-250,240,250,250).boundary)), (comp[0] if comp else None)
for c in (0,17,20,30,40,44,TH,ST):
    sh=unary_union([shadow(pose(p,c)) for p in solid_parts])
    e0,comp=enclosed_at(sh,0); lo,hi=0.0,6.0
    if not e0:
        if not enclosed_at(sh,hi)[0]: hi=None
        else:
            for _ in range(16):
                mid=(lo+hi)/2
                if enclosed_at(sh,mid)[0]: hi=mid
                else: lo=mid
    else: hi=0.0
    rec=dict(enclosed_as_modelled=e0, largest_escape_gap_mm=(round(2*hi,2) if hi is not None else ">12 (open)"))
    if comp is not None and e0: rec.update(loop_interior_bbox=[round(v,1) for v in comp.bounds],loop_interior_area_mm2=round(comp.area,1))
    loop[f"c{c}"]=rec
loop["method"]=("xy footprint (projection) of torso, brackets, arms and pads; a straight vertical strap spanning z20..110 can only move "
  "laterally through gaps in that footprint. largest_escape_gap = 2 x the smallest dilation that closes the loop = widest slot "
  "an edge-on strap would need. Flexible strap snaking between heights is NOT analysed.")
o["loop_topology"]=loop
# entry corridor clearance at open: distance from x=+-28 strap corridor (y>=44) to arms/pads at c=0 and c=SO
def corridor_clear(c):
    cor=trimesh.creation.box(extents=[56,300,90]); cor.apply_translation([0,44+150,65])
    return {p:round(mindist(pose(p,c),cor,3000),2) for p in ("arm_L","arm_R","paw_pad_L","paw_pad_R","sleeve_proxy_L","sleeve_proxy_R")}
o["entry_exit_corridor_open"]=dict(c0=corridor_clear(0),c_open_stop=corridor_clear(SO),
   definition="clearance to a 56 mm wide corridor x in [-28,28], y>=44, z 20..110 (strap path in/out); >0 = strap can enter/exit")
# corridor clear angle: largest clasp where corridor still clear
cc=None
for c in np.arange(0,45.1,1.0):
    d=min(mindist(pose(p,c),trimesh.creation.box(extents=[56,300,90],transform=trimesh.transformations.translation_matrix([0,194,65])),1500) for p in ("paw_pad_L","paw_pad_R","sleeve_proxy_L","sleeve_proxy_R"))
    if d>0: cc=float(c)
o["entry_exit_corridor_open"]["largest_clasp_deg_with_corridor_clear"]=cc
# ---- fur / sleeve clearances across travel
fur={}
for c in np.arange(SO,ST+0.01,7.0/1):
    fur[f"c{round(c,1)}"]=dict(sleeveL_to_fur=round(mindist(pose("sleeve_proxy_L",c),M["fur_proxy_torso"],2500),2),
      sleeveR_to_fur=round(mindist(pose("sleeve_proxy_R",c),M["fur_proxy_torso"],2500),2),
      padL_to_fur=round(mindist(pose("paw_pad_L",c),M["fur_proxy_torso"],1500),2),
      armL_to_fur=round(mindist(pose("arm_L",c),M["fur_proxy_torso"],2500),2))
o["fur_sleeve_proxy_clearance_mm"]=fur
json.dump(o,open("results/metrics_contact.json","w"),indent=1,default=float)
print(json.dumps(o,indent=1,default=float))
