import unittest
from typing import Any

from src.assemblee_contextualization.mock_provider import MockContextualReviewProvider
from src.assemblee_contextualization.providers import ContextualReviewProvider
from src.assemblee_contextualization.reviewer import ContextualReviewer
from tests.assemblee_contextualization.test_context_builder import sample_interventions


class FalsePositiveProvider(ContextualReviewProvider):
    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "candidate_id": payload["candidate_id"],
            "decision": "false_positive",
            "needs_human_review": False,
            "confidence": "high",
            "rationale": "Cas clair.",
            "evidence_span": payload["target"]["texte"],
            "limits": [],
            "model_provider": "test",
            "model_name": "false-positive-v0",
        }


class InvalidValidatedProvider(ContextualReviewProvider):
    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "candidate_id": payload["candidate_id"],
            "decision": "validated_signal",
            "needs_human_review": False,
            "confidence": "high",
            "rationale": "Invalide en v0.",
            "evidence_span": payload["target"]["texte"],
            "limits": [],
            "model_provider": "test",
            "model_name": "invalid-v0",
        }


class ReviewerDecisionsTest(unittest.TestCase):
    def test_reviewer_orchestrates_context_and_mock_provider(self) -> None:
        reviewer = ContextualReviewer(
            MockContextualReviewProvider(),
            source_file="pilot.xml",
            window=1,
        )
        output = reviewer.review_candidate(sample_interventions(), "i3")

        self.assertEqual(output.candidate_id, "i3")
        self.assertEqual(output.decision.value, "ambiguous")
        self.assertTrue(output.needs_human_review)

    def test_reviewer_accepts_clear_false_positive(self) -> None:
        reviewer = ContextualReviewer(FalsePositiveProvider(), source_file="pilot.xml")
        output = reviewer.review_candidate(sample_interventions(), "i3")

        self.assertEqual(output.decision.value, "false_positive")
        self.assertFalse(output.needs_human_review)

    def test_reviewer_rejects_validated_signal_without_human_review(self) -> None:
        reviewer = ContextualReviewer(InvalidValidatedProvider(), source_file="pilot.xml")

        with self.assertRaises(ValueError):
            reviewer.review_candidate(sample_interventions(), "i3")


if __name__ == "__main__":
    unittest.main()
