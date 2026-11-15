#!/bin/bash
# SPDX-License-Identifier: MIT
cd "$(dirname "$0")/.."
python3 scripts/design_params.py
bash scripts/build_stl.sh
python3 scripts/fit_audit.py
python3 scripts/sim_v3.py
python3 scripts/metrics_v3.py
python3 scripts/render_v3.py
