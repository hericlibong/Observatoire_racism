from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .context_builder import build_context_payload, candidate_ids, load_interventions_csv
from .contracts import (
    Confidence,
    ContextualReviewOutputV2,
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
)
from .mock_provider_v2 import MockContextualReviewProviderV2


ROOT_DIR = Path(__file__).resolve().parents[2]
INTERVENTIONS_PATH = ROOT_DIR / "data/interim/assemblee/interventions_test.csv"
OUTPUT_PATH = ROOT_DIR / "data/interim/assemblee/contextual_reviews_pilot_v2.jsonl"
PILOT_SOURCE_FILE = "CRSANR5L17S2026O1N191.xml"


def review_candidates_v2(
    interventions: list[dict[str, Any]],
    provider: MockContextualReviewProviderV2,
    *,
    source_file: str = PILOT_SOURCE_FILE,
    window: int = 2,
) -> list[ContextualReviewOutputV2]:
    outputs: list[ContextualReviewOutputV2] = []
    for candidate_id in candidate_ids(interventions):
        context = build_context_payload(
            interventions,
            candidate_id,
            source_file=source_file,
            window=window,
        )
        output = validate_review_output_v2(provider.review(context.to_dict()))
        if output.candidate_id != candidate_id:
            raise ValueError("La sortie provider V2 ne correspond pas au candidat demande.")
        outputs.append(output)

    validate_fallback_invariants(outputs)
    return outputs


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


def write_outputs_v2(outputs: list[ContextualReviewOutputV2], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for output in outputs:
            handle.write(json.dumps(output.to_dict(), ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Assemblee contextual review V2 on the N191 pilot file.")
    parser.add_argument("--input", type=Path, default=INTERVENTIONS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--window", type=int, default=2)
    args = parser.parse_args()

    interventions = load_interventions_csv(args.input)
    provider = MockContextualReviewProviderV2()
    outputs = review_candidates_v2(
        interventions,
        provider,
        source_file=PILOT_SOURCE_FILE,
        window=args.window,
    )
    write_outputs_v2(outputs, args.output)
    summary = summarize_outputs_v2(outputs)

    print("Provider : mock_v2")
    print(f"Fichier ecrit : {_display_path(args.output)}")
    print(f"Lignes : {summary['total']}")
    print(f"Fallbacks techniques : {summary['fallback_technical']}")
    print(f"Hors perimetre substantiels : {summary['substantive_hors_perimetre']}")
    print("Apercu :")
    for output in outputs[:3]:
        print(json.dumps(output.to_dict(), ensure_ascii=False))


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(ROOT_DIR)
    except ValueError:
        return path


if __name__ == "__main__":
    main()
