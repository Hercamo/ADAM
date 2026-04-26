"""Worked example — Azure AI Foundry action governed by BOSS.

The payload mirrors what the ``azure-ai-agents`` SDK produces when an
agent's tool call is intercepted by a ``ToolCallInterceptor``. In a real
integration you would call ``score_foundry_action`` from inside the
interceptor and return ``True`` (allow) / ``False`` (block) based on
``decision.action``.
"""

from __future__ import annotations

from boss_adapters.ai_foundry_adapter import score_foundry_action


def main() -> None:
    action = {
        "tool": "summarize_financial_disclosure",
        "tool_input": {
            "document_path": "s3://reports/q1-2026-earnings.pdf",
        },
        "evaluators": {
            "pii": 0.35,
            "indirect_attack": 0.20,
            "protected_material": 0.15,
            "hate_unfairness": 0.05,
        },
        "data_residency": "eu-west-3",
    }

    decision = score_foundry_action(action, tenant="netstreamx")
    print(f"{action['tool']}: {decision.action.value}")
    print(f"  tier:      {decision.escalation_tier.value}")
    print(f"  composite: {decision.composite:.1f}")
    print(f"  rationale: {decision.rationale}")


if __name__ == "__main__":
    main()
