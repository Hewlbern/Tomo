# SPDX-License-Identifier: MIT
"""Tomo (formerly evoKin V.01) metrics from the exported STLs: mass and centre of mass, hanging stability on a strap,
passive-hug spring forces (from results/summary_sweep.json), head pan/tilt loads vs the FS90MG, servo power budget,
and which STLs changed vs the servo-clasp V.01 (commit bed94ce). Estimates only; nothing has been built or weighed."""
import numpy as np, trimesh, json, os, sys, hashlib, subprocess, math
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
G=9.81; RHO_PLA=1.24e-3; RHO_TPU=1.21e-3
FILL=0.75      # ASSUMED effective density of a 3-perimeter, 20 % infill print of these thin parts (solid = 1.0)
STALL_KGCM_6V=2.2; STALL_A_6V=0.8
L=lambda n: trimesh.load(stl_path(n))
SW=json.load(open("results/summary_sweep.json"))
o={"assumptions":dict(material=f"PLA 1.24 g/cm³ × {FILL} effective fill (solid upper bound also given); TPU pads 1.21 g/cm³ solid",
   components="FS90MG 13.4 g each (Feetech listing), horn 1 g, Adafruit 3351 speaker 25 g (ASSUMED), XIAO ESP32S3 Sense + camera 8 g, amp 2 g, mic 1 g, INA219 2 g, boost 5 g, wiring 8 g, fasteners 8 g, springs 2 × 1 g, fur skin 30 g (ASSUMED). Battery listed separately (portable power unresolved).",
   cad_only=True,physically_tested=False)}
printed="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer neck_turret tilt_hub head_back head_front arm_L arm_R bezel shutter".split()
items=[]
for n in printed:
    m=L(n); q=2 if n=="bezel" else 1
    items.append((n,m.volume*RHO_PLA*FILL*q,m.center_mass if n!="bezel" else np.array([0,-37.0,120.0]),m.volume*RHO_PLA*q))
for n in ("paw_pad_L","paw_pad_R"):
    m=L(n); items.append((n,m.volume*RHO_TPU,m.center_mass,m.volume*RHO_TPU))
def cen(n): return L(n).center_mass
comp=[("FS90MG pan + horn",14.4,cen("dummy_servo_yaw")),("FS90MG tilt + horn",14.4,cen("dummy_servo_tilt")),
      ("speaker (Adafruit 3351)",25.0,cen("dummy_speaker")),("brain + camera",8.0,cen("dummy_pi")),("amp",2.0,cen("dummy_amp")),
      ("mic",1.0,cen("dummy_mic")),("INA219 + boost",7.0,np.array([0,10.0,40.0])),("wiring",8.0,np.array([0,0,60.0])),
      ("fasteners",8.0,np.array([0,-5.0,60.0])),("springs",2.0,np.array([0,-31.2,78.0])),("fur skin",30.0,np.array([0,0,70.0]))]
for c in comp: items.append((c[0],c[1],c[2],c[1]))
def summ(items,solid=False):
    m=np.array([it[3] if solid else it[1] for it in items]); p=np.array([it[2] for it in items]); return float(m.sum()), (m[:,None]*p).sum(0)/m.sum()
mt,cm=summ(items); ms,_=summ(items,True)
bat=("1S LiPo 2000 mAh (optional, portable power unresolved)",38.0,np.array([0,12.0,14.0]),38.0)
mtb,cmb=summ(items+[bat])
o["mass"]=dict(estimate_g=round(mt,0),solid_print_upper_bound_g=round(ms,0),with_2000mAh_battery_g=round(mtb,0),
   centre_of_mass_mm=np.round(cm,1).tolist(),centre_of_mass_with_battery_mm=np.round(cmb,1).tolist(),
   breakdown_g={it[0]:round(it[1],1) for it in items},
   note="Mirumi is 155 g and about 100 x 118 x 143 mm. Tomo is one Ø92 x 148 mm egg (about 102 x 108 x 152 mm with 4-5 mm fur and the arms) and carries a speaker and a camera brain, so it is heavier.")
# ---- clinging to a bag handle that runs diagonally across the chest (Mirumi pose) and hanging free from it
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
            note="Hanging free from the handle (nothing under it): the body rolls about the handle until the COM is under it, so with a vertical handle it hangs tipped about 35 deg sideways; slip along the handle is resisted only by friction."))
