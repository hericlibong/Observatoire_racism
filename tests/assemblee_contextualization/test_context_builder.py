import unittest

from src.assemblee_contextualization.context_builder import (
    build_context_payload,
    candidate_ids,
)


def sample_interventions() -> list[dict[str, object]]:
    return [
        _row(1, "i1", "Intro", "", False, "", "", 0),
        _row(2, "i2", "Debat", "Sous-point A", False, "", "", 0),
        _row(3, "i3", "Debat", "Sous-point A", True, "devalorisation", "irresponsable", 2),
        _row(4, "i4", "Debat", "Sous-point A", False, "", "", 0),
        _row(5, "i5", "Debat", "Sous-point B", True, "designation_groupe", "flnks", 1),
    ]


def _row(
    ordre: int,
    intervention_id: str,
    point_titre: str,
    sous_point_titre: str,
    signal_candidate: bool,
    signal_family: str,
    signal_trigger: str,
    signal_intensity: int,
) -> dict[str, object]:
    return {
        "intervention_id": intervention_id,
        "seance_id": "s1",
        "ordre": ordre,
        "point_titre": point_titre,
        "sous_point_titre": sous_point_titre,
        "orateur_nom": f"Orateur {ordre}",
        "texte": f"Texte {ordre}",
        "signal_candidate": signal_candidate,
        "signal_family": signal_family,
        "signal_trigger": signal_trigger,
        "signal_intensity": signal_intensity,
    }


class ContextBuilderTest(unittest.TestCase):
    def test_candidate_ids_are_derived_from_enriched_interventions(self) -> None:
        self.assertEqual(candidate_ids(sample_interventions()), ["i3", "i5"])

    def test_builds_context_payload_with_local_neighbors(self) -> None:
        payload = build_context_payload(
            sample_interventions(),
            "i3",
            source_file="pilot.xml",
            window=1,
        )

        self.assertEqual(payload.candidate_id, "i3")
        self.assertEqual(payload.source.source_file, "pilot.xml")
        self.assertEqual(payload.target.sous_point_titre, "Sous-point A")
        self.assertEqual(payload.rule_based_signal.signal_family, "devalorisation")
        self.assertEqual([item.intervention_id for item in payload.local_context.previous], ["i2"])
        self.assertEqual([item.intervention_id for item in payload.local_context.next], ["i4"])

    def test_rejects_non_candidate_target(self) -> None:
        with self.assertRaises(ValueError):
            build_context_payload(sample_interventions(), "i2", source_file="pilot.xml")


if __name__ == "__main__":
    unittest.main()

