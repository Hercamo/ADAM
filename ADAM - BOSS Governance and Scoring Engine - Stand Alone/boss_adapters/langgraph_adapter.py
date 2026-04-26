"""LangGraph / LangChain adapter — deep integration.

This is the reference adapter. It provides:

1. ``normalize_tool_call`` — a pure function that turns a LangGraph
   ``ToolMessage`` / ``ToolCall`` payload into a BOSS intent and scores it.
2. ``BossGuardTool`` — a drop-in ``BaseTool`` subclass that wraps any
   existing LangChain tool and routes it through BOSS before the
   wrapped tool runs. Import requires LangChain.
3. ``boss_guard_node`` — a LangGraph node factory that can be inserted
   between your agent's planner and its tool executor to govern every
   tool call without modifying the tools themselves.
4. ``on_tool_start_callback`` — a LangChain callback handler fragment
   (as a plain dict/function) you can add to any RunnableConfig.

Every symbol is importable without LangChain installed *except* the
class/node that genuinely need it. Those raise a clear ImportError at
call time if the dependency is missing.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from boss_adapters.base import (
    AdapterDecision,
    DecisionAction,
    evaluate_payload,
    intent_from_payload,
)
from boss_core.composite import evaluate as evaluate_intent
from boss_core.exceptions import AdapterError
from boss_core.schemas import IntentObject, RiskRole, Urgency
from boss_core.tiers import ADAM_DEFAULT_TIERS, TierConfig

__all__ = [
    "BossGovernanceError",
    "BossGuardTool",
    "LangGraphToolPayload",
    "boss_guard_node",
    "evaluate_intent",
    "normalize_tool_call",
    "on_tool_start_callback",
    "score_tool_call",
]


class BossGovernanceError(RuntimeError):
    """Raised when BOSS denies a LangGraph tool call outright."""

    def __init__(self, decision: AdapterDecision) -> None:
        self.decision = decision
        super().__init__(
            f"BOSS {decision.escalation_tier.value} ({decision.composite:.1f}): "
            f"{decision.rationale}"
        )


@dataclass
class LangGraphToolPayload:
    """Normalized view of a LangGraph tool invocation.

    LangGraph/LangChain variants all converge on roughly these fields;
    this dataclass is the common denominator we hand to BOSS.
    """

    name: str
    args: dict[str, Any]
    tool_call_id: str | None = None
    run_id: str | None = None
    parent_run_id: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Return a BOSS-compatible payload dict."""
        payload: dict[str, Any] = {
            "tool": self.name,
            "args": dict(self.args),
            "headline": f"LangGraph tool: {self.name}",
        }
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        if self.run_id:
            payload["run_id"] = self.run_id
        if self.parent_run_id:
            payload["parent_run_id"] = self.parent_run_id
        # If the user attached boss_inputs on the args, promote them so
        # dimension scorers see the data.
        boss_inputs = self.args.get("boss_inputs") if isinstance(self.args, dict) else None
        if isinstance(boss_inputs, Mapping):
            payload["boss_inputs"] = dict(boss_inputs)
        return payload


def _coerce_tool_call(obj: Any) -> LangGraphToolPayload:
    """Best-effort coercion of a LangChain/LangGraph tool call object."""
    if isinstance(obj, LangGraphToolPayload):
        return obj
    if isinstance(obj, Mapping):
        # LangChain ToolCall: {"name": "...", "args": {...}, "id": "..."}
        name = obj.get("name") or obj.get("tool") or obj.get("type")
        args = obj.get("args") or obj.get("arguments") or {}
        if isinstance(args, str):
            # Some providers return JSON-encoded strings.
            import json

            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"raw": args}
        if not isinstance(args, Mapping):
            args = {"raw": args}
        return LangGraphToolPayload(
            name=str(name or "unnamed_tool"),
            args=dict(args),
            tool_call_id=obj.get("id") or obj.get("tool_call_id"),
            run_id=obj.get("run_id"),
            parent_run_id=obj.get("parent_run_id"),
        )
    # Duck-type fallback: attribute access
    name = getattr(obj, "name", None) or getattr(obj, "tool", None)
    args = getattr(obj, "args", None) or {}
    if not name:
        raise AdapterError(
            "normalize_tool_call: cannot determine tool name from object "
            f"of type {type(obj).__name__}."
        )
    if not isinstance(args, Mapping):
        args = {"raw": args}
    return LangGraphToolPayload(
        name=str(name),
        args=dict(args),
        tool_call_id=getattr(obj, "id", None) or getattr(obj, "tool_call_id", None),
        run_id=getattr(obj, "run_id", None),
        parent_run_id=getattr(obj, "parent_run_id", None),
    )


