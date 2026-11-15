# SPDX-License-Identifier: MIT
"""Resolve an Evokin STL whether it lives in stl/, stl/templates/ or stl/reference/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH_DIRS = (
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
