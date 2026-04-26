"""Rights Certainty scorer — ISO 31000 + NIST AI RMF.

Sub-components (BOSS Formulas v3.2, Section 5.6):
    A. Authorization Chain Verification — 0 to 30  (inverted)
    B. Ownership & IP Verification       — 0 to 30  (inverted)
    C. Entitlement Trustworthiness       — 0 to 20  (inverted)
    D. Conflict & Ambiguity Assessment   — 0 to 20

Canonical input fields (operational):
    * ``authorization_certainty`` — float in ``[0, 1]``. 1.0 means every
      step of the authorization chain is verified.
    * ``ownership_certainty`` — float in ``[0, 1]`` for IP/ownership of
      any artefact being produced or consumed.
    * ``consent_lineage_verified`` — bool. When ``False`` the entitlement
      sub-component is pegged high.
    * ``entitlement_certainty`` — optional float in ``[0, 1]``; overrides
      the consent-lineage inference when supplied.
    * ``conflict_index`` — optional float in ``[0, 1]`` for the conflict
      & ambiguity sub-component.
"""

from __future__ import annotations

from typing import Any

from boss_core.dimensions.base import Scorer, register_scorer
from boss_core.schemas import DimensionScore, SubComponentScore
from boss_core.tiers import DimensionKey


class RightsCertaintyScorer(Scorer):
    """Risk grows as rights certainty shrinks; high ambiguity drives the score."""

    dimension = DimensionKey.RIGHTS

    def score(self, payload: dict[str, Any]) -> DimensionScore:
        authorization = self._cap(float(payload.get("authorization_certainty", 1.0)), 1.0)
        ownership = self._cap(float(payload.get("ownership_certainty", 1.0)), 1.0)
        consent_verified = bool(payload.get("consent_lineage_verified", True))

        entitlement_override = payload.get("entitlement_certainty")
        if entitlement_override is not None:
            entitlement = self._cap(float(entitlement_override), 1.0)
        else:
            entitlement = 1.0 if consent_verified else 0.25

        conflict_override = payload.get("conflict_index")
        if conflict_override is not None:
            conflict_index = self._cap(float(conflict_override), 1.0)
        else:
            # Infer conflict from the spread of certainty signals.
            spread = max(
                abs(authorization - ownership),
                abs(authorization - entitlement),
                abs(ownership - entitlement),
            )
            conflict_index = self._cap(spread, 1.0)

        a_value = self._cap((1.0 - authorization) * 30.0, 30.0)
        b_value = self._cap((1.0 - ownership) * 30.0, 30.0)
        c_value = self._cap((1.0 - entitlement) * 20.0, 20.0)
        d_value = self._cap(conflict_index * 20.0, 20.0)

        subs = [
            SubComponentScore(
                name="Authorization Chain Verification (inverted)",
                value=round(a_value, 4),
                max_value=30.0,
                rationale=f"Authorization certainty {authorization:.2f}.",
            ),
            SubComponentScore(
                name="Ownership & IP Verification (inverted)",
                value=round(b_value, 4),
                max_value=30.0,
                rationale=f"Ownership certainty {ownership:.2f}.",
            ),
            SubComponentScore(
                name="Entitlement Trustworthiness (inverted)",
                value=round(c_value, 4),
                max_value=20.0,
                rationale=(
                    f"Entitlement certainty {entitlement:.2f} "
                    f"(consent {'verified' if consent_verified else 'unverified'})."
                ),
            ),
            SubComponentScore(
                name="Conflict & Ambiguity Assessment",
                value=round(d_value, 4),
                max_value=20.0,
                rationale=f"Conflict index {conflict_index:.2f}.",
            ),
        ]
        return self._assemble(subs)


register_scorer(RightsCertaintyScorer())
