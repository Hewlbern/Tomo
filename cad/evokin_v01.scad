// SPDX-License-Identifier: MIT
// evoKin V.01 CAD. MIT License, see LICENSE.
// evokin_v01.scad -- BENCH PROTOTYPE CAD. UNPRINTED, MOTION/FORCE UNTESTED.
// Not production, not child-ready, not waterproof, power bench-tethered only.
// V.01 (Nov 2026): MIRUMI-STYLE PASSIVE SPRING HUG, MIRUMI PROPORTIONS (replaces the servo clasp of bed94ce
//   and the hip-hinge layout of 1b048e5).
//  * ONE EGG BODY: head and torso are cut from one egg of revolution (begg); the face is a cap split off by a
//    seam sphere centred on the tilt-axis line, so it pans and tilts inside the egg.
//  * ARMS ARE PASSIVE. Each arm hangs on a vertical hinge at the SHOULDER, just under the face (axis parallel to z
//    through HX,HY; left arm at +x, right mirrored). A music-wire torsion spring (0.048 in / 1.22 mm wire, 3/8 in
//    OD, 90 deg legs; catalogue 3HPG6 LH / 3HPD1 RH, 2.679 lbf.in = 0.303 N.m at 90 deg, i.e. 3.36 N.mm/deg) sits in
//    the knuckle, preloaded SPRING_PRE deg against a printed hard stop, so the arms hug with zero power. The arms
//    are short, thick and symmetric (two-arms pass): each runs from its shoulder round its own side to the front,
//    where the two paws nearly meet in front of the handle without crossing. Open by hand to the ARM_OPEN stop,
//    bring the handle straight in, let go.
//  * BELLY GROOVE: centre R8 channel, near-vertical (5.9 deg), so a bag-handle upright runs up the belly like Mirumi's,
//    for 10-15 mm round handles or a flat strap up to 25 mm; TPU sleeves (paw_pad_L/R) at both arm crossings.
//  * HEAD: pan (FS90MG in the yaw collar) + tilt/nod (FS90MG on a neck_turret that rides the yaw journal; spline on
//    the tilt axis, x direction, through y=TILT_Y z=TILT_Z). 2x FS90MG total; the arm servos are gone.
// History: hip-hinge passive hug = 1b048e5, servo clasp V.01 = bed94ce, v4 = d8b6367, v3 = 237c37d.
// NAMING: arm_L / paw_pad_L = the CRITTER'S OWN LEFT = +x.
// Units mm. Frame: z up, -y = face/front, +y = back.
// Pose variables: yaw (pan, + = turn to its own left / +x, CCW from above), tilt (+ = nod DOWN), armL/armR = arm OPENING
// angle in deg (0 = closed on the rest stop, ARM_OPEN = open stop). STLs export at yaw=0, tilt=0, armL=armR=0.
// openscad -D 'part="arm_L"' -o x.stl evokin_v01.scad
part = "assembly";
yaw = 0;
tilt = 0;     // deg, + = nose down (nod)
armL = 0;     // deg opening, 0 = hugging (rest stop)
armR = 0;
$fn = 56; clr = 0.3;


/* ---- official FS90MG, drawing p.5, all ±0.1 mm (verified from the PDF, not from marketing text) ----
   Body 22.5 x 12.1, case height 22.4, boss top 26.7, overall (spline tip) 30.7,
   tab overall 32.3, hole centres 27.7, holes Ø2.2, spline Ø4.7 20T,
   8.7 = body-end (spline side) to spline axis. Centre offset s_off = 22.5/2 - 8.7 = 2.55.
   Tab underside is the 18.2 mark => tab thickness 22.4-18.2 = 4.2, top flush with case.
   15.7 is a lower-body step; not used for the seat.
   DISCREPANCIES / FLAGS (see README):
   - Spec text 6-1 is 22.5×12.1×26.7 (C = boss top), not the 30.7 overall.
   - 6-9 and the drawing say 20T / Ø4.7; Feetech product pages and wiki say 21T. Measure on arrival.
   - p.6 is a blank "No Accessories" sheet; product pages usually include POM horns. Horn size is
     unspecified. Envelope below is a typical 2.0 mm disc + 4-arm star, OD 24. Measure on arrival.
   - Included horn screw is listed as M2.5×4 (6-13). Too short for horn (2 mm) + yaw coupler (1.6 mm)
     + thread. Buy a longer M2.5 (e.g. 8–10 mm) and confirm on arrival. The v4 arm hubs need M2.5×12.
   - p.3 no-load speed "0.87 sec/60° at 4.8 V" is almost certainly a missing zero (0.087).
   - Stall 2.2 kg·cm / 800 mA at 6 V. Bench rail only; budget the 800 mA conservatively. */
FS_BODY=[22.5,12.1,22.4];
FS_S_OFF=22.5/2-8.7;          // 2.55; body centre at -s_off, spline at 0
FS_TAB=32.3; FS_HOLE_SPAN=27.7; FS_HOLE_D=2.2;
FS_TAB_T=22.4-18.2;           // 4.2
FS_TAB_DZ=FS_TAB_T;           // underside is 4.2 below case top
FS_BOSS_H=26.7-22.4;          // 4.3
FS_BOSS_D=11.8;               // typical boss OD (not dimensioned on p.5); seat uses +1 mm
FS_SPLINE_H=30.7-26.7;        // 4.0 above boss
FS_SPLINE_D=4.7;
HORN_T=2.0; HORN_OD=24.0;     // ASSUMED typical envelope; not on the drawing

/* ---- fastener scheme (one scheme, used everywhere printed-to-printed) ----
   M2.5: clearance 2.8 in the accessible / front / through half, pilot 2.1 in the receiving half.
   Optional M2.5 heat-set later: receiving bosses are Ø7, long enough for a standard M2.5 brass insert.
   Servo tab self-tappers (or M2): pilot 1.7 in the printed hanger/shelf, through the servo's Ø2.2 tab holes.
   Retainer M2: clearance 2.3 in the retainer, pilot 1.7 in the neck_turret skirt. */
M25_CLR=2.8; M25_PIL=2.1; M2_CLR=2.3; M2_PIL=1.7; SERVO_PIL=1.7;

/* ---- running fits (FDM, 0.2 mm layers) ----
   Journal radial and coupler-blade side clearance are 0.35 mm, the tight end of the requested
   0.35–0.4 mm FDM running-fit band. 0.30 mm (v2) is too tight once typical hole shrinkage and
   elephant-foot are included. 0.40 mm would add more yaw backlash than needed. At the blade,
   0.35 mm/side at r=8 mm is atan(0.35/8)*2 ≈ 5.0° total backlash; software yaw clamp ±42° so
   the 47° hard stop is not relied on as a running face. Revisit after the first article. */
JRN_RAD=0.35; BLADE_CLR=0.35; AXIAL_GAP=0.30; AXIAL_PLAY=0.35;
SEAM_LIP_CLR=0.25; SEAM_CHAMFER=0.40;
/* ---- envelopes ---- */
/* MIRUMI PROPORTIONS (Nov 2026): one egg/bean of revolution for the whole body (no separate head egg).
   Radius R_EGG at the equator ZEQ; lower half an ellipse (semi-axis ZEQ), upper half a superellipse (exponent
   N_UP, semi-axis H_EGG-ZEQ) so the dome stays blunt. The face is a CAP cut off by the seam sphere (centre on the
   tilt axis line, radius SEAM_R): it pans and tilts inside the egg, and because the egg is round in plan the cap
   skin matches the body at every pan angle. tcut / hcut stay as the internal yaw-stack datums. */
