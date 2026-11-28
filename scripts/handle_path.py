# SPDX-License-Identifier: MIT
"""Robot-frame centre line (mm) of the Ø12.5 bag handle used in the Blender renders and the Folitomo clearance check.
Its upright leg rises out of the bag top straight up the centre belly groove between the paws, then peels off over the
critter's right shoulder (-x) and slightly back so it passes beside the head, then arches over into the bag.
bpy-free so scripts/render_blender.py and scripts/folitomo_check.py share one definition."""
import numpy as np
import groove_geo as gg

HANDLE_D = 12.5
G_FR = np.array(gg.FR, float); G_U = np.array(gg.U, float); G_N = np.array(gg.N, float)


def handle_points(variant="orange"):
    r = HANDLE_D / 2.0 + 0.15
    T1 = 36.0
    pts = [G_FR + G_U * (-52.0 + (T1 + 52.0) * k / 40.0) + G_N * r for k in range(41)]
    p0 = pts[-1]
    ctrl = [pts[-2], p0,
            np.array([-6.0, p0[1] - 4.0, 95.0]),
            np.array([-28.0, p0[1] - 10.0, 106.0]),
            np.array([-56.0, p0[1] - 4.0, 120.0]),
            np.array([-72.0, p0[1] + 14.0, 138.0]),
            np.array([-86.0, p0[1] + 34.0, 160.0]),
            np.array([-112.0, p0[1] + 46.0, 180.0]),
            np.array([-150.0, p0[1] + 48.0, 178.0]),
            np.array([-180.0, p0[1] + 44.0, 142.0]),
            np.array([-188.0, p0[1] + 42.0, 80.0])]
    for i in range(1, len(ctrl) - 2):
        a, b, c, d = ctrl[i - 1], ctrl[i], ctrl[i + 1], ctrl[i + 2]
        for k in range(1, 13):
            u = k / 12.0
            pts.append(0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3))
    last = pts[-1]
    for k in range(1, 13):
        pts.append(np.array([last[0], last[1], last[2] - (last[2] + 8.0) * k / 12.0]))
    return [tuple(float(x) for x in p) for p in pts]
