"""Base scorer contract and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from boss_core.exceptions import DimensionScoreError
from boss_core.frameworks import DIMENSION_FRAMEWORKS
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey


class Scorer(ABC):
    """Abstract base class for a BOSS dimension scorer."""

    dimension: DimensionKey

    def framework_keys(self) -> tuple[str, ...]:
        """Framework attribution tuple for this dimension."""
        return DIMENSION_FRAMEWORKS[self.dimension]

    @abstractmethod
    def score(self, payload: dict[str, Any]) -> DimensionScore:
        """Return the dimension score for a raw input payload."""

    @staticmethod
    def _cap(value: float, hi: float, lo: float = 0.0) -> float:
        """Clip a value into an inclusive range [lo, hi]."""
        if value < lo:
            return lo
        if value > hi:
            return hi
        return value

    def _assemble(
        self,
        sub_components: list[SubComponentScore],
        *,
        evidence_refs: list[str] | None = None,
        notes: str | None = None,
    ) -> DimensionScore:
        total = sum(sc.value for sc in sub_components)
        # Each sub-component is bounded by its max; guard the sum too.
        raw = max(0.0, min(100.0, total))
        return DimensionScore(
            dimension=self.dimension,
            raw_score=round(raw, 4),
            sub_components=sub_components,
            frameworks=list(self.framework_keys()),
            evidence_refs=evidence_refs or [],
            notes=notes,
        )


_REGISTRY: dict[DimensionKey, Scorer] = {}


def register_scorer(scorer: Scorer) -> Scorer:
    """Register a scorer instance so the engine can look it up by dimension."""
    _REGISTRY[scorer.dimension] = scorer
    return scorer


def scorer_for(dimension: DimensionKey) -> Scorer:
    """Return the registered scorer for a dimension."""
    try:
        return _REGISTRY[dimension]
    except KeyError as exc:  # pragma: no cover - defensive
        raise DimensionScoreError(f"No scorer registered for dimension {dimension.value}") from exc


def registered_dimensions() -> tuple[DimensionKey, ...]:
    """Expose which dimensions currently have scorers installed."""
    return tuple(_REGISTRY.keys())


# Typing alias used by callers that want to build ad-hoc pipelines.
ScorerFactory = Callable[[], Scorer]
