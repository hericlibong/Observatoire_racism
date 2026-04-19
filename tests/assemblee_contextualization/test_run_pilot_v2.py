import csv
import tempfile
import unittest
from pathlib import Path

from src.assemblee_contextualization.mock_provider_v2 import MockContextualReviewProviderV2
from src.assemblee_contextualization.run_pilot_v2 import (
    OUTPUT_PATH,
    PILOT_SOURCE_FILE,
    build_provider,
    default_output_path,
    load_interventions_for_source,
)
from tests.assemblee_contextualization.test_context_builder import sample_interventions


class RunPilotV2Test(unittest.TestCase):
    def test_build_provider_returns_mock_provider(self) -> None:
        provider = build_provider("mock")

        self.assertIsInstance(provider, MockContextualReviewProviderV2)

    def test_build_provider_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError):
            build_provider("unknown")

    def test_default_output_path_keeps_legacy_pilot_mock_path(self) -> None:
        self.assertEqual(default_output_path(PILOT_SOURCE_FILE, "mock"), OUTPUT_PATH)

    def test_default_output_path_uses_session_slug_for_other_sources(self) -> None:
        output_path = default_output_path("CRSANR5L17S2026O1N205.xml", "mistral")

        self.assertEqual(output_path.name, "contextual_reviews_n205_v2_mistral.jsonl")

    def test_load_interventions_for_source_reads_input_csv(self) -> None:
        rows = sample_interventions()

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "interventions.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            loaded = load_interventions_for_source("ignored.xml", input_path)

        self.assertEqual([row["intervention_id"] for row in loaded], ["i1", "i2", "i3", "i4", "i5"])


if __name__ == "__main__":
    unittest.main()
