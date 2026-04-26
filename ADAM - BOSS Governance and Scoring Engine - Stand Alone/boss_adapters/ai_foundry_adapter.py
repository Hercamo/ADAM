"""Azure AI Foundry adapter (thin translator).

Azure AI Foundry agents surface tool invocations as ``AgentAction``
objects with ``tool`` / ``tool_input`` fields when using the
``azure-ai-agents`` SDK, or as ``ToolCall`` items when using the
Responses-style Foundry endpoint. This adapter accepts either shape
as a duck-typed dict and produces a BOSS governance decision.

Foundry-specific notes
----------------------
* If the payload carries an Azure ``evaluators`` section (PII, Indirect
  Attack, Protected Material, Hate/Unfairness, Groundedness), the
  adapter promotes those into the BOSS security/reputational/rights
  dimension inputs where natural mappings exist.
* If the payload specifies ``data_residency`` or ``region``, those are
  copied to the sovereignty dimension inputs so the SEAL scorer can
  flag cross-region execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from boss_adapters.base import AdapterDecision, evaluate_payload
from boss_core.schemas import RiskRole, Urgency
from boss_core.tiers import TierConfig

__all__ = ["normalize_foundry_action", "score_foundry_action"]


def _coerce_action(action: Any) -> dict[str, Any]:
    """Normalize an Azure AI Foundry action into a BOSS payload dict."""
    if isinstance(action, Mapping):
        # Langchain-style AgentAction: {"tool": "...", "tool_input": {...}}
        if action.get("tool") is not None and "tool_input" in action:
            name = action["tool"]
            args = action.get("tool_input") or {}
        # Foundry ToolCall: {"name": "...", "parameters": {...}, "id": "..."}
        elif "parameters" in action:
            name = action.get("name") or action.get("tool_name")
            args = action.get("parameters") or {}
        else:
            name = (
                action.get("name")
                or action.get("tool")
                or action.get("tool_name")
                or action.get("action")
            )
            args = action.get("arguments") or action.get("args") or action.get("input") or {}
    else:
        name = (
            getattr(action, "name", None)
            or getattr(action, "tool", None)
            or getattr(action, "tool_name", None)
        )
        args = (
            getattr(action, "tool_input", None)
            or getattr(action, "parameters", None)
            or getattr(action, "arguments", None)
            or {}
        )

    if not isinstance(args, Mapping):
        args = {"raw": args}
    args = dict(args)

    payload: dict[str, Any] = {
        "action": name or "unnamed_action",
        "args": args,
        "headline": f"AI Foundry action: {name or 'unnamed_action'}",
    }

    # Promote Foundry evaluator outputs into BOSS dimension inputs.
    boss_inputs: dict[str, dict[str, Any]] = {}

    evaluators = (action.get("evaluators") if isinstance(action, Mapping) else None) or args.get(
        "evaluators"
    )
    if isinstance(evaluators, Mapping):
        security: dict[str, Any] = {}
        rights: dict[str, Any] = {}
        reputational: dict[str, Any] = {}
        if "indirect_attack" in evaluators:
            security["prompt_injection_risk"] = _to_float(evaluators["indirect_attack"])
        if "pii" in evaluators:
            rights["authorization_certainty"] = 1.0 - _to_float(evaluators["pii"])
        if "protected_material" in evaluators:
            rights["ownership_certainty"] = 1.0 - _to_float(evaluators["protected_material"])
        if "hate_unfairness" in evaluators:
            reputational["esg_severity_score"] = _to_float(evaluators["hate_unfairness"]) * 100.0
        if security:
            boss_inputs["security"] = security
        if rights:
            boss_inputs["rights"] = rights
        if reputational:
            boss_inputs["reputational"] = reputational

    # Sovereignty — data residency / region pinning.
    region = (
        (action.get("data_residency") if isinstance(action, Mapping) else None)
        or args.get("data_residency")
        or (action.get("region") if isinstance(action, Mapping) else None)
        or args.get("region")
    )
    if region:
        boss_inputs.setdefault("sovereignty", {})["data_residency"] = str(region)

    # Merge any explicit boss_inputs already on the payload.
    explicit = args.get("boss_inputs")
    if isinstance(explicit, Mapping):
        for key, value in explicit.items():
            if isinstance(value, Mapping):
                boss_inputs.setdefault(key, {}).update(dict(value))

    if boss_inputs:
        payload["boss_inputs"] = boss_inputs

    return payload


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_foundry_action(action: Any) -> dict[str, Any]:
    """Return the BOSS payload dict for a Foundry action/tool call."""
    return _coerce_action(action)


def score_foundry_action(
    action: Any,
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    actor_id: str = "ai_foundry_agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
) -> AdapterDecision:
    """Score an Azure AI Foundry action and return a decision."""
    payload = _coerce_action(action)
    return evaluate_payload(
        payload,
        framework="ai_foundry",
        tier_config=tier_config,
        tenant=tenant,
        actor_id=actor_id,
        actor_role=actor_role,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
    )
