import json
import tempfile
import unittest
from pathlib import Path

from src.assemblee_contextualization.contracts import (
    ContextualReviewOutputV2,
    Confidence,
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
)
from src.assemblee_contextualization.mock_provider_v2 import MockContextualReviewProviderV2
from src.assemblee_contextualization.run_pilot_v2 import (
    review_candidates_v2,
    summarize_outputs_v2,
    validate_fallback_invariants,
    write_outputs_v2,
)
from tests.assemblee_contextualization.test_context_builder import sample_interventions


class RunPilotV2Test(unittest.TestCase):
    def test_review_candidates_v2_validates_outputs(self) -> None:
        outputs = review_candidates_v2(
            sample_interventions(),
            MockContextualReviewProviderV2(),
            source_file="pilot.xml",
            window=1,
        )

        self.assertEqual([output.candidate_id for output in outputs], ["i3", "i5"])
        self.assertTrue(all(not output.is_fallback for output in outputs))
        self.assertTrue(all(output.scope_level == ScopeLevel.ADJACENT for output in outputs))
        self.assertTrue(all(output.signal_category == SignalCategory.AMBIGUOUS for output in outputs))

    def test_write_outputs_v2_writes_valid_jsonl(self) -> None:
        outputs = review_candidates_v2(
            sample_interventions(),
            MockContextualReviewProviderV2(),
            source_file="pilot.xml",
            window=1,
        )

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "contextual_reviews_pilot_v2.jsonl"
            write_outputs_v2(outputs, output_path)
            lines = output_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 2)
        for line in lines:
            validate_review_output_v2(json.loads(line))

    def test_summary_keeps_fallback_out_of_substantive_hors_perimetre(self) -> None:
        fallback = ContextualReviewOutputV2(
            candidate_id="fallback",
            scope_level=ScopeLevel.HORS_PERIMETRE,
            signal_category=SignalCategory.AMBIGUOUS,
            is_fallback=True,
            needs_human_review=True,
            confidence=Confidence.LOW,
            rationale="Fallback technique.",
            evidence_span="",
            limits=[],
            model_provider="test",
            model_name="test",
        )
        hors_perimetre = ContextualReviewOutputV2(
            candidate_id="clear",
            scope_level=ScopeLevel.HORS_PERIMETRE,
            signal_category=SignalCategory.NO_SIGNAL,
            is_fallback=False,
            needs_human_review=False,
            confidence=Confidence.HIGH,
            rationale="Aucun ancrage dans le perimetre.",
            evidence_span="",
            limits=[],
            model_provider="test",
            model_name="test",
        )

        validate_fallback_invariants([fallback, hors_perimetre])
        summary = summarize_outputs_v2([fallback, hors_perimetre])

        self.assertEqual(summary["fallback_technical"], 1)
        self.assertEqual(summary["substantive_hors_perimetre"], 1)


if __name__ == "__main__":
    unittest.main()
