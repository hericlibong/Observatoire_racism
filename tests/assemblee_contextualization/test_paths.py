from pathlib import Path
import unittest

from src.assemblee_contextualization.paths import (
    ROOT_DIR,
    as_int,
    display_path,
    normalize_syceron_date,
    session_slug,
)


class PathsTest(unittest.TestCase):
    def test_display_path_returns_project_relative_path(self) -> None:
        path = ROOT_DIR / "data/interim/assemblee/output.json"

        self.assertEqual(display_path(path), Path("data/interim/assemblee/output.json"))

    def test_display_path_keeps_external_path(self) -> None:
        path = Path("/tmp/observatoire-output.json")

        self.assertEqual(display_path(path), path)

    def test_session_slug_extracts_assemblee_session_number(self) -> None:
        self.assertEqual(session_slug("CRSANR5L17S2026O1N191.xml"), "n191")

    def test_session_slug_falls_back_to_lowercase_stem(self) -> None:
        self.assertEqual(session_slug("custom_session.xml"), "custom_session")

    def test_as_int_converts_valid_values_and_defaults_invalid_values(self) -> None:
        self.assertEqual(as_int("42"), 42)
        self.assertEqual(as_int(7), 7)
        self.assertEqual(as_int(""), 0)
        self.assertEqual(as_int(None), 0)

    def test_normalize_syceron_date_converts_yyyymmdd_prefix(self) -> None:
        self.assertEqual(normalize_syceron_date("20260402093000", Path("N.xml")), "2026-04-02")

    def test_normalize_syceron_date_rejects_invalid_date(self) -> None:
        with self.assertRaises(ValueError):
            normalize_syceron_date("202604", Path("N.xml"))


if __name__ == "__main__":
    unittest.main()
