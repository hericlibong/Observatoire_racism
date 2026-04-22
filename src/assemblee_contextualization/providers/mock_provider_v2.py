from __future__ import annotations

from typing import Any

from ..contracts import validate_review_output_v2
from . import ContextualReviewProvider


class MockContextualReviewProviderV2(ContextualReviewProvider):
    model_provider = "mock_v2"
    model_name = "mock-contextual-reviewer-v2-minimal"

    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        target_text = str(payload.get("target", {}).get("texte", ""))
        output = {
            "candidate_id": payload["candidate_id"],
            "scope_level": "adjacent",
            "signal_category": "ambiguous",
            "is_fallback": False,
            "needs_human_review": True,
            "confidence": "low",
            "rationale": (
                "Provider V2 minimal deterministe : cas conserve pour revue humaine, "
                "sans qualification substantielle automatique."
            ),
            "evidence_span": target_text[:180],
            "limits": [
                "Sortie V2 minimale de stabilisation.",
                "Analyse limitee au contexte local.",
                "Aucune recherche web effectuee.",
            ],
            "model_provider": self.model_provider,
            "model_name": self.model_name,
        }
        return validate_review_output_v2(output).to_dict()
