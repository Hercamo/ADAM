"""BOSS adapters — integrations for agent and workflow frameworks.

The adapter layer lets any agent framework submit actions to the BOSS
Engine for governance without importing the framework itself. Each
adapter accepts the native "tool call" or "action" payload of its
target framework, normalizes it into an :class:`boss_core.schemas.IntentObject`,
calls :func:`boss_core.composite.evaluate`, and returns a structured
:class:`boss_adapters.base.AdapterDecision` the caller can use to
allow, block, or escalate the action.

Shipped adapters
----------------

* :mod:`boss_adapters.generic` — framework-agnostic callback adapter
  (use with any LLM application or custom agent loop)
* :mod:`boss_adapters.langgraph_adapter` — LangGraph / LangChain tools
* :mod:`boss_adapters.openai_agents_adapter` — OpenAI Agents SDK tools
* :mod:`boss_adapters.ai_foundry_adapter` — Azure AI Foundry agents
* :mod:`boss_adapters.crewai_adapter` — CrewAI tasks and tools

All adapters are pure-Python and do not import the target framework;
instead they accept duck-typed dicts (or, optionally, native objects
converted via the framework's own ``.dict()``/``.model_dump()``). This
keeps the adapter layer free of optional dependencies so ``pip install
boss-engine`` does not drag in LangChain, Azure SDKs, etc.
"""

from boss_adapters.base import (
    AdapterDecision,
    AdapterError,
    DecisionAction,
    evaluate_payload,
    intent_from_payload,
)
from boss_adapters.generic import GenericBossAdapter

__all__ = [
    "AdapterDecision",
    "AdapterError",
    "DecisionAction",
    "GenericBossAdapter",
    "evaluate_payload",
    "intent_from_payload",
]
