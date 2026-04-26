"""Shared helpers for every BOSS adapter.

Adapters live outside the core scoring engine and must never import a
framework-specific dependency at module load time. Instead, they accept
duck-typed dicts that mirror whatever the framework hands them (a
LangGraph tool call, an Azure AI Foundry action, a CrewAI task, etc.)
and translate those into an :class:`boss_core.schemas.IntentObject`.

The goal is to make integration a single function call::

    from boss_adapters import evaluate_payload, DecisionAction

    decision = evaluate_payload(
        payload={"tool": "transfer_funds", "args": {"amount_eur": 250000}},
        framework="langgraph",
        tenant="netstreamx",
    )
    if decision.action is DecisionAction.BLOCK:
        raise RuntimeError(decision.rationale)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from boss_core.composite import evaluate
from boss_core.exceptions import AdapterError
from boss_core.schemas import (
    BOSSResult,
    DimensionInputBundle,
    EscalationTier,
    IntentContext,
    IntentObject,
    IntentSource,
    RiskRole,
    RiskTolerance,
    Urgency,
)
from boss_core.tiers import ADAM_DEFAULT_TIERS, TierConfig

__all__ = [
    "AdapterDecision",
    "AdapterError",
    "DecisionAction",
    "evaluate_payload",
    "intent_from_payload",
]


class DecisionAction(str, Enum):  # noqa: UP042 - py310 dev-sandbox compat
    """High-level instruction for the calling framework.

    The mapping from escalation tier to action is the ADAM default —
    callers may override by consulting :class:`BOSSResult` directly and
    making their own decision.
    """

    ALLOW = "allow"
    ALLOW_WITH_LOGGING = "allow_with_logging"
    ESCALATE = "escalate"
    BLOCK = "block"
    EMERGENCY_STOP = "emergency_stop"


_TIER_TO_ACTION: dict[EscalationTier, DecisionAction] = {
    EscalationTier.SOAP: DecisionAction.ALLOW,
    EscalationTier.MODERATE: DecisionAction.ALLOW_WITH_LOGGING,
    EscalationTier.ELEVATED: DecisionAction.ESCALATE,
    EscalationTier.HIGH: DecisionAction.ESCALATE,
    EscalationTier.OHSHAT: DecisionAction.EMERGENCY_STOP,
}


@dataclass(frozen=True)
class AdapterDecision:
    """Normalized governance decision returned by every adapter.

    Attributes
    ----------
    action:
        High-level instruction to the caller (ALLOW, ESCALATE, etc.).
    composite:
        Final BOSS composite score (0-100).
    escalation_tier:
        SOAP..OHSHAT routing result.
    rationale:
        Human-readable explanation summarizing dominant dimensions.
    intent_id:
        UUID of the IntentObject the engine built for this action.
    result_id:
        UUID of the BOSSResult the engine produced.
    framework:
        The adapter framework name (``langgraph``, ``openai_agents``,
        ``ai_foundry``, ``crewai``, or ``generic``).
    boss_result:
        Full :class:`BOSSResult` if the caller wants deeper introspection.
    """

    action: DecisionAction
    composite: float
    escalation_tier: EscalationTier
    rationale: str
    intent_id: UUID
    result_id: UUID
    framework: str
    boss_result: BOSSResult = field(repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""
        return {
            "action": self.action.value,
            "composite": self.composite,
            "escalation_tier": self.escalation_tier.value,
            "rationale": self.rationale,
            "intent_id": str(self.intent_id),
            "result_id": str(self.result_id),
            "framework": self.framework,
            "boss_result": self.boss_result.model_dump(mode="json"),
        }


# ---------------------------------------------------------------------------
# Intent construction
# ---------------------------------------------------------------------------


def intent_from_payload(
    payload: Mapping[str, Any],
    *,
    framework: str,
    tenant: str = "default",
    actor_id: str = "agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
    doctrine_version: str = "unspecified",
    policy_bundle: str = "default",
    risk_tolerance: RiskTolerance | None = None,
) -> IntentObject:
    """Build an IntentObject from a generic payload dictionary.

    The payload is expected to have (at minimum) a ``headline`` or
    ``tool`` field. Every other field is optional — anything the caller
    does not supply defaults to conservative zero-risk inputs. This is
    deliberate: BOSS will still score the dimensions, just without
    specific evidence, so the caller gets a low-but-non-zero baseline
    they can refine as their pipeline matures.

    Parameters
    ----------
    payload:
        Framework-native action payload (duck-typed dict).
    framework:
        Name of the originating framework (for audit/attribution).
    tenant:
        Tenant identifier recorded on the intent.
    actor_id, actor_role:
        Identity of the caller — who is asking BOSS to govern.
    urgency:
        Urgency class; influences Exception Economy SLA selection.
    is_non_idempotent:
        If ``True``, the +15 irreversibility penalty is applied. If
        ``None``, BOSS inspects the payload for an ``is_non_idempotent``
        or ``reversible`` hint.
    doctrine_version, policy_bundle:
        Snapshot identifiers recorded on the intent context.
    risk_tolerance:
        Director-supplied tolerances; defaults to BOSS conservative baseline.

    Returns
    -------
    IntentObject
        A fully valid intent ready for :func:`boss_core.composite.evaluate`.
    """
    if not isinstance(payload, Mapping):
        raise AdapterError(
            f"Adapter payload must be a mapping/dict; got {type(payload).__name__} instead."
        )

    headline = _extract_headline(payload, framework=framework)
    description = payload.get("description") or payload.get("reasoning")

    # Determine non-idempotence.
    if is_non_idempotent is None:
        is_non_idempotent = bool(
            payload.get("is_non_idempotent")
            or payload.get("irreversible")
            or (payload.get("reversible") is False)
        )

    # Pull dimension inputs — adapters may pass nested inputs explicitly
    # under ``boss_inputs`` to signal exact values per dimension.
    dimension_inputs = _extract_dimension_inputs(payload)

    source = IntentSource(
        user_id=str(actor_id),
        role=actor_role,
        delegation_chain=list(payload.get("delegation_chain", []) or []),
    )

    context = IntentContext(
        doctrine_version=doctrine_version,
        policy_bundle=policy_bundle,
        active_policies=list(payload.get("active_policies", []) or []),
        core_graph_snapshot_ref=payload.get("core_graph_snapshot_ref"),
        previous_intents=[str(x) for x in payload.get("previous_intents", []) or []],
        region_scope=list(payload.get("region_scope", []) or []),
        tenant=str(tenant),
    )

    return IntentObject(
        source=source,
        headline=headline[:512],
        description=description,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
        context=context,
        dimension_inputs=dimension_inputs,
        risk_tolerance=risk_tolerance or RiskTolerance(),
    )


def _extract_headline(payload: Mapping[str, Any], *, framework: str) -> str:
    """Derive a human-readable headline from a framework payload."""
    for key in ("headline", "summary", "title"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Framework-specific quirks
    if framework == "langgraph":
        tool = payload.get("tool") or payload.get("name")
        if tool:
            return f"LangGraph tool: {tool}"
    if framework == "openai_agents":
        tool = payload.get("name") or payload.get("function", {}).get("name")
        if tool:
            return f"OpenAI Agents tool: {tool}"
    if framework == "ai_foundry":
        tool = payload.get("action") or payload.get("tool_name")
        if tool:
            return f"AI Foundry action: {tool}"
    if framework == "crewai":
        task = payload.get("task") or payload.get("description")
        if task:
            return f"CrewAI task: {task}"

    # Fall back to the first stringy value
    for key in ("tool", "name", "action"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return f"{framework} action: {value.strip()}"

    return f"{framework} action (unlabelled)"


def _extract_dimension_inputs(payload: Mapping[str, Any]) -> DimensionInputBundle:
    """Pull per-dimension inputs out of the payload.

    Callers may pre-populate dimension inputs by nesting them under
    ``boss_inputs``. Otherwise a blank bundle is returned and every
    scorer will produce a zero/low baseline.
    """
    nested = payload.get("boss_inputs")
    if isinstance(nested, Mapping):
        data: dict[str, Any] = {}
        for key in (
            "security",
            "sovereignty",
            "financial",
            "regulatory",
            "reputational",
            "rights",
            "doctrinal",
        ):
            raw = nested.get(key)
            if isinstance(raw, Mapping):
                data[key] = dict(raw)
        return DimensionInputBundle(**data)
    return DimensionInputBundle()


def evaluate_payload(
    payload: Mapping[str, Any],
    *,
    framework: str,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    actor_id: str = "agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
) -> AdapterDecision:
    """One-shot adapter entry-point — normalize, score, decide."""
    intent = intent_from_payload(
        payload,
        framework=framework,
        tenant=tenant,
        actor_id=actor_id,
        actor_role=actor_role,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
    )
    cfg = tier_config or ADAM_DEFAULT_TIERS
    result = evaluate(intent, cfg)
    rationale = _rationale_from_result(result)
    action = _TIER_TO_ACTION[result.escalation_tier]
    return AdapterDecision(
        action=action,
        composite=result.composite_final,
        escalation_tier=result.escalation_tier,
        rationale=rationale,
        intent_id=result.intent_id,
        result_id=result.result_id,
        framework=framework,
        boss_result=result,
    )


def _rationale_from_result(result: BOSSResult) -> str:
    """Build a one-line rationale summarizing the dominant risk driver(s)."""
    ordered = sorted(
        result.dimension_scores.values(),
        key=lambda ds: ds.raw_score,
        reverse=True,
    )
    top = ordered[0]
    second = ordered[1] if len(ordered) > 1 else None
    if top.raw_score <= 5:
        return (
            f"Composite {result.composite_final:.1f} — all dimensions low; "
            f"tier {result.escalation_tier.value}."
        )
    parts = [
        f"{top.dimension.value}={top.raw_score:.1f}",
    ]
    if second and second.raw_score > 5:
        parts.append(f"{second.dimension.value}={second.raw_score:.1f}")
    return (
        f"Composite {result.composite_final:.1f} ({result.escalation_tier.value}); "
        f"top drivers: {', '.join(parts)}."
    )
