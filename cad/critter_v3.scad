// SPDX-License-Identifier: CERN-OHL-P-2.0
// Evokin v3 CAD. Hardware licensed under CERN-OHL-P v2. See LICENSE-CERN-OHL-P.
// critter_v3.scad -- v3 BENCH PROTOTYPE CAD. UNPRINTED, MOTION/FORCE UNTESTED.
// Not production, not child-ready, not waterproof, power bench-tethered only.
// NEW folder; v0/v1/v2 sources and STLs are not modified.
// v3 redesigns seats and seams around 2x Feetech FS90MG (official drawing p.5, edition A/0, 2021-04-30).
// NAMING (same as v2): arm_L / shoulder_bracket_L / paw_pad_L = the CRITTER'S OWN LEFT = +x.
// Units mm. Frame: z up, -y = face/front, +y = wearer/strap side. STLs export at yaw=0, clasp=0 (open).
// openscad -D 'part="arm_L"' -D yaw=0 -D clasp=0 -o x.stl critter_v3.scad
include <v3_params.scad>
part = "assembly";
yaw = 0;
clasp = 0;
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
     + thread. Buy a longer M2.5 (e.g. 8–10 mm) and confirm on arrival.
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
HORN_CLEAR=2.0;               // min air from horn top to drum underside
DRUM_ABOVE_BOSS=HORN_T+HORN_CLEAR; // 4.0

/* ---- fastener scheme (one scheme, used everywhere printed-to-printed) ----
   M2.5: clearance 2.8 in the accessible / front / through half, pilot 2.1 in the receiving half.
   Optional M2.5 heat-set later: receiving bosses are Ø7, long enough for a standard M2.5 brass insert.
   Servo tab self-tappers (or M2): pilot 1.7 in the printed hanger/shelf, through the servo's Ø2.2 tab holes.
   Retainer M2: clearance 2.3 in the retainer, pilot 1.7 in the head skirt. */
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
TH=100; TW=92; TD=80; tw=2.4; tcut=85;
HC=118; HH=64; HW=84; HD=74; hcut=98;
sb=FS_BODY; s_off=FS_S_OFF; s_tab=FS_TAB; s_tab_t=FS_TAB_T; s_tab_dz=FS_TAB_DZ; s_boss=[FS_BOSS_D,FS_BOSS_H];
yaw_top=84;
clasp_top=51;                 // lowered 4 mm vs v2 so drum grooves still straddle zq=63.5 after the 4.0 mm horn gap
clasp_xy=[0,20];
piv_x=58; piv_y=10; sh_z=62; hub_d=10; hub_h=7.4; ear_gap=hub_h+0.8;
pi=[65,8.5,30]; pi_holes=[58,23]; pi_z=43;           // 8.5 mm y-envelope allows a header
cam=[25,11.5,24]; cam_holes=[21,12.5]; eye_z=120; eye_x=13; cam_y=-20;
// Adafruit 3351 Mono Enclosed Speaker 3 W 4 Ω (Core A$8.95): 70 x 30 x 17, holes 3.4 on 63 x 24.
// Matches MAX98357A (3.2 W into 4 Ω at 5 V). The Ø28 placeholder and the 0.5 W 8 Ω mini are retired.
SPK=[70,17,30]; SPK_HOLES=[63,24];
// Adafruit 3006 MAX98357A published 19.4 x 17.8 x 3.0, plus ~8 mm for the post-2024 terminal block.
AMP=[19.4,17.8,3.0]; AMP_HEAD=8.0;
// Adafruit 3421 SPH0645LM4H breakout 16.7 x 12.7 x 1.8, bottom-ported, aligned to the mic hole.
MIC=[16.7,12.7,1.8];

