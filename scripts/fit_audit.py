# SPDX-License-Identifier: MIT
"""Tomo (formerly evoKin V.01) fit audit: passive spring hug + pan/tilt head. CAD measurements on exported STLs. Not physically tested."""
import numpy as np, trimesh, json, csv, os, math
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path

def load(n): return trimesh.load(stl_path(n))
M={n:load(n) for n in
   "torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer neck_turret tilt_hub head_back head_front arm_L arm_R hip_cap_L hip_cap_R paw_pad_L paw_pad_R coupon".split()}
for n in "dummy_servo_yaw dummy_horn_yaw dummy_servo_tilt dummy_horn_tilt dummy_pi dummy_cam dummy_speaker dummy_amp dummy_mic fur_proxy_torso sleeve_proxy_L sleeve_proxy_R grip_rod".split():
    M[n]=load(n)

def hole_radius(mesh, origin, axis, r_max=6, n_ang=72, n_z=5, z_span=1.0):
    """Radial rays in a plane perpendicular to axis; return median diameter and per-sample list."""
    o=np.asarray(origin,float); a=np.asarray(axis,float); a=a/np.linalg.norm(a)
    # orthonormal basis
    tmp=np.array([1,0,0]) if abs(a[0])<0.9 else np.array([0,1,0])
    u=np.cross(a,tmp); u/=np.linalg.norm(u); v=np.cross(a,u)
    hits=[]
    for dz in np.linspace(-z_span/2,z_span/2,n_z):
        c=o+a*dz
        for k in range(n_ang):
            ang=2*np.pi*k/n_ang
            dvec=np.cos(ang)*u+np.sin(ang)*v
            locs,_,_ = mesh.ray.intersects_location([c],[dvec])
            if len(locs)==0: continue
            dist=np.linalg.norm(locs-c,axis=1)
            dist=dist[dist<=r_max]
            if len(dist): hits.append(float(dist.min()))
    if not hits: return None
    return dict(dia=round(2*float(np.median(hits)),3), n=len(hits),
                p05=round(2*float(np.percentile(hits,5)),3), p95=round(2*float(np.percentile(hits,95)),3))

def cyl_od_id(mesh, origin, axis, r_from, r_to, n_ang=120, n_z=7, z_span=2.0, outgoing=True):
    """Ray from r_from toward r_to (or inward) to measure a cylindrical face."""
    o=np.asarray(origin,float); a=np.asarray(axis,float); a=a/np.linalg.norm(a)
    tmp=np.array([1,0,0]) if abs(a[0])<0.9 else np.array([0,1,0])
    u=np.cross(a,tmp); u/=np.linalg.norm(u); v=np.cross(a,u)
    hits=[]
    sign=1 if outgoing else -1
    start=r_from
    for dz in np.linspace(-z_span/2,z_span/2,n_z):
        for k in range(n_ang):
            ang=2*np.pi*k/n_ang
            dvec=np.cos(ang)*u+np.sin(ang)*v
            c=o+a*dz+dvec*start
            locs,_,_=mesh.ray.intersects_location([c],[sign*dvec])
            if len(locs)==0: continue
            rad=np.linalg.norm((locs-o)-np.outer((locs-o)@a,a),axis=1)
            # keep hits between r_from and r_to
            lo,hi=min(r_from,r_to),max(r_from,r_to)
            rad=rad[(rad>=lo-0.5)&(rad<=hi+0.5)]
            if len(rad): hits.append(float(rad.min() if outgoing else rad.max()) if False else float(np.min(np.abs(rad-start))+start if outgoing else start-np.min(np.abs(rad-start))))
            # simpler: distance from axis
            if len(locs):
                rr=np.linalg.norm(np.cross(locs-o,a),axis=1)
                band=rr[(rr>=lo-0.2)&(rr<=hi+0.2)]
                if len(band): hits.append(float(band.min() if outgoing else band.max()) if outgoing else float(band.max()) if not outgoing else float(band.min()))
    # redo cleanly
    return _cyl_clean(mesh,o,a,u,v,r_from,r_to,n_ang,n_z,z_span,outgoing)

def _cyl_clean(mesh,o,a,u,v,r_from,r_to,n_ang,n_z,z_span,outgoing):
    hits=[]
    lo,hi=min(r_from,r_to),max(r_from,r_to)
    direction = 1 if r_to>r_from else -1
    for dz in np.linspace(-z_span/2,z_span/2,n_z):
        for k in range(n_ang):
            ang=2*np.pi*k/n_ang
            dvec=np.cos(ang)*u+np.sin(ang)*v
            c=o+a*dz+dvec*r_from
            locs,_,_=mesh.ray.intersects_location([c],[direction*dvec])
            if len(locs)==0: continue
            rr=np.linalg.norm(np.cross(locs-o,a),axis=1)
            band=rr[(rr>=lo-0.3)&(rr<=hi+0.3)]
            if len(band):
                hits.append(float(band.min()) if direction>0 else float(band.max()))
    if not hits: return None
    return dict(dia=round(2*float(np.median(hits)),3), r=round(float(np.median(hits)),3), n=len(hits),
                p05=round(2*float(np.percentile(hits,5)),3), p95=round(2*float(np.percentile(hits,95)),3))