R_EGG=46; ZEQ=58; H_EGG=148; N_UP=3.4; tw=2.4; tcut=85; hcut=98;
// The printed shell stays 148 mm tall: neck_turret reaches z ≈ 139.9 and the tilt-servo tabs z ≈ 137.7,
// so a shorter crown would collide. A lower, rounder look is done in soft goods (mid-body padding, shorter pile, tucked feet).
TD=2*R_EGG; HD=2*R_EGG;
sb=FS_BODY; s_off=FS_S_OFF; s_tab=FS_TAB; s_tab_t=FS_TAB_T; s_tab_dz=FS_TAB_DZ; s_boss=[FS_BOSS_D,FS_BOSS_H];
yaw_top=84;
/* ---- V.01 passive hug arms ----
   Body egg at height z: half-width ea(z), half-depth eb(z). The arm band follows the egg at offset O_ARM
   (band centre line) from the hinge at PSI_H to PSI_P, then the paw curls in to PAW_TIP.
   Band = hull chain of spheres r=ARM_RS at z=ARM_ZT (top) and z=ARM_ZB (bottom): band z 22..38. */
function eggr(z,o=0)= z<ZEQ ? (R_EGG-o)*sqrt(max(0,1-pow((z-ZEQ)/(ZEQ-o),2)))
                            : (R_EGG-o)*pow(max(0,1-pow(abs(z-ZEQ)/(H_EGG-ZEQ-o),N_UP)),1/N_UP);
function eggdr(z)=(eggr(z+0.2)-eggr(z-0.2))/0.4;
function on_egg(psi,z,off=0)=[(eggr(z)+off)*cos(psi),(eggr(z)+off)*sin(psi),z];
/* ---- SHOULDER hinges: vertical axes just under the face (was the hip, z 22..38).
   Left arm (critter's own left, +x) hinge at azimuth PSI_H, right arm mirrored (azimuth 180-PSI_H). ---- */
ARM_RS=3.0; ARM_HW=4;                                  // lighter Tomo: band = pairs of r3 spheres ±4 across the path (≈6 x 14 section, was 7 x 17)
ARM_THIN=3.5-ARM_RS;                                   // path offsets are reduced by this so the band's INNER face stays where the r3.5 band had it
KN_R=8; KN_Z0=70; KN_Z1=86;                           // knuckle Ø16, z 70..86 (shoulder, just under the face seam; ear top 92.4 clears the nodding cap rim)
PSI_H=-35; O_ARM=8.5;
R_AX=eggr((KN_Z0+KN_Z1)/2)+O_ARM;                     // 54.4
HX=R_AX*cos(PSI_H); HY=R_AX*sin(PSI_H);               // hinge axis (44.4, -31.1) for the left arm
EAR_T=6; EAR_GAP=0.4;                                 // ear (moulded into torso_front) z 86.4..92.4; NO lower cap: the knuckle
                                                      // hangs on an M3x30 pin thread-formed into the ear (pilot PIN_D), nyloc +
                                                      // washer under the knuckle, so the arm band can leave the knuckle downwards
PIN_D=2.5; PIN_RUN=3.4;                               // M3 pin: 2.5 thread-forming pilot in the ear/spigot, 3.4 running in the knuckle
REC_D=11; REC_Z0=KN_Z0+8;                             // spring recess Ø11 from KN_Z0+8 to the knuckle top
SPIG_D=5.9; SPIG_Z0=KN_Z0+8.4;                        // arbor spigot on the upper ear (spring ID 7.09 free)
ARM_OPEN=60;                                          // printed open stop (deg); thick-arm pass: 60 (was 30, which left no straight path in for a handle)
SPRING_PRE=30;                                        // spring preload at the rest stop (deg); 90 deg wind-up at the 60 deg open stop (= catalogue rating)
SPRING_K=0.3027/90*1000;                              // N.mm per deg (3HPG6/3HPD1 catalogue: 2.679 lbf.in at 90 deg)
LUG_A=60; LUG_W=24; LUG_R=[5.7,7.7]; LUG_Z0=KN_Z0+13.8;   // stop lug on the upper ear, hangs into the knuckle relief
REL_R=[5.3,8.6]; REL_Z0=KN_Z0+13.4;                   // relief sector in the knuckle top: [LUG_A-LUG_W/2-ARM_OPEN, LUG_A+LUG_W/2]
PAD_T=1.5;                                            // TPU pad thickness
/* ---- arm paths [azimuth, z, offset of the band centre from the skin]. TWO SYMMETRIC, SHORT, Mirumi-style arms
   (two-arms pass; the v0.1 asymmetric arms crossed each other over the belly). Each runs from its shoulder hinge
   forward and down round its own side of the body to the front, where the paws nearly meet in front of a
   near-vertical handle lying in the centre belly groove. The RIGHT path is the left path mirrored (psi -> -180-psi).
   Offset 8.5 clears 4 mm fur; 5.3 at the paws (pads ≈0.3 mm off the skin at rest). ---- */
// Mirumi polish pass: the arms run nearly level round the upper chest, so the paws meet at z ≈ 70, just under the
// face (were z 48, mid-body).
ARM_PATH_L=[[PSI_H,78,O_ARM],[-41,77.5,8.5],[-47,77,8.5],[-53,76,8.5],[-58,75,8.5],[-63,74,8.5],[-68,73,8],
            [-74,71.5,6.5],[-78,70.5,5.3],[-81,70,5.3],[-82.5,70,5.3]];
ARM_PATH_R=[for(p=ARM_PATH_L) [-180-p[0],p[1],p[2]]];
PAD_SEC_L=[7,10]; PAD_SEC_R=[7,10];                    // path sections covered by the TPU pads (the paws, in front of the handle)
/* ---- CENTRE belly groove (two-arms pass): R8 channel down the front centre (azimuth -90) for a near-vertical handle;
   floor line from G_FR (bottom, z 48.3, 2.5 mm below the skin) to G_FL (top, z 80, 4 mm below), 1.7 deg from vertical
   (Mirumi polish pass: raised from z 33..64 with the hug, paws now meet at z ≈ 70);
   shallow so a Ø10 handle stands proud enough for the paws to reach round it.
   G_U = line direction (up), G_N = outward groove normal. R8 capsule from t=G_T0 to G_T1 along the line, wall GW.
   Constants from scripts/groove_geo.py. ---- */
GR=8; GW=2.4;
G_FR=[0.0000,-42.8349,48.3438]; G_FL=[0.0000,-41.8878,79.9301];
G_U=[0.0000,0.0300,0.9996]; G_N=[0.0000,-0.9996,0.0300]; G_T0=-12; G_T1=46; G_MIDT=22;   // T1 46: the channel runs on up to the torso rim (z ≈ 94) so a straight handle clears the shell above the paws
function gline(t)=G_FR+t*G_U;
/* ---- head tilt (nod): spline axis along x through (TILT_Y, TILT_Z); FS90MG case top at x=-TS_X, spline pointing -x ---- */
TILT_Y=6; TILT_Z=119; TS_X=22;
TILT_SOFT=[-10,10];                                    // firmware clamp (deg), see results/summary_sweep.json for the first contact
pi=[65,8.5,30]; pi_holes=[58,23]; pi_z=43;           // 8.5 mm y-envelope allows a header
// Lighter Tomo / Mirumi look: small 8 mm safety eyes set lower and closer; the camera (XIAO ESP32S3 Sense OV3660/OV5640 module on a
// long 24-pin FPC, ASSUMED 8.5 x 8.5 x 6 envelope incl. lens) looks out through a Ø3.5 'nose' window between and below the eyes.
eye_z=120; eye_x=13; EYE_HOLE=5.0;   /* v3-bear pass: 10 mm glossy eyes, x ±13, z 120 */   /* likeness pass: 8 mm beads a little closer (were x ±14, z 121; was ±10.5, z 114) */ nose_z=110; NOSE_HOLE=3.5;   // v0.1 light: nose 110 (107 put the camera pod into the collar at +9.5° nod)
cam=[8.5,6.0,8.5]; cam_y=-(eggr(nose_z)-2.4)+0.5+cam[1]/2;   // lens face 0.5 mm behind the inner skin
// Adafruit 3351 Mono Enclosed Speaker 3 W 4 Ω (Core A$8.95): 70 x 30 x 17, holes 3.4 on 63 x 24.
// Matches MAX98357A (3.2 W into 4 Ω at 5 V). The Ø28 placeholder and the 0.5 W 8 Ω mini are retired.
SPK=[30,5,20]; SPK_C=[0,38,64];     // Adafruit 3923 Mini Oval 8 Ω 1 W, 30 x 20 x 5 mm, 3 g (was the 25 g Adafruit 3351); on the BACK wall, facing out
// Adafruit 3006 MAX98357A published 19.4 x 17.8 x 3.0, plus ~8 mm for the post-2024 terminal block.
AMP=[19.4,17.8,3.0]; AMP_HEAD=8.0;
// Adafruit 3421 SPH0645LM4H breakout 16.7 x 12.7 x 1.8, bottom-ported, aligned to the mic hole.
MIC=[16.7,12.7,1.8];

