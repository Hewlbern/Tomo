# SPDX-License-Identifier: MIT
"""Tomo by DreamMachina (formerly evoKin V.01) metrics from the exported STLs: mass and centre of mass, hanging stability on a strap,
passive-hug spring forces (from results/summary_sweep.json), head pan/tilt loads vs the FS90 (plastic gear; was FS90MG), servo power budget,
and which STLs changed vs the servo-clasp V.01 (commit bed94ce). Estimates only; nothing has been built or weighed."""
import numpy as np, trimesh, json, os, sys, hashlib, subprocess, math
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
G=9.81; RHO_PLA=1.24e-3; RHO_TPU=1.21e-3
FILL0=0.75     # v0.1 Mirumi-proportions estimate (6ad85c3): every printed part at 0.75 of solid
# Lighter Tomo print profiles (ASSUMED effective fraction of solid; weigh the first prints):
#  shells: 1 perimeter (0.45 mm) each face + 10 % gyroid + 2 top/bottom layers on a 2.4 mm wall ≈ 0.48
#  arms (spring loads): 2 perimeters + 15 % gyroid, PETG ≈ 0.62;  collar / turret: 3 perimeters + 15 % ≈ 0.60;  tray 0.50
#  small bearing parts (retainers, coupler, washer, hub): 0.75 (unchanged)
FILL={"torso_front":0.48,"torso_back":0.48,"head_front":0.48,"head_back":0.48,"arm_L":0.62,"arm_R":0.62,
      "yaw_collar":0.60,"neck_turret":0.60,"tray":0.50,"yaw_retainer_A":0.75,"yaw_retainer_B":0.75,"yaw_coupler":0.75,
      "yaw_thrust_washer":0.75,"tilt_hub":0.75}
STALL_KGCM=1.3; STALL_KGCM_6V=1.5; STALL_A=0.7; STALL_A_6V=0.8     # Feetech FS90 at 4.8 V / 6 V (Feetech spec sheet)
L=lambda n: trimesh.load(stl_path(n))
SW=json.load(open("results/summary_sweep.json"))
o={"assumptions":dict(material="PLA 1.24 g/cm³ × per-part effective fill (see print_profiles); TPU pads 1.21 g/cm³ solid",
   print_profiles=FILL,
   components="Feetech FS90 9 g each (Feetech spec sheet / Core Electronics CE09376) + horn 1 g; Adafruit 3923 mini oval speaker 3 g (Adafruit listing); "
     "XIAO ESP32S3 Sense with camera 6.6 g (distributor spec) + long-FPC camera allowance 0.9 g; MAX98357A amp 2 g; mic 1 g; INA219 2 g; Pololu U3V16F5 boost 0.4 g (Pololu listing); "
     "wiring 5 g (ASSUMED, trimmed 30 AWG); fasteners 5.5 g (steel M3 pins and servo/horn screws; nylon M2.5 shell/collar screws); springs 2 × 1 g; 8 mm safety eyes 2 × 0.7 g (ASSUMED); "
     "long-pile fur skin 19 g (ASSUMED light knit-backed faux fur ≈380 g/m² over ≈0.050 m²) + feet fibrefill 2 g; battery Core Electronics CE04375 1S 400 mAh 11 g (listing).",
   cad_only=True,physically_tested=False)}
printed=list(FILL)
items=[]
for n in printed:
    m=L(n); items.append((n,m.volume*RHO_PLA*FILL[n],m.center_mass,m.volume*RHO_PLA))
for n in ("paw_pad_L","paw_pad_R"):
    m=L(n); items.append((n,m.volume*RHO_TPU,m.center_mass,m.volume*RHO_TPU))
def cen(n): return L(n).center_mass
comp=[("FS90 pan + horn",10.0,cen("dummy_servo_yaw")),("FS90 tilt + horn",10.0,cen("dummy_servo_tilt")),
      ("speaker (Adafruit 3923)",3.0,cen("dummy_speaker")),("brain + camera (XIAO ESP32S3 Sense)",7.5,cen("dummy_pi")),("amp",2.0,cen("dummy_amp")),
      ("mic",1.0,cen("dummy_mic")),("INA219 + U3V16F5 boost",2.4,np.array([0,10.0,40.0])),("wiring",5.0,np.array([0,0,60.0])),
      ("fasteners",5.5,np.array([0,-5.0,60.0])),("springs",2.0,np.array([0,-31.2,78.0])),("safety eyes",1.4,np.array([0,-40.0,121.0])),
      ("fur skin (short v3 pile)",21.0,np.array([0,-2.0,68.0]))]