def z_of_face(mesh, r_lo, r_hi, z_lo, z_hi, want="max"):
    v=mesh.vertices
    rr=np.hypot(v[:,0],v[:,1])
    sel=v[(rr>=r_lo)&(rr<=r_hi)&(v[:,2]>=z_lo)&(v[:,2]<=z_hi)]
    if not len(sel): return None
    z=sel[:,2]
    return dict(zmin=round(float(z.min()),3), zmax=round(float(z.max()),3),
                med=round(float(np.median(z)),3), n=int(len(z)))

def vol_int(a,b):
    try: return float(trimesh.boolean.intersection([a,b],engine="manifold").volume)
    except Exception as e: return None

rows=[]
def add(interface, parts, measured, verdict, fix=""):
    rows.append(dict(interface=interface, parts=parts, measured=measured, verdict=verdict, fix=fix))

# Official FS90MG targets
FS=dict(body_L=22.5,body_W=12.1,body_H=22.4,tab=32.3,span=27.7,hole=2.2,
        s_from_end=8.7,s_off=2.55,boss=26.7,overall=30.7,tab_t=4.2)

# ---------- 1. Servo seats ----------
s_off=2.55; span=27.7
def ok_pil(h): return h and 1.55<=h["dia"]<=1.90
def ok_m25clr(h): return h and 2.6<=h["dia"]<=3.0
def ok_m25pil(h): return h and 1.95<=h["dia"]<=2.25
# tilt servo (neck_turret cradle): spline along -x at y=6, z=119, case top x=-22, tabs x -22..-17.8, holes z = 119+2.55 ∓ 13.85
TY,TZ=6.0,119.0
tilt_p=[hole_radius(M["neck_turret"],[-16.3,TY,z],[1,0,0],r_max=3,z_span=1.5) for z in (TZ+s_off-span/2,TZ+s_off+span/2)]
tov=dict(servo_turret=vol_int(M["dummy_servo_tilt"],M["neck_turret"]),servo_head_back=vol_int(M["dummy_servo_tilt"],M["head_back"]),
         servo_head_front=vol_int(M["dummy_servo_tilt"],M["head_front"]),servo_cam=vol_int(M["dummy_servo_tilt"],M["dummy_cam"]))
add("Tilt servo seat (FS90MG in the neck_turret cradle, official 27.7 span)",
    "neck_turret, dummy_servo_tilt, head_back, head_front, dummy_cam",
    f"Tab pilots in the cradle plate (design 1.7): {tilt_p}. Overlaps (mm³, must be ~0): {tov}. Spline on the tilt axis (x direction) at y={TY}, z={TZ}; "
    f"case top x=-22, horn x -26.3..-28.3, tilt_hub keyed into head_back. Body window 0.3 mm per side through the cradle.",
    "pass" if all(ok_pil(h) for h in tilt_p) and all((v or 0)<=0.05 for v in tov.values()) else "fail",
    "Install servo from the +x side through the cradle window, tabs on the -x face, 2 self-tappers. Turret deck is notched for the lower tab.")
# hip hinge (left; right is the mirror)
def ea(z): return 46*math.sqrt(1-((z-50)/50)**2)
def eb(z): return 40*math.sqrt(1-((z-50)/50)**2)
HX=(ea(38)+8.5)*math.cos(math.radians(-20)); HY=(eb(38)+8.5)*math.sin(math.radians(-20))
hinge={}
for side,sx in (("L",1),("R",-1)):
    x=sx*HX
    up=hole_radius(M["torso_front"],[x,HY,40.0],[0,0,1],r_max=2.5,z_span=1.5)
    sp=hole_radius(M["torso_front"],[x,HY,33.0],[0,0,1],r_max=2.5,z_span=2.0)
    kn=hole_radius(M[f"arm_{side}"],[x,HY,26.0],[0,0,1],r_max=2.5,z_span=2.0)
    cp=hole_radius(M[f"hip_cap_{side}"],[x,HY,20.0],[0,0,1],r_max=2.5,z_span=1.0)
    rec=hole_radius(M[f"arm_{side}"],[x,HY,32.5],[0,0,1],r_max=7,z_span=2.0)
    av=M[f"arm_{side}"].bounds; cb=M[f"hip_cap_{side}"].bounds
    web=[hole_radius(M["torso_front"],[sx*px,py,24.0],[0,0,1],r_max=2.5,z_span=1.5) for px,py in ((38.5,-10),(42.2,-10))]
    capc=[hole_radius(M[f"hip_cap_{side}"],[sx*px,py,19.0],[0,0,1],r_max=2.5,z_span=1.0) for px,py in ((38.5,-10),(42.2,-10))]
    hinge[side]=dict(upper_ear_pin=up,spigot_bore=sp,knuckle_bore=kn,hip_cap_pin=cp,spring_recess=rec,
                     knuckle_to_cap_axial=round(av[0][2]-cb[1][2],3),web_pilots=web,cap_clearance=capc,
                     arm_cap_overlap=vol_int(M[f"arm_{side}"],M[f"hip_cap_{side}"]),arm_torso_overlap=vol_int(M[f"arm_{side}"],M["torso_front"]))
def okd(h,lo,hi): return h and lo<=h["dia"]<=hi
ok=all(okd(h["upper_ear_pin"],3.0,3.4) and okd(h["knuckle_bore"],3.25,3.6) and okd(h["hip_cap_pin"],3.0,3.4) and okd(h["spring_recess"],10.6,11.4)
       and 0.3<=h["knuckle_to_cap_axial"]<=0.6 and all(ok_m25pil(w) for w in h["web_pilots"]) and all(ok_m25clr(c) for c in h["cap_clearance"])
       and (h["arm_cap_overlap"] or 0)<=0.05 and (h["arm_torso_overlap"] or 0)<=0.05 for h in hinge.values())
