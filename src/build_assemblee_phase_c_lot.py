from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from assemblee_contextualization.paths import INTERIM_DIR, ROOT_DIR, display_path
from assemblee_contextualization.sources.xml_parser import (
    InterventionRow,
    parse_source_file,
    write_csv,
)


PHASE_C_LOT_FILES = [
    "CRSANR5L17S2026O1N191.xml",
    "CRSANR5L17S2026O1N190.xml",
    "CRSANR5L17S2026O1N120.xml",
    "CRSANR5L17S2025O1N150.xml",
    "CRSANR5L17S2025E1N014.xml",
]
OUTPUT_PATH = INTERIM_DIR / "interventions_phase_c_lot.csv"


def build_phase_c_lot(source_files: list[str] | None = None) -> list[InterventionRow]:
    rows: list[InterventionRow] = []
    for source_file in source_files or PHASE_C_LOT_FILES:
        rows.extend(parse_source_file(source_file))
    return rows


def write_phase_c_lot_csv(output_path: Path = OUTPUT_PATH) -> list[InterventionRow]:
    rows = build_phase_c_lot()
    validate_phase_c_lot_rows(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(rows, output_path)
    return rows


def validate_phase_c_lot_rows(rows: list[InterventionRow]) -> None:
    expected_seance_ids = {Path(source_file).stem for source_file in PHASE_C_LOT_FILES}
    actual_seance_ids = {row.seance_id for row in rows}
    missing = expected_seance_ids - actual_seance_ids
    if missing:
        raise ValueError(f"Seances Phase C absentes de la sortie : {sorted(missing)}")

    for row in rows:
        if not row.intervention_id or not row.seance_id or not row.texte.strip():
            raise ValueError(f"Intervention Phase C inexploitable : {row.intervention_id}")


def seance_counts(rows: list[InterventionRow]) -> dict[str, int]:
    return dict(sorted(Counter(row.seance_id for row in rows).items()))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse the Phase C Assemblee lot into one structured CSV."
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    rows = write_phase_c_lot_csv(args.output)
    print(f"CSV ecrit : {display_path(args.output, ROOT_DIR)}")
    print(f"Seances : {len(seance_counts(rows))}")
    print("Interventions par seance :")
    for seance_id, count in seance_counts(rows).items():
        print(f"- {seance_id}: {count}")


if __name__ == "__main__":
    main()