EGG_NP=72;
function egg_prof(o)=concat([[0,o]],[for(i=[1:EGG_NP-1]) let(t=-90+180*i/EGG_NP)
    t<0 ? [(R_EGG-o)*cos(t),ZEQ+(ZEQ-o)*sin(t)] : [(R_EGG-o)*pow(cos(t),2/N_UP),ZEQ+(H_EGG-ZEQ-o)*pow(sin(t),2/N_UP)]],[[0,H_EGG-o]]);
module begg(o=0) rotate_extrude($fn=144) polygon(egg_prof(o));
module tegg(o=0) begg(o);
module hegg(o=0) begg(o);
/* face cap / body split: seam sphere on the tilt axis line (0,0,TILT_Z), meeting the skin at z=SEAM_Z; gap 2*SEAM_G */
SEAM_Z=101; SEAM_G=1.5;
module cap_region()  translate([0,0,119]) sphere(r=sqrt(pow(eggr(SEAM_Z),2)+pow(119-SEAM_Z,2))-SEAM_G,$fn=144);
module body_region() difference(){ translate([-150,-150,-10]) cube([300,300,300]); translate([0,0,119]) sphere(r=sqrt(pow(eggr(SEAM_Z),2)+pow(119-SEAM_Z,2))+SEAM_G,$fn=144); }
module F() translate([-150,-150,-10]) cube([300,150,300]);
module B() translate([-150,0,-10]) cube([300,150,300]);
module below(z) translate([-150,-150,-10]) cube([300,300,z+10]);
module above(z) translate([-150,-150,z]) cube([300,300,300]);

/* ---- servo / horn envelopes (for seats and dummies) ---- */
module servo_env(top) translate([0,0,top]) {
  translate([-s_off-sb[0]/2,-sb[1]/2,-sb[2]]) cube(sb);
  translate([-s_off-s_tab/2,-sb[1]/2,-s_tab_dz]) cube([s_tab,sb[1],s_tab_t]);
  cylinder(d=s_boss[0],h=s_boss[1]);
  cylinder(d=FS_SPLINE_D,h=s_boss[1]+FS_SPLINE_H);
}
module servo_pilots(top) for(sx=[-1,1])
  translate([-s_off+sx*(FS_HOLE_SPAN/2),0,top-s_tab_dz-8]) cylinder(d=SERVO_PIL,h=16);
module horn_env() {                     // ASSUMED typical; sits on the boss
  cylinder(d=21,h=HORN_T);
  for(a=[0,90,180,270]) rotate(a) hull(){
    translate([0,-2,0]) cube([0.6,4,HORN_T]);
    translate([11,-1.6,0]) cube([0.6,3.2,HORN_T]);
  }
  // keep an OD 24 cylinder as the clearance envelope (not a solid used in booleans of printed parts)
}

/* ---- seam lip / groove / elephant-foot chamfer ---- */
// Male lip on the BACK half (protrudes into y<0). Female groove cut from the FRONT half.
// Mid-wall ribbon, 1.2 mm thick, 1.2 mm tall, 0.25 mm FDM clearance. 0.4 mm outer chamfer.
LIP_IN=0.55; LIP_W=1.30; LIP_H=1.20;
module torso_ribbon(inset, thick) difference(){ tegg(inset); tegg(inset+thick); }
module head_ribbon(inset, thick) difference(){ hegg(inset); hegg(inset+thick); }
module seam_male_torso() intersection(){ torso_ribbon(LIP_IN, LIP_W); translate([-80,-LIP_H,-5]) cube([160,LIP_H,160]); body_region(); }
module seam_fem_torso()  intersection(){ torso_ribbon(LIP_IN-SEAM_LIP_CLR, LIP_W+2*SEAM_LIP_CLR); translate([-80,-(LIP_H+SEAM_LIP_CLR),-5]) cube([160,LIP_H+SEAM_LIP_CLR+0.2,160]); body_region(); }
module seam_male_head()  intersection(){ head_ribbon(LIP_IN, LIP_W); translate([-80,-LIP_H,-5]) cube([160,LIP_H,200]); cap_region(); }
module seam_fem_head()   intersection(){ head_ribbon(LIP_IN-SEAM_LIP_CLR, LIP_W+2*SEAM_LIP_CLR); translate([-80,-(LIP_H+SEAM_LIP_CLR),-5]) cube([160,LIP_H+SEAM_LIP_CLR+0.2,200]); cap_region(); }
module seam_chamfer_torso() intersection(){ difference(){ tegg(-SEAM_CHAMFER); tegg(0); } translate([-80,-0.5,-5]) cube([160,1.0,160]); body_region(); }
module seam_chamfer_head()  intersection(){ difference(){ hegg(-SEAM_CHAMFER); hegg(0); } translate([-80,-0.5,-5]) cube([160,1.0,200]); cap_region(); }

/* ================= TORSO ================= */
// v4: upper torso bosses moved to z=79 and lower to z=12. V.01 hug: shoulder pods removed from torso_back;
// belly groove + shoulder hinge ears added to torso_front (module names keep the old hip_ prefix).
tboss=[[-24,12],[24,12],[-30,79],[30,79]];
cboss=[[-16,-18],[16,-18],[-16,18],[16,18]];
TAB_Z=23; TAB_X=29;             // v4: tray tabs moved from (x=±34, z=40) to (x=±29, z=23): clear of the shoulder pods and the Pi standoffs
module torso_shell() intersection(){ difference(){ tegg(); tegg(tw); } body_region(); }
module torso_add(){ intersection(){ tegg(0.1); union(){
  for(p=tboss) translate([p[0],0,p[1]]) rotate([90,0,0]) hull(){ cylinder(d=7,h=16,center=true); translate([sign(p[0])*12,0,0]) cylinder(d=7,h=16,center=true);}
  for(p=cboss) translate([p[0],p[1],tcut-10]) hull(){ cylinder(d=7,h=10); translate([0,sign(p[1])*24,0]) cylinder(d=7,h=10);}
  for(sx=[-1,1]) translate([sx*TAB_X,1.5,TAB_Z]) cube([14,10,12],center=true);
  // mini-speaker frame on the inside of the back wall (speaker glued / foam-taped into the pocket)
  translate([SPK_C[0],SPK_C[1]+2.5,SPK_C[2]]) cube([SPK[0]+4,SPK[1]+6,SPK[2]+4],center=true);
  // mic pocket boss
  translate([18,-28,80]) rotate([90,0,0]) cylinder(d=8,h=8,center=true);
}}}
module torso_cuts_shared(){
  for(sx=[-1,1]) translate([sx*TAB_X,1.5,TAB_Z]) cube([10.6,3.6,10.6],center=true);   // 0.3 mm per side around 10x3x10 tab
  for(sx=[-1,1]) translate([sx*25.4,1.5,TAB_Z]) cube([7.8,3.8,12.4],center=true);  // spine relief through the rib
  // mini speaker pocket (0.3 mm per side) on the back wall, open towards the inside, and a 5 x 3 grille of Ø2.2 holes
  translate(SPK_C) cube([SPK[0]+0.6,SPK[1]+0.6,SPK[2]+0.6],center=true);
  translate([SPK_C[0],SPK_C[1]-5,SPK_C[2]]) cube([SPK[0]-4,8,SPK[2]-4],center=true);
  for(i=[-2:2],k=[-1:1]) translate([SPK_C[0]+i*5,SPK_C[1],SPK_C[2]+k*5]) rotate([-90,0,0]) cylinder(d=2.2,h=20);
  translate([18,-TD/2,80]) rotate([90,0,0]) cylinder(d=2.4,h=30,center=true);
  translate([18,-30.5,80]) cube([MIC[0]+0.6,2.6,MIC[1]+0.6],center=true);
  // webbing slots (optional strap mount on the back)
  for(z=[15.5,30.5]) translate([0,36,z]) cube([22,28,3.2],center=true);
  // bench grommet + vents (v4: vents moved inboard of the shoulder pods)
  translate([0,30,8]) rotate([-70,0,0]) cylinder(d=8,h=30,center=true);
  for(sx=[-1,1],i=[0:2]) translate([sx*(14+i*4),30,45]) cube([2,30,12],center=true);
  // ribbon duct down the +x side of the yaw bore (15 x 1 FPC, 17 x 2.5 slot), torso side
  translate([14,0,tcut-8]) cube([17,2.5,16],center=true);
  translate([14,-6,60]) cube([17,2.5,30],center=true);
}
function aside(side)=side=="L"?1:-1;
module mir(side) mirror([side=="L"?0:1,0,0]) children();
/* ---- belly groove ---- */
module groove_capsule(o=0) hull(){ translate(gline(G_T0)+GR*G_N) sphere(r=GR+o,$fn=48); translate(gline(G_T1)+GR*G_N) sphere(r=GR+o,$fn=48); }
module groove_liner() intersection(){ begg(0.1); body_region(); difference(){ groove_capsule(GW); groove_capsule(0); } }   // body_region: the raised liner stops at the face-cap seam
/* ---- SHOULDER hinge (left; right mirrored). Ear + rear post are moulded into torso_front. Local frame sh_frame():
   x radial at PSI_H. The post ties the ear back into the shell behind the knuckle (away from the arm swing). ---- */
