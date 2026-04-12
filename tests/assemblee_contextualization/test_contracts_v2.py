import unittest

from src.assemblee_contextualization.contracts import (
    Confidence,
    ScopeLevel,
    SignalCategory,
    validate_review_output_v2,
    validate_v2_combination,
)


VALID_NORMAL_COMBINATIONS = {
    ("core", "problematic_group_targeting"),
    ("core", "stereotype_essentialization"),
    ("core", "devaluation_dehumanization"),
    ("core", "exclusion_discrimination"),
    ("core", "hostility_threat"),
    ("adjacent", "problematic_group_targeting"),
    ("adjacent", "stereotype_essentialization"),
    ("adjacent", "devaluation_dehumanization"),
    ("adjacent", "exclusion_discrimination"),
    ("adjacent", "hostility_threat"),
    ("adjacent", "ambiguous"),
    ("hors_perimetre", "no_signal"),
}


def v2_payload(**overrides: object) -> dict:
    payload = {
        "candidate_id": "c1",
        "scope_level": "core",
        "signal_category": "problematic_group_targeting",
        "is_fallback": False,
        "needs_human_review": True,
        "confidence": "medium",
        "rationale": "Ancrage explicite dans le perimetre.",
        "evidence_span": "extrait",
        "limits": ["Analyse limitee au contexte local."],
        "model_provider": "test",
        "model_name": "contract-v2",
    }
    payload.update(overrides)
    return payload


