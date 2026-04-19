import json
import tempfile
import unittest
from pathlib import Path

from src.assemblee_contextualization.contracts import (
    Confidence,
    ContextualReviewOutputV2,
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
)
from src.assemblee_contextualization.io_v2 import (
    read_outputs_v2,
    summarize_outputs_v2,
    write_comparison_summary,
    write_outputs_v2,
)


class IoV2Test(unittest.TestCase):
    def test_write_outputs_v2_writes_valid_jsonl(self) -> None:
        outputs = [_adjacent_output("s1_adjacent"), _clear_output("s1_clear")]

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "contextual_reviews_pilot_v2.jsonl"
            write_outputs_v2(outputs, output_path)
            lines = output_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 2)
        for line in lines:
            validate_review_output_v2(json.loads(line))

    def test_read_outputs_v2_reads_valid_jsonl(self) -> None:
        outputs = [_adjacent_output("s1_adjacent")]

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "contextual_reviews_pilot_v2.jsonl"
            write_outputs_v2(outputs, output_path)
            loaded = read_outputs_v2(output_path)

        self.assertEqual([output.candidate_id for output in loaded], ["s1_adjacent"])

    def test_summary_keeps_fallback_out_of_substantive_hors_perimetre(self) -> None:
        fallback = _fallback_output("s1_fallback")
        hors_perimetre = _clear_output("s1_clear")

        summary = summarize_outputs_v2([fallback, hors_perimetre])

        self.assertEqual(summary["fallback_technical"], 1)
        self.assertEqual(summary["substantive_hors_perimetre"], 1)

    def test_comparison_summary_excludes_fallback_from_substantive_metrics(self) -> None:
        fallback = _fallback_output("s1_fallback")
        adjacent = _adjacent_output("s1_adjacent")
        clear = _clear_output("s2_clear")

        with tempfile.TemporaryDirectory() as directory:
            mixed_path = Path(directory) / "mixed.jsonl"
            clear_path = Path(directory) / "clear.jsonl"
            summary_path = Path(directory) / "summary.json"
            write_outputs_v2([fallback, adjacent, clear], mixed_path)
            write_outputs_v2([clear], clear_path)
            summary = write_comparison_summary([mixed_path, clear_path], summary_path)

            self.assertEqual(len(read_outputs_v2(mixed_path)), 3)
            self.assertTrue(summary_path.exists())

        self.assertTrue(summary["fallbacks_excluded_from_substantive_metrics"])
        self.assertEqual(summary["sessions"][0]["fallback_technical"], 1)
        self.assertEqual(summary["sessions"][0]["true_hors_perimetre_no_signal"], 1)
        self.assertEqual(summary["sessions"][0]["scope_level_distribution"]["hors_perimetre"], 2)
        self.assertEqual(summary["sessions"][0]["signal_category_distribution"]["ambiguous"], 2)
        self.assertEqual(
            summary["sessions"][0]["substantive_scope_level_distribution"],
            {"adjacent": 1, "hors_perimetre": 1},
        )
        self.assertEqual(
            summary["sessions"][0]["substantive_signal_category_distribution"],
            {"ambiguous": 1, "no_signal": 1},
        )
        self.assertEqual(summary["sessions"][1]["true_hors_perimetre_no_signal"], 1)


def _fallback_output(candidate_id: str) -> ContextualReviewOutputV2:
    return ContextualReviewOutputV2(
        candidate_id=candidate_id,
        scope_level=ScopeLevel.HORS_PERIMETRE,
        signal_category=SignalCategory.AMBIGUOUS,
        is_fallback=True,
        needs_human_review=True,
        confidence=Confidence.LOW,
        rationale="Fallback technique.",
        evidence_span="",
        limits=[],
        model_provider="test",
        model_name="test",
    )


def _adjacent_output(candidate_id: str) -> ContextualReviewOutputV2:
    return ContextualReviewOutputV2(
        candidate_id=candidate_id,
        scope_level=ScopeLevel.ADJACENT,
        signal_category=SignalCategory.AMBIGUOUS,
        is_fallback=False,
        needs_human_review=True,
        confidence=Confidence.LOW,
        rationale="Cas frontiere substantif.",
        evidence_span="",
        limits=[],
        model_provider="test",
        model_name="test",
    )


def _clear_output(candidate_id: str) -> ContextualReviewOutputV2:
    return ContextualReviewOutputV2(
        candidate_id=candidate_id,
        scope_level=ScopeLevel.HORS_PERIMETRE,
        signal_category=SignalCategory.NO_SIGNAL,
        is_fallback=False,
        needs_human_review=False,
        confidence=Confidence.HIGH,
        rationale="Aucun ancrage dans le perimetre.",
        evidence_span="",
        limits=[],
        model_provider="test",
        model_name="test",
    )


if __name__ == "__main__":
    unittest.main()
