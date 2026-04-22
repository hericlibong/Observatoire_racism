import csv
import tempfile
from pathlib import Path
import unittest

from src.assemblee_contextualization.context_builder import (
    build_context_payload,
    candidate_ids,
    load_interventions_csv,
)
from src.build_assemblee_phase_c_lot import (
    PHASE_C_LOT_FILES,
    seance_counts,
    write_phase_c_lot_csv,
)
from src.assemblee_contextualization.sources.xml_parser import CSV_FIELDS


class BuildAssembleePhaseCLotTest(unittest.TestCase):
    def test_phase_c_lot_csv_contains_expected_sessions_and_v2_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "interventions_phase_c_lot.csv"
            rows = write_phase_c_lot_csv(output_path)
            loaded_rows = load_interventions_csv(output_path)

            with output_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, CSV_FIELDS)

        expected_seance_ids = {
            Path(source_file).stem
            for source_file in PHASE_C_LOT_FILES
        }

        self.assertEqual(set(seance_counts(rows)), expected_seance_ids)
        self.assertEqual({row["seance_id"] for row in loaded_rows}, expected_seance_ids)
        self.assertTrue(all(count > 0 for count in seance_counts(rows).values()))

        review_ids = candidate_ids(loaded_rows)
        self.assertGreater(len(review_ids), 0)
        payload = build_context_payload(
            loaded_rows,
            review_ids[0],
            source_file="interventions_phase_c_lot.csv",
            window=2,
        )

        self.assertIn(payload.source.seance_id, expected_seance_ids)
        self.assertEqual(payload.candidate_id, review_ids[0])
        self.assertTrue(payload.target.texte)
        self.assertTrue(payload.target.point_titre)


if __name__ == "__main__":
    unittest.main()
