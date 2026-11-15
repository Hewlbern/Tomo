# evoKin V.01 CAD — clasp around the middle (forward-facing arms, motorised head pan)

This is the detailed engineering note for the OpenSCAD model in this folder. The project README is one level up.


**CAD only. Unprinted. Motion, grip force, fail-safe behaviour and wear are untested.
Not production, not child-ready, not waterproof. Power is bench-tethered only.
Do not treat these STLs as a fit-check or a print-ready kit.**

Source: [`evokin_v01.scad`](evokin_v01.scad) (renamed from `critter_v4.scad`; v4 is in git history at `d8b6367`, v3 at `237c37d`).

## What changed vs v4 (V.01: clasp around the middle)

- **Forearm blades.** Each arm is now an L. The upper arm runs forward outside the fur (x 52.5 … 60.5) to an elbow, then a forearm blade runs inward along −x across the front of the belly to **18 mm past the midline** (`FORE_TIP`). Blade cross-section: 10 mm radial (r 66 … 76 from the shoulder axis, `FORE_R = 71`, `FORE_DR = 10`) × 8 mm tangential (`FORE_T`), 2.5 mm edge radius. The elbow disc is no thicker than the blade, so a pen lies flat along it. Toe bumps removed.
- **Scissor clasp.** Both blades sit at the same radius from the same axis, so they overlap 36 mm across x −18 … +18. With the left arm above the right, closing the angle difference Δ = armL − armR squeezes anything between the blades. Rigid gap ≈ (Δ − 6.62°) / 0.848 mm: **0.98 mm at the Δ = 7.5° interlock**, 25 mm at Δ ≈ 27.8°, up to 33 mm in travel. Blades touch at Δ ≈ 6.5°.
- **Grip force** (datasheet stall 2.2 kg·cm at 6 V, both servos stalled, not measured): 3.27 N at r = 66, **3.04 N at r = 71**, 2.84 N at r = 76; 2.92 N at the pen pose after the lower arm's own weight. Suggested continuous hold ≤ 50 % (≈1.5 N).
- **Interlock and clamps.** Firmware must keep **armL − armR ≥ 7.5°**. Software clamp is now **−45° … +30°** per arm: −45° keeps the forearm 4.5 mm off the desk; +30° keeps the blade top (z 100.5) under the eye bezels (z 106.5); first head contact is at +42°. STLs are exported at **armL −15°, armR −25°** (ARM_REST_L/R).
- **Compliance.** The 2 mm fur sleeve on each blade (≈4 mm of pile between them) is the only give. No spring or breakaway part: a breakaway clutch would not fit the 26 mm hub without a new part, and a 4th servo for a hug axis does not fit inside the torso.
- **Servo count unchanged (3).** No new parts or fasteners. Everything else is geometrically identical to v4.
- New reference module `grip_pen(d, len)` for the Ø8 × 140 mm render/test cylinder.

## What changed vs v3 (v4)

- **Arms face forward.** v3 used one clasp servo, a cord drum and return elastics so the paws hugged backward around a strap at +y. v4 drops all of that: **one FS90MG per shoulder, direct drive**, arms swing about a left–right (x) axis at **y = 13, z = 60**. Angle convention: **0° = arm straight forward (−y), + = up**. v4 clamp was −55° … +70° at a −20° rest; V.01 changes it (above).
- **Third FS90MG** (the second arm servo). Head pan servo unchanged.
- **Head pan** unchanged from v3: FS90MG in the `yaw_collar`, coupler blade in a 2.7 mm slot in `head_back`, ±42° software clamp, hard stop ≈ ±47° (sweep confirms collar ↔ head contact at 47.0°). **No tilt**: a tilt axis would need a fourth servo and a gimbal inside the 64 mm head beside the camera and its FPC loop; it does not fit cleanly.
- **Ears:** the model has no ears. The side shapes in earlier renders are the arms. Nothing changed.

### Shoulder (each side, mirrored)