# thick Mirumi-style soft arm sleeves (soft goods): polyester fibrefill inside (ASSUMED 15 kg/m³ loosely packed) +
# the extra fur over the larger tube (ASSUMED 380 g/m², same as the body pile) vs the old 2 mm sleeve (7,953 mm² for both arms)
RHO_FILL=0.015e-3; FUR_GM2=380.0; OLD_SLEEVE_AREA=7953.0
slv={}
for sd in ("L","R"):
    sm=L(f"sleeve_proxy_{sd}"); am=L(f"arm_{sd}")
    slv[sd]=dict(volume_mm3=round(sm.volume,0),area_mm2=round(sm.area,0),stuffing_g=round(max(0.0,sm.volume-am.volume)*RHO_FILL,2),centre=sm.center_mass)
stuff=sum(v["stuffing_g"] for v in slv.values()); xfur=max(0.0,(sum(v["area_mm2"] for v in slv.values())-OLD_SLEEVE_AREA)*1e-6*FUR_GM2)
comp.append(("arm sleeves: fibrefill",stuff,(slv["L"]["centre"]+slv["R"]["centre"])/2))
comp.append(("arm sleeves: extra fur over the thicker tubes",xfur,(slv["L"]["centre"]+slv["R"]["centre"])/2))
# v3-bear soft goods (cad soft_body + soft_head): fibrefill padding to a round BALL torso (sphere R60 about z 48, cut flat at
# z 0) and a round head ball (ellipse of revolution 55 x 41 about z 114), two small stuffed bear ears, no feet, and the v3
# critter's short dense pile (≈6–9 mm, ASSUMED 380 g/m², same as the base skin). Padding volume from the revolved profiles
# less the handle channel; ears are ellipsoids.
sys.path.insert(0,"scripts"); import groove_geo as gg
FUR_SKIN=4.0; PILE_OLD,PILE_NEW=380.0,380.0; SKIN_M2=0.050
TB_Z,TB_R,PAD_Z4=48.0,60.0,92.0; HB_A,HB_B,HB_Z=55.0,41.0,114.0; SEAM_Z=101.0; EAR_R=(12.0,5.5,11.0); FOOT_R=(0.0,0.0,0.0)
def ball_r(z): d=z-TB_Z; return math.sqrt(TB_R*TB_R-d*d) if abs(d)<TB_R else 0.0
def body_pad(z): return 0.0 if (z<0 or z>=PAD_Z4) else max(0.0,ball_r(z)-gg.eggr(z)-FUR_SKIN)
def head_ball_r(z): d=(z-HB_Z)/HB_B; return HB_A*math.sqrt(1-d*d) if abs(d)<1 else 0.0
def egg_or0(z): return gg.eggr(z) if z<148.0 else 0.0
zz=np.linspace(0,PAD_Z4,461); dz=zz[1]-zz[0]
r0=np.array([gg.eggr(z)+FUR_SKIN for z in zz]); pp=np.array([body_pad(z) for z in zz])
pad_v=float(np.sum(math.pi*((r0+pp)**2-r0**2))*dz)*(1-18.0/(2*math.pi*50.0))     # less the ≈18 mm handle channel
pad_a=float(np.sum(2*math.pi*pp)*dz)                                            # extra outer skin area (approx.)
zh=np.linspace(SEAM_Z,HB_Z+HB_B,301); dzh=zh[1]-zh[0]
rh0=np.array([(egg_or0(z)+FUR_SKIN) if z<148.0 else 0.0 for z in zh]); rh=np.array([max(rh0[i],head_ball_r(z)) for i,z in enumerate(zh)])
head_v=float(np.sum(math.pi*(rh**2-rh0**2))*dzh); head_a=float(np.sum(2*math.pi*(rh-rh0))*dzh)
foot_v=2*4/3*math.pi*EAR_R[0]*EAR_R[1]*EAR_R[2]*0.8                              # ears: ≈⅕ of each sits inside the head skin
foot_a=2*0.8*4*math.pi*((EAR_R[0]*EAR_R[1])**1.6+(EAR_R[0]*EAR_R[2])**1.6+(EAR_R[1]*EAR_R[2])**1.6)**(1/1.6)/3**(1/1.6)
soft_fill=(pad_v+head_v+foot_v)*RHO_FILL; soft_fur=(pad_a+head_a+foot_a)*1e-6*PILE_NEW+SKIN_M2*(PILE_NEW-PILE_OLD)
comp.append(("soft body: ball-torso padding (fibrefill)",pad_v*RHO_FILL,np.array([0,-4.0,40.0])))
comp.append(("soft head: head-ball padding + ears (fibrefill)",(head_v+foot_v)*RHO_FILL,np.array([0,-2.0,125.0])))
comp.append(("soft goods: extra skin + short pile over the padding and ears",soft_fur,np.array([0,-2.0,80.0])))
for c in comp: items.append((c[0],c[1],c[2],c[1]))
def summ(items,solid=False):
    m=np.array([it[3] if solid else it[1] for it in items]); p=np.array([it[2] for it in items]); return float(m.sum()), (m[:,None]*p).sum(0)/m.sum()
