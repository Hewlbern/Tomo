# SPDX-License-Identifier: MIT
"""evoKin V.01 joint metrics from the exported STLs: arm mass/torque vs the FS90MG, clasp grip force (datasheet
torque only), head-pan inertia, reach, pinch gaps, servo power budget, and which parts changed vs v4.
Imposed kinematics and solid-PLA upper bounds only."""
import numpy as np, trimesh, json, os, sys, hashlib, subprocess
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from stl_paths import stl_path
from trimesh.transformations import rotation_matrix as Rm
RHO=1.24e-3            # g/mm³, solid PLA (upper bound; a 20–40 % infill print is lighter)
G=9.81
SH=np.array([0,13.0,60.0]); REST_L=-15.0; REST_R=-25.0
FORE_R=71.0; FORE_RIN=66.0; FORE_ROUT=76.0
STALL_KGCM_6V=2.2; STALL_A_6V=0.8   # official FS90MG drawing/spec, 6 V. 5 V figures are not on the drawing (expect lower torque).
L=lambda n: trimesh.load(stl_path(n))
o={"assumptions":dict(material="solid PLA 1.24 g/cm³ (upper bound)",sleeve_fur_g="4 g per arm, ASSUMED (not weighed)",
   horn_g="1 g, ASSUMED",stall=f"{STALL_KGCM_6V} kg·cm / {STALL_A_6V} A at 6 V (official); 5 V not specified",
   cad_only=True,physically_tested=False)}
# ---- arm torque
arm=L("arm_L"); horn=L("dummy_horn_arm_L")
m_arm=arm.volume*RHO; m_fur=4.0; m_horn=1.0
def com_r(mesh):   # distance of the centre of mass from the shoulder axis (x axis through SH)
    c=mesh.center_mass; return float(np.hypot(c[1]-SH[1],c[2]-SH[2]))
r_arm=com_r(arm); sl=L("sleeve_proxy_L"); r_fur=com_r(sl)
m_tot=m_arm+m_fur+m_horn
tau_gmm=m_arm*r_arm+m_fur*r_fur        # horn on the axis
tau_kgcm=tau_gmm/1000/10               # g·mm -> kg·cm
o["arm_drive"]=dict(arm_print_g=round(m_arm,2),total_moving_g=round(m_tot,2),arm_com_from_axis_mm=round(r_arm,1),
   fur_com_from_axis_mm=round(r_fur,1),gravity_torque_max_kgcm=round(tau_kgcm,3),
   fraction_of_stall_6V=round(tau_kgcm/STALL_KGCM_6V,3),
   paw_force_at_stall_N=round(STALL_KGCM_6V*G/(FORE_R/10),2),
   note="Worst case is the arm horizontal. paw_force_at_stall = 2.2 kg·cm at r=71 mm (blade centre) — the most a blade can push on a finger before the servo stalls.")
# ---- clasp grip force (datasheet stall torque only; no friction claimed)
tau=STALL_KGCM_6V*G/100                 # N·m
sw0=json.load(open("results/summary_sweep.json")); C=sw0.get("clasp",{})
pen=next((g for g in C.get("grip_clearance",[]) if g["d_mm"]==8 and g["mean_deg"]==-10),None)
aR=pen["armR"] if pen else -16.45
tg=tau_gmm*1e-6*G                       # N·m, gravity torque of one arm when horizontal
tgR=tg*np.cos(np.radians(aR))           # the lower (right) arm lifts its own weight while squeezing up
o["clasp_grip"]=dict(
   mechanism="Both FS90MG arm servos drive their forearm blades toward each other about the shared shoulder axis; the object is squeezed between the blades.",
   stall_torque_Nm=round(tau,4),
   pinch_force_at_stall_N=dict(at_r66_inner_edge=round(tau/0.066,2),at_r71_blade_centre=round(tau/0.071,2),at_r76_outer_edge=round(tau/0.076,2)),
   pinch_force_at_stall_pen_pose_N=round((tau-tgR)/0.071,2),
   pen_pose=dict(armL=pen["armL"] if pen else None,armR=aR,gap_mm=8),
   gravity_torque_one_arm_horizontal_Nm=round(tg,5),
   continuous_hold_suggestion_N=round(0.5*tau/0.071,2),
   gap_control=C.get("delta_deg_for_gap"),
   closed_gap_mm=C.get("closed_gap_mm"), interlock_deg=7.5,
   compliance="2 mm fur sleeve over each blade (≈4 mm of compressible pile in the clasp). Squeeze is set by commanding the blades past contact; the servo's position loop then pushes up to stall. No spring or breakaway part.",
   note="Datasheet stall torque 2.2 kg·cm at 6 V, both servos at stall; 5 V torque is not specified (expect less). Not measured. Holding a stalled FS90MG continuously heats it: grip at ≤50 % for long holds, and let the INA219 trip limit current.")
# ---- reach: paw front point at several angles
def paw_front(a):
    m=arm.copy(); m.apply_transform(Rm(np.radians(-(a-REST_L)),[1,0,0],SH)); v=m.vertices
    return dict(front_y=round(float(v[:,1].min()),1),top_z=round(float(v[:,2].max()),1),bottom_z=round(float(v[:,2].min()),1))