module sh_frame() rotate(PSI_H) children();
POST=[43,9,10,9];                                     // post block in the local frame: u0, v0, du, dv
module hip_plan_upper() hull(){ translate([R_AX,0]) circle(r=KN_R+0.5); translate([41,-6]) square([11,24]); }
module hip_web() difference(){
  translate([POST[0],POST[1],KN_Z0]) cube([POST[2],POST[3],(KN_Z1+EAR_GAP)-KN_Z0+0.01]);
  translate([R_AX,0,0]) cylinder(r=KN_R+0.4,h=200);
}
module hip_upper_ear() {
  sh_frame() translate([0,0,KN_Z1+EAR_GAP]) linear_extrude(EAR_T) hip_plan_upper();
  translate([HX,HY,SPIG_Z0]) cylinder(d=SPIG_D,h=KN_Z1+EAR_GAP-SPIG_Z0+0.01);                    // arbor spigot
  translate([HX,HY,LUG_Z0]) rotate(LUG_A-LUG_W/2) rotate_extrude(angle=LUG_W,$fn=96)
    translate([LUG_R[0],0]) square([LUG_R[1]-LUG_R[0],KN_Z1+EAR_GAP-LUG_Z0+0.01]);                 // stop lug
}
module hip_bracket(side) mir(side) { hip_upper_ear(); sh_frame() hip_web(); }
module hip_bracket_cuts(side) mir(side) {
  translate([HX,HY,0]) cylinder(d=PIN_D,h=200);                                                  // M3 thread-forming pilot
  translate([HX,HY,KN_Z1+EAR_GAP+EAR_T-1.0]) cylinder(d=6.2,h=3);                                // head seat
}
module torso_front() difference(){
  union(){ intersection(){ torso_shell(); F(); } intersection(){ torso_add(); F(); } groove_liner();
    hip_bracket("L"); hip_bracket("R"); }
  torso_cuts_shared();
  seam_fem_torso();
  seam_chamfer_torso();
  groove_capsule(0);
  for(p=tboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_CLR,h=40,center=true);
  for(p=cboss) translate([p[0],p[1],tcut-12]) cylinder(d=M25_PIL,h=20);
  hip_bracket_cuts("L"); hip_bracket_cuts("R");
}
module torso_back() difference(){
  union(){ intersection(){ torso_shell(); B(); } intersection(){ torso_add(); B(); } seam_male_torso(); }
  torso_cuts_shared();
  seam_chamfer_torso();
  for(p=tboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_PIL,h=40,center=true);
  for(p=cboss) translate([p[0],p[1],tcut-12]) cylinder(d=M25_PIL,h=20);
}

