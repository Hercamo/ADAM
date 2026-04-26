"""Hypothesis property tests for the BOSS scoring invariants.

Properties verified:

1. Composite is always within ``[0, 100]`` regardless of inputs.
2. Composite of a uniform score ``x`` equals ``x`` before modifiers
   (this is the weighted-mean identity).
3. Adding the non-idempotent flag never decreases the composite.
4. The escalation tier is monotone in the composite.
5. ``TierConfig`` total weight equals the sum of the per-dimension
   weights (a tautology that guards regressions in ``TIER_WEIGHTS``).
"""

from __future__ import annotations

import hypothesis.strategies as st
from hypothesis import given, settings

from boss_core.composite import compute_composite
from boss_core.router import route
from boss_core.schemas import DimensionScore, EscalationTier
from boss_core.tiers import ADAM_DEFAULT_TIERS, DIMENSION_ORDER, DimensionKey

scores_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


def _build_scores(
    values: dict[DimensionKey, float],
) -> dict[DimensionKey, DimensionScore]:
    return {dim: DimensionScore(dimension=dim, raw_score=values[dim]) for dim in DIMENSION_ORDER}


@given(
    security=scores_strategy,
    sovereignty=scores_strategy,
    financial=scores_strategy,
    regulatory=scores_strategy,
    reputational=scores_strategy,
    rights=scores_strategy,
    doctrinal=scores_strategy,
    non_idempotent=st.booleans(),
)
@settings(max_examples=200, deadline=None)
def test_composite_bounds(
    security: float,
    sovereignty: float,
    financial: float,
    regulatory: float,
    reputational: float,
    rights: float,
    doctrinal: float,
    non_idempotent: bool,
) -> None:
    scores = _build_scores(
        {
            DimensionKey.SECURITY: security,
            DimensionKey.SOVEREIGNTY: sovereignty,
            DimensionKey.FINANCIAL: financial,
            DimensionKey.REGULATORY: regulatory,
            DimensionKey.REPUTATIONAL: reputational,
            DimensionKey.RIGHTS: rights,
            DimensionKey.DOCTRINAL: doctrinal,
        }
    )
    _, raw, final, _ = compute_composite(
        scores, ADAM_DEFAULT_TIERS, is_non_idempotent=non_idempotent
    )
    assert 0.0 <= raw <= 100.0
    assert 0.0 <= final <= 100.0


@given(x=scores_strategy)
@settings(max_examples=100, deadline=None)
def test_uniform_composite_equals_itself(x: float) -> None:
    scores = _build_scores(dict.fromkeys(DIMENSION_ORDER, x))
    _, raw, _, _ = compute_composite(scores, ADAM_DEFAULT_TIERS, is_non_idempotent=False)
    # Weighted mean of identical values must equal the value.
    # compute_composite rounds to 4 decimal places for display stability,
    # so tolerate 1e-4 (half the rounding step is 5e-5 plus fp error).
    assert abs(raw - x) < 1e-4


@given(
    vals=st.dictionaries(
        keys=st.sampled_from(list(DIMENSION_ORDER)),
        values=scores_strategy,
        min_size=7,
        max_size=7,
    )
)
@settings(max_examples=100, deadline=None)
def test_non_idempotent_never_lowers_composite(
    vals: dict[DimensionKey, float],
) -> None:
    scores = _build_scores(vals)
    _, _, without, _ = compute_composite(scores, ADAM_DEFAULT_TIERS, is_non_idempotent=False)
    _, _, with_penalty, _ = compute_composite(scores, ADAM_DEFAULT_TIERS, is_non_idempotent=True)
    assert with_penalty >= without - 1e-9


@given(x=scores_strategy, y=scores_strategy)
@settings(max_examples=100, deadline=None)
def test_route_monotone(x: float, y: float) -> None:
    x, y = min(x, y), max(x, y)
    tier_order = [
        EscalationTier.SOAP,
        EscalationTier.MODERATE,
        EscalationTier.ELEVATED,
        EscalationTier.HIGH,
        EscalationTier.OHSHAT,
    ]
    assert tier_order.index(route(x)) <= tier_order.index(route(y))


def test_tier_weight_total_matches_sum() -> None:
    from boss_core.tiers import TIER_WEIGHTS

    manual = sum(TIER_WEIGHTS[ADAM_DEFAULT_TIERS.assignments[d]] for d in DIMENSION_ORDER)
    assert manual == ADAM_DEFAULT_TIERS.total_weight()
