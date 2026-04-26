"""Decision receipt API tests."""

from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest

from boss_core.flight_recorder import FlightRecorder
from boss_core.schemas import IntentObject


@pytest.mark.asyncio
async def test_receipt_round_trip(
    api_client: httpx.AsyncClient,
    amber_coast_intent: IntentObject,
    flight_recorder: FlightRecorder,
) -> None:
    # Step 1 — score
    score_resp = await api_client.post(
        "/v1/score",
        json=json.loads(amber_coast_intent.model_dump_json()),
    )
    assert score_resp.status_code == 200
    score = score_resp.json()

    # Step 2 — raise exception packet
    packet_resp = await api_client.post(
        "/v1/exceptions",
        json={
            "intent": json.loads(amber_coast_intent.model_dump_json()),
            "alternatives": [],
        },
    )
    assert packet_resp.status_code == 201
    packet = packet_resp.json()

    # Step 3 — sign receipt
    receipt_resp = await api_client.post(
        "/v1/receipts",
        json={
            "packet_id": packet["packet_id"],
            "intent_id": str(amber_coast_intent.intent_id),
            "result_id": score["result_id"],
            "director_id": "director.eu.governor",
            "decision": "APPROVE_WITH_CONSTRAINTS",
            "applied_constraints": ["eu_residency_only", "cap_spend_10m"],
            "director_note": "Approved subject to EU-only data path.",
        },
    )
    assert receipt_resp.status_code == 200
    receipt = receipt_resp.json()
    assert receipt["decision"] == "APPROVE_WITH_CONSTRAINTS"
    assert receipt["director_id"] == "director.eu.governor"
    assert len(receipt["receipt_hash"]) == 64

    # Flight recorder must now include a DECISION_RECORDED event.
    events = list(flight_recorder.events())
    decision_events = [e for e in events if e.event_type == "DECISION_RECORDED"]
    assert len(decision_events) == 1
    assert decision_events[0].payload["decision"] == "APPROVE_WITH_CONSTRAINTS"
    assert flight_recorder.verify() is True


@pytest.mark.asyncio
async def test_receipt_rejects_empty_director_id(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post(
        "/v1/receipts",
        json={
            "packet_id": str(uuid4()),
            "intent_id": str(uuid4()),
            "result_id": str(uuid4()),
            "director_id": "",
            "decision": "APPROVE",
        },
    )
    assert response.status_code == 422
