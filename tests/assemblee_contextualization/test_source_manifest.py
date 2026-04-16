import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from src.assemblee_contextualization.source_manifest import (
    build_source_manifest,
    write_source_manifest,
)


XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">
  <uid>{seance_id}</uid>
  <metadonnees>
    <dateSeance>{raw_date}</dateSeance>
    <dateSeanceJour>{date_label}</dateSeanceJour>
  </metadonnees>
  <contenu>{content}</contenu>
</compteRendu>
"""


def xml_payload(
    seance_id: str,
    raw_date: str,
    date_label: str,
    content: str = "",
) -> str:
    return XML_TEMPLATE.format(
        seance_id=seance_id,
        raw_date=raw_date,
        date_label=date_label,
        content=content,
    )


def write_zip(zip_path: Path, files: dict[str, str]) -> None:
    with zipfile.ZipFile(zip_path, "w") as archive:
        for source_file, payload in files.items():
            archive.writestr(f"syseron.xml/xml/compteRendu/{source_file}", payload)


def write_journal(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )


def journal_entry(
    seance_id: str,
    source_file: str,
    seance_date: str,
    seance_date_label: str,
    status: str = "success",
) -> dict[str, object]:
    return {
        "seance_id": seance_id,
        "source_file": source_file,
        "seance_date": seance_date,
        "seance_date_label": seance_date_label,
        "processed_at": "2026-04-13T20:14:00+02:00",
        "provider": "mistral_v2",
        "model_name": "mistral-medium-latest",
        "status": status,
        "outputs": [],
        "fallback_count": 0,
        "reviewed_items": 0,
        "error": "",
    }


class SourceManifestTest(unittest.TestCase):
    def test_builds_manifest_from_zip_and_filters_before_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            zip_path = root / "syseron.xml.zip"
            destination_dir = root / "raw"
            journal_path = root / "processing_journal_v2.jsonl"
            write_zip(
                zip_path,
                {
                    "CRSANR5L17S2026O1N190.xml": xml_payload(
                        "CRSANR5L17S2026O1N190",
                        "20260401150000000",
                        "mercredi 01 avril 2026",
                    ),
                    "CRSANR5L17S2026O1N191.xml": xml_payload(
                        "CRSANR5L17S2026O1N191",
                        "20260402110000000",
                        "jeudi 02 avril 2026",
                    ),
                    "CRSANR5L17S2026O1N192.xml": xml_payload(
                        "CRSANR5L17S2026O1N192",
                        "20260403100000000",
                        "vendredi 03 avril 2026",
                    ),
                },
            )
            write_journal(
                journal_path,
                [
                    journal_entry(
                        "CRSANR5L17S2026O1N191",
                        "CRSANR5L17S2026O1N191.xml",
                        "2026-04-02",
                        "jeudi 02 avril 2026",
                    )
                ],
            )

            manifest = build_source_manifest(
                zip_path=zip_path,
                destination_dir=destination_dir,
                journal_path=journal_path,
                start_date=date(2026, 4, 2),
                generated_at="2026-04-16T00:00:00+00:00",
            )

            self.assertEqual(manifest["initialization_from_date"], "2026-04-02")
            self.assertEqual(
                [session["source_file"] for session in manifest["sessions"]],
                ["CRSANR5L17S2026O1N191.xml", "CRSANR5L17S2026O1N192.xml"],
            )
            self.assertTrue((destination_dir / "CRSANR5L17S2026O1N191.xml").exists())
            self.assertTrue((destination_dir / "CRSANR5L17S2026O1N192.xml").exists())
            self.assertFalse((destination_dir / "CRSANR5L17S2026O1N190.xml").exists())
            self.assertEqual(manifest["summary"]["ignored_before_threshold_count"], 1)
            self.assertEqual(manifest["summary"]["total_sessions_from_threshold"], 2)
            self.assertEqual(manifest["summary"]["already_processed_sessions"], 1)
            self.assertEqual(manifest["summary"]["candidate_sessions_count"], 1)
            self.assertEqual(
                manifest["summary"]["candidate_sessions"],
                ["CRSANR5L17S2026O1N192.xml"],
            )

    def test_manifest_marks_journal_status_and_candidate_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            zip_path = root / "syseron.xml.zip"
            destination_dir = root / "raw"
            journal_path = root / "processing_journal_v2.jsonl"
            write_zip(
                zip_path,
                {
                    "CRSANR5L17S2026O1N191.xml": xml_payload(
                        "CRSANR5L17S2026O1N191",
                        "20260402110000000",
                        "jeudi 02 avril 2026",
                    ),
                    "CRSANR5L17S2026O1N192.xml": xml_payload(
                        "CRSANR5L17S2026O1N192",
                        "20260403100000000",
                        "vendredi 03 avril 2026",
                    ),
                },
            )
            write_journal(
                journal_path,
                [
                    journal_entry(
                        "CRSANR5L17S2026O1N191",
                        "CRSANR5L17S2026O1N191.xml",
                        "2026-04-02",
                        "jeudi 02 avril 2026",
                    )
                ],
            )

            manifest = build_source_manifest(
                zip_path=zip_path,
                destination_dir=destination_dir,
                journal_path=journal_path,
            )
            by_file = {session["source_file"]: session for session in manifest["sessions"]}

            self.assertTrue(by_file["CRSANR5L17S2026O1N191.xml"]["already_processed"])
            self.assertEqual(by_file["CRSANR5L17S2026O1N191.xml"]["journal_status"], "success")
            self.assertFalse(by_file["CRSANR5L17S2026O1N192.xml"]["already_processed"])
            self.assertEqual(by_file["CRSANR5L17S2026O1N192.xml"]["journal_status"], "not_processed")
            self.assertEqual(manifest["summary"]["candidate_sessions"], ["CRSANR5L17S2026O1N192.xml"])

    def test_marks_hash_conflict_for_existing_local_xml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            zip_path = root / "syseron.xml.zip"
            destination_dir = root / "raw"
            journal_path = root / "processing_journal_v2.jsonl"
            destination_dir.mkdir()
            write_zip(
                zip_path,
                {
                    "CRSANR5L17S2026O1N191.xml": xml_payload(
                        "CRSANR5L17S2026O1N191",
                        "20260402110000000",
                        "jeudi 02 avril 2026",
                        "zip-version",
                    )
                },
            )
            (destination_dir / "CRSANR5L17S2026O1N191.xml").write_text(
                xml_payload(
                    "CRSANR5L17S2026O1N191",
                    "20260402110000000",
                    "jeudi 02 avril 2026",
                    "local-version",
                ),
                encoding="utf-8",
            )
            write_journal(journal_path, [])

            manifest = build_source_manifest(
                zip_path=zip_path,
                destination_dir=destination_dir,
                journal_path=journal_path,
            )

            self.assertEqual(manifest["sessions"][0]["available_status"], "conflict")
            self.assertEqual(
                manifest["summary"]["conflict_sessions"],
                ["CRSANR5L17S2026O1N191.xml"],
            )
            self.assertEqual(manifest["summary"]["candidate_sessions"], [])

    def test_writes_manifest_without_modifying_journal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            zip_path = root / "syseron.xml.zip"
            destination_dir = root / "raw"
            journal_path = root / "processing_journal_v2.jsonl"
            manifest_path = root / "source_manifest.json"
            write_zip(
                zip_path,
                {
                    "CRSANR5L17S2026O1N191.xml": xml_payload(
                        "CRSANR5L17S2026O1N191",
                        "20260402110000000",
                        "jeudi 02 avril 2026",
                    )
                },
            )
            write_journal(
                journal_path,
                [
                    journal_entry(
                        "CRSANR5L17S2026O1N191",
                        "CRSANR5L17S2026O1N191.xml",
                        "2026-04-02",
                        "jeudi 02 avril 2026",
                    )
                ],
            )
            before_journal = journal_path.read_text(encoding="utf-8")
            manifest = build_source_manifest(
                zip_path=zip_path,
                destination_dir=destination_dir,
                journal_path=journal_path,
            )

            write_source_manifest(manifest, manifest_path)

            self.assertEqual(journal_path.read_text(encoding="utf-8"), before_journal)
            self.assertTrue(manifest_path.exists())
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("sessions", saved)
            self.assertEqual(saved["summary"]["candidate_sessions_count"], 0)

    def test_manifest_generation_does_not_create_v2_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            zip_path = root / "syseron.xml.zip"
            destination_dir = root / "raw"
            journal_path = root / "processing_journal_v2.jsonl"
            write_zip(
                zip_path,
                {
                    "CRSANR5L17S2026O1N192.xml": xml_payload(
                        "CRSANR5L17S2026O1N192",
                        "20260403100000000",
                        "vendredi 03 avril 2026",
                    )
                },
            )
            write_journal(journal_path, [])

            build_source_manifest(
                zip_path=zip_path,
                destination_dir=destination_dir,
                journal_path=journal_path,
            )

            self.assertEqual(
                [path.name for path in destination_dir.iterdir()],
                ["CRSANR5L17S2026O1N192.xml"],
            )


if __name__ == "__main__":
    unittest.main()
