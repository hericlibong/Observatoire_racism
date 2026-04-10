import csv
import json
import subprocess
import sys
from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "src/build_assemblee_pilot.py"
CSV_PATH = ROOT_DIR / "data/interim/assemblee/interventions_test.csv"
MANIFEST_PATH = ROOT_DIR / "data/interim/assemblee/source_manifest.json"
JSON_PATH = ROOT_DIR / "data/exports/d3/assemblee_pilot_timeline.json"

EXPECTED_COLUMNS = [
    "intervention_id",
    "seance_id",
    "ordre",
    "point_titre",
    "sous_point_titre",
    "orateur_nom",
    "orateur_qualite",
    "code_grammaire",
    "roledebat",
    "texte",
    "nb_mots",
    "nb_caracteres",
]

EXPECTED_JSON_FIELDS = EXPECTED_COLUMNS + ["signal_intensity"]


class BuildAssembleePilotTest(unittest.TestCase):
    def test_script_produces_expected_outputs(self) -> None:
        subprocess.run([sys.executable, str(SCRIPT_PATH)], check=True, cwd=ROOT_DIR)

        self.assertTrue(MANIFEST_PATH.exists(), "Le manifest doit être créé.")
        self.assertTrue(CSV_PATH.exists(), "Le CSV doit être créé.")
        self.assertTrue(JSON_PATH.exists(), "Le JSON D3 doit être créé.")

        with CSV_PATH.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, EXPECTED_COLUMNS)
            first_row = next(reader, None)

        self.assertIsNotNone(first_row, "Le CSV doit contenir au moins une ligne.")

        with JSON_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertIsInstance(payload, list, "Le JSON D3 doit contenir une liste.")
        self.assertGreater(len(payload), 0, "Le JSON D3 doit contenir au moins une intervention.")
        self.assertEqual(list(payload[0].keys()), EXPECTED_JSON_FIELDS)


if __name__ == "__main__":
    unittest.main()