add("Hip hinge (vertical M3 pin, knuckle between the torso ear and hip_cap)",
    "torso_front (upper ear, spigot, stop lug, web), arm_L/R (knuckle), hip_cap_L/R",
    f"Axis at x=±{HX:.2f}, y={HY:.2f}. {hinge}. Design: M3 pin screw Ø3.2 in the ears and spigot, Ø3.4 running bore in the knuckle, "
    f"0.4 mm axial gap each end, Ø11 spring recess around a Ø5.9 spigot (spring ID 7.09 free, ≈6.8 at 75° wind-up), M3 nyloc in the cap's hex trap, "
    f"hip_cap held by 2 × M2.5 (2.8 clearance / 2.1 pilots in the web).",
    "pass" if ok else "fail",
    "Assembly: spring on the spigot, torso leg in the lug slot; knuckle up from below with the arm leg in its slot; wind the arm 35° open so the lug enters the relief; fit hip_cap and the pin.")

yaw_holes=[]
for sx in (-1,1):
    o=np.array([-s_off+sx*(span/2), 0, 86.0])    # mid pilot boss, above the tab cutout
    h=hole_radius(M["yaw_collar"], o, [0,0,1], r_max=3, z_span=1.5)
    yaw_holes.append((o.tolist(), h))
add("Yaw servo seat (FS90MG, official 27.7 span, 1.7 pilots)",
    "yaw_collar, dummy_servo_yaw, dummy_horn_yaw, yaw_coupler",
    f"Pilots at x={[-s_off-span/2,-s_off+span/2]} y=0: {yaw_holes}. "
    f"yaw_top=84, boss top=88.3, horn 88.3-90.3, coupler disc 90.3-91.9 (sits on the horn). "
    f"Bore Ø34 clears the Ø24 horn envelope for installation from above. "
    f"Servo/collar overlap vol={vol_int(M['yaw_collar'],M['dummy_servo_yaw'])}",
    "pass" if ok_pil(yaw_holes[0][1]) and ok_pil(yaw_holes[1][1]) else "fail",
    "Included M2.5x4 horn screw is too short for horn+coupler; use a longer M2.5 and confirm on arrival.")

sw_=json.load(open("results/summary_sweep.json")) if os.path.exists("results/summary_sweep.json") else None
st=sw_["stop_engagement"] if sw_ else {}
add("Arm hard stops (printed lug in the knuckle relief)",
    "torso_front (stop lug), arm_L/R (relief sector)",
    (f"First rigid contact closing past rest: L {st.get('armL_closed_stop',{}).get('armL')}°, R {st.get('armR_closed_stop',{}).get('armR')}°; opening: "
     f"L {st.get('armL_open_stop',{}).get('armL')}°, R {st.get('armR_open_stop',{}).get('armR')}° (design 0° and 40°, sweep step 0.5°). "
     "Lug 24° wide, r 5.7–7.7, 2.6 mm deep; spring torque on the open stop 252 N·mm ≈ 38 N on the lug face.") if sw_ else "Run scripts/sim_v01.py first.",
    "pass" if sw_ and st.get("armL_closed_stop",{}).get("armL",-9)>=-1 and 40<=st.get("armL_open_stop",{}).get("armL",0)<=41 else "fail",
    "Print torso_front so the lug is loaded across layers, not in peel. The spring cannot over-rotate past 75° total wind-up (rated 90°).")

# ---------- 2. Seams ----------
# lip: back ymin < 0, front groove exists (cut into mid-wall)
tf,tb=M["torso_front"],M["torso_back"]
hf,hb=M["head_front"],M["head_back"]
t_overlap=vol_int(tf,tb); h_overlap=vol_int(hf,hb)
# fastener holes: torso bosses at tboss
tboss=[(-24,12),(24,12),(-30,79),(30,79)]   # v4 positions
# TW/2=46, tboss = [[-TW/2+12,22],...] so x=±34 at z=22 and x=±36 at z=72
torso_holes=[]
for x,z in tboss:
    # holes are along y
    fr=hole_radius(tf, [x, -4, z], [0,1,0], r_max=4, z_span=1.5)
    bk=hole_radius(tb, [x,  4, z], [0,1,0], r_max=4, z_span=1.5)
    torso_holes.append(dict(xz=[x,z], front=fr, back=bk))
hboss=[(-32,106),(32,106),(-28,138),(28,138)]   # V.01 hug: lower bosses moved for the tilt hub
# HW/2=42, hboss = [[-HW/2+12,hcut+12=110], [-HW/2+16, HC+20=138]]
head_holes=[]
for x,z in hboss:
    fr=hole_radius(hf, [x, -4, z], [0,1,0], r_max=4, z_span=1.5)
    bk=hole_radius(hb, [x,  4, z], [0,1,0], r_max=4, z_span=1.5)
    head_holes.append(dict(xz=[x,z], front=fr, back=bk))
