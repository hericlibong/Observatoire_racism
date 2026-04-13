import json
import tempfile
import unittest
from pathlib import Path

from src.assemblee_contextualization.contracts import (
    ContextualReviewOutputV2,
    Confidence,
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
)
from src.assemblee_contextualization.mock_provider_v2 import MockContextualReviewProviderV2
from src.assemblee_contextualization.run_pilot_v2 import (
    read_outputs_v2,
    review_candidates_v2,
    select_review_ids,
    summarize_outputs_v2,
    write_comparison_summary,
    validate_fallback_invariants,
    write_outputs_v2,
)
from tests.assemblee_contextualization.test_context_builder import sample_interventions


class RunPilotV2Test(unittest.TestCase):
    def test_review_candidates_v2_validates_outputs(self) -> None:
        outputs = review_candidates_v2(
            sample_interventions(),
            MockContextualReviewProviderV2(),
            source_file="pilot.xml",
            window=1,
        )

        self.assertEqual([output.candidate_id for output in outputs], ["i3", "i5"])
        self.assertTrue(all(not output.is_fallback for output in outputs))
        self.assertTrue(all(output.scope_level == ScopeLevel.ADJACENT for output in outputs))
        self.assertTrue(all(output.signal_category == SignalCategory.AMBIGUOUS for output in outputs))

    def test_write_outputs_v2_writes_valid_jsonl(self) -> None:
        outputs = review_candidates_v2(
            sample_interventions(),
            MockContextualReviewProviderV2(),
            source_file="pilot.xml",
            window=1,
        )

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "contextual_reviews_pilot_v2.jsonl"
            write_outputs_v2(outputs, output_path)
            lines = output_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 2)
        for line in lines:
            validate_review_output_v2(json.loads(line))

    def test_select_review_ids_samples_when_no_rule_based_candidates(self) -> None:
        rows = [
            {**row, "signal_candidate": False, "signal_family": "", "signal_trigger": "", "signal_intensity": 0}
            for row in sample_interventions()
        ]

        review_ids, allow_non_candidates = select_review_ids(rows, sample_size_when_no_candidates=3)

        self.assertTrue(allow_non_candidates)
        self.assertEqual(len(review_ids), 3)

    def test_review_candidates_v2_can_review_sample_without_rule_based_candidates(self) -> None:
        rows = [
            {**row, "signal_candidate": False, "signal_family": "", "signal_trigger": "", "signal_intensity": 0}
            for row in sample_interventions()
        ]

        outputs = review_candidates_v2(
            rows,
            MockContextualReviewProviderV2(),
            source_file="pilot.xml",
            window=1,
            sample_size_when_no_candidates=2,
        )

        self.assertEqual(len(outputs), 2)
        self.assertTrue(all(output.signal_category == SignalCategory.AMBIGUOUS for output in outputs))

    def test_summary_keeps_fallback_out_of_substantive_hors_perimetre(self) -> None:
        fallback = ContextualReviewOutputV2(
            candidate_id="fallback",
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
        hors_perimetre = ContextualReviewOutputV2(
            candidate_id="clear",
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

        validate_fallback_invariants([fallback, hors_perimetre])
        summary = summarize_outputs_v2([fallback, hors_perimetre])

        self.assertEqual(summary["fallback_technical"], 1)
        self.assertEqual(summary["substantive_hors_perimetre"], 1)

    def test_comparison_summary_excludes_fallback_from_substantive_metrics(self) -> None:
        fallback = ContextualReviewOutputV2(
            candidate_id="s1_fallback",
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
        adjacent = ContextualReviewOutputV2(
            candidate_id="s1_adjacent",
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
        clear = ContextualReviewOutputV2(
            candidate_id="s2_clear",
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


if __name__ == "__main__":
    unittest.main()