module egg(c,h,w,d) translate([0,0,c]) scale([w/2,d/2,h/2]) sphere(1);
module tegg(o=0) egg(TH/2,TH-2*o,TW-2*o,TD-2*o);
module hegg(o=0) egg(HC,HH-2*o,HW-2*o,HD-2*o);
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
module seam_male_torso() intersection(){ torso_ribbon(LIP_IN, LIP_W); translate([-80,-LIP_H,-5]) cube([160,LIP_H,120]); below(tcut); }
module seam_fem_torso()  intersection(){ torso_ribbon(LIP_IN-SEAM_LIP_CLR, LIP_W+2*SEAM_LIP_CLR); translate([-80,-(LIP_H+SEAM_LIP_CLR),-5]) cube([160,LIP_H+SEAM_LIP_CLR+0.2,120]); below(tcut); }
module seam_male_head()  intersection(){ head_ribbon(LIP_IN, LIP_W); translate([-80,-LIP_H,-5]) cube([160,LIP_H,200]); above(hcut+3); }
module seam_fem_head()   intersection(){ head_ribbon(LIP_IN-SEAM_LIP_CLR, LIP_W+2*SEAM_LIP_CLR); translate([-80,-(LIP_H+SEAM_LIP_CLR),-5]) cube([160,LIP_H+SEAM_LIP_CLR+0.2,200]); above(hcut+3); }
module seam_chamfer_torso() intersection(){ difference(){ tegg(-SEAM_CHAMFER); tegg(0); } translate([-80,-0.5,-5]) cube([160,1.0,120]); below(tcut); }
module seam_chamfer_head()  intersection(){ difference(){ hegg(-SEAM_CHAMFER); hegg(0); } translate([-80,-0.5,-5]) cube([160,1.0,200]); above(hcut+3); }

/* ================= TORSO ================= */
tboss=[[-TW/2+12,22],[TW/2-12,22],[-TW/2+10,72],[TW/2-10,72]];
cboss=[[-16,-18],[16,-18],[-16,18],[16,18]];
// tray clamp ribs recentred on the 10 mm tabs at x=±34; rib 14 mm wide so the 10.6 pocket is fully in the rib
module torso_shell() intersection(){ difference(){ tegg(); tegg(tw); } below(tcut); }
module torso_add(){ intersection(){ tegg(0.1); union(){
  for(p=tboss) translate([p[0],0,p[1]]) rotate([90,0,0]) hull(){ cylinder(d=7,h=16,center=true); translate([sign(p[0])*12,0,0]) cylinder(d=7,h=16,center=true);}
  for(p=cboss) translate([p[0],p[1],tcut-10]) hull(){ cylinder(d=7,h=10); translate([0,sign(p[1])*14,0]) cylinder(d=7,h=10);}
  for(sx=[-1,1]) translate([sx*34,1.5,40]) cube([14,10,12],center=true);
  // speaker mounting bosses (63 x 24 hole rectangle), inside the front
  for(sx=[-1,1],sz=[-1,1]) translate([sx*SPK_HOLES[0]/2,-28,68+sz*SPK_HOLES[1]/2]) rotate([90,0,0]) cylinder(d=6,h=8,center=true);
  // mic pocket boss
  translate([18,-28,80]) rotate([90,0,0]) cylinder(d=8,h=8,center=true);
}}}
module torso_cuts_shared(){
  for(sx=[-1,1]) translate([sx*34,1.5,40]) cube([10.6,3.6,10.6],center=true);   // 0.3 mm per side around 10x3x10 tab (tab itself is 10x3x10)
  for(sx=[-1,1]) translate([sx*28.0,1.5,40]) cube([4.0,3.8,12.4],center=true);  // spine relief through the 12 mm rib, z covers the whole rib
  // Adafruit 3351 grille: 66 x 26 window + slots
  translate([0,-TD/2,68]) cube([66,30,26],center=true);
  for(sx=[-1,1],sz=[-1,1]) translate([sx*SPK_HOLES[0]/2,-28,68+sz*SPK_HOLES[1]/2]) rotate([90,0,0]) cylinder(d=3.4,h=16,center=true);
  // speaker body pocket (0.3 mm per side, 17 mm deep from the inner face)
  translate([0,-26,68]) cube([SPK[0]+0.6,SPK[1]+0.6,SPK[2]+0.6],center=true);
  // mic port + pocket: port through the shell, pocket for 16.7x12.7x1.8, port facing the hole
  translate([18,-TD/2,80]) rotate([90,0,0]) cylinder(d=2.4,h=30,center=true);
  translate([18,-30.5,80]) cube([MIC[0]+0.6,2.6,MIC[1]+0.6],center=true);
  // webbing slots: y starts behind the clasp servo (servo y<=26.05 at clasp_top=51)
  for(z=[15.5,30.5]) translate([0,36,z]) cube([22,28,3.2],center=true);
  cord_channels();
  // bench grommet + vents
  translate([0,30,8]) rotate([-70,0,0]) cylinder(d=8,h=30,center=true);
  for(sx=[-1,1],i=[0:2]) translate([sx*(26+i*4),30,45]) cube([2,30,12],center=true);
  // ribbon duct down the +x side of the yaw bore (15 x 1 FPC, 17 x 2.5 slot), torso side
  translate([14,0,tcut-8]) cube([17,2.5,16],center=true);
  translate([14,-6,60]) cube([17,2.5,30],center=true);
}
module torso_front() difference(){
  union(){ intersection(){ torso_shell(); F(); } intersection(){ torso_add(); F(); } }
  torso_cuts_shared();
  seam_fem_torso();
  seam_chamfer_torso();
  for(p=tboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_CLR,h=40,center=true);
  for(p=cboss) translate([p[0],p[1],tcut-12]) cylinder(d=M25_PIL,h=20);
  for(sx=[-1,1]) for(p=[[6,sh_z-5],[14,sh_z+5]]) translate([sx*44,p[0],p[1]]) rotate([0,90,0]) cylinder(d=M25_PIL,h=16,center=true);
}
module torso_back() difference(){
  union(){ intersection(){ torso_shell(); B(); } intersection(){ torso_add(); B(); } seam_male_torso(); }
  torso_cuts_shared();
  seam_chamfer_torso();
  for(p=tboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_PIL,h=40,center=true);
  for(p=cboss) translate([p[0],p[1],tcut-12]) cylinder(d=M25_PIL,h=20);
  for(sx=[-1,1]) for(p=[[6,sh_z-5],[14,sh_z+5]]) translate([sx*44,p[0],p[1]]) rotate([0,90,0]) cylinder(d=M25_PIL,h=16,center=true);
}