mt,cm=summ(items); ms,_=summ(items,True)
bat=("battery 1S 400 mAh (Core CE04375)",11.0,np.array([0,12.0,30.0]),11.0)
mtb,cmb=summ(items+[bat])
# before (v0.1 Mirumi proportions, commit 6ad85c3)
BEFORE={"shells (torso + head, 4 parts)":106.3,"arms":22.3,"TPU pads":4.0,"tray":11.5,"yaw collar":15.3,"turret + hub + yaw small parts":10.4,
        "eye bezels + shutter":6.0,"servos 2 × FS90MG + horns":28.8,"speaker (Adafruit 3351)":25.0,"brain + camera":8.0,"amp + mic":3.0,
        "INA219 + XL6009 boost":7.0,"wiring":8.0,"fasteners":8.0,"springs":2.0,"eyes (in bezels)":0.0,"fur skin":30.0,"thick arm sleeves (fibrefill + extra fur)":0.0,"potato padding, feet, shaggy pile":0.0,"battery (2000 mAh)":38.0}
bd={it[0]:it[1] for it in items}
AFTER={"shells (torso + head, 4 parts)":sum(bd[k] for k in ("torso_front","torso_back","head_front","head_back")),
       "arms":bd["arm_L"]+bd["arm_R"],"TPU pads":bd["paw_pad_L"]+bd["paw_pad_R"],"tray":bd["tray"],"yaw collar":bd["yaw_collar"],
       "turret + hub + yaw small parts":sum(bd[k] for k in ("neck_turret","tilt_hub","yaw_retainer_A","yaw_retainer_B","yaw_coupler","yaw_thrust_washer")),
       "eye bezels + shutter":0.0,"servos 2 × FS90MG + horns":20.0,"speaker (Adafruit 3351)":3.0,"brain + camera":7.5,"amp + mic":3.0,
       "INA219 + XL6009 boost":2.4,"wiring":5.0,"fasteners":5.5,"springs":2.0,"eyes (in bezels)":1.4,"fur skin":21.0,"thick arm sleeves (fibrefill + extra fur)":stuff+xfur,"potato padding, feet, shaggy pile":soft_fill+soft_fur,"battery (2000 mAh)":11.0}
RENAME={"servos 2 × FS90MG + horns":"servos (2 × FS90MG → 2 × FS90, + horns)","speaker (Adafruit 3351)":"speaker (Adafruit 3351 → 3923)",
        "INA219 + XL6009 boost":"INA219 + boost (XL6009 → Pololu U3V16F5)","eyes (in bezels)":"10 mm safety eyes","fur skin":"fur skin (short v3 pile)","potato padding, feet, shaggy pile":"ball torso + head-ball padding, ears, extra pile",
        "battery (2000 mAh)":"battery (1S 2000 mAh → 400 mAh)","fasteners":"fasteners (→ nylon M2.5 shell screws)","eye bezels + shutter":"eye bezels + shutter (removed)"}
