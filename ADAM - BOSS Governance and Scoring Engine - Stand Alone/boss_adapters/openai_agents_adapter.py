"""OpenAI Agents SDK adapter (thin translator).

The OpenAI Agents SDK (Assistants / Responses API) dispatches actions
as ``function_call`` items with ``name`` and ``arguments`` (JSON
string). This adapter:

1. Normalizes such a call into a BOSS intent.
2. Returns an :class:`boss_adapters.AdapterDecision` the caller can
   use to gate ``client.responses.submit_tool_outputs(...)``.

The adapter does not import the OpenAI SDK. It duck-types the
function-call payload so users can pass either an SDK object or a
plain dict obtained via ``.model_dump()``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from boss_adapters.base import AdapterDecision, evaluate_payload
from boss_core.schemas import RiskRole, Urgency
from boss_core.tiers import TierConfig

__all__ = ["normalize_function_call", "score_function_call"]


def _parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
        return parsed if isinstance(parsed, dict) else {"raw": parsed}
    return {"raw": raw}


def _coerce_call(call: Any) -> dict[str, Any]:
    """Normalize an OpenAI function_call payload into a BOSS payload dict."""
    if isinstance(call, Mapping):
        # Responses API top-level: {"type": "function_call", "name": "...", "arguments": "..."}
        if call.get("type") == "function_call":
            name = call.get("name")
            args = _parse_arguments(call.get("arguments"))
            call_id = call.get("call_id") or call.get("id")
        # Assistants API: {"function": {"name": "...", "arguments": "..."}, "id": "..."}
        elif isinstance(call.get("function"), Mapping):
            name = call["function"].get("name")
            args = _parse_arguments(call["function"].get("arguments"))
            call_id = call.get("id")
        else:
            name = call.get("name") or call.get("tool")
            args = _parse_arguments(call.get("arguments") or call.get("args"))
            call_id = call.get("id") or call.get("call_id")
    else:
        name = getattr(call, "name", None)
        args = _parse_arguments(getattr(call, "arguments", None))
        call_id = getattr(call, "id", None) or getattr(call, "call_id", None)

    payload: dict[str, Any] = {
        "name": name or "unnamed_function",
        "args": args,
        "headline": f"OpenAI Agents tool: {name or 'unnamed_function'}",
    }
    if call_id:
        payload["call_id"] = call_id
    boss_inputs = args.get("boss_inputs") if isinstance(args, dict) else None
    if isinstance(boss_inputs, Mapping):
        payload["boss_inputs"] = dict(boss_inputs)
    return payload


def normalize_function_call(call: Any) -> dict[str, Any]:
    """Return the BOSS-compatible payload dict for an OpenAI function call."""
    return _coerce_call(call)


def score_function_call(
    call: Any,
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    actor_id: str = "openai_agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
) -> AdapterDecision:
    """Score an OpenAI Agents function call and return a decision."""
    payload = _coerce_call(call)
    return evaluate_payload(
        payload,
        framework="openai_agents",
        tier_config=tier_config,
        tenant=tenant,
        actor_id=actor_id,
        actor_role=actor_role,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
    )
