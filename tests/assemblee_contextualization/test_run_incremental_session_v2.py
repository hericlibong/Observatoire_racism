import json
import tempfile
import unittest
from pathlib import Path

from src.assemblee_contextualization.providers.mock_provider_v2 import MockContextualReviewProviderV2
from src.assemblee_contextualization.processing_journal import read_processing_journal
from src.assemblee_contextualization.runners.run_incremental_session_v2 import (
    IncrementalSessionError,
    build_dry_run_status,
    run_incremental_session,
)
from src.assemblee_contextualization.io_v2 import read_outputs_v2
from tests.assemblee_contextualization.test_context_builder import sample_interventions


def write_manifest(path: Path, sessions: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "source_url": "test",
                "archive_name": "test.zip",
                "generated_at": "2026-04-17T00:00:00+02:00",
                "initialization_from_date": "2026-04-02",
                "anchor_source_file": "CRSANR5L17S2026O1N191.xml",
                "sessions": sessions,
                "summary": {},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def session_payload(
    root: Path,
    source_file: str,
    seance_id: str,
    *,
    available_status: str = "available",
    already_processed: bool = False,
    journal_status: str = "not_processed",
) -> dict[str, object]:
    xml_path = root / source_file
    xml_path.write_text("<xml />", encoding="utf-8")
    return {
        "source_file": source_file,
        "seance_id": seance_id,
        "seance_date": "2026-04-07",
        "seance_date_label": "mardi 07 avril 2026",
        "local_path": str(xml_path),
        "content_hash": "hash",
        "available_status": available_status,
        "already_processed": already_processed,
        "journal_status": journal_status,
    }


def journal_entry(source_file: str, seance_id: str, status: str = "success") -> dict[str, object]:
    return {
        "seance_id": seance_id,
        "source_file": source_file,
        "seance_date": "2026-04-07",
        "seance_date_label": "mardi 07 avril 2026",
        "processed_at": "2026-04-17T00:00:00+02:00",
        "provider": "mistral_v2",
        "model_name": "mistral-medium-latest",
        "status": status,
        "outputs": [],
        "fallback_count": 0,
        "reviewed_items": 0,
        "error": "",
    }


def write_journal(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )


class RunIncrementalSessionV2Test(unittest.TestCase):
    def test_dry_run_on_candidate_does_not_call_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "source_manifest.json"
            journal_path = root / "processing_journal_v2.jsonl"
            output_dir = root / "outputs"
            write_manifest(
                manifest_path,
                [
                    session_payload(
                        root,
                        "CRSANR5L17S2026O1N192.xml",
                        "CRSANR5L17S2026O1N192",
                    )
                ],
            )

            status = build_dry_run_status(
                "CRSANR5L17S2026O1N192.xml",
                provider_name="mistral",
                manifest_path=manifest_path,
                journal_path=journal_path,
                output_dir=output_dir,
            )

            self.assertTrue(status["dry_run"])
            self.assertFalse(status["will_call_provider"])
            self.assertEqual(status["available_status"], "available")
            self.assertFalse(status["already_processed"])
            self.assertTrue(status["output_jsonl"].endswith("contextual_reviews_incremental_n192_v2_mistral.jsonl"))
            self.assertFalse(output_dir.exists())

    def test_refuses_already_journalized_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "source_manifest.json"
            journal_path = root / "processing_journal_v2.jsonl"
            write_manifest(
                manifest_path,
                [
                    session_payload(
                        root,
                        "CRSANR5L17S2026O1N192.xml",
                        "CRSANR5L17S2026O1N192",
                    )
                ],
            )
            write_journal(
                journal_path,
                [journal_entry("CRSANR5L17S2026O1N192.xml", "CRSANR5L17S2026O1N192")],
            )

            with self.assertRaises(IncrementalSessionError):
                build_dry_run_status(
                    "CRSANR5L17S2026O1N192.xml",
                    provider_name="mistral",
                    manifest_path=manifest_path,
                    journal_path=journal_path,
                )

    def test_refuses_conflict_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "source_manifest.json"
            journal_path = root / "processing_journal_v2.jsonl"
            write_manifest(
                manifest_path,
                [
                    session_payload(
                        root,
                        "CRSANR5L17S2026O1N191.xml",
                        "CRSANR5L17S2026O1N191",
                        available_status="conflict",
                    )
                ],
            )

            with self.assertRaises(IncrementalSessionError):
                build_dry_run_status(
                    "CRSANR5L17S2026O1N191.xml",
                    provider_name="mistral",
                    manifest_path=manifest_path,
                    journal_path=journal_path,
                )

    def test_refuses_real_run_without_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "source_manifest.json"
            journal_path = root / "processing_journal_v2.jsonl"
            output_dir = root / "outputs"
            write_manifest(
                manifest_path,
                [
                    session_payload(
                        root,
                        "CRSANR5L17S2026O1N192.xml",
                        "CRSANR5L17S2026O1N192",
                    )
                ],
            )

            with self.assertRaises(PermissionError):
                run_incremental_session(
                    "CRSANR5L17S2026O1N192.xml",
                    provider_name="mock",
                    confirm=False,
                    manifest_path=manifest_path,
                    journal_path=journal_path,
                    output_dir=output_dir,
                    provider=MockContextualReviewProviderV2(),
                    interventions_loader=lambda source_file: sample_interventions(),
                )

            self.assertFalse(output_dir.exists())
            self.assertFalse(journal_path.exists())

    def test_runs_one_session_with_mock_and_journalizes_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "source_manifest.json"
            journal_path = root / "processing_journal_v2.jsonl"
            output_dir = root / "outputs"
            write_manifest(
                manifest_path,
                [
                    session_payload(
                        root,
                        "CRSANR5L17S2026O1N192.xml",
                        "CRSANR5L17S2026O1N192",
                    ),
                    session_payload(
                        root,
                        "CRSANR5L17S2026O1N193.xml",
                        "CRSANR5L17S2026O1N193",
                    ),
                    session_payload(
                        root,
                        "CRSANR5L17S2026O1N194.xml",
                        "CRSANR5L17S2026O1N194",
                    ),
                ],
            )

            result = run_incremental_session(
                "CRSANR5L17S2026O1N192.xml",
                provider_name="mock",
                confirm=True,
                manifest_path=manifest_path,
                journal_path=journal_path,
                output_dir=output_dir,
                provider=MockContextualReviewProviderV2(),
                interventions_loader=lambda source_file: sample_interventions(),
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["reviewed_items"], 2)
            self.assertEqual(result["fallback_count"], 0)
            output_path = output_dir / "contextual_reviews_incremental_n192_v2_mock.jsonl"
            summary_path = output_dir / "contextual_reviews_incremental_n192_v2_mock_summary.json"
            self.assertTrue(output_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertEqual(len(read_outputs_v2(output_path)), 2)

            journal = read_processing_journal(journal_path)
            self.assertEqual([entry["source_file"] for entry in journal], ["CRSANR5L17S2026O1N192.xml"])
            self.assertEqual(journal[0]["status"], "success")
            self.assertEqual(journal[0]["reviewed_items"], 2)
            self.assertEqual(journal[0]["fallback_count"], 0)
            self.assertNotIn("CRSANR5L17S2026O1N193.xml", json.dumps(journal))
            self.assertNotIn("CRSANR5L17S2026O1N194.xml", json.dumps(journal))


if __name__ == "__main__":
    unittest.main()
