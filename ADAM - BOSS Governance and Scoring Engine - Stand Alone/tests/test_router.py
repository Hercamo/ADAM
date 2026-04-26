"""SOAP → OHSHAT escalation router boundary tests.

Boundary table (BOSS Formulas v3.2 Table 3):
    [ 0, 10]  SOAP      SLA 0    min
    (10, 30]  MODERATE  SLA 0    min
    (30, 50]  ELEVATED  SLA 60   min
    (50, 75]  HIGH      SLA 240  min
    (75, 100] OHSHAT    SLA 15   min

The bounds are closed on the upper side so a score landing exactly on a
threshold is always assigned the lower tier.
"""

from __future__ import annotations

import itertools

import pytest

from boss_core.router import TIERS, route, window_for
from boss_core.schemas import EscalationTier


@pytest.mark.parametrize(
    "score, expected",
    [
        (0.0, EscalationTier.SOAP),
        (5.0, EscalationTier.SOAP),
        (10.0, EscalationTier.SOAP),
        (10.01, EscalationTier.MODERATE),
        (20.0, EscalationTier.MODERATE),
        (30.0, EscalationTier.MODERATE),
        (30.01, EscalationTier.ELEVATED),
        (40.0, EscalationTier.ELEVATED),
        (50.0, EscalationTier.ELEVATED),
        (50.01, EscalationTier.HIGH),
        (60.0, EscalationTier.HIGH),
        (75.0, EscalationTier.HIGH),
        (75.01, EscalationTier.OHSHAT),
        (80.0, EscalationTier.OHSHAT),
        (99.99, EscalationTier.OHSHAT),
        (100.0, EscalationTier.OHSHAT),
    ],
)
def test_route_boundaries(score: float, expected: EscalationTier) -> None:
    assert route(score) is expected


class TestTierWindows:
    """SLA expectations per tier — these are load-bearing for the UI."""

    def test_soap_sla_is_zero(self) -> None:
        assert window_for(EscalationTier.SOAP).sla_minutes == 0

    def test_moderate_sla_is_zero(self) -> None:
        assert window_for(EscalationTier.MODERATE).sla_minutes == 0

    def test_elevated_sla_is_sixty(self) -> None:
        assert window_for(EscalationTier.ELEVATED).sla_minutes == 60

    def test_high_sla_is_four_hours(self) -> None:
        assert window_for(EscalationTier.HIGH).sla_minutes == 240

    def test_ohshat_sla_is_fifteen(self) -> None:
        # OHSHAT is 15 min because humans must be in-loop immediately.
        assert window_for(EscalationTier.OHSHAT).sla_minutes == 15

    def test_all_five_tiers_declared(self) -> None:
        tiers = {t for t, _ in TIERS}
        assert tiers == set(EscalationTier)

    def test_windows_partition_zero_to_hundred(self) -> None:
        # The tier windows, concatenated, must cover [0, 100] contiguously.
        windows = [w for _, w in TIERS]
        assert windows[0].lower == 0.0
        assert windows[-1].upper == 100.0
        for earlier, later in itertools.pairwise(windows):
            assert earlier.upper == later.lower
