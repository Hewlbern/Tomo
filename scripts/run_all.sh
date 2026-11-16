#!/bin/bash
# SPDX-License-Identifier: MIT
set -euo pipefail
cd "$(dirname "$0")/.."
EXPORT_CHECK=1 bash scripts/build_stl.sh
python3 scripts/sim_v01.py        # imposed-motion sweep (head pan + tilt + both passive arms), a few minutes
python3 scripts/fit_audit.py     # reads results/summary_sweep.json for the joint rows
python3 scripts/metrics_v01.py
python3 scripts/validation_summary.py
python3 scripts/render_v01.py