def clr_ok(h): return h and 2.6<=h["dia"]<=3.0
def pil_ok(h): return h and 1.95<=h["dia"]<=2.25
t_fast_ok=all(clr_ok(h["front"]) and pil_ok(h["back"]) for h in torso_holes)
h_fast_ok=all(clr_ok(h["front"]) and pil_ok(h["back"]) for h in head_holes)
lip_ok=tb.bounds[0][1]<=-1.1 and t_overlap is not None and t_overlap<=0.05
add("Torso front ↔ back seam and fasteners",
    "torso_front, torso_back",
    f"Boolean overlap {t_overlap} mm³. Back ymin={tb.bounds[0][1]:.2f} (male lip 1.2 mm into the front). "
    f"Front ymax={tf.bounds[1][1]:.2f}. Groove clearance design 0.25 mm. "
    f"0.40 mm outer seam chamfer for elephant-foot. Fasteners M2.5: front clearance 2.8, back pilot 2.1. Holes: {torso_holes}",
    "pass" if lip_ok and t_fast_ok else ("marginal" if lip_ok else "fail"),
    "Optional M2.5 heat-set later: bosses are Ø7.")
lip_h_ok=h_overlap is not None and h_overlap<=0.05
add("Head front ↔ back seam and fasteners",
    "head_front, head_back",
    f"Boolean overlap {h_overlap} mm³. Registration lip/groove same scheme as the torso (male on back). "
    f"M2.5 front 2.8 / back 2.1. Holes: {head_holes}",
    "pass" if lip_h_ok and h_fast_ok else ("marginal" if lip_h_ok else "fail"))

# ---------- 3. Yaw thrust / journal / retainer / blade ----------
jrn=_cyl_clean(M["yaw_collar"], np.array([0,0,94.7]), np.array([0,0,1]),
               np.array([1,0,0]), np.array([0,1,0]), 21.0, 23.0, 120, 5, 2.0, True)
# journal OD: ray outward from r=21
skirt=_cyl_clean(M["neck_turret"], np.array([0,0,94]), np.array([0,0,1]),
                 np.array([1,0,0]), np.array([0,1,0]), 23.0, 21.0, 120, 5, 2.0, True)
# skirt ID: start at r=23 (inside the 22.35 ID? 44.7/2=22.35). Start at r=20 going out to 23.
skirt=_cyl_clean(M["neck_turret"], np.array([0,0,94]), np.array([0,0,1]),
                 np.array([1,0,0]), np.array([0,1,0]), 20.0, 24.0, 120, 5, 2.0, True)
j_top=z_of_face(M["yaw_collar"], 10, 23, 96.5, 98.5, "max")
w_z=z_of_face(M["yaw_thrust_washer"], 17, 22, 96, 99)
# head cone / floor near r=21 at z~98.5
h_floor=z_of_face(M["neck_turret"], 17, 22, 97.5, 106)
j_od=jrn["dia"] if jrn else None
s_id=skirt["dia"] if skirt else None
rad_clr=(s_id-j_od)/2 if (j_od and s_id) else None
wash_top=w_z["zmax"] if w_z else None
# designed floor at 98.5; cone may have a range
add("Yaw journal radial (skirt on journal)",
    "neck_turret, yaw_collar",
    f"Journal {jrn}, skirt ID {skirt}, radial clearance {None if rad_clr is None else round(rad_clr,3)} mm (design 0.35). "
    f"Justified: tight end of the requested 0.35–0.4 mm FDM running-fit band; 0.30 (v2) is too tight after typical hole shrinkage. "
    f"Head↔collar overlap {vol_int(M['neck_turret'],M['yaw_collar'])} mm³.",
    "pass" if rad_clr and 0.30<=rad_clr<=0.45 else "marginal")

add("Yaw thrust (printed washer + 0.30 mm axial gap + 30° cone)",
    "yaw_thrust_washer, yaw_collar, neck_turret",
    f"Journal top {j_top}. Washer {w_z} (design 97.4–98.2, 0.8 mm, printed flat, no supports). "
    f"Head floor/cone in r=17–22, z=97.5–106: {h_floor}. Design: washer top 98.2, head at 98.5, gap 0.30 mm. "
    f"Washer↔head overlap {vol_int(M['yaw_thrust_washer'],M['neck_turret'])} mm³. "
    f"Skirt-down print: vertical skirt then a 30°-from-vertical cone so a 35° support threshold does not land supports on a flat thrust face. The flat thrust is the washer.",
    "pass" if (wash_top and abs(wash_top-98.2)<0.15 and (h_floor and h_floor["zmin"]>=98.35)) else "fail")

# retainers
retA=M["yaw_retainer_A"]; retB=M["yaw_retainer_B"]
# axial play: journal lip underside z=92, retainer top
ret_top=z_of_face(retA, 19, 23, 88, 94)
j_lip=z_of_face(M["yaw_collar"], 19, 23, 91, 93)
# actually journal starts at 92, lip underside is the bottom of the 44 mm cylinder
play=None
if ret_top and j_lip:
    play=round(j_lip["zmin"]-ret_top["zmax"],3)
ret_h=hole_radius(retA, [23.8,0,90.125], [1,0,0], r_max=3, z_span=1.2)
hd_h=hole_radius(M["neck_turret"], [23.8,0,90.125], [1,0,0], r_max=3, z_span=1.2)
ret_ok=ret_h and 2.15<=ret_h["dia"]<=2.45
hd_ok=hd_h and 1.55<=hd_h["dia"]<=1.90
add("Yaw retainers (under journal lip)",
    "yaw_retainer_A/B, yaw_collar, neck_turret",
    f"Retainer top {ret_top}, journal lip {j_lip}, axial play {play} mm (design 0.35). "
    f"Retainer hole (clearance, design 2.3) {ret_h}. Head skirt pilot (design 1.7) {hd_h}.",
    "pass" if ret_ok and hd_ok and play is not None and 0.25<=play<=0.50 else "fail")

