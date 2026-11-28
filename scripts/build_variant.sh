#!/bin/bash
# SPDX-License-Identifier: MIT
# Export the soft-goods parts of a skin variant (default: folitomo) to stl/variants/<variant>/.
# The printed parts, clasp and head mechanism are identical for every variant, so only the soft parts differ:
#   soft_head (head ball without the round fleece ears), fol_ear_L/R (leaf ears), fol_sprout, fol_bud, fol_tail.
# Then: python3 scripts/folitomo_check.py ; TOMO_VARIANT=folitomo python3 scripts/sim_v01.py && TOMO_VARIANT=folitomo python3 scripts/fit_audit.py
#       blender -b -P scripts/render_blender.py -- --final --variant folitomo
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
V="${1:-folitomo}"
OS="${OPENSCAD:-$(command -v openscad || true)}"; [ -n "$OS" ] || { echo "set OPENSCAD=/path/to/openscad" >&2; exit 1; }
mkdir -p "stl/variants/$V"
pids=()
for p in soft_head fol_ear_L fol_ear_R fol_sprout fol_bud fol_tail; do
  "$OS" -D "part=\"$p\"" -D "variant=\"$V\"" -D yaw=0 -D tilt=0 -D armL=0 -D armR=0 -o "stl/variants/$V/$p.stl" cad/evokin_v01.scad >/dev/null 2>&1 & pids+=($!)
done
for pid in "${pids[@]}"; do wait "$pid"; done
ls -la "stl/variants/$V"