| Item | Value |
|---|---|
| Servo | FS90MG, output axis along x, case top at \|x\| = 42 |
| Pod | moulded into `torso_back`, \|x\| 30 … 46, FS90MG case pocket + 0.3 mm cap rebate, 2 × 2.1 mm cap-screw pilots |
| Cap (`shoulder_bracket_L/R`) | 4 mm plate, 43 × 16.8, servo tabs screw into it (1.7 mm pilots, blind) on the bench; boss passes through a Ø12.8 hole; 2 × M2.5 (2.8 mm) into the pod at ±19.3 |
| Horn | assumed Ø24 × 2.0 disc/star on the boss, x 46.3 … 48.3 |
| Arm hub | Ø26, x 46.6 … 52.6; horn pocket to 48.3; Ø5.5 spline pocket to 50.8; Ø3.2 through-hole for an **M2.5×12** axial screw, Ø5.5 counterbore; 2 × Ø1.7 horn pilots at an **assumed** r = 7 |
| Upper arm + forearm (V.01) | upper arm x 52.5 … 60.5 to the elbow at r ≈ 64; forearm blade r 66 … 76, 8 mm thick, from the elbow to x = ∓18 (past the midline) |
| Clearances (V.01) | hub ↔ cap face 0.6 mm; arm ↔ shell min 0.6 mm in travel; arm ↔ head 17.8 mm; forearm ≥ 4.5 mm off the desk |
| Load (V.01) | arm print 21.0 g (+4 g assumed sleeve, 1 g horn), gravity torque 0.092 kg·cm = 4.2 % of stall; blade force at stall ≈ 3.0 N at r = 71 |

The shoulder bearing is the servo's own output bearing: the arm is cantilevered off the spline with no outboard support. Fine at 4 % of stall statically, but a child levering the arm loads the servo gears directly. There is **no breakaway**.

### Other part changes

- `torso_back`: pods; seam fasteners moved to (±24, z 12) and (±30, z 79) to clear the pods.
- `torso_front`: matching fastener holes; side vents moved to x ±(14 … 22).
- `tray`: clasp-servo shelf removed. Tabs at **x = ±29, z = 23** in 10.6 mm pockets in a 14 × 10 × 12 rib; widened spine relief.
- `fur_proxy_torso`: r = 15 openings round each shoulder axis. `sleeve_proxy_L/R`: follow the new arms.
- Removed: `clasp_drum`, paw-pad templates, `strap_env`, clasp servo/horn dummies. New dummies: `dummy_servo_arm_L/R`, `dummy_horn_arm_L/R`.
- Unchanged geometry: head, yaw stack, bezel, shutter.

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
- Servo-tab self-tappers (or M2): **pilot 1.7** in the yaw hanger and the shoulder caps, through the servo’s Ø2.2 tab holes.
- Yaw retainers: **M2 clearance 2.3** in the retainer, **pilot 1.7** in the head skirt.

## Yaw stack

- Journal OD 44.0, skirt ID 44.7, **0.35 mm** radial running clearance.
- Blade 2.0 mm in a 2.7 mm slot, **0.35 mm** per side. Backlash at r = 8 mm ≈ **5.0°** total. Software yaw clamp **±42°** so the ~47° hard stop is not a running face.
- Justification: 0.35 mm is the tight end of the requested 0.35–0.4 mm FDM running-fit band. v2’s 0.30 mm is too tight once typical hole shrinkage and elephant-foot are included. 0.40 mm would add more yaw backlash than needed. Revisit after the first article.
- Separate **yaw_thrust_washer** (0.8 mm, ID 35, OD 43), printed flat, no supports. Journal top 97.4, washer 97.4–98.2, designed **0.30 mm** axial gap, head cone at 98.5.
- `head_back` still prints skirt-down, but the underside is a **30°-from-vertical cone**, so a 35° support threshold should not put supports on a flat thrust face. The flat thrust is the washer.
- Retainer axial play **0.35 mm**. Retainer OD is 48 mm so the M2 holes at r = 23.8 go through both the retainer and the skirt.
- The official tab holes sit at r = 16.4 and 11.3, **inside** a Ø34 cylinder, so the collar bore is **stepped**: boss clearance in the flange, Ø34 from the boss top (z = 88.3) up, for horn / coupler / ribbon installation from above.

## Electronics seats

- **Speaker:** Adafruit **3351** Mono Enclosed, **3 W 4 Ω**, 70 × 30 × 17 mm, holes Ø3.4 on 63 × 24, Core **A$8.95**. This is the honest match for MAX98357A (3.2 W into 4 Ω at 5 V). The v2 Ø28 placeholder and any 0.5 W 8 Ω mini are retired. The front grille is now a 66 × 26 window.
- **Amp:** Adafruit 3006 MAX98357A, pocket 19.4 × 17.8 × 3.0 plus 8 mm headroom for the post-2024 terminal block, on the +y face of the tray spine. Two M2 pilots at an **assumed** 15 × 13 span — measure the board.
- **Mic:** Adafruit 3421, 16.7 × 12.7 × 1.8, bottom-ported, pocket aligned to the Ø2.4 shell hole at (18, front, 80).
- **Ribbon:** loop bay r = 14 mm (π·14 ≈ 44 mm extra vs the ≥ 9.4 mm requirement), slot 17 × 2.5 mm for a 15 × 1 mm FPC. Path: camera → loop → floor slot at x = 14 → +x side of the Ø34 bore → torso duct → Pi CSI.
- **Pi:** y-envelope 8.5 mm (v2’s 5 mm was tight if a header is used). Camera is the standard Module 3 (25 × 24 × 11.5), not the Wide.

