#!/bin/bash
# SPDX-License-Identifier: MIT
# Export evoKin V.01 parts at yaw=0, armL=-15, armR=-25 (forearms overlapped across the middle).
# Printable STLs go to stl/, fit dummies and fur/sleeve proxies to stl/reference/.
# Set EXPORT_CHECK=1 to also write imposed-pose intermediates to check/
# (used by scripts/sim_v01.py to validate its transforms; not checked in).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -n "${OPENSCAD:-}" ]; then
  OS="$OPENSCAD"
elif command -v openscad >/dev/null 2>&1; then
  OS="$(command -v openscad)"
else
  echo "OpenSCAD not found. Install OpenSCAD 2021.01+ and/or set OPENSCAD=/path/to/openscad" >&2
  exit 1
fi

mkdir -p stl stl/reference
SCAD="cad/evokin_v01.scad"

run_os() {
  # STL export does not need a display. Retry once in case a parallel run trips over a temp file.
  "$OS" "$@" >/dev/null 2>&1 || "$OS" "$@" >/dev/null 2>&1
}
export_part() { run_os -D "part=\"$1\"" -D yaw=0 -D armL=-15 -D armR=-25 -o "$2" "$SCAD"; }

PRINT="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer head_back head_front arm_L arm_R shoulder_bracket_L shoulder_bracket_R bezel shutter coupon"
REFERENCE="dummies dummy_servo_yaw dummy_horn_yaw dummy_servo_arm_L dummy_servo_arm_R dummy_horn_arm_L dummy_horn_arm_R dummy_pi dummy_cam dummy_speaker dummy_amp dummy_mic fur_proxy_torso sleeve_proxy_L sleeve_proxy_R"

pids=()
for p in $PRINT; do export_part "$p" "stl/$p.stl" & pids+=($!); done
for p in $REFERENCE; do export_part "$p" "stl/reference/$p.stl" & pids+=($!); done
for pid in "${pids[@]}"; do wait "$pid"; done

if [ "${EXPORT_CHECK:-0}" = "1" ]; then
  mkdir -p check
  rm -f check/*.stl
  pids=()
  for a in 30 -45 0; do
    run_os -D 'part="arm_L"' -D yaw=0 -D armL=$a -D armR=-25 -o "check/arm_L_a${a}.stl" "$SCAD" & pids+=($!)
    run_os -D 'part="arm_R"' -D yaw=0 -D armL=-15 -D armR=$a -o "check/arm_R_a${a}.stl" "$SCAD" & pids+=($!)
  done
  for p in head_back head_front yaw_coupler; do
    run_os -D "part=\"$p\"" -D yaw=30 -D armL=-15 -D armR=-25 -o "check/${p}_y30.stl" "$SCAD" & pids+=($!)
  done
  for pid in "${pids[@]}"; do wait "$pid"; done
  ls -la check
fi

echo "Exported STLs:"
ls -la stl stl/reference
