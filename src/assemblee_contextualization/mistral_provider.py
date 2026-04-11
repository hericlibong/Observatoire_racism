from __future__ import annotations

import json
import os
from typing import Any

from .contracts import validate_review_output
from .env import load_dotenv
from .providers import ContextualReviewProvider


DEFAULT_MISTRAL_MODEL = "mistral-medium-latest"


SYSTEM_PROMPT = """Tu es un agent de relecture contextuelle locale pour le projet OBSERVATOIRE.
Tu relis un passage candidat deja repere par des regles deterministes.
Tu ne fais aucune recherche web.
Tu ne conclus jamais automatiquement qu'un passage est raciste, discriminatoire ou haineux.
Tu aides uniquement a distinguer un signal pertinent, un faux positif ou un cas ambigu.
Tu dois repondre uniquement avec un objet JSON strict conforme au contrat demande."""


USER_PROMPT_TEMPLATE = """Relis le payload JSON suivant.

Contraintes:
- Analyse uniquement le passage cible et son contexte local.
- Ne produis pas de verdict moral definitif.
- decision doit etre exactement une des valeurs suivantes: validated_signal, false_positive, ambiguous.
- confidence doit etre exactement une des valeurs suivantes: low, medium, high.
- ambiguous implique needs_human_review=true.
- validated_signal implique needs_human_review=true en v0.
- false_positive peut avoir needs_human_review=false si le cas est clair.
- evidence_span doit etre un court extrait du texte utilise pour la decision.
- limits doit mentionner les limites utiles, dont l'absence de recherche web.

Retourne uniquement un objet JSON avec ces champs:
candidate_id, decision, needs_human_review, confidence, rationale, evidence_span, limits, model_provider, model_name.

Payload:
{payload_json}
"""


class MistralContextualReviewProvider(ContextualReviewProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        load_dotenv()
        self.api_key = api_key if api_key is not None else os.environ.get("MISTRAL_API_KEY", "")
        self.model = model or os.environ.get("MISTRAL_MODEL", DEFAULT_MISTRAL_MODEL)
        self.client = client

    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            self._validate_payload(payload)
            if not self.api_key and self.client is None:
                return self._fallback(payload, "MISTRAL_API_KEY absent.")
            raw_output = self._call_mistral(payload)
            parsed = json.loads(raw_output)
            parsed["candidate_id"] = str(parsed.get("candidate_id") or payload["candidate_id"])
            parsed["model_provider"] = "mistral"
            parsed["model_name"] = self.model
            return validate_review_output(parsed).to_dict()
        except (json.JSONDecodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
            return self._fallback(payload, f"Sortie Mistral invalide ou non conforme : {exc}")
        except Exception as exc:
            return self._fallback(payload, f"Erreur appel Mistral : {exc}")

    def _call_mistral(self, payload: dict[str, Any]) -> str:
        client = self.client or self._create_client()
        response = client.chat.complete(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        payload_json=json.dumps(payload, ensure_ascii=False, indent=2)
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return self._extract_content(response)

    def _create_client(self) -> Any:
        from mistralai.client import Mistral

        return Mistral(api_key=self.api_key)

    @staticmethod
    def _extract_content(response: Any) -> str:
        content = response.choices[0].message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
        return str(content)

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        required_top_level = {"candidate_id", "source", "target", "rule_based_signal", "local_context"}
        missing = required_top_level - payload.keys()
        if missing:
            raise ValueError(f"Payload Mistral incomplet : {sorted(missing)}")
        required_target = {"ordre", "orateur_nom", "point_titre", "sous_point_titre", "texte"}
        target = payload.get("target")
        if not isinstance(target, dict):
            raise ValueError("target doit etre un objet.")
        missing_target = required_target - target.keys()
        if missing_target:
            raise ValueError(f"target incomplet : {sorted(missing_target)}")

    def _fallback(self, payload: dict[str, Any], rationale: str) -> dict[str, Any]:
        candidate_id = str(payload.get("candidate_id", "unknown"))
        target = payload.get("target", {})
        target_text = target.get("texte", "") if isinstance(target, dict) else ""
        fallback = {
            "candidate_id": candidate_id,
            "decision": "ambiguous",
            "needs_human_review": True,
            "confidence": "low",
            "rationale": rationale,
            "evidence_span": str(target_text)[:180],
            "limits": [
                "Fallback sur sortie sure.",
                "Analyse limitee au contexte local.",
                "Aucune recherche web effectuee.",
            ],
            "model_provider": "mistral",
            "model_name": self.model,
        }
        return validate_review_output(fallback).to_dict()
