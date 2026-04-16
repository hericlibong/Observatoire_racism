import tempfile
import unittest
import zipfile
from pathlib import Path

from src.assemblee_contextualization.source_acquisition import (
    download_zip_archive,
    extract_session_xml_from_zip,
    file_sha256,
    import_session_xml,
    list_session_xmls_in_zip,
    read_session_xml_metadata,
)
from src.assemblee_contextualization.source_inventory import parse_local_session_xml


XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">
  <uid>{seance_id}</uid>
  <metadonnees>
    <dateSeance>{raw_date}</dateSeance>
    <dateSeanceJour>{date_label}</dateSeanceJour>
  </metadonnees>
  <contenu>{content}</contenu>
</compteRendu>
"""


def write_xml(
    directory: Path,
    filename: str,
    seance_id: str = "CRSANR5L17S2026O1N191",
    raw_date: str = "20260402110000000",
    date_label: str = "jeudi 02 avril 2026",
    content: str = "",
) -> Path:
    path = directory / filename
    path.write_text(
        XML_TEMPLATE.format(
            seance_id=seance_id,
            raw_date=raw_date,
            date_label=date_label,
            content=content,
        ),
        encoding="utf-8",
    )
    return path


def zip_bytes(files: dict[str, str]) -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        zip_path = Path(directory) / "syseron.xml.zip"
        with zipfile.ZipFile(zip_path, "w") as archive:
            for filename, payload in files.items():
                archive.writestr(filename, payload)
        return zip_path.read_bytes()


class SourceAcquisitionTest(unittest.TestCase):
    def test_file_sha256_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(b"abc")

            self.assertEqual(
                file_sha256(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
            self.assertEqual(file_sha256(path), file_sha256(path))

    def test_downloads_zip_archive_with_injected_fetcher(self) -> None:
        payload = zip_bytes(
            {
                "syseron.xml/xml/compteRendu/CRSANR5L17S2026O1N191.xml": XML_TEMPLATE.format(
                    seance_id="CRSANR5L17S2026O1N191",
                    raw_date="20260402110000000",
                    date_label="jeudi 02 avril 2026",
                    content="",
                )
            }
        )

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "syseron.xml.zip"
            result = download_zip_archive(
                "https://example.test/syseron.xml.zip",
                destination,
                fetcher=lambda url: payload,
            )

            self.assertEqual(result.status, "downloaded")
            self.assertEqual(result.bytes_written, len(payload))
            self.assertTrue(destination.exists())
            self.assertEqual(file_sha256(destination), result.content_hash)

    def test_download_zip_archive_reports_unchanged_archive(self) -> None:
        payload = zip_bytes({"sample.xml": "<root />"})

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "syseron.xml.zip"
            download_zip_archive("https://example.test/syseron.xml.zip", destination, fetcher=lambda url: payload)
            result = download_zip_archive(
                "https://example.test/syseron.xml.zip",
                destination,
                fetcher=lambda url: payload,
            )

            self.assertEqual(result.status, "unchanged")

    def test_download_zip_archive_refuses_different_archive_without_overwrite(self) -> None:
        first_payload = zip_bytes({"first.xml": "<root />"})
        second_payload = zip_bytes({"second.xml": "<root />"})

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "syseron.xml.zip"
            download_zip_archive("https://example.test/syseron.xml.zip", destination, fetcher=lambda url: first_payload)

            with self.assertRaises(FileExistsError):
                download_zip_archive(
                    "https://example.test/syseron.xml.zip",
                    destination,
                    fetcher=lambda url: second_payload,
                    overwrite=False,
                )

    def test_download_zip_archive_rejects_invalid_zip_without_replacing_existing(self) -> None:
        payload = zip_bytes({"sample.xml": "<root />"})

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "syseron.xml.zip"
            download_zip_archive("https://example.test/syseron.xml.zip", destination, fetcher=lambda url: payload)
            before_hash = file_sha256(destination)

            with self.assertRaises(ValueError):
                download_zip_archive(
                    "https://example.test/syseron.xml.zip",
                    destination,
                    fetcher=lambda url: b"not a zip",
                )

            self.assertEqual(file_sha256(destination), before_hash)

    def test_reads_minimal_session_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory)
            source_path = write_xml(source_dir, "CRSANR5L17S2026O1N191.xml")

            metadata = read_session_xml_metadata(source_path)

            self.assertEqual(metadata.source_file, "CRSANR5L17S2026O1N191.xml")
            self.assertEqual(metadata.seance_id, "CRSANR5L17S2026O1N191")
            self.assertEqual(metadata.seance_date, "2026-04-02")
            self.assertEqual(metadata.seance_date_label, "jeudi 02 avril 2026")
            self.assertEqual(metadata.local_path, str(source_path))

    def test_imports_valid_local_xml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "incoming"
            destination_dir = root / "raw"
            source_dir.mkdir()
            source_path = write_xml(source_dir, "CRSANR5L17S2026O1N191.xml")

            result = import_session_xml(source_path, destination_dir)

            self.assertEqual(result.status, "imported")
            self.assertEqual(result.source_file, "CRSANR5L17S2026O1N191.xml")
            self.assertTrue((destination_dir / "CRSANR5L17S2026O1N191.xml").exists())
            self.assertEqual(result.content_hash, file_sha256(source_path))
            self.assertEqual(result.metadata.seance_date, "2026-04-02")
            self.assertEqual(
                parse_local_session_xml(Path(result.destination_path)).seance_id,
                "CRSANR5L17S2026O1N191",
            )

    def test_refuses_identical_duplicate_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "incoming"
            destination_dir = root / "raw"
            source_dir.mkdir()
            source_path = write_xml(source_dir, "CRSANR5L17S2026O1N191.xml")

            first_result = import_session_xml(source_path, destination_dir)
            second_result = import_session_xml(source_path, destination_dir)

            self.assertEqual(first_result.status, "imported")
            self.assertEqual(second_result.status, "already_exists")
            self.assertEqual(first_result.content_hash, second_result.content_hash)

    def test_detects_conflict_same_name_different_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_source_dir = root / "incoming_1"
            second_source_dir = root / "incoming_2"
            destination_dir = root / "raw"
            first_source_dir.mkdir()
            second_source_dir.mkdir()
            import_session_xml(
                write_xml(first_source_dir, "CRSANR5L17S2026O1N191.xml", content="original"),
                destination_dir,
            )
            conflict_path = write_xml(
                second_source_dir,
                "CRSANR5L17S2026O1N191.xml",
                content="different",
            )

            with self.assertRaises(FileExistsError):
                import_session_xml(conflict_path, destination_dir)

    def test_overwrites_conflict_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_source_dir = root / "incoming_1"
            second_source_dir = root / "incoming_2"
            destination_dir = root / "raw"
            first_source_dir.mkdir()
            second_source_dir.mkdir()
            import_session_xml(
                write_xml(first_source_dir, "CRSANR5L17S2026O1N191.xml", content="original"),
                destination_dir,
            )
            replacement_path = write_xml(
                second_source_dir,
                "CRSANR5L17S2026O1N191.xml",
                content="replacement",
            )

            result = import_session_xml(replacement_path, destination_dir, overwrite=True)

            self.assertEqual(result.status, "overwritten")
            self.assertEqual(result.content_hash, file_sha256(replacement_path))

    def test_lists_and_extracts_target_xml_from_zip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "incoming"
            destination_dir = root / "raw"
            source_dir.mkdir()
            source_path = write_xml(source_dir, "CRSANR5L17S2026O1N191.xml")
            zip_path = root / "syseron.xml.zip"

            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.write(
                    source_path,
                    "syseron.xml/xml/compteRendu/CRSANR5L17S2026O1N191.xml",
                )

            self.assertEqual(list_session_xmls_in_zip(zip_path), ["CRSANR5L17S2026O1N191.xml"])

            result = extract_session_xml_from_zip(
                zip_path,
                "CRSANR5L17S2026O1N191.xml",
                destination_dir,
            )

            self.assertEqual(result.status, "imported")
            self.assertTrue((destination_dir / "CRSANR5L17S2026O1N191.xml").exists())

    def test_rejects_invalid_or_non_parseable_xml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.xml"
            path.write_text(
                '<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel"><uid>missing',
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                read_session_xml_metadata(path)

    def test_import_only_copies_xml_without_v2_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "incoming"
            destination_dir = root / "raw"
            source_dir.mkdir()
            source_path = write_xml(source_dir, "CRSANR5L17S2026O1N191.xml")

            import_session_xml(source_path, destination_dir)

            self.assertEqual(
                [path.name for path in destination_dir.iterdir()],
                ["CRSANR5L17S2026O1N191.xml"],
            )


if __name__ == "__main__":
    unittest.main()