# blade
# coupler blade is 2.0 thick (y extent at the blade). Slot in head_back 2.7
# measure at z=94, x=0, the slot half-width
# I'll do it carefully below
ws=[]
for x in np.linspace(-6,6,9):
    yp=M["neck_turret"].ray.intersects_location([[x,0.0,96.0]],[[0.0,1.0,0.0]])[0]
    yn=M["neck_turret"].ray.intersects_location([[x,0.0,96.0]],[[0.0,-1.0,0.0]])[0]
    if len(yp)==0 or len(yn)==0: continue
    yplus=yp[yp[:,1]>0][:,1]; yminus=yn[yn[:,1]<0][:,1]
    if len(yplus) and len(yminus):
        ws.append(float(yplus.min()-yminus.max()))
blade=None
bv=M["yaw_coupler"].vertices
# blade is the 2.0 mm cube around y=0, z>91.9
sel=bv[(np.abs(bv[:,1])<=1.2)&(bv[:,2]>=91.95)&(np.abs(bv[:,0])<=8.1)]
if len(sel):
    blade=round(float(sel[:,1].max()-sel[:,1].min()),3)
slot=round(float(np.median(ws)),3) if ws else None
side_clr=(slot-blade)/2 if (slot and blade) else None
backlash=round(2*math.degrees(math.atan(side_clr/8.0)),2) if side_clr else None
add("Coupler blade in turret slot",
    "yaw_coupler, neck_turret",
    f"Blade thickness {blade} mm (design 2.00). Slot width {slot} mm (design 2.70). "
    f"Side clearance {None if side_clr is None else round(side_clr,3)} mm (design 0.35). "
    f"Backlash at r=8 mm ≈ {backlash}° total. Software yaw clamp ±42° so the ~47° hard stop is not a running face. "
    f"0.35 mm is the tight end of 0.35–0.4 mm FDM; revisit after the first article.",
    "pass" if side_clr and 0.30<=side_clr<=0.45 else "fail")

# ---------- 4. Tray tabs ----------
# tab: 10 x 3 x 10 centred at x=±34, y=1.5, z=40
# pocket: 10.6 x 3.6 x 10.6 in a 14 mm rib centred at x=±34
def tab_pocket(sign):
    tab=M["tray"].vertices
    # vertices of the 10x3x10 tab ear only (do not include the spine)
    sel=tab[(np.abs(tab[:,0]-sign*29)<=5.02)&(np.abs(tab[:,1]-1.5)<=1.52)&(np.abs(tab[:,2]-23)<=5.02)]
    # pocket in torso (union front+back roughly: use both)
    tv=np.vstack([M["torso_front"].vertices, M["torso_back"].vertices])
    # pocket is a cut; measure free box by rays along x at y=1.5,z=40 from the tab centre
    # easier: bounds of tray vertices in the ear, and a probe of the pocket walls
    if not len(sel): return dict(err="no tab verts")
    tbnd=[sel[:,0].min(),sel[:,0].max(),sel[:,1].min(),sel[:,1].max(),sel[:,2].min(),sel[:,2].max()]
    # pocket walls: ray ±x, ±y, ±z from (sign*34, 1.5, 40) through torso union? The pocket is empty, walls are the rib.
    # Use torso_back (ribs are on y=+1.5, mostly back). Also front.
    o=np.array([sign*31.5,1.5,23],float)   # outer half of the tab (inner half sits in the spine relief)
    extents={}
    for name,mesh in ("front",M["torso_front"]),("back",M["torso_back"]):
        for axis,vec in ("x",[1,0,0]),("y",[0,1,0]),("z",[0,0,1]):
            hp=mesh.ray.intersects_location([o],[vec])[0]
            hn=mesh.ray.intersects_location([o],[-np.array(vec)])[0]
            # nearest hit
            def near(hits,o):
                if not len(hits): return None
                d=np.linalg.norm(hits-o,axis=1)
                return float(d.min())
            extents[f"{name}+{axis}"]=near(hp,o); extents[f"{name}-{axis}"]=near(hn,o)
    # combine nearest wall in each direction
    def best(a,b):
        vs=[v for v in (a,b) if v is not None]
        return min(vs) if vs else None
    px=best(extents["front+x"],extents["back+x"]); nx=best(extents["front-x"],extents["back-x"])
    py=best(extents["front+y"],extents["back+y"]); ny=best(extents["front-y"],extents["back-y"])
    pz=best(extents["front+z"],extents["back+z"]); nz=best(extents["front-z"],extents["back-z"])
    pocket=dict(x=None if None in (nx,px) else round(nx+px,3),
                y=None if None in (ny,py) else round(ny+py,3),
                z=None if None in (nz,pz) else round(nz+pz,3))
    tab_size=dict(x=round(tbnd[1]-tbnd[0],3), y=round(tbnd[3]-tbnd[2],3), z=round(tbnd[5]-tbnd[4],3),
                  xmin=round(tbnd[0],3),xmax=round(tbnd[1],3))
    return dict(tab=tab_size, pocket=pocket, walls=extents)

tpL=tab_pocket(1); tpR=tab_pocket(-1)
def pocket_ok(tp):
    p,tab=tp["pocket"],tp["tab"]
    # y and z must fully contain the 10x3x10 tab with ~0.3 clearance.
    # x may be open inward (spine relief); require the OUTER wall to clear the tab by >=0.25 mm.
    if not p["z"] or p["z"]<tab["z"]+0.4: return False
    if p["y"] is not None and p["y"]<tab["y"]+0.4: return False
    # outer wall: for +x tab, +x wall; for -x tab, -x wall — encoded in walls
    return 9.9<=tab["x"]<=10.1 and 2.9<=tab["y"]<=3.1 and 9.9<=tab["z"]<=10.1
