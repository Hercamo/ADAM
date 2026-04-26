"""Read-only Flight Recorder tail endpoint.

This endpoint is optional and is gated by the ``BOSS_FLIGHT_RECORDER_TAIL``
environment variable (``0`` by default). Production deployments where the
Flight Recorder is backed by a SIEM normally leave it disabled and route
operator traffic through the SIEM's own UI.

When enabled, it returns the most recent events (newest first), optionally
filtered by event type, so the Evidence Console can render the
hash-chained audit log and surface any integrity break in real time.
"""

from __future__ import annotations

from collections import deque

from fastapi import APIRouter, Depends, HTTPException, Query, status

from boss_api.config import Settings, get_settings
from boss_api.deps import get_flight_recorder
from boss_api.security import require_token
from boss_core.flight_recorder import FlightRecorder
from boss_core.schemas import FlightRecorderEvent

router = APIRouter(prefix="/flightrecorder", tags=["flight-recorder"])


def _tail_enabled(settings: Settings) -> bool:
    import os

    # Settings isn't re-read on every request; check the env directly so
    # operators can flip the toggle without restarting the engine.
    raw = os.getenv("BOSS_FLIGHT_RECORDER_TAIL", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


@router.get(
    "",
    response_model=list[FlightRecorderEvent],
    summary="Return the most recent Flight Recorder events (tail).",
    description=(
        "Returns events newest first. Use `event_type` to filter to a single "
        "category (e.g. `SCORED`) and `limit` to bound the response size. "
        "Disabled unless `BOSS_FLIGHT_RECORDER_TAIL=1`."
    ),
)
async def tail(
    event_type: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=200, ge=1, le=2000),
    flight: FlightRecorder = Depends(get_flight_recorder),
    settings: Settings = Depends(get_settings),
    _token: str = Depends(require_token),
) -> list[FlightRecorderEvent]:
    if not _tail_enabled(settings):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Flight Recorder tail endpoint is disabled. Set "
                "BOSS_FLIGHT_RECORDER_TAIL=1 on the API to enable it."
            ),
        )

    # Efficient tail: keep the last `limit` matching events without
    # materializing the entire log.
    buffer: deque[FlightRecorderEvent] = deque(maxlen=limit)
    for event in flight.events():
        if event_type and event.event_type != event_type:
            continue
        buffer.append(event)
    # Return newest first.
    return list(reversed(buffer))
