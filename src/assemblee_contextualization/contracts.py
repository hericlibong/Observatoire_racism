from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Decision(str, Enum):
    VALIDATED_SIGNAL = "validated_signal"
    FALSE_POSITIVE = "false_positive"
    AMBIGUOUS = "ambiguous"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class SourceRef:
    source_file: str
    seance_id: str
    intervention_id: str


@dataclass(frozen=True)
class InterventionContextItem:
    ordre: int
    intervention_id: str
    orateur_nom: str
    point_titre: str
    sous_point_titre: str
    texte: str


@dataclass(frozen=True)
class TargetIntervention(InterventionContextItem):
    pass


@dataclass(frozen=True)
class RuleBasedSignal:
    signal_candidate: bool
    signal_family: str
    signal_trigger: str
    signal_intensity: int


@dataclass(frozen=True)
class LocalContext:
    previous: list[InterventionContextItem]
    next: list[InterventionContextItem]


@dataclass(frozen=True)
class ContextPayload:
    candidate_id: str
    source: SourceRef
    target: TargetIntervention
    rule_based_signal: RuleBasedSignal
    local_context: LocalContext

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextualReviewOutput:
    candidate_id: str
    decision: Decision
    needs_human_review: bool
    confidence: Confidence
    rationale: str
    evidence_span: str
    limits: list[str]
    model_provider: str
    model_name: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision"] = self.decision.value
        payload["confidence"] = self.confidence.value
        return payload


def validate_review_output(payload: dict[str, Any]) -> ContextualReviewOutput:
    required = {
        "candidate_id",
        "decision",
        "needs_human_review",
        "confidence",
        "rationale",
        "evidence_span",
        "limits",
        "model_provider",
        "model_name",
    }
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"Sortie contextualisation incomplete : {sorted(missing)}")

    try:
        decision = Decision(payload["decision"])
    except ValueError as exc:
        raise ValueError(f"Decision non autorisee : {payload['decision']}") from exc

    try:
        confidence = Confidence(payload["confidence"])
    except ValueError as exc:
        raise ValueError(f"Confidence non autorisee : {payload['confidence']}") from exc

    needs_human_review = payload["needs_human_review"]
    if not isinstance(needs_human_review, bool):
        raise ValueError("needs_human_review doit etre un booleen.")

    if decision in {Decision.AMBIGUOUS, Decision.VALIDATED_SIGNAL} and not needs_human_review:
        raise ValueError(f"{decision.value} implique needs_human_review = true en v0.")

    limits = payload["limits"]
    if not isinstance(limits, list) or not all(isinstance(item, str) for item in limits):
        raise ValueError("limits doit etre une liste de chaines.")

    return ContextualReviewOutput(
        candidate_id=str(payload["candidate_id"]),
        decision=decision,
        needs_human_review=needs_human_review,
        confidence=confidence,
        rationale=str(payload["rationale"]),
        evidence_span=str(payload["evidence_span"]),
        limits=limits,
        model_provider=str(payload["model_provider"]),
        model_name=str(payload["model_name"]),
    )

