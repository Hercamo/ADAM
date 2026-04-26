"""Director decision receipt endpoint."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from boss_api.deps import get_flight_recorder
from boss_api.security import require_token
from boss_core.flight_recorder import FlightRecorder
from boss_core.receipts import sign_decision
from boss_core.schemas import DecisionReceipt

router = APIRouter(prefix="/receipts", tags=["receipts"])


class ReceiptRequest(BaseModel):
    """Input body for creating a decision receipt."""

    packet_id: UUID
    intent_id: UUID
    result_id: UUID
    director_id: str = Field(..., min_length=1)
    decision: Literal[
        "APPROVE",
        "APPROVE_WITH_CONSTRAINTS",
        "REJECT",
        "DEFER",
        "ESCALATE",
    ]
    selected_alternative: str | None = None
    applied_constraints: list[str] = Field(default_factory=list)
    director_note: str | None = None


@router.post(
    "",
    response_model=DecisionReceipt,
    summary="Sign a director decision and append to the Flight Recorder",
)
async def create_receipt(
    body: ReceiptRequest,
    flight: FlightRecorder = Depends(get_flight_recorder),
    _token: str = Depends(require_token),
) -> DecisionReceipt:
    prior_hash = flight._sink.head()
    receipt = sign_decision(
        packet_id=body.packet_id,
        intent_id=body.intent_id,
        result_id=body.result_id,
        director_id=body.director_id,
        decision=body.decision,
        prior_hash=prior_hash,
        selected_alternative=body.selected_alternative,
        applied_constraints=body.applied_constraints,
        director_note=body.director_note,
    )
    flight.append(
        "DECISION_RECORDED",
        {
            "receipt_id": str(receipt.receipt_id),
            "packet_id": str(receipt.packet_id),
            "intent_id": str(receipt.intent_id),
            "decision": receipt.decision,
            "director_id": receipt.director_id,
            "receipt_hash": receipt.receipt_hash,
        },
    )
    return receipt
