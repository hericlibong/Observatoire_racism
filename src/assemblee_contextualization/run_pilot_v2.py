from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .context_builder import build_context_payload, candidate_ids, load_interventions_csv
from .contracts import (
    Confidence,
    ContextualReviewOutputV2,
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
)
from .mistral_provider_v2 import MistralContextualReviewProviderV2
from .mock_provider_v2 import MockContextualReviewProviderV2
from .providers import ContextualReviewProvider
from src.build_assemblee_pilot import NS, SOURCE_DIR, child_text, iter_paragraphs


ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT_DIR / "data/interim/assemblee/contextual_reviews_pilot_v2.jsonl"
PILOT_SOURCE_FILE = "CRSANR5L17S2026O1N191.xml"
DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES = 15


def review_candidates_v2(
    interventions: list[dict[str, Any]],
    provider: ContextualReviewProvider,
    *,
    source_file: str = PILOT_SOURCE_FILE,
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
    rows = sorted(interventions, key=lambda row: (_as_int(row.get("ordre")), str(row.get("intervention_id", ""))))
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
        "path": str(_display_path(output_path)),
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


def load_interventions_for_source(source_file: str, input_path: Path | None = None) -> list[dict[str, Any]]:
    if input_path is not None:
        return load_interventions_csv(input_path)

    source_path = _source_path(source_file)
    root = ET.parse(source_path).getroot()
    compte_rendu_uid = child_text(root, "uid")
    if not compte_rendu_uid:
        raise ValueError(f"UID introuvable dans {source_path}")

    contenu = root.find("a:contenu", NS)
    if contenu is None:
        raise ValueError(f"Element contenu introuvable dans {source_path}")

    rows = list(iter_paragraphs(contenu, compte_rendu_uid, "", ""))
    for row in rows:
        row.seance_id = compte_rendu_uid
    rows.sort(key=lambda row: (row.ordre, row.intervention_id))
    return [
        {
            "intervention_id": row.intervention_id,
            "seance_id": row.seance_id,
            "ordre": row.ordre,
            "point_titre": row.point_titre,
            "sous_point_titre": row.sous_point_titre,
            "orateur_nom": row.orateur_nom,
            "orateur_qualite": row.orateur_qualite,
            "code_grammaire": row.code_grammaire,
            "roledebat": row.roledebat,
            "texte": row.texte,
            "nb_mots": row.nb_mots,
            "nb_caracteres": row.nb_caracteres,
            "signal_candidate": row.signal_candidate,
            "signal_family": row.signal_family,
            "signal_trigger": row.signal_trigger,
            "signal_intensity": row.signal_intensity,
        }
        for row in rows
    ]


def build_provider(name: str) -> ContextualReviewProvider:
    if name == "mistral":
        return MistralContextualReviewProviderV2()
    if name == "mock":
        return MockContextualReviewProviderV2()
    raise ValueError(f"Provider V2 non supporte : {name}")


def default_output_path(source_file: str, provider_name: str) -> Path:
    if source_file == PILOT_SOURCE_FILE and provider_name == "mock":
        return OUTPUT_PATH
    return ROOT_DIR / f"data/interim/assemblee/contextual_reviews_{_session_slug(source_file)}_v2_{provider_name}.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Assemblee contextual review V2 on one local Assemblee file.")
    parser.add_argument("--provider", choices=["mock", "mistral"], default="mock")
    parser.add_argument("--source-file", default=PILOT_SOURCE_FILE)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--window", type=int, default=2)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES)
    parser.add_argument("--compare-with", type=Path, action="append", default=[])
    parser.add_argument("--summary-output", type=Path, default=None)
    args = parser.parse_args()

    output_path = args.output or default_output_path(args.source_file, args.provider)
    interventions = load_interventions_for_source(args.source_file, args.input)
    provider = build_provider(args.provider)
    outputs = review_candidates_v2(
        interventions,
        provider,
        source_file=args.source_file,
        window=args.window,
        sample_size_when_no_candidates=args.sample_size,
    )
    write_outputs_v2(outputs, output_path)
    summary = summarize_outputs_v2(outputs)

    print(f"Provider : {args.provider}")
    print(f"Source : {args.source_file}")
    print(f"Fichier ecrit : {_display_path(output_path)}")
    print(f"Lignes : {summary['total']}")
    print(f"Fallbacks techniques : {summary['fallback_technical']}")
    print(f"Hors perimetre substantiels : {summary['substantive_hors_perimetre']}")
    if args.summary_output is not None:
        comparison = write_comparison_summary([*args.compare_with, output_path], args.summary_output)
        print(f"Resume comparatif : {_display_path(args.summary_output)}")
        print(f"Seances comparees : {len(comparison['sessions'])}")
    print("Apercu :")
    for output in outputs[:3]:
        print(json.dumps(output.to_dict(), ensure_ascii=False))


def _source_path(source_file: str) -> Path:
    path = Path(source_file)
    if path.exists():
        return path
    return SOURCE_DIR / source_file


def _session_slug(source_file: str) -> str:
    stem = Path(source_file).stem.lower()
    marker = stem.rsplit("n", maxsplit=1)
    if len(marker) == 2 and marker[1].isdigit():
        return f"n{marker[1]}"
    return stem


def _source_id_from_outputs(outputs: list[ContextualReviewOutputV2]) -> str:
    if not outputs:
        return ""
    candidate_id = outputs[0].candidate_id
    if "_" not in candidate_id:
        return ""
    return candidate_id.rsplit("_", maxsplit=1)[0]


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(ROOT_DIR)
    except ValueError:
        return path


if __name__ == "__main__":
    main()
