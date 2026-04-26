"""Canonical Pydantic v2 schemas for the BOSS Engine.

These models are the wire format for the REST API, the Flight Recorder
append log, and the graph loader. They intentionally mirror the ADAM
Intent Object v1.0 and Appendix 6 artifacts as closely as possible so
that BOSS can be embedded inside an existing ADAM deployment without
translation.
"""

from __future__ import annotations

import sys
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

if sys.version_info >= (3, 11):  # noqa: UP036 - py310 dev-sandbox fallback only
    from datetime import UTC
else:  # pragma: no cover - py310 dev-sandbox fallback; CODEX runs on py311+
    from datetime import timezone as _tz

    UTC = _tz.utc  # noqa: UP017 - alias required on py310

from pydantic import BaseModel, ConfigDict, Field, field_validator

from boss_core.tiers import DIMENSION_ORDER, DimensionKey, Tier, TierConfig

# ---------------------------------------------------------------------------
# Common types
# ---------------------------------------------------------------------------


def utcnow() -> datetime:
    """UTC now as a timezone-aware datetime. Isolated for test stubbing."""
    return datetime.now(UTC)


class RiskRole(str, Enum):  # noqa: UP042 - py310 dev-sandbox compat
    """Sources allowed to submit intents against the BOSS Engine."""

    DIRECTOR = "director"
    EXECUTIVE = "executive"
    OPERATOR = "operator"
    SYSTEM = "system"
    EXTERNAL_PARTNER = "external_partner"


class Urgency(str, Enum):  # noqa: UP042 - py310 dev-sandbox compat
    """Urgency class, influences escalation SLA and autonomy budget draw."""

    ROUTINE = "routine"
    ELEVATED = "elevated"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ConstraintType(str, Enum):  # noqa: UP042 - py310 dev-sandbox compat
    """Whether a constraint is hard (block) or soft (preference)."""

    HARD = "hard"
    SOFT = "soft"


class ConstraintDomain(str, Enum):  # noqa: UP042 - py310 dev-sandbox compat
    """BOSS dimension family the constraint belongs to."""

    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    RIGHTS = "rights"
    SAFETY = "safety"
    REPUTATIONAL = "reputational"
    OPERATIONAL = "operational"
    SOVEREIGNTY = "sovereignty"


class EscalationTier(str, Enum):  # noqa: UP042 - py310 dev-sandbox compat
    """SOAP to OHSHAT escalation spectrum (BOSS Formulas Table 3)."""

    SOAP = "SOAP"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    OHSHAT = "OHSHAT"


# ---------------------------------------------------------------------------
# Intent Object (ADAM Intent Object v1.0, condensed)
# ---------------------------------------------------------------------------


class IntentSource(BaseModel):
    """Identity and role of the intent originator."""

    user_id: str = Field(..., description="Unique ID of the human or system caller.")
    role: RiskRole = RiskRole.SYSTEM
    delegation_chain: list[dict[str, Any]] = Field(default_factory=list)


class IntentConstraint(BaseModel):
    """Constraint carried by the intent object."""

    constraint_id: str
    type: ConstraintType
    domain: ConstraintDomain
    description: str
    enforcement_level: Literal["block", "escalate", "log", "warn"] = "block"


class RiskTolerance(BaseModel):
    """Director-specified risk tolerances embedded in the intent."""

    financial_threshold_eur: float | None = Field(default=None, ge=0)
    regulatory_exposure_max: Literal["none", "low", "medium", "high"] = "medium"
    reputational_risk_max: Literal["none", "low", "medium", "high"] = "medium"
    rights_certainty_min: float = Field(default=0.0, ge=0, le=100)
    composite_cap_without_escalation: float = Field(default=30.0, ge=0, le=100)


class IntentContext(BaseModel):
    """Policy/doctrine versioning snapshot."""

    doctrine_version: str = "unspecified"
    policy_bundle: str = "default"
    active_policies: list[dict[str, Any]] = Field(default_factory=list)
    core_graph_snapshot_ref: str | None = None
    previous_intents: list[str] = Field(default_factory=list)
    region_scope: list[str] = Field(default_factory=list)
    tenant: str = "default"


class DimensionInputBundle(BaseModel):
    """Raw, per-dimension input data supplied by the caller.

    Each key is a dimension name, each value is a free-form dict. Every
    dimension scorer validates its own sub-schema in ``dimensions/``. The
    outer layer is deliberately loose so the engine can accept input
    from agent frameworks that only know the rough shape of an action.
    """

    model_config = ConfigDict(extra="allow")

    security: dict[str, Any] = Field(default_factory=dict)
    sovereignty: dict[str, Any] = Field(default_factory=dict)
    financial: dict[str, Any] = Field(default_factory=dict)
    regulatory: dict[str, Any] = Field(default_factory=dict)
    reputational: dict[str, Any] = Field(default_factory=dict)
    rights: dict[str, Any] = Field(default_factory=dict)
    doctrinal: dict[str, Any] = Field(default_factory=dict)