/* ================= TRAY ================= */
// v4: clasp-servo shelf removed (no clasp). Tabs lowered to z=23, x=±29.
module tray() difference(){
  union(){
    translate([0,1.5,39]) cube([58,3,38],center=true);    // x=±29, flush with tab inner end
    for(sx=[-1,1]) translate([sx*TAB_X,1.5,TAB_Z]) cube([10,3,10],center=true);
    for(sx=[-1,1],sz=[-1,1]) translate([sx*pi_holes[0]/2,-2,pi_z+sz*pi_holes[1]/2]) rotate([90,0,0]) cylinder(d=5,h=4,center=true);
    translate([0,9.9,23]) cube([36,14.2,6],center=true);                          // wrap bar
    translate([0,6.5,42]) cube([AMP[0]+4,6,AMP[1]+AMP_HEAD+4],center=true);       // amp pocket on the +y face of the spine
  }
  for(sx=[-1,1],sz=[-1,1]) translate([sx*pi_holes[0]/2,0,pi_z+sz*pi_holes[1]/2]) rotate([90,0,0]) cylinder(d=M25_CLR,h=12,center=true);
  for(sx=[-1,1]) translate([sx*26,1.5,50]) cube([4,6,2.5],center=true);           // wire slots
  translate([0,6.5,42]) cube([AMP[0]+0.6,3.6,AMP[1]+0.4+AMP_HEAD],center=true);
  for(sx=[-1,1],sz=[-1,1]) translate([sx*7.5,6.5,42+sz*6.5]) rotate([90,0,0]) cylinder(d=M2_PIL,h=10,center=true);
}
/* ================= YAW STACK ================= */
// Journal 92..97.4, washer 97.4..98.2, 0.30 mm axial gap, head cone starts so z=98.5 is 0.30 above the washer.
JRN_Z0=tcut+7;            // 92
JRN_Z1=97.4;
JRN_OD=44.0;
SKIRT_ID=JRN_OD+2*JRN_RAD;  // 44.7
SKIRT_OD=50.6;
WASH_T=0.8; WASH_ID=35; WASH_OD=43.0;
WASH_Z0=JRN_Z1; WASH_Z1=JRN_Z1+WASH_T;   // 97.4..98.2
FLOOR_Z=WASH_Z1+AXIAL_GAP;               // 98.5
RET_Z0=tcut+3.6; RET_H=3.05;             // top 91.65, play vs journal lip at 92.0 = 0.35
module yaw_collar() difference(){
  union(){
    translate([0,0,tcut]) cylinder(d=64,h=3);
    translate([0,0,tcut+3]) cylinder(d=38,h=4);
    translate([0,0,JRN_Z0]) cylinder(d=JRN_OD,h=JRN_Z1-JRN_Z0);
    for(a=[55,-55]) rotate(90+a) translate([27,-2,tcut+3]) cube([2,4,5]);
    translate([0,0,tcut+3]) difference(){ cylinder(d=63,h=8.5); cylinder(d=60,h=20); }
    // hangers at official tab / hole locations; pilots 1.7. Solid is ABOVE the tabs; tab envelope is cut out below.
    for(x0=[-s_off-s_tab/2, -s_off+sb[0]/2+0.3])
      translate([x0,-sb[1]/2,yaw_top-s_tab_dz]) cube([s_tab/2-sb[0]/2-0.3,sb[1],tcut-(yaw_top-s_tab_dz)+0.5]);
    translate([-s_off+sb[0]/2+0.3,-sb[1]/2,yaw_top-s_tab_dz]) cube([20-(-s_off+sb[0]/2+0.3),sb[1],3.5]);
    translate([17.5,-sb[1]/2,yaw_top-s_tab_dz]) cube([2.5,sb[1],tcut-(yaw_top-s_tab_dz)+0.5]);
    for(sx=[-1,1]) translate([-s_off+sx*(FS_HOLE_SPAN/2),0,yaw_top]) cylinder(d=6,h=5);  // pilot bosses above tabs
  }
  // tab + body clearance so the servo seats without a volume clash
  translate([-s_off-s_tab/2-clr,-sb[1]/2-clr,yaw_top-s_tab_dz-0.2]) cube([s_tab+2*clr,sb[1]+2*clr,s_tab_t+0.3]);
  translate([-s_off-sb[0]/2-clr,-sb[1]/2-clr,yaw_top-sb[2]-1]) cube([sb[0]+2*clr,sb[1]+2*clr,sb[2]+1.2]);
  // Stepped bore: the official holes at x=-16.4 and +11.3 sit at r=16.4 / 11.3, inside a Ø34
  // cylinder, so a full-height Ø34 would delete the pilots. The horn (Ø24 envelope) is installed
  // from above and lives on the boss (z=88.3), so the Ø34 starts at the boss top.
  translate([0,0,yaw_top+s_boss[1]]) cylinder(d=34,h=20);          // 88.3 up: horn, coupler, ribbon
  translate([0,0,yaw_top-0.2]) cylinder(d=s_boss[0]+1.6,h=s_boss[1]+0.4);  // boss clearance in the flange
  for(p=cboss) translate([p[0],p[1],tcut-1]) cylinder(d=M25_CLR,h=10);     // clearance in the collar
  servo_pilots(yaw_top);
  translate([14,0,yaw_top+s_boss[1]+6]) cube([8,2.8,16],center=true);
}
module yaw_thrust_washer() translate([0,0,WASH_Z0]) difference(){ cylinder(d=WASH_OD,h=WASH_T); translate([0,0,-1]) cylinder(d=WASH_ID,h=WASH_T+2); }
module yaw_retainer_half(sx=1) rotate(yaw) difference(){
  intersection(){ translate([0,0,RET_Z0]) difference(){ cylinder(d=48.0,h=RET_H); cylinder(d=39,h=12,center=true);} translate([sx>0?0.4:-100.4,-50,0]) cube([100,100,200]); }
  translate([sx*23.8,0,RET_Z0+RET_H/2]) rotate([0,90,0]) cylinder(d=M2_CLR,h=14,center=true);
}
// coupler sits ON the horn (no air gap). Disc 1.6 mm, blade 2.0 mm in a 2.7 mm slot (0.35 / side).
COUP_Z0=yaw_top+s_boss[1]+HORN_T;         // 90.3, on the horn
module yaw_coupler() rotate(yaw) difference(){
  union(){
    translate([0,0,COUP_Z0]) cylinder(d=20,h=1.6);
    translate([-8,-1,COUP_Z0+1.6]) cube([16,2.0,5.2]);   // blade 2.0 thick
  }
  translate([0,0,yaw_top]) cylinder(d=3,h=24);
  for(sx=[-1,1]) translate([sx*7,0,yaw_top]) cylinder(d=2.3,h=24);   // clearance for horn screws through the disc
}
/* ================= NECK TURRET + HEAD (pan + tilt) ================= */
// neck_turret yaws with the pan coupler and carries the tilt FS90MG. The head (shell, camera, bosses) pivots on
// the turret about the tilt axis: the servo horn drives tilt_hub, keyed into a socket in head_back on -x;
// an M3 screw through the head wall on +x runs in the turret idler column.
module tilt_pose() translate([0,TILT_Y,TILT_Z]) rotate([tilt,0,0]) translate([0,-TILT_Y,-TILT_Z]) children();
module head_pose() rotate(yaw) tilt_pose() children();
HEAD_Z0=hcut+5.5;   // V.01 hug: head shell now starts at z=103.5 (was 101) so the rim clears the turret/collar when nodding
module head_shell() intersection(){ difference(){ begg(); begg(2.4); } cap_region(); }
// V.01 hug: the two lower seam bosses moved from z=110 to z=106 (x ±32) to clear the tilt horn / hub; upper to x ±28.
hboss=[[-32,hcut+8],[32,hcut+8],[-27,136],[27,136]];
module head_bosses() intersection(){ begg(0.1); cap_region(); above(HEAD_Z0); for(p=hboss) translate([p[0],0,p[1]]) rotate([90,0,0]) hull(){ cylinder(d=7,h=16,center=true); translate([sign(p[0])*12,0,0]) cylinder(d=7,h=16,center=true);} }
// Skirt-down printable bearing: vertical skirt, then a 30°-from-vertical cone so a 35° support
// threshold does not put supports on the bearing faces. Flat thrust is the separate washer.
// Cone: 30° from vertical, starts at skirt ID 44.7, z=96.8. At z=98.5 (floor), ID ≈ 42.7, over the washer.
module yaw_skirt_and_cone() {
  difference(){
    union(){
      translate([0,0,tcut+4]) cylinder(d=SKIRT_OD,h=FLOOR_Z-(tcut+4));          // 89 .. 98.5
      // 30° cone from z=97.0 to z=104 (at washer top 98.2 the cone is just outside OD 43.0)
      translate([0,0,97.0]) cylinder(d1=SKIRT_OD,d2=36.4+2*(SKIRT_OD-SKIRT_ID)/2,h=7.0);
      translate([0,0,104]) cylinder(d=50,h=2);
    }
    translate([0,0,tcut+3.9]) cylinder(d=SKIRT_ID,h=97.0-(tcut+3.9)+0.05);
    translate([0,0,97.0]) cylinder(d1=SKIRT_ID,d2=SKIRT_ID-2*7.0*tan(30),h=7.01);  // 44.7 -> ~36.6
    translate([0,0,103.9]) cylinder(d=34,h=8);
  }
}
module ribbon_loop_bay() {
  // service loop r=14 (π*14 ≈ 44 mm extra; requirement was ≥9.4 mm extra). Slot 17 x 2.5 for 15 x 1 FPC.
  translate([14,-6,112]) rotate([90,0,0]) rotate_extrude(angle=180,$fn=32) translate([14,0]) square([3.2,18],center=true);
}
// tilt servo frame: local z (spline) -> world -x, local x (servo long axis) -> world -z, local y -> world -y.
module tiltservo_frame() translate([-TS_X,TILT_Y,TILT_Z]) multmatrix([[0,0,-1,0],[0,-1,0,0],[-1,0,0,0],[0,0,0,1]]) children();
TILT_HOLES_Z=[TILT_Z+s_off-FS_HOLE_SPAN/2, TILT_Z+s_off+FS_HOLE_SPAN/2];   // tab holes (world z)
CR_X=[-TS_X+s_tab_t, -TS_X+s_tab_t+3];                                       // cradle plate x -17.8..-14.8 (tab underside face)
IDL_X=[24,27];                                                               // idler column on +x
HUB_X0=-TS_X-s_boss[1]-HORN_T;                                               // horn outer face -28.3
module neck_turret() rotate(yaw) union(){
    for(sy=[-1,1]) translate([-9, sy*(1.0+BLADE_CLR) - (sy<0?2:0), hcut-4]) cube([18,2,8]);   // coupler slot walls (2.7)
  difference(){
  union(){
    yaw_skirt_and_cone();
    translate([-2,24.6,tcut+4]) cube([4,3.4,4]);                              // pan hard-stop lug (from v3 head_back)
    // cradle plate for the tilt FS90MG (tabs screw to its -x face)
    intersection(){
      translate([CR_X[0],TILT_Y-8,100]) cube([CR_X[1]-CR_X[0],16,TILT_HOLES_Z[1]+4.5-100]);
      hegg(4.5);
    }
    // idler column on +x: foot on the deck, column up to the tilt axis
    translate([16,TILT_Y-4,104]) cube([IDL_X[1]-16,8,2]);
    translate([IDL_X[0],TILT_Y-4,104]) cube([IDL_X[1]-IDL_X[0],8,TILT_Z+5-104]);
    translate([IDL_X[0],TILT_Y,TILT_Z]) rotate([0,90,0]) cylinder(d=8,h=IDL_X[1]-IDL_X[0]);
  }
  translate([0,0,tcut+3.9]) cylinder(d=SKIRT_ID,h=97.0-(tcut+3.9)+0.05);   // retainer/journal bay
  translate([-40,-60,98.6]) cube([80,57,20]);                // front of deck/cone cut away: camera + chin clear when nodding
  translate([23.8,0,RET_Z0+RET_H/2]) rotate([0,90,0]) cylinder(d=M2_PIL,h=12,center=true);
  translate([-23.8,0,RET_Z0+RET_H/2]) rotate([0,90,0]) cylinder(d=M2_PIL,h=12,center=true);
  translate([-9,10,hcut-1]) cube([18,4,10]);                 // servo wires (pan + tilt service loop)
  translate([14,0,hcut+2]) cube([17,2.5,16],center=true);    // camera FPC slot (17 x 2.5)
  translate([-9,-14,hcut-1]) cube([18,4,10]);
  // tilt servo: body window through the cradle, tab envelope, pilots
  tiltservo_frame() {
    translate([-s_off-sb[0]/2-clr,-sb[1]/2-clr,-sb[2]-1]) cube([sb[0]+2*clr,sb[1]+2*clr,sb[2]+1.2]);
    translate([-s_off-s_tab/2-clr,-sb[1]/2-clr,-s_tab_dz-0.01]) cube([s_tab+2*clr,sb[1]+2*clr,s_tab_t+5]);
    cylinder(d=s_boss[0]+1.6,h=20);
  }
  for(z=TILT_HOLES_Z) translate([CR_X[0]-1,TILT_Y,z]) rotate([0,90,0]) cylinder(d=SERVO_PIL,h=8);
  translate([IDL_X[0]-1,TILT_Y,TILT_Z]) rotate([0,90,0]) cylinder(d=2.5,h=10);      // M3 pivot screw pilot (thread-forming)
  }
}
// tilt_hub: screws to the tilt horn (2 x M2 at r=7), 10 x 10 key into the head_back socket.
module tilt_hub() head_pose() difference(){
  union(){
    translate([HUB_X0,TILT_Y,TILT_Z]) rotate([0,-90,0]) cylinder(d=18,h=2.5);
    translate([HUB_X0-2.5-6,TILT_Y-5,TILT_Z-5]) cube([6.01,10,10]);
  }
  translate([0,TILT_Y,TILT_Z]) rotate([0,90,0]) cylinder(d=2.8,h=200,center=true);              // horn screw
  translate([HUB_X0-0.01,TILT_Y,TILT_Z]) rotate([0,-90,0]) cylinder(d=FS_SPLINE_D+0.8,h=2.6);    // spline tip (-30.3) clearance
  for(a=[0,180]) translate([HUB_X0+0.01,TILT_Y,TILT_Z]) rotate([a,0,0]) translate([0,0,7]) rotate([0,-90,0]) cylinder(d=1.7,h=2.6);
}
module head_tilt_socket() difference(){
  intersection(){ hegg(0.1); translate([-60,0.2,TILT_Z-7]) cube([60-(-HUB_X0+2.5+0.5),TILT_Y+7-0.2,14]); }
  translate([HUB_X0-2.5-6.5,TILT_Y-5.2,TILT_Z-5.2]) cube([7,10.4,10.4]);                         // key pocket 10.4
  translate([0,TILT_Y,TILT_Z]) rotate([0,90,0]) cylinder(d=6,h=200,center=true);                 // screwdriver access
}
module head_idler_boss() difference(){
  intersection(){ hegg(0.1); translate([IDL_X[1]+0.6,TILT_Y-5,TILT_Z-5]) cube([30,10,10]); }
  translate([0,TILT_Y,TILT_Z]) rotate([0,90,0]) cylinder(d=PIN_RUN,h=200);
}
module head_back() head_pose() difference(){
  union(){
    intersection(){ head_shell(); B(); } intersection(){ head_bosses(); B(); }
    head_tilt_socket(); head_idler_boss();
    seam_male_head();
  }
  for(p=hboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_PIL,h=40,center=true);
  translate([HUB_X0-2.5-6.5,TILT_Y-5.2,TILT_Z-5.2]) cube([7,10.4,10.4]);                         // hub key pocket (also through the shell wall)
  ribbon_loop_bay();
  seam_chamfer_head();
}
module head_front() head_pose() difference(){
  union(){ intersection(){ head_shell(); F(); } intersection(){ head_bosses(); F(); }
    intersection(){ hegg(0.1); F(); cap_region(); translate([0,cam_y-1.5,nose_z]) cube([cam[0]+4.5,cam[1]+4,cam[2]+4.5],center=true); } }
  for(p=hboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_CLR,h=40,center=true);
  translate([0,cam_y+3,nose_z]) cube([cam[0]+0.4,cam[1]+6,cam[2]+0.4],center=true);                // camera pocket, open to the inside
  translate([0,0,nose_z]) rotate([90,0,0]) cylinder(d=NOSE_HOLE,h=60);                             // 'nose' window for the lens
  translate([0,cam_y,nose_z+cam[2]/2]) cube([6,2,6],center=true);                                  // FPC exit on top of the pocket
  translate([0,cam_y-1,nose_z-(cam[2]+4.5)/2]) rotate([45,0,0]) translate([-(cam[0]+6)/2,0,-20]) cube([cam[0]+6,20,20]);  // 45° chamfer on the pod's inner lower edge: clears the collar when nodding
  for(sx=[-1,1]) translate([sx*eye_x,0,eye_z]) rotate([90,0,0]) cylinder(d=EYE_HOLE,h=60);          // 8 mm safety-eye shanks
  ribbon_loop_bay();
  translate([14,-8,120]) cube([17,2.5,20],center=true);      // ribbon run camera -> loop
  seam_fem_head();
  seam_chamfer_head();
}

