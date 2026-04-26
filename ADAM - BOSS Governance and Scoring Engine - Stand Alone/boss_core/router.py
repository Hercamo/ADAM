"""SOAP-to-OHSHAT escalation router.

The composite BOSS score is mapped to one of five escalation tiers and
the per-tier response SLA is derived from the ADAM Exception Economy.
"""

from __future__ import annotations

from dataclasses import dataclass

from boss_core.schemas import EscalationTier


@dataclass(frozen=True)
class TierWindow:
    """Upper and lower composite bounds for a tier."""

    lower: float
    upper: float
    sla_minutes: int
    description: str


TIERS: tuple[tuple[EscalationTier, TierWindow], ...] = (
    (
        EscalationTier.SOAP,
        TierWindow(
            lower=0.0,
            upper=10.0,
            sla_minutes=0,
            description="Safe & Optimum Autonomous Performance. Execute.",
        ),
    ),
    (
        EscalationTier.MODERATE,
        TierWindow(
            lower=10.0,
            upper=30.0,
            sla_minutes=0,
            description="Constrained execution with enhanced logging.",
        ),
    ),
    (
        EscalationTier.ELEVATED,
        TierWindow(
            lower=30.0,
            upper=50.0,
            sla_minutes=60,
            description="Exception likely; Domain Governor review.",
        ),
    ),
    (
        EscalationTier.HIGH,
        TierWindow(
            lower=50.0,
            upper=75.0,
            sla_minutes=240,
            description="Director approval required within 4 hours.",
        ),
    ),
    (
        EscalationTier.OHSHAT,
        TierWindow(
            lower=75.0,
            upper=100.0,
            sla_minutes=15,
            description=(
                "Operational Hell, Send Humans Act Today — CEO + all directors; safe-mode engaged."
            ),
        ),
    ),
)


def route(composite: float) -> EscalationTier:
    """Route a composite score to a tier.

    Thresholds mirror the ADAM Exception Economy table:
      0 - 10  -> SOAP
     11 - 30  -> MODERATE
     31 - 50  -> ELEVATED
     51 - 75  -> HIGH
     76 - 100 -> OHSHAT
    """
    if composite <= 10.0:
        return EscalationTier.SOAP
    if composite <= 30.0:
        return EscalationTier.MODERATE
    if composite <= 50.0:
        return EscalationTier.ELEVATED
    if composite <= 75.0:
        return EscalationTier.HIGH
    return EscalationTier.OHSHAT


def window_for(tier: EscalationTier) -> TierWindow:
    """Return the tier window metadata for documentation or UI."""
    for candidate, window in TIERS:
        if candidate is tier:
            return window
    raise KeyError(tier)  # pragma: no cover - defensive
