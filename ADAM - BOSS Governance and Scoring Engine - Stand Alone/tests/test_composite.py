"""Composite BOSS score formula invariants.

These tests exercise ``compute_composite`` in isolation so they do not
depend on the dimension scorers. We synthesise ``DimensionScore``
objects directly and assert on:

* weighted sum = Σ S_d * W_d
* composite_raw = weighted_sum / Σ W_d
* Critical Dimension Override (any dim > 75 -> floor at max - 10)
* Non-Idempotent Penalty (+15)
* Cap at 100
"""

from __future__ import annotations

import pytest

from boss_core.composite import (
    COMPOSITE_CAP,
    CRITICAL_OVERRIDE_REDUCTION,
    CRITICAL_OVERRIDE_THRESHOLD,
    NON_IDEMPOTENT_PENALTY,
    compute_composite,
)
from boss_core.schemas import DimensionScore
from boss_core.tiers import (
    ADAM_DEFAULT_TIERS,
    DIMENSION_ORDER,
    DimensionKey,
)


def _scores(uniform: float) -> dict[DimensionKey, DimensionScore]:
    """Return a dict of dimension scores all set to the same value."""
    return {dim: DimensionScore(dimension=dim, raw_score=uniform) for dim in DIMENSION_ORDER}


def _heterogeneous(values: dict[DimensionKey, float]) -> dict[DimensionKey, DimensionScore]:
    return {
        dim: DimensionScore(dimension=dim, raw_score=values.get(dim, 0.0))
        for dim in DIMENSION_ORDER
    }


class TestWeightedSum:
    """Composite is the weighted average of the seven dimensions."""

    def test_all_zero_yields_zero(self) -> None:
        weighted, raw, final, mods = compute_composite(
            _scores(0.0), ADAM_DEFAULT_TIERS, is_non_idempotent=False
        )
        assert weighted == 0.0
        assert raw == 0.0
        assert final == 0.0
        assert mods == []

    def test_uniform_score_equals_itself(self) -> None:
        # If every dimension equals x, the weighted average must equal x.
        weighted, raw, final, mods = compute_composite(
            _scores(20.0), ADAM_DEFAULT_TIERS, is_non_idempotent=False
        )
        assert raw == pytest.approx(20.0)
        assert final == pytest.approx(20.0)
        assert weighted == pytest.approx(20.0 * ADAM_DEFAULT_TIERS.total_weight())
        assert mods == []

    def test_security_weighting_drives_composite(self) -> None:
        # Security is TOP (weight 5/24); sending security=100 and others=0
        # should yield a composite of (5 / 24) * 100 ≈ 20.833.
        values = {DimensionKey.SECURITY: 100.0}
        _, raw, _, _ = compute_composite(
            _heterogeneous(values), ADAM_DEFAULT_TIERS, is_non_idempotent=False
        )
        assert raw == pytest.approx((5.0 / 24.0) * 100.0, abs=1e-3)


class TestCriticalOverride:
    """Any dimension > 75 drags the composite up to max - 10."""

    def test_override_triggers_when_dimension_above_threshold(self) -> None:
        # One dimension at 90 — composite would otherwise be small.
        values = {DimensionKey.REGULATORY: 90.0}
        _, raw, final, mods = compute_composite(
            _heterogeneous(values), ADAM_DEFAULT_TIERS, is_non_idempotent=False
        )
        # Raw score is driven only by regulatory (weight 3 of 24): ~11.25
        assert raw < 20.0
        # But override floors it at 90 - 10 = 80.
        assert final == pytest.approx(90.0 - CRITICAL_OVERRIDE_REDUCTION)
        names = [m.name for m in mods]
        assert "critical_dimension_override" in names

    def test_override_noop_when_raw_already_exceeds_floor(self) -> None:
        # If composite would naturally exceed the override floor, no bump.
        values = dict.fromkeys(DIMENSION_ORDER, 80.0)
        _, raw, final, mods = compute_composite(
            _heterogeneous(values), ADAM_DEFAULT_TIERS, is_non_idempotent=False
        )
        # Raw ≈ 80, override floor = 70 — so override must not apply.
        assert raw == pytest.approx(80.0)
        assert final == pytest.approx(80.0)
        assert all(m.name != "critical_dimension_override" for m in mods)

    def test_override_boundary_not_triggered_at_exactly_75(self) -> None:
        values = {DimensionKey.SECURITY: CRITICAL_OVERRIDE_THRESHOLD}
        _, _, final, mods = compute_composite(
            _heterogeneous(values), ADAM_DEFAULT_TIERS, is_non_idempotent=False
        )
        # Threshold is strictly greater than; 75 should NOT override.
        assert all(m.name != "critical_dimension_override" for m in mods)
        # Raw ≈ (5/24)*75 ≈ 15.625
        assert final < 20.0


class TestNonIdempotentPenalty:
    """Non-idempotent actions get +15 to force at least one escalation tier."""

    def test_penalty_added(self) -> None:
        _, raw, final, mods = compute_composite(
            _scores(20.0), ADAM_DEFAULT_TIERS, is_non_idempotent=True
        )
        assert raw == pytest.approx(20.0)
        assert final == pytest.approx(20.0 + NON_IDEMPOTENT_PENALTY)
        assert any(m.name == "non_idempotent_penalty" for m in mods)

    def test_penalty_respects_cap(self) -> None:
        _, _, final, mods = compute_composite(
            _scores(95.0), ADAM_DEFAULT_TIERS, is_non_idempotent=True
        )
        # 95 + 15 = 110, capped to 100.
        assert final == COMPOSITE_CAP
        names = [m.name for m in mods]
        assert "non_idempotent_penalty" in names
        assert "cap_100" in names


class TestCap:
    """The composite must never exceed 100."""

    def test_cap_triggers_when_sum_exceeds_100(self) -> None:
        # Force a runaway: max 100 + non-idempotent penalty.
        _, _, final, mods = compute_composite(
            _scores(100.0), ADAM_DEFAULT_TIERS, is_non_idempotent=True
        )
        assert final == COMPOSITE_CAP
        assert any(m.name == "cap_100" for m in mods)

    def test_no_cap_when_inside_bounds(self) -> None:
        _, _, final, mods = compute_composite(
            _scores(50.0), ADAM_DEFAULT_TIERS, is_non_idempotent=False
        )
        assert final == pytest.approx(50.0)
        assert all(m.name != "cap_100" for m in mods)
