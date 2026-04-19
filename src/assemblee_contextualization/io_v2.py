from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .contracts import ContextualReviewOutputV2, ScopeLevel, SignalCategory, validate_review_output_v2
from .paths import display_path


def summarize_outputs_v2(outputs: list[ContextualReviewOutputV2]) -> dict[str, int]:
    fallback_count = sum(output.is_fallback for output in outputs)
    substantive_hors_perimetre_count = sum(
        output.scope_level == ScopeLevel.HORS_PERIMETRE and not output.is_fallback for output in outputs
    )
    return {
        "total": len(outputs),
        "fallback_technical": fallback_count,
        "substantive_hors_perimetre": substantive_hors_perimetre_count,
    }


def summarize_output_file(output_path: Path) -> dict[str, Any]:
    outputs = read_outputs_v2(output_path)
    scope_distribution = _count_values(output.scope_level.value for output in outputs)
    signal_distribution = _count_values(output.signal_category.value for output in outputs)
    substantive_outputs = [output for output in outputs if not output.is_fallback]

    return {
        "path": str(display_path(output_path)),
        "source_id": _source_id_from_outputs(outputs) or output_path.stem,
        "reviewed_items": len(outputs),
        "scope_level_distribution": scope_distribution,
        "signal_category_distribution": signal_distribution,
        "fallback_technical": sum(output.is_fallback for output in outputs),
        "true_hors_perimetre_no_signal": sum(
            output.scope_level == ScopeLevel.HORS_PERIMETRE
            and output.signal_category == SignalCategory.NO_SIGNAL
            and not output.is_fallback
            for output in outputs
        ),
        "substantive_metrics_exclude_fallback": True,
        "substantive_scope_level_distribution": _count_values(
            output.scope_level.value for output in substantive_outputs
        ),
        "substantive_signal_category_distribution": _count_values(
            output.signal_category.value for output in substantive_outputs
        ),
    }


def write_outputs_v2(outputs: list[ContextualReviewOutputV2], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for output in outputs:
            handle.write(json.dumps(output.to_dict(), ensure_ascii=False) + "\n")


def read_outputs_v2(output_path: Path) -> list[ContextualReviewOutputV2]:
    if not output_path.exists():
        raise FileNotFoundError(f"Export V2 introuvable : {output_path}")
    return [
        validate_review_output_v2(json.loads(line))
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_comparison_summary(output_paths: list[Path], summary_path: Path) -> dict[str, Any]:
    summaries = [summarize_output_file(path) for path in output_paths]
    payload = {
        "summary_type": "assemblee_contextual_reviews_v2_comparison",
        "fallbacks_excluded_from_substantive_metrics": True,
        "sessions": summaries,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _source_id_from_outputs(outputs: list[ContextualReviewOutputV2]) -> str:
    if not outputs:
        return ""
    candidate_id = outputs[0].candidate_id
    if "_" not in candidate_id:
        return ""
    return candidate_id.rsplit("_", maxsplit=1)[0]


def _count_values(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts
