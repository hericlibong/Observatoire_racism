import json
import tempfile
import unittest
from pathlib import Path

from src.assemblee_contextualization.processing_journal import (
    is_seance_already_processed,
    read_processing_journal,
)


class ProcessingJournalTest(unittest.TestCase):
    def test_missing_journal_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processing_journal_v2.jsonl"

            self.assertEqual(read_processing_journal(path), [])
            self.assertFalse(is_seance_already_processed("CRSANR5L17S2026O1N191", path))

    def test_detects_successful_processed_seance(self) -> None:
        entry = {
            "seance_id": "CRSANR5L17S2026O1N191",
            "source_file": "CRSANR5L17S2026O1N191.xml",
            "seance_date": "2026-04-02",
            "seance_date_label": "jeudi 02 avril 2026",
            "processed_at": "2026-04-13T20:14:00+02:00",
            "provider": "mistral_v2",
            "model_name": "mistral-medium-latest",
            "status": "success",
            "outputs": ["data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl"],
            "fallback_count": 0,
            "reviewed_items": 26,
            "error": "",
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processing_journal_v2.jsonl"
            path.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

            self.assertEqual(read_processing_journal(path), [entry])
            self.assertTrue(is_seance_already_processed("CRSANR5L17S2026O1N191", path))
            self.assertFalse(is_seance_already_processed("CRSANR5L17S2026O1N192", path))

    def test_rejects_incomplete_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processing_journal_v2.jsonl"
            path.write_text(json.dumps({"seance_id": "CRSANR5L17S2026O1N191"}) + "\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_processing_journal(path)

    def test_rejects_invalid_seance_date(self) -> None:
        entry = {
            "seance_id": "CRSANR5L17S2026O1N191",
            "source_file": "CRSANR5L17S2026O1N191.xml",
            "seance_date": "20260402",
            "seance_date_label": "jeudi 02 avril 2026",
            "processed_at": "2026-04-13T20:14:00+02:00",
            "provider": "mistral_v2",
            "model_name": "mistral-medium-latest",
            "status": "success",
            "outputs": ["data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl"],
            "fallback_count": 0,
            "reviewed_items": 26,
            "error": "",
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processing_journal_v2.jsonl"
            path.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_processing_journal(path)


if __name__ == "__main__":
    unittest.main()
