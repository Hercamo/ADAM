"""Tier configuration invariants.

BOSS Formulas v3.2 §2.3 pins these rules:

* Exactly one dimension must be at Priority Tier "Top".
* The tier → weight mapping is fixed: 5, 4, 3, 2, 1, 0.5.
* The contribution percentage of a dimension is ``weight / total * 100``.
"""

from __future__ import annotations

import pytest

from boss_core.exceptions import TierConfigurationError
from boss_core.tiers import (
    ADAM_DEFAULT_TIERS,
    DIMENSION_ORDER,
    TIER_WEIGHTS,
    DimensionKey,
    Tier,
    TierConfig,
)


class TestTierWeightMapping:
    """Numeric weights are non-configurable and match the spec."""

    def test_top_is_five(self) -> None:
        assert TIER_WEIGHTS[Tier.TOP] == 5.0

    def test_very_high_is_four(self) -> None:
        assert TIER_WEIGHTS[Tier.VERY_HIGH] == 4.0

    def test_high_is_three(self) -> None:
        assert TIER_WEIGHTS[Tier.HIGH] == 3.0

    def test_medium_is_two(self) -> None:
        assert TIER_WEIGHTS[Tier.MEDIUM] == 2.0

    def test_low_is_one(self) -> None:
        assert TIER_WEIGHTS[Tier.LOW] == 1.0

    def test_very_low_is_half(self) -> None:
        assert TIER_WEIGHTS[Tier.VERY_LOW] == 0.5

    def test_six_tiers_exactly(self) -> None:
        assert len(TIER_WEIGHTS) == 6

    def test_weights_are_strictly_decreasing(self) -> None:
        tier_ordinal = [
            Tier.TOP,
            Tier.VERY_HIGH,
            Tier.HIGH,
            Tier.MEDIUM,
            Tier.LOW,
            Tier.VERY_LOW,
        ]
        weights = [TIER_WEIGHTS[t] for t in tier_ordinal]
        assert weights == sorted(weights, reverse=True)


class TestSingleTopRule:
    """Exactly one dimension may be Top."""

    def _assignments(self, overrides: dict[DimensionKey, Tier]) -> dict[DimensionKey, Tier]:
        base = dict.fromkeys(DIMENSION_ORDER, Tier.MEDIUM)
        base.update(overrides)
        return base

    def test_zero_top_rejected(self) -> None:
        with pytest.raises(TierConfigurationError):
            TierConfig(assignments=self._assignments({}))

    def test_two_tops_rejected(self) -> None:
        assignments = self._assignments(
            {
                DimensionKey.SECURITY: Tier.TOP,
                DimensionKey.REGULATORY: Tier.TOP,
            }
        )
        with pytest.raises(TierConfigurationError):
            TierConfig(assignments=assignments)

    def test_one_top_accepted(self) -> None:
        cfg = TierConfig(assignments=self._assignments({DimensionKey.SECURITY: Tier.TOP}))
        assert cfg.weight(DimensionKey.SECURITY) == 5.0


class TestCoverage:
    """Every BOSS dimension must be assigned a tier."""

    def test_missing_dimension_rejected(self) -> None:
        partial = {dim: Tier.MEDIUM for dim in DIMENSION_ORDER if dim is not DimensionKey.DOCTRINAL}
        partial[DimensionKey.SECURITY] = Tier.TOP
        with pytest.raises(TierConfigurationError):
            TierConfig(assignments=partial)


class TestAdamDefaults:
    """The shipped defaults line up with the ADAM v3.2 recommendation."""

    def test_security_is_top(self) -> None:
        assert ADAM_DEFAULT_TIERS.assignments[DimensionKey.SECURITY] is Tier.TOP

    def test_total_weight_is_stable(self) -> None:
        # TOP(5) + VH(4) + VH(4) + H(3) + H(3) + H(3) + M(2) = 24
        assert ADAM_DEFAULT_TIERS.total_weight() == 24.0

    def test_contribution_percentages_sum_to_100(self) -> None:
        total = sum(ADAM_DEFAULT_TIERS.contribution(dim) for dim in DIMENSION_ORDER)
        assert total == pytest.approx(100.0)

    def test_security_contribution_is_largest(self) -> None:
        contributions = {dim: ADAM_DEFAULT_TIERS.contribution(dim) for dim in DIMENSION_ORDER}
        assert contributions[DimensionKey.SECURITY] == max(contributions.values())

    def test_doctrinal_contribution_is_smallest(self) -> None:
        contributions = {dim: ADAM_DEFAULT_TIERS.contribution(dim) for dim in DIMENSION_ORDER}
        assert contributions[DimensionKey.DOCTRINAL] == min(contributions.values())
