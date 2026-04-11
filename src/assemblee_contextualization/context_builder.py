from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Mapping

from .contracts import (
    ContextPayload,
    InterventionContextItem,
    LocalContext,
    RuleBasedSignal,
    SourceRef,
    TargetIntervention,
)


TRUTHY = {"1", "true", "True", "yes", "oui"}


def load_interventions_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def is_signal_candidate(row: Mapping[str, Any]) -> bool:
    return str(row.get("signal_candidate", "")).strip() in TRUTHY


def candidate_ids(interventions: Iterable[Mapping[str, Any]]) -> list[str]:
    return [str(row["intervention_id"]) for row in interventions if is_signal_candidate(row)]


def build_context_payload(
    interventions: list[Mapping[str, Any]],
    candidate_id: str,
    *,
    source_file: str,
    window: int = 2,
) -> ContextPayload:
    if window < 0:
        raise ValueError("window doit etre positif ou nul.")

    rows = sorted(interventions, key=lambda row: (_as_int(row.get("ordre")), str(row.get("intervention_id", ""))))
    target_index = _find_target_index(rows, candidate_id)
    target_row = rows[target_index]
    if not is_signal_candidate(target_row):
        raise ValueError(f"Intervention non candidate : {candidate_id}")

    seance_id = str(target_row.get("seance_id", ""))
    same_seance_rows = [row for row in rows if str(row.get("seance_id", "")) == seance_id]
    same_seance_index = _find_target_index(same_seance_rows, candidate_id)

    previous_rows = same_seance_rows[max(0, same_seance_index - window) : same_seance_index]
    next_rows = same_seance_rows[same_seance_index + 1 : same_seance_index + 1 + window]

    payload = ContextPayload(
        candidate_id=candidate_id,
        source=SourceRef(
            source_file=source_file,
            seance_id=seance_id,
            intervention_id=candidate_id,
        ),
        target=TargetIntervention(**_context_item_kwargs(target_row)),
        rule_based_signal=RuleBasedSignal(
            signal_candidate=True,
            signal_family=str(target_row.get("signal_family", "")),
            signal_trigger=str(target_row.get("signal_trigger", "")),
            signal_intensity=_as_int(target_row.get("signal_intensity")),
        ),
        local_context=LocalContext(
            previous=[InterventionContextItem(**_context_item_kwargs(row)) for row in previous_rows],
            next=[InterventionContextItem(**_context_item_kwargs(row)) for row in next_rows],
        ),
    )
    return payload


def _find_target_index(rows: list[Mapping[str, Any]], candidate_id: str) -> int:
    for index, row in enumerate(rows):
        if str(row.get("intervention_id", "")) == candidate_id:
            return index
    raise ValueError(f"Intervention introuvable : {candidate_id}")


def _context_item_kwargs(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ordre": _as_int(row.get("ordre")),
        "intervention_id": str(row.get("intervention_id", "")),
        "orateur_nom": str(row.get("orateur_nom", "")),
        "point_titre": str(row.get("point_titre", "")),
        "sous_point_titre": str(row.get("sous_point_titre", "")),
        "texte": str(row.get("texte", "")),
    }


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

