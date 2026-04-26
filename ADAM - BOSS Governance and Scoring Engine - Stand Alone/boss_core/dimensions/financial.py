"""Financial Exposure scorer — FAIR + COSO ERM.

Sub-components (BOSS Formulas v3.2, Section 5.3):
    A. Action Monetary Value         — 0 to 30
    B. Cumulative Budget Exposure    — 0 to 25
    C. Loss Magnitude Estimate       — 0 to 25
    D. Cascading Financial Risk      — 0 to 20

Canonical input fields (operational, in millions of EUR unless stated):
    * ``projected_revenue_m`` — expected revenue from the intent.
    * ``projected_cost_m`` — expected committed cost.
    * ``single_loss_expectancy_m`` — FAIR LM (magnitude of a single loss).
    * ``annualized_rate_of_occurrence`` — FAIR LEF (0-1 typically, or >1
      for very frequent events).
    * ``risk_appetite_m`` — approved risk appetite expressed in M€.
    * ``cascading_risk_beta`` — optional 0-1 beta for downstream exposure.
"""

from __future__ import annotations

import math
from typing import Any

from boss_core.dimensions.base import Scorer, register_scorer
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey


class FinancialExposureScorer(Scorer):
    """Financial exposure derived from FAIR LEF/LM and COSO appetite signals."""

    dimension = DimensionKey.FINANCIAL

    def score(self, payload: dict[str, Any]) -> DimensionScore:
        revenue = max(0.0, float(payload.get("projected_revenue_m", 0.0)))
        cost = max(0.0, float(payload.get("projected_cost_m", 0.0)))
        sle = max(0.0, float(payload.get("single_loss_expectancy_m", 0.0)))
        aro = max(0.0, float(payload.get("annualized_rate_of_occurrence", 0.0)))
        appetite = max(0.0, float(payload.get("risk_appetite_m", 0.0)))
        beta = max(0.0, float(payload.get("cascading_risk_beta", 0.0)))

        action_value_m = max(revenue, cost)

        # A - Action Monetary Value (0-30).
        # Distance above the risk appetite in log-space; actions below
        # appetite contribute nothing. Every ~10x over appetite adds 15.
        if action_value_m <= 0.0 or appetite <= 0.0 or action_value_m <= appetite:
            a_value = 0.0
        else:
            ratio = action_value_m / appetite
            a_value = self._cap(math.log10(ratio) * 15.0, 30.0)

        # B - Cumulative Budget Exposure (0-25).
        # Cost relative to appetite. At 1x appetite: 10 pts. At 2x: 20 pts.
        cost_ratio = cost / appetite if appetite > 0.0 else (1.0 if cost > 0.0 else 0.0)
        b_value = self._cap(cost_ratio * 10.0, 25.0)

        # C - Loss Magnitude Estimate (0-25). FAIR: Expected Annual Loss.
        eal = sle * aro
        loss_ratio = eal / appetite if appetite > 0.0 else 0.0
        # 1x appetite EAL -> 20 pts; saturates at 25 above ~1.25x.
        c_value = self._cap(loss_ratio * 20.0, 25.0)

        # D — Cascading Financial Risk (0-20).
        # Explicit beta if provided; otherwise tail-risk proxy from SLE.
        if beta > 0.0:
            d_value = self._cap(beta * 20.0, 20.0)
        elif appetite > 0.0 and sle > 0.0:
            d_value = self._cap((sle / appetite) * 5.0, 20.0)
        else:
            d_value = 0.0

        subs = [
            SubComponentScore(
                name="Action Monetary Value",
                value=round(a_value, 4),
                max_value=30.0,
                rationale=(
                    f"Action value €{action_value_m:.2f}M vs appetite "
                    f"€{appetite:.2f}M (log-scaled)."
                ),
            ),
            SubComponentScore(
                name="Cumulative Budget Exposure (COSO)",
                value=round(b_value, 4),
                max_value=25.0,
                rationale=(f"Cost €{cost:.2f}M = {cost_ratio * 100.0:.1f}% of appetite."),
            ),
            SubComponentScore(
                name="Loss Magnitude Estimate (FAIR)",
                value=round(c_value, 4),
                max_value=25.0,
                rationale=(
                    f"EAL €{eal:.3f}M (SLE €{sle:.2f}M x ARO {aro:.3f}) "
                    f"vs appetite €{appetite:.2f}M."
                ),
            ),
            SubComponentScore(
                name="Cascading Financial Risk",
                value=round(d_value, 4),
                max_value=20.0,
                rationale=(f"Cascading beta {beta:.2f}; tail-loss proxy €{sle:.2f}M."),
            ),
        ]
        return self._assemble(subs)


register_scorer(FinancialExposureScorer())
