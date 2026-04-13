from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator
import xml.etree.ElementTree as ET


NS = {"a": "http://schemas.assemblee-nationale.fr/referentiel"}

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "data/raw/assemblee/extracted/syceron_initial_import/syseron.xml/xml/compteRendu"
PILOT_FILENAME = "CRSANR5L17S2026O1N191.xml"
PILOT_PATH = SOURCE_DIR / PILOT_FILENAME
INTERIM_DIR = ROOT_DIR / "data/interim/assemblee"
MANIFEST_PATH = INTERIM_DIR / "source_manifest.json"
CSV_PATH = INTERIM_DIR / "interventions_test.csv"
EXPORTS_D3_DIR = ROOT_DIR / "data/exports/d3"
JSON_PATH = EXPORTS_D3_DIR / "assemblee_pilot_timeline.json"

CSV_FIELDS = [
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
    "signal_candidate",
    "signal_family",
    "signal_trigger",
    "signal_intensity",
]


@dataclass(frozen=True)
class SignalRule:
    family: str
    trigger: str
    intensity: int


@dataclass(frozen=True)
class SignalHit:
    signal_candidate: bool
    signal_family: str
    signal_trigger: str
    signal_intensity: int


SIGNAL_RULES = [
    SignalRule("devalorisation", "honteuse", 2),
    SignalRule("devalorisation", "une honte", 2),
    SignalRule("devalorisation", "propos deshonorants", 2),
    SignalRule("devalorisation", "inadmissibles", 2),
    SignalRule("devalorisation", "irresponsable", 2),
    SignalRule("devalorisation", "inacceptable", 2),
    SignalRule("devalorisation", "mepris", 2),
    SignalRule("devalorisation", "trahir", 2),
    SignalRule("tension_politique", "passage en force", 2),
    SignalRule("tension_politique", "ligne rouge", 2),
    SignalRule("tension_politique", "chaos", 2),
    SignalRule("tension_politique", "colere", 2),
    SignalRule("tension_politique", "violences", 2),
    SignalRule("tension_politique", "obstruction", 2),
    SignalRule("designation_groupe", "anti-independantistes", 2),
    SignalRule("designation_groupe", "puissance colonisatrice", 2),
    SignalRule("designation_groupe", "independantistes", 1),
    SignalRule("designation_groupe", "non-independantistes", 1),
    SignalRule("designation_groupe", "peuple kanak", 1),
    SignalRule("designation_groupe", "identite kanak", 1),
    SignalRule("designation_groupe", "communautes", 1),
    SignalRule("designation_groupe", "loyalistes", 1),
    SignalRule("designation_groupe", "kanaky", 1),
    SignalRule("designation_groupe", "flnks", 1),
]


@dataclass
class InterventionRow:
    intervention_id: str
    seance_id: str
    ordre: int
    point_titre: str
    sous_point_titre: str
    orateur_nom: str
    orateur_qualite: str
    code_grammaire: str
    roledebat: str
    texte: str
    nb_mots: int
    nb_caracteres: int
    signal_candidate: bool
    signal_family: str
    signal_trigger: str
    signal_intensity: int


def normalize_for_signal(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.replace("’", "'")).strip()


def signal_hit_from_text(text: str) -> SignalHit:
    normalized = normalize_for_signal(text)
    best_match: SignalRule | None = None

    for rule in SIGNAL_RULES:
        trigger = normalize_for_signal(rule.trigger)
        if re.search(rf"(?<!\w){re.escape(trigger)}(?!\w)", normalized):
            if best_match is None or rule.intensity > best_match.intensity:
                best_match = rule

    if best_match is None:
        return SignalHit(False, "", "", 0)

    return SignalHit(True, best_match.family, best_match.trigger, best_match.intensity)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    chunks = [normalize_text(part) for part in element.itertext()]
    chunks = [chunk for chunk in chunks if chunk]
    return normalize_text(" ".join(chunks))


def child_text(element: ET.Element, child_name: str) -> str:
    child = element.find(f"a:{child_name}", NS)
    return element_text(child)