# ---------------------------------------------------------------------------
# Pure-function API
# ---------------------------------------------------------------------------


def normalize_tool_call(
    tool_call: Any,
    *,
    tenant: str = "default",
    actor_id: str = "langgraph_agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
) -> IntentObject:
    """Turn a LangChain/LangGraph tool call into a BOSS IntentObject."""
    payload = _coerce_tool_call(tool_call).to_payload()
    return intent_from_payload(
        payload,
        framework="langgraph",
        tenant=tenant,
        actor_id=actor_id,
        actor_role=actor_role,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
    )


def score_tool_call(
    tool_call: Any,
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    actor_id: str = "langgraph_agent",
    actor_role: RiskRole = RiskRole.SYSTEM,
    urgency: Urgency = Urgency.ROUTINE,
    is_non_idempotent: bool | None = None,
) -> AdapterDecision:
    """Score a tool call and return a :class:`AdapterDecision`."""
    payload = _coerce_tool_call(tool_call).to_payload()
    return evaluate_payload(
        payload,
        framework="langgraph",
        tier_config=tier_config,
        tenant=tenant,
        actor_id=actor_id,
        actor_role=actor_role,
        urgency=urgency,
        is_non_idempotent=is_non_idempotent,
    )


# ---------------------------------------------------------------------------
# LangGraph node factory
# ---------------------------------------------------------------------------


