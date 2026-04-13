import unittest

from src.assemblee_contextualization.contracts import (
    Confidence,
    ContextualReviewOutputV2,
    ScopeLevel,
    SignalCategory,
)
from src.assemblee_contextualization.heatmap_export import build_heatmap_session_payload


class HeatmapExportTest(unittest.TestCase):
    def test_builds_prudent_click_detail_payload(self) -> None:
        payload = build_heatmap_session_payload(
            source_file="CRSANR5L17S2026O1N191.xml",
            journal_entry={
                "seance_id": "CRSANR5L17S2026O1N191",
                "source_file": "CRSANR5L17S2026O1N191.xml",
                "seance_date": "2026-04-02",
                "seance_date_label": "jeudi 02 avril 2026",
                "processed_at": "2026-04-13T20:14:00+02:00",
                "provider": "mistral_v2",
                "model_name": "mistral-medium-latest",
            },
            interventions=[
                {
                    "intervention_id": "CRSANR5L17S2026O1N191_1",
                    "seance_id": "CRSANR5L17S2026O1N191",
                    "ordre": 7,
                    "orateur_nom": "Mme Exemple",
                    "point_titre": "Point",
                    "sous_point_titre": "Sous-point",
                    "texte": "Texte parlementaire relu.",
                }
            ],
            outputs=[
                ContextualReviewOutputV2(
                    candidate_id="CRSANR5L17S2026O1N191_1",
                    scope_level=ScopeLevel.ADJACENT,
                    signal_category=SignalCategory.PROBLEMATIC_GROUP_TARGETING,
                    is_fallback=False,
                    needs_human_review=True,
                    confidence=Confidence.MEDIUM,
                    rationale="Cas a revoir.",
                    evidence_span="Texte parlementaire",
                    limits=["Analyse locale."],
                    model_provider="mistral_v2",
                    model_name="mistral-medium-latest",
                )
            ],
        )

        item = payload["items"][0]
        self.assertTrue(payload["fallbacks_excluded_from_substantive_metrics"])
        self.assertEqual(payload["metrics"]["non_fallback_items"], 1)
        self.assertEqual(payload["metrics"]["substantive_items"], 1)
        self.assertEqual(payload["axis"]["field"], "ordre")
        for field in (
            "ordre",
            "axis_position",
            "intervention_id",
            "orateur_nom",
            "point_titre",
            "sous_point_titre",
            "excerpt",
            "evidence_span",
            "scope_level",
            "signal_category",
            "confidence",
            "needs_human_review",
            "is_fallback",
            "review_label",
        ):
            self.assertIn(field, item)
        self.assertEqual(item["seance_date"], "2026-04-02")
        self.assertEqual(item["ordre"], 7)
        self.assertEqual(item["review_label"], "signal \u00e0 revoir")
        self.assertNotIn("valid\u00e9", item["review_label"])

    def test_keeps_fallback_visible_but_out_of_substantive_metrics(self) -> None:
        payload = build_heatmap_session_payload(
            source_file="CRSANR5L17S2026O1N191.xml",
            journal_entry={
                "seance_id": "CRSANR5L17S2026O1N191",
                "source_file": "CRSANR5L17S2026O1N191.xml",
                "seance_date": "2026-04-02",
                "seance_date_label": "jeudi 02 avril 2026",
                "processed_at": "2026-04-13T20:14:00+02:00",
                "provider": "mistral_v2",
                "model_name": "mistral-medium-latest",
            },
            interventions=[
                {
                    "intervention_id": "CRSANR5L17S2026O1N191_1",
                    "seance_id": "CRSANR5L17S2026O1N191",
                    "ordre": 1,
                    "orateur_nom": "",
                    "point_titre": "",
                    "sous_point_titre": "",
                    "texte": "Texte.",
                }
            ],
            outputs=[
                ContextualReviewOutputV2(
                    candidate_id="CRSANR5L17S2026O1N191_1",
                    scope_level=ScopeLevel.HORS_PERIMETRE,
                    signal_category=SignalCategory.AMBIGUOUS,
                    is_fallback=True,
                    needs_human_review=True,
                    confidence=Confidence.LOW,
                    rationale="Fallback technique.",
                    evidence_span="Texte.",
                    limits=["Fallback technique."],
                    model_provider="mistral_v2",
                    model_name="mistral-medium-latest",
                )
            ],
        )

        self.assertEqual(payload["metrics"]["fallback_count"], 1)
        self.assertEqual(payload["metrics"]["non_fallback_items"], 0)
        self.assertEqual(payload["metrics"]["substantive_items"], 0)
        self.assertTrue(payload["items"][0]["is_fallback"])
        self.assertEqual(payload["items"][0]["review_label"], "fallback technique \u00e0 revoir")


if __name__ == "__main__":
    unittest.main()
