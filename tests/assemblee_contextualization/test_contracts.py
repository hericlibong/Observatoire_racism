import unittest

from src.assemblee_contextualization.contracts import (
    Confidence,
    Decision,
    validate_review_output,
)


class ContractsTest(unittest.TestCase):
    def test_accepts_valid_output(self) -> None:
        output = validate_review_output(
            {
                "candidate_id": "c1",
                "decision": "ambiguous",
                "needs_human_review": True,
                "confidence": "medium",
                "rationale": "Cas incertain.",
                "evidence_span": "extrait",
                "limits": ["Contexte local."],
                "model_provider": "mock",
                "model_name": "mock-v0",
            }
        )

        self.assertEqual(output.decision, Decision.AMBIGUOUS)
        self.assertEqual(output.confidence, Confidence.MEDIUM)

    def test_rejects_unknown_decision(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output(
                {
                    "candidate_id": "c1",
                    "decision": "needs_human_review",
                    "needs_human_review": True,
                    "confidence": "low",
                    "rationale": "",
                    "evidence_span": "",
                    "limits": [],
                    "model_provider": "mock",
                    "model_name": "mock-v0",
                }
            )

    def test_rejects_ambiguous_without_human_review(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output(
                {
                    "candidate_id": "c1",
                    "decision": "ambiguous",
                    "needs_human_review": False,
                    "confidence": "low",
                    "rationale": "",
                    "evidence_span": "",
                    "limits": [],
                    "model_provider": "mock",
                    "model_name": "mock-v0",
                }
            )

    def test_accepts_clear_false_positive_without_human_review(self) -> None:
        output = validate_review_output(
            {
                "candidate_id": "c1",
                "decision": "false_positive",
                "needs_human_review": False,
                "confidence": "high",
                "rationale": "Declencheur cite hors cible.",
                "evidence_span": "extrait",
                "limits": [],
                "model_provider": "mock",
                "model_name": "mock-v0",
            }
        )

        self.assertEqual(output.decision, Decision.FALSE_POSITIVE)
        self.assertFalse(output.needs_human_review)


if __name__ == "__main__":
    unittest.main()

