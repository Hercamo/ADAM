"""Exception packet generator and decision receipt builder."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Literal
from uuid import UUID

from boss_core.router import window_for
from boss_core.schemas import (
    AlternativeAction,
    BOSSResult,
    DecisionReceipt,
    EscalationTier,
    ExceptionPacket,
    IntentObject,
    utcnow,
)
from boss_core.tiers import DimensionKey

DecisionLiteral = Literal["APPROVE", "APPROVE_WITH_CONSTRAINTS", "REJECT", "DEFER", "ESCALATE"]

_APPROVERS_BY_TIER: dict[EscalationTier, tuple[str, ...]] = {
    EscalationTier.SOAP: (),
    EscalationTier.MODERATE: ("domain_governor",),
    EscalationTier.ELEVATED: ("domain_governor",),
    EscalationTier.HIGH: ("domain_director",),
    EscalationTier.OHSHAT: ("ceo", "cfo", "legal_director", "market_director", "ciso"),
}

_DIMENSION_TO_DIRECTOR: dict[DimensionKey, str] = {
    DimensionKey.SECURITY: "ciso",
    DimensionKey.SOVEREIGNTY: "ciso",
    DimensionKey.FINANCIAL: "cfo",
    DimensionKey.REGULATORY: "legal_director",
    DimensionKey.REPUTATIONAL: "market_director",
    DimensionKey.RIGHTS: "legal_director",
    DimensionKey.DOCTRINAL: "ceo",
}


def _drivers_from_result(result: BOSSResult, limit: int = 3) -> list[str]:
    ranked = sorted(result.dimension_scores.values(), key=lambda ds: ds.raw_score, reverse=True)
    drivers: list[str] = []
    for ds in ranked[:limit]:
        if ds.raw_score <= 0:
            continue
        contribution = result.tier_config.contribution(ds.dimension)
        drivers.append(
            f"{ds.dimension.value} scored {ds.raw_score:.2f} "
            f"(tier contribution {contribution:.2f}%)"
        )
    for modifier in result.modifiers:
        drivers.append(f"{modifier.name}: {modifier.explanation}")
    return drivers


def _required_approvers(result: BOSSResult) -> list[str]:
    base = set(_APPROVERS_BY_TIER[result.escalation_tier])
    for ds in result.dimension_scores.values():
        if ds.raw_score >= 50.0:
            base.add(_DIMENSION_TO_DIRECTOR[ds.dimension])
    return sorted(base)


def build_exception_packet(
    intent: IntentObject,
    result: BOSSResult,
    alternatives: Sequence[AlternativeAction] | None = None,
) -> ExceptionPacket:
    """Produce an exception packet when an intent does not qualify for SOAP."""
    window = window_for(result.escalation_tier)
    summary = (
        f"Intent '{intent.headline}' routed to {result.escalation_tier.value}"
        f" (composite {result.composite_final:.2f})."
    )
    return ExceptionPacket(
        intent_id=intent.intent_id,
        result_id=result.result_id,
        escalation_tier=result.escalation_tier,
        summary=summary,
        drivers=_drivers_from_result(result),
        required_approvers=_required_approvers(result),
        alternatives=list(alternatives or []),
        response_sla_minutes=window.sla_minutes,
        recommended_alternative=(alternatives[0].alt_id if alternatives else None),
    )


def _canonical(payload: Mapping[str, object]) -> bytes:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )


def sign_decision(
    *,
    packet_id: UUID,
    intent_id: UUID,
    result_id: UUID,
    director_id: str,
    decision: DecisionLiteral,
    prior_hash: str,
    selected_alternative: str | None = None,
    applied_constraints: Sequence[str] | None = None,
    director_note: str | None = None,
) -> DecisionReceipt:
    """Produce a hash-chained decision receipt."""
    signed_at = utcnow()
    body = {
        "packet_id": str(packet_id),
        "intent_id": str(intent_id),
        "result_id": str(result_id),
        "director_id": director_id,
        "decision": decision,
        "selected_alternative": selected_alternative,
        "applied_constraints": list(applied_constraints or []),
        "director_note": director_note,
        "signed_at": signed_at.isoformat(),
        "prior_hash": prior_hash,
    }
    receipt_hash = hashlib.sha256(_canonical(body)).hexdigest()
    return DecisionReceipt(
        packet_id=packet_id,
        intent_id=intent_id,
        result_id=result_id,
        director_id=director_id,
        decision=decision,
        selected_alternative=selected_alternative,
        applied_constraints=list(applied_constraints or []),
        director_note=director_note,
        signed_at=signed_at,
        prior_hash=prior_hash,
        receipt_hash=receipt_hash,
    )