/* ================= PASSIVE HUG ARMS (V.01, Mirumi proportions) ================= */
// Band through the path samples: centre on_egg(psi,z,off); the two spheres of each section sit ±ARM_HW across the
// path, in the skin tangent plane (binormal = egg normal x path tangent).
function apath(side)=side=="L"?ARM_PATH_L:ARM_PATH_R;
function npath(side)=len(apath(side));
function ac(side,i)=let(p=apath(side)[i]) on_egg(p[0],p[1],p[2]-ARM_THIN);
function an(side,i)=let(p=apath(side)[i], n=[cos(p[0]),sin(p[0]),-eggdr(p[1])]) n/norm(n);
function at(side,i)=let(n=npath(side), a=ac(side,max(0,i-1)), b=ac(side,min(n-1,i+1))) (b-a)/norm(b-a);
function aw(side,i)=let(w=cross(an(side,i),at(side,i))) w/norm(w);
function ahw(side,i)= i==0 ? 3.5 : (i==npath(side)-1 ? 3.0 : ARM_HW);   // narrower root (clears the ear) and paw tip
module sec(side,i,r) for(s=[-1,1]) translate(ac(side,i)+s*ahw(side,i)*aw(side,i)) sphere(r=r,$fn=20);
module arm_band(side,o=0,i0=0,i1=-1) { e=(i1<0?npath(side)-1:i1); for(i=[i0:e-1]) hull(){ sec(side,i,ARM_RS+o); sec(side,i+1,ARM_RS+o); } }
module knuckle_local() difference(){
  translate([HX,HY,KN_Z0]) cylinder(r=KN_R,h=KN_Z1-KN_Z0,$fn=64);
  translate([HX,HY,0]) cylinder(d=PIN_RUN,h=200);
}
module knuckle_cuts() {
  translate([HX,HY,0]) cylinder(d=PIN_RUN,h=200);
  translate([HX,HY,KN_Z0-0.01]) cylinder(d=7.2,h=1.0);                                       // M3 washer seat under the knuckle
  translate([HX,HY,REC_Z0]) cylinder(d=REC_D,h=20);                                          // spring recess
  translate([HX,HY,REL_Z0]) rotate(LUG_A-LUG_W/2-ARM_OPEN) rotate_extrude(angle=LUG_W+ARM_OPEN,$fn=96)
    translate([REL_R[0],0]) square([REL_R[1]-REL_R[0],10]);                                    // stop relief
  translate([HX,HY,REC_Z0-0.01]) rotate(-100) translate([3.0,-0.8,0]) cube([4.5,1.6,2.2]);   // arm-side spring leg slot
}
module arm_local(side) difference(){
  union(){ mir(side) knuckle_local(); arm_band(side,0); }
  mir(side) knuckle_cuts();
}
// opening rotates the arm about its own hinge axis: + for the left arm (CCW from above), - for the right
module arm_pose(side) let(sx=aside(side)) translate([sx*HX,HY,0]) rotate(side=="L"?armL:-armR) translate([-sx*HX,-HY,0]) children();
module arm(side) arm_pose(side) arm_local(side);
// TPU pad: a 1.5 mm sleeve over the band where it crosses the handle (glue or stretch on). Shore 85-95A.
function padsec(side)=side=="L"?PAD_SEC_L:PAD_SEC_R;
module paw_pad(side) arm_pose(side) difference(){ arm_band(side,PAD_T,padsec(side)[0],padsec(side)[1]); arm_band(side,0.02); }
// Mirumi-style SOFT ARM SLEEVE (soft goods, not printed): a stuffed fur tube, SLV_R round, around the printed band.
// Each section is a sphere whose INNER face (toward the body) coincides with the band's inner face, so the sleeve
// adds bulk outward and sideways only: the pads (1.5 mm below the band) still make the handle contact and the
// grip geometry is unchanged. A shoulder cap centred on the hinge axis hides the knuckle and blends into the
// body; a rounded mitten closes the tip. Body egg subtracted at rest. Pile (≈5–8 mm) goes on top of this.
SLV_R=9.5; SLV_ROOT=8.0; SLV_CAP_R=11.0; SLV_CAP_Z=[68,90]; MIT_R=12.0;   /* v3-bear pass: plumper mitten paws (were SLV_R 9, MIT_R 10.5) */ MIT_FWD=3.0;
function sc(side,i,r)=ac(side,i)+an(side,i)*(r-ARM_RS);
function slv_r(side,i)= i<=1 ? SLV_ROOT : SLV_R;
module ssec(side,i) let(r=slv_r(side,i)) translate(sc(side,i,r)) sphere(r=r,$fn=32);
module sleeve_solid(side) {
  n=npath(side);
  for(i=[1:n-2]) hull(){ ssec(side,i); ssec(side,i+1); }
  hull(){ mir(side) translate([HX,HY,SLV_CAP_Z[0]+SLV_CAP_R*0.6]) cylinder(r=SLV_CAP_R,h=SLV_CAP_Z[1]-SLV_CAP_Z[0]-SLV_CAP_R*1.2,$fn=48);
          mir(side) translate([HX,HY,SLV_CAP_Z[1]-SLV_CAP_R*0.6]) sphere(r=SLV_CAP_R*0.6,$fn=32);
          mir(side) translate([HX,HY,SLV_CAP_Z[0]+SLV_CAP_R*0.6]) sphere(r=SLV_CAP_R,$fn=32);
          ssec(side,1); }
  hull(){ ssec(side,n-2); translate(sc(side,n-1,MIT_R)+at(side,n-1)*MIT_FWD) sphere(r=MIT_R,$fn=32); }   // mitten paw
}
SLV_MEET=0.75;   // the two stuffed mittens are flattened where they meet in front of the handle: 1.5 mm apart at rest, never overlapping
module sleeve_proxy(side) arm_pose(side) difference(){ sleeve_solid(side); begg(0);
  translate([aside(side)*(SLV_MEET-100),0,0]) cube([200,400,400],center=true); }
