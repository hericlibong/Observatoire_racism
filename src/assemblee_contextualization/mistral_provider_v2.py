from __future__ import annotations

import json
import os
from typing import Any

from .contracts import validate_review_output_v2
from .env import DEFAULT_MISTRAL_MODEL, load_dotenv
from .providers import ContextualReviewProvider


SYSTEM_PROMPT_V2 = """Tu es un agent de relecture contextuelle locale pour le projet OBSERVATOIRE.
Tu relis un passage parlementaire dans son contexte local.
Tu ne fais aucune recherche web.
Tu ne produis jamais de verdict moral et tu ne qualifies jamais definitivement un propos comme raciste, discriminatoire, xenophobe ou haineux.
Tu qualifies seulement un niveau de perimetre et une categorie de signal a revoir.
Tu dois repondre uniquement avec un objet JSON strict conforme au contrat V2 demande."""


USER_PROMPT_TEMPLATE_V2 = """Relis le payload JSON suivant.

Perimetre strict de l'observatoire:
- haine;
- racisme;
- xenophobie;
- discrimination;
- ciblage problematique de groupes lies notamment a l'origine, la nationalite, l'ethnicite reelle ou supposee, la religion, ou a des categories comparables du meme perimetre discriminatoire.

Contraintes:
- Analyse uniquement le passage cible et son contexte local.
- Ne produis pas de verdict moral.
- N'elargis pas core a une tension politique ordinaire, une critique institutionnelle, un conflit partisan, un groupe professionnel ou un groupe comportemental sans ancrage discriminatoire clair.
- adjacent est reserve aux cas frontieres avec ancrage plausible dans le perimetre, pas aux discours simplement durs ou conflictuels.
- hors_perimetre designe les cas sans ancrage suffisant dans le perimetre.
- is_fallback doit etre false dans une analyse reelle. Reserve is_fallback=true aux erreurs techniques; dans cette reponse, tu dois donc utiliser is_fallback=false.
- needs_human_review doit etre true pour tout core, tout adjacent, tout ambiguous, toute confiance low ou medium.
- needs_human_review=false est autorise seulement pour hors_perimetre / no_signal avec confidence=high.
- evidence_span doit etre un court extrait du texte utilise.
- limits doit etre une liste de chaines et mentionner les limites utiles, dont l'absence de recherche web.

Valeurs autorisees:
- scope_level: core, adjacent, hors_perimetre.
- signal_category: problematic_group_targeting, stereotype_essentialization, devaluation_dehumanization, exclusion_discrimination, hostility_threat, ambiguous, no_signal.
- confidence: low, medium, high.

Combinaisons autorisees:
- core avec une categorie substantielle: problematic_group_targeting, stereotype_essentialization, devaluation_dehumanization, exclusion_discrimination, hostility_threat.
- adjacent avec une categorie substantielle, ou adjacent / ambiguous pour un vrai cas frontiere.
- hors_perimetre / no_signal pour un cas clairement hors perimetre.
- N'utilise pas hors_perimetre / ambiguous dans une analyse reelle.

Retourne uniquement un objet JSON avec ces champs:
candidate_id, scope_level, signal_category, is_fallback, needs_human_review, confidence, rationale, evidence_span, limits, model_provider, model_name.

Exemple de forme attendue:
{{
  "candidate_id": "exemple",
  "scope_level": "hors_perimetre",
  "signal_category": "no_signal",
  "is_fallback": false,
  "needs_human_review": false,
  "confidence": "high",
  "rationale": "Critique institutionnelle sans ciblage d'un groupe du perimetre.",
  "evidence_span": "court extrait utilise",
  "limits": ["Analyse limitee au contexte local.", "Aucune recherche web effectuee."],
  "model_provider": "mistral_v2",
  "model_name": "{model_name}"
}}

Payload:
{payload_json}
"""


class MistralContextualReviewProviderV2(ContextualReviewProvider):
    model_provider = "mistral_v2"

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
            parsed["candidate_id"] = str(payload["candidate_id"])
            parsed["model_provider"] = self.model_provider
            parsed["model_name"] = self.model
            parsed = self._normalize_review_payload(parsed)
            return validate_review_output_v2(parsed).to_dict()
        except (json.JSONDecodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
            return self._fallback(payload, f"Sortie Mistral V2 invalide ou non conforme : {exc}")
        except Exception as exc:
            return self._fallback(payload, f"Erreur appel Mistral V2 : {exc}")

    def _call_mistral(self, payload: dict[str, Any]) -> str:
        client = self.client or self._create_client()
        response = client.chat.complete(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_V2},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE_V2.format(
                        payload_json=json.dumps(payload, ensure_ascii=False, indent=2),
                        model_name=self.model,
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
            raise ValueError(f"Payload Mistral V2 incomplet : {sorted(missing)}")
        required_target = {"ordre", "orateur_nom", "point_titre", "sous_point_titre", "texte"}
        target = payload.get("target")
        if not isinstance(target, dict):
            raise ValueError("target doit etre un objet.")
        missing_target = required_target - target.keys()
        if missing_target:
            raise ValueError(f"target incomplet : {sorted(missing_target)}")

    @staticmethod
    def _normalize_review_payload(payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        limits = normalized.get("limits", [])
        if isinstance(limits, str):
            normalized["limits"] = [limits]
        elif isinstance(limits, list):
            normalized["limits"] = [str(item) for item in limits]
        else:
            normalized["limits"] = [str(limits)]
        return normalized

    def _fallback(self, payload: dict[str, Any], rationale: str) -> dict[str, Any]:
        candidate_id = str(payload.get("candidate_id", "unknown"))
        target = payload.get("target", {})
        target_text = target.get("texte", "") if isinstance(target, dict) else ""
        fallback = {
            "candidate_id": candidate_id,
            "scope_level": "hors_perimetre",
            "signal_category": "ambiguous",
            "is_fallback": True,
            "needs_human_review": True,
            "confidence": "low",
            "rationale": rationale,
            "evidence_span": str(target_text)[:180],
            "limits": [
                "Fallback technique sur sortie sure.",
                "Analyse limitee au contexte local.",
                "Aucune recherche web effectuee.",
            ],
            "model_provider": self.model_provider,
            "model_name": self.model,
        }
        return validate_review_output_v2(fallback).to_dict()
