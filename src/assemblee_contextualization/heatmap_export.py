from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContextualReviewOutputV2
from .paths import ROOT_DIR, as_int
from .processing_journal import JOURNAL_PATH, read_processing_journal
from .run_pilot_v2 import load_interventions_for_source, read_outputs_v2


DEFAULT_REVIEW_PATH = (
    ROOT_DIR / "data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl"
)
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data/interim/assemblee/heatmap_session_n191_v2.json"
EDITORIAL_POLICY = "signal \u00e0 revoir, sans jugement automatique"
PUBLIC_DISPLAY_REPLACEMENTS = (
    (re.compile(r"\bsignal valid[eé]\b", re.IGNORECASE), "signal"),
    (re.compile(r"\bpropos raciste(s)?\b", re.IGNORECASE), "propos"),
    (re.compile(r"\bpropos haineux\b", re.IGNORECASE), "propos"),
    (re.compile(r"\balert\w*\b", re.IGNORECASE), "repère"),
    (re.compile(r"\bfaute(s)?\b", re.IGNORECASE), "[terme du passage]"),
    (re.compile(r"\bverdict(s)?\b", re.IGNORECASE), "lecture"),
)


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
    non_fallback_items = [item for item in items if not item["is_fallback"]]
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
        "non_fallback_items": non_fallback_items,
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


def build_sessions_overview_payload(
    heatmap_payloads: list[Mapping[str, Any]],
    *,
    detail_hrefs: Mapping[str, str],
    generated_from: list[str],
) -> dict[str, Any]:
    sessions = []
    for payload in heatmap_payloads:
        session = payload["session"]
        source_file = str(session["source_file"])
        href = detail_hrefs.get(source_file, "")
        if not href:
            continue
        sessions.append(_overview_session_from_heatmap(payload, href))

    sessions.sort(key=lambda item: (item["seance_date"], item["source_file"]))
    return {
        "export_type": "assemblee_sessions_overview_v1",
        "editorial_policy": "guide de lecture, sans jugement automatique",
        "source_policy": "séances journalisées ou exports disponibles uniquement",
        "generated_from": generated_from,
        "labels": {
            "nothing_to_report": "rien à signaler ici",
            "read_with_caution": "à lire avec prudence",
            "important_for_observatoire": "important pour l’observatoire",
            "analysis_unavailable": "analyse non disponible",
        },
        "sessions": sessions,
    }


def write_sessions_overview_export(
    payload: Mapping[str, Any],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _journal_entry_for_source(source_file: str, journal_path: Path) -> dict[str, Any]:
    seance_id = Path(source_file).stem
    for entry in read_processing_journal(journal_path):
        if entry["source_file"] == source_file or entry["seance_id"] == seance_id:
            return entry
    raise ValueError(f"Seance absente du journal : {source_file}")


def _overview_session_from_heatmap(payload: Mapping[str, Any], href: str) -> dict[str, Any]:
    session = payload["session"]
    metrics = payload["metrics"]
    items = list(payload["items"])
    non_fallback_items = list(payload.get("non_fallback_items") or [item for item in items if not item["is_fallback"]])
    source_file = str(session["source_file"])
    return {
        "seance_id": str(session["seance_id"]),
        "short_label": _short_label(source_file),
        "source_file": source_file,
        "seance_date": str(session["seance_date"]),
        "seance_date_label": str(session["seance_date_label"]),
        "processed_at": str(session["processed_at"]),
        "status": "success",
        "reviewed_items": int(metrics["reviewed_items"]),
        "available_analyses": int(metrics["non_fallback_items"]),
        "nothing_to_report": sum(
            item["scope_level"] == "hors_perimetre" and item["signal_category"] == "no_signal"
            for item in non_fallback_items
        ),
        "read_with_caution": sum(item["scope_level"] == "adjacent" for item in non_fallback_items),
        "important_for_observatoire": sum(item["scope_level"] == "core" for item in non_fallback_items),
        "fallback_count": int(metrics["fallback_count"]),
        "detail_view": {
            "exists": True,
            "href": href,
            "label": "Ouvrir la vue détaillée",
        },
    }


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
        "ordre": as_int(row.get("ordre")),
        "axis_position": as_int(row.get("ordre")),
        "intervention_id": str(row["intervention_id"]),
        "orateur_nom": str(row.get("orateur_nom", "")),
        "point_titre": str(row.get("point_titre", "")),
        "sous_point_titre": str(row.get("sous_point_titre", "")),
        "excerpt": _public_display_text(_excerpt(str(row.get("texte", "")))),
        "evidence_span": _public_display_text(output.evidence_span),
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


def _short_label(source_file: str) -> str:
    match = re.search(r"N(\d+)\.xml$", source_file)
    if match:
        return f"N{match.group(1)}"
    return Path(source_file).stem


def _excerpt(text: str, max_length: int = 280) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1].rstrip() + "\u2026"


def _public_display_text(text: str) -> str:
    value = text
    for pattern, replacement in PUBLIC_DISPLAY_REPLACEMENTS:
        value = pattern.sub(replacement, value)
    return value
