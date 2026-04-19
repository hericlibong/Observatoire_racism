from __future__ import annotations

from typing import Any

from .context_builder import build_context_payload, candidate_ids
from .contracts import (
    Confidence,
    ContextualReviewOutputV2,
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
)
from .paths import as_int
from .providers import ContextualReviewProvider


DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES = 15


def review_candidates_v2(
    interventions: list[dict[str, Any]],
    provider: ContextualReviewProvider,
    *,
    source_file: str = "CRSANR5L17S2026O1N191.xml",
    window: int = 2,
    sample_size_when_no_candidates: int = 0,
) -> list[ContextualReviewOutputV2]:
    outputs: list[ContextualReviewOutputV2] = []
    review_ids, allow_non_candidates = select_review_ids(
        interventions,
        sample_size_when_no_candidates=sample_size_when_no_candidates,
    )
    for candidate_id in review_ids:
        context = build_context_payload(
            interventions,
            candidate_id,
            source_file=source_file,
            window=window,
            allow_non_candidate=allow_non_candidates,
        )
        output = validate_review_output_v2(provider.review(context.to_dict()))
        if output.candidate_id != candidate_id:
            raise ValueError("La sortie provider V2 ne correspond pas au candidat demande.")
        outputs.append(output)

    validate_fallback_invariants(outputs)
    return outputs


def select_review_ids(
    interventions: list[dict[str, Any]],
    *,
    sample_size_when_no_candidates: int = 0,
) -> tuple[list[str], bool]:
    rule_based_candidate_ids = candidate_ids(interventions)
    if rule_based_candidate_ids or sample_size_when_no_candidates <= 0:
        return rule_based_candidate_ids, False
    return sample_intervention_ids(interventions, sample_size_when_no_candidates), True


def sample_intervention_ids(interventions: list[dict[str, Any]], sample_size: int) -> list[str]:
    rows = sorted(interventions, key=lambda row: (as_int(row.get("ordre")), str(row.get("intervention_id", ""))))
    rows = [row for row in rows if str(row.get("texte", "")).strip()]
    if sample_size >= len(rows):
        return [str(row["intervention_id"]) for row in rows]
    if sample_size <= 0 or not rows:
        return []

    if sample_size == 1:
        return [str(rows[0]["intervention_id"])]

    last_index = len(rows) - 1
    selected_indexes = sorted({round(index * last_index / (sample_size - 1)) for index in range(sample_size)})
    return [str(rows[index]["intervention_id"]) for index in selected_indexes]


def validate_fallback_invariants(outputs: list[ContextualReviewOutputV2]) -> None:
    for output in outputs:
        if not output.is_fallback:
            continue
        if (
            output.scope_level,
            output.signal_category,
            output.needs_human_review,
            output.confidence,
        ) != (
            ScopeLevel.HORS_PERIMETRE,
            SignalCategory.AMBIGUOUS,
            True,
            Confidence.LOW,
        ):
            raise ValueError("Fallback V2 hors combinaison technique autorisee.")
