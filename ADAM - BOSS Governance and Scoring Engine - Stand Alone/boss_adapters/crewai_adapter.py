"""CrewAI adapter (thin translator).

CrewAI ``Task`` and ``Tool`` invocations carry a ``description``,
``expected_output``, an ``agent`` reference, and a ``tools`` list.
Tool calls themselves look like ``{"name": str, "args": dict}``. This
adapter accepts either a Task dict or a tool-call dict.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from boss_adapters.base import AdapterDecision, evaluate_payload
from boss_core.schemas import RiskRole, Urgency
from boss_core.tiers import TierConfig

__all__ = [
    "normalize_crewai_task",
    "normalize_crewai_tool",
    "score_crewai_task",
    "score_crewai_tool",
]


def _task_to_payload(task: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(task, Mapping):
        description = task.get("description") or task.get("prompt") or ""
        expected = task.get("expected_output") or task.get("expected_outcome")
        agent = task.get("agent")
        tools = list(task.get("tools", []) or [])
    else:
        description = getattr(task, "description", "") or ""
        expected = getattr(task, "expected_output", None)
        agent = getattr(task, "agent", None)
        tools = list(getattr(task, "tools", []) or [])

    agent_name: str | None
    if isinstance(agent, Mapping):
        agent_name = agent.get("role") or agent.get("name")
    else:
        agent_name = getattr(agent, "role", None) or getattr(agent, "name", None)

    payload: dict[str, Any] = {
        "task": description[:480],
        "headline": f"CrewAI task: {description[:80] or 'unlabelled'}",
        "description": description,
        "expected_output": expected,
        "agent": agent_name,
        "tools": [
            getattr(t, "name", None) or (t.get("name") if isinstance(t, Mapping) else str(t))
            for t in tools
        ],
    }
    boss_inputs = (
        task.get("boss_inputs") if isinstance(task, Mapping) else getattr(task, "boss_inputs", None)
    )
    if isinstance(boss_inputs, Mapping):
        payload["boss_inputs"] = dict(boss_inputs)
    return payload


def _tool_to_payload(tool_call: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(tool_call, Mapping):
        name = tool_call.get("name") or tool_call.get("tool")
        args = tool_call.get("args") or tool_call.get("arguments") or {}
    else:
        name = getattr(tool_call, "name", None) or getattr(tool_call, "tool", None)
        args = getattr(tool_call, "args", None) or {}
    if not isinstance(args, Mapping):
        args = {"raw": args}
    payload: dict[str, Any] = {
        "tool": name or "unnamed_tool",
        "args": dict(args),
        "headline": f"CrewAI tool: {name or 'unnamed_tool'}",
    }
    boss_inputs = args.get("boss_inputs") if isinstance(args, dict) else None
    if isinstance(boss_inputs, Mapping):
        payload["boss_inputs"] = dict(boss_inputs)
    return payload


def normalize_crewai_task(task: Any) -> dict[str, Any]:
    """Return the BOSS payload dict for a CrewAI Task."""
    return _task_to_payload(task)


def normalize_crewai_tool(tool_call: Any) -> dict[str, Any]:
    """Return the BOSS payload dict for a CrewAI tool invocation."""
    return _tool_to_payload(tool_call)


def score_crewai_task(
    task: Any,
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    actor_id: str = "crewai_agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
) -> AdapterDecision:
    """Score a CrewAI Task and return a decision."""
    payload = _task_to_payload(task)
    return evaluate_payload(
        payload,
        framework="crewai",
        tier_config=tier_config,
        tenant=tenant,
        actor_id=actor_id,
        actor_role=actor_role,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
    )


def score_crewai_tool(
    tool_call: Any,
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    actor_id: str = "crewai_agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
) -> AdapterDecision:
    """Score a CrewAI tool invocation and return a decision."""
    payload = _tool_to_payload(tool_call)
    return evaluate_payload(
        payload,
        framework="crewai",
        tier_config=tier_config,
        tenant=tenant,
        actor_id=actor_id,
        actor_role=actor_role,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
    )
