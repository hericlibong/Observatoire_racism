from __future__ import annotations

import argparse
import json
from pathlib import Path

from .context_builder import load_interventions_csv
from .mistral_provider import MistralContextualReviewProvider
from .mock_provider import MockContextualReviewProvider
from .reviewer import ContextualReviewer


ROOT_DIR = Path(__file__).resolve().parents[2]
INTERVENTIONS_PATH = ROOT_DIR / "data/interim/assemblee/interventions_test.csv"
OUTPUT_PATH = ROOT_DIR / "data/interim/assemblee/contextual_reviews_pilot.jsonl"
PILOT_SOURCE_FILE = "CRSANR5L17S2026O1N191.xml"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Assemblee contextual review on the pilot file.")
    parser.add_argument("--provider", choices=["mock", "mistral"], default="mock")
    parser.add_argument("--input", type=Path, default=INTERVENTIONS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--window", type=int, default=2)
    args = parser.parse_args()

    provider = (
        MistralContextualReviewProvider()
        if args.provider == "mistral"
        else MockContextualReviewProvider()
    )
    reviewer = ContextualReviewer(provider, source_file=PILOT_SOURCE_FILE, window=args.window)
    interventions = load_interventions_csv(args.input)
    outputs = reviewer.review_candidates(interventions)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for output in outputs:
            handle.write(json.dumps(output.to_dict(), ensure_ascii=False) + "\n")

    print(f"Provider : {args.provider}")
    print(f"Fichier ecrit : {args.output.relative_to(ROOT_DIR)}")
    print(f"Lignes : {len(outputs)}")
    print("Apercu :")
    for output in outputs[:3]:
        print(json.dumps(output.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    main()