/* ================= TRAY ================= */
module tray() difference(){
  union(){
    translate([0,1.5,39]) cube([58,3,38],center=true);    // x=±29, flush with tab inner end, stays inside the 10.6 pockets
    for(sx=[-1,1]) translate([sx*34,1.5,40]) cube([10,3,10],center=true);         // 10 mm tabs, fully in 10.6 pockets
    for(sx=[-1,1],sz=[-1,1]) translate([sx*pi_holes[0]/2,-2,pi_z+sz*pi_holes[1]/2]) rotate([90,0,0]) cylinder(d=5,h=4,center=true);
    translate([0,9.9,23]) cube([36,14.2,6],center=true);                          // wrap bar
    // clasp servo shelf + thicker pilots (5 mm) at the official 27.7 mm hole span
    difference(){
      // 5 mm shelf UNDER the tabs (z = tab underside-5 .. tab underside). Screws from above through the tabs into 1.7 pilots.
      translate([-s_off-s_tab/2-3,2.9,clasp_top-s_tab_dz-5]) cube([s_tab+6,24,5]);
      translate(clasp_xy) translate([-s_off-sb[0]/2-clr,-sb[1]/2-clr,clasp_top-20]) cube([sb[0]+2*clr,sb[1]+2*clr,24]);
      translate(clasp_xy) cylinder(d=s_boss[0]+1,h=40);
    }
    // amp pocket on the +y face of the spine, clear of the clasp servo (y>=13.95) and the wrap bar (z<=26)
    translate([0,6.5,42]) cube([AMP[0]+4,6,AMP[1]+AMP_HEAD+4],center=true);
  }
  for(sx=[-1,1],sz=[-1,1]) translate([sx*pi_holes[0]/2,0,pi_z+sz*pi_holes[1]/2]) rotate([90,0,0]) cylinder(d=M25_CLR,h=12,center=true);
  translate(clasp_xy) servo_pilots(clasp_top);
  for(sx=[-1,1]) translate([sx*26,1.5,50]) cube([4,6,2.5],center=true);
  translate([0,6.5,42]) cube([AMP[0]+0.6,3.6,AMP[1]+0.4+AMP_HEAD],center=true);
  // two M2 pilots (assumed 15 x 13 span — MEASURE the board on arrival)
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

/* ================= HEAD ================= */
module head_shell() intersection(){ difference(){ hegg(); hegg(2.4); } above(hcut+3); }
hboss=[[-HW/2+12,hcut+12],[HW/2-12,hcut+12],[-HW/2+16,HC+20],[HW/2-16,HC+20]];
module head_bosses() intersection(){ hegg(0.1); above(hcut+3); for(p=hboss) translate([p[0],0,p[1]]) rotate([90,0,0]) hull(){ cylinder(d=7,h=16,center=true); translate([sign(p[0])*12,0,0]) cylinder(d=7,h=16,center=true);} }
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
module head_back() rotate(yaw) difference(){
  union(){
    intersection(){ head_shell(); B(); } intersection(){ head_bosses(); B(); }
    yaw_skirt_and_cone();
    translate([-2,24.6,tcut+4]) cube([4,3.4,4]);
    for(sy=[-1,1]) translate([-9, sy*(1.0+BLADE_CLR) - (sy<0?2:0), hcut-4]) cube([18,2,8]);  // slot y=-1.35..+1.35 (2.7)
    seam_male_head();
  }
  for(p=hboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_PIL,h=40,center=true);
  translate([23.8,0,RET_Z0+RET_H/2]) rotate([0,90,0]) cylinder(d=M2_PIL,h=12,center=true);
  translate([-23.8,0,RET_Z0+RET_H/2]) rotate([0,90,0]) cylinder(d=M2_PIL,h=12,center=true);
  translate([-9,10,hcut-1]) cube([18,4,10]);                 // servo/LED wires
  translate([14,0,hcut+2]) cube([17,2.5,16],center=true);    // ribbon floor slot (17 x 2.5)
  ribbon_loop_bay();
  seam_chamfer_head();
  // camera-side wire still has a front slot; keep a pass-through at the seam
  translate([-9,-14,hcut-1]) cube([18,4,10]);
}
module head_front() rotate(yaw) difference(){
  union(){ intersection(){ head_shell(); F(); } intersection(){ head_bosses(); F(); }
    intersection(){ hegg(0.1); F(); hull(){ translate([-eye_x,cam_y-1.5,eye_z]) cube([30,3,24],center=true); translate([-eye_x,cam_y-8,eye_z]) cube([30,3,24],center=true);} } }
  for(p=hboss) translate([p[0],0,p[1]]) rotate([90,0,0]) cylinder(d=M25_CLR,h=40,center=true);
  translate([-eye_x,cam_y,eye_z]) cube([cam[0]-6,10,cam[2]-6],center=true);
  for(sx=[-1,1],sz=[-1,1]) translate([-eye_x+sx*cam_holes[0]/2,cam_y,eye_z+sz*cam_holes[1]/2]) rotate([90,0,0]) cylinder(d=M25_CLR,h=12,center=true);
  for(sx=[-1,1]) translate([sx*eye_x,-HD/2-5,eye_z]) rotate([-90,0,0]) cylinder(d=21.6,h=14);
  ribbon_loop_bay();
  translate([14,-8,120]) cube([17,2.5,20],center=true);      // ribbon run camera -> loop
  seam_fem_head();
  seam_chamfer_head();
}

/* ================= CORD LINES (xy from scripts/design_params.py; z from the new drum stack) ================= */
drum_base = clasp_top + s_boss[1] + DRUM_ABOVE_BOSS;   // 51+4.3+4.0 = 59.3
zg_lo=drum_base+2.4; zg_hi=drum_base+6.0; zq=sh_z+1.5; // 61.7, 65.3, 63.5 — mid-groove = pulley, fleet ±1.8°
cordL=[[drum_pt_L[0],drum_pt_L[1],zg_lo],[pulley_pt_L[0],pulley_pt_L[1],zq]];
cordR=[[-drum_pt_R[0],drum_pt_R[1],zg_hi],[-pulley_pt_R[0],pulley_pt_R[1],zq]];
function lerp(a,b,t)=a+(b-a)*t;
function tx(c,x)=(x-c[0][0])/(c[1][0]-c[0][0]);
module chan(c,x0,x1,d=2.6) hull(){ translate(lerp(c[0],c[1],tx(c,x0))) sphere(d=d,$fn=16); translate(lerp(c[0],c[1],tx(c,x1))) sphere(d=d,$fn=16); }
module cord_channels(){ chan(cordL,30,52); chan(cordR,-30,-52); }

/* ================= ARMS (unchanged xy / paw / pulley from v2; zq still 63.5) ================= */
PIV=[piv_x,piv_y,sh_z];
pawz=[54,70]; beamz=[57,67];
R1=[piv_x+23*cos(root_local+th_c), piv_y+23*sin(root_local+th_c)];
BEAM=[R1,[76,42],[67,60],[40,65.5],[31,64.5]];
module cap(p,d=6,z=beamz,o=0) translate([p[0],p[1],z[0]-o]) cylinder(d=d+2*o,h=z[1]-z[0]+2*o,$fn=24);
module beam(o=0) for(i=[0:len(BEAM)-2]) hull(){ cap(BEAM[i],o=o); cap(BEAM[i+1],o=o); }
module paw_core(style){
  hull(){ translate([3.25,60,pawz[0]]) cube([31,3,pawz[1]-pawz[0]]);
          translate([3.25,60,pawz[0]]) cube([1,9,pawz[1]-pawz[0]]);
          if(style=="L") for(x=[10,30]) translate([x,64.5,pawz[0]]) cylinder(r=4.5,h=pawz[1]-pawz[0]);
          else { translate([12,65,pawz[0]]) cylinder(r=5,h=pawz[1]-pawz[0]); translate([30,63.5,pawz[0]+2]) cylinder(r=4,h=pawz[1]-pawz[0]-4); } }
  if(style=="L") for(x=[11,19,27]) translate([x,69.2,66]) sphere(d=5);
  else { for(x=[8,14,20,26]) translate([x,69.6,65]) sphere(d=4);
         translate([24,63.5,70]) sphere(d=8); }
}
pad_tip_x=-0.15; pad_strap_y=55.8;
module paw_pad_closed() union(){ translate([pad_tip_x,pad_strap_y,pawz[0]]) cube([3.25-pad_tip_x,69-pad_strap_y,pawz[1]-pawz[0]]); translate([3.25,pad_strap_y,pawz[0]]) cube([31,60-pad_strap_y,pawz[1]-pawz[0]]); }
module to_local() rotate(-th_c) translate(-PIV) children();
module pulley_hub(anchor){
  difference(){ union(){ cylinder(r=7.75,h=hub_h,center=true);
      translate([0,0,-hub_h/2]) cylinder(r=9.5,h=hub_h/2+0.7); translate([0,0,2.3]) cylinder(r=9.5,h=hub_h/2-2.3); }
    rotate(anchor) { translate([5.5,-0.6,0.7]) cube([4.5,1.2,1.6]); translate([5.5,0,0.7]) cylinder(d=3,h=5); } }
}
module arm_local(style,anchor) difference(){
  union(){
    pulley_hub(anchor);
    rotate(root_local) hull(){ translate([3,-2.5,-3.5]) cube([1,5,7]); translate([20,-2.5,-3.5]) cube([1,5,7]); }
    to_local(){ beam(); paw_core(style); }
    rotate(root_local) translate([24,0,4.9]) cylinder(d=3,h=6.6);
  }
  cylinder(d=3.4,h=30,center=true);
  to_local() for(t=[0.25,0.5,0.75]) translate(lerp([BEAM[1][0],BEAM[1][1],0],[BEAM[2][0],BEAM[2][1],0],t)+[0,0,62]) rotate([0,90,0]) cylinder(d=1.4,h=12,center=true);
}
function aside(side)=side=="L"?1:-1;
module mir(side) mirror([side=="L"?0:1,0,0]) children();
module arm(side) mir(side) translate(PIV) rotate(clasp) arm_local(side, side=="L"?anchor_local_L:anchor_local_R);
module paw_pad(side) mir(side) translate(PIV) rotate(clasp) to_local() paw_pad_closed();
module sleeve_proxy(side) mir(side) translate(PIV) rotate(clasp) to_local() beam(2);
module bracket_local() difference(){
  union(){
    for(z=[-ear_gap/2-3.8, ear_gap/2]) translate([0,0,z]) {
      hull(){ translate([-13,-8,0]) cube([1,22,3.8]); cylinder(d=22,h=3.8); }
      for(p=[[pillar_r,pillar_close_ang],[pillar_r,pillar_open_ang],[13,-90]]) hull(){ cylinder(d=22,h=3.8); rotate(p[1]) translate([p[0],0,0]) cylinder(d=6,h=3.8); } }
    translate([-16,-8,-ear_gap/2-3.8]) cube([4,22,ear_gap+7.6]);
    for(a=[pillar_close_ang,pillar_open_ang]) rotate(a) translate([pillar_r,0,-ear_gap/2-0.01]) cylinder(d=3,h=ear_gap+0.02);
    translate([0,-13,ear_gap/2+3.8]) translate([0,0,-0.3]) cylinder(d=3,h=11.8-ear_gap/2-3.8);
  }
  cylinder(d=3.2,h=30,center=true);
  for(p=[[-4,-5],[4,5]]) translate([-14,p[0],p[1]]) rotate([0,90,0]) cylinder(d=M25_CLR,h=10,center=true);
}
module shoulder_bracket(side) difference(){ mir(side) difference(){ translate(PIV) bracket_local(); tegg(-0.05); } cord_channels(); }

module clasp_drum() translate([clasp_xy[0],clasp_xy[1],drum_base]) rotate(-clasp*drum_ratio) difference(){
  union(){ cylinder(d=20,h=8.4); cylinder(d=24,h=1.2); translate([0,0,1.2]) cylinder(d=20,h=2.4); translate([0,0,3.6]) cylinder(d=24,h=1.2); translate([0,0,4.8]) cylinder(d=20,h=2.4); translate([0,0,7.2]) cylinder(d=24,h=1.2); }
  translate([0,0,-1]) cylinder(d=7,h=20); for(sx=[-1,1]) translate([sx*7,0,-1]) cylinder(d=2.3,h=4);  // horn-screw clearance
  translate([0,0,-1]) cylinder(d=3.2,h=20);                                                          // access for a longer M2.5 horn screw
  rotate(drum_anchor_L) { translate([6.5,-0.6,1.6]) cube([4,1.2,1.6]); translate([6.5,0,1.6]) cylinder(d=3,h=7); }
  rotate(drum_anchor_R) { translate([6.5,-0.6,5.2]) cube([4,1.2,1.6]); translate([6.5,0,5.2]) cylinder(d=3,h=4); }
}
module bezel() difference(){ union(){ cylinder(d=21,h=12); cylinder(d=27,h=1.6); } translate([0,0,-1]) cylinder(d=12,h=20); translate([-8,-1.1,2.2]) cube([30,2.2,2.4]); }
module shutter() union(){ translate([-6,-0.9,0]) cube([27,1.8,2]); cylinder(d=14,h=0.9); translate([20,-0.9,0]) cube([1.8,1.8,5]); }

/* ================= DUMMIES / PROXIES ================= */
module dummy_servo_yaw() servo_env(yaw_top);
module dummy_servo_clasp() translate(clasp_xy) servo_env(clasp_top);
module dummy_horn_yaw() translate([0,0,yaw_top+s_boss[1]]) horn_env();
module dummy_horn_clasp() translate([clasp_xy[0],clasp_xy[1],clasp_top+s_boss[1]]) horn_env();
module dummy_pi() translate([0,-4-pi[1]/2,pi_z]) cube(pi,center=true);
module dummy_cam() rotate(yaw) translate([-eye_x,cam_y+0.5+cam[1]/2,eye_z]) cube(cam,center=true);
module dummy_speaker() translate([0,-26,68]) cube(SPK,center=true);           // Adafruit 3351 70x17x30, 70 along x
module dummy_amp() translate([0,6.5,42]) cube([AMP[0],3.0,AMP[1]],center=true);
module dummy_mic() translate([18,-30.5,80]) cube([MIC[0],MIC[2],MIC[1]],center=true);
module dummies(){ dummy_servo_yaw(); dummy_servo_clasp(); dummy_horn_yaw(); dummy_horn_clasp();
  dummy_pi(); dummy_cam(); dummy_speaker(); dummy_amp(); dummy_mic(); }
module strap_env() translate([-28,44,20]) cube([56,12,90]);
module fur_proxy_torso() difference(){ intersection(){ difference(){ tegg(-4); tegg(0); } below(tcut); }
  for(sx=[-1,1]) translate([sx*57,10,62]) cube([30,34,26],center=true); }

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

if(part=="torso_front") torso_front(); else if(part=="torso_back") torso_back();
else if(part=="tray") tray(); else if(part=="yaw_collar") yaw_collar();
else if(part=="yaw_retainer_A") yaw_retainer_half(1); else if(part=="yaw_retainer_B") yaw_retainer_half(-1);
else if(part=="yaw_coupler") yaw_coupler(); else if(part=="yaw_thrust_washer") yaw_thrust_washer();
else if(part=="head_back") head_back(); else if(part=="head_front") head_front();
else if(part=="arm_L") arm("L"); else if(part=="arm_R") arm("R");
else if(part=="shoulder_bracket_L") shoulder_bracket("L"); else if(part=="shoulder_bracket_R") shoulder_bracket("R");
else if(part=="clasp_drum") clasp_drum(); else if(part=="bezel") bezel(); else if(part=="shutter") shutter();
else if(part=="dummies") dummies(); else if(part=="strap_env") strap_env();
else if(part=="paw_pad_L") paw_pad("L"); else if(part=="paw_pad_R") paw_pad("R");
else if(part=="sleeve_proxy_L") sleeve_proxy("L"); else if(part=="sleeve_proxy_R") sleeve_proxy("R");
else if(part=="fur_proxy_torso") fur_proxy_torso();
else if(part=="coupon") coupon();
else if(part=="dummy_servo_yaw") dummy_servo_yaw();
else if(part=="dummy_servo_clasp") dummy_servo_clasp();
else if(part=="dummy_horn_yaw") dummy_horn_yaw();
else if(part=="dummy_horn_clasp") dummy_horn_clasp();
else if(part=="dummy_pi") dummy_pi();
else if(part=="dummy_cam") dummy_cam();
else if(part=="dummy_speaker") dummy_speaker();
else if(part=="dummy_amp") dummy_amp();
else if(part=="dummy_mic") dummy_mic();
else { torso_front(); torso_back(); tray(); yaw_collar(); yaw_retainer_half(1); yaw_retainer_half(-1); yaw_coupler(); yaw_thrust_washer(); head_back(); head_front(); arm("L"); arm("R"); shoulder_bracket("L"); shoulder_bracket("R"); clasp_drum(); color("red") dummies(); color("pink") { paw_pad("L"); paw_pad("R"); } %strap_env(); }
