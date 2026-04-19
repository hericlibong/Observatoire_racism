from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from src.assemblee_contextualization.context_builder import load_interventions_csv
from src.assemblee_contextualization.io_v2 import (
    summarize_output_file,
    write_comparison_summary,
    write_outputs_v2,
)
from src.assemblee_contextualization.paths import ROOT_DIR, display_path, session_slug
from src.assemblee_contextualization.providers import ContextualReviewProvider
from src.assemblee_contextualization.review_engine import (
    DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES,
    review_candidates_v2,
)
from src.assemblee_contextualization.run_pilot_v2 import (
    build_provider,
)
from src.build_assemblee_phase_c_lot import OUTPUT_PATH as PHASE_C_INPUT_PATH
from src.build_assemblee_phase_c_lot import PHASE_C_LOT_FILES


OUTPUT_PREFIX = "contextual_reviews_phase_c_lot"
SUMMARY_PATH_TEMPLATE = "contextual_reviews_phase_c_lot_v2_{provider}.json"


def run_phase_c_lot_v2(
    provider: ContextualReviewProvider,
    *,
    provider_name: str,
    input_path: Path = PHASE_C_INPUT_PATH,
    output_dir: Path | None = None,
    sample_size_when_no_candidates: int = DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES,
    source_files: list[str] | None = None,
) -> list[Path]:
    rows = load_interventions_csv(input_path)
    selected_source_files = source_files or PHASE_C_LOT_FILES
    output_paths: list[Path] = []
    target_dir = output_dir or input_path.parent

    for source_file in selected_source_files:
        seance_rows = _rows_for_source(rows, source_file)
        outputs = review_candidates_v2(
            seance_rows,
            provider,
            source_file=source_file,
            sample_size_when_no_candidates=sample_size_when_no_candidates,
        )
        output_path = phase_c_output_path(source_file, provider_name, target_dir)
        write_outputs_v2(outputs, output_path)
        output_paths.append(output_path)

    return output_paths


def write_phase_c_summary(output_paths: list[Path], provider_name: str, output_dir: Path) -> Path:
    summary_path = output_dir / SUMMARY_PATH_TEMPLATE.format(provider=provider_name)
    write_comparison_summary(output_paths, summary_path)
    return summary_path


def phase_c_output_path(source_file: str, provider_name: str, output_dir: Path) -> Path:
    return output_dir / f"{OUTPUT_PREFIX}_{session_slug(source_file)}_v2_{provider_name}.jsonl"


def phase_c_export_summary(output_paths: list[Path]) -> list[dict[str, Any]]:
    return [summarize_output_file(path) for path in output_paths]


def _rows_for_source(rows: list[dict[str, str]], source_file: str) -> list[dict[str, str]]:
    seance_id = Path(source_file).stem
    selected = [row for row in rows if row.get("seance_id") == seance_id]
    if not selected:
        raise ValueError(f"Seance Phase C absente du CSV structure : {seance_id}")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V2 review on the Phase C Assemblee lot.")
    parser.add_argument("--provider", choices=["mock", "mistral"], default="mock")
    parser.add_argument("--input", type=Path, default=PHASE_C_INPUT_PATH)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE_WHEN_NO_CANDIDATES)
    parser.add_argument("--no-summary", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir or args.input.parent
    output_paths = run_phase_c_lot_v2(
        build_provider(args.provider),
        provider_name=args.provider,
        input_path=args.input,
        output_dir=output_dir,
        sample_size_when_no_candidates=args.sample_size,
    )
    summary_path = None if args.no_summary else write_phase_c_summary(output_paths, args.provider, output_dir)

    print(f"Provider : {args.provider}")
    print(f"Input : {display_path(args.input, ROOT_DIR)}")
    for summary in phase_c_export_summary(output_paths):
        print(
            "- {source_id}: {reviewed_items} sorties, {fallback_technical} fallbacks techniques, {path}".format(
                **summary
            )
        )
    if summary_path is not None:
        print(f"Resume : {display_path(summary_path, ROOT_DIR)}")


if __name__ == "__main__":
    main()