budget=[dict(item=RENAME.get(k,k),before_g=round(BEFORE[k],1),after_g=round(AFTER[k],1)) for k in BEFORE]
o["mass"]=dict(soft_body=dict(padding_volume_cm3=round(pad_v/1000,1),head_padding_volume_cm3=round(head_v/1000,1),ears_volume_cm3=round(foot_v/1000,1),fibrefill_g=round(soft_fill,2),
                extra_pile_and_skin_g=round(soft_fur,2),previous_total_with_battery_g_494c22f=185.0,previous_total_with_battery_g_03bc2f7=194.0,previous_total_with_battery_g_a5e3067=194.0,
                note="v3-bear soft goods: fibrefill padding to a round ball torso (sphere R60 about z 48, cut flat at z 0, gone by z ≈ 81) and a round head ball (55 x 41 about z 114, top z 155), two small stuffed bear ears, no feet, and the v3 short dense pile (ASSUMED 380 g/m²). The printed shell stays 148 mm to clear the tilt servo. Fibrefill 15 kg/m³ ASSUMED."),
   arm_sleeves=dict(L={k:v for k,v in slv["L"].items() if k!="centre"},R={k:v for k,v in slv["R"].items() if k!="centre"},
                stuffing_g=round(stuff,2),extra_fur_g=round(xfur,2),previous_total_with_battery_g_b458259=191.0,
                note="Soft goods: a stuffed fur tube (Ø16–18 mm before pile, Ø≈26–28 mm with it) round each printed spine, a shoulder cap over the knuckle and a mitten paw. Stuffing 15 kg/m³ and fur 380 g/m² are ASSUMED."),
   estimate_g=round(mt,0),solid_print_upper_bound_g=round(ms,0),with_battery_g=round(mtb,0),
   battery="Core Electronics CE04375 1S 400 mAh, 11 g",
   centre_of_mass_mm=np.round(cm,1).tolist(),centre_of_mass_with_battery_mm=np.round(cmb,1).tolist(),
   breakdown_g={it[0]:round(it[1],1) for it in items},
   budget_before_after=budget,before_total_with_battery_g=round(sum(BEFORE.values()),0),after_total_with_battery_g=round(sum(AFTER.values()),0),
   note="Mirumi is about 135–155 g and about 100 x 118 x 143 mm. Target 160–180 g with battery, ceiling 200 g. Printed masses use the ASSUMED print profiles; weigh the first prints.")
# ---- overall size with soft goods (estimate; pile lengths from the render groom)
PILE_BODY,PILE_HEAD,PILE_CROWN=8.5,7.5,6.5
o["size_estimate_mm"]=dict(seated_height=round(HB_Z+HB_B+PILE_CROWN,0),torso_ball_width=round(2*TB_R+2*PILE_BODY,0),
   head_ball_width=round(2*HB_A+2*PILE_HEAD,0),neck_width=round(2*(gg.eggr(92)+FUR_SKIN)+2*0.6*PILE_BODY,0),
   note="Over the pile, robot frame (z 0 = sit pad). Shell is Ø92 x 148; torso ball R60 to z 0, head ball top z 155. Mirumi is ≈100 x 118 x 143.")
# ---- clinging to the upright of a bag handle running up the belly (Mirumi pose) and hanging free from it
sys.path.insert(0,"scripts"); import groove_geo as gg
H=SW["hug"]; g125=next(g for g in H["grip"] if g["d_mm"]==12.5)
def cling(mass,com,g=g125,mu=0.5):
    W=mass/1000*G; d=g["d_mm"]
    P0=gg.FR+gg.N*d/2; u=gg.U
    r=com-P0; perp=r-u*np.dot(r,u); off=float(np.linalg.norm(perp))
    F=g["total_pad_force_N"]; Fin=g["total_into_groove_N"]
    zc=float(np.mean([g["L"]["contact_point"][2],g["R"]["contact_point"][2]]))
    # (a) seated on the bag top, base on the bag, handle across the chest: the bag top carries the weight; the hug only
    #     has to stop it toppling away from the handle. Max backward tilt held = asin(F*zc/(W*z_com)) beyond its own base.
    tilt=math.degrees(math.asin(min(1.0,F*zc/(W*float(com[2])))))
    # (b) free hang from the handle with the handle line vertical: friction along the handle on both faces (pads + groove)
    cap=mu*2*F
    # a round handle in a round groove does not resist roll about its own axis, so the body swings until its COM is below the line
    return dict(weight_N=round(W,2),com_mm=np.round(com,1).tolist(),handle_axis_to_com_mm=round(off,1),
        handle_angle_from_body_vertical_deg=round(math.degrees(math.acos(u[2])),1),
        pad_force_total_N=round(F,2),pad_force_into_groove_N=round(Fin,2),mean_clamp_height_mm=round(zc,1),
        seated_on_bag=dict(max_backward_tilt_held_deg=round(tilt,1),hug_moment_over_toppling_moment_at_90deg=round(F*zc/(W*float(com[2])),2),
            note="Mirumi pose: bottom resting on the bag top, both arms round the handle. The bag carries the weight; the springs hold it upright against the handle."),
        free_hang=dict(friction_capacity_along_handle_N_mu0p5=round(cap,2),slip_safety_factor_vertical_handle=round(cap/W,2),
            roll_to_hang_com_under_handle=True,
            note="Hanging free from a vertical handle upright (nothing under it): slip down the handle is resisted only by friction on the pads and the groove; the COM offset from the handle is carried as a moment by the pad / groove couple."))
