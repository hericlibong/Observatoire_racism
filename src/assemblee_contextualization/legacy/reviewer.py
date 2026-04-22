from __future__ import annotations

# DEPRECATED — V1, kept for historical reference only.
# V2 is the active contract (contracts.py ScopeLevel/SignalCategory).
# Do not modify or extend this file.

from typing import Any, Mapping

from ..context_builder import build_context_payload, candidate_ids
from ..contracts import ContextualReviewOutput, validate_review_output
from ..providers import ContextualReviewProvider


class ContextualReviewer:
    def __init__(
        self,
        provider: ContextualReviewProvider,
        *,
        source_file: str,
        window: int = 2,
    ) -> None:
        self.provider = provider
        self.source_file = source_file
        self.window = window

    def review_candidate(
        self,
        interventions: list[Mapping[str, Any]],
        candidate_id: str,
    ) -> ContextualReviewOutput:
        context = build_context_payload(
            interventions,
            candidate_id,
            source_file=self.source_file,
            window=self.window,
        )
        raw_output = self.provider.review(context.to_dict())
        output = validate_review_output(raw_output)
        if output.candidate_id != candidate_id:
            raise ValueError("La sortie provider ne correspond pas au candidat demande.")
        return output

    def review_candidates(self, interventions: list[Mapping[str, Any]]) -> list[ContextualReviewOutput]:
        return [self.review_candidate(interventions, candidate_id) for candidate_id in candidate_ids(interventions)]