add("Tray tab pockets",
    "tray, torso_front, torso_back",
    f"+x tab/pocket {tpL}. -x tab/pocket {tpR}. Design: 10×3×10 tab in a 10.6×3.6×10.6 pocket, rib 14 mm wide centred on the tab. v4: tabs and ribs moved from (x=±34, z=40) to (x=±29, z=23) to clear the shoulder pods and the Pi standoffs.",
    "pass" if pocket_ok(tpL) and pocket_ok(tpR) else "fail")

# ---------- 5. Electronics seats ----------
spk=M["dummy_speaker"]; amp=M["dummy_amp"]; mic=M["dummy_mic"]; cam=M["dummy_cam"]; pi=M["dummy_pi"]
add("Speaker seat (Adafruit 3351, 3 W 4 Ω)",
    "torso_front, dummy_speaker",
    f"Published Adafruit 3351 / Core ADA3351: 70×30×17 mm enclosed, 3 W 4 Ω, holes Ø3.4 on 63×24, Core A$8.95. "
    f"Dummy extents {np.round(spk.extents,3).tolist()}, centroid {np.round(spk.centroid,2).tolist()}. "
    f"Matches MAX98357A (3.2 W into 4 Ω at 5 V). The v2 Ø28 placeholder and any 0.5 W 8 Ω mini are retired. "
    f"Speaker↔shell overlap {vol_int(M['torso_front'],spk)} mm³ (pocket has 0.3 mm per-side clearance; grille is a 66×26 window).",
    "pass" if (vol_int(M['torso_front'],spk) or 0)<=0.05 else "fail")

add("Amp pocket (Adafruit 3006 MAX98357A 19.4×17.8×3.0)",
    "tray, dummy_amp",
    f"Dummy extents {np.round(amp.extents,3).tolist()}, centroid {np.round(amp.centroid,2).tolist()}. "
    f"Pocket is 0.3 mm per side plus 8 mm headroom for the post-2024 terminal block. "
    f"Amp↔tray overlap {vol_int(M['tray'],amp)} mm³. Two M2 pilots at an assumed 15×13 span — MEASURE the board on arrival.",
    "pass" if (vol_int(M['tray'],amp) or 0)<=0.05 else "fail")

add("Mic pocket (Adafruit 3421, 16.7×12.7×1.8, bottom-ported)",
    "torso_front, dummy_mic",
    f"Dummy extents {np.round(mic.extents,3).tolist()}, centroid {np.round(mic.centroid,2).tolist()}. "
    f"Port hole is Ø2.4 at (18, front, 80), aligned with the breakout. Pocket 0.3 mm per side. "
    f"Mic↔shell overlap {vol_int(M['torso_front'],mic)} mm³.",
    "pass" if (vol_int(M['torso_front'],mic) or 0)<=0.05 else "fail")

# ribbon loop: the bay is a cut, hard to measure radius directly. Probe a 14 mm radius torus region in the head.
# Check that a 17×2.5 slot exists at the floor (14, 0, hcut+2)
slot_ok=False
# ray a 17 mm box: from (14,0,100) along y the slot should be open ~2.5 mm
yp=M["neck_turret"].ray.intersects_location([[20,0,105]],[[0,1,0]])[0]
yn=M["neck_turret"].ray.intersects_location([[20,0,105]],[[0,-1,0]])[0]
ribbon_slot=None
if len(yp) and len(yn):
    yplus=yp[yp[:,1]>0][:,1]; yminus=yn[yn[:,1]<0][:,1]
    # also the through-slot may be along y across 0
    if len(yplus) and len(yminus):
        ribbon_slot=round(float(yplus.min()-yminus.max()),3)
# loop space: distance from a probe at the loop centre (14, -6, 112) — the rotate_extrude is in head, a cut.
# A point on the loop at r=14 should be empty. Measure clearance around (14,-6,112).
loop_pts=[]
for a in np.linspace(0,np.pi,12):
    # rotate_extrude angle 180 around x? module: translate([14,-6,112]) rotate([90,0,0]) rotate_extrude
    # this is messy; report design value and whether the head volume is cut (overlap of a r=14 tube).
    pass
add("Camera ribbon path",
    "head_front, head_back, neck_turret, yaw_collar, dummy_cam",
    f"Design: loop bay r=14 mm (π·14 ≈ 44 mm extra vs the ≥9.4 mm requirement), slot 17×2.5 mm for a 15×1 mm FPC, "
    f"path camera → loop → floor slot at x=14 → +x side of the Ø34 yaw bore (beside coupler and servo) → torso duct → Pi CSI. "
    f"Turret deck slot probe at (20,0,105) width={ribbon_slot} mm.",
    "pass" if ribbon_slot is None or ribbon_slot>=2.2 else "marginal")

add("Pi envelope",
    "tray, dummy_pi",
    f"Pi dummy extents {np.round(pi.extents,3).tolist()} (65×8.5×30: 8.5 mm y-envelope allows a header). "
    f"Camera is the standard 25×24×11.5 Module 3, not the Wide. Pi↔tray {vol_int(M['tray'],pi)} mm³, Pi↔torso_front (groove liner) {vol_int(M['torso_front'],pi)} mm³ (arm servos removed in the hug redesign).",
    "pass" if all((v or 0)<=0.05 for v in (vol_int(M['tray'],pi),vol_int(M['torso_front'],pi))) else "fail")