class ContractsV2Test(unittest.TestCase):
    def test_scope_level_enum_values_are_locked(self) -> None:
        self.assertEqual(
            {item.value for item in ScopeLevel},
            {"core", "adjacent", "hors_perimetre"},
        )

    def test_signal_category_enum_values_are_locked(self) -> None:
        self.assertEqual(
            {item.value for item in SignalCategory},
            {
                "problematic_group_targeting",
                "stereotype_essentialization",
                "devaluation_dehumanization",
                "exclusion_discrimination",
                "hostility_threat",
                "ambiguous",
                "no_signal",
            },
        )

    def test_v2_combination_matrix_is_exhaustive(self) -> None:
        for scope_level in ScopeLevel:
            for signal_category in SignalCategory:
                combination = (scope_level.value, signal_category.value)
                with self.subTest(combination=combination):
                    if combination in VALID_NORMAL_COMBINATIONS:
                        self.assertEqual(
                            validate_v2_combination(scope_level.value, signal_category.value),
                            (scope_level, signal_category),
                        )
                    else:
                        with self.assertRaises(ValueError):
                            validate_v2_combination(scope_level.value, signal_category.value)

    def test_v2_fallback_combination_is_explicit(self) -> None:
        self.assertEqual(
            validate_v2_combination(
                "hors_perimetre",
                "ambiguous",
                is_fallback=True,
            ),
            (ScopeLevel.HORS_PERIMETRE, SignalCategory.AMBIGUOUS),
        )

    def test_accepts_core_canonical_signal(self) -> None:
        output = validate_review_output_v2(
            v2_payload(
                scope_level="core",
                signal_category="devaluation_dehumanization",
                needs_human_review=True,
                confidence="medium",
            )
        )

        self.assertEqual(output.scope_level, ScopeLevel.CORE)
        self.assertEqual(output.signal_category, SignalCategory.DEVALUATION_DEHUMANIZATION)
        self.assertFalse(output.is_fallback)
        self.assertTrue(output.needs_human_review)

    def test_accepts_adjacent_ambiguous_boundary_case(self) -> None:
        output = validate_review_output_v2(
            v2_payload(
                scope_level="adjacent",
                signal_category="ambiguous",
                needs_human_review=True,
                confidence="low",
                rationale="Ancrage possible, mais cible implicite.",
            )
        )

        self.assertEqual(output.scope_level, ScopeLevel.ADJACENT)
        self.assertEqual(output.signal_category, SignalCategory.AMBIGUOUS)
        self.assertFalse(output.is_fallback)
        self.assertTrue(output.needs_human_review)

    def test_accepts_clear_hors_perimetre_without_human_review(self) -> None:
        output = validate_review_output_v2(
            v2_payload(
                scope_level="hors_perimetre",
                signal_category="no_signal",
                needs_human_review=False,
                confidence="high",
                rationale="Critique institutionnelle sans groupe du perimetre.",
            )
        )

        self.assertEqual(output.scope_level, ScopeLevel.HORS_PERIMETRE)
        self.assertEqual(output.signal_category, SignalCategory.NO_SIGNAL)
        self.assertFalse(output.is_fallback)
        self.assertFalse(output.needs_human_review)
        self.assertEqual(output.confidence, Confidence.HIGH)

    def test_accepts_v2_fallback_shape(self) -> None:
        output = validate_review_output_v2(
            v2_payload(
                scope_level="hors_perimetre",
                signal_category="ambiguous",
                is_fallback=True,
                needs_human_review=True,
                confidence="low",
                rationale="Fallback technique : sortie provider non conforme.",
            )
        )

        self.assertEqual(output.scope_level, ScopeLevel.HORS_PERIMETRE)
        self.assertEqual(output.signal_category, SignalCategory.AMBIGUOUS)
        self.assertTrue(output.is_fallback)
        self.assertTrue(output.needs_human_review)

    def test_rejects_hors_perimetre_ambiguous_without_fallback(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output_v2(
                v2_payload(
                    scope_level="hors_perimetre",
                    signal_category="ambiguous",
                    is_fallback=False,
                    needs_human_review=True,
                    confidence="low",
                )
            )

    def test_rejects_fallback_outside_technical_combination(self) -> None:
        invalid_cases = [
            ("core", "problematic_group_targeting"),
            ("adjacent", "ambiguous"),
            ("hors_perimetre", "no_signal"),
        ]
        for scope_level, signal_category in invalid_cases:
            with self.subTest(scope_level=scope_level, signal_category=signal_category):
                with self.assertRaises(ValueError):
                    validate_review_output_v2(
                        v2_payload(
                            scope_level=scope_level,
                            signal_category=signal_category,
                            is_fallback=True,
                            needs_human_review=True,
                            confidence="low",
                        )
                    )

    def test_rejects_fallback_without_low_confidence(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output_v2(
                v2_payload(
                    scope_level="hors_perimetre",
                    signal_category="ambiguous",
                    is_fallback=True,
                    needs_human_review=True,
                    confidence="medium",
                )
            )

    def test_rejects_fallback_without_human_review(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output_v2(
                v2_payload(
                    scope_level="hors_perimetre",
                    signal_category="ambiguous",
                    is_fallback=True,
                    needs_human_review=False,
                    confidence="low",
                )
            )

    def test_rejects_no_signal_outside_hors_perimetre(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output_v2(
                v2_payload(
                    scope_level="adjacent",
                    signal_category="no_signal",
                    needs_human_review=True,
                )
            )

    def test_rejects_substantive_signal_with_hors_perimetre(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output_v2(
                v2_payload(
                    scope_level="hors_perimetre",
                    signal_category="hostility_threat",
                    needs_human_review=True,
                )
            )

    def test_rejects_human_review_false_for_adjacent(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output_v2(
                v2_payload(
                    scope_level="adjacent",
                    signal_category="ambiguous",
                    needs_human_review=False,
                    confidence="high",
                )
            )

    def test_rejects_human_review_false_without_high_confidence(self) -> None:
        with self.assertRaises(ValueError):
            validate_review_output_v2(
                v2_payload(
                    scope_level="hors_perimetre",
                    signal_category="no_signal",
                    needs_human_review=False,
                    confidence="medium",
                )
            )


if __name__ == "__main__":
    unittest.main()
