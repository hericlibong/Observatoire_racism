from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from src.build_assemblee_pilot import ROOT_DIR, SOURCE_DIR


JOURNAL_PATH = ROOT_DIR / "data/interim/assemblee/processing_journal_v2.jsonl"
DEFAULT_START_DATE = date(2026, 4, 2)


@dataclass(frozen=True)
class LocalSessionXml:
    source_file: str
    seance_id: str
    seance_date: str
    seance_date_label: str
    local_path: str


@dataclass(frozen=True)
class JournalSession:
    seance_id: str
    source_file: str
    seance_date: str
    seance_date_label: str
    status: str


@dataclass(frozen=True)
class LocalInventoryStatus:
    latest_local_session: dict[str, str] | None
    latest_processed_session: dict[str, str] | None
    candidate_sessions: list[dict[str, str]]
    has_new_session: bool
    status_message: str


def list_local_session_xmls(
    source_dir: Path = SOURCE_DIR,
    start_date: date = DEFAULT_START_DATE,
) -> list[LocalSessionXml]:
    sessions: list[LocalSessionXml] = []
    if not source_dir.exists():
        return sessions

    for path in sorted(source_dir.glob("*.xml")):
        session = parse_local_session_xml(path)
        if date.fromisoformat(session.seance_date) >= start_date:
            sessions.append(session)

    return sorted(sessions, key=_session_sort_key)


def parse_local_session_xml(path: Path) -> LocalSessionXml:
    seance_id = ""
    raw_date = ""
    seance_date_label = ""

    for event, element in ET.iterparse(path, events=("end",)):
        tag = element.tag.split("}")[-1]
        text = "".join(element.itertext()).strip()
        if tag == "uid" and not seance_id:
            seance_id = text
        elif tag == "dateSeance" and not raw_date:
            raw_date = text
        elif tag == "dateSeanceJour" and not seance_date_label:
            seance_date_label = text

        if seance_id and raw_date and seance_date_label:
            break
        element.clear()

    if not seance_id:
        raise ValueError(f"UID introuvable dans {path}.")
    seance_date = _normalize_syceron_date(raw_date, path)
    if not seance_date_label:
        raise ValueError(f"Libelle dateSeanceJour introuvable dans {path}.")

    return LocalSessionXml(
        source_file=path.name,
        seance_id=seance_id,
        seance_date=seance_date,
        seance_date_label=seance_date_label,
        local_path=str(path),
    )


def read_journal_sessions(path: Path = JOURNAL_PATH) -> list[JournalSession]:
    if not path.exists():
        return []

    sessions: list[JournalSession] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        entry = json.loads(line)
        sessions.append(_journal_session_from_entry(entry, line_number))

    return sorted(sessions, key=_session_sort_key)


def build_local_inventory_status(
    source_dir: Path = SOURCE_DIR,
    journal_path: Path = JOURNAL_PATH,
    start_date: date = DEFAULT_START_DATE,
) -> LocalInventoryStatus:
    local_sessions = list_local_session_xmls(source_dir, start_date)
    journal_sessions = [
        session
        for session in read_journal_sessions(journal_path)
        if date.fromisoformat(session.seance_date) >= start_date and session.status == "success"
    ]
    processed_ids = {session.seance_id for session in journal_sessions}
    candidates = [session for session in local_sessions if session.seance_id not in processed_ids]

    latest_local = local_sessions[-1] if local_sessions else None
    latest_processed = journal_sessions[-1] if journal_sessions else None
    count = len(candidates)

    if count == 0:
        status_message = "aucune nouvelle séance à traiter"
    elif count == 1:
        status_message = "1 nouvelle séance candidate"
    else:
        status_message = f"{count} nouvelles séances candidates"

    return LocalInventoryStatus(
        latest_local_session=_session_to_dict(latest_local),
        latest_processed_session=_session_to_dict(latest_processed),
        candidate_sessions=[_session_to_dict(session) for session in candidates],
        has_new_session=count > 0,
        status_message=status_message,
    )


def local_inventory_status_as_dict(status: LocalInventoryStatus) -> dict[str, Any]:
    return asdict(status)


def _journal_session_from_entry(entry: dict[str, Any], line_number: int) -> JournalSession:
    required = {"seance_id", "source_file", "seance_date", "seance_date_label", "status"}
    missing = required - entry.keys()
    if missing:
        raise ValueError(f"Journal de traitement incomplet ligne {line_number} : {sorted(missing)}")

    seance_date = str(entry["seance_date"])
    try:
        date.fromisoformat(seance_date)
    except ValueError as exc:
        raise ValueError(f"Date de seance invalide ligne {line_number} : {seance_date}") from exc

    return JournalSession(
        seance_id=str(entry["seance_id"]),
        source_file=str(entry["source_file"]),
        seance_date=seance_date,
        seance_date_label=str(entry["seance_date_label"]),
        status=str(entry["status"]),
    )


def _normalize_syceron_date(raw_date: str, path: Path) -> str:
    if len(raw_date) < 8 or not raw_date[:8].isdigit():
        raise ValueError(f"dateSeance invalide dans {path} : {raw_date}")
    return date(
        int(raw_date[0:4]),
        int(raw_date[4:6]),
        int(raw_date[6:8]),
    ).isoformat()


def _session_sort_key(session: LocalSessionXml | JournalSession) -> tuple[str, str]:
    return session.seance_date, session.seance_id


def _session_to_dict(session: LocalSessionXml | JournalSession | None) -> dict[str, str] | None:
    if session is None:
        return None
    payload = {
        "source_file": session.source_file,
        "seance_id": session.seance_id,
        "seance_date": session.seance_date,
        "seance_date_label": session.seance_date_label,
    }
    if isinstance(session, LocalSessionXml):
        payload["local_path"] = session.local_path
    if isinstance(session, JournalSession):
        payload["journal_status"] = session.status
    return payload
