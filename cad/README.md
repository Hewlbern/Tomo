# Tomo by DreamMachina (formerly evoKin V.01) — CAD note: Mirumi-style passive spring hug, head pan + tilt

This is the detailed engineering note for the OpenSCAD model in this folder. The project README is one level up. Repository: [github.com/Hewlbern/Tomo](https://github.com/Hewlbern/Tomo).

**CAD only. Unprinted. Grip, hanging, spring life and wear are untested.
Not production, not child-ready, not waterproof. Power is bench-tethered only.
Do not treat these STLs as a fit-check or a print-ready kit.**

Source: [`evokin_v01.scad`](evokin_v01.scad) (internal file names keep the `evokin_` prefix; the servo-clasp V.01 is in git history at `bed94ce`, v4 at `d8b6367`, v3 at `237c37d`).

Pose variables: `yaw` (pan, deg), `tilt` (deg, + = nose down), `armL` / `armR` (opening angle, 0 = closed on the rest stop). STLs are exported at all zeros. Pose a part by hand with `-D yaw=… -D tilt=… -D armL=… -D armR=…`.

## What changed vs the servo clasp (bed94ce)

- **Arm servos removed.** Shoulder pods in `torso_back`, `shoulder_bracket_L/R`, arm hubs, arm-servo and arm-horn dummies are gone.
- **Passive hug arms.** Each arm is a curved band (hull chain of r = 3 spheres at z 25 / 35, so the band spans z 22–38) that follows the torso egg at an 8.5 mm offset from ψ = −20° at the hinge to ψ = −76°, then curls in to a paw near x ≈ ±5, y ≈ −42. The inner face sits 5.5 mm off the shell, clear of 4 mm fur.
- **Vertical hip hinge**, one per side at (±49.95, −16.19). See the table below.
- **Torsion spring** per hip, preloaded 35° against a printed rest stop; printed open stop at 40°.
- **Belly groove** moulded into `torso_front`, leaning 14°; **TPU paw pads** (`paw_pad_L/R`).
- **Head tilt.** New `neck_turret` (rides the yaw journal, carries the tilt FS90MG) and `tilt_hub`; `head_back` / `head_front` changed. Servo count stays at two.
- New reference module `grip_rod(d)` (Ø12.5 test rod lying in the groove, `stl/reference/grip_rod.stl`).

### Hip hinge (each side, mirrored)

| Item | Value |
|---|---|
| Axis | vertical (z), x = ±49.95, y = −16.19 |
| Arm knuckle | Ø16, z 22–38; Ø3.4 running bore for an M3 pin; Ø11 spring recess from z = 30 to the top; arm-side leg slot; 64° relief sector in the top (stop lug travel 0–40°) |
| Upper ear | moulded into `torso_front` on a hip web, z 38.4–43.4; Ø3.2 pin hole, Ø6 counterbore for the head; **Ø5.9 spigot** down into the spring (spring ID 7.1 free, ≈6.8 at full wind-up); **stop lug** 24° wide, r 5.7–7.7, centred at 60°, from z 35.8 |
| Hip cap | separate (`hip_cap_L/R`), z 16.6–21.6, 2 × M2.5 into the hip web, M3 nyloc hex trap; 0.4 mm axial gap each side of the knuckle |
| Pin | M3 × ~30 socket head, nyloc underneath; snug, not clamped |
| Spring | music wire 0.048 in (1.22 mm), 3/8 in OD, 90° legs (trim to ~6 mm); Grainger 3HPG6 (LH, left arm) / 3HPD1 (RH, right arm); 2.679 lbf·in = 302.7 N·mm at 90° → **3.363 N·mm/°** |
| Preload / travel | 35° at the closed stop (117.7 N·mm), 75° at the 40° open stop (252.3 N·mm, inside the 90° rating; bending stress ≈1.55 GPa vs ≈1.86 GPa at the rating) |
| Stops | sweep: closed stop engages at −0.5°, open at 40.5° |
| Clearances | arm ↔ hip cap 0.4 mm; arm ↔ shell 0.39 mm in travel (0 at the stops, where the lug touches); closed pad ↔ shell 1.04 mm; band never below z = 22 |

### Belly groove

| Item | Value |
|---|---|
| Shape | capsule of R8 spheres from z = 12 to 62, centre line 8 mm in front of the floor line |
| Floor line | y = −30 − 0.25·(z − 30): leans 14° (top forward) so a straight strap clears the upper belly and the speaker grille |
| Liner | 2.4 mm wall inside the shell; ≈0.9 mm to the speaker pocket at z ≈ 53; Pi ↔ liner 0 mm³ |
| Objects | round Ø10–15 (Ø12.5 reference rod touches the floor only, 0.06 mm³ facet contact); flat strap 25 × 2.5 laid across the groove |

### Grip (catalogue rate, not measured)

Force per paw = spring torque ÷ perpendicular lever from the hinge axis to the pad contact. Contact sits low on the pad (z ≈ 36).

| Object | Opens | Torque | Lever | Per paw | Push into groove |
|---|---:|---:|---:|---:|---:|
| Ø10 | 1.90° | 124.1 N·mm | 51.3 mm | 2.42 N | 3.66 N |
| Ø12.5 | 4.39° | 132.5 N·mm | 51.0 mm | 2.60 N | 3.70 N |
| Ø15 | 6.83° | 140.7 N·mm | 50.8 mm | 2.77 N | 3.73 N |
| Flat 25 × 2.5 | 2.62° | 126.5 N·mm | 43.9 mm | 2.88 N | 5.76 N |

The rigid arm stays ≈1.46–1.48 mm clear of each object; the 1.5 mm TPU pad makes the contact. Holding the arms fully open takes ≈4.95 N at each paw. Open: pad ↔ belly 28.3 mm, tip ↔ tip 54 mm; a Ø15 rod slides in along the groove normal without touching the arms.

Hanging (no battery, 263 g): COM 40.6 mm behind the strap axis, body leans back 14°, pitch moment 105 N·mm carried by a 27 mm couple between the paws and the top of the groove → 3.86 N needed vs 5.2 N available; friction capacity 9.06 N at μ = 0.5 (assumed) → slip factor 3.5 (3.3 with a 2000 mAh battery).

### Head tilt

| Item | Value |
|---|---|
| Axis | along x through y = 6, z = 119 (+ = nose down). The camera sits at y −19.5…−8, which forced the axis back to y = 6 |
| Servo | FS90MG, case top at x = −22, spline pointing −x, screwed by its tabs to a cradle plate on the turret (x −17.8…−14.8) |
| Hub | `tilt_hub`: Ø18 × 2.5 disc on the horn (2 × M2 at r = 7, assumed), 10 × 10 key into a socket in `head_back`; spline-tip clearance bore 2.6 deep |
| Idler | turret column at x 24–27 with an M3 thread-forming pivot screw into a boss on `head_back` |
| Turret | `neck_turret` took over `head_back`'s skirt, cone, coupler slot, retainer pilots and pan-stop lug; deck front cut away at y < −3 above z 98.6 |
| Head shell | starts at z = 103.5 (was 101); lower seam bosses at x ±32, z 106; upper at x ±28, z 138 |
| Range | firmware ±10°; first contact +12° (head_front rim on yaw_collar) and −15.5° (head_back on turret). At ±12°: turret 0.6 mm, camera ↔ tilt servo ≥4.9 mm |
| Load | head ≈41 g, COM 9 mm from the axis: 0.037 kg·cm = 1.7 % of stall |
| Cables | tilt lead crosses the pan joint (≥40 mm loop down the Ø34 bore, tied to the FPC); FPC loop bay near the tilt axis, ±3 mm of travel at ±10° |

## Official FS90MG drawing (verified)

File: [`../datasheets/FS90MG.pdf`](../datasheets/FS90MG.pdf) (edition A/0, model FS90MG-C001, 2021-04-30; fetched from Feetech, file dated 23 Jun 2026). All linear values below are **±0.1 mm** as on p.5.

| Feature | Drawing | Used in CAD |
|---|---|---|
| Body L × W | 22.5 × 12.1 | yes |
| Case height | 22.4 | yes |
| Boss top (C) | 26.7 | yes (boss height 4.3) |
| Overall (spline tip) | 30.7 | yes (spline 4.0 above boss) |
| Tab overall | 32.3 | yes |
| Hole centres | 27.7 | yes |
| Hole Ø | 2.2 | tab holes (printed pilots are 1.7) |
| 8.7 | body-end (spline side) to spline axis | s_off = 22.5/2 − 8.7 = **2.55 mm** |
| Spline | Ø4.7, marked **20T** | shaft envelope Ø4.7; tooth count not modelled |
| Tab underside | 18.2 mark | tab thickness 4.2, top flush with the case |
| 15.7 | lower-body step | not used for the seat |

8.7 is **not** a centre offset. The witness lines on p.5 run from the body end (same datum as the 22.5) down to the spline crosshair. Check: left hole at body-end − 2.6, right hole at body-end + 22.5 + 2.6, spline at +8.7 → 11.3 + 16.4 = 27.7.

### Discrepancies and flags (measure on arrival)

1. Spec text 6-1 is 22.5 × 12.1 × **26.7** (C = boss top), not the 30.7 overall to the spline tip.
2. 6-9 and the p.5 drawing say **20T / Ø4.7**. Feetech product pages and the wiki say **21T**. CAD uses the drawing (20T / Ø4.7 envelope). Count the teeth on arrival.
3. Page 6 is a nearly blank **“No Accessories”** sheet. Product pages usually include POM horns and screws. Horn size is **not specified**. CAD uses an **assumed** typical disc + 4-arm star, **2.0 mm thick, Ø24 envelope**. Leave ≥ 2 mm air from the horn top to the drum underside (4.0 mm from boss top to drum). **Measure the included horn.**
4. The included horn screw is listed as **M2.5 × 4** (6-13). That is too short for 2.0 mm horn + 1.6 mm yaw coupler + thread. Buy a longer M2.5 (8–10 mm) and confirm on arrival.
5. p.3 no-load speed “0.87 sec/60° at 4.8 V” is almost certainly a missing zero (0.087).
6. Stall 2.2 kg·cm / 800 mA at 6 V, 180° at 500–2500 μs, cable 25 cm. Bench rail only; budget 800 mA per servo conservatively.

## Seams and fasteners (one scheme)

- Male registration lip on the **back** half, female groove on the **front**, **0.25 mm** FDM clearance.
- **0.40 mm** chamfer on the outer seam edge (bed face when printed seam-down) to give elephant-foot somewhere to go.
- **M2.5: clearance 2.8** in the front / through / accessible half; **pilot 2.1** in the back / receiving half. Optional M2.5 heat-set later: bosses are Ø7.
- Servo-tab self-tappers (or M2): **pilot 1.7** in the yaw hanger and the tilt cradle on the neck turret, through the servo’s Ø2.2 tab holes.
- Yaw retainers: **M2 clearance 2.3** in the retainer, **pilot 1.7** in the neck_turret skirt.

## Yaw stack

- Journal OD 44.0, skirt ID 44.7, **0.35 mm** radial running clearance.
- Blade 2.0 mm in a 2.7 mm slot (now on the `neck_turret`), **0.35 mm** per side. Backlash at r = 8 mm ≈ **5.0°** total. Software yaw clamp **±42°** so the ~47° hard stop is not a running face.
- Justification: 0.35 mm is the tight end of the requested 0.35–0.4 mm FDM running-fit band. v2’s 0.30 mm is too tight once typical hole shrinkage and elephant-foot are included. 0.40 mm would add more yaw backlash than needed. Revisit after the first article.
- Separate **yaw_thrust_washer** (0.8 mm, ID 35, OD 43), printed flat, no supports. Journal top 97.4, washer 97.4–98.2, designed **0.30 mm** axial gap, turret cone at 98.5.
- `neck_turret` (which took over the skirt and cone from `head_back`) prints skirt-down; the underside is a **30°-from-vertical cone**, so a 35° support threshold should not put supports on a flat thrust face. The flat thrust is the washer.
- Retainer axial play **0.35 mm**. Retainer OD is 48 mm so the M2 holes at r = 23.8 go through both the retainer and the skirt.
- The official tab holes sit at r = 16.4 and 11.3, **inside** a Ø34 cylinder, so the collar bore is **stepped**: boss clearance in the flange, Ø34 from the boss top (z = 88.3) up, for horn / coupler / ribbon installation from above.

## Electronics seats

- **Speaker:** Adafruit **3351** Mono Enclosed, **3 W 4 Ω**, 70 × 30 × 17 mm, holes Ø3.4 on 63 × 24, Core **A$8.95**. This is the honest match for MAX98357A (3.2 W into 4 Ω at 5 V). The v2 Ø28 placeholder and any 0.5 W 8 Ω mini are retired. The front grille is now a 66 × 26 window.
- **Amp:** Adafruit 3006 MAX98357A, pocket 19.4 × 17.8 × 3.0 plus 8 mm headroom for the post-2024 terminal block, on the +y face of the tray spine. Two M2 pilots at an **assumed** 15 × 13 span — measure the board.
- **Mic:** Adafruit 3421, 16.7 × 12.7 × 1.8, bottom-ported, pocket aligned to the Ø2.4 shell hole at (18, front, 80).
- **Ribbon:** loop bay r = 14 mm (π·14 ≈ 44 mm extra vs the ≥ 9.4 mm requirement), slot 17 × 2.5 mm for a 15 × 1 mm FPC. Path: camera → loop (head) → turret deck slot at x = 14 → +x side of the Ø34 bore → torso duct → Pi CSI.
- **Pi:** y-envelope 8.5 mm (v2’s 5 mm was tight if a header is used). Camera is the standard Module 3 (25 × 24 × 11.5), not the Wide.

## Tray tabs

10 × 3 × 10 mm tabs at **x = ±29, z = 23** (v3: ±34) sit in 10.6 × 3.6 × 10.6 mm pockets (0.3 mm per side) in 14 mm ribs. They moved inboard and down in v4 to clear the (now removed) shoulder pods. The tab is retained over its outer ~5 mm only, where the rib is clear of the spine relief; watch for rattle on the first print.

## Assembly order (so the pilots are reachable)

1. **Hips:** spring into the knuckle recess (arm leg in its slot); knuckle under the ear with the spring over the spigot; wind 35° and hook the torso leg; hip cap on (2 × M2.5); M3 pin from the top, nyloc underneath, snug. Press on the TPU pads.
2. **Tray** into the torso pockets; close the torso shells on the registration lip (M2.5 front → back).
3. **Head pan:** FS90MG into the collar hangers from below; collar onto the torso. From above, through the Ø34 bore: horn, coupler, longer M2.5 horn screw; thrust washer on the journal. Lower the `neck_turret`; retainers from the side into its skirt.
4. **Head tilt:** tilt FS90MG to the turret cradle (tab self-tappers). Centre it, horn on, `tilt_hub` on the horn (2 × M2). Hang `head_back` on the hub key and the M3 idler screw; close `head_front` (M2.5).

## Test coupon

`../stl/coupon.stl`: one plate with the journal + skirt (0.35 mm radial) + 0.8 mm washer, a 10 mm tab in a 10.6 mm pocket, and an FS90MG shelf with 27.7 mm span / 1.7 mm pilots. Print this first if you print at all. A passing coupon is **not** a full fit-check.

## Parts that changed vs the servo clasp (bed94ce)

**New:** `neck_turret`, `tilt_hub`, `hip_cap_L/R`, `paw_pad_L/R`; reference `dummy_servo_tilt`, `dummy_horn_tilt`, `grip_rod`.

**Changed — reprint:** `torso_front` (groove, hips), `torso_back` (pods removed), `head_back`, `head_front`, `arm_L`, `arm_R`.

**Removed:** `shoulder_bracket_L/R`, `dummy_servo_arm_L/R`, `dummy_horn_arm_L/R`.

**Unchanged:** `tray`, `yaw_collar`, `yaw_coupler`, `yaw_retainer_A/B`, `yaw_thrust_washer`, `bezel`, `shutter`, `coupon`. Per-file volumes: `results/metrics_v01.json` → `changed_vs_servo_clasp_bed94ce`.

## Rebuild / audit

```bash
# from the repository root
EXPORT_CHECK=1 bash scripts/build_stl.sh   # needs OpenSCAD 2021.01+; posed copies go to check/
python3 scripts/sim_v01.py                 # sweep + hug checks, 457 poses, ~2 minutes
python3 scripts/fit_audit.py
python3 scripts/metrics_v01.py
python3 scripts/validation_summary.py
python3 scripts/render_v01.py
# or: bash scripts/run_all.sh
```

## Residual blockers

- Nothing here has been printed or assembled. The audit is CAD measurements on exported STLs (25/25 fit-audit rows, 0 rigid overlaps in a 457-pose sweep).
- Grip forces come from the catalogue spring rate with no hinge friction; real pads, fur and friction will change them. Spring price on Raptor Supplies AU is inconsistent (A$16.98 vs ≈A$108 per 6-pack); confirm the part and winding hand before ordering.
- The paws close to a soft ≈2.5 N pinch; the arms open by hand.
- Tilt has only 2° margin nodding down (+10° clamp, +12° contact). Keep the firmware clamp.
- The tilt servo lead now crosses the pan joint beside the FPC.
- The fur skin needs a slit/channel down the groove, hip-knuckle openings and bare paw pads.
- Horn size and screw radius (assumed Ø24, r = 7), tooth count (20T vs 21T) and the included screws must be measured on arrival.
- Two servos can draw up to 1.6 A at stall; size the 5 V rail accordingly.
- Heavier than Mirumi (≈263 g vs 155 g).
- Portable power is unresolved. Bench rail only. Not child-ready.

Priced mechanical subtotal **A$23.75** (2 × FS90MG A$7.40 + Adafruit 3351 A$8.95). Springs and fasteners are not priced into it. Nothing purchased. See [`../BOM.csv`](../BOM.csv).
