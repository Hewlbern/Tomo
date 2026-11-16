# SPDX-License-Identifier: MIT
"""Tomo (formerly evoKin V.01): egg profile + near-vertical centre belly-groove constants shared by cad/evokin_v01.scad
and scripts/sim_v01.py. Run it after changing the egg or the groove end points and paste the printed constants."""
import math, numpy as np
R=46.0; ZEQ=58.0; H=148.0; NUP=3.4
def eggr(z,o=0.0):
    if z<ZEQ: b=ZEQ-o; u=(z-ZEQ)/b; return (R-o)*math.sqrt(max(0.0,1-u*u))
    a=H-ZEQ-o; u=abs(z-ZEQ)/a; return (R-o)*max(0.0,1-u**NUP)**(1/NUP)
def on_egg(psi,z,off=0.0):
    r=eggr(z)+off; p=math.radians(psi); return np.array([r*math.cos(p),r*math.sin(p),z])
def normal(psi,z):
    dr=(eggr(z+0.2)-eggr(z-0.2))/0.4; p=math.radians(psi)
    n=np.array([math.cos(p),math.sin(p),-dr]); return n/np.linalg.norm(n)
# Two symmetric Mirumi-style arms meet in front of a near-VERTICAL handle at the front centre (azimuth -90). Floor line
# through a TOP point (z 80, 4 mm below the skin) and a BOTTOM point (z 48, 2.5 mm below) (Mirumi polish: raised with the hug), so it leans only ≈1.7 deg
# from vertical while the belly curves away below the equator. Shallow, so a Ø10 handle stands proud enough for the paws. FL = top end, FR = bottom end (names kept).
C_TOP=(-90.0,80.0,4.0); C_BOT=(-90.0,48.0,2.5)
FL=on_egg(*C_TOP[:2])-C_TOP[2]*normal(*C_TOP[:2]); FR=on_egg(*C_BOT[:2])-C_BOT[2]*normal(*C_BOT[:2])
U=(FL-FR)/np.linalg.norm(FL-FR)
N=normal(*C_TOP[:2])+normal(*C_BOT[:2]); N-=np.dot(N,U)*U; N/=np.linalg.norm(N)
MIDT=22.0                                           # handle test objects are centred here along the floor line (paw meeting, z ≈ 70: upper chest, Mirumi polish pass)
if __name__=="__main__":
    f=lambda v:"["+",".join(f"{x:.4f}" for x in v)+"]"
    print(f"G_FR={f(FR)}; G_FL={f(FL)};\nG_U={f(U)}; G_N={f(N)}; // {math.degrees(math.acos(U[2])):.1f} deg from vertical, floor span {np.linalg.norm(FL-FR):.2f} mm")
    for z in (26,57,82,100,101,110,120,124,128,131,134,138,145): print(z, round(eggr(z),2))
