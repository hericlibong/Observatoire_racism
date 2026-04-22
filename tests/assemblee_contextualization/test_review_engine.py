import unittest

from src.assemblee_contextualization.contracts import (
    Confidence,
    ContextualReviewOutputV2,
    ScopeLevel,
    SignalCategory,
)
from src.assemblee_contextualization.providers.mock_provider_v2 import MockContextualReviewProviderV2
from src.assemblee_contextualization.review_engine import (
    review_candidates_v2,
    select_review_ids,
    validate_fallback_invariants,
)
from tests.assemblee_contextualization.test_context_builder import sample_interventions


class ReviewEngineTest(unittest.TestCase):
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

    def test_select_review_ids_samples_when_no_rule_based_candidates(self) -> None:
        rows = [
            {**row, "signal_candidate": False, "signal_family": "", "signal_trigger": "", "signal_intensity": 0}
            for row in sample_interventions()
        ]

        review_ids, allow_non_candidates = select_review_ids(rows, sample_size_when_no_candidates=3)

        self.assertTrue(allow_non_candidates)
        self.assertEqual(len(review_ids), 3)

    def test_review_candidates_v2_can_review_sample_without_rule_based_candidates(self) -> None:
        rows = [
            {**row, "signal_candidate": False, "signal_family": "", "signal_trigger": "", "signal_intensity": 0}
            for row in sample_interventions()
        ]

        outputs = review_candidates_v2(
            rows,
            MockContextualReviewProviderV2(),
            source_file="pilot.xml",
            window=1,
            sample_size_when_no_candidates=2,
        )

        self.assertEqual(len(outputs), 2)
        self.assertTrue(all(output.signal_category == SignalCategory.AMBIGUOUS for output in outputs))

    def test_validate_fallback_invariants_accepts_authorized_fallback(self) -> None:
        validate_fallback_invariants([_fallback_output()])

    def test_validate_fallback_invariants_rejects_unauthorized_fallback(self) -> None:
        output = _fallback_output(confidence=Confidence.HIGH)

        with self.assertRaises(ValueError):
            validate_fallback_invariants([output])


def _fallback_output(*, confidence: Confidence = Confidence.LOW) -> ContextualReviewOutputV2:
    return ContextualReviewOutputV2(
        candidate_id="fallback",
        scope_level=ScopeLevel.HORS_PERIMETRE,
        signal_category=SignalCategory.AMBIGUOUS,
        is_fallback=True,
        needs_human_review=True,
        confidence=confidence,
        rationale="Fallback technique.",
        evidence_span="",
        limits=[],
        model_provider="test",
        model_name="test",
    )


if __name__ == "__main__":
    unittest.main()