// grip test object (reference only): round handle Ø d lying in the centre groove on the floor line
module grip_rod(d=12.5,h=50) translate(gline(G_MIDT)+G_N*(d/2+0.1)) multmatrix(rotmat_to(G_U)) translate([0,0,-h/2]) cylinder(d=d,h=h,$fn=48);
function rotmat_to(u)=let(z=[0,0,1], v=cross(z,u), c=u*z, s=norm(v), k=v/(s>1e-9?s:1))
  // Rodrigues: rotate z onto u
  let(K=[[0,-k[2],k[1]],[k[2],0,-k[0]],[-k[1],k[0],0]], I=[[1,0,0],[0,1,0],[0,0,1]], R=I+s*K+(1-c)*K*K)
  [[R[0][0],R[0][1],R[0][2],0],[R[1][0],R[1][1],R[1][2],0],[R[2][0],R[2][1],R[2][2],0],[0,0,0,1]];

module bezel() difference(){ union(){ cylinder(d=21,h=12); cylinder(d=27,h=1.6); } translate([0,0,-1]) cylinder(d=12,h=20); translate([-8,-1.1,2.2]) cube([30,2.2,2.4]); }
module shutter() union(){ translate([-6,-0.9,0]) cube([27,1.8,2]); cylinder(d=14,h=0.9); translate([20,-0.9,0]) cube([1.8,1.8,5]); }
/* ================= DUMMIES / PROXIES ================= */
module dummy_servo_yaw() servo_env(yaw_top);
module dummy_horn_yaw() translate([0,0,yaw_top+s_boss[1]]) horn_env();
module dummy_servo_tilt() rotate(yaw) tiltservo_frame() servo_env(0);
module dummy_horn_tilt() head_pose() tiltservo_frame() translate([0,0,s_boss[1]]) horn_env();   // horn rides with the head
module dummy_pi() translate([0,-4-pi[1]/2,pi_z]) cube(pi,center=true);
module dummy_cam() head_pose() translate([0,cam_y,nose_z]) cube(cam,center=true);
module dummy_speaker() translate(SPK_C) cube(SPK,center=true);                 // Adafruit 3923 30x5x20, 30 along x
module dummy_amp() translate([0,6.5,42]) cube([AMP[0],3.0,AMP[1]],center=true);
module dummy_mic() translate([18,-30.5,80]) cube([MIC[0],MIC[2],MIC[1]],center=true);
module dummies(){ dummy_servo_yaw(); dummy_horn_yaw(); dummy_servo_tilt(); dummy_horn_tilt();
  dummy_pi(); dummy_cam(); dummy_speaker(); dummy_amp(); dummy_mic(); }
// v3-bear-look SOFT BODY (soft goods, not printed): the fur skin (FUR_SKIN) plus loose fibrefill padding sewn into the
// round BALL torso of the v3 bear: outer soft surface = sphere TB_R about (0,0,TB_Z), wherever that is outside the egg + skin.
// The ball is cut flat at z 0 (Ø≈72 sit-pad on the bag top). Padding is gone by z ≈ 81, so above that the egg + skin forms
// a short 'neck' (r ≈ 49.8) under the head ball. No feet (v3 had none). The handle channel is kept clear down the belly.
FUR_SKIN=4; TB_Z=48; TB_R=60; PAD_Z4=92;
function ball_r(z)=(abs(z-TB_Z)>=TB_R)?0:sqrt(TB_R*TB_R-(z-TB_Z)*(z-TB_Z));
function body_pad(z)=(z<0||z>=PAD_Z4)?0:max(0,ball_r(z)-eggr(z)-FUR_SKIN);
function pear_pad(z)=body_pad(z);   // alias kept for older scripts
FOOT_PSI=30; FOOT_Z=8; FOOT_OFF=12; FOOT_R=[13,11,7];   // (feet dropped in the v3-bear pass; kept for older scripts)
module plush_feet() for(sx=[-1,1]) let(ps=-90+sx*FOOT_PSI) translate(on_egg(ps,FOOT_Z,FOOT_OFF)) rotate([0,0,ps])
  scale(FOOT_R) sphere(r=1,$fn=40);
