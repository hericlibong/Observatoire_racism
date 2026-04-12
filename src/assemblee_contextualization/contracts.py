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


class ScopeLevel(str, Enum):
    CORE = "core"
    ADJACENT = "adjacent"
    HORS_PERIMETRE = "hors_perimetre"


class SignalCategory(str, Enum):
    PROBLEMATIC_GROUP_TARGETING = "problematic_group_targeting"
    STEREOTYPE_ESSENTIALIZATION = "stereotype_essentialization"
    DEVALUATION_DEHUMANIZATION = "devaluation_dehumanization"
    EXCLUSION_DISCRIMINATION = "exclusion_discrimination"
    HOSTILITY_THREAT = "hostility_threat"
    AMBIGUOUS = "ambiguous"
    NO_SIGNAL = "no_signal"


V2_SUBSTANTIVE_SIGNAL_CATEGORIES = frozenset(
    {
        SignalCategory.PROBLEMATIC_GROUP_TARGETING,
        SignalCategory.STEREOTYPE_ESSENTIALIZATION,
        SignalCategory.DEVALUATION_DEHUMANIZATION,
        SignalCategory.EXCLUSION_DISCRIMINATION,
        SignalCategory.HOSTILITY_THREAT,
    }
)

V2_ALLOWED_COMBINATIONS = frozenset(
    {(ScopeLevel.CORE, category) for category in V2_SUBSTANTIVE_SIGNAL_CATEGORIES}
    | {(ScopeLevel.ADJACENT, category) for category in V2_SUBSTANTIVE_SIGNAL_CATEGORIES}
    | {
        (ScopeLevel.ADJACENT, SignalCategory.AMBIGUOUS),
        (ScopeLevel.HORS_PERIMETRE, SignalCategory.NO_SIGNAL),
    }
)

V2_FALLBACK_COMBINATION = (ScopeLevel.HORS_PERIMETRE, SignalCategory.AMBIGUOUS)


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


@dataclass(frozen=True)
class ContextualReviewOutputV2:
    candidate_id: str
    scope_level: ScopeLevel
    signal_category: SignalCategory
    is_fallback: bool
    needs_human_review: bool
    confidence: Confidence
    rationale: str
    evidence_span: str
    limits: list[str]
    model_provider: str
    model_name: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scope_level"] = self.scope_level.value
        payload["signal_category"] = self.signal_category.value
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


def validate_v2_combination(
    scope_level: ScopeLevel | str,
    signal_category: SignalCategory | str,
    *,
    is_fallback: bool = False,
) -> tuple[ScopeLevel, SignalCategory]:
    try:
        scope = ScopeLevel(scope_level)
    except ValueError as exc:
        raise ValueError(f"scope_level non autorise : {scope_level}") from exc

    try:
        category = SignalCategory(signal_category)
    except ValueError as exc:
        raise ValueError(f"signal_category non autorisee : {signal_category}") from exc

    if is_fallback:
        if (scope, category) == V2_FALLBACK_COMBINATION:
            return scope, category
        raise ValueError(
            "is_fallback=true est autorise seulement avec "
            "hors_perimetre / ambiguous."
        )

    if (scope, category) not in V2_ALLOWED_COMBINATIONS:
        raise ValueError(f"Combinaison v2 invalide : {scope.value} / {category.value}")

    return scope, category


def validate_review_output_v2(payload: dict[str, Any]) -> ContextualReviewOutputV2:
    required = {
        "candidate_id",
        "scope_level",
        "signal_category",
        "is_fallback",
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
        raise ValueError(f"Sortie contextualisation v2 incomplete : {sorted(missing)}")

    is_fallback = payload["is_fallback"]
    if not isinstance(is_fallback, bool):
        raise ValueError("is_fallback doit etre un booleen.")

    scope_level, signal_category = validate_v2_combination(
        payload["scope_level"],
        payload["signal_category"],
        is_fallback=is_fallback,
    )

    try:
        confidence = Confidence(payload["confidence"])
    except ValueError as exc:
        raise ValueError(f"Confidence non autorisee : {payload['confidence']}") from exc

    needs_human_review = payload["needs_human_review"]
    if not isinstance(needs_human_review, bool):
        raise ValueError("needs_human_review doit etre un booleen.")

    if is_fallback and (
        scope_level,
        signal_category,
        needs_human_review,
        confidence,
    ) != (
        ScopeLevel.HORS_PERIMETRE,
        SignalCategory.AMBIGUOUS,
        True,
        Confidence.LOW,
    ):
        raise ValueError(
            "is_fallback=true est autorise seulement pour "
            "hors_perimetre / ambiguous avec needs_human_review=true et confidence=low."
        )

    if (
        not needs_human_review
        and (scope_level, signal_category, confidence)
        != (ScopeLevel.HORS_PERIMETRE, SignalCategory.NO_SIGNAL, Confidence.HIGH)
    ):
        raise ValueError(
            "needs_human_review=false est autorise seulement pour "
            "hors_perimetre / no_signal avec confidence=high."
        )

    limits = payload["limits"]
    if not isinstance(limits, list) or not all(isinstance(item, str) for item in limits):
        raise ValueError("limits doit etre une liste de chaines.")

    return ContextualReviewOutputV2(
        candidate_id=str(payload["candidate_id"]),
        scope_level=scope_level,
        signal_category=signal_category,
        is_fallback=is_fallback,
        needs_human_review=needs_human_review,
        confidence=confidence,
        rationale=str(payload["rationale"]),
        evidence_span=str(payload["evidence_span"]),
        limits=limits,
        model_provider=str(payload["model_provider"]),
        model_name=str(payload["model_name"]),
    )
