from __future__ import annotations

import unittest

from src.assemblee_contextualization.signal_rules import (
    normalize_for_signal,
    signal_hit_from_text,
)


class NormalizeForSignalTest(unittest.TestCase):
    def test_lowercases_text(self) -> None:
        self.assertEqual(normalize_for_signal("CHAOS"), "chaos")

    def test_removes_accents(self) -> None:
        self.assertEqual(normalize_for_signal("mépris"), "mepris")

    def test_normalizes_apostrophes(self) -> None:
        result = normalize_for_signal("l\u2019envahisseur")
        self.assertEqual(result, "l'envahisseur")

    def test_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_for_signal("passage  en  force"), "passage en force")

    def test_strips_leading_and_trailing_space(self) -> None:
        self.assertEqual(normalize_for_signal("  chaos  "), "chaos")


class SignalHitFromTextTest(unittest.TestCase):
    def test_returns_no_hit_for_neutral_text(self) -> None:
        hit = signal_hit_from_text("Ce texte ne contient aucun signal.")
        self.assertFalse(hit.signal_candidate)
        self.assertEqual(hit.signal_trigger, "")
        self.assertEqual(hit.signal_intensity, 0)

    def test_detects_designation_groupe_trigger(self) -> None:
        hit = signal_hit_from_text("Les communautés locales ont été consultées.")
        self.assertTrue(hit.signal_candidate)
        self.assertEqual(hit.signal_family, "designation_groupe")
        self.assertEqual(hit.signal_trigger, "communautes")

    def test_detects_tension_politique_trigger(self) -> None:
        hit = signal_hit_from_text("Ce passage en force est inacceptable.")
        self.assertTrue(hit.signal_candidate)
        self.assertIn(hit.signal_family, {"tension_politique", "devalorisation"})

    def test_selects_highest_intensity_when_multiple_match(self) -> None:
        # "anti-independantistes" intensity 2 vs "independantistes" intensity 1
        hit = signal_hit_from_text("Les anti-independantistes et les independantistes s'affrontent.")
        self.assertTrue(hit.signal_candidate)
        self.assertEqual(hit.signal_trigger, "anti-independantistes")
        self.assertEqual(hit.signal_intensity, 2)

    def test_respects_word_boundary(self) -> None:
        # "chaos" should not match "chaotique"
        hit = signal_hit_from_text("La situation est chaotique.")
        self.assertFalse(hit.signal_candidate)

    def test_returns_no_hit_for_empty_text(self) -> None:
        hit = signal_hit_from_text("")
        self.assertFalse(hit.signal_candidate)
        self.assertEqual(hit.signal_family, "")


if __name__ == "__main__":
    unittest.main()
