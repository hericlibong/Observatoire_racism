import unittest
from pathlib import Path

from src.assemblee_contextualization.contracts import (
    Confidence,
    ContextualReviewOutputV2,
    ScopeLevel,
    SignalCategory,
)
from src.assemblee_contextualization.heatmap_export import build_heatmap_session_payload
from src.assemblee_contextualization.heatmap_export import build_sessions_overview_payload


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

    def test_masks_verdict_terms_in_public_display_snippets(self) -> None:
        payload = build_heatmap_session_payload(
            source_file="CRSANR5L17S2026O1N193.xml",
            journal_entry={
                "seance_id": "CRSANR5L17S2026O1N193",
                "source_file": "CRSANR5L17S2026O1N193.xml",
                "seance_date": "2026-04-07",
                "seance_date_label": "mardi 07 avril 2026",
                "processed_at": "2026-04-17T13:50:23+02:00",
                "provider": "mistral_v2",
                "model_name": "mistral-medium-latest",
            },
            interventions=[
                {
                    "intervention_id": "CRSANR5L17S2026O1N193_1",
                    "seance_id": "CRSANR5L17S2026O1N193",
                    "ordre": 1,
                    "orateur_nom": "",
                    "point_titre": "",
                    "sous_point_titre": "",
                    "texte": "Ce passage parle d'une faute institutionnelle et les soignants alertent.",
                }
            ],
            outputs=[
                ContextualReviewOutputV2(
                    candidate_id="CRSANR5L17S2026O1N193_1",
                    scope_level=ScopeLevel.HORS_PERIMETRE,
                    signal_category=SignalCategory.NO_SIGNAL,
                    is_fallback=False,
                    needs_human_review=False,
                    confidence=Confidence.HIGH,
                    rationale="Aucun ancrage.",
                    evidence_span="une faute institutionnelle et les soignants alertent",
                    limits=["Analyse locale."],
                    model_provider="mistral_v2",
                    model_name="mistral-medium-latest",
                )
            ],
        )

        item = payload["items"][0]
        self.assertNotIn("faute", item["excerpt"].lower())
        self.assertNotIn("faute", item["evidence_span"].lower())
        self.assertNotIn("alert", item["excerpt"].lower())
        self.assertNotIn("alert", item["evidence_span"].lower())
        self.assertIn("[terme du passage]", item["evidence_span"])

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
        self.assertEqual(payload["non_fallback_items"], [])
        self.assertTrue(payload["items"][0]["is_fallback"])
        self.assertEqual(payload["items"][0]["review_label"], "fallback technique \u00e0 revoir")

    def test_builds_payload_for_parameterized_session(self) -> None:
        payload = build_heatmap_session_payload(
            source_file="CRSANR5L17S2026O1N192.xml",
            journal_entry={
                "seance_id": "CRSANR5L17S2026O1N192",
                "source_file": "CRSANR5L17S2026O1N192.xml",
                "seance_date": "2026-04-07",
                "seance_date_label": "mardi 07 avril 2026",
                "processed_at": "2026-04-17T12:16:38+02:00",
                "provider": "mistral_v2",
                "model_name": "mistral-medium-latest",
            },
            interventions=[
                {
                    "intervention_id": "CRSANR5L17S2026O1N192_1",
                    "seance_id": "CRSANR5L17S2026O1N192",
                    "ordre": 3,
                    "orateur_nom": "",
                    "point_titre": "",
                    "sous_point_titre": "",
                    "texte": "Texte N192.",
                }
            ],
            outputs=[
                ContextualReviewOutputV2(
                    candidate_id="CRSANR5L17S2026O1N192_1",
                    scope_level=ScopeLevel.HORS_PERIMETRE,
                    signal_category=SignalCategory.NO_SIGNAL,
                    is_fallback=False,
                    needs_human_review=False,
                    confidence=Confidence.HIGH,
                    rationale="Aucun ancrage.",
                    evidence_span="Texte N192.",
                    limits=["Analyse locale."],
                    model_provider="mistral_v2",
                    model_name="mistral-medium-latest",
                )
            ],
        )

        self.assertEqual(payload["session"]["source_file"], "CRSANR5L17S2026O1N192.xml")
        self.assertEqual(payload["session"]["seance_date"], "2026-04-07")
        self.assertEqual(payload["axis"]["reviewed_items"], 1)
        self.assertEqual(len(payload["non_fallback_items"]), 1)

    def test_overview_keeps_only_treated_sessions_with_detail_view(self) -> None:
        n191_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N191.xml",
            "CRSANR5L17S2026O1N191",
            "2026-04-02",
            "jeudi 02 avril 2026",
            "adjacent",
            "problematic_group_targeting",
        )
        n192_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N192.xml",
            "CRSANR5L17S2026O1N192",
            "2026-04-07",
            "mardi 07 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n193_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N193.xml",
            "CRSANR5L17S2026O1N193",
            "2026-04-07",
            "mardi 07 avril 2026",
            "hors_perimetre",
            "no_signal",
        )

        n194_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N194.xml",
            "CRSANR5L17S2026O1N194",
            "2026-04-07",
            "mardi 07 avril 2026",
            "hors_perimetre",
            "no_signal",
        )

        n195_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N195.xml",
            "CRSANR5L17S2026O1N195",
            "2026-04-07",
            "mardi 07 avril 2026",
            "hors_perimetre",
            "no_signal",
        )

        n196_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N196.xml",
            "CRSANR5L17S2026O1N196",
            "2026-04-08",
            "mercredi 08 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n197_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N197.xml",
            "CRSANR5L17S2026O1N197",
            "2026-04-09",
            "jeudi 09 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n198_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N198.xml",
            "CRSANR5L17S2026O1N198",
            "2026-04-09",
            "jeudi 09 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n199_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N199.xml",
            "CRSANR5L17S2026O1N199",
            "2026-04-09",
            "jeudi 09 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n200_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N200.xml",
            "CRSANR5L17S2026O1N200",
            "2026-04-10",
            "vendredi 10 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n201_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N201.xml",
            "CRSANR5L17S2026O1N201",
            "2026-04-13",
            "lundi 13 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n202_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N202.xml",
            "CRSANR5L17S2026O1N202",
            "2026-04-13",
            "lundi 13 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n203_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N203.xml",
            "CRSANR5L17S2026O1N203",
            "2026-04-14",
            "mardi 14 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n204_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N204.xml",
            "CRSANR5L17S2026O1N204",
            "2026-04-14",
            "mardi 14 avril 2026",
            "hors_perimetre",
            "no_signal",
        )
        n205_payload = self._minimal_heatmap_payload(
            "CRSANR5L17S2026O1N205.xml",
            "CRSANR5L17S2026O1N205",
            "2026-04-15",
            "mercredi 15 avril 2026",
            "hors_perimetre",
            "no_signal",
        )

        overview = build_sessions_overview_payload(
            [
                n191_payload,
                n192_payload,
                n193_payload,
                n194_payload,
                n195_payload,
                n196_payload,
                n197_payload,
                n198_payload,
                n199_payload,
                n200_payload,
                n201_payload,
                n202_payload,
                n203_payload,
                n204_payload,
                n205_payload,
            ],
            detail_hrefs={
                "CRSANR5L17S2026O1N191.xml": "./assemblee_session_heatmap_n191.html",
                "CRSANR5L17S2026O1N192.xml": "./assemblee_session_heatmap_n192.html",
                "CRSANR5L17S2026O1N193.xml": "./assemblee_session_heatmap_n193.html",
                "CRSANR5L17S2026O1N194.xml": "./assemblee_session_heatmap_n194.html",
                "CRSANR5L17S2026O1N195.xml": "./assemblee_session_heatmap_n195.html",
                "CRSANR5L17S2026O1N196.xml": "./assemblee_session_heatmap_n196.html",
                "CRSANR5L17S2026O1N197.xml": "./assemblee_session_heatmap_n197.html",
                "CRSANR5L17S2026O1N198.xml": "./assemblee_session_heatmap_n198.html",
                "CRSANR5L17S2026O1N199.xml": "./assemblee_session_heatmap_n199.html",
                "CRSANR5L17S2026O1N200.xml": "./assemblee_session_heatmap_n200.html",
                "CRSANR5L17S2026O1N201.xml": "./assemblee_session_heatmap_n201.html",
                "CRSANR5L17S2026O1N202.xml": "./assemblee_session_heatmap_n202.html",
                "CRSANR5L17S2026O1N203.xml": "./assemblee_session_heatmap_n203.html",
                "CRSANR5L17S2026O1N204.xml": "./assemblee_session_heatmap_n204.html",
                "CRSANR5L17S2026O1N205.xml": "./assemblee_session_heatmap_n205.html",
            },
            generated_from=["test"],
        )

        self.assertEqual(
            [session["source_file"] for session in overview["sessions"]],
            [
                "CRSANR5L17S2026O1N191.xml",
                "CRSANR5L17S2026O1N192.xml",
                "CRSANR5L17S2026O1N193.xml",
                "CRSANR5L17S2026O1N194.xml",
                "CRSANR5L17S2026O1N195.xml",
                "CRSANR5L17S2026O1N196.xml",
                "CRSANR5L17S2026O1N197.xml",
                "CRSANR5L17S2026O1N198.xml",
                "CRSANR5L17S2026O1N199.xml",
                "CRSANR5L17S2026O1N200.xml",
                "CRSANR5L17S2026O1N201.xml",
                "CRSANR5L17S2026O1N202.xml",
                "CRSANR5L17S2026O1N203.xml",
                "CRSANR5L17S2026O1N204.xml",
                "CRSANR5L17S2026O1N205.xml",
            ],
        )
        self.assertEqual(overview["sessions"][0]["read_with_caution"], 1)
        self.assertEqual(overview["sessions"][1]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][3]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][4]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][5]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][6]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][7]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][8]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][9]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][10]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][11]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][12]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][13]["nothing_to_report"], 1)
        self.assertEqual(overview["sessions"][14]["nothing_to_report"], 1)
        self.assertEqual(
            {
                session["source_file"]: session["detail_view"]["href"]
                for session in overview["sessions"]
            },
            {
                "CRSANR5L17S2026O1N191.xml": "./assemblee_session_heatmap_n191.html",
                "CRSANR5L17S2026O1N192.xml": "./assemblee_session_heatmap_n192.html",
                "CRSANR5L17S2026O1N193.xml": "./assemblee_session_heatmap_n193.html",
                "CRSANR5L17S2026O1N194.xml": "./assemblee_session_heatmap_n194.html",
                "CRSANR5L17S2026O1N195.xml": "./assemblee_session_heatmap_n195.html",
                "CRSANR5L17S2026O1N196.xml": "./assemblee_session_heatmap_n196.html",
                "CRSANR5L17S2026O1N197.xml": "./assemblee_session_heatmap_n197.html",
                "CRSANR5L17S2026O1N198.xml": "./assemblee_session_heatmap_n198.html",
                "CRSANR5L17S2026O1N199.xml": "./assemblee_session_heatmap_n199.html",
                "CRSANR5L17S2026O1N200.xml": "./assemblee_session_heatmap_n200.html",
                "CRSANR5L17S2026O1N201.xml": "./assemblee_session_heatmap_n201.html",
                "CRSANR5L17S2026O1N202.xml": "./assemblee_session_heatmap_n202.html",
                "CRSANR5L17S2026O1N203.xml": "./assemblee_session_heatmap_n203.html",
                "CRSANR5L17S2026O1N204.xml": "./assemblee_session_heatmap_n204.html",
                "CRSANR5L17S2026O1N205.xml": "./assemblee_session_heatmap_n205.html",
            },
        )

    def test_overview_html_uses_sequential_heatmap_cells(self) -> None:
        html = Path("data/exports/d3/assemblee_sessions_overview.html").read_text(
            encoding="utf-8"
        )

        self.assertIn('data-layout="sequential-heatmap"', html)
        self.assertIn(".scaleBand()", html)
        self.assertIn("session.source_file", html)
        self.assertNotIn(".scalePoint()", html)
        self.assertNotIn(".scaleTime()", html)

    @staticmethod
    def _minimal_heatmap_payload(
        source_file: str,
        seance_id: str,
        seance_date: str,
        seance_date_label: str,
        scope_level: str,
        signal_category: str,
    ) -> dict[str, object]:
        return {
            "session": {
                "seance_id": seance_id,
                "source_file": source_file,
                "seance_date": seance_date,
                "seance_date_label": seance_date_label,
                "processed_at": "2026-04-17T00:00:00+02:00",
            },
            "metrics": {
                "reviewed_items": 1,
                "fallback_count": 0,
                "non_fallback_items": 1,
            },
            "items": [
                {
                    "scope_level": scope_level,
                    "signal_category": signal_category,
                    "is_fallback": False,
                }
            ],
            "non_fallback_items": [
                {
                    "scope_level": scope_level,
                    "signal_category": signal_category,
                    "is_fallback": False,
                }
            ],
        }


if __name__ == "__main__":
    unittest.main()