o["clinging"]=dict(no_battery=cling(mt,cm),with_battery=cling(mtb,cmb),
   per_handle={f'{g["d_mm"]}':dict(pad_force_total_N=g["total_pad_force_N"],into_groove_N=g["total_into_groove_N"],
        free_hang_slip_SF_no_battery=round(0.5*2*g["total_pad_force_N"]/(mt/1000*G),2)) for g in H["grip"]},
   assumption="Handle Ø12.5 lying on the diagonal groove floor line (35° from the body vertical). μ = 0.5 TPU/fur on a fabric or leather handle (ASSUMED). Pad forces from scripts/sim_v01.py. Not tested.")
L_lev={sd:float(np.linalg.norm((L(f"paw_pad_{sd}").center_mass-np.array([(1 if sd=="L" else -1)*(gg.eggr(78)+8.5)*math.cos(math.radians(-35)),(gg.eggr(78)+8.5)*math.sin(math.radians(-35)),0]))[:2])) for sd in ("L","R")}
Mopen=H["spring"]["torque_at_open_stop_Nmm"]; sig=32*Mopen*1.1/(math.pi*1.22**3)
o["hug_springs"]=dict(rate_Nmm_per_deg=H["spring"]["rate_Nmm_per_deg"],preload_deg=H["spring"]["preload_deg"],
   torque_rest_Nmm=H["spring"]["torque_at_rest_Nmm"],torque_open_stop_Nmm=Mopen,
   finger_force_to_hold_open_at_pad_N={sd:round(Mopen/L_lev[sd],2) for sd in L_lev},pad_lever_mm={sd:round(L_lev[sd],1) for sd in L_lev},
   grip={f'{g["d_mm"]}':dict(open_deg_L=g["L"].get("open_deg"),open_deg_R=g["R"].get("open_deg"),force_L_N=g["L"].get("pad_normal_force_N"),force_R_N=g["R"].get("pad_normal_force_N"),total_N=g["total_pad_force_N"]) for g in H["grip"]},
   spring_stress_check=f"σ ≈ 32·M·Ki/(π·d³) with M = {Mopen:.0f} N·mm at the open stop (80° wind-up), d = 1.22 mm, Ki ≈ 1.1: ≈{sig/1000:.2f} GPa, under the ≈1.86 GPa at the catalogue 90° rating (302.7 N·mm).")
# ---- head pan / tilt loads
head=[L(n) for n in ("head_front","head_back","tilt_hub")]
hm=sum(h.volume for h in head)*RHO_PLA*FILL+8.0+2*1.0    # + camera/brain allowance + bezels
hc=sum(h.volume*h.center_mass for h in head)/sum(h.volume for h in head)
ax=np.array([0,6.0,119.0]); arm=float(np.hypot(hc[1]-ax[1],hc[2]-ax[2]))
tau_tilt=hm/1000*G*arm/1000      # N·m worst case (lever horizontal)
turret=[L(n) for n in ("neck_turret","yaw_coupler","yaw_retainer_A","yaw_retainer_B")]
parts=head+turret
I=sum(p.moment_inertia[2,2]*RHO_PLA*FILL + p.volume*RHO_PLA*FILL*(p.center_mass[0]**2+p.center_mass[1]**2) for p in parts)+14.4*(15**2)
th=np.radians(60); t=0.12; alpha=4*th/t**2; tau_acc=float(I)*1e-9*alpha
o["head"]=dict(pan=dict(servo="FS90MG in the yaw collar (unchanged)",software_clamp_deg=[-42,42],hard_stop_deg=SW["stop_engagement"]["yaw_pos"]["yaw"],
      moving_inertia_g_mm2=round(float(I),0),accel_torque_60deg_in_0p12s_kgcm=round(tau_acc/G*100,4),fraction_of_stall_6V=round(tau_acc/G*100/STALL_KGCM_6V,4),
      note="Pan now also turns the turret and the tilt servo."),
   tilt=dict(servo="FS90MG on the neck turret, spline on the tilt axis (x direction, y=6, z=119)",software_clamp_deg=[-10,10],
      first_contact_deg=dict(nod_down=SW["stop_engagement"]["tilt_down"]["tilt"],look_up=SW["stop_engagement"]["tilt_up"]["tilt"]),
      head_mass_g=round(hm,1),head_com_from_axis_mm=round(arm,1),gravity_torque_kgcm=round(tau_tilt/G*100,3),fraction_of_stall_6V=round(tau_tilt/G*100/STALL_KGCM_6V,3)))
o["servo_power"]=dict(servos=2,channels=["head pan","head tilt"],stall_each_A_6V=STALL_A_6V,worst_case_all_stalled_A=round(2*STALL_A_6V,2),
   note="Arms are passive and draw nothing; hugging costs no power. Budget the 5 V servo rail for ≥1.6 A peak.")
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
