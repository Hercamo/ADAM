"""Regulatory Impact scorer — EU AI Act + GRC Compliance Scoring.

Sub-components (BOSS Formulas v3.2, Section 5.4):
    A. AI Act Risk Classification    — 0 to 40
    B. Jurisdictional Compliance Gap — 0 to 25
    C. Fundamental Rights Impact     — 0 to 20
    D. Documentation Completeness    — 0 to 10 (inverted)
    E. Cross-Border Complexity       — 0 to 5

Canonical input fields (operational):
    * ``primary_regulations`` — list of regulation keys touched by the
      intent (e.g. ``GDPR``, ``EU_AI_ACT``, ``DORA``, ``NIS2``, ``HIPAA``).
    * ``controls_passed`` / ``controls_total`` — GRC control posture.
    * ``open_findings_severity_max`` — one of
      ``NONE|LOW|MEDIUM|HIGH|CRITICAL``.
    * ``eu_ai_act_class`` — optional explicit classification override
      (``prohibited``/``high_risk``/``limited_risk``/``minimal_risk``).
    * ``fundamental_rights_impact`` — optional explicit ``[0, 1]`` value.
"""

from __future__ import annotations

from typing import Any

from boss_core.dimensions.base import Scorer, register_scorer
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey

AI_ACT_CLASS_WEIGHTS: dict[str, float] = {
    "prohibited": 40.0,
    "high_risk": 32.0,
    "limited_risk": 20.0,
    "minimal_risk": 5.0,
    "unclassified": 24.0,
}

SEVERITY_WEIGHTS: dict[str, float] = {
    "NONE": 0.0,
    "LOW": 2.0,
    "MEDIUM": 5.0,
    "HIGH": 8.0,
    "CRITICAL": 10.0,
}

RIGHTS_HEAVY_REGS = frozenset({"GDPR", "EU_AI_ACT", "CCPA", "HIPAA", "UK_GDPR"})


def _infer_ai_act_class(regs: list[str]) -> str:
    upper = {r.upper() for r in regs}
    if "EU_AI_ACT" in upper:
        return "high_risk"
    return "unclassified" if upper else "minimal_risk"


class RegulatoryImpactScorer(Scorer):
    """Regulatory risk spanning EU AI Act, GDPR, DORA and NIS2 exposure."""

    dimension = DimensionKey.REGULATORY

    def score(self, payload: dict[str, Any]) -> DimensionScore:
        raw_regs = payload.get("primary_regulations") or []
        regs = [str(r).strip().upper() for r in raw_regs if str(r).strip()]
        controls_passed = max(0, int(payload.get("controls_passed", 0)))
        controls_total = max(0, int(payload.get("controls_total", 0)))
        severity = str(payload.get("open_findings_severity_max", "NONE")).upper()
        rights_impact = payload.get("fundamental_rights_impact")
        ai_class = str(payload.get("eu_ai_act_class") or _infer_ai_act_class(regs)).lower()

        # A — AI Act Risk Classification (0-40).
        # No regulations in scope → no AI Act exposure for this intent.
        a_value = AI_ACT_CLASS_WEIGHTS.get(ai_class, 24.0) if regs else 0.0

        # B - Jurisdictional Compliance Gap (0-25): derived from controls.
        gap_pct = (1.0 - controls_passed / controls_total) * 100.0 if controls_total > 0 else 0.0
        b_value = self._cap(gap_pct * 0.5, 25.0)

        # C — Fundamental Rights Impact (0-20).
        if rights_impact is not None:
            rights_val = self._cap(float(rights_impact), 1.0)
            c_value = self._cap(rights_val * 20.0, 20.0)
        else:
            # Infer from rights-heavy regulations plus severity of findings.
            rights_hits = sum(1 for r in regs if r in RIGHTS_HEAVY_REGS)
            severity_boost = {"CRITICAL": 5.0, "HIGH": 3.0, "MEDIUM": 1.0}.get(severity, 0.0)
            c_value = self._cap(rights_hits * 7.5 + severity_boost, 20.0)

        # D — Documentation Completeness (0-10, inverted).
        d_value = self._cap(SEVERITY_WEIGHTS.get(severity, 0.0), 10.0)

        # E — Cross-Border Complexity (0-5): ≈1.5 per regulation touched.
        e_value = self._cap(len(regs) * 1.5, 5.0)

        subs = [
            SubComponentScore(
                name="EU AI Act Risk Classification",
                value=round(a_value, 4),
                max_value=40.0,
                rationale=(
                    f"Classification: {ai_class}" + ("" if regs else " (no regulations in scope).")
                ),
            ),
            SubComponentScore(
                name="Jurisdictional Compliance Gap",
                value=round(b_value, 4),
                max_value=25.0,
                rationale=(
                    f"Controls: {controls_passed}/{controls_total} passed ({gap_pct:.1f}% gap)."
                ),
            ),
            SubComponentScore(
                name="Fundamental Rights Impact",
                value=round(c_value, 4),
                max_value=20.0,
                rationale=(
                    "Explicit rights_impact input used."
                    if rights_impact is not None
                    else "Inferred from rights-heavy regulations and findings."
                ),
            ),
            SubComponentScore(
                name="Documentation Completeness (inverted)",
                value=round(d_value, 4),
                max_value=10.0,
                rationale=f"Max open finding severity: {severity}.",
            ),
            SubComponentScore(
                name="Cross-Border Complexity",
                value=round(e_value, 4),
                max_value=5.0,
                rationale=f"{len(regs)} regulations in scope.",
            ),
        ]
        return self._assemble(subs)


register_scorer(RegulatoryImpactScorer())
