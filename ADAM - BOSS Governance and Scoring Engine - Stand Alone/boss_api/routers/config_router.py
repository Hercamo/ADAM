"""Tier configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from boss_api.deps import get_flight_recorder, get_tier_config, set_tier_config
from boss_api.security import require_token
from boss_core.exceptions import TierConfigurationError
from boss_core.flight_recorder import FlightRecorder
from boss_core.schemas import TierConfigRequest
from boss_core.tiers import TierConfig

router = APIRouter(prefix="/config", tags=["config"])


@router.get(
    "/tiers",
    response_model=TierConfig,
    summary="Return the currently active Priority Tier configuration",
)
async def read_tiers(
    tier_config: TierConfig = Depends(get_tier_config),
) -> TierConfig:
    return tier_config


@router.put(
    "/tiers",
    response_model=TierConfig,
    summary="Replace the active Priority Tier configuration (director-only)",
)
async def write_tiers(
    body: TierConfigRequest,
    flight: FlightRecorder = Depends(get_flight_recorder),
    _token: str = Depends(require_token),
) -> TierConfig:
    try:
        new_config = TierConfig(assignments=body.assignments)
    except (TierConfigurationError, ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    set_tier_config(new_config)
    flight.append(
        "CONFIG_CHANGED",
        {
            "author": body.author,
            "reason": body.reason,
            "assignments": {k.value: v.value for k, v in body.assignments.items()},
        },
    )
    return new_config