o["clinging"]=dict(no_battery=cling(mt,cm),with_battery=cling(mtb,cmb),
   per_handle={f'{g["d_mm"]}':dict(pad_force_total_N=g["total_pad_force_N"],into_groove_N=g["total_into_groove_N"],
        free_hang_slip_SF_no_battery=round(0.5*2*g["total_pad_force_N"]/(mt/1000*G),2)) for g in H["grip"]},
   assumption="Handle Ø12.5 upright on the centre groove floor line (≈2° from the body vertical). μ = 0.5 TPU/fur on a fabric or leather handle (ASSUMED). Pad forces from scripts/sim_v01.py. Not tested.")
L_lev={sd:float(np.linalg.norm((L(f"paw_pad_{sd}").center_mass-np.array([(1 if sd=="L" else -1)*(gg.eggr(78)+8.5)*math.cos(math.radians(-35)),(gg.eggr(78)+8.5)*math.sin(math.radians(-35)),0]))[:2])) for sd in ("L","R")}
Mopen=H["spring"]["torque_at_open_stop_Nmm"]; sig=32*Mopen*1.1/(math.pi*1.22**3)
o["hug_springs"]=dict(rate_Nmm_per_deg=H["spring"]["rate_Nmm_per_deg"],preload_deg=H["spring"]["preload_deg"],
   torque_rest_Nmm=H["spring"]["torque_at_rest_Nmm"],torque_open_stop_Nmm=Mopen,
   finger_force_to_hold_open_at_pad_N={sd:round(Mopen/L_lev[sd],2) for sd in L_lev},pad_lever_mm={sd:round(L_lev[sd],1) for sd in L_lev},
   grip={f'{g["d_mm"]}':dict(open_deg_L=g["L"].get("open_deg"),open_deg_R=g["R"].get("open_deg"),force_L_N=g["L"].get("pad_normal_force_N"),force_R_N=g["R"].get("pad_normal_force_N"),total_N=g["total_pad_force_N"]) for g in H["grip"]},
   spring_stress_check=f"σ ≈ 32·M·Ki/(π·d³) with M = {Mopen:.0f} N·mm at the open stop (90° wind-up), d = 1.22 mm, Ki ≈ 1.1: ≈{sig/1000:.2f} GPa, vs ≈1.86 GPa at the catalogue 90° rating (302.7 N·mm): the open stop sits exactly at the rating, no margin; do not hold the arms open past the stop.")
