from __future__ import annotations

import json
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.assemblee_contextualization.paths import (
    INTERIM_DIR,
    ROOT_DIR,
    SOURCE_DIR,
    display_path,
)
from src.assemblee_contextualization.processing_journal import (
    JOURNAL_PATH,
    read_processing_journal,
)
from src.assemblee_contextualization.source_acquisition import (
    extract_session_xml_from_zip,
    file_sha256,
    read_session_xml_metadata,
)
from src.assemblee_contextualization.source_inventory import DEFAULT_START_DATE


SOURCE_URL = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/"
    "syceronbrut/syseron.xml.zip"
)
ARCHIVE_PATH = ROOT_DIR / "data/raw/assemblee/zips/syseron.xml.zip"
MANIFEST_PATH = INTERIM_DIR / "source_manifest.json"
ANCHOR_SOURCE_FILE = "CRSANR5L17S2026O1N191.xml"


@dataclass(frozen=True)
class ZipSessionCandidate:
    member_name: str
    source_file: str
    seance_id: str
    seance_date: str
    seance_date_label: str


def build_source_manifest(
    *,
    zip_path: Path = ARCHIVE_PATH,
    destination_dir: Path = SOURCE_DIR,
    journal_path: Path = JOURNAL_PATH,
    source_url: str = SOURCE_URL,
    start_date: date = DEFAULT_START_DATE,
    anchor_source_file: str = ANCHOR_SOURCE_FILE,
    generated_at: str | None = None,
) -> dict[str, Any]:
    journal_status_by_session = _journal_status_by_session(journal_path)
    candidates, archive_xml_count, ignored_before_threshold_count = _read_zip_candidates(
        zip_path,
        start_date,
    )

    sessions = []
    extracted_from_zip: list[str] = []
    already_present: list[str] = []
    conflict_sessions: list[str] = []
    error_sessions: list[str] = []

    for candidate in sorted(candidates, key=lambda item: (item.seance_date, item.seance_id)):
        local_path = destination_dir / candidate.source_file
        available_status = "available"
        content_hash = ""

        try:
            import_result = extract_session_xml_from_zip(
                zip_path,
                candidate.member_name,
                destination_dir,
            )
            if import_result.status == "imported":
                extracted_from_zip.append(candidate.source_file)
            elif import_result.status == "already_exists":
                already_present.append(candidate.source_file)

            metadata = read_session_xml_metadata(local_path)
            content_hash = file_sha256(local_path)
            seance_id = metadata.seance_id
            seance_date = metadata.seance_date
            seance_date_label = metadata.seance_date_label
        except FileExistsError:
            available_status = "conflict"
            conflict_sessions.append(candidate.source_file)
            seance_id = candidate.seance_id
            seance_date = candidate.seance_date
            seance_date_label = candidate.seance_date_label
            if local_path.exists():
                content_hash = file_sha256(local_path)
        except ValueError:
            available_status = "error"
            error_sessions.append(candidate.source_file)
            seance_id = candidate.seance_id
            seance_date = candidate.seance_date
            seance_date_label = candidate.seance_date_label

        journal_status = journal_status_by_session.get(seance_id, "not_processed")
        already_processed = journal_status != "not_processed"
        sessions.append(
            {
                "source_file": candidate.source_file,
                "seance_id": seance_id,
                "seance_date": seance_date,
                "seance_date_label": seance_date_label,
                "local_path": _project_relative_path(local_path),
                "content_hash": content_hash,
                "available_status": available_status,
                "already_processed": already_processed,
                "journal_status": journal_status,
            }
        )

    candidate_sessions = [
        session["source_file"]
        for session in sessions
        if _is_processing_candidate(session, start_date)
    ]

    return {
        "source_url": source_url,
        "archive_name": zip_path.name,
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "initialization_from_date": start_date.isoformat(),
        "anchor_source_file": anchor_source_file,
        "sessions": sessions,
        "summary": {
            "archive_xml_count": archive_xml_count,
            "ignored_before_threshold_count": ignored_before_threshold_count,
            "total_sessions_from_threshold": len(sessions),
            "available_sessions": sum(
                1 for session in sessions if session["available_status"] == "available"
            ),
            "already_processed_sessions": sum(
                1 for session in sessions if session["already_processed"]
            ),
            "candidate_sessions_count": len(candidate_sessions),
            "candidate_sessions": candidate_sessions,
            "extracted_from_zip_count": len(extracted_from_zip),
            "extracted_from_zip_sessions": extracted_from_zip,
            "already_present_sessions": already_present,
            "conflict_sessions": conflict_sessions,
            "error_sessions": error_sessions,
        },
    }


def write_source_manifest(manifest: dict[str, Any], path: Path = MANIFEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_and_write_source_manifest(
    *,
    zip_path: Path = ARCHIVE_PATH,
    destination_dir: Path = SOURCE_DIR,
    journal_path: Path = JOURNAL_PATH,
    manifest_path: Path = MANIFEST_PATH,
    source_url: str = SOURCE_URL,
    start_date: date = DEFAULT_START_DATE,
    anchor_source_file: str = ANCHOR_SOURCE_FILE,
) -> dict[str, Any]:
    manifest = build_source_manifest(
        zip_path=zip_path,
        destination_dir=destination_dir,
        journal_path=journal_path,
        source_url=source_url,
        start_date=start_date,
        anchor_source_file=anchor_source_file,
    )
    write_source_manifest(manifest, manifest_path)
    return manifest


def main() -> None:
    manifest = build_and_write_source_manifest()
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))


def _read_zip_candidates(
    zip_path: Path,
    start_date: date,
) -> tuple[list[ZipSessionCandidate], int, int]:
    candidates: list[ZipSessionCandidate] = []
    ignored_before_threshold_count = 0

    with zipfile.ZipFile(zip_path) as archive:
        member_names = sorted(
            member.filename
            for member in archive.infolist()
            if not member.is_dir() and Path(member.filename).name.endswith(".xml")
        )

        for member_name in member_names:
            metadata = _read_zip_member_metadata(archive, member_name)
            if date.fromisoformat(metadata.seance_date) < start_date:
                ignored_before_threshold_count += 1
                continue

            candidates.append(
                ZipSessionCandidate(
                    member_name=member_name,
                    source_file=metadata.source_file,
                    seance_id=metadata.seance_id,
                    seance_date=metadata.seance_date,
                    seance_date_label=metadata.seance_date_label,
                )
            )

    return candidates, len(member_names), ignored_before_threshold_count


def _read_zip_member_metadata(
    archive: zipfile.ZipFile,
    member_name: str,
):
    payload = archive.read(member_name)
    with tempfile.TemporaryDirectory() as tmp_dir:
        temporary_path = Path(tmp_dir) / Path(member_name).name
        temporary_path.write_bytes(payload)
        return read_session_xml_metadata(temporary_path)


def _journal_status_by_session(journal_path: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for entry in read_processing_journal(journal_path):
        statuses[str(entry["seance_id"])] = str(entry["status"])
    return statuses


def _is_processing_candidate(session: dict[str, Any], start_date: date) -> bool:
    return (
        session["available_status"] == "available"
        and not session["already_processed"]
        and date.fromisoformat(str(session["seance_date"])) >= start_date
    )


def _project_relative_path(path: Path) -> str:
    return str(display_path(path))


if __name__ == "__main__":
    main()
