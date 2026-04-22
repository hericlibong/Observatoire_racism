import csv
import tempfile
from pathlib import Path
import unittest

from src.assemblee_contextualization.mock_provider_v2 import MockContextualReviewProviderV2
from src.assemblee_contextualization.run_phase_c_lot_v2 import (
    phase_c_output_path,
    run_phase_c_lot_v2,
    write_phase_c_summary,
)
from src.assemblee_contextualization.io_v2 import read_outputs_v2
from src.assemblee_contextualization.xml_parser import CSV_FIELDS


class RunPhaseCLotV2Test(unittest.TestCase):
    def test_run_phase_c_lot_v2_writes_per_session_exports_and_samples_empty_session(self) -> None:
        source_files = [
            "CRSANR5L17S2026O1N191.xml",
            "CRSANR5L17S2026O1N190.xml",
        ]

        with tempfile.TemporaryDirectory() as directory:
            tmp_dir = Path(directory)
            input_path = tmp_dir / "interventions_phase_c_lot.csv"
            self._write_rows(input_path)

            output_paths = run_phase_c_lot_v2(
                MockContextualReviewProviderV2(),
                provider_name="mock",
                input_path=input_path,
                output_dir=tmp_dir,
                sample_size_when_no_candidates=2,
                source_files=source_files,
            )
            summary_path = write_phase_c_summary(output_paths, "mock", tmp_dir)

            n191_outputs = read_outputs_v2(
                phase_c_output_path(source_files[0], "mock", tmp_dir)
            )
            n190_outputs = read_outputs_v2(
                phase_c_output_path(source_files[1], "mock", tmp_dir)
            )

            self.assertEqual(len(output_paths), 2)
            self.assertTrue(summary_path.exists())
            self.assertEqual(len(n191_outputs), 1)
            self.assertEqual(len(n190_outputs), 2)
            self.assertTrue(all(not output.is_fallback for output in n191_outputs + n190_outputs))

    @staticmethod
    def _write_rows(path: Path) -> None:
        rows = [
            {
                "intervention_id": "CRSANR5L17S2026O1N191_1",
                "seance_id": "CRSANR5L17S2026O1N191",
                "ordre": "1",
                "point_titre": "Point",
                "sous_point_titre": "",
                "orateur_nom": "Orateur",
                "orateur_qualite": "",
                "code_grammaire": "",
                "roledebat": "",
                "texte": "Texte candidat.",
                "nb_mots": "2",
                "nb_caracteres": "15",
                "signal_candidate": "True",
                "signal_family": "designation_groupe",
                "signal_trigger": "communautes",
                "signal_intensity": "1",
            },
            {
                "intervention_id": "CRSANR5L17S2026O1N190_1",
                "seance_id": "CRSANR5L17S2026O1N190",
                "ordre": "1",
                "point_titre": "Point",
                "sous_point_titre": "",
                "orateur_nom": "Orateur",
                "orateur_qualite": "",
                "code_grammaire": "",
                "roledebat": "",
                "texte": "Texte neutre un.",
                "nb_mots": "3",
                "nb_caracteres": "16",
                "signal_candidate": "False",
                "signal_family": "",
                "signal_trigger": "",
                "signal_intensity": "0",
            },
            {
                "intervention_id": "CRSANR5L17S2026O1N190_2",
                "seance_id": "CRSANR5L17S2026O1N190",
                "ordre": "2",
                "point_titre": "Point",
                "sous_point_titre": "",
                "orateur_nom": "Orateur",
                "orateur_qualite": "",
                "code_grammaire": "",
                "roledebat": "",
                "texte": "Texte neutre deux.",
                "nb_mots": "3",
                "nb_caracteres": "18",
                "signal_candidate": "False",
                "signal_family": "",
                "signal_trigger": "",
                "signal_intensity": "0",
            },
            {
                "intervention_id": "CRSANR5L17S2026O1N190_3",
                "seance_id": "CRSANR5L17S2026O1N190",
                "ordre": "3",
                "point_titre": "Point",
                "sous_point_titre": "",
                "orateur_nom": "Orateur",
                "orateur_qualite": "",
                "code_grammaire": "",
                "roledebat": "",
                "texte": "Texte neutre trois.",
                "nb_mots": "3",
                "nb_caracteres": "19",
                "signal_candidate": "False",
                "signal_family": "",
                "signal_trigger": "",
                "signal_intensity": "0",
            },
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