# ---- head pan / tilt loads
head=[L(n) for n in ("head_front","head_back","tilt_hub")]; h_cam=1.0
hm=sum(h.volume for h in head)*RHO_PLA*FILL['head_front']+0.9*h_cam+1.4+4.0+(head_v+foot_v)*RHO_FILL+head_a*1e-6*PILE_NEW    # + camera module/FPC, safety eyes, head fur share (ASSUMED 4 g), head-ball padding + ears
hc=sum(h.volume*h.center_mass for h in head)/sum(h.volume for h in head)
ax=np.array([0,6.0,119.0]); arm=float(np.hypot(hc[1]-ax[1],hc[2]-ax[2]))
tau_tilt=hm/1000*G*arm/1000      # N·m worst case (lever horizontal)
turret=[L(n) for n in ("neck_turret","yaw_coupler","yaw_retainer_A","yaw_retainer_B")]
parts=head+turret
I=sum(p.moment_inertia[2,2]*RHO_PLA*0.6 + p.volume*RHO_PLA*0.6*(p.center_mass[0]**2+p.center_mass[1]**2) for p in parts)+10.0*(15**2)
th=np.radians(60); t=0.12; alpha=4*th/t**2; tau_acc=float(I)*1e-9*alpha
o["head"]=dict(pan=dict(servo="Feetech FS90 (plastic gear, 9 g) in the yaw collar; same 22.5 x 12.1 x 22.4 case as the FS90MG",software_clamp_deg=[-42,42],hard_stop_deg=SW["stop_engagement"]["yaw_pos"]["yaw"],
      moving_inertia_g_mm2=round(float(I),0),accel_torque_60deg_in_0p12s_kgcm=round(tau_acc/G*100,4),fraction_of_stall_4p8V=round(tau_acc/G*100/STALL_KGCM,4),
      note="Pan now also turns the turret and the tilt servo."),
   tilt=dict(servo="Feetech FS90 on the neck turret, spline on the tilt axis (x direction, y=6, z=119)",software_clamp_deg=[-10,10],
      first_contact_deg=dict(nod_down=SW["stop_engagement"]["tilt_down"]["tilt"],look_up=SW["stop_engagement"]["tilt_up"]["tilt"]),
      head_mass_g=round(hm,1),head_com_from_axis_mm=round(arm,1),gravity_torque_kgcm=round(tau_tilt/G*100,3),fraction_of_stall_4p8V=round(tau_tilt/G*100/STALL_KGCM,3)))
o["servo_power"]=dict(servos=2,channels=["head pan","head tilt"],stall_each_A_5V=STALL_A,worst_case_all_stalled_A=round(2*STALL_A,2),
   note="Arms are passive and draw nothing. FS90 stall 700 mA at 4.8 V (Feetech). U3V16F5 from a 3.7 V cell gives roughly 1 A continuous at 5 V, so the firmware must not stall both servos at once; the INA219 trip covers it.",
   runtime=dict(battery_mAh=400,idle_wifi_mA=110,servo_avg_mA=60,est_hours=round(400*0.85/(110+60),1),note="XIAO ESP32S3 Sense Wi-Fi active ≈110 mA (Seeed), servos moving ~20 % of the time ≈60 mA average (ASSUMED): ≈2 h; ≈3–4 h with Wi-Fi light-sleep between interactions."))
def sha(b): return hashlib.sha1(b).hexdigest()
chg={}
for f in sorted(os.listdir("stl"))+["reference/"+x for x in sorted(os.listdir("stl/reference"))]:
    if not f.endswith(".stl"): continue
    new=open("stl/"+f,"rb").read()
    try: old=subprocess.run(["git","show",f"bed94ce:stl/{f}"],capture_output=True,check=True).stdout
    except subprocess.CalledProcessError: chg[f]="new"; continue
    if sha(old)==sha(new): chg[f]="identical"; continue
    a=trimesh.load(trimesh.util.wrap_as_stream(old),file_type="stl"); b=trimesh.load(trimesh.util.wrap_as_stream(new),file_type="stl")
    same=abs(a.volume-b.volume)<0.5 and np.allclose(a.bounds,b.bounds,atol=0.01)
    chg[f]="geometrically unchanged (bytes differ)" if same else f"changed (volume {a.volume:.0f} -> {b.volume:.0f} mm³)"
o["changed_vs_servo_clasp_bed94ce"]=chg
o["removed_vs_servo_clasp_bed94ce"]=["stl/shoulder_bracket_L.stl","stl/shoulder_bracket_R.stl","stl/reference/dummy_servo_arm_L.stl","stl/reference/dummy_servo_arm_R.stl","stl/reference/dummy_horn_arm_L.stl","stl/reference/dummy_horn_arm_R.stl"]
json.dump(o,open("results/metrics_v01.json","w"),indent=1,default=float)
print(json.dumps({k:o[k] for k in ("mass","clinging","hug_springs","head","servo_power")},indent=1,default=float))
