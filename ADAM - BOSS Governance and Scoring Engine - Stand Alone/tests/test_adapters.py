"""Adapter translation tests.

Each adapter must turn its framework-native payload into an
:class:`IntentObject` and then a :class:`AdapterDecision`. We do *not*
import the upstream frameworks — the adapters are designed to accept
duck-typed dicts so they can be exercised in isolation.

Coverage:
* LangGraph deep integration — ``normalize_tool_call`` and ``score_tool_call``
* OpenAI Agents — ``normalize_function_call`` (Responses + Assistants shapes)
* AI Foundry — evaluator promotion into BOSS dimension inputs
* CrewAI — both Task and Tool shapes
* Generic ``evaluate_payload`` — happy path and error on non-mapping
"""

from __future__ import annotations

import pytest

from boss_adapters.ai_foundry_adapter import score_foundry_action
from boss_adapters.base import (
    AdapterDecision,
    DecisionAction,
    evaluate_payload,
    intent_from_payload,
)
from boss_adapters.crewai_adapter import score_crewai_task, score_crewai_tool
from boss_adapters.langgraph_adapter import (
    BossGovernanceError,
    boss_guard_node,
    normalize_tool_call,
    score_tool_call,
)
from boss_adapters.openai_agents_adapter import (
    normalize_function_call,
    score_function_call,
)
from boss_core.exceptions import AdapterError
from boss_core.schemas import EscalationTier


class TestLangGraph:
    def test_normalize_tool_call_dict(self) -> None:
        intent = normalize_tool_call(
            {
                "name": "send_email",
                "args": {"to": "ceo@example.com", "body": "hi"},
                "id": "call-1",
            }
        )
        assert intent.headline == "LangGraph tool: send_email"
        assert intent.source.user_id == "langgraph_agent"

    def test_score_defaults_to_soap(self) -> None:
        decision = score_tool_call({"name": "read_kpi_dashboard", "args": {}})
        assert decision.framework == "langgraph"
        assert decision.escalation_tier is EscalationTier.SOAP
        assert decision.action is DecisionAction.ALLOW

    def test_score_ohshat_with_explicit_boss_inputs(self) -> None:
        decision = score_tool_call(
            {
                "name": "transfer_funds",
                "args": {
                    "amount_eur": 5_000_000,
                    "boss_inputs": {
                        "security": {
                            "prompt_injection_risk": 0.9,
                            "cve_exposure_max_cvss": 9.5,
                            "mitre_tactics_detected": 6,
                        },
                        "financial": {
                            "projected_revenue_m": 0.0,
                            "projected_cost_m": 5.0,
                            "single_loss_expectancy_m": 12.0,
                            "annualized_rate_of_occurrence": 0.5,
                            "risk_appetite_m": 1.0,
                        },
                    },
                },
            },
            is_non_idempotent=True,
        )
        assert decision.escalation_tier in {
            EscalationTier.HIGH,
            EscalationTier.OHSHAT,
        }
        assert decision.action in {
            DecisionAction.ESCALATE,
            DecisionAction.EMERGENCY_STOP,
        }

    def test_boss_guard_node_blocks_ohshat(self) -> None:
        node = boss_guard_node()
        state = {
            "messages": [
                {
                    "tool_calls": [
                        {
                            "name": "wipe_backups",
                            "args": {
                                "is_non_idempotent": True,
                                "boss_inputs": {
                                    "security": {
                                        "prompt_injection_risk": 0.95,
                                        "cve_exposure_max_cvss": 9.9,
                                        "mitre_tactics_detected": 10,
                                    },
                                },
                            },
                        }
                    ],
                }
            ],
        }
        with pytest.raises(BossGovernanceError):
            node(state)


class TestOpenAIAgents:
    def test_responses_api_shape(self) -> None:
        payload = normalize_function_call(
            {
                "type": "function_call",
                "name": "transfer_funds",
                "arguments": '{"amount_eur": 100}',
                "call_id": "call-42",
            }
        )
        assert payload["name"] == "transfer_funds"
        assert payload["args"] == {"amount_eur": 100}
        assert payload["call_id"] == "call-42"

    def test_assistants_api_shape(self) -> None:
        payload = normalize_function_call(
            {
                "id": "call-7",
                "function": {
                    "name": "search",
                    "arguments": '{"q":"hello"}',
                },
            }
        )
        assert payload["name"] == "search"
        assert payload["args"] == {"q": "hello"}

    def test_score_default_tier_soap(self) -> None:
        decision = score_function_call({"type": "function_call", "name": "noop", "arguments": "{}"})
        assert decision.framework == "openai_agents"
        assert decision.escalation_tier is EscalationTier.SOAP

    def test_malformed_arguments_fallback(self) -> None:
        payload = normalize_function_call(
            {"type": "function_call", "name": "x", "arguments": "not-json"}
        )
        assert payload["args"] == {"raw": "not-json"}


class TestAIFoundry:
    def test_evaluators_promoted(self) -> None:
        decision: AdapterDecision = score_foundry_action(
            {
                "tool": "draft_announcement",
                "tool_input": {"text": "Public launch"},
                "evaluators": {
                    "indirect_attack": 0.8,
                    "pii": 0.3,
                    "hate_unfairness": 0.5,
                },
            }
        )
        # Elevated evaluators should drag the tier above SOAP.
        assert decision.escalation_tier is not EscalationTier.SOAP

    def test_data_residency_attached(self) -> None:
        decision = score_foundry_action(
            {
                "name": "query_customers",
                "parameters": {"q": "x"},
                "data_residency": "eu-west-1",
            }
        )
        assert decision.framework == "ai_foundry"


class TestCrewAI:
    def test_task_payload(self) -> None:
        decision = score_crewai_task(
            {
                "description": "Summarize quarterly sales",
                "expected_output": "paragraph",
                "agent": {"role": "sales_analyst"},
                "tools": [{"name": "sql_query"}],
            }
        )
        assert decision.framework == "crewai"
        assert decision.escalation_tier is EscalationTier.SOAP

    def test_tool_payload(self) -> None:
        decision = score_crewai_tool({"name": "web_search", "args": {"q": "x"}})
        assert decision.framework == "crewai"


class TestGeneric:
    def test_intent_from_payload_rejects_non_mapping(self) -> None:
        with pytest.raises(AdapterError):
            intent_from_payload([1, 2, 3], framework="custom")

    def test_evaluate_payload_happy_path(self) -> None:
        decision = evaluate_payload(
            {"headline": "manual action"},
            framework="generic",
        )
        assert decision.framework == "generic"
        assert 0 <= decision.composite <= 100
        assert isinstance(decision.to_dict(), dict)
