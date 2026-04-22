from __future__ import annotations

import csv
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.assemblee_contextualization.xml_parser import (
    CSV_FIELDS,
    InterventionRow,
    child_text,
    element_text,
    iter_paragraphs,
    normalize_text,
    paragraph_id,
    parse_source_file,
    write_csv,
)


ANS = "http://schemas.assemblee-nationale.fr/referentiel"


def _el(tag: str, text: str | None = None) -> ET.Element:
    elem = ET.Element(f"{{{ANS}}}{tag}")
    if text is not None:
        elem.text = text
    return elem


def _make_compte_rendu(uid: str, paragraphs: list[tuple[str, int, str]]) -> ET.Element:
    root = ET.Element(f"{{{ANS}}}compteRendu")
    uid_elem = ET.SubElement(root, f"{{{ANS}}}uid")
    uid_elem.text = uid
    contenu = ET.SubElement(root, f"{{{ANS}}}contenu")
    point = ET.SubElement(contenu, f"{{{ANS}}}point")
    point.set("nivpoint", "1")
    pt = ET.SubElement(point, f"{{{ANS}}}texte")
    pt.text = "Point principal"
    for id_syceron, ordre, text in paragraphs:
        para = ET.SubElement(point, f"{{{ANS}}}paragraphe")
        para.set("id_syceron", id_syceron)
        para.set("ordre_absolu_seance", str(ordre))
        texte = ET.SubElement(para, f"{{{ANS}}}texte")
        texte.text = text
    return root


class NormalizeTextTest(unittest.TestCase):
    def test_collapses_internal_whitespace(self) -> None:
        self.assertEqual(normalize_text("hello   world"), "hello world")

    def test_replaces_nbsp(self) -> None:
        self.assertEqual(normalize_text("hello\xa0world"), "hello world")

    def test_strips_edges(self) -> None:
        self.assertEqual(normalize_text("  hello  "), "hello")


class ElementTextTest(unittest.TestCase):
    def test_returns_empty_for_none(self) -> None:
        self.assertEqual(element_text(None), "")

    def test_returns_text_content(self) -> None:
        elem = _el("texte", "Bonjour")
        self.assertEqual(element_text(elem), "Bonjour")

    def test_concatenates_itertext(self) -> None:
        parent = ET.Element(f"{{{ANS}}}texte")
        parent.text = "Hello "
        child = ET.SubElement(parent, f"{{{ANS}}}em")
        child.text = "world"
        self.assertEqual(element_text(parent), "Hello world")


class ChildTextTest(unittest.TestCase):
    def test_returns_empty_when_child_missing(self) -> None:
        parent = ET.Element(f"{{{ANS}}}root")
        self.assertEqual(child_text(parent, "missing"), "")

    def test_returns_text_when_child_found(self) -> None:
        parent = ET.Element(f"{{{ANS}}}root")
        uid = ET.SubElement(parent, f"{{{ANS}}}uid")
        uid.text = "CRSANR5L17S2026O1N191"
        self.assertEqual(child_text(parent, "uid"), "CRSANR5L17S2026O1N191")


class ParagraphIdTest(unittest.TestCase):
    def test_uses_id_syceron_when_present(self) -> None:
        para = ET.Element(f"{{{ANS}}}paragraphe")
        para.set("id_syceron", "P042")
        self.assertEqual(paragraph_id(para, "UID123", 0), "UID123_P042")

    def test_uses_fallback_when_id_syceron_absent(self) -> None:
        para = ET.Element(f"{{{ANS}}}paragraphe")
        self.assertEqual(paragraph_id(para, "UID123", 7), "UID123_fallback_7")


class IterParagraphsTest(unittest.TestCase):
    def test_yields_one_row_per_paragraph(self) -> None:
        root = _make_compte_rendu("UID001", [
            ("P001", 1, "Premier texte."),
            ("P002", 2, "Deuxieme texte."),
        ])
        contenu = root.find(f"{{{ANS}}}contenu")
        assert contenu is not None
        rows = list(iter_paragraphs(contenu, "UID001", "", ""))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].intervention_id, "UID001_P001")
        self.assertEqual(rows[1].intervention_id, "UID001_P002")

    def test_skips_empty_paragraphs(self) -> None:
        root = _make_compte_rendu("UID001", [
            ("P001", 1, ""),
            ("P002", 2, "Texte valide."),
        ])
        contenu = root.find(f"{{{ANS}}}contenu")
        assert contenu is not None
        rows = list(iter_paragraphs(contenu, "UID001", "", ""))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].intervention_id, "UID001_P002")

    def test_row_has_expected_fields(self) -> None:
        root = _make_compte_rendu("UID001", [("P001", 5, "Texte de test.")])
        contenu = root.find(f"{{{ANS}}}contenu")
        assert contenu is not None
        row = list(iter_paragraphs(contenu, "UID001", "", ""))[0]
        self.assertEqual(row.ordre, 5)
        self.assertEqual(row.texte, "Texte de test.")
        self.assertEqual(row.point_titre, "Point principal")
        self.assertIsInstance(row.signal_candidate, bool)


class ParseSourceFileTest(unittest.TestCase):
    def test_raises_for_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            parse_source_file("/nonexistent/file.xml")

    def test_parses_minimal_xml(self, tmp_path: Path = None) -> None:  # type: ignore[assignment]
        import tempfile

        root = _make_compte_rendu("CRSANR5L17S2026O1N191", [
            ("P001", 1, "Texte de l'intervention."),
        ])
        tree = ET.ElementTree(root)

        with tempfile.TemporaryDirectory() as directory:
            xml_path = Path(directory) / "session.xml"
            tree.write(str(xml_path), xml_declaration=True, encoding="utf-8")
            rows = parse_source_file(xml_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].seance_id, "CRSANR5L17S2026O1N191")
        self.assertEqual(rows[0].intervention_id, "CRSANR5L17S2026O1N191_P001")


class WriteCsvTest(unittest.TestCase):
    def test_produces_expected_columns(self) -> None:
        import tempfile

        rows = [
            InterventionRow(
                intervention_id="ID001",
                seance_id="SID001",
                ordre=1,
                point_titre="Point",
                sous_point_titre="",
                orateur_nom="Dupont",
                orateur_qualite="Député",
                code_grammaire="",
                roledebat="",
                texte="Texte.",
                nb_mots=1,
                nb_caracteres=6,
                signal_candidate=False,
                signal_family="",
                signal_trigger="",
                signal_intensity=0,
            )
        ]
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "out.csv"
            write_csv(rows, output_path)
            with output_path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, CSV_FIELDS)
                first = next(reader)

        self.assertEqual(first["intervention_id"], "ID001")
        self.assertEqual(first["texte"], "Texte.")


if __name__ == "__main__":
    unittest.main()
