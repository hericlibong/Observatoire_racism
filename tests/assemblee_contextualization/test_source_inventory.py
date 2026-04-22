import json
import tempfile
import unittest
from pathlib import Path

import pytest

from src.assemblee_contextualization.sources.source_acquisition import SessionXmlMetadata
from src.assemblee_contextualization.sources.source_inventory import (
    build_local_inventory_status,
    list_local_session_xmls,
    local_inventory_status_as_dict,
    parse_local_session_xml,
    read_journal_sessions,
)


XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">
  <uid>{seance_id}</uid>
  <metadonnees>
    <dateSeance>{raw_date}</dateSeance>
    <dateSeanceJour>{date_label}</dateSeanceJour>
  </metadonnees>
  <contenu />
</compteRendu>
"""


def write_xml(directory: Path, filename: str, seance_id: str, raw_date: str, date_label: str) -> None:
    (directory / filename).write_text(
        XML_TEMPLATE.format(seance_id=seance_id, raw_date=raw_date, date_label=date_label),
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


def test_local_inventory_uses_shared_session_xml_metadata(tmp_path: Path) -> None:
    xml_path = tmp_path / "CRSANR5L17S2026O1N191.xml"
    write_xml(
        tmp_path,
        xml_path.name,
        "CRSANR5L17S2026O1N191",
        "20260402110000000",
        "jeudi 02 avril 2026",
    )

    session = parse_local_session_xml(xml_path)
    sessions = list_local_session_xmls(tmp_path)
    status = build_local_inventory_status(tmp_path, tmp_path / "missing_journal.jsonl")
    payload = local_inventory_status_as_dict(status)

    assert isinstance(session, SessionXmlMetadata)
    assert isinstance(sessions[0], SessionXmlMetadata)
    assert payload["latest_local_session"] == {
        "source_file": "CRSANR5L17S2026O1N191.xml",
        "seance_id": "CRSANR5L17S2026O1N191",
        "seance_date": "2026-04-02",
        "seance_date_label": "jeudi 02 avril 2026",
        "local_path": str(xml_path),
    }


def test_local_inventory_raises_shared_metadata_error_for_invalid_xml(tmp_path: Path) -> None:
    invalid_path = tmp_path / "CRSANR5L17S2026O1N191.xml"
    invalid_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">
  <uid>CRSANR5L17S2026O1N191</uid>
  <metadonnees>
    <dateSeance>20260402110000000</dateSeance>
    <dateSeanceJour>jeudi 02 avril 2026</dateSeanceJour>
  </metadonnees>
</compteRendu>
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Bloc contenu introuvable"):
        list_local_session_xmls(tmp_path)


class SourceInventoryTest(unittest.TestCase):
    def test_lists_local_xmls_and_filters_from_april_2_2026(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory)
            write_xml(
                source_dir,
                "CRSANR5L17S2026O1N190.xml",
                "CRSANR5L17S2026O1N190",
                "20260401150000000",
                "mercredi 01 avril 2026",
            )
            write_xml(
                source_dir,
                "CRSANR5L17S2026O1N191.xml",
                "CRSANR5L17S2026O1N191",
                "20260402110000000",
                "jeudi 02 avril 2026",
            )

            sessions = list_local_session_xmls(source_dir)

            self.assertEqual([session.seance_id for session in sessions], ["CRSANR5L17S2026O1N191"])
            self.assertEqual(sessions[0].seance_date, "2026-04-02")
            self.assertEqual(sessions[0].seance_date_label, "jeudi 02 avril 2026")

    def test_reads_journal_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processing_journal_v2.jsonl"
            entry = journal_entry(
                "CRSANR5L17S2026O1N191",
                "CRSANR5L17S2026O1N191.xml",
                "2026-04-02",
                "jeudi 02 avril 2026",
            )
            path.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

            sessions = read_journal_sessions(path)

            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].seance_id, "CRSANR5L17S2026O1N191")
            self.assertEqual(sessions[0].status, "success")

    def test_reports_no_new_session_when_latest_local_is_processed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "xml"
            source_dir.mkdir()
            journal_path = Path(directory) / "processing_journal_v2.jsonl"
            write_xml(
                source_dir,
                "CRSANR5L17S2026O1N191.xml",
                "CRSANR5L17S2026O1N191",
                "20260402110000000",
                "jeudi 02 avril 2026",
            )
            journal_path.write_text(
                json.dumps(
                    journal_entry(
                        "CRSANR5L17S2026O1N191",
                        "CRSANR5L17S2026O1N191.xml",
                        "2026-04-02",
                        "jeudi 02 avril 2026",
                    ),
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            status = build_local_inventory_status(source_dir, journal_path)

            self.assertFalse(status.has_new_session)
            self.assertEqual(status.status_message, "aucune nouvelle séance à traiter")
            self.assertEqual(status.latest_local_session["seance_id"], "CRSANR5L17S2026O1N191")
            self.assertEqual(status.latest_processed_session["seance_id"], "CRSANR5L17S2026O1N191")
            self.assertEqual(status.candidate_sessions, [])

    def test_reports_new_local_session_not_in_journal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "xml"
            source_dir.mkdir()
            journal_path = Path(directory) / "processing_journal_v2.jsonl"
            write_xml(
                source_dir,
                "CRSANR5L17S2026O1N191.xml",
                "CRSANR5L17S2026O1N191",
                "20260402110000000",
                "jeudi 02 avril 2026",
            )
            write_xml(
                source_dir,
                "CRSANR5L17S2026O1N192.xml",
                "CRSANR5L17S2026O1N192",
                "20260403100000000",
                "vendredi 03 avril 2026",
            )
            journal_path.write_text(
                json.dumps(
                    journal_entry(
                        "CRSANR5L17S2026O1N191",
                        "CRSANR5L17S2026O1N191.xml",
                        "2026-04-02",
                        "jeudi 02 avril 2026",
                    ),
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            status = build_local_inventory_status(source_dir, journal_path)

            self.assertTrue(status.has_new_session)
            self.assertEqual(status.status_message, "1 nouvelle séance candidate")
            self.assertEqual(status.latest_local_session["seance_id"], "CRSANR5L17S2026O1N192")
            self.assertEqual(status.latest_processed_session["seance_id"], "CRSANR5L17S2026O1N191")
            self.assertEqual(
                [session["seance_id"] for session in status.candidate_sessions],
                ["CRSANR5L17S2026O1N192"],
            )

    def test_missing_journal_makes_all_filtered_local_sessions_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "xml"
            source_dir.mkdir()
            missing_journal = Path(directory) / "processing_journal_v2.jsonl"
            write_xml(
                source_dir,
                "CRSANR5L17S2026O1N191.xml",
                "CRSANR5L17S2026O1N191",
                "20260402110000000",
                "jeudi 02 avril 2026",
            )

            status = build_local_inventory_status(source_dir, missing_journal)

            self.assertTrue(status.has_new_session)
            self.assertEqual(status.status_message, "1 nouvelle séance candidate")
            self.assertIsNone(status.latest_processed_session)
            self.assertEqual(
                [session["seance_id"] for session in status.candidate_sessions],
                ["CRSANR5L17S2026O1N191"],
            )


if __name__ == "__main__":
    unittest.main()
