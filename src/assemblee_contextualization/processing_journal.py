from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .paths import INTERIM_DIR


JOURNAL_PATH = INTERIM_DIR / "processing_journal_v2.jsonl"
REQUIRED_FIELDS = {
    "seance_id",
    "source_file",
    "seance_date",
    "seance_date_label",
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
        _validate_entry(entry, line_number)
        entries.append(entry)
    return entries


def append_processing_journal_entry(entry: dict[str, Any], path: Path = JOURNAL_PATH) -> None:
    _validate_entry(entry, line_number=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def is_seance_already_processed(seance_id: str, path: Path = JOURNAL_PATH) -> bool:
    return any(
        entry.get("seance_id") == seance_id and entry.get("status") == "success"
        for entry in read_processing_journal(path)
    )


def _validate_entry(entry: dict[str, Any], line_number: int) -> None:
    missing = REQUIRED_FIELDS - entry.keys()
    if missing:
        raise ValueError(f"Journal de traitement incomplet ligne {line_number} : {sorted(missing)}")

    seance_date = str(entry["seance_date"])
    try:
        parsed_date = date.fromisoformat(seance_date)
    except ValueError as exc:
        raise ValueError(
            f"Date de seance invalide ligne {line_number} : {entry['seance_date']}"
        ) from exc
    if parsed_date.isoformat() != seance_date:
        raise ValueError(f"Date de seance non normalisee ligne {line_number} : {seance_date}")

    if not str(entry["seance_date_label"]).strip():
        raise ValueError(f"Libelle de date de seance vide ligne {line_number}.")
