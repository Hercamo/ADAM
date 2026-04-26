"""Worked example — LangGraph agent governed by BOSS.

This example demonstrates the three integration styles offered by the
LangGraph adapter:

1. ``score_tool_call`` — pure function, zero framework coupling.
2. ``boss_guard_node`` — LangGraph node factory that sits between the
   planner and the tool executor.
3. ``BossGuardTool`` — LangChain ``BaseTool`` wrapper (requires
   ``langchain-core``).

Run it with::

    python examples/example_langgraph.py

No Neo4j or FastAPI server is required — the scoring engine is pure
Python.
"""

from __future__ import annotations

from boss_adapters import DecisionAction
from boss_adapters.langgraph_adapter import (
    BossGovernanceError,
    boss_guard_node,
    score_tool_call,
)


def demo_pure_function() -> None:
    print("--- demo_pure_function ---")

    safe_call = {
        "name": "read_weather",
        "args": {"city": "Amsterdam"},
        "id": "call_weather_1",
    }
    decision = score_tool_call(safe_call, tenant="netstreamx")
    print(
        f"  {safe_call['name']:<24} -> {decision.action.value} "
        f"({decision.escalation_tier.value}, composite={decision.composite:.1f})"
    )

    risky_call = {
        "name": "publish_press_release",
        "args": {
            "headline": "Breaking announcement",
            "boss_inputs": {
                "reputational": {
                    "esg_severity_score": 80,
                    "reach_population": 10_000_000,
                    "stakeholder_concern_level": "high",
                    "novelty_score": 60,
                },
            },
        },
        "id": "call_pr_1",
    }
    decision = score_tool_call(risky_call, tenant="netstreamx", is_non_idempotent=True)
    print(
        f"  {risky_call['name']:<24} -> {decision.action.value} "
        f"({decision.escalation_tier.value}, composite={decision.composite:.1f})"
    )
    print(f"    rationale: {decision.rationale}")


def demo_guard_node() -> None:
    print("--- demo_guard_node ---")

    escalations: list[str] = []

    def log_escalation(decision):  # type: ignore[no-untyped-def]
        escalations.append(f"{decision.escalation_tier.value} ({decision.composite:.1f})")

    guard = boss_guard_node(tenant="netstreamx", on_escalate=log_escalation)

    state = {
        "messages": [
            {
                "role": "assistant",
                "tool_calls": [
                    {"name": "read_weather", "args": {}, "id": "c1"},
                    {
                        "name": "transfer_funds",
                        "args": {
                            "amount_eur": 750_000,
                            "boss_inputs": {
                                "financial": {
                                    "monetary_value_eur": 750_000,
                                    "budget_exposure_pct": 35,
                                },
                            },
                        },
                        "id": "c2",
                    },
                ],
            }
        ],
    }

    new_state = guard(state)
    print(f"  decisions recorded: {len(new_state['boss_decisions'])}")
    for entry in new_state["boss_decisions"]:
        print(f"    - {entry['action']:<18} tier={entry['escalation_tier']}")
    print(f"  escalations fired: {escalations}")


def demo_blocking_behavior() -> None:
    print("--- demo_blocking_behavior ---")

    def abort_policy(decision):  # type: ignore[no-untyped-def]
        # Treat HIGH/OHSHAT as a hard block in this demo.
        pass

    guard = boss_guard_node(
        tenant="netstreamx",
        on_escalate=abort_policy,
        block_actions=(DecisionAction.BLOCK, DecisionAction.EMERGENCY_STOP),
    )

    state = {
        "messages": [
            {
                "tool_calls": [
                    {
                        "name": "shutdown_production_cluster",
                        "args": {
                            "boss_inputs": {
                                "security": {
                                    "ai_exposure": 90,
                                    "prompt_injection_risk": 90,
                                    "control_maturity": 10,
                                },
                            },
                        },
                        "id": "c_shutdown",
                    },
                ],
            }
        ],
    }

    try:
        guard(state)
    except BossGovernanceError as exc:
        print(f"  BOSS blocked: {exc}")


if __name__ == "__main__":
    demo_pure_function()
    demo_guard_node()
    demo_blocking_behavior()
