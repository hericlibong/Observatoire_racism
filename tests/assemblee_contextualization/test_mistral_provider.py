import json
import unittest

from src.assemblee_contextualization.legacy.mistral_provider import MistralContextualReviewProvider


def payload() -> dict:
    return {
        "candidate_id": "c1",
        "source": {
            "source_file": "pilot.xml",
            "seance_id": "s1",
            "intervention_id": "c1",
        },
        "target": {
            "ordre": 1,
            "orateur_nom": "Orateur",
            "point_titre": "Point",
            "sous_point_titre": "Sous-point",
            "texte": "Texte cible avec un declencheur.",
        },
        "rule_based_signal": {
            "signal_candidate": True,
            "signal_family": "devalorisation",
            "signal_trigger": "declencheur",
            "signal_intensity": 2,
        },
        "local_context": {
            "previous": [],
            "next": [],
        },
    }


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [FakeChoice(content)]


class FakeChat:
    def __init__(self, content: str) -> None:
        self.content = content
        self.last_kwargs = {}

    def complete(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeResponse(self.content)


class FakeClient:
    def __init__(self, content: str) -> None:
        self.chat = FakeChat(content)


class MistralProviderTest(unittest.TestCase):
    def test_valid_response_is_validated(self) -> None:
        client = FakeClient(
            json.dumps(
                {
                    "candidate_id": "c1",
                    "decision": "false_positive",
                    "needs_human_review": False,
                    "confidence": "high",
                    "rationale": "Usage hors cible.",
                    "evidence_span": "Texte cible",
                    "limits": ["Contexte local."],
                    "model_provider": "ignored",
                    "model_name": "ignored",
                }
            )
        )
        provider = MistralContextualReviewProvider(api_key="test-key", model="test-model", client=client)

        output = provider.review(payload())

        self.assertEqual(output["decision"], "false_positive")
        self.assertEqual(output["model_provider"], "mistral")
        self.assertEqual(output["model_name"], "test-model")
        self.assertEqual(client.chat.last_kwargs["response_format"], {"type": "json_object"})

    def test_string_limits_are_normalized_before_validation(self) -> None:
        client = FakeClient(
            json.dumps(
                {
                    "candidate_id": "c1",
                    "decision": "validated_signal",
                    "needs_human_review": True,
                    "confidence": "high",
                    "rationale": "Signal pertinent dans le contexte local.",
                    "evidence_span": "Texte cible",
                    "limits": "Analyse limitee au contexte local.",
                    "model_provider": "ignored",
                    "model_name": "ignored",
                }
            )
        )
        provider = MistralContextualReviewProvider(api_key="test-key", model="test-model", client=client)

        output = provider.review(payload())

        self.assertEqual(output["decision"], "validated_signal")
        self.assertEqual(output["limits"], ["Analyse limitee au contexte local."])

    def test_mixed_limits_are_normalized_before_validation(self) -> None:
        client = FakeClient(
            json.dumps(
                {
                    "candidate_id": "c1",
                    "decision": "false_positive",
                    "needs_human_review": False,
                    "confidence": "medium",
                    "rationale": "Faux positif clair.",
                    "evidence_span": "Texte cible",
                    "limits": ["Contexte local.", 123],
                    "model_provider": "ignored",
                    "model_name": "ignored",
                }
            )
        )
        provider = MistralContextualReviewProvider(api_key="test-key", model="test-model", client=client)

        output = provider.review(payload())

        self.assertEqual(output["limits"], ["Contexte local.", "123"])

    def test_candidate_id_is_forced_from_payload(self) -> None:
        client = FakeClient(
            json.dumps(
                {
                    "candidate_id": "wrong-id",
                    "decision": "false_positive",
                    "needs_human_review": False,
                    "confidence": "medium",
                    "rationale": "Faux positif clair.",
                    "evidence_span": "Texte cible",
                    "limits": ["Contexte local."],
                    "model_provider": "ignored",
                    "model_name": "ignored",
                }
            )
        )
        provider = MistralContextualReviewProvider(api_key="test-key", model="test-model", client=client)

        output = provider.review(payload())

        self.assertEqual(output["candidate_id"], "c1")

    def test_missing_api_key_uses_safe_fallback(self) -> None:
        provider = MistralContextualReviewProvider(api_key="", model="test-model")

        output = provider.review(payload())

        self.assertEqual(output["decision"], "ambiguous")
        self.assertTrue(output["needs_human_review"])
        self.assertEqual(output["confidence"], "low")
        self.assertIn("MISTRAL_API_KEY absent", output["rationale"])

    def test_invalid_response_uses_safe_fallback(self) -> None:
        provider = MistralContextualReviewProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient("pas du json"),
        )

        output = provider.review(payload())

        self.assertEqual(output["decision"], "ambiguous")
        self.assertTrue(output["needs_human_review"])
        self.assertEqual(output["confidence"], "low")
        self.assertIn("Sortie Mistral invalide", output["rationale"])

    def test_invalid_payload_uses_safe_fallback(self) -> None:
        provider = MistralContextualReviewProvider(api_key="test-key", model="test-model")

        output = provider.review({"candidate_id": "c1"})

        self.assertEqual(output["decision"], "ambiguous")
        self.assertTrue(output["needs_human_review"])
        self.assertEqual(output["candidate_id"], "c1")


if __name__ == "__main__":
    unittest.main()
