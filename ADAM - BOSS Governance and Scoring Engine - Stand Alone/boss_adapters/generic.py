"""Generic BOSS adapter — framework-agnostic callback.

Use this adapter when you are NOT on LangGraph, OpenAI Agents, AI
Foundry, or CrewAI, or when you just want the smallest possible
integration surface for a bespoke agent loop.

Example
-------

.. code-block:: python

    from boss_adapters import GenericBossAdapter, DecisionAction

    guard = GenericBossAdapter(tenant="netstreamx")

    action = {
        "tool": "publish_press_release",
        "boss_inputs": {
            "reputational": {
                "esg_severity_score": 80,
                "reach_population": 10_000_000,
                "stakeholder_concern_level": "high",
            },
        },
    }

    decision = guard.evaluate(action, is_non_idempotent=True)
    if decision.action is DecisionAction.BLOCK:
        raise RuntimeError(decision.rationale)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from boss_adapters.base import AdapterDecision, evaluate_payload
from boss_core.schemas import RiskRole, Urgency
from boss_core.tiers import TierConfig


@dataclass
class GenericBossAdapter:
    """Minimal reusable adapter — a thin wrapper over ``evaluate_payload``."""

    tenant: str = "default"
    actor_id: str = "agent"
    actor_role: RiskRole = RiskRole.SYSTEM
    urgency: Urgency = Urgency.ROUTINE
    tier_config: TierConfig | None = None

    def evaluate(
        self,
        payload: Mapping[str, Any],
        *,
        is_non_idempotent: bool | None = None,
        urgency: Urgency | None = None,
    ) -> AdapterDecision:
        """Score a framework-agnostic payload and return a decision."""
        return evaluate_payload(
            payload,
            framework="generic",
            tier_config=self.tier_config,
            tenant=self.tenant,
            actor_id=self.actor_id,
            actor_role=self.actor_role,
            urgency=urgency or self.urgency,
            is_non_idempotent=is_non_idempotent,
        )
