from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator
import xml.etree.ElementTree as ET

from .paths import SOURCE_DIR
from .signal_rules import signal_hit_from_text


NS = {"a": "http://schemas.assemblee-nationale.fr/referentiel"}

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


def parse_source_file(source_file: str | Path) -> list[InterventionRow]:
    path = _resolve_source_path(source_file)
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


def write_csv(rows: list[InterventionRow], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _resolve_source_path(source_file: str | Path) -> Path:
    path = Path(source_file)
    if path.exists():
        return path
    return SOURCE_DIR / path
