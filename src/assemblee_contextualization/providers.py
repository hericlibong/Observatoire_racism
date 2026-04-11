from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ContextualReviewProvider(ABC):
    @abstractmethod
    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