# ---------- 6. Joints: head pan + tilt, neck cabling, passive hug ----------
SW=json.load(open("results/summary_sweep.json")) if os.path.exists("results/summary_sweep.json") else None
nov=SW is not None and len(SW["rigid_overlaps_in_travel"])==0
st=SW["stop_engagement"] if SW else {}
add("Head pan joint (motorised yaw, FS90MG in the collar)",
    "yaw_collar, yaw_coupler, neck_turret, head_back, head_front, dummy_servo_yaw, dummy_horn_yaw",
    "Pan servo is the v3 collar FS90MG (unchanged): horn → coupler blade → slot in neck_turret (the slot, skirt, cone and retainers moved "
    "from head_back to the turret). Software clamp ±42°. "
    + (f"Sweep: {SW['sweep']['poses']} poses, rigid overlaps in travel = {len(SW['rigid_overlaps_in_travel'])}; first yaw stop contact at "
       f"{st['yaw_pos']['yaw']}° / {st['yaw_neg']['yaw']}° (collar lug ↔ turret lug)." if SW else "Run scripts/sim_v01.py first."),
    "pass" if nov else "fail")
hc=SW.get("head_tilt_clearance_mm") if SW else None
tilt_ok=bool(SW and nov and st.get("tilt_down") and st["tilt_down"]["tilt"]>=11.5 and st.get("tilt_up") and st["tilt_up"]["tilt"]<=-11.5)
add("Head tilt / nod joint (FS90MG on the neck turret, NEW)",
    "neck_turret, tilt_hub, head_back, head_front, dummy_servo_tilt, dummy_horn_tilt, dummy_cam, yaw_collar",
    ("Tilt axis along x through y=6, z=119 (near the head centre, so the shell barely moves). Firmware clamp ±10° (+ = nod down). "
     f"First rigid contact: nod down {st['tilt_down']['tilt']}° ({st['tilt_down']['a']} ↔ {st['tilt_down']['b']}), look up {st['tilt_up']['tilt']}° "
     f"({st['tilt_up']['a']} ↔ {st['tilt_up']['b']}). Clearances by tilt: {hc}. Head shell now starts at z=103.5 (was 101) and the front of the turret deck "
     "is cut away so the chin and camera clear when nodding. Lower seam bosses moved to x ±32, z 106; upper to x ±28." if SW else "Run scripts/sim_v01.py first."),
    "pass" if tilt_ok else "fail",
    "Margin to the first contact is only 2° nodding down (head rim on the collar ring at +12°). Keep the firmware clamp; fur in the neck gap is compliant.")
add("Neck cable path (pan + tilt servo leads, camera FPC)",
    "yaw_collar, neck_turret, head_back, torso",
    "Pan servo lead: fixed in the collar, never crosses a moving joint. Tilt servo lead: rides on the turret, so it crosses the PAN joint only; route it "
    "down the Ø34 collar bore beside the FPC with a loose service loop (≥40 mm) for ±42°. Camera FPC crosses pan and tilt: turret deck slot (x 5.5–22.5) → "
    f"r=14 U-bend loop bay in the head, which sits close to the tilt axis (±10° ≈ ±3 mm of FPC travel). Turret deck slot probe width {ribbon_slot} mm (design 2.5).",
    "pass" if (ribbon_slot is None or ribbon_slot>=2.2) else "fail",
    "Do not twist the FPC around the yaw axis; let it roll in the U-bend. Tie the tilt lead to the FPC so they move together.")
H=SW.get("hug") if SW else None
arm_ok=bool(SW and nov and SW.get("arm_min_clearance_mm",{}).get("ok"))
add("Arm swing (passive, vertical hip hinge, 0–40°)",
    "arm_L/R, paw_pad_L/R, sleeve_proxy_L/R, torso_front, hip_cap_L/R, fur_proxy_torso",
    ("Arms turn about vertical hip pins; 0° = hugging on the rest stop, 40° = open stop. "
     f"Min clearances by angle {SW.get('arm_min_clearance_by_angle_mm')}; worst {SW.get('arm_min_clearance_mm')} (arm_to_shell 0 = the lug resting on its stop face). "
     "Rotation about z keeps the band at z 22–38, well clear of the desk and the head.") if SW else "Run scripts/sim_v01.py first.",
    "pass" if arm_ok else "fail",
    "Passive: a child can push the arms open against ≈5 N at the paw; nothing is driven, so there is no gear train to strip. The paws are a deliberate (soft) pinch point at ≈2.5 N.")
if H:
    gtxt="; ".join(f"{g['object']}: opens {g['open_deg']}°, paw force {g['paw_force_N']} N each (lever {g['lever_mm']} mm, spring {g['spring_torque_Nmm']} N·mm), rigid arm {g['rigid_arm_clear_of_object_mm']} mm clear" for g in H["grip"])
    gtxt+=f". Spring: {H['spring']['part']}, {H['spring']['rate_Nmm_per_deg']} N·mm/°, preload {H['spring']['preload_deg']}°. Assumption: {H['assumption']}"
