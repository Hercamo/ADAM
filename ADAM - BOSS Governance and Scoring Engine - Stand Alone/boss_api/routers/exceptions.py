"""Exception packet endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from boss_api.deps import get_flight_recorder, get_tier_config
from boss_api.security import require_token
from boss_api.telemetry import EXCEPTION_COUNTER
from boss_core.composite import evaluate
from boss_core.flight_recorder import FlightRecorder
from boss_core.receipts import build_exception_packet
from boss_core.schemas import AlternativeAction, ExceptionPacket, IntentObject
from boss_core.tiers import TierConfig

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


@router.post(
    "",
    response_model=ExceptionPacket,
    status_code=status.HTTP_201_CREATED,
    summary="Generate an exception packet for an intent",
)
async def raise_exception(
    intent: Annotated[IntentObject, Body(...)],
    alternatives: Annotated[list[AlternativeAction] | None, Body(...)] = None,
    tier_config: TierConfig = Depends(get_tier_config),
    flight: FlightRecorder = Depends(get_flight_recorder),
    _token: str = Depends(require_token),
) -> ExceptionPacket:
    result = evaluate(intent, tier_config)
    if result.escalation_tier.value in {"SOAP"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Intent routed to SOAP; no exception packet required. "
                f"Composite {result.composite_final:.2f}."
            ),
        )
    packet = build_exception_packet(intent, result, alternatives or [])
    EXCEPTION_COUNTER.labels(tier=result.escalation_tier.value).inc()
    flight.append(
        "EXCEPTION_RAISED",
        {
            "packet_id": str(packet.packet_id),
            "intent_id": str(intent.intent_id),
            "tier": result.escalation_tier.value,
            "composite_final": result.composite_final,
        },
    )
    return packet
