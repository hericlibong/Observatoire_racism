import unittest

from src.assemblee_contextualization.contracts import (
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
)
from src.assemblee_contextualization.mock_provider_v2 import MockContextualReviewProviderV2


class MockProviderV2Test(unittest.TestCase):
    def test_mock_provider_v2_returns_valid_contract_shape(self) -> None:
        provider = MockContextualReviewProviderV2()
        output = validate_review_output_v2(
            provider.review(
                {
                    "candidate_id": "c1",
                    "target": {
                        "texte": "Un passage candidat assez long pour servir d'extrait de test.",
                    },
                }
            )
        )

        self.assertEqual(output.candidate_id, "c1")
        self.assertEqual(output.scope_level, ScopeLevel.ADJACENT)
        self.assertEqual(output.signal_category, SignalCategory.AMBIGUOUS)
        self.assertFalse(output.is_fallback)
        self.assertTrue(output.needs_human_review)
        self.assertEqual(output.model_provider, "mock_v2")
        self.assertIn("passage candidat", output.evidence_span)


if __name__ == "__main__":
    unittest.main()