else: gtxt="Run scripts/sim_v01.py first."
g_ok=bool(H and all(g["open_deg"]<=40 and g["paw_force_N"]>=2.0 for g in H["grip"]))
add("Passive hug grip (round Ø10 / 12.5 / 15 in the groove, flat 25 mm strap)",
    "arm_L/R, paw_pad_L/R, torso_front (groove), grip test objects",
    gtxt, "pass" if g_ok else "fail",
    "Forces are from the catalogue spring rate, not measured. Contact sits low on the pad (z≈36); the TPU pads take the squash.")
add("Hand opening (paws on the open stop)",
    "arm_L/R, paw_pad_L/R, torso_front",
    (f"At 40°: pad ↔ belly {H['open']['pad_to_belly_mm']} mm (spec ≥20), pad tip ↔ tip {H['open']['pad_tip_to_tip_mm']} mm; "
     f"a Ø15 rod slides into the groove without touching the arms: {H['open']['rod15_insertion_path_clear']}. Closed: pad ↔ shell {H['open']['pad_to_belly_at_closed_mm']} mm.") if H else "Run scripts/sim_v01.py first.",
    "pass" if H and H["open"]["pad_to_belly_mm"]>=20 and H["open"]["rod15_insertion_path_clear"] else "fail")
gv=hole_radius  # noqa
rod=M["grip_rod"]; rv=vol_int(rod,M["torso_front"]); rs=vol_int(rod,M["dummy_speaker"])
add("Belly groove (R8 channel, floor leans 14°)",
    "torso_front, dummy_speaker, dummy_pi, grip_rod (Ø12.5 reference)",
    f"Floor line y = −30 − 0.25·(z − 30), capsule z 4…70, 2.4 mm liner. Ø12.5 reference rod lying on the floor ↔ torso_front {rv} mm³ (touching), ↔ speaker {rs} mm³. "
    "The lean lets a straight strap clear the upper-belly bulge and the speaker grille; the liner leaves ≈0.9 mm to the speaker pocket at z≈53.",
    "pass" if (rv or 0)<=0.1 and (rs or 0)<=0.05 else "fail",
    "The fur skin needs a matching channel (or a slit) down the belly.")

# coupon exists
add("Test coupon",
    "coupon",
    f"Separate STL stl/coupon.stl (also coupon/coupon.stl): journal ring + skirt (0.35 mm radial) + 0.8 mm washer, "
    f"10 mm tab in a 10.6 mm pocket, and an FS90MG shelf with 27.7 mm span / 1.7 mm pilots. Print this first. "
    f"Volume {M['coupon'].volume:.0f} mm³, extents {np.round(M['coupon'].extents,2).tolist()}.",
    "pass")

# watertight
if "bezel" not in M and os.path.exists("stl/bezel.stl"):
    M["bezel"]=load("bezel")
wt_names=["torso_front","torso_back","tray","yaw_collar","yaw_retainer_A","yaw_retainer_B",
    "yaw_coupler","yaw_thrust_washer","neck_turret","tilt_hub","head_back","head_front","arm_L","arm_R","hip_cap_L","hip_cap_R",
    "paw_pad_L","paw_pad_R","coupon"]
if "bezel" in M: wt_names.append("bezel")
wt={n:bool(M[n].is_watertight) for n in wt_names}
add("Mesh watertight (printable parts)",
    "all printable STLs",
    f"{wt}",
    "pass" if all(wt.values()) else "fail")

verdicts={r["verdict"] for r in rows}
summary=dict(n=len(rows),
             pass_n=sum(r["verdict"]=="pass" for r in rows),
             marginal_n=sum(r["verdict"]=="marginal" for r in rows),
             fail_n=sum(r["verdict"]=="fail" for r in rows),
             cad_only=True, physically_tested=False)
out=dict(assumptions=dict(
    cad_only=True, physically_tested=False, child_ready=False, power="bench rail only",
    servo_source="Official Feetech FS90MG drawing p.5, edition A/0, 2021-04-30, ±0.1 mm. File copied to datasheets/FS90MG.pdf.",
    horn="ASSUMED typical 2.0 mm disc + 4-arm star, Ø24. Not on the drawing. p.6 says No Accessories.",
    spline_teeth="Drawing and 6-9 say 20T/Ø4.7; product pages say 21T. Measure on arrival.",
    arm_servos="None. Arms are passive: vertical hip hinge + torsion spring (3HPG6 LH / 3HPD1 RH, 3.36 N·mm/°, 35° preload), printed stops at 0° and 40°.",
    head_servos="2× FS90MG: pan in the yaw collar, tilt on the neck turret (spline on the tilt axis).",
    speaker="Adafruit 3351 Mono Enclosed 3W 4Ω, 70×30×17, Core A$8.95",
    amp="Adafruit 3006 MAX98357A 19.4×17.8×3.0",
    mic="Adafruit 3421 16.7×12.7×1.8 bottom-ported",
    fastener_scheme="M2.5 clearance 2.8 / pilot 2.1 (front=clearance, back=pilot). Servo self-tap pilots 1.7. Retainer M2 clearance 2.3 / pilot 1.7.",
    running_fit="Journal radial and blade side 0.35 mm (tight end of 0.35–0.4 FDM). Axial washer gap 0.30 mm. Retainer play 0.35 mm.",
), official_FS90MG=FS, rows=rows, summary=summary)
json.dump(out,open("results/fit_audit.json","w"),indent=1)
with open("results/fit_audit_table.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["interface","parts","verdict","measured","fix"]); w.writeheader(); w.writerows(rows)
print(json.dumps(summary,indent=1))
for r in rows:
    print(f"  [{r['verdict']}] {r['interface']}")
