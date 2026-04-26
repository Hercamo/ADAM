"""Flight Recorder tail endpoint tests."""

from __future__ import annotations

import json

import httpx
import pytest

from boss_core.flight_recorder import FlightRecorder
from boss_core.schemas import IntentObject


@pytest.mark.asyncio
async def test_tail_returns_events_when_enabled(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
) -> None:
    # Fixture sets BOSS_FLIGHT_RECORDER_TAIL=1 — so the endpoint is live.
    await api_client.post(
        "/v1/score",
        json=json.loads(amber_coast_intent.model_dump_json()),
    )
    response = await api_client.get("/v1/flightrecorder?limit=50")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    # Newest-first ordering.
    assert events[0]["event_type"] == "SCORED"


@pytest.mark.asyncio
async def test_tail_filter_by_event_type(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
) -> None:
    await api_client.post(
        "/v1/intents",
        json=json.loads(amber_coast_intent.model_dump_json()),
    )
    await api_client.post(
        "/v1/score",
        json=json.loads(amber_coast_intent.model_dump_json()),
    )
    response = await api_client.get("/v1/flightrecorder?event_type=SCORED&limit=10")
    assert response.status_code == 200
    events = response.json()
    assert all(e["event_type"] == "SCORED" for e in events)


@pytest.mark.asyncio
async def test_tail_disabled_returns_404(
    api_client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The tail endpoint re-reads BOSS_FLIGHT_RECORDER_TAIL at request time
    # so this flip is observed immediately. conftest.fresh_settings set it
    # to "1"; undoing that here should make the endpoint respond with 404.
    monkeypatch.setenv("BOSS_FLIGHT_RECORDER_TAIL", "0")
    response = await api_client.get("/v1/flightrecorder")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tail_rejects_oversized_limit(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/v1/flightrecorder?limit=9999")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_after_api_activity(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
    flight_recorder: FlightRecorder,
) -> None:
    # Mixed traffic on the API must still leave a verifiable chain.
    for _ in range(3):
        await api_client.post(
            "/v1/score",
            json=json.loads(amber_coast_intent.model_dump_json()),
        )
    assert flight_recorder.verify() is True