def boss_guard_node(
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    on_escalate: Callable[[AdapterDecision], None] | None = None,
    block_actions: tuple[DecisionAction, ...] = (
        DecisionAction.BLOCK,
        DecisionAction.EMERGENCY_STOP,
    ),
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a LangGraph node callable that governs every tool call.

    The returned node expects the standard LangGraph state dict with a
    ``messages`` list whose last message contains ``tool_calls``. Every
    tool call is scored by BOSS:

    * If any call resolves to a blocked action the node raises
      :class:`BossGovernanceError`.
    * Escalated calls trigger ``on_escalate`` (if provided) and pass
      through — the caller is responsible for actually pausing the run.
    * Allowed calls pass through unchanged.

    Example::

        from langgraph.graph import StateGraph
        from boss_adapters.langgraph_adapter import boss_guard_node

        graph = StateGraph(AgentState)
        graph.add_node("plan", planner)
        graph.add_node("boss_guard", boss_guard_node(tenant="acme"))
        graph.add_node("tools", ToolNode(my_tools))
        graph.add_edge("plan", "boss_guard")
        graph.add_edge("boss_guard", "tools")
    """
    cfg = tier_config or ADAM_DEFAULT_TIERS

    def _node(state: dict[str, Any]) -> dict[str, Any]:
        messages = state.get("messages") or []
        if not messages:
            return state
        last = messages[-1]
        tool_calls = (
            last.get("tool_calls")
            if isinstance(last, Mapping)
            else getattr(last, "tool_calls", None)
        ) or []
        decisions: list[AdapterDecision] = []
        for call in tool_calls:
            decision = score_tool_call(call, tier_config=cfg, tenant=tenant)
            decisions.append(decision)
            if decision.action in block_actions:
                raise BossGovernanceError(decision)
            if (
                decision.action
                in (
                    DecisionAction.ESCALATE,
                    DecisionAction.ALLOW_WITH_LOGGING,
                )
                and on_escalate is not None
            ):
                on_escalate(decision)

        new_state = dict(state)
        existing = new_state.get("boss_decisions") or []
        new_state["boss_decisions"] = list(existing) + [d.to_dict() for d in decisions]
        return new_state

    return _node


# ---------------------------------------------------------------------------
# BaseTool wrapper
# ---------------------------------------------------------------------------


def BossGuardTool(  # noqa: N802 — mimics LangChain's CapWords tool constructors
    wrapped: Any,
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    block_actions: tuple[DecisionAction, ...] = (
        DecisionAction.BLOCK,
        DecisionAction.EMERGENCY_STOP,
    ),
    on_escalate: Callable[[AdapterDecision], None] | None = None,
) -> Any:
    """Return a LangChain BaseTool subclass that governs ``wrapped``.

    Requires ``langchain-core`` to be importable. The wrapper delegates
    ``name``, ``description``, and ``args_schema`` to the wrapped tool
    and overrides ``_run`` / ``_arun`` to inject BOSS.
    """
    try:
        from langchain_core.tools import BaseTool
    except ImportError as exc:  # pragma: no cover - requires optional dep
        raise AdapterError(
            "BossGuardTool requires 'langchain-core'. Install with "
            "`pip install boss-engine[langgraph]` or `pip install langchain-core`."
        ) from exc

    cfg = tier_config or ADAM_DEFAULT_TIERS

    class _Guarded(BaseTool):  # type: ignore[misc]
        name: str = getattr(wrapped, "name", "wrapped_tool")
        description: str = getattr(wrapped, "description", "BOSS-governed tool wrapper.")

        def _run(self, *args: Any, **kwargs: Any) -> Any:
            decision = score_tool_call(
                {"name": self.name, "args": kwargs},
                tier_config=cfg,
                tenant=tenant,
            )
            if decision.action in block_actions:
                raise BossGovernanceError(decision)
            if (
                decision.action in (DecisionAction.ESCALATE, DecisionAction.ALLOW_WITH_LOGGING)
                and on_escalate is not None
            ):
                on_escalate(decision)
            return wrapped._run(*args, **kwargs)

        async def _arun(self, *args: Any, **kwargs: Any) -> Any:
            decision = score_tool_call(
                {"name": self.name, "args": kwargs},
                tier_config=cfg,
                tenant=tenant,
            )
            if decision.action in block_actions:
                raise BossGovernanceError(decision)
            if (
                decision.action in (DecisionAction.ESCALATE, DecisionAction.ALLOW_WITH_LOGGING)
                and on_escalate is not None
            ):
                on_escalate(decision)
            return await wrapped._arun(*args, **kwargs)

    return _Guarded()


# ---------------------------------------------------------------------------
# Callback handler fragment
# ---------------------------------------------------------------------------


def on_tool_start_callback(
    *,
    tier_config: TierConfig | None = None,
    tenant: str = "default",
    on_escalate: Callable[[AdapterDecision], None] | None = None,
    block_actions: tuple[DecisionAction, ...] = (
        DecisionAction.BLOCK,
        DecisionAction.EMERGENCY_STOP,
    ),
) -> Callable[[dict[str, Any], str, str], None]:
    """Return a callback matching LangChain's ``on_tool_start`` signature.

    Attach it to a ``CallbackManager`` or pass to ``RunnableConfig``::

        config = {"callbacks": [MyHandler(on_tool_start=on_tool_start_callback())]}
    """
    cfg = tier_config or ADAM_DEFAULT_TIERS

    def _callback(
        serialized: dict[str, Any],
        input_str: str,
        run_id: str,
    ) -> None:
        name = serialized.get("name") or "unnamed_tool"
        payload = {"tool": name, "args": {"raw": input_str}, "run_id": run_id}
        decision = evaluate_payload(
            payload,
            framework="langgraph",
            tier_config=cfg,
            tenant=tenant,
        )
        if decision.action in block_actions:
            raise BossGovernanceError(decision)
        if on_escalate is not None and decision.action in (
            DecisionAction.ESCALATE,
            DecisionAction.ALLOW_WITH_LOGGING,
        ):
            on_escalate(decision)

    return _callback
