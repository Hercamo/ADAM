"""Reputational Risk scorer — RepRisk RRI + RepTrak ESG + SASB.

Sub-components (BOSS Formulas v3.2, Section 5.5):
    A. ESG Category Exposure          — 0 to 30
    B. Source Reach & Amplification   — 0 to 25
    C. Stakeholder Concern Level      — 0 to 25
    D. Precedent & Novelty            — 0 to 20

Canonical input fields (operational):
    * ``esg_severity_score`` — float in ``[0, 1]`` summarising RepRisk RRI
      intensity across environmental/social/governance categories.
    * ``sasb_material_topics_touched`` — list of SASB material topic keys
      (e.g. ``data_privacy``, ``media_ethics``).
    * ``reptrak_delta`` — projected RepTrak reputation shift in points;
      negative values indicate stakeholder concern. Typical range
      ``[-20, +20]``.
    * ``source_reach`` / ``amplification`` — optional ``[0, 1]`` overrides
      for the reach sub-component (used when a comms or PR team has sized
      the anticipated reach directly).
    * ``precedent_novelty`` — optional ``[0, 1]`` override.
"""

from __future__ import annotations

from typing import Any

from boss_core.dimensions.base import Scorer, register_scorer
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey


class ReputationalRiskScorer(Scorer):
    """Reputational exposure mixing RepRisk RRI intensity and reach signals."""

    dimension = DimensionKey.REPUTATIONAL

    def score(self, payload: dict[str, Any]) -> DimensionScore:
        esg_severity = self._cap(
            float(payload.get("esg_severity_score", payload.get("esg_severity", 0.0))),
            1.0,
        )
        topics = payload.get("sasb_material_topics_touched") or []
        topic_count = len([t for t in topics if str(t).strip()])
        reptrak_delta = float(payload.get("reptrak_delta", 0.0))

        source_reach = payload.get("source_reach")
        amplification = payload.get("amplification")
        novelty = payload.get("precedent_novelty")

        # A — ESG Category Exposure (0-30).
        a_value = self._cap(esg_severity * 22.0 + min(topic_count, 4) * 2.0, 30.0)

        # B — Source Reach & Amplification (0-25).
        if source_reach is not None or amplification is not None:
            reach_val = self._cap(float(source_reach or 0.0), 1.0)
            amp_val = self._cap(float(amplification or 0.0), 1.0)
            b_value = self._cap((reach_val * 0.6 + amp_val * 0.4) * 25.0, 25.0)
        else:
            # Infer reach from the number of SASB topics touched.
            b_value = self._cap(min(topic_count, 4) * 4.0, 25.0)

        # C — Stakeholder Concern (0-25). Negative RepTrak delta dominates.
        concern = max(0.0, -reptrak_delta)
        c_value = self._cap(concern * 2.0, 25.0)

        # D — Precedent & Novelty (0-20).
        if novelty is not None:
            d_value = self._cap(float(novelty) * 20.0, 20.0)
        else:
            d_value = self._cap(min(topic_count, 3) * 2.5 + esg_severity * 7.5, 20.0)

        subs = [
            SubComponentScore(
                name="ESG Category Exposure (RepRisk RRI)",
                value=round(a_value, 4),
                max_value=30.0,
                rationale=(
                    f"ESG severity {esg_severity:.2f}; {topic_count} SASB material topics touched."
                ),
            ),
            SubComponentScore(
                name="Source Reach & Amplification",
                value=round(b_value, 4),
                max_value=25.0,
                rationale=(
                    "Operator-supplied reach/amplification."
                    if source_reach is not None or amplification is not None
                    else f"Inferred from {topic_count} material topics."
                ),
            ),
            SubComponentScore(
                name="Stakeholder Concern Level (RepTrak)",
                value=round(c_value, 4),
                max_value=25.0,
                rationale=f"RepTrak delta {reptrak_delta:+.1f} pts.",
            ),
            SubComponentScore(
                name="Precedent & Novelty",
                value=round(d_value, 4),
                max_value=20.0,
                rationale=(
                    "Explicit novelty input used."
                    if novelty is not None
                    else "Inferred from topic breadth and ESG severity."
                ),
            ),
        ]
        return self._assemble(subs)


register_scorer(ReputationalRiskScorer())
