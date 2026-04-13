from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContextualReviewOutputV2
from .processing_journal import JOURNAL_PATH, read_processing_journal
from .run_pilot_v2 import ROOT_DIR, load_interventions_for_source, read_outputs_v2


DEFAULT_REVIEW_PATH = (
    ROOT_DIR / "data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl"
)
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/interim/assemblee/heatmap_session_n191_v2.json"
EDITORIAL_POLICY = "signal \u00e0 revoir, jamais verdict automatique"


def build_heatmap_session_payload(
    *,
    source_file: str,
    journal_entry: Mapping[str, Any],
    interventions: list[Mapping[str, Any]],
    outputs: list[ContextualReviewOutputV2],
) -> dict[str, Any]:
    intervention_by_id = {str(row["intervention_id"]): row for row in interventions}
    items = [_heatmap_item(source_file, journal_entry, intervention_by_id, output) for output in outputs]
    items.sort(key=lambda item: (item["ordre"], item["intervention_id"]))

    fallback_count = sum(item["is_fallback"] for item in items)
    orders = [item["ordre"] for item in items]
    return {
        "export_type": "assemblee_heatmap_session_v2",
        "editorial_policy": EDITORIAL_POLICY,
        "fallbacks_excluded_from_substantive_metrics": True,
        "session": {
            "seance_id": str(journal_entry["seance_id"]),
            "source_file": source_file,
            "seance_date": str(journal_entry["seance_date"]),
            "seance_date_label": str(journal_entry["seance_date_label"]),
            "processed_at": str(journal_entry["processed_at"]),
            "provider": str(journal_entry["provider"]),
            "model_name": str(journal_entry["model_name"]),
        },
        "axis": {
            "field": "ordre",
            "min": min(orders) if orders else None,
            "max": max(orders) if orders else None,
            "reviewed_items": len(items),
        },
        "metrics": {
            "reviewed_items": len(items),
            "fallback_count": fallback_count,
            "non_fallback_items": len(items) - fallback_count,
            "substantive_items": len(items) - fallback_count,
        },
        "items": items,
    }


def write_heatmap_session_export(
    *,
    source_file: str,
    review_path: Path = DEFAULT_REVIEW_PATH,
    journal_path: Path = JOURNAL_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    journal_entry = _journal_entry_for_source(source_file, journal_path)
    interventions = load_interventions_for_source(source_file)
    outputs = read_outputs_v2(review_path)
    payload = build_heatmap_session_payload(
        source_file=source_file,
        journal_entry=journal_entry,
        interventions=interventions,
        outputs=outputs,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _journal_entry_for_source(source_file: str, journal_path: Path) -> dict[str, Any]:
    seance_id = Path(source_file).stem
    for entry in read_processing_journal(journal_path):
        if entry["source_file"] == source_file or entry["seance_id"] == seance_id:
            return entry
    raise ValueError(f"Seance absente du journal : {source_file}")


def _heatmap_item(
    source_file: str,
    journal_entry: Mapping[str, Any],
    intervention_by_id: Mapping[str, Mapping[str, Any]],
    output: ContextualReviewOutputV2,
) -> dict[str, Any]:
    row = intervention_by_id.get(output.candidate_id)
    if row is None:
        raise ValueError(f"Intervention absente du parsing : {output.candidate_id}")

    return {
        "seance_id": str(journal_entry["seance_id"]),
        "source_file": source_file,
        "seance_date": str(journal_entry["seance_date"]),
        "seance_date_label": str(journal_entry["seance_date_label"]),
        "ordre": _as_int(row.get("ordre")),
        "axis_position": _as_int(row.get("ordre")),
        "intervention_id": str(row["intervention_id"]),
        "orateur_nom": str(row.get("orateur_nom", "")),
        "point_titre": str(row.get("point_titre", "")),
        "sous_point_titre": str(row.get("sous_point_titre", "")),
        "excerpt": _excerpt(str(row.get("texte", ""))),
        "evidence_span": output.evidence_span,
        "scope_level": output.scope_level.value,
        "signal_category": output.signal_category.value,
        "confidence": output.confidence.value,
        "needs_human_review": output.needs_human_review,
        "is_fallback": output.is_fallback,
        "review_label": _review_label(output),
    }


def _review_label(output: ContextualReviewOutputV2) -> str:
    if output.is_fallback:
        return "fallback technique \u00e0 revoir"
    if output.needs_human_review:
        return "signal \u00e0 revoir"
    return "aucun signal \u00e0 revoir"


def _excerpt(text: str, max_length: int = 280) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1].rstrip() + "\u2026"


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
