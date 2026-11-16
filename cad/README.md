# Tomo by DreamMachina (formerly evoKin V.01) — CAD note: Mirumi-style passive spring hug, head pan + tilt

This is the detailed engineering note for the OpenSCAD model in this folder. The project README is one level up. Repository: [github.com/Hewlbern/Tomo](https://github.com/Hewlbern/Tomo).

**CAD only. Unprinted. Grip, hanging, spring life and wear are untested.
Not production, not child-ready, not waterproof. Power is bench-tethered only.
Do not treat these STLs as a fit-check or a print-ready kit.**

Source: [`evokin_v01.scad`](evokin_v01.scad) (internal file names keep the `evokin_` prefix; the servo-clasp V.01 is in git history at `bed94ce`, v4 at `d8b6367`, v3 at `237c37d`).

Pose variables: `yaw` (pan, deg), `tilt` (deg, + = nose down), `armL` / `armR` (opening angle, 0 = closed on the rest stop). STLs are exported at all zeros. Pose a part by hand with `-D yaw=… -D tilt=… -D armL=… -D armR=…`.

## What changed in the two-arms pass (vs b458259)

- **Two short, symmetric arms.** `ARM_PATH_L` runs from the left shoulder round its own side to the front (11 samples, ≈55 mm, ending at azimuth −82.5°, z 48, offset 5.3); `ARM_PATH_R` is the same list mirrored (`psi → −180 − psi`). The old long asymmetric paths (82 / 111 mm) crossed over the belly. `PAD_SEC_L = PAD_SEC_R = [7, 10]`: the pads cover the paw ends, 2.2 mm apart at rest.
- **Thick soft sleeves** (`sleeve_proxy_L/R`, soft goods, not printed): a chain of spheres whose inner face sits on the band's inner face (`SLV_ROOT` 8, `SLV_R` 9), a shoulder cap on the hinge axis (`SLV_CAP_R` 11, z 68–90) and a mitten (`MIT_R` 10.5, 3 mm forward). The mittens are cut flat at x = ±`SLV_MEET` (0.75) so the two never overlap. Body egg subtracted.
- **Centre groove**, 5.9° from vertical, floor 2.5 mm (z 33) to 4 mm (z 64) under the skin at azimuth −90°; capsule t −12…42; test objects centred at `G_MIDT` 15 (z ≈ 48). Constants from `scripts/groove_geo.py`.
- **Stops / spring:** `ARM_OPEN` 30 → 60 (the knuckle relief grows with it), `SPRING_PRE` 50 → 30, so the open stop is at the 90° catalogue rating.
- Mass ≈185 g with battery (191 g before).

## What changed in the lighter Tomo / Mirumi-look pass (vs 6ad85c3)

- **Mass ≈191 g with battery** (was ≈334 g; ASSUMED print profiles, see `results/metrics_v01.json` → `mass.budget_before_after` and the README table).
- **Lightening windows** (`scripts/lighten_shells.py`, run once by `build_stl.sh` after export): Ø14 holes on a 17.5 mm hex pattern, 3.5 mm land, kept only where the shell is plain 2.4 mm wall (within 1.5 % of a revolved plain shell), not below z 12 and not in the face zone (|x| < 24, z < 128). torso_front 14, torso_back 12, head_front 7, head_back 10 windows (11.5–19.6 % of each shell's volume). The posed head copies in `check/` get the same windows so the sweep's transform check still matches. Windows list: `results/lightening.json`. Not idempotent: re-export before re-running.
- **Arms** thinner: `ARM_RS` 3.0 (was 3.5), `ARM_HW` 4, root 3.5 / tip 3.0; the band is offset inward by `ARM_THIN` so the inner face (pad contact, grip geometry) is unchanged.
- **Face**: Pi-camera block and Ø21.6 bezel seats removed. Camera pod at the nose (`nose_z` 110, lens 0.5 mm behind a Ø3.5 window, pocket open to the inside, FPC exit on top, 45° chamfer on the pod's inner lower edge so it clears the collar until +13.5° of nod). Ø5 safety-eye shank holes at x ±10.5, z 114. `bezel` and `shutter` are no longer exported.
- **Speaker**: Adafruit 3923 (30 × 5 × 20 envelope) in a printed frame on the inside of `torso_back` at (0, 38, 64), 5 × 3 grid of Ø2.2 grille holes; the 3351 bosses and front grille are gone.
- **Servos**: Feetech FS90 in both seats (same case as the FS90MG drawing per the Feetech spec sheet; 21T spline). Seat geometry unchanged.
- The egg (R 46, ZEQ 58, H 148, n 3.4) is unchanged: at H 145 / n 3.6 the turret already clears the dome by −0.02 mm, so it cannot be lowered with this neck stack.

## What changed in the Mirumi-proportion pass (vs 1b048e5)

- **One egg body.** `torso_front/back` and `head_front/back` are now cut from one egg of revolution (`begg`): R 46 at z = 58, ellipse below, superellipse n = 3.4 above, top at z = 148. The face cap is split off by a **seam sphere** centred at (0, 0, 119) on the tilt-axis line, radius √(r(101)² + 18²) ≈ 48.3 mm, meeting the skin at z ≈ 101 with a 2 × 1.5 mm gap. Because the egg is round in plan and the sphere is centred near the tilt axis, the cap pans and tilts inside the body.
- **Shoulder hinges** replace the hip hinges (z 22–38 → knuckle z 70–86). The **hip caps are gone**: the M3 pin is thread-formed into the ear and spigot, with a washer and nyloc under the knuckle, so the arm band can leave the knuckle downwards.
- *(superseded by the two-arms pass)* **Long asymmetric arms** built as "path bands": hulls of sphere pairs (r 3.5, ±5 mm across the path; r 4 at the root, 3.5 at the tip) placed along an azimuth/height path (`ARM_PATH_L/R`) at an offset off the skin (8.5 mm, 6.5 mm at the handle crossing). The left arm crosses the chest high (C_L, z ≈ 57) and ends low on the far side; the right arm drops down its own flank and sweeps under the belly (C_R, z ≈ 26). TPU sleeves (`paw_pad_L/R`) cover the crossing sections.
- *(superseded)* **Diagonal off-centre groove**, 35° from vertical, floor 7 mm under the skin at both crossings.
- Spring preload 35° → **50°**, open stop 40° → **30°**. Camera 4 mm forward (y −24). Upper head seam bosses moved to x ±27, z 136; the tilt-hub key pocket is cut through the head_back shell.

## What changed vs the servo clasp (bed94ce)

- **Arm servos removed.** Shoulder pods in `torso_back`, `shoulder_bracket_L/R`, arm hubs, arm-servo and arm-horn dummies are gone.
- **Passive hug arms** on vertical sprung hinges (now at the shoulders, see above).
- **Head tilt.** New `neck_turret` (rides the yaw journal, carries the tilt servo) and `tilt_hub`; `head_back` / `head_front` changed. Servo count stays at two.
- Reference module `grip_rod(d, h = 50)` (Ø12.5 test rod upright on the groove floor, `stl/reference/grip_rod.stl`).

### Shoulder hinge (each side, mirrored)

| Item | Value |
|---|---|
| Axis | vertical (z), x = ±44.58, y = −31.21 (azimuth 35° forward of the side, 54.4 mm from the centre = skin at z 78 + 8.5) |
| Arm knuckle | Ø16, z 70–86; Ø3.4 running bore for the M3 pin; Ø11 spring recess; arm-side leg slot; relief sector in the top (stop lug travel 0–60°) |
| Ear | moulded into `torso_front`, z 86.4–92.4 (6 mm), tied back into the shell by a rear post; Ø2.5 pilot for the thread-formed pin; **Ø5.9 spigot** down into the spring (spring ID 7.1 free); **stop lug** 24° wide, r 5.7–7.7, 2.6 mm deep |
| Pin | M3 × 30, thread-formed into the ear and spigot; M3 washer (Ø7.2 seat) and nyloc under the knuckle; snug, not clamped |
| Spring | music wire 0.048 in (1.22 mm), 3/8 in OD, 90° legs (trim to ~6 mm); Grainger 3HPG6 (LH, left arm) / 3HPD1 (RH, right arm); 2.679 lbf·in = 302.7 N·mm at 90° → **3.363 N·mm/°** |
| Preload / travel | 30° at the closed stop (100.9 N·mm), 90° at the 60° open stop (302.7 N·mm = the catalogue rating, no margin; bending stress ≈1.87 GPa vs ≈1.86 GPa at the rating; ≈45 N on the lug face) |
| Stops | sweep: closed stop engages at −0.5°, open at 30.5° |
| Clearances | knuckle ↔ ear 0.4 mm axial; arm ↔ shell 0.4 mm in travel (0 at the stops, where the lug touches); closed pad ↔ shell 0.28 mm; left ↔ right arm ≥ 5.14 mm with both at the same angle, 46.9 mm (L closed / R open), 46.4 mm (L open / R closed); lowest arm point z 41.8 |

### Belly groove

| Item | Value |
|---|---|
| Shape | capsule of R8 spheres along the floor line, t = −12…42 mm (≈ z 21…75), 2.4 mm liner inside the shell |
| Floor line | from (0, −38.8, 32.9) (bottom, 2.5 mm below the skin) to (0, −42.0, 64.0) (top, 4 mm below) at azimuth −90°; **5.9° from vertical**, so a handle upright runs up the belly between the paws. Constants in `scripts/groove_geo.py` |
| Clearance | Ø12.5 reference rod touches the floor only; rod ↔ speaker 0 mm³, ↔ Pi 0 mm³; torso_front ↔ speaker 0 mm³ |
| Objects | round Ø10–15; flat strap 25 × 2.5 laid along the groove line, all centred at z ≈ 48 |

### Grip (catalogue rate, not measured)

The two paws close on the handle from either side. Pad force = spring torque ÷ perpendicular lever from the hinge axis to the deepest pad contact.

| Object | L opens | L torque / lever | L pad | R opens | R torque / lever | R pad | Total | Into groove |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ø10 | 3.22° | 111.7 N·mm / 39.4 mm | 2.83 N | 3.22° | 111.7 / 39.6 | 2.82 N | 5.65 N | 3.61 N |
| Ø12.5 | 6.13° | 121.5 / 40.4 | 3.01 N | 6.13° | 121.5 / 40.6 | 3.00 N | 6.00 N | 3.83 N |
| Ø15 | 8.98° | 131.1 / 41.0 | 3.20 N | 8.98° | 131.1 / 41.0 | 3.20 N | 6.39 N | 3.99 N |
| Flat 25 × 2.5 | 5.01° | 117.7 / 32.0 | 3.68 N | 5.01° | 117.7 / 32.0 | 3.68 N | 7.36 N | 7.36 N |

The rigid arm stays ≈1.40–1.46 mm clear of each object; the 1.5 mm TPU pad makes the contact (the rigid spine alone would open only 1.1° / 4.1° / 6.9° on Ø10 / 12.5 / 15). Holding the arms fully open takes ≈7.7 N at each paw. Open (60°): pads ↔ belly 29.0 / 29.1 mm. Loading: a Ø15 × 50 rod brought in on straight lines perpendicular to its axis reaches the groove floor without touching the rigid arms, pads or shell for every approach within ±30° of the groove normal (not at ±45° or wider); the soft sleeves are not squashed on the way in. Until this pass the check iterated over an empty range (`np.arange` with the wrong step sign) and always passed; with the old 30° stop there is no clear straight path.

**Clinging.** Mass ≈174 g (no battery) / 185 g with the 400 mAh cell, COM (−0.8, −2.4, 72.2) with battery, ≈46 mm from the handle axis. *Seated on the bag* (Mirumi's pose): the bag carries the weight and the hug only resists toppling; at 90° of lean the hug moment is 2.41× (2.35× with battery) the toppling moment. *Free hang* from a vertical handle: slip is held by friction only, 2 × 6.0 N × μ 0.5 (assumed) → safety factor 3.5 (3.3 with the battery).

### Head tilt

| Item | Value |
|---|---|
| Axis | along x through y = 6, z = 119 (+ = nose down) |
| Servo | Feetech FS90 (FS90MG-drawing case), case top at x = −22, spline pointing −x, screwed by its tabs to a cradle plate on the turret (x −17.8…−14.8) |
| Hub | `tilt_hub`: Ø18 × 2.5 disc on the horn (2 × M2 at r = 7, assumed), 10 × 10 key into a pocket in `head_back` (cut through the shell; the fur covers it) |
| Idler | turret column at x 24–27 with an M3 thread-forming pivot screw into a boss on `head_back` |
| Turret | `neck_turret` carries the skirt, cone, coupler slot, retainer pilots and pan-stop lug |
| Face cap | split from the egg by the seam sphere (z ≈ 101 at the skin); lower seam bosses at x ±32, z 106; upper at x ±27, z 136; camera at y −24 |
| Range | firmware ±10°; first contact **+16.5°** (neck_turret ↔ head_front) and **−23.5°** (yaw_collar ↔ head_back). At ±12°: turret 0.6 mm, collar ≥ 3.5 mm, camera ↔ tilt servo ≥ 8.9 mm |
| Load | head ≈49.5 g, COM 9.3 mm from the axis: 0.046 kg·cm = 2.1 % of stall |
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

- **Speaker:** Adafruit **3923** mini oval, **8 Ω 1 W**, 30 × 20 × 5 mm, 3 g, Core **A$4.80** (ADA3923). Printed frame on the inside of `torso_back` at (0, 38, 64), firing through a 5 × 3 grid of Ø2.2 holes (the fur is acoustically open). The MAX98357A can put ≈1.4 W into 8 Ω at 5 V, so keep its gain low. The 25 g Adafruit 3351 and its front grille are retired.
- **Amp:** Adafruit 3006 MAX98357A, pocket 19.4 × 17.8 × 3.0 plus 8 mm headroom for the post-2024 terminal block, on the +y face of the tray spine. Two M2 pilots at an **assumed** 15 × 13 span — measure the board.
- **Mic:** Adafruit 3421, 16.7 × 12.7 × 1.8, bottom-ported, pocket aligned to the Ø2.4 shell hole at (18, front, 80).
- **Ribbon:** loop bay r = 14 mm (π·14 ≈ 44 mm extra vs the ≥ 9.4 mm requirement), slot 17 × 2.5 mm for a 15 × 1 mm FPC. Path: camera → loop (head) → turret deck slot at x = 14 → +x side of the Ø34 bore → torso duct → Pi CSI.
- **Pi:** y-envelope 8.5 mm (v2’s 5 mm was tight if a header is used); a XIAO ESP32S3 Sense fits easily. **Camera:** ASSUMED 8.5 × 6 × 8.5 module (XIAO Sense OV3660/OV5640) in the nose pod at z 110 on a long 24-pin FPC.

## Tray tabs

10 × 3 × 10 mm tabs at **x = ±29, z = 23** (v3: ±34) sit in 10.6 × 3.6 × 10.6 mm pockets (0.3 mm per side) in 14 mm ribs. They moved inboard and down in v4 to clear the (now removed) shoulder pods. The tab is retained over its outer ~5 mm only, where the rib is clear of the spine relief; watch for rattle on the first print.

## Assembly order (so the pilots are reachable)

1. **Shoulders:** spring into the knuckle recess (arm leg in its slot); knuckle under the ear with the spring over the spigot; wind 30° and hook the torso leg; M3 × 30 pin down through the ear (thread-forming), washer and nyloc under the knuckle, snug. Stretch the TPU sleeves onto the crossings.
2. **Tray** into the torso pockets; close the torso shells on the registration lip (M2.5 front → back).
3. **Head pan:** FS90 into the collar hangers from below; collar onto the torso. From above, through the Ø34 bore: horn, coupler, longer M2.5 horn screw; thrust washer on the journal. Lower the `neck_turret`; retainers from the side into its skirt.
4. **Head tilt:** tilt FS90 to the turret cradle (tab self-tappers). Centre it, horn on, `tilt_hub` on the horn (2 × M2). Hang `head_back` on the hub key and the M3 idler screw; push the safety eyes through `head_front` and fit their washers, seat the camera in the nose pod, then close `head_front` (M2.5, nylon).

## Test coupon

`../stl/coupon.stl`: one plate with the journal + skirt (0.35 mm radial) + 0.8 mm washer, a 10 mm tab in a 10.6 mm pocket, and an FS90/FS90MG shelf with 27.7 mm span / 1.7 mm pilots. Print this first if you print at all. A passing coupon is **not** a full fit-check.

## Parts that changed vs the servo clasp (bed94ce)

**New:** `neck_turret`, `tilt_hub`, `paw_pad_L/R` (`hip_cap_L/R` were added in 1b048e5 and removed again in the proportion pass); reference `dummy_servo_tilt`, `dummy_horn_tilt`, `grip_rod`.

**Changed — reprint:** `torso_front` (egg, diagonal groove, shoulder ears), `torso_back` (egg, pods removed), `head_back`, `head_front` (face cap), `arm_L`, `arm_R`.

**Removed:** `shoulder_bracket_L/R`, `dummy_servo_arm_L/R`, `dummy_horn_arm_L/R`.

**Unchanged:** `tray`, `yaw_collar`, `yaw_coupler`, `yaw_retainer_A/B`, `yaw_thrust_washer`, `coupon` (`bezel` / `shutter` dropped in the lighter pass). Per-file volumes: `results/metrics_v01.json` → `changed_vs_servo_clasp_bed94ce`.

## Rebuild / audit

```bash
# from the repository root
EXPORT_CHECK=1 bash scripts/build_stl.sh   # needs OpenSCAD 2021.01+; posed copies go to check/
python3 scripts/sim_v01.py                 # sweep + hug checks, 537 poses, several minutes
python3 scripts/fit_audit.py
python3 scripts/metrics_v01.py
python3 scripts/validation_summary.py
python3 scripts/render_v01.py
# or: bash scripts/run_all.sh
```

## Residual blockers

- Nothing here has been printed or assembled. The audit is CAD measurements on exported STLs (27/27 fit-audit rows, 0 rigid overlaps in a 537-pose sweep).
- Grip forces come from the catalogue spring rate with no hinge friction; real pads, fur and friction will change them. Spring price on Raptor Supplies AU is inconsistent (A$16.98 vs ≈A$108 per 6-pack); confirm the part and winding hand before ordering.
- The pads close to a soft ≈3 N pinch per paw; the arms open by hand.
- Fully open, the springs sit exactly at their 90° rating. A Ø10 handle gets only 3.2° of follow-through (≈2 mm of squash at the paw).
- Free hanging from a handle rolls the body ≈35° until the COM is under the handle; the seated Mirumi pose is the intended one.
- Tilt margin is 3.5° nodding down (+10° clamp, +13.5° contact: the camera pod on the collar). Keep the firmware clamp.
- The tilt servo lead now crosses the pan joint beside the FPC.
- The fur skin needs a vertical channel or slit down the centre groove, two stuffed arm sleeves with pad slots in the mittens, shoulder-knuckle openings, bare TPU pads and a pile-covered seam round the face cap.
- Horn size and screw radius (assumed Ø24, r = 7), tooth count (20T vs 21T) and the included screws must be measured on arrival.
- Two FS90s can draw ≈1.4 A at stall, more than the 400 mAh cell (0.8 A) or the U3V16F5 (≈1 A) supply: move one joint at a time (firmware default) and set the INA219 trip below ≈0.6 A.
- Heavier than Mirumi (≈185 g with battery vs ≈135–155 g; target was 160–180 g) and taller (148 mm egg, ≈160 mm over the pile, vs ≈143 mm). Next ≈5–11 g: sub-micro servos with new seats.
- Windowed 2.4 mm shells at a 1-perimeter profile are unprinted and undropped.
- Portable power (400 mAh + U3V16F5) is planned, untested. Not child-ready.

Priced mechanical + power subtotal **A$21.75** (2 × FS90 A$5.70 + Adafruit 3923 A$4.80 + 400 mAh LiPo A$5.55). Springs and fasteners are not priced into it. Nothing purchased. See [`../BOM.csv`](../BOM.csv).
