import unittest

from src.assemblee_contextualization.legacy.mock_provider import MockContextualReviewProvider


class MockProviderTest(unittest.TestCase):
    def test_mock_provider_returns_stable_valid_shape(self) -> None:
        provider = MockContextualReviewProvider()
        output = provider.review(
            {
                "candidate_id": "c1",
                "target": {
                    "texte": "Un passage candidat assez long pour servir d'extrait de test.",
                },
            }
        )

        self.assertEqual(output["candidate_id"], "c1")
        self.assertEqual(output["decision"], "ambiguous")
        self.assertTrue(output["needs_human_review"])
        self.assertEqual(output["confidence"], "low")
        self.assertEqual(output["model_provider"], "mock")
        self.assertIn("passage candidat", output["evidence_span"])


if __name__ == "__main__":
    unittest.main()

