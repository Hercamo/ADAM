"""Worked example — OpenAI Agents SDK tool call governed by BOSS."""

from __future__ import annotations

from boss_adapters.openai_agents_adapter import score_function_call


def main() -> None:
    # Responses API function_call item.
    call = {
        "type": "function_call",
        "name": "create_vendor_payment",
        "arguments": (
            '{"amount_eur": 120000, "vendor_id": "v_42",'
            ' "boss_inputs": {'
            '  "financial": {"monetary_value_eur": 120000, "budget_exposure_pct": 12},'
            '  "regulatory": {"eu_ai_act_class": "minimal_risk"}'
            "}}"
        ),
        "call_id": "fc_9f3",
    }

    decision = score_function_call(call, tenant="netstreamx", is_non_idempotent=True)
    print(
        f"{call['name']} -> {decision.action.value} "
        f"({decision.escalation_tier.value}, composite={decision.composite:.1f})"
    )
    print(f"  rationale: {decision.rationale}")


if __name__ == "__main__":
    main()
