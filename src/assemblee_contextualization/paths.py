from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
SOURCE_DIR = (
    ROOT_DIR
    / "data/raw/assemblee/extracted/syceron_initial_import/syseron.xml/xml/compteRendu"
)
INTERIM_DIR = ROOT_DIR / "data/interim/assemblee"
EXPORTS_D3_DIR = ROOT_DIR / "data/exports/d3"


def display_path(path: Path, root_dir: Path = ROOT_DIR) -> Path:
    try:
        return path.relative_to(root_dir)
    except ValueError:
        return path


def session_slug(source_file: str) -> str:
    stem = Path(source_file).stem.lower()
    marker = stem.rsplit("n", maxsplit=1)
    if len(marker) == 2 and marker[1].isdigit():
        return f"n{marker[1]}"
    return stem


def as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def normalize_syceron_date(raw_date: str, path: Path) -> str:
    if len(raw_date) < 8 or not raw_date[:8].isdigit():
        raise ValueError(f"dateSeance invalide dans {path} : {raw_date}")
    return date(
        int(raw_date[0:4]),
        int(raw_date[4:6]),
        int(raw_date[6:8]),
    ).isoformat()
