"""Composite BOSS scoring per v3.2.

Formula::

    C = Σ (S_d * W_d) / Σ W_d

where S_d is the 0-100 dimension risk score and W_d is the numeric
weight derived from the dimension's Priority Tier assignment.

Modifiers:

* Critical Dimension Override — if any dimension > 75, composite
  becomes at least (max dimension - 10).
* Non-Idempotent Penalty — +15 if the intent is irreversible.
* The composite is capped at 100.
"""

from __future__ import annotations

from boss_core.dimensions.base import scorer_for
from boss_core.router import route
from boss_core.schemas import (
    BOSSResult,
    CompositeModifier,
    DimensionScore,
    IntentObject,
)
from boss_core.tiers import DIMENSION_ORDER, DimensionKey, TierConfig

CRITICAL_OVERRIDE_THRESHOLD = 75.0
CRITICAL_OVERRIDE_REDUCTION = 10.0
NON_IDEMPOTENT_PENALTY = 15.0
COMPOSITE_CAP = 100.0


def score_dimensions(
    intent: IntentObject,
) -> dict[DimensionKey, DimensionScore]:
    """Run every registered dimension scorer against an intent."""
    bundle = intent.dimension_inputs
    payload_map = {
        DimensionKey.SECURITY: bundle.security,
        DimensionKey.SOVEREIGNTY: bundle.sovereignty,
        DimensionKey.FINANCIAL: bundle.financial,
        DimensionKey.REGULATORY: bundle.regulatory,
        DimensionKey.REPUTATIONAL: bundle.reputational,
        DimensionKey.RIGHTS: bundle.rights,
        DimensionKey.DOCTRINAL: bundle.doctrinal,
    }
    return {dim: scorer_for(dim).score(payload_map[dim]) for dim in DIMENSION_ORDER}


def compute_composite(
    dimension_scores: dict[DimensionKey, DimensionScore],
    tier_config: TierConfig,
    is_non_idempotent: bool,
) -> tuple[float, float, float, list[CompositeModifier]]:
    """Return (weighted_sum, composite_raw, composite_final, modifiers)."""
    weighted_sum = 0.0
    total_weight = tier_config.total_weight()
    for dim in DIMENSION_ORDER:
        weighted_sum += dimension_scores[dim].raw_score * tier_config.weight(dim)

    composite_raw = weighted_sum / total_weight if total_weight else 0.0
    composite = composite_raw
    modifiers: list[CompositeModifier] = []

    max_dimension = max(dimension_scores.values(), key=lambda ds: ds.raw_score)
    if max_dimension.raw_score > CRITICAL_OVERRIDE_THRESHOLD:
        override_floor = max_dimension.raw_score - CRITICAL_OVERRIDE_REDUCTION
        if composite < override_floor:
            modifiers.append(
                CompositeModifier(
                    name="critical_dimension_override",
                    delta=round(override_floor - composite, 4),
                    explanation=(
                        f"Dimension '{max_dimension.dimension.value}' scored "
                        f"{max_dimension.raw_score:.2f} (> "
                        f"{CRITICAL_OVERRIDE_THRESHOLD:.0f}); "
                        f"composite raised to max - "
                        f"{CRITICAL_OVERRIDE_REDUCTION:.0f}."
                    ),
                )
            )
            composite = override_floor

    if is_non_idempotent:
        modifiers.append(
            CompositeModifier(
                name="non_idempotent_penalty",
                delta=NON_IDEMPOTENT_PENALTY,
                explanation=(
                    "Action is non-idempotent (irreversible); "
                    "BOSS adds +15 to ensure at least one tier of escalation."
                ),
            )
        )
        composite += NON_IDEMPOTENT_PENALTY

    if composite > COMPOSITE_CAP:
        modifiers.append(
            CompositeModifier(
                name="cap_100",
                delta=round(COMPOSITE_CAP - composite, 4),
                explanation="Composite capped at 100.",
            )
        )
        composite = COMPOSITE_CAP

    return (
        round(weighted_sum, 4),
        round(composite_raw, 4),
        round(composite, 4),
        modifiers,
    )


def evaluate(intent: IntentObject, tier_config: TierConfig) -> BOSSResult:
    """Score every dimension and build a BOSSResult with modifiers & tier."""
    dimension_scores = score_dimensions(intent)
    weighted_sum, composite_raw, composite_final, modifiers = compute_composite(
        dimension_scores,
        tier_config,
        is_non_idempotent=intent.is_non_idempotent,
    )
    tier = route(composite_final)
    return BOSSResult(
        intent_id=intent.intent_id,
        tier_config=tier_config,
        dimension_scores=dimension_scores,
        weighted_sum=weighted_sum,
        tier_weight_total=tier_config.total_weight(),
        composite_raw=composite_raw,
        composite_final=composite_final,
        modifiers=modifiers,
        escalation_tier=tier,
    )
