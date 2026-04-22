from __future__ import annotations

import csv
import json
from datetime import datetime

from assemblee_contextualization.paths import EXPORTS_D3_DIR, INTERIM_DIR, ROOT_DIR, SOURCE_DIR
from assemblee_contextualization.sources.xml_parser import (
    InterventionRow,
    parse_source_file,
    write_csv,
)


PILOT_FILENAME = "CRSANR5L17S2026O1N191.xml"
PILOT_PATH = SOURCE_DIR / PILOT_FILENAME
MANIFEST_PATH = INTERIM_DIR / "source_manifest.json"
CSV_PATH = INTERIM_DIR / "interventions_test.csv"
JSON_PATH = EXPORTS_D3_DIR / "assemblee_pilot_timeline.json"


def build_manifest() -> dict:
    files = []
    for path in sorted(SOURCE_DIR.glob("*.xml")):
        stat = path.stat()
        files.append(
            {
                "nom_fichier": path.name,
                "chemin": str(path.relative_to(ROOT_DIR)),
                "taille_octets": stat.st_size,
                "mtime_local": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
            }
        )

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "root": str(SOURCE_DIR.relative_to(ROOT_DIR)),
        "files": files,
    }


def parse_pilot() -> list[InterventionRow]:
    return parse_source_file(PILOT_PATH)


def build_d3_json_from_csv() -> list[dict[str, object]]:
    interventions: list[dict[str, object]] = []

    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            intervention = {
                "intervention_id": row["intervention_id"],
                "seance_id": row["seance_id"],
                "ordre": int(row["ordre"]),
                "point_titre": row["point_titre"],
                "sous_point_titre": row["sous_point_titre"],
                "orateur_nom": row["orateur_nom"],
                "orateur_qualite": row["orateur_qualite"],
                "code_grammaire": row["code_grammaire"],
                "roledebat": row["roledebat"],
                "texte": row["texte"],
                "nb_mots": int(row["nb_mots"]),
                "nb_caracteres": int(row["nb_caracteres"]),
                "signal_candidate": row["signal_candidate"] == "True",
                "signal_family": row["signal_family"],
                "signal_trigger": row["signal_trigger"],
                "signal_intensity": int(row["signal_intensity"]),
            }
            interventions.append(intervention)

    interventions.sort(key=lambda item: (item["ordre"], item["intervention_id"]))
    for index, intervention in enumerate(interventions, start=1):
        intervention["display_order"] = index
    return interventions


def write_d3_json(interventions: list[dict[str, object]]) -> None:
    EXPORTS_D3_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(interventions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest()
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    rows = parse_pilot()
    write_csv(rows, CSV_PATH)
    d3_interventions = build_d3_json_from_csv()
    write_d3_json(d3_interventions)

    print(f"Manifest écrit : {MANIFEST_PATH.relative_to(ROOT_DIR)} ({len(manifest['files'])} fichiers)")
    print(f"CSV écrit : {CSV_PATH.relative_to(ROOT_DIR)} ({len(rows)} lignes)")
    print(f"JSON écrit : {JSON_PATH.relative_to(ROOT_DIR)} ({len(d3_interventions)} objets)")
    print("Aperçu signaux candidats :")
    for row in [item for item in d3_interventions if item["signal_candidate"]][:5]:
        preview = dict(row)
        preview["texte"] = preview["texte"][:120]
        print(json.dumps(preview, ensure_ascii=False))


if __name__ == "__main__":
    main()
