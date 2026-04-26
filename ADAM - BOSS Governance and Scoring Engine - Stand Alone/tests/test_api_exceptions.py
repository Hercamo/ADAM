"""Exception packet API tests."""

from __future__ import annotations

import json

import httpx
import pytest

from boss_core.schemas import IntentObject


@pytest.mark.asyncio
async def test_soap_intent_rejected_as_no_exception_needed(
    api_client: httpx.AsyncClient,
    soap_intent: IntentObject,
) -> None:
    response = await api_client.post(
        "/v1/exceptions",
        json={
            "intent": json.loads(soap_intent.model_dump_json()),
            "alternatives": [],
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_amber_coast_generates_exception_packet(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
) -> None:
    response = await api_client.post(
        "/v1/exceptions",
        json={
            "intent": json.loads(amber_coast_intent.model_dump_json()),
            "alternatives": [
                {
                    "alt_id": "alt-reduce-scope",
                    "description": "Launch in 4 countries, not 8",
                    "projected_composite": 28.0,
                    "rationale": "Drops regulatory footprint below ELEVATED.",
                }
            ],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["escalation_tier"] == "ELEVATED"
    assert body["response_sla_minutes"] == 60
    assert body["intent_id"] == str(amber_coast_intent.intent_id)
    assert len(body["alternatives"]) == 1
    assert body["alternatives"][0]["alt_id"] == "alt-reduce-scope"


@pytest.mark.asyncio
async def test_ohshat_generates_packet_with_fifteen_minute_sla(
    api_client: httpx.AsyncClient,
    ohshat_intent: IntentObject,
) -> None:
    response = await api_client.post(
        "/v1/exceptions",
        json={
            "intent": json.loads(ohshat_intent.model_dump_json()),
            "alternatives": [],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["escalation_tier"] == "OHSHAT"
    assert body["response_sla_minutes"] == 15
