"""Contextual review providers for the V2 contract.

This package exposes the :class:`ContextualReviewProvider` abstract base
class and the concrete implementations used by the pipeline (mock and
Mistral). Keeping the ABC at package level preserves the historical
``from assemblee_contextualization.providers import ContextualReviewProvider``
import path while grouping implementations in their own modules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ContextualReviewProvider(ABC):
    @abstractmethod
    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
