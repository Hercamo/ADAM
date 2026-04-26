"""Scoring endpoint: accept an intent, return a full BOSS result."""

from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends

from boss_api.deps import get_flight_recorder, get_tier_config
from boss_api.security import require_token
from boss_api.telemetry import LATENCY, SCORE_TOTAL
from boss_core.composite import evaluate
from boss_core.flight_recorder import FlightRecorder
from boss_core.schemas import BOSSResult, IntentObject
from boss_core.tiers import TierConfig

router = APIRouter(prefix="/score", tags=["scoring"])


class ScoreEnvelope(BOSSResult):
    """Wire-format response envelope extending the BOSSResult."""


@router.post(
    "",
    response_model=ScoreEnvelope,
    summary="Score an intent object",
    description=(
        "Run all seven BOSS dimensions, compute the composite, apply the "
        "Critical Dimension Override and Non-Idempotent Penalty modifiers, "
        "route to a SOAP-to-OHSHAT tier, and append a flight recorder event."
    ),
)
async def score_intent(
    intent: IntentObject,
    tier_config: TierConfig = Depends(get_tier_config),
    flight: FlightRecorder = Depends(get_flight_recorder),
    _token: str = Depends(require_token),
) -> ScoreEnvelope:
    start = time.perf_counter()
    result = evaluate(intent, tier_config)
    LATENCY.observe(time.perf_counter() - start)
    SCORE_TOTAL.labels(tier=result.escalation_tier.value).inc()
    flight.append(
        "SCORED",
        {
            "intent_id": str(intent.intent_id),
            "result_id": str(result.result_id),
            "composite_final": result.composite_final,
            "escalation_tier": result.escalation_tier.value,
        },
    )
    return ScoreEnvelope.model_validate(result.model_dump())


@router.get(
    "/{intent_id}/explain",
    summary="Explain the last score for an intent",
)
async def explain(
    intent_id: UUID,
    flight: FlightRecorder = Depends(get_flight_recorder),
    _token: str = Depends(require_token),
) -> dict[str, object]:
    events = [
        e.model_dump() for e in flight.events() if e.payload.get("intent_id") == str(intent_id)
    ]
    return {"intent_id": str(intent_id), "events": events}