def first_orateur(paragraph: ET.Element) -> tuple[str, str]:
    orateur = paragraph.find("a:orateurs/a:orateur", NS)
    if orateur is None:
        return "", ""
    return child_text(orateur, "nom"), child_text(orateur, "qualite")


def paragraph_text(paragraph: ET.Element) -> str:
    texte = paragraph.find("a:texte", NS)
    return element_text(texte)


def paragraph_id(paragraph: ET.Element, compte_rendu_uid: str, fallback_index: int) -> str:
    id_syceron = paragraph.attrib.get("id_syceron")
    if id_syceron:
        return f"{compte_rendu_uid}_{id_syceron}"
    return f"{compte_rendu_uid}_fallback_{fallback_index}"


def point_context(
    element: ET.Element,
    point_titre: str,
    sous_point_titre: str,
) -> tuple[str, str]:
    tag = element.tag.split("}")[-1]
    if tag in {"ouvertureSeance", "finSeance"}:
        direct_title = child_text(element, "texte")
        if direct_title:
            return direct_title, ""
        return point_titre, sous_point_titre

    if tag == "point":
        direct_title = child_text(element, "texte")
        if direct_title:
            level = element.attrib.get("nivpoint", "")
            if level == "1" or not point_titre:
                return direct_title, ""
            return point_titre, direct_title

    return point_titre, sous_point_titre


def iter_paragraphs(
    element: ET.Element,
    compte_rendu_uid: str,
    point_titre: str,
    sous_point_titre: str,
) -> Iterator[InterventionRow]:
    point_titre, sous_point_titre = point_context(element, point_titre, sous_point_titre)

    for child in list(element):
        child_tag = child.tag.split("}")[-1]
        if child_tag == "paragraphe":
            texte = paragraph_text(child)
            if not texte:
                continue
            signal_hit = signal_hit_from_text(texte)
            orateur_nom, orateur_qualite = first_orateur(child)
            ordre_raw = child.attrib.get("ordre_absolu_seance", "0")
            try:
                ordre = int(ordre_raw)
            except ValueError:
                ordre = 0
            yield InterventionRow(
                intervention_id=paragraph_id(child, compte_rendu_uid, ordre),
                seance_id="",
                ordre=ordre,
                point_titre=point_titre,
                sous_point_titre=sous_point_titre,
                orateur_nom=orateur_nom,
                orateur_qualite=orateur_qualite,
                code_grammaire=child.attrib.get("code_grammaire", ""),
                roledebat=child.attrib.get("roledebat", ""),
                texte=texte,
                nb_mots=len(texte.split()),
                nb_caracteres=len(texte),
                signal_candidate=signal_hit.signal_candidate,
                signal_family=signal_hit.signal_family,
                signal_trigger=signal_hit.signal_trigger,
                signal_intensity=signal_hit.signal_intensity,
            )
        elif child_tag in {"point", "ouvertureSeance", "finSeance", "interExtraction"}:
            yield from iter_paragraphs(child, compte_rendu_uid, point_titre, sous_point_titre)


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


def source_path(source_file: str | Path) -> Path:
    path = Path(source_file)
    if path.exists():
        return path
    return SOURCE_DIR / path


def parse_source_file(source_file: str | Path) -> list[InterventionRow]:
    path = source_path(source_file)
    if not path.exists():
        raise FileNotFoundError(f"Fichier Assemblee introuvable : {path}")

    root = ET.parse(path).getroot()
    compte_rendu_uid = child_text(root, "uid")
    if not compte_rendu_uid:
        raise ValueError(f"UID introuvable dans {path}.")

    contenu = root.find("a:contenu", NS)
    if contenu is None:
        raise ValueError(f"Element contenu introuvable dans {path}.")

    rows = list(iter_paragraphs(contenu, compte_rendu_uid, "", ""))
    for row in rows:
        row.seance_id = compte_rendu_uid
    rows.sort(key=lambda row: (row.ordre, row.intervention_id))
    return rows


def parse_pilot() -> list[InterventionRow]:
    return parse_source_file(PILOT_PATH)


def write_csv(rows: list[InterventionRow], output_path: Path = CSV_PATH) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


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
    write_csv(rows)
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
