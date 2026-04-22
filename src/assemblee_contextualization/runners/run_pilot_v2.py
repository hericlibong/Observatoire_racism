from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..context_builder import load_interventions_csv
from ..io_v2 import summarize_outputs_v2, write_comparison_summary, write_outputs_v2
from ..providers.mistral_provider_v2 import MistralContextualReviewProviderV2
from ..providers.mock_provider_v2 import MockContextualReviewProviderV2
from ..paths import ROOT_DIR, display_path, session_slug
from ..providers import ContextualReviewProvider
from ..review_engine import DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES, review_candidates_v2
from ..sources.xml_parser import parse_source_file


OUTPUT_PATH = ROOT_DIR / "data/interim/assemblee/contextual_reviews_pilot_v2.jsonl"
PILOT_SOURCE_FILE = "CRSANR5L17S2026O1N191.xml"


def load_interventions_for_source(source_file: str, input_path: Path | None = None) -> list[dict[str, Any]]:
    if input_path is not None:
        return load_interventions_csv(input_path)

    rows = parse_source_file(source_file)
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
    return ROOT_DIR / f"data/interim/assemblee/contextual_reviews_{session_slug(source_file)}_v2_{provider_name}.jsonl"


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
    print(f"Fichier ecrit : {display_path(output_path)}")
    print(f"Lignes : {summary['total']}")
    print(f"Fallbacks techniques : {summary['fallback_technical']}")
    print(f"Hors perimetre substantiels : {summary['substantive_hors_perimetre']}")
    if args.summary_output is not None:
        comparison = write_comparison_summary([*args.compare_with, output_path], args.summary_output)
        print(f"Resume comparatif : {display_path(args.summary_output)}")
        print(f"Seances comparees : {len(comparison['sessions'])}")
    print("Apercu :")
    for output in outputs[:3]:
        print(json.dumps(output.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    main()
