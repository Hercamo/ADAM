"""Security Impact dimension scorer.

Framework attribution: NIST CSF 2.0 + CVSS v4.0 + MITRE ATT&CK + NIST AI RMF.

Sub-components (BOSS Formulas v3.2, Section 5.1):
    A. Attack Surface / CVSS Exposure   — 0 to 40
    B. Control Maturity (NIST CSF)      — 0 to 10
    C. Threat Intelligence (MITRE)      — 0 to 25
    D. AI-Specific Security             — 0 to 25

Canonical input fields (operational):
    * ``cve_exposure_max_cvss`` — float in ``[0, 10]`` (CVSS base score).
    * ``mitre_tactics_detected`` — non-negative integer.
    * ``prompt_injection_risk`` — float in ``[0, 1]``.
    * ``nist_csf_maturity`` — optional float in ``[1, 5]``; defaults to ``3``
      (partial). Lower maturity increases the sub-score.
    * ``ai_specific_exposure`` — optional float in ``[0, 1]`` layered on top
      of prompt-injection for generic adversarial AI risk.
"""

from __future__ import annotations

from typing import Any

from boss_core.dimensions.base import Scorer, register_scorer
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey


class SecurityImpactScorer(Scorer):
    """Security impact scoring using NIST CSF 2.0 + CVSS v4.0 + MITRE ATT&CK."""

    dimension = DimensionKey.SECURITY

    def score(self, payload: dict[str, Any]) -> DimensionScore:
        cvss = float(payload.get("cve_exposure_max_cvss", 0.0))
        tactics = int(payload.get("mitre_tactics_detected", 0))
        prompt_inj = float(payload.get("prompt_injection_risk", 0.0))
        csf_maturity = float(payload.get("nist_csf_maturity", 3.0))
        ai_exposure = float(payload.get("ai_specific_exposure", 0.0))

        # A — Attack Surface (0-40): CVSS magnitude proxy.
        a_value = self._cap((cvss / 10.0) * 40.0, 40.0)

        # B — Control Maturity (0-10): NIST CSF 2.0 maturity inverted.
        # Defaults to mid-scale (3) so undefined payloads do not inflate.
        csf_clamped = self._cap(csf_maturity, 5.0, 1.0)
        b_value = self._cap((5.0 - csf_clamped) * (10.0 / 4.0), 10.0)

        # C — Threat Intelligence (0-25): MITRE ATT&CK tactics observed.
        # 5 points per tactic; 5 tactics saturates the sub-component.
        c_value = self._cap(max(tactics, 0) * 5.0, 25.0)

        # D — AI-Specific Security (0-25): prompt injection dominates,
        # with a residual term for adversarial/AI-specific exposure.
        d_value = self._cap(prompt_inj * 20.0 + ai_exposure * 10.0, 25.0)

        subs = [
            SubComponentScore(
                name="Attack Surface (CVSS v4.0)",
                value=round(a_value, 4),
                max_value=40.0,
                rationale=f"Max CVSS {cvss:.2f} scaled to 40.",
            ),
            SubComponentScore(
                name="Control Maturity (NIST CSF 2.0)",
                value=round(b_value, 4),
                max_value=10.0,
                rationale=f"CSF maturity {csf_clamped:.1f}/5 (inverted).",
            ),
            SubComponentScore(
                name="Threat Intelligence (MITRE ATT&CK)",
                value=round(c_value, 4),
                max_value=25.0,
                rationale=f"{max(tactics, 0)} tactics observed.",
            ),
            SubComponentScore(
                name="AI-Specific Security (NIST AI RMF)",
                value=round(d_value, 4),
                max_value=25.0,
                rationale=(
                    f"Prompt-injection risk {prompt_inj:.2f}; "
                    f"adversarial exposure {ai_exposure:.2f}."
                ),
            ),
        ]
        return self._assemble(subs)


register_scorer(SecurityImpactScorer())
