# SPDX-License-Identifier: MIT
"""Resolve an evoKin STL whether it lives in stl/, stl/templates/ or stl/reference/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Skin variants (soft goods only): TOMO_VARIANT=folitomo makes sim/audit scripts prefer stl/variants/folitomo/ and write their
# JSON/CSV under results/variants/folitomo/ so the default orange bear's results are never overwritten.
VARIANT = os.environ.get("TOMO_VARIANT", "").strip()
RES = f"results/variants/{VARIANT}/" if VARIANT else "results/"
if VARIANT:
    os.makedirs(ROOT / RES, exist_ok=True)
SEARCH_DIRS = (
    *((ROOT / "stl" / "variants" / VARIANT,) if VARIANT else ()),
    ROOT / "stl",
    ROOT / "stl" / "templates",
    ROOT / "stl" / "reference",
)


def stl_path(name: str) -> str:
    filename = name if str(name).endswith(".stl") else f"{name}.stl"
    filename = Path(filename).name
    for folder in SEARCH_DIRS:
        candidate = folder / filename
        if candidate.is_file():
            return str(candidate)
    searched = ", ".join(str(d) for d in SEARCH_DIRS)
    raise FileNotFoundError(f"{filename} not found in {searched}")
