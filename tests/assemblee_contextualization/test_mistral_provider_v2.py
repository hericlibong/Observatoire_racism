import json
import unittest

from src.assemblee_contextualization.mistral_provider_v2 import MistralContextualReviewProviderV2


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


class MistralProviderV2Test(unittest.TestCase):
    def test_valid_response_is_validated(self) -> None:
        client = FakeClient(
            json.dumps(
                {
                    "candidate_id": "c1",
                    "scope_level": "hors_perimetre",
                    "signal_category": "no_signal",
                    "is_fallback": False,
                    "needs_human_review": False,
                    "confidence": "high",
                    "rationale": "Critique procedurale sans groupe du perimetre.",
                    "evidence_span": "Texte cible",
                    "limits": ["Analyse locale."],
                    "model_provider": "ignored",
                    "model_name": "ignored",
                }
            )
        )
        provider = MistralContextualReviewProviderV2(api_key="test-key", model="test-model", client=client)

        output = provider.review(payload())

        self.assertEqual(output["scope_level"], "hors_perimetre")
        self.assertEqual(output["signal_category"], "no_signal")
        self.assertFalse(output["is_fallback"])
        self.assertEqual(output["model_provider"], "mistral_v2")
        self.assertEqual(output["model_name"], "test-model")
        self.assertEqual(client.chat.last_kwargs["response_format"], {"type": "json_object"})

    def test_missing_api_key_uses_v2_fallback(self) -> None:
        provider = MistralContextualReviewProviderV2(api_key="", model="test-model")

        output = provider.review(payload())

        self.assertEqual(output["scope_level"], "hors_perimetre")
        self.assertEqual(output["signal_category"], "ambiguous")
        self.assertTrue(output["is_fallback"])
        self.assertTrue(output["needs_human_review"])
        self.assertEqual(output["confidence"], "low")
        self.assertIn("MISTRAL_API_KEY absent", output["rationale"])

    def test_invalid_response_uses_v2_fallback(self) -> None:
        provider = MistralContextualReviewProviderV2(
            api_key="test-key",
            model="test-model",
            client=FakeClient("pas du json"),
        )

        output = provider.review(payload())

        self.assertEqual(output["scope_level"], "hors_perimetre")
        self.assertEqual(output["signal_category"], "ambiguous")
        self.assertTrue(output["is_fallback"])
        self.assertEqual(output["confidence"], "low")
        self.assertIn("Sortie Mistral V2 invalide", output["rationale"])

    def test_invalid_contract_response_uses_v2_fallback(self) -> None:
        client = FakeClient(
            json.dumps(
                {
                    "candidate_id": "c1",
                    "scope_level": "hors_perimetre",
                    "signal_category": "ambiguous",
                    "is_fallback": False,
                    "needs_human_review": True,
                    "confidence": "low",
                    "rationale": "Combinaison invalide.",
                    "evidence_span": "Texte cible",
                    "limits": ["Analyse locale."],
                    "model_provider": "ignored",
                    "model_name": "ignored",
                }
            )
        )
        provider = MistralContextualReviewProviderV2(api_key="test-key", model="test-model", client=client)

        output = provider.review(payload())

        self.assertTrue(output["is_fallback"])
        self.assertEqual(output["scope_level"], "hors_perimetre")
        self.assertEqual(output["signal_category"], "ambiguous")


if __name__ == "__main__":
    unittest.main()