## Tray tabs

10 × 3 × 10 mm tabs at **x = ±29, z = 23** (v3: ±34) sit in 10.6 × 3.6 × 10.6 mm pockets (0.3 mm per side) in 14 mm ribs. They moved inboard and down to clear the shoulder pods. The tab is retained over its outer ~5 mm only, where the rib is clear of the spine relief; watch for rattle on the first print.

## Assembly order (so the pilots are reachable)

1. **Arm servos:** centre each servo electrically. On the bench, screw the FS90MG tabs to the cap (self-tappers into 1.7 pilots). Drop servo + cap into the pod from outside, cap in its rebate, 2 × M2.5 into the pod. Press the horn on for −20°, screw hub to horn (2 × M2), then the M2.5×12 axial screw through the hub.
2. **Tray** into the torso pockets.
3. **Head pan:** drop the FS90MG into the collar hangers from below; self-tappers from below through the tabs into the 1.7 bosses. Screw the collar onto the torso (M2.5 clearance in the collar, pilots in the torso). From above, through the Ø34 bore: horn, coupler, longer M2.5 horn screw. Drop the thrust washer onto the journal. Lower the head (retainers from the side into 1.7 pilots in the skirt).
4. Close torso and head shells on the registration lip; M2.5 from the front (2.8 clearance) into the back (2.1 pilots).

## Test coupon

`../stl/coupon.stl`: one plate with the journal + skirt (0.35 mm radial) + 0.8 mm washer, a 10 mm tab in a 10.6 mm pocket, and an FS90MG shelf with 27.7 mm span / 1.7 mm pilots. Print this first if you print at all. A passing coupon is **not** a full fit-check.

## Parts that changed vs v4 (V.01)

**Geometrically changed — reprint these:** `arm_L`, `arm_R`. Reference only: `sleeve_proxy_L/R`, posed arm-horn dummies.

**Unchanged:** everything else. Per-file volumes: `results/metrics_v01.json` → `changed_vs_v4`.

## Parts that changed vs v3 (v4)

**Geometrically changed — reprint these:** `torso_front`, `torso_back`, `tray`, `arm_L`, `arm_R`, `shoulder_bracket_L`, `shoulder_bracket_R` (now caps), `coupon` (tiny tab change).

**Removed:** `clasp_drum`, paw-pad templates.

**Unchanged:** `head_front`, `head_back`, `yaw_collar`, `yaw_coupler`, `yaw_retainer_A/B`, `yaw_thrust_washer`, `bezel`, `shutter`.

These STLs are CAD only.

## Rebuild / audit

```bash
# from the repository root
EXPORT_CHECK=1 bash scripts/build_stl.sh   # needs OpenSCAD 2021.01+; posed copies go to check/
python3 scripts/sim_v01.py                 # imposed-motion sweep + clasp checks, ~1,000 poses, ~6 minutes
python3 scripts/fit_audit.py
python3 scripts/metrics_v01.py
python3 scripts/render_v01.py
# or: bash scripts/run_all.sh
```

OpenSCAD 2021.01 or later. Set `OPENSCAD=/path/to/openscad` if it is not on your `PATH`. Pose a single part by hand with `-D armL=<deg> -D armR=<deg> -D yaw=<deg>`.

## Residual blockers

- Nothing here has been printed or assembled. The V.01 audit is CAD measurements on exported STLs (23/23 fit-audit rows, 0 rigid overlaps in a 988-pose sweep).
- The clasp is a deliberate pinch point: it closes to ≈1 mm at ≈3 N. The blade interlock (armL − armR ≥ 7.5°) is firmware only; if it is skipped the blades crash edge-on.
- Large objects (20–25 mm) sit between blade faces meeting at Δ ≈ 23–28°, so they are wedged outward; small objects grip best.
- High wave is gone (arms max +30°), and the right arm can never rise above the left.
- Direct-drive arms: no breakaway; the servo gears take any forced motion. Fail-safe relies on an INA219 trip and a load switch that are not built.
- The arm is cantilevered on the servo's output bearing alone.
- Shoulder pods poke up to 9.6 mm past the nominal 4 mm torso fur envelope; the fur pattern must cover them.
- Horn size and screw radius (assumed Ø24, r = 7), tooth count (20T vs 21T) and the included screws must be measured on arrival.
- Three servos can draw up to 2.4 A together at stall; size the 5 V rail or stagger moves.
- Portable power is unresolved. Bench rail only. Not child-ready.

Priced mechanical subtotal **A$31.15** (3 × FS90MG A$7.40 + Adafruit 3351 A$8.95). Nothing purchased. See [`../BOM.csv`](../BOM.csv).
