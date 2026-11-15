#!/bin/bash
# SPDX-License-Identifier: MIT
# Export v3 parts at yaw=0 clasp=0 (open).
# Printable STLs go to stl/, foam templates to stl/templates/,
# fit dummies and fur/sleeve proxies to stl/reference/.
# Set EXPORT_CHECK=1 to also write imposed-pose intermediates to check/
# (those files are used by scripts/sim_v3.py and are not checked in).
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

mkdir -p stl stl/templates stl/reference
SCAD="cad/critter_v3.scad"

export_part() {
  local part="$1" dest="$2"
  if command -v xvfb-run >/dev/null 2>&1; then
    xvfb-run -a "$OS" -D "part=\"$part\"" -D yaw=0 -D clasp=0 -o "$dest" "$SCAD" >/dev/null 2>&1
  else
    "$OS" -D "part=\"$part\"" -D yaw=0 -D clasp=0 -o "$dest" "$SCAD" >/dev/null 2>&1
  fi
}

PRINT="torso_front torso_back tray yaw_collar yaw_retainer_A yaw_retainer_B yaw_coupler yaw_thrust_washer head_back head_front arm_L arm_R shoulder_bracket_L shoulder_bracket_R clasp_drum bezel shutter coupon"
TEMPLATES="paw_pad_L paw_pad_R"
REFERENCE="dummies dummy_servo_yaw dummy_servo_clasp dummy_horn_yaw dummy_horn_clasp dummy_pi dummy_cam dummy_speaker dummy_amp dummy_mic fur_proxy_torso sleeve_proxy_L sleeve_proxy_R strap_env"

pids=()
for p in $PRINT; do
  export_part "$p" "stl/$p.stl" &
  pids+=($!)
done
for p in $TEMPLATES; do
  export_part "$p" "stl/templates/$p.stl" &
  pids+=($!)
done
for p in $REFERENCE; do
  export_part "$p" "stl/reference/$p.stl" &
  pids+=($!)
done
for pid in "${pids[@]}"; do wait "$pid"; done

if [ "${EXPORT_CHECK:-0}" = "1" ]; then
  mkdir -p check
  run_os() {
    if command -v xvfb-run >/dev/null 2>&1; then
      xvfb-run -a "$OS" "$@" >/dev/null 2>&1
    else
      "$OS" "$@" >/dev/null 2>&1
    fi
  }
  pids=()
  for p in arm_L arm_R paw_pad_L paw_pad_R clasp_drum; do
    for c in 45 46 -3; do
      dest="check/${p}_c${c}.stl"
      part_path="stl/$p.stl"
      [ -f "stl/templates/$p.stl" ] && part_path="stl/templates/$p.stl"
      run_os -D "part=\"$p\"" -D yaw=0 -D clasp="$c" -o "$dest" "$SCAD" &
      pids+=($!)
    done
  done
  for pid in "${pids[@]}"; do wait "$pid"; done
  pids=()
  for p in head_back head_front yaw_coupler; do
    run_os -D "part=\"$p\"" -D yaw=45 -D clasp=45 -o "check/${p}_y45_c45.stl" "$SCAD" &
    pids+=($!)
  done
  for pid in "${pids[@]}"; do wait "$pid"; done
  ls -la check
fi

echo "Exported STLs:"
ls -la stl stl/templates stl/reference
