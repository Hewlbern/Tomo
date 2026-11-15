# Evokin CAD — v3 (FS90MG seats)

This is the detailed engineering note for the OpenSCAD model in this folder. The project README is one level up.


**CAD only. Unprinted. Motion, grip force, fail-open and wear are untested.
Not production, not child-ready, not waterproof. Power is bench-tethered only.
Do not treat these STLs as a fit-check or a print-ready kit.**

v0, v1 and v2 sources and STLs are untouched. This folder is a new tree.

## What changed vs v2

The v2 fit audit (the v2 fit audit) failed the servo seats, the torso/head seams, the yaw thrust face and retainer holes, the tray tab pockets, and the unmodelled ribbon / speaker / amp / mic seats. v3 redesigns those interfaces around **2× Feetech FS90MG**, using the official drawing (p.5) rather than a generic 9 g envelope.

Arm beams, paws, pulleys, pads, bezels and the shutter are **geometrically unchanged** from v2 (SHA may differ because of vertex order). Brackets change only because the torso screw holes are now 2.8 mm clearance and the cord-channel z moved 0.2 mm with the new drum height.

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

## Drive / clasp angle (recomputed)

Drum xy, r_d = 10.25 and r_q = 8.0 are unchanged from v2, so the travel is unchanged:

- 0–45° arm close = **6.28 mm** of cord = **35.12°** of drum.
- The drum is 1:1 on the FS90MG horn, so the **servo angle is also 35.12°** (38.24° stop-to-stop, −3° to 46°). Well inside 180°.
- `clasp_top` is lowered to **51** (v2 was 55) so that, after the 4.0 mm horn gap, the grooves at 61.7 / 65.3 still straddle the pulley at zq = 63.5. Fleet angle **±1.8°**. Arms and pulleys do not move.

## Seams and fasteners (one scheme)

- Male registration lip on the **back** half, female groove on the **front**, **0.25 mm** FDM clearance.
- **0.40 mm** chamfer on the outer seam edge (bed face when printed seam-down) to give elephant-foot somewhere to go.
- **M2.5: clearance 2.8** in the front / through / accessible half; **pilot 2.1** in the back / receiving half. Optional M2.5 heat-set later: bosses are Ø7.
- Servo-tab self-tappers (or M2): **pilot 1.7** in the printed hanger / shelf, through the servo’s Ø2.2 tab holes.
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
- **Amp:** Adafruit 3006 MAX98357A, pocket 19.4 × 17.8 × 3.0 plus 8 mm headroom for the post-2024 terminal block, on the +y face of the tray spine (clear of the clasp servo). Two M2 pilots at an **assumed** 15 × 13 span — measure the board.
- **Mic:** Adafruit 3421, 16.7 × 12.7 × 1.8, bottom-ported, pocket aligned to the Ø2.4 shell hole at (18, front, 80).
- **Ribbon:** loop bay r = 14 mm (π·14 ≈ 44 mm extra vs the ≥ 9.4 mm requirement), slot 17 × 2.5 mm for a 15 × 1 mm FPC. Path: camera → loop → floor slot at x = 14 → +x side of the Ø34 bore → torso duct → Pi CSI.
- **Pi:** y-envelope 8.5 mm (v2’s 5 mm was tight if a header is used). Camera is the standard Module 3 (25 × 24 × 11.5), not the Wide.

## Tray tabs

10 × 3 × 10 mm tabs at x = ±34 sit in 10.6 × 3.6 × 10.6 mm pockets (0.3 mm per side) in 14 mm ribs centred on the tabs (v2’s rib was centred at ±37 and only held 8.3 mm of the 10 mm tab). A spine relief through the rib lets the 58 mm spine meet the tab without a clash.

## Assembly order (so the pilots are reachable)

1. **Clasp:** drop the FS90MG onto the tray, tabs on the shelf (shelf is *under* the tabs). Drive the self-tappers **from above** through the Ø2.2 tab holes into the 1.7 pilots, *before* the horn and drum go on. Fit the horn, then the drum (Ø3.2 access hole for a longer horn screw). Then slide the tray into the torso pockets and close the shells.
2. **Yaw:** drop the FS90MG into the collar hangers from below; self-tappers from below through the tabs into the 1.7 bosses. Screw the collar onto the torso (M2.5 clearance in the collar, pilots in the torso). From above, through the Ø34 bore: horn, coupler, longer M2.5 horn screw. Drop the thrust washer onto the journal. Lower the head (retainers from the side into 1.7 pilots in the skirt).
3. Close torso and head shells on the registration lip; M2.5 from the front (2.8 clearance) into the back (2.1 pilots).

## Test coupon

`../stl/coupon.stl`: one plate with the journal + skirt (0.35 mm radial) + 0.8 mm washer, a 10 mm tab in a 10.6 mm pocket, and an FS90MG shelf with 27.7 mm span / 1.7 mm pilots. Print this first if you print at all. A passing coupon is **not** a full fit-check.

## Parts that changed vs v2 (odm-print already has v2 slices)

**Geometrically changed — send these if anyone reprints:**

- `torso_front.stl`, `torso_back.stl`
- `tray.stl`
- `yaw_collar.stl`, `yaw_retainer_A.stl`, `yaw_retainer_B.stl`, `yaw_coupler.stl`
- `yaw_thrust_washer.stl` (**new**)
- `head_front.stl`, `head_back.stl`
- `clasp_drum.stl`
- `shoulder_bracket_L.stl`, `shoulder_bracket_R.stl` (screw holes 2.8 mm and a 0.2 mm cord-channel z shift)
- `coupon.stl` (**new**, optional)

**Geometrically unchanged — do not resend:** `arm_L`, `arm_R`, `bezel`, `shutter`, `paw_pad_L/R`, `sleeve_proxy_L/R`, `fur_proxy_torso`, `strap_env`.

These STLs are CAD only. Nothing here has been printed or fit-checked in plastic.

## Rebuild / audit

```bash
# from the repository root
python3 scripts/design_params.py
bash scripts/build_stl.sh          # needs OpenSCAD 2021.01+
python3 scripts/fit_audit.py
python3 scripts/sim_v3.py          # dense imposed-motion sweep, several minutes
python3 scripts/metrics_v3.py
python3 scripts/render_v3.py
```

OpenSCAD 2021.01 or later. Set `OPENSCAD=/path/to/openscad` if it is not on your `PATH`.

## Residual blockers (unchanged honesty)

- Nothing here has been printed or assembled. The v3 audit is CAD measurements on exported STLs.
- Breakaway / fail-open is still a requirement only, not a designed or rated part.
- Portable power is unresolved. Bench rail only.
- Foam pad stiffness is unknown; no grip force is claimed. Contact metrics at 45° / 46° should match v2 (pads and arms unchanged).
- Horn size, tooth count (20T vs 21T), and the included screws must be measured on arrival.
- Not child-ready.

Priced BOM subtotal **A$158.60** (2 × FS90MG A$7.40 + Adafruit 3351 A$8.95 + electronics A$134.85 carried over and not re-priced).