o["arm_reach"]={f"a{a}":paw_front(a) for a in (-45,-15,0,15,30)}
o["arm_reach"]["note"]="Torso front is y=-40, head front ≈ y=-37. Negative y = in front of the bear. The desk is z=0 (torso bottom)."
o["arm_travel"]=dict(software_clamp_deg=[-45,30],interlock="armL - armR >= 7.5 deg (left blade over right)",servo_deg_used=75,servo_deg_available=180,
   pulse_map="≈ 500–2500 µs over 180° (FS90MG spec); calibrate centre per servo; ≈0.85° of differential angle per mm of grip gap")
# ---- head pan
head=[L(n) for n in ("head_front","head_back","yaw_coupler","yaw_retainer_A","yaw_retainer_B")]
hm=sum(h.volume for h in head)*RHO+3.0      # + ~3 g camera module (ASSUMED)
I=sum(h.moment_inertia[2,2]*RHO + h.volume*RHO*(h.center_mass[0]**2+h.center_mass[1]**2) for h in head)  # g·mm² about the z axis (parallel-axis)
I_gmm2=float(I)
# 60° in 0.12 s with a triangular velocity profile -> alpha = 4θ/t²
th=np.radians(60); t=0.12; alpha=4*th/t**2
tau_acc=I_gmm2*1e-9*alpha      # N·m
o["head_pan"]=dict(servo="FS90MG in the yaw collar (unchanged from v3)",software_clamp_deg=[-42,42],hard_stop_deg=47,
   head_printed_plus_camera_g=round(hm,1),inertia_about_z_g_mm2=round(I_gmm2,0),
   accel_torque_for_60deg_in_0p12s_kgcm=round(tau_acc/G*100,4),fraction_of_stall_6V=round(tau_acc/G*100/STALL_KGCM_6V,4),
   tilt="not fitted", note="Yaw axis is vertical, so gravity does not load the pan servo; friction on the 0.35 mm journal is untested.")
# ---- pinch gaps from the sweep
sw=json.load(open("results/summary_sweep.json"))
o["pinch_gaps_mm"]=dict(hub_to_cap_face=0.6,arm_to_shell_min=sw["arm_min_clearance_mm"]["arm_to_shell"],
   sleeve_to_torso_fur_min=sw["arm_min_clearance_mm"]["sleeve_to_fur"],
   clasp_blade_gap_range=[C.get("closed_gap_mm"),C.get("max_gap_in_travel_mm")],
   note="The clasp is a deliberate pinch point: the blades close to ~1 mm and can trap a finger with up to ~3 N per the datasheet torque. "
        "Hub/shell rigid gaps are under 4 mm. Not assessed against any toy standard.")
# ---- shoulder pods vs the 4 mm torso fur envelope (tegg(-4) = ellipsoid 50 x 44 x 54 semi-axes about z=50)
tb=L("torso_back"); v=tb.vertices
rn=np.sqrt((v[:,0]/50)**2+(v[:,1]/44)**2+((v[:,2]-50)/54)**2)
out_pts=v[(rn>1.0)&(v[:,2]<85)]
prot=0.0
if len(out_pts):
    # approximate radial protrusion beyond the fur envelope
    r=np.sqrt((out_pts[:,0]/50)**2+(out_pts[:,1]/44)**2+((out_pts[:,2]-50)/54)**2)
    prot=float(np.max((1-1/r)*np.linalg.norm(out_pts-[0,0,50],axis=1)))
o["shoulder_pod_vs_fur_envelope"]=dict(max_protrusion_mm=round(prot,1),
   note="Positive = the printed pod corner pokes outside the nominal 4 mm torso fur envelope (fur skin must be patterned over it).")
# ---- power
o["servo_power"]=dict(servos=3,channels=["head pan","arm L","arm R"],stall_each_A_6V=STALL_A_6V,
   worst_case_all_stalled_A=round(3*STALL_A_6V,2),
   note="Budget the 5 V servo rail for ≥2.4 A peak or stagger moves in firmware. The XL6009 module is not specified for that; the protected 2 A+ Pololu S13V20F5 is closer but still below an all-stalled peak.")
# ---- changed vs v4
def sha(b): return hashlib.sha1(b).hexdigest()
chg={}
for f in sorted(os.listdir("stl"))+["reference/"+x for x in sorted(os.listdir("stl/reference"))]:
    if not f.endswith(".stl"): continue
    new=open("stl/"+f,"rb").read()
    try: old=subprocess.run(["git","show",f"d8b6367:stl/{f}"],capture_output=True,check=True).stdout
    except subprocess.CalledProcessError: chg[f]="new in V.01"; continue
    if sha(old)==sha(new): chg[f]="identical"; continue
    a=trimesh.load(trimesh.util.wrap_as_stream(old),file_type="stl"); b=trimesh.load(trimesh.util.wrap_as_stream(new),file_type="stl")
    same=abs(a.volume-b.volume)<0.5 and np.allclose(a.bounds,b.bounds,atol=0.01)
    chg[f]="geometrically unchanged (bytes differ)" if same else f"changed (volume {a.volume:.0f} -> {b.volume:.0f} mm³)"
o["changed_vs_v4"]=chg
json.dump(o,open("results/metrics_v01.json","w"),indent=1,default=float)
print(json.dumps(o,indent=1,default=float))
