from __future__ import annotations

from typing import Any

from .providers import ContextualReviewProvider


class MockContextualReviewProvider(ContextualReviewProvider):
    model_provider = "mock"
    model_name = "mock-contextual-reviewer-v0"

    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        target_text = str(payload.get("target", {}).get("texte", ""))
        return {
            "candidate_id": payload["candidate_id"],
            "decision": "ambiguous",
            "needs_human_review": True,
            "confidence": "low",
            "rationale": "Provider mock : aucune analyse LLM reelle.",
            "evidence_span": target_text[:180],
            "limits": [
                "Sortie de test.",
                "Aucune recherche web effectuee.",
            ],
            "model_provider": self.model_provider,
            "model_name": self.model_name,
        }