module soft_body() difference(){
  rotate_extrude($fn=96) polygon(concat([[0,0]],[for(z=[0:2:PAD_Z4]) [eggr(z)+FUR_SKIN+body_pad(z),z]],[[0,PAD_Z4]]));
  begg(0);
  hull(){ groove_capsule(0); translate(G_N*30) groove_capsule(0); }      // handle channel stays open
  // the handle channel through the padding runs on down to the bag top
  hull(){ for(t=[-56,G_T0]) for(o=[0,30]) translate(gline(t)+(GR+o)*G_N) sphere(r=GR,$fn=32); }
}
// v3-bear-look SOFT HEAD (soft goods on the face cap, rides with the head): skin + padding to a round head BALL, an
// ellipse of revolution HB_A wide (radius) x HB_B tall about (0,0,HB_Z), top at z 155 (shell top 148 + 7 mm skin and crown padding),
// plus two small round stuffed bear ears (fleece, sewn on). Starts at the face-cap seam (z 101).
HB_A=55; HB_B=41; HB_Z=114;
function head_ball_r(z)=(abs(z-HB_Z)>=HB_B)?0:HB_A*sqrt(1-pow((z-HB_Z)/HB_B,2));
function head_soft_r(z)=max(z<H_EGG?eggr(z)+FUR_SKIN:0, head_ball_r(z));
function head_pad(z)=max(0,head_ball_r(z)-(z<H_EGG?eggr(z):0)-FUR_SKIN);
EAR_R=[12,5.5,11]; EAR_C=[32.5,-3,146]; EAR_ROLL=28;     // ear disc (x wide, y thick, z tall), centre, outward roll (deg)
module plush_ears() for(sx=[-1,1]) translate([sx*EAR_C[0],EAR_C[1],EAR_C[2]]) rotate([0,-sx*EAR_ROLL,0]) scale(EAR_R) sphere(r=1,$fn=40);
// The lower edge is a soft brim: inside it is undercut to r = neck skin + 1 mm up to z 107, then back to the egg by z 118,
// so when the head nods ±10° the brim swings over the neck fur and never pinches against the rigid torso rim.
NECK_CLR_R=eggr(SEAM_Z)+FUR_SKIN+1.0;
module soft_head_rest() difference(){
  union(){ rotate_extrude($fn=96) polygon(concat([[0,SEAM_Z]],[for(z=[SEAM_Z:1:HB_Z+HB_B]) [head_soft_r(z),z]],[[0,HB_Z+HB_B]])); plush_ears(); }
  begg(0);
  rotate_extrude($fn=96) polygon([[0,SEAM_Z-1],[NECK_CLR_R,SEAM_Z-1],[NECK_CLR_R,SEAM_Z+6],[eggr(SEAM_Z+17)+0.2,SEAM_Z+17],[0,SEAM_Z+17]]);
  below(SEAM_Z+2);   // brim hem 2 mm above the seam: clears the shoulder-ear tops (z 92.4) at yaw ±42 + nod 10
}
module soft_head() head_pose() soft_head_rest();
// torso fur envelope (4 mm), with the belly groove
module fur_proxy_torso() difference(){ intersection(){ difference(){ tegg(-4); tegg(0); } body_region(); } groove_capsule(0); }


/* ================= TEST COUPON (print this first) ================= */
module coupon() {
  // one plate: journal+skirt+washer, tray tab/pocket, FS90MG servo seat
  difference(){
    union(){
      translate([0,0,0]) cube([90,50,3]);
      // journal boss + skirt ring (same diameters / 0.35 radial)
      translate([18,25,3]) cylinder(d=JRN_OD,h=6);
      translate([18,25,3]) difference(){ cylinder(d=SKIRT_OD,h=8); translate([0,0,-1]) cylinder(d=SKIRT_ID,h=12); }
      // washer printed flat next to it
      translate([18,8,3]) difference(){ cylinder(d=WASH_OD,h=WASH_T); translate([0,0,-1]) cylinder(d=WASH_ID,h=WASH_T+2); }
      // tab and a pocket rib
      translate([48,8,3]) cube([10,3,10]);
      translate([48,20,3]) difference(){ cube([14,8,12]); translate([1.7,2.2,0.7]) cube([10.6,3.6,10.6]); }
      // servo seat: shelf with official 27.7 span, 1.7 pilots, body cutout
      translate([46,34,3]) difference(){
        cube([s_tab+8,16,5]);
        translate([4+(s_tab-sb[0])/2-clr,8-sb[1]/2-clr,1]) cube([sb[0]+2*clr,sb[1]+2*clr,8]);
        for(sx=[-1,1]) translate([4+s_tab/2+sx*(FS_HOLE_SPAN/2),8,-1]) cylinder(d=SERVO_PIL,h=10);
      }
    }
    // label recesses (shallow)
    translate([2,2,2.4]) cube([12,4,1]);
  }
}

PRINTED_PARTS=["torso_front","torso_back","tray","yaw_collar","yaw_retainer_A","yaw_retainer_B","yaw_coupler","yaw_thrust_washer",
  "neck_turret","tilt_hub","head_back","head_front","arm_L","arm_R","paw_pad_L","paw_pad_R","coupon"];   // bezel + shutter removed (bought 8 mm safety eyes)
if(part=="torso_front") torso_front(); else if(part=="torso_back") torso_back();
else if(part=="tray") tray(); else if(part=="yaw_collar") yaw_collar();
else if(part=="yaw_retainer_A") yaw_retainer_half(1); else if(part=="yaw_retainer_B") yaw_retainer_half(-1);
else if(part=="yaw_coupler") yaw_coupler(); else if(part=="yaw_thrust_washer") yaw_thrust_washer();
else if(part=="neck_turret") neck_turret(); else if(part=="tilt_hub") tilt_hub();
else if(part=="head_back") head_back(); else if(part=="head_front") head_front();
else if(part=="arm_L") arm("L"); else if(part=="arm_R") arm("R");
else if(part=="paw_pad_L") paw_pad("L"); else if(part=="paw_pad_R") paw_pad("R");
else if(part=="bezel") bezel(); else if(part=="shutter") shutter();
else if(part=="dummies") dummies();
else if(part=="sleeve_proxy_L") sleeve_proxy("L"); else if(part=="sleeve_proxy_R") sleeve_proxy("R");
else if(part=="fur_proxy_torso") fur_proxy_torso();
else if(part=="soft_body") soft_body();
else if(part=="soft_head") soft_head();
else if(part=="coupon") coupon();
else if(part=="dummy_servo_yaw") dummy_servo_yaw();
else if(part=="dummy_horn_yaw") dummy_horn_yaw();
else if(part=="dummy_servo_tilt") dummy_servo_tilt();
else if(part=="dummy_horn_tilt") dummy_horn_tilt();
else if(part=="dummy_pi") dummy_pi();
else if(part=="dummy_cam") dummy_cam();
else if(part=="dummy_speaker") dummy_speaker();
else if(part=="dummy_amp") dummy_amp();
else if(part=="dummy_mic") dummy_mic();
else if(part=="grip_rod") grip_rod();
else { torso_front(); torso_back(); tray(); yaw_collar(); yaw_retainer_half(1); yaw_retainer_half(-1); yaw_coupler(); yaw_thrust_washer();
  neck_turret(); tilt_hub(); head_back(); head_front(); arm("L"); arm("R"); color("black") { paw_pad("L"); paw_pad("R"); } color("red") dummies(); }
