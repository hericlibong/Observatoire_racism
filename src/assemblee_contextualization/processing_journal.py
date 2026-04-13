from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
JOURNAL_PATH = ROOT_DIR / "data/interim/assemblee/processing_journal_v2.jsonl"
REQUIRED_FIELDS = {
    "seance_id",
    "source_file",
    "processed_at",
    "provider",
    "model_name",
    "status",
    "outputs",
    "fallback_count",
    "reviewed_items",
    "error",
}


def read_processing_journal(path: Path = JOURNAL_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        entry = json.loads(line)
        missing = REQUIRED_FIELDS - entry.keys()
        if missing:
            raise ValueError(f"Journal de traitement incomplet ligne {line_number} : {sorted(missing)}")
        entries.append(entry)
    return entries


def is_seance_already_processed(seance_id: str, path: Path = JOURNAL_PATH) -> bool:
    return any(
        entry.get("seance_id") == seance_id and entry.get("status") == "success"
        for entry in read_processing_journal(path)
    )
