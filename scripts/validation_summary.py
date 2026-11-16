# SPDX-License-Identifier: MIT
"""Collect the V.01 passive-hug validation numbers into results/validation_summary.json."""
import json, os
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
SW=json.load(open("results/summary_sweep.json")); FA=json.load(open("results/fit_audit.json")); ME=json.load(open("results/metrics_v01.json"))
st=SW["stop_engagement"]; H=SW["hug"]
out=dict(
  version="V.01 passive spring hug, Mirumi proportions (one egg body, two short symmetric shoulder arms, centre groove)",
  project="Tomo by DreamMachina (formerly evoKin V.01)",
  repository="https://github.com/Hewlbern/Tomo",
  cad_only=True, physically_tested=False, child_ready=False, power="bench rail only",
  date_local_australia_sydney="2026-11-16",
  official_FS90MG="datasheets/FS90MG.pdf p.5, edition A/0, 2021-04-30, all ±0.1 mm",
  servos=dict(count=2,
    head_pan="Feetech FS90 in yaw_collar, software ±42°, hard stop ±47°",
    head_tilt=f"Feetech FS90 on neck_turret, axis along x through y=6, z=119; software ±10°, first contact +{st['tilt_down']['tilt']}° (nod down) / {st['tilt_up']['tilt']}° (look up)",
    arms="none — passive"),
  hug=dict(
    mechanism="Mirumi-style passive hug: each arm turns on a vertical M3 shoulder pin just under the face (knuckle z 70–86); a music-wire torsion spring in the knuckle closes it onto a printed rest stop (30° preload); opened by hand to a 60° printed stop; zero power to hold. Two short symmetric arms whose paws nearly meet in front of the handle",
    spring=H["spring"], arm_angle_convention="0 = closed on the rest stop, + = open; rotation about z through each shoulder (x=±44.6, y=−31.2)",
    groove="R8 channel down the front centre, 1.7° from vertical (for a handle upright), floor 2.5 mm (z 48) to 4 mm (z 80) below the skin, capsule z ≈ 36–94 (up to the torso rim), 2.4 mm liner; paws meet at z ≈ 70 (upper chest)",
    grip=H["grip"], open=H["open"], assumption=H["assumption"],
    stops=dict(closed=st["armL_closed_stop"]["armL"], open=st["armL_open_stop"]["armL"])),
  sweep=dict(poses=SW["sweep"]["poses"], pair_tests=SW["sweep"]["pair_tests"], booleans=SW["sweep"]["aabb_passed_to_boolean"],
             rigid_overlaps_in_travel=len(SW["rigid_overlaps_in_travel"]),
             head_tilt_clearance_mm=SW.get("head_tilt_clearance_mm"), arm_min_clearance_mm=SW.get("arm_min_clearance_mm")),
  fit_audit=FA["summary"] if "summary" in FA else None,
  mass=dict(estimate_g=ME["mass"]["estimate_g"], solid_upper_bound_g=ME["mass"]["solid_print_upper_bound_g"],
            with_400mAh_battery_g=ME["mass"]["with_battery_g"], centre_of_mass_mm=ME["mass"]["centre_of_mass_mm"]),
  proportions=dict(shell_mm="Ø92 x 148 (one egg: R46 at z58, superellipse n=3.4 dome)", with_fur_mm="≈106 wide (arm knuckles) x 104 deep x 152 tall", mirumi_mm="≈100 x 118 x 143"),
  clinging=ME["clinging"],
  servo_power=ME["servo_power"])
json.dump(out,open("results/validation_summary.json","w"),indent=1,ensure_ascii=False); print("wrote results/validation_summary.json")
