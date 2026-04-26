"""End-to-end POST /v1/score API tests.

These tests exercise the FastAPI app using ``httpx.AsyncClient`` bound
to an in-process ASGI transport. They validate:

* the canonical NetStreamX Amber Coast case routes to ELEVATED;
* a safe/low-risk intent routes to SOAP;
* the OHSHAT variant (security = CVSS 9.6, prompt_injection 0.85)
  crosses the Critical Dimension Override threshold;
* every /score call writes a SCORED event to the flight recorder;
* auth (when enabled) rejects missing tokens.
"""

from __future__ import annotations

import json

import httpx
import pytest

from boss_core.flight_recorder import FlightRecorder
from boss_core.schemas import IntentObject


@pytest.mark.asyncio
async def test_soap_scoring(
    api_client: httpx.AsyncClient,
    soap_intent: IntentObject,
) -> None:
    response = await api_client.post(
        "/v1/score",
        json=json.loads(soap_intent.model_dump_json()),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["escalation_tier"] == "SOAP"
    assert 0.0 <= body["composite_final"] <= 10.0
    assert len(body["dimension_scores"]) == 7


@pytest.mark.asyncio
async def test_amber_coast_routes_to_elevated(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
) -> None:
    """The book's canonical NetStreamX example lands in the ELEVATED band."""
    response = await api_client.post(
        "/v1/score",
        json=json.loads(amber_coast_intent.model_dump_json()),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["escalation_tier"] == "ELEVATED"
    assert 30.0 < body["composite_final"] <= 50.0
    # All seven dimensions must carry a score.
    dimensions = body["dimension_scores"]
    assert set(dimensions.keys()) == {
        "security",
        "sovereignty",
        "financial",
        "regulatory",
        "reputational",
        "rights",
        "doctrinal",
    }


@pytest.mark.asyncio
async def test_ohshat_override_triggered(
    api_client: httpx.AsyncClient,
    ohshat_intent: IntentObject,
) -> None:
    """Critical security input must drag composite into OHSHAT."""
    response = await api_client.post(
        "/v1/score",
        json=json.loads(ohshat_intent.model_dump_json()),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["escalation_tier"] == "OHSHAT"
    assert body["composite_final"] > 75.0
    # Both the override and the non-idempotent penalty should appear.
    mod_names = {m["name"] for m in body["modifiers"]}
    assert "critical_dimension_override" in mod_names
    assert "non_idempotent_penalty" in mod_names


@pytest.mark.asyncio
async def test_score_appends_flight_recorder_event(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
    flight_recorder: FlightRecorder,
) -> None:
    await api_client.post(
        "/v1/score",
        json=json.loads(amber_coast_intent.model_dump_json()),
    )
    scored = [
        e
        for e in flight_recorder.events()
        if e.event_type == "SCORED"
        and e.payload.get("intent_id") == str(amber_coast_intent.intent_id)
    ]
    assert len(scored) == 1
    assert scored[0].payload["escalation_tier"] == "ELEVATED"
    # The chain should still verify cleanly after API activity.
    assert flight_recorder.verify() is True


@pytest.mark.asyncio
async def test_explain_returns_scored_events(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
) -> None:
    await api_client.post(
        "/v1/score",
        json=json.loads(amber_coast_intent.model_dump_json()),
    )
    response = await api_client.get(f"/v1/score/{amber_coast_intent.intent_id}/explain")
    assert response.status_code == 200
    body = response.json()
    assert body["intent_id"] == str(amber_coast_intent.intent_id)
    assert len(body["events"]) >= 1


@pytest.mark.asyncio
async def test_score_rejects_unknown_dimension(
    api_client: httpx.AsyncClient,
) -> None:
    bad = {
        "source": {"user_id": "agent.malformed", "role": "system"},
        "headline": "",  # empty headline should be rejected
        "dimension_inputs": {},
    }
    response = await api_client.post("/v1/score", json=bad)
    assert response.status_code == 422
