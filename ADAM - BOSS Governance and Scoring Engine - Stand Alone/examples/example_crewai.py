"""Worked example — CrewAI task governed by BOSS."""

from __future__ import annotations

from boss_adapters.crewai_adapter import score_crewai_task, score_crewai_tool


def main() -> None:
    task = {
        "description": (
            "Draft a customer-facing announcement about the Q1 cloud "
            "region migration from US-EAST-1 to EU-WEST-3."
        ),
        "expected_output": "Markdown press release under 600 words.",
        "agent": {"role": "Chief Communications Officer"},
        "tools": [{"name": "web_search"}, {"name": "publish_press_release"}],
        "boss_inputs": {
            "sovereignty": {"data_residency": "eu-west-3", "seal_objectives_met": 6},
            "reputational": {"esg_severity_score": 15, "reach_population": 250_000},
        },
    }

    decision = score_crewai_task(task, tenant="netstreamx")
    print(
        f"Task -> {decision.action.value} "
        f"({decision.escalation_tier.value}, composite={decision.composite:.1f})"
    )
    print(f"  rationale: {decision.rationale}")

    tool_call = {
        "name": "publish_press_release",
        "args": {
            "draft_id": "pr-2026-04",
            "boss_inputs": {
                "reputational": {
                    "esg_severity_score": 25,
                    "reach_population": 10_000_000,
                    "stakeholder_concern_level": "medium",
                    "novelty_score": 20,
                },
            },
        },
    }

    tdecision = score_crewai_tool(tool_call, tenant="netstreamx", is_non_idempotent=True)
    print(
        f"Tool -> {tdecision.action.value} "
        f"({tdecision.escalation_tier.value}, composite={tdecision.composite:.1f})"
    )


if __name__ == "__main__":
    main()