class IntentObject(BaseModel):
    """ADAM-compatible intent object consumed by the BOSS Engine."""

    intent_id: UUID = Field(default_factory=uuid4)
    schema_version: str = "1.0"
    timestamp: datetime = Field(default_factory=utcnow)
    source: IntentSource
    headline: str = Field(..., min_length=1, max_length=512)
    description: str | None = None
    constraints: list[IntentConstraint] = Field(default_factory=list)
    risk_tolerance: RiskTolerance = Field(default_factory=RiskTolerance)
    urgency: Urgency = Urgency.ROUTINE
    is_non_idempotent: bool = Field(
        default=False,
        description=(
            "Whether the action is non-idempotent (irreversible). "
            "Non-idempotent actions trigger the +15 composite penalty."
        ),
    )
    context: IntentContext = Field(default_factory=IntentContext)
    dimension_inputs: DimensionInputBundle = Field(default_factory=DimensionInputBundle)

    @field_validator("timestamp", mode="before")
    @classmethod
    def _ensure_tz(cls, value: Any) -> Any:
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


# ---------------------------------------------------------------------------
# Scoring output models
# ---------------------------------------------------------------------------


class SubComponentScore(BaseModel):
    """A single labelled sub-component contributing to a dimension."""

    name: str
    value: float = Field(..., ge=0)
    max_value: float = Field(..., gt=0)
    rationale: str | None = None


class DimensionScore(BaseModel):
    """Scored output for a single BOSS dimension."""

    dimension: DimensionKey
    raw_score: float = Field(..., ge=0, le=100)
    sub_components: list[SubComponentScore] = Field(default_factory=list)
    frameworks: list[str] = Field(
        default_factory=list,
        description="Keys from boss_core.frameworks.FRAMEWORKS.",
    )
    evidence_refs: list[str] = Field(default_factory=list)
    notes: str | None = None


class CompositeModifier(BaseModel):
    """Explanatory record of a modifier applied to the composite."""

    name: Literal["critical_dimension_override", "non_idempotent_penalty", "cap_100"]
    delta: float
    explanation: str


class BOSSResult(BaseModel):
    """Full BOSS scoring result for an intent."""

    result_id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    tier_config: TierConfig
    dimension_scores: dict[DimensionKey, DimensionScore]
    weighted_sum: float
    tier_weight_total: float
    composite_raw: float
    composite_final: float
    modifiers: list[CompositeModifier] = Field(default_factory=list)
    escalation_tier: EscalationTier
    computed_at: datetime = Field(default_factory=utcnow)

    @field_validator("dimension_scores")
    @classmethod
    def _full_coverage(
        cls, value: dict[DimensionKey, DimensionScore]
    ) -> dict[DimensionKey, DimensionScore]:
        missing = [d for d in DIMENSION_ORDER if d not in value]
        if missing:
            raise ValueError(
                "BOSSResult missing dimension scores: " + ", ".join(m.value for m in missing)
            )
        return value


# ---------------------------------------------------------------------------
# Exception Packet and Decision Receipt
# ---------------------------------------------------------------------------


class AlternativeAction(BaseModel):
    """One of a set of alternatives surfaced to a director."""

    alt_id: str
    description: str
    projected_composite: float = Field(..., ge=0, le=100)
    rationale: str | None = None


class ExceptionPacket(BaseModel):
    """Structured escalation packet (ADAM Exception Economy)."""

    packet_id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    result_id: UUID
    generated_at: datetime = Field(default_factory=utcnow)
    escalation_tier: EscalationTier
    summary: str
    drivers: list[str] = Field(default_factory=list)
    required_approvers: list[str] = Field(default_factory=list)
    alternatives: list[AlternativeAction] = Field(default_factory=list)
    response_sla_minutes: int = Field(..., ge=0)
    recommended_alternative: str | None = None


class DecisionReceipt(BaseModel):
    """Hash-chained receipt produced when a director resolves an exception."""

    receipt_id: UUID = Field(default_factory=uuid4)
    packet_id: UUID
    intent_id: UUID
    result_id: UUID
    director_id: str
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
    signed_at: datetime = Field(default_factory=utcnow)
    prior_hash: str = Field(..., min_length=64, max_length=128)
    receipt_hash: str = Field(..., min_length=64, max_length=128)


# ---------------------------------------------------------------------------
# Flight Recorder event
# ---------------------------------------------------------------------------


class FlightRecorderEvent(BaseModel):
    """Immutable, hash-chained append entry."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: Literal[
        "INTENT_RECEIVED",
        "SCORED",
        "EXCEPTION_RAISED",
        "DECISION_RECORDED",
        "CONFIG_CHANGED",
    ]
    timestamp: datetime = Field(default_factory=utcnow)
    signer: str
    prior_hash: str
    payload: dict[str, Any]
    event_hash: str


# ---------------------------------------------------------------------------
# Tier configuration request/response
# ---------------------------------------------------------------------------


class TierConfigRequest(BaseModel):
    """Request to update the active tier configuration."""

    assignments: dict[DimensionKey, Tier]
    author: str = Field(..., description="Director or authority approving the change.")
    reason: str | None = None


__all__ = [
    "AlternativeAction",
    "BOSSResult",
    "CompositeModifier",
    "ConstraintDomain",
    "ConstraintType",
    "DecisionReceipt",
    "DimensionInputBundle",
    "DimensionScore",
    "EscalationTier",
    "ExceptionPacket",
    "FlightRecorderEvent",
    "IntentConstraint",
    "IntentContext",
    "IntentObject",
    "IntentSource",
    "RiskRole",
    "RiskTolerance",
    "SubComponentScore",
    "TierConfigRequest",
    "Urgency",
    "utcnow",
]
