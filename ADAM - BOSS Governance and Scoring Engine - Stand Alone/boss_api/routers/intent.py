"""Intent submission endpoint (fire-and-forget, records a flight event)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from boss_api.deps import get_flight_recorder
from boss_api.security import require_token
from boss_core.flight_recorder import FlightRecorder
from boss_core.schemas import IntentObject

router = APIRouter(prefix="/intents", tags=["intents"])


@router.post("", summary="Register an intent object without scoring it")
async def register_intent(
    intent: IntentObject,
    flight: FlightRecorder = Depends(get_flight_recorder),
    _token: str = Depends(require_token),
) -> dict[str, str]:
    flight.append(
        "INTENT_RECEIVED",
        {
            "intent_id": str(intent.intent_id),
            "headline": intent.headline,
            "tenant": intent.context.tenant,
        },
    )
    return {"intent_id": str(intent.intent_id), "status": "received"}
