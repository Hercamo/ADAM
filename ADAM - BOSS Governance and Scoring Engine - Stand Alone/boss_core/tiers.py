"""Priority Tier weighting system from BOSS Score Formulas v3.2.

The BOSS specification replaces arbitrary numeric weights with a
human-readable tier scale that any director, auditor, or regulator can
interpret at a glance. The mapping from tier to weight is fixed and
deterministic:

    Top       -> 5.0   (only one dimension permitted)
    Very High -> 4.0
    High      -> 3.0
    Medium    -> 2.0
    Low       -> 1.0
    Very Low  -> 0.5

Contribution percentage for any dimension is:

    contribution = (dimension_weight / sum_of_all_weights) * 100

Because the tier-to-weight mapping uses fixed values, all dimensions at
the same tier automatically carry identical influence. This eliminates
the hidden decimal differences that existed in earlier BOSS versions.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from boss_core.exceptions import TierConfigurationError


class Tier(str, Enum):  # noqa: UP042 - str+Enum kept for py310 compat in dev sandboxes
    """Priority tier ordinal. String values keep JSON payloads human-readable."""

    TOP = "Top"
    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"


TIER_WEIGHTS: Mapping[Tier, float] = {
    Tier.TOP: 5.0,
    Tier.VERY_HIGH: 4.0,
    Tier.HIGH: 3.0,
    Tier.MEDIUM: 2.0,
    Tier.LOW: 1.0,
    Tier.VERY_LOW: 0.5,
}


class DimensionKey(str, Enum):  # noqa: UP042 - py310 dev-sandbox compat
    """Canonical identifiers for the seven BOSS dimensions."""

    SECURITY = "security"
    SOVEREIGNTY = "sovereignty"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    REPUTATIONAL = "reputational"
    RIGHTS = "rights"
    DOCTRINAL = "doctrinal"


DIMENSION_ORDER: tuple[DimensionKey, ...] = (
    DimensionKey.SECURITY,
    DimensionKey.SOVEREIGNTY,
    DimensionKey.FINANCIAL,
    DimensionKey.REGULATORY,
    DimensionKey.REPUTATIONAL,
    DimensionKey.RIGHTS,
    DimensionKey.DOCTRINAL,
)


class TierAssignment(BaseModel):
    """Priority tier assignment for a single dimension."""

    dimension: DimensionKey
    tier: Tier

    @property
    def weight(self) -> float:
        """Numeric weight derived from the tier."""
        return TIER_WEIGHTS[self.tier]


class TierConfig(BaseModel):
    """Full tier configuration covering every BOSS dimension.

    The configuration is the director-approved input that drives the
    composite formula. Exactly one dimension must be designated Top.
    """

    assignments: dict[DimensionKey, Tier] = Field(
        ..., description="Priority tier per BOSS dimension."
    )

    @field_validator("assignments")
    @classmethod
    def _require_full_coverage(cls, value: dict[DimensionKey, Tier]) -> dict[DimensionKey, Tier]:
        missing = [d for d in DIMENSION_ORDER if d not in value]
        if missing:
            raise TierConfigurationError(
                "Tier configuration is missing dimensions: " + ", ".join(m.value for m in missing)
            )
        return value

    @model_validator(mode="after")
    def _enforce_single_top(self) -> TierConfig:
        top_count = sum(1 for t in self.assignments.values() if t is Tier.TOP)
        if top_count == 0:
            raise TierConfigurationError(
                "BOSS requires exactly one dimension at Priority Tier 'Top'."
            )
        if top_count > 1:
            raise TierConfigurationError(
                "Only one dimension may be assigned 'Top' — if everything is "
                "the highest priority, nothing is."
            )
        return self

    def weight(self, dimension: DimensionKey) -> float:
        """Return the numeric weight for a dimension."""
        return TIER_WEIGHTS[self.assignments[dimension]]

    def total_weight(self) -> float:
        """Sum of weights across all dimensions (denominator for composite)."""
        return sum(TIER_WEIGHTS[t] for t in self.assignments.values())

    def contribution(self, dimension: DimensionKey) -> float:
        """Return the percentage contribution of a dimension to the composite."""
        total = self.total_weight()
        if total == 0:
            return 0.0
        return (self.weight(dimension) / total) * 100.0


# ---------------------------------------------------------------------------
# ADAM default configuration (v3.2)
# ---------------------------------------------------------------------------

ADAM_DEFAULT_TIERS: TierConfig = TierConfig(
    assignments={
        DimensionKey.SECURITY: Tier.TOP,
        DimensionKey.SOVEREIGNTY: Tier.VERY_HIGH,
        DimensionKey.FINANCIAL: Tier.VERY_HIGH,
        DimensionKey.REGULATORY: Tier.HIGH,
        DimensionKey.REPUTATIONAL: Tier.HIGH,
        DimensionKey.RIGHTS: Tier.HIGH,
        DimensionKey.DOCTRINAL: Tier.MEDIUM,
    }
)
"""ADAM's recommended defaults per BOSS Formulas v3.2, Section 2.3."""
